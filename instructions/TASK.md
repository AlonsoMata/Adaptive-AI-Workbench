# TASK.md

## Current Objective
Improve candidate workflow generation reliability and usefulness without breaking candidate generation, candidate review/edit/install flow, installed action execution, or current UI usability.

## Current Branch
feature/workflow-generation-hardening

## What this milestone should achieve
- Make generated candidate packs more consistently complete, useful, and installable
- Harden prompt construction, output handling, and failure reporting in the generation path
- Preserve the current workflow generation/review/install/execute flow end-to-end
- Preserve current product stability without broad redesign

## In Scope
This milestone DOES include:
- targeted changes in the candidate generation pipeline
- prompt/template adjustments that improve candidate pack quality
- parsing/repair/validation hardening where a confirmed root cause requires it
- service-level failure handling or diagnostics for generation
- updating tests affected by the hardening work

## Out of Scope
This milestone does NOT include:
- migrating away from Tkinter
- redesigning the entire product flow
- large unrelated refactors
- adding external tools/web search integrations
- broad UI/layout redesign
- installed action execution redesign unless required by a confirmed generation-path issue

## Important Constraints
- Do not break candidate generation
- Do not break candidate review/edit/install flow
- Do not break installed action execution
- Do not weaken schema validation casually
- Keep the implementation incremental, focused, and verifiable
- Respect the architectural separation in `ARCHITECTURE.md`
- Respect the settled decisions in `DECISIONS.md`

## Likely Affected Files
- `services/workbench_service.py`
- `planning/workflow_generator.py`
- `planning/goal_analyzer.py` if truly needed
- `templates/prompts/generate_action_pack.txt`
- `safety/parsing.py`
- `safety/repair.py` if truly needed
- `safety/validators.py` if truly needed
- `model/gateway.py` if output handling needs a small targeted fix
- relevant tests

## Risks to Avoid
- weakening schema validation instead of fixing generation quality
- mixing this milestone with unrelated UI/layout work
- broad refactors that obscure the root cause
- touching installed execution without a confirmed need
- leaving generation failures unclear or hard to debug

## Success Criteria
- [ ] Candidate generation still works end-to-end
- [ ] Generated candidate packs are more consistently useful and installable
- [ ] Parsing/validation failures are handled more robustly
- [ ] Candidate generation still works
- [ ] Candidate review/edit/install still works
- [ ] Installed action execution still works
- [ ] Tests covering the changed generation behavior pass

## Manual Verification Checklist
- [ ] Generate a candidate pack from a normal workflow request
- [ ] Review/edit/install the candidate successfully
- [ ] Run an installed action successfully
- [ ] Confirm generated candidate packs contain practical task-solving actions
- [ ] Confirm malformed or truncated generation output fails clearly
- [ ] Confirm no regression in current UI usability during candidate review/install

## Notes for Codex
- Do root-cause analysis before editing the generation path
- Do not do an uncontrolled rewrite
- Prefer the smallest focused fix set that materially improves reliability
