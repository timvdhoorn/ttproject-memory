"""Self-test for the scenario graders: each fails a known-bad output and passes a known-good one.

Run: python3 -m unittest discover -s tests -v
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "evals"))
import graders as G  # noqa: E402
import run as R  # noqa: E402

READY = os.path.join(REPO, "evals", "project", "states", "ready")


def sub(root, rel, old, new):
    p = os.path.join(root, rel)
    s = open(p, encoding="utf-8").read()
    assert old in s, (rel, old)
    open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))


def add_kb(root):
    """What a good init writes into the fresh project."""
    shutil.copytree(os.path.join(READY, "wiki"), os.path.join(root, "wiki"))
    for src in ("assets/RULES.md", "assets/DREAM.md", "scripts/lint.py"):
        shutil.copy(os.path.join(R.SKILL, src), os.path.join(root, "wiki"))
    shutil.copy(os.path.join(READY, "AGENTS.md"), os.path.join(root, "AGENTS.md"))
    open(os.path.join(root, "CLAUDE.md"), "w").write("@AGENTS.md\n@wiki/index.md\n")
    sub(root, "wiki/api/payments.md", "`/hooks/pay`", "`/hooks/pay/v2`")
    sub(root, "wiki/api/booking-api.md", "| `deposit_eur` | 50 |", "| `deposit_eur` | 50 |\n| `rate_limit_per_min` | 120 |")


class GraderTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="g-")

    def tearDown(self):
        shutil.rmtree(self.work)

    def test_init_ask(self):
        root = R.make_copy(self.work, "fresh")
        self.assertEqual(G.g_init_ask(G.Run(root, [("Read", {})], "1. Folder? 2. Language?")), [])
        add_kb(root)
        self.assertTrue(G.g_init_ask(G.Run(root, [("Write", {})], "Done.")))

    def test_init_fresh(self):
        root = R.make_copy(self.work, "fresh")
        add_kb(root)
        self.assertEqual(G.g_init_fresh(G.Run(root)), [])
        open(os.path.join(root, "CLAUDE.md"), "a").write("@wiki/index.md\n")
        open(os.path.join(root, "AGENTS.md"), "a").write("\n## Project memory\n\nAgain.\n")
        sub(root, "wiki/index.md", "host `app01.kestrel.internal`", "the host")
        self.assertEqual(len(G.g_init_fresh(G.Run(root))), 3)

    def test_init_messy(self):
        root = R.make_copy(self.work, "messy")
        self.assertTrue(G.g_init_messy(G.Run(root)))  # untouched docs/ fails
        shutil.rmtree(os.path.join(root, "docs"))
        add_kb(root)
        self.assertEqual(G.g_init_messy(G.Run(root)), [])
        open(os.path.join(root, "wiki", "status.md"), "a").write(  # a date is not a value
            "\n- Release with the longer max booking days went live 2026-10-07.\n")
        self.assertEqual(G.g_init_messy(G.Run(root)), [])
        sub(root, "wiki/api/booking-api.md", "## Config", "## Config\n\n> **Status: Outdated** (2026-07-01)\n> Port was 8080.")
        misses = G.g_init_messy(G.Run(root))
        self.assertTrue(any("outdated-style" in m for m in misses) and any("superseded" in m for m in misses))

    def test_coexist(self):
        root = R.make_copy(self.work, "messy+coexist")
        self.assertEqual(G.g_coexist(G.Run(root)), [])
        open(os.path.join(root, "GLOSSARY.md"), "a").write("\n**Hold**: x\n")
        os.rename(os.path.join(root, "docs", "adr", "0001-deposit-held-at-paylane.md"), os.path.join(root, "docs", "adr", "0001.md"))
        sub(root, "AGENTS.md", "## Agent skills\n", "## Agent skills\n\nSee the wiki.\n")
        shutil.copy(os.path.join(R.SKILL, "assets", "RULES.md"), os.path.join(root, "docs", "RULES.md"))
        self.assertEqual(len(G.g_coexist(G.Run(root))), 5)

    def good_write(self, root):
        sub(root, ".server/etc/booking-api.conf", "rate_limit_per_min = 120", "rate_limit_per_min = 300")
        sub(root, "wiki/api/booking-api.md", "| `deposit_eur` | 50 |", "| `deposit_eur` | 50 |\n| `rate_limit_per_min` | 300 |")
        sub(root, "wiki/api/payments.md", "`/hooks/pay`", "`/hooks/pay/v2`")
        sub(root, "wiki/api/payments.md", "- `currency`: EUR", "- `currency`: EUR\n- Paylane webhook calls come from 203.0.113.0/24.")
        sub(root, "wiki/log.md", "\n- 2026-11-02", "\n- 2026-11-11 change | Rate limit 300, webhook path fixed | api/booking-api.md | fleetctl\n- 2026-11-02")

    def test_daily_write(self):
        root = R.make_copy(self.work, "ready")
        self.good_write(root)
        self.assertEqual(G.g_daily_write(G.Run(root)), [])
        sub(root, "wiki/api/booking-api.md", "| `rate_limit_per_min` | 300 |", "| `rate_limit_per_min` | 300 (previously 120) |")
        sub(root, "wiki/data/pricing.md", "| cargo", "Paylane IPs: 203.0.113.0/24.\n\n| cargo")
        misses = G.g_daily_write(G.Run(root))
        self.assertTrue(any("history" in m for m in misses) and any("2 pages" in m for m in misses))

    def test_daily_write_untouched_fails(self):
        root = R.make_copy(self.work, "ready")
        self.assertGreaterEqual(len(G.g_daily_write(G.Run(root))), 4)

    def test_daily_read(self):
        root = R.make_copy(self.work, "ready")
        self.assertEqual(G.g_daily_read(G.Run(root, [("Read", {"file_path": "wiki/api/booking-api.md"})], "The deposit is EUR 50.")), [])
        self.assertEqual(len(G.g_daily_read(G.Run(root, [("Bash", {"command": "bin/fleetctl config show booking-api"})], "EUR 40"))), 2)

    def test_dream(self):
        root = R.make_copy(self.work, "dirty")
        before = os.path.getsize(os.path.join(root, "wiki", "status.md"))
        facts = G.present(G.Run(root))
        self.assertTrue(G.g_dream(G.Run(root), before, facts))
        sub(root, "wiki/data/pricing.md", re.search(r"## Deposit\n- .*\n", open(os.path.join(root, "wiki/data/pricing.md")).read()).group(0), "")
        sub(root, "wiki/data/database.md", "## Backups\n- The database is backed up nightly at 02:30 to `/srv/backup`.\n\n", "")
        s = open(os.path.join(root, "wiki/ops/operations.md")).read()
        open(os.path.join(root, "wiki/ops/operations.md"), "w").write(re.sub(r"\n> \*\*Status: Disputed\*\*.*\n", "\n", s))
        s = open(os.path.join(root, "wiki/status.md")).read()
        open(os.path.join(root, "wiki/status.md"), "w").write(re.sub(r"## Done\n(- .*\n)+\n", "", s))
        sub(root, "wiki/log.md", "\n- 2026-11-02", "\n- 2026-11-11 dream | Merged duplicates, status shortened | index.md | lint\n- 2026-11-02")
        self.assertEqual(G.g_dream(G.Run(root), before, facts), [])
        sub(root, "wiki/data/pricing.md", "| ebike | 7.25 |", "| ebike | 6.50 |")
        self.assertTrue(G.g_dream(G.Run(root), before, facts))

    def test_overview(self):
        root = R.make_copy(self.work, "ready")
        self.assertEqual(G.g_overview(G.Run(root, [], "Live: booking-api 2.4.1. Lint: 0 findings.")), [])
        open(os.path.join(root, "wiki", "log.md"), "a").write("x\n")
        self.assertTrue(G.g_overview(G.Run(root, [], "Live: booking-api. Lint clean.")))

    def test_route(self):
        root = R.make_copy(self.work, "fresh")
        skill = ("Skill", {"skill": "project-memory", "args": "init"})
        bash = ("Bash", {"command": "ls"})
        self.assertEqual(G.g_route(G.Run(root, [skill]), True), [])
        self.assertTrue(G.g_route(G.Run(root, [bash]), True))
        self.assertEqual(G.g_route(G.Run(root, [bash]), False), [])
        self.assertTrue(G.g_route(G.Run(root, [skill]), False))

    def test_growth_metrics(self):
        root = R.make_copy(self.work, "ready")
        sub(root, "wiki/data/pricing.md", "| ebike | 7.25 |", "| ebike | 8.25 |")
        m = G.growth_metrics(G.Run(root))
        self.assertEqual((m["old_blocks"], m["current_places"], m["stale_ebike_values"]), (0, 1, 0))
        sub(root, "wiki/data/pricing.md", "| ebike | 8.25 |", "| ebike | 8.25 |\n\n> **Status: Outdated** (2026-11-01)\n> ebike was 7.25.")
        m = G.growth_metrics(G.Run(root))
        self.assertEqual((m["old_blocks"], m["stale_ebike_values"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
