# Adaptive AI Workbench

Adaptive AI Workbench is a goal-driven desktop app that installs validated workflows on demand. It is designed as a safer middle ground between rigid single-purpose tools and opaque autonomous agents: flexible enough to adapt to the user's task, but constrained enough to stay inspectable, schema-bound, and easy to explain.

## What It Is
- A local-first Python desktop app with a Tkinter UI
- A workflow workbench for writing, CV improvement, code help, and meeting notes
- A fixed execution engine that generates and installs workflow packs as validated data, not source code

## Why It Exists
Most AI productivity apps either hardcode a small feature set or hide too much behind agent behavior. This project explores a more credible product shape:
- the user provides a goal
- the app generates a candidate workflow pack
- the candidate is parsed, validated, and reviewed
- the user explicitly installs the pack
- actions stay within approved categories
- execution remains visible, reviewable, and safe

That makes the project useful both as a practical tool and as a portfolio example of AI product architecture, validation, and controlled execution.

## How It Works
The core model is:

`User goal -> Candidate workflow pack -> Validation and repair -> Installed workflow pack -> Safe execution`

In the current version, the app includes built-in workflow packs and can also generate new candidate workflow packs from the Goal field. The UI lets you:
1. Describe a goal
2. Generate a candidate workflow pack from that goal
3. Inspect the candidate's title, summary, reasoning, warnings, recommended presets, and actions
4. Install the candidate into the workflow catalog
5. Select an installed pack and action
6. Run the action safely through the existing dispatcher and model gateway
7. Get a real generated result when the model is configured, or a graceful fallback when it is not

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
4. Set `OPENAI_API_KEY` and optionally adjust `AI_WORKBENCH_MODEL` if you want goal-based workflow generation and live execution
5. Use a Python installation that includes Tkinter/Tcl support for the desktop UI

## Run
Launch the app with:

```bash
python -m adaptive_ai_workbench
```

Run the test suite with:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
```