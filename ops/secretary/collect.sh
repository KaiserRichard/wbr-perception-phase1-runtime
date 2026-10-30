#!/usr/bin/env bash
set -euo pipefail

secretary_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$secretary_dir" rev-parse --show-toplevel)
out_dir="$secretary_dir/out"
mkdir -p "$out_dir"
run_date=$(date +%F)
bundle="$out_dir/bundle-$run_date.md"
scratch=$(mktemp -d "$out_dir/.collect.XXXXXX")
trap 'rm -rf "$scratch"' EXIT
draft="$scratch/bundle.md"

collect_repo() {
    local repo=$1 include_worktree=$2 ref branch path last_date count
    printf '\n## Repository: %s\n' "$repo" >> "$draft"
    if ! git -C "$repo" fetch origin > "$scratch/fetch.log" 2>&1; then
        printf '\nCollection status: BLOCKED — git fetch origin failed; the following remote refs are cached and may be stale.\n```text\n' >> "$draft"
        cat "$scratch/fetch.log" >> "$draft"
        printf '\n```\n' >> "$draft"
        cat "$scratch/fetch.log" >&2
    fi
    git -C "$repo" for-each-ref --format='%(refname)' refs/remotes/origin/ > "$scratch/refs"
    count=0
    while read -r ref; do
        [[ "$ref" != refs/remotes/origin/HEAD ]] || continue
        branch=${ref#refs/remotes/}
        count=$((count + 1))
        printf '\n### Branch: %s\n' "$branch" >> "$draft"
        git -C "$repo" ls-tree -r --name-only "$ref" -- \
            ops/worklog/reviews/ ops/worklog/ledger/ | \
            awk '/^ops\/worklog\/(reviews|ledger)\/.*\.md$/ {print}' | LC_ALL=C sort -u > "$scratch/paths"
        while IFS= read -r path; do
            [[ -n "$path" ]] || continue
            last_date=$(git -C "$repo" log -1 --format=%cI "$ref" -- "$path")
            printf '\n#### Source file: %s | repo: %s | branch: %s | last commit date: %s\n\n' \
                "$path" "$repo" "$branch" "$last_date" >> "$draft"
            git -C "$repo" show "$ref:$path" >> "$draft"
            printf '\n' >> "$draft"
        done < "$scratch/paths"
        printf '\n#### Existing image paths | repo: %s | branch: %s\n\n' "$repo" "$branch" >> "$draft"
        git -C "$repo" ls-tree -r --name-only "$ref" -- reports/ results/ docs/ | \
            awk '/\.(png|svg)$/ {print "- " $0}' >> "$draft"
    done < "$scratch/refs"
    if [[ "$count" -eq 0 ]]; then
        printf '\nNo origin branch tips were found.\n' >> "$draft"
    fi
    if [[ "$include_worktree" == yes ]]; then
        branch=$(git -C "$repo" symbolic-ref --short -q HEAD || git -C "$repo" rev-parse --short HEAD)
        for path in "$repo"/ops/worklog/reviews/*.md "$repo"/ops/worklog/ledger/*.md; do
            [[ -f "$path" ]] || continue
            path=${path#"$repo"/}
            last_date=$(git -C "$repo" log -1 --format=%cI -- "$path")
            printf '\n#### Source file: %s | repo: %s | branch: %s (local working tree) | last commit date: %s\n\n' \
                "$path" "$repo" "$branch" "${last_date:-uncommitted}" >> "$draft"
            cat "$repo/$path" >> "$draft"
            printf '\n' >> "$draft"
        done
        printf '\n#### Existing image paths | repo: %s | branch: %s (HEAD)\n\n' "$repo" "$branch" >> "$draft"
        git -C "$repo" ls-tree -r --name-only HEAD -- reports/ results/ docs/ | \
            awk '/\.(png|svg)$/ {print "- " $0}' >> "$draft"
    fi
}

printf '# Secretary source bundle\n\nGenerated: %s\nWindow: all existing review and ledger Markdown files at every fetched origin branch tip.\n' \
    "$(date -Iseconds)" > "$draft"
collect_repo "$repo_root" no
for extra_repo in "$HOME/Desktop/OS/OS-project/heterogeneous-edge-ai-os" "$HOME/Desktop/CN"; do
    if [[ -d "$extra_repo" ]]; then
        if git -C "$extra_repo" rev-parse --show-toplevel > "$scratch/root" 2>/dev/null && \
            [[ "$(cat "$scratch/root")" == "$extra_repo" ]]; then
            collect_repo "$extra_repo" yes
        else
            printf '\n## Repository: %s\nCollection status: BLOCKED — directory exists but is not a Git repository root.\n' "$extra_repo" >> "$draft"
        fi
    fi
done

for pr_repo in "$repo_root" KaiserRichard/heterogeneous-edge-ai-os; do
    printf '\n## Open PRs | source: gh pr list | repo: %s\n\n```json\n' "$pr_repo" >> "$draft"
    if [[ "$pr_repo" == "$repo_root" ]]; then
        if (cd "$repo_root" && gh pr list --state open --json number,title,headRefName,updatedAt) > "$scratch/prs.json" 2> "$scratch/prs.err"; then
            cat "$scratch/prs.json" >> "$draft"
        else
            printf '```\nCollection status: BLOCKED — open PRs unavailable.\n```text\n' >> "$draft"
            cat "$scratch/prs.err" >> "$draft"
        fi
    elif gh pr list --repo "$pr_repo" --state open --json number,title,headRefName,updatedAt > "$scratch/prs.json" 2> "$scratch/prs.err"; then
        cat "$scratch/prs.json" >> "$draft"
    else
        printf '```\nCollection status: BLOCKED — repository not visible or PR query failed.\n```text\n' >> "$draft"
        cat "$scratch/prs.err" >> "$draft"
    fi
    printf '\n```\n' >> "$draft"
done
mv "$draft" "$bundle"
printf '%s\n' "$bundle"
