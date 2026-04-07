# TASK.md

## Current Objective
Redesign the current preset system into universal reusable response controls without breaking candidate generation, candidate review, installation, execution, or the current UI usability.

## Current Branch
feature/preset-controls-redesign

## What this milestone should achieve
- Replace domain-specific preset semantics with universal reusable controls
- Keep the workflow generation/review/install/execute flow working end-to-end
- Adapt the UI so these controls are understandable and usable
- Preserve current product stability

## In Scope
This milestone DOES include:
- redesigning preset/configuration semantics
- updating the domain model if needed
- updating service logic to support the new controls
- adapting generation prompts to the new controls
- adapting the UI to expose the new controls cleanly
- updating tests affected by the redesign

## Out of Scope
This milestone does NOT include:
- migrating away from Tkinter
- redesigning the entire product flow
- large unrelated refactors
- adding external tools/web search integrations
- broad changes to persistence unrelated to control storage/compatibility
- changing the candidate-review concept itself

## Important Constraints
- Do not break candidate generation
- Do not break candidate review/edit/install flow
- Do not break installed action execution
- Do not weaken schema validation casually
- Keep the implementation incremental and backward-safe where possible
- Prefer a small set of genuinely useful controls over a bloated configuration system

## Likely Affected Files
- `domain/models.py`
- `services/workbench_service.py`
- `planning/workflow_generator.py`
- `templates/prompts/generate_action_pack.txt`
- `execution/dispatcher.py`
- `execution/handlers/*` if needed
- `ui/controller.py`
- `ui/root.py`
- `ui/widgets.py`
- `ui/state.py`
- `persistence/preset_store.py` or equivalent
- relevant tests

## Risks to Avoid
- breaking prompt construction for installed action execution
- generating candidates that reference invalid controls
- making the UI cluttered or confusing
- keeping old preset names alive in confusing ways
- mixing this milestone with unrelated generation robustness work

## Success Criteria
- [ ] Universal controls are implemented and domain-agnostic
- [ ] Candidate generation still works
- [ ] Candidate review/edit/install still works
- [ ] Installed action execution still works
- [ ] The UI exposes the controls clearly
- [ ] The layout remains usable
- [ ] Tests covering the redesigned control model pass

## Manual Verification Checklist
- [ ] Generate a candidate pack from a normal workflow request
- [ ] Review/edit/install the candidate successfully
- [ ] Run an installed action successfully
- [ ] Confirm the controls are understandable and reusable across domains
- [ ] Confirm no weird domain-specific preset naming remains in the main UX
- [ ] Confirm the app layout remains comfortable after the control redesign

## Notes for Codex
- Keep the change focused on presets -> universal controls
- Do not do an uncontrolled rewrite
- Explain the compatibility strategy clearly
- Prefer robust migration over flashy redesign