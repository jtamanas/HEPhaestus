# shared/install-helpers

Single source of truth for install helpers shared across all hephaestus plugins.

## Why this exists

The hep-ph-demo plugin originally contained `_common.sh` locally.  Once three
other plugins (model-building W1–W5) needed identical helpers the rule-of-three
was exceeded.  W0 promoted the file here and replaced the original with a shim.

## Files

| File | Purpose |
|------|---------|
| `_common.sh` | Bash helpers: exit codes, logging, disk check, checksum, download, config r/w |
| `config_helpers.py` | Python mirror of `config_get` / `config_merge`; atomic write with fsync |

## Sourcing pattern

### model-building skills (script at `plugins/hep-ph-toolkit/skills/<skill>/scripts/`)

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
. "$SHARED_COMMON"
```

### hep-ph-demo scripts (script at `plugins/hep-ph-toolkit/skills/install/scripts/`)

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
```

The `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` file is a one-line
shim that sources this path.  It exists only to avoid breaking any external
consumer that sources the hep-ph-demo path directly.

## Python import

```python
import sys
sys.path.insert(0, "/path/to/plugins/shared/install-helpers")
from config_helpers import load_config, merge_config, register_model, get_model
```

Or via `PYTHONPATH`:
```bash
PYTHONPATH="$SCRIPT_DIR/../../../../shared/install-helpers" python3 my_script.py
```

## Ownership

Only `workstream/w0-shared-contracts` (W0) edits these files.
W1–W6 are consumers.  If a downstream workstream needs a new helper, it must
be added via a W0 patch commit on `main` before the downstream branch merges.

## Test isolation

All tests must set:
```bash
export HEPPH_STATE_ROOT="$(mktemp -d -t hepph-state-XXXXXX)"
export XDG_CONFIG_HOME="$(mktemp -d -t hepph-cfg-XXXXXX)"
```
and call `config_helpers._reload_roots()` after setting env vars in Python.
