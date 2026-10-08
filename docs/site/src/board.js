/* KwaBoard — « Une demande, de bout en bout ».
   Tableau animé : des tickets glissent de colonne en colonne et, à chaque déplacement,
   les briques Kwa qui se déclenchent apparaissent l'une après l'autre.
   Script classique, sans dépendance : window.KwaBoard.mount(rootEl). */
(function () {
  'use strict';

  var COLS = ['Cadrer', 'Faire', 'Prouver', 'Livrer', 'Capitaliser'];
  var TYPES = { skill: 'Skill', hook: 'Hook', agent: 'Sous-agent', garde: 'Garde', humain: 'Toi' };
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
    specOk: B('humain', 'Tu approuves la spec', 'Porte d’approbation avant tout plan.', '', 'Sans accord, on ne passe pas à /kwa-plan.'),
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
    commitOk: B('humain', 'Tu décides du commit', '/kwa-commit puis /kwa-ship, jamais sans ta demande.', '', 'Un commit par changement logique ; push de branche confirmé ; fusion = décision séparée.'),
    ship: B('skill', '/kwa-ship', 'Vérifie, résume ce qui part, demande confirmation.', 'Sur ta demande de publier', 'Branche ≠ main, état propre, vérifications lancées.'),
    git: B('garde', 'guard-git', 'Pas de commit ni de push sur main ; force refusé ; push de branche confirmé.', 'PreToolUse · Bash', 'KWA_ALLOW_MAIN=1 pour une exception assumée. Les push de branche demandent confirmation selon git.push_branch de la politique.'),
    github: B('garde', 'guard-github', '« Closes #N » à la création d’une PR ; issue et preuve avant fusion.', 'PreToolUse · Bash · module issue-flow', 'Lit la PR et ses issues via gh. Preuve = une image, ou une section « Preuve » réellement remplie.'),
    nudge: B('hook', 'memory-nudge', 'Une invitation à capitaliser, une seule par session.', 'Stop · module memory', 'Seulement si 3 fichiers de code ou plus ont changé et qu’aucune note n’a été captée. Désactivable : KWA_MEMORY_NUDGE=0.'),
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
      intro: 'Une idée encore floue devient une fonctionnalité relue, prouvée et publiée, avec deux portes où tu décides.',
      steps: [
        S(0, 'Ta demande #12 arrive dans Cadrer. skills-router a injecté la table « quand → skill » au démarrage : l’agent choisit /kwa-brainstorm au lieu de coder. Pourquoi : une intention floue se clarifie avant toute ligne de code.', [K.router, K.brainstorm, K.interview]),
        S(0, 'La spec courte est écrite dans docs/specs/. La carte s’arrête à la porte « Toi » : sans ton accord, on ne passe pas à /kwa-plan. Pourquoi : valider l’intention coûte moins que la corriger après coup.', [K.specOk], { gate: true }),
        S(0, 'Spec approuvée : /kwa-plan la découpe en tâches de 2 à 5 minutes, avec les commandes de vérification exactes de la politique. Pourquoi : un plan sans « à définir » se vérifie.', [K.plan]),
        S(1, 'La carte passe dans Faire. /kwa-start-dev ouvre l’issue #12 et une branche dans un worktree ; guard-write veille à ce qu’aucun code produit ne s’écrive sur main. Pourquoi : le dépôt principal reste propre.', [K.startDev, K.write]),
        S(1, 'Un implémenteur (sonnet pour l’intégration) prend une seule tâche avec un contexte neuf ; format-after-edit ne formate que les fichiers nouveaux. Pourquoi : chaque tâche reste petite et isolée.', [K.impl, K.format]),
        S(1, 'L’implémenteur veut lire .env pour une valeur de configuration. guard-secrets refuse : la carte revient et il remonte le refus (BLOCKED) au lieu de le contourner. Pourquoi : un agent ne lit jamais un secret.', [K.secrets], { deny: { by: 'guard-secrets', msg: 'commande refusée : touche un fichier de secrets (.env)' } }),
        S(1, 'Chaque tâche est relue par des agents neufs : d’abord la conformité (ni plus ni moins que demandé), puis la qualité. Pourquoi : l’implémenteur ne se relit pas lui-même.', [K.conform, K.quality]),
        S(2, 'La carte passe dans Prouver. Aucune affirmation de succès sans la sortie fraîche d’une commande : typecheck, lint, tests, capture si l’interface a changé. Pourquoi : « ça marche » n’est pas une preuve.', [K.verify]),
        S(2, 'Un relecteur examine toute la branche ; verify-stop, s’il est activé, refuse de rendre la main sur du rouge. Sortie de boucle : zéro critique et zéro important ouverts.', [K.review, K.stop]),
        S(3, 'La carte arrive dans Livrer et attend ta demande : /kwa-commit puis /kwa-ship ne partent jamais sans toi. Pourquoi : publier est une décision humaine.', [K.commitOk], { gate: true }),
        S(3, 'Commit au format Conventional Commits, puis /kwa-ship : guard-git demande confirmation du push de branche, guard-github exige « Closes #12 » dans la PR. La fusion reste une décision séparée.', [K.ship, K.git, K.github]),
        S(4, 'Dans Capitaliser, memory-nudge propose, une seule fois par session, de ranger ce qui a coûté à apprendre ; /kwa-learn n’applique rien sans ton accord. Pourquoi : la prochaine session ne repaie pas la même leçon.', [K.nudge, K.learn], { done: true })
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
        S(3, 'La carte attend ta demande dans Livrer. guard-git refuse tout commit ou push sur main et demande confirmation pour une branche. Pourquoi : la publication reste une décision humaine.', [K.commitOk, K.git], { gate: true }),
        S(4, 'Le piège coûte cher à apprendre : memory-nudge invite à le capitaliser, et /kwa-learn le range dans docs/gotchas.md ou en règle de garde-fou, après ton accord.', [K.nudge, K.learn], { done: true })
      ]
    },
    {
      id: 'delivery', label: 'Livraison', card: { id: '#14', title: 'Déploiement recette' },
      intro: 'De la branche prête à la révision servie : chaque garde bloque ce qui ne doit pas partir.',
      steps: [
        S(3, 'Le ticket #14 est prêt et tu demandes de publier. /kwa-ship vérifie que la branche n’est pas main, que l’état est propre, lance les vérifications et résume ce qui part. Pourquoi : on ne publie pas à l’aveugle.', [K.ship]),
        S(3, 'Un push direct vers main est tenté : guard-git refuse et la carte revient. Pourquoi : tout passe par une branche de travail et une PR.', [K.git], { deny: { by: 'guard-git', msg: 'push direct vers main refusé : pousser la branche de travail et ouvrir une PR' } }),
        S(3, 'Le push de la branche, lui, est permis mais publie du code : guard-git demande ta confirmation. La carte attend à la porte « Toi ».', [K.git, B('humain', 'Tu confirmes le push', 'Le push de branche publie la branche : confirmation demandée.', '', 'Selon git.push_branch de la politique du projet, le push de branche demande confirmation.')], { gate: true }),
        S(3, 'La PR est ouverte sans « Closes #14 » : guard-github refuse. Pourquoi : une PR se rattache toujours à son issue.', [K.github], { deny: { by: 'guard-github', msg: 'Une PR se rattache à son issue : le corps doit porter « Closes #N ». Pas d’issue ? L’ouvrir d’abord (kwa-start-dev).' } }),
        S(3, 'Avec « Closes #14 » dans le corps, la PR est créée. Pourquoi : la fusion de la PR fermera l’issue, et la trace reste lisible.', [B('garde', 'guard-github', 'La PR doit porter « Closes #N ».', 'PreToolUse · gh pr create', 'Sinon refus avec la marche à suivre.')]),
        S(3, 'La fusion est une décision séparée : la carte s’arrête à la porte « Toi » jusqu’à ton GO. Kwa annonce si la fusion déclenche un déploiement.', [B('humain', 'Tu donnes le GO', 'La fusion est une décision séparée.', '', 'Kwa annonce si elle déclenche un déploiement.')], { gate: true }),
        S(3, 'Fusion tentée sans preuve : guard-github refuse. Il faut une image, ou une section « Preuve » réellement remplie, sur la PR ou son issue. Pourquoi : un changement non prouvé ne part pas.', [B('garde', 'guard-github', 'Fusion refusée sans issue liée ni preuve.', 'PreToolUse · gh pr merge', 'Preuve = image, ou section « Preuve » remplie.')], { deny: { by: 'guard-github', msg: 'Aucune preuve sur la PR ni sur ses issues (#14). Joindre les captures (gh issue comment <n°> --attach …) ou remplir la section « Preuve » pour un changement sans interface.' } }),
        S(3, '/kwa-deploy déroule le pré-vol point par point avec preuve. Le déploiement relève des règles bash.ask de la politique : guard-policy demande, et la carte attend ton accord.', [
          B('skill', '/kwa-deploy', 'Pré-vol point par point, avec preuve, depuis les environnements de la politique.', 'Sur ta demande de déployer', 'Un pré-vol non vérifiable est non coché : on n’avance pas.'),
          B('garde', 'guard-policy', 'Déploiement prod, scw direct, soumission EAS : demande.', 'PreToolUse · règles bash.ask', 'Définies par le projet dans sa politique.'),
          B('humain', 'Tu confirmes le déploiement', 'Le déploiement demande ton accord.', '', 'Les commandes soumises à bash.ask ne partent pas sans confirmation.')], { gate: true }),
        S(3, 'Une fois déployé, on vérifie la révision réellement servie : santé et parcours touché, avec capture. En production, cette étape est en lecture seule. Pourquoi : « déployé » ne veut pas dire « fonctionne ».', [
          B('skill', 'Vérification de la révision servie', 'Santé + le parcours réellement touché, avec capture.', '/kwa-deploy §4', 'En production : lecture seule.')]),
        S(4, 'Fin de session : /kwa-learn range ce qui a été appris (docs, politique, mémoire de l’agent, base de connaissance), en 7 lignes maximum et rien d’appliqué sans ton accord.', [K.learn], { done: true })
      ]
    }
  ];

  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'text') e.textContent = attrs[k];
      else if (attrs[k] === false || attrs[k] == null) continue;
      else e.setAttribute(k, attrs[k]);
    }
    if (kids) kids.forEach(function (c) { if (c) e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return e;
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }

  var uid = 0;

  function mount(root) {
    if (!root || root.__kwaBoard) return root && root.__kwaBoard;
    var uidn = ++uid;
    var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
    var st = { sc: 0, i: 0, playing: false, speed: 1, timers: [], approved: false, visible: true, selBrick: -1, cardCell: null, started: false };
    var els = {};

    function reduced() { return !!mq.matches; }

    root.classList.add('kb');
    root.textContent = '';

    /* ---------- squelette ---------- */
    els.tabs = h('div', { class: 'kb-tabs', role: 'group', 'aria-label': 'Scénario' });
    els.intro = h('p', { class: 'kb-intro' });
    els.btnPlay = h('button', { class: 'kb-btn kb-btn--primary kb-play', type: 'button' });
    els.btnPrev = h('button', { class: 'kb-btn', type: 'button', 'aria-label': 'Étape précédente' }, ['Précédent']);
    els.btnNext = h('button', { class: 'kb-btn', type: 'button', 'aria-label': 'Étape suivante' }, ['Suivant']);
    els.btnSpeed = h('button', { class: 'kb-btn kb-speed', type: 'button' });
    els.btnReplay = h('button', { class: 'kb-btn', type: 'button', 'aria-label': 'Rejouer le scénario depuis le début' }, ['Rejouer']);
    els.count = h('p', { class: 'kb-count' });
    els.controls = h('div', { class: 'kb-controls', role: 'group', 'aria-label': 'Contrôles de lecture' }, [els.btnPlay, els.btnPrev, els.btnNext, els.btnSpeed, els.btnReplay, els.count]);
    els.progress = h('div', { class: 'kb-progress', 'aria-hidden': 'true' });
    els.board = h('div', { class: 'kb-board' });
    els.wrap = h('div', { class: 'kb-boardwrap', tabindex: '0', role: 'group', 'aria-label': 'Tableau des tickets : colonnes Cadrer, Faire, Prouver, Livrer, Capitaliser' }, [els.board]);

    els.eyebrow = h('p', { class: 'kb-eyebrow', text: 'Ce qui se déclenche' });
    els.stepno = h('span', { class: 'kb-eyebrow-n' });
    els.statusLive = h('div', { class: 'kb-status', 'aria-live': 'polite', 'aria-atomic': 'true' });
    els.gatebar = h('div', { class: 'kb-gatebar', hidden: 'hidden' });
    els.bricks = h('div', { class: 'kb-bricks', role: 'group', 'aria-label': 'Briques déclenchées' });
    els.detail = h('div', { class: 'kb-detail' });
    els.legend = h('ul', { class: 'kb-legend', 'aria-label': 'Légende des briques' });
    Object.keys(TYPES).forEach(function (t) {
      els.legend.appendChild(h('li', null, [h('i', { class: 'kb-sw kb-sw--' + t, 'aria-hidden': 'true' }), h('span', null, [h('b', { text: TYPES[t] }), ' ' + TYPE_HELP[t]])]));
    });
    els.banner = h('div', { class: 'kb-banner' }, [
      h('div', { class: 'kb-banner-head' }, [els.eyebrow, els.stepno]),
      els.statusLive, els.gatebar, els.bricks, els.detail, els.legend
    ]);
    root.appendChild(els.tabs);
    root.appendChild(els.intro);
    root.appendChild(els.controls);
    root.appendChild(els.progress);
    root.appendChild(els.wrap);
    root.appendChild(els.banner);

    SCENARIOS.forEach(function (sc, idx) {
      var b = h('button', { class: 'kb-tab', type: 'button', 'aria-pressed': idx === 0 ? 'true' : 'false' }, [h('span', { class: 'kb-tab-l', text: sc.label }), h('span', { class: 'kb-tab-n', text: sc.card.id })]);
      b.addEventListener('click', function () { setScenario(idx, true); });
      els.tabs.appendChild(b);
    });

    /* ---------- minuterie ---------- */
    function clearTimers() { st.timers.forEach(clearTimeout); st.timers = []; }
    function later(fn, ms) { st.timers.push(setTimeout(fn, ms)); }
    function cur() { return SCENARIOS[st.sc]; }
    function step() { return cur().steps[st.i]; }
    function brickBase(n) { return 350 + n * 450; }

    /* ---------- construction d'un scénario ---------- */
    function buildBoard() {
      var sc = cur();
      els.board.textContent = '';
      els.cols = []; els.bodies = []; els.gates = [];
      COLS.forEach(function (name, c) {
        var stt = h('span', { class: 'kb-col-st' });
        var body = h('div', { class: 'kb-body' });
        var gate = h('div', { class: 'kb-gate' }, [h('span', { class: 'kb-gate-l', text: 'Toi · porte' })]);
        var col = h('section', { class: 'kb-col', 'aria-label': name }, [
          h('div', { class: 'kb-col-h' }, [h('h3', null, [h('span', { class: 'kb-num', text: pad(c + 1) }), name]), stt]),
          body, gate
        ]);
        col.__st = stt;
        els.board.appendChild(col);
        els.cols.push(col); els.bodies.push(body); els.gates.push(gate);
      });
      els.cardSt = h('span', { class: 'kb-card-st' });
      els.card = h('article', { class: 'kb-card', 'aria-label': 'Ticket ' + sc.card.id + ' ' + sc.card.title }, [
        h('span', { class: 'kb-card-id', text: sc.card.id }),
        h('b', { class: 'kb-card-t', text: sc.card.title }),
        els.cardSt
      ]);
      st.cardCell = null;
      els.progress.textContent = '';
      sc.steps.forEach(function () { els.progress.appendChild(h('i')); });
    }

    function placeCard(animate) {
      var s = step();
      var cell = s.gate ? els.gates[s.col] : els.bodies[s.col];
      var wrap = els.wrap, wr = wrap.getBoundingClientRect();
      var first = null;
      if (animate && st.cardCell && els.card.parentNode && !reduced()) {
        var r = els.card.getBoundingClientRect();
        first = { x: r.left - wr.left + wrap.scrollLeft, y: r.top - wr.top + wrap.scrollTop };
      }
      if (st.cardCell !== cell) {
        cell.appendChild(els.card);
        st.cardCell = cell;
        if (first) {
          var l = els.card.getBoundingClientRect();
          var dx = first.x - (l.left - wr.left + wrap.scrollLeft), dy = first.y - (l.top - wr.top + wrap.scrollTop);
          els.card.style.transition = 'none';
          els.card.style.translate = dx + 'px ' + dy + 'px';
          void els.card.offsetWidth;
          els.card.style.transition = '';
          els.card.style.translate = '0px 0px';
        } else {
          els.card.style.transition = 'none';
          els.card.style.translate = '0px 0px';
          void els.card.offsetWidth;
          els.card.style.transition = '';
        }
      }
      // colonnes : état en toutes lettres + mise en valeur
      els.cols.forEach(function (col, c) {
        col.__st.textContent = c < s.col ? 'passé' : (c === s.col ? (s.done && c === 4 ? 'terminé' : 'ici') : 'à venir');
        col.classList.toggle('kb-col--on', c === s.col);
        els.gates[c].classList.toggle('kb-gate--on', !!s.gate && c === s.col);
      });
      scrollToCol(s.col, animate);
    }

    function scrollToCol(c, animate) {
      var w = els.wrap;
      if (w.scrollWidth <= w.clientWidth + 2) return;
      var col = els.cols[c];
      var left = col.offsetLeft - 12;
      try { w.scrollTo({ left: left, behavior: animate && !reduced() ? 'smooth' : 'auto' }); } catch (e) { w.scrollLeft = left; }
    }

    function cardState() {
      var s = step();
      if (s.deny) return 'refusé par ' + s.deny.by;
      if (s.gate) return st.approved ? 'accord donné' : 'attend ton accord';
      if (s.done) return 'terminé';
      return 'en cours';
    }

    function renderStatus() {
      var s = step(), n = cur().steps.length;
      els.stepno.textContent = 'Étape ' + (st.i + 1) + ' / ' + n;
      els.count.textContent = 'Étape ' + (st.i + 1) + ' sur ' + n;
      els.statusLive.textContent = '';
      els.statusLive.appendChild(h('p', { class: 'kb-caption', text: s.caption }));
      if (s.deny) {
        els.statusLive.appendChild(h('div', { class: 'kb-deny' }, [
          h('span', { class: 'kb-deny-t', text: 'Refusé · ' + s.deny.by }),
          h('p', { class: 'kb-deny-m', text: s.deny.msg })
        ]));
      }
      if (s.gate && st.approved) {
        els.statusLive.appendChild(h('p', { class: 'kb-approved', text: st.approvedBy === 'auto' ? 'Approuvé automatiquement (lecture automatique).' : 'Approuvé par toi.' }));
      }
      els.card.classList.toggle('kb-card--deny', !!s.deny);
      els.card.classList.toggle('kb-card--wait', !!s.gate && !st.approved);
      els.cardSt.textContent = cardState();
      renderGate();
      [].forEach.call(els.progress.children, function (seg, k) { seg.className = k < st.i ? 'is-done' : (k === st.i ? 'is-cur' : ''); });
      els.btnPrev.disabled = st.i === 0;
      els.btnNext.disabled = st.i === cur().steps.length - 1;
    }

    function renderGate() {
      var s = step();
      els.gatebar.textContent = '';
      if (s.gate && !st.approved) {
        els.gatebar.hidden = false;
        var auto = st.playing && !reduced();
        var bar = null;
        if (auto) {
          bar = h('span', { class: 'kb-wait', 'aria-hidden': 'true' }, [h('i')]);
          bar.firstChild.style.animationDelay = (brickBase(s.bricks.length) / st.speed) + 'ms';
          bar.firstChild.style.animationDuration = (2400 / st.speed) + 'ms';
        }
        var btn = h('button', { class: 'kb-btn kb-btn--primary kb-approve', type: 'button' }, ['Approuver']);
        btn.addEventListener('click', function () { approve('user'); });
        els.gatebar.appendChild(h('p', { class: 'kb-gate-t', text: auto ? 'La carte attend à la porte « Toi » : approbation automatique dans un instant.' : 'La carte attend à la porte « Toi » : approuve pour continuer.' }));
        els.gatebar.appendChild(btn);
        if (bar) els.gatebar.appendChild(bar);
      } else {
        els.gatebar.hidden = true;
      }
    }

    function renderBricks() {
      var s = step();
      els.bricks.textContent = '';
      st.selBrick = -1;
      s.bricks.forEach(function (br, k) {
        var b = h('button', { class: 'kb-brick kb-brick--' + br.type, type: 'button', 'aria-pressed': 'false', 'aria-label': TYPES[br.type] + ' : ' + br.name + '. Afficher le détail.' }, [
          h('span', { class: 'kb-ty', text: pad(k + 1) + ' · ' + TYPES[br.type] }),
          h('b', { text: br.name }),
          h('span', { class: 'kb-d', text: br.d })
        ]);
        b.style.setProperty('--i', k);
        b.addEventListener('click', function () { selectBrick(k); });
        els.bricks.appendChild(b);
      });
      els.detail.textContent = '';
      els.detail.appendChild(h('p', { class: 'kb-detail-hint', text: 'Clique une brique pour voir ce qu’elle fait exactement.' }));
    }

    function selectBrick(k) {
      var s = step(), br = s.bricks[k];
      st.selBrick = k;
      [].forEach.call(els.bricks.children, function (b, j) { b.setAttribute('aria-pressed', j === k ? 'true' : 'false'); });
      els.detail.textContent = '';
      els.detail.appendChild(h('p', { class: 'kb-detail-t' }, [TYPES[br.type] + ' · ', h('b', { text: br.name })]));
      els.detail.appendChild(h('p', { class: 'kb-detail-b', text: br.detail }));
      if (br.when) els.detail.appendChild(h('p', { class: 'kb-detail-w', text: br.when }));
    }

    /* ---------- navigation ---------- */
    function enter(i, animate) {
      clearTimers();
      var n = cur().steps.length;
      st.i = Math.max(0, Math.min(n - 1, i));
      st.approved = false; st.approvedBy = null;
      els.root.style.setProperty('--kb-sp', st.speed);
      placeCard(animate);
      renderBricks();
      renderStatus();
      var s = step();
      if (s.deny) {
        els.card.classList.remove('kb-nope');
        void els.card.offsetWidth;
        if (!reduced()) els.card.classList.add('kb-nope');
        els.card.style.setProperty('--kb-nope-d', (brickBase(0) / st.speed) + 'ms');
      } else {
        els.card.classList.remove('kb-nope');
      }
      syncPlay();
      scheduleAdvance();
    }

    function scheduleAdvance() {
      clearTimers();
      if (!st.playing || !st.visible || reduced()) return;
      var s = step(), n = cur().steps.length;
      var base = brickBase(s.bricks.length);
      if (s.gate && !st.approved) {
        later(function () { approve('auto'); }, (base + 2400) / st.speed);
        return;
      }
      if (st.i >= n - 1) {
        later(function () { st.playing = false; syncPlay(); renderGate(); }, (base + 1200) / st.speed);
        return;
      }
      later(function () { enter(st.i + 1, true); }, (base + 1900) / st.speed);
    }

    function approve(by) {
      var s = step();
      if (!s.gate || st.approved) return;
      st.approved = true; st.approvedBy = by;
      clearTimers();
      els.cardSt.textContent = cardState();
      els.card.classList.remove('kb-card--wait');
      renderGate();
      var p = h('p', { class: 'kb-approved', text: by === 'auto' ? 'Approuvé automatiquement (lecture automatique).' : 'Approuvé par toi.' });
      els.statusLive.appendChild(p);
      if (st.i < cur().steps.length - 1) {
        if (by === 'user' && !st.playing) later(function () { enter(st.i + 1, true); }, 450);
        else later(function () { enter(st.i + 1, true); }, 800 / st.speed);
      }
    }

    function next() {
      var s = step();
      if (st.i >= cur().steps.length - 1) return;
      enter(st.i + 1, true);
    }
    function prev() { if (st.i > 0) enter(st.i - 1, true); }

    function syncPlay() {
      var atEnd = st.i >= cur().steps.length - 1 && !st.playing;
      els.btnPlay.textContent = st.playing ? 'Pause' : (atEnd ? 'Rejouer' : 'Lecture');
      els.btnPlay.setAttribute('aria-label', st.playing ? 'Mettre en pause' : (atEnd ? 'Rejouer le scénario' : 'Lancer la lecture automatique'));
      els.btnSpeed.textContent = 'Vitesse ' + st.speed + '×';
      els.btnSpeed.setAttribute('aria-label', 'Vitesse de lecture ' + st.speed + ' fois, passer à ' + (st.speed === 1 ? 2 : 1) + ' fois');
      root.classList.toggle('kb--playing', st.playing);
    }

    function play() {
      if (reduced()) return;
      if (st.i >= cur().steps.length - 1 && !(step().gate && !st.approved)) { st.playing = true; enter(0, true); return; }
      st.playing = true; syncPlay(); renderGate(); scheduleAdvance();
    }
    function pause() { st.playing = false; clearTimers(); syncPlay(); renderGate(); }

    function setScenario(idx, autoplay) {
      st.sc = idx; clearTimers();
      [].forEach.call(els.tabs.children, function (b, k) { b.setAttribute('aria-pressed', k === idx ? 'true' : 'false'); });
      els.intro.textContent = cur().intro;
      buildBoard();
      st.playing = !!autoplay && !reduced();
      enter(0, false);
    }

    /* ---------- événements ---------- */
    els.btnPlay.addEventListener('click', function () { st.playing ? pause() : play(); });
    els.btnNext.addEventListener('click', function () { if (st.playing) pause(); next(); });
    els.btnPrev.addEventListener('click', function () { if (st.playing) pause(); prev(); });
    els.btnSpeed.addEventListener('click', function () { st.speed = st.speed === 1 ? 2 : 1; els.root.style.setProperty('--kb-sp', st.speed); syncPlay(); renderGate(); scheduleAdvance(); });
    els.btnReplay.addEventListener('click', function () { st.playing = !reduced(); enter(0, true); });

    root.addEventListener('keydown', function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      var tag = e.target && e.target.tagName;
      if (e.key === 'ArrowRight') { e.preventDefault(); if (st.playing) pause(); next(); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); if (st.playing) pause(); prev(); }
      else if ((e.key === ' ' || e.code === 'Space') && tag !== 'BUTTON' && tag !== 'A') { e.preventDefault(); if (!reduced()) st.playing ? pause() : play(); }
    });

    function onVis() { st.visible = !document.hidden && st.inView !== false; if (st.visible) scheduleAdvance(); else clearTimers(); }
    document.addEventListener('visibilitychange', onVis);
    var io = null;
    if ('IntersectionObserver' in window) {
      io = new IntersectionObserver(function (ents) {
        var e = ents[ents.length - 1];
        st.inView = e.isIntersecting;
        if (e.isIntersecting && !st.started && !reduced()) { st.started = true; st.playing = true; syncPlay(); }
        onVis();
      }, { threshold: 0.3 });
      io.observe(root);
    } else if (!reduced()) { st.playing = true; }
    function onMq() { root.classList.toggle('kb--reduce', reduced()); if (reduced()) { st.playing = false; clearTimers(); } syncPlay(); renderGate(); }
    if (mq.addEventListener) mq.addEventListener('change', onMq); else if (mq.addListener) mq.addListener(onMq);

    els.root = root;
    root.classList.toggle('kb--reduce', reduced());
    root.__kwaBoard = {
      destroy: function () { clearTimers(); document.removeEventListener('visibilitychange', onVis); if (io) io.disconnect(); root.textContent = ''; root.classList.remove('kb'); delete root.__kwaBoard; },
      state: st
    };
    setScenario(0, false);
    return root.__kwaBoard;
  }

  window.KwaBoard = { mount: mount };
})();
