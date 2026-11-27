// 11-25 year page top v2 (year_ux.py): the "See where the score comes from" sheet closes with Done, Escape or a tap outside it.
(function () {
  var d = document.querySelector('details.yux-src'); if (!d) return;
  function close() { d.open = false; }
  var x = d.querySelector('.yux-x'); if (x) x.addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && d.open) { close(); d.querySelector('summary').focus(); } });
  document.addEventListener('click', function (e) { if (d.open && !d.contains(e.target)) close(); });
})();
// 11-27 "Better years to buy": the (i) by the heading shows / hides the one-line note on what the chip numbers are
(function () {
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.yux-ib'); if (!b) return;
    var n = document.getElementById(b.getAttribute('aria-controls')); if (!n) return;
    var on = b.getAttribute('aria-expanded') !== 'true';
    b.setAttribute('aria-expanded', on ? 'true' : 'false'); n.hidden = !on;
  });
})();
