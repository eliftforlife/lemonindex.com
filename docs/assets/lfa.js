// 11-12 round 2 UX fixes (build.py LFA_JS):
// 1. A long year list (.lfa-sc, year pages) opens scrolled to the page's own year, inside its box, the first time it is visible.
// 2. Match-up pages (form.lfa-yp): "Your years" recomputes the winner for just those model years (2023+ partial years never count).
//    #y2016 or #y2018-2020 in the URL preselects them.
(function () {
  var boxes = [].slice.call(document.querySelectorAll('.lfa-sc'));
  var go = function (box) {
    if (box._lfa) return; var c = box.querySelector('.b.cur'); if (!c || !box.clientHeight) return;
    box.scrollTop = Math.max(0, c.offsetTop - box.clientHeight / 2 + c.offsetHeight / 2); box._lfa = 1;
  };
  var all = function () { boxes.forEach(go); };
  if (boxes.length) {
    all();   // visible at load (e.g. #years)
    document.addEventListener('click', function () { setTimeout(all, 60); }, true);   // a tab switch shows the list
    window.addEventListener('hashchange', function () { setTimeout(all, 60); });
    if ('IntersectionObserver' in window) { var io = new IntersectionObserver(function () { all(); }); boxes.forEach(function (b) { io.observe(b); }); }
  }

  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (ch) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]; }); };
  document.querySelectorAll('form.lfa-yp').forEach(function (f) {
    var A = f.getAttribute('data-a'), B = f.getAttribute('data-b'), out = f.querySelector('output'), sF = f.elements.f, sT = f.elements.t;
    var rows = [].slice.call(document.querySelectorAll('.yrs .yr[data-a]'));
    if (!sF || !sT || !rows.length) return;
    f.addEventListener('submit', function (e) { e.preventDefault(); });
    var near = function (sel, y) {   // the closest year the select offers
      var best = null; [].forEach.call(sel.options, function (o) { if (best === null || Math.abs(+o.value - y) < Math.abs(+best - y)) best = o.value; });
      if (best !== null) sel.value = best;
    };
    function run(user) {
      var lo = Math.min(+sF.value, +sT.value), hi = Math.max(+sF.value, +sT.value), wa = 0, wb = 0, sa = 0, sb = 0, n = 0;
      rows.forEach(function (r) {
        var y = +r.getAttribute('data-y'), on = y >= lo && y <= hi && !r.hasAttribute('data-p');
        r.classList.toggle('lfa-on', !!user && on);
        if (!on) return;
        var a = +r.getAttribute('data-a'), b = +r.getAttribute('data-b'); n++; sa += a; sb += b; if (a < b) wa++; else if (b < a) wb++;
        if (user) { var d = r.closest('details'); if (d) d.open = true; }
      });
      if (!user) { out.innerHTML = 'Pick the model years you&#39;re shopping to see who wins for just those years.'; return; }
      if (!n) { out.textContent = 'No scored years in that range.'; return; }
      var ma = Math.round(sa / n), mb = Math.round(sb / n), span = lo === hi ? String(lo) : lo + '–' + hi;
      var close = Math.abs(ma - mb) <= Math.max(ma, mb) * 0.08, aw = ma < mb;
      var avg = (n > 1 ? 'Average Lemon Index for those years: ' : 'Lemon Index: ') + esc(A) + ' ' + ma + ', ' + esc(B) + ' ' + mb + ' (100 = average car, lower is better).';
      out.innerHTML = close
        ? '<b>' + span + ': too close to call.</b> ' + esc(A) + ' had fewer complaints per car sold in ' + wa + ' of ' + n + ', ' + esc(B) + ' in ' + wb + '. ' + avg
        : '<b>' + span + ': ' + esc(aw ? A : B) + ' wins.</b> Fewer complaints per car sold in ' + (aw ? wa : wb) + ' of ' + n + ' year' + (n === 1 ? '' : 's') + '. ' + avg;
    }
    sF.addEventListener('change', function () { run(true); });
    sT.addEventListener('change', function () { run(true); });
    var m = location.hash.match(/^#y((?:19|20)\d\d)(?:-((?:19|20)\d\d))?$/);
    if (m) {
      var a = +m[1], b = m[2] ? +m[2] : +m[1];
      if (!m[2]) { a -= 1; b += 1; }   // one year from a year page: show it with its neighbours
      near(sF, Math.min(a, b)); near(sT, Math.max(a, b)); run(true);
      var h = document.getElementById('your-years'); if (h) h.scrollIntoView({ block: 'start' });
    } else run(false);
  });
})();
