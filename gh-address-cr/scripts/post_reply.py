#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

from python_common import audit_event, run_cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Post a reply to a GitHub PR review thread.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo", default="")
    parser.add_argument("--pr", dest="pr_number", default="")
    parser.add_argument("--audit-id", default="default")
    parser.add_argument("thread_id")
    parser.add_argument("reply_markdown_file")
    args = parser.parse_args()

    reply_file = Path(args.reply_markdown_file)
    if not reply_file.exists():
        print(f"Reply file not found: {reply_file}", file=sys.stderr)
        return 1

    reply_body = reply_file.read_text(encoding="utf-8")

    if args.dry_run:
        print(f"[dry-run] Would reply to thread: {args.thread_id}")
        print("-----")
        print(reply_body.rstrip())
        print("-----")
        if args.repo and args.pr_number:
            audit_event(
                "post_reply",
                "dry-run",
                args.repo,
                args.pr_number,
                args.audit_id,
                "Previewed thread reply",
                {"thread_id": args.thread_id, "reply_file": str(reply_file)},
            )
        return 0

    query = (
        "mutation($threadId:ID!,$body:String!){ "
        "addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$threadId,body:$body}){ comment{ url } } }"
    )
    result = run_cmd(
        ["gh", "api", "graphql", "-f", f"query={query}", "-F", f"threadId={args.thread_id}", "-F", f"body={reply_body}"],
        check=True,
    )
    sys.stdout.write(result.stdout)
    if args.repo and args.pr_number:
        payload = json.loads(result.stdout)
        reply_url = payload.get("data", {}).get("addPullRequestReviewThreadReply", {}).get("comment", {}).get("url", "")
        audit_event(
            "post_reply",
            "ok",
            args.repo,
            args.pr_number,
            args.audit_id,
            "Posted thread reply",
            {"thread_id": args.thread_id, "reply_file": str(reply_file), "reply_url": reply_url},
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
