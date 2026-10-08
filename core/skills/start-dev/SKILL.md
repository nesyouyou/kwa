---
name: kwa-start-dev
description: Démarrer puis livrer tout développement selon le circuit issue → branche dédiée dans un worktree → preuve → PR liée à son issue (« Closes »). À utiliser DÈS qu'une demande implique de modifier le produit (correctif, fonctionnalité, retouche d'interface, web, mobile ou API), avant d'écrire la moindre ligne de code, même pour un petit changement.
allowed-tools: Bash(gh *) Bash(git *) Bash(python3 .claude/kwa/bin/kwa-start *) Bash(pnpm *)
---

# Démarrer et livrer un développement

Le circuit est décrit dans `.claude/rules/kwa-github-workflow.md`. Cette skill le déroule. Deux garde-fous le
tiennent : `guard-write` refuse d'écrire du code produit sur `main`, `guard-github` refuse une PR sans `Closes #N`
et une fusion sans preuve. Les commandes de vérification, d'installation et les dossiers de code viennent de
`.claude/kwa.policy.json` (`verify.commands`, `start.install`, `write.no_code_on_main`).

## Avec les skills de méthode Kwa (module craft)

Cette skill porte ce qui est propre au circuit : issue, branche, preuve, PR. Pour le travail lui-même :

| Étape | Skill |
|---|---|
| Cadrer une fonctionnalité non triviale | `/kwa-brainstorm`, puis `/kwa-plan` |
| Cadrer un bug | `/kwa-debug` |
| Développer | `/kwa-tdd` ; `/kwa-execute` ou `/kwa-agents` si un plan existe |
| Avant de dire « fait » | `/kwa-verify` |
| Relire avant la PR | `/kwa-review` |

Le worktree est celui de `kwa-start`, à côté du dépôt. Seule l'option « pousser la branche et ouvrir une PR »
est valable : jamais de fusion locale dans `main`.

## 1. Cadrer

- Reformuler la demande en une phrase ; s'il y a plusieurs lectures, les exposer avant de continuer.
- Chercher une issue existante : `gh issue list --search "<mots clés>" --state open`. Si elle existe, la reprendre.
- Bug : établir la cause avant de rédiger l'issue (lire le code, reproduire).

## 2. Ouvrir l'issue et la branche

Corps de l'issue dans un fichier temporaire (modèles : `.github/ISSUE_TEMPLATE/`) : constat ou besoin, cause si
connue, décisions, critères de réussite vérifiables. Puis :

```bash
python3 .claude/kwa/bin/kwa-start <fix|feat|chore|docs> <slug> "<titre>" --body-file <fichier>
# ou, pour une issue existante :
python3 .claude/kwa/bin/kwa-start <type> <slug> "<titre>" --issue <n°>
```

`<slug>` : anglais, kebab-case. Titre de l'issue : français. **L'issue est ouverte automatiquement** à partir de la demande, sans la redemander, sauf si la politique a `flow.auto_issue: false` ou si tu passes `--no-issue` : on a alors juste la branche `<type>/<slug>`. Le script ouvre l'issue, crée `<type>/<n°>-<slug>` dans
un worktree à côté du dépôt, relie les fichiers locaux de `start.link` (un fichier d'environnement ignoré par git : lien symbolique vers celui du dépôt principal, jamais une copie) et lance `start.install`. `--base <branche>` change la branche de départ. **Tout le travail se fait dans ce worktree.**

## 3. Développer

- Tests d'abord (`/kwa-tdd`) : le test échoue, puis passe.
- Changements chirurgicaux, dans le style du code existant.
- Avant de livrer : les `verify.commands` de la politique, plus les tests concernés. Citer les résultats.

## 4. Prouver

- **Visible (web, mobile, e-mail)** : captures réelles après le changement (web : bureau et 375 px ; mobile :
  simulateur ; avant/après pour un correctif ; données de démonstration uniquement).

  ```bash
  gh issue comment <n°> --body "<ce qui est montré, comment c'est vérifié>" --attach 'capture.png#Ce que montre la capture'
  ```

  Envoyer aussi les captures à l'utilisateur dans la conversation : une preuve qu'il ne voit pas ne compte pas.
- **Sans interface** : la sortie qui le démontre (test rouge puis vert, requête et réponse, journal), dans la
  section « Preuve » de la PR.

## 5. Ouvrir la PR

Corps selon `.github/pull_request_template.md`, première ligne `Closes #<n°>`. Pousser la branche (confirmation
demandée par le garde-fou), puis :

```bash
gh pr create --base <base> --head <branche> --title "<type>(<portée>): <titre>" --body-file <fichier>
```

**Ne pas fusionner sans le GO du demandeur** ; dire si la fusion déclenche un déploiement. Une fois la PR fusionnée,
retirer le worktree (`git worktree remove <chemin>`). Pour capitaliser ce qui a été appris : `/kwa-learn`.
