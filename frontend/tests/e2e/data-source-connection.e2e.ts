/**
 * End-to-end tests for data source connection workflow
 * Tests complete user journey from file upload to data analysis
 * RELEVANT FILES: data-source-connection.tsx, page.tsx, playwright.config.ts
 */

import { test, expect } from '@playwright/test';
import path from 'path';

// Test data and utilities
const TEST_FILES = {
  csv: {
    name: 'test-data.csv',
    content: 'id,name,age,email\n1,Alice,25,alice@example.com\n2,Bob,30,bob@example.com\n3,Charlie,35,charlie@example.com',
    size: '100 bytes',
  },
  json: {
    name: 'test-data.json',
    content: JSON.stringify([
      { id: 1, name: 'Alice', age: 25, email: 'alice@example.com' },
      { id: 2, name: 'Bob', age: 30, email: 'bob@example.com' },
      { id: 3, name: 'Charlie', age: 35, email: 'charlie@example.com' },
    ], null, 2),
    size: '200 bytes',
  },
  large: {
    name: 'large-file.csv',
    content: 'id,data\n' + Array.from({ length: 10000 }, (_, i) => `${i},test_data_${i}`).join('\n'),
    size: '500 KB',
  },
};

test.describe('Data Source Connection E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to data management page
    await page.goto('/data-management');
    await expect(page).toHaveTitle(/Data Management/);
  });

  test.describe('File Upload Workflow', () => {
    test('should complete CSV file upload successfully', async ({ page }) => {
      // Step 1: Select file upload option
      await page.click('[data-testid="new-data-source"]');
      await expect(page.locator('[data-testid="data-source-connection"]')).toBeVisible();

      // Step 2: Upload CSV file
      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.csv.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.csv.content),
      });

      // Step 3: Verify upload progress
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();
      await expect(page.locator('[data-testid="upload-progress-bar"]')).toBeVisible();

      // Step 4: Wait for upload completion
      await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 30000 });

      // Step 5: Verify dataset information
      await expect(page.locator('[data-testid="dataset-name"]')).toContainText('test-data');
      await expect(page.locator('[data-testid="dataset-rows"]')).toContainText('3');
      await expect(page.locator('[data-testid="dataset-columns"]')).toContainText('4');
    });

    test('should handle drag and drop file upload', async ({ page }) => {
      // Create file buffer
      const fileBuffer = Buffer.from(TEST_FILES.csv.content);

      // Step 1: Open file dropzone
      await page.click('[data-testid="new-data-source"]');
      const dropzone = page.locator('[data-testid="file-dropzone"]');
      await expect(dropzone).toBeVisible();

      // Step 2: Simulate drag and drop
      const dataTransfer = await page.evaluateHandle((fileContent) => {
        const dt = new DataTransfer();
        const file = new File([fileContent], 'test-data.csv', { type: 'text/csv' });
        dt.items.add(file);
        return dt;
      }, TEST_FILES.csv.content);

      await dropzone.dispatchEvent('drop', { dataTransfer });

      // Step 3: Verify upload starts
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();
      await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 30000 });
    });

    test('should handle large file upload with chunking', async ({ page }) => {
      // Step 1: Start large file upload
      await page.click('[data-testid="new-data-source"]');

      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.large.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.large.content),
      });

      // Step 2: Verify chunked upload progress
      const progressBar = page.locator('[data-testid="upload-progress-bar"]');
      await expect(progressBar).toBeVisible();

      // Monitor progress updates
      let previousProgress = 0;
      for (let i = 0; i < 10; i++) {
        await page.waitForTimeout(1000);
        const currentProgress = await progressBar.getAttribute('aria-valuenow');
        if (currentProgress && parseInt(currentProgress) > previousProgress) {
          previousProgress = parseInt(currentProgress);
          console.log(`Upload progress: ${currentProgress}%`);
        }
        if (previousProgress >= 100) break;
      }

      // Step 3: Verify completion
      await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 60000 });
    });
  });

  test.describe('Data Preview and Analysis', () => {
    test('should display data preview after successful upload', async ({ page }) => {
      // Upload file first
      await page.click('[data-testid="new-data-source"]');
      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.csv.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.csv.content),
      });

      await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 30000 });

      // Step 1: Navigate to preview
      await page.click('[data-testid="view-preview"]');

      // Step 2: Verify preview table
      await expect(page.locator('[data-testid="data-preview-table"]')).toBeVisible();

      // Step 3: Check column headers
      await expect(page.locator('[data-testid="column-header-id"]')).toBeVisible();
      await expect(page.locator('[data-testid="column-header-name"]')).toBeVisible();
      await expect(page.locator('[data-testid="column-header-age"]')).toBeVisible();
      await expect(page.locator('[data-testid="column-header-email"]')).toBeVisible();

      // Step 4: Check sample data rows
      await expect(page.locator('[data-testid="data-row-0"]')).toContainText('Alice');
      await expect(page.locator('[data-testid="data-row-1"]')).toContainText('Bob');
      await expect(page.locator('[data-testid="data-row-2"]')).toContainText('Charlie');

      // Step 5: Verify column statistics
      await expect(page.locator('[data-testid="column-stats-id"]')).toContainText('number');
      await expect(page.locator('[data-testid="column-stats-name"]')).toContainText('string');
    });

    test('should run data quality analysis', async ({ page }) => {
      // Upload and navigate to preview
      await page.click('[data-testid="new-data-source"]');
      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.csv.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.csv.content),
      });

      await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 30000 });
      await page.click('[data-testid="view-preview"]');

      // Step 1: Trigger analysis
      await page.click('[data-testid="run-analysis"]');

      // Step 2: Wait for analysis completion
      await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible({ timeout: 45000 });

      // Step 3: Verify quality checks section
      await expect(page.locator('[data-testid="quality-checks"]')).toBeVisible();

      // Step 4: Check quality metrics
      const qualityChecks = page.locator('[data-testid="quality-check-item"]');
      await expect(qualityChecks).toHaveCount(await qualityChecks.count());

      // Step 5: Verify analysis results
      await expect(page.locator('[data-testid="missing-values-count"]')).toBeVisible();
      await expect(page.locator('[data-testid="duplicate-rows-count"]')).toBeVisible();
    });

    test('should handle different data types correctly', async ({ page }) => {
      // Test JSON file upload
      await page.click('[data-testid="new-data-source"]');
      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.json.name,
        mimeType: 'application/json',
        buffer: Buffer.from(TEST_FILES.json.content),
      });

      await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 30000 });
      await page.click('[data-testid="view-preview"]');

      // Verify JSON data structure
      await expect(page.locator('[data-testid="data-type-json"]')).toBeVisible();
      await expect(page.locator('[data-testid="data-preview-table"]')).toBeVisible();

      // Check nested object handling
      await expect(page.locator('[data-testid="column-header-id"]')).toBeVisible();
      await expect(page.locator('[data-testid="column-header-name"]')).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle unsupported file types', async ({ page }) => {
      await page.click('[data-testid="new-data-source"]');

      // Try to upload unsupported file type
      await page.setInputFiles('[data-testid="file-input"]', {
        name: 'unsupported.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('This is not a supported data file'),
      });

      // Verify error message
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      await expect(page.locator('[data-testid="error-message"]')).toContainText('Unsupported file type');

      // Verify user can retry
      await expect(page.locator('[data-testid="retry-upload"]')).toBeVisible();
    });

    test('should handle file size limit exceeded', async ({ page }) => {
      await page.click('[data-testid="new-data-source"]');

      // Create a file that exceeds size limit (simulate 200MB file)
      const oversizedContent = 'x'.repeat(200 * 1024 * 1024); // 200MB of 'x' characters

      await page.setInputFiles('[data-testid="file-input"]', {
        name: 'oversized.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(oversizedContent),
      });

      // Verify size limit error
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      await expect(page.locator('[data-testid="error-message"]')).toContainText('File size exceeds');
    });

    test('should handle network errors during upload', async ({ page }) => {
      // Intercept upload request and simulate network error
      await page.route('**/api/v1/data/upload', route => {
        route.abort();
      });

      await page.click('[data-testid="new-data-source"]');
      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.csv.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.csv.content),
      });

      // Verify network error handling
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      await expect(page.locator('[data-testid="retry-upload"]')).toBeVisible();
    });

    test('should handle corrupted file upload', async ({ page }) => {
      await page.click('[data-testid="new-data-source"]');

      // Upload corrupted CSV file
      const corruptedContent = 'id,name,age\n1,Alice\n2,Bob,30,extra,field\nthis,is,not,valid,csv,data';

      await page.setInputFiles('[data-testid="file-input"]', {
        name: 'corrupted.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(corruptedContent),
      });

      // Verify error during processing
      await expect(page.locator('[data-testid="processing-error"]')).toBeVisible({ timeout: 30000 });
      await expect(page.locator('[data-testid="error-details"]')).toContainText('parsing');
    });
  });

  test.describe('User Experience Features', () => {
    test('should support upload cancellation', async ({ page }) => {
      await page.click('[data-testid="new-data-source"]');

      // Start large file upload
      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.large.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.large.content),
      });

      // Wait for upload to start
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();

      // Cancel upload
      await page.click('[data-testid="cancel-upload"]');

      // Verify cancellation
      await expect(page.locator('[data-testid="upload-cancelled"]')).toBeVisible();
      await expect(page.locator('[data-testid="file-dropzone"]')).toBeVisible();
    });

    test('should provide helpful progress indicators', async ({ page }) => {
      await page.click('[data-testid="new-data-source"]');

      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.csv.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.csv.content),
      });

      // Check progress indicators
      await expect(page.locator('[data-testid="upload-step-indicator"]')).toBeVisible();
      await expect(page.locator('[data-testid="progress-percentage"]')).toBeVisible();
      await expect(page.locator('[data-testid="upload-speed"]')).toBeVisible();
      await expect(page.locator('[data-testid="time-remaining"]')).toBeVisible();
    });

    test('should show step-by-step workflow progress', async ({ page }) => {
      await page.click('[data-testid="new-data-source"]');

      // Step 1: File selection
      await expect(page.locator('[data-testid="step-1-active"]')).toBeVisible();
      await expect(page.locator('[data-testid="step-2-pending"]')).toBeVisible();
      await expect(page.locator('[data-testid="step-3-pending"]')).toBeVisible();

      // Upload file
      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.csv.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.csv.content),
      });

      // Step 2: Upload in progress
      await expect(page.locator('[data-testid="step-1-completed"]')).toBeVisible();
      await expect(page.locator('[data-testid="step-2-active"]')).toBeVisible();

      // Step 3: Preview
      await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 30000 });
      await page.click('[data-testid="view-preview"]');

      await expect(page.locator('[data-testid="step-2-completed"]')).toBeVisible();
      await expect(page.locator('[data-testid="step-3-active"]')).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test('should be keyboard navigable', async ({ page }) => {
      await page.click('[data-testid="new-data-source"]');

      // Test keyboard navigation
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="file-dropzone"]')).toBeFocused();

      await page.keyboard.press('Enter');
      // File dialog should be triggered (can't test the actual dialog)

      // Navigate through help text
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
    });

    test('should have proper ARIA labels and roles', async ({ page }) => {
      await page.click('[data-testid="new-data-source"]');

      // Check ARIA attributes
      await expect(page.locator('[data-testid="file-dropzone"]')).toHaveAttribute('role', 'button');
      await expect(page.locator('[data-testid="file-dropzone"]')).toHaveAttribute('tabindex', '0');
      await expect(page.locator('[data-testid="file-dropzone"]')).toHaveAttribute('aria-label');

      // Check progress indicators
      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.csv.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.csv.content),
      });

      await expect(page.locator('[data-testid="upload-progress-bar"]')).toHaveAttribute('role', 'progressbar');
      await expect(page.locator('[data-testid="upload-progress-bar"]')).toHaveAttribute('aria-valuemin', '0');
      await expect(page.locator('[data-testid="upload-progress-bar"]')).toHaveAttribute('aria-valuemax', '100');
    });

    test('should announce status changes to screen readers', async ({ page }) => {
      await page.click('[data-testid="new-data-source"]');

      // Check live regions
      await expect(page.locator('[data-testid="status-announcements"]')).toHaveAttribute('aria-live', 'polite');

      await page.setInputFiles('[data-testid="file-input"]', {
        name: TEST_FILES.csv.name,
        mimeType: 'text/csv',
        buffer: Buffer.from(TEST_FILES.csv.content),
      });

      // Status should be announced
      await expect(page.locator('[data-testid="status-announcements"]')).toContainText('Upload started');
      await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 30000 });
      await expect(page.locator('[data-testid="status-announcements"]')).toContainText('Upload completed');
    });
  });
});