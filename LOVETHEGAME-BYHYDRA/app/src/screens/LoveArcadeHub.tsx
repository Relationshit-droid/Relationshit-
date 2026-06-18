import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Dimensions,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { ScreenLayout } from '../layout';
import { COLORS, TYPOGRAPHY, SPACING, BORDER_RADIUS, SHADOWS, ANIMATIONS, GRADIENTS } from '../theme';
import { GlassCard, Typography, SquishyButton } from '../components/ui';
import DrMarcieOverlay from '../components/DrMarcieOverlay';
import * as Haptics from 'expo-haptics';

// Backend integration
import { useGameSession } from '../hooks/useGameSession';
import { getGameByScreen } from '../lib/gameRegistry';

const { width } = Dimensions.get('window');

const ARCADE_GAMES = [
  {
    id: 'truth-teller-tower',
    name: 'Truth Teller Tower',
    phase: 'Phase 1: Foundation',
    format: 'Who Wants to Be a Millionaire meets Newlywed Game',
    description: "Scale the lie-avalanche. Five questions. Three lifelines. One shared brain—if you're lucky.",
    icon: '🗼',
    colors: [COLORS.emotionalConnection, COLORS.brightYellow, COLORS.warmOrange],
    maxScore: 100,
  },
  {
    id: 'echo-chamber-escape',
    name: 'Escape the Echo Chamber',
    phase: 'Phase 2: Deconstruction',
    format: 'Digital Escape Room',
    description: "Trapped in a hall of infinite mirrors, each reflecting a version of the 'love script.' Break the loop.",
    icon: '🪞',
    colors: [COLORS.softViolet, COLORS.lavenderPurple, COLORS.rosePink],
    maxScore: 100,
  },
  {
    id: 'intimacy-feud',
    name: 'The Intimacy Feud',
    phase: 'Phase 3: Shared Reality',
    format: 'Family Feud Style',
    description: "Survey says... be boring. Be authentic. Face off against The Ghost of the Old Script.",
    icon: '👨‍👩‍👧‍👦',
    colors: [COLORS.conflictResolution, COLORS.mintGreen, COLORS.aquaTeal],
    maxScore: 250,
  },
];

const ArcadeGameCard = ({ game, onPress, index }: any) => {
  const [scaleAnim] = useState(new Animated.Value(1));
  const [glowAnim] = useState(new Animated.Value(0.6));

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: ANIMATIONS.duration.slower * 2,
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0.6,
          duration: ANIMATIONS.duration.slower * 2,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const handlePressIn = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    Animated.spring(scaleAnim, {
      toValue: 0.96,
      useNativeDriver: true,
      speed: 50,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
      speed: 50,
    }).start();
  };

  return (
    <Animated.View 
      style={[
        styles.arcadeCard,
        { transform: [{ scale: scaleAnim }] }
      ]}
    >
      <SquishyButton
        variant="ghost"
        size="large"
        onPress={onPress}
        style={styles.cardTouchable}
      >
        <Animated.View 
          style={[
            styles.cabinetGlow,
            { 
              opacity: glowAnim,
              shadowColor: COLORS.glowPink,
            }
          ]}
        />
        
        <GlassCard style={styles.cabinetBody} variant="elevated">
          <View style={[styles.cabinetFrame, { borderColor: game.colors[0] }]}>
            <View style={styles.gameScreen}>
              <LinearGradient
                colors={[game.colors[0], game.colors[1]]}
                style={styles.screenGradient}
                start={GRADIENTS.primary.start}
                end={GRADIENTS.primary.end}
              >
                <Typography variant="h1" style={styles.gameIcon}>
                  {game.icon}
                </Typography>
              </LinearGradient>
            </View>
            
            <View style={styles.marqueeContainer}>
              <Typography variant="h2" style={[styles.gameName, { color: game.colors[1] }]}>
                {game.name}
              </Typography>
            </View>
            
            <View style={[styles.phaseIndicator, { backgroundColor: game.colors[0] }]}>
              <Typography variant="caption" style={styles.phaseText}>
                {game.phase}
              </Typography>
            </View>
            
            <Typography variant="body" style={styles.gameDesc}>
              {game.description}
            </Typography>
            
            <View style={styles.controlPanel}>
              <View style={styles.scoreDisplay}>
                <Typography variant="caption" style={styles.scoreLabel}>
                  Max Score
                </Typography>
                <Typography variant="h2" style={[styles.scoreValue, { color: game.colors[1] }]}>
                  {game.maxScore}
                </Typography>
              </View>
              
              <SquishyButton
                variant="primary"
                size="medium"
                onPress={onPress}
              >
                <Typography variant="button" color={COLORS.textPrimary}>
                  ▶ PLAY
                </Typography>
              </SquishyButton>
            </View>
            
            <View style={styles.cabinetLegs}>
              <View style={[styles.leg, { backgroundColor: game.colors[0] }]} />
              <View style={[styles.leg, { backgroundColor: game.colors[0] }]} />
            </View>
          </View>
        </GlassCard>
      </SquishyButton>
    </Animated.View>
  );
};

