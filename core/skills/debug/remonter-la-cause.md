# Remonter la chaîne causale

Complément de `/kata-debug`. Le bug se manifeste en bas de la pile ; la cause est presque toujours plus haut.
Corriger là où ça casse traite le symptôme.

## Technique

1. **Observer le symptôme** : l'erreur exacte, par exemple `git init` exécuté dans le mauvais dossier.
2. **Trouver l'appelant direct** : quelle ligne a émis l'appel qui casse ?
3. **Demander : qui l'a appelé, et avec quelle valeur ?** Remonter d'un cran, noter la valeur à chaque étage.
4. **Continuer jusqu'à la source** : l'endroit où la valeur fausse naît (chaîne vide, `undefined`, mauvaise clé, état périmé).
5. **Corriger à la source**, puis ajouter des garde-fous aux étages traversés (`defense-en-profondeur.md`).

Ne jamais s'arrêter au premier endroit où l'on « voit » le problème.

## Quand la trace manque : instrumenter

Si on ne peut pas remonter à la main, journaliser **juste avant** l'opération qui échoue, pas après :

- la valeur reçue, le dossier courant, la variable d'environnement concernée ;
- une trace d'appel (`new Error().stack`, `traceback.print_stack()`) ;
- sur une sortie d'erreur visible (dans les tests, un journal peut être masqué).

Lancer une fois, lire, trier : chercher le fichier de test, le worker, la route ou l'écran qui déclenche, et les
valeurs répétées. Retirer l'instrumentation ensuite.

## Un test pollue l'état d'un autre

Quand un test crée un fichier, une ligne ou un état global qui ne devrait pas exister, trouver le coupable en
bissectant : lancer les tests un à un (ou par moitié) jusqu'à isoler celui qui laisse la trace. Le correctif porte
sur ce test (nettoyage, isolation par dossier ou base temporaire), pas sur celui qui subit.

## Contrôle

Avant de corriger, tu dois pouvoir écrire en une phrase : « la valeur X naît en <lieu> parce que <raison>, traverse
<étages> et casse en <lieu> ». Impossible : tu n'as pas la cause.
