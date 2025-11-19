import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../../components/layout/Layout';
import { Card, CardHeader, CardBody } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { useJobsStore } from '../../stores/jobsStore';
import { Job, JobStatus } from '../../types';
import {
  IconPlus,
  IconCalculator,
  IconFormula,
  IconChartLine,
  IconFlask,
  IconCheck,
  IconX,
  IconClock,
  IconPlayerPlay,
  IconAlertTriangle,
  IconDownload,
  IconEye,
} from '@tabler/icons-react';
import { Badge } from '@mantine/core';

const getJobTypeIcon = (jobType: string) => {
  switch (jobType) {
    case 'pinn_training':
      return <IconCalculator size={16} />;
    case 'pde_discovery':
      return <IconFormula size={16} />;
    case 'derivative_feature':
      return <IconChartLine size={16} />;
    case 'active_experiment':
      return <IconFlask size={16} />;
    default:
      return <IconCalculator size={16} />;
  }
};

const getJobTypeLabel = (jobType: string) => {
  switch (jobType) {
    case 'pinn_training':
      return 'PINN Training';
    case 'pde_discovery':
      return 'PDE Discovery';
    case 'derivative_feature':
      return 'Derivative Features';
    case 'active_experiment':
      return 'Active Experiment';
    default:
      return jobType;
  }
};

const getStatusIcon = (status: JobStatus) => {
  switch (status) {
    case JobStatus.COMPLETED:
      return <IconCheck size={16} className="text-green-500" />;
    case JobStatus.FAILED:
      return <IconX size={16} className="text-red-500" />;
    case JobStatus.RUNNING:
      return <IconPlayerPlay size={16} className="text-blue-500" />;
    case JobStatus.PENDING:
      return <IconClock size={16} className="text-yellow-500" />;
    case JobStatus.CANCELLED:
      return <IconAlertTriangle size={16} className="text-gray-500" />;
    default:
      return <IconClock size={16} className="text-gray-500" />;
  }
};

const getStatusColor = (status: JobStatus) => {
  switch (status) {
    case JobStatus.COMPLETED:
      return 'green';
    case JobStatus.FAILED:
      return 'red';
    case JobStatus.RUNNING:
      return 'blue';
    case JobStatus.PENDING:
      return 'yellow';
    case JobStatus.CANCELLED:
      return 'gray';
    default:
      return 'gray';
  }
};

