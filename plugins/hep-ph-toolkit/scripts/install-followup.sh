#!/usr/bin/env bash
# Stop hook: after an install skill from this plugin runs, re-wake Claude to
# (1) ask the user whether installation succeeded, (2) offer to file a scrubbed
# bug report against the hephaestus GitHub repo, and (3) only post it with
# explicit user approval.
set -u

INSTALL_SKILLS_REGEX='^install$'

INPUT=$(cat)

if [ "$(printf '%s' "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)" = "true" ]; then
  exit 0
fi

TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  exit 0
fi

LAST_USER_LINE=$(jq -c 'select(.type=="user" and has("promptId") and .promptId != null) | input_line_number' "$TRANSCRIPT" 2>/dev/null | tail -n 1)
if [ -z "$LAST_USER_LINE" ]; then
  LAST_USER_LINE=0
fi

FIRED_SKILL=$(tail -n +$((LAST_USER_LINE + 1)) "$TRANSCRIPT" \
  | jq -r 'select(.type=="assistant") | (.message.content // [])[]? | select(.type=="tool_use" and .name=="Skill") | .input.skill // empty' 2>/dev/null \
  | grep -E "$INSTALL_SKILLS_REGEX" \
  | tail -n 1)

if [ -z "$FIRED_SKILL" ]; then
  exit 0
fi

SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // "nosession"' 2>/dev/null)
MARKER="${TMPDIR:-/tmp}/claude-hep-install-followup-${SESSION_ID}-${LAST_USER_LINE}"
if [ -f "$MARKER" ]; then
  exit 0
fi
: > "$MARKER"

REPO_SLUG=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || printf 'jtamanas/hephaestus')

jq -n --arg skill "$FIRED_SKILL" --arg repo "$REPO_SLUG" '
{
  decision: "block",
  reason: ("Install follow-up: the install skill \"" + $skill + "\" ran this turn. Before stopping: " +
    "(1) Ask the user verbatim: \"Did the installation complete successfully?\" Wait for their answer. " +
    "(2) If they report failure, partial success, or uncertainty, ask whether they want to file a scrubbed bug report against " + $repo + ". " +
    "(3) If yes, draft a GitHub issue: title summarizing the failure; body with OS + arch, install skill name (" + $skill + "), the failing command, and the last ~40 lines of relevant error output. " +
    "REDACT before showing: replace $HOME with ~, strip absolute user paths, remove env var values, tokens, API keys, email addresses, hostnames, and anything that looks personally identifying. " +
    "Show the drafted title and body to the user and ask for explicit \"yes, post it\" confirmation. " +
    "(4) Only after explicit confirmation, create the issue with: gh issue create --repo " + $repo + " --title <title> --body-file <tempfile> --label install-failure. " +
    "(5) If the user says install succeeded or declines to file a report, acknowledge briefly and stop.")
}'
