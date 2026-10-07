#!/usr/bin/env python3
"""PreToolUse Bash — règles propres au projet, lues dans .claude/kata.policy.json (bash.deny / bash.ask).

Une règle : {"id", "reason", "all": [regex…], "any": [regex…]}. Elle s'applique quand TOUS les motifs de
`all` ET au moins un de `any` trouvent dans la commande (corps de heredoc non exécuté exclu).
Deux motifs valent mieux qu'un : on bloque l'APPEL, pas la simple mention du mot dans une doc.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kata import decide, guarded, load_payload, load_policy, strip_heredocs  # noqa: E402


def applies(rule: dict, cmd: str) -> bool:
    all_, any_ = rule.get("all", []), rule.get("any", [])
    if not all_ and not any_:
        return False
    return all(re.search(p, cmd) for p in all_) and (not any_ or any(re.search(p, cmd) for p in any_))


def main() -> None:
    d = load_payload()
    if d.get("tool_name") != "Bash":
        return
    cmd = strip_heredocs((d.get("tool_input") or {}).get("command", ""))
    bash = load_policy(d).get("bash", {})
    for kind in ("deny", "ask"):  # le refus l'emporte toujours sur la demande
        for rule in bash.get(kind, []):
            if applies(rule, cmd):
                decide(kind, f"[{rule.get('id', kind)}] {rule['reason']}")


if __name__ == "__main__":
    guarded(main)
