/* KwaCircuit : « Une demande, de bout en bout », lisible sur un seul écran.
   Trois scénarios (une couleur chacun), un rail horizontal des étapes (les portes où tu décides et les refus de
   garde y sont visibles d'un coup d'œil), et une grande fiche qui change au même endroit. Rien ne bouge tout seul.
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
  function cap(t) { return t.charAt(0).toUpperCase() + t.slice(1); }

  function mount(root) {
    var D = window.KwaBoard && window.KwaBoard.data;
    if (!root || !D) return;
    var rm = window.matchMedia('(prefers-reduced-motion: reduce)');
    var st = { sc: 0, i: 0 };
    root.classList.add('kc');
    root.textContent = '';

    var scen = h('div', { class: 'kc-scen', role: 'group', 'aria-label': 'Scénario' });
    var track = h('ol', { class: 'kc-track', 'aria-label': 'Étapes du scénario' });
    var legend = h('ul', { class: 'kc-legend', 'aria-label': 'Légende' }, [
      h('li', null, [h('i', { class: 'kc-key kc-key--auto', 'aria-hidden': 'true' }), 'Étape automatique, sous les gardes']),
      h('li', null, [h('i', { class: 'kc-key kc-key--gate', 'aria-hidden': 'true' }), 'Porte : c’est toi qui décides']),
      h('li', null, [h('i', { class: 'kc-key kc-key--deny', 'aria-hidden': 'true' }), 'Refus : un garde bloque'])
    ]);
    var fiche = h('article', { class: 'kc-fiche', 'aria-live': 'polite' });
    var prev = h('button', { class: 'kc-btn', type: 'button', text: '← Précédent' });
    var next = h('button', { class: 'kc-btn kc-btn--primary', type: 'button', text: 'Suivant →' });
    prev.addEventListener('click', function () { go(st.i - 1); });
    next.addEventListener('click', function () { go(st.i === sc().steps.length - 1 ? 0 : st.i + 1); });
    var bar = h('div', { class: 'kc-bar' }, [legend, h('div', { class: 'kc-ctrl' }, [prev, next])]);
    [scen, h('div', { class: 'kc-trackwrap' }, [track]), bar, fiche].forEach(function (e) { root.appendChild(e); });

    D.SCENARIOS.forEach(function (sc, idx) {
      var b = h('button', { class: 'kc-sc kc-sc--' + sc.id, type: 'button', 'aria-pressed': idx === 0 ? 'true' : 'false' }, [
        h('span', { class: 'kc-sc-t' }, [h('i', { class: 'kc-dot', 'aria-hidden': 'true' }), sc.label, h('span', { class: 'kc-sc-n', text: sc.card.id + ' · ' + sc.card.title })]),
        h('span', { class: 'kc-sc-d', text: sc.intro })
      ]);
      b.addEventListener('click', function () { st.sc = idx; st.i = 0; build(); });
      scen.appendChild(b);
    });

    function sc() { return D.SCENARIOS[st.sc]; }
    function label(i) { return (LABELS[sc().id] || [])[i] || 'Étape ' + (i + 1); }
    function kind(s) { return s.gate ? 'gate' : (s.deny ? 'deny' : 'auto'); }
    function plain(i) { return cap(label(i).replace(/^(Porte|Refus) : /, '')); }

    function build() {
      var S = sc();
      root.setAttribute('data-sc', S.id);
      Array.prototype.forEach.call(scen.children, function (b, k) { b.setAttribute('aria-pressed', k === st.sc ? 'true' : 'false'); });
      track.textContent = '';
      var group = null, lastCol = -1;
      S.steps.forEach(function (s, i) {
        if (s.col !== lastCol) {
          lastCol = s.col;
          group = h('div', { class: 'kc-ph-steps' });
          track.appendChild(h('li', { class: 'kc-ph' }, [h('span', { class: 'kc-ph-l', text: D.COLS[s.col] }), group]));
        }
        var k = kind(s);
        var b = h('button', { class: 'kc-dotbtn kc-dotbtn--' + k, type: 'button', 'data-i': String(i), 'aria-label': 'Étape ' + (i + 1) + ' : ' + plain(i) + (k === 'gate' ? ' (porte)' : k === 'deny' ? ' (refus)' : '') }, [
          h('span', { class: 'kc-dotbtn-c', text: String(i + 1) }),
          k !== 'auto' && h('span', { class: 'kc-dotbtn-t', text: k === 'gate' ? 'Porte' : 'Refus' })
        ]);
        b.addEventListener('click', function () { go(i); });
        group.appendChild(b);
      });
      go(st.i, true);
    }

    function split(caption) {
      var m = caption.split(/ Pourquoi : /);
      return { what: m[0], why: m[1] || '' };
    }

    function block(title, kids, cls) {
      return h('section', { class: 'kc-block' + (cls ? ' ' + cls : '') }, [h('h4', { text: title })].concat(kids));
    }

    function renderFiche() {
      var S = sc(), s = S.steps[st.i], k = kind(s), parts = split(s.caption);
      fiche.textContent = '';
      fiche.className = 'kc-fiche kc-fiche--' + k;
      var badge = k === 'gate' ? 'Porte : c’est toi qui décides' : (k === 'deny' ? 'Un garde refuse' : 'Automatique, sous les gardes');

      var left = h('div', { class: 'kc-left' });
      left.appendChild(h('p', { class: 'kc-meta' }, [h('span', { text: 'Étape ' + (st.i + 1) + ' sur ' + S.steps.length + ' · ' + D.COLS[s.col] }), h('span', { class: 'kc-badge kc-badge--' + k, text: badge })]));
      left.appendChild(h('h3', { class: 'kc-title', text: plain(st.i) }));
      left.appendChild(block('Ce qui se passe', [h('p', { text: parts.what })]));
      if (parts.why) left.appendChild(block('Pourquoi', [h('p', { text: cap(parts.why) })]));
      if (s.deny) left.appendChild(block(s.deny.by + ' répond', [h('code', { text: s.deny.msg })], 'kc-block--deny'));
      var human = s.bricks.filter(function (b) { return b.type === 'humain'; })[0];
      if (human) left.appendChild(block('Ce que tu décides', [h('p', { text: human.name + '. ' + (human.detail || human.d) })], 'kc-block--gate'));

      var right = h('div', { class: 'kc-right' });
      right.appendChild(h('h4', { class: 'kc-rt', text: 'Ce qui se déclenche' }));
      var list = h('ul', { class: 'kc-bricks', 'aria-label': 'Briques déclenchées' });
      var shown = s.bricks.filter(function (b) { return b.type !== 'humain'; });
      if (!shown.length) list.appendChild(h('li', { class: 'kc-none', text: 'Rien ne se déclenche : le circuit attend ta décision.' }));
      shown.forEach(function (b) {
        list.appendChild(h('li', { class: 'kc-brick kc-brick--' + b.type }, [
          h('span', { class: 'kc-bt', text: D.TYPES[b.type] }),
          h('b', { text: b.name }),
          h('span', { class: 'kc-bd', text: b.d }),
          b.when && h('span', { class: 'kc-bw', text: b.when })
        ]));
      });
      right.appendChild(list);

      fiche.appendChild(h('div', { class: 'kc-cols' }, [left, right]));
    }

    function go(i, quiet) {
      st.i = Math.max(0, Math.min(sc().steps.length - 1, i));
      Array.prototype.forEach.call(track.querySelectorAll('.kc-dotbtn'), function (b) {
        var n = Number(b.getAttribute('data-i'));
        if (n === st.i) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
        b.classList.toggle('is-done', n < st.i);
      });
      prev.disabled = st.i === 0;
      next.textContent = st.i === sc().steps.length - 1 ? 'Recommencer' : 'Suivant →';
      renderFiche();
      var cur = track.querySelector('.kc-dotbtn[aria-current="step"]');
      Array.prototype.forEach.call(track.querySelectorAll('.kc-ph'), function (li) { li.classList.toggle('is-cur', !!cur && li.contains(cur)); });
      var wrap = track.parentNode;
      if (cur && wrap.scrollWidth > wrap.clientWidth) wrap.scrollTo({ left: cur.offsetLeft - wrap.clientWidth / 2 + cur.offsetWidth / 2, behavior: quiet || rm.matches ? 'auto' : 'smooth' });
    }

    root.addEventListener('keydown', function (e) {
      if (e.target && e.target.closest && e.target.closest('input, textarea, select')) return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); go(st.i + 1); focusCur(); }
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); go(st.i - 1); focusCur(); }
    });
    function focusCur() { var b = track.querySelector('.kc-dotbtn[aria-current="step"]'); if (b) b.focus({ preventScroll: true }); }

    build();
  }

  window.KwaCircuit = { mount: mount };
})();
