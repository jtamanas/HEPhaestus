"""
test_constraint_dispatch.py — lint SKILL.md for required §Constraint &
observable dispatch content.

These tests assert that the orchestrator SKILL.md:
- contains the four intent sections by heading anchor
- names the correct sub-skills for each intent
- mentions the scattering/v1 schema (data hand-off contract) where expected
- has a data-flow diagram section

No external tools or install state required.
"""

import re
from pathlib import Path

import pytest

_SKILL_MD = (
    Path(__file__).resolve().parent.parent / "SKILL.md"
)


@pytest.fixture(scope="module")
def skill_text() -> str:
    return _SKILL_MD.read_text()


# ---------------------------------------------------------------------------
# Section-presence guards
# ---------------------------------------------------------------------------


def test_constraint_dispatch_section_present(skill_text: str) -> None:
    """The orchestrator must contain a §Constraint & observable dispatch section."""
    assert "## Constraint & observable dispatch" in skill_text, (
        "SKILL.md must have '## Constraint & observable dispatch' heading"
    )


def test_data_flow_diagram_section_present(skill_text: str) -> None:
    """The orchestrator must include a data-flow diagram section."""
    assert "## Data-flow diagram" in skill_text, (
        "SKILL.md must have '## Data-flow diagram' heading"
    )


def test_prerequisite_install_table_present(skill_text: str) -> None:
    """A prerequisite install table must reference the shared install
    references for each tool. Post-2026-04-29 refactor the *-install
    skills are gone; consumers point at _shared/installs/<tool>/."""
    assert "_shared/installs/micromegas" in skill_text, (
        "SKILL.md must reference _shared/installs/micromegas prerequisite"
    )
    assert "_shared/installs/higgstools" in skill_text, (
        "SKILL.md must reference _shared/installs/higgstools prerequisite"
    )
    assert "_shared/installs/ddcalc" in skill_text, (
        "SKILL.md must reference _shared/installs/ddcalc prerequisite"
    )


# ---------------------------------------------------------------------------
# Intent 1 — relic density
# ---------------------------------------------------------------------------


def test_intent_relic_density_heading(skill_text: str) -> None:
    """Intent 1 heading must be present."""
    assert "Intent 1" in skill_text and "relic density" in skill_text, (
        "SKILL.md must have an Intent 1 (relic density) heading"
    )


def test_intent_relic_density_trigger_phrases(skill_text: str) -> None:
    """Relic density section must list example trigger phrases."""
    assert "Ωh²" in skill_text or "relic" in skill_text.lower(), (
        "SKILL.md must mention relic density / Ωh² trigger phrases"
    )


def test_intent_relic_density_dispatches_micromegas_relic(skill_text: str) -> None:
    """/micromegas relic must be the dispatched command for relic intent."""
    assert "/micromegas relic" in skill_text, (
        "SKILL.md must dispatch '/micromegas relic' for relic-density intent"
    )


def test_intent_relic_density_mentions_slha_and_ufo_flags(skill_text: str) -> None:
    """The relic command must pass --slha and --ufo."""
    # Find the relic section and check flags appear
    idx = skill_text.find("/micromegas relic")
    assert idx != -1
    snippet = skill_text[idx : idx + 300]
    assert "--slha" in snippet, "relic dispatch must include --slha flag"
    assert "--ufo" in snippet, "relic dispatch must include --ufo flag"


def test_intent_relic_density_no_dd_stage(skill_text: str) -> None:
    """Relic density is a single-call chain — no /ddcalc in the relic intent block."""
    # Extract only the Intent 1 section (between "Intent 1" and "Intent 2")
    intent1_start = skill_text.find("### Intent 1")
    intent2_start = skill_text.find("### Intent 2")
    assert intent1_start != -1 and intent2_start != -1
    intent1_block = skill_text[intent1_start:intent2_start]
    assert "/ddcalc" not in intent1_block, (
        "Intent 1 (relic) must not dispatch /ddcalc — single-call chain only"
    )


