---
name: kata-commit
description: Committer le travail en cours par changement logique, sans jamais pousser. À lancer seulement quand l'utilisateur demande de committer ("on commit", "/kata-commit").
disable-model-invocation: true
---

# kata-commit

Committe les modifications en cours, un commit par changement logique. **Ne pousse jamais.**

1. `git status` et `git diff` : lire ce qui change. Si la branche courante est `main` ou `master`, **s'arrêter** :
   proposer un nom de branche `<type>/<slug>` et la créer après accord.
2. Regrouper les fichiers en changements logiques (code + test lié ensemble ; refonte et correctif séparés).
   Si un fichier mélange deux sujets, le dire et proposer de scinder avec `git add -p`.
3. Écarter ce qui ne doit pas être committé : secrets, `.env`, artefacts de build, fichiers générés non suivis par
   convention du projet (en cas de doute, demander).
4. Pour chaque groupe : `git add <fichiers précis>` (jamais `git add -A`), puis un message au format de
   `.claude/rules/kata-writing-standard.md`. Ne pas utiliser `--no-verify`.
5. Si un hook de pré-commit échoue : corriger la cause, recréer un **nouveau** commit, ne pas amender sauf demande.
6. Terminer par `git log --oneline` des commits créés et l'état de `git status`. Dire que rien n'est poussé.

> Inspiré de super-board (Eric Tech, MIT, commit 120bc1d) ; réécrit pour Kata.
