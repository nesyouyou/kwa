# Apprentissage continu et reprise de session

Statut : proposition, à approuver avant tout plan. Rien de ce qui suit n'est encore codé.

## But

Que chaque session de travail démarre en sachant ce qui s'est passé dans les dernières, et que chaque session laisse
le projet un peu mieux documenté que la précédente. Deux besoins distincts, un même mécanisme de capture :

- **Continuité** : où en est-on ? Ce qui a été fait, décidé, ce qui reste. Court, daté, propre à une session.
- **Connaissance** : qu'a-t-on appris qui vaut pour toutes les sessions suivantes ? Piège, décision, règle. Durable,
  rangé dans la documentation du projet, ses règles ou sa politique.

## Ce qui existe déjà

| Pièce | Rôle aujourd'hui | Limite |
|---|---|---|
| `kwa-memory capture / pending / digest / clear` | Notes rapides dans `.claude/kwa/local/inbox.md` | Il faut y penser : aucune capture automatique |
| `memory-context` (SessionStart) | Dit qu'il y a N notes en attente | Ne dit rien de ce qui s'est passé |
| `memory-nudge` (Stop) | Un rappel par session si 3 fichiers de code ou plus ont changé | Le seuil mesure du volume, pas de l'apprentissage ; rien si la session s'arrête brutalement |
| `/kwa-learn` | Trie, vérifie, propose, applique après accord | Part de ce qu'on lui donne : conversation et diff |
| `/kwa-handoff` | Document de reprise écrit à la demande pour un autre agent | Manuel : il faut le demander avant de partir |

Vérifié dans la documentation des hooks de Claude Code : `SessionStart` (sources `startup`, `resume`, `clear`,
`compact`, `fork`) peut injecter du contexte ; `UserPromptSubmit` reçoit le texte du message ; `PreCompact` précède la
compaction ; `Stop` peut bloquer la fin d'une réponse ; `SessionEnd` ne peut rien bloquer et dispose d'1,5 seconde au
total pour tous ses hooks.

## Ce que font les autres

Lu dans leur code et leurs fichiers de présentation, sans les avoir exécutés :

- **claude-reflect** (MIT) : un hook sur chaque message repère les corrections et les « remember: », les met en file
  avec un score ; `/reflect` fait valider avant d'écrire dans `CLAUDE.md`. Sauvegarde la file avant la compaction.
- **Claudeception** (MIT) : un texte injecté à chaque message demande au modèle d'évaluer s'il a appris quelque chose ;
  critères de qualité stricts ; écrit une skill sans relecture.
- **ECC continuous-learning-v2** (MIT) : hooks avant et après chaque appel d'outil, enregistrement tronqué avec
  masquage des secrets par motifs, agent d'analyse en arrière-plan, « instincts » à score de confiance.

À prendre : la file de candidats sans appel au modèle, la sauvegarde avant compaction, les critères de qualité.
À laisser : l'enregistrement de chaque appel d'outil, l'agent d'arrière-plan, les scores de confiance, la création de
skills sans relecture.

## Conception

Quatre pièces. Aucun hook n'appelle un modèle.

### A. Journal de sessions (continuité)

Une entrée par session, dans `.claude/kwa/local/journal/AAAA-MM-JJ-HHMMSS-<session>.md`. Local, non versionné, déjà
exclu de git par le dossier `local/`.

- **En-tête de faits**, écrit par un script : date, branche, worktree, base, commits de la session, fichiers touchés,
  issue ou PR si connus, état git à la fin (modifications non committées).
- **Corps de 8 lignes au plus**, rédigé par l'agent : Objectif · Fait · Décisions · Reste à faire · Pièges.
  Commande : `kwa-memory journal "<texte>"`.

Trois moments d'écriture, du meilleur au filet de sécurité :

1. **Fin de session substantielle** : le rappel `Stop` actuel demande aussi l'entrée de journal (une fois par session).
2. **Avant une compaction** (`PreCompact`) : écrit l'en-tête de faits et rappelle de rédiger le corps.
3. **Filet** (`SessionEnd`, rapide, sans récit) : si la session n'a aucune entrée, écrit l'en-tête de faits seul, marqué
   « automatique ». Une session fermée brutalement laisse donc au moins une trace vérifiable.

### B. Reprise au démarrage

`memory-context` injecte, à `startup`, `resume`, `clear` et `compact`, un bloc de **2 000 caractères au plus** :

