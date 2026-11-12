// 11-11 performance-car pages (perf_page.py): the generation slider. Picking a generation swaps the hero car, its big numbers and the
// Overview's generation block (performance, engine, YouTube, buy). Without JS the focus generation shows (all of them are in the HTML).
(function () {
  document.documentElement.classList.add('pfjs');
  function init() {
    var root = document.querySelector('.pf-gens'); if (!root) return;
    var stops = root.querySelectorAll('.pf-stop'), cars = root.querySelectorAll('.pf-car'), stats = root.querySelectorAll('.pf-stats'),
        blocks = document.querySelectorAll('.pf-g'), range = root.querySelector('.pf-range'), cur = -1;
    var tr = root.querySelector('.pf-track'); if (tr) tr.style.setProperty('--n', stops.length);
    function show(i, focus) {
      if (i === cur || i < 0 || i >= stops.length) return; cur = i;
      stops.forEach(function (b, k) { b.setAttribute('aria-pressed', k === i ? 'true' : 'false'); b.tabIndex = k === i ? 0 : -1; });
      if (cars.length > 1) cars.forEach(function (im, k) { if (k === i) im.removeAttribute('loading'); im.classList.toggle('on', k === i); });   // one picture: it stays
      stats.forEach(function (s, k) { s.classList.toggle('on', k === i); });
      blocks.forEach(function (b) { b.classList.toggle('on', +b.getAttribute('data-i') === i); });
      blocks.forEach(function (b) { var row = b.querySelector('.pf-vs'), st = row && row.querySelector('.pf-star');   // phones: the starred trim first in view
        if (row && st && row.scrollWidth > row.clientWidth + 4 && b.classList.contains('on')) row.scrollLeft = st.offsetLeft - row.offsetLeft - 16; });
      if (range) { range.value = i; range.setAttribute('aria-valuetext', stops[i].querySelector('b').textContent); }
      filt();
      if (tr && tr.scrollWidth > tr.clientWidth + 2) tr.scrollLeft = Math.max(0, stops[i].offsetLeft - tr.offsetLeft - 24);   // phones: the picked generation in view
      if (focus) stops[i].focus();
      try { history.replaceState(null, '', location.pathname + location.search + (location.hash && location.hash.indexOf('#p-') === 0 ? location.hash : '')); } catch (e) {}
    }
    // 11-12 (UX test: the G80 tab showed 2008 data): the Years / Problems / Recalls / Specs rows of other generations hide (data-pfy = their
    // model years), each tab's note says which years show, and "Show every year" turns the filter off. One picture for every generation
    // (the C63): a line under it says which generation it shows when another one is picked.
    var all = false, pic = root.querySelector('.pf-car[data-pg]'), picl = root.querySelector('.pf-pic');
    function filt() {
      if (cur < 0) return;
      var st = stops[cur], y0 = +st.getAttribute('data-y0'), y1 = +st.getAttribute('data-y1'), code = st.querySelector('b').textContent, yrs = st.querySelector('span').textContent;
      document.querySelectorAll('[data-pfy]').forEach(function (el) {
        var on = all || el.getAttribute('data-pfy').split(' ').some(function (y) { y = +y; return y >= y0 && y <= y1; });
        el.classList.toggle('pf-off', !on);
      });
      document.querySelectorAll('.pf-yf').forEach(function (n) {
        n.querySelector('.pf-yfg').textContent = code; n.querySelector('.pf-yfr').textContent = yrs; n.classList.toggle('pf-yfa', all);
        var b = n.querySelector('.pf-yall'); b.textContent = all ? 'Only the ' + code + ' years' : 'Show every year'; b.setAttribute('aria-pressed', all ? 'true' : 'false');
      });
      if (pic && picl) { var o = +pic.getAttribute('data-pg') !== cur; picl.classList.toggle('on', o); var pn = picl.querySelector('.pf-picn'); if (pn) pn.textContent = o ? 'No ' + code + ' picture yet.' : ''; }
    }
    document.querySelectorAll('.pf-yall').forEach(function (b) { b.addEventListener('click', function () { all = !all; filt(); }); });
    stops.forEach(function (b, k) {
      b.addEventListener('click', function () { show(k); });
      b.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (e.key === 'Home') { e.preventDefault(); show(0, true); } else if (e.key === 'End') { e.preventDefault(); show(stops.length - 1, true); }
        else if (d) { e.preventDefault(); show(Math.max(0, Math.min(stops.length - 1, cur + d)), true); }
      });
    });
    // swipe the car left / right on phones
    var stage = root.querySelector('.pf-stage'), x0 = null;
    if (stage && stops.length > 1) stage.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    if (stage && stops.length > 1) stage.addEventListener('touchend', function (e) {
      if (x0 === null) return; var dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 40) show(Math.max(0, Math.min(stops.length - 1, cur + (dx < 0 ? 1 : -1))));
    });
    // preload the other cars once the page is idle
    setTimeout(function () { cars.forEach(function (im) { im.removeAttribute('loading'); }); }, 1500);
    show(+root.getAttribute('data-focus') || 0);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
