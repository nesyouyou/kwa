---
name: kata-simple
description: À utiliser avant d'écrire du code neuf, et dès qu'une solution prévoit une abstraction, une dépendance, une option de configuration ou un « au cas où ». Déclencheurs — ajouter une fonctionnalité, un helper, un wrapper, une lib, un cache, un service ; ou quand l'utilisateur dit « le plus simple », « sans sur-ingénierie », « YAGNI », « on a vraiment besoin de ça ? ».
---

# Le plus simple qui marche

Le meilleur code est celui qu'on n'écrit pas. Chaque ligne se relit, se teste, se migre et se déboguera un jour.
Avant de produire, on grimpe l'échelle ci-dessous et on s'arrête au premier barreau qui tient.

## Loi de fer

```
AUCUN CODE NEUF TANT QU'UN BARREAU PLUS HAUT DE L'ÉCHELLE N'A PAS ÉTÉ ESSAYÉ ET ÉCARTÉ AVEC UNE RAISON.
```

L'échelle raccourcit la solution, jamais la compréhension. Lire d'abord la demande et le code concerné, suivre le
flux réel de bout en bout, puis seulement grimper. Un petit diff au mauvais endroit n'est pas simple : c'est un
second bug.

## L'échelle

| # | Barreau | Le test | Si oui |
|---|---|---|---|
| 1 | Ne pas le faire | Qui est bloqué aujourd'hui sans ce code ? Personne : le besoin est spéculatif. | Ne rien écrire, le dire en une ligne. |
| 2 | Cela existe déjà dans le dépôt | `Grep` du verbe métier, du type, du nom voisin ; lire le dossier frère. | Réutiliser, ne pas réécrire. |
| 3 | La stdlib ou la plateforme le fait | Existe-t-il une fonction native, un attribut HTML, une règle CSS, une contrainte SQL ? | L'utiliser. |
| 4 | Une dépendance déjà installée le fait | `package.json`, lockfile, modules déjà importés. | L'utiliser. Aucune nouvelle dépendance pour quelques lignes. |
| 5 | Une option de configuration suffit | Un réglage existant du framework, de Payload, d'Expo, de l'infra, change-t-il le comportement ? | Changer la config, pas le code. |
| 6 | Un petit ajout au code existant | Peut-on étendre une fonction ou un composant en place, sans nouveau fichier ? | Ajouter, le plus court possible. |
| 7 | Code neuf | Tous les barreaux plus hauts ont été écartés, chacun avec sa raison. | Le minimum qui passe le test. |

Deux barreaux conviennent : prendre le plus haut et avancer. Deux options de même taille : prendre celle qui est
juste sur les cas limites. Écrire moins ne veut pas dire choisir l'algorithme fragile.

## Ne pas spéculer

- Pas d'interface à une seule implémentation, pas de fabrique pour un seul produit.
- Pas de paramètre, de drapeau ou de configuration pour une valeur qui ne change jamais.
- Pas d'échafaudage « pour plus tard » : plus tard saura s'échafauder lui-même.
- Pas de couche qui ne fait que déléguer, pas de fichier qui n'exporte qu'une ligne.
- Une généralisation attend le deuxième vrai cas d'usage, pas le deuxième imaginaire.
- Une simplification qui coupe un vrai coin (verrou global, parcours en O(n²)) se note par un commentaire court :
  la limite connue et le déclencheur de la reprise.

## Excuses

| Excuse | Réalité |
|---|---|
| « Ce sera utile plus tard » | Plus tard demande souvent autre chose. Le code inutile se paie tout de suite. |
| « C'est plus propre avec une abstraction » | Une abstraction à un seul usage cache le code sans le simplifier. |
| « Une lib le fait déjà » | Une dépendance se met à jour, se sécurise et casse. Pour dix lignes, écrire les dix lignes. |
| « Je ne sais pas si ça existe déjà » | Le chercher prend une minute. Dupliquer coûte une maintenance. |
| « Je le rends configurable, au cas où » | Chaque option est une branche à tester. Personne ne la réglera. |
| « Le framework impose cette structure » | Vérifier dans sa documentation avant de la croire. |
| « C'est rapide à écrire » | Ce qui est rapide à écrire est rarement rapide à relire et à maintenir. |

## Signaux d'alerte

Arrêter et remonter l'échelle si tu écris :

- une classe ou un type dont un seul appelant se sert ;
- un `utils`, `helpers` ou `manager` nouveau pour une seule fonction ;
- un wrapper autour d'un appel qui n'ajoute ni validation ni gestion d'erreur ;
- un paramètre optionnel que personne ne passe, un `try/catch` qui avale l'erreur ;
- une dépendance ajoutée pour un format de date, un clone profond, un identifiant ;
- plus de lignes de justification que de lignes de code.

## Sur les stacks Nakama

- **Next.js** : composant serveur avant composant client ; `fetch` et cache natifs avant une lib de requêtes ;
  CSS et variables avant un état JS ; `<dialog>`, `<details>`, `<input type="date">` avant une bibliothèque de
  composants ; le routage par fichiers avant un routeur maison.
- **NestJS** : un module et un service par vrai domaine, pas par entité ; les pipes et gardes natifs avant un
  décorateur maison ; pas de dépôt (repository) qui double déjà l'ORM ; pas d'interface pour un fournisseur unique.
- **Prisma** : une contrainte (`@unique`, clé étrangère, valeur par défaut) avant un contrôle applicatif ; un
  `select` précis avant une couche de mapping.
- **Expo / React Native** : les modules Expo SDK avant un paquet natif tiers (il coûte un build et un risque
  de compatibilité) ; les composants de base avant une bibliothèque d'interface ; un hook local avant un store global.
- **Payload** : une option de champ ou de collection (`access`, `defaultValue`, `validate`, `hooks`) avant un
  endpoint sur mesure ; un bloc existant réutilisé avant un nouveau bloc ; toute modification du schéma garde
  sa migration, la simplicité ne la supprime pas.

## Ce qu'on ne simplifie jamais

Validation aux frontières de confiance, gestion d'erreur qui évite une perte de données, sécurité, accessibilité
de base, migrations, et tout ce que l'utilisateur a demandé explicitement. S'il insiste sur la version complète,
la construire sans rediscuter.

## Articulation avec les autres skills

- `/kata-brainstorm` et `/kata-plan` : parcourir l'échelle avant de figer l'approche ; une tâche du plan qui n'a pas
  passé les barreaux 1 à 6 est à supprimer ou à justifier.
- `/kata-tdd` : le test dit le comportement minimal ; le code vert minimal s'arrête là, sans anticiper le test suivant.
- `/kata-execute` : un écart de simplicité par rapport au plan se signale, il ne se corrige pas en silence.
- `/kata-review` : l'axe « simplicité » juge le diff avec les mêmes barreaux.
- `/kata-audit` : applique cette échelle à un dépôt existant, pour trouver ce qui peut disparaître.

## Rendu

Le code d'abord. Puis trois lignes au plus : ce qui a été écarté et à quel déclencheur le reprendre.
Pas de plaidoyer : une explication plus longue que le code est de la complexité déguisée.

> Inspiré de ponytail (DietrichGebert, MIT, commit 552acd5) ; réécrit pour Kata.
