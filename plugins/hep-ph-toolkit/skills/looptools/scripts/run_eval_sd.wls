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
$scriptDir = DirectoryName[
  If[$InputFileName =!= "" && $InputFileName =!= Null, $InputFileName,
     $ScriptCommandLine[[1]]]];
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
  Module[{subSymOf, boxySyms, changed, triQ, termVals, triIdx},
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

  (* ---- STRUCTURAL GUARD, EVALUATED SIDE + GRAM MONITOR ------------------------
     Catches inert symbolic ddBoxHead leftovers (arguments never went numeric,
     e.g. an unresolved index blocked the mkNum rules).  A raw numeric D0i cannot
     be caught here (it auto-evaluates) — that case is owned by the symbolic-side
     guard above.  Also emits the Gram/degeneracy monitor line from the real
     evaluation set. *)
  If[$ddExpansion,
    Module[{mon = ddMonitorSummary[]},
      WriteString["stderr",
        "run_eval_sd: GRAM-MONITOR n_box_signatures=" <>
        ToString[Lookup[mon, "n_box_signatures", 0]] <>
        " max_rank1_residual=" <> ToString[Lookup[mon, "max_rank1_residual", "NA"], InputForm] <>
        " min_abs_gram_det_over_scale3=" <>
        ToString[Lookup[mon, "min_abs_gram_det_over_scale3", "NA"], InputForm] <> "\n"];
      ddAssertNoSurvivors[Mnum, "evaluated"]]];

  (* ---- amp_dd.m SIDECAR (Decision A3) ---------------------------------------- *)
  If[$ddExpansion,
    writeAmpDdSidecar[
      FileNameJoin[{DirectoryName[outPath], "amp_dd.m"}], Mnum, boxCensusBefore,
      "leading-DD (v=0) collinear reconstruction; rank-2 method accuracy budget " <>
      "~3e-3 at TEPS (see sd_dd_expansion.wl header)",
      <|"point_id" -> mchi, "external_quark" -> "d"|>]];

  (* ---- LOUD GUARD: unresolved abbreviations / non-numeric coefficients -------
     If the reduced amp was Put[] WITHOUT its FormCalc Subexpr[] table (the STEP2
     amp_reduced.m case), the Sub#### abbreviations — which hide the F-chains and
     couplings — are undefined, so the projected coefficients are NOT numeric.
     Fail LOUDLY at a named guard rather than emit a nonsense floor. *)
  resid = residualSymbols[Mnum];
  If[Length[resid] > 0,
    WriteString["stderr",
      "run_eval_sd: SD-AMP-ABBREVIATIONS-UNRESOLVED " <>
      ToString[Take[ToString /@ resid, UpTo[30]], InputForm] <> "\n" <>
      "  The reduced amplitude is not fully numeric after substitution: the named\n" <>
      "  symbols survived the mkNum binding rules.  Common causes: (a) a coupling\n" <>
      "  the amplitude uses but the binding table does not cover (e.g. g3 before\n" <>
      "  this fix); (b) a Sub#### abbreviation with no definition in the persisted\n" <>
      "  Subexpr[] table; (c) an index left symbolic so an indexed rule could not\n" <>
      "  fire.  The F-chains/couplings inside unresolved abbreviations are\n" <>
      "  unreachable, so the coefficient-level projection refuses to continue.\n"];
    Exit[3]];

  (* ---- projection onto the operator basis (sd_projection.wl, Decision 3.2) ----
     Numerical spinor-basis solve: each chain is read from its ACTUAL WeylChain
     definition (no hard-coded index blocks — the F1 review fix) and evaluated on
     an explicit spinor basis; the operator coefficients are the least-squares
     solution.  A structurally-unrecognized chain or an incomplete fit fails loud
     (the F2 review fix — no silent fall-through). *)
  proj = projectOperators[Mnum, abbrF, mchi, mq];
  (* instrument-level failures carry their own marker names (SD-FIERZ-ROTATION-
     INEXACT, SD-PROJECTION-BASIS-{RANK-DEFICIENT,ILLCONDITIONED,UNIDENTIFIABLE},
     SD-PROJECTION-MONOMIAL-OUT-OF-SPAN) — emitted verbatim + Exit[3] here *)
  projInstrumentAssert[proj];
  If[! TrueQ[proj["ok"]],
    WriteString["stderr",
      "run_eval_sd: SD-PROJECTION-FAILED " <> ToString[proj["reason"]] <> " " <>
      ToString[Lookup[proj, "unrecognized_chains", {}], InputForm] <> "\n" <>
      "  The chain-coefficient projection could not map the amplitude onto the\n" <>
      "  recognized SI operator set.  Either a chain's WeylChain structure is\n" <>
      "  outside the {chi|quark|mixed} x {rank 0|1} taxonomy the projector handles,\n" <>
      "  or the amplitude carries content the recognized {scalar, twist-2, chi-\n" <>
      "  vector} operators do not span.  This is a LOUD refusal, not a silent drop.\n"];
    Exit[3]];
  cScalar = proj["C_scalar"]; cTw = proj["C_twist2"]; cChiV = proj["C_chi_vector"];
  complResidual = proj["completeness_rel_residual"];

  (* ---- COMPLETENESS GUARD (AMENDMENT2 Ruling 4, rotated-complete) ------------
     Criterion 1: the ROTATED-COMPLETE reference instrument (rank-verified
     256-column dictionary, Majorana-crossed monomials C-conjugate-rotated) must
     span the ROTATED amplitude to $fullCompletenessTol = 1e-8.  RECONCILIATION
     (AMENDMENT2, RF-minor-2): the historical 0.669 residual here was an
     instrument artifact of a rank-12 basis plus UNROTATED Majorana-crossed
     content — no physics meaning; the earlier frozen-kinematics reading is
     RETRACTED (pr35-rereview/REVIEW.md).  A residual over the bar WITH the
     rotation + rank guards green is pre-registered reopen trigger (a) for
     per-config kinematics (Ruling 2).  The 3-op residual is still reported
     (si3_completeness_ok) but is NOT the shipping guard; the instrument NAMES
     out-of-span content (out_of_span_diagnostics), never feeds nucleon
     matching (Ruling 2: only C_scalar/C_twist2/C_G ever flow onward). *)
  If[! TrueQ[proj["completeness_ok"]],
    WriteString["stderr",
      "run_eval_sd: SD-PROJECTION-INCOMPLETE full_basis_completeness_rel_residual=" <>
      ToString[proj["full_basis_completeness_rel_residual"], InputForm] <>
      " (tol=" <> ToString[$fullCompletenessTol, InputForm] <> ", 3-op residual=" <>
      ToString[complResidual, InputForm] <> ")\n" <>
      "  The rotated-complete REFERENCE instrument does not span the rotated\n" <>
      "  amplitude to the bar with its rank/rotation guards green — the\n" <>
      "  pre-registered reopen trigger (a) for per-config kinematics\n" <>
      "  (DESIGN-ITEM4-AMENDMENT2.md Ruling 2).  Nothing ships.\n"];
    Exit[3]];

  (* ---- SI-EXTRACTION SHIFT: superseded gate, now a REPORT -------------------
     HISTORY: through PR #35 this block was the SD-SI-EXTRACTION-UNSTABLE
     Exit[3] refusal (Ruling 3 criterion 2), and it FIRED on the canonical
     point (si_shift 100.1%) — the pre-registered retirement clause.
     DESIGN-ITEM4-AMENDMENT3.md Ruling 1 adjudicated it: the 3-op fit on the
     UNROTATED amplitude is RETIRED as the production SI extractor (the
     unrotated Majorana-crossed monomials project a spurious scalar onto O_S,
     probeH), the full-basis fit is production, and the shipping guard is the
     THREE-INSTRUMENT cross-check (SD-SI-CROSS-INSTRUMENT-DISAGREE, enforced
     inside projectOperators / projInstrumentAssert above).  si_shift_rel
     remains REPORTED (a ~100% shift is the EXPECTED signature of the retired
     fit's pollution; a small shift would now be the anomaly worth reading). *)
  WriteString["stderr",
    "run_eval_sd: si_shift_rel=" <> ToString[proj["si_shift_rel"], InputForm] <>
    " (retired 3-op fit vs production full-basis; REPORT ONLY per AMENDMENT3 " <>
    "Ruling 1 — cross-instrument guard is the shipping gate)\n"];

  cScalarProd = proj["C_scalar_production"];
  cTw2Sum = proj["C_twist2_sum"];
  cTw2Dif = proj["C_twist2_dif"];

  (* REPORT the production measurements immediately (stderr): a later named
     refusal (velocity/UV/reopen) must not orphan the measured coefficients —
     the falsifier legs (AMENDMENT3 Ruling 3) read C_scalar_production and the
     cross-instrument triple from THESE lines even when nothing ships. *)
  WriteString["stderr",
    "run_eval_sd: PRODUCTION C_scalar_production=" <>
    ToString[cScalarProd, InputForm] <>
    " C_twist2_sum=" <> ToString[cTw2Sum, InputForm] <>
    " C_twist2_dif=" <> ToString[cTw2Dif, InputForm] <> "\n" <>
    "run_eval_sd: CROSS-INSTRUMENT threeop_rotated=" <>
    ToString[proj["cross_instrument"]["threeop_rotated"], InputForm] <>
    " transfer_R_S_S=" <> ToString[proj["cross_instrument"]["transfer_R_S_S"], InputForm] <>
    " forward_R_S_S=" <> ToString[proj["cross_instrument"]["forward_R_S_S"], InputForm] <>
    " max_pairwise_diff=" <> ToString[proj["cross_instrument"]["max_pairwise_diff"], InputForm] <>
    " tol=" <> ToString[proj["cross_instrument"]["tolerance"], InputForm] <> "\n"];

  (* ---- VELOCITY STABILITY (AMENDMENT3 Ruling 2 replacement bar) --------------
     The transfer dictionary is honestly UNMEASURABLE at v/10 (cond ~ 1/v^2 ->
     4.8e6; ratified named refusal, Ruling 4c) — its refusal is RECORDED, not
     fatal, and never retried by loosening cond.  Velocity stability of the
     PRODUCTION coefficients is measured on the green-guarded legs
     (productionVLeg: 3-op-on-rotated + contracted twist-2, each under its own
     fatal rank/cond/identifiability guards).  The pre-registered reopen
     trigger — any coefficient carrying > 1% of |f_N| drifting > 1% relative
     under a green-guarded v change, or |Delta C_scalar| > 6e-10 ABSOLUTE — is
     adjudicated AFTER the nucleon contraction below (it needs the f_N
     shares); the measurements happen here. *)
  Module[{projV = projectOperators[Mnum, abbrF, mchi, mq, 0.1]},
    transferV10Outcome = If[TrueQ[projV["ok"]],
      <|"measurable" -> True,
        "C_scalar_full_drift_rel" ->
          If[Abs[proj["C_scalar_full"]] < 1*^-300, Abs[projV["C_scalar_full"]],
            Abs[(projV["C_scalar_full"] - proj["C_scalar_full"])/
              proj["C_scalar_full"]]]|>,
      <|"measurable" -> False,
        "outcome" -> "UNMEASURABLE: " <> ToString[projV["reason"]] <>
          " (named outcome per AMENDMENT3 Ruling 4c; transfer conditioning " <>
          "collapses ~1/v^2, never retried by loosening bars)"|>]];
  prodV = productionVLeg[Mnum, abbrF, mchi, mq, 0.1];
  If[! TrueQ[prodV["ok"]],
    WriteString["stderr",
      "run_eval_sd: SD-VELOCITY-UNSTABLE production velocity leg refused: " <>
      ToString[prodV["reason"]] <> " " <> ToString[Lookup[prodV, "detail", ""]] <> "\n" <>
      "  The GREEN-GUARDED production legs (3-op-on-rotated + contracted\n" <>
      "  twist-2) could not be built at v/10 under their own guards, so the\n" <>
      "  Ruling-2 replacement stability bar is unmeasurable.  Nothing ships.\n"];
    Exit[3]];
  driftCscalarAbs = Max[
    Abs[prodV["threeop_rotated_coeffs"]["C_scalar"] -
        proj["threeop_rotated_coeffs"]["C_scalar"]],
    Abs[prodV["contracted_coeffs"]["C_scalar"] -
        proj["C_scalar_contracted_rotated"]]];
  driftTw2SumRel = If[Abs[cTw2Sum] < 1*^-300,
    Abs[prodV["contracted_coeffs"]["C_twist2_sum"]],
    Abs[(prodV["contracted_coeffs"]["C_twist2_sum"] - cTw2Sum)/cTw2Sum]];
  vlegNote = "green-guarded v/10 legs: 3-op-on-rotated (forward samples) + " <>
    "contracted twist-2 (cond " <> ToString[prodV["production_basis_cond"], InputForm] <> ")";

  (* ---- PER-COEFFICIENT UV-residue check (Decision 2, load-bearing) -----------
     The SD reduced core carries DIVERGENT B0i heads; setdelta/setmudim variation
     must leave every projected coefficient invariant (nonzero residue = a
     genuine 1/eps that the 1PI-core-only scope failed to cancel).  Assert
     per-coefficient: setdelta-residue < 1e-10 rel, setmudim-residue < 1e-6 rel.
     projAt re-projects the amplitude re-evaluated at a different setdelta/setmudim
     (first executable on live SD data — Decision 2's guard). *)
  (* PRODUCTION coefficient set for the UV/scale gate (AMENDMENT3 Ruling 1):
     the f_N inputs C_scalar_production and C_twist2_sum, plus the retired-fit
     names for continuity reporting.  ABSOLUTE FLOOR on the C_scalar family:
     the shipped C_scalar carries a declared +-6e-10 rank-2 band, so a
     scheme-variation wobble INSIDE that band cannot change any shipped
     statement — the relative bar alone would spuriously refuse a ~1e-10
     near-cancellation coefficient over ~1e-16 absolute scheme noise. *)
  projAt[delta_, mudim_] := Module[{p = projectOperators[evalAmp[delta, mudim],
      abbrF, mchi, mq]},
    projInstrumentAssert[p];
    If[! TrueQ[p["ok"]],
      WriteString["stderr", "run_eval_sd: SD-PROJECTION-FAILED (UV/scale leg) " <>
        ToString[p["reason"]] <> "\n"]; Exit[3]];
    p];
  coeffNames = {"C_scalar_production", "C_twist2_sum", "C_scalar", "C_twist2",
    "C_chi_vector"};
  Module[{p1 = projAt[1.0*^4, 1], p2 = projAt[0, 100.], relD, relS, absFloor,
      okD, okS},
    absFloor[c_] := If[StringStartsQ[c, "C_scalar"], 6.0*^-10, 0.];
    relD = Max[Table[
      If[Abs[proj[c]] < 1*^-300, Abs[p1[c] - proj[c]],
         Abs[(p1[c] - proj[c])/proj[c]]], {c, coeffNames}]];
    relS = Max[Table[
      If[Abs[proj[c]] < 1*^-300, Abs[p2[c] - proj[c]],
         Abs[(p2[c] - proj[c])/proj[c]]], {c, coeffNames}]];
    okD = AllTrue[coeffNames, (Abs[p1[#] - proj[#]] <=
      Max[1.0*^-10 Abs[proj[#]], absFloor[#]]) &];
    okS = AllTrue[coeffNames, (Abs[p2[#] - proj[#]] <=
      Max[1.0*^-6 Abs[proj[#]], absFloor[#]]) &];
    uvResidue = relD; scaleResidue = relS;
    uvOkQ = okD && okS];
  setdelta[0]; setmudim[1];

  finiteQ = AllTrue[{cScalar, cTw, cChiV, cScalarProd, cTw2Sum},
              (NumberQ[#] && Abs[#] < Infinity) &] && uvOkQ;

  If[! finiteQ,
    WriteString["stderr",
      "run_eval_sd: LOOPTOOLS_AMPLITUDE_NONFINITE per-coefficient UV/scale residue " <>
      "(setdelta_rel=" <> ToString[uvResidue, InputForm] <> ", setmudim_rel=" <> ToString[scaleResidue, InputForm] <>
      ") — the 1PI-core-only scope did not cancel a 1/eps; extend to the\n" <>
      "  15-topology set with explicit counterterms (STEP3-DESIGN.md Decision 2).\n"]];

  nPV = Length[Cases[terms, (B0i | C0i | D0i)[__], Infinity]];

  (* ---- TRIANGLE-SECTOR 3-op fit (heavy-quark C_Q, Decision A4) ---------------
     threeOpFit is arithmetic-identical to the projectOperators production leg,
     so at the canonical point the triangle-only C_scalar below reproduces the
     continuity fixture -1.2831509485455282e-7 BIT-FOR-BIT (the falsifier
     prediction (i) check rides on this value).  C_Q = C_scalar(triangle)/m_q
     is the m_q-normalized flavor-universal h-exchange coefficient (the SVZ
     heavy-quark theorem input; cross-flavor equality assert is round-2 item
     (iii)).  Its v-stability is measured here for the reopen adjudication. *)
  chainDefsA = Association[abbrF];
  fsymsA = Keys[chainClass[abbrF]];
  triFit = threeOpFit[Mtri, chainDefsA, fsymsA, mchi, mq];
  cTri = triFit["coeffs"]["C_scalar"];
  triFitV = threeOpFit[Mtri, chainDefsA, fsymsA, mchi, mq, 0.1];
  cQuniv = cTri/mq;
  cQdrift = If[Abs[cTri] < 1*^-300, Abs[triFitV["coeffs"]["C_scalar"]],
    Abs[(triFitV["coeffs"]["C_scalar"] - cTri)/cTri]];
  WriteString["stderr", "run_eval_sd: C_scalar_triangle=" <>
    ToString[Re[cTri], InputForm] <> " C_Q_universal=" <>
    ToString[Re[cQuniv], InputForm] <> " triangle_v10_drift_rel=" <>
    ToString[cQdrift, InputForm] <> "\n"];

  (* ---- NUCLEON CONTRACTION, DRIVER-SIDE (Decision A5 / AMENDMENT3 Ruling 1) --
     match_nucleon.py stays byte-untouched (it owns only (4/pi) mu^2 f^2; this
     block owns the contraction, per its module docstring's division of labor).
     Formula (Hisano-Ishiwata-Nagata arXiv:1104.0228 Eqs. (6)-(8) convention;
     C^(i) = g^(i)/m_chi, see sd_projection.wl section 3c):
       f_N/m_N = Sum_{q=u,d,s} f_Tq^N C_q
               + (2/27) f_TG^N Sum_{Q=c,b,t} C_Q
               + (3/4) m_chi Sum_q [q^N(2)+qbar^N(2)] (C_q^(1)+C_q^(2))
     Constants transcribed from eval/2506.19062_wimps_blind_spots/constants.py
     (measured data, not physics reimplementation):
       f_Tq (Hoferichter et al.): F_U_P=0.0153 F_D_P=0.0191 F_S_P=0.0447,
         F_U_N=0.0110 F_D_N=0.0273 F_S_N=0.0447; f_TG^N = 1 - Sum f_q^N.
       Second moments Q2_*/QBAR2_* (proton): u 0.22/0.034, d 0.11/0.036,
         s 0.026 (q=qbar), c 0.019, b 0.012.  NEUTRON moments = isospin
         u<->d swap of the proton values (s,c,b unchanged) — standard, noted.
       CAVEAT (reported, not tuned): constants.py labels the moments mu=2 GeV;
       AMENDMENT3 Ruling 1 directs their use as the mu=m_Z inputs of the
       Hisano convention — the discrepancy is an anchor-leg (item (v)) matter.
     THIS LEG measures flavor d ONLY (per-flavor u/s runs are round-2 item
     (iii)): the light-quark scalar and twist-2 sums below carry the d term
     alone, flagged in flavors_measured — a PARTIAL f_N, honestly labeled.
     The light-quark scalar term uses the MEASURED C_q = C_scalar/m_q (a ~0 is
     a value, not a zero by hand) with the +-6e-10 rank-2 band propagated into
     f_N.  sigma_SI ships as a TWO-VALUE BRACKET (with / without the C_G
     gluon term): C_Q carries full triangle strength — its box partner is the
     out-of-scope two-loop gluon box — so a single unbracketed floor number is
     FORBIDDEN until the Hisano pure-doublet anchor adjudicates (Ruling 1). *)
  nucleon = Module[{fT, fTG, mom2d, mNs, cq, cqBand, terms2, gev2cm2, out},
    fT = <|"p" -> <|"u" -> 0.0153, "d" -> 0.0191, "s" -> 0.0447|>,
           "n" -> <|"u" -> 0.0110, "d" -> 0.0273, "s" -> 0.0447|>|>;
    fTG = <|"p" -> 1. - 0.0153 - 0.0191 - 0.0447,
            "n" -> 1. - 0.0110 - 0.0273 - 0.0447|>;
    (* [q(2)+qbar(2)] for the d quark; neutron = proton u-moments (isospin) *)
    mom2d = <|"p" -> 0.11 + 0.036, "n" -> 0.22 + 0.034|>;
    mNs = <|"p" -> 0.93827, "n" -> 0.93957|>;
    gev2cm2 = 0.3894*^-27;
    cq = Re[cScalarProd]/mq;         (* m_q-normalized MEASURED C_q, flavor d *)
    cqBand = 6.0*^-10/mq;            (* rank-2 band, propagated *)
    out = Association @@ Table[Module[
        {scalarD, scalarBand, gluon, tw2, fom, fomNoCG, f, fNoCG, fLo, fHi,
         fNoCGLo, fNoCGHi, muN, sig},
        scalarD = fT[nuc]["d"] cq;
        scalarBand = fT[nuc]["d"] cqBand;
        gluon = (2./27.) fTG[nuc] 3. Re[cQuniv];
        tw2 = (3./4.) mchi mom2d[nuc] Re[cTw2Sum];
        fom = scalarD + gluon + tw2;
        fomNoCG = scalarD + tw2;
        f = mNs[nuc] fom;          fLo = mNs[nuc] (fom - scalarBand);
        fHi = mNs[nuc] (fom + scalarBand);
        fNoCG = mNs[nuc] fomNoCG;  fNoCGLo = mNs[nuc] (fomNoCG - scalarBand);
        fNoCGHi = mNs[nuc] (fomNoCG + scalarBand);
        muN = mchi mNs[nuc]/(mchi + mNs[nuc]);
        sig[ff_] := (4./Pi) muN^2 ff^2 gev2cm2;
        nuc -> <|
          "terms_f_over_mN" -> <|"scalar_d" -> scalarD, "scalar_d_band_abs" -> scalarBand,
            "gluon_CG" -> gluon, "twist2_d" -> tw2|>,
          "shares_with_CG" -> If[Abs[fom] < 1*^-300, <||>,
            <|"scalar_d" -> Abs[scalarD/fom], "gluon_CG" -> Abs[gluon/fom],
              "twist2_d" -> Abs[tw2/fom]|>],
          "shares_without_CG" -> If[Abs[fomNoCG] < 1*^-300, <||>,
            <|"scalar_d" -> Abs[scalarD/fomNoCG], "twist2_d" -> Abs[tw2/fomNoCG]|>],
          "f_gev2_with_CG" -> f, "f_gev2_with_CG_band" -> {fLo, fHi},
          "f_gev2_without_CG" -> fNoCG, "f_gev2_without_CG_band" -> {fNoCGLo, fNoCGHi},
          "sigma_SI_cm2_with_CG" -> sig[f],
          "sigma_SI_cm2_with_CG_band" -> Sort[{sig[fLo], sig[fHi]}],
          "sigma_SI_cm2_without_CG" -> sig[fNoCG],
          "sigma_SI_cm2_without_CG_band" -> Sort[{sig[fNoCGLo], sig[fNoCGHi]}]|>],
      {nuc, {"p", "n"}}];
    out];

  (* diagnostic report of the contraction terms (stderr; sigma itself is NOT
     printed here — it ships only through the guarded JSON path below) *)
  WriteString["stderr", "run_eval_sd: F_N-TERMS(p, f/m_N) scalar_d=" <>
    ToString[nucleon["p"]["terms_f_over_mN"]["scalar_d"], InputForm] <>
    " gluon_CG=" <> ToString[nucleon["p"]["terms_f_over_mN"]["gluon_CG"], InputForm] <>
    " twist2_d=" <> ToString[nucleon["p"]["terms_f_over_mN"]["twist2_d"], InputForm] <>
    " (band_abs=" <> ToString[nucleon["p"]["terms_f_over_mN"]["scalar_d_band_abs"], InputForm] <>
    ")\n"];

  (* ---- KINEMATICS REOPEN ADJUDICATION (AMENDMENT3 Ruling 2 replacement bar) --
     Per-config kinematics REOPENS — and this driver refuses to ship — if any
     production coefficient carrying > 1% of |f_N| (either bracket member,
     either nucleon) drifts > 1% relative under the green-guarded v change, or
     if |Delta C_scalar| > 6e-10 ABSOLUTE under any green-guarded v change.
     Report, never tune. *)
  reopenChecks = Module[{share, checks = {}},
    share[term_] := Max[Table[Max[
        Lookup[nucleon[nuc]["shares_with_CG"], term, 0.],
        Lookup[nucleon[nuc]["shares_without_CG"], term, 0.]],
      {nuc, {"p", "n"}}]];
    If[driftCscalarAbs > 6.0*^-10,
      AppendTo[checks, "C_scalar ABSOLUTE v-drift " <>
        ToString[driftCscalarAbs, InputForm] <> " > 6e-10"]];
    If[share["twist2_d"] > 0.01 && driftTw2SumRel > 0.01,
      AppendTo[checks, "C_twist2_sum carries " <> ToString[share["twist2_d"]] <>
        " of f_N and drifts " <> ToString[driftTw2SumRel, InputForm] <> " > 1% at v/10"]];
    If[share["gluon_CG"] > 0.01 && cQdrift > 0.01,
      AppendTo[checks, "C_Q(triangle) carries " <> ToString[share["gluon_CG"]] <>
        " of f_N(with-CG) and drifts " <> ToString[cQdrift, InputForm] <> " > 1% at v/10"]];
    (* C_scalar carries NO relative-drift check by design: Ruling 2 replaced it
       with the ABSOLUTE 6e-10 bar above (a relative bar on a noise-scale
       coefficient did not survive its anchor's retirement). *)
    checks];
  If[reopenChecks =!= {},
    WriteString["stderr",
      "run_eval_sd: SD-KINEMATICS-REOPEN-TRIGGERED " <>
      StringRiffle[reopenChecks, " | "] <> "\n" <>
      "  The pre-registered AMENDMENT3 Ruling 2 replacement trigger fired:\n" <>
      "  per-config kinematics REOPENS and this driver refuses to ship a\n" <>
      "  sigma_SI whose inputs are velocity-biased.  Report upstream; do not\n" <>
      "  tune the bars.\n"];
    Exit[3]];

  jsonAssoc = <|
    "schema" -> "looptools_sd_coefficients/v2",
    "model" -> "singlet_doublet",
    "point_id" -> "singlet-doublet-dm" <> ToString[mchi],
    "m_dm_gev" -> mchi,
    "external_quark" -> "d",
    "sigma_provisional" -> True,
    "amplitude" -> <|
      "finite" -> finiteQ,
      "uv_pole_residue" -> uvResidue,
      "scale_residue" -> scaleResidue,
      "ir_pole_residue" -> 0.0,
      "completeness_rel_residual" -> complResidual,
      "gauge_parameter_dependence" -> Null (* Rxi variation deferred (Decision 2) *)
    |>,
    "a6_amended" -> <|  (* AMENDMENT2 Rulings 1+4 + AMENDMENT3 Ruling 1/2 bars,
                           all green (each is a hard Exit[3] guard above) *)
      "full_basis_completeness_rel_residual" ->
        proj["full_basis_completeness_rel_residual"],
      "full_basis_completeness_tol" -> $fullCompletenessTol,
      "si_shift_rel" -> proj["si_shift_rel"],
      "si_shift_status" -> "REPORT ONLY (AMENDMENT3 Ruling 1: 3-op retired; " <>
        "~100% shift is the expected signature of the retired fit's pollution)",
      "si3_completeness_rel_residual" -> complResidual,
      "rotation_exactness_max" -> proj["rotation_exactness_max"],
      "basis_rank" -> proj["basis_rank"],
      "basis_n_columns" -> proj["basis_n_columns"],
      "basis_cond" -> proj["basis_cond"],
      "identifiability_max_err" -> proj["identifiability_max_err"],
      "monomial_worst" -> proj["monomial_worst"],
      (* AMENDMENT3 Ruling 1 shipping guard state (green if we got here) *)
      "cross_instrument" -> <|
        "threeop_rotated_re" -> Re[proj["cross_instrument"]["threeop_rotated"]],
        "threeop_rotated_im" -> Im[proj["cross_instrument"]["threeop_rotated"]],
        "transfer_R_S_S_re" -> Re[proj["cross_instrument"]["transfer_R_S_S"]],
        "transfer_R_S_S_im" -> Im[proj["cross_instrument"]["transfer_R_S_S"]],
        "forward_R_S_S_re" -> Re[proj["cross_instrument"]["forward_R_S_S"]],
        "forward_R_S_S_im" -> Im[proj["cross_instrument"]["forward_R_S_S"]],
        "max_pairwise_diff" -> proj["cross_instrument"]["max_pairwise_diff"],
        "tolerance" -> proj["cross_instrument"]["tolerance"]|>,
      "forward_instrument" -> <|
        "n_retained" -> proj["forward_instrument"]["n_retained"],
        "n_null_columns" -> proj["forward_instrument"]["n_null_columns"],
        "retained_cond" -> proj["forward_instrument"]["retained_cond"],
        "retained_ident_err" -> proj["forward_instrument"]["retained_ident_err"],
        "completeness_rel_residual" ->
          proj["forward_instrument"]["completeness_rel_residual"]|>,
      "production_basis_cond" -> proj["production_basis_cond"],
      "production_basis_ident_err" -> proj["production_basis_ident_err"],
      (* AMENDMENT3 Ruling 2 replacement-bar measurements (adjudicated above) *)
      "velocity" -> <|
        "transfer_instrument_v10" -> transferV10Outcome,
        "production_leg_note" -> vlegNote,
        "C_scalar_v10_drift_abs" -> driftCscalarAbs,
        "C_scalar_abs_bar" -> 6.0*^-10,
        "C_twist2_sum_v10_drift_rel" -> driftTw2SumRel,
        "C_Q_triangle_v10_drift_rel" -> cQdrift|>
    |>,
    "out_of_span_diagnostics" -> <|  (* Ruling 2: DIAGNOSTICS ONLY — never
        matched, never a cross-section; only C_scalar/C_twist2/C_G flow onward *)
      "full_basis_coeffs_re" -> Map[Re, proj["full_basis_coeffs"]],
      "absorbed_norm_shares" -> proj["absorbed_norm_shares"],
      "monomial_residuals" -> proj["monomial_residuals"],
      "monomial_contributions" -> proj["monomial_contributions"]
    |>,
    "dd_expansion" -> <|
      "enabled" -> $ddExpansion,
      "method" -> "box small-momentum DD (rank-1 collinear {g,uu} basis) -> " <>
                  "scalar D0/C0/B0; DESIGN-ITEM4.md Decision A1",
      "ov_order" -> "leading-DD (v=0) collinear reconstruction; rank-2 method " <>
                    "accuracy budget ~3e-3 at TEPS",
      "box_head_census_before" -> boxCensusBefore,
      "gram_monitor" -> If[$ddExpansion, ddMonitorSummary[], <||>]
    |>,
    "wilson_coefficients" -> <|
      (* PRODUCTION (AMENDMENT3 Ruling 1): C_scalar = full-basis R_S_S at
         canonical v; convention: coefficient of (chibar chi)(qbar q) — the
         m_q-normalized Hisano f_q is C_scalar/m_q (emitted as C_q_mq_norm).
         Im(C_scalar) is measured transfer-instrument leakage, |Im| < the
         6e-10 band (the other two instruments carry Im ~ 1e-14). *)
      "C_scalar"    -> Re[cScalarProd],
      "C_scalar_im" -> Im[cScalarProd],
      "C_scalar_band_abs" -> 6.0*^-10,
      "C_q_mq_norm" -> Re[cScalarProd]/mq,
      "C_twist2_sum" -> Re[cTw2Sum],   (* = C^(1)+C^(2) = (g1+g2)/m_chi; the f_N input *)
      "C_twist2_dif" -> Re[cTw2Dif],   (* DIAGNOSTIC: intrinsically ill-resolved split *)
      "C_twist2_g1" -> Re[proj["C_twist2_g1"]],
      "C_twist2_g2" -> Re[proj["C_twist2_g2"]],
      "C_scalar_triangle" -> Re[cTri],
      "C_scalar_triangle_str" -> ToString[Re[cTri], InputForm], (* fixture; full precision *)
      "C_Q_universal" -> Re[cQuniv],   (* triangle/m_q: heavy-quark SVZ input *)
      "C_chi_vector" -> Re[proj["C_chi_vector_rotated"]], (* Majorana diagnostic: ~0 *)
      "retired_3op_fit" -> <|  (* continuity report ONLY (AMENDMENT3 Ruling 1) *)
        "C_scalar" -> Re[cScalar], "C_scalar_im" -> Im[cScalar],
        "C_twist2" -> Re[cTw], "C_chi_vector" -> Re[cChiV]|>
    |>,
    "nucleon_matching" -> <|
      "status" -> "driver-side A5 contraction (match_nucleon.py byte-untouched)",
      "convention" -> "Hisano arXiv:1104.0228 Eqs.(6)-(8); C^(i)=g^(i)/m_chi; " <>
        "f_q = C_scalar/m_q (m_q-normalized); moments transcribed from " <>
        "eval/2506.19062_wimps_blind_spots/constants.py",
      "moments_scale_caveat" -> "constants.py labels the second moments mu=2 GeV; " <>
        "AMENDMENT3 Ruling 1 directs their use as the mu=m_Z Hisano inputs — " <>
        "discrepancy deferred to the Hisano-anchor leg (round-2 item (v))",
      "flavors_measured" -> {"d"},
      "flavors_pending" -> {"u", "s"},
      "partial_fN_caveat" -> "light-quark scalar + twist-2 sums carry the " <>
        "MEASURED d flavor only (item (iii) adds u,s); heavy-quark gluon term " <>
        "carries all of c,b,t via the flavor-universal triangle C_Q",
      "neutron_moments" -> "isospin u<->d swap of proton values",
      "CG_bracket_caveat" -> "C_Q is NOT cancelled: its box partner is the " <>
        "declared-out-of-scope two-loop gluon box, hence the with/without-CG " <>
        "TWO-VALUE BRACKET (AMENDMENT3 Ruling 1); single floor number forbidden " <>
        "until the Hisano pure-doublet anchor",
      "normalization_caveat" -> "global amplitude-to-L_eff normalization is " <>
        "unanchored until the Hisano pure-doublet leg; sigma_provisional on " <>
        "BOTH bracket values",
      "proton" -> nucleon["p"],
      "neutron" -> nucleon["n"]
    |>,
    "loop_topologies" -> {"chi_triangle_IRR2", "W_box_IRR3", "crossed_box_IRR4"},
    "looptools_version" -> "2.16",
    "n_pv_calls" -> nPV,
    "n_diagrams" -> Length[terms],
    "pv_heads_used" -> {"B0i", "C0i", "D0i"},
    "_diagnostics" -> <|
      "method" -> "Majorana-chi + down-quark NUMERICAL basis-vector projection " <>
                  "(Decision 3.2): chains read from the real Abbr[] WeylChains, " <>
                  "evaluated on an explicit spinor basis, operator coefficients " <>
                  "least-squares-solved (NOT hard-coded index blocks, NOT the " <>
                  "2HDM+a static spin-summed collapse)",
      "gamma5_scheme" -> "naive",
      "znmix_convention" -> "ZN = ZNMIX + I*IMZNMIX",
      "yh_block" -> "BSMPARAMS(3,4) preferred, MINPAR fallback",
      "chain_map" -> "SD real Abbr: F1,F4=chi-scalar; F2,F3=quark-scalar; " <>
                     "F13,F14=chi-vector; F15,F16=quark-vector(twist-2); " <>
                     "F5-F12,F17,F18=mixed Fierz",
      "note" -> "PARTIAL f_N / sigma_SI bracket (AMENDMENT3 Ruling 1): flavor d " <>
                "measured; per-flavor u,s runs are round-2 item (iii); Hisano " <>
                "pure-doublet anchor is item (v).  sigma_provisional on both " <>
                "bracket values.",
      "n_triangle_terms" -> nTriTerms,
      "n_terms" -> Length[terms]
    |>
  |>;

  writeEvalOutput[outPath, jsonAssoc];
  Print["run_eval_sd: wrote ", outPath, " (finite=", finiteQ,
        ", C_scalar_production=", Re[cScalarProd],
        ", C_twist2_sum=", Re[cTw2Sum],
        ", C_scalar_triangle=", Re[cTri],
        ", sigma_SI_p_with_CG=", nucleon["p"]["sigma_SI_cm2_with_CG"],
        ", sigma_SI_p_without_CG=", nucleon["p"]["sigma_SI_cm2_without_CG"],
        ", completeness_resid=", complResidual, ")"];
  Exit[0]
]
