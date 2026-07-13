#!/usr/bin/env wolframscript
(* run_eval_sd.wls — Wolfram + LoopTools (MathLink) DD evaluation driver for the
   SINGLET-DOUBLET model (STEP3-DESIGN.md Decision 4).  Parallel to run_eval.wls
   (2HDM+a); shares the model-agnostic plumbing via run_eval_common.wl and the
   chain-coefficient projection via sd_projection.wl.

   The 2HDM+a driver is the toolkit's only EW-anchor-validated chain; this file
   NEVER touches it.  Blast radius of a parallel driver: zero (Decision 4).

   Usage (from run_looptools.py run_driver, --model singlet_doublet):
     wolframscript -script run_eval_sd.wls \
       <amp_reduced.m> <point.json> <form_factor_preset> <eval_output.json> <looptools_prefix>

   ------------------------------------------------------------------------------
   WHAT THIS COMPUTES  (physics; read before editing)
   ------------------------------------------------------------------------------
   The elastic  chi1 q -> chi1 q  one-loop amplitude for a MAJORANA chi1 and an
   external DOWN-type quark (STEP2.md: process {F[5,{1}], F[4,{.}]} elastic).
   Unlike run_eval.wls it does NOT spin-sum-collapse the Weyl chains: it keeps the
   FormCalc form factors symbolic in the chains (F1..F18 for the real SD amp)
   and projects onto the operator basis
   (scalar C_q + twist-2 C^(1,2)_q, Decision 3) via sd_projection.wl, so scalar
   and twist-2 are SEPARATED (they are degenerate under the static collapse).

   Output: per-operator Wilson coefficients + driver-side A5 nucleon contraction
   (schema looptools_sd_coefficients/v2).  sigma_SI ships as the AMENDMENT3
   Ruling-1 TWO-VALUE BRACKET (with / without the C_G gluon term), both values
   sigma_provisional, with the +-6e-10 rank-2 band on the measured light-quark
   C_q propagated into f_N.  match_nucleon.py stays byte-untouched.

   ------------------------------------------------------------------------------
   TWO [VERIFY] FLAGS resolved against the SD SPheno output (Decision 4 table):
   ------------------------------------------------------------------------------
   - ZN phase convention: the SD neutralino mixing is genuinely COMPLEX.  SPheno
     splits it across ZNMIX (Re) and IMZNMIX (Im); binding ZN from ZNMIX ALONE
     would zero chi2's entire coupling (its ZNMIX row is 0, its IMZNMIX row is
     not).  Correct: ZN[i,j] = ZNMIX[i,j] + I*IMZNMIX[i,j].  SARAH generates both
     the SPheno spectrum and the FeynArts model from one model file, so the phase
     convention is consistent by construction.
   - yh1/yh2 portal-Yukawa block: SPheno writes them at BOTH MINPAR (3,4) and
     BSMPARAMS (3,4).  We bind from BSMPARAMS (the running values at the
     renormalisation scale Q, consistent with how Yu/Yd/GAUGE are bound), with
     MINPAR as a documented fallback.
*)

(* ---- model-specific TOP-LEVEL constants (before the common Get) ------------- *)
mUlight = 2.16*^-3; mDlight = 4.67*^-3; mSlight = 0.093;
mClight = 1.27;     mBlight = 4.18;     mTlight = 173.4;
TEPS = 1.0*^-4;  (* spacelike t->0 regulator (GeV^2), per run_eval.wls:24-28 *)

(* Box small-momentum (DD-limit) expansion (DESIGN-ITEM4.md A1): rewrite the box
   tensor D0i[dd1..dd33] heads onto the rank-1 collinear {g,uu} basis -> scalar
   D0/C0/B0, curing the Gram-determinant spurious pole that put ||M||~1e28 (the
   verified item-4 blocker).  ON by default for the SD path (the SD box sector was
   un-evaluable without it); env HEPPH_SD_DD_EXPANSION=0 disables it to reproduce
   the pre-item-4 (Gram-poled) behaviour for A/B comparison.  sd_dd_expansion.wl
   is Get[]-loaded below, AFTER run_eval_common.wl has Install[]ed LoopTools. *)
