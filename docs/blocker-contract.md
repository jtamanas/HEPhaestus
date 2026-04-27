# Three-state blocker contract

Status: live. PR-A owns the canonical schema for `tool_verified` and
`blocked`; PR-D extended it with `reference_only`. The PR-D follow-up
promoted `REFERENCE_ONLY` into `OutcomeMode` and wired it into
`outcome.classify`; the former `outcome_extensions.py` shim is gone.
This doc also covers the recoverable-failure list agents are expected
to handle before blocking.

Cross-refs: `ROADMAP.md`, `feedback_augment_not_replace.md`, SYSTEM_PROMPT
in `eval/harness/runners/claude_code.py`.

## Why three states

The original two-state contract (`tool_verified` vs `blocked`) forces a
binary choice that does not match how practitioners actually work. A
theorist whose MG5 install is missing LHAPDF does not "block" — they add
a flag and move on. A theorist asked for an order-of-magnitude estimate
does not need Monte Carlo — a tree-level closed form is the right answer.
The third state, `reference_only`, labels that estimate honestly so
downstream tooling can mark it as intentional rather than as a silent
Python fallback.

## Schema

### 1. `tool_verified`

Returned when the agent computed the answer with a verified Monte Carlo
tool (MadGraph, MadDM, Pythia, etc.) and the numerical result can be
reproduced from the generated artifacts (proc_card, param_card, LHE
output).

```json
{
  "status": "tool_verified",
  "value": {"sigma_SI": 7.6e-45, "sigma_SI_unit": "cm^2"},
  "tool": "MadDM 3.2",
  "artifacts": ["proc_card.dat", "param_card.dat", "maddm.log"]
}
```

### 2. `reference_only` (PR-D)

Returned for pedagogical / quick-estimate tasks where a closed-form
reference is the right answer. The agent MUST cite the equation used and
list caveats.

```json
{
  "status": "reference_only",
  "value": {"sigma_SI": 7.6e-45, "sigma_SI_unit": "cm^2"},
  "reference_method": "tree-level Higgs-portal closed-form, Eq. 5 of arXiv:2506.19062",
  "caveats": [
    "LO only",
    "no radiative corrections",
    "nucleon form factors from Hoferichter 2015"
  ]
}
```

Opt-in criteria (ALL must hold):

- Task has tag `pedagogical` or `quick_estimate`, OR the user prompt
  contains "estimate", "rough", or "order of magnitude".
- Agent can cite paper + equation number.
- Payload contains non-empty `reference_method` and `caveats`.

### 3. `blocked`

Returned for genuine, unrecoverable inability to produce an answer.

```json
{
  "status": "blocked",
  "reason": "MadDM not installed and task is not opted into reference_only",
  "what_would_unblock": "install MadDM 3.2 with LHAPDF, re-run"
}
```

## Decision tree (agent-facing)

```
Can I run the Monte Carlo tool and get a number?
├── yes → status: tool_verified
└── no  → Is the failure in the recoverable list?
          ├── yes → recover, retry, report as tool_verified
          └── no  → Is the task tagged pedagogical / quick_estimate,
                    or does the prompt ask for an estimate?
                    ├── yes → status: reference_only (cite + caveat)
                    └── no  → status: blocked
```

## Recoverable failures (do NOT block)

| Failure | Recovery |
|---|---|
| LHAPDF missing | `--no-lhapdf` or rely on built-in PDFs for DM-only observables |
| syscalc hang | `set systematics_program none` in run_card |
| Narrow-width warning on resonances | `set small_width_treatment 0` or accept warning for on-shell decays |
| UFO Py2/Py3 residue | Patch bare `print` statements; most modern UFOs are clean |
| Mass-ordering abort | Fix param_card: DM lighter than mediator (or model-specific order) |
| Timeout on first `launch` | Re-run with `nevents=1000` to validate, then scale up |

## Genuine blockers (DO block)

- MadGraph / MadDM binary not installed on the host.
- UFO / model file for the requested BSM model not available.
- Required skill not implemented in the plugin.
- Task asks for an observable the available tools physically cannot
  compute (e.g. NLO EW in a tool that only does LO QCD).

## Classifier mapping

| `status` | `OutcomeMode` |
|---|---|
| `tool_verified` | `MG_CORRECT` / `MG_WRONG` (by pass/fail) |
| `reference_only` | `REFERENCE_ONLY` (promoted into `OutcomeMode` and classified by `outcome.classify`) |
| `blocked` | `BLOCKED_CORRECTLY` |
| no `status` field, numeric answer present | `PY_FALLBACK` |
| runner error / exception | `RUNNER_ERROR` (PR-A) |

`REFERENCE_ONLY` is desired behavior for pedagogical tasks. It is NOT a
Python fallback and must not be counted as one in pass-rate reporting.
The validation logic (`_is_reference_only`) lives directly in
`eval/harness/outcome.py`; `outcome.classify` consults it ahead of the
PY_FALLBACK branch but after the `blocked` branch.

## Examples

### Recoverable → tool_verified (not blocked)

Agent runs MG5, sees `LHAPDF not found`, adds `--no-lhapdf`, re-runs,
gets a cross-section, returns `tool_verified`.

### Pedagogical → reference_only

Task tagged `pedagogical`, prompt asks for "a rough estimate of the
spin-independent cross section for a 100 GeV scalar singlet". Agent
evaluates the tree-level Higgs-portal formula, returns
`reference_only` with `reference_method` pointing at the formula and
`caveats` listing LO + form-factor uncertainty.

### Genuine → blocked

Task is a production-grade NLO calculation, MadGraph is not installed,
task has no estimation opt-in. Agent returns `blocked` with a clear
`what_would_unblock`.
