# Prompt d'agent parallèle

Un exemplaire par agent. Outil `Agent` : `subagent_type: "general-purpose"` (ou `Explore` pour de la lecture pure),
`model` explicite, `name` unique, `run_in_background: true`, `isolation: "worktree"` si les zones sont voisines.
Tous les appels dans le même message.

````
Tu traites UN problème précis, indépendant de ceux que d'autres agents traitent en même temps.

## Contexte
{{Le projet en deux phrases. Ce qui a changé récemment et qui explique le problème, si c'est utile.}}
Répertoire : {{chemin}} (branche {{branche}}).

## Problème
{{Symptôme exact. Coller les messages d'erreur, les noms de tests, les commandes pour reproduire.}}

## Périmètre
Tu peux modifier : {{fichiers ou dossiers}}
Tu ne dois PAS toucher : {{tout le reste ; en particulier fichiers partagés, config, lockfile, schéma, migrations}}
Si la cause se trouve hors de ton périmètre, ne la corrige pas : décris-la dans ton rapport.

## Objectif et critères de fin
{{Résultat vérifiable : ces tests passent, cette commande réussit, cette question a une réponse sourcée.}}
Vérification : {{verify.commands pertinentes + tests ciblés}}. Cite la sortie réelle.

## Méthode
- Comprends d'abord la cause racine ; ne traite pas le symptôme.
- Interdit de masquer : pas de timeout allongé, de test supprimé ou affaibli, de skip, de mock qui cache le défaut.
- Changement minimal, dans le style du code existant.
- Si le problème est en fait lié à autre chose (cause commune probable), arrête-toi et dis-le.

## Interdits
- Aucun `git commit`, `git push`, `git stash`, `git reset`, création ou changement de branche.
- Ne contourne jamais un garde-fou (hooks `.claude/kata/hooks`, refus de permission) : arrête-toi et remonte le
  message exact avec le statut BLOCKED.
- Ne lance pas d'autre agent. N'écris aucun secret dans le code ou les rapports.

## Format de retour
STATUT : DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
CAUSE : ce que tu as trouvé
CHANGEMENTS : fichiers modifiés, une ligne chacun
VÉRIFICATION : commandes lancées et résultats réels
HORS PÉRIMÈTRE : tout ce que tu as vu et pas touché (ou « rien »)
DOUTES : ce qui mérite un second regard (ou « aucun »)
````
