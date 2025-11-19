// TypeScript type definitions for the PhysForge Platform

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  username: string;
  password: string;
  full_name: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  metadata: Record<string, any>;
  owner_id: string;
  created_at: string;
  updated_at: string;
  version: number;
  tags: string[];
}

export interface DatasetMetadata {
  name: string;
  description: string;
  tags: string[];
  metadata: Record<string, any>;
}

export interface Job {
  id: string;
  job_type: JobType;
  status: JobStatus;
  config: Record<string, any>;
  owner_id: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  result_path?: string;
  error_message?: string;
  progress?: number;
  rq_job_id?: string;
}

export enum JobType {
  PINN_TRAINING = 'pinn_training',
  PDE_DISCOVERY = 'pde_discovery',
  DERIVATIVE_COMPUTATION = 'derivative_computation',
  ACTIVE_EXPERIMENT = 'active_experiment'
}

export enum JobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface PinnJobConfig {
  model_architecture: {
    layers: number[];
    activations: string[];
  };
  training: {
    learning_rate: number;
    epochs: number;
    optimizer: string;
    batch_size: number;
  };
  data: {
    dataset_id: string;
    domain_bounds: [number, number][];
    num_collocation_points: number;
    num_boundary_points: number;
  };
  physics: {
    pde_equation: string;
    boundary_conditions: string[];
    initial_conditions?: string[];
  };
}

export interface PdeDiscoveryConfig {
  algorithm: 'sindy' | 'pysr';
  data: {
    dataset_id: string;
    feature_library: string[];
    time_derivative_order: number;
    spatial_derivative_order: number;
  };
  discovery: {
    threshold: number;
    max_iterations: number;
    tolerance: number;
  };
  sindy?: {
    poly_order: number;
    include_sine: boolean;
    include_cos: boolean;
  };
  pysr?: {
    binary_operators: string[];
    unary_operators: string[];
    populations: number;
    population_size: number;
  };
}

export interface DerivativeComputationConfig {
  data: {
    dataset_id: string;
    variable_name: string;
    derivative_orders: [number, number, number]; // [x_order, y_order, t_order]
  };
  computation: {
    method: 'finite_difference' | 'spectral' | 'automatic_differentiation';
    accuracy_order: number;
    boundary_handling: 'periodic' | 'neumann' | 'dirichlet';
  };
  grid: {
    dimensions: [number, number, number]; // [nx, ny, nt]
    domain_bounds: [number, number][]; // [[x_min, x_max], [y_min, y_max], [t_min, t_max]]
  };
}

export interface ActiveExperimentConfig {
  objective: {
    function: string;
    minimize: boolean;
  };
  parameters: {
    name: string;
    bounds: [number, number];
    type: 'continuous' | 'discrete' | 'categorical';
    values?: number[] | string[];
  }[];
  optimization: {
    acquisition_function: 'EI' | 'PI' | 'UCB';
    initial_points: number;
    max_evaluations: number;
  };
  data?: {
    dataset_id: string;
    x_columns: string[];
    y_column: string;
  };
}

export interface JobResult {
  job_id: string;
  job_type: JobType;
  status: JobStatus;
  result_data: Record<string, any>;
  metrics?: Record<string, any>;
  plots?: PlotData[];
  equations?: string[];
  created_at: string;
}

export interface PlotData {
  id: string;
  title: string;
  type: '2d' | '3d' | 'contour' | 'surface';
  data: any[];
  layout: any;
}

export interface PinnResult extends JobResult {
  result_data: {
    model_path: string;
    training_history: {
      loss_pde: number[];
      loss_data: number[];
      loss_boundary: number[];
      epochs: number[];
    };
    final_losses: {
      total_loss: number;
      pde_loss: number;
      data_loss: number;
      boundary_loss: number;
    };
    solution_surface: PlotData;
    loss_curves: PlotData;
  };
}

export interface PdeDiscoveryResult extends JobResult {
  result_data: {
    discovered_equations: {
      equation: string;
      complexity: number;
      score: number;
      coefficients: Record<string, number>;
    }[];
    feature_importance: Record<string, number>;
    model_coefficients: Record<string, number[]>;
    sparsity_pattern: number[][];
  };
}

export interface DerivativeResult extends JobResult {
  result_data: {
    derivative_field: number[][][];
    computation_metadata: {
      method: string;
      accuracy_order: number;
      grid_dimensions: [number, number, number];
      computation_time: number;
    };
    derivative_plots: PlotData[];
    error_analysis?: {
      numerical_error: number;
      convergence_rate: number;
    };
  };
}

