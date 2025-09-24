/**
 * React Hook for Managing Data Source File Uploads
 * Handles file validation, chunked uploads, progress tracking, and error states
 */

import { useState, useCallback, useRef } from 'react';
import { toast } from '@/hooks/use-toast';
import dataSourceAPI from '@/lib/api/data-sources';
import {
  DataSource,
  FileUploadState,
  FileValidationError,
  UploadTimeoutError,
  UploadOptions,
  SUPPORTED_FILE_TYPES,
  MAX_FILE_SIZE,
} from '@/lib/api/types/data-sources';
import { DataSourceAPIError } from '@/lib/api/types/data-sources';

// 从内容类型推断文件类型
function getFileTypeFromContentType(contentType: string): 'csv' | 'json' | 'excel' | 'parquet' | 'other' {
  if (contentType.includes('csv')) return 'csv';
  if (contentType.includes('json')) return 'json';
  if (contentType.includes('excel') || contentType.includes('spreadsheet')) return 'excel';
  if (contentType.includes('parquet')) return 'parquet';
  return 'other';
}

export interface UseDataSourceUploadOptions {
  projectId: number;
  onUploadComplete?: (dataset: DataSource) => void;
  onUploadError?: (error: string) => void;
  chunkSize?: number;
  timeout?: number;
}

export interface UseDataSourceUploadReturn {
  uploadState: FileUploadState;
  uploadFile: (file: File) => Promise<void>;
  cancelUpload: () => Promise<void>;
  resetUpload: () => void;
  validateFile: (file: File) => { isValid: boolean; error?: string };
}

