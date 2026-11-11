"""Graders: judge a finished run from its files and transcript, never from the agent's claims.

Each grader takes a Run and returns a list of misses (empty = pass). Self-test: tests/test_graders.py.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(os.path.dirname(HERE), "skills", "project-memory", "scripts", "lint.py")
KEY = json.load(open(os.path.join(HERE, "key.json")))["facts"]
OLD_BLOCK = re.compile(r"\*\*(Status:\s*)?(Outdated|Superseded|Deprecated|Verouderd)\b")
HISTORY = re.compile(r"(?i)\bpreviously\b|\bformerly\b|changed from|raised from|lowered from|\bwas (set|raised|changed|lowered)\b|→|\bused to be\b")
SKIP = ("log.md", "RULES.md", "DREAM.md", "README.md")


class Run:
    """A finished run: its directory, the tool calls [(name, input)], and the final reply text."""

    def __init__(self, root, calls=(), text="", base="HEAD"):
        self.root, self.calls, self.text, self.base = root, list(calls), text or "", base

    def kb(self):
        for name in ("wiki", "docs", "kb", "knowledge"):
            d = os.path.join(self.root, name)
            if os.path.isfile(os.path.join(d, "index.md")) and any(os.path.isfile(os.path.join(d, r)) for r in ("RULES.md", "README.md")):
                return d
        for d, _, files in os.walk(self.root):
            if ".git" in d or ".claude" in d:
                continue
            if "index.md" in files and "RULES.md" in files:
                return d
        return None

    def pages(self, skip=SKIP):
        kb = self.kb()
        out = {}
        if not kb:
            return out
        for d, _, files in os.walk(kb):
            for f in files:
                rel = os.path.relpath(os.path.join(d, f), kb)
                if f.endswith(".md") and f not in skip:
                    out[rel] = open(os.path.join(d, f), encoding="utf-8").read()
        return out

    def git(self, *args):
        return subprocess.run(["git", "-C", self.root] + list(args), capture_output=True, text=True).stdout

    def added_lines(self, rel):
        diff = self.git("diff", self.base, "--", rel) + self.untracked(rel)
        return [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]

    def untracked(self, rel):
        out = ""
        for f in self.git("ls-files", "--others", "--exclude-standard", "--", rel).split():
            out += "".join("+" + l + "\n" for l in open(os.path.join(self.root, f), encoding="utf-8").read().splitlines())
        return out

    def live_calls(self):
        return [c for c in self.calls if (c[0] == "Bash" and re.search(r"fleetctl|\.server", str(c[1].get("command", ""))))
                or (c[0] in ("Read", "Grep", "Glob") and ".server" in json.dumps(c[1]))]

    def writes(self):
        return [c for c in self.calls if c[0] in ("Write", "Edit", "MultiEdit", "NotebookEdit")
                or (c[0] == "Bash" and re.search(r"(^|[;&|]\s*)(cp|mv|mkdir|tee|touch|rm)\b|(?<![0-9&])>\s*(?!/dev/null)\S", str(c[1].get("command", ""))))]


def lint_exit(run):
    kb = run.kb()
    if not kb:
        return None
    return subprocess.run([sys.executable, LINT, kb], capture_output=True, text=True).returncode


def fact_lines(pages, fact):
    ident = re.compile(fact["id"], re.I)
    bare = lambda l: re.sub(r"\]\([^)]*\)|\b\d{4}-\d{2}-\d{2}\b", "]", l)  # a link target or a date is not a value of the fact
    return [(p, bare(l)) for p, t in pages.items() for l in t.splitlines() if ident.search(bare(l))]


def check_facts(run, facts=KEY, once=True):
    """Each fact present with its current value, no superseded value on its lines, on at most one topic page."""
    misses, pages = [], run.pages()
    for f in facts:
        lines = fact_lines(pages, f)
        now = [(p, l) for p, l in lines if re.search(f["now"], l, re.I)]
        if not now:
            misses.append("missing fact: %s" % f["name"])
        if f.get("old"):
            stale = [p for p, l in lines if re.search(f["old"], l, re.I)]
            if stale:
                misses.append("superseded value for %s on %s" % (f["name"], ", ".join(sorted(set(stale)))))
        topic = {p for p, _ in now if os.path.basename(p) not in ("index.md", "status.md")}
        if once and len(topic) > 1:
            misses.append("%s on %d pages: %s" % (f["name"], len(topic), ", ".join(sorted(topic))))
    return misses


def check_no_old_blocks(run):
    return ["outdated-style block in %s" % p for p, t in run.pages().items() if OLD_BLOCK.search(t)]


def check_lint(run):
    code = lint_exit(run)
    return [] if code == 0 else ["lint exit %s" % code]


def check_installed(run):
    """RULES.md, DREAM.md and lint.py sit in the knowledge folder, byte-identical to the skill's."""
    kb, skill = run.kb(), os.path.dirname(os.path.dirname(LINT))
    out = []
    for src in ("assets/RULES.md", "assets/DREAM.md", "scripts/lint.py"):
        dst = os.path.join(kb or "", os.path.basename(src))
        if not kb or not os.path.isfile(dst):
            out.append("not installed: %s" % os.path.basename(src))
        elif open(dst, "rb").read() != open(os.path.join(skill, src), "rb").read():
            out.append("installed copy differs: %s" % os.path.basename(src))
    return out


