# MG5 model-import gotchas

Non-obvious failure modes when importing UFO models into MG5 for
downstream `/madgraph` or `/maddm` use. Mirrors the catalogue style of
`plugins/hep-ph-toolkit/skills/sarah-build/references/sarah-workarounds.md`.

---

## 1. `import model <name>` by bare name can resolve to a `$MG5_HOME/models/` stub

- **Symptom:** `import model SingletDoublet` (or any bare name matching
  a dir in `$MG5_HOME/models/`) succeeds silently, but downstream
  `generate chi1 chi1 > all all` produces wrong processes or no
  processes — or `define darkmatter chi1` raises
  `DMError: chi1 is not a valid particle for the model.` because the
  resolved UFO has a completely different particle set.
- **Cause:** MG5's `import model` search order looks in
  `$MG5_HOME/models/` before consulting any absolute path. If a dir
  with the same (or suffix-matching, e.g. `__REAL`) name already exists
  there — from a prior unrelated install, a restriction copy, or a
  half-finished import — MG5 loads *that* UFO instead. The name
  collision is silent. For `hephaestus` specifically, the
  `$MG5_HOME/models/SingletDoublet__REAL/` tree found on one dev box
  contains `Fsdm`/`~vdm`/`Fvdm` particles (PDGs 999000008–10) — a
  DMsimp-like scalar/vector DM UFO, nothing to do with the
  singlet-doublet fermion model we build via SARAH.
- **Mitigation:** Always pass the **absolute path** to the SARAH-output
  UFO directory to `import model`, never the bare name:
  ```
  import model /Users/.../hephaestus/models/singlet_doublet/sarah_output/UFO/SingletDoublet
  ```
  The `$STATE_ROOT/models/<model>/ufo` symlink (produced by
  `/sarah-build`) is a stable pointer. `config.json`'s
  `models.<name>.ufo` field holds this path; read it at driver time.
- **Where:** — (MG5-level, not hephaestus-level); driver scripts in
  `demo_output/.../drive.py` and `plugins/hep-ph-toolkit/skills/maddm/scripts/maddm_run.py`
  should read `config.json` rather than pass a bare name.

---

## 2. MG5 lowercases UFO particle names at import

- **Symptom:** UFO declares `Chi1 = Particle(...)`, but after
  `import model`, commands referring to `Chi1` (uppercase) fail while
  `chi1` (lowercase) works. `define darkmatter Chi1` →
  `DMError: Chi1 is not a valid particle for the model.`
- **Cause:** The log line `INFO: Change particles name to pass to MG5
  convention` does a case normalisation: MG5's convention is
  lowercase-with-tilde for antiparticles (e.g. `chi1`, `chi1~`), and
  UFO `name` fields are rewritten to match. The UFO source file is not
  modified; only the in-memory particle registry.
- **Mitigation:** Use the lowercased name when referring to particles
  in MG5/MadDM commands. Cross-reference: see
  `plugins/hep-ph-toolkit/skills/maddm-install/references/maddm-workarounds.md`
  § 11 for the analogous trap on `define darkmatter`.
- **Where:** — (upstream convention; unchanged since MG5 2.x).
