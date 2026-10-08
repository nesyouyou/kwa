# Standard d'écriture (Kwa)

| Objet | Format |
|---|---|
| Commit | `<type>(<scope>): <sujet à l'impératif, ≤ 72 car.>` — types : `feat` `fix` `chore` `refactor` `docs` `test` `perf` `ci` `revert` |
| Branche | `<type>/<slug-en-anglais>` |
| Titre de PR | même format que le commit |
| Corps de PR | **Contexte** · **Changements** · **Vérification** · **Risque / déploiement** |

- Messages de commit et de PR en français ; noms de branche et de scope en anglais.
- Un commit explique le *pourquoi* quand il n'est pas évident ; jamais un récit du *quoi*.
- Un commit ne mélange pas deux changements logiques (code et migration liée : oui ; refonte et correctif : non).
