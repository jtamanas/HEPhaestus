D=/Users/yianni/.claude/jobs/c703354a/tmp/item4-r2/d3
SCRIPTS=/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-a4f66e3295b1b33b8/plugins/hep-ph-toolkit/skills
FORMBIN=/Users/yianni/Library/WolframEngine/Applications/FormCalc-9.10/MacOSX-ARM64/form
run_step () { # name logfile cmd...
  name=$1; log=$2; shift 2
  for attempt in 1 2 3 4 5 6 7 8; do
    until [ "$(pgrep -x WolframKernel | wc -l | tr -d ' ')" = "0" ]; do sleep 60; done
    "$@" > "$log" 2>&1
    rc=$?
    if [ $rc -eq 0 ] && ! grep -q "license error" "$log"; then
      echo "D3: $name rc=0 attempt=$attempt"; return 0
    fi
    if grep -q "license error" "$log" || [ $rc -eq 139 ]; then
      echo "D3: $name attempt=$attempt license-contention rc=$rc; retrying in 300s"
      sleep 300
    else
      echo "D3: $name rc=$rc attempt=$attempt NON-LICENSE FAILURE"; return $rc
    fi
  done
  echo "D3: $name EXHAUSTED retries"; return 1
}
set -e
run_step gen $D/gen.log wolframscript -script $D/toy_gen.wls
run_step reduce $D/reduce.log wolframscript -script $SCRIPTS/formcalc/scripts/run_calcfeynamp.wls $D/toy_amps.m $D/kinematics.m $D/out $HOME/Library/WolframEngine/Applications $FORMBIN weyl D $D/run
run_step project $D/project.log wolframscript -script $D/toy_project.wls $D/out/amp_reduced.m $D/kinematics.m default_2018 $D/out/unused.json /Users/yianni/LoopTools/LoopTools-2.16
echo "D3: ALL DONE"
