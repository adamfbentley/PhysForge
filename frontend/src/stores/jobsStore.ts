import { create } from 'zustand';
import { Job, JobType, JobStatus, PinnJobConfig, PdeDiscoveryConfig, DerivativeComputationConfig, ActiveExperimentConfig } from '../types';
import { API_ENDPOINTS, POLLING_INTERVALS } from '../constants';
import { useAuthStore } from './authStore';

interface JobsState {
  jobs: Job[];
  currentJob: Job | null;
  isLoading: boolean;
  error: string | null;
  pollingJobs: Set<string>; // Jobs being polled for status updates

  // Actions
  fetchJobs: (params?: {
    page?: number;
    size?: number;
    status?: JobStatus;
    job_type?: JobType;
    owner_id?: string;
  }) => Promise<void>;

  submitJob: (config: any, type: JobType) => Promise<Job>;
  cancelJob: (jobId: string) => Promise<void>;
  getJob: (jobId: string) => Promise<Job>;
  watchJob: (jobId: string, callback?: (job: Job) => void) => () => void;
  stopWatchingJob: (jobId: string) => void;

  // Internal actions
  setJobs: (jobs: Job[]) => void;
  setCurrentJob: (job: Job | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updateJob: (jobId: string, updates: Partial<Job>) => void;
  addJob: (job: Job) => void;
  removeJob: (jobId: string) => void;
}

export const useJobsStore = create<JobsState>((set, get) => ({
  jobs: [],
  currentJob: null,
  isLoading: false,
  error: null,
  pollingJobs: new Set(),

  fetchJobs: async (params = {}) => {
    set({ isLoading: true, error: null });
    try {
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });

      const url = `${process.env.REACT_APP_API_BASE_URL}${API_ENDPOINTS.JOBS.LIST}?${queryParams}`;
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch jobs');
      }

      const data = await response.json();
      set({ jobs: data.items || data, isLoading: false });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch jobs',
      });
      throw error;
    }
  },

  submitJob: async (config: any, type: JobType) => {
    set({ isLoading: true, error: null });
    try {
      const endpoint = API_ENDPOINTS.JOB_TYPES[type.toUpperCase() as keyof typeof API_ENDPOINTS.JOB_TYPES];
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error('Failed to submit job');
      }

      const job: Job = await response.json();
      get().addJob(job);
      set({ isLoading: false });
      return job;
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to submit job',
      });
      throw error;
    }
  },

  cancelJob: async (jobId: string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}${API_ENDPOINTS.JOBS.CANCEL(jobId)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to cancel job');
      }

      get().updateJob(jobId, { status: JobStatus.CANCELLED });
      get().stopWatchingJob(jobId);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to cancel job' });
      throw error;
    }
  },

  getJob: async (jobId: string) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL}${API_ENDPOINTS.JOBS.DETAIL(jobId)}`, {
        headers: {
          'Authorization': `Bearer ${useAuthStore.getState().tokens?.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get job');
      }

      const job: Job = await response.json();
      get().updateJob(jobId, job);
      return job;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to get job' });
      throw error;
    }
  },

  watchJob: (jobId: string, callback?: (job: Job) => void) => {
    const { pollingJobs } = get();
    if (pollingJobs.has(jobId)) {
      return () => get().stopWatchingJob(jobId);
    }

    set({ pollingJobs: new Set([...pollingJobs, jobId]) });

    const poll = async () => {
      try {
        const job = await get().getJob(jobId);
        callback?.(job);

        // Stop polling if job is completed, failed, or cancelled
        if ([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED].includes(job.status)) {
          get().stopWatchingJob(jobId);
          return;
        }

        // Continue polling
        setTimeout(poll, POLLING_INTERVALS.JOB_STATUS);
      } catch (error) {
        console.error('Error polling job status:', error);
        get().stopWatchingJob(jobId);
      }
    };

    // Start polling
    setTimeout(poll, POLLING_INTERVALS.JOB_STATUS);

    return () => get().stopWatchingJob(jobId);
  },

  stopWatchingJob: (jobId: string) => {
    const { pollingJobs } = get();
    const newPollingJobs = new Set(pollingJobs);
    newPollingJobs.delete(jobId);
    set({ pollingJobs: newPollingJobs });
  },

  setJobs: (jobs: Job[]) => set({ jobs }),
  setCurrentJob: (job: Job | null) => set({ currentJob: job }),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),

  updateJob: (jobId: string, updates: Partial<Job>) => {
    set((state) => ({
      jobs: state.jobs.map(job =>
        job.id === jobId ? { ...job, ...updates } : job
      ),
      currentJob: state.currentJob?.id === jobId
        ? { ...state.currentJob, ...updates }
        : state.currentJob,
    }));
  },

  addJob: (job: Job) => {
    set((state) => ({
      jobs: [job, ...state.jobs],
    }));
  },

  removeJob: (jobId: string) => {
    set((state) => ({
      jobs: state.jobs.filter(job => job.id !== jobId),
      currentJob: state.currentJob?.id === jobId ? null : state.currentJob,
    }));
  },
}));