#!/usr/bin/env bash
# install.sh — /maddm-install skill entry point.
#
# Subcommands:
#   detect              Print JSON state of existing MadDM install. No side effects.
#   use-path <dir>      Register an existing MadDM plugin directory in config.
#   install [dir]       Run `mg5_aMC -f <script>` with `install maddm`; falls back
#                       to `git clone` of maddmhep/maddm on failure.
#   validate            Re-run the smoke test against the currently-configured MadDM.
#
# HEPPH_MADDM_VERSION env override respected (defaults to 3.2.13).
set -euo pipefail

_LOG_TAG="maddm_install"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source shared helpers (4 levels up: skills/maddm-install/scripts → plugins).
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then
  SHARED_COMMON="$SCRIPT_DIR/_common.sh"
fi
# shellcheck source=../../../../shared/install-helpers/_common.sh
. "$SHARED_COMMON"

# Source blocker helper.
# shellcheck source=_blocker.sh
. "$SCRIPT_DIR/_blocker.sh"

# ---------------------------------------------------------------------------
# Version / URL configuration (HEPPH_MADDM_VERSION override).
# ---------------------------------------------------------------------------
MADDM_VERSION="${HEPPH_MADDM_VERSION:-3.2.13}"
MADDM_GIT_URL="https://github.com/maddmhep/maddm.git"
MADDM_GIT_TAG="v${MADDM_VERSION}"
MADDM_SHA256="TODO"  # verify_checksum warns-not-aborts for TODO; git path doesn't hit it.
MG5_MIN_VERSION="2.6.2"

MG5_SCRIPT_TMP="/tmp/maddm_install_mg5_script.$$"
MG5_LOG_TMP="/tmp/maddm_install_mg5.log"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Compare two semver strings. Returns 0 if $1 >= $2, else 1.
version_ge() {
  # Use sort -V; the older version sorts first.
  local a="$1" b="$2"
  local first
  first="$(printf '%s\n%s\n' "$a" "$b" | sort -V | head -n1)"
  [ "$first" = "$b" ]
}

# Probe MG5 version from its binary.
mg5_probe_version() {
  local bin="$1"
  [ -x "$bin" ] || return 1
  "$bin" --version 2>/dev/null | grep -Eo 'v?[0-9]+\.[0-9]+\.[0-9]+' | head -n1 | sed 's/^v//'
}

# Derive <MG5_ROOT> from madgraph_path (.../bin/mg5_aMC → ...).
mg5_root_from_bin() {
  local bin="$1"
  (cd "$(dirname "$bin")/.." && pwd)
}

# Require that MG5 is present and recent enough. On failure, emits a blocker
# and exits. On success, echoes MG5_ROOT on stdout.
require_mg5() {
  local mg5_bin
  mg5_bin="$(config_get madgraph_path)"
  if [ -z "$mg5_bin" ] || [ ! -x "$mg5_bin" ]; then
    emit_blocker "MADGRAPH_ABSENT" "fatal" \
      "madgraph_path is not set in config or points to a non-executable path." \
      "Run /install (hep-ph-demo) first to install MadGraph5_aMC@NLO, then retry /maddm-install."
    exit 20
  fi
  local version
  version="$(mg5_probe_version "$mg5_bin" || echo "")"
  if [ -n "$version" ] && ! version_ge "$version" "$MG5_MIN_VERSION"; then
    emit_blocker "MADGRAPH_VERSION_TOO_OLD" "fatal" \
      "MG5 version $version is older than the minimum $MG5_MIN_VERSION required by MadDM 3.x." \
      "Upgrade MG5 to $MG5_MIN_VERSION or later (rerun /install) and retry /maddm-install."
    exit 20
  fi
  local root
  root="$(mg5_root_from_bin "$mg5_bin")"
  echo "$root"
}

# Require gfortran on PATH (Fortran compilation of cross-section code).
require_gfortran() {
  if command -v gfortran >/dev/null 2>&1; then
    log "gfortran found: $(command -v gfortran)"
    return 0
  fi
  local user_instruction
  case "$(os_name)" in
    macos) user_instruction="Install gfortran with Homebrew: brew install gcc" ;;
    linux) user_instruction="Install gfortran with: sudo apt-get install -y gfortran  (Debian/Ubuntu) or sudo yum install -y gcc-gfortran  (RHEL/CentOS)" ;;
    *)     user_instruction="Install a Fortran compiler (gfortran) for your OS before retrying." ;;
  esac
  emit_blocker "GFORTRAN_ABSENT" "fatal" \
    "gfortran is required to compile MadDM cross-section code but was not found on PATH." \
    "$user_instruction"
  exit 25
}

