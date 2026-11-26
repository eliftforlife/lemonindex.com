// 11-25 year page top v2 (year_ux.py): the "See where the score comes from" sheet closes with Done, Escape or a tap outside it.
(function () {
  var d = document.querySelector('details.yux-src'); if (!d) return;
  function close() { d.open = false; }
  var x = d.querySelector('.yux-x'); if (x) x.addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && d.open) { close(); d.querySelector('summary').focus(); } });
  document.addEventListener('click', function (e) { if (d.open && !d.contains(e.target)) close(); });
})();
