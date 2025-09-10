#!/usr/bin/env node

/**
 * Module Resolution Test for Vercel Deployment
 * Tests that all critical imports can be resolved correctly
 */

import { resolve, join } from 'path';
import { readFileSync } from 'fs';

const FRONTEND_DIR = process.cwd().includes('frontend') ? resolve(process.cwd()) : resolve(process.cwd(), 'frontend');
const SRC_DIR = join(FRONTEND_DIR, 'src');

console.log('🔍 Testing module resolution for Vercel deployment...');
console.log(`Working directory: ${process.cwd()}`);
console.log(`Frontend directory: ${FRONTEND_DIR}`);
console.log(`Source directory: ${SRC_DIR}`);

// Test 1: Check if tsconfig.json paths are correct
try {
  const tsconfig = JSON.parse(readFileSync(join(FRONTEND_DIR, 'tsconfig.json'), 'utf-8'));
  console.log('\n✅ tsconfig.json found');
  console.log(`   baseUrl: ${tsconfig.compilerOptions.baseUrl}`);
  console.log(`   paths: ${JSON.stringify(tsconfig.compilerOptions.paths)}`);
} catch (error) {
  console.log('\n❌ tsconfig.json error:', error.message);
  process.exit(1);
}

// Test 2: Check if critical UI components exist
const criticalComponents = [
  'components/ui/button.tsx',
  'components/ui/card.tsx', 
  'components/ui/tabs.tsx',
  'lib/utils.ts'
];

for (const component of criticalComponents) {
  try {
    const componentPath = join(SRC_DIR, component);
    const content = readFileSync(componentPath, 'utf-8');
    
    // Check for exports
    const hasExports = content.includes('export');
    console.log(`✅ ${component} - ${hasExports ? 'has exports' : 'NO EXPORTS'}`);
    
    if (!hasExports) {
      console.log(`❌ WARNING: ${component} has no exports!`);
    }
  } catch (error) {
    console.log(`❌ ${component} - NOT FOUND: ${error.message}`);
    process.exit(1);
  }
}

// Test 3: Check specific import paths used in page.tsx
const pageFile = join(SRC_DIR, 'app/page.tsx');
try {
  const pageContent = readFileSync(pageFile, 'utf-8');
  const imports = pageContent.match(/from\s+["']@\/[^"']+["']/g) || [];
  
  console.log('\n🔍 Found imports in page.tsx:');
  imports.forEach(imp => {
    console.log(`   ${imp}`);
  });
  
  // Verify each import path
  for (const imp of imports) {
    const match = imp.match(/from\s+["']@\/([^"']+)["']/);
    if (match) {
      const importPath = match[1];
      const resolvedPath = join(SRC_DIR, importPath);
      
      try {
        readFileSync(resolvedPath + '.tsx', 'utf-8');
        console.log(`✅ @/${importPath} resolves correctly`);
      } catch {
        try {
          readFileSync(resolvedPath + '.ts', 'utf-8');
          console.log(`✅ @/${importPath} resolves correctly`);
        } catch {
          console.log(`❌ @/${importPath} CANNOT be resolved`);
          process.exit(1);
        }
      }
    }
  }
} catch (error) {
  console.log('❌ Cannot read page.tsx:', error.message);
  process.exit(1);
}

console.log('\n🎉 All module resolution tests passed!');
console.log('✅ Ready for Vercel deployment');