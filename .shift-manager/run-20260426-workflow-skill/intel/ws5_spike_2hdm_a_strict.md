# SPIKE ERROR

EXCEPTION: ModelNotInRegistry: Model '2hdm-a' not found in constraints.yaml models block. Known models: ['singlet-doublet', 'dark-su3', 'two-hdm-a']

```
Traceback (most recent call last):
  File "/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260426-workflow-skill/impl/ws5_spike.py", line 85, in <module>
    report = route(
  File "/Users/yianni/Projects/hep-ph-agents/plugins/workflow/skills/model-router/scripts/model_router/orchestrator.py", line 88, in route
    ctx: LoadedContext = _load_mod.stage_p0_load(
  File "/Users/yianni/Projects/hep-ph-agents/plugins/workflow/skills/model-router/scripts/model_router/stages/load.py", line 192, in stage_p0_load
    raise ModelNotInRegistry(
model_router.types.ModelNotInRegistry: Model '2hdm-a' not found in constraints.yaml models block. Known models: ['singlet-doublet', 'dark-su3', 'two-hdm-a']

```
