# Lab assistant kit (ChatGPT / Codex)

This folder lets ChatGPT or Codex run the routine parts of a lab day (storage move,
power check, hardware check, evidence copy, running lab cards A and B) by reading
the rules and steps directly from the repository. Claude is used only for review
and decisions, through a short handoff file.

| File | What it is |
|---|---|
| `INSTRUCTIONS.md` | Operating rules: role, system facts, evidence labels, safety stops |
| `skills/wbr-lab-preflight` | First 10 minutes of the session |
| `skills/wbr-storage-migrate` | Clone the 32 GB microSD to the 128 GB microSD |
| `skills/wbr-power-check` | Power, throttling, temperature, then card A |
| `skills/wbr-camera-hw-check` | USB3 link, serial, kernel log, then card B |
| `skills/wbr-evidence-copy` | Copy a run folder to the Mac with SHA-256 verification |
| `skills/wbr-claude-handoff` | Superseded by `ops/skills/wbr-session-end`; field checklist |
| `show_result.py` | Prints any lab tool `result.json` as a short table |
| `handoffs/` | Scratch notes (git-ignored); the real record is `ops/worklog/` |
| `claude/wbr-lab-handoff-review` | The matching skill for Claude |

## Setup, option A (recommended): Codex in the Mac repo folder

Codex reads `AGENTS.md` at the repository root automatically, which points here.

1. On the Mac, update the repo without switching branches:
   `cd ~/Desktop/Research/wbr-perception-phase1-runtime && git status -sb && git pull --ff-only`.
   If it is not on `main` or has local changes, stop and ask Claude; do not switch.
2. Pick a Codex account that is idle (accounts are shared between threads).
3. Start Codex in that folder with approvals on, so it asks before running a
   command (for the CLI: `codex` in the folder, keeping the default approval mode;
   do not use a "full auto" or "never ask" mode).
4. First message to Codex:
   > Read AGENTS.md and ops/lab-assistant/INSTRUCTIONS.md. We are starting a lab
   > session. Run the wbr-lab-preflight skill with me.
5. If Codex is allowed to run commands, it can run read-only checks itself on the
   Mac and over `ssh wbr-pi5`. Destructive steps still need you to type the
   `CONFIRM ...` phrase. Approve each command only after reading it.
6. Optional: if your Codex version supports skills folders, you can also copy
   `ops/lab-assistant/skills/*` into `~/.codex/skills/`. The kit works without it,
   because the instructions tell Codex where to read them.

## Setup, option B: ChatGPT app (chat only)

Use this when you just want a chat partner and will paste outputs yourself.

1. In ChatGPT, create a new **Project** named "WBR Lab Ops". If asked about memory,
   choose project-only memory.
2. Open the project's **Instructions** and paste the full text of `INSTRUCTIONS.md`
   (about 6 KB).
3. Add these as project **files**: every `skills/*/SKILL.md`, plus
   `docs/LAB_COMPANION.md` and `docs/PROJECT_STATE.md` for background.
   If your ChatGPT has a GitHub connector, you can instead connect
   `KaiserRichard/wbr-perception-phase1-runtime` and tell it to read this folder
   on `main`; uploaded files are simpler and do not go stale mid-session.
4. Pick a reasoning ("Thinking") model for diagnosis; a fast model is fine for
   simple command steps.
5. First message in a new chat inside the project:
   > Lab session today. Follow the project instructions. Start the
   > wbr-lab-preflight skill. One step at a time; I will paste outputs.
6. ChatGPT cannot write the handoff file here: it prints the block, and you save it
   as `ops/lab-assistant/handoffs/<date>-<topic>.md` on the Mac or paste it to Claude.

## Daily flow

1. `ops/skills/wbr-session-start` -> preflight -> (storage migration, if not done
   yet) -> power check -> camera hardware check -> card B if unblocked -> evidence
   copy -> `ops/skills/wbr-session-end`.
2. Every run gets a new output folder. Failures are kept.
3. Routine decisions are the assistant's (INSTRUCTIONS.md "Decision authority").
   Claude-level questions go through `ops/skills/wbr-claude-review-request`.
4. Setup for ChatGPT Work: `ops/CHATGPT_WORK_SETUP.md`.

## Boundaries

ChatGPT/Codex in this role does not change code, thresholds, profiles or
`docs/PROJECT_STATE.md`, does not commit or push, does not declare gate PASS, and
does not run cards C to G or any storage benchmark.
