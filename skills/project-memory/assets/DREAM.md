# Dream

The consolidation pass over this folder, by [RULES.md](RULES.md). Started by the user, or by their yes after lint printed `dream due`.
Done when lint exits 0 (or only markers you listed remain) and one log line records the pass.

0. **Delegate.** You are the main agent and your harness can start a subagent: start one with the brief "Follow `<this folder>/DREAM.md` from step 1 and report what changed", wait, relay its report and stop here. Steps 1-6 are for that subagent, or for you when no subagent exists.
1. Run lint; fix every finding.
2. Merge duplicates: list the identifiers (backticked terms, config keys, values) that occur on more than one page, e.g. ``rg -o '`[^`]+`' <this folder> | sort | uniq -c``; each stays on its owner, the others link.
   A page that defines a term `GLOSSARY.md` defines, or retells an ADR's reasoning, gives way: the page keeps the current state and links there. Where the two disagree, change neither and list it for the user.
3. Move misplaced facts to their owning page; split an oversized page by topic.
4. Shorten `status.md`: finished items leave, their facts go to the owning page.
5. Stale markers: settle each with evidence you can read (repo, `raw/`, human docs, a read-only query of the live system); list any left for the user.
6. Append `- <date> dream | <what changed> | index.md | lint` at the top of `log.md`; run lint again.
