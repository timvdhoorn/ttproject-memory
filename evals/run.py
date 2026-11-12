#!/usr/bin/env python3
"""Run ttproject-memory scenarios against a fresh `claude -p` session, one at a time.

Usage: python3 evals/run.py <scenario|all> [--model M] [--runs N] [--work DIR] [--clean]
Scenarios: init-fresh init-messy write write-hook read dream overview route
           write-old growth-new growth-old (the last three feed the blind comparison).
Results append to <work>/results.jsonl; the table prints at the end.
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL = os.path.join(REPO, "skills", "ttproject-memory")
PROJECT = os.path.join(HERE, "project")
sys.path.insert(0, HERE)
import graders as G  # noqa: E402

ANSWERS = ("1. `wiki/`. 2. English. 3. Areas: api, data, ops. 4. Customer procedures are on the shared drive `Ops/Procedures`. "
           "5. The host is reached only with `bin/fleetctl`; no turn-end hook. 6. No other repos share this. Go ahead.")
PROMPTS = {
    "init-1": "/ttproject-memory init",
    "init-messy": "/ttproject-memory init\n\nMigrate the existing `docs/` folder. My answers up front: " + ANSWERS.replace("1. `wiki/`.", "1. `wiki/` (move docs/ there)."),
    "init-coexist": "/ttproject-memory init\n\nMigrate the existing `docs/` folder and clean up everything in it. My answers up front: "
                    + ANSWERS.replace("1. `wiki/`.", "1. Keep it in `docs/` if you can."),
    "write": ("Paylane says our webhook calls get rate-limited. Can you check which webhook path and rate limit we're running with, "
              "and raise the booking-api rate limit to 300 per minute? Also FYI: Paylane told me today their webhook calls now come "
              "from 203.0.113.0/24, we'll need that for the firewall later."),
    "read": "Quick one: what deposit do we charge per booking at the moment?",
    "dream": "/ttproject-memory dream",
    "overview": "/ttproject-memory",
    "route-yes": "Our agents keep forgetting how this setup works between sessions. Can you set up a knowledge base in this repo that they keep current?",
    "route-no": "Our agents keep forgetting what bin/fleetctl can do. Can you list its commands for me?",
    "growth": ["Finance set the e-bike hourly rate to 7.60 from today. Please put it live.",
               "Correction from finance: the e-bike per hour goes to 7.90.",
               "Weekend promo: e-bike hourly rate 7.40 starting now, please update it.",
               "Promo is over; set the e-bike hourly rate to 8.10.",
               "Last one this quarter: e-bike hourly rate 8.25, please apply."],
    "growth-ask": "What's the current e-bike hourly rate? Answer from what's in the repo; I don't want anything touched on the host.",
}


def make_copy(work, state, hook=False):
    root = os.path.join(tempfile.mkdtemp(prefix="r", dir=work), "kestrel-ops")
    shutil.copytree(os.path.join(PROJECT, "base"), root, ignore=shutil.ignore_patterns("server"))
    for s in [] if state == "fresh" else state.split("+"):  # "messy+coexist" layers states
        shutil.copytree(os.path.join(PROJECT, "states", s), root, dirs_exist_ok=True)
    srv = os.path.join(root, ".server")
    shutil.copytree(os.path.join(PROJECT, "base", "server"), srv)
    db = sqlite3.connect(os.path.join(srv, "rentals.db"))
    db.executescript(open(os.path.join(srv, "seed.sql")).read())
    db.commit()
    os.remove(os.path.join(srv, "seed.sql"))
    if state == "fresh":
        open(os.path.join(root, "CLAUDE.md"), "w").write("@AGENTS.md\n")
    if os.path.isfile(os.path.join(root, "wiki", "index.md")) and state != "oldrules":
        for src in ("assets/RULES.md", "assets/DREAM.md", "scripts/lint.py"):
            shutil.copy(os.path.join(SKILL, src), os.path.join(root, "wiki"))
    shutil.copytree(SKILL, os.path.join(root, ".claude", "skills", "ttproject-memory"), ignore=shutil.ignore_patterns("__pycache__"))
    if hook:
        hooks = os.path.join(root, ".claude", "hooks")
        os.makedirs(hooks)
        src = open(os.path.join(SKILL, "assets", "stop_hook.py")).read()
        src = re.sub(r'(?m)^TRIGGER_BASH = .*$', 'TRIGGER_BASH = r"\\bfleetctl\\b"', src)
        open(os.path.join(hooks, "project-memory.py"), "w").write(src)
        json.dump({"hooks": {"Stop": [{"hooks": [{"type": "command", "timeout": 15,
                   "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/project-memory.py"'}]}]}},
                  open(os.path.join(root, ".claude", "settings.json"), "w"))
    git = lambda *a: subprocess.run(["git", "-C", root] + list(a), capture_output=True, check=True)
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("-c", "user.name=ops", "-c", "user.email=ops@kestrel.invalid", "commit", "-qm", "initial")
    return root


def transcript(root, sid):
    enc = re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(root))
    path = os.path.expanduser("~/.claude/projects/%s/%s.jsonl" % (enc, sid))
    calls, usage, seen = [], {"in": 0, "out": 0}, set()
    if not os.path.exists(path):
        return calls, usage, None
    for line in open(path, encoding="utf-8"):
        e = json.loads(line)
        if e.get("type") != "assistant":
            continue
        msg = e.get("message") or {}
        for part in msg.get("content") or []:
            if isinstance(part, dict) and part.get("type") == "tool_use":
                calls.append((part.get("name", ""), part.get("input") or {}))
        if msg.get("id") not in seen and msg.get("usage"):
            seen.add(msg.get("id"))
            u = msg["usage"]
            usage["in"] += u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
            usage["out"] += u.get("output_tokens", 0)
    return calls, usage, path


def tpath(root, sid):
    return os.path.expanduser("~/.claude/projects/%s/%s.jsonl" % (re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(root)), sid))


def finished_but_waiting(root, sid, quiet=60):
    p = tpath(root, sid)
    if not os.path.exists(p) or time.time() - os.path.getmtime(p) < quiet:
        return False
    last = [json.loads(l) for l in open(p, encoding="utf-8") if '"type":"assistant"' in l.replace(" ", "")]
    return bool(last) and (last[-1].get("message") or {}).get("stop_reason") == "end_turn"


def last_text(root, sid):
    text = ""
    if os.path.exists(tpath(root, sid)):
        for line in open(tpath(root, sid), encoding="utf-8"):
            e = json.loads(line)
            if e.get("type") == "assistant":
                parts = [p.get("text", "") for p in (e.get("message") or {}).get("content") or [] if isinstance(p, dict) and p.get("type") == "text"]
                text = "\n".join(parts) or text
    return text


def claude(root, prompt, model, resume=None, max_turns=None, timeout=900, prev=None):
    sid = resume or str(uuid.uuid4())
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--setting-sources", "project,local",
           "--strict-mcp-config", "--dangerously-skip-permissions"]
    cmd += ["--resume", sid] if resume else ["--session-id", sid]
    if max_turns:
        cmd += ["--max-turns", str(max_turns)]
    t0 = time.time()
    proc = subprocess.Popen(cmd + [prompt], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    while proc.poll() is None and time.time() - t0 < timeout:
        time.sleep(5)
        if finished_but_waiting(root, sid):  # a backgrounded Bash task keeps `claude -p` alive after the last turn
            proc.kill()
    if proc.poll() is None:
        proc.kill()
    out = proc.stdout.read()
    try:
        res = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    except json.JSONDecodeError as exc:
        res = {"result": "", "error": str(exc)[:200]}
    if not res.get("result"):
        res["result"] = last_text(root, sid)
    calls, usage, path = transcript(root, sid)
    if prev:  # a resumed session's transcript holds the earlier turns too
        calls = calls[len(prev["calls"]):]
        usage = {k: usage[k] - prev["usage"][k] for k in usage}
    return {"sid": sid, "text": res.get("result") or "", "calls": calls, "usage": usage, "secs": round(time.time() - t0),
            "cost": res.get("total_cost_usd"), "transcript": path}


def total(*turns):
    return {"calls": sum(len(t["calls"]) for t in turns), "tokens_in": sum(t["usage"]["in"] for t in turns),
            "tokens_out": sum(t["usage"]["out"] for t in turns), "cost": round(sum(t["cost"] or 0 for t in turns), 3),
            "secs": sum(t["secs"] for t in turns), "transcripts": [t["transcript"] for t in turns]}


def scenario(name, work, rep, model):
    """Run one repetition; return (misses, metrics, root)."""
    if name == "init-fresh":
        root = make_copy(work, "fresh")
        t1 = claude(root, PROMPTS["init-1"], model)
        misses = ["turn1: " + m for m in G.g_init_ask(G.Run(root, t1["calls"], t1["text"]))]
        t2 = claude(root, ANSWERS, model, resume=t1["sid"], prev=t1)
        misses += G.g_init_fresh(G.Run(root, t2["calls"], t2["text"]))
        turns = [t1, t2]
        if rep == 1:  # rerun init once: block and import must stay single
            t3 = claude(root, PROMPTS["init-1"] + "\n\nSame answers as last time: " + ANSWERS, model)
            misses += ["rerun: " + m for m in G.instruction_block(G.Run(root), "wiki")]
            turns.append(t3)
        return misses, total(*turns), root
    if name == "init-messy":
        root = make_copy(work, "messy")
        t = claude(root, PROMPTS["init-messy"], model)
        if not G.Run(root).kb():  # it asked anyway: answer once
            t2 = claude(root, ANSWERS, model, resume=t["sid"], prev=t)
            return G.g_init_messy(G.Run(root)) + ["asked although answered"], total(t, t2), root
        return G.g_init_messy(G.Run(root)), total(t), root
    if name == "init-coexist":
        root = make_copy(work, "messy+coexist")
        t = claude(root, PROMPTS["init-coexist"], model)
        turns = [t]
        if not G.Run(root).kb():
            turns.append(claude(root, ANSWERS, model, resume=t["sid"], prev=t))
        return G.g_init_messy(G.Run(root)) + G.g_coexist(G.Run(root)), total(*turns), root
    if name in ("write", "write-hook", "write-old"):
        root = make_copy(work, "oldrules" if name == "write-old" else "ready", hook=name == "write-hook")
        t = claude(root, PROMPTS["write"], model)
        run = G.Run(root, t["calls"], t["text"])
        return (G.g_daily_write(run) if name != "write-old" else []), total(t), root
    if name == "read":
        root = make_copy(work, "ready")
        t = claude(root, PROMPTS["read"], model)
        return G.g_daily_read(G.Run(root, t["calls"], t["text"])), total(t), root
    if name == "dream":
        root = make_copy(work, "dirty")
        before = os.path.getsize(os.path.join(root, "wiki", "status.md"))
        facts = G.present(G.Run(root))
        t = claude(root, PROMPTS["dream"], model)
        return G.g_dream(G.Run(root, t["calls"], t["text"]), before, facts), total(t), root
    if name == "overview":
        root = make_copy(work, "ready")
        t = claude(root, PROMPTS["overview"], model)
        return G.g_overview(G.Run(root, t["calls"], t["text"])), total(t), root
    if name == "route":
        out, turns = [], []
        for kind, expect in (("route-yes", True), ("route-no", False)):
            root = make_copy(work, "fresh")
            t = claude(root, PROMPTS[kind], model, max_turns=2)
            out += ["%s: %s" % (kind, m) for m in G.g_route(G.Run(root, t["calls"], t["text"]), expect)]
            turns.append(t)
        return out, total(*turns), root
    if name in ("growth-new", "growth-old"):
        root = make_copy(work, "ready" if name == "growth-new" else "oldrules")
        turns = []
        for p in PROMPTS["growth"]:
            turns.append(claude(root, p, model))
            subprocess.run(["git", "-C", root, "add", "-A"], capture_output=True)
            subprocess.run(["git", "-C", root, "-c", "user.name=ops", "-c", "user.email=ops@kestrel.invalid",
                            "commit", "-qm", "session"], capture_output=True)
        ask = claude(root, PROMPTS["growth-ask"], model)
        m = G.growth_metrics(G.Run(root))
        m["answer_ok"] = bool(re.search(r"8\.25", ask["text"])) and not re.search(r"7\.(25|60|90|40)|8\.10", ask["text"].split("8.25")[0][-40:] if "8.25" in ask["text"] else "")
        m["answer_live_calls"] = len(G.Run(root, ask["calls"]).live_calls())
        misses = [] if m["answer_ok"] else ["fresh session answered wrong: %s" % ask["text"][:120]]
        met = total(*turns, ask)
        met["growth"] = m
        return misses, met, root
    raise SystemExit("unknown scenario %s" % name)


ALL = ["init-fresh", "init-messy", "init-coexist", "write", "write-hook", "read", "dream", "overview", "route"]
RUNS = {"overview": 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--runs", type=int)
    ap.add_argument("--work", default=os.path.join(tempfile.gettempdir(), "kestrel-work"))
    ap.add_argument("--clean", action="store_true", help="remove run directories after grading")
    a = ap.parse_args()
    names = ALL if a.scenario == "all" else a.scenario.split(",")
    os.makedirs(a.work, exist_ok=True)
    for name in names:
        for i in range(1, (a.runs or RUNS.get(name, 3)) + 1):
            misses, met, root = scenario(name, a.work, i, a.model)
            row = {"scenario": name, "rep": i, "model": a.model, "pass": not misses, "misses": misses, **met, "root": root}
            open(os.path.join(a.work, "results.jsonl"), "a").write(json.dumps(row) + "\n")
            print("%-11s #%d %s calls=%d tok_in=%d tok_out=%d $%s %ss %s" % (name, i, "PASS" if not misses else "MISS",
                  met["calls"], met["tokens_in"], met["tokens_out"], met["cost"], met["secs"], "; ".join(misses)), flush=True)
            if a.clean:
                shutil.rmtree(os.path.dirname(root), ignore_errors=True)


if __name__ == "__main__":
    main()
