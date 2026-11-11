// 11-11 performance-car pages (perf_page.py): the generation slider. Picking a generation swaps the hero car, its big numbers and the
// Overview's generation block (performance, engine, YouTube, buy). Without JS the focus generation shows (all of them are in the HTML).
(function () {
  document.documentElement.classList.add('pfjs');
  function init() {
    var root = document.querySelector('.pf-gens'); if (!root) return;
    var stops = root.querySelectorAll('.pf-stop'), cars = root.querySelectorAll('.pf-car'), stats = root.querySelectorAll('.pf-stats'),
        blocks = document.querySelectorAll('.pf-g'), range = root.querySelector('.pf-range'), cur = -1;
    root.querySelector('.pf-track').style.setProperty('--n', stops.length);
    function show(i, focus) {
      if (i === cur || i < 0 || i >= stops.length) return; cur = i;
      stops.forEach(function (b, k) { b.setAttribute('aria-pressed', k === i ? 'true' : 'false'); b.tabIndex = k === i ? 0 : -1; });
      cars.forEach(function (im, k) { if (k === i) im.removeAttribute('loading'); im.classList.toggle('on', k === i); });
      stats.forEach(function (s, k) { s.classList.toggle('on', k === i); });
      blocks.forEach(function (b) { b.classList.toggle('on', +b.getAttribute('data-i') === i); });
      blocks.forEach(function (b) { var row = b.querySelector('.pf-vs'), st = row && row.querySelector('.pf-star');   // phones: the starred trim first in view
        if (row && st && row.scrollWidth > row.clientWidth + 4 && b.classList.contains('on')) row.scrollLeft = st.offsetLeft - row.offsetLeft - 16; });
      if (range) { range.value = i; range.setAttribute('aria-valuetext', stops[i].querySelector('b').textContent); }
      if (focus) stops[i].focus();
      try { history.replaceState(null, '', location.pathname + location.search + (location.hash && location.hash.indexOf('#p-') === 0 ? location.hash : '')); } catch (e) {}
    }
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
    stage.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    stage.addEventListener('touchend', function (e) {
      if (x0 === null) return; var dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 40) show(Math.max(0, Math.min(stops.length - 1, cur + (dx < 0 ? 1 : -1))));
    });
    // preload the other cars once the page is idle
    setTimeout(function () { cars.forEach(function (im) { im.removeAttribute('loading'); }); }, 1500);
    show(+root.getAttribute('data-focus') || 0);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
