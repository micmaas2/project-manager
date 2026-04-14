/**
 * Unit tests for n8n Health Check — Idle Workflow Alert
 * Tests the Code node logic in isolation using node:vm mock context.
 *
 * Run with: /root/.nvm/versions/node/v24.12.0/bin/node artefacts/task-030/test_healthcheck_workflow.js
 */

'use strict';

const assert = require('assert');
const vm = require('vm');
const fs = require('fs');
const path = require('path');

// Load workflow JSON
const wfPath = path.join(__dirname, '../../pensieve/workflows/n8n-healthcheck.json');
const workflow = JSON.parse(fs.readFileSync(wfPath, 'utf8'));

// Helper: extract jsCode from a node by name
function getNodeCode(name) {
  const node = workflow.nodes.find(n => n.name === name);
  if (!node) throw new Error(`Node "${name}" not found`);
  return node.parameters.jsCode;
}

// Helper: run Code node in a mock n8n context
function runCode(code, inputItems, nodeDataMap) {
  const mockInput = {
    all: () => inputItems,
    first: () => inputItems[0] || { json: {} }
  };

  const mockNodeAccess = (name) => ({
    all: () => nodeDataMap[name] || [],
    first: () => (nodeDataMap[name] || [{ json: {} }])[0]
  });

  const $ = (name) => mockNodeAccess(name);
  $['input'] = mockInput;

  const context = { $input: mockInput, $ };
  const wrappedCode = `(function() { ${code} })()`;
  return vm.runInNewContext(wrappedCode, context);
}

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch (err) {
    console.error(`  ✗ ${name}`);
    console.error(`    ${err.message}`);
    failed++;
  }
}

// ─── "Time Check + Split" node ─────────────────────────────────────────────
console.log('\n[Time Check + Split]');

const timeCheckCode = getNodeCode('Time Check + Split');

test('returns workflow items during waking hours', () => {
  // Mock Intl.DateTimeFormat to return hour 10 (waking)
  const mockInput = {
    all: () => [{ json: {} }],
    first: () => ({
      json: {
        data: [
          { id: 'wf-1', name: 'My Workflow' },
          { id: 'wf-2', name: 'Another Workflow' }
        ]
      }
    })
  };
  const MockIntl = {
    DateTimeFormat: function(locale, options) {
      return { format: () => '10' };
    }
  };
  const code = timeCheckCode;
  const context = {
    $input: mockInput,
    $: () => ({ all: () => [], first: () => ({ json: {} }) }),
    Intl: MockIntl,
    parseInt: parseInt
  };
  const result = vm.runInNewContext(`(function() { ${code} })()`, context);
  assert.strictEqual(result.length, 2, 'Should return 2 workflow items');
  assert.strictEqual(result[0].json.id, 'wf-1');
  assert.strictEqual(result[1].json.name, 'Another Workflow');
});

test('returns empty array outside waking hours (02:00)', () => {
  const mockInput = {
    all: () => [{ json: {} }],
    first: () => ({
      json: { data: [{ id: 'wf-1', name: 'My Workflow' }] }
    })
  };
  const MockIntl = {
    DateTimeFormat: function() { return { format: () => '2' }; }
  };
  const result = vm.runInNewContext(`(function() { ${timeCheckCode} })()`, {
    $input: mockInput,
    $: () => ({ all: () => [] }),
    Intl: MockIntl,
    parseInt: parseInt
  });
  assert.strictEqual(result.length, 0, 'Should return empty array at 02:00');
});

test('returns empty array at exactly 23:00', () => {
  const mockInput = {
    all: () => [{ json: {} }],
    first: () => ({ json: { data: [{ id: 'wf-1', name: 'X' }] } })
  };
  const MockIntl = {
    DateTimeFormat: function() { return { format: () => '23' }; }
  };
  const result = vm.runInNewContext(`(function() { ${timeCheckCode} })()`, {
    $input: mockInput,
    $: () => ({}),
    Intl: MockIntl,
    parseInt: parseInt
  });
  assert.strictEqual(result.length, 0, 'Should return empty at 23:00 (exclusive)');
});

test('excludes health-check workflow itself by name', () => {
  const mockInput = {
    all: () => [{ json: {} }],
    first: () => ({
      json: {
        data: [
          { id: 'wf-1', name: 'Real Workflow' },
          { id: 'wf-hc', name: 'n8n Health Check \u2014 Idle Workflow Alert' }
        ]
      }
    })
  };
  const MockIntl = {
    DateTimeFormat: function() { return { format: () => '12' }; }
  };
  const result = vm.runInNewContext(`(function() { ${timeCheckCode} })()`, {
    $input: mockInput,
    $: () => ({}),
    Intl: MockIntl,
    parseInt: parseInt
  });
  assert.strictEqual(result.length, 1, 'Should exclude health-check itself');
  assert.strictEqual(result[0].json.id, 'wf-1');
});

