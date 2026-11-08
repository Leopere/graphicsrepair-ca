#!/usr/bin/env python3
"""Submit the exact pushed main revision to the primary's trusted Jenkins client."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

DEFAULT_SUBMIT = str(Path.home() / ".local/share/jenkins-local/graphicsrepair-client/submit-graphicsrepair-pages.py")


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    revision = os.environ.get("DEPLOY_IT_COMMIT", "")
    if os.environ.get("DEPLOY_IT_BRANCH") != "main" or not re.fullmatch("[a-f0-9]{40}", revision):
        raise RuntimeError("Jenkins submission requires the exact pushed main revision")
    submit = Path(os.environ.get("JENKINS_GRAPHICSREPAIR_SUBMIT", DEFAULT_SUBMIT)).expanduser()
    if not submit.is_absolute() or not submit.is_file():
        raise RuntimeError("Trusted Jenkins submitter must be an existing absolute path")
    # Inherit stdout/stderr so operation handles survive failed or uncertain observations.
    # The trusted client owns timing, deduplication, stale-main checks and acceptance.
    subprocess.run([sys.executable, str(submit), revision], check=True)


if __name__ == "__main__":
    main()
