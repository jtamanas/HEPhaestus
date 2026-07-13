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
   3b.  ROTATED-COMPLETE reference instrument
        (DESIGN-ITEM4-AMENDMENT2.md + DESIGN-ITEM4-AMENDMENT2R1.md)
   ============================================================================
   MEASUREMENT INSTRUMENTATION, NOT a physical-operator extension.  THE RULE
   (AMENDMENT Ruling 2, unchanged): only {C_scalar, C_twist2 (C^(1,2)), C_G}
   may ever flow toward nucleon matching; every coefficient fitted on this
   instrument is a DIAGNOSTIC, emitted under out_of_span_diagnostics, never
   matched, never quoted as a cross-section.  match_nucleon.py hard-refuses SD
   couplings (invariant kept).

   HISTORY / RECONCILIATION (binding account of the 0.669 residual, per
   pr35-rereview/REVIEW.md + AMENDMENT2): the first "Fierz-complete" 27-column
   basis was rank 12 (cond 4.1e5; D_Vq_Ac == D_Aq_Vc to 13 digits; 7
   pseudoscalar columns identically zero at the purely FORWARD sample
   kinematics, where ubar(p)g5u(p) == 0 exactly), and the amplitude carries two
   MAJORANA-CROSSED monomials (F5*F6, F7*F8: both chains chi-barred, pairing
   incoming-together/outgoing-together) that NO chi(x)q line-product dictionary
   can hold unrotated (probe8: 0.186 residual each; all 14 other monomials
   in-span at ~2e-15).  The historical 0.669 full-basis residual was therefore
   an INSTRUMENT ARTIFACT of a rank-deficient basis plus unrotated Majorana-
   crossed content — it carried NO physics meaning.  The earlier "confirms the
   frozen-kinematics hypothesis" reading is RETRACTED: fixed scalar
   coefficients cannot create content orthogonal to a complete local basis
   (REVIEW.md Claim 2).  Per-config kinematics stays DEMOTED with two
   pre-registered reopen triggers (AMENDMENT2 Ruling 2).

   THE INSTRUMENT (this revision):
   1. Reference columns = the free line-product dictionary
      (chibar G_i chi)(qbar G_j q), G_i in the 16-Gamma basis -> 256 named
      columns R_<i>_<j>.  Probe8 established every DIRECT monomial of the real
      amplitude lies in this span to ~2e-15 (same-line EoM reductions).
   2. Sampling adds MOMENTUM-TRANSFER configurations (|q| = sqrt(TEPS) = 0.01,
      the amplitude's own T) to the forward set: at forward kinematics
      ubar(p)g5u(p) == 0 kills every pseudoscalar column (the review's 7 null
      columns) and collapses the rank.  Off-axis all-helicity sampling is kept
      (parity-even sampling remains REJECTED as guard-blinding).
   3. The two Majorana-crossed monomials are C-CONJUGATE-THEN-ROTATED into the
      chi(x)q sector (AMENDMENT2R1 R1/R2; NO crossed reference columns — they
      would park real crossed-box SI-scalar strength away from C_scalar).
      Realization, fully machine-evaluated (A2: no transcribed identity):
        thread C = i g2 g0 through the chain whose chi leg must become the
        unbarred reference end,  ubar(k1) A u(k2) = [u(k2)^T C^-1][C A^T C^-1]
        [C ubar(k1)^T]  (pure transpose algebra), then 16-Gamma completeness
        on the adjacent outer product, then eliminate the conjugate spinors
        via the MEASURED Majorana relations (verified ~1e-16 in this rep):
          v(p,s) = C ubar(p,s)^T = s * g5 u(p,-s)
          u(p,s)^T C^-1 = s * ubar(p,-s) K,   K = (C^-1 g5 C)^T
      The net production form is the flipped-spin re-evaluation
          rot(FaFb)(c) = s(k1) s(k4) * (FaFb)(c with s(k1),s(k4) flipped)
      whose equality with the CONSTANT-coefficient algebraic direct combination
          Sum_IJ Ginv_IJ (chibar B_J g5 chi)(c) * (qbar dress(A' B_I B) q)(c),
          dress(Mx) = -K C Mx^T K^T C^-1 g5,   A' = C A^T C^-1
      is the SD-FIERZ-ROTATION-INEXACT guard (< 1e-12 scale-relative, every
      run — the identity, including the Majorana phase convention, is checked
      by evaluation, never trusted).  The rotation's ABSOLUTE sign was further
      validated by Majorana crossing symmetry (probeH, 2026-07): the
      opposite-direction mixed pair (F9*F10, F11*F12 — plain Fierz, in-span
      UNROTATED, sign-unambiguous) projects ~0 scalar (1.5e-14), and the
      rotated crossed pair agrees (5.5e-15), while the UNROTATED crossed pair
      projects a spurious -2.099e-7 onto O_S — i.e. the round-2 "direct-sector
      C_scalar = -2.0973e-7" was itself out-of-span leakage, not physics.
   4. FATAL PRE-FIT GUARDS (AMENDMENT2 Ruling 1): SVD rank == column count
      (null-space combinations NAMED), null/collinear column detection,
      cond < 1e4 (column-normalized), per-column identifiability < 1e-10.
      A rank-deficient instrument can never silently measure again.
   5. PERMANENT PER-MONOMIAL DIAGNOSTIC (AMENDMENT2R1 R3, probe8 made
      permanent): every F-monomial of the amplitude is INDIVIDUALLY fitted;
      the fatal bar is each monomial's CONTRIBUTION to the completeness
      residual (< 1e-8), with raw residuals reported — see the guard comment
      in projectOperators for the measured derivative-monomial rationale.
      Failure names the monomial. *)

$metric = {1, -1, -1, -1};
$sigmaMats = Table[(I/2) ($gamma[[mu]] . $gamma[[nu]] - $gamma[[nu]] . $gamma[[mu]]),
  {mu, 4}, {nu, 4}];

(* ---- 16-Gamma basis, inverse Gram, charge conjugation ---------------------- *)
$B16 = Join[{$id4, $g5}, Table[$gamma[[mu]], {mu, 4}],
  Table[$gamma[[mu]] . $g5, {mu, 4}],
  Flatten[Table[$sigmaMats[[mu, nu]], {mu, 4}, {nu, mu + 1, 4}], 1]];
$B16Names = Join[{"S", "P"}, Table["V" <> ToString[mu - 1], {mu, 4}],
  Table["A" <> ToString[mu - 1], {mu, 4}],
  Flatten[Table["T" <> ToString[mu - 1] <> ToString[nu - 1], {mu, 4}, {nu, mu + 1, 4}]]];
$B16Ginv = Inverse[N[Table[Tr[$B16[[i]] . $B16[[j]]], {i, 16}, {j, 16}]]];
$CC = I $gamma[[3]] . $gamma[[1]];      (* C = i g2 g0, Dirac rep *)
$CCinv = Inverse[$CC];
$KK = Transpose[$CCinv . $g5 . $CC];
fierzDress[Mx_] := -$KK . $CC . Transpose[Mx] . Transpose[$KK] . $CCinv . $g5;

(* general bilinear on the chi / quark line for an arbitrary 4x4 spin matrix *)
chiBilin[kin_, spin_, mat_] := Module[{ua, ub},
  ua = uSpinor[k[3] /. kin, MassFChi[1] /. kin, k[3] /. spin];
  ub = uSpinor[k[1] /. kin, MassFChi[1] /. kin, k[1] /. spin];
  ubar[ua] . mat . ub];
quarkBilin[kin_, spin_, mat_] := Module[{ua, ub},
  ua = uSpinor[k[4] /. kin, MassFd[1] /. kin, k[4] /. spin];
  ub = uSpinor[k[2] /. kin, MassFd[1] /. kin, k[2] /. spin];
  ubar[ua] . mat . ub];

(* ---- instrument columns: one row of the 256-column dictionary -------------- *)
$refNames = Flatten[Table["R_" <> $B16Names[[i]] <> "_" <> $B16Names[[j]],
  {i, 16}, {j, 16}]];
refRow[kin_, spin_] := Module[{cv, qv},
  cv = Table[chiBilin[kin, spin, $B16[[i]]], {i, 16}];
  qv = Table[quarkBilin[kin, spin, $B16[[j]]], {j, 16}];
  Flatten[Outer[Times, cv, qv]]];
(* the SI scalar (chibar chi)(qbar q) is dictionary column R_S_S *)
$refScalarName = "R_S_S";

(* ---- Majorana-crossed monomial detection + rotation ------------------------ *)
(* a chain is "crossed-type" when its BARRED (first) spinor is the chi and its
   unbarred spinor is a quark; two such chains multiplied = a Majorana-crossed
   monomial (both chi legs barred: F5*F6 / F7*F8 layout). *)
barChiMixedQ[wc_WeylChain] := Module[{sp = Cases[List @@ wc, _Spinor]},
  Length[sp] === 2 && $chiMassQ[sp[[1, 2]]] && $quarkMassQ[sp[[2, 2]]]];
chainLegMomenta[wc_WeylChain] := (#[[1]] &) /@ Cases[List @@ wc, _Spinor];

(* numeric 4x4 chain matrix (chirality projector . slashed insertions), the
   same structure chainValueOn sandwiches between the end spinors *)
chainMatrixOn[wc_WeylChain, kin_] := Module[{args, chir, ins},
  args = List @@ wc;
  chir = FirstCase[args, i_Integer /; (i === 6 || i === 7), 6];
  ins = DeleteCases[DeleteCases[args, _Spinor], i_Integer /; (i === 6 || i === 7)];
  $Pom[chir] . If[ins === {}, $id4, Dot @@ (slash[# /. kin] & /@ ins)]];

(* Rotated production value: rot(FaFb)(c) = s(kA_chi) s(kB_q) * (FaFb)(pi(c)),
   pi flips the spin of chain A's chi leg and chain B's q leg.  Chain A is the
   one whose chi leg is k[1] (the reference-unbarred end), chain B the one
   whose chi leg is k[3].  Returns $Failed on an unsupported layout (loud in
   the caller — never a silent guess). *)
crossedRotValue[wcA_WeylChain, wcB_WeylChain, kin_, spin_] := Module[
  {mA = chainLegMomenta[wcA], mB = chainLegMomenta[wcB], a = wcA, b = wcB,
   sflip, s1, s4},
  If[mA[[1]] === k[3], {a, b} = {wcB, wcA}; {mA, mB} = {mB, mA}];
  If[! (mA === {k[1], k[2]} && mB === {k[3], k[4]}), Return[$Failed]];
  s1 = k[1] /. spin; s4 = k[4] /. spin;
  sflip = spin /. {(k[1] -> s_) :> (k[1] -> -s), (k[4] -> s_) :> (k[4] -> -s)};
  s1 s4 chainValueOn[a, kin, sflip] chainValueOn[b, kin, sflip]];

(* Algebraic constant-coefficient direct form of the same rotated monomial —
   the OTHER side of the SD-FIERZ-ROTATION-INEXACT guard *)
crossedRotAlgebraic[wcA_WeylChain, wcB_WeylChain, kin_, spin_] := Module[
  {mA = chainLegMomenta[wcA], a = wcA, b = wcB, Am, Bm, Ap, cv, qv},
  If[mA[[1]] === k[3], {a, b} = {wcB, wcA}];
  Am = chainMatrixOn[a, kin]; Bm = chainMatrixOn[b, kin];
  Ap = $CC . Transpose[Am] . $CCinv;
  cv = Table[chiBilin[kin, spin, $B16[[j]] . $g5], {j, 16}];
  qv = Table[quarkBilin[kin, spin, fierzDress[Ap . $B16[[i]] . Bm]], {i, 16}];
  Sum[$B16Ginv[[i, j]] cv[[j]] qv[[i]], {i, 16}, {j, 16}]];

(* ---- fatal pre-fit instrument guards (AMENDMENT2 Ruling 1) ----------------- *)
$refCondTol = 1.0*^4;
$refIdentTol = 1.0*^-10;
$refCollinTol = 1.0*^-10;   (* pairwise |cos| > 1 - this  => collinear *)
$refNullTol = 1.0*^-12;     (* ||col|| < this * ||mat||_F => null *)

referenceBasisGuards[mat_?MatrixQ, names_List] := Module[
  {fro, norms, nullIdx, nmat, sv, rank, cond, gramI, identErr, colPairs, vlist,
   nullCombos},
  fro = Norm[mat, "Frobenius"];
  norms = Norm /@ Transpose[mat];
  nullIdx = Flatten[Position[norms, x_ /; x < $refNullTol fro, {1}, Heads -> False]];
  If[nullIdx =!= {},
    Return[<|"ok" -> False, "reason" -> "SD-PROJECTION-BASIS-ILLCONDITIONED",
      "detail" -> "null columns: " <> ToString[names[[nullIdx]]]|>]];
  nmat = Transpose[Transpose[mat]/norms];
  colPairs = Reap[Do[
    If[Abs[Conjugate[nmat[[All, i]]] . nmat[[All, j]]] > 1 - $refCollinTol,
      Sow[{names[[i]], names[[j]]}]],
    {i, Length[names]}, {j, i + 1, Length[names]}]][[2]];
  If[colPairs =!= {},
    Return[<|"ok" -> False, "reason" -> "SD-PROJECTION-BASIS-ILLCONDITIONED",
      "detail" -> "collinear column pairs (|cos| > 1-1e-10): " <>
        ToString[First[colPairs]]|>]];
  sv = SingularValueList[nmat, Tolerance -> 0];
  rank = Count[sv, x_ /; x > 1*^-10 Max[sv]];
  If[rank < Length[names],
    (* NAME the null-space combinations: top-weight columns of each null
       right-singular vector *)
    vlist = SingularValueDecomposition[nmat][[3]];
    nullCombos = Table[Module[{v = vlist[[All, jj]], top},
        top = Ordering[Abs[v], -3];
        ToString[Thread[names[[top]] -> Round[v[[top]], 0.001]]]],
      {jj, rank + 1, Length[names]}];
    Return[<|"ok" -> False, "reason" -> "SD-PROJECTION-BASIS-RANK-DEFICIENT",
      "detail" -> "rank " <> ToString[rank] <> " of " <> ToString[Length[names]] <>
        " (tol 1e-10*sigma_max); null-space combinations: " <>
        StringRiffle[nullCombos, " | "], "rank" -> rank|>]];
  cond = Max[sv]/Min[sv];
  If[cond >= $refCondTol,
    Return[<|"ok" -> False, "reason" -> "SD-PROJECTION-BASIS-ILLCONDITIONED",
      "detail" -> "cond(column-normalized) = " <> ToString[cond, InputForm] <>
        " >= " <> ToString[$refCondTol, InputForm], "cond" -> cond|>]];
  gramI = PseudoInverse[nmat] . nmat;
  identErr = Max[Abs[gramI - IdentityMatrix[Length[names]]]];
  If[identErr >= $refIdentTol,
    Return[<|"ok" -> False, "reason" -> "SD-PROJECTION-BASIS-UNIDENTIFIABLE",
      "detail" -> "per-column synthetic recovery error " <>
        ToString[identErr, InputForm] <> " >= " <>
        ToString[$refIdentTol, InputForm], "ident_err" -> identErr|>]];
  <|"ok" -> True, "rank" -> rank, "cond" -> cond, "ident_err" -> identErr,
    "n_columns" -> Length[names]|>];

(* Retained convenience momenta (used by tests/fixtures) *)
$PqOf[kin_] := (k[2] + k[4])/2 /. kin;
$PcOf[kin_] := (k[1] + k[3])/2 /. kin;


(* ============================================================================
   3c.  PRODUCTION path (DESIGN-ITEM4-AMENDMENT3.md Ruling 1)
   ============================================================================
   The 3-op fit on the UNROTATED amplitude is RETIRED as the production SI
   extractor (measured si_shift 100.1% fired the pre-registered AMENDMENT2
   Ruling-3 clause; the unrotated Majorana-crossed monomials project a spurious
   scalar onto O_S — probeH crossing symmetry).  It survives ONLY as
   (a) the byte-stable triangle-continuity fixture path (section 5 production
   leg, bit-for-bit contract) and (b) a cross-instrument consistency probe
   evaluated on the ROTATED amplitude.

   PRODUCTION COEFFICIENTS:
   - C_scalar = the rotated-complete instrument's scalar (x) scalar dictionary
     coefficient R_S_S (transfer sampling, canonical v).  SHIPPING GUARD
     (replaces SD-SI-EXTRACTION-UNSTABLE): THREE independent instruments must
     agree on C_scalar within max(1% relative, 6e-10 absolute — the rank-2
     dd-expansion budget 3e-3 times the 2.1e-7 triangle scale):
       (1) the 3-op fit on the ROTATED amplitude (forward sample set),
       (2) the transfer-sampled dictionary R_S_S (the shipping value),
       (3) a forward-manifold retained-dictionary R_S_S (golden-spiral
           directions, R_S_S-seeded greedy retention — an independent sampling
           manifold AND an independent column-selection scheme).
     Any disagreement -> SD-SI-CROSS-INSTRUMENT-DISAGREE, Exit[3] at the driver
     (projInstrumentAssert).  NOTE the forward instrument carries NO hard cond
     bar of its own (measured retained cond 2.9e4 at canonical v, probeE2): its
     authority here is only as a cross-check, and any conditioning-induced bias
     beyond the agreement bar IS the guard firing.
   - C_twist2 split (C^(1), C^(2)) = contracted twist-2 reference operators fit
     on the ROTATED amplitude (NOT the local dictionary: derivative content is
     out of local span by construction off the forward manifold — the ratified
     probe8 exemption).  CONVENTION (pinned, resolving the DESIGN-ITEM4.md A5
     [VERIFY]): Hisano-Ishiwata-Nagata arXiv:1104.0228 Eqs. (2)-(3),
       L_eff  ⊃  (g_q^(1)/m_chi)   chibar i d^mu gamma^nu chi O^q_{mu nu}
              +  (g_q^(2)/m_chi^2) chibar i d^mu i d^nu chi O^q_{mu nu},
       O^q_{mu nu} = (1/2) qbar i (D_mu gamma_nu + D_nu gamma_mu
                                   - (1/2) g_{mu nu} Dslash) q .
     The reference operators below are the FREE-SPINOR matrix elements with the
     symmetrized momenta P_chi = (k1+k3)/2, P_q = (k2+k4)/2 and the on-shell
     reduction qbar i Dslash q -> m_q qbar q:
       <O^q_{mu nu}> = (1/2)[P_q_mu (qbar gamma_nu q) + P_q_nu (qbar gamma_mu q)]
                       - (1/4) g_{mu nu} m_q (qbar q),
     normalized so the FITTED coefficients are C^(i) = g^(i)/m_chi, i.e. the A5
     contraction  f_N/m_N ⊃ (3/4) m_chi Sum_q [q(2)+qbar(2)] (C^(1)+C^(2))
     equals Hisano Eq. (6)'s  (3/4) [q(2)+qbar(2)] (g^(1)+g^(2))  exactly:
       ref(C^(1)) =          P_chi^mu (chibar gamma^nu chi) <O^q_{mu nu}>
       ref(C^(2)) = (1/m_chi) P_chi^mu P_chi^nu (chibar chi) <O^q_{mu nu}> .

   CONDITIONING (measured): ref(C^(1)) and ref(C^(2)) are IDENTICAL on every
   chi-spin-DIAGONAL config at forward kinematics (chibar gamma^nu chi -> 2 P^nu
   and chibar chi -> 2 m_chi collapse them onto the same value); only the
   chi-spin-off-diagonal rows separate them, so the raw {g1, g2} column pair is
   nearly parallel at DD kinematics (measured cond 1.05e5 — over the 1e4 bar).
   f_N consumes ONLY THE SUM C^(1)+C^(2) (Hisano Eq. (6): both multiply the same
   (3/4)[q(2)+qbar(2)] moment), so the fit basis is the exactly-equivalent
   orthogonalized pair
       O_sum = (ref1+ref2)/2  with coefficient  c_sum = C^(1)+C^(2)  (SHIPS),
       O_dif = (ref1-ref2)/2  with coefficient  c_dif = C^(1)-C^(2)  (DIAGNOSTIC)
   (exact linear reparametrization: C^(1) = (c_sum+c_dif)/2, C^(2) =
   (c_sum-c_dif)/2).  O_sum captures the common (near-parallel) direction and
   O_dif the small separating direction, so the FIT basis passes the fatal
   cond/identifiability guards honestly, while the g1/g2 SPLIT inherits the
   intrinsic near-degeneracy — it is reported as a diagnostic with exactly that
   caveat, never consumed by f_N. *)

$mdot[a_, b_] := a[[1]] b[[1]] - a[[2]] b[[2]] - a[[3]] b[[3]] - a[[4]] b[[4]];
chiVec[kin_, spin_]   := Table[chiBilin[kin, spin, $gamma[[mu]]], {mu, 4}];
quarkVec[kin_, spin_] := Table[quarkBilin[kin, spin, $gamma[[mu]]], {mu, 4}];

(* free-spinor matrix elements of the two Hisano twist-2 contractions *)
twist2Ref1[kin_, spin_, mchi_, mq_] := Module[
  {Pc = $PcOf[kin], Pq = $PqOf[kin], cv = chiVec[kin, spin],
   qv = quarkVec[kin, spin], Sq = quarkScalar[kin, spin]},
  (1/2) ($mdot[Pc, Pq] $mdot[cv, qv] + $mdot[Pc, qv] $mdot[cv, Pq])
    - (1/4) $mdot[Pc, cv] mq Sq];
twist2Ref2[kin_, spin_, mchi_, mq_] := Module[
  {Pc = $PcOf[kin], Pq = $PqOf[kin], qv = quarkVec[kin, spin],
   Sc = chiScalar[kin, spin], Sq = quarkScalar[kin, spin]},
  (Sc/mchi) ($mdot[Pc, Pq] $mdot[Pc, qv] - (1/4) $mdot[Pc, Pc] mq Sq)];

$opRefs2 = <|
  "C_scalar" -> Function[{kin, spin, mchi, mq},
    (chiScalar[kin, spin]) (quarkScalar[kin, spin])],
  "C_twist2_sum" -> Function[{kin, spin, mchi, mq},
    (twist2Ref1[kin, spin, mchi, mq] + twist2Ref2[kin, spin, mchi, mq])/2],
  "C_twist2_dif" -> Function[{kin, spin, mchi, mq},
    (twist2Ref1[kin, spin, mchi, mq] - twist2Ref2[kin, spin, mchi, mq])/2],
  "C_chi_vector" -> Function[{kin, spin, mchi, mq},
    (chiVector[kin, spin, (k[2] + k[4])/2 /. kin]) (quarkScalar[kin, spin])]
|>;

(* cross-instrument agreement bars (AMENDMENT3 Ruling 1) *)
$crossInstrTolRel = 0.01;
$crossInstrTolAbs = 6.0*^-10;

(* ---- rotated monomial evaluation over an arbitrary config list -------------
   Shared by the transfer-instrument leg of projectOperators, the forward
   instrument, and the production velocity leg.  Returns per-monomial values
   (crossed monomials C-conjugate-ROTATED) and, when checkAlgebraic is True,
   the scale-relative rotation-exactness maximum (the SD-FIERZ-ROTATION-INEXACT
   quantity; see the guard comment in projectOperators). *)
rotatedMonoVals[chainDefs_Association, fsyms_List, crules_List, crossedQ_List,
    cfgs_List, checkAlgebraic_:True] := Module[
  {rotAbsErr, rotScaleRef, refData, failed = False},
  rotAbsErr = ConstantArray[0., Length[crules]];
  rotScaleRef = ConstantArray[0., Length[crules]];
  refData = Table[Module[
      {kin = cfg["kin"], spin = cfg["spin"], fvals},
      fvals = Association[(# -> chainValueOn[chainDefs[#], kin, spin]) & /@ fsyms];
      Table[Module[{ex = Keys[crules][[t]], ss, v},
          ss = Flatten[Table[ConstantArray[fsyms[[i]], ex[[i]]], {i, Length[fsyms]}]];
          If[crossedQ[[t]],
            v = crossedRotValue[chainDefs[ss[[1]]], chainDefs[ss[[2]]], kin, spin];
            If[v === $Failed, failed = True; $Failed,
              If[checkAlgebraic,
                Module[{alg = crossedRotAlgebraic[chainDefs[ss[[1]]],
                    chainDefs[ss[[2]]], kin, spin]},
                  rotAbsErr[[t]] = Max[rotAbsErr[[t]], Abs[v - alg]];
                  rotScaleRef[[t]] = Max[rotScaleRef[[t]], Abs[v], Abs[alg]];
                  v],
                v]],
            Times @@ (fvals /@ ss)]],
        {t, Length[crules]}]],
    {cfg, cfgs}];
  <|"failed" -> failed,
    (* per monomial, over configs *)
    "mono_vals" -> If[failed, $Failed, Transpose[refData]],
    "rot_err_max" -> Max[0., MapThread[If[#2 > 0., #1/#2, 0.] &,
      {rotAbsErr, rotScaleRef}]]|>];

(* ---- 3-op fit, byte-equivalent arithmetic of the section-5 production leg --
   Reusable on ANY F-linear numeric amplitude (e.g. the driver's triangle-only
   sector: the bit-for-bit fixture contract -1.2831509485455282e-7 goes through
   exactly this construction).  fsyms may include chains absent from M. *)
threeOpFit[M_, chainDefs_Association, fsyms_List, mchi_, mq_, vscale_:1.0] := Module[
  {cfgs, Mvals, opCols, mat, sol},
  cfgs = sampleConfigs[N[mchi], N[mq], vscale];
  {Mvals, opCols} = Transpose[Table[
    Module[{kin = cfg["kin"], spin = cfg["spin"], frule, mval, orow},
      frule = (# -> chainValueOn[chainDefs[#], kin, spin]) & /@ fsyms;
      mval = M /. frule;
      orow = Table[$opRefs[op][kin, spin, N[mchi], N[mq]], {op, Keys[$opRefs]}];
      {mval, orow}],
    {cfg, cfgs}]];
  mat = N[opCols];
  sol = Quiet[LeastSquares[mat, N[Mvals]]];
  <|"coeffs" -> AssociationThread[Keys[$opRefs] -> sol],
    "rel_residual" -> If[Norm[N[Mvals]] < 1*^-300, Norm[N[Mvals] - mat . sol],
      Norm[N[Mvals] - mat . sol]/Norm[N[Mvals]]]|>];

(* ---- forward-manifold retained-dictionary instrument (probeE2, ported) -----
   Third C_scalar instrument: purely FORWARD sampling (k1 == k3, k2 == k4) on a
   golden-spiral direction set, exact-null columns excluded (31 pseudoscalar
   columns vanish identically at forward kinematics — ubar(p) g5 u(p) == 0),
   remaining columns greedily retained (R_S_S-seeded, threshold 1e-4 on
   normalized residual direction) so the fit never solves through the
   machine-noise tail that broke the naive forward fit (probeE: cond 3.9e16).
   The rotation-exactness identity is NOT re-checked here (checkAlgebraic
   False): the SAME crossedRotValue path is guarded against the algebraic form
   on the 1104-config transfer set every run; this leg adds only kinematics,
   not new rotation algebra. *)
$fwdNDirs = 50;
$fwdRetainTol = 1.0*^-4;
$fwdNullTol = 1.0*^-14;
fwdUnitDir[i_, n_, ph_] := Module[{z = 1. - 2. (i - 0.5)/n, r, th},
  r = Sqrt[1 - z^2]; th = 2. Pi i N[GoldenRatio] + ph; {r Cos[th], r Sin[th], z}];
forwardConfigs[mchi_, mq_, vscale_:1.0] := Flatten[Table[
  Module[{dc, dq, kchi, kq, kin},
    dc = (0.15 + 0.25 FractionalPart[i Sqrt[2.]]) fwdUnitDir[i, $fwdNDirs, 0.];
    dq = (0.15 + 0.25 FractionalPart[i Sqrt[3.] + 0.3]) fwdUnitDir[i, $fwdNDirs, 1.];
    kchi = onShell[vscale dc mchi, mchi]; kq = onShell[vscale dq mq, mq];
    kin = {k[1] -> kchi, k[3] -> kchi, k[2] -> kq, k[4] -> kq,
           MassFChi[_] -> mchi, MassFd[_] -> mq, MassFu[_] -> mq};
    Table[<|"kin" -> kin,
      "spin" -> {k[1] -> s[[1]], k[3] -> s[[2]], k[2] -> s[[3]], k[4] -> s[[4]]}|>,
      {s, Tuples[{1, -1}, 4]}]],
  {i, $fwdNDirs}], 1];

forwardScalarInstrument[chainDefs_Association, fsyms_List, crules_List,
    crossedQ_List, mchi_, mq_, vscale_:1.0] := Module[
  {cfgs, rot, fullMat, MrotVals, fro, norms, gpos, zn, nzIdx, nmat, seedPos,
   ordering, retIdx, Q, rm, svr, condRet, identRet, sol, resid, cS},
  cfgs = forwardConfigs[N[mchi], N[mq], vscale];
  rot = rotatedMonoVals[chainDefs, fsyms, crules, crossedQ, cfgs, False];
  If[rot["failed"],
    Return[<|"ok" -> False, "reason" -> "SD-FIERZ-ROTATION-INEXACT",
      "detail" -> "forward instrument: unsupported crossed-chain leg layout " <>
        "(chi legs must be k1/k3, quark legs k2/k4) — refusing"|>]];
  fullMat = N[Table[refRow[c["kin"], c["spin"]], {c, cfgs}]];
  MrotVals = N[Transpose[rot["mono_vals"]] . Values[crules]];
  fro = Norm[fullMat, "Frobenius"];
  norms = Norm /@ Transpose[fullMat];
  gpos = Position[$refNames, $refScalarName][[1, 1]];
  zn = Flatten[Position[norms, x_ /; x < $fwdNullTol fro, {1}, Heads -> False]];
  If[MemberQ[zn, gpos],
    Return[<|"ok" -> False, "reason" -> "SD-PROJECTION-BASIS-ILLCONDITIONED",
      "detail" -> "forward instrument: R_S_S column numerically null — " <>
        "cannot seed the retention, no forward C_scalar cross-check"|>]];
  nzIdx = Complement[Range[Length[$refNames]], zn];
  nmat = Transpose[Transpose[fullMat[[All, nzIdx]]]/norms[[nzIdx]]];
  seedPos = Position[nzIdx, gpos][[1, 1]];
  ordering = Join[{seedPos}, DeleteCases[Ordering[-norms[[nzIdx]]], seedPos]];
  retIdx = {}; Q = {};
  Do[Module[{col = nmat[[All, j]], r},
      r = If[Q === {}, col, col - Transpose[Q] . (Conjugate[Q] . col)];
      If[Norm[r] > $fwdRetainTol, AppendTo[retIdx, j]; AppendTo[Q, r/Norm[r]]]],
    {j, ordering}];
  rm = nmat[[All, Sort[retIdx]]];
  svr = SingularValueList[rm, Tolerance -> 0];
  condRet = Max[svr]/Min[svr];
  identRet = Max[Abs[PseudoInverse[rm] . rm - IdentityMatrix[Length[retIdx]]]];
  sol = Quiet[LeastSquares[rm, MrotVals]];
  resid = If[Norm[MrotVals] < 1*^-300, Norm[rm . sol - MrotVals],
    Norm[rm . sol - MrotVals]/Norm[MrotVals]];
  cS = sol[[Position[Sort[retIdx], seedPos][[1, 1]]]]/norms[[gpos]];
  <|"ok" -> True, "C_scalar_fwd" -> cS,
    "n_configs" -> Length[cfgs], "n_null_columns" -> Length[zn],
    "n_retained" -> Length[retIdx], "n_nonnull" -> Length[nzIdx],
    "retained_cond" -> condRet, "retained_ident_err" -> identRet,
    "completeness_rel_residual" -> resid|>];

(* ---- production velocity leg (AMENDMENT3 Ruling 2 replacement bar) ----------
   The 256-column transfer dictionary is honestly UNMEASURABLE at v/10 (cond
   ~ 1/v^2, ratified named refusal — Ruling 4c), so velocity stability of the
   PRODUCTION coefficients is measured on the two legs whose own conditioning
   guards stay green at reduced v: the 3-op fit on the rotated amplitude
   (forward samples) and the contracted twist-2 fit (its 4-column basis carries
   the same fatal rank/cond/identifiability guards).  Returns the measured
   coefficients at `vscale`, or ok -> False with the guard reason if this leg's
   OWN guards refuse (in which case drift is unmeasurable — a named outcome,
   never a silent value). *)
productionVLeg[M_, abbr_List, mchi_, mq_, vscale_] := Module[
  {cc, fsyms, chainDefs, crules, crossedQ, cfgs, refCfgs, rot, monoVals,
   MrotVals, mat, opCols, c3Sol, prodNames, prodMat, prodGuards, prodColNorms,
   prodSol},
  cc = chainClass[abbr];
  fsyms = Keys[cc];
  chainDefs = Association[Cases[abbr, (f_ -> wc_WeylChain) :> (f -> wc)]];
  crules = Quiet[CoefficientRules[M, fsyms]];
  crossedQ = Table[Module[{ex = Keys[crules][[t]], ss},
      ss = Flatten[Table[ConstantArray[fsyms[[i]], ex[[i]]], {i, Length[fsyms]}]];
      Length[ss] === 2 && ss[[1]] =!= ss[[2]] &&
        barChiMixedQ[chainDefs[ss[[1]]]] && barChiMixedQ[chainDefs[ss[[2]]]]],
    {t, Length[crules]}];
  cfgs = sampleConfigs[N[mchi], N[mq], vscale];
  refCfgs = referenceConfigs[N[mchi], N[mq], vscale];
  rot = rotatedMonoVals[chainDefs, fsyms, crules, crossedQ, refCfgs, True];
  If[TrueQ[rot["failed"]] || rot["rot_err_max"] >= $fierzRotationTol,
    Return[<|"ok" -> False, "reason" -> "SD-FIERZ-ROTATION-INEXACT",
      "detail" -> "production velocity leg at vscale " <> ToString[vscale] <>
        ": rotation exactness " <> ToString[rot["rot_err_max"], InputForm]|>]];
  monoVals = rot["mono_vals"];
  MrotVals = N[Transpose[monoVals] . Values[crules]];
  opCols = Table[Table[$opRefs[op][cfg["kin"], cfg["spin"], N[mchi], N[mq]],
    {op, Keys[$opRefs]}], {cfg, cfgs}];
  mat = N[opCols];
  c3Sol = Quiet[LeastSquares[mat, MrotVals[[1 ;; Length[cfgs]]]]];
  prodNames = Keys[$opRefs2];
  prodMat = N[Table[Table[$opRefs2[op][cfg["kin"], cfg["spin"], N[mchi], N[mq]],
    {op, prodNames}], {cfg, refCfgs}]];
  prodGuards = referenceBasisGuards[prodMat, ("CONTRACTED_" <> # &) /@ prodNames];
  If[! TrueQ[prodGuards["ok"]],
    Return[Join[prodGuards, <|"detail" -> ToString[Lookup[prodGuards, "detail", ""]] <>
      " (contracted production twist-2 basis, velocity leg vscale " <>
      ToString[vscale] <> ")"|>]]];
  prodColNorms = Norm /@ Transpose[prodMat];
  prodSol = Quiet[LeastSquares[
    Transpose[Transpose[prodMat]/prodColNorms], MrotVals]]/prodColNorms;
  <|"ok" -> True, "vscale" -> vscale,
    "threeop_rotated_coeffs" -> AssociationThread[Keys[$opRefs] -> c3Sol],
    "contracted_coeffs" -> AssociationThread[prodNames -> prodSol],
    "production_basis_cond" -> prodGuards["cond"]|>];



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

(* ---- reference-instrument sampling (AMENDMENT2 Ruling 1) --------------------
   The PRODUCTION 3-op fit keeps sampleConfigs UNCHANGED (byte-stable fixture
   contract).  The rotated-complete instrument additionally needs MOMENTUM
   TRANSFER: at forward configs (k1 == k3) the pseudoscalar bilinear
   ubar(p,s) g5 u(p,s') vanishes IDENTICALLY (kinematic null, not a bug), which
   is exactly how the review's 7 null columns and the rank-12 collapse arose.
   Transfer scale |q| = sqrt(TEPS) = 0.01 GeV — the amplitude's own T — applied
   with exact 3-momentum conservation (k1 - k3 = k4 - k2 = q), both ends
   on-shell.  The transfer is NOT scaled by vscale: vscale scales VELOCITIES
   (the v -> v/10 DD-limit probe), while sqrt(TEPS) is the fixed
   momentum-transfer scale of the amplitude itself — scaling it with v
   collapses the pseudoscalar excitation and blows the conditioning
   (measured: cond 2.7e7 at vscale 0.1 with scaled transfers).
   ROW COUNT + CONDITIONING: 256 free columns need well over 256 rows for the
   rank guard to be a real test, and the cond < 1e4 bar is met by DIVERSIFYING
   the sampling (never by tuning bars): the instrument uses its OWN 8-member
   direction sets ($refChiDirs/$refQDirs — supersets of the production
   $chiDirs/$qDirs, which stay byte-identical for the 3-op fixture contract)
   crossed with 8 transfer vectors of varied magnitude and orientation (quark
   direction decorrelated by a cyclic shift): 8x8 kins x 16 spins = 1024
   transfer rows + 80 forward rows = 1104 rows.  Measured at the canonical
   point: rank 256, cond 6.1e3, well inside the bars (probeD, 2026-07). *)
$refChiDirs = {{0.30, 0.00, 0.35}, {0.00, 0.40, 0.20}, {0.25, 0.25, 0.20},
               {0.35, 0.15, 0.00}, {0.10, 0.30, 0.25}, {0.15, -0.30, 0.25},
               {-0.20, 0.10, 0.35}, {0.30, 0.20, -0.15}};
$refQDirs   = {{0.40, 0.10, 0.00}, {0.10, 0.30, 0.20}, {0.20, 0.20, 0.25},
               {0.00, 0.35, 0.15}, {0.30, 0.00, 0.30}, {-0.25, 0.20, 0.10},
               {0.15, -0.10, 0.30}, {0.05, 0.25, -0.30}};
$qTransfers = {{0.010, 0., 0.}, {0., 0.007, -0.007}, {-0.006, 0.008, 0.},
               {0.005, 0.005, 0.007}, {0., -0.010, 0.}, {0.012, -0.005, 0.004},
               {-0.004, -0.006, 0.011}, {0.007, 0.011, -0.003}};
referenceConfigs[mchi_, mq_, vscale_:1.0] := Join[
  sampleConfigs[mchi, mq, vscale],
  Flatten[Table[
    Module[{kchi, kq, qv, kin},
      kchi = vscale $refChiDirs[[d]] mchi;
      kq = vscale $refQDirs[[Mod[d + t - 2, Length[$refQDirs]] + 1]] mq;
      qv = $qTransfers[[t]];   (* fixed T-scale, NOT velocity-scaled (above) *)
      kin = {k[1] -> onShell[kchi, mchi], k[3] -> onShell[kchi - qv, mchi],
             k[2] -> onShell[kq, mq],     k[4] -> onShell[kq + qv, mq],
             MassFChi[_] -> mchi, MassFd[_] -> mq, MassFu[_] -> mq};
      Table[<|"kin" -> kin,
              "spin" -> {k[1] -> s[[1]], k[3] -> s[[2]], k[2] -> s[[3]], k[4] -> s[[4]]}|>,
        {s, Tuples[{1, -1}, 4]}]],
    {d, Length[$refChiDirs]}, {t, Length[$qTransfers]}], 2]];


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
   CAUTION (PR #33 review, RESOLVED in round 3): a large residual is NOT
   evidence for any particular missing operator.  The once-unidentified 3-op
   out-of-span content on the real amp IS now identified (re-review probe8 +
   AMENDMENT2): unrotated Majorana-crossed chain monomials, which no chi(x)q
   line-product set spans unrotated — handled by the rotated-complete
   instrument in section 3b.  This 3-op residual is a LEADING-ORDER report
   (si3), no longer the shipping guard. *)
$completenessTol = 1.0*^-4;

(* AMENDED completeness bar (AMENDMENT Ruling 3, RE-DERIVED per AMENDMENT2
   Ruling 4 / re-review RF2): the ROTATED-COMPLETE instrument — the rotated
   amplitude fitted against the rank-verified, identifiability-controlled
   direct-sector dictionary — must span to numerical precision.  Reachable BY
   CONSTRUCTION (probe8: direct monomials in-span ~2e-15; crossed monomials
   in-span after the C-conjugate rotation), so a residual above this bar is
   structural (a projector bug or genuinely new content), never an "expected
   physics residual".  Pre-registered post-fix prediction: < 1e-10; residual
   > 1e-6 with rotation + rank guards green REOPENS per-config kinematics
   (AMENDMENT2 Ruling 2 trigger (a)).  The 3-op residual ($completenessTol
   above) remains REPORTED for continuity but is not the shipping guard. *)
$fullCompletenessTol = 1.0*^-8;

(* rotation-exactness and per-monomial in-span bars (AMENDMENT2R1).
   $monomialContribTol is on each monomial's CONTRIBUTION to the completeness
   residual (raw_resid * |coeff| * ||mono|| / ||M_rot||), not the raw in-span
   residual — see the guard comment inside projectOperators for the measured
   derivative-monomial rationale.  Raw residuals are reported per monomial. *)
$fierzRotationTol = 1.0*^-12;
$monomialContribTol = 1.0*^-8;

projectOperators[M_, abbr_List, mchi_, mq_, vscale_:1.0] := Module[
  {cc, badChains, fsyms, chainDefs, cfgs, Mvals, opCols, opNames, mat, sol,
   fit, residVec, mnorm, relResid, worstIdx, coeffs, projClass,
   crules, monoNames, crossedQ, refCfgs, rotErrMax,
   refData, monoVals,
   fullMat, MrotVals, basisGuards, colNorms, nmat, fullSol, fullCoeffs,
   fullFit, fullResidVec, refMnorm, fullRelResid, monoResids, monoContribs,
   derivMonoQ, monoWorst, diagShares, siShift,
   c3rotSol, c3rotCoeffs, prodNames, prodMat, prodGuards, prodColNorms,
   prodSol, prodCoeffs, fwd, crossVals, crossAbs, crossDiff, crossTol},
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

  (* ---- PRODUCTION LEG (unchanged; fixture-stable): M + the 3 SI ops on the
     UNCHANGED forward sample set, plain LeastSquares.  This code path is the
     bit-for-bit contract behind the triangle fixture -1.2831509485455282e-7 —
     the instrument below must never feed back into it. *)
  {Mvals, opCols} = Transpose[Table[
    Module[{kin = cfg["kin"], spin = cfg["spin"], frule, mval, orow},
      frule = (# -> chainValueOn[chainDefs[#], kin, spin]) & /@ fsyms;
      mval = M /. frule;
      orow = Table[$opRefs[op][kin, spin, N[mchi], N[mq]], {op, opNames}];
      {mval, orow}],
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

  (* ---- ROTATED-COMPLETE INSTRUMENT LEG (AMENDMENT2 + 2R1; diagnostics only,
     Ruling 2 — nothing here feeds nucleon matching) --------------------------- *)

  (* monomial census of M in F-space (compact polynomial: coeffs are numbers) *)
  crules = Quiet[CoefficientRules[M, fsyms]];
  If[Max[Total /@ Keys[crules]] > 2,
    Return[<|"ok" -> False, "reason" -> "SD-FIERZ-ROTATION-INEXACT",
      "detail" -> "amplitude has F-degree > 2; the degree-2 monomial rotation " <>
        "does not apply — refusing (never a silent guess)"|>]];
  monoNames = Table[Module[{ex = Keys[crules][[t]], ss},
      ss = Flatten[Table[ConstantArray[fsyms[[i]], ex[[i]]], {i, Length[fsyms]}]];
      If[ss === {}, "CONST", StringRiffle[ToString /@ ss, "*"]]],
    {t, Length[crules]}];
  crossedQ = Table[Module[{ex = Keys[crules][[t]], ss},
      ss = Flatten[Table[ConstantArray[fsyms[[i]], ex[[i]]], {i, Length[fsyms]}]];
      Length[ss] === 2 && ss[[1]] =!= ss[[2]] &&
        barChiMixedQ[chainDefs[ss[[1]]]] && barChiMixedQ[chainDefs[ss[[2]]]]],
    {t, Length[crules]}];
  (* Monomials with exactly ONE barred-chi mixed chain (opposite-direction
     mixed pairs, e.g. F9*F10 / F11*F12: one chi-barred chain paired with a
     QUARK-barred chain) are IN-SPAN of the direct dictionary as they stand
     (probe8: residual 2e-15) and pass through UNTOUCHED, per AMENDMENT2R1 —
     the rotation applies ONLY to the both-chi-barred pairs.  Any monomial
     that in fact fails to project is caught, BY NAME, by the per-monomial
     out-of-span diagnostic below (probe8 made permanent) — a measured guard,
     not an assumed classification. *)

  refCfgs = referenceConfigs[N[mchi], N[mq], vscale];

  (* per-config chain values, monomial values (crossed ones ROTATED), rows.
     The SD-FIERZ-ROTATION-INEXACT guard compares, per rotated monomial, the
     flipped-spin production value against the constant-coefficient algebraic
     direct form.  The comparison is SCALE-relative (max |diff| over configs
     divided by the monomial's max magnitude over configs), NOT per-config
     relative: on configs where the monomial value is itself near the numeric
     null of the sampled bilinears, a per-config ratio measures rounding noise
     against a vanishing denominator (measured: per-config-relative inflates
     to 4.4e-11 at vscale 0.1 while scale-relative stays at 8.5e-16 — probeE2,
     2026-07).  Scale-relative is the uniform-norm statement of the identity
     and is what the < 1e-12 bar guards. *)
  refData = rotatedMonoVals[chainDefs, fsyms, crules, crossedQ, refCfgs, True];
  If[TrueQ[refData["failed"]],
    Return[<|"ok" -> False, "reason" -> "SD-FIERZ-ROTATION-INEXACT",
      "detail" -> "unsupported crossed-chain leg layout (chi legs must be " <>
        "k1/k3, quark legs k2/k4) — refusing, never a silent guess"|>]];
  rotErrMax = refData["rot_err_max"];
  If[rotErrMax >= $fierzRotationTol,
    Return[<|"ok" -> False, "reason" -> "SD-FIERZ-ROTATION-INEXACT",
      "detail" -> "scale-relative rotation exactness " <> ToString[rotErrMax, InputForm] <>
        " >= 1e-12 (flipped-spin production form vs machine-evaluated " <>
        "C-conjugate+16-Gamma direct combination)",
      "rotation_exactness_max" -> rotErrMax|>]];

  monoVals = refData["mono_vals"];                      (* per monomial, over cfgs *)
  fullMat = N[Table[refRow[cfg["kin"], cfg["spin"]], {cfg, refCfgs}]];
  MrotVals = N[Transpose[monoVals] . Values[crules]];   (* rotated amplitude *)

  (* fatal pre-fit instrument guards (rank / null+collinear / cond / ident) *)
  basisGuards = referenceBasisGuards[fullMat, $refNames];
  If[! TrueQ[basisGuards["ok"]], Return[Join[basisGuards, <|"classification" -> cc|>]]];

  (* column-normalized LS fit of the ROTATED amplitude *)
  colNorms = Norm /@ Transpose[fullMat];
  nmat = Transpose[Transpose[fullMat]/colNorms];
  fullSol = Quiet[LeastSquares[nmat, MrotVals]]/colNorms;
  fullCoeffs = AssociationThread[$refNames -> fullSol];
  fullFit = fullMat . fullSol;
  fullResidVec = MrotVals - fullFit;
  refMnorm = Norm[MrotVals];
  fullRelResid = If[refMnorm < 1*^-300, Norm[fullResidVec], Norm[fullResidVec]/refMnorm];

  (* PERMANENT PER-MONOMIAL DIAGNOSTIC (probe8 made permanent, AMENDMENT2R1 R3):
     every monomial is individually fitted against the instrument and NAMED on
     failure.  The FATAL bar is on each monomial's CONTRIBUTION to the full
     completeness residual (raw_resid * |coeff| * ||mono|| / ||M_rot||), not on
     the raw per-monomial residual: the real amplitude carries derivative
     (momentum-insertion, F13-F18) monomials whose LOCAL constant-coefficient
     decomposition is exact only on the forward (DD) manifold — at the transfer
     rows that repair the pseudoscalar rank their raw residual is O(0.1)
     regardless of numerical health, while their weight in M is 1e-9..1e-14
     (measured: worst raw F3*F13 = 0.189, worst contribution 9.6e-10 — probeF,
     2026-07).  A raw 1e-10 bar is therefore unreachable IN PRINCIPLE for any
     amplitude carrying derivative dust monomials; the contribution bar is the
     honest instrument-level statement and still names any monomial that
     actually damages completeness.  Raw residuals ship in the sidecar. *)
  monoResids = Table[Module[{v = N[monoVals[[t]]], sres, nv},
      nv = Norm[v];
      If[nv < 1*^-300, 0.,
        sres = Quiet[LeastSquares[nmat, v]];
        Norm[nmat . sres - v]/nv]],
    {t, Length[crules]}];
  monoContribs = Table[
    monoResids[[t]] Abs[Values[crules][[t]]] Norm[N[monoVals[[t]]]]/
      (refMnorm + 1*^-300), {t, Length[crules]}];
  (* DERIVATIVE EXEMPTION from the FATAL bar (not from reporting): a monomial
     containing a rank-1 (momentum-insertion) chain is a twist-2-family
     DERIVATIVE operator — out of LOCAL 4-fermi span by construction once the
     sampling leaves the forward manifold (its local decomposition coefficients
     are momentum-dependent).  That content is handled by the production
     CONTRACTED operators (O_Tq/O_Tchi), not by this local dictionary; its raw
     residual still ships in the sidecar, and weight-bearing derivative content
     still trips the full completeness bar at the driver.  The fatal
     per-monomial bar targets rank-0 content that claims to be local but is not
     (the Majorana-crossed class probe8 caught). *)
  derivMonoQ = Table[Module[{ex = Keys[crules][[t]], ss},
      ss = Flatten[Table[ConstantArray[fsyms[[i]], ex[[i]]], {i, Length[fsyms]}]];
      AnyTrue[ss, (cc[#]["rank"] >= 1) &]],
    {t, Length[crules]}];
  monoWorst = First[Ordering[
    MapThread[If[#2, 0., #1] &, {monoContribs, derivMonoQ}], -1]];
  If[! derivMonoQ[[monoWorst]] && monoContribs[[monoWorst]] >= $monomialContribTol,
    Return[<|"ok" -> False, "reason" -> "SD-PROJECTION-MONOMIAL-OUT-OF-SPAN",
      "detail" -> "F-monomial " <> monoNames[[monoWorst]] <>
        " contributes relative completeness residual " <>
        ToString[monoContribs[[monoWorst]], InputForm] <>
        " >= " <> ToString[$monomialContribTol, InputForm] <> " (raw in-span residual " <>
        ToString[monoResids[[monoWorst]], InputForm] <> ")",
      "monomial_residuals" -> AssociationThread[monoNames -> monoResids],
      "monomial_contributions" -> AssociationThread[monoNames -> monoContribs],
      "full_basis_completeness_rel_residual" -> fullRelResid,
      "rotation_exactness_max" -> rotErrMax|>]];

  (* per-column absorbed-norm share (names the absorbing structures;
     sidecar diagnostics only, Ruling 2) *)
  diagShares = AssociationThread[$refNames ->
    Table[Abs[fullSol[[j]]] colNorms[[j]]/(refMnorm + 1*^-300),
      {j, Length[$refNames]}]];

  (* SI-extraction stability (Ruling 3 criterion 2): the SI scalar operator is
     dictionary column R_S_S = (chibar chi)(qbar q), the same operator the 3-op
     C_scalar column measures *)
  siShift = If[Abs[coeffs["C_scalar"]] < 1*^-300, Abs[fullCoeffs[$refScalarName]],
    Abs[(fullCoeffs[$refScalarName] - coeffs["C_scalar"])/coeffs["C_scalar"]]];

  (* ---- PRODUCTION legs (section 3c; AMENDMENT3 Ruling 1) --------------------- *)

  (* instrument 1: the retired 3-op basis fit on the ROTATED amplitude, forward
     sample set.  referenceConfigs PREPENDS sampleConfigs, so the first
     Length[cfgs] rotated values correspond exactly to the production-leg
     configs and `mat` (the 3-op matrix) is reusable verbatim. *)
  c3rotSol = Quiet[LeastSquares[mat, MrotVals[[1 ;; Length[cfgs]]]]];
  c3rotCoeffs = AssociationThread[opNames -> c3rotSol];

  (* production contracted-operator fit (C_twist2 g1/g2 split) on the ROTATED
     amplitude over the full transfer-diversified sample set.  Its OWN basis
     health goes through the same fatal guards as the dictionary (4 columns:
     rank, collinearity, cond < 1e4, identifiability). *)
  prodNames = Keys[$opRefs2];
  prodMat = N[Table[Table[$opRefs2[op][cfg["kin"], cfg["spin"], N[mchi], N[mq]],
    {op, prodNames}], {cfg, refCfgs}]];
  prodGuards = referenceBasisGuards[prodMat, ("CONTRACTED_" <> # &) /@ prodNames];
  If[! TrueQ[prodGuards["ok"]],
    Return[Join[prodGuards, <|"detail" -> ToString[Lookup[prodGuards, "detail", ""]] <>
      " (contracted production twist-2 basis)", "classification" -> cc|>]]];
  prodColNorms = Norm /@ Transpose[prodMat];
  prodSol = Quiet[LeastSquares[
    Transpose[Transpose[prodMat]/prodColNorms], MrotVals]]/prodColNorms;
  prodCoeffs = AssociationThread[prodNames -> prodSol];

  (* instrument 3: forward-manifold retained dictionary *)
  fwd = forwardScalarInstrument[chainDefs, fsyms, crules, crossedQ,
    N[mchi], N[mq], vscale];
  If[! TrueQ[fwd["ok"]], Return[Join[fwd, <|"classification" -> cc|>]]];

  (* SHIPPING GUARD: three-instrument C_scalar agreement,
     max pairwise |a-b| <= max(1% * max|value|, 6e-10 absolute) *)
  crossVals = <|
    "threeop_rotated" -> c3rotCoeffs["C_scalar"],
    "transfer_R_S_S"  -> fullCoeffs[$refScalarName],
    "forward_R_S_S"   -> fwd["C_scalar_fwd"]|>;
  crossAbs = Abs /@ Values[crossVals];
  crossDiff = Max[Flatten[Table[Abs[Values[crossVals][[i]] - Values[crossVals][[j]]],
    {i, 3}, {j, i + 1, 3}]]];
  crossTol = Max[$crossInstrTolRel Max[crossAbs], $crossInstrTolAbs];
  If[crossDiff > crossTol,
    Return[<|"ok" -> False, "reason" -> "SD-SI-CROSS-INSTRUMENT-DISAGREE",
      "detail" -> "C_scalar instruments disagree: 3-op-on-rotated=" <>
        ToString[crossVals["threeop_rotated"], InputForm] <> ", transfer R_S_S=" <>
        ToString[crossVals["transfer_R_S_S"], InputForm] <> ", forward R_S_S=" <>
        ToString[crossVals["forward_R_S_S"], InputForm] <>
        "; max pairwise diff " <> ToString[crossDiff, InputForm] <> " > tol " <>
        ToString[crossTol, InputForm] <> " = max(1% rel, 6e-10 abs) " <>
        "(AMENDMENT3 Ruling 1 shipping guard)",
      "cross_instrument" -> Join[crossVals,
        <|"max_pairwise_diff" -> crossDiff, "tolerance" -> crossTol|>],
      (* carried for diagnosis/tests: the legacy 3-op values and the per-leg
         instrument states at the refusal point *)
      "C_scalar" -> coeffs["C_scalar"], "C_twist2" -> coeffs["C_twist2"],
      "threeop_rotated_coeffs" -> c3rotCoeffs,
      "forward_instrument" -> fwd,
      "classification" -> cc|>]];

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
    (* AMENDED guard (Ruling 3 criterion 1, rotated-complete re-derivation) *)
    "full_basis_completeness_rel_residual" -> fullRelResid,
    "completeness_ok" -> (fullRelResid < $fullCompletenessTol),
    "si3_completeness_ok" -> (relResid < $completenessTol),
    "C_scalar_full" -> fullCoeffs[$refScalarName],
    (* PRODUCTION coefficients (AMENDMENT3 Ruling 1): C_scalar ships from the
       transfer dictionary R_S_S; the twist-2 split ships from the contracted
       fit on the rotated amplitude (Hisano C^(i) = g^(i)/m_chi, section 3c) *)
    "C_scalar_production" -> fullCoeffs[$refScalarName],
    (* c_sum = C^(1)+C^(2) is the f_N input; the split is a conditioned
       DIAGNOSTIC (see the section-3c conditioning note) *)
    "C_twist2_sum" -> prodCoeffs["C_twist2_sum"],
    "C_twist2_dif" -> prodCoeffs["C_twist2_dif"],
    "C_twist2_g1" -> (prodCoeffs["C_twist2_sum"] + prodCoeffs["C_twist2_dif"])/2,
    "C_twist2_g2" -> (prodCoeffs["C_twist2_sum"] - prodCoeffs["C_twist2_dif"])/2,
    "C_scalar_contracted_rotated" -> prodCoeffs["C_scalar"],
    "C_chi_vector_rotated" -> prodCoeffs["C_chi_vector"],
    "production_basis_cond" -> prodGuards["cond"],
    "production_basis_ident_err" -> prodGuards["ident_err"],
    "threeop_rotated_coeffs" -> c3rotCoeffs,
    "forward_instrument" -> fwd,
    "cross_instrument" -> Join[crossVals,
      <|"max_pairwise_diff" -> crossDiff, "tolerance" -> crossTol, "ok" -> True|>],
    "si_shift_rel" -> siShift,
    "rotation_exactness_max" -> rotErrMax,
    "basis_rank" -> basisGuards["rank"],
    "basis_n_columns" -> basisGuards["n_columns"],
    "basis_cond" -> basisGuards["cond"],
    "identifiability_max_err" -> basisGuards["ident_err"],
    "monomial_residuals" -> AssociationThread[monoNames -> monoResids],
    "monomial_contributions" -> AssociationThread[monoNames -> monoContribs],
    "monomial_worst" -> <|"name" -> monoNames[[monoWorst]],
      "rel_residual" -> monoResids[[monoWorst]],
      "contribution" -> monoContribs[[monoWorst]],
      (* worst among the guard-relevant (non-derivative) monomials; derivative
         monomials are bar-exempt but fully reported in monomial_contributions *)
      "guard_scope" -> "non-derivative"|>,
    "instrument" -> "rotated-complete/v2: 256-column line-product dictionary, " <>
      "transfer sampling |q|=sqrt(TEPS), Majorana-crossed monomials " <>
      "C-conjugate-rotated (DESIGN-ITEM4-AMENDMENT2R1.md)",
    "full_basis_coeffs" -> fullCoeffs,
    "absorbed_norm_shares" -> diagShares,
    "worst_config_residual" -> If[worstIdx > 0, Abs[residVec[[worstIdx]]], 0.],
    "n_configs" -> Length[cfgs],
    "n_configs_instrument" -> Length[refCfgs],
    "vscale" -> vscale,
    "unrecognized_chains" -> (ToString /@ badChains),
    "classification" -> cc,
    "present" -> projClass
  |>];


(* THE loud instrument guard (shared by run_eval_sd.wls and the runtime-driven
   exit-3 tests, like ddAssertNoSurvivors): any instrument-level failure reason
   (SD-FIERZ-ROTATION-INEXACT, SD-PROJECTION-BASIS-RANK-DEFICIENT,
   SD-PROJECTION-BASIS-ILLCONDITIONED, SD-PROJECTION-BASIS-UNIDENTIFIABLE,
   SD-PROJECTION-MONOMIAL-OUT-OF-SPAN, SD-SI-CROSS-INSTRUMENT-DISAGREE) is
   emitted verbatim as a single-line
   marker + detail, then Exit[3] — nothing ships on a defective instrument. *)
projInstrumentAssert[proj_Association] :=
  If[! TrueQ[proj["ok"]] && StringQ[Lookup[proj, "reason", Null]] &&
      StringStartsQ[proj["reason"], "SD-"],
    WriteString["stderr", "run_eval_sd: " <> proj["reason"] <> " " <>
      ToString[Lookup[proj, "detail", ""]] <> "\n"];
    Exit[3]];


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
