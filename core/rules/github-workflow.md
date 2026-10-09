# Tout développement se trace sur GitHub, avec sa preuve (Kwa · issue-flow)

Chaque demande (correctif, fonctionnalité, retouche d'interface, même petite) suit le même workflow, et rien n'est
déclaré « fait » sans preuve. `/kwa-start-dev` le déroule ; `guard-write` et `guard-github` le tiennent.

1. **Issue d'abord** : le constat, la cause quand elle est connue, les décisions prises, des critères de réussite
   vérifiables (modèles dans `.github/ISSUE_TEMPLATE/`).
2. **Une branche par issue, dans son worktree** : `.claude/kwa/bin/kwa-start <fix|feat|chore|docs> <slug> "<titre>"`
   ouvre l'issue et crée `<type>/<n°>-<slug>`. Noms de branche en anglais, titres en français. Le garde-fou refuse
   d'écrire du code produit sur `main`.
3. **Une PR par issue** : le corps commence par `Closes #N` (le garde-fou refuse un `gh pr create` sans lien).
4. **Preuve** : tout ce qui se voit est capturé en vrai, après le changement (web : bureau et 375 px ; mobile :
   simulateur ; avant/après pour un correctif), publié sur l'issue avec
   `gh issue comment <n°> --attach 'avant.png#Avant' --attach 'apres.png#Après'`. Sans interface : la sortie qui le
   démontre (test rouge puis vert, requête et réponse, extrait de journal), en texte dans la PR.
5. **Fusion** : le garde-fou refuse `gh pr merge` si la PR n'est liée à aucune issue, ou si ni la PR ni ses issues
   ne portent de preuve. Pas de fusion sans le GO du demandeur.

Dans une issue ou une PR : du fonctionnel et du technique. Pas de nom de personne (un rôle), pas de secret, pas de
donnée client réelle, y compris dans les captures.
