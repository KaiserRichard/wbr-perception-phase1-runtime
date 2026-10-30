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
    --model claude-opus-4-6-thinking -p "$prompt" > "$draft" 2>> "$error_log"; then
    if ! [[ -s "$draft" ]] || ! LC_ALL=C grep -q '[^[:space:]]' "$draft"; then
        printf 'agy returned an empty digest; see %s\n' "$error_log" >&2
        exit 1
    fi
    lines=$(awk 'END {print NR}' "$draft")
    if [[ "$lines" -ge 60 ]]; then
        cp "$draft" "$secretary_dir/out/digest-$run_date-$mode.rejected.md"
        printf 'agy returned %s lines (must be under 60); rejected draft retained in out/.\n' "$lines" >&2
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
