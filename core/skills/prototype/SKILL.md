---
name: kata-prototype
description: Construire un prototype jetable pour répondre à une question de conception. À utiliser quand l'utilisateur doute qu'un modèle d'état ou une logique tienne, ou veut voir plusieurs formes d'interface avant de choisir ("fais un proto", "est-ce que ça tient ?", "montre-moi des variantes", "/kata-prototype"). Pas pour du code destiné à la production.
allowed-tools: Read Grep Glob Write Edit Bash
---

# Prototype jetable

Un prototype est du code qui **répond à une question**, puis disparaît. La réponse est le livrable, pas le code.

## Loi de fer

```
LE PROTOTYPE N'EST JAMAIS FUSIONNÉ TEL QUEL. ON GARDE LA RÉPONSE, PAS LE CODE.
```

Le code d'un prototype saute les tests, les erreurs et les limites : il ne sert que ce qu'il a prouvé.
Si l'utilisateur veut le garder, c'est une nouvelle demande : la cadrer avec `/kata-brainstorm` puis la refaire
proprement avec `/kata-tdd`.

## 1. Écrire la question d'abord

Avant la moindre ligne : une phrase qui commence par un verbe de décision, et un critère de réponse.

- « Le modèle d'état couvre-t-il l'annulation après paiement partiel ? »
- « Quelle forme de tableau de bord lit-on le plus vite : liste, grille ou résumé ? »

Une question sans critère donne un prototype sans fin. Si elle est floue, `/kata-grill` d'abord. La voie
« sonde » de `/kata-brainstorm` mène ici.

## 2. Choisir la forme selon la question

| La question porte sur | Forme |
|---|---|
| Logique, transitions d'état, forme des données | Un fichier autonome (un seul HTML ouvrable par double-clic, ou un script) avec la logique dans un module pur, séparé de l'affichage, et des boutons qui font évoluer l'état. Afficher l'état complet après chaque action. |
| Aspect, mise en page, parcours | Trois variantes radicalement différentes (pas trois nuances) sur la page réelle, choisies par un paramètre d'URL ou un interrupteur. Avec les vraies données et le vrai entourage, sinon toutes les variantes ont l'air bonnes dans le vide. |

Question ambiguë et utilisateur absent : choisir la forme qui colle au code voisin (module métier : logique ;
page : interface) et écrire l'hypothèse en tête du prototype.

## 3. Règles de construction

1. **Périmètre minimal** : seulement ce qui répond à la question. Un cas, un parcours.
2. **Dossier isolé et marqué jetable** : `prototypes/<sujet>/` ou un nom contenant `prototype`. Une ligne d'en-tête
   « PROTOTYPE JETABLE, à supprimer » dans chaque fichier. Suivre le routage du projet si une page est requise.
   Respecter `write.deny` et `write.no_code_on_main` : travailler sur une branche ou un worktree
   (`/kata-start-dev`), jamais sur `main`.
3. **Sans persistance** : état en mémoire. Si la persistance est la question, une base ou un fichier de
   brouillon nommé « jetable ».
4. **Sans test ni finition** : aucune abstraction, gestion d'erreur minimale pour que ça tourne. Pas de dépendance
   nouvelle sans accord.
5. **Facile à lancer** : une commande ou un fichier à ouvrir. Donner cette commande.
6. **Aucun secret, aucune donnée client réelle** : des données factices.
7. **Une seule passe** : si on réécrit trois fois, la question était mal posée. S'arrêter et la reposer.

## 4. Conclure

Écrire la réponse, en quelques lignes : question, verdict (oui / non / oui sous condition), ce qui l'a montré,
ce qu'on ignore encore, ce qu'on décide de faire. Puis, au choix de l'humain :

- **Supprimer** le dossier. C'est le défaut.
- **Archiver** sur une branche à part, hors `main`, avec un pointeur dans l'issue ou la spec.

La décision validée se reporte dans la spec ou l'ADR (`/kata-learn`), jamais le code du prototype. Rien n'est
committé sans demande (`/kata-commit`).

## Signaux d'alerte

| Pensée | Réalité |
|---|---|
| « Il marche, je le garde » | Refusé : nouvelle demande, à cadrer et refaire proprement. |
| « J'ajoute des tests pour être sûr » | Les tests servent le code durable. Le prototype sert une réponse. |
| « Je rajoute un cas, ça coûte peu » | Chaque cas hors question retarde la réponse. Le noter, ne pas le construire. |
| « Je n'ai pas écrit la question, mais je vois ce qu'il veut » | Sans question écrite, impossible de savoir quand s'arrêter. |

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kata.
