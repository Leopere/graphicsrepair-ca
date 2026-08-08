# Static site production audit

Audit date: 2026-08-08  
Scope: generated `_site` artifact and the public `https://graphicsrepair.ca` deployment, across all six approved locales, legal routes, assets, forms, GitHub Pages and Cloudflare delivery.

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
- Aligned non-English process claims with the qualified English intake scope; the site no longer promises a diagnosis, parts decision or price before billable work.
- Added responsive 480 px and 720 px hero sources, correct intrinsic dimensions, decoding/loading hints and a lazy footer logo. This removes roughly 73 KiB from the typical desktop hero transfer.
- Added an explicit empty request-type option so browser validation requires a deliberate choice.
- Prevented backend error details from being exposed in customer-facing status text.
- Disclosed the language preference stored in local storage and the intake metadata sent with a form request.
- Pinned every GitHub Action to an exact commit, added the JavaScript syntax gate to deployment, and confined Pages write/OIDC permissions to the deployment job.

Baseline live Lighthouse scores were 100 performance, 97 accessibility, 93 best practices and 92 SEO on desktop; mobile performance was 97. After the corrections, the loopback-built artifact scored 100 accessibility and 100 best practices on both profiles, with performance 100 desktop and 99 mobile. Lighthouse's only SEO finding was inability to download `robots.txt`; direct requests repeatedly returned the valid file with HTTP 200, so this was treated as a scanner false positive.

## External edge findings

Cloudflare currently injects its Web Analytics beacon into browser-delivered HTML. The site's CSP blocks that script, so it neither functions nor sends analytics, but the injection causes a console error and conflicts with the disclosed no-client-script posture. The available DNS token and Wrangler OAuth session both receive HTTP 403 from the Web Analytics/RUM configuration API. Resolution requires disabling Web Analytics automatic setup in the Cloudflare dashboard or using a token with Web Analytics/RUM edit permission. The CSP must not be weakened.

The live edge does not currently emit HSTS, an HTTP CSP with `frame-ancestors`, `X-Content-Type-Options`, `Permissions-Policy` or COOP. GitHub Pages cannot configure these headers, and the available Cloudflare token is DNS-scoped. Add them only through a reviewed Cloudflare response-header rule that preserves every existing DNS record and Worker binding.

## Intentional boundaries

- Mail-in requests ask for a return address during intake to retain the approved MRC contact workflow; the field is conditional and the privacy policy discloses it.
- The approved locale and hreflang set remains `en-CA`, `fr-FR`, `es-419`, `vi-VN`, `ar` and `ja-JP`.
- The $50 CAD plus tax service is only a non-invasive used-card completeness and listing-consistency check. It is not a repair diagnostic or a legal determination of fraud.
- Intel graphics cards are normally not accepted.
- Drop-offs are welcome whenever MRC is open; the site does not claim appointments are scheduled.
- Notomo site ID 2 is never reused. The separately created graphics property remains inactive until a replay-free, host-scoped integration can be proven.
