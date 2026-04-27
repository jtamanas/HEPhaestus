"""conftest.py — ensure modelspec_v3 is importable."""
import sys
from pathlib import Path

# Add _shared/ to sys.path so `from modelspec_v3 import ...` works.
# Path layout: skills/_shared/modelspec_v3/tests/conftest.py
#   parents[0] = tests/
#   parents[1] = modelspec_v3/
#   parents[2] = _shared/   <-- this is the package root
_SHARED = Path(__file__).parents[2]  # .../skills/_shared
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
