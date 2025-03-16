import { initializeApp, FirebaseApp } from 'firebase/app';
import { getMessaging, getToken, onMessage, Messaging } from 'firebase/messaging';
import { 
  getAuth, 
  GoogleAuthProvider, 
  signInWithPopup, 
  onAuthStateChanged, 
  User,
  signOut as firebaseSignOut
} from 'firebase/auth';

// Firebase configuration
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Initialize Firebase
let firebaseApp: FirebaseApp;
let messaging: Messaging;
let auth: ReturnType<typeof getAuth>;
let googleProvider: GoogleAuthProvider;

// Only initialize Firebase on the client side
if (typeof window !== 'undefined') {
  try {
    firebaseApp = initializeApp(firebaseConfig);
    
    // Initialize Firebase Cloud Messaging
    messaging = getMessaging(firebaseApp);
    
    // Initialize Firebase Authentication
    auth = getAuth(firebaseApp);
    googleProvider = new GoogleAuthProvider();
    
    // Register the service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/firebase-messaging-sw.js')
        .then((registration) => {
          console.log('Service Worker registered with scope:', registration.scope);
          
          // Pass the Firebase config to the service worker
          const serviceWorkerMessage = {
            type: 'INIT_FIREBASE',
            config: firebaseConfig
          };
          
          // Try to send the config to the service worker
          if (registration.active) {
            registration.active.postMessage(serviceWorkerMessage);
          }
          
          // Also listen for when the service worker becomes active
          navigator.serviceWorker.addEventListener('controllerchange', () => {
            if (navigator.serviceWorker.controller) {
              navigator.serviceWorker.controller.postMessage(serviceWorkerMessage);
            }
          });
        })
        .catch((err) => {
          console.error('Service Worker registration failed:', err);
        });
    }
    
    console.log('Firebase initialized successfully');
  } catch (error) {
    console.error('Error initializing Firebase:', error);
  }
}

// Request permission and get FCM token
export const requestNotificationPermission = async (userId: string) => {
  try {
    if (!messaging) {
      console.error('Firebase messaging is not initialized');
      return null;
    }
    
    // Check if permission is already granted
    if (Notification.permission === 'granted') {
      console.log('Notification permission already granted');
    } else {
      // Request permission
      const permission = await Notification.requestPermission();
      
      if (permission !== 'granted') {
        console.log('Notification permission not granted');
        return null;
      }
    }
    
    console.log('Getting FCM token...');
    
    // Get FCM token with retry
    let retries = 0;
    let currentToken = null;
    
    while (!currentToken && retries < 3) {
      try {
        currentToken = await getToken(messaging, {
          vapidKey: process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY,
        });
        
        if (!currentToken) {
          console.log(`No FCM token available, retry ${retries + 1}/3`);
          retries++;
          await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
        }
      } catch (error) {
        console.error(`Error getting FCM token on try ${retries + 1}/3:`, error);
        retries++;
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retry
      }
    }
    
    if (currentToken) {
      console.log('FCM token:', currentToken);
      
      // Subscribe to Mumbai hackathons topic
      const subscribed = await subscribeToTopic(currentToken, 'mumbai_hackathons');
      
      if (subscribed) {
        console.log('Successfully subscribed to mumbai_hackathons topic');
      } else {
        console.error('Failed to subscribe to mumbai_hackathons topic');
      }
      
      return currentToken;
    } else {
      console.error('Failed to get FCM token after 3 retries');
      return null;
    }
  } catch (error) {
    console.error('Error requesting notification permission:', error);
    return null;
  }
};

// Subscribe to a topic
export const subscribeToTopic = async (token: string, topic: string) => {
  try {
    // In a real implementation, your backend would handle this
    // This is just a placeholder - you'll need to implement a backend API endpoint for this
    console.log(`Subscribing token ${token} to topic ${topic}`);
    
    // Call your backend API to subscribe
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
    const response = await fetch(`${apiUrl}/notifications/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token,
        topic,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to subscribe to topic: ${response.statusText}`);
    }
    
    return true;
  } catch (error) {
    console.error('Error subscribing to topic:', error);
    return false;
  }
};

// Handle foreground messages
export const onForegroundMessage = (callback: (payload: any) => void) => {
  if (!messaging) {
    console.error('Firebase messaging is not initialized');
    return;
  }
  
  return onMessage(messaging, (payload) => {
    console.log('Foreground message received:', payload);
    callback(payload);
  });
};

// Google sign in
export const signInWithGoogle = async () => {
  if (!auth || !googleProvider) {
    console.error('Firebase auth is not initialized');
    return null;
  }
  
  try {
    const result = await signInWithPopup(auth, googleProvider);
    return result.user;
  } catch (error) {
    console.error('Error signing in with Google:', error);
    return null;
  }
};

// Sign out
export const signOut = async () => {
  if (!auth) {
    console.error('Firebase auth is not initialized');
    return false;
  }
  
  try {
    await firebaseSignOut(auth);
    return true;
  } catch (error) {
    console.error('Error signing out:', error);
    return false;
  }
};

// Get current user
export const getCurrentUser = (): User | null => {
  if (!auth) {
    console.error('Firebase auth is not initialized');
    return null;
  }
  
  return auth.currentUser;
};

// Subscribe to auth state changes
export const onAuthChange = (callback: (user: User | null) => void) => {
  if (!auth) {
    console.error('Firebase auth is not initialized');
    return () => {};
  }
  
  return onAuthStateChanged(auth, callback);
};

export { firebaseApp, messaging, auth };