"""
test_skill_structure.py — structural assertions for per-model SKILL.md files.

Parametrized over SKILLS = ["singlet-doublet", "2hdm-a", "dark-su3"].
WS5: skip-if-missing guards removed; all three cases run unconditionally.
A missing SKILL.md now causes a test FAILURE, not a skip.

Assertions per skill:
  (a) ## Model metadata YAML block agrees with constraints.yaml models.<id>
      on ALL keys: display, dm_candidates, plot_axes, multi_component,
      multi_component_prereq (if present), time_overrides.
  (b) Step 2 AskUserQuestion JSON parses and has exact ids ['relic','dd','id','collider'],
      allowMultiple: true, required: true.
  (c) Step 3 gate JSONs: blocked-branch ids ['run_ready','back','cancel'],
      ready-branch ids ['go','back','cancel']; both allowMultiple: false, required: true.
  (d) Step 4 relic branch contains exactly 4 prose directives matching
      the regex ^>\\s*Invoke\\s+/[a-z0-9-]+\\b, in order:
      /sarah-build, /spheno-build, /madgraph, /maddm.
  (e) "All-constraints cold total" line value matches
      time_budget.resolve(<id>, all_non_collider).overlap_totals.cold_all within 0.5 hr.
  (f) SKILL.md body contains the literal string "demo_output/<id>/summary.json".

Cross-skill assertions (WS5):
  (g) All three SKILL.md files have the same 7 section headings in the same order.
  (h) Step 2 AskUserQuestion JSON is identical in shape (option ids, allowMultiple,
      required) across all three skills.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest
import yaml

# Ensure _shared/ is importable (conftest.py also does this, but belt-and-suspenders)
_SHARED = pathlib.Path(__file__).parent.parent
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

from time_budget import resolve  # noqa: E402

_SKILLS_DIR = pathlib.Path(__file__).parent.parent.parent
_CONSTRAINTS_YAML = _SHARED / "constraints.yaml"

SKILLS = ["singlet-doublet", "2hdm-a", "dark-su3"]

# ---------------------------------------------------------------------------
# SKILL.md path helpers
# ---------------------------------------------------------------------------

def _skill_md(skill_id: str) -> pathlib.Path:
    return _SKILLS_DIR / skill_id / "SKILL.md"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def constraints_data():
    with open(_CONSTRAINTS_YAML) as fh:
        return yaml.safe_load(fh)


def _load_skill_md(skill_id: str) -> str:
    return _skill_md(skill_id).read_text()


def _extract_model_metadata_yaml(content: str) -> dict:
    """Extract the fenced YAML block under ## Model metadata."""
    # Match ```yaml block that follows "## Model metadata"
    pattern = r'## Model metadata\s*\n+```yaml\n(.*?)```'
    m = re.search(pattern, content, re.DOTALL)
    if m is None:
        raise AssertionError("## Model metadata fenced YAML block not found in SKILL.md")
    return yaml.safe_load(m.group(1))


def _extract_step2_json(content: str) -> dict:
    """Extract the first AskUserQuestion JSON in Step 2."""
    # Find Step 2 section
    step2_match = re.search(r'### Step 2.*?\n(.*?)(?=\n### Step 3)', content, re.DOTALL)
    if step2_match is None:
        raise AssertionError("Step 2 section not found")
    step2_body = step2_match.group(1)
    # Find JSON block within Step 2
    json_match = re.search(r'```json\n(\{.*?\})\n```', step2_body, re.DOTALL)
    if json_match is None:
        raise AssertionError("AskUserQuestion JSON block not found in Step 2")
    return json.loads(json_match.group(1))


def _extract_step3_gate_jsons(content: str) -> tuple[dict, dict]:
    """Extract both Step 3 gate JSON blocks: (blocked_branch, ready_branch)."""
    step3_match = re.search(r'### Step 3.*?\n(.*?)(?=\n### Step 4)', content, re.DOTALL)
    if step3_match is None:
        raise AssertionError("Step 3 section not found")
    step3_body = step3_match.group(1)
    json_blocks = re.findall(r'```json\n(\{.*?\})\n```', step3_body, re.DOTALL)
    if len(json_blocks) < 2:
        raise AssertionError(f"Expected 2 JSON blocks in Step 3, found {len(json_blocks)}")
    return json.loads(json_blocks[0]), json.loads(json_blocks[1])


