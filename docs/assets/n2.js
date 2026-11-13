// 11-13 navigation (N2, n2_nav.py): the Every year list can be sorted newest first (its HTML order) or by fewest complaints per car sold.
(function () {
  function sortable(so) {
    var box = so.parentElement.querySelector('.bars'); if (!box) return;
    var rows = Array.prototype.filter.call(box.children, function (e) { return e.classList.contains('b'); });
    if (rows.length < 3) return;
    var li = function (e) { var b = e.querySelector(':scope > b'), n = b ? parseFloat(b.textContent) : NaN; return isNaN(n) || e.classList.contains('early') || e.classList.contains('na') ? Infinity : n; };  // partial (2023+) and unscored years last
    var yr = function (e) { var n = e.querySelector('.bn'); return n ? +n.textContent : 0; };
    var leg = so.parentElement.querySelector('.lfa-leg');
    so.hidden = false;
    so.addEventListener('click', function (ev) {
      var bt = ev.target.closest('button'); if (!bt || bt.getAttribute('aria-pressed') === 'true') return;
      var k = bt.getAttribute('data-k');
      so.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', b === bt ? 'true' : 'false'); });
      rows.slice().sort(k === 'li' ? function (a, b) { return (li(a) - li(b)) || (yr(b) - yr(a)); } : function (a, b) { return yr(b) - yr(a); })
        .forEach(function (e) { box.appendChild(e); });
      var t = leg && leg.firstChild;
      if (t && t.nodeType === 3) t.nodeValue = t.nodeValue.replace(/^(Newest year first|Fewest complaints first)\./, k === 'li' ? 'Fewest complaints first.' : 'Newest year first.');
      box.scrollTop = 0;
    });
  }
  function init() { document.querySelectorAll('.n2-so').forEach(sortable); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
