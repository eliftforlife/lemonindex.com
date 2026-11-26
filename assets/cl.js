// 11-25 Lemon Index checklist wizard (lemon-store). The approved mockup (3 Lemon Index/checklist/wizard mockup 11-25), wired to the
// lemon-store Worker. This file holds NO paid content: the checklist (GET /content) and the answer (POST /answer: the offer engine runs
// in the Worker) arrive only after sign-in, for an account that owns them, and are kept in memory, never in storage.
// Pages: /checklist/<gen>/ (data-page="checklist"), /account/ ("account"), /account/signin/ ("signin"). Config: #cl-cfg (JSON).
(function () {
  'use strict';
  var CFG = JSON.parse(document.getElementById('cl-cfg').textContent), API = CFG.api, TEASE = CFG.teaser || null, GEN = CFG.gen || null;
  // 11-26 from the store's year buttons (?y=2021): the cards say "2021 3 Series" instead of the generation's year range
  (function () { var y = null; try { y = new URLSearchParams(location.search).get('y'); } catch (e) {}
    var r = TEASE && /^\d{4}$/.test(y || '') && /(\d{4})–(\d{4})$/.exec(TEASE.title || '');
    if (r && +y >= +r[1] && +y <= +r[2]) TEASE.title = y + ' ' + TEASE.short; })();
  var app = document.getElementById('app');

  // ---------------- small helpers ----------------
  var IC = {
    check: '<path d="M20 6 9 17l-5-5"/>', x: '<path d="M18 6 6 18M6 6l12 12"/>', back: '<path d="m15 18-6-6 6-6"/>', chev: '<path d="m9 18 6-6-6-6"/>',
    bang: '<path d="M12 7v6"/><path d="M12 17.5h.01"/>', q: '<path d="M9.2 9a3 3 0 0 1 5.6 1c0 2-2.8 2.8-2.8 2.8"/><path d="M12 17.5h.01"/>',
    lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>', mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>', store: '<path d="M3 9 4.5 4h15L21 9"/><path d="M4 9v11h16V9"/><path d="M9 20v-6h6v6"/>',
    tag: '<path d="M12.6 2.6A2 2 0 0 0 11.2 2H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    wallet: '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>', chat: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    share: '<path d="M12 3v13M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/>', shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>',
    wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9z"/>',
    ext: '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>', help: '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  };
  var ic = function (n, s, w) { return '<svg width="' + (s || 22) + '" height="' + (s || 22) + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="' + (w || 1.9) + '" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + IC[n] + '</svg>'; };
  var LOGO = '<svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true"><ellipse cx="16" cy="17" rx="12" ry="9.5" transform="rotate(-20 16 17)" fill="#ffd400" stroke="#1d1d1f" stroke-width="2"/><path d="M9 20a8 8 0 0 1 13-7" fill="none" stroke="#1d1d1f" stroke-width="2" stroke-linecap="round"/><path d="m16 18 4-5" stroke="#1d1d1f" stroke-width="2.2" stroke-linecap="round"/></svg>';
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]; }); };
  var $f = function (n) { return '$' + Math.round(n).toLocaleString('en-US'); };
  var $r = function (c) { return c[0] === c[1] ? $f(c[0]) : $f(c[0]) + '–' + $f(c[1]); };
  var desk = function () { return innerWidth >= 900; };
  var store = {get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
    del: function (k) { try { localStorage.removeItem(k); } catch (e) {} }};
  var CHAPTERS = ['Before you go', 'Walk around it', 'Tires and brakes', 'Under the hood', 'Start it', 'A/C, then heat', 'Inside', 'Test drive', 'Paperwork', 'Your answer'];

  // ---------------- the store API: a bearer token in localStorage (the Worker is on workers.dev, so no cookie) ----------------
  var TK = 'li-store-token', DK = 'li-store-dev';
  function token() { try { var t = JSON.parse(store.get(TK) || 'null'); return t && t.t && t.exp * 1000 > Date.now() ? t.t : null; } catch (e) { return null; } }
  function setToken(t, exp) { store.set(TK, JSON.stringify({t: t, exp: exp})); }
  function dropLocal() { store.del(TK); try { Object.keys(localStorage).forEach(function (k) { if (k.indexOf('lcw:') === 0) localStorage.removeItem(k); }); } catch (e) {} }
  function device() { var d = store.get(DK); if (!d || !/^[A-Za-z0-9_-]{16,64}$/.test(d)) { var r = new Uint8Array(18); crypto.getRandomValues(r); d = btoa(String.fromCharCode.apply(null, r)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); store.set(DK, d); } return d; }
  function api(method, path, body, keep) {
    var h = {}, t = token(); if (t) h.Authorization = 'Bearer ' + t; if (body !== undefined) h['Content-Type'] = 'application/json';
    return fetch(API + path, {method: method, headers: h, body: body === undefined ? undefined : JSON.stringify(body), credentials: 'omit', cache: 'no-store', keepalive: !!keep})
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (r.status === 401 && t) store.del(TK); j._s = r.status; return j; }); })
      .catch(function () { return {_s: 0, error: 'offline'}; });
  }
  var ME = null;
  function loadMe() {
    if (!token()) { ME = null; return Promise.resolve(null); }
    return api('GET', '/me').then(function (j) { if (j._s !== 200) { ME = null; return null; } if (j.rotate) setToken(j.rotate.token, j.rotate.exp); ME = j; return j; });
  }
  var owns = function (g) { return !!ME && (ME.all || ME.free === g || (ME.owned || []).indexOf(g) >= 0); };

  // ---------------- shells (the mockup's) ----------------
  function siteNav() {
    return '<div class="nav"><a class="lg" href="/">' + LOGO + 'The Lemon Index</a><span class="sp"></span>' + (desk() ? '<a class="nl" href="/cars/">Cars</a><a class="nl" href="/checklist/">Checklists</a>' : '') +
      '<a class="nl" href="/account/">' + (token() ? 'My checklists' : 'Sign in') + '</a></div>';
  }
  function shell(inner, o) {
    o = o || {}; var ch = o.ch || 0, frac = o.frac || 0;
    var pg = CHAPTERS.map(function (c, j) { var n = j + 1; return n < ch ? '<i class="dn"></i>' : n === ch ? '<i><b style="width:' + Math.max(8, frac * 100) + '%"></b></i>' : '<i></i>'; }).join('');
    var head = '<div class="ah"><div class="ahr"><button class="ib" data-back="1" aria-label="Back">' + (o.back === false ? '' : ic('back', 24)) + '</button><div class="ct">' + esc(o.title || '') + (o.sub ? '<small>' + esc(o.sub) + '</small>' : '') +
      '</div><a class="ib" href="' + (o.close || '/account/') + '" aria-label="Close">' + ic('x', 22) + '</a></div>' + (ch ? '<div class="pg">' + pg + '</div>' : '') + '</div>';
    var body = head + '<div class="ab">' + inner + '</div>' + (o.foot ? '<div class="ft">' + o.foot + '</div>' : '');
    return (o.top || '') + (desk() ? siteNav() + '<div class="app"><div class="wrap' + (o.w ? ' w' : '') + '">' + body + '</div></div>' : '<div class="app">' + body + '</div>');
  }
  function backdrop() {
    var T = TEASE || {};
    return '<div class="bk">' + siteNav() + '<div class="bk-h"><h1>' + esc(T.title || 'Before-you-buy checklists') + '</h1><p>' + esc(T.line || '') + '</p>' + (T.img ? '<img src="' + esc(T.img) + '" alt="">' : '') + '</div><div class="bk-g"></div><div class="bk-g"></div></div>';
  }
  // 11-26 (Elijah): opened from the list of every checklist, X goes back to that list, not to the car page
  function sheetClose() { try { var r = document.referrer && new URL(document.referrer); if (r && r.origin === location.origin && r.pathname === '/checklist/') return '/checklist/'; } catch (e) {} return TEASE ? TEASE.home : '/'; }
  function sheet(body, o) {
    o = o || {};
    return backdrop() + '<div class="dim"></div><div class="sh" role="dialog" aria-modal="true"><div class="gr"></div><div class="sh-top"><span>' + (o.back ? '<button data-back="1">‹ Back</button>' : '') + '</span><span>' + esc(o.top || '') +
      '</span><a class="x" href="' + sheetClose() + '" aria-label="Close">' + ic('x', 18) + '</a></div>' + (o.bar ? '<div class="bar"><i style="width:' + o.bar + '%"></i></div>' : '') + body + (o.foot ? '<div class="sf">' + o.foot + '</div>' : '') + '</div>';
  }
  function hk(o) {
    var pic = o.img2 ? '<span class="hk-p two"><img src="' + o.img2 + '" alt=""><img src="' + o.img + '" alt=""></span>' : o.img ? '<span class="hk-p"><img src="' + esc(o.img) + '" alt=""></span>' : '';
    return '<' + (o.href ? 'a href="' + esc(o.href) + '"' : 'div') + ' class="hk-c ' + (o.cls || '') + '">' + (o.badge ? '<span class="bdg">' + o.badge + '</span>' : '') + '<span class="hk-t"><b>' + esc(o.name) + '</b>' +
      (o.small ? '<small>' + esc(o.small) + '</small>' : '') + (o.price ? '<span class="hp">' + o.price + '</span>' : '') + '</span>' + pic + (o.ok ? '<span class="okb">' + ic('check', 22, 3) + '</span>' : '') + '</' + (o.href ? 'a' : 'div') + '>';
  }
  var ALLCARS = {img: '/assets/ai-models/ford-f-series.webp', img2: '/assets/ai-models/honda-civic.webp'};
  // 11-26 (Elijah: back got stuck between 'Which year?' and 'Who is selling it?'): only a step forward adds a history entry (push); toggles,
  // answers and the in-app Back replace the current one. Back = history.back() when this entry was pushed from the step before it.
  var go = function (h, push) {
    if (location.hash === h || (location.hash === '' && h === '#')) return render();
    var u = location.pathname + location.search + h, from = location.hash || '#';
    if (push) history.pushState({cl: 1, from: from}, '', u); else history.replaceState({cl: 1, from: history.state && history.state.from || null}, '', u);
    render();
  };

  // ======================================================================== the checklist page
  var DOC = null, S = null, RES = null, RES_KEY = '', SAVE_T = null, BUSY = false, PEND = false;
  var SK = function () { return 'lcw:' + GEN; };
  function freshS() { var ys = Object.keys(DOC.ys).sort(); return {v: 1, y: ys.length === 1 ? ys[0] : null, seller: null, stype: null, trim: null, eng: null, tr: null, drive: null, cab: null, miles: '', ask: '', rec: null, tax: null, ans: {}, unk: {}, quote: {}, full: false, papers: {}, vin: '', i: 0, at: 0}; }
  function saveS(sync) {
    S.at = Date.now(); store.set(SK(), JSON.stringify(S));
    if (sync === false) return;
    PEND = true; clearTimeout(SAVE_T); SAVE_T = setTimeout(function () { pushS(false); }, 2000);
  }
  function pushS(keep) { if (!PEND || !S) return; PEND = false; clearTimeout(SAVE_T); api('PUT', '/progress', {gen: GEN, data: S}, keep); }   // keep: the page is closing (fetch keepalive)
  function loadS() {
    var loc = null; try { loc = JSON.parse(store.get(SK()) || 'null'); } catch (e) {}
    return api('GET', '/progress?gen=' + GEN).then(function (j) {
      var srv = j && j.data && j.data.v === 1 ? j.data : null;
      S = (srv && (!loc || (srv.at || 0) >= (loc.at || 0))) ? srv : loc || freshS();
      if (!S.ans) S.ans = {}; if (!S.unk) S.unk = {}; if (!S.quote) S.quote = {}; if (!S.papers) S.papers = {};
      // 11-26 the store's year buttons open /checklist/<gen>/?y=<year>: pick that year unless this checklist already has one
      var PY = null; try { PY = new URLSearchParams(location.search).get('y'); } catch (e) {}
      if (!S.y && PY && DOC.ys[PY]) S.y = PY;
      store.set(SK(), JSON.stringify(S));
    });
  }
  // the year's car, as the buyer picked it
  var Y = function () { return S && S.y && DOC.ys[S.y] ? DOC.ys[S.y] : null; };
  var dlr = function () { return S.seller === 'dealer'; };
  function trimO() { var y = Y(); return y && S.trim ? y.trims.filter(function (t) { return t.t === S.trim; })[0] || null : null; }
  function engName() { var y = Y(), t = trimO(); if (t) { var vs = Object.keys(t.eng || {}).map(function (k) { return t.eng[k]; }); if (vs.length && vs.every(function (v) { return v === vs[0]; })) return vs[0]; }
    if (S.eng != null && y.eng2[S.eng]) return y.eng2[S.eng].name; return y.eng2.length === 1 ? y.eng2[0].name : null; }
  function trLock() { var t = trimO(); return t && t.tr !== 'both' ? t.tr : null; }
  function drives() { var y = Y(), out = [], tm = trimO() ? trimO().t : null;
    (y.driveR || []).some(function (r) { var f = r.fit; if (f && f.trim && tm && f.trim.indexOf(tm) < 0) return false; if (f && f.not_trim && tm && f.not_trim.indexOf(tm) >= 0) return false;
      (r.opts || []).forEach(function (o) { if (out.indexOf(o) < 0) out.push(o); }); return !f || !!tm; });
    return out.length ? out : (y.drives || []); }
  function fitOk(f) {
    if (!f) return true;
    var tm = trimO() ? trimO().t : null, en = engName(), tr = trLock() || S.tr, dv = S.drive || (drives().length === 1 ? drives()[0] : null);
    if (f.trim && tm && f.trim.indexOf(tm) < 0) return false; if (f.not_trim && tm && f.not_trim.indexOf(tm) >= 0) return false;
    if (f.eng && en && f.eng.indexOf(en) < 0) return false; if (f.not_eng && en && f.not_eng.indexOf(en) >= 0) return false;
    if (f.tr && tr && f.tr !== tr) return false;
    if (f.drive && dv) { var L = [].concat(f.drive).map(String), all = function (x) { return x === 'awd' || x === '4wd'; }; if (L.indexOf(dv) < 0 && !(all(dv) && L.some(all))) return false; }
    if (f.cab && S.cab && [].concat(f.cab).map(function (c) { return String(c).toLowerCase(); }).indexOf(S.cab.toLowerCase()) < 0) return false;
    return true;
  }
  var sel = function () { return dlr() ? 'd' : 'p'; };
  function checkKeys() {
    var y = Y(); if (!y) return [];
    var ks = S.full ? y.ids : y.quick, seen = {};
    return ks.filter(function (k) { var c = DOC.checks[k]; if (!c || seen[k.split('@')[0]]) return false; if (c.seller && c.seller !== sel()) return false; if (!fitOk(c.fit)) return false; seen[k.split('@')[0]] = 1; return true; })
      .sort(function (a, b) { return DOC.checks[a].ch - DOC.checks[b].ch; });
  }
  function seq() {
    var y = Y(), st = [{ch: 1, k: 'seller'}];
    if (Object.keys(DOC.ys).length > 1) st.push({ch: 1, k: 'year'});
    if (y && y.trims.length > 1) st.push({ch: 1, k: 'trim'});
    if (y && (drives().length > 1 || (!trLock() && y.manual) || (y.cabs || []).length > 1 || (!trimO() && y.eng2.length > 1))) st.push({ch: 1, k: 'drive'});
    st.push({ch: 1, k: 'miles'}, {ch: 1, k: 'msg'});
    checkKeys().forEach(function (k) { st.push({ch: DOC.checks[k].ch, k: 'check', key: k}); });
    st.push({ch: 10, k: 'answer'});
    return st;
  }
  function chFrac(st, i) { var ch = st[i].ch, all = st.filter(function (x) { return x.ch === ch; }); return (all.indexOf(st[i]) + 1) / all.length; }
  // [[label|key]] -> label + an (i) button that opens DOC.info[key]
  function tx(s, open) { return esc(s).replace(/\[\[([^|\]]+)\|([^\]]+)\]\]([?:.,!]*)/g, function (_, l, k, pu) { return l + pu + '<button class="ii' + (open === k ? ' on' : '') + '" data-i="' + k + '" aria-label="What is ' + l + '?">' + ic('info', 19) + '</button>'; }); }
  var keyIn = function (s) { var m = String(s || '').match(/\[\[[^|\]]+\|([^\]]+)\]\]/); return m ? m[1] : null; };
  function costOf(c) { var v = c && c.cost; if (!v) return null; var e = (Y().eng2 || []).filter(function (x) { return x.name === engName(); })[0]; if (e && e.est && v[e.est]) return v[e.est]; if (v['*']) return v['*'];
    var ks = Object.keys(v); return [Math.min.apply(null, ks.map(function (k) { return v[k][0]; })), Math.max.apply(null, ks.map(function (k) { return v[k][1]; }))]; }
  function ipanel(key, c) {
    var I = (DOC.info || {})[key] || {};
    if (I.only) return '<div class="ip"><p>' + esc(I.what) + '</p></div>';
    var ok = I.ok || c.ok, bad = I.bad || c.bad, mo = costOf(c);
    return '<div class="ip">' + (I.what ? '<p><b>What it is:</b> ' + esc(I.what) + '</p>' : '') + (ok ? '<p><b>Fine:</b> ' + esc(ok) + '</p>' : '') + (bad ? '<p><b>Bad:</b> ' + esc(bad) + '</p>' : '') +
      (mo && c.note ? '<p><b>' + $r(mo) + ' EST:</b> ' + esc(c.note) + '</p>' : '') + '</div>';
  }
  function unkOf(key) { var b = key.split('@')[0]; return (Y().unk || []).filter(function (u) { return (u.checks || []).indexOf(b) >= 0; })[0] || null; }
  var H = [], MODE = '';
  var has = function (t) { return MODE.split('.').indexOf(t) >= 0; };

  function stepCheck(st, i) {
    var s = st[i], key = s.key, c = DOC.checks[key], keys = checkKeys(), k = keys.indexOf(key) + 1;
    if (c.kind === 'vin') return stepVin(st, i, k, keys.length);
    var a = S.ans[key] || '';
    var q = dlr() && c.qd ? c.qd : c.q, qa = q.match(/^Ask the (seller|dealer): (.*)$/), qt = qa ? qa[2].charAt(0).toUpperCase() + qa[2].slice(1) : q;
    var tags = (c.tag || '').split('').filter(Boolean).map(function (t) { return t === 's' ? '<span class="tg s">' + ic('shield', 13, 2.4) + ' Safety</span>' : '<span class="tg k">Known on the ' + esc(S.y) + '</span>'; }).join('');
    var I = (DOC.info || {})[c.i] || {}, fine = c.ok || I.ok, bad = c.bad || I.bad;
    var howBody = (c.how2 || c.how ? '<div style="margin-bottom:10px">' + esc(c.how2 || c.how) + '</div>' : '') + (fine || bad ? '<div class="pf">' + (fine ? '<span class="p">' + ic('check', 13, 3) + '</span><div><b>' + esc(c.a[0]) + ':</b> ' + esc(fine) + '</div>' : '') +
      (bad ? '<span class="f">' + ic('x', 12, 3) + '</span><div><b>' + esc(c.a[1]) + ':</b> ' + esc(bad) + '</div>' : '') + '</div>' : '');
    var wk = keyIn(c.why), whyBody = tx(c.why || '', has('wi') ? wk : '') + (c.src ? '<div class="src">' + esc(c.src) + '</div>' : '') + (wk && has('wi') ? '<div style="margin-top:10px">' + ipanel(wk, {}) + '</div>' : '');
    var card = '';
    if (a === 'na') { var u = unkOf(key), uc = u && u.v ? (u.v['*'] || u.v[Object.keys(u.v)[0]]) : null;
      card = '<div class="rc u"><div class="rh"><b>On your mechanic list</b></div>' + (uc ? '<p>If it’s bad: <b class="num" style="color:var(--ink)">' + $r(uc) + '</b> <span class="est">EST</span></p>' : '<p>Ask your mechanic to check it.</p>') + '</div>'; }
    if (a === 'bad') { var pk = keyIn(c.prob) || c.i, mo = costOf(c);
      card = '<div class="rc b"><div class="rh"><b>' + tx(c.prob || 'Problem', has('pi') ? pk : '') + '</b></div>' + (mo ? '<div class="rm num">' + $r(mo) + '<button class="est" data-t="pi">EST ' + ic('info', 12, 2.6) + '</button></div>' : '') +
        (c.act ? '<p>' + esc(c.act) + '</p>' : '') + '</div>' + (has('pi') ? ipanel(pk, c) : ''); }
    var inner = (qa ? '<p class="eb">' + ic('chat', 16, 2.2) + ' Ask the ' + qa[1] + '</p>' : '') + '<h1 class="q" style="margin-top:' + (qa ? 0 : 8) + 'px">' + tx(qt, has('i') ? c.i : '') + '</h1>' +
      (has('i') && c.i ? ipanel(c.i, c) : '') + (tags ? '<div class="tags">' + tags + '</div>' : '') + card +
      '<div class="dl"><button class="dr' + (has('how') ? ' op2' : '') + '" data-t="how">How to check<span class="cv">' + ic('chev', 20) + '</span></button>' + (has('how') ? '<div class="dp">' + howBody + '</div>' : '') +
      (c.why ? '<button class="dr' + (has('why') ? ' op2' : '') + '" data-t="why">Why it matters<span class="cv">' + ic('chev', 20) + '</span></button>' + (has('why') ? '<div class="dp">' + whyBody + '</div>' : '') : '') + '</div>';
    var lab = [c.a[0], c.a[1], c.a[2] || 'Not sure'], icn = [ic('check', 16, 3), ic('bang', 17, 3), ic('q', 16, 2.6)], cls = ['p', 'b', 'u'], ak = ['ok', 'bad', 'na'], j = ak.indexOf(a);
    var foot = a ? '<div class="pick"><span class="pk ' + cls[j] + '"><span class="ai">' + icn[j] + '</span>' + esc(lab[j]) + '</span><button class="chg" data-t="change">Change</button></div><div class="btn" data-go="next">Next</div>'
      : '<div class="ans3">' + lab.map(function (l, n) { return '<button class="a3 ' + cls[n] + '" data-a="' + ak[n] + '"><span class="ai">' + icn[n] + '</span>' + esc(l) + '</button>'; }).join('') + '</div>';
    return shell(inner, {title: CHAPTERS[s.ch - 1], sub: 'Check ' + k + ' of ' + keys.length, ch: s.ch, frac: chFrac(st, i), foot: foot, close: '/account/'});
  }

  // ---------------- the VIN step: NHTSA vPIC + NHTSA recalls, straight from the browser (free, no key), named by recallName() ----------------
  var VIN = null;
  function vinResult(dec, recalls) {
    var want = (S.y + ' ' + DOC.brand + ' ' + DOC.short).toLowerCase(), got = dec.y + ' ' + dec.mk + ' ' + dec.md;
    var match = +dec.y === +S.y && String(dec.mk).toLowerCase() === String(DOC.brand).toLowerCase();
    if (!match) return '<div class="vm bad"><span class="vi">' + ic('bang', 18, 3) + '</span><span>This VIN is a ' + esc(got) + '<small>You’re checking a ' + esc(S.y + ' ' + DOC.short) + '. Ask the seller why.</small></span></div><p class="vdc">' + esc([dec.eng, dec.drive, dec.body].filter(Boolean).join(' · ')) + '</p>';
    var all = has('all'), rs = all ? recalls : recalls.slice(0, 3);
    return '<div class="vm ok"><span class="vi">' + ic('check', 17, 3) + '</span><span>Matches: ' + esc(got) + '</span></div><p class="vdc">' + esc([dec.eng, dec.drive, dec.body].filter(Boolean).join(' · ')) + '</p>' +
      '<div class="rlh"><b>Recalls on the ' + esc(S.y + ' ' + DOC.short) + ': ' + recalls.length + '</b>' + (recalls.length > 3 ? '<span data-t="all">' + (all ? 'Show less' : 'See all') + '</span>' : '') + '</div>' +
      '<div class="rl">' + rs.map(function (r) { var n = window.recallName ? window.recallName(r) : {name: r.Component, what: ''}; return '<div><span><b>' + esc(n.name) + '</b><small>' + esc(n.what) + '</small></span><span class="id">' + esc(r.NHTSACampaignNumber) + '</span></div>'; }).join('') + '</div>' +
      '<a class="btn w" href="https://www.nhtsa.gov/recalls" target="_blank" rel="noopener">Check which are still open ' + ic('ext', 17) + '</a>';
  }
  function stepVin(st, i, k, n) {
    var out = VIN && VIN.vin === S.vin ? VIN.html : '';
    var inner = '<h1 class="q" style="margin-top:8px">Check the VIN</h1><form class="vf" id="vinf" autocomplete="off"><input class="in' + (S.vin ? ' f' : '') + '" name="vin" maxlength="20" spellcheck="false" placeholder="Paste the VIN" value="' + esc(S.vin) + '" aria-label="VIN"><button type="submit">Check</button></form><div id="vinout">' + out + '</div>';
    return shell(inner, {title: CHAPTERS[0], sub: 'Check ' + k + ' of ' + n, ch: 1, frac: chFrac(st, i), foot: '<div class="btn" data-go="next">' + (S.ans[st[i].key] ? 'Next' : 'Skip for now') + '</div>', close: '/account/'});
  }
  function liveVin(key, vin) {
    var out = document.getElementById('vinout'); vin = String(vin).toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (vin.length !== 17) { out.innerHTML = '<p class="vdc" style="color:var(--r)">A VIN is 17 letters and numbers.</p>'; return; }
    S.vin = vin; saveS(); out.innerHTML = '<p class="vdc">Checking…</p>';
    fetch('https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/' + vin + '?format=json').then(function (r) { return r.json(); }).then(function (j) {
      var r = j.Results[0]; if (!r || !r.Make) throw 0;
      var dec = {y: +r.ModelYear, mk: r.Make.charAt(0) + r.Make.slice(1).toLowerCase(), md: r.Model, body: (r.BodyClass || '').split('/')[0], drive: (r.DriveType || '').split('/')[0].replace(/^4x2$/, '2WD'),
        eng: [r.DisplacementL && (+r.DisplacementL).toFixed(1) + 'L', r.EngineCylinders && (/^V/.test(r.EngineConfiguration || '') ? 'V' + r.EngineCylinders : r.EngineCylinders + '-cyl'), r.FuelTypePrimary && r.FuelTypePrimary.replace(/^Gasoline$/, 'gas').toLowerCase()].filter(Boolean).join(' ')};
      return fetch('https://api.nhtsa.gov/recalls/recallsByVehicle?make=' + encodeURIComponent(dec.mk) + '&model=' + encodeURIComponent(dec.md) + '&modelYear=' + dec.y).then(function (r) { return r.json(); })
        .catch(function () { return {results: []}; }).then(function (rj) {
          var html = vinResult(dec, rj.results || []); VIN = {vin: vin, html: html};
          S.ans[key] = +dec.y === +S.y && String(dec.mk).toLowerCase() === String(DOC.brand).toLowerCase() ? 'ok' : 'bad'; saveS(); render();
        });
    }).catch(function () { out.innerHTML = '<p class="vdc" style="color:var(--r)">Couldn’t decode that VIN. Check it for typos, or try again in a minute.</p>'; });
  }

  // ---------------- step 1 screens ----------------
  var chooser = function (name, opts, on, cols) { return '<div class="ch" style="--c:' + (cols || 2) + '">' + opts.map(function (o) { return '<button class="' + (o[0] === on ? 'on' : '') + '" data-set="' + name + '" data-v="' + esc(o[0]) + '">' + esc(o[1]) + '</button>'; }).join('') + '</div>'; };
  function stepOther(st, i) {
    var s = st[i], y = Y(), inner = '', foot = '<div class="btn' + (s.k === 'seller' && !S.seller || s.k === 'year' && !S.y ? ' off' : '') + '" data-go="next">Next</div>';
    var head = function (t) { return '<h1 class="q" style="margin:8px 0 18px">' + t + '</h1>'; };
    if (s.k === 'seller') inner = head('Who is selling it?') + [['private', 'user', 'Private seller'], ['dealer', 'store', 'Dealer'], ['nohaggle', 'tag', 'No-haggle store'], ['bhph', 'wallet', 'Buy-here-pay-here']].map(function (o) {
      return '<button class="op' + ((S.stype || S.seller) === o[0] ? ' on' : '') + '" data-seller="' + o[0] + '"><span class="oi">' + ic(o[1]) + '</span><span>' + o[2] + '</span></button>'; }).join('');
    if (s.k === 'year') inner = head('Which year?') + chooser('y', Object.keys(DOC.ys).sort().map(function (k) { return [k, k]; }), S.y, 3);
    if (s.k === 'trim') inner = head('Which trim?') + chooser('trim', y.trims.map(function (t) { return [t.t, t.t]; }).concat([['', 'Not sure']]), S.trim || (S.trim === '' ? '' : null));
    if (s.k === 'drive') {
      var dv = drives();
      if (!trimO() && y.eng2.length > 1) inner += '<p class="lab" style="margin-top:0">Engine</p>' + chooser('eng', y.eng2.map(function (e, j) { return [String(j), e.name.replace(/ (2TR-FE|2ZR-FE|2ZR-FAE|K20C|R18|D16|D17|K20|K24|B16)\b/, '')]; }), S.eng == null ? null : String(S.eng));
      if (dv.length > 1) inner += '<p class="lab"' + (inner ? '' : ' style="margin-top:0"') + '>Drive</p>' + chooser('drive', dv.map(function (d) { return [d, d === 'rwd' && (DOC.type === 'truck' || dv.indexOf('4wd') >= 0) ? '2WD' : d.toUpperCase()]; }), S.drive);
      if (!trLock() && y.manual) inner += '<p class="lab">Gearbox</p>' + chooser('tr', [['auto', 'Automatic'], ['manual', 'Manual']], S.tr);
      if ((y.cabs || []).length > 1) inner += '<p class="lab">Cab</p>' + chooser('cab', y.cabs.map(function (c) { return [c, c.replace(/ Cab$/, '')]; }), S.cab, 3);
      inner = head('The car') + inner;
    }
    if (s.k === 'miles') inner = head('Miles and asking price') + '<label class="inl" for="f-mi">Miles on it</label><input class="in' + (S.miles ? ' f' : '') + '" id="f-mi" inputmode="numeric" data-num="miles" value="' + esc(S.miles ? (+S.miles).toLocaleString('en-US') : '') + '" placeholder="e.g. 120,000">' +
      '<label class="inl" for="f-ask">Asking price</label><div class="inw"><span class="iic">' + ic('tag', 16, 2.2) + '</span><input class="in' + (S.ask ? ' f' : '') + '" id="f-ask" inputmode="numeric" data-num="ask" value="' + esc(S.ask ? '$' + (+S.ask).toLocaleString('en-US') : '') + '" placeholder="$ optional"></div>' +
      '<p class="lab">Service records?</p>' + chooser('rec', [['full', 'Full'], ['some', 'Some'], ['none', 'None']], S.rec, 3);
    if (s.k === 'msg') { var who = dlr() ? 'dealer' : 'seller', Q = (DOC.questions || {})[sel()] || [];
      inner = head('Send the ' + who + ' ' + Q.length + ' questions') + '<div class="cd gy" style="padding:6px 16px"><ol class="ml">' + Q.map(function (m) { return '<li>' + esc(m) + '</li>'; }).join('') + '</ol></div><button class="btn w" style="margin-top:6px" data-copy="msg">' + ic('copy', 18) + ' Copy questions</button>';
      foot = '<div class="btn" data-go="next">I sent them</div><button class="lnk" data-go="next" style="width:100%;margin-top:12px">No thanks</button>'; }
    return shell(inner, {title: CHAPTERS[0], ch: 1, frac: chFrac(st, i), foot: foot, close: '/account/'});
  }

  // ---------------- step 10: your answer (computed by the Worker) ----------------
  function answerInput() { return {y: S.y, seller: dlr() ? 'dealer' : 'private', stype: S.stype, trim: S.trim || null, eng: S.eng, tr: trLock() || S.tr, drive: S.drive, cab: S.cab, miles: +S.miles || 0, ask: +S.ask || 0, rec: S.rec, tax: S.tax, ans: S.ans, unk: S.unk, quote: S.quote}; }
  function fetchAnswer() {
    var inp = answerInput(), k = JSON.stringify(inp); if (k === RES_KEY && RES) return Promise.resolve(RES);
    return api('POST', '/answer', {gen: GEN, s: inp}).then(function (j) { if (j._s === 200) { RES = j; RES_KEY = k; } else RES = {err: j.error || 'offline'}; return RES; });
  }
  function answer(open) {
    var A = RES; if (!A) return shell('<p class="s">Working out your answer…</p>', {title: CHAPTERS[9], ch: 10, frac: 1, close: '/account/'});
    if (A.err) return shell('<p class="s">' + (A.err === 'busy' ? 'Too many tries in a row. Wait a minute, then reload.' : 'Couldn’t reach the Lemon Index just now. Check your connection, then reload.') + '</p>', {title: CHAPTERS[9], ch: 10, frac: 1, close: '/account/'});
    var D = A.seller === 'dealer';
    var xc = function (key, name, small, n, body) { return '<div class="xc' + (open === key ? ' open' : '') + '"><button class="xh" data-x="' + key + '"><span class="hk-t"><b>' + esc(name) + '</b><small>' + esc(small) + '</small></span><span class="n">' + n + '</span><span class="cv">' + ic('chev', 20) + '</span></button>' + (open === key ? '<div class="xb">' + body + '</div>' : '') + '</div>'; };
    var uo = A.unk.filter(function (u) { return u.st === 'open'; }), uk = A.unk.filter(function (u) { return u.st === 'ok'; });
    var dec;
    if (A.c === 'walk' || A.c === 'fix' || A.max == null) dec = '<div class="dec' + (A.c === 'walk' ? ' bad' : '') + '"><span class="dh">' + esc(A.w) + '</span>' + (A.lead ? '<small class="bt">' + esc(A.lead) + '</small>' : '') + (A.s ? '<p class="note" style="margin:8px 0 0">' + esc(A.s) + '</p>' : '') + '</div>';
    else dec = '<div class="dec' + (uo.length ? '' : ' clr') + '"><span class="dh">Buy it at <i>' + $f(A.max) + '</i> <span style="white-space:nowrap">or less</span></span>' + (D ? '<small class="bt">Car price, before tax and fees</small>' : '') +
      '<div class="ofr"><span>Open with</span><b>' + $f(A.open) + '</b></div>' + (D && A.otd ? '<div class="ofr otd"><span>Out the door</span><b>' + $r(A.otd) + '</b></div><small class="otn">With ' + A.fees.taxPct + '% tax, title, registration and a ' + $r(A.fees.docFee) + ' doc fee</small>' : '') +
      (uo.length ? '<span class="cond">' + ic('wrench', 14, 2.4) + ' Once your mechanic clears ' + esc(uo.map(function (u) { return u.name; }).join(' and ')) + '</span>' : uk.length ? '<span class="cond">' + ic('check', 14, 3) + ' ' + esc(uk.map(function (u) { return u.name.replace(/^the /, ''); }).join(' and ')) + ' cleared by your mechanic</span>' : '') + '</div>';
    var forL = '<p class="note" style="margin:10px 4px 12px">Prices for a ' + esc(A.for) + (A.trimKnown ? '' : ' (trim not picked: base price)') + '.</p>';
    var all = A.probs.map(function (p) { return {key: p.key, name: p.name, cost: p.cost, safe: p.safe, quote: p.quote}; }).concat(A.first.map(function (p) { return {key: p.key, name: p.name, cost: p.cost, safe: p.safe, first: true}; }),
      A.confirm.map(function (p) { return {key: p.key, name: p.name, cost: p.cost, conf: true}; }), A.risk.map(function (p) { return {key: p.key, name: p.name, cost: p.cost, risk: true}; }), A.walk.map(function (p) { return {key: p.key, name: p.name, walk: true}; }),
      A.mech.concat(A.paper, A.free).map(function (p) { return {key: p.key, name: p.name}; }));
    var probs = all.map(function (p) {
      return '<div class="xr"><div class="pb"><div><b>' + esc(p.name) + '</b>' + (p.safe ? '<div style="margin-top:6px"><span class="tg s">' + ic('shield', 13, 2.4) + ' Safety</span></div>' : p.walk ? '<div style="margin-top:6px"><span class="tg s">Deal-breaker</span></div>' : '') + '</div>' +
        '<div class="c num">' + (p.cost ? (p.quote ? $f(p.cost[0]) + '<small class="mine">Your mechanic’s quote</small>' : $r(p.cost) + '<span class="est">EST</span>') : '') + '</div></div>' +
        (p.cost && !p.walk ? '<label class="qb"><span>Mechanic’s quote</span><input class="qin" inputmode="numeric" data-quote="' + esc(p.key) + '" placeholder="$ Add" value="' + esc(S.quote[p.key] || '') + '"></label>' : '') + '</div>';
    }).join('') + (A.two ? '<p class="note" style="margin:10px 4px 0">' + (D ? 'Fixed first, on the We Owe form: pay up to ' + $f(A.fixed) + '. Open with ' + $f(A.fixedOpen) + '.' : 'Fixed first: pay up to ' + $f(A.fixed) + '.') + '</p>' : '');
    var mech = A.unk.map(function (u) {
      return '<div class="xr"><div class="pb"><div><b>' + esc(u.name.charAt(0).toUpperCase() + u.name.slice(1)) + '</b></div><div class="c num">' +
        (u.st === 'ok' ? '<span class="ok" style="margin:0">' + ic('check', 18, 3) + ' Cleared</span>' : u.cost ? $r(u.cost) + '<span class="est">EST</span><small>' + (u.out === 'walk' ? 'if it’s bad: walk away' : 'if it’s bad') + '</small>' : '') + '</div></div>' + (u.ask ? '<p class="note" style="margin:8px 0 0">Ask for ' + esc(u.ask) + '</p>' : '') +
        '<div class="tg2"><button class="' + (u.st === 'ok' ? 'on' : '') + '" data-unk="' + esc(u.id) + '" data-v="ok">Cleared</button><button class="' + (u.st === 'bad' ? 'on' : '') + '" data-unk="' + esc(u.id) + '" data-v="bad">Found a problem</button></div></div>';
    }).join('');
    var lab = function (t) { return '<small class="note" style="display:block;margin-bottom:6px;font-weight:600">' + t + '</small>'; };
    var addons = D && A.c !== 'walk' ? lab('1. Add-ons first: they bend more than the price') + '“Please take the add-ons off. I’ll pay the price, tax, title, registration and the doc fee.”<p class="note" style="margin:8px 0 0;font-weight:500">Add-ons: etching, nitrogen, paint or fabric protection, prep fees, market adjustment.</p><div class="q2">' + lab('2. Then the price') : '';
    var say = '<div class="xr" style="font-size:16.5px;line-height:1.45;font-weight:550">' + addons + A.say.map(function (l, j) { return j ? '<p class="note" style="margin:10px 0 0;font-weight:500">' + esc(l) + '</p>' : esc(l); }).join('') + (addons ? '</div>' : '') + '</div><button class="btn w" style="margin-top:8px;height:50px" data-copy="say">' + ic('copy', 18) + ' Copy</button>';
    var paper = '<div class="xl">' + A.papers.map(function (p, j) { var on = !!S.papers[j]; return '<button class="xlb" data-paper="' + j + '"><span class="ck' + (on ? ' y' : '') + '">' + (on ? ic('check', 13, 3) : '') + '</span>' + esc(p) + '</button>'; }).join('') + '</div>';
    var nP = all.length, small = nP ? all.slice(0, 2).map(function (p) { return p.name + (p.cost ? ' · ' + $r(p.cost) : ''); }).join(', ') : 'Nothing marked';
    var inner = dec + forL + (nP ? xc('p', 'Problems found', small, nP, probs) : '') + (A.unk.length ? xc('m', 'For your mechanic', uo.length ? uo.map(function (u) { return u.name; }).join(', ') + ', on a lift' : A.unk.some(function (u) { return u.st === 'bad'; }) ? 'Found a problem: ' + A.unk.filter(function (u) { return u.st === 'bad'; }).map(function (u) { return u.name; }).join(', ') : 'Cleared', A.unk.length, mech) : '') +
      (A.say.length ? xc('s', 'Ask the ' + (D ? 'dealer' : 'seller'), D ? 'What to say, add-ons first' : 'What to say', D ? 2 : 1, say) : '') + xc('d', 'Paperwork', 'Before you pay', A.papers.length, paper) +
      (A.math ? '<details class="xc"><summary class="xh"><span class="hk-t"><b>How we got this</b><small>Our estimates, step by step</small></span><span class="cv">' + ic('chev', 20) + '</span></summary><div class="xb"><p class="note">' + esc(A.math) + '</p></div></details>' : '') +
      '<a class="cl" style="width:100%" href="' + esc(TEASE.yearPage.replace('{y}', S.y)) + '"><span>Cost to own and the full ' + esc(S.y) + ' report</span><span style="color:var(--gray2);display:grid">' + ic('chev', 18) + '</span></a>';
    var foot = '<div style="display:flex;gap:10px"><button class="btn w" style="flex:1" data-share="1">' + ic('share', 18) + ' Share</button><a class="btn" style="flex:1.4" href="/account/">Done</a></div>';
    return shell(inner, {title: CHAPTERS[9], sub: S.y + ' ' + DOC.short + ' · ' + (D ? 'dealer' : 'private seller'), ch: 10, frac: 1, foot: foot, w: true, close: '/account/'});
  }

  // ---------------- before the checklist: sign up, free, paywall, checkout, unlocked ----------------
  function signup(err) {
    var T = TEASE;
    return sheet(hk({name: T.title, small: 'Checklist · Free', img: T.img, cls: 'mini'}) + '<h2 class="t" style="margin-top:12px">Your first checklist is free</h2><p class="s" style="color:var(--ink2)">Sign up with your email to get it. No password, no spam.</p>' +
      '<form id="emf" novalidate><label class="vh" for="em">Email</label><input class="in" id="em" type="email" autocomplete="email" inputmode="email" placeholder="you@email.com" required maxlength="254">' +
      (CFG.turnstile ? '<div class="cf-turnstile" data-sitekey="' + esc(CFG.turnstile) + '"></div>' : '') + '<button class="btn y" style="margin-top:12px;width:100%" type="submit">Email me my checklist</button></form>' +
      (err ? '<p class="note" style="color:var(--r);margin-top:10px">' + esc(err) + '</p>' : '') + '<p class="note" style="margin-top:12px">Already have an account? Use the same email: we send a sign-in link.</p>');
  }
  function emailSent(addr, dev) {
    return sheet('<div class="ctr"><div class="bigic">' + ic('mail', 36) + '</div><h2 class="t">Check your email</h2><p class="s">We sent a link to <b style="color:var(--ink)">' + esc(addr) + '</b>. It works once, for 15 minutes.</p>' +
      (dev && /^http:\/\/(127\.0\.0\.1|localhost):\d+\/account\/signin\/#t=lsl_[A-Za-z0-9_-]{43}$/.test(dev) ?'<a class="btn" href="' + esc(dev) + '">Open the sign-in link (local test)</a>' : '') + '<p class="note" style="margin-top:14px">Didn’t get it? Check spam.</p><button class="lnk" data-go-h="">Send it again</button></div>');
  }
  function paywall(open) {
    var T = TEASE, all = open === 'all';
    var ONE = ['Built from the ' + T.title + '’s own known problems'].concat(T.known && T.known.length ? ['Checks for ' + T.known.slice(0, 2).join(' and ')] : [], ['VIN and recall check', T.drive + ' test drive checks', '5 questions to send the ' + 'seller', 'Your offer: buy-at and open-with prices']);
    var ALL = ['Every car and truck checklist we have: ' + T.nModels + ' models', 'Every checklist we add later, free', 'Use them on as many cars as you shop', 'Offer price and seller questions for each'];
    var card = function (key, o, items, note) { var op = open === key || open === key + '-i', on = key === 'all' ? all : !all;
      return '<div class="pwc' + (on ? ' on' : '') + '"><button class="pwb" data-plan="' + key + '">' + hk(Object.assign({}, o, {cls: 'pw' + (on ? ' on' : '')})) + '</button><button class="inc" data-inc="' + key + '">What’s included <span class="cv' + (op ? ' up' : '') + '">' + ic('chev', 16, 2.4) + '</span></button>' +
        (op ? '<ul class="incl">' + items.map(function (t) { return '<li>' + ic('check', 15, 2.8) + '<span>' + esc(t) + '</span></li>'; }).join('') + '<li class="more"><span>+ more' + (key === 'one' ? ' (' + T.all + ' checks in all)' : '') + '</span></li></ul>' + (note ? '<p class="incn">' + note + '</p>' : '') : '') + '</div>'; };
    return sheet('<h2 class="t" style="margin-bottom:16px">Unlock the ' + esc(T.short) + ' checklist</h2>' + card('one', {name: T.title, small: 'This ' + (T.type === 'truck' ? 'truck' : 'car'), price: '$7.99', img: T.img}, ONE) +
      card('all', {name: 'All cars & trucks', small: 'Every checklist', price: '$19.99', img: ALLCARS.img, img2: ALLCARS.img2, badge: 'Best value'}, ALL, 'Not included: motorcycles, planes and dirt bikes.'),
      {foot: '<button class="btn" data-buy="' + (all ? 'all' : 'one') + '" style="width:100%">Continue · ' + (all ? '$19.99' : '$7.99') + '</button><div class="lk" style="margin-top:10px">' + ic('lock', 15) + ' One-time payment. Apple Pay works.</div>' +
        '<p class="note" style="text-align:center;margin:8px 0 0"><!-- needs Elijah’s OK -->Not happy? Email us within 14 days for a full refund.</p>'});
  }
  function checkoutScreen(price, err) {
    return sheet('<div class="co"><img src="' + esc(TEASE.img) + '" alt=""><h2>' + esc(price === '$19.99' ? 'All cars & trucks' : TEASE.short + ' checklist') + '</h2><div class="pp num">' + price + '</div>' +
      (err ? '<p class="note" style="color:var(--r)">' + esc(err) + '</p><button class="btn" data-go-h="paywall">Back</button>' : '<div class="btn"><span class="spin"></span> Opening secure checkout</div>') + '<div class="lk">' + ic('lock', 15) + ' Stripe handles your card.</div></div>');
  }
  function intro(state) {
    var T = TEASE, Sx = S || {}, done = Object.keys(Sx.ans || {}).length;
    var inner = '<div class="un">' + (state === 'unlocked' ? '<div class="glow"></div>' : '') + '<div class="ahr" style="position:relative;padding:6px 12px"><span class="ib"></span><span class="ct"></span><a class="ib" href="/account/" aria-label="Close">' + ic('x', 22) + '</a></div>' +
      '<div class="bd2" style="text-align:left;padding:' + (desk() ? 18 : 0) + 'px 20px 0"><h1 style="margin:0 0 18px">' + (state === 'unlocked' ? 'Unlocked' : state === 'wait' ? 'Payment received' : done ? 'Welcome back' : 'Your checklist is ready') + '</h1>' +
      hk({name: T.title, small: state === 'wait' ? 'Unlocking…' : 'Checklist · ' + (ME && ME.free === GEN ? 'Free' : 'Paid'), img: T.img, cls: 'big', ok: state === 'unlocked'}) +
      '<div class="stats" style="justify-content:stretch;margin-top:4px"><div style="max-width:none"><b>' + T.checks + '</b><small>quick checks</small></div><div style="max-width:none"><b>' + T.mins + ' min</b><small>at the ' + (T.type === 'truck' ? 'truck' : 'car') + '</small></div></div>' +
      (state === 'wait' ? '<p class="note" style="margin-top:14px;text-align:center">Stripe is confirming your payment. This page unlocks by itself.</p>' : '') + '</div>' +
      '<div class="ft2">' + (state === 'wait' ? '' : '<a class="btn y" style="height:60px;font-size:18px" href="#run/' + (done ? (Sx.i || 0) : 0) + '">' + (done ? 'Continue checklist' : 'Start checklist') + '</a>') + '</div></div>';
    return desk() ? siteNav() + '<div class="app"><div class="wrap" style="width:520px">' + inner + '</div></div>' : inner;
  }

  // ---------------- render + wiring ----------------
  function render() {
    document.body.classList.toggle('desk', desk());
    H = (location.hash || '#').slice(1).split('/'); MODE = H[0] === 'run' ? (H[2] || '') : '';
    var html;
    if (H[0] === 'email') html = emailSent(decodeURIComponent(H[1] || ''), sessionStorage.getItem('lcw-dev-link'));
    else if (!token() || !ME) html = H[0] === 'paywall' ? signup() : signup(H[0] === 'err' ? decodeURIComponent(H[1] || '') : '');
    else if (!owns(GEN)) html = H[0] === 'checkout' ? checkoutScreen(H[1] === 'all' ? '$19.99' : '$7.99', H[2] ? decodeURIComponent(H[2]) : '') : H[0] === 'wait' ? intro('wait') : paywall(H[1] || (H[0] === 'paywall' ? '' : ''));
    else if (!DOC || !S) html = shell('<p class="s">Loading your checklist…</p>', {title: TEASE.title, close: '/account/'});
    else if (H[0] === 'run') {
      var st = seq(), i = Math.min(+H[1] || 0, st.length - 1);
      if (S.i !== i) { S.i = i; saveS(); }
      html = st[i].k === 'check' ? stepCheck(st, i) : st[i].k === 'answer' ? answer(H[2] === 'x' ? H[3] || '' : '') : stepOther(st, i);
      if (st[i].k === 'answer') fetchAnswer().then(function () { if (location.hash.indexOf('#run/') === 0) paint(answer(H[2] === 'x' ? H[3] || '' : '')); });
    } else html = intro(H[0] === 'unlocked' ? 'unlocked' : '');
    paint(html);
  }
  function paint(html) { app.innerHTML = html; wire(); if (window.turnstile && document.querySelector('.cf-turnstile')) try { window.turnstile.render('.cf-turnstile'); } catch (e) {} }
  function setNum(el) { var v = String(el.value).replace(/[^\d]/g, '').slice(0, 7); S[el.dataset.num] = v; saveS(); RES = null; }
  function wire() {
    var st = H[0] === 'run' && S ? seq() : null, i = st ? Math.min(+H[1] || 0, st.length - 1) : 0;
    var toggle = function (t) { var m = MODE ? MODE.split('.') : [], j = m.indexOf(t); if (j >= 0) m.splice(j, 1); else m.push(t); go('#run/' + i + (m.length ? '/' + m.join('.') : '')); };
    var next = function () { go('#run/' + Math.min(i + 1, st.length - 1), true); };
    q('[data-back]').forEach(function (b) { b.onclick = function () {
      var f = history.state && history.state.from, stepOf = function (h) { var m = /^#run\/(\d+)/.exec(h || ''); return m ? +m[1] : -1; };
      if (st && i > 0) { if (f && stepOf(f) === i - 1) history.back(); else { if (history.state) history.replaceState({cl: 1, from: null}, '', location.href); go('#run/' + (i - 1)); } }
      else if (st && f && stepOf(f) < 0) history.back();          // pushed from the intro: go back to it
      else if (st) go('#');                                       // first step, reached some other way: show the intro
      else history.back(); }; });
    q('[data-go=next]').forEach(function (b) { b.onclick = function () { if (!b.classList.contains('off')) next(); }; });
    q('[data-go-h]').forEach(function (b) { b.onclick = function () { go('#' + b.dataset.goH); }; });
    q('[data-a]').forEach(function (b) { b.onclick = function () { S.ans[st[i].key] = b.dataset.a; saveS(); RES = null; if (b.dataset.a === 'ok') next(); else go('#run/' + i); }; });
    q('[data-t]').forEach(function (b) { b.onclick = function (e) { e.preventDefault(); e.stopPropagation(); if (b.dataset.t === 'change') { delete S.ans[st[i].key]; saveS(); RES = null; return go('#run/' + i); } toggle(b.dataset.t); }; });
    q('.ii').forEach(function (b) { b.onclick = function (e) { e.preventDefault(); e.stopPropagation(); toggle(b.closest('.dp') ? 'wi' : b.closest('.rc') ? 'pi' : 'i'); }; });
    q('[data-seller]').forEach(function (b) { b.onclick = function () { var v = b.dataset.seller; S.stype = v; S.seller = v === 'private' ? 'private' : 'dealer'; saveS(); RES = null; render(); }; });
    q('[data-set]').forEach(function (b) { b.onclick = function () { var k = b.dataset.set, v = b.dataset.v; S[k] = k === 'eng' ? +v : v === '' && k === 'trim' ? '' : v; if (k === 'y') { S.trim = null; S.eng = null; } saveS(); RES = null; render(); }; });
    q('[data-num]').forEach(function (el) { el.oninput = function () { setNum(el); }; el.onblur = function () { var k = el.dataset.num, v = S[k]; el.value = v ? (k === 'ask' ? '$' : '') + (+v).toLocaleString('en-US') : ''; el.classList.toggle('f', !!v); }; });   // 11-26: format in place; a re-render here took focus from the next box
    q('[data-x]').forEach(function (b) { b.onclick = function () { var cur = H[2] === 'x' ? H[3] : ''; go('#run/' + i + (cur === b.dataset.x ? '' : '/x/' + b.dataset.x)); }; });
    q('[data-unk]').forEach(function (b) { b.onclick = function () { var id = b.dataset.unk; if (S.unk[id] === b.dataset.v) delete S.unk[id]; else S.unk[id] = b.dataset.v; saveS(); RES = null; render(); }; });
    q('[data-quote]').forEach(function (el) { el.onchange = function () { var v = String(el.value).replace(/[^\d]/g, '').slice(0, 6); if (+v > 0) S.quote[el.dataset.quote] = v; else delete S.quote[el.dataset.quote]; saveS(); RES = null; render(); }; });
    q('[data-paper]').forEach(function (b) { b.onclick = function () { var j = b.dataset.paper; S.papers[j] = !S.papers[j]; saveS(); render(); }; });
    q('[data-copy]').forEach(function (b) { b.onclick = function () { var t = b.dataset.copy === 'msg' ? ((DOC.questions || {})[sel()] || []).map(function (m, j) { return (j + 1) + '. ' + m; }).join('\n') : (RES && RES.say || []).join('\n');
      (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(function () { b.innerHTML = ic('check', 18, 3) + ' Copied'; }).catch(function () {}); }; });
    q('[data-share]').forEach(function (b) { b.onclick = function () { var A = RES || {}, t = A.max != null ? DOC.short + ' ' + S.y + ': buy it at ' + $f(A.max) + ' or less, open with ' + $f(A.open) + '.' : A.w || '';
      if (navigator.share) navigator.share({title: 'My ' + DOC.short + ' answer', text: t}).catch(function () {}); else location.href = 'mailto:?subject=' + encodeURIComponent('My ' + DOC.short + ' answer') + '&body=' + encodeURIComponent(t); }; });
    q('[data-inc]').forEach(function (b) { b.onclick = function () { go('#paywall/' + ((H[1] || '') === b.dataset.inc ? (b.dataset.inc === 'all' ? 'all-c' : '') : b.dataset.inc)); }; });
    q('[data-plan]').forEach(function (b) { b.onclick = function () { go('#paywall/' + (b.dataset.plan === 'all' ? 'all-c' : 'one-c')); }; });
    q('[data-buy]').forEach(function (b) { b.onclick = function () { buy(b.dataset.buy); }; });
    var f = document.getElementById('vinf'); if (f) f.onsubmit = function (e) { e.preventDefault(); liveVin(st[i].key, f.vin.value); };
    var ef = document.getElementById('emf'); if (ef) ef.onsubmit = function (e) { e.preventDefault(); startSignin(ef); };
  }
  var q = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };
  function startSignin(f) {
    var em = String(f.em.value || '').trim(), tsi = f.querySelector('[name="cf-turnstile-response"]');
    if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(em)) return paint(signup('Type your email, like you@email.com.'));
    if (BUSY) return; BUSY = true;
    sessionStorage.setItem('lcw-next', GEN); device();
    api('POST', '/auth/start', {email: em, next: GEN, ts: tsi ? tsi.value : undefined}).then(function (j) {
      BUSY = false;
      if (j._s === 200) { if (j.dev_link) sessionStorage.setItem('lcw-dev-link', j.dev_link); else sessionStorage.removeItem('lcw-dev-link'); go('#email/' + encodeURIComponent(em)); return; }
      paint(signup({email: 'That email doesn’t work here. Use your everyday email.', disposable: 'Please use your everyday email, not a throwaway one.', busy: 'Too many sign-in emails. Try again in an hour.', 'email-off': 'Sign-in emails are paused for a moment. Try again soon.', turnstile: 'Please tick the box to show you’re not a robot.'}[j.error] || 'Couldn’t send the email. Try again in a minute.'));
    });
  }
  function buy(item) {
    go('#checkout/' + item);
    api('POST', '/checkout', {item: item, gen: GEN}).then(function (j) {
      if (j._s === 200 && j.url && /^https:\/\/checkout\.stripe\.com\//.test(j.url)) { location.href = j.url; return; }
      if (j.error === 'owned') return loadMe().then(start);
      go('#checkout/' + item + '/' + encodeURIComponent(j.error === 'busy' ? 'Too many tries. Wait a few minutes.' : 'Checkout isn’t open yet. Try again soon.'));
    });
  }
  function waitPaid(n) {     // the webhook grants the purchase; the redirect from Stripe never does. Ask /me until it shows up.
    loadMe().then(function () { if (owns(GEN)) { history.replaceState(null, '', location.pathname + '#unlocked'); start(); } else if (n < 20) { go('#wait'); setTimeout(function () { waitPaid(n + 1); }, 2500); } else render(); });
  }
  function start() {
    if (!owns(GEN)) {
      if (ME && ME.freeLeft && !ME.free) return api('POST', '/free', {gen: GEN, dev: device()}).then(function (j) { if (j._s === 200) return loadMe().then(start); render(); });
      return render();
    }
    if (DOC) return render();
    render();
    api('GET', '/content?gen=' + GEN).then(function (j) { if (j._s !== 200) { DOC = null; return render(); } DOC = j; return loadS().then(function () {   // 11-26 (Elijah): no 'Welcome back' stop; reopen straight at the step you left
      if ((location.hash === '' || location.hash === '#') && S && (S.i || Object.keys(S.ans || {}).length)) history.replaceState(null, '', location.pathname + location.search + '#run/' + (S.i || 0));
      render(); }); });
  }
  function bootChecklist() {
    addEventListener('hashchange', render); addEventListener('pagehide', function () { pushS(true); }); document.addEventListener('visibilitychange', function () { if (document.hidden) pushS(true); }); var rt = null, wasDesk = desk(); addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () {   // 11-26: the phone keyboard opening is a resize; re-drawing then closed it
      var d = desk(); if (d === wasDesk) return; var a = document.activeElement; if (a && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)) return; wasDesk = d; render(); }, 150); });
    addEventListener('popstate', render);
    var paid = /[?&]paid=1/.test(location.search);
    loadMe().then(function () { if (paid) { history.replaceState(null, '', location.pathname + location.hash); return waitPaid(0); } start(); });
  }

  // ======================================================================== /account/ and /account/signin/
  // 11-26 (Elijah): signed out, the person icon lands here: a sign-up page that says what you get. Signed in: your checklists + settings.
  var PERKS = [['check', 'Your first checklist free', 'Pick any car or truck. No card needed.'], ['user', 'Your answers on any device', 'Start at the car on your phone, finish at home.'],
    ['tag', 'An offer price for the car', 'What to pay and what to open with, from your answers.']];
  function accWrap(inner) { return siteNav() + (desk() ? '<div class="app"><div class="wrap acw">' + inner + '</div></div>' : inner); }
  function devLink() { var d = sessionStorage.getItem('lcw-dev-link'); return d && /^http:\/\/(127\.0\.0\.1|localhost):\d+\/account\/signin\/#t=lsl_[A-Za-z0-9_-]{43}$/.test(d) ? d : ''; }
  function joinPage(err, sent) {
    if (sent) return accWrap('<div class="acc ctr"><div class="bigic">' + ic('mail', 36) + '</div><h1>Check your email</h1><p class="s">We sent a link to <b style="color:var(--ink)">' + esc(sent) + '</b>. It works once, for 15 minutes.</p>' +
      (devLink() ? '<a class="btn" href="' + esc(devLink()) + '">Open the sign-in link (local test)</a>' : '') +
      '<p class="note" style="margin-top:14px">Didn’t get it? Check spam.</p><button class="btn w" style="margin-top:18px" data-again="1">Use a different email</button></div>');
    return accWrap('<div class="acc"><h1>Sign in or sign up</h1><p class="s">No password. We email you a link.</p>' +
      '<form id="acf" novalidate><label class="vh" for="aem">Email</label><input class="in" id="aem" name="em" type="email" autocomplete="email" inputmode="email" placeholder="you@email.com" required maxlength="254">' +
      (CFG.turnstile ? '<div class="cf-turnstile" data-sitekey="' + esc(CFG.turnstile) + '"></div>' : '') + '<button class="btn y" style="margin-top:12px" type="submit">Email me a link</button></form>' +
      (err ? '<p class="note" style="color:var(--r);margin-top:10px">' + esc(err) + '</p>' : '') +
      '<p class="sec">What you get</p><div class="pk">' + PERKS.map(function (k) { return '<div class="pki"><span class="pkc">' + ic(k[0], 20, 2.4) + '</span><span><b>' + k[1] + '</b><small>' + k[2] + '</small></span></div>'; }).join('') + '</div>' +
      '<p class="note" style="margin-top:14px">More checklists are $7.99 a car, or $19.99 for every car and truck. We never sell or share your email.</p></div>');
  }
  function accountPage() {
    var T = CFG.titles || {};
    if (!ME) return joinPage();
    var mine = (ME.all ? Object.keys(T) : [ME.free].concat(ME.owned || [])).filter(function (g, j, a) { return g && T[g] && a.indexOf(g) === j; });
    var prog = {}; (ME.progress || []).forEach(function (p) { prog[p.gen] = p.updated; });
    mine.sort(function (a, b) { return (prog[b] || 0) - (prog[a] || 0); });
    var list = mine.slice(0, ME.all ? 12 : 99).map(function (g) { return hk({name: T[g][0], small: (ME.free === g ? 'Free' : 'Unlocked') + (prog[g] ? ' · In progress' : ' · Start'), img: T[g][1], cls: 'mini', href: '/checklist/' + g + '/'}); }).join('');
    var inner = '<div class="acc"><div class="ach"><span class="ava">' + esc((ME.email || '?').charAt(0).toUpperCase()) + '</span><span><h1>Your account</h1><p class="em">' + esc(ME.email) + '</p></span></div>' +
      '<p class="sec">My checklists' + (ME.all ? ' · every car and truck' : '') + '</p>' + (list || '<p class="note">None yet.</p>') + (ME.all && mine.length > 12 ? '<a class="btn w" style="margin-top:4px" href="/checklist/">See every checklist</a>' : '') +
      (ME.all ? '' : '<p class="sec">Get more</p>' + hk({name: 'All cars & trucks', small: 'Every checklist · $19.99', img: ALLCARS.img, img2: ALLCARS.img2, cls: 'mini', href: '/checklist/'})) +
      '<p class="sec">Settings</p><div class="lst"><button data-out="1">Sign out <span style="color:var(--gray2)">' + ic('chev', 18) + '</span></button><button data-out="all">Sign out on every device <span style="color:var(--gray2)">' + ic('chev', 18) + '</span></button><button class="r" data-del="1">Delete my account</button></div>' +
      '<div id="delbox"></div>' +
      '<details class="pv"><summary>Privacy and refunds</summary><p class="note"><!-- needs Elijah’s OK -->We keep your email, what you bought and your checklist answers, so they’re there on any device. That’s all: no password, no card number (Stripe handles payment), and we never sell or share your email. Sign-in links are single-use and stored scrambled. Delete your account here any time, and the answers go with it; we keep only the Stripe receipt, which the law requires.</p>' +
      '<p class="note"><!-- needs Elijah’s OK -->Not happy? Email us within 14 days for a full refund: <a href="mailto:' + esc(CFG.contact) + '">' + esc(CFG.contact) + '</a>.</p></details></div>';
    return accWrap(inner);
  }
  function paintAcc(html) { app.innerHTML = html; wireAccount(); if (window.turnstile && document.querySelector('.cf-turnstile')) try { window.turnstile.render('.cf-turnstile'); } catch (e) {} }
  var ABUSY = false;
  function acctSignin(f) {
    var em = String(f.em.value || '').trim(), tsi = f.querySelector('[name="cf-turnstile-response"]');
    if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(em)) return paintAcc(joinPage('Type your email, like you@email.com.'));
    if (ABUSY) return; ABUSY = true; device(); sessionStorage.removeItem('lcw-next');
    api('POST', '/auth/start', {email: em, next: null, ts: tsi ? tsi.value : undefined}).then(function (j) {
      ABUSY = false;
      if (j._s === 200) { if (j.dev_link) sessionStorage.setItem('lcw-dev-link', j.dev_link); else sessionStorage.removeItem('lcw-dev-link'); return paintAcc(joinPage('', em)); }
      paintAcc(joinPage({email: 'That email doesn’t work here. Use your everyday email.', disposable: 'Please use your everyday email, not a throwaway one.', busy: 'Too many sign-in emails. Try again in an hour.', 'email-off': 'Sign-in emails are paused for a moment. Try again soon.', turnstile: 'Please tick the box to show you’re not a robot.'}[j.error] || 'Couldn’t send the email. Try again in a minute.'));
    });
  }
  function wireAccount() {
    var af = document.getElementById('acf'); if (af) af.onsubmit = function (e) { e.preventDefault(); acctSignin(af); };
    q('[data-again]').forEach(function (b) { b.onclick = function () { paintAcc(joinPage()); }; });
    q('[data-out]').forEach(function (b) { b.onclick = function () { api('POST', '/auth/signout', {all: b.dataset.out === 'all'}).then(function () { dropLocal(); ME = null; paintAcc(accountPage()); }); }; });
    q('[data-del]').forEach(function (b) { b.onclick = function () {
      var box = document.getElementById('delbox'); box.innerHTML = '<form id="delf" class="cd gy" style="padding:14px 16px;margin-top:12px"><p class="note" style="margin-top:0">This deletes your account, your answers and your free checklist. Purchases can’t be restored. Type your email to confirm.</p><input class="in" name="c" type="email" autocomplete="off"><button class="btn" style="margin-top:10px;width:100%;background:var(--r)" type="submit">Delete for good</button></form>';
      document.getElementById('delf').onsubmit = function (e) { e.preventDefault(); api('POST', '/account/delete', {confirm: this.c.value}).then(function (j) { if (j._s === 200) { dropLocal(); ME = null; paintAcc(accountPage()); } else box.querySelector('p').textContent = 'That email doesn’t match this account.'; }); }; }; });
  }
  function bootAccount() { loadMe().then(function () { document.body.classList.toggle('desk', desk()); paintAcc(accountPage()); }); }
  function bootSignin() {
    var m = /#t=(lsl_[A-Za-z0-9_-]{43})/.exec(location.hash);
    history.replaceState(null, '', location.pathname);          // the link is single-use: drop it from the address bar and history
    var msg = function (h, p, a) { document.body.classList.toggle('desk', desk()); app.innerHTML = accWrap('<div class="acc"><h1>' + h + '</h1><p class="s">' + p + '</p>' + (a || '') + '</div>'); };
    if (!m) return msg('That link didn’t work', 'Open the newest email from us, or ask for a new link.', '<a class="btn" href="/account/">Get a new link</a>');
    msg('Signing you in…', '<span class="ld"><i></i></span>');
    api('POST', '/auth/verify', {t: m[1], dev: device()}).then(function (j) {
      if (j._s !== 200) return msg('That link has ' + (j.error === 'used' ? 'already been used' : j.error === 'expired' ? 'expired' : 'a problem'), 'Sign-in links work once, for 15 minutes. Ask for a new one.', '<a class="btn" href="' + (j.next ? '/checklist/' + j.next + '/' : '/account/') + '">Get a new link</a>');
      setToken(j.token, j.exp);
      var g = j.claimed || j.next || sessionStorage.getItem('lcw-next');
      location.replace(g && /^[a-z0-9]+(?:-[a-z0-9]+){0,6}-g\d{1,2}$/.test(g) ? '/checklist/' + g + '/' : '/account/');
    });
  }
  if (CFG.page === 'checklist') bootChecklist(); else if (CFG.page === 'signin') bootSignin(); else bootAccount();
})();
