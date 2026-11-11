// 11-10: BMW engines hub (11-11: also the supercar engines hub: 12 / hy pills, recalls and maker sorts). Every engine card is in the HTML; this only filters (pills) and sorts (select).
(function () {
  var g = document.querySelector('.ehub-g'); if (!g) return;
  var cards = Array.prototype.slice.call(g.querySelectorAll('.ehc'));
  var pills = document.querySelectorAll('.ehub-p'), sel = document.getElementById('ehub-sort'), cnt = document.querySelector('.ehub-c');
  var f = 'all';
  function keep(c) {
    var d = c.dataset;
    if (f === 'all') return true;
    if (f === '4' || f === '6' || f === '8' || f === '12') return d.cyl === f;
    if (f === 'hy') return d.hy === '1';
    if (f === 'm') return d.m === '1';
    if (f === 'turbo') return d.turbo === '1';
    if (f === 'na') return d.turbo === '0';
    return true;
  }
  var by = {
    own: function (a, b) { return (+a.dataset.rank - +b.dataset.rank) || (+a.dataset.y0 - +b.dataset.y0); },
    new: function (a, b) { return +b.dataset.y0 - +a.dataset.y0; },
    old: function (a, b) { return +a.dataset.y0 - +b.dataset.y0; },
    yt: function (a, b) { return +b.dataset.yt - +a.dataset.yt; },
    rec: function (a, b) { return +b.dataset.rec - +a.dataset.rec; },
    mk: function (a, b) { return a.dataset.mk.localeCompare(b.dataset.mk) || (+a.dataset.y0 - +b.dataset.y0); }
  };
  function draw() {
    var n = 0;
    cards.slice().sort(by[sel ? sel.value : 'own'] || by.own).forEach(function (c) {
      var on = keep(c); c.hidden = !on; if (on) n++; g.appendChild(c);
    });
    if (cnt) cnt.textContent = n + (n === 1 ? ' engine' : ' engines');
  }
  Array.prototype.forEach.call(pills, function (p) {
    p.addEventListener('click', function () {
      f = p.getAttribute('data-f');
      Array.prototype.forEach.call(pills, function (q) { q.setAttribute('aria-pressed', q === p ? 'true' : 'false'); });
      draw();
    });
  });
  if (sel) sel.addEventListener('change', draw);
})();
