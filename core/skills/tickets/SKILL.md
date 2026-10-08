---
name: kwa-tickets
description: Découper une spec, un plan ou une discussion en tickets GitHub livrables séparément, avec leurs dépendances. À utiliser quand une demande est trop grosse pour une seule issue ou une seule PR, quand un plan validé doit être réparti entre plusieurs personnes ou agents, ou quand l'utilisateur dit "découpe en tickets", "fais les issues", "/kwa-tickets".
allowed-tools: Bash(gh issue *) Bash(gh auth status) Bash(git log *) Read Grep Glob
---

# Découper en tickets

Un gros chantier livré d'un bloc se relit mal, se teste mal et se défait mal. On le coupe en **balles traçantes** :
chaque ticket traverse toutes les couches de bout en bout sur un cas étroit, et se livre et se vérifie seul.
Cette skill produit la liste, la fait valider, puis crée les issues. **Rien n'est créé sans accord.**

Articulation : `/kwa-brainstorm` cadre le besoin, `/kwa-plan` écrit le plan local (étapes d'exécution pour
l'agent), `/kwa-tickets` répartit le travail en issues GitHub. Chaque ticket est ensuite repris par
`/kwa-start-dev <issue>` (branche, worktree, preuve, PR). `/kwa-interview` aide si la spec est encore floue.

## Étape 1 : rassembler

Partir de ce qui est déjà dans la conversation, ou de la référence donnée (chemin de spec ou de plan, numéro
d'issue : `gh issue view <n°> --comments`). Lire le code concerné pour connaître l'état réel, et le vocabulaire
du domaine du projet pour nommer les tickets. Si la spec est floue, s'arrêter et passer par `/kwa-interview`.

Chercher les **préparatifs** : une petite refonte qui rend le reste facile se fait en premier, dans son ticket.
Rendre le changement facile, puis faire le changement facile.

## Étape 2 : tracer les tranches verticales

Règles :

- Une tranche coupe un chemin étroit mais **complet** (données, API, interface, tests) : jamais une couche seule.
- Une tranche est démontrable ou vérifiable seule, avec une preuve qu'on peut citer.
- Une tranche tient dans un contexte de travail frais : si elle déborde, la couper.
- Pas de ticket « faire le schéma » suivi de « faire l'interface » : c'est une coupe horizontale.

**Exception : le refactor large** (renommer une colonne, changer le type d'un symbole partagé, tout casse d'un coup).
Ne pas le forcer en tranche. Procéder par expansion puis contraction : ajouter la nouvelle forme à côté de
l'ancienne (rien ne casse) ; migrer les appelants par lots (par paquet, par dossier), un ticket par lot, chacun
bloqué par l'expansion ; supprimer l'ancienne forme dans un dernier ticket bloqué par tous les lots.

Pour chaque ticket, fixer ses **dépendances bloquantes** : les tickets qui doivent être finis avant lui. Pas de
dépendance par confort, seulement par nécessité réelle. Sans bloquant, le ticket peut démarrer tout de suite :
c'est ce qui permet de paralléliser (`/kwa-parallel`, `/kwa-agents`).

## Étape 3 : proposer la liste, avant toute création

Présenter une liste numérotée, rien d'écrit sur GitHub. Pour chaque ticket :

- **Titre** : court, au format du projet (`feat(portée): …`, en français).
- **Bloqué par** : numéros de la liste, ou « aucun ».
- **Livre** : le comportement de bout en bout, vu de l'utilisateur.
- **Preuve attendue** : ce qui montrera que c'est fait (test, capture, commande).

Demander : la taille est-elle bonne (trop gros, trop fin) ? Les dépendances sont-elles réelles ? Faut-il fusionner
ou couper ? Itérer jusqu'à l'accord explicite.

## Étape 4 : gabarit d'un ticket

Aligné sur `.github/ISSUE_TEMPLATE/` (`feature.md` pour une évolution, `bug.md` pour un correctif). Corps dans un
fichier temporaire :

```markdown
## Parent

<!-- #<n°> de l'issue ou de la spec d'origine ; omettre sinon -->

## Besoin

Le comportement que ce ticket rend possible, vu de l'utilisateur. Pas une liste de tâches par couche.

## Décisions

Choix déjà arrêtés qui s'imposent à ce ticket (autrement : « aucune »).

## Bloqué par

- #<n°> ... ou « aucun : peut démarrer tout de suite »

## Critères de réussite

- [ ] Critère observable et vérifiable (une commande, un écran, une réponse)
- [ ] ...

## Preuve

<!-- Ajoutée à la livraison, voir /kwa-start-dev -->
```

Éviter chemins de fichiers et extraits de code : ils périment vite. Seule exception : un extrait qui fixe une
décision plus précisément que la prose (schéma, machine d'états), réduit à l'essentiel.
Un critère vérifiable se réfute : « la liste affiche 20 lignes par page », pas « la pagination est correcte ».

## Étape 5 : créer, sur accord seulement

Après le « oui » de l'utilisateur, et seulement alors :

1. `gh auth status`, puis vérifier qu'aucune issue équivalente n'existe : `gh issue list --search "<mots>" --state open`.
2. Créer **un ticket à la fois, bloquants d'abord**, pour pouvoir citer de vrais numéros :
   `gh issue create --title "<titre>" --body-file <fichier> --label <bug|enhancement>`.
3. Reporter le numéro obtenu dans les sections « Bloqué par » des tickets suivants avant de les créer.
4. Rendre à l'utilisateur la liste finale : numéro, titre, bloquants, lien.

Ne pas fermer ni modifier l'issue parente. Ne pas ajouter de labels qui n'existent pas dans le dépôt.
Le travail démarre par `/kwa-start-dev` avec `--issue <n°>`, en commençant par les tickets sans bloquant.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kwa.