# ---------------------------------------------------------------------------
# Intent 2 — direct-detection exclusion
# ---------------------------------------------------------------------------


def test_intent_dd_exclusion_heading(skill_text: str) -> None:
    """Intent 2 heading must be present."""
    assert "Intent 2" in skill_text and "direct-detection" in skill_text, (
        "SKILL.md must have an Intent 2 (direct-detection exclusion) heading"
    )


def test_intent_dd_dispatches_micromegas_scatter(skill_text: str) -> None:
    """/micromegas scatter must be Stage 1 of the DD chain."""
    assert "/micromegas scatter" in skill_text, (
        "SKILL.md must dispatch '/micromegas scatter' for DD exclusion intent"
    )


def test_intent_dd_dispatches_ddcalc_exclude(skill_text: str) -> None:
    """/ddcalc exclude must be Stage 2 of the DD chain."""
    assert "/ddcalc exclude" in skill_text, (
        "SKILL.md must dispatch '/ddcalc exclude' for DD exclusion intent"
    )


def test_intent_dd_mentions_scattering_schema(skill_text: str) -> None:
    """The DD chain must mention the scattering/v1 data contract."""
    assert "scattering/v1" in skill_text, (
        "SKILL.md must mention 'scattering/v1' schema in DD dispatch chain"
    )


def test_intent_dd_data_handoff_sigma_json(skill_text: str) -> None:
    """The hand-off from Stage 1 to Stage 2 must use --sigma-json."""
    assert "--sigma-json" in skill_text, (
        "SKILL.md must use '--sigma-json' for Stage 1→Stage 2 hand-off in DD chain"
    )


def test_intent_dd_two_stages(skill_text: str) -> None:
    """DD exclusion must be documented as a two-stage chain."""
    intent2_start = skill_text.find("### Intent 2")
    intent3_start = skill_text.find("### Intent 3")
    assert intent2_start != -1 and intent3_start != -1
    intent2_block = skill_text[intent2_start:intent3_start]
    assert "Stage 1" in intent2_block, "Intent 2 must label Stage 1"
    assert "Stage 2" in intent2_block, "Intent 2 must label Stage 2"


# ---------------------------------------------------------------------------
# Intent 3 — Higgs constraints
# ---------------------------------------------------------------------------


def test_intent_higgs_constraints_heading(skill_text: str) -> None:
    """Intent 3 heading must be present."""
    assert "Intent 3" in skill_text and "Higgs" in skill_text, (
        "SKILL.md must have an Intent 3 (Higgs constraints) heading"
    )


def test_intent_higgs_dispatches_higgstools_run(skill_text: str) -> None:
    """/higgstools run must be the dispatched command."""
    assert "/higgstools run" in skill_text, (
        "SKILL.md must dispatch '/higgstools run' for Higgs-constraints intent"
    )


def test_intent_higgs_passes_slha(skill_text: str) -> None:
    """The higgstools command must pass --slha."""
    idx = skill_text.find("/higgstools run")
    assert idx != -1
    snippet = skill_text[idx : idx + 200]
    assert "--slha" in snippet, "Higgs dispatch must include --slha flag"


def test_intent_higgs_mentions_hb_and_hs(skill_text: str) -> None:
    """The Higgs section must mention both hb_allowed and hs_consistent."""
    intent3_start = skill_text.find("### Intent 3")
    intent4_start = skill_text.find("### Intent 4")
    assert intent3_start != -1 and intent4_start != -1
    intent3_block = skill_text[intent3_start:intent4_start]
    assert "hb_allowed" in intent3_block, "Intent 3 must mention hb_allowed"
    assert "hs_consistent" in intent3_block, "Intent 3 must mention hs_consistent"


