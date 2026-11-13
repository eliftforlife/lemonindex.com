// 11-13 navigation fix N3: an #eng-<id> link (the car pages' "Engines in this car" chips, the /engines/ cards) opens the engine chart's
// Engines view and scrolls to that engine. tabs.js already opens the tab that holds it.
(function () {
  function go() {
    var h = decodeURIComponent((location.hash || '').slice(1)); if (h.indexOf('eng-') !== 0) return;
    var el = document.getElementById(h); if (!el) return;
    var v = el.closest('.tg-v'), tg = v && v.closest('.tg');
    if (tg && !v.classList.contains('on')) { var b = tg.querySelector('.tg-o[data-v="' + v.getAttribute('data-v') + '"]'); if (b) b.click(); }
    setTimeout(function () { el.scrollIntoView({ block: 'start' }); window.scrollBy(0, -90); }, 80);   // -90: under the sticky header and tab row
  }
  window.addEventListener('hashchange', go);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(go, 60); }); else setTimeout(go, 60);
})();
