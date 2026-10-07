"""Installeur : idempotence, bloc géré, CLAUDE.md, settings.json, retouches locales, dry-run."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

KATA = os.path.join(os.path.dirname(__file__), "..", "bin", "kata")


def kata(*args):
    return subprocess.run([sys.executable, KATA, *args], capture_output=True, text=True)


def tree(root):
    out = {}
    for d, _, fs in os.walk(root):
        if "/.git" in d:
            continue
        for f in fs:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root)] = open(p, "rb").read()
    return out


class Install(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.mkdtemp()

    def p(self, *a):
        return os.path.join(self.t, *a)

    def test_fresh_install(self):
        r = kata("install", self.t)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("<!-- kata:begin", open(self.p("AGENTS.md")).read())
        self.assertEqual(open(self.p("CLAUDE.md")).read().strip(), "@AGENTS.md")
        self.assertTrue(os.access(self.p(".claude/kata/hooks/guard-git.py"), os.X_OK))
        self.assertTrue(os.path.exists(self.p(".claude/skills/kata-commit/SKILL.md")))
        s = json.load(open(self.p(".claude/settings.json")))
        self.assertEqual(len(s["hooks"]["PreToolUse"]), 3)
        self.assertEqual(kata("doctor", self.t).returncode, 0)

    def test_idempotent(self):
        kata("install", self.t)
        before = tree(self.t)
        r = kata("install", self.t)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(tree(self.t).keys(), before.keys(), "aucun backup ni fichier en plus")
        self.assertEqual(tree(self.t), before)

    def test_existing_content_untouched_outside_markers(self):
        open(self.p("AGENTS.md"), "w").write("# Mon projet\n\nrègle perso\n\n## Fin\nbas de page\n")
        kata("install", self.t)
        a = open(self.p("AGENTS.md")).read()
        self.assertTrue(a.startswith("# Mon projet\n\nrègle perso\n\n## Fin\nbas de page\n"))
        # ré-installation : seul l'intérieur du bloc peut changer
        open(self.p("AGENTS.md"), "w").write(a.replace("règle perso", "règle perso modifiée") + "\npied\n")
        kata("install", self.t)
        b = open(self.p("AGENTS.md")).read()
        self.assertIn("règle perso modifiée", b)
        self.assertTrue(b.rstrip().endswith("pied"))

    def test_claude_md_with_own_rules_not_overwritten(self):
        open(self.p("CLAUDE.md"), "w").write("# règles à moi\n")
        r = kata("install", self.t)
        self.assertEqual(open(self.p("CLAUDE.md")).read(), "# règles à moi\n")
        self.assertIn("À FUSIONNER", r.stdout)
        self.assertEqual(kata("doctor", self.t).returncode, 1)

    def test_claude_md_symlink_kept(self):
        open(self.p("AGENTS.md"), "w").write("# x\n")
        os.symlink("AGENTS.md", self.p("CLAUDE.md"))
        kata("install", self.t)
        self.assertTrue(os.path.islink(self.p("CLAUDE.md")))

    def test_settings_merge_keeps_existing_and_backs_up(self):
        os.makedirs(self.p(".claude"))
        open(self.p(".claude/settings.json"), "w").write(json.dumps({
            "permissions": {"allow": ["Bash(ls)"]},
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "mon-hook"}]}]}}))
        kata("install", self.t)
        s = json.load(open(self.p(".claude/settings.json")))
        self.assertEqual(s["permissions"]["allow"], ["Bash(ls)"])
        cmds = [h["command"] for e in s["hooks"]["PreToolUse"] if e["matcher"] == "Bash" for h in e["hooks"]]
        self.assertIn("mon-hook", cmds)
        self.assertEqual(len([c for c in cmds if "guard-git" in c]), 1)
        self.assertTrue([f for f in os.listdir(self.p(".claude")) if f.startswith("settings.json.bak-")])

    def test_invalid_settings_left_intact(self):
        os.makedirs(self.p(".claude"))
        open(self.p(".claude/settings.json"), "w").write("{pas du json")
        r = kata("install", self.t)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(open(self.p(".claude/settings.json")).read(), "{pas du json")

    def test_local_edit_backed_up_then_restored(self):
        kata("install", self.t)
        f = self.p(".claude/rules/kata-git-discipline.md")
        open(f, "a").write("\nretouche locale\n")
        r = kata("install", self.t)
        self.assertIn("sauvegardé", r.stdout)
        self.assertNotIn("retouche locale", open(f).read())
        found = [os.path.join(d, x) for d, _, fs in os.walk(self.p(".claude/kata/backup")) for x in fs]
        self.assertTrue(any(open(x).read().endswith("retouche locale\n") for x in found))

    def test_dry_run_writes_nothing(self):
        r = kata("install", self.t, "--dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(tree(self.t), {})

    def test_never_runs_git(self):
        subprocess.run(["git", "init", "-q", self.t], check=True)
        kata("install", self.t)
        log = subprocess.run(["git", "-C", self.t, "log"], capture_output=True, text=True)
        self.assertNotEqual(log.returncode, 0, "aucun commit ne doit exister")
        self.assertEqual(subprocess.run(["git", "-C", self.t, "diff", "--cached", "--name-only"],
                                        capture_output=True, text=True).stdout, "")

    def test_refuses_installing_into_pack(self):
        self.assertEqual(kata("install", os.path.join(os.path.dirname(__file__), "..")).returncode, 2)

    def test_status_reports_drift(self):
        kata("install", self.t)
        self.assertEqual(kata("status", self.t).returncode, 0)
        open(self.p(".claude/kata/hooks/guard-git.py"), "a").write("# x\n")
        self.assertEqual(kata("status", self.t).returncode, 1)


if __name__ == "__main__":
    unittest.main()
