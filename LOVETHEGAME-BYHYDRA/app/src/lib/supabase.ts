/**
 * Supabase-compatible data layer for Love Actually - The Game
 *
 * Screens were written against the Supabase JS API (auth.getSession,
 * from().select().eq().single(), realtime channels, etc). This module is a
 * drop-in compatibility layer backed by the platform's real stack:
 *
 *  - Auth        -> Firebase Auth (src/lib/firebaseClient)
 *  - Data        -> Firebase Firestore, using the SAME collections the
 *                   FastAPI backend reads/writes (users, couples,
 *                   game_sessions, fights, sos_sessions)
 *  - Realtime    -> Firestore onSnapshot / channel shims
 *  - Couple link -> Firestore transaction (mirrors backend /couples/link)
 *
 * When Firebase is not configured (dev/mock mode) every operation degrades
 * gracefully to empty results so screens render instead of crashing.
 */

import {
  collection,
  doc,
  getDocs,
  query,
  where,
  limit as fsLimit,
  addDoc,
  setDoc,
  runTransaction,
  onSnapshot,
} from 'firebase/firestore';
import { sendPasswordResetEmail, type User as FirebaseUser } from 'firebase/auth';
import { auth, db, isFirebaseConfigured } from './firebaseClient';
import { coupleApi, gamesApi } from './api';

// ============================================================================
// Types
// ============================================================================

export interface Game {
  name: string;
  category: string;
  difficulty: string;
  xp: number;
  description: string;
  mechanics: string;
  marcieIntro: string;
  id?: string;
}

export interface Profile {
  user_id?: string;
  id?: string;
  couple_code?: string | null;
  partner_id?: string | null;
  couple_id?: string | null;
  sarcasm_level?: number;
  personality?: string;
  plan?: string;
  beta_code?: string;
  beta_active?: boolean;
  preview_mode?: boolean;
  origin_story?: string;
  first_red_flag?: string;
  relationship_score?: number;
}

type Result = { data: any; error: any };

// ============================================================================
// Table mapping: supabase table name -> Firestore collection
// ============================================================================

const TABLE_MAP: Record<string, string> = {
  profiles: 'users',
  fights: 'fights',
  game_sessions: 'game_sessions',
  analytics: 'analytics_events',
  feedback_events: 'feedback_events',
  experiments: 'experiments',
};

function resolveCollection(table: string): string {
  return TABLE_MAP[table] || table;
}

// ============================================================================
// Auth helpers
// ============================================================================

function mapFirebaseUser(u: any): any {
  return {
    id: u.uid,
    uid: u.uid,
    email: u.email,
    app_metadata: { plan: u?.customClaims?.plan || 'free' },
    getIdToken: () => u.getIdToken(),
  };
}

/**
 * Resolve the current Firebase user, waiting for auth state to restore when
 * needed (Firebase restores the session asynchronously after cold start).
 */
function getFirebaseUser(): Promise<FirebaseUser | null> {
  if (!isFirebaseConfigured) {
    return new Promise<FirebaseUser | null>((resolve) => {
      const unsub = (auth as any).onAuthStateChanged((u: any) => {
        if (unsub) {
          try {
            unsub();
          } catch {
            /* already unsubscribed */
          }
        }
        resolve(u || null);
      });
    });
  }
  if (auth.currentUser) {
    return Promise.resolve(auth.currentUser);
  }
  return new Promise<FirebaseUser | null>((resolve) => {
    const unsub = auth.onAuthStateChanged((u) => {
      if (unsub) {
        try {
          unsub();
        } catch {
          /* already unsubscribed */
        }
      }
      resolve(u || null);
    });
  });
}

// ============================================================================
// Query builder (supabase .select().eq().single() shape, Firestore-backed)
// ============================================================================

type Filter = { field: string; op: '==' | '!=' | 'range'; value: any };

function docToRow(docSnap: any): any {
  const data = docSnap.data ? docSnap.data() : docSnap;
  return { ...data, id: docSnap.id };
}

class QueryBuilder implements PromiseLike<Result> {
  private filters: Filter[] = [];
  private limitVal: number | null = null;
  private singleResult = false;