def _extract_step4_relic_prose_directives(content: str) -> list[str]:
    """Extract prose directives from the Step 4 relic branch."""
    # Find Step 4 section
    step4_match = re.search(r'### Step 4.*?\n(.*?)(?=\n## Error paths|\Z)', content, re.DOTALL)
    if step4_match is None:
        raise AssertionError("Step 4 section not found")
    step4_body = step4_match.group(1)
    pattern = r'^>\s*Invoke\s+/[a-z0-9-]+'
    matches = re.findall(pattern, step4_body, re.MULTILINE)
    return matches


def _extract_skill_names_from_directives(directives: list[str]) -> list[str]:
    """Extract the skill name (e.g., 'sarah-build') from each prose directive."""
    names = []
    for d in directives:
        m = re.search(r'/([a-z0-9-]+)', d)
        if m:
            names.append(m.group(1))
    return names


def _extract_cold_total_line(content: str) -> tuple[float, float]:
    """Extract lo, hi from 'All-constraints cold total (overlap-adjusted): **X–Y hr**'."""
    m = re.search(r'All-constraints cold total.*?\*\*([0-9.]+)[–-]([0-9.]+)\s*hr\*\*', content)
    if m is None:
        raise AssertionError("All-constraints cold total line not found in SKILL.md")
    return float(m.group(1)), float(m.group(2))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSingletDoublet:
    """Structural assertions for singlet-doublet SKILL.md."""

    SKILL_ID = "singlet-doublet"

    @pytest.fixture(scope="class")
    def content(self):
        return _load_skill_md(self.SKILL_ID)

    @pytest.fixture(scope="class")
    def model_meta(self, content):
        return _extract_model_metadata_yaml(content)

    @pytest.fixture(scope="class")
    def constraints_model(self, constraints_data):
        return constraints_data["models"][self.SKILL_ID]

    # (a) Model metadata matches constraints.yaml
    def test_metadata_display(self, model_meta, constraints_model):
        assert model_meta["display"] == constraints_model["display"], (
            f"display mismatch: SKILL.md={model_meta['display']!r} "
            f"vs constraints.yaml={constraints_model['display']!r}"
        )

    def test_metadata_dm_candidates(self, model_meta, constraints_model):
        assert model_meta["dm_candidates"] == constraints_model["dm_candidates"], (
            "dm_candidates mismatch"
        )

    def test_metadata_plot_axes(self, model_meta, constraints_model):
        assert model_meta["plot_axes"] == constraints_model["plot_axes"], (
            "plot_axes mismatch"
        )

    def test_metadata_multi_component(self, model_meta, constraints_model):
        assert model_meta["multi_component"] == constraints_model["multi_component"], (
            "multi_component mismatch"
        )

    def test_metadata_time_overrides(self, model_meta, constraints_model):
        expected = constraints_model.get("time_overrides", {})
        actual = model_meta.get("time_overrides", {})
        assert actual == expected, f"time_overrides mismatch: {actual!r} vs {expected!r}"

    def test_metadata_multi_component_prereq_absent(self, model_meta, constraints_model):
        """singlet-doublet has no multi_component_prereq; must not appear or be null."""
        assert "multi_component_prereq" not in constraints_model or \
               constraints_model.get("multi_component_prereq") is None, \
               "singlet-doublet should not have multi_component_prereq"
        assert "multi_component_prereq" not in model_meta or \
               model_meta.get("multi_component_prereq") is None, \
               "SKILL.md metadata should not have multi_component_prereq for singlet-doublet"

    # (b) Step 2 JSON
    def test_step2_json_option_ids(self, content):
        step2 = _extract_step2_json(content)
        ids = [o["id"] for o in step2["options"]]
        assert ids == ["relic", "dd", "id", "collider"], \
            f"Step 2 option ids: {ids}"

    def test_step2_json_allow_multiple(self, content):
        step2 = _extract_step2_json(content)
        assert step2["allowMultiple"] is True

    def test_step2_json_required(self, content):
        step2 = _extract_step2_json(content)
        assert step2["required"] is True

    # (c) Step 3 gate JSONs
    def test_step3_blocked_branch_ids(self, content):
        blocked, _ready = _extract_step3_gate_jsons(content)
        ids = [o["id"] for o in blocked["options"]]
        assert ids == ["run_ready", "back", "cancel"], \
            f"Blocked-branch option ids: {ids}"

    def test_step3_blocked_branch_flags(self, content):
        blocked, _ready = _extract_step3_gate_jsons(content)
        assert blocked["allowMultiple"] is False
        assert blocked["required"] is True

    def test_step3_ready_branch_ids(self, content):
        _blocked, ready = _extract_step3_gate_jsons(content)
        ids = [o["id"] for o in ready["options"]]
        assert ids == ["go", "back", "cancel"], \
            f"Ready-branch option ids: {ids}"

    def test_step3_ready_branch_flags(self, content):
        _blocked, ready = _extract_step3_gate_jsons(content)
        assert ready["allowMultiple"] is False
        assert ready["required"] is True

    # (e) Cold total line matches time_budget
    def test_cold_total_within_tolerance(self, content):
        lo, hi = _extract_cold_total_line(content)
        report = resolve(self.SKILL_ID, ["relic", "dd", "id"])
        expected_lo, expected_hi = report.overlap_totals.cold_all
        assert abs(lo - expected_lo) <= 0.5, \
            f"cold_all lo mismatch: SKILL.md={lo}, time_budget={expected_lo}"
        assert abs(hi - expected_hi) <= 0.5, \
            f"cold_all hi mismatch: SKILL.md={hi}, time_budget={expected_hi}"

    # (f) summary.json path
    def test_summary_json_path(self, content):
        assert "demo_output/singlet-doublet/summary.json" in content, \
            "SKILL.md body must contain 'demo_output/singlet-doublet/summary.json'"

    # Additional structural checks
    def test_sections_present_and_ordered(self, content):
        """All 7 required sections must exist in order."""
        sections = [
            "# Singlet-Doublet",
            "## When to invoke",
            "## Model metadata",
            "## Constraints and time estimates",
            "## Flow",
            "## Error paths",
            "## File map",
        ]
        positions = []
        for s in sections:
            idx = content.find(s)
            assert idx != -1, f"Section not found: {repr(s)}"
            positions.append(idx)
        assert positions == sorted(positions), \
            "Sections are not in the required order"

    def test_frontmatter_keys(self, content):
        """Frontmatter must have name and description only."""
        fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        assert fm_match is not None, "No frontmatter found"
        fm = yaml.safe_load(fm_match.group(1))
        assert set(fm.keys()) == {"name", "description"}, \
            f"Frontmatter keys: {set(fm.keys())}"
        assert fm["name"] == "singlet-doublet"

    def test_maddm_guidance_keywords(self, content):
        """Step 4 MadDM paragraph must mention Majorana, relic_density, launch, Omega."""
        keywords = ["Majorana", "relic_density", "launch", "Omega"]
        for kw in keywords:
            assert kw in content, f"Step 4 MadDM paragraph missing keyword: {kw!r}"

    def test_plotting_guidance_keywords(self, content):
        """Step 4 plotting block must mention matplotlib, analytic, black."""
        for kw in ["matplotlib", "analytic", "black"]:
            assert kw in content, f"Step 4 plotting block missing keyword: {kw!r}"


