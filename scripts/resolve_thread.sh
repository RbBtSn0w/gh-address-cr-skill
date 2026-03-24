#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "$script_dir/common.sh"

dry_run=false
repo=""
pr_number=""
audit_id="default"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=true
      shift
      ;;
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --pr)
      pr_number="${2:-}"
      shift 2
      ;;
    --audit-id)
      audit_id="${2:-}"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--dry-run] [--repo <owner/repo> --pr <number>] [--audit-id <id>] <thread_id>"
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 [--dry-run] [--repo <owner/repo> --pr <number>] [--audit-id <id>] <thread_id>" >&2
  exit 1
fi

require_tools gh jq

thread_id="$1"

if [[ "$dry_run" == true ]]; then
  echo "[dry-run] Would resolve thread: $thread_id"
  if [[ -n "$repo" && -n "$pr_number" ]]; then
    details_json="$(jq -cn --arg tid "$thread_id" '{thread_id:$tid}')"
    audit_event "resolve_thread" "dry-run" "$repo" "$pr_number" "$audit_id" "Previewed thread resolve" \
      "$details_json"
  fi
  exit 0
fi

response="$(
gh api graphql \
  -f query='mutation($threadId:ID!){ resolveReviewThread(input:{threadId:$threadId}) { thread { id isResolved } } }' \
  -F threadId="$thread_id"
)"
echo "$response"

ensure_state_dir
if [[ -n "$repo" && -n "$pr_number" ]]; then
  mark_handled_thread "$thread_id" "$repo" "$pr_number"
  resolved="$(echo "$response" | jq -r '.data.resolveReviewThread.thread.isResolved // false')"
  details_json="$(jq -cn --arg tid "$thread_id" --arg resolved "$resolved" '{thread_id:$tid, is_resolved:($resolved=="true")}')"
  audit_event "resolve_thread" "ok" "$repo" "$pr_number" "$audit_id" "Resolved thread" \
    "$details_json"
else
  mark_handled_thread "$thread_id"
fi
