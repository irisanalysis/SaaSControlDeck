/**
 * Global teardown for Playwright E2E tests
 * Cleans up test environment, removes test data, and stops services
 * RELEVANT FILES: playwright.config.ts, global-setup.ts, auth.cleanup.ts
 */

import { chromium, FullConfig } from '@playwright/test';
import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs/promises';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global E2E test teardown...');

  // Clean up test data
  await cleanupTestData();

  // Clean up authentication
  await cleanupAuthentication();

  // Clean up test database
  await cleanupTestDatabase();

  // Clean up artifacts
  await cleanupArtifacts();

  // Generate test report summary
  await generateTestSummary();

  console.log('✅ Global E2E test teardown completed');
}

async function cleanupTestData() {
  console.log('🗑️  Cleaning up test data...');

  try {
    // Load test data references
    const testDataPath = path.join(__dirname, 'test-data.json');
    const testDataExists = await fs.access(testDataPath).then(() => true).catch(() => false);

    if (!testDataExists) {
      console.log('📋 No test data file found, skipping cleanup');
      return;
    }

    const testDataContent = await fs.readFile(testDataPath, 'utf-8');
    const testData = JSON.parse(testDataContent);

    // Clean up datasets
    if (testData.datasets && testData.datasets.length > 0) {
      for (const dataset of testData.datasets) {
        await deleteDataset(dataset.id);
      }
      console.log(`✅ Cleaned up ${testData.datasets.length} test datasets`);
    }

    // Clean up project
    if (testData.project) {
      await deleteProject(testData.project.id);
      console.log('✅ Cleaned up test project');
    }

    // Remove test data file
    await fs.unlink(testDataPath);
    console.log('✅ Removed test data references file');

  } catch (error) {
    console.warn('⚠️  Test data cleanup failed:', error.message);
  }
}

async function deleteDataset(datasetId: number) {
  try {
    const response = await fetch(`${process.env.API_BASE_URL}/api/v1/data/datasets/${datasetId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getTestAuthToken()}`,
      },
    });

    if (!response.ok) {
      console.warn(`⚠️  Failed to delete dataset ${datasetId}: ${response.statusText}`);
    }
  } catch (error) {
    console.warn(`⚠️  Error deleting dataset ${datasetId}:`, error.message);
  }
}

async function deleteProject(projectId: number) {
  try {
    const response = await fetch(`${process.env.API_BASE_URL}/api/v1/projects/${projectId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getTestAuthToken()}`,
      },
    });

    if (!response.ok) {
      console.warn(`⚠️  Failed to delete project ${projectId}: ${response.statusText}`);
    }
  } catch (error) {
    console.warn(`⚠️  Error deleting project ${projectId}:`, error.message);
  }
}

async function cleanupAuthentication() {
  console.log('🔐 Cleaning up authentication artifacts...');

  try {
    // Remove authentication state files
    const authFiles = [
      'tests/e2e/auth/user.json',
      'tests/e2e/auth/admin.json',
    ];

    for (const authFile of authFiles) {
      const authFileExists = await fs.access(authFile).then(() => true).catch(() => false);
      if (authFileExists) {
        await fs.unlink(authFile);
        console.log(`✅ Removed auth file: ${authFile}`);
      }
    }

    // Logout any active sessions
    await logoutActiveSessions();

  } catch (error) {
    console.warn('⚠️  Authentication cleanup failed:', error.message);
  }
}

async function logoutActiveSessions() {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to logout endpoint
    await page.goto(process.env.E2E_BASE_URL + '/logout');
    console.log('✅ Logged out active sessions');
  } catch (error) {
    console.warn('⚠️  Session logout failed:', error.message);
  } finally {
    await browser.close();
  }
}

async function cleanupTestDatabase() {
  console.log('🗄️  Cleaning up test database...');

  try {
    // Clean up test database
    const cleanupCommand = 'cd ../backend/backend-pro1 && python scripts/cleanup_test_data.py';

    try {
      execSync(cleanupCommand, {
        stdio: 'pipe',
        env: { ...process.env, TESTING: '1' },
        timeout: 30000 // 30 seconds timeout
      });
      console.log('✅ Test database cleanup completed');
    } catch (commandError) {
      console.warn('⚠️  Database cleanup command failed:', commandError.message);

      // Try alternative cleanup method
      await cleanupDatabaseDirectly();
    }
  } catch (error) {
    console.warn('⚠️  Database cleanup failed:', error.message);
  }
}

