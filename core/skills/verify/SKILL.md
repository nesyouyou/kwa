---
name: kata-verify
description: Prouver qu'un travail est terminé avant de dire "fait", "corrigé", "ça passe", de committer, d'ouvrir une PR ou de passer à la tâche suivante. À utiliser dès qu'on s'apprête à affirmer un succès, y compris après une tâche déléguée à un sous-agent ("c'est bon ?", "vérifie", "/kata-verify").
---

# Vérifier avant de déclarer « fait »

« Fait » veut dire vérifié. Dire qu'un travail marche sans l'avoir prouvé, ce n'est pas être optimiste : c'est
affirmer une chose qu'on ignore. Cette skill est la dernière marche avant `/kata-commit`, `/kata-ship` et `/kata-deploy`.

## La loi

```
AUCUNE AFFIRMATION DE SUCCÈS SANS LA SORTIE D'UNE COMMANDE FRAÎCHE QUI LA PROUVE.
```

Fraîche : lancée après la dernière modification, dans ce tour de travail. Une exécution d'avant ton dernier changement, celle d'un autre agent, ou « ça passait tout à l'heure » ne comptent pas.

## Le portillon

Avant toute phrase qui dit ou laisse entendre un succès :

1. **Identifier** la commande qui prouve l'affirmation.
2. **La lancer en entier**, pas une version partielle.
3. **Lire toute la sortie** : code de retour, nombre d'échecs, avertissements, tests sautés.
4. **Comparer** : la sortie confirme-t-elle l'affirmation ?
5. Seulement alors, **affirmer, avec la preuve**. Sinon, dire l'état réel.

Sauter une étape, c'est affirmer sans savoir.

## D'où viennent les commandes

Ne rien coder en dur. Lire `.claude/kata.policy.json` :

- `verify.commands` : la liste de vérification du projet (types, lint, tests, build…). Les lancer **toutes**, dans l'ordre, telles quelles.
- Les **tests ciblés** du changement : le test écrit avec `/kata-tdd`, et les tests voisins du code touché, via la commande de test de la stack détectée.
- Les parcours touchés si l'interface a changé (plus bas).

`verify.commands` vide ou absent : le dire, déduire les commandes du `package.json` (ou équivalent), les annoncer
à l'utilisateur, et proposer de les inscrire dans la politique. Une commande qui ne s'exécute pas ici (outil absent,
service injoignable) est une vérification **non faite** : l'écrire comme telle.

## Ce qui prouve quoi

| Affirmation | Preuve requise | Ne suffit pas |
|---|---|---|
| Les tests passent | Sortie de la commande de test : 0 échec | Un run précédent, « ça devrait passer » |
| Le typage / lint est propre | Sortie de la commande : 0 erreur | Un test vert |
| Le build réussit | La commande de build, code 0 | Le lint, ou « les logs ont l'air bons » |
| Le bug est corrigé | Le test de non-régression passe ; **et** rouge si on retire le correctif | Le code a changé, donc c'est réglé |
| Le test de non-régression est valide | Cycle rouge-vert constaté (`/kata-tdd`) | Il passe une fois |
| La fonctionnalité répond au besoin | Relecture des critères de l'issue, un par un | Les tests passent |
| Un sous-agent a terminé | `git diff` et relancer les vérifications soi-même | Son rapport dit « succès » |
| Le déploiement est en ligne | Révision servie constatée (`/kata-deploy`) | Le workflow est vert |

## Effet visible : capture quand il y a une interface

Quand le changement touche une interface (web ou mobile), les tests ne suffisent pas : **regarder le résultat**.

1. Lancer l'application avec la commande du projet, ouvrir le parcours touché.
2. Prendre une capture de l'état attendu, et des états limites utiles (vide, erreur, petit écran).
3. Comparer à ce qui est demandé ; la joindre au compte rendu et à la PR (captures avant/après, `/kata-ship`).

Une capture qu'on n'a pas regardée ne compte pas. Impossible de lancer l'interface ici : le dire, ne pas le déduire.

## Tests sautés et instables

- Un test sauté (`skip`, `todo`, `xit`) ou ignoré n'est **pas** un test vert. Le nommer dans le compte rendu.
- Un test qui échoue par intermittence est un échec non expliqué, pas du bruit : un seul passage vert ne le
  réhabilite pas. Le relancer plusieurs fois, chercher la cause avec `/kata-debug` (souvent un délai fixe : attentes conditionnelles).
- Ne jamais désactiver, supprimer ou assouplir un test pour obtenir du vert, sauf accord explicite de l'utilisateur.
- Un échec présent avant ton changement reste un échec : le signaler par son nom, ne pas le passer sous silence.

## Rendre compte

Chaque affirmation de succès porte sa commande et son résultat, concrètement :

```
pnpm typecheck : 0 erreur
pnpm test src/orders : 34 passés, 0 échoué, 0 sauté
Capture : écran « commande vide », petit écran (jointe)
Non vérifié : parcours de paiement (service tiers injoignable ici)
```

Pas de formule sans chiffre (« tout est vert »). Toujours un bloc « non vérifié » honnête, même vide : « rien ».

## Excuses courantes

| Excuse | Réalité |
|---|---|
| « Ça devrait marcher maintenant » | Lance la vérification. |
| « Je suis confiant » | La confiance n'est pas une preuve. |
| « Le lint passe » | Le lint ne compile pas. |
| « Le sous-agent dit que c'est bon » | Vérifier le diff et relancer soi-même. |
| « Une vérification partielle suffit » | Le partiel ne prouve rien du reste. |
| « Juste cette fois » | Aucune exception. |
| « Je suis fatigué, je finis » | La fatigue ne remplace pas la preuve. |
| « Une autre formulation, donc la règle ne s'applique pas » | L'esprit prime sur la lettre. |

## Signaux d'alerte : stop, on lance la commande

Les mots « devrait », « probablement », « a l'air de », « c'est bon », « parfait », « terminé » écrits avant d'avoir
une sortie. Un enthousiasme avant la vérification. Une envie de committer, pousser ou ouvrir la PR sans avoir relancé.
Se fier à une exécution ancienne ou à un rapport d'agent. Une vérification partielle présentée comme complète.

## Quand l'appliquer

Avant tout compte rendu de réussite, toute expression de satisfaction, tout passage à la tâche suivante,
toute délégation conclue. Avant `/kata-commit`, `/kata-ship`, `/kata-deploy`. La règle vaut aussi pour les
paraphrases et les sous-entendus de réussite. Les commits et poussées restent soumis à la demande explicite de l'utilisateur, et jamais sur `main`.

> Inspiré de superpowers (Jesse Vincent, MIT, v6.4.1) ; réécrit pour Kata.