class Test2HdmA:
    """Structural assertions for 2hdm-a SKILL.md."""

    SKILL_ID = "2hdm-a"

    @pytest.fixture(scope="class")
    def content(self):
        return _load_skill_md(self.SKILL_ID)

    @pytest.fixture(scope="class")
    def model_meta(self, content):
        return _extract_model_metadata_yaml(content)

    @pytest.fixture(scope="class")
    def constraints_model(self, constraints_data):
        return constraints_data["models"][self.SKILL_ID]

    def test_metadata_display(self, model_meta, constraints_model):
        assert model_meta["display"] == constraints_model["display"]

    def test_metadata_dm_candidates(self, model_meta, constraints_model):
        assert model_meta["dm_candidates"] == constraints_model["dm_candidates"]

    def test_metadata_plot_axes(self, model_meta, constraints_model):
        assert model_meta["plot_axes"] == constraints_model["plot_axes"]

    def test_metadata_multi_component(self, model_meta, constraints_model):
        assert model_meta["multi_component"] == constraints_model["multi_component"]

    def test_metadata_time_overrides(self, model_meta, constraints_model):
        expected = constraints_model.get("time_overrides", {})
        actual = model_meta.get("time_overrides", {})
        assert actual == expected

    def test_step2_json_option_ids(self, content):
        step2 = _extract_step2_json(content)
        ids = [o["id"] for o in step2["options"]]
        assert ids == ["relic", "dd", "id", "collider"]

    def test_step2_json_flags(self, content):
        step2 = _extract_step2_json(content)
        assert step2["allowMultiple"] is True
        assert step2["required"] is True

    def test_step3_blocked_branch_ids(self, content):
        blocked, _ready = _extract_step3_gate_jsons(content)
        ids = [o["id"] for o in blocked["options"]]
        assert ids == ["run_ready", "back", "cancel"]

    def test_step3_ready_branch_ids(self, content):
        _blocked, ready = _extract_step3_gate_jsons(content)
        ids = [o["id"] for o in ready["options"]]
        assert ids == ["go", "back", "cancel"]

    def test_step4_relic_branch_mentions_chain_in_order(self, content):
        """2hdm-a Step 4 uses the hand-crafted SARAH fixture (no /sarah-build,
        no /spheno-build for relic), so the narrative under the
        '#### Step 4 — Relic density branch' subsection is SARAH → MadGraph
        → MadDM.  Assert these tool references appear in that order, scoped
        to the relic-density subsection only."""
        relic_match = re.search(
            r'####\s+Step 4\s+[—-]\s+Relic density branch'
            r'(.*?)(?=\n####\s+Step 4|\n##\s+Error paths|\Z)',
            content, re.DOTALL,
        )
        assert relic_match is not None, "Step 4 relic-density subsection not found"
        body = relic_match.group(1)
        markers = ["SARAH", "MadGraph", "MadDM"]
        positions = []
        for m in markers:
            idx = body.find(m)
            assert idx != -1, f"Step 4 relic branch missing tool marker {m!r}"
            positions.append(idx)
        assert positions == sorted(positions), (
            f"Step 4 relic branch tool markers out of order: "
            f"{list(zip(markers, positions))}"
        )

    def test_cold_total_within_tolerance(self, content):
        lo, hi = _extract_cold_total_line(content)
        report = resolve(self.SKILL_ID, ["relic", "dd", "id"])
        expected_lo, expected_hi = report.overlap_totals.cold_all
        assert abs(lo - expected_lo) <= 0.5
        assert abs(hi - expected_hi) <= 0.5

    def test_summary_json_path(self, content):
        assert "demo_output/2hdm-a/summary.json" in content

    def test_physics_adaptation_words(self, content):
        """WS3 physics adaptation: required words must appear."""
        for word in ["Dirac", "CP-odd", "loop-only"]:
            assert word in content, f"Missing physics adaptation word: {word!r}"
        assert re.search(r'a-resonance|a resonance', content), \
            "Missing 'a-resonance' in 2hdm-a SKILL.md"
        assert re.search(r'tan.?β|tan_beta|tan beta', content), \
            "Missing 'tan β' in 2hdm-a SKILL.md"


