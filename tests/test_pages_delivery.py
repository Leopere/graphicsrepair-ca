"""Checks for alias refresh and live acceptance without network or deployment."""

import io
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deploy_pages


class PagesDeliveryTests(unittest.TestCase):
    def test_only_new_runs_for_the_expected_revision_are_selected(self):
        old = {"id": 1, "head_sha": "expected"}
        wrong = {"id": 2, "head_sha": "another"}
        current = {"id": 3, "head_sha": "expected"}
        self.assertEqual(deploy_pages.new_run([old, wrong, current], {1}, "expected"), current)
        self.assertIsNone(deploy_pages.new_run([old, wrong], {1}, "expected"))

    def test_alias_acceptance_checks_the_alias_host_and_exact_content(self):
        with patch.object(deploy_pages, "urlopen", return_value=io.BytesIO(b"new form")) as fetch:
            self.assertEqual(deploy_pages.check_live("fixgpu.ca", {"fr/index.html": b"new form"}, "revision", time.monotonic() + 10), [])
        self.assertEqual(fetch.call_args.args[0].full_url, "https://fixgpu.ca/fr/index.html?revision=revision")

    def test_stale_published_form_is_not_a_successful_deployment(self):
        with patch.object(deploy_pages, "urlopen", return_value=io.BytesIO(b"old form")):
            self.assertEqual(deploy_pages.check_live("gpufix.ca", {"index.html": b"new form"}, "revision", time.monotonic() + 10), ["index.html"])

    def test_an_unreachable_site_is_reported(self):
        with patch.object(deploy_pages, "urlopen", side_effect=OSError("unreachable")):
            self.assertEqual(deploy_pages.check_live("graphicsrepair.com", {"index.html": b"form"}, "revision", time.monotonic() + 10), ["index.html: unreachable"])

    def test_expired_deadline_does_not_start_another_request(self):
        with patch.object(deploy_pages, "urlopen") as fetch:
            self.assertTrue(deploy_pages.check_live("fixgpu.ca", {"index.html": b"form"}, "revision", time.monotonic() - 1))
            fetch.assert_not_called()

    def test_deployment_requires_the_native_pushed_revision(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(sys, "argv", ["deploy_pages.py"]), patch.object(deploy_pages, "api") as api:
            with self.assertRaisesRegex(RuntimeError, "native ship-it/deploy-it"):
                deploy_pages.main()
            api.assert_not_called()

    def test_expired_deadline_does_not_start_a_github_request(self):
        with patch.object(deploy_pages.subprocess, "run") as run:
            with self.assertRaisesRegex(TimeoutError, "before GitHub request"):
                deploy_pages.api("repos/Leopere/graphicsrepair-ca/pages", deadline=time.monotonic() - 1)
            run.assert_not_called()

    def test_github_request_timeout_fits_the_remaining_deadline(self):
        with patch.object(deploy_pages.time, "monotonic", return_value=100), patch.object(deploy_pages.subprocess, "run") as run:
            run.return_value.stdout = '{"sha": "expected"}'
            self.assertEqual(deploy_pages.head("graphicsrepair-ca", 103), "expected")
            self.assertEqual(run.call_args.kwargs["timeout"], 3)


if __name__ == "__main__":
    unittest.main()
