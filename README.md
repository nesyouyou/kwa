# Kwa

**Site : https://nesyouyou.github.io/kwa/** (documentation illustrée et trois parcours de formation)

Un socle de harness pour agents de code : mêmes règles, mêmes garde-fous, mêmes skills, partout.
Kwa se lit **K**it · **W**orkflow · **A**gents (le K est aussi *Knowledge* : la connaissance qui s'enrichit) : un kit de process de développement pour travailler avec des agents de code.

## Pourquoi ce dépôt

Kwa est avant tout un **support pédagogique**. Il montre, avec de vrais fichiers qui tournent, comment encadrer un agent
de code : règles, garde-fous, skills, mémoire, workflow. Chaque pièce est lisible, testée, et expliquée sur le
site de documentation et dans trois parcours de formation (culture de l'IA générative, context engineering, harness).

- **En français.** Presque tout ce qui existe sur le sujet est en anglais. Les skills, les règles, la documentation et les
  parcours sont ici en français, pour les développeuses et les développeurs que l'anglais freine.
- **Pour partager des bonnes pratiques.** Ce qui est ici vient de l'usage et d'idées reprises à d'autres projets, toujours
  créditées. Si cela sert à d'autres, tant mieux ; les retours et les corrections sont bienvenus.
- **Sans prétendre à plus.** Les garde-fous sont des filets contre la bévue, pas une frontière de sécurité. Les
  documentations officielles des outils font foi. Les parcours n'ont pas encore été éprouvés avec un groupe.

**Parcours d'apprentissage** : `docs/site/parcours.html`, trois parcours qui s'enchaînent. 1) Culture IA générative (modèle, jetons et probabilités, fenêtre de contexte, agent, hallucinations, prompt engineering, risques). 2) Context engineering (session, AGENTS.md et CLAUDE.md, règles, skills, sous-agents, MCP avec Context7 et Playwright, permissions). 3) Harness (de l'histoire du processus de développement à Kwa, avec dix étapes sur un dépôt jetable dont les sorties viennent de l'exécution réelle, et le flux complet d'un développeur aujourd'hui).

**Documentation illustrée** : `docs/site/index.html` (présentation, arborescence, démarrage) et une page par sujet
(carte des skills, workflow d'une demande, terminal, skills, gardes en action, mémoire, méthode, remplacement de
l'existant, limites, crédits), avec une feuille de style propre (polices dans
`docs/site/style/`, avec leur licence). Régénérer avec `python3 docs/site/build.py` : les exemples sont
calculés en exécutant les gardes.

```bash
bin/kwa detect    <projet>                  # stack, modules proposés, politique déduite ; n'écrit rien
bin/kwa install   <projet> --dry-run        # montre ce qui changerait ; n'écrit rien
bin/kwa install   <projet> [--with client-handover] [--codex]
bin/kwa doctor    <projet>                  # conformité, doublons avec l'outillage existant du projet
bin/kwa status    <projet>                  # version, modules, dérive locale
bin/kwa recommend <projet>                  # skills tierces utiles pour la stack (rien n'est installé)
bash tests/run-safety.sh                     # suite hors-ligne
```

## Noyau + modules + politique

| Module | Apporte |
|---|---|
| `core` | gardes secrets / git / suppression / écriture / politique ; règles ; `/kwa-commit`, `/kwa-ship` |
| `craft` | méthode : `/kwa-brainstorm`, `plan`, `execute`, `agents`, `parallel`, `tdd`, `debug`, `verify`, `review`, `review-feedback` + routage des skills au démarrage de session (remplace superpowers) |
| `memory` | journal des sessions et reprise au démarrage, notes et signaux (corrections, « retiens : », refus de garde), invitation unique en fin de session, `/kwa-learn` (docs, politique, skill de projet, mémoire agent, base de connaissance) |
| `issue-flow` | workflow issue → worktree → preuve → PR « Closes #N » → fusion gardée ; `/kwa-start-dev`, gabarits GitHub |
| `verify` | formatage des fichiers nouveaux ; garde Stop opt-in (`KWA_STOP_VERIFY=1`) |
| `deploy` | `/kwa-deploy` : pré-vol, déploiement, vérification, pilotés par `environments` |
| `client-handover` | règle des 4 tests, `kwa-hygiene`, exceptions datées, job CI (jamais déduit : sur demande) |
| `stack-prisma` | migrations append-only, pas de reset / db push |
| `stack-expo` | `/kwa-testflight`, soumission EAS confirmée |
| `stack-scaleway` | déploiement direct confirmé |

Le spécifique d'un projet vit dans `.claude/kwa.policy.json` (créé une fois à partir de la détection, jamais écrasé) :
`bash.deny/ask`, `write.deny`, `write.no_code_on_main`, `verify.commands`, `start.install`, `environments`, `mobile`,
`hygiene`, `memory`. Exemple complet (monorepo web + API + mobile Expo) : `examples/expo-monorepo.policy.json`.

## Garanties

- `AGENTS.md` : seul le bloc `<!-- kwa:begin … -->` est géré, le reste est intact (testé dans `tests/test_agents_md_bytes.py` : fins de ligne CRLF, absence de retour final, espaces en fin de ligne, saut de page, BOM, accents).
  `CLAUDE.md` devient un pointeur `@AGENTS.md`, sans jamais écraser un fichier qui porte ses propres règles.
- `settings.json` : fusion sans doublon, sauvegarde, écriture atomique, JSON invalide laissé intact.
- Retouche locale d'un fichier géré : sauvegardée avant d'être écrasée. Gabarits « seed » : copiés une fois.
- Aucune action git. Les notes locales et sauvegardes sont exclues via `.git/info/exclude`.
- Les gardes sont des filets contre la bévue, pas une frontière de sécurité ; leurs erreurs internes demandent à
  l'humain. Pour une vraie barrière : protection de branche GitHub + `permissions.deny`.

## Remplacer un outillage maison

`tests/test_policy_example.py` rejoue contre Kwa des cas représentatifs d'un harnais de garde-fous réel (reset de
base, force-push, cibles de production, workflow issue → PR → preuve, migrations, heredocs) avec la politique d'exemple.
`kwa doctor` signale, dans un projet existant, les hooks et skills maison qui font doublon avec Kwa.

## Origine

Kwa assemble des idées de super-board, superpowers, des skills de Matt Pocock et de ponytail (tous MIT), réécrites
et testées : voir `THIRD_PARTY_NOTICES.md`, `credits.json` et `licenses/`. Aucun fichier copié.

## Licence

MIT, voir `LICENSE`. Les idées reprises d'autres projets (MIT également) sont créditées dans `THIRD_PARTY_NOTICES.md`. Les polices Geist et Geist Mono, vendorisées dans `docs/site/style/`, gardent leur licence (SIL OFL), dans `docs/site/style/assets/licenses/`.
