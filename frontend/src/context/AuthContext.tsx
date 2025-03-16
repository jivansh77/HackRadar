"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from 'firebase/auth';
import { onAuthChange, signInWithGoogle, signOut as firebaseSignOut, requestNotificationPermission } from '@/lib/firebase';
import { toast } from 'sonner';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
  enableNotifications: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signIn: async () => {},
  signOut: async () => {},
  enableNotifications: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthChange((user) => {
      setUser(user);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signIn = async () => {
    try {
      const user = await signInWithGoogle();
      if (user) {
        toast.success('Signed in successfully!');
        // After successful sign-in, request notification permissions
        requestNotificationPermission(user.uid)
          .then((token) => {
            if (token) {
              toast.success('Notifications enabled!');
            } else {
              toast.error('Failed to enable notifications. Please try again later.');
            }
          })
          .catch(() => {
            toast.error('Failed to enable notifications. Please try again later.');
          });
      } else {
        toast.error('Failed to sign in. Please try again.');
      }
    } catch (error) {
      console.error('Error signing in:', error);
      toast.error('Failed to sign in. Please try again.');
    }
  };

  const signOut = async () => {
    try {
      await firebaseSignOut();
      toast.success('Signed out successfully!');
    } catch (error) {
      console.error('Error signing out:', error);
      toast.error('Failed to sign out. Please try again.');
    }
  };

  const enableNotifications = async () => {
    if (!user) {
      toast.error('Please sign in to enable notifications.');
      return;
    }

    try {
      const token = await requestNotificationPermission(user.uid);
      if (token) {
        toast.success('Notifications enabled!');
      } else {
        toast.error('Failed to enable notifications. Please try again later.');
      }
    } catch (error) {
      console.error('Error enabling notifications:', error);
      toast.error('Failed to enable notifications. Please try again later.');
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut, enableNotifications }}>
      {children}
    </AuthContext.Provider>
  );
} 