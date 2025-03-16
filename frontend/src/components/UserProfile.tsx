"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { 
  BellIcon, 
  BellOffIcon,
  LogOutIcon, 
  UserIcon 
} from "lucide-react";
import Link from "next/link";

export default function UserProfile() {
  const { user, loading, signOut, enableNotifications } = useAuth();
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  
  // Check if notifications are enabled on component mount
  useEffect(() => {
    if (typeof Notification !== 'undefined') {
      setNotificationsEnabled(Notification.permission === 'granted');
    }
  }, []);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setShowMenu(false);
    };

    if (showMenu) {
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showMenu]);

  const handleEnableNotifications = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await enableNotifications();
      setNotificationsEnabled(true);
      // Show success notification
      console.log("Notifications enabled successfully");
    } catch (error) {
      // Show error notification
      console.error("Error enabling notifications");
    }
  };

  const toggleMenu = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(!showMenu);
  };

  if (loading) {
    return (
      <div className="flex items-center space-x-2 animate-pulse">
        <div className="w-10 h-10 rounded-full bg-gray-200"></div>
        <div className="h-4 w-24 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <Button asChild size="sm" className="font-medium shadow-sm hover:shadow-md transition-all duration-300">
        <Link href="/login" className="flex items-center gap-2">
          <UserIcon className="h-4 w-4" />
          Sign In
        </Link>
      </Button>
    );
  }

  const userInitials = user.displayName
    ? user.displayName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : "U";

  return (
    <div className="flex items-center space-x-3">
      <Button
        onClick={handleEnableNotifications}
        variant={notificationsEnabled ? "ghost" : "outline"}
        size="icon"
        className="transition-all duration-300 hover:scale-105 relative"
        title={notificationsEnabled ? "Notifications enabled" : "Enable notifications"}
      >
        {notificationsEnabled && (
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full" />
        )}
        {notificationsEnabled ? (
          <BellIcon className="h-4 w-4 text-green-500" />
        ) : (
          <BellOffIcon className="h-4 w-4" />
        )}
      </Button>
      
      <div className="relative">
        <Button 
          variant="ghost" 
          className="p-0 h-auto hover:bg-transparent"
          onClick={toggleMenu}
        >
          <div className="flex items-center gap-2 p-1 hover:bg-accent rounded-lg transition-all duration-300">
            <Avatar className="h-9 w-9 border-2 border-transparent hover:border-primary transition-all duration-300">
              {user.photoURL ? (
                <AvatarImage 
                  src={user.photoURL} 
                  alt={user.displayName || "User"}
                  className="object-cover"
                />
              ) : (
                <AvatarFallback className="bg-gradient-to-br from-primary to-primary/80 text-white">
                  {userInitials}
                </AvatarFallback>
              )}
            </Avatar>
            <span className="text-sm font-medium max-w-[120px] truncate">
              {user.displayName || "User"}
            </span>
          </div>
        </Button>
        
        {showMenu && (
          <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 z-50 animate-in fade-in slide-in-from-top-5 duration-200">
            <div className="py-2 px-4">
              <div className="flex flex-col py-2">
                <span className="text-sm font-semibold">{user.displayName}</span>
                <span className="text-xs text-gray-500 dark:text-gray-400 truncate">{user.email}</span>
              </div>
              
              <div className="h-px bg-gray-200 dark:bg-gray-700 my-2"></div>
              
              <Link
                href="/profile"
                className="flex items-center gap-2 px-2 py-2 text-sm rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                onClick={() => setShowMenu(false)}
              >
                <UserIcon className="h-4 w-4" />
                <span>My Profile</span>
              </Link>
              
              <button
                onClick={signOut}
                className="w-full mt-1 flex items-center gap-2 px-2 py-2 text-sm text-red-600 rounded-md hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
              >
                <LogOutIcon className="h-4 w-4" />
                <span>Sign out</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 