async function cleanupDatabaseDirectly() {
  try {
    // Direct database cleanup via API
    const response = await fetch(`${process.env.API_BASE_URL}/api/v1/admin/cleanup-test-data`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getTestAuthToken()}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ confirm: true }),
    });

    if (response.ok) {
      console.log('✅ Direct database cleanup completed');
    } else {
      console.warn(`⚠️  Direct database cleanup failed: ${response.statusText}`);
    }
  } catch (error) {
    console.warn('⚠️  Direct database cleanup error:', error.message);
  }
}

async function cleanupArtifacts() {
  console.log('🧽 Cleaning up test artifacts...');

  try {
    // Clean up temporary files
    const tempDirs = [
      'test-results/temp',
      'tests/e2e/temp',
      'uploads/test',
    ];

    for (const tempDir of tempDirs) {
      try {
        const dirExists = await fs.access(tempDir).then(() => true).catch(() => false);
        if (dirExists) {
          await fs.rmdir(tempDir, { recursive: true });
          console.log(`✅ Cleaned up temp directory: ${tempDir}`);
        }
      } catch (error) {
        console.warn(`⚠️  Failed to clean up ${tempDir}:`, error.message);
      }
    }

    // Clean up old screenshots and videos (keep only recent ones)
    await cleanupOldArtifacts();

  } catch (error) {
    console.warn('⚠️  Artifact cleanup failed:', error.message);
  }
}

async function cleanupOldArtifacts() {
  try {
    const artifactDirs = [
      'test-results/e2e',
      'playwright-report',
    ];

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - 7); // Keep last 7 days

    for (const artifactDir of artifactDirs) {
      try {
        const dirExists = await fs.access(artifactDir).then(() => true).catch(() => false);
        if (!dirExists) continue;

        const files = await fs.readdir(artifactDir, { withFileTypes: true });

        for (const file of files) {
          if (file.isFile()) {
            const filePath = path.join(artifactDir, file.name);
            const stats = await fs.stat(filePath);

            if (stats.mtime < cutoffDate) {
              await fs.unlink(filePath);
              console.log(`✅ Cleaned up old artifact: ${file.name}`);
            }
          }
        }
      } catch (error) {
        console.warn(`⚠️  Failed to clean up old artifacts in ${artifactDir}:`, error.message);
      }
    }
  } catch (error) {
    console.warn('⚠️  Old artifact cleanup failed:', error.message);
  }
}

async function generateTestSummary() {
  console.log('📊 Generating test summary...');

  try {
    // Read test results
    const resultsPath = 'test-results/e2e-results.json';
    const resultsExist = await fs.access(resultsPath).then(() => true).catch(() => false);

    if (!resultsExist) {
      console.log('📋 No test results found, skipping summary generation');
      return;
    }

    const resultsContent = await fs.readFile(resultsPath, 'utf-8');
    const results = JSON.parse(resultsContent);

    // Generate summary
    const summary = {
      timestamp: new Date().toISOString(),
      total: results.suites?.reduce((acc, suite) => acc + suite.tests?.length || 0, 0) || 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      duration: 0,
    };

    // Calculate statistics
    if (results.suites) {
      for (const suite of results.suites) {
        if (suite.tests) {
          for (const test of suite.tests) {
            switch (test.outcome) {
              case 'passed':
                summary.passed++;
                break;
              case 'failed':
                summary.failed++;
                break;
              case 'skipped':
                summary.skipped++;
                break;
            }
            summary.duration += test.duration || 0;
          }
        }
      }
    }

    // Save summary
    const summaryPath = 'test-results/e2e-summary.json';
    await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2));

    // Log summary
    console.log('📈 Test Summary:');
    console.log(`   Total: ${summary.total}`);
    console.log(`   Passed: ${summary.passed}`);
    console.log(`   Failed: ${summary.failed}`);
    console.log(`   Skipped: ${summary.skipped}`);
    console.log(`   Duration: ${(summary.duration / 1000).toFixed(2)}s`);

    console.log('✅ Test summary generated');

  } catch (error) {
    console.warn('⚠️  Test summary generation failed:', error.message);
  }
}

function getTestAuthToken(): string {
  return process.env.E2E_TEST_TOKEN || 'test-token';
}

// Error handling for global teardown
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection in global teardown:', reason);
  // Don't exit on teardown errors to ensure cleanup continues
});

process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception in global teardown:', error);
  // Don't exit on teardown errors to ensure cleanup continues
});

export default globalTeardown;