# Check that MG5 is running on a Python 3.7+ interpreter compatible with MadDM.
check_python_compat() {
  local mg5_bin="$1"
  local py_exe=""
  # MG5 3.x uses $MG5_ROOT/../python3 on some installs; safer: parse banner.
  py_exe="$("$mg5_bin" --version 2>/dev/null | grep -Eo 'python[[:space:]]*[0-9]+\.[0-9]+' \
            | grep -Eo '[0-9]+\.[0-9]+' | head -n1 || true)"
  if [ -z "$py_exe" ]; then
    # Fall back to checking whichever python3 is on PATH; assume MG5 uses it.
    if command -v python3 >/dev/null 2>&1; then
      py_exe="$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null || true)"
    fi
  fi
  if [ -z "$py_exe" ]; then
    warn "Could not determine Python version used by MG5; skipping compat check."
    return 0
  fi
  if ! version_ge "$py_exe" "3.7"; then
    emit_blocker "MADDM_PYTHON_MISMATCH" "fatal" \
      "MG5 appears to be running under Python $py_exe, but MadDM 3.x requires Python 3.7 or later." \
      "Reinstall MG5 against a Python 3.7+ interpreter (rerun /install) and retry /maddm-install."
    exit 20
  fi
  log "Python $py_exe OK for MadDM (>= 3.7)."
}

# ---------------------------------------------------------------------------
# Upstream patches.
#
# MadDM 3.2.13 ships as Python 2 and has not been ported. The three functions
# below perform the minimum transformations needed to load the plugin under
# MG5 3.5.6 on Python 3.7+. Each is idempotent (safe to re-run); the
# apply_maddm_upstream_patches orchestrator writes a sentinel file so a
# second install invocation is a no-op. If upstream lands its own Python 3
# port these patches can be removed in one commit.
#
# Each patch addresses a *specific* upstream bug, verified against
#   maddmhep/maddm@v3.2.13 (== madgraph.phys.ucl.ac.be/Downloads/maddm/maddm_V3.2.13.tar.gz)
# Sources of each bug are cited inline. When adding a patch for a newer
# upstream bug, append a new helper rather than extending one of these so
# each helper stays scoped to one symptom.
# ---------------------------------------------------------------------------

MADDM_PATCH_SENTINEL=".hepph_maddm_patches_applied_v2"

# Ensure a 2to3 binary is available. Python ships 2to3 up through 3.12; 3.13+
# removed it from the default install and it must be installed separately
# (``pip install 2to3`` or the ``lib2to3`` package).
require_2to3() {
  if command -v 2to3 >/dev/null 2>&1; then
    log "2to3 found: $(command -v 2to3)"
    return 0
  fi
  # Fallback: try `python3 -m lib2to3`.
  if python3 -c 'import lib2to3' >/dev/null 2>&1; then
    log "2to3 not on PATH but python3 -m lib2to3 is available; will use that."
    return 0
  fi
  emit_blocker "MADDM_PATCH_FAILED" "fatal" \
    "2to3 is required to convert MadDM 3.2.13 (Python 2) to Python 3, but neither '2to3' nor 'python3 -m lib2to3' is available." \
    "Install 2to3: on Python 3.12 and earlier it ships with Python; on 3.13+ run 'pip install 2to3' or use a 3.12 interpreter. Then retry /maddm-install."
  return 1
}

# Invoke 2to3 -w -n in-place over the plugin tree.
#
# Why: MadDM 3.2.13 is pure Python 2: ``print X`` statements, ``except E, e:``
# binding, ``raise E, "msg"``, etc. Upstream has not published a Python 3
# release (last tag v3.2.13 from 2023-07-16 is P2, verified against both
# github.com/maddmhep/maddm@v3.2.13 and the MG5-hosted tarball at
# madgraph.phys.ucl.ac.be/Downloads/maddm/maddm_V3.2.13.tar.gz). Without
# this step, ``import PLUGIN.maddm`` fails at module load with a SyntaxError
# before MG5 can dispatch --mode=maddm.
patch_maddm_py3_2to3() {
  local maddm_dir="$1"
  log "Running 2to3 -w -n over $maddm_dir ..."
  local rc=0
  if command -v 2to3 >/dev/null 2>&1; then
    2to3 -w -n "$maddm_dir" >>"$MG5_LOG_TMP" 2>&1 || rc=$?
  else
    python3 -m lib2to3 -w -n "$maddm_dir" >>"$MG5_LOG_TMP" 2>&1 || rc=$?
  fi
  # 2to3 returns non-zero if any file had issues, but partial conversion is
  # still useful. The sweep test in probe_maddm.sh is authoritative.
  if [ "$rc" -ne 0 ]; then
    warn "2to3 returned exit $rc; continuing — sweep test will catch residues."
  fi
  return 0
}

