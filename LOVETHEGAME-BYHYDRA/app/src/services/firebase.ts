import { getFunctions } from 'firebase/functions';
import { app, isFirebaseConfigured } from '../lib/firebaseClient';

const mockFunctions = {
  httpsCallable: (_name: string) => async () => {
    throw new Error('Firebase Functions are not configured');
  },
};

export const functions: any = isFirebaseConfigured
  ? getFunctions(app)
  : mockFunctions;

export default functions;
