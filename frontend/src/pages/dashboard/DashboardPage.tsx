import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../../components/layout/Layout';
import { Card, CardHeader, CardBody } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { useJobsStore } from '../../stores/jobsStore';
import { useDatasetsStore } from '../../stores/datasetsStore';
import { useAuthStore } from '../../stores/authStore';
import { formatDate, formatFileSize, getJobStatusColor } from '../../utils';
import {
  IconDatabase,
  IconCalculator,
  IconChartBar,
  IconTrendingUp,
  IconPlus,
  IconEye
} from '@tabler/icons-react';

const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const { jobs, isLoading: jobsLoading, fetchJobs } = useJobsStore();
  const { datasets, isLoading: datasetsLoading, fetchDatasets } = useDatasetsStore();

  useEffect(() => {
    fetchJobs({ page: 1, size: 5 });
    fetchDatasets({ page: 1, size: 5 });
  }, [fetchJobs, fetchDatasets]);

  const recentJobs = jobs.slice(0, 5);
  const recentDatasets = datasets.slice(0, 5);

  const stats = [
    {
      name: 'Total Datasets',
      value: datasets.length,
      icon: IconDatabase,
      color: 'blue',
      link: '/datasets',
    },
    {
      name: 'Active Jobs',
      value: jobs.filter(job => job.status === 'running').length,
      icon: IconCalculator,
      color: 'green',
      link: '/jobs',
    },
    {
      name: 'Completed Jobs',
      value: jobs.filter(job => job.status === 'completed').length,
      icon: IconChartBar,
      color: 'purple',
      link: '/results',
    },
    {
      name: 'Success Rate',
      value: jobs.length > 0
        ? Math.round((jobs.filter(job => job.status === 'completed').length / jobs.length) * 100)
        : 0,
      icon: IconTrendingUp,
      color: 'indigo',
      suffix: '%',
      link: '/reports',
    },
  ];

  if (jobsLoading || datasetsLoading) {
    return (
      <Layout>
        <Loading text="Loading dashboard..." />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Welcome Header */}
        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Welcome back, {user?.full_name || user?.username}!
                </h1>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  Here's what's happening with your scientific discovery projects.
                </p>
              </div>
              <div className="flex space-x-3">
                <Button
                  component={Link}
                  to="/datasets/upload"
                  leftIcon={<IconPlus size={16} />}
                >
                  Upload Dataset
                </Button>
                <Button
                  component={Link}
                  to="/jobs/new"
                  variant="outline"
                  leftIcon={<IconCalculator size={16} />}
                >
                  New Job
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.name} hover clickable component={Link} to={stat.link}>
              <CardBody>
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <stat.icon
                      size={24}
                      className={`text-${stat.color}-600 dark:text-${stat.color}-400`}
                    />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        {stat.name}
                      </dt>
                      <dd className="text-lg font-medium text-gray-900 dark:text-white">
                        {stat.value}{stat.suffix}
                      </dd>
                    </dl>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Recent Jobs */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Recent Jobs
                </h3>
                <Button
                  component={Link}
                  to="/jobs"
                  variant="subtle"
                  size="sm"
                  rightIcon={<IconEye size={16} />}
                >
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardBody>
              {recentJobs.length === 0 ? (
                <div className="text-center py-6">
                  <IconCalculator size={48} className="mx-auto text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                    No jobs yet
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Get started by creating your first job.
                  </p>
                  <div className="mt-6">
                    <Button component={Link} to="/jobs/new" size="sm">
                      Create Job
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentJobs.map((job) => (
                    <div key={job.id} className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div
                          className={`w-3 h-3 rounded-full bg-${getJobStatusColor(job.status)}-500`}
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {job.job_type.replace('_', ' ').toUpperCase()}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(job.created_at, 'relative')}
                        </p>
                      </div>
                      <div className="flex-shrink-0">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize bg-${getJobStatusColor(job.status)}-100 text-${getJobStatusColor(job.status)}-800`}>
                          {job.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>

          {/* Recent Datasets */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Recent Datasets
                </h3>
                <Button
                  component={Link}
                  to="/datasets"
                  variant="subtle"
                  size="sm"
                  rightIcon={<IconEye size={16} />}
                >
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardBody>
              {recentDatasets.length === 0 ? (
                <div className="text-center py-6">
                  <IconDatabase size={48} className="mx-auto text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                    No datasets yet
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Upload your first dataset to get started.
                  </p>
                  <div className="mt-6">
                    <Button component={Link} to="/datasets/upload" size="sm">
                      Upload Dataset
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentDatasets.map((dataset) => (
                    <div key={dataset.id} className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <IconDatabase size={20} className="text-blue-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {dataset.name}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(dataset.created_at, 'relative')} • {dataset.file_size ? formatFileSize(dataset.file_size) : 'Unknown size'}
                        </p>
                      </div>
                      <div className="flex-shrink-0">
                        <Button
                          component={Link}
                          to={`/datasets/${dataset.id}`}
                          variant="subtle"
                          size="xs"
                        >
                          View
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Quick Actions
            </h3>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Button
                component={Link}
                to="/jobs/new/pinn"
                variant="outline"
                className="h-20 flex-col"
                leftIcon={<IconCalculator size={20} />}
              >
                <span className="font-medium">PINN Training</span>
                <span className="text-xs text-gray-500">Neural PDE Solver</span>
              </Button>
              <Button
                component={Link}
                to="/jobs/new/pde-discovery"
                variant="outline"
                className="h-20 flex-col"
                leftIcon={<IconChartBar size={20} />}
              >
                <span className="font-medium">PDE Discovery</span>
                <span className="text-xs text-gray-500">Symbolic Regression</span>
              </Button>
              <Button
                component={Link}
                to="/jobs/new/derivative"
                variant="outline"
                className="h-20 flex-col"
                leftIcon={<IconTrendingUp size={20} />}
              >
                <span className="font-medium">Derivatives</span>
                <span className="text-xs text-gray-500">Numerical Computation</span>
              </Button>
              <Button
                component={Link}
                to="/jobs/new/active-experiment"
                variant="outline"
                className="h-20 flex-col"
                leftIcon={<IconDatabase size={20} />}
              >
                <span className="font-medium">Active Learning</span>
                <span className="text-xs text-gray-500">Bayesian Optimization</span>
              </Button>
            </div>
          </CardBody>
        </Card>
      </div>
    </Layout>
  );
};

export default DashboardPage;