  constructor(private table: string) {}

  select(_cols?: string): this {
    return this;
  }

  eq(field: string, value: any): this {
    this.filters.push({ field, op: '==', value });
    return this;
  }

  neq(field: string, value: any): this {
    this.filters.push({ field, op: '!=', value });
    return this;
  }

  not(field: string, op: string, value: any): this {
    this.filters.push({ field, op: op === 'eq' ? '!=' : '==', value });
    return this;
  }

  limit(n: number): this {
    this.limitVal = n;
    return this;
  }

  order(): this {
    return this;
  }

  single(): this {
    this.singleResult = true;
    return this;
  }

  insert(obj: any): PromiseLike<Result> {
    return toThenable(this.doInsert(obj));
  }

  private async doInsert(obj: any): Promise<Result> {
    if (!isFirebaseConfigured) {
      return { data: { ...obj, id: `mock-${Date.now()}` }, error: null };
    }
    try {
      const col = resolveCollection(this.table);
      let ref: any;
      if (obj && obj.id) {
        ref = doc(db, col, String(obj.id));
        await setDoc(ref, obj, { merge: true });
      } else {
        ref = await addDoc(collection(db, col), obj);
      }
      return { data: { ...obj, id: ref.id }, error: null };
    } catch (error) {
      return { data: null, error };
    }
  }

  private async execute(): Promise<Result> {
    if (!isFirebaseConfigured) {
      const empty: any = this.singleResult ? {} : [];
      return { data: empty, error: null };
    }
    try {
      const col = resolveCollection(this.table);

      // Direct doc read when filtering by id + single.
      const idFilter = this.filters.find((f) => f.field === 'id' && f.op === '==' && this.singleResult);
      if (idFilter && this.filters.length === 1) {
        const snap = await getDocs(query(collection(db, col), where('__name__', '==', String(idFilter.value))));
        const docSnap = snap.docs[0];
        if (!docSnap) return { data: null, error: null };
        return { data: docToRow(docSnap), error: null };
      }

      // Apply == / range filters to the Firestore query; != filters in JS to
      // avoid composite index requirements.
      const eqFilters = this.filters.filter((f) => f.op !== '!=');
      const neqFilters = this.filters.filter((f) => f.op === '!=');

      const constraints: any[] = eqFilters.map((f) => {
        if (f.field === 'id') return where('__name__', '==', String(f.value));
        return where(f.field, f.op as any, f.value);
      });
      if (this.limitVal && neqFilters.length === 0) {
        constraints.push(fsLimit(this.limitVal));
      }

      const base = query(collection(db, col), ...constraints);
      let snaps = await getDocs(base);
      let rows = snaps.docs.map(docToRow);

      if (neqFilters.length > 0) {
        rows = rows.filter((row) =>
          neqFilters.every((f) => row[f.field] !== f.value)
        );
        if (this.limitVal) rows = rows.slice(0, this.limitVal);
      }

      if (this.singleResult) {
        return { data: rows.length > 0 ? rows[0] : null, error: null };
      }
      return { data: rows, error: null };
    } catch (error) {
      return { data: null, error };
    }
  }

  then<TResult1 = Result, TResult2 = never>(
    onfulfilled?: (value: Result) => TResult1 | PromiseLike<TResult1>,
    onrejected?: (reason: any) => TResult2 | PromiseLike<TResult2>
  ): Promise<TResult1 | TResult2> {
    return this.execute().then(onfulfilled, onrejected);
  }
}

function toThenable<T>(promise: Promise<T>): PromiseLike<T> {
  return {
    then: (res?: (v: T) => any, rej?: (e: any) => any) => promise.then(res, rej),
  };
}

// ============================================================================
// Realtime subscriptions
// ============================================================================

interface Channel {
  unsubscribe: () => void;
}

function onUserProfileChanged(userId: string, cb: () => void): Channel {
  if (!isFirebaseConfigured) {
    return { unsubscribe: () => {} };
  }
  try {
    const unsub = onSnapshot(doc(db, 'users', userId), () => cb());
    return { unsubscribe: unsub };
  } catch (error) {
    return { unsubscribe: () => {} };
  }
}

