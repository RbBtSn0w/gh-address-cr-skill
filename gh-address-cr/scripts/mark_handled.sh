#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "$script_dir/common.sh"

repo=""
pr_number=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --pr)
      pr_number="${2:-}"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--repo <owner/repo> --pr <number>] <thread_id>"
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 [--repo <owner/repo> --pr <number>] <thread_id>" >&2
  exit 1
fi

thread_id="$1"
ensure_state_dir
if [[ -n "$repo" && -n "$pr_number" ]]; then
  mark_handled_thread "$thread_id" "$repo" "$pr_number"
  echo "Marked handled: $thread_id (scope: $repo#$pr_number)"
else
  mark_handled_thread "$thread_id"
  echo "Marked handled: $thread_id (scope: global fallback)"
fi
