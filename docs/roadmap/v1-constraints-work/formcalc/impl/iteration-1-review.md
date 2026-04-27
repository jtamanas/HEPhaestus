# `/formcalc` + `/formcalc-install` — Iteration-1 Skeptical Review

**Reviewer:** Claude Opus 4.7 (audit role)
**Date:** 2026-04-19
**Base:** `workstream-feyndiag-feynarts` → **HEAD:** `bbe140d`
**Tests at HEAD:** `63 passed, 2 skipped in 1.69s` (independently reproduced).

---

## Verdict: **NEEDS_FIXES**

Iteration-1 lands a substantively complete `/formcalc` + `/formcalc-install` pair:
the γ₅ static-check algorithm, FeynArts version gate, and sidecar-conformance
pipeline all match the plan literally, and the Phase-0 contracts (`_common.sh`
exit codes, shared schemas) are consumed as-is. Three issues block "DONE":
(1) the FORM 4.3.1 download URL is a live 404 and the FormCalc 10.0 URL
is also a 404, which will brick `install` on the first real run;
(2) `.build_key` and the sidecar JSON are written via a Python reimplementation
of the tmp+fsync+rename+dir-fsync pattern instead of the Phase-0
`atomic_write.sh` helper the plan explicitly mandates; and
(3) two plan deviations (smoke_test `Time =` assertion demoted to a warning,
C7 integration test always-skipped ungated) are acknowledged by the report
but still leave the installer path under-tested.

---

## Per-area findings

### 1. Commit discipline — CONCERN

`git log --oneline workstream-feyndiag-feynarts..HEAD` returns **10** commits
(1 report + 9 implementation): `1e51dbb, 89a2dff, cdedf9b, a86526a, cef0f4d,
e950c28, b5e511d, 8a72a97, d5ecd92, bbe140d`. Plan §2 asked for ~12–14.
Report §"Deviations" #2 explicitly acknowledges collapsing C8–C11 (four
sub-steps) into `b5e511d`. Spot-checked two intermediate commits:
- `89a2dff` (C2): adds SKILL.md + `install_formcalc.sh` + `skill_env.yaml` only — green.
- `cef0f4d` (C5): adds `build_looptools.sh` + tests only — green.

All commits prefixed `W12-fC:` per plan. **PASS** on prefix; **CONCERN** on
granularity — the C8–C11 megacommit is 21 files / 2033 insertions, which
hurts bisectability even though the resulting tree is correct.

### 2. File manifest — PASS

All paths from plan §1.1 and §1.2 exist with sensible content:
`/formcalc-install/{SKILL.md, skill_env.yaml, scripts/{install_formcalc.sh,
install_formcalc_full.sh, build_form.sh, build_looptools.sh,
probe_formcalc.wls, smoke_test.wls}, tests/…}`;
`/formcalc/{SKILL.md, scripts/{run_formcalc.py, gamma5_static_check.wls,
run_calcfeynamp.wls, prepare_kinematics.py, parse_summary.py,
write_sidecar.py, cache_key.py}, tests/fixtures/{ee_to_mumu, chiral_amp,
chiral_via_coupling, non_chiral_amp, wrong_version_meta}/…}`.
`skill_env.yaml` pins `formcalc_version: "10.0"`, `form_version: "4.3.1"`,
`looptools_version: "10.0"` — literal match to plan.

### 3. γ₅ static-check algorithm — PASS

`gamma5_static_check.wls` L41–52 implements the exact plan §1.3 structure:

```
chiralHits = Cases[held,
  (ChiralityProjector | gamma5 |
    _Symbol?(Function[s, Context[s] === "System`" && (s === 6 || s === 7)])),
  Infinity];
