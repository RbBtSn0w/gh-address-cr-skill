import importlib.util
import io
import json
import subprocess
import sys
from contextlib import contextmanager
from unittest.mock import patch

from tests.helpers import PythonScriptTestCase, CR_LOOP_PY


BATCH_GITHUB_EXECUTE_PY = CR_LOOP_PY.parent / "batch_github_execute.py"


@contextmanager
def patched_argv(argv: list[str]):
    with patch.object(sys, "argv", argv):
        yield


@contextmanager
def patched_stdin(text: str):
    with patch.object(sys, "stdin", io.StringIO(text)):
        yield


class BatchGitHubExecuteTestCase(PythonScriptTestCase):
    def load_module(self):
        sys.path.insert(0, str(BATCH_GITHUB_EXECUTE_PY.parent))
        spec = importlib.util.spec_from_file_location("batch_github_execute_under_test", BATCH_GITHUB_EXECUTE_PY)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        return module

    def test_batch_github_execute_submits_only_new_pending_reviews(self):
        module = self.load_module()
        action_payload = json.dumps(
            [
                {
                    "item_id": "github-thread:THREAD_1",
                    "thread_id": "THREAD_1",
                    "reply_body": "Reply body",
                    "resolve": True,
                }
            ]
        )
        pending_sets = [{11}, {11, 22}]
        submitted = []

        def fake_list_pending_review_ids(repo, pr_number, login):
            return pending_sets.pop(0)

        def fake_submit_pending_reviews(repo, pr_number, review_ids):
            submitted.extend(review_ids)
            return list(review_ids)

        def fake_run_cmd(cmd, *, check=False):
            self.assertIn("gh", cmd[0])
            self.assertIn("graphql", cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                json.dumps(
                    {
                        "data": {
                            "reply0": {"comment": {"url": "https://example.test/reply"}},
                            "resolve0": {"thread": {"id": "THREAD_1", "isResolved": True}},
                        }
                    }
                ),
                "",
            )

        module.list_pending_review_ids = fake_list_pending_review_ids
        module.submit_pending_reviews = fake_submit_pending_reviews
        module.current_login = lambda: "tester"
        module.run_cmd = fake_run_cmd
        module.audit_event = lambda *args, **kwargs: None

        with patched_argv(
            [
                "batch_github_execute.py",
                "--repo",
                self.repo,
                "--pr",
                self.pr,
            ]
        ), patched_stdin(action_payload):
            rc = module.main()

        self.assertEqual(rc, 0)
        self.assertEqual(submitted, [22])

    def test_batch_github_execute_returns_nonzero_when_graphql_fails(self):
        module = self.load_module()
        action_payload = json.dumps(
            [
                {
                    "item_id": "github-thread:THREAD_2",
                    "thread_id": "THREAD_2",
                    "reply_body": "Reply body",
                    "resolve": True,
                }
            ]
        )
        submitted = []

        def fake_list_pending_review_ids(repo, pr_number, login):
            return set()

        def fake_submit_pending_reviews(repo, pr_number, review_ids):
            submitted.extend(review_ids)
            return list(review_ids)

        def fake_run_cmd(cmd, *, check=False):
            return subprocess.CompletedProcess(cmd, 1, "", "graphql failed")

        module.list_pending_review_ids = fake_list_pending_review_ids
        module.submit_pending_reviews = fake_submit_pending_reviews
        module.current_login = lambda: "tester"
        module.run_cmd = fake_run_cmd
        module.audit_event = lambda *args, **kwargs: None

        with patched_argv(
            [
                "batch_github_execute.py",
                "--repo",
                self.repo,
                "--pr",
                self.pr,
            ]
        ), patched_stdin(action_payload):
            rc = module.main()

        self.assertNotEqual(rc, 0)
        self.assertEqual(submitted, [])
