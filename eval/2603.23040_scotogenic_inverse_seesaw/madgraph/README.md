# MadGraph / MadDM — arXiv:2603.23040 Scotogenic Inverse Seesaw

## UFO Model Plan State

**Current state:** Plan-C (UFO blocked — Day 0, no model yet)

### UFO Request Template (for author email)

```
Subject: Request for FeynRules UFO model — arXiv:2603.23040

Dear authors,

We are implementing the benchmark evaluation harness for arXiv:2603.23040
and would like to request the FeynRules/UFO model for the scotogenic
inverse seesaw model. Would you be willing to share the UFO package
(ScotoInverseSeesaw_UFO) or point us to a public repository?

Thank you.
```

**Author email:** [TODO: extract from paper front matter]

### Version Pin Fields (to be populated when UFO lands)

- FeynRules version: [TODO]
- UFO MD5 hash: [TODO]
- MG5_aMC version last verified: [TODO]
- Build date: [TODO]

## Plan A / Plan B / Plan C Clock

- **Day 0 (plan landing):** User emails authors with UFO request (template above).
- **Day 2:** If no response, begin Plan B (FeynRules rebuild) under `feynrules/`.
- **Day 5:** Plan B should yield a loadable UFO.
- **Day 7 (hard deadline):** Cutover to Plan C.

**Current status:** Plan-C ship. Tier-1 tasks relocated to `tier1_scoto_blocked.yaml.disabled`.

## Known Gap — UFO Blocked

The ScotoInverseSeesaw_UFO model is not yet available. Tier-1 tasks (proc_card, param_card)
are blocked and relocated to `eval/tasks/tier1_scoto_blocked.yaml.disabled`.

To re-enable when UFO lands:
1. Place the UFO directory at `eval/2603.23040_scotogenic_inverse_seesaw/madgraph/ScotoInverseSeesaw_UFO/`
2. Rename `eval/tasks/tier1_scoto_blocked.yaml.disabled` → `eval/tasks/tier1_scoto.yaml`
3. Run the reference runner: `python -m eval.harness.run --runner reference --tier 1 --tag paper-2`

## MadDM Gating

**Status:** Plan-C MadDM drop. Sample output could not be obtained within 2h search budget.

`generate_maddm_tasks.py` always returns 0 and emits nothing. To restore MadDM:
1. Obtain a MadDM v3.2 sample output showing `<sigma*v> (cm^3/s) = ...` and `Omega h^2 = ...` format.
2. Implement `_maddm_env_ok()` gate in `generate_maddm_tasks.py`.
3. Write `run_comparison.py` with parser matching the actual output format.
4. Add `scoto_maddm_sigmav_BP2` and `scoto_maddm_omega_BP2` to `eval/harness/refs.py`.