# Replace tabs with 8 spaces in two files 2to3 leaves with mixed
# tab/space indentation (legal in Python 2, TabError in Python 3).
#
# Why: ``init.py`` and ``Templates/plotting.py`` are the only files in the
# upstream tree where 2to3 cannot resolve indentation because the P2 source
# mixed tabs and spaces on consecutive lines inside one suite. Python 3's
# tokenizer refuses the mixture. ``init.py`` is not imported on plugin load
# (only at runtime by specific install helpers) and ``Templates/plotting.py``
# is loaded lazily for plot generation, so a broken-at-install state would
# only surface later; detab them up-front so the failure mode is catch-at-
# install, not catch-at-plot.
patch_maddm_detab_files() {
  local maddm_dir="$1"
  local f
  for f in "$maddm_dir/init.py" "$maddm_dir/Templates/plotting.py"; do
    if [ ! -f "$f" ]; then
      warn "patch_maddm_detab_files: $f not found (upstream layout changed?); skipping."
      continue
    fi
    python3 - "$f" <<'PYEOF'
import sys
p = sys.argv[1]
with open(p) as fh:
    src = fh.read()
with open(p, 'w') as fh:
    fh.write(src.expandtabs(8))
PYEOF
    log "Detabbed $f."
  done
  return 0
}

# Patch ``MGoutput.py`` line 178: add the ``model`` argument to the call of
# ``self.write_source_makefile(...)``.
#
# Why: ``ProcessExporterFortranMEGroup.write_source_makefile`` (MG5's base
# class for MadDM's ``ProcessExporterMadDM``) changed its signature in
# MG5 3.5.6 from ``write_source_makefile(self, writer)`` to
# ``write_source_makefile(self, writer, model)`` (see
# madgraph/iolibs/export_v4.py:2863). MadDM 3.2.13's subclass still calls
# the base with a single argument, so ``output`` aborts with a TypeError
# mid-directory-tree. The surrounding ``copy_template(self, model)`` already
# has ``model`` in scope, so the fix is a one-token insertion.
patch_maddm_mg5_api() {
  local maddm_dir="$1"
  local f="$maddm_dir/MGoutput.py"
  if [ ! -f "$f" ]; then
    warn "patch_maddm_mg5_api: $f not found; skipping."
    return 0
  fi
  local old='self.write_source_makefile(writers.FortranWriter(filename))'
  local new='self.write_source_makefile(writers.FortranWriter(filename), model)'
  if ! grep -qF "$old" "$f"; then
    if grep -qF "$new" "$f"; then
      log "MGoutput.py already has the 2-arg write_source_makefile call; skipping."
      return 0
    fi
    warn "MGoutput.py neither matches the P2 1-arg nor the patched 2-arg call (upstream drift?); leaving as-is."
    return 0
  fi
  # In-place sed with a BSD/GNU-portable tmpfile dance (sed -i '' differs).
  python3 - "$f" "$old" "$new" <<'PYEOF'
import sys
p, old, new = sys.argv[1:4]
with open(p) as fh:
    src = fh.read()
src = src.replace(old, new)
with open(p, 'w') as fh:
    fh.write(src)
PYEOF
  log "Patched MGoutput.py write_source_makefile call (MG5 3.5.6 API)."
  return 0
}

