#!/usr/bin/env wolframscript
(* run_projection_sd.wls — standalone runner for the SD chain-coefficient
   projector (sd_projection.wl), used by the R2 cross-talk fixture test
   (STEP3-DESIGN.md Decision 6 R2).

   NO LoopTools / FormCalc PV — it consumes a PRE-REDUCED fixture amp
   (wrapped association {"abbr"->{F->WeylChain..}, "subexpr"->{Sub->..},
   "amp"->Amp[..][..]}) whose PV heads have already been replaced by plain
   numbers, so it needs only a Wolfram kernel.  The projector then evaluates every
   chain on an explicit spinor basis and solves for the operator coefficients
   (Decision 3.2 numerical basis-vector solve) — this is what lets R2 run without
   the HEPPH_RUN_WOLFRAM_TESTS / MathLink gate.

   CRUCIAL (why the fixture MUST carry an "abbr" table): the new projector reads
   each chain's operator content from its ACTUAL WeylChain definition (the F1
   review fix — no hard-coded {F1..F4}=scalar index block).  A fixture without
   real chain definitions cannot be projected.

   Usage:
     wolframscript -script run_projection_sd.wls <fixture_amp.m> <out.json> [mchi] [mq]

   Emits {"C_scalar":..,"C_twist2":..,"C_chi_vector":..,
          "completeness_rel_residual":..,"completeness_ok":..,
          "unrecognized_chains":[..],"residual_symbols":[..],"ok":..} to <out.json>. *)

Off[General::shdw]; Off[General::stop]; Off[General::infy]; Off[Power::infy];

If[Length[$ScriptCommandLine] < 3,
  WriteString["stderr", "run_projection_sd: usage: <fixture> <out> [mchi] [mq]\n"];
  Exit[1]];
$fixture = $ScriptCommandLine[[2]];
$out     = $ScriptCommandLine[[3]];
$mchi    = If[Length[$ScriptCommandLine] >= 4, ToExpression[$ScriptCommandLine[[4]]], 132.69];
$mq      = If[Length[$ScriptCommandLine] >= 5, ToExpression[$ScriptCommandLine[[5]]], 4.67*^-3];

$scriptDir = DirectoryName[
  If[$InputFileName =!= "" && $InputFileName =!= Null, $InputFileName,
     $ScriptCommandLine[[1]]]];
Get[FileNameJoin[{$scriptDir, "sd_projection.wl"}]];

amp = Quiet[Check[Get[$fixture], $Failed]];
If[amp === $Failed,
  WriteString["stderr", "run_projection_sd: could not read fixture " <> $fixture <> "\n"];
  Exit[1]];

(* Accept the wrapped-association fixture format (abbr/subexpr/amp keys) or a bare
   Amp[..][..] (no abbr -> cannot project the new way). *)
getKey[assoc_, key_, default_] :=
  If[MatchQ[assoc, _List] && MemberQ[assoc[[All, 1]], key], key /. assoc, default];
abbr    = getKey[amp, "abbr", {}];
subexpr = getKey[amp, "subexpr", {}];
ampBody = getKey[amp, "amp", amp];
(* HoldPattern: Cases treats a bare `lhs -> rhs` 2nd arg as a pattern->transform
   rule, so `(_ -> _WeylChain)` would misparse.  Wrap it to match the RULES. *)
abbrF   = Cases[abbr, HoldPattern[_ -> _WeylChain]];

If[abbrF === {},
  WriteString["stderr",
    "run_projection_sd: fixture carries no Abbr[] WeylChain table; the numerical\n" <>
    "  basis-vector projector (Decision 3.2) needs real chain definitions.\n"];
  Exit[1]];

(* ampBody is Amp[process][expr]; its head is Amp[process], so List @@ replaces
   that head and yields {expr} (the process spec stays in the head, out of M). *)
terms = If[Head[Head[ampBody]] === Amp, List @@ ampBody, {ampBody}];

(* Build the F-symbolic amplitude M: expand SumOver ranges, apply the subexpr
   abbreviations and IndexSum, drop the color/matrix wrapper — F1..F18 KEPT
   SYMBOLIC (that is the whole point of the coefficient-level projection). *)
M = Total[Table[
  Module[{iters, s},
    iters = Cases[terms[[k]], SumOver[i_, n_, ___] :> {i, 1, n}];
    s = terms[[k]] /. SumOver[_, _, ___] -> 1;
    s = s //. subexpr;
    s = s /. IndexSum -> Function[{e, r}, Sum[e, Evaluate[r]]];
    s = s /. {Mat[_] -> 1};
    If[iters === {}, s, Sum[s, Evaluate[Sequence @@ iters]]]],
  {k, Length[terms]}]];

resid = residualSymbols[M];
proj  = projectOperators[M, abbrF, $mchi, $mq];

numOrNull[x_] := If[NumberQ[N[x]], N[Re[x]], Null];
result = If[TrueQ[proj["ok"]],
  <|
    "ok" -> True,
    "C_scalar"     -> numOrNull[proj["C_scalar"]],
    "C_twist2"     -> numOrNull[proj["C_twist2"]],
    "C_chi_vector" -> numOrNull[proj["C_chi_vector"]],
    "completeness_rel_residual" -> N[proj["completeness_rel_residual"]],
    "completeness_ok" -> TrueQ[proj["completeness_ok"]],
    "unrecognized_chains" -> proj["unrecognized_chains"],
    "residual_symbols" -> (ToString /@ resid)
  |>,
  <|
    "ok" -> False,
    "reason" -> proj["reason"],
    "unrecognized_chains" -> Lookup[proj, "unrecognized_chains", {}],
    "residual_symbols" -> (ToString /@ resid)
  |>];

Export[$out, result, "RawJSON"];
Print["run_projection_sd: wrote ", $out, " (ok=", result["ok"],
      If[TrueQ[result["ok"]],
        ", C_scalar=" <> ToString[result["C_scalar"]] <>
        ", C_twist2=" <> ToString[result["C_twist2"]] <>
        ", completeness_ok=" <> ToString[result["completeness_ok"]],
        ", reason=" <> ToString[result["reason"]]], ")"];
Exit[0]
