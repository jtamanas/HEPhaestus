(* sd_projection.wl — Majorana-chi + external-quark projection onto the SD
   operator basis at the Weyl-chain-COEFFICIENT level (STEP3-DESIGN.md Decision 3).

   This is the physics the 2HDM+a driver's static spin-summed collapse
   (run_eval.wls:30-44) CANNOT do: at a single static point the scalar
   (chi-bar chi)(q-bar q) and the twist-2 q-bar(gamma.d)q operators are
   degenerate as c-numbers (both proportional to m_chi m_q), so substituting
   rest-frame numbers for every Weyl chain F1..F16 and spin-summing folds
   twist-2 into the scalar coefficient.  Fatal for the SD floor because the boxes
   (the twist-2 source) ARE the floor.

   Instead we keep the FormCalc form factors SYMBOLIC in the chains: FormCalc
   organises the reduced amplitude as  M = Sum_i b_i(S,T,U;PV) F_i , where each
   F_i (Abbr[]) is a complete external Dirac structure and the b_i are the
   numeric-after-substitution form factors.  Projection = linear extraction of
   the b_i, grouped by which operator each chain block realises:

     scalar block   {F1,F2,F3,F4}  ubar_chi u_chi * ubar_q u_q  (no kslash)
     twist-2 block  {F5,F6,F7,F8}  kslash-inserted bilinear (quark momentum)
     mixed  block   {F9..F16}      chi-q spin-delta chains (spin-dependent; SD)

   The scalar and twist-2 blocks are DISJOINT index sets, so a pure-scalar
   amplitude projects to zero twist-2 and vice versa — this is exactly the
   cross-talk the R2 fixture (Decision 6 R2) is built to catch.

   NO LoopTools / FormCalc PV heads are touched here — pure algebra.  So the R2
   cross-talk fixture test needs only a Wolfram kernel (Tier-2-ish), not the
   LoopTools MathLink / HEPPH_RUN_WOLFRAM_TESTS gate.

   Majorana chi (Decision 3.4): FeynArts/FormCalc already carry the Majorana
   fermion flow (the crossed box IRR-4 is in the amplitude); the projector must
   NOT add symmetry factors by hand.  The only Majorana-specific choice is the
   chi-bar chi normalisation convention, applied via `majoranaNorm` below and
   verified by the R2 fixture.
*)

$scalarChains = {F1, F2, F3, F4};
$twist2Chains = {F5, F6, F7, F8};
$mixedChains  = {F9, F10, F11, F12, F13, F14, F15, F16};
$allChains    = Join[$scalarChains, $twist2Chains, $mixedChains];

(* Self-conjugate (Majorana) chi normalisation.  Dirac (chi-bar chi) and
   Majorana (self-conjugate) differ by the standard factor-2 convention in the
   bilinear normalisation; the amplitude itself already encodes the Majorana
   fermion flow, so this is a single overall scalar, NOT a per-diagram symmetry
   factor. *)
majoranaNorm = 1;

(* Linear form-factor extraction: b_i = coefficient of chain F_i in M.
   Expand first so distributed products expose the single F_i factor per term
   (FormCalc amplitudes are LINEAR in the external chains). *)
chainCoeff[M_, f_] := Coefficient[Expand[M], f];

(* Guard: after Expand, M must be F-LINEAR and carry no residual chain products
   or free FormCalc/abbreviation symbols.  A residual Sub#### / ZN / g2 symbol
   means the amplitude was not fully numeric-substituted (the dominant SD
   failure mode: the STEP2 amp_reduced.m was written by Put[reduced] WITHOUT its
   FormCalc Subexpr[] table, so the Sub#### abbreviations — which hide the
   F-chains and couplings — are undefined).  Return the offending symbols so the
   driver can fail LOUDLY at a named guard instead of emitting a nonsense
   coefficient. *)
residualSymbols[M_] := Module[{syms},
  (* Scan the expression tree directly (NO Expand): the forbidden symbols appear
     as atoms regardless of expansion, and Expand[] on the fully-summed real SD
     amplitude is prohibitively expensive.  Detection only. *)
  syms = Cases[M, s_Symbol /; (
      StringMatchQ[SymbolName[s], "Sub" ~~ DigitCharacter ..] ||
      MemberQ[{"ZN", "UM", "UP", "ZDL", "ZDR", "ZUL", "ZUR", "Yu", "Yd",
               "yh1", "yh2", "g1", "g2", "Lam", "vvSM", "PhaseFS",
               "MassFChi", "MassFd", "MassFu", "Masshh", "MassAh", "MassHp",
               "MassVWp", "MassVZ", "MassFChiM"}, SymbolName[s]]),
    Infinity];
  DeleteDuplicates[syms]];

(* Project the (numeric-substituted, F-symbolic) amplitude M onto the operator
   basis.  Returns an Association of raw block-summed form factors.  The scalar
   and twist-2 blocks share no chain, so cross-talk is structurally zero — the
   R2 test verifies exactly this against the 2HDM+a-collapse failure mode. *)
projectOperators[M_, mchi_, mq_] := Module[{bF, cScalar, cTw, cTw1, cTw2},
  bF = Association[Table[F[i] -> chainCoeff[M, Symbol["F" <> ToString[i]]], {i, 16}]];
  (* scalar (chi-bar chi)(q-bar q): sum the scalar-block form factors *)
  cScalar = majoranaNorm * Total[chainCoeff[M, #] & /@ $scalarChains];
  (* twist-2 (kslash-inserted quark bilinear): the two independent momentum
     structures.  Convention (provisional, documented): C^(1) <- {F5,F7},
     C^(2) <- {F6,F8}; the block total is the load-bearing separation from
     scalar, the C1/C2 sub-split is the twist-2 spin/moment convention. *)
  cTw  = majoranaNorm * Total[chainCoeff[M, #] & /@ $twist2Chains];
  cTw1 = majoranaNorm * (chainCoeff[M, F5] + chainCoeff[M, F7]);
  cTw2 = majoranaNorm * (chainCoeff[M, F6] + chainCoeff[M, F8]);
  <|
    "C_scalar"   -> cScalar,
    "C_twist2"   -> cTw,
    "C_twist2_1" -> cTw1,
    "C_twist2_2" -> cTw2
  |>];
