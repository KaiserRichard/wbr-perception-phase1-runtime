# Asking Claude for help (only when stuck)

Create `YYYY-MM-DD-<topic>.md`:

```markdown
# Stuck: <topic>
Branch: <branch>
## Error
<exact error, a few lines, plus the full log path>
## What I tried
- <attempt> -> <result>
## Question
<one question>
## Claude answer
```

Push it, then the owner sends Claude: `Help with ops/worklog/reviews/<file> on branch <branch>.`
