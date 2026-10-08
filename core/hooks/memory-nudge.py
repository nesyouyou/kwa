#!/usr/bin/env python3
"""Stop : une seule fois par session, si du travail substantiel a eu lieu, demande l'entrée de journal et invite à capitaliser.

Déclencheur : au moins `memory.min_files` (défaut 3) fichiers modifiés ou ajoutés hors documentation, ou au moins un
signal fort (correction, « retiens : », refus de garde) dans la session. Une seule invitation par session ; chaque
demande est omise si elle est déjà satisfaite (journal écrit, notes déjà captées pendant la session).
Désactivable : KWA_MEMORY_NUDGE=0. N'écrit rien dans la documentation.
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
    import _journal

    root = project_dir(d)
    policy = load_policy(d)
    local = _journal.local_dir(root)
    sid = _journal._sid(d)
    marker = os.path.join(local, f"nudged-{sid}")
    if os.path.exists(marker):
        return 0
    out = subprocess.run(["git", "-C", root, "status", "--porcelain", "-uall"], capture_output=True, text=True).stdout
    changed = [x[3:] for x in out.splitlines() if not x[3:].startswith(".claude/") and not x[3:].endswith(DOC_EXT)]
    use_journal = _journal.enabled()
    signals = _journal.session_signals(root, sid) if use_journal else 0
    if len(changed) < (policy.get("memory") or {}).get("min_files", 3) and not signals:
        return 0
    sess = _journal.start_session(root, d) if use_journal else None
    inbox = os.path.join(local, "inbox.md")
    want_journal = use_journal and not _journal.has_body(root, sess, policy)
    want_learn = not (os.path.exists(inbox) and sess and os.path.getmtime(inbox) >= sess["ts"])
    if not (want_journal or want_learn):
        return 0
    open(marker, "w").close()
    asks = []
    if want_journal:
        asks.append("écris l'entrée de journal de cette session, 8 lignes au plus (Objectif · Fait · Décisions · Reste à "
                    "faire · Pièges), avec `python3 .claude/kwa/bin/kwa-memory journal \"<texte>\"`")
    if want_learn:
        asks.append("y a-t-il un apprentissage durable (décision, piège, commande, règle à automatiser) ? Si oui, lance "
                    "/kwa-learn pour le proposer ; sinon réponds « rien à capitaliser »")
    print("Kwa mémoire : du travail substantiel a eu lieu dans cette session. Avant de conclure : " + ". Puis : ".join(asks)
          + ". (Une seule invitation par session.)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
