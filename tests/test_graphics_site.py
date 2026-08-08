#!/usr/bin/env python3
"""Production artifact checks for Graphics Repair Canada."""

from __future__ import annotations

import re
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
LOCALES = {"en": "en-CA", "fr": "fr-FR", "es": "es-419", "vi": "vi-VN", "ar": "ar", "ja": "ja-JP"}
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
        html_tags = [attrs for name, attrs in parser.tags if name == "html"]
        assert html_tags and html_tags[0].get("lang") == tag
        assert len([1 for name, _attrs in parser.tags if name == "h1"]) == 1
        assert {"faults", "process", "used-check", "contact", "repair-form", "form-status"} <= parser.ids
        text = " ".join(parser.text).lower()
        for required in ("mrc", "gpu", "50"):
            assert required in text, f"{path} is missing {required}"
        assert "session replay" not in source.lower()
        assert "notomo" not in source.lower()
        assert "google-analytics" not in source.lower()
        assert "googletagmanager" not in source.lower()
        assert "plausible" not in source.lower()
        assert 'form_id" value="graphics_card_repair_quote"' in source
        for field_name in (
            "name", "email", "country", "phone", "model", "serial_number",
            "request_type", "message", "service_type", "mailing_address",
            "unit_number", "accept_terms",
        ):
            assert re.search(rf'name="{field_name}"', source), f"{path} is missing form field {field_name}"
        assert 'option value="In-Person"' in source
        assert 'option value="Mail-In"' in source
        assert 'id="mailing-fields"' in source and " hidden" in source
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
                    assert parsed.netloc in {"graphicsrepair.ca", "motherboardrepair.ca"}

    english = (SITE / "index.html").read_text(encoding="utf-8").lower()
    assert "used graphics card completeness check" in english
    assert "this is not a repair diagnostic" in english
    assert "material misrepresentation" in english

    js = (SITE / "assets/site.js").read_text(encoding="utf-8")
    for country in COUNTRIES:
        assert re.search(rf"\b{country}: \{{ code:", js), f"Missing phone rule for {country}"
    for protection in ("form-proof", "form_proof_token", "form_proof_counter", "leadingZeros", "website", "start_time"):
        assert protection in js
    assert "document.cookie" not in js
    assert "sendBeacon" not in js
    assert "forms.motherboardrepair.ca/api/submit" in js
    for intake_contract in (
        "setupMailingFields", "address.required = mailIn", "serial_number",
        "request_type", "mailing_address", "unit_number", "Graphics card:",
        "Request details:",
    ):
        assert intake_contract in js

    css = (SITE / "assets/style.css").read_text(encoding="utf-8")
    assert ".form-row { display: grid; grid-template-columns: 1fr 1fr; align-items: start;" in css
    assert '.repair-form input:not([type="checkbox"]), .repair-form select { min-height: 48px; }' in css

    for legal_kind in ("privacy", "terms"):
        legal_parser, legal_source = parse(SITE / legal_kind / "index.html")
        legal_canonical = [attrs.get("href") for name, attrs in legal_parser.tags if name == "link" and attrs.get("rel") == "canonical"]
        assert legal_canonical == [f"https://graphicsrepair.ca/{legal_kind}/"]
        assert f'href="/{legal_kind}/"' in legal_source
        assert 'href="../assets/style.css"' in legal_source
        assert 'src="../assets/mrc-logo-white.svg"' in legal_source

    terms = (SITE / "terms" / "index.html").read_text(encoding="utf-8").lower()
    assert "it is not a repair diagnostic" in terms

    not_found = (SITE / "404.html").read_text(encoding="utf-8")
    assert "Page not found" in not_found
    assert 'content="noindex,follow"' in not_found
    assert 'href="assets/style.css"' in not_found
    assert "Information we collect" not in not_found

    privacy = (SITE / "privacy" / "index.html").read_text(encoding="utf-8").lower()
    for disclosure in ("no form text is sent to analytics", "do not run advertising analytics", "session replay", "aggregate edge traffic metrics", "cloudflare", "github"):
        assert disclosure in privacy

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
    print("✓ protected country-aware form")
    print("✓ cookie-free, replay-free metrics posture")
