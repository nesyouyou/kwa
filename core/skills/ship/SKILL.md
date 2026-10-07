---
name: kata-ship
description: Publier la branche de travail et ouvrir la PR, après confirmation. À lancer seulement quand l'utilisateur demande de pousser ou d'ouvrir une PR ("on pousse", "ouvre la PR", "/kata-ship").
disable-model-invocation: true
---

# kata-ship

Publie la branche courante et ouvre (ou met à jour) la PR. **Ne fusionne jamais.**

1. Vérifier : branche ≠ `main`/`master`, `git status` propre (sinon proposer `/kata-commit` d'abord).
2. Lancer les vérifications du projet (typecheck, lint, tests : voir `AGENTS.md`) et citer le résultat.
   Un échec bloque la suite : le dire, ne pas pousser.
3. Résumer à l'utilisateur ce qui sera publié (`git log origin/main..HEAD --oneline`, fichiers touchés) et
   **demander confirmation** du push.
4. Après accord : `git push -u origin <branche>`. Jamais de force.
5. `gh pr create` avec un titre au format `.claude/rules/kata-writing-standard.md` et un corps
   Contexte / Changements / Vérification / Risque-déploiement. Si l'interface change : captures avant/après.
   Si `/kata-humanize` est installée, passer le titre et le corps par elle en mode intégré avant `gh pr create`
   (même format, sans faits ajoutés).
6. Donner le lien de la PR. Rappeler que la fusion est une décision séparée, et dire si elle déclenche un
   déploiement de production.

> Inspiré de super-board (Eric Tech, MIT, commit 120bc1d) ; réécrit pour Kata.
