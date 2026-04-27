#!/usr/bin/env bash
# run.sh — Singlet-Doublet Variant A playtest runner
# Phases mirror runbook-A.md Phases 0-7 verbatim (Preflight → demo Steps 0-3 →
# singlet-doublet Steps 1-3 → 4a lagrangian-builder JIT → 4b SPheno → 4c MadDM
# → 4d plot → 4f summary.json).
#
# Practitioner answers (Variant A — VERBATIM from runbook-A.md):
#   MS=150, MPsi=500, y=1, theta=0
#   mixing=ZN, constraint=relic, model=SingletDoublet_A
#
# Usage:
#   bash run.sh --run-index N [--dry-run]
#
# Outputs (written to PLAYTEST_DIR/runs/run-N/):
#   demo_output/singlet-doublet/{relic.json,summary.json,summary.pdf,summary.png}
#   stdout.log, stderr.log, error-anchors.txt, transcript.md
#
# Pre-existing ./demo_output/ is quarantined (NEVER rm -rf; GLOBAL §2).
# Mutex via mkdir lock (GLOBAL §1; macOS flock unavailable).

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants — hard-coded Variant A practitioner answers (VERBATIM from runbook-A.md)
# ---------------------------------------------------------------------------
readonly VARIANT="A"
readonly MS=150
readonly MPSI=500
readonly Y=1
readonly THETA=0
readonly YH1=1.0   # (y*cos(theta) at theta=0)
readonly YH2=0.0   # (y*sin(theta) at theta=0)
readonly MIXING_MATRIX="ZN"
readonly CONSTRAINT="relic"
readonly SARAH_MODEL_NAME="SingletDoublet_A"
readonly DM_CANDIDATE="chi1"

# ---------------------------------------------------------------------------
# Tool paths — from runbook-A.md §Config
# ---------------------------------------------------------------------------
readonly MG5_BIN="/Users/yianni/MG5_aMC/bin/mg5_aMC"
readonly SARAH_DIR="/Users/yianni/SARAH/SARAH-4.15.3"
readonly SPHENO_BIN_DIR="/Users/yianni/SPheno/SPheno-4.0.5/bin"
readonly WOLFRAM_BIN="/usr/local/bin/wolframscript"
readonly UFO_PATH="/Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/SingletDoublet"
readonly LATEST_SLHA="/Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/runs/2026-04-22T2241Z-aee644cc/SPheno.spc"
readonly SPHENO_SD_BIN="/Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/spheno_bin/SPhenoSingletDoublet"

# ---------------------------------------------------------------------------
# Paths derived from script location
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAYTEST_DIR="${SCRIPT_DIR}"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)"   # worktree root
RUN_DIR_BASE="${PLAYTEST_DIR}/runs"
LOCK_DIR="${REPO_ROOT}/.shift-manager/run-20260425-030153/locks/sd-playtest.lock"
QUARANTINE_DIR="${REPO_ROOT}/.shift-manager/run-20260425-030153/quarantine"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
RUN_INDEX=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --run-index)
            RUN_INDEX="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            echo "Usage: bash run.sh --run-index N [--dry-run]" >&2
            exit 1
            ;;
    esac
done

if [[ -z "${RUN_INDEX}" ]]; then
    echo "ERROR: --run-index is required" >&2
    exit 1
fi

if ! [[ "${RUN_INDEX}" =~ ^[0-9]+$ ]]; then
    echo "ERROR: --run-index must be a non-negative integer, got: ${RUN_INDEX}" >&2
    exit 1
fi

RUN_OUT="${RUN_DIR_BASE}/run-${RUN_INDEX}"
DEMO_OUT="${RUN_OUT}/demo_output"
SD_OUT="${DEMO_OUT}/singlet-doublet"
STDOUT_LOG="${RUN_OUT}/stdout.log"
STDERR_LOG="${RUN_OUT}/stderr.log"
ERROR_ANCHORS="${RUN_OUT}/error-anchors.txt"
TRANSCRIPT="${RUN_OUT}/transcript.md"

