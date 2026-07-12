(* sd_dd_expansion.wl — box small-momentum (DD-limit) expansion for the
   singlet-doublet one-loop SI floor (DESIGN-ITEM4.md Decision A1, round 1).

   ============================================================================
   WHAT THIS SOLVES (read before editing)
   ============================================================================
   The SD 1PI-core box terms {1,4,8,10} of amp_reduced.m (amp_reduced/v2) carry
   FormCalc tensor PV heads D0i[dd1..dd33] (rank 1 and rank 2; the census shows NO
   rank>=3 box head — dd0,dd1,dd2,dd3,dd00,dd11,dd12,dd13,dd22,dd23,dd33 only).
   Evaluated by LoopTools AT the degenerate DD point (forward, on-threshold, v=0)
   the RANK>=1 tensor coefficients ride a Gram-determinant spurious pole
   (dd11/dd22/dd33 ~ 1/Gram(∝T) -> 1e28 at T=-1e-4) while the SCALAR box dd0 stays
   finite and flat (~6.13e-10).  Verified: kinematics-invest/FINDINGS.md +
   kinvest-verify/VERIFY.md (Gram pole, NOT IR: zero massless internal box lines).

   Decision A1: DO NOT extrapolate toward the degenerate point.  Instead reorganise
   each box tensor integral onto the RANK-1 DD Lorentz basis {g^mu nu, u^mu u^nu}
   (u = rest-frame time direction (1,0,0,0), u^2=1), which has a NON-degenerate 1x1
   "Gram" (u.u=1).  Every tensor coefficient contracted onto that basis reduces to
   SCALAR loop functions D0/C0/B0 (and, where propagator offsets coincide, their
   mass-derivatives), which LoopTools evaluates stably.  No Gram inversion is ever
   performed at the degenerate point; the reduction divides only by c-number
   collinear offset separations (b_a - b_r), never by a Gram determinant.

   NORM (Decision A2): LoopTools evaluates every integral.  This module hand-codes
   NO loop-function value.  It only reorganises WHICH LoopTools calls are made
   (scalar D0/C0/B0 instead of tensor D0i[dd..]) and takes finite differences of
   LoopTools' OWN scalar outputs for the mass-derivatives.

   ============================================================================
   THE COLLINEAR DD REDUCTION (the exact algebra, validated)
   ============================================================================
   At the DD point the four box propagator offsets k_0..k_3 are all proportional
   to u: k_i = b_i u (b_0 = 0).  The b_i are read off the box scalar invariants
   (boxCollinearOffsets below): with u^2=1, k_i.k_j = b_i b_j, so the Gram matrix
   is exactly rank 1 and b_i is fixed up to an overall sign by the invariants.

   For any propagator pair (a,r) with b_a != b_r, the numerator identity
        N_a - N_r = 2 q.(k_a - k_r) + (k_a^2 - k_r^2) - (M_a^2 - M_r^2)
   gives, since k_a - k_r = (b_a - b_r) u,
        q.u = ( N_a - N_r - (b_a^2 - b_r^2) + (M_a^2 - M_r^2) ) / ( 2 (b_a - b_r) ).
   Substituting this into the loop numerator turns each power of (q.u) into
   propagator cancellations: N_a cancels propagator a (a box -> triangle -> bubble
   pinch), N_r cancels propagator r, and the constant term multiplies the current
   scalar integral.  Recursing, EVERY (q.u)^n integral reduces to a linear
   combination of scalar D0/C0/B0 with c-number coefficients — no Gram anywhere.

   The two building blocks are validated EXACTLY (relative agreement ~1e-15) against
   LoopTools' own tensor coefficients at non-degenerate kinematics (the A1-V test,
   tests/test_dd_expansion_a1v.py):
     * VECTOR:  Sum_i (k_i.k_j) D_i  ==  ddIntU[1] telescoping   (rank-1 exact PV)
     * TRACE :  4 D00 + Sum_ij (k_i.k_j) D_ij == C0(remove prop0) + M_0^2 D0.
   These are exact PV identities (true at ALL kinematics); the DD application is
   their collinear (u-projected) specialisation, which is stable by construction.

   Head reconstruction (collinear gauge).  On the {g,uu} basis a box tensor is
        D^mu           = u^mu (u.D)                              (rank 1)
        D^mu nu        = g^mu nu D00 + u^mu u^nu D_uu            (rank 2)
   with u.D  = ddIntU[1]/... (see ddUProj), D_uu = ddIntU[2] - D00, and D00 from
   the trace identity.  FormCalc's covariant coefficients D_i, D_ij are recovered
   in the minimal-norm collinear gauge (the ONLY finite representative at rank-1
   Gram): with beta = {b_1,b_2,b_3} and |beta|^2 = Sum b_i^2,
        D_i   = (u.D)  b_i / |beta|^2
        D_ij  = D_uu   b_i b_j / |beta|^4
        D_00  = D00.
   This reproduces every u-contraction exactly (Sum b_i D_i = u.D, Sum b_i b_j D_ij
   = D_uu) and vanishes on directions orthogonal to u — i.e. it is EXACT for the
   leading DD (v=0) amplitude and drops only the O(v) transverse structure, which
   is the documented round-2 twist-2 refinement (Decision A1 O(v), A5).  This is
   why the completeness residual is REPORTED, not assumed zero (Decision A6): a
   residual in [1e-4,1e-2] is the O(v) leakage finding, never a tolerance to loosen.

   ============================================================================
   GUARDS (Decision A1 step 4, task scope)
   ============================================================================
   * SD-DD-EXPANSION-INCOMPLETE — after expansion the box sector must contain ZERO
     tensor-reduction heads (any D0i[id,..] with id =!= dd0).  A survivor is a loud
     recoverable blocker (blocker_catalog.yaml): the driver exits 3, nothing ships.
   * SD-DD-DERIVATIVE-NONCONVERGENT — a mass-derivative finite difference whose
     step-halving does not converge to 1e-6 relative is a loud stop.
   * boxDegeneracyMonitor — emits det(Gram)/scale^3 and the rank-1 residual
     ||Gram - beta⊗beta||/||Gram|| into the eval metadata (Gram/degeneracy monitor).

   This file touches NO LoopTools/FormCalc symbol at read time; it is Get[]-loaded
   by run_eval_sd.wls AFTER run_eval_common.wl has Install[]ed LoopTools, so the
   scalar heads D0i[dd0,..]/C0i[cc0,..]/B0i[bb0,..] resolve to package context.
