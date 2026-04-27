# synthetic-plan.md — model-x end-to-end check_plan fixture

## T-MX-1 — Run model-x and verify

Run the synthetic model-x skill:

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

Check summary.json model field:

```bash
jq -e '.model == "model-x"' summary.json
```

Also verify provenance.json exists:

```bash
test -f provenance.json
```
