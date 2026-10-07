# Pièges connus

## Tester un garde par la ligne de commande est refusé par le garde lui-même (2026-10-07)

- **Symptôme** : une commande de test qui cite un motif interdit (par exemple une lecture d'un fichier `.env`)
  est refusée avant d'être exécutée, même quand le motif n'est qu'un argument d'`echo`.
- **Cause** : les gardes (`PreToolUse`) lisent le *texte* de la commande, pas son effet. Un test qui contient le
  motif est donc, pour eux, la commande dangereuse.
- **Correctif** : tester un garde avec un test unitaire qui lui envoie la charge utile JSON (voir `tests/helpers.py`),
  ou construire le motif à l'exécution dans un fichier de test. Ne pas le coller dans une commande interactive.
