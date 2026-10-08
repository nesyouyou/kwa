"""Promesse du README : hors des marqueurs kwa:begin / kwa:end, AGENTS.md reste identique octet pour octet."""
import os
import re
import subprocess
import sys
import tempfile
import unittest

KWA = os.path.join(os.path.dirname(__file__), "..", "bin", "kwa")
CASES = {
    "lf": b"# Projet\n\nregle perso\n",
    "crlf": b"# Projet\r\n\r\nregle perso\r\n",
    "sans retour final": b"# Projet\n\nregle perso",
    "espaces et tabulations en fin de ligne": b"# Projet  \n\nregle perso \t\n",
    "saut de page et séparateur Unicode": b"# Projet\n\x0c\nligne\xe2\x80\xa8suite\n",
    "accents, emoji, bom": b"\xef\xbb\xbf# Projet \xc3\xa9\xc3\xa0 \xf0\x9f\x98\x80\n\nr\xc3\xa8gle\n",
    "lignes vides multiples": b"# A\n\n\n\n## B\n\n\n",
}


def install(d, *extra):
    return subprocess.run([sys.executable, KWA, "install", d, "--modules", "core", *extra], capture_output=True, text=True)


class ByteForByte(unittest.TestCase):
    def check(self, content, tail=b""):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "AGENTS.md")
        open(p, "wb").write(content)
        self.assertEqual(install(d).returncode, 0)
        first = open(p, "rb").read()
        self.assertTrue(first.startswith(content), "le contenu d'origine doit rester un préfixe exact")
        self.assertIn(b"<!-- kwa:begin", first)
        # ré-installation : strictement idempotente
        install(d)
        self.assertEqual(open(p, "rb").read(), first, "une seconde installation ne doit rien changer")
        # contenu ajouté APRÈS le bloc, puis mise à jour du bloc modifié à la main
        end = first.index(b"<!-- kwa:end -->") + len(b"<!-- kwa:end -->")
        eol = b"\r\n" if b"\r\n" in content else b"\n"
        after = first[:end].replace(b"profile=pr-flow", b"profile=pr-flow (retouche)") + eol + b"pied de page" + tail
        open(p, "wb").write(after)
        install(d)
        final = open(p, "rb").read()
        self.assertTrue(final.startswith(content), "le début est intact après mise à jour du bloc")
        self.assertTrue(final.endswith(b"pied de page" + tail), "la fin est intacte après mise à jour du bloc")
        self.assertNotIn(b"(retouche)", final, "la retouche faite dans le bloc est bien écrasée")
        self.assertEqual(final.count(b"<!-- kwa:begin"), 1)

    def test_cases(self):
        for name, content in CASES.items():
            with self.subTest(cas=name):
                self.check(content)

    def test_no_lf_leak_in_crlf_files(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "AGENTS.md")
        open(p, "wb").write(CASES["crlf"])
        install(d)
        data = open(p, "rb").read()
        self.assertFalse(re.search(rb"(?<!\r)\n", data), "un fichier CRLF ne doit contenir aucun LF seul, bloc compris")


if __name__ == "__main__":
    unittest.main()
