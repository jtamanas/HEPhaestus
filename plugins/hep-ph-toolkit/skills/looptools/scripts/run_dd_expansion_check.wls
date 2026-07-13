#!/usr/bin/env wolframscript
(* run_dd_expansion_check.wls — gated cross-check runner for the box DD-expansion
   (sd_dd_expansion.wl).  Emits a JSON the pytest (tests/test_dd_expansion_a1v.py)
   asserts against.  Needs LoopTools MathLink (HEPPH_RUN_WOLFRAM_TESTS gate on the
   pytest side).

   Usage:  wolframscript -script run_dd_expansion_check.wls <out.json> <looptools_prefix>

   THREE sections (PR #35 review F2 / DESIGN-ITEM4-AMENDMENT.md stage-0c):

   1. EXACT PRIMITIVES (validation-side; true at ALL kinematics):
        ddIntOffsetExact[da,j] == Sum_i (k_i.k_j) D_i^LT   (exact PV vector)
        ddTraceScalar[da]      == 4 D00^LT + Sum (k.k) D_ij^LT (exact PV trace)
      at 3 NON-degenerate box kinematics (Gram O(1)); 1e-6 bar.  NOTE:
      ddIntOffsetExact is NOT called by the production path — this section
      certifies ddScalarInt (shared with production) + the numerator machinery.

   2. PRODUCTION PATH, CONTRACTED LEVEL (the amendment-0c prescription): the
      telescoper ddIntU and the ddBasisComponents that feed ddBoxHead, compared
      against LoopTools' OWN tensor u-contractions
        u1LT  = Sum_i b_i D_i^LT
        u2LT  = D00^LT + Sum_ij b_i b_j D_ij^LT      (b = collinear offsets)
        D00LT
      at 3 points along the physical SD chi+-/W/W signature's non-zero-Gram
      T-path (T = -100, -10, -1; rank-1 Gram residual ~1.3e-3 .. 1.3e-5):
        * rank-1: MACHINE-PRECISION agreement at every point (the 1e-6 bar met
          literally — the collinear numerator identity is exact for the
          longitudinal component at all T);
        * rank-2: the deviation must FALL toward the DD point with the budget
          power laws (u2: O(sqrt|T|), D00: O(|T|)) — fitted log-log slopes;
        * extrapolated reference: LT contractions on T = -2..-0.125 polynomial-
          extrapolated to T=0, vs the PRODUCTION values at T = -TEPS.  Budget:
          u2/Duu <= 1e-2 (collinear leakage O(sqrt TEPS) ~ 3e-3 + extrapolation
          + cancellation loss), D00 <= 1e-3, rank-1 <= 1e-6.

   3. DD FINITENESS (the payoff): at the degenerate DD point the reduction
      ddBoxHead[dd11,..] stays finite while LoopTools' own D0i[dd11,..] rides the
      Gram pole (~1/T).  Report both + the ratio + the Gram monitor.
*)

Off[General::shdw]; Off[General::stop]; Off[General::infy]; Off[Power::infy];

If[Length[$ScriptCommandLine] < 3,
  WriteString["stderr", "run_dd_expansion_check: usage <out.json> <looptools_prefix>\n"];
  Exit[1]];
$out = $ScriptCommandLine[[2]];
$ltPrefix = $ScriptCommandLine[[3]];

Needs["FormCalc`"];
$ltBin = FileNameJoin[{$ltPrefix, "bin", "LoopTools"}];
If[Install[$ltBin] === $Failed,
  WriteString["stderr", "run_dd_expansion_check: Install[LoopTools] failed\n"]; Exit[1]];
Quiet[Check[ltini[], Null]];

$scriptDir = DirectoryName[
  If[$InputFileName =!= "" && $InputFileName =!= Null, $InputFileName, $ScriptCommandLine[[1]]]];
Get[FileNameJoin[{$scriptDir, "sd_dd_expansion.wl"}]];

dot[a_, b_] := a[[1]] b[[1]] - a[[2]] b[[2]] - a[[3]] b[[3]] - a[[4]] b[[4]];

(* ============================ section 1: exact primitives ==================== *)
boxes = {
  {{5.0, 0.3, 0.1, 0.2}, {4.0, -0.2, 0.4, 0.1}, {-4.5, 0.1, -0.3, 0.25}, {2.0, 3.0, 4.0, 3.5}},
  {{9.0, 1.1, -0.7, 0.5}, {6.0, -0.9, 1.3, 0.2}, {-7.0, 0.4, -1.1, 0.8}, {1.5, 2.5, 3.0, 2.2}},
  {{14.0, 2.2, 1.4, -1.0}, {10.0, -1.6, 2.1, 1.2}, {-11.0, 0.9, -1.7, 0.6}, {3.0, 5.0, 6.0, 4.0}}};

checkOne[bx_] := Module[{p1, p2, p3, p4, mm, da, kk, d, Di, Dijf, Gt, vec, trace, tLT},
  {p1, p2, p3, mm} = bx; p4 = -(p1 + p2 + p3);
  da = {dot[p1, p1], dot[p2, p2], dot[p3, p3], dot[p4, p4], dot[p1 + p2, p1 + p2],
        dot[p2 + p3, p2 + p3], mm[[1]]^2, mm[[2]]^2, mm[[3]]^2, mm[[4]]^2};
  kk = {p1, p1 + p2, p1 + p2 + p3};
  d[id_] := D0i[id, Sequence @@ da];
  Di = {d[dd1], d[dd2], d[dd3]};
  Dijf[i_, j_] := Switch[Sort[{i, j}], {1, 1}, d[dd11], {1, 2}, d[dd12], {1, 3}, d[dd13],
     {2, 2}, d[dd22], {2, 3}, d[dd23], {3, 3}, d[dd33]];
  Gt = Table[dot[kk[[i]], kk[[j]]], {i, 3}, {j, 3}];
  vec = Table[
    Module[{lt = Sum[Gt[[j, i]] Di[[i]], {i, 3}]},
      Abs[(ddIntOffsetExact[da, j] - lt)/lt]], {j, 3}];
  tLT = 4 d[dd00] + Sum[Gt[[i, j]] Dijf[i, j], {i, 3}, {j, 3}];
  trace = Abs[(ddTraceScalar[da] - tLT)/tLT];
  Max[Append[vec, trace]]];

a1vReldiffs = checkOne /@ boxes;
a1vMax = Max[a1vReldiffs];

(* ================= section 2: production path, contracted level ============== *)
mchi = 132.69; mq = 4.67*^-3; mChiM = 200.0; mW = 80.4; mFu = 2.16*^-3;
TEPS = 1.0*^-4;
mk[T_] := {(mchi + mq)^2, mq^2, T, mchi^2, mchi^2, mq^2, mChiM^2, mFu^2, mW^2, mW^2};

(* LoopTools u-contractions of the box tensors (b = collinear offsets of dargs) *)
uLT[da_] := Module[{b = ddBoffsets[da][[2 ;; 4]], Di, Dij, D00v},
  Di = {D0i[dd1, Sequence @@ da], D0i[dd2, Sequence @@ da], D0i[dd3, Sequence @@ da]};
  D00v = D0i[dd00, Sequence @@ da];
  Dij = Table[D0i[{{dd11, dd12, dd13}, {dd12, dd22, dd23}, {dd13, dd23, dd33}}[[i, j]],
    Sequence @@ da], {i, 3}, {j, 3}];
  <|"u1" -> Sum[b[[i]] Di[[i]], {i, 3}],
    "u2" -> D00v + Sum[b[[i]] b[[j]] Dij[[i, j]], {i, 3}, {j, 3}],
    "D00" -> D00v|>];

(* production values at kinematics da (ddBasisComponents feeds ddBoxHead) *)
uProd[da_] := Module[{c = ddBasisComponents[da]},
  <|"u1" -> c["uD"], "u2" -> c["D00"] + c["Duu"], "D00" -> c["D00"],
    "Duu" -> c["Duu"], "D0" -> c["D0"]|>];

(* --- 2a: same-T comparison at the 3 non-zero-Gram points -------------------- *)
prodTs = {-100., -10., -1.};
sameT = Table[Module[{da = mk[T], lt, pr, mon},
   lt = uLT[da]; pr = uProd[da]; mon = boxDegeneracyMonitor[da];
   <|"T" -> T, "rank1_residual" -> N[mon["rank1_residual"]],
     "u1_rel" -> N[Abs[(pr["u1"] - lt["u1"])/lt["u1"]]],
     "u2_rel" -> N[Abs[(pr["u2"] - lt["u2"])/lt["u2"]]],
     "D00_rel" -> N[Abs[(pr["D00"] - lt["D00"])/lt["D00"]]]|>], {T, prodTs}];

u1MaxRel = Max[#["u1_rel"] & /@ sameT];

(* fitted log-log convergence slopes (deviation ~ |T|^p): budget p~0.5 (u2), ~1 (D00) *)
u2Slope  = Coefficient[Fit[{Log[Abs[#["T"]]], Log[#["u2_rel"]]} & /@ sameT, {1, x}, x], x];
d00Slope = Coefficient[Fit[{Log[Abs[#["T"]]], Log[#["D00_rel"]]} & /@ sameT, {1, x}, x], x];

(* --- 2b: extrapolated T->0 LoopTools reference vs PRODUCTION at T=-TEPS ------
   Extrapolation toward the degenerate point is SANCTIONED here per Decision A1:
   option (b) was rejected as the production path and demoted "to a per-head
   validation role (A1-V)" — this is that role.  The CONTRACTED LT values are
   finite and smooth in T (the 1/Gram cancels in the contraction), unlike the
   individual tensor components. *)
extrapTs = {-2., -1., -0.5, -0.25, -0.125};
ltSeq = uLT[mk[#]] & /@ extrapTs;
extrap[key_] := Module[{f},
  f = InterpolatingPolynomial[Transpose[{extrapTs, (#[key] &) /@ ltSeq}], tvar];
  f /. tvar -> 0.];
u1Ref = extrap["u1"]; u2Ref = extrap["u2"]; d00Ref = extrap["D00"];

prodAtTeps = uProd[mk[-TEPS]];
u1ExtrapRel  = N[Abs[(prodAtTeps["u1"] - u1Ref)/u1Ref]];
u2ExtrapRel  = N[Abs[(prodAtTeps["u2"] - u2Ref)/u2Ref]];
d00ExtrapRel = N[Abs[(prodAtTeps["D00"] - d00Ref)/d00Ref]];
duuExtrapRel = N[Abs[(prodAtTeps["Duu"] - (u2Ref - d00Ref))/(u2Ref - d00Ref)]];

(* ==================== section 3: DD finiteness (the payoff) ================== *)
ddSig = mk[-TEPS];
ltDD11 = D0i[dd11, Sequence @@ ddSig];
ddDD11 = ddBoxHead[dd11, Sequence @@ ddSig];
mon = boxDegeneracyMonitor[ddSig];

toNum[x_] := N[Re[x]];
result = <|
  (* section 1 *)
  "a1v_reldiffs" -> a1vReldiffs,
  "a1v_max_reldiff" -> a1vMax,
  "a1v_ok" -> (a1vMax < 1.0*^-6),
  (* section 2a *)
  "prod_sameT" -> sameT,
  "prod_u1_max_rel" -> N[u1MaxRel],
  "prod_u2_conv_slope" -> N[u2Slope],
  "prod_d00_conv_slope" -> N[d00Slope],
  (* section 2b *)
  "prod_u1_extrap_rel" -> u1ExtrapRel,
  "prod_u2_extrap_rel" -> u2ExtrapRel,
  "prod_d00_extrap_rel" -> d00ExtrapRel,
  "prod_duu_extrap_rel" -> duuExtrapRel,
  (* section 3 *)
  "dd_finite_box_dd11_re" -> toNum[ddDD11],
  "dd_finite_box_dd11_abs" -> N[Abs[ddDD11]],
  "lt_gram_poled_dd11_abs" -> N[Abs[ltDD11]],
  "dd_over_lt_ratio" -> N[Abs[ddDD11]/Abs[ltDD11]],
  "dd_box_dd11_finite" -> (NumberQ[ddDD11] && Abs[ddDD11] < 1.0),
  "gram_det_over_scale3" -> toNum[mon["gram_det_over_scale3"]],
  "rank1_residual" -> N[mon["rank1_residual"]]
|>;

Export[$out, result, "RawJSON"];
Print["run_dd_expansion_check: a1v_max=", a1vMax,
      " | prod u1_max=", N[u1MaxRel], " u2_slope=", N[u2Slope], " d00_slope=", N[d00Slope],
      " | extrap u1=", u1ExtrapRel, " u2=", u2ExtrapRel, " D00=", d00ExtrapRel,
      " duu=", duuExtrapRel,
      " | dd11 ", N[Abs[ddDD11]], " vs LT ", N[Abs[ltDD11]]];
Quiet[Check[ltexi[], Null]];
Exit[0]
