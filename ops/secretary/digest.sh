#!/usr/bin/env bash
set -euo pipefail

secretary_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
mode=${1:-daily}
if [[ $# -gt 1 || ( "$mode" != daily && "$mode" != afternoon ) ]]; then
    printf 'Usage: bash ops/secretary/digest.sh [daily|afternoon]\n' >&2
    exit 2
fi
bundle=$(bash "$secretary_dir/collect.sh")
run_date=$(date +%F)
digest="$secretary_dir/out/digest-$run_date-$mode.md"
error_log="$secretary_dir/out/digest-$run_date-$mode.stderr.log"
draft=$(mktemp "$secretary_dir/out/.digest.XXXXXX")
trap 'rm -f "$draft"' EXIT
prompt="$(cat "$secretary_dir/prompt_$mode.md")

<source_bundle>
$(cat "$bundle")
</source_bundle>"

printf '\n--- Attempt: %s ---\n' "$(date -Iseconds)" >> "$error_log"
# Keep CLI logs in the writable output directory. -p and its prompt stay last.
if agy --log-file "$secretary_dir/out/agy-$run_date-$mode.log" \
    --model claude-opus-4-6-thinking --output-format text -p "$prompt" > "$draft" 2>> "$error_log"; then
    lines=$(awk 'END {print NR}' "$draft")
    rejection=
    if [[ "$lines" -lt 20 || "$lines" -ge 60 ]]; then
        rejection="agy returned $lines lines (must be 20–59)"
    fi
    required_headers=(
        '## What works now (with key numbers)'
        '## What failed or is blocked'
        '## What the owner must do by hand'
        '## Open PRs to decide'
    )
    if [[ "$mode" == afternoon ]]; then
        required_headers+=('## How to demo it yourself' '## Next steps')
    fi
    for header in "${required_headers[@]}"; do
        if ! LC_ALL=C grep -Fxq -- "$header" "$draft"; then
            rejection="${rejection:+$rejection; }missing required heading: $header"
        fi
    done
    if [[ -n "$rejection" ]]; then
        cp "$draft" "$secretary_dir/out/digest-$run_date-$mode.rejected.md"
        printf '%s; rejected draft retained in out/.\n' "$rejection" | tee -a "$error_log" >&2
        exit 1
    fi
else
    status=$?
    cat "$draft" >> "$error_log"
    cat "$error_log" >&2
    printf 'agy failed (exit %s); retained error: %s\n' "$status" "$error_log" >&2
    exit "$status"
fi
mv "$draft" "$digest"
printf '%s\n' "$digest"
