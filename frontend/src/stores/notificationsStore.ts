import { create } from 'zustand';
import { NotificationItem } from '../types';

interface NotificationsState {
  notifications: NotificationItem[];
  unreadCount: number;

  // Actions
  addNotification: (notification: Omit<NotificationItem, 'id' | 'timestamp' | 'read'>) => void;
  removeNotification: (id: string) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;

  // Internal actions
  updateUnreadCount: () => void;
}

export const useNotificationsStore = create<NotificationsState>((set, get) => ({
  notifications: [],
  unreadCount: 0,

  addNotification: (notificationData) => {
    const notification: NotificationItem = {
      ...notificationData,
      id: `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      read: false,
    };

    set((state) => ({
      notifications: [notification, ...state.notifications],
    }));

    get().updateUnreadCount();
  },

  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter(n => n.id !== id),
    }));

    get().updateUnreadCount();
  },

  markAsRead: (id: string) => {
    set((state) => ({
      notifications: state.notifications.map(n =>
        n.id === id ? { ...n, read: true } : n
      ),
    }));

    get().updateUnreadCount();
  },

  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map(n => ({ ...n, read: true })),
    }));

    set({ unreadCount: 0 });
  },

  clearAll: () => {
    set({ notifications: [], unreadCount: 0 });
  },

  updateUnreadCount: () => {
    set((state) => ({
      unreadCount: state.notifications.filter(n => !n.read).length,
    }));
  },
}));