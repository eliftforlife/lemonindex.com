// Google Analytics 4 for lemonindex.com (added 11-08 for the Mediavine Journey application, which reads GA4 sessions).
// 11-09 phone speed: gtag.js is ~180 KB, so it now loads once the page has finished loading instead of competing with the car photos.
// Page views are still sent (gtag replays the queued commands); only a visit that closes the tab before the page loads goes uncounted.
(function () {
  var id = (document.currentScript && document.currentScript.dataset.ga) || 'G-3352CDDC5E';
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { dataLayer.push(arguments); };
  gtag('js', new Date());
  gtag('config', id);
  function go() { var s = document.createElement('script'); s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + id; document.head.appendChild(s); }
  if (document.readyState === 'complete') setTimeout(go, 0); else addEventListener('load', function () { setTimeout(go, 0); });
})();