couplingAxialHits = Cases[held, Mat[DiracChain[6 | 7, ___]], Infinity];
```

No regex-on-text anywhere (`git grep -n 'RegularExpression\|StringMatchQ'
plugins/hep-ph-toolkit/skills/formcalc*` → empty). Dispatcher logic
(`run_gamma5_check`, `run_formcalc.py` L154–184) correctly maps exit 1 →
`FORMCALC_G5_SCHEME_REQUIRED` fatal + exit 1 when `--gamma5` absent.
Three fixtures (`chiral_amp`, `chiral_via_coupling`, `non_chiral_amp`)
are present and drive six unit-test assertions (verified: the `gamma5`
keyword selected 6 tests, all passed).

### 4. FeynArts version gate — PASS

`run_formcalc.py` L38 pins `SUPPORTED_FEYNARTS_VERSIONS = {"3.11"}`,
L121–149 reads `FeynAmpList.meta.json`, emits
`FORMCALC_FEYNARTS_VERSION_INCOMPATIBLE` fatal with `context.found`,
`context.supported`, and a `/feynarts-install` user_instruction when
version is missing or unsupported. `wrong_version_meta/FeynAmpList.meta.json`
fixture with `"feynarts_version":"3.10"` drives a dedicated unit test.

### 5. Sidecar conformance — PASS (with one template nit)

`write_sidecar.py` L23–34 validates via `jsonschema.Draft202012Validator`
against `plugins/shared/schemas/amp_reduced.meta.schema.json`; fatal
`FORMCALC_SIDECAR_INVALID` on any error. I ran a synthetic-sidecar
round-trip (`{pv_heads: "formcalc-native", input_hashes.feynamplist_m:
64×'a'}`) against the shipped Phase-0 schema — **validates**. Emitted
sidecar hardcodes `pv_heads: "formcalc-native"` literal (L418), writes
`input_hashes.feynamplist_m` as a 64-hex sha256 of the raw file bytes
(L392), and writes `input_hashes.processspec_json` as a sha256 of the
canonical JSON (L393–395). Nit: `tests/fixtures/ee_to_mumu/expected_meta.json`
uses `"__TO_BE_COMPUTED__"` placeholders that do **not** match the
schema pattern `^[a-f0-9]{64}$`; the fixture is intentionally a
template (not validated as-is in any test), so this is cosmetic.

### 6. Install paths — PASS

`install_formcalc.sh` L38–39 and `install_formcalc_full.sh` L39–40:
`DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"`,
`INSTALL_ROOT="${DATA_HOME}/hep-ph-agents/formcalc-${FORMCALC_VERSION}"`.
FORM binary path (`build_form.sh` L39–40):
`FORM_DEST_DIR="$INSTALL_ROOT/form/${ARCH}-${OS_TAG}"`, binary at
`$FORM_DEST_DIR/form` — not on `$PATH`. `form_binary` is written into
config by `config_merge` (L188); `run_formcalc.py` L298 treats it as
the sole contract, never reconstructing the path.

### 7. Exit codes — PASS

`_common.sh` L40–41 defines `EXIT_FORM_BUILD=28` and
`EXIT_LOOPTOOLS_BUILD=29` (from Phase-0). `build_form.sh` L54 uses the
sourced variable directly; same for `build_looptools.sh` L40. No
re-definition in the workstream tree (verified by grep). No reuse of
`EXIT_SPHENO_MAKE=23`.

### 8. Cache key & atomicity — **MIXED (one FAIL, one PASS)**

**PASS:** `cache_key.py` `compute()` folds all 7 inputs (SHA256 of
FeynAmpList bytes, canonical JSON of ProcessSpec, `--reg`, `--gamma5`
or `"none"`, three tool versions) into a single SHA256 with `\x00`
separators. `_cache_hit()` (L218–228) correctly requires
`amp_reduced.m` + `amp_reduced.meta.json` + `.build_key` all to exist;
`test_cache_atomic.py::test_cache_hit_requires_all_three` and
`test_build_key_written_last_semantics` both pass (delete `amp_reduced.m`
with `.build_key` in place → miss).

**FAIL:** Plan §1.3 mandates: "`.build_key` is written via the Phase-0
`atomic_write.sh` helper (tmp + `fsync` + `rename` + dir-fsync)."
Instead, `run_formcalc.py` L455–480 defines
`_write_build_key_atomic()` — a Python reimplementation of the same
pattern. `write_sidecar.py` L55–82 does the same with
`_write_atomic()`. `git grep atomic_write plugins/feynman-diagrams/
skills/formcalc/scripts/*.py` → only one docstring comment, never a
call. The Phase-0 `atomic_write.sh` is loaded inside the shell installer
scripts but never invoked from the Python side.

This is a plan-contract violation even if the pattern is semantically
equivalent: (a) it duplicates the fsync discipline that Phase-0
centralised, (b) any future fix to `atomic_write.sh` (e.g. Windows
handling) must now be mirrored in two Python call-sites, and (c) the
report checklist marks this PASS with the misleading evidence
"`_write_build_key_atomic` in `run_formcalc.py` L470-490" — which
proves the reimplementation, not the plan compliance.

