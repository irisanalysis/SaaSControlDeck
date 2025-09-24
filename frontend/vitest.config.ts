/**
 * Vitest configuration for frontend testing
 * Configures test environment, globals, and module resolution
 * RELEVANT FILES: setup.ts, tsconfig.json, vite.config.ts, package.json
 */

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],

  test: {
    // Test environment configuration
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],

    // Global configuration
    globals: true,
    clearMocks: true,
    restoreMocks: true,

    // Test discovery patterns
    include: [
      'tests/**/*.{test,spec}.{js,ts,jsx,tsx}',
      'src/**/*.{test,spec}.{js,ts,jsx,tsx}',
    ],
    exclude: [
      'node_modules',
      'dist',
      '.next',
      'coverage',
      'tests/e2e',
    ],

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'tests/',
        'src/**/*.d.ts',
        'src/**/*.config.*',
        'src/**/*.test.*',
        'src/**/*.spec.*',
        'src/app/layout.tsx',
        'src/app/not-found.tsx',
        'src/app/error.tsx',
        'src/app/loading.tsx',
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80,
        },
        // Stricter thresholds for critical components
        'src/hooks/**': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90,
        },
        'src/lib/api/**': {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85,
        },
      },
    },

    // Test timeout configuration
    testTimeout: 10000,
    hookTimeout: 10000,

    // Test isolation and cleanup
    isolate: true,
    pool: 'threads',

    // Reporter configuration
    reporter: ['verbose', 'json', 'html'],
    outputFile: {
      json: './test-results.json',
      html: './test-results.html',
    },

    // Watch mode configuration
    watch: false,

    // Mock configuration
    deps: {
      inline: [
        '@testing-library/jest-dom',
        '@testing-library/react',
        '@testing-library/user-event',
      ],
    },
  },

  // Resolve configuration for tests
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@/components': resolve(__dirname, './src/components'),
      '@/hooks': resolve(__dirname, './src/hooks'),
      '@/lib': resolve(__dirname, './src/lib'),
      '@/app': resolve(__dirname, './src/app'),
      '@/types': resolve(__dirname, './src/types'),
    },
  },

  // Define environment variables for tests
  define: {
    'process.env.NODE_ENV': '"test"',
    'process.env.NEXT_PUBLIC_API_URL': '"http://localhost:8000"',
  },

  // Optimize dependencies for testing
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@testing-library/react',
      '@testing-library/jest-dom',
      '@testing-library/user-event',
    ],
  },
});