D=/Users/yianni/.claude/jobs/c703354a/tmp/item4-r2/d3-toy2
SCRIPTS=/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-a4f66e3295b1b33b8/plugins/hep-ph-toolkit/skills
FORMBIN=/Users/yianni/Library/WolframEngine/Applications/FormCalc-9.10/MacOSX-ARM64/form
FAK="/Applications/Wolfram Engine 2.app/Contents/MacOS/WolframKernel"
: > $D/kinematics.m
run_step () { # name logfile cmd...
  name=$1; log=$2; shift 2
  for attempt in 1 2 3 4 5 6 7 8; do
    until [ "$(pgrep -x WolframKernel | wc -l | tr -d ' ')" = "0" ]; do sleep 60; done
    "$@" > "$log" 2>&1
    rc=$?
    if [ $rc -eq 0 ] && ! grep -q "license error" "$log"; then
      echo "TOY2: $name rc=0 attempt=$attempt"; return 0
    fi
    if grep -q "license error" "$log"; then
      echo "TOY2: $name attempt=$attempt license-contention rc=$rc; retry in 300s"
      sleep 300
    else
      echo "TOY2: $name rc=$rc attempt=$attempt NON-LICENSE FAILURE"; return 1
    fi
  done
  echo "TOY2: $name EXHAUSTED retries"; return 1
}
run_step gen $D/gen.log "$FAK" -script $D/toy2_gen.wls || exit 1
run_step reduce $D/reduce.log wolframscript -script $SCRIPTS/formcalc/scripts/run_calcfeynamp.wls $D/toy2_amps.m $D/kinematics.m $D/out $HOME/Library/WolframEngine/Applications $FORMBIN weyl D $D/run || exit 1
echo "TOY2: ALL DONE"
