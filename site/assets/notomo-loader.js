function notomoSiteId(hostname) {
  const host = String(hostname || "").replace(/^www\./i, "").toLowerCase();
  return host === "graphicsrepair.com" ? "graphicsrepair.com" : "graphicsrepair.ca";
}

(function startGraphicsNotomo() {
  const embed = document.currentScript;
  if (!embed || window.__graphicsNotomoStarted) {
    return;
  }
  const fallbackSrc = embed.dataset.trackerSrc;
  const fallbackIntegrity = embed.dataset.trackerIntegrity;
  if (!fallbackSrc || !fallbackIntegrity) {
    return;
  }
  window.__graphicsNotomoStarted = true;
  const siteId = notomoSiteId(location.hostname);
  const origin = "https://notomo.colinknapp.com";

  // Only finite contact diagnostics enter custom error metadata. Replay policy
  // and property selection are independent of this diagnostic boundary.
  const pendingIssues = [];
  const failureCodes = new Set([
    'proof_network', 'proof_timeout', 'proof_response_read', 'proof_response_json',
    'proof_http', 'proof_challenge', 'proof_compute', 'submit_network',
    'submit_timeout', 'submit_response_read', 'submit_response_json',
    'submit_http', 'submit_rejected', 'unknown'
  ]);
  function sendIssue(metadata) {
    if (!window.notomo || typeof window.notomo.captureError !== 'function') return false;
    window.notomo.captureError(new Error('contact_form_submission_failed'), metadata);
    return true;
  }
  window.reportNotomoIssue = function (name, details) {
    if (name !== 'contact_form_submission_failed') return;
    details = details || {};
    const parts = typeof details.code === 'string' ? details.code.split(':') : [];
    const validCode = parts.length <= 2 && failureCodes.has(parts[0]) &&
      (parts.length === 1 || ['FORM_PROOF_INVALID', 'FORM_PROOF_UNAVAILABLE'].includes(parts[1]));
    const metadata = {
      component: 'contact_form',
      form_id: details.form_id === 'graphics_card_repair_quote' ? details.form_id : 'unknown',
      stage: 'submit',
      status: Number.isInteger(details.status) && details.status >= 100 && details.status <= 599 ? details.status : 0,
      code: validCode ? details.code : 'unknown'
    };
    if (!sendIssue(metadata) && pendingIssues.length < 10) pendingIssues.push(metadata);
  };

  function inject(src, integrity) {
    const tracker = document.createElement("script");
    tracker.async = true;
    tracker.src = src;
    tracker.dataset.siteId = siteId;
    if (integrity) {
      tracker.integrity = integrity;
      tracker.crossOrigin = "anonymous";
    }
    tracker.addEventListener('load', function () {
      pendingIssues.splice(0).forEach(sendIssue);
    }, { once: true });
    embed.after(tracker);
  }

  fetch(origin + "/n-config/" + encodeURIComponent(siteId), { credentials: "omit" })
    .then(function (res) {
      return res.ok ? res.json() : {};
    })
    .then(function (cfg) {
      const src = cfg.tracker_asset
        ? new URL(cfg.tracker_asset, origin).href
        : fallbackSrc;
      inject(src, cfg.tracker_integrity || fallbackIntegrity);
    })
    .catch(function () {
      inject(fallbackSrc, fallbackIntegrity);
    });
})();
