(* sd_projection.wl — Majorana-chi + external-quark projection onto the SD
   operator basis via a NUMERICAL spinor-basis solve (STEP3-DESIGN.md Decision
   3.2).  This replaces PR #31's hard-coded contiguous-index block map
   ({F1..F4}=scalar, {F5..F8}=twist-2), which the PR #31 adversarial review found
   to be an UNPROVEN convention (F1 [MAJOR]).

   ============================================================================
   WHY THE OLD BLOCK MAP WAS WRONG (not right-by-luck) — established from the
   REAL SD Abbr[] table (reduce_chi1/amp_reduced.m, PR #32 self-contained artifact)
   ============================================================================
   FormCalc numbers the fermion-chain abbreviations F1,F2,... by ORDER OF
   GENERATION, not by Dirac structure, and the numbering is PROCESS-SPECIFIC.
   The real SD elastic chi1 q -> chi1 q amplitude classifies (from the actual
   WeylChain definitions in "abbr") as:

     F1,F4   chi-line  scalar   (chibar P_R/L chi)              [k3,k1]
     F2,F3   quark-line scalar  (qbar  P_R/L q)                 [k4,k2]
     F13,F14 chi-line  vector   (chibar P_R/L gamma.k q chi)    [k3,k,k1]
     F15,F16 quark-line vector  (qbar  P_R/L gamma.k q)         [k4,k,k2]  (TWIST-2)
     F5..F12,F17,F18   MIXED chi<->quark Fierz chains           (one chi, one q spinor)

   So {F1..F4} is NOT "the scalar operator": F1,F4 live on the chi line and F2,F3
   on the quark line.  {F5..F8} are NOT twist-2: they are mixed Fierz chains.  The
   2HDM+a amplitude (run_eval.wls) happens to number its OWN chains differently
   (its F1+F4=chibar chi, F7+F8=chibar kslash chi); importing that block layout to
   the SD process is the exact error the review flagged.

   Crucially, the physical amplitude is BILINEAR in the chains: every term is
   c_ab * F_a * F_b, one bilinear per external fermion line (chi line x quark
   line), possibly Fierz-rearranged into mixed*mixed products (e.g. F5*F8, verified
   max total F-degree = 2 on the real amp).  PR #31's `Coefficient[Expand[M], Fi]`
   extracts the LINEAR coefficient of Fi, which for a QUADRATIC form returns other
   chains (Coefficient[F1 F2, F1] = F2) — a non-numeric, physically meaningless
   result that PR #31's residual guard did NOT catch (F2 is not a forbidden
   symbol).  That is F1+F2 combined: silently wrong on live data.

   ============================================================================
   THE METHOD (Decision 3.2, literal): numerical basis-vector solve in F-space
   ============================================================================
   Each F_i is a Dirac bilinear evaluated between explicit external spinors.  We
   therefore evaluate every chain on an explicit spinor/momentum/helicity BASIS
   (small numeric samples), which turns each product F_a*F_b into the full
   amplitude matrix element for that external configuration — Fierz rearrangements
   are then handled automatically by the numerics.  We build reference operator
   matrix elements O_op on the SAME samples and solve, by least squares,

       M(config) = Sum_op  c_op * O_op(config) + residual(config).

   The recognized operator set (parity-even, SI-relevant; Decision 3 table):
     O_S    scalar          (chibar chi)(qbar q)
     O_Tq   quark twist-2   (chibar chi)(qbar gamma.P_chi q)     P_chi=(k1+k3)/2
     O_Tchi chi   twist-2   (chibar gamma.P_q chi)(qbar q)       P_q  =(k2+k4)/2
   C_scalar and C_twist2(quark) are the physics outputs; C_chi_vector is a
   diagnostic (must be small/vanishing for a Majorana chi — chibar gamma^mu chi
   is zero for a self-conjugate field; a large value flags a normalization/flow
   error — Decision 3.4).

   COMPLETENESS GUARD (F2, the demand): after the fit, the residual
     ||M - Sum_op c_op O_op|| / ||M||   (max over configs)
   must be below `$completenessTol` or projection FAILS LOUDLY, naming the
   worst-config residual — M carries structure outside the recognized set
   (pseudoscalar / tensor / higher-moment twist-2) that must not be silently
   dropped.

   Two-way cross-check (Decision 6 R2, for fixtures with pure diagonal content):
   the numeric solve is cross-checked against a STRUCTURAL classification of each
   chain's WeylChain (chainClass), so a pure-scalar fixture (only F1..F4-type
   diagonal chains) must give C_scalar from BOTH the structural sum and the solve.

   NO LoopTools / FormCalc PV heads are touched here — pure algebra + linear
   solve.  So the R2 fixture test needs only a Wolfram kernel (no MathLink gate).

   Majorana chi (Decision 3.4): the amplitude already carries the Majorana fermion
   flow (crossed box IRR-4); the projector adds NO symmetry factors by hand.
