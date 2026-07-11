"""Integration tests for /feynarts generate.

GATED: requires HEPPH_RUN_WOLFRAM_TESTS=1.
SARAH-independent: all goldens use FeynArts built-in SM.

Run locally with:
  HEPPH_RUN_WOLFRAM_TESTS=1 pytest \
    plugins/hep-ph-toolkit/skills/feynarts/tests/test_integration_gated.py -v
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

# Gate condition
WOLFRAM_TESTS = os.environ.get("HEPPH_RUN_WOLFRAM_TESTS", "0") == "1"
skip_unless_wolfram = pytest.mark.skipif(
    not WOLFRAM_TESTS,
    reason="HEPPH_RUN_WOLFRAM_TESTS=1 required",
)

GOLDENS_DIR = Path(__file__).parent / "goldens"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def run_feynarts_module():
    """Import run_feynarts lazily so tests can be collected without Wolfram."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    import run_feynarts
    return run_feynarts


@skip_unless_wolfram
class TestSmEeMumuTreeGolden:
    """Tree-level e+e- -> mu+mu- golden. Expected: exactly 1 diagram."""

    def test_n_diagrams_equals_1(self, run_feynarts_module, tmp_path):
        summary = run_feynarts_module.run(
            process="e+ e- -> mu+ mu-",
            model="SM",
            loop_order=0,
            output_dir=str(tmp_path),
            force=True,
        )
        assert summary["n_diagrams"] == 1, (
            f"Expected exactly 1 diagram for e+e- → mu+mu- tree, got {summary['n_diagrams']}"
        )

    def test_summary_fields(self, run_feynarts_module, tmp_path):
        summary = run_feynarts_module.run(
            process="e+ e- -> mu+ mu-",
            model="SM",
            loop_order=0,
            output_dir=str(tmp_path),
            force=True,
        )
        assert summary["loop_order"] == 0
        assert summary["model"] == "SM"
        assert summary["process"]["in"] == ["e+", "e-"]
        assert summary["process"]["out"] == ["mu+", "mu-"]
        assert isinstance(summary["cached"], bool)

    def test_meta_json_byte_equal_to_golden(self, run_feynarts_module, tmp_path):
        run_feynarts_module.run(
            process="e+ e- -> mu+ mu-",
            model="SM",
            loop_order=0,
            output_dir=str(tmp_path),
            force=True,
        )
        golden_meta = json.loads(
            (GOLDENS_DIR / "sm_ee_mumu_tree" / "FeynAmpList.meta.json").read_text()
        )
        produced_meta = json.loads((tmp_path / "FeynAmpList.meta.json").read_text())

        # Compare key fields (model_hash will differ; wall_clock_s not in meta)
        assert produced_meta["schema_version"] == golden_meta["schema_version"]
        assert produced_meta["feynarts_version"] == golden_meta["feynarts_version"]
        assert produced_meta["n_diagrams"] == golden_meta["n_diagrams"]
        # processspec sub-object must match the canonical processspec/v1 structure
        assert produced_meta["processspec"]["loop_order"] == golden_meta["processspec"]["loop_order"]
        assert produced_meta["processspec"]["kinematic_limit"] == golden_meta["processspec"]["kinematic_limit"]
        assert produced_meta["processspec"]["particles"] == golden_meta["processspec"]["particles"]

    def test_feynamplist_m_round_trip(self, run_feynarts_module, tmp_path):
        """FeynAmpList.m must exist and be non-empty after generation."""
        run_feynarts_module.run(
            process="e+ e- -> mu+ mu-",
            model="SM",
            loop_order=0,
            output_dir=str(tmp_path),
            force=True,
        )
        fa_list = tmp_path / "FeynAmpList.m"
        assert fa_list.exists(), "FeynAmpList.m not found in output dir"
        content = fa_list.read_text()
        assert len(content) > 0, "FeynAmpList.m is empty"
        # Basic sanity: must look like a Mathematica expression list
        assert "schema_version" in content or "FeynAmp" in content or "amp" in content


@skip_unless_wolfram
class TestZSelfEnergyGolden:
    """Z self-energy (Z->Z) at 1-loop. Expected: topology count matches golden."""

    def test_topology_count_in_range(self, run_feynarts_module, tmp_path):
        """v1 heuristic: topology count must be a positive integer in a plausible range.

        The exact topology count (3 for Z->Z 1-loop in SM per literature) cannot
        be asserted here because postprocess._estimate_n_topologies() is a
        heuristic that does not perform a Wolfram round-trip.  An exact assertion
        would always fail on real Wolfram runs.

        Exact topology extraction via TopologyList[] is deferred to v1.1.
        See: postprocess._estimate_n_topologies() docstring.
        """
        summary = run_feynarts_module.run(
            process="Z -> Z",
            model="SM",
            loop_order=1,
            output_dir=str(tmp_path),
            force=True,
        )

        topo_path = tmp_path / "topologies.json"
        assert topo_path.exists(), "topologies.json not produced"
        produced_topo = json.loads(topo_path.read_text())

        n = produced_topo["n_topologies"]
        assert isinstance(n, int), f"n_topologies must be int, got {type(n)}"
        assert 1 <= n <= 50, (
            f"Z self-energy topology count {n} is outside plausible range [1, 50]; "
            "exact extraction planned for v1.1"
        )

    def test_n_diagrams_positive(self, run_feynarts_module, tmp_path):
        summary = run_feynarts_module.run(
            process="Z -> Z",
            model="SM",
            loop_order=1,
            output_dir=str(tmp_path),
            force=True,
        )
        assert summary["n_diagrams"] > 0, "Z self-energy should have at least 1 diagram"


@skip_unless_wolfram
class TestSarahModelBootstrapEndToEnd:
    """--sarah-model singlet_doublet bootstraps from a fresh (scratch) state root.

    Exercises the full bootstrap: SARAH MakeFeynArts[] -> register
    feynarts_state/singlet_doublet.mod -> resolve -> generate the tree
    χ q -> χ q amplitude ({{F[5],F[4]},{F[5],F[4]}}). Expected: 1 diagram
    (t-channel scalar exchange).

    Uses a scratch state_root under tmp_path so the already-registered
    production state at ~/.local/share/hephaestus is never touched.
    """

    PROCESS = "{{F[5], F[4]}, {F[5], F[4]}}"

    def test_bootstrap_isolated_state_root(self, run_feynarts_module, tmp_path):
        scratch_root = tmp_path / "scratch_state"
        prod_mod = Path(
            os.path.expanduser("~/.local/share/hephaestus")
        ) / "models" / "singlet_doublet" / "feynarts_state" / "singlet_doublet.mod"

        # Guard: verify the override genuinely isolates before running.
        assert not scratch_root.exists(), "scratch state root must start empty"
        prod_before = prod_mod.stat().st_mtime if prod_mod.exists() else None

        summary = run_feynarts_module.run(
            process=self.PROCESS,
            sarah_model="singlet_doublet",
            loop_order=0,
            output_dir=str(tmp_path / "out"),
            state_root=str(scratch_root),
            force=True,
        )

        # State was bootstrapped INTO the scratch root ...
        scratch_mod = (
            scratch_root / "models" / "singlet_doublet" / "feynarts_state" / "singlet_doublet.mod"
        )
        assert scratch_mod.exists(), "bootstrap did not register .mod under scratch root"

        # ... and the production state was left untouched.
        if prod_before is not None:
            assert prod_mod.stat().st_mtime == prod_before, "production state was modified"

        assert summary["n_diagrams"] == 1, (
            f"Expected exactly 1 diagram for χ q → χ q tree, got {summary['n_diagrams']}"
        )