def instruction_block(run, folder):
    """Exactly one `## Project memory` block in the instruction files and one index import in CLAUDE.md."""
    misses, blocks = [], 0
    for name in ("AGENTS.md", "CLAUDE.md"):
        p = os.path.join(run.root, name)
        if os.path.isfile(p) and not os.path.islink(p):
            blocks += len(re.findall(r"(?m)^## Project memory\s*$", open(p, encoding="utf-8").read()))
    if blocks != 1:
        misses.append("%d `## Project memory` blocks" % blocks)
    cl = os.path.join(run.root, "CLAUDE.md")
    if os.path.isfile(cl):
        n = len(re.findall(r"(?m)^@%s/index\.md\s*$" % re.escape(folder), open(cl, encoding="utf-8").read()))
        if n != 1:
            misses.append("%d `@%s/index.md` lines in CLAUDE.md" % (n, folder))
    return misses


# --- scenario graders -------------------------------------------------------------------------

def g_init_ask(run):
    """Turn 1 of init: a question round, no file written."""
    misses = []
    if run.writes():
        misses.append("wrote before asking: %s" % run.writes()[0][0])
    if run.git("status", "--porcelain").strip():
        misses.append("files changed before the question round")
    if run.text.count("?") < 2 and len(re.findall(r"(?m)^\s*\d\.\s", run.text)) < 3:
        misses.append("no question round in the reply")
    return misses


def g_init_fresh(run):
    misses = check_lint(run)
    kb = run.kb()
    if not kb:
        return misses + ["no knowledge folder"]
    idx = open(os.path.join(kb, "index.md"), encoding="utf-8").read()
    quick = idx.split("\n## ", 2)[1] if idx.count("\n## ") >= 1 else ""
    for need in ("fleetctl", "app01.kestrel.internal"):
        if need not in quick:
            misses.append("quick facts lack %s" % need)
    wrong = [f["name"] for f in KEY if f.get("old") and any(re.search(f["old"], l, re.I) for _, l in fact_lines(run.pages(), f))]
    misses += ["wrong value for %s" % w for w in wrong]
    block = open(os.path.join(run.root, "AGENTS.md"), encoding="utf-8").read().split("## Project memory")[-1]
    if "skills/project-memory" in block:
        misses.append("block points into the skill folder")
    return misses + check_installed(run) + instruction_block(run, os.path.relpath(kb, run.root))


def g_init_messy(run):
    misses = check_lint(run) + check_facts(run) + check_no_old_blocks(run) + check_installed(run)
    for p, t in run.pages().items():
        if re.search(r"(?im)^#+\s*step \d", t) or re.search(r"chang(e|es)[-_ ]?(record|log)?\.md$", p):
            misses.append("journal still present: %s" % p)
            break
    kb = run.kb()
    if kb and os.path.relpath(kb, run.root) != "docs" and os.path.isdir(os.path.join(run.root, "docs")):
        left = [f for f in os.listdir(os.path.join(run.root, "docs")) if f.endswith(".md")]
        if left:
            misses.append("old docs/ left beside the new folder: %d pages" % len(left))
    return misses


