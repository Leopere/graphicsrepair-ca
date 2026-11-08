# Prepared Motherboard contact integration

Prepared against **Leopere/staging-motherboardrepair-ca**, branch/default `staging`, exact base `7d5de862274ce72e3bf237aabea2a56902933342`. No Motherboard commit or push was made. The separate preparation checkout is `/home/runner/motherboard-patch-work`. Canonical `Leopere/motherboardrepair-ca` default `production` was compared using `git ls-remote` only; its head matched this base. It is not the edit/delivery repository.

`READY.json` lists the patch digest, every changed path and all four artifact hashes. `contact-embed.patch` contains only text changes: loader, manifest and all 62 loader-reference files under `docs/` and `locales/templates/`, including source/localized modal loaders. The unchanged runtime JS and WASM are supplied through the exact four Graphics assets. No source assets, property IDs, replay settings, localized copy or publication-manager files are changed.

## Exact application process (primary only)

Use a fresh review checkout of the declared staging repository. Resolve `GRAPHICS_COMMIT` to the commit containing this handoff (`git log -1 --format=%H -- docs/contact-embed-integration-ready.json` in Graphics); record and verify that full SHA. Do not use an unverified moving branch for assets.

```bash
git clone --branch staging https://github.com/Leopere/staging-motherboardrepair-ca.git motherboard-contact-review
cd motherboard-contact-review
test "$(git rev-parse HEAD)" = 7d5de862274ce72e3bf237aabea2a56902933342
test -z "$(git status --porcelain)"
# GRAPHICS_CHECKOUT must be the verified exact integration commit.
sha256sum "$GRAPHICS_CHECKOUT/docs/motherboard-contact-patch/contact-embed.patch"
# Compare with READY.json patch_sha256 before applying.
git apply --check "$GRAPHICS_CHECKOUT/docs/motherboard-contact-patch/contact-embed.patch"
git apply "$GRAPHICS_CHECKOUT/docs/motherboard-contact-patch/contact-embed.patch"
for asset in contact-form.wasm loader.js manifest.json wasm_exec.js; do
  cp "$GRAPHICS_CHECKOUT/site/contact-embed/$asset" "docs/contact-embed/$asset"
done
python3 - <<'PY'
import hashlib, json
from pathlib import Path
embed = Path('docs/contact-embed')
expected = {
 'contact-form.wasm': '90090136e89e41e4e72d31db55944ea2f86b93b41c19a8a102ce113dc8398492',
 'loader.js': '0a58738b67e4ce6ec64bbd89563d427b31225d167f5b79fbf4e3cce47f5329f0',
 'manifest.json': 'fd1b6e64a32fa2e678a9d827648fd607a7ac53e942dfcf463282f47f9c56dc22',
 'wasm_exec.js': '0c949f4996f9a89698e4b5c586de32249c3b69b7baadb64d220073cc04acba14',
}
for name, digest in expected.items():
 assert hashlib.sha256((embed / name).read_bytes()).hexdigest() == digest, name
PY
python3 -m pytest -q tests/test_contact_wasm_embed.py
git diff --check
git diff --stat
```

If staging has moved, stop exact-base application and review/adapt against the new head; do not force, rebase or assume production routing. Review the concrete diff, run affected staging checks, and use the Notomo registry's declared **staging remote and promotion flow**. Legacy DEVELOPMENT.md routing examples and the canonical production default do not override that declaration. Primary owns any later commit, push, Jenkins delivery, acceptance and Notomo closure. The runner did none of these for Motherboard. Existing `scripts/deploy-jenkins.sh` is a primary-owned delivery entry point, not an instruction to invoke it here.

## Rebuilding the exact reviewed artifacts

Reviewed source is `Leopere/motherboardrepair-contact` at `acfbb65c1b5a18790ad85d4356e863ae23cd754e`; tested implementation is `8a2ae6a40a16f662d2369eadda136b57ff450631`. Build with Go **1.26.7**. The reviewed WASM contains Go VCS stamping from base `dc432755caa6d6ed95644344fed6a6add45fc67b` with the tested implementation pending (`vcs.modified=true`). A clean build at the later commits changes that embedded stamp and therefore the hash. The content revision remains `sha256:2d1d83e083943a7540335e22282e7606a0b7121540c41a9b886317d690ecb0d9`; it is not a Git SHA.

Keep the exact reviewed clone read-only. In a disposable **normal clone**, reconstruct only the tested changes, verify their identity, then run the source contract:

```bash
git clone https://github.com/Leopere/motherboardrepair-contact.git contact-build
cd contact-build
git checkout --detach dc432755caa6d6ed95644344fed6a6add45fc67b
git diff dc432755caa6d6ed95644344fed6a6add45fc67b 8a2ae6a40a16f662d2369eadda136b57ff450631 -- cmd web tests | git apply
git diff 8a2ae6a40a16f662d2369eadda136b57ff450631 -- cmd web tests go.mod scripts
# Above must be empty. Build/sync scripts are unchanged between these commits.
make verify
./scripts/sync.sh /tmp/contact-exact-embed
sha256sum /tmp/contact-exact-embed/*
```

All four hashes must match READY.json. No runtime changes were invented to make the hashes match. The retained Graphics assets are the durable binary handoff.

Historical source evidence: 35 offline browser cases (15 native, 18 Graphics UI, 2 exported API) and `make verify` passed at the tested implementation. This integration reuses that native matrix because Motherboard base and relay inputs match, and reruns the Graphics subset against its actual committed embeds and new Notomo wrapper. The original historical relay failure cause is **UNPROVEN**. This patch improves diagnostics; it is not a root-cause or live-delivery claim.
