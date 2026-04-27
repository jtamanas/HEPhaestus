# Plot A/B Test Eval Suite

**Date:** 2026-04-16
**Status:** Approved
**Scope:** Re-runnable evaluation suite that A/B tests the hep-ph-agents design system's impact on plot quality

## Motivation

The hep-ph-agents project has a detailed design system (color palettes, typography, line weights, fill opacities, layout rules) and three plotting skills (`hep-plot`, `exclusion-contour`, `theory-data-comparison`) that encode those rules. We need empirical evidence that these skills actually produce better-looking plots compared to an agent working from general knowledge alone.

## Design

### Overview

Two Claude Code agents generate the same plot from the same synthetic data. One agent has access to the design system, style sheets, and plotting skills. The other has only a generic prompt. A human evaluator votes blind on which plot looks better.

### Structure

```
eval/plot_ab_test/
├── README.md                    # How to run, prerequisites, what it tests
├── run_eval.py                  # Orchestrator: data gen → agent spawning → HTML build
├── test_cases.py                # 12 case definitions (data generators + prompts)
├── viewer.html                  # Generated static voting page
├── data/                        # Generated synthetic data (.npz files)
├── outputs/                     # Agent-generated plots
│   └── {case_name}/
│       ├── with_skills.png
│       └── without_skills.png
└── results/                     # Voting results (gitignored)
    └── votes_{timestamp}.json
```

### Test Cases (12 plot types)

Each case provides: a synthetic data generator function, a physics description string, and the skill category it exercises.

| # | Case ID | Physics | Design system rules exercised |
|---|---------|---------|-------------------------------|
| 1 | `z_mass_peak` | Breit-Wigner resonance + flat combinatorial background in μμ invariant mass | 1D histogram, signal/background color assignment |
| 2 | `pt_spectrum` | Steeply falling pT spectrum with power-law tail | Log-scale axes, line weight hierarchy |
| 3 | `stacked_backgrounds` | H→γγ signal peak on γγ, γj, jj backgrounds | Stacked fill colors, ordering, legend placement |
| 4 | `exclusion_contour` | CLs values on (mχ, mmed) grid | Brazil bands, observed/expected limits, fill opacity rules |
| 5 | `theory_data_ratio` | NLO prediction vs binned measurement with uncertainties | Ratio panel, uncertainty bands, error bar conventions |
| 6 | `parameter_scan_2d` | χ² heatmap over (tan β, mA) plane | Colormap choice, contour lines, axis treatment |
| 7 | `running_couplings` | α₁, α₂, α₃ RGE running from MZ to MGUT | Multi-curve escalation rules, log x-axis |
| 8 | `angular_distribution` | dσ/d cos θ for e⁺e⁻→μ⁺μ⁻ | Clean line plot, LaTeX labels, typography |
| 9 | `cross_section_vs_sqrt_s` | σ(pp→tt̄) at multiple √s with theory band | Data points + errors + theory band, wide x range |
| 10 | `missing_et` | MET distribution: W→ℓν signal + QCD/Z backgrounds | Stacked + overlay, log y-axis |
| 11 | `branching_ratios` | BR(H→xx) vs mH for 5-6 SM Higgs channels | Many curves, direct labeling, legend-free design |
| 12 | `multi_panel_comparison` | Same observable at 8 TeV vs 13 TeV | Small multiples, shared axes, panel spacing |

### Data Generation

Each test case function in `test_cases.py` returns:
- A `.npz` file saved to `data/{case_id}.npz` containing numpy arrays
- A `description` string explaining the physics (shared by both agents)
- A `skill_category` string (`hep-plot`, `exclusion-contour`, or `theory-data-comparison`) indicating which skill applies

Data generators use `numpy` with fixed random seeds for reproducibility. The data should look realistic — proper distributions, reasonable axis ranges, physically motivated parameters.

**Pre-processing for complex cases:** The `exclusion_contour` case (case 4) provides pre-interpolated contour coordinates (observed limit x/y, expected limit x/y, +/-1σ and +/-2σ band boundaries) rather than a raw CLs grid. This avoids requiring agents to do scipy interpolation and CLs level-finding, which is too complex for a single-pass budget-limited agent. The agent's job is purely visualization: draw the contours and bands from the provided coordinates.

### Agent Invocation

For each test case, two `claude` CLI subprocesses run in parallel.

Both agents run from isolated temporary directories (under `/tmp`, outside the repo tree) with only the data file copied in. This prevents any filesystem access to the repo's `styles/`, `plugins/`, or `docs/` directories.

