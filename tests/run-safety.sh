#!/usr/bin/env bash
# Suite hors-ligne : aucune écriture hors de répertoires temporaires, aucun réseau.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -p 'test_*.py' -v 2>&1 | tail -n 60