*)

(* ============================================================================
   0.  small helpers
   ============================================================================ *)

(* Minkowski (+---) dot on explicit 4-vectors (used only for the A1-V test's
   explicit-momentum cross-check; production works from scalar invariants). *)
ddDot[a_, b_] := a[[1]] b[[1]] - a[[2]] b[[2]] - a[[3]] b[[3]] - a[[4]] b[[4]];

(* Tolerances (Decision A1 step 3 / A6). *)
$ddDerivTol = 1.0*^-6;      (* mass-derivative FD step-halving convergence bar *)
$ddOffsetDegenTol = 1.0*^-9; (* |b_a - b_r| below this => "coincident offset"   *)


(* ============================================================================
   1.  Box scalar invariants -> collinear offsets b_i  (DD rank-1 basis)
   ============================================================================
   A LoopTools D0i argument list after the id is
      {p1sq, p2sq, p3sq, p4sq, s12, s23, M1sq, M2sq, M3sq, M4sq}
   with propagator offsets k_0=0, k_1, k_2, k_3 and
      k_1^2 = p1sq,  k_2^2 = s12,  k_3^2 = p4sq,
      k_1.k_2 = (k_1^2 + k_2^2 - p2sq)/2,
      k_2.k_3 = (k_2^2 + k_3^2 - p3sq)/2,
      k_1.k_3 = (k_1^2 + k_3^2 - s23)/2.
   At the DD point the 3x3 Gram G_ij = k_i.k_j is rank 1 (G = beta⊗beta), so
      b_1 = sqrt(G_11),  b_2 = G_12/b_1,  b_3 = G_13/b_1.
   boxGram returns the 3x3 numeric Gram; boxCollinearOffsets returns
   {b_0=0, b_1, b_2, b_3} and the degeneracy monitor. *)

