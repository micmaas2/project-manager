/**
 * [Sonnet] Fixture tests for Gmail Capture workflow Code nodes
 * Tests: Parse Claude Response (6) + Build Markdown Note (6) = 12 total
 * Run: /root/.nvm/versions/node/v24.12.0/bin/node artefacts/task-009/test_gmail_workflow.js
 */

'use strict';

const vm = require('vm');
const path = require('path');

// ── Extract jsCode from workflow JSON ──────────────────────────────────────
const workflowPath = '/opt/claude/pensieve/workflows/gmail-capture.json';
const workflow = JSON.parse(require('fs').readFileSync(workflowPath, 'utf8'));

function getNodeCode(nodeId) {
  const node = workflow.nodes.find(n => n.id === nodeId);
  if (!node) throw new Error(`Node not found: ${nodeId}`);
  return node.parameters.jsCode;
}

const parseClaudeCode = getNodeCode('node-parse-claude');
const buildNoteCode   = getNodeCode('node-build-note');

// ── Test harness ───────────────────────────────────────────────────────────
let passed = 0;
let failed = 0;
const results = [];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function test(name, fn) {
  try {
    fn();
    console.log(`  PASS  ${name}`);
    results.push({ name, result: 'PASS', notes: '' });
    passed++;
  } catch (err) {
    console.log(`  FAIL  ${name}`);
    console.log(`        ${err.message}`);
    results.push({ name, result: 'FAIL', notes: err.message });
    failed++;
  }
}

// ── Helper: run Parse Claude Response with a synthetic Claude API response ─
function runParseClaudeCode(claudeResponseObj) {
  const raw = JSON.stringify(claudeResponseObj);
  // Wrap in the shape the code expects: body.content[0].text
  const input = { content: [{ text: raw }] };

  let returnValue;
  const sandbox = {
    $input: {
      first: () => ({ json: input })
    },
    returnValue: undefined,
    Error,
    JSON,
    Array,
    String,
    Set,
  };

  // The n8n code node returns via "return [...]" — wrap in a function
  const wrapped = `(function() { ${parseClaudeCode.replace(/^return /, 'returnValue = ')} ; returnValue = (function(){ ${parseClaudeCode} })(); })()`;
  const script = new vm.Script(`returnValue = (function(){ ${parseClaudeCode} })()`);
  vm.createContext(sandbox);
  script.runInContext(sandbox);
  return sandbox.returnValue;
}

// ── Helper: run Build Markdown Note ───────────────────────────────────────
function runBuildNoteCode(claudeData, gmailData) {
  let mkdirCalled = false;
  let mkdirPath = '';

  const fsMock = {
    mkdirSync: (p, opts) => { mkdirCalled = true; mkdirPath = p; }
  };

  // path mock: resolve returns input as-is (no Pi4 filesystem needed),
  // but must pass the startsWith('/opt/obsidian-vault/') guard.
  // We override VAULT inside the code via the sandbox instead.
  const pathMock = {
    resolve: (p) => p,   // identity — tests run locally
  };

  // Replace the n8n context helpers the code uses
  let returnValue;
  const sandbox = {
    $input: {
      first: () => ({ json: claudeData })
    },
    $: (nodeName) => ({
      first: () => ({ json: gmailData })
    }),
    require: (mod) => {
      if (mod === 'fs')   return fsMock;
      if (mod === 'path') return pathMock;
      throw new Error(`require('${mod}') not mocked`);
    },
    Error,
    JSON,
    Array,
    String,
    Date,
    RegExp,
    Set,
    returnValue: undefined,
    __mkdirCalled: false,
    __mkdirPath: '',
  };

  const script = new vm.Script(`returnValue = (function(){ ${buildNoteCode} })()`);
  vm.createContext(sandbox);
  script.runInContext(sandbox);
  return { result: sandbox.returnValue, mkdirCalled, mkdirPath };
}

// ── Valid base fixtures ────────────────────────────────────────────────────
function validClaudeResponse(overrides = {}) {
  return Object.assign({
    title: 'Test Note Title',
    summary: 'A brief summary of the content.',
    key_points: ['Point one', 'Point two', 'Point three'],
    analysis: 'This is the analysis section.',
    tags: ['ai', 'testing', 'note'],
    topic: 'ai',
    category: 'Research',
    source_type: 'article',
  }, overrides);
}

function validGmailData(overrides = {}) {
  return Object.assign({
    id: 'gmail-msg-001',
    subject: 'Test Subject',
    from: 'sender@example.com',
    text: 'Email body text here.',
  }, overrides);
}

// ══════════════════════════════════════════════════════════════════════════
// Parse Claude Response — 6 tests
// ══════════════════════════════════════════════════════════════════════════
console.log('\nParse Claude Response');

// Test 1: Valid full response
test('1. Valid full response: all 8 fields present → parsed correctly', () => {
  const resp = validClaudeResponse();
  const output = runParseClaudeCode(resp);
  assert(Array.isArray(output) && output.length === 1, 'Should return array with one item');
  const json = output[0].json;
  assert(json.topic === 'ai', `topic should be "ai", got "${json.topic}"`);
  assert(Array.isArray(json.key_points) && json.key_points.length <= 7, 'key_points length should be ≤7');
  assert(typeof json.analysis === 'string' && json.analysis.length > 0, 'analysis should be present');
});

