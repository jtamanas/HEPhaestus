# DESIGN-ITEM4-AMENDMENT6 — P3 inconclusive-by-confound; P3' protocol

Amends AMENDMENT5R1.md after the P3 leg (PR #37 draft, /tmp/item4-p3-handoff.md).
Accepted as measured: transcription adversarially verified with reproduced
Eq.-33 self-checks; scalar ratio ours/Hisano = −25.4 (MS=3 TeV) / −10.8
(10 TeV), sign DISAGREES; twist-2 sign agrees (kills a uniform M sign-flip);
our Re drops 2.35× between legs while Hisano's pure-doublet f_q is flat;
the legs were only ~6%/~2% singlet-admixed with TREE masses (loop spectrum
tachyonic at MS ≥ 3.5 TeV, y=1). Verdict on P3 as run: **NO VERDICT — the
comparison point was illegitimate** (our reading is a mixed-point object;
Hisano's is pure-doublet). Neither promotion nor the noise-scale FAIL fires.
The overall-i rescue is CLOSED (production 3-op Im/Re = 3.7e-8 — convention-
independent); the Im ≈ |Hisano| coincidence is the named transfer artifact.

## R1 — P3' protocol (pre-registered)

**Legs (serial kernel, SPheno LOOP-level spectrum MANDATORY — flag 55 on; a
tree fallback invalidates the leg, named refusal):**
- L1: MS = 3 TeV, y chosen so the measured singlet fraction of χ1 (from the
  SPheno mixing matrix, |N_singlet|²) is ~1e-2 — the SCALING leg.
- L2: MS = 3 TeV, y chosen for fraction < 1e-3 — decoupled leg A.
- L3: MS = 10 TeV, y chosen for fraction < 1e-3 — decoupled leg B. If loop
  spectrum is unreachable at 10 TeV for any y meeting the bar, substitute the
  largest MS that works with MS(L3) ≥ 2×MS(L2), documented.
Every leg's sidecar records: y, singlet fraction, χ1/χ2 masses and splitting,
loop-spectrum status. The y(MS) schedule is thereby OUTCOME-pinned (fraction
bars), not formula-pinned — the owner dials y per leg to hit the bars.

**Pre-registered bars:**
1. Decoupling diagnostic: |Re C_ours| drift L2→L3 < 25% (Hisano flat to 0.1%;
   allowance covers residual mixing + rank-2 budget). The P3-measured 2.35×
   must flatten; if it does not at fraction < 1e-3, the legs are not measuring
   a decoupled object — named refusal, no verdict.
2. PASS (promotion fires, +1.66e-10 → VALIDATED): scalar |C_ours/C_Hisano| ∈
   [0.2, 5] AND same sign at BOTH decoupled legs. Twist-2: sign must agree;
   magnitude reported under the O(3) O_Tq-bridge caveat, NOT a bar until the
   C^(1)/C^(2) split lands.
3. FAIL (assembly-level construction error CONFIRMED — Q3 already cleared the
   read-off): at fraction < 1e-3 with bar-1 met, sign still disagrees OR
   |ratio| outside [0.2, 5]. Consequence: a diagnose round on the
   FormCalc/DD-expansion chain, first target the SIGN (twist-2 sign agreeing
   while scalar disagrees points at a structure-specific slip, not a global
   convention).
4. Scaling diagnostic (L1 vs L2, same MS, fraction ×10): fit the excess
   component's exponent in fraction; ∈ [0.5, 2] (linear-to-quadratic in
   mixing) → the P3 mixed-point excess is mixing physics; excess moves < 2×
   while fraction moves 10× → assembly red flag corroborating FAIL.

## R2 — Status of the ~1e-10 reading, and what P3 did/did not show

UNVALIDATED, unchanged — P3's mixed-point numbers carry NO verdict weight on
it (Hisano's formula does not apply at 6% admixture; sign and magnitude there
are unadjudicable). Two observations REGISTERED, evidence-grade only:
(a) the 2.35× Re drift against a 3× fraction drop is consistent-with-LINEAR
in singlet fraction — the reading contains real, parameter-tracking content,
not pure noise; favorable to mixing-physics, settled by R1 bar 4;
(b) a large opposite-sign scalar coefficient at a strongly mixed point is not
physically absurd (singlet-exchange/interference content Hisano never
computes), so it is NOT an assembly red flag by itself. Discriminators are
pre-registered above: mixing-physics iff bar-4 scaling holds AND decoupled
legs pass; assembly error iff decoupled legs fail with bar 1 met.

## R3 — PR #37 MERGES as a validation record

Criteria: (1) body/STATUS state measured-facts-only with the illegitimate-
comparison finding and NO physics verdict; (2) AMENDMENT6 committed in-repo;
(3) suite green, protected files byte-identical; (4) fresh-reviewer sign-off
(the line-by-line transcription review counts; a delta review of the final
body suffices). The transcription + self-checks + durable p3_cours_raw.json
are assets P3' reuses — holding them in draft serves nothing.

## R4 — SD-COEFF-IMAGINARY absorbs the P3 lesson

Bar unchanged (|Im C|/|C| < 0.1 on the shipping instrument's reading; transfer
instrument exempt-by-name). ADDED, report-only: a "constant-Im riding
varying-Re" sidecar diagnostic — when Im is MORE stable across parameter legs
than Re (P3: Im 3.2→2.6e-12 vs Re 5.7→2.4e-11), flag artifact-signature. The
exemption design is hereby confirmed by an independent episode; codified.

## R5 — Sequencing

(1) R3-of-5R1 share re-measurement leg completes first (short, in flight);
(2) P3' immediately after — it holds the kernel until done (single decision
point; owner standing by); (3) the stayed kinematics retest runs only if the
share leg says the trigger still trips, and AFTER P3'; (4) per-flavor u/s
DEFERRED until P3' passes — measuring more flavors with an unvalidated
instrument is motion, not progress; (5) on P3' FAIL, the diagnose round
preempts everything. Sanctioned round-3 work item (from the P3 owner):
driver-side rotated-lineage output in eval_output.json so future legs need no
extraction probe — schedule after the P3' verdict, either branch.
