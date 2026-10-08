/* KwaCircuit : « Une demande, de bout en bout », en un seul écran.
   La liste des étapes et la fiche de l'étape courante sont côte à côte (bureau) ou la fiche s'ouvre sous l'étape
   (mobile) : ce qui change est toujours là où l'œil se trouve. Aucune lecture automatique.
   Les données viennent de board.js (window.KwaBoard.data). Script classique, sans dépendance. */
(function () {
  'use strict';

  var LABELS = {
    feature: ['Cadrage : brainstorm avant de coder', 'Porte : tu approuves la spec', 'Plan en tâches de 2 à 5 minutes', 'Issue, branche et worktree',
      'Un implémenteur par tâche', 'Refus : lecture de .env', 'Relecture : conformité puis qualité', 'Preuve : sortie fraîche des vérifications',
      'Revue de toute la branche', 'Porte : tu demandes le commit', 'Commit, push confirmé, PR liée', 'Capitaliser ce qui a coûté'],
    bug: ['Cause racine avant tout correctif', 'Refus : code sur main', 'Issue et branche', 'Test rouge d’abord', 'Correctif minimal',
      'Preuve par mutation', 'Porte : tu demandes la publication', 'Capitaliser le piège'],
    delivery: ['Vérifications avant publication', 'Refus : push direct sur main', 'Porte : tu confirmes le push', 'Refus : PR sans issue',
      'PR avec « Closes #14 »', 'Porte : ton GO de fusion', 'Refus : fusion sans preuve', 'Porte : tu confirmes le déploiement',
      'Vérifier la révision servie', 'Capitaliser']
  };

  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'text') e.textContent = attrs[k];
      else if (attrs[k] === false || attrs[k] == null) continue;
      else e.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return e;
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function cap(t) { return t.charAt(0).toUpperCase() + t.slice(1); }

  function mount(root) {
    var D = window.KwaBoard && window.KwaBoard.data;
    if (!root || !D) return;
    var mq = window.matchMedia('(max-width: 899px)');
    var rm = window.matchMedia('(prefers-reduced-motion: reduce)');
    var st = { sc: 0, i: 0 };
    root.classList.add('kc');
    root.textContent = '';

    var tabs = h('div', { class: 'kc-tabs', role: 'group', 'aria-label': 'Scénario' });
    var intro = h('p', { class: 'kc-intro' });
    var decisions = h('div', { class: 'kc-dec' });
    var list = h('ol', { class: 'kc-list', 'aria-label': 'Étapes' });
    var fiche = h('article', { class: 'kc-fiche', 'aria-live': 'polite' });
    var grid = h('div', { class: 'kc-grid' }, [list, fiche]);
    [tabs, intro, decisions, grid].forEach(function (e) { root.appendChild(e); });

    D.SCENARIOS.forEach(function (sc, idx) {
      var b = h('button', { class: 'kc-tab', type: 'button', 'aria-pressed': idx === 0 ? 'true' : 'false' }, [h('span', { text: sc.label }), h('span', { class: 'kc-tab-n', text: sc.card.id })]);
      b.addEventListener('click', function () { st.sc = idx; st.i = 0; build(); });
      tabs.appendChild(b);
    });

    function sc() { return D.SCENARIOS[st.sc]; }
    function label(i) { return (LABELS[sc().id] || [])[i] || 'Étape ' + (i + 1); }
    function kind(s) { return s.gate ? 'gate' : (s.deny ? 'deny' : 'auto'); }

    function build() {
      var S = sc();
      Array.prototype.forEach.call(tabs.children, function (b, k) { b.setAttribute('aria-pressed', k === st.sc ? 'true' : 'false'); });
      intro.textContent = S.intro;
      var gates = S.steps.map(function (s, i) { return s.gate ? i : -1; }).filter(function (i) { return i >= 0; });
      decisions.textContent = '';
      decisions.appendChild(h('span', { class: 'kc-dec-l', text: gates.length === 1 ? 'Ta décision' : 'Tes ' + gates.length + ' décisions' }));
      gates.forEach(function (i) {
        var b = h('button', { class: 'kc-chip', type: 'button' }, [h('b', { text: pad(i + 1) }), ' ' + cap(label(i).replace(/^Porte : /, ''))]);
        b.addEventListener('click', function () { go(i, true); });
        decisions.appendChild(b);
      });
      list.textContent = '';
      var lastCol = -1;
      S.steps.forEach(function (s, i) {
        if (s.col !== lastCol) {
          lastCol = s.col;
          list.appendChild(h('li', { class: 'kc-phase', 'aria-hidden': 'true', text: D.COLS[s.col] }));
        }
        var k = kind(s);
        var mark = k === 'gate' ? 'Porte' : (k === 'deny' ? 'Refus' : '');
        var b = h('button', { class: 'kc-step kc-step--' + k, type: 'button', 'data-i': String(i) }, [
          h('span', { class: 'kc-n', text: pad(i + 1) }), h('span', { class: 'kc-t', text: cap(label(i).replace(/^(Porte|Refus) : /, '')) }), mark && h('span', { class: 'kc-mark', text: mark })
        ]);
        b.addEventListener('click', function () { go(i, false); });
        list.appendChild(h('li', { class: 'kc-item' }, [b]));
      });
      go(st.i, false, true);
    }

    function split(caption) {
      var m = caption.split(/ Pourquoi : /);
      return { what: m[0], why: m[1] || '' };
    }

    function renderFiche() {
      var S = sc(), s = S.steps[st.i], k = kind(s), parts = split(s.caption);
      fiche.textContent = '';
      fiche.className = 'kc-fiche kc-fiche--' + k;
      var badge = k === 'gate' ? 'Porte : c’est toi qui décides' : (k === 'deny' ? 'Un garde refuse' : 'Se fait tout seul, sous les gardes');
      var prev = h('button', { class: 'kc-btn', type: 'button', 'aria-label': 'Étape précédente', text: '←' });
      var next = h('button', { class: 'kc-btn kc-btn--primary', type: 'button', text: st.i === S.steps.length - 1 ? 'Recommencer' : 'Suivant →' });
      prev.disabled = st.i === 0;
      prev.addEventListener('click', function () { go(st.i - 1, false); });
      next.addEventListener('click', function () { go(st.i === S.steps.length - 1 ? 0 : st.i + 1, false); });
      fiche.appendChild(h('div', { class: 'kc-fh' }, [
        h('div', { class: 'kc-nav' }, [prev, next, h('span', { class: 'kc-fh-n', text: 'Étape ' + (st.i + 1) + ' sur ' + S.steps.length + ' · ' + D.COLS[s.col] })]),
        h('span', { class: 'kc-badge kc-badge--' + k, text: badge })
      ]));
      fiche.appendChild(h('h3', { class: 'kc-title', text: cap(label(st.i).replace(/^(Porte|Refus) : /, '')) }));
      fiche.appendChild(h('p', { class: 'kc-what', text: parts.what }));
      if (parts.why) fiche.appendChild(h('p', { class: 'kc-why' }, [h('b', { text: 'Pourquoi ' }), parts.why]));
      if (s.deny) {
        fiche.appendChild(h('div', { class: 'kc-deny' }, [h('span', { text: s.deny.by + ' répond' }), h('code', { text: s.deny.msg })]));
      }
      var bricks = h('ul', { class: 'kc-bricks', 'aria-label': 'Briques déclenchées' });
      s.bricks.forEach(function (b) {
        var li = h('li', { class: 'kc-brick kc-brick--' + b.type }, [
          h('span', { class: 'kc-bt', text: D.TYPES[b.type] }),
          h('b', { text: b.name }),
          h('span', { class: 'kc-bd', text: b.d }),
          b.when && h('span', { class: 'kc-bw', text: b.when })
        ]);
        bricks.appendChild(li);
      });
      fiche.appendChild(bricks);
    }

    function place() {
      var active = list.querySelector('.kc-step[aria-current="step"]');
      if (mq.matches && active) active.parentNode.appendChild(fiche);
      else if (fiche.parentNode !== grid) grid.appendChild(fiche);
    }

    function go(i, scroll, quiet) {
      var n = sc().steps.length;
      st.i = Math.max(0, Math.min(n - 1, i));
      Array.prototype.forEach.call(list.querySelectorAll('.kc-step'), function (b) {
        var on = Number(b.getAttribute('data-i')) === st.i;
        if (on) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
        b.classList.toggle('is-done', Number(b.getAttribute('data-i')) < st.i);
      });
      renderFiche();
      place();
      if (!quiet && (scroll || mq.matches)) {
        var target = mq.matches ? list.querySelector('.kc-step[aria-current="step"]') : fiche;
        if (target && target.scrollIntoView) target.scrollIntoView({ block: mq.matches ? 'start' : 'nearest', behavior: rm.matches ? 'auto' : 'smooth' });
      }
    }

    root.addEventListener('keydown', function (e) {
      var t = e.target && e.target.closest && e.target.closest('.kc-step');
      if (!t) return;
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') { e.preventDefault(); go(st.i + 1, false); focusStep(); }
      else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') { e.preventDefault(); go(st.i - 1, false); focusStep(); }
    });
    function focusStep() { var b = list.querySelector('.kc-step[aria-current="step"]'); if (b) b.focus({ preventScroll: true }); }
    if (mq.addEventListener) mq.addEventListener('change', place);

    build();
  }

  window.KwaCircuit = { mount: mount };
})();
