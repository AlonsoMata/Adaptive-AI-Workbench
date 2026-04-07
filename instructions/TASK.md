# TASK.md

## Current Objective
Add a small, maintainable quality-gating layer for generated candidate workflow packs so structurally valid but obviously low-value packs are rejected or retried once before they enter normal candidate state.

## Current Branch
feature/generation-quality-gating

## What this milestone should achieve
- Define explicit, narrow quality criteria for generated candidate packs beyond schema validity
- Detect low-value but schema-valid packs before they are accepted into normal candidate review state
- Prefer at most one focused regeneration with stricter guidance when a pack fails semantic quality
- Preserve the current workflow generation/review/install/execute flow end-to-end without broad redesign

## In Scope
This milestone DOES include:
- targeted changes in the candidate generation pipeline
- a small explicit semantic quality gate for candidate packs
- prompt/template adjustments only if needed to support a focused retry
- service-level failure handling or diagnostics for rejected low-value candidates
- updating tests affected by the quality-gating work

## Out of Scope
This milestone does NOT include:
- migrating away from Tkinter
- redesigning the entire product flow
- large unrelated refactors
- adding external tools/web search integrations
- broad UI/layout redesign
- installed action execution redesign unless required by a confirmed generation-path issue
- weakening strict schema validation

## Important Constraints
- Do not break candidate generation
- Do not break candidate review/edit/install flow
- Do not break installed action execution
- Do not weaken schema validation
- Keep the implementation incremental, focused, and verifiable
- Respect the architectural separation in `ARCHITECTURE.md`
- Respect the settled decisions in `DECISIONS.md`

## Likely Affected Files
- `services/workbench_service.py`
- `planning/workflow_generator.py`
- `templates/prompts/generate_action_pack.txt`
- `safety/validators.py` if truly needed
- a new small helper module only if clearly justified
- relevant tests

## Risks to Avoid
- weakening schema validation instead of fixing generation quality
- mixing this milestone with unrelated UI/layout work
- broad refactors that obscure the root cause
- touching installed execution without a confirmed need
- leaving low-value generation failures unclear or hard to debug

## Success Criteria
- [ ] Candidate generation still works end-to-end
- [ ] Structurally valid but obviously low-value packs are no longer silently accepted
- [ ] Candidate generation still works
- [ ] Candidate review/edit/install still works
- [ ] Installed action execution still works
- [ ] Tests covering the changed quality-gating behavior pass

## Manual Verification Checklist
- [ ] Generate a candidate pack from a normal workflow request
- [ ] Review/edit/install the candidate successfully
- [ ] Run an installed action successfully
- [ ] Confirm low-value but schema-valid packs are rejected or retried clearly
- [ ] Confirm generated candidate packs contain practical task-solving actions
- [ ] Confirm no regression in current UI usability during candidate review/install

## Notes for Codex
- Do root-cause analysis before editing the generation path
- Do not do an uncontrolled rewrite
- Prefer the smallest focused fix set that materially improves semantic usefulness
