"""Stub module — raises ANALYTIC_MODULE_MISSING on call.

Used as a placeholder for models whose analytic module has not been written yet
(e.g. dark_su3 pending WS-B/WS-C). Behaves like a 'registered but unimplemented'
marker: the analytic backend catches the RuntimeError and emits the fatal code.
"""

STUB = True  # detected by /model-router; promote to a real impl + registry entry to clear


def compute(spec, params):
    raise RuntimeError(
        "Analytic module for this model is not implemented. "
        "Either remove backends.analytic_module from spec.yaml or wait for the "
        "model's analytic module to land."
    )
