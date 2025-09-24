"use client";

import React, { useCallback, useState, useRef, DragEvent } from 'react';
import { Upload, FileText, AlertCircle, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  SUPPORTED_FILE_TYPES,
  SUPPORTED_FILE_EXTENSIONS,
  MAX_FILE_SIZE,
} from '@/lib/api/types/data-sources';

export interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  onError: (error: string) => void;
  acceptedTypes?: string[];
  maxFileSize?: number;
  disabled?: boolean;
  className?: string;
}

export function FileDropzone({
  onFileSelect,
  onError,
  acceptedTypes = [...SUPPORTED_FILE_TYPES],
  maxFileSize = MAX_FILE_SIZE,
  disabled = false,
  className,
}: FileDropzoneProps) {
  const [dragError, setDragError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isDragReject, setIsDragReject] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): { isValid: boolean; error?: string } => {
      // Check file size
      if (file.size > maxFileSize) {
        const sizeMB = (file.size / 1024 / 1024).toFixed(1);
        const maxSizeMB = (maxFileSize / 1024 / 1024).toFixed(0);
        return {
          isValid: false,
          error: `File size ${sizeMB}MB exceeds maximum allowed size of ${maxSizeMB}MB`,
        };
      }

      // Check file type
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      const isValidType = acceptedTypes.includes(file.type);
      const isValidExtension = SUPPORTED_FILE_EXTENSIONS.includes(extension as any);

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
    },
    [acceptedTypes, maxFileSize]
  );

  const handleFileSelection = useCallback(
    (files: FileList | null) => {
      setDragError(null);

      if (!files || files.length === 0) {
        const error = 'No files selected';
        setDragError(error);
        onError(error);
        return;
      }

      const file = files[0];
      const validation = validateFile(file);

      if (!validation.isValid) {
        const error = validation.error || 'File validation failed';
        setDragError(error);
        onError(error);
        return;
      }

      onFileSelect(file);
    },
    [onFileSelect, onError, validateFile]
  );

  const handleDragEnter = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);

    // Check if dragged items are valid
    const items = Array.from(e.dataTransfer.items);
    const hasValidFiles = items.some(item => {
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          const extension = '.' + file.name.split('.').pop()?.toLowerCase();
          return acceptedTypes.includes(file.type) || SUPPORTED_FILE_EXTENSIONS.includes(extension as any);
        }
      }
      return false;
    });

    setIsDragReject(!hasValidFiles);
  }, [acceptedTypes]);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    // Only set drag to false if we're leaving the dropzone entirely
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;

    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      setIsDragActive(false);
      setIsDragReject(false);
    }
  }, []);

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);
      setIsDragReject(false);

      const files = e.dataTransfer.files;
      handleFileSelection(files);
    },
    [handleFileSelection]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFileSelection(e.target.files);
    },
    [handleFileSelection]
  );

  const handleClick = useCallback(() => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [disabled]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={cn('w-full', className)}>
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        className={cn(
          'relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer',
          'hover:border-primary/50 hover:bg-primary/5',
          {
            'border-primary bg-primary/10': isDragActive && !isDragReject,
            'border-destructive bg-destructive/10': isDragReject || dragError,
            'border-muted-foreground/25 bg-muted/20': !isDragActive && !dragError,
            'opacity-50 cursor-not-allowed': disabled,
          }
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleInputChange}
          accept={SUPPORTED_FILE_EXTENSIONS.join(',')}
          className="hidden"
          disabled={disabled}
        />

        <div className="flex flex-col items-center space-y-4">
          {/* Icon */}
          <div
            className={cn(
              'w-16 h-16 rounded-full flex items-center justify-center',
              'bg-primary/10 text-primary',
              {
                'bg-destructive/10 text-destructive': isDragReject || dragError,
                'bg-primary/20 text-primary scale-110': isDragActive && !isDragReject,
              }
            )}
          >
            {isDragReject || dragError ? (
              <AlertCircle className="w-8 h-8" />
            ) : (
              <Upload className="w-8 h-8" />
            )}
          </div>

          {/* Text */}
          <div className="space-y-2">
            <p className="text-lg font-medium">
              {isDragActive
                ? isDragReject
                  ? 'Invalid file type'
                  : 'Drop your file here'
                : 'Drag & drop your data file here'}
            </p>
            <p className="text-sm text-muted-foreground">
              or{' '}
              <Button variant="link" className="p-0 h-auto text-primary">
                browse files
              </Button>
            </p>
          </div>

          {/* File type badges */}
          <div className="flex flex-wrap gap-2 justify-center">
            {SUPPORTED_FILE_EXTENSIONS.map((ext) => (
              <Badge key={ext} variant="secondary" className="text-xs">
                {ext.toUpperCase()}
              </Badge>
            ))}
          </div>

          {/* File size limit */}
          <p className="text-xs text-muted-foreground">
            Maximum file size: {formatFileSize(maxFileSize)}
          </p>
        </div>
      </div>

      {/* Error Display */}
      {dragError && (
        <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{dragError}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setDragError(null)}
              className="h-auto p-1"
            >
              <X className="h-4 w-4" />
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}

export default FileDropzone;