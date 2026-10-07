---
name: kata-plan
description: Transformer une spec approuvée (ou des exigences claires) en plan d'implémentation avant de toucher au code. À utiliser quand une tâche demande plusieurs étapes ou plusieurs fichiers, après /kata-brainstorm, ou quand l'utilisateur dit « fais-moi le plan », « découpe en tâches », « prépare l'implémentation ».
allowed-tools: Read Grep Glob Write Edit Bash(git log *) Bash(git status *)
---

# Écrire le plan d'implémentation

Un bon plan se lit sans contexte : celui qui l'exécute ne connaît ni la conversation ni les choix qui ont mené
ici. Il connaît le métier de développeur, pas ce dépôt. Tout ce dont il a besoin est dans le plan.

## Loi de fer

```
UN PLAN NE CONTIENT NI « TODO », NI « À DÉFINIR », NI « SIMILAIRE À LA TÂCHE N ».
CHAQUE ÉTAPE MONTRE LE CODE OU LA COMMANDE EXACTE.
```

## Prérequis

- Une spec approuvée par l'humain (`docs/specs/…` ou le dossier de la politique). Sans spec, demander si on cadre
  d'abord avec `/kata-brainstorm`. Pour un changement trivial et net, les exigences écrites dans la conversation
  tiennent lieu de spec : le dire, et les recopier dans l'en-tête du plan.
- Lire `.claude/kata.policy.json`. Les commandes du plan viennent de là, jamais de ta mémoire :
  - `verify.commands` : les vérifications finales de chaque tâche, recopiées telles quelles ;
  - `start.install` : l'installation, à mentionner dans la préparation, pas à réinventer ;
  - `write.deny` et `write.no_code_on_main` : chemins interdits ou dossiers protégés, à ne jamais planifier en écriture.
- Si `verify.commands` est vide, l'écrire en tête du plan comme question à l'humain. Ne pas inventer de commande.
- Si la spec couvre plusieurs sous-systèmes indépendants : un plan par sous-système, chacun livrant un résultat
  qui marche et se teste seul.

## Cartographier les fichiers d'abord

Avant les tâches, lister les fichiers créés ou modifiés, et le rôle de chacun. C'est ici que le découpage se
fige. Un fichier, une responsabilité. Ce qui change ensemble vit ensemble. Dans un dépôt existant, suivre ses
motifs ; n'inclure un découpage de fichier trop gros que s'il gêne le travail.

## Taille des tâches

Une tâche est la plus petite unité qui porte son propre cycle de test et que l'humain pourrait valider ou
rejeter seule. Intégrer dans la tâche qui en a besoin la configuration, l'échafaudage et la doc. Chaque tâche
finit sur un résultat testable.

Chaque étape est une action de 2 à 5 minutes : écrire le test qui échoue, le lancer et le voir échouer, écrire le
code minimal, le relancer, vérifier. Méthode de test : `/kata-tdd`.

## Fichier du plan

Chemin : `docs/plans/AAAA-MM-JJ-<sujet>.md` (ou `memory.plans_dir` si la politique le définit). Même règle de
branche que les specs : pas d'écriture sur `main` si le dossier est protégé.

En-tête obligatoire :

```markdown
# <Sujet> : plan d'implémentation
**But :** une phrase.
**Approche :** 2-3 phrases.
**Spec :** chemin du fichier. Le plan en découle ; l'exécutant lit les deux.
**Préparation :** commandes de `start.install` ; branche et worktree via /kata-start-dev.
**Vérification :** les `verify.commands` de la politique, copiées mot pour mot.

## Contraintes globales
Une ligne chacune, valeurs exactes de la spec : versions, limites, nommage, textes. S'appliquent à toutes les tâches.

## Points de vigilance
Les cas limites que la spec implique et qu'aucun test de tâche ne couvre : entrée, condition, comportement attendu.
Chacun reçoit un test dans la tâche qui possède le code. Section vide = vérifié, rien trouvé.
```

Structure d'une tâche :

