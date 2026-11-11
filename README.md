# project-memory

A knowledge base that coding agents keep current for one project: how its systems work and what their state is now. Git holds the history.

It suits projects where the truth lives somewhere an agent cannot simply read: a remote server, a customer environment, a database, decisions made in a call. The agent writes down what it verifies, in the same turn, and the next session starts from that.

## Install

Open your project with your coding agent and give it this:

```text
Clone https://github.com/timvdhoorn/project-memory-template to a temporary folder, read skills/project-memory/SKILL.md there and run its "init" section for this repository. Delete the temporary folder when you are done.
```

The agent asks one round of questions (folder name, page language, areas, where human-facing docs live), then installs everything into your repository. Nothing outside the repository is needed afterwards. An existing docs or wiki folder can be migrated in the same run.

## What lands in your repository

```text
your-repo/
├── AGENTS.md            one "## Project memory" block that points at the files below
├── CLAUDE.md            imports AGENTS.md and wiki/index.md
└── wiki/
    ├── index.md         loaded every session: quick facts and one routing line per page
    ├── RULES.md         the writing rules
    ├── DREAM.md         the steps of a consolidation pass
    ├── lint.py          checks the folder; Python 3.9+, standard library only
    ├── status.md        what is live, in progress and open
    ├── log.md           one line per change, newest first
    └── <area>/<page>.md the current state of one topic
```

Only `index.md` is loaded in every session, and lint keeps it under 6,000 bytes. Everything else is read on demand.

## How it works

- **Read.** The agent answers from the pages and queries the live system only when a page lacks the fact or marks it as disputed.
- **Write.** A fact goes on exactly one page; other pages link to it without repeating the value. A changed value replaces the old one in place. Pages hold no history.
- **Unknown state.** When the real state cannot be settled, the claim gets a dated `Disputed` or `Unverified` marker that says how to settle it.
- **Lint.** `python3 wiki/lint.py` checks the index, links, anchors, history words, markers, sizes, the log format and secret-like strings. Exit 0 is clean.
- **Dream.** Once the last dream pass is over 7 days old and changes were logged since, lint prints `dream due` and the agent offers a pass: merge duplicates, move misplaced facts, shorten the status page, settle stale markers. The pass runs in a subagent when the agent has one.
- **Optional hook.** For a live system that is hard to reach, a Claude Code `Stop` hook sends a turn back once when it touched that system without changing a page.

## Beside a glossary and ADRs

`GLOSSARY.md`, `docs/adr/`, `docs/solutions/` and `docs/agents/` belong to other skills. project-memory reads them and links to them, and never changes them: a term's meaning stays in the glossary, a decision's reason in its ADR, and the pages state the resulting current state.

## The skill, optional

Copy [`skills/project-memory`](skills/project-memory) into your agent's skills folder (for Claude Code: `~/.claude/skills/`) to get three commands:

| Command | Does |
| --- | --- |
| `/project-memory` | Shows what is stored, and whether the installed files are behind this skill |
| `/project-memory init` | Installs into a repository, or migrates an existing docs folder |
| `/project-memory dream` | Runs a consolidation pass |

## Development

Unit tests: `python3 -m unittest discover -s tests`. Scenario tests against real agent sessions on an invented project: [evals/](evals/README.md).

## License

[MIT](LICENSE)
