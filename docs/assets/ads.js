// Google AdSense for lemonindex.com (added 11-09). Auto ads; placements and formats are set in the AdSense dashboard.
// Speed: adsbygoogle.js loads after the page has finished loading (like ga.js), so it never competes with the car photos.
// Site ownership is verified by the google-adsense-account meta tag in <head> and /ads.txt, not by this script.
(function () {
  var id = (document.currentScript && document.currentScript.dataset.ads) || 'ca-pub-6568065738106248';
  function go() {
    var s = document.createElement('script');
    s.async = true; s.crossOrigin = 'anonymous';
    s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + id;
    document.head.appendChild(s);
  }
  if (document.readyState === 'complete') setTimeout(go, 0); else addEventListener('load', function () { setTimeout(go, 0); });
})();
