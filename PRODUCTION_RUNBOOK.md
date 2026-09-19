# Production runbook

## Release gates

1. `python3 build_graphics_site.py --check` and `node --check site/assets/site.js` pass.
2. GitHub Pages deploys the `_site` artifact from `main` and the `Leopere/graphicsrepair-ca` Pages URL returns the GPU site.
3. The form proof endpoint returns a valid challenge for both `https://graphicsrepair.ca` and `https://www.graphicsrepair.ca` origins.
4. Only then replace the parked apex and `www` records with proven GitHub Pages targets.
5. Confirm the custom domain, certificate and redirects, then keep apex and `www` DNS-only. Do not enable the Cloudflare proxy or WAF for this site.

## DNS and mail safety record

The web launch initially preserved Namecheap forwarding. On 2026-08-08, mail was intentionally migrated to MRC's Mail-in-a-Box at `box.p.nixc.us`:

- apex MX: `10 box.p.nixc.us.`
- apex SPF: `v=spf1 mx -all`
- DKIM selector: `mail._domainkey.graphicsrepair.ca`
- DMARC: `v=DMARC1; p=quarantine;`
- MTA-STS host: `mta-sts.graphicsrepair.ca` at `89.117.56.210`, DNS-only, with an enforced policy for `box.p.nixc.us`
- MTA-STS discovery: `_mta-sts.graphicsrepair.ca TXT "v=STSv1; id=2026080801"`; increment the ID whenever the policy changes
- support alias: `repairs@graphicsrepair.ca` forwards to the established `repairs@motherboardrepair.ca` support alias

Mail-in-a-Box also maintains automatic abuse, admin and postmaster aliases for the domain. Do not restore the old `eforward1` through `eforward5.registrar-servers.com` MX records or the old Namecheap SPF record. Do not import Mail-in-a-Box's suggested apex or `www` web records: those names remain DNS-only GitHub Pages targets.

Inside Mail-in-a-Box, custom DNS records mirror the four GitHub Pages apex A records and `www CNAME leopere.github.io.`. These internal records mark the website as hosted elsewhere, preventing false TLS-health alarms and certificate requests for apex or `www`; Cloudflare remains authoritative. Only `mta-sts.graphicsrepair.ca` is provisioned on the Mail-in-a-Box certificate.

## Form protection

The browser uses the MRC Cloudflare Worker endpoint with a short-lived proof-of-work challenge. The form also has country-specific phone validation, a honeypot, a minimum completion time, strict length limits and server-side rate limiting. Production requires `graphicsrepair.ca` and `www.graphicsrepair.ca` in the Worker's allowed-origin and proof-origin runtime configuration.

## Infrastructure direction

Treat `leadform` and Woodpecker references as legacy context. New runtime services should use Cloudflare Workers, and automation or deployment should use GitHub Actions on local runners unless current production evidence requires a different path.

## Metrics boundary

Notomo uses the dedicated property ID `graphicsrepair.ca`; never reuse the motherboard site ID `2`. The checked-in Notomo fleet map must allow `graphicsrepair.ca`, `www.graphicsrepair.ca`, `fixgpu.ca` and `gpufix.ca` on that property, and `graphicsrepair.com` on its sibling property. Keep `replay_enabled` set to `true`, `replay_sample_rate` set to `1` and literal input recording enabled. Before and after deployment, confirm `https://notomo.colinknapp.com/n-config/graphicsrepair.ca` and `https://notomo.colinknapp.com/n-config/graphicsrepair.com` match that full-capture policy. The browser loader chooses the property from the page host and reports pageviews, technical errors and complete session replay, including literal repair-form values.

Cloudflare is authoritative DNS only. Apex and `www` must have `proxied: false`; this keeps the WAF, edge HTML rewriting and automatic Web Analytics beacon out of the HTTP path. Validate browser-facing HTML contains no `static.cloudflareinsights.com` script. Do not relax the CSP to admit a beacon.

## Edge security controls

The HTML contains a restrictive meta CSP. GitHub Pages does not provide project-defined response headers such as HSTS or `frame-ancestors`; do not put Cloudflare's proxy or WAF in front of the site merely to add them.
