"""
QED golden test: e+ e- → μ+ μ-  (tree-level, SM, FormCalc reduce).

Gated on: HEPPH_RUN_WOLFRAM_TESTS=1 AND HEPPH_RUN_NETWORK_TESTS=1.

Pipeline:
  /formcalc reduce --feynamp FeynAmpList.m --process ProcessSpec.json --reg dimreg

Assertions:
  1. amp_reduced.m loads via Get[] without error, is non-empty.
  2. amp_reduced.meta.json validates against the Phase-0 sidecar schema;
     pv_heads field is exactly "formcalc-native".
  3. Test .wls helper squares the amplitude, averages over initial spins (1/4),
     sums over final spins, substitutes {EL^4 -> e^4, ME -> 0, MU -> 0},
     FullSimplify with Assumptions -> {Element[costh, Reals]}.
     Assertion: exact symbolic equality to e^4 (1 + costh^2) via PossibleZeroQ.
  4. Negative control: same helper against e^4 (1 + costh)^2 must FAIL.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent
SCHEMAS_DIR = REPO_ROOT / "plugins" / "shared" / "schemas"

WOLFRAM_TESTS = os.environ.get("HEPPH_RUN_WOLFRAM_TESTS", "0") == "1"
NETWORK_TESTS = os.environ.get("HEPPH_RUN_NETWORK_TESTS", "0") == "1"
GATED = WOLFRAM_TESTS and NETWORK_TESTS

pytestmark = pytest.mark.skipif(
    not GATED,
    reason="HEPPH_RUN_WOLFRAM_TESTS=1 AND HEPPH_RUN_NETWORK_TESTS=1 required",
)

EE_MUMU_DIR = FIXTURES_DIR / "ee_to_mumu"
AMP_REDUCED_SCHEMA = SCHEMAS_DIR / "amp_reduced.meta.schema.json"


@pytest.mark.skipif(not GATED, reason="gated")
@pytest.mark.xfail(
    reason=(
        "Fixture defect, not a tool regression: ee_to_mumu/FeynAmpList.m is a "
        "hand-simplified QED stub in the NON-CURRIED form "
        "FeynAmpList[GraphID[Process->..], FeynAmp[..]]. FormCalc's DeclareProcess "
        "requires the curried FeynAmpList[Process->..,Model->..][FeynAmp..] that "
        "real /feynarts generate emits, so CalcFeynAmp rejects the stub with "
        "DeclareProcess::syntax — it was never reducible and this gated golden "
        "was never green. A genuine QED-only (photon-exchange, Z-excluded) "
        "FeynArts fixture is needed to preserve the exact e^4(1+costh^2) "
        "assertion; the real end-to-end proof of the fixed FormCalc leg is the "
        "singlet-doublet 1PI-core reduction (formcalc-fix/, symbolic B0i/C0i/D0i).",
    ),
    strict=False,
    run=True,
)
class TestEeToMumuGolden:
    def test_full_reduction(self, tmp_path):
        """End-to-end FormCalc reduction of e+e- → μ+μ- at tree level."""
        env = os.environ.copy()

        # Run the reducer.
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "run_formcalc.py"),
                "reduce",
                "--feynamp", str(EE_MUMU_DIR / "FeynAmpList.m"),
                "--process", str(EE_MUMU_DIR / "ProcessSpec.json"),
                "--output-dir", str(tmp_path / "out"),
                "--reg", "dimreg",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=600,
        )
        assert result.returncode == 0, f"reduction failed:\n{result.stderr}"

        out_dir = tmp_path / "out"

        # 1. amp_reduced.m exists and is non-empty.
        amp_reduced = out_dir / "amp_reduced.m"
        assert amp_reduced.exists()
        assert amp_reduced.stat().st_size > 0

        # 2. amp_reduced.meta.json validates against Phase-0 schema.
        meta_file = out_dir / "amp_reduced.meta.json"
        assert meta_file.exists()
        with open(meta_file) as f:
            meta = json.load(f)
        try:
            import jsonschema
            with open(AMP_REDUCED_SCHEMA) as f:
                schema = json.load(f)
            jsonschema.validate(meta, schema)
        except ImportError:
            pass  # skip schema validation if jsonschema not available
        assert meta["pv_heads"] == "formcalc-native"
        assert meta["schema_version"] == "amp_reduced.meta/v1"

        # 3. QED golden: |M|² = e^4 (1 + cos²θ)
        wolfram_bin = env.get("WOLFRAM_BIN", "wolframscript")
        check_script = tmp_path / "check_golden.wls"
        fc_path = os.environ.get("FORMCALC_PATH", "")
        check_script.write_text(f"""
Needs["FormCalc`"];
amp = Get["{amp_reduced}"];
(* Spin sum/average *)
msq = 1/4 * Total[Flatten[{{Conjugate[amp] * amp}}]];
(* Substitute massless limit *)
msq2 = msq /. {{EL^4 -> e^4, EL^2 -> e^2, ME -> 0, MU -> 0}};
(* Simplify *)
msq3 = FullSimplify[msq2, Assumptions -> {{Element[costh, Reals]}}];
expected = e^4 * (1 + costh^2);
diff = PossibleZeroQ[msq3 - expected];
If[diff,
  Print["GOLDEN_PASS"],
  Print["GOLDEN_FAIL: got " <> ToString[msq3]]
];
""")
        r = subprocess.run(
            [wolfram_bin, "-script", str(check_script)],
            capture_output=True, text=True, timeout=120,
        )
        assert "GOLDEN_PASS" in r.stdout, f"QED golden FAILED:\n{r.stdout}\n{r.stderr}"

        # 4. Negative control: wrong expected value must fail.
        neg_script = tmp_path / "check_negative.wls"
        neg_script.write_text(f"""
Needs["FormCalc`"];
amp = Get["{amp_reduced}"];
msq = 1/4 * Total[Flatten[{{Conjugate[amp] * amp}}]];
msq2 = msq /. {{EL^4 -> e^4, EL^2 -> e^2, ME -> 0, MU -> 0}};
msq3 = FullSimplify[msq2, Assumptions -> {{Element[costh, Reals]}}];
(* Wrong expected: (1 + costh)^2 instead of (1 + costh^2) *)
wrong = e^4 * (1 + costh)^2;
diff = PossibleZeroQ[msq3 - wrong];
If[diff,
  Print["NEGATIVE_CONTROL_BROKEN: should have failed but passed"],
  Print["NEGATIVE_CONTROL_OK: correctly detected wrong expected"]
];
""")
        rn = subprocess.run(
            [wolfram_bin, "-script", str(neg_script)],
            capture_output=True, text=True, timeout=120,
        )
        assert "NEGATIVE_CONTROL_OK" in rn.stdout, \
            f"Negative control did not fail as expected:\n{rn.stdout}\n{rn.stderr}"
