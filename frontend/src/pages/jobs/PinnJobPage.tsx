import React, { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
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
  IconCalculator,
  IconPlus,
  IconTrash,
  IconInfoCircle,
  IconChevronDown,
  IconChevronUp
} from '@tabler/icons-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@mantine/core';

const pinnJobSchema = z.object({
  model_architecture: z.object({
    layers: z.array(z.number().min(1)).min(1, 'At least one layer required'),
    activations: z.array(z.string().min(1)).min(1, 'At least one activation required'),
  }),
  training: z.object({
    learning_rate: z.number().min(0.000001).max(1),
    epochs: z.number().min(1).max(100000),
    optimizer: z.enum(['adam', 'sgd', 'rmsprop', 'adagrad']),
    batch_size: z.number().min(1).max(10000),
  }),
  data: z.object({
    dataset_id: z.string().min(1, 'Dataset selection is required'),
    domain_bounds: z.array(z.tuple([z.number(), z.number()])).min(1),
    num_collocation_points: z.number().min(100).max(100000),
    num_boundary_points: z.number().min(10).max(10000),
  }),
  physics: z.object({
    pde_equation: z.string().min(1, 'PDE equation is required'),
    boundary_conditions: z.array(z.string()).min(1, 'At least one boundary condition required'),
    initial_conditions: z.array(z.string()).optional(),
  }),
});

type PinnJobFormData = z.infer<typeof pinnJobSchema>;

