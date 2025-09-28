/**
 * Data Sources API Client
 * Handles all API interactions for data source management, file uploads, and previews
 * Now with automatic JWT authentication integration
 */

import {
  DataSource,
  DataSourceCreate,
  DataSourceUpdate,
  DataSourceList,
  DataSourcePreview,
  UploadSession,
  UploadSessionCreate,
  FileUploadResponse,
  ChunkUploadResponse,
  DataQualityCheck,
  DataSourceAPIError,
  UploadOptions,
  SUPPORTED_FILE_TYPES,
  MAX_FILE_SIZE,
  DEFAULT_CHUNK_SIZE,
} from './types/data-sources';
import authAPI from './auth';

// 使用前端API代理路由到统一后端服务
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

class DataSourceAPIClient {
  private baseURL: string;
  private defaultHeaders: HeadersInit;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    // Get authentication headers
    const authHeaders = authAPI.getAuthHeaders();

    const config: RequestInit = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...authHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new DataSourceAPIError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof DataSourceAPIError) {
        throw error;
      }
      throw new DataSourceAPIError(
        error instanceof Error ? error.message : 'Network error'
      );
    }
  }

  // File Upload Methods
  async createUploadSession(data: UploadSessionCreate): Promise<UploadSession> {
    return this.request<UploadSession>('/data/upload/session', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async uploadFile(
    file: File,
    projectId: number,
    options: UploadOptions = {}
  ): Promise<FileUploadResponse> {
    // Validate file
    this.validateFile(file);

    // Check if user is authenticated
    if (!authAPI.isAuthenticated()) {
      throw new DataSourceAPIError('Authentication required. Please log in.', 401);
    }

    // Now use authenticated upload with chunking support
    const chunkSize = options.chunkSize || DEFAULT_CHUNK_SIZE;

    // For small files, use direct upload
    if (file.size <= chunkSize) {
      return this.uploadFileDirectly(file, projectId, options);
    }

    // For large files, use chunked upload
    return this.uploadFileChunked(file, projectId, options);
  }

  private validateFile(file: File): void {
    if (file.size > MAX_FILE_SIZE) {
      throw new DataSourceAPIError(
        `File size ${(file.size / 1024 / 1024).toFixed(1)}MB exceeds maximum allowed size of ${MAX_FILE_SIZE / 1024 / 1024}MB`
      );
    }

    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED_FILE_TYPES.includes(file.type as any) &&
        !extension.match(/\.(csv|json|xlsx|xls|parquet)$/)) {
      throw new DataSourceAPIError(
        'Unsupported file type. Please upload CSV, JSON, Excel, or Parquet files.'
      );
    }
  }

  private async uploadFileDirectly(
    file: File,
    projectId: number,
    options: UploadOptions
  ): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId.toString());

    // Get authentication headers
    const authHeaders = authAPI.getAuthHeaders();
    const xhr = new XMLHttpRequest();

    return new Promise((resolve, reject) => {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && options.onProgress) {
          const percentage = (event.loaded / event.total) * 100;
          options.onProgress({
            uploaded: event.loaded,
            total: event.total,
            percentage,
          });
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            // Now using the actual upload endpoint instead of test endpoint
            resolve(response);
          } catch (error) {
            reject(new DataSourceAPIError('Invalid response format'));
          }
        } else if (xhr.status === 401) {
          reject(new DataSourceAPIError('Authentication required. Please log in.', 401));
        } else {
          reject(new DataSourceAPIError(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new DataSourceAPIError('Upload failed'));
      });

      // Set up the request with authentication
      // 使用API代理路由：/api/data/upload/file -> /upload/file
      xhr.open('POST', `${this.baseURL}/data/upload/file`);

      // Add authentication header if available
      if (authHeaders.Authorization) {
        xhr.setRequestHeader('Authorization', authHeaders.Authorization as string);
      }

      xhr.send(formData);
    });
  }

  private async uploadFileChunked(
    file: File,
    projectId: number,
    options: UploadOptions
  ): Promise<FileUploadResponse> {
    const chunkSize = options.chunkSize || DEFAULT_CHUNK_SIZE;
    const totalChunks = Math.ceil(file.size / chunkSize);

    // Create upload session
    const session = await this.createUploadSession({
      filename: file.name,
      file_size: file.size,
      project_id: projectId,
      chunk_size: chunkSize,
    });

    let uploadedChunks = 0;

    // Upload chunks
    for (let i = 0; i < totalChunks; i++) {
      const start = i * chunkSize;
      const end = Math.min(start + chunkSize, file.size);
      const chunk = file.slice(start, end);

      const chunkFile = new File([chunk], `chunk-${i}`, { type: file.type });

      await this.uploadChunk(session.id, i, chunkFile);

      uploadedChunks++;

      if (options.onProgress) {
        const percentage = (uploadedChunks / totalChunks) * 100;
        options.onProgress({
          uploaded: uploadedChunks * chunkSize,
          total: file.size,
          percentage,
        });
      }
    }

    // Get final result
    const finalSession = await this.getUploadProgress(session.id);

    return {
      success: true,
      session_id: session.id,
      dataset_id: finalSession.dataset_id,
      message: 'File uploaded successfully',
    };
  }

  async uploadChunk(
    sessionId: string,
    chunkIndex: number,
    chunk: File
  ): Promise<ChunkUploadResponse> {
    const formData = new FormData();
    formData.append('chunk', chunk);
    formData.append('chunk_index', chunkIndex.toString());

    const response = await fetch(
      `${this.baseURL}/data/upload/chunk/${sessionId}`,
      {
        method: 'POST',
        body: formData,
      }
    );

    if (!response.ok) {
      throw new DataSourceAPIError(`Chunk upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getUploadProgress(sessionId: string): Promise<UploadSession> {
    return this.request<UploadSession>(`/data/upload/session/${sessionId}`);
  }

  async cancelUpload(sessionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(
      `/data/upload/session/${sessionId}`,
      { method: 'DELETE' }
    );
  }

  // Data Preview Methods
  async getDataPreview(datasetId: number): Promise<DataSourcePreview> {
    // 临时模拟数据以停止无限循环（紧急修复）
    await new Promise(resolve => setTimeout(resolve, 500)); // 模拟网络延迟

    const mockPreview: DataSourcePreview = {
      dataset_id: datasetId,
      rows_count: 1000,
      columns_count: 5,
      columns: [
        {
          column_name: "id",
          column_index: 0,
          data_type: "number",
          is_nullable: false,
          unique_count: 1000,
          missing_count: 0,
          min_value: "1",
          max_value: "1000",
          avg_value: 500.5,
          std_value: 288.67,
          sample_values: ["1", "2", "3", "4", "5"]
        },
        {
          column_name: "name",
          column_index: 1,
          data_type: "string",
          is_nullable: false,
          unique_count: 980,
          missing_count: 0,
          min_value: "3",
          max_value: "25",
          avg_value: 12.5,
          std_value: 4.2,
          sample_values: ["Alice", "Bob", "Charlie", "David", "Eve"]
        }
      ],
      sample_data: [
        { id: 1, name: "Alice", age: 25, city: "New York", score: 95.5 },
        { id: 2, name: "Bob", age: 30, city: "San Francisco", score: 87.2 },
        { id: 3, name: "Charlie", age: 28, city: "Chicago", score: 92.1 }
      ],
      data_types: {
        id: "number",
        name: "string",
        age: "number",
        city: "string",
        score: "number"
      },
      missing_values_summary: {
        id: 0,
        name: 0,
        age: 5,
        city: 2,
        score: 1
      },
      memory_usage: 45600
    };

    return mockPreview;
  }

  async getQualityChecks(datasetId: number): Promise<DataQualityCheck[]> {
    // 临时模拟数据以停止无限循环（紧急修复）
    await new Promise(resolve => setTimeout(resolve, 300)); // 模拟网络延迟

    const mockQuality: DataQualityCheck[] = [
      {
        id: 1,
        dataset_id: datasetId,
        check_type: "missing_values",
        column_name: "age",
        severity: "warning",
        message: "列 \"age\" 有 5 个缺失值 (0.5%)",
        details: {
          missing_count: 5,
          total_count: 1000,
          percentage: 0.5
        },
        affected_rows: 5,
        created_at: new Date().toISOString()
      },
      {
        id: 2,
        dataset_id: datasetId,
        check_type: "duplicates",
        column_name: null,
        severity: "info",
        message: "发现 2 行重复数据 (0.2%)",
        details: {
          duplicate_count: 2,
          total_count: 1000,
          percentage: 0.2
        },
        affected_rows: 2,
        created_at: new Date().toISOString()
      }
    ];

    return mockQuality;
  }

  async triggerAnalysis(datasetId: number): Promise<{ message: string; dataset_id: number }> {
    return this.request<{ message: string; dataset_id: number }>(
      `/data/analyze/${datasetId}`,
      { method: 'POST' }
    );
  }

  // Data Management Methods

  // 获取数据源列表 - 直接调用后端 API
  async getDataSources(): Promise<{ success: boolean; data?: any; message?: string }> {
    try {
      // 调用后端的 /data/sources 端点
      const response = await this.request<any>('/data/sources');
      return {
        success: true,
        data: response
      };
    } catch (error) {
      console.error('获取数据源列表失败:', error);
      return {
        success: false,
        message: error instanceof DataSourceAPIError ? error.detail : 'Failed to fetch data sources'
      };
    }
  }

  // 获取单个数据源详情
  async getDataSource(sourceId: string): Promise<{ success: boolean; data?: any; message?: string }> {
    try {
      const response = await this.request<any>(`/data/sources/${sourceId}`);
      return {
        success: true,
        data: response
      };
    } catch (error) {
      console.error('获取数据源详情失败:', error);
      return {
        success: false,
        message: error instanceof DataSourceAPIError ? error.detail : 'Failed to fetch data source details'
      };
    }
  }

  // 更新数据源
  async updateDataSource(
    sourceId: string,
    data: { name: string; description?: string; type: string }
  ): Promise<{ success: boolean; data?: any; message?: string }> {
    try {
      const response = await this.request<any>(`/data/sources/${sourceId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
      return {
        success: true,
        data: response
      };
    } catch (error) {
      console.error('更新数据源失败:', error);
      return {
        success: false,
        message: error instanceof DataSourceAPIError ? error.detail : 'Failed to update data source'
      };
    }
  }

  // 删除数据源
  async deleteDataSource(sourceId: string): Promise<{ success: boolean; message?: string }> {
    try {
      const response = await this.request<any>(`/data/sources/${sourceId}`, {
        method: 'DELETE',
      });
      return {
        success: true,
        message: response.message || '数据源删除成功'
      };
    } catch (error) {
      console.error('删除数据源失败:', error);
      return {
        success: false,
        message: error instanceof DataSourceAPIError ? error.detail : 'Failed to delete data source'
      };
    }
  }

  // 获取数据统计
  async getDataStats(): Promise<{ success: boolean; data?: any; message?: string }> {
    try {
      const response = await this.request<any>('/data/stats');
      return {
        success: true,
        data: response
      };
    } catch (error) {
      console.error('获取数据统计失败:', error);
      return {
        success: false,
        message: error instanceof DataSourceAPIError ? error.detail : 'Failed to fetch data stats'
      };
    }
  }

  async listDatasets(params: {
    project_id?: number;
    status?: string;
    type?: string;
    page?: number;
    size?: number;
  } = {}): Promise<DataSourceList> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString());
      }
    });

    const endpoint = `/data/preview/datasets${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return this.request<DataSourceList>(endpoint);
  }

  async getDataset(datasetId: number): Promise<DataSource> {
    return this.request<DataSource>(`/data/manage/datasets/${datasetId}`);
  }

  async updateDataset(datasetId: number, data: DataSourceUpdate): Promise<DataSource> {
    return this.request<DataSource>(`/data/manage/datasets/${datasetId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteDataset(datasetId: number): Promise<{ message: string; dataset_id: number }> {
    return this.request<{ message: string; dataset_id: number }>(
      `/data/manage/datasets/${datasetId}`,
      { method: 'DELETE' }
    );
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/data/health');
  }
}

// Export singleton instance
export const dataSourceAPI = new DataSourceAPIClient();
export default dataSourceAPI;