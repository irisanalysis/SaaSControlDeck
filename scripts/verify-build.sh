#!/bin/bash
set -e

echo "🚀 Verifying Vercel deployment configuration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Error: package.json not found. Please run from project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Pre-flight checks...${NC}"

# Check Node.js version
NODE_VERSION=$(node --version)
echo "✅ Node.js version: $NODE_VERSION"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm ci --prefer-offline --no-audit --no-fund --ignore-scripts
else
    echo "✅ Dependencies already installed"
fi

# Verify package.json scripts
echo -e "${YELLOW}🔍 Verifying build scripts...${NC}"
if npm run-script --silent 2>/dev/null | grep -q "vercel-build"; then
    echo "✅ vercel-build script found"
else
    echo -e "${RED}❌ vercel-build script missing${NC}"
    exit 1
fi

# Set production environment
export NODE_ENV=production
export VERCEL=1
export CI=true
export SKIP_TYPE_CHECK=true

echo -e "${YELLOW}🏗️  Testing build process...${NC}"

# Clean previous build
rm -rf frontend/.next

# Test the build
if npm run vercel-build; then
    echo -e "${GREEN}✅ Build successful!${NC}"
    
    # Check output directory
    if [ -d "frontend/.next" ]; then
        echo -e "${GREEN}✅ Output directory created: frontend/.next${NC}"
        
        # Check build size
        BUILD_SIZE=$(du -sh frontend/.next | cut -f1)
        echo "📊 Build size: $BUILD_SIZE"
        
        # Check for critical files
        if [ -f "frontend/.next/BUILD_ID" ]; then
            echo "✅ Build ID file present"
        fi
        
        if [ -d "frontend/.next/static" ]; then
            echo "✅ Static assets directory present"
        fi
        
        if [ -d "frontend/.next/server" ]; then
            echo "✅ Server directory present"
        fi
        
        echo -e "${GREEN}🎉 Deployment verification successful!${NC}"
        echo -e "${GREEN}📤 Ready for Vercel deployment${NC}"
        
    else
        echo -e "${RED}❌ Build output directory not found${NC}"
        exit 1
    fi
    
else
    echo -e "${RED}❌ Build failed${NC}"
    echo -e "${YELLOW}💡 Check the error messages above for details${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔧 Deployment tips:${NC}"
echo "• Build size should be under 250MB total"
echo "• Large dependencies are cached by Vercel"
echo "• TypeScript errors are skipped in production builds"
echo "• Check Vercel dashboard for deployment logs"
echo ""
echo -e "${GREEN}✅ Local verification complete. Proceed with git push to trigger Vercel deployment.${NC}"