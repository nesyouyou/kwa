#!/usr/bin/env python3
"""Stop — une seule fois par session, si du travail substantiel a eu lieu : invite à capitaliser (/kwa-learn).

Déclencheur : au moins `memory.min_files` (défaut 3) fichiers modifiés ou ajoutés hors documentation, aucune note
captée pendant la session, pas déjà invité. Désactivable : KWA_MEMORY_NUDGE=0. N'écrit rien dans la documentation.
"""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kwa import load_payload, load_policy, project_dir  # noqa: E402

DOC_EXT = (".md", ".mdx", ".txt")


def main() -> int:
    if os.environ.get("KWA_MEMORY_NUDGE") == "0":
        return 0
    d = load_payload()
    if d.get("stop_hook_active"):
        return 0
    root = project_dir(d)
    local = os.path.join(root, ".claude", "kwa", "local")
    marker = os.path.join(local, f"nudged-{d.get('session_id', 'x')}")
    if os.path.exists(marker) or os.path.exists(os.path.join(local, "inbox.md")):
        return 0
    out = subprocess.run(["git", "-C", root, "status", "--porcelain", "-uall"], capture_output=True, text=True).stdout
    changed = [x[3:] for x in out.splitlines() if not x[3:].startswith(".claude/") and not x[3:].endswith(DOC_EXT)]
    if len(changed) < load_policy(d).get("memory", {}).get("min_files", 3):
        return 0
    os.makedirs(local, exist_ok=True)
    open(marker, "w").close()
    print("Kwa mémoire — du travail substantiel a eu lieu dans cette session. Avant de conclure : y a-t-il un "
          "apprentissage durable (décision, piège, commande, règle à automatiser) ? Si oui, lance /kwa-learn pour "
          "le proposer ; sinon réponds simplement « rien à capitaliser ». (Une seule invitation par session.)",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
