#!/usr/bin/env bash
set -euo pipefail

severity="P2"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --severity)
      severity="${2:-}"
      shift 2
      ;;
    --help|-h)
      cat <<'EOF'
Usage:
  reply_fixed.sh [--severity P1|P2|P3] <output_md> <commit_hash> <files_csv> <test_command> <test_result> [why]

Example:
  reply_fixed.sh --severity P1 /tmp/reply.md 3434256 \
    "src/specify_cli/__init__.py,tests/test_ai_skills.py" \
    "uv run pytest tests/test_ai_skills.py" \
    "passed" \
    "Adjusted Kimi command display and added regression coverage."
EOF
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 5 ]]; then
  cat >&2 <<'EOF'
Usage:
  reply_fixed.sh [--severity P1|P2|P3] <output_md> <commit_hash> <files_csv> <test_command> <test_result> [why]
EOF
  exit 1
fi

output_md="$1"
commit_hash="$2"
files_csv="$3"
test_command="$4"
test_result="$5"
why="${6:-Addressed the CR with minimal targeted changes and regression coverage.}"
output_dir="$(dirname "$output_md")"

mkdir -p "$output_dir"

IFS=',' read -r -a files <<< "$files_csv"

case "$severity" in
  P1|p1)
    severity="P1"
    risk_note="High-severity path validated with targeted regression checks."
    ;;
  P2|p2)
    severity="P2"
    risk_note="Medium-severity path validated and behavior aligned with expected workflow."
    ;;
  P3|p3)
    severity="P3"
    risk_note="Low-severity improvement validated for non-breaking behavior."
    ;;
  *)
    echo "Invalid severity: $severity (expected P1/P2/P3)" >&2
    exit 1
    ;;
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
} > "$output_md" || {
  echo "Failed to write reply file: $output_md" >&2
  exit 1
}

echo "Wrote reply template: $output_md"
