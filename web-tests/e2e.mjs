import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WEB_DIR = path.resolve(__dirname, '../web');
const SCREENSHOT_DIR = path.resolve(__dirname, '../design/web-built');

fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.json': 'application/json',
};

function startStaticServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const urlPath = (req.url || '/').split('?')[0];
      const rel = urlPath === '/' ? 'index.html' : urlPath.replace(/^\/+/, '');
      const fullPath = path.join(WEB_DIR, rel);
      if (!fullPath.startsWith(WEB_DIR) || !fs.existsSync(fullPath) || fs.statSync(fullPath).isDirectory()) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }
      const ext = path.extname(fullPath);
      res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
      fs.createReadStream(fullPath).pipe(res);
    });
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address();
      resolve({ server, url: `http://127.0.0.1:${addr.port}` });
    });
  });
}

const MOCK_RESPONSES = {
  answered: {
    status: 'answered',
    question: '[FIXTURE] What are my rights if arrested?',
    short_answer: {
      simple: '[FIXTURE] Simple plain-language summary from verified statute.',
      detailed: '[FIXTURE] Detailed statutory explanation with legal terminology.',
    },
    key_points: ['[FIXTURE] Key point 1: Right to be informed of grounds.', '[FIXTURE] Key point 2: Right to bail info.'],
    details: [
      {
        claim: '[FIXTURE] Right to know grounds of arrest',
        law: '[FIXTURE] Sample Act, 2023',
        section: 'Section 47(1)',
        old_equivalent: 'Old Code Section 50',
        quote: '[FIXTURE] Every police officer arresting any person without warrant shall forthwith communicate full particulars.',
        source_id: 'fixture-bnss',
        source_title: '[FIXTURE] Person arrested to be informed of grounds',
        source_url: 'https://egazette.gov.in/sample.pdf',
        location: 'Page 18',
      },
    ],
    last_verified: '2026-11-25',
    disclaimer: 'General information, not legal advice.',
  },
  needs_clarification: {
    status: 'needs_clarification',
    question: '[FIXTURE] How do I report fraud?',
    clarification_question: '[FIXTURE] Which situation describes your issue?',
    clarification_options: [
      '[FIXTURE] Criminal complaint (FIR)',
      '[FIXTURE] Defective product (Consumer Protection)',
    ],
    disclaimer: 'General information, not legal advice.',
  },
  not_covered_yet: {
    status: 'not_covered_yet',
    question: '[FIXTURE] What is the traffic fine?',
    uncovered_area: '[FIXTURE] Traffic Law',
    disclaimer: 'General information, not legal advice.',
  },
  insufficient_evidence: {
    status: 'insufficient_evidence',
    question: '[FIXTURE] Unsupported legal claim',
    key_points: ['[FIXTURE] No direct verified passages found.'],
    related_sources: [],
    disclaimer: 'General information, not legal advice.',
  },
  out_of_scope: {
    status: 'out_of_scope',
    question: '[FIXTURE] How to bake bread?',
    disclaimer: 'General information, not legal advice.',
  },
};

async function setupApiMocks(page) {
  await page.route('**/health', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'healthy', service: 'NyayaSahayak', version: '0.1.0' }),
    })
  );
  await page.route('**/examples', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        examples: [
          '[FIXTURE] What are my rights if arrested?',
          '[FIXTURE] How do I report fraud?',
          '[FIXTURE] What is the traffic fine?',
        ],
      }),
    })
  );
  await page.route('**/coverage', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        note: 'Selected sections only. Only the listed sections are indexed.',
        total_chunks: 1,
        laws: [
          {
            law: '[FIXTURE] Sample Act, 2023',
            source_id: 'fixture-act',
            last_verified: '2026-11-25',
            sections: [{ section: 'Section 47', title: '[FIXTURE] Grounds of arrest', old_equivalent: 'Old Sec 50' }],
          },
        ],
      }),
    })
  );
  await page.route('**/feedback', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'received', message: 'Recorded' }),
    })
  );
  await page.route('**/ask', async (route) => {
    const body = route.request().postDataJSON();
    const q = (body?.question || '').toLowerCase();
    if (q.includes('429')) {
      return route.fulfill({ status: 429, contentType: 'application/json', body: JSON.stringify({ detail: 'Rate limit' }) });
    }
    if (q.includes('fraud') || q.includes('clarify')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_RESPONSES.needs_clarification) });
    }
    if (q.includes('traffic') || q.includes('not_covered')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_RESPONSES.not_covered_yet) });
    }
    if (q.includes('unsupported')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_RESPONSES.insufficient_evidence) });
    }
    if (q.includes('bread')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_RESPONSES.out_of_scope) });
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_RESPONSES.answered) });
  });
}

