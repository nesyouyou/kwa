---
name: kata-architecture
description: Repérer où approfondir les modules d'un dépôt quand le code est dur à comprendre, à tester ou à modifier sans tout casser — interfaces larges sur peu de logique, couplages, fuites d'implémentation, tests qui visent l'intérieur. À utiliser pour un audit d'architecture, avant une refonte, ou quand un même secteur du code revient sans cesse dans les correctifs ("l'architecture est bancale", "où refactorer", "/kata-architecture").
allowed-tools: Bash(git log *) Bash(git diff *) Read Grep Glob
---

# Approfondir l'architecture

Un module profond cache beaucoup de comportement derrière une petite interface. Un module superficiel fait
l'inverse : il expose presque autant qu'il contient. Cette skill cherche les modules superficiels qui coûtent cher
et propose de les approfondir. **Lecture seule : aucune modification sans l'accord de l'utilisateur.**
Elle s'enchaîne avec `/kata-interview` (creuser l'option choisie), `/kata-plan` (planifier la refonte), `/kata-tickets`
(la découper), `/kata-simple` (nettoyage local) et `/kata-audit` (revue plus large).

## Vocabulaire commun

Employer ces mots, et pas « composant », « service », « API » ou « frontière » : ils brouillent le propos.

| Terme | Sens |
|---|---|
| Module | Tout ce qui a une interface et une implémentation : fonction, classe, paquet, tranche verticale. |
| Interface | Tout ce qu'un appelant doit savoir : signature, mais aussi invariants, ordre d'appel, erreurs, configuration, coûts. |
| Profondeur | Quantité de comportement exploitable par unité d'interface à apprendre. |
| Couture | Endroit où l'on change un comportement sans éditer sur place ; là où vit l'interface. |
| Adaptateur | Chose concrète qui remplit une interface à une couture (base réelle, double en mémoire). |
| Levier | Ce que gagnent les appelants : une implémentation sert N sites d'appel et M tests. |
| Localité | Ce que gagnent les mainteneurs : changements, bugs et vérifications se concentrent au même endroit. |

Quatre principes guident le jugement :

- **Test de suppression** : imagine supprimer le module. Si la complexité disparaît, c'était un simple passe-plat.
  Si elle réapparaît chez N appelants, il méritait sa place.
- **L'interface est la surface de test** : si pour tester il faut passer derrière l'interface, la forme est mauvaise.
- **Un adaptateur, c'est une couture hypothétique ; deux, une couture réelle.** Pas de couture sans variation réelle.
- **Dépendances, pas fabrication** : un module reçoit ses dépendances, il ne les instancie pas ; il rend des résultats
  plutôt que de produire des effets de bord.

## Étape 1 : cadrer

- Si l'utilisateur nomme un secteur (module, sous-système, douleur), partir de là.
- Sinon, chercher les points chauds : `git log --name-only --since="6 months ago"` et compter les fichiers qui
  reviennent. Le code qui change souvent rapporte le plus quand on l'approfondit.
- Lire d'abord `AGENTS.md`, la doc d'architecture et les décisions déjà prises (`docs/decisions/`) du secteur.
  Une décision écrite ne se rediscute pas sans friction réelle ; si un candidat la contredit, le signaler explicitement.
- Employer le vocabulaire du domaine du projet pour nommer les modules (« le module de prise de commande », pas
  « le FooBarHandler »).

## Étape 2 : explorer sans grille rigide

Lire le code, noter où l'on peine. Questions utiles :

- Où comprendre une notion oblige-t-il à sauter entre beaucoup de petits modules ?
- Où l'interface est-elle presque aussi complexe que l'implémentation ?
- Où des fonctions pures ont-elles été extraites « pour tester » alors que les vrais bugs vivent dans la façon de
  les appeler (aucune localité) ?
- Où des modules très couplés fuient-ils l'un dans l'autre à travers leur couture ?
- Quelles parties sont sans test, ou intestables par leur interface actuelle ?

Appliquer le test de suppression à tout soupçon de module superficiel. Classer les dépendances du candidat :
en mémoire (fusionner et tester directement), substituable en local (doublure locale dans la suite de tests),
distante mais possédée (port et deux adaptateurs : réel et mémoire), vraiment externe (port injecté, double simulé).

## Étape 3 : rapport classé

Présenter dans la conversation (pas de fichier, pas de page HTML) un classement de 3 à 7 candidats, du plus rentable
au plus spéculatif. Pour chacun :

- **Où** : fichiers et lignes (`chemin:ligne`). Une affirmation sans preuve est une opinion : la retirer.
- **Problème** : la friction concrète, avec le terme précis du vocabulaire (interface large, fuite, couture fausse…).
- **Piste** : en une ou deux phrases, ce qui changerait. Pas de signature détaillée à ce stade.
- **Gain** : en localité et en levier, et ce que deviendraient les tests.
- **Force** : `forte`, `à explorer` ou `spéculative`.

Terminer par la recommandation : par quoi commencer et pourquoi. Puis demander « lequel veux-tu creuser ? ».

Un rapport écrit dans `docs/architecture/AAAA-MM-JJ-<sujet>.md` n'est créé **que sur demande**, avec le même contenu.

## Étape 4 : creuser le candidat choisi

Lancer `/kata-interview` sur l'option retenue : contraintes, dépendances, forme du module approfondi, ce qui se trouve
derrière la couture, quels tests survivent. Règles de la discussion :

- Une fois le nouveau module en place, les anciens tests sur les modules superficiels deviennent du bruit : on les
  remplace par des tests à l'interface, on ne les empile pas.
- Un terme du domaine encore flou se tranche pendant la discussion, et se note dans la doc du projet avec accord.
- Si l'utilisateur refuse pour une raison durable (contrainte, choix assumé), proposer de la consigner en décision
  (`/kata-learn`) pour que le prochain audit ne la repropose pas. Pas pour une raison passagère.
- Pour comparer plusieurs formes d'interface, en dessiner deux ou trois très différentes et les juger sur la
  profondeur, la localité et l'emplacement de la couture.

## Interdits

- Modifier du code, renommer, déplacer, sans accord explicite.
- Proposer une refonte « parce que c'est plus propre » sans friction observée ni preuve.
- Lister toutes les refontes théoriques : un classement court vaut mieux qu'un inventaire.
- Committer ou pousser (`/kata-commit`, `/kata-ship` sur demande seulement).

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kata.
