---
name: kata-reexplain
description: Reformuler le dernier message quand l'utilisateur n'a pas compris. À utiliser dès qu'il dit « stop », « je ne comprends pas », « explique autrement », « reformule », « c'est quoi ça ? », « /kata-reexplain ».
disable-model-invocation: true
---

# Reformuler autrement

Le message précédent n'a pas atterri. Le répéter à l'identique recommence l'échec. Ce n'est pas une question
d'intelligence de l'utilisateur : c'est ton explication qui a raté.

## Faire

1. **Poser le contexte en une ou deux phrases** : où on en est et pourquoi ce point compte. Le message précédent
   supposait peut-être un contexte absent.
2. **Dire l'essentiel en une phrase** avant tout détail. Si cette phrase est impossible à écrire, c'est que le
   message d'origine était confus : le dire et trancher.
3. **Un exemple concret** : un cas réel du projet, avec des valeurs, de préférence plutôt qu'une métaphore. Un
   avant/après vaut une définition.
4. **Mots simples** : phrases courtes, une idée chacune, voix active, sujet d'abord. Un terme technique qui doit
   rester est défini à sa première occurrence.
5. **Vocabulaire du projet** : reprendre les termes du `GLOSSARY.md` s'il existe, pas des synonymes inventés.
6. **Terminer par ce qui est attendu** : décision à prendre, action à valider ou rien du tout. Dire clairement
   lequel.

## Ne pas faire

- Reprendre les mêmes phrases en changeant deux mots.
- Ajouter plus de jargon pour « préciser ».
- S'excuser longuement, ou répondre « comme je l'ai dit ». Aucune condescendance non plus : pas de « en gros, pour
  faire simple » ni de ton de maître d'école.
- Allonger. La reformulation est plus courte que l'original, sauf si l'exemple l'exige.
- Changer le fond en douce. Si une erreur apparaît en reformulant, la signaler : « En reformulant, je vois que
  j'avais tort sur... »

## Si la reformulation échoue aussi

Demander **un seul point précis** : « Qu'est-ce qui coince : le mot X, le pourquoi, ou ce que je te demande ? »
Reformuler à nouveau à partir de la réponse. Si le sujet est un plan entier flou, proposer `/kata-grill`.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kata.
