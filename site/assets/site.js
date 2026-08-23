(function () {
  'use strict';

  const phoneRules = {
    CA: { code: '1', trunk: false, pattern: /^[2-9]\d{2}[2-9]\d{6}$/ },
    FR: { code: '33', trunk: true, pattern: /^[67]\d{8}$/ },
    ES: { code: '34', trunk: false, pattern: /^[67]\d{8}$/ },
    VN: { code: '84', trunk: true, pattern: /^[35789]\d{8}$/ },
    SA: { code: '966', trunk: true, pattern: /^5\d{8}$/ },
    MX: { code: '52', trunk: false, pattern: /^\d{10}$/ },
    JP: { code: '81', trunk: true, pattern: /^(?:70|80|90)\d{8}$/ },
    CO: { code: '57', trunk: false, pattern: /^3\d{9}$/ },
    EG: { code: '20', trunk: true, pattern: /^1[0125]\d{8}$/ },
    MA: { code: '212', trunk: true, pattern: /^[67]\d{8}$/ }
  };

  function setupMenu() {
    const button = document.querySelector('.menu-button');
    const nav = document.querySelector('#site-nav');
    if (!button || !nav) return;
    button.addEventListener('click', function () {
      const open = nav.classList.toggle('open');
      button.setAttribute('aria-expanded', String(open));
    });
    nav.addEventListener('click', function () {
      nav.classList.remove('open');
      button.setAttribute('aria-expanded', 'false');
    });
  }

  function setupLanguages() {
    document.querySelectorAll('[data-language]').forEach(function (link) {
      link.addEventListener('click', function () {
        try { localStorage.setItem('graphicsrepair-language', link.dataset.language); } catch (error) {}
      });
    });
    if (document.body.dataset.locale !== 'en' || location.pathname !== '/') return;
    let selected = '';
    try { selected = localStorage.getItem('graphicsrepair-language') || ''; } catch (error) {}
    const browser = (navigator.languages || [navigator.language || '']).map(function (value) { return value.toLowerCase(); });
    const supported = ['fr', 'es', 'vi', 'ar', 'ja'];
    const match = selected || supported.find(function (locale) { return browser.some(function (value) { return value === locale || value.startsWith(locale + '-'); }); });
    if (supported.includes(match)) location.replace('/' + match + '/');
  }

  function localDigits(value, rule) {
    const trimmed = value.trim();
    if (!/^\+?[0-9\s().-]+$/.test(trimmed)) return '';
    let digits = trimmed.replace(/\D/g, '');
    if (trimmed.startsWith('+')) {
      digits = digits.startsWith(rule.code) ? digits.slice(rule.code.length) : '';
    } else if (rule.trunk && digits.startsWith('0')) {
      digits = digits.slice(1);
    } else if (!rule.trunk && !rule.pattern.test(digits) && digits.startsWith(rule.code)) {
      digits = digits.slice(rule.code.length);
    }
    return digits;
  }

  function setupPhone(form) {
    const phone = form.elements.phone;
    const detection = form.querySelector('#phone-validation-profile');
    const locale = document.documentElement.lang || 'en-CA';
    const names = typeof Intl.DisplayNames === 'function' ? new Intl.DisplayNames([locale], { type: 'region' }) : null;
    const defaultCountry = document.body.dataset.defaultCountry || 'CA';
    let country = defaultCountry;
    const byLongestCode = Object.keys(phoneRules).sort(function (a, b) { return phoneRules[b].code.length - phoneRules[a].code.length; });
    function detectCountry() {
      const trimmed = phone.value.trim();
      const digits = trimmed.replace(/\D/g, '');
      if (trimmed.startsWith('+')) {
        const match = byLongestCode.find(function (candidate) { return digits.startsWith(phoneRules[candidate].code); });
        country = match || 'INTL';
      } else {
        // A leading 1 is unambiguous among the approved countries. Other
        // unprefixed numbers remain local to the page locale to avoid treating
        // a Canadian 212 area code as Morocco's +212, for example.
        country = digits.startsWith('1') ? 'CA' : defaultCountry;
      }
      detection.textContent = country === 'INTL'
        ? detection.dataset.internationalLabel
        : (names ? names.of(country) : country) + ' (+' + phoneRules[country].code + ')';
      return country;
    }
    function validate() {
      const detected = detectCountry();
      if (detected === 'INTL') {
        const trimmed = phone.value.trim();
        const validInternational = /^\+[0-9\s().-]+$/.test(trimmed)
          && /^[1-9]\d{6,14}$/.test(trimmed.replace(/\D/g, ''));
        phone.setCustomValidity(validInternational ? '' : phone.dataset.error);
        phone.setAttribute('aria-invalid', String(!validInternational));
        return validInternational;
      }
      const rule = phoneRules[detected];
      const digits = localDigits(phone.value, rule);
      const valid = rule.pattern.test(digits);
      phone.setCustomValidity(valid ? '' : phone.dataset.error);
      phone.setAttribute('aria-invalid', String(!valid));
      return valid;
    }
    function update() {
      detectCountry();
      phone.placeholder = country === 'INTL' ? '+' : '+' + phoneRules[country].code;
      if (phone.value) validate();
    }
    phone.addEventListener('input', update);
    phone.addEventListener('blur', validate);
    update();
    return {
      profile: function () { return detectCountry(); },
      e164: function () {
        const detected = detectCountry();
        if (detected === 'INTL') return '+' + phone.value.replace(/\D/g, '').slice(0, 15);
        const rule = phoneRules[detected];
        return '+' + rule.code + localDigits(phone.value, rule);
      },
      update: update
    };
  }

  function clean(value, max) { return String(value || '').replace(/[<>\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max); }
  function normalizeSiteLanguage(value) {
    const normalized = String(value || '').trim().replace(/_/g, '-');
    return /^(?:fr|fr-ca)$/i.test(normalized) ? 'fr-CA' : normalized;
  }
  function setupMailingFields(form) {
    const serviceType = form.elements.service_type;
    const fields = form.querySelector('#mailing-fields');
    const internationalFields = form.querySelector('#international-mailing-fields');
    const address = form.elements.mailing_address;
    const unitNumber = form.elements.unit_number;
    const returnCountry = form.elements.return_country;
    const province = form.elements.province;
    const ownershipConfirmed = form.elements.ownership_confirmed;
    const shippingAcknowledged = form.elements.international_shipping_ack;
    function update() {
      const mailIn = serviceType.value === 'Mail-In';
      const international = mailIn && returnCountry.value && returnCountry.value !== 'CA';
      fields.hidden = !mailIn;
      address.required = mailIn;
      address.disabled = !mailIn;
      unitNumber.disabled = !mailIn;
      returnCountry.required = mailIn;
      returnCountry.disabled = !mailIn;
      province.required = mailIn;
      province.disabled = !mailIn;
      internationalFields.hidden = !international;
      ownershipConfirmed.required = Boolean(international);
      ownershipConfirmed.disabled = !international;
      shippingAcknowledged.required = Boolean(international);
      shippingAcknowledged.disabled = !international;
      if (!mailIn) {
        address.value = '';
        unitNumber.value = '';
        returnCountry.value = '';
        province.value = '';
      }
      if (!international) {
        ownershipConfirmed.checked = false;
        shippingAcknowledged.checked = false;
      }
    }
    serviceType.addEventListener('change', update);
    returnCountry.addEventListener('change', update);
    update();
    return update;
  }
  function buildLeadPayload(form, phoneSetup, siteLanguage) {
    const message = form.elements.message.value;
    const model = clean(form.elements.model.value, 160);
    const requestType = form.elements.request_type.value;
    const serviceType = form.elements.service_type.value;
    const mailIn = serviceType === 'Mail-In';
    const mailingAddress = mailIn ? clean(form.elements.mailing_address.value, 300) : '';
    const unitNumber = mailIn ? clean(form.elements.unit_number.value, 30) : '';
    const returnCountry = mailIn ? clean(form.elements.return_country.value, 10) : '';
    const province = mailIn ? clean(form.elements.province.value, 100) : '';
    const internationalMailIn = Boolean(mailIn && returnCountry && returnCountry !== 'CA');
    const ownershipConfirmed = internationalMailIn && form.elements.ownership_confirmed.checked;
    const shippingAcknowledged = internationalMailIn && form.elements.international_shipping_ack.checked;
    const replyPreference = form.elements.english_support_preference;
    return {
      name: clean(form.elements.name.value, 100),
      email: clean(form.elements.email.value, 254),
      phone: phoneSetup.e164(),
      company: '',
      message: message,
      form_id: 'graphics_card_repair_quote',
      website: form.elements.website.value,
      start_time: Number(form.elements.start_time.value),
      extra_fields: {
        phone_validation_profile: phoneSetup.profile(),
        graphics_card_model: model,
        request_type: requestType,
        service_type: serviceType,
        mailing_address: mailingAddress || undefined,
        unit_number: unitNumber || undefined,
        province: province || undefined,
        country: returnCountry || undefined,
        return_country: returnCountry || undefined,
        international_mail_in: internationalMailIn,
        ownership_confirmed: ownershipConfirmed || undefined,
        international_shipping_ack: shippingAcknowledged || undefined,
        site_language: normalizeSiteLanguage(siteLanguage),
        english_support_preference: replyPreference ? replyPreference.value : undefined,
        accepted_privacy_and_terms: true,
        source_site: 'graphicsrepair.ca'
      }
    };
  }
  function submitLeadPayload(payload, contactForm) {
    if (!contactForm || typeof contactForm.submitProtectedPayload !== 'function') {
      return Promise.reject(new Error('Submission is unavailable.'));
    }
    return contactForm.submitProtectedPayload(payload);
  }
  function setupForm() {
    const form = document.querySelector('#repair-form');
    if (!form) return;
    form.elements.start_time.value = String(Math.floor(Date.now() / 1000));
    const phoneSetup = setupPhone(form);
    const updateMailingFields = setupMailingFields(form);
    const button = form.querySelector('button[type="submit"]');
    const status = form.querySelector('#form-status');
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      if (!form.reportValidity()) return;
      button.disabled = true;
      status.className = 'form-status';
      status.textContent = form.dataset.sending;
      const payload = buildLeadPayload(form, phoneSetup, document.documentElement.lang);
      try {
        await submitLeadPayload(payload, window.ContactForm);
        form.reset();
        form.elements.start_time.value = String(Math.floor(Date.now() / 1000));
        phoneSetup.update();
        updateMailingFields();
        status.className = 'form-status success';
        status.textContent = form.dataset.success;
      } catch (error) {
        console.error('Form submission failed:', error);
        status.className = 'form-status error';
        status.textContent = form.dataset.error;
      } finally {
        button.disabled = false;
      }
    });
  }

  function setupRepairPrompt() {
    const prompt = document.querySelector('[data-repair-prompt]');
    const openLink = document.querySelector('[data-repair-open]');
    const dismissButton = document.querySelector('[data-repair-dismiss]');
    if (!prompt || !openLink) return;
    const dismissKey = 'graphicsrepair-repair-prompt-dismissed';
    let revealTimer = null;

    function dismissed() {
      try { return sessionStorage.getItem(dismissKey) === '1'; } catch (error) { return false; }
    }
    function rememberDismissal() {
      try { sessionStorage.setItem(dismissKey, '1'); } catch (error) {}
    }
    function removeTriggers() {
      if (revealTimer !== null) window.clearTimeout(revealTimer);
      revealTimer = null;
      window.removeEventListener('scroll', checkScrollProgress);
    }
    function reveal() {
      if (dismissed()) return;
      if (document.visibilityState === 'hidden') {
        document.addEventListener('visibilitychange', reveal, { once: true });
        return;
      }
      removeTriggers();
      prompt.hidden = false;
      window.requestAnimationFrame(function () { prompt.classList.add('is-visible'); });
    }
    function checkScrollProgress() {
      const distance = Math.max(document.documentElement.scrollHeight - window.innerHeight, 0);
      if (distance && Math.max(window.scrollY, document.documentElement.scrollTop, 0) / distance >= 1 / 3) reveal();
    }
    function dismiss() {
      rememberDismissal();
      removeTriggers();
      prompt.classList.remove('is-visible');
      window.setTimeout(function () { prompt.hidden = true; }, 250);
    }

    openLink.addEventListener('click', dismiss);
    if (dismissButton) dismissButton.addEventListener('click', dismiss);
    if (!dismissed()) {
      revealTimer = window.setTimeout(reveal, 35000);
      window.addEventListener('scroll', checkScrollProgress, { passive: true });
      checkScrollProgress();
    }
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { buildLeadPayload: buildLeadPayload, normalizeSiteLanguage: normalizeSiteLanguage, submitLeadPayload: submitLeadPayload };
  }
  if (typeof document !== 'undefined') {
    setupMenu();
    setupLanguages();
    setupForm();
    setupRepairPrompt();
  }
}());
