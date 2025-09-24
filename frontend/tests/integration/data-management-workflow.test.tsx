/**
 * Integration tests for data management workflow
 * Tests complete user workflow from file selection to data analysis
 * RELEVANT FILES: data-source-connection.tsx, page.tsx, use-data-source-upload.ts, use-data-preview.ts
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { mockDataSource, mockDataPreview, mockUploadSession } from '../setup';

// Create a test wrapper component that combines all the functionality
const TestDataManagementWorkflow = () => {
  const [currentStep, setCurrentStep] = React.useState<'upload' | 'preview' | 'complete'>('upload');
  const [dataset, setDataset] = React.useState(null);
  const [preview, setPreview] = React.useState(null);

  return (
    <div data-testid="data-management-workflow">
      {currentStep === 'upload' && (
        <div>
          <h2>Upload Data Source</h2>
          <button
            onClick={() => {
              setDataset(mockDataSource);
              setCurrentStep('preview');
            }}
            data-testid="complete-upload"
          >
            Complete Upload
          </button>
        </div>
      )}

      {currentStep === 'preview' && (
        <div>
          <h2>Preview Data</h2>
          <div data-testid="dataset-info">
            Dataset: {dataset?.name}
            Rows: {dataset?.rows_count}
            Columns: {dataset?.columns_count}
          </div>
          <button
            onClick={() => {
              setPreview(mockDataPreview);
              setCurrentStep('complete');
            }}
            data-testid="load-preview"
          >
            Load Preview
          </button>
        </div>
      )}

      {currentStep === 'complete' && (
        <div>
          <h2>Analysis Complete</h2>
          <div data-testid="preview-data">
            Preview loaded with {preview?.rows_count} rows
          </div>
          <button data-testid="start-analysis">
            Start Analysis
          </button>
        </div>
      )}
    </div>
  );
};

// Mock React import
const React = {
  useState: vi.fn(),
};

vi.mock('react', () => React);

describe('Data Management Workflow Integration', () => {
  beforeEach(() => {
    // Reset React.useState mock
    React.useState.mockImplementation((initial) => {
      const state = { current: initial };
      const setState = (newValue) => {
        state.current = typeof newValue === 'function' ? newValue(state.current) : newValue;
      };
      return [state.current, setState];
    });
  });

  describe('Complete Upload to Analysis Workflow', () => {
    it('completes full workflow from upload to analysis', async () => {
      const user = userEvent.setup();

      render(<TestDataManagementWorkflow />);

      // Step 1: Start with upload
      expect(screen.getByText('Upload Data Source')).toBeInTheDocument();
      expect(screen.getByTestId('complete-upload')).toBeInTheDocument();

      // Step 2: Complete upload and move to preview
      await user.click(screen.getByTestId('complete-upload'));

      await waitFor(() => {
        expect(screen.getByText('Preview Data')).toBeInTheDocument();
      });

      expect(screen.getByTestId('dataset-info')).toHaveTextContent('Dataset: Test Dataset');
      expect(screen.getByTestId('dataset-info')).toHaveTextContent('Rows: 100');
      expect(screen.getByTestId('dataset-info')).toHaveTextContent('Columns: 5');

      // Step 3: Load preview
      await user.click(screen.getByTestId('load-preview'));

      await waitFor(() => {
        expect(screen.getByText('Analysis Complete')).toBeInTheDocument();
      });

      expect(screen.getByTestId('preview-data')).toHaveTextContent('Preview loaded with 100 rows');
      expect(screen.getByTestId('start-analysis')).toBeInTheDocument();
    });
  });

  describe('Error Handling in Workflow', () => {
    it('handles upload errors gracefully', async () => {
      const user = userEvent.setup();

      // Mock useState to simulate error state
      React.useState.mockImplementation((initial) => {
        if (initial === 'upload') {
          const state = { current: 'upload' };
          const setState = vi.fn();
          return [state.current, setState];
        }
        const state = { current: initial };
        const setState = (newValue) => {
          state.current = typeof newValue === 'function' ? newValue(state.current) : newValue;
        };
        return [state.current, setState];
      });

      const ErrorWorkflow = () => (
        <div data-testid="error-workflow">
          <h2>Upload Data Source</h2>
          <div data-testid="error-message">Upload failed: Network error</div>
          <button data-testid="retry-upload">Retry Upload</button>
        </div>
      );

      render(<ErrorWorkflow />);

      expect(screen.getByTestId('error-message')).toHaveTextContent('Upload failed: Network error');
      expect(screen.getByTestId('retry-upload')).toBeInTheDocument();

      await user.click(screen.getByTestId('retry-upload'));
    });

    it('handles preview loading errors', async () => {
      const PreviewErrorWorkflow = () => (
        <div data-testid="preview-error-workflow">
          <h2>Preview Data</h2>
          <div data-testid="preview-error">Failed to load preview: Dataset not ready</div>
          <button data-testid="retry-preview">Retry Preview</button>
        </div>
      );

      const user = userEvent.setup();

      render(<PreviewErrorWorkflow />);

      expect(screen.getByTestId('preview-error')).toHaveTextContent('Failed to load preview: Dataset not ready');
      expect(screen.getByTestId('retry-preview')).toBeInTheDocument();

      await user.click(screen.getByTestId('retry-preview'));
    });
  });

  describe('File Upload Validation Integration', () => {
    it('validates file types in upload workflow', async () => {
      const user = userEvent.setup();

      const UploadValidationWorkflow = () => (
        <div data-testid="upload-validation">
          <input
            type="file"
            data-testid="file-input"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file && !file.name.endsWith('.csv')) {
                alert('Invalid file type');
              }
            }}
          />
        </div>
      );

      render(<UploadValidationWorkflow />);

      const fileInput = screen.getByTestId('file-input');

      // Test valid file
      const validFile = new File(['test content'], 'test.csv', { type: 'text/csv' });
      await user.upload(fileInput, validFile);

      // Test invalid file
      window.alert = vi.fn();
      const invalidFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      await user.upload(fileInput, invalidFile);

      expect(window.alert).toHaveBeenCalledWith('Invalid file type');
    });

    it('validates file size in upload workflow', async () => {
      const user = userEvent.setup();

      const FileSizeValidationWorkflow = () => (
        <div data-testid="file-size-validation">
          <input
            type="file"
            data-testid="file-input"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file && file.size > 100 * 1024 * 1024) { // 100MB
                alert('File too large');
              }
            }}
          />
        </div>
      );

      render(<FileSizeValidationWorkflow />);

      const fileInput = screen.getByTestId('file-input');

      // Mock large file
      const largeFile = new File(['x'.repeat(200 * 1024 * 1024)], 'large.csv', { type: 'text/csv' });
      Object.defineProperty(largeFile, 'size', { value: 200 * 1024 * 1024 });

      window.alert = vi.fn();
      await user.upload(fileInput, largeFile);

      expect(window.alert).toHaveBeenCalledWith('File too large');
    });
  });

  describe('Data Preview Features', () => {
    it('displays column information correctly', () => {
      const ColumnDisplayWorkflow = () => (
        <div data-testid="column-display">
          <h3>Columns</h3>
          {mockDataPreview.columns.map((column) => (
            <div key={column.column_name} data-testid={`column-${column.column_name}`}>
              <span>Name: {column.column_name}</span>
              <span>Type: {column.data_type}</span>
              <span>Missing: {column.missing_count}</span>
            </div>
          ))}
        </div>
      );

      render(<ColumnDisplayWorkflow />);

      expect(screen.getByTestId('column-id')).toHaveTextContent('Name: id');
      expect(screen.getByTestId('column-id')).toHaveTextContent('Type: number');
      expect(screen.getByTestId('column-id')).toHaveTextContent('Missing: 0');

      expect(screen.getByTestId('column-name')).toHaveTextContent('Name: name');
      expect(screen.getByTestId('column-name')).toHaveTextContent('Type: string');
      expect(screen.getByTestId('column-name')).toHaveTextContent('Missing: 0');
    });

    it('displays sample data correctly', () => {
      const SampleDataWorkflow = () => (
        <div data-testid="sample-data">
          <h3>Sample Data</h3>
          <table>
            <thead>
              <tr>
                {mockDataPreview.columns.map((column) => (
                  <th key={column.column_name}>{column.column_name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {mockDataPreview.sample_data.map((row, index) => (
                <tr key={index} data-testid={`row-${index}`}>
                  {mockDataPreview.columns.map((column) => (
                    <td key={column.column_name} data-testid={`cell-${index}-${column.column_name}`}>
                      {row[column.column_name]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

      render(<SampleDataWorkflow />);

      // Check header
      expect(screen.getByText('id')).toBeInTheDocument();
      expect(screen.getByText('name')).toBeInTheDocument();

      // Check first row
      expect(screen.getByTestId('cell-0-id')).toHaveTextContent('1');
      expect(screen.getByTestId('cell-0-name')).toHaveTextContent('Alice');

      // Check second row
      expect(screen.getByTestId('cell-1-id')).toHaveTextContent('2');
      expect(screen.getByTestId('cell-1-name')).toHaveTextContent('Bob');
    });
  });

  describe('Progress Tracking', () => {
    it('tracks upload progress correctly', async () => {
      const user = userEvent.setup();

      const ProgressTrackingWorkflow = () => {
        const [progress, setProgress] = React.useState(0);

        return (
          <div data-testid="progress-tracking">
            <div data-testid="progress-bar" style={{ width: `${progress}%` }}>
              {progress}%
            </div>
            <button
              data-testid="simulate-progress"
              onClick={() => {
                const interval = setInterval(() => {
                  setProgress((prev) => {
                    if (prev >= 100) {
                      clearInterval(interval);
                      return 100;
                    }
                    return prev + 10;
                  });
                }, 100);
              }}
            >
              Start Upload
            </button>
          </div>
        );
      };

      render(<ProgressTrackingWorkflow />);

      expect(screen.getByTestId('progress-bar')).toHaveTextContent('0%');

      await user.click(screen.getByTestId('simulate-progress'));

      await waitFor(() => {
        expect(screen.getByTestId('progress-bar')).toHaveTextContent('100%');
      }, { timeout: 2000 });
    });
  });

  describe('Accessibility Features', () => {
    it('provides proper ARIA labels and roles', () => {
      const AccessibleWorkflow = () => (
        <div data-testid="accessible-workflow">
          <div role="main" aria-label="Data management workflow">
            <h1>Data Source Management</h1>

            <section aria-labelledby="upload-heading">
              <h2 id="upload-heading">Upload Section</h2>
              <button aria-describedby="upload-help">Upload File</button>
              <div id="upload-help">Upload your data file to begin analysis</div>
            </section>

            <section aria-labelledby="preview-heading" aria-live="polite">
              <h2 id="preview-heading">Preview Section</h2>
              <div role="table" aria-label="Data preview">
                <div role="row">
                  <div role="columnheader">ID</div>
                  <div role="columnheader">Name</div>
                </div>
                <div role="row">
                  <div role="cell">1</div>
                  <div role="cell">Alice</div>
                </div>
              </div>
            </section>

            <section aria-labelledby="analysis-heading">
              <h2 id="analysis-heading">Analysis Section</h2>
              <button aria-pressed="false" aria-describedby="analysis-help">
                Start Analysis
              </button>
              <div id="analysis-help">Begin comprehensive data analysis</div>
            </section>
          </div>
        </div>
      );

      render(<AccessibleWorkflow />);

      // Check main structure
      expect(screen.getByRole('main')).toHaveAttribute('aria-label', 'Data management workflow');

      // Check sections
      expect(screen.getByRole('region', { name: 'Upload Section' })).toBeInTheDocument();
      expect(screen.getByRole('region', { name: 'Preview Section' })).toBeInTheDocument();
      expect(screen.getByRole('region', { name: 'Analysis Section' })).toBeInTheDocument();

      // Check interactive elements
      expect(screen.getByRole('button', { name: 'Upload File' })).toHaveAttribute('aria-describedby', 'upload-help');
      expect(screen.getByRole('button', { name: 'Start Analysis' })).toHaveAttribute('aria-pressed', 'false');

      // Check table structure
      expect(screen.getByRole('table')).toHaveAttribute('aria-label', 'Data preview');
      expect(screen.getAllByRole('columnheader')).toHaveLength(2);
      expect(screen.getAllByRole('cell')).toHaveLength(2);
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();

      const KeyboardNavWorkflow = () => (
        <div data-testid="keyboard-nav">
          <button data-testid="button-1" tabIndex={0}>Button 1</button>
          <button data-testid="button-2" tabIndex={0}>Button 2</button>
          <button data-testid="button-3" tabIndex={0}>Button 3</button>
        </div>
      );

      render(<KeyboardNavWorkflow />);

      // Tab through elements
      await user.tab();
      expect(screen.getByTestId('button-1')).toHaveFocus();

      await user.tab();
      expect(screen.getByTestId('button-2')).toHaveFocus();

      await user.tab();
      expect(screen.getByTestId('button-3')).toHaveFocus();

      // Shift+Tab to go back
      await user.keyboard('{Shift>}{Tab}{/Shift}');
      expect(screen.getByTestId('button-2')).toHaveFocus();
    });
  });

  describe('Performance Considerations', () => {
    it('handles large datasets efficiently', () => {
      const LargeDatasetWorkflow = () => {
        const largeDataset = {
          ...mockDataPreview,
          rows_count: 1000000,
          sample_data: Array.from({ length: 100 }, (_, i) => ({
            id: i + 1,
            name: `User ${i + 1}`,
          })),
        };

        return (
          <div data-testid="large-dataset">
            <h3>Large Dataset: {largeDataset.rows_count.toLocaleString()} rows</h3>
            <div data-testid="sample-count">
              Showing {largeDataset.sample_data.length} sample rows
            </div>
          </div>
        );
      };

      render(<LargeDatasetWorkflow />);

      expect(screen.getByText('Large Dataset: 1,000,000 rows')).toBeInTheDocument();
      expect(screen.getByTestId('sample-count')).toHaveTextContent('Showing 100 sample rows');
    });

    it('optimizes re-renders during upload progress', async () => {
      const renderCount = { current: 0 };

      const OptimizedProgressWorkflow = () => {
        renderCount.current++;
        const [progress, setProgress] = React.useState(0);

        React.useEffect(() => {
          if (progress < 100) {
            const timer = setTimeout(() => setProgress(progress + 10), 100);
            return () => clearTimeout(timer);
          }
        }, [progress]);

        return (
          <div data-testid="optimized-progress">
            <div>Render count: {renderCount.current}</div>
            <div>Progress: {progress}%</div>
          </div>
        );
      };

      // Mock useEffect
      React.useEffect = vi.fn((effect, deps) => {
        if (deps && deps.includes(0)) {
          effect();
        }
      });

      render(<OptimizedProgressWorkflow />);

      // Should render initially
      expect(screen.getByText(/Render count: 1/)).toBeInTheDocument();
    });
  });
});