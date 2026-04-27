# CONVENTIONS — Adding a New BSM Model (6-Step Recipe)

This document specifies the authoritative 6-step protocol for adding a new BSM model
to the hep-ph-demo plugin. Follow these steps exactly. No edits to `_shared/` or
`tools/` are required.

---

## Step 1 — Create skill directory

```bash
mkdir plugins/hep-ph-toolkit/skills/<new-model>
```

Drop a `SKILL.md` describing the model, constraints, and the parameter space.

---

## Step 2 — Write per-skill summary schema

Create `<new-model>/summary.schema.json` as an `allOf` composition:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "allOf": [
    {"$ref": "../_shared/summary.core.schema.json"},
    {
      "type": "object",
      "properties": {
        "model": {"const": "<new-model>"}
      }
    }
  ]
}
```

Add model-specific `gate_check` fields or other extensions in the second `allOf` element.

---

## Step 3 — Author at least one benchmark fixture

Create `<new-model>/benchmarks/<name>/expectations.json` with paper-cited numeric values.
Use the universal expectations schema as a template
(`singlet-doublet/benchmarks/canonical-2026/expectations.schema.json`):

```json
{
  "schema_version": "1",
  "benchmark_id": "<name>",
  "model": "<new-model>",
  "parameter_point": {"<param>": <value>},
  "expectations": {
    "omega_h2": {"central": <value>, "band": [<lo>, <hi>], "tolerance": "<str>"}
  },
  "source": {"paper": "arXiv:XXXX.XXXXX", "section": "III", "commit": "<git-sha>"}
}
```

---

## Step 4 — Wire summary.json writer in SKILL.md

In your SKILL.md Step 4e, instruct writers to:
- Set `model: "<new-model>"`
- Set `benchmark_id: "<name>"`
- Write `provenance.json` **BEFORE** `summary.json` (atomic-write invariant)
- Set `provenance_ref: "provenance.json"` in summary.json

---

## Step 5 — Run the validator

```bash
python -c "import json, jsonschema; \
  jsonschema.validate( \
    json.load(open('<path-to-example-summary.json>')), \
    json.load(open('plugins/hep-ph-toolkit/skills/_shared/summary.core.schema.json')))"

python -c "import json, jsonschema; \
  jsonschema.validate( \
    json.load(open('<path-to-example-provenance.json>')), \
    json.load(open('plugins/hep-ph-toolkit/skills/_shared/provenance.schema.json')))"
```

Both must exit 0. No edits to `_shared/` or `tools/` required.

---

## Step 6 — Run plan lint

```bash
python tools/check_plan.py <plan-md-for-your-skill>
```

Must exit 0. If a gate references `omega_h2` with a numeric literal, add:
```
# fixture: plugins/hep-ph-toolkit/skills/<new-model>/benchmarks/<name>/expectations.json
```
within 3 lines above the gate.

---

## Proof of forward-compatibility

This recipe is validated by the `_test_model_x` synthetic skill. Run:

```bash
python -c "import json, jsonschema; \
  jsonschema.validate( \
    json.load(open('plugins/hep-ph-toolkit/skills/_test_model_x/fixtures/example-summary.json')), \
    json.load(open('plugins/hep-ph-toolkit/skills/_shared/summary.core.schema.json')))"

python -c "import json, jsonschema; \
  jsonschema.validate( \
    json.load(open('plugins/hep-ph-toolkit/skills/_test_model_x/fixtures/example-provenance.json')), \
    json.load(open('plugins/hep-ph-toolkit/skills/_shared/provenance.schema.json')))"
```

Both should exit 0 without any changes to `_shared/` or `tools/`.
