import React from 'react';
import { TextInput, TextInputProps, PasswordInput, PasswordInputProps, Textarea, TextareaProps } from '@mantine/core';
import clsx from 'clsx';

interface InputProps extends Omit<TextInputProps, 'size'> {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  className,
  size = 'md',
  error,
  ...props
}) => {
  return (
    <TextInput
      size={size}
      error={error}
      className={clsx('transition-all duration-200', className)}
      {...props}
    />
  );
};

interface PasswordInputProps extends Omit<PasswordInputProps, 'size'> {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  error?: string;
}

export const PasswordField: React.FC<PasswordInputProps> = ({
  className,
  size = 'md',
  error,
  ...props
}) => {
  return (
    <PasswordInput
      size={size}
      error={error}
      className={clsx('transition-all duration-200', className)}
      {...props}
    />
  );
};

interface TextAreaProps extends Omit<TextareaProps, 'size'> {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  error?: string;
  rows?: number;
}

export const TextArea: React.FC<TextAreaProps> = ({
  className,
  size = 'md',
  error,
  rows = 4,
  ...props
}) => {
  return (
    <Textarea
      size={size}
      error={error}
      rows={rows}
      className={clsx('transition-all duration-200', className)}
      {...props}
    />
  );
};