test('excludes health-check workflow itself by UUID', () => {
  const mockInput = {
    all: () => [{ json: {} }],
    first: () => ({
      json: {
        data: [
          { id: 'wf-1', name: 'Real Workflow' },
          { id: 'b5717a69-a46c-484e-ac44-aa65e143acfd', name: 'Renamed Health Check' }
        ]
      }
    })
  };
  const MockIntl = {
    DateTimeFormat: function() { return { format: () => '12' }; }
  };
  const result = vm.runInNewContext(`(function() { ${timeCheckCode} })()`, {
    $input: mockInput,
    $: () => ({}),
    Intl: MockIntl,
    parseInt: parseInt
  });
  assert.strictEqual(result.length, 1, 'Should exclude health-check by UUID even if renamed');
  assert.strictEqual(result[0].json.id, 'wf-1');
});

// ─── "Check Idle" node ──────────────────────────────────────────────────────
console.log('\n[Check Idle]');

const checkIdleCode = getNodeCode('Check Idle');
const THREE_HOURS_AGO = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString();
const ONE_HOUR_AGO = new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString();

function runCheckIdle(execItems, wfItems) {
  const mockInput = { all: () => execItems, first: () => execItems[0] };
  const nodeData = { 'Time Check + Split': wfItems };
  const $ = (name) => ({ all: () => nodeData[name] || [], first: () => (nodeData[name] || [])[0] });
  return vm.runInNewContext(`(function() { ${checkIdleCode} })()`, {
    $input: mockInput,
    $,
    Date: Date
  });
}

test('returns idle workflow when last execution >2h ago (waking hours)', () => {
  const execItems = [{
    json: { data: [{ startedAt: THREE_HOURS_AGO, stoppedAt: THREE_HOURS_AGO }] }
  }];
  const wfItems = [{ json: { id: 'wf-1', name: 'My Workflow' } }];
  const result = runCheckIdle(execItems, wfItems);
  assert.strictEqual(result.length, 1, 'Should return 1 idle workflow');
  assert.strictEqual(result[0].json.idleWorkflows[0].name, 'My Workflow');
  assert(result[0].json.idleWorkflows[0].idleMinutes >= 180, 'Should be >= 180 idle minutes');
});

test('returns empty when last execution <2h ago', () => {
  const execItems = [{
    json: { data: [{ startedAt: ONE_HOUR_AGO, stoppedAt: ONE_HOUR_AGO }] }
  }];
  const wfItems = [{ json: { id: 'wf-1', name: 'Healthy Workflow' } }];
  const result = runCheckIdle(execItems, wfItems);
  assert.strictEqual(result.length, 0, 'Should return empty for healthy workflow');
});

test('skips workflow with no executions yet', () => {
  const execItems = [{ json: { data: [] } }];
  const wfItems = [{ json: { id: 'wf-new', name: 'New Workflow' } }];
  const result = runCheckIdle(execItems, wfItems);
  assert.strictEqual(result.length, 0, 'Should skip new workflow with no executions');
});

test('skips workflow on HTTP error', () => {
  const execItems = [{ json: { error: true, message: 'Not found' } }];
  const wfItems = [{ json: { id: 'wf-err', name: 'Error Workflow' } }];
  const result = runCheckIdle(execItems, wfItems);
  assert.strictEqual(result.length, 0, 'Should skip on HTTP error');
});

test('handles multiple workflows — only idle ones returned', () => {
  const execItems = [
    { json: { data: [{ startedAt: THREE_HOURS_AGO }] } },  // idle
    { json: { data: [{ startedAt: ONE_HOUR_AGO }] } },     // healthy
    { json: { data: [] } }                                   // new - no executions
  ];
  const wfItems = [
    { json: { id: 'wf-1', name: 'Idle One' } },
    { json: { id: 'wf-2', name: 'Healthy One' } },
    { json: { id: 'wf-3', name: 'New One' } }
  ];
  const result = runCheckIdle(execItems, wfItems);
  assert.strictEqual(result.length, 1, 'Only 1 idle workflow should be returned');
  assert.strictEqual(result[0].json.idleWorkflows[0].name, 'Idle One');
});

