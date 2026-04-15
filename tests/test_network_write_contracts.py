import importlib.util
import io
import json
import subprocess
import sys
from contextlib import contextmanager
from unittest.mock import patch

from tests.helpers import PythonScriptTestCase, SCRIPTS_DIR


@contextmanager
def patched_argv(argv: list[str]):
    with patch.object(sys, "argv", argv):
        yield


class NetworkWriteContractTest(PythonScriptTestCase):
    def load_module(self, script_name: str, module_name: str):
        path = SCRIPTS_DIR / script_name
        sys.path.insert(0, str(path.parent))
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        return module

    def test_resolve_thread_reports_unknown_when_session_update_fails_after_remote_success(self):
        module = self.load_module("resolve_thread.py", "resolve_thread_under_test")

        module.gh_write_cmd = lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            0,
            json.dumps(
                {
                    "data": {
                        "resolveReviewThread": {
                            "thread": {
                                "id": "THREAD_RESOLVE",
                                "isResolved": True,
                            }
                        }
                    }
                }
            ),
            "",
        )
        module.session_engine = lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", "")
        module.append_handled = lambda *args, **kwargs: None
        module.audit_event = lambda *args, **kwargs: None

        def failing_run_cmd(*args, **kwargs):
            raise subprocess.CalledProcessError(7, args[0], "", "session update failed")

        module.run_cmd = failing_run_cmd

        with patched_argv(
            [
                "resolve_thread.py",
                "--repo",
                self.repo,
                "--pr",
                self.pr,
                "THREAD_RESOLVE",
            ]
        ), patch("sys.stdout", new=io.StringIO()) as stdout, patch("sys.stderr", new=io.StringIO()) as stderr:
            rc = module.main()
            payload = json.loads(stdout.getvalue())

        self.assertNotEqual(rc, 0)
        self.assertEqual(payload["status"], "unknown")
        self.assertEqual(payload["remote_status"], "succeeded")
        self.assertEqual(payload["session_status"], "failed")
        self.assertTrue(payload["resolved"])
        self.assertIn("session update failed", payload["error"])
        self.assertIn("session update failed", stderr.getvalue())

    def test_publish_finding_reports_unknown_when_mark_published_fails_after_comment_creation(self):
        module = self.load_module("publish_finding.py", "publish_finding_under_test")

        module.load_item = lambda *args, **kwargs: {
            "item_id": "local-finding:abc",
            "item_kind": "local_finding",
            "title": "Publish me",
            "body": "Body",
            "path": "src/a.py",
            "line": 4,
        }
        module.gh_read_cmd = lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "deadbeef\n", "")
        module.load_pr_files = lambda *args, **kwargs: [{"filename": "src/a.py", "patch": "@@ -1,1 +1,4 @@\n line1\n+line2\n+line3\n+line4"}]
        module.audit_event = lambda *args, **kwargs: None
        module.gh_write_cmd = lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            0,
            json.dumps({"id": 123, "html_url": "https://example.test/comment/123"}),
            "",
        )

        def failing_run_cmd(*args, **kwargs):
            raise subprocess.CalledProcessError(9, args[0], "", "mark-published failed")

        module.run_cmd = failing_run_cmd

        with patched_argv(
            [
                "publish_finding.py",
                "--repo",
                self.repo,
                "--pr",
                self.pr,
                "local-finding:abc",
            ]
        ), patch("sys.stdout", new=io.StringIO()) as stdout, patch("sys.stderr", new=io.StringIO()) as stderr:
            rc = module.main()
            payload = json.loads(stdout.getvalue())

        self.assertNotEqual(rc, 0)
        self.assertEqual(payload["status"], "unknown")
        self.assertEqual(payload["remote_status"], "succeeded")
        self.assertEqual(payload["session_status"], "failed")
        self.assertEqual(payload["comment_id"], 123)
        self.assertEqual(payload["comment_url"], "https://example.test/comment/123")
        self.assertIn("mark-published failed", payload["error"])
        self.assertIn("mark-published failed", stderr.getvalue())
