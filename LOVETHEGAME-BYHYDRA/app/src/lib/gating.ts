
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAppStore } from '../state/store';
import SHA256 from 'crypto-js/sha256';
import { firebaseAuth, firestore } from './firebaseClient';
import { doc, updateDoc } from 'firebase/firestore';

const STATIC_CODES = ['MARCIEBETA', 'LOVEBETA2025', 'TABSIMONBETA'];

export async function validateBetaCode(code: string, email?: string): Promise<boolean> {
  const normalizedCode = code.trim().toUpperCase();
  
  // Check static codes
  if (STATIC_CODES.includes(normalizedCode)) {
    return true;
  }

  // Check email-based codes
  if (email && normalizedCode.startsWith('BETATESTER')) {
    const emailHash = SHA256(email.toLowerCase().trim()).toString();
    const expectedCode = `BETATESTER${emailHash.substring(0, 8).toUpperCase()}`;
    if (normalizedCode === expectedCode) {
      return true;
    }
  }
  
  return false;
}

export async function activateBeta(code: string, email?: string) {
  const isValid = await validateBetaCode(code, email);
  if (isValid) {
    await AsyncStorage.setItem('beta_active', 'true');
    await AsyncStorage.setItem('beta_code', code);
    
    // Update profile in Firebase if user is logged in
    const user = firebaseAuth.currentUser;
    if (user) {
        const userDocRef = doc(firestore, 'users', user.uid);
        await updateDoc(userDocRef, {
            is_beta: true, 
            beta_code: code 
        });
    }
    
    return true;
  }
  return false;
}

export async function isBetaActive() {
  const v = await AsyncStorage.getItem('beta_active');
  return v === 'true';
}

export function useAccess() {
  const plan = useAppStore((s) => s.plan);
  const isBeta = useAppStore((s) => s.isBeta);
  const previewRole = useAppStore((s) => s.previewRole);

  if (previewRole) {
    return {
      plan: previewRole === 'blocked' ? 'free' : previewRole,
      isBeta: previewRole === 'beta',
      isPremium: previewRole === 'premium' || previewRole === 'beta',
      isBlocked: previewRole === 'blocked',
    };
  }

  return { plan, isBeta, isPremium: plan === 'premium' || isBeta, isBlocked: false };
}