class TestDarkSU3:
    """Structural assertions for dark-su3 SKILL.md."""

    SKILL_ID = "dark-su3"

    @pytest.fixture(scope="class")
    def content(self):
        return _load_skill_md(self.SKILL_ID)

    @pytest.fixture(scope="class")
    def model_meta(self, content):
        return _extract_model_metadata_yaml(content)

    @pytest.fixture(scope="class")
    def constraints_model(self, constraints_data):
        return constraints_data["models"][self.SKILL_ID]

    def test_metadata_display(self, model_meta, constraints_model):
        assert model_meta["display"] == constraints_model["display"]

    def test_metadata_dm_candidates(self, model_meta, constraints_model):
        assert model_meta["dm_candidates"] == constraints_model["dm_candidates"]

    def test_metadata_plot_axes(self, model_meta, constraints_model):
        assert model_meta["plot_axes"] == constraints_model["plot_axes"]

    def test_metadata_multi_component(self, model_meta, constraints_model):
        assert model_meta["multi_component"] is True
        assert constraints_model["multi_component"] is True

    def test_metadata_multi_component_prereq(self, model_meta, constraints_model):
        assert model_meta.get("multi_component_prereq") == "dark-matter-constraints"
        assert constraints_model.get("multi_component_prereq") == "dark-matter-constraints"

    def test_metadata_time_overrides(self, model_meta, constraints_model):
        expected = constraints_model.get("time_overrides", {})
        actual = model_meta.get("time_overrides", {})
        assert actual == expected

    def test_step2_json_option_ids(self, content):
        step2 = _extract_step2_json(content)
        ids = [o["id"] for o in step2["options"]]
        assert ids == ["relic", "dd", "id", "collider"]

    def test_step2_json_flags(self, content):
        step2 = _extract_step2_json(content)
        assert step2["allowMultiple"] is True
        assert step2["required"] is True

    def test_step3_blocked_branch_ids(self, content):
        blocked, _ready = _extract_step3_gate_jsons(content)
        ids = [o["id"] for o in blocked["options"]]
        assert ids == ["run_ready", "back", "cancel"]

    def test_summary_json_path(self, content):
        assert "demo_output/dark-su3/summary.json" in content

    def test_physics_adaptation_words(self, content):
        """WS4 physics adaptation: required words must appear."""
        for phrase in ["scalar dark pion", "vector dark meson", "confining", "multi-component"]:
            assert phrase in content, f"Missing physics adaptation word: {phrase!r}"
        assert re.search(r'blind.?spot', content, re.IGNORECASE), \
            "Missing 'blind spot' in dark-su3 SKILL.md"

    def test_dark_matter_constraints_in_chains(self, content):
        """dark-matter-constraints must appear at least 3 times (one per constraint chain)."""
        count = content.count("dark-matter-constraints")
        assert count >= 3, \
            f"Expected ≥3 occurrences of 'dark-matter-constraints', found {count}"

    def test_no_run_ready_zero_constraints_message(self, content):
        """Blocked-UX message must be present."""
        assert "No selected constraints are currently runnable" in content


