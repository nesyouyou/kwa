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
                self.assertEqual(fm["name"], f"kwa-{d}")
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
        names = {f"kwa-{d}" for d in self.skills()}
        for d in self.skills():
            text = open(os.path.join(SKILLS, d, "SKILL.md"), encoding="utf-8").read()
            for ref in set(re.findall(r"(?<![\w./-])/(kwa-[a-z]+(?:-[a-z]+)*)(?![\w/])", text)):
                with self.subTest(skill=d, ref=ref):
                    self.assertIn(ref, names, f"{d} renvoie vers {ref}, qui n'existe pas")

    def test_manifest_covers_every_skill(self):
        man = json.load(open(os.path.join(PACK, "manifest.json")))["modules"]
        dests = " ".join(s["dest"] for m in man.values() for s in m.get("files", {}).values())
        for d in self.skills():
            self.assertIn(f".claude/skills/kwa-{d}", dests, f"kwa-{d} n'est dans aucun module")


class Router(unittest.TestCase):
    def run_router(self, installed):
        root = os.path.realpath(tempfile.mkdtemp())
        os.makedirs(os.path.join(root, ".claude", "kwa"))
        open(os.path.join(root, ".claude", "kwa", "router.md"), "w").write(
            open(os.path.join(PACK, "core", "templates", "skills-router.md")).read())
        for s in installed:
            os.makedirs(os.path.join(root, ".claude", "skills", s))
        p = subprocess.run([sys.executable, os.path.join(HOOKS, "skills-router.py")], input=json.dumps({"cwd": root}),
                           capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": root})
        return json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"] if p.stdout.strip() else ""

    def test_only_installed_skills_are_listed(self):
        out = self.run_router(["kwa-debug", "kwa-commit"])
        self.assertIn("/kwa-debug", out)
        self.assertIn("/kwa-commit", out)
        self.assertNotIn("/kwa-deploy", out)

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
            self.assertIn("/kwa-humanize", self.read("core", "skills", skill, "SKILL.md"))
        self.assertIn("/kwa-humanize", self.read("core", "templates", "skills-router.md"))

    def test_module_ships_it(self):
        manifest = json.loads(self.read("manifest.json"))
        dests = [d.get("dest") for m in manifest["modules"].values() for d in (m.get("files") or {}).values()]
        self.assertIn(".claude/skills/kwa-humanize", dests)


class Parcours(unittest.TestCase):
    SITE = os.path.join(PACK, "docs", "site")
    PAGES = ["parcours.html", "parcours-culture.html", "parcours-contexte.html", "parcours-harness.html"]

    def page(self, name):
        return open(os.path.join(self.SITE, name), encoding="utf-8").read()

    def test_harness_page_has_history_and_eight_stages_with_real_output(self):
        text = self.page("parcours-harness.html")
        for n in range(0, 9):
            self.assertIn(f'id="etape-{n}"', text)
        self.assertIn("non branchés dans settings.json", text)  # sortie réelle de kwa doctor
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
            for bad in ("/var/folders", "/private", "kwa-parcours-", "/Users/"):
                self.assertNotIn(bad, text, name)
            self.assertIsNone(re.search(r"(?i)mycecca|cecca|\\bvault\\b", text), name)

    def test_prose_has_no_em_dash_outside_real_output(self):
        # la prose écrite à la main applique /kwa-humanize ; seules les sorties réelles d'un garde portent « Kwa — »
        for name in ("parcours.html", "parcours-culture.html", "parcours-contexte.html"):
            body = re.search(r"<main.*?</main>", self.page(name), re.S).group(0)
            self.assertNotIn("\u2014", body, name)

    def test_linked_from_home_and_readme(self):
        self.assertIn("parcours.html", open(os.path.join(PACK, "README.md"), encoding="utf-8").read())
        self.assertIn("parcours.html", open(os.path.join(self.SITE, "template.html"), encoding="utf-8").read())


class Neutral(unittest.TestCase):
    def test_no_organisation_name_in_tracked_files(self):
        # le dépôt est personnel pour l'instant : aucun nom d'organisation, y compris dans les pages générées
        files = subprocess.run(["git", "ls-files"], cwd=PACK, capture_output=True, text=True).stdout.split("\n")
        needle = "naka" + "ma"
        hits = []
        for f in files:
            path = os.path.join(PACK, f)
            if not f or not os.path.isfile(path) or f.endswith((".woff2", ".ttf", ".png", ".jpg", ".svg")):
                continue
            if needle in open(path, encoding="utf-8", errors="ignore").read().lower() or needle in f.lower():
                hits.append(f)
        self.assertEqual(hits, [])


class ThemeIcon(unittest.TestCase):
    def test_every_page_uses_an_icon_button_without_visible_label(self):
        site = os.path.join(PACK, "docs", "site")
        pages = [f for f in os.listdir(site) if f.endswith(".html")]
        self.assertGreaterEqual(len(pages), 7)
        for name in pages:
            text = open(os.path.join(site, name), encoding="utf-8").read()
            button = re.search(r'<button[^>]*id="theme".*?</button>', text, re.S)
            self.assertIsNotNone(button, name)
            html = button.group(0)
            self.assertIn("i-sun", html, name)
            self.assertIn("i-moon", html, name)
            self.assertIn("aria-label", html, name)
            self.assertNotRegex(re.sub(r"<[^>]+>", "", html).strip(), r"\S", f"{name} : le bouton ne porte aucun texte visible")
            self.assertNotIn("Thème sombre</button>", text, name)


class Circuit(unittest.TestCase):
    SITE = os.path.join(PACK, "docs", "site")

    def read(self, *p):
        return open(os.path.join(self.SITE, *p), encoding="utf-8").read()

    def test_pages_mount_the_circuit_not_the_animated_board(self):
        for name in ("board.html", "index.html"):
            text = self.read(name)
            self.assertIn("circuit.js", text, name)
            self.assertIn("KwaCircuit.mount", text, name)
            self.assertNotIn("KwaBoard.mount", text, name)

    def test_no_autoplay_and_every_step_has_a_label(self):
        js = self.read("src", "circuit.js")
        for banned in ("setInterval", "setTimeout", "Pause", "Vitesse", "Rejouer"):
            self.assertNotIn(banned, js, "le circuit ne se lit pas tout seul : rien ne doit bouger hors de l'action de la personne")
        data = self.read("src", "board.js")
        for sid, count in (("feature", 12), ("bug", 8), ("delivery", 10)):
            labels = re.search(sid + r": \[(.*?)\]", js, re.S).group(1)
            self.assertEqual(len(re.findall(r"'(?:[^'\\]|\\.)*'", labels)), count, sid)
        self.assertIn("data: { COLS: COLS", data)
        self.assertIn("Étape précédente", js)
        self.assertIn("Étape suivante", js)


class BorderStyle(unittest.TestCase):
    """Choix de style : un trait épais d'un seul côté est permis sur un rectangle, jamais sur un coin arrondi."""

    def test_no_thick_one_sided_border_on_rounded_box(self):
        site = os.path.join(PACK, "docs", "site")
        files = [os.path.join(site, "template.html")] + [os.path.join(site, "src", f) for f in os.listdir(os.path.join(site, "src")) if f.endswith(".css")]
        bad = []
        for path in files:
            text = open(path, encoding="utf-8").read()
            for rule in re.findall(r"[^{}]+\{[^{}]*\}", text):
                one_side = re.search(r"border-(?:left|right|top|bottom)\s*:\s*([2-9]|\d{2,})px", rule)
                radius = re.search(r"border-radius\s*:\s*([1-9]\d*)px", rule)
                if one_side and radius and int(radius.group(1)) >= 6:
                    bad.append(os.path.basename(path) + " : " + rule.strip()[:90])
        self.assertEqual(bad, [])


class MotionRespect(unittest.TestCase):
    """Toute animation du site doit se couper quand la personne demande de réduire les animations."""

    def test_reduced_motion_is_honoured_wherever_there_is_animation(self):
        site = os.path.join(PACK, "docs", "site")
        for rel in ("src/circuit.css", "src/parcours.css"):
            text = open(os.path.join(site, rel), encoding="utf-8").read()
            if "@keyframes" in text or "transition:" in text:
                self.assertIn("prefers-reduced-motion", text, rel)
        js = open(os.path.join(site, "src", "circuit.js"), encoding="utf-8").read()
        self.assertIn("prefers-reduced-motion", js)
        tpl = open(os.path.join(site, "template.html"), encoding="utf-8").read()
        self.assertIn("prefers-reduced-motion: reduce", tpl)
        self.assertIn("startViewTransition", tpl)


if __name__ == "__main__":
    unittest.main()
