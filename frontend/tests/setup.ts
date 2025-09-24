/**
 * Test setup configuration for React Testing Library and Vitest
 * Configures global test environment, mocks, and utilities
 */

import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { configure } from '@testing-library/react';

// Configure Testing Library
configure({
  testIdAttribute: 'data-testid',
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock File API
global.File = class MockFile {
  constructor(
    public fileBits: BlobPart[],
    public fileName: string,
    public options?: FilePropertyBag
  ) {
    this.name = fileName;
    this.size = fileBits.reduce((size, bit) => {
      if (typeof bit === 'string') return size + bit.length;
      if (bit instanceof ArrayBuffer) return size + bit.byteLength;
      return size + (bit as Blob).size;
    }, 0);
    this.type = options?.type || '';
    this.lastModified = options?.lastModified || Date.now();
  }

  name: string;
  size: number;
  type: string;
  lastModified: number;

  slice() {
    return new Blob();
  }

  stream() {
    return new ReadableStream();
  }

  text() {
    return Promise.resolve('');
  }

  arrayBuffer() {
    return Promise.resolve(new ArrayBuffer(0));
  }
};

// Mock FileReader
global.FileReader = class MockFileReader {
  result: string | ArrayBuffer | null = null;
  error: DOMException | null = null;
  readyState: number = 0;
  onload: ((ev: ProgressEvent<FileReader>) => any) | null = null;
  onerror: ((ev: ProgressEvent<FileReader>) => any) | null = null;
  onprogress: ((ev: ProgressEvent<FileReader>) => any) | null = null;

  readAsText(file: Blob) {
    setTimeout(() => {
      this.result = 'mocked file content';
      this.readyState = 2;
      if (this.onload) {
        this.onload(new ProgressEvent('load'));
      }
    }, 10);
  }

  readAsDataURL(file: Blob) {
    setTimeout(() => {
      this.result = 'data:text/plain;base64,bW9ja2VkIGZpbGUgY29udGVudA==';
      this.readyState = 2;
      if (this.onload) {
        this.onload(new ProgressEvent('load'));
      }
    }, 10);
  }

  abort() {
    this.readyState = 2;
  }

  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() {
    return true;
  }
};

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mocked-object-url');
global.URL.revokeObjectURL = vi.fn();

// Mock toast function
vi.mock('@/hooks/use-toast', () => ({
  toast: vi.fn(),
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock Lucide React icons
vi.mock('lucide-react', () => {
  const MockIcon = ({ className, ...props }: any) => {
    return {
      type: 'svg',
      props: {
        className,
        ...props,
        'data-testid': 'mock-icon'
      }
    };
  };

  return new Proxy(
    {},
    {
      get: () => MockIcon,
    }
  );
});

// Global test utilities
global.createMockFile = (
  name: string,
  content: string = 'test content',
  type: string = 'text/plain'
): File => {
  return new File([content], name, { type });
};

global.createMockFileList = (files: File[]): FileList => {
  const fileList = {
    length: files.length,
    item: (index: number) => files[index] || null,
    ...files,
  };
  return fileList as FileList;
};

// Mock data for tests
export const mockDataSource = {
  id: 1,
  project_id: 1,
  name: 'Test Dataset',
  type: 'csv' as const,
  file_path: '/tmp/test.csv',
  file_size: 1024,
  rows_count: 100,
  columns_count: 5,
  status: 'ready' as const,
  original_filename: 'test.csv',
  mime_type: 'text/csv',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const mockDataPreview = {
  dataset_id: 1,
  rows_count: 100,
  columns_count: 5,
  columns: [
    {
      column_name: 'id',
      column_index: 0,
      data_type: 'number',
      is_nullable: false,
      unique_count: 100,
      missing_count: 0,
      sample_values: ['1', '2', '3', '4', '5'],
    },
    {
      column_name: 'name',
      column_index: 1,
      data_type: 'string',
      is_nullable: false,
      unique_count: 100,
      missing_count: 0,
      sample_values: ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    },
  ],
  sample_data: [
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' },
    { id: 3, name: 'Charlie' },
  ],
  data_types: { id: 'int64', name: 'object' },
  missing_values_summary: { id: 0, name: 0 },
  memory_usage: 1024,
};

export const mockUploadSession = {
  id: 'session-123',
  user_id: 1,
  project_id: 1,
  filename: 'test.csv',
  file_size: 1024,
  uploaded_size: 512,
  chunk_size: 256,
  total_chunks: 4,
  uploaded_chunks: 2,
  status: 'uploading' as const,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  progress_percentage: 50,
};

// Console spy setup for testing
const originalConsoleError = console.error;
beforeEach(() => {
  console.error = vi.fn();
});

afterEach(() => {
  console.error = originalConsoleError;
  vi.clearAllMocks();
});