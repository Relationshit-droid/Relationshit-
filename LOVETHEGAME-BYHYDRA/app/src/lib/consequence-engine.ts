import * as Notifications from 'expo-notifications';
import AsyncStorage from '@react-native-async-storage/async-storage';

type ConsequenceState = {
  lastActive: number;
  romanceLockedUntil?: number;
};

export async function markActivity() {
  const state: ConsequenceState = { lastActive: Date.now() };
  await AsyncStorage.setItem('consequence_state', JSON.stringify(state));
}

export async function checkInactivityAndTrigger() {
  const beta = await AsyncStorage.getItem('beta_active');
  if (beta === 'true') return;
  const raw = await AsyncStorage.getItem('consequence_state');
  const now = Date.now();
  const st: ConsequenceState = raw ? JSON.parse(raw) : { lastActive: now };
  if (now - st.lastActive > 24 * 3600 * 1000) {
    await Notifications.requestPermissionsAsync();
    for (let i = 0; i < 5; i++) {
      await Notifications.scheduleNotificationAsync({ content: { title: 'Dr. Marcie', body: 'We need to talk.' }, trigger: { type: Notifications.SchedulableTriggerInputTypes.TIME_INTERVAL, seconds: 60 * (i + 1) } as any });
    }
    const until = now + 4 * 3600 * 1000;
    await AsyncStorage.setItem('consequence_state', JSON.stringify({ lastActive: st.lastActive, romanceLockedUntil: until }));
  }
}

export async function isRomanceLocked() {
  const beta = await AsyncStorage.getItem('beta_active');
  if (beta === 'true') return false;
  const raw = await AsyncStorage.getItem('consequence_state');
  const st: ConsequenceState = raw ? JSON.parse(raw) : { lastActive: Date.now() };
  return !!st.romanceLockedUntil && Date.now() < st.romanceLockedUntil;
}

export async function enforceSkipPenalty(hours = 1) {
  const beta = await AsyncStorage.getItem('beta_active');
  if (beta === 'true') return;
  const raw = await AsyncStorage.getItem('consequence_state');
  const st: ConsequenceState = raw ? JSON.parse(raw) : { lastActive: Date.now() };
  const until = Date.now() + hours * 3600 * 1000;
  await AsyncStorage.setItem('consequence_state', JSON.stringify({ ...st, romanceLockedUntil: until }));
  await Notifications.requestPermissionsAsync();
  await Notifications.scheduleNotificationAsync({ content: { title: 'Dr. Marcie', body: 'Skipping sets a short cooldown.' }, trigger: { seconds: 5 } as any });
}

// --- EXTENDED LOGIC ---

export type PenaltyType = 'wallpaper_swap' | 'notification_spam' | 'hub_lockout' | 'public_shame';

interface Penalty {
  type: PenaltyType;
  active: boolean;
  expiresAt: number;
  description: string;
}

const PENALTY_DEFS: Record<PenaltyType, Omit<Penalty, 'active' | 'expiresAt'>> = {
  wallpaper_swap: { type: 'wallpaper_swap', description: 'Your wallpaper is now a photo of your partner looking disappointed.' },
  notification_spam: { type: 'notification_spam', description: 'Receiving hourly reminders to "Do Better".' },
  hub_lockout: { type: 'hub_lockout', description: 'Access to Romance Hub denied until tasks completed.' },
  public_shame: { type: 'public_shame', description: 'Your avatar wears a "Timeout" hat on the leaderboard.' }
};

export async function getActivePenalties(): Promise<Penalty[]> {
  const raw = await AsyncStorage.getItem('active_penalties');
  const current: Penalty[] = raw ? JSON.parse(raw) : [];
  const now = Date.now();
  // Filter expired
  const active = current.filter(p => p.expiresAt > now);
  if (active.length !== current.length) {
    await AsyncStorage.setItem('active_penalties', JSON.stringify(active));
  }
  return active;
}

export async function triggerPenalty(type: PenaltyType, durationHours: number) {
  const active = await getActivePenalties();
  const existing = active.find(p => p.type === type);
  if (existing) {
    existing.expiresAt = Date.now() + durationHours * 3600000; // Extend
  } else {
    active.push({ ...PENALTY_DEFS[type], active: true, expiresAt: Date.now() + durationHours * 3600000 } as Penalty);
  }
  await AsyncStorage.setItem('active_penalties', JSON.stringify(active));
}

export async function clearPenalty(type: PenaltyType) {
  const active = await getActivePenalties();
  const filtered = active.filter(p => p.type !== type);
  await AsyncStorage.setItem('active_penalties', JSON.stringify(filtered));
}
