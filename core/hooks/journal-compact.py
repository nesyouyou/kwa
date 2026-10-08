#!/usr/bin/env python3
"""PreCompact : sauvegarde les faits de la session dans le journal avant que la compaction n'efface le contexte.

Aucun récit : le corps d'une entrée déjà écrite est conservé. Silencieux, jamais bloquant. KWA_JOURNAL=0 le coupe.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kwa import load_payload, load_policy, project_dir  # noqa: E402


def main() -> int:
    d = load_payload()
    try:
        import _journal

        if _journal.enabled():
            root = project_dir(d)
            _journal.write_entry(root, _journal.start_session(root, d), load_policy(d))
    except Exception:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
