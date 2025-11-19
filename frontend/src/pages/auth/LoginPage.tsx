import React from 'react';
import { AuthLayout } from '../components/layout/Layout';
import { LoginForm } from '../components/forms/AuthForms';

const LoginPage: React.FC = () => {
  return (
    <AuthLayout>
      <div>
        <h2 className="text-center text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Sign in to your account
        </h2>
        <p className="text-center text-sm text-gray-600 dark:text-gray-400 mb-6">
          Access your physics-informed scientific discovery platform
        </p>
        <LoginForm />
      </div>
    </AuthLayout>
  );
};

export default LoginPage;