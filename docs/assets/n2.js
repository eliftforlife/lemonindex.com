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
// the sticky car label (problem 8): once the tab row is pinned and the title has scrolled away, the row says which car this is
// ("2015 Ford F-150 · 89"); a tap goes back to the top. Built from the page's own title and gauge, so it needs no extra HTML.
(function () {
  function label() {
    var row = document.querySelector('.tbl .tb-row'), h1 = document.querySelector('.tbl .tb-hero h1');
    if (!row || !h1 || row.querySelector('.n2-sl')) return;
    var name = ((h1.querySelector('.yct-big') || h1).textContent || '').replace(/\s+/g, ' ').trim().replace(/\.$/, '');
    if (!name) return;
    var g = document.querySelector('.tbl .tb-hero .yhero .gauge figcaption b'), vd = document.querySelector('.tbl .tb-hero .yhero .yverd');
    var el = document.createElement('button'); el.type = 'button'; el.className = 'n2-sl'; el.setAttribute('aria-label', 'Back to the top: ' + name);
    var n = document.createElement('span'); n.textContent = name; el.appendChild(n);
    if (g && /\d/.test(g.textContent)) {
      var b = document.createElement('b'); b.textContent = g.textContent.trim();
      b.className = vd && vd.classList.contains('good') ? 'good' : vd && vd.classList.contains('bad') ? 'bad' : 'mid'; el.appendChild(b);
    }
    el.addEventListener('click', function () { try { scrollTo({ top: 0, behavior: 'smooth' }); } catch (e) { scrollTo(0, 0); } });
    row.insertBefore(el, row.firstChild); row.classList.add('n2-l');
    var on = false, tick = false;
    function check() {
      tick = false; var top = parseFloat(getComputedStyle(row).top) || 0;
      var stuck = row.getBoundingClientRect().top <= top + 1 && h1.getBoundingClientRect().bottom < top + row.offsetHeight;
      if (stuck !== on) { on = stuck; row.classList.toggle('n2-on', on); }
    }
    addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(check); } }, { passive: true });
    addEventListener('resize', check); check();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', label); else label();
})();
