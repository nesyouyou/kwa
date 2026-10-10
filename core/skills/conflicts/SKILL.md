---
name: kwa-conflicts
description: Résoudre une fusion ou un rebase arrêté sur des conflits, morceau par morceau, en lisant l'intention de chaque côté avant de toucher au texte. À utiliser dès que git signale des conflits (marqueurs dans l'arbre, « CONFLIT » à la fusion ou au rebase, PR marquée en conflit), ou quand l'utilisateur dit « résous les conflits », « /kwa-conflicts ».
allowed-tools: Read Grep Glob Edit Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git show *) Bash(gh pr view *) Bash(gh pr list *)
---

# Résoudre des conflits de fusion

Un conflit n'est pas un problème de texte : deux personnes ont voulu deux choses. Choisir un bloc parce qu'il
« a l'air plus récent » fait disparaître sans bruit un changement voulu, et le résultat compile quand même.
Tu choisis entre deux intentions, pas entre deux blocs.

## Faire

1. **État des lieux.** `git status` : fusion ou rebase, quelle branche entre dans quelle autre, combien de fichiers
   en conflit. Formule en une phrase l'objectif de l'opération (« ramener main dans la branche du filtre »).
2. **Lire l'intention des deux côtés, avant le diff.** Pour chaque fichier en conflit :
   `git log --oneline --merge -- <fichier>`, puis le message de chaque commit concerné, la PR et l'issue liées
   (`gh pr list --search <sha> --state all`). Cite-les en résolvant : c'est la preuve que tu as lu.
3. **Mettre de côté les fichiers générés.** Un fichier produit par un outil (site généré, données de build,
   fichier de verrouillage, types générés) ne se fusionne pas à la main : prends l'une des deux versions, termine
   les autres conflits, puis **régénère** avec la commande du projet. La politique ou AGENTS.md la donne ; sinon,
   la demander.
4. **Résoudre morceau par morceau.**
   - Les deux intentions sont compatibles : garder les deux.
   - Elles s'excluent : garder celle qui sert l'objectif de l'opération et **nommer ce qui est abandonné**, avec
     sa raison, dans le compte rendu.
   - Ne rien inventer qui n'était sur aucune des deux branches pour « arranger » le conflit.
5. **Vérifier avant de conclure.** Les commandes `verify.commands` de la politique, plus les tests des fichiers
   touchés. Une fusion produit facilement du code qui satisfait les deux branches et ne passe les tests d'aucune.
6. **Terminer l'opération, sans publier.** `git add`, puis le commit de fusion ou `git rebase --continue` jusqu'au
   dernier commit du rebase, si l'utilisateur a demandé cette fusion. Sinon, laisser l'arbre résolu et le dire.
   Jamais de push dans cette skill : c'est `/kwa-ship`.

## Compte rendu

Pour chaque fichier : la résolution, les commits ou PR lus, ce qui a été gardé des deux côtés ou abandonné, puis
les vérifications lancées avec leur résultat. Un fichier généré se signale comme « régénéré par <commande> ».

## Rationalisations

| Pensée | Réalité |
|---|---|
| « Je prends leur version pour tout le fichier, c'est plus rapide » | Sur un fichier source, c'est supprimer le travail de l'autre côté. Réservé aux fichiers générés. |
| « Les marqueurs ont disparu, ça compile, c'est bon » | Compiler ne dit rien de l'intention. Les vérifications de la politique le disent. |
| « Je fusionne les deux en une version qui fait un peu des deux » | Un comportement qui n'existait sur aucune branche est un nouveau bug. Garder, ou abandonner en le disant. |
| « J'annule la fusion et on verra » | Abandonner (`--abort`) est une décision de l'utilisateur. Le proposer, ne pas le faire. |
| « Je résous tous les conflits de toutes les branches à la fin » | La session qui a écrit un changement connaît son intention : la fusion lui revient. |

## C'est réussi si

- Tu as cité des messages de commit ou des PR, pas seulement des morceaux de diff.
- Chaque morceau garde les deux comportements, ou nomme ce qui est abandonné et pourquoi.
- Rien n'apparaît qui n'était sur aucune des deux branches.
- Les vérifications sont passées avant le commit, pas après.

Si la fusion se termine proprement mais que le code se comporte mal : c'est un diagnostic, `/kwa-debug`.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit 49dd158) ; réécrit pour Kwa.
