// 11-26 model page hub (hub_cards.py): the 4 small buttons open their panel in place (one at a time; tap again to close).
// A #hash link to anything inside a panel or a card (#recall-alerts, #p-questions, #youtube...) opens it.
// 11-27 (Elijah, year pages: hub has class mhb-acc): an accordion over the big cards AND the small-button panels together: opening one
// closes whichever is open, tapping the open one closes it. A card or panel that opens by a tap is scrolled into view only when its top
// ended up off-screen (closing a long card above it moves it up); otherwise nothing jumps. Hash links still open the right one.
(function () {
  function btn(p) { return document.querySelector('.mhb-b[href="#' + p.id + '"]'); }
  function acc(el) { return !!(el && el.closest && el.closest('.mhb-acc')); }
  function cards(keep) { document.querySelectorAll('.mhb-acc details.mhx[open]').forEach(function (d) { if (d !== keep) d.open = false; }); }
  function set(p, on) {
    p.classList.toggle('on', on); var b = btn(p); if (b) b.setAttribute('aria-expanded', on ? 'true' : 'false');
    if (on) { var t = p.querySelector('.rla-tg[aria-expanded="false"]'); if (t) t.click(); if (acc(p)) cards(null); }
  }
  function only(p) { document.querySelectorAll('.mhb-p.on').forEach(function (x) { if (x !== p) set(x, false); }); }
  function unhash(p) {   // a closed panel's #id leaves the address bar
    if (history.replaceState && location.hash === '#' + p.id) history.replaceState(null, '', location.pathname + location.search);
  }
  function panels() { document.querySelectorAll('.mhb-acc .mhb-p.on').forEach(function (x) { set(x, false); unhash(x); }); }
  // While the card above closes (it animates), keep the one just opened from sliding up under the sticky header: each frame for ~0.7 s,
  // if its top went above the header, scroll by just that much. Nothing moves when it stays on screen. If it ends up below the screen,
  // one smooth scroll brings it up. A finger or wheel scroll by the visitor stops all of it.
  function reveal(el, at) {
    var h = document.querySelector('header.gh'), t0 = performance.now(), stop = false;
    var halt = function () { stop = true; };
    ['wheel', 'touchstart', 'keydown'].forEach(function (k) { addEventListener(k, halt, { once: true, passive: true }); });
    var hb = function () { return h ? Math.max(0, h.getBoundingClientRect().bottom) : 0; };
    var off = function () { return (at || el).getBoundingClientRect().top - hb() - 12; };
    (function f() {
      if (stop) return;
      if (el.getBoundingClientRect().top < hb()) window.scrollBy(0, off());
      if (performance.now() - t0 < 700) { requestAnimationFrame(f); return; }
      if (el.getBoundingClientRect().top > innerHeight - 72) {
        var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
        window.scrollTo({ top: Math.max(0, scrollY + off()), behavior: reduce ? 'auto' : 'smooth' });
      }
    })();
  }
  function go() {
    var h = decodeURIComponent((location.hash || '').slice(1)); if (!h) return;
    var el = document.getElementById(h) || document.getElementById('p-' + h); if (!el) return;
    var p = el.closest('.mhb-p'); if (p) { only(p); set(p, true); }
    var i = el.closest('.mhb-i'); var d = i && i.querySelector('details.mhx'); if (d && !d.open) d.open = true;
    if (p || i) setTimeout(function () { el.scrollIntoView({ block: 'start' }); }, 0);
  }
  document.addEventListener('click', function (e) {
    var s = e.target.closest && e.target.closest('.mhb-acc details.mhx > summary');
    if (s) {   // a card face: closing the others first (before the browser opens this one), so both are never open in one frame
      var d = s.parentElement;
      if (!d.open) { cards(d); panels(); reveal(s); }
      return;
    }
    var b = e.target.closest && e.target.closest('.mhb-b'); if (!b) return;
    var p = document.getElementById(b.getAttribute('href').slice(1)); if (!p) return;
    e.preventDefault(); var on = !p.classList.contains('on'); only(p); set(p, on);
    if (history.replaceState) history.replaceState(null, '', on ? '#' + p.id : location.pathname + location.search);
    if (on && acc(p)) reveal(p, b.parentElement);   // keep the button row in view above the panel
  });
  // any other way a card opens (a #hash link, cpl.js, find-in-page) still leaves only that one open
  document.addEventListener('toggle', function (e) {
    var d = e.target; if (!d.open || !d.matches || !d.matches('.mhb-acc details.mhx')) return;
    cards(d); panels();
  }, true);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
  window.addEventListener('hashchange', go);
})();