export interface ActiveExperimentResult extends JobResult {
  result_data: {
    optimal_parameters: Record<string, number>;
    optimization_history: {
      parameters: Record<string, number>[];
      objectives: number[];
      evaluations: number[];
    };
    surrogate_model: {
      predictions: number[];
      uncertainties: number[];
    };
    acquisition_landscape: PlotData;
    optimization_trajectory: PlotData;
  };
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    name: string;
    status: 'up' | 'down' | 'degraded';
    response_time?: number;
    last_check: string;
  }[];
  metrics: {
    total_jobs: number;
    active_jobs: number;
    total_datasets: number;
    storage_used: number;
    storage_total: number;
  };
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, any>;
  ip_address: string;
  user_agent: string;
}

// Form validation schemas
export interface ValidationError {
  field: string;
  message: string;
}

export interface FormState<T> {
  data: T;
  errors: ValidationError[];
  isSubmitting: boolean;
  isValid: boolean;
}

// API service interfaces
export interface ApiClient {
  get<T>(url: string, config?: any): Promise<ApiResponse<T>>;
  post<T>(url: string, data?: any, config?: any): Promise<ApiResponse<T>>;
  put<T>(url: string, data?: any, config?: any): Promise<ApiResponse<T>>;
  delete<T>(url: string, config?: any): Promise<ApiResponse<T>>;
  patch<T>(url: string, data?: any, config?: any): Promise<ApiResponse<T>>;
}

// Component prop interfaces
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingProps extends BaseComponentProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
}

export interface ErrorBoundaryProps extends BaseComponentProps {
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  onError?: (error: Error, errorInfo: any) => void;
}

export interface ModalProps extends BaseComponentProps {
  opened: boolean;
  onClose: () => void;
  title?: string;
  size?: string | number;
  centered?: boolean;
}

export interface TableColumn<T> {
  key: keyof T | string;
  title: string;
  render?: (value: any, record: T) => React.ReactNode;
  sortable?: boolean;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
}

export interface TableProps<T> extends BaseComponentProps {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  pagination?: {
    current: number;
    total: number;
    pageSize: number;
    onChange: (page: number, pageSize: number) => void;
  };
  onRowClick?: (record: T) => void;
  rowKey?: keyof T | ((record: T) => string);
}

// Chart component interfaces
export interface ChartProps extends BaseComponentProps {
  data: any[];
  layout?: any;
  config?: any;
  onClick?: (event: any) => void;
  onHover?: (event: any) => void;
}

export interface PlotlyChartProps extends ChartProps {
  type: 'scatter' | 'bar' | 'line' | 'heatmap' | 'contour' | 'surface';
  x?: number[];
  y?: number[];
  z?: number[][];
  mode?: 'lines' | 'markers' | 'lines+markers';
  name?: string;
}

// Three.js component interfaces
export interface ThreeSceneProps extends BaseComponentProps {
  camera?: {
    position: [number, number, number];
    fov?: number;
  };
  controls?: boolean;
  lights?: boolean;
}

export interface SurfacePlotProps extends ThreeSceneProps {
  data: number[][][];
  bounds: [number, number][]; // [[x_min, x_max], [y_min, y_max], [z_min, z_max]]
  colormap?: string;
  wireframe?: boolean;
  opacity?: number;
}

// Hook return types
export interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

export interface UseJobsReturn {
  jobs: Job[];
  currentJob: Job | null;
  isLoading: boolean;
  error: string | null;
  fetchJobs: (params?: any) => Promise<void>;
  submitJob: (config: any, type: JobType) => Promise<Job>;
  cancelJob: (jobId: string) => Promise<void>;
  getJob: (jobId: string) => Promise<Job>;
  watchJob: (jobId: string, callback: (job: Job) => void) => () => void;
}

export interface UseDatasetsReturn {
  datasets: Dataset[];
  isLoading: boolean;
  error: string | null;
  uploadDataset: (file: File, metadata: DatasetMetadata) => Promise<Dataset>;
  fetchDatasets: (params?: any) => Promise<void>;
  deleteDataset: (datasetId: string) => Promise<void>;
  getDataset: (datasetId: string) => Promise<Dataset>;
  downloadDataset: (datasetId: string) => Promise<void>;
}

export interface UseNotificationsReturn {
  notifications: NotificationItem[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  addNotification: (notification: Omit<NotificationItem, 'id' | 'timestamp' | 'read'>) => void;
  removeNotification: (id: string) => void;
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> = Pick<T, Exclude<keyof T, Keys>> & {
  [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Keys>>;
}[Keys];

export type ValueOf<T> = T[keyof T];

export type NonNullable<T> = T extends null | undefined ? never : T;