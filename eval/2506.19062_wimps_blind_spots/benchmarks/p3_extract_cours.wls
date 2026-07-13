#!/usr/bin/env wolframscript
(* p3_extract_cours.wls — VALIDATION-ONLY (P3 / Ruling 4).

   Extracts OUR pipeline's operator Wilson coefficients from a driver-produced
   amp_dd.m sidecar by calling the PRODUCTION projector (sd_projection.wl)
   directly.  This is used because the production driver run_eval_sd.wls may
   Exit[3] at a downstream guard (e.g. SD-SI-EXTRACTION-UNSTABLE) BEFORE writing
   eval_output.json — but it writes amp_dd.m first (run_eval_sd.wls: writeAmpDdSidecar
   precedes the projection guards).  We therefore read amp_dd.m and re-project so
   the raw C_ours values exist independently of the guard outcome.  It touches
   NOTHING in the production path; it only READS the production projector output.

   The extracted C_scalar_full == full_basis_coeffs["R_S_S"] is the ROTATED-
   COMPLETE transfer read-off (the ~1.66e-10 round-3 lineage, AMENDMENT5R1) —
   the gH axis.  C_twist2 is the O_Tq contracted twist-2 coefficient — the free
   second axis.

   Usage:
     wolframscript -script p3_extract_cours.wls <sd_projection.wl> \
        <amp_reduced.m> <amp_dd.m> <mchi> <mq> <out.json>
*)
args = Rest[$ScriptCommandLine];
{projPath, ampPath, ddPath, mchiS, mqS, outPath} = args;
mchi = ToExpression[mchiS];
mq = ToExpression[mqS];

Get[projPath];
amp = Get[ampPath];
abbrF = Cases["abbr" /. amp, HoldPattern[_ -> _WeylChain]];
dd = Get[ddPath];
Mnum = dd["expanded_amplitude"];

p = projectOperators[Mnum, abbrF, mchi, mq];

result = <|
  "ok" -> TrueQ[p["ok"]],
  "reason" -> Lookup[p, "reason", "OK"],
  "m_chi" -> mchi,
  "m_q" -> mq,
  (* gH axis: rotated-complete R_S_S read-off (the physical scalar lineage) *)
  "C_scalar_full_re" -> Re[Lookup[p, "C_scalar_full", Missing[]]],
  "C_scalar_full_im" -> Im[Lookup[p, "C_scalar_full", Missing[]]],
  (* the 3-op (unrotated) scalar fit, for the record (the polluted lineage) *)
  "C_scalar_3op_re" -> Re[Lookup[p, "C_scalar", Missing[]]],
  "C_scalar_3op_im" -> Im[Lookup[p, "C_scalar", Missing[]]],
  (* twist-2 axis: O_Tq contracted coefficient *)
  "C_twist2_re" -> Re[Lookup[p, "C_twist2", Missing[]]],
  "C_twist2_im" -> Im[Lookup[p, "C_twist2", Missing[]]],
  (* Majorana diagnostic (must be ~0) *)
  "C_chi_vector_re" -> Re[Lookup[p, "C_chi_vector", Missing[]]],
  (* instrument health *)
  "si_shift_rel" -> Lookup[p, "si_shift_rel", Missing[]],
  "full_basis_completeness_rel_residual" ->
    Lookup[p, "full_basis_completeness_rel_residual", Missing[]],
  "rotation_exactness_max" -> Lookup[p, "rotation_exactness_max", Missing[]],
  "basis_rank" -> Lookup[p, "basis_rank", Missing[]],
  "basis_cond" -> Lookup[p, "basis_cond", Missing[]],
  "completeness_ok" -> Lookup[p, "completeness_ok", Missing[]]
|>;

Export[outPath, result, "JSON"];
Print["p3_extract: wrote ", outPath];
Print["  C_scalar_full(R_S_S) Re = ", InputForm[result["C_scalar_full_re"]],
      "  Im = ", InputForm[result["C_scalar_full_im"]]];
Print["  C_twist2 Re = ", InputForm[result["C_twist2_re"]]];
Print["  si_shift_rel = ", InputForm[result["si_shift_rel"]],
      "  full_completeness = ", InputForm[result["full_basis_completeness_rel_residual"]]];
Exit[0]
