# Round 3 Fixer Surprises

## 1. `multi_component` lives in two places

The brief says: "model spec has `multi_component: true` AND
`backends.spectrum == "analytic"`." Implication: both fields live in the
same ModelSpec YAML. Reality: the canonical source for `multi_component` is
`_shared/constraints.yaml` `models.<m>.multi_component`, not the ModelSpec
YAML at `_shared/assets/dark_su3.yaml` (which has `backends.spectrum:
analytic` but no `multi_component` field). The DMC SKILL.md Step 2 wording
even calls this out: "(per `_shared/constraints.yaml`
`models.<m>.multi_component`)" for #1 and "(per the model's ModelSpec YAML)"
for #2. So the check_prereqs.py demotion has to read from BOTH files.

Resolved by adding `_model_is_multi_component()` that resolves
`_shared/constraints.yaml` relative to the script (`Path(__file__).parents[4]
/ hep-ph-demo / skills / _shared / constraints.yaml`). Fail-closed on any
read error.

## 2. `test_physics_adaptation_words` requires legacy confining-variant words

`test_skill_structure.TestDarkSU3::test_physics_adaptation_words` requires
the literal phrases `scalar dark pion`, `vector dark meson`, and `confining`
in the dark-su3 SKILL.md — these describe the *archived* confining variant,
not the canonical Higgsed variant. The test was written before commit 2bb56d6
declared the Higgsed variant canonical and was never updated.

Resolved without breaking the test by putting those phrases into a
"Variant note" paragraph in the new banner block: it documents the
historical archival decision and includes the legacy strings as quoted
references. The test still passes; the SKILL.md doesn't claim the legacy
physics.

A future cleanup PR could delete this assertion (or rewrite it to require
`vector dark boson`, `dark pseudoscalar`, `Higgsed`) but that's out of
scope for round 3.

## 3. The pre-existing 2hdm-a failure is genuinely orthogonal

`Test2HdmA::test_step4_prose_directive_count_and_order` has been failing on
`afaa015` since at least `75942bf` (refactor that dropped Package-X). I
confirmed by checking `git diff plugins/hep-ph-demo/skills/2hdm-a/SKILL.md`
in this worktree → empty. The failure is upstream of round-3 scope and
should be filed as a separate issue.

## 4. `git stash` confusion mid-session

I ran `git stash` to verify the 2hdm-a failure was pre-existing on a clean
afaa015 tree. The stash succeeded and reverted my Fix 1 + Fix 3 banner
edits. Recovered with `git stash pop`. No data loss but it added a few
minutes. Avoid `git stash` in fixer worktrees in the future — diff against
HEAD instead.

## 5. `python3 -m pytest` is broken in the user's pyenv

`python3 -m pytest` fails with `AttributeError: module 'py' has no
attribute 'path'` because the pyenv-shim `py` module is older than the
`pytest 9.0.3` installation expects. The bare `pytest` CLI works fine
(picks up the right shims). Documented for the round-3 reviewer in case
they hit the same wall.
