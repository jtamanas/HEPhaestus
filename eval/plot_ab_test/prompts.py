"""
Build the two prompt variants for each A/B test case.

- with_skills: includes design system, style sheet, helper module, and skill excerpt
- without_skills: generic "make a publication-quality plot" instruction
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # eval/plot_ab_test -> repo root

# Skill files mapped by category
_SKILL_FILES = {
    "hep-plot": REPO_ROOT / "plugins/hep-ph-toolkit/skills/hep-plot/SKILL.md",
    "exclusion-contour": REPO_ROOT / "plugins/hep-ph-toolkit/skills/exclusion-contour/SKILL.md",
    "theory-data-comparison": REPO_ROOT / "plugins/hep-ph-toolkit/skills/theory-data-comparison/SKILL.md",
}

# Style sheet mapped by category
_STYLE_SHEETS = {
    "hep-plot": REPO_ROOT / "styles/hephaestus-analytic.mplstyle",
    "exclusion-contour": REPO_ROOT / "styles/hephaestus-slate.mplstyle",
    "theory-data-comparison": REPO_ROOT / "styles/hephaestus-analytic.mplstyle",
}

_DESIGN_SYSTEM = REPO_ROOT / "docs/design-system.md"
_HELPER_MODULE = REPO_ROOT / "styles/hep_ph_style.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_style_section(skill_text: str) -> str:
    """Extract from '## Style' onward, excluding '## Style Rules' (legacy section).

    Falls back to full text if section not found.
    """
    # Match "## Style\n" exactly — not "## Style Rules" which has legacy defaults
    marker = "## Style\n"
    idx = skill_text.find(marker)
    if idx == -1:
        return skill_text
    return skill_text[idx:]


def build_with_skills_prompt(
    case_description: str,
    skill_category: str,
    data_path: str,
    output_dir: str,
) -> str:
    """Build the prompt for the agent WITH design skills."""
    skill_text = _read(_SKILL_FILES[skill_category])

    # For hep-plot, extract only the Style section to avoid conflicting legacy defaults
    if skill_category == "hep-plot":
        skill_excerpt = _extract_style_section(skill_text)
    else:
        skill_excerpt = skill_text

    style_sheet = _read(_STYLE_SHEETS[skill_category])
    design_system = _read(_DESIGN_SYSTEM)
    helper_module = _read(_HELPER_MODULE)

    style_sheet_name = _STYLE_SHEETS[skill_category].name

    return f"""You are generating a publication-quality plot for a high-energy physics paper.

## Task

{case_description}

The synthetic data is at: {data_path}
Save your final plot as: {output_dir}/plot.png

## Design System

Follow these visual rules exactly:

{design_system}

## Skill Reference

{skill_excerpt}

## Style Sheet

Write this to a local file called `{style_sheet_name}` before using it:

```
{style_sheet}
```

## Helper Module

Write this to a local file called `hep_ph_style.py` before importing it.
IMPORTANT: After writing the file, update the `_STYLE_DIR` variable to point to the current
directory so it can find the `.mplstyle` file you wrote above.

```python
{helper_module}
```

## Instructions

1. First, write the style sheet and helper module as local files
2. In the helper module, change `_STYLE_DIR = Path(__file__).resolve().parent` to point to your working directory (or just use `Path(".")`)
3. Write a Python plotting script that:
   - Loads the data from the .npz file
   - Uses the helper module and style sheet
   - Follows the design system rules exactly (colors, typography, line weights, no gridlines, no legend boxes, direct labels, etc.)
   - Saves the plot as plot.png in the output directory
4. Run the script to generate the plot
5. If there are errors, fix them and re-run

The plot MUST be saved at exactly: {output_dir}/plot.png"""


def build_without_skills_prompt(
    case_description: str,
    data_path: str,
    output_dir: str,
) -> str:
    """Build the prompt for the agent WITHOUT design skills."""
    return f"""You are generating a publication-quality plot for a high-energy physics paper.

## Task

{case_description}

The synthetic data is at: {data_path}
Save your final plot as: {output_dir}/plot.png

## Instructions

Write a Python script that:
1. Loads the data from the .npz file
2. Produces a publication-quality plot suitable for a hep-ph paper
3. Use matplotlib (and mplhep if available)
4. Follow standard HEP plotting conventions
5. Saves the plot as plot.png in the output directory
6. Run the script to generate the plot
7. If there are errors, fix them and re-run

The plot MUST be saved at exactly: {output_dir}/plot.png"""
