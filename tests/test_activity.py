"""Journal d'activité : un fichier par session, écritures concurrentes, plafond, nettoyage des secrets, purge."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

from helpers import HOOKS
from test_tools import git_repo, sh

sys.path.insert(0, HOOKS)
import _activity  # noqa: E402
import _journal  # noqa: E402

# faux secret assemblé à l'exécution : aucun jeton d'apparence réelle n'est écrit dans ce fichier
FAKE_GH = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123"


def files(repo):
    d = os.path.join(repo, ".claude", "kwa", "local", "activity")
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


class Sessions(unittest.TestCase):
    def setUp(self):
        self.repo = git_repo({"README.md": "x"})
        os.environ.pop("KWA_JOURNAL", None)

    def test_each_session_writes_its_own_file(self):
        _activity.record(self.repo, "sess-A", "skill", name="/kwa:debug")
        _activity.record(self.repo, "sess-B", "tool", tool="Edit", brick="faire", target="src/a.py")
        _activity.record(self.repo, "sess-A", "tool", tool="Bash", brick="prouver", target="python3 -m unittest")
        self.assertEqual(len(files(self.repo)), 2)
        a = _activity.read_session(self.repo, "sess-A")
        self.assertEqual([e["kind"] for e in a], ["skill", "tool"])
        self.assertEqual([e["kind"] for e in _activity.read_session(self.repo, "sess-B")], ["tool"])
        self.assertEqual(a[0]["agent"], "claude")

    def test_a_worktree_writes_in_the_main_repository(self):
        sh("git", "-C", self.repo, "add", "-A")
        sh("git", "-C", self.repo, "commit", "-qm", "init")
        wt = os.path.join(tempfile.mkdtemp(), "wt")
        sh("git", "-C", self.repo, "worktree", "add", "-q", "-b", "feat/x", wt)
        _activity.record(wt, "sess-W", "turn")
        self.assertEqual(len(files(self.repo)), 1)
        self.assertEqual(files(wt), [])

    def test_two_concurrent_writers_never_mix_their_lines(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import _activity\n"
                "for i in range(400): _activity.record(sys.argv[2], 'sess-C', 'tool', tool='Read', brick='cadrer',"
                " target='src/' + sys.argv[3] + str(i) + '.py')")
        procs = [subprocess.Popen([sys.executable, "-c", code, HOOKS, self.repo, w]) for w in ("a", "b")]
        for p in procs:
            self.assertEqual(p.wait(), 0)
        lines = open(os.path.join(self.repo, ".claude", "kwa", "local", "activity", files(self.repo)[0]), encoding="utf-8").read().splitlines()
        self.assertEqual(len(lines), 800)
        for line in lines:
            json.loads(line)   # aucune ligne coupée ni mêlée

    def test_no_secret_and_short_targets(self):
        _activity.record(self.repo, "sess-S", "tool", tool="Bash", target=f"curl -H 'Authorization: token {FAKE_GH}' x")
        _activity.record(self.repo, "sess-S", "tool", tool="Bash", target="echo " + "y" * 500)
        raw = open(os.path.join(self.repo, ".claude", "kwa", "local", "activity", files(self.repo)[0]), encoding="utf-8").read()
        self.assertNotIn(FAKE_GH, raw)
        self.assertLessEqual(max(len(e.get("target", "")) for e in _activity.read_session(self.repo, "sess-S")), _activity.TARGET_CHARS)

    def test_disabled_with_the_journal(self):
        os.environ["KWA_JOURNAL"] = "0"
        try:
            _activity.record(self.repo, "sess-D", "turn")
        finally:
            os.environ.pop("KWA_JOURNAL", None)
        self.assertEqual(files(self.repo), [])


class Cap(unittest.TestCase):
    def setUp(self):
        self.repo = git_repo({"README.md": "x"})
        self.saved = _activity.SESSION_BYTES
        _activity.SESSION_BYTES = 600

    def tearDown(self):
        _activity.SESSION_BYTES = self.saved

    def test_beyond_the_cap_steps_are_kept_and_tools_only_counted(self):
        for i in range(30):
            _activity.record(self.repo, "sess-K", "tool", tool="Read", brick="cadrer", target=f"f{i}.py")
        _activity.record(self.repo, "sess-K", "skill", name="/kwa:tdd")
        events = _activity.read_session(self.repo, "sess-K")
        self.assertLess(len(events), 31)                     # le détail a cessé d'être écrit…
        self.assertEqual(events[-1]["kind"], "skill")        # …pas les étapes
        path = _activity.session_file(self.repo, "sess-K")
        counts = json.load(open(path + ".counts.json"))
        self.assertEqual(counts["cadrer"] + sum(1 for e in events if e["kind"] == "tool"), 30)


class Prune(unittest.TestCase):
    def setUp(self):
        self.repo = git_repo({"README.md": "x"})

    def test_old_sessions_go_and_the_folder_stays_under_its_cap(self):
        for s in ("old", "mid", "new"):
            _activity.record(self.repo, f"sess-{s}", "turn")
        now = time.time()
        old = _activity.session_file(self.repo, "sess-old")
        os.utime(old, (now - 40 * 86400, now - 40 * 86400))
        self.assertEqual(_activity.prune(self.repo, None, now), 1)
        self.assertFalse(os.path.exists(old))
        # la durée se règle dans la politique
        mid = _activity.session_file(self.repo, "sess-mid")
        os.utime(mid, (now - 10 * 86400, now - 10 * 86400))
        self.assertEqual(_activity.prune(self.repo, {"memory": {"activity_days": 7}}, now), 1)
        # plafond global : les plus anciens partent d'abord
        saved = _activity.TOTAL_BYTES
        _activity.TOTAL_BYTES = 1
        try:
            for i in range(3):
                _activity.record(self.repo, f"sess-x{i}", "turn")
                os.utime(_activity.session_file(self.repo, f"sess-x{i}"), (now - 100 + i, now - 100 + i))
            _activity.prune(self.repo, None, now)
        finally:
            _activity.TOTAL_BYTES = saved
        self.assertLessEqual(len(files(self.repo)), 1)

    def test_signals_are_pruned_and_housekeeping_purges_both(self):
        path = _journal.signals_path(self.repo)
        old = {"t": "x", "ts": time.time() - 60 * 86400, "kind": "refus", "key": "k", "text": ""}
        new = {**old, "ts": time.time()}
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(old) + "\n" + json.dumps(new) + "\n")
        _activity.record(self.repo, "sess-old", "turn")
        stale = _activity.session_file(self.repo, "sess-old")
        os.utime(stale, (time.time() - 40 * 86400,) * 2)
        _journal.housekeeping(self.repo, None)
        self.assertEqual([json.loads(x)["ts"] for x in open(path)], [new["ts"]])
        self.assertFalse(os.path.exists(stale))


if __name__ == "__main__":
    unittest.main()


def run_hook(repo, payload, env=None):
    p = {"session_id": "sess-H", "cwd": repo, **payload}
    e = {k: v for k, v in os.environ.items() if k not in ("KWA_AGENT", "COPILOT_PLUGIN_DATA", "KWA_JOURNAL")}
    return subprocess.run([sys.executable, os.path.join(HOOKS, "activity-log.py")], input=json.dumps(p),
                          capture_output=True, text=True, env={**e, "CLAUDE_PROJECT_DIR": repo, **(env or {})})


class Hook(unittest.TestCase):
    def setUp(self):
        self.repo = git_repo({"README.md": "x", ".claude/kwa.policy.json": json.dumps({"verify": {"commands": ["make check"]}})})

    def events(self):
        return _activity.read_session(self.repo, "sess-H")

    def test_a_session_becomes_lines_one_per_event_and_nothing_is_printed(self):
        steps = [
            {"hook_event_name": "SessionStart", "source": "startup"},
            {"hook_event_name": "PostToolUse", "tool_name": "Skill", "tool_input": {"skill": "kwa:debug"}},
            {"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_input": {"file_path": os.path.join(self.repo, "src", "panier.py")}},
            {"hook_event_name": "PostToolUse", "tool_name": "Edit", "tool_input": {"file_path": os.path.join(self.repo, "src", "panier.py")}},
            {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "make check"}},
            {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "git commit -m fix"}},
            {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "ls -la"}},
            {"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"subagent_type": "kwa:reviewer", "description": "relire"}},
            {"hook_event_name": "PostToolUse", "tool_name": "Agent", "tool_input": {"subagent_type": "kwa:reviewer"}},
            {"hook_event_name": "Stop"},
        ]
        for s in steps:
            r = run_hook(self.repo, s)
            self.assertEqual((r.returncode, r.stdout), (0, ""), r.stderr)
        ev = self.events()
        self.assertEqual([e["kind"] for e in ev], ["session", "skill", "tool", "tool", "tool", "tool", "tool", "agent", "agent-end", "turn"])
        self.assertEqual(ev[0].get("branch"), "main")
        self.assertEqual(ev[1]["name"], "kwa:debug")
        self.assertEqual([e.get("brick", "") for e in ev[2:7]], ["cadrer", "faire", "prouver", "livrer", ""])
        self.assertEqual(ev[3]["target"], "src/panier.py")   # chemin relatif au projet
        self.assertEqual(ev[7]["name"], "kwa:reviewer")

    def test_the_agent_is_named_and_codex_tools_are_understood(self):
        run_hook(self.repo, {"hook_event_name": "PostToolUse", "tool_name": "apply_patch",
                             "tool_input": {"input": "*** Begin Patch\n*** Update File: src/a.py\n@@\n"}}, {"KWA_AGENT": "codex"})
        run_hook(self.repo, {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "pytest"}},
                 {"COPILOT_PLUGIN_DATA": tempfile.mkdtemp()})
        a, b = self.events()
        self.assertEqual((a["agent"], a["brick"], a["target"]), ("codex", "faire", "src/a.py"))
        self.assertEqual((b["agent"], b["brick"]), ("copilot", "prouver"))

    def test_a_guard_refusal_is_a_step_of_the_journal(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "cwd": self.repo, "session_id": "sess-H"}
        e = {k: v for k, v in os.environ.items() if k not in ("KWA_JOURNAL",)}
        r = subprocess.run([sys.executable, os.path.join(HOOKS, "guard-git.py")], input=json.dumps(payload), capture_output=True,
                           text=True, env={**e, "CLAUDE_PROJECT_DIR": self.repo, "KWA_RUNTIME": "plugin"})
        self.assertIn("deny", r.stdout)
        deny = [x for x in self.events() if x["kind"] == "deny"]
        self.assertEqual(len(deny), 1)
        self.assertEqual(deny[0]["tool"], "Bash")

    def test_off_with_the_journal(self):
        run_hook(self.repo, {"hook_event_name": "Stop"}, {"KWA_JOURNAL": "0"})
        self.assertEqual(self.events(), [])


ACTIVITY = os.path.join(os.path.dirname(__file__), "..", "core", "bin", "kwa-activity")


class Summary(unittest.TestCase):
    def test_the_workflow_comes_from_the_first_skill_then_the_branch(self):
        self.assertEqual(_activity.workflow([{"kind": "skill", "name": "kwa:debug"}, {"kind": "skill", "name": "kwa:ship"}]),
                         ("bug", "skill kwa:debug"))
        self.assertEqual(_activity.workflow([{"kind": "session", "branch": "fix/14-dark-navy-pills"}])[0], "bug")
        self.assertEqual(_activity.workflow([{"kind": "session", "branch": "feat/82-kwa-activity"}])[0], "feature")
        self.assertEqual(_activity.workflow([{"kind": "session", "branch": "main"}]), ("feature", "par défaut"))

    def test_a_session_summary(self):
        ev = [{"kind": "session", "ts": 1000, "agent": "claude", "branch": "fix/14-dark-navy-pills"},
              {"kind": "skill", "ts": 1010, "name": "kwa:debug"},
              {"kind": "tool", "ts": 1020, "brick": "faire"}, {"kind": "tool", "ts": 1030, "brick": "prouver"},
              {"kind": "agent", "ts": 1040, "name": "kwa:reviewer"}, {"kind": "deny", "ts": 1050, "reason": "git commit sur main refusé"},
              {"kind": "turn", "ts": 1300}]
        x = _activity.summarize(ev, {"cadrer": 4}, now=1300 + 60)
        self.assertEqual((x["workflow"], x["issue"], x["minutes"], x["turns"], x["subagents"]), ("bug", 14, 5, 1, 1))
        self.assertEqual(x["bricks"]["cadrer"], 4)   # les outils comptés au-delà du plafond
        self.assertEqual(x["denials"], ["git commit sur main refusé"])
        self.assertTrue(x["live"])
        self.assertFalse(_activity.summarize(ev, None, now=1300 + 3600)["live"])


class Command(unittest.TestCase):
    def setUp(self):
        self.repo = git_repo({"README.md": "x"})
        for sid, branch, skill in (("aaaa1111", "fix/14-x", "kwa:debug"), ("bbbb2222", "feat/82-y", None)):
            _activity.record(self.repo, sid, "session", branch=branch)
            if skill:
                _activity.record(self.repo, sid, "skill", name=skill)
            _activity.record(self.repo, sid, "tool", tool="Edit", brick="faire", target="src/a.py")

    def kwa(self, *args):
        return sh(sys.executable, ACTIVITY, *args, cwd=self.repo)

    def test_list_detail_filters_and_json(self):
        out = self.kwa().stdout
        self.assertIn("Corriger un bug", out)
        self.assertIn("Développer une fonctionnalité", out)
        detail = self.kwa("aaaa").stdout
        self.assertIn("Workflow : Corriger un bug (d'après skill kwa:debug)", detail)
        self.assertIn("issue #14", detail)
        self.assertIn("Étapes : Faire 1", detail)
        rows = json.loads(self.kwa("--branch", "feat/82-y", "--json").stdout)
        self.assertEqual([r["session"] for r in rows], ["bbbb2222"])
        self.assertEqual(len(json.loads(self.kwa("--live", "--json").stdout)), 2)
        self.assertNotEqual(self.kwa("zzzz").returncode, 0)

    def test_prune_on_demand(self):
        old = _activity.session_file(self.repo, "aaaa1111")
        os.utime(old, (time.time() - 40 * 86400,) * 2)
        self.assertIn("1 fichier", self.kwa("--prune").stdout)
        self.assertFalse(os.path.exists(old))
