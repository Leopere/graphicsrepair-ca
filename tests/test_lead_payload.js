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

function fakeForm({ message, province, returnCountry = 'CA', languagePreference, serviceType = 'Mail-In', rush = false }) {
  const elements = {
    name: field('Alex Customer'),
    email: field('alex@example.com'),
    website: field(''),
    start_time: field('1723900000'),
    phone: field(''),
    model: field('ASUS RTX 3080'),
    request_type: field('Repair quote'),
    service_type: field(serviceType),
    rush_service: field('yes', { checked: rush }),
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

const { buildLeadPayload, normalizeSiteLanguage, submitLeadPayload } = loadLeadHelpers();

async function sendThroughContactRuntime(payload) {
  let submitted;
  await submitLeadPayload(payload, {
    submitProtectedPayload: async (candidate) => {
      submitted = candidate;
      return { ok: true, success: true };
    },
  });
  assert.equal(submitted, payload);
  return submitted;
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
  const leadApiBody = await sendThroughContactRuntime(payload);

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
  const leadApiBody = await sendThroughContactRuntime(payload);

  assert.equal(leadApiBody.message, originalMessage);
  assert.equal(leadApiBody.extra_fields.service_type, 'Mail-In');
  assert.equal(leadApiBody.extra_fields.province, 'QC');
  assert.equal(leadApiBody.extra_fields.country, 'CA');
  assert.equal(leadApiBody.extra_fields.site_language, 'en-CA');
  assert.equal(leadApiBody.extra_fields.english_support_preference, undefined);
  assert.equal(leadApiBody.preferred_language, undefined);
});

for (const serviceType of ['Mail-In', 'In-Person']) {
  for (const rush of [false, true]) {
    test(`${serviceType} request ${rush ? 'includes optional rush for $130' : 'has no rush fee by default'}`, async () => {
      const message = 'Please assess my graphics card for repair.';
      const form = fakeForm({ message, province: 'ON', serviceType, rush });
      const payload = buildLeadPayload(form, {
        e164: () => '+12265550123',
        profile: () => 'CA',
      }, 'en-CA');
      const submitted = await sendThroughContactRuntime(payload);
      const body = JSON.parse(JSON.stringify(submitted));

      assert.equal(body.message, message);
      assert.equal(body.extra_fields.service_type, serviceType);
      assert.equal(body.extra_fields.rush_service, rush);
      assert.equal(body.extra_fields.rush_fee, rush ? 130 : undefined);
      assert.equal(Object.hasOwn(body.extra_fields, 'rush_fee'), rush);
      assert.equal(body.extra_fields.request_type, 'Repair quote');
      assert.equal(body.extra_fields.mailing_address, serviceType === 'Mail-In' ? '123 Main Street' : undefined);
      assert.equal(body.extra_fields.return_country, serviceType === 'Mail-In' ? 'CA' : undefined);
    });
  }
}

test('unchecking rush removes its fee from the next submission', () => {
  const form = fakeForm({ message: 'My graphics card needs a repair.', province: 'ON', rush: true });
  const phone = { e164: () => '+12265550123', profile: () => 'CA' };
  assert.equal(buildLeadPayload(form, phone, 'en-CA').extra_fields.rush_fee, 130);
  form.elements.rush_service.checked = false;
  const body = JSON.parse(JSON.stringify(buildLeadPayload(form, phone, 'en-CA')));
  assert.equal(body.extra_fields.rush_service, false);
  assert.equal(Object.hasOwn(body.extra_fields, 'rush_fee'), false);
});
