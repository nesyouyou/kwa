---
name: kwa-learn
description: Capitaliser ce que la session a appris — décisions, pièges, commandes, règles à automatiser — en le rangeant au bon endroit (docs du projet, garde-fous, mémoire de l'agent, base de connaissance de l'équipe) après accord de l'utilisateur. À lancer en fin de session substantielle, quand un piège a coûté du temps, ou quand l'invitation Kwa mémoire le propose ("/kwa-learn", "capitalise", "qu'est-ce qu'on retient ?").
allowed-tools: Bash(python3 .claude/kwa/bin/kwa-memory *) Bash(git *) Read Grep Glob
---

# Capitaliser une session

Objectif : que la prochaine session (la tienne, celle d'un autre agent, celle d'un collègue) démarre avec ce que
celle-ci a coûté à apprendre. **Rien n'est écrit sans l'accord de l'utilisateur, rien n'est committé.**
« Rien à capitaliser » est une réponse valable et fréquente : ne pas fabriquer d'apprentissages.

## 1. Rassembler

```bash
python3 .claude/kwa/bin/kwa-memory digest
```

Relire aussi la conversation et le diff. Une note déjà captée (`kwa-memory capture …`) est un candidat de plus.

## 2. Filtrer — ne garder que le non-dérivable

Garder seulement ce qu'on ne retrouve **ni dans le code, ni dans `git log`, ni dans la doc existante** :

- une décision et son *pourquoi* (alternatives écartées, contrainte cachée) ;
- un piège : symptôme, cause réelle, correctif, comment le reconnaître ;
- une commande ou une procédure qui n'était écrite nulle part ;
- une erreur qui peut se reproduire et qu'un garde-fou empêcherait.

Écarter : ce que le diff dit déjà, un récit de session, une hypothèse non vérifiée. **Vérifier** chaque affirmation
contre le code actuel (le fichier, la fonction, la commande existent-ils encore ?). Dates en absolu (jamais « hier »).
Pas de nom de personne (un rôle), pas de secret, pas de donnée client réelle.

### Rétrospective de travail

Se demander aussi, au-delà de ce qu'on retient : **qu'est-ce qui a fait perdre du temps dans la façon de travailler
avec l'agent ?** Une consigne absente ou ambiguë, un garde-fou qui n'existait pas, une skill qui n'a pas été invoquée,
un fichier introuvable, une information inaccessible. Chaque perte devient un candidat : règle (`AGENTS.md`),
garde-fou (`kwa.policy.json`), skill ou pointeur de navigation. Préférer un contrôle automatique à une consigne en
prose quand l'erreur est mécanique. Le même tableau de l'étape 4 les accueille.

## 3. Router chaque candidat

| Nature | Destination | Forme |
|---|---|---|
| Décision d'architecture ou de produit | `memory.decisions_dir` (défaut `docs/decisions/`) | ADR numéroté : Contexte · Décision · Conséquences |
| Piège, gotcha, procédure | `memory.gotchas_file` (défaut `docs/gotchas.md`) ou la doc concernée | entrée datée : symptôme · cause · correctif |
| Convention ou commande valable pour tout agent | `AGENTS.md`, **hors** du bloc `kwa:begin…end` | une ligne, au bon chapitre |
| Erreur répétable | `.claude/kwa.policy.json` (`bash.deny/ask`, `write.deny`) | règle `{id, reason, all/any}` + cas de test si possible |
| Préférence de collaboration, retour sur ta façon de faire | mémoire de l'agent (fichier mémoire, selon la configuration de la session) | une idée par fichier, avec *Pourquoi* et *Comment l'appliquer* |
| Client, mission, décision métier, transverse aux projets | base de connaissance de l'équipe via `$KWA_VAULT_INBOX` (capture rapide **seulement**) | une ligne datée ; jamais un fichier marqué immuable ; données financières ou RH : ne pas y écrire |
| Amélioration générale de Kwa lui-même | boîte de réception de l'équipe, étiquette `#kwa` | une ligne : problème rencontré, idée |

Si `KWA_VAULT_INBOX` n'est pas défini, ne rien écrire dans la base de connaissance : le dire.

## 4. Proposer

Présenter à l'utilisateur **un tableau** (max. 7 lignes) : n° · candidat en une phrase · destination · preuve
(fichier:ligne ou commande). Puis, pour chaque ligne retenue, le diff exact qui serait appliqué. Demander quoi
appliquer (« tout », « 1 et 3 », « rien »).

## 5. Appliquer et clôturer

- Appliquer **seulement** les lignes validées, par lot ; relire le résultat.
- Une règle de garde-fou ajoutée à la politique : la tester (`bash tests/run-safety.sh` du pack si disponible, ou un
  cas manuel) avant de dire qu'elle marche.
- `python3 .claude/kwa/bin/kwa-memory clear` pour archiver les notes traitées.
- Ne pas committer : rappeler que `/kwa-commit` existe, sur la branche de travail.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kwa.
