#!/usr/bin/env wolframscript
(* wp1_project.wls — W-P1 stage-by-stage twist-2 sign trace
   (DESIGN-ITEM4-AMENDMENT8R4 R3, decisive H-A1/H-A2 discriminator).

   Consumes the vector-toy amp_reduced.m (PRODUCTION run_calcfeynamp.wls on
   the ToyDiracV FeynArts amplitude) and pushes it through the FULL
   production projection, comparing the SHIPPING twist-2 coefficient
   C_twist2_sum against the identical fit run on the ANALYTIC amplitude.

   A-PRIORI (hand Wick, ToyDiracV.mod header):
     M_phys = +gchi gq/(t - MV^2) (chibar gamma^mu chi)(qbar gamma_mu q)
            = -gchi gq/(MV^2 + TEPS) * mdot[chiVec, quarkVec]   at t=-TEPS.

   PRE-REGISTERED READ-OUT (FROZEN BEFORE THE RUN):
     Primary: sgn = sign(Re C_twist2_sum^pipeline) * sign(Re C_twist2_sum^analytic)
       where BOTH coefficients come from the byte-identical production
       contracted fit (column-normalized LeastSquares of amplitude values on
       referenceConfigs against $opRefs2, exactly the projectOperators
       arithmetic that ships C_twist2_sum).
       sgn = -1  ->  toy twist-2 FLIPS alongside scalar  ->  H-A1
             (the boundary -1 hits both classes; a compensator exists
              elsewhere in production)
       sgn = +1  ->  toy twist-2 AGREES while D3 scalar flipped -> H-A2
             (defect class-specific already at toy level; amplitude
              boundary provisionally exonerated)
     Secondary (amplitude boundary datum): config-wise ratio
       M_pipeline/M_analytic (a-priori +1 if the assembly were faithful;
       D3 measured -1 on scalar exchange — prediction under the item-1
       per-diagram mechanism read: -1 here too. NOTE this secondary is
       NOT the H-A1/H-A2 discriminator; the primary is, because the
       hypotheses differ in the PROJECTION pathway's class response.)
     MATERIALITY BAR (frozen): |C_twist2_sum^analytic| must exceed
       1e-6 * max column-projection scale AND the pipeline/analytic
       magnitudes must agree within a factor of 3, else the probe is
       VOID (named refusal, no verdict; report and stop).
     CONSISTENCY LATTICE (8R4): if this result combined with W-P3's
       hand-Wick verdict lands in {W-P1 flips + W-P3 correct} or
       {W-P1 agrees + W-P3 incorrect}, STOP and escalate — no
       improvised reconciliation.

   Args (run_eval_common contract): <amp_reduced.m> <point.json(ignored)>
   <preset> <out(ignored)> <lt_prefix(ignored)> *)

mUlight = 2.16*^-3; mDlight = 4.67*^-3; mSlight = 0.093;
mClight = 1.27;     mBlight = 4.18;     mTlight = 173.4;
TEPS = 1.0*^-4;
$ddExpansion = False;

$scriptDir = "/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-a4f66e3295b1b33b8/plugins/hep-ph-toolkit/skills/looptools/scripts/";
Get[FileNameJoin[{$scriptDir, "run_eval_common.wl"}]];
Get[FileNameJoin[{$scriptDir, "sd_projection.wl"}]];

Module[{mchi, mq, mv, gv, amp, subexpr, ampBody, abbr, abbrF, terms, mkR,
        extIdx, extPins, Mnum, resid, chainDefsP, fsymsP, cc, crossedChains,
        analyticOf, cfgs, refCfgs, frule, fit3, proj, prodNames, prodMat,
        prodColNorms, nprod, pipeVals, anaVals, pipeSol, anaSol, pipeC, anaC,
        pipeResid, anaResid, colScale, sgn},

  mchi = 132.692344; mq = mDlight; mv = 90.; gv = 1.;

  amp = Quiet[Check[Get[$ampPath], $Failed]];
  If[amp === $Failed,
    WriteString["stderr", "wp1_project: Get[amp_reduced.m] failed\n"]; Exit[1]];
  subexpr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "subexpr"], "subexpr" /. amp, {}];
  ampBody = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "amp"], "amp" /. amp, amp];
  abbr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "abbr"], "abbr" /. amp, {}];
  abbrF = Cases[abbr, HoldPattern[_ -> _WeylChain]];
  terms = List @@ ampBody;
  Print["wp1_project: n_terms = ", Length[terms], " n_chains = ", Length[abbrF]];
  If[abbrF === {}, Print["wp1_project: NO WeylChain table"]; Exit[3]];

  (* stage 0: taxonomy + crossed census — DOES the suspect C-conjugation
     rotation path (crossedRotValue) get exercised by this toy? *)
  cc = chainClass[abbrF];
  Print["wp1_project: stage0 chainClass = ", InputForm[cc]];
  Print["wp1_project: stage0 unrecognized = ", InputForm[unrecognizedChains[abbrF]]];
  chainDefsP = Association[Cases[abbrF, (f_ -> wc_WeylChain) :> (f -> wc)]];
  fsymsP = Keys[cc];
  crossedChains = Select[fsymsP, barChiMixedQ[chainDefsP[#]] &];
  Print["wp1_project: stage0 barChiMixedQ chains = ", InputForm[crossedChains],
        "  (nonempty => the C-conjugate-rotate suspect path IS exercised)"];

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
    Print["wp1_project: UNRESOLVED symbols ", InputForm[Take[resid, UpTo[20]]]];
    Exit[3]];

  (* analytic amplitude on the projector's own spinor conventions *)
  analyticOf[kin_, spin_] := Module[{cv, qvv},
    cv = chiVec[kin, spin]; qvv = quarkVec[kin, spin];
    -gv*gv/(mv^2 + TEPS) * $mdot[cv, qvv]];

  (* stage 1: config-wise pipeline/analytic ratio (amplitude-boundary datum) *)
  cfgs = sampleConfigs[N[mchi], N[mq], 1.0];
  refCfgs = referenceConfigs[N[mchi], N[mq], 1.0];
  Module[{rs},
    rs = Table[Module[{kin = cfg["kin"], spin = cfg["spin"], fr, mval, an},
        fr = (# -> chainValueOn[chainDefsP[#], kin, spin]) & /@ fsymsP;
        mval = Mnum /. fr;
        an = analyticOf[kin, spin];
        If[Abs[an] < 1*^-8, Nothing, mval/an]],
      {cfg, Join[Take[cfgs, 48], Take[refCfgs, -48]]}];
    Print["wp1_project: stage1 n_usable = ", Length[rs],
          "  ratio M_pipe/M_analytic: mean = ", InputForm[Mean[rs]],
          "  min|.| = ", InputForm[Min[Abs[rs]]],
          "  max|.| = ", InputForm[Max[Abs[rs]]]];
    Print["wp1_project: stage1 (a-priori +1 faithful; D3 scalar measured -1;",
          " item-1 mechanism predicts -1 here)"]];

  (* stage 2: legacy 3-op fit (diagnostic; its C_twist2 column is the old
     contracted quark-vector reference) *)
  fit3 = threeOpFit[Mnum, chainDefsP, fsymsP, mchi, mq];
  Print["wp1_project: stage2 threeOpFit coeffs = ", InputForm[fit3["coeffs"]],
        "  rel_resid = ", InputForm[fit3["rel_residual"]]];

  (* stage 3: FULL production projection on the pipeline amplitude *)
  proj = projectOperators[Mnum, abbrF, mchi, mq];
  If[! TrueQ[proj["ok"]],
    Print["wp1_project: stage3 projectOperators REFUSED (named): ",
          proj["reason"], " ", ToString[Lookup[proj, "detail", ""]]];
    Print["wp1_project: continuing to stage4 sidecar contracted fit (same",
          " arithmetic) — refusal reported, not silently bypassed"],
    Print["wp1_project: stage3 C_twist2_sum (SHIPPING) = ",
          InputForm[proj["C_twist2_sum"]]];
    Print["wp1_project: stage3 C_twist2_dif = ", InputForm[proj["C_twist2_dif"]]];
    Print["wp1_project: stage3 C_scalar_production = ",
          InputForm[proj["C_scalar_production"]], " (a-priori ~0: pure vector)"];
    Print["wp1_project: stage3 completeness = ",
          InputForm[proj["full_basis_completeness_rel_residual"]],
          "  rotation_exactness = ", InputForm[proj["rotation_exactness_max"]]]];

  (* stage 4: byte-identical contracted-fit arithmetic on BOTH amplitudes.
     Pipeline values here use the UNROTATED direct monomial evaluation when no
     crossed monomials exist; if crossed monomials exist the stage-3 shipping
     value (rotated) is the pipeline read-out and this leg is the analytic
     reference only. *)
  prodNames = Keys[$opRefs2];
  prodMat = N[Table[Table[$opRefs2[op][cfg["kin"], cfg["spin"], N[mchi], N[mq]],
    {op, prodNames}], {cfg, refCfgs}]];
  prodColNorms = Norm /@ Transpose[prodMat];
  nprod = Transpose[Transpose[prodMat]/prodColNorms];
  pipeVals = N[Table[Module[{kin = cfg["kin"], spin = cfg["spin"], fr},
      fr = (# -> chainValueOn[chainDefsP[#], kin, spin]) & /@ fsymsP;
      Mnum /. fr], {cfg, refCfgs}]];
  anaVals = N[Table[analyticOf[cfg["kin"], cfg["spin"]], {cfg, refCfgs}]];
  pipeSol = Quiet[LeastSquares[nprod, pipeVals]]/prodColNorms;
  anaSol = Quiet[LeastSquares[nprod, anaVals]]/prodColNorms;
  pipeC = AssociationThread[prodNames -> pipeSol];
  anaC = AssociationThread[prodNames -> anaSol];
  pipeResid = Norm[prodMat . pipeSol - pipeVals]/Norm[pipeVals];
  anaResid = Norm[prodMat . anaSol - anaVals]/Norm[anaVals];
  Print["wp1_project: stage4 contracted fit PIPELINE  = ", InputForm[pipeC],
        "  rel_resid = ", InputForm[pipeResid]];
  Print["wp1_project: stage4 contracted fit ANALYTIC  = ", InputForm[anaC],
        "  rel_resid = ", InputForm[anaResid]];

  (* materiality + verdict input *)
  colScale = Max[Abs[anaVals]]/Max[prodColNorms/Sqrt[Length[refCfgs]]];
  If[Abs[anaC["C_twist2_sum"]] < 1*^-6 Abs[colScale],
    Print["wp1_project: VOID — analytic C_twist2_sum immaterial (",
          InputForm[anaC["C_twist2_sum"]], " vs scale ", InputForm[colScale],
          "); no twist-2 verdict from this toy"]; Exit[4]];
  If[!(1/3 < Abs[pipeC["C_twist2_sum"]/anaC["C_twist2_sum"]] < 3),
    Print["wp1_project: VOID — pipeline/analytic C_twist2_sum magnitudes",
          " disagree beyond factor 3: ",
          InputForm[Abs[pipeC["C_twist2_sum"]/anaC["C_twist2_sum"]]],
          "; probe not interpretable as a sign read"]; Exit[4]];
  sgn = Sign[Re[pipeC["C_twist2_sum"]]] Sign[Re[anaC["C_twist2_sum"]]];
  Print["wp1_project: VERDICT-INPUT sign(C_twist2_sum^pipe)*sign(C_twist2_sum^ana) = ",
        sgn, "   ratio = ", InputForm[pipeC["C_twist2_sum"]/anaC["C_twist2_sum"]]];
  Print["wp1_project: PRE-REGISTERED MAP: -1 -> H-A1 (twist-2 FLIPS too);",
        " +1 -> H-A2 (twist-2 AGREES while scalar flips)"];
  Print["wp1_project: DONE"];
];
Exit[0]
