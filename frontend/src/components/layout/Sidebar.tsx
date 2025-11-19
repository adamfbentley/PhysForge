import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  IconDashboard,
  IconDatabase,
  IconCalculator,
  IconChartBar,
  IconSettings,
  IconShield,
  IconFileAnalytics
} from '@tabler/icons-react';
import clsx from 'clsx';

interface SidebarProps {
  className?: string;
  collapsed?: boolean;
  onToggle?: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  current?: boolean;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: IconDashboard },
  { name: 'Datasets', href: '/datasets', icon: IconDatabase },
  { name: 'Jobs', href: '/jobs', icon: IconCalculator },
  { name: 'Results', href: '/results', icon: IconChartBar },
  { name: 'Reports', href: '/reports', icon: IconFileAnalytics },
];

const adminNavigation: NavItem[] = [
  { name: 'Admin', href: '/admin', icon: IconShield },
  { name: 'Settings', href: '/settings', icon: IconSettings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  className,
  collapsed = false,
  onToggle
}) => {
  const location = useLocation();

  return (
    <div className={clsx(
      'flex flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300',
      collapsed ? 'w-16' : 'w-64',
      className
    )}>
      {/* Logo */}
      <div className="flex items-center justify-center h-16 px-4 border-b border-gray-200 dark:border-gray-700">
        <Link to="/" className="flex items-center">
          <div className="flex-shrink-0">
            <h1 className={clsx(
              'font-bold text-indigo-600 dark:text-indigo-400 transition-all',
              collapsed ? 'text-lg' : 'text-xl'
            )}>
              {collapsed ? 'PF' : 'PhysForge'}
            </h1>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {/* Main Navigation */}
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                  isActive
                    ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400'
                )}
              >
                <item.icon
                  size={20}
                  className={clsx(
                    'flex-shrink-0',
                    collapsed ? 'mx-auto' : 'mr-3'
                  )}
                />
                {!collapsed && (
                  <span className="truncate">{item.name}</span>
                )}
              </Link>
            );
          })}
        </div>

        {/* Admin Navigation */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="space-y-1">
            {adminNavigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                    isActive
                      ? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400'
                  )}
                >
                  <item.icon
                    size={20}
                    className={clsx(
                      'flex-shrink-0',
                      collapsed ? 'mx-auto' : 'mr-3'
                    )}
                  />
                  {!collapsed && (
                    <span className="truncate">{item.name}</span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Collapse Toggle */}
      {onToggle && (
        <div className="p-2 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onToggle}
            className="w-full flex items-center justify-center p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            <svg
              className={clsx(
                'w-5 h-5 transition-transform',
                collapsed ? 'rotate-180' : ''
              )}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};