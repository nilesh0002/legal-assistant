/**
 * Single API Configuration for NyayaSahayak Web App.
 * Production deployments must use HTTPS. Local development permits http://localhost or http://127.0.0.1.
 */

export const DEFAULT_PRODUCTION_API_URL = 'https://legal-assistant-1qgm.onrender.com';
export const MAX_QUESTION_LENGTH = 1000;
export const WAKEUP_THRESHOLD_MS = 8000;
export const REQUEST_TIMEOUT_MS = 60000;

export function isLocalHostOrigin(hostname) {
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]';
}

export function normalizeBaseUrl(rawUrl) {
  if (!rawUrl || typeof rawUrl !== 'string') return '';
  return rawUrl.trim().replace(/\/+$/, '');
}

export function validateApiBaseUrl(rawUrl, currentHostname = (typeof window !== 'undefined' ? window.location.hostname : 'localhost')) {
  const cleaned = normalizeBaseUrl(rawUrl);
  if (!cleaned) {
    return { valid: false, error: 'URL cannot be empty.' };
  }
  let parsed;
  try {
    parsed = new URL(cleaned);
  } catch {
    return { valid: false, error: 'Please enter a valid URL (e.g., https://api.example.com).' };
  }

  const isLocalTarget = isLocalHostOrigin(parsed.hostname);
  const isLocalPage = isLocalHostOrigin(currentHostname);

  if (parsed.protocol !== 'https:' && !(parsed.protocol === 'http:' && (isLocalTarget || isLocalPage))) {
    return { valid: false, error: 'Production API URLs must use HTTPS.' };
  }

  return { valid: true, url: cleaned };
}

export function getDefaultApiBaseUrl() {
  if (typeof window !== 'undefined' && isLocalHostOrigin(window.location.hostname)) {
    return window.location.port === '8000' ? window.location.origin : 'http://127.0.0.1:8000';
  }
  return DEFAULT_PRODUCTION_API_URL;
}