def test_intent_higgs_slha_missing_blocks_blocker(skill_text: str) -> None:
    """The Higgs section must mention HIGGSTOOLS_SLHA_MISSING_BLOCKS."""
    assert "HIGGSTOOLS_SLHA_MISSING_BLOCKS" in skill_text, (
        "SKILL.md must mention HIGGSTOOLS_SLHA_MISSING_BLOCKS in Higgs intent"
    )


# ---------------------------------------------------------------------------
# Intent 4 — one-loop scattering
# ---------------------------------------------------------------------------


def test_intent_oneloop_heading(skill_text: str) -> None:
    """Intent 4 heading must be present."""
    assert "Intent 4" in skill_text and "one-loop" in skill_text, (
        "SKILL.md must have an Intent 4 (one-loop scattering) heading"
    )


def test_intent_oneloop_dispatches_feynarts_generate(skill_text: str) -> None:
    """/feynarts generate must be Stage 1 of the one-loop chain."""
    assert "/feynarts generate" in skill_text, (
        "SKILL.md must dispatch '/feynarts generate' for one-loop intent"
    )


def test_intent_oneloop_dispatches_formcalc_reduce(skill_text: str) -> None:
    """/formcalc reduce must be Stage 2 of the one-loop chain."""
    assert "/formcalc reduce" in skill_text, (
        "SKILL.md must dispatch '/formcalc reduce' for one-loop intent"
    )


def test_intent_oneloop_dispatches_looptools_stage3(skill_text: str) -> None:
    """LoopTools must be Stage 3 of the one-loop chain."""
    assert "LoopTools" in skill_text, (
        "SKILL.md must reference 'LoopTools' for one-loop intent Stage 3"
    )


def test_intent_oneloop_optional_ddcalc_stage4(skill_text: str) -> None:
    """Stage 4 (/ddcalc exclude) must be documented as optional."""
    intent4_start = skill_text.find("### Intent 4")
    # Find next section boundary
    next_section = skill_text.find("\n---\n", intent4_start)
    assert intent4_start != -1
    intent4_block = (
        skill_text[intent4_start:next_section]
        if next_section != -1
        else skill_text[intent4_start:]
    )
    assert "Stage 4" in intent4_block, "Intent 4 must have a Stage 4 block"
    # Stage 4 must be marked optional
    assert "optional" in intent4_block.lower(), (
        "Intent 4 Stage 4 (/ddcalc exclude) must be marked optional"
    )


def test_intent_oneloop_three_stage_chain_has_amp_reduced(skill_text: str) -> None:
    """amp_reduced.m must be named as the Stage 2→Stage 3 hand-off file."""
    intent4_start = skill_text.find("### Intent 4")
    assert intent4_start != -1
    intent4_block = skill_text[intent4_start:]
    assert "amp_reduced.m" in intent4_block, (
        "Intent 4 must name 'amp_reduced.m' as the FormCalc→LoopTools hand-off"
    )


def test_intent_oneloop_output_is_scattering_v1(skill_text: str) -> None:
    """LoopTools sigma.json output must be labeled as scattering/v1 schema."""
    intent4_start = skill_text.find("### Intent 4")
    assert intent4_start != -1
    # scattering/v1 appears in the intent 4 block or in the data-flow diagram
    fragment = skill_text[intent4_start:]
    assert "scattering/v1" in fragment, (
        "Intent 4 must reference 'scattering/v1' schema for sigma.json output"
    )


def test_intent_oneloop_gamma5_gate_documented(skill_text: str) -> None:
    """The γ₅ gate and FORMCALC_G5_SCHEME_REQUIRED must be documented."""
    intent4_start = skill_text.find("### Intent 4")
    assert intent4_start != -1
    intent4_block = skill_text[intent4_start:]
    assert "FORMCALC_G5_SCHEME_REQUIRED" in intent4_block, (
        "Intent 4 must document the FORMCALC_G5_SCHEME_REQUIRED γ₅ gate"
    )