### 9. Apple Silicon branch — PASS

`build_looptools.sh` L44 sets `ARCH="$(uname -m)"`; L50 gates an
`arm64` branch that iterates `gcc@{13,14,15}` via `brew --prefix`
(L55–63), falls back to plain `brew --prefix gcc` (L64–69), probes
`-print-file-name=libquadmath.dylib` (L79), and on failure sets
`LOOPTOOLS_QUAD="false"` + `EXTRA_CONFIGURE_FLAGS="--without-quad"`
(L89–93). `config_merge` writes `looptools_quad` into config (L192).
Matches the plan verbatim.

### 10. QED golden — PASS (but gated — not executed)

`test_ee_to_mumu_golden.py` L94–117 writes a Wolfram helper that
computes `1/4 * Total[Flatten[{Conjugate[amp] * amp}]]`, applies
`{EL^4 -> e^4, EL^2 -> e^2, ME -> 0, MU -> 0}`, `FullSimplify` with
`Assumptions -> {Element[costh, Reals]}`, then asserts
`PossibleZeroQ[msq3 - e^4 (1 + costh^2)]`. Negative control at L119–140
re-checks against `(1 + costh)^2` and asserts **failure**. Both
pytest-skip under current CI gating; cannot execute without
`HEPPH_RUN_WOLFRAM_TESTS=1 && HEPPH_RUN_NETWORK_TESTS=1`, matching plan
§3.3. The fixture `ee_to_mumu/{FeynAmpList.m, FeynAmpList.meta.json,
ProcessSpec.json, expected_meta.json}` is committed.

### 11. v1 scope (no Fortran emission) — PASS

`git grep 'WriteSquaredME\|FortranRun' plugins/feynman-diagrams/
skills/formcalc*` → **no hits at all** (not even in documentation).

### 12. No `reference_only` / analytic fallback — PASS

