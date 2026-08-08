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
FORM_COPY = content_module.FORM_COPY
UI_COPY = content_module.UI_COPY


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


def header(content: dict[str, object], locale: str, asset_prefix: str | None = None, anchor_prefix: str = "") -> str:
    prefix = ("" if locale == "en" else "../") if asset_prefix is None else asset_prefix
    ui = UI_COPY[locale]
    return f"""
    <a class="skip-link" href="#main">{esc(ui['skip'])}</a>
    <div class="network-bar"><div class="shell">{esc(content['network'])} <a href="https://motherboardrepair.ca/" rel="noopener">motherboardrepair.ca</a></div></div>
    <header class="site-header">
      <div class="shell header-row">
        <a class="brand" href="/{locale_path(locale)}">
          <img src="{prefix}assets/mrc-logo.svg" width="182" height="66" alt="MRC">
          <span><strong>Graphics Repair</strong><small>Canada</small></span>
        </a>
        <button class="menu-button" type="button" aria-expanded="false" aria-controls="site-nav">{esc(ui['menu'])}</button>
        <nav id="site-nav" aria-label="{esc(ui['primary'])}">
          <a href="{anchor_prefix}#faults">{esc(content['nav_faults'])}</a>
          <a href="{anchor_prefix}#process">{esc(content['nav_process'])}</a>
          <a href="{anchor_prefix}#used-check">{esc(content['nav_check'])}</a>
          <a class="button button-small" href="{anchor_prefix}#contact">{esc(content['nav_contact'])}</a>
        </nav>
      </div>
    </header>"""


def footer(content: dict[str, object], locale: str, asset_prefix: str | None = None) -> str:
    prefix = ("" if locale == "en" else "../") if asset_prefix is None else asset_prefix
    ui = UI_COPY[locale]
    return f"""
    <footer class="site-footer">
      <div class="shell footer-grid">
        <div><img src="{prefix}assets/mrc-logo-white.svg" width="158" height="57" alt="MRC" loading="lazy" decoding="async"><p>{esc(content['copyright'])}</p></div>
        <div><p><a href="https://motherboardrepair.ca/graphics-card-repair.html" rel="noopener">{esc(content['backlink'])}</a></p><p><a href="/privacy/">{esc(content['privacy'])}</a> · <a href="/terms/">{esc(content['terms'])}</a></p></div>
        <nav class="languages" aria-label="{esc(ui['footer_languages'])}">{language_links(locale)}</nav>
      </div>
    </footer>"""