# ---------------------------------------------------------------------------
# Data-flow diagram correctness
# ---------------------------------------------------------------------------


def test_dataflow_diagram_mentions_all_constraint_skills(skill_text: str) -> None:
    """The data-flow diagram must mention the constraint sub-skills."""
    diagram_start = skill_text.find("## Data-flow diagram")
    assert diagram_start != -1
    diagram_block = skill_text[diagram_start:]
    for skill in (
        "/micromegas",
        "/ddcalc",
        "/higgstools",
        "/feynarts",
        "/formcalc",
    ):
        assert skill in diagram_block, (
            f"Data-flow diagram must mention '{skill}'"
        )


def test_dataflow_diagram_mentions_scattering_schema(skill_text: str) -> None:
    """Data-flow diagram must reference scattering.schema.json."""
    diagram_start = skill_text.find("## Data-flow diagram")
    assert diagram_start != -1
    diagram_block = skill_text[diagram_start:]
    assert "scattering.schema.json" in diagram_block, (
        "Data-flow diagram must reference 'scattering.schema.json'"
    )


# ---------------------------------------------------------------------------
# Linkage table completeness
# ---------------------------------------------------------------------------


def test_linkage_table_includes_constraint_skills(skill_text: str) -> None:
    """The Linkage table must reference the constraint skills."""
    linkage_start = skill_text.find("## Linkage")
    assert linkage_start != -1
    linkage_block = skill_text[linkage_start:]
    for entry in (
        "micromegas/SKILL.md",
        "ddcalc/SKILL.md",
        "higgstools/SKILL.md",
        "feynarts/SKILL.md",
        "formcalc/SKILL.md",
    ):
        assert entry in linkage_block, (
            f"Linkage table must include '{entry}'"
        )


def test_linkage_table_includes_scattering_schema(skill_text: str) -> None:
    """The Linkage table must reference scattering.schema.json."""
    linkage_start = skill_text.find("## Linkage")
    assert linkage_start != -1
    linkage_block = skill_text[linkage_start:]
    assert "scattering.schema.json" in linkage_block


# ---------------------------------------------------------------------------
# Regression guard — flag-name correctness
# ---------------------------------------------------------------------------


def test_no_dm_candidate_flag(skill_text: str) -> None:
    """Intent 1 must NOT use the non-existent --dm-candidate flag.

    The real /micromegas relic CLI exposes --dm-pdg and --auto-detect.
    --dm-candidate does not exist in run_micromegas.py and will cause
    argparse to error at runtime. This regression guard prevents the
    wrong flag name from re-appearing in the orchestrator.
    """
    assert "--dm-candidate" not in skill_text, (
        "SKILL.md must not contain '--dm-candidate'; use '--dm-pdg <id>' or "
        "'--auto-detect' (or rely on spec.yaml dm_candidate.pdg). "
        "See plugins/hep-ph-toolkit/skills/micromegas/scripts/run_micromegas.py."
    )


def test_intent_relic_density_uses_correct_dm_flag(skill_text: str) -> None:
    """Intent 1 must reference a real /micromegas relic DM flag.

    One of --dm-pdg, --auto-detect, or dm_candidate (spec.yaml key) must
    appear in the relic section so downstream agents know how to pass the
    DM candidate.
    """
    intent1_start = skill_text.find("### Intent 1")
    intent2_start = skill_text.find("### Intent 2")
    assert intent1_start != -1 and intent2_start != -1
    intent1_block = skill_text[intent1_start:intent2_start]
    has_valid_flag = (
        "--dm-pdg" in intent1_block
        or "--auto-detect" in intent1_block
        or "dm_candidate" in intent1_block
    )
    assert has_valid_flag, (
        "Intent 1 must reference '--dm-pdg', '--auto-detect', or 'dm_candidate' "
        "(spec.yaml key) — not '--dm-candidate'."
    )
