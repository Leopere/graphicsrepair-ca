**Fixes merged and pushed; production deployment is blocked.**

The client compared the Worker's 2.5-second readiness timestamp with the visitor's clock. A fast clock skipped the wait on both the original attempt and its retry. On the base build, the French regression sent both attempts within 0.35 seconds of challenge issuance and failed. The fix uses elapsed timers for readiness and cache expiry, retains the single fresh-challenge retry, and preserves input on terminal failure. All six locales and the JavaScript fallback pass.

Separately, the live Worker denies `fixgpu.ca` and `gpufix.ca`: both were missing from its origin lists. Those aliases and their www hosts are now configured. Live main/www challenges have a one-hour TTL; signed proofs work after waiting. There is no demonstrated locale-path, signing-key or build-version mismatch. The historical Notomo events lack enough detail to attribute each rejection conclusively.

All repositories used `fix/grc-contact-verification`, followed by normal pushes and main merges. Implementation revisions (this report follows the site merge):

| Repository | Fix commit | Merged main |
| --- | --- | --- |
| graphicsrepair-ca | `91d3ce112ea8` | `75d5b0cf9707` |
| motherboardrepair-contact | `ec39d74b34d0` | `fea83395d83a` |
| hearth-home-contact-relay | `435892b3ffd2` | `7fbecd4a0c1b` |

Files changed:

- Graphics: three `site/contact-embed/` artifacts; all six `site/**/js/contact-form.min.js` fallbacks; `tests/test_wasm_browser.py`; `README.md`; `.gitignore`; this report.
- Contact runtime: `cmd/contact/{main.go,form.go,form_test.go}`, `web/loader.js`, `scripts/{build.sh,sync.sh}`, `tests/contact-browser.cjs`, `docs/contact-failure-runbook.md`.
- Worker: `worker/{abuse-protection.js,public-intake.js}`, `wrangler.leads.toml`, `.github/workflows/deploy.yml`, `test/grc-verification.test.js`, `README.md`. Adds relative readiness and `/api/form-proof/validate`, which validates without delivering mail.

Verification passed:

- Graphics: build/static checks, JavaScript syntax, 9 Node tests, 6 deployment tests, 20 diagnostic browser cases, and the complete WASM/browser suite: 15 submission cases, favicon and desktop/mobile CSP. New cases cover all locales, fast clocks, refresh/retry, fallback and French input retention.
- Contact: `make verify`, `make sync`, explicit Graphics artifact sync, and all 51 browser cases against the real Worker verifier.
- Worker: `npm ci`, all 91 tests, `npm run check` and `npm run check:leads`, including both Wrangler dry-run builds. New tests cover expiry recovery, aliases, French referrers, signature/origin/payload mismatches and validation without queueing.
- Pre-existing failure confirmed on base `fb44f6a`: repeating the Go build failed copying read-only `wasm_exec.js`. Fixed with replacement-safe copies; repeat builds now pass. No remaining local suite failures. Source-repo GitHub Verify is queued.

Live state remains unchanged:

- https://forms.motherboardrepair.ca/version : release `standalone-lead-intake-v1`, version_id `8f6593ca-93a1-4ab2-9e6b-2c32b5d32947`. A new version-to-commit mapping cannot be recorded because deployment has not run.
- https://graphicsrepair.ca/contact-embed/manifest.json : loader SHA `2f727ac6a13205e06ab481ab6098508c83ba450d0b4f665775e25ee7deeedb5c`; `/` and `/fr/` still use `v=2f727ac6a132`. Expected new loader is `v=30ee873d4bed`, with WASM SHA `5e3a1eb43a091edbba7649d6caf28f2749876a8e71de51735de38a62a7a28322`.
- Two deliberately incomplete live TEST POSTs, one with each locale referrer: `/fr/` returned 403 `FORM_PROOF_INVALID` before readiness; `/` waited and passed proof verification, then returned 400 for the omitted mandatory phone. Both used name `TEST Grok DO Coder`, email `test@example.invalid`, and a message starting `TEST - please ignore`. Neither queued a lead. No further live submissions were made.

Deployment blockers:

- Worker run https://github.com/Leopere/hearth-home-contact-relay/actions/runs/42824511160 remains queued for `self-hosted, Linux, ARM64, leopere, local`; GitHub lists zero repository runners. `gh run watch` observed the queue; the run remains available to deploy when a matching runner becomes available.
- Site publication requires the missing trusted client `~/.local/share/jenkins-local/graphicsrepair-client/submit-graphicsrepair-normal.py` (protocol `graphicsrepair-normal/v1`). Exact-main submission failed because that file is absent. `deploy_pages.py --check` is no longer supported; README now reflects the current helper. Existing Pages publication remains on branch `pages`, whose last successful run is 42507337564.

New live artifacts and successful live end-to-end delivery remain unverified pending those deployment facilities. DNS and motherboardrepair-ca were untouched. Motherboard's vendored runtime needs a separate staging/Jenkins rollout to receive the shared client fix.
