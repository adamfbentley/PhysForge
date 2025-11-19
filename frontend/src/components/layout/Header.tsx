import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { IconLogout, IconUser, IconBell, IconSettings } from '@tabler/icons-react';
import { Menu, Button, Indicator } from '@mantine/core';
import { useAuthStore } from '../../stores/authStore';
import { useNotificationsStore } from '../../stores/notificationsStore';

interface HeaderProps {
  className?: string;
}

export const Header: React.FC<HeaderProps> = ({ className }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { unreadCount } = useNotificationsStore();

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  return (
    <header className={`bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                PhysForge
              </h1>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex space-x-8">
            <Link
              to="/dashboard"
              className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 text-sm font-medium transition-colors"
            >
              Dashboard
            </Link>
            <Link
              to="/datasets"
              className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 text-sm font-medium transition-colors"
            >
              Datasets
            </Link>
            <Link
              to="/jobs"
              className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 text-sm font-medium transition-colors"
            >
              Jobs
            </Link>
            <Link
              to="/results"
              className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 text-sm font-medium transition-colors"
            >
              Results
            </Link>
          </nav>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <Button variant="subtle" size="sm" className="relative">
              <Indicator disabled={unreadCount === 0} label={unreadCount} size={16}>
                <IconBell size={20} />
              </Indicator>
            </Button>

            {/* User Menu */}
            <Menu shadow="md" width={200}>
              <Menu.Target>
                <Button variant="subtle" size="sm" className="flex items-center space-x-2">
                  <IconUser size={20} />
                  <span className="hidden sm:block text-sm">{user?.username}</span>
                </Button>
              </Menu.Target>

              <Menu.Dropdown>
                <Menu.Label>Account</Menu.Label>
                <Menu.Item icon={<IconUser size={14} />}>
                  Profile
                </Menu.Item>
                <Menu.Item icon={<IconSettings size={14} />}>
                  Settings
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item
                  icon={<IconLogout size={14} />}
                  onClick={handleLogout}
                  color="red"
                >
                  Logout
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </div>
        </div>
      </div>
    </header>
  );
};