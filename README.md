# Adaptive AI Workbench

Adaptive AI Workbench is a goal-driven desktop app that installs validated workflows on demand. It is designed as a safer middle ground between rigid single-purpose tools and opaque autonomous agents: flexible enough to adapt to the user's task, but constrained enough to stay inspectable, schema-bound, and easy to explain.

## What It Is
- A local-first Python desktop app with a Tkinter UI
- A workflow workbench for writing, CV improvement, code help, and meeting notes
- A structured system that uses validated workflow packs instead of arbitrary generated code

## Why It Exists
Most AI productivity apps either hardcode a small feature set or hide too much behind agent behavior. This project explores a more credible product shape:
- the user provides a goal
- the app installs or activates a workflow pack
- actions stay within approved categories
- execution remains visible, reviewable, and safe

That makes the project useful both as a practical tool and as a portfolio example of AI product architecture, validation, and controlled execution.

## How It Works
The core model is:

`User goal -> Candidate workflow pack -> Validation -> Installed workflow pack -> Safe execution`

In the current version, the app already includes built-in workflow packs and presets. The UI lets you:
1. Select a built-in pack
2. Inspect the pack and its actions
3. Select a preset
4. Run an action
5. See a structured execution preview in the Output panel

## Built-In Workflows
- `email_assistant`: draft, rewrite, reply to, and translate emails
- `cv_improver`: improve bullets, rewrite summaries, and tailor a CV to a role
- `code_helper`: explain code, review code, and suggest refactor plans
- `meeting_notes`: clean notes, summarize meetings, extract decisions, and draft follow-ups

Built-in presets:
- `professional_email`
- `concise_cv`
- `strict_code_review`

## Local Setup
1. Create and activate a virtual environment.
2. Install the project in editable mode with dev dependencies:

```bash
pip install -e .[dev]
```

3. Copy `.env.example` to `.env`
4. Add `OPENAI_API_KEY` later if you want model-backed generation and execution features
5. Use a Python installation that includes Tkinter/Tcl support for the desktop UI

## Run
Launch the app with:

```bash
python -m adaptive_ai_workbench
```

Run the test suite with:

```bash
python -m pytest -q
```
