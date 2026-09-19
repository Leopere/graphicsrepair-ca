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
