# Anomaly ledger: reading ANOMALY_CANCELLATION_FAILED

This document is operational, not a physics textbook.  It tells you what to do
when SARAH's `CheckModel[]` reports anomaly non-cancellation and `/sarah-build`
emits the `ANOMALY_CANCELLATION_FAILED` fatal blocker.

---

## What SARAH reports

When anomalies do not cancel, SARAH prints lines like:

```
Anomalies are not cancelled.
  Coefficient of [SU(3)]^3: 3
  Coefficient of [SU(2)]^3: 0
  Coefficient of [U(1)]^3: 1/6
  Coefficient of [SU(3)]^2 x U(1): 1
  Coefficient of [SU(2)]^2 x U(1): 0
  Coefficient of [gravity]^2 x U(1): 1/6
```

The agent reads `sarah.log` directly and extracts the 10 lines following
`Anomalies are not cancelled` — lines matching `coefficient.*=` — into the
blocker's `context.coefficients` list (see `/sarah-build` SKILL.md
§"Reading sarah.log").

---

## Blocker JSON shape

```json
{
  "code": "ANOMALY_CANCELLATION_FAILED",
  "mode": "fatal",
  "message": "SARAH anomaly check failed for model DarkSU3",
  "context": {
    "coefficients": [
      "Coefficient of [SU(3)]^3: 3",
      "Coefficient of [U(1)]^3: 1/6",
      "Coefficient of [gravity]^2 x U(1): 1/6"
    ]
  }
}
```

---

## How to read the coefficients

Each non-zero coefficient tells you which anomaly is uncancelled:

| Coefficient label | Anomaly type | Constraint |
|---|---|---|
| `[SU(3)]^3` | Pure color | Sum over left-handed color reps must vanish |
| `[SU(2)]^3` | Pure weak | Sum over left-handed SU(2) reps must vanish |
| `[U(1)]^3` | Pure hypercharge | Sum_L Y^3 - Sum_R Y^3 = 0 |
| `[SU(3)]^2 x U(1)` | Color-hypercharge | Sum_L T_3(SU3) Y - Sum_R T_3(SU3) Y = 0 |
| `[SU(2)]^2 x U(1)` | Weak-hypercharge | Sum_L T(SU2) Y - Sum_R T(SU2) Y = 0 |
| `[gravity]^2 x U(1)` | Gravitational | Sum_L Y - Sum_R Y = 0 |

For a new non-Abelian factor (e.g., SU(3)_dark):
- `[SU(3)_D]^3` must vanish.
- `[SU(3)_D]^2 x U(1)` with any U(1) must vanish.

---

## Common fixes

### Vector-like fermions (most BSM dark-quark models)

A pair `(psiDL, psiDR)` with opposite chiralities and identical gauge reps
contributes equal and opposite amounts to every anomaly coefficient.
Result: all coefficients are zero automatically.

If you see non-zero coefficients for a model with only vector-like pairs, check:
1. Are `psiDL` and `psiDR` declared with the same `reps`?
2. Is one declared as `dirac` (SARAH handles internally) while the other is
   `left`/`right`?  Fix: use `chirality: dirac` for a single entry.
3. Did you accidentally include an SM Weyl fermion (e.g., quark doublet `qL`)
   without its right-handed partner?

### Adding a spectator fermion

If the anomaly cancellation requires an additional fermion, add a new entry
to `fermions[]` in the spec with:
- The hypercharge that cancels the offending coefficient.
- Appropriate gauge reps (a SM-singlet is simplest).
- A mass term pairing with its conjugate in `lagrangian.mass_terms`.

Example: if `[gravity]^2 x U(1)` = 1/6 is non-zero, add a fermion with
Y = -1/6 to cancel it (with an equal contribution from its conjugate).

### Changing the hypercharge assignment

If the constraint is `[SU(3)]^2 x U(1): non-zero`, the hypercharge of a
color-charged fermion is wrong.  Check:
- `hypercharge` must be a rational with denominator ≤ 6.
- For a color triplet in SU(2) doublet: Y = 1/6 (quark doublet).
- For a color triplet singlet under SU(2): Y = 2/3 (up-type) or -1/3 (down-type).
- A color triplet with Y = 0 is allowed only if its SU(3) contribution is exactly
  cancelled by a corresponding anti-triplet with Y = 0.

### Dark SU(3) models

For pure-dark-QCD (no U(1)_D charge):
- All U(1)-involving coefficients are zero automatically if dark fermions are
  SM-neutral (hypercharge = 0).
- Only `[SU(3)_D]^3` is non-trivial.  For a triplet representation (3),
  this coefficient is 1 per left-handed fermion and -1 per right-handed fermion.
  A vector-like triplet (3_L + 3_R) gives coefficient 0.

---

## Re-running after a fix

After modifying `fermions[]` or `parameters[]` in the spec, run:

```bash
python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/validate_spec.py \
    <spec.yaml>
```

Then:

```bash
python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/build.py \
    <spec.yaml> --force
```

The `--force` flag bypasses the input-hash cache to ensure a full rebuild.
SARAH's `CheckModel[]` will re-run.  If anomalies cancel, the build proceeds.

---

## SARAH output location

The full SARAH log (including all `CheckModel[]` output) is at:

```
$STATE_ROOT/models/<name>/sarah_output/sarah.log
```

Read this file directly for the complete SARAH session output if the 10-line
excerpt in the blocker context is insufficient.