# Patch ``maddm_run_interface.py:MadDMRunCmd.compile`` to touch an empty
# ``include/run.inc`` before calling ``self.maddm_card.write_include_file``.
#
# Why: MG5 3.5.6's ``banner.RunCard.write_include_file`` unconditionally calls
# ``write_autodef`` (banner.py:3343), which in turn unconditionally opens
# ``<output_dir>/run.inc`` (banner.py:3437) *even when* the card has no
# autodef parameters to inject. MadDMCard has zero ``autodef=True`` params,
# and MadDM's output tree never produces a ``run.inc`` (it has its own
# ``maddm.inc``, ``dm_info.inc``, etc.), so the read raises
# ``FileNotFoundError`` and ``launch`` aborts before the relic integrator
# starts. Touching an empty file lets ``write_autodef``'s otherwise-no-op
# path succeed.
patch_maddm_run_inc_touch() {
  local maddm_dir="$1"
  local f="$maddm_dir/maddm_run_interface.py"
  if [ ! -f "$f" ]; then
    warn "patch_maddm_run_inc_touch: $f not found; skipping."
    return 0
  fi
  local marker='# hephaestus: touch run.inc for banner.write_autodef'
  if grep -qF "$marker" "$f"; then
    log "maddm_run_interface.py already has run.inc touch; skipping."
    return 0
  fi
  local old='        if self.in_scan_mode:
            return

        self.maddm_card.write_include_file(pjoin(self.dir_path,'"'"'include'"'"'))'
  local new='        if self.in_scan_mode:
            return

        '"$marker"'
        # MG5 3.5.6 banner.write_autodef opens include/run.inc unconditionally
        # (banner.py:3437); MadDMCard has no autodef params and MadDM output
        # never writes run.inc. Empty file lets the no-op path succeed.
        run_inc = pjoin(self.dir_path, '"'"'include'"'"', '"'"'run.inc'"'"')
        if not os.path.exists(run_inc):
            open(run_inc, '"'"'a'"'"').close()
        self.maddm_card.write_include_file(pjoin(self.dir_path,'"'"'include'"'"'))'
  if ! grep -qF "        self.maddm_card.write_include_file(pjoin(self.dir_path,'include'))" "$f"; then
    warn "maddm_run_interface.py doesn't contain the expected write_include_file call (upstream drift?); leaving as-is."
    return 0
  fi
  python3 - "$f" "$old" "$new" <<'PYEOF'
import sys
p, old, new = sys.argv[1:4]
with open(p) as fh:
    src = fh.read()
src = src.replace(old, new, 1)
with open(p, 'w') as fh:
    fh.write(src)
PYEOF
  log "Patched maddm_run_interface.py to touch run.inc (MG5 3.5.6 banner.write_autodef)."
  return 0
}

# Patch ``MadDMCard.default_setup`` to register a ``custom_fcts`` param.
#
# Why: MG5 3.5.6's ``banner.RunCard.write_include_file`` reads
# ``self["custom_fcts"]`` (banner.py:3345) on every write, but the param is
# only registered on ``RunCardLO`` / ``RunCardNLO`` (banner.py:3995, 5409),
# not on base ``RunCard``. MadDMCard extends ``RunCard`` directly, so the
# access raises ``KeyError: 'custom_fcts'`` during compile. Adding the param
# as an empty list (the LO/NLO default) silences the lookup without altering
# behaviour — MadDM doesn't support custom function overrides.
patch_maddm_custom_fcts() {
  local maddm_dir="$1"
  local f="$maddm_dir/maddm_run_interface.py"
  if [ ! -f "$f" ]; then
    warn "patch_maddm_custom_fcts: $f not found; skipping."
    return 0
  fi
  local marker='# hephaestus: custom_fcts for banner RunCard API'
  if grep -qF "$marker" "$f"; then
    log "MadDMCard already has custom_fcts param; skipping."
    return 0
  fi
  # Anchor on the first add_param inside MadDMCard.default_setup. The string
  # below (print_out / status update) is unique to this method in the file.
  local old='    def default_setup(self):
        """define the default value"""

        self.add_param('"'"'print_out'"'"', False, hidden=True, comment="status update" )'
  local new='    def default_setup(self):
        """define the default value"""

        '"$marker"'
        # MG5 3.5.6 banner.write_include_file reads self["custom_fcts"]
        # (banner.py:3345); registered on RunCardLO/NLO but not base RunCard.
        self.add_param("custom_fcts", [], typelist="str", include=False,
                       comment="list of files containing function that overwrite dummy functions")

        self.add_param('"'"'print_out'"'"', False, hidden=True, comment="status update" )'
  if ! grep -qF '        self.add_param('"'"'print_out'"'"', False, hidden=True, comment="status update" )' "$f"; then
    warn "maddm_run_interface.py MadDMCard.default_setup doesn't start with the expected line (upstream drift?); leaving as-is."
    return 0
  fi
  python3 - "$f" "$old" "$new" <<'PYEOF'
import sys
p, old, new = sys.argv[1:4]
with open(p) as fh:
    src = fh.read()
src = src.replace(old, new, 1)
with open(p, 'w') as fh:
    fh.write(src)
PYEOF
  log "Patched MadDMCard.default_setup to register custom_fcts (MG5 3.5.6 banner API)."
  return 0
}

