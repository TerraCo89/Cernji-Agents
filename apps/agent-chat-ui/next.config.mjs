/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
  webpack: (config, { isServer }) => {
    if (isServer) {
      // Externalize problematic packages that don't work with webpack
      config.externals.push(
        'elastic-apm-node',
        '@azure/functions-core'
      );
    }
    return config;
  },
};

export default nextConfig;
