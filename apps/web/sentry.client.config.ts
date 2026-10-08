/**
 * Sentry Client Configuration for Next.js
 * 
 * This file configures error tracking and performance monitoring
 * for the browser/client-side of the application.
 */

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  
  // Environment (development, staging, production)
  environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development",
  
  // Performance Monitoring
  tracesSampleRate: parseFloat(
    process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"
  ),
  
  // Session Replay
  replaysSessionSampleRate: parseFloat(
    process.env.NEXT_PUBLIC_SENTRY_REPLAYS_SESSION_SAMPLE_RATE || "0.1"
  ),
  replaysOnErrorSampleRate: parseFloat(
    process.env.NEXT_PUBLIC_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE || "1.0"
  ),
  
  // Don't send errors in development
  enabled: process.env.NODE_ENV === "production",
  
  // Release tracking (auto-populated by Vercel)
  release: process.env.VERCEL_GIT_COMMIT_SHA,
  
  // Ignore common browser errors that we can't control
  ignoreErrors: [
    // Browser extensions
    "top.GLOBALS",
    "chrome-extension://",
    "moz-extension://",
    // Network errors
    "NetworkError",
    "Failed to fetch",
    // React hydration mismatches (handled by Next.js)
    "Minified React error",
  ],
  
  // Filter sensitive data from breadcrumbs
  beforeBreadcrumb(breadcrumb) {
    // Don't log clicks on password fields
    if (breadcrumb.category === "ui.click") {
      const target = breadcrumb.message;
      if (target?.includes("password") || target?.includes("secret")) {
        return null;
      }
    }
    return breadcrumb;
  },
  
  // Filter sensitive data from events
  beforeSend(event, hint) {
    // Remove sensitive data from request URLs
    if (event.request?.url) {
      try {
        const url = new URL(event.request.url);
        // Remove query parameters that might contain tokens
        if (url.searchParams.has("token")) url.searchParams.delete("token");
        if (url.searchParams.has("key")) url.searchParams.delete("key");
        event.request.url = url.toString();
      } catch (e) {
        // Invalid URL, skip sanitization
      }
    }
    
    return event;
  },
});
