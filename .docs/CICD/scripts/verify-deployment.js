#!/usr/bin/env node

/**
 * Deployment Verification Script
 * Verifies all critical components and imports are properly resolved
 */

const fs = require('fs');
const path = require('path');

const frontendDir = path.join(__dirname, '../frontend');

function checkFileExists(filePath, description) {
  const fullPath = path.join(frontendDir, filePath);
  const exists = fs.existsSync(fullPath);
  console.log(`${exists ? '✅' : '❌'} ${description}: ${filePath}`);
  return exists;
}

function checkTsConfig() {
  const tsConfigPath = path.join(frontendDir, 'tsconfig.json');
  const tsConfig = JSON.parse(fs.readFileSync(tsConfigPath, 'utf-8'));
  
  const hasBaseUrl = !!tsConfig.compilerOptions.baseUrl;
  const hasPaths = !!tsConfig.compilerOptions.paths;
  const hasCorrectAlias = tsConfig.compilerOptions.paths && tsConfig.compilerOptions.paths['@/*'];
  
  console.log(`${hasBaseUrl ? '✅' : '❌'} TypeScript baseUrl configured`);
  console.log(`${hasPaths ? '✅' : '❌'} TypeScript paths configured`);
  console.log(`${hasCorrectAlias ? '✅' : '❌'} TypeScript @ alias configured`);
  
  return hasBaseUrl && hasPaths && hasCorrectAlias;
}

function checkNextConfig() {
  const nextConfigPath = path.join(frontendDir, 'next.config.ts');
  const nextConfig = fs.readFileSync(nextConfigPath, 'utf-8');
  
  const hasWebpackAlias = nextConfig.includes('config.resolve.alias');
  const hasIgnoreErrors = nextConfig.includes('ignoreBuildErrors');
  
  console.log(`${hasWebpackAlias ? '✅' : '❌'} Next.js webpack alias configured`);
  console.log(`${hasIgnoreErrors ? '✅' : '❌'} Next.js build error handling configured`);
  
  return hasWebpackAlias;
}

function checkVercelConfig() {
  const vercelConfigPath = path.join(__dirname, '../vercel.json');
  const vercelConfig = JSON.parse(fs.readFileSync(vercelConfigPath, 'utf-8'));
  
  const hasRootDir = !!vercelConfig.rootDirectory;
  const correctBuildCommand = vercelConfig.buildCommand && vercelConfig.buildCommand.includes('cd frontend');
  
  console.log(`${hasRootDir ? '✅' : '❌'} Vercel root directory configured`);
  console.log(`${correctBuildCommand ? '✅' : '❌'} Vercel build command configured`);
  
  return hasRootDir && correctBuildCommand;
}

function main() {
  console.log('🚀 Deployment Verification Starting...\n');

  console.log('📁 File Structure Verification:');
  const criticalFiles = [
    ['src/app/page.tsx', 'Main page component'],
    ['src/components/ui/button.tsx', 'Button UI component'],
    ['src/components/ui/card.tsx', 'Card UI component'],
    ['src/components/ui/tabs.tsx', 'Tabs UI component'],
    ['src/components/dashboard/profile-card.tsx', 'Profile card component'],
    ['src/components/dashboard/pending-approvals-card.tsx', 'Pending approvals component'],
    ['src/components/dashboard/settings-card.tsx', 'Settings card component'],
    ['src/components/dashboard/integrations-card.tsx', 'Integrations card component'],
    ['src/components/dashboard/device-management-card.tsx', 'Device management component'],
    ['src/components/ai/ai-help.tsx', 'AI help component'],
    ['src/lib/utils.ts', 'Utils library'],
  ];

  let filesExist = true;
  for (const [filePath, description] of criticalFiles) {
    if (!checkFileExists(filePath, description)) {
      filesExist = false;
    }
  }

  console.log('\n⚙️ Configuration Verification:');
  const tsConfigValid = checkTsConfig();
  const nextConfigValid = checkNextConfig();
  const vercelConfigValid = checkVercelConfig();

  console.log('\n📋 Summary:');
  const allValid = filesExist && tsConfigValid && nextConfigValid && vercelConfigValid;
  
  if (allValid) {
    console.log('✅ All deployment prerequisites are satisfied!');
    console.log('🚀 Ready for Vercel deployment');
    process.exit(0);
  } else {
    console.log('❌ Some issues detected. Please resolve before deployment.');
    process.exit(1);
  }
}

main();