#!/usr/bin/env python3
"""SessionStart — rappelle les notes d'apprentissage en attente et la façon de les traiter (/kwa-learn)."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kwa import load_payload, project_dir  # noqa: E402


def main() -> int:
    d = load_payload()
    inbox = os.path.join(project_dir(d), ".claude", "kwa", "local", "inbox.md")
    try:
        n = sum(1 for x in open(inbox, encoding="utf-8") if x.strip())
    except OSError:
        n = 0
    if not n:
        return 0
    msg = (f"Kwa mémoire : {n} note(s) d'apprentissage en attente d'une session précédente "
           "(`python3 .claude/kwa/bin/kwa-memory pending`). Proposer à l'utilisateur de les traiter avec /kwa-learn "
           "quand le moment s'y prête ; ne pas les appliquer sans son accord.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
