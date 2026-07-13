#!/usr/bin/env wolframscript
(* toy_project.wls — D3 stage-by-stage sign trace (AMENDMENT8 Ruling 2).
   Consumes the toy amp_reduced.m (produced by the PRODUCTION
   run_calcfeynamp.wls on the ToyDiracH FeynArts amplitude) and pushes it
   through the FULL production projection (sd_projection.wl projectOperators
   + threeOpFit), reporting the recovered C_scalar sign at every stage where
   a sign could flip:
     stage 0: chain taxonomy + crossed census (expect 0 crossed: Dirac toy)
     stage 1: RAW amplitude value vs the analytic t-channel h-exchange form
              +gchi gq/(Mhh^2 - t) * (chibar chi)(qbar q) on the pipeline's
              own spinor basis (complex ratio reported — catches any overall
              i or -1 in the Amp convention)
     stage 2: unrotated 3-op read-off (threeOpFit) C_scalar
     stage 3: full production read-off (projectOperators): transfer R_S_S,
              rotated-3op, forward instrument
   A-PRIORI: C_scalar = +gchi gq/Mhh^2 = +6.40e-5 (POSITIVE; attractive).
   Args (run_eval_common contract): <amp_reduced.m> <point.json(ignored,
   pass any)> <preset> <out> <lt_prefix> *)

mUlight = 2.16*^-3; mDlight = 4.67*^-3; mSlight = 0.093;
mClight = 1.27;     mBlight = 4.18;     mTlight = 173.4;
TEPS = 1.0*^-4;
$ddExpansion = False;

$scriptDir = "/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-a4f66e3295b1b33b8/plugins/hep-ph-toolkit/skills/looptools/scripts/";
Get[FileNameJoin[{$scriptDir, "run_eval_common.wl"}]];
Get[FileNameJoin[{$scriptDir, "sd_projection.wl"}]];

