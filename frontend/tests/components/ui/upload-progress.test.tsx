/**
 * Unit tests for UploadProgress component
 * Tests progress display, status handling, and user interactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadProgress from '@/components/ui/upload-progress';

describe('UploadProgress', () => {
  const mockOnCancel = vi.fn();

  const defaultProps = {
    progress: 50,
    fileName: 'test-file.csv',
    fileSize: 1024000, // 1MB
    uploadedSize: 512000, // 512KB
    onCancel: mockOnCancel,
    status: 'uploading' as const,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with default props', () => {
    render(<UploadProgress {...defaultProps} />);

    expect(screen.getByText('test-file.csv')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText(/512\s*KB\s*\/\s*1\s*MB/)).toBeInTheDocument();
  });

  it('displays correct progress percentage', () => {
    const { rerender } = render(
      <UploadProgress {...defaultProps} progress={25} />
    );

    expect(screen.getByText('25%')).toBeInTheDocument();

    rerender(<UploadProgress {...defaultProps} progress={75} />);
    expect(screen.getByText('75%')).toBeInTheDocument();

    rerender(<UploadProgress {...defaultProps} progress={100} />);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('displays correct file size formatting', () => {
    const testCases = [
      {
        fileSize: 1024, // 1KB
        uploadedSize: 512, // 512B
        expected: /512\s*B\s*\/\s*1\s*KB/,
      },
      {
        fileSize: 1024 * 1024, // 1MB
        uploadedSize: 1024 * 512, // 512KB
        expected: /512\s*KB\s*\/\s*1\s*MB/,
      },
      {
        fileSize: 1024 * 1024 * 1024, // 1GB
        uploadedSize: 1024 * 1024 * 512, // 512MB
        expected: /512\s*MB\s*\/\s*1\s*GB/,
      },
    ];

    testCases.forEach(({ fileSize, uploadedSize, expected }, index) => {
      const { unmount } = render(
        <UploadProgress
          {...defaultProps}
          fileSize={fileSize}
          uploadedSize={uploadedSize}
        />
      );

      expect(screen.getByText(expected)).toBeInTheDocument();
      unmount();
    });
  });

  it('shows uploading status correctly', () => {
    render(<UploadProgress {...defaultProps} status="uploading" />);

    expect(screen.getByText(/uploading/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('shows processing status correctly', () => {
    render(<UploadProgress {...defaultProps} status="processing" />);

    expect(screen.getByText(/processing/i)).toBeInTheDocument();
    // Cancel button should still be available during processing
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('shows completed status correctly', () => {
    render(
      <UploadProgress
        {...defaultProps}
        status="completed"
        progress={100}
      />
    );

    expect(screen.getByText(/completed/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
  });

  it('shows error status correctly', () => {
    const errorMessage = 'Upload failed due to network error';

    render(
      <UploadProgress
        {...defaultProps}
        status="error"
        error={errorMessage}
      />
    );

    expect(screen.getByText(/error/i)).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();

    render(<UploadProgress {...defaultProps} status="uploading" />);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('disables cancel button when onCancel is not provided', () => {
    render(
      <UploadProgress
        {...defaultProps}
        onCancel={undefined}
        status="uploading"
      />
    );

    expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
  });

  it('shows progress bar with correct value', () => {
    render(<UploadProgress {...defaultProps} progress={75} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '75');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  it('handles edge case of zero progress', () => {
    render(
      <UploadProgress
        {...defaultProps}
        progress={0}
        uploadedSize={0}
      />
    );

    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(screen.getByText(/0\s*B\s*\/\s*1\s*MB/)).toBeInTheDocument();
  });

  it('handles edge case of 100% progress', () => {
    render(
      <UploadProgress
        {...defaultProps}
        progress={100}
        uploadedSize={1024000}
      />
    );

    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText(/1\s*MB\s*\/\s*1\s*MB/)).toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    render(
      <UploadProgress
        {...defaultProps}
        className="custom-upload-progress"
      />
    );

    const container = screen.getByRole('progressbar').closest('div');
    expect(container).toHaveClass('custom-upload-progress');
  });

  it('handles very long filenames gracefully', () => {
    const longFileName = 'a'.repeat(100) + '.csv';

    render(
      <UploadProgress
        {...defaultProps}
        fileName={longFileName}
      />
    );

    expect(screen.getByText(longFileName)).toBeInTheDocument();
  });

  it('handles special characters in filename', () => {
    const specialFileName = 'file with spaces & special-chars (1).csv';

    render(
      <UploadProgress
        {...defaultProps}
        fileName={specialFileName}
      />
    );

    expect(screen.getByText(specialFileName)).toBeInTheDocument();
  });

  it('shows correct ARIA labels for accessibility', () => {
    render(<UploadProgress {...defaultProps} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAccessibleName(/upload progress/i);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    expect(cancelButton).toBeInTheDocument();
  });

  it('updates progress smoothly during animation', () => {
    const { rerender } = render(
      <UploadProgress {...defaultProps} progress={25} />
    );

    expect(screen.getByText('25%')).toBeInTheDocument();

    // Simulate progress update
    rerender(<UploadProgress {...defaultProps} progress={50} />);
    expect(screen.getByText('50%')).toBeInTheDocument();

    rerender(<UploadProgress {...defaultProps} progress={75} />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('displays estimated time remaining when provided', () => {
    render(
      <UploadProgress
        {...defaultProps}
        estimatedTimeRemaining={30}
      />
    );

    expect(screen.getByText(/30 seconds remaining/i)).toBeInTheDocument();
  });

  it('formats estimated time correctly', () => {
    const timeTestCases = [
      { seconds: 30, expected: /30 seconds/i },
      { seconds: 90, expected: /1 minute/i },
      { seconds: 150, expected: /2 minutes/i },
      { seconds: 3600, expected: /1 hour/i },
    ];

    timeTestCases.forEach(({ seconds, expected }) => {
      const { unmount } = render(
        <UploadProgress
          {...defaultProps}
          estimatedTimeRemaining={seconds}
        />
      );

      expect(screen.getByText(expected)).toBeInTheDocument();
      unmount();
    });
  });

  it('handles upload speed display when provided', () => {
    render(
      <UploadProgress
        {...defaultProps}
        uploadSpeed={1024 * 1024} // 1 MB/s
      />
    );

    expect(screen.getByText(/1\s*MB\/s/i)).toBeInTheDocument();
  });

  it('formats upload speed correctly', () => {
    const speedTestCases = [
      { speed: 1024, expected: /1\s*KB\/s/i },
      { speed: 1024 * 1024, expected: /1\s*MB\/s/i },
      { speed: 1024 * 512, expected: /512\s*KB\/s/i },
    ];

    speedTestCases.forEach(({ speed, expected }) => {
      const { unmount } = render(
        <UploadProgress
          {...defaultProps}
          uploadSpeed={speed}
        />
      );

      expect(screen.getByText(expected)).toBeInTheDocument();
      unmount();
    });
  });

  it('shows retry option on error status', () => {
    const mockOnRetry = vi.fn();

    render(
      <UploadProgress
        {...defaultProps}
        status="error"
        error="Upload failed"
        onRetry={mockOnRetry}
      />
    );

    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnRetry = vi.fn();

    render(
      <UploadProgress
        {...defaultProps}
        status="error"
        error="Upload failed"
        onRetry={mockOnRetry}
      />
    );

    const retryButton = screen.getByRole('button', { name: /retry/i });
    await user.click(retryButton);

    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it('shows pause/resume functionality when supported', async () => {
    const user = userEvent.setup();
    const mockOnPause = vi.fn();
    const mockOnResume = vi.fn();

    render(
      <UploadProgress
        {...defaultProps}
        status="uploading"
        canPause={true}
        onPause={mockOnPause}
        onResume={mockOnResume}
      />
    );

    const pauseButton = screen.getByRole('button', { name: /pause/i });
    await user.click(pauseButton);

    expect(mockOnPause).toHaveBeenCalledTimes(1);
  });

  it('handles paused status correctly', () => {
    render(
      <UploadProgress
        {...defaultProps}
        status="paused"
        canPause={true}
      />
    );

    expect(screen.getByText(/paused/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /resume/i })).toBeInTheDocument();
  });

  it('prevents interaction when upload is completed', async () => {
    const user = userEvent.setup();

    render(
      <UploadProgress
        {...defaultProps}
        status="completed"
        progress={100}
      />
    );

    // Should not have cancel button
    expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();

    // Should show completed status
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });

  it('handles keyboard interactions correctly', async () => {
    const user = userEvent.setup();

    render(<UploadProgress {...defaultProps} status="uploading" />);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });

    // Test keyboard navigation
    await user.tab();
    expect(cancelButton).toHaveFocus();

    // Test Enter key
    await user.keyboard('{Enter}');
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });
});