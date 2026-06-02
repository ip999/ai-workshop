# CLAUDE.md

Guidance for AI coding sessions working in this repo.

## What this repo is

A linear, self-service workshop on building LLM agents — the tutorials in
`agents/`, `mcp/`, `skills/`, `memory/`, and `capstone/` — plus a classroom
layer in `training/` (Marp slides and hands-on labs) that mirrors those
tutorials one-to-one.

The course is linear: **agents → mcp → skills → memory → capstone**.

## Keep the training materials aligned with the course

`training/` is a *presentation layer* over the tutorials, not a separate
source of truth. **When you change a tutorial, update its matching slide
deck (`training/slides/`) and lab (`training/labs/`) in the same change**,
so the two never drift. This applies to renaming an example file, adding /
removing / reordering a Part, changing an example, or changing the lesson
order. See guidelines.md → "Keeping the training materials in sync" for the
specifics, and the mapping table in `training/README.md`.

## Conventions

- Follow `guidelines.md` for tutorial style (voice, structure, the linear
  `Next:` pointers, the capstone's exemption).
- Each runnable example block opens with a `# filename.py` comment; helper
  fragments and illustrative blocks stay unnamed.
- Before committing changes to any tutorial, verify the code blocks still
  parse — and ideally run the pure-Python ones (`build_skill_index`,
  `summarize.py`, `trim`) and that `capstone/agent.py` compiles.
- The slides publish to GitHub Pages via `.github/workflows/slides.yml`.
