"use client";

import React, { useState, useCallback } from 'react';
import {
  Upload,
  Database,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  RefreshCw,
  AlertCircle,
  FileText,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { toast } from '@/hooks/use-toast';

// Import our custom components
import FileDropzone from '@/components/ui/file-dropzone';
import UploadProgress from '@/components/ui/upload-progress';
import DataPreviewTable from '@/components/ui/data-preview-table';

// Import hooks
import useDataSourceUpload from '@/hooks/use-data-source-upload';
import useDataPreview from '@/hooks/use-data-preview';

// Import types
import {
  DataSource,
  DataSourceConnectionState,
  DataSourcePreview,
  ColumnInfo,
} from '@/lib/api/types/data-sources';

export interface DataSourceConnectionProps {
  projectId: number;
  onConnectionComplete?: (dataset: DataSource) => void;
  onCancel?: () => void;
  className?: string;
}

type ConnectionStep = 'select' | 'upload' | 'preview' | 'complete';

export function DataSourceConnection({
  projectId,
  onConnectionComplete,
  onCancel,
  className,
}: DataSourceConnectionProps) {
  const [currentStep, setCurrentStep] = useState<ConnectionStep>('select');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [completedDataset, setCompletedDataset] = useState<DataSource | null>(null);

  // Upload hook
  const {
    uploadState,
    uploadFile,
    cancelUpload,
    resetUpload,
    validateFile,
  } = useDataSourceUpload({
    projectId,
    onUploadComplete: (dataset) => {
      setCompletedDataset(dataset);
      setCurrentStep('preview');
      toast({
        title: 'Upload Complete',
        description: 'Your data source has been uploaded successfully!',
      });
    },
    onUploadError: (error) => {
      toast({
        title: 'Upload Failed',
        description: error,
        variant: 'destructive',
      });
    },
  });

  // 使用useCallback稳定回调函数引用，避免无限循环
  const handlePreviewLoad = useCallback((preview: any) => {
    toast({
      title: 'Preview Loaded',
      description: `Loaded preview with ${preview.rows_count} rows and ${preview.columns_count} columns`,
    });
  }, []);

  const handlePreviewError = useCallback((error: string) => {
    toast({
      title: 'Preview Error',
      description: error,
      variant: 'destructive',
    });
  }, []);

  // Preview hook
  const {
    state: previewState,
    loadPreview,
    triggerAnalysis,
    resetPreview,
  } = useDataPreview({
    datasetId: completedDataset?.id || null,
    autoLoad: true,
    onPreviewLoad: handlePreviewLoad,
    onError: handlePreviewError,
  });

  const handleFileSelect = useCallback(
    async (file: File) => {
      const validation = validateFile(file);
      if (!validation.isValid) {
        toast({
          title: 'Invalid File',
          description: validation.error,
          variant: 'destructive',
        });
        return;
      }

      setSelectedFile(file);
      setCurrentStep('upload');

      // Start upload immediately
      await uploadFile(file);
    },
    [uploadFile, validateFile]
  );

  const handleFileError = useCallback((error: string) => {
    toast({
      title: 'File Error',
      description: error,
      variant: 'destructive',
    });
  }, []);

  const handleCancelUpload = useCallback(async () => {
    await cancelUpload();
    setSelectedFile(null);
    setCurrentStep('select');
  }, [cancelUpload]);

  const handleRestart = useCallback(() => {
    resetUpload();
    resetPreview();
    setSelectedFile(null);
    setCompletedDataset(null);
    setCurrentStep('select');
  }, [resetUpload, resetPreview]);

  const handleComplete = useCallback(() => {
    if (completedDataset) {
      setCurrentStep('complete');
      onConnectionComplete?.(completedDataset);
      toast({
        title: 'Connection Complete',
        description: 'Your data source is now ready for analysis!',
        variant: 'default',
      });
    }
  }, [completedDataset, onConnectionComplete]);

  const handleAnalyze = useCallback(async () => {
    if (completedDataset) {
      await triggerAnalysis();
    }
  }, [completedDataset, triggerAnalysis]);

  const getStepConfig = (step: ConnectionStep) => {
    const baseConfig = {
      select: {
        title: 'Select Data Source',
        description: 'Choose a file to upload and connect as a data source',
        icon: Upload,
        color: 'text-blue-600',
      },
      upload: {
        title: 'Upload in Progress',
        description: 'Your file is being uploaded and processed',
        icon: Database,
        color: 'text-yellow-600',
      },
      preview: {
        title: 'Data Preview',
        description: 'Review your data structure and quality',
        icon: BarChart3,
        color: 'text-purple-600',
      },
      complete: {
        title: 'Connection Complete',
        description: 'Your data source is ready for analysis',
        icon: CheckCircle,
        color: 'text-green-600',
      },
    };

    return baseConfig[step];
  };

  const currentStepConfig = getStepConfig(currentStep);

  const renderStepIndicator = () => {
    const steps: ConnectionStep[] = ['select', 'upload', 'preview', 'complete'];
    const currentIndex = steps.indexOf(currentStep);

    return (
      <div className="flex items-center justify-center space-x-4 mb-8">
        {steps.map((step, index) => {
          const config = getStepConfig(step);
          const Icon = config.icon;
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex;
          const isUpcoming = index > currentIndex;

          return (
            <React.Fragment key={step}>
              <div className="flex flex-col items-center space-y-2">
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-200',
                    {
                      'bg-primary border-primary text-primary-foreground': isActive,
                      'bg-green-100 border-green-500 text-green-600': isCompleted,
                      'bg-muted border-muted-foreground text-muted-foreground': isUpcoming,
                    }
                  )}
                >
                  <Icon className="w-5 h-5" />
                </div>
                <span
                  className={cn(
                    'text-xs font-medium text-center max-w-20',
                    {
                      'text-primary': isActive,
                      'text-green-600': isCompleted,
                      'text-muted-foreground': isUpcoming,
                    }
                  )}
                >
                  {config.title}
                </span>
              </div>
              {index < steps.length - 1 && (
                <ArrowRight
                  className={cn(
                    'w-4 h-4 transition-colors duration-200',
                    {
                      'text-primary': index < currentIndex,
                      'text-muted-foreground': index >= currentIndex,
                    }
                  )}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  return (
    <div className={cn('w-full max-w-4xl mx-auto space-y-6', className)}>
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Data Source Connection</h1>
        <p className="text-muted-foreground">
          Connect your data files to start analyzing and building insights
        </p>
      </div>

      {/* Step Indicator */}
      {renderStepIndicator()}

      {/* Main Content */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <currentStepConfig.icon className={cn('w-6 h-6', currentStepConfig.color)} />
            <span>{currentStepConfig.title}</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            {currentStepConfig.description}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Step Content */}
          {currentStep === 'select' && (
            <div className="space-y-4">
              <FileDropzone
                onFileSelect={handleFileSelect}
                onError={handleFileError}
                className="min-h-[300px]"
              />
              <Alert>
                <FileText className="h-4 w-4" />
                <AlertDescription>
                  Supported formats: CSV, JSON, Excel (.xlsx, .xls), and Parquet files up to 100MB
                </AlertDescription>
              </Alert>
            </div>
          )}

          {currentStep === 'upload' && selectedFile && (
            <div className="space-y-4">
              <UploadProgress
                progress={uploadState.progress}
                fileName={selectedFile.name}
                fileSize={selectedFile.size}
                uploadedSize={(uploadState.progress / 100) * selectedFile.size}
                onCancel={handleCancelUpload}
                status={
                  uploadState.isUploading
                    ? 'uploading'
                    : uploadState.error
                    ? 'error'
                    : uploadState.dataset
                    ? 'completed'
                    : 'processing'
                }
                error={uploadState.error || undefined}
              />
              {uploadState.error && (
                <div className="flex justify-center space-x-2">
                  <Button variant="outline" onClick={handleRestart}>
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Start Over
                  </Button>
                  <Button onClick={() => handleFileSelect(selectedFile)}>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Retry Upload
                  </Button>
                </div>
              )}
            </div>
          )}

          {currentStep === 'preview' && completedDataset && (
            <div className="space-y-4">
              {previewState.loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-center space-y-2">
                    <RefreshCw className="w-8 h-8 animate-spin mx-auto text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">Loading preview...</p>
                  </div>
                </div>
              ) : previewState.error ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{previewState.error}</AlertDescription>
                </Alert>
              ) : previewState.preview ? (
                <DataPreviewTable
                  preview={previewState.preview}
                  qualityChecks={previewState.qualityChecks}
                  maxRows={10}
                />
              ) : null}

              <div className="flex justify-center space-x-2">
                <Button variant="outline" onClick={handleRestart}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Upload Different File
                </Button>
                <Button variant="outline" onClick={handleAnalyze}>
                  <BarChart3 className="w-4 h-4 mr-2" />
                  Run Analysis
                </Button>
                <Button onClick={handleComplete}>
                  Complete Connection
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {currentStep === 'complete' && completedDataset && (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-semibold">Data Source Connected!</h3>
                <p className="text-muted-foreground">
                  Your data source "{completedDataset.name}" is now ready for analysis
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-md mx-auto">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {completedDataset.rows_count?.toLocaleString() || '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">Rows</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {completedDataset.columns_count || '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">Columns</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {completedDataset.file_size
                      ? `${(completedDataset.file_size / 1024 / 1024).toFixed(1)}MB`
                      : '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">Size</div>
                </div>
                <div className="text-center">
                  <Badge variant={completedDataset.status === 'ready' ? 'default' : 'secondary'}>
                    {completedDataset.status}
                  </Badge>
                </div>
              </div>
              <div className="flex justify-center space-x-2">
                <Button variant="outline" onClick={handleRestart}>
                  Connect Another Source
                </Button>
                <Button onClick={() => onCancel?.()}>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Done
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default DataSourceConnection;