---
name: kwa-research
description: Répondre à une question factuelle (comportement d'une API, version, option d'un outil, spécification) à partir des sources primaires, avec une citation par affirmation, dans un fichier daté. À utiliser quand une décision attend un fait extérieur au dépôt, avant d'écrire une affirmation technique qu'on n'a pas vérifiée, ou quand l'utilisateur dit « vérifie dans la doc », « renseigne-toi », « /kwa-research ».
allowed-tools: Read Grep Glob Write WebFetch WebSearch Agent
---

# Chercher un fait à la source

Ce que tu crois savoir d'une bibliothèque date de ton entraînement. Une option a pu être renommée, un
comportement a pu changer. Le but est un fait **vérifié à sa source**, assez précis pour décider, et une trace que
quelqu'un d'autre peut relire.

## Faire

1. **Cadrer la question.** Une API, un comportement, une version. « Renseigne-toi sur X » ne se cherche pas : le
   découper en questions auxquelles on peut répondre par oui, non ou une valeur. Écrire la question en tête du
   fichier.
2. **Déléguer la lecture, une seule fois.** Lance un sous-agent en arrière-plan pour lire, et continue ton travail.
   **Si tu es toi-même ce sous-agent, fais la recherche toi-même : ne lance pas d'autre agent.**
3. **Lire les sources primaires.** Documentation officielle, code source, spécification, journal des versions,
   réponse réelle de l'API. Un article qui résume une doc accessible ne compte pas : remonter à la doc.
4. **Citer chaque affirmation** : le lien exact (avec l'ancre si possible) et la date de lecture. Ce que tu n'as
   pas pu vérifier est écrit comme tel, jamais complété de mémoire. Deux sources primaires qui se contredisent :
   les citer toutes les deux et le dire.
5. **S'arrêter** quand chaque question cadrée a sa réponse sourcée, ou quand il est établi qu'aucune source
   primaire ne répond. Pas de tour d'horizon au-delà de la question.
6. **Écrire le fichier** dans le dossier de notes du projet s'il en a un, sinon dans
   `.claude/kwa/local/research/<AAAA-MM-JJ>-<sujet>.md` (local, non versionné : un fait daté vieillit vite).
   Le garder dans le dépôt seulement si l'utilisateur le demande.
7. **Rendre compte en cinq lignes au plus** : la réponse, les deux citations qui la portent, ce qui reste non
   vérifié, le chemin du fichier.

## Contrôle

Avant de rendre la main, suis deux citations au hasard. Si l'une mène à un résumé et non à la chose elle-même, la
recherche n'est pas finie.

## Ce que cette skill ne fait pas

- Décider : un fait nourrit la décision, qui se prend avec l'utilisateur (`/kwa-interview`).
- Tester dans le code : savoir si une approche marche ici, c'est `/kwa-prototype`.
- Consigner une décision durable : un ADR, avec `/kwa-domain`.

Un piège trouvé en chemin, qui coûtera encore : le noter pour `/kwa-learn`.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit 49dd158) ; réécrit pour Kwa.