export function useDataSourceUpload(
  options: UseDataSourceUploadOptions
): UseDataSourceUploadReturn {
  const [uploadState, setUploadState] = useState<FileUploadState>({
    file: null,
    isUploading: false,
    progress: 0,
    error: null,
    sessionId: null,
    dataset: null,
  });

  const uploadAbortController = useRef<AbortController | null>(null);
  const uploadTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const validateFile = useCallback((file: File): { isValid: boolean; error?: string } => {
    try {
      // Check file size
      if (file.size > MAX_FILE_SIZE) {
        const sizeMB = (file.size / 1024 / 1024).toFixed(1);
        const maxSizeMB = (MAX_FILE_SIZE / 1024 / 1024).toFixed(0);
        return {
          isValid: false,
          error: `File size ${sizeMB}MB exceeds maximum allowed size of ${maxSizeMB}MB`,
        };
      }

      // Check file type
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      const isValidType = SUPPORTED_FILE_TYPES.includes(file.type as any);
      const isValidExtension = ['.csv', '.json', '.xlsx', '.xls', '.parquet'].includes(extension);

      if (!isValidType && !isValidExtension) {
        return {
          isValid: false,
          error: 'Unsupported file type. Please upload CSV, JSON, Excel, or Parquet files.',
        };
      }

      // Check if file is empty
      if (file.size === 0) {
        return {
          isValid: false,
          error: 'File is empty. Please select a valid file.',
        };
      }

      return { isValid: true };
    } catch (error) {
      return {
        isValid: false,
        error: 'Failed to validate file. Please try again.',
      };
    }
  }, []);

  const resetUpload = useCallback(() => {
    if (uploadAbortController.current) {
      uploadAbortController.current.abort();
    }
    if (uploadTimeoutRef.current) {
      clearTimeout(uploadTimeoutRef.current);
    }

    setUploadState({
      file: null,
      isUploading: false,
      progress: 0,
      error: null,
      sessionId: null,
      dataset: null,
    });
  }, []);

  const cancelUpload = useCallback(async () => {
    try {
      if (uploadState.sessionId && uploadState.isUploading) {
        await dataSourceAPI.cancelUpload(uploadState.sessionId);
        toast({
          title: 'Upload Cancelled',
          description: 'File upload has been cancelled successfully.',
        });
      }
    } catch (error) {
      console.error('Failed to cancel upload:', error);
      toast({
        title: 'Cancel Failed',
        description: 'Failed to cancel upload. Please try again.',
        variant: 'destructive',
      });
    } finally {
      resetUpload();
    }
  }, [uploadState.sessionId, uploadState.isUploading, resetUpload]);

  const uploadFile = useCallback(
    async (file: File) => {
      // Validate file first
      const validation = validateFile(file);
      if (!validation.isValid) {
        const error = validation.error || 'File validation failed';
        setUploadState(prev => ({ ...prev, error }));
        options.onUploadError?.(error);
        toast({
          title: 'Invalid File',
          description: error,
          variant: 'destructive',
        });
        return;
      }

      // Reset previous state
      setUploadState(prev => ({
        ...prev,
        file,
        isUploading: true,
        progress: 0,
        error: null,
        sessionId: null,
        dataset: null,
      }));

      // Create abort controller for this upload
      uploadAbortController.current = new AbortController();

      // Set upload timeout
      if (options.timeout) {
        uploadTimeoutRef.current = setTimeout(() => {
          cancelUpload();
          const error = 'Upload timed out. Please try again.';
          setUploadState(prev => ({ ...prev, error, isUploading: false }));
          options.onUploadError?.(error);
          toast({
            title: 'Upload Timeout',
            description: error,
            variant: 'destructive',
          });
        }, options.timeout);
      }

      try {
        const uploadOptions: UploadOptions = {
          chunkSize: options.chunkSize,
          onProgress: (progress) => {
            setUploadState(prev => ({
              ...prev,
              progress: progress.percentage,
            }));
          },
        };

        toast({
          title: 'Upload Started',
          description: `Uploading ${file.name}...`,
        });

        const response = await dataSourceAPI.uploadFile(
          file,
          options.projectId,
          uploadOptions
        );

        if (response.success && response.file) {
          // 创建一个DataSource对象，基于后端返回的文件信息
          const dataset: DataSource = {
            id: parseInt(response.file.id.replace(/\D/g, '')) || Date.now(), // 提取数字作为ID
            name: response.file.filename,
            type: getFileTypeFromContentType(response.file.content_type),
            status: 'ready' as const,
            file_size: response.file.size,
            rows_count: null,
            columns_count: null,
            created_at: response.file.uploaded_at,
            updated_at: response.file.uploaded_at,
          };

          setUploadState(prev => ({
            ...prev,
            isUploading: false,
            progress: 100,
            sessionId: null, // 简化版后端没有session概念
            dataset,
          }));

          options.onUploadComplete?.(dataset);

          toast({
            title: 'Upload Complete',
            description: `${file.name} has been uploaded successfully!`,
            variant: 'default',
          });
        } else {
          throw new Error(response.message || 'Upload failed');
        }
      } catch (error) {
        let errorMessage = 'Upload failed';

        if (error instanceof DataSourceAPIError) {
          errorMessage = error.detail;

          // Handle authentication errors specifically
          if (error.statusCode === 401) {
            errorMessage = 'Authentication required. Please log in and try again.';
            toast({
              title: 'Authentication Required',
              description: 'Please log in to upload files.',
              variant: 'destructive',
            });
          }
        } else if (error instanceof Error) {
          errorMessage = error.message;
        }

        setUploadState(prev => ({
          ...prev,
          isUploading: false,
          error: errorMessage,
        }));

        options.onUploadError?.(errorMessage);

        // Only show toast if not authentication error (already shown above)
        if (!(error instanceof DataSourceAPIError && error.statusCode === 401)) {
          toast({
            title: 'Upload Failed',
            description: errorMessage,
            variant: 'destructive',
          });
        }
      } finally {
        // Clean up
        if (uploadTimeoutRef.current) {
          clearTimeout(uploadTimeoutRef.current);
          uploadTimeoutRef.current = null;
        }
        uploadAbortController.current = null;
      }
    },
    [options, validateFile, cancelUpload]
  );

  return {
    uploadState,
    uploadFile,
    cancelUpload,
    resetUpload,
    validateFile,
  };
}

export default useDataSourceUpload;