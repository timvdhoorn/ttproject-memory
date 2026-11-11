# Docs: how we work

Agents' technical notes for the Kestrel platform: how it works and its current state.

## When to update
In the same turn you establish it: a discovery verified on the host, a change to config, data or a release, or a disproved claim.

## How
1. Find the page via `index.md` or grep; update it rather than adding one.
2. Set `Updated` to today on a content change and update the row in `index.md`.
3. Add a line at the bottom of `log.md`.
4. If the change touches other pages (same table, setting), update those too.

## Status blocks
A claim that no longer holds stays, with directly below it:

    > **Status: Outdated** (YYYY-MM-DD)
    > What changed and what holds now, with source.

    > **Status: Disputed**
    > The conflicting sources, and how to decide.

## Log
`log.md` is append-only, newest at the bottom: `## [YYYY-MM-DD] discovery | <topic>` with `- Pages:` and `- Source:` lines.
