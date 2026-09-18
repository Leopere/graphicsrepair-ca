#!/usr/bin/env python3
"""Refresh the four existing Graphics Repair Pages sites after native shipping."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen

import build_graphics_site as builder
from verify_publication import check_integrity

SITES = (
    ("graphicsrepair-ca", "graphicsrepair.ca", "deploy.yml"),
    ("graphicsrepair-com", "graphicsrepair.com", "pages.yml"),
    ("fixgpu-ca", "fixgpu.ca", "pages.yml"),
    ("gpufix-ca", "gpufix.ca", "pages.yml"),
)
PUBLIC_PATHS = (
    "index.html", "fr/index.html", "es/index.html", "vi/index.html",
    "ar/index.html", "ja/index.html", "privacy/index.html", "terms/index.html",
    "assets/site.js",
)


def api(path: str, *args: str, deadline: float):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError(f"Deployment deadline exceeded before GitHub request: {path}")
    result = subprocess.run(
        ["gh", "api", path, *args], check=True, capture_output=True,
        text=True, timeout=min(20, remaining),
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


def head(repo: str, deadline: float) -> str:
    return api(f"repos/Leopere/{repo}/commits/main", deadline=deadline)["sha"]


def runs(repo: str, workflow: str, deadline: float):
    return api(
        f"repos/Leopere/{repo}/actions/workflows/{workflow}/runs"
        "?event=workflow_dispatch&per_page=10", deadline=deadline,
    )["workflow_runs"]


def new_run(candidates, previous_ids, expected_head):
    return next((run for run in candidates
                 if run["id"] not in previous_ids
                 and run["head_sha"] == expected_head), None)


def check_live(domain: str, expected: dict[str, bytes], revision: str, deadline: float):
    mismatches = []
    for path, content in expected.items():
        if time.monotonic() >= deadline:
            mismatches.append(f"{path}: deployment deadline exceeded")
            break
        url = f"https://{domain}/{path}?revision={revision}"
        try:
            with urlopen(Request(url, headers={"Cache-Control": "no-cache"}), timeout=max(0.1, min(10, deadline - time.monotonic()))) as response:
                if response.read() != content:
                    mismatches.append(path)
        except OSError as error:
            mismatches.append(f"{path}: {error}")
    return mismatches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Build and check existing Pages access without deploying")
    args = parser.parse_args()
    deadline = time.monotonic() + 265
    revision = os.environ.get("DEPLOY_IT_COMMIT", "")
    if not args.check and (not revision or os.environ.get("DEPLOY_IT_BRANCH") != "main"):
        raise RuntimeError("Deploy through native ship-it/deploy-it after pushing main.")

    with tempfile.TemporaryDirectory(prefix="graphicsrepair-pages-", ignore_cleanup_errors=True) as temporary:
        builder.OUTPUT = Path(temporary) / "_site"
        builder.build()
        check_integrity(builder.OUTPUT)
        expected = {path: (builder.OUTPUT / path).read_bytes() for path in PUBLIC_PATHS}
        targets = []
        for repo, domain, workflow in SITES:
            pages = api(f"repos/Leopere/{repo}/pages", deadline=deadline)
            if pages.get("cname") != domain or pages.get("build_type") != "workflow":
                raise RuntimeError(f"Unexpected Pages destination for {repo}: {pages.get('cname')}")
            targets.append({"repo": repo, "domain": domain, "workflow": workflow, "head": head(repo, deadline)})
        if args.check:
            print("Build and Pages access checked for: " + ", ".join(site[1] for site in SITES))
            return
        if targets[0]["head"] != revision:
            raise RuntimeError("Graphics Repair main moved beyond the pushed revision; refusing to deploy a different revision.")

        for target in targets:
            target["previous_ids"] = {run["id"] for run in runs(target["repo"], target["workflow"], deadline)}
            api(f"repos/Leopere/{target['repo']}/actions/workflows/{target['workflow']}/dispatches",
                "--method", "POST", "-f", "ref=main", deadline=deadline)
            print(f"Requested existing Pages workflow for {target['domain']}", flush=True)

        pending = list(targets)
        while pending and time.monotonic() < deadline:
            if head("graphicsrepair-ca", deadline) != revision:
                raise RuntimeError("Graphics Repair main changed during rollout; cannot verify this revision on the aliases.")
            for target in pending[:]:
                run = new_run(runs(target["repo"], target["workflow"], deadline), target["previous_ids"], target["head"])
                if not run or run["status"] != "completed":
                    continue
                if run["conclusion"] != "success":
                    raise RuntimeError(f"Pages workflow {run['html_url']} finished with {run['conclusion']}")
                print(f"Pages workflow succeeded for {target['domain']}: {run['html_url']}", flush=True)
                pending.remove(target)
            if pending:
                time.sleep(max(0, min(5, deadline - time.monotonic())))
        if pending:
            raise TimeoutError("Pages workflows did not finish in time: " + ", ".join(target["domain"] for target in pending))

        outstanding = {target["domain"]: [] for target in targets}
        while outstanding and time.monotonic() < deadline:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                results = {domain: pool.submit(check_live, domain, expected, revision, deadline) for domain in outstanding}
                for domain, future in results.items():
                    mismatches = future.result()
                    if mismatches:
                        outstanding[domain] = mismatches
                    else:
                        del outstanding[domain]
                        print(f"Verified all six forms, terms, privacy and submission JavaScript at https://{domain}/", flush=True)
            if outstanding:
                time.sleep(max(0, min(5, deadline - time.monotonic())))
        if outstanding:
            raise TimeoutError(f"Published files did not match the pushed revision: {outstanding}")


if __name__ == "__main__":
    main()
