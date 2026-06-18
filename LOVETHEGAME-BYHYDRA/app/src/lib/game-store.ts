import { create } from 'zustand';
import { collection, doc, setDoc, getDoc, updateDoc, onSnapshot, query, where, orderBy, serverTimestamp } from 'firebase/firestore';
import { db } from './firebaseClient';
import * as Haptics from 'expo-haptics';
import { 
  GameSession, 
  GameResults, 
  GameState, 
  MarcieAnimation,
  Couple,
  RealtimeSync,
  BuzzerData 
} from './game-types';

interface GameStore {
  // Current game session
  currentSession: GameSession | null;
  gameState: GameState;
  loading: boolean;
  error: string | null;
  
  // Partner synchronization
  partnerOnline: boolean;
  lastPartnerUpdate: number | null;
  
  // Marcie AI integration
  currentMarcieAnimation: MarcieAnimation | null;
  marcieVisible: boolean;
  
  // Game lifecycle methods
  initializeGame: (coupleId: string, gameName: string) => Promise<void>;
  updateGameState: (updates: Partial<GameSession['game_state']>) => Promise<void>;
  submitAnswer: (playerId: string, answer: any) => Promise<void>;
  handleBuzz: (playerId: string, questionId: string) => Promise<void>;
  endGame: (finalScores: GameResults['scores']) => Promise<void>;
  
  // Real-time sync
  subscribeToPartner: (coupleId: string) => () => void;
  broadcastUpdate: (channel: string, data: any) => Promise<void>;
  
  // Marcie AI integration
  triggerMarcieAnimation: (animation: MarcieAnimation) => void;
  hideMarcie: () => void;
  showMarcie: () => void;
  
  // Utility methods
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  resetGame: () => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  currentSession: null,
  gameState: 'waiting_for_partner',
  loading: false,
  error: null,
  partnerOnline: false,
  lastPartnerUpdate: null,
  currentMarcieAnimation: null,
  marcieVisible: true,

  initializeGame: async (coupleId: string, gameName: string) => {
    set({ loading: true, error: null });
    
    try {
      // Create new game session
      const sessionRef = doc(collection(db, 'game_sessions'));
      const newSession: Omit<GameSession, 'id'> = {
        couple_id: coupleId,
        game_name: gameName,
        game_state: {
          currentRound: 1,
          currentQuestion: null,
          activePlayer: null,
          buzzerEnabled: false,
          gameStarted: false,
        },
        player1_data: {},
        player2_data: {},
        scores: { player1: 0, player2: 0 },
        completed: false,
        started_at: new Date().toISOString(),
        session_data: {},
      };

      await setDoc(sessionRef, {
        ...newSession,
        created_at: serverTimestamp(),
      });

      const session = { ...newSession, id: sessionRef.id };
      set({ 
        currentSession: session, 
        gameState: 'loading_content',
        loading: false 
      });

      // Subscribe to partner updates
      const unsubscribe = get().subscribeToPartner(coupleId);
      
      // Store unsubscribe function for cleanup
      (session as any).unsubscribe = unsubscribe;

    } catch (error) {
      console.error('Failed to initialize game:', error);
      set({ 
        error: 'Failed to start game. Please try again.',
        loading: false 
      });
    }
  },

  updateGameState: async (updates: Partial<GameSession['game_state']>) => {
    const { currentSession } = get();
    if (!currentSession) return;

    try {
      const sessionRef = doc(db, 'game_sessions', currentSession.id);
      const newGameState = { ...currentSession.game_state, ...updates };
      
      await updateDoc(sessionRef, {
        game_state: newGameState,
        updated_at: serverTimestamp(),
      });

      set({
        currentSession: {
          ...currentSession,
          game_state: newGameState,
        },
      });

      // Trigger haptic feedback for game state changes
      if (updates.buzzerEnabled !== undefined) {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }

    } catch (error) {
      console.error('Failed to update game state:', error);
      set({ error: 'Failed to update game state' });
    }
  },

  submitAnswer: async (playerId: string, answer: any) => {
    const { currentSession, updateGameState } = get();
    if (!currentSession) return;

    try {
      // Update player data with answer
      const playerDataKey = playerId === currentSession.couple_id ? 'player1_data' : 'player2_data';
      const sessionRef = doc(db, 'game_sessions', currentSession.id);
      
      await updateDoc(sessionRef, {
        [playerDataKey]: {
          ...currentSession[playerDataKey],
          lastAnswer: answer,
          answerTimestamp: serverTimestamp(),
        },
      });

      // Update game state
      await updateGameState({
        answerSubmitted: true,
        answeringPlayer: playerId,
      });

      // Trigger Marcie animation for answer submitted
      get().triggerMarcieAnimation({
        type: 'listening',
        speech: "Interesting answer, darling...",
      });

    } catch (error) {
      console.error('Failed to submit answer:', error);
      set({ error: 'Failed to submit answer' });
    }
  },

