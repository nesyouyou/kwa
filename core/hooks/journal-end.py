#!/usr/bin/env python3
"""SessionEnd : filet de sécurité. Rafraîchit les faits du journal, ou écrit une entrée « automatique » si la session
a laissé une trace (commit, fichier touché, signal) sans avoir été racontée.

SessionEnd ne peut rien bloquer et dispose d'1,5 s pour tous ses hooks : seulement des faits git, aucun récit, une
échéance interne d'une seconde. KWA_JOURNAL=0 le coupe.
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kwa import load_payload, load_policy, project_dir  # noqa: E402


def main() -> int:
    d = load_payload()
    try:
        import _journal

        if not _journal.enabled():
            return 0
        _journal._DEADLINE[0] = time.time() + 1.0
        root = project_dir(d)
        policy = load_policy(d)
        # sans enregistrement de début, la base git est inconnue : mieux vaut ne rien écrire que de se tromper
        if not os.path.exists(os.path.join(_journal.sessions_dir(root), f"{_journal._sid(d)}.json")):
            return 0
        sess = _journal.start_session(root, d)
        f = _journal.facts(sess)
        existing = os.path.exists(_journal.entry_path(_journal.journal_dir(root, policy), sess))
        if existing or f["commits"] or f["files"] or _journal.session_signals(root, sess["id"]):
            _journal.write_entry(root, sess, policy, f=f)
    except Exception:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
