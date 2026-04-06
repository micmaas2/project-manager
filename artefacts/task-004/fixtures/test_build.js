// Test harness for node-build-note logic
// Extracted from /opt/claude/pensieve/workflows/telegram-capture.json

const fs = require('fs');
const path = require('path');
const os = require('os');

let passed = 0;
let failed = 0;
const results = [];

// We redirect VAULT to a temp directory to avoid writing to /opt/obsidian-vault
const REAL_VAULT = '/opt/obsidian-vault';
const TEMP_VAULT = fs.mkdtempSync(path.join(os.tmpdir(), 'pensieve-test-'));

function runBuildCode(claudeData, telegramMessage) {
  const $input = { first: () => ({ json: claudeData }) };
  const $ = () => ({ first: () => ({ json: { message: { text: telegramMessage, caption: null, chat: { id: 12345 } } } }) });

  // Extracted jsCode from node-build-note, with VAULT patched to temp dir
  const claudeDataLocal = $input.first().json;
  const triggerData = $().first().json;

  const now = new Date('2026-04-05T12:00:00.000Z'); // Fixed date for reproducibility
  const dateStr = now.toISOString().split('T')[0];

  function slugify(text) {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\.+/g, '')
      .trim()
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 50);
  }

  const slug = slugify(claudeDataLocal.title) || 'untitled';
  const filename = dateStr + '-' + slug + '.md';

  if (!/^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$/.test(filename)) {
    throw new Error('Invalid filename: ' + filename);
  }

  // Use TEMP_VAULT instead of /opt/obsidian-vault
  const VAULT = TEMP_VAULT;
  const CATEGORY_FOLDERS = { Research: VAULT + '/Research', Ideas: VAULT + '/Ideas', Links: VAULT + '/Links', Inbox: VAULT + '/Inbox' };
  const categoryFolder = CATEGORY_FOLDERS[claudeDataLocal.category] || (VAULT + '/Inbox');

  const topicSlug = claudeDataLocal.topic || 'general';
  const topicFolderName = topicSlug.charAt(0).toUpperCase() + topicSlug.slice(1);
  const topicFolder = categoryFolder + '/' + topicFolderName;
  const filepath = topicFolder + '/' + filename;

  // Path traversal check (uses VAULT variable, which is TEMP_VAULT here)
  if (!filepath.startsWith(VAULT + '/')) {
    throw new Error('Path traversal detected: ' + filepath);
  }

  fs.mkdirSync(topicFolder, { recursive: true });

  const tagsYaml = claudeDataLocal.tags.join(', ');
  const keyPointsBullets = claudeDataLocal.key_points.map(p => '- ' + p).join('\n');
  const rawMessage = triggerData.message.text || triggerData.message.caption || '(no text)';

  const noteContent = '---\ntitle: "' + claudeDataLocal.title + '"\ndate: ' + dateStr + '\ncategory: ' + claudeDataLocal.category + '\ntopic: ' + claudeDataLocal.topic + '\nsource: ' + claudeDataLocal.source_type + '\nchannel: telegram\ntags: [' + tagsYaml + ']\n---\n\n## Summary\n\n' + claudeDataLocal.summary + '\n\n' + keyPointsBullets + '\n\n## Analysis\n\n' + claudeDataLocal.analysis + '\n\n---\n\n## Raw capture\n\n' + rawMessage + '\n';

  return [{ json: { filename, filepath, noteContent, title: claudeDataLocal.title, category: claudeDataLocal.category, topic: claudeDataLocal.topic } }];
}

// Version with real VAULT for path traversal test
function runBuildCodeRealVault(claudeData, telegramMessage) {
  const $input = { first: () => ({ json: claudeData }) };

  const claudeDataLocal = $input.first().json;

  const now = new Date('2026-04-05T12:00:00.000Z');
  const dateStr = now.toISOString().split('T')[0];

  function slugify(text) {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\.+/g, '')
      .trim()
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 50);
  }

  const slug = slugify(claudeDataLocal.title) || 'untitled';
  const filename = dateStr + '-' + slug + '.md';

  if (!/^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$/.test(filename)) {
    throw new Error('Invalid filename: ' + filename);
  }

  const VAULT = REAL_VAULT;
  const CATEGORY_FOLDERS = { Research: VAULT + '/Research', Ideas: VAULT + '/Ideas', Links: VAULT + '/Links', Inbox: VAULT + '/Inbox' };
  const categoryFolder = CATEGORY_FOLDERS[claudeDataLocal.category] || (VAULT + '/Inbox');

  const topicSlug = claudeDataLocal.topic || 'general';
  const topicFolderName = topicSlug.charAt(0).toUpperCase() + topicSlug.slice(1);
  const topicFolder = categoryFolder + '/' + topicFolderName;
  const filepath = topicFolder + '/' + filename;

  // Path traversal check - does NOT create dir or write, just checks path
  if (!filepath.startsWith(VAULT + '/')) {
    throw new Error('Path traversal detected: ' + filepath);
  }

  return [{ json: { filename, filepath, noteContent: '', title: claudeDataLocal.title, category: claudeDataLocal.category, topic: claudeDataLocal.topic } }];
}

function assert(name, condition, actual, expected) {
  if (condition) {
    console.log(`  PASS: ${name}`);
    passed++;
    results.push({ name, result: 'PASS' });
  } else {
    console.log(`  FAIL: ${name}`);
    console.log(`    Expected: ${JSON.stringify(expected)}`);
    console.log(`    Actual:   ${JSON.stringify(actual)}`);
    failed++;
    results.push({ name, result: 'FAIL', actual, expected });
  }
}