function parseFilter(filter?: string): { field?: string; op?: string; value?: string } {
  if (!filter) return {};
  const match = /^([a-z_]+)=eq\.(.+)$/.exec(filter);
  if (!match) return {};
  return { field: match[1], op: 'eq', value: match[2] };
}

function watchGameSessionTable(filter?: string, cb?: (payload: any) => void): Channel {
  if (!isFirebaseConfigured) {
    return { unsubscribe: () => {} };
  }
  const parsed = parseFilter(filter);
  try {
    let q: any = collection(db, 'game_sessions');
    if (parsed.field) {
      q = query(q, where(parsed.field, '==', parsed.value));
    }
    const unsub = onSnapshot(q, (snap: any) => {
      snap.docs.forEach((d: any) => {
        if (cb) cb({ new: docToRow(d) });
      });
    });
    return { unsubscribe: unsub };
  } catch (error) {
    return { unsubscribe: () => {} };
  }
}

function watchFight(fightId: string, cb: (payload: any) => void): Channel {
  if (!isFirebaseConfigured) {
    return { unsubscribe: () => {} };
  }
  try {
    const unsub = onSnapshot(doc(db, 'fights', fightId), (snap) => {
      if (!snap.exists()) return;
      cb({ new: docToRow(snap) });
    });
    return { unsubscribe: unsub };
  } catch (error) {
    return { unsubscribe: () => {} };
  }
}

// ============================================================================
// Supabase-shaped client
// ============================================================================

export const supabase = {
  auth: {
    getSession: async (): Promise<{ data: { session: { user: any } | null } }> => {
      const user = await getFirebaseUser();
      if (!user) return { data: { session: null } };
      return { data: { session: { user: mapFirebaseUser(user) } } };
    },

    onAuthStateChange: (cb: (event: string, session: any) => void) => {
      const unsub = (auth as any).onAuthStateChanged((u: any) => {
        const session = u ? { user: mapFirebaseUser(u) } : null;
        cb(u ? 'SIGNED_IN' : 'SIGNED_OUT', session);
      });
      return { data: { subscription: { unsubscribe: () => unsub() } } };
    },

    resetPassword: async (email: string, redirectTo?: string): Promise<void> => {
      if (!isFirebaseConfigured) return;
      const actionCodeSettings = redirectTo ? { url: redirectTo } : undefined;
      await sendPasswordResetEmail(auth, email, actionCodeSettings);
    },

    updateUser: async () => ({}),
    getUser: async () => ({ data: { user: null } }),
  },

  from: (table: string): QueryBuilder => new QueryBuilder(table),

  channel: (name: string) => ({
    on: (_event: string, opts: any, cb: (payload: any) => void) => ({
      subscribe: () => {
        if (opts?.table === 'game_sessions') {
          watchGameSessionTable(opts?.filter, cb);
        }
        return { unsubscribe: () => {} };
      },
    }),
  }),

  removeChannel: (channel: Channel | null | undefined) => {
    if (channel && typeof channel.unsubscribe === 'function') {
      channel.unsubscribe();
    }
  },

  rpc: async () => ({ data: null, error: null }),
  storage: { from: () => ({ upload: async () => ({ error: null }), getPublicUrl: () => ({ data: { publicUrl: '' } }) }) },
};

// ============================================================================
// Named data helpers (used by screens)
// ============================================================================

export async function getProfile(userId: string): Promise<{ data: Profile | null }> {
  if (!isFirebaseConfigured) return { data: null };
  try {
    const snap = await getDocs(query(collection(db, 'users'), where('__name__', '==', userId)));
    const row = snap.docs[0];
    if (!row) return { data: null };
    return { data: { ...row.data(), id: row.id, user_id: row.id } };
  } catch (error) {
    return { data: null };
  }
}

export async function upsertProfile(data: Partial<Profile> & { user_id: string }): Promise<void> {
  if (!isFirebaseConfigured) return;
  const { user_id, ...rest } = data;
  await setDoc(doc(db, 'users', user_id), { ...rest, user_id }, { merge: true });
}

