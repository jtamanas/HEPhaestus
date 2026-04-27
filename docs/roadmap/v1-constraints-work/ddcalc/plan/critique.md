# `/ddcalc` plan critique (SKEPTICAL PLAN CRITIC)

Reviewer: skeptical-critic agent
Date: 2026-04-19
Inputs reviewed: `plan/draft.md`, `brainstorm/final.md`, `CLAUDE.md`,
`plugins/hep-ph-toolkit/skills/spheno-build/`,
`plugins/shared/install-helpers/_common.sh`, sibling
`/micromegas` + `/higgstools` plan drafts, sibling `/micromegas` +
`/formcalc` brainstorm finals.

Format: **quote → counter → synthesizer-action.** Findings are ordered by
severity; first five are blockers.

---

## 1. Overlay-patch authoring is not actually feasible from the plan alone (BLOCKER)

**Quote (draft §2 `/ddcalc-install`):**
> "`overlays/lz_xenonnt_pandax4t_2024/patches/LZ_WS2024.patch` — Fortran module
> adding LZ 2024 WS exposure + efficiency constructor. **Stub in this
> workstream; real content authored in overlay-publication PR per
> brainstorm §3.**"

And step 7:
> "Overlay manifest remains a stub until the external overlay-publication PR
> lands; the plumbing must be merge-ready without the Fortran content."

**Counter.** The plan nowhere demonstrates that *anyone* has inspected
DDCalc 2.2.0's `src/experiments/` layout. `git apply --3way` requires a patch
authored against a specific file tree. The brainstorm's "Option (a)" ruling
assumes LZ-like constructors can be plugged in as new source modules rather
than as edits to existing ones — this is an unverified architectural
assumption about someone else's Fortran codebase. If DDCalc's experiment
registration is table-driven through a central dispatcher (plausible: most
likelihood frameworks work this way), then **every overlay patch must also
edit that central file**, which means patch conflicts between overlays are
guaranteed and `git apply --3way` will routinely fail. The plan gates this as
`DDCALC_OVERLAY_APPLY_FAILED` fatal, but there is no fallback plan and no
"run DDCalc's build first, inspect, then author patches" step.

Additionally: step 1 (planning-phase verifications) lists six items but does
**not** include "clone DDCalc, build it, inspect `src/experiments/`, confirm
experiment registration mechanism." This is the most fundamental open
question and it is missing from the gating list.

**Synthesizer action.**
- Add planning-phase verification item 7: *"Clone DDCalc v2.2.0; build
  locally; enumerate `src/experiments/` file tree; identify experiment
  registration mechanism (central dispatcher vs drop-in module); record
  findings in `plan/verifications.md` §overlay-feasibility."*
- Gate step 7 (implement overlay) on item 7, not on the overlay-publication
  PR. If registration is central-dispatcher, rewrite the overlay design to
  "patch dispatcher + add module," not "add module only."
- Add a decision branch: if verification shows `git apply --3way` is
  structurally fragile, downgrade v1 to **native experiments only** and
  document the overlay mechanism as v1.1 contingent on upstream collaboration.
  The brainstorm §3 escape hatch already permits this; the plan should too.

---

## 2. `HEPPH_DDCALC_URL` probe is not a blocking step (BLOCKER)

**Quote (draft §1, "Planning-phase resolutions"):**
> "1. Canonical DDCalc URL verified (`DDCALC_UPSTREAM_UNVERIFIED` cleared)."

And §5:
> "`HEPPH_DDCALC_URL` points at the verified canonical upstream, not a
> personal fork."

**Counter.** The plan says "verify" but never specifies *what command proves
it* and never specifies *what the implementer does if the URL is down at
verification time.* The `/formcalc` brainstorm models this correctly
(probe chain: HEPForge → GitHub release → archive.org) and emits a fatal
if all three fail. The `/ddcalc` plan has no probe chain, no mirror list,
no fallback. If gitlab.com/ddcalc/ddcalc is unreachable the day the
implementer starts, the workstream stalls silently.

**Synthesizer action.**
- Add probe chain to `skill_env.yaml`: primary
  `https://gitlab.com/ddcalc/ddcalc/-/archive/v2.2.0/ddcalc-v2.2.0.tar.gz`;
  secondary HEPForge mirror; tertiary archive.org snapshot. Spec the
  resolution rule: first HEAD 200 wins, record in `ddcalc_upstream_url`.
- Add the verification command explicitly:
  `curl -sI "$HEPPH_DDCALC_URL" | head -1 | grep -q '200'` and commit its
  output into `plan/verifications.md`.
- If all probes fail, block on `DDCALC_UPSTREAM_UNREACHABLE` fatal and
  halt the workstream — do not fall through to a stale pin.

