#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "$script_dir/common.sh"

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <owner/repo> <pr_number>" >&2
  exit 1
fi

require_tools jq
ensure_state_dir

repo="$1"
pr_number="$2"
log_file="$(audit_log_file "$repo" "$pr_number")"
summary_file="$(audit_summary_file "$repo" "$pr_number")"

echo "== Audit Report =="
echo "Repo: $repo"
echo "PR:   $pr_number"
echo "Log:  $log_file"
echo "Summary: $summary_file"
echo

if [[ -f "$log_file" ]]; then
  echo "== Last 20 Audit Events =="
  tail -n 20 "$log_file" | jq -c '.'
else
  echo "No audit log found."
fi

echo
if [[ -f "$summary_file" ]]; then
  echo "== Audit Summary SHA256 =="
  sha="$(sha256_of_file "$summary_file")"
  echo "$sha  $summary_file"
else
  echo "No audit summary found."
fi