- la dernière entrée **de la branche courante** (sinon la dernière entrée du projet) : objectif, fait, reste à faire ;
- une ligne de titre pour chacune des deux sessions précédentes ;
- l'état git actuel (branche, modifications non committées) ;
- le nombre de candidats d'apprentissage en attente.

Une entrée de plus de 14 jours est signalée comme ancienne, et une entrée dont la branche a été fusionnée comme
« branche fusionnée ». Au-delà du budget : renvoi vers `kwa-memory journal --last 5`. Un contexte court vaut mieux
qu'un contexte complet.

### C. Capture de signaux (connaissance)

- **`UserPromptSubmit`** : repère les marqueurs explicites (« retiens : », « remember: ») et les corrections
  (motifs français et anglais, message court) et les ajoute à `inbox.md` comme candidats. Texte de 300 caractères au
  plus, secrets masqués, aucun message long conservé.
- **Refus de garde** : chaque garde qui refuse ajoute une ligne à `local/signals.jsonl` (identifiant de la règle,
  commande tronquée et masquée). Un refus est l'erreur réelle que le projet voulait éviter : le signal le plus fiable,
  que les autres outils n'ont pas.
- **Rappel de fin de session** : déclenché par au moins un signal fort **ou** 3 fichiers de code, au lieu du seul
  volume.

### D. Traitement (`/kwa-learn`)

Le digest lit journal, inbox et signaux. Ajouts aux règles actuelles, qui ne changent pas (rien n'est écrit sans accord,
tout est vérifié contre le code) :

- **mettre à jour plutôt que créer** : chercher d'abord une entrée existante du même sujet ;
- **péremption** : dater, nommer la version, marquer l'obsolète ;
- **refus répétés** : trois refus de la même règle indiquent une consigne manquante, à proposer en règle ou en doc ;
- **nouvelle destination** : une procédure répétable devient une skill de projet, via `/kwa-agent-docs`.

## Confidentialité et garde-fous

- Journal et signaux sont locaux. Aucun appel d'outil n'est enregistré, seulement des faits git, des messages courts
  et des refus.
- Masquage des secrets avec le détecteur de `guard-secrets` avant toute écriture ; en cas de doute, ne pas écrire.
- Désactivables : `KWA_JOURNAL=0`, `KWA_MEMORY_NUDGE=0`.
- Conservation : 90 jours par défaut (`memory.journal_days`), `kwa-memory journal --prune` ; nettoyage des marqueurs
  `nudged-*` de plus de 30 jours.
- Les hooks sont des filets : une erreur interne ne bloque jamais la session.

## Hors périmètre

Instincts et scores de confiance, agent d'observation en arrière-plan, création de skills sans relecture, partage du
journal entre projets ou entre personnes.

## Tests prévus

- Entrée de journal : en-tête de faits exact sur un dépôt jetable ; corps limité à 8 lignes ; secret masqué.
- Filet `SessionEnd` : écrit sans récit, ne s'exécute pas si une entrée existe, tient dans 1,5 seconde.
- Reprise : budget de 2 000 caractères respecté ; préférence pour la branche courante ; entrée ancienne et branche
  fusionnée signalées ; silence si aucun journal.
- Signaux : « retiens : » et corrections captés, message long ignoré, refus de garde consigné, aucun secret conservé.
- Migration : rien ne change pour un projet sans journal ; `kwa doctor` signale les hooks non branchés.

## Décisions à trancher

1. **Local ou partagé** : journal local par défaut (proposé). Un journal partagé (`docs/journal/`, versionné) aiderait
   une équipe mais expose des récits de session ; à n'activer que sur demande (`memory.journal_dir`).
2. **Profondeur de la reprise** : dernière entrée complète plus deux titres (proposé), ou plus.
3. **Qui rédige le corps** : l'agent, sur invitation (proposé), avec le filet automatique pour les sessions fermées.
4. **Durée de conservation** : 90 jours (proposé).

## Plan par étapes

1. Journal et reprise (A et B) : la valeur immédiate, la plus petite surface.
2. Signaux (C) : corrections, « retiens : », refus de garde.
3. `/kwa-learn` enrichi (D) et critères de qualité.

Chaque étape : une PR, des tests, `kwa doctor` à jour. Idées reprises de claude-reflect et de Claudeception :
crédits à ajouter aux notices (MIT, comme pour `humanizer`), sans copie de texte.