---

## 3. SHA256 computation and upstream-bump recovery unspecified (BLOCKER)

**Quote (brainstorm §1):**
> "Tarball `DDCalc-2.2.0.tar.gz`; SHA256 MUST be a real value before merge.
> Authoring path: planning-phase implementer fetches once, records sha256
> in `skill_env.yaml`, commits."

**Counter.** "Fetches once" is not a command. `_common.sh` line 81–84 shows
the repo's checksum logic uses `sha256sum || shasum -a 256`. The plan should
specify the exact one-liner for the implementer. More importantly, the plan
doesn't say what happens if the upstream tarball gets re-rolled (tag moves,
or gitlab re-generates the archive tarball with different timestamps —
which gitlab archives routinely do). DDCalc is single-author abandonware-adjacent,
but gitlab auto-archive tarballs are **not byte-stable** across re-downloads
in general. The plan risks shipping a SHA256 that goes stale within days.

**Synthesizer action.**
- Spec the exact command in the verification step:
  `curl -L "$HEPPH_DDCALC_URL" -o /tmp/ddcalc.tgz && shasum -a 256 /tmp/ddcalc.tgz`
  (prefer `shasum -a 256` since macOS is the primary dev target).
- Add a note in `skill_env.yaml`: "If gitlab auto-archive tarballs prove
  unstable, switch to a pinned git-clone-by-commit path and compute SHA
  over a deterministic `git archive` tarball." The clone-by-commit
  approach is what `/spheno-build`-era tools use; model on that.
- Gate: verification step must record both the SHA **and** the date of
  fetch in `plan/verifications.md`; if > 30 days elapse before merge,
  re-verify.

---

## 4. Overlay licence/provenance is underspecified (BLOCKER)

**Quote (draft §2):**
> "`...overlays/lz_xenonnt_pandax4t_2024/NOTICE` — provenance + licence
> statement."

**Counter.** One `NOTICE` file for the whole overlay is wrong. LZ, XENONnT,
and PandaX-4T publish under different arrangements. LZ's public-data
release (PRL 131, 041002, 2023) requires explicit acknowledgment text
verbatim. XENONnT's 2023 limit paper (PRL 131, 041003) has its own citation
norm. PandaX-4T commissioning-run data (PRL 127, 261802, 2021) has a third.
The plan conflates three distinct attribution contracts into a single file.

Checklist item §5 says "O'Hare CSV `NOTICE` names the paper, the figure,
and the licence" — that's the right shape, but the same rigor must apply
per-experiment.

**Synthesizer action.**
- Restructure overlay directory to one NOTICE per experiment:
  `overlays/.../LZ_WS2024.NOTICE`, `.../XENONnT_2023.NOTICE`,
  `.../PandaX_4T_2021.NOTICE`. Each names (a) the primary publication,
  (b) the quoted acknowledgment text, (c) the data-release URL, (d) the
  licence (or "no explicit licence, redistribution as derived product").
- Add a top-level `overlays/.../ATTRIBUTIONS.md` aggregating the three for
  human-readable audit.
- Add verification-checklist item: "every overlay experiment has a NOTICE
  file; no NOTICE omitted; each NOTICE names a specific PRL citation."

---

## 5. Schema collision with `/micromegas` goes the wrong way (BLOCKER)

**Quote (draft §1, coordination rules):**
> "If absent: create minimal viable stubs in this workstream, mark each
> created file with a header comment `# CREATED BY /ddcalc WORKSTREAM — to
> be reconciled with /micromegas before merge`…"

**Counter.** Cross-check against sibling `/micromegas` plan (§2.2):
> "Create only if missing; otherwise load, diff against §2.10 draft, and
> coordinate via a TODO note in the draft. `required` =
> `["m_dm_gev","sigma_si_proton_cm2","source","source_run","dm_candidate"]`."

And against `/formcalc` brainstorm §3, which specifies snake_case +
unit-suffix, `halo: {profile, v0, vesc, rho0}`, **and an optional
`operator_coeffs` block**. The `/ddcalc` brainstorm §2 specifies
`halo: object (optional)` with sub-fields `rho_local_gev_cm3`, `v_0_km_s`,
`v_esc_km_s`. The `/micromegas` brainstorm §3 specifies
`halo: {rho_local_gev_cm3, v_esc_km_s, v_0_km_s}`. The `/formcalc`
brainstorm specifies `halo: {"profile": "SHM", "v0": 238, "vesc": 544,
"rho0": 0.3}`. **All three differ.** This is the exact collision the
coordination gate is supposed to prevent, but none of the three plans
reference the other two's field names byte-for-byte.

