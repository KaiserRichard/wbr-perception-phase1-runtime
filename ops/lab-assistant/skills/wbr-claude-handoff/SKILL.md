---
name: wbr-claude-handoff
description: Superseded by ops/skills/wbr-session-end and wbr-claude-review-request; kept as the field checklist for a lab session log. Use when the user says "handoff", at the end of the lab day, or when a decision belongs to Claude under INSTRUCTIONS.md "Decision authority".
---

# Handoff for Claude (superseded)

Use `ops/skills/wbr-session-end` (session log, CURRENT.md, decisions) and
`ops/skills/wbr-claude-review-request` instead. The template below is still a good
checklist for the "Done" and "Raw facts" parts of a lab session log.

Goal: give Claude everything it needs in one short file so it does not have to
re-ask or re-run anything. Facts only, labeled, under 40 lines.

## Where
If you can write files in this repository folder, create
`ops/lab-assistant/handoffs/YYYY-MM-DD-HHMM-<topic>.md` (this folder is git-ignored;
do not commit it). Otherwise print the block and ask the user to save it there.
Then tell the user to send Claude, in the WBR project chat, one line:
`Review handoff ops/lab-assistant/handoffs/<file name> in my Mac repo folder.`
If Claude cannot reach the folder, the user pastes the block instead.

## Template
```markdown
# WBR lab handoff: <topic>, <YYYY-MM-DD HH:MM local>
Assistant: <ChatGPT / Codex>   Repo commit on Pi: <hash or UNKNOWN>

## Done (MEASURED unless labeled)
- <step>: <result in one line> (output folder: <path>, exit <code>)

## Tool results
| Tool | Folder | Exit | FAIL / BLOCKED criteria |
|---|---|---|---|

## Problems
- <symptom> | first broken layer: <power/USB/raw/...> | what was tried | INFERRED cause

## Decisions I made (and why)
- <decision>: <one-line reason>

## Open decisions for Claude or the owner
1. <only items that are Claude's or the owner's per Decision authority>

## Not done / blocked
- <item>: <why>

## Raw facts
throttled=<..>  temp=<..>  EXT5V=<..>  supply=<.. mA>  camera_usb=<5000M/480M>
serial=<..>  pyrealsense2=<OK/FAIL>  root_fs=<size/free>
```

## Rules
- No gate PASS claims. Write "tool PASS, awaiting review".
- Exact paths and exit codes; never paraphrase a status.
- Do not paste whole logs; point to their paths.
