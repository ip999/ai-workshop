# CLAUDE.md

Guidance for AI coding sessions working in this repo.

## What this repo is

A linear, self-service workshop on building LLM agents — the tutorials in
`agents/`, `mcp/`, `skills/`, `memory/`, and `capstone/` — plus a classroom
layer in `training/` (Marp slides and hands-on labs) that mirrors those
tutorials one-to-one.

The course is linear: **agents → mcp → skills → memory → capstone**.

## Keep the training materials aligned with the course

The tutorials are the single source of truth: each carries its own hands-on
exercises inline — **🧪 Your turn** boxes at the end of each Part — and
`training/slides/` is a presentation layer over them. There is **no separate
`labs/` folder**.

**When you change a tutorial, update its 🧪 Your turn box and its slide deck
in the same change**, so content, exercise, and slides never drift. This
applies to renaming an example file, adding / removing / reordering a Part,
changing an example, or changing the lesson order. See guidelines.md →
"Keeping the training materials in sync" for the specifics, and the table in
`training/README.md`.

## Conventions

- Follow `guidelines.md` for tutorial style (voice, structure, the linear
  `Next:` pointers, the capstone's exemption).
- Each runnable example block opens with a `# filename.py` comment; helper
  fragments and illustrative blocks stay unnamed.
- Before committing changes to any tutorial, verify the code blocks still
  parse — and ideally run the pure-Python ones (`build_skill_index`,
  `summarize.py`, `trim`) and that `capstone/agent.py` compiles.
- The slides publish to GitHub Pages via `.github/workflows/slides.yml`.
- Canonical term definitions (agent, harness, model, tool, loop, …) live in
  `GLOSSARY.md` — it states the definitions the course uses and is explicit
  that the field has no single consensus. Keep usage consistent with it.
