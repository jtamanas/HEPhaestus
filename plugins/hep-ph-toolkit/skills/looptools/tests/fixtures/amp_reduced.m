(* amp_reduced.m — frozen FormCalc-reduced amplitude (fixture).
   Stand-in for /formcalc reduce output on the TwoHdmAfix charged-Higgs/W box
   (A0 H+ W- topology) for the loop-only DD subchain.  Native FormCalc PV heads
   (B0i/C0i/D0i) are retained per the formcalc PV-heads policy.
   Numbers are placeholder-but-consistent; the Tier-3 smoke replaces them.
   This file is read only as bytes by the cache key here; the deferred
   run_eval.wls Get[]s it on a tooled box. *)
amp = Amp[{F[11, {1}], -F[11, {1}]} -> {F[3, {1}], -F[3, {1}]}][
  (Alfa^2 * Pi) * (
      gchi^2 * (
          D0i[dd0, MW2, MHp2, Ma2, 0, S, T] * Pair[e[1], e[2]]
        + C0i[cc0, MW2, MHp2, Ma2] * Pair[k[1], e[2]]
        + B0i[bb0, S, MW2, MHp2]
      )
  )
];
amp