`git grep 'reference_only\|HEPPH_ALLOW_REFERENCE\|analytic_fallback'`
returns 2 hits: `test_install_unit.py:261` (a comment naming the
blocker-schema variants) and `SKILL.md:127` (a section titled "No
`reference_only` fallback" explicitly forbidding the behaviour). Zero
in live code.

### 13. Integration gating — PASS

`test_ee_to_mumu_golden.py` L34–36 gates on
`HEPPH_RUN_WOLFRAM_TESTS=1 && HEPPH_RUN_NETWORK_TESTS=1`;
`test_install_integration.py` gates on `HEPPH_RUN_NETWORK_TESTS=1`.
With neither env var set, 63 tests pass and 2 skip — matching report.

### 14. Plugin.json + marketplace — PASS

`plugins/feynman-diagrams/.claude-plugin/plugin.json` is valid JSON,
version `0.3.0`, skills list = `[draw-feynman, amplitude-calc,
feynarts-install, feynarts, formcalc-install, formcalc]`. Pre-existing
skills preserved. `.claude-plugin/marketplace.json` L13 bumps
`feynman-diagrams` to `0.3.0` with an updated description naming the
new skills.

### 15. Test counts — PASS

Independently reproduced:
`$ python3 -m pytest plugins/hep-ph-toolkit/skills/formcalc
plugins/hep-ph-toolkit/skills/formcalc-install -q` → `63 passed,
2 skipped in 1.69s`. Report claims `63 passed, 2 skipped in 1.89s`.
Match.

### 16. Non-goal drift — PASS

`git diff workstream-feyndiag-feynarts..HEAD -- plugins/model-building/
plugins/shared/ plugins/hep-ph-toolkit/skills/feynarts
plugins/hep-ph-toolkit/skills/amplitude-calc
plugins/hep-ph-toolkit/skills/draw-feynman` → empty. No unauthorised
edits outside the two new skill directories and the two manifest files.

### 17. Reviewer risks (from report) — **MIXED**

- **FORM 4.3.1 URL — FAIL.** The pinned URL is
  `https://www.nikhef.nl/~form/maindir/binaries/unix/v4.3.1/form-4.3.1.tar.gz`
  (build_form.sh L44). I ran `curl -sI` against it — **HTTP/2 404**.
  The report flagged this as a risk but shipped the URL anyway. The
  `binaries/unix/v4.3.1/` path does not exist on the NIKHEF server.
  Worse, the plan said "ships a generated configure" which implies the
  *source* tarball; the current URL pattern targets `binaries/unix/`
  which is conceptually wrong even if it resolved.

- **FormCalc 10.0 URL — FAIL.** `install_formcalc_full.sh` L43:
  `FORMCALC_URL="https://www.feynarts.de/formcalc/FormCalc-${FORMCALC_VERSION}.tar.gz"`.
  I ran `curl -sIL` — redirects to `https://feynarts.de/formcalc/
  FormCalc-10.0.tar.gz` which returns **HTTP 404**. The report did
  **not** flag this URL. First `install` run will fatal at
  `download_with_retry` with a generic DOWNLOAD_FAILED, never
  reaching `verify_checksum`.

- **LoopTools source subdir — CONCERN but acceptable.** `install_formcalc_full.sh`
  L141–149 searches three candidates
  (`$FORMCALC_SRC_DIR/LoopTools`, lowercase variant, glob) and falls
  back to a warn-skip path if none match. No hard pin. This is more
  robust than a pinned constant; the report's risk framing is
  overblown.

- **`write_sidecar.py` imports `emit_blocker` from `run_formcalc.py` —
  CONCERN (style, not correctness).** L42:
  `from scripts.run_formcalc import emit_blocker`. Because
  `run_formcalc.py` has no import-time side effects beyond module-level
  constants, re-importing it does not trigger the CLI. However, this
  creates a semantic coupling that breaks if `run_formcalc.py` ever
  gains a module-level `argparse` call or similar. A trivial refactor
  would lift `emit_blocker` into `scripts/blocker.py`. Not a v1 blocker.

---

## Required fixes (before "DONE")

1. **Replace both download URLs with verified live endpoints.**
   `curl -sI` must return HTTP 200. Pin the resulting SHA256 at the
   same time and flip `skill_env.yaml` `formcalc_sha256`/`form_sha256`
   off `"TODO"`. Add a CI-gated probe (inside
   `test_install_integration.py` under `HEPPH_RUN_NETWORK_TESTS=1`)
   that issues a HEAD against both URLs so future URL drift is caught.
2. **Route `.build_key` and `amp_reduced.meta.json` through
   `plugins/shared/install-helpers/atomic_write.sh`.** Either shell out
   to `atomic_write_stdin` via `subprocess.run(["bash", "-c", "..."],
   input=...)`, or add a thin Python wrapper in
   `plugins/shared/install-helpers/` that imports the same logic so
   both shell and Python installers converge on one implementation.
   The current Python reimplementation is a plan-contract violation
   even though the semantics are equivalent.
3. **Update the report checklist** so the `.build_key` row honestly
   records "CONCERN: Python reimplementation, not the Phase-0 shell
   helper" rather than PASS.

## Nice-to-haves

- Lift `emit_blocker` into a shared helper module to eliminate the
  `write_sidecar → run_formcalc` import cycle.
- The C8–C11 megacommit (`b5e511d`, 21 files / 2033 insertions) is hard
  to bisect. Future iterations should split cache_key, kinematics,
  gamma5 gate, and driver/sidecar into separate commits as the plan
  originally specified.
- The smoke_test `Time =` downgrade from fatal to warn (report
  deviation #3) is pragmatic for tree-level, but the plan's original
  assertion was stronger. Consider adding an explicit `--expect-form`
  flag so the loop-level install path can still enforce it.
- `FORMCALC_URL` in `install_formcalc.sh` (L42) and
  `install_formcalc_full.sh` (L43) are duplicated — lift to a single
  sourced `_urls.sh` so both scripts can't drift.

## Re-verification requested

After fixes 1–3 above, please rerun and attach:

- `curl -sI <FORM_URL>` and `curl -sI <FORMCALC_URL>` showing HTTP 200.
- `git grep -n atomic_write plugins/hep-ph-toolkit/skills/formcalc*`
  showing at least one real call-site (not a comment) per atomic write.
- `pytest -q` showing 63+ passed still green.
- An updated `iteration-1-impl.md` with the `.build_key` row corrected.

Once those are in place, this workstream is ready to merge into
`workstream-feyndiag-feynarts`.

---

**Word count:** ~1580.
