# SESSION_STATE.md

## Current State Summary
The app already supports workflow generation, candidate review/editing, installation, and execution. The workflow-generation-hardening milestone is complete. The next milestone is generation-quality-gating: detect and handle structurally valid but obviously low-value candidate packs before normal candidate state.

## Last Completed Milestone
workflow-generation-hardening

## What Is Working Now
- workflow request input
- candidate workflow generation
- candidate review/edit/install flow
- installed workflow catalog selection
- installed action execution
- improved UI layout and section distribution
- better candidate review usability than earlier versions

## Recent Important Problems That Were Resolved
- domain-specific preset semantics were replaced with more universal response controls
- candidate generation received a larger output token budget
- BOM-related template/profile loading issues were hardened
- current UI usability improved enough to continue focused product work

## Last Important Root Cause
The project became less stable when broad UI/layout work and generation/debugging work were mixed together. Keeping milestones narrow improved stability and made regressions easier to isolate.

## Current Product Weakness
Candidate workflow generation is now structurally safer, but schema-valid low-value packs can still pass through. The system still needs a narrow semantic usefulness gate for overly meta/planning-heavy packs, redundant actions, weak action differentiation, and packs whose actions do not materially help achieve the requested outcome.

## Current Branch
feature/generation-quality-gating

## Recommended Next Step
Trace the end-to-end generation path, identify the top semantic failure modes still possible after structural hardening, and add a small explicit quality gate with at most one focused regeneration path.

## Key Risks Right Now
- weakening schema validation instead of fixing the real issue
- mixing generation hardening with unrelated UI/layout work
- broad refactors that obscure whether generation actually improved
- accidentally regressing candidate review/install or installed execution
- silently accepting low-value candidate packs because they are schema-valid

## Files Likely to Matter Next
- `services/workbench_service.py`
- `planning/workflow_generator.py`
- `templates/prompts/generate_action_pack.txt`
- `safety/validators.py`
- relevant generation tests

## Quick Verification of Current Healthy Baseline
1. Launch the app
2. Generate a candidate workflow from a normal request
3. Review/edit/install it
4. Select an installed action and run it
5. Confirm output/inspector/catalog still behave coherently
