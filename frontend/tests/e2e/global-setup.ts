/**
 * Global setup for Playwright E2E tests
 * Configures test environment, authentication, and data seeding
 * RELEVANT FILES: playwright.config.ts, global-teardown.ts, auth.setup.ts
 */

import { chromium, FullConfig } from '@playwright/test';
import { execSync } from 'child_process';
import path from 'path';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global E2E test setup...');

  // Environment validation
  validateEnvironment();

  // Database setup
  await setupTestDatabase();

  // Service health checks
  await checkServiceHealth();

  // Authentication setup
  await setupAuthentication();

  // Test data seeding
  await seedTestData();

  console.log('✅ Global E2E test setup completed');
}

function validateEnvironment() {
  console.log('📋 Validating test environment...');

  const requiredEnvVars = [
    'E2E_BASE_URL',
    'API_BASE_URL',
  ];

  const missingVars = requiredEnvVars.filter(
    (varName) => !process.env[varName] && !getDefaultValue(varName)
  );

  if (missingVars.length > 0) {
    console.warn(`⚠️  Missing environment variables: ${missingVars.join(', ')}`);
    console.log('Using default values for missing variables');
  }

  // Set defaults
  process.env.E2E_BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:9000';
  process.env.API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

  console.log(`Frontend URL: ${process.env.E2E_BASE_URL}`);
  console.log(`Backend URL: ${process.env.API_BASE_URL}`);
}

function getDefaultValue(varName: string): string | undefined {
  const defaults: Record<string, string> = {
    E2E_BASE_URL: 'http://localhost:9000',
    API_BASE_URL: 'http://localhost:8000',
  };
  return defaults[varName];
}

async function setupTestDatabase() {
  console.log('🗄️  Setting up test database...');

  try {
    // Run database migrations for tests
    const migrationCommand = 'cd ../backend/backend-pro1 && python scripts/apply_migrations.py';
    execSync(migrationCommand, { stdio: 'pipe', env: { ...process.env, TESTING: '1' } });
    console.log('✅ Test database migrations completed');
  } catch (error) {
    console.warn('⚠️  Database migration failed:', error.message);
    console.log('Continuing with existing database state');
  }
}

async function checkServiceHealth() {
  console.log('🏥 Checking service health...');

  const services = [
    { name: 'Frontend', url: process.env.E2E_BASE_URL + '/api/health' },
    { name: 'Backend', url: process.env.API_BASE_URL + '/health' },
  ];

  for (const service of services) {
    try {
      const response = await fetch(service.url);
      if (response.ok) {
        console.log(`✅ ${service.name} service is healthy`);
      } else {
        console.warn(`⚠️  ${service.name} service returned ${response.status}`);
      }
    } catch (error) {
      console.warn(`⚠️  ${service.name} service is not available:`, error.message);
    }
  }
}

async function setupAuthentication() {
  console.log('🔐 Setting up authentication for tests...');

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to login page
    await page.goto(process.env.E2E_BASE_URL + '/login');

    // Check if already authenticated or if login is needed
    const isLoginPage = await page.locator('[data-testid="login-form"]').isVisible().catch(() => false);

    if (isLoginPage) {
      // Perform login for test user
      await page.fill('[data-testid="email-input"]', 'test@example.com');
      await page.fill('[data-testid="password-input"]', 'test123456');
      await page.click('[data-testid="login-button"]');

      // Wait for successful login
      await page.waitForURL('**/dashboard', { timeout: 10000 });
      console.log('✅ Test user authentication completed');
    } else {
      console.log('✅ Authentication not required or already authenticated');
    }

    // Save authentication state
    await context.storageState({ path: 'tests/e2e/auth/user.json' });
  } catch (error) {
    console.warn('⚠️  Authentication setup failed:', error.message);
    console.log('Tests will run without authentication');
  } finally {
    await browser.close();
  }
}

async function seedTestData() {
  console.log('🌱 Seeding test data...');

  try {
    // Create test project
    const testProject = await createTestProject();
    console.log(`✅ Created test project: ${testProject.id}`);

    // Create sample datasets
    const testDatasets = await createTestDatasets(testProject.id);
    console.log(`✅ Created ${testDatasets.length} test datasets`);

    // Store test data references
    await saveTestDataReferences({
      project: testProject,
      datasets: testDatasets,
    });

    console.log('✅ Test data seeding completed');
  } catch (error) {
    console.warn('⚠️  Test data seeding failed:', error.message);
    console.log('Tests will create data as needed');
  }
}

async function createTestProject() {
  const response = await fetch(`${process.env.API_BASE_URL}/api/v1/projects`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getTestAuthToken()}`,
    },
    body: JSON.stringify({
      name: 'E2E Test Project',
      description: 'Project for end-to-end testing',
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create test project: ${response.statusText}`);
  }

  return await response.json();
}

async function createTestDatasets(projectId: number) {
  const datasets = [];

  // Create CSV dataset
  const csvDataset = await createDataset(projectId, 'csv', 'test_data.csv');
  datasets.push(csvDataset);

  // Create JSON dataset
  const jsonDataset = await createDataset(projectId, 'json', 'test_data.json');
  datasets.push(jsonDataset);

  return datasets;
}

async function createDataset(projectId: number, type: string, filename: string) {
  // This would typically upload a test file and create a dataset
  // For now, we'll create a mock dataset
  const response = await fetch(`${process.env.API_BASE_URL}/api/v1/data/datasets`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getTestAuthToken()}`,
    },
    body: JSON.stringify({
      project_id: projectId,
      name: `Test ${type.toUpperCase()} Dataset`,
      type: type,
      filename: filename,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create ${type} dataset: ${response.statusText}`);
  }

  return await response.json();
}

function getTestAuthToken(): string {
  // In a real scenario, this would get the token from authentication
  // For testing, we might use a test token or mock authentication
  return process.env.E2E_TEST_TOKEN || 'test-token';
}

async function saveTestDataReferences(testData: any) {
  const fs = require('fs').promises;
  const testDataPath = path.join(__dirname, 'test-data.json');

  await fs.writeFile(testDataPath, JSON.stringify(testData, null, 2));
}

// Error handling for global setup
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection in global setup:', reason);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception in global setup:', error);
  process.exit(1);
});

export default globalSetup;