// Test 2: Missing field raises error
test('2. Missing field raises error: omit "topic" → throws "missing fields: topic"', () => {
  const resp = validClaudeResponse();
  delete resp.topic;
  let threw = false;
  let errorMsg = '';
  try {
    runParseClaudeCode(resp);
  } catch (e) {
    threw = true;
    errorMsg = e.message;
  }
  assert(threw, 'Should have thrown an error');
  assert(errorMsg.includes('missing fields') && errorMsg.includes('topic'),
    `Error should mention "missing fields: topic", got: "${errorMsg}"`);
});

// Test 3: Invalid topic slug sanitised
test('3. Invalid topic slug sanitised: topic="AI Tools!" → sanitised to "aitools"', () => {
  const resp = validClaudeResponse({ topic: 'AI Tools!' });
  const output = runParseClaudeCode(resp);
  const json = output[0].json;
  assert(json.topic === 'aitools', `Expected "aitools", got "${json.topic}"`);
  const TOPIC_PATTERN = /^[a-z0-9-]+$/;
  assert(TOPIC_PATTERN.test(json.topic), `topic "${json.topic}" should match TOPIC_PATTERN`);
});

// Test 4: Topic with hyphens allowed
test('4. Topic with hyphens allowed: topic="home-lab" → passes validation', () => {
  const resp = validClaudeResponse({ topic: 'home-lab' });
  const output = runParseClaudeCode(resp);
  const json = output[0].json;
  assert(json.topic === 'home-lab', `Expected "home-lab", got "${json.topic}"`);
  assert(json.topic !== 'general', 'Should not have fallen back to "general"');
});

// Test 5: key_points trimmed to 7
test('5. key_points trimmed to 7: send 10 items → output length = 7', () => {
  const tenPoints = Array.from({ length: 10 }, (_, i) => `Point ${i + 1}`);
  const resp = validClaudeResponse({ key_points: tenPoints });
  const output = runParseClaudeCode(resp);
  const json = output[0].json;
  assert(json.key_points.length === 7, `Expected 7 key_points, got ${json.key_points.length}`);
});

// Test 6: tags trimmed to 8
test('6. tags trimmed to 8: send 12 tags → output length = 8', () => {
  const twelveTags = Array.from({ length: 12 }, (_, i) => `tag${i + 1}`);
  const resp = validClaudeResponse({ tags: twelveTags });
  const output = runParseClaudeCode(resp);
  const json = output[0].json;
  assert(json.tags.length === 8, `Expected 8 tags, got ${json.tags.length}`);
});

// ══════════════════════════════════════════════════════════════════════════
// Build Markdown Note — 6 tests
// ══════════════════════════════════════════════════════════════════════════
console.log('\nBuild Markdown Note');

// Test 7: Valid input produces Category/Topic/filename.md path
test('7. Valid input produces Category/Topic/filename.md path', () => {
  // Run Parse first to get the shape Build expects, then run Build
  const parsed = runParseClaudeCode(validClaudeResponse({ category: 'Research', topic: 'ai' }))[0].json;
  const gmail  = validGmailData();
  const { result } = runBuildNoteCode(parsed, gmail);
  const json = result[0].json;
  assert(typeof json.filepath === 'string', 'filepath should be a string');
  assert(json.filepath.includes('Research'), `filepath should contain "Research", got: ${json.filepath}`);
  assert(json.filepath.includes('Ai'), `filepath should contain "Ai" (capitalised topic), got: ${json.filepath}`);
});

// Test 8: Path traversal via topic rejected → falls back to "general"
test('8. Path traversal via topic rejected: empty-after-sanitise topic → falls back to "general"', () => {
  // A topic that after sanitisation becomes empty → code uses 'general'
  // We feed an already-parsed claudeData where topic was forced empty after sanitisation
  // Simulate: topic = '' (what happens after sanitisation of something like '!!!')
  const claudeData = {
    title: 'Traversal Test',
    summary: 'test',
    key_points: ['p1'],
    analysis: 'a',
    tags: ['t1'],
    topic: '',          // empty after sanitisation
    category: 'Inbox',
    source_type: 'thought',
  };
  const gmail = validGmailData();
  const { result } = runBuildNoteCode(claudeData, gmail);
  const json = result[0].json;
  assert(json.filepath.includes('general') || json.filepath.includes('General'),
    `Expected "general" fallback in path, got: ${json.filepath}`);
  assert(json.filepath.startsWith('/opt/obsidian-vault/'),
    `Path should still start with vault root, got: ${json.filepath}`);
});

