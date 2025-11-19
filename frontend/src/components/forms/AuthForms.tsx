import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../ui/Button';
import { Input, PasswordField } from '../ui/Input';
import { useAuthStore } from '../../stores/authStore';
import { validateEmail, validatePassword } from '../../utils';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  username: z.string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters')
    .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
      'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'),
  confirmPassword: z.string(),
  full_name: z.string().min(1, 'Full name is required'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type LoginFormData = z.infer<typeof loginSchema>;
type RegisterFormData = z.infer<typeof registerSchema>;

interface LoginFormProps {
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const navigate = useNavigate();
  const { login, isLoading, error } = useAuthStore();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setFormError(null);
      await login(data);
      onSuccess?.();
      navigate('/dashboard');
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Username or Email"
          placeholder="Enter your username or email"
          error={errors.username?.message}
          {...register('username')}
        />

        <PasswordField
          label="Password"
          placeholder="Enter your password"
          error={errors.password?.message}
          {...register('password')}
        />

        {(formError || error) && (
          <div className="text-red-600 text-sm">
            {formError || error}
          </div>
        )}

        <Button
          type="submit"
          fullWidth
          loading={isLoading}
          className="mt-6"
        >
          Sign In
        </Button>
      </form>

      <div className="text-center">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Don't have an account?{' '}
          <Link
            to="/auth/register"
            className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
};

interface RegisterFormProps {
  onSuccess?: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess }) => {
  const navigate = useNavigate();
  const { register: registerUser, isLoading, error } = useAuthStore();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const password = watch('password');

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setFormError(null);
      const { confirmPassword, ...registerData } = data;
      await registerUser(registerData);
      onSuccess?.();
      navigate('/dashboard');
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Registration failed');
    }
  };

  const getPasswordStrength = (password: string) => {
    if (!password) return { strength: 0, label: '' };
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[@$!%*?&]/.test(password)) strength++;

    const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
    return { strength, label: labels[strength] || '' };
  };

  const passwordStrength = getPasswordStrength(password || '');

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Full Name"
          placeholder="Enter your full name"
          error={errors.full_name?.message}
          {...register('full_name')}
        />

        <Input
          label="Email"
          type="email"
          placeholder="Enter your email"
          error={errors.email?.message}
          {...register('email')}
        />

        <Input
          label="Username"
          placeholder="Choose a username"
          error={errors.username?.message}
          {...register('username')}
        />

        <div>
          <PasswordField
            label="Password"
            placeholder="Create a password"
            error={errors.password?.message}
            {...register('password')}
          />
          {password && (
            <div className="mt-2">
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      passwordStrength.strength <= 1 ? 'bg-red-500' :
                      passwordStrength.strength <= 2 ? 'bg-yellow-500' :
                      passwordStrength.strength <= 3 ? 'bg-blue-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${(passwordStrength.strength / 4) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600">
                  {passwordStrength.label}
                </span>
              </div>
            </div>
          )}
        </div>

        <PasswordField
          label="Confirm Password"
          placeholder="Confirm your password"
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />

        {(formError || error) && (
          <div className="text-red-600 text-sm">
            {formError || error}
          </div>
        )}

        <Button
          type="submit"
          fullWidth
          loading={isLoading}
          className="mt-6"
        >
          Create Account
        </Button>
      </form>

      <div className="text-center">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Already have an account?{' '}
          <Link
            to="/auth/login"
            className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};