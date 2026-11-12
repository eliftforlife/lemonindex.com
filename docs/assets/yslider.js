// 11-10: "Every <model>, year by year" slider (year_slider.py). Two stacked <img>s crossfade as the range moves.
// Keyboard: the range input handles arrows/Home/End. Touch: native range drag. Images: neighbours preloaded, the rest on demand.
(function () {
  document.querySelectorAll('.ysl').forEach(function (root) {
    var d; try { d = JSON.parse(root.querySelector('.ysl-data').textContent); } catch (e) { return; }
    var Y = d.years, imgs = root.querySelectorAll('.ysl-stage img'), front = 0, cur = 0, want = 0, busy = false;
    var r = root.querySelector('.ysl-range'), yr = root.querySelector('.ysl-yr b'), gen = root.querySelector('.ysl-gen'),
        li = root.querySelector('.ysl-li'), yt = root.querySelector('.ysl-yt'), go = root.querySelector('.ysl-go'), sel = root.querySelector('.ysl-sel'), cache = {};
    function pre(i) { if (i < 0 || i >= Y.length || cache[i]) return; var im = new Image(); im.decoding = 'async'; im.src = Y[i].src; cache[i] = im; }
    function info(i) {
      var v = Y[i]; yr.textContent = v.y; gen.textContent = v.gen; r.setAttribute('aria-valuetext', String(v.y)); if (+r.value !== i) r.value = i; if (sel && +sel.value !== i) sel.value = i;
      li.textContent = v.li != null ? 'Lemon Index ' + v.li : 'No Lemon Index for ' + v.y;
      li.className = 'ysl-li' + (v.li == null ? ' na' : v.li <= 80 ? ' good' : v.li >= 130 ? ' bad' : '');
      yt.textContent = v.yt != null ? 'YouTube score ' + v.yt : ''; yt.hidden = v.yt == null;
      var bt = root.querySelector('.ysl-best'); if (bt) bt.hidden = v.y !== d.best;
      if (v.url) { go.hidden = false; go.href = v.url; go.textContent = 'See the ' + v.y + ' report ›'; } else go.hidden = true;
    }
    function show(i) {
      want = i; info(i); pre(i - 1); pre(i + 1); pre(i + 2);
      if (busy || i === cur) return;
      busy = true; var back = imgs[1 - front], v = Y[i];
      var done = function () { back.alt = v.y + ' ' + d.name + ' illustration'; back.removeAttribute('aria-hidden'); imgs[front].setAttribute('aria-hidden', 'true');
        back.classList.add('on'); imgs[front].classList.remove('on'); front = 1 - front; cur = i;
        setTimeout(function () { busy = false; if (want !== cur) show(want); }, 120); };
      if (back.getAttribute('src') === v.src && back.complete) done(); else { back.onload = done; back.onerror = function () { busy = false; }; back.src = v.src; }
    }
    r.addEventListener('input', function () { show(+r.value); });
    // 11-12 (Jess: ~14 px per year on a phone): a year picker next to the slider
    if (sel) sel.addEventListener('change', function () { for (var i = 0; i < Y.length; i++) pre(i); show(+sel.value); });
    cur = want = +r.value || 0;   // 11-12: opens on a popular used year
    info(cur); pre(cur - 1); pre(cur + 1); pre(cur + 2);
    // warm the whole set only once someone uses the slider
    r.addEventListener('pointerdown', function once() { r.removeEventListener('pointerdown', once); for (var i = 0; i < Y.length; i++) pre(i); });
  });
})();
