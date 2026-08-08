#!/usr/bin/env python3
"""Build the production-only Graphics Repair Canada static artifact."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "site"
OUTPUT = ROOT / "_site"
DOMAIN = "https://graphicsrepair.ca"
LOCALE_ORDER = ("en", "fr", "es", "vi", "ar", "ja")
HREFLANG = {"en": "en-CA", "fr": "fr-FR", "es": "es-419", "vi": "vi-VN", "ar": "ar", "ja": "ja-JP"}

content_spec = importlib.util.spec_from_file_location("graphics_site_content", SOURCE / "content.py")
if content_spec is None or content_spec.loader is None:
    raise RuntimeError("Unable to load localized site content")
content_module = importlib.util.module_from_spec(content_spec)
content_spec.loader.exec_module(content_module)
LOCALES = content_module.LOCALES


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def locale_path(locale: str) -> str:
    return "" if locale == "en" else f"{locale}/"


def language_links(current: str) -> str:
    links = []
    for locale in LOCALE_ORDER:
        content = LOCALES[locale]
        active = ' aria-current="page"' if locale == current else ""
        links.append(
            f'<a href="/{locale_path(locale)}" lang="{esc(content["tag"])}" '
            f'data-language="{locale}"{active}>{esc(content["native"])}</a>'
        )
    return "".join(links)


def alternates(page: str = "") -> str:
    tags = []
    for locale in LOCALE_ORDER:
        url = f"{DOMAIN}/{locale_path(locale)}{page}"
        tags.append(f'<link rel="alternate" hreflang="{HREFLANG[locale]}" href="{url}">')
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/{page}">')
    return "\n".join(tags)


def header(content: dict[str, object], locale: str) -> str:
    prefix = "" if locale == "en" else "../"
    return f"""
    <a class="skip-link" href="#main">Skip to content</a>
    <div class="network-bar"><div class="shell">{esc(content['network'])} <a href="https://motherboardrepair.ca/" rel="noopener">motherboardrepair.ca</a></div></div>
    <header class="site-header">
      <div class="shell header-row">
        <a class="brand" href="/{locale_path(locale)}" aria-label="Graphics Repair Canada home">
          <img src="{prefix}assets/mrc-logo.svg" width="182" height="66" alt="MRC">
          <span><strong>Graphics Repair</strong><small>Canada</small></span>
        </a>
        <button class="menu-button" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
        <nav id="site-nav" aria-label="Primary">
          <a href="#faults">{esc(content['nav_faults'])}</a>
          <a href="#process">{esc(content['nav_process'])}</a>
          <a href="#used-check">{esc(content['nav_check'])}</a>
          <a class="button button-small" href="#contact">{esc(content['nav_contact'])}</a>
        </nav>
      </div>
    </header>"""


def footer(content: dict[str, object], locale: str) -> str:
    prefix = "" if locale == "en" else "../"
    return f"""
    <footer class="site-footer">
      <div class="shell footer-grid">
        <div><img src="{prefix}assets/mrc-logo-white.svg" width="158" height="57" alt="MRC"><p>{esc(content['copyright'])}</p></div>
        <div><p><a href="https://motherboardrepair.ca/graphics-card-repair.html" rel="noopener">{esc(content['backlink'])}</a></p><p><a href="{prefix}privacy.html">{esc(content['privacy'])}</a> · <a href="{prefix}terms.html">{esc(content['terms'])}</a></p></div>
        <div class="languages" aria-label="Languages">{language_links(locale)}</div>
      </div>
    </footer>"""


def render_index(locale: str) -> str:
    c = LOCALES[locale]
    path = locale_path(locale)
    prefix = "" if locale == "en" else "../"
    canonical = f"{DOMAIN}/{path}"
    list_items = lambda values: "".join(f"<li>{esc(value)}</li>" for value in values)
    fault_cards = "".join(
        f'<article class="fault-card"><span class="trace-dot" aria-hidden="true"></span><h3>{esc(c[f"fault{index}_title"])}</h3><p>{esc(c[f"fault{index}_body"])}</p></article>'
        for index in (1, 2, 3)
    )
    steps = "".join(
        f'<li><span>{esc(number)}</span><div><h3>{esc(title)}</h3><p>{esc(body)}</p></div></li>'
        for number, title, body in c["steps"]
    )
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization", "@id": f"{DOMAIN}/#organization",
                "name": "Graphics Repair Canada", "alternateName": "MRC",
                "url": f"{DOMAIN}/", "telephone": "+1-226-702-0555",
                "logo": f"{DOMAIN}/assets/mrc-logo.svg",
                "sameAs": ["https://motherboardrepair.ca/"],
            },
            {
                "@type": "Service", "@id": f"{canonical}#service",
                "name": c["title"], "description": c["description"],
                "provider": {"@id": f"{DOMAIN}/#organization"},
                "areaServed": {"@type": "Country", "name": "Canada"},
                "serviceType": "Board-level graphics card and GPU repair",
                "offers": {"@type": "Offer", "name": "Used graphics card verification", "price": "50", "priceCurrency": "CAD"},
            },
        ],
    }
    return f"""<!doctype html>