*)

(* ============================================================================
   1.  Dirac algebra (Dirac representation) + explicit spinors
   ============================================================================ *)

$pauli = {{{0, 1}, {1, 0}}, {{0, -I}, {I, 0}}, {{1, 0}, {0, -1}}};
$id2 = IdentityMatrix[2];
$id4 = IdentityMatrix[4];
$g0 = ArrayFlatten[{{$id2, 0}, {0, -$id2}}];
$gsp = Table[ArrayFlatten[{{0, $pauli[[i]]}, {-$pauli[[i]], 0}}], {i, 3}];
$g5 = ArrayFlatten[{{0, $id2}, {$id2, 0}}];
$gamma = Prepend[$gsp, $g0];                (* {g0,g1,g2,g3} *)
(* chirality projectors: FormCalc omega index 6 = (1+g5)/2 = P_R, 7 = P_L *)
$Pom[6] = ($id4 + $g5)/2;  $Pom[7] = ($id4 - $g5)/2;
(* 2-spinor eigenstates of sigma_z *)
$xi[1] = {1, 0};  $xi[-1] = {0, 1};

(* Dirac feynman-slash of a 4-vector (metric +---): v0 g0 - v.g_spatial. *)
slash[v_] := v[[1]] $g0 - v[[2]] $gsp[[1]] - v[[3]] $gsp[[2]] - v[[4]] $gsp[[3]];

(* On-shell u-spinor, p = {E,px,py,pz}, mass m, spin s in {+1,-1}.  ubar u = 2m. *)
uSpinor[p_, m_, s_] := Module[{en = p[[1]], sp},
  sp = (p[[2]] $pauli[[1]] + p[[3]] $pauli[[2]] + p[[4]] $pauli[[3]]);
  Sqrt[en + m] Join[$xi[s], (sp . $xi[s])/(en + m)]];
ubar[u_] := Conjugate[u] . $g0;

(* on-shell energy for 3-momentum {px,py,pz} and mass m *)
onShell[p3_, m_] := Prepend[p3, Sqrt[m^2 + p3 . p3]];


