# SESSION_STATE.md

## Current State Summary
The app already supports workflow generation, candidate review/editing, installation, and execution. The generation-quality-gating milestone is complete. The next milestone is candidate-feedback-clarity: make candidate-generation failures and rejections easier for users to understand without redesigning the core flow.

## Last Completed Milestone
generation-quality-gating

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
Candidate workflow generation is now more resilient and quality-gated, but generation failures and rejections are still surfaced inconsistently. Some messages are too technical, too generic, or not actionable enough across the service, controller, inspector, and status path.

## Current Branch
feature/candidate-feedback-clarity

## Recommended Next Step
Trace the end-to-end candidate-generation failure path, identify the top feedback clarity problems, and add a small normalized feedback model or mapping so users can understand why generation failed or a candidate was rejected.

## Key Risks Right Now
- weakening schema validation instead of clarifying the real issue
- mixing feedback work with unrelated UI/layout work
- broad refactors that obscure whether feedback actually improved
- accidentally regressing candidate review/install or installed execution
- continuing to leak raw low-level generation errors directly into user-facing status and inspector text

## Files Likely to Matter Next
- `services/workbench_service.py`
- `ui/controller.py`
- `model/gateway.py`
- `safety/parsing.py`
- `safety/validators.py`
- relevant generation/controller tests

## Quick Verification of Current Healthy Baseline
1. Launch the app
2. Generate a candidate workflow from a normal request
3. Review/edit/install it
4. Select an installed action and run it
5. Confirm output/inspector/catalog still behave coherently
