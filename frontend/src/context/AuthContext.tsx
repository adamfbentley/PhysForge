import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { loginUser, registerUser, fetchCurrentUser, logoutUser, User, LoginData, RegisterData, AxiosError } from '../api/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface JwtPayload {
  exp: number;
  iat: number;
  sub: string;
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadUser = async () => {
      try {
        const currentUser = await fetchCurrentUser();
        setUser(currentUser);
      } catch (error) {
        console.log('No active session or failed to fetch user:', error);
        setUser(null);
      }
      finally {
        setLoading(false);
      }
    };
    loadUser();
  }, []);

  const login = async (data: LoginData) => {
    setLoading(true);
    try {
      const loggedInUser = await loginUser(data);
      setUser(loggedInUser);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (data: RegisterData) => {
    setLoading(true);
    try {
      await registerUser(data);
      await login({ username: data.email, password: data.password });
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await logoutUser();
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
