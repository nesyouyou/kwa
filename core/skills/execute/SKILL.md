---
name: kata-execute
description: Exécuter un plan d'implémentation écrit (docs/plans/…) dans la session courante, tâche par tâche. À utiliser quand un plan approuvé existe et que l'humain veut qu'on le déroule ici, ou quand il dit « exécute le plan », « go sur le plan », « on implémente ».
allowed-tools: Read Grep Glob Edit Write Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git branch *) Bash(pnpm *)
---

# Exécuter un plan

Le plan a déjà fait la réflexion. Ici on l'applique à l'identique, on prouve chaque étape par une commande dont
on a lu la sortie, et on s'arrête dès que le terrain ne correspond plus au plan.

## Loi de fer

```
UNE TÂCHE N'EST TERMINÉE QUE SI LES COMMANDES DE VÉRIFICATION ONT TOURNÉ DANS CETTE SESSION
ET QUE LEUR SORTIE A ÉTÉ LUE. « DEVRAIT PASSER » N'EST PAS UNE PREUVE.
```

Seconde loi : un blocage s'arrête et se remonte. Il ne se contourne jamais en silence.

## Préparation

1. **Lire le plan en entier, une fois, de façon critique.** Si une tâche est floue, contradictoire avec la spec
   ou référence un nom qui n'existe nulle part, le dire avant de commencer, pas au milieu.
2. **Lire la spec** citée dans l'en-tête. En cas de conflit, la spec l'emporte sur le plan.
3. **Vérifier la branche.** `git branch --show-current`. Sur `main` (ou une branche de `protected_branches`) :
   stop. Les modifications de code produit y sont refusées. Passer par `/kata-start-dev` : issue, branche,
   worktree. Ne pas contourner le garde-fou.
4. **Installer** selon `start.install` de `.claude/kata.policy.json` si l'environnement n'est pas prêt.
5. **Mesurer l'état de départ** : lancer les `verify.commands` avant de modifier quoi que ce soit. Un échec
   préexistant se signale à l'humain maintenant, sinon il sera mis sur ton compte.
6. **Créer la liste de tâches** à partir du plan (un suivi par tâche).
7. Pour un plan long, relire `git log` et les cases cochées du plan après toute interruption : le fichier du plan
   est la mémoire, pas la conversation.

Avant de démarrer : annoncer le plan, le nombre de tâches, les arrêts humains prévus. Pas de code avant
le « go » si l'humain n'a pas encore relu le plan.

## Boucle par tâche

1. **Annoncer** la tâche en une ligne. Relire son texte exact : ne pas se fier à un résumé mental.
2. **Dérouler les étapes dans l'ordre.** Test d'abord, vu en échec, puis le code minimal, puis vu en succès
   (`/kata-tdd`). Un test qui passe avant le code est une anomalie à traiter, pas une bonne nouvelle.
3. **Comparer chaque sortie à l'« Attendu »** du plan. Trois cas :
   - elle correspond : étape suivante ;
   - le code est faux : chercher la cause, pas le symptôme (`/kata-debug`) ;
   - le plan est faux ou incohérent avec le terrain : arrêt, voir « Blocage ».
4. **Vérifier la tâche** : les `verify.commands` de la politique, plus les tests nommés par la tâche. Lire la
   sortie. Avant de dire « terminé », appliquer `/kata-verify`.
5. **Cocher** les cases de la tâche dans le fichier du plan (`- [x]`), en citant en fin de ligne la commande de
   vérification et son résultat. Mettre à jour la liste de suivi.
6. **Arrêt humain** si la tâche est marquée « Arrêt humain : oui », ou si elle clôt un lot logique : résumer ce
   qui a changé (fichiers, résultat des commandes), proposer `/kata-commit` pour ce lot, et attendre. Sinon
   enchaîner.

Ne rien committer, ne rien pousser sans demande explicite. Proposer `/kata-commit` par lot logique, jamais un
commit par étape.

## Blocage : on s'arrête et on remonte

S'arrêter immédiatement, sans essayer une autre voie, quand :

- une dépendance, un fichier, une interface ou une commande du plan manque ou ne fonctionne pas ;
- une vérification échoue de façon répétée sans cause claire ;
- le plan contredit la spec, ou deux tâches se contredisent ;
- un garde-fou refuse une action (secret, chemin protégé, commande interdite, branche protégée) ;
- l'étape demande une action irréversible ou à effet externe : migration appliquée, suppression, push, publication,
  déploiement, appel à un service réel ;
- tu ne comprends pas une instruction du plan.

Le message de remontée contient : la tâche et l'étape, ce qui était attendu, ce qui s'est produit (sortie
exacte), ce que tu soupçonnes, et les options (corriger le plan, corriger la spec, lever le blocage). Puis tu
attends. Aucune modification supplémentaire n'est faite entre-temps, sauf pour remettre le dépôt dans un état sain.

Un garde-fou qui refuse n'est jamais un obstacle à contourner : ne pas le réécrire, ne pas passer par un autre
chemin. Demander à l'humain.

Écart mineur, localisé, qui sert la spec (un nom corrigé selon le « Produit » d'une tâche amont) : le faire,
l'écrire en note sous la tâche (`Écart : … — raison`) et le citer au rapport final. Tout écart structurel est un
blocage.

## Fin du plan

1. Relancer toutes les `verify.commands` sur l'ensemble. Citer commande et résultat.
2. Relire le diff contre la spec : chaque critère de réussite est-il démontré ? Un critère sans preuve se dit.
3. Rapport : tâches faites, écarts notés, points non traités, état de `git status`. Rien n'est committé ni poussé.
4. Proposer la suite : `/kata-review` avant de livrer, `/kata-commit` pour les lots restants, puis `/kata-ship`
   (PR, preuve, fusion gardée). Pour retenir ce qui a été appris : `/kata-learn`.

## Signaux d'alerte

| Pensée | Réalité |
|---|---|
| « Je me souviens de la tâche N » | Tu te souviens d'un résumé. Relis le texte. |
| « Le test est évident, je saute le rouge » | Un test jamais vu échouer ne prouve rien. |
| « Je lance toute la suite à la fin » | À la fin, on ne sait plus quelle étape a cassé. Vérifier à chaque tâche. |
| « Le plan se trompe, je fais au mieux » | Écart mineur : note. Écart structurel : arrêt et remontée. Jamais de décision secrète. |
| « Ça passera, c'était trivial » | « Ça passera » n'est pas une sortie de commande. |
| « Le garde-fou gêne, je contourne juste cette fois » | Le garde-fou demande l'humain. Lui demander. |
| « Je committe petit à petit pour sauvegarder » | Pas de commit sans demande. Un lot logique, via `/kata-commit`. |
| « Je coche d'avance, je vais finir » | Une case cochée sans vérification lue est un mensonge dans le plan. |
| « Je m'arrête à chaque tâche pour demander si je continue » | Les arrêts sont ceux du plan et des blocages. Le reste s'enchaîne. |

> Inspiré de superpowers (Jesse Vincent, MIT, v6.4.1) ; réécrit pour Kata.
