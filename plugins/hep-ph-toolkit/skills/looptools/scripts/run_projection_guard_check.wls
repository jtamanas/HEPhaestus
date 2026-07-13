#!/usr/bin/env wolframscript
(* run_projection_guard_check.wls — runtime driver for the rotated-complete
   instrument guards (DESIGN-ITEM4-AMENDMENT2.md Ruling 1 + AMENDMENT2R1):
   exercises referenceBasisGuards / projectOperators / projInstrumentAssert —
   the SAME functions run_eval_sd.wls calls — so every Exit[3] path is actually
   DRIVEN, not source-grepped (the F5 discipline).

   Needs only a bare Wolfram kernel (no LoopTools/FormCalc): the instrument is
   pure spinor numerics.

   Usage (mode -> required outcome):
     rank-deficient   -> Exit[3], SD-PROJECTION-BASIS-RANK-DEFICIENT with the
                         null-space combination NAMED (duplicate-column injection
                         — the D_Vq_Ac == D_Aq_Vc class of defect)
     null-column      -> Exit[3], SD-PROJECTION-BASIS-ILLCONDITIONED naming the
                         null column (the 7-forward-null-pseudoscalar class)
     collinear        -> Exit[3], SD-PROJECTION-BASIS-ILLCONDITIONED naming a
                         collinear pair
     illconditioned   -> Exit[3], SD-PROJECTION-BASIS-ILLCONDITIONED with
                         cond >= 1e4 (full-rank, no collinear pair)
     unidentifiable   -> Exit[3], SD-PROJECTION-BASIS-UNIDENTIFIABLE (driven
                         with the cond bar Block-raised, DOCUMENTED: in nature
                         cond >= 1e4 fires first, since recovery error scales
                         with cond; this mode proves the inequality + marker
                         path with a cond ~1e8 matrix whose recovery error
                         lands above 1e-10)
     rotation-inexact -> Exit[3], SD-FIERZ-ROTATION-INEXACT (wrong-sign
                         injection: fierzDress Block-redefined with a flipped
                         sign, so the flipped-spin production value and the
                         algebraic direct combination MUST disagree O(1) —
                         proving the guard actually compares two independent
                         evaluations)
     monomial-out-of-span -> Exit[3], SD-PROJECTION-MONOMIAL-OUT-OF-SPAN naming
                         the monomial (a single-barred-chi crossed pairing that
                         is NOT rotatable and NOT plain-Fierz-reachable, with
                         O(1) weight)
     cross-instrument -> Exit[3], SD-SI-CROSS-INSTRUMENT-DISAGREE (AMENDMENT3
                         Ruling 1 shipping guard): the forward instrument is
                         Block-redefined to return a corrupted C_scalar, so the
                         three-instrument agreement check MUST fire — proving
                         the guard actually compares three independently
                         produced values, names them, and exits 3
     pass             -> Exit[0]: a synthetic amplitude carrying a genuine
                         Majorana-crossed pair (rotated) + direct products runs
                         end-to-end green through rotation, pre-fit guards and
                         the per-monomial diagnostic at the canonical masses.
*)

Off[General::shdw]; Off[General::stop];

If[Length[$ScriptCommandLine] < 2,
  WriteString["stderr",
    "run_projection_guard_check: usage <rank-deficient|null-column|collinear|" <>
    "illconditioned|unidentifiable|rotation-inexact|monomial-out-of-span|" <>
    "cross-instrument|pass>\n"];
  Exit[1]];
$mode = $ScriptCommandLine[[2]];

$scriptDir = DirectoryName[
  If[$InputFileName =!= "" && $InputFileName =!= Null, $InputFileName, $ScriptCommandLine[[1]]]];
Get[FileNameJoin[{$scriptDir, "sd_projection.wl"}]];

(* canonical-point masses: the instrument is measured green here
   (rank 256/256, cond 6.1e3, ident 7.0e-13) *)
$mchi = 132.69; $mq = 4.67*^-3;

(* deterministic test blocks for the matrix modes; orthoMat = exact standard-
   basis columns, PERFECTLY conditioned, so an injected epsilon-direction sets
   the spectrum exactly (a smooth pseudo-random seed is itself too degenerate
   to control the small singular values) *)
seedMat[n_, m_] := Table[N[Sin[i^2 + 3 j + i j]], {i, n}, {j, m}];
orthoMat[n_, m_] := N[IdentityMatrix[n][[All, 1 ;; m]]];

(* synthetic chain set: a genuine Majorana-crossed pair (both chi-barred,
   F5*F6 leg layout) + direct chi-line/quark-line chains *)
