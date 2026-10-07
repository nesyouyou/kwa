#!/usr/bin/env python3
"""PostToolUse Edit|Write — formate UNIQUEMENT les fichiers nouveaux.

Sur un fichier déjà suivi par git, reformater à la sauvegarde noie un changement d'une ligne dans un diff de 23
(le dépôt n'est pas forcément « clean »). On se contente de signaler ; un formatage global appartient à un lot dédié.
Politique : format.command (défaut « npx --no-install prettier --write {file} »), format.extensions, format.check.
Un outil absent se tait : il ne doit jamais produire d'erreur.
"""
from __future__ import annotations

import os
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kata import load_payload, load_policy, project_dir  # noqa: E402

DEFAULT_EXT = [".ts", ".tsx", ".js", ".jsx", ".json", ".md"]


def run(cmd: str, path: str, cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(shlex.split(cmd.replace("{file}", shlex.quote(path))), cwd=cwd, capture_output=True, text=True, timeout=60)


def main() -> int:
    d = load_payload()
    policy = load_policy(d).get("format", {})
    path = (d.get("tool_input") or {}).get("file_path", "")
    if not path or not os.path.isfile(path) or os.path.splitext(path)[1] not in policy.get("extensions", DEFAULT_EXT):
        return 0
    root = project_dir(d)
    write = policy.get("command", "npx --no-install prettier --write {file}")
    check = policy.get("check", "npx --no-install prettier --check {file}")
    try:
        if run("npx --no-install prettier --version", path, root).returncode != 0 \
                and "prettier" in write:
            return 0
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", path], cwd=root, capture_output=True).returncode == 0
        if tracked:
            if run(check, path, root).returncode != 0:
                print(f"note : {path} n'est pas au format attendu (pré-existant). Non corrigé automatiquement — "
                      "un formatage global appartient à un lot dédié.", file=sys.stderr)
            return 0
        r = run(write, path, root)
        if r.returncode != 0:
            print(f"le formateur a échoué sur {path} :\n{r.stdout}{r.stderr}", file=sys.stderr)
            return 1
    except (OSError, subprocess.SubprocessError):
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
