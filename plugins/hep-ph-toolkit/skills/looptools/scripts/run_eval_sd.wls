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

   Output: per-operator Wilson coefficients (schema looptools_sd_coefficients/v1).
   NO sigma_SI — nucleon matching (twist-2 + 2/27-gluon contractions through the
   SD Higgs sector) is build-order item 4.

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

(* ---- model-agnostic plumbing (argv, FormCalc+LoopTools load, self-test,
        evalTermCommon / emitUnboundGuard / writeEvalOutput). ------------------- *)
$scriptDir = DirectoryName[
  If[$InputFileName =!= "" && $InputFileName =!= Null, $InputFileName,
     $ScriptCommandLine[[1]]]];
Get[FileNameJoin[{$scriptDir, "run_eval_common.wl"}]];
Get[FileNameJoin[{$scriptDir, "sd_projection.wl"}]];

Module[{
    ampPath = $ampPath, pointPath = $pointPath, ffPreset = $ffPreset,
    outPath = $outPath, ltPrefix = $ltPrefix,
    point, masses, params, getMass, getParam, getParamAny,
    mchi1, mchi2, mchi3, mchiM, mh, mZ, mW, mchi, mq,
    ZNm, IMZNm, UMm, UPm, ZDLm, ZDRm, ZULm, ZURm, Yum, Ydm,
    yh1v, yh2v, g1v, g2v, g3v, Lamv, PhaseFSv, vvSMv, ctw, stw,
    amp, subexpr, ampBody, abbr, abbrF, terms, mkNum, extIdx, extPins,
    evalAmp, Mnum, resid, proj, projAt, coeffNames,
    cScalar, cTw, cChiV, uvResidue, scaleResidue, finiteQ, complResidual,
    nPV, jsonAssoc, bindGuard, unbound, matrixUnbound
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

  (* Evaluate the full amplitude to an F-LINEAR numeric form.  Fp = {} keeps the
     external chains symbolic (that IS the coefficient-level projection); the
     SumOver internal-eigenstate/generation sums are expanded exactly by
     evalTermCommon (R3: no gen pinning). *)
  evalAmp[delta_, mudim_] := Total[Table[
    evalTermCommon[terms[[k]], subexpr, {}, mkNum[delta, mudim], extPins],
    {k, Length[terms]}]];

  Mnum = evalAmp[0, 1];

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

  (* ---- COMPLETENESS GUARD (F2, Decision) -------------------------------------
     M - Sum_op c_op O_op must be ~0 (relative, to $completenessTol); a larger
     residual means content the recognized SI set does not span -> fail loud, do
     not emit a floor built on a partial fit.  Do NOT assume the residual is a
     particular physics operator: on the real amp the PR #33 review showed no
     Fierz-complete bilinear set spans it (projection/kinematics artifact
     suspected — see the guard message). *)
  If[! TrueQ[proj["completeness_ok"]],
    WriteString["stderr",
      "run_eval_sd: SD-PROJECTION-INCOMPLETE completeness_rel_residual=" <>
      ToString[complResidual] <> " (tol=" <> ToString[$completenessTol] <> ")\n" <>
      "  The recognized operator set {scalar, twist-2, chi-vector} does NOT span\n" <>
      "  the amplitude at the sampled kinematics: M - Sum c_op O_op is non-zero.\n" <>
      "  The out-of-span content is NOT identified (PR #33 review: no Fierz-\n" <>
      "  complete bilinear operator set spans it either; ||M|| scale anomaly +\n" <>
      "  unphysical-lambda PV warnings suggest a static-coefficient / off-axis-\n" <>
      "  chain kinematic inconsistency).  Do NOT interpret the residual as\n" <>
      "  physics; resolving it is the mandatory next work item before item 4.\n"];
    Exit[3]];

  (* ---- PER-COEFFICIENT UV-residue check (Decision 2, load-bearing) -----------
     The SD reduced core carries DIVERGENT B0i heads; setdelta/setmudim variation
     must leave every projected coefficient invariant (nonzero residue = a
     genuine 1/eps that the 1PI-core-only scope failed to cancel).  Assert
     per-coefficient: setdelta-residue < 1e-10 rel, setmudim-residue < 1e-6 rel.
     projAt re-projects the amplitude re-evaluated at a different setdelta/setmudim
     (first executable on live SD data — Decision 2's guard). *)
  projAt[delta_, mudim_] := projectOperators[evalAmp[delta, mudim], abbrF, mchi, mq];
  coeffNames = {"C_scalar", "C_twist2", "C_chi_vector"};
  Module[{p1 = projAt[1.0*^4, 1], p2 = projAt[0, 100.], relD, relS},
    relD = Max[Table[
      If[Abs[proj[c]] < 1*^-300, Abs[p1[c] - proj[c]],
         Abs[(p1[c] - proj[c])/proj[c]]], {c, coeffNames}]];
    relS = Max[Table[
      If[Abs[proj[c]] < 1*^-300, Abs[p2[c] - proj[c]],
         Abs[(p2[c] - proj[c])/proj[c]]], {c, coeffNames}]];
    uvResidue = relD; scaleResidue = relS];
  setdelta[0]; setmudim[1];

  finiteQ = AllTrue[{cScalar, cTw, cChiV}, (NumberQ[#] && Abs[#] < Infinity) &] &&
            (uvResidue < 1.0*^-10) && (scaleResidue < 1.0*^-6);

  If[! finiteQ,
    WriteString["stderr",
      "run_eval_sd: LOOPTOOLS_AMPLITUDE_NONFINITE per-coefficient UV/scale residue " <>
      "(setdelta_rel=" <> ToString[uvResidue] <> ", setmudim_rel=" <> ToString[scaleResidue] <>
      ") — the 1PI-core-only scope did not cancel a 1/eps; extend to the\n" <>
      "  15-topology set with explicit counterterms (STEP3-DESIGN.md Decision 2).\n"]];

  nPV = Length[Cases[terms, (B0i | C0i | D0i)[__], Infinity]];

  jsonAssoc = <|
    "schema" -> "looptools_sd_coefficients/v1",
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
    "wilson_coefficients" -> <|
      "C_scalar"    -> Re[cScalar],
      "C_scalar_im" -> Im[cScalar],
      "C_twist2"    -> Re[cTw],
      "C_chi_vector" -> Re[cChiV] (* Majorana diagnostic: expected ~0 *)
    |>,
    "nucleon_matching" -> "deferred_item4",
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
      "note" -> "Provisional: NO nucleon matching, NO sigma_SI (build-order item 4). " <>
                "External quark pinned to representative down; per-flavor (u,d,s) runs " <>
                "and the C^(1)/C^(2) twist-2 split are item 4."
    |>
  |>;

  writeEvalOutput[outPath, jsonAssoc];
  Print["run_eval_sd: wrote ", outPath, " (finite=", finiteQ,
        ", C_scalar=", Re[cScalar], ", C_twist2=", Re[cTw],
        ", completeness_resid=", complResidual, ")"];
  Exit[0]
]