$wcA = WeylChain[Spinor[k[1], MassFChi[1]], 6, k[2], Spinor[k[2], MassFd[1]]];
$wcB = WeylChain[Spinor[k[3], MassFChi[1]], 7, Spinor[k[4], MassFd[1]]];
$wcChi = WeylChain[Spinor[k[3], MassFChi[1]], 6, Spinor[k[1], MassFChi[1]]];
$wcQ = WeylChain[Spinor[k[4], MassFd[1]], 7, Spinor[k[2], MassFd[1]]];
(* single-barred-chi crossed pairing (chi=k3 unbarred end; barred quark k4):
   (chibar(k1) A q(k2)) (qbar(k4) B chi(k3)) — not rotatable (only one chain is
   chi-barred), not plain-Fierz-reachable to the ubar(k3)..u(k1) dictionary *)
$wcQmix = WeylChain[Spinor[k[4], MassFd[1]], 7, Spinor[k[3], MassFChi[1]]];
$abbrCrossed = {FA -> $wcA, FB -> $wcB, FC -> $wcChi, FQ -> $wcQ};
(* rank-0 variant of the crossed chain for the out-of-span mode: a rank-1
   (insertion) chain would be derivative-EXEMPT from the fatal bar *)
$wcA0 = WeylChain[Spinor[k[1], MassFChi[1]], 6, Spinor[k[2], MassFd[1]]];
$abbrOutOfSpan = {FA -> $wcA0, FX -> $wcQmix, FC -> $wcChi, FQ -> $wcQ};