**Agent WITH design skills:**
```
claude --print --dangerously-skip-permissions \
  --bare \
  --allowedTools Edit,Write,Bash,Read \
  --max-budget-usd 1.00 \
  -p "{prompt_with_design_context}"
```

The `--bare` flag disables CLAUDE.md auto-discovery and hooks. The design context is injected explicitly into the prompt instead:
- Physics description (same as baseline)
- Path to the synthetic data file
- Full content of the relevant SKILL.md (Style section only — see note on skill conflicts below)
- Full content of `docs/design-system.md`
- Full content of `styles/hep_ph_style.py` (inlined in prompt, with instruction to write it to a local file before importing)
- Full content of the relevant `.mplstyle` file (inlined, with instruction to write locally)
- Instruction: Write a Python script that loads the data from {path} and produces a publication-quality plot following the design system and skill instructions. Save the helper module and style sheet as local files first, then write and run your plotting script. Save the final plot as plot.png in {output_dir}.

**Note on skill file conflicts:** The `hep-plot` SKILL.md has legacy defaults in its top half (8x6 inches, 16pt fonts) that contradict the design system section at the bottom (85mm, 9pt). The prompt must include only the "Style" section (from `## Style` onward) to avoid giving the agent conflicting instructions. The `exclusion-contour` and `theory-data-comparison` skills do not have this conflict.

**Agent WITHOUT design skills:**
```
claude --print --dangerously-skip-permissions \
  --bare \
  --allowedTools Edit,Write,Bash,Read \
  --max-budget-usd 1.00 \
  -p "{prompt_without_design_context}"
```

The `--bare` flag is critical here: without it, `claude` would walk up the directory tree and discover the project's `CLAUDE.md`, which describes the entire design system and plugin marketplace — completely defeating the A/B test.

The prompt includes:
- Physics description (identical)
- Path to the synthetic data file
- Instruction: Write a Python script that loads the data from {path} and produces a publication-quality plot suitable for a hep-ph paper. Use matplotlib and mplhep if available. Save as plot.png in {output_dir}.

**Parallelism:** All 24 agents (12 cases × 2 variants) can be spawned concurrently, bounded by a configurable `--max-parallel` flag (default: 4 agent pairs = 8 concurrent processes).

### HTML Voting Viewer

Generated by `run_eval.py` after all agents complete. Self-contained HTML file (images embedded as base64, no server needed).

**Features:**
- One pair per screen, side-by-side layout
- Left/right assignment randomized per case (seeded per session via `crypto.getRandomValues`)
- Blind labels: "Plot A" / "Plot B" with no indication of which had design skills
- Vote buttons: "Prefer Left" / "Prefer Right" / "Tie"
- Progress bar: "4 / 12 voted"
- Previous / Next navigation to revisit and change votes
- After all 12 voted: results page that unblinds assignments, shows tally, and provides "Download Results JSON" button
- Votes persist in `localStorage`

**Results JSON format:**
```json
{
  "timestamp": "2026-04-16T14:30:00Z",
  "cases": [
    {
      "case_id": "z_mass_peak",
      "design_side": "left",
      "vote": "left",
      "design_won": true
    }
  ],
  "summary": {
    "design_wins": 8,
    "baseline_wins": 2,
    "ties": 2,
    "total": 12
  }
}
```

### Prerequisites

- Python 3.10+ with numpy, scipy, matplotlib
- `claude` CLI installed and authenticated (version with `--bare` and `--max-budget-usd` flags)
- `--dangerously-skip-permissions` must be available (required for unattended agent runs). If your CLI config doesn't support this, use `--permission-mode bypassPermissions` as an alternative.
- Sufficient API credits: ~$24 budget ceiling (12 cases × 2 agents × $1.00 max each). Actual spend will typically be lower.

### Running

```bash
cd eval/plot_ab_test
python run_eval.py              # Run full eval (generate data, spawn agents, build viewer)
python run_eval.py --data-only  # Only generate synthetic data
python run_eval.py --view-only  # Only rebuild/open the viewer (if outputs exist)
python run_eval.py --max-parallel 2  # Limit concurrent agent pairs
```

### What Is NOT in Scope

- Automated scoring (no CLIP, no FID — human judgment only)
- Statistical significance testing (12 cases is enough for a directional signal, not a p-value)
- Comparing different design system variants against each other (this tests design vs. no design)
