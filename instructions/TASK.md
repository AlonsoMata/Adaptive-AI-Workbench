# DECISIONS.md

## Purpose
This file records decisions that are already settled enough that they should not be reopened casually in every Codex session.

---

## 1. Candidate workflows must be reviewed before installation
**Decision**  
Generated workflow packs are first treated as `CandidateActionPack` objects and reviewed before installation.

**Reason**  
Model output should not become executable project state without review.

**Impact**  
The app preserves a dedicated candidate review phase and UI.

---

## 2. Installed workflows are the only workflows executed through the main runtime
**Decision**  
Only installed packs are executed from the standard action runtime.

**Reason**  
Execution should operate on validated, persisted workflow structures.

**Impact**  
Candidate packs remain editable/reviewable objects, not directly executable production state.

---

## 3. Validation remains strict
**Decision**  
The schema should remain strict and should not be relaxed merely because the model sometimes returns malformed output.

**Reason**  
The product depends on predictable structured workflows, not “best effort” broken structures.

**Impact**  
Repair must be conservative and validation remains an important gate.

---

## 4. Repair must stay conservative
**Decision**  
Repair is allowed only for minor and low-risk issues such as harmless wrappers or formatting normalization.

**Reason**  
Repair should improve resilience without inventing missing business-critical fields.

**Impact**  
The app may strip wrappers or normalize values, but should not hallucinate missing structure.

---

## 5. Layout work and generation/parsing work should be separated when possible
**Decision**  
UI/layout branches should avoid touching generation/parsing logic, and generation/parsing branches should avoid touching layout unless explicitly needed.

**Reason**  
Mixing these concerns made debugging harder and created confusing regressions.

**Impact**  
Future milestones should stay focused by layer and problem type.

---

## 6. Generated packs should prefer useful task-solving actions over overly meta planning actions
**Decision**  
Workflow generation should prioritize packs that help the user achieve the requested outcome, not merely plan how to do so.

**Reason**  
Users want useful outputs, not only reframed research or planning scaffolds.

**Impact**  
Generation prompts should steer away from “meta-only” workflow designs unless explicitly requested.

---

## 7. Candidate review is a core product surface, not a temporary debug view
**Decision**  
The Candidate Review Editor is part of the intended product flow and should remain a first-class interface.

**Reason**  
Review/edit/install is central to the workbench concept.

**Impact**  
Layout and UX should continue to support candidate editing seriously.

---

## 8. The repo should act as the project’s persistent memory
**Decision**  
Project memory must live in repository files, not mainly in long chat history.

**Reason**  
Long sessions degrade, compact, and lose detail over time.

**Impact**  
Use `AGENTS.md`, `ARCHITECTURE.md`, `TASK.md`, and `SESSION_STATE.md` as the primary continuity mechanism.

---

## 9. Changes should be focused and verifiable
**Decision**  
Each branch/milestone should solve one clear problem with limited scope.

**Reason**  
Broad mixed changes increase regressions and make Codex less reliable.

**Impact**  
Work should be done milestone by milestone, with explicit scope and verification.

---

## 10. The next major product direction is to move from domain-specific presets toward universal response controls
**Decision**  
The current preset model should evolve toward reusable universal controls (for example tone, length, language, style, format).

**Reason**  
Domain-specific presets scale poorly for arbitrary generated workflow packs.

**Impact**  
Future work should redesign presets/controls carefully without breaking current flows.