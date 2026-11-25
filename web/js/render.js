/**
 * Pure DOM rendering helpers for NyayaSahayak Web App.
 * SECURITY: All backend text is rendered strictly via textContent (zero innerHTML with backend data).
 */

const SVG_NS = 'http://www.w3.org/2000/svg';

export const STATUS_META = {
  answered: { label: 'Answered', icon: 'check' },
  needs_clarification: { label: 'Needs clarification', icon: 'help' },
  not_covered_yet: { label: 'Not covered yet', icon: 'schedule' },
  insufficient_evidence: { label: 'Not enough information', icon: 'search_off' },
  out_of_scope: { label: 'Out of scope', icon: 'block' },
  error: { label: 'Connection or server issue', icon: 'warning' },
};

const ICON_PATHS = {
  check: 'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z',
  help: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z',
  schedule: 'M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z',
  search_off: 'M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z',
  block: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM4 12c0-4.42 3.58-8 8-8 1.85 0 3.55.63 4.9 1.69L5.69 16.9A7.902 7.902 0 0 1 4 12zm8 8c-1.85 0-3.55-.63-4.9-1.69L18.31 7.1A7.902 7.902 0 0 1 20 12c0 4.42-3.58 8-8 8z',
  warning: 'M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z',
  open_in_new: 'M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z',
  chevron_right: 'M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z',
  expand_more: 'M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z',
  expand_less: 'M12 8l-6 6 1.41 1.41L12 10.83l4.59 4.58L18 14z',
  thumb_up: 'M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z',
  thumb_down: 'M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z',
  flag: 'M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z',
  copy: 'M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z',
  share: 'M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z',
  print: 'M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V3z',
  delete: 'M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z',
  gavel: 'M1 21h12v2H1zM5.245 8.07l2.83-2.827 14.14 14.142-2.828 2.828zM12.317 1l5.657 5.656-2.83 2.83-5.654-5.66zM3.825 9.485l5.657 5.657-2.828 2.828-5.657-5.657z',
  refresh: 'M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z',
};

export function createSvgIcon(doc, name, size = 18, extraClass = '') {
  const svg = doc.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('width', String(size));
  svg.setAttribute('height', String(size));
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('fill', 'currentColor');
  svg.setAttribute('aria-hidden', 'true');
  if (extraClass) svg.setAttribute('class', extraClass);
  const path = doc.createElementNS(SVG_NS, 'path');
  path.setAttribute('d', ICON_PATHS[name] || ICON_PATHS.check);
  svg.appendChild(path);
  return svg;
}

export function el(doc, tag, className = '', text = null) {
  const node = doc.createElement(tag);
  if (className) node.className = className;
  if (text !== null && text !== undefined) node.textContent = String(text);
  return node;
}

export function isSafeHttpUrl(url) {
  if (!url || typeof url !== 'string') return false;
  try {
    const parsed = new URL(url.trim());
    return parsed.protocol === 'https:' || parsed.protocol === 'http:';
  } catch {
    return false;
  }
}

