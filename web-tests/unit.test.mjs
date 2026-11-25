import test from 'node:test';
import assert from 'node:assert/strict';
import { validateApiBaseUrl } from '../web/js/config.js';
import {
  formatCopyAnswerText,
  formatDisplayDate,
  isSafeHttpUrl,
  renderAnswerView,
} from '../web/js/render.js';

// Minimal DOM mock for pure textContent/createElement testing in Node
function createMockDocument() {
  class MockNode {
    constructor(tagName, ns = null) {
      this.tagName = tagName ? tagName.toUpperCase() : '#TEXT';
      this.namespaceURI = ns;
      this.children = [];
      this.attributes = {};
      this.style = {};
      this.listeners = {};
      this._textContent = '';
      this.className = '';
      this.hidden = false;
      this.href = '';
      this.target = '';
      this.rel = '';
      this.type = '';
    }
    set textContent(val) {
      this._textContent = String(val);
      this.children = [];
    }
    get textContent() {
      if (this.children.length === 0) return this._textContent;
      return this._textContent + this.children.map((c) => c.textContent).join('');
    }
    setAttribute(k, v) {
      this.attributes[k] = String(v);
    }
    getAttribute(k) {
      return this.attributes[k] ?? null;
    }
    appendChild(child) {
      this.children.push(child);
      return child;
    }
    append(...nodes) {
      nodes.forEach((n) => this.appendChild(n));
    }
    replaceChildren(...nodes) {
      this.children = [];
      this._textContent = '';
      nodes.forEach((n) => this.appendChild(n));
    }
    addEventListener(ev, fn) {
      this.listeners[ev] = this.listeners[ev] || [];
      this.listeners[ev].push(fn);
    }
    querySelectorAll(predicate) {
      const out = [];
      for (const c of this.children) {
        if (predicate(c)) out.push(c);
        out.push(...c.querySelectorAll(predicate));
      }
      return out;
    }
  }

  return {
    createElement: (tag) => new MockNode(tag),
    createElementNS: (ns, tag) => new MockNode(tag, ns),
  };
}

const FIXTURES = {
  answered: {
    status: 'answered',
    question: '[FIXTURE] Sample question about procedural rights?',
    short_answer: {
      simple: '[FIXTURE] Simple summary placeholder text.',
      detailed: '[FIXTURE] Detailed summary placeholder text.',
    },
    key_points: ['[FIXTURE] Key point one', '[FIXTURE] Key point two'],
    details: [
      {
        claim: '[FIXTURE] Claim one',
        law: '[FIXTURE] Sample Act, 2023',
        section: 'Section 1',
        old_equivalent: 'Old Section 1',
        quote: '[FIXTURE] Exact placeholder statutory quote.',
        source_id: 'fixture-source',
        source_title: '[FIXTURE] Sample Section Title',
        source_url: 'https://example.gov.in/sample.pdf',
        location: 'Page 1',
      },
    ],
    last_verified: '2026-11-25',
    disclaimer: 'General information, not legal advice.',
  },
  needs_clarification: {
    status: 'needs_clarification',
    question: '[FIXTURE] Ambiguous sample query',
    clarification_question: '[FIXTURE] Which scenario applies?',
    clarification_options: ['[FIXTURE] Option A', '[FIXTURE] Option B'],
    disclaimer: 'General information, not legal advice.',
  },
  not_covered_yet: {
    status: 'not_covered_yet',
    question: '[FIXTURE] Unindexed domain query',
    uncovered_area: '[FIXTURE] Sample Uncovered Domain',
    disclaimer: 'General information, not legal advice.',
  },
  insufficient_evidence: {
    status: 'insufficient_evidence',
    question: '[FIXTURE] Unsupported query',
    key_points: ['[FIXTURE] No supporting passage found.'],
    related_sources: [
      {
        law: '[FIXTURE] Related Act',
        section: 'Section 99',
        quote: '[FIXTURE] Related reference quote.',
        source_url: 'https://example.gov.in/ref.pdf',
      },
    ],
    disclaimer: 'General information, not legal advice.',
  },
  out_of_scope: {
    status: 'out_of_scope',
    question: '[FIXTURE] Non-legal query',
    disclaimer: 'General information, not legal advice.',
  },
  error: {
    status: 'error',
    question: '[FIXTURE] Error query',
    short_answer: { simple: '[FIXTURE] Simulated 429 rate-limit error.' },
    disclaimer: 'General information, not legal advice.',
  },
};

