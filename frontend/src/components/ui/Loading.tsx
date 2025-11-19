import React from 'react';
import { Loader, LoaderProps } from '@mantine/core';
import clsx from 'clsx';

interface LoadingProps extends Omit<LoaderProps, 'size'> {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  fullScreen?: boolean;
  className?: string;
}

export const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  text,
  fullScreen = false,
  className,
  ...props
}) => {
  const loader = (
    <div className={clsx('flex flex-col items-center justify-center gap-2', className)}>
      <Loader size={size} {...props} />
      {text && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{text}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white dark:bg-gray-900 bg-opacity-75 dark:bg-opacity-75 flex items-center justify-center z-50">
        {loader}
      </div>
    );
  }

  return loader;
};