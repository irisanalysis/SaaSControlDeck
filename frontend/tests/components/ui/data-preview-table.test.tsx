/**
 * Unit tests for DataPreviewTable component
 * Tests data display, sorting, filtering, and quality checks
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataPreviewTable from '@/components/ui/data-preview-table';
import { mockDataPreview } from '../../setup';

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
  {
    id: 2,
    dataset_id: 1,
    check_type: 'data_type_inconsistency',
    column_name: 'id',
    severity: 'error' as const,
    message: 'Data type inconsistency found',
    details: { inconsistent_count: 2 },
    affected_rows: 2,
    created_at: new Date().toISOString(),
  },
];

describe('DataPreviewTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with data preview', () => {
    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
      />
    );

    // Check headers
    expect(screen.getByText('id')).toBeInTheDocument();
    expect(screen.getByText('name')).toBeInTheDocument();

    // Check data rows
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
  });

  it('displays column information in header', () => {
    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
      />
    );

    // Check for data type information
    expect(screen.getByText(/number/i)).toBeInTheDocument();
    expect(screen.getByText(/string/i)).toBeInTheDocument();
  });

  it('shows quality check indicators for columns with issues', () => {
    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={mockQualityChecks}
      />
    );

    // Should show warning indicator for 'name' column
    const nameHeader = screen.getByText('name').closest('th');
    expect(within(nameHeader!).getByTestId('mock-icon')).toBeInTheDocument();

    // Should show error indicator for 'id' column
    const idHeader = screen.getByText('id').closest('th');
    expect(within(idHeader!).getByTestId('mock-icon')).toBeInTheDocument();
  });

  it('limits rows when maxRows prop is provided', () => {
    const extendedPreview = {
      ...mockDataPreview,
      sample_data: [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' },
        { id: 3, name: 'Charlie' },
        { id: 4, name: 'David' },
        { id: 5, name: 'Eve' },
      ],
    };

    render(
      <DataPreviewTable
        preview={extendedPreview}
        qualityChecks={[]}
        maxRows={3}
      />
    );

    // Should show only 3 rows
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Charlie')).toBeInTheDocument();
    expect(screen.queryByText('David')).not.toBeInTheDocument();
    expect(screen.queryByText('Eve')).not.toBeInTheDocument();

    // Should show truncation message
    expect(screen.getByText(/showing 3 of 5 rows/i)).toBeInTheDocument();
  });

  it('handles sorting when column headers are clicked', async () => {
    const user = userEvent.setup();

    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
      />
    );

    const idHeader = screen.getByText('id').closest('th')!;
    await user.click(idHeader);

    // Should show sort indicator
    expect(within(idHeader).getByTestId('mock-icon')).toBeInTheDocument();
  });

  it('displays column statistics in tooltips or details', async () => {
    const user = userEvent.setup();

    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
        showColumnStats={true}
      />
    );

    const idHeader = screen.getByText('id').closest('th')!;
    await user.hover(idHeader);

    // Should show column statistics
    expect(screen.getByText(/unique count: 100/i)).toBeInTheDocument();
    expect(screen.getByText(/missing count: 0/i)).toBeInTheDocument();
  });

  it('shows quality check details when indicators are clicked', async () => {
    const user = userEvent.setup();

    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={mockQualityChecks}
      />
    );

    const nameHeader = screen.getByText('name').closest('th')!;
    const warningIcon = within(nameHeader).getByTestId('mock-icon');

    await user.click(warningIcon);

    // Should show quality check details
    expect(screen.getByText('Column has missing values')).toBeInTheDocument();
    expect(screen.getByText(/5 affected rows/i)).toBeInTheDocument();
  });

  it('handles empty data gracefully', () => {
    const emptyPreview = {
      ...mockDataPreview,
      sample_data: [],
      rows_count: 0,
    };

    render(
      <DataPreviewTable
        preview={emptyPreview}
        qualityChecks={[]}
      />
    );

    expect(screen.getByText(/no data available/i)).toBeInTheDocument();
  });

  it('displays data type badges correctly', () => {
    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
      />
    );

    // Should show data type badges
    expect(screen.getByText('number')).toBeInTheDocument();
    expect(screen.getByText('string')).toBeInTheDocument();
  });

  it('handles null and undefined values in data', () => {
    const previewWithNulls = {
      ...mockDataPreview,
      sample_data: [
        { id: 1, name: 'Alice' },
        { id: null, name: 'Bob' },
        { id: 3, name: null },
        { id: 4, name: undefined },
      ],
    };

    render(
      <DataPreviewTable
        preview={previewWithNulls}
        qualityChecks={[]}
      />
    );

    // Should display null/undefined values appropriately
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    // null and undefined should be shown as empty or with placeholder
    const cells = screen.getAllByRole('cell');
    expect(cells.some(cell => cell.textContent === '' || cell.textContent === '—')).toBeTruthy();
  });

  it('supports custom column renderers when provided', () => {
    const customRenderers = {
      id: (value: any) => `ID: ${value}`,
      name: (value: any) => value?.toUpperCase(),
    };

    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
        columnRenderers={customRenderers}
      />
    );

    expect(screen.getByText('ID: 1')).toBeInTheDocument();
    expect(screen.getByText('ALICE')).toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
        className="custom-table-class"
      />
    );

    const table = screen.getByRole('table');
    expect(table.closest('div')).toHaveClass('custom-table-class');
  });

  it('handles very wide tables with horizontal scrolling', () => {
    const widePreview = {
      ...mockDataPreview,
      columns: Array.from({ length: 20 }, (_, i) => ({
        column_name: `column_${i}`,
        column_index: i,
        data_type: 'string',
        is_nullable: true,
        unique_count: 100,
        missing_count: 0,
        sample_values: ['value1', 'value2', 'value3'],
      })),
      sample_data: [
        Object.fromEntries(Array.from({ length: 20 }, (_, i) => [`column_${i}`, `value_${i}`])),
      ],
    };

    render(
      <DataPreviewTable
        preview={widePreview}
        qualityChecks={[]}
      />
    );

    // Should render all columns
    expect(screen.getByText('column_0')).toBeInTheDocument();
    expect(screen.getByText('column_19')).toBeInTheDocument();

    // Table container should be scrollable
    const tableContainer = screen.getByRole('table').closest('div');
    expect(tableContainer).toHaveClass(/overflow/);
  });

  it('shows loading state when specified', () => {
    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
        loading={true}
      />
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('displays data summary statistics', () => {
    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
        showSummary={true}
      />
    );

    expect(screen.getByText(/100 rows/i)).toBeInTheDocument();
    expect(screen.getByText(/5 columns/i)).toBeInTheDocument();
    expect(screen.getByText(/1 kb/i)).toBeInTheDocument();
  });

  it('handles filter functionality when enabled', async () => {
    const user = userEvent.setup();

    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
        filterable={true}
      />
    );

    const filterInput = screen.getByPlaceholderText(/filter/i);
    await user.type(filterInput, 'Alice');

    // Should filter rows to show only Alice
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.queryByText('Bob')).not.toBeInTheDocument();
  });

  it('displays pagination when enabled', () => {
    const largePreview = {
      ...mockDataPreview,
      sample_data: Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        name: `User ${i + 1}`,
      })),
    };

    render(
      <DataPreviewTable
        preview={largePreview}
        qualityChecks={[]}
        paginated={true}
        pageSize={10}
      />
    );

    // Should show pagination controls
    expect(screen.getByText(/page/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
  });

  it('handles accessibility correctly', () => {
    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={mockQualityChecks}
      />
    );

    const table = screen.getByRole('table');
    expect(table).toHaveAttribute('aria-label', expect.stringContaining('data preview'));

    // Headers should be properly associated
    const headers = screen.getAllByRole('columnheader');
    headers.forEach(header => {
      expect(header).toHaveAttribute('scope', 'col');
    });

    // Quality check indicators should have appropriate ARIA labels
    const qualityIndicators = screen.getAllByTestId('mock-icon');
    qualityIndicators.forEach(indicator => {
      expect(indicator.closest('button')).toHaveAttribute('aria-label');
    });
  });

  it('supports keyboard navigation', async () => {
    const user = userEvent.setup();

    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={mockQualityChecks}
      />
    );

    // Should be able to tab through interactive elements
    await user.tab();

    // Should focus on sortable column headers
    const firstHeader = screen.getByText('id').closest('th')!;
    expect(firstHeader).toHaveFocus();

    // Should be able to activate with Enter/Space
    await user.keyboard('{Enter}');

    // Sort should be activated
    expect(within(firstHeader).getByTestId('mock-icon')).toBeInTheDocument();
  });

  it('exports data when export button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnExport = vi.fn();

    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
        onExport={mockOnExport}
      />
    );

    const exportButton = screen.getByRole('button', { name: /export/i });
    await user.click(exportButton);

    expect(mockOnExport).toHaveBeenCalledWith(mockDataPreview.sample_data);
  });

  it('handles responsive behavior on mobile devices', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(
      <DataPreviewTable
        preview={mockDataPreview}
        qualityChecks={[]}
      />
    );

    // Should adapt layout for mobile
    const table = screen.getByRole('table');
    expect(table.closest('div')).toHaveClass(/responsive/);
  });
});