# Patch ``MadDMCard`` to declare a ``dummy_fct_file = {}`` class attribute.
#
# Why: MG5 3.5.6's ``banner.edit_dummy_fct_from_file`` (banner.py:3160) does
# ``set(self.dummy_fct_file.values())`` at cleanup time, after checking for
# previously-edited dummy fct backups. The attribute is defined on
# ``RunCardLO`` / ``RunCardNLO`` (banner.py:3913, 5290) but not base
# ``RunCard``. The access raises ``AttributeError: 'MadDMCard' object has no
# attribute 'dummy_fct_file'`` during compile. Declaring it as an empty dict
# at class level is the LO/NLO pattern of least resistance — MadDM doesn't
# override any of MadEvent's dummy cut/fct functions so there is nothing to
# track.
patch_maddm_dummy_fct_file() {
  local maddm_dir="$1"
  local f="$maddm_dir/maddm_run_interface.py"
  if [ ! -f "$f" ]; then
    warn "patch_maddm_dummy_fct_file: $f not found; skipping."
    return 0
  fi
  local marker='# hephaestus: dummy_fct_file for banner RunCard API'
  if grep -qF "$marker" "$f"; then
    log "MadDMCard already has dummy_fct_file attr; skipping."
    return 0
  fi
  local old='    filename = '"'"'maddm_card'"'"'
    default_include_file = '"'"'maddm_card.inc'"'"'
    initial_jfactors = {}'
  local new='    filename = '"'"'maddm_card'"'"'
    default_include_file = '"'"'maddm_card.inc'"'"'
    '"$marker"'
    # MG5 3.5.6 banner.edit_dummy_fct_from_file (banner.py:3160) iterates
    # this on every card write; defined on RunCardLO/NLO but not base RunCard.
    dummy_fct_file = {}
    initial_jfactors = {}'
  if ! grep -qF "    filename = 'maddm_card'" "$f"; then
    warn "maddm_run_interface.py MadDMCard class body doesn't match expected layout (upstream drift?); leaving as-is."
    return 0
  fi
  python3 - "$f" "$old" "$new" <<'PYEOF'
import sys
p, old, new = sys.argv[1:4]
with open(p) as fh:
    src = fh.read()
src = src.replace(old, new, 1)
with open(p, 'w') as fh:
    fh.write(src)
PYEOF
  log "Patched MadDMCard to declare dummy_fct_file (MG5 3.5.6 banner API)."
  return 0
}

# Apply all upstream patches in order. Sentinel file makes re-invocation a
# no-op so a subsequent `install` call that hits the idempotency fast-path
# in cmd_install doesn't double-patch an already-converted tree.
#
# When adding a new patch, append the helper call and bump MADDM_PATCH_SENTINEL
# (v1 → v2 → ...) so existing installs get re-patched with the new helpers.
apply_maddm_upstream_patches() {
  local maddm_dir="$1"
  local sentinel="$maddm_dir/$MADDM_PATCH_SENTINEL"
  if [ -f "$sentinel" ]; then
    log "Upstream patches already applied at $sentinel; skipping."
    return 0
  fi
  require_2to3 || return 1
  log "Applying MadDM upstream patches to $maddm_dir ..."
  patch_maddm_py3_2to3        "$maddm_dir" || return 1
  patch_maddm_detab_files     "$maddm_dir" || return 1
  patch_maddm_mg5_api         "$maddm_dir" || return 1
  patch_maddm_run_inc_touch   "$maddm_dir" || return 1
  patch_maddm_custom_fcts     "$maddm_dir" || return 1
  patch_maddm_dummy_fct_file  "$maddm_dir" || return 1
  date -u +%Y-%m-%dT%H:%M:%SZ >"$sentinel"
  log "Upstream patches applied; sentinel written to $sentinel."
  return 0
}

