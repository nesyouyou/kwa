## Kwa — socle commun

Ce bloc est géré par Kwa (`kwa install`) : ne pas l'éditer ici, le modifier dans le pack.
Tout ce qui est propre au projet va **au-dessus ou en dessous** des marqueurs, ou dans `.claude/kwa.policy.json`.

- `AGENTS.md` est la source unique. `CLAUDE.md` n'est qu'un pointeur `@AGENTS.md`.
- Modules actifs : {{MODULES}}.
- Règles communes : `.claude/rules/kwa-*.md`. Garde-fous automatiques : `.claude/kwa/hooks/` ; ce sont des
  filets contre la bévue, pas une frontière de sécurité : ne jamais les contourner ni les éditer sans accord.
- Règles propres au projet (commandes interdites, chemins protégés, vérifications, environnements) :
  `.claude/kwa.policy.json`, propriété du projet.
- Skills : `/kwa-commit`, `/kwa-ship` ; selon les modules : méthode (`/kwa-brainstorm`, `/kwa-plan`, `/kwa-execute`,
  `/kwa-agents`, `/kwa-parallel`, `/kwa-tdd`, `/kwa-debug`, `/kwa-verify`, `/kwa-review`), circuit (`/kwa-start-dev`),
  livraison (`/kwa-deploy`, `/kwa-testflight`), mémoire (`/kwa-learn`). Un rappel de routage est injecté à chaque session.
{{KNOWLEDGE_LINE}}

### Façon de travailler

- **Langue : répondre en français.**
- **Réfléchir avant de coder** : énoncer les hypothèses ; si plusieurs interprétations existent, les présenter, ne
  pas trancher en silence ; oser contredire quand c'est justifié.
- **Simplicité d'abord** : le minimum de code qui résout le problème, rien de spéculatif, pas d'abstraction pour
  du code à usage unique.
- **Changements chirurgicaux** : ne toucher qu'au nécessaire, respecter le style existant, ne pas refactorer ce
  qui n'est pas cassé, ne nettoyer que les orphelins créés par ses propres changements.
- **Exécution guidée par l'objectif** : définir des critères de réussite vérifiables (tests) et boucler jusqu'à
  vérification. « Fait » veut dire vérifié : citer la commande lancée et son résultat.
- **Confidentialité** : jamais de nom de personne, d'hypothèse de financement ni de lien privé dans le code, les
  specs, les issues ou les PR. Du fonctionnel et du technique.

### Flux git de ce projet

{{PROFILE_RULES}}
