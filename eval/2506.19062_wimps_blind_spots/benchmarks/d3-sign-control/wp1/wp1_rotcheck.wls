#!/usr/bin/env wolframscript
(* wp1_rotcheck.wls — W-P1 v2 (instrument repair + re-ruled read-out).

   WHY v2 (v1 declared VOID, named grounds, log committed): v1's stage-1/
   stage-4 evaluated the toy's Fierzed chains by naive unrotated
   chainValueOn substitution.  The vector toy's chains carry Weyl-flag
   layouts (Spinor 5-arg patterns (1,1,1)/(1,2,1), in-in/out-out pairings
   F1..F4) never present in production amplitudes; the naive evaluation is
   outside the projector's validated domain (measured: pipeline/analytic
   ratio spread 0.0017..37292 — not proportional).  The PRODUCTION
   evaluation of this amplitude is the ROTATED monomial path, which ran
   green on this toy (rotation exactness 4.3e-16, 256-dict completeness
   2.0e-15).  v2 therefore compares the ROTATED pipeline values — exactly
   the values production ships coefficients from — against the analytic
   amplitude.

   RE-RULED READ-OUT (coordinator relay of designer post-W-P3 ruling;
   FROZEN HERE BEFORE THE RUN):
   W-P3 proved the CreateFeynAmp FermionSign is CORRECT convention physics
   and class-blind by code; D3's scalar offset c_scalar = -1 is a
   CONVENTION-ALIGNMENT OFFSET, expected, not evidence.  The H-A1 cell is
   GONE.  The decisive read-out is RELATIVE:
     c_vector := config-wise ratio  M_rot_pipeline / M_analytic  for this
     twist-2-carrying (pure vector-exchange) toy, with
     M_analytic = +gchi gq/(t-MV^2) (chibar gamma^mu chi)(qbar gamma_mu q)
     (hand Wick, ToyDiracV.mod header) evaluated on the projector's own
     spinor conventions.
   BARS (frozen): c_vector must be config-CONSTANT (relative spread < 1e-6)
   with |c_vector| within 1e-6 of 1; else VOID (named), no verdict.
   MAP (frozen):
     c_vector = -1  (SAME offset as D3's measured scalar -1: the
        convention constant passes through class-blind)  ->  AGREES-
        RELATIVE  ->  H-A2 path: production's class-specific defect is
        NOT at the amplitude boundary nor class-induced in reduce/rotate;
        it lives elsewhere (W-P2's named suspect remains prime).
     c_vector = +1  (vector/twist-2 channel unflipped while scalar
        flipped: class-specific offset already at toy level)  ->
        PRE-REGISTERED CONTRADICTION-STOP: escalate to design, no
        improvised reconciliation.
   By linearity, once c_vector is constant, EVERY operator component of
   this amplitude (its twist-2 content included) carries the same c —
   the within-toy relative comparison is then automatic; the informative
   relative datum is c_vector vs D3's c_scalar.  Secondary (reported, not
   verdict-bearing): production contracted fits of the SAME rotated values
   and of the analytic values (both signs stated absolutely).

   Args: <amp_reduced.m> <ignored> <preset> <ignored> <ignored> *)

mUlight = 2.16*^-3; mDlight = 4.67*^-3; mSlight = 0.093;
mClight = 1.27;     mBlight = 4.18;     mTlight = 173.4;
TEPS = 1.0*^-4;
$ddExpansion = False;

$scriptDir = "/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-a4f66e3295b1b33b8/plugins/hep-ph-toolkit/skills/looptools/scripts/";
Get[FileNameJoin[{$scriptDir, "run_eval_common.wl"}]];
Get[FileNameJoin[{$scriptDir, "sd_projection.wl"}]];

