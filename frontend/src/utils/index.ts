// Utility functions for the PhysForge Platform

import { JobStatus, JobType, Dataset } from '../types';
import { JOB_STATUSES, FILE_TYPES } from '../constants';

// Job utilities
export const getJobStatusColor = (status: JobStatus): string => {
  switch (status) {
    case JOB_STATUSES.PENDING:
      return 'yellow';
    case JOB_STATUSES.RUNNING:
      return 'blue';
    case JOB_STATUSES.COMPLETED:
      return 'green';
    case JOB_STATUSES.FAILED:
      return 'red';
    case JOB_STATUSES.CANCELLED:
      return 'gray';
    default:
      return 'gray';
  }
};

export const getJobStatusIcon = (status: JobStatus): string => {
  switch (status) {
    case JOB_STATUSES.PENDING:
      return 'clock';
    case JOB_STATUSES.RUNNING:
      return 'loader';
    case JOB_STATUSES.COMPLETED:
      return 'check-circle';
    case JOB_STATUSES.FAILED:
      return 'x-circle';
    case JOB_STATUSES.CANCELLED:
      return 'minus-circle';
    default:
      return 'help-circle';
  }
};

export const getJobTypeLabel = (type: JobType): string => {
  switch (type) {
    case 'pinn_training':
      return 'PINN Training';
    case 'pde_discovery':
      return 'PDE Discovery';
    case 'derivative_computation':
      return 'Derivative Computation';
    case 'active_experiment':
      return 'Active Experiment';
    default:
      return 'Unknown';
  }
};

export const formatJobDuration = (startTime: string, endTime?: string): string => {
  const start = new Date(startTime);
  const end = endTime ? new Date(endTime) : new Date();
  const duration = end.getTime() - start.getTime();

  const seconds = Math.floor(duration / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ${hours % 24}h`;
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getFileTypeFromMime = (mimeType: string): string => {
  if (FILE_TYPES.HDF5.includes(mimeType)) return 'HDF5';
  if (FILE_TYPES.CSV.includes(mimeType)) return 'CSV';
  if (FILE_TYPES.JSON.includes(mimeType)) return 'JSON';
  if (FILE_TYPES.NUMPY.includes(mimeType)) return 'NumPy';
  if (FILE_TYPES.MATLAB.includes(mimeType)) return 'MATLAB';
  return 'Unknown';
};

export const validateFileType = (file: File): boolean => {
  const allTypes = [
    ...FILE_TYPES.HDF5,
    ...FILE_TYPES.CSV,
    ...FILE_TYPES.JSON,
    ...FILE_TYPES.NUMPY,
    ...FILE_TYPES.MATLAB,
  ];
  return allTypes.includes(file.type) || file.name.endsWith('.npy') || file.name.endsWith('.mat');
};

export const formatDate = (date: string | Date, format: 'short' | 'long' | 'relative' = 'short'): string => {
  const d = new Date(date);

  switch (format) {
    case 'short':
      return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    case 'long':
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    case 'relative':
      const now = new Date();
      const diff = now.getTime() - d.getTime();
      const seconds = Math.floor(diff / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);

      if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
      if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
      if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
      return 'Just now';
    default:
      return d.toLocaleDateString();
  }
};

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

export const generateId = (): string => {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      return true;
    } catch (fallbackErr) {
      return false;
    } finally {
      document.body.removeChild(textArea);
    }
  }
};

export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

export const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

export const groupBy = <T, K extends keyof any>(
  array: T[],
  key: (item: T) => K
): Record<K, T[]> => {
  return array.reduce((groups, item) => {
    const groupKey = key(item);
    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(item);
    return groups;
  }, {} as Record<K, T[]>);
};

export const sortBy = <T>(
  array: T[],
  key: keyof T,
  direction: 'asc' | 'desc' = 'asc'
): T[] => {
  return [...array].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];

    if (aVal < bVal) return direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return direction === 'asc' ? 1 : -1;
    return 0;
  });
};

export const filterBy = <T>(
  array: T[],
  predicate: (item: T) => boolean
): T[] => {
  return array.filter(predicate);
};

export const paginate = <T>(
  array: T[],
  page: number,
  pageSize: number
): { items: T[]; total: number; pages: number } => {
  const total = array.length;
  const pages = Math.ceil(total / pageSize);
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const items = array.slice(start, end);

  return { items, total, pages };
};

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePassword = (password: string): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }

  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }

  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

export const sanitizeHtml = (html: string): string => {
  // Basic HTML sanitization - in production, use a proper library like DOMPurify
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '')
    .replace(/on\w+="[^"]*"/gi, '')
    .replace(/javascript:/gi, '');
};

export const truncateText = (text: string, maxLength: number, suffix: string = '...'): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - suffix.length) + suffix;
};

export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

export const camelToKebab = (str: string): string => {
  return str.replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, '$1-$2').toLowerCase();
};

export const kebabToCamel = (str: string): string => {
  return str.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
};