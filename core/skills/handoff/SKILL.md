---
name: kata-handoff
description: Compacter la conversation en un document de reprise pour un autre agent ou une autre session. À lancer quand l'utilisateur dit « passe la main », « fais un handoff », « je reprends dans une autre session », « /kata-handoff », ou quand le contexte est trop chargé pour continuer ici.
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash(git status *) Bash(git log *) Bash(git diff *) Write
---

# Passer la main

Un handoff sert la reprise **immédiate** : un agent neuf lit un seul fichier et continue sans reposer les questions
déjà tranchées. Pour la connaissance durable (décision, piège, procédure), c'est `/kata-learn`. Les deux ne
se substituent pas : ne pas recopier ici ce qui doit vivre dans une doc.

## 1. Cadrer

Si l'utilisateur dit à quoi servira la prochaine session, adapter le document à cet usage. Sinon, supposer « continuer
le travail en cours » et l'écrire en tête.

## 2. Vérifier l'état réel

Ne pas résumer de mémoire. Lancer `git status` et `git log -5`, regarder la branche, le worktree, les tests ou
commandes lancés. Un handoff faux est pire que pas de handoff.

## 3. Écrire le document

Chemin par défaut : fichier temporaire **hors dépôt** (`$TMPDIR`, sinon `/tmp`), nom
`kata-handoff-<sujet>-AAAA-MM-JJ.md`. Dans `docs/` seulement si l'utilisateur le demande ; alors vérifier
`write.deny` et `write.no_code_on_main` de la politique. Donner le chemin à la fin.

Plan du document, dans cet ordre :

1. **Objectif** : le résultat attendu, en deux phrases, et pour qui.
2. **État** : fait, en cours, pas commencé. Branche, worktree, dernier commit, modifications non committées.
3. **Décisions et pourquoi** : chaque choix, l'alternative écartée, la raison. C'est la partie que l'agent suivant
   ne peut pas deviner.
4. **Fichiers clés** : chemins, une ligne chacun sur leur rôle ici.
5. **Prochaines étapes** : numérotées, la première immédiatement actionnable. Commande exacte quand elle existe.
6. **Pièges** : ce qui a échoué, les faux départs, les environnements fragiles.
7. **Non vérifié** : ce qui est supposé, pas prouvé. Séparer clairement du reste.
8. **Skills à appeler** : lesquelles des skills Kata l'agent suivant doit lancer (`/kata-execute`,
   `/kata-debug`, `/kata-verify`...) et pourquoi.

## Règles

- **Référencer, ne pas dupliquer** : spec, plan, ADR, issue, PR, diff, commit se citent par chemin, numéro ou
  hash. Ne pas les recopier.
- **Masquer les sensibles** : clés, mots de passe, jetons, URL privées, données personnelles ou client réelles.
  Écrire « voir le gestionnaire de mots de passe », jamais la valeur. Aucun nom de personne : un rôle.
- **Concis** : une page suffit presque toujours. Une phrase par idée, pas de récit chronologique.
- **Absolu** : dates en clair, jamais « hier » ni « tout à l'heure ».
- Rien n'est committé ni poussé.

## Fin

Annoncer le chemin du fichier et la phrase à donner au prochain agent : « Lis `<chemin>` puis continue à partir de
la première étape. » Si la session a aussi produit des apprentissages durables, proposer `/kata-learn` séparément.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kata.
