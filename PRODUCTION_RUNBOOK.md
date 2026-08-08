# Production runbook

## Release gates

1. `python3 build_graphics_site.py --check` and `node --check site/assets/site.js` pass.
2. GitHub Pages deploys the `_site` artifact from `main` and the `Leopere/graphicsrepair-ca` Pages URL returns the GPU site.
3. The form proof endpoint returns a valid challenge for both `https://graphicsrepair.ca` and `https://www.graphicsrepair.ca` origins.
4. Only then replace the parked apex and `www` records with proven GitHub Pages targets.
5. Confirm the custom domain, certificate and redirects before optionally enabling the Cloudflare proxy for aggregate edge metrics.

## DNS safety record

Observed before launch on 2026-08-08:

- parked apex: `A 162.255.119.26` (proxied)
- parked `www`: `CNAME parkingpage.namecheap.com` (proxied)
- MX: `eforward1` through `eforward5.registrar-servers.com` with priorities 10, 10, 10, 15 and 20
- TXT: `v=spf1 include:spf.efwd.registrar-servers.com ~all`

The MX and TXT records are out of scope for the web launch and must not be modified.

## Form protection

The browser uses the MRC Cloudflare Worker endpoint with a short-lived proof-of-work challenge. The form also has country-specific phone validation, a honeypot, a minimum completion time, strict length limits and server-side rate limiting. Production requires `graphicsrepair.ca` and `www.graphicsrepair.ca` in the Worker's allowed-origin and proof-origin runtime configuration.

## Infrastructure direction

Treat `leadform` and Woodpecker references as legacy context. New runtime services should use Cloudflare Workers, and automation or deployment should use GitHub Actions on local runners unless current production evidence requires a different path.

## Metrics boundary

The Notomo admin API has a distinct `graphicsrepair.ca` property. Do not reuse the motherboard site ID `2`. No Notomo browser snippet is installed: an API-created property has no public host allowlist until it is added to Notomo's checked-in fleet map, and Notomo replay can record literal form values. Until a separately reviewed, replay-disabled host policy is deployed, production metrics remain Cloudflare's aggregate edge request metrics only, as disclosed in the privacy policy.
