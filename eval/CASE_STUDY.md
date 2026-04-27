# Case Study: How the Eval Suite Found Its Own Bugs

**Date**: 2026-04-16
**Paper**: arXiv:2506.19062 — WIMPs Below the Radar (Arcadi & Profumo)
**Model tested**: Opus, with and without MadGraph/MadDM skills

## Summary

While building evals to measure whether MadGraph skills improve Claude's physics
calculations, the eval itself surfaced two bugs in our reference implementation —
one caught by the eval's A/B comparison, and one caught by Claude reading the
original paper more carefully than we did.

The punchline: **we set out to test the skills, and the skills tested us.**

---

## What we built

An eval harness with 35 tasks across three tiers, graded by comparing Claude's
output against analytical Python implementations of the paper's equations. Two
runner modes:

- `--runner claude` — spawns Claude Code with the MadGraph/MadDM plugin loaded
- `--runner claude --no-skills` — same prompts, no plugin

Both modes require Claude to write and execute Python code (not compute from
memory). The A/B comparison measures the delta the skills provide.

## The first run: skills vs no-skills on Tier 2 (18 physics tasks)

Both scored **16/18** — same pass rate, but different failures:

| Task | With Skills | Without Skills |
|------|-------------|----------------|
| `t2_sd_si_symmetric` (θ=π/4) | **PASS** | FAIL (376% error) |
| `t2_sd_si_heavy` (m_S=1000) | FAIL (19%) | FAIL (138%) |
| `t2_dsu3_vector_bp1` (g̃=2) | FAIL (10.5%) | **PASS** (exact match) |

Two things stood out:

1. The skills clearly helped on `t2_sd_si_symmetric` — the hardest singlet-doublet
   benchmark, where maximal mixing makes the coupling formula most sensitive.
   Without skills: 376% error. With skills: exact pass.

2. But `t2_dsu3_vector_bp1` was **worse** with skills — 10.5% error vs exact match
   without skills. That shouldn't happen if the skills are providing correct
   information. Something was wrong, but with which side?

## Diagnosis 1: The nucleon form factor convention (f_N)

The user asked Claude Code (the same Opus instance running the conversation)
to investigate the failures. All diagnosis happened live in one session — Claude
Code reading the eval JSON output, running Python snippets to decompose the
formulas, and tracing the discrepancy step by step. No archived chats were
resurfaced; it was real-time detective work in the terminal.

Claude Code started with `t2_sd_si_heavy`. It pulled the expected and actual
values from the JSON report and noticed the DM mass was perfect (5×10⁻¹³
relative error) but σ_SI was 19% off. Since σ_SI depends on m_chi1, y_h, and
f_N, and the mass was exact, the error had to be in the coupling or the form
factor.

Claude Code then ran a sequence of Python snippets to decompose the formula:
computed the reference's y_h step by step, computed what y_h Claude's answer
would imply (via `y_h_implied = y_h_ref × sqrt(σ_claude/σ_ref)`), and found
the ratio was 1.090 — not a clean factor of 2 or π, so not a structural bug.

Then it checked the other input: the nucleon form factor. σ_SI goes as f_N²,
where f_N is the effective Higgs-nucleon coupling:

```
f_N = f_u + f_d + f_s + (2/9)(1 - f_u - f_d - f_s) = 0.2838
```

using the Hoferichter et al. (2017) values (f_u=0.0153, f_d=0.0191, f_s=0.0447).

Claude Code swept over candidate f_N values and found that f_N = 0.309 gives
a σ ratio of 1.186 — matching the observed 1.188 to three significant figures.
Without skills, the eval's Claude used f_N ≈ 0.309 (a common textbook
approximation). **The skill reference should have told it the right value, but
didn't.**

Claude Code checked the skill docs (`observables.md`) and confirmed: the table
listed the individual form factors (f_u, f_d, f_s) but didn't show how to
combine them into f_N, and didn't warn against the f_N ≈ 0.3 approximation.

**Fix**: Claude Code added the full f_N derivation formula to the skill
reference docs, with explicit values and a note: "Always use these exact values
— do not approximate f_N ≈ 0.3."

## Diagnosis 2: The coupling sign (the bug the skill found in us)

Next, Claude Code investigated `t2_dsu3_vector_bp1` — the task where skills
made things *worse*. Without skills, Claude got an exact match. With skills,
10.5% error.

Claude Code pulled the numbers: the ratio was 0.894. It checked our
`sigma_SI_vector()` reference function and found it used `f_N = 0.3` as a
hardcoded default parameter. The ratio (0.2838/0.300)² = 0.896 — matching the
discrepancy. So the eval's Claude *with skills* was using the correct Hoferichter
value (learned from the skill docs), and our reference function was using the
approximate one.

**The skill was making Claude more accurate. Our reference was the one with the bug.**

Claude Code fixed the default f_N in the reference and re-ran the task. It
*still* failed — now at 11.8% error, and 0/3 across multiple trials. So there
was a second, systematic issue.

