import { initializeApp, FirebaseApp, getApp, getApps } from "firebase/app";
import { getAuth, Auth } from "firebase/auth";
import { getFirestore, Firestore } from "firebase/firestore";
import { getStorage, FirebaseStorage } from "firebase/storage";
import { ENV } from './env';

const firebaseConfig = {
  apiKey: ENV.FIREBASE_API_KEY,
  authDomain: ENV.FIREBASE_AUTH_DOMAIN,
  projectId: ENV.FIREBASE_PROJECT_ID,
  storageBucket: ENV.FIREBASE_STORAGE_BUCKET,
  messagingSenderId: ENV.FIREBASE_MESSAGING_SENDER_ID,
  appId: ENV.FIREBASE_APP_ID,
};

let app: FirebaseApp;
let auth: Auth;
let db: Firestore;
let storage: FirebaseStorage;

// Check if Firebase is properly configured
const isFirebaseConfigured = firebaseConfig.apiKey && firebaseConfig.apiKey.length > 0;

if (isFirebaseConfigured) {
  // Initialize Firebase only if config is present
  if (getApps().length === 0) {
    app = initializeApp(firebaseConfig);
  } else {
    app = getApp();
  }
  auth = getAuth(app);
  db = getFirestore(app);
  storage = getStorage(app);
} else {
  // Create mock objects when Firebase is not configured
  console.warn("Firebase not configured. Using mock objects for development.");

  // Create mock implementations
  app = {
    name: '[DEFAULT]',
    options: firebaseConfig,
    delete: async () => Promise.resolve()
  } as FirebaseApp;

  auth = {
    onAuthStateChanged: (callback: any) => {
      console.log("Mock Auth: Automatically logging in developer user");
      // Simulate a small delay then log in
      setTimeout(() => {
        callback({
          uid: 'dev-user-123',
          email: 'dev@lovetrae.app',
          displayName: 'Developer',
          getIdToken: async () => 'mock-token'
        });
      }, 500);
      return () => {}; // Return unsubscribe function
    },
    signOut: async () => {
      console.log("Mock Auth: Signing out");
      return Promise.resolve();
    }
  } as any;

  db = {
    // Minimal mock implementation
  } as Firestore;

  storage = {
    // Minimal mock implementation
  } as FirebaseStorage;
}

export { app, auth, db, storage, isFirebaseConfigured };