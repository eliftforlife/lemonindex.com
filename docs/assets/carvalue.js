/* 11-26 /car-value/ (car_value_pages.py): "What's this car worth?". Data: /assets/carvalue.json (data_car_value.py).
   base() = prices_brackets.price_at() for no trim, checklist_template.html price() for a picked trim; tools/check_car_value.py checks it.
   Then the rules of thumb: Rough x0.80, Great x1.08 (never above the price-new caps), salvage = low x0.60 / high x0.80. ?m=&y=&t=&mi=&c=&ti= */
(function () {
  var D = null, st = {c: 'average', ti: 'clean'};
  var K = {rough: 0.8, average: 1, great: 1.08};
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); };
  var money = function (v) { return '$' + Math.round(v).toLocaleString('en-US'); };
  // Python's round(): half to even (prices_brackets.rnd)
  function rnd(v, s) { var x = v / s, fl = Math.floor(x), d = x - fl, r = d > 0.5 ? fl + 1 : d < 0.5 ? fl : (fl % 2 === 0 ? fl : fl + 1); return r * s; }
  function trimsOf(o, y) { return (o.t || []).filter(function (r) { return r[1] <= y && y <= r[2]; }); }
  function trimRow(o, y, t) { return t ? trimsOf(o, y).filter(function (r) { return r[0] === t; })[0] || null : null; }
  // unrounded [private lo, hi], [dealer lo, hi] plus the caps that applied; null = no price for that year
  function base(o, y, t, miles) {
    var tr = trimRow(o, y, t), T = tr && tr[3] === -1 ? o.ty[t] : null, a = tr && !T ? tr[3] : 1, na = tr && !T ? tr[4] : 1, p;
    if (T) { var r = T.y[y]; if (!r) return null; p = {lo: r[0], hi: r[1], mi: r[2], nw: T.n[y] || 0}; }
    else { var q = o.y[y]; if (!q) return null; p = {lo: q[0], hi: q[1], mi: q[2], nw: q[3]}; }
    var m = miles > 0 ? miles : p.mi, age = D.now - y, rate = 0;
    o.mi[0].forEach(function (x) { if (age >= x[0]) rate = x[1]; });
    var fm = Math.min(o.mi[2], Math.max(o.mi[1], 1 + rate * (p.mi - m) / 10000));
    var pp = [p.lo * fm * a, p.hi * fm * a], pcap = T ? T.pc : o.pc, dcap = T ? (T.cap || o.cap) : o.cap, pc = 0, dc = 0;
    if (p.nw && pcap) { pc = p.nw * na * pcap; if (pp[1] > pc) { pp[1] = pc; pp[0] = Math.min(pp[0], pc * 0.85); } }
    var dl = pp.map(function (v) { return v * o.d[0] + o.d[1] * Math.min(1, v / 8000); });
    if (p.nw) { dc = p.nw * na * dcap; dl[1] = Math.min(dl[1], dc); dl[0] = Math.min(dl[0], dl[1] * 0.88); }
    dl[0] = Math.max(dl[0], pp[0] * 1.05); dl[1] = Math.max(dl[1], pp[1] * 1.05);
    return {pp: pp, dl: dl, mi: m, typ: p.mi, pc: pc, dc: dc};
  }
  function value(o, y, t, miles, c, ti) {
    var b = base(o, y, t, miles); if (!b) return null;
    var k = K[c] || 1, pp = b.pp.map(function (v) { return v * k; }), dl = b.dl.map(function (v) { return v * k; });
    if (c === 'great') {   // never above the price-new caps the data already uses
      if (b.pc) { pp[1] = Math.min(pp[1], Math.max(b.pc, b.pp[1])); pp[0] = Math.min(pp[0], pp[1] * 0.9); }
      if (b.dc) { dl[1] = Math.min(dl[1], Math.max(b.dc, b.dl[1])); dl[0] = Math.min(dl[0], dl[1] * 0.9); }
      dl[0] = Math.max(dl[0], pp[0] * 1.05); dl[1] = Math.max(dl[1], pp[1] * 1.05);
    }
    if (ti === 'salvage') { pp = [pp[0] * 0.6, pp[1] * 0.8]; dl = [dl[0] * 0.6, dl[1] * 0.8]; }
    var R = function (v) { return rnd(v, o.r); };
    pp = pp.map(R); dl = dl.map(R);
    if (pp[1] <= pp[0]) pp[1] = pp[0] + o.r; if (dl[1] <= dl[0]) dl[1] = dl[0] + o.r;
    return {pp: pp, dl: dl, mi: b.mi, typ: b.typ};
  }
  window.LX_CV = {base: base, value: value, rnd: rnd, data: function (d) { if (d) D = d; return D; }};   // tools/check_car_value.py

  var f = document.getElementById('cvf'), out = document.getElementById('cvo'); if (!f || !out) return;
  var $ = function (id) { return document.getElementById(id); };
  var sMk = $('cv-mk'), sM = $('cv-m'), sY = $('cv-y'), sT = $('cv-t'), iMi = $('cv-mi'), wT = f.querySelector('.cv-trim');

  function opts(sel, list, first) { sel.innerHTML = (first ? '<option value="">' + esc(first) + '</option>' : '') + list.map(function (x) { return '<option value="' + esc(x[0]) + '">' + esc(x[1]) + '</option>'; }).join(''); }
  function years(o) {   // every year from the first priced one to the last, newest first (a gap year says we have no price yet)
    var ys = Object.keys(o.y).map(Number), lo = Math.min.apply(null, ys), hi = Math.max.apply(null, ys), r = [];
    for (var y = hi; y >= lo; y--) r.push(y); return r;
  }
  function fillModels() {
    var mk = sMk.value, ms = Object.keys(D.m).filter(function (id) { return D.m[id].b === mk; })
      .sort(function (a, b) { return D.m[a].n.localeCompare(D.m[b].n); }).map(function (id) { return [id, D.m[id].n]; });
    opts(sM, ms, 'Model'); sM.disabled = !mk; fillYears();
  }
  function fillYears() {
    var o = D.m[sM.value]; opts(sY, o ? years(o).map(function (y) { return [y, y]; }) : [], 'Year'); sY.disabled = !o; fillTrims();
  }
  function fillTrims() {
    var o = D.m[sM.value], y = +sY.value, ts = o && y ? trimsOf(o, y) : [], cur = sT.value;
    opts(sT, ts.map(function (r) { return [r[0], r[0]]; }), 'Not sure'); wT.hidden = !ts.length;
    if (ts.some(function (r) { return r[0] === cur; })) sT.value = cur;
  }
  function miles() { var v = parseInt(String(iMi.value).replace(/[^0-9]/g, ''), 10); return v > 0 && v < 1000000 ? v : 0; }
  function seg() { f.querySelectorAll('.cv-seg button').forEach(function (b) { var k = b.dataset.c ? 'c' : 'ti'; b.setAttribute('aria-pressed', b.dataset[k] === st[k] ? 'true' : 'false'); }); }
  function url() {
    var q = [];
    if (sM.value) q.push('m=' + encodeURIComponent(sM.value));
    if (sY.value) q.push('y=' + sY.value);
    if (sT.value && !wT.hidden) q.push('t=' + encodeURIComponent(sT.value));
    if (miles()) q.push('mi=' + miles());
    if (sM.value) { q.push('c=' + st.c); q.push('ti=' + st.ti); }
    try { history.replaceState(null, '', location.pathname + (q.length ? '?' + q.join('&') : '')); } catch (_) {}
  }
  function show() {
    seg(); url();
    var id = sM.value, o = D.m[id], y = +sY.value;
    if (!o || !y) { out.innerHTML = '<p class="cv-empty">' + (!sMk.value ? 'Pick a make, model and year.' : !o ? 'Now pick the model.' : 'Now pick the year.') + '</p>'; return; }
    var name = y + ' ' + o.b + ' ' + o.n, t = wT.hidden ? '' : sT.value;
    var rep = o.k === 's' ? '/supercars/' + id + '/' : (o.np && o.np.indexOf(y) >= 0) ? '/cars/' + id + '/' : '/cars/' + id + '/' + y + '/';
    var link = '<a class="cv-rep" href="' + rep + '">See the ' + esc(o.k === 's' || rep.split('/').length < 5 ? o.b + ' ' + o.n : name) + ' report <span aria-hidden="true">›</span></a>';
    var v = value(o, y, t, miles(), st.c, st.ti);
    if (!v) { out.innerHTML = '<p class="cv-none">We don&#39;t have prices for the ' + esc(name) + ' yet.</p>' + link; return; }
    var mi = miles() ? 'At ' + v.mi.toLocaleString('en-US') + ' miles' : 'About ' + (Math.round(v.typ / 1000) * 1000).toLocaleString('en-US') + ' miles assumed';
    out.innerHTML = '<div class="cv-res"><p class="cv-name">' + esc(name + (t ? ' ' + t : '')) + '</p>'
      + '<p class="cv-k">Private sale</p><p class="cv-big' + (money(v.pp[0]).length + money(v.pp[1]).length > 14 ? ' cv-long' : '') + '"><span>' + money(v.pp[0]) + '</span> <span class="cv-to">–</span> <span>' + money(v.pp[1]) + '</span></p>'
      + '<p class="cv-dl">Dealer: about <span>' + money(v.dl[0]) + ' – ' + money(v.dl[1]) + '</span></p>'
      + '<p class="cv-mi">' + mi + (st.ti === 'salvage' ? ' · salvage title' : '') + '</p></div>'
      + '<details class="cv-how"><summary>AI estimate, not an appraisal</summary><div class="cv-hb">'
      + '<p>Lemon Index AI estimate (' + esc(D.date) + ') of a fair price for this model year, adjusted for your miles' + (o.t ? ' and trim' : '') + '. Not listings, sales records or an appraisal.</p>'
      + '<p>Rough: about 20% less. Great: about 8% more, never above its price new. Salvage or rebuilt title: 40% under the low end to 20% under the high end of a clean car&#39;s range.</p>'
      + '<p>Dealer = what a lot typically asks. Check local listings before you sell or buy.</p></div></details>' + link;
  }
  function fromUrl() {
    var P = {}; location.search.slice(1).split('&').forEach(function (kv) { var i = kv.indexOf('='); if (i > 0) try { P[kv.slice(0, i)] = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, ' ')); } catch (_) {} });
    var o = D.m[P.m];
    if (o) { sMk.value = o.b; fillModels(); sM.value = P.m; fillYears(); if (P.y && sY.querySelector('option[value="' + (+P.y) + '"]')) { sY.value = +P.y; fillTrims(); } }
    if (o && P.t && !wT.hidden && trimsOf(o, +sY.value).some(function (r) { return r[0] === P.t; })) sT.value = P.t;
    if (/^\d{1,6}$/.test(P.mi || '')) iMi.value = (+P.mi).toLocaleString('en-US');
    if (K[P.c]) st.c = P.c; if (P.ti === 'clean' || P.ti === 'salvage') st.ti = P.ti;
  }
  sMk.addEventListener('change', function () { fillModels(); show(); });
  sM.addEventListener('change', function () { fillYears(); show(); });
  // phones: the first price shows under the form; bring it into view once the year is picked
  sY.addEventListener('change', function () { fillTrims(); show(); var r = out.getBoundingClientRect();
    if (sY.value && r.top > innerHeight - 140) try { out.scrollIntoView({behavior: 'smooth', block: 'center'}); } catch (_) { out.scrollIntoView(); } });
  sT.addEventListener('change', show);
  iMi.addEventListener('input', show);
  iMi.addEventListener('blur', function () { var m = miles(); iMi.value = m ? m.toLocaleString('en-US') : ''; });
  f.addEventListener('submit', function (e) { e.preventDefault(); show(); });
  f.addEventListener('click', function (e) { var b = e.target.closest('.cv-seg button'); if (!b) return; if (b.dataset.c) st.c = b.dataset.c; else st.ti = b.dataset.ti; show(); });
  out.innerHTML = '<p class="cv-empty">Loading prices…</p>';
  fetch('/assets/carvalue.json?v=1').then(function (r) { return r.json(); }).then(function (d) { D = d; fromUrl(); show(); })
    .catch(function () { out.innerHTML = '<p class="cv-none">Prices didn&#39;t load. Refresh the page to try again.</p>'; });
})();
