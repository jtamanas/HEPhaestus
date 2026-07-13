#!/usr/bin/env wolframscript
(* probe_q3.wls — AMENDMENT5 Ruling 2 Q3: synthetic-amplitude identifiability
   control THROUGH the Majorana-crossed path (job-dir sidecar; no production
   code).  Builds M_syn = alpha*(Fa1 Fb1) + beta*(Fa2 Fb2) from the real
   amplitude's own crossed-layout chains, computes the KNOWN S(x)S content of
   each crossed monomial two independent ways (exact Dirac-trace projection of
   the crossedRotAlgebraic decomposition; full-256-dictionary LS of the
   crossedRotValue config values), then pushes M_syn through the FULL
   rotate-then-read-off production pipeline (projectOperators) and compares.
   Pre-registered bar: recovery to < 1e-10 exonerates the read-off; failure
   convicts Y1 and localizes it. *)

mUlight = 2.16*^-3; mDlight = 4.67*^-3; mSlight = 0.093;
mClight = 1.27;     mBlight = 4.18;     mTlight = 173.4;
TEPS = 1.0*^-4;
$ddExpansion = False;  (* no PV evaluation in this control *)

$scriptDir = "/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-a4f66e3295b1b33b8/plugins/hep-ph-toolkit/skills/looptools/scripts/";
Get[FileNameJoin[{$scriptDir, "run_eval_common.wl"}]];
Get[FileNameJoin[{$scriptDir, "sd_projection.wl"}]];