<html lang="{esc(c['tag'])}" dir="{esc(c['dir'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(c['description'])}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src https://forms.motherboardrepair.ca; object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests">
  <title>{esc(c['title'])}</title>
  <link rel="canonical" href="{canonical}">
  {alternates()}
  <meta property="og:type" content="website"><meta property="og:site_name" content="Graphics Repair Canada"><meta property="og:title" content="{esc(c['title'])}"><meta property="og:description" content="{esc(c['description'])}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{DOMAIN}/assets/gpu-repair.webp">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="{prefix}assets/style.css">
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')}</script>
  <script src="{prefix}assets/site.js" defer></script>
</head>
<body data-locale="{locale}" data-default-country="{esc(c['country'])}">
{header(c, locale)}
<main id="main">
  <section class="hero">
    <div class="hero-art" aria-hidden="true"><img src="{prefix}assets/gpu-repair.webp" width="1080" height="720" alt=""></div>
    <div class="shell hero-grid"><div class="hero-copy">
      <p class="eyebrow">{esc(c['eyebrow'])}</p><h1>{esc(c['hero'])}</h1><p class="lede">{esc(c['hero_body'])}</p>
      <div class="hero-actions"><a class="button" href="#contact">{esc(c['hero_cta'])}</a><span>{esc(c['hero_note'])}</span></div>
    </div><div class="board-card" aria-label="Service scope"><span>GPU</span><strong>DIAG / REPAIR</strong><small>NVIDIA · AMD · INTEL</small></div></div>
  </section>
  <aside class="language-notice"><div class="shell"><span>{esc(c['notice'])}</span><div class="languages">{language_links(locale)}</div></div></aside>
  <section class="section" id="faults"><div class="shell"><div class="section-heading"><p class="eyebrow">01 / DIAGNOSIS</p><h2>{esc(c['faults_title'])}</h2><p>{esc(c['faults_intro'])}</p></div><div class="fault-grid">{fault_cards}</div></div></section>
  <section class="section section-dark"><div class="shell split"><div><p class="eyebrow">02 / SCOPE</p><h2>{esc(c['scope_title'])}</h2><p>{esc(c['scope_body'])}</p><ul class="check-list">{list_items(c['scope_items'])}</ul></div><aside class="limit-card"><h3>{esc(c['limits_title'])}</h3><ul>{list_items(c['limits_items'])}</ul></aside></div></section>
  <section class="section" id="process"><div class="shell"><div class="section-heading"><p class="eyebrow">03 / INTAKE</p><h2>{esc(c['process_title'])}</h2></div><ol class="steps">{steps}</ol></div></section>
  <section class="section verification" id="used-check"><div class="shell split"><div><p class="eyebrow">04 / VERIFY</p><h2>{esc(c['check_title'])}</h2><p>{esc(c['check_body'])}</p><ul class="check-list">{list_items(c['check_items'])}</ul></div><div class="price-card"><span>{esc(c['check_price'])}</span><small>{esc(c['hero_note'])}</small><a class="button" href="#contact">{esc(c['nav_check'])}</a></div></div></section>
  <section class="section contact-section" id="contact"><div class="shell contact-grid"><div><p class="eyebrow">05 / REQUEST</p><h2>{esc(c['contact_title'])}</h2><p>{esc(c['contact_intro'])}</p><div class="reply-card"><h3>{esc(c['reply_title'])}</h3><p>{esc(c['reply_body'])}</p></div></div>
    <form id="repair-form" class="repair-form" novalidate data-sending="{esc(c['sending'])}" data-success="{esc(c['success'])}" data-error="{esc(c['error'])}">
      <input type="hidden" name="form_id" value="graphics_card_repair_quote"><input type="hidden" name="start_time" value="">
      <div class="form-row"><label>{esc(c['name'])}<input name="name" autocomplete="name" maxlength="100" required></label><label>{esc(c['email'])}<input name="email" type="email" autocomplete="email" maxlength="254" required></label></div>
      <div class="form-row"><label>{esc(c['country_label'])}<select name="country" id="country" autocomplete="country" required></select></label><label>{esc(c['phone'])}<input name="phone" id="phone" type="tel" autocomplete="tel" inputmode="tel" maxlength="30" required></label></div>
      <label>{esc(c['model'])}<input name="model" maxlength="160" required placeholder="e.g. ASUS TUF RTX 3080 10GB"></label>
      <label>{esc(c['service'])}<select name="service_type" required><option value="repair">{esc(c['repair'])}</option><option value="verification">{esc(c['verify'])}</option></select></label>
      <label>{esc(c['symptoms'])}<textarea name="message" rows="6" minlength="20" maxlength="1000" required></textarea></label>
      <label class="honeypot" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
      <label class="consent"><input name="accept_terms" type="checkbox" required><span>{esc(c['consent'])} <a href="{prefix}privacy.html" target="_blank" rel="noopener">{esc(c['privacy'])}</a> · <a href="{prefix}terms.html" target="_blank" rel="noopener">{esc(c['terms'])}</a></span></label>
      <button class="button" type="submit">{esc(c['send'])}</button><p class="form-note">{esc(c['form_privacy'])}</p><p id="form-status" class="form-status" role="status" aria-live="polite"></p>
    </form>
  </div></section>
