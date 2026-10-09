"""Coloration syntaxique des blocs de code : elle ajoute des balises, jamais du texte."""
import html
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "site", "src"))
import hl  # noqa: E402

SAMPLES = {
    "json": '{"a": [1, true, null, "x\\"y"], "b": {"c": -2.5e3}}',
    "rpc": '-> {"jsonrpc": "2.0", "id": 1}\n<- {"result": {"ok": true}}',
    "shell": '#!/bin/bash\n# note\nFILE=$(cat | jq -r \'.x // empty\')\nfor m in "a" "b"; do\n  echo "x $m" >&2\n  exit 2\ndone',
    "frontmatter": '---\nname: x\ndescription: Faire ça. À utiliser.\ndisable: false\n---\n\n# Titre\n- une `ligne` "citée"',
    "http": "GET /orders/42 HTTP/1.1\nAuthorization: Bearer <jeton>\n\n200 OK\n{ \"id\": 42 }",
    "plain": "Texte <brut> & simple : avec « guillemets »",
}


def text_of(markup: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


class Highlight(unittest.TestCase):
    def test_text_is_never_altered(self):
        for name, sample in SAMPLES.items():
            self.assertEqual(text_of(hl.highlight(sample)), sample, name)

    def test_json_keys_values_and_literals_get_their_own_colours(self):
        out = hl.highlight('{"name": "x", "n": 3, "ok": true}')
        self.assertIn('<span class="sx-k">&quot;name&quot;</span>'.replace("&quot;", '"'), out)
        self.assertIn('<span class="sx-s">"x"</span>', out)
        self.assertIn('<span class="sx-n">3</span>', out)
        self.assertIn('<span class="sx-b">true</span>', out)

    def test_shell_comments_flags_and_variables(self):
        out = hl.highlight("# titre\nkwa install ./p --dry-run\necho $HOME", "shell")
        self.assertIn('<span class="sx-c"># titre</span>', out)
        self.assertIn('<span class="sx-f">--dry-run</span>', out)
        self.assertIn('<span class="sx-v">$HOME</span>', out)

    def test_language_is_detected(self):
        self.assertEqual(hl.detect('{"a": 1}'), "json")
        self.assertEqual(hl.detect("---\nname: x\n---\n"), "frontmatter")
        self.assertEqual(hl.detect("#!/bin/bash\nexit 0"), "shell")
        self.assertEqual(hl.detect("GET /x HTTP/1.1"), "http")
        self.assertEqual(hl.detect("Résume le contrat."), "plain")

    def test_prose_is_not_coloured(self):
        self.assertNotIn("sx-", hl.highlight("Contexte : première relance, ton cordial."))

    def test_markup_in_code_is_escaped(self):
        out = hl.highlight('<script>alert("x")</script>')
        self.assertNotIn("<script>", out)


if __name__ == "__main__":
    unittest.main()
