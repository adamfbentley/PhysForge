import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../../components/layout/Layout';
import { Card, CardHeader, CardBody } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { useDatasetsStore } from '../../stores/datasetsStore';
import { useNotificationsStore } from '../../stores/notificationsStore';
import { Dataset } from '../../types';
import {
  IconPlus,
  IconDatabase,
  IconDownload,
  IconEye,
  IconTrash,
  IconFileText,
  IconTable,
  IconChartLine,
  IconSearch,
} from '@tabler/icons-react';
import { Badge, TextInput, Select } from '@mantine/core';

const DatasetsPage: React.FC = () => {
  const {
    datasets,
    isLoading,
    fetchDatasets,
    deleteDataset,
    previewDataset
  } = useDatasetsStore();
  const { addNotification } = useNotificationsStore();

  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('created_at');

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  const handleDeleteDataset = async (datasetId: string, datasetName: string) => {
    if (window.confirm(`Are you sure you want to delete "${datasetName}"? This action cannot be undone.`)) {
      try {
        await deleteDataset(datasetId);
        addNotification({
          type: 'success',
          title: 'Dataset deleted',
          message: `"${datasetName}" has been deleted successfully`,
        });
      } catch (err) {
        addNotification({
          type: 'error',
          title: 'Deletion failed',
          message: err instanceof Error ? err.message : 'Failed to delete dataset',
        });
      }
    }
  };

  const handlePreviewDataset = async (dataset: Dataset) => {
    try {
      const preview = await previewDataset(dataset.id);
      // TODO: Show preview modal or navigate to preview page
      console.log('Dataset preview:', preview);
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Preview failed',
        message: err instanceof Error ? err.message : 'Failed to load dataset preview',
      });
    }
  };

  const filteredAndSortedDatasets = datasets
    .filter(dataset => {
      const matchesSearch = dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          dataset.description?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = filterType === 'all' || dataset.data_type === filterType;
      return matchesSearch && matchesType;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'size':
          return (b.size || 0) - (a.size || 0);
        case 'created_at':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

  const getDataTypeIcon = (dataType: string) => {
    switch (dataType) {
      case 'csv':
      case 'excel':
        return <IconTable size={16} />;
      case 'json':
        return <IconFileText size={16} />;
      case 'numpy':
      case 'matlab':
        return <IconChartLine size={16} />;
      default:
        return <IconDatabase size={16} />;
    }
  };

  const getDataTypeColor = (dataType: string) => {
    switch (dataType) {
      case 'csv':
        return 'green';
      case 'excel':
        return 'blue';
      case 'json':
        return 'purple';
      case 'numpy':
        return 'orange';
      case 'matlab':
        return 'red';
      default:
        return 'gray';
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (isLoading && datasets.length === 0) {
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
              Datasets
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Manage your uploaded datasets and data files
            </p>
          </div>
          <Button
            component={Link}
            to="/datasets/upload"
            leftIcon={<IconPlus size={16} />}
          >
            Upload Dataset
          </Button>
        </div>

        {/* Filters and Search */}
        <Card>
          <CardBody>
            <div className="flex flex-col sm:flex-row gap-4">
              <TextInput
                placeholder="Search datasets..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                leftSection={<IconSearch size={16} />}
                className="flex-1"
              />
              <Select
                placeholder="Filter by type"
                value={filterType}
                onChange={(value) => setFilterType(value || 'all')}
                data={[
                  { value: 'all', label: 'All Types' },
                  { value: 'csv', label: 'CSV' },
                  { value: 'excel', label: 'Excel' },
                  { value: 'json', label: 'JSON' },
                  { value: 'numpy', label: 'NumPy' },
                  { value: 'matlab', label: 'MATLAB' },
                ]}
                className="w-full sm:w-48"
              />
              <Select
                placeholder="Sort by"
                value={sortBy}
                onChange={(value) => setSortBy(value || 'created_at')}
                data={[
                  { value: 'created_at', label: 'Date Created' },
                  { value: 'name', label: 'Name' },
                  { value: 'size', label: 'Size' },
                ]}
                className="w-full sm:w-48"
              />
            </div>
          </CardBody>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardBody className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {datasets.length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Total Datasets
              </div>
            </CardBody>
          </Card>
          <Card>
            <CardBody className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {datasets.filter(d => d.status === 'processed').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Processed
              </div>
            </CardBody>
          </Card>
          <Card>
            <CardBody className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {datasets.filter(d => d.status === 'processing').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Processing
              </div>
            </CardBody>
          </Card>
          <Card>
            <CardBody className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {formatFileSize(datasets.reduce((sum, d) => sum + (d.size || 0), 0))}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Total Size
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Datasets List */}
        <div className="space-y-4">
          {filteredAndSortedDatasets.length === 0 ? (
            <Card>
              <CardBody className="text-center py-12">
                <IconDatabase size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  {datasets.length === 0 ? 'No datasets found' : 'No matching datasets'}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {datasets.length === 0
                    ? "You haven't uploaded any datasets yet."
                    : 'Try adjusting your search or filter criteria.'
                  }
                </p>
                {datasets.length === 0 && (
                  <Button
                    component={Link}
                    to="/datasets/upload"
                    leftIcon={<IconPlus size={16} />}
                  >
                    Upload Your First Dataset
                  </Button>
                )}
              </CardBody>
            </Card>
          ) : (
            filteredAndSortedDatasets.map((dataset) => (
              <Card key={dataset.id}>
                <CardBody>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0 mt-1">
                        {getDataTypeIcon(dataset.data_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
                            {dataset.name}
                          </h3>
                          <Badge color={getDataTypeColor(dataset.data_type)} size="sm">
                            {dataset.data_type.toUpperCase()}
                          </Badge>
                          <Badge
                            color={dataset.status === 'processed' ? 'green' :
                                   dataset.status === 'processing' ? 'yellow' : 'red'}
                            size="sm"
                          >
                            {dataset.status}
                          </Badge>
                        </div>
                        {dataset.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            {dataset.description}
                          </p>
                        )}

                        {/* Metadata */}
                        <div className="flex items-center space-x-6 text-xs text-gray-500 dark:text-gray-400">
                          <span>Size: {formatFileSize(dataset.size)}</span>
                          <span>Uploaded: {new Date(dataset.created_at).toLocaleDateString()}</span>
                          {dataset.num_rows && <span>Rows: {dataset.num_rows.toLocaleString()}</span>}
                          {dataset.num_columns && <span>Columns: {dataset.num_columns}</span>}
                        </div>

                        {/* Tags */}
                        {dataset.tags && dataset.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {dataset.tags.map((tag, index) => (
                              <Badge key={index} size="sm" variant="light">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {/* Actions */}
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          leftIcon={<IconEye size={14} />}
                          onClick={() => handlePreviewDataset(dataset)}
                        >
                          Preview
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          leftIcon={<IconDownload size={14} />}
                          onClick={() => {
                            // TODO: Implement download
                            console.log('Download dataset:', dataset.id);
                          }}
                        >
                          Download
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          color="red"
                          leftIcon={<IconTrash size={14} />}
                          onClick={() => handleDeleteDataset(dataset.id, dataset.name)}
                        >
                          Delete
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
        {datasets.length > 0 && (
          <div className="text-center">
            <Button
              variant="outline"
              onClick={() => fetchDatasets()}
              loading={isLoading}
            >
              {isLoading ? 'Loading...' : 'Load More Datasets'}
            </Button>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default DatasetsPage;