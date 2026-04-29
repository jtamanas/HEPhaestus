#!/usr/bin/env bash
# Vendored upstream patches for micrOMEGAs.
#
# Mirrors the convention in plugins/hep-ph-toolkit/skills_shared/installs/maddm/
# scripts/install.sh — each `patch_micromegas_*` function fixes one specific
# upstream defect, idempotency is gated by a sentinel file, and the rationale
# for every patch lives in references/micromegas-workarounds.md.
#
# When upstream micrOMEGAs ships a release that fixes one of these, delete
# the corresponding function and bump MICROMEGAS_PATCH_SENTINEL.

MICROMEGAS_PATCH_SENTINEL=".hepph_micromegas_patches_applied_v1"

# Adds `.NOTPARALLEL:` to the CalcHEP_src/c_source/*/Makefile files whose
# archive-member rule races under `make -j`. See workarounds doc § 1.
patch_micromegas_calchep_archive_race() {
  local install_dir="$1"
  local mk f
  for mk in chep_crt dynamicME getmem polynom ntools strfun num symb service2 SLHAplus; do
    f="$install_dir/CalcHEP_src/c_source/$mk/Makefile"
    if [ ! -f "$f" ]; then
      warn "patch_micromegas_calchep_archive_race: $f not found (upstream layout changed?); skipping."
      continue
    fi
    grep -q "^\.NOTPARALLEL:" "$f" && continue
    printf '.NOTPARALLEL:\n\n%s' "$(cat "$f")" > "$f.tmp" && mv "$f.tmp" "$f"
  done
}

# Apply all upstream patches in order. Sentinel makes re-invocation a no-op.
apply_micromegas_upstream_patches() {
  local install_dir="$1"
  local sentinel="$install_dir/$MICROMEGAS_PATCH_SENTINEL"
  if [ -e "$sentinel" ]; then
    log "micrOMEGAs upstream patches already applied (sentinel: $sentinel)."
    return 0
  fi
  log "Applying micrOMEGAs upstream patches..."
  patch_micromegas_calchep_archive_race "$install_dir"
  touch "$sentinel"
  log "Patches applied; sentinel written: $sentinel"
}
