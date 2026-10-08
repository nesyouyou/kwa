#!/usr/bin/env python3
"""PreToolUse Bash — refuse rm / find -delete / git clean / rsync --delete hors du projet,
et toute suppression de .git ou .claude."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kwa import decide, guarded, load_payload, project_dir, segments  # noqa: E402

TMP = ("/tmp", "/private/tmp", "/var/folders", "/private/var/folders")


def inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def judge(path: str, cwd: str, root: str) -> None:
    if "$" in path or "`" in path:
        decide("ask", f"suppression d'une cible calculée à l'exécution ({path}) : confirmer")
    real = os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))
    if real in {"/", os.path.realpath(os.path.expanduser("~"))}:
        decide("deny", "suppression de / ou ~ refusée")
    if inside(real, root):
        rel = os.path.relpath(real, root)
        if rel == ".git" or rel.startswith(".git/") or rel == ".claude" or rel.startswith(".claude/hooks") or rel.startswith(".claude/kwa"):
            decide("deny", f"suppression de {rel} refusée (garde-fous du projet)")
        return
    if any(inside(real, t) for t in TMP):
        return
    decide("deny", f"suppression hors du projet refusée : {real}")


def main() -> None:
    d = load_payload()
    if d.get("tool_name") != "Bash":
        return
    root = project_dir(d)
    cwd = os.path.realpath(d.get("cwd") or root)
    for words in segments((d.get("tool_input") or {}).get("command", "")):
        prog, args = os.path.basename(words[0]), words[1:]
        if prog in {"rm", "rmdir", "unlink", "shred", "trash"}:
            for a in args:
                if not a.startswith("-"):
                    judge(a, cwd, root)
        elif prog == "find" and any(a in {"-delete", "-exec", "-execdir"} for a in args):
            if "-delete" in args or any(os.path.basename(a) in {"rm", "unlink"} for a in args):
                judge(args[0] if args and not args[0].startswith("-") else ".", cwd, root)
        elif prog == "git" and "clean" in args:
            decide("ask", "git clean supprime des fichiers non suivis")
        elif prog == "rsync" and any(a.startswith("--delete") for a in args):
            decide("ask", "rsync --delete peut effacer la destination")


if __name__ == "__main__":
    guarded(main)
