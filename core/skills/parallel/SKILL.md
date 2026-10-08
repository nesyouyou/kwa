---
name: kwa-parallel
description: Lancer plusieurs sous-agents en même temps sur des problèmes indépendants. À utiliser quand 2 problèmes ou plus n'ont ni fichier ni état en commun (plusieurs suites de tests en échec pour des causes distinctes, plusieurs modules à auditer, plusieurs recherches), jamais pour des échecs liés ni pour du travail exploratoire.
---

# Agents en parallèle

Plusieurs problèmes indépendants traités l'un après l'autre gaspillent du temps. Chacun va à un agent, tous
démarrent ensemble, tu intègres ensuite. Cette skill est le mode « parallèle » ; l'exécution d'un plan par tâches
séquentielles est `/kwa-agents`.

## Quand l'utiliser

Les quatre conditions doivent être vraies :

1. **Domaines disjoints** : chaque problème touche des fichiers, un module ou une question que les autres ne touchent pas.
2. **Aucun état partagé** : pas de base commune modifiée, pas de port, pas de fichier généré, pas de cache de build,
   pas de lockfile, pas de migration.
3. **Causes distinctes** : corriger l'un ne peut pas corriger ou casser l'autre.
4. **Compréhension locale** : chaque problème se comprend sans connaître l'état global du système.

Exemples valides : trois fichiers de tests en échec pour des raisons sans rapport ; l'audit de trois paquets ; la
recherche de trois bibliothèques candidates ; des correctifs dans des modules séparés d'un monorepo.

## Quand NE PAS l'utiliser

- Les échecs sont liés : une cause commune se cherche d'abord, seul, avec `/kwa-debug`.
- Tu ne sais pas encore ce qui est cassé : explore d'abord, découpe ensuite.
- Deux agents devraient écrire dans le même fichier, le même schéma ou la même config.
- La tâche suivante a besoin du résultat de la précédente : c'est un enchaînement, pas du parallèle.
- Le travail est petit : le coût de rédaction des prompts dépasse le gain.
- Une migration ou un changement de schéma est en jeu : toujours en série.

## Procédure

1. **Découper.** Une ligne par domaine : problème, fichiers concernés, critère de fin. Si deux lignes partagent un
   fichier, fusionne-les ou sérialise-les.
2. **Choisir le mode d'écriture.**
   - Lecture seule (audit, recherche, diagnostic) : `Explore` ou `general-purpose`, aucune isolation requise.
   - Écriture sur des fichiers strictement disjoints : même worktree acceptable.
   - Écriture sur des zones voisines, ou doute sur un état partagé : `isolation: "worktree"` pour chaque agent.
     Tu récupères alors les changements de chaque worktree (voir intégration).
3. **Rédiger un prompt autonome par agent** à partir de `agent-prompt.md` (même dossier). L'agent ne voit pas la
   conversation : contexte, fichiers, erreurs exactes collées, contraintes, format de retour.
4. **Dispatcher tout en un seul message**, plusieurs appels à l'outil `Agent`, avec `run_in_background: true`,
   un `model` explicite et un `name` par agent. Un appel par message serait séquentiel.
5. **Pendant que ça tourne**, ne refais pas leur travail. Prépare l'intégration (commandes de vérification de
   `verify.commands`, grille de lecture des rapports). Les fins te sont notifiées ; ne scrute pas en boucle.

## Règles de fer

1. **Aucun agent ne committe ni ne pousse**, et toi non plus sans demande explicite. Jamais sur `main` : le travail
   se fait sur la branche de `/kwa-start-dev`.
2. **Les gardes (`.claude/kwa/hooks`) s'appliquent aux sous-agents.** Un refus se remonte dans le rapport, il ne se
   contourne pas, ni par l'agent ni par toi.
3. **Périmètre fermé.** Chaque prompt liste ce que l'agent peut modifier et ce qu'il ne doit jamais toucher.
4. **Un agent n'en lance pas d'autres.**
5. **Un rapport n'est pas une preuve.** Tu relances les vérifications toi-même.

## Intégration

1. **Lire chaque rapport en entier**, statut et doutes compris. Un agent qui a « tout corrigé » sans citer de
   commande est à renvoyer (`SendMessage` vers son `name`).
2. **Détecter les conflits** avant de fusionner quoi que ce soit :
   - `git status --short` et `git diff --stat` : deux agents ont-ils touché le même fichier ?
   - Fichiers hors périmètre modifiés : à annuler ou à justifier.
   - Changements de contrat (signature, type, config, dépendance) qui touchent un autre domaine.
   - Dépendances ajoutées ou lockfile modifié par plusieurs agents.
   Avec des worktrees isolés : `git diff <base>` dans chacun, appliquer l'un après l'autre
   (`git apply`), en s'arrêtant au premier conflit.
3. **Résoudre un conflit toi-même seulement s'il est trivial** (import dupliqué). Sinon, renvoyer à un agent
   le second changement avec le premier en contexte. L'hypothèse « indépendants » était fausse : le noter.
4. **Vérifier l'ensemble** : tous les `verify.commands` sur l'état intégré, pas agent par agent. Des correctifs
   individuellement verts peuvent casser ensemble.
5. **Contrôle par sondage** : relire le diff d'au moins un agent. Ils font des erreurs systématiques
   (test affaibli plutôt que bug corrigé, timeout allongé, mock qui masque le défaut).
6. Passer ensuite à `/kwa-review` sur l'ensemble si le changement est de taille, puis `/kwa-commit` à la demande.

## Rationalisations

| Excuse | Réalité |
|---|---|
| « Ils ont l'air indépendants, je ne vérifie pas les fichiers » | La vérification des fichiers communs prend une minute ; un conflit découvert à l'intégration en coûte dix. |
| « Un agent corrige tout, ce sera plus cohérent » | Un seul agent noyé dans trois domaines fait plus d'erreurs que trois agents ciblés. |
| « Je lance le deuxième après le premier, c'est pareil » | Un appel par message, c'est du séquentiel. Tout dans le même message. |
| « L'agent a augmenté le timeout, ça passe » | Un correctif qui masque le défaut n'en est pas un. Le prompt l'interdit, et tu le contrôles. |
| « Les tests de chaque agent sont verts, inutile de tout relancer » | L'intégration est le seul état qui compte. |

## Signaux d'alerte

Un prompt qui dit « corrige tout ». Deux agents sur le même fichier. Aucun `model` précisé. Des rapports acceptés
sans lecture. Pas de vérification sur l'état intégré. Un agent qui a commité.

> Inspiré de superpowers (Jesse Vincent, MIT, v6.4.1) ; réécrit pour Kwa.
