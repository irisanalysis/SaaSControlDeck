"use client";

import React, { useState, useMemo } from 'react';
import {
  Info,
  AlertTriangle,
  CheckCircle,
  Database,
  Hash,
  Calendar,
  Type,
  ToggleLeft,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  DataSourcePreview,
  ColumnInfo,
  DataQualityCheck,
} from '@/lib/api/types/data-sources';

export interface DataPreviewTableProps {
  preview: DataSourcePreview;
  qualityChecks?: DataQualityCheck[];
  onColumnClick?: (column: ColumnInfo) => void;
  maxRows?: number;
  className?: string;
}

export function DataPreviewTable({
  preview,
  qualityChecks = [],
  onColumnClick,
  maxRows = 10,
  className,
}: DataPreviewTableProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [showColumnDetails, setShowColumnDetails] = useState(false);
  const [selectedColumn, setSelectedColumn] = useState<ColumnInfo | null>(null);

  const rowsPerPage = maxRows;
  const totalPages = Math.ceil(preview.sample_data.length / rowsPerPage);
  const startIndex = currentPage * rowsPerPage;
  const endIndex = Math.min(startIndex + rowsPerPage, preview.sample_data.length);
  const currentRows = preview.sample_data.slice(startIndex, endIndex);

  // Group quality checks by column
  const qualityChecksByColumn = useMemo(() => {
    const grouped: Record<string, DataQualityCheck[]> = {};
    qualityChecks.forEach(check => {
      if (check.column_name) {
        if (!grouped[check.column_name]) {
          grouped[check.column_name] = [];
        }
        grouped[check.column_name].push(check);
      }
    });
    return grouped;
  }, [qualityChecks]);

  const getDataTypeIcon = (dataType: string) => {
    switch (dataType.toLowerCase()) {
      case 'number':
      case 'integer':
      case 'float':
        return <Hash className="w-4 h-4" />;
      case 'string':
      case 'text':
        return <Type className="w-4 h-4" />;
      case 'date':
      case 'datetime':
        return <Calendar className="w-4 h-4" />;
      case 'boolean':
        return <ToggleLeft className="w-4 h-4" />;
      default:
        return <Database className="w-4 h-4" />;
    }
  };

  const getDataTypeColor = (dataType: string) => {
    switch (dataType.toLowerCase()) {
      case 'number':
      case 'integer':
      case 'float':
        return 'text-blue-600 bg-blue-50';
      case 'string':
      case 'text':
        return 'text-green-600 bg-green-50';
      case 'date':
      case 'datetime':
        return 'text-purple-600 bg-purple-50';
      case 'boolean':
        return 'text-orange-600 bg-orange-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getQualitySeverityConfig = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50' };
      case 'error':
        return { icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-50' };
      case 'warning':
        return { icon: AlertTriangle, color: 'text-yellow-600', bg: 'bg-yellow-50' };
      case 'info':
        return { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50' };
      default:
        return { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' };
    }
  };

  const handleColumnClick = (column: ColumnInfo) => {
    setSelectedColumn(column);
    onColumnClick?.(column);
  };

  const formatCellValue = (value: any): string => {
    if (value === null || value === undefined) {
      return '';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <TooltipProvider>
      <div className={cn('w-full space-y-4', className)}>
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Rows</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{preview.rows_count.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Columns</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{preview.columns_count}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Missing Values</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {Object.values(preview.missing_values_summary).reduce((a, b) => a + b, 0)}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Column Details Toggle */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Data Preview</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowColumnDetails(!showColumnDetails)}
            className="ml-auto"
          >
            {showColumnDetails ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
            {showColumnDetails ? 'Hide' : 'Show'} Column Details
          </Button>
        </div>

        {/* Column Details Panel */}
        {showColumnDetails && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Column Information</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-32">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {preview.columns.map((column) => {
                    const qualityIssues = qualityChecksByColumn[column.column_name] || [];
                    const hasIssues = qualityIssues.length > 0;

                    return (
                      <Tooltip key={column.column_name}>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleColumnClick(column)}
                            className={cn(
                              'flex items-center justify-between w-full h-auto p-2 text-left',
                              hasIssues && 'bg-yellow-50 border-yellow-200',
                              selectedColumn?.column_name === column.column_name && 'bg-primary/10'
                            )}
                          >
                            <div className="flex items-center space-x-2 min-w-0">
                              <div className={cn('p-1 rounded', getDataTypeColor(column.data_type))}>
                                {getDataTypeIcon(column.data_type)}
                              </div>
                              <span className="text-sm font-medium truncate">
                                {column.column_name}
                              </span>
                            </div>
                            <div className="flex items-center space-x-1 ml-2">
                              <Badge variant="secondary" className="text-xs">
                                {column.data_type}
                              </Badge>
                              {hasIssues && (
                                <Badge variant="destructive" className="text-xs">
                                  {qualityIssues.length}
                                </Badge>
                              )}
                            </div>
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="space-y-1">
                            <p><strong>Type:</strong> {column.data_type}</p>
                            <p><strong>Unique:</strong> {column.unique_count}</p>
                            <p><strong>Missing:</strong> {column.missing_count}</p>
                            {column.min_value && <p><strong>Min:</strong> {column.min_value}</p>}
                            {column.max_value && <p><strong>Max:</strong> {column.max_value}</p>}
                            {qualityIssues.length > 0 && (
                              <div className="border-t pt-1">
                                <p className="font-medium text-red-600">Quality Issues:</p>
                                {qualityIssues.map((issue, idx) => (
                                  <p key={idx} className="text-xs text-red-500">
                                    {issue.message}
                                  </p>
                                ))}
                              </div>
                            )}
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Data Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Sample Data</CardTitle>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-muted-foreground">
                  Showing {startIndex + 1}-{endIndex} of {preview.sample_data.length} rows
                </span>
                {totalPages > 1 && (
                  <div className="flex items-center space-x-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                      disabled={currentPage === 0}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="text-xs px-2">
                      {currentPage + 1} / {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                      disabled={currentPage === totalPages - 1}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="w-full">
              <Table>
                <TableHeader>
                  <TableRow>
                    {preview.columns.map((column) => {
                      const qualityIssues = qualityChecksByColumn[column.column_name] || [];
                      const hasIssues = qualityIssues.length > 0;

                      return (
                        <TableHead
                          key={column.column_name}
                          className={cn(
                            'whitespace-nowrap cursor-pointer hover:bg-muted/50',
                            hasIssues && 'bg-yellow-50'
                          )}
                          onClick={() => handleColumnClick(column)}
                        >
                          <div className="flex items-center space-x-2">
                            <div className={cn('p-1 rounded', getDataTypeColor(column.data_type))}>
                              {getDataTypeIcon(column.data_type)}
                            </div>
                            <span className="font-medium">{column.column_name}</span>
                            {hasIssues && (
                              <Badge variant="destructive" className="text-xs">
                                {qualityIssues.length}
                              </Badge>
                            )}
                          </div>
                        </TableHead>
                      );
                    })}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentRows.map((row, rowIndex) => (
                    <TableRow key={startIndex + rowIndex}>
                      {preview.columns.map((column) => (
                        <TableCell
                          key={column.column_name}
                          className="whitespace-nowrap max-w-xs overflow-hidden text-ellipsis"
                        >
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className={cn(
                                row[column.column_name] === null || row[column.column_name] === undefined
                                  ? 'text-muted-foreground italic'
                                  : 'text-foreground'
                              )}>
                                {row[column.column_name] === null || row[column.column_name] === undefined
                                  ? '(null)'
                                  : formatCellValue(row[column.column_name])
                                }
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>{formatCellValue(row[column.column_name])}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  );
}

export default DataPreviewTable;