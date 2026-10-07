---
name: kata-debug
description: Diagnostiquer un bug, un test qui échoue, un build cassé, un comportement inattendu, un test instable ou un problème de performance, avant de proposer le moindre correctif. À utiliser dès qu'un symptôme apparaît, surtout sous pression ou après un premier essai raté ("ça plante", "pourquoi", "ça ne marche plus", "/kata-debug").
---

# Débogage systématique

Deviner coûte plus cher que comprendre : un correctif posé sans cause connue masque le symptôme, déplace le bug
et en crée un autre. Cette skill vaut pour tout symptôme technique, y compris le « petit » et l'urgent.
Elle s'enchaîne avec `/kata-tdd` (test de non-régression), `/kata-verify` (preuve) et `/kata-start-dev` (issue, branche).

## La loi

```
AUCUNE CORRECTION SANS CAUSE RACINE ÉTABLIE.
```

Tant que la phase 1 n'est pas finie, tu n'as pas le droit de proposer un correctif, pas même « juste pour voir ».
Cela vaut surtout quand c'est urgent, évident, ou quand un premier essai a déjà échoué.

## Phase 1 : reproduire et comprendre

1. **Lire le message d'erreur en entier.** Trace complète, fichier, ligne, code. La réponse y est souvent.
2. **Reproduire de façon fiable.** Étapes exactes, à chaque fois ? Sinon, collecter des données, ne pas supposer.
3. **Regarder ce qui a changé** : `git diff`, `git log`, dépendances, configuration, environnement.
4. **Collecter des preuves à chaque frontière** si le système a plusieurs composants (voir plus bas).
5. **Remonter la chaîne causale** : d'où vient la mauvaise valeur, qui l'a passée, et ainsi de suite jusqu'à la source. Voir `remonter-la-cause.md`. On corrige à la source, jamais là où ça casse.

## Phase 2 : comparer

- Trouver dans le même dépôt un code semblable qui marche. Lister **toutes** les différences avec le cas cassé, même minuscules.
- Si on suit un modèle ou une documentation, la lire en entier, pas en diagonale.
- Dépendances, configuration, hypothèses : qu'est-ce que ce code suppose et qui n'est plus vrai ?

## Phase 3 : une hypothèse, un test

1. Énoncer une hypothèse unique, écrite : « la cause est X parce que Y ».
2. La tester par le plus petit changement possible, une variable à la fois.
3. Confirmée : phase 4. Infirmée : nouvelle hypothèse. **Ne pas empiler** un second changement sur le premier.
4. Quand tu ne sais pas, dis « je ne comprends pas X » à l'utilisateur. Faire semblant coûte plus cher.

## Phase 4 : corriger

1. **Test de non-régression d'abord** (`/kata-tdd`) : il reproduit le bug, on le voit échouer pour la bonne raison.
2. **Un seul correctif**, sur la cause racine. Pas de « tant que j'y suis », pas de refactor groupé.
3. **Vérifier** : le test passe, le reste de la suite aussi, le symptôme d'origine a disparu (`/kata-verify`).
4. **Ajouter des garde-fous** si la valeur invalide pouvait passer ailleurs : `defense-en-profondeur.md`.

## Bug difficile, flaky ou lenteur : la boucle d'abord

Quand la reproduction est incertaine, construire avant tout une **boucle de retour** : une commande unique, rapide,
déterministe, qui échoue pour **ce** symptôme et pas pour un voisin. Sans elle, ne pas émettre d'hypothèse.
- **Preuve par mutation** : retirer le correctif (ou le défaire) ; le symptôme doit revenir. Sinon le correctif n'agit pas.
- **Performance** : mesurer avant, mesurer après, avec le même protocole ; un gain non mesuré est une impression.
- Bug intermittent : viser un taux de reproduction élevé (rejouer 100 fois) plutôt qu'une repro propre.
Détail et variantes : `boucle-de-diagnostic.md`.

## Règle des 3 échecs

Compter les correctifs tentés. Après deux échecs, retourner en phase 1 avec ce qu'on a appris.
**Au troisième échec, arrêter de corriger et remettre l'architecture en question.** Signes :

