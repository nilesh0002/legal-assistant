/**
 * Browser-only localStorage persistence for NyayaSahayak.
 * Zero accounts, zero analytics, zero server-side user tracking.
 */

const KEYS = {
  API_URL: 'nyaya_api_url',
  THEME: 'nyaya_theme', // 'light' | 'dark' | 'system'
  TEXT_SIZE: 'nyaya_text_size', // 'standard' | 'large'
  DISCLAIMER: 'nyaya_disclaimer_accepted_v1',
  HISTORY: 'nyaya_history_v1',
};

const MAX_HISTORY_ITEMS = 50;

function safeGet(key, fallback = null) {
  try {
    const val = window.localStorage.getItem(key);
    return val !== null ? val : fallback;
  } catch {
    return fallback;
  }
}

function safeSet(key, value) {
  try {
    window.localStorage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

export function getSavedApiUrl() {
  return safeGet(KEYS.API_URL, null);
}

export function saveApiUrl(url) {
  return safeSet(KEYS.API_URL, url);
}

export function getSavedTheme() {
  return safeGet(KEYS.THEME, 'system');
}

export function saveTheme(theme) {
  return safeSet(KEYS.THEME, theme);
}

export function getSavedTextSize() {
  return safeGet(KEYS.TEXT_SIZE, 'standard');
}

export function saveTextSize(size) {
  return safeSet(KEYS.TEXT_SIZE, size);
}

export function hasAcceptedDisclaimer() {
  return safeGet(KEYS.DISCLAIMER, 'false') === 'true';
}

export function setDisclaimerAccepted() {
  return safeSet(KEYS.DISCLAIMER, 'true');
}

export function getHistory() {
  try {
    const raw = window.localStorage.getItem(KEYS.HISTORY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function addHistoryItem(question, response) {
  const items = getHistory();
  const entry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    timestamp: Date.now(),
    question: String(question || ''),
    response,
  };
  const next = [entry, ...items.filter((it) => it.question !== entry.question)].slice(0, MAX_HISTORY_ITEMS);
  safeSet(KEYS.HISTORY, JSON.stringify(next));
  return next;
}

export function deleteHistoryItem(id) {
  const next = getHistory().filter((it) => it.id !== id);
  safeSet(KEYS.HISTORY, JSON.stringify(next));
  return next;
}

export function clearHistory() {
  safeSet(KEYS.HISTORY, JSON.stringify([]));
  return [];
}
