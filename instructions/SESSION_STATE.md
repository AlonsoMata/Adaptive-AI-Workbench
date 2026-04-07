# SESSION_STATE.md

## Current State Summary
The app already supports workflow generation, candidate review/editing, installation, and execution. The preset-controls-redesign milestone is complete. The next milestone is workflow-generation-hardening: improve candidate generation reliability and usefulness without broad UI or execution redesign.

## Last Completed Milestone
preset-controls-redesign

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
Candidate workflow generation is still not reliable enough. The system can fail on malformed or truncated candidate-pack output, schema-valid but low-value packs, inconsistent control references, overly meta/planning-heavy packs, and unclear generation failures.

## Current Branch
feature/workflow-generation-hardening

## Recommended Next Step
Trace the end-to-end generation path, identify the top real root causes, and apply the smallest focused fixes in planning, prompting, parsing, validation, and service-level error handling.

## Key Risks Right Now
- weakening schema validation instead of fixing the real issue
- mixing generation hardening with unrelated UI/layout work
- broad refactors that obscure whether generation actually improved
- accidentally regressing candidate review/install or installed execution

## Files Likely to Matter Next
- `services/workbench_service.py`
- `planning/workflow_generator.py`
- `planning/goal_analyzer.py`
- `templates/prompts/generate_action_pack.txt`
- `safety/parsing.py`
- `safety/repair.py`
- `safety/validators.py`
- `model/gateway.py`

## Quick Verification of Current Healthy Baseline
1. Launch the app
2. Generate a candidate workflow from a normal request
3. Review/edit/install it
4. Select an installed action and run it
5. Confirm output/inspector/catalog still behave coherently
