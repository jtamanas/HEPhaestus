# Run report — workflow-skill (2026-04-26)


## WS5 validation summary

_Generated 2026-04-26T17:55:50Z @ 6c3631a0929aaad59492436f7ba9d422df201b6c_

# Model-Router Validation Report (WS5)

Fixture registry: /Users/yianni/Projects/hep-ph-agents/plugins/workflow/skills/model-router/tests/fixtures/registries

## singlet-doublet

**Verdict (default):** CLEAR
**Exit code:** default=0, strict=0

| Observable | Status | Active Chain | Blockers |
|---|---|---|---|
| relic | ROUTED | maddm | (none) |
| dd | ROUTED | ddcalc | (none) |
| id | ROUTED | maddm | (none) |

**Assertion categories:**
  [OK] per_observable_active_chain_dd
  [OK] per_observable_active_chain_id
  [OK] per_observable_active_chain_relic
  [OK] per_observable_blockers_set_dd
  [OK] per_observable_blockers_set_id
  [OK] per_observable_blockers_set_relic
  [OK] per_observable_status_dd
  [OK] per_observable_status_id
  [OK] per_observable_status_relic
  [OK] verdict

---

## two-hdm-a

**Verdict (default):** HALT_FOR_SIGNOFF
**Exit code:** default=0, strict=5

| Observable | Status | Active Chain | Blockers |
|---|---|---|---|
| relic | HALT | null | (none) |
| dd | HALT | null | (none) |
| id | HALT | null | (none) |

**Placements (2):**
  [0] kind=halt_notice position=top exception_id=None
  [1] kind=signoff_prompt position=appendix exception_id=None

**Assertion categories:**
  [OK] per_observable_active_chain_dd
  [OK] per_observable_active_chain_id
  [OK] per_observable_active_chain_relic
  [OK] per_observable_blockers_set_dd
  [OK] per_observable_blockers_set_id
  [OK] per_observable_blockers_set_relic
  [OK] per_observable_status_dd
  [OK] per_observable_status_id
  [OK] per_observable_status_relic
  [OK] verdict

---

## dark-su3

**Verdict (default):** ROUTE_TO_ANALYTIC
**Exit code:** default=0, strict=4

| Observable | Status | Active Chain | Blockers |
|---|---|---|---|
| relic | ROUTED | analytic_backend | (none) |
| dd | ROUTED | analytic_backend | (none) |
| id | ROUTED | analytic_backend | (none) |

**Placements (1):**
  [0] kind=analytic position=before_per_observable exception_id=dsu3-002

**Assertion categories:**
  [OK] dsu3_banner_triple_substring
  [OK] per_observable_active_chain_dd
  [OK] per_observable_active_chain_id
  [OK] per_observable_active_chain_relic
  [OK] per_observable_blockers_set_dd
  [OK] per_observable_blockers_set_id
  [OK] per_observable_blockers_set_relic
  [OK] per_observable_status_dd
  [OK] per_observable_status_id
  [OK] per_observable_status_relic
  [OK] verdict

---

## dark-su3-confining-synthetic

**Verdict (default):** HARD_HALT
**Exit code:** default=0, strict=6

| Observable | Status | Active Chain | Blockers |
|---|---|---|---|
| relic | HARD_HALT | null | (none) |
| dd | HARD_HALT | null | (none) |
| id | HARD_HALT | null | (none) |

**Placements (1):**
  [0] kind=hard_halt_prompt position=top exception_id=None

**Assertion categories:**
  [OK] hard_halt_no_signoff
  [OK] per_observable_active_chain_dd
  [OK] per_observable_active_chain_id
  [OK] per_observable_active_chain_relic
  [OK] per_observable_blockers_set_dd
  [OK] per_observable_blockers_set_id
  [OK] per_observable_blockers_set_relic
  [OK] per_observable_status_dd
  [OK] per_observable_status_id
  [OK] per_observable_status_relic
  [OK] verdict

---

