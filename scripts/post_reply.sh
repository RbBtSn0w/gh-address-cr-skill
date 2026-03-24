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
      echo "Usage: $0 [--dry-run] [--repo <owner/repo> --pr <number>] [--audit-id <id>] <thread_id> <reply_markdown_file>"
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 [--dry-run] [--repo <owner/repo> --pr <number>] [--audit-id <id>] <thread_id> <reply_markdown_file>" >&2
  exit 1
fi

require_tools gh jq

thread_id="$1"
reply_file="$2"

if [[ ! -f "$reply_file" ]]; then
  echo "Reply file not found: $reply_file" >&2
  exit 1
fi

reply_body="$(cat "$reply_file")"

if [[ "$dry_run" == true ]]; then
  echo "[dry-run] Would reply to thread: $thread_id"
  echo "-----"
  cat "$reply_file"
  echo "-----"
  if [[ -n "$repo" && -n "$pr_number" ]]; then
    details_json="$(jq -cn --arg tid "$thread_id" --arg rf "$reply_file" '{thread_id:$tid, reply_file:$rf}')"
    audit_event "post_reply" "dry-run" "$repo" "$pr_number" "$audit_id" "Previewed thread reply" \
      "$details_json"
  fi
  exit 0
fi

response="$(
gh api graphql \
  -f query='mutation($threadId:ID!,$body:String!){ addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$threadId,body:$body}){ comment{ url } } }' \
  -F threadId="$thread_id" \
  -F body="$reply_body"
)"
echo "$response"

if [[ -n "$repo" && -n "$pr_number" ]]; then
  reply_url="$(echo "$response" | jq -r '.data.addPullRequestReviewThreadReply.comment.url // ""')"
  details_json="$(jq -cn --arg tid "$thread_id" --arg rf "$reply_file" --arg ru "$reply_url" '{thread_id:$tid, reply_file:$rf, reply_url:$ru}')"
  audit_event "post_reply" "ok" "$repo" "$pr_number" "$audit_id" "Posted thread reply" \
    "$details_json"
fi
