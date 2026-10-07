---
name: kata-brainstorm
description: Cadrer avant de coder une fonctionnalité ou un changement non trivial. À utiliser quand la demande crée un comportement, touche plusieurs fichiers ou une interface dont d'autres dépendent, laisse plusieurs lectures possibles, ou quand l'utilisateur dit « on pourrait », « je voudrais ajouter », « comment faire pour », « réfléchissons à ».
allowed-tools: Read Grep Glob Bash(git log *) Bash(git status *) Bash(gh issue *) Write Edit
---

# Cadrer avant de construire

Le coût d'une erreur de cadrage se paie en code jeté. Cette skill produit une spec courte que l'humain a lue et
approuvée. Elle ne produit pas de code.

## Loi de fer

```
AUCUN CODE PRODUIT, AUCUNE INSTALLATION, AUCUN SQUELETTE TANT QUE L'HUMAIN N'A PAS APPROUVÉ LE CADRAGE.
```

Lire le projet est permis à tout moment. Le reste attend le « oui ». Un « oui » vaut pour l'étape présentée, pas
pour les suivantes : l'accord sur une idée n'approuve pas une spec qui n'existe pas encore.

## 1. Choisir la voie, à voix haute

Annoncer la voie avant la première question, pour que l'humain puisse la corriger.

| Voie | Quand | Livrable |
|---|---|---|
| Sonde | « est-ce faisable ? », la sortie est une réponse, pas du code à garder | 2-3 phrases : question et essai prévu. Un feu vert, puis résultat en recommandation. Tout ce qui a été construit est étiqueté jetable. |
| Bornée | Changement net dans un flux qui existe déjà et qu'on peut lire dans le dépôt | Design court dans la conversation. Stop. Pas de fichier. Le code suit le « oui » (`/kata-tdd`). |
| Structurante | Nouveau module, interface dont d'autres dépendent, changement de modèle de données, plusieurs sous-systèmes | Parcours complet ci-dessous, spec écrite, puis `/kata-plan`. |

En cas d'hésitation entre deux voies, prendre la plus lourde. Le cliquet ne descend jamais : une complexité
découverte en route fait remonter la voie, on s'arrête et on le dit.

## 2. Parcours structurant

1. **Explorer le contexte.** `AGENTS.md`, `.claude/kata.policy.json`, code voisin, `git log` récent, issues
   ouvertes (`gh issue list --search`). Lire les décisions déjà prises (`memory.decisions_dir`, défaut
   `docs/decisions/`). Si la politique désigne une base de connaissance (`knowledge_base`), elle fait foi ; si elle est muette, le dire.
2. **Évaluer l'ampleur.** Si la demande couvre plusieurs sous-systèmes indépendants, le signaler tout de suite et
   proposer un découpage. Chaque sous-projet a sa spec, son plan, son cycle. Brainstormer le premier seulement.
3. **Poser les questions une par une.** Une question par message. Choix multiple quand c'est possible.
   Viser dans l'ordre : le but, pour qui, ce qui prouvera que c'est réussi, les contraintes, ce qui est hors
   périmètre. Ne pas redemander ce que la demande ou le code disent déjà.
4. **Reformuler.** Un court paragraphe : résultat attendu, contraintes, critères de réussite. Séparer ce que
   l'humain a dit de ce que tu as supposé. Attendre la correction avant d'aller plus loin.
5. **Proposer 2 à 3 approches.** Pour chacune : principe, coût, risque. Annoncer ta recommandation en premier,
   avec la raison. Retirer de chaque approche ce qui n'est pas nécessaire aujourd'hui.
6. **Valider le design par sections.** Une section = un message, de quelques phrases à 200 mots : architecture,
   composants et leurs frontières, flux de données, erreurs, tests. Demander après chaque section si elle tient.
   Revenir en arrière sans résistance.
7. **Écrire la spec.** Voir plus bas.
8. **Auto-relire.** Voir plus bas.
9. **Porte d'approbation.** Voir plus bas.