def render_index(locale: str) -> str:
    c = LOCALES[locale]
    f = FORM_COPY[locale]
    ui = UI_COPY[locale]
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
                "offers": {"@type": "Offer", "name": "Used graphics card purchase validation", "price": "50", "priceCurrency": "CAD"},
            },
        ],
    }
    return f"""<!DOCTYPE html>
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
    <div class="hero-art" aria-hidden="true"><img src="{prefix}assets/gpu-repair-720.webp" srcset="{prefix}assets/gpu-repair-480.webp 480w, {prefix}assets/gpu-repair-720.webp 720w" sizes="(max-width: 920px) 100vw, 51vw" width="720" height="720" alt="" fetchpriority="high" decoding="async"></div>
    <div class="shell hero-grid"><div class="hero-copy">
      <p class="eyebrow">{esc(c['eyebrow'])}</p><h1>{esc(c['hero'])}</h1><p class="lede">{esc(c['hero_body'])}</p>
      <div class="hero-actions"><a class="button" href="#contact">{esc(c['hero_cta'])}</a><span>{esc(c['hero_note'])}</span></div>
    </div><div class="board-card" aria-hidden="true"><span>GPU</span><strong>DIAG / REPAIR</strong><small>NVIDIA · AMD</small></div></div>
  </section>
  <div class="language-notice"><div class="shell"><span>{esc(c['notice'])}</span><nav class="languages" aria-label="{esc(ui['languages'])}">{language_links(locale)}</nav></div></div>
  <section class="section" id="faults"><div class="shell"><div class="section-heading"><p class="eyebrow">01 / {esc(c['nav_faults'])}</p><h2>{esc(c['faults_title'])}</h2><p>{esc(c['faults_intro'])}</p></div><div class="fault-grid">{fault_cards}</div></div></section>
  <section class="section section-dark"><div class="shell split"><div><p class="eyebrow">02 / {esc(c['scope_title'])}</p><h2>{esc(c['scope_title'])}</h2><p>{esc(c['scope_body'])}</p><ul class="check-list">{list_items(c['scope_items'])}</ul></div><div class="limit-card"><h3>{esc(c['limits_title'])}</h3><ul>{list_items(c['limits_items'])}</ul></div></div></section>
  <section class="section" id="process"><div class="shell"><div class="section-heading"><p class="eyebrow">03 / {esc(c['nav_process'])}</p><h2>{esc(c['process_title'])}</h2></div><ol class="steps">{steps}</ol></div></section>
  <section class="section verification" id="used-check"><div class="shell split"><div><p class="eyebrow">04 / {esc(c['nav_check'])}</p><h2>{esc(c['check_title'])}</h2><p>{esc(c['check_body'])}</p><ul class="check-list">{list_items(c['check_items'])}</ul></div><div class="price-card"><span>{esc(c['check_price'])}</span><small>{esc(c['hero_note'])}</small><a class="button" href="#contact">{esc(c['nav_check'])}</a></div></div></section>
  <section class="section contact-section" id="contact"><div class="shell contact-grid"><div><p class="eyebrow">05 / {esc(c['nav_contact'])}</p><h2>{esc(c['contact_title'])}</h2><p>{esc(c['contact_intro'])}</p><div class="reply-card"><h3>{esc(c['reply_title'])}</h3><p>{esc(c['reply_body'])}</p></div></div>
    <form id="repair-form" class="repair-form" novalidate data-sending="{esc(c['sending'])}" data-success="{esc(c['success'])}" data-error="{esc(c['error'])}">
      <input type="hidden" name="form_id" value="graphics_card_repair_quote"><input type="hidden" name="start_time" value="">
      <fieldset><legend>{esc(f['contact_details'])}</legend>
        <div class="form-row"><label>{esc(c['name'])}<input name="name" type="text" autocomplete="name" maxlength="100" required></label><label>{esc(c['email'])}<input name="email" type="email" autocomplete="email" maxlength="254" aria-describedby="email-hint" required><small id="email-hint" class="form-hint">{esc(f['email_hint'])}</small></label></div>
        <label>{esc(c['phone'])}<input name="phone" id="phone" type="tel" autocomplete="tel" inputmode="tel" maxlength="30" aria-describedby="phone-country-detected phone-hint" data-error="{esc(f['phone_error'])}" required><span id="phone-country-detected" class="phone-detection" aria-live="polite"></span><small id="phone-hint" class="form-hint">{esc(f['phone_hint'])}</small></label>
      </fieldset>
      <fieldset><legend>{esc(f['card_details'])}</legend>
        <label>{esc(c['model'])}<input name="model" type="text" maxlength="160" required placeholder="e.g. ASUS TUF RTX 3080 10GB" aria-describedby="model-hint"><small id="model-hint" class="form-hint">{esc(f['model_hint'])}</small></label>
      </fieldset>
      <fieldset><legend>{esc(f['request_details'])}</legend>
        <label>{esc(c['service'])}<select name="request_type" required><option value="">{esc(f['choose'])}</option><option value="repair">{esc(c['repair'])}</option><option value="verification">{esc(c['verify'])}</option></select></label>
        <label>{esc(f['request_prompt'])}<textarea name="message" rows="6" minlength="20" maxlength="900" required aria-describedby="request-hint"></textarea><small id="request-hint" class="form-hint">{esc(f['request_hint'])}</small></label>
      </fieldset>
      <fieldset><legend>{esc(f['intake'])}</legend>
        <label>{esc(f['intake'])}<select name="service_type" id="service_type" required aria-describedby="intake-hint"><option value="">{esc(f['choose'])}</option><option value="In-Person">{esc(f['dropoff'])}</option><option value="Mail-In">{esc(f['mailin'])}</option></select><small id="intake-hint" class="form-hint">{esc(f['intake_hint'])}</small></label>
        <div id="mailing-fields" class="conditional-fields" hidden>
          <label>{esc(f['address'])}<textarea name="mailing_address" rows="3" maxlength="300" autocomplete="street-address" aria-describedby="address-hint"></textarea><small id="address-hint" class="form-hint">{esc(f['address_hint'])}</small></label>
          <label>{esc(f['unit'])}<input name="unit_number" type="text" maxlength="30" autocomplete="address-line2"></label>
        </div>
      </fieldset>
      <label class="honeypot" aria-hidden="true">Website<input name="website" type="text" tabindex="-1" autocomplete="off"></label>
      <label class="consent"><input name="accept_terms" type="checkbox" required><span>{esc(c['consent'])} <a href="/privacy/" target="_blank" rel="noopener">{esc(c['privacy'])}</a> · <a href="/terms/" target="_blank" rel="noopener">{esc(c['terms'])}</a></span></label>
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
        <h2>Information we collect</h2><p>When you submit the repair form, we receive the name, email, phone number, country, card manufacturer and model, request type, symptoms and prior-work history you provide. For a mail-in request, we also receive the return address and optional unit number you provide. We use this information to assess, communicate about and, if accepted, deliver the requested service. We do not ask for the card serial number.</p>
        <h2>Protected form processing</h2><p>The form is sent over HTTPS to MRC's Cloudflare Worker at forms.motherboardrepair.ca. Along with the fields shown, it sends the selected intake method, detected phone country, page language, consent confirmation and source site. It uses strict field validation, a hidden honeypot, a minimum completion time, rate limiting and a short-lived proof-of-work challenge. Do not include passwords, payment-card numbers or unrelated sensitive information.</p>
        <h2>Language preference</h2><p>If you choose a language, the site stores that language code in your browser's local storage so it can open the same translation on a later visit. It is not a tracking identifier and is not sent with analytics.</p>
        <h2>Privacy-respecting operation</h2><p>We do not run advertising analytics, session replay, fingerprinting or a client-side analytics script. No form text is sent to analytics. GitHub Pages delivers the site and may temporarily process IP addresses, browser details, requested paths and timestamps in ordinary hosting and security logs. Cloudflare provides authoritative DNS only for this site and does not proxy page requests.</p>
        <h2>Privacy questions</h2><p>Use the contact form to ask MRC a privacy question. Do not send unrelated sensitive information through the form.</p>
        """
    else:
        title = "Service Terms"
        description = "Basic request terms for Graphics Repair Canada."
        body = """
        <h2>Request only</h2><p>Graphics Repair Canada is an MRC specialist site. Submitting the form sends a request for review; it does not reserve a time, authorize work or guarantee a repair. Do not mail a card until MRC provides shipping instructions.</p>
        <h2>Used-card purchase validation</h2><p>The advertised $50 CAD plus tax covers one purchase-validation check on one supported used desktop graphics card after model acceptance. MRC compares the card with its listing and expected reference configuration, checks that required chips and assemblies are present, determines whether the inspected configuration can be certified as complete, and attempts to boot it on the shop testing rig. If the card boots, MRC provides a written test report describing the checks completed and observed results. The service is intended to help validate marketplace and other aftermarket purchases. It is not a repair diagnostic, performance guarantee, warranty or proof that no latent fault exists, and excludes shipping, repair and parts. MRC does not determine seller intent, ownership or make legal findings of fraud. The fee is non-refundable once checking begins.</p>
        <h2>Job-specific details</h2><p>Any proposed scope, price or other job-specific detail is communicated separately by MRC. Only the details MRC actually provides for that job apply.</p>
        """
    prefix = "../"
    canonical = f"{DOMAIN}/{kind}/"
    return f"""<!DOCTYPE html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{description}"><meta name="robots" content="index,follow"><meta name="referrer" content="strict-origin-when-cross-origin"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'"><title>{title} | Graphics Repair Canada</title><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="{prefix}assets/style.css"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><script src="{prefix}assets/site.js" defer></script></head><body data-locale="en" data-default-country="CA">{header(LOCALES['en'], 'en', asset_prefix=prefix, anchor_prefix='/')}<main id="main"><section class="legal"><div class="shell legal-copy"><p class="eyebrow">MRC · Updated {date.today().isoformat()}</p><h1>{title}</h1><p class="lede">{description}</p>{body}<p><a class="button" href="/#contact">Start a repair</a></p></div></section></main>{footer(LOCALES['en'], 'en', asset_prefix=prefix)}</body></html>"""