  handleBuzz: async (playerId: string, questionId: string) => {
    const { currentSession, gameState } = get();
    if (!currentSession || gameState !== 'question_active') return;

    try {
      const buzzData: BuzzerData = {
        playerId,
        timestamp: Date.now(),
        questionId,
      };

      // Record buzz time with millisecond precision
      const sessionRef = doc(db, 'game_sessions', currentSession.id);
      const buzzTimes = currentSession.session_data.buzzTimes || {};
      buzzTimes[questionId] = {
        ...buzzTimes[questionId],
        [playerId]: buzzData.timestamp,
      };

      await updateDoc(sessionRef, {
        'session_data.buzzTimes': buzzTimes,
      });

      // Update game state to show who buzzed first
      await get().updateGameState({
        activePlayer: playerId,
        buzzerEnabled: false,
      });

      // Haptic feedback for buzz
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

      // Trigger Marcie animation
      get().triggerMarcieAnimation({
        type: 'thinking',
        speech: "First buzz! Go ahead, darling...",
      });

    } catch (error) {
      console.error('Failed to handle buzz:', error);
      set({ error: 'Failed to record buzz' });
    }
  },

  endGame: async (finalScores: GameResults['scores']) => {
    const { currentSession } = get();
    if (!currentSession) return;

    try {
      const sessionRef = doc(db, 'game_sessions', currentSession.id);
      const winner = finalScores.player1 > finalScores.player2 ? 'player1' : 
                    finalScores.player2 > finalScores.player1 ? 'player2' : 'tie';

      await updateDoc(sessionRef, {
        scores: finalScores,
        completed: true,
        completed_at: serverTimestamp(),
      });

      set({
        gameState: 'game_complete',
        currentSession: {
          ...currentSession,
          scores: finalScores,
          completed: true,
        },
      });

      // Trigger victory/defeat animation
      get().triggerMarcieAnimation({
        type: winner === 'tie' ? 'thinking' : 'correct',
        speech: winner === 'player1' ? "Player One takes the crown!" :
                winner === 'player2' ? "Player Two reigns supreme!" :
                "A perfect tie! How romantic!",
      });

    } catch (error) {
      console.error('Failed to end game:', error);
      set({ error: 'Failed to end game' });
    }
  },

  subscribeToPartner: (coupleId: string) => {
    // Subscribe to partner's real-time updates
    const q = query(
      collection(db, 'realtime_sync'),
      where('couple_id', '==', coupleId),
      orderBy('created_at', 'desc'),
      limit(1)
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      if (!snapshot.empty) {
        const latestUpdate = snapshot.docs[0].data() as RealtimeSync;
        set({
          partnerOnline: true,
          lastPartnerUpdate: new Date(latestUpdate.created_at).getTime(),
        });

        // Handle partner game state updates
        if (latestUpdate.data.type === 'game_state_update') {
          const { gameState } = latestUpdate.data;
          set({ gameState });
        }
      }
    }, (error) => {
      console.error('Partner sync error:', error);
      set({ partnerOnline: false });
    });

    return unsubscribe;
  },

  broadcastUpdate: async (channel: string, data: any) => {
    const { currentSession } = get();
    if (!currentSession) return;

    try {
      const syncRef = doc(collection(db, 'realtime_sync'));
      const syncData: Omit<RealtimeSync, 'id'> = {
        couple_id: currentSession.couple_id,
        channel,
        data,
        sender_id: 'current_user', // This should be replaced with actual user ID
        created_at: new Date().toISOString(),
      };

      await setDoc(syncRef, {
        ...syncData,
        created_at: serverTimestamp(),
      });

    } catch (error) {
      console.error('Failed to broadcast update:', error);
    }
  },

  triggerMarcieAnimation: (animation: MarcieAnimation) => {
    set({
      currentMarcieAnimation: animation,
      marcieVisible: true,
    });

    // Auto-hide after duration
    if (animation.duration) {
      setTimeout(() => {
        set({ currentMarcieAnimation: null });
      }, animation.duration);
    }
  },

  hideMarcie: () => {
    set({ marcieVisible: false });
  },

  showMarcie: () => {
    set({ marcieVisible: true });
  },

  setLoading: (loading: boolean) => {
    set({ loading });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  resetGame: () => {
    set({
      currentSession: null,
      gameState: 'waiting_for_partner',
      loading: false,
      error: null,
      partnerOnline: false,
      lastPartnerUpdate: null,
      currentMarcieAnimation: null,
      marcieVisible: true,
    });
  },
}));
