# ARCHITECTURE.md

## Overview
Adaptive AI Workbench is a Python desktop application with a Tkinter UI. It helps users create reusable workflow packs with AI, review them before installation, and then execute installed actions through a controlled runtime.

The app is built around a strict distinction between:
- **candidate workflows** (generated, reviewable, editable, not yet trusted)
- **installed workflows** (validated, persisted, executable)

---

## Main Product Flow

### 1. Workflow request
The user writes a request in **New Workflow Request** describing the workflow pack they want.

### 2. Candidate generation
The application generates a `CandidateActionPack` using the model.

### 3. Candidate review
The candidate is shown in the **Candidate Review Editor**.
The user can inspect and edit parts of the candidate before installation.

### 4. Installation
The candidate is revalidated and installed as an `InstalledActionPack`.

### 5. Execution
The user selects an installed pack and one of its actions.
The app builds the final execution request and runs it through the model.

---

## Layered Design

## UI Layer
### Files
- `ui/root.py`
- `ui/widgets.py`
- `ui/state.py`
- `ui/background_tasks.py`

### Responsibilities
- create and arrange widgets
- bind buttons and list selections
- render state into the interface
- keep long-running operations off the Tkinter main thread where needed

### Notes
- `root.py` is the Tkinter shell
- `widgets.py` contains widget construction/layout helpers
- `state.py` is the UI source of truth
- `background_tasks.py` handles async/background task execution safely for the Tkinter app

---

## Controller Layer
### File
- `ui/controller.py`

### Responsibilities
- translate UI events into service operations
- keep candidate-review state coherent
- keep installed-execution state coherent
- update inspector/output/status representations
- coordinate selection flows

### Important distinction
The controller orchestrates. It should not become the place where core business rules or schema rules live.

---

## Service Layer
### File
- `services/workbench_service.py`

### Responsibilities
- list catalog data
- generate candidate workflows
- validate candidate workflows
- install candidate workflows
- preview installed actions
- execute installed actions
- resolve presets/controls for execution
- provide app health/status summaries

### Notes
This is the central business orchestration layer.

---

## Planning Layer
### Files
- `planning/workflow_generator.py`
- `planning/goal_analyzer.py`

### Responsibilities
- normalize the user goal
- build structured prompts for candidate workflow generation
- steer generation toward useful workflow packs

### Notes
This layer should push the model toward:
- complete schema-valid packs
- practical actions
- useful outputs
- less meta/planning-only behavior unless explicitly requested

---

## Safety Layer
### Files
- `safety/parsing.py`
- `safety/repair.py`
- `safety/validators.py`

### Responsibilities
- extract JSON-like candidate payloads from model output
- remove harmless wrappers if needed (for example fences or extra text)
- repair conservative structural issues
- validate final structured objects strictly

### Notes
This layer is critical.
It should improve robustness without lowering standards.

---

## Domain Model Layer
### File
- `domain/models.py`

### Responsibilities
Defines the structural truth of the app.

### Important models
- `ActionDefinition`
- `PresetDefinition` or future equivalent response-control model
- `CandidateActionPack`
- `InstalledActionPack`
- `WorkbenchProject`

### Notes
If a structure is invalid, this layer should say so.
Do not bypass it casually.

---

## Execution Layer
### Files
- `execution/dispatcher.py`
- `execution/handlers/text_handlers.py`
- `execution/handlers/code_handlers.py`
- `execution/handlers/cv_handlers.py`

### Responsibilities
- route an installed action to the appropriate handler
- build execution preview content
- build final prompt inputs for the model

### Notes
This layer defines how supported action kinds become executable requests.

---

## Model Gateway Layer
### File
- `model/gateway.py`

### Responsibilities
- build model requests
- call OpenAI
- normalize the returned text output
- encapsulate model API details

### Notes
The gateway should not contain product logic.
It should remain an adapter around the model.

---

## Persistence Layer
### Files
- `persistence/action_pack_store.py`
- `persistence/preset_store.py`
- `persistence/project_store.py`

### Responsibilities
- built-in template access
- installed pack storage
- project storage
- preset/control definitions as needed

---

## End-to-End Technical Flow

## Candidate generation flow
1. UI sends workflow request to controller
2. Controller starts background generation task
3. Service normalizes the goal
4. Planning builds generation prompt
5. Gateway calls model
6. Safety layer parses and repairs if appropriate
7. Domain models validate the candidate strictly
8. Controller stores candidate in UI state
9. UI renders candidate review editor

## Candidate install flow
1. User edits candidate in UI
2. Controller updates candidate copy
3. Service validates the edited candidate
4. Service installs the candidate through persistence
5. Controller refreshes catalog
6. Candidate state is cleared
7. Installed pack becomes selectable in the sidebar

## Installed execution flow
1. User selects installed pack
2. User selects action
3. Controller requests execution
4. Service builds preview/execution request
5. Dispatcher chooses handler
6. Handler constructs execution prompt
7. Gateway calls model
8. Controller renders output and preview

---

## Current UI Sections
1. Toolbar
2. New Workflow Request
3. Installed Workflow Catalog sidebar
4. Installed Action Execution
5. Inspector
6. Candidate Review Editor
7. Status

### Intended visual hierarchy
The UI should prioritize:
1. Candidate review/editing
2. Workflow request input
3. Installed execution and inspector
4. Sidebar and status

---

## Key Risks
- UI changes accidentally affecting logic
- generation producing meta packs instead of useful packs
- parser fragility around model output formatting
- validation becoming too permissive
- controller absorbing too much responsibility
- unclear distinction between candidate and installed states

---

## Current Product Evolution Direction
The product is moving toward:
- stronger generation reliability
- better candidate review UX
- more universal response controls instead of domain-specific presets
- improved continuity and maintainability through project memory files

---

## Source-of-Truth Guidance
When in doubt:
- schema and structural rules: `domain/models.py`
- business orchestration: `services/workbench_service.py`
- generation prompt behavior: `planning/`
- parsing/repair/validation: `safety/`
- runtime execution: `execution/`
- UI rendering/layout: `ui/`