export async function linkPartnersTransactional(
  userId: string,
  partnerUserId: string,
  coupleCode: string
): Promise<void> {
  if (!isFirebaseConfigured) return;
  await runTransaction(db, async (tx) => {
    const partnerRef = doc(db, 'users', partnerUserId);
    const partnerSnap = await tx.get(partnerRef);
    if (!partnerSnap.exists()) {
      throw new Error('Partner not found. Check the code and try again.');
    }
    const partner = partnerSnap.data();
    if (partner.partner_id && partner.partner_id !== userId) {
      throw new Error('Partner already linked to someone else.');
    }
    if (partner.couple_code && partner.couple_code !== coupleCode) {
      throw new Error('Couple code mismatch. Try again.');
    }

    const coupleRef = doc(collection(db, 'couples'));
    tx.set(coupleRef, {
      id: coupleRef.id,
      user1_id: userId,
      user2_id: partnerUserId,
      created_at: new Date().toISOString(),
      trust_meter: 0.5,
      vulnerability_meter: 0.5,
      romance_meter: 0.5,
      connection_meter: 0.5,
      total_points: 0,
      streak_days: 0,
      status: 'active',
      last_interaction: new Date().toISOString(),
    });

    tx.set(
      doc(db, 'users', userId),
      { partner_id: partnerUserId, couple_id: coupleRef.id, couple_code: coupleCode },
      { merge: true }
    );
    tx.set(
      partnerRef,
      { partner_id: userId, couple_id: coupleRef.id, couple_code: coupleCode },
      { merge: true }
    );
  });
}

export async function subscribeCouple(code: string, cb: () => void): Promise<Channel> {
  try {
    const user = await getFirebaseUser();
    if (!user) return { unsubscribe: () => {} };
    return onUserProfileChanged(user.uid, cb);
  } catch (error) {
    return { unsubscribe: () => {} };
  }
}

export async function subscribeFight(fightId: string, cb: (payload: any) => void): Promise<Channel> {
  return watchFight(fightId, cb);
}

export async function updateFight(fightId: string, updates: Record<string, any>): Promise<void> {
  if (!isFirebaseConfigured) return;
  await setDoc(doc(db, 'fights', fightId), updates, { merge: true });
}

export async function createGameSession(
  gameId: string,
  userId: string,
  coupleCode: string
): Promise<{ id: string }> {
  if (!isFirebaseConfigured) {
    return { id: `mock-session-${Date.now()}` };
  }
  const ref = await addDoc(collection(db, 'game_sessions'), {
    game_id: gameId,
    user_id: userId,
    couple_id: coupleCode,
    couple_code: coupleCode,
    started_at: new Date().toISOString(),
    completed: false,
    score: 0,
    status: 'active',
    responses: [],
  });
  return { id: ref.id };
}

export async function updateGameSession(
  sessionId: string,
  updates: { finished_at?: string; score?: number; state?: string }
): Promise<void> {
  if (!isFirebaseConfigured) return;
  await setDoc(doc(db, 'game_sessions', sessionId), updates, { merge: true });
}

export async function listGames(): Promise<Game[]> {
  try {
    const registry = await gamesApi.getRegistry();
    const games = registry?.games || {};
    return Object.entries(games).map(([id, g]: [string, any]) => ({
      id,
      name: g.name || id,
      category: g.category_name || g.category || 'general',
      difficulty: 'Medium',
      xp: g.max_score || 0,
      description: g.description || '',
      mechanics: '',
      marcieIntro: '',
    }));
  } catch (error) {
    return [];
  }
}

export async function resetPassword(email: string, redirectTo?: string): Promise<void> {
  await supabase.auth.resetPassword(email, redirectTo);
}

export default {
  supabase,
  getProfile,
  upsertProfile,
  linkPartnersTransactional,
  subscribeCouple,
  subscribeFight,
  updateFight,
  createGameSession,
  updateGameSession,
  listGames,
  resetPassword,
};
