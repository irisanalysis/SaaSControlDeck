import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  // Remove standalone output for Vercel deployment
  // output: 'standalone',  // Commented out for Vercel compatibility
  
  // Server external packages for Server Components optimization
  serverExternalPackages: ['@genkit-ai/googleai'],

  // Environment variables
  env: {
    NEXT_PUBLIC_APP_NAME: 'SaaS Control Deck',
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version || '1.0.0',
  },

  // Build configuration
  generateBuildId: async () => {
    // Use git commit hash or timestamp for build ID
    return process.env.GIT_COMMIT || `build-${Date.now()}`;
  },


  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
      {
        source: '/api/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
        ],
      },
    ];
  },

  // Rewrites for API proxying
  async rewrites() {
    return [
      {
        source: '/api/pro1/:path*',
        destination: `${process.env.BACKEND_PRO1_URL || 'http://localhost:8000'}/:path*`,
      },
      {
        source: '/api/pro2/:path*',
        destination: `${process.env.BACKEND_PRO2_URL || 'http://localhost:8100'}/:path*`,
      },
    ];
  },

  // TypeScript configuration
  typescript: {
    // Type checking is handled by separate CI step in production
    ignoreBuildErrors: process.env.NODE_ENV === 'production' || process.env.VERCEL === '1',
  },
  
  // Experimental features for faster builds - disabled for stability
  // experimental: {
  //   optimizeCss: true,
  //   forceSwcTransforms: true,
  // },
  
  // Webpack optimization for Vercel
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    const path = require('path');
    const fs = require('fs');
    
    // Robust path resolution for both monorepo and standalone scenarios
    const srcPath = (() => {
      const cwd = process.cwd();
      
      // Strategy 1: Check if we have src directory in current working directory
      const cwdSrc = path.join(cwd, 'src');
      if (fs.existsSync(cwdSrc)) {
        return cwdSrc;
      }
      
      // Strategy 2: Check if we're in a subdirectory and need to go up
      const parentSrc = path.resolve(cwd, '../src');
      if (fs.existsSync(parentSrc)) {
        return parentSrc;
      }
      
      // Strategy 3: Check for frontend/src pattern
      const frontendSrc = path.join(cwd, 'frontend/src');
      if (fs.existsSync(frontendSrc)) {
        return frontendSrc;
      }
      
      // Strategy 4: Check if we're already in frontend and need to find src
      if (cwd.includes('frontend')) {
        const srcInFrontend = path.join(cwd, 'src');
        if (fs.existsSync(srcInFrontend)) {
          return srcInFrontend;
        }
      }
      
      // Fallback: assume current directory structure
      return path.resolve(cwd, 'src');
    })();
    
    // Ensure all critical paths exist
    const requiredPaths = {
      components: path.join(srcPath, 'components'),
      lib: path.join(srcPath, 'lib'), 
      hooks: path.join(srcPath, 'hooks'),
      ai: path.join(srcPath, 'ai')
    };
    
    // Validate path structure
    const pathsExist = Object.entries(requiredPaths).map(([key, dir]) => {
      const exists = fs.existsSync(dir);
      return { key, dir, exists };
    });
    
    // Debug information for troubleshooting
    const isDebugMode = process.env.NODE_ENV !== 'production' || process.env.DEBUG_MODULE_RESOLUTION || process.env.VERCEL;
    
    if (isDebugMode) {
      console.log('\n🔧 NEXT.JS WEBPACK MODULE RESOLUTION DEBUG');
      console.log('Environment:', {
        NODE_ENV: process.env.NODE_ENV,
        VERCEL: process.env.VERCEL,
        cwd: process.cwd(),
        srcPath
      });
      
      console.log('Path validation:');
      pathsExist.forEach(({ key, dir, exists }) => {
        console.log(`  📁 ${key}: ${exists ? '✅' : '❌'} ${dir}`);
      });
      
      // Test critical component imports
      const criticalComponents = [
        'components/ui/button.tsx',
        'components/ui/tabs.tsx', 
        'components/dashboard/profile-card.tsx',
        'components/dashboard/pending-approvals-card.tsx',
        'lib/utils.ts'
      ];
      
      console.log('Component resolution test:');
      criticalComponents.forEach(comp => {
        const fullPath = path.join(srcPath, comp);
        const exists = fs.existsSync(fullPath);
        console.log(`  📦 ${comp}: ${exists ? '✅ FOUND' : '❌ MISSING'} ${fullPath}`);
      });
    }
    
    // Configure robust path aliases
    const aliases = {
      '@': srcPath,
      '@/components': requiredPaths.components,
      '@/lib': requiredPaths.lib,
      '@/hooks': requiredPaths.hooks,
      '@/ai': requiredPaths.ai
    };
    
    config.resolve.alias = {
      ...config.resolve.alias,
      ...aliases
    };
    
    // Ensure module resolution can find dependencies in both local and parent node_modules
    config.resolve.modules = [
      path.join(process.cwd(), 'node_modules'),
      path.resolve(process.cwd(), '../node_modules'),
      'node_modules'
    ];
    
    if (isDebugMode) {
      console.log('Webpack aliases configured:');
      Object.entries(aliases).forEach(([alias, path]) => {
        console.log(`  🔗 ${alias} → ${path}`);
      });
      console.log('Module resolution paths:', config.resolve.modules);
      console.log('=== END DEBUG ===\n');
    }
    
    // Ignore handlebars warnings from Genkit
    config.ignoreWarnings = [
      /require\.extensions is not supported by webpack/,
      /Cannot resolve module 'critters'/
    ];
    
    // Bundle analyzer in development only
    if (process.env.ANALYZE === 'true' && !process.env.VERCEL) {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          openAnalyzer: false,
          reportFilename: isServer ? '../analyze/server.html' : './analyze/client.html',
        })
      );
    }

    return config;
  },
  
  // Image optimization
  images: {
    domains: ['cdn.saascontroldeck.com'],
    formats: ['image/webp', 'image/avif'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'picsum.photos',
        port: '',
        pathname: '/**',
      },
    ],
  },

  // Compression
  compress: true,
  
  // Power by header
  poweredByHeader: false,
  
  // React strict mode
  reactStrictMode: true,
  
  // SWC minification (default in Next.js 13+)
  // swcMinify: true, // Removed as it's default
  
  // ESLint during builds
  eslint: {
    // Only run ESLint on specific directories during production builds
    dirs: ['src', 'pages', 'components', 'lib', 'utils'],
  },
};

export default nextConfig;