(* ============================================================================
   2.  Structural classification of the real Abbr[] WeylChains  (the F1 fix:
       operator content read from the ACTUAL definition, never a fixed block)
   ============================================================================
   Each rule is  F_i -> WeylChain[Spinor[k[a],m_a,..], om, ins..., Spinor[k[b],m_b,..]].
   We classify by (fermion line, chirality, rank = # inserted momenta):
     line  : "chi"  (both spinors MassFChi), "quark" (both MassFd/MassFu), or "mixed"
     rank  : 0 (scalar bilinear) or 1 (one momentum insertion -> vector/twist-2)
   Any chain whose structure is outside this taxonomy is UNRECOGNIZED -> loud. *)

$chiMassQ[m_]   := MatchQ[m, MassFChi[_]];
$quarkMassQ[m_] := MatchQ[m, MassFd[_] | MassFu[_]];

classifyChain[wc_WeylChain] := Module[{args, spins, masses, ins, chir, line},
  args = List @@ wc;
  spins = Cases[args, _Spinor];
  If[Length[spins] =!= 2, Return[<|"line" -> "UNRECOGNIZED", "rank" -> -1, "chir" -> 0|>]];
  masses = spins[[All, 2]];
  chir = FirstCase[args, i_Integer /; (i === 6 || i === 7), 0];
  (* inserted momenta = args between the two spinors that are not the projector *)
  ins = DeleteCases[DeleteCases[args, _Spinor], i_Integer /; (i === 6 || i === 7)];
  line = Which[
    AllTrue[masses, $chiMassQ],   "chi",
    AllTrue[masses, $quarkMassQ], "quark",
    (($chiMassQ[masses[[1]]] && $quarkMassQ[masses[[2]]]) ||
     ($quarkMassQ[masses[[1]]] && $chiMassQ[masses[[2]]])), "mixed",
    True, "UNRECOGNIZED"];
  <|"line" -> line, "rank" -> Length[ins], "chir" -> chir|>];

(* Association F_i -> classification, from a list of abbr rules (F -> WeylChain). *)
chainClass[abbr_List] := Association[
  Cases[abbr, (f_ -> wc_WeylChain) :> (f -> classifyChain[wc])]];

(* Loud taxonomy guard: names any chain whose structure is not in the recognized
   {chi|quark|mixed} x {rank 0|1} taxonomy. *)
unrecognizedChains[abbr_List] := Module[{cc = chainClass[abbr]},
  Keys[Select[cc, (#["line"] === "UNRECOGNIZED" || #["rank"] > 1 || #["chir"] === 0) &]]];


(* ============================================================================
   3.  Numeric evaluation of a WeylChain on a concrete external configuration
   ============================================================================
   `kin` maps each external momentum symbol k[i] -> numeric 4-vector; `spin` maps
   k[i] -> {+1|-1}.  The first Spinor in the chain is the BARRED one. *)

chainValueOn[wc_WeylChain, kin_, spin_] := Module[{args, sa, sb, ins, chir, ua, ub, gins},
  args = List @@ wc;
  {sa, sb} = Cases[args, _Spinor];
  chir = FirstCase[args, i_Integer /; (i === 6 || i === 7), 6];
  ins = DeleteCases[DeleteCases[args, _Spinor], i_Integer /; (i === 6 || i === 7)];
  ua = uSpinor[sa[[1]] /. kin, sa[[2]] /. kin, sa[[1]] /. spin];
  ub = uSpinor[sb[[1]] /. kin, sb[[2]] /. kin, sb[[1]] /. spin];
  gins = If[ins === {}, $id4, Dot @@ (slash[# /. kin] & /@ ins)];
  ubar[ua] . $Pom[chir] . gins . ub];

(* reference operator matrix elements (see header).  P_chi=(k1+k3)/2, P_q=(k2+k4)/2 *)
$opRefs = <|
  "C_scalar" -> Function[{kin, spin, mchi, mq},
    (chiScalar[kin, spin]) (quarkScalar[kin, spin])],
  "C_twist2" -> Function[{kin, spin, mchi, mq},
    (chiScalar[kin, spin]) (quarkVector[kin, spin, (k[1] + k[3])/2 /. kin])],
  "C_chi_vector" -> Function[{kin, spin, mchi, mq},
    (chiVector[kin, spin, (k[2] + k[4])/2 /. kin]) (quarkScalar[kin, spin])]
  |>;

chiScalar[kin_, spin_]   := chainValueOn[
  WeylChain[Spinor[k[3], MassFChi[1]], 6, Spinor[k[1], MassFChi[1]]], kin, spin] +
  chainValueOn[WeylChain[Spinor[k[3], MassFChi[1]], 7, Spinor[k[1], MassFChi[1]]], kin, spin];
quarkScalar[kin_, spin_] := chainValueOn[
  WeylChain[Spinor[k[4], MassFd[1]], 6, Spinor[k[2], MassFd[1]]], kin, spin] +
  chainValueOn[WeylChain[Spinor[k[4], MassFd[1]], 7, Spinor[k[2], MassFd[1]]], kin, spin];
quarkVector[kin_, spin_, P_] := Module[{ua, ub},
  ua = uSpinor[k[4] /. kin, MassFd[1] /. kin, k[4] /. spin];
  ub = uSpinor[k[2] /. kin, MassFd[1] /. kin, k[2] /. spin];
  ubar[ua] . slash[P] . ub];
chiVector[kin_, spin_, P_] := Module[{ua, ub},
  ua = uSpinor[k[3] /. kin, MassFChi[1] /. kin, k[3] /. spin];
  ub = uSpinor[k[1] /. kin, MassFChi[1] /. kin, k[1] /. spin];
  ubar[ua] . slash[P] . ub];


(* ============================================================================
   3b.  Fierz-complete REFERENCE basis (DESIGN-ITEM4-AMENDMENT.md Rulings 1-2)
   ============================================================================
   MEASUREMENT INSTRUMENTATION, NOT a physical-operator extension: these columns
   let the completeness guard NAME the out-of-span content (Ruling-1 working
   diagnosis: genuine Dirac content the 3-op SI basis cannot hold, leading
   candidate axial x axial) instead of reporting an anonymous ~1 residual.
   THE RULE (Ruling 2): only {C_scalar, C_twist2 (C^(1,2)), C_G} may ever flow
   toward nucleon matching; every coefficient fitted on this basis is a
   DIAGNOSTIC, emitted under out_of_span_diagnostics, never matched, never
   quoted as a cross-section.  match_nucleon.py hard-refuses SD couplings
   (invariant kept).  Sampling is UNCHANGED (off-axis, all helicities): the
   amendment explicitly REJECTS parity-even sampling as guard-blinding.

   Construction: general Dirac bilinears on each line between the explicit
   spinors (chi line: kbar=k3,k=k1; quark: kbar=k4,k=k2), then line products and
   metric contractions.  Momentum insertions use the OPPOSITE line's momentum
   (P_q on the chi line, P_chi on the quark line): same-line insertions reduce
   to S/P by the equations of motion and would only add degenerate columns. *)

$metric = {1, -1, -1, -1};
$sigmaMats = Table[(I/2) ($gamma[[mu]] . $gamma[[nu]] - $gamma[[nu]] . $gamma[[mu]]),
  {mu, 4}, {nu, 4}];

(* general bilinear on the chi / quark line for an arbitrary 4x4 spin matrix *)
chiBilin[kin_, spin_, mat_] := Module[{ua, ub},
  ua = uSpinor[k[3] /. kin, MassFChi[1] /. kin, k[3] /. spin];
  ub = uSpinor[k[1] /. kin, MassFChi[1] /. kin, k[1] /. spin];
  ubar[ua] . mat . ub];
quarkBilin[kin_, spin_, mat_] := Module[{ua, ub},
  ua = uSpinor[k[4] /. kin, MassFd[1] /. kin, k[4] /. spin];
  ub = uSpinor[k[2] /. kin, MassFd[1] /. kin, k[2] /. spin];
  ubar[ua] . mat . ub];

(* Diagnostic reference operators.  Naming: D_<chi-structure>_<quark-structure>:
   S/P = (pseudo)scalar; V/A = metric-contracted vector/axial pair; Vq/Aq =
   gamma.P_q(gamma5) on the chi line; Vc/Ac = gamma.P_chi(gamma5) on the quark
   line; T = tensor (sigma_munu), Tq/Tc = sigma-momentum contractions. *)
$PqOf[kin_] := (k[2] + k[4])/2 /. kin;
$PcOf[kin_] := (k[1] + k[3])/2 /. kin;

$opRefsDiag = <|
  "D_P_P" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, $g5] quarkBilin[kin, spin, $g5]],
  "D_S_P" -> Function[{kin, spin, mchi, mq},
    chiScalar[kin, spin] quarkBilin[kin, spin, $g5]],
  "D_P_S" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, $g5] quarkScalar[kin, spin]],
  "D_V_V" -> Function[{kin, spin, mchi, mq}, Sum[$metric[[mu]] *
    chiBilin[kin, spin, $gamma[[mu]]] quarkBilin[kin, spin, $gamma[[mu]]], {mu, 4}]],
  "D_A_A" -> Function[{kin, spin, mchi, mq}, Sum[$metric[[mu]] *
    chiBilin[kin, spin, $gamma[[mu]] . $g5] quarkBilin[kin, spin, $gamma[[mu]] . $g5], {mu, 4}]],
  "D_V_A" -> Function[{kin, spin, mchi, mq}, Sum[$metric[[mu]] *
    chiBilin[kin, spin, $gamma[[mu]]] quarkBilin[kin, spin, $gamma[[mu]] . $g5], {mu, 4}]],
  "D_A_V" -> Function[{kin, spin, mchi, mq}, Sum[$metric[[mu]] *
    chiBilin[kin, spin, $gamma[[mu]] . $g5] quarkBilin[kin, spin, $gamma[[mu]]], {mu, 4}]],
  "D_T_T" -> Function[{kin, spin, mchi, mq}, Sum[$metric[[mu]] $metric[[nu]] *
    chiBilin[kin, spin, $sigmaMats[[mu, nu]]] quarkBilin[kin, spin, $sigmaMats[[mu, nu]]],
    {mu, 4}, {nu, 4}]],
  "D_T_T5" -> Function[{kin, spin, mchi, mq}, Sum[$metric[[mu]] $metric[[nu]] *
    chiBilin[kin, spin, $sigmaMats[[mu, nu]]] quarkBilin[kin, spin, $sigmaMats[[mu, nu]] . $g5],
    {mu, 4}, {nu, 4}]],
  "D_Vq_Vc" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, slash[$PqOf[kin]]] quarkBilin[kin, spin, slash[$PcOf[kin]]]],
  "D_Aq_Ac" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, slash[$PqOf[kin]] . $g5] quarkBilin[kin, spin, slash[$PcOf[kin]] . $g5]],
  "D_Vq_Ac" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, slash[$PqOf[kin]]] quarkBilin[kin, spin, slash[$PcOf[kin]] . $g5]],
  "D_Aq_Vc" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, slash[$PqOf[kin]] . $g5] quarkBilin[kin, spin, slash[$PcOf[kin]]]],
  "D_S_Ac" -> Function[{kin, spin, mchi, mq},
    chiScalar[kin, spin] quarkBilin[kin, spin, slash[$PcOf[kin]] . $g5]],
  "D_P_Vc" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, $g5] quarkBilin[kin, spin, slash[$PcOf[kin]]]],
  "D_P_Ac" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, $g5] quarkBilin[kin, spin, slash[$PcOf[kin]] . $g5]],
  "D_Aq_S" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, slash[$PqOf[kin]] . $g5] quarkScalar[kin, spin]],
  "D_Vq_P" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, slash[$PqOf[kin]]] quarkBilin[kin, spin, $g5]],
  "D_Aq_P" -> Function[{kin, spin, mchi, mq},
    chiBilin[kin, spin, slash[$PqOf[kin]] . $g5] quarkBilin[kin, spin, $g5]],
  "D_Tq_V" -> Function[{kin, spin, mchi, mq}, Module[{Pq = $PqOf[kin]},
    Sum[$metric[[mu]] *
      Sum[$metric[[nu]] Pq[[nu]] chiBilin[kin, spin, $sigmaMats[[mu, nu]]], {nu, 4}] *
      quarkBilin[kin, spin, $gamma[[mu]]], {mu, 4}]]],
  "D_V_Tc" -> Function[{kin, spin, mchi, mq}, Module[{Pc = $PcOf[kin]},
    Sum[$metric[[mu]] chiBilin[kin, spin, $gamma[[mu]]] *
      Sum[$metric[[nu]] Pc[[nu]] quarkBilin[kin, spin, $sigmaMats[[mu, nu]]], {nu, 4}],
      {mu, 4}]]],
  "D_Tq_A" -> Function[{kin, spin, mchi, mq}, Module[{Pq = $PqOf[kin]},
    Sum[$metric[[mu]] *
      Sum[$metric[[nu]] Pq[[nu]] chiBilin[kin, spin, $sigmaMats[[mu, nu]]], {nu, 4}] *
      quarkBilin[kin, spin, $gamma[[mu]] . $g5], {mu, 4}]]],
  "D_A_Tc" -> Function[{kin, spin, mchi, mq}, Module[{Pc = $PcOf[kin]},
    Sum[$metric[[mu]] chiBilin[kin, spin, $gamma[[mu]] . $g5] *
      Sum[$metric[[nu]] Pc[[nu]] quarkBilin[kin, spin, $sigmaMats[[mu, nu]]], {nu, 4}],
      {mu, 4}]]],
  "D_Tq_Tc" -> Function[{kin, spin, mchi, mq}, Module[
    {Pq = $PqOf[kin], Pc = $PcOf[kin]},
    Sum[$metric[[mu]] *
      Sum[$metric[[nu]] Pq[[nu]] chiBilin[kin, spin, $sigmaMats[[mu, nu]]], {nu, 4}] *
      Sum[$metric[[rho]] Pc[[rho]] quarkBilin[kin, spin, $sigmaMats[[mu, rho]]], {rho, 4}],
      {mu, 4}]]]
  |>;