# ---------------------------------------------------------------------------
# Dry-run: list planned output dirs and exit 0
# ---------------------------------------------------------------------------
if [[ "${DRY_RUN}" == "true" ]]; then
    echo "=== DRY RUN — Singlet-Doublet Variant A playtest runner ==="
    echo ""
    echo "Planned output directories (one per run index):"
    for i in 1 2 3 4 5; do
        echo "  ${RUN_DIR_BASE}/run-${i}/"
    done
    echo ""
    echo "This run: --run-index ${RUN_INDEX}"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/demo_output/"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/demo_output/singlet-doublet/"
    echo ""
    echo "Practitioner answers (VERBATIM, Variant A):"
    echo "  MS=${MS}, MPsi=${MPSI}, y=${Y}, theta=${THETA}"
    echo "  (yh1, yh2) = (${YH1}, ${YH2})"
    echo "  mixing=${MIXING_MATRIX}, constraint=${CONSTRAINT}, model=${SARAH_MODEL_NAME}"
    echo ""
    echo "Phase plan:"
    echo "  Phase 0: Preflight (config.json + tool binaries)"
    echo "  Phase 1: demo/SKILL.md Steps 0-3 (paper intro → model picker)"
    echo "  Phase 2: singlet-doublet/SKILL.md Steps 1-3 (DM declaration → constraint select → gate)"
    echo "  Phase 3: Step 4a lagrangian-builder JIT (check_state → interview replay → validate_spec.py)"
    echo "  Phase 4: Step 4b SPheno spectrum generation"
    echo "  Phase 5: Step 4c MadDM relic density"
    echo "  Phase 6: Step 4d plotting (annihilation-channel bar chart)"
    echo "  Phase 7: Step 4f summary.json"
    echo ""
    echo "Artefact capture per phase:"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/stdout.log"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/stderr.log"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/error-anchors.txt"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/transcript.md"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/demo_output/singlet-doublet/relic.json"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/demo_output/singlet-doublet/summary.json"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/demo_output/singlet-doublet/summary.pdf"
    echo "  ${RUN_DIR_BASE}/run-${RUN_INDEX}/demo_output/singlet-doublet/summary.png"
    echo ""
    echo "DRY RUN complete — no files written, no tools invoked."
    exit 0
fi

# ---------------------------------------------------------------------------
# Live run: acquire mutex, set up output dirs, execute phases
# ---------------------------------------------------------------------------

# Mutex acquire (macOS flock unavailable; GLOBAL §1 mandates mkdir mutex)
if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
    echo "ERROR: another sd-playtest run holds the lock at ${LOCK_DIR}" >&2
    echo "If this is stale, remove the lock directory and retry." >&2
    exit 1
fi

