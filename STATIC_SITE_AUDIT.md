# Static site production audit

Audit date: 2026-08-08  
Scope: generated `_site` artifact and the public `https://graphicsrepair.ca` deployment, across all six approved locales, legal routes, assets, forms, GitHub Pages and Cloudflare DNS.

## Repeatable gate

Run these from the repository root:

```bash
python3 build_graphics_site.py --check
node --check site/assets/site.js
python3 tests/test_graphics_site.py
npx --yes html-validate@latest '_site/**/*.html'
```

Production checks also cover every sitemap route, a nested unknown route, canonical and hreflang links, local-versus-live asset hashes, form-proof CORS for apex and `www`, TLS, redirects, response headers, desktop/mobile Lighthouse, and screenshots at responsive widths.

## Baseline findings and corrections

- Corrected root-relative assets and navigation in the custom 404 so nested unknown URLs render correctly.
- Corrected legal-page header links that previously targeted nonexistent fragments on the legal pages.
- Removed 66 HTML validation findings: normalized the doctype, named or removed invalid landmarks, removed an accessible-name mismatch, and made every input type explicit.
- Replaced the low-contrast accent palette. The nine measured text/button contrast failures now pass WCAG AA in the generated site.
- Localized skip navigation, menu text, navigation landmark names, language landmark names and phone-validation errors for all approved languages.
- Aligned all locales with MRC's actual workflow: the free intake assessment determines acceptance; accepted repair jobs receive a proper diagnostic and quote before any repair work begins.
- Adapted the current motherboardrepair.ca international intake gate for standalone GPUs: mail-in requests identify the return country, and non-Canadian requests require ownership/authorization plus cross-border shipping-cost acknowledgement. Serial/IMEI and battery questions are intentionally excluded.
- Added responsive 480 px and 720 px hero sources, correct intrinsic dimensions, decoding/loading hints and a lazy footer logo. This removes roughly 73 KiB from the typical desktop hero transfer.
- Added an explicit empty request-type option so browser validation requires a deliberate choice.
- Prevented backend error details from being exposed in customer-facing status text.
- Disclosed the language preference stored in local storage and the intake metadata sent with a form request.
- Pinned every GitHub Action to an exact commit, added the JavaScript syntax gate to deployment, and confined Pages write/OIDC permissions to the deployment job.

Baseline live Lighthouse scores were 100 performance, 97 accessibility, 93 best practices and 92 SEO on desktop; mobile performance was 97. After the corrections, the loopback-built artifact scored 100 accessibility and 100 best practices on both profiles, with performance 100 desktop and 99 mobile. Lighthouse's only SEO finding was inability to download `robots.txt`; direct requests repeatedly returned the valid file with HTTP 200, so this was treated as a scanner false positive.

## DNS-only correction

The initial audit found that proxied Cloudflare web records injected a Web Analytics beacon. The site's CSP blocked it, but the injection caused a console error and contradicted the intended no-client-analytics posture. On 2026-08-08, all four apex GitHub Pages A records and the `www` CNAME were changed to `proxied: false`; the then-current MX and TXT records were preserved during that web-only change. Public DNS now resolves the apex directly to GitHub Pages IPv4 targets; the `www` CNAME resolves to GitHub Pages IPv4 and IPv6 targets. Mail was subsequently migrated in a separate authorized change to MRC's Mail-in-a-Box, as recorded in `PRODUCTION_RUNBOOK.md`.

After the DNS-only change, browser-facing HTML contains no Cloudflare beacon, the CSP console error is gone and live desktop Lighthouse best practices scores 100. Cloudflare is not in the HTTP path and its WAF is not used for this site. GitHub Pages does not provide project-defined response headers such as HSTS or `frame-ancestors`; this limitation is accepted rather than adding an unwanted reverse proxy.

## Intentional boundaries

- Mail-in requests ask for a return address during intake to retain the approved MRC contact workflow; the field is conditional and the privacy policy discloses it.
- The approved locale and hreflang set remains `en-CA`, `fr-FR`, `es-419`, `vi-VN`, `ar` and `ja-JP`.
- The $50 CAD plus tax service is named GPU Certification. It records factual observations about an accepted used card's identity, required chips, assemblies and expected configuration to help reveal missing, substituted or changed chips in deceptive marketplace or aftermarket sales. MRC attempts a boot on the shop testing rig and provides a written test report if it boots. It does not assert OEM compliance and is not a repair diagnostic, authenticity guarantee, performance guarantee, warranty or legal determination of fraud.
- Intel graphics cards are normally not accepted.
- Drop-offs are welcome whenever MRC is open; the site does not claim appointments are scheduled.
- Notomo site ID 2 is never reused. The separately created graphics property remains inactive until a replay-free, host-scoped integration can be proven.

## Comprehensive follow-up scan

The 2026-08-08 follow-up rebuilt the artifact and proved that the live homepage
matched it byte for byte before remediation. All six locales, both legal pages,
the sitemap, robots policy, assets and an unknown route returned the expected
status. Safe form checks proved short-lived `no-store` challenges, allowed
apex/`www` CORS preflights and rejection of invalid submissions without sending
a lead.

Repeated live Lighthouse runs produced median scores of 100 performance, 100
accessibility and 100 best practices on mobile and desktop. Median LCP was 1.25
seconds on mobile and 0.33 seconds on desktop, with zero layout shift. The SEO
score remained 92 only because Lighthouse said it could not download
`robots.txt`; direct curl, Chromium and GitHub Pages requests all returned the
valid 70-byte policy with HTTP 200.

This pass corrected an invalid `aria-hidden` form-label pattern, added sticky
header offsets for fragment targets, removed an English-only model placeholder
from translated forms, renamed derived phone metadata as a validation profile,
stopped duplicating mail-in addresses in both message and extra metadata, made
legal review dates explicit, simplified the English search description and
documented form-Worker network diagnostics. W3C validation has no HTML errors;
its remaining JSON-LD CSP notice is informational, while browser best-practices
checks report no console or CSP failure.

The full local SST run passed 264 checks and skipped 709, with 50 reported
failures. Review showed those failures were scanner/environment mismatches:
localhost HTTPS, caching and canonical assumptions; the packaged trailing-slash
lookup bug; GitHub Pages' known header limitation; false tracking matches in
privacy disclosures; and optional sitemap fields. The one actionable SST
finding, English meta readability, was corrected and its focused rerun passed.

The missing MTA-STS discovery marker was added without changing any existing web
or mail record: `_mta-sts.graphicsrepair.ca TXT "v=STSv1; id=2026080801"`.
GitHub Pages still cannot set HSTS, frame protection or `nosniff` response
headers. That residual risk remains accepted while the site stays unproxied and
DNS-only, as required.
