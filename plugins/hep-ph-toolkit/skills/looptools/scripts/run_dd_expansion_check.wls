#!/usr/bin/env wolframscript
(* run_dd_expansion_check.wls — gated cross-check runner for the box DD-expansion
   (sd_dd_expansion.wl).  Drives the A1-V head-level validation (DESIGN-ITEM4.md
   Decision A1-V) + the DD-point finiteness demonstration, and emits a JSON the
   pytest (tests/test_dd_expansion_a1v.py) asserts against.  Needs LoopTools
   MathLink (HEPPH_RUN_WOLFRAM_TESTS gate on the pytest side).

   Usage:  wolframscript -script run_dd_expansion_check.wls <out.json> <looptools_prefix>

   A1-V (exact PV identities, true at ALL kinematics -> tool-precision agreement):
     * VECTOR : ddIntOffsetExact[da,j]  == Sum_i (k_i.k_j) D_i          (LoopTools)
     * TRACE  : ddTraceScalar[da]       == 4 D00 + Sum_ij (k_i.k_j) D_ij (LoopTools)
   checked at 3 NON-degenerate box kinematics (Gram = O(1)); 1e-6 relative bar.

   DD finiteness (the payoff): at the degenerate DD point the collinear reduction
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

(* ---- A1-V: exact identities at 3 non-degenerate boxes ---------------------- *)
(* three explicit-momentum boxes with distinct scales (Gram O(1), non-collinear) *)
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

(* ---- DD finiteness at the SD chi+/W/W box signature ------------------------- *)
mchi = 132.69; mq = 4.67*^-3; mChiM = 200.0; mW = 80.4; mFu = 2.16*^-3;
ddSig = {(mchi + mq)^2, mq^2, -1.0*^-4, mchi^2, mchi^2, mq^2, mChiM^2, mFu^2, mW^2, mW^2};
ltDD11 = D0i[dd11, Sequence @@ ddSig];
ddDD11 = ddBoxHead[dd11, Sequence @@ ddSig];
mon = boxDegeneracyMonitor[ddSig];

toNum[x_] := N[Re[x]];
result = <|
  "a1v_reldiffs" -> a1vReldiffs,
  "a1v_max_reldiff" -> a1vMax,
  "a1v_ok" -> (a1vMax < 1.0*^-6),
  "dd_finite_box_dd11_re" -> toNum[ddDD11],
  "dd_finite_box_dd11_abs" -> N[Abs[ddDD11]],
  "lt_gram_poled_dd11_abs" -> N[Abs[ltDD11]],
  "dd_over_lt_ratio" -> N[Abs[ddDD11]/Abs[ltDD11]],
  "dd_box_dd11_finite" -> (NumberQ[ddDD11] && Abs[ddDD11] < 1.0),
  "gram_det_over_scale3" -> toNum[mon["gram_det_over_scale3"]],
  "rank1_residual" -> N[mon["rank1_residual"]]
|>;

Export[$out, result, "RawJSON"];
Print["run_dd_expansion_check: a1v_max_reldiff=", a1vMax,
      " dd_box_dd11_abs=", N[Abs[ddDD11]], " lt_dd11_abs=", N[Abs[ltDD11]]];
Quiet[Check[ltexi[], Null]];
Exit[0]
