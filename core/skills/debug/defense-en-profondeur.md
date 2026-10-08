# Défense en profondeur

Complément de `/kwa-debug`. Une fois la cause racine corrigée, une seule validation ne suffit pas : un autre chemin
d'appel, un refactor ou un double de test peut la contourner. Valider à **chaque couche** que la donnée traverse
rend le bug impossible plutôt que corrigé.

## Les quatre couches

1. **Entrée.** Rejeter l'invalide à la frontière (route d'API, formulaire, paramètre de commande) : vide, mauvais
   type, inexistant, hors plage. Erreur explicite qui nomme le champ et la valeur reçue.
2. **Logique métier.** Vérifier que la donnée a du sens pour *cette* opération, même si l'entrée est déjà validée
   (ex. une organisation requise pour cette action, un état de commande compatible).
3. **Garde d'environnement.** Interdire l'opération dangereuse dans un contexte précis : en test, refuser
   d'écrire hors d'un dossier temporaire ; en recette, refuser toute écriture destructive ; jamais de migration
   réécrite. Ces gardes sont des filets, pas des frontières de sécurité.
4. **Traçabilité.** Journaliser le contexte (valeur, appelant, environnement) avant l'opération risquée, pour
   que la prochaine investigation commence avec des preuves. Sans donnée personnelle ni secret dans les journaux.

## Méthode

1. Suivre la donnée de sa source jusqu'à l'endroit où elle casse.
2. Lister chaque point de passage.
3. Ajouter une vérification à chacun, avec son test (`/kwa-tdd`).
4. Tester chaque couche séparément : contourner la première, la deuxième doit encore arrêter le bug.

## Limites

Ne pas empiler des validations qui n'ont pas d'échec plausible : une couche par risque réel, pas par principe.
Une validation sert à échouer fort et clairement, jamais à réparer en silence (pas de valeur par défaut qui masque l'absence).