# Scan well-known MadDM plugin locations relative to a possible MG5 root.
scan_candidates() {
  local roots=()
  local mg5_bin
  mg5_bin="$(config_get madgraph_path)"
  if [ -n "$mg5_bin" ] && [ -x "$mg5_bin" ]; then
    roots+=("$(mg5_root_from_bin "$mg5_bin")")
  fi
  roots+=("$HOME/MG5_aMC" "$HOME/software/MG5_aMC" "/usr/local/MG5_aMC")

  local root
  for root in "${roots[@]}"; do
    [ -d "$root" ] || continue
    if [ -f "$root/PLUGIN/maddm/__init__.py" ]; then
      echo "$root/PLUGIN/maddm"
      return 0
    fi
  done
  return 1
}

# Record both maddm_path and maddm_version + timestamp in config.
record_maddm_config() {
  local maddm_dir="$1"
  local version="$2"
  local installed_at
  installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  config_merge \
    maddm_path "$maddm_dir" \
    maddm_version "$version" \
    maddm_installed_at "$installed_at"
  log "Recorded maddm_path=$maddm_dir version=$version"
}

# Run probe_maddm.sh and echo the version. On failure, emits a blocker and exits.
run_probe_or_block() {
  local maddm_dir="$1"
  local mg5_root="${2:-}"
  local version
  if ! version="$(bash "$SCRIPT_DIR/probe_maddm.sh" "$maddm_dir" "$mg5_root" 2>>"$MG5_LOG_TMP")"; then
    emit_blocker "MADDM_SMOKE_TEST_FAILED" "fatal" \
      "MadDM probe failed for plugin dir $maddm_dir. See $MG5_LOG_TMP for details." \
      "Check that $maddm_dir/__init__.py exists and that $mg5_root/bin/maddm is executable."
    exit 15
  fi
  echo "$version"
}

# ---------------------------------------------------------------------------
# cmd_detect
# ---------------------------------------------------------------------------
cmd_detect() {
  local path version
  path="$(config_get maddm_path)"

  if [ -n "$path" ] && [ -f "$path/__init__.py" ]; then
    local mg5_root=""
    local mg5_bin
    mg5_bin="$(config_get madgraph_path)"
    if [ -n "$mg5_bin" ] && [ -x "$mg5_bin" ]; then
      mg5_root="$(mg5_root_from_bin "$mg5_bin")"
    fi
    version="$(bash "$SCRIPT_DIR/probe_maddm.sh" "$path" "$mg5_root" 2>/dev/null || echo "")"
    if [ -n "$version" ]; then
      printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
      return 0
    fi
  fi

  local found
  if found="$(scan_candidates)"; then
    printf '{"status":"found","path":"%s"}\n' "$found"
    return 0
  fi

  printf '{"status":"missing"}\n'
}

# ---------------------------------------------------------------------------
# cmd_use_path
# ---------------------------------------------------------------------------
cmd_use_path() {
  local path="${1:-}"
  [ -n "$path" ] || {
    emit_blocker "MADDM_PATH_INVALID" "fatal" \
      "use-path requires a path argument (the MadDM plugin directory containing __init__.py)."
    exit 16
  }

  # Expand ~ to $HOME.
  path="${path/#\~/$HOME}"

  if [ ! -d "$path" ] || [ ! -f "$path/__init__.py" ]; then
    emit_blocker "MADDM_PATH_INVALID" "fatal" \
      "Path $path is not a valid MadDM plugin directory (missing __init__.py)." \
      "Provide the absolute path to the directory that contains __init__.py (typically <MG5_ROOT>/PLUGIN/maddm/)."
    exit 16
  fi

  # Derive MG5 root (two levels up from <MG5_ROOT>/PLUGIN/maddm).
  local mg5_root
  mg5_root="$(cd "$path/../.." && pwd)"

  # Bring an arbitrary existing tree up to the patched state before probing.
  # Common case: user points at a tree they installed manually with MG5's
  # `install maddm`, which ships upstream P2 content unchanged.
  : > "$MG5_LOG_TMP"
  if ! apply_maddm_upstream_patches "$path"; then
    emit_blocker "MADDM_PATCH_FAILED" "fatal" \
      "Failed to apply upstream patches to existing MadDM install at $path." \
      "Inspect $MG5_LOG_TMP. Patches are documented in SKILL.md § Upstream patches."
    exit 13
  fi

  # Probe and record.
  local version
  version="$(run_probe_or_block "$path" "$mg5_root")"
  record_maddm_config "$path" "$version"
  printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
}

