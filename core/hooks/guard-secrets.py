#!/usr/bin/env python3
"""PreToolUse Bash|Read|Grep — refuse la lecture de secrets (dotenv, clés, jetons CLI)."""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kata import decide, guarded, is_secret_path as is_secret, load_payload, segments  # noqa: E402

CMD_DENY = [
    (("printenv",), "affiche tout l'environnement"),
    (("gh", "auth", "token"), "affiche le jeton GitHub"),
    (("security", "find-generic-password"), "lit le trousseau macOS"),
    (("security", "find-internet-password"), "lit le trousseau macOS"),
    (("scw", "config", "get", "secret-key"), "affiche la clé secrète Scaleway"),
]


def main() -> None:
    d = load_payload()
    tool, ti = d.get("tool_name", ""), d.get("tool_input", {}) or {}
    if tool == "Read" and is_secret(ti.get("file_path", "")):
        decide("deny", f"lecture refusée : {os.path.basename(ti['file_path'])} est un fichier de secrets")
    if tool == "Grep" and is_secret(ti.get("path", "") or ""):
        decide("deny", "grep refusé sur un fichier de secrets")
    if tool != "Bash":
        return
    for words in segments(ti.get("command", "")):
        base = [os.path.basename(words[0])] + words[1:]
        for pat, why in CMD_DENY:
            if tuple(base[: len(pat)]) == pat:
                decide("deny", f"commande refusée : {' '.join(pat)} ({why})")
        if base[0] == "env" and len(words) == 1:
            decide("deny", "`env` seul affiche tout l'environnement")
        for w in words[1:]:
            if is_secret(w) or any(is_secret(x) for x in re.split(r"[=,:<>]", w) if x):
                decide("deny", f"commande refusée : touche un fichier de secrets ({os.path.basename(w)})")


if __name__ == "__main__":
    guarded(main)
