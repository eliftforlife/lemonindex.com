// 11-12 (ycarousel.py): the year carousel on year pages and the year explorer on model pages. Links work without this file.
(function () {
  var de = document.documentElement;
  function sbw() { de.style.setProperty('--sbw', Math.max(0, innerWidth - de.clientWidth) + 'px'); }
  if (document.querySelector('.ycr')) { sbw(); addEventListener('resize', sbw); }
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---- year carousel: swipe / arrows / a tap on a peeking car slide that car to the middle, then open its page
  document.querySelectorAll('.ycr').forEach(function (root) {
    var tr = root.querySelector('.ycr-track'), p = root.querySelector('.ycr-p[href]'), n = root.querySelector('.ycr-n[href]'), going = false;
    function go(a, dir) {
      if (!a || going) return; going = true;
      if (reduce) { location.href = a.href; return; }
      tr.classList.remove('drag'); tr.style.transform = 'translateX(' + (dir === 'p' ? 50 : -50) + '%)';
      a.style.opacity = '1';
      setTimeout(function () { location.href = a.href; }, 230);
      setTimeout(function () { going = false; tr.style.transform = ''; a.style.opacity = ''; }, 1500);   // back/forward cache: never stay stuck
    }
    root.querySelectorAll('.ycr-ar, .ycr-p[href], .ycr-n[href]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
        e.preventDefault(); var d = a.dataset.dir || (a.classList.contains('ycr-p') ? 'p' : 'n'); go(d === 'p' ? p : n, d);
      });
    });
    root.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft' && p) { e.preventDefault(); go(p, 'p'); } else if (e.key === 'ArrowRight' && n) { e.preventDefault(); go(n, 'n'); }
    });
    var x0 = null, y0 = 0, dx = 0, lock = null, w = 1;
    root.addEventListener('touchstart', function (e) { if (e.touches.length !== 1) return; x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; dx = 0; lock = null; w = root.offsetWidth; }, { passive: true });
    root.addEventListener('touchmove', function (e) {
      if (x0 === null) return;
      var ddx = e.touches[0].clientX - x0, ddy = e.touches[0].clientY - y0;
      if (lock === null && (Math.abs(ddx) > 8 || Math.abs(ddy) > 8)) lock = Math.abs(ddx) > Math.abs(ddy) ? 'x' : 'y';
      if (lock !== 'x') return;
      dx = ddx; if ((dx > 0 && !p) || (dx < 0 && !n)) dx = dx / 4;   // rubber band at the first / last year
      tr.classList.add('drag'); tr.style.transform = 'translateX(' + dx + 'px)';
    }, { passive: true });
    root.addEventListener('touchend', function () {
      if (x0 === null) return; x0 = null; tr.classList.remove('drag');
      if (lock === 'x' && Math.abs(dx) > Math.min(70, w * .18)) { if (dx > 0 && p) return go(p, 'p'); if (dx < 0 && n) return go(n, 'n'); }
      tr.style.transform = '';
    });
    window.addEventListener('pageshow', function () { going = false; tr.style.transform = ''; });
  });

  // ---- year explorer: the bar strip is the slider (a transparent range input on top of it); arrows step one year
  document.querySelectorAll('.yx').forEach(function (root) {
    var d; try { d = JSON.parse(root.querySelector('.yx-data').textContent); } catch (e) { return; }
    var Y = d.years, imgs = root.querySelectorAll('.yx-stage img'), bars = root.querySelectorAll('.yx-bars i'), front = 0, cur, want, busy = false, cache = {};
    var r = root.querySelector('.yx-r'), yr = root.querySelector('.yx-yr b'), gen = root.querySelector('.yx-gen'), li = root.querySelector('.yx-li'),
        yt = root.querySelector('.yx-yt'), best = root.querySelector('.yx-best'), go = root.querySelector('.yx-go'), bp = root.querySelector('.yx-sp'), bn = root.querySelector('.yx-sn');
    function pre(i) { if (i < 0 || i >= Y.length || cache[i]) return; var im = new Image(); im.decoding = 'async'; im.src = Y[i].src; cache[i] = im; }
    function info(i) {
      var v = Y[i]; yr.textContent = v.y; gen.textContent = v.gen || ''; r.setAttribute('aria-valuetext', String(v.y)); if (+r.value !== i) r.value = i;
      li.textContent = v.li != null ? 'Lemon Index ' + v.li : 'No score for ' + v.y;
      li.className = 'yx-li ' + (v.li == null ? 'na' : v.li > 110 ? 'bad' : 'good');
      yt.textContent = v.rk ? 'YouTube #' + v.rk + ' of ' + v.n : ''; yt.hidden = !v.rk;
      best.hidden = v.y !== d.best;
      if (v.url) { go.hidden = false; go.href = v.url; go.textContent = 'See the ' + v.y + ' report ›'; } else go.hidden = true;
      bars.forEach(function (b, k) { b.classList.toggle('on', k === i); });
      bp.disabled = i === 0; bn.disabled = i === Y.length - 1;
    }
    function show(i) {
      i = Math.max(0, Math.min(Y.length - 1, i)); want = i; info(i); pre(i - 1); pre(i + 1);
      if (busy || i === cur) return;
      busy = true; var back = imgs[1 - front], v = Y[i];
      var done = function () { back.alt = v.y + ' ' + d.name + ' illustration'; back.removeAttribute('aria-hidden'); imgs[front].setAttribute('aria-hidden', 'true');
        back.classList.add('on'); imgs[front].classList.remove('on'); front = 1 - front; cur = i;
        setTimeout(function () { busy = false; if (want !== cur) show(want); }, reduce ? 0 : 110); };
      if (back.getAttribute('src') === v.src && back.complete) done(); else { back.onload = done; back.onerror = function () { busy = false; }; back.src = v.src; }
    }
    r.addEventListener('input', function () { show(+r.value); });
    r.addEventListener('pointerdown', function once() { r.removeEventListener('pointerdown', once); for (var i = 0; i < Y.length; i++) pre(i); });
    bp.addEventListener('click', function () { show(want - 1); });
    bn.addEventListener('click', function () { show(want + 1); });
    cur = want = +r.value || 0; info(cur); pre(cur - 1); pre(cur + 1);
  });

  // ---- YouTube block: generation chips
  document.querySelectorAll('.yot').forEach(function (root) {
    var bs = root.querySelectorAll('.yot-g'), ps = root.querySelectorAll('.yot-p');
    bs.forEach(function (b) {
      b.addEventListener('click', function () {
        bs.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        ps.forEach(function (p) { var on = p.dataset.i === b.dataset.i; p.hidden = !on; p.classList.toggle('on', on); });
      });
    });
    var on = root.querySelector('.yot-g[aria-pressed="true"]'); if (on && on.scrollIntoView) { var g = on.parentNode; g.scrollLeft = on.offsetLeft - g.clientWidth / 2 + on.offsetWidth / 2; }
  });
})();
