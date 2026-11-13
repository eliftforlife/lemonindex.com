// 11-10 (Elijah): image credits/AI disclosures live behind a small "i" button on each image instead of a visible caption line.
// Markup (from year_slider.info()): <button class="ii" aria-label="Image info" aria-expanded="false" aria-controls="ID">i</button><div class="ii-pop" id="ID" hidden>...</div>
(function () {
  var open = null;
  // 11-12 round 2 (Carlos: the credit popup opened off the left edge of a phone): keep the open popup inside the screen
  function fit(p) {
    p.style.transform = ''; p.style.maxWidth = '';
    var vw = document.documentElement.clientWidth, r = p.getBoundingClientRect();
    if (r.width > vw - 16) { p.style.maxWidth = (vw - 16) + 'px'; r = p.getBoundingClientRect(); }
    var dx = r.left < 8 ? 8 - r.left : r.right > vw - 8 ? vw - 8 - r.right : 0;
    if (dx) p.style.transform = 'translateX(' + Math.round(dx) + 'px)';
  }
  window.addEventListener('resize', function () { if (open) fit(open.pop); });
  function close(focusBtn) {
    if (!open) return;
    open.pop.hidden = true; open.btn.setAttribute('aria-expanded', 'false');
    if (focusBtn) open.btn.focus();
    open = null;
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.ii');
    if (b) {
      e.preventDefault(); e.stopPropagation();
      var p = document.getElementById(b.getAttribute('aria-controls'));
      if (!p) return;
      var same = open && open.btn === b; close(false);
      if (!same) { p.hidden = false; b.setAttribute('aria-expanded', 'true'); open = { btn: b, pop: p }; fit(p); }
      return;
    }
    if (open && !(e.target.closest && e.target.closest('.ii-pop'))) close(false);
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && open) close(true); });
})();
