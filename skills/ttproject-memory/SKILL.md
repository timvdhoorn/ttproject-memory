---
name: ttproject-memory
description: Set up or consolidate a project's agent knowledge base (wiki of current state, routing index, status page, one-line log). Use for "/ttproject-memory" (overview of what is stored), "/ttproject-memory init" in a new repo or to migrate an existing docs/wiki folder, and "/ttproject-memory dream".
---

# Project memory

The contract is [assets/RULES.md](assets/RULES.md); read it before any command.
`init` **installs** `RULES.md`, `DREAM.md` and `lint.py` into the knowledge folder, so the knowledge base works where this skill is absent. Lint: `python3 <folder>/lint.py` (exit 0 clean, 1 findings).

**Neighbour docs** are files other skills own: `GLOSSARY.md`, `GLOSSARY-MAP.md`, `CONTEXT.md`, `docs/adr/`, `docs/solutions/`, `docs/agents/` and the `## Agent skills` block. Every command here reads them and leaves them byte-identical: no edit, move, rename, reformat or copy into the knowledge folder.

## No command

"/ttproject-memory" alone shows what is stored; it changes nothing.

- No knowledge folder in this repo: say so in one line and offer `init`.
- Otherwise read `index.md`, `status.md` and the top five lines of `log.md`, run lint, and reply in the user's language with:
  the sections with their page count and total size; what `status.md` lists as live, in progress and open;
  every disputed or unverified marker with its page and date; the last five changes; the lint result with its `dream due` line, or the date of the last `dream` log line.
  Offer `dream` when lint has findings or prints `dream due`.
  Compare the installed `RULES.md`, `DREAM.md`, `lint.py` and hook with this skill's; name any that differ and offer to reinstall them.

## init

Done when the folder exists, lint exits 0, and the user has the report (step 6).

1. **Look first.** Read the repo's `AGENTS.md`/`CLAUDE.md`, README and any docs/wiki folder; list the neighbour docs that exist.
2. **Ask one round** before writing anything, only what the repo did not answer (one message, numbered, a proposed default per question):
   1. Folder name (default `wiki/`; an existing docs folder can be migrated in place, except one that holds neighbour docs: then the knowledge folder is a sibling such as `wiki/` and only the other pages move).
   2. Page language (rules stay English).
   3. Areas: the top-level sections (one folder each).
   4. Where human-facing docs live (customer notes, procedures, change records), if anywhere.
   5. Is there a live system that is hard to reach (remote session, customer environment)? Then offer the turn-end hook and ask which tools or commands touch it.
   6. Do several repos share business rules or a live system? Then that knowledge goes in one shared memory repo set up the same way, at the same `~/` path on every machine; each member repo's block gets one line pointing there, and a fact lives in one of the two, never both. Plain paths, no symlinks or submodules.
3. **Write.**
   - Install `assets/RULES.md`, `assets/DREAM.md` and `scripts/lint.py` into the folder, byte-identical; a rerun replaces them.
   - Copy `assets/index.md`, `assets/status.md`, `assets/log.md` into the folder; translate their headings and the header labels into the page language.
   - Fill the quick facts with what you found (connect, tools, files in/out, deploy); leave out what you do not know.
   - Neighbour docs that exist: one routing line each in `index.md`, under its own heading, linking to the file or folder where it is.
   - **Migrating an existing folder:** keep the old tree at the default branch as reference, then for each page:
     move every still-true fact out of journal-like pages (change logs, step histories) to its owning topic page, put what is live/in progress/open in `status.md`, and drop the history;
     rewrite outdated-marked claims to their current value, keeping a dated disputed marker only where the real state is unknown;
     keep each fact on one page and link from others; convert the old log to one line per entry.
     Change no claim's meaning you cannot verify.
   - One `setup` line in `log.md`.
4. **Wire.**
   - Instruction file: the `AGENTS.md` or `CLAUDE.md` that exists; when one imports or links to the other, the canonical one. Never create a second beside it, with one exception: only `AGENTS.md` exists, then create a `CLAUDE.md` holding `@AGENTS.md` (Claude Code does not read `AGENTS.md`). When neither exists, ask which in the question round.
   - In it, one `## Project memory` block: the folder, "read `<folder>/index.md` first; write by `<folder>/RULES.md`", the lint command `python3 <folder>/lint.py`, "dream: `<folder>/DREAM.md`", and the human-docs location. A rerun replaces this block in place and leaves the rest of the file alone.
   - `CLAUDE.md`, when it exists or is the chosen file, gets `@<folder>/index.md` once; never a second copy.
   - Hook, only if the user said yes: copy `assets/stop_hook.py` to `.claude/hooks/project-memory.py`, set `KB_DIR`, `TRIGGER_TOOLS` and `TRIGGER_BASH` at its top, and add the `Stop` entry from its docstring to `.claude/settings.json`.
   - Remove old hooks or rule files the new ones replace; `rg` their names and any removed page names until nothing refers to them.
5. **Verify.**
   - Lint exits 0.
   - Migration: extract identifiers (backticked terms, table/column names, versions, hostnames, IPs, paths) from the old tree and confirm each appears in the new one, or list it as dropped history.
   - Hook: feed it one live turn without a page edit (expect `"decision": "block"`) and one with a page edit (expect no output). Stdin is `{"transcript_path": "<jsonl>"}`; the transcript needs a user line with `timestamp` and an assistant `tool_use` line matching the triggers.
6. **Report:** lint exit code, sizes before/after (index and total), the hook results, and for a migration the identifier counts and the dropped list.

## dream

Follow the installed `<folder>/DREAM.md`.
