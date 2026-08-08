# Graphics Repair Canada

Distinct MRC-branded static site for board-level graphics-card repair and used-GPU verification at [graphicsrepair.ca](https://graphicsrepair.ca/).

The production artifact is generated into `_site/`. It contains only the GPU-focused site; the legacy `docs/` tree is retained as an unpublished architectural source snapshot and is never uploaded by the Pages workflow. The sibling `motherboardrepair-ca` repository is a read-only architectural reference.

## Build and test

```bash
python3 build_graphics_site.py --check
node --check site/assets/site.js
python3 tests/test_graphics_site.py
```

The checks prove:

- one focused production page in English plus approved French, Latin-American Spanish, Vietnamese, Arabic and Japanese localizations;
- correct canonical and hreflang links;
- MRC branding and backlinks to `motherboardrepair.ca`;
- a proof-of-work, honeypot, time-gated form with country-aware mobile validation;
- a `graphicsrepair.ca` CNAME, sitemap and robots policy;
- no session replay, advertising tracker, analytics cookies or form-field analytics;
- a production artifact with no copied motherboard-service pages.

## Deployment

GitHub Actions builds `_site/` and deploys it with the official GitHub Pages artifact workflow from `main`. Run:

```bash
./ship.sh "Describe the release"
```

DNS is managed separately in Cloudflare. Apex and `www` must not move until the Pages deployment is successful and the GitHub Pages target has been proven. Existing MX and TXT records are mail infrastructure and must remain unchanged.

## Service and privacy posture

Service content deliberately avoids outcome guarantees. A form submission is a free assessment request, not acceptance. Customers are told not to ship until instructed. The fixed $50 CAD plus tax service is a non-invasive used-card completeness and listing-consistency check, not a repair diagnostic, performance grade or legal finding of fraud.

The site has no client-side analytics. Aggregate request metrics come from Cloudflare's edge; no session replay or typed form values are collected for analytics. Contact requests are sent to MRC's protected form processor at `forms.motherboardrepair.ca`.
