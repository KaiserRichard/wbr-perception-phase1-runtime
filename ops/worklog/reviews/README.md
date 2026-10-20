# Review requests for Claude

Create `YYYY-MM-DD-<topic>.md` from this template, commit it on the branch of the PR
it concerns (or on its own worklog branch), push, then send Claude one line in the
WBR Claude project:

`Review ops/worklog/reviews/<file> on branch <branch> (PR #<n>).`

```markdown
# Review request: <topic>
Requested: <date time +07> by <agent>   PR: #<n>   Branch: <branch>

## What I need from Claude
1. <specific question, answerable with a decision>

## Context (cold-start summary, max 15 lines)
- <state, evidence paths, what was tried>

## My recommendation
<what I would do and why, with evidence labels>

## Claude review
<Claude writes here>
```
