#!/usr/bin/env wolframscript
(* run_eval.wls — Wolfram + LoopTools (MathLink) numerical evaluation driver.

   DEFERRED REAL PATH (mechanism A — build plan §2).  Exercised only by the
   Tier-3 smoke (tests/test_smoke.py, gated on HEPPH_RUN_WOLFRAM_TESTS=1).  It
   is a static asset: writing it requires no tools; running it requires Wolfram
   Engine + FormCalc + the LoopTools MathLink binary.

   Usage (called from run_looptools.py run_driver):
     wolframscript -script run_eval.wls \
       <amp_reduced.m> <point.json> <form_factor_preset> <eval_output.json> <looptools_prefix>

   Contract — writes <eval_output.json> conforming to looptools_eval_output/v1:
     {
       "schema": "looptools_eval_output/v1",
       "point_id": <string>,
       "m_dm_gev": <number>,
       "amplitude": {"finite": <bool>, "uv_pole_residue": <number>,
                     "ir_pole_residue": <number>,
                     "gauge_parameter_dependence": <number>},
       "effective_couplings": {"f_p_si_gev_minus2": <number>,
                               "f_n_si_gev_minus2": <number>,
                               "f_p_sd_gev_minus2": <number|null>,
                               "f_n_sd_gev_minus2": <number|null>},
       "nucleon_form_factors": {"preset": <string>},
       "loop_topologies": [<string>...],
       "looptools_version": <string>, "n_pv_calls": <int>,
       "n_diagrams": <int>, "pv_heads_used": [<string>...]
     }

   The quark→nucleon scalar form-factor contraction (α_q → f_N with the
   default_2018 / A1 σ-terms and the 2/27 f_TG heavy-quark gluon matching) is
   performed HERE — see build plan §8 dec. #4: this is the right place to know
   the quark content, and it is the part validated only by the smoke.  Python's
   match_nucleon.py then just applies σ = (4/π) μ² f².
*)

Module[{
    ampPath, pointPath, ffPreset, outPath, ltPrefix,
    point, mDM, amp, finiteQ, uvRes, irRes, gaugeDep,
    fp, fn, fpSD, fnSD, nPV, nDiag, pvHeads, ltVersion, pointId,
    ltBin, jsonAssoc
  },

  If[Length[$ScriptCommandLine] < 6,
    WriteString["stderr", "run_eval.wls: insufficient arguments\n"]; Exit[1]
  ];
  ampPath   = $ScriptCommandLine[[2]];
  pointPath = $ScriptCommandLine[[3]];
  ffPreset  = $ScriptCommandLine[[4]];
  outPath   = $ScriptCommandLine[[5]];
  ltPrefix  = $ScriptCommandLine[[6]];

  (* Load FormCalc *)
  Check[Needs["FormCalc`"],
    WriteString["stderr", "run_eval: Needs[FormCalc`] failed\n"]; Exit[1]
  ];

  (* Install the LoopTools MathLink binary so A0i/B0i/C0i/D0i evaluate numerically. *)
  ltBin = FileNameJoin[{ltPrefix, "bin", "LoopTools"}];
  If[!FileExistsQ[ltBin],
    WriteString["stderr", "run_eval: LoopTools MathLink binary not found: " <> ltBin <> "\n"];
    Exit[1]
  ];
  Check[Install[ltBin],
    WriteString["stderr", "run_eval: Install[LoopTools] failed\n"]; Exit[1]
  ];
  (* Initialise LoopTools (UV pole 'getdelta', renormalisation scale 'getmudim'). *)
  Quiet[Check[ltini[], Null]];

  (* Read the model point (numeric substitution map + DM mass). *)
  point  = Quiet[Check[Import[pointPath, "RawJSON"], $Failed]];
  If[point === $Failed,
    WriteString["stderr", "run_eval: could not read point.json\n"]; Exit[1]
  ];
  mDM    = point["m_dm_gev"];
  pointId = "twohdmafix-dm" <> ToString[mDM];

  (* Load the FormCalc-reduced amplitude (symbolic, with native PV heads). *)
  amp = Quiet[Check[Get[ampPath], $Failed]];
  If[amp === $Failed,
    WriteString["stderr", "run_eval: Get[amp_reduced.m] failed\n"]; Exit[1]
  ];

  (* ---------------------------------------------------------------------------
     PLACEHOLDER NUMERICAL CORE.  On a tooled machine this section:
       1. builds the kinematics for elastic DM–quark scattering (t→0),
       2. substitutes the numeric model point into the amplitude abbreviations,
       3. lets the installed LoopTools MathLink functions evaluate the PV heads,
       4. extracts the scalar Wilson coefficients α_q (q=u,d,s,c,b,t),
       5. contracts α_q with the chosen nucleon σ-term preset (ffPreset):
            f_N = m_N [ Σ_{u,d,s} f_Tq^N α_q/m_q
                       + (2/27) f_TG^N Σ_{c,b,t} α_q/m_q ],
          with default_2018 / A1 σ-terms,
       6. records UV/IR/gauge residues from the abbreviation manifest so the
          smoke can assert UV-finiteness + gauge-stability.
     The numbers below are intentionally left as 0/None so that an UNMODIFIED
     run on a tooled box FAILS LOUDLY (non-finite gate) rather than emitting a
     fake cross-section.  The smoke test replaces this core with the real
     CalcFeynAmp/LoopTools evaluation. --------------------------------------- *)
  finiteQ = False;             (* real run sets True after UV/IR cancellation check *)
  uvRes   = 0.0;
  irRes   = 0.0;
  gaugeDep = 0.0;
  fp = 0.0; fn = 0.0; fpSD = Null; fnSD = Null;
  nPV = 0; nDiag = If[Head[amp] === FeynAmpList, Length[amp], 0];
  pvHeads = {"B0i", "C0i", "D0i"};
  ltVersion = "2.16";

  jsonAssoc = <|
    "schema" -> "looptools_eval_output/v1",
    "point_id" -> pointId,
    "m_dm_gev" -> mDM,
    "amplitude" -> <|
      "finite" -> finiteQ,
      "uv_pole_residue" -> uvRes,
      "ir_pole_residue" -> irRes,
      "gauge_parameter_dependence" -> gaugeDep
    |>,
    "effective_couplings" -> <|
      "f_p_si_gev_minus2" -> fp,
      "f_n_si_gev_minus2" -> fn,
      "f_p_sd_gev_minus2" -> fpSD,
      "f_n_sd_gev_minus2" -> fnSD
    |>,
    "nucleon_form_factors" -> <|"preset" -> ffPreset|>,
    "loop_topologies" -> {"chargedHiggs_W_box", "mediator_triangle"},
    "looptools_version" -> ltVersion,
    "n_pv_calls" -> nPV,
    "n_diagrams" -> nDiag,
    "pv_heads_used" -> pvHeads
  |>;

  Export[outPath, jsonAssoc, "RawJSON"];
  Quiet[Check[ltexi[], Null]];
  Print["run_eval: wrote ", outPath, " (finite=", finiteQ, ")"];
  Exit[0]
]
