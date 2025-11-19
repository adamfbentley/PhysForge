import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { Loading } from './ui/Loading';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  redirectTo?: string;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  requireAuth = true,
  redirectTo
}) => {
  const { isAuthenticated, isLoading } = useAuthStore();
  const location = useLocation();

  // Show loading while checking authentication
  if (isLoading) {
    return <Loading fullScreen text="Checking authentication..." />;
  }

  // If authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    const redirectPath = redirectTo || `/auth/login?redirect=${encodeURIComponent(location.pathname)}`;
    return <Navigate to={redirectPath} replace />;
  }

  // If authentication is not required but user is authenticated (e.g., login page)
  if (!requireAuth && isAuthenticated) {
    const redirectPath = redirectTo || '/dashboard';
    return <Navigate to={redirectPath} replace />;
  }

  return <>{children}</>;
};

// Admin guard for admin-only routes
interface AdminGuardProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export const AdminGuard: React.FC<AdminGuardProps> = ({
  children,
  redirectTo = '/dashboard'
}) => {
  const { user, isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <Loading fullScreen text="Checking permissions..." />;
  }

  if (!isAuthenticated || !user?.is_superuser) {
    return <Navigate to={redirectTo} replace />;
  }

  return <>{children}</>;
};

export default AuthGuard;
