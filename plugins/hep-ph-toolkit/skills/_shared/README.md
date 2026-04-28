# _shared/ — Cross-skill registries and shared utilities

This directory contains registries and utilities shared across all skills in the
`hep-ph-demo` plugin and consumed by downstream plugins (e.g., `constraints`,
`workflow`).

## Files

**`constraints.yaml`** — canonical compatibility registry. Per-constraint default
chains, per-model chain overrides, prereq status (`exists` / `planned`), and
time estimates. The primary input for `time_budget.py` and the
`/dark-matter-constraints` prereq checker. See skill docs for schema details.

**`time_budget.py`** — render-chain logic. Given a model + selected constraints,
produces a `TimeReport` with `READY`/`BLOCKED` status per constraint (printed to
users as `READY` / `COMING SOON`) and overlap-adjusted time estimates. CLI:
`python3 time_budget.py --model dark-su3 --constraints relic dd id`.

**`analytic_exceptions.yaml`** — registry of mandatory regression-anchor and
proxy-run disclosures. Each entry pins a verbatim banner that must appear at
registered placement file paths (P1 = DMC SKILL.md, P2 = model SKILL.md,
P3 = analytic module docstring for `analytic` kind). Adding an entry is the
ONLY way to authorize a new analytic-backend or proxy-run pattern; entries are
reviewed in PR and gated by CI (banner well-formedness + placement assertions).
See `plugins/hep-ph-toolkit/skills/analytic-exception-detector/SKILL.md` for the
full sign-off contract, retirement policy, and lint-warning documentation.

**`assets/`** — auxiliary YAML assets shared across skills (cross-skill
helpers; canonical ModelSpec specs live at `modelspec_v3/specs/`).
