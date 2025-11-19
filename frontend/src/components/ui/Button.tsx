import React from 'react';
import { Button as MantineButton, ButtonProps as MantineButtonProps } from '@mantine/core';
import clsx from 'clsx';

interface ButtonProps extends Omit<MantineButtonProps, 'variant'> {
  variant?: 'filled' | 'outline' | 'light' | 'subtle' | 'gradient';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'filled',
  size = 'md',
  loading = false,
  fullWidth = false,
  disabled,
  ...props
}) => {
  return (
    <MantineButton
      variant={variant}
      size={size}
      loading={loading}
      disabled={disabled || loading}
      fullWidth={fullWidth}
      className={clsx(
        'transition-all duration-200',
        {
          'opacity-50 cursor-not-allowed': disabled || loading,
        },
        className
      )}
      {...props}
    >
      {children}
    </MantineButton>
  );
};