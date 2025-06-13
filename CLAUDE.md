## Project Summary
A web/app platform to help users pass the Norwegian driver’s theory test. The stack includes Flask + SQLAlchemy + MySQL, with Jinja + Tailwind frontend and modular architecture.

## Files to Reference
- plan/plan.yaml → defines structure, models, routes, modules
- project_checklist.txt → use this as the authoritative roadmap for phases and progress tracking
Do not analyze:
  - /venv/
  - /__pycache__/
  - /plan/plan.docx
  - /plan/plan.pdf
  - /plan/steps.txt
  - /repomix-output.xml
  - /questions.db
  - All image files: *.png, *.gif

## Behavior Instructions
- Always check `plan/plan.yaml` before suggesting architecture-level changes
- Only modify one file at a time
- Ask before introducing new dependencies or breaking structure
- Prefer minimal, surgical changes
- Don't suggest things already marked as complete in steps.txt
- If a roadmap item is implemented during a change, it should be marked complete in steps.txt

## Response Style
- Short, structured, high signal
- Only explain when something is non-obvious
- Use comments in code when appropriate
- Avoid repeating file contents unless directly relevant

## Voice & Tone
- Neutral, direct
- Think like a senior developer writing commit messages and merge requests