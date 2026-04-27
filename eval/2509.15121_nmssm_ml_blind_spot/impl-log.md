# Implementation Log — arXiv:2509.15121

---

## Round-1 (branch `paper-2509.15121`, commit 1a9afd1)

**Date:** 2026-04-18
**Status:** 20/20 pytest pass. Harness load blocked (namespace collision).

### Completed
- All physics modules: `constants.py`, `models/`, `cross_sections/`, `benchmarks/`
- YAML rows: 3 Tier-1, 5 Tier-2, 4 Tier-3
- `eval/harness/refs.py` NMSSM ref_fns (10 functions)
- MadGraph cards and scripts (offline; no cache generated)
- Phase-1 transcription log (`phase1_notes.md`)

### Gate outcomes (Round-1)
| Gate | Result |
|------|--------|
| `pytest benchmarks/test_benchmarks.py` | 20/20 pass |
| Harness tier-1 `--tier 1` | FAIL (ModuleNotFoundError) |
| Harness tier-2 `--tier 2` | FAIL (same root cause) |
| Harness tier-3 `--tier 3` | FAIL (same root cause) |

### Blockers
- **B1 (hard):** `_get_nmssm_modules()` used bare `importlib.import_module("models.*")`,
  colliding with paper-2's `models` package already bound in `sys.modules`.
- **B2 (process):** zero commits on branch before Round-2.

---

## Round-2 (commit e37e62f)

**Date:** 2026-04-18
**Status:** All harness tiers pass. All pytest pass.

### B1 Fix
Replaced `_get_nmssm_modules()` in `eval/harness/refs.py` with `spec_from_file_location`
loading under unique `p5_*` cache keys. Also temporarily swaps `sys.modules["constants"]`
to the NMSSM constants during module loading, then restores it. Fixed two additional
inline bare imports (`from constants import G1_SM, V_H` and `from models.neutralino_spectrum
import neutralino_mass_matrix`) in ref_fns.

### B2 Fix
Committed Round-1 implementation as first commit before applying any R2 changes.

### Gate outcomes (Round-2)
| Gate | Result |
|------|--------|
| `pytest benchmarks/test_benchmarks.py` | 20/20 pass |
| Harness `--tier 1` | 11/11 pass |
| Harness `--tier 2` | 23/23 pass (includes 5 NMSSM rows) |
| Harness `--tier 3` | 13/13 pass (includes 4 NMSSM rows) |
| `python -c "from eval.harness import refs; print('ok')"` | ok |

### Strong concern resolutions
- **S-2 (README missing):** Added `README.md` with "What we compute vs. what we pin"
  table, Phase-1 finding (LHS ~ 3.33 at paper BPs), and implementation notes.
- **N-1 (impl-log missing):** This file.
- **N-2 (deviations undocumented):** Added `impl-deviations.md` covering D1-D5.

### Phase-1 key finding (documented in README.md and test docstrings)
The paper BPs are NOT on the Eq. 7 blind spot at tree level. Measured:
- BP1-3: LHS = 3.33 (not 1.0)
- BP1-3-off: LHS = 2.65 (|LHS-1| = 1.65 < 5 * 2.33, so relational_excess < 0)
- Synthetic 4x4: LHS = 1.000000 (true blind spot, constructed)

This is intentional. The `t3_nmssm_blind_spot_eq7_on_bp1_3` test pins at 3.33 (formula
reproducibility), and `t3_nmssm_blind_spot_eq7_synthetic` is the true blind-spot test.

### Remaining items (non-blocking)
- N-3: test tolerance 1% vs YAML tolerance 0.5% for bp1_3 m_chi1/m_chi3 (documented D5)
- N-4: BP5-2 pytest lacks m_chi2/m_chi3 assertions (symmetry only; YAML grades them)
- N-5: convergence logic duplicated between refs.py and test_synthetic_4x4_limit
- MadGraph5 never run; `t2_nmssm_sigma_prod_bp1_3` row not authored (correct per plan)
