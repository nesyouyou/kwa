---
name: kata-review
description: Faire relire un diff ou une branche par un sous-agent relecteur. À utiliser avant de livrer (/kata-ship), à la fin d'un plan ou d'une fonctionnalité importante, après un correctif délicat, ou quand l'utilisateur dit « relis ça », « review », « regarde mon diff ».
---

# Demander une revue de code

La relecture est confiée à un agent neuf qui ne voit que le diff, la spec et les critères. Il n'hérite ni de ta
conversation ni de tes certitudes, et ton contexte reste libre. Relire toi-même le diff n'est pas une revue : tu en
connais déjà les raisons.

## Quand

- **Obligatoire** : avant `/kata-ship`, à la fin d'un plan exécuté avec `/kata-agents`, sur tout changement touchant
  l'authentification, l'argent, les migrations ou des données de clients.
- **Utile** : quand tu bloques, avant un refactor (état de référence), après un bug difficile.
- **Inutile** : une coquille ou un changement de texte sans effet sur le comportement.

## Procédure

1. **Fixer le périmètre par des références explicites.** Rien de flou comme « mes derniers changements ».
   ```bash
   BASE=$(git merge-base origin/main HEAD)     # ou le commit de départ
   HEAD_REF=$(git rev-parse HEAD)
   git diff --stat $BASE..$HEAD_REF
   ```
   Si le travail n'est pas committé (cas courant sous Kata, où l'on ne committe que sur demande), le périmètre est
   l'état du worktree : `git diff HEAD` plus les fichiers non suivis de `git status --short`. Le dire au relecteur.
   Ne committe pas pour pouvoir relire.
2. **Rassembler le contexte** : ce que le changement doit faire (issue, tâche du plan ou critères, citer et non
   résumer), ce qui est volontairement hors sujet, les doutes que tu as.
3. **Choisir le modèle** : `sonnet` pour un diff courant, `opus` pour un changement subtil ou risqué (concurrence,
   sécurité, données) et pour la relecture finale d'une branche entière. Toujours le préciser dans l'appel.
4. **Dispatcher** : outil `Agent`, `subagent_type: "general-purpose"` (il lui faut `git` et la lecture), avec le
   prompt de `reviewer-prompt.md` rempli. Un seul relecteur par passe. Au premier plan si tu attends son verdict.
5. **Classer et traiter** les retours (voir ci-dessous).
6. **Boucler** jusqu'au vert, avec les règles de sortie.

## Axes de relecture

Le prompt les impose au relecteur :

- **Correction** : le code fait ce que la spec demande ; cas limites ; erreurs gérées ; concurrence.
- **Sécurité** : secrets en dur ou journalisés, entrées non fiables (SQL, shell, chemins, HTML, désérialisation),
  autorisations, dépendances ajoutées.
- **Régressions** : appelants existants, contrats d'API, valeurs par défaut, migrations irréversibles.
- **Tests manquants** : comportement nouveau non couvert, test qui ne peut pas échouer, tests qui valident un mock.
- **Sur-ingénierie** (échelle de `/kata-simple`) : code mort, abstraction à usage unique, dépendance évitable,
  helper qui double un existant, option que personne ne règle, changement hors sujet. Un constat = un lieu, ce
  qu'on coupe, ce qui le remplace. Un test qui protège un comportement n'est pas du superflu.
- **Hygiène de remise** si le module `client-handover` est actif (le savoir par `.claude/kata.policy.json` ou les
  modules listés dans `AGENTS.md`) : secret, compte personnel, nom de personne, phrase périmable dans un fichier
  versionné ; voir `.claude/rules/kata-remise-au-client.md`. Ce n'est pas la même chose que la sécurité.

## Gravité et traitement

| Niveau | Contenu | Action |
|---|---|---|
| Critique | Bug, faille, perte de données, fonctionnalité cassée | Corriger tout de suite, avant toute autre chose |
| Important | Défaut de conception, test manquant, régression probable | Corriger avant de continuer ou de livrer |
| Mineur | Style, optimisation, polish ; sur-ingénierie sans risque | Noter ; corriger si c'est gratuit ; ne bloque pas |

Chaque retour reçu passe par `/kata-review-feedback` avant d'être appliqué : le relecteur peut se tromper. Un retour
faux se conteste avec la preuve (code, test), il ne s'applique pas par politesse.

## Boucle jusqu'au vert

1. Corriger les critiques et les importants (toi-même sur un petit changement, ou par un agent d'implémentation
   si le correctif est conséquent : l'orchestrateur ne fait pas le travail produit, voir `/kata-agents`).
2. Relancer `verify.commands` de `.claude/kata.policy.json` ; citer les résultats.
3. Nouvelle relecture **ciblée** : donner au relecteur la liste des retours précédents et le diff des seules
   corrections, lui demander si chaque point est réglé et si le correctif introduit un défaut.
4. Vert = zéro critique et zéro important ouverts, vérifications réussies.
5. Après trois tours sans converger, ou si deux relectures se contredisent : remonter à l'utilisateur avec les
   points ouverts. Ne pas tourner indéfiniment.

## Règles de fer

1. **Le relecteur est en lecture seule** : ni édition, ni commit, ni push, ni changement de branche ou d'index.
2. **Les gardes (`.claude/kata/hooks`) s'appliquent au relecteur.** Un refus se rapporte, il ne se contourne pas.
3. **Aucun commit ni push** pour faciliter la revue. Le commit vient de `/kata-commit` à la demande de l'utilisateur.
4. **Le relecteur ne lance pas d'autre agent.**
5. **Aucun critique ou important ne reste ouvert au moment de livrer.**

## Rationalisations

| Excuse | Réalité |
|---|---|
| « C'est simple, pas besoin de revue » | Les erreurs coûteuses se cachent dans les changements qu'on croit simples. |
| « Je relis mon diff moi-même » | Tu connais l'intention, donc tu lis l'intention. Un agent neuf lit le code. |
| « Il faut tout lui raconter la session » | Spec, diff, critères. L'histoire de la session biaise. |
| « C'est un important, mais ça passera en suivi » | Un important repoussé devient une régression en production. |
| « Le relecteur dit vert, donc je livre » | Relance les vérifications et lis les écarts écartés. |

## Suite

Retours à traiter : `/kata-review-feedback`. Revue verte : `/kata-verify`, puis `/kata-commit`, puis `/kata-ship`.

> Inspiré de ponytail (DietrichGebert, MIT, commit 552acd5) ; réécrit pour Kata.

> Inspiré de superpowers (Jesse Vincent, MIT, v6.4.1) ; réécrit pour Kata.