def g_daily_write(run):
    """Scenario 3: rate limit learned and changed to 300, webhook claim corrected, user's IP range recorded."""
    misses = check_lint(run)
    conf = open(os.path.join(run.root, ".server", "etc", "booking-api.conf")).read()
    if not re.search(r"rate_limit_per_min = 300\b", conf):
        misses.append("task not done: live rate limit is not 300")
    pages = run.pages(skip=SKIP + ("index.md", "status.md"))  # status lists open work
    rl = [p for p, t in pages.items() for l in t.splitlines() if re.search(r"rate.?limit", l, re.I) and re.search(r"\b300\b", l)]
    if not rl:
        misses.append("rate limit 300 not recorded on a page")
    elif len(set(rl)) > 1:
        misses.append("rate limit on %d pages" % len(set(rl)))
    elif not any(p.startswith("api") and "booking" in p for p in rl):
        misses.append("rate limit recorded on %s, owner is api/booking-api.md" % rl[0])
    if any(re.search(r"rate.?limit", l, re.I) and re.search(r"\b120\b", l) for t in pages.values() for l in t.splitlines()):
        misses.append("old rate limit 120 kept on a page")
    pay = next((t for p, t in pages.items() if "payment" in p), "")
    if "/hooks/pay/v2" not in pay or re.search(r"/hooks/pay(?!/v2)", pay):
        misses.append("webhook claim not corrected in place on the payments page")
    ip = {p for p, t in pages.items() if "203.0.113.0/24" in t}
    if len(ip) != 1:
        misses.append("user fact 203.0.113.0/24 on %d pages" % len(ip))
    kb = run.kb()
    rel = os.path.relpath(kb, run.root) if kb else "wiki"
    for p in pages:
        hist = [l for l in run.added_lines(os.path.join(rel, p)) if HISTORY.search(l) or OLD_BLOCK.search(l)]
        if hist:
            misses.append("history appended on %s: %s" % (p, hist[0][:80]))
    logs = [l for l in run.added_lines(os.path.join(rel, "log.md")) if l.strip().startswith(("-", "##"))]
    if not 1 <= len(logs) <= 3:
        misses.append("%d log lines added" % len(logs))
    return misses


def g_daily_read(run):
    misses = [] if re.search(r"\b50\b", run.text) else ["wrong or no deposit in the answer"]
    if run.live_calls():
        misses.append("re-queried the live system (%d calls)" % len(run.live_calls()))
    return misses


def present(run):
    """Facts whose current value the knowledge base holds now (dream must not lose them)."""
    return [f for f in KEY if "missing fact: %s" % f["name"] not in check_facts(run, [f])]


def g_dream(run, status_before, facts):
    misses = check_lint(run) + check_facts(run, facts)
    kb = run.kb()
    st = os.path.join(kb, "status.md") if kb else ""
    if not os.path.isfile(st) or os.path.getsize(st) >= status_before:
        misses.append("status.md not shortened")
    rel = os.path.relpath(kb, run.root) if kb else "wiki"
    logs = [l for l in run.added_lines(os.path.join(rel, "log.md")) if l.startswith("- ")]
    if len(logs) != 1 or " dream " not in logs[0]:
        misses.append("expected one dream log line, got %d" % len(logs))
    return misses


def g_overview(run):
    misses = []
    if run.git("status", "--porcelain").strip():
        misses.append("files changed: %s" % run.git("status", "--porcelain").split("\n")[0])
    if not re.search(r"(?i)lint", run.text):
        misses.append("overview lacks the lint result")
    if not re.search(r"(?i)status|live|in progress", run.text):
        misses.append("overview lacks the status summary")
    return misses


def g_route(run, expect):
    first = run.calls[0] if run.calls else ("none", {})
    took = first[0] == "Skill" and "project-memory" in json.dumps(first[1])
    if expect and not took:
        return ["first call %s, expected the project-memory skill" % first[0]]
    if not expect and any(c[0] == "Skill" and "project-memory" in json.dumps(c[1]) for c in run.calls):
        return ["took the project-memory skill"]
    return []


def growth_metrics(run, value="8.25"):
    pages = run.pages(skip=("RULES.md", "DREAM.md", "README.md"))
    topic = next((t for p, t in pages.items() if "pricing" in p), "")
    idx = pages.get("index.md", "")
    return {
        "topic_bytes": len(topic.encode()),
        "index_bytes": len(idx.encode()),
        "old_blocks": sum(len(OLD_BLOCK.findall(t)) for p, t in pages.items() if p != "log.md"),
        "current_places": sum(t.count(value) for p, t in pages.items() if p != "log.md"),
        "stale_ebike_values": sum(len(re.findall(r"7\.(25|60|90|40)|8\.10", l)) for p, t in pages.items() if p != "log.md"
                                  for l in t.splitlines() if re.search(r"e-?bike", l, re.I)),
    }


NEIGHBOURS = ("GLOSSARY.md", "docs/adr", "docs/agents")
SKILLS_BLOCK = "## Agent skills\n\n### Domain docs\n\nSingle-context. See `docs/agents/domain.md`.\n"


def g_coexist(run):
    """Init beside another skill's docs: those stay byte-identical and outside the knowledge folder."""
    misses = ["neighbour doc changed: %s" % l.strip() for l in run.git("status", "--porcelain", "--", *NEIGHBOURS).splitlines()]
    agents = os.path.join(run.root, "AGENTS.md")
    if SKILLS_BLOCK not in (open(agents, encoding="utf-8").read() if os.path.isfile(agents) else ""):
        misses.append("`## Agent skills` block changed or gone")
    if os.path.isfile(os.path.join(run.root, "docs", "RULES.md")):
        misses.append("knowledge folder wraps the neighbour docs")
    return misses
