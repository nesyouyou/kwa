"""Crédits : chaque skill créditée porte sa ligne d'origine, chaque source a sa licence, aucune skill n'est orpheline de classement."""
import json
import os
import re
import unittest

PACK = os.path.join(os.path.dirname(__file__), "..")
CREDITS = json.load(open(os.path.join(PACK, "credits.json")))
SKILLS = os.path.join(PACK, "core", "skills")


class Credits(unittest.TestCase):
    def test_every_credited_skill_carries_its_line(self):
        for src in CREDITS["sources"]:
            for sk in src["skills"]:
                with self.subTest(source=src["id"], skill=sk):
                    path = os.path.join(SKILLS, sk, "SKILL.md")
                    self.assertTrue(os.path.isfile(path), f"{sk} n'existe pas")
                    self.assertIn(src.get("credit_lines", {}).get(sk, src["credit_line"]), open(path, encoding="utf-8").read())

    def test_every_credit_line_in_a_skill_is_declared(self):
        declared = {(s.get("credit_lines", {}).get(sk, s["credit_line"]), sk) for s in CREDITS["sources"] for sk in s["skills"]}
        for d in os.listdir(SKILLS):
            f = os.path.join(SKILLS, d, "SKILL.md")
            if not os.path.isfile(f):
                continue
            for line in re.findall(r"^> (Inspiré .*)$", open(f, encoding="utf-8").read(), re.M):
                self.assertIn((line, d), declared, f"{d} cite une source absente de credits.json")

    def test_licenses_exist_and_name_the_author(self):
        for src in CREDITS["sources"]:
            path = os.path.join(PACK, src["license_file"])
            self.assertTrue(os.path.isfile(path), src["license_file"])
            text = open(path, encoding="utf-8").read()
            self.assertIn("MIT License", text)
            self.assertIn(src.get("license_holder", src["author"]).split()[0], text)

    def test_body_never_names_upstream_projects(self):
        for d in os.listdir(SKILLS):
            f = os.path.join(SKILLS, d, "SKILL.md")
            if os.path.isfile(f):
                body = "\n".join(l for l in open(f, encoding="utf-8").read().splitlines() if not l.startswith("> Inspiré"))
                self.assertNotRegex(body, r"(?i)pocock|ponytail|superpowers", f"{d} nomme une source dans le corps")


if __name__ == "__main__":
    unittest.main()
