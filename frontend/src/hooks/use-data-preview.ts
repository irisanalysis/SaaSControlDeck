/**
 * React Hook for Managing Data Preview
 * Handles data preview loading, quality checks, and analysis triggering
 */

import { useState, useEffect, useCallback } from 'react';
import { toast } from '@/hooks/use-toast';
import dataSourceAPI from '@/lib/api/data-sources';
import {
  DataSource,
  DataSourcePreview,
  DataQualityCheck,
  UseDataPreviewState,
} from '@/lib/api/types/data-sources';

export interface UseDataPreviewOptions {
  datasetId: number | null;
  autoLoad?: boolean;
  onPreviewLoad?: (preview: DataSourcePreview) => void;
  onError?: (error: string) => void;
}

export interface UseDataPreviewReturn {
  state: UseDataPreviewState;
  loadPreview: () => Promise<void>;
  triggerAnalysis: () => Promise<void>;
  refreshQualityChecks: () => Promise<void>;
  resetPreview: () => void;
}

export function useDataPreview(
  options: UseDataPreviewOptions
): UseDataPreviewReturn {
  const [state, setState] = useState<UseDataPreviewState>({
    preview: null,
    qualityChecks: [],
    loading: false,
    error: null,
  });

  // 稳定化options的值，避免每次渲染都变化
  const { datasetId, autoLoad, onPreviewLoad, onError } = options;

  const resetPreview = useCallback(() => {
    setState({
      preview: null,
      qualityChecks: [],
      loading: false,
      error: null,
    });
  }, []);

  const loadPreview = useCallback(async () => {
    if (!datasetId) {
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [preview, qualityChecks] = await Promise.all([
        dataSourceAPI.getDataPreview(datasetId),
        dataSourceAPI.getQualityChecks(datasetId).catch(() => []),
      ]);

      setState(prev => ({
        ...prev,
        preview,
        qualityChecks,
        loading: false,
      }));

      onPreviewLoad?.(preview);

      toast({
        title: 'Preview Loaded',
        description: `Loaded ${preview.rows_count} rows and ${preview.columns_count} columns`,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load preview';

      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));

      onError?.(errorMessage);

      toast({
        title: 'Preview Failed',
        description: errorMessage,
        variant: 'destructive',
      });
    }
  }, [datasetId, onPreviewLoad, onError]);

  const refreshQualityChecks = useCallback(async () => {
    if (!datasetId) {
      return;
    }

    try {
      const qualityChecks = await dataSourceAPI.getQualityChecks(datasetId);

      setState(prev => ({
        ...prev,
        qualityChecks,
      }));

      if (qualityChecks.length > 0) {
        const issueCount = qualityChecks.filter(check =>
          check.severity === 'error' || check.severity === 'warning'
        ).length;

        toast({
          title: 'Quality Checks Updated',
          description: `Found ${issueCount} data quality issues`,
          variant: issueCount > 0 ? 'destructive' : 'default',
        });
      }
    } catch (error) {
      console.error('Failed to refresh quality checks:', error);
      toast({
        title: 'Quality Check Failed',
        description: 'Failed to load quality checks',
        variant: 'destructive',
      });
    }
  }, [datasetId]);

  const triggerAnalysis = useCallback(async () => {
    if (!datasetId) {
      return;
    }

    setState(prev => ({ ...prev, loading: true }));

    try {
      await dataSourceAPI.triggerAnalysis(datasetId);

      toast({
        title: 'Analysis Started',
        description: 'Data analysis has been triggered. Results will be available shortly.',
      });

      // Refresh preview and quality checks after analysis
      setTimeout(() => {
        loadPreview();
        refreshQualityChecks();
      }, 2000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to trigger analysis';

      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));

      toast({
        title: 'Analysis Failed',
        description: errorMessage,
        variant: 'destructive',
      });
    }
  }, [datasetId, loadPreview, refreshQualityChecks]);

  // Auto-load preview when datasetId changes - 修复无限循环问题
  useEffect(() => {
    if (autoLoad && datasetId) {
      loadPreview();
    } else if (!datasetId) {
      resetPreview();
    }
  }, [datasetId, autoLoad, loadPreview, resetPreview]); // 添加完整的依赖数组

  return {
    state,
    loadPreview,
    triggerAnalysis,
    refreshQualityChecks,
    resetPreview,
  };
}

export default useDataPreview;