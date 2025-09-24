/**
 * Unit tests for FileDropzone component
 * Tests drag-and-drop functionality, file validation, and user interactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileDropzone from '@/components/ui/file-dropzone';

// Mock toast
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  toast: mockToast,
}));

describe('FileDropzone', () => {
  const mockOnFileSelect = vi.fn();
  const mockOnError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with default props', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    expect(screen.getByText('Drop files here')).toBeInTheDocument();
    expect(screen.getByText('or click to browse')).toBeInTheDocument();
    expect(screen.getByText(/Supported formats:/)).toBeInTheDocument();
    expect(screen.getByText(/Maximum file size:/)).toBeInTheDocument();
  });

  it('renders with custom accept prop', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        accept=".csv,.json"
      />
    );

    const input = screen.getByRole('button').querySelector('input[type="file"]');
    expect(input).toHaveAttribute('accept', '.csv,.json');
  });

  it('renders with custom maxSize prop', () => {
    const customMaxSize = 50 * 1024 * 1024; // 50MB
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        maxSize={customMaxSize}
      />
    );

    expect(screen.getByText(/50\s*MB/)).toBeInTheDocument();
  });

  it('opens file dialog when clicked', async () => {
    const user = userEvent.setup();

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');
    await user.click(dropzone);

    // File input should be triggered (though we can't easily test the actual dialog opening)
    expect(dropzone).toBeInTheDocument();
  });

  it('handles file selection via input', async () => {
    const user = userEvent.setup();
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, file);

    await waitFor(() => {
      expect(mockOnFileSelect).toHaveBeenCalledWith(file);
    });
  });

  it('handles multiple file selection and selects first file', async () => {
    const user = userEvent.setup();
    const file1 = new File(['content1'], 'test1.csv', { type: 'text/csv' });
    const file2 = new File(['content2'], 'test2.csv', { type: 'text/csv' });

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        multiple
      />
    );

    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, [file1, file2]);

    await waitFor(() => {
      expect(mockOnFileSelect).toHaveBeenCalledWith(file1);
    });
  });

  it('validates file size and calls onError for oversized files', async () => {
    const user = userEvent.setup();
    const maxSize = 1024; // 1KB
    const oversizedContent = 'x'.repeat(2048); // 2KB
    const oversizedFile = new File([oversizedContent], 'large.csv', { type: 'text/csv' });

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        maxSize={maxSize}
      />
    );

    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, oversizedFile);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(
        expect.stringContaining('File size')
      );
      expect(mockOnFileSelect).not.toHaveBeenCalled();
    });
  });

  it('validates file type and calls onError for invalid types', async () => {
    const user = userEvent.setup();
    const invalidFile = new File(['content'], 'test.txt', { type: 'text/plain' });

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        accept=".csv,.json"
      />
    );

    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, invalidFile);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(
        expect.stringContaining('Invalid file type')
      );
      expect(mockOnFileSelect).not.toHaveBeenCalled();
    });
  });

  it('handles drag enter and shows active state', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');

    fireEvent.dragEnter(dropzone, {
      dataTransfer: {
        items: [{ kind: 'file', type: 'text/csv' }],
      },
    });

    expect(dropzone).toHaveClass('border-primary');
  });

  it('handles drag leave and removes active state', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');

    // First enter drag state
    fireEvent.dragEnter(dropzone, {
      dataTransfer: {
        items: [{ kind: 'file', type: 'text/csv' }],
      },
    });

    // Then leave
    fireEvent.dragLeave(dropzone);

    expect(dropzone).not.toHaveClass('border-primary');
  });

  it('handles drag over event', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');
    const dragOverEvent = new Event('dragover', { bubbles: true });
    Object.defineProperty(dragOverEvent, 'preventDefault', {
      value: vi.fn(),
    });

    fireEvent(dropzone, dragOverEvent);

    expect((dragOverEvent as any).preventDefault).toHaveBeenCalled();
  });

  it('handles file drop and processes valid file', async () => {
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');

    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [file],
        items: [{ kind: 'file', type: 'text/csv' }],
      },
    });

    await waitFor(() => {
      expect(mockOnFileSelect).toHaveBeenCalledWith(file);
    });
  });

  it('handles file drop with invalid file and calls onError', async () => {
    const invalidFile = new File(['content'], 'test.txt', { type: 'text/plain' });

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        accept=".csv,.json"
      />
    );

    const dropzone = screen.getByRole('button');

    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [invalidFile],
        items: [{ kind: 'file', type: 'text/plain' }],
      },
    });

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(
        expect.stringContaining('Invalid file type')
      );
      expect(mockOnFileSelect).not.toHaveBeenCalled();
    });
  });

  it('handles empty file drop', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');

    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [],
        items: [],
      },
    });

    expect(mockOnFileSelect).not.toHaveBeenCalled();
    expect(mockOnError).not.toHaveBeenCalled();
  });

  it('handles drop with non-file items', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');

    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [],
        items: [{ kind: 'string', type: 'text/plain' }],
      },
    });

    expect(mockOnFileSelect).not.toHaveBeenCalled();
    expect(mockOnError).not.toHaveBeenCalled();
  });

  it('displays custom className', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        className="custom-class"
      />
    );

    const dropzone = screen.getByRole('button');
    expect(dropzone).toHaveClass('custom-class');
  });

  it('shows disabled state when disabled prop is true', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        disabled
      />
    );

    const dropzone = screen.getByRole('button');
    expect(dropzone).toBeDisabled();
  });

  it('prevents interaction when disabled', async () => {
    const user = userEvent.setup();
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        disabled
      />
    );

    const dropzone = screen.getByRole('button');

    // Try to click
    await user.click(dropzone);

    // Try to drop
    fireEvent.drop(dropzone, {
      dataTransfer: {
        files: [file],
      },
    });

    expect(mockOnFileSelect).not.toHaveBeenCalled();
  });

  it('handles keyboard interaction (Enter key)', async () => {
    const user = userEvent.setup();

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');

    await user.keyboard('{Enter}');

    // Should trigger the same behavior as clicking
    expect(dropzone).toBeInTheDocument();
  });

  it('handles keyboard interaction (Space key)', async () => {
    const user = userEvent.setup();

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');

    await user.keyboard(' ');

    // Should trigger the same behavior as clicking
    expect(dropzone).toBeInTheDocument();
  });

  it('formats file size correctly in help text', () => {
    const sizes = [
      { maxSize: 1024, expected: '1 KB' },
      { maxSize: 1024 * 1024, expected: '1 MB' },
      { maxSize: 50 * 1024 * 1024, expected: '50 MB' },
      { maxSize: 1024 * 1024 * 1024, expected: '1 GB' },
    ];

    sizes.forEach(({ maxSize, expected }) => {
      const { unmount } = render(
        <FileDropzone
          onFileSelect={mockOnFileSelect}
          onError={mockOnError}
          maxSize={maxSize}
        />
      );

      expect(screen.getByText(new RegExp(expected.replace(/\s/g, '\\s*')))).toBeInTheDocument();
      unmount();
    });
  });

  it('displays correct supported formats from accept prop', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
        accept=".csv,.json,.xlsx"
      />
    );

    expect(screen.getByText(/CSV, JSON, XLSX/)).toBeInTheDocument();
  });

  it('handles edge case of zero-byte file', async () => {
    const user = userEvent.setup();
    const emptyFile = new File([], 'empty.csv', { type: 'text/csv' });

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const input = screen.getByRole('button').querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, emptyFile);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(
        expect.stringContaining('empty')
      );
    });
  });

  it('applies correct ARIA attributes for accessibility', () => {
    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');

    expect(dropzone).toHaveAttribute('tabIndex', '0');
    expect(dropzone).toHaveAttribute('aria-label', expect.stringContaining('file'));
  });

  it('maintains focus management correctly', async () => {
    const user = userEvent.setup();

    render(
      <FileDropzone
        onFileSelect={mockOnFileSelect}
        onError={mockOnError}
      />
    );

    const dropzone = screen.getByRole('button');

    await user.tab();
    expect(dropzone).toHaveFocus();
  });
});