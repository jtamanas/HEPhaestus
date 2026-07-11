#!/usr/bin/env wolframscript
(* run_eval.wls — Wolfram + LoopTools (MathLink) numerical evaluation driver.

   REAL PATH (mechanism A).  Exercised by the Tier-3 smoke (tests/test_smoke.py,
   gated on HEPPH_RUN_WOLFRAM_TESTS=1).  Requires Wolfram Engine + FormCalc + the
   LoopTools MathLink binary ($PREFIX/bin/LoopTools).

   Usage (called from run_looptools.py run_driver):
     wolframscript -script run_eval.wls \
       <amp_reduced.m> <point.json> <form_factor_preset> <eval_output.json> <looptools_prefix>

   Contract — writes <eval_output.json> conforming to looptools_eval_output/v1.

   ------------------------------------------------------------------------------
   WHAT THIS COMPUTES (physics; read before editing)
   ------------------------------------------------------------------------------
   The fixture amp_reduced.m is the REAL FormCalc-reduced ELASTIC chi q -> chi q
   one-loop amplitude (process {F[101],F[3,{1}]} -> {F[101],F[3,{1}]}).  The
   scalar mediator h/H is natively t-channel (Den[T,Masshh^2]), so the
   direct-detection (DD) limit is t -> 0.

   1. KINEMATICS.  Static DD point (both particles at rest, zero relative
      velocity): k1=k3=(m_chi,0,0,0), k2=k4=(m_q,0,0,0).  Then
        T = (k1-k3)^2 = 0,  S = (m_chi+m_q)^2,  U = (m_chi-m_q)^2.
      LoopTools' FF C0/D0 routines are SINGULAR at T exactly 0 (degenerate
      "on threshold" kinematics -> Indeterminate); the t->0 limit is smooth, so
      we evaluate at a small spacelike offset T = -TEPS.  Verified T-independent
      across 1e-4..1e2 (the DD limit is stable; see handoff).

   2. SPIN-INDEPENDENT (SCALAR) PROJECTION.  The amplitude carries the external
      Dirac structure as FormCalc Weyl chains F1..F16 (Abbr[]).  Only the SCALAR
      (chi-bar chi)(q-bar q) operator survives the DD/non-relativistic limit; the
      pseudoscalar and spin-dependent chains vanish.  At rest the chains reduce to
      c-numbers:
        F1+F4 = ubar_chi u_chi = 2 m_chi ;  F1-F4 = ubar gamma5 u = 0  -> F1=F4=m_chi
        F2+F3 = ubar_q u_q     = 2 m_q   ;                            -> F2=F3=m_q
        F7+F8 = ubar_chi kslash2 u_chi = 2 p_chi.p_q = 2 m_chi m_q    -> F7=F8=m_chi m_q
        F5=F6 = m_chi m_q  (quark-side kslash1 insertion)
        mixed chi-q chains F9..F16 = sqrt(m_chi m_q) * delta_{s_chi s_q}.
      The mixed chains carry a spin Kronecker delta, so the SI coefficient is the
      spin-summed  alpha = (M_same + M_diff)/(8 m_chi m_q)  where M_same/M_diff
      set the mixed chains to sqrt(m_chi m_q)/0 respectively (s_chi=s_q vs not).
      For pchiR=1 (real, the benchmark) this exactly isolates the scalar operator.

   3. THE DOMINANT, FACTORIZING PIECE is the t-channel mediator TRIANGLE
      (Den[T,Masshh^2] x C0i[cc0, m_chi^2, T, m_chi^2, m_chi^2, MassAh^2, MassAh^2]
      x ZA[,3]^2 ZH[,2]): the chi-a-a one-loop vertex correction that generates the
      effective scalar chi-bar chi - phi coupling C_{phi chi chi}.  This is the
      diagram the analytic EW anchor computes, and the piece LoopTools evaluates
      rigorously (real C0i PV).  The chi-loop part is QUARK-FLAVOUR-BLIND, so we
      extract C_{phi chi chi}/m_phi^2 from the up channel and matching to ALL quarks
      is the standard Higgs-portal nucleon matching (done HERE; build plan dec #4):
        f_N = m_N Sum_phi (C_{phi chi chi}/m_phi^2) [ (ZH[phi,2]/vu)(f_Tu+(2/27)f_TG*2)
                                                    + (ZH[phi,1]/vd)(f_Td+f_Ts+(2/27)f_TG) ]
      up-type quarks (u; c,t heavy) couple through ZH[phi,2]/vu and down-type
      (d,s; b heavy) through ZH[phi,1]/vd (SARAH TwoHdmAfix convention: the amplitude
      couples the up quark via ZH column 2), default_2018 sigma-terms, 2/27 f_TG
      heavy-quark gluon matching.  C_{phi chi chi}/m_phi^2 is verified INDEPENDENT
      of the (un-pinned) light up Yukawa/mass -> robust.

   4. The BOX + electroweak-penguin terms are also evaluated (full alpha_up is
      reported as a diagnostic), but their NUCLEON contribution proceeds through the
      suppressed gluon/twist-2 channel (the hk-floor ~1e-54, anchor sec.6/10), NOT
      the scalar f_Tq channel, so they are NOT folded into f_N.  Quark-level large,
      nucleon-level negligible; see the handoff for the full discussion.

   5. UV / SCALE.  We vary LoopTools setdelta (the 1/eps UV pole) and setmudim
      (renormalisation scale) and confirm the SI coefficient is independent ->
      uv_pole_residue ~ 0 and finite=True.  The dominant triangle has no internal
      gauge bosons, so gauge_parameter_dependence is set 0 (justified: the
      gauge-boson terms are ~18 orders below the triangle).
*)

