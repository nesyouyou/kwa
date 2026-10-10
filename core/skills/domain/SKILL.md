---
name: kwa-domain
description: Construire et affiner le vocabulaire métier d'un projet (GLOSSARY.md) et consigner les décisions durables (ADR) pendant la conception. À utiliser quand des termes du domaine se contredisent ou restent flous, quand on écrit ou modifie GLOSSARY.md ou un ADR, ou quand l'utilisateur dit « glossaire », « vocabulaire », « on note la décision », « /kwa-domain ».
allowed-tools: Read Grep Glob Write Edit
---

# Le vocabulaire du domaine

Quand l'équipe dit « compte » pour trois choses différentes, l'agent code l'une des trois. Un glossaire court,
tenu pendant la conception, évite ce malentendu. Cette skill sert quand on **change** le vocabulaire ; le lire
pour s'en servir est un réflexe de toute skill.

## Les fichiers

- **`GLOSSARY.md`** à la racine pour la plupart des dépôts. Si un `GLOSSARY-MAP.md` existe, le projet a plusieurs
  contextes : la carte dit où vit le glossaire de chacun et comment ils se parlent.
- **Les ADR** dans le dossier de décisions de la politique (`memory.decisions_dir`, par défaut `docs/decisions/`),
  numérotés `0001-<sujet>.md`.
- Les créer au moment où il y a quelque chose à écrire, pas avant. Le format est dans [formats.md](formats.md).

## Pendant la conception

1. **Confronter au glossaire.** Un terme employé autrement que sa définition : le relever tout de suite.
   « Le glossaire dit qu'une annulation porte sur toute la commande ; tu parles d'annuler une ligne. Lequel ? »
2. **Préciser le flou.** Un mot surchargé : proposer le terme canonique. « Compte : le client ou l'utilisateur ? »
3. **Éprouver par des cas.** Inventer des scénarios limites qui forcent à tracer la frontière entre deux notions.
4. **Recouper avec le code.** Quand l'utilisateur dit comment une chose marche, vérifier que le code dit pareil, et
   signaler l'écart.
5. **Écrire au fil de l'eau.** Un terme tranché entre dans `GLOSSARY.md` aussitôt, et tu le dis. Pas de liste à
   reporter plus tard.

`GLOSSARY.md` ne contient que le langage du domaine : ni détail d'implémentation, ni spec, ni brouillon, ni
notion générale de programmation (délai d'attente, type d'erreur).

## Les ADR, rarement

Proposer un ADR seulement si les trois sont vrais :

1. **Difficile à défaire** : changer d'avis plus tard coûte cher.
2. **Surprenant sans contexte** : un lecteur futur se demandera « pourquoi comme ça ? ».
3. **Issu d'un vrai arbitrage** : il y avait des alternatives, on en a choisi une pour des raisons précises.

S'il en manque un, pas d'ADR. L'écrire sur accord de l'utilisateur.

## Avec les autres skills

`/kwa-interview` s'appuie sur ce glossaire pour poser ses questions, `/kwa-rephrase` en reprend les termes, et
`/kwa-learn` peut proposer d'y ranger un terme découvert en session.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit 49dd158) ; réécrit pour Kwa.
