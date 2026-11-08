const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadNotomoLoader() {
  const source = fs.readFileSync(path.join(__dirname, '..', 'site/assets/notomo-loader.js'), 'utf8');
  const context = {
    window: {},
    document: { currentScript: null },
    location: { hostname: 'graphicsrepair.ca' },
  };
  vm.runInNewContext(source, context, { filename: 'site/assets/notomo-loader.js' });
  return context.notomoSiteId;
}

test('maps public hosts to dedicated Notomo properties', () => {
  const siteId = loadNotomoLoader();
  assert.equal(siteId('graphicsrepair.ca'), 'graphicsrepair.ca');
  assert.equal(siteId('www.graphicsrepair.ca'), 'graphicsrepair.ca');
  assert.equal(siteId('fixgpu.ca'), 'graphicsrepair.ca');
  assert.equal(siteId('gpufix.ca'), 'graphicsrepair.ca');
  assert.equal(siteId('graphicsrepair.com'), 'graphicsrepair.com');
  assert.equal(siteId('www.graphicsrepair.com'), 'graphicsrepair.com');
});

test('contact diagnostics allow only finite metadata and flush once after tracker load', async () => {
  const trackers = [];
  const captured = [];
  const context = {
    window: {}, location: { hostname: 'graphicsrepair.ca' },
    document: {
      currentScript: {
        dataset: { trackerSrc: 'https://notomo.colinknapp.com/n.js', trackerIntegrity: 'fixture' },
        after: tracker => trackers.push(tracker),
      },
      createElement: () => ({ dataset: {}, addEventListener: (_event, callback) => { context.onLoad = callback; } }),
    },
    fetch: async () => ({ ok: true, json: async () => ({}) }),
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../site/assets/notomo-loader.js'), 'utf8'), context);
  const safe = { component: 'contact_form', form_id: 'graphics_card_repair_quote', stage: 'submit', status: 503, code: 'submit_http:FORM_PROOF_UNAVAILABLE' };
  context.window.reportNotomoIssue('contact_form_submission_failed', { ...safe, token: 'PRIVATE', message: 'PRIVATE' });
  context.window.reportNotomoIssue('PRIVATE', safe);
  await new Promise(resolve => setImmediate(resolve));
  context.window.notomo = { captureError: (error, metadata) => captured.push([error.message, JSON.parse(JSON.stringify(metadata))]) };
  context.onLoad();
  context.onLoad();
  assert.deepEqual(captured, [['contact_form_submission_failed', safe]]);
  context.window.reportNotomoIssue('contact_form_submission_failed', { component: 'PRIVATE', form_id: 'PRIVATE', stage: 'PRIVATE', status: 'PRIVATE', code: 'submit_http:PRIVATE' });
  assert.deepEqual(captured[1][1], { component: 'contact_form', form_id: 'unknown', stage: 'submit', status: 0, code: 'unknown' });
  assert.equal(JSON.stringify(captured).includes('PRIVATE'), false);
  assert.equal(trackers.length, 1);
});