$ddExpansion = (Environment["HEPPH_SD_DD_EXPANSION"] =!= "0");

(* ---- model-agnostic plumbing (argv, FormCalc+LoopTools load, self-test,
        evalTermCommon / emitUnboundGuard / writeEvalOutput). ------------------- *)
$scriptDir = "/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-a4f66e3295b1b33b8/plugins/hep-ph-toolkit/skills/looptools/scripts/"; (* PROBE PATCH: pinned to repo scripts dir *)
Get[FileNameJoin[{$scriptDir, "run_eval_common.wl"}]];
Get[FileNameJoin[{$scriptDir, "sd_projection.wl"}]];
Get[FileNameJoin[{$scriptDir, "sd_dd_expansion.wl"}]];

Module[{
    ampPath = $ampPath, pointPath = $pointPath, ffPreset = $ffPreset,
    outPath = $outPath, ltPrefix = $ltPrefix,
    point, masses, params, getMass, getParam, getParamAny,
    mchi1, mchi2, mchi3, mchiM, mh, mZ, mW, mchi, mq,
    ZNm, IMZNm, UMm, UPm, ZDLm, ZDRm, ZULm, ZURm, Yum, Ydm,
    yh1v, yh2v, g1v, g2v, g3v, Lamv, PhaseFSv, vvSMv, ctw, stw,
    amp, subexpr, ampBody, abbr, abbrF, terms, mkNum, extIdx, extPins,
    boxCensusBefore, ddTerms, ddSubexpr,
    evalAmp, Mnum, Mtri, nTriTerms, resid, proj, projAt, coeffNames,
    cScalar, cTw, cChiV, uvResidue, scaleResidue, finiteQ, complResidual,
    nPV, jsonAssoc, bindGuard, unbound, matrixUnbound,
    chainDefsA, fsymsA, triFit, triFitV, cTri, cQuniv, cQdrift,
    transferV10Outcome, prodV, cScalarProd, cTw2Sum, cTw2Dif,
    driftCscalarAbs, driftTw2SumRel, vlegNote, nucleon, uvOkQ, reopenChecks
  },

  (* ---- point import (model-agnostic; duplicated per include header note) ----- *)
  point = Quiet[Check[Import[pointPath, "RawJSON"], $Failed]];
  If[point === $Failed,
    WriteString["stderr", "run_eval_sd: could not read point.json\n"]; Exit[1]];
  masses = point["masses"]; params = point["params"];
  mchi = point["m_dm_gev"];
  getMass[pdg_] := masses[ToString[pdg]];
  getParam[k_]  := Lookup[params, k, $Failed];
  (* BSMPARAMS preferred, MINPAR fallback (yh1/yh2 resolution). *)
  getParamAny[ks_List] := Module[{hit},
    hit = SelectFirst[ks, (Lookup[params, #, $Failed] =!= $Failed) &, $Failed];
    If[hit === $Failed, $Failed, Lookup[params, hit, $Failed]]];

  (* ---- SD mass lookups by SD PDG code (STEP2.md; SPheno MASS block) ---------- *)
  mchi1 = getMass[9958431]; mchi2 = getMass[9956206]; mchi3 = getMass[9979223];
  mchiM = getMass[9984071];
  mh = getMass[25]; mZ = getMass[23]; mW = getMass[24];
  mchi = If[NumberQ[mchi1], mchi1, mchi];  (* external chi1 *)
  mq   = mDlight;                          (* representative external down quark;
                                              per-flavor pinning is item 4 *)

  (* ---- SD coupling / mixing binding table (Decision 4) ----------------------- *)
  (* ZN COMPLEX: ZNMIX (Re) + I*IMZNMIX (Im) — [VERIFY] resolved. *)
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
  (* yh1/yh2 — [VERIFY] resolved: BSMPARAMS (running), MINPAR fallback. *)
  yh1v = getParamAny[{"BSMPARAMS:3", "MINPAR:3"}];
  yh2v = getParamAny[{"BSMPARAMS:4", "MINPAR:4"}];
  g1v = getParam["GAUGE:1"]; g2v = getParam["GAUGE:2"];
  g3v = getParam["GAUGE:3"];  (* the real reduced amp carries g3 (QCD coupling,
     e.g. Sub352 in the Subexpr table); PR #31 never bound it — first exposed by
     the live self-contained-artifact run. *)
  Lamv = getParam["SM:2"];
  PhaseFSv = getParam["PHASES:1"];
  vvSMv = getParam["HMIX:3"];
  ctw = mW/mZ; stw = Sqrt[1 - ctw^2];

  (* ---- MODEL-BINDING GUARD (loud-failure; DETECTION ONLY) -------------------- *)
  bindGuard = {
    "MassFChi[1](chi1,9958431)" -> mchi1, "MassFChi[2](chi2,9956206)" -> mchi2,
    "MassFChi[3](chi3,9979223)" -> mchi3, "MassFChiM(chi+-,9984071)" -> mchiM,
    "Masshh(h,25)" -> mh, "MassVZ/MassAh(Z/G0,23)" -> mZ, "MassVWp/MassHp(W/G+,24)" -> mW,
    "yh1(BSMPARAMS:3|MINPAR:3)" -> yh1v, "yh2(BSMPARAMS:4|MINPAR:4)" -> yh2v,
    "g1(GAUGE:1)" -> g1v, "g2(GAUGE:2)" -> g2v, "g3(GAUGE:3)" -> g3v,
    "Lam(SM:2)" -> Lamv,
    "PhaseFS(PHASES:1)" -> PhaseFSv, "vvSM(HMIX:3)" -> vvSMv};
  matrixUnbound = Join[
    If[MemberQ[Flatten[ZNm], $Failed] || ! FreeQ[ZNm, _Missing], {"ZN(ZNMIX+I*IMZNMIX)"}, {}],
    If[MemberQ[Flatten[UMm], $Failed] || ! FreeQ[UMm, _Missing], {"UM(UMMIX)"}, {}],
    If[MemberQ[Flatten[UPm], $Failed] || ! FreeQ[UPm, _Missing], {"UP(UPMIX)"}, {}],
    If[MemberQ[Flatten[ZDLm], $Failed] || ! FreeQ[ZDLm, _Missing], {"ZDL(UDLMIX)"}, {}],
    If[MemberQ[Flatten[ZDRm], $Failed] || ! FreeQ[ZDRm, _Missing], {"ZDR(UDRMIX)"}, {}],
    If[MemberQ[Flatten[ZULm], $Failed] || ! FreeQ[ZULm, _Missing], {"ZUL(UULMIX)"}, {}],
    If[MemberQ[Flatten[ZURm], $Failed] || ! FreeQ[ZURm, _Missing], {"ZUR(UURMIX)"}, {}],
    If[MemberQ[Flatten[Yum], $Failed] || ! FreeQ[Yum, _Missing], {"Yu(YU)"}, {}],
    If[MemberQ[Flatten[Ydm], $Failed] || ! FreeQ[Ydm, _Missing], {"Yd(YD)"}, {}]];
  unbound = Join[Keys[Select[bindGuard, unboundQ[Last[#]] &]], matrixUnbound];
  emitUnboundGuard[unbound,
    "  The supplied model point does not bind these singlet-doublet amplitude\n" <>
    "  symbols. run_eval_sd.wls expects an SD SPheno spectrum (SD PDG codes,\n" <>
    "  ZNMIX/IMZNMIX/UMMIX/UPMIX/UDLMIX/UDRMIX/YU/YD/GAUGE/SM/PHASES/HMIX/BSMPARAMS).\n" <>
    "  A 2HDM+a point belongs to run_eval.wls (--model 2hdma).\n"];

  (* ---- amplitude read (both wrapped-association and bare-Amp formats) -------- *)
  amp = Quiet[Check[Get[ampPath], $Failed]];
  If[amp === $Failed,
    WriteString["stderr", "run_eval_sd: Get[amp_reduced.m] failed\n"]; Exit[1]];
  subexpr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "subexpr"], "subexpr" /. amp, {}];
  ampBody = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "amp"], "amp" /. amp, amp];
  (* Abbr[] WeylChain table — REQUIRED by the numerical basis-vector projector
     (sd_projection.wl): it reads each chain's operator content from its ACTUAL
     WeylChain definition (the F1 review fix; no hard-coded index blocks). *)
  abbr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "abbr"], "abbr" /. amp, {}];
  abbrF = Cases[abbr, HoldPattern[_ -> _WeylChain]];  (* HoldPattern: else Cases
     reads `_ -> _WeylChain` as a pattern->transform rule, not a match target. *)
  terms = List @@ ampBody;

  (* ---- EARLY LOUD GUARD: undefined FormCalc abbreviations --------------------
     Cheap structural check BEFORE any PV/LoopTools work.  If the reduced amp was
     Put[] without its Subexpr[] table (the STEP2 amp_reduced.m case), the Sub####
     abbreviations are undefined after `//. subexpr` and the F-chains they hide
     cannot be reached.  Detect it here so the failure is loud and fast, not a
     slow full-amplitude evaluation that ends non-numeric. *)
  Module[{danglingSub},
    (* Heads -> True (F3 review fix): the real amp carries FUNCTION-FORM
       abbreviations Sub####[I3G2,...] whose Sub#### appears only as a HEAD; the
       default Heads -> False would miss them when no bare-symbol Sub coexists. *)
    danglingSub = DeleteDuplicates[Cases[terms //. subexpr,
      s_Symbol /; StringMatchQ[SymbolName[s], "Sub" ~~ DigitCharacter ..],
      Infinity, Heads -> True]];
    If[Length[danglingSub] > 0,
      WriteString["stderr",
        "run_eval_sd: SD-AMP-ABBREVIATIONS-UNRESOLVED " <>
        ToString[Take[SymbolName /@ danglingSub, UpTo[30]], InputForm] <> "\n" <>
        "  The reduced amplitude carries undefined FormCalc abbreviations (Sub####):\n" <>
        "  amp_reduced.m was written by Put[reduced] WITHOUT the Subexpr[] table, so\n" <>
        "  the external Weyl chains and couplings hidden inside those abbreviations\n" <>
        "  are unreachable and the coefficient-level projection cannot resolve them.\n" <>
        "  Fix: re-run /formcalc reduce persisting Subexpr[] into amp_reduced.m as a\n" <>
        "  wrapped {\"amp\"->..,\"subexpr\"->..} association.\n"];
      Exit[3]]];

  (* ---- GUARD: Abbr[] table present (numerical basis-vector projector needs it) *)
  If[abbrF === {},
    WriteString["stderr",
      "run_eval_sd: SD-AMP-ABBREVIATIONS-UNRESOLVED (no Abbr[] WeylChain table)\n" <>
      "  The reduced amplitude carries no \"abbr\" -> {F -> WeylChain[..]} table, so\n" <>
      "  the numerical basis-vector projector (Decision 3.2) cannot read each\n" <>
      "  chain's operator content from its actual spinor structure.  Re-run\n" <>
      "  /formcalc reduce persisting BOTH Subexpr[] and the Abbr[] WeylChain table.\n"];
    Exit[3]];

  (* ---- numeric substitution rules — F-chains KEPT SYMBOLIC (Decision 3.1;
        the real SD amp carries F1..F18) ------------------------------------- *)
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

  (* ---- EXTERNAL-index pinning ------------------------------------------------
     The reduced amp carries 3-arg `SumOver[i, n, External]` factors for the
     EXTERNAL quark generation indices (I3G2 incoming, I3G4 outgoing).  These are
     class-level bookkeeping, NOT physical sums: the elastic process has a fixed
     external flavor, so we PIN them to generation 1 (down quark, matching
     mq = mDlight and "external_quark": "d") and drop the SumOver factors.
     evalTermCommon's iterator pattern is 2-arg, so unhandled External SumOvers
     would otherwise leave I3G2/I3G4 symbolic (PV heads non-numeric).  INTERNAL
     sums (I3G5, j21i, j22i, ...) remain expanded exactly (R3: no gen pinning
     applies to internal sums; per-flavor EXTERNAL runs are item 4). *)
  extIdx = DeleteDuplicates[Cases[terms, SumOver[i_, _, External] :> i, Infinity]];
  extPins = Join[{SumOver[_, _, External] -> 1}, (# -> 1) & /@ extIdx];

  (* ---- BOX SMALL-MOMENTUM (DD) EXPANSION (DESIGN-ITEM4.md A1) ----------------
     Rewrite the box tensor D0i heads onto the rank-1 collinear scalar basis by
     substituting the head symbol D0i -> ddBoxHead on BOTH the term bodies and the
     Subexpr[] table (box heads hide inside Sub#### too).  ddBoxHead stays inert on
     symbolic kinematics and fires the scalar reduction only once mkNum makes the
     arguments numeric — so LoopTools never evaluates a Gram-poled tensor D0i at
     the degenerate point.  Scalar boxes (dd0) and all triangles/bubbles (C0i/B0i)
     pass through untouched. *)
  boxCensusBefore = ddBoxHeadCensus[terms];
  ddTerms   = If[$ddExpansion, terms   /. ddExpandRule, terms];
  ddSubexpr = If[$ddExpansion, subexpr /. ddExpandRule, subexpr];

  (* ---- STRUCTURAL GUARD, SYMBOLIC SIDE (F5, load-bearing) --------------------
     Any D0i tensor head still present in the term bodies or the Subexpr table
     AFTER the rewrite has SYMBOLIC arguments here, so it cannot yet have
     auto-evaluated through the MathLink.  This is the ONLY stage at which an
     un-rewritten box tensor is pattern-visible: once mkNum numericizes the
     arguments, LoopTools evaluates it to a Gram-poled NUMBER and no head check
     can see it (PR #35 review F5).  Exit 3 on any survivor — nothing ships. *)
  If[$ddExpansion,
    ddAssertNoSurvivors[ddTerms, "symbolic-pre-eval-terms"];
    ddAssertNoSurvivors[ddSubexpr, "symbolic-pre-eval-subexpr"]];

  (* Evaluate the full amplitude to an F-LINEAR numeric form.  Fp = {} keeps the
     external chains symbolic (that IS the coefficient-level projection); the
     SumOver internal-eigenstate/generation sums are expanded exactly by
     evalTermCommon (R3: no gen pinning). *)
  evalAmp[delta_, mudim_] := Total[Table[
    evalTermCommon[ddTerms[[k]], ddSubexpr, {}, mkNum[delta, mudim], extPins],
    {k, Length[ddTerms]}]];

  (* ---- TRIANGLE/BOX SECTOR SPLIT (AMENDMENT3 Ruling 1 / Decision A4) ---------
     The heavy-quark C_Q (SVZ gluon term) is the flavor-universal h-exchange
     TRIANGLE coefficient, so the driver needs the triangle-only sector.  Same
     exact split as run_dd_triangle_continuity.wls: a term's resolved body
     contains a D0i iff the raw term carries D0i directly or references (at any
     depth) a Sub whose definition transitively does.  Computed on the RAW
     terms/subexpr (the dd expansion touches only D0i heads, so D0i-free terms
     and the Subs they reference are byte-identical before/after — the
     triangle-only evaluation below is bit-for-bit the continuity fixture's).
     Evaluated per term ONCE at the canonical (0,1) scheme point, so the split
     costs no extra amplitude evaluation. *)
  Module[{subSymOf, boxySyms, changed, triQ},  (* PROBE PATCH: termVals/triIdx leak to Global for the P1/P1b tail *)
    subSymOf[lhs_] := If[AtomQ[lhs], lhs, Head[lhs]];
    boxySyms = {}; changed = True;
    While[changed, changed = False;
      Do[Module[{s = subSymOf[r[[1]]], rhs = r[[2]]},
          If[! MemberQ[boxySyms, s] &&
             (! FreeQ[rhs, D0i] || AnyTrue[boxySyms, ! FreeQ[rhs, #] &]),
            AppendTo[boxySyms, s]; changed = True]],
        {r, subexpr}]];
    triQ[t_] := FreeQ[t, D0i] && AllTrue[boxySyms, FreeQ[t, #] &];
    triIdx = Flatten[Position[terms, t_ /; triQ[t], {1}, Heads -> False]];
    termVals = Table[
      evalTermCommon[ddTerms[[k]], ddSubexpr, {}, mkNum[0, 1], extPins],
      {k, Length[ddTerms]}];
    Mnum = Total[termVals];
    If[triIdx === {} || Length[triIdx] === Length[terms],
      WriteString["stderr",
        "run_eval_sd: SD-TRIANGLE-SECTOR-EMPTY degenerate triangle/box split (" <>
        ToString[Length[triIdx]] <> " of " <> ToString[Length[terms]] <>
        " terms triangle-only)\n" <>
        "  The flavor-universal heavy-quark C_Q is the triangle-sector scalar\n" <>
        "  coefficient (Decision A4); with a degenerate split it is unmeasurable\n" <>
        "  and no sigma_SI bracket can be built.  Nothing ships.\n"];
      Exit[3]];
    Mtri = Total[termVals[[triIdx]]];
    nTriTerms = Length[triIdx]];


  (* ======================================================================
     PROBE TAIL — AMENDMENT5 Ruling 2, Q1 + Q2 (job-dir sidecar; the
     production driver is untouched).  Head above is the exact driver
     preamble; Mtri/termVals/triIdx available per the PROBE PATCH.
     ====================================================================== *)
  Module[{ccP, fsymsP, chainDefsP, rot3fit, q1, crulesT, crossedQT, nCross,
          MtriCross, MtriDir, cfgsS, vals, vC, vD, vT, coefShare,
          fitCU, fitDU, q2CR, q2DR},

  ccP = chainClass[abbrF]; fsymsP = Keys[ccP];
  chainDefsP = Association[Cases[abbrF, (f_ -> wc_WeylChain) :> (f -> wc)]];

  (* rotated-3op fit on an arbitrary F-linear amplitude: byte-follows the
     productionVLeg construction (sd_projection.wl) at vscale 1, with the
     fit residual added *)
  rot3fit[M_] := Module[
    {crules, crossedQ, cfgs, refCfgs, rot, monoVals, MrotVals, opCols, mat,
     y, sol},
    crules = Quiet[CoefficientRules[M, fsymsP]];
    If[crules === {}, Return[<|"ok" -> False, "reason" -> "empty amplitude"|>]];
    crossedQ = Table[Module[{ex = Keys[crules][[t]], ss},
        ss = Flatten[Table[ConstantArray[fsymsP[[i]], ex[[i]]], {i, Length[fsymsP]}]];
        Length[ss] === 2 && ss[[1]] =!= ss[[2]] &&
          barChiMixedQ[chainDefsP[ss[[1]]]] && barChiMixedQ[chainDefsP[ss[[2]]]]],
      {t, Length[crules]}];
    cfgs = sampleConfigs[N[mchi], N[mq], 1.0];
    refCfgs = referenceConfigs[N[mchi], N[mq], 1.0];
    rot = rotatedMonoVals[chainDefsP, fsymsP, crules, crossedQ, refCfgs, True];
    If[TrueQ[rot["failed"]],
      Return[<|"ok" -> False, "reason" -> "crossed rotation failed"|>]];
    monoVals = rot["mono_vals"];
    MrotVals = N[Transpose[monoVals] . Values[crules]];
    opCols = Table[Table[$opRefs[op][cfg["kin"], cfg["spin"], N[mchi], N[mq]],
      {op, Keys[$opRefs]}], {cfg, cfgs}];
    mat = N[opCols]; y = MrotVals[[1 ;; Length[cfgs]]];
    sol = Quiet[LeastSquares[mat, y]];
    <|"ok" -> True, "coeffs" -> AssociationThread[Keys[$opRefs] -> sol],
      "rel_residual" -> If[Norm[y] < 1*^-300, Norm[y - mat . sol],
        Norm[y - mat . sol]/Norm[y]],
      "rot_err_max" -> rot["rot_err_max"], "n_cfgs" -> Length[cfgs],
      "n_crossed" -> Count[crossedQ, True]|>];

  (* ---- Q1: rotated-3op fit on M_tri alone ---- *)
  q1 = rot3fit[Mtri];
  If[TrueQ[q1["ok"]],
    Print["probe_q12: Q1 rotated-3op(M_tri) C_scalar = ",
          InputForm[q1["coeffs"]["C_scalar"]],
          " rel_resid = ", InputForm[q1["rel_residual"]],
          " rot_err_max = ", InputForm[q1["rot_err_max"]],
          " n_cfgs = ", q1["n_cfgs"], " n_crossed_monos = ", q1["n_crossed"]];
    Print["probe_q12: Q1 all coeffs = ", InputForm[q1["coeffs"]]],
    Print["probe_q12: Q1 REFUSED: ", q1["reason"]]];

  (* ---- Q2: probeH-style crossing split of M_tri ---- *)
  crulesT = Quiet[CoefficientRules[Mtri, fsymsP]];
  crossedQT = Table[Module[{ex = Keys[crulesT][[t]], ss},
      ss = Flatten[Table[ConstantArray[fsymsP[[i]], ex[[i]]], {i, Length[fsymsP]}]];
      Length[ss] === 2 && ss[[1]] =!= ss[[2]] &&
        barChiMixedQ[chainDefsP[ss[[1]]]] && barChiMixedQ[chainDefsP[ss[[2]]]]],
    {t, Length[crulesT]}];
  nCross = Count[crossedQT, True];
  Print["probe_q12: Q2 M_tri monomials total = ", Length[crulesT],
        " crossed = ", nCross, " crossed_monos = ",
        InputForm[Pick[Keys[crulesT], crossedQT]],
        " crossed_coeffs = ", InputForm[Pick[Values[crulesT], crossedQT]]];
  MtriCross = If[nCross == 0, 0, FromCoefficientRules[Pick[crulesT, crossedQT], fsymsP]];
  MtriDir  = Mtri - MtriCross;

  cfgsS = sampleConfigs[N[mchi], N[mq], 1.0];
  vals[M_] := Table[Module[{kin = cfg["kin"], spin = cfg["spin"], frule},
      frule = (# -> chainValueOn[chainDefsP[#], kin, spin]) & /@ fsymsP;
      M /. frule], {cfg, cfgsS}];
  vT = vals[Mtri]; vC = vals[MtriCross]; vD = vals[MtriDir];
  coefShare = If[nCross == 0, 0.,
    Norm[N[Pick[Values[crulesT], crossedQT]]]/Norm[N[Values[crulesT]]]];
  Print["probe_q12: Q2 crossed share ||vals||: ", InputForm[Norm[vC]/Norm[vT]],
        "  direct share: ", InputForm[Norm[vD]/Norm[vT]],
        "  coeff-norm share: ", InputForm[coefShare]];

  If[nCross > 0,
    fitCU = threeOpFit[MtriCross, chainDefsP, fsymsP, mchi, mq];
    fitDU = threeOpFit[MtriDir,  chainDefsP, fsymsP, mchi, mq];
    Print["probe_q12: Q2 UNROTATED O_S: crossed = ",
          InputForm[fitCU["coeffs"]["C_scalar"]],
          "  direct = ", InputForm[fitDU["coeffs"]["C_scalar"]]];
    q2CR = rot3fit[MtriCross]; q2DR = rot3fit[MtriDir];
    Print["probe_q12: Q2 ROTATED O_S: crossed = ",
          InputForm[If[TrueQ[q2CR["ok"]], q2CR["coeffs"]["C_scalar"], q2CR["reason"]]],
          "  direct = ",
          InputForm[If[TrueQ[q2DR["ok"]], q2DR["coeffs"]["C_scalar"], q2DR["reason"]]]],
    Print["probe_q12: Q2 M_tri carries NO crossed monomials — X REFUTED at the",
          " pre-registered bar (crossed share exactly 0); rotation cannot",
          " explain the tri-sector gap."]];
  Print["probe_q12: DONE"];
  ];
];
Exit[0]
