import React from 'react';
import { Card as MantineCard, CardProps as MantineCardProps } from '@mantine/core';
import clsx from 'clsx';

interface CardProps extends MantineCardProps {
  hover?: boolean;
  clickable?: boolean;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  hover = false,
  clickable = false,
  onClick,
  ...props
}) => {
  return (
    <MantineCard
      className={clsx(
        'transition-all duration-200',
        {
          'hover:shadow-lg hover:scale-105': hover,
          'cursor-pointer': clickable || onClick,
        },
        className
      )}
      onClick={onClick}
      {...props}
    >
      {children}
    </MantineCard>
  );
};

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className }) => (
  <div className={clsx('p-4 border-b border-gray-200 dark:border-gray-700', className)}>
    {children}
  </div>
);

interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
}

export const CardBody: React.FC<CardBodyProps> = ({ children, className }) => (
  <div className={clsx('p-4', className)}>
    {children}
  </div>
);

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const CardFooter: React.FC<CardFooterProps> = ({ children, className }) => (
  <div className={clsx('p-4 border-t border-gray-200 dark:border-gray-700', className)}>
    {children}
  </div>
);