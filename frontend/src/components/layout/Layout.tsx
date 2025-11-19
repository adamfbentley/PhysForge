import React, { useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import clsx from 'clsx';

interface LayoutProps {
  children: React.ReactNode;
  className?: string;
  showSidebar?: boolean;
  sidebarCollapsed?: boolean;
  onSidebarToggle?: () => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  className,
  showSidebar = true,
  sidebarCollapsed: initialCollapsed = false,
  onSidebarToggle,
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(initialCollapsed);

  const handleSidebarToggle = () => {
    const newCollapsed = !sidebarCollapsed;
    setSidebarCollapsed(newCollapsed);
    onSidebarToggle?.();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      <div className="flex">
        {showSidebar && (
          <Sidebar
            collapsed={sidebarCollapsed}
            onToggle={handleSidebarToggle}
          />
        )}

        <main className={clsx(
          'flex-1 transition-all duration-300',
          showSidebar && !sidebarCollapsed ? 'ml-0' : '',
          className
        )}>
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

// Auth Layout (no sidebar, centered content)
interface AuthLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children, className }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white dark:from-gray-900 dark:to-gray-800 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <h1 className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
            PhysForge
          </h1>
        </div>
        <h2 className="mt-6 text-center text-2xl font-bold text-gray-900 dark:text-white">
          Physics-Informed Scientific Discovery
        </h2>
      </div>

      <div className={clsx('mt-8 sm:mx-auto sm:w-full sm:max-w-md', className)}>
        <div className="bg-white dark:bg-gray-800 py-8 px-4 shadow-lg sm:rounded-lg sm:px-10 border border-gray-200 dark:border-gray-700">
          {children}
        </div>
      </div>
    </div>
  );
};