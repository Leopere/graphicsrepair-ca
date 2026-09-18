#!/usr/bin/env python3
"""Browser contract for the committed Go/WASM contact runtime."""

from __future__ import annotations

import functools
import http.server
import json
import os
import shutil
import socketserver
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return


def browser_executable() -> str | None:
    candidates = (
        os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    )
    return next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)


def test_wasm_submission_contract() -> None:
    handler = functools.partial(QuietHandler, directory=SITE)
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    payload: dict[str, object] = {}
    wasm_requested = False

    try:
        with sync_playwright() as playwright:
            executable = browser_executable()
            browser = playwright.chromium.launch(executable_path=executable) if executable else playwright.chromium.launch()
            page = browser.new_page()

            def observe_request(request) -> None:
                nonlocal wasm_requested
                if request.url.endswith("/contact-embed/contact-form.wasm?v=1d608f6bad6e2fa5cb6431be16880846bd072f79b9213e8f37e7dc83ce5805ff"):
                    wasm_requested = True

            def proof(route) -> None:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({
                        "challenge": "graphics-wasm-browser-contract",
                        "difficulty": 0,
                        "ready_at": 0,
                        "expires_at": 9_999_999_999_999,
                    }),
                )

            def submit(route) -> None:
                payload.update(route.request.post_data_json)
                route.fulfill(
                    status=202,
                    content_type="application/json",
                    body='{"ok":true,"success":true,"status":"queued"}',
                )

            page.on("request", observe_request)
            page.route("https://forms.motherboardrepair.ca/api/form-proof", proof)
            page.route("https://forms.motherboardrepair.ca/api/submit", submit)
            page.goto(f"http://127.0.0.1:{server.server_address[1]}/", wait_until="domcontentloaded")
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                active = page.locator("html").evaluate(
                    "() => Boolean(window.MRCContactWASM && window.ContactForm === window.MRCContactWASM)"
                )
                if active:
                    break
                page.wait_for_timeout(50)
            else:
                raise AssertionError("Go/WASM contact runtime did not activate")
            page.locator('[name="name"]').fill("WASM Browser Contract")
            page.locator('[name="email"]').fill("production-acceptance@example.com")
            page.locator('[name="phone"]').fill("+1 226-555-0100")
            page.locator('[name="model"]').fill("Test RTX 3080")
            page.locator('[name="request_type"]').select_option("repair")
            page.locator('[name="message"]').fill("Intercepted browser contract; no production lead is created.")
            page.locator('[name="service_type"]').select_option("In-Person")
            assert not page.locator('[name="rush_service"]').is_checked()
            page.locator('[name="rush_service"]').check()
            page.locator('[name="accept_terms"]').check()
            page.locator('#repair-form button[type="submit"]').click()
            page.locator("#form-status.success").wait_for(state="visible")
            assert not page.locator('[name="rush_service"]').is_checked()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert wasm_requested
    assert payload["form_id"] == "graphics_card_repair_quote"
    assert payload["extra_fields"]["graphics_card_model"] == "Test RTX 3080"
    assert payload["extra_fields"]["rush_service"] is True
    assert payload["extra_fields"]["rush_fee"] == 130
    assert "form_proof_token" in payload
    assert "form_proof_counter" in payload


if __name__ == "__main__":
    test_wasm_submission_contract()
    print("✓ Graphics Repair uses the committed Go/WASM contact runtime")
