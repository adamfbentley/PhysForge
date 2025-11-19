import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { Layout } from '../../components/layout/Layout';
import { Card, CardHeader, CardBody } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input, TextArea } from '../../components/ui/Input';
import { useJobsStore } from '../../stores/jobsStore';
import { useDatasetsStore } from '../../stores/datasetsStore';
import { useNotificationsStore } from '../../stores/notificationsStore';
import { JobType } from '../../types';
import {
  IconFormula,
  IconInfoCircle,
  IconChevronDown,
  IconChevronUp
} from '@tabler/icons-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@mantine/core';

const pdeDiscoverySchema = z.object({
  discovery_method: z.enum(['sindy', 'pysr', 'hybrid']),
  dataset_id: z.string().min(1, 'Dataset selection is required'),
  target_variables: z.array(z.string()).min(1, 'At least one target variable required'),
  input_variables: z.array(z.string()).min(1, 'At least one input variable required'),
  sindy_config: z.object({
    threshold: z.number().min(0.001).max(1),
    max_terms: z.number().min(1).max(100),
    poly_order: z.number().min(1).max(10),
  }).optional(),
  pysr_config: z.object({
    population_size: z.number().min(10).max(1000),
    max_evals: z.number().min(100).max(100000),
    binary_operators: z.array(z.string()),
    unary_operators: z.array(z.string()),
  }).optional(),
  hybrid_config: z.object({
    sindy_weight: z.number().min(0).max(1),
    pysr_weight: z.number().min(0).max(1),
  }).optional(),
});

type PdeDiscoveryFormData = z.infer<typeof pdeDiscoverySchema>;