Module[{mchi, mq, mv, gv, amp, subexpr, ampBody, abbr, abbrF, terms, mkR,
        extIdx, extPins, Mnum, resid, chainDefsP, cc, fsymsP, crules,
        crossedQ, refCfgs, rot, MrotVals, anaVals, ratios, cval, spread,
        prodNames, prodMat, prodColNorms, nprod, pipeSol, anaSol},

  mchi = 132.692344; mq = mDlight; mv = 90.; gv = 1.;

  amp = Quiet[Check[Get[$ampPath], $Failed]];
  If[amp === $Failed, WriteString["stderr", "rotcheck: Get failed\n"]; Exit[1]];
  subexpr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "subexpr"], "subexpr" /. amp, {}];
  ampBody = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "amp"], "amp" /. amp, amp];
  abbr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "abbr"], "abbr" /. amp, {}];
  abbrF = Cases[abbr, HoldPattern[_ -> _WeylChain]];
  terms = List @@ ampBody;

  mkR = {Den[a_, b_] :> 1/(a - b),
         MassFChi[_] -> mchi, MassFd[_] -> mq, MV -> mv,
         gchi -> gv, gq -> gv, GaugeXi[_] -> 1,
         IndexDelta[_, _] -> 1, Mat[_] -> 1, Finite -> 1,
         T -> -TEPS, S -> (mchi + mq)^2, U -> (mchi - mq)^2};
  extIdx = DeleteDuplicates[Cases[terms, SumOver[i_, _, External] :> i, Infinity]];
  extPins = Join[{SumOver[_, _, External] -> 1}, (# -> 1) & /@ extIdx];
  Mnum = Total[Table[
    evalTermCommon[terms[[k]], subexpr, {}, mkR, extPins], {k, Length[terms]}]];
  resid = residualSymbols[Mnum];
  If[Length[resid] > 0,
    Print["rotcheck: UNRESOLVED ", InputForm[resid]]; Exit[3]];

  cc = chainClass[abbrF];
  chainDefsP = Association[Cases[abbrF, (f_ -> wc_WeylChain) :> (f -> wc)]];
  fsymsP = Keys[cc];
  (* byte-identical monomial/crossed construction (projectOperators lines) *)
  crules = Quiet[CoefficientRules[Mnum, fsymsP]];
  crossedQ = Table[Module[{ex = Keys[crules][[t]], ss},
      ss = Flatten[Table[ConstantArray[fsymsP[[i]], ex[[i]]], {i, Length[fsymsP]}]];
      Length[ss] === 2 && ss[[1]] =!= ss[[2]] &&
        barChiMixedQ[chainDefsP[ss[[1]]]] && barChiMixedQ[chainDefsP[ss[[2]]]]],
    {t, Length[crules]}];
  Print["rotcheck: n_monomials = ", Length[crules],
        "  crossed = ", Count[crossedQ, True]];

  refCfgs = referenceConfigs[N[mchi], N[mq], 1.0];
  rot = rotatedMonoVals[chainDefsP, fsymsP, crules, crossedQ, refCfgs, True];
  If[TrueQ[rot["failed"]],
    Print["rotcheck: ROTATION REFUSED (named layout guard) — VOID"]; Exit[4]];
  Print["rotcheck: rotation_exactness = ", InputForm[rot["rot_err_max"]]];
  MrotVals = N[Transpose[rot["mono_vals"]] . Values[crules]];

  anaVals = N[Table[Module[{cv, qvv},
      cv = chiVec[cfg["kin"], cfg["spin"]]; qvv = quarkVec[cfg["kin"], cfg["spin"]];
      -gv*gv/(mv^2 + TEPS) * $mdot[cv, qvv]], {cfg, refCfgs}]];

  ratios = MapThread[If[Abs[#2] < 1*^-8, Nothing, #1/#2] &, {MrotVals, anaVals}];
  cval = Mean[ratios];
  spread = Max[Abs[ratios - cval]]/Abs[cval];
  Print["rotcheck: n_usable = ", Length[ratios], "  c_vector = ", InputForm[cval],
        "  rel spread = ", InputForm[spread]];
  If[spread >= 1*^-6,
    Print["rotcheck: VOID — c_vector not config-constant (bar 1e-6); no verdict"];
    Exit[4]];
  If[Abs[Abs[cval] - 1] >= 1*^-6,
    Print["rotcheck: VOID — |c_vector| = ", InputForm[Abs[cval]],
          " not 1 within 1e-6 (analytic normalization mismatch); no verdict"];
    Exit[4]];

  (* secondary: production contracted fits of the SAME rotated values *)
  prodNames = Keys[$opRefs2];
  prodMat = N[Table[Table[$opRefs2[op][cfg["kin"], cfg["spin"], N[mchi], N[mq]],
    {op, prodNames}], {cfg, refCfgs}]];
  prodColNorms = Norm /@ Transpose[prodMat];
  nprod = Transpose[Transpose[prodMat]/prodColNorms];
  pipeSol = Quiet[LeastSquares[nprod, MrotVals]]/prodColNorms;
  anaSol = Quiet[LeastSquares[nprod, anaVals]]/prodColNorms;
  Print["rotcheck: contracted C_twist2_sum pipeline(rotated) = ",
        InputForm[AssociationThread[prodNames -> pipeSol]["C_twist2_sum"]],
        "  analytic = ",
        InputForm[AssociationThread[prodNames -> anaSol]["C_twist2_sum"]]];
  Print["rotcheck: contracted rel_resid pipeline = ",
        InputForm[Norm[prodMat . pipeSol - MrotVals]/Norm[MrotVals]],
        "  analytic = ",
        InputForm[Norm[prodMat . anaSol - anaVals]/Norm[anaVals]]];

  Print["rotcheck: VERDICT-INPUT c_vector = ", InputForm[cval],
        "  (D3 measured c_scalar = -1)"];
  Print["rotcheck: MAP: c_vector = -1 -> AGREES-RELATIVE -> H-A2 path;",
        " c_vector = +1 -> CONTRADICTION-STOP (escalate)"];
  Print["rotcheck: DONE"];
];
Exit[0]