Module[{point, mchi, mq, amp, abbrF, chainDefsP, fsymsP, aType, bType, pairs,
        cfgsV, traceSS, dictSS, alpha, beta, fa1, fb1, fa2, fb2, Msyn, cKnown,
        p, rec, cSSpairs},

  point = Quiet[Check[Import[$pointPath, "RawJSON"], $Failed]];
  If[point === $Failed,
    WriteString["stderr", "probe_q3: could not read point.json\n"]; Exit[1]];
  mchi = point["m_dm_gev"]; mq = mDlight;

  amp = Quiet[Check[Get[$ampPath], $Failed]];
  If[amp === $Failed,
    WriteString["stderr", "probe_q3: Get[amp_reduced.m] failed\n"]; Exit[1]];
  abbrF = Cases["abbr" /. amp, HoldPattern[_ -> _WeylChain]];
  chainDefsP = Association[Cases[abbrF, (f_ -> wc_WeylChain) :> (f -> wc)]];
  fsymsP = Keys[chainClass[abbrF]];

  (* crossed-layout chains: barred chi + unbarred quark; A-type legs {k1,k2},
     B-type legs {k3,k4} (crossedRotValue's supported layout) *)
  aType = Select[fsymsP, barChiMixedQ[chainDefsP[#]] &&
    chainLegMomenta[chainDefsP[#]] === {k[1], k[2]} &];
  bType = Select[fsymsP, barChiMixedQ[chainDefsP[#]] &&
    chainLegMomenta[chainDefsP[#]] === {k[3], k[4]} &];
  Print["probe_q3: A-type crossed chains = ", InputForm[aType],
        "  B-type = ", InputForm[bType]];
  If[Length[aType] < 1 || Length[bType] < 1,
    Print["probe_q3: NO crossed-layout chain pairs in the amplitude — control",
          " not constructible"]; Exit[3]];
  pairs = Take[Flatten[Outer[List, aType, bType], 1], UpTo[2]];
  Print["probe_q3: synthetic pairs = ", InputForm[pairs]];

  cfgsV = Take[sampleConfigs[N[mchi], N[mq], 1.0], 7];

  (* KNOWN content, method 1: exact Dirac-trace S(x)S projection of the
     crossedRotAlgebraic decomposition  Sum Ginv[i,j] cv[j] qv[i] with
     cv[j] = chibar(B16_j.g5)chi, qv[i] = qbar fierzDress[Ap.B16_i.Bm] q;
     proj_S(X) = Tr[X]/4 (S is Gram-orthogonal in the 16-basis). *)
  traceSS[fa_, fb_, kin_] := Module[{a = chainDefsP[fa], b = chainDefsP[fb],
      Am, Bm, Ap},
    Am = chainMatrixOn[a, kin]; Bm = chainMatrixOn[b, kin];
    Ap = $CC . Transpose[Am] . $CCinv;
    Sum[$B16Ginv[[i, j]] * (Tr[$B16[[j]] . $g5]/4) *
        (Tr[fierzDress[Ap . $B16[[i]] . Bm]]/4), {i, 16}, {j, 16}]];

  (* KNOWN content, method 2: LS of the pipeline's own rotated crossed values
     onto the full 256-column dictionary over the reference configs; read the
     R_S_S component.  Independent of method 1's algebra. *)
  dictSS[fa_, fb_] := Module[{cfgs = referenceConfigs[N[mchi], N[mq], 1.0],
      rows, vals, sol, idx},
    rows = Table[refRow[cfg["kin"], cfg["spin"]], {cfg, cfgs}];
    vals = Table[crossedRotValue[chainDefsP[fa], chainDefsP[fb],
      cfg["kin"], cfg["spin"]], {cfg, cfgs}];
    If[MemberQ[vals, $Failed], Return[$Failed]];
    sol = Quiet[LeastSquares[N[rows], N[vals]]];
    idx = Position[$refNames, $refScalarName][[1, 1]];
    <|"R_S_S" -> sol[[idx]],
      "resid" -> Norm[N[vals] - N[rows] . sol]/Norm[N[vals]]|>];

  cSSpairs = Table[Module[{fa = pr[[1]], fb = pr[[2]], tvals, dv},
      tvals = Table[traceSS[fa, fb, cfg["kin"]], {cfg, cfgsV}];
      Print["probe_q3: pair ", InputForm[pr], " traceSS per-config = ",
            InputForm[tvals], "  (constancy spread = ",
            InputForm[Max[Abs[tvals - Mean[tvals]]]], ")"];
      dv = dictSS[fa, fb];
      Print["probe_q3: pair ", InputForm[pr], " dictSS R_S_S = ",
            InputForm[If[dv === $Failed, $Failed, dv["R_S_S"]]],
            "  dict resid = ",
            InputForm[If[dv === $Failed, $Failed, dv["resid"]]]];
      Mean[tvals]],
    {pr, pairs}];

  alpha = 1.2831509485455282*^-7; beta = -0.5*^-7;
  If[Length[pairs] == 1, beta = 0.];
  {fa1, fb1} = pairs[[1]];
  Msyn = alpha fa1 fb1 +
    If[Length[pairs] > 1, beta pairs[[2, 1]] pairs[[2, 2]], 0];
  cKnown = alpha cSSpairs[[1]] +
    If[Length[pairs] > 1, beta cSSpairs[[2]], 0];
  Print["probe_q3: M_syn = ", InputForm[Msyn]];
  Print["probe_q3: c_known (S x S) = ", InputForm[cKnown]];

  p = projectOperators[Msyn, abbrF, mchi, mq];
  If[! TrueQ[p["ok"]],
    Print["probe_q3: projectOperators REFUSED: ", p["reason"], " ",
          ToString[Lookup[p, "detail", ""]]];
    Exit[3]];
  rec = p["C_scalar_production"];
  Print["probe_q3: RECOVERY transfer C_scalar_production = ", InputForm[rec]];
  Print["probe_q3: RECOVERY threeop_rotated = ",
        InputForm[p["cross_instrument"]["threeop_rotated"]],
        "  forward = ", InputForm[p["cross_instrument"]["forward_R_S_S"]]];
  Print["probe_q3: RECOVERY |transfer - c_known| = ", InputForm[Abs[rec - cKnown]],
        "  |threeop - c_known| = ",
        InputForm[Abs[p["cross_instrument"]["threeop_rotated"] - cKnown]],
        "  bar = 1e-10"];
  Print["probe_q3: full_basis_completeness = ",
        InputForm[p["full_basis_completeness_rel_residual"]]];
  Print["probe_q3: DONE"];
];
Exit[0]
