/* Parcours : explications visuelles (jetons, fenêtre de contexte) et apparition des étapes. Aucun appel à un modèle : ce sont
   des illustrations, présentées comme telles. Script classique, sans dépendance. */
(function () {
  'use strict';
  function $(s, r) { return (r || document).querySelector(s); }
  function fmt(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* apparition des étapes au défilement */
  var stages = document.querySelectorAll('.pc-stage');
  if (stages.length && 'IntersectionObserver' in window && !reduced) {
    document.documentElement.classList.add('pc-js');
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } }); }, { rootMargin: '0px 0px -8% 0px' });
    Array.prototype.forEach.call(stages, function (s) { io.observe(s); });
  }

  /* ---------- jetons : un découpage illustratif, en couleurs ---------- */
  var area = $('#tok-input');
  if (area) {
    var chips = $('#tok-chips'), out = $('#tok-out'), MAX = 700;
    var cut = function (text) {
      var parts = text.match(/\s*[\p{L}\p{N}'’-]+|\s*[^\s\p{L}\p{N}]/gu) || [], toks = [];
      parts.forEach(function (p) {
        var lead = (p.match(/^\s*/) || [''])[0], core = p.slice(lead.length);
        if (core.length <= 6) { toks.push(lead + core); return; }
        for (var i = 0; i < core.length; i += 5) toks.push((i === 0 ? lead : '') + core.slice(i, i + 5));
      });
      return toks;
    };
    var render = function (animate) {
      var text = area.value, toks = cut(text), chars = text.length, words = (text.trim().match(/\S+/g) || []).length;
      chips.textContent = '';
      chips.classList.toggle('pc-anim', !!animate && !reduced);
      toks.slice(0, MAX).forEach(function (t, i) {
        var c = document.createElement('span');
        c.className = 'pc-tok pc-t' + (i % 6);
        c.textContent = t.replace(/\n/g, '↵');
        if (animate && !reduced) c.style.animationDelay = Math.min(i * 14, 900) + 'ms';
        chips.appendChild(c);
      });
      if (toks.length > MAX) { var more = document.createElement('span'); more.className = 'pc-tok pc-more'; more.textContent = '… ' + fmt(toks.length - MAX) + ' de plus'; chips.appendChild(more); }
      var lo = Math.min(chars / 4, words * 1.3), hi = Math.max(chars / 4, words * 1.3);
      out.innerHTML = '<div><b>' + fmt(toks.length) + '</b> jetons dans ce découpage</div><div><b>' + fmt(chars) + '</b> caractères, <b>' + fmt(words) + '</b> mots</div>' +
        '<div>Ordre de grandeur d\'un vrai compte : <b>' + fmt(lo) + ' à ' + fmt(hi) + '</b></div>';
    };
    area.addEventListener('input', function () { render(false); });
    var replay = $('#tok-replay');
    if (replay) replay.addEventListener('click', function () { render(true); });
    render(false);
    if ('IntersectionObserver' in window) {
      var seen = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { render(true); seen.disconnect(); } }, { threshold: 0.4 });
      seen.observe(chips);
    }
  }

  /* ---------- fenêtre de contexte : barre empilée, simulation, compaction ---------- */
  var gauge = $('#ctx-gauge');
  if (gauge) {
    var F = ['sys', 'rules', 'tools', 'hist', 'files', 'res'];
    var win = $('#ctx-win'), txt = $('#ctx-txt'), msg = $('#ctx-msg'), stack = $('#ctx-stack');
    var PRESETS = {
      chat: { sys: 1500, rules: 0, tools: 0, hist: 6000, files: 0, res: 0 },
      agent: { sys: 6000, rules: 3000, tools: 12000, hist: 30000, files: 40000, res: 25000 },
      long: { sys: 6000, rules: 3000, tools: 25000, hist: 180000, files: 150000, res: 220000 }
    };
    var STAGES = [
      [{ sys: 6000, rules: 3000, tools: 12000, hist: 0, files: 0, res: 0 }, 'Au démarrage, les consignes, les instructions et les outils occupent déjà la fenêtre, avant votre premier message.'],
      [{ hist: 8000 }, 'Vous posez une question, l\'agent répond : l\'historique commence à grossir.'],
      [{ files: 40000 }, 'L\'agent lit des fichiers pour comprendre le code : chaque fichier lu reste dans la fenêtre.'],
      [{ hist: 25000, res: 45000 }, 'Les résultats d\'outils (tests, recherches, commandes) s\'accumulent.'],
      [{ hist: 45000, files: 50000, res: 60000 }, 'La session s\'allonge : la fenêtre est presque pleine, et la précision peut baisser avant même qu\'elle ne déborde.']
    ];
    var COMPACT = [{ hist: 4000, files: 8000, res: 3000 }, 'Compaction : l\'historique et les résultats sont résumés, la session continue avec un contexte court.'];
    var run = 0;
    var get = function () { var v = {}; F.forEach(function (f) { v[f] = Number($('#ctx-' + f).value) || 0; }); return v; };
    var set = function (v) { F.forEach(function (f) { if (f in v) $('#ctx-' + f).value = Math.round(v[f]); }); read(); };
    function read(note) {
      var v = get(), total = 0, w = Number(win.value);
      F.forEach(function (f) { total += v[f]; });
      var scale = total > w ? total : w;
      F.forEach(function (f) { $('#seg-' + f).style.width = (v[f] / scale * 100) + '%'; });
      stack.classList.toggle('pc-over', total > w);
      var pct = total / w * 100;
      txt.textContent = fmt(total) + ' jetons sur ' + fmt(w) + ' (' + Math.round(pct) + ' %)';
      if (note) { msg.textContent = note; return; }
      msg.textContent = total > w ? 'Ça ne rentre pas : il faut résumer (compaction), repartir d\'une session neuve ou déléguer à un sous-agent.'
        : (pct > 60 ? 'Beaucoup de place est prise. Plus de contexte n\'est pas mieux : la précision peut baisser quand il grossit.' : 'Il reste de la marge, mais regardez la composition : ce qui est là sans servir coûte quand même.');
    }
    function tween(target, ms, done) {
      var from = get(), t0 = null, id = run;
      if (reduced || ms <= 0) { set(Object.assign({}, from, target)); if (done) done(); return; }
      (function step(ts) {
        if (id !== run) return;
        if (t0 === null) t0 = ts;
        var k = Math.min(1, (ts - t0) / ms), e = 1 - Math.pow(1 - k, 3), v = {};
        F.forEach(function (f) { v[f] = from[f] + ((f in target ? target[f] : from[f]) - from[f]) * e; });
        set(v);
        if (k < 1) requestAnimationFrame(step); else if (done) done();
      })(performance.now());
    }
    function play() {
      var id = ++run, i = 0;
      set({ sys: 0, rules: 0, tools: 0, hist: 0, files: 0, res: 0 });
      (function next() {
        if (id !== run || i >= STAGES.length) return;
        var s = STAGES[i++];
        tween(s[0], 800, function () { read(s[1]); setTimeout(next, reduced ? 200 : 900); });
      })();
    }
    function compact() {
      var id = ++run;
      tween(COMPACT[0], 900, function () { if (id === run) read(COMPACT[1]); });
    }
    F.forEach(function (f) { $('#ctx-' + f).addEventListener('input', function () { run++; read(); }); });
    win.addEventListener('change', function () { run++; read(); });
    Array.prototype.forEach.call(document.querySelectorAll('[data-ctx-preset]'), function (b) {
      b.addEventListener('click', function () { run++; set(PRESETS[b.getAttribute('data-ctx-preset')]); });
    });
    var bp = $('[data-ctx-play]'), bc = $('[data-ctx-compact]');
    if (bp) bp.addEventListener('click', play);
    if (bc) bc.addEventListener('click', compact);
    read();
  }
})();
