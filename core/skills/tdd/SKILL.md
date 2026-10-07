---
name: kata-tdd
description: Écrire du code produit en test d'abord (rouge, vert, refactor). À utiliser avant d'écrire la moindre ligne de code de fonctionnalité, de correctif ou de comportement modifié, côté API, web ou mobile, et dès qu'on touche ou écrit un test ("TDD", "test d'abord", "ajoute un test", "/kata-tdd").
---

# Test d'abord

Un test qu'on n'a jamais vu échouer ne prouve rien : il peut passer pour une mauvaise raison, ou ne rien tester.
Cette skill s'applique à tout code produit : fonctionnalité, correctif, changement de comportement, refactor.
Elle s'emboîte dans `/kata-start-dev` (circuit) et se complète de `/kata-debug` (cause racine) et `/kata-verify` (preuve finale).

## La loi

```
PAS DE CODE PRODUIT SANS UN TEST QUI A ÉCHOUÉ D'ABORD.
```

Violer la lettre de cette règle, c'est la violer tout court : pas de « esprit contre rituel ».

## Le cycle

### 1. Rouge : écrire un seul test

- Un comportement, un nom qui le décrit (`rejette un email vide`, pas `test2`). Un « et » dans le nom : scinder.
- Du vrai code. Un double (mock) seulement pour ce qui sort du processus : réseau, horloge, service tiers payant.
- Avant de l'écrire, dire quel changement de production le ferait échouer. Si tu ne sais pas, le test est flou.

### 2. Vérifier le rouge : obligatoire

Lancer **ce test seul** avec la commande de test de la stack (voir « Commandes »). Contrôler trois choses :

- Il **échoue** (une erreur de syntaxe ou d'import n'est pas un échec : corriger, relancer).
- Le message d'échec est celui attendu.
- Il échoue parce que la fonctionnalité manque, pas à cause d'une faute de frappe ou d'un décor mal monté.

Il passe du premier coup ? Il teste un comportement qui existe déjà. Réécrire le test.

### 3. Vert : le code minimal

