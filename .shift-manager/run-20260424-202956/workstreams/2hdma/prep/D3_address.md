# D3 — env.json config error + mg5/maddm versions unavailable

**Status**: FIXED
**Severity**: blocker for PT1
**Round**: 2 (sonnet address)

## What was wrong
`env.json` showed `config: {error: "config.json not found"}` and `mg5_version="unavailable"`, `maddm_version="unavailable"` because `capture_env.py` only looked for `config.json` at the repo root, which does not exist.

The actual config lives at `~/.config/hep-ph-agents/config.json` (XDG path, 2.5k, verified readable).

## Fix applied

### 1. XDG-first config discovery
Added `_find_config_path()` to `capture_env.py` that searches in order:
1. `$XDG_CONFIG_HOME/hep-ph-agents/config.json`
2. `$HOME/.config/hep-ph-agents/config.json`  ← hits here on this machine
3. repo-root `config.json` (legacy fallback)

### 2. mg5/maddm version resolution
- `get_mg5_version()` now accepts `cfg` dict and first checks `cfg["madgraph_version"]` (present in XDG config as `"3.5.6"`).
- `get_maddm_version()` now accepts `cfg` dict and first checks `cfg["maddm_version"]` (present as `"3.2.13"`).
- Both also handle `madgraph_path` pointing to the binary directly (not a directory), via `_resolve_mg5_bin()`.
- Added `maddm_path` from config as a direct probe path for MadDM.

### 3. env.json regenerated
After fix:
- `config._config_source = "/Users/yianni/.config/hep-ph-agents/config.json"`
- `mg5_version = "3.5.6"`
- `maddm_version = "3.2.13"`
- `sarah_version = "4.15.3"` (D2 fix also applied)

## Files changed
- `plugins/hep-ph-demo/skills/2hdm-a/scripts/capture_env.py`
- `demo_output/2hdm-a/playtest_log/env.json` (regenerated)
