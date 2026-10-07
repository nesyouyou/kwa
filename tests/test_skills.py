"""Qualité des skills : frontmatter valide, pas de résidu, références croisées existantes, routeur filtré."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.join(os.path.dirname(__file__), "..")
SKILLS = os.path.join(PACK, "core", "skills")
HOOKS = os.path.join(PACK, "core", "hooks")


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} : frontmatter manquant"
    return {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)}, text


class Lint(unittest.TestCase):
    def skills(self):
        return sorted(d for d in os.listdir(SKILLS) if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md")))

    def test_frontmatter_and_names(self):
        for d in self.skills():
            with self.subTest(skill=d):
                fm, text = frontmatter(os.path.join(SKILLS, d, "SKILL.md"))
                self.assertEqual(fm["name"], f"kata-{d}")
                self.assertGreater(len(fm["description"]), 40, "description trop courte")
                self.assertLessEqual(len(fm["description"]), 700)
                self.assertLessEqual(len(text.splitlines()), 220, "SKILL.md trop long : déplacer le détail en annexe")

    def test_description_survives_yaml_parsing(self):
        """Un « #N » ou un « : » dans une description non quotée tronque ou casse l'en-tête YAML : la skill perd ses déclencheurs."""
        for d in self.skills():
            with self.subTest(skill=d):
                line = open(os.path.join(SKILLS, d, "SKILL.md"), encoding="utf-8").read().split("\n")[2]
                value = line.split(": ", 1)[1]
                if value[:1] not in "\"'":
                    self.assertIsNone(re.search(r"\s#", value), "« #… » est lu comme un commentaire YAML : description tronquée")
                    self.assertNotIn(": ", value, "« : » dans une description non quotée casse le YAML")
                self.assertNotRegex(value, r"(?i)\bvault\b")

    def test_no_residue(self):
        for d in self.skills():
            for dirpath, _, files in os.walk(os.path.join(SKILLS, d)):
                for f in files:
                    p = os.path.join(dirpath, f)
                    text = "\n".join(l for l in open(p, encoding="utf-8").read().splitlines() if not l.startswith("> Inspiré"))
                    with self.subTest(file=os.path.relpath(p, PACK)):
                        self.assertNotRegex(text, r"(?i)superpowers", "mention de superpowers")
                        self.assertNotRegex(text, r"(?i)lorem ipsum|titre de slide|une idée forte")
                        self.assertNotIn("EXTREMELY", text)

    def test_cross_references_exist(self):
        names = {f"kata-{d}" for d in self.skills()}
        for d in self.skills():
            text = open(os.path.join(SKILLS, d, "SKILL.md"), encoding="utf-8").read()
            for ref in set(re.findall(r"(?<![\w./-])/(kata-[a-z]+(?:-[a-z]+)*)(?![\w/])", text)):
                with self.subTest(skill=d, ref=ref):
                    self.assertIn(ref, names, f"{d} renvoie vers {ref}, qui n'existe pas")

    def test_manifest_covers_every_skill(self):
        man = json.load(open(os.path.join(PACK, "manifest.json")))["modules"]
        dests = " ".join(s["dest"] for m in man.values() for s in m.get("files", {}).values())
        for d in self.skills():
            self.assertIn(f".claude/skills/kata-{d}", dests, f"kata-{d} n'est dans aucun module")


class Router(unittest.TestCase):
    def run_router(self, installed):
        root = os.path.realpath(tempfile.mkdtemp())
        os.makedirs(os.path.join(root, ".claude", "kata"))
        open(os.path.join(root, ".claude", "kata", "router.md"), "w").write(
            open(os.path.join(PACK, "core", "templates", "skills-router.md")).read())
        for s in installed:
            os.makedirs(os.path.join(root, ".claude", "skills", s))
        p = subprocess.run([sys.executable, os.path.join(HOOKS, "skills-router.py")], input=json.dumps({"cwd": root}),
                           capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": root})
        return json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"] if p.stdout.strip() else ""

    def test_only_installed_skills_are_listed(self):
        out = self.run_router(["kata-debug", "kata-commit"])
        self.assertIn("/kata-debug", out)
        self.assertIn("/kata-commit", out)
        self.assertNotIn("/kata-deploy", out)

    def test_silent_when_nothing_installed(self):
        self.assertEqual(self.run_router([]), "")


if __name__ == "__main__":
    unittest.main()
