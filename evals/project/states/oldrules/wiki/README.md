# Wiki: how we work

Agents' technical knowledge base for the Kestrel platform: how it works and its current state. Based on Karpathy's "LLM wiki" (index, log, raw vs wiki, lint), simplified for one project.

## What goes where

| Place | Contents |
| --- | --- |
| `wiki/` | How it works and the current state: services, database, config, operations, gotchas. Agents write, everyone reads. |
| `raw/<area>/` | Verbatim copies from the host (config exports, SQL output), as found. |
| `scripts/<area>/` | What we make: SQL and analysis scripts. May be changed. |
| Shared drive `Ops/Procedures` | Customer-facing: meeting notes, procedures, change records (what, where, rollback), task lists. |

The wiki does not repeat the shared drive: it summarises the technology and points to the note in its `Source` line.

## When to update

In the same turn you establish it:

- a **discovery**: a fact you verified on the host, in SQL or in a document;
- a **change** to config, data or a release;
- a **disproved assumption**: a wiki claim that does not hold.

Write suspicions as suspicions ("probably", "to verify"), never as fact.

## How

1. Check in `index.md` and with grep in `wiki/` whether the topic already has a page; update it instead of creating a new one.
2. New page: in the area folder (one level, e.g. `wiki/api/`), kebab-case filename after the concept. New area: new folder plus section in `index.md`.
3. Set `Updated` to today on a content change and update the row in `index.md`.
4. Add a line at the bottom of `log.md`.
5. If the change touches other pages (same table, function or setting), update those too.

## Page format

```markdown
# Title

> Source: <service + query | shared-drive note | raw/...>; <second source>
> Updated: YYYY-MM-DD

One paragraph: what this is and where it lives.

## <Sections by content>

## See also
- [Other page](../area/page.md)
```

Links inside the wiki are relative to the file. Code identifiers, table and field names stay original.

## Status blocks

A claim that no longer holds stays, with directly below it:

```markdown
> **Status: Outdated** (YYYY-MM-DD)
> What changed and what holds now, with source.

> **Status: Disputed**
> The conflicting sources, and how to decide (query, screen).
```

When you settle a Disputed block, replace it with the established value and note that in the log.

## Log

`log.md` is append-only, newest at the bottom:

```markdown
## [YYYY-MM-DD] discovery | <topic>
- Pages: <updated pages>
- Source: <where established>
```

Actions: `setup`, `discovery`, `change`, `correction`, `lint`. For a change on the host also `- Procedure: <note>.md`.

## Secrets

Passwords, client secrets, tokens and connection strings with credentials never go in `wiki/`, `raw/` or `scripts/`. Replace them with `<redacted>`. Usernames, IPs and object ids are not secret.

## Lint

On request ("lint the wiki"):

- `index.md` against the files in `wiki/`: add missing rows, mark dead rows with `[MISSING]`, align `Updated`.
- Check internal links and links to `raw/`.
- Report, do not fix: contradictions between pages, claims without source, outdated claims without status block, pages without incoming link, terms that occur often but have no page.
- Log line `## [date] lint | <N> points, <M> fixed`.
