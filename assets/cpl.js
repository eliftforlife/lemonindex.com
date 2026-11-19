// 11-18 compact boxes (car_pills.py, engine_pills.py): a #hash link (old tab links like #p-recalls, #recalls, #questions, links from
// other pages, the recall bell) opens every closed box that holds its target, then scrolls to it. Without JS the boxes still open by tap.
(function () {
  function target(h) {
    h = decodeURIComponent((h || '').replace(/^#/, '')); if (!h) return null;
    return document.getElementById(h) || document.getElementById('p-' + h);
  }
  function show(el, scroll) {
    if (!el) return false;
    var opened = false;
    if (el.tagName === 'SECTION' && el.classList.contains('cpl-sec')) { var d0 = el.querySelector('details'); if (d0 && !d0.open) { d0.open = true; opened = true; } }
    for (var p = el.parentElement; p; p = p.parentElement) if (p.tagName === 'DETAILS' && !p.open) { p.open = true; opened = true; }
    if (scroll && (opened || scroll === 2)) setTimeout(function () { el.scrollIntoView({ block: 'start' }); }, 0);
    return true;
  }
  function go() { show(target(location.hash), 2); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
  window.addEventListener('hashchange', go);
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]'); if (!a) return;
    var el = target(a.getAttribute('href')); if (el && a.getAttribute('href') === location.hash) show(el, 2); else show(el, 0);
  });
})();
