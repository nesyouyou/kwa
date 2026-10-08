# Écrire des tests fiables

Complément de `/kwa-tdd`. Un test peut être vert et inutile : voici les quatre façons les plus courantes.

## 1. Tester le comportement, pas le mock

Un test qui vérifie qu'un mock existe ou a été appelé teste le test, pas le code.

```typescript
// Mauvais : on constate que le double est affiché
test('affiche la barre latérale', () => {
  render(<Page />);                       // Sidebar est doublée
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});

// Bon : on teste le vrai composant, ou on ne teste pas la barre ici
test('affiche la navigation', () => {
  render(<Page />);
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});
```

Question de contrôle avant chaque assertion : « est-ce que je teste un comportement réel, ou la présence de mon décor ? »
Si c'est le décor, supprimer l'assertion ou retirer le double.

## 2. Pas de méthode « pour les tests » en production

Une méthode appelée seulement par des tests (`reset()`, `destroy()`, `_setForTest()`) pollue la classe et s'appelle un jour en production par erreur.
La mettre dans un utilitaire de test (`tests/utils/`), qui manipule l'objet de l'extérieur.

Avant d'ajouter une méthode à une classe de production : qui l'appelle en dehors des tests ? Personne : elle n'a pas sa place là.

## 3. Comprendre avant de doubler

Avant de doubler une dépendance, se demander :

1. Quels effets de bord a la vraie méthode (écriture, config, cache) ?
2. Mon test en dépend-il, sans que je l'aie vu ?
3. Si oui, doubler plus bas (l'appel lent ou externe) et laisser le comportement dont dépend le test.

Signal d'alerte : un double ajouté « pour être tranquille », sans pouvoir dire ce qu'il remplace. Autre signal : un
test qui échoue de façon inexplicable dès qu'on ajoute un double, car l'effet de bord dont il dépendait a disparu.

## 4. Doubles fidèles à la réalité

Un double de réponse API doit avoir la structure complète de la vraie réponse (tous les champs que le code aval lit),
pas seulement ceux que ton test utilise. Un champ manquant dans le double passe en test et casse en production.
Partir d'une vraie réponse enregistrée ou du schéma de l'API.

## Garde-fou général

Pour chaque test, savoir répondre : « quel changement de code le ferait échouer ? » Aucune réponse : il ne protège rien.
Un test jamais vu en rouge reste suspect, même s'il paraît juste.
