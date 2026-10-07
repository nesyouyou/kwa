# Discipline git (Kata)

1. Avant de modifier du code : être sur une branche de travail, jamais sur `main`.
2. Commit seulement sur demande (« on commit »). Un commit = un changement logique ; utiliser `/kata-commit`.
3. Publier seulement sur demande (« on pousse », « ouvre la PR »). Utiliser `/kata-ship`.
4. Ne jamais forcer un push, ne jamais réécrire l'historique partagé, ne jamais contourner un hook
   (`--no-verify`, édition de `.claude/kata/`). Si un garde-fou bloque, le dire et demander.
5. Fusion d'une PR : demande explicite uniquement, et annoncer si elle déclenche un déploiement.
6. « Fait » veut dire vérifié : citer la commande lancée et son résultat.
