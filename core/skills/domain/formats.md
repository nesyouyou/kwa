# Formats du glossaire et des ADR

## GLOSSARY.md

```md
# {Nom du contexte}

{Une ou deux phrases : ce qu'est ce contexte et pourquoi il existe.}

## Langage

**Commande** :
Demande d'un client portant sur un ou plusieurs articles.
_À éviter_ : achat, transaction

**Facture** :
Demande de paiement envoyée au client après la livraison.
_À éviter_ : note, demande de règlement
```

Règles :

- **Trancher.** Plusieurs mots pour une même notion : garder le meilleur, ranger les autres sous _À éviter_.
- **Définitions courtes.** Une ou deux phrases, ce que la chose **est**, pas ce qu'elle fait.
- **Seulement le domaine du projet.** Avant d'ajouter un terme : notion propre à ce métier, ou notion générale de
  programmation ? Seule la première entre.
- **Regrouper** sous des sous-titres quand des familles apparaissent ; sinon une liste suffit.

Plusieurs contextes : un `GLOSSARY-MAP.md` à la racine liste chaque contexte (lien vers son glossaire, une ligne de
rôle) puis leurs relations (« Commandes → Facturation : la livraison déclenche la facture »).

## ADR

```md
# {Titre court de la décision}

{Une à trois phrases : le contexte, la décision, la raison.}
```

C'est tout : un ADR peut tenir en un paragraphe. Sections facultatives, seulement si elles apportent quelque chose :
`Statut` (proposée, acceptée, remplacée par ADR-NNNN), `Options écartées` (si le rejet n'est pas évident),
`Conséquences` (si un effet en aval n'est pas visible).

Numérotation : chercher le plus grand numéro du dossier et ajouter un.

Ce qui mérite un ADR : la forme de l'architecture, la façon dont deux contextes communiquent, une technologie qui
enferme (base de données, fournisseur d'authentification, cible de déploiement), une frontière de responsabilité,
un écart volontaire au chemin évident, une contrainte invisible dans le code (conformité, contrat de temps de
réponse), une alternative écartée pour une raison qui ne saute pas aux yeux.