# ---------------------------------------------------------------------------
# Cross-skill assertions (WS5) — assert properties that must hold uniformly
# across ALL three per-model SKILL.md files.
# ---------------------------------------------------------------------------

_EXPECTED_SECTIONS = [
    "## When to invoke",
    "## Model metadata",
    "## Constraints and time estimates",
    "## Flow",
    "## Error paths",
    "## File map",
]


def _section_order(content: str) -> list[int]:
    """Return the character positions of each expected section header."""
    return [content.find(s) for s in _EXPECTED_SECTIONS]


def _step2_shape(content: str) -> dict:
    """Return a normalised descriptor of Step 2 JSON shape (ids, flags)."""
    data = _extract_step2_json(content)
    return {
        "option_ids": [o["id"] for o in data["options"]],
        "allowMultiple": data["allowMultiple"],
        "required": data["required"],
    }


class TestCrossSkill:
    """
    Cross-skill invariants: properties that must be identical across all three
    per-model SKILL.md files.  A failure here means a drift was introduced
    that is not permitted by the plan.
    """

    @pytest.fixture(scope="class")
    def contents(self):
        return {sid: _load_skill_md(sid) for sid in SKILLS}

    def test_all_skill_md_files_exist(self):
        """All three SKILL.md files must exist (no skip-if-missing in WS5)."""
        for sid in SKILLS:
            path = _skill_md(sid)
            assert path.exists(), (
                f"Missing SKILL.md for {sid!r}: {path}. "
                "WS5 requires all three files to be present."
            )

    def test_all_skills_have_same_six_section_headings(self, contents):
        """(g) All three files share the same 6 required section headings."""
        for sid, content in contents.items():
            for heading in _EXPECTED_SECTIONS:
                assert heading in content, (
                    f"{sid}: missing required section heading {heading!r}"
                )

    def test_all_skills_have_sections_in_same_order(self, contents):
        """(g) Section headings appear in the same relative order in each file."""
        ref_id = "singlet-doublet"
        ref_positions = _section_order(contents[ref_id])
        # Verify reference itself is sane (ascending positions)
        assert ref_positions == sorted(ref_positions), (
            f"Sections out of order in {ref_id}"
        )
        for sid in ["2hdm-a", "dark-su3"]:
            positions = _section_order(contents[sid])
            assert positions == sorted(positions), (
                f"Sections out of order in {sid}: {list(zip(_EXPECTED_SECTIONS, positions))}"
            )

    def test_step2_json_identical_shape_across_skills(self, contents):
        """(h) Step 2 AskUserQuestion JSON has the same option ids and flags in all three skills."""
        shapes = {sid: _step2_shape(content) for sid, content in contents.items()}
        ref = shapes["singlet-doublet"]
        expected_ids = ["relic", "dd", "id", "collider"]
        assert ref["option_ids"] == expected_ids, (
            f"singlet-doublet Step 2 ids: {ref['option_ids']}"
        )
        for sid in ["2hdm-a", "dark-su3"]:
            assert shapes[sid] == ref, (
                f"{sid} Step 2 shape differs from singlet-doublet: "
                f"{shapes[sid]} vs {ref}"
            )