export default function LoveArcadeHub({ navigation }: any) {
  const [totalScore, setTotalScore] = useState(0);
  const [fadeAnim] = useState(new Animated.Value(0));
  const [titleGlowAnim] = useState(new Animated.Value(0.6));
  const [showMarcie, setShowMarcie] = useState(true);

  // Get game info from registry for the hub
  const gameInfo = getGameByScreen('LoveArcadeHub');
  const GAME_ID = gameInfo?.id || 'love-arcade-hub';
  const CATEGORY_ID = gameInfo?.categoryId || 'love-arcade';
  
  // Backend session (for tracking hub visit/engagement)
  const {
    session,
    updateScore,
    completeGame,
    isLoading: sessionLoading,
    isSyncing,
    partnerProgress
  } = useGameSession(GAME_ID, CATEGORY_ID);

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: ANIMATIONS.duration.slow,
      useNativeDriver: true,
    }).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(titleGlowAnim, {
          toValue: 1,
          duration: ANIMATIONS.duration.slower,
          useNativeDriver: true,
        }),
        Animated.timing(titleGlowAnim, {
          toValue: 0.6,
          duration: ANIMATIONS.duration.slower,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const handleBackPress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    navigation?.goBack();
  };

  const handleGamePress = (game: any) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    const screenMap: Record<string, string> = {
      'truth-teller-tower': 'TruthTellerTower',
      'echo-chamber-escape': 'EscapeEchoChamber',
      'intimacy-feud': 'IntimacyFeud',
    };
    navigation?.navigate(screenMap[game.id] || 'MainGameLibrary');
  };

  // Loading state
  if (sessionLoading) {
    return (
      <ScreenLayout showMarcie={true} marcieQuote="Loading the arcade...">
        <View style={styles.loadingContainer}>
          <Typography variant="body" center>Entering Love Arcade...</Typography>
        </View>
      </ScreenLayout>
    );
  }

  return (
    <ScreenLayout showHeader={false} scrollable={false}>
      <LinearGradient 
        colors={[
          COLORS.arenaBgStart,
          COLORS.arenaBgEnd,
          COLORS.deepCosmicPurple
        ]}
        style={styles.backgroundGradient}
        start={GRADIENTS.background.start}
        end={GRADIENTS.background.end}
      >
        {/* Sync indicator */}
        {isSyncing && (
          <View style={styles.syncIndicator}>
            <Typography variant="caption" color={COLORS.success}>💾 Saving...</Typography>
          </View>
        )}
        
        <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
          {/* Header */}
          <View style={styles.header}>
            <SquishyButton variant="ghost" size="small" onPress={handleBackPress} style={styles.backButton}>
              <LinearGradient
                colors={GRADIENTS.avatarRing.colors}
                style={styles.backButtonGradient}
                start={GRADIENTS.avatarRing.start}
                end={GRADIENTS.avatarRing.end}
              >
                <Typography variant="h2" style={styles.backButtonText}>
                  ←
                </Typography>
              </LinearGradient>
            </SquishyButton>
            
            <View style={styles.headerCenter}>
              <Animated.View style={[styles.titleContainer, { opacity: titleGlowAnim }]}>
                <Typography variant="gameTitle" style={styles.arcadeTitle}>
                  🎮 The Love Arcade 🎮
                </Typography>
              </Animated.View>
              <Typography variant="caption" style={styles.arcadeSubtitle}>
                +100 Games to Deepen Connection
              </Typography>
            </View>
            
            <View style={styles.headerRight} />
          </View>

          {/* Dr. Marcie Intro */}
          <GlassCard style={styles.marcieIntro} variant="outlined">
            <Typography variant="sass" style={styles.marcieQuote}>
              "Welcome to the Love Arcade, you glorious disaster couple. We don't do 'safe spaces.' We do safe SCORES."
            </Typography>
            <Typography variant="label" style={styles.marcieSig}>
              — Dr. Marcie Liss, PhD in Calling It Like She Sees It
            </Typography>
          </GlassCard>

          {/* Leaderboard */}
          <View style={styles.leaderboard}>
            <GlassCard style={[styles.scoreBox, styles.neonBox]} variant="elevated">
              <Typography variant="caption" style={styles.scoreLabel}>
                Total Arcade Score
              </Typography>
              <Typography variant="gameTitle" style={styles.totalScore}>
                {totalScore}
              </Typography>
              <Typography variant="caption" style={styles.maxLabel}>
                / 2450 MAX
              </Typography>
            </GlassCard>
            <GlassCard style={[styles.badgesBox, styles.neonBox]} variant="elevated">
              <Typography variant="caption" style={styles.badgesLabel}>
                Badges Earned
              </Typography>
              <View style={styles.badgeRow}>
                <Typography variant="h1" style={styles.badge}>🏗️</Typography>
                <Typography variant="h1" style={styles.badge}>🪞</Typography>
                <Typography variant="h1" style={styles.badge}>🗡️</Typography>
                <Typography variant="h1" style={styles.badge}>🏰</Typography>
              </View>
            </GlassCard>
          </View>

          {/* Games List */}
          <ScrollView 
            style={styles.gamesList} 
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.gamesListContent}
          >
            <Typography variant="h2" style={styles.sectionTitle}>
              Championship Games
            </Typography>
            {ARCADE_GAMES.map((game, index) => (
              <ArcadeGameCard
                key={game.id}
                game={game}
                index={index}
                onPress={() => handleGamePress(game)}
              />
            ))}

            {/* Final Ritual Teaser */}
            <GlassCard style={styles.finalRitual} variant="outlined">
              <Typography variant="h1" style={styles.ritualIcon}>
                🔥
              </Typography>
              <Typography variant="h2" style={styles.ritualTitle}>
                The Digital Bonfire
              </Typography>
              <Typography variant="body" style={styles.ritualDesc}>
                Complete all 4 phases to unlock the Final Ritual. Burn the workbook. Rise from the ashes.
              </Typography>
            </GlassCard>

            <View style={{ height: SPACING.xxxlarge }} />
          </ScrollView>
        </Animated.View>
      </LinearGradient>

      {/* Dr. Marcie Overlay - Contextual during transitions */}
      <DrMarcieOverlay
        animation="intro"
        position="bottom-right"
        visible={showMarcie}
        quote="Ready to play? Pick a game and let's see what you're made of!"
        showBubble={true}
        bubbleDuration={6000}
      />
    </ScreenLayout>
  );
}