Specifically `/ddcalc` verification §5 says:
> "`plugins/shared/schemas/scattering.schema.json` is snake_case, carries
> an optional `nreft_coefficients` key, and field names match the draft
> in `/micromegas` final §3 byte-for-byte."

But `/micromegas` final §3 lists `halo: {rho_local_gev_cm3, v_esc_km_s,
v_0_km_s}` and `/formcalc` final §3 lists `halo: {profile, v0, vesc,
rho0}` — byte-for-byte matching `/micromegas` means breaking `/formcalc`.

**Synthesizer action.**
- Add a new pre-W3 coordination artefact: a 5-line canonical field
  dictionary at `docs/roadmap/v1-constraints-work/_shared/scattering-schema-v1.md`
  enumerating every field's exact snake_case name and type. All three
  plans reference it by path, not by "see sibling §N."
- The `/ddcalc` plan should adopt "first-writer wins, second-writer rebases
  onto the actual committed file" rather than "create stub with header
  comment." Header-comment stubs create merge-time confusion.
- Halo convention: reconcile to one of the three. Recommended:
  `{profile, v0_kms, vesc_kms, rho0_gev_cm3}` (unit-suffixed, matches
  looptools style and ddcalc's `halo_used` output field names).

---

## 6. O'Hare 2021 licence is not actually verified (MAJOR)

**Quote (brainstorm §4):**
> "O'Hare 2021 is available as an opt-in overlay… we **do** vendor
> `neutrino_fog_ohare_2021.csv` with a NOTICE file crediting 'O'Hare, PRL
> 127, 251802 (2021)' and a pointer to the public GitHub notebook
> (MIT-licensed). Before merge, verify the actual licence on the source
> data and the specific curve used in Fig. 6/7 of 2506.19062."

**Counter.** The plan defers licence verification to "planning item 4"
(§1, item 4) but never specifies the URL being verified. The brainstorm
parenthetical says "public GitHub notebook (MIT-licensed)" — which
notebook? O'Hare has multiple repos. PRL publication itself does not
confer a redistribution licence on the paper's figures/data. Without a
specific repo URL (e.g., `github.com/cajohare/NeutrinoFog` and its LICENSE
file verified), "MIT-licensed" is a guess.

**Synthesizer action.**
- Pin the exact repo URL in the plan: `github.com/cajohare/NeutrinoFog`
  (verify this is the canonical one), specific commit SHA, specific CSV
  file path within that repo.
- Verification-step output must include `curl` of the repo's `LICENSE`
  file committed into `plan/verifications.md`.
- If licence is anything other than MIT / CC0 / CC-BY: do not vendor;
  fall back to DDCalc's built-in ν-floor only, and mark `--nu-floor
  ohare_2021` as v1.1.

---

## 7. `HEPPH_ALLOW_REFERENCE` grep check not an executable command (MINOR)

**Quote (draft §5):**
> "Zero references to `HEPPH_ALLOW_REFERENCE` in this workstream."

**Counter.** This is stated as a checklist item but has no command. The
implementer will eyeball-grep and miss things. The repo has a `Grep` tool
convention; the command should be spelled.

**Synthesizer action.**
- Replace the checklist bullet with the exact command:
  `git grep -n "HEPPH_ALLOW_REFERENCE\|DDCALC_REFERENCE_ONLY\|reference_only"
  plugins/constraints/` must return empty. Same for `allow-analytic-fallback`.
- Add `test_no_reference_fallback.py` in
  `plugins/hep-ph-toolkit/skills/ddcalc/tests/` that runs the grep as a unit
  test. Pattern follows `/micromegas` plan §2.4's `test_blocker_shape.py`.

---

## 8. Helper-function reality check (MINOR — passes)

**Quote (draft §2):**
> "`install_ddcalc.sh` — Sources `_common.sh` via the 4-levels-deep
> pattern. `check_disk 1`, `download_with_retry`, `verify_checksum` (no
> `TODO` path), `tar xf`, `cd build && make FFLAGS=... CFLAGS=...
> -j$(python3 -c ...)`, smoke-test via `DDCalc_exampleC`."

**Counter.** Verified against `_common.sh`:
- `check_disk` ✓ (line 55)
- `download_with_retry` ✓ (line 94)
- `verify_checksum` ✓ (line 73) — note it *warns* on `TODO` rather than
  fails. The plan says "no `TODO` path" which is correct intent but
  means the plan must enforce that `HEPPH_DDCALC_SHA256` is a real value
  before this script runs. Since the verification gate already says so
  (§1 item 2, §5 bullet 2), this is self-consistent.
- `config_merge` ✓ (line 131) — not mentioned in the plan but needed;
  the plan's "Config keys written" table implies it.
- `EXIT_NO_GFORTRAN` ✓ (line 25).

**But:** the plan says "`check_disk 1`" — one GB. Verified: DDCalc source
is ~6 MB (per brainstorm §1) but the build artefacts plus a potential
`gfortran` module cache can easily exceed 1 GB on first build. `/micromegas`
uses `check_disk 3 5`. The 1 GB floor is too tight.

**Synthesizer action.**
- Raise to `check_disk 2 4`. Leave rationale in a comment in
  `install_ddcalc.sh`.
- Explicitly document which `_common.sh` helpers are used in the plan
  text (good practice; matches `/micromegas` plan §2.3 discipline).

---

## 9. Apple-Silicon build quirks are listed but not proved (MINOR)

**Quote (draft §3 step 5):**
> "Verify Apple-Silicon build quirks. Exercise `FFLAGS='-std=legacy
> -fallow-invalid-boz -O2'` + `CFLAGS='-Wno-implicit-function-declaration'`
> on gfortran 13+ / clang 15+."

**Counter.** The plan lists Fortran flags. What is missing is the macOS
linker flag. `/micromegas` brainstorm §1 step 2 has this explicitly:
`LDFLAGS="-Wl,-ld_classic"` for Xcode-15 Homebrew gfortran. DDCalc is
similarly Homebrew-gfortran-dependent on arm64. The plan mentions clang 15
CFLAGS but says nothing about `-ld_classic`. Without it, the link stage
fails on macOS 14.4+ with cryptic `ld: unsupported tapi file type` errors.

Additionally: the plan doesn't check `SDKROOT="$(xcrun --show-sdk-path)"`.
Missing SDKROOT on macOS 14+ causes `<stdio.h>: file not found` at the C
shim compile. `/micromegas` plan §2.3 already handles this via
`_macos_env.sh`; `/ddcalc` should reuse the same helper or borrow the
pattern.

**Synthesizer action.**
- Add `LDFLAGS="-Wl,-ld_classic"` (conditional on macOS + Homebrew
  gfortran detection) to `install_ddcalc.sh`.
- Add `SDKROOT="$(xcrun --show-sdk-path)"` export on macOS 14+; emit
  `DDCALC_MACOS_SDK_MISMATCH` fatal if `xcrun` fails.
- Lift the `_macos_env.sh` helper from `/micromegas` into
  `plugins/shared/install-helpers/_macos_env.sh` in a prep step, and
  source it from both skills. This is genuine cross-workstream reuse;
  propose as a W0 patch.

---

## 10. Plan integrity — step count, atomicity, gating (MINOR)

**Quote (draft §3 header):**
> "## 3. Implementation sequence (11 steps)"

**Counter.** Eleven is on the low end for a two-skill plugin with overlay
plumbing. `/micromegas` plan has 12 atomic commits for a comparable scope,
`/higgstools` has 12. `/ddcalc`'s step 4 ("Scaffold install path") rolls
six script authorings into one commit; step 8 ("Author driver + schema
validator") rolls five files into one. These are not atomic. Review
burden per commit balloons.

**Separate integrity issue:** step 1 is "planning-phase verifications"
with "no code yet" — but it is listed as step 1 of the **implementation
sequence**. Verification is pre-implementation; conflating them hides
whether the gate was actually met before step 2. The other plans separate
prereq resolution from implementation steps. Step 1 should either be
labelled "Step 0" or moved into §1.

**Synthesizer action.**
- Renumber: make the planning-phase verifications "Step 0 — preconditions"
  outside the sequence, or move them entirely into §1 as a precondition
  checklist that must be `plan/verifications.md`-committed **before** the
  branch is created.
- Split step 4 into three commits: (a) `detect` + `use-path` + `_blocker.sh`,
  (b) `install_ddcalc.sh` + `skill_env.yaml` + `_smoke_test.sh`,
  (c) offline-cache test + unit tests. Matches `/micromegas` step 3+4 split.
- Split step 8 into two commits: (a) `ddcalc_driver.c` + build/cache
  machinery + parser, (b) `run_ddcalc.py` + `validate_scattering.py` +
  `halo.py`. Parser + driver are different review surfaces.
- Result: 13 atomic commits, which aligns with sibling workstreams.

---

## Summary

Five blockers, two majors, three minors. Overlay feasibility (#1) is the
one that, if it fails the verification probe, forces a scope change for
v1 (native-only experiments). The URL probe (#2), SHA256 provenance (#3),
and schema-field coordination (#5) are each fixable with one additional
paragraph in the plan; attack them before opening the implementation PR.
Per-experiment NOTICEs (#4) and O'Hare licence (#6) are compliance issues
that will surface at PR review if not handled up front. The minors are
code-hygiene — fix while the plan is still cheap.

Word count: ~1480.
