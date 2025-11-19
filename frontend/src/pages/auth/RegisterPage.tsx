import React from 'react';
import { AuthLayout } from '../../components/layout/Layout';
import { RegisterForm } from '../../components/forms/AuthForms';

const RegisterPage: React.FC = () => {
  return (
    <AuthLayout>
      <div>
        <h2 className="text-center text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Create your account
        </h2>
        <p className="text-center text-sm text-gray-600 dark:text-gray-400 mb-6">
          Join the physics-informed scientific discovery platform
        </p>
        <RegisterForm />
      </div>
    </AuthLayout>
  );
};

export default RegisterPage;