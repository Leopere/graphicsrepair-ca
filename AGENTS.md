# Project infrastructure direction

- Treat references to `leadform` and Woodpecker as legacy context, not as the default architecture.
- Prefer Cloudflare Workers for runtime services, including protected form handling.
- Prefer GitHub Actions on local runners for automation and deployment.
- Never reuse motherboardrepair.ca's Notomo site ID `2`; the distinct reserved property is `graphicsrepair.ca`, with no client snippet enabled.
- Confirm current production state before following older notes or names.
- Keep `motherboardrepair-ca` read-only when using it as an architectural reference.