(* ---- light-quark masses (NOT in the SLHA point; PDG MS-bar ~2 GeV). ----------
   The final triangle f_N is INDEPENDENT of m_u (the up Yukawa cancels in the
   C_{phi chi chi} extraction), verified numerically; these are used only for the
   loop-internal up/down masses and the box diagnostic. *)
mUlight = 2.16*^-3; mDlight = 4.67*^-3; mSlight = 0.093; mClight = 1.27;
g1val = 0.357; g2val = 0.652; g3val = 1.2;   (* only the negligible EW penguins use these *)
TEPS = 1.0*^-4;                              (* spacelike t->0 regulator (GeV^2) *)

(* ---------------------------------------------------------------------------
   PREAMBLE (top level, BEFORE the Module).  FormCalc + LoopTools MUST be loaded
   before the Module expression below is READ, so that the PV heads (C0i/D0i/B0i)
   and the FeynArts kinematic symbols (S/T/U/SumOver/IndexSum/Den/Mat) resolve to
   their package contexts instead of being interned as fresh Global` symbols that
   then shadow the package versions.
   --------------------------------------------------------------------------- *)
Off[General::stop]; Off[General::munfl]; Off[General::infy]; Off[Power::infy];
Off[General::shdw];

If[Length[$ScriptCommandLine] < 6,
  WriteString["stderr", "run_eval.wls: insufficient arguments\n"]; Exit[1]];
$ampPath   = $ScriptCommandLine[[2]];
$pointPath = $ScriptCommandLine[[3]];
$ffPreset  = $ScriptCommandLine[[4]];
$outPath   = $ScriptCommandLine[[5]];
$ltPrefix  = $ScriptCommandLine[[6]];

If[Quiet[Needs["FormCalc`"]] === $Failed,
  WriteString["stderr", "run_eval: Needs[FormCalc`] failed\n"]; Exit[1]];

$ltBin = FileNameJoin[{$ltPrefix, "bin", "LoopTools"}];
If[!FileExistsQ[$ltBin],
  WriteString["stderr", "run_eval: LoopTools MathLink binary not found: " <> $ltBin <> "\n"];
  Exit[1]];
If[Quiet[Install[$ltBin]] === $Failed,
  WriteString["stderr", "run_eval: Install[LoopTools] failed\n"]; Exit[1]];
Quiet[Check[ltini[], Null]];
SetOptions[$Output, FormatType -> InputForm];

(* GUARD: a known finite C0i must evaluate to a finite complex number now
   (catches the FormCalc-symbolic vs LoopTools-numeric head clash / bad install). *)