const styles = StyleSheet.create({
  backgroundGradient: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.screenPadding,
    paddingTop: SPACING.regular,
    paddingBottom: SPACING.regular,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.round,
    overflow: 'hidden',
    padding: SPACING.none,
  },
  backButtonGradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backButtonText: {
    color: COLORS.textPrimary,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerRight: {
    width: 40,
  },
  titleContainer: {
    marginBottom: SPACING.micro,
  },
  arcadeTitle: {
    color: COLORS.primaryGradientStart,
    textAlign: 'center',
    textShadowColor: COLORS.glowPink,
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 10,
  },
  arcadeSubtitle: {
    color: COLORS.textSecondary,
    textAlign: 'center',
    textTransform: 'uppercase',
  },
  marcieIntro: {
    marginHorizontal: SPACING.screenPadding,
    marginVertical: SPACING.regular,
    padding: SPACING.cardPadding,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primaryGradientStart,
  },
  marcieQuote: {
    color: COLORS.textPrimary,
    marginBottom: SPACING.small,
  },
  marcieSig: {
    color: COLORS.primaryGradientStart,
  },
  leaderboard: {
    flexDirection: 'row',
    marginHorizontal: SPACING.screenPadding,
    gap: SPACING.regular,
    marginBottom: SPACING.regular,
  },
  neonBox: {
    borderRadius: BORDER_RADIUS.card,
    borderWidth: 1,
    borderColor: COLORS.borderSubtle,
    ...SHADOWS.neonSoft,
  },
  scoreBox: {
    flex: 1,
    padding: SPACING.cardPadding,
    alignItems: 'center',
    backgroundColor: `${COLORS.brightYellow}10`,
  },
  badgesBox: {
    flex: 1,
    padding: SPACING.cardPadding,
    alignItems: 'center',
  },
  scoreLabel: {
    color: COLORS.textSecondary,
    marginBottom: SPACING.micro,
  },
  totalScore: {
    color: COLORS.brightYellow,
    textShadowColor: `${COLORS.brightYellow}80`,
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 8,
  },
  maxLabel: {
    color: COLORS.textHint,
  },
  badgesLabel: {
    color: COLORS.textSecondary,
    marginBottom: SPACING.small,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: SPACING.small,
  },
  badge: {
    textShadowColor: `${COLORS.textPrimary}30`,
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 4,
  },
  gamesList: {
    flex: 1,
  },
  gamesListContent: {
    paddingHorizontal: SPACING.screenPadding,
  },
  sectionTitle: {
    color: COLORS.textPrimary,
    marginBottom: SPACING.regular,
    textAlign: 'center',
  },
  arcadeCard: {
    marginBottom: SPACING.xlarge,
    borderRadius: BORDER_RADIUS.card,
    overflow: 'hidden',
  },
  cardTouchable: {
    flex: 1,
    padding: SPACING.none,
    backgroundColor: 'transparent',
    borderWidth: 0,
  },
  cabinetGlow: {
    position: 'absolute',
    top: -10,
    left: -10,
    right: -10,
    bottom: -10,
    borderRadius: BORDER_RADIUS.card + 10,
    ...SHADOWS.neonStrong,
  },
  cabinetBody: {
    borderRadius: BORDER_RADIUS.card,
    padding: SPACING.cardPadding,
    borderWidth: 2,
    borderColor: COLORS.borderSubtle,
  },
  cabinetFrame: {
    flex: 1,
    borderRadius: BORDER_RADIUS.medium,
    borderWidth: 1,
    padding: SPACING.regular,
    backgroundColor: `${COLORS.backgroundPrimary}20`,
  },
  gameScreen: {
    height: 120,
    borderRadius: BORDER_RADIUS.medium,
    overflow: 'hidden',
    marginBottom: SPACING.regular,
    borderWidth: 2,
    borderColor: COLORS.borderSubtle,
  },
  screenGradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  gameIcon: {
    fontSize: TYPOGRAPHY.fontSize.displayLarge,
  },
  marqueeContainer: {
    marginBottom: SPACING.small,
  },
  gameName: {
    textAlign: 'center',
    textTransform: 'uppercase',
  },
  phaseIndicator: {
    alignSelf: 'center',
    paddingHorizontal: SPACING.medium,
    paddingVertical: SPACING.micro,
    borderRadius: BORDER_RADIUS.small,
    marginBottom: SPACING.small,
  },
  phaseText: {
    color: COLORS.textPrimary,
  },
  gameDesc: {
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: SPACING.regular,
  },
  controlPanel: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: SPACING.regular,
  },
  scoreDisplay: {
    alignItems: 'center',
  },
  scoreValue: {
    fontWeight: '700',
  },
  cabinetLegs: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: SPACING.regular,
    paddingHorizontal: SPACING.xlarge,
  },
  leg: {
    width: 8,
    height: 20,
    borderRadius: BORDER_RADIUS.small,
  },
  finalRitual: {
    backgroundColor: `${COLORS.crimsonRed}10`,
    borderRadius: BORDER_RADIUS.card,
    padding: SPACING.cardPadding,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: `${COLORS.crimsonRed}30`,
    marginTop: SPACING.xlarge,
  },
  ritualIcon: {
    marginBottom: SPACING.small,
  },
  ritualTitle: {
    color: COLORS.primaryGradientStart,
    textAlign: 'center',
    marginBottom: SPACING.small,
  },
  ritualDesc: {
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  syncIndicator: {
    position: 'absolute',
    top: SPACING.small,
    right: SPACING.small,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: SPACING.small,
    paddingVertical: SPACING.tiny,
    borderRadius: BORDER_RADIUS.small,
    zIndex: 1000,
  },
});
