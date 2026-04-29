# `_shared/installs/`

Reference docs and scripts for every external tool hephaestus drives. Each
`<tool>/` directory carries:

- `INSTALL.md` — what to install, prerequisites, blocker codes, smoke test.
  No skill frontmatter; this is a reference, not an invokable skill.
- `detect.sh` — cheap "is this tool ready" probe. Exit 0 = ready, non-zero =
  not ready. Two-tier: config fast path (~5 ms) then slow binary probe.
- `install.sh` — full installer. Returns 0 on success, documented non-zero
  codes on `activation_required`, `download_failed`, `build_failed`, etc.
  See the per-tool `INSTALL.md` for the code table.
- `tests/` — unit tests for the tool's scripts (kept beside the scripts).

Runner skills (`sarah-build`, `formcalc`, `maddm`, …) `bash detect.sh` at the
top of their `SKILL.md` and, on non-zero exit, load `INSTALL.md` into
context and walk the user through it. `/install` (the bundle front door)
drives the same scripts.

`_detect_common.sh` is the shared config fast-path helper used by every
`<tool>/detect.sh`. See `tests/test_detect_common.sh` for the contract.
