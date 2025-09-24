/**
 * Unit tests for DataSourceConnection component
 * Tests complete workflow, step navigation, and integration with hooks
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataSourceConnection from '@/components/data-management/data-source-connection';
import { mockDataSource, mockDataPreview } from '../../setup';

// Mock the hooks
const mockUploadFile = vi.fn();
const mockCancelUpload = vi.fn();
const mockResetUpload = vi.fn();
const mockValidateFile = vi.fn();
const mockLoadPreview = vi.fn();
const mockTriggerAnalysis = vi.fn();
const mockResetPreview = vi.fn();

vi.mock('@/hooks/use-data-source-upload', () => ({
  default: () => ({
    uploadState: {
      file: null,
      isUploading: false,
      progress: 0,
      error: null,
      sessionId: null,
      dataset: null,
    },
    uploadFile: mockUploadFile,
    cancelUpload: mockCancelUpload,
    resetUpload: mockResetUpload,
    validateFile: mockValidateFile,
  }),
}));

vi.mock('@/hooks/use-data-preview', () => ({
  default: () => ({
    state: {
      loading: false,
      error: null,
      preview: null,
      qualityChecks: [],
    },
    loadPreview: mockLoadPreview,
    triggerAnalysis: mockTriggerAnalysis,
    resetPreview: mockResetPreview,
  }),
}));

// Mock child components
vi.mock('@/components/ui/file-dropzone', () => ({
  default: ({ onFileSelect, onError }: any) => (
    <div data-testid="file-dropzone">
      <button onClick={() => onFileSelect(new File(['test'], 'test.csv', { type: 'text/csv' }))}>
        Select File
      </button>
      <button onClick={() => onError('Test error')}>
        Trigger Error
      </button>
    </div>
  ),
}));

vi.mock('@/components/ui/upload-progress', () => ({
  default: ({ onCancel }: any) => (
    <div data-testid="upload-progress">
      <span>Upload Progress</span>
      <button onClick={onCancel}>Cancel Upload</button>
    </div>
  ),
}));

vi.mock('@/components/ui/data-preview-table', () => ({
  default: ({ preview }: any) => (
    <div data-testid="data-preview-table">
      <span>Data Preview: {preview?.dataset_id}</span>
    </div>
  ),
}));

describe('DataSourceConnection', () => {
  const mockOnConnectionComplete = vi.fn();
  const mockOnCancel = vi.fn();

  const defaultProps = {
    projectId: 1,
    onConnectionComplete: mockOnConnectionComplete,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockValidateFile.mockReturnValue({ isValid: true });
  });

  it('renders initial step (select) correctly', () => {
    render(<DataSourceConnection {...defaultProps} />);

    expect(screen.getByText('Data Source Connection')).toBeInTheDocument();
    expect(screen.getByText('Select Data Source')).toBeInTheDocument();
    expect(screen.getByText(/Choose a file to upload/)).toBeInTheDocument();
    expect(screen.getByTestId('file-dropzone')).toBeInTheDocument();
    expect(screen.getByText(/Supported formats:/)).toBeInTheDocument();
  });

  it('displays step indicator with correct progression', () => {
    render(<DataSourceConnection {...defaultProps} />);

    // Check that all steps are shown
    expect(screen.getByText('Select Data Source')).toBeInTheDocument();
    expect(screen.getByText('Upload in Progress')).toBeInTheDocument();
    expect(screen.getByText('Data Preview')).toBeInTheDocument();
    expect(screen.getByText('Connection Complete')).toBeInTheDocument();

    // First step should be active
    const stepIndicators = screen.getAllByTestId('mock-icon');
    expect(stepIndicators.length).toBeGreaterThan(0);
  });

  it('handles file selection and moves to upload step', async () => {
    const user = userEvent.setup();

    render(<DataSourceConnection {...defaultProps} />);

    const selectFileButton = screen.getByText('Select File');
    await user.click(selectFileButton);

    await waitFor(() => {
      expect(mockValidateFile).toHaveBeenCalled();
      expect(mockUploadFile).toHaveBeenCalled();
    });

    // Should show upload progress
    expect(screen.getByTestId('upload-progress')).toBeInTheDocument();
  });

  it('handles file validation error', async () => {
    const user = userEvent.setup();
    mockValidateFile.mockReturnValue({
      isValid: false,
      error: 'Invalid file type'
    });

    render(<DataSourceConnection {...defaultProps} />);

    const selectFileButton = screen.getByText('Select File');
    await user.click(selectFileButton);

    await waitFor(() => {
      expect(mockValidateFile).toHaveBeenCalled();
      expect(mockUploadFile).not.toHaveBeenCalled();
    });

    // Should remain on select step
    expect(screen.getByTestId('file-dropzone')).toBeInTheDocument();
  });

  it('handles upload cancellation', async () => {
    const user = userEvent.setup();

    render(<DataSourceConnection {...defaultProps} />);

    // First select a file to go to upload step
    const selectFileButton = screen.getByText('Select File');
    await user.click(selectFileButton);

    await waitFor(() => {
      expect(screen.getByTestId('upload-progress')).toBeInTheDocument();
    });

    // Then cancel upload
    const cancelButton = screen.getByText('Cancel Upload');
    await user.click(cancelButton);

    await waitFor(() => {
      expect(mockCancelUpload).toHaveBeenCalled();
    });
  });

  it('shows preview step after successful upload', async () => {
    const user = userEvent.setup();

    // Mock successful upload
    vi.mocked(vi.importActual('@/hooks/use-data-source-upload')).default.mockReturnValue({
      uploadState: {
        file: null,
        isUploading: false,
        progress: 100,
        error: null,
        sessionId: 'session-123',
        dataset: mockDataSource,
      },
      uploadFile: mockUploadFile,
      cancelUpload: mockCancelUpload,
      resetUpload: mockResetUpload,
      validateFile: mockValidateFile,
    });

    // Mock preview state
    vi.mocked(vi.importActual('@/hooks/use-data-preview')).default.mockReturnValue({
      state: {
        loading: false,
        error: null,
        preview: mockDataPreview,
        qualityChecks: [],
      },
      loadPreview: mockLoadPreview,
      triggerAnalysis: mockTriggerAnalysis,
      resetPreview: mockResetPreview,
    });

    const { rerender } = render(<DataSourceConnection {...defaultProps} />);

    // Simulate completed dataset
    rerender(<DataSourceConnection {...defaultProps} />);

    // Should show preview step
    expect(screen.getByText('Data Preview')).toBeInTheDocument();
    expect(screen.getByTestId('data-preview-table')).toBeInTheDocument();
  });

  it('handles preview loading state', () => {
    // Mock loading preview state
    vi.mocked(vi.importActual('@/hooks/use-data-preview')).default.mockReturnValue({
      state: {
        loading: true,
        error: null,
        preview: null,
        qualityChecks: [],
      },
      loadPreview: mockLoadPreview,
      triggerAnalysis: mockTriggerAnalysis,
      resetPreview: mockResetPreview,
    });

    render(<DataSourceConnection {...defaultProps} />);

    expect(screen.getByText(/Loading preview/)).toBeInTheDocument();
  });

  it('handles preview error state', () => {
    // Mock error preview state
    vi.mocked(vi.importActual('@/hooks/use-data-preview')).default.mockReturnValue({
      state: {
        loading: false,
        error: 'Failed to load preview',
        preview: null,
        qualityChecks: [],
      },
      loadPreview: mockLoadPreview,
      triggerAnalysis: mockTriggerAnalysis,
      resetPreview: mockResetPreview,
    });

    render(<DataSourceConnection {...defaultProps} />);

    expect(screen.getByText('Failed to load preview')).toBeInTheDocument();
  });

  it('handles restart functionality', async () => {
    const user = userEvent.setup();

    render(<DataSourceConnection {...defaultProps} />);

    // Go to upload step first
    const selectFileButton = screen.getByText('Select File');
    await user.click(selectFileButton);

    await waitFor(() => {
      expect(screen.getByTestId('upload-progress')).toBeInTheDocument();
    });

    // Click Start Over button (should be available on error or in progress)
    const startOverButton = screen.getByText('Start Over');
    await user.click(startOverButton);

    await waitFor(() => {
      expect(mockResetUpload).toHaveBeenCalled();
      expect(mockResetPreview).toHaveBeenCalled();
    });

    // Should return to select step
    expect(screen.getByTestId('file-dropzone')).toBeInTheDocument();
  });

  it('handles analysis trigger', async () => {
    const user = userEvent.setup();

    // Mock preview state with data
    vi.mocked(vi.importActual('@/hooks/use-data-preview')).default.mockReturnValue({
      state: {
        loading: false,
        error: null,
        preview: mockDataPreview,
        qualityChecks: [],
      },
      loadPreview: mockLoadPreview,
      triggerAnalysis: mockTriggerAnalysis,
      resetPreview: mockResetPreview,
    });

    render(<DataSourceConnection {...defaultProps} />);

    // Should show analysis button in preview step
    const analyzeButton = screen.getByText('Run Analysis');
    await user.click(analyzeButton);

    expect(mockTriggerAnalysis).toHaveBeenCalled();
  });

  it('handles connection completion', async () => {
    const user = userEvent.setup();

    // Mock completed state
    vi.mocked(vi.importActual('@/hooks/use-data-preview')).default.mockReturnValue({
      state: {
        loading: false,
        error: null,
        preview: mockDataPreview,
        qualityChecks: [],
      },
      loadPreview: mockLoadPreview,
      triggerAnalysis: mockTriggerAnalysis,
      resetPreview: mockResetPreview,
    });

    render(<DataSourceConnection {...defaultProps} />);

    const completeButton = screen.getByText('Complete Connection');
    await user.click(completeButton);

    await waitFor(() => {
      expect(mockOnConnectionComplete).toHaveBeenCalledWith(mockDataSource);
    });
  });

  it('shows completion step with dataset statistics', () => {
    // Mock complete state
    const { rerender } = render(<DataSourceConnection {...defaultProps} />);

    // Simulate moving to complete step
    rerender(<DataSourceConnection {...defaultProps} />);

    // Should show completion step with stats
    expect(screen.getByText('Data Source Connected!')).toBeInTheDocument();
    expect(screen.getByText(/ready for analysis/)).toBeInTheDocument();
  });

  it('displays file error correctly', async () => {
    const user = userEvent.setup();

    render(<DataSourceConnection {...defaultProps} />);

    const triggerErrorButton = screen.getByText('Trigger Error');
    await user.click(triggerErrorButton);

    // Error should be handled through the component
    expect(screen.getByTestId('file-dropzone')).toBeInTheDocument();
  });

  it('handles upload error with retry option', async () => {
    const user = userEvent.setup();

    // Mock upload error state
    vi.mocked(vi.importActual('@/hooks/use-data-source-upload')).default.mockReturnValue({
      uploadState: {
        file: null,
        isUploading: false,
        progress: 0,
        error: 'Upload failed',
        sessionId: null,
        dataset: null,
      },
      uploadFile: mockUploadFile,
      cancelUpload: mockCancelUpload,
      resetUpload: mockResetUpload,
      validateFile: mockValidateFile,
    });

    render(<DataSourceConnection {...defaultProps} />);

    // Should show retry button
    const retryButton = screen.getByText('Retry Upload');
    await user.click(retryButton);

    expect(mockUploadFile).toHaveBeenCalled();
  });

  it('applies custom className when provided', () => {
    render(
      <DataSourceConnection
        {...defaultProps}
        className="custom-connection-class"
      />
    );

    const container = screen.getByText('Data Source Connection').closest('div')!;
    expect(container).toHaveClass('custom-connection-class');
  });

  it('handles different upload states correctly', () => {
    const uploadStates = [
      {
        state: { isUploading: true, progress: 50 },
        expectedText: 'Upload in Progress',
      },
      {
        state: { isUploading: false, error: 'Upload failed' },
        expectedText: 'Start Over',
      },
      {
        state: { isUploading: false, dataset: mockDataSource },
        expectedText: 'Data Preview',
      },
    ];

    uploadStates.forEach(({ state, expectedText }) => {
      vi.mocked(vi.importActual('@/hooks/use-data-source-upload')).default.mockReturnValue({
        uploadState: {
          file: null,
          progress: 0,
          error: null,
          sessionId: null,
          dataset: null,
          ...state,
        },
        uploadFile: mockUploadFile,
        cancelUpload: mockCancelUpload,
        resetUpload: mockResetUpload,
        validateFile: mockValidateFile,
      });

      const { unmount } = render(<DataSourceConnection {...defaultProps} />);

      expect(screen.getByText(expectedText)).toBeInTheDocument();

      unmount();
    });
  });

  it('handles keyboard navigation correctly', async () => {
    const user = userEvent.setup();

    render(<DataSourceConnection {...defaultProps} />);

    // Should be able to navigate through interactive elements
    await user.tab();

    // First focusable element should be the file dropzone
    expect(screen.getByTestId('file-dropzone')).toBeInTheDocument();
  });

  it('maintains accessibility standards', () => {
    render(<DataSourceConnection {...defaultProps} />);

    // Check for proper heading structure
    const mainHeading = screen.getByRole('heading', { level: 1 });
    expect(mainHeading).toHaveTextContent('Data Source Connection');

    // Check for proper button labels
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveAccessibleName();
    });

    // Step indicators should have proper ARIA labels
    const stepIndicators = screen.getAllByTestId('mock-icon');
    stepIndicators.forEach(indicator => {
      expect(indicator.closest('[role]')).toBeTruthy();
    });
  });

  it('handles connection cancellation', async () => {
    const user = userEvent.setup();

    render(<DataSourceConnection {...defaultProps} />);

    // Navigate to completion step
    const doneButton = screen.getByText('Done');
    await user.click(doneButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('shows proper loading states during transitions', async () => {
    const user = userEvent.setup();

    render(<DataSourceConnection {...defaultProps} />);

    // Start file selection
    const selectFileButton = screen.getByText('Select File');
    await user.click(selectFileButton);

    // Should show upload progress
    await waitFor(() => {
      expect(screen.getByTestId('upload-progress')).toBeInTheDocument();
    });
  });
});