/**
 * Unit tests for useDataPreview hook
 * Tests data preview loading, analysis, and error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import useDataPreview from '@/hooks/use-data-preview';
import { mockDataPreview } from '../setup';

// Mock the API
const mockGetDataPreview = vi.fn();
const mockTriggerDataAnalysis = vi.fn();

vi.mock('@/lib/api/data-sources', () => ({
  default: {
    getDataPreview: mockGetDataPreview,
    triggerDataAnalysis: mockTriggerDataAnalysis,
  },
}));

// Mock toast
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  toast: mockToast,
}));

const mockQualityChecks = [
  {
    id: 1,
    dataset_id: 1,
    check_type: 'missing_values',
    column_name: 'name',
    severity: 'warning' as const,
    message: 'Column has missing values',
    details: { missing_count: 5 },
    affected_rows: 5,
    created_at: new Date().toISOString(),
  },
];

describe('useDataPreview', () => {
  const defaultOptions = {
    datasetId: 1,
    autoLoad: false,
    onPreviewLoad: vi.fn(),
    onError: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useDataPreview(defaultOptions));

    expect(result.current.state).toEqual({
      loading: false,
      error: null,
      preview: null,
      qualityChecks: [],
    });
  });

  it('initializes with autoLoad=true', async () => {
    mockGetDataPreview.mockResolvedValue({
      preview: mockDataPreview,
      qualityChecks: mockQualityChecks,
    });

    renderHook(() => useDataPreview({
      ...defaultOptions,
      autoLoad: true,
    }));

    await waitFor(() => {
      expect(mockGetDataPreview).toHaveBeenCalledWith(1);
    });
  });

  it('does not auto-load when datasetId is null', () => {
    renderHook(() => useDataPreview({
      ...defaultOptions,
      datasetId: null,
      autoLoad: true,
    }));

    expect(mockGetDataPreview).not.toHaveBeenCalled();
  });

  describe('loadPreview', () => {
    it('successfully loads preview data', async () => {
      mockGetDataPreview.mockResolvedValue({
        preview: mockDataPreview,
        qualityChecks: mockQualityChecks,
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      expect(result.current.state.loading).toBe(false);
      expect(result.current.state.error).toBeNull();
      expect(result.current.state.preview).toEqual(mockDataPreview);
      expect(result.current.state.qualityChecks).toEqual(mockQualityChecks);

      expect(defaultOptions.onPreviewLoad).toHaveBeenCalledWith(mockDataPreview);
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Preview Loaded',
        })
      );
    });

    it('handles loading state correctly', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockGetDataPreview.mockReturnValue(promise);

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      // Start loading
      act(() => {
        result.current.loadPreview();
      });

      expect(result.current.state.loading).toBe(true);
      expect(result.current.state.error).toBeNull();

      // Complete loading
      await act(async () => {
        resolvePromise!({
          preview: mockDataPreview,
          qualityChecks: [],
        });
        await promise;
      });

      expect(result.current.state.loading).toBe(false);
    });

    it('handles API error correctly', async () => {
      const errorMessage = 'Failed to load preview';
      mockGetDataPreview.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      expect(result.current.state.loading).toBe(false);
      expect(result.current.state.error).toBe(errorMessage);
      expect(result.current.state.preview).toBeNull();

      expect(defaultOptions.onError).toHaveBeenCalledWith(errorMessage);
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Preview Error',
          variant: 'destructive',
        })
      );
    });

    it('does not load when datasetId is null', async () => {
      const { result } = renderHook(() => useDataPreview({
        ...defaultOptions,
        datasetId: null,
      }));

      await act(async () => {
        await result.current.loadPreview();
      });

      expect(mockGetDataPreview).not.toHaveBeenCalled();
      expect(result.current.state.loading).toBe(false);
    });

    it('handles non-Error objects thrown during load', async () => {
      mockGetDataPreview.mockRejectedValue('String error');

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      expect(result.current.state.error).toBe('Failed to load preview');
    });

    it('ignores stale requests', async () => {
      let resolveFirst: (value: any) => void;
      let resolveSecond: (value: any) => void;

      const firstPromise = new Promise((resolve) => {
        resolveFirst = resolve;
      });

      const secondPromise = new Promise((resolve) => {
        resolveSecond = resolve;
      });

      mockGetDataPreview
        .mockReturnValueOnce(firstPromise)
        .mockReturnValueOnce(secondPromise);

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      // Start first request
      act(() => {
        result.current.loadPreview();
      });

      // Start second request before first completes
      act(() => {
        result.current.loadPreview();
      });

      // Complete second request first
      await act(async () => {
        resolveSecond!({
          preview: mockDataPreview,
          qualityChecks: [],
        });
        await secondPromise;
      });

      expect(result.current.state.preview).toEqual(mockDataPreview);

      // Complete first request (should be ignored)
      await act(async () => {
        resolveFirst!({
          preview: { ...mockDataPreview, dataset_id: 999 },
          qualityChecks: [],
        });
        await firstPromise;
      });

      // Should still have the second request's data
      expect(result.current.state.preview).toEqual(mockDataPreview);
    });
  });

  describe('triggerAnalysis', () => {
    it('successfully triggers analysis', async () => {
      const analysisResult = {
        analysis_id: 'analysis-123',
        status: 'completed',
        results: { insights: ['Data quality is good'] },
      };

      mockTriggerDataAnalysis.mockResolvedValue(analysisResult);

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.triggerAnalysis();
      });

      expect(mockTriggerDataAnalysis).toHaveBeenCalledWith(1);
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Analysis Started',
        })
      );
    });

    it('handles analysis API error', async () => {
      const errorMessage = 'Analysis failed';
      mockTriggerDataAnalysis.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.triggerAnalysis();
      });

      expect(defaultOptions.onError).toHaveBeenCalledWith(errorMessage);
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Analysis Error',
          variant: 'destructive',
        })
      );
    });

    it('does not trigger analysis when datasetId is null', async () => {
      const { result } = renderHook(() => useDataPreview({
        ...defaultOptions,
        datasetId: null,
      }));

      await act(async () => {
        await result.current.triggerAnalysis();
      });

      expect(mockTriggerDataAnalysis).not.toHaveBeenCalled();
    });

    it('handles custom analysis options', async () => {
      const analysisOptions = {
        includeOutlierDetection: true,
        correlationThreshold: 0.7,
      };

      mockTriggerDataAnalysis.mockResolvedValue({
        analysis_id: 'analysis-123',
        status: 'completed',
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.triggerAnalysis(analysisOptions);
      });

      expect(mockTriggerDataAnalysis).toHaveBeenCalledWith(1, analysisOptions);
    });
  });

  describe('resetPreview', () => {
    it('resets state to initial values', async () => {
      mockGetDataPreview.mockResolvedValue({
        preview: mockDataPreview,
        qualityChecks: mockQualityChecks,
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      // Load some data first
      await act(async () => {
        await result.current.loadPreview();
      });

      expect(result.current.state.preview).toEqual(mockDataPreview);
      expect(result.current.state.qualityChecks).toEqual(mockQualityChecks);

      // Reset
      act(() => {
        result.current.resetPreview();
      });

      expect(result.current.state).toEqual({
        loading: false,
        error: null,
        preview: null,
        qualityChecks: [],
      });
    });

    it('cancels pending requests when resetting', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockGetDataPreview.mockReturnValue(promise);

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      // Start loading
      act(() => {
        result.current.loadPreview();
      });

      expect(result.current.state.loading).toBe(true);

      // Reset while loading
      act(() => {
        result.current.resetPreview();
      });

      expect(result.current.state.loading).toBe(false);

      // Complete the original request (should be ignored)
      await act(async () => {
        resolvePromise!({
          preview: mockDataPreview,
          qualityChecks: [],
        });
        await promise;
      });

      // State should remain reset
      expect(result.current.state.preview).toBeNull();
    });
  });

  describe('datasetId changes', () => {
    it('auto-loads when datasetId changes and autoLoad is true', async () => {
      mockGetDataPreview.mockResolvedValue({
        preview: mockDataPreview,
        qualityChecks: [],
      });

      const { result, rerender } = renderHook(
        ({ datasetId }) => useDataPreview({
          ...defaultOptions,
          datasetId,
          autoLoad: true,
        }),
        { initialProps: { datasetId: 1 } }
      );

      await waitFor(() => {
        expect(mockGetDataPreview).toHaveBeenCalledWith(1);
      });

      mockGetDataPreview.mockClear();

      // Change datasetId
      rerender({ datasetId: 2 });

      await waitFor(() => {
        expect(mockGetDataPreview).toHaveBeenCalledWith(2);
      });
    });

    it('resets state when datasetId changes', () => {
      const { result, rerender } = renderHook(
        ({ datasetId }) => useDataPreview({
          ...defaultOptions,
          datasetId,
          autoLoad: false,
        }),
        { initialProps: { datasetId: 1 } }
      );

      // Set some state
      act(() => {
        Object.assign(result.current.state, {
          preview: mockDataPreview,
          qualityChecks: mockQualityChecks,
          error: 'Some error',
        });
      });

      // Change datasetId
      rerender({ datasetId: 2 });

      expect(result.current.state).toEqual({
        loading: false,
        error: null,
        preview: null,
        qualityChecks: [],
      });
    });

    it('does not auto-load when changing to null datasetId', () => {
      mockGetDataPreview.mockClear();

      const { rerender } = renderHook(
        ({ datasetId }) => useDataPreview({
          ...defaultOptions,
          datasetId,
          autoLoad: true,
        }),
        { initialProps: { datasetId: 1 } }
      );

      rerender({ datasetId: null });

      expect(mockGetDataPreview).not.toHaveBeenCalledWith(null);
    });
  });

  describe('error edge cases', () => {
    it('handles API returning malformed data', async () => {
      mockGetDataPreview.mockResolvedValue({
        // Missing required preview field
        qualityChecks: [],
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      expect(result.current.state.error).toBeTruthy();
      expect(defaultOptions.onError).toHaveBeenCalled();
    });

    it('handles empty response gracefully', async () => {
      mockGetDataPreview.mockResolvedValue({
        preview: null,
        qualityChecks: [],
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      expect(result.current.state.preview).toBeNull();
      expect(result.current.state.qualityChecks).toEqual([]);
      expect(result.current.state.error).toBeNull();
    });

    it('handles network timeout', async () => {
      mockGetDataPreview.mockImplementation(() => {
        return new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Network timeout')), 100);
        });
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      expect(result.current.state.error).toBe('Network timeout');
    });
  });

  describe('callback handling', () => {
    it('handles missing optional callbacks gracefully', async () => {
      mockGetDataPreview.mockResolvedValue({
        preview: mockDataPreview,
        qualityChecks: [],
      });

      const minimalOptions = {
        datasetId: 1,
        autoLoad: false,
      };

      const { result } = renderHook(() => useDataPreview(minimalOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      // Should complete without errors
      expect(result.current.state.preview).toEqual(mockDataPreview);
    });

    it('calls onPreviewLoad with correct data', async () => {
      const customPreview = { ...mockDataPreview, dataset_id: 999 };
      mockGetDataPreview.mockResolvedValue({
        preview: customPreview,
        qualityChecks: [],
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      expect(defaultOptions.onPreviewLoad).toHaveBeenCalledWith(customPreview);
    });

    it('calls onError with correct error message', async () => {
      const customError = 'Custom error message';
      mockGetDataPreview.mockRejectedValue(new Error(customError));

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      expect(defaultOptions.onError).toHaveBeenCalledWith(customError);
    });
  });

  describe('memory management', () => {
    it('cleans up properly on unmount', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockGetDataPreview.mockReturnValue(promise);

      const { result, unmount } = renderHook(() => useDataPreview(defaultOptions));

      // Start a request
      act(() => {
        result.current.loadPreview();
      });

      // Unmount before request completes
      unmount();

      // Complete the request
      await act(async () => {
        resolvePromise!({
          preview: mockDataPreview,
          qualityChecks: [],
        });
        await promise;
      });

      // Should not cause any errors or warnings
    });

    it('handles rapid successive calls correctly', async () => {
      mockGetDataPreview.mockResolvedValue({
        preview: mockDataPreview,
        qualityChecks: [],
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      // Make multiple rapid calls
      await act(async () => {
        await Promise.all([
          result.current.loadPreview(),
          result.current.loadPreview(),
          result.current.loadPreview(),
        ]);
      });

      // Should handle gracefully without duplicate state updates
      expect(result.current.state.preview).toEqual(mockDataPreview);
    });
  });

  describe('data validation', () => {
    it('validates preview data structure', async () => {
      const invalidPreview = {
        // Missing required fields
        dataset_id: 1,
      };

      mockGetDataPreview.mockResolvedValue({
        preview: invalidPreview,
        qualityChecks: [],
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      // Should handle invalid data gracefully
      expect(result.current.state.error).toBeTruthy();
    });

    it('validates quality checks structure', async () => {
      const invalidQualityChecks = [
        {
          // Missing required fields
          id: 1,
        },
      ];

      mockGetDataPreview.mockResolvedValue({
        preview: mockDataPreview,
        qualityChecks: invalidQualityChecks,
      });

      const { result } = renderHook(() => useDataPreview(defaultOptions));

      await act(async () => {
        await result.current.loadPreview();
      });

      // Should handle gracefully, possibly filtering out invalid checks
      expect(result.current.state.preview).toEqual(mockDataPreview);
    });
  });
});