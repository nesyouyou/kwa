---
name: kwa-agents
description: Exécuter un plan docs/plans/*.md dont les tâches sont assez indépendantes, en déléguant chaque tâche à un sous-agent frais. À utiliser quand un plan validé existe et que l'utilisateur dit « exécute le plan », « lance les agents », « on délègue » ; pas pour une tâche unique ni un plan fortement couplé (voir /kwa-execute).
---

# Développement piloté par sous-agents

Tu es l'orchestrateur. Tu découpes, tu dispatches, tu contrôles, tu intègres. Tu n'écris pas le code produit toi-même.
Chaque tâche du plan va à un agent frais, qui ne voit rien de ta conversation. Deux relectures successives valident
le résultat : conformité à la spec, puis qualité. Le plan vient de `/kwa-plan` ; le cadrage de `/kwa-brainstorm`.

## Prérequis

- Un plan `docs/plans/*.md` relu, avec pour chaque tâche : fichiers, étapes, critères d'acceptation vérifiables.
  Sinon, retourner à `/kwa-plan`. Ne jamais improviser un plan en route.
- Le circuit de `/kwa-start-dev` est en place : issue, branche dédiée `<type>/<n°>-<slug>`, worktree. Jamais sur
  `main`. Si tu es sur `main`, t'arrêter et lancer `/kwa-start-dev`.
- Les commandes de vérification sont celles de `verify.commands` dans `.claude/kwa.policy.json`. Les lire une fois,
  les recopier dans chaque prompt d'agent. Ne jamais en inventer.

## Règles de fer

1. **Aucun agent ne committe ni ne pousse.** Toi non plus, sans demande explicite de l'utilisateur. Le travail reste
   en modifications locales dans le worktree. Le commit se fait ensuite avec `/kwa-commit`, la livraison avec `/kwa-ship`.
2. **Les gardes (`.claude/kwa/hooks`) s'appliquent aux sous-agents.** Un refus de garde n'est pas un obstacle à
   contourner : l'agent s'arrête et remonte le refus. Tu ne le contournes pas à sa place.
3. **Tu ne fais pas le travail produit.** Pas de « petite retouche rapide » : elle va à un agent. Tu peux lire,
   lancer les vérifications, mettre à jour le suivi.
4. **Un agent frais par tâche.** Jamais deux tâches dans le même agent, sauf lot de micro-éditions identiques.
5. **« Fait » exige une preuve.** Commande lancée, sortie citée. Un rapport d'agent n'est pas une preuve : relance
   toi-même `verify.commands` avant de clore une tâche.

## Mécanique Claude Code

- Dispatch : outil `Agent`, avec `subagent_type: "general-purpose"` pour implémenter et relire (il faut Read, Edit,
  Bash). `Explore` ou `Plan` servent à cartographier, jamais à écrire.
- Toujours renseigner `model` (`haiku`, `sonnet`, `opus`). Omis, l'agent hérite de ton modèle et la règle de coût saute.
- `name` donne un nom à l'agent, ce qui permet de le reprendre avec `SendMessage` (contexte conservé). Un agent
  repris garde son historique : utile pour corriger, nocif pour une relecture neuve.
- `run_in_background: true` pour les tâches indépendantes lancées ensemble ; leur fin te notifie. Ne pas attendre
  en boucle. Une tâche dont la suivante dépend s'exécute au premier plan.
- `isolation: "worktree"` donne un worktree jetable à l'agent. À réserver aux tâches parallèles qui touchent des
  zones voisines (voir /kwa-parallel). Séquentiellement, tous les agents travaillent dans le worktree de la branche.
- Un agent ne doit pas lancer d'agents : le dire dans le prompt.

## Choix du modèle

Le moins puissant qui réussit, mais pas en dessous du milieu de gamme quand la tâche est décrite en prose.

| Tâche | Modèle |
|---|---|
| Code complet fourni dans le plan, 1 à 2 fichiers, mécanique | `haiku` |
| Plusieurs fichiers, intégration, adaptation au code existant | `sonnet` |
| Conception, concurrence, sécurité, point où les tests ne suffisent pas | `opus` |
| Relecture de conformité | `sonnet` |
| Relecture de qualité | `sonnet` ; `opus` si le diff est subtil ou risqué |
| Relecture finale de toute la branche | `opus` |

Un modèle trop faible multiplie les tours et coûte plus cher. En cas d'échec, monter d'un cran avant de rédiger autrement.

## Boucle par tâche

Avant la première tâche : `git status` propre dans le worktree, lecture du plan, une phrase de doute par ambiguïté
repérée. Une ambiguïté bloquante se tranche avec l'utilisateur, pas dans le dos du plan.

1. **Instantané.** Avant de dispatcher, sauvegarder l'état de départ de la tâche dans le répertoire temporaire de
   la session : `git diff HEAD > <tmp>/avant-N.patch` et `git status --short > <tmp>/avant-N.status`. Il délimite ce
   que la tâche a changé, puisque rien n'est committé.
2. **Implémenter.** Remplir `implementer-prompt.md` (même dossier) avec le texte intégral de la tâche, le contexte
   des tâches précédentes (interfaces, décisions, pas leur historique), les `verify.commands`. Dispatcher.
3. **Traiter le statut.** Voir ci-dessous.
4. **Relecture de conformité** (`spec-reviewer-prompt.md`) : le code fait-il exactement ce que la tâche demande,
   ni plus ni moins ? Elle passe avant la qualité : il est inutile de polir du code qui ne répond pas à la demande.
5. **Relecture de qualité** (`quality-reviewer-prompt.md`), seulement quand la conformité est verte.
6. **Corriger.** Les retours critiques et importants repartent vers l'implémenteur (`SendMessage`), puis nouvelle
   relecture ciblée sur les seuls points corrigés. Au troisième aller-retour sans progrès : agent neuf, un cran
   au-dessus ; au cinquième : remonter à l'utilisateur avec les points ouverts.
7. **Vérifier toi-même** les `verify.commands`, cocher la tâche dans le plan, passer à la suivante.

Les relecteurs sont toujours des agents neufs, jamais l'implémenteur, et lisent le code réel, pas son rapport.

## Statuts d'un implémenteur

| Statut | Signification | Ta réaction |
|---|---|---|
| `DONE` | Terminé, vérifié, critères remplis | Passer à la conformité |
| `DONE_WITH_CONCERNS` | Terminé mais doute (taille, hypothèse, dette) | Lire les doutes ; si ce sont des risques de correction, trancher avant la relecture ; si ce sont des remarques, les transmettre aux relecteurs |
| `NEEDS_CONTEXT` | Une information manque | La fournir (ou la chercher), reprendre le même agent avec `SendMessage` |
| `BLOCKED` | Impossible en l'état | Diagnostiquer : contexte insuffisant, tâche trop grosse (la découper), modèle trop faible (monter), plan faux (remonter à l'utilisateur). Jamais relancer à l'identique |

Un refus de garde est toujours `BLOCKED`. Un agent qui dit « fait » sans citer de commande ni de sortie : le renvoyer.

## Fin de plan

Relecture de toute la branche avec `/kwa-review` (base `main`, tête = état du worktree), sur le modèle le plus fort.
Puis `/kwa-verify` sur l'ensemble. Ne proposer `/kwa-commit` puis `/kwa-ship` qu'une fois les deux verts. Si des
retours arrivent plus tard d'une PR, `/kwa-review-feedback`.

## Rationalisations

| Excuse | Réalité |
|---|---|
| « C'est trois lignes, je le fais moi-même » | Ton contexte sert à coordonner. Trois lignes de plus aujourd'hui, un orchestrateur saturé demain. |
| « L'agent dit que tout passe » | Un rapport n'est pas une exécution. Relance les vérifications. |
| « La conformité est bonne, je saute la qualité » | Les deux axes attrapent des défauts différents. Les deux, dans l'ordre. |
| « Je lui laisse committer, ce sera plus propre » | Interdit. Le commit est une décision de l'utilisateur. |
| « La garde bloque, je lui dis de passer par un autre chemin » | Un refus se remonte. Le contourner annule la garde. |
| « Deux tâches proches, un seul agent » | Contexte pollué, relecture floue. Un agent par tâche. |

## Signaux d'alerte

Dispatcher sans modèle explicite. Coller la conversation dans un prompt. Lancer deux agents qui écrivent dans les
mêmes fichiers. Passer à la tâche suivante avec un retour critique ouvert. Dire « terminé » sans avoir relancé les
vérifications. Éditer le code toi-même pour « gagner du temps ».

> Inspiré de superpowers (Jesse Vincent, MIT, v6.4.1) ; réécrit pour Kwa.
