---
name: kwa-audit
description: À utiliser pour passer un dépôt ou un dossier au crible de la sur-ingénierie et de la dette, par exemple « audite ce code », « qu'est-ce qu'on peut supprimer », « trouve le code mort », « on a trop de dépendances », « ce dossier est devenu illisible », avant un gros refactor ou une reprise de projet. Produit un rapport, ne modifie rien.
allowed-tools: Read Grep Glob Agent Bash(git log *) Bash(git status *) Bash(wc *)
---

# Auditer la sur-ingénierie et la dette

Un audit liste ce qui peut disparaître ou se simplifier, avec la preuve et le gain. Il n'applique rien.
Les corrections passent ensuite par `/kwa-plan` et `/kwa-execute`, sur accord.

## Loi de fer

```
AUCUNE MODIFICATION PENDANT L'AUDIT. UN CONSTAT SANS PREUVE fichier:ligne N'EST PAS UN CONSTAT.
```

Seule exception : écrire `docs/dette.md`, et uniquement si l'utilisateur l'a demandé (voir plus bas).

## Procédure

1. **Cadrer.** Dépôt entier ou dossier ? Si c'est large, demander la zone qui fait mal. Lire `AGENTS.md`,
   `package.json` (ou équivalent) et la structure de premier niveau pour connaître la stack.
2. **Balayer en parallèle.** Pour un périmètre de plus de quelques dizaines de fichiers, lancer des sous-agents
   `Explore` en lecture seule, un message, plusieurs appels : un par axe ou par sous-dossier (voir la grille).
   Leur demander des candidats avec `fichier:ligne`, pas des conclusions. Voir `/kwa-parallel` pour le découpage.
3. **Vérifier chaque candidat soi-même** avant de le retenir. Un sous-agent signale, il ne tranche pas.
4. **Classer** par gain décroissant, puis rédiger le rapport.
5. **Proposer** la suite : lesquels corriger, lesquels consigner comme dette.

## Grille de recherche

| Axe | Ce qu'on cherche | Preuve à fournir |
|---|---|---|
| Usage unique | Interface à une implémentation, fabrique à un produit, wrapper qui ne fait que déléguer, fichier d'une seule ligne exportée | Nom de l'abstraction, son unique appelant |
| Code mort | Export jamais importé, fonction jamais appelée, drapeau toujours égal, route sans client, branche inatteignable | Recherche du symbole : zéro occurrence hors définition |
| Dépendances | Paquet jamais importé, doublon fonctionnel, lib pour quelques lignes, équivalent natif | Aucun `import` ; fonction native de remplacement |
| Couches sans valeur | Service qui recopie le contrôleur, DTO identique au modèle, dépôt par-dessus l'ORM | Les deux fichiers côte à côte, champs identiques |
| Duplication | Même logique à plusieurs endroits, helper qui double un existant | Les emplacements, ce qui diffère (rien, ou presque) |
| Configuration morte | Options jamais lues, variables d'environnement inutilisées, valeurs jamais changées | Recherche de la clé : seule la définition apparaît |

Avant de classer un élément « mort », chercher dans tout l'arbre : tests, fixtures, scripts, configuration, et
références dynamiques ou par chaîne (routage par fichiers, injection, noms de champs Payload, tâches planifiées).
En cas de doute, le marquer « à confirmer » et ne pas l'inclure dans le gain.

## Format du rapport

Une ligne par constat, numérotée, pour qu'on puisse dire « corrige 2 et 5 » :

`N. [axe] Quoi. Remplacement. gain : -X lignes / -Y dépendances. risque : faible|moyen|élevé. preuve : chemin:ligne`

- **Gain** : estimé honnêtement, jamais gonflé ; un chiffre inconnu s'écrit « non estimé ».
- **Risque** : faible si les tests couvrent et que la suppression est locale ; élevé si migration, contrat d'API,
  sécurité, donnée de client ou usage dynamique possible.
- **Preuve** : le `fichier:ligne` de la définition, plus la recherche qui montre l'absence d'usage.

Terminer par le total (`net : -X lignes, -Y dépendances possibles`), les trois meilleurs rapports gain/risque,
puis les zones non regardées et pourquoi. Rien à couper : le dire, c'est un résultat.

## Hors périmètre

Bugs de correction, failles de sécurité et performance : les signaler en une ligne à part si on les croise, puis
les router vers `/kwa-review` ou `/kwa-debug`. Ne pas ouvrir de chantier ici. Les tests ne se comptent pas
comme du bloat : un test qui protège un comportement reste.

## Consigner la dette retenue

Proposer à la fin : « Je consigne ce qu'on garde dans `docs/dette.md` ? » Écrire seulement si l'utilisateur dit oui.
Créer le fichier s'il manque, ajouter sinon, sans réécrire l'existant. Une entrée par dette retenue :

```
### <titre court> (<AAAA-MM-JJ>)
- Où : chemin:ligne
- Pourquoi on la garde : <raison métier ou technique>
- Coût de ne rien faire : <ce que ça coûte par mois ou par évolution : lenteur de lecture, bug probable, dépendance à patcher>
- Déclencheur de reprise : <événement qui fait basculer>
```

Pas de nom de personne ni d'hypothèse de financement dans ce fichier (voir les règles de confidentialité du bloc Kwa).
Une dette sans déclencheur de reprise pourrit : en exiger un. Aucun commit sans demande : `/kwa-commit`.

## Rationalisations

| Excuse | Réalité |
|---|---|
| « Je corrige tout de suite, c'est évident » | L'audit s'arrête au rapport. L'accord vient avant la modification. |
| « Plus aucun appel, donc mort » | Chercher les usages dynamiques, les tests et la config avant de l'affirmer. |
| « Le sous-agent l'a dit » | Vérifier chaque candidat avant de le retenir. |
| « Je gonfle le gain pour convaincre » | Un chiffre faux ruine la confiance dans tout le rapport. |
| « Il y a trop de constats, je les garde tous » | Classer et couper : dix constats utiles valent mieux que cinquante. |

## Suite

Constats approuvés : `/kwa-plan`, puis `/kwa-execute` avec `/kwa-tdd` ; chaque suppression est vérifiée par
`/kwa-verify`. Le critère de choix de chaque simplification vient de `/kwa-simple`.

> Inspiré de ponytail (DietrichGebert, MIT, commit 552acd5) ; réécrit pour Kwa.