const PdeDiscoveryPage: React.FC = () => {
  const [expandedSections, setExpandedSections] = useState({
    basic: true,
    sindy: false,
    pysr: false,
    hybrid: false,
  });

  const { submitJob, isLoading } = useJobsStore();
  const { datasets } = useDatasetsStore();
  const { addNotification } = useNotificationsStore();

  const {
    register,
    watch,
    setValue,
    handleSubmit,
    formState: { errors },
  } = useForm<PdeDiscoveryFormData>({
    resolver: zodResolver(pdeDiscoverySchema),
    defaultValues: {
      discovery_method: 'sindy',
      target_variables: ['u'],
      input_variables: ['x', 't'],
      sindy_config: {
        threshold: 0.05,
        max_terms: 10,
        poly_order: 3,
      },
      pysr_config: {
        population_size: 100,
        max_evals: 10000,
        binary_operators: ['+', '-', '*', '/'],
        unary_operators: ['sin', 'cos', 'exp', 'log'],
      },
      hybrid_config: {
        sindy_weight: 0.5,
        pysr_weight: 0.5,
      },
    },
  });

  const watchedMethod = watch('discovery_method');

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const onSubmit = async (data: PdeDiscoveryFormData) => {
    try {
      await submitJob(data, JobType.PDE_DISCOVERY);
      addNotification({
        type: 'success',
        title: 'Job submitted',
        message: 'PDE discovery job has been submitted successfully',
      });
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Submission failed',
        message: err instanceof Error ? err.message : 'Failed to submit job',
      });
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              PDE Discovery Job
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Discover governing equations from data using symbolic regression
            </p>
          </div>
          <Button
            component={Link}
            to="/jobs"
            variant="outline"
            leftIcon={<IconFormula size={16} />}
          >
            View Jobs
          </Button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Configuration */}
          <Card>
            <CardHeader>
              <CollapsibleTrigger
                onClick={() => toggleSection('basic')}
                className="flex items-center justify-between w-full text-left"
              >
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Basic Configuration
                </h2>
                {expandedSections.basic ? (
                  <IconChevronUp size={20} />
                ) : (
                  <IconChevronDown size={20} />
                )}
              </CollapsibleTrigger>
            </CardHeader>
            <Collapsible open={expandedSections.basic}>
              <CardBody className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Discovery Method
                  </label>
                  <select
                    {...register('discovery_method')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="sindy">SINDy (Sparse Identification)</option>
                    <option value="pysr">PySR (Symbolic Regression)</option>
                    <option value="hybrid">Hybrid Approach</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Dataset
                  </label>
                  <select
                    {...register('dataset_id')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select a dataset...</option>
                    {datasets.map((dataset) => (
                      <option key={dataset.id} value={dataset.id}>
                        {dataset.name}
                      </option>
                    ))}
                  </select>
                  {errors.dataset_id && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.dataset_id.message}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Target Variables
                    </label>
                    <Input
                      placeholder="e.g., u,v (comma-separated)"
                      {...register('target_variables')}
                      onChange={(e) => {
                        const value = e.target.value.split(',').map(v => v.trim()).filter(v => v);
                        setValue('target_variables', value);
                      }}
                    />
                    {errors.target_variables && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.target_variables.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Input Variables
                    </label>
                    <Input
                      placeholder="e.g., x,y,t (comma-separated)"
                      {...register('input_variables')}
                      onChange={(e) => {
                        const value = e.target.value.split(',').map(v => v.trim()).filter(v => v);
                        setValue('input_variables', value);
                      }}
                    />
                    {errors.input_variables && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.input_variables.message}
                      </p>
                    )}
                  </div>
                </div>
              </CardBody>
            </Collapsible>
          </Card>

          {/* SINDy Configuration */}
          {(watchedMethod === 'sindy' || watchedMethod === 'hybrid') && (
            <Card>
              <CardHeader>
                <CollapsibleTrigger
                  onClick={() => toggleSection('sindy')}
                  className="flex items-center justify-between w-full text-left"
                >
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    SINDy Configuration
                  </h2>
                  {expandedSections.sindy ? (
                    <IconChevronUp size={20} />
                  ) : (
                    <IconChevronDown size={20} />
                  )}
                </CollapsibleTrigger>
              </CardHeader>
              <Collapsible open={expandedSections.sindy}>
                <CardBody className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Input
                    label="Threshold"
                    type="number"
                    step="0.001"
                    {...register('sindy_config.threshold', { valueAsNumber: true })}
                    error={errors.sindy_config?.threshold?.message}
                  />

                  <Input
                    label="Max Terms"
                    type="number"
                    {...register('sindy_config.max_terms', { valueAsNumber: true })}
                    error={errors.sindy_config?.max_terms?.message}
                  />

                  <Input
                    label="Polynomial Order"
                    type="number"
                    {...register('sindy_config.poly_order', { valueAsNumber: true })}
                    error={errors.sindy_config?.poly_order?.message}
                  />
                </CardBody>
              </Collapsible>
            </Card>
          )}

          {/* PySR Configuration */}
          {(watchedMethod === 'pysr' || watchedMethod === 'hybrid') && (
            <Card>
              <CardHeader>
                <CollapsibleTrigger
                  onClick={() => toggleSection('pysr')}
                  className="flex items-center justify-between w-full text-left"
                >
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    PySR Configuration
                  </h2>
                  {expandedSections.pysr ? (
                    <IconChevronUp size={20} />
                  ) : (
                    <IconChevronDown size={20} />
                  )}
                </CollapsibleTrigger>
              </CardHeader>
              <Collapsible open={expandedSections.pysr}>
                <CardBody className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input
                      label="Population Size"
                      type="number"
                      {...register('pysr_config.population_size', { valueAsNumber: true })}
                      error={errors.pysr_config?.population_size?.message}
                    />

                    <Input
                      label="Max Evaluations"
                      type="number"
                      {...register('pysr_config.max_evals', { valueAsNumber: true })}
                      error={errors.pysr_config?.max_evals?.message}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Binary Operators
                      </label>
                      <Input
                        placeholder="+,-,*,/"
                        {...register('pysr_config.binary_operators')}
                        onChange={(e) => {
                          const value = e.target.value.split(',').map(op => op.trim()).filter(op => op);
                          setValue('pysr_config.binary_operators', value);
                        }}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Unary Operators
                      </label>
                      <Input
                        placeholder="sin,cos,exp,log"
                        {...register('pysr_config.unary_operators')}
                        onChange={(e) => {
                          const value = e.target.value.split(',').map(op => op.trim()).filter(op => op);
                          setValue('pysr_config.unary_operators', value);
                        }}
                      />
                    </div>
                  </div>
                </CardBody>
              </Collapsible>
            </Card>
          )}

          {/* Hybrid Configuration */}
          {watchedMethod === 'hybrid' && (
            <Card>
              <CardHeader>
                <CollapsibleTrigger
                  onClick={() => toggleSection('hybrid')}
                  className="flex items-center justify-between w-full text-left"
                >
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Hybrid Configuration
                  </h2>
                  {expandedSections.hybrid ? (
                    <IconChevronUp size={20} />
                  ) : (
                    <IconChevronDown size={20} />
                  )}
                </CollapsibleTrigger>
              </CardHeader>
              <Collapsible open={expandedSections.hybrid}>
                <CardBody className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="SINDy Weight"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    {...register('hybrid_config.sindy_weight', { valueAsNumber: true })}
                    error={errors.hybrid_config?.sindy_weight?.message}
                  />

                  <Input
                    label="PySR Weight"
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    {...register('hybrid_config.pysr_weight', { valueAsNumber: true })}
                    error={errors.hybrid_config?.pysr_weight?.message}
                  />
                </CardBody>
              </Collapsible>
            </Card>
          )}

          {/* Method Info */}
          <Card>
            <CardBody>
              <div className="flex items-start space-x-3">
                <IconInfoCircle size={20} className="text-blue-500 mt-0.5" />
                <div>
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                    About {watchedMethod?.toUpperCase()} Discovery
                  </h3>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {watchedMethod === 'sindy' && (
                      <>SINDy identifies sparse representations of nonlinear dynamical systems from data using sparse regression techniques.</>
                    )}
                    {watchedMethod === 'pysr' && (
                      <>PySR uses genetic programming and symbolic regression to discover mathematical expressions that best fit the data.</>
                    )}
                    {watchedMethod === 'hybrid' && (
                      <>Hybrid approach combines SINDy and PySR methods, weighting their contributions to find optimal PDE representations.</>
                    )}
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Submit */}
          <div className="flex justify-end space-x-4">
            <Button
              component={Link}
              to="/jobs"
              variant="outline"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              loading={isLoading}
              leftIcon={<IconFormula size={16} />}
            >
              {isLoading ? 'Submitting...' : 'Submit Job'}
            </Button>
          </div>
        </form>
      </div>
    </Layout>
  );
};

export default PdeDiscoveryPage;