(* run_eval_common.wl — model-AGNOSTIC plumbing for the LoopTools eval drivers.

   Shared include for run_eval.wls (2HDM+a) and the future run_eval_sd.wls
   (singlet-doublet).  Factored out of run_eval.wls per STEP3-DESIGN.md Decision 4
   / build-order item 2, with ZERO behaviour change on the 2HDM+a path.

   ============================================================================
   CONTRACT — what a model driver must do (in this order)
   ============================================================================
   A model driver (run_eval.wls, run_eval_sd.wls, ...) is a wolframscript that:

     1. Defines its model-specific TOP-LEVEL constants (light-quark masses,
        gauge couplings, the t->0 regulator TEPS, etc.) — anything needed BEFORE
        the amplitude Module.  These are plain numeric assignments and must not
        reference FormCalc/LoopTools symbols.

     2. Get[]s THIS file EARLY, before referencing ANY FormCalc/LoopTools symbol
        (PV heads C0i/D0i/B0i, or the FeynArts kinematic symbols
        S/T/U/SumOver/IndexSum/Den/Mat).  Loading this file, in order:
          - suppresses the standard warning stream (Off[General::shdw], ...);
          - parses the standard positional argv (see below) into the globals
            $ampPath, $pointPath, $ffPreset, $outPath, $ltPrefix;
          - loads FormCalc, Install[]s the LoopTools MathLink binary, runs
            ltini[], and self-tests a known-finite C0i (Exit[1] on any failure);
          - defines the generic helpers below.
        Because the FormCalc/LoopTools load happens WHILE this file is being read,
        every helper defined afterwards (and every symbol in the driver's Module,
        which is read after this Get returns) interns C0i/SumOver/... into their
        PACKAGE contexts rather than as fresh Global` symbols that would shadow
        the package versions.  This is why the load lives here and not later.

   STANDARD POSITIONAL ARGV (set by run_looptools.py run_driver):
     [[2]] amp_reduced.m   [[3]] point.json   [[4]] form_factor_preset
     [[5]] eval_output.json (out)   [[6]] looptools_prefix

   GLOBALS the driver may read after Get:
     $ampPath  $pointPath  $ffPreset  $outPath  $ltPrefix

   HELPERS the driver calls:
     unboundQ[v]                    — True if v is $Failed or a Missing[...]
                                      (use to build the model's unbound list).
     emitUnboundGuard[unbound,help] — if unbound is non-empty, write the
                                      UNBOUND-MODEL-PARAMETERS marker (parsed by
                                      run_looptools._extract_unbound) plus the
                                      driver-supplied model help text to stderr
                                      and Exit[3].  Call this BEFORE any PV /
                                      MathLink use, so an un-bindable model point
                                      fails loud (guided blocker) not by crash.
     evalTermCommon[term, subexpr, Fp, nr, override:{}]
                                    — the SumOver/IndexSum evaluation engine.
                                      HoldFirst on term.  Expands SumOver ranges
                                      (minus any overridden index), applies the
                                      amp's subexpr substitutions and the IndexSum
                                      -> Sum rewrite, then the external-chain
                                      values Fp and the numeric/PV rules nr.
     writeEvalOutput[outPath, jsonAssoc]
                                    — Export the result assoc as RawJSON, then
                                      run the (harmless) LoopTools MathLink
                                      teardown.  The driver Prints + Exit[0]s
                                      itself AFTER this, so the JSON-on-disk (not
                                      the link teardown) defines success.

   The driver keeps everything model-specific: the point Import, the mass/coupling
   binding table + bindGuard, the numeric substitution rules (mkNum), the external
   Dirac/Majorana chain projection (Fsame/Fdiff), the nucleon matching, and the
   assembly of the looptools_eval_output/v1 jsonAssoc.
*)

(* ---- warning suppression (MUST precede Needs so shadow msgs are quiet) ------ *)
Off[General::stop]; Off[General::munfl]; Off[General::infy]; Off[Power::infy];
Off[General::shdw];

(* ---- standard positional argv contract ------------------------------------- *)
If[Length[$ScriptCommandLine] < 6,
  WriteString["stderr", "run_eval.wls: insufficient arguments\n"]; Exit[1]];
$ampPath   = $ScriptCommandLine[[2]];
$pointPath = $ScriptCommandLine[[3]];
$ffPreset  = $ScriptCommandLine[[4]];
$outPath   = $ScriptCommandLine[[5]];
$ltPrefix  = $ScriptCommandLine[[6]];

(* ---- FormCalc + LoopTools (MathLink) load + self-test ----------------------
   Loaded HERE (while this file is being read) so the PV heads (C0i/D0i/B0i) and
   the FeynArts kinematic symbols (S/T/U/SumOver/IndexSum/Den/Mat) resolve to
   their package contexts for every helper defined below AND for the driver's
   Module (read after this Get returns).
   --------------------------------------------------------------------------- *)
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
   (catches the FormCalc-symbolic vs LoopTools-numeric head clash / bad install).
   The regulator here is arbitrary and does not affect any driver output. *)
$c0test = Quiet[C0i[cc0, 100.^2, -1.0*^-4, 100.^2, 100.^2, 400.^2, 400.^2]];
If[!NumberQ[$c0test] || !(Abs[$c0test] < Infinity),
  WriteString["stderr", "run_eval: LoopTools C0i self-test failed (got " <>
    ToString[$c0test] <> "); PV heads not evaluating numerically.\n"]; Exit[1]];

(* ---- generic helpers (defined AFTER the load, so package symbols resolve) --- *)

(* Model-binding predicate: an amplitude symbol is unbound if its point lookup
   returned $Failed (absent SLHA block) or Missing[...] (absent PDG mass). *)
unboundQ[v_] := (v === $Failed) || MatchQ[v, _Missing];

(* Loud-failure guard (DETECTION ONLY).  A model driver builds `unbound` (the
   names of amplitude symbols its point failed to bind) and calls this before any
   PV / MathLink work.  Emits the UNBOUND-MODEL-PARAMETERS marker (grepped +
   parsed by run_looptools._diagnose_eval_failure / _extract_unbound) followed by
   the driver's model-specific help text, then Exit[3] — so the caller gets a
   guided LOOPTOOLS_EVAL_NO_OUTPUT blocker instead of a MathLink crash. *)
emitUnboundGuard[unbound_List, helpText_:""] := If[Length[unbound] > 0,
  WriteString["stderr",
    "run_eval: UNBOUND-MODEL-PARAMETERS " <> ToString[unbound, InputForm] <> "\n" <>
    helpText];
  Exit[3]];

(* SumOver/IndexSum evaluation engine.  HoldFirst on `term` (a single amplitude
   term, held so its SumOver structure survives to Cases).  `subexpr` is the amp's
   subexpr substitution list, `Fp` the external-chain values (Fsame/Fdiff), `nr`
   the numeric + PV substitution rules, `override` optional per-index pins. *)
SetAttributes[evalTermCommon, HoldFirst];
evalTermCommon[term_, subexpr_, Fp_, nr_, override_:{}] := Module[{iters, s},
  iters = Cases[term, SumOver[i_, n_] :> {i, 1, n}];
  iters = DeleteCases[iters, {x_, _, _} /; MemberQ[override[[All, 1]], x]];
  s = (term /. SumOver[_, _] -> 1) //. subexpr;
  s = s /. IndexSum -> Function[{e, r}, Sum[e, Evaluate[r]]];
  s = s /. override;
  Sum[Quiet[(s /. Fp) //. nr], Evaluate[Sequence @@ iters]]];

(* Write the result assoc, then tear the LoopTools MathLink link down.
   KNOWN ISSUE: ltexi[] can throw an uncaught MathLink::MLException at
   process exit-cleanup.  It fires AFTER the JSON is already written here, so it
   is HARMLESS to the result, but a caller that inspects raw process exit
   semantics could be misled.  The driver Exit[0]s explicitly AFTER this call so
   the JSON-on-disk, not the link teardown, defines success. *)
writeEvalOutput[outPath_, jsonAssoc_] := (
  Export[outPath, jsonAssoc, "RawJSON"];
  Quiet[Check[ltexi[], Null]];
);
