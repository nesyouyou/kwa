#!/usr/bin/env python3
"""UserPromptSubmit : repère les « retiens : » et les corrections de l'utilisateur et en fait des candidats d'apprentissage.

Aucun appel à un modèle, rien n'est affiché (la sortie de ce hook entrerait dans le contexte) : une ligne dans
`.claude/kwa/local/inbox.md` et un signal dans `signals.jsonl`. Message court seulement, secrets masqués.
/kwa-learn les propose ensuite, rien n'est appliqué sans l'accord de l'utilisateur. KWA_JOURNAL=0 le coupe.
"""
from __future__ import annotations

import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kwa import load_payload, project_dir  # noqa: E402

EXPLICIT = re.compile(r"^\s*(?:retiens|à retenir|a retenir|remember)\s*(?:que)?\s*:\s*(.+)$", re.I | re.S)
CORRECTION = [re.compile(p, re.I) for p in (
    r"^\s*(?:non|no|nope)\b[ ,.!:;-]+(?:utilise|use|plutôt|rather|pas|not|ne |n'|don'?t|stop|arrête|c'est|that'?s|fais|do)\b",
    r"^\s*(?:ne fais (?:pas|plus)|arrête (?:de|d')|n'utilise (?:pas|plus)|stop (?:doing|using)|don'?t (?:use|do|add|touch)|do not (?:use|do|add|touch))",
    r"^\s*(?:je t'ai dit|i told you)\b",
    r"\b(?:c'est faux|ce n'est pas ça|c'est pas ça|that'?s wrong|that is wrong)\b",
)]
MAX_CORRECTION = 300
MAX_EXPLICIT = 400


def classify(prompt: str) -> tuple[str, str]:
    text = prompt.strip()
    if not text or text.startswith(("/", "<")):
        return "", ""
    m = EXPLICIT.match(text)
    if m:
        return "marqueur", m.group(1).strip()[:MAX_EXPLICIT]
    if len(text) <= MAX_CORRECTION and any(rx.search(text) for rx in CORRECTION):
        return "correction", text
    return "", ""


def main() -> int:
    d = load_payload()
    try:
        import _journal

        if not _journal.enabled():
            return 0
        kind, text = classify(str(d.get("prompt") or d.get("message") or ""))
        if not kind:
            return 0
        root = project_dir(d)
        text = " ".join(_journal.scrub(text).split())
        inbox = os.path.join(_journal.local_dir(root), "inbox.md")
        line = f"- [{time.strftime('%Y-%m-%d')}] [{'rule' if kind == 'marqueur' else 'pref'}] {text}\n"
        try:
            last = open(inbox, encoding="utf-8").read().splitlines()[-1:]
        except OSError:
            last = []
        if not last or last[0].split("] ", 2)[-1] != text:
            with open(inbox, "a", encoding="utf-8") as f:
                f.write(line)
            _journal.append_signal(root, kind, session=_journal._sid(d), text=text)
    except Exception:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
