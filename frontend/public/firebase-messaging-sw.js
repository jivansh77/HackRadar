// Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here.
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Log when the service worker is installed and activated
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installation successful');
  // Force the waiting service worker to become the active service worker
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activation successful');
  // Take control of all clients as soon as the service worker becomes active
  event.waitUntil(clients.claim());
});

// Initialize the Firebase app in the service worker
// We'll use a self-executing function to get the config from the main app
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Received message:', event.data);
  if (event.data && event.data.type === 'INIT_FIREBASE') {
    const firebaseConfig = event.data.config;
    
    console.log('[Service Worker] Initializing Firebase with config');
    
    try {
      // Initialize Firebase
      firebase.initializeApp(firebaseConfig);
      
      // Retrieve an instance of Firebase Messaging so that it can handle background messages
      const messaging = firebase.messaging();
      console.log('[Service Worker] Firebase Messaging initialized');
      
      // Handle background messages
      messaging.onBackgroundMessage((payload) => {
        console.log('[Service Worker] Received background message:', payload);
        
        // Customize notification here
        const notificationTitle = payload.notification?.title || 'New Hackathon Notification';
        const notificationOptions = {
          body: payload.notification?.body || 'Check out the latest hackathons!',
          icon: '/logo2.png', // Add path to your notification icon
          tag: 'hackathon-notification', // Added tag to group similar notifications
          data: payload.data || {}
        };
      
        console.log('[Service Worker] Showing notification:', notificationTitle, notificationOptions);
        return self.registration.showNotification(notificationTitle, notificationOptions)
          .then(() => {
            console.log('[Service Worker] Notification displayed successfully');
          })
          .catch(error => {
            console.error('[Service Worker] Error showing notification:', error);
          });
      });
    } catch (error) {
      console.error('[Service Worker] Error initializing Firebase:', error);
    }
  }
});

// Also listen for push events directly
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received:', event);
  
  let notificationData;
  
  try {
    if (event.data) {
      notificationData = event.data.json();
      console.log('[Service Worker] Push payload:', notificationData);
    } else {
      console.log('[Service Worker] Push event had no data');
      notificationData = {};
    }
  } catch (e) {
    console.error('[Service Worker] Error parsing push data:', e);
    notificationData = {
      notification: {
        title: 'New Notification',
        body: event.data ? event.data.text() : 'Check the latest updates!'
      }
    };
  }
  
  // Extract notification content
  const title = notificationData.notification?.title || 
                'New Hackathon Notification';
  
  const options = {
    body: notificationData.notification?.body || 
          'Check out the latest hackathons!',
    icon: '/logo2.png',
    badge: '/badge.png',
    tag: 'hackathon-notification',
    data: notificationData.data || {},
    requireInteraction: true, // Keep the notification until user interacts with it
    actions: [
      {
        action: 'view',
        title: 'View Details'
      }
    ]
  };
  
  console.log('[Service Worker] Preparing to show notification:', title, options);
  
  // Show notification
  event.waitUntil(
    self.registration.showNotification(title, options)
      .then(() => {
        console.log('[Service Worker] Notification displayed successfully');
      })
      .catch(error => {
        console.error('[Service Worker] Error showing notification:', error);
      })
  );
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked:', event);
  
  // Close the notification
  event.notification.close();
  
  // Handle actions
  if (event.action === 'view' && event.notification.data?.url) {
    // Open specific URL if available
    const urlToOpen = event.notification.data.url;
    console.log('[Service Worker] Opening URL:', urlToOpen);
    
    event.waitUntil(
      clients.openWindow(urlToOpen)
    );
  } else {
    // Default: open main app
    event.waitUntil(
      clients.matchAll({type: 'window', includeUncontrolled: true})
        .then((clientList) => {
          // Check if there's already a window open
          for (const client of clientList) {
            if (client.url.includes(self.location.origin) && 'focus' in client) {
              return client.focus();
            }
          }
          
          // If no window is open, open a new one
          if (clients.openWindow) {
            return clients.openWindow('/hackathons');
          }
        })
    );
  }
}); 