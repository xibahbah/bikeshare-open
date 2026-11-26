---
name: capture-fault
description: Capture the diff, hook stderr, and pytest output for an active seeded fault.
---

# Capture a seeded fault

Use `$ARGUMENTS` as the path of the modified Python file under `src/`.

1. Run `git --no-pager diff -- <path>` and show the exact change. If the
   path is missing or the diff is empty, stop and report that no fault is active.
2. Replay `.claude/hooks/check_leakage.sh` from the repo root with
   `CLAUDE_PROJECT_DIR` set to that root. Send a JSON payload with the
   absolute path as `tool_input.file_path`. Capture stderr and the exit code
   and label this a manual replay.
3. Run `make test` and capture its actual output and exit status. Identify
   the failing test and its assertion. Report a passing run if it passes.
4. Return the diff, hook stderr, and test output in separate code blocks
   for `docs/SEEDED_FAULTS.md`. Leave the fault in place for review.
