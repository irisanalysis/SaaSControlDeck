# Check if Next.js config needs standalone output
if [ ! -f "frontend/next.config.js" ] && [ ! -f "frontend/next.config.mjs" ]; then
    cat > frontend/next.config.js << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    outputFileTracingRoot: '../'
  }
}

module.exports = nextConfig
EOF
    echo "✅ Created Next.js config with standalone output for Docker"
fi