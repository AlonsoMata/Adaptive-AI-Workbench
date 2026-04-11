# TASK.md

## Current Objective
Improve the clarity and usefulness of candidate-generation feedback so users can understand why generation failed or why a candidate was rejected, without redesigning the core flow.

## Current Branch
feature/candidate-feedback-clarity

## What this milestone should achieve
- Trace the current candidate-generation failure path end to end across gateway, parsing, validation, service, controller, and UI surfaces
- Categorize candidate-generation failures clearly without weakening validation or changing candidate review as a concept
- Improve user-facing feedback so failures are understandable, consistent, and actionable
- Preserve the current workflow generation/review/install/execute flow end-to-end without broad redesign

## In Scope
This milestone DOES include:
- targeted changes in the candidate-generation feedback path
- small structured error or reason mapping if needed
- service/controller/UI feedback shaping for generation failures and rejections
- small gateway or validator output adjustments only if required for clearer categorized feedback
- updating tests affected by the feedback-clarity work

## Out of Scope
This milestone does NOT include:
- migrating away from Tkinter
- redesigning the entire product flow
- large unrelated refactors
- adding external tools/web search integrations
- broad UI/layout redesign
- installed action execution redesign
- weakening strict schema validation
- generation heuristic redesign except where already present and only feedback wording is being clarified

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
- `ui/controller.py`
- `ui/state.py` if truly needed
- `model/gateway.py`
- `safety/parsing.py`
- `safety/validators.py` if truly needed
- a new small helper module only if clearly justified
- relevant tests

## Risks to Avoid
- weakening schema validation instead of clarifying failures
- mixing this milestone with unrelated UI/layout work
- broad refactors that obscure the root cause
- touching installed execution without a confirmed need
- leaking raw low-level exceptions directly to users when clearer feedback is available

## Success Criteria
- [ ] Candidate generation still works end-to-end
- [ ] Candidate-generation failures are surfaced clearly and consistently
- [ ] Users can distinguish incomplete responses, parse failures, structural validation failures, unsupported runtime shapes, and semantic quality rejections
- [ ] Candidate review/edit/install still works
- [ ] Installed action execution still works
- [ ] Tests covering the changed quality-gating behavior pass

## Manual Verification Checklist
- [ ] Generate a candidate pack from a normal workflow request
- [ ] Review/edit/install the candidate successfully
- [ ] Run an installed action successfully
- [ ] Confirm model/gateway failures are explained clearly
- [ ] Confirm parse and structural validation failures are explained clearly
- [ ] Confirm unsupported runtime-shape failures and semantic quality rejections are explained clearly
- [ ] Confirm no regression in current UI usability during candidate review/install

## Notes for Codex
- Do root-cause analysis before editing the generation feedback path
- Do not do an uncontrolled rewrite
- Prefer the smallest focused fix set that materially improves user-facing failure clarity