Règles de conception : des unités qui font une seule chose, avec une interface claire, testables seules.
Dans du code existant, suivre les motifs en place ; ne proposer un nettoyage que s'il gêne ce travail.

## 3. Écrire la spec

Chemin : `docs/specs/AAAA-MM-JJ-<sujet>.md`. Si la politique définit `memory.specs_dir`, ou un dossier de
documentation désigné pour les specs, l'utiliser à la place. Dossier absent : le créer. Pas d'écriture sur
`main` si `write.no_code_on_main` couvre ce dossier ; en cas de doute, travailler dans le worktree de
`/kata-start-dev`.

Une page ou deux. Fonctionnel et technique seulement : aucun nom de personne, hypothèse de financement ni lien
privé.

```markdown
# <Sujet>
Date : AAAA-MM-JJ · Issue : #<n°> si elle existe
## But et utilisateur
## Hors périmètre
## Contraintes
Valeurs exactes : versions, limites, règles de nommage, plateformes.
## Design
Composants, interfaces, flux de données, erreurs.
## Critères de réussite
Vérifiables : chacun se prouve par un test ou une commande.
## Tests
## Risques et questions ouvertes
Vide si aucune. Jamais de « à définir ».
```

## 4. Auto-relecture

Relire la spec comme un étranger, puis corriger sur place. Ne pas relancer de boucle.

- **Trous** : « à définir », « etc. », section vide, exigence floue.
- **Contradictions** : le design dit-il la même chose que le but et les critères ?
- **Ampleur** : tient-elle dans un seul plan ? Sinon, découper.
- **Ambiguïté** : une exigence lisible de deux façons ? Choisir et l'écrire.
- **Critères** : chacun est-il vérifiable par une commande de `verify.commands` ou un test nommé ?
- **Hors périmètre** : ce qui n'a pas été demandé est-il sorti ?

## 5. Porte d'approbation

Annoncer : « Spec écrite dans `<chemin>`. Relis-la et dis-moi ce qui change. Je ne passe au plan qu'après ton
accord. » Puis attendre. Une demande de modification relance l'auto-relecture. Un silence n'est pas un accord.

Après l'accord seulement : proposer `/kata-plan`. Aucune autre skill d'implémentation à ce stade. Commit de la
spec : seulement sur demande, via `/kata-commit`. Issue, branche, worktree : `/kata-start-dev`.

## Signaux d'alerte

| Pensée | Réalité |
|---|---|
| « C'est trop simple pour un cadrage » | Une phrase de design validée suffit pour une voie bornée. Zéro cadrage n'existe pas. |
| « C'est borné, je saute la spec » | Se chercher une étiquette pour éviter le travail est le doute lui-même : voie plus lourde. |
| « Je présente le design et je commence en même temps » | La porte, c'est le « oui », pas la longueur du texte. Présenter, puis s'arrêter. |
| « Je connais ce genre d'appli » | Borné se mesure au dépôt, pas à ta familiarité. Sans flux existant à lire, c'est structurant. |
| « Je pose cinq questions d'un coup, ça va plus vite » | L'humain répond à la plus facile et esquive le reste. Une question, un message. |
| « La sonde marche, je garde le code » | Garder le code est une nouvelle demande : la reclasser et la cadrer. |
| « Ça grossit, mais je suis presque au bout » | La complexité cachée fait remonter la voie. Stop, le dire. |
| « Il a dit oui à l'idée, donc à la spec » | Chaque étape a sa porte. Reprendre à la première étape non approuvée. |
| « Je n'ai pas besoin de lire le code, je devine » | Une spec bâtie sur une supposition produit un plan faux. Lire d'abord. |

## Fin

Voie sonde : recommandation rendue. Voie bornée : design approuvé, puis `/kata-tdd`. Voie structurante : spec
approuvée, puis `/kata-plan`. Pour capitaliser une décision durable : `/kata-learn`.

> Inspiré de superpowers (Jesse Vincent, MIT, v6.4.1) ; réécrit pour Kata.
