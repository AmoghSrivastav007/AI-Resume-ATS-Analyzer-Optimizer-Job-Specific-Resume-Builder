/**
 * Sentry Server Configuration for Next.js
 * 
 * This file configures error tracking and performance monitoring
 * for the server-side/API routes of the Next.js application.
 */

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  
  // Environment (development, staging, production)
  environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development",
  
  // Performance Monitoring (lower sample rate for server)
  tracesSampleRate: parseFloat(
    process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"
  ),
  
  // Don't send errors in development
  enabled: process.env.NODE_ENV === "production",
  
  // Release tracking (auto-populated by Vercel)
  release: process.env.VERCEL_GIT_COMMIT_SHA,
  
  // Don't send default PII (personally identifiable information)
  sendDefaultPii: false,
  
  // Filter sensitive data from events
  beforeSend(event) {
    // Remove sensitive environment variables from context
    if (event.contexts?.runtime?.name === "node") {
      delete event.contexts.runtime;
    }
    
    // Remove Authorization headers
    if (event.request?.headers) {
      delete event.request.headers["authorization"];
      delete event.request.headers["cookie"];
    }
    
    return event;
  },
});
