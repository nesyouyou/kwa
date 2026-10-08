"""Installeur : idempotence, bloc géré, CLAUDE.md, settings.json, retouches locales, dry-run."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

KWA = os.path.join(os.path.dirname(__file__), "..", "bin", "kwa")


def kwa(*args):
    return subprocess.run([sys.executable, KWA, *args], capture_output=True, text=True)


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
        r = kwa("install", self.t)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("<!-- kwa:begin", open(self.p("AGENTS.md")).read())
        self.assertEqual(open(self.p("CLAUDE.md")).read().strip(), "@AGENTS.md")
        self.assertTrue(os.access(self.p(".claude/kwa/hooks/guard-git.py"), os.X_OK))
        self.assertTrue(os.path.exists(self.p(".claude/skills/kwa-commit/SKILL.md")))
        s = json.load(open(self.p(".claude/settings.json")))
        self.assertEqual(len(s["hooks"]["PreToolUse"]), 3)
        self.assertEqual(kwa("doctor", self.t).returncode, 0)

    def test_idempotent(self):
        kwa("install", self.t)
        before = tree(self.t)
        r = kwa("install", self.t)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(tree(self.t).keys(), before.keys(), "aucun backup ni fichier en plus")
        self.assertEqual(tree(self.t), before)

    def test_existing_content_untouched_outside_markers(self):
        open(self.p("AGENTS.md"), "w").write("# Mon projet\n\nrègle perso\n\n## Fin\nbas de page\n")
        kwa("install", self.t)
        a = open(self.p("AGENTS.md")).read()
        self.assertTrue(a.startswith("# Mon projet\n\nrègle perso\n\n## Fin\nbas de page\n"))
        # ré-installation : seul l'intérieur du bloc peut changer
        open(self.p("AGENTS.md"), "w").write(a.replace("règle perso", "règle perso modifiée") + "\npied\n")
        kwa("install", self.t)
        b = open(self.p("AGENTS.md")).read()
        self.assertIn("règle perso modifiée", b)
        self.assertTrue(b.rstrip().endswith("pied"))

    def test_claude_md_with_own_rules_not_overwritten(self):
        open(self.p("CLAUDE.md"), "w").write("# règles à moi\n")
        r = kwa("install", self.t)
        self.assertEqual(open(self.p("CLAUDE.md")).read(), "# règles à moi\n")
        self.assertIn("À FUSIONNER", r.stdout)
        self.assertEqual(kwa("doctor", self.t).returncode, 1)

    def test_claude_md_symlink_kept(self):
        open(self.p("AGENTS.md"), "w").write("# x\n")
        os.symlink("AGENTS.md", self.p("CLAUDE.md"))
        kwa("install", self.t)
        self.assertTrue(os.path.islink(self.p("CLAUDE.md")))

    def test_settings_merge_keeps_existing_and_backs_up(self):
        os.makedirs(self.p(".claude"))
        open(self.p(".claude/settings.json"), "w").write(json.dumps({
            "permissions": {"allow": ["Bash(ls)"]},
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "mon-hook"}]}]}}))
        kwa("install", self.t)
        s = json.load(open(self.p(".claude/settings.json")))
        self.assertEqual(s["permissions"]["allow"], ["Bash(ls)"])
        cmds = [h["command"] for e in s["hooks"]["PreToolUse"] if e["matcher"] == "Bash" for h in e["hooks"]]
        self.assertIn("mon-hook", cmds)
        self.assertEqual(len([c for c in cmds if "guard-git" in c]), 1)
        self.assertTrue([f for f in os.listdir(self.p(".claude")) if f.startswith("settings.json.bak-")])

    def test_invalid_settings_left_intact(self):
        os.makedirs(self.p(".claude"))
        open(self.p(".claude/settings.json"), "w").write("{pas du json")
        r = kwa("install", self.t)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(open(self.p(".claude/settings.json")).read(), "{pas du json")

    def test_local_edit_backed_up_then_restored(self):
        kwa("install", self.t)
        f = self.p(".claude/rules/kwa-git-discipline.md")
        open(f, "a").write("\nretouche locale\n")
        r = kwa("install", self.t)
        self.assertIn("sauvegardé", r.stdout)
        self.assertNotIn("retouche locale", open(f).read())
        found = [os.path.join(d, x) for d, _, fs in os.walk(self.p(".claude/kwa/backup")) for x in fs]
        self.assertTrue(any(open(x).read().endswith("retouche locale\n") for x in found))

    def test_dry_run_writes_nothing(self):
        r = kwa("install", self.t, "--dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(tree(self.t), {})

    def test_never_runs_git(self):
        subprocess.run(["git", "init", "-q", self.t], check=True)
        kwa("install", self.t)
        log = subprocess.run(["git", "-C", self.t, "log"], capture_output=True, text=True)
        self.assertNotEqual(log.returncode, 0, "aucun commit ne doit exister")
        self.assertEqual(subprocess.run(["git", "-C", self.t, "diff", "--cached", "--name-only"],
                                        capture_output=True, text=True).stdout, "")

    def test_refuses_installing_into_pack(self):
        self.assertEqual(kwa("install", os.path.join(os.path.dirname(__file__), "..")).returncode, 2)

    def test_status_reports_drift(self):
        kwa("install", self.t)
        self.assertEqual(kwa("status", self.t).returncode, 0)
        open(self.p(".claude/kwa/hooks/guard-git.py"), "a").write("# x\n")
        self.assertEqual(kwa("status", self.t).returncode, 1)


class MigrationFromOldName(unittest.TestCase):
    """Un projet installé sous l'ancien nom (dossier .claude/kata, marqueurs kata:begin) est migré sans perte."""

    OLD_AGENTS_HEAD = "# AGENTS.md\r\n\r\nRègles du projet, à garder octet pour octet.\r\n\r\n"
    OLD_AGENTS_TAIL = "\r\n## Après le bloc\r\nSans retour final"

    def setUp(self):
        self.t = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.t, ".git", "info"))
        with open(self.p("AGENTS.md"), "w", newline="") as f:
            f.write(self.OLD_AGENTS_HEAD + self.OLD_AGENTS_TAIL)
        self.assertEqual(kwa("install", self.t).returncode, 0)
        with open(self.p("AGENTS.md"), newline="") as f:
            text = f.read()
        i, j = text.index("<!-- kwa:begin"), text.index("<!-- kwa:end -->") + len("<!-- kwa:end -->")
        with open(self.p("AGENTS.md"), "w", newline="") as f:  # texte du projet avant ET après le bloc
            f.write(text[:i] + text[i:j] + self.OLD_AGENTS_TAIL)
        self.to_legacy()

    def p(self, *a):
        return os.path.join(self.t, *a)

    def to_legacy(self):
        """Reproduit la disposition de l'ancien nom à partir d'une installation neuve."""
        os.rename(self.p(".claude", "kwa"), self.p(".claude", "kata"))
        for d, _, fs in os.walk(self.p(".claude", "kata")):
            for f in fs:
                if "kwa" in f:
                    os.rename(os.path.join(d, f), os.path.join(d, f.replace("kwa", "kata")))
        for sub in ("skills", "rules"):
            base = self.p(".claude", sub)
            for name in os.listdir(base):
                if name.startswith("kwa-"):
                    os.rename(os.path.join(base, name), os.path.join(base, "kata-" + name[4:]))
        os.rename(self.p(".claude", "kwa.policy.json"), self.p(".claude", "kata.policy.json"))
        for rel in (".claude/settings.json", ".claude/kata/state.json", ".claude/kata.policy.json", "AGENTS.md"):
            with open(self.p(rel), newline="") as f:
                text = f.read()
            with open(self.p(rel), "w", newline="") as f:
                f.write(text.replace("kwa", "kata"))
        s = json.load(open(self.p(".claude/settings.json")))
        s["hooks"]["PreToolUse"].append({"matcher": "Bash", "hooks": [{"type": "command", "command": "./mon-hook-projet.sh"}]})
        json.dump(s, open(self.p(".claude/settings.json"), "w"))
        os.makedirs(self.p(".claude", "kata", "local"))
        open(self.p(".claude", "kata", "local", "notes.jsonl"), "w").write('{"kind":"gotcha"}\n')
        with open(self.p(".claude", "rules", "kata-git-discipline.md"), "a") as f:
            f.write("\nretouche locale\n")

    def test_dry_run_changes_nothing_and_says_what_it_would_do(self):
        before = tree(self.t)
        r = kwa("install", self.t, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("migration :", r.stdout)
        self.assertEqual(tree(self.t), before)

    def test_old_install_is_detected(self):
        self.assertEqual(kwa("status", self.t).returncode, 1)
        self.assertIn("ancien nom", kwa("status", self.t).stdout)
        self.assertEqual(kwa("doctor", self.t).returncode, 1)

    def test_migration(self):
        r = kwa("install", self.t)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("migration :", r.stdout)
        # ancien nom disparu, nouveau en place
        self.assertFalse(os.path.exists(self.p(".claude", "kata")))
        self.assertFalse(os.path.exists(self.p(".claude", "kata.policy.json")))
        self.assertFalse([n for n in os.listdir(self.p(".claude", "skills")) if n.startswith("kata-")])
        self.assertFalse([n for n in os.listdir(self.p(".claude", "rules")) if n.startswith("kata-")])
        self.assertTrue(os.path.exists(self.p(".claude/kwa/hooks/guard-git.py")))
        self.assertTrue(os.path.exists(self.p(".claude/skills/kwa-commit/SKILL.md")))
        # politique : renommée, clé mise à jour
        self.assertEqual(json.load(open(self.p(".claude/kwa.policy.json")))["kwa"], 1)
        # notes et sauvegardes conservées, retouche locale sauvegardée
        self.assertEqual(open(self.p(".claude/kwa/local/notes.jsonl")).read(), '{"kind":"gotcha"}\n')
        saved = [os.path.join(d, f) for d, _, fs in os.walk(self.p(".claude/kwa/backup")) for f in fs]
        self.assertTrue(any(x.endswith("kata-git-discipline.md") for x in saved), saved)
        # settings : plus aucun ancien hook, le hook du projet reste, les nouveaux sont branchés
        cmds = [h["command"] for ev in json.load(open(self.p(".claude/settings.json")))["hooks"].values()
                for e in ev for h in e["hooks"]]
        self.assertFalse([c for c in cmds if ".claude/kata/" in c], cmds)
        self.assertIn("./mon-hook-projet.sh", cmds)
        self.assertTrue([c for c in cmds if ".claude/kwa/hooks/guard-git.py" in c])
        # AGENTS.md : hors bloc, octet pour octet ; marqueurs neufs
        with open(self.p("AGENTS.md"), newline="") as f:
            text = f.read()
        self.assertTrue(text.startswith(self.OLD_AGENTS_HEAD), "début du fichier intact (fins de ligne comprises)")
        self.assertTrue(text.endswith(self.OLD_AGENTS_TAIL), "fin du fichier intacte, sans retour final ajouté")
        self.assertIn("<!-- kwa:begin", text)
        self.assertNotIn("kata", text.lower())
        self.assertEqual(kwa("doctor", self.t).returncode, 0)

    def test_migration_is_idempotent(self):
        kwa("install", self.t)
        before = tree(self.t)
        r = kwa("install", self.t)
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("migration :", r.stdout)
        self.assertEqual(tree(self.t).keys(), before.keys())

    def test_unknown_file_in_old_folder_is_kept_and_reported(self):
        open(self.p(".claude", "kata", "mine.txt"), "w").write("à moi")
        r = kwa("install", self.t)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(open(self.p(".claude", "kata", "mine.txt")).read(), "à moi")
        self.assertIn("À VÉRIFIER", r.stdout)


if __name__ == "__main__":
    unittest.main()
