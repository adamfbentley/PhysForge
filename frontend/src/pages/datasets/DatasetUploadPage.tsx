import React, { useState, useCallback } from 'react';
import { useDropzone } from '@mantine/dropzone';
import { Link } from 'react-router-dom';
import { Layout } from '../../components/layout/Layout';
import { Card, CardHeader, CardBody } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input, TextArea } from '../../components/ui/Input';
import { Loading } from '../../components/ui/Loading';
import { useDatasetsStore } from '../../stores/datasetsStore';
import { useNotificationsStore } from '../../stores/notificationsStore';
import { validateFileType, formatFileSize } from '../../utils';
import { FILE_TYPES, MAX_FILE_SIZE } from '../../constants';
import {
  IconUpload,
  IconFile,
  IconX,
  IconCheck,
  IconAlertCircle,
  IconDatabase
} from '@tabler/icons-react';

const DatasetUploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState({
    name: '',
    description: '',
    tags: [] as string[],
  });
  const [tagInput, setTagInput] = useState('');

  const { uploadDataset, isLoading, error } = useDatasetsStore();
  const { addNotification } = useNotificationsStore();

  const onDrop = useCallback((files: File[]) => {
    const file = files[0];
    if (file) {
      if (file.size > MAX_FILE_SIZE) {
        addNotification({
          type: 'error',
          title: 'File too large',
          message: `File size exceeds maximum limit of ${formatFileSize(MAX_FILE_SIZE)}`,
        });
        return;
      }

      if (!validateFileType(file)) {
        addNotification({
          type: 'error',
          title: 'Invalid file type',
          message: 'Please upload a supported file format (HDF5, CSV, JSON, NumPy, MATLAB)',
        });
        return;
      }

      setSelectedFile(file);
      // Auto-fill name if empty
      if (!metadata.name) {
        setMetadata(prev => ({
          ...prev,
          name: file.name.replace(/\.[^/.]+$/, ''), // Remove extension
        }));
      }
    }
  }, [metadata.name, addNotification]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      'application/x-hdf5': ['.h5', '.hdf5'],
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'application/octet-stream': ['.npy'],
      'application/matlab-mat': ['.mat'],
    },
  });

  const handleAddTag = () => {
    if (tagInput.trim() && !metadata.tags.includes(tagInput.trim())) {
      setMetadata(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()],
      }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setMetadata(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      addNotification({
        type: 'error',
        title: 'No file selected',
        message: 'Please select a file to upload',
      });
      return;
    }

    if (!metadata.name.trim()) {
      addNotification({
        type: 'error',
        title: 'Name required',
        message: 'Please provide a name for the dataset',
      });
      return;
    }

    try {
      await uploadDataset(selectedFile, {
        name: metadata.name.trim(),
        description: metadata.description.trim(),
        tags: metadata.tags,
        metadata: {},
      });

      addNotification({
        type: 'success',
        title: 'Upload successful',
        message: `Dataset "${metadata.name}" has been uploaded successfully`,
      });

      // Reset form
      setSelectedFile(null);
      setMetadata({
        name: '',
        description: '',
        tags: [],
      });
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Upload failed',
        message: err instanceof Error ? err.message : 'Failed to upload dataset',
      });
    }
  };

  const supportedFormats = [
    { ext: '.h5, .hdf5', type: 'HDF5', desc: 'Hierarchical Data Format' },
    { ext: '.csv', type: 'CSV', desc: 'Comma-separated values' },
    { ext: '.json', type: 'JSON', desc: 'JavaScript Object Notation' },
    { ext: '.npy', type: 'NumPy', desc: 'NumPy array file' },
    { ext: '.mat', type: 'MATLAB', desc: 'MATLAB data file' },
  ];

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Upload Dataset
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Upload scientific datasets for analysis and model training
            </p>
          </div>
          <Button
            component={Link}
            to="/datasets"
            variant="outline"
            leftIcon={<IconDatabase size={16} />}
          >
            Browse Datasets
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Dataset Information
                </h2>
              </CardHeader>
              <CardBody>
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* File Upload */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      File Upload
                    </label>
                    <div
                      {...getRootProps()}
                      className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                        isDragActive
                          ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                      }`}
                    >
                      <input {...getInputProps()} />
                      {selectedFile ? (
                        <div className="flex items-center justify-center space-x-3">
                          <IconFile size={24} className="text-green-500" />
                          <div className="text-left">
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {selectedFile.name}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {formatFileSize(selectedFile.size)}
                            </p>
                          </div>
                          <Button
                            type="button"
                            variant="subtle"
                            size="xs"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedFile(null);
                            }}
                          >
                            <IconX size={16} />
                          </Button>
                        </div>
                      ) : (
                        <div>
                          <IconUpload size={48} className="mx-auto text-gray-400 mb-4" />
                          <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                            {isDragActive ? 'Drop the file here' : 'Drag & drop a file here'}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            or click to browse files
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Dataset Name */}
                  <Input
                    label="Dataset Name"
                    placeholder="Enter a descriptive name for your dataset"
                    value={metadata.name}
                    onChange={(e) => setMetadata(prev => ({ ...prev, name: e.target.value }))}
                    required
                  />

                  {/* Description */}
                  <TextArea
                    label="Description (Optional)"
                    placeholder="Provide additional details about your dataset"
                    value={metadata.description}
                    onChange={(e) => setMetadata(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                  />

                  {/* Tags */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Tags (Optional)
                    </label>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {metadata.tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                        >
                          {tag}
                          <button
                            type="button"
                            onClick={() => handleRemoveTag(tag)}
                            className="ml-1 hover:text-blue-600 dark:hover:text-blue-400"
                          >
                            <IconX size={12} />
                          </button>
                        </span>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Add a tag"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddTag();
                          }
                        }}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleAddTag}
                        disabled={!tagInput.trim()}
                      >
                        Add
                      </Button>
                    </div>
                  </div>

                  {/* Error Display */}
                  {error && (
                    <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
                      <IconAlertCircle size={16} />
                      <span className="text-sm">{error}</span>
                    </div>
                  )}

                  {/* Submit Button */}
                  <Button
                    type="submit"
                    fullWidth
                    loading={isLoading}
                    disabled={!selectedFile || !metadata.name.trim()}
                    leftIcon={<IconUpload size={16} />}
                  >
                    {isLoading ? 'Uploading...' : 'Upload Dataset'}
                  </Button>
                </form>
              </CardBody>
            </Card>
          </div>

          {/* Info Panel */}
          <div className="space-y-6">
            {/* Supported Formats */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Supported Formats
                </h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  {supportedFormats.map((format) => (
                    <div key={format.ext} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {format.ext}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {format.desc}
                        </p>
                      </div>
                      <IconCheck size={16} className="text-green-500" />
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Maximum file size: {formatFileSize(MAX_FILE_SIZE)}
                  </p>
                </div>
              </CardBody>
            </Card>

            {/* Upload Tips */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Upload Tips
                </h3>
              </CardHeader>
              <CardBody>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li>• Use descriptive names for easy identification</li>
                  <li>• Add relevant tags for better organization</li>
                  <li>• Include metadata in descriptions</li>
                  <li>• Ensure data is properly formatted</li>
                  <li>• Large files may take time to upload</li>
                </ul>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default DatasetUploadPage;