// ---- Test 5: folder path is Category/Topic/filename ----
console.log('\nTest 5 — Build: folder path is Category/Topic/filename');
try {
  const claudeData = {
    title: "Test Article About Claude",
    summary: "A test article about Claude AI.",
    key_points: ["Claude is an AI assistant", "It is made by Anthropic"],
    analysis: "This is a test article to verify path construction.",
    tags: ["ai", "claude", "anthropic"],
    topic: "ai",
    category: "Research",
    source_type: "article"
  };

  const result = runBuildCode(claudeData, "Test message about Claude");
  const out = result[0].json;

  console.log(`  filepath: ${out.filepath}`);

  // filepath should contain Research/Ai/2026- and end in .md
  // Note: topicFolderName is topic with first char uppercased, so "ai" -> "Ai"
  assert('filepath contains category', out.filepath.includes('/Research/'), out.filepath, 'contains /Research/');
  assert('filepath contains topic folder', out.filepath.includes('/Ai/'), out.filepath, 'contains /Ai/');
  assert('filepath contains date prefix 2026-', out.filepath.includes('/2026-'), out.filepath, 'contains /2026-');
  assert('filepath ends with .md', out.filepath.endsWith('.md'), out.filepath, 'ends with .md');
  assert('filepath stays within vault', out.filepath.startsWith(TEMP_VAULT + '/'), out.filepath, `starts with ${TEMP_VAULT}/`);

  // Verify the file structure: VAULT/Research/Ai/2026-04-05-test-article-about-claude.md
  const parts = out.filepath.replace(TEMP_VAULT + '/', '').split('/');
  assert('path has 3 parts: category/topic/filename', parts.length === 3, parts.length, 3);
  assert('first part is category', parts[0] === 'Research', parts[0], 'Research');
  assert('second part is topic', parts[1] === 'Ai', parts[1], 'Ai');
  assert('filename matches pattern', /^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$/.test(parts[2]), parts[2], 'YYYY-MM-DD-slug.md');

  console.log('  => Test 5 COMPLETE');
} catch (e) {
  console.log(`  FAIL (exception): ${e.message}`);
  failed++;
  results.push({ name: 'Test 5 (exception)', result: 'FAIL', actual: e.message, expected: 'no error' });
}

// ---- Test 6: path traversal rejected ----
console.log('\nTest 6 — Build: path traversal rejected');

// First, understand what happens to "../../../etc/passwd" as a topic
// In Parse node: toLowerCase().replace(/[^a-z0-9-]/g, '') removes slashes and dots
// "../../../etc/passwd" -> "etcpasswd"
// Then TOPIC_PATTERN /^[a-z0-9-]+$/ matches "etcpasswd" -> topic stays "etcpasswd"
// In Build node: topicFolderName = "Etcpasswd"
// filepath = VAULT/Research/Etcpasswd/2026-04-05-path-traversal-test.md
// This starts with VAULT + '/' so no path traversal is detected.

// The sanitization in Parse prevents path traversal from reaching Build.
// Let's verify this behavior end-to-end.

try {
  // Simulate what Parse node produces after sanitizing "../../../etc/passwd"
  const maliciousTopic = "../../../etc/passwd";
  const sanitizedTopic = maliciousTopic.toLowerCase().replace(/[^a-z0-9-]/g, '').substring(0, 30);
  const TOPIC_PATTERN = /^[a-z0-9-]+$/;
  const finalTopic = TOPIC_PATTERN.test(sanitizedTopic) ? sanitizedTopic : 'general';

  console.log(`  Input topic: "${maliciousTopic}"`);
  console.log(`  After sanitization: "${sanitizedTopic}"`);
  console.log(`  Final topic passed to build: "${finalTopic}"`);

  const claudeData = {
    title: "Path Traversal Test",
    summary: "Test for path traversal.",
    key_points: ["Security test"],
    analysis: "Testing path traversal prevention.",
    tags: ["security"],
    topic: finalTopic,  // This is what Parse produces after sanitizing
    category: "Research",
    source_type: "article"
  };

  const result = runBuildCodeRealVault(claudeData, "Test message");
  const out = result[0].json;

  console.log(`  filepath: ${out.filepath}`);

  assert('filepath starts with VAULT (no path traversal)', out.filepath.startsWith(REAL_VAULT + '/'), out.filepath, `starts with ${REAL_VAULT}/`);
  assert('filepath does not contain ../..', !out.filepath.includes('..'), out.filepath, 'no ../.. in path');
  assert('topic sanitized away traversal chars', !finalTopic.includes('/') && !finalTopic.includes('.'), finalTopic, 'no / or . in topic');

  console.log('  => Test 6 COMPLETE');
} catch (e) {
  if (e.message && e.message.startsWith('Path traversal detected')) {
    // This would also be a PASS - path traversal was detected and blocked
    console.log(`  PASS: path traversal correctly detected and rejected: ${e.message}`);
    passed++;
    results.push({ name: 'Test 6 path traversal blocked', result: 'PASS' });
  } else {
    console.log(`  FAIL (unexpected exception): ${e.message}`);
    failed++;
    results.push({ name: 'Test 6 (exception)', result: 'FAIL', actual: e.message, expected: 'no error or path traversal error' });
  }
}

// Cleanup temp vault
try { fs.rmSync(TEMP_VAULT, { recursive: true }); } catch (e) {}

// Summary
console.log('\n=============================');
console.log(`Build tests: ${passed} passed, ${failed} failed`);
console.log('=============================\n');

module.exports = { passed, failed, results };
