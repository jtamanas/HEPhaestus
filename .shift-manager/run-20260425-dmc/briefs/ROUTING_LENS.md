# Routing Lens — How to decide deterministic-helper vs LLM-judgment

**This is the load-bearing philosophy for every workstream in this run. Every subagent must apply it.**

## The lens

The user wants Claude to act as a **competent collaborator** for the `/dark-matter-constraints` router — someone who knows the right tools and how to use them, and who can handle one-off requests SKILL.md flags don't anticipate.

That gives a clean rule for splitting work between code (deterministic helpers) and the LLM (the agent itself):

| If a piece of logic is… | Owner |
|---|---|
| Truly mechanical AND model-agnostic (works for any BSM model) | **Deterministic helper (code)** |
| Heuristic with a default but expert-overridable | **LLM (agent reads SKILL.md prose)** |
| A contract between tools (field names, schemas, exit codes) | **Deterministic helper (code)** |
| A judgment call about *whether* this case warrants a check | **LLM** |
| Cannot be guaranteed to work for any BSM model the user might throw at it | **LLM (do NOT put in code)** |

## The hard constraint (user emphasized)

> **Deterministic helpers MUST be model-agnostic. If we cannot guarantee a helper works for any BSM model the user might bring, that piece must stay in the LLM, not in code.**

Apply this lens with extra scrutiny to:

- **`read_maddm_output`** — MadDM output formats may vary by model class (MSSM-style with full SLHA spectrum vs simplified-model UFO with `param_card.dat`). If the parser can't be guaranteed to handle both, the parsing stays in the LLM and only a thin "open this file, assert these specific keys exist" check goes in code.
- **`read_micromegas_output`** — same risk; CalcHEP path emits different output for different model classes.
- **`compare_dm`** — must compare canonical fields. If the canonical schema can't accommodate every model class (e.g. multi-component DM, asymmetric DM), the comparison stays in the LLM.
- **`detect_drake`** — purely about tool installation state, not model. **Safe for code.**
- **Step 1 prereq check** — file existence checks. **Safe for code.**

## Step ownership map (target end-state)

From `plugins/constraints/skills/dark-matter-constraints/SKILL.md`:

| Step | Currently | Should be |
|---|---|---|
| Step 1 — prereq check | LLM in prose | **Helper** (`check_prereqs`) — pure file-existence |
| Step 2 — invoke /maddm | LLM | **LLM** (orchestration; no judgment but trivial) |
| Step 3 — 10% trigger arithmetic | LLM | **LLM** (the 10% is heuristic; expert may override) |
| Step 4a — invoke /micromegas | LLM | **LLM** |
| Step 4b — extract fields, compute rel-diff | LLM | **Helper** (`compare_dm`) — IF model-agnostic schema possible |
| Step 5a — DRAKE four-branch availability | LLM | **Helper** (`detect_drake`) — pure tool-state check |
| Step 5b — narrow-resonance trigger (5%) | LLM | **LLM** (heuristic) |
| Output — refuse to silently pick winner | LLM in prose | **Helper** (`compare_dm` returns flagged rows; render is mechanical) |

## What every subagent must do

1. **Read the user's actual `/dark-matter-constraints` SKILL.md** at `plugins/constraints/skills/dark-matter-constraints/SKILL.md` before producing output. Don't reason from summaries.
2. **Read `/maddm`, `/micromegas`, `/drake` SKILL.md** if your task touches output contracts.
3. **Always state, for any piece of logic you propose moving into code, why you can guarantee model-agnosticism.** If you can't, route it to the LLM.
4. **Never** invent a field name. If you can't find it documented, say "field name not specified in source; agent must adjudicate at runtime."

## Workflow (this run)

Strict ordering: **WS-1 → WS-4 → (WS-2 ∥ WS-3)**.

- **WS-1: Output-contract verification.** Audit which JSON fields the router reads, find where each is defined in the downstream skill spec and emitted in real run output, flag drift.
- **WS-4: Refactor.** Build small model-agnostic helpers. Rewrite SKILL.md so routing/judgment stays LLM-driven. Helpers identified as risk-of-non-agnostic go back to the LLM.
- **WS-2: Test harness.** Fixture-based tests for all helpers from WS-4.
- **WS-3: Dark SU(3) end-to-end playtest.** Exercise the new router on Profumo's Fig. 8 (arXiv:2506.19062) — chosen because it fires the DRAKE branch.

## Non-goals

- No GitHub interaction. Local git only.
- No router-level deterministic Python orchestrator (`dark-matter-constraints.py`). That was the discarded option.
- No new physics. The router is a router; helpers are contract guards. Physics stays in /maddm, /micromegas, /drake.
