# Graphics Repair Canada

Distinct MRC-branded static site for board-level graphics-card repair and used-GPU verification at [graphicsrepair.ca](https://graphicsrepair.ca/).

The production artifact is generated into `_site/`. It contains only the GPU-focused site; the legacy `docs/` tree is retained as an unpublished architectural source snapshot and is never uploaded by the Pages workflow. The sibling `motherboardrepair-ca` repository is a read-only architectural reference.

## Build and test

```bash
python3 build_graphics_site.py --check
node --check site/assets/site.js
node --check site/assets/notomo-loader.js
node --test tests/test_lead_payload.js tests/test_notomo_loader.js
python3 tests/test_pages_delivery.py
python3 tests/test_graphics_site.py
```

The checks prove:

- one focused production page in English plus approved French, Latin-American Spanish, Vietnamese, Arabic and Japanese localizations;
- correct canonical and hreflang links;
- MRC branding and backlinks to `motherboardrepair.ca`;
- a proof-of-work, honeypot, time-gated form with country-aware mobile validation;
- a `graphicsrepair.ca` CNAME, sitemap and robots policy;
- self-hosted Notomo pageview analytics and full session replay, including literal form-field recording;
- a production artifact with no copied motherboard-service pages.

Run the project-specific static-site policy with the local SST installation:

```bash
python3 ../consolerepair-ca/scan_sst.py --repo . --sst-repo ../static-site-tests --output audits/local-graphics
```

[`sst.yml`](sst.yml) sets no minimum keyword density, so the test suite never
pressures authors to repeat phrases. It defines a maximum per page, tracks the
approved service vocabulary in every locale, and requires configuration for
every sitemap URL. English Flesch checks do not apply to translated copy. Canonical directory paths share the same settings as SST's normalized paths; all configured density ceilings remain within SST's valid range.

## Deployment

Native `ship-it` hooks commit and push completed work. The tracked `deploy-it` contract then runs `python3 deploy_pages.py` to refresh the existing GitHub Pages workflows for `graphicsrepair.ca`, `graphicsrepair.com`, `fixgpu.ca` and `gpufix.ca`.

The handoff uses the existing authenticated GitHub CLI configuration. It checks that the shared source still matches the pushed revision and verifies the published forms in all six languages, terms, privacy copy and submission JavaScript against that revision. It does not change DNS or publish the legacy `docs/` snapshot.

Check the shipped contract and existing Pages access without deploying. The contract check requires the new manifest to have been shipped first:

```bash
deploy-it check
python3 deploy_pages.py --check
```

DNS is managed separately in Cloudflare. Apex and `www` must not move until the Pages deployment is successful and the GitHub Pages target has been proven. Both web records must remain DNS-only so Cloudflare does not proxy site traffic or enable its WAF. Mail is handled by MRC's Mail-in-a-Box; preserve the MX, SPF, DKIM, DMARC and MTA-STS records documented in `PRODUCTION_RUNBOOK.md`.

## Service and privacy posture

Rush service is an optional $130 addition for drop-off or mail-in requests. The checkbox starts unchecked. The submitted request includes the rush choice and includes its fee only when selected.

Service content deliberately avoids outcome guarantees. A form submission starts a free intake assessment that determines whether MRC will accept the job; it is not the repair diagnostic. Customers are told not to ship until instructed. After an accepted card arrives, MRC performs a proper diagnostic and provides a quote before any repair work begins. Canada is the main market; international mail-in requests collect the return country and require ownership and cross-border-cost acknowledgements before submission. The fixed $50 CAD plus tax service is named GPU Certification. It records factual observations about an accepted used card's identity, chip population and expected configuration to help expose missing, substituted or changed chips in deceptive marketplace or aftermarket sales. MRC attempts a boot on the shop testing rig and provides a written test report if it boots. The certification does not assert OEM compliance and is not a repair diagnostic, authenticity guarantee, performance guarantee, warranty or legal finding of fraud.

The site uses the dedicated `graphicsrepair.ca` property in MRC's self-hosted Notomo service for pageview analytics, browser errors and full session replay. `www.graphicsrepair.ca`, `fixgpu.ca` and `gpufix.ca` report into that property. `graphicsrepair.com` is a sibling property grouped on the same dashboard because Notomo cannot register `.com` and `.ca` on one allowlist. Notomo records page contents, interactions and literal text entered into form fields as it is typed. Cloudflare is authoritative DNS only and does not proxy page requests. Contact requests are sent to MRC's form service at `forms.motherboardrepair.ca`.

The [publication audit and keyword review](../consolerepair-ca/audits/2026-09-09/site-audit.md) cover this source and its three aliases. Recheck current Trends evidence before copy publications; a rising generic phrase is not proof of demand for GPU repairs. `verify_publication.py` validates the external analytics script hash and anonymous CORS. The native deployment command checks that script before refreshing and byte-verifying all four public sites.
