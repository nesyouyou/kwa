#!/usr/bin/env python3
"""PreToolUse Bash — flux PR. Commit/push direct sur main refusés ; tout push de branche demande
validation ; les cas destructeurs (force, suppression) sont refusés sur les branches protégées."""
from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kata import decide, guarded, load_payload, load_policy, segments  # noqa: E402

PROTECTED = {"main", "master"} | {b for b in os.environ.get("KATA_PROTECTED_BRANCHES", "").split(",") if b}


def current_branch(cwd: str) -> str:
    try:
        return subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short", "-q", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def git_args(words: list[str]) -> list[str]:
    """Retire les options globales de git (-C x, -c k=v, --git-dir=…) et les alias connus."""
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"} else 1
    return words[i:]


def main() -> None:
    d = load_payload()
    if d.get("tool_name") != "Bash":
        return
    cwd = d.get("cwd") or os.getcwd()
    git_pol = load_policy(d).get("git", {})
    protected = PROTECTED | set(load_policy(d).get("protected_branches", []))
    push_branch = git_pol.get("push_branch", "ask")  # "ask" | "allow"
    direct_main_ok = os.environ.get("KATA_ALLOW_MAIN") == "1"
    for words in segments((d.get("tool_input") or {}).get("command", "")):
        prog = os.path.basename(words[0])
        if prog == "git":
            args = git_args(words)
            if not args:
                continue
            if args[0] in {"commit", "merge", "cherry-pick", "revert", "rebase"} and not direct_main_ok \
                    and current_branch(cwd) in protected:
                decide("deny", f"git {args[0]} sur {current_branch(cwd)} refusé : travailler sur une branche "
                               "dédiée et ouvrir une PR (KATA_ALLOW_MAIN=1 pour une exception assumée)")
            if args[0] == "push":
                rest = args[1:]
                lease = any(a == "--force-with-lease" or a.startswith("--force-with-lease=") for a in rest)
                hard = any(a in {"-f", "--force", "--mirror", "--all", "--delete", "-d"} or a.startswith("+") for a in rest)
                force = lease or hard
                targets = {re.sub(r"^\+|^refs/heads/", "", t.split(":")[-1]) for t in rest if not t.startswith("-")}
                if hard:
                    decide("deny", "push forcé ou destructif refusé (--force, -f, +ref, --delete, --all, --mirror). "
                                   "Après un rebase : --force-with-lease, avec confirmation.")
                if lease and (targets & protected or not targets):
                    decide("deny", "push forcé vers une branche protégée : refusé")
                if lease:
                    decide("ask", "push forcé (--force-with-lease) : confirmer explicitement")
                if not direct_main_ok and (targets & protected or (not targets and current_branch(cwd) in protected)):
                    decide("deny", "push direct vers main refusé : pousser la branche de travail et ouvrir une PR")
                if push_branch == "ask":
                    decide("ask", "git push publie la branche : confirmer.")
            if args[0] == "reset" and "--hard" in args:
                decide("ask", "git reset --hard détruit les modifications non commitées")
            if args[0] == "checkout" and ("--" in args or "." in args[1:]):
                decide("ask", "git checkout écrase les modifications locales")
            if args[0] in {"restore", "clean"} and any(a in {".", "-f", "-fd", "-fdx", "-ffd"} for a in args[1:]):
                decide("ask", f"git {args[0]} détruit des modifications locales")
            if args[0] in {"branch"} and any(a in {"-D", "--delete"} for a in args[1:]):
                decide("ask", "suppression de branche")
        elif prog == "gh":
            joined = " ".join(words[1:])
            if re.search(r"\bpr merge\b", joined):
                decide("ask", "gh pr merge : fusion = publication")
            if re.search(r"\b(release|repo)\s+(create|delete)\b", joined) or re.search(r"\bapi\b.*(-X|--method)\s*(PUT|PATCH|DELETE|POST)", joined, re.I):
                decide("ask", "appel GitHub en écriture : confirmer")


if __name__ == "__main__":
    guarded(main)
