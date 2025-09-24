"use client";

import React from 'react';
import { X, CheckCircle, AlertCircle, Loader2, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

export interface UploadProgressProps {
  progress: number;
  fileName: string;
  fileSize: number;
  uploadedSize: number;
  onCancel?: () => void;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  className?: string;
}

export function UploadProgress({
  progress,
  fileName,
  fileSize,
  uploadedSize,
  onCancel,
  status,
  error,
  className,
}: UploadProgressProps) {
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'uploading':
        return {
          icon: <Loader2 className="w-5 h-5 animate-spin" />,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50 border-blue-200',
          badge: { text: 'Uploading', variant: 'secondary' as const },
        };
      case 'processing':
        return {
          icon: <Loader2 className="w-5 h-5 animate-spin" />,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50 border-yellow-200',
          badge: { text: 'Processing', variant: 'secondary' as const },
        };
      case 'completed':
        return {
          icon: <CheckCircle className="w-5 h-5" />,
          color: 'text-green-600',
          bgColor: 'bg-green-50 border-green-200',
          badge: { text: 'Complete', variant: 'default' as const },
        };
      case 'error':
        return {
          icon: <AlertCircle className="w-5 h-5" />,
          color: 'text-red-600',
          bgColor: 'bg-red-50 border-red-200',
          badge: { text: 'Error', variant: 'destructive' as const },
        };
      default:
        return {
          icon: <FileText className="w-5 h-5" />,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50 border-gray-200',
          badge: { text: 'Unknown', variant: 'secondary' as const },
        };
    }
  };

  const statusConfig = getStatusConfig();

  return (
    <Card className={cn('w-full', statusConfig.bgColor, className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={cn('flex-shrink-0', statusConfig.color)}>
              {statusConfig.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {fileName}
              </p>
              <p className="text-xs text-gray-500">
                {formatFileSize(fileSize)}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={statusConfig.badge.variant}>
              {statusConfig.badge.text}
            </Badge>
            {onCancel && (status === 'uploading' || status === 'processing') && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onCancel}
                className="h-8 w-8 p-0 hover:bg-red-100"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Cancel upload</span>
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Progress Bar */}
        {(status === 'uploading' || status === 'processing') && (
          <div className="space-y-2">
            <Progress
              value={progress}
              className={cn(
                'h-2',
                status === 'processing' && 'animate-pulse'
              )}
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>
                {status === 'uploading' ? 'Uploading...' : 'Processing...'}
              </span>
              <span>{Math.round(progress)}%</span>
            </div>
            {status === 'uploading' && (
              <div className="text-xs text-gray-500">
                {formatFileSize(uploadedSize)} of {formatFileSize(fileSize)}
              </div>
            )}
          </div>
        )}

        {/* Completion Message */}
        {status === 'completed' && (
          <div className="text-sm text-green-700">
            File uploaded and processed successfully!
          </div>
        )}

        {/* Error Message */}
        {status === 'error' && error && (
          <div className="text-sm text-red-700 bg-red-100 rounded p-2 border border-red-200">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Speed and Time Estimation (for uploading) */}
        {status === 'uploading' && progress > 0 && (
          <div className="mt-2 text-xs text-gray-500">
            <div className="flex justify-between">
              <span>Speed: ~{formatFileSize(uploadedSize / (progress / 100))}/s</span>
              {progress > 10 && (
                <span>
                  ETA: {Math.round(((100 - progress) / progress) * (Date.now() / 1000))}s
                </span>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default UploadProgress;