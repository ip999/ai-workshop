# Authoring Guide

This document captures the style and structure for tutorials in this repo. It's written so you can paste it as system context when asking an LLM to draft a new piece, or skim it yourself before writing one by hand.

The reference implementation is [agents/agents.md](agents/agents.md). When in doubt, match its rhythm.

## Core philosophy

Each tutorial teaches **one concept** by walking the reader through the smallest possible code that demonstrates it. Examples are deliberately minimal — no error handling, no abstractions, no production niceties. The point is to see the *shape* of an idea clearly. Production hardening, framework wrappers, and "real-world" complications come at the end as pointers, not as the lesson.

The reader should be able to copy each code block, run it, and see something happen. If a block depends on earlier code, say so explicitly.

## Structure

Every tutorial follows the same skeleton:

1. **Title** in the form *"From X to Y: A Hands-On Intro"* or similar.
2. **One-paragraph intro** stating what the reader will have built by the end and roughly who it's for.
3. **A "deliberately minimal" disclaimer** — restate that examples skip error handling and abstractions.
4. **Prerequisites** — language version, pip installs, accounts/keys.
5. **Contents** — a numbered TOC of the parts.
6. **Parts 1..N** — progressive disclosure, each part building on the last.
7. **Recap** — a short numbered list of the artefacts the reader has built.
8. **"Next steps"** inside the recap — bullets pointing at things to improve once the concept is solid.
9. **Optional "But what about X?" section** — addressing a sibling concept readers will be wondering about.
10. **Further reading** — 3–6 curated links with one-line annotations.

## Each part should

- Open with a one-sentence mental model of what this part introduces. Italicise the *shape* word when relevant: "see the *shape* of the idea."
- Show a short, complete code block (typically 10–40 lines).
- Follow with a short "few things to internalise" list when introducing new mechanics. Three or four bullets is plenty.
- Avoid over-explaining. Let code carry the weight. If a code block is self-explanatory, don't gloss it line-by-line.
- End with a sentence that motivates the next part — a tension the next part resolves.

## Prose voice

- **Second person.** Speak to the reader: "you'll have built", "you keep appending".
- **Conversational but precise.** Short sentences. Confident, not breathless. Avoid hedging ("you might want to consider possibly...").
- **Declarative summaries.** "That's it." "That's the entire pattern." "This is the foundation."
- **Bold for key concept names** on first introduction (e.g. **stateless**, **tools**, **skills**, **MCP server**).
- **Italics sparingly** — for emphasis on a mental model word, not for visual flair.
- **No emojis.** No headings with emojis. No callout banners.

## Code conventions

- Python unless the topic dictates otherwise.
- Concrete API calls, not pseudocode. Show real imports and real return shapes.
- Print statements with the expected output as a `# comment` underneath, so readers can confirm without running.
- Type hints in function signatures (they often pull double duty as schema sources).
- No try/except, no logging, no retries — unless the lesson is *about* try/except.
- Use the simplest model and dependencies that demonstrate the concept. Default to OpenAI for LLM calls and the most popular library for everything else.

## What to avoid

- **Long preambles.** Don't spend three paragraphs setting the scene before the first code block.
- **Architecture diagrams.** This is hands-on; readers learn by typing.
- **Production warnings sprinkled throughout.** Save them for the recap's "next steps" list. They distract from the concept.
- **Repeated reminders that "this is just a toy example."** State it once at the top and trust the reader.
- **Marketing voice.** No "powerful", "seamless", "robust", "unlock". Describe what the code does.
- **Headings deeper than `##`.** Two levels is enough. If you want sub-structure inside a part, use **bold paragraph leads**.

## A note on the "But what about X?" section

This section exists because every tutorial in this series is one slice of a bigger picture, and a reader who's been paying attention will finish with a sibling concept on their mind. Address it head-on rather than leaving them to wonder. Keep it short — a few paragraphs that situate the sibling concept relative to what was just taught, and explain why it wasn't introduced earlier. Reserve it for concepts the course does *not* cover in a later lesson (e.g. RAG, or MCP's resources and prompts) — for the topic that comes next, use the **Next:** pointer instead, not a "But what about X?" aside.

## A note on cross-references

The tutorials form a linear course — agents → mcp → skills → memory → capstone — and each builds on the ones before it. Link **backward** to a prerequisite when you lean on it, and close each lesson with a one-line **Next:** pointer to the lesson that follows. Use a relative path (`../mcp/mcp.md`) and a one-line description. Don't link sideways or skip ahead in a way that implies the course can be read in any order.

## A note on the capstone

The capstone ([capstone/capstone.md](capstone/capstone.md)) is intentionally exempt from the structure above. It's a guided read of one runnable program, not a type-along, so it drops the numbered Parts, the Recap, and the "But what about X?" section in favour of descriptive `##` sections. It keeps the prose voice and the deliberately-minimal ethos, but its job is to show how the concepts *compose* rather than to teach one in isolation. Don't reshape it into the tutorial skeleton.
