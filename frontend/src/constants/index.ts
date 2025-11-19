// Application constants and configuration

export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
export const API_GATEWAY_URL = process.env.REACT_APP_API_GATEWAY_URL || 'http://localhost:8080';

export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
    CHANGE_PASSWORD: '/auth/change-password',
  },

  // Datasets
  DATASETS: {
    LIST: '/datasets',
    UPLOAD: '/datasets/upload',
    DETAIL: (id: string) => `/datasets/${id}`,
    DOWNLOAD: (id: string) => `/datasets/${id}/download`,
    DELETE: (id: string) => `/datasets/${id}`,
    PREVIEW: (id: string) => `/datasets/${id}/preview`,
    METADATA: (id: string) => `/datasets/${id}/metadata`,
  },

  // Jobs
  JOBS: {
    LIST: '/jobs',
    SUBMIT: '/jobs/submit',
    DETAIL: (id: string) => `/jobs/${id}`,
    CANCEL: (id: string) => `/jobs/${id}/cancel`,
    LOGS: (id: string) => `/jobs/${id}/logs`,
    RESULTS: (id: string) => `/jobs/${id}/results`,
    STATUS: (id: string) => `/jobs/${id}/status`,
  },

  // Job Types
  JOB_TYPES: {
    PINN_TRAINING: '/jobs/pinn-training',
    PDE_DISCOVERY: '/jobs/pde-discovery',
    DERIVATIVE_COMPUTATION: '/jobs/derivative-computation',
    ACTIVE_EXPERIMENT: '/jobs/active-experiment',
  },

  // Reporting
  REPORTING: {
    JOBS: '/reporting/jobs',
    DATASETS: '/reporting/datasets',
    SYSTEM: '/reporting/system',
    PERFORMANCE: '/reporting/performance',
  },

  // Audit
  AUDIT: {
    EVENTS: '/audit/events',
    SEARCH: '/audit/search',
    EXPORT: '/audit/export',
  },

  // Admin
  ADMIN: {
    USERS: '/admin/users',
    SYSTEM_HEALTH: '/admin/health',
    METRICS: '/admin/metrics',
    CONFIG: '/admin/config',
  },
} as const;

export const JOB_TYPES = {
  PINN_TRAINING: 'pinn_training',
  PDE_DISCOVERY: 'pde_discovery',
  DERIVATIVE_COMPUTATION: 'derivative_computation',
  ACTIVE_EXPERIMENT: 'active_experiment',
} as const;

export const JOB_STATUSES = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;

export const FILE_TYPES = {
  HDF5: ['application/x-hdf5', 'application/x-hdf'],
  CSV: ['text/csv', 'application/csv'],
  JSON: ['application/json'],
  NUMPY: ['application/octet-stream'], // .npy files
  MATLAB: ['application/matlab-mat'], // .mat files
} as const;

export const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB
export const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB chunks for uploads

export const POLLING_INTERVALS = {
  JOB_STATUS: 5000, // 5 seconds
  SYSTEM_HEALTH: 30000, // 30 seconds
  NOTIFICATIONS: 10000, // 10 seconds
} as const;

export const PAGINATION_DEFAULTS = {
  PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const;

export const VALIDATION_RULES = {
  PASSWORD_MIN_LENGTH: 8,
  USERNAME_MIN_LENGTH: 3,
  USERNAME_MAX_LENGTH: 50,
  EMAIL_MAX_LENGTH: 255,
  DATASET_NAME_MAX_LENGTH: 100,
  DATASET_DESCRIPTION_MAX_LENGTH: 1000,
} as const;

export const CHART_COLORS = {
  PRIMARY: '#3b82f6',
  SECONDARY: '#10b981',
  ACCENT: '#f59e0b',
  ERROR: '#ef4444',
  WARNING: '#f97316',
  SUCCESS: '#22c55e',
  INFO: '#06b6d4',
  GRAY: '#6b7280',
} as const;

export const THEME_COLORS = {
  LIGHT: {
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#1e293b',
    textSecondary: '#64748b',
    border: '#e2e8f0',
    primary: '#3b82f6',
    primaryHover: '#2563eb',
    error: '#ef4444',
    success: '#22c55e',
  },
  DARK: {
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f1f5f9',
    textSecondary: '#94a3b8',
    border: '#334155',
    primary: '#3b82f6',
    primaryHover: '#60a5fa',
    error: '#ef4444',
    success: '#22c55e',
  },
} as const;

export const BREAKPOINTS = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

export const Z_INDEX = {
  DROPDOWN: 1000,
  STICKY: 1020,
  FIXED: 1030,
  MODAL_BACKDROP: 1040,
  MODAL: 1050,
  POPOVER: 1060,
  TOOLTIP: 1070,
  NOTIFICATION: 1080,
} as const;

export const ANIMATION_DURATIONS = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const;

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_PREFERENCES: 'user_preferences',
  THEME: 'theme',
  LANGUAGE: 'language',
} as const;

export const DEFAULT_JOB_CONFIGS = {
  PINN_TRAINING: {
    model_architecture: {
      layers: [2, 50, 50, 50, 1],
      activations: ['tanh', 'tanh', 'tanh'],
    },
    training: {
      learning_rate: 0.001,
      epochs: 10000,
      optimizer: 'adam',
      batch_size: 1000,
    },
    data: {
      num_collocation_points: 10000,
      num_boundary_points: 1000,
    },
    physics: {
      pde_equation: '∂²u/∂x² + ∂²u/∂y² = 0', // Laplace equation
      boundary_conditions: ['u(x,0) = 0', 'u(x,1) = sin(πx)', 'u(0,y) = 0', 'u(1,y) = 0'],
    },
  },
  PDE_DISCOVERY: {
    algorithm: 'sindy',
    data: {
      feature_library: ['x', 'y', 'z', 'x*y', 'x*z', 'y*z', 'x²', 'y²', 'z²'],
      time_derivative_order: 1,
      spatial_derivative_order: 2,
    },
    discovery: {
      threshold: 0.1,
      max_iterations: 100,
      tolerance: 1e-6,
    },
    sindy: {
      poly_order: 3,
      include_sine: false,
      include_cos: false,
    },
  },
  DERIVATIVE_COMPUTATION: {
    data: {
      variable_name: 'u',
      derivative_orders: [1, 1, 0], // ∂u/∂x∂y
    },
    computation: {
      method: 'finite_difference',
      accuracy_order: 4,
      boundary_handling: 'neumann',
    },
    grid: {
      dimensions: [100, 100, 50],
      domain_bounds: [[0, 1], [0, 1], [0, 1]],
    },
  },
  ACTIVE_EXPERIMENT: {
    objective: {
      function: 'f(x,y) = (x-0.5)² + (y-0.5)²', // Simple quadratic
      minimize: true,
    },
    parameters: [
      {
        name: 'x',
        bounds: [0, 1],
        type: 'continuous' as const,
      },
      {
        name: 'y',
        bounds: [0, 1],
        type: 'continuous' as const,
      },
    ],
    optimization: {
      acquisition_function: 'EI',
      initial_points: 5,
      max_evaluations: 50,
    },
  },
} as const;

export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
] as const;

export const TIME_ZONES = [
  'UTC',
  'America/New_York',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Australia/Sydney',
] as const;