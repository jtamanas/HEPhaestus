"""test_main_c_template.py — byte-identical golden tests for main_c_template.py.

For each subcommand (relic, scatter, annihilate, indirect), the rendered output
must be byte-identical to the committed golden fixture.
Also verifies that HEPPH_MICROMEGAS_SEED=42 is embedded in all outputs.
"""
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from main_c_template import render, _SEED

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "main_c"

_DM = {"pdg": 9000001, "name": "S", "mass_gev": 100.0}
_SPEC = {"dm_candidate": {"pdg": 9000001, "name": "S", "mass_gev": 100.0}}


@pytest.mark.parametrize("subcommand", ["relic", "scatter", "annihilate", "indirect"])
def test_byte_identical_golden(subcommand):
    """Rendered output must match the committed golden fixture byte-for-byte."""
    golden_path = _FIXTURES / f"{subcommand}_singletDM.c"
    assert golden_path.exists(), f"Golden fixture missing: {golden_path}"
    golden = golden_path.read_text()
    rendered = render(subcommand, _SPEC, _DM)
    assert rendered == golden, (
        f"Output for '{subcommand}' differs from golden.\n"
        f"First difference at char {next((i for i, (a, b) in enumerate(zip(rendered, golden)) if a != b), 'end')}\n"
        f"Rendered[:200]: {rendered[:200]!r}\n"
        f"Golden[:200]:   {golden[:200]!r}"
    )


def test_seed_pinned_in_relic():
    rendered = render("relic", _SPEC, _DM)
    assert str(_SEED) in rendered, f"Seed {_SEED} not found in relic output"


def test_seed_pinned_in_scatter():
    rendered = render("scatter", _SPEC, _DM)
    assert str(_SEED) in rendered


def test_seed_value_is_42():
    assert _SEED == 42


def test_invalid_subcommand_raises():
    with pytest.raises(ValueError, match="Unknown subcommand"):
        render("all", _SPEC, _DM)


def test_hepph_micromegas_seed_env_in_all_subcommands():
    for sub in ["relic", "scatter", "annihilate", "indirect"]:
        rendered = render(sub, _SPEC, _DM)
        assert "HEPPH_MICROMEGAS_SEED" in rendered, (
            f"HEPPH_MICROMEGAS_SEED not in {sub} output"
        )
