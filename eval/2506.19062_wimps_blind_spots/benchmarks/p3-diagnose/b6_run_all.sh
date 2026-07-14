#!/bin/bash
# B6 batch: run every (leg,sector,channel) DD projection sequentially.
# Skips a combo whose cours.json already exists (idempotent / resumable).
set -u
KROOT=/Users/yianni/.claude/jobs/c703354a/tmp/p3-b6-worktree/eval/2506.19062_wimps_blind_spots/benchmarks/p3-diagnose
BSC=/Users/yianni/.claude/jobs/c703354a/tmp/p3-b6-scratch
for LEG in L2 L3; do
  for SEC in db cb; do
    for CHAN in Wpure Zpure Yukawa WwithHp remainder; do
      OUT=$BSC/runs/${LEG}_${SEC}_${CHAN}/cours.json
      if [ -s "$OUT" ]; then echo "SKIP $LEG/$SEC/$CHAN (exists)"; continue; fi
      echo "############ RUN $LEG/$SEC/$CHAN $(date +%T) ############"
      bash $KROOT/b6_kernel.sh $LEG $SEC $CHAN 2>&1 | tail -4
    done
  done
done
echo "ALL DONE $(date +%T)"
