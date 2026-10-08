/* Kwa — terminal simulé (documentation). Script classique, sans dépendance.
 * Usage : KwaTerminal.mount(document.getElementById('kwa-terminal'), data)   // data = terminal-data.json
 * Les textes passent par textContent / nœuds DOM : aucune injection HTML possible. */
(function () {
  'use strict';

  var SVG_NS = 'http://www.w3.org/2000/svg';
  var ICONS = {
    play: 'M8 5.5v13l11-6.5z',
    pause: 'M8 5.5v13M16 5.5v13',
    prev: 'M15 5.5 8 12l7 6.5',
    next: 'M9 5.5 16 12l-7 6.5',
    replay: 'M4.5 12a7.5 7.5 0 1 0 2.4-5.5M4.5 4.5v4h4',
    skip: 'M5 5.5v13l8-6.5zM17 5.5v13',
    copy: 'M9 9h10v10H9zM5 15V5h10'
  };
  var SPEEDS = [0.5, 1, 2, 4];
  var uid = 0;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function icon(name) {
    var s = document.createElementNS(SVG_NS, 'svg');
    s.setAttribute('viewBox', '0 0 24 24');
    s.setAttribute('aria-hidden', 'true');
    s.setAttribute('focusable', 'false');
    var p = document.createElementNS(SVG_NS, 'path');
    p.setAttribute('d', ICONS[name]);
    s.appendChild(p);
    return s;
  }

  function button(cls, label, ic, text) {
    var b = el('button', 'kt-btn ' + (cls || ''));
    b.type = 'button';
    if (label) b.setAttribute('aria-label', label);
    if (ic) b.appendChild(icon(ic));
    var t = el('span', 'kt-btn-label', text);
    b.appendChild(t);
    return b;
  }

  /* **gras** et `code` dans les textes pédagogiques */
  function inline(parent, text) {
    var re = /(\*\*[^*]+\*\*|`[^`]+`)/g, last = 0, m;
    while ((m = re.exec(text))) {
      if (m.index > last) parent.appendChild(document.createTextNode(text.slice(last, m.index)));
      var tok = m[0];
      if (tok.charAt(0) === '`') parent.appendChild(el('code', 'kt-code', tok.slice(1, -1)));
      else parent.appendChild(el('strong', null, tok.slice(2, -2)));
      last = m.index + tok.length;
    }
    if (last < text.length) parent.appendChild(document.createTextNode(text.slice(last)));
    return parent;
  }

  function plain(text) { return String(text).replace(/\*\*|`/g, ''); }

  /* Mise en évidence de la sortie : gras et traits, jamais de couleur ajoutée. */
  function renderLine(text) {
    var line = el('div', 'kt-line'), m;
    if (text === '') { line.appendChild(document.createTextNode(' ')); return line; }
    if ((m = /^(\s*"permissionDecision": ")(deny|ask|allow)(",?)$/.exec(text))) {
      line.className += ' kt-line--dec kt-dec-' + m[2];
      line.appendChild(document.createTextNode(m[1]));
      line.appendChild(el('span', 'kt-tag', m[2]));
      line.appendChild(document.createTextNode(m[3]));
      return line;
    }
    if ((m = /^(\s*)([✓✗])(\s+)(.+?)(\s{2,})(.*)$/.exec(text))) {
      line.appendChild(document.createTextNode(m[1]));
      line.appendChild(el('span', m[2] === '✓' ? 'kt-ok' : 'kt-mark', m[2]));
      line.appendChild(document.createTextNode(m[3]));
      line.appendChild(el('strong', null, m[4]));
      line.appendChild(document.createTextNode(m[5] + m[6]));
      if (m[2] === '✗') line.className += ' kt-line--ko';
      return line;
    }
    if ((m = /^(\s*)([✓✗?•])(\s+)(\S+)(.*)$/.exec(text))) {
      line.appendChild(document.createTextNode(m[1]));
      line.appendChild(el('span', m[2] === '✓' ? 'kt-ok' : 'kt-mark', m[2]));
      line.appendChild(document.createTextNode(m[3]));
      if (m[2] === '•') line.appendChild(document.createTextNode(m[4]));
      else line.appendChild(el('strong', null, m[4]));
      line.appendChild(document.createTextNode(m[5]));
      if (m[2] === '✗') line.className += ' kt-line--ko';
      return line;
    }
    if (/^## /.test(text)) { line.appendChild(el('strong', null, text)); return line; }
    if ((m = /^(\s{2})([A-ZÉÀ]{4,})(\s.*)$/.exec(text))) {
      line.appendChild(document.createTextNode(m[1]));
      line.appendChild(el('strong', null, m[2]));
      line.appendChild(document.createTextNode(m[3]));
      return line;
    }
    if ((m = /^(\s+)([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 ._\/-]*?)( : .*)$/.exec(text))) {
      line.appendChild(document.createTextNode(m[1]));
      line.appendChild(el('strong', null, m[2]));
      line.appendChild(document.createTextNode(m[3]));
      return line;
    }
    if ((m = /^(\[[^\]]+\]|[A-Za-zÀ-ÿ0-9#][^\s]*)(.*)$/.exec(text))) {
      line.appendChild(el('strong', null, m[1]));
      line.appendChild(document.createTextNode(m[2]));
      return line;
    }
    line.appendChild(document.createTextNode(text));
    return line;
  }

  function renderCommandText(parent, cmd) {
    var m = /^(\S+)([\s\S]*)$/.exec(cmd);
    parent.textContent = '';
    if (!m) return;
    parent.appendChild(el('strong', 'kt-prog', m[1]));
    parent.appendChild(document.createTextNode(m[2]));
  }

  function copyText(text, done) {
    function fallback() {
      var ta = el('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      done(ok);
    }
    if (navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    } else fallback();
  }

  function mount(root, data) {
    if (!root || !data || !data.scenarios || !data.scenarios.length) return null;
    var id = 'kt' + (++uid);
    var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
    var st = {
      sc: 0, i: -1, shown: 0, mode: 'auto', paused: false, speed: 1, timer: 0, cont: null,
      animating: false, instant: !!mq.matches, started: false, copyTimer: 0
    };
    var scenarios = data.scenarios;

    /* ---------- structure ---------- */
    root.textContent = '';
    root.classList.add('kt');
    var tabs = el('div', 'kt-tabs');
    tabs.setAttribute('role', 'tablist');
    tabs.setAttribute('aria-label', 'Scénarios');
    var tabEls = scenarios.map(function (s, k) {
      var b = el('button', 'kt-tab', s.title);
      b.type = 'button';
      b.id = id + '-tab-' + k;
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-controls', id + '-panel');
      b.addEventListener('click', function () { selectScenario(k, true); });
      b.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : e.key === 'Home' ? 'h' : e.key === 'End' ? 'e' : 0;
        if (!d) return;
        e.preventDefault();
        var n = d === 'h' ? 0 : d === 'e' ? scenarios.length - 1 : (st.sc + d + scenarios.length) % scenarios.length;
        selectScenario(n, true);
        tabEls[n].focus();
      });
      tabs.appendChild(b);
      return b;
    });

    var panel = el('div', 'kt-panel');
    panel.id = id + '-panel';
    panel.setAttribute('role', 'tabpanel');
    var prep = el('p', 'kt-prep');
    var grid = el('div', 'kt-grid');
    var main = el('div', 'kt-main');
    var win = el('div', 'kt-window');
    var bar = el('div', 'kt-bar');
    var dots = el('span', 'kt-dots');
    dots.setAttribute('aria-hidden', 'true');
    dots.appendChild(el('i')); dots.appendChild(el('i')); dots.appendChild(el('i'));
    var wtitle = el('span', 'kt-wtitle');
    var copyBtn = button('kt-btn--small kt-copy', 'Copier la commande', 'copy', 'Copier la commande');
    var copyStatus = el('span', 'kt-sr');
    copyStatus.setAttribute('role', 'status');
    bar.appendChild(dots); bar.appendChild(wtitle); bar.appendChild(copyBtn); bar.appendChild(copyStatus);
    var screen = el('div', 'kt-screen');
    screen.tabIndex = 0;
    screen.setAttribute('role', 'log');
    screen.setAttribute('aria-live', 'polite');
    screen.setAttribute('aria-relevant', 'additions');
    screen.setAttribute('aria-label', 'Sortie du terminal');
    win.appendChild(bar); win.appendChild(screen);

    var controls = el('div', 'kt-controls');
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', 'Contrôles de lecture');
    var bPlay = button('kt-btn--primary', null, 'play', 'Lecture');
    var bPrev = button('', 'Étape précédente', 'prev', 'Précédent');
    var bNext = button('', 'Étape suivante', 'next', 'Suivant');
    var bReplay = button('', 'Rejouer le scénario', 'replay', 'Rejouer');
    var bSkip = button('', 'Passer : tout afficher d’un coup', 'skip', 'Passer');
    var bSpeed = button('kt-btn--speed', null, null, '');
    [bPlay, bPrev, bNext, bReplay, bSkip, bSpeed].forEach(function (b) { controls.appendChild(b); });
    main.appendChild(win); main.appendChild(controls);

    var side = el('aside', 'kt-side');
    side.setAttribute('aria-label', 'Explications');
    var eyebrow = el('p', 'kt-eyebrow', 'Ce qui se passe');
    var counter = el('p', 'kt-counter');
    var exTitle = el('h3', 'kt-ex-title');
    var exBody = el('div', 'kt-ex-body');
    var stepsLabel = el('p', 'kt-eyebrow kt-eyebrow--steps', 'Étapes');
    var list = el('ol', 'kt-steps');
    side.appendChild(eyebrow); side.appendChild(counter); side.appendChild(exTitle); side.appendChild(exBody);
    side.appendChild(stepsLabel); side.appendChild(list);
    grid.appendChild(main); grid.appendChild(side);
    panel.appendChild(prep); panel.appendChild(grid);
    root.appendChild(tabs); root.appendChild(panel);

    /* ---------- moteur ---------- */
    function sc() { return scenarios[st.sc]; }
    function steps() { return sc().steps; }

    function clearTimer() { if (st.timer) { clearTimeout(st.timer); st.timer = 0; } }

    function later(fn, ms, force) {
      if (st.instant && !force) { fn(); return; }
      st.cont = fn;
      if (st.paused) return;
      clearTimer();
      st.timer = setTimeout(function () { st.timer = 0; var f = st.cont; st.cont = null; if (f) f(); }, ms / st.speed);
    }

    function stop() { clearTimer(); st.cont = null; st.animating = false; }

    function scrollEnd() { screen.scrollTop = screen.scrollHeight; }

    function blockFor(step, complete) {
      var b = el('div', 'kt-block');
      var cl = el('div', 'kt-cmdline');
      cl.appendChild(el('span', 'kt-cwd', step.cwd || '~'));
      cl.appendChild(el('span', 'kt-prompt', ' $ '));
      var ct = el('span', 'kt-cmd');
      cl.appendChild(ct);
      b.appendChild(cl);
      var out = el('div', 'kt-out');
      b.appendChild(out);
      if (complete) {
        renderCommandText(ct, step.cmd);
        fillOutput(out, step, 99999);
      }
      return { block: b, cmd: ct, line: cl, out: out };
    }

    function outputLines(step) {
      var lines = step.output ? step.output.split('\n') : [];
      var tail = [];
      if (!step.output && step.empty_note) tail.push({ note: step.empty_note });
      if (step.code) tail.push({ note: 'code de sortie ' + step.code });
      return { lines: lines, tail: tail };
    }

    function noteLine(text) {
      var n = el('div', 'kt-line kt-note');
      n.appendChild(el('span', 'kt-note-arrow', '↳ '));
      n.appendChild(document.createTextNode(text));
      return n;
    }

    function fillOutput(out, step, upto) {
      var o = outputLines(step), k;
      for (k = 0; k < o.lines.length && k < upto; k++) out.appendChild(renderLine(o.lines[k]));
      if (upto >= o.lines.length) o.tail.forEach(function (t) { out.appendChild(noteLine(t.note)); });
    }

    function renderStatic(count) {
      screen.setAttribute('aria-live', 'off');
      screen.textContent = '';
      for (var k = 0; k < count; k++) screen.appendChild(blockFor(steps()[k], true).block);
      st.shown = count;
      requestAnimationFrame(function () { screen.setAttribute('aria-live', 'polite'); });
      scrollEnd();
    }

    function runStep(i) {
      var step = steps()[i];
      if (st.shown !== i) renderStatic(i);
      st.i = i;
      st.animating = true;
      updateUI();
      var b = blockFor(step, false);
      screen.appendChild(b.block);
      var caret = el('span', 'kt-caret');
      caret.setAttribute('aria-hidden', 'true');
      b.line.appendChild(caret);
      b.line.setAttribute('aria-hidden', 'true');
      scrollEnd();
      var sr = el('div', 'kt-sr', 'Commande : ' + step.cmd);
      var cmd = step.cmd;

      /* progression au temps écoulé (et non au nombre de ticks) : robuste aux onglets ralentis ; plafonné à
         120 ms par tick pour qu'une pause ne compte pas */
      function progress(total, onFrac, onDone) {
        var frac = 0, last = 0;
        (function tick() {
          var now = Date.now();
          var dt = last ? Math.min(now - last, 120) : 0;
          last = now;
          frac = st.instant ? 1 : Math.min(1, frac + (dt * st.speed) / total);
          onFrac(frac);
          if (frac < 1) later(tick, 16); else onDone();
        })();
      }

      function typing() {
        progress(Math.min(1800, Math.max(500, cmd.length * 26)), function (f) {
          renderCommandText(b.cmd, cmd.slice(0, Math.ceil(cmd.length * f)));
          scrollEnd();
        }, function () { later(afterTyping, 420); });
      }
      function afterTyping() {
        if (caret.parentNode) caret.parentNode.removeChild(caret);
        b.line.setAttribute('aria-hidden', 'true');
        b.out.appendChild(sr);
        var o = outputLines(step), n = 0;
        function lines() {
          progress(Math.min(2400, Math.max(200, o.lines.length * 45)), function (f) {
            var end = Math.ceil(o.lines.length * f);
            for (; n < end; n++) b.out.appendChild(renderLine(o.lines[n]));
            scrollEnd();
          }, function () {
            o.tail.forEach(function (t) { b.out.appendChild(noteLine(t.note)); });
            scrollEnd();
            finish();
          });
        }
        lines();
      }
      function finish() {
        st.shown = i + 1;
        st.animating = false;
        if (st.mode === 'auto' && i + 1 < steps().length) later(function () { runStep(i + 1); }, 1500, true);
        else if (i + 1 >= steps().length) st.mode = 'manual';
        updateUI();
      }
      if (!cmd.length) { later(afterTyping, 0); return; }
      later(typing, 250);
    }

    function finishNow() {
      var prevMode = st.mode;
      st.mode = 'manual';
      var wasInstant = st.instant;
      st.instant = true;
      clearTimer();
      var f = st.cont;
      st.cont = null;
      st.paused = false;
      if (f) f();
      st.instant = wasInstant;
      if (prevMode === 'auto') st.mode = 'manual';
      updateUI();
    }

    /* ---------- actions ---------- */
    function start() { st.started = true; st.mode = 'auto'; st.paused = false; stop(); st.shown = -1; runStep(0); }
    function play() {
      if (st.paused && st.cont) {
        st.paused = false; st.mode = 'auto';
        var f = st.cont; st.cont = null; later(f, 0);
        updateUI();
        return;
      }
      st.paused = false; st.mode = 'auto';
      if (st.animating) { updateUI(); return; }
      if (st.i >= 0 && st.i + 1 < steps().length && st.shown > st.i) runStep(st.i + 1);
      else start();
    }
    function pause() { st.paused = true; clearTimer(); updateUI(); }
    function next() {
      if (st.animating) { finishNow(); return; }
      if (st.i + 1 < steps().length) { st.mode = 'manual'; st.paused = false; runStep(st.i + 1); }
    }
    function prev() {
      stop(); st.mode = 'manual'; st.paused = false;
      if (st.i > 0) { st.i--; renderStatic(st.i + 1); }
      updateUI();
    }
    function replay() { stop(); st.started = true; st.mode = 'auto'; st.paused = false; st.shown = -1; renderStatic(0); runStep(0); }
    function skip() {
      stop(); st.started = true; st.mode = 'manual'; st.paused = false;
      st.i = steps().length - 1;
      renderStatic(steps().length);
      updateUI();
    }
    function goTo(k) {
      stop(); st.started = true; st.paused = false;
      if (st.shown !== k) renderStatic(k);
      runStep(k);
    }
    function selectScenario(k, userInitiated) {
      stop();
      st.sc = k; st.i = -1; st.shown = 0; st.paused = false; st.mode = 'auto';
      buildScenario();
      renderStatic(0);
      if (userInitiated) st.started = true;
      if (st.started && !st.instant) runStep(0);
      else if (st.instant) { st.mode = 'manual'; renderStatic(1); st.i = 0; }
      updateUI();
    }

    /* ---------- interface ---------- */
    function buildScenario() {
      var s = sc();
      tabEls.forEach(function (b, k) {
        var on = k === st.sc;
        b.setAttribute('aria-selected', on ? 'true' : 'false');
        b.tabIndex = on ? 0 : -1;
        if (on) panel.setAttribute('aria-labelledby', b.id);
      });
      prep.textContent = '';
      prep.appendChild(el('strong', null, 'Cadre : '));
      inline(prep, s.prep || s.summary || '');
      list.textContent = '';
      s.steps.forEach(function (step, k) {
        var li = el('li', 'kt-step');
        var b = el('button', 'kt-step-btn');
        b.type = 'button';
        b.appendChild(el('span', 'kt-step-n', String(k + 1)));
        var tx = el('span', 'kt-step-tx');
        tx.appendChild(el('span', 'kt-step-t', plain(step.explain.title)));
        tx.appendChild(el('span', 'kt-step-c', step.cmd));
        b.appendChild(tx);
        b.addEventListener('click', function () { goTo(k); });
        li.appendChild(b);
        list.appendChild(li);
      });
      wtitle.textContent = '~/mon-projet — zsh';
    }

    function setLabel(btn, text, ic) {
      btn.querySelector('.kt-btn-label').textContent = text;
      var old = btn.querySelector('svg');
      if (ic && old) { btn.replaceChild(icon(ic), old); }
    }

    function updateUI() {
      var n = steps().length, i = st.i, step = steps()[Math.max(i, 0)];
      var playing = st.mode === 'auto' && !st.paused && (st.animating || !!st.cont);
      setLabel(bPlay, playing ? 'Pause' : 'Lecture', playing ? 'pause' : 'play');
      bPlay.setAttribute('aria-label', playing ? 'Mettre en pause' : 'Lancer la lecture');
      bPlay.setAttribute('aria-pressed', playing ? 'true' : 'false');
      bPrev.disabled = i <= 0;
      bNext.disabled = !st.animating && i + 1 >= n;
      bSpeed.firstChild.textContent = 'Vitesse ×' + (st.speed === 0.5 ? '0,5' : st.speed);
      bSpeed.setAttribute('aria-label', 'Vitesse de lecture : ×' + st.speed + ' (changer)');
      var ex = step.explain;
      counter.textContent = 'Étape ' + (Math.max(i, 0) + 1) + ' sur ' + n;
      exTitle.textContent = '';
      inline(exTitle, ex.title);
      exBody.textContent = '';
      ex.body.forEach(function (p) { exBody.appendChild(inline(el('p'), p)); });
      var items = list.children;
      for (var k = 0; k < items.length; k++) {
        var b = items[k].firstChild;
        var active = k === i, done = k < st.shown && k !== i;
        b.classList.toggle('is-active', active);
        b.classList.toggle('is-done', done);
        if (active) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
      }
    }

    /* ---------- événements ---------- */
    bPlay.addEventListener('click', function () {
      var playing = st.mode === 'auto' && !st.paused && (st.animating || !!st.cont);
      if (playing) pause(); else play();
    });
    bPrev.addEventListener('click', prev);
    bNext.addEventListener('click', next);
    bReplay.addEventListener('click', replay);
    bSkip.addEventListener('click', skip);
    bSpeed.addEventListener('click', function () {
      st.speed = SPEEDS[(SPEEDS.indexOf(st.speed) + 1) % SPEEDS.length];
      updateUI();
    });
    copyBtn.addEventListener('click', function () {
      var step = steps()[Math.max(st.i, 0)];
      copyText(step.cmd, function (ok) {
        copyStatus.textContent = ok ? 'Commande copiée' : 'Copie impossible';
        setLabel(copyBtn, ok ? 'Copié' : 'Copie impossible');
        clearTimeout(st.copyTimer);
        st.copyTimer = setTimeout(function () {
          setLabel(copyBtn, 'Copier la commande');
          copyStatus.textContent = '';
        }, 1800);
      });
    });
    var onMq = function (e) { st.instant = e.matches; };
    if (mq.addEventListener) mq.addEventListener('change', onMq);
    else if (mq.addListener) mq.addListener(onMq);

    /* ---------- départ ---------- */
    selectScenario(0, false);
    var io = null;
    if (!st.instant) {
      var go = function () { if (!st.started) start(); };
      if ('IntersectionObserver' in window) {
        io = new IntersectionObserver(function (entries) {
          if (entries.some(function (e) { return e.isIntersecting; })) { io.disconnect(); io = null; go(); }
        }, { threshold: 0.25 });
        io.observe(win);
      } else go();
    }

    return {
      destroy: function () {
        stop();
        if (io) io.disconnect();
        if (mq.removeEventListener) mq.removeEventListener('change', onMq);
        root.textContent = '';
        root.classList.remove('kt');
      }
    };
  }

  window.KwaTerminal = { mount: mount };
})();
