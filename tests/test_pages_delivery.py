"""Exact-main Jenkins submission contracts; no build, network or activation."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deploy_pages

REVISION = "e211f9ae2e6085df8d97abdd69c5b68cc527f393"


class PagesDeliveryTests(unittest.TestCase):
    def test_requires_exact_main_before_submission(self):
        for branch, revision in (("feature", REVISION), ("", REVISION), ("main", "short"), ("main", "")):
            with self.subTest(branch=branch, revision=revision), patch.dict(os.environ, {"DEPLOY_IT_BRANCH": branch, "DEPLOY_IT_COMMIT": revision}, clear=True), patch.object(sys, "argv", ["deploy_pages.py"]), patch.object(deploy_pages.subprocess, "run") as run:
                with self.assertRaisesRegex(RuntimeError, "exact pushed main"):
                    deploy_pages.main()
                run.assert_not_called()

    def test_submits_exact_revision_to_primary_without_capturing_operation_handle(self):
        with patch.dict(os.environ, {"DEPLOY_IT_BRANCH": "main", "DEPLOY_IT_COMMIT": REVISION}, clear=True), patch.object(sys, "argv", ["deploy_pages.py"]), patch.object(Path, "is_file", return_value=True), patch.object(deploy_pages.subprocess, "run") as run:
            deploy_pages.main()
        run.assert_called_once_with([sys.executable, deploy_pages.DEFAULT_SUBMIT, REVISION], check=True)

    def test_override_and_failure_never_retry_or_fall_back_to_actions(self):
        environment = {"DEPLOY_IT_BRANCH": "main", "DEPLOY_IT_COMMIT": REVISION, "JENKINS_GRAPHICSREPAIR_SUBMIT": "/trusted/submit-graphicsrepair-pages.py"}
        with patch.dict(os.environ, environment, clear=True), patch.object(sys, "argv", ["deploy_pages.py"]), patch.object(Path, "is_file", return_value=True), patch.object(deploy_pages.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "submit")) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                deploy_pages.main()
            run.assert_called_once_with([sys.executable, environment["JENKINS_GRAPHICSREPAIR_SUBMIT"], REVISION], check=True)


if __name__ == "__main__":
    unittest.main()
