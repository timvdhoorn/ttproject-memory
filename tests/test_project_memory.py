"""Tests for the project-memory lint and turn-end hook. Run: python3 -m unittest discover -s tests -v

Each lint rule gets one violating mutation of the clean fixture; the clean fixture passes.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import date, datetime, timedelta, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(REPO, "skills", "project-memory")
FIXTURE = os.path.join(REPO, "tests", "fixture")
LINT = os.path.join(SKILL, "scripts", "lint.py")
HOOK = os.path.join(SKILL, "assets", "stop_hook.py")
sys.path.insert(0, os.path.dirname(LINT))
import lint  # noqa: E402


def make_project():
    root = tempfile.mkdtemp(prefix="pm-test-")
    shutil.copytree(FIXTURE, root, dirs_exist_ok=True)
    shutil.copy(os.path.join(SKILL, "assets", "RULES.md"), os.path.join(root, "wiki", "RULES.md"))
    return root


def edit(root, rel, old=None, new="", append=None):
    path = os.path.join(root, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if old is not None:
        assert old in text, (rel, old)
        text = text.replace(old, new, 1)
    if append:
        text += append
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class LintTest(unittest.TestCase):
    def setUp(self):
        self.root = make_project()
        self.kb = os.path.join(self.root, "wiki")

    def tearDown(self):
        shutil.rmtree(self.root)

    def rules(self):
        return {r for _, _, r, _ in lint.lint(self.kb, date(2026, 3, 10))}

    def assertOnly(self, rule):
        self.assertEqual(self.rules(), {rule})

    def cli(self):
        return subprocess.run([sys.executable, LINT, self.kb], capture_output=True, text=True).returncode

    def test_clean_fixture_passes(self):
        self.assertEqual(self.rules(), set())
        self.assertEqual(self.cli(), 0)

    def test_cli_exit_codes(self):
        os.remove(os.path.join(self.kb, "status.md"))
        self.assertEqual(self.cli(), 1)
        self.assertEqual(subprocess.run([sys.executable, LINT, os.path.join(self.root, "nope")], capture_output=True).returncode, 2)

    def test_installed_copy_lints_its_own_folder(self):
        for src in (LINT, os.path.join(SKILL, "assets", "DREAM.md")):
            shutil.copy(src, self.kb)
        run = subprocess.run([sys.executable, os.path.join("wiki", "lint.py")], cwd=self.root, capture_output=True, text=True)
        self.assertEqual((run.returncode, run.stdout.splitlines()[0]), (0, "lint: 0 findings"))

    def test_missing_file(self):
        os.remove(os.path.join(self.kb, "status.md"))
        edit(self.root, "wiki/index.md", "- [Status](status.md): what is live, in progress, open\n", "")
        edit(self.root, "wiki/index.md", " Status: [status.md](status.md).", "")
        self.assertOnly("missing-file")

    def test_not_indexed(self):
        with open(os.path.join(self.kb, "web", "dns.md"), "w") as fh:
            fh.write("# DNS\n\n> Source: zone file\n> Updated: 2026-03-02\n\nZones.\n")
        self.assertOnly("not-indexed")

    def test_neighbour_docs(self):
        os.makedirs(os.path.join(self.kb, "adr"))
        for rel in ("adr/0001-x.md", "GLOSSARY.md"):
            with open(os.path.join(self.kb, rel), "w") as fh:
                fh.write("# X\n\nWe previously used Y (was 3).\n")
        self.assertOnly("neighbour-docs")

    def test_solutions_area_passes(self):
        os.makedirs(os.path.join(self.kb, "solutions"))
        with open(os.path.join(self.kb, "solutions", "bag.md"), "w") as fh:
            fh.write("# Bag\n\n> Source: designer\n> Updated: 2026-03-02\n\nForms.\n")
        edit(self.root, "wiki/index.md", append="- [Bag](solutions/bag.md): forms\n")
        self.assertEqual(self.rules(), set())

    def test_dream_due(self):
        log = os.path.join(self.kb, "log.md")
        dates = sorted(re.findall(r"(?m)^- (\d{4}-\d{2}-\d{2}) ", open(log).read()))
        first, last = date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
        self.assertIsNone(lint.dream_due(self.kb, first + timedelta(days=lint.DREAM_DAYS)))
        self.assertIn("dream due: last setup", lint.dream_due(self.kb, first + timedelta(days=lint.DREAM_DAYS + 1)))
        edit(self.root, "wiki/log.md", old="\n- ", new="\n- %s dream | Merged duplicates | index.md | lint\n- " % last)
        self.assertIsNone(lint.dream_due(self.kb, last + timedelta(days=60)))  # nothing logged since the dream
        self.assertEqual(self.rules(), set())

    def test_dead_link(self):
        edit(self.root, "wiki/web/iis.md", append="\nSee [export](../../raw/web/missing.xml).\n")
        self.assertOnly("dead-link")

    def test_dead_anchor(self):
        edit(self.root, "wiki/web/iis.md", append="\nSee [pools](iis.md#app-pool) and [facts](../index.md#facts).\n")
        self.assertOnly("dead-anchor")

    def test_live_anchor_passes(self):
        edit(self.root, "wiki/web/iis.md", append="\nSee [pools](#app-pools), [move](iis.md#transfer), [facts](../index.md#quick-facts).\n")
        self.assertEqual(self.rules(), set())

    def test_history(self):
        edit(self.root, "wiki/web/iis.md", append="\n- Port 8443 (was 8080).\n")
        self.assertOnly("history")

    def test_current_value_passes_history(self):
        edit(self.root, "wiki/web/iis.md", append="\n- Port 8443; the app was built in 2024.\n")
        self.assertEqual(self.rules(), set())

    def test_quoted_text_passes_history(self):
        edit(self.root, "wiki/web/iis.md", append='\n- The app shows "It was set to inactive (was 3)".\n')
        self.assertEqual(self.rules(), set())

    def test_log_duplicate(self):
        path = os.path.join(self.kb, "log.md")
        line = [l for l in open(path).read().splitlines() if l.startswith("- ")][0]
        edit(self.root, "wiki/log.md", old=line, new=line + "\n" + line)
        self.assertOnly("log-duplicate")

    def test_route_too_long(self):
        edit(self.root, "wiki/index.md", "app pools, bindings,", "app pools, bindings, certificates, rewrite rules, logging, health checks, recycle times,")
        self.assertOnly("route-too-long")

    def test_route_has_date(self):
        edit(self.root, "wiki/index.md", "app pools, bindings,", "app pools (changed 2026-03-02), bindings,")
        self.assertOnly("route-has-date")

    def test_route_empty(self):
        edit(self.root, "wiki/index.md", ": app pools, bindings, `svc-app` identity, file transfer", "")
        self.assertOnly("route-empty")

    def test_index_size(self):
        edit(self.root, "wiki/index.md", append="\n".join(["Filler that does not belong in the index."] * 160))
        self.assertOnly("index-size")

    def test_missing_quick_facts(self):
        edit(self.root, "wiki/index.md", "## Quick facts\n", "")
        edit(self.root, "wiki/index.md", "## General\n", "")
        self.assertIn("missing-quick-facts", self.rules())

    def test_page_size(self):
        edit(self.root, "wiki/web/iis.md", append="\n".join(["Filler line for size."] * 900))
        self.assertOnly("page-size")

    def test_status_size(self):
        edit(self.root, "wiki/status.md", append="\n".join(["- An old finished item that should have left."] * 120))
        self.assertOnly("page-size")

    def test_missing_source(self):
        edit(self.root, "wiki/web/iis.md", "> Source: [app pool export](../../raw/web/2026-03-02-apppool.xml); human doc \"2026-03-02 IIS change\"\n", "")
        self.assertOnly("missing-source")

    def test_missing_updated(self):
        edit(self.root, "wiki/web/iis.md", "> Updated: 2026-03-02", "> Updated: March")
        self.assertOnly("missing-updated")

    def test_log_format(self):
        edit(self.root, "wiki/log.md", append="- 2026-02-01 setup: free text without fields\n")
        self.assertOnly("log-format")

    def test_log_action(self):
        edit(self.root, "wiki/log.md", append="- 2026-02-01 discovery | found it | web/iis.md | query\n")
        self.assertOnly("log-action")

    def test_log_page(self):
        edit(self.root, "wiki/log.md", append="- 2026-02-01 add | found it | web/nope.md | query\n")
        self.assertOnly("log-page")

    def test_log_order(self):
        edit(self.root, "wiki/log.md", append="- 2026-04-01 add | newer at the bottom | web/iis.md | query\n")
        self.assertOnly("log-order")

    def test_log_size(self):
        edit(self.root, "wiki/log.md", append="".join("- 2026-01-01 add | entry %d | - | test\n" % i for i in range(200)))
        self.assertOnly("log-size")

    def test_marker_forbidden(self):
        edit(self.root, "wiki/web/iis.md", append="\n> **Status: Outdated** (2026-03-01): was svc-old.\n")
        self.assertOnly("marker-forbidden")

    def test_marker_undated(self):
        edit(self.root, "wiki/web/iis.md", append="\n> **Status: Disputed**: two exports disagree. Settle: query.\n")
        self.assertOnly("marker-undated")

    def test_marker_stale(self):
        edit(self.root, "wiki/web/iis.md", append="\n> **Status: Disputed** (2026-01-01): two exports disagree. Settle: query.\n")
        self.assertOnly("marker-stale")

    def test_fresh_marker_passes(self):
        edit(self.root, "wiki/web/iis.md", append="\n> **Status: Betwist** (2026-03-05): twee exports. Beslissen: query.\n")
        self.assertEqual(self.rules(), set())

    def test_line_too_long(self):
        edit(self.root, "wiki/web/iis.md", append="\n" + "word " * 60 + "\n")
        self.assertOnly("line-too-long")

    def test_long_line_in_code_fence_passes(self):
        edit(self.root, "wiki/web/iis.md", append="\n```\n" + "x" * 400 + "\n```\n")
        self.assertEqual(self.rules(), set())

    def test_secret_like(self):
        edit(self.root, "wiki/web/iis.md", append="\nconnection: password=Hunter2isverysecret\n")
        self.assertOnly("secret-like")

    def test_redacted_secret_passes(self):
        edit(self.root, "wiki/web/iis.md", append="\nconnection: password=<redacted>\n")
        self.assertEqual(self.rules(), set())


class HookTest(unittest.TestCase):
    def setUp(self):
        self.root = make_project()
        for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"]):
            subprocess.run(["git", "-C", self.root] + cmd, check=True)
        time.sleep(1.1)
        self.start = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.tx = os.path.join(self.root, "t.jsonl")

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_hook(self, tools, active=False):
        entries = [{"type": "user", "timestamp": self.start, "message": {"content": "do it"}}]
        entries += [{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": n, "input": i}]}} for n, i in tools]
        with open(self.tx, "w") as fh:
            fh.write("\n".join(json.dumps(e) for e in entries))
        data = {"transcript_path": self.tx, "stop_hook_active": active}
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.root)
        res = subprocess.run([sys.executable, HOOK], input=json.dumps(data), capture_output=True, text=True, env=env)
        self.assertEqual(res.returncode, 0, res.stderr)
        return json.loads(res.stdout) if res.stdout.strip() else None

    SSH = [("Bash", {"command": "ssh app01 hostname"})]

    def test_live_turn_without_page_edit_blocks(self):
        self.assertEqual(self.run_hook(self.SSH)["decision"], "block")

    def test_live_tool_name_triggers(self):
        self.assertEqual(self.run_hook([("mcp__remote__exec", {})])["decision"], "block")

    def test_log_edit_only_blocks(self):
        edit(self.root, "wiki/log.md", "# Log\n\n", "# Log\n\n- 2026-03-03 verify | checked | web/iis.md | ssh\n")
        self.assertEqual(self.run_hook(self.SSH)["decision"], "block")

    def test_touch_without_change_blocks(self):
        os.utime(os.path.join(self.root, "wiki", "web", "iis.md"))
        self.assertEqual(self.run_hook(self.SSH)["decision"], "block")

    def test_page_edit_passes(self):
        edit(self.root, "wiki/web/iis.md", append="\nBindings: port 443 only.\n")
        self.assertIsNone(self.run_hook(self.SSH))

    def test_committed_page_edit_passes(self):
        edit(self.root, "wiki/web/iis.md", append="\nBindings: port 443 only.\n")
        subprocess.run(["git", "-C", self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "docs"], check=True)
        self.assertIsNone(self.run_hook(self.SSH))

    def test_quiet_turn_passes(self):
        self.assertIsNone(self.run_hook([("Read", {"file_path": "x"})]))

    def test_second_stop_never_blocks(self):
        self.assertIsNone(self.run_hook(self.SSH, active=True))


if __name__ == "__main__":
    unittest.main()
