#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys

from post_reply import list_pending_review_ids, submit_pending_reviews, current_login
from python_common import run_cmd, audit_event

def chunk_actions(actions: list[dict], max_size: int) -> list[list[dict]]:
    return [actions[i:i + max_size] for i in range(0, len(actions), max_size)]

def main() -> int:
    parser = argparse.ArgumentParser(description="Batch execute GitHub review thread actions.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", dest="pr_number", required=True)
    parser.add_argument("--audit-id", default="default")
    args = parser.parse_args()

    raw_input = sys.stdin.read().strip()
    if not raw_input:
        print("{}", file=sys.stdout)
        return 0

    try:
        actions = json.loads(raw_input)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON input: {exc}", file=sys.stderr)
        return 1

    if not actions:
        print("{}", file=sys.stdout)
        return 0

    login = current_login()
    pending_before = list_pending_review_ids(args.repo, args.pr_number, login)

    results = {}
    had_error = False
    
    # GraphQL limits node size, chunking to safe size (e.g. 20 operations per request)
    for chunk in chunk_actions(actions, 20):
        query_parts = []
        variables = {}
        flags = []
        
        for i, action in enumerate(chunk):
            thread_id = action.get("thread_id")
            if not thread_id:
                continue
            if action.get("reply_body"):
                query_parts.append(f"reply{i}: addPullRequestReviewThreadReply(input:{{pullRequestReviewThreadId: $reply{i}_threadId, body: $reply{i}_body}}) {{ comment {{ url }} }}")
                variables[f"reply{i}_threadId"] = "ID!"
                variables[f"reply{i}_body"] = "String!"
                flags.extend(["-F", f"reply{i}_threadId={thread_id}", "-F", f"reply{i}_body={action['reply_body']}"])
            
            if action.get("resolve"):
                query_parts.append(f"resolve{i}: resolveReviewThread(input:{{threadId: $resolve{i}_threadId}}) {{ thread {{ id isResolved }} }}")
                variables[f"resolve{i}_threadId"] = "ID!"
                flags.extend(["-F", f"resolve{i}_threadId={thread_id}"])

        if not query_parts:
            continue

        var_str = ", ".join(f"${k}: {v}" for k, v in variables.items())
        query = f"mutation({var_str}) {{ {' '.join(query_parts)} }}"
        
        cmd = ["gh", "api", "graphql", "-f", f"query={query}"] + flags
        result = run_cmd(cmd, check=False)
        
        payload = {}
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            if result.returncode != 0:
                had_error = True
                print(f"GraphQL request failed: {result.stderr}", file=sys.stderr)
                for action in chunk:
                    results[action["item_id"]] = {"error": result.stderr or "GraphQL request failed"}
                continue
        errors = payload.get("errors")
        data = payload.get("data") or {}
        if errors or result.returncode != 0:
            had_error = True
        
        for i, action in enumerate(chunk):
            item_id = action["item_id"]
            res = {}
            if action.get("reply_body"):
                res["reply_url"] = data.get(f"reply{i}", {}).get("comment", {}).get("url") if data.get(f"reply{i}") else None
            if action.get("resolve"):
                res["resolved"] = data.get(f"resolve{i}", {}).get("thread", {}).get("isResolved") if data.get(f"resolve{i}") else None
            
            # Check for specific field errors if GraphQL returned partial success
            if errors:
                item_errors = [e["message"] for e in errors if any(p.startswith(f"reply{i}") or p.startswith(f"resolve{i}") for p in e.get("path", []))]
                if item_errors:
                    res["error"] = "; ".join(item_errors)
                elif "error" not in res:
                    res["error"] = "; ".join(e["message"] for e in errors)

            if "error" not in res and not errors and result.returncode == 0:
                 res["error"] = None
            elif not errors and result.returncode != 0:
                 res["error"] = "Unknown error"
                 
            results[item_id] = res

    pending_after = list_pending_review_ids(args.repo, args.pr_number, login)
    submitted = []
    new_pending = sorted(pending_after - pending_before)
    if new_pending:
        submitted = submit_pending_reviews(args.repo, args.pr_number, new_pending)

    audit_event(
        "batch_github_execute",
        "ok",
        args.repo,
        args.pr_number,
        args.audit_id,
        "Executed batch GitHub operations",
        {
            "actions_count": len(actions),
            "pending_before": sorted(pending_before),
            "pending_after": sorted(pending_after),
            "submitted": submitted,
        },
    )

    print(json.dumps(results, indent=2))
    return 1 if had_error else 0

if __name__ == "__main__":
    raise SystemExit(main())
