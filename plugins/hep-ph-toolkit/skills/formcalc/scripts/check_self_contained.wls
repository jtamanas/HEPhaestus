#!/usr/bin/env wolframscript
(* check_self_contained.wls — verify an amp_reduced.m is self-contained.

   Usage:
     wolframscript -script check_self_contained.wls <amp_reduced.m> [<formcalc_path>]

   Loads FormCalc (so F##/Sub###/WeylChain/PV heads intern into their package
   contexts, exactly as a real eval driver sees them) in a FRESH kernel that has
   run NO reduction, Get[]s the artifact, and resolves the reduced amplitude
   against its own persisted abbreviation tables:

       resolved = amp //. Join[subexpr, abbr]

   then counts any Sub### / F## heads still dangling after resolution. A
   self-contained artifact leaves ZERO. Prints one machine-parseable line

     SELF_CONTAINED_RESULT sub_refs=<n> sub_unresolved=<n> f_refs=<n> f_unresolved=<n> ok=<True|False>

   and exits 0 when fully resolved, 2 otherwise (1 on structural/load error). *)

Module[{args, ampPath, fcPath, data, amp, abbr, sub, resolved,
        subRefs, subUnres, fRefs, fUnres, ok},

  args = $ScriptCommandLine;
  If[Length[args] < 2,
    Print["check_self_contained: usage: <amp_reduced.m> [formcalc_path]"]; Exit[1]];
  ampPath = args[[2]];
  fcPath  = If[Length[args] >= 3, args[[3]], ""];

  If[fcPath =!= "", AppendTo[$Path, fcPath]];
  If[Quiet[Needs["FormCalc`"], {General::shdw}] === $Failed,
    Print["check_self_contained: Needs[FormCalc`] failed"]; Exit[1]];

  data = Quiet[Check[Get[ampPath], $Failed]];
  If[data === $Failed,
    Print["check_self_contained: Get[amp_reduced.m] failed"]; Exit[1]];

  (* Reject the old bare-Amp[...] format loudly: it carries no wrapped keys. *)
  If[FreeQ[data, "amp"] || FreeQ[data, "subexpr"],
    Print["check_self_contained: amp_reduced.m is not a wrapped association ",
          "(missing amp/subexpr keys) — not self-contained (old writer format)"];
    Print["SELF_CONTAINED_RESULT sub_refs=-1 sub_unresolved=-1 f_refs=-1 ",
          "f_unresolved=-1 ok=False"];
    Exit[2]];

  amp  = "amp" /. data;
  abbr = "abbr" /. data;    (* may be the literal "abbr" if key absent -> {} below *)
  sub  = "subexpr" /. data;
  If[!ListQ[abbr], abbr = {}];
  If[!ListQ[sub], sub = {}];

  (* Symbol-name predicates: a Sub### / F## head is any symbol whose name is
     "Sub"/"F" followed only by digits (excludes e.g. Fchi, SUN1). Indexed subs
     like Sub7[i] have Head Sub7 — Cases at all levels with Heads->True catches
     both the atomic and the applied forms. *)
  subQ = Function[s, Head[s] === Symbol &&
     StringMatchQ[SymbolName[s], "Sub" ~~ DigitCharacter ..]];
  fQ = Function[s, Head[s] === Symbol &&
     StringMatchQ[SymbolName[s], "F" ~~ DigitCharacter ..]];

  subRefs = Length[DeleteDuplicates[Cases[amp, s_?subQ, Infinity, Heads -> True]]];
  fRefs   = Length[DeleteDuplicates[Cases[amp, s_?fQ, Infinity, Heads -> True]]];

  resolved = amp //. Join[sub, abbr];

  subUnres = DeleteDuplicates[Cases[resolved, s_?subQ, Infinity, Heads -> True]];
  fUnres   = DeleteDuplicates[Cases[resolved, s_?fQ, Infinity, Heads -> True]];

  ok = (Length[subUnres] == 0) && (Length[fUnres] == 0);

  If[Length[subUnres] > 0,
    Print["check_self_contained: UNRESOLVED Sub###: ",
      ToString[Take[subUnres, UpTo[20]], InputForm]]];
  If[Length[fUnres] > 0,
    Print["check_self_contained: UNRESOLVED F##: ",
      ToString[Take[fUnres, UpTo[20]], InputForm]]];

  Print["SELF_CONTAINED_RESULT sub_refs=", subRefs,
        " sub_unresolved=", Length[subUnres],
        " f_refs=", fRefs,
        " f_unresolved=", Length[fUnres],
        " ok=", ok];
  Exit[If[ok, 0, 2]]
]
