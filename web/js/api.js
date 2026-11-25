import { REQUEST_TIMEOUT_MS, WAKEUP_THRESHOLD_MS, normalizeBaseUrl } from './config.js';

export class RateLimitError extends Error {
  constructor(message = 'Rate limit reached (HTTP 429). Please wait a minute before trying again.') {
    super(message);
    this.name = 'RateLimitError';
    this.code = 429;
  }
}

export class TimeoutError extends Error {
  constructor(message = 'The request timed out while waiting for the server.') {
    super(message);
    this.name = 'TimeoutError';
  }
}

export class OfflineError extends Error {
  constructor(message = 'You appear to be offline or the server could not be reached.') {
    super(message);
    this.name = 'OfflineError';
  }
}

export class CancelledError extends Error {
  constructor(message = 'Request cancelled.') {
    super(message);
    this.name = 'CancelledError';
  }
}

export class ApiError extends Error {
  constructor(message, status = 500) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function fetchJsonWithGuard(url, options = {}, { onWakeup = null, externalSignal = null, timeoutMs = REQUEST_TIMEOUT_MS } = {}) {
  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    throw new OfflineError();
  }

  const controller = new AbortController();
  let timedOut = false;
  let wakeupTimer = null;
  let timeoutTimer = null;

  const onExternalAbort = () => controller.abort();
  if (externalSignal) {
    if (externalSignal.aborted) {
      throw new CancelledError();
    }
    externalSignal.addEventListener('abort', onExternalAbort, { once: true });
  }

  if (typeof onWakeup === 'function') {
    wakeupTimer = setTimeout(() => {
      onWakeup();
    }, WAKEUP_THRESHOLD_MS);
  }

  if (timeoutMs > 0) {
    timeoutTimer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);
  }

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    if (res.status === 429) {
      let msg;
      try {
        const body = await res.json();
        msg = body?.detail;
      } catch {
        msg = null;
      }
      throw new RateLimitError(msg || undefined);
    }

    if (!res.ok) {
      let detail = `Server returned HTTP ${res.status}`;
      try {
        const errBody = await res.json();
        if (errBody?.detail) detail = String(errBody.detail);
      } catch {
        // Ignore parse failure
      }
      throw new ApiError(detail, res.status);
    }

    return await res.json();
  } catch (err) {
    if (err instanceof RateLimitError || err instanceof ApiError || err instanceof OfflineError) {
      throw err;
    }
    if (err?.name === 'AbortError') {
      if (timedOut) throw new TimeoutError();
      throw new CancelledError();
    }
    throw new OfflineError(
      'Unable to reach the legal knowledge server. Please check your connection or server URL in About.'
    );
  } finally {
    if (wakeupTimer) clearTimeout(wakeupTimer);
    if (timeoutTimer) clearTimeout(timeoutTimer);
    if (externalSignal) {
      externalSignal.removeEventListener('abort', onExternalAbort);
    }
  }
}

export function createApiClient(getBaseUrlFn) {
  const base = () => normalizeBaseUrl(getBaseUrlFn());

  return {
    async checkHealth() {
      return fetchJsonWithGuard(`${base()}/health`, { method: 'GET' }, { timeoutMs: 12000 });
    },

    async getExamples() {
      return fetchJsonWithGuard(`${base()}/examples`, { method: 'GET' }, { timeoutMs: 15000 });
    },

    async getCoverage() {
      return fetchJsonWithGuard(`${base()}/coverage`, { method: 'GET' }, { timeoutMs: 20000 });
    },

    async askQuestion(question, conversationHistory = [], { onWakeup = null, signal = null } = {}) {
      const payload = { question };
      if (Array.isArray(conversationHistory) && conversationHistory.length > 0) {
        payload.conversation_history = conversationHistory.slice(-2);
      }
      return fetchJsonWithGuard(
        `${base()}/ask`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        },
        { onWakeup, externalSignal: signal, timeoutMs: REQUEST_TIMEOUT_MS }
      );
    },

    async submitFeedback({ question, feedback, responseStatus, comment, details = {} }) {
      return fetchJsonWithGuard(
        `${base()}/feedback`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question,
            feedback,
            response_status: responseStatus || null,
            comment: comment || null,
            details,
          }),
        },
        { timeoutMs: 15000 }
      );
    },
  };
}
