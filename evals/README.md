# Scenarios

Real `claude -p` sessions against an invented project (Kestrel Rentals, `project/`) whose host is simulated by `bin/fleetctl` over a local SQLite database and config files. Each run copies a starting state to `<work>/r…/kestrel-ops`, installs the skill as a project skill, commits, runs the prompt with user settings excluded, and grades the files and the transcript (`graders.py`, answer key `key.json`; neither is copied into a run).

```sh
python3 evals/run.py all [--model claude-sonnet-5-5] [--runs 3] [--work DIR] [--clean]
python3 evals/run.py write,read --runs 1      # comma list of scenarios
```

Results append to `<work>/results.jsonl`; run directories stay for inspection unless `--clean`.

| Scenario | State | Proves |
| --- | --- | --- |
| `init-fresh` | fresh | asks one question round before writing; with answers: lint 0, quick facts match the host, one `## Project memory` block and one `@wiki/index.md` (rep 1 reruns `init` to check both stay single) |
| `init-messy` | messy | migration: every still-true key fact once, no superseded value, no outdated blocks, journal gone, lint 0 |
| `init-coexist` | messy + coexist | `GLOSSARY.md`, `docs/adr/`, `docs/agents/` and the `## Agent skills` block stay byte-identical; the knowledge folder sits beside `docs/`; plus the `init-messy` checks |
| `write`, `write-hook` | ready | daily write without naming the skill: learned, corrected and told facts land on the owning page in place, no history, 1-3 log lines, lint 0; with and without the `Stop` hook |
| `read` | ready | answers from the knowledge base; any host query counts as a miss |
| `read-bare` | fresh | no-memory baseline for `read`: same question, no wiki; pass is the correct deposit (50), host queries are expected; compare calls, host calls and cost with `read` |
| `dream` | dirty | lint 0, duplicates merged, `status.md` shorter, one `dream` log line, no fact lost; the unmarked stale e-bike rate (6.50, host says 7.25) is replaced on `pricing.md` |
| `overview` | ready | bare `/ttproject-memory` reports and changes nothing |
| `route` | fresh | routing pair, first tool call with `--max-turns 2` |
| `write-old`, `growth-new`, `growth-old` | ready / oldrules | blind comparison inputs: the old rules file against the new; growth is five sessions changing one value, then a fresh question |

Cost on Sonnet 5.5 (2026-11-11): `all` at 3 reps is 30 sessions, about $3 and 12 minutes; the comparison adds 14 sessions, about $1.2 and 5 minutes. Graders self-test: `python3 -m unittest discover -s tests`.
