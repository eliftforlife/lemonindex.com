// 11-12 compare match-ups (cmp_pages.py) + /best/ lists (best_ui.py).
// 1. The "Check the VIN" box hands the VIN to /vin/ in the URL hash (#v=...), so it never reaches a server log.
//    Without JS the form still opens /vin/ (the input has no name, so nothing is sent).
// 2. 11-13 v4 info popovers (.cb-inf): the (i) button opens its note on tap / click (hover on desktop is CSS); Esc, a second tap or a tap
//    elsewhere closes it. The note opens toward the side of the screen with more room.
// 3. 11-13 v4 sticky section nav (.cb-jump): the pill of the section on screen is highlighted and kept in view in the scrolling row.
(function () {
  document.querySelectorAll('form.cbx-vinf').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      var v = (f.querySelector('input').value || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
      if (!v) return; e.preventDefault(); location.href = '/vin/#v=' + v;
    });
  });

  var infs = [].slice.call(document.querySelectorAll('.cb-inf'));
  var side = function (w) {
    var b = w.querySelector('.cb-ib').getBoundingClientRect(), pop = w.querySelector('.cb-pop');
    pop.classList.toggle('cb-pl', b.left + b.width / 2 < innerWidth / 2);
  };
  var close = function (w) { w.classList.remove('open'); w.querySelector('.cb-ib').setAttribute('aria-expanded', 'false'); };
  infs.forEach(function (w) {
    var btn = w.querySelector('.cb-ib');
    btn.addEventListener('click', function (e) {
      e.stopPropagation(); var open = !w.classList.contains('open');
      infs.forEach(function (o) { if (o !== w) close(o); });
      if (open) { side(w); w.classList.add('open'); btn.setAttribute('aria-expanded', 'true'); } else close(w);
    });
    w.addEventListener('mouseenter', function () { side(w); });
  });
  document.addEventListener('click', function (e) { infs.forEach(function (w) { if (!w.contains(e.target)) close(w); }); });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    infs.forEach(function (w) { if (w.classList.contains('open')) { close(w); w.querySelector('.cb-ib').focus(); } });
  });

  var nav = document.querySelector('.cb-jump');
  if (!nav) return;
  var links = [].slice.call(nav.querySelectorAll('a[href^="#"]')), row = nav.querySelector('.cb-jin');
  var heads = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  var cur = -1, tick = false;
  function spy() {
    tick = false;
    var line = nav.getBoundingClientRect().bottom + 24, k = -1;
    heads.forEach(function (h, i) { if (h && h.getBoundingClientRect().top <= line) k = i; });
    nav.classList.toggle('cb-stuck', nav.getBoundingClientRect().top <= 60 && scrollY > 200);
    if (k === cur) return; cur = k;
    if (k < 0 && row) row.scrollTo({ left: 0 });
    links.forEach(function (a, i) { if (i === k) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
    if (k >= 0 && row) {
      var a = links[k], l = a.offsetLeft - row.offsetLeft, r = l + a.offsetWidth;
      if (l < row.scrollLeft || r > row.scrollLeft + row.clientWidth) row.scrollTo({ left: Math.max(0, l - 16), behavior: 'smooth' });
    }
  }
  addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(spy); } }, { passive: true });
  addEventListener('resize', spy); spy();
})();
