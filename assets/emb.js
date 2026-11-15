// 11-14 /embed/cars/<model>/ (embed_pages.py): ?y=2016 highlights that model year and credits its page; ?theme=light|dark fixes the colors.
(function () {
  var q = new URLSearchParams(location.search), t = q.get('theme'), y = q.get('y'), r = y && /^\d{4}$/.test(y) && document.getElementById('y' + y);
  if (t === 'light' || t === 'dark') document.documentElement.className = t;
  if (!r) return;
  r.className += ' cur';
  var a = document.querySelector('.cr a'); if (a) a.href = a.href.replace(/\/?$/, '/') + y + '/';
})();
