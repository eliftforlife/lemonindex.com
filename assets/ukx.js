// 11-15 UK MOT pass rates hub (uk_pages.py): filter the model table by text and kind, and sort it by any column.
// Without JS the table shows every model in test-count order.
(function () {
  function init() {
    var t = document.getElementById('ukx-t'); if (!t) return;
    var tb = t.tBodies[0], rows = [].slice.call(tb.rows);
    var q = document.getElementById('ukx-q'), kind = document.getElementById('ukx-k'), none = document.getElementById('ukx-none'), cnt = document.getElementById('ukx-n');
    function apply() {
      var s = (q && q.value || '').trim().toLowerCase(), k = kind ? kind.value : '', n = 0;
      rows.forEach(function (r) {
        var on = (!s || r.dataset.s.indexOf(s) >= 0) && (!k || r.dataset.k === k);
        r.hidden = !on; if (on) n++;
      });
      if (none) none.hidden = n > 0;
      if (cnt) cnt.textContent = n + ' model' + (n === 1 ? '' : 's');
    }
    if (q) q.addEventListener('input', apply);
    if (kind) kind.addEventListener('change', apply);
    var ths = [].slice.call(t.tHead.rows[0].cells);
    ths.forEach(function (th, i) {
      var b = th.querySelector('button'); if (!b) return;
      b.addEventListener('click', function () {
        var dir = th.getAttribute('aria-sort') === 'descending' ? 'ascending' : 'descending';
        ths.forEach(function (x) { x.removeAttribute('aria-sort'); });
        th.setAttribute('aria-sort', dir);
        var num = th.dataset.t !== 'text';
        rows.sort(function (a, c) {
          var x = a.cells[i].dataset.v, y = c.cells[i].dataset.v;
          var r = num ? (parseFloat(x) - parseFloat(y)) : x.localeCompare(y);
          return dir === 'ascending' ? r : -r;
        });
        rows.forEach(function (r) { tb.appendChild(r); });
      });
    });
    apply();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
