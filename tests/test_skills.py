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


class Humanize(unittest.TestCase):
    def read(self, *parts):
        return open(os.path.join(PACK, *parts), encoding="utf-8").read()

    def test_never_invents_and_bans_dashes(self):
        text = self.read("core", "skills", "humanize", "SKILL.md")
        self.assertIn("n'inventer aucun fait", text)
        self.assertIn("ne contient pas de tiret cadratin", text)

    def test_own_prose_has_no_dash(self):
        # la skill doit appliquer ce qu'elle enseigne : seule la ligne qui nomme les tirets les cite
        lines = [l for l in self.read("core", "skills", "humanize", "SKILL.md").splitlines() if "\u2014" in l or "\u2013" in l]
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("tiret cadratin", lines[0])

    def test_wired_into_commit_ship_and_router(self):
        for skill in ("commit", "ship"):
            self.assertIn("/kata-humanize", self.read("core", "skills", skill, "SKILL.md"))
        self.assertIn("/kata-humanize", self.read("core", "templates", "skills-router.md"))

    def test_module_ships_it(self):
        manifest = json.loads(self.read("manifest.json"))
        dests = [d.get("dest") for m in manifest["modules"].values() for d in (m.get("files") or {}).values()]
        self.assertIn(".claude/skills/kata-humanize", dests)


class Parcours(unittest.TestCase):
    SITE = os.path.join(PACK, "docs", "site")
    PAGES = ["parcours.html", "parcours-culture.html", "parcours-contexte.html", "parcours-harness.html"]

    def page(self, name):
        return open(os.path.join(self.SITE, name), encoding="utf-8").read()

    def test_harness_page_has_history_and_eight_stages_with_real_output(self):
        text = self.page("parcours-harness.html")
        for n in range(0, 9):
            self.assertIn(f'id="etape-{n}"', text)
        self.assertIn("non branchés dans settings.json", text)  # sortie réelle de kata doctor
        self.assertIn("permissionDecision", text)               # sortie réelle d'un garde

    def test_culture_and_context_stages(self):
        for name, count in (("parcours-culture.html", 6), ("parcours-contexte.html", 6)):
            text = self.page(name)
            for n in range(1, count + 1):
                self.assertIn(f'id="etape-{n}"', text, name)
        self.assertIn("parcours-widgets.js", self.page("parcours-culture.html"))
        self.assertTrue(os.path.isfile(os.path.join(self.SITE, "src", "parcours-widgets.js")))

    def test_hub_links_the_three_parcours(self):
        text = self.page("parcours.html")
        for target in self.PAGES[1:]:
            self.assertIn(f'href="{target}"', text)

    def test_context_examples_are_valid_and_secret_free(self):
        text = self.page("parcours-contexte.html")
        self.assertIn("${DB_CONNECTION_STRING}", text)
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9]{8,}", text))

    def test_no_temp_path_or_private_term(self):
        for name in self.PAGES:
            text = self.page(name)
            for bad in ("/var/folders", "/private/", "kata-parcours-", "/Users/"):
                self.assertNotIn(bad, text, name)
            self.assertIsNone(re.search(r"(?i)mycecca|cecca|\\bvault\\b", text), name)

    def test_prose_has_no_em_dash_outside_real_output(self):
        # la prose écrite à la main applique /kata-humanize ; seules les sorties réelles d'un garde portent « Kata — »
        for name in ("parcours.html", "parcours-culture.html", "parcours-contexte.html"):
            body = re.search(r"<main.*?</main>", self.page(name), re.S).group(0)
            self.assertNotIn("\u2014", body, name)

    def test_linked_from_home_and_readme(self):
        self.assertIn("parcours.html", open(os.path.join(PACK, "README.md"), encoding="utf-8").read())
        self.assertIn("parcours.html", open(os.path.join(self.SITE, "template.html"), encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
