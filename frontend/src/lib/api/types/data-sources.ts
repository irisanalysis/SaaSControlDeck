/**
 * TypeScript type definitions for Data Source Connection API
 * Frontend-specific type definitions with backend compatibility
 */

// Basic enums
export enum DataSourceType {
  CSV = "csv",
  JSON = "json",
  EXCEL = "excel",
  PARQUET = "parquet"
}

export enum DataSourceStatus {
  UPLOADING = "uploading",
  PROCESSING = "processing",
  READY = "ready",
  ERROR = "error"
}

export enum UploadSessionStatus {
  UPLOADING = "uploading",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled"
}

export enum DataQualitySeverity {
  INFO = "info",
  WARNING = "warning",
  ERROR = "error",
  CRITICAL = "critical"
}

// Data models
export interface ColumnInfo {
  id?: number;
  column_name: string;
  column_index: number;
  data_type: string; // "string" | "number" | "date" | "boolean" | "null"
  is_nullable: boolean;
  unique_count: number;
  missing_count: number;
  min_value?: string | null;
  max_value?: string | null;
  avg_value?: number | null;
  std_value?: number | null;
  sample_values: string[];
}

export interface DataSourceMetadata {
  encoding: string;
  delimiter?: string | null;
  has_header: boolean;
  columns: ColumnInfo[];
  data_types: Record<string, string>;
  sample_data: Record<string, any>[];
  missing_values_count: number;
  total_memory_usage?: number | null;
  file_info: Record<string, any>;
}

// Request models
export interface DataSourceCreate {
  name: string;
  type: DataSourceType;
  project_id: number;
  description?: string;
}

export interface DataSourceUpdate {
  name?: string;
  description?: string;
  status?: DataSourceStatus;
}

export interface UploadSessionCreate {
  filename: string;
  file_size: number;
  project_id: number;
  chunk_size?: number;
}

// Response models
export interface DataSource {
  id: number;
  name: string;
  type: DataSourceType;
  project_id: number;
  file_path?: string | null;
  file_size?: number | null;
  rows_count?: number | null;
  columns_count?: number | null;
  status: DataSourceStatus;
  metadata?: DataSourceMetadata | null;
  file_hash?: string | null;
  original_filename?: string | null;
  mime_type?: string | null;
  encoding?: string | null;
  delimiter?: string | null;
  has_header?: boolean | null;
  preview_data?: Record<string, any>[] | null;
  error_details?: string | null;
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
  processing_started_at?: string | null;
  processing_completed_at?: string | null;
}

export interface UploadSession {
  id: string;
  user_id: number;
  project_id: number;
  filename: string;
  file_size: number;
  uploaded_size: number;
  chunk_size: number;
  total_chunks: number;
  uploaded_chunks: number;
  status: UploadSessionStatus;
  dataset_id?: number | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string;
}

export interface DataSourcePreview {
  dataset_id: number;
  rows_count: number;
  columns_count: number;
  columns: ColumnInfo[];
  sample_data: Record<string, any>[];
  data_types: Record<string, string>;
  missing_values_summary: Record<string, number>;
  memory_usage?: number | null;
}

export interface DataQualityCheck {
  id: number;
  dataset_id: number;
  check_type: string;
  column_name?: string | null;
  severity: DataQualitySeverity;
  message: string;
  details: Record<string, any>;
  affected_rows: number;
  created_at: string;
}

export interface DataSourceList {
  items: DataSource[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface DataSourceAnalytics {
  total_datasets: number;
  datasets_by_type: Record<string, number>;
  datasets_by_status: Record<string, number>;
  total_size: number;
  total_rows: number;
  recent_uploads: DataSource[];
  quality_issues: number;
}

export interface FileUploadResponse {
  success: boolean;
  session_id: string;
  dataset_id?: number | null;
  message: string;
  upload_url?: string | null;
}

export interface ChunkUploadResponse {
  success: boolean;
  chunk_index: number;
  uploaded_chunks: number;
  total_chunks: number;
  progress_percentage: number;
  is_complete: boolean;
  message: string;
}

// Error handling
export interface APIError {
  detail: string;
  status_code?: number;
}

export class DataSourceAPIError extends Error {
  public statusCode?: number;
  public detail: string;

  constructor(detail: string, statusCode?: number) {
    super(detail);
    this.name = 'DataSourceAPIError';
    this.detail = detail;
    this.statusCode = statusCode;
  }
}

// Tool types
export type FileUploadProgressCallback = (progress: {
  uploaded: number;
  total: number;
  percentage: number;
}) => void;

export interface UploadOptions {
  onProgress?: FileUploadProgressCallback;
  chunkSize?: number;
  timeout?: number;
}

// React Hook types
export interface UseUploadState {
  isUploading: boolean;
  progress: number;
  error: string | null;
  sessionId: string | null;
  dataset: DataSource | null;
}

export interface UseDatasetListState {
  datasets: DataSource[];
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    size: number;
    total: number;
    pages: number;
  };
}

export interface UseDataPreviewState {
  preview: DataSourcePreview | null;
  qualityChecks: DataQualityCheck[];
  loading: boolean;
  error: string | null;
}

// Constants
export const SUPPORTED_FILE_TYPES = [
  'text/csv',
  'application/json',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/octet-stream'
] as const;

export const SUPPORTED_FILE_EXTENSIONS = [
  '.csv',
  '.json',
  '.xlsx',
  '.xls',
  '.parquet'
] as const;

export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
export const DEFAULT_CHUNK_SIZE = 1024 * 1024; // 1MB
export const PREVIEW_ROWS = 100;

// Frontend-specific types
export interface FileUploadState {
  file: File | null;
  isUploading: boolean;
  progress: number;
  error: string | null;
  sessionId: string | null;
  dataset: DataSource | null;
}

export interface DataPreviewTableProps {
  preview: DataSourcePreview;
  onColumnClick?: (column: ColumnInfo) => void;
  maxRows?: number;
}

export interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  onError: (error: string) => void;
  acceptedTypes?: string[];
  maxFileSize?: number;
  disabled?: boolean;
}

export interface UploadProgressProps {
  progress: number;
  fileName: string;
  fileSize: number;
  uploadedSize: number;
  onCancel?: () => void;
  status: 'uploading' | 'processing' | 'completed' | 'error';
}

export interface DataSourceFormProps {
  onSubmit: (data: DataSourceCreate) => void;
  onCancel: () => void;
  initialData?: Partial<DataSourceCreate>;
  isLoading?: boolean;
}

export interface DataSourceConnectionState {
  currentStep: 'select' | 'upload' | 'preview' | 'complete';
  selectedFile: File | null;
  uploadState: FileUploadState;
  previewData: DataSourcePreview | null;
  qualityChecks: DataQualityCheck[];
  errors: Record<string, string>;
}

// Frontend-specific error types
export class FileValidationError extends Error {
  constructor(
    message: string,
    public code: 'SIZE_EXCEEDED' | 'INVALID_TYPE' | 'INVALID_EXTENSION'
  ) {
    super(message);
    this.name = 'FileValidationError';
  }
}

export class UploadTimeoutError extends Error {
  constructor(message: string = 'Upload timed out') {
    super(message);
    this.name = 'UploadTimeoutError';
  }
}

// Aliases for convenience
export type Dataset = DataSource;
export type FileType = DataSourceType;
export type DatasetStatus = DataSourceStatus;
export type ColumnMetadata = ColumnInfo;
export type DatasetMetadata = DataSourceMetadata;