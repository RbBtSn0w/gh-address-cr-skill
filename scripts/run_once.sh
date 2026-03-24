#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "$script_dir/common.sh"

show_all=false
audit_id="default"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --show-all)
      show_all=true
      shift
      ;;
    --audit-id)
      audit_id="${2:-}"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--show-all] [--audit-id <id>] <owner/repo> <pr_number>"
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 [--show-all] [--audit-id <id>] <owner/repo> <pr_number>" >&2
  exit 1
fi

require_tools jq
ensure_state_dir

repo="$1"
pr_number="$2"
audit_event "run_once" "start" "$repo" "$pr_number" "$audit_id" "Starting triage snapshot"

list_script="$script_dir/list_threads.sh"
snapshot="$(snapshot_file "$repo" "$pr_number")"
handled_file="$(handled_threads_file "$repo" "$pr_number")"
prev_snapshot="${snapshot}.prev"
repo_key="$(normalize_repo "$repo")"
curr_unresolved_ids_file="$state_dir/${repo_key}__pr${pr_number}__current_unresolved_ids.txt"
prev_unresolved_ids_file="$state_dir/${repo_key}__pr${pr_number}__prev_unresolved_ids.txt"
new_unresolved_ids_file="$state_dir/${repo_key}__pr${pr_number}__new_unresolved_ids.txt"

if [[ ! -x "$list_script" ]]; then
  echo "Missing executable script: $list_script" >&2
  exit 1
fi

if [[ -f "$snapshot" ]]; then
  cp "$snapshot" "$prev_snapshot"
fi

echo "== PR Review Threads =="
"$list_script" "$repo" "$pr_number" | tee "$snapshot"

echo
if [[ ! -f "$handled_file" ]]; then
  touch "$handled_file"
fi

if [[ "$show_all" == true ]]; then
  echo "== Unresolved Threads (including handled) =="
  jq -c 'select(.isResolved == false)' "$snapshot"
else
  echo "== Unresolved Threads (excluding handled) =="
  jq -c 'select(.isResolved == false)' "$snapshot" \
    | while IFS= read -r row; do
        tid="$(echo "$row" | jq -r '.id')"
        if ! grep -Fxq "$tid" "$handled_file"; then
          echo "$row"
        fi
      done
fi

jq -r 'select(.isResolved == false) | .id' "$snapshot" | sort -u > "$curr_unresolved_ids_file"

if [[ -f "$prev_snapshot" ]]; then
  jq -r 'select(.isResolved == false) | .id' "$prev_snapshot" | sort -u > "$prev_unresolved_ids_file"
  comm -23 "$curr_unresolved_ids_file" "$prev_unresolved_ids_file" > "$new_unresolved_ids_file"
else
  : > "$new_unresolved_ids_file"
fi

echo
echo "== Newly Appeared Unresolved Threads Since Last Snapshot =="
if [[ -s "$new_unresolved_ids_file" ]]; then
  while IFS= read -r tid; do
    jq -c --arg tid "$tid" 'select(.id == $tid and .isResolved == false)' "$snapshot"
  done < "$new_unresolved_ids_file"
else
  echo "None"
fi

echo
echo "Snapshot saved: $snapshot"
echo "Handled state:  $handled_file"

unresolved_count="$(wc -l < "$curr_unresolved_ids_file" | tr -d ' ')"
new_unresolved_count="$(wc -l < "$new_unresolved_ids_file" | tr -d ' ')"
details_json="$(jq -cn \
  --arg uc "$unresolved_count" \
  --arg nc "$new_unresolved_count" \
  --arg snapshot "$snapshot" \
  '{unresolved_count:($uc|tonumber), new_unresolved_count:($nc|tonumber), snapshot:$snapshot}')"
audit_event "run_once" "ok" "$repo" "$pr_number" "$audit_id" "Triage snapshot completed" \
  "$details_json"