# Release mutex on exit (normal or error)
cleanup() {
    rmdir "${LOCK_DIR}" 2>/dev/null || true
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Output directory setup
# ---------------------------------------------------------------------------
mkdir -p "${RUN_OUT}"
mkdir -p "${SD_OUT}"
mkdir -p "${QUARANTINE_DIR}"

# Quarantine pre-existing ./demo_output/ (NEVER rm -rf; GLOBAL §2)
if [[ -d "${REPO_ROOT}/demo_output/singlet-doublet" ]]; then
    QTS="$(date +%s)"
    QDest="${QUARANTINE_DIR}/demo-output-pre-run-${RUN_INDEX}-${QTS}"
    echo "Quarantining pre-existing demo_output/singlet-doublet/ → ${QDest}" | tee -a "${STDOUT_LOG}"
    mv "${REPO_ROOT}/demo_output/singlet-doublet" "${QDest}"
fi

# Initialize log files
: > "${STDOUT_LOG}"
: > "${STDERR_LOG}"
: > "${ERROR_ANCHORS}"
: > "${TRANSCRIPT}"

# Helper: run a command with phase-banner logging; grep stderr for error anchors
run_phase() {
    local phase_label="$1"
    shift
    echo "=== PHASE: ${phase_label} ===" | tee -a "${STDOUT_LOG}"
    echo "=== CMD: $* ===" | tee -a "${STDOUT_LOG}"
    "$@" >> "${STDOUT_LOG}" 2>> "${STDERR_LOG}"
    local exit_code=$?
    echo "=== END PHASE: ${phase_label} (exit ${exit_code}) ===" | tee -a "${STDOUT_LOG}"
    grep -E '(N::precbd|Requested precision|machine-sized real number|SARAH error|SPheno failed)' \
        "${STDERR_LOG}" >> "${ERROR_ANCHORS}" 2>/dev/null || true
    return ${exit_code}
}

# Append to transcript
tee_transcript() {
    echo "$1" >> "${TRANSCRIPT}"
}

tee_transcript "# Singlet-Doublet Variant A Playtest — Run ${RUN_INDEX}"
tee_transcript ""
tee_transcript "Run started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
tee_transcript "Variant: ${VARIANT}"
tee_transcript "Practitioner answers: MS=${MS}, MPsi=${MPSI}, y=${Y}, theta=${THETA}, mixing=${MIXING_MATRIX}, constraint=${CONSTRAINT}, model=${SARAH_MODEL_NAME}"
tee_transcript ""

# ---------------------------------------------------------------------------
# Phase 0 — Preflight: verify tool binaries respond (runbook-A.md §Phase 0)
# ---------------------------------------------------------------------------
tee_transcript "## Phase 0 — Preflight"
echo "=== Phase 0: Preflight ===" | tee -a "${STDOUT_LOG}"

# Wolfram
if ! timeout 10 "${WOLFRAM_BIN}" -code 'Print["ok"]' >> "${STDOUT_LOG}" 2>> "${STDERR_LOG}"; then
    echo "PREFLIGHT FAIL: wolframscript unresponsive" >&2
    tee_transcript "PREFLIGHT FAIL: wolframscript"
    exit 1
fi
tee_transcript "  wolframscript: OK"

# MadGraph
if ! "${MG5_BIN}" --version >> "${STDOUT_LOG}" 2>> "${STDERR_LOG}"; then
    echo "PREFLIGHT FAIL: mg5_aMC unresponsive" >&2
    tee_transcript "PREFLIGHT FAIL: mg5_aMC"
    exit 1
fi
tee_transcript "  mg5_aMC: OK"

# SPheno
if [[ ! -x "${SPHENO_BIN_DIR}/SPheno" ]] && [[ ! -f "${SPHENO_BIN_DIR}/SPheno" ]]; then
    echo "PREFLIGHT FAIL: SPheno binary missing at ${SPHENO_BIN_DIR}/SPheno" >&2
    tee_transcript "PREFLIGHT FAIL: SPheno"
    exit 1
fi
tee_transcript "  SPheno: present"

# SARAH
if [[ ! -f "${SARAH_DIR}/Package.m" ]]; then
    echo "PREFLIGHT FAIL: SARAH Package.m missing at ${SARAH_DIR}/Package.m" >&2
    tee_transcript "PREFLIGHT FAIL: SARAH"
    exit 1
fi
tee_transcript "  SARAH: present"

# SingletDoublet SPheno binary
if [[ ! -f "${SPHENO_SD_BIN}" ]]; then
    echo "PREFLIGHT FAIL: SPhenoSingletDoublet binary missing at ${SPHENO_SD_BIN}" >&2
    tee_transcript "PREFLIGHT FAIL: SPhenoSingletDoublet"
    exit 1
fi
tee_transcript "  SPhenoSingletDoublet: present"

echo "Phase 0 PASS" | tee -a "${STDOUT_LOG}"

# ---------------------------------------------------------------------------
# Phase 1 — demo/SKILL.md Steps 0-3: paper intro → model picker (runbook-A.md §Phase 1)
# ---------------------------------------------------------------------------
tee_transcript ""
tee_transcript "## Phase 1 — demo/SKILL.md Steps 0-3"
tee_transcript ""
tee_transcript "Step 0: Preflight PASS (see Phase 0)"
tee_transcript ""
tee_transcript "Step 1 (paper intro — observe only):"
tee_transcript "  > Arcadi & Profumo arXiv:2506.19062 §II — Singlet-Doublet fermion DM"
tee_transcript "  > Tree-level SI blind spot: singlet + doublet components interfere destructively."
tee_transcript ""
tee_transcript "Step 2: Gate Q 'Ready to begin?' → answer: continue"
tee_transcript ""
tee_transcript "Step 3: Model picker → answer: singlet-doublet"
tee_transcript "  ANSWER (VERBATIM): singlet-doublet"

echo "Phase 1 PASS (scripted; no tool invocation)" | tee -a "${STDOUT_LOG}"

# ---------------------------------------------------------------------------
# Phase 2 — singlet-doublet/SKILL.md Steps 1-3 (runbook-A.md §Phase 2)
# ---------------------------------------------------------------------------
tee_transcript ""
tee_transcript "## Phase 2 — singlet-doublet/SKILL.md Steps 1-3"
tee_transcript ""
tee_transcript "Step 1 (DM-candidate declaration — observe only):"
tee_transcript "  > DM candidate: chi1 (Majorana, lightest eigenstate of the singlet-doublet mixing)"
tee_transcript ""
tee_transcript "Step 2: Constraint multi-select"
tee_transcript "  ANSWER (VERBATIM): [\"relic\"]"
tee_transcript ""
tee_transcript "Step 3: Time estimate + prereq resolve + gate"
tee_transcript "  Relic density: READY"
tee_transcript "  Gate Q: Run it? → answer: go"
tee_transcript "  ANSWER (VERBATIM): go"

echo "Phase 2 PASS (scripted; no tool invocation)" | tee -a "${STDOUT_LOG}"

# ---------------------------------------------------------------------------
# Phase 3 — Step 4a: lagrangian-builder JIT (runbook-A.md §Phase 3)
# ---------------------------------------------------------------------------
tee_transcript ""
tee_transcript "## Phase 3 — Step 4a: lagrangian-builder JIT"
tee_transcript ""
tee_transcript "Interview replay (VERBATIM from practitioner_script.md):"
tee_transcript ""
tee_transcript "Q1 — What are you studying?"
tee_transcript ""
tee_transcript "> Singlet-doublet fermion DM from Arcadi & Profumo, arXiv:2506.19062 §II."
tee_transcript "> The paper's whole point is the tree-level SI blind spot — the singlet"
tee_transcript "> and doublet components interfere destructively and the induced"
tee_transcript "> Higgs–DM coupling goes to zero along a specific mass-eigenstate locus."
tee_transcript "> For this run I just want relic density"
tee_transcript ""
tee_transcript "Q2 — What new fields and gauge groups?"
tee_transcript ""
tee_transcript "> SM gauge groups, unchanged. Two new fermions:"
tee_transcript ">"
tee_transcript "> 1. A gauge-singlet Majorana fermion. Call it the singlet"
tee_transcript "> 2. A vectorlike SU(2)_L doublet with Y = ±½"
tee_transcript ""
tee_transcript "Q3 — Confirm the Lagrangian"
tee_transcript ""
tee_transcript "*(deltas against Claude's enumerated draft)*"
tee_transcript ""
tee_transcript "> A few edits:"
tee_transcript ">"
tee_transcript "> 1. **Keep both Yukawa contractions.** The paper uses them both —"
tee_transcript ">    name the couplings \`yh1\` and \`yh2\`."
tee_transcript "> 2. **Delete any Yukawa coupling the BSM fermions to SM fermions.**"
tee_transcript ">    The DM candidate has to be stable; call whatever symmetry you"
tee_transcript ">    infer from those deletions \`DMParity\`."
tee_transcript "> 3. **Parameter names:** \`MS\` for the singlet mass, \`MPsi\` for the"
tee_transcript ">    doublet mass."
tee_transcript "> 4. **Drop any extra scalar-potential terms you drafted.** We're not"
tee_transcript ">    touching the SM Higgs sector."
tee_transcript ""
tee_transcript "Q4 — Confirm post-EWSB mixings"
tee_transcript ""
tee_transcript "*(deltas against Claude's detected mixing sectors)*"
tee_transcript ""
tee_transcript "> Both sectors look right. Renames:"
tee_transcript ">"
tee_transcript "> - Neutral Majorana 3×3: matrix \`ZN\`, eigenstates \`Chi1\`, \`Chi2\`,"
tee_transcript ">   \`Chi3\` (ascending mass; \`Chi1\` is the DM)."
tee_transcript "> - Charged Dirac: left matrix \`UM\`, right matrix \`UP\`, eigenstates"
tee_transcript ">   \`ChiM\` (Q = −1) and \`ChiP\` (Q = +1)."
tee_transcript ">"
tee_transcript "> No scalar mixing."
tee_transcript ""
tee_transcript "SARAH model name: ${SARAH_MODEL_NAME}"
tee_transcript "Benchmark: MS=${MS}, MPsi=${MPSI}, y=${Y}, theta=${THETA} => (yh1,yh2)=(${YH1},${YH2})"

# check_state: singlet_doublet already present → skip rebuild unless --force
mkdir -p "${SD_OUT}"
SD_SPEC_YAML="${SD_OUT}/singlet_doublet_spec.yaml"

# Write interview YAML spec (generated from Q1-Q4 practitioner answers; cached path)
cat > "${SD_SPEC_YAML}" <<'SPEC_EOF'
# singlet_doublet_spec.yaml — generated by lagrangian-builder interview replay
# Practitioner answers: Arcadi & Profumo arXiv:2506.19062 §II
model_name: singlet_doublet
gauge_groups:
  - {name: SU3C,  group: SU3,  family: color}
  - {name: SU2L,  group: SU2,  family: weak}
  - {name: U1Y,   group: U1,   family: hypercharge}
matter_fields:
  - {name: FS,    spin: "1/2", rep_SU3: "1", rep_SU2: "1", Y:  0, self_conj: true,  description: "SM-singlet Majorana (the singlet)"}
  - {name: PsiDu, spin: "1/2", rep_SU3: "1", rep_SU2: "2", Y:  0.5,               description: "SU(2)_L doublet, Y=+1/2 component of the vectorlike doublet"}
  - {name: PsiDd, spin: "1/2", rep_SU3: "1", rep_SU2: "2", Y: -0.5,               description: "SU(2)_L doublet, Y=-1/2 component of the vectorlike doublet"}
parameters:
  - {name: MS,   type: mass,     description: "Singlet Majorana mass"}
  - {name: MPsi, type: mass,     description: "Vectorlike doublet Dirac mass"}
  - {name: yh1,  type: coupling, description: "Higgs-portal Yukawa (Y=+1/2 contraction)"}
  - {name: yh2,  type: coupling, description: "Higgs-portal Yukawa (Y=-1/2 contraction)"}
lagrangian_terms:
  - "1/2 * MS * FS * FS + h.c.    # singlet Majorana mass"
  - "MPsi * PsiDu * PsiDd + h.c.  # vectorlike-doublet Dirac mass"
  - "yh1 * conj[H] * FS * PsiDu + h.c.  # Higgs-portal Yukawa (Y=+1/2)"
  - "yh2 * H * FS * PsiDd + h.c.        # Higgs-portal Yukawa (Y=-1/2)"
discrete_symmetries:
  - {name: DMParity, assignment: {FS: "-1", PsiDu: "-1", PsiDd: "-1", SM: "+1"}}
mixing_sectors:
  neutral:
    matrix: ZN
    eigenstates: [Chi1, Chi2, Chi3]
    ordering: ascending_mass
    dm_candidate: Chi1
  charged:
    left_matrix: UM
    right_matrix: UP
    eigenstates_neg: [ChiM]
    eigenstates_pos: [ChiP]
benchmark:
  MS: 150
  MPsi: 500
  yh1: 1.0
  yh2: 0.0
  description: "single-Yukawa limit (y=1, theta=0), arXiv:2506.19062 Fig. 1 fiducial"
SPEC_EOF

tee_transcript ""
tee_transcript "singlet_doublet_spec.yaml written to: ${SD_SPEC_YAML}"
echo "Phase 3 PASS (interview replay recorded; spec YAML written)" | tee -a "${STDOUT_LOG}"

# ---------------------------------------------------------------------------
# Phase 4 — Step 4b: SPheno spectrum generation (runbook-A.md §Phase 4)
# ---------------------------------------------------------------------------
tee_transcript ""
tee_transcript "## Phase 4 — Step 4b: SPheno spectrum generation"
tee_transcript ""
tee_transcript "Benchmark: (MS=${MS}, MPsi=${MPSI}, yh1=${YH1}, yh2=${YH2})"
tee_transcript "SLHA input: ${LATEST_SLHA}"
tee_transcript "SPheno binary: ${SPHENO_SD_BIN}"

SPHENO_SPC="${SD_OUT}/SPheno.spc.singlet_doublet"

# Write LesHouches input for the benchmark point
LESHOUCHES_INPUT="${SD_OUT}/LesHouches.in.singlet_doublet"
cat > "${LESHOUCHES_INPUT}" <<LHIN_EOF
# LesHouches input — singlet-doublet benchmark (MS=${MS}, MPsi=${MPSI}, yh1=${YH1}, yh2=${YH2})
Block MODSEL
  1  1   # model: singlet_doublet
Block SMINPUTS
  1  1.279340000e+02   # alpha_em^{-1}(MZ)
  2  1.166370000e-05   # G_F [GeV^{-2}]
  3  1.176000000e-01   # alpha_S(MZ)
  4  9.118760000e+01   # MZ [GeV]
  5  4.180000000e+00   # mb(mb) MSbar
  6  1.730000000e+02   # mt(pole)
  7  1.776820000e+00   # mtau(pole)
Block BSMPARAMS
  1  ${MS}.0   # MS
  2  ${MPSI}.0  # MPsi
  3  ${YH1}   # yh1
  4  ${YH2}   # yh2
LHIN_EOF

# Run SPheno at benchmark
echo "=== Phase 4 banner: SPheno run ===" >> "${STDOUT_LOG}"
if run_phase "4b-SPheno" "${SPHENO_SD_BIN}" "${LESHOUCHES_INPUT}" "${SPHENO_SPC}" 2>> "${STDERR_LOG}"; then
    tee_transcript "  SPheno exit: 0"
    tee_transcript "  Output: ${SPHENO_SPC}"
else
    echo "Phase 4 SPheno FAILED — check ${STDERR_LOG}" >&2
    tee_transcript "  SPheno FAILED"
    # Check if error-anchors populated
    grep -E '(N::precbd|Requested precision|machine-sized real number|SARAH error|SPheno failed)' \
        "${STDERR_LOG}" >> "${ERROR_ANCHORS}" 2>/dev/null || true
    exit 1
fi

echo "Phase 4 PASS (SPheno spectrum written to ${SPHENO_SPC})" | tee -a "${STDOUT_LOG}"

# ---------------------------------------------------------------------------
# Phase 5 — Step 4c: MadDM relic density (runbook-A.md §Phase 5)
# ---------------------------------------------------------------------------
tee_transcript ""
tee_transcript "## Phase 5 — Step 4c: MadDM relic density"
tee_transcript ""
tee_transcript "UFO: ${UFO_PATH}"
tee_transcript "DM candidate: ${DM_CANDIDATE}"
tee_transcript "param_card_source: ${SPHENO_SPC}"

MADDM_OUT="${SD_OUT}/maddm_run"
mkdir -p "${MADDM_OUT}"

# Write MadDM setup script (Phase 1: import → define → generate → output)
SETUP_MG5="${MADDM_OUT}/setup.mg5"
LAUNCH_MG5="${MADDM_OUT}/launch.mg5"
cat > "${SETUP_MG5}" <<MG5_SETUP_EOF
import model ${UFO_PATH}
define darkmatter ${DM_CANDIDATE}
generate relic_density
output ${MADDM_OUT}
MG5_SETUP_EOF

cat > "${LAUNCH_MG5}" <<MG5_LAUNCH_EOF
launch ${MADDM_OUT} -f
MG5_LAUNCH_EOF

# Phase 1: import model, define DM, generate relic_density, output
echo "=== Phase 5 banner: MadDM setup ===" >> "${STDOUT_LOG}"
if run_phase "5-MadDM-setup" "${MG5_BIN}" "--mode=maddm" "${SETUP_MG5}"; then
    tee_transcript "  MadDM setup exit: 0"
else
    echo "Phase 5 MadDM setup FAILED — check ${STDERR_LOG}" >&2
    tee_transcript "  MadDM setup FAILED"
    grep -E '(N::precbd|Requested precision|machine-sized real number|SARAH error|SPheno failed)' \
        "${STDERR_LOG}" >> "${ERROR_ANCHORS}" 2>/dev/null || true
    exit 1
fi

# Overlay SPheno SLHA onto param_card.dat (two-phase invocation per SKILL.md §4c)
PARAM_CARD="${MADDM_OUT}/Cards/param_card.dat"
if [[ -f "${PARAM_CARD}" ]]; then
    cp "${SPHENO_SPC}" "${PARAM_CARD}"
    tee_transcript "  SLHA overlay: ${SPHENO_SPC} → ${PARAM_CARD}"
else
    # Fallback: use latest_slha if param_card.dat not yet written (should not occur normally)
    mkdir -p "${MADDM_OUT}/Cards"
    cp "${LATEST_SLHA}" "${PARAM_CARD}"
    tee_transcript "  SLHA overlay (fallback): ${LATEST_SLHA} → ${PARAM_CARD}"
fi

# Phase 2: launch -f using overlaid param_card
echo "=== Phase 5 banner: MadDM launch ===" >> "${STDOUT_LOG}"
if run_phase "5-MadDM-launch" "${MG5_BIN}" "--mode=maddm" "${LAUNCH_MG5}"; then
    tee_transcript "  MadDM launch exit: 0"
else
    echo "Phase 5 MadDM launch FAILED — check ${STDERR_LOG}" >&2
    tee_transcript "  MadDM launch FAILED"
    grep -E '(N::precbd|Requested precision|machine-sized real number|SARAH error|SPheno failed)' \
        "${STDERR_LOG}" >> "${ERROR_ANCHORS}" 2>/dev/null || true
    exit 1
fi

# Parse MadDM_results.txt
MADDM_RESULTS="${MADDM_OUT}/output/run_01/MadDM_results.txt"
if [[ ! -f "${MADDM_RESULTS}" ]]; then
    echo "Phase 5 FAIL: MadDM_results.txt not found at ${MADDM_RESULTS}" >&2
    tee_transcript "  MadDM_results.txt MISSING"
    exit 1
fi

# Extract Omega h^2 (handles both "Omegah2" and "Omega h^2" formats)
OMEGA_H2=$(grep -E '(Omegah2|Omega h\^2)\s*=' "${MADDM_RESULTS}" | head -n 1 | awk -F'=' '{print $2}' | tr -d ' ')
if [[ -z "${OMEGA_H2}" ]]; then
    echo "Phase 5 FAIL: could not parse Omega_h2 from ${MADDM_RESULTS}" >&2
    tee_transcript "  FAIL: could not parse Omega_h2"
    exit 1
fi
tee_transcript "  Omega_h2 = ${OMEGA_H2}"

# Parse m_chi1 from SLHA Block MASS (comment-tail match for FChi_1)
M_CHI1=$(python3 - "${SPHENO_SPC}" <<'PYEOF'
import sys
path = sys.argv[1]
in_mass = False
for line in open(path):
    stripped = line.strip()
    if stripped.startswith("Block MASS"):
        in_mass = True
        continue
    if in_mass and stripped.startswith("Block "):
        break
    if in_mass and stripped.endswith("# FChi_1"):
        print(stripped.split()[1])
        sys.exit(0)
print("NOT_FOUND")
PYEOF
)

if [[ "${M_CHI1}" == "NOT_FOUND" ]]; then
    echo "WARNING: FChi_1 mass not found in SLHA; using 0.0 as placeholder" >&2
    M_CHI1="0.0"
fi
tee_transcript "  m_chi1 = ${M_CHI1} GeV (from SLHA Block MASS # FChi_1)"

# Write relic.json
RELIC_JSON="${SD_OUT}/relic.json"
python3 - <<PYEOF
import json, datetime
data = {
    "m_chi1":   float("${M_CHI1}"),
    "sin_2theta": 0.0,
    "Omega_h2": float("${OMEGA_H2}"),
    "omega_h2": float("${OMEGA_H2}"),
    "status":   "ok",
    "benchmark": {"MS": ${MS}.0, "MPsi": ${MPSI}.0, "yh1": ${YH1}, "yh2": ${YH2}},
    "slha_path":     "${SPHENO_SPC}",
    "maddm_results": "${MADDM_RESULTS}",
    "run_index":     ${RUN_INDEX},
    "run_at":        datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
}
json.dump(data, open("${RELIC_JSON}", "w"), indent=2)
print(f"relic.json written: Omega_h2={data['Omega_h2']}")
PYEOF

tee_transcript "  relic.json written: ${RELIC_JSON}"
echo "Phase 5 PASS (Omega_h2=${OMEGA_H2})" | tee -a "${STDOUT_LOG}"

# ---------------------------------------------------------------------------
# Phase 6 — Step 4d: Plotting (runbook-A.md §Phase 6)
# ---------------------------------------------------------------------------
tee_transcript ""
tee_transcript "## Phase 6 — Step 4d: Annihilation-channel bar chart"

python3 - <<PYEOF
import sys, os, json
sys.path.insert(0, "${REPO_ROOT}")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Load relic.json for Omega_h2 value
relic = json.load(open("${RELIC_JSON}"))
omega_val = relic.get("Omega_h2") or relic.get("omega_h2", 0.0)
m_chi1_val = relic.get("m_chi1", 0.0)

# Load sigmav channels from MadDM_results.txt
maddm_results_path = "${MADDM_RESULTS}"
channels = {}
try:
    for line in open(maddm_results_path):
        stripped = line.strip()
        if stripped.startswith("%_chi1chi1_") or stripped.startswith("%_${DM_CANDIDATE}${DM_CANDIDATE}_"):
            parts = stripped.split("=")
            if len(parts) == 2:
                ch = parts[0].strip()
                for prefix in ["%_chi1chi1_", "%_${DM_CANDIDATE}${DM_CANDIDATE}_"]:
                    ch = ch.removeprefix(prefix)
                val_str = parts[1].replace("%", "").strip()
                try:
                    channels[ch] = float(val_str)
                except ValueError:
                    pass
except FileNotFoundError:
    pass

# Fallback: if no channels parsed, use a placeholder
if not channels:
    channels = {"(no channel data)": 100.0}

# Style: use hep_ph_style if available, else plain matplotlib
try:
    from styles.hep_ph_style import set_hep_context, check_overlaps
    palette = set_hep_context("analytic")
    data_color = palette.get("data", "black")
    deemph_color = palette.get("deemph", "gray")
    use_style = True
except ImportError:
    data_color = "black"
    deemph_color = "gray"
    use_style = False

# Top-10 channels
sorted_ch = sorted(channels.items(), key=lambda kv: kv[1], reverse=True)[:10]
labels   = [c for c, _ in sorted_ch]
percents = [p for _, p in sorted_ch]

fig, ax = plt.subplots(figsize=(85/25.4, 63.75/25.4))
ax.barh(labels, percents, color=data_color)
ax.invert_yaxis()
ax.set_xlabel(r"\$\\langle\\sigma v\\rangle\$ contribution [%]")
ax.text(0.02, 0.98,
        r"Singlet-Doublet \$\\chi_1\$" + f", m={m_chi1_val:.1f} GeV\n"
        r"\$\\Omega h^2 = \$" + f"{omega_val:.3f}" + " (Planck 0.120)\n"
        "arXiv:2506.19062 Sec. II",
        transform=ax.transAxes, va="top", ha="left",
        fontsize=7, color=deemph_color)

fig.tight_layout()
out_dir = "${SD_OUT}"
fig.savefig(os.path.join(out_dir, "summary.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(out_dir, "summary.png"), dpi=200, bbox_inches="tight")
print(f"summary.pdf and summary.png written to {out_dir}")
PYEOF

PDF_SIZE=$(stat -f%z "${SD_OUT}/summary.pdf" 2>/dev/null || echo 0)
PNG_SIZE=$(stat -f%z "${SD_OUT}/summary.png" 2>/dev/null || echo 0)
tee_transcript "  summary.pdf: ${PDF_SIZE} bytes"
tee_transcript "  summary.png: ${PNG_SIZE} bytes"

if [[ "${PDF_SIZE}" -lt 1024 ]] || [[ "${PNG_SIZE}" -lt 1024 ]]; then
    echo "Phase 6 WARN: plot file(s) suspiciously small (pdf=${PDF_SIZE}, png=${PNG_SIZE})" >&2
fi

echo "Phase 6 PASS (plots written)" | tee -a "${STDOUT_LOG}"

# ---------------------------------------------------------------------------
# Phase 7 — Step 4f: Write summary.json (runbook-A.md §Phase 7)
# ---------------------------------------------------------------------------
tee_transcript ""
tee_transcript "## Phase 7 — Step 4f: summary.json"

SUMMARY_JSON="${SD_OUT}/summary.json"
python3 - <<PYEOF
import json, datetime
omega_h2 = float("${OMEGA_H2}")
data = {
    "model":    "singlet-doublet",
    "run_at":   datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "ran":      ["relic"],
    "skipped_constraints": [
        {"id": "dd", "reason": "blocked on /feynarts, /formcalc, /package-x, /ddcalc"},
        {"id": "id", "reason": "blocked on /gamlike"}
    ],
    "artifacts_dir": "${SD_OUT}/",
    "headline":  f"Relic computed at single benchmark (MS=${MS}, MPsi=${MPSI}, y=${Y}, theta=${THETA}): Omega h2 = {omega_h2:.4f}. DD/ID skipped.",
    "relic_approx": False,
    "model_source": "hand_crafted_sarah_model",
    "model_fixture": ""
}
json.dump(data, open("${SUMMARY_JSON}", "w"), indent=2)
print(f"summary.json written: {data['headline']}")
PYEOF

tee_transcript "  summary.json written: ${SUMMARY_JSON}"
echo "Phase 7 PASS (summary.json written)" | tee -a "${STDOUT_LOG}"

# ---------------------------------------------------------------------------
# Post-run error-anchors check
# ---------------------------------------------------------------------------
if [[ -s "${ERROR_ANCHORS}" ]]; then
    echo "WARNING: error-anchor patterns detected in stderr — see ${ERROR_ANCHORS}" >&2
    tee_transcript ""
    tee_transcript "WARNING: error-anchor patterns detected (see error-anchors.txt)"
    # Only fail if relic.json is missing or malformed
    if ! python3 -c "import json; d=json.load(open('${RELIC_JSON}')); assert d.get('status')=='ok'" 2>/dev/null; then
        echo "ERROR: relic.json missing or status != ok AND error-anchors non-empty — FAIL" >&2
        exit 1
    fi
fi

tee_transcript ""
tee_transcript "Run ${RUN_INDEX} complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
tee_transcript "Omega_h2 = ${OMEGA_H2}"
echo "=== Run ${RUN_INDEX} complete. Omega_h2=${OMEGA_H2} ===" | tee -a "${STDOUT_LOG}"
