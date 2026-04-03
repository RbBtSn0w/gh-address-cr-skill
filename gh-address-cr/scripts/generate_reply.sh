#!/usr/bin/env bash
set -euo pipefail

severity="P2"
mode="fix"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --severity)
      severity="${2:-}"
      shift 2
      ;;
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    --help|-h)
      cat <<'EOF'
Usage:
  generate_reply.sh [--severity P1|P2|P3] [--mode fix|clarify|defer] <output_md> [args...]

Modes:
  fix (default):
    generate_reply.sh [--severity P1|P2|P3] <output_md> <commit_hash> <files_csv> <test_command> <test_result> [why]
  
  clarify:
    generate_reply.sh --mode clarify <output_md> <rationale_text>
    
  defer:
    generate_reply.sh --mode defer <output_md> <rationale_text>

Examples:
  generate_reply.sh --severity P1 /tmp/reply.md 3434256 "src/app.py" "pytest" "passed" "Fixed bug."
  generate_reply.sh --mode clarify /tmp/reply.md "The current logic is correct because X."
  generate_reply.sh --mode defer /tmp/reply.md "This requires massive refactoring, deferring to next PR."
EOF
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 1 ]]; then
  echo "Error: Missing <output_md>" >&2
  exit 1
fi

output_md="$1"
output_dir="$(dirname "$output_md")"
mkdir -p "$output_dir"
shift

if [[ "$mode" == "fix" ]]; then
  if [[ $# -lt 4 ]]; then
    echo "Usage for fix: generate_reply.sh [--severity P1|P2|P3] <output_md> <commit_hash> <files_csv> <test_command> <test_result> [why]" >&2
    exit 1
  fi
  commit_hash="$1"
  files_csv="$2"
  test_command="$3"
  test_result="$4"
  why="${5:-Addressed the CR with minimal targeted changes and regression coverage.}"
  
  IFS=',' read -r -a files <<< "$files_csv"

  case "$severity" in
    P1|p1) severity="P1"; risk_note="High-severity path validated with targeted regression checks." ;;
    P2|p2) severity="P2"; risk_note="Medium-severity path validated and behavior aligned with expected workflow." ;;
    P3|p3) severity="P3"; risk_note="Low-severity improvement validated for non-breaking behavior." ;;
    *) echo "Invalid severity: $severity (expected P1/P2/P3)" >&2; exit 1 ;;
  esac

  {
    echo "Fixed in \`$commit_hash\`."
    echo
    echo "Severity: \`$severity\`"
    echo
    echo "What I changed:"
    for f in "${files[@]}"; do
      trimmed="$(echo "$f" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
      [[ -n "$trimmed" ]] && echo "- \`$trimmed\`: updated per CR scope"
    done
    echo
    echo "Why this addresses the CR:"
    echo "- $why"
    echo "- $risk_note"
    echo
    echo "Validation:"
    echo "- \`$test_command\`"
    echo "- Result: $test_result"
    echo
    echo "If anything still looks off, I can follow up with a focused patch."
  } > "$output_md"

elif [[ "$mode" == "clarify" ]]; then
  rationale="${1:-No code changes were made for this specific comment.}"
  {
    echo "Thanks for the review."
    echo
    echo "Analysis & Rationale:"
    echo "- $rationale"
    echo
    echo "Decision:"
    echo "- No code changes were made for this specific comment."
    echo
    echo "If you feel this still needs an adjustment, let me know and I can follow up with a patch!"
  } > "$output_md"

elif [[ "$mode" == "defer" ]]; then
  rationale="${1:-Marking as deferred (non-blocking for this PR).}"
  {
    echo "Thanks, this is valid feedback."
    echo
    echo "Decision:"
    echo "- Marking as deferred (non-blocking for this PR) because: $rationale"
    echo
    echo "Follow-up plan:"
    echo "1. Track in follow-up issue/PR."
    echo "2. Risk before follow-up: Low."
    echo
    echo "If you prefer, I can bring this into the current PR instead."
  } > "$output_md"

else
  echo "Invalid mode: $mode" >&2
  exit 1
fi

echo "Wrote reply template ($mode mode): $output_md"
