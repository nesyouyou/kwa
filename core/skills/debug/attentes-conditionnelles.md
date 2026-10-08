# Attentes conditionnelles

Complément de `/kwa-debug`. Les tests instables devinent souvent un délai. Sur une machine rapide, ils passent ;
en CI ou sous charge, ils échouent. On attend **la condition**, pas une durée.

## Quand l'appliquer

- Un test contient `sleep`, `setTimeout`, `waitForTimeout`, `time.sleep`.
- Un test passe parfois, échoue sous charge ou en parallèle.
- On attend un événement asynchrone : job traité, message reçu, élément affiché, écriture en base visible.

Exception : tester un vrai comportement temporel (anti-rebond, intervalle de relance). Alors le délai est voulu :
le commenter en disant pourquoi, et le dériver d'une constante du code plutôt que le recopier.

## Le motif

```typescript
// Mauvais : on devine la durée
await new Promise(r => setTimeout(r, 50));
expect(getResult()).toBeDefined();

// Bon : on attend l'état voulu, avec délai maximal
await waitFor(() => getResult() !== undefined, 'résultat disponible');
expect(getResult()).toBeDefined();
```

## Outils déjà fournis par les stacks

| Contexte | À utiliser |
|---|---|
| Playwright | assertions web qui réessaient (`expect(locator).toBeVisible()`), `waitForResponse`, `expect.poll` ; pas de `waitForTimeout` |
| Jest / Vitest, composants | `waitFor`, `findBy*` (Testing Library) |
| Jest / Vitest, horloge | horloge simulée (`useFakeTimers`) pour le code temporel |
| API, worker, file | interroger l'état (ligne en base, statut du job) en boucle avec délai maximal |

Si aucun utilitaire n'existe, écrire une petite fonction : interroger toutes les 10 à 50 ms, retourner dès que la
condition est vraie, lever une erreur au délai maximal qui nomme la condition attendue.

## Erreurs fréquentes

- **Interroger trop serré** (boucle sans pause) : charge CPU inutile ; viser 10 à 50 ms.
- **Pas de délai maximal** : un test qui boucle à l'infini ; toujours une borne et un message clair.
- **Lire un état périmé** : évaluer la condition à chaque tour, ne pas mémoriser la valeur avant la boucle.
- **Attendre un détail interne** au lieu de ce que l'utilisateur observe.

## Après le correctif

Relancer le test plusieurs fois et en parallèle ; un test qui ne passe qu'une fois sur trois n'est pas corrigé.
Un test dont l'instabilité reste inexpliquée n'est pas ignoré en silence : voir `/kwa-verify`.