def render_not_found() -> str:
    title = "Page not found"
    description = "The requested page does not exist. Return to the Graphics Repair Canada home page."
    return f"""<!DOCTYPE html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{description}"><meta name="robots" content="noindex,follow"><meta name="referrer" content="strict-origin-when-cross-origin"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'"><title>{title} | Graphics Repair Canada</title><link rel="stylesheet" href="/assets/style.css"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><script src="/assets/site.js" defer></script></head><body data-locale="en" data-default-country="CA">{header(LOCALES['en'], 'en', asset_prefix='/', anchor_prefix='/')}<main id="main"><section class="legal"><div class="shell legal-copy"><p class="eyebrow">MRC</p><h1>{title}</h1><p class="lede">{description}</p><p><a class="button" href="/">Return home</a></p></div></section></main>{footer(LOCALES['en'], 'en', asset_prefix='/')}</body></html>"""


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
    for kind in ("privacy", "terms"):
        destination = OUTPUT / kind
        destination.mkdir()
        (destination / "index.html").write_text(render_legal(kind), encoding="utf-8")
    (OUTPUT / "404.html").write_text(render_not_found(), encoding="utf-8")
    (OUTPUT / "CNAME").write_text("graphicsrepair.ca\n", encoding="utf-8")
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n", encoding="utf-8")
    urls = [f"{DOMAIN}/", *(f"{DOMAIN}/{locale}/" for locale in LOCALE_ORDER if locale != "en"), f"{DOMAIN}/privacy/", f"{DOMAIN}/terms/"]
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