export function formatDisplayDate(input) {
  if (!input) return '';
  const d = typeof input === 'number' ? new Date(input) : new Date(String(input));
  if (Number.isNaN(d.getTime())) return String(input);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const day = String(d.getDate()).padStart(2, '0');
  return `${day} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

export function createStatusBadge(doc, statusKey) {
  const normalized = STATUS_META[statusKey] ? statusKey : 'error';
  const meta = STATUS_META[normalized];
  const badge = el(doc, 'span', `status-badge ${normalized}`);
  badge.setAttribute('role', 'status');
  badge.appendChild(createSvgIcon(doc, meta.icon, 16));
  badge.appendChild(el(doc, 'span', '', meta.label));
  return badge;
}

export function createSourceCard(doc, detail, lastVerified = null) {
  const card = el(doc, 'article', 'card source-card');

  const header = el(doc, 'header', '');
  const topRow = el(doc, 'div', 'status-row');
  const lawLabel = el(doc, 'span', 'source-law-label', `${detail.law || 'Official Statute'} · ${detail.section || ''}`.trim());
  topRow.appendChild(lawLabel);

  if (detail.old_equivalent) {
    topRow.appendChild(el(doc, 'span', 'earlier-law-tag', `Earlier law: ${detail.old_equivalent}`));
  }
  header.appendChild(topRow);

  if (detail.source_title || detail.claim) {
    header.appendChild(el(doc, 'h3', 'card-title-md', detail.source_title || detail.claim));
  }
  card.appendChild(header);

  if (detail.quote) {
    const quote = el(doc, 'blockquote', 'statute-quote', `"${detail.quote}"`);
    card.appendChild(quote);
  }

  const footer = el(doc, 'footer', 'source-card-footer');
  const metaCol = el(doc, 'div', '');
  if (detail.location) {
    metaCol.appendChild(el(doc, 'div', 'card-body-sm', `Location: ${detail.location}`));
  }
  if (lastVerified) {
    metaCol.appendChild(el(doc, 'div', 'mono-meta', `Last verified: ${formatDisplayDate(lastVerified)}`));
  }
  footer.appendChild(metaCol);

  if (isSafeHttpUrl(detail.source_url)) {
    const link = el(doc, 'a', 'source-ext-link');
    link.href = detail.source_url.trim();
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.appendChild(el(doc, 'span', '', 'Open official source'));
    link.appendChild(createSvgIcon(doc, 'open_in_new', 16));
    footer.appendChild(link);
  }

  card.appendChild(footer);
  return card;
}

export function formatCopyAnswerText(response, isDetailed = false) {
  if (!response) return '';
  const lines = [];
  if (response.question) lines.push(`Question: ${response.question}`);
  lines.push(`Status: ${(STATUS_META[response.status] || STATUS_META.error).label}`);

  if (response.short_answer) {
    const text = isDetailed ? (response.short_answer.detailed || response.short_answer.simple) : response.short_answer.simple;
    if (text) lines.push(`\nAnswer:\n${text}`);
  }
  if (Array.isArray(response.key_points) && response.key_points.length > 0) {
    lines.push('\nKey points:');
    response.key_points.forEach((pt) => lines.push(`- ${pt}`));
  }
  const sources = (response.details && response.details.length > 0) ? response.details : (response.related_sources || []);
  if (sources.length > 0) {
    lines.push('\nOfficial Sources:');
    sources.forEach((s, idx) => {
      lines.push(`${idx + 1}. ${s.law || ''} ${s.section || ''}${s.old_equivalent ? ` (Earlier law: ${s.old_equivalent})` : ''}`);
      if (s.quote) lines.push(`   "${s.quote}"`);
      if (s.source_url) lines.push(`   Source: ${s.source_url}`);
    });
  }
  lines.push(`\nDisclaimer: ${response.disclaimer || 'General information, not legal advice.'}`);
  return lines.join('\n');
}

/**
 * Renders the Answer + Sources layout into mainContainer and sourcesContainer.
 */
export function renderAnswerView(
  doc,
  {
    mainCol,
    sourcesAside,
    response,
    state,
    callbacks = {},
  }
) {
  mainCol.replaceChildren();
  sourcesAside.replaceChildren();

  const status = STATUS_META[response?.status] ? response.status : 'error';
  const detailsList = Array.isArray(response?.details) ? response.details : [];
  const relatedList = Array.isArray(response?.related_sources) ? response.related_sources : [];
  const sourcesToShow = detailsList.length > 0 ? detailsList : relatedList;

  // Status + Checked sources count
  const statusRow = el(doc, 'div', 'status-row');
  statusRow.appendChild(createStatusBadge(doc, status));
  if (sourcesToShow.length > 0) {
    statusRow.appendChild(
      el(doc, 'span', 'card-body-sm', `Checked ${sourcesToShow.length} official ${sourcesToShow.length === 1 ? 'source' : 'sources'}`)
    );
  }
  mainCol.appendChild(statusRow);

  // Question bubble (semantic h1 for Answer view)
  if (response?.question) {
    const qBubble = el(doc, 'div', 'question-bubble');
    qBubble.appendChild(el(doc, 'h1', 'question-bubble-text', response.question));
    mainCol.appendChild(qBubble);
  }

  const card = el(doc, 'article', 'card');
  card.setAttribute('data-status', status);

  if (status === 'answered') {
    const header = el(doc, 'header', 'answer-card-header');
    header.appendChild(el(doc, 'h2', 'answer-card-title', 'Short answer'));

    const toggleGroup = el(doc, 'div', 'segmented-group');
    toggleGroup.setAttribute('role', 'group');
    toggleGroup.setAttribute('aria-label', 'Reading level');

    const simpleBtn = el(doc, 'button', 'segmented-btn', 'Simple');
    simpleBtn.type = 'button';
    simpleBtn.setAttribute('aria-pressed', String(!state.isDetailed));
    simpleBtn.addEventListener('click', () => callbacks.onToggleDetail?.(false));

    const detailedBtn = el(doc, 'button', 'segmented-btn', 'Detailed');
    detailedBtn.type = 'button';
    detailedBtn.setAttribute('aria-pressed', String(Boolean(state.isDetailed)));
    detailedBtn.addEventListener('click', () => callbacks.onToggleDetail?.(true));

    toggleGroup.append(simpleBtn, detailedBtn);
    header.appendChild(toggleGroup);
    card.appendChild(header);

    const summaryText = state.isDetailed
      ? (response.short_answer?.detailed || response.short_answer?.simple || '')
      : (response.short_answer?.simple || response.short_answer?.detailed || '');

    if (summaryText) {
      const p = el(doc, 'p', 'answer-summary-text', summaryText);
      p.style.marginTop = '1rem';
      card.appendChild(p);
    }

    if (Array.isArray(response.key_points) && response.key_points.length > 0) {
      const ul = el(doc, 'ul', 'keypoints-list');
      ul.style.marginTop = '1rem';
      response.key_points.forEach((pt) => {
        const li = el(doc, 'li', 'keypoint-item');
        li.appendChild(createSvgIcon(doc, 'check', 18, 'keypoint-check'));
        li.appendChild(el(doc, 'span', '', pt));
        ul.appendChild(li);
      });
      card.appendChild(ul);
    }

    // Mobile/tablet collapsible toggle for sources
    if (sourcesToShow.length > 0) {
      const toggleWrap = el(doc, 'div', 'mobile-sources-toggle');
      toggleWrap.style.marginTop = '1rem';
      const expandBtn = el(doc, 'button', 'btn btn-secondary');
      expandBtn.type = 'button';
      expandBtn.setAttribute('aria-expanded', String(Boolean(state.sourcesExpanded)));
      expandBtn.appendChild(createSvgIcon(doc, state.sourcesExpanded ? 'expand_less' : 'expand_more', 20));
      expandBtn.appendChild(el(doc, 'span', '', `Show details and sources (${sourcesToShow.length})`));
      expandBtn.addEventListener('click', () => callbacks.onToggleSources?.());
      toggleWrap.appendChild(expandBtn);
      card.appendChild(toggleWrap);
    }

    // Footer with disclaimer + action buttons
    const footer = el(doc, 'footer', 'answer-footer');
    footer.style.marginTop = '1.25rem';
    footer.appendChild(
      el(doc, 'p', 'card-body-sm', response.disclaimer || 'General information, not legal advice.')
    );

    const actions = el(doc, 'div', 'action-row');
    const mkAction = (id, icon, label, active, handler) => {
      const b = el(doc, 'button', `action-btn${active ? ' active' : ''}`);
      b.type = 'button';
      b.setAttribute('data-action', id);
      b.appendChild(createSvgIcon(doc, icon, 18));
      b.appendChild(el(doc, 'span', '', label));
      b.addEventListener('click', handler);
      return b;
    };

    actions.appendChild(mkAction('helpful', 'thumb_up', 'Helpful', state.feedback === 'helpful', () => callbacks.onFeedback?.('helpful')));
    actions.appendChild(mkAction('wrong', 'thumb_down', 'Wrong', state.feedback === 'wrong', () => callbacks.onFeedback?.('wrong')));
    actions.appendChild(mkAction('report', 'flag', 'Report', false, () => callbacks.onOpenFeedback?.()));
    actions.appendChild(mkAction('copy', 'copy', 'Copy answer', false, () => callbacks.onCopyAnswer?.()));
    actions.appendChild(mkAction('share', 'share', 'Share link', false, () => callbacks.onShareLink?.()));
    actions.appendChild(mkAction('print', 'print', 'Print', false, () => callbacks.onPrint?.()));
    footer.appendChild(actions);
    card.appendChild(footer);
  } else if (status === 'needs_clarification') {
    card.appendChild(
      el(doc, 'h2', 'answer-card-title', response.clarification_question || 'Please clarify your question')
    );
    const list = el(doc, 'div', 'clarification-list');
    list.style.marginTop = '1rem';
    (response.clarification_options || []).forEach((opt) => {
      const btn = el(doc, 'button', 'clarification-btn');
      btn.type = 'button';
      btn.appendChild(el(doc, 'span', '', opt));
      btn.appendChild(createSvgIcon(doc, 'chevron_right', 22));
      btn.addEventListener('click', () => callbacks.onClarificationPick?.(opt));
      list.appendChild(btn);
    });
    card.appendChild(list);
    const disc = el(doc, 'p', 'card-body-sm', response.disclaimer || 'General information, not legal advice.');
    disc.style.marginTop = '1rem';
    card.appendChild(disc);
  } else if (status === 'not_covered_yet') {
    card.appendChild(el(doc, 'h2', 'answer-card-title', 'This legal area is not covered yet'));
    const domain = response.uncovered_area ? `Requested topic: ${response.uncovered_area}. ` : '';
    const msg = el(
      doc,
      'p',
      'answer-summary-text',
      `${domain}NyayaSahayak currently indexes selected sections of official Indian statutes and refuses to guess on unindexed laws.`
    );
    msg.style.marginTop = '0.75rem';
    card.appendChild(msg);

    const row = el(doc, 'div', 'action-row');
    row.style.marginTop = '1rem';
    const covBtn = el(doc, 'button', 'btn btn-primary', 'See what is covered');
    covBtn.type = 'button';
    covBtn.addEventListener('click', () => callbacks.onNavigate?.('coverage'));
    const askBtn = el(doc, 'button', 'btn btn-secondary', 'Ask another question');
    askBtn.type = 'button';
    askBtn.addEventListener('click', () => callbacks.onNavigate?.('home'));
    row.append(covBtn, askBtn);
    card.appendChild(row);
  } else if (status === 'insufficient_evidence') {
    card.appendChild(el(doc, 'h2', 'answer-card-title', 'Not enough official evidence to answer'));
    const msg = el(
      doc,
      'p',
      'answer-summary-text',
      'No verified passages in the approved corpus directly support this question. NyayaSahayak does not speculate.'
    );
    msg.style.marginTop = '0.75rem';
    card.appendChild(msg);

    if (Array.isArray(response.key_points) && response.key_points.length > 0) {
      const ul = el(doc, 'ul', 'keypoints-list');
      ul.style.marginTop = '0.75rem';
      response.key_points.forEach((pt) => {
        const li = el(doc, 'li', 'keypoint-item');
        li.appendChild(el(doc, 'span', '', `• ${pt}`));
        ul.appendChild(li);
      });
      card.appendChild(ul);
    }

    const row = el(doc, 'div', 'action-row');
    row.style.marginTop = '1rem';
    const covBtn = el(doc, 'button', 'btn btn-secondary', 'Check covered statutes');
    covBtn.type = 'button';
    covBtn.addEventListener('click', () => callbacks.onNavigate?.('coverage'));
    row.appendChild(covBtn);
    card.appendChild(row);
  } else if (status === 'out_of_scope') {
    card.appendChild(el(doc, 'h2', 'answer-card-title', 'Outside Indian legal scope'));
    const msg = el(
      doc,
      'p',
      'answer-summary-text',
      'This question appears to be outside the scope of Indian central statutes. Try asking about fundamental rights, arrest or bail under BNSS, offences under BNS, consumer rights, or RTI.'
    );
    msg.style.marginTop = '0.75rem';
    card.appendChild(msg);

    const row = el(doc, 'div', 'action-row');
    row.style.marginTop = '1rem';
    const covBtn = el(doc, 'button', 'btn btn-secondary', 'See what is covered');
    covBtn.type = 'button';
    covBtn.addEventListener('click', () => callbacks.onNavigate?.('coverage'));
    row.appendChild(covBtn);
    card.appendChild(row);
  } else {
    card.appendChild(el(doc, 'h2', 'answer-card-title', 'Could not complete verification'));
    const errText = response?.short_answer?.simple || 'An error occurred while verifying your question.';
    const msg = el(doc, 'p', 'answer-summary-text', errText);
    msg.style.marginTop = '0.75rem';
    card.appendChild(msg);

    const row = el(doc, 'div', 'action-row');
    row.style.marginTop = '1rem';
    const retryBtn = el(doc, 'button', 'btn btn-primary');
    retryBtn.type = 'button';
    retryBtn.appendChild(createSvgIcon(doc, 'refresh', 18));
    retryBtn.appendChild(el(doc, 'span', '', 'Try again'));
    retryBtn.addEventListener('click', () => callbacks.onRetry?.());
    row.appendChild(retryBtn);
    card.appendChild(row);
  }

  mainCol.appendChild(card);

  // Render Sources Aside
  if (sourcesToShow.length > 0) {
    sourcesAside.hidden = false;
    const sHead = el(doc, 'div', 'sources-header');
    const sTitle = el(doc, 'h2', 'sources-title');
    sTitle.appendChild(createSvgIcon(doc, 'gavel', 20));
    sTitle.appendChild(
      el(doc, 'span', '', detailsList.length > 0 ? 'Sources & exact quotes' : 'Related official provisions (reference only)')
    );
    sHead.appendChild(sTitle);
    sHead.appendChild(el(doc, 'span', 'mono-meta', `${sourcesToShow.length} verified`));
    sourcesAside.appendChild(sHead);

    sourcesToShow.forEach((src) => {
      sourcesAside.appendChild(createSourceCard(doc, src, response.last_verified));
    });
  } else {
    sourcesAside.hidden = true;
  }
}
