import { create } from 'zustand';
import { Dataset, DatasetMetadata } from '../types';
import { API_ENDPOINTS, MAX_FILE_SIZE, CHUNK_SIZE } from '../constants';
import { useAuthStore } from './authStore';

interface DatasetsState {
  datasets: Dataset[];
  currentDataset: Dataset | null;
  isLoading: boolean;
  error: string | null;
  uploadProgress: number;

  // Actions
  fetchDatasets: (params?: {
    page?: number;
    size?: number;
    search?: string;
    tags?: string[];
    owner_id?: string;
  }) => Promise<void>;

  uploadDataset: (file: File, metadata: DatasetMetadata) => Promise<Dataset>;
  deleteDataset: (datasetId: string) => Promise<void>;
  getDataset: (datasetId: string) => Promise<Dataset>;
  downloadDataset: (datasetId: string) => Promise<void>;
  updateDatasetMetadata: (datasetId: string, metadata: Partial<DatasetMetadata>) => Promise<void>;

  // Internal actions
  setDatasets: (datasets: Dataset[]) => void;
  setCurrentDataset: (dataset: Dataset | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setUploadProgress: (progress: number) => void;
  updateDataset: (datasetId: string, updates: Partial<Dataset>) => void;
  addDataset: (dataset: Dataset) => void;
  removeDataset: (datasetId: string) => void;
}

export const useDatasetsStore = create<DatasetsState>((set, get) => ({
  datasets: [],
  currentDataset: null,
  isLoading: false,
  error: null,
  uploadProgress: 0,

  fetchDatasets: async (params = {}) => {
    set({ isLoading: true, error: null });
    try {
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => queryParams.append(key, v));
          } else {
            queryParams.append(key, value.toString());
          }
        }
      });

      const url = `${process.env.REACT_APP_API_BASE_URL}${API_ENDPOINTS.DATASETS.LIST}?${queryParams}`;
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch datasets');
      }

      const data = await response.json();
      set({ datasets: data.items || data, isLoading: false });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch datasets',
      });
      throw error;
    }
  },

  uploadDataset: async (file: File, metadata: DatasetMetadata) => {
    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      throw new Error(`File size exceeds maximum limit of ${MAX_FILE_SIZE / (1024 * 1024)}MB`);
    }

    set({ isLoading: true, error: null, uploadProgress: 0 });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', metadata.name);
      formData.append('description', metadata.description || '');
      metadata.tags.forEach(tag => formData.append('tags', tag));

      if (metadata.metadata) {
        formData.append('metadata', JSON.stringify(metadata.metadata));
      }

      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}${API_ENDPOINTS.DATASETS.UPLOAD}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload dataset');
      }

      const dataset: Dataset = await response.json();
      get().addDataset(dataset);
      set({ isLoading: false, uploadProgress: 100 });
      return dataset;
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to upload dataset',
      });
      throw error;
    }
  },

  deleteDataset: async (datasetId: string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}${API_ENDPOINTS.DATASETS.DELETE(datasetId)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete dataset');
      }

      get().removeDataset(datasetId);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to delete dataset' });
      throw error;
    }
  },

  getDataset: async (datasetId: string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}${API_ENDPOINTS.DATASETS.DETAIL(datasetId)}`, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get dataset');
      }

      const dataset: Dataset = await response.json();
      get().updateDataset(datasetId, dataset);
      return dataset;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to get dataset' });
      throw error;
    }
  },

  downloadDataset: async (datasetId: string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}${API_ENDPOINTS.DATASETS.DOWNLOAD(datasetId)}`, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download dataset');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dataset_${datasetId}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to download dataset' });
      throw error;
    }
  },

  updateDatasetMetadata: async (datasetId: string, metadata: Partial<DatasetMetadata>) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}${API_ENDPOINTS.DATASETS.METADATA(datasetId)}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
        body: JSON.stringify(metadata),
      });

      if (!response.ok) {
        throw new Error('Failed to update dataset metadata');
      }

      const updatedDataset: Dataset = await response.json();
      get().updateDataset(datasetId, updatedDataset);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to update dataset metadata' });
      throw error;
    }
  },

  setDatasets: (datasets: Dataset[]) => set({ datasets }),
  setCurrentDataset: (dataset: Dataset | null) => set({ currentDataset: dataset }),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  setUploadProgress: (progress: number) => set({ uploadProgress: progress }),

  updateDataset: (datasetId: string, updates: Partial<Dataset>) => {
    set((state) => ({
      datasets: state.datasets.map(dataset =>
        dataset.id === datasetId ? { ...dataset, ...updates } : dataset
      ),
      currentDataset: state.currentDataset?.id === datasetId
        ? { ...state.currentDataset, ...updates }
        : state.currentDataset,
    }));
  },

  addDataset: (dataset: Dataset) => {
    set((state) => ({
      datasets: [dataset, ...state.datasets],
    }));
  },

  removeDataset: (datasetId: string) => {
    set((state) => ({
      datasets: state.datasets.filter(dataset => dataset.id !== datasetId),
      currentDataset: state.currentDataset?.id === datasetId ? null : state.currentDataset,
    }));
  },
}));