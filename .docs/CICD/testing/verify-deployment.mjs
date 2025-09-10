#!/usr/bin/env node

/**
 * Vercel Build Simulation Script
 * Simulates the exact steps Vercel takes during deployment
 */

import { execSync } from 'child_process';
import { resolve } from 'path';

const PROJECT_ROOT = resolve(process.cwd());
const FRONTEND_DIR = resolve(PROJECT_ROOT, 'frontend');

console.log('🚀 Simulating Vercel deployment process...');
console.log(`Project root: ${PROJECT_ROOT}`);
console.log(`Frontend directory: ${FRONTEND_DIR}`);

try {
  // Step 1: Install dependencies (simulating Vercel's install command)
  console.log('\n📦 Step 1: Installing dependencies...');
  execSync('npm ci --prefer-offline --no-audit --no-fund', {
    cwd: PROJECT_ROOT,
    stdio: 'inherit'
  });
  console.log('✅ Dependencies installed successfully');

  // Step 2: Build the project (simulating Vercel's build command)
  console.log('\n🔨 Step 2: Building the project...');
  execSync('npm run build', {
    cwd: PROJECT_ROOT,
    stdio: 'inherit'
  });
  console.log('✅ Build completed successfully');

  // Step 3: Verify build output exists
  console.log('\n🔍 Step 3: Verifying build output...');
  execSync('ls -la frontend/.next', {
    cwd: PROJECT_ROOT,
    stdio: 'inherit'
  });
  console.log('✅ Build output verified');

  console.log('\n🎉 Vercel deployment simulation completed successfully!');
  console.log('✅ Ready for actual Vercel deployment');

} catch (error) {
  console.error('❌ Build simulation failed:', error.message);
  process.exit(1);
}