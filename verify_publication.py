#!/usr/bin/env python3
"""Verify deployed page bytes and browser-enforced external script integrity."""
import argparse
import base64
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import time
from urllib.request import Request, urlopen


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.external = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script" and values.get("src", "").startswith("https://"):
            self.external.add((values["src"], values.get("integrity", "")))
        tracker = values.get("data-tracker-src", "")
        if tag == "script" and tracker.startswith("https://"):
            self.external.add((tracker, values.get("data-tracker-integrity", "")))


def check_integrity(site):
    scripts = Scripts()
    for page in site.rglob("*.html"):
        scripts.feed(page.read_text(encoding="utf-8"))
    for url, integrity in scripts.external:
        if not integrity:
            raise ValueError(f"External script lacks integrity: {url}")
        with urlopen(url, timeout=20) as response:
            content = response.read()
            cors = response.headers.get("Access-Control-Allow-Origin")
        valid = False
        for token in integrity.split():
            algorithm, expected = token.split("-", 1)
            actual = base64.b64encode(hashlib.new(algorithm, content).digest()).decode()
            valid |= actual == expected
        if not valid or cors != "*":
            raise ValueError(f"External script integrity or anonymous CORS mismatch: {url}")
    print(f"Verified integrity and anonymous CORS for {len(scripts.external)} external script(s).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("_site"))
    parser.add_argument("--domain")
    parser.add_argument("--revision", default="acceptance")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if not (args.site / "index.html").is_file():
        raise FileNotFoundError("Build the site before checking publication.")
    check_integrity(args.site)
    if not args.domain:
        return
    expected = {str(p.relative_to(args.site)): p.read_bytes() for p in args.site.rglob("*.html") if p.name != "404.html"}
    expected["assets/site.js"] = (args.site / "assets/site.js").read_bytes()
    expected["assets/notomo-loader.js"] = (args.site / "assets/notomo-loader.js").read_bytes()
    deadline = time.monotonic() + args.timeout
    pending = dict(expected)
    while pending and time.monotonic() < deadline:
        for path, content in list(pending.items()):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                request = Request(f"https://{args.domain}/{path}?revision={args.revision}", headers={"Cache-Control": "no-cache"})
                with urlopen(request, timeout=min(15, remaining)) as response:
                    if response.read() == content:
                        del pending[path]
            except OSError:
                pass
        if pending:
            time.sleep(max(0, min(5, deadline - time.monotonic())))
    if pending:
        raise RuntimeError(f"Published files differ at {args.domain}: {', '.join(pending)}")
    print(f"Verified {len(expected)} published files at https://{args.domain}/")


if __name__ == "__main__":
    main()