const JobsPage: React.FC = () => {
  const { jobs, isLoading, fetchJobs, cancelJob } = useJobsStore();
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const filteredJobs = jobs.filter(job => {
    if (filter === 'all') return true;
    return job.status === filter;
  });

  const handleCancelJob = async (jobId: string) => {
    if (window.confirm('Are you sure you want to cancel this job?')) {
      try {
        await cancelJob(jobId);
      } catch (error) {
        console.error('Failed to cancel job:', error);
      }
    }
  };

  if (isLoading && jobs.length === 0) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <Loading size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Jobs
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Monitor and manage your computational jobs
            </p>
          </div>
          <div className="flex space-x-3">
            <Button
              component={Link}
              to="/jobs/new/pinn"
              leftIcon={<IconCalculator size={16} />}
            >
              New PINN Job
            </Button>
            <Button
              component={Link}
              to="/jobs/new/pde"
              variant="outline"
              leftIcon={<IconFormula size={16} />}
            >
              New PDE Discovery
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardBody>
            <div className="flex flex-wrap gap-2">
              <Button
                variant={filter === 'all' ? 'filled' : 'outline'}
                size="sm"
                onClick={() => setFilter('all')}
              >
                All ({jobs.length})
              </Button>
              <Button
                variant={filter === JobStatus.RUNNING ? 'filled' : 'outline'}
                size="sm"
                onClick={() => setFilter(JobStatus.RUNNING)}
              >
                Running ({jobs.filter(j => j.status === JobStatus.RUNNING).length})
              </Button>
              <Button
                variant={filter === JobStatus.PENDING ? 'filled' : 'outline'}
                size="sm"
                onClick={() => setFilter(JobStatus.PENDING)}
              >
                Pending ({jobs.filter(j => j.status === JobStatus.PENDING).length})
              </Button>
              <Button
                variant={filter === JobStatus.COMPLETED ? 'filled' : 'outline'}
                size="sm"
                onClick={() => setFilter(JobStatus.COMPLETED)}
              >
                Completed ({jobs.filter(j => j.status === JobStatus.COMPLETED).length})
              </Button>
              <Button
                variant={filter === JobStatus.FAILED ? 'filled' : 'outline'}
                size="sm"
                onClick={() => setFilter(JobStatus.FAILED)}
              >
                Failed ({jobs.filter(j => j.status === JobStatus.FAILED).length})
              </Button>
            </div>
          </CardBody>
        </Card>

        {/* Jobs List */}
        <div className="space-y-4">
          {filteredJobs.length === 0 ? (
            <Card>
              <CardBody className="text-center py-12">
                <IconCalculator size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No jobs found
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {filter === 'all'
                    ? "You haven't submitted any jobs yet."
                    : `No jobs with status "${filter}".`
                  }
                </p>
                <Button
                  component={Link}
                  to="/jobs/new/pinn"
                  leftIcon={<IconPlus size={16} />}
                >
                  Create Your First Job
                </Button>
              </CardBody>
            </Card>
          ) : (
            filteredJobs.map((job) => (
              <Card key={job.id}>
                <CardBody>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0">
                        {getJobTypeIcon(job.job_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
                            {job.name || `Job ${job.id.slice(-8)}`}
                          </h3>
                          <Badge color={getStatusColor(job.status)} size="sm">
                            {job.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {getJobTypeLabel(job.job_type)} • Submitted {new Date(job.created_at).toLocaleDateString()}
                        </p>
                        {job.description && (
                          <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                            {job.description}
                          </p>
                        )}

                        {/* Progress */}
                        {job.status === JobStatus.RUNNING && job.progress !== undefined && (
                          <div className="mb-2">
                            <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                              <span>Progress</span>
                              <span>{Math.round(job.progress * 100)}%</span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${job.progress * 100}%` }}
                              />
                            </div>
                          </div>
                        )}

                        {/* Error Message */}
                        {job.status === JobStatus.FAILED && job.error_message && (
                          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-2">
                            <p className="text-sm text-red-700 dark:text-red-300">
                              {job.error_message}
                            </p>
                          </div>
                        )}

                        {/* Timing */}
                        <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                          {job.started_at && (
                            <span>Started: {new Date(job.started_at).toLocaleString()}</span>
                          )}
                          {job.completed_at && (
                            <span>Completed: {new Date(job.completed_at).toLocaleString()}</span>
                          )}
                          {job.duration && (
                            <span>Duration: {Math.round(job.duration)}s</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {getStatusIcon(job.status)}

                      {/* Actions */}
                      <div className="flex space-x-2">
                        {job.status === JobStatus.COMPLETED && job.results && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              leftIcon={<IconEye size={14} />}
                              component={Link}
                              to={`/jobs/${job.id}/results`}
                            >
                              View Results
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              leftIcon={<IconDownload size={14} />}
                              onClick={() => {
                                // TODO: Implement download results
                                console.log('Download results for job:', job.id);
                              }}
                            >
                              Download
                            </Button>
                          </>
                        )}

                        {(job.status === JobStatus.PENDING || job.status === JobStatus.RUNNING) && (
                          <Button
                            size="sm"
                            variant="outline"
                            color="red"
                            onClick={() => handleCancelJob(job.id)}
                          >
                            Cancel
                          </Button>
                        )}

                        <Button
                          size="sm"
                          variant="outline"
                          component={Link}
                          to={`/jobs/${job.id}`}
                        >
                          Details
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))
          )}
        </div>

        {/* Load More */}
        {jobs.length > 0 && (
          <div className="text-center">
            <Button
              variant="outline"
              onClick={() => fetchJobs()}
              loading={isLoading}
            >
              {isLoading ? 'Loading...' : 'Load More Jobs'}
            </Button>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default JobsPage;