(* ============================================================================
   4.  Sample configurations (forward DD momenta, all helicities, several
       OFF-AXIS momentum directions to resolve twist-2 AND expose every
       Dirac structure to the completeness guard)
   ============================================================================
   Forward elastic (zero momentum transfer): k1=k3 (chi), k2=k4 (quark).  A
   nonzero 3-momentum lifts the static scalar<->twist-2 degeneracy (twist-2 is
   the O(v) quark-current structure).  CRUCIAL: the spins are sigma_z eigenstates,
   so the chi/quark 3-momenta MUST carry transverse (x,y) components — otherwise
   parity-odd structures like (chibar gamma5 chi)(qbar gamma5 q) evaluate to zero
   on every sample and the completeness guard would MISS them (a false clean fit).
   We therefore tilt every momentum off the z axis and use several directions. *)
$chiDirs = {{0.30, 0.00, 0.35}, {0.00, 0.40, 0.20}, {0.25, 0.25, 0.20},
            {0.35, 0.15, 0.00}, {0.10, 0.30, 0.25}};
$qDirs   = {{0.40, 0.10, 0.00}, {0.10, 0.30, 0.20}, {0.20, 0.20, 0.25},
            {0.00, 0.35, 0.15}, {0.30, 0.00, 0.30}};
sampleConfigs[mchi_, mq_, vscale_:1.0] := Module[{spins, cfgs},
  spins = Tuples[{1, -1}, 4];
  cfgs = Flatten[Table[
    Module[{kchi, kq, kin},
      kchi = onShell[vscale $chiDirs[[d]] mchi, mchi];
      kq   = onShell[vscale $qDirs[[d]] mq, mq];
      kin = {k[1] -> kchi, k[3] -> kchi, k[2] -> kq, k[4] -> kq,
             MassFChi[_] -> mchi, MassFd[_] -> mq, MassFu[_] -> mq};
      Table[<|"kin" -> kin,
              "spin" -> {k[1] -> s[[1]], k[3] -> s[[2]], k[2] -> s[[3]], k[4] -> s[[4]]}|>,
        {s, spins}]],
    {d, Length[$chiDirs]}], 1];
  cfgs];


