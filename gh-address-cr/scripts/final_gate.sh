#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "$script_dir/common.sh"

auto_clean=true
audit_id="default"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto-clean)
      auto_clean=true
      shift
      ;;
    --no-auto-clean)
      auto_clean=false
      shift
      ;;
    --audit-id)
      audit_id="${2:-}"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--auto-clean|--no-auto-clean] [--audit-id <id>] <owner/repo> <pr_number>"
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 [--auto-clean|--no-auto-clean] [--audit-id <id>] <owner/repo> <pr_number>" >&2
  exit 1
fi

require_tools jq
ensure_state_dir

repo="$1"
pr_number="$2"
audit_event "final_gate" "start" "$repo" "$pr_number" "$audit_id" "Running final freshness gate"
list_script="$script_dir/list_threads.sh"

if [[ ! -x "$list_script" ]]; then
  echo "Missing executable script: $list_script" >&2
  exit 1
fi

snapshot="$(snapshot_file "$repo" "$pr_number")"
tmp_snapshot="${snapshot}.final"
summary_file="$(audit_summary_file "$repo" "$pr_number")"

"$list_script" "$repo" "$pr_number" > "$tmp_snapshot"
mv "$tmp_snapshot" "$snapshot"

unresolved_count="$(jq -r 'select(.isResolved == false) | .id' "$snapshot" | wc -l | tr -d ' ')"

echo "== Final Freshness Check =="
echo "Unresolved thread count: $unresolved_count"

if [[ "$unresolved_count" -gt 0 ]]; then
  echo
  echo "== Pending Review Table =="
  jq -r '
    select(.isResolved == false) |
    [.id, (.path // "-"), (if .line == null then "-" else (.line|tostring) end), (.url // "-")] |
    @tsv
  ' "$snapshot" | while IFS=$'\t' read -r id path line url; do
    echo "- id=$id path=$path line=$line url=$url"
  done
  {
    echo "# Audit Summary"
    echo
    echo "- audit_id: $audit_id"
    echo "- repo: $repo"
    echo "- pr: $pr_number"
    echo "- gate: FAILED"
    echo "- unresolved_count: $unresolved_count"
    echo
    echo "## Pending Review Table"
    jq -r '
      select(.isResolved == false) |
      "- id=\(.id) path=\(.path // "-") line=\(if .line == null then "-" else (.line|tostring) end) url=\(.url // "-")"
    ' "$snapshot"
  } > "$summary_file"
  summary_hash="$(sha256_of_file "$summary_file")"
  echo "Audit summary: $summary_file"
  echo "Audit summary sha256: $summary_hash"
  details_json="$(jq -cn \
    --arg uc "$unresolved_count" \
    --arg sf "$summary_file" \
    --arg sh "$summary_hash" \
    '{unresolved_count:($uc|tonumber), summary_file:$sf, summary_sha256:$sh}')"
  audit_event "final_gate" "failed" "$repo" "$pr_number" "$audit_id" "Gate failed; unresolved threads remain" \
    "$details_json"
  echo
  echo "Gate FAILED: unresolved threads remain. Do not send completion summary." >&2
  exit 3
fi

echo "Verified: 0 Unresolved Threads found"

{
  echo "# Audit Summary"
  echo
  echo "- audit_id: $audit_id"
  echo "- repo: $repo"
  echo "- pr: $pr_number"
  echo "- gate: PASSED"
  echo "- unresolved_count: 0"
  echo "- confirmation: Verified: 0 Unresolved Threads found"
} > "$summary_file"
summary_hash="$(sha256_of_file "$summary_file")"
echo "Audit summary: $summary_file"
echo "Audit summary sha256: $summary_hash"
details_json="$(jq -cn --arg sf "$summary_file" --arg sh "$summary_hash" '{unresolved_count:0, summary_file:$sf, summary_sha256:$sh}')"
audit_event "final_gate" "ok" "$repo" "$pr_number" "$audit_id" "Gate passed with zero unresolved threads" \
  "$details_json"

if [[ "$auto_clean" == true ]]; then
  cleanup_pr_state_files "$repo" "$pr_number"
  echo "Auto-cleaned PR state snapshot files."
  audit_event "final_gate" "ok" "$repo" "$pr_number" "$audit_id" "Auto-clean completed after gate pass"
fi
