/* Carte interactive de Kwa. Sans dépendance : SVG + JS vanilla. Expose window.KwaMap.mount(root, data).
   Fonctions : zoom/déplacement, minimap, recherche (Ctrl/Cmd+K), panneau de détail, plongée dans une skill (double-clic),
   fil d'Ariane, liens profonds #view=…&node=…, export SVG/PNG, clavier. */
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var KIND_LABEL = { skill: 'Skill', agent: 'Sous-agent', hook: 'Hook', garde: 'Garde', humain: 'Toi', policy: 'Politique', step: 'Étape' };
  var EDGE_LABEL = { calls: 'appelle', feeds: 'alimente', loop: 'reboucle' };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function s(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function h(tag, attrs, html) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) { if (k === 'class') e.className = attrs[k]; else e.setAttribute(k, attrs[k]); }
    if (html != null) e.innerHTML = html;
    return e;
  }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function wrap(text, max, lines) {
    var words = String(text || '').split(/\s+/), out = [], cur = '';
    for (var i = 0; i < words.length; i++) {
      if ((cur + ' ' + words[i]).trim().length > max) { out.push(cur); cur = words[i]; if (out.length === lines) break; }
      else cur = (cur + ' ' + words[i]).trim();
    }
    if (out.length < lines && cur) out.push(cur);
    var truncated = out.length === lines && (words.join(' ').length > out.join(' ').length + 2);
    if (truncated) out[lines - 1] = out[lines - 1].replace(/[\s,.;:]+$/, '').slice(0, max - 1) + '…';
    return out.slice(0, lines);
  }

  function mount(root, data) {
    var G = data.grid, W = G.w, H = G.h;
    var state = { view: data.start, sel: null, cam: { x: 0, y: 0, k: 1 }, depth: [] };
    var el = {};

    root.classList.add('km');
    root.innerHTML = '';
    var bar = h('div', { class: 'km-bar' });
    el.menuBtn = h('button', { class: 'km-ico', type: 'button', 'aria-label': 'Vues', 'aria-haspopup': 'true' }, '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>');
    el.title = h('div', { class: 'km-title' });
    el.search = h('input', { class: 'km-search', type: 'search', placeholder: 'Chercher un nœud…', 'aria-label': 'Chercher un nœud' });
    el.kbd = h('kbd', { class: 'km-kbd' }, 'Ctrl K');
    el.exportBtn = h('button', { class: 'km-btn', type: 'button', 'aria-haspopup': 'true' }, 'Exporter ▾');
    el.help = h('button', { class: 'km-ico km-ico--text', type: 'button', 'aria-label': 'Aide clavier' }, '?');
    var sw = h('div', { class: 'km-searchwrap' }); sw.appendChild(el.search); sw.appendChild(el.kbd);
    bar.appendChild(el.menuBtn); bar.appendChild(el.title); bar.appendChild(sw); bar.appendChild(el.exportBtn); bar.appendChild(el.help);
    root.appendChild(bar);

    el.crumbs = h('div', { class: 'km-crumbs', 'aria-label': 'Fil d’Ariane' });
    root.appendChild(el.crumbs);

    var stage = h('div', { class: 'km-stage' });
    el.svg = s('svg', { class: 'km-svg', role: 'img', 'aria-label': 'Carte des skills Kwa', tabindex: '0' });
    var defs = s('defs', {}, el.svg);
    ['calls', 'loop', 'feeds'].forEach(function (k) {
      var m = s('marker', { id: 'kma-' + k, viewBox: '0 0 10 10', refX: '9', refY: '5', markerWidth: '7', markerHeight: '7', orient: 'auto-start-reverse' }, defs);
      s('path', { d: 'M1 1 L9 5 L1 9', class: 'km-arrow km-arrow--' + k }, m);
    });
    el.world = s('g', { class: 'km-world' }, el.svg);
    el.gGroups = s('g', {}, el.world); el.gEdges = s('g', {}, el.world); el.gNodes = s('g', {}, el.world);
    stage.appendChild(el.svg);

    el.panel = h('aside', { class: 'km-panel', hidden: '', 'aria-live': 'polite' });
    stage.appendChild(el.panel);
    el.legend = h('div', { class: 'km-legend' });
    var lh = '<b>Légende</b>';
    Object.keys(data.kinds).forEach(function (k) { lh += '<span><i class="km-sw km-sw--' + k + '"></i>' + KIND_LABEL[k] + '</span>'; });
    lh += '<span><i class="km-sw km-sw--av"></i>Avatar : d’où vient l’idée</span><span class="km-lg-line"><i></i>appelle</span><span class="km-lg-line km-lg-line--loop"><i></i>reboucle</span>';
    el.legend.innerHTML = lh;
    el.mini = h('div', { class: 'km-mini', 'aria-hidden': 'true' }); el.miniSvg = s('svg', {}); el.mini.appendChild(el.miniSvg); stage.appendChild(el.mini);
    el.zoom = h('div', { class: 'km-zoom' },
      '<button type="button" data-z="out" aria-label="Dézoomer">−</button><output aria-live="off">100 %</output><button type="button" data-z="in" aria-label="Zoomer">+</button><button type="button" data-z="fit" aria-label="Tout voir">Ajuster</button><button type="button" data-z="one" aria-label="Taille réelle">1:1</button>');
    stage.appendChild(el.zoom);
    el.hint = h('div', { class: 'km-hint' }, 'molette = zoom · glisser = déplacer · double-clic = ouvrir · Ctrl K = chercher · ? = aide');
    stage.appendChild(el.hint);
    el.menu = h('div', { class: 'km-menu', hidden: '', role: 'menu' }); stage.appendChild(el.menu);
    el.exmenu = h('div', { class: 'km-menu km-menu--right', hidden: '', role: 'menu' }, '<button type="button" role="menuitem" data-ex="svg">SVG</button><button type="button" role="menuitem" data-ex="png">PNG</button>'); stage.appendChild(el.exmenu);
    el.results = h('div', { class: 'km-results', hidden: '', role: 'listbox' }); stage.appendChild(el.results);
    el.helpbox = h('div', { class: 'km-helpbox', hidden: '' }, '<b>Clavier</b><dl><dt>Molette</dt><dd>zoom</dd><dt>Glisser</dt><dd>déplacer</dd><dt>+ −</dt><dd>zoomer, dézoomer</dd><dt>0</dt><dd>tout voir</dd><dt>1</dt><dd>taille réelle</dd><dt>Flèches</dt><dd>déplacer</dd><dt>Ctrl K</dt><dd>chercher</dd><dt>Entrée</dt><dd>ouvrir la skill sélectionnée</dd><dt>Échap</dt><dd>fermer, remonter</dd></dl>');
    stage.appendChild(el.helpbox);
    root.insertBefore(el.legend, null);
    root.appendChild(stage);
    el.stage = stage;

    /* ---------- vues ---------- */
    function node(id) { return data.nodes[id]; }
    function view() { return data.views[state.view]; }
    function placed(id) { var v = view(); for (var i = 0; i < v.nodes.length; i++) if (v.nodes[i].id === id) return v.nodes[i]; return null; }
    function related(id) {
      var up = {}, down = {};
      Object.keys(data.views).forEach(function (vk) {
        data.views[vk].edges.forEach(function (e) {
          if (e.to === id && e.kind !== 'loop') up[e.from] = 1;
          if (e.from === id && e.kind !== 'loop') down[e.to] = 1;
        });
      });
      Object.keys(data.nodes).forEach(function (k) {
        var n = data.nodes[k];
        if (n.kind === 'skill' && n.refs.indexOf(id) >= 0 && k !== id) up[k] = up[k] || 2;
      });
      (node(id).refs || []).forEach(function (r) { down[r] = down[r] || 2; });
      return { up: Object.keys(up).filter(function (k) { return data.nodes[k]; }), down: Object.keys(down).filter(function (k) { return data.nodes[k]; }) };
    }

    function route(a, b, kind) {
      var ax = a.x, ay = a.y, bx = b.x, by = b.y, pts;
      var aR = ax + W, aB = ay + H, bR = bx + W, bB = by + H, acx = ax + W / 2, bcx = bx + W / 2, acy = ay + H / 2, bcy = by + H / 2;
      if (kind === 'loop') {
        var yb = Math.max(aB, bB) + 34;
        pts = [[acx, aB], [acx, yb], [bcx, yb], [bcx, bB]];
        if (Math.abs(ay - by) > H) { pts = [[ax, acy], [ax - 22, acy], [ax - 22, bcy], [bx, bcy]]; if (bx > ax) pts = [[aR, acy], [aR + 22, acy], [aR + 22, bcy], [bR, bcy]]; }
      } else if (Math.abs(ay - by) < 4 && bx > ax) pts = [[aR, acy], [bx, bcy]];
      else if (Math.abs(ax - bx) < 4) pts = by > ay ? [[acx, aB], [bcx, by]] : [[acx, ay], [bcx, bB]];
      else if (bx > aR - 4) { var mx = (aR + bx) / 2; pts = [[aR, acy], [mx, acy], [mx, bcy], [bx, bcy]]; }
      else if (by > ay) { var my = (aB + by) / 2; pts = [[acx, aB], [acx, my], [bcx, my], [bcx, by]]; }
      else { var my2 = (ay + bB) / 2; pts = [[acx, ay], [acx, my2], [bcx, my2], [bcx, bB]]; }
      return pts;
    }
    function rounded(pts, r) {
      var d = 'M' + pts[0][0] + ' ' + pts[0][1];
      for (var i = 1; i < pts.length - 1; i++) {
        var p0 = pts[i - 1], p1 = pts[i], p2 = pts[i + 1];
        var l1 = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]), l2 = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
        var rr = Math.min(r, l1 / 2, l2 / 2);
        var a = [p1[0] - (p1[0] - p0[0]) / l1 * rr, p1[1] - (p1[1] - p0[1]) / l1 * rr];
        var b = [p1[0] + (p2[0] - p1[0]) / l2 * rr, p1[1] + (p2[1] - p1[1]) / l2 * rr];
        d += ' L' + a[0] + ' ' + a[1] + ' Q' + p1[0] + ' ' + p1[1] + ' ' + b[0] + ' ' + b[1];
      }
      var last = pts[pts.length - 1];
      return d + ' L' + last[0] + ' ' + last[1];
    }

    function drawNode(p) {
      var n = node(p.id); if (!n) return null;
      var g = s('g', { class: 'km-node km-node--' + n.kind, 'data-id': n.id, transform: 'translate(' + p.x + ' ' + p.y + ')', tabindex: '0', role: 'button', 'aria-label': KIND_LABEL[n.kind] + ' ' + n.label });
      if (n.child) { s('rect', { class: 'km-stackrect', x: 6, y: 6, width: W, height: H, rx: 12 }, g); }
      var r = n.kind === 'humain' ? H / 2 : 12;
      s('rect', { class: 'km-box', width: W, height: H, rx: r }, g);
      if (n.kind === 'agent') s('rect', { class: 'km-box km-box--inner', x: 4, y: 4, width: W - 8, height: H - 8, rx: 9 }, g);
      if (n.kind === 'garde') s('line', { class: 'km-bar4', x1: 2.5, y1: 12, x2: 2.5, y2: H - 12 }, g);
      var padX = n.kind === 'humain' ? 26 : 16;
      var t = s('text', { class: 'km-kind', x: padX, y: 20 }, g); t.textContent = KIND_LABEL[n.kind].toUpperCase();
      var lab = n.label.length > 24 ? n.label.slice(0, 23) + '…' : n.label;
      var l = s('text', { class: 'km-label', x: padX, y: 41 }, g); l.textContent = lab;
      var lines = wrap(n.what, n.kind === 'humain' ? 30 : 34, 2);
      lines.forEach(function (ln, i) { var sub = s('text', { class: 'km-sub', x: padX, y: 59 + i * 14 }, g); sub.textContent = ln; });
      var origins = (n.origin || []).filter(function (o) { return o !== 'kwa'; });
      origins.slice(0, 3).forEach(function (o, i) {
        var od = data.origins[o]; if (!od) return;
        var cx = W - 20 - i * 15, cy = 18;
        var id = 'kc-' + n.id.replace(/[^a-z0-9]/gi, '_') + i;
        var cp = s('clipPath', { id: id }, g); s('circle', { cx: cx, cy: cy, r: 11 }, cp);
        s('image', { href: od.avatar, x: cx - 11, y: cy - 11, width: 22, height: 22, 'clip-path': 'url(#' + id + ')', preserveAspectRatio: 'xMidYMid slice' }, g);
        s('circle', { class: 'km-avring', cx: cx, cy: cy, r: 11 }, g);
      });
      if (origins.length) { var hd = s('text', { class: 'km-handle', x: W - 16, y: H - 8, 'text-anchor': 'end' }, g); hd.textContent = (data.origins[origins[0]] || {}).handle || ''; }
      if (n.child) { var st = s('text', { class: 'km-open', x: padX, y: H - 8 }, g); st.textContent = '⤢ étapes'; }
      g.addEventListener('click', function (ev) { ev.stopPropagation(); select(n.id); });
      g.addEventListener('dblclick', function (ev) { ev.stopPropagation(); if (n.child) openView(n.child); });
      g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); if (state.sel === n.id && n.child) openView(n.child); else select(n.id); } });
      return g;
    }

    function render(keepCam) {
      var v = view();
      el.gGroups.innerHTML = ''; el.gEdges.innerHTML = ''; el.gNodes.innerHTML = '';
      (v.groups || []).forEach(function (gr) {
        s('rect', { class: 'km-group', x: gr.x, y: gr.y, width: gr.w, height: gr.h, rx: 20 }, el.gGroups);
        var t = s('text', { class: 'km-grouplabel', x: gr.x + 18, y: gr.y + 24 }, el.gGroups); t.textContent = gr.label.toUpperCase();
      });
      v.edges.forEach(function (e) {
        var a = placed(e.from), b = placed(e.to); if (!a || !b) return;
        var pts = route(a, b, e.kind);
        var p = s('path', { class: 'km-edge km-edge--' + e.kind, d: rounded(pts, 10), 'marker-end': 'url(#kma-' + e.kind + ')', 'data-from': e.from, 'data-to': e.to }, el.gEdges);
        if (e.label) { var mid = pts[Math.floor(pts.length / 2)]; var lt = s('text', { class: 'km-edgelabel', x: (pts[1] || mid)[0] + 6, y: (pts[1] || mid)[1] - 6 }, el.gEdges); lt.textContent = e.label; }
      });
      v.nodes.forEach(function (p) { var g = drawNode(p); if (g) el.gNodes.appendChild(g); });
      /* un nom trop long est comprimé pour tenir dans son nœud (mesure réelle du texte) */
      el.gNodes.querySelectorAll('.km-label').forEach(function (t) {
        try {
          var max = t.closest('.km-node--humain') ? W - 52 : W - 32;
          if (t.getComputedTextLength() > max) { t.setAttribute('textLength', max); t.setAttribute('lengthAdjust', 'spacingAndGlyphs'); }
        } catch (e) { /* texte non rendu */ }
      });
      var crumbs = '<button type="button" data-v="pack">Le pack Kwa</button>';
      if (state.view !== 'pack') crumbs += '<span>›</span><b>' + esc(v.title) + '</b>';
      el.crumbs.innerHTML = crumbs + '<p class="km-intro">' + esc(v.intro || '') + '</p>';
      el.title.innerHTML = '<i class="km-dot"></i><b>' + esc(v.title) + '</b><span class="km-pill">' + v.nodes.length + ' nœuds</span>';
      el.menu.innerHTML = Object.keys(data.views).filter(function (k) { return k.indexOf('skill:') !== 0; }).map(function (k) {
        return '<button type="button" role="menuitem" data-v="' + k + '"' + (k === state.view ? ' aria-current="true"' : '') + '>' + esc(data.views[k].title) + '<small>' + data.views[k].nodes.length + '</small></button>';
      }).join('');
      if (!keepCam) fit(false);
      applySel(); drawMini(); hash();
    }

    /* ---------- caméra ---------- */
    function bbox() {
      var v = view(), x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      v.nodes.forEach(function (p) { x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y); x1 = Math.max(x1, p.x + W + 8); y1 = Math.max(y1, p.y + H + 8); });
      (v.groups || []).forEach(function (g) { x0 = Math.min(x0, g.x); y0 = Math.min(y0, g.y); x1 = Math.max(x1, g.x + g.w); y1 = Math.max(y1, g.y + g.h); });
      v.edges.forEach(function (e) { if (e.kind === 'loop') y1 += 24; });
      return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
    }
    function size() { var r = el.svg.getBoundingClientRect(); return { w: r.width, h: r.height }; }
    function setCam(c, animate) {
      state.cam = c;
      el.world.style.transition = animate && !reduce ? 'transform .5s cubic-bezier(.22,1,.36,1)' : 'none';
      el.world.style.transform = 'translate(' + c.x + 'px,' + c.y + 'px) scale(' + c.k + ')';
      el.svg.classList.toggle('km-far', c.k < 0.62);
      el.zoom.querySelector('output').textContent = Math.round(c.k * 100) + ' %';
      drawViewport();
    }
    function fit(animate) {
      var b = bbox(), sz = size(), pad = sz.w < 700 ? 16 : 40;
      var k = Math.min((sz.w - pad * 2) / b.w, (sz.h - pad * 2) / b.h, 1.15);
      setCam({ k: k, x: (sz.w - b.w * k) / 2 - b.x * k, y: (sz.h - b.h * k) / 2 - b.y * k }, animate);
    }
    function zoomAt(f, cx, cy, animate) {
      var c = state.cam, k = Math.max(0.12, Math.min(2.6, c.k * f)); f = k / c.k;
      setCam({ k: k, x: cx - (cx - c.x) * f, y: cy - (cy - c.y) * f }, animate);
    }
    function center(id) {
      var p = placed(id); if (!p) return;
      var sz = size(), k = Math.max(state.cam.k, 0.9), panel = sz.w > 760 && !el.panel.hidden ? 160 : 0;
      setCam({ k: k, x: sz.w / 2 - panel - (p.x + W / 2) * k, y: sz.h / 2 - (p.y + H / 2) * k }, true);
    }

    el.stage.addEventListener('wheel', function (ev) {
      if (!ev.target.closest('.km-svg')) return;
      ev.preventDefault();
      var r = el.svg.getBoundingClientRect();
      zoomAt(Math.exp(-ev.deltaY * (ev.ctrlKey ? 0.01 : 0.0016)), ev.clientX - r.left, ev.clientY - r.top, false);
    }, { passive: false });
    var drag = null;
    el.svg.addEventListener('pointerdown', function (ev) {
      if (ev.target.closest('.km-node')) return;
      drag = { x: ev.clientX, y: ev.clientY, cx: state.cam.x, cy: state.cam.y, moved: false };
      el.svg.setPointerCapture(ev.pointerId); el.svg.classList.add('km-grab');
    });
    el.svg.addEventListener('pointermove', function (ev) {
      if (!drag) return;
      var dx = ev.clientX - drag.x, dy = ev.clientY - drag.y; if (Math.abs(dx) + Math.abs(dy) > 3) drag.moved = true;
      setCam({ k: state.cam.k, x: drag.cx + dx, y: drag.cy + dy }, false);
    });
    function endDrag() { if (drag && !drag.moved) select(null); drag = null; el.svg.classList.remove('km-grab'); }
    el.svg.addEventListener('pointerup', endDrag); el.svg.addEventListener('pointercancel', endDrag);
    el.zoom.addEventListener('click', function (ev) {
      var b = ev.target.closest('button'); if (!b) return; var sz = size(), z = b.dataset.z;
      if (z === 'in') zoomAt(1.25, sz.w / 2, sz.h / 2, true); else if (z === 'out') zoomAt(0.8, sz.w / 2, sz.h / 2, true);
      else if (z === 'fit') fit(true); else if (z === 'one') zoomAt(1 / state.cam.k, sz.w / 2, sz.h / 2, true);
    });

    /* ---------- minimap ---------- */
    var MW = 168, MH = 100, mscale = 1, mox = 0, moy = 0, vp;
    function drawMini() {
      var b = bbox(); mscale = Math.min((MW - 8) / b.w, (MH - 8) / b.h); mox = 4 - b.x * mscale + (MW - 8 - b.w * mscale) / 2; moy = 4 - b.y * mscale + (MH - 8 - b.h * mscale) / 2;
      el.miniSvg.setAttribute('viewBox', '0 0 ' + MW + ' ' + MH); el.miniSvg.innerHTML = '';
      (view().groups || []).forEach(function (g) { s('rect', { class: 'km-mg', x: g.x * mscale + mox, y: g.y * mscale + moy, width: g.w * mscale, height: g.h * mscale, rx: 3 }, el.miniSvg); });
      view().nodes.forEach(function (p) { s('rect', { class: 'km-mn km-mn--' + (node(p.id) || {}).kind, x: p.x * mscale + mox, y: p.y * mscale + moy, width: W * mscale, height: H * mscale, rx: 2 }, el.miniSvg); });
      vp = s('rect', { class: 'km-mv', rx: 2 }, el.miniSvg); drawViewport();
    }
    function drawViewport() {
      if (!vp) return; var sz = size(), c = state.cam;
      vp.setAttribute('x', (-c.x / c.k) * mscale + mox); vp.setAttribute('y', (-c.y / c.k) * mscale + moy);
      vp.setAttribute('width', (sz.w / c.k) * mscale); vp.setAttribute('height', (sz.h / c.k) * mscale);
    }
    function miniMove(ev) {
      var r = el.miniSvg.getBoundingClientRect(), sz = size(), k = state.cam.k;
      var wx = ((ev.clientX - r.left) * (MW / r.width) - mox) / mscale, wy = ((ev.clientY - r.top) * (MH / r.height) - moy) / mscale;
      setCam({ k: k, x: sz.w / 2 - wx * k, y: sz.h / 2 - wy * k }, false);
    }
    var mdrag = false;
    el.mini.addEventListener('pointerdown', function (ev) { mdrag = true; el.mini.setPointerCapture(ev.pointerId); miniMove(ev); });
    el.mini.addEventListener('pointermove', function (ev) { if (mdrag) miniMove(ev); });
    el.mini.addEventListener('pointerup', function () { mdrag = false; });

    /* ---------- sélection et panneau ---------- */
    function chip(id) { var n = node(id); if (!n) return ''; return '<button type="button" class="km-chip" data-go="' + esc(id) + '">' + esc(n.label) + '</button>'; }
    function select(id) {
      state.sel = id; applySel();
      if (!id) { el.panel.hidden = true; hash(); return; }
      var n = node(id), rel = related(id), od = (n.origin || []).filter(function (o) { return o !== 'kwa'; });
      var html = '<button type="button" class="km-x" aria-label="Fermer">×</button><div class="km-kindtag">' + KIND_LABEL[n.kind] + '</div><h3>' + esc(n.label) + '</h3>';
      if (n.what) html += '<h4>Quoi</h4><p>' + esc(n.what) + '</p>';
      if (n.when) html += '<h4>Quand</h4><p>' + esc(n.when) + '</p>';
      if (n.how) html += '<h4>Comment</h4><p>' + esc(n.how) + '</p>';
      if (od.length) html += '<h4>Origine</h4>' + od.map(function (o) { var d = data.origins[o]; return '<a class="km-origin" href="' + esc(d.url) + '" target="_blank" rel="noopener noreferrer"><img src="' + esc(d.avatar) + '" alt="" width="28" height="28"><span><b>' + esc(d.name) + '</b><small>' + esc(d.handle) + ' · ' + esc(d.license) + (d.ref ? ' · ' + esc(d.ref) : '') + '</small></span></a>'; }).join('') + '<p class="km-note">Idées reprises, textes réécrits pour Kwa.</p>';
      else if (n.kind === 'skill') html += '<h4>Origine</h4><p>Conception propre à Kwa.</p>';
      if (n.source && n.source.length) html += '<h4>Source</h4><ul class="km-src">' + n.source.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>';
      if (rel.up.length) html += '<h4>En amont</h4><div class="km-chips">' + rel.up.map(chip).join('') + '</div>';
      if (rel.down.length) html += '<h4>En aval</h4><div class="km-chips">' + rel.down.map(chip).join('') + '</div>';
      if (n.child) html += '<button type="button" class="km-open-btn" data-open="' + esc(n.child) + '">Ouvrir les étapes ⤢</button>';
      el.panel.innerHTML = html; el.panel.hidden = false; el.panel.scrollTop = 0; hash();
    }
    function applySel() {
      var sel = state.sel, rel = sel && node(sel) ? related(sel) : null;
      var near = {}; if (rel) { near[sel] = 1; rel.up.concat(rel.down).forEach(function (k) { near[k] = 1; }); }
      el.gNodes.querySelectorAll('.km-node').forEach(function (g) {
        var id = g.getAttribute('data-id');
        g.classList.toggle('is-sel', id === sel); g.classList.toggle('is-dim', !!sel && !near[id]);
      });
      el.gEdges.querySelectorAll('.km-edge').forEach(function (p) {
        var on = !!sel && (p.getAttribute('data-from') === sel || p.getAttribute('data-to') === sel);
        p.classList.toggle('is-on', on); p.classList.toggle('is-dim', !!sel && !on);
      });
    }
    el.panel.addEventListener('click', function (ev) {
      if (ev.target.closest('.km-x')) { select(null); return; }
      var go = ev.target.closest('[data-go]'); if (go) { focusNode(go.dataset.go); return; }
      var op = ev.target.closest('[data-open]'); if (op) openView(op.dataset.open);
    });

    function openView(vid) { if (!data.views[vid]) return; state.view = vid; state.sel = null; el.panel.hidden = true; render(false); el.svg.focus({ preventScroll: true }); }
    function focusNode(id) {
      if (!placed(id)) {
        var found = Object.keys(data.views).filter(function (k) { return k.indexOf('skill:') !== 0 && data.views[k].nodes.some(function (p) { return p.id === id; }); })[0] ||
                    Object.keys(data.views).filter(function (k) { return data.views[k].nodes.some(function (p) { return p.id === id; }); })[0];
        if (!found) return; state.view = found; render(false);
      }
      select(id); center(id);
    }

    /* ---------- menus, recherche, export, aide ---------- */
    function toggle(m, on) { m.hidden = on === undefined ? !m.hidden : !on; }
    el.menuBtn.addEventListener('click', function (ev) { ev.stopPropagation(); toggle(el.exmenu, false); toggle(el.menu); });
    el.exportBtn.addEventListener('click', function (ev) { ev.stopPropagation(); toggle(el.menu, false); toggle(el.exmenu); });
    el.help.addEventListener('click', function (ev) { ev.stopPropagation(); toggle(el.helpbox); });
    el.menu.addEventListener('click', function (ev) { var b = ev.target.closest('[data-v]'); if (b) { toggle(el.menu, false); openView(b.dataset.v); } });
    el.crumbs.addEventListener('click', function (ev) { var b = ev.target.closest('[data-v]'); if (b) openView(b.dataset.v); });
    el.exmenu.addEventListener('click', function (ev) { var b = ev.target.closest('[data-ex]'); if (b) { toggle(el.exmenu, false); doExport(b.dataset.ex); } });
    document.addEventListener('click', function (ev) { if (!root.contains(ev.target) || !ev.target.closest('.km-menu,.km-helpbox,.km-btn,.km-ico')) { toggle(el.menu, false); toggle(el.exmenu, false); toggle(el.results, false); if (!ev.target.closest('.km-help,.km-ico--text')) toggle(el.helpbox, false); } });

    function searchAll(q) {
      q = q.toLowerCase(); var seen = {}, out = [];
      Object.keys(data.nodes).forEach(function (k) {
        var n = data.nodes[k]; if (n.kind === 'step') return;
        if ((n.label + ' ' + (n.what || '')).toLowerCase().indexOf(q) >= 0 && !seen[k]) { seen[k] = 1; out.push(n); }
      });
      return out.slice(0, 7);
    }
    el.search.addEventListener('input', function () {
      var q = el.search.value.trim(); if (!q) { toggle(el.results, false); return; }
      var r = searchAll(q);
      el.results.innerHTML = r.length ? r.map(function (n) { return '<button type="button" role="option" data-go="' + esc(n.id) + '"><i class="km-sw km-sw--' + n.kind + '"></i><b>' + esc(n.label) + '</b><small>' + KIND_LABEL[n.kind] + '</small></button>'; }).join('') : '<p>Aucun résultat.</p>';
      toggle(el.results, true);
    });
    el.search.addEventListener('keydown', function (ev) { if (ev.key === 'Enter') { var f = el.results.querySelector('[data-go]'); if (f) { focusNode(f.dataset.go); toggle(el.results, false); el.search.blur(); } } if (ev.key === 'Escape') { el.search.value = ''; toggle(el.results, false); el.search.blur(); } });
    el.results.addEventListener('click', function (ev) { var b = ev.target.closest('[data-go]'); if (b) { focusNode(b.dataset.go); toggle(el.results, false); } });

    root.addEventListener('keydown', function (ev) {
      if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === 'k') { ev.preventDefault(); el.search.focus(); return; }
      if (ev.target === el.search) return;
      var sz = size(), k = ev.key;
      if (k === '+' || k === '=') zoomAt(1.2, sz.w / 2, sz.h / 2, true);
      else if (k === '-') zoomAt(0.83, sz.w / 2, sz.h / 2, true);
      else if (k === '0') fit(true);
      else if (k === '1') zoomAt(1 / state.cam.k, sz.w / 2, sz.h / 2, true);
      else if (k === '?') toggle(el.helpbox);
      else if (k === 'Escape') { if (!el.helpbox.hidden) toggle(el.helpbox, false); else if (state.sel) select(null); else if (state.view !== 'pack') openView('pack'); }
      else if (k.indexOf('Arrow') === 0 && ev.target === el.svg) { ev.preventDefault(); var d = 60; setCam({ k: state.cam.k, x: state.cam.x + (k === 'ArrowLeft' ? d : k === 'ArrowRight' ? -d : 0), y: state.cam.y + (k === 'ArrowUp' ? d : k === 'ArrowDown' ? -d : 0) }, false); }
    });

    function cssText() {
      var rules = [];
      for (var i = 0; i < document.styleSheets.length; i++) { try { var cr = document.styleSheets[i].cssRules; for (var j = 0; j < cr.length; j++) if (cr[j].cssText.indexOf('.km-') >= 0 && cr[j].cssText.indexOf('.km-svg') >= 0 || /\.km-(node|edge|group|arrow|box|kind|label|sub|handle|open|bar4|edgelabel|stackrect|avring)/.test(cr[j].cssText)) rules.push(cr[j].cssText); } catch (e) { /* feuille externe */ } }
      var cs = getComputedStyle(root), out = rules.join('\n');
      return out.replace(/var\((--[a-z0-9-]+)\)/gi, function (_, v) { return cs.getPropertyValue(v).trim() || '#000'; });
    }
    function doExport(kind) {
      var b = bbox(), pad = 24, clone = el.svg.cloneNode(true);
      clone.setAttribute('xmlns', NS); clone.setAttribute('width', b.w + pad * 2); clone.setAttribute('height', b.h + pad * 2);
      clone.setAttribute('viewBox', [b.x - pad, b.y - pad, b.w + pad * 2, b.h + pad * 2].join(' ')); clone.removeAttribute('class'); clone.removeAttribute('tabindex');
      var world = clone.querySelector('.km-world'); world.removeAttribute('style');
      var bg = s('rect', { x: b.x - pad, y: b.y - pad, width: b.w + pad * 2, height: b.h + pad * 2, fill: getComputedStyle(root).getPropertyValue('--nkui-bg').trim() || '#fff' });
      clone.insertBefore(bg, clone.firstChild);
      var st = s('style'); st.textContent = cssText() + '\ntext{font-family:Geist,Arial,sans-serif}'; clone.insertBefore(st, clone.firstChild);
      var xml = new XMLSerializer().serializeToString(clone), name = 'kwa-' + state.view.replace(':', '-');
      function dl(blob, fn) { var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = fn; document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000); }
      if (kind === 'svg') { dl(new Blob([xml], { type: 'image/svg+xml' }), name + '.svg'); return; }
      var img = new Image(), url = URL.createObjectURL(new Blob([xml], { type: 'image/svg+xml' }));
      img.onload = function () {
        var cv = document.createElement('canvas'); cv.width = (b.w + pad * 2) * 2; cv.height = (b.h + pad * 2) * 2;
        var ctx = cv.getContext('2d'); ctx.scale(2, 2); ctx.drawImage(img, 0, 0, b.w + pad * 2, b.h + pad * 2);
        try { cv.toBlob(function (bl) { if (bl) dl(bl, name + '.png'); }); } catch (e) { dl(new Blob([xml], { type: 'image/svg+xml' }), name + '.svg'); }
        URL.revokeObjectURL(url);
      };
      img.onerror = function () { dl(new Blob([xml], { type: 'image/svg+xml' }), name + '.svg'); };
      img.src = url;
    }

    /* ---------- lien profond ---------- */
    function hash() {
      if (!root.hasAttribute('data-deeplink')) return;
      var q = '#view=' + encodeURIComponent(state.view) + (state.sel ? '&node=' + encodeURIComponent(state.sel) : '');
      try { history.replaceState(null, '', q); } catch (e) { /* file:// */ }
    }
    function fromHash() {
      if (!root.hasAttribute('data-deeplink')) return false;
      var m = /view=([^&]+)/.exec(location.hash), n = /node=([^&]+)/.exec(location.hash);
      if (m && data.views[decodeURIComponent(m[1])]) { state.view = decodeURIComponent(m[1]); }
      return n ? decodeURIComponent(n[1]) : null;
    }

    var ro = window.ResizeObserver ? new ResizeObserver(function () { drawViewport(); }) : null; if (ro) ro.observe(el.svg);
    var pending = fromHash();
    render(false);
    if (pending && node(pending)) focusNode(pending);
    window.addEventListener('resize', function () { fit(false); });
    return { openView: openView, focusNode: focusNode, fit: fit };
  }

  window.KwaMap = { mount: mount };
})();
