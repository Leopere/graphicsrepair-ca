const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function loadLeadHelpers() {
  const source = fs.readFileSync(path.join(__dirname, '..', 'site/assets/site.js'), 'utf8');
  const context = {
    console,
    TextEncoder,
    module: { exports: {} },
    document: {
      body: { dataset: { locale: 'en' } },
      documentElement: { lang: 'en-CA' },
      querySelector: () => null,
      querySelectorAll: () => [],
    },
    location: { pathname: '/' },
    localStorage: { getItem: () => '', setItem: () => {} },
    navigator: { languages: ['en-CA'], language: 'en-CA' },
    window: {},
  };
  vm.runInNewContext(source, context, { filename: 'site/assets/site.js' });
  return context.module.exports;
}

function field(value, extra = {}) {
  return { value, ...extra };
}

function fakeForm({ message, province, returnCountry = 'CA', languagePreference }) {
  const elements = {
    name: field('Alex Customer'),
    email: field('alex@example.com'),
    website: field(''),
    start_time: field('1723900000'),
    phone: field(''),
    model: field('ASUS RTX 3080'),
    request_type: field('Repair quote'),
    service_type: field('Mail-In'),
    mailing_address: field('123 Main Street'),
    unit_number: field('4'),
    return_country: field(returnCountry),
    province: field(province),
    ownership_confirmed: field('', { checked: false }),
    international_shipping_ack: field('', { checked: false }),
    message: field(message),
  };
  if (languagePreference !== undefined) {
    elements.english_support_preference = field(languagePreference);
  }
  return { elements };
}

const { buildLeadPayload, normalizeSiteLanguage, sendLeadPayload } = loadLeadHelpers();

async function sendToFormApi(payload) {
  let request;
  await sendLeadPayload(payload, {
    form_proof_token: 'test-proof',
    form_proof_counter: 42,
  }, async (url, options) => {
    request = { url, options };
    return { ok: true, json: async () => ({ ok: true }) };
  });
  assert.equal(request.url, 'https://forms.motherboardrepair.ca/api/submit');
  assert.equal(request.options.method, 'POST');
  return JSON.parse(request.options.body);
}

test('French Quebec lead preserves the original message and sends French/location metadata', async () => {
  const originalMessage = 'Bonjour!\n\nMa carte RTX <ne démarre plus>.  Pouvez-vous\nme donner un devis?';
  const form = fakeForm({
    message: originalMessage,
    province: 'Québec',
    languagePreference: 'no',
  });
  const payload = buildLeadPayload(form, {
    e164: () => '+15145550123',
    profile: () => 'CA',
  }, 'fr_CA');
  const leadApiBody = await sendToFormApi(payload);

  assert.equal(leadApiBody.message, originalMessage);
  assert.equal(normalizeSiteLanguage('fr_CA'), 'fr-CA');
  assert.equal(leadApiBody.extra_fields.service_type, 'Mail-In');
  assert.equal(leadApiBody.extra_fields.province, 'Québec');
  assert.equal(leadApiBody.extra_fields.country, 'CA');
  assert.equal(leadApiBody.extra_fields.site_language, 'fr-CA');
  assert.equal(leadApiBody.extra_fields.english_support_preference, 'no');
  assert.doesNotMatch(leadApiBody.message, /Request details:|Province:|Return country:/);
});

test('English Quebec lead preserves the original message without English duplication or preference metadata', async () => {
  const originalMessage = 'Hello!\n\nMy RTX card has <no display output>.  Please send a quote.';
  const form = fakeForm({
    message: originalMessage,
    province: 'QC',
  });
  const payload = buildLeadPayload(form, {
    e164: () => '+15145550123',
    profile: () => 'CA',
  }, 'en-CA');
  const leadApiBody = await sendToFormApi(payload);

  assert.equal(leadApiBody.message, originalMessage);
  assert.equal(leadApiBody.extra_fields.service_type, 'Mail-In');
  assert.equal(leadApiBody.extra_fields.province, 'QC');
  assert.equal(leadApiBody.extra_fields.country, 'CA');
  assert.equal(leadApiBody.extra_fields.site_language, 'en-CA');
  assert.equal(leadApiBody.extra_fields.english_support_preference, undefined);
  assert.equal(leadApiBody.preferred_language, undefined);
});
