#!/usr/bin/env wolframscript
(* run_projection_sd.wls — standalone runner for the SD chain-coefficient
   projector (sd_projection.wl), used by the R2 cross-talk fixture test
   (STEP3-DESIGN.md Decision 6 R2).

   NO LoopTools / FormCalc PV — it consumes a PRE-REDUCED fixture amp
   (wrapped association {"amp"->Amp[..][..], "subexpr"->{Sub->..}}) whose PV heads
   have already been replaced by plain numbers, so it needs only a Wolfram
   kernel.  This is what lets R2 run without the HEPPH_RUN_WOLFRAM_TESTS gate.

   Usage:
     wolframscript -script run_projection_sd.wls <fixture_amp.m> <out.json> [mchi] [mq]

   Emits {"C_scalar":..,"C_twist2":..,"C_twist2_1":..,"C_twist2_2":..,
          "residual_symbols":[..]} to <out.json>. *)

Off[General::shdw]; Off[General::stop];

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

(* Accept both the wrapped-association fixture format and a bare Amp[..][..]. *)
subexpr = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "subexpr"], "subexpr" /. amp, {}];
ampBody = If[MatchQ[amp, _List] && MemberQ[amp[[All, 1]], "amp"], "amp" /. amp, amp];
terms   = List @@ ampBody;

(* Static-DD numeric substitution — F1..F16 kept SYMBOLIC (that is the whole
   point of the coefficient-level projection).  Fixtures carry plain-number PV
   heads already, so no LoopTools call here. *)
numRules = {
  Mat[_] -> 1,
  MassFChi[i_] :> $mchi, MassFd[_] :> $mq, MassFu[_] :> $mq,
  T -> -1.0*^-4, S -> ($mchi + $mq)^2, U -> ($mchi - $mq)^2,
  Pi -> N[Pi]};

M = Total[Table[
  Module[{iters, s},
    iters = Cases[terms[[k]], SumOver[i_, n_, ___] :> {i, 1, n}];
    s = terms[[k]] /. SumOver[_, _, ___] -> 1;
    s = s //. subexpr;
    s = s /. IndexSum -> Function[{e, r}, Sum[e, Evaluate[r]]];
    s = s /. numRules;
    If[iters === {}, s, Sum[s, Evaluate[Sequence @@ iters]]]],
  {k, Length[terms]}]];

resid = residualSymbols[M];
proj  = projectOperators[M, $mchi, $mq];

(* If abbreviations are unresolved the coefficients are non-numeric; emit Null
   so the JSON is still exportable and the caller keys off residual_symbols. *)
numOrNull[x_] := If[NumberQ[N[x]], N[x], Null];
result = <|
  "C_scalar"   -> numOrNull[proj["C_scalar"]],
  "C_twist2"   -> numOrNull[proj["C_twist2"]],
  "C_twist2_1" -> numOrNull[proj["C_twist2_1"]],
  "C_twist2_2" -> numOrNull[proj["C_twist2_2"]],
  "residual_symbols" -> (ToString /@ resid)
|>;

Export[$out, result, "RawJSON"];
Print["run_projection_sd: wrote ", $out, " (C_scalar=", N[proj["C_scalar"]],
      ", C_twist2=", N[proj["C_twist2"]], ", residual=", Length[resid], ")"];
Exit[0]
