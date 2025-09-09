import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',
  
  // Enable experimental features for performance
  experimental: {
    // Enable Server Components optimization
    serverComponentsExternalPackages: ['@genkit-ai/googleai'],
  },

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

  // Webpack configuration for bundle optimization
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Bundle analyzer in development
    if (process.env.ANALYZE === 'true') {
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
    ignoreBuildErrors: process.env.NODE_ENV === 'production',
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
  
  // SWC minification
  swcMinify: true,
  
  // ESLint during builds
  eslint: {
    // Only run ESLint on specific directories during production builds
    dirs: ['src', 'pages', 'components', 'lib', 'utils'],
  },
};

export default nextConfig;
