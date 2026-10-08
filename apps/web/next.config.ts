import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable instrumentation for Sentry
  experimental: {
    instrumentationHook: true,
  },
  
  // Sentry webpack plugin configuration
  webpack: (config, { isServer }) => {
    // Sentry source maps upload (only in production)
    if (process.env.NODE_ENV === "production" && process.env.SENTRY_AUTH_TOKEN) {
      config.devtool = "hidden-source-map";
    }
    
    return config;
  },
};

export default nextConfig;
