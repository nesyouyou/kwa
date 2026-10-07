---
name: kata-agent-docs
description: Écrire ou modifier un document destiné aux agents : skill, AGENTS.md, règle, gabarit, note de politique. À utiliser dès qu'on crée ou édite un fichier dans .claude/skills, .claude/rules, core/skills ou AGENTS.md, quand une skill ne se déclenche pas comme prévu, ou quand l'utilisateur dit « écris une skill », « ajoute une règle », « /kata-agent-docs ».
allowed-tools: Read Grep Glob Edit Write
---

# Écrire pour des agents

Un document d'agent est lu à chaque exécution par un lecteur qui n'a que lui. Son travail est de rendre le
**processus** prévisible, pas la sortie. Chaque ligne coûte du contexte ou de l'attention : elle doit changer un
comportement.

## 0. Avant d'écrire : où cela va-t-il ?

| Vous voulez... | Destination |
|---|---|
| Une procédure déclenchée par une situation | une skill (`.claude/skills/<nom>/SKILL.md`, ou `core/skills/` dans le pack) |
| Une convention valable pour tout agent du projet | `AGENTS.md`, **au-dessus ou en dessous** du bloc `<!-- kata:begin ... -->` jamais dedans |
| Une règle commune à tous les projets Nakama | `.claude/rules/kata-*.md` : ce sont des fichiers gérés, à modifier dans le pack, pas localement |
| Un garde-fou qui doit **empêcher** (commande, chemin) | `.claude/kata.policy.json`, pas un texte : un texte se contourne, une garde non |
| Une connaissance durable (décision, piège) | `/kata-learn` : docs du projet, pas un document d'agent |

Le bloc géré de `AGENTS.md` et les fichiers `kata-*` sont réécrits à la mise à jour : toute retouche locale s'y
perd (elle est sauvegardée, mais pas conservée). `CLAUDE.md` reste un pointeur `@AGENTS.md`.

## 1. Ce qui va dans le document

- **Le non-dérivable** : la convention non écrite, la raison d'un choix, le piège qu'aucune config ne révèle.
- **Les branches** : chaque cas distinct que le document traite, avec son critère.
- **Un critère de fin vérifiable** : une commande, un état observable, « chaque règle appliquée ». Pas « terminer
  quand c'est bien ».
- **Un exemple** là où une règle peut être lue de deux façons.

## 2. Ce qui n'y va pas

- Ce que l'environnement dit déjà : scripts de `package.json`, structure des dossiers, `--help`. Le document
  en serait une copie qui vieillit. Pointer vers la source.
- Un récit de session, une hypothèse non vérifiée, une date relative.
- Ce que l'agent fait déjà par défaut (« sois rigoureux »). Une phrase qui ne change rien est du bruit : la
  supprimer entière.
- La même idée à deux endroits. Une source de vérité par sens ; l'autre document y renvoie.
- Des noms de personnes, des financements, des liens privés, des secrets.

## 3. Concision et clarté

- Une idée par phrase. Impératif, voix active, sujet d'abord.
- **Dire le comportement voulu**, pas l'interdit : une interdiction fait penser à la chose interdite. Une
  interdiction n'a sa place que comme garde-fou impossible à formuler en positif ; l'accompagner alors de la
  conduite attendue.
- **Un mot directeur** vaut une phrase : réutiliser un terme déjà familier (« rouge » pour un test qui échoue,
  « jetable » pour un prototype) et le garder identique partout.
- Tableaux pour les décisions (si... alors...), listes numérotées pour les séquences, prose pour le reste.
- Taille : une skill de 180 lignes au plus. Au-delà, déplacer le détail dans une annexe du même dossier citée
  par une phrase qui dit quand la lire.

## 4. La description : un déclencheur, pas un résumé

La description est toujours chargée. Elle décide si la skill est choisie ; elle doit donc dire **quand**.

- Mettre en premier le mot qui déclenche. Lister des situations réelles et des phrases que l'humain dit.
- Un déclencheur par branche. Des synonymes d'une même branche sont un seul déclencheur écrit deux fois.
- **Ne jamais y mettre le déroulé.** Un agent qui lit les étapes dans la description saute le corps.
- Ne pas répéter ce que le nom porte déjà.
- Skill qu'on ne lance que par commande : `disable-model-invocation: true`, description courte pour l'humain.
- Frontmatter Kata : `name: kata-<nom>`, `description:`, `allowed-tools:` au plus juste.

## 5. Éviter la dérive

- **Élaguer à chaque édition** : ajouter est facile, retirer semble risqué, d'où les couches mortes. Avant
  d'ajouter, relire pour supprimer.
- **Vérifier contre le réel** : le fichier, la commande, la clé de politique cités existent-ils encore ?
- **Tester par l'usage** : lancer le scénario dont le document dépend, avec un agent sans contexte, et observer
  s'il prend le bon chemin. Une divergence se règle par un mot plus fort ou une branche explicite, pas par un
  paragraphe de plus.
- Renvoyer vers les skills existantes plutôt que recopier leur contenu (`/kata-commit`, `/kata-review`...).
- Pas de compatibilité de façade : on supprime proprement ce qui est remplacé.
- Rien n'est committé sans demande (`/kata-commit`).

## 6. Relire avant de rendre

Cochez : où va ce texte (§0) ? chaque ligne change-t-elle un comportement ? la description dit-elle quand, pas
comment ? un critère de fin vérifiable ? rien de dupliqué ni de dérivable ? sous 180 lignes ?

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kata.
