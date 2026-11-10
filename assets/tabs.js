// 11-10 tabbed car pages (tabbed.py). Loaded right after the tab bar (not deferred) so the inactive panels are hidden before they paint.
// Without JS every panel shows. Deep links: #problems, #recalls ... open the tab that holds that element; #p-<tab> opens that tab.
document.documentElement.classList.add('tbjs');
(function () {
  function init() {
    document.querySelectorAll('.tbx').forEach(function (root) {
      var tabs = [].slice.call(root.querySelectorAll('[role=tab]'));
      var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute('aria-controls')); });
      function sel(i, focus, setHash) {
        tabs.forEach(function (t, j) {
          var on = j === i; t.setAttribute('aria-selected', on ? 'true' : 'false'); t.tabIndex = on ? 0 : -1;
          panels[j].classList.toggle('on', on);
        });
        if (focus) tabs[i].focus();
        if (setHash) { try { history.replaceState(null, '', '#' + tabs[i].dataset.h); } catch (e) {} }
        tabs[i].scrollIntoView({ block: 'nearest', inline: 'nearest' });
      }
      function fromHash(scroll) {
        var h = decodeURIComponent((location.hash || '').slice(1)); if (!h) return false;
        var el = document.getElementById(h) || document.getElementById('p-' + h); if (!el) return false;
        for (var i = 0; i < panels.length; i++) {
          if (panels[i] === el || panels[i].contains(el)) {
            sel(i, false, false);
            if (scroll && el !== panels[i]) setTimeout(function () { el.scrollIntoView({ block: 'start' }); }, 0);
            return true;
          }
        }
        return false;
      }
      tabs.forEach(function (t, i) {
        t.addEventListener('click', function () { sel(i, false, true); });
        t.addEventListener('keydown', function (e) {
          var k = e.key, n = tabs.length, j = null;
          if (k === 'ArrowRight') j = (i + 1) % n; else if (k === 'ArrowLeft') j = (i - 1 + n) % n; else if (k === 'Home') j = 0; else if (k === 'End') j = n - 1;
          if (j !== null) { e.preventDefault(); sel(j, true, true); }
        });
      });
      fromHash(true);
      window.addEventListener('hashchange', function () { fromHash(true); });
      // in-page links (#recalls, #fixes, #years ...) open the tab that holds their target
      document.addEventListener('click', function (e) {
        var a = e.target.closest && e.target.closest('a[href^="#"]'); if (!a) return;
        var id = a.getAttribute('href').slice(1), el = id && document.getElementById(id); if (!el) return;
        for (var i = 0; i < panels.length; i++) if (panels[i].contains(el) && !panels[i].classList.contains('on')) { sel(i, false, false); break; }
      });
    });
    // Years / Engines toggle inside the chart
    document.querySelectorAll('.tg').forEach(function (tg) {
      var bs = [].slice.call(tg.querySelectorAll('.tg-o')), vs = [].slice.call(tg.querySelectorAll('.tg-v'));
      bs.forEach(function (b) {
        b.addEventListener('click', function () {
          bs.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
          vs.forEach(function (v) { v.classList.toggle('on', v.dataset.v === b.dataset.v); });
        });
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
