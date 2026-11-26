// 11-26 model page hub (hub_cards.py): the 4 small buttons open their panel in place (one at a time; tap again to close).
// A #hash link to anything inside a panel or a card (#recall-alerts, #p-questions, #youtube...) opens it.
(function () {
  function btn(p) { return document.querySelector('.mhb-b[href="#' + p.id + '"]'); }
  function set(p, on) {
    p.classList.toggle('on', on); var b = btn(p); if (b) b.setAttribute('aria-expanded', on ? 'true' : 'false');
    if (on) { var t = p.querySelector('.rla-tg[aria-expanded="false"]'); if (t) t.click(); }
  }
  function only(p) { document.querySelectorAll('.mhb-p.on').forEach(function (x) { if (x !== p) set(x, false); }); }
  function go() {
    var h = decodeURIComponent((location.hash || '').slice(1)); if (!h) return;
    var el = document.getElementById(h) || document.getElementById('p-' + h); if (!el) return;
    var p = el.closest('.mhb-p'); if (p) { only(p); set(p, true); }
    var i = el.closest('.mhb-i'); var d = i && i.querySelector('details.mhx'); if (d && !d.open) d.open = true;
    if (p || i) setTimeout(function () { el.scrollIntoView({ block: 'start' }); }, 0);
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.mhb-b'); if (!b) return;
    var p = document.getElementById(b.getAttribute('href').slice(1)); if (!p) return;
    e.preventDefault(); var on = !p.classList.contains('on'); only(p); set(p, on);
    if (history.replaceState) history.replaceState(null, '', on ? '#' + p.id : location.pathname + location.search);
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
  window.addEventListener('hashchange', go);
})();
