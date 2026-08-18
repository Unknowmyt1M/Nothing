/** @type {import('next').NextConfig} */
const backendUrl = process.env.BACKEND_URL;
if (!backendUrl && process.env.NODE_ENV === 'production') {
  console.warn('[next.config.mjs] BACKEND_URL env var is not set. API rewrites will fail.');
}

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const target = backendUrl || 'http://127.0.0.1:3000';
    return [
      {
        source: '/api/:path*',
        destination: `${target}/api/:path*`,
      },
      {
        source: '/api/sse/:path*',
        destination: `${target}/api/sse/:path*`,
      },
    ]
  },
};

export default nextConfig;
