- **Flux git : une branche par sujet, une PR par branche, `main` protégée.** Jamais de commit, de push ni de
  fusion locale directement sur `main`. Nom de branche : `<type>/<slug-en-anglais>` (`feat`, `fix`, `chore`, `docs`).
- **Une PR par sujet**, titre au format du standard d'écriture. Le corps dit : ce qui change, pourquoi, comment
  c'est vérifié (captures avant/après si l'interface bouge, bureau et 375 px).
- **Pousser la branche demande confirmation ; fusionner la PR n'est jamais fait sans demande explicite.** Si la
  fusion sur `main` déclenche un déploiement, le dire avant de fusionner.
- **Aucun commit sans demande.** Faire les modifications, résumer, attendre. Les petites retouches s'accumulent
  sur la même branche plutôt que d'ouvrir une PR par retouche.
