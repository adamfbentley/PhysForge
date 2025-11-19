import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Layout } from '../../components/layout/Layout';
import { Card, CardHeader, CardBody } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { useJobsStore } from '../../stores/jobsStore';
import { Job, JobStatus } from '../../types';
import {
  IconArrowLeft,
  IconDownload,
  IconEye,
  IconFormula,
  IconChartLine,
  IconCheck,
  IconX,
} from '@tabler/icons-react';
import { Badge, Tabs } from '@mantine/core';

const JobResultsPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const { jobs, fetchJobDetails, isLoading } = useJobsStore();
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    if (jobId) {
      const existingJob = jobs.find(j => j.id === jobId);
      if (existingJob) {
        setJob(existingJob);
      } else {
        fetchJobDetails(jobId).then(setJob);
      }
    }
  }, [jobId, jobs, fetchJobDetails]);

  if (isLoading || !job) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <Loading size="lg" />
        </div>
      </Layout>
    );
  }

  const renderPinnResults = () => {
    if (!job.results?.pinn_results) return null;

    const results = job.results.pinn_results;
    return (
      <div className="space-y-6">
        {/* Training Metrics */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Training Metrics
            </h3>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {results.final_loss?.toExponential(3)}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Final Loss
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {results.best_loss?.toExponential(3)}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Best Loss
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {results.epochs_trained}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Epochs Trained
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {results.training_time?.toFixed(1)}s
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Training Time
                </div>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Loss History */}
        {results.loss_history && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Loss History
              </h3>
            </CardHeader>
            <CardBody>
              <div className="h-64 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <IconChartLine size={48} className="mx-auto mb-2" />
                  <p>Loss history chart would be displayed here</p>
                  <p className="text-sm">Final loss: {results.final_loss?.toExponential(3)}</p>
                </div>
              </div>
            </CardBody>
          </Card>
        )}

        {/* Model Architecture */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Model Architecture
            </h3>
          </CardHeader>
          <CardBody>
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg font-mono text-sm">
              <div className="text-gray-700 dark:text-gray-300">
                Layers: [{results.model_architecture?.layers?.join(', ')}]<br/>
                Activations: [{results.model_architecture?.activations?.join(', ')}]
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  };

  const renderPdeDiscoveryResults = () => {
    if (!job.results?.pde_discovery_results) return null;

    const results = job.results.pde_discovery_results;
    return (
      <div className="space-y-6">
        {/* Discovered Equations */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Discovered Equations
            </h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {results.discovered_equations?.map((equation, index) => (
                <div key={index} className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Equation {index + 1}
                    </span>
                    <Badge color="green" size="sm">
                      Score: {equation.score?.toFixed(3)}
                    </Badge>
                  </div>
                  <div className="font-mono text-lg text-gray-900 dark:text-white">
                    {equation.equation}
                  </div>
                  {equation.complexity && (
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      Complexity: {equation.complexity}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Method Performance */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Method Performance
            </h3>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {results.method}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Discovery Method
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {results.total_candidates}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Total Candidates
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {results.discovery_time?.toFixed(1)}s
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Discovery Time
                </div>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              component={Link}
              to="/jobs"
              variant="outline"
              leftIcon={<IconArrowLeft size={16} />}
            >
              Back to Jobs
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Job Results
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {job.name || `Job ${job.id.slice(-8)}`}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge color={job.status === JobStatus.COMPLETED ? 'green' : 'red'} size="sm">
              {job.status}
            </Badge>
            <Button
              leftIcon={<IconDownload size={16} />}
              onClick={() => {
                // TODO: Implement download results
                console.log('Download results for job:', job.id);
              }}
            >
              Download Results
            </Button>
          </div>
        </div>

        {/* Job Summary */}
        <Card>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Job Type</div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {job.job_type.replace('_', ' ').toUpperCase()}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Submitted</div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {new Date(job.created_at).toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Duration</div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {job.duration ? `${Math.round(job.duration)}s` : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Status</div>
                <div className="flex items-center space-x-2">
                  {job.status === JobStatus.COMPLETED ? (
                    <IconCheck size={16} className="text-green-500" />
                  ) : (
                    <IconX size={16} className="text-red-500" />
                  )}
                  <span className="font-medium text-gray-900 dark:text-white">
                    {job.status}
                  </span>
                </div>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Results */}
        {job.status === JobStatus.COMPLETED && job.results ? (
          <Tabs defaultValue="results">
            <Tabs.List>
              <Tabs.Tab value="results" leftSection={<IconEye size={16} />}>
                Results
              </Tabs.Tab>
              <Tabs.Tab value="logs" leftSection={<IconFormula size={16} />}>
                Logs
              </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="results" pt="md">
              {job.job_type === 'pinn_training' && renderPinnResults()}
              {job.job_type === 'pde_discovery' && renderPdeDiscoveryResults()}
              {!['pinn_training', 'pde_discovery'].includes(job.job_type) && (
                <Card>
                  <CardBody className="text-center py-12">
                    <IconFormula size={48} className="mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">
                      Results visualization for this job type is not yet implemented.
                    </p>
                  </CardBody>
                </Card>
              )}
            </Tabs.Panel>

            <Tabs.Panel value="logs" pt="md">
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Job Logs
                  </h3>
                </CardHeader>
                <CardBody>
                  <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
                    {job.logs ? (
                      job.logs.split('\n').map((line, index) => (
                        <div key={index} className="whitespace-pre-wrap">
                          {line}
                        </div>
                      ))
                    ) : (
                      <div className="text-gray-400">No logs available</div>
                    )}
                  </div>
                </CardBody>
              </Card>
            </Tabs.Panel>
          </Tabs>
        ) : (
          <Card>
            <CardBody className="text-center py-12">
              <IconX size={48} className="mx-auto text-red-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No Results Available
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {job.status === JobStatus.FAILED
                  ? 'This job failed to complete. Check the logs for error details.'
                  : 'This job has not completed yet or has no results to display.'
                }
              </p>
            </CardBody>
          </Card>
        )}
      </div>
    </Layout>
  );
};

export default JobResultsPage;