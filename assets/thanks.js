// /thanks/ (thanks_page.py): the Share button and the donor request form. 11-25: moved out of the page, because the site CSP
// (script-src 'self' + one hash) blocked it as an inline script. Marking the visitor as paid is support.js's job.
(function () {
  var b = document.getElementById('thx-share'); if (!b) return;
  var f = document.getElementById('thx-req');
  if (f) f.addEventListener('submit', function (e) {
    e.preventDefault(); var t = document.getElementById('thx-req-t').value.trim(), m = f.querySelector('.thx-req-m');
    if (t.length < 2) { m.textContent = 'Type a car or a feature first.'; return; }
    var sid = new URLSearchParams(location.search).get('session_id') || '';
    m.textContent = 'Sending...';
    fetch('https://lemon-survey.elift08.workers.dev/donor-request', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request: t, session: sid, page: location.pathname, hp: document.getElementById('thx-req-hp').value }) })
      .then(function (r) { m.textContent = r.ok ? 'Got it. Thank you, it goes to the front of the line.' : (r.status === 429 ? 'Too many sends today. Try again tomorrow.' : 'That didn’t send. Try again in a minute.'); if (r.ok) f.querySelector('textarea').value = ''; })
      .catch(function () { m.textContent = 'That didn’t send. Check your connection and try again.'; });
  });
  b.addEventListener('click', function () {
    var d = { title: 'The Lemon Index', text: 'Check any car for problems before you buy it. Free, from real owner complaints.', url: 'https://lemonindex.com/' };
    if (navigator.share) { navigator.share(d).catch(function () {}); return; }
    try { navigator.clipboard.writeText(d.url); b.textContent = 'Link copied'; } catch (e) { b.textContent = 'lemonindex.com'; }
  });
})();