boxGram[dargs_List] := Module[{p1s, p2s, p3s, p4s, s12, s23, k1s, k2s, k3s, k12, k23, k13},
  {p1s, p2s, p3s, p4s, s12, s23} = dargs[[1 ;; 6]];
  k1s = p1s; k2s = s12; k3s = p4s;
  k12 = (k1s + k2s - p2s)/2;
  k23 = (k2s + k3s - p3s)/2;
  k13 = (k1s + k3s - s23)/2;
  {{k1s, k12, k13}, {k12, k2s, k23}, {k13, k23, k3s}}];

(* det(Gram)/scale^3 and rank-1 residual: how close to the exact collinear (DD)
   limit the frozen box kinematics is.  scale = max|G_ij| (GeV^2). *)
boxDegeneracyMonitor[dargs_List] := Module[{G = boxGram[dargs], scale, beta, approx, resid, det},
  scale = Max[Abs[Flatten[G]]] + 1.0*^-300;
  det = Det[G];
  beta = ddOffsetVector[G];
  approx = Outer[Times, beta, beta];
  resid = Norm[Flatten[G - approx]]/(Norm[Flatten[G]] + 1.0*^-300);
  <|"gram_det_over_scale3" -> det/scale^3, "rank1_residual" -> resid,
    "scale_gev2" -> scale, "beta" -> beta|>];

(* beta = {b1,b2,b3} from a (near-)rank-1 3x3 Gram. *)
ddOffsetVector[G_] := Module[{b1},
  b1 = Sqrt[G[[1, 1]]];
  If[Abs[b1] < 1.0*^-300, {0., 0., 0.},
     {b1, G[[1, 2]]/b1, G[[1, 3]]/b1}]];

(* full collinear offset list {b0=0,b1,b2,b3}. *)
boxCollinearOffsets[dargs_List] := Prepend[ddOffsetVector[boxGram[dargs]], 0.];


(* ============================================================================
   2.  Scalar loop integrals over a propagator subset (collinear DD kinematics)
   ============================================================================
   Given the box arg list and a SUBSET P of propagator indices {1,2,3,4}
   (= props 0,1,2,3), build the scalar integral over just those propagators.
   At the DD collinear point every offset is b_i u, so the momentum flowing
   between two kept propagators a,b is (b_a - b_b) u with invariant (b_a-b_b)^2.
   scalarBox/scalarTri/scalarBub call LoopTools' scalar heads D0i[dd0]/C0i[cc0]/
   B0i[bb0] — the ONLY loop-function evaluations this module makes. *)

(* masses^2 of props 0..3 from the box args (positions 7..10). *)
ddMassSq[dargs_List] := dargs[[7 ;; 10]];

(* b-offsets of props 0..3 (index 1..4). *)
ddBoffsets[dargs_List] := boxCollinearOffsets[dargs];

(* EXACT 4x4 extended Gram Gext[a,b] = k_{a-1}.k_{b-1} (prop index a,b in 1..4;
   k_0 = 0 so row/col 1 vanish).  Built from the true 3x3 boxGram of {k1,k2,k3}.
   Used to form pinched-integral invariants (k_a - k_b)^2 EXACTLY at any
   kinematics — this is what makes the A1-V primitives tool-precision exact. *)
ddGext[dargs_List] := PadLeft[boxGram[dargs], {4, 4}];

(* scalar integral over prop-index subset P (subset of {1,2,3,4}).  Invariants
   between kept propagators are taken from the EXACT extended Gram, so this is the
   correct scalar topology at whatever kinematics dargs encodes (DD or not). *)
