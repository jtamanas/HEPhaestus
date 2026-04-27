# T4_IMPL_NOTE — sd-T4 Per-run schema validation (×5)

## Task

sd-T4: Validate each `summary.json` (runs 1-5) against schema v1.1 using `validate_one.py`.

## Commands executed

Working directory: `/Users/yianni/Projects/hep-ph-agents-sd-playtest-r2/.shift-manager/run-20260425-030153/workstreams/singlet-doublet/playtest`

```
python3 validate_one.py runs/run-1/demo_output/singlet-doublet/summary.json
python3 validate_one.py runs/run-2/demo_output/singlet-doublet/summary.json
python3 validate_one.py runs/run-3/demo_output/singlet-doublet/summary.json
python3 validate_one.py runs/run-4/demo_output/singlet-doublet/summary.json
python3 validate_one.py runs/run-5/demo_output/singlet-doublet/summary.json
```

## Per-run results

| run   | exit | first_line                                                              |
|-------|------|-------------------------------------------------------------------------|
| run-1 | 0    | [PASS] runs/run-1/demo_output/singlet-doublet/summary.json              |
| run-2 | 0    | [PASS] runs/run-2/demo_output/singlet-doublet/summary.json              |
| run-3 | 0    | [PASS] runs/run-3/demo_output/singlet-doublet/summary.json              |
| run-4 | 0    | [PASS] runs/run-4/demo_output/singlet-doublet/summary.json              |
| run-5 | 0    | [PASS] runs/run-5/demo_output/singlet-doublet/summary.json              |

## jq gate

```
jq -e 'all(.runs[]; .exit == 0)' schema-validation.json
```
Exit: 0 (true). All 5 pass.

## Verdict

**PASS** — 5/5 `validate_one.py` calls exit 0. Schema v1.1 validation clear.

## Artefacts produced

- `schema-validation.json` — consolidated per-run exit code + first_line
- `T4_IMPL_NOTE.md` (this file)

## Worktree note

`validate_one.py` was NOT modified (sd-T1 closed it). `_shared/` was NOT touched.