test('skips item when startedAt is null/missing', () => {
  const execItems = [{ json: { data: [{ startedAt: null, stoppedAt: null }] } }];
  const wfItems = [{ json: { id: 'wf-x', name: 'No Timestamp Wf' } }];
  const result = runCheckIdle(execItems, wfItems);
  assert.strictEqual(result.length, 0, 'Should skip if no timestamp available');
});

test('returns empty array on exec/wf length mismatch (stops chain safely)', () => {
  const execItems = [
    { json: { data: [{ startedAt: THREE_HOURS_AGO }] } },
    { json: { data: [{ startedAt: THREE_HOURS_AGO }] } }  // extra item
  ];
  const wfItems = [{ json: { id: 'wf-1', name: 'Only One' } }];
  const result = runCheckIdle(execItems, wfItems);
  assert.strictEqual(result.length, 0, 'Should return empty array on mismatch — stops chain without spurious alert');
});

// ─── "Format Alert" node ─────────────────────────────────────────────────
console.log('\n[Format Alert]');

const formatCode = getNodeCode('Format Alert');

test('formats single idle workflow correctly', () => {
  const idleWorkflows = [{
    name: 'My Workflow',
    id: 'wf-1',
    lastRun: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    idleMinutes: 180
  }];
  const mockInput = { all: () => [{ json: { idleWorkflows } }], first: () => ({ json: { idleWorkflows } }) };
  const $ = () => ({ all: () => [], first: () => ({ json: {} }) });
  const result = vm.runInNewContext(`(function() { ${formatCode} })()`, {
    $input: mockInput, $, Date: Date
  });
  assert.strictEqual(result.length, 1);
  const text = result[0].json.text;
  assert(text.includes('n8n health check'), 'Should include header');
  assert(text.includes('My Workflow'), 'Should include workflow name');
  assert(text.includes('3h'), 'Should include hours');
  assert(!text.includes('workflows'), 'Should say "workflow" (singular)');
});

test('formats multiple idle workflows with plural', () => {
  const idleWorkflows = [
    { name: 'Wf One', id: 'wf-1', lastRun: null, idleMinutes: 130 },
    { name: 'Wf Two', id: 'wf-2', lastRun: null, idleMinutes: 200 }
  ];
  const mockInput = { all: () => [{ json: { idleWorkflows } }], first: () => ({ json: { idleWorkflows } }) };
  const $ = () => ({});
  const result = vm.runInNewContext(`(function() { ${formatCode} })()`, {
    $input: mockInput, $, Date: Date
  });
  const text = result[0].json.text;
  assert(text.includes('2 workflows'), 'Should say "2 workflows"');
  assert(text.includes('Wf One'), 'Should include first workflow');
  assert(text.includes('Wf Two'), 'Should include second workflow');
});

// ─── Workflow structure validation ────────────────────────────────────────
console.log('\n[Workflow Structure]');

test('workflow has required id (UUID format)', () => {
  assert.match(workflow.id, /^[0-9a-f-]{36}$/, 'Workflow ID must be UUID');
});

test('workflow has all 7 required nodes', () => {
  const expectedNodes = [
    'Schedule Trigger', 'Get Active Workflows', 'Time Check + Split',
    'Get Last Execution', 'Check Idle', 'Format Alert', 'Send Alert'
  ];
  for (const name of expectedNodes) {
    const found = workflow.nodes.find(n => n.name === name);
    assert(found, `Missing node: ${name}`);
  }
});

test('all 6 connections are present', () => {
  const expected = [
    'Schedule Trigger', 'Get Active Workflows', 'Time Check + Split',
    'Get Last Execution', 'Check Idle', 'Format Alert'
  ];
  for (const name of expected) {
    assert(workflow.connections[name], `Missing connection from: ${name}`);
  }
});

test('Get Last Execution has continueOnFail: true', () => {
  const node = workflow.nodes.find(n => n.name === 'Get Last Execution');
  assert.strictEqual(node.continueOnFail, true, 'continueOnFail must be true');
});

test('Telegram node uses correct chat_id and credential', () => {
  const node = workflow.nodes.find(n => n.name === 'Send Alert');
  assert.strictEqual(node.parameters.chatId, '7761755508');
  assert.strictEqual(node.credentials.telegramApi.id, 'NB55cLp798oiazqt');
});

test('Schedule Trigger set to 15-minute interval', () => {
  const node = workflow.nodes.find(n => n.name === 'Schedule Trigger');
  const interval = node.parameters.rule.interval[0];
  assert.strictEqual(interval.field, 'minutes');
  assert.strictEqual(interval.minutesInterval, 15);
});

// ─── Results ──────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(50)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
if (failed > 0) {
  console.log('FAIL');
  process.exit(1);
} else {
  console.log('PASS');
}