Claude Code then ran the task one more time with full output capture (not just
the JSON answer but Claude's complete reasoning and formula). The eval's Claude
had included its formula in the JSON response:

```
A ∝ sin θ cos θ × (-1/m²_{H₁} + 1/m²_{H₂})
```

Our reference computed:

```
A ∝ sin θ cos θ × (+1/m²_{H₁} + 1/m²_{H₂})
```

Subtraction vs addition. A sign difference in the VV-H₁ coupling.

The user asked Claude Code to read the paper to settle it. Claude Code fetched
the PDF of arXiv:2506.19062, read pages 14-15, and found Equation 26 — the
first line of the Dark SU(3) Lagrangian:

```
L ⊃ (g̃ m_V / 2) (-sin θ H₁ + cos θ H₂) V^a_μ V^{μa}
```

The H₁ coupling has a **minus sign** from the scalar mixing rotation. This minus
sign is what makes the scalar blind spot work (Eq. 29) — for the scalar Ψ, the
H₁ and H₂ diagrams cancel exactly. For the vector V, they partially cancel.

Our `coupling_VV_Hi()` function was returning `+g̃² sin θ` for H₁. The paper says
it should be `-(g̃ m_V/2) sin θ`. Two bugs in one function: wrong sign and wrong
prefactor. Both came from a docstring that said "here we use the simplified form
from the paper's conventions" — but the simplification dropped the sign.

**The eval's Claude derived the coupling directly from the Lagrangian description
in the prompt and got it right. Our hand-written reference code had the wrong
sign from the start.**

The reason the no-skills run got an "exact match" on this task was a coincidence
of cancelling errors: wrong f_N (0.3 vs 0.2838) combined with wrong coupling sign
happened to produce the same number as our (also wrong) reference. Two wrongs
made a right — but only at one specific parameter point.

## What we fixed

| Component | Bug | Fix |
|-----------|-----|-----|
| Skill reference (`observables.md`) | Form factor table existed but didn't show f_N derivation | Added full formula: f_N = 0.0153 + 0.0191 + 0.0447 + (2/9)(0.9209) = 0.2838 |
| `coupling_VV_Hi()` | Sign: returned `+g² sin θ` for H₁ | Now returns `-(g̃ m_V/2) sin θ` per Eq. 26 |
| `coupling_VV_Hi()` | Prefactor: used `g̃²` | Now uses `g̃ m_V / 2` per Eq. 26 |
| `sigma_SI_vector()` | Default `f_N = 0.3` | Now derives f_N from Hoferichter form factors (0.2838) |

After fixes: reference runner 35/35, pytest suite 40/40 (39 pass + 1 tolerance fix).

### Postscript (2026-04-18)

The sign and form-factor bugs documented above are exactly the silent-error
class that the project's "augment don't replace" guiding principle aims to
prevent in agent production paths. They reinforce the case for two-track
separation —
reference implementations must be held to the same scrutiny as any other code,
which is easier when they live in `eval/<paper>/` as benchmark oracles rather
than being load-bearing inside a skill.

## Lessons

**1. The eval found bugs in the reference, not just in Claude.**

The Anthropic evals article warns about this: "CORE-Bench initially scored 42% on
Opus → 95% after fixing rigid grading, ambiguous specs, and stochastic tasks."
Our experience was the same — what looked like model failures were reference bugs.

**2. The A/B comparison (skills vs no-skills) was the diagnostic key.**

A task that passes without skills but fails with skills is a strong signal that
the reference is wrong — the skill is giving Claude better information, and the
"failure" is the reference not keeping up.

**3. Convention mismatches are the dominant failure mode for HEP calculations.**

Both bugs were convention issues:
- Which nucleon form factors to use (Hoferichter vs textbook approximation)
- Which sign convention for the scalar mixing rotation

The physics was correct on both sides. The formulas were algebraically equivalent.
But different numerical conventions produced different numbers. This is exactly
the kind of thing skills should standardize.

**4. Claude reads papers more carefully than we wrote the reference code.**

The minus sign in Eq. 26 is clearly visible in the Lagrangian. Our `coupling_VV_Hi`
function had a docstring that said "here we use the simplified form from the
paper's conventions" — but it didn't actually match the paper. Claude, given the
same paper reference, derived the coupling correctly. The eval caught the
disagreement, and tracing it back to the paper showed Claude was right.

## Appendix: numerical details

### f_N discrepancy

```
Our reference:  f_N = 0.2838 (Hoferichter et al. 2017)
Claude default: f_N ≈ 0.309  (common approximation)
Skill default:  f_N = 0.3    (was hardcoded in sigma_SI_vector)

(0.309/0.2838)² = 1.186  ← matches observed 18.8% error on sd_si_heavy
(0.2838/0.300)² = 0.895  ← matches observed 10.5% error on dsu3_vector_bp1
```

### Coupling sign discrepancy

```
Our reference:  A = g̃² sin θ cos θ (1/m²_{H₁} + 1/m²_{H₂})    [WRONG — addition]
Paper (Eq. 26): A = (g̃mV/2) sin θ cos θ (-1/m²_{H₁} + 1/m²_{H₂}) [RIGHT — subtraction]
Claude's code:  A = sin θ cos θ (-1/m²_{H₁} + 1/m²_{H₂})          [RIGHT — subtraction]
```

### Why the no-skills run got an "exact match" despite two bugs

At the bp1 benchmark (g̃=2, m_V=150, sin θ=0.1, m_H2=500):

```
Wrong f_N (0.3) × Wrong sign (addition):    1.024 × 10⁻⁴³ cm²
Correct f_N (0.2838) × Correct sign (sub):  matches Claude's output

The two errors partially cancelled at this specific parameter point.
At other parameter points (bp2, bp3), the cancellation was less precise
and both versions passed within 5% tolerance — the bugs were hiding.
```