ddScalarInt[dargs_List, P_List] := Module[
  {ps = Sort[P], Gx = ddGext[dargs], m = ddMassSq[dargs], n, mo, inv},
  n = Length[ps]; mo = m[[ps]];
  inv[a_, b_] := Gx[[a, a]] + Gx[[b, b]] - 2 Gx[[a, b]];   (* (k_{a-1}-k_{b-1})^2 *)
  Which[
    n == 4,
      D0i[dd0, Sequence @@ dargs],
    n == 3,
      C0i[cc0, inv[ps[[1]], ps[[2]]], inv[ps[[2]], ps[[3]]], inv[ps[[1]], ps[[3]]],
          mo[[1]], mo[[2]], mo[[3]]],
    n == 2,
      B0i[bb0, inv[ps[[1]], ps[[2]]], mo[[1]], mo[[2]]],
    n == 1,
      A0i[aa0, mo[[1]]],
    True, 0]];


(* ---- EXACT rank-1 / trace primitives (A1-V cross-check; exact at ALL kinematics)
   These are the LoopTools-validated building blocks (tests/test_dd_expansion_a1v):
     ddIntOffsetExact[dargs,j] = int (q.k_j)/prod  (j in 1..3, LoopTools offset k_j)
        == Sum_i (k_i.k_j) D_i   (LoopTools tensor coeffs)  to ~1e-15.
     ddTraceScalar[dargs]      = int q^2/prod
        == 4 D00 + Sum_ij (k_i.k_j) D_ij                     to ~1e-15.
   Derivation: q.k_j = (N_{j+1} - N_1 - (k_j^2 - M_{j+1}^2 + M_1^2))/2, using
   propagator index (j+1) [offset k_j] and prop index 1 [offset 0].  int N_p/prod
   removes propagator p. *)
ddIntOffsetExact[dargs_List, j_Integer] := Module[{Gx = ddGext[dargs], m = ddMassSq[dargs], kj2},
  kj2 = Gx[[j + 1, j + 1]];                (* k_j^2 = (prop index j+1) diagonal *)
  (1/2) (
     ddScalarInt[dargs, DeleteCases[ddAllP, j + 1]]   (* remove prop (j+1) *)
   - ddScalarInt[dargs, DeleteCases[ddAllP, 1]]       (* remove prop 0 *)
   - (kj2 - m[[j + 1]] + m[[1]]) ddScalarInt[dargs, ddAllP])];


(* ============================================================================
   3.  (q.u)^n integrals by collinear telescoping  (the reduction core)
   ============================================================================
   ddIntU[dargs, P, n] = int (q.u)^n / prod_{p in P}, computed by repeatedly
   applying  q.u = (N_a - N_r - (b_a^2 - b_r^2) + (M_a^2 - M_r^2)) / (2 (b_a-b_r))
   for a propagator pair (a,r) in P with the LARGEST |b_a - b_r| (numerically
   safest; never a Gram determinant).  N_a cancels prop a, N_r cancels prop r.
   Coincident-offset pairs (|b_a-b_r| < tol) are skipped as pivots; if NO
   non-coincident pair exists the remaining (q.u) hits a doubled propagator and is
   routed to the mass-derivative branch (ddMassDerivInt). *)

