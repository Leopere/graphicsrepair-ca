# Project infrastructure direction

- Treat references to `leadform` and Woodpecker as legacy context, not as the default architecture.
- Prefer Cloudflare Workers for runtime services, including protected form handling.
- Prefer GitHub Actions on local runners for automation and deployment.
- Use the dedicated Notomo property ID `graphicsrepair.ca`; never reuse motherboardrepair.ca's site ID `2`. Keep full session replay enabled for this property, including literal repair-form values.
- Confirm current production state before following older notes or names.
- Keep `motherboardrepair-ca` read-only when using it as an architectural reference.