</main>
{footer(c, locale)}
</body></html>"""


def render_legal(kind: str) -> str:
    if kind == "privacy":
        title = "Privacy Policy"
        description = "How Graphics Repair Canada handles contact information, repair details, hosting metrics and service records."
        body = """
        <h2>Information we collect</h2><p>When you submit the repair form, we receive the name, email, phone number, country, card model, request type, symptoms and prior-work history you provide. We use this information to assess, communicate about and, if accepted, deliver the requested service.</p>
        <h2>Protected form processing</h2><p>The form is sent over HTTPS to MRC's form processor at forms.motherboardrepair.ca. It uses strict field validation, a hidden honeypot, a minimum completion time, rate limiting and a short-lived proof-of-work challenge. The processor stores the request and forwards it to MRC's repair workflow. Do not include passwords, payment-card numbers or unrelated sensitive information.</p>
        <h2>Privacy-respecting metrics</h2><p>We do not run advertising analytics, session replay, fingerprinting or a client-side analytics script. No form text is sent to analytics. Cloudflare and GitHub process standard request information needed to deliver and secure the site; Cloudflare provides aggregate edge traffic metrics. These providers may temporarily process IP addresses, browser details, requested paths and timestamps as part of ordinary hosting, security and network logs.</p>
        <h2>Service records and disclosures</h2><p>If a job is accepted, we may retain communications, diagnostics, work performed, parts and payment metadata for operations, warranty, accounting and legal obligations. Payment processors and shipping carriers receive only the information needed for their roles. We do not sell personal information.</p>
        <h2>Your choices</h2><p>You may ask MRC to access, correct or delete your personal information, subject to operational and legal retention requirements, by submitting a new form request marked “privacy request.”</p>
        """
    else:
        title = "Service Terms"
        description = "Terms for Graphics Repair Canada diagnostics, GPU repair, used-card verification, payment and shipping."
        body = """
        <h2>Scope and acceptance</h2><p>Graphics Repair Canada is an MRC specialist site. Submitting the form starts a free job assessment; it does not mean the card or job has been accepted. Do not ship until MRC confirms acceptance and supplies instructions.</p>
        <h2>Diagnostics and outcomes</h2><p>You authorize reasonable diagnostics for an accepted card. Any diagnostic charge, repair estimate, parts cost and practical test limitation will be disclosed before related billable work. Electronics diagnostics and repair are best-effort services. No outcome or turnaround is guaranteed unless MRC states it in writing.</p>
        <h2>Used-GPU verification</h2><p>The advertised $50 CAD plus tax covers one non-invasive testing attempt on one supported desktop graphics card after model acceptance. It excludes shipping, teardown, repair, parts and deeper board-level diagnosis. Results are limited to “consistent with the listing,” “concerns found” or “inconclusive.” MRC does not determine seller intent, ownership or make legal findings of fraud. The fee is non-refundable once testing begins.</p>
        <h2>Payment, shipping and risk</h2><p>Most repairs are paid after approved work is complete and before release or return shipping. Special parts may require a disclosed deposit. Customers pay inbound and return shipping, insurance, customs, duties, taxes and brokerage unless agreed otherwise. Shipping risk is carried under the selected carrier and insurance terms.</p>
        <h2>Prior work and repair risk</h2><p>Heat, corrosion, prior repair, missing parts and latent faults increase risk. Diagnostic and repair processes may involve heat, cleaning and irreversible component removal or replacement. MRC is not responsible for pre-existing damage or faults that become apparent during reasonable work. Never send a card with a battery or undeclared hazardous contamination.</p>
        <h2>Warranty and governing terms</h2><p>Unless confirmed in writing for a work order, MRC does not promise a repair warranty. Any parts coverage is limited to the supplied part and its supplier terms. Ontario law and applicable Canadian federal law govern the service, without limiting non-waivable consumer rights.</p>
        """
    return f"""<!doctype html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{description}"><meta name="robots" content="index,follow"><meta name="referrer" content="strict-origin-when-cross-origin"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'"><title>{title} | Graphics Repair Canada</title><link rel="canonical" href="{DOMAIN}/{kind}.html"><link rel="stylesheet" href="assets/style.css"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><script src="assets/site.js" defer></script></head><body data-locale="en" data-default-country="CA">{header(LOCALES['en'], 'en')}<main id="main"><section class="legal"><div class="shell legal-copy"><p class="eyebrow">MRC · Updated {date.today().isoformat()}</p><h1>{title}</h1><p class="lede">{description}</p>{body}<p><a class="button" href="/#contact">Start a repair</a></p></div></section></main>{footer(LOCALES['en'], 'en')}</body></html>"""


def build() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    (OUTPUT / "assets").mkdir(parents=True)
    for source in (SOURCE / "assets").iterdir():
        if source.is_file():
            shutil.copy2(source, OUTPUT / "assets" / source.name)
    asset_map = {
        ROOT / "docs/SVG/MRC_Logo_Main_Color.svg": OUTPUT / "assets/mrc-logo.svg",
        ROOT / "docs/SVG/MRC_Logo_Secondary_White.svg": OUTPUT / "assets/mrc-logo-white.svg",
        ROOT / "docs/images/graphics_card_repair.webp": OUTPUT / "assets/gpu-repair.webp",
        ROOT / "docs/boot-logo.svg": OUTPUT / "assets/favicon.svg",
    }
    for source, destination in asset_map.items():
        if not source.is_file():
            raise FileNotFoundError(f"Required MRC source asset is missing: {source}")
        shutil.copy2(source, destination)
    for locale in LOCALE_ORDER:
        destination = OUTPUT if locale == "en" else OUTPUT / locale
        destination.mkdir(exist_ok=True)
        (destination / "index.html").write_text(render_index(locale), encoding="utf-8")
    (OUTPUT / "privacy.html").write_text(render_legal("privacy"), encoding="utf-8")
    (OUTPUT / "terms.html").write_text(render_legal("terms"), encoding="utf-8")
    (OUTPUT / "404.html").write_text(render_legal("privacy").replace("Privacy Policy", "Page not found").replace("How Graphics Repair Canada handles contact information, repair details, hosting metrics and service records.", "The requested page does not exist. Return to the Graphics Repair Canada home page."), encoding="utf-8")
    (OUTPUT / "CNAME").write_text("graphicsrepair.ca\n", encoding="utf-8")
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    urls = [f"{DOMAIN}/", *(f"{DOMAIN}/{locale}/" for locale in LOCALE_ORDER if locale != "en"), f"{DOMAIN}/privacy.html", f"{DOMAIN}/terms.html"]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{url}</loc></url>\n" for url in urls) + "</urlset>\n"
    (OUTPUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Build and run structural validation")
    args = parser.parse_args()
    build()
    if args.check:
        from tests.test_graphics_site import validate_site
        validate_site()
    print(f"Built {OUTPUT}")


if __name__ == "__main__":
    main()
