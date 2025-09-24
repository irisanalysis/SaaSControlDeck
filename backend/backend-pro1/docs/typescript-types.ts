// TypeScript类型定义 - 数据源连接API
// 供前端开发使用

// 基础枚举类型
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

// 数据模型接口
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

// 请求模型
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

// 响应模型
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

// API客户端接口
export interface DataSourceAPI {
  // 文件上传相关
  createUploadSession(data: UploadSessionCreate): Promise<UploadSession>;
  uploadFile(file: File, projectId: number): Promise<FileUploadResponse>;
  uploadChunk(sessionId: string, chunkIndex: number, chunk: File): Promise<ChunkUploadResponse>;
  getUploadProgress(sessionId: string): Promise<UploadSession>;
  cancelUpload(sessionId: string): Promise<{ message: string }>;
  listUploadSessions(status?: string, limit?: number, offset?: number): Promise<{
    items: UploadSession[];
    total: number;
    limit: number;
    offset: number;
  }>;

  // 数据预览相关
  getDataPreview(datasetId: number): Promise<DataSourcePreview>;
  listDatasets(params?: {
    project_id?: number;
    status?: string;
    type?: string;
    page?: number;
    size?: number;
  }): Promise<DataSourceList>;
  getQualityChecks(datasetId: number): Promise<DataQualityCheck[]>;
  triggerAnalysis(datasetId: number): Promise<{ message: string; dataset_id: number }>;

  // 数据管理相关
  getDataset(datasetId: number): Promise<DataSource>;
  updateDataset(datasetId: number, data: DataSourceUpdate): Promise<DataSource>;
  deleteDataset(datasetId: number): Promise<{ message: string; dataset_id: number }>;
  getAnalytics(projectId?: number): Promise<DataSourceAnalytics>;
  getProjectSummary(projectId: number): Promise<{
    project_id: number;
    datasets_summary: {
      total_count: number;
      ready_count: number;
      processing_count: number;
      error_count: number;
      total_size: number;
      total_rows: number;
    };
  }>;
}

// 错误处理
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

// 工具类型
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

// React Hook 相关类型
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

// 常量定义
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

// 表单验证模式 (Zod schemas in TypeScript)
export const uploadSessionCreateSchema = {
  filename: { required: true, minLength: 1, maxLength: 255 },
  file_size: { required: true, min: 1, max: MAX_FILE_SIZE },
  project_id: { required: true, min: 1 },
  chunk_size: { optional: true, min: 1024, default: DEFAULT_CHUNK_SIZE }
};

export const dataSourceUpdateSchema = {
  name: { optional: true, minLength: 1, maxLength: 200 },
  description: { optional: true, maxLength: 1000 },
  status: { optional: true, enum: Object.values(DataSourceStatus) }
};

// 前端组件Props类型
export interface FileUploaderProps {
  projectId: number;
  onUploadComplete?: (dataset: DataSource) => void;
  onUploadError?: (error: string) => void;
  acceptedTypes?: string[];
  maxFileSize?: number;
  allowChunked?: boolean;
}

export interface DataPreviewProps {
  datasetId: number;
  showQualityChecks?: boolean;
  maxPreviewRows?: number;
}

export interface DatasetListProps {
  projectId?: number;
  filters?: {
    status?: DataSourceStatus[];
    type?: DataSourceType[];
  };
  onDatasetSelect?: (dataset: DataSource) => void;
  onDatasetDelete?: (datasetId: number) => void;
}

export interface AnalyticsDashboardProps {
  projectId?: number;
  refreshInterval?: number;
}