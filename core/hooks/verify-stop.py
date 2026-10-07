#!/usr/bin/env python3
"""Stop — refuse de rendre la main sur du rouge. OPT-IN : KATA_STOP_VERIFY=1.

Sur une session courte, typecheck + lint à chaque tour coûtent plus qu'ils ne rapportent ; sur une session longue et
autonome, c'est ce qui empêche « ça a l'air fini » de passer pour une vérification. Commandes : verify.commands de la
politique. Claude Code reprend la main après 8 blocages consécutifs : pas de boucle infinie.
"""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kata import load_payload, load_policy, project_dir  # noqa: E402


def main() -> int:
    if os.environ.get("KATA_STOP_VERIFY") != "1":
        return 0
    d = load_payload()
    root = project_dir(d)
    commands = load_policy(d).get("verify", {}).get("commands", [])
    clean = subprocess.run("git diff --quiet && git diff --cached --quiet", shell=True, cwd=root).returncode == 0
    if not commands or clean:
        return 0
    for cmd in commands:
        r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            tail = "\n".join((r.stdout + r.stderr).splitlines()[-40:])
            print(f"STOP BLOQUÉ — `{cmd}` est rouge. Corriger avant de rendre la main :\n{tail}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
