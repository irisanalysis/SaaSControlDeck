/**
 * Unit tests for useDataSourceUpload hook
 * Tests file upload logic, progress tracking, and error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import useDataSourceUpload from '@/hooks/use-data-source-upload';
import { mockDataSource } from '../setup';

// Mock the API
const mockUploadFile = vi.fn();
const mockCancelUpload = vi.fn();
const mockGetDataset = vi.fn();

vi.mock('@/lib/api/data-sources', () => ({
  default: {
    uploadFile: mockUploadFile,
    cancelUpload: mockCancelUpload,
    getDataset: mockGetDataset,
  },
}));

// Mock toast
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  toast: mockToast,
}));

describe('useDataSourceUpload', () => {
  const defaultOptions = {
    projectId: 1,
    onUploadComplete: vi.fn(),
    onUploadError: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

    expect(result.current.uploadState).toEqual({
      file: null,
      isUploading: false,
      progress: 0,
      error: null,
      sessionId: null,
      dataset: null,
    });
  });

  describe('validateFile', () => {
    it('validates file size correctly', () => {
      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      // Valid file size
      const validFile = new File(['test'], 'test.csv', { type: 'text/csv' });
      Object.defineProperty(validFile, 'size', { value: 1024 });

      const validResult = result.current.validateFile(validFile);
      expect(validResult.isValid).toBe(true);

      // Invalid file size (too large)
      const largeFile = new File(['test'], 'large.csv', { type: 'text/csv' });
      Object.defineProperty(largeFile, 'size', { value: 200 * 1024 * 1024 }); // 200MB

      const invalidResult = result.current.validateFile(largeFile);
      expect(invalidResult.isValid).toBe(false);
      expect(invalidResult.error).toContain('exceeds maximum allowed size');
    });

    it('validates file type correctly', () => {
      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      // Valid file types
      const validTypes = [
        { name: 'test.csv', type: 'text/csv' },
        { name: 'test.json', type: 'application/json' },
        { name: 'test.xlsx', type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' },
        { name: 'test.parquet', type: 'application/octet-stream' },
      ];

      validTypes.forEach(({ name, type }) => {
        const file = new File(['test'], name, { type });
        const result_validation = result.current.validateFile(file);
        expect(result_validation.isValid).toBe(true);
      });

      // Invalid file type
      const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });
      const invalidResult = result.current.validateFile(invalidFile);
      expect(invalidResult.isValid).toBe(false);
      expect(invalidResult.error).toContain('Unsupported file type');
    });

    it('validates empty files', () => {
      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      const emptyFile = new File([], 'empty.csv', { type: 'text/csv' });
      const validationResult = result.current.validateFile(emptyFile);

      expect(validationResult.isValid).toBe(false);
      expect(validationResult.error).toContain('empty');
    });

    it('handles validation errors gracefully', () => {
      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      // Mock file with problematic properties
      const problematicFile = {
        name: 'test.csv',
        type: 'text/csv',
        size: 1024,
      } as File;

      // Mock an error during validation
      const originalSplit = String.prototype.split;
      String.prototype.split = vi.fn().mockImplementation(() => {
        throw new Error('Split error');
      });

      const validationResult = result.current.validateFile(problematicFile);

      expect(validationResult.isValid).toBe(false);
      expect(validationResult.error).toContain('Failed to validate file');

      // Restore original method
      String.prototype.split = originalSplit;
    });
  });

  describe('uploadFile', () => {
    it('successfully uploads a valid file', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      mockUploadFile.mockResolvedValue({
        success: true,
        dataset_id: 1,
        session_id: 'session-123',
        message: 'Upload successful',
      });

      mockGetDataset.mockResolvedValue(mockDataSource);

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.uploadState.isUploading).toBe(false);
      expect(result.current.uploadState.progress).toBe(100);
      expect(result.current.uploadState.dataset).toEqual(mockDataSource);
      expect(result.current.uploadState.sessionId).toBe('session-123');
      expect(result.current.uploadState.error).toBeNull();

      expect(defaultOptions.onUploadComplete).toHaveBeenCalledWith(mockDataSource);
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Upload Complete',
        })
      );
    });

    it('handles file validation failure', async () => {
      const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      await act(async () => {
        await result.current.uploadFile(invalidFile);
      });

      expect(result.current.uploadState.isUploading).toBe(false);
      expect(result.current.uploadState.error).toContain('Unsupported file type');
      expect(mockUploadFile).not.toHaveBeenCalled();
      expect(defaultOptions.onUploadError).toHaveBeenCalled();
    });

    it('handles upload API failure', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      mockUploadFile.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.uploadState.isUploading).toBe(false);
      expect(result.current.uploadState.error).toBe('Network error');
      expect(defaultOptions.onUploadError).toHaveBeenCalledWith('Network error');
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Upload Failed',
        })
      );
    });

    it('handles upload progress updates', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      mockUploadFile.mockImplementation((file, projectId, options) => {
        // Simulate progress updates
        setTimeout(() => options.onProgress({ percentage: 25 }), 10);
        setTimeout(() => options.onProgress({ percentage: 50 }), 20);
        setTimeout(() => options.onProgress({ percentage: 75 }), 30);

        return Promise.resolve({
          success: true,
          dataset_id: 1,
          session_id: 'session-123',
        });
      });

      mockGetDataset.mockResolvedValue(mockDataSource);

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      await act(async () => {
        await result.current.uploadFile(file);
      });

      // Progress should have been updated during upload
      expect(result.current.uploadState.progress).toBe(100);
    });

    it('handles timeout correctly', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      // Mock a slow upload
      mockUploadFile.mockImplementation(() => {
        return new Promise((resolve) => {
          setTimeout(() => resolve({
            success: true,
            dataset_id: 1,
            session_id: 'session-123',
          }), 200); // 200ms delay
        });
      });

      const { result } = renderHook(() => useDataSourceUpload({
        ...defaultOptions,
        timeout: 100, // 100ms timeout
      }));

      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.uploadState.error).toContain('Upload timed out');
      expect(defaultOptions.onUploadError).toHaveBeenCalled();
    });

    it('handles API response without dataset_id', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      mockUploadFile.mockResolvedValue({
        success: false,
        message: 'Upload failed',
      });

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.uploadState.error).toBe('Upload failed');
      expect(defaultOptions.onUploadError).toHaveBeenCalled();
    });

    it('sets upload state correctly during upload', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      mockUploadFile.mockImplementation(() => {
        return new Promise((resolve) => {
          setTimeout(() => resolve({
            success: true,
            dataset_id: 1,
            session_id: 'session-123',
          }), 50);
        });
      });

      mockGetDataset.mockResolvedValue(mockDataSource);

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      // Start upload
      act(() => {
        result.current.uploadFile(file);
      });

      // Check initial upload state
      expect(result.current.uploadState.isUploading).toBe(true);
      expect(result.current.uploadState.file).toBe(file);
      expect(result.current.uploadState.progress).toBe(0);
      expect(result.current.uploadState.error).toBeNull();

      // Wait for completion
      await waitFor(() => {
        expect(result.current.uploadState.isUploading).toBe(false);
      });
    });
  });

  describe('cancelUpload', () => {
    it('cancels active upload successfully', async () => {
      mockCancelUpload.mockResolvedValue(undefined);

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      // Set up an active upload state
      act(() => {
        result.current.uploadFile(new File(['test'], 'test.csv', { type: 'text/csv' }));
      });

      await act(async () => {
        await result.current.cancelUpload();
      });

      expect(mockCancelUpload).toHaveBeenCalled();
      expect(result.current.uploadState.isUploading).toBe(false);
      expect(result.current.uploadState.file).toBeNull();
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Upload Cancelled',
        })
      );
    });

    it('handles cancel upload failure', async () => {
      mockCancelUpload.mockRejectedValue(new Error('Cancel failed'));

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      // Set up upload state with session
      act(() => {
        result.current.uploadState.sessionId = 'session-123';
        result.current.uploadState.isUploading = true;
      });

      await act(async () => {
        await result.current.cancelUpload();
      });

      expect(result.current.uploadState.isUploading).toBe(false);
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Cancel Failed',
        })
      );
    });

    it('does not call API when no active upload', async () => {
      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      await act(async () => {
        await result.current.cancelUpload();
      });

      expect(mockCancelUpload).not.toHaveBeenCalled();
    });
  });

  describe('resetUpload', () => {
    it('resets upload state completely', () => {
      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      // Set some state
      act(() => {
        Object.assign(result.current.uploadState, {
          file: new File(['test'], 'test.csv'),
          isUploading: true,
          progress: 50,
          error: 'Some error',
          sessionId: 'session-123',
          dataset: mockDataSource,
        });
      });

      act(() => {
        result.current.resetUpload();
      });

      expect(result.current.uploadState).toEqual({
        file: null,
        isUploading: false,
        progress: 0,
        error: null,
        sessionId: null,
        dataset: null,
      });
    });

    it('cleans up pending operations', () => {
      const { result } = renderHook(() => useDataSourceUpload({
        ...defaultOptions,
        timeout: 1000,
      }));

      // Start an upload to create timeout
      act(() => {
        result.current.uploadFile(new File(['test'], 'test.csv', { type: 'text/csv' }));
      });

      // Reset should clean up timeout
      act(() => {
        result.current.resetUpload();
      });

      expect(result.current.uploadState.isUploading).toBe(false);
    });
  });

  describe('custom options', () => {
    it('uses custom chunk size', async () => {
      const customChunkSize = 2048;
      const options = {
        ...defaultOptions,
        chunkSize: customChunkSize,
      };

      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      mockUploadFile.mockResolvedValue({
        success: true,
        dataset_id: 1,
        session_id: 'session-123',
      });

      mockGetDataset.mockResolvedValue(mockDataSource);

      const { result } = renderHook(() => useDataSourceUpload(options));

      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(mockUploadFile).toHaveBeenCalledWith(
        file,
        options.projectId,
        expect.objectContaining({
          chunkSize: customChunkSize,
        })
      );
    });

    it('handles missing optional callbacks', async () => {
      const minimalOptions = {
        projectId: 1,
      };

      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      mockUploadFile.mockResolvedValue({
        success: true,
        dataset_id: 1,
        session_id: 'session-123',
      });

      mockGetDataset.mockResolvedValue(mockDataSource);

      const { result } = renderHook(() => useDataSourceUpload(minimalOptions));

      await act(async () => {
        await result.current.uploadFile(file);
      });

      // Should complete without errors even without callbacks
      expect(result.current.uploadState.dataset).toEqual(mockDataSource);
    });
  });

  describe('error edge cases', () => {
    it('handles non-Error objects thrown during upload', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      mockUploadFile.mockRejectedValue('String error');

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.uploadState.error).toBe('Upload failed');
    });

    it('handles dataset fetch failure after successful upload', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

      mockUploadFile.mockResolvedValue({
        success: true,
        dataset_id: 1,
        session_id: 'session-123',
      });

      mockGetDataset.mockRejectedValue(new Error('Dataset fetch failed'));

      const { result } = renderHook(() => useDataSourceUpload(defaultOptions));

      await act(async () => {
        await result.current.uploadFile(file);
      });

      expect(result.current.uploadState.error).toBe('Dataset fetch failed');
    });
  });

  describe('memory management', () => {
    it('cleans up properly on unmount', () => {
      const { result, unmount } = renderHook(() => useDataSourceUpload({
        ...defaultOptions,
        timeout: 1000,
      }));

      // Start an upload to create pending operations
      act(() => {
        result.current.uploadFile(new File(['test'], 'test.csv', { type: 'text/csv' }));
      });

      // Unmount should not cause any errors
      expect(() => unmount()).not.toThrow();
    });
  });
});