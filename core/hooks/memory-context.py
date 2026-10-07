#!/usr/bin/env python3
"""SessionStart — rappelle les notes d'apprentissage en attente et la façon de les traiter (/kata-learn)."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kata import load_payload, project_dir  # noqa: E402


def main() -> int:
    d = load_payload()
    inbox = os.path.join(project_dir(d), ".claude", "kata", "local", "inbox.md")
    try:
        n = sum(1 for x in open(inbox, encoding="utf-8") if x.strip())
    except OSError:
        n = 0
    if not n:
        return 0
    msg = (f"Kata mémoire : {n} note(s) d'apprentissage en attente d'une session précédente "
           "(`python3 .claude/kata/bin/kata-memory pending`). Proposer à l'utilisateur de les traiter avec /kata-learn "
           "quand le moment s'y prête ; ne pas les appliquer sans son accord.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
