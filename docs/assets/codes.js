// Engine code lookup (11-10). Client-side only: /assets/codes.json loads on first focus/typing; nothing is sent or saved.
(function () {
  var q = document.getElementById('cs-q'), out = document.getElementById('cs-out'), form = q && q.form;
  if (!q || !out) return;
  var data = null, loading = null;
  var SYS = { P: 'Powertrain (engine and transmission)', B: 'Body (airbags, seats, lights, locks)', C: 'Chassis (brakes, steering, suspension)', U: 'Network (how the car’s computers talk to each other)' };
  var SEV = { 1: ['Drive on, get it checked', 'You can usually keep driving. Get the code checked when you can.'],
              2: ['Get it fixed soon', 'Fix it soon. Waiting can lead to a bigger repair or a breakdown.'],
              3: ['Stop and fix now', 'Don’t put it off. This can affect safety, stall the car or cause expensive damage.'] };
  var SEVW = ['Fix soon', 'Fix it soon. Stop driving if the car slips, shakes, overheats or warns you.'];
  function st(x) { return x.w ? SEVW : SEV[x.s]; }
  function load() {
    if (data) return Promise.resolve(data);
    if (!loading) loading = fetch('/assets/codes.json?v=2').then(function (r) { return r.json(); }).then(function (j) { data = j; return j; });
    return loading;
  }
  function esc(s) { var d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }
  function norm(s) {
    s = (s || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (/^[0-9A-F]{4}$/.test(s) && /^[0-3]/.test(s)) s = 'P' + s;           // 0420 -> P0420
    if (/^[0-9]{3}$/.test(s)) s = 'P0' + s;                                  // 420 -> P0420
    if (/^[PBCU][0-9A-F]{3}$/.test(s)) s = s[0] + '0' + s.slice(1);          // P420 -> P0420
    return s;
  }
  function gauge(s, w) {
    var a = { 1: -60, 2: 0, 3: 60 }[s];
    return '<figure class="cgauge sm s' + s + '"><svg viewBox="0 0 200 112" aria-hidden="true"><path d="M14 100 A86 86 0 0 1 57 25" class="g1"/><path d="M61 23 A86 86 0 0 1 139 23" class="g2"/><path d="M143 25 A86 86 0 0 1 186 100" class="g3"/>' +
      '<g transform="rotate(' + a + ' 100 100)"><line x1="100" y1="100" x2="100" y2="30" class="nd"/></g><circle cx="100" cy="100" r="8" class="hub"/></svg><figcaption>' + esc(w ? SEVW[0] : SEV[s][0]) + '</figcaption></figure>';
  }
  function structure(c) {
    var gen = (c[0] === 'P' && (c[1] === '0' || c[1] === '2' || c.slice(0, 3) === 'P34')) || (c[0] !== 'P' && c[1] === '0');
    return '<p class="cs-sys"><b>' + esc(c[0]) + '</b> = ' + esc(SYS[c[0]]) + '. <b>' + esc(c[1]) + '</b> = ' + (!gen ? 'a manufacturer code (each carmaker sets the meaning)' : c[0] === 'P' ? 'a generic code (same meaning on every car)' : 'a code from the standard list, though carmakers often use these their own way') + '.</p>';
  }
  function render(raw) {
    var c = norm(raw);
    if (!c) { out.innerHTML = ''; return; }
    if (!/^[PBCU][0-3][0-9A-F]{3}$/.test(c)) {
      out.innerHTML = '<div class="cs-card cs-bad"><p><b>' + esc(raw) + '</b> doesn’t look like an engine code. They look like <b>P0420</b>: a letter (P, B, C or U) and four characters.</p></div>';
      return;
    }
    load().then(function (j) {
      var x = j.codes[c], h = '<div class="cs-card"><div class="cs-top"><div class="cs-code"><span>' + esc(SYS[c[0]].split(' (')[0]) + '</span><b>' + c + '</b></div>' + (x && x.s ? gauge(x.s, x.w) : '') + '</div>';
      if (x && x.t) {
        h += '<h3>' + esc(x.t) + '</h3>' + (x.mf ? '<p class="cs-note">This meaning is for ' + esc(x.mf.join(', ')) + '. On other makes it can differ.</p>' : '') +
             '<p>' + esc(x.m) + '</p><p><b>' + esc(st(x)[0]) + '.</b> ' + esc(st(x)[1]) + '</p>' +
             '<p class="cs-k">Common causes</p><ul>' + x.c.map(function (k) { return '<li>' + esc(k) + '</li>'; }).join('') + '</ul>';
      } else if (x) {
        var mfr = !((c[0] === 'P' && (c[1] === '0' || c[1] === '2' || c.slice(0, 3) === 'P34')) || (c[0] !== 'P' && c[1] === '0'));
        h += '<h3>' + (mfr ? 'Manufacturer-specific code' : 'Meaning not checked yet') + '</h3><p>' + (mfr ? 'Each carmaker decides what ' + c + ' means' : 'Its exact meaning can depend on the make') + ', and we haven’t verified it yet. A dealer or a scanner with the maker’s software can tell you exactly.</p>' + structure(c);
      } else {
        h += '<h3>Not in our list yet</h3><p>No owner complaint we’ve read names ' + c + ', and we don’t have a verified meaning for it yet.</p>' + structure(c);
      }
      if (x && x.n) {
        h += '<p class="cs-data">Owners named ' + c + ' in <b>' + x.n.toLocaleString() + '</b> complaints to the U.S. government' +
             (x.top && x.top.length ? ', most on the ' + x.top.map(function (t) { return '<a href="/cars/' + t[0] + '/">' + esc(t[1]) + '</a> (' + t[2] + ')'; }).join(', ') + '.' :
              (x.mk && x.mk.length ? ', mostly on ' + esc(x.mk.join(', ')) + '.' : '.')) + '</p>';
      }
      if (x && x.p) h += '<a class="cs-go" href="/check-engine-light/' + c.toLowerCase() + '/">Full ' + c + ' page →</a>';
      out.innerHTML = h + '</div>';
    }).catch(function () { out.innerHTML = '<div class="cs-card cs-bad"><p>Couldn’t load the code list. Check your connection and try again.</p></div>'; });
  }
  q.addEventListener('focus', load, { once: true });
  var t; q.addEventListener('input', function () { clearTimeout(t); var v = q.value; t = setTimeout(function () { if (norm(v).length >= 5) render(v); else if (!v) out.innerHTML = ''; }, 120); });
  if (form) form.addEventListener('submit', function (e) { e.preventDefault(); render(q.value); });
  var m = /[?&]code=([^&#]+)/.exec(location.search);
  if (m) { q.value = decodeURIComponent(m[1]).slice(0, 8); render(q.value); }
})();
