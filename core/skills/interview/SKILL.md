---
name: kwa-interview
description: Interroger sans relâche l'utilisateur sur un plan, une conception ou une décision pour l'éprouver avant d'agir. À utiliser quand il dit « challenge-moi », « interviewe-moi », « grille-moi », « teste mon idée », « /kwa-interview », ou quand un plan paraît flou, que des termes du domaine se contredisent ou que /kwa-brainstorm bute sur une décision à fort enjeu.
allowed-tools: Read Grep Glob Bash(git log *) Bash(git status *) Write Edit
---

# Éprouver un plan par l'interrogatoire

Le but est une compréhension partagée, pas un livrable. On parcourt l'arbre des décisions jusqu'à ce que chaque
branche soit tranchée ou écartée à voix haute. Cette skill ne produit pas de code et n'implémente rien.

## Règles du jeu

1. **Une question par message.** L'humain répond à la plus facile si on en pose cinq. Une question, un message.
2. **Ta recommandation à chaque question.** Formuler la question pour que « oui » vaille acceptation de ta
   recommandation, avec la raison en une phrase. Ne jamais poser une question nue.
3. **Chercher avant de demander.** Si la réponse se trouve dans le code, `git log`, `AGENTS.md`, les décisions
   (`memory.decisions_dir`, défaut `docs/decisions/`) ou la base de connaissance de l'équipe, aller la lire. Les faits sont ton
   travail ; les décisions sont celles de l'humain.
4. **Dans l'ordre de l'arbre.** Une décision dont la réponse dépend d'une autre encore ouverte attend. Poser d'abord
   celle qui débloque le plus de branches.
5. **Citer le code quand il contredit.** « Tu dis X, mais `fichier:ligne` fait Y. Lequel est juste ? »
6. **Pas de remplissage.** Aucune validation de politesse, aucun résumé après chaque réponse.

## Format d'une question

```
Q<n> - <titre court> : <la question, avec les options si elles sont fermées>
Ma recommandation : <option> parce que <raison>.
```

Une fois par bloc de 4 à 5 décisions tranchées, rappeler en trois lignes ce qui est acquis. Cela évite que l'humain
perde le fil, sans ralentir.

## Éprouver le vocabulaire

Un plan flou cache souvent des mots flous. Pendant l'interrogatoire :

- **Un mot en conflit** avec le glossaire existant : le signaler tout de suite et demander lequel est juste.
- **Un mot vague ou surchargé** (« compte », « client », « annulation ») : proposer un terme canonique et demander
  confirmation.
- **Un scénario concret** pour tester une frontière : inventer le cas limite qui force à préciser (annulation
  partielle, doublon, droit manquant), plutôt que demander « et si... ? » en général.
- **Un contrôle croisé avec le code** quand l'humain décrit un comportement : si le code dit autre chose, le dire.

## Consigner, sur accord

Ne rien écrire sans demander. Quand un point cristallise, proposer l'écriture en une ligne et attendre le « oui ».

| Quoi | Où | Condition |
|---|---|---|
| Terme tranché | `GLOSSARY.md` à la racine (ou `docs/GLOSSARY.md` si le projet range ses docs là) | un terme propre au projet, défini en une ou deux phrases, avec les synonymes à éviter. Aucun détail d'implémentation. |
| Décision durable | ADR dans `memory.decisions_dir` (défaut `docs/decisions/`) | les trois à la fois : difficile à inverser, surprenante sans contexte, vrai arbitrage entre alternatives. Sinon, pas d'ADR. |

- Glossaire : une entrée par terme, **Terme** puis définition, puis « À éviter : ... ». Inscrire au fil de l'eau,
  pas en lot final. Un glossaire n'est ni une spec ni un brouillon.
- ADR : numéro suivant, Contexte, Décision, Conséquences, alternatives écartées et pourquoi. Même format que
  `/kwa-learn`.
- Respecter `write.deny` et `write.no_code_on_main` de la politique : pas d'écriture sur `main` si elle couvre
  ces dossiers. Pas de nom de personne, de financement ni de lien privé dans ces fichiers.
- Rien n'est committé. `/kwa-commit` sur demande.

## Terminer

L'interrogatoire est fini quand toutes les branches de l'arbre sont visitées et que rien n'est resté supposé en
silence. Le dire : « Plus de branche ouverte. » Puis résumer en un court tableau : décision, raison, ce qui reste
à faire. Attendre la confirmation de l'humain avant d'agir.

Suite possible, au choix de l'humain : `/kwa-brainstorm` pour écrire la spec, `/kwa-plan` pour le plan,
`/kwa-architecture` si l'enjeu est la structure du code, `/kwa-learn` pour capitaliser le reste.
`/kwa-brainstorm` peut appeler cette skill pour une décision difficile ; la reprise se fait là où il s'était arrêté.

## Signaux d'alerte

| Pensée | Réalité |
|---|---|
| « Je pose toutes mes questions d'un coup » | Une question par message. Les autres dépendent peut-être de la première. |
| « Je demande, c'est plus rapide que chercher » | Si le code répond, demander gaspille le temps de l'humain. |
| « Je n'ai pas de recommandation, je laisse choisir » | Sans position, la question ne fait pas avancer. Prendre parti, quitte à être contredit. |
| « J'écris l'ADR, c'est évident » | Écrire sur accord. Et si l'un des trois critères manque, pas d'ADR. |
| « Il a compris, je passe au code » | Cette skill s'arrête à la compréhension. Le code attend l'accord explicite. |

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kwa.
