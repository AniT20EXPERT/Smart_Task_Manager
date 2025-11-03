import { useEffect, useState } from 'react';

// Type definitions for the Electron API
interface ElectronAPI {
  getAppVersion: () => Promise<string>;
  getPlatform: () => Promise<string>;
  checkForUpdates: () => Promise<{ hasUpdate: boolean; version: string }>;
  onWindowMaximized: (callback: () => void) => void;
  onWindowUnmaximized: (callback: () => void) => void;
  onMenuNewTask: (callback: () => void) => void;
  showNotification: (title: string, body: string) => void;
  requestNotificationPermission: () => Promise<NotificationPermission>;
}

// Extend the Window interface to include our Electron API
declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

export const useElectron = () => {
  const [isElectron, setIsElectron] = useState(false);
  const [appVersion, setAppVersion] = useState<string>('');
  const [platform, setPlatform] = useState<string>('');

  useEffect(() => {
    // Check if we're running in Electron
    const checkElectron = async () => {
      if (window.electronAPI) {
        setIsElectron(true);
        
        try {
          const version = await window.electronAPI.getAppVersion();
          const platformInfo = await window.electronAPI.getPlatform();
          setAppVersion(version);
          setPlatform(platformInfo);
        } catch (error) {
          console.error('Error getting Electron info:', error);
        }
      }
    };

    checkElectron();
  }, []);

  const showNotification = (title: string, body: string) => {
    if (isElectron && window.electronAPI) {
      window.electronAPI.showNotification(title, body);
    } else {
      // Fallback for web version
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body });
      }
    }
  };

  const requestNotificationPermission = async (): Promise<NotificationPermission> => {
    if (isElectron && window.electronAPI) {
      return await window.electronAPI.requestNotificationPermission();
    } else {
      // Fallback for web version
      if ('Notification' in window) {
        return await Notification.requestPermission();
      }
      return 'denied';
    }
  };

  const checkForUpdates = async () => {
    if (isElectron && window.electronAPI) {
      try {
        return await window.electronAPI.checkForUpdates();
      } catch (error) {
        console.error('Error checking for updates:', error);
        return { hasUpdate: false, version: appVersion };
      }
    }
    return { hasUpdate: false, version: appVersion };
  };

  const setupMenuListeners = (onNewTask: () => void) => {
    if (isElectron && window.electronAPI) {
      window.electronAPI.onMenuNewTask(onNewTask);
    }
  };

  const setupWindowListeners = (onMaximized: () => void, onUnmaximized: () => void) => {
    if (isElectron && window.electronAPI) {
      window.electronAPI.onWindowMaximized(onMaximized);
      window.electronAPI.onWindowUnmaximized(onUnmaximized);
    }
  };

  return {
    isElectron,
    appVersion,
    platform,
    showNotification,
    requestNotificationPermission,
    checkForUpdates,
    setupMenuListeners,
    setupWindowListeners
  };
};
