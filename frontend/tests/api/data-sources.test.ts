/**
 * Integration tests for data sources API client
 * Tests API communication, error handling, and response parsing
 * RELEVANT FILES: data-sources.ts, use-data-source-upload.ts, use-data-preview.ts, setup.ts
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import dataSourceAPI from '@/lib/api/data-sources';
import { mockDataSource, mockDataPreview } from '../setup';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Data Sources API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('uploadFile', () => {
    it('uploads file successfully with progress tracking', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const projectId = 1;
      const mockProgressCallback = vi.fn();

      // Mock successful upload response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          dataset_id: 1,
          session_id: 'session-123',
          message: 'Upload successful',
        }),
      });

      const options = {
        onProgress: mockProgressCallback,
        chunkSize: 1024,
      };

      const result = await dataSourceAPI.uploadFile(file, projectId, options);

      expect(result.success).toBe(true);
      expect(result.dataset_id).toBe(1);
      expect(result.session_id).toBe('session-123');

      // Verify fetch was called with correct parameters
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/data/upload'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      );
    });

    it('handles upload failure with error response', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const projectId = 1;

      // Mock error response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          detail: 'File too large',
        }),
      });

      await expect(dataSourceAPI.uploadFile(file, projectId)).rejects.toThrow('File too large');

      expect(mockFetch).toHaveBeenCalled();
    });

    it('handles network errors', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const projectId = 1;

      // Mock network error
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(dataSourceAPI.uploadFile(file, projectId)).rejects.toThrow('Network error');
    });

    it('includes authentication headers when available', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const projectId = 1;

      // Mock localStorage to return auth token
      const mockToken = 'mock-jwt-token';
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: vi.fn(() => mockToken),
        },
        writable: true,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          dataset_id: 1,
          session_id: 'session-123',
        }),
      });

      await dataSourceAPI.uploadFile(file, projectId);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockToken}`,
          }),
        })
      );
    });

    it('formats form data correctly', async () => {
      const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const projectId = 1;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          dataset_id: 1,
          session_id: 'session-123',
        }),
      });

      await dataSourceAPI.uploadFile(file, projectId);

      const callArgs = mockFetch.mock.calls[0];
      const formData = callArgs[1].body as FormData;

      expect(formData.get('file')).toBe(file);
      expect(formData.get('project_id')).toBe(projectId.toString());
    });
  });

  describe('getDataset', () => {
    it('fetches dataset successfully', async () => {
      const datasetId = 1;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockDataSource,
      });

      const result = await dataSourceAPI.getDataset(datasetId);

      expect(result).toEqual(mockDataSource);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/datasets/${datasetId}`),
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('handles dataset not found', async () => {
      const datasetId = 999;

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({
          detail: 'Dataset not found',
        }),
      });

      await expect(dataSourceAPI.getDataset(datasetId)).rejects.toThrow('Dataset not found');
    });
  });

  describe('getDataPreview', () => {
    it('fetches data preview successfully', async () => {
      const datasetId = 1;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockDataPreview,
      });

      const result = await dataSourceAPI.getDataPreview(datasetId);

      expect(result).toEqual(mockDataPreview);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/datasets/${datasetId}/preview`),
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('handles preview generation error', async () => {
      const datasetId = 1;

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          detail: 'Dataset not ready for preview',
        }),
      });

      await expect(dataSourceAPI.getDataPreview(datasetId)).rejects.toThrow('Dataset not ready for preview');
    });
  });

  describe('listDatasets', () => {
    it('lists datasets with pagination', async () => {
      const mockDatasetList = {
        items: [mockDataSource],
        total: 10,
        page: 1,
        size: 20,
        pages: 1,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockDatasetList,
      });

      const params = {
        project_id: 1,
        status: 'ready',
        page: 1,
        size: 20,
      };

      const result = await dataSourceAPI.listDatasets(params);

      expect(result).toEqual(mockDatasetList);

      // Check URL parameters
      const callUrl = mockFetch.mock.calls[0][0];
      expect(callUrl).toContain('project_id=1');
      expect(callUrl).toContain('status=ready');
      expect(callUrl).toContain('page=1');
      expect(callUrl).toContain('size=20');
    });

    it('handles empty results', async () => {
      const emptyList = {
        items: [],
        total: 0,
        page: 1,
        size: 20,
        pages: 0,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => emptyList,
      });

      const result = await dataSourceAPI.listDatasets({});

      expect(result.items).toEqual([]);
      expect(result.total).toBe(0);
    });
  });

  describe('getQualityChecks', () => {
    it('fetches quality checks successfully', async () => {
      const datasetId = 1;
      const mockQualityChecks = [
        {
          id: 1,
          dataset_id: 1,
          check_type: 'missing_values',
          column_name: 'age',
          severity: 'warning',
          message: 'Column has missing values',
          details: { missing_count: 10 },
          affected_rows: 10,
          created_at: new Date().toISOString(),
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockQualityChecks,
      });

      const result = await dataSourceAPI.getQualityChecks(datasetId);

      expect(result).toEqual(mockQualityChecks);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/datasets/${datasetId}/quality`),
        expect.objectContaining({
          method: 'GET',
        })
      );
    });
  });

  describe('triggerAnalysis', () => {
    it('triggers analysis successfully', async () => {
      const datasetId = 1;
      const mockResponse = {
        message: 'Analysis started',
        dataset_id: 1,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await dataSourceAPI.triggerAnalysis(datasetId);

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/datasets/${datasetId}/analyze`),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('handles analysis trigger failure', async () => {
      const datasetId = 1;

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          detail: 'Dataset is already being analyzed',
        }),
      });

      await expect(dataSourceAPI.triggerAnalysis(datasetId)).rejects.toThrow('Dataset is already being analyzed');
    });
  });

  describe('cancelUpload', () => {
    it('cancels upload session successfully', async () => {
      const sessionId = 'session-123';

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: 'Upload cancelled',
        }),
      });

      const result = await dataSourceAPI.cancelUpload(sessionId);

      expect(result.message).toBe('Upload cancelled');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/session/${sessionId}`),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('handles cancel failure', async () => {
      const sessionId = 'session-123';

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({
          detail: 'Upload session not found',
        }),
      });

      await expect(dataSourceAPI.cancelUpload(sessionId)).rejects.toThrow('Upload session not found');
    });
  });

  describe('error handling', () => {
    it('handles JSON parsing errors', async () => {
      const datasetId = 1;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      await expect(dataSourceAPI.getDataset(datasetId)).rejects.toThrow('Invalid JSON');
    });

    it('handles non-JSON error responses', async () => {
      const datasetId = 1;

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => {
          throw new Error('Not JSON');
        },
      });

      await expect(dataSourceAPI.getDataset(datasetId)).rejects.toThrow('HTTP error! status: 500');
    });

    it('handles missing error details', async () => {
      const datasetId = 1;

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({}), // Empty response
      });

      await expect(dataSourceAPI.getDataset(datasetId)).rejects.toThrow('HTTP error! status: 400');
    });
  });

  describe('request timeout', () => {
    it('handles request timeout', async () => {
      const datasetId = 1;

      // Mock AbortController
      const mockAbortController = {
        abort: vi.fn(),
        signal: { aborted: false },
      };
      global.AbortController = vi.fn(() => mockAbortController) as any;

      mockFetch.mockImplementation(() => {
        return new Promise((_, reject) => {
          setTimeout(() => {
            reject(new Error('Request timeout'));
          }, 100);
        });
      });

      await expect(dataSourceAPI.getDataset(datasetId)).rejects.toThrow('Request timeout');
    });
  });

  describe('concurrent requests', () => {
    it('handles multiple concurrent uploads', async () => {
      const files = [
        new File(['content1'], 'file1.csv', { type: 'text/csv' }),
        new File(['content2'], 'file2.csv', { type: 'text/csv' }),
        new File(['content3'], 'file3.csv', { type: 'text/csv' }),
      ];

      // Mock successful responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, dataset_id: 1, session_id: 'session-1' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, dataset_id: 2, session_id: 'session-2' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, dataset_id: 3, session_id: 'session-3' }),
        });

      const uploadPromises = files.map((file, index) =>
        dataSourceAPI.uploadFile(file, index + 1)
      );

      const results = await Promise.all(uploadPromises);

      expect(results).toHaveLength(3);
      results.forEach((result, index) => {
        expect(result.success).toBe(true);
        expect(result.dataset_id).toBe(index + 1);
      });

      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it('handles mixed success and failure in concurrent requests', async () => {
      const files = [
        new File(['content1'], 'file1.csv', { type: 'text/csv' }),
        new File(['content2'], 'file2.csv', { type: 'text/csv' }),
      ];

      // Mock mixed responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, dataset_id: 1, session_id: 'session-1' }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'File too large' }),
        });

      const uploadPromises = files.map((file, index) =>
        dataSourceAPI.uploadFile(file, index + 1).catch(error => ({ error: error.message }))
      );

      const results = await Promise.all(uploadPromises);

      expect(results[0]).toEqual({ success: true, dataset_id: 1, session_id: 'session-1' });
      expect(results[1]).toEqual({ error: 'File too large' });
    });
  });

  describe('API base URL configuration', () => {
    it('uses correct base URL for different environments', async () => {
      const originalEnv = process.env.NODE_ENV;

      // Test development environment
      process.env.NODE_ENV = 'development';

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockDataSource,
      });

      await dataSourceAPI.getDataset(1);

      const devUrl = mockFetch.mock.calls[0][0];
      expect(devUrl).toContain('/api/v1/data');

      // Restore environment
      process.env.NODE_ENV = originalEnv;
    });
  });

  describe('response transformation', () => {
    it('transforms dataset response correctly', async () => {
      const rawDataset = {
        ...mockDataSource,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T01:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => rawDataset,
      });

      const result = await dataSourceAPI.getDataset(1);

      expect(result.created_at).toBe('2023-01-01T00:00:00Z');
      expect(result.updated_at).toBe('2023-01-01T01:00:00Z');
    });

    it('handles nested object responses', async () => {
      const complexPreview = {
        ...mockDataPreview,
        columns: [
          {
            column_name: 'id',
            data_type: 'number',
            sample_values: ['1', '2', '3'],
            statistics: {
              min: 1,
              max: 100,
              avg: 50.5,
            },
          },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => complexPreview,
      });

      const result = await dataSourceAPI.getDataPreview(1);

      expect(result.columns[0].statistics).toEqual({
        min: 1,
        max: 100,
        avg: 50.5,
      });
    });
  });
});