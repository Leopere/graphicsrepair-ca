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

  function inject(src, integrity) {
    const tracker = document.createElement("script");
    tracker.async = true;
    tracker.src = src;
    tracker.dataset.siteId = siteId;
    if (integrity) {
      tracker.integrity = integrity;
      tracker.crossOrigin = "anonymous";
    }
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
