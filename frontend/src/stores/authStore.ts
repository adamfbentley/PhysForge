import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, LoginCredentials, RegisterCredentials, AuthTokens } from '../types';
import { STORAGE_KEYS } from '../constants';

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  setUser: (user: User) => void;
  setTokens: (tokens: AuthTokens) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
          });

          if (!response.ok) {
            throw new Error('Login failed');
          }

          const data = await response.json();
          const tokens: AuthTokens = {
            access_token: data.access_token,
            refresh_token: data.refresh_token,
            token_type: data.token_type,
          };

          // Get user info
          const userResponse = await fetch(`${process.env.REACT_APP_API_BASE_URL}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${tokens.access_token}`,
            },
          });

          if (!userResponse.ok) {
            throw new Error('Failed to get user info');
          }

          const user: User = await userResponse.json();

          set({
            user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Login failed',
          });
          throw error;
        }
      },

      register: async (credentials: RegisterCredentials) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
          });

          if (!response.ok) {
            throw new Error('Registration failed');
          }

          const data = await response.json();
          const tokens: AuthTokens = {
            access_token: data.access_token,
            refresh_token: data.refresh_token,
            token_type: data.token_type,
          };

          const user: User = data.user;

          set({
            user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Registration failed',
          });
          throw error;
        }
      },

      logout: () => {
        set({
          user: null,
          tokens: null,
          isAuthenticated: false,
          error: null,
        });
      },

      refreshToken: async () => {
        const { tokens } = get();
        if (!tokens?.refresh_token) {
          throw new Error('No refresh token available');
        }

        try {
          const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              refresh_token: tokens.refresh_token,
            }),
          });

          if (!response.ok) {
            throw new Error('Token refresh failed');
          }

          const data = await response.json();
          const newTokens: AuthTokens = {
            access_token: data.access_token,
            refresh_token: data.refresh_token || tokens.refresh_token,
            token_type: data.token_type,
          };

          set({ tokens: newTokens });
          return newTokens.access_token;
        } catch (error) {
          // If refresh fails, logout
          get().logout();
          throw error;
        }
      },

      setUser: (user: User) => set({ user }),
      setTokens: (tokens: AuthTokens) => set({ tokens, isAuthenticated: true }),
      setLoading: (loading: boolean) => set({ isLoading: loading }),
      setError: (error: string | null) => set({ error }),

      clearAuth: () => set({
        user: null,
        tokens: null,
        isAuthenticated: false,
        error: null,
      }),
    }),
    {
      name: STORAGE_KEYS.AUTH_TOKEN,
      partialize: (state) => ({
        tokens: state.tokens,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);