# ---------------------------------------------------------------------------
# Install primary path: drive `mg5_aMC` with an `install maddm` command script.
# Returns 0 on success, 1 on failure.
# ---------------------------------------------------------------------------
try_mg5_install() {
  local mg5_bin="$1"
  log "Primary install path: running '$mg5_bin -f <script>' with 'install maddm' ..."

  cat >"$MG5_SCRIPT_TMP" <<'EOF'
install maddm
exit
EOF

  if "$mg5_bin" -f "$MG5_SCRIPT_TMP" >"$MG5_LOG_TMP" 2>&1; then
    rm -f "$MG5_SCRIPT_TMP"
    log "MG5 'install maddm' completed successfully."
    return 0
  fi
  warn "MG5 'install maddm' failed. See $MG5_LOG_TMP (last lines will be shown below)."
  tail -n 30 "$MG5_LOG_TMP" >&2 || true
  rm -f "$MG5_SCRIPT_TMP"
  return 1
}

# ---------------------------------------------------------------------------
# Install fallback: git clone maddmhep/maddm into <MG5_ROOT>/PLUGIN/maddm.
# Returns 0 on success, 1 on failure.
# ---------------------------------------------------------------------------
try_git_install() {
  local mg5_root="$1"
  local plugin_parent="$mg5_root/PLUGIN"
  local plugin_dir="$plugin_parent/maddm"

  mkdir -p "$plugin_parent"

  if [ -e "$plugin_dir" ]; then
    warn "Existing $plugin_dir will be removed before git clone fallback."
    rm -rf "$plugin_dir"
  fi

  log "Fallback: git clone $MADDM_GIT_URL (tag $MADDM_GIT_TAG) → $plugin_dir ..."
  if ! command -v git >/dev/null 2>&1; then
    warn "git not found; fallback path cannot proceed."
    return 1
  fi

  if git clone --depth 1 --branch "$MADDM_GIT_TAG" "$MADDM_GIT_URL" "$plugin_dir" \
        >>"$MG5_LOG_TMP" 2>&1; then
    log "git clone at tag $MADDM_GIT_TAG succeeded."
  else
    warn "Tag clone failed; trying default branch."
    rm -rf "$plugin_dir"
    if ! git clone --depth 1 "$MADDM_GIT_URL" "$plugin_dir" >>"$MG5_LOG_TMP" 2>&1; then
      return 1
    fi
  fi

  # Install launcher shim at <MG5_ROOT>/bin/maddm.
  if [ -f "$plugin_dir/maddm" ]; then
    cp "$plugin_dir/maddm" "$mg5_root/bin/maddm"
    chmod +x "$mg5_root/bin/maddm"
    log "Copied launcher to $mg5_root/bin/maddm."
  else
    warn "No launcher file found at $plugin_dir/maddm; smoke test will reflect this."
  fi

  return 0
}

