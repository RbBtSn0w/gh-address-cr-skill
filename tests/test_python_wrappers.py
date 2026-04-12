import json
import sys
from pathlib import Path

from tests.helpers import (
    CLI_PY,
    FINAL_GATE_PY,
    LIST_THREADS_PY,
    POST_REPLY_PY,
    PUBLISH_FINDING_PY,
    RESOLVE_THREAD_PY,
    RUN_LOCAL_REVIEW_PY,
    RUN_ONCE_PY,
    SCRIPT,
    PythonScriptTestCase,
)


class PythonWrapperCLITest(PythonScriptTestCase):
    def test_cli_help_lists_unified_commands(self):
        result = self.run_cmd([sys.executable, str(CLI_PY), "--help"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("run-once", result.stdout)
        self.assertIn("session-engine", result.stdout)

    def test_cli_dispatches_run_once(self):
        gh = self.bin_dir / "gh"
        gh.write_text(
            """#!/usr/bin/env python3
import json
import sys

if sys.argv[1:3] == ['api', 'graphql']:
    print(json.dumps({
        'data': {
            'repository': {
                'pullRequest': {
                    'reviewThreads': {
                        'pageInfo': {'hasNextPage': False, 'endCursor': None},
                        'nodes': [{
                            'id': 'THREAD_CLI',
                            'isResolved': False,
                            'isOutdated': False,
                            'path': 'src/cli.py',
                            'line': 6,
                            'firstComment': {'nodes': [{'url': 'https://example.test/thread/cli', 'body': 'cli'}]},
                            'latestComment': {'nodes': [{'url': 'https://example.test/thread/cli', 'body': 'cli'}]},
                        }]
                    }
                }
            }
        }
    }))
else:
    raise SystemExit(f'unhandled gh args: {sys.argv[1:]}')
""",
            encoding="utf-8",
        )
        gh.chmod(0o755)

        result = self.run_cmd([sys.executable, str(CLI_PY), "run-once", self.repo, self.pr])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("github-thread:THREAD_CLI", result.stdout)

    def test_run_local_review_python_ingests_findings(self):
        adapter = Path(self.temp_dir.name) / "adapter.py"
        adapter.write_text(
            "import json\nprint(json.dumps([{'title':'py-adapter','body':'body','path':'src/a.py','line':4}]))\n",
            encoding="utf-8",
        )

        self.run_cmd([sys.executable, str(SCRIPT), "init", self.repo, self.pr], check=True)
        result = self.run_cmd(
            [
                sys.executable,
                str(RUN_LOCAL_REVIEW_PY),
                "--source",
                "local-agent:test",
                self.repo,
                self.pr,
                sys.executable,
                str(adapter),
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Created 1 local item", result.stdout)

    def test_publish_finding_python_dry_run_uses_diff_position(self):
        gh = self.bin_dir / "gh"
        gh.write_text(
            """#!/usr/bin/env python3
import json
import sys

args = sys.argv[1:]
if args[:3] == ['pr', 'view', '77']:
    print('deadbeefdeadbeefdeadbeefdeadbeefdeadbeef')
elif args[:2] == ['api', 'repos/octo/example/pulls/77/files']:
    print(json.dumps([{'filename':'src/a.py','patch':'@@ -1,1 +1,4 @@\\n line1\\n+line2\\n+line3\\n+line4'}]))
else:
    raise SystemExit(f'unhandled gh args: {args}')
""",
            encoding="utf-8",
        )
        gh.chmod(0o755)

        self.run_cmd([sys.executable, str(SCRIPT), "init", self.repo, self.pr], check=True)
        payload = json.dumps(
            [
                {
                    "title": "Publish me",
                    "body": "Dry-run publication.",
                    "path": "src/a.py",
                    "line": 4,
                    "severity": "P3",
                    "category": "docs",
                }
            ]
        )
        ingest = self.run_cmd(
            [sys.executable, str(SCRIPT), "ingest-local", self.repo, self.pr, "--source", "local-agent:test"],
            stdin=payload,
            check=True,
        )
        self.assertIn("Created 1 local item", ingest.stdout)

        list_result = self.run_cmd([sys.executable, str(SCRIPT), "list-items", self.repo, self.pr, "--item-kind", "local_finding"], check=True)
        item_id = json.loads(list_result.stdout.strip())["item_id"]
        result = self.run_cmd(
            [
                sys.executable,
                str(PUBLISH_FINDING_PY),
                "--dry-run",
                "--repo",
                self.repo,
                "--pr",
                self.pr,
                item_id,
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("position=4", result.stdout)

    def test_run_once_python_syncs_session_with_mocked_gh(self):
        gh = self.bin_dir / "gh"
        gh.write_text(
            """#!/usr/bin/env python3
import json
import sys

if sys.argv[1:3] == ['api', 'graphql']:
    print(json.dumps({
        'data': {
            'repository': {
                'pullRequest': {
                    'reviewThreads': {
                        'pageInfo': {'hasNextPage': False, 'endCursor': None},
                        'nodes': [{
                            'id': 'THREAD_A',
                            'isResolved': False,
                            'isOutdated': False,
                            'path': 'src/a.py',
                            'line': 4,
                            'firstComment': {'nodes': [{'url': 'https://example.test/thread/A', 'body': 'Please fix'}]},
                            'latestComment': {'nodes': [{'url': 'https://example.test/thread/A', 'body': 'Please fix'}]},
                        }]
                    }
                }
            }
        }
    }))
else:
    raise SystemExit(f'unhandled gh args: {sys.argv[1:]}')
""",
            encoding="utf-8",
        )
        gh.chmod(0o755)

        result = self.run_cmd([sys.executable, str(RUN_ONCE_PY), "--audit-id", "test", self.repo, self.pr])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("== PR Review Threads ==", result.stdout)
        self.assertIn("github-thread:THREAD_A", result.stdout)

    def test_final_gate_python_passes_on_resolved_threads(self):
        gh = self.bin_dir / "gh"
        gh.write_text(
            """#!/usr/bin/env python3
import json
import sys

if sys.argv[1:3] == ['api', 'graphql']:
    print(json.dumps({
        'data': {
            'repository': {
                'pullRequest': {
                    'reviewThreads': {
                        'pageInfo': {'hasNextPage': False, 'endCursor': None},
                        'nodes': [{
                            'id': 'THREAD_DONE',
                            'isResolved': True,
                            'isOutdated': False,
                            'path': 'src/a.py',
                            'line': 4,
                            'firstComment': {'nodes': [{'url': 'https://example.test/thread/done', 'body': 'Done'}]},
                            'latestComment': {'nodes': [{'url': 'https://example.test/thread/done', 'body': 'Done'}]},
                        }]
                    }
                }
            }
        }
    }))
else:
    raise SystemExit(f'unhandled gh args: {sys.argv[1:]}')
""",
            encoding="utf-8",
        )
        gh.chmod(0o755)

        result = self.run_cmd([sys.executable, str(FINAL_GATE_PY), "--no-auto-clean", "--audit-id", "gate-test", self.repo, self.pr])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified: 0 Unresolved Threads found", result.stdout)

    def test_list_threads_python_outputs_normalized_rows(self):
        gh = self.bin_dir / "gh"
        gh.write_text(
            """#!/usr/bin/env python3
import json
import sys

if sys.argv[1:3] == ['api', 'graphql']:
    print(json.dumps({
        'data': {
            'repository': {
                'pullRequest': {
                    'reviewThreads': {
                        'pageInfo': {'hasNextPage': False, 'endCursor': None},
                        'nodes': [{
                            'id': 'THREAD_LIST',
                            'isResolved': False,
                            'isOutdated': True,
                            'path': 'src/list.py',
                            'line': 2,
                            'firstComment': {'nodes': [{'url': 'https://example.test/thread/list-first', 'body': 'first'}]},
                            'latestComment': {'nodes': [{'url': 'https://example.test/thread/list-latest', 'body': 'latest'}]},
                        }]
                    }
                }
            }
        }
    }))
else:
    raise SystemExit(f'unhandled gh args: {sys.argv[1:]}')
""",
            encoding="utf-8",
        )
        gh.chmod(0o755)

        result = self.run_cmd([sys.executable, str(LIST_THREADS_PY), self.repo, self.pr])
        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads(result.stdout.strip())
        self.assertEqual(row["id"], "THREAD_LIST")
        self.assertEqual(row["url"], "https://example.test/thread/list-latest")
        self.assertEqual(row["comment_source"], "latest")

    def test_post_reply_python_dry_run_prints_body(self):
        reply_file = Path(self.temp_dir.name) / "reply.md"
        reply_file.write_text("Reply body", encoding="utf-8")

        result = self.run_cmd(
            [
                sys.executable,
                str(POST_REPLY_PY),
                "--dry-run",
                "--repo",
                self.repo,
                "--pr",
                self.pr,
                "THREAD_REPLY",
                str(reply_file),
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[dry-run] Would reply to thread: THREAD_REPLY", result.stdout)
        self.assertIn("Reply body", result.stdout)

    def test_resolve_thread_python_updates_session(self):
        gh = self.bin_dir / "gh"
        gh.write_text(
            """#!/usr/bin/env python3
import json
import sys

if sys.argv[1:3] == ['api', 'graphql']:
    print(json.dumps({
        'data': {
            'resolveReviewThread': {
                'thread': {
                    'id': 'THREAD_RESOLVE',
                    'isResolved': True,
                }
            }
        }
    }))
else:
    raise SystemExit(f'unhandled gh args: {sys.argv[1:]}')
""",
            encoding="utf-8",
        )
        gh.chmod(0o755)

        payload = json.dumps(
            [
                {
                    "id": "THREAD_RESOLVE",
                    "isResolved": False,
                    "isOutdated": False,
                    "path": "src/resolve.py",
                    "line": 9,
                    "body": "Resolve me.",
                    "url": "https://example.test/thread/resolve",
                }
            ]
        )
        self.run_cmd([sys.executable, str(SCRIPT), "init", self.repo, self.pr], check=True)
        self.run_cmd(
            [sys.executable, str(SCRIPT), "sync-github", self.repo, self.pr],
            stdin=payload,
            check=True,
        )

        result = self.run_cmd(
            [
                sys.executable,
                str(RESOLVE_THREAD_PY),
                "--repo",
                self.repo,
                "--pr",
                self.pr,
                "THREAD_RESOLVE",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        session = json.loads((self.state_dir / "octo__example__pr77__session.json").read_text(encoding="utf-8"))
        item = session["items"]["github-thread:THREAD_RESOLVE"]
        self.assertEqual(item["status"], "CLOSED")
        self.assertTrue(item["handled"])
