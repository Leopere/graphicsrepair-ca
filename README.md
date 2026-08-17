# Graphics Repair Canada

Distinct MRC-branded static site for board-level graphics-card repair and used-GPU verification at [graphicsrepair.ca](https://graphicsrepair.ca/).

The production artifact is generated into `_site/`. It contains only the GPU-focused site; the legacy `docs/` tree is retained as an unpublished architectural source snapshot and is never uploaded by the Pages workflow. The sibling `motherboardrepair-ca` repository is a read-only architectural reference.

## Build and test

```bash
python3 build_graphics_site.py --check
node --check site/assets/site.js
node --test tests/test_lead_payload.js
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

Run the project-specific static-site policy with the local SST installation:

```bash
/Volumes/macmini\ dump/Dev/static-site-tests/dist/sst run "$PWD" --json
```

[`sst.yml`](sst.yml) sets no minimum keyword density, so the test suite never
pressures authors to repeat phrases. It defines a maximum per page, tracks the
approved service vocabulary in every locale, and requires configuration for
every sitemap URL. The localized-page notes document SST's current ASCII-only
word denominator; every configured ceiling remains within SST's valid range.

## Deployment

GitHub Actions builds `_site/` and deploys it with the official GitHub Pages artifact workflow from `main`. Run:

```bash
./ship.sh "Describe the release"
```

DNS is managed separately in Cloudflare. Apex and `www` must not move until the Pages deployment is successful and the GitHub Pages target has been proven. Both web records must remain DNS-only so Cloudflare does not proxy site traffic or enable its WAF. Mail is handled by MRC's Mail-in-a-Box; preserve the MX, SPF, DKIM, DMARC and MTA-STS records documented in `PRODUCTION_RUNBOOK.md`.

## Service and privacy posture

Service content deliberately avoids outcome guarantees. A form submission starts a free intake assessment that determines whether MRC will accept the job; it is not the repair diagnostic. Customers are told not to ship until instructed. After an accepted card arrives, MRC performs a proper diagnostic and provides a quote before any repair work begins. Canada is the main market; international mail-in requests collect the return country and require ownership and cross-border-cost acknowledgements before submission. The fixed $50 CAD plus tax service is named GPU Certification. It records factual observations about an accepted used card's identity, chip population and expected configuration to help expose missing, substituted or changed chips in deceptive marketplace or aftermarket sales. MRC attempts a boot on the shop testing rig and provides a written test report if it boots. The certification does not assert OEM compliance and is not a repair diagnostic, authenticity guarantee, performance guarantee, warranty or legal finding of fraud.

The site has no client-side analytics. Cloudflare is authoritative DNS only and does not proxy page requests; no session replay or typed form values are collected for analytics. Contact requests are sent to MRC's form service at `forms.motherboardrepair.ca`.
