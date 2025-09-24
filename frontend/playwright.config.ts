/**
 * Playwright configuration for end-to-end testing
 * Configures browsers, test settings, and environment for E2E tests
 * RELEVANT FILES: package.json, docker-compose.yml, .env.test
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Test configuration
  testDir: './tests/e2e',
  testMatch: '**/*.e2e.{ts,js}',

  // Global test settings
  timeout: 30000,
  expect: {
    timeout: 10000,
  },

  // Fail build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry settings
  retries: process.env.CI ? 2 : 0,

  // Parallel execution
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/e2e-results.json' }],
    ['junit', { outputFile: 'test-results/e2e-results.xml' }],
    process.env.CI ? ['github'] : ['list'],
  ],

  // Global setup and teardown
  globalSetup: require.resolve('./tests/e2e/global-setup.ts'),
  globalTeardown: require.resolve('./tests/e2e/global-teardown.ts'),

  // Test output directory
  outputDir: 'test-results/e2e',

  // Test artifacts
  use: {
    // Browser settings
    headless: !!process.env.CI,
    viewport: { width: 1280, height: 720 },

    // Context settings
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:9000',

    // Network settings
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
    },

    // Test artifacts
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',

    // Action settings
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  // Project configurations for different browsers and scenarios
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Mobile browsers
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },

    // Authenticated scenarios
    {
      name: 'authenticated-chrome',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'tests/e2e/auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Setup project for authentication
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
      teardown: 'cleanup',
    },

    // Cleanup project
    {
      name: 'cleanup',
      testMatch: /.*\.cleanup\.ts/,
    },

    // API testing
    {
      name: 'api',
      testMatch: /.*\.api\.e2e\.ts/,
      use: {
        baseURL: process.env.API_BASE_URL || 'http://localhost:8000',
      },
    },
  ],

  // Web server configuration
  webServer: [
    // Frontend server
    {
      command: 'npm run dev',
      port: 9000,
      reuseExistingServer: !process.env.CI,
      env: {
        NODE_ENV: 'test',
        NEXT_PUBLIC_API_URL: 'http://localhost:8000',
      },
    },
    // Backend server (if needed)
    {
      command: 'cd ../backend/backend-pro1 && python -m uvicorn data_service.app.main:app --host 0.0.0.0 --port 8001',
      port: 8001,
      reuseExistingServer: !process.env.CI,
      env: {
        TESTING: '1',
        DATABASE_URL: 'sqlite:///test.db',
        REDIS_URL: 'redis://localhost:6379/15',
      },
    },
  ],

  // Test directory organization
  testIgnore: [
    '**/node_modules/**',
    '**/build/**',
    '**/dist/**',
    '**/.next/**',
  ],

  // Metadata
  metadata: {
    'test-environment': 'e2e',
    'application': 'data-source-connection',
    'version': process.env.npm_package_version || 'unknown',
  },
});