Le plus simple qui fasse passer ce test. Pas d'option, pas de paramètre « au cas où », pas de refactor voisin
(règles « simplicité d'abord » et « changements chirurgicaux » du bloc Kata de `AGENTS.md`).

### 4. Vérifier le vert : obligatoire

Relancer le test, puis **toute la suite concernée** et les commandes de `verify.commands`. Un test vert ne dit rien
du reste. Une sortie propre : aucun warning ni erreur parasite. Tout échec constaté, même non causé par toi, se
signale par son nom dans le compte rendu.

### 5. Refactor, sous vert uniquement

Doublons, noms, extractions. Aucun comportement ajouté. Relancer après chaque pas : un test rouge pendant un
refactor veut dire que tu as changé le comportement, annule.

Puis le test suivant. Un cycle = un comportement.

## Du code écrit avant le test

Ça arrive. La réponse est brutale : **supprimer ce code** et repartir du test.

- Ne pas le garder « comme référence » : tu l'adapteras, ce serait un test écrit après.
- Ne pas le relire en écrivant le test : il biaiserait les cas que tu retiens.
- Ce qui a été appris (le bon algorithme, un piège) reste dans ta tête ; le code, lui, est rejoué sous test.
- Si la suppression te paraît coûteuse, c'est du coût irrécupérable : le choix réel est entre du code prouvé et du code qu'on ne peut pas croire.

Exploration autorisée : un essai jetable pour comprendre une API ou une idée, supprimé avant de commencer vraiment.

## Excuses courantes

| Excuse | Réalité |
|---|---|
| « Trop simple pour un test » | Le code simple casse aussi. Le test coûte une minute. |
| « Je teste après » | Un test écrit après passe tout de suite : il ne prouve pas qu'il détecte quoi que ce soit. |
| « Tests après = même résultat » | Après, tu vérifies ce que le code fait ; avant, ce qu'il doit faire. Tu ne testes que les cas dont tu te souviens. |
| « Je l'ai testé à la main » | Pas rejouable, pas tracé, oublié au premier changement. |
| « Supprimer, c'est du gâchis » | Le temps est déjà dépensé. Reste à choisir entre code prouvé et code invérifiable. |
| « Je garde pour référence » | Tu l'adapteras : c'est un test après. Supprimer veut dire supprimer. |
| « C'est difficile à tester » | Écoute le test : difficile à tester, c'est difficile à utiliser. Simplifier l'interface. |
| « Il faut tout mocker » | Le code est trop couplé. Injecter les dépendances. |
| « Le TDD me ralentit » | Il déplace le temps perdu en débogage vers l'avant, où il coûte moins. |
| « Là c'est différent » | Non. |

## Signaux d'alerte : stop, on reprend au rouge

Du code avant son test. Un test qui passe dès la première exécution. Un échec qu'on ne sait pas expliquer. « Les tests viendront ensuite. » « Juste cette fois. » « Je l'ai déjà essayé à la main. » « C'est du pragmatisme, pas du dogmatisme. » Un test qui ne vérifie que des appels de mock.

## Bons tests : comportement, pas mocks

Règles détaillées et exemples : `tests-fiables.md` (même dossier). À lire dès qu'on écrit ou modifie un test. Le noyau :

- Asserter sur le résultat observable (valeur, état, écran, réponse HTTP), jamais sur l'existence d'un mock.
- Aucune méthode « pour les tests » dans une classe de production : un utilitaire de test à côté.
- Comprendre les effets de bord d'une dépendance avant de la doubler ; ne pas doubler à l'aveugle.
- Un double incomplet par rapport à la vraie réponse masque des bugs d'intégration : le calquer sur la structure réelle.

## Cas particuliers

**Bug.** Le test de non-régression vient d'abord : il reproduit le bug, on le voit échouer pour la bonne raison,
puis on corrige. La cause racine se cherche avec `/kata-debug` *avant* d'écrire le correctif. Preuve rouge-vert :
corrige, test vert ; retire le correctif, le test redevient rouge ; remets-le.

**Code d'interface (web, mobile).** Tester le comportement visible : ce que l'utilisateur lit, clique, voit
changer. Pas la structure interne du composant ni les noms de classes. Un parcours complet relève d'un test de bout en bout.

**Migrations.** Une migration appliquée ne se réécrit jamais ; en créer une nouvelle. Le test porte sur le schéma
et les données résultants (colonne présente, ligne migrée, retour à l'état antérieur si prévu), sur une base de test jetable, jamais sur recette ni production.

**API (Vitest, Jest).** Tester au niveau route ou service avec une vraie base de test quand la stack le permet ;
doubler seulement les services tiers. Cas d'erreur et validation d'entrée inclus.

**Mobile Expo (Jest).** Jest pour la logique et les composants. Un module natif ajouté ou mis à jour ne se prouve
pas en Jest : `/kata-testflight` impose un test Release sur simulateur.

**Web (Playwright).** Un test par parcours utilisateur qui compte. Attendre une condition, jamais un délai fixe
(voir `/kata-debug`, section attentes). Le test échoue d'abord sur la fonctionnalité absente, pas sur un sélecteur erroné.

## Commandes

Ne rien coder en dur. Lire `.claude/kata.policy.json` : `verify.commands` pour la vérification globale, et le
`package.json` (ou l'équivalent) de la stack détectée pour lancer **un seul test**. Commande introuvable : le dire à l'utilisateur, ne pas deviner.

## Exceptions : à valider avec l'utilisateur

Seulement avec son accord explicite, demandé avant d'écrire le code, et notées dans le compte rendu :

- prototype jetable, destiné à être supprimé ;
- code généré par un outil ;
- fichier de configuration pur.

Se dire « on saute le test pour cette fois » est de la rationalisation, pas une exception.

## Liste de contrôle avant « fait »

- [ ] Chaque comportement nouveau a un test, vu en rouge avant le code, pour la bonne raison.
- [ ] Code minimal pour chacun ; rien d'extra.
- [ ] Suite concernée et `verify.commands` verts, sortie propre (`/kata-verify`).
- [ ] Tests sur du vrai comportement ; cas limites et erreurs couverts.

Une case décochée : le cycle a été sauté, reprendre. Ne jamais committer sans demande explicite : `/kata-commit`.

> Inspiré de superpowers (Jesse Vincent, MIT, v6.4.1) ; réécrit pour Kata.
