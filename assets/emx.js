// 11-14 "Embed this chart" (embed_pages.py): copy buttons and the Colors choice in the car pages' panel, and the code picker on /embed/.
(function () {
  if (window.emxOn) return; window.emxOn = 1;
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.emx .cpy-b, .emxp .cpy-b'); if (!b) return;
    var t = b.textContent, done = function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = t; }, 1600); };
    var sel = function () { var c = b.parentElement.querySelector('code'), r = document.createRange(); r.selectNodeContents(c); var s = getSelection(); s.removeAllRanges(); s.addRange(r); };
    if (navigator.clipboard) navigator.clipboard.writeText(b.dataset.copy).then(done, sel); else sel();
  });
  function put(box, s) { var c = box.querySelector('code'), b = box.querySelector('.cpy-b'); if (c) c.textContent = s; if (b) b.dataset.copy = s; }
  document.addEventListener('change', function (e) {
    var r = e.target; if (!r.matches || !r.matches('.emx-t input')) return;
    put(r.closest('.emx'), r.dataset.snip);
  });
  var dj = document.getElementById('emx-data'); if (!dj) return;
  var D = JSON.parse(dj.textContent), M = document.getElementById('emx-m'), Y = document.getElementById('emx-y'), C = document.getElementById('emx-c');
  var esc = function (s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
  var by = {}; D.cars.forEach(function (c) { by[c[1]] = c; var o = document.createElement('option'); o.value = c[1]; o.textContent = c[0]; M.appendChild(o); });
  M.value = D.def;
  function years() {
    var c = by[M.value]; Y.length = 1;
    c[2].forEach(function (y) { var o = document.createElement('option'); o.value = y; o.textContent = y; Y.appendChild(o); });
  }
  function draw() {
    var c = by[M.value], y = Y.value, th = C.value, q = [y ? 'y=' + y : '', th ? 'theme=' + th : ''].filter(Boolean).join('&');
    var src = D.base + '/embed/cars/' + c[1] + '/' + (q ? '?' + q : ''), cred = D.base + '/cars/' + c[1] + '/' + (y ? y + '/' : '');
    var s = '<iframe src="' + src + '" title="' + esc(c[0]) + ' reliability by model year (The Lemon Index)" width="100%" height="' + c[3] + '" style="border:0;max-width:720px" loading="lazy"></iframe>'
      + '<p style="font-size:13px;margin:4px 0 0">Data: <a href="' + cred + '">Lemon Index</a> (' + esc(y ? y + ' ' + c[0] + ' reliability' : c[0] + ' reliability by year') + ')</p>';
    put(document.getElementById('get'), s);
    document.getElementById('emx-prev').href = '/embed/cars/' + c[1] + '/' + (q ? '?' + q : '');
  }
  M.addEventListener('change', function () { years(); draw(); }); Y.addEventListener('change', draw); C.addEventListener('change', draw);
  years(); draw();
})();
