#!/usr/bin/env python3
"""SessionStart (startup|clear|compact) — rappelle à l'agent quand invoquer quelle skill Kata.

La table vient de .claude/kata/router.md ; seules les lignes dont la skill est réellement installée sont gardées
(.claude/skills/kata-*). Court et calibré : une demande conversationnelle n'appelle aucune skill.
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kata import load_payload, project_dir  # noqa: E402


def main() -> int:
    root = project_dir(load_payload())
    try:
        text = open(os.path.join(root, ".claude", "kata", "router.md"), encoding="utf-8").read()
    except OSError:
        return 0
    kept = []
    for line in text.splitlines():
        m = re.search(r"/(kata-[a-z-]+)", line)
        if m and line.startswith("|") and not os.path.isdir(os.path.join(root, ".claude", "skills", m.group(1))):
            continue
        kept.append(line)
    if not any(re.search(r"/kata-", x) for x in kept if x.startswith("|")):
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(kept)}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
