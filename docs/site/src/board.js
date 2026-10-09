/* Données du circuit : colonnes, types de briques et les trois scénarios (étapes, briques, portes, refus).
   Lues par circuit.js via window.KwaBoard.data. Script classique, sans dépendance. */
(function () {
  'use strict';

  var COLS = ['Cadrer', 'Faire', 'Prouver', 'Livrer', 'Capitaliser'];
  var TYPES = { skill: 'Skill', hook: 'Hook', agent: 'Sous-agent', garde: 'Garde', humain: 'Vous' };
  var TYPE_HELP = {
    skill: 'une procédure que l’agent suit',
    hook: 'se lance tout seul à un moment du cycle',
    agent: 'un agent neuf pour une tâche',
    garde: 'refuse ou demande avant une action',
    humain: 'porte d’approbation humaine'
  };

  function B(type, name, d, when, detail) { return { type: type, name: name, d: d, when: when || '', detail: detail || d }; }

  /* Briques réutilisées (contenu repris de template.html) */
  var K = {
    router: B('hook', 'skills-router', 'Injecte la table « quand → skill », filtrée sur les skills installées.', 'SessionStart · startup, clear, compact', 'Court et calibré : une conversation simple n’appelle aucune skill. Les lignes dont la skill n’est pas installée sont retirées.'),
    brainstorm: B('skill', '/kwa-brainstorm', 'Explore le contexte, compare 2 ou 3 approches, écrit une spec courte.', 'Intention floue ou changement non trivial', 'Spec dans docs/specs/. Aucune ligne de code avant la porte suivante.'),
    interview: B('skill', '/kwa-interview', 'Interrogatoire sans relâche : une question à la fois, avec une recommandation.', 'Au besoin, depuis /kwa-brainstorm', 'Consigne les décisions durables (ADR, glossaire) sur accord.'),
    specOk: B('humain', 'Vous approuvez la spec', 'Porte d’approbation avant tout plan.', '', 'Sans accord, on ne passe pas à /kwa-plan.'),
    plan: B('skill', '/kwa-plan', 'Tâches de 2 à 5 minutes, fichiers exacts, tests d’abord, commandes de verify.commands.', 'Spec approuvée', 'Aucun « à définir ». Auto-relecture : couverture de la spec, cohérence des noms.'),
    startDev: B('skill', '/kwa-start-dev', 'Issue, branche dans un worktree, dépendances installées.', 'Demande qui modifie le produit', 'kwa-start crée l’issue puis le worktree à côté du dépôt. Jamais de travail sur main.'),
    write: B('garde', 'guard-write', 'Secrets en clair, .env, migrations appliquées, pas de code sur main.', 'PreToolUse · Edit, Write', 'Demande aussi confirmation avant de toucher à .claude/kwa/ ou settings.json.'),
    secrets: B('garde', 'guard-secrets', 'Refuse .env, clés SSH, jetons CLI, trousseau.', 'PreToolUse · Bash, Read, Grep', 'Analyse par segments de commande : bash -c, env, nice, .e\'\'nv, sauts de ligne sont couverts. .env.example reste lisible.'),
    impl: B('agent', 'Implémenteur (sonnet)', 'Un agent frais par tâche, modèle choisi selon la difficulté.', '/kwa-agents · Agent tool', 'haiku pour le mécanique, sonnet pour l’intégration, opus pour la conception. Il ne commite pas et remonte tout refus de garde en BLOCKED.'),
    format: B('hook', 'format-after-edit', 'Formate seulement les fichiers nouveaux, signale les autres.', 'PostToolUse · Edit, Write · module verify', 'Un formatage global appartient à un lot dédié, pas à chaque sauvegarde.'),
    conform: B('agent', 'Relecteur de conformité', 'Le code fait-il exactement ce que la tâche demande, ni plus ni moins ?', 'Après chaque tâche', 'Agent neuf, jamais l’implémenteur. Passe avant la qualité.'),
    quality: B('agent', 'Relecteur de qualité', 'Lisibilité, tests, sécurité, simplicité.', 'Quand la conformité est verte', 'Axe anti-sur-ingénierie inclus. Retours critiques renvoyés à l’implémenteur.'),
    verify: B('skill', '/kwa-verify', 'Aucune affirmation de succès sans la sortie fraîche d’une commande.', 'Avant de dire « fait »', 'Commandes de verify.commands, capture si interface, tests sautés nommés, bloc « non vérifié » honnête.'),
    review: B('agent', 'Relecteur de branche', 'Revue de toute la branche : correction, sécurité, régressions, tests manquants.', '/kwa-review · fin de plan', 'Sortie de boucle : zéro critique et zéro important ouverts, sinon remontée après 3 tours.'),
    stop: B('hook', 'verify-stop', 'Refuse de rendre la main sur du rouge (typecheck, lint).', 'Stop · opt-in KWA_STOP_VERIFY=1', 'Claude Code reprend la main après 8 blocages consécutifs : pas de boucle infinie.'),
    commitOk: B('humain', 'Vous décidez du commit', '/kwa-commit puis /kwa-ship, jamais sans votre demande.', '', 'Un commit par changement logique ; push de branche confirmé ; fusion = décision séparée.'),
    ship: B('skill', '/kwa-ship', 'Vérifie, résume ce qui part, demande confirmation.', 'Sur votre demande de publier', 'Branche ≠ main, état propre, vérifications lancées.'),
    git: B('garde', 'guard-git', 'Pas de commit ni de push sur main ; force refusé ; push de branche confirmé.', 'PreToolUse · Bash', 'KWA_ALLOW_MAIN=1 pour une exception assumée. Les push de branche demandent confirmation selon git.push_branch de la politique.'),
    github: B('garde', 'guard-github', '« Closes #N » à la création d’une PR ; issue et preuve avant fusion.', 'PreToolUse · Bash · module issue-flow', 'Lit la PR et ses issues via gh. Preuve = une image, ou une section « Preuve » réellement remplie.'),
    nudge: B('hook', 'memory-nudge', 'Demande l’entrée de journal et invite à capitaliser, une seule fois par session.', 'Stop · module memory', 'Seulement si 3 fichiers de code ou plus ont changé, ou si un signal fort a été capté (correction, « retiens : », refus de garde). Chaque demande est omise si elle est déjà satisfaite. Désactivable : KWA_MEMORY_NUDGE=0.'),
    learn: B('skill', '/kwa-learn', 'Range ce qui a été appris : docs, politique, mémoire de l’agent, base de connaissance.', 'Fin de session', 'Tableau de 7 lignes maximum, rien appliqué sans accord.')
  };

  function S(col, caption, bricks, extra) {
    var s = { col: col, caption: caption, bricks: bricks };
    if (extra) for (var k in extra) s[k] = extra[k];
    return s;
  }

  var SCENARIOS = [
    {
      id: 'feature', label: 'Fonctionnalité', card: { id: '#12', title: 'Filtre du portefeuille' },
      intro: 'Une idée encore floue devient une fonctionnalité relue, prouvée et publiée, avec deux portes où vous décidez.',
      steps: [
        S(0, 'Votre demande #12 arrive dans Cadrer. skills-router a injecté la table « quand → skill » au démarrage : l’agent choisit /kwa-brainstorm au lieu de coder. Pourquoi : une intention floue se clarifie avant toute ligne de code.', [K.router, K.brainstorm, K.interview]),
        S(0, 'La spec courte est écrite dans docs/specs/. La carte s’arrête à la porte « Vous » : sans votre accord, on ne passe pas à /kwa-plan. Pourquoi : valider l’intention coûte moins que la corriger après coup.', [K.specOk], { gate: true }),
        S(0, 'Spec approuvée : /kwa-plan la découpe en tâches de 2 à 5 minutes, avec les commandes de vérification exactes de la politique. Pourquoi : un plan sans « à définir » se vérifie.', [K.plan]),
        S(1, 'La carte passe dans Faire. /kwa-start-dev ouvre l’issue #12 et une branche dans un worktree ; guard-write veille à ce qu’aucun code produit ne s’écrive sur main. Pourquoi : le dépôt principal reste propre.', [K.startDev, K.write]),
        S(1, 'Un implémenteur (sonnet pour l’intégration) prend une seule tâche avec un contexte neuf ; format-after-edit ne formate que les fichiers nouveaux. Pourquoi : chaque tâche reste petite et isolée.', [K.impl, K.format]),
        S(1, 'L’implémenteur veut lire .env pour une valeur de configuration. guard-secrets refuse : la carte revient et il remonte le refus (BLOCKED) au lieu de le contourner. Pourquoi : un agent ne lit jamais un secret.', [K.secrets], { deny: { by: 'guard-secrets', msg: 'commande refusée : touche un fichier de secrets (.env)' } }),
        S(1, 'Chaque tâche est relue par des agents neufs : d’abord la conformité (ni plus ni moins que demandé), puis la qualité. Pourquoi : l’implémenteur ne se relit pas lui-même.', [K.conform, K.quality]),
        S(2, 'La carte passe dans Prouver. Aucune affirmation de succès sans la sortie fraîche d’une commande : typecheck, lint, tests, capture si l’interface a changé. Pourquoi : « ça marche » n’est pas une preuve.', [K.verify]),
        S(2, 'Un relecteur examine toute la branche ; verify-stop, s’il est activé, refuse de rendre la main sur du rouge. Sortie de boucle : zéro critique et zéro important ouverts.', [K.review, K.stop]),
        S(3, 'La carte arrive dans Livrer et attend votre demande : /kwa-commit puis /kwa-ship ne partent jamais sans vous. Pourquoi : publier est une décision humaine.', [K.commitOk], { gate: true }),
        S(3, 'Commit au format Conventional Commits, puis /kwa-ship : guard-git demande confirmation du push de branche, guard-github exige « Closes #12 » dans la PR. La fusion reste une décision séparée.', [K.ship, K.git, K.github]),
        S(4, 'Dans Capitaliser, memory-nudge propose, une seule fois par session, de ranger ce qui a coûté à apprendre ; /kwa-learn n’applique rien sans votre accord. Pourquoi : la prochaine session ne repaie pas la même leçon.', [K.nudge, K.learn], { done: true })
      ]
    },
    {
      id: 'bug', label: 'Bug', card: { id: '#13', title: 'Export CSV cassé' },
      intro: 'Un bug se règle par sa cause racine : le test rouge d’abord, la preuve par mutation ensuite.',
      steps: [
        S(0, 'Le ticket #13 arrive dans Cadrer. /kwa-debug interdit tout correctif avant la cause racine : reproduire, collecter les preuves, remonter la chaîne. Un sous-agent Explore, en lecture seule, cartographie le code si le périmètre est vaste.', [
          B('skill', '/kwa-debug', 'Aucune correction avant la cause racine.', 'Bug, test qui échoue, comportement inattendu', 'Reproduire, collecter les preuves, remonter la chaîne causale, une hypothèse à la fois.'),
          B('agent', 'Explore (lecture seule)', 'Cartographie large du code concerné.', 'Si le périmètre est vaste', 'Sous-agent Explore : ne peut rien écrire.')]),
        S(1, 'La cause est trouvée, la carte passe dans Faire. Le test de non-régression commence à s’écrire, mais sur main : guard-write refuse. Pourquoi : on n’écrit pas de code avant d’avoir une issue et une branche.', [K.write], { deny: { by: 'guard-write', msg: 'Pas de code sur main : ouvrir d’abord l’issue et sa branche (kwa-start-dev), puis travailler dans le worktree créé.' } }),
        S(1, 'Le refus est suivi : /kwa-start-dev ouvre l’issue et la branche dans un worktree. Pourquoi : le dépôt principal reste propre pendant tout le correctif.', [K.startDev]),
        S(1, 'Le test de non-régression est écrit d’abord et doit échouer pour la bonne raison (rouge). Pourquoi : un bug est d’abord un test.', [
          B('skill', '/kwa-tdd · test rouge', 'Le test de non-régression échoue pour la bonne raison.', 'Avant tout correctif', 'Cycle rouge, vert, refactor. Un bug est d’abord un test.')]),
        S(1, 'Le plus petit changement qui rend le test vert, sans rien ajouter autour ; format-after-edit ne touche que les fichiers nouveaux. Pourquoi : un petit correctif se relit et se défait facilement.', [
          B('skill', 'Correctif minimal', 'Le plus petit changement qui rend le test vert.', '/kwa-simple', 'Échelle de simplicité : ne pas écrire, réutiliser, configurer, ajouter, enfin coder.'), K.format]),
        S(2, 'Dans Prouver, on retire le correctif : le symptôme doit revenir. Puis /kwa-verify cite la sortie fraîche des vérifications. Pourquoi : montrer que le correctif agit, pas qu’il coïncide avec un test vert.', [
          B('skill', 'Preuve par mutation', 'On retire le correctif : le symptôme doit revenir.', '/kwa-debug · bug difficile', 'Prouve que le correctif agit, pas qu’il coïncide avec un test vert.'), K.verify]),
        S(3, 'La carte attend votre demande dans Livrer. guard-git refuse tout commit ou push sur main et demande confirmation pour une branche. Pourquoi : la publication reste une décision humaine.', [K.commitOk, K.git], { gate: true }),
        S(4, 'Le piège coûte cher à apprendre : memory-nudge invite à le capitaliser, et /kwa-learn le range dans docs/gotchas.md ou en règle de garde-fou, après votre accord.', [K.nudge, K.learn], { done: true })
      ]
    },
    {
      id: 'delivery', label: 'Livraison', card: { id: '#14', title: 'Déploiement recette' },
      intro: 'De la branche prête à la révision servie : chaque garde bloque ce qui ne doit pas partir.',
      steps: [
        S(3, 'Le ticket #14 est prêt et vous demandez de publier. /kwa-ship vérifie que la branche n’est pas main, que l’état est propre, lance les vérifications et résume ce qui part. Pourquoi : on ne publie pas à l’aveugle.', [K.ship]),
        S(3, 'Un push direct vers main est tenté : guard-git refuse et la carte revient. Pourquoi : tout passe par une branche de travail et une PR.', [K.git], { deny: { by: 'guard-git', msg: 'push direct vers main refusé : pousser la branche de travail et ouvrir une PR' } }),
        S(3, 'Le push de la branche, lui, est permis mais publie du code : guard-git demande votre confirmation. La carte attend à la porte « Vous ».', [K.git, B('humain', 'Vous confirmez le push', 'Le push de branche publie la branche : confirmation demandée.', '', 'Selon git.push_branch de la politique du projet, le push de branche demande confirmation.')], { gate: true }),
        S(3, 'La PR est ouverte sans « Closes #14 » : guard-github refuse. Pourquoi : une PR se rattache toujours à son issue.', [K.github], { deny: { by: 'guard-github', msg: 'Une PR se rattache à son issue : le corps doit porter « Closes #N ». Pas d’issue ? L’ouvrir d’abord (kwa-start-dev).' } }),
        S(3, 'Avec « Closes #14 » dans le corps, la PR est créée. Pourquoi : la fusion de la PR fermera l’issue, et la trace reste lisible.', [B('garde', 'guard-github', 'La PR doit porter « Closes #N ».', 'PreToolUse · gh pr create', 'Sinon refus avec la marche à suivre.')]),
        S(3, 'La fusion est une décision séparée : la carte s’arrête à la porte « Vous » jusqu’à votre GO. Kwa annonce si la fusion déclenche un déploiement.', [B('humain', 'Vous donnez le GO', 'La fusion est une décision séparée.', '', 'Kwa annonce si elle déclenche un déploiement.')], { gate: true }),
        S(3, 'Fusion tentée sans preuve : guard-github refuse. Il faut une image, ou une section « Preuve » réellement remplie, sur la PR ou son issue. Pourquoi : un changement non prouvé ne part pas.', [B('garde', 'guard-github', 'Fusion refusée sans issue liée ni preuve.', 'PreToolUse · gh pr merge', 'Preuve = image, ou section « Preuve » remplie.')], { deny: { by: 'guard-github', msg: 'Aucune preuve sur la PR ni sur ses issues (#14). Joindre les captures (gh issue comment <n°> --attach …) ou remplir la section « Preuve » pour un changement sans interface.' } }),
        S(3, '/kwa-deploy déroule le pré-vol point par point avec preuve. Le déploiement relève des règles bash.ask de la politique : guard-policy demande, et la carte attend votre accord.', [
          B('skill', '/kwa-deploy', 'Pré-vol point par point, avec preuve, depuis les environnements de la politique.', 'Sur votre demande de déployer', 'Un pré-vol non vérifiable est non coché : on n’avance pas.'),
          B('garde', 'guard-policy', 'Déploiement prod, scw direct, soumission EAS : demande.', 'PreToolUse · règles bash.ask', 'Définies par le projet dans sa politique.'),
          B('humain', 'Vous confirmez le déploiement', 'Le déploiement demande votre accord.', '', 'Les commandes soumises à bash.ask ne partent pas sans confirmation.')], { gate: true }),
        S(3, 'Une fois déployé, on vérifie la révision réellement servie : santé et parcours touché, avec capture. En production, cette étape est en lecture seule. Pourquoi : « déployé » ne veut pas dire « fonctionne ».', [
          B('skill', 'Vérification de la révision servie', 'Santé + le parcours réellement touché, avec capture.', '/kwa-deploy §4', 'En production : lecture seule.')]),
        S(4, 'Fin de session : /kwa-learn range ce qui a été appris (docs, politique, mémoire de l’agent, base de connaissance), en 7 lignes maximum et rien d’appliqué sans votre accord.', [K.learn], { done: true })
      ]
    }
  ];

  window.KwaBoard = { data: { COLS: COLS, TYPES: TYPES, SCENARIOS: SCENARIOS } };
})();
