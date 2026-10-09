/* Coquille du site : tiroir de navigation sur mobile, repère de la section lue, arborescence. Sans dépendance. */
(function () {
  'use strict';
  var body = document.body;

  /* tiroir de navigation (mobile) */
  var menu = document.getElementById('menu'), scrim = document.getElementById('scrim');
  function setOpen(open) { body.classList.toggle('side-open', open); if (menu) menu.setAttribute('aria-expanded', String(open)); }
  if (menu) menu.addEventListener('click', function () { setOpen(!body.classList.contains('side-open')); });
  if (scrim) scrim.addEventListener('click', function () { setOpen(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
  var side = document.getElementById('side');
  if (side) side.addEventListener('click', function (e) { if (e.target.closest('a')) setOpen(false); });

  /* repère de la section lue */
  var links = Array.prototype.slice.call(document.querySelectorAll('[data-spy]'));
  var targets = links.map(function (a) { return document.getElementById(a.getAttribute('data-spy')); });
  if (links.length && 'IntersectionObserver' in window) {
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) current = en.target.id; });
      if (!current) return;
      links.forEach(function (a) { var on = a.getAttribute('data-spy') === current; a.classList.toggle('is-active', on); if (on) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current'); });
    }, { rootMargin: '-15% 0px -70% 0px' });
    targets.forEach(function (t) { if (t) io.observe(t); });
  }

  /* arborescence */
  var tree = document.getElementById('tree');
  if (!tree) return;
  var tabs = tree.querySelectorAll('[data-tab]');
  Array.prototype.forEach.call(tabs, function (t) {
    t.addEventListener('click', function () {
      Array.prototype.forEach.call(tabs, function (x) { x.setAttribute('aria-selected', String(x === t)); });
      Array.prototype.forEach.call(tree.querySelectorAll('[data-panel]'), function (p) { p.hidden = p.getAttribute('data-panel') !== t.getAttribute('data-tab'); });
    });
  });
  var chips = Array.prototype.slice.call(tree.querySelectorAll('.tr-chip'));
  function filter() {
    var on = {};
    chips.forEach(function (c) { if (c.getAttribute('aria-pressed') === 'true') on[c.getAttribute('data-m')] = true; });
    var panel = tree.querySelector('[data-panel="project"]');
    Array.prototype.forEach.call(panel.querySelectorAll('.tr-file, .tr-dir'), function (n) {
      var mods = (n.getAttribute('data-mod') || '').split(' ');
      n.classList.toggle('tr-off', !mods.some(function (m) { return on[m]; }));
    });
  }
  var note = tree.querySelector('#tr-modnote'), rest = note ? note.textContent : '';
  chips.forEach(function (c) {
    var show = function () { if (note) note.textContent = c.getAttribute('data-m') + ' : ' + c.getAttribute('data-about'); };
    var hide = function () { if (note) note.textContent = rest; };
    c.addEventListener('mouseenter', show); c.addEventListener('focus', show); c.addEventListener('mouseleave', hide); c.addEventListener('blur', hide);
  });
  chips.forEach(function (c) { c.addEventListener('click', function () { c.setAttribute('aria-pressed', String(c.getAttribute('aria-pressed') !== 'true')); filter(); }); });
  tree.addEventListener('click', function (e) {
    var b = e.target.closest('[data-act]');
    if (!b) return;
    Array.prototype.forEach.call(tree.querySelectorAll('.tr-dir'), function (d) { d.open = b.getAttribute('data-act') === 'open'; });
  });
})();
