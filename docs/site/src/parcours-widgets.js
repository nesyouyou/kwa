/* Petits simulateurs du parcours « Culture IA générative ». Aucun appel à un modèle : ce sont des ordres de grandeur. */
(function () {
  'use strict';

  function $(s, r) { return (r || document).querySelector(s); }
  function fmt(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }

  /* Estimateur de jetons : deux heuristiques, présentées comme un ordre de grandeur, jamais comme un compte exact. */
  var est = $('#tok-input');
  if (est) {
    var out = $('#tok-out');
    var update = function () {
      var t = est.value, chars = t.length, words = (t.trim().match(/\S+/g) || []).length;
      var a = chars / 4, b = words * 1.3;
      var lo = Math.min(a, b), hi = Math.max(a, b);
      out.innerHTML = '<div><b>' + fmt(chars) + '</b> caractères</div><div><b>' + fmt(words) + '</b> mots</div>' +
        '<div>Ordre de grandeur : <b>' + fmt(lo) + ' à ' + fmt(hi) + '</b> jetons</div>';
    };
    est.addEventListener('input', update);
    update();
  }

  /* Jauge de contexte : tout ce qui entre dans la fenêtre compte, pas seulement votre message. */
  var gauge = $('#ctx-gauge');
  if (gauge) {
    var fields = ['sys', 'rules', 'tools', 'hist', 'files', 'res'];
    var presets = {
      chat: { sys: 1500, rules: 0, tools: 0, hist: 6000, files: 0, res: 0 },
      agent: { sys: 6000, rules: 3000, tools: 12000, hist: 30000, files: 40000, res: 25000 },
      long: { sys: 6000, rules: 3000, tools: 25000, hist: 180000, files: 150000, res: 220000 }
    };
    var win = $('#ctx-win');
    var bar = $('#ctx-bar'), txt = $('#ctx-txt'), msg = $('#ctx-msg');
    var read = function () {
      var total = 0;
      fields.forEach(function (f) { total += Number($('#ctx-' + f).value) || 0; });
      var w = Number(win.value);
      var pct = Math.min(100, total / w * 100);
      bar.style.width = pct + '%';
      txt.textContent = fmt(total) + ' jetons sur ' + fmt(w) + ' (' + Math.round(pct) + ' %)';
      msg.textContent = total > w
        ? 'Ça ne rentre pas : il faut résumer (compaction), repartir d\'une session neuve ou déléguer à un sous-agent.'
        : (pct > 60
          ? 'Beaucoup de place est prise. Plus de contexte n\'est pas mieux : la précision peut baisser quand il grossit. Gardez ce qui sert, déléguez le reste.'
          : 'Il reste de la marge, mais regardez la composition : ce qui est là sans servir coûte quand même.');
    };
    fields.forEach(function (f) { $('#ctx-' + f).addEventListener('input', read); });
    win.addEventListener('change', read);
    document.querySelectorAll('[data-ctx-preset]').forEach(function (b) {
      b.addEventListener('click', function () {
        var p = presets[b.getAttribute('data-ctx-preset')];
        fields.forEach(function (f) { $('#ctx-' + f).value = p[f]; });
        read();
      });
    });
    read();
  }
})();