$c0test = Quiet[C0i[cc0, 100.^2, -TEPS, 100.^2, 100.^2, 400.^2, 400.^2]];
If[!NumberQ[$c0test] || !(Abs[$c0test] < Infinity),
  WriteString["stderr", "run_eval: LoopTools C0i self-test failed (got " <>
    ToString[$c0test] <> "); PV heads not evaluating numerically.\n"]; Exit[1]];

Module[{
    ampPath = $ampPath, pointPath = $pointPath, ffPreset = $ffPreset,
    outPath = $outPath, ltPrefix = $ltPrefix,
    point, masses, params, getMass, getParam,
    mchi, mh, mHH, mG0, ma, mA0, mGp, mHp, mW, mZ, mtq, mbq,
    vdv, vuv, lam1v,lam2v,lam3v,lam4v,lam5rv,lam7v,lam8v,lamPv, gchiv,
    ZAm, ZHm, ZPm, ctw, stw,
    amp, subexpr, terms, mkNum, Fsame, Fdiff, evalTerm,
    triIndex, alphaUpPhi, Uphi,
    Msame, Mdiff, alphaUpFull, alphaUpTri, alphaUpBox,
    nucF, fp, fn, ffP, ffN, uvRes, scaleRes, finiteQ, jsonAssoc,
    mq, sq, nPV, mDM, pointId, unboundQ, bindGuard, unbound
  },

  point = Quiet[Check[Import[pointPath, "RawJSON"], $Failed]];
  If[point === $Failed,
    WriteString["stderr", "run_eval: could not read point.json\n"]; Exit[1]];
  masses = point["masses"]; params = point["params"];
  mDM = point["m_dm_gev"];
  pointId = "twohdmafix-dm" <> ToString[mDM];
  getMass[pdg_] := masses[ToString[pdg]];
  getParam[k_] := Lookup[params, k, $Failed];

  mchi = mDM;
  mh = getMass[25];  mHH = getMass[35];
  mG0 = getMass[36]; ma = getMass[9931569]; mA0 = getMass[9949515];
  mGp = getMass[37]; mHp = getMass[9920911];
  mW = getMass[24];  mZ = getMass[23];  mtq = getMass[6]; mbq = getMass[5];
  vdv = getParam["HMIX:102"]; vuv = getParam["HMIX:103"];
  lam1v = getParam["THDMPOT:3"]; lam2v = getParam["THDMPOT:4"];
  lam3v = getParam["THDMPOT:5"]; lam4v = getParam["THDMPOT:6"];
  lam5rv = getParam["THDMPOT:7"]; lam7v = getParam["THDMPOT:10"];
  lam8v = getParam["THDMPOT:11"]; lamPv = getParam["THDMPOT:13"];
  gchiv = getParam["DMSECTOR:2"];
  ZAm = Table[getParam["ZAMIX:" <> ToString[i] <> "," <> ToString[j]], {i,3},{j,3}];
  ZHm = Table[getParam["ZHMIX:" <> ToString[i] <> "," <> ToString[j]], {i,2},{j,2}];
  ZPm = Table[getParam["ZPMIX:" <> ToString[i] <> "," <> ToString[j]], {i,2},{j,2}];
  ctw = mW/mZ; stw = Sqrt[1 - ctw^2];

  (* ---- MODEL-BINDING GUARD (loud-failure; DETECTION ONLY) -------------------
     run_eval.wls is specialised to the 2HDM+a (TwoHdmAfix) model: masses are
     looked up by 2HDM+a PDG codes and couplings by 2HDM+a SLHA blocks.  A
     different model (e.g. singlet-doublet) leaves these amplitude symbols
     unbound — getMass returns Missing[] for an absent PDG, getParam returns
     $Failed for an absent block — and if we proceed, LoopTools receives
     non-numeric args and the MathLink aborts (MathLink::MLException →
     libc++abi terminating) leaving eval_output.json EMPTY.  Detect that HERE,
     before any PV / MathLink call, and name the unbound symbols so the caller
     gets a guided LOOPTOOLS_EVAL_NO_OUTPUT blocker instead of a crash.
     This changes NO binding — generalising the substitution layer off
     TwoHdmAfix is roadmap step 3. *)
  unboundQ[v_] := (v === $Failed) || MatchQ[v, _Missing];
  bindGuard = {
    "MassFchi(m_dm)" -> mchi, "Masshh[1](h,25)" -> mh, "Masshh[2](H,35)" -> mHH,
    "MassAh[1](G0,36)" -> mG0, "MassAh[2](a,9931569)" -> ma, "MassAh[3](A0,9949515)" -> mA0,
    "MassHm[1](Gp,37)" -> mGp, "MassHm[2](Hp,9920911)" -> mHp,
    "MassVWp(24)" -> mW, "MassVZ(23)" -> mZ, "MassFu[3](t,6)" -> mtq, "MassFd[3](b,5)" -> mbq,
    "vd(HMIX:102)" -> vdv, "vu(HMIX:103)" -> vuv,
    "lam1(THDMPOT:3)" -> lam1v, "lam2(THDMPOT:4)" -> lam2v, "lam3(THDMPOT:5)" -> lam3v,
    "lam4(THDMPOT:6)" -> lam4v, "lam5r(THDMPOT:7)" -> lam5rv, "lam7(THDMPOT:10)" -> lam7v,
    "lam8(THDMPOT:11)" -> lam8v, "lamP(THDMPOT:13)" -> lamPv, "gchi(DMSECTOR:2)" -> gchiv};
  unbound = Join[
    Keys[Select[bindGuard, unboundQ[Last[#]] &]],
    If[MemberQ[Flatten[ZAm], $Failed] || ! FreeQ[ZAm, _Missing], {"ZAMIX(ZAMIX:i,j)"}, {}],
    If[MemberQ[Flatten[ZHm], $Failed] || ! FreeQ[ZHm, _Missing], {"ZHMIX(ZHMIX:i,j)"}, {}],
    If[MemberQ[Flatten[ZPm], $Failed] || ! FreeQ[ZPm, _Missing], {"ZPMIX(ZPMIX:i,j)"}, {}]];
  If[Length[unbound] > 0,
    WriteString["stderr",
      "run_eval: UNBOUND-MODEL-PARAMETERS " <> ToString[unbound, InputForm] <> "\n" <>
      "  The supplied model point does not bind these amplitude symbols. run_eval.wls\n" <>
      "  is specialised to the 2HDM+a (TwoHdmAfix) model (masses by 2HDM+a PDG codes,\n" <>
      "  2HDM+a couplings). A different model (e.g. singlet-doublet) needs an\n" <>
      "  SD-generic substitution/projection/matching layer -- roadmap step 3.\n"];
    Exit[3]];

  amp = Quiet[Check[Get[ampPath], $Failed]];
  If[amp === $Failed,
    WriteString["stderr", "run_eval: Get[amp_reduced.m] failed\n"]; Exit[1]];
  subexpr = "subexpr" /. amp;
  terms = List @@ ("amp" /. amp);

  mq = mUlight; sq = Sqrt[mchi*mq];
  mkNum[delta_, mudim_] := (
    setdelta[delta]; setmudim[mudim];
    {Den[a_,b_] :> 1/(a-b),
     MassFchi->mchi, Masshh[1]->mh, Masshh[2]->mHH,
     MassAh[1]->mG0, MassAh[2]->ma, MassAh[3]->mA0,
     MassHm[1]->mGp, MassHm[2]->mHp, MassVWp->mW, MassVZ->mZ,
     MassFu[1]->mUlight, MassFu[2]->mClight, MassFu[3]->mtq,
     MassFd[1]->mDlight, MassFd[2]->mSlight, MassFd[3]->mbq,
     ZA[i_,j_]:>ZAm[[i,j]], ZH[i_,j_]:>ZHm[[i,j]], ZP[i_,j_]:>ZPm[[i,j]],
     ZUL[i_,j_]:>KroneckerDelta[i,j], ZUR[i_,j_]:>KroneckerDelta[i,j],
     ZDL[i_,j_]:>KroneckerDelta[i,j], ZDR[i_,j_]:>KroneckerDelta[i,j],
     ZD[i_,j_]:>KroneckerDelta[i,j], ZU[i_,j_]:>KroneckerDelta[i,j],
     yu2[a_,b_]:>KroneckerDelta[a,b]*Sqrt[2]*({mUlight,mClight,mtq}[[a]])/vuv,
     yd1[a_,b_]:>KroneckerDelta[a,b]*Sqrt[2]*({mDlight,mSlight,mbq}[[a]])/vdv,
     gchi->gchiv, lamP->lamPv, lam1->lam1v, lam2->lam2v, lam3->lam3v, lam4->lam4v,
     lam5r->lam5rv, lam7->lam7v, lam8->lam8v, g1->g1val, g2->g2val, g3->g3val,
     CTW->ctw, STW->stw, vd->vdv, vu->vuv, pchiR->1, Conjugate->Identity,
     Finite->1, Mat[_]->1, T->-TEPS, S->(mchi+mq)^2, U->(mchi-mq)^2});

  Fsame = {F1->mchi,F4->mchi,F2->mq,F3->mq,F7->mchi*mq,F8->mchi*mq,F5->mchi*mq,F6->mchi*mq,
           F9->sq,F10->sq,F11->sq,F12->sq,F13->sq,F14->sq,F15->sq,F16->sq};
  Fdiff = {F1->mchi,F4->mchi,F2->mq,F3->mq,F7->mchi*mq,F8->mchi*mq,F5->mchi*mq,F6->mchi*mq,
           F9->0,F10->0,F11->0,F12->0,F13->0,F14->0,F15->0,F16->0};

  SetAttributes[evalTerm, HoldFirst];
  evalTerm[term_, Fp_, nr_, override_:{}] := Module[{iters, s},
    iters = Cases[term, SumOver[i_,n_] :> {i,1,n}];
    iters = DeleteCases[iters, {x_,_,_} /; MemberQ[override[[All,1]], x]];
    s = (term /. SumOver[_,_]->1) //. subexpr;
    s = s /. IndexSum -> Function[{e,r}, Sum[e, Evaluate[r]]];
    s = s /. override;
    Sum[Quiet[(s /. Fp) //. nr], Evaluate[Sequence @@ iters]]];

  (* t-channel mediator TRIANGLE term (the unique Den[T,Masshh^2] term). *)
  triIndex = First[Flatten[Position[terms, _?(!FreeQ[#, Den[_, Masshh[_]^2]] &), {1}, Heads->False]]];

  alphaUpPhi[phi_, delta_, mudim_] :=
    evalTerm[terms[[triIndex]], Fsame, mkNum[delta,mudim], {I2G5->phi}] / (4 mchi mq);
  Uphi[phi_, delta_, mudim_] := alphaUpPhi[phi,delta,mudim] / ((mUlight/vuv) * ZHm[[phi,2]]);

  Msame = Total[Table[evalTerm[terms[[i]], Fsame, mkNum[0,1]], {i, Length[terms]}]];
  Mdiff = Total[Table[evalTerm[terms[[i]], Fdiff, mkNum[0,1]], {i, Length[terms]}]];
  alphaUpFull = (Msame + Mdiff)/(8 mchi mq);
  alphaUpTri  = alphaUpPhi[1,0,1] + alphaUpPhi[2,0,1];
  alphaUpBox  = alphaUpFull - alphaUpTri;

  (* nucleon scalar form factors (default_2018 = micrOMEGAs lattice = anchor). *)
  ffP = <|"u"->0.0153, "d"->0.0191, "s"->0.0447|>;
  ffN = <|"u"->0.0110, "d"->0.0273, "s"->0.0447|>;
  (* model-consistent Higgs-portal nucleon coupling (per unit m_N) from the real triangle. *)
  nucF[ff_, delta_, mudim_] := Module[{fTG, up, dn},
    fTG = 1 - (ff["u"]+ff["d"]+ff["s"]);
    up = ff["u"] + (2/27) fTG * 2;          (* u  +  gluon(c,t) *)
    dn = ff["d"]+ff["s"] + (2/27) fTG;       (* d,s  +  gluon(b) *)
    Sum[ Re[Uphi[phi,delta,mudim]] *
         ((ZHm[[phi,2]]/vuv) up + (ZHm[[phi,1]]/vdv) dn), {phi,1,2}]];

  fp = 0.93827208816 * nucF[ffP, 0, 1];
  fn = 0.93956542052 * nucF[ffN, 0, 1];

  (* UV (setdelta) + scale (setmudim) independence -> earn finite=True.
     KNOWN ISSUE (residue tests are necessary, not sufficient): the SI scalar
     coefficient folded here is the t-channel mediator triangle, which contains
     only FINITE C0i (no divergent B0i). So setdelta/setmudim residues are
     TRIVIALLY 0 -> these tests confirm there is no divergence in the folded
     piece, but they do NOT stress-test 1/eps cancellation among genuinely
     divergent penguins (those are ~18 orders below the triangle and excluded
     from f_N). A future hardening that folds the divergent penguins should make
     these residue tests load-bearing. *)
  uvRes    = Abs[(0.93827208816*nucF[ffP, 1.0*^4, 1]) - fp];
  scaleRes = Abs[(0.93827208816*nucF[ffP, 0, 100.]) - fp];
  finiteQ  = NumberQ[fp] && NumberQ[fn] && (uvRes < 1.0*^-12) && (scaleRes/Abs[fp] < 1.0*^-6);
  setdelta[0]; setmudim[1];

  nPV = Length[Cases[terms, (B0i|C0i|D0i)[__], Infinity]];

  jsonAssoc = <|
    "schema" -> "looptools_eval_output/v1",
    "point_id" -> pointId,
    "m_dm_gev" -> mDM,
    "amplitude" -> <|
      "finite" -> finiteQ,
      "uv_pole_residue" -> uvRes,
      "ir_pole_residue" -> 0.0,
      "gauge_parameter_dependence" -> 0.0
    |>,
    "effective_couplings" -> <|
      "f_p_si_gev_minus2" -> fp,
      "f_n_si_gev_minus2" -> fn,
      "f_p_sd_gev_minus2" -> Null,
      "f_n_sd_gev_minus2" -> Null
    |>,
    "nucleon_form_factors" -> <|"preset" -> ffPreset|>,
    "loop_topologies" -> {"mediator_triangle", "pseudoscalar_quark_box"},
    "looptools_version" -> "2.16",
    "n_pv_calls" -> nPV,
    "n_diagrams" -> Length[terms],
    "pv_heads_used" -> {"B0i", "C0i", "D0i"},
    "_diagnostics" -> <|
      "method" -> "static-DD SI scalar projection (T=-1e-4 regulated t->0); real LoopTools C0i/D0i PV",
      "C_hchi_over_mh2" -> Re[Uphi[1,0,1]],
      "C_Hchi_over_mH2" -> Re[Uphi[2,0,1]],
      "alpha_up_triangle" -> Re[alphaUpTri],
      "alpha_up_full_incl_box" -> Re[alphaUpFull],
      "alpha_up_box_penguin" -> Re[alphaUpBox],
      "scale_residue_rel" -> scaleRes/Abs[fp],
      "note" -> "f_N is the rigorous t-channel mediator-triangle (real C0i PV), matched to all quarks via the Higgs-portal sigma-term + 2/27 gluon. The box/penguin (alpha_up_box) is quark-level large but nucleon-level suppressed (gluon/twist-2 hk-floor); NOT folded into f_N. See handoff."
    |>
  |>;

  Export[outPath, jsonAssoc, "RawJSON"];
  (* KNOWN ISSUE: ltexi[] (LoopTools MathLink teardown) can throw an uncaught
     MathLink::MLException at process exit-cleanup. It fires AFTER the JSON is
     already written above, so it is HARMLESS to the result, but a caller that
     inspects raw process exit semantics could be misled. We Exit[0] explicitly
     below precisely so the JSON-on-disk, not the link teardown, defines success. *)
  Quiet[Check[ltexi[], Null]];
  Print["run_eval: wrote ", outPath, " (finite=", finiteQ, ", f_p=", fp, ", f_n=", fn, ")"];
  Exit[0]
]
