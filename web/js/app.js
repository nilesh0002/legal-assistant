import {
  MAX_QUESTION_LENGTH,
  getDefaultApiBaseUrl,
  validateApiBaseUrl,
} from './config.js';
import {
  CancelledError,
  OfflineError,
  RateLimitError,
  TimeoutError,
  createApiClient,
} from './api.js';
import {
  addHistoryItem,
  clearHistory,
  deleteHistoryItem,
  getHistory,
  getSavedApiUrl,
  getSavedTextSize,
  getSavedTheme,
  hasAcceptedDisclaimer,
  saveApiUrl,
  saveTextSize,
  saveTheme,
  setDisclaimerAccepted,
} from './storage.js';
import {
  STATUS_META,
  createStatusBadge,
  createSvgIcon,
  el,
  formatCopyAnswerText,
  formatDisplayDate,
  renderAnswerView,
} from './render.js';

const DEFAULT_EXAMPLES = [
  'What are my rights if arrested?',
  'How do I file an RTI application?',
  'What does Article 21 protect?',
  'How to complain about a faulty product?',
  'When is bail a right under BNSS?',
  'Time limit to reply to an RTI?',
  'Can police arrest women after sunset?',
  'What is the punishment for theft under BNS?',
];

const appState = {
  view: 'home', // 'home' | 'answer' | 'history' | 'coverage' | 'about'
  apiBaseUrl: getSavedApiUrl() || getDefaultApiBaseUrl(),
  theme: getSavedTheme(),
  textSize: getSavedTextSize(),
  lastQuestion: '',
  currentResponse: null,
  isDetailed: false,
  sourcesExpanded: false,
  feedback: null,
  conversationTurns: [], // last 2 turns for follow-up support
  coverageData: null,
  activeAbortController: null,
  toastTimer: null,
};

const api = createApiClient(() => appState.apiBaseUrl);

// DOM references
const $ = (id) => document.getElementById(id);

function announce(message) {
  const region = $('aria-live-region');
  if (region) {
    region.textContent = '';
    setTimeout(() => {
      region.textContent = message;
    }, 50);
  }
}