- chaque correctif révèle un autre couplage ou un état partagé ailleurs ;
- chaque correctif exige une grosse refonte ;
- chaque correctif crée un nouveau symptôme à côté.

Ce n'est plus une hypothèse fausse, c'est un modèle faux. Exposer à l'utilisateur ce qu'on a établi, les options
(refonte ciblée, contournement assumé, abandon), et attendre sa décision avant le correctif suivant.

## Systèmes multi-composants : la boucle de preuves

Pour un enchaînement mobile, API, worker, base, ou CI, build, déploiement : **avant tout correctif, instrumenter** chaque frontière.

```
Pour chaque frontière :
  - noter ce qui entre, ce qui sort
  - vérifier que l'environnement et la configuration se propagent
  - relever l'état à chaque couche
Un seul passage donne l'endroit exact de la rupture ; seulement ensuite, creuser ce composant.
```

Exemples de ce qu'on relève : charge utile envoyée par le mobile et reçue par l'API ; job posé dans la file puis
repris par le worker ; requête SQL réellement émise et lignes réellement lues ; variable d'environnement présente
dans le worker mais pas dans l'API. Les commandes d'observation viennent du projet (journaux, scripts du `package.json`,
`.claude/kata.policy.json`) : ne rien deviner. En recette ou production : lecture seule, jamais d'écriture pour « tester » ; un déploiement relève de `/kata-deploy`.

Retirer l'instrumentation temporaire une fois la cause trouvée.

## Attentes conditionnelles, pas de `sleep`

Un test qui attend « 50 ms, ça devrait suffire » passe sur ta machine et échoue en CI. Attendre la **condition**
réellement visée : un état, un événement, un élément affiché, un enregistrement présent. Avec un délai maximal et un
message d'échec clair. Détail et schémas : `attentes-conditionnelles.md`.
Un délai fixe n'est légitime que pour tester un comportement temporel (anti-rebond, intervalle) : le commenter.

## Excuses courantes

| Excuse | Réalité |
|---|---|
| « C'est simple, pas besoin de méthode » | Les bugs simples ont une cause aussi. La méthode est rapide quand c'est simple. |
| « C'est urgent » | Procéder au hasard est plus lent que comprendre. |
| « J'essaie ça d'abord, j'enquête après » | Le premier essai fixe la direction. Commencer par la cause. |
| « Je regroupe plusieurs correctifs » | Tu ne sauras pas lequel a servi, et tu en casseras un autre. |
| « Je vois le problème, je corrige » | Voir un symptôme n'est pas connaître la cause. |
| « Je teste le correctif à la main » | Un correctif sans test régresse. Test d'abord. |
| « Encore un essai » (après deux échecs) | Trois échecs signalent un problème d'architecture. On en parle. |
| « Ça marche chez moi » | Chercher ce qui diffère : environnement, données, version. |

## Signaux d'alerte : retour en phase 1

« Correctif rapide, je creuse plus tard. » « Je change X et je regarde. » Plusieurs modifications avant de relancer.
« C'est sûrement X. » Un correctif proposé avant d'avoir suivi la donnée. Un correctif qui révèle un nouveau
problème ailleurs. Un `sleep` ajouté pour « stabiliser ». Un `try/catch` qui avale l'erreur. Une valeur par défaut
qui cache l'absence d'une donnée. Si l'utilisateur dit « arrête de deviner » ou « tu l'as vérifié ? », tu as sauté une phase.

## Quand il n'y a pas de cause racine

Si l'enquête complète conclut à un cas environnemental, temporel ou externe : le dire, documenter ce qui a été
établi, ajouter une gestion adaptée (nouvel essai, délai maximal, message d'erreur explicite) et de la surveillance.
Mais 95 % des « causes inconnues » sont une enquête incomplète. Une leçon durable se range avec `/kata-learn`.

Ne jamais committer ni pousser sans demande explicite (`/kata-commit`, `/kata-ship`) ; jamais de correctif sur `main`.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kata.

> Inspiré de superpowers (Jesse Vincent, MIT, v6.4.1) ; réécrit pour Kata.
