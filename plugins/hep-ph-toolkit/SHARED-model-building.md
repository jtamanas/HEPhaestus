# model-building shared conventions

Normative cross-skill reference for all model-building workstreams (W0–W6).
See `plugins/shared/install-helpers/` for the shared Bash/Python config helpers.

---

## State and config roots

| Purpose | Path | Test override |
|---------|------|---------------|
| Per-model state (build outputs, SLHA runs) | `~/.local/share/hephaestus/` | `HEPPH_STATE_ROOT` |
| Config file directory | `~/.config/hephaestus/` | `XDG_CONFIG_HOME` |
| Config file | `~/.config/hephaestus/config.json` | derived from `XDG_CONFIG_HOME` |

Python computation (in `config_helpers.py`):
```python
STATE_ROOT = Path(os.environ.get("HEPPH_STATE_ROOT")
                  or Path.home() / ".local/share/hephaestus")
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME")
                  or Path.home() / ".config") / "hephaestus"
CONFIG_PATH = CONFIG_DIR / "config.json"
```

Base tool installs (`$HOME/SARAH`, `$HOME/SPheno`) are **not** governed by
`HEPPH_STATE_ROOT`.  Only `models/` lives under `STATE_ROOT`.

---

## Model-name regex

```
^[a-z][a-z0-9_]{1,30}$
```

- Must start with a lowercase letter.
- Followed by 1–30 characters that are lowercase letters, digits, or `_`.
- Enforced at `validate_spec.py` and at `register_model()`.

Examples: `dark_su3`, `singlet_doublet`, `sm_extended`.

Invalid: `2hdm` (leading digit), `DarkSU3` (uppercase), `x` (too short at length 1
— wait: the regex requires at least 2 chars total: `[a-z]` + `{1,30}` ⇒ min 2).

---

## Timestamps

UTC ISO 8601 with `Z` suffix: `YYYY-MM-DDTHH:MM:SSZ`.

- Shell: `date -u +%Y-%m-%dT%H:%M:%SZ`
- Python: `datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`

---

## Env-var overrides

The following variables are defined here and noted with their intended consumers.
W0 itself reads only `HEPPH_STATE_ROOT`, `XDG_CONFIG_HOME`, and `NO_NETWORK`;
`HEPPH_SARAH_VERSION` and `HEPPH_SPHENO_VERSION` are defined here and consumed
by the W1 and W2 install scripts respectively — W0 does not read them.

| Variable | Purpose | Consumed by | Default |
|----------|---------|-------------|---------|
| `HEPPH_STATE_ROOT` | Test-isolation for per-model state | W0, W3, W4, W5 Python | `~/.local/share/hephaestus` |
| `XDG_CONFIG_HOME` | Test-isolation for config file | W0 + all | `~/.config` |
| `HEPPH_SARAH_VERSION` | Override pinned SARAH version | W1 `install_sarah.sh` | `4.15.3` |
| `HEPPH_SPHENO_VERSION` | Override pinned SPheno version | W2 `install_spheno.sh` | `4.0.5` |
| `NO_NETWORK` | Skip integration tests needing network | W0 (smoke), W1, W2, W5 integration | unset |

`HEPPH_WOLFRAM_KERNEL` is NOT implemented.

Version-override pattern (bash):
```bash
SARAH_VERSION="${HEPPH_SARAH_VERSION:-4.15.3}"
SARAH_URL="https://sarah.hepforge.org/downloads/SARAH-${SARAH_VERSION}.tar.gz"
```

---

## Cache keys

### W3 (sarah-build)

File: `$STATE_ROOT/models/<name>/.sarah_build_key`

Contents (single line):
```
sha256(<spec.yaml bytes>, hex)=<sarah_version>
```

Example: `a3f2c1...=4.15.3`

Missing key or mismatch → rebuild.  `--force` forces rebuild regardless.

### W4 (spheno-build)

File: `$STATE_ROOT/models/<name>/spheno_bin/.build_key`

Contents (single line):
```
sha256(<spec.yaml bytes>, hex)=<sarah_version>=<spheno_version>
```

---

## Three-state blocker contract

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

Three modes:

### `fatal`
```json
{
  "code": "SARAH_DOWNLOAD_FAILED",
  "mode": "fatal",
  "message": "Human-readable description.",
  "context": {},
  "user_instruction": "Optional: exact shell command or action for user."
}
```

### `recoverable`
```json
{
  "code": "SPHENO_SPECTRUM_PROBLEM",
  "mode": "recoverable",
  "message": "Human-readable description."
}
```

### `reference_only`
```json
{
  "status": "reference_only",
  "reference_method": "analytic computation via FeynCalc",
  "caveats": ["result not from SARAH", "no cross-check performed"]
}
```

`reference_only` does NOT carry `code`/`message`/`context`; those fields
are exclusive to `fatal`/`recoverable`.

Known `fatal` codes: `SARAH_DOWNLOAD_FAILED`, `SARAH_SMOKE_TEST_FAILED`,
`SARAH_OUTPUT_MISSING`, `ANOMALY_CANCELLATION_FAILED`, `MODELSPEC_INVALID`,
`WOLFRAM_KERNEL_ABSENT`, `GFORTRAN_ABSENT`, `SPHENO_DOWNLOAD_FAILED`,
`SPHENO_BASE_BUILD_FAILED`, `SPHENO_PATH_INVALID`, `SPHENO_COMPILE_FAILED`,
`SPHENO_NO_OUTPUT`.

Known `recoverable` codes: `SPHENO_SPECTRUM_PROBLEM`, `SPHENO_RGE_NONCONVERGENT`.

---

## Config-key alignment

| hep-ph-demo key (existing) | Meaning |
|---------------------------|---------|
| `wolfram_engine_path` | Path to the `wolframscript` binary |
| `sarah_path` | Path to the SARAH package directory (contains `SARAH.m`) |
| `spheno_path` | Path to the SPheno base build directory |
| `mg5_path` | Path to the MadGraph5 `bin/mg5_aMC` binary |
| `models` | Dict of registered models (added by W3/W4/W5) |
| `last_configured` | UTC ISO 8601 timestamp of last config write |
| `python` | Path to `python3` binary |

W0's `config_migration.py --check` asserts that none of these keys are
renamed or removed by migration.

---

## Templates

`str.format` only.  No Jinja2.  Lists are pre-joined in the calling Python to
a single string token before `template.format(**tokens)`.  No conditionals in
templates.

---

## §X SARAH-name probe result (filled by W3)

*Reserved.*  W3 Day-1 probe fills this section with the verified SARAH
canonicalization rule.  Until that probe runs, the provisional rule is:

```python
def modelspec_name_to_sarah(name: str) -> str:
    return "".join(w.capitalize() for w in name.split("_"))
```

W3 amends `plugins/hep-ph-toolkit/skills/_shared/sarah_name.py` if the
observed rule diverges from this provisional one, and updates this section.