# ---------------------------------------------------------------------------
# cmd_install
# ---------------------------------------------------------------------------
cmd_install() {
  # Idempotency: if already configured and probe-passes, just re-emit status.
  # Patches are sentinel-guarded so this is also the place where a user who
  # re-runs `install` on a pre-existing install-script-era tree gets it
  # upgraded to the patched state without needing to delete first.
  local existing
  existing="$(config_get maddm_path)"
  if [ -n "$existing" ] && [ -f "$existing/__init__.py" ]; then
    : > "$MG5_LOG_TMP"
    if ! apply_maddm_upstream_patches "$existing"; then
      emit_blocker "MADDM_PATCH_FAILED" "fatal" \
        "Failed to upgrade existing MadDM install at $existing to the patched state." \
        "Inspect $MG5_LOG_TMP or delete $existing and re-run /maddm-install install for a clean slate."
      exit 13
    fi
    local mg5_bin mg5_root=""
    mg5_bin="$(config_get madgraph_path)"
    [ -n "$mg5_bin" ] && [ -x "$mg5_bin" ] && mg5_root="$(mg5_root_from_bin "$mg5_bin")"
    local ver
    ver="$(bash "$SCRIPT_DIR/probe_maddm.sh" "$existing" "$mg5_root" 2>/dev/null || echo "")"
    if [ -n "$ver" ]; then
      log "MadDM already configured at $existing (v$ver); no-op."
      printf '{"status":"configured","path":"%s","version":"%s"}\n' "$existing" "$ver"
      return 0
    fi
  fi

  local mg5_bin mg5_root
  mg5_bin="$(config_get madgraph_path)"
  mg5_root="$(require_mg5)"   # exits with blocker if MG5 missing or too old
  require_gfortran            # exits with GFORTRAN_ABSENT if absent
  check_python_compat "$mg5_bin"

  check_disk 1 2

  # Warn if the MG5_ROOT filesystem has <500 MB (MadDM + templates + data ~200 MB).
  local avail_mb
  avail_mb=$(df -m "$mg5_root" 2>/dev/null | awk 'NR==2 {print $4}')
  if [ -n "$avail_mb" ] && [ "$avail_mb" -lt 500 ]; then
    warn "Only ${avail_mb} MB free under $mg5_root; MadDM needs ~200 MB."
  fi

  : > "$MG5_LOG_TMP"

  # Primary: run `install maddm` via MG5.
  if ! try_mg5_install "$mg5_bin"; then
    warn "Primary install path failed; attempting git-clone fallback."
    if ! try_git_install "$mg5_root"; then
      emit_blocker "MADDM_DOWNLOAD_FAILED" "fatal" \
        "Both 'mg5_aMC install maddm' and 'git clone maddmhep/maddm' failed. See $MG5_LOG_TMP." \
        "Check network connectivity to launchpad.net and github.com. Last log lines may indicate the root cause."
      exit 12
    fi
  fi

  local maddm_dir="$mg5_root/PLUGIN/maddm"
  if [ ! -f "$maddm_dir/__init__.py" ]; then
    emit_blocker "MADDM_SMOKE_TEST_FAILED" "fatal" \
      "Install reported success but $maddm_dir/__init__.py is missing." \
      "Inspect $MG5_LOG_TMP and the $maddm_dir directory contents."
    exit 15
  fi

  # Upstream MadDM 3.2.13 is Python 2 and has an MG5 3.5.6 API mismatch.
  # Apply patches before the probe so the import-sweep in probe_maddm.sh
  # sees a loadable tree.
  if ! apply_maddm_upstream_patches "$maddm_dir"; then
    emit_blocker "MADDM_PATCH_FAILED" "fatal" \
      "Failed to apply upstream-bug patches to MadDM plugin at $maddm_dir." \
      "Inspect $MG5_LOG_TMP. The patches are documented in plugins/hep-ph-toolkit/skills/maddm-install/SKILL.md § Upstream patches; they can be applied manually and the install re-validated with '/maddm-install validate'."
    exit 13
  fi

  local version
  version="$(run_probe_or_block "$maddm_dir" "$mg5_root")"

  record_maddm_config "$maddm_dir" "$version"
  log "MadDM v${version} installed at $maddm_dir."
  printf '{"status":"installed","path":"%s","version":"%s"}\n' "$maddm_dir" "$version"
}

# ---------------------------------------------------------------------------
# cmd_validate — re-run probe against currently-configured install.
# ---------------------------------------------------------------------------
cmd_validate() {
  local path
  path="$(config_get maddm_path)"
  if [ -z "$path" ]; then
    emit_blocker "MADDM_PATH_INVALID" "fatal" \
      "No maddm_path in config; nothing to validate." \
      "Run /maddm-install detect or /maddm-install install first."
    exit 16
  fi
  local mg5_bin mg5_root=""
  mg5_bin="$(config_get madgraph_path)"
  [ -n "$mg5_bin" ] && [ -x "$mg5_bin" ] && mg5_root="$(mg5_root_from_bin "$mg5_bin")"

  local version
  version="$(run_probe_or_block "$path" "$mg5_root")"
  printf '{"status":"configured","path":"%s","version":"%s"}\n' "$path" "$version"
}

# ---------------------------------------------------------------------------
# usage / main
# ---------------------------------------------------------------------------
usage() {
  cat >&2 <<'EOF'
Usage: install.sh <command> [args]

Commands:
  detect              Print JSON state of existing MadDM install (no side effects).
  use-path <dir>      Register an existing MadDM plugin dir (contains __init__.py).
  install [dir]       Run `mg5_aMC` with `install maddm`; falls back to git clone
                      of maddmhep/maddm. Requires madgraph_path in config.
  validate            Re-run the smoke test against the currently-configured MadDM.

Env overrides:
  HEPPH_MADDM_VERSION    Pin a specific MadDM release (default: 3.2.13)
  XDG_CONFIG_HOME        Override config directory (test isolation)
EOF
  exit 2
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    detect)   cmd_detect ;;
    use-path) cmd_use_path "${1:-}" ;;
    install)  cmd_install "${1:-}" ;;
    validate) cmd_validate ;;
    *)        usage ;;
  esac
}

main "$@"