function showToast(message) {
  const toast = $('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.hidden = false;
  if (appState.toastTimer) clearTimeout(appState.toastTimer);
  appState.toastTimer = setTimeout(() => {
    toast.hidden = true;
  }, 3200);
}

function applyTheme(mode) {
  appState.theme = mode;
  saveTheme(mode);
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = mode === 'dark' || (mode === 'system' && prefersDark);
  document.documentElement.classList.toggle('dark', isDark);

  const btn = $('btn-theme-toggle');
  if (btn) {
    btn.setAttribute('aria-pressed', String(isDark));
    btn.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
  }
  const lightBtn = $('btn-pref-light');
  const darkBtn = $('btn-pref-dark');
  if (lightBtn && darkBtn) {
    lightBtn.setAttribute('aria-pressed', String(!isDark));
    darkBtn.setAttribute('aria-pressed', String(isDark));
  }
}

function applyTextSize(size) {
  appState.textSize = size;
  saveTextSize(size);
  const isLarge = size === 'large';
  document.documentElement.classList.toggle('text-large', isLarge);
  const stdBtn = $('btn-size-standard');
  const lgBtn = $('btn-size-large');
  if (stdBtn && lgBtn) {
    stdBtn.setAttribute('aria-pressed', String(!isLarge));
    lgBtn.setAttribute('aria-pressed', String(isLarge));
  }
}

function switchView(viewName) {
  appState.view = viewName;
  const views = ['home', 'answer', 'history', 'coverage', 'about'];
  views.forEach((v) => {
    const section = $(`view-${v}`);
    if (section) section.hidden = v !== viewName;
  });

  // Update nav active states
  document.querySelectorAll('[data-nav]').forEach((btn) => {
    const target = btn.getAttribute('data-nav');
    const isCurrent = target === viewName || (target === 'home' && viewName === 'answer');
    if (isCurrent) {
      btn.setAttribute('aria-current', 'page');
    } else {
      btn.removeAttribute('aria-current');
    }
  });

  // Close mobile drawer on navigation
  const drawer = $('mobile-menu-drawer');
  if (drawer) drawer.hidden = true;
  const menuBtn = $('btn-mobile-menu');
  if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');

  if (viewName === 'history') renderHistoryList();
  if (viewName === 'coverage' && !appState.coverageData) loadCoverage();
}

function updateBackendStatusPill(status, label) {
  const pill = $('backend-status');
  const text = $('backend-status-text');
  if (!pill || !text) return;
  pill.className = `status-dot-pill ${status}`;
  text.textContent = label;
}

async function checkBackendHealth() {
  updateBackendStatusPill('connecting', 'Checking...');
  try {
    const data = await api.checkHealth();
    if (data && (data.status === 'healthy' || data.status === 'ok')) {
      updateBackendStatusPill('online', 'Live');
    } else {
      updateBackendStatusPill('offline', 'Offline');
    }
  } catch {
    updateBackendStatusPill('offline', 'Offline');
  }
}

function renderExampleChips(examples) {
  const container = $('example-chips');
  if (!container) return;
  container.replaceChildren();
  (examples || DEFAULT_EXAMPLES).slice(0, 8).forEach((q) => {
    const btn = el(document, 'button', 'chip-action', q);
    btn.type = 'button';
    btn.addEventListener('click', () => runQuestion(q));
    container.appendChild(btn);
  });
}

async function loadExamples() {
  renderExampleChips(DEFAULT_EXAMPLES);
  try {
    const data = await api.getExamples();
    if (data && Array.isArray(data.examples) && data.examples.length > 0) {
      renderExampleChips(data.examples);
    }
  } catch {
    // Fallback to default examples already rendered
  }
}

function syncMobileSourcesVisibility() {
  const aside = $('sources-aside');
  if (!aside) return;
  const isDesktop = window.innerWidth >= 1024;
  const isRelatedOnly = appState.currentResponse?.status === 'insufficient_evidence' &&
    Array.isArray(appState.currentResponse?.related_sources) &&
    appState.currentResponse.related_sources.length > 0;
  if (isDesktop || isRelatedOnly) {
    aside.style.display = '';
  } else {
    aside.style.display = appState.sourcesExpanded ? 'flex' : 'none';
  }
}

function renderCurrentAnswer() {
  if (!appState.currentResponse) return;
  const mainCol = $('answer-main-col');
  const sourcesAside = $('sources-aside');
  const printDate = $('print-date');
  if (printDate) printDate.textContent = `Printed ${formatDisplayDate(Date.now())}`;

  renderAnswerView(document, {
    mainCol,
    sourcesAside,
    response: appState.currentResponse,
    state: {
      isDetailed: appState.isDetailed,
      sourcesExpanded: appState.sourcesExpanded,
      feedback: appState.feedback,
    },
    callbacks: {
      onToggleDetail: (detailed) => {
        appState.isDetailed = detailed;
        renderCurrentAnswer();
      },
      onToggleSources: () => {
        appState.sourcesExpanded = !appState.sourcesExpanded;
        renderCurrentAnswer();
        syncMobileSourcesVisibility();
      },
      onFeedback: async (rating) => {
        appState.feedback = rating;
        renderCurrentAnswer();
        try {
          await api.submitFeedback({
            question: appState.currentResponse.question || appState.lastQuestion,
            feedback: rating,
            responseStatus: appState.currentResponse.status,
          });
          showToast('Thank you! Feedback recorded.');
        } catch {
          showToast('Could not send feedback right now.');
        }
      },
      onOpenFeedback: () => openFeedbackModal(),
      onCopyAnswer: async () => {
        const txt = formatCopyAnswerText(appState.currentResponse, appState.isDetailed);
        try {
          await navigator.clipboard.writeText(txt);
          showToast('Answer and sources copied.');
        } catch {
          showToast('Copy not supported in this browser.');
        }
      },
      onShareLink: async () => {
        const q = appState.currentResponse.question || appState.lastQuestion;
        const url = `${window.location.origin}${window.location.pathname}?q=${encodeURIComponent(q)}`;
        try {
          await navigator.clipboard.writeText(url);
          showToast('Shareable link copied.');
        } catch {
          showToast(`Share URL: ?q=${encodeURIComponent(q)}`);
        }
      },
      onPrint: () => window.print(),
      onClarificationPick: (option) => runQuestion(option),
      onNavigate: (target) => switchView(target),
      onRetry: () => runQuestion(appState.lastQuestion),
    },
  });

  syncMobileSourcesVisibility();
}

async function runQuestion(rawQuestion) {
  const question = String(rawQuestion || '').trim().slice(0, MAX_QUESTION_LENGTH);
  if (question.length < 3) {
    showToast('Please enter at least 3 characters.');
    return;
  }

  if (appState.activeAbortController) {
    appState.activeAbortController.abort();
  }
  const controller = new AbortController();
  appState.activeAbortController = controller;

  appState.lastQuestion = question;
  appState.currentResponse = null;
  appState.feedback = null;
  appState.sourcesExpanded = false;

  const homeInput = $('ask-input-home');
  if (homeInput) homeInput.value = question;
  const charCount = $('char-count');
  if (charCount) charCount.textContent = `${question.length} / ${MAX_QUESTION_LENGTH}`;

  switchView('answer');
  $('answer-loading').hidden = false;
  $('wakeup-banner').hidden = true;
  $('answer-results-grid').hidden = true;
  $('followup-box').hidden = true;
  announce('Searching verified Indian legal sources...');

  try {
    const response = await api.askQuestion(question, appState.conversationTurns, {
      signal: controller.signal,
      onWakeup: () => {
        $('wakeup-banner').hidden = false;
        announce('The server is waking up, this can take up to a minute.');
      },
    });

    appState.activeAbortController = null;
    appState.currentResponse = response;

    // Track last 2 turns for follow-up support
    const ansSummary = response.short_answer?.simple || response.short_answer?.detailed || '';
    if (response.status === 'answered' && ansSummary) {
      appState.conversationTurns = [
        ...appState.conversationTurns,
        { question, answer: ansSummary },
      ].slice(-2);
    }

    addHistoryItem(question, response);
    $('answer-loading').hidden = true;
    $('answer-results-grid').hidden = false;
    $('followup-box').hidden = false;
    updateBackendStatusPill('online', 'Live');
    renderCurrentAnswer();

    const meta = STATUS_META[response.status] || STATUS_META.error;
    announce(`Response ready. Status: ${meta.label}.`);
  } catch (err) {
    appState.activeAbortController = null;
    $('answer-loading').hidden = true;

    if (err instanceof CancelledError) {
      switchView('home');
      announce('Search cancelled.');
      return;
    }

    let friendly = err.message || 'An unexpected error occurred.';
    if (err instanceof RateLimitError) {
      friendly = 'Rate limit reached (HTTP 429). Please wait a moment and tap Try again.';
    } else if (err instanceof TimeoutError) {
      friendly = 'The server took too long to respond (timeout). It may still be starting up—tap Try again.';
    } else if (err instanceof OfflineError) {
      updateBackendStatusPill('offline', 'Offline');
    }

    appState.currentResponse = {
      status: 'error',
      question,
      short_answer: { simple: friendly, detailed: friendly },
      disclaimer: 'General information, not legal advice.',
    };

    $('answer-results-grid').hidden = false;
    $('followup-box').hidden = false;
    renderCurrentAnswer();
    announce(`Error: ${friendly}`);
  }
}

function renderHistoryList() {
  const listEl = $('history-list');
  const emptyEl = $('history-empty');
  const clearBtn = $('btn-clear-history');
  if (!listEl || !emptyEl) return;

  const items = getHistory();
  listEl.replaceChildren();
  if (items.length === 0) {
    emptyEl.hidden = false;
    if (clearBtn) clearBtn.hidden = true;
    return;
  }

  emptyEl.hidden = true;
  if (clearBtn) clearBtn.hidden = false;

  items.forEach((item) => {
    const li = el(document, 'li', 'card history-item');

    const openBtn = el(document, 'button', 'history-open-btn');
    openBtn.type = 'button';

    const metaRow = el(document, 'div', 'status-row');
    metaRow.appendChild(createStatusBadge(document, item.response?.status || 'error'));
    metaRow.appendChild(el(document, 'span', 'mono-meta', formatDisplayDate(item.timestamp)));
    openBtn.appendChild(metaRow);
    openBtn.appendChild(el(document, 'span', 'card-title-md', item.question));

    openBtn.addEventListener('click', () => {
      appState.lastQuestion = item.question;
      appState.currentResponse = item.response;
      appState.feedback = null;
      appState.sourcesExpanded = false;
      switchView('answer');
      $('answer-loading').hidden = true;
      $('answer-results-grid').hidden = false;
      $('followup-box').hidden = false;
      renderCurrentAnswer();
    });

    const delBtn = el(document, 'button', 'btn-icon');
    delBtn.type = 'button';
    delBtn.setAttribute('aria-label', `Delete "${item.question}" from history`);
    delBtn.appendChild(createSvgIcon(document, 'delete', 20));
    delBtn.addEventListener('click', () => {
      deleteHistoryItem(item.id);
      renderHistoryList();
      showToast('Removed from history.');
    });

    li.append(openBtn, delBtn);
    listEl.appendChild(li);
  });
}

function renderCoverageList(filterText = '') {
  const container = $('coverage-list');
  if (!container) return;
  container.replaceChildren();

  const data = appState.coverageData;
  if (!data || !Array.isArray(data.laws)) return;

  const q = filterText.trim().toLowerCase();
  const filteredLaws = data.laws
    .map((law) => {
      const lawMatches = (law.law || '').toLowerCase().includes(q);
      const matchingSections = (law.sections || []).filter((s) => {
        if (!q || lawMatches) return true;
        return (
          (s.section || '').toLowerCase().includes(q) ||
          (s.title || '').toLowerCase().includes(q) ||
          (s.old_equivalent || '').toLowerCase().includes(q)
        );
      });
      if (matchingSections.length === 0 && !lawMatches) return null;
      return { ...law, sections: matchingSections };
    })
    .filter(Boolean);

  if (filteredLaws.length === 0) {
    container.appendChild(el(document, 'p', 'card-body-sm', 'No indexed sections matched your filter.'));
    return;
  }

  filteredLaws.forEach((law) => {
    const card = el(document, 'article', 'card');
    const headerBtn = el(document, 'button', 'coverage-law-header');
    headerBtn.type = 'button';
    headerBtn.setAttribute('aria-expanded', 'false');

    const titleCol = el(document, 'div', '');
    titleCol.appendChild(el(document, 'h2', 'card-title-md', law.law));
    titleCol.appendChild(
      el(
        document,
        'p',
        'card-body-sm',
        `${(law.sections || []).length} selected sections · Last verified: ${formatDisplayDate(law.last_verified)}`
      )
    );

    const icon = createSvgIcon(document, 'expand_more', 22);
    headerBtn.append(titleCol, icon);

    const secList = el(document, 'div', 'coverage-sections-list');
    secList.hidden = true;
    (law.sections || []).forEach((s) => {
      const row = el(document, 'div', 'coverage-section-row');
      const left = el(document, 'div', '');
      left.appendChild(el(document, 'div', 'card-title-md', s.title || s.section));
      if (s.old_equivalent) {
        left.appendChild(el(document, 'div', 'card-body-sm', `Earlier law: ${s.old_equivalent}`));
      }
      row.appendChild(left);
      row.appendChild(el(document, 'span', 'earlier-law-tag', s.section));
      secList.appendChild(row);
    });

    headerBtn.addEventListener('click', () => {
      const willOpen = secList.hidden;
      secList.hidden = !willOpen;
      headerBtn.setAttribute('aria-expanded', String(willOpen));
    });

    card.append(headerBtn, secList);
    container.appendChild(card);
  });
}

async function loadCoverage() {
  const loading = $('coverage-loading');
  const errBox = $('coverage-error');
  const list = $('coverage-list');
  if (loading) loading.hidden = false;
  if (errBox) errBox.hidden = true;
  if (list) list.replaceChildren();

  try {
    const data = await api.getCoverage();
    appState.coverageData = data;
    if (loading) loading.hidden = true;
    const noteEl = $('coverage-note-text');
    if (noteEl && data.note) noteEl.textContent = data.note;
    renderCoverageList($('coverage-filter')?.value || '');
  } catch (err) {
    if (loading) loading.hidden = true;
    if (errBox) {
      errBox.hidden = false;
      $('coverage-error-text').textContent = err.message || 'Unable to load coverage catalog.';
    }
  }
}

function openFeedbackModal() {
  const modal = $('modal-feedback');
  if (modal) modal.hidden = false;
  $('feedback-notes').value = '';
}

function closeFeedbackModal() {
  const modal = $('modal-feedback');
  if (modal) modal.hidden = true;
}

function initEventListeners() {
  // Navigation
  document.querySelectorAll('[data-nav]').forEach((btn) => {
    btn.addEventListener('click', () => switchView(btn.getAttribute('data-nav')));
  });

  // Topic cards on Home
  document.querySelectorAll('[data-topic-query]').forEach((btn) => {
    btn.addEventListener('click', () => runQuestion(btn.getAttribute('data-topic-query')));
  });

  // Mobile menu toggle
  $('btn-mobile-menu')?.addEventListener('click', () => {
    const drawer = $('mobile-menu-drawer');
    const willOpen = drawer.hidden;
    drawer.hidden = !willOpen;
    $('btn-mobile-menu').setAttribute('aria-expanded', String(willOpen));
  });

  // Theme toggles
  $('btn-theme-toggle')?.addEventListener('click', () => {
    const isCurrentlyDark = document.documentElement.classList.contains('dark');
    applyTheme(isCurrentlyDark ? 'light' : 'dark');
  });
  $('btn-pref-light')?.addEventListener('click', () => applyTheme('light'));
  $('btn-pref-dark')?.addEventListener('click', () => applyTheme('dark'));

  // Text size toggles
  $('btn-size-standard')?.addEventListener('click', () => applyTextSize('standard'));
  $('btn-size-large')?.addEventListener('click', () => applyTextSize('large'));

  // Home search form
  const homeInput = $('ask-input-home');
  homeInput?.addEventListener('input', () => {
    $('char-count').textContent = `${homeInput.value.length} / ${MAX_QUESTION_LENGTH}`;
  });
  $('ask-form-home')?.addEventListener('submit', (e) => {
    e.preventDefault();
    runQuestion(homeInput.value);
  });

  // Follow-up form
  $('followup-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const input = $('followup-input');
    if (input.value.trim()) {
      const q = input.value.trim();
      input.value = '';
      runQuestion(q);
    }
  });

  // Cancel slow wake-up request
  $('btn-cancel-request')?.addEventListener('click', () => {
    if (appState.activeAbortController) {
      appState.activeAbortController.abort();
    }
  });

  // History clear all
  $('btn-clear-history')?.addEventListener('click', () => {
    clearHistory();
    renderHistoryList();
    showToast('History cleared.');
  });

  // Coverage filter & retry
  $('coverage-filter')?.addEventListener('input', (e) => {
    renderCoverageList(e.target.value);
  });
  $('btn-coverage-retry')?.addEventListener('click', () => loadCoverage());

  // Settings API URL
  const urlInput = $('input-api-url');
  if (urlInput) urlInput.value = appState.apiBaseUrl;
  $('btn-save-api-url')?.addEventListener('click', () => {
    const check = validateApiBaseUrl(urlInput.value);
    const errEl = $('api-url-error');
    if (!check.valid) {
      errEl.textContent = check.error;
      errEl.hidden = false;
      return;
    }
    errEl.hidden = true;
    appState.apiBaseUrl = check.url;
    saveApiUrl(check.url);
    showToast('API URL updated.');
    checkBackendHealth();
    loadExamples();
  });

  // Disclaimer modal
  $('btn-disclaimer-accept')?.addEventListener('click', () => {
    setDisclaimerAccepted();
    $('modal-disclaimer').hidden = true;
    $('ask-input-home')?.focus();
  });

  // Feedback modal
  $('btn-open-feedback-about')?.addEventListener('click', () => openFeedbackModal());
  $('btn-feedback-close')?.addEventListener('click', () => closeFeedbackModal());
  $('btn-feedback-cancel')?.addEventListener('click', () => closeFeedbackModal());
  $('feedback-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const reason = document.querySelector('input[name="feedback-reason"]:checked')?.value || 'other';
    const notes = $('feedback-notes').value.trim();
    closeFeedbackModal();
    try {
      await api.submitFeedback({
        question: appState.currentResponse?.question || appState.lastQuestion || 'General feedback',
        feedback: 'wrong',
        responseStatus: appState.currentResponse?.status || null,
        comment: `[${reason}] ${notes}`.trim(),
      });
      showToast('Thank you! Feedback submitted.');
    } catch {
      showToast('Could not submit feedback right now.');
    }
  });

  window.addEventListener('resize', syncMobileSourcesVisibility);
}

function bootstrap() {
  applyTheme(appState.theme);
  applyTextSize(appState.textSize);
  initEventListeners();

  if (!hasAcceptedDisclaimer()) {
    $('modal-disclaimer').hidden = false;
  }

  checkBackendHealth();
  loadExamples();

  // Shareable link: ?q=<question>
  const params = new URLSearchParams(window.location.search);
  const sharedQ = params.get('q');
  if (sharedQ && sharedQ.trim().length >= 3) {
    setDisclaimerAccepted();
    $('modal-disclaimer').hidden = true;
    runQuestion(sharedQ);
  }
}

bootstrap();
