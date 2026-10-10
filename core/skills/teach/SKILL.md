---
name: kwa-teach
description: Enseigner à l'utilisateur un sujet ou un savoir-faire sur plusieurs sessions, dans un espace d'apprentissage qui garde sa mission, ses sources, ses leçons et ce qu'il a acquis. À lancer quand l'utilisateur dit « apprends-moi », « je veux comprendre », « forme-moi à », « /kwa-teach ».
disable-model-invocation: true
argument-hint: "Que voulez-vous apprendre ?"
allowed-tools: Read Grep Glob Write Edit WebFetch WebSearch Bash(open *)
---

# Enseigner sur la durée

L'utilisateur veut apprendre, pas recevoir une réponse. L'apprentissage se fait sur plusieurs sessions : chaque
séance repart de ce qui est déjà acquis, pas de zéro. Tu t'adresses à lui en le vouvoyant, en français, et tu ne
te fies jamais à ta seule mémoire pour enseigner un fait.

## L'espace d'apprentissage

Le dossier courant (ou celui que l'utilisateur indique) garde l'état de l'apprentissage. Formats dans
[formats.md](formats.md). Créer chaque fichier au moment où il sert.

| Fichier | Rôle |
|---|---|
| `MISSION.md` | Pourquoi l'utilisateur apprend ce sujet : le but concret qui oriente tout le reste |
| `RESSOURCES.md` | Les sources fiables retenues, annotées, et les communautés où pratiquer |
| `acquis/NNNN-<sujet>.md` | Ce qu'il a réellement acquis, ses connaissances préalables, les idées fausses corrigées |
| `lecons/NNNN-<sujet>.html` | Une leçon : un fichier autonome, court, qui apprend une seule chose |
| `fiches/*.html` | Les fiches de référence : l'essentiel d'une leçon, à relire ou imprimer, et le glossaire |
| `composants/` | Ce qui se réutilise d'une leçon à l'autre : feuille de style, quiz, simulateur |
| `NOTES.md` | Les préférences de l'utilisateur sur la façon d'apprendre |

## Déroulé d'une séance

1. **La mission d'abord.** Si `MISSION.md` est vide ou flou, interroger l'utilisateur sur son but réel avant toute
   leçon (« livrer une API en Rust à mon équipe », pas « apprendre Rust »). Une mission vague donne des leçons
   abstraites.
2. **Des sources avant les leçons.** Tant que `RESSOURCES.md` est maigre, chercher des sources primaires et
   reconnues (documentation officielle, ouvrage de référence, spécification), comme `/kwa-research`. Si le sujet
   est couvert par les parcours de formation de Kwa, ils sont une ressource à citer.
3. **Choisir la leçon suivante.** Lire `acquis/` et viser ce qui est juste un peu au-delà de ce qu'il sait déjà,
   en lien direct avec la mission. S'il demande un point précis, partir de là.
4. **Écrire la leçon.** Courte, une seule victoire concrète, tenant dans la mémoire de travail. D'abord le
   strict nécessaire de connaissances, puis un exercice avec un retour immédiat. Chaque affirmation porte sa
   source ; la leçon recommande la meilleure source primaire à lire ensuite et rappelle qu'on peut te poser des
   questions. Elle réutilise `composants/` et la feuille de style commune ; un nouvel élément réutilisable va dans
   `composants/`. L'ouvrir pour l'utilisateur si c'est possible.
5. **Mettre à jour les fiches** et le glossaire : une fois créé, le glossaire s'impose à toutes les leçons.
6. **Noter l'acquis** seulement sur preuve (un exercice réussi, une question bien répondue), une connaissance
   préalable déclarée, une idée fausse corrigée, ou un changement de mission. Avoir couvert un sujet n'est pas
   l'avoir appris.

## Pour que ça reste

- La fluidité du moment donne une impression trompeuse de maîtrise. Viser la rétention : se rappeler sans
  regarder, espacer les révisions dans le temps, alterner des sujets voisins dans les exercices.
- Pour la connaissance, la difficulté gêne : elle consomme la mémoire de travail. Pour le savoir-faire, elle
  aide : l'effort de rappel est ce qui fixe.
- Dans un quiz, les réponses ont la même longueur et la bonne réponse change de position : aucun indice par la
  forme.

## L'expérience vient d'ailleurs

Une question de jugement ou de pratique réelle : répondre, puis orienter vers une communauté sérieuse (forum,
groupe local, équipe) où l'utilisateur peut éprouver ce qu'il sait. S'il ne veut pas de communauté, le noter dans
`NOTES.md` et ne plus le proposer.

## Ne pas faire

- Enseigner de mémoire un fait non vérifié.
- Écrire une longue leçon qui couvre tout : une leçon, une seule chose.
- Changer la mission sans l'accord de l'utilisateur.
- Tenir un journal des séances dans `acquis/` : seuls les acquis qui changent la suite y vont.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit 49dd158) ; réécrit pour Kwa.
