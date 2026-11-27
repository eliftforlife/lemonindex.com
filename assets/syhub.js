// 11-27 symptom pages (symptom_pages.py, Elijah: one section open at a time): an accordion over every big card (details.mhx) and the
// Questions / Data & sources panels (.mhb-p) of the .sy-hub sections. Opening one closes whichever is open; tapping the open one closes it.
// A #link to a card, a panel or anything inside one (#sy-cost, #questions ...) opens it. A card that opens by a tap scrolls into view only
// when closing a long card above it pushed its top off-screen.
(function () {
  var all = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };
  function btn(p) { return document.querySelector('.sy-hub .mhb-b[aria-controls="' + p.id + '"]'); }
  function setP(p, on) {
    p.classList.toggle('on', on); var b = btn(p); if (b) b.setAttribute('aria-expanded', on ? 'true' : 'false');
    if (!on && history.replaceState && location.hash === '#' + p.id) history.replaceState(null, '', location.pathname + location.search);
  }
  function closeAll(keep) {
    all('.sy-hub details.mhx[open]').forEach(function (d) { if (d !== keep) d.open = false; });
    all('.sy-hub .mhb-p.on').forEach(function (p) { if (p !== keep) setP(p, false); });
  }
  function reveal(el) {
    requestAnimationFrame(function () { requestAnimationFrame(function () {
      var h = document.querySelector('header.gh'), top = h ? Math.max(0, h.getBoundingClientRect().bottom) : 0;
      var r = el.getBoundingClientRect().top;
      if (r >= top && r <= innerHeight - 72) return;
      var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: Math.max(0, scrollY + r - top - 12), behavior: reduce ? 'auto' : 'smooth' });
    }); });
  }
  function go() {
    var h = decodeURIComponent((location.hash || '').slice(1)); if (!h) return;
    var el = document.getElementById(h); if (!el || !el.closest('.sy-hub')) return;
    var p = el.closest('.mhb-p');
    if (p) { closeAll(p); setP(p, true); }
    else {
      var i = el.closest('.mhb-i'), d = i && i.querySelector('details.mhx');
      if (d) { closeAll(d); d.open = true; }
    }
    setTimeout(function () { el.scrollIntoView({ block: 'start' }); }, 0);
  }
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var s = e.target.closest('.sy-hub details.mhx > summary');
    if (s) {   // close the others before the browser opens this one, so two are never open in the same frame
      if (!s.parentElement.open) { closeAll(s.parentElement); reveal(s); }
      return;
    }
    var b = e.target.closest('.sy-hub .mhb-b'); if (!b) return;
    var p = document.getElementById(b.getAttribute('aria-controls')); if (!p) return;
    e.preventDefault();
    var on = !p.classList.contains('on');
    closeAll(on ? p : null); setP(p, on);
    if (on) { if (history.replaceState) history.replaceState(null, '', '#' + p.id); reveal(b); }
  });
  // a card opened any other way (cpl.js #links, find-in-page) still leaves only that one open
  document.addEventListener('toggle', function (e) {
    var d = e.target; if (d.open && d.matches && d.matches('.sy-hub details.mhx')) closeAll(d);
  }, true);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
  window.addEventListener('hashchange', go);
})();