const PinnJobPage: React.FC = () => {
  const [expandedSections, setExpandedSections] = useState({
    architecture: true,
    training: false,
    data: false,
    physics: false,
  });

  const { submitJob, isLoading } = useJobsStore();
  const { datasets } = useDatasetsStore();
  const { addNotification } = useNotificationsStore();

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<PinnJobFormData>({
    resolver: zodResolver(pinnJobSchema),
    defaultValues: {
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
        pde_equation: '∂²u/∂x² + ∂²u/∂y² = 0',
        boundary_conditions: ['u(x,0) = 0', 'u(x,1) = sin(πx)', 'u(0,y) = 0', 'u(1,y) = 0'],
      },
    },
  });

  const {
    fields: layerFields,
    append: appendLayer,
    remove: removeLayer,
  } = useFieldArray({
    control,
    name: 'model_architecture.layers',
  });

  const {
    fields: activationFields,
    append: appendActivation,
    remove: removeActivation,
  } = useFieldArray({
    control,
    name: 'model_architecture.activations',
  });

  const {
    fields: bcFields,
    append: appendBC,
    remove: removeBC,
  } = useFieldArray({
    control,
    name: 'physics.boundary_conditions',
  });

  const {
    fields: icFields,
    append: appendIC,
    remove: removeIC,
  } = useFieldArray({
    control,
    name: 'physics.initial_conditions',
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const onSubmit = async (data: PinnJobFormData) => {
    try {
      await submitJob(data, JobType.PINN_TRAINING);
      addNotification({
        type: 'success',
        title: 'Job submitted',
        message: 'PINN training job has been submitted successfully',
      });
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Submission failed',
        message: err instanceof Error ? err.message : 'Failed to submit job',
      });
    }
  };

  const watchedLayers = watch('model_architecture.layers');
  const watchedActivations = watch('model_architecture.activations');

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              PINN Training Job
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Configure and submit a Physics-Informed Neural Network training job
            </p>
          </div>
          <Button
            component={Link}
            to="/jobs"
            variant="outline"
            leftIcon={<IconCalculator size={16} />}
          >
            View Jobs
          </Button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Model Architecture */}
          <Card>
            <CardHeader>
              <CollapsibleTrigger
                onClick={() => toggleSection('architecture')}
                className="flex items-center justify-between w-full text-left"
              >
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Model Architecture
                </h2>
                {expandedSections.architecture ? (
                  <IconChevronUp size={20} />
                ) : (
                  <IconChevronDown size={20} />
                )}
              </CollapsibleTrigger>
            </CardHeader>
            <Collapsible open={expandedSections.architecture}>
              <CardBody className="space-y-4">
                {/* Layers */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Network Layers
                  </label>
                  <div className="space-y-2">
                    {layerFields.map((field, index) => (
                      <div key={field.id} className="flex items-center space-x-2">
                        <Input
                          type="number"
                          placeholder={`Layer ${index + 1} size`}
                          {...register(`model_architecture.layers.${index}` as const, {
                            valueAsNumber: true,
                          })}
                          className="flex-1"
                        />
                        {layerFields.length > 1 && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => removeLayer(index)}
                          >
                            <IconTrash size={16} />
                          </Button>
                        )}
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => appendLayer(50)}
                      leftIcon={<IconPlus size={16} />}
                    >
                      Add Layer
                    </Button>
                  </div>
                  {errors.model_architecture?.layers && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.model_architecture.layers.message}
                    </p>
                  )}
                </div>

                {/* Activations */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Activation Functions
                  </label>
                  <div className="space-y-2">
                    {activationFields.map((field, index) => (
                      <div key={field.id} className="flex items-center space-x-2">
                        <select
                          {...register(`model_architecture.activations.${index}` as const)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="tanh">Tanh</option>
                          <option value="relu">ReLU</option>
                          <option value="sigmoid">Sigmoid</option>
                          <option value="linear">Linear</option>
                          <option value="elu">ELU</option>
                          <option value="selu">SELU</option>
                        </select>
                        {activationFields.length > 1 && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => removeActivation(index)}
                          >
                            <IconTrash size={16} />
                          </Button>
                        )}
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => appendActivation('tanh')}
                      leftIcon={<IconPlus size={16} />}
                    >
                      Add Activation
                    </Button>
                  </div>
                </div>

                {/* Architecture Preview */}
                <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Network Preview
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                    Input({watchedLayers?.[0] || 0}) →
                    {watchedLayers?.slice(1, -1).map((layer, i) =>
                      ` ${watchedActivations?.[i] || 'tanh'}(${layer}) →`
                    ).join('')}
                    Output({watchedLayers?.[watchedLayers.length - 1] || 0})
                  </p>
                </div>
              </CardBody>
            </Collapsible>
          </Card>

          {/* Training Configuration */}
          <Card>
            <CardHeader>
              <CollapsibleTrigger
                onClick={() => toggleSection('training')}
                className="flex items-center justify-between w-full text-left"
              >
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Training Configuration
                </h2>
                {expandedSections.training ? (
                  <IconChevronUp size={20} />
                ) : (
                  <IconChevronDown size={20} />
                )}
              </CollapsibleTrigger>
            </CardHeader>
            <Collapsible open={expandedSections.training}>
              <CardBody className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Learning Rate"
                  type="number"
                  step="0.000001"
                  {...register('training.learning_rate', { valueAsNumber: true })}
                  error={errors.training?.learning_rate?.message}
                />

                <Input
                  label="Epochs"
                  type="number"
                  {...register('training.epochs', { valueAsNumber: true })}
                  error={errors.training?.epochs?.message}
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Optimizer
                  </label>
                  <select
                    {...register('training.optimizer')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="adam">Adam</option>
                    <option value="sgd">SGD</option>
                    <option value="rmsprop">RMSprop</option>
                    <option value="adagrad">Adagrad</option>
                  </select>
                </div>

                <Input
                  label="Batch Size"
                  type="number"
                  {...register('training.batch_size', { valueAsNumber: true })}
                  error={errors.training?.batch_size?.message}
                />
              </CardBody>
            </Collapsible>
          </Card>

          {/* Data Configuration */}
          <Card>
            <CardHeader>
              <CollapsibleTrigger
                onClick={() => toggleSection('data')}
                className="flex items-center justify-between w-full text-left"
              >
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Data Configuration
                </h2>
                {expandedSections.data ? (
                  <IconChevronUp size={20} />
                ) : (
                  <IconChevronDown size={20} />
                )}
              </CollapsibleTrigger>
            </CardHeader>
            <Collapsible open={expandedSections.data}>
              <CardBody className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Dataset
                  </label>
                  <select
                    {...register('data.dataset_id')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select a dataset...</option>
                    {datasets.map((dataset) => (
                      <option key={dataset.id} value={dataset.id}>
                        {dataset.name}
                      </option>
                    ))}
                  </select>
                  {errors.data?.dataset_id && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.data.dataset_id.message}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Collocation Points"
                    type="number"
                    {...register('data.num_collocation_points', { valueAsNumber: true })}
                    error={errors.data?.num_collocation_points?.message}
                  />

                  <Input
                    label="Boundary Points"
                    type="number"
                    {...register('data.num_boundary_points', { valueAsNumber: true })}
                    error={errors.data?.num_boundary_points?.message}
                  />
                </div>
              </CardBody>
            </Collapsible>
          </Card>

          {/* Physics Configuration */}
          <Card>
            <CardHeader>
              <CollapsibleTrigger
                onClick={() => toggleSection('physics')}
                className="flex items-center justify-between w-full text-left"
              >
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Physics Configuration
                </h2>
                {expandedSections.physics ? (
                  <IconChevronUp size={20} />
                ) : (
                  <IconChevronDown size={20} />
                )}
              </CollapsibleTrigger>
            </CardHeader>
            <Collapsible open={expandedSections.physics}>
              <CardBody className="space-y-4">
                <TextArea
                  label="PDE Equation"
                  placeholder="Enter the PDE equation (e.g., ∂²u/∂x² + ∂²u/∂y² = 0)"
                  {...register('physics.pde_equation')}
                  error={errors.physics?.pde_equation?.message}
                />

                {/* Boundary Conditions */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Boundary Conditions
                  </label>
                  <div className="space-y-2">
                    {bcFields.map((field, index) => (
                      <div key={field.id} className="flex items-center space-x-2">
                        <Input
                          placeholder={`Boundary condition ${index + 1}`}
                          {...register(`physics.boundary_conditions.${index}` as const)}
                          className="flex-1"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeBC(index)}
                        >
                          <IconTrash size={16} />
                        </Button>
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => appendBC('')}
                      leftIcon={<IconPlus size={16} />}
                    >
                      Add Boundary Condition
                    </Button>
                  </div>
                </div>

                {/* Initial Conditions (Optional) */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Initial Conditions (Optional)
                  </label>
                  <div className="space-y-2">
                    {icFields.map((field, index) => (
                      <div key={field.id} className="flex items-center space-x-2">
                        <Input
                          placeholder={`Initial condition ${index + 1}`}
                          {...register(`physics.initial_conditions.${index}` as const)}
                          className="flex-1"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeIC(index)}
                        >
                          <IconTrash size={16} />
                        </Button>
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => appendIC('')}
                      leftIcon={<IconPlus size={16} />}
                    >
                      Add Initial Condition
                    </Button>
                  </div>
                </div>
              </CardBody>
            </Collapsible>
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
              leftIcon={<IconCalculator size={16} />}
            >
              {isLoading ? 'Submitting...' : 'Submit Job'}
            </Button>
          </div>
        </form>
      </div>
    </Layout>
  );
};

export default PinnJobPage;