#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./common.sh
source "$script_dir/common.sh"

clean_tmp=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean-tmp)
      clean_tmp=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--clean-tmp]"
      echo "  --clean-tmp   Also remove /tmp/gh-cr-reply*.md files"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--clean-tmp]" >&2
      exit 1
      ;;
  esac
done

if [[ -d "$state_dir" ]]; then
  rm -rf "$state_dir"
  echo "Removed state dir: $state_dir"
else
  echo "State dir not found: $state_dir"
fi

if [[ "$clean_tmp" == true ]]; then
  found=false
  for pattern in /tmp/gh-cr-reply*.md /tmp/reply-fixed-*.md; do
    if compgen -G "$pattern" > /dev/null; then
      rm -f $pattern
      echo "Removed temp files: $pattern"
      found=true
    fi
  done
  if [[ "$found" == false ]]; then
    echo "No matching temp reply files found in /tmp."
  fi
fi