async function run() {
  const { server, url } = await startStaticServer();
  const browser = await chromium.launch({ channel: 'msedge', headless: true });

  const axeSummary = {};
  const viewports = [
    { name: '390', width: 390, height: 844 },
    { name: '768', width: 768, height: 1024 },
    { name: '1280', width: 1280, height: 800 },
  ];

  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    await setupApiMocks(page);

    // 1. Load page & verify First-Visit Disclaimer modal
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForSelector('#modal-disclaimer:not([hidden])');
    await page.click('#btn-disclaimer-accept');
    await page.waitForSelector('#modal-disclaimer', { state: 'hidden' });

    // Accessibility check on Home (Light)
    const axeHomeLight = await new AxeBuilder({ page }).analyze();
    axeSummary.homeLightViolations = axeHomeLight.violations.length;
    assert.equal(axeHomeLight.violations.length, 0, `Home Light axe violations: ${JSON.stringify(axeHomeLight.violations)}`);

    // Screenshot Home across 390, 768, 1280
    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `home_${vp.name}.png`), fullPage: true });
    }
    await page.setViewportSize({ width: 1280, height: 800 });

    // 2. Ask question -> Answered status
    await page.fill('#ask-input-home', '[FIXTURE] What are my rights if arrested?');
    await page.click('#ask-form-home button[type="submit"]');
    await page.waitForSelector('[data-status="answered"]');
    assert.ok((await page.textContent('#answer-main-col')).includes('[FIXTURE] Simple plain-language summary'));

    // Toggle Simple / Detailed
    await page.click('button.segmented-btn:has-text("Detailed")');
    assert.ok((await page.textContent('#answer-main-col')).includes('[FIXTURE] Detailed statutory explanation'));

    // Accessibility check on Answer (Light)
    const axeAnswer = await new AxeBuilder({ page }).analyze();
    axeSummary.answerLightViolations = axeAnswer.violations.length;
    assert.equal(axeAnswer.violations.length, 0, `Answer axe violations: ${JSON.stringify(axeAnswer.violations)}`);

    // Screenshot Answered across 390, 768, 1280
    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `answered_${vp.name}.png`), fullPage: true });
    }
    await page.setViewportSize({ width: 1280, height: 800 });

    // 3. Test Needs Clarification
    await page.fill('#followup-input', '[FIXTURE] How do I report fraud?');
    await page.click('#followup-form button[type="submit"]');
    await page.waitForSelector('[data-status="needs_clarification"]');
    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `needs_clarification_${vp.name}.png`), fullPage: true });
    }
    await page.setViewportSize({ width: 1280, height: 800 });

    // 4. Test Not Covered Yet
    await page.fill('#followup-input', '[FIXTURE] What is the traffic fine?');
    await page.click('#followup-form button[type="submit"]');
    await page.waitForSelector('[data-status="not_covered_yet"]');
    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `not_covered_yet_${vp.name}.png`), fullPage: true });
    }
    await page.setViewportSize({ width: 1280, height: 800 });

    // 5. Test Insufficient Evidence & Out of Scope
    await page.fill('#followup-input', '[FIXTURE] unsupported query');
    await page.click('#followup-form button[type="submit"]');
    await page.waitForSelector('[data-status="insufficient_evidence"]');

    await page.fill('#followup-input', '[FIXTURE] bread recipe');
    await page.click('#followup-form button[type="submit"]');
    await page.waitForSelector('[data-status="out_of_scope"]');

    // 6. Test Error (429 Rate Limit)
    await page.fill('#followup-input', '[FIXTURE] trigger 429');
    await page.click('#followup-form button[type="submit"]');
    await page.waitForSelector('[data-status="error"]');
    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `error_${vp.name}.png`), fullPage: true });
    }
    await page.setViewportSize({ width: 1280, height: 800 });

    // 7. Test History & Delete & Clear All
    await page.click('[data-nav="history"]');
    await page.waitForSelector('#history-list li');
    const initialCount = await page.locator('#history-list li').count();
    assert.ok(initialCount >= 4, 'History should record asked questions');
    await page.locator('#history-list li button[aria-label^="Delete"]').first().click();
    assert.equal(await page.locator('#history-list li').count(), initialCount - 1);
    await page.click('#btn-clear-history');
    await page.waitForSelector('#history-empty:not([hidden])');

    // 8. Test Coverage
    await page.click('[data-nav="coverage"]');
    await page.waitForSelector('#coverage-list article');
    assert.ok((await page.textContent('#coverage-note-text')).includes('Selected sections only'));

    // 9. Test Dark Mode + Axe check in Dark Mode
    await page.click('#btn-theme-toggle');
    const isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
    assert.equal(isDark, true);
    const axeDark = await new AxeBuilder({ page }).analyze();
    axeSummary.coverageDarkViolations = axeDark.violations.length;
    assert.equal(axeDark.violations.length, 0, `Dark mode axe violations: ${JSON.stringify(axeDark.violations)}`);

    // 10. Test Shareable ?q= parameter
    await page.goto(`${url}/?q=${encodeURIComponent('[FIXTURE] What are my rights if arrested?')}`, { waitUntil: 'networkidle' });
    await page.waitForSelector('[data-status="answered"]');

    console.log('E2E_RESULT=PASS');
    console.log('AXE_SUMMARY=' + JSON.stringify(axeSummary));
  } finally {
    await browser.close();
    server.close();
  }
}

run().catch((err) => {
  console.error('E2E_RESULT=FAIL', err);
  process.exit(1);
});