Module[{mchi, mq, mh, gv, amp, subexpr, ampBody, abbr, abbrF, terms, mkR,
        extIdx, extPins, Mnum, resid, chainDefsP, fsymsP, cc, cfgs, best,
        frule, mval, chiS, qS, analytic, fit3, proj, aPriori},

  mchi = 132.692344; mq = mDlight; mh = 125.; gv = 1.;
  aPriori = gv*gv/(mh^2 + TEPS);   (* t = -TEPS: +6.3999...e-5, POSITIVE *)

  amp = Quiet[Check[Get[$ampPath], $Failed]];
  If[amp === $Failed,
    WriteString["stderr", "toy_project: Get[amp_reduced.m] failed\n"]; Exit[1]];
  subexpr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "subexpr"], "subexpr" /. amp, {}];
  ampBody = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "amp"], "amp" /. amp, amp];
  abbr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "abbr"], "abbr" /. amp, {}];
  abbrF = Cases[abbr, HoldPattern[_ -> _WeylChain]];
  terms = List @@ ampBody;
  Print["toy_project: n_terms = ", Length[terms], " n_chains = ", Length[abbrF]];
  If[abbrF === {}, Print["toy_project: NO WeylChain table"]; Exit[3]];

  (* stage 0: taxonomy + crossed census *)
  cc = chainClass[abbrF];
  Print["toy_project: stage0 chainClass = ", InputForm[cc]];
  Print["toy_project: stage0 unrecognized = ", InputForm[unrecognizedChains[abbrF]]];
  chainDefsP = Association[Cases[abbrF, (f_ -> wc_WeylChain) :> (f -> wc)]];
  fsymsP = Keys[cc];
  Print["toy_project: stage0 crossed-type chains (barChiMixedQ) = ",
        InputForm[Select[fsymsP, barChiMixedQ[chainDefsP[#]] &]],
        "  (expect none material: Dirac toy, direct chi x q chains)"];

  (* numeric rules; SD-driver conventions where they overlap *)
  mkR = {Den[a_, b_] :> 1/(a - b),
         MassFChi[_] -> mchi, MassFd[_] -> mq, Mhh -> mh,
         gchi -> gv, gq -> gv,
         IndexDelta[_, _] -> 1, Mat[_] -> 1, Finite -> 1,
         T -> -TEPS, S -> (mchi + mq)^2, U -> (mchi - mq)^2};
  extIdx = DeleteDuplicates[Cases[terms, SumOver[i_, _, External] :> i, Infinity]];
  extPins = Join[{SumOver[_, _, External] -> 1}, (# -> 1) & /@ extIdx];

  Mnum = Total[Table[
    evalTermCommon[terms[[k]], subexpr, {}, mkR, extPins], {k, Length[terms]}]];
  resid = residualSymbols[Mnum];
  If[Length[resid] > 0,
    Print["toy_project: UNRESOLVED symbols ", InputForm[Take[resid, UpTo[20]]]];
    Exit[3]];

  (* stage 1: raw amplitude vs analytic h-exchange on the pipeline's spinors *)
  cfgs = sampleConfigs[N[mchi], N[mq], 1.0];
  best = First[MaximalBy[cfgs, Module[{kin = #["kin"], spin = #["spin"]},
    Abs[chiScalar[kin, spin] quarkScalar[kin, spin]]] &]];
  Module[{kin = best["kin"], spin = best["spin"]},
    frule = (# -> chainValueOn[chainDefsP[#], kin, spin]) & /@ fsymsP;
    mval = Mnum /. frule;
    chiS = chiScalar[kin, spin]; qS = quarkScalar[kin, spin];
    analytic = aPriori chiS qS;
    Print["toy_project: stage1 M(best cfg) = ", InputForm[mval]];
    Print["toy_project: stage1 analytic +g^2/(mh^2-t)*(chibar chi)(qbar q) = ",
          InputForm[analytic]];
    Print["toy_project: stage1 ratio M/analytic = ", InputForm[mval/analytic],
          "  (a-priori: +1 if Amp==M with L-convention; the complex phase IS",
          " the assembly convention datum)"]];
  (* several configs for robustness *)
  Module[{rs},
    rs = Table[Module[{kin = cfg["kin"], spin = cfg["spin"], fr, mv, an},
        fr = (# -> chainValueOn[chainDefsP[#], kin, spin]) & /@ fsymsP;
        mv = Mnum /. fr;
        an = aPriori chiScalar[kin, spin] quarkScalar[kin, spin];
        If[Abs[an] < 1*^-10, Nothing, mv/an]],
      {cfg, Take[cfgs, 32]}];
    Print["toy_project: stage1 ratio spread over ", Length[rs],
          " configs: min ", InputForm[Min[Abs[rs]]],
          " max ", InputForm[Max[Abs[rs]]],
          " mean-phase ", InputForm[Mean[rs]/Abs[Mean[rs]]]]];

  (* stage 2: unrotated 3-op read-off *)
  fit3 = threeOpFit[Mnum, chainDefsP, fsymsP, mchi, mq];
  Print["toy_project: stage2 threeOpFit C_scalar = ",
        InputForm[fit3["coeffs"]["C_scalar"]],
        "  rel_resid = ", InputForm[fit3["rel_residual"]],
        "  a-priori = +", InputForm[aPriori]];

  (* stage 3: full production read-off *)
  proj = projectOperators[Mnum, abbrF, mchi, mq];
  If[! TrueQ[proj["ok"]],
    Print["toy_project: stage3 projectOperators REFUSED: ", proj["reason"], " ",
          ToString[Lookup[proj, "detail", ""]]];
    Exit[3]];
  Print["toy_project: stage3 C_scalar_production (transfer R_S_S) = ",
        InputForm[proj["C_scalar_production"]]];
  Print["toy_project: stage3 threeop_rotated = ",
        InputForm[proj["cross_instrument"]["threeop_rotated"]],
        "  forward = ", InputForm[proj["cross_instrument"]["forward_R_S_S"]]];
  Print["toy_project: stage3 completeness = ",
        InputForm[proj["full_basis_completeness_rel_residual"]]];
  Print["toy_project: stage3 C_twist2_sum = ", InputForm[proj["C_twist2_sum"]],
        " (a-priori ~0: pure scalar exchange)"];
  Print["toy_project: VERDICT-INPUT sign(Re C_scalar_production) = ",
        Sign[Re[proj["C_scalar_production"]]],
        "  vs a-priori sign = +1;  |C|/aPriori = ",
        InputForm[Abs[proj["C_scalar_production"]]/aPriori]];
  Print["toy_project: DONE"];
];
Exit[0]