test('config.validateApiBaseUrl enforces HTTPS in production and allows localhost HTTP', () => {
  assert.equal(validateApiBaseUrl('https://api.example.com', 'app.vercel.app').valid, true);
  assert.equal(validateApiBaseUrl('http://api.example.com', 'app.vercel.app').valid, false);
  assert.equal(validateApiBaseUrl('http://127.0.0.1:8000', 'localhost').valid, true);
  assert.equal(validateApiBaseUrl('not-a-url', 'localhost').valid, false);
});

test('isSafeHttpUrl blocks javascript: and data: URLs', () => {
  assert.equal(isSafeHttpUrl('https://indiacode.nic.in/doc.pdf'), true);
  assert.equal(isSafeHttpUrl('javascript:alert(1)'), false);
  assert.equal(isSafeHttpUrl('data:text/html,<script>'), false);
});

test('formatDisplayDate formats ISO date as DD MMM YYYY', () => {
  assert.equal(formatDisplayDate('2026-11-25'), '25 Nov 2026');
});

for (const [statusKey, fixture] of Object.entries(FIXTURES)) {
  test(`renderAnswerView renders status "${statusKey}" cleanly without HTML injection`, () => {
    const doc = createMockDocument();
    const mainCol = doc.createElement('div');
    const sourcesAside = doc.createElement('aside');

    renderAnswerView(doc, {
      mainCol,
      sourcesAside,
      response: fixture,
      state: { isDetailed: false, sourcesExpanded: false, feedback: null },
    });

    const fullText = mainCol.textContent;
    assert.ok(fullText.includes(fixture.question), 'Question should be rendered');
    const articles = mainCol.querySelectorAll((n) => n.tagName === 'ARTICLE');
    assert.equal(articles.length, 1);
    assert.equal(articles[0].getAttribute('data-status'), statusKey);

    if (statusKey === 'answered' || statusKey === 'insufficient_evidence') {
      assert.equal(sourcesAside.hidden, false);
      assert.ok(sourcesAside.textContent.includes('quote') || sourcesAside.textContent.includes('FIXTURE'));
    }
  });
}

test('renderAnswerView neutralizes XSS payloads via textContent', () => {
  const doc = createMockDocument();
  const mainCol = doc.createElement('div');
  const sourcesAside = doc.createElement('aside');
  const malicious = {
    ...FIXTURES.answered,
    question: '<img src=x onerror=alert(1)>',
    short_answer: { simple: '<script>window.pwned=true</script>', detailed: '' },
    details: [
      {
        ...FIXTURES.answered.details[0],
        source_url: 'javascript:alert(1)',
      },
    ],
  };

  renderAnswerView(doc, {
    mainCol,
    sourcesAside,
    response: malicious,
    state: { isDetailed: false, sourcesExpanded: true, feedback: null },
  });

  // No <img> or <script> elements created
  assert.equal(mainCol.querySelectorAll((n) => n.tagName === 'SCRIPT' || n.tagName === 'IMG').length, 0);
  // Malicious javascript: link should NOT be rendered
  assert.equal(sourcesAside.querySelectorAll((n) => n.tagName === 'A').length, 0);
  // Literal text preserved safely
  assert.ok(mainCol.textContent.includes('<script>window.pwned=true</script>'));
});

test('formatCopyAnswerText includes summary, sources, and disclaimer', () => {
  const txt = formatCopyAnswerText(FIXTURES.answered, false);
  assert.ok(txt.includes('[FIXTURE] Simple summary placeholder text.'));
  assert.ok(txt.includes('Earlier law: Old Section 1'));
  assert.ok(txt.includes('General information, not legal advice.'));
});
