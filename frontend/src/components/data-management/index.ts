/**
 * Data Management Components Export
 */

export { default as DataSourceConnection } from './data-source-connection';
export type { DataSourceConnectionProps } from './data-source-connection';

// Re-export related UI components for convenience
export { default as FileDropzone } from '../ui/file-dropzone';
export type { FileDropzoneProps } from '../ui/file-dropzone';

export { default as UploadProgress } from '../ui/upload-progress';
export type { UploadProgressProps } from '../ui/upload-progress';

export { default as DataPreviewTable } from '../ui/data-preview-table';
export type { DataPreviewTableProps } from '../ui/data-preview-table';

// Re-export hooks
export { default as useDataSourceUpload } from '../../hooks/use-data-source-upload';
export type {
  UseDataSourceUploadOptions,
  UseDataSourceUploadReturn
} from '../../hooks/use-data-source-upload';

export { default as useDataPreview } from '../../hooks/use-data-preview';
export type {
  UseDataPreviewOptions,
  UseDataPreviewReturn
} from '../../hooks/use-data-preview';

// Re-export API client
export { default as dataSourceAPI } from '../../lib/api/data-sources';

// Re-export types
export * from '../../lib/api/types/data-sources';