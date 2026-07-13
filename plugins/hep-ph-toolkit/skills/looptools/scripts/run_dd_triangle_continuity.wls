#!/usr/bin/env wolframscript
(* run_dd_triangle_continuity.wls — triangle-continuity fixture (PR #35 review
   F3) + rotated-complete sector fits (AMENDMENT probe 3, re-read per
   DESIGN-ITEM4-AMENDMENT2.md).

   TRIANGLE CONTINUITY (F3): the box DD expansion touches ONLY D0i heads, so the
   triangle/bubble sector must reproduce the item-3 baseline C_scalar exactly.
   This runner rebuilds the TRIANGLE-ONLY amplitude — the terms whose fully
   resolved bodies are free of D0i, computed cheaply via the transitive closure
   of Sub#### definitions that (directly or through other Subs) contain a D0i —
   evaluates it with the CANONICAL binding pattern (identical to
   run_eval_sd.wls: same mkNum, same external pins, setdelta 0 / setmudim 1),
   projects it, and writes the FULL-PRECISION C_scalar as the pinned fixture.

   PROBE 3 (amendment Ruling 4, RECONCILED per AMENDMENT2/RF-minor-2): if an
   amp_dd.m sidecar (the cured FULL amplitude from the canonical run) is
   supplied, also fit the ROTATED-COMPLETE reference instrument to (a) the
   full amplitude, (b) the triangle-only sector, (c) the expanded-box-only
   sector (full - triangle, exact by F-linearity), reporting for each: the
   instrument completeness residual, named absorbing operators (norm shares),
   and the 3-op-vs-full C_scalar shift.  HISTORY: the earlier version of this
   note mapped "< 1e-8 supports frozen-kinematics" — that mapping was inverted
   nonsense and is RETRACTED (pr35-rereview/REVIEW.md): the historical 0.669
   residual was an instrument artifact (rank-12 basis + unrotated
   Majorana-crossed monomials), no physics meaning.  The v -> v/10 leg is
   attempted and reported; the transfer-sampled instrument is measured to
   refuse ILLCONDITIONED at v/10 (cond ~ 1/v^2), which is recorded as a named
   outcome, not a runner failure — the fixture is this runner's primary job.

   Usage (positional contract shared with run_eval_sd.wls via run_eval_common.wl):
     wolframscript -script run_dd_triangle_continuity.wls \
       <amp_reduced.m> <point.json> <ff_preset(ignored)> <out.json> <lt_prefix> \
       [amp_dd.m] [amp_tri_out.m]

   amp_tri_out.m (optional): Put[] destination for the evaluated triangle-only
   amplitude (F-symbolic, numeric coefficients) so later probes need no kernel
   re-evaluation.  Serial Wolfram discipline: ONE kernel, everything in one leg.
*)

(* ---- model constants: MUST match run_eval_sd.wls verbatim ------------------- *)
mUlight = 2.16*^-3; mDlight = 4.67*^-3; mSlight = 0.093;
mClight = 1.27;     mBlight = 4.18;     mTlight = 173.4;
TEPS = 1.0*^-4;

$scriptDir = DirectoryName[
  If[$InputFileName =!= "" && $InputFileName =!= Null, $InputFileName,
     $ScriptCommandLine[[1]]]];
Get[FileNameJoin[{$scriptDir, "run_eval_common.wl"}]];
Get[FileNameJoin[{$scriptDir, "sd_projection.wl"}]];
Get[FileNameJoin[{$scriptDir, "sd_dd_expansion.wl"}]];

$ampDdPath  = If[Length[$ScriptCommandLine] >= 7, $ScriptCommandLine[[7]], None];
$triOutPath = If[Length[$ScriptCommandLine] >= 8, $ScriptCommandLine[[8]], None];

(* full-precision serialization: RawJSON shortens reals; the fixture must
   round-trip exactly, so every headline number also ships as InputForm text *)
fp[x_] := ToString[x, InputForm];

Module[{
    ampPath = $ampPath, pointPath = $pointPath, outPath = $outPath,
    point, masses, params, getMass, getParam, getParamAny,
    mchi1, mchi2, mchi3, mchiM, mh, mZ, mW, mchi, mq,
    ZNm, UMm, UPm, ZDLm, ZDRm, ZULm, ZURm, Yum, Ydm,
    yh1v, yh2v, g1v, g2v, g3v, Lamv, PhaseFSv, vvSMv, ctw, stw,
    amp, subexpr, ampBody, abbr, abbrF, terms, mkNum, extIdx, extPins,
    subSymOf, boxySyms, changed, triQ, triTerms, nBoxTerms,
    Mtri, projTri, sector, jsonAssoc,
    MnumFull, Mbox, projFull, projFullV, projBox, vDrift = Null
  },

  point = Quiet[Check[Import[pointPath, "RawJSON"], $Failed]];
  If[point === $Failed,
    WriteString["stderr", "run_dd_triangle_continuity: could not read point.json\n"]; Exit[1]];
  masses = point["masses"]; params = point["params"];
  mchi = point["m_dm_gev"];
  getMass[pdg_] := masses[ToString[pdg]];
  getParam[k_]  := Lookup[params, k, $Failed];
  getParamAny[ks_List] := Module[{hit},
    hit = SelectFirst[ks, (Lookup[params, #, $Failed] =!= $Failed) &, $Failed];
    If[hit === $Failed, $Failed, Lookup[params, hit, $Failed]]];

  mchi1 = getMass[9958431]; mchi2 = getMass[9956206]; mchi3 = getMass[9979223];
  mchiM = getMass[9984071];
  mh = getMass[25]; mZ = getMass[23]; mW = getMass[24];
  mchi = If[NumberQ[mchi1], mchi1, mchi];
  mq   = mDlight;

  ZNm = Table[getParam["ZNMIX:" <> ToString[i] <> "," <> ToString[j]]
              + I*Lookup[params, "IMZNMIX:" <> ToString[i] <> "," <> ToString[j], 0.],
              {i, 3}, {j, 3}];
  UMm = Table[getParam["UMMIX:" <> ToString[i] <> "," <> ToString[j]], {i, 1}, {j, 1}];
  UPm = Table[getParam["UPMIX:" <> ToString[i] <> "," <> ToString[j]], {i, 1}, {j, 1}];
  ZDLm = Table[getParam["UDLMIX:" <> ToString[i] <> "," <> ToString[j]], {i, 3}, {j, 3}];
  ZDRm = Table[getParam["UDRMIX:" <> ToString[i] <> "," <> ToString[j]], {i, 3}, {j, 3}];
  ZULm = Table[getParam["UULMIX:" <> ToString[i] <> "," <> ToString[j]], {i, 3}, {j, 3}];
  ZURm = Table[getParam["UURMIX:" <> ToString[i] <> "," <> ToString[j]], {i, 3}, {j, 3}];
  Yum = Table[getParam["YU:" <> ToString[i] <> "," <> ToString[j]], {i, 3}, {j, 3}];
  Ydm = Table[getParam["YD:" <> ToString[i] <> "," <> ToString[j]], {i, 3}, {j, 3}];
  yh1v = getParamAny[{"BSMPARAMS:3", "MINPAR:3"}];
  yh2v = getParamAny[{"BSMPARAMS:4", "MINPAR:4"}];
  g1v = getParam["GAUGE:1"]; g2v = getParam["GAUGE:2"]; g3v = getParam["GAUGE:3"];
  Lamv = getParam["SM:2"]; PhaseFSv = getParam["PHASES:1"]; vvSMv = getParam["HMIX:3"];
  ctw = mW/mZ; stw = Sqrt[1 - ctw^2];

  amp = Quiet[Check[Get[ampPath], $Failed]];
  If[amp === $Failed,
    WriteString["stderr", "run_dd_triangle_continuity: Get[amp_reduced.m] failed\n"]; Exit[1]];
  subexpr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "subexpr"], "subexpr" /. amp, {}];
  ampBody = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "amp"], "amp" /. amp, amp];
  abbr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "abbr"], "abbr" /. amp, {}];
  abbrF = Cases[abbr, HoldPattern[_ -> _WeylChain]];
  If[abbrF === {},
    WriteString["stderr", "run_dd_triangle_continuity: no Abbr[] WeylChain table\n"]; Exit[3]];
  terms = List @@ ampBody;

  mkNum[delta_, mudim_] := (
    setdelta[delta]; setmudim[mudim];
    {Den[a_, b_] :> 1/(a - b),
     MassFChi[i_] :> {mchi1, mchi2, mchi3}[[i]], MassFChiM -> mchiM,
     Masshh -> mh, MassAh -> mZ, MassHp -> mW, MassVWp -> mW, MassVZ -> mZ,
     MassFu[i_] :> {mUlight, mClight, mTlight}[[i]],
     MassFd[i_] :> {mDlight, mSlight, mBlight}[[i]],
     ZN[i_, j_] :> ZNm[[i, j]], UM[i_, j_] :> UMm[[i, j]], UP[i_, j_] :> UPm[[i, j]],
     ZDL[i_, j_] :> ZDLm[[i, j]], ZDR[i_, j_] :> ZDRm[[i, j]],
     ZUL[i_, j_] :> ZULm[[i, j]], ZUR[i_, j_] :> ZURm[[i, j]],
     Yu[i_, j_] :> Yum[[i, j]], Yd[i_, j_] :> Ydm[[i, j]],
     yh1 -> yh1v, yh2 -> yh2v, g1 -> g1v, g2 -> g2v, g3 -> g3v, Lam -> Lamv,
     PhaseFS -> PhaseFSv, vvSM -> vvSMv, CTW -> ctw, STW -> stw,
     Finite -> 1, Mat[_] -> 1,
     T -> -TEPS, S -> (mchi + mq)^2, U -> (mchi - mq)^2});

  extIdx = DeleteDuplicates[Cases[terms, SumOver[i_, _, External] :> i, Infinity]];
  extPins = Join[{SumOver[_, _, External] -> 1}, (# -> 1) & /@ extIdx];

  (* ---- triangle-only split: transitive closure of D0i-carrying Subs ----------
     A term's RESOLVED body contains a D0i iff the raw term contains D0i directly
     or references (at any depth) a Sub whose definition transitively does —
     substitution is pure structural replacement, so no D0i can appear or vanish
     any other way.  This gives the exact resolved-level split without paying the
     full `//. subexpr` resolution twice. *)
  subSymOf[lhs_] := If[AtomQ[lhs], lhs, Head[lhs]];
  boxySyms = {}; changed = True;
  While[changed, changed = False;
    Do[Module[{s = subSymOf[r[[1]]], rhs = r[[2]]},
        If[! MemberQ[boxySyms, s] &&
           (! FreeQ[rhs, D0i] || AnyTrue[boxySyms, ! FreeQ[rhs, #] &]),
          AppendTo[boxySyms, s]; changed = True]],
      {r, subexpr}]];
  triQ[t_] := FreeQ[t, D0i] && AllTrue[boxySyms, FreeQ[t, #] &];
  triTerms = Select[terms, triQ];
  nBoxTerms = Length[terms] - Length[triTerms];
  WriteString["stderr",
    "run_dd_triangle_continuity: terms=" <> ToString[Length[terms]] <>
    " triangle-only=" <> ToString[Length[triTerms]] <>
    " box-carrying=" <> ToString[nBoxTerms] <>
    " boxy_subs=" <> ToString[Length[boxySyms]] <> "\n"];
  If[triTerms === {} || nBoxTerms === 0,
    WriteString["stderr",
      "run_dd_triangle_continuity: degenerate split (one sector empty) — the\n" <>
      "  fixture would be vacuous; refusing to write one.\n"];
    Exit[3]];

  (* ---- canonical evaluation of the triangle-only sector ---------------------- *)
  Mtri = Total[Table[
    evalTermCommon[triTerms[[k]], subexpr, {}, mkNum[0, 1], extPins],
    {k, Length[triTerms]}]];
  If[Length[residualSymbols[Mtri]] > 0,
    WriteString["stderr", "run_dd_triangle_continuity: non-numeric triangle amp: " <>
      ToString[Take[ToString /@ residualSymbols[Mtri], UpTo[20]], InputForm] <> "\n"];
    Exit[3]];
  If[$triOutPath =!= None,
    Put[<|"schema" -> "amp_tri/v1",
          "sector" -> "triangle-only (terms with D0i-free resolved bodies)",
          "n_terms" -> Length[triTerms], "n_box_terms_dropped" -> nBoxTerms,
          "setdelta" -> 0, "setmudim" -> 1,
          "amplitude" -> Mtri|>, $triOutPath]];

  projTri = projectOperators[Mtri, abbrF, mchi, mq];
  If[! TrueQ[projTri["ok"]],
    WriteString["stderr", "run_dd_triangle_continuity: triangle projection failed: " <>
      ToString[projTri["reason"]] <> "\n"];
    Exit[3]];

  sector[proj_] := <|
    "C_scalar_re" -> Re[proj["C_scalar"]], "C_scalar_re_str" -> fp[Re[proj["C_scalar"]]],
    "C_scalar_im" -> Im[proj["C_scalar"]], "C_scalar_im_str" -> fp[Im[proj["C_scalar"]]],
    "C_twist2_re" -> Re[proj["C_twist2"]],
    "si3_completeness_rel_residual" -> proj["completeness_rel_residual"],
    "full_basis_completeness_rel_residual" ->
      proj["full_basis_completeness_rel_residual"],
    "full_basis_completeness_rel_residual_str" ->
      fp[proj["full_basis_completeness_rel_residual"]],
    "C_scalar_full_re" -> Re[proj["C_scalar_full"]],
    "si_shift_rel" -> proj["si_shift_rel"],
    "absorbed_norm_shares" -> proj["absorbed_norm_shares"]|>;

  jsonAssoc = <|
    "schema" -> "dd_triangle_continuity/v1",
    "n_terms" -> Length[terms],
    "n_triangle_terms" -> Length[triTerms],
    "n_box_terms" -> nBoxTerms,
    "n_boxy_subs" -> Length[boxySyms],
    "binding" -> "canonical (run_eval_sd.wls mkNum, extPins, setdelta 0, setmudim 1)",
    "triangle_only" -> sector[projTri]
  |>;

  (* ---- probe 3 (amendment Ruling 4): full / box sector fits ------------------ *)
  If[$ampDdPath =!= None,
    Module[{dd = Quiet[Check[Get[$ampDdPath], $Failed]]},
      If[dd === $Failed || ! AssociationQ[dd] || ! KeyExistsQ[dd, "expanded_amplitude"],
        WriteString["stderr",
          "run_dd_triangle_continuity: could not read expanded_amplitude from " <>
          ToString[$ampDdPath] <> "\n"];
        Exit[1]];
      MnumFull = dd["expanded_amplitude"]];
    Mbox = MnumFull - Mtri;  (* exact by F-linearity of the evaluation *)
    projFull  = projectOperators[MnumFull, abbrF, mchi, mq];
    projFullV = projectOperators[MnumFull, abbrF, mchi, mq, 0.1];
    projBox   = projectOperators[Mbox, abbrF, mchi, mq];
    If[! TrueQ[projFull["ok"]] || ! TrueQ[projBox["ok"]],
      WriteString["stderr", "run_dd_triangle_continuity: probe-3 projection failed\n"];
      Exit[3]];
    (* v -> v/10 on C_scalar_full ONLY (C_twist2_full no longer exists in the
       rotated-complete instrument).  A guard REFUSAL at v/10 (measured:
       ILLCONDITIONED, cond ~ 1/v^2) is a named outcome here, not a runner
       failure. *)
    vDrift = If[TrueQ[projFullV["ok"]],
      If[Abs[projFull["C_scalar_full"]] < 1*^-300, Abs[projFullV["C_scalar_full"]],
        Abs[(projFullV["C_scalar_full"] - projFull["C_scalar_full"])/projFull["C_scalar_full"]]],
      "UNMEASURABLE: " <> ToString[projFullV["reason"]]];
    jsonAssoc = Join[jsonAssoc, <|
      "probe3" -> <|
        "full" -> sector[projFull],
        "expanded_box_only" -> sector[projBox],
        "full_basis_velocity_drift_rel_v10" -> vDrift,
        "full_basis_velocity_drift_rel_v10_str" ->
          If[StringQ[vDrift], vDrift, fp[vDrift]],
        "note" -> "rotated-complete instrument fits (DESIGN-ITEM4-AMENDMENT2.md); " <>
          "diagnostics ONLY (Ruling 2) — nothing here flows to nucleon matching. " <>
          "The historical 0.669 residual was an instrument artifact (rank-12 " <>
          "basis + unrotated Majorana-crossed monomials); the earlier " <>
          "frozen-kinematics mapping in this note was retracted (RF-minor-2)."
      |>|>]];

  writeEvalOutput[outPath, jsonAssoc];
  Print["run_dd_triangle_continuity: wrote ", outPath,
        " C_scalar(tri)=", fp[Re[projTri["C_scalar"]]],
        " full_basis_resid(tri)=", fp[projTri["full_basis_completeness_rel_residual"]],
        If[$ampDdPath =!= None,
          " full_basis_resid(full)=" <> fp[projFull["full_basis_completeness_rel_residual"]] <>
          " si_shift(full)=" <> fp[projFull["si_shift_rel"]] <>
          " vdrift(full)=" <> fp[vDrift], ""]];
  Exit[0]
]
