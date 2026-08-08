#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

message="${1:-}"
if [[ -z "$message" ]]; then
  echo 'Usage: ./ship.sh "release message"' >&2
  exit 1
fi

if [[ "$(git branch --show-current)" != "main" ]]; then
  echo "Refusing to ship outside main." >&2
  exit 1
fi

python3 build_graphics_site.py --check
node --check site/assets/site.js
python3 tests/test_graphics_site.py

git add README.md build_graphics_site.py site tests/test_graphics_site.py .github .gitignore ship.sh
if ! git diff --cached --quiet; then
  git commit -m "$message"
fi
git push origin main

echo "Pushed main. GitHub Pages deployment is handled by Actions."