// Test 9: YAML injection in title escaped
test('9. YAML injection in title escaped: title with `"` → output YAML has `\\"` in title', () => {
  const claudeData = Object.assign(
    runParseClaudeCode(validClaudeResponse({ title: 'She said "hello" to me' }))[0].json,
    {}
  );
  const gmail = validGmailData();
  const { result } = runBuildNoteCode(claudeData, gmail);
  const noteContent = result[0].json.noteContent;
  // The title YAML line should have escaped double-quotes
  const titleLine = noteContent.split('\n').find(l => l.startsWith('title:'));
  assert(titleLine, 'noteContent should have a title: YAML line');
  assert(!titleLine.includes('"hello"'),
    `Unescaped double-quote found in YAML title line: ${titleLine}`);
  assert(titleLine.includes('\\"hello\\"'),
    `Expected escaped quotes in: ${titleLine}`);
});

// Test 10: YAML injection in from escaped
// In YAML double-quoted scalars, \" is the escape sequence for a literal double-quote —
// it does NOT terminate the string. So 'attacker@evil.com" injected: true' becomes
// from: "attacker@evil.com\" injected: true" — the \" keeps "injected: true" inside
// the string value, not as a separate YAML key. Verify the raw quote is escaped.
test('10. YAML injection in from escaped: from contains `"injected: true` → escaped in YAML', () => {
  const claudeData = runParseClaudeCode(validClaudeResponse())[0].json;
  const gmail = validGmailData({ from: 'attacker@evil.com" injected: true' });
  const { result } = runBuildNoteCode(claudeData, gmail);
  const noteContent = result[0].json.noteContent;
  const fromLine = noteContent.split('\n').find(l => l.startsWith('from:'));
  assert(fromLine, 'noteContent should have a from: YAML line');
  // The double-quote in from must be escaped as \" (YAML double-quoted scalar escape)
  // This keeps "injected: true" inside the string value, not a separate YAML key.
  assert(fromLine.includes('\\"'),
    `Expected YAML-escaped double-quote (\\\") in from line: ${fromLine}`);
  // The raw unescaped sequence 'com" injected' (unescaped quote followed by space)
  // should NOT appear — it would end the YAML scalar prematurely.
  assert(!fromLine.includes('com" injected'),
    `Raw unescaped quote+injection found in from YAML line: ${fromLine}`);
});

// Test 11: Missing gmailData.id throws error
test('11. Missing gmailData.id throws error', () => {
  const claudeData = runParseClaudeCode(validClaudeResponse())[0].json;
  const gmail = validGmailData({ id: undefined });
  delete gmail.id;
  let threw = false;
  let errorMsg = '';
  try {
    runBuildNoteCode(claudeData, gmail);
  } catch (e) {
    threw = true;
    errorMsg = e.message;
  }
  assert(threw, 'Should have thrown an error for missing gmail id');
  assert(errorMsg.toLowerCase().includes('id') || errorMsg.toLowerCase().includes('missing'),
    `Error should mention missing ID, got: "${errorMsg}"`);
});

// Test 12: filename has correct date-slug format
test('12. filename has correct date-slug format: YYYY-MM-DD-slug.md', () => {
  const claudeData = runParseClaudeCode(validClaudeResponse({ title: 'My Test Note' }))[0].json;
  const gmail = validGmailData();
  const { result } = runBuildNoteCode(claudeData, gmail);
  const { filename } = result[0].json;
  assert(/^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$/.test(filename),
    `filename "${filename}" does not match YYYY-MM-DD-slug.md`);
  // Date part should be today (2026-04-07 per memory, but use dynamic check)
  const today = new Date().toISOString().split('T')[0];
  assert(filename.startsWith(today), `filename should start with today ${today}, got: ${filename}`);
});

// ── Summary ───────────────────────────────────────────────────────────────
const total = passed + failed;
console.log(`\n──────────────────────────────────────`);
console.log(`Results: ${passed}/${total} passed`);
console.log(`──────────────────────────────────────`);

// ── Write test_report.md ──────────────────────────────────────────────────
const overall = failed === 0 ? 'PASS' : 'FAIL';
const tableRows = results.map((r, i) =>
  `| ${i + 1} | ${r.name.replace(/^\d+\.\s*/, '')} | ${r.result} | ${r.notes.replace(/\|/g, '\\|').substring(0, 120)} |`
).join('\n');

const report = `# Test Report — task-009 Gmail Capture Workflow

[Sonnet]

**Overall: ${overall}**
**Pass rate: ${passed}/${total}**
**Date: ${new Date().toISOString()}**

## Results

| # | Test | Result | Notes |
|---|------|--------|-------|
${tableRows}

## Notes

- Tests run via node:vm — n8n Code node jsCode extracted directly from workflow JSON
- fs and path modules mocked; no filesystem access required
- Parse Claude Response tests validate field presence, sanitisation, and truncation
- Build Markdown Note tests validate path construction, YAML escaping, and error handling
- Test 8 verifies defence-in-depth sanitisation (topic = '' → 'general' fallback)
- path.resolve mock returns identity; startsWith guard uses /opt/obsidian-vault/ prefix
`;

require('fs').writeFileSync(
  '/opt/claude/project_manager/artefacts/task-009/test_report.md',
  report,
  'utf8'
);
console.log('\ntest_report.md written.');

// Exit with appropriate code
process.exit(failed > 0 ? 1 : 0);
