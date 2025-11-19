import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse, ApiClient } from '../types';
import { API_BASE_URL } from '../constants';
import { useAuthStore } from '../stores/authStore';

class ApiService implements ApiClient {
  private axiosInstance: AxiosInstance;

  constructor(baseURL: string = API_BASE_URL) {
    this.axiosInstance = axios.create({
      baseURL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor for authentication
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = useAuthStore.getState().tokens?.access_token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for token refresh
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            await useAuthStore.getState().refreshToken();
            const newToken = useAuthStore.getState().tokens?.access_token;

            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return this.axiosInstance(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, logout user
            useAuthStore.getState().logout();
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.get<ApiResponse<T>>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.post<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.put<ApiResponse<T>>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.delete<ApiResponse<T>>(url, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.patch<ApiResponse<T>>(url, data, config);
    return response.data;
  }
}

// Create singleton instance
export const apiService = new ApiService();

// Auth API
export const authApi = {
  login: (credentials: { username: string; password: string }) =>
    apiService.post('/auth/login', credentials),

  register: (userData: { email: string; username: string; password: string; full_name: string }) =>
    apiService.post('/auth/register', userData),

  refreshToken: (refreshToken: string) =>
    apiService.post('/auth/refresh', { refresh_token: refreshToken }),

  getCurrentUser: () =>
    apiService.get('/auth/me'),

  changePassword: (data: { current_password: string; new_password: string }) =>
    apiService.post('/auth/change-password', data),

  logout: () =>
    apiService.post('/auth/logout'),
};

// Datasets API
export const datasetsApi = {
  getDatasets: (params?: {
    page?: number;
    size?: number;
    search?: string;
    tags?: string[];
    owner_id?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => queryParams.append(key, v));
          } else {
            queryParams.append(key, value.toString());
          }
        }
      });
    }
    return apiService.get(`/datasets?${queryParams}`);
  },

  uploadDataset: (formData: FormData) =>
    apiService.post('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  getDataset: (id: string) =>
    apiService.get(`/datasets/${id}`),

  updateDataset: (id: string, data: any) =>
    apiService.put(`/datasets/${id}`, data),

  deleteDataset: (id: string) =>
    apiService.delete(`/datasets/${id}`),

  downloadDataset: (id: string) =>
    apiService.get(`/datasets/${id}/download`, { responseType: 'blob' }),

  getDatasetPreview: (id: string) =>
    apiService.get(`/datasets/${id}/preview`),

  updateMetadata: (id: string, metadata: any) =>
    apiService.patch(`/datasets/${id}/metadata`, metadata),
};

// Jobs API
export const jobsApi = {
  getJobs: (params?: {
    page?: number;
    size?: number;
    status?: string;
    job_type?: string;
    owner_id?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiService.get(`/jobs?${queryParams}`);
  },

  submitPinnJob: (config: any) =>
    apiService.post('/jobs/pinn-training', config),

  submitPdeDiscoveryJob: (config: any) =>
    apiService.post('/jobs/pde-discovery', config),

  submitDerivativeJob: (config: any) =>
    apiService.post('/jobs/derivative-computation', config),

  submitActiveExperimentJob: (config: any) =>
    apiService.post('/jobs/active-experiment', config),

  getJob: (id: string) =>
    apiService.get(`/jobs/${id}`),

  cancelJob: (id: string) =>
    apiService.post(`/jobs/${id}/cancel`),

  getJobLogs: (id: string) =>
    apiService.get(`/jobs/${id}/logs`),

  getJobResults: (id: string) =>
    apiService.get(`/jobs/${id}/results`),

  getJobStatus: (id: string) =>
    apiService.get(`/jobs/${id}/status`),
};

// Reporting API
export const reportingApi = {
  getJobReports: (params?: any) =>
    apiService.get('/reporting/jobs', { params }),

  getDatasetReports: (params?: any) =>
    apiService.get('/reporting/datasets', { params }),

  getSystemReports: () =>
    apiService.get('/reporting/system'),

  getPerformanceReports: (params?: any) =>
    apiService.get('/reporting/performance', { params }),
};

// Audit API
export const auditApi = {
  getEvents: (params?: {
    page?: number;
    size?: number;
    user_id?: string;
    action?: string;
    resource_type?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiService.get(`/audit/events?${queryParams}`);
  },

  searchEvents: (query: string, params?: any) =>
    apiService.get('/audit/search', { params: { q: query, ...params } }),

  exportEvents: (params?: any) =>
    apiService.get('/audit/export', { params, responseType: 'blob' }),
};

// Admin API
export const adminApi = {
  getUsers: (params?: any) =>
    apiService.get('/admin/users', { params }),

  getSystemHealth: () =>
    apiService.get('/admin/health'),

  getMetrics: () =>
    apiService.get('/admin/metrics'),

  getConfig: () =>
    apiService.get('/admin/config'),

  updateConfig: (config: any) =>
    apiService.put('/admin/config', config),
};