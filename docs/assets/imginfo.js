// 11-10 (Elijah): image credits/AI disclosures live behind a small "i" button on each image instead of a visible caption line.
// Markup (from year_slider.info()): <button class="ii" aria-label="Image info" aria-expanded="false" aria-controls="ID">i</button><div class="ii-pop" id="ID" hidden>...</div>
(function () {
  var open = null;
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
      if (!same) { p.hidden = false; b.setAttribute('aria-expanded', 'true'); open = { btn: b, pop: p }; }
      return;
    }
    if (open && !(e.target.closest && e.target.closest('.ii-pop'))) close(false);
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && open) close(true); });
})();
