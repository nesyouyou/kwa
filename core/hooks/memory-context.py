#!/usr/bin/env python3
"""SessionStart : reprise de session (dernière entrée du journal, état git, notes en attente).

Enregistre aussi la session (début et base git) pour que le journal puisse dire ce qu'elle a fait. Court et calibré :
2 000 caractères au plus ; silencieux s'il n'y a rien à dire. N'écrit rien dans la documentation. KWA_JOURNAL=0 coupe
le journal : il reste alors le simple rappel des notes en attente.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kwa import load_payload, load_policy, project_dir  # noqa: E402


def main() -> int:
    d = load_payload()
    root = project_dir(d)
    msg = ""
    try:
        import _journal

        if _journal.enabled():
            policy = load_policy(d)
            sess = _journal.start_session(root, d)
            _journal.housekeeping(root, policy)
            msg = _journal.render_resume(root, sess, policy)
        else:
            n = _journal.inbox_count(root)
            if n:
                msg = (f"Kwa mémoire : {n} note(s) d'apprentissage en attente (`python3 .claude/kwa/bin/kwa-memory pending`). "
                       "Proposer de les traiter avec /kwa-learn ; ne pas les appliquer sans l'accord de l'utilisateur.")
    except Exception:  # noqa: BLE001  un filet ne doit jamais empêcher une session de démarrer
        msg = ""
    if msg:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
