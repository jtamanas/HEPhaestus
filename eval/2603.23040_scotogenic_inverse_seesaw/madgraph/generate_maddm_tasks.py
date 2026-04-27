"""
MadDM task generator for arXiv:2603.23040 scotogenic inverse seesaw model.
Step 18: gating script.

PLAN-C MADDM DROP (Step 0.5.3 triggered):
MadDM sample output could not be obtained within the 2h search budget.
Per plan §4 Plan-C, this script always returns 0 and emits no tasks.
M1/M2 test stubs are removed from test_benchmarks.py.

If MadDM becomes available in the future, restore the original logic:
1. Implement _maddm_env_ok() to check MADDM_PATH, MG5_AMC_PATH, mg5_aMC executable, UFO dir.
2. Write tier3_maddm_paper2.generated.yaml when environment passes the gate.
"""

import os
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def _maddm_env_ok() -> bool:
    """Strict MadDM environment gate.

    Returns True iff ALL of:
    - os.environ.get('MADDM_PATH') exists and is a directory
    - os.environ.get('MG5_AMC_PATH') exists and is a directory
    - $MG5_AMC_PATH/bin/mg5_aMC is an executable file
    - The UFO model dir exists under the paper's madgraph/ dir

    Plan-C MadDM drop: always returns False.
    """
    return False  # Plan-C: always disabled


def main() -> int:
    """Emit tier3_maddm_paper2.generated.yaml if MadDM environment is configured.

    Under Plan-C MadDM drop, always returns 0 and emits nothing.
    """
    if not _maddm_env_ok():
        logger.info("MadDM not configured; emitting no tasks")
        return 0
    # Unreachable under Plan-C drop
    logger.info("MadDM configured; writing generated task file...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
