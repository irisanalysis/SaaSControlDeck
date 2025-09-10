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
    // Configure path aliases for robust module resolution
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': require('path').resolve(process.cwd(), 'frontend/src'),
      '@/components': require('path').resolve(process.cwd(), 'frontend/src/components'),
      '@/lib': require('path').resolve(process.cwd(), 'frontend/src/lib'),
      '@/hooks': require('path').resolve(process.cwd(), 'frontend/src/hooks'),
      '@/ai': require('path').resolve(process.cwd(), 'frontend/src/ai'),
    };
    
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