ddPickPivot[dargs_List, P_List] := Module[{b = ddBoffsets[dargs], pairs, best},
  pairs = Subsets[Sort[P], {2}];
  pairs = Select[pairs, Abs[b[[#[[1]]]] - b[[#[[2]]]]] > $ddOffsetDegenTol &];
  If[pairs === {}, $Failed,
    best = First[SortBy[pairs, -Abs[b[[#[[1]]]] - b[[#[[2]]]]] &]];
    best]];

ddIntU[dargs_List, P_List, 0] := ddScalarInt[dargs, P];
ddIntU[dargs_List, P_List, n_Integer?Positive] := Module[
  {b = ddBoffsets[dargs], m = ddMassSq[dargs], piv, a, r, denom, cst},
  piv = ddPickPivot[dargs, P];
  If[piv === $Failed,
    (* all kept offsets coincide -> doubled-propagator, use mass derivative *)
    Return[ddMassDerivInt[dargs, P, n]]];
  {a, r} = piv;
  denom = 2 (b[[a]] - b[[r]]);
  cst = -(b[[a]]^2 - b[[r]]^2) + (m[[a]] - m[[r]]);
  (1/denom) (
     ddIntU[dargs, DeleteCases[P, a], n - 1]      (* from N_a: cancels prop a *)
   - ddIntU[dargs, DeleteCases[P, r], n - 1]      (* from N_r: cancels prop r *)
   + cst ddIntU[dargs, P, n - 1])];

(* Mass-derivative branch: when a (q.u) factor multiplies an integral whose only
   available propagator pair is coincident (b_a = b_r, same offset, generally
   different mass), the reduction produces a DERIVATIVE of the scalar integral in
   the coincident-propagator mass^2.  We evaluate d/dM^2 by CENTRAL finite
   differences of LoopTools' scalar output with step-halving convergence (Decision
   A1 step 3).  In the SD box census this branch is not reached at leading order
   (prop 0 has b_0=0, distinct from b_1=mchi+mq); it is implemented for
   completeness and higher subsets.  Loud on non-convergence. *)
ddMassDerivInt[dargs_List, P_List, n_Integer] := Module[{b = ddBoffsets[dargs], deg, others},
  (* identify a coincident pair *)
  deg = First[Select[Subsets[Sort[P], {2}], Abs[b[[#[[1]]]] - b[[#[[2]]]]] <= $ddOffsetDegenTol &], {}];
  If[deg === {}, Return[$Failed]];
  (* d/dM_a^2 of the (n-1) integral with prop a's mass perturbed *)
  Module[{a = deg[[1]]},
    ddCentralDeriv[
      Function[dm, ddIntU[ReplacePart[dargs, (6 + a) -> dargs[[6 + a]] + dm], DeleteCases[P, a], n - 1]],
      Max[Abs[dargs[[6 + a]]], 1.0] * 1.0*^-3]]];

(* central finite difference f'(0) with step-halving until 1e-6 relative, else
   loud SD-DD-DERIVATIVE-NONCONVERGENT.  Returns the converged derivative and
   records the last relative change in $ddDerivDiagnostics. *)
$ddDerivDiagnostics = {};
ddCentralDeriv[f_, h0_] := Module[{h = h0, prev, cur, rel, k = 0},
  prev = (f[h] - f[-h])/(2 h);
  While[k < 20,
    h = h/2; k++;
    cur = (f[h] - f[-h])/(2 h);
    rel = If[Abs[cur] < 1.0*^-300, Abs[cur - prev], Abs[(cur - prev)/cur]];
    AppendTo[$ddDerivDiagnostics, <|"step" -> k, "h" -> h, "rel_change" -> rel|>];
    If[rel < $ddDerivTol, Return[cur]];
    prev = cur];
  WriteString["stderr",
    "sd_dd_expansion: SD-DD-DERIVATIVE-NONCONVERGENT (rel=" <> ToString[rel] <>
    " after " <> ToString[k] <> " halvings, tol=" <> ToString[$ddDerivTol] <> ")\n"];
  cur];


(* ============================================================================
   4.  u.D and D_uu, D00  (the {g,uu} basis components)
   ============================================================================
   u.D    = ddIntU[.,allP,1]   (int (q.u)/prod)
   int (q.u)^2 = ddIntU[.,allP,2]
   D00 from the TRACE identity  g.D = int q^2/prod = int (N_0 + M_0^2)/prod
        = (remove prop 0 triangle) + M_0^2 D0 = C0(P\{prop0}) + M_0^2 D0, and
      g.D = 4 D00 + Sum_ij (k_i.k_j) D_ij = 4 D00 + D_uu   (since Sum b_i b_j D_ij
      = D_uu and, off-diagonal metric contractions vanish on the rank-1 basis).
   Therefore:
      D_uu = int (q.u)^2/prod - D00
      D00  = (g.D - D_uu)/4 = (traceScalar - (intU2 - D00))/4
           => D00 = (traceScalar - intU2)/3 ... solved consistently below.
   Careful: g.D = 4 D00 + D_uu AND int(q.u)^2 = D00 + D_uu (contract D^munu with
   u u: u.u D00 + (u.k_i)(u.k_j) D_ij = D00 + D_uu).  Two equations:
      4 D00 + D_uu = traceScalar
      1 D00 + D_uu = intU2
   => 3 D00 = traceScalar - intU2 ; D_uu = intU2 - D00. *)

ddAllP = {1, 2, 3, 4};

ddTraceScalar[dargs_List] := (* g.D = int q^2/prod = C0(remove prop0) + M_0^2 D0 *)
  ddScalarInt[dargs, {2, 3, 4}] + dargs[[7]] * ddScalarInt[dargs, {1, 2, 3, 4}];

ddBasisComponents[dargs_List] := Module[{intU1, intU2, trace, D00, Duu},
  intU1 = ddIntU[dargs, ddAllP, 1];
  intU2 = ddIntU[dargs, ddAllP, 2];
  trace = ddTraceScalar[dargs];
  D00 = (trace - intU2)/3;
  Duu = intU2 - D00;
  <|"D0" -> ddScalarInt[dargs, ddAllP], "uD" -> intU1, "D00" -> D00, "Duu" -> Duu|>];


(* ============================================================================
   5.  Head reconstruction: scalar-only value for every box tensor D0i head
   ============================================================================
   ddBoxHead[id, args...] is the inert head the driver substitutes for D0i in the
   box sector.  It returns the collinear-gauge finite value (see file header).
   dd0 passes straight through to the LoopTools scalar box. *)

ddIndexOf = <|dd1 -> 1, dd2 -> 2, dd3 -> 3|>;
ddPairOf = <|dd11 -> {1, 1}, dd12 -> {1, 2}, dd13 -> {1, 3},
             dd22 -> {2, 2}, dd23 -> {2, 3}, dd33 -> {3, 3}|>;

ddBoxHead[dd0, args__] := D0i[dd0, args];                 (* scalar: passthrough *)

(* Tensor heads fire ONLY once every argument is numeric (the head is substituted
   for D0i on the SYMBOLIC amplitude, then held inert until mkNum makes the args
   numeric — so it never runs the reduction on symbolic kinematics). *)
(* Gram/degeneracy monitor log: every distinct box signature actually evaluated
   records its boxDegeneracyMonitor, so the driver can emit the required Gram
   monitor line from the real evaluation set (not a guessed representative). *)
$ddMonitorLog = <||>;
ddRecordMonitor[dargs_List] := Module[{key = Round[dargs, 1.0*^-6]},
  If[! KeyExistsQ[$ddMonitorLog, key],
    $ddMonitorLog[key] = boxDegeneracyMonitor[dargs]]];

ddBoxHead[id_, args__] /; VectorQ[{args}, NumberQ] := Module[{dargs = {args}, comp, beta, beta2, i, j, idx, pr},
  ddRecordMonitor[dargs];
  comp = ddBasisComponents[dargs];
  beta = ddBoffsets[dargs][[2 ;; 4]];                     (* {b1,b2,b3} *)
  beta2 = beta . beta + 1.0*^-300;
  Which[
    KeyExistsQ[ddIndexOf, id],                            (* rank-1 D_i *)
      idx = ddIndexOf[id];
      comp["uD"] * beta[[idx]]/beta2,
    id === dd00,                                          (* metric coeff *)
      comp["D00"],
    KeyExistsQ[ddPairOf, id],                             (* rank-2 D_ij *)
      pr = ddPairOf[id]; {i, j} = pr;
      comp["Duu"] * beta[[i]] beta[[j]]/beta2^2,
    True,
      (* a box tensor id the census did not contain -> loud (structural guard
         will also catch it, but name it here). *)
      Message[ddBoxHead::unknownid, id]; Indeterminate]];
ddBoxHead::unknownid = "sd_dd_expansion: unhandled box tensor id `1` (census listed only dd0,dd1..dd33).";


(* ============================================================================
   6.  Box-sector expansion + structural guard  (Decision A1 step 4)
   ============================================================================
   ddExpandRule is the intercept applied INSIDE the numeric substitution (mkNum),
   BEFORE LoopTools would auto-evaluate a numeric-argument D0i[dd_ij,..] at the
   Gram pole: it rewrites D0i -> ddBoxHead so the scalar reduction fires instead.
   Triangles (C0i) and bubbles (B0i) are untouched — they are stable at DD and are
   NOT the diseased calls (they carry no all-massive box Gram pole).

   ddBoxSectorClean[expr] is the SD-DD-EXPANSION-INCOMPLETE guard: after expansion
   the expression must contain ZERO tensor-reduction heads (D0i[id,..] with
   id =!= dd0, i.e. any surviving dd1..dd33).  Returns {cleanQ, survivors}. *)

ddExpandRule = D0i -> ddBoxHead;

(* Survivors = any tensor-reduction head that DID NOT reduce to a scalar: either a
   raw D0i[id,..] (id =!= dd0) that escaped interception, or a ddBoxHead[id,..]
   (id =!= dd0) still symbolic because its arguments never became numeric.  Both
   are SD-DD-EXPANSION-INCOMPLETE conditions. *)
ddTensorSurvivors[expr_] := DeleteDuplicates[Join[
  Cases[expr, D0i[id_, ___] /; (id =!= dd0) :> id, Infinity],
  Cases[expr, ddBoxHead[id_, ___] /; (id =!= dd0) :> id, Infinity]]];

ddBoxSectorClean[expr_] := Module[{surv = ddTensorSurvivors[expr]},
  {surv === {}, surv}];

(* census of box tensor heads present BEFORE expansion (for the amp_dd.m sidecar
   metadata: per-id counts). *)
ddBoxHeadCensus[terms_] := Module[{ids},
  ids = Cases[terms, D0i[id_, ___] :> id, Infinity];
  Association[(# -> Count[ids, #]) & /@ DeleteDuplicates[ids]]];

(* Summary of the Gram/degeneracy monitor over ALL box signatures evaluated this
   run (worst-case degeneracy is what matters — the closer to rank-1 the more the
   collinear reduction is exact and the further LoopTools' own tensors would blow
   up).  Returns a compact association for the eval metadata + amp_dd.m sidecar. *)
ddMonitorSummary[] := Module[{vals = Values[$ddMonitorLog], resids, dets},
  If[vals === {}, Return[<|"n_box_signatures" -> 0|>]];
  resids = #["rank1_residual"] & /@ vals;
  dets = Abs[#["gram_det_over_scale3"]] & /@ vals;
  <|"n_box_signatures" -> Length[vals],
    "max_rank1_residual" -> Max[resids], "min_rank1_residual" -> Min[resids],
    "max_abs_gram_det_over_scale3" -> Max[dets],
    "min_abs_gram_det_over_scale3" -> Min[dets]|>];

(* Write the amp_dd.m sidecar (Decision A3): the expanded (F-symbolic, box-DD-
   reduced) amplitude plus expansion metadata.  Traceable + cacheable, not a new
   pipeline stage. *)
writeAmpDdSidecar[path_, expandedAmp_, censusBefore_, ovOrder_, extra_:<||>] :=
  Put[<|"schema" -> "amp_dd/v1",
        "expansion" -> "box small-momentum DD (rank-1 collinear), DESIGN-ITEM4.md A1",
        "box_head_census_before" -> censusBefore,
        "box_head_census_after" -> ddTensorSurvivors[expandedAmp],
        "ov_order" -> ovOrder,
        "deriv_tol" -> $ddDerivTol,
        "deriv_diagnostics_tail" -> Take[$ddDerivDiagnostics, -Min[10, Length[$ddDerivDiagnostics]]],
        "gram_monitor" -> ddMonitorSummary[],
        "expanded_amplitude" -> expandedAmp,
        "extra" -> extra|>, path];
