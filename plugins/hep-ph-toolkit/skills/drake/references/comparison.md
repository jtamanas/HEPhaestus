# Interpreting DRAKE Results and Comparing with MadDM / micrOMEGAs

## The intended use case: disagreement IS the signal

`/drake` is designed for regimes where the standard `<σv>` Taylor expansion fails.
A large departure from the MadDM or micrOMEGAs result is **expected and physically
meaningful** in narrow-resonance, early-kinetic-decoupling, forbidden, and
Sommerfeld-enhanced regimes. Report it as a result, not as a warning.

---

## Resonance trigger condition

Invoke `/drake` when:

```
|m_med − 2 m_χ| / m_med  <  0.1
```

(The mediator mass is within ~10% of twice the DM mass.) This is the regime where
the resonance in the s-channel becomes kinematically accessible near threshold and
the narrow-width approximation underlying the `<σv>` expansion breaks down.

The `scripts/resonance_check.py` helper evaluates this condition from a parameter dict.

---

## Comparison workflow

### Step 1: Run the standard tool

```python
# From /maddm output
omega_h2_standard = 0.034   # anomalously low due to resonance enhancement
```

### Step 2: Check the resonance trigger

```python
from scripts.resonance_check import is_narrow_resonance

in_regime = is_narrow_resonance(m_dm=100.0, m_med=195.0, threshold=0.1)
# True — proceed with DRAKE
```

### Step 3: Run DRAKE

```python
from scripts.run_drake import run_drake

result = run_drake(model="VRES", benchmark="bm_VRES", settings="settings_VRES")
# Read result["stdout"] to extract omega_h2 — see SKILL.md "Reading DRAKE output"
```

### Step 4: Report the comparison

```python
departure = (omega_h2_drake - omega_h2_standard) / omega_h2_standard

print(f"MadDM result:  Ω h² = {omega_h2_standard:.4f}")
print(f"DRAKE result:  Ω h² = {omega_h2_drake:.4f}")
print(f"Departure:     {departure:+.1%}")
```

---

## What departures mean physically

| Departure | Interpretation |
|-----------|---------------|
| < 5% | Standard tools adequate; DRAKE consistent |
| 5–20% | Moderate resonance / threshold effect; DRAKE more reliable |
| 20–50% | Significant breakdown of `<σv>` expansion; use DRAKE result |
| > 50% | Strong narrow-resonance or EKD effect; DRAKE result is the correct one; MadDM/micrOMEGAs result should not be used for exclusion or relic-density comparison |

The benchmarks in arXiv:2103.01944 demonstrate order-of-magnitude departures in the
narrow-resonance regime. Departures of this magnitude validate the need for DRAKE and
should be reported prominently.

---

## Expansion-breakdown diagnostic

If DRAKE's stdout contains a ratio of the full result to the standard `<σv>` expansion
result, record it alongside Ω h². Values far from 1 (say < 0.5 or > 2) confirm that
the expansion breakdown is driving the departure from MadDM. If no such ratio appears
in the stdout, compute it directly from the two Ω h² values:

```
expansion_ratio = omega_h2_drake / omega_h2_standard
```

The exact label for this quantity in DRAKE's stdout (if present) is visible in the
actual output — read the raw stdout rather than relying on a fixed field name.

---

## Planck 2018 comparison

After obtaining Ω h² from DRAKE, compare against the Planck 2018 measurement:

- **Planck 2018**: Ω h² = 0.1200 ± 0.0012 (TT,TE,EE+lowE+lensing)
- A model is consistent with observations when DRAKE's Ω h² ∈ [0.1188, 0.1212]
  (1σ band); relax to [0.1164, 0.1236] for 2σ

In the narrow-resonance regime, small changes in parameters (m_χ, m_med, coupling)
can shift Ω h² by orders of magnitude. DRAKE's full Boltzmann treatment correctly
captures this sensitivity.

---

## Multi-tool summary table (recommended output format)

When reporting results from a full workflow, emit a comparison table:

```
Tool          Ω h²         Status
-----------  -----------  -------
MadDM         3.4e-02      expansion breakdown suspected
micrOMEGAs    3.7e-02      consistent with MadDM
DRAKE (VRES)  1.19e-01     PREFERRED — full Boltzmann
Planck 2018   1.20e-01     target

Departure (DRAKE vs MadDM):  +250%   ← resonance funnel confirmed
Departure (DRAKE vs micrOMEGAs): +222%
```

---

## Tool-role summary

| Tool | Role | Notes |
|------|------|-------|
| `/maddm` | Primary relic density | Run first; triggers DRAKE comparison when expansion fails |
| `/micromegas` | Validator | Large coannihilation library; not designed for narrow-resonance regimes |
| `/drake` | Narrow-resonance / EKD specialist | Use when trigger condition fires; DRAKE result is authoritative |
