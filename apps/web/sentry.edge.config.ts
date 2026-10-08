/**
 * Sentry Edge Configuration for Next.js
 * 
 * This file configures error tracking for Next.js edge runtime
 * (middleware, edge API routes, edge functions).
 */

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  
  // Environment (development, staging, production)
  environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development",
  
  // Performance Monitoring (lower sample rate for edge)
  tracesSampleRate: parseFloat(
    process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"
  ),
  
  // Don't send errors in development
  enabled: process.env.NODE_ENV === "production",
  
  // Release tracking (auto-populated by Vercel)
  release: process.env.VERCEL_GIT_COMMIT_SHA,
  
  // Don't send default PII
  sendDefaultPii: false,
});
