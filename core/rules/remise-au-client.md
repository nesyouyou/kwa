---
description: Ce dépôt sera remis au client — quatre tests avant d'écrire dans un fichier versionné
---

# Le lecteur final n'est pas nous (Kwa · client-handover)

Ce dépôt sera remis au client. **Tout ce qui est versionné part avec lui** : le code, les commentaires, les docs,
l'outillage `.claude/`. Avant d'écrire dans un fichier suivi, quatre tests (code et outillage ; `docs/` est un
compte rendu daté et échappe aux tests 3 et 4) :

| Test | Question | Correction |
|---|---|---|
| **Secret** | Une valeur d'identifiant apparaît-elle ? | Variable d'environnement, sans valeur par défaut. Jamais de repli silencieux. |
| **Compte** | Une adresse personnelle ou prestataire est-elle câblée au produit ? | Variable d'environnement. Pour un exemple en commentaire : `@example.test`. |
| **Nom** | Une personne est-elle nommée ? | Un rôle : « le mainteneur », « l'administrateur ». Un rôle survit à une rotation d'équipe. |
| **Péremption** | Cette phrase sera-t-elle encore vraie dans six mois ? | Énoncer l'invariant, pas la mesure. |

Dans du **code**, un nombre mesuré documente une décision de conception et se garde ; dans un fichier
d'**instruction**, le même nombre date la consigne.

`python3 .claude/kwa/bin/kwa-hygiene` vérifie les quatre tests et tourne en CI. Les exceptions assumées vont dans
`.claude/kwa.hygiene.allow` avec leur échéance : le script les réaffiche à chaque exécution, cette liste tient lieu
de checklist de remise. Y ajouter une ligne est une décision, pas un contournement.
