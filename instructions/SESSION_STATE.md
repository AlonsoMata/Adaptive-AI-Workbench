# SESSION_STATE.md

## Current State Summary
The app already supports workflow generation, candidate review/editing, installation, and execution. The UI layout has been improved enough to continue product work. The next major milestone is not another UI-only pass, but a structural product improvement: replacing domain-specific presets with universal reusable response controls.

## Last Completed Milestone
ui-layout-polish-v2

## What Is Working Now
- workflow request input
- candidate workflow generation
- candidate review/edit/install flow
- installed workflow catalog selection
- installed action execution
- improved UI layout and section distribution
- better candidate review usability than earlier versions

## Recent Important Problems That Were Resolved
- candidate action review list visibility/sync issues
- workflow generation parsing/debugging issues that caused confusing failures
- poor UI distribution that made candidate review difficult

## Last Important Root Cause
The project suffered from mixed concerns across milestones: UI/layout work and generation/debugging work were getting conflated. Separating these concerns and fixing them milestone by milestone improved stability.

## Current Product Weakness
The preset model is still conceptually weak for a system that generates arbitrary workflow packs. Domain-specific presets like `professional_email`, `concise_cv`, and `strict_code_review` do not scale well across new generated pack domains.

## Current Branch
feature/preset-controls-redesign

## Recommended Next Step
Redesign presets into universal reusable controls such as tone, length, language, style, and format, while preserving the current workflow generation/review/install/execute model.

## Key Risks Right Now
- breaking generation while redesigning control semantics
- making the UI more confusing while adding new controls
- introducing compatibility problems between built-in packs and generated packs
- overengineering the redesign instead of keeping it practical

## Files Likely to Matter Next
- `domain/models.py`
- `services/workbench_service.py`
- `planning/workflow_generator.py`
- `templates/prompts/generate_action_pack.txt`
- `ui/controller.py`
- `ui/root.py`
- `ui/widgets.py`
- `ui/state.py`

## Quick Verification of Current Healthy Baseline
1. Launch the app
2. Generate a candidate workflow from a normal request
3. Review/edit/install it
4. Select an installed action and run it
5. Confirm output/inspector/catalog still behave coherently