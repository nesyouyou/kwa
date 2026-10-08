# Boucle de diagnostic

Une boucle de retour fiable vaut plus que toute lecture de code. Si une commande dit « rouge » exactement quand
le bug se produit et « vert » quand il disparaît, la cause finit par se trouver : bissection, hypothèses et sondes
ne font que consommer ce signal. Sans elle, on raconte des histoires.

## Construire la boucle, du plus simple au plus lourd

1. Un test qui échoue, à la couture qui atteint le bug (unitaire, intégration, de bout en bout).
2. Un appel HTTP scripté contre le serveur de développement.
3. Une commande avec une entrée figée, dont la sortie est comparée à une référence connue.
4. Un script de navigateur sans interface qui pilote l'écran et vérifie le DOM, la console, le réseau.
5. Le rejeu d'une trace réelle : requête ou événement sauvegardé, rejoué sur le chemin de code isolé.
6. Un banc jetable : un seul service, dépendances simulées, une seule fonction appelée.
7. Une boucle d'entrées aléatoires (1 000 tirages) quand le défaut est « parfois faux ».
8. Une bissection automatique (`git bisect run`) quand le bug est apparu entre deux états connus.
9. Un différentiel : même entrée dans l'ancienne et la nouvelle version, sorties comparées.
10. En dernier recours, un script qui guide l'humain pas à pas et collecte son retour.

## L'affûter

- Plus rapide : mettre la préparation en cache, réduire le périmètre du test. Quelques secondes, pas des minutes.
- Plus net : vérifier le symptôme exact, jamais « ne plante pas ».
- Plus déterministe : figer l'heure, fixer la graine aléatoire, isoler le disque, couper le réseau.
- Bug intermittent : viser un taux de reproduction élevé. Rejouer 100 fois, en parallèle, sous charge, en
  resserrant les fenêtres de timing. À 50 %, on débogue ; à 1 %, non.

## Critère de fin de la phase

Une commande nommée, déjà lancée une fois (sortie montrée, secrets masqués), qui est :

- capable de rougir sur **ce** bug et de verdir une fois corrigé, pas seulement « s'exécute sans erreur » ;
- déterministe, ou à taux de reproduction fixé ;
- rapide ;
- exécutable sans humain.

Si aucune boucle n'est possible : le dire, lister ce qui a été essayé, demander un accès à l'environnement, un
artefact capturé (journal, HAR, enregistrement horodaté) ou l'autorisation d'instrumenter. Ne pas conjecturer.

Puis réduire : retirer entrées, appelants, configuration, étapes **un par un** en relançant la boucle, jusqu'à ce
que chaque élément restant soit nécessaire. Ce cas minimal devient le test de non-régression.

## Prouver que le correctif agit : la mutation

Un test vert après correction ne prouve rien s'il aurait été vert sans lui.

1. Boucle rouge, avec le correctif absent : noter la sortie.
2. Appliquer le correctif : la boucle passe au vert.
3. **Retirer le correctif** (défaire la modification, ou la neutraliser) : le symptôme doit **revenir**.
4. Le remettre : vert de nouveau.

Si le symptôme ne revient pas en 3, le correctif n'est pas la cause du retour au vert : coïncidence, cache,
instabilité. Reprendre l'enquête. Si le rouge initial a été forcé en modifiant du code ou une donnée, comparer
avec une copie intacte (`diff`) pour s'assurer que la modification a bien eu lieu.

## Performance

Les journaux trompent ici. Établir d'abord une mesure de référence : banc de chronométrage, profileur, plan de
requête, taille de bundle. Même protocole avant et après (même machine, mêmes données, plusieurs passes, médiane
et dispersion). Bissecter sur la mesure, corriger, remesurer. Annoncer le gain en chiffres, pas en impression.

## Sondes

Chaque sonde répond à une prédiction écrite. Un seul changement à la fois. Préférer un débogueur à dix journaux,
jamais « tout journaliser puis chercher ». Préfixer chaque journal temporaire d'une étiquette unique
(`[DEBUG-a4f2]`) : le nettoyage se réduit à un `grep`.

## Nettoyage avant de conclure

- La boucle d'origine ne reproduit plus le symptôme.
- Le test de non-régression passe (ou l'absence de couture est notée : c'est un constat d'architecture, voir `/kwa-architecture`).
- Plus aucune sonde étiquetée dans le code ; les bancs jetables sont supprimés.
- L'hypothèse qui s'est avérée est écrite dans le message de commit ou de PR.
