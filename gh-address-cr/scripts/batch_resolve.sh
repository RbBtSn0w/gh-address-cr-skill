#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
resolve_script="$script_dir/resolve_thread.sh"

dry_run=false
yes=false
repo=""
pr_number=""
audit_id="default"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=true
      shift
      ;;
    --yes)
      yes=true
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
      echo "Usage: $0 [--dry-run] [--yes] [--repo <owner/repo> --pr <number>] [--audit-id <id>] <thread_ids_file>"
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 [--dry-run] [--yes] [--repo <owner/repo> --pr <number>] [--audit-id <id>] <thread_ids_file>" >&2
  exit 1
fi

thread_file="$1"
if [[ ! -f "$thread_file" ]]; then
  echo "Thread id file not found: $thread_file" >&2
  exit 1
fi

if [[ "$dry_run" == false && "$yes" == false ]]; then
  echo "Refusing destructive bulk action without --yes (or use --dry-run)." >&2
  exit 1
fi

while IFS= read -r tid; do
  [[ -z "$tid" ]] && continue
  [[ "$tid" =~ ^# ]] && continue
  extra_args=()
  if [[ -n "$repo" && -n "$pr_number" ]]; then
    extra_args+=(--repo "$repo" --pr "$pr_number" --audit-id "$audit_id")
  fi
  if [[ "$dry_run" == true ]]; then
    bash "$resolve_script" --dry-run "${extra_args[@]}" "$tid"
  else
    bash "$resolve_script" "${extra_args[@]}" "$tid"
  fi
done < "$thread_file"