````markdown
### Tâche N : <composant>
**Fichiers :** Créer `chemin/exact` · Modifier `chemin/exact:120-145` · Test `chemin/exact.test.ts`
**Consomme :** ce qui vient des tâches précédentes, signatures exactes.
**Produit :** noms, paramètres et types dont les tâches suivantes dépendent.
**Arrêt humain :** oui/non. Oui si la tâche touche un schéma, une interface publique, ou un effet de bord externe.

- [ ] **Étape 1 : écrire le test qui échoue** (bloc de code complet)
- [ ] **Étape 2 : le lancer.** Commande exacte. Attendu : ÉCHEC, avec le message précis.
- [ ] **Étape 3 : code minimal** (bloc de code complet)
- [ ] **Étape 4 : relancer.** Commande exacte. Attendu : SUCCÈS.
- [ ] **Étape 5 : vérifier la tâche.** Les `verify.commands`, une par ligne. Attendu : zéro erreur.
````

Les étapes de commit ne figurent pas dans le plan. Le plan se termine tâche par tâche sur une vérification ;
le commit se fait sur demande (`/kata-commit`). Le plan peut marquer des « points de lot » où il serait logique
de le proposer.

## Échecs de plan

Tout ce qui suit est un défaut, à corriger avant de montrer le plan :

- « TBD », « TODO », « à compléter », « implémenter plus tard » ;
- « ajouter la gestion d'erreurs », « valider les entrées », « gérer les cas limites » sans dire lesquels ;
- « écrire des tests pour ce qui précède » sans le code du test ;
- « comme la tâche N » : recopier, l'exécutant peut lire dans le désordre ;
- une étape qui dit quoi faire sans montrer comment ;
- un type, une fonction ou un champ utilisé mais défini dans aucune tâche ;
- une commande de vérification qui ne figure pas dans la politique.

## Auto-relecture

Une checklist que tu passes toi-même, pas une délégation.

1. **Couverture** : parcourir la spec exigence par exigence. Chaque exigence et chaque critère de réussite
   pointe vers une tâche. Ajouter la tâche manquante.
2. **Trous** : relire en cherchant les motifs de la liste ci-dessus.
3. **Cohérence des noms** : une fonction appelée `clearLayers()` en tâche 3 ne devient pas `clearFullLayers()` en
   tâche 7. Comparer chaque « Consomme » à un « Produit ».
4. **Commandes** : chaque commande d'une tâche existe-t-elle dans le dépôt ou la politique ?
5. **Points de vigilance** : chacun a-t-il son test ?
6. **Périmètre** : une tâche fait-elle plus que la spec ne demande ? La retirer.

Corriger sur place, sans nouvelle boucle.

## Porte et passage

Annoncer : « Plan écrit dans `<chemin>`. Relis-le : couvre-t-il ce que tu veux ? » Attendre la réponse. Un plan
non relu ne s'exécute pas.

Puis proposer le mode d'exécution, avec une recommandation d'une phrase tirée du plan (nombre de tâches,
dépendance entre interfaces, coût d'une erreur livrée) :

- `/kata-execute` : je déroule le plan ici, tâche par tâche, avec des arrêts humains ;
- `/kata-agents` : un agent par tâche, relecture entre les tâches ; pour un plan long ou aux tâches indépendantes
  (voir aussi `/kata-parallel`).

## Signaux d'alerte

| Pensée | Réalité |
|---|---|
| « Le dev comprendra ce que je veux dire » | Il n'a pas la conversation. Écris le code ou la commande. |
| « Je mets une étape de plus, ça fait sérieux » | Chaque étape inutile est du bruit. Retire ce que la spec ne demande pas. |
| « Les commandes habituelles feront l'affaire » | La seule source, c'est `verify.commands`. Les autres sont des suppositions. |
| « La spec est floue ici, je comble en silence » | Remonter la question à l'humain, ou corriger la spec avec son accord. |
| « Tâche similaire à la 3, je renvoie » | Recopier. Elle sera lue seule. |
| « Je relis plus tard » | La relecture est le moment où la tâche 7 contredit la tâche 3. Elle se fait maintenant. |

> Inspiré de superpowers (Jesse Vincent, MIT, v6.4.1) ; réécrit pour Kata.
