#!/usr/bin/env python3
"""Production artifact checks for Graphics Repair Canada."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
LOCALES = {"en": "en-CA", "fr": "fr-CA", "es": "es-419", "vi": "vi-VN", "ar": "ar", "ja": "ja-JP"}
COUNTRIES = {"CA", "FR", "ES", "VN", "SA", "MX", "JP", "CO", "EG", "MA"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.tags.append((tag, values))
        if values.get("id"):
            self.ids.add(values["id"])

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def parse(path: Path) -> tuple[PageParser, str]:
    source = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(source)
    return parser, source


def validate_site() -> None:
    assert (SITE / "CNAME").read_text(encoding="utf-8") == "graphicsrepair.ca\n"
    expected_pages = {"index.html", "privacy/index.html", "terms/index.html", "404.html"}
    expected_pages.update(f"{locale}/index.html" for locale in LOCALES if locale != "en")
    actual_pages = {path.relative_to(SITE).as_posix() for path in SITE.rglob("*.html")}
    assert actual_pages == expected_pages, f"Unexpected production pages: {sorted(actual_pages ^ expected_pages)}"

    public_copy = "\n".join(path.read_text(encoding="utf-8").lower() for path in SITE.rglob("*.html"))
    for unsupported_scheduling_claim in (
        "scheduled drop-off",
        "scheduled kitchener",
        "dépôt planifié",
        "entrega programada",
        "giao theo lịch",
        "تسليم مجدول",
        "予約持込",
    ):
        assert unsupported_scheduling_claim not in public_copy

    for walk_in_copy in (
        "drop-offs are welcome whenever we are open",
        "sans rendez-vous",
        "cuando estemos abiertos",
        "không cần hẹn trước",
        "من دون موعد",
        "予約なしで持ち込み",
    ):
        assert walk_in_copy in public_copy

    for locale, tag in LOCALES.items():
        path = SITE / ("index.html" if locale == "en" else f"{locale}/index.html")
        parser, source = parse(path)
        assert source.startswith("<!DOCTYPE html>")
        html_tags = [attrs for name, attrs in parser.tags if name == "html"]
        assert html_tags and html_tags[0].get("lang") == tag
        assert len([1 for name, _attrs in parser.tags if name == "h1"]) == 1
        assert {"faults", "process", "gpu-certification", "contact", "repair-form", "form-status"} <= parser.ids
        text = " ".join(parser.text).lower()
        for required in ("mrc", "gpu", "50"):
            assert required in text, f"{path} is missing {required}"
        assert "session replay" not in source.lower()
        assert source.count('src="https://notomo.colinknapp.com/n.js"') == 1
        assert source.count('data-site-id="graphicsrepair.ca"') == 1
        assert 'data-site-id="2"' not in source
        assert "script-src 'self' 'wasm-unsafe-eval'" in source
        assert "https://notomo.colinknapp.com/n.js" in source
        assert "https://notomo.colinknapp.com/n-rrweb.js" in source
        assert "connect-src 'self' https://forms.motherboardrepair.ca https://notomo.colinknapp.com/collect https://notomo.colinknapp.com/replay https://notomo.colinknapp.com/n-config/graphicsrepair.ca" in source
        assert "sha384-NBbFxiYXSJk326gDu3z2Ak3usWitZIBpVRhbqjBxVynTBnvrnFnHlG+AcLKZf8te" in source
        assert "google-analytics" not in source.lower()
        assert "googletagmanager" not in source.lower()
        assert "plausible" not in source.lower()
        assert 'form_id" value="graphics_card_repair_quote"' in source
        for field_name in (
            "name", "email", "phone", "model",
            "request_type", "message", "service_type", "mailing_address",
            "unit_number", "return_country", "province", "ownership_confirmed",
            "international_shipping_ack", "rush_service", "accept_terms",
        ):
            assert re.search(rf'name="{field_name}"', source), f"{path} is missing form field {field_name}"
        rush = [attrs for name, attrs in parser.tags if name == "input" and attrs.get("name") == "rush_service"]
        assert len(rush) == 1 and rush[0].get("type") == "checkbox"
        assert not {"checked", "required", "disabled"} & rush[0].keys()
        assert "serial_number" not in source
        assert "device_serial" not in source
        assert "battery_status" not in source
        assert "imei" not in source.lower()
        assert 'option value="In-Person"' in source
        assert 'option value="Mail-In"' in source
        assert 'id="mailing-fields"' in source and " hidden" in source
        assert 'id="international-mailing-fields"' in source
        assert 'name="return_country" id="return_country"' in source
        assert 'autocomplete="country-name"' in source
        assert 'name="mailing_address" rows="3" maxlength="300" autocomplete="street-address" aria-describedby="address-hint" disabled' in source
        assert 'name="unit_number" type="text" maxlength="30" autocomplete="address-line2" disabled' in source
        assert 'name="province" type="text" maxlength="100" autocomplete="address-level1" disabled' in source
        assert 'role="group" aria-labelledby="international-title" hidden' in source
        assert 'name="ownership_confirmed" type="checkbox" value="confirmed" disabled' in source
        assert 'name="international_shipping_ack" type="checkbox" value="accepted" disabled' in source
        for return_country in COUNTRIES | {"OTHER"}:
            assert f'<option value="{return_country}">' in source
        assert 'id="phone-validation-profile"' in source
        assert 'data-international-label="' in source
        assert 'data-error="' in source
        if locale == "en":
            assert 'name="english_support_preference"' not in source
        else:
            assert re.search(
                r'name="english_support_preference" required[^>]*>.*?'
                r'<option value="no">.*?</option><option value="yes">',
                source,
                re.DOTALL,
            )
        assert 'name="country"' not in source
        assert 'placeholder="e.g. ASUS TUF RTX 3080 10GB"' not in source
        assert '<div class="auxiliary-field" inert>' in source
        assert 'data-repair-prompt hidden' in source
        assert 'data-repair-dismiss' in source
        assert 'name="accept_terms" type="checkbox" required' in source
        assert 'href="/privacy/" target="_blank" rel="noopener"' in source
        assert 'href="/terms/" target="_blank" rel="noopener"' in source
        assert all(attrs.get("type") for name, attrs in parser.tags if name == "input")
        assert 'srcset="' in source and "gpu-repair-480.webp 480w" in source and "gpu-repair-720.webp 720w" in source
        for fragment in ("faults", "process", "gpu-certification", "contact"):
            assert f'href="#{fragment}"' in source
        assert "https://motherboardrepair.ca/" in source
        assert source.count('rel="alternate" hreflang=') == 7
        canonical = [attrs.get("href") for name, attrs in parser.tags if name == "link" and attrs.get("rel") == "canonical"]
        expected_url = "https://graphicsrepair.ca/" if locale == "en" else f"https://graphicsrepair.ca/{locale}/"
        assert canonical == [expected_url]

        for name, attrs in parser.tags:
            for attribute in ("href", "src"):
                target = attrs.get(attribute, "")
                if not target or target.startswith(("#", "mailto:", "tel:", "data:")):
                    continue
                parsed = urlparse(target)
                if parsed.scheme:
                    assert parsed.scheme == "https"
                    assert parsed.netloc in {"graphicsrepair.ca", "motherboardrepair.ca", "notomo.colinknapp.com"}

    english = (SITE / "index.html").read_text(encoding="utf-8").lower()
    assert "mrc provides graphics card repair and used gpu checks. canada is our main market" in english
    assert "we review overseas mail-in requests one by one" in english
    assert "graphics card repair starts with a diagnosis and quote" in english
    assert "we review your request for free. diagnosis is a separate step" in english
    assert "once your card arrives, we diagnose it and give you a quote" in english
    assert "no repair work begins without your approval" in english
    assert "displayed phone format" in english
    assert "detected country" not in english
    assert "gpu certification" in english
    assert "not a repair diagnostic" in english
    assert "missing, substituted or changed chips" in english
    assert "deceptive online sales" in english
    assert "does not certify that the card meets the manufacturer’s standards" in english
    assert "chips and other required parts are present" in english
    assert "shop’s test system" in english
    assert "written test report" in english
    assert "we don’t normally accept intel graphics cards" in english
    assert "nvidia · amd · intel" not in english
    assert "nvidia · amd</small>" in english
    assert "country where the card is located and will be returned" in english
    assert "i’ve had time to review, and i accept the" in english
    assert "send protected request" not in english
    assert "protected by a time delay" not in english
    assert "international mail-in details" in english
    assert "shipping, customs, duties, taxes, brokerage, insurance and return costs" in english
    for stale_claim in (
        "diagnosed before it is promised",
        "diagnostic avant toute promesse",
        "diagnóstico antes de prometer",
        "chẩn đoán trước khi cam kết",
        "إصلاح بطاقات الرسومات بعد التشخيص",
        "約束する前に診断する",
    ):
        assert stale_claim not in public_copy

    locale_workflow_markers = {
        "fr": ("l’étude de votre demande est gratuite", "aucune réparation ne commence sans votre accord"),
        "es": ("revisamos su solicitud sin costo", "no comenzaremos ninguna reparación sin su aprobación"),
        "vi": ("chúng tôi xem xét yêu cầu của bạn miễn phí", "chúng tôi không bắt đầu sửa chữa nếu chưa có sự chấp thuận của bạn"),
        "ar": ("نراجع طلبك مجاناً", "لا يبدأ الإصلاح من دون موافقتك"),
        "ja": ("依頼内容の確認は無料です", "お客様の承認なしに修理を始めることはありません"),
    }
    for locale, markers in locale_workflow_markers.items():
        localized = (SITE / locale / "index.html").read_text(encoding="utf-8").lower()
        assert all(marker in localized for marker in markers)
    localized_international_titles = {
        "fr": "détails de l’envoi international",
        "es": "datos del envío internacional",
        "vi": "thông tin gửi bưu điện quốc tế",
        "ar": "تفاصيل الإرسال الدولي",
        "ja": "海外郵送の詳細",
    }
    for locale, title in localized_international_titles.items():
        localized = (SITE / locale / "index.html").read_text(encoding="utf-8").lower()
        assert title in localized
    assert (SITE / "assets" / "gpu-repair-480.webp").stat().st_size < 60_000
    assert (SITE / "assets" / "gpu-repair-720.webp").stat().st_size < 100_000

    js = (SITE / "assets/site.js").read_text(encoding="utf-8")
    for country in COUNTRIES:
        assert re.search(rf"\b{country}: \{{ code:", js), f"Missing phone rule for {country}"
    for submission_contract in ("contactForm.submitProtectedPayload", "website", "start_time"):
        assert submission_contract in js
    for local_name in ("submitLeadPayload", "setupRepairPrompt"):
        assert local_name in js
    for removed_proof_implementation in ("prepareSubmission", "submissionBinding", "meetsTarget", "form_proof_token"):
        assert removed_proof_implementation not in js
    assert "Protected form submission" not in js
    assert "document.cookie" not in js
    assert "sendBeacon" not in js
    assert "forms.motherboardrepair.ca/api/submit" not in js
    assert "console.error('Form submission failed:', error)" in js
    for intake_contract in (
        "setupMailingFields", "setupPhone", "address.required = mailIn",
        "request_type", "mailing_address", "unit_number", "buildLeadPayload", "submitLeadPayload",
        "rush_service", "rush_fee: rushService ? 130 : undefined",
        "normalizeSiteLanguage", "digits.startsWith('1') ? 'CA'", "phoneSetup.profile()",
        "english_support_preference", "replyPreference ? replyPreference.value : undefined",
        "returnCountry.required = mailIn", "returnCountry.disabled = !mailIn",
        "province.required = mailIn", "province.disabled = !mailIn",
        "address.disabled = !mailIn", "unitNumber.disabled = !mailIn",
        "returnCountry.value !== 'CA'", "internationalFields.hidden = !international",
        "ownershipConfirmed.required = Boolean(international)",
        "shippingAcknowledged.required = Boolean(international)",
        "province: province || undefined", "country: returnCountry || undefined",
        "return_country: returnCountry || undefined", "international_mail_in: internationalMailIn",
        "country = match || 'INTL'", "detected === 'INTL'", "^[1-9]\\d{6,14}$",
        "return '+' + phone.value.replace(/\\D/g, '').slice(0, 15)",
    ):
        assert intake_contract in js
    assert "serial" not in js.lower()
    assert "phone.setCustomValidity(valid ? '' : phone.dataset.error)" in js
    assert "form.dataset.error + ' ('" not in js
    assert "message: message" in js
    assert "messageParts" not in js
    assert "mailing_address: mailingAddress || undefined" in js
    assert "unit_number: unitNumber || undefined" in js

    manifest = json.loads((SITE / "contact-embed/manifest.json").read_text(encoding="utf-8"))
    for filename, key in (
        ("contact-form.wasm", "sha256"),
        ("loader.js", "loader_sha256"),
        ("wasm_exec.js", "wasm_exec_sha256"),
    ):
        assert hashlib.sha256((SITE / "contact-embed" / filename).read_bytes()).hexdigest() == manifest[key]
    assert manifest["source_repository"] == "Leopere/motherboardrepair-contact"
    assert (SITE / "js/contact-form.min.js").is_file()
    assert "ContactForm" in (SITE / "js/contact-form.min.js").read_text(encoding="utf-8")
    for locale in LOCALES:
        if locale != "en":
            assert (SITE / locale / "js/contact-form.min.js").is_file()

    for locale in LOCALES:
        page = SITE / ("index.html" if locale == "en" else f"{locale}/index.html")
        source = page.read_text(encoding="utf-8")
        assert source.index('src="/contact-embed/loader.js"') < source.index('src="/assets/site.js"')
        assert "'wasm-unsafe-eval'" in source

    css = (SITE / "assets/style.css").read_text(encoding="utf-8")
    assert ".form-row { display: grid; grid-template-columns: 1fr 1fr; align-items: start;" in css
    assert '.repair-form input:not([type="checkbox"]), .repair-form select { min-height: 48px; }' in css
    assert "#faults, #process, #gpu-certification, #contact { scroll-margin-block-start: 7rem; }" in css
    assert "@keyframes repair-prompt-shimmer" in css

    for legal_kind in ("privacy", "terms"):
        legal_parser, legal_source = parse(SITE / legal_kind / "index.html")
        legal_canonical = [attrs.get("href") for name, attrs in legal_parser.tags if name == "link" and attrs.get("rel") == "canonical"]
        assert legal_canonical == [f"https://graphicsrepair.ca/{legal_kind}/"]
        assert "MRC · Updated 2026-09-09" in legal_source
        assert f'href="/{legal_kind}/"' in legal_source
        assert 'href="../assets/style.css"' in legal_source
        assert 'src="../assets/mrc-logo-white.svg"' in legal_source
        assert 'href="https://motherboardrepair.ca/"' in legal_source
        assert 'https://motherboardrepair.ca/graphics-card-repair.html' not in legal_source
        assert 'property="og:title"' in legal_source
        assert 'property="og:description"' in legal_source
        assert 'property="og:image" content="https://graphicsrepair.ca/assets/gpu-repair.webp"' in legal_source
        assert 'name="twitter:card" content="summary_large_image"' in legal_source
        assert 'name="twitter:title"' in legal_source
        assert 'name="twitter:description"' in legal_source
        assert 'name="twitter:image" content="https://graphicsrepair.ca/assets/gpu-repair.webp"' in legal_source
        assert '"@type":"WebPage"' in legal_source
        for fragment in ("faults", "process", "gpu-certification", "contact"):
            assert f'href="/#{fragment}"' in legal_source

    terms = (SITE / "terms" / "index.html").read_text(encoding="utf-8").lower()
    assert "is not a repair diagnostic" in terms
    assert "missing, substituted or changed chips" in terms
    assert "does not certify that the card meets the manufacturer’s standards" in terms
    assert "written test report" in terms
    assert "shop’s test system" in terms
    assert "canada is our main market" in terms
    assert "international mail-in service is available only for jobs mrc accepts" in terms
    assert "shipping, customs, duties, taxes, brokerage, insurance and return costs" in terms
    assert "we review your request for free to decide whether we can take the job" in terms
    assert "once a card we have agreed to work on arrives, we diagnose it and give you a quote" in terms

    not_found = (SITE / "404.html").read_text(encoding="utf-8")
    assert "Page not found" in not_found
    assert 'content="noindex,follow"' in not_found
    assert 'href="/assets/style.css"' in not_found
    assert 'src="/assets/site.js"' in not_found
    assert 'src="/assets/mrc-logo.svg"' in not_found
    assert 'src="/assets/mrc-logo-white.svg"' in not_found
    for fragment in ("faults", "process", "gpu-certification", "contact"):
        assert f'href="/#{fragment}"' in not_found
    assert "Information we collect" not in not_found
    assert not_found.count('src="https://notomo.colinknapp.com/n.js"') == 1
    assert 'data-site-id="graphicsrepair.ca"' in not_found
    assert "script-src 'self' 'wasm-unsafe-eval'" in not_found
    assert "https://notomo.colinknapp.com/n-rrweb.js" in not_found

    privacy = (SITE / "privacy" / "index.html").read_text(encoding="utf-8").lower()
    assert "our privacy policy explains how we use your contact details. it also covers what this site records while you visit." in privacy
    terms_source = (SITE / "terms" / "index.html").read_text(encoding="utf-8").lower()
    assert "these service terms explain how repair requests work. read about quotes, rush service and shipping before you send your device." in terms_source
    for disclosure in (
        "self-hosted notomo", "random visitor and session identifiers", "session replay",
        "literal text entered into website fields as you type", "before you submit the form",
        "cloudflare", "github", "drop-off or mail-in choice",
        "phone validation profile", "page language", "local storage",
        "selected text-message reply language",
        "return country", "province, state or region", "ownership or owner-authorization confirmation",
        "international-mail-in status", "cross-border shipping costs",
    ):
        assert disclosure in privacy
    for legal_kind in ("privacy", "terms"):
        legal_source = (SITE / legal_kind / "index.html").read_text(encoding="utf-8")
        assert legal_source.count('src="https://notomo.colinknapp.com/n.js"') == 1
        assert 'data-site-id="graphicsrepair.ca"' in legal_source
        assert "script-src 'self' 'wasm-unsafe-eval'" in legal_source
        assert "https://notomo.colinknapp.com/n-rrweb.js" in legal_source
    for exposed_implementation in ("honeypot", "minimum completion time", "rate limiting", "proof-of-work", "protected form processing"):
        assert exposed_implementation not in privacy

    deploy = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    build_workflow = (ROOT / ".github/workflows/build-and-test.yml").read_text(encoding="utf-8")
    assert "actions/checkout@v" not in deploy + build_workflow
    assert "actions/setup-python@v" not in deploy + build_workflow
    assert "actions/configure-pages@v" not in deploy
    assert "actions/upload-pages-artifact@v" not in deploy
    assert "actions/deploy-pages@v" not in deploy
    assert deploy.count("pages: write") == 1
    assert deploy.count("id-token: write") == 1
    assert "node --check site/assets/site.js" in deploy
    assert "node --test tests/test_lead_payload.js" in deploy
    assert "node --test tests/test_lead_payload.js" in build_workflow
    assert "ubuntu-latest" not in deploy + build_workflow
    assert (deploy + build_workflow).count("runs-on: [self-hosted, Linux, ARM64, leopere, local]") == 3

    sitemap = ET.parse(SITE / "sitemap.xml").getroot()
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = {node.text for node in sitemap.findall("s:url/s:loc", namespace)}
    assert len(urls) == 8
    assert "https://graphicsrepair.ca/" in urls
    assert "https://graphicsrepair.ca/privacy/" in urls
    assert "https://graphicsrepair.ca/terms/" in urls
    assert all(url and url.startswith("https://graphicsrepair.ca/") for url in urls)


def test_production_artifact() -> None:
    subprocess.run(["python3", str(ROOT / "build_graphics_site.py")], cwd=ROOT, check=True)
    validate_site()


if __name__ == "__main__":
    test_production_artifact()
    print("✓ distinct GPU production artifact")
    print("✓ six approved locales and hreflang graph")
    print("✓ country-aware repair form")
    print("✓ dedicated full-capture Notomo posture")