(* ============================================================================
   5.  Projection: solve M(config) = Sum_op c_op O_op(config)  (Decision 3.2)
   ============================================================================
   `M` is the F-symbolic amplitude with fully-numeric coefficients (couplings, PV
   values, masses, SumOver sums already substituted; chains F_i kept symbolic).
   `abbr` is the real Abbr[] WeylChain table (F_i -> WeylChain[...]).  Returns an
   Association including per-operator coefficients, the completeness residual, and
   the structural chain classification. *)

(* Completeness tolerance: max per-config ||resid||/||M|| for a clean fit.  Set at
   1e-4 (documented): the recognized parity-even set {S, Tq, Tchi} spans the
   leading SI structure at the sample velocities (~0.3); a residual above this
   flags content the SI set does not span, which must not be silently dropped.
   CAUTION (PR #33 review): a large residual is NOT evidence for any particular
   missing operator — on the real amp no Fierz-complete bilinear set spans it,
   and the ||M|| scale anomaly + unphysical-lambda PV warnings point to a
   static-coefficient / off-axis-chain kinematic inconsistency.  This is a
   LEADING-ORDER guard — the full velocity expansion (C^(1)/C^(2) twist-2 split,
   sub-leading operators) is build-order item 4. *)
$completenessTol = 1.0*^-4;

(* AMENDED completeness bar (DESIGN-ITEM4-AMENDMENT.md Ruling 3): the FULL
   (Fierz-complete reference) basis must span the amplitude to numerical
   precision — a residual above this is structural (un-spannable content or a
   projector bug), never an "expected physics residual".  The 3-op residual
   ($completenessTol above) remains REPORTED for continuity but is no longer the
   shipping guard: any amplitude with Z/W content legitimately carries large
   out-of-span-of-3-ops (e.g. axial x axial) structure. *)
$fullCompletenessTol = 1.0*^-8;

projectOperators[M_, abbr_List, mchi_, mq_, vscale_:1.0] := Module[
  {cc, badChains, fsyms, chainDefs, cfgs, Mvals, opCols, opNames, mat, sol,
   fit, residVec, mnorm, relResid, worstIdx, coeffs, projClass,
   diagNames, fullNames, fullCols, fullMat, fullSol, fullCoeffs, fullFit,
   fullResidVec, fullRelResid, diagShares, siShift},
  cc = chainClass[abbr];
  badChains = unrecognizedChains[abbr];
  (* FAIL-FAST structural guard (F1/F2): any chain whose WeylChain is outside the
     recognized {chi|quark|mixed} x {rank 0|1} taxonomy (e.g. a rank>=2 double
     insertion, or a non-fermion-line spinor pair) is a structure this projector
     does not know how to map to an operator -> refuse, naming it, rather than
     silently fitting garbage. *)
  If[Length[badChains] > 0,
    Return[<|"ok" -> False, "reason" -> "UNRECOGNIZED-CHAIN-STRUCTURE",
             "unrecognized_chains" -> (ToString /@ badChains),
             "classification" -> cc|>]];
  fsyms = Keys[cc];
  chainDefs = Association[Cases[abbr, (f_ -> wc_WeylChain) :> (f -> wc)]];

  cfgs = sampleConfigs[N[mchi], N[mq], vscale];
  opNames = Keys[$opRefs];
  diagNames = Keys[$opRefsDiag];
  fullNames = Join[opNames, diagNames];

  (* evaluate M, the 3 SI reference ops, AND the diagnostic reference basis on
     each config (one pass — the chain substitution dominates the cost) *)
  {Mvals, opCols, fullCols} = Transpose[Table[
    Module[{kin = cfg["kin"], spin = cfg["spin"], frule, mval, orow, drow},
      frule = (# -> chainValueOn[chainDefs[#], kin, spin]) & /@ fsyms;
      mval = M /. frule;
      orow = Table[$opRefs[op][kin, spin, N[mchi], N[mq]], {op, opNames}];
      drow = Table[$opRefsDiag[op][kin, spin, N[mchi], N[mq]], {op, diagNames}];
      {mval, orow, Join[orow, drow]}],
    {cfg, cfgs}]];

  (* guard: M must be numeric after chain substitution (else stray symbols) *)
  If[! AllTrue[Mvals, NumberQ[N[#]] &],
    Return[<|"ok" -> False, "reason" -> "M_NONNUMERIC_AFTER_CHAINS",
             "classification" -> cc|>]];

  (* PRODUCTION 3-op least-squares solve (unchanged behavior) *)
  mat = N[opCols];
  sol = Quiet[LeastSquares[mat, N[Mvals]]];
  coeffs = AssociationThread[opNames -> sol];
  fit = mat . sol;
  residVec = N[Mvals] - fit;
  mnorm = Norm[N[Mvals]];
  relResid = If[mnorm < 1*^-300, Norm[residVec], Norm[residVec]/mnorm];
  worstIdx = If[Length[residVec] > 0, First[Ordering[Abs[residVec], -1]], 0];

  (* FULL-BASIS (Fierz-complete reference) fit — Ruling 1/3 instrumentation.
     PseudoInverse (SVD, min-norm) rather than LeastSquares: the reference set is
     deliberately generous and may be rank-deficient on the sample set; the SVD
     solution is stable and reproducible under column near-degeneracy. *)
  fullMat = N[fullCols];
  fullSol = Quiet[PseudoInverse[fullMat, Tolerance -> 1.0*^-10] . N[Mvals]];
  fullCoeffs = AssociationThread[fullNames -> fullSol];
  fullFit = fullMat . fullSol;
  fullResidVec = N[Mvals] - fullFit;
  fullRelResid = If[mnorm < 1*^-300, Norm[fullResidVec], Norm[fullResidVec]/mnorm];

  (* per-operator absorbed-norm share: ||c_op * O_op-column|| / ||M||  (names the
     absorbing operators; sidecar diagnostics only, Ruling 2) *)
  diagShares = AssociationThread[fullNames ->
    Table[Abs[fullCoeffs[fullNames[[j]]]] Norm[fullMat[[All, j]]]/(mnorm + 1*^-300),
      {j, Length[fullNames]}]];

  (* SI-extraction stability (Ruling 3 criterion 2): 3-op vs full-basis C_scalar *)
  siShift = If[Abs[coeffs["C_scalar"]] < 1*^-300, Abs[fullCoeffs["C_scalar"]],
    Abs[(fullCoeffs["C_scalar"] - coeffs["C_scalar"])/coeffs["C_scalar"]]];

  (* structural cross-check classification of which chains are present *)
  projClass = <|
    "scalar_chains" -> Keys[Select[cc, (#["line"] =!= "mixed" && #["rank"] == 0 &&
                             #["line"] =!= "UNRECOGNIZED") &]],
    "vector_chains" -> Keys[Select[cc, (#["rank"] == 1) &]],
    "mixed_chains"  -> Keys[Select[cc, (#["line"] === "mixed") &]]|>;

  <|
    "ok" -> True,
    "C_scalar"      -> coeffs["C_scalar"],
    "C_twist2"      -> coeffs["C_twist2"],
    "C_chi_vector"  -> coeffs["C_chi_vector"],
    (* 3-op residual: REPORTED for continuity; no longer the shipping guard *)
    "completeness_rel_residual" -> relResid,
    (* AMENDED guard (Ruling 3 criterion 1): full-basis span to num. precision *)
    "full_basis_completeness_rel_residual" -> fullRelResid,
    "completeness_ok" -> (fullRelResid < $fullCompletenessTol),
    "si3_completeness_ok" -> (relResid < $completenessTol),
    "C_scalar_full" -> fullCoeffs["C_scalar"],
    "C_twist2_full" -> fullCoeffs["C_twist2"],
    "si_shift_rel" -> siShift,
    "full_basis_coeffs" -> fullCoeffs,
    "absorbed_norm_shares" -> diagShares,
    "worst_config_residual" -> If[worstIdx > 0, Abs[residVec[[worstIdx]]], 0.],
    "n_configs" -> Length[cfgs],
    "vscale" -> vscale,
    "unrecognized_chains" -> (ToString /@ badChains),
    "classification" -> cc,
    "present" -> projClass
  |>];


(* ============================================================================
   6.  residualSymbols — early loud guard on unresolved abbreviations
   ============================================================================
   After chain substitution M must be numeric.  A residual Sub#### (bare-symbol
   OR function-form Sub####[args] — F3 fix: scan HEADS too) or a free
   FormCalc/coupling symbol means the amplitude was not fully numeric-substituted
   (the dominant SD failure: amp_reduced.m Put[] without its Subexpr[] table).
   Return the offending symbols so the driver fails LOUDLY at a named guard. *)
$forbiddenCouplings = {"ZN", "UM", "UP", "ZDL", "ZDR", "ZUL", "ZUR", "Yu", "Yd",
   "yh1", "yh2", "g1", "g2", "g3", "Lam", "vvSM", "PhaseFS", "CTW", "STW",
   "MassFChi", "MassFd", "MassFu", "Masshh", "MassAh", "MassHp",
   "MassVWp", "MassVZ", "MassFChiM"};

residualSymbols[M_] := DeleteDuplicates[Cases[M,
   s_Symbol /; (
     StringMatchQ[SymbolName[s], "Sub" ~~ DigitCharacter ..] ||
     MemberQ[$forbiddenCouplings, SymbolName[s]]),
   Infinity, Heads -> True]];