Which[
  $mode === "rank-deficient",
  Module[{mat = seedMat[12, 5], res},
    (* col6 = col1 + col2 EXACTLY: rank 5 of 6, but no pairwise-collinear pair
       (so the rank guard itself, not the collinear pre-check, must fire and
       NAME the combination — the D_Vq_Ac == D_Aq_Vc defect class) *)
    mat = Transpose[Append[Transpose[mat], mat[[All, 1]] + mat[[All, 2]]]];
    res = referenceBasisGuards[mat, {"c1", "c2", "c3", "c4", "c5", "c6combo"}];
    projInstrumentAssert[res];   (* must Exit[3] *)
    WriteString["stderr", "run_projection_guard_check: GUARD DID NOT FIRE (rank-deficient), got " <>
      ToString[res, InputForm] <> "\n"];
    Exit[9]],

  $mode === "null-column",
  Module[{mat = seedMat[12, 5], res},
    mat = Transpose[Append[Transpose[mat], ConstantArray[0., 12]]];
    res = referenceBasisGuards[mat, {"c1", "c2", "c3", "c4", "c5", "cNULL"}];
    projInstrumentAssert[res];
    WriteString["stderr", "run_projection_guard_check: GUARD DID NOT FIRE (null-column)\n"];
    Exit[9]],

  $mode === "collinear",
  Module[{mat = seedMat[12, 5], res},
    mat = Transpose[Append[Transpose[mat], 3.7 mat[[All, 4]]]];
    res = referenceBasisGuards[mat, {"c1", "c2", "c3", "c4", "c5", "c6scaled4"}];
    projInstrumentAssert[res];
    WriteString["stderr", "run_projection_guard_check: GUARD DID NOT FIRE (collinear)\n"];
    Exit[9]],

  $mode === "illconditioned",
  Module[{mat = orthoMat[12, 4], res},
    (* col5 = col1 + col2 + 1e-6 * e5, where e5 is a fresh direction NOT among
       the columns (else col5 would lie exactly in their span -> rank guard,
       not cond, would fire): pairwise cosines stay far from 1, the joint
       spectrum gains an exactly ~7e-7 direction -> full rank (over the 1e-10
       rank tol), cond >> 1e4 *)
    mat = Transpose[Append[Transpose[mat],
      mat[[All, 1]] + mat[[All, 2]] + 1.0*^-6 N[IdentityMatrix[12][[All, 5]]]]];
    res = referenceBasisGuards[mat, {"c1", "c2", "c3", "c4", "c5near"}];
    projInstrumentAssert[res];
    WriteString["stderr", "run_projection_guard_check: GUARD DID NOT FIRE (illconditioned), got " <>
      ToString[res, InputForm] <> "\n"];
    Exit[9]],

  $mode === "unidentifiable",
  Module[{mat = orthoMat[12, 4], res},
    mat = Transpose[Append[Transpose[mat],
      mat[[All, 1]] + mat[[All, 2]] + 1.0*^-8 N[IdentityMatrix[12][[All, 5]]]]];
    (* DOCUMENTED DRIVE: for any full-rank matrix pinv.nmat == I holds to
       ~machine precision via a clean SVD (measured 3.1e-16 even at cond 2.8e8),
       so in nature the cond bar fires FIRST and a natural identifiability
       failure is unreachable below cond ~1e12+.  This mode therefore
       Block-raises the cond bar AND Block-lowers the identifiability bar below
       machine precision to drive the detection inequality, the column naming,
       and the marker + Exit[3] path end-to-end.  The guard's value in
       production is as the LAST line of defence should the pseudoinverse ever
       silently truncate (rank-adjacent regime). *)
    Block[{$refCondTol = 1.0*^12, $refIdentTol = 1.0*^-17},
      res = referenceBasisGuards[mat, {"c1", "c2", "c3", "c4", "c5near"}]];
    projInstrumentAssert[res];
    WriteString["stderr", "run_projection_guard_check: GUARD DID NOT FIRE (unidentifiable), got " <>
      ToString[res, InputForm] <> "\n"];
    Exit[9]],

  $mode === "rotation-inexact",
  Module[{res},
    Block[{fierzDress},
      fierzDress[Mx_] := +$KK . $CC . Transpose[Mx] . Transpose[$KK] . $CCinv . $g5;
      (* sign-flipped dressing: the algebraic direct combination now DISAGREES
         with the flipped-spin production value O(1) on every config *)
      res = projectOperators[2.0 FA FB + 0.3 FC FQ, $abbrCrossed, $mchi, $mq]];
    projInstrumentAssert[res];
    WriteString["stderr", "run_projection_guard_check: GUARD DID NOT FIRE (rotation-inexact), got ok=" <>
      ToString[res["ok"]] <> " reason=" <> ToString[Lookup[res, "reason", ""]] <> "\n"];
    Exit[9]],

  $mode === "monomial-out-of-span",
  Module[{res},
    res = projectOperators[1.0 FA FX + 0.3 FC FQ, $abbrOutOfSpan, $mchi, $mq];
    projInstrumentAssert[res];
    WriteString["stderr", "run_projection_guard_check: GUARD DID NOT FIRE (monomial-out-of-span), got ok=" <>
      ToString[res["ok"]] <> " reason=" <> ToString[Lookup[res, "reason", ""]] <> "\n"];
    Exit[9]],

  $mode === "cross-instrument",
  Module[{res},
    Block[{forwardScalarInstrument},
      (* corrupted third instrument: a fixed wrong C_scalar, far outside
         max(1% rel, 6e-10 abs) of the other two legs *)
      forwardScalarInstrument[___] := <|"ok" -> True, "C_scalar_fwd" -> 1.0*^6,
        "n_configs" -> 0, "n_null_columns" -> 0, "n_retained" -> 0,
        "n_nonnull" -> 0, "retained_cond" -> 1.0, "retained_ident_err" -> 0.,
        "completeness_rel_residual" -> 0.|>;
      res = projectOperators[2.0 FA FB + 0.3 FC FQ, $abbrCrossed, $mchi, $mq]];
    projInstrumentAssert[res];
    WriteString["stderr", "run_projection_guard_check: GUARD DID NOT FIRE (cross-instrument), got ok=" <>
      ToString[res["ok"]] <> " reason=" <> ToString[Lookup[res, "reason", ""]] <> "\n"];
    Exit[9]],

  $mode === "pass",
  Module[{res},
    res = projectOperators[2.0 FA FB + 0.3 FC FQ, $abbrCrossed, $mchi, $mq];
    projInstrumentAssert[res];
    If[! TrueQ[res["ok"]],
      WriteString["stderr", "run_projection_guard_check: pass mode NOT ok: " <>
        ToString[Lookup[res, "reason", ""]] <> " " <>
        ToString[Lookup[res, "detail", ""]] <> "\n"];
      Exit[9]];
    Print["run_projection_guard_check: pass — rank ", res["basis_rank"], "/",
      res["basis_n_columns"], " cond ", ToString[res["basis_cond"], InputForm],
      " ident ", ToString[res["identifiability_max_err"], InputForm],
      " rotation ", ToString[res["rotation_exactness_max"], InputForm],
      " completeness ", ToString[res["full_basis_completeness_rel_residual"], InputForm],
      " monomial-worst-contribution ",
      ToString[res["monomial_worst"]["contribution"], InputForm]];
    Exit[0]],

  True,
  WriteString["stderr", "run_projection_guard_check: unknown mode " <> $mode <> "\n"];
  Exit[1]]
