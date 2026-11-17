// 11-14 growth plan 4d: saved cars ("My cars"). Loaded on every page by nav.js.
// Storage: this browser only (localStorage "li-saved", every read and write in try/catch). No account; the list itself is never sent anywhere
// (the /saved/ recall-email box sends only the cars the visitor ticks, with the email they type, to the lemon-alerts Worker).
//   entry = {id: model id (as in /cars/<id>/ and compare.json), y: model year or null (a model page saves the model), n: model name,
//            img: picture path, sy: the year picked on /saved/ for a model entry, t: saved time,
//            11-15: u: page address + k: kind + c: compare.json id for pages with no vr file (performance, JDM, supercar, complaints-only,
//            EV-only and motorcycle pages; data in /assets/saved-x.json, saved_page.py), sg: the generation picked for a performance car}
// What it does:
//   1. a Save button next to Share on model pages, year pages and Advanced pages (found from the page's Car JSON-LD or the
//      /cars/<id>/<year>/advanced/ address), plus any [data-lsv-id] button another script draws (the /vin/ report card);
//      11-15: on the pages above, found by address in /assets/saved-x.json (fetched only on those pages)
//   2. once something is saved: a count bubble on the header's More / menu button, and "My cars" first in its sheet
//   3. the /saved/ page (#lsvx): each saved model year's score, verdict, top problem and recalls from /assets/vr/<id>.json
//      (vin_report.py), the other kinds from saved-x.json, a "Compare" link to /compare/?cars=<id>-<year>,... (compare.js reads ?cars=,
//      up to 4), and (11-15) "Get recall emails for these cars": the recall-alert signup (assets/ralert.js) for up to 5 of them at once
(() => {
  if (window.LSAVE) return;
  const K = 'li-saved', MAX = 24, CMP = 4;
  const ok = (() => { try { localStorage.setItem('li-t', '1'); localStorage.removeItem('li-t'); return true; } catch (e) { return false; } })();
  const read = () => { if (!ok) return []; try { const a = JSON.parse(localStorage.getItem(K) || '[]'); return Array.isArray(a) ? a.filter(x => x && typeof x.id === 'string' && x.id) : []; } catch (e) { return []; } };
  const write = a => { try { localStorage.setItem(K, JSON.stringify(a.slice(0, MAX))); return true; } catch (e) { return false; } };
  const yk = y => (y == null || y === '' ? '' : String(y));
  const same = (x, id, y) => x.id === id && yk(x.y) === yk(y);
  const has = (id, y) => read().some(x => same(x, id, y));
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const HEART = '<svg class="lsv-h" aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20.5s-7.5-4.6-9.2-9.4C1.7 7.9 3.6 4.5 7 4.5c2 0 3.7 1.1 5 3 1.3-1.9 3-3 5-3 3.4 0 5.3 3.4 4.2 6.6-1.7 4.8-9.2 9.4-9.2 9.4z"/></svg>';
  const label = (n, y) => (y ? `${y} ` : '') + n;
  // 11-15: the pages with no vr file (saved_page.py SVX_WRITE), keyed by address; one small cached file
  let sxP = null;
  const SX = () => sxP || (sxP = fetch('/assets/saved-x.json?v=1').then(r => (r.ok ? r.json() : null)).then(j => (j && j.p) || {}).catch(() => ({})));

  function toggle(c) {
    if (!ok || !c || !c.id) return null;
    const a = read(), i = a.findIndex(x => same(x, c.id, c.y));
    if (i >= 0) { a.splice(i, 1); write(a); return false; }
    if (a.length >= MAX) return 'full';
    const e = { id: c.id, y: c.y ? String(c.y) : null, n: c.n || c.id, img: c.img || '', t: Date.now() };
    if (c.u) Object.assign(e, { u: c.u, k: c.k || '', c: c.c || '' });
    a.unshift(e);
    return write(a) ? true : null;
  }

  // ---- 1. which car this page is
  function pageCar() {
    const p = location.pathname;
    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
      let d; try { d = JSON.parse(s.textContent); } catch (e) { continue; }
      if (!d || d['@type'] !== 'Car' || !d.url) continue;
      let u; try { u = new URL(d.url, location.origin); } catch (e) { continue; }
      if (u.pathname !== p) continue;
      const m = u.pathname.match(/^\/cars\/(.+?)\/(?:(\d{4})\/)?$/); if (!m) continue;
      let img = ''; try { if (d.image) { const iu = new URL(d.image, location.origin); if (iu.origin === location.origin || /(^|\.)lemonindex\.com$/.test(iu.hostname)) img = iu.pathname + iu.search; } } catch (e) { }
      return { id: m[1], y: m[2] || null, n: String(d.name || '').replace(/^\d{4}\s+/, ''), img };
    }
    const a = p.match(/^\/cars\/(.+?)\/(\d{4})\/advanced\/$/);
    if (a) {
      const h = document.querySelector('h1'), n = h && (h.textContent.match(/^\d{4}\s+(.+?)\.\s*Advanced/) || [])[1];
      if (n) return { id: a[1], y: a[2], n, img: '' };
    }
    return null;
  }
  // 11-15: performance (/cars/camaro-ss/), JDM, supercar, complaints-only, EV (/electric/<id>/) and motorcycle pages
  async function pageX() {
    const m = location.pathname.match(/^\/(cars|supercars|jdm|motorcycles|electric)\/([^/]+)\/(?:advanced\/)?$/); if (!m) return null;
    const base = `/${m[1]}/${m[2]}/`, r = (await SX())[base]; if (!r) return null;
    if (r.m) return { id: r.m, y: null, n: r.n, img: '' };   // an EV page whose model has a full page: saves that model
    return { id: r.c || base, y: null, n: r.n, img: r.im || '', u: base, k: r.k, c: r.c || '' };
  }

  function mkBtn(c, kind) {
    const b = document.createElement('button'); b.type = 'button';
    b.dataset.lsvId = c.id; if (c.y) b.dataset.lsvY = c.y; b.dataset.lsvN = c.n; if (c.img) b.dataset.lsvImg = c.img;
    if (c.u) { b.dataset.lsvU = c.u; b.dataset.lsvK = c.k || ''; b.dataset.lsvC = c.c || ''; }
    if (kind === 'ic') { b.className = 'tb-ic lsv-b'; b.innerHTML = `<span class="tb-ic-i">${HEART}</span><span class="tb-ic-l">Save</span>`; }
    else { b.className = 'btn btn-ghost lsv-b lsv-bt'; b.innerHTML = `${HEART}<span class="lsv-l">Save</span>`; }
    return b;
  }
  function addButtons(c) {
    if (!c) return;
    let n = 0;
    document.querySelectorAll('[data-share]').forEach(sh => {
      if (sh.classList.contains('shl') || sh.nextElementSibling && sh.nextElementSibling.matches('[data-lsv-id]')) return;
      if (sh.classList.contains('tb-ic')) { sh.after(mkBtn(c, 'ic')); n++; }
      else if (sh.classList.contains('btn') && sh.closest('.ph, .tb-hero, .ycn-wide')) { sh.after(mkBtn(c, 'bt')); n++; }
    });
    if (n) return;
    const hero = document.querySelector('.ph, .tb-hero'); if (!hero || hero.querySelector('[data-lsv-id]')) return;
    const row = hero.querySelector('.n3-cmp');   // supercar pages: next to "Compare it with another car"
    if (row) { row.appendChild(mkBtn(c, 'bt')); return; }
    // Advanced, performance, EV, motorcycle and complaints-only pages: no Share button up top, so the Save button goes under the answer line
    const at = hero.querySelector('.ans') || hero.querySelector('h1'); if (!at) return;
    const p = document.createElement('p'); p.className = 'lsv-row'; p.appendChild(mkBtn(c, 'bt')); at.after(p);
  }

  // ---- state on every Save button + the header count
  function sync(root) {
    const L = read();
    (root || document).querySelectorAll('[data-lsv-id]').forEach(b => {
      const on = L.some(x => same(x, b.dataset.lsvId, b.dataset.lsvY)), nm = label(b.dataset.lsvN || '', b.dataset.lsvY);
      b.setAttribute('aria-pressed', on ? 'true' : 'false'); b.classList.toggle('on', on);
      b.setAttribute('aria-label', on ? `Saved to My cars: ${nm}. Tap to remove` : `Save the ${nm} to My cars`);
      const l = b.querySelector('.tb-ic-l, .lsv-l'); if (l) l.textContent = on ? 'Saved' : 'Save';
    });
    badge(L.length);
  }
  // the header is full at every width (11-14 test: an extra item squeezed the links on desktop and pushed the menu off a 375 px phone),
  // so the count rides as a small bubble on the existing More / menu button, and "My cars" is the first link in their sheet
  let sl = null;
  function badge(n) {
    const t = n > 99 ? '99+' : String(n);
    document.querySelectorAll('.gh .gh-more, .gh .gh-menu').forEach(b => {
      b.classList.toggle('lsv-dot', !!n);
      if (b.dataset.lsvL === undefined) b.dataset.lsvL = b.getAttribute('aria-label') || '';
      if (n) { b.dataset.lsv = t; if (b.dataset.lsvL) b.setAttribute('aria-label', `${b.dataset.lsvL} (${n} saved car${n === 1 ? '' : 's'})`); }
      else { delete b.dataset.lsv; if (b.dataset.lsvL) b.setAttribute('aria-label', b.dataset.lsvL); }
    });
    const g = document.querySelector('.gh-sheet .gh-g0'); if (!g) return;
    if (!n) { if (sl) sl.hidden = true; return; }
    if (!sl) { sl = document.createElement('a'); sl.className = 'gh-i0 lsv-sl'; sl.href = '/saved/'; g.after(sl); }
    sl.hidden = false; sl.innerHTML = `${HEART}<span>My cars</span><b>${t}</b>`;
    if (location.pathname === '/saved/') sl.setAttribute('aria-current', 'page');
  }

  let tt = null;
  function toast(html) {
    let t = document.querySelector('.lsv-toast');
    if (!t) { t = document.createElement('div'); t.className = 'lsv-toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.innerHTML = html; t.classList.add('in'); clearTimeout(tt); tt = setTimeout(() => t.classList.remove('in'), 4000);
  }

  document.addEventListener('click', e => {
    const b = e.target.closest('[data-lsv-id]'); if (!b) return;
    e.preventDefault();
    const c = { id: b.dataset.lsvId, y: b.dataset.lsvY || null, n: b.dataset.lsvN || b.dataset.lsvId, img: b.dataset.lsvImg || '', u: b.dataset.lsvU || '', k: b.dataset.lsvK || '', c: b.dataset.lsvC || '' };
    const r = toggle(c);
    if (r === true) toast(`Saved the ${esc(label(c.n, c.y))}. <a href="/saved/">See My cars</a>`);
    else if (r === false) toast(`Removed the ${esc(label(c.n, c.y))} from My cars.`);
    else if (r === 'full') toast(`My cars holds up to ${MAX}. <a href="/saved/">Remove one first</a>`);
    else toast('This browser is blocking site storage, so cars can&#39;t be saved here.');
    sync(); if (view) view();
  });
  window.addEventListener('storage', e => { if (e.key === K) { sync(); if (view) view(); } });

  // ---- 3. the /saved/ page
  let view = null;
  const KIND = { perf: 'Performance car', jdm: 'JDM', sc: 'Supercar', co: 'Complaints only', ev: 'Electric', moto: 'Motorcycle' };
  // the site's one set of band words (build.py band(), compare.js word())
  const band = li => li == null ? ['na', 'No score'] : li < 50 ? ['good', 'One of the most reliable'] : li < 85 ? ['good', 'Better than average'] : li <= 115 ? ['mid', 'About average'] : li < 200 ? ['bad', 'Worse than average'] : ['bad', 'Avoid'];
  const RAV = '1115s';
  let raP = null;
  const loadRA = () => raP || (raP = new Promise(res => {
    if (window.LXRA && window.LXRA.cars) { res(true); return; }
    if (!document.querySelector('link[href^="/assets/ralert.css"]')) { const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = `/assets/ralert.css?v=${RAV}`; document.head.appendChild(l); }
    const s = document.createElement('script'); s.src = `/assets/ralert.js?v=${RAV}`; s.onload = () => res(!!(window.LXRA && window.LXRA.cars)); s.onerror = () => res(false); document.head.appendChild(s);
  }));
  async function savedPage(root) {
    if (!ok) { root.innerHTML = '<p class="lsv-empty">This browser is blocking site storage (a private window or a privacy setting), so it can&#39;t keep saved cars. Try a regular window.</p>'; return; }
    const D = {}, tried = new Set(), sel = new Set();
    let X = null, first = true;
    root.innerHTML = '<div class="lsv-top"></div><div class="lsv-rap" id="lsv-rap" hidden></div><div class="lsv-list"></div>';
    const top = root.querySelector('.lsv-top'), rap = root.querySelector('.lsv-rap'), list = root.querySelector('.lsv-list');
    const key = x => `${x.id}|${yk(x.y)}`;
    const dY = d => { const ys = Object.keys(d.years).sort().reverse(); return ys.find(y => d.years[y].ok && !d.years[y].early) || ys[0]; };
    const yOf = x => { const d = D[x.id]; if (x.y) return String(x.y); if (d && x.sy && d.years[x.sy]) return x.sy; return d ? dY(d) : null; };
    // the saved-x record: entries saved on those pages, or a model whose vr file didn't load but that page exists there
    const xr = x => (X ? (x.u ? X[x.u] : (!D[x.id] && tried.has(x.id) ? X[`/cars/${x.id}/`] : null)) : null) || null;
    const isX = x => !!(x.u || xr(x));
    // the generation (performance) or model year (supercar, complaints-only) shown on a saved-x card
    const xv = (x, r) => r.g ? (r.g.some(g => g[0] === x.sg) ? x.sg : r.d) : r.y ? (r.y[x.sy] ? x.sy : String(r.d)) : null;
    const gen = (x, r) => r.g.find(g => g[0] === xv(x, r)) || r.g[r.g.length - 1];
    const num = v => (v == null ? '' : Number(v).toLocaleString('en-US'));
    const pl = (n, w) => `${num(n)} ${w}${n === 1 ? '' : 's'}`;
    const FB = id => `/assets/ai-models/${id.replace(/\//g, '-')}.webp?v=1`;   // the model's picture (the file name swaps a slash for a dash)
    async function load(L) {
      const need = [...new Set(L.filter(x => !x.u).map(x => x.id))].filter(id => !tried.has(id));
      need.forEach(id => tried.add(id));
      await Promise.all(need.map(async id => { try { const r = await fetch(`/assets/vr/${id.replace(/\//g, '_')}.json`); if (r.ok) D[id] = await r.json(); } catch (e) { } }));
      if (!X && L.some(x => x.u || !D[x.id])) X = await SX();
    }
    const cmpTok = x => {
      if (isX(x)) { const r = xr(x); if (!r || !r.c) return null; const v = xv(x, r); return encodeURIComponent(r.c) + (v ? `-${v}` : ''); }
      const y = yOf(x); return encodeURIComponent(x.id) + (y ? `-${y}` : '');
    };
    const pickBox = (k, f, opts, v, lab) => `<label class="lsv-ys"><span class="vh">${lab}</span><select data-k="${esc(k)}" data-f="${f}">${opts.map(([o, l]) => `<option value="${esc(o)}"${o === v ? ' selected' : ''}>${esc(l)}</option>`).join('')}</select></label>`;
    const facts = a => { a = a.filter(Boolean); return a.length ? `<p class="lsv-f">${a.join(' · ')}</p>` : ''; };
    const topBox = (t, note) => t ? `<p class="lsv-tp"><span>Top problem</span><b>${esc(t[0])}</b>${note ? `<em>${note}</em>` : ''}</p>` : '';
    const actions = (x, k, url, name, canCmp) => `<div class="lsv-act">${canCmp ? `<label class="lsv-ck"><input type="checkbox" data-k="${esc(k)}"${sel.has(k) ? ' checked' : ''}> Compare</label>` : '<span class="lsv-nocmp">Not in the compare tool</span>'}`
      + `<a class="lsv-go" href="${esc(url)}">Full report</a><button type="button" class="lsv-rm" data-k="${esc(k)}" aria-label="Remove the ${esc(name)}">Remove</button></div>`;
    const shell = (x, k, url, img, fb, title, kind, body, canCmp, rmName) => `<article class="lsv-c" data-k="${esc(k)}"><a class="lsv-ph" href="${esc(url)}" tabindex="-1" aria-hidden="true"><img src="${esc(img)}" data-fb="${esc(fb)}" alt="" width="1000" height="600" loading="lazy" decoding="async"></a>`
      + `<div class="lsv-bd">${kind ? `<p class="lsv-kd">${esc(kind)}</p>` : ''}<h2 class="lsv-n">${title}</h2>${body}${actions(x, k, url, rmName, canCmp)}</div></article>`;
    // 11-15: performance / JDM, supercar, complaints-only, EV-only and motorcycle cards: only what their own pages show
    function xcard(x) {
      const r = xr(x), k = key(x), url = x.u || `/cars/${x.id}/`, name = r ? r.n : x.n;
      const img = x.img || (r && r.im) || '', fb = (r && r.im) || '';
      if (!r) return shell(x, k, url, img, fb, `<a href="${esc(url)}">${esc(name)}</a>`, KIND[x.k] || '', '<p class="lsv-na">Couldn&#39;t load this car&#39;s numbers just now. Refresh to try again.</p>', false, name);
      const v = xv(x, r); let pick = '', body = '';
      if (r.g) {   // [id, code, years, trim, hp, 0-60, engine, complaints, recalls, y0, y1, 0-60 trim]
        const G = gen(x, r), mk = r.nm ? r.nm[1].toLowerCase().replace(/\b[a-z]/g, c => c.toUpperCase()) : '';
        pick = r.g.length > 1 ? pickBox(k, 'sg', r.g.map(g => [g[0], `${g[1]} · ${g[2]}`]), G[0], 'Generation') : `<span class="lsv-yr">${esc(G[1])} · ${esc(G[2])}</span>`;
        body = (G[4] != null ? `<div class="lsv-sc"><b class="lsv-li">${esc(G[4])}</b><span>horsepower<br>${esc(G[3] || '')}</span></div>` : '')
          + (G[5] ? `<p class="lsv-w">0–60 mph in ${esc(G[5])} s${G[11] ? ` <small>(${esc(G[11])})</small>` : ''}</p>` : '')
          + (G[6] ? `<p class="lsv-tp"><span>Engine</span><b>${esc(G[6])}</b></p>` : '')
          + facts([G[7] != null ? `${pl(G[7], 'owner complaint')}${mk ? ` filed under ${esc(mk)}` : ''}` : '', G[8] != null ? pl(G[8], 'recall') : '', esc(G[2])]);
      } else if (r.k === 'sc') {   // year: [recalls, mpg lo, mpg hi, engine]
        const Y = r.y[v] || [];
        pick = pickBox(k, 'sy', Object.keys(r.y).sort().reverse().map(y => [y, y]), v, 'Model year');
        body = '<div class="lsv-sc"><b class="lsv-li na">–</b><span>No score<br>owner complaints are too rare to score supercars</span></div>'
          + (Y[3] ? `<p class="lsv-tp"><span>Engine</span><b>${esc(Y[3])}</b></p>` : '')
          + facts([Y[1] != null ? `${Y[1] === Y[2] ? Y[1] : `${Y[1]}–${Y[2]}`} mpg combined (EPA)` : '', Y[0] != null ? `${pl(Y[0], 'recall')} for the ${esc(v)}` : '']);
      } else if (r.k === 'co') {   // year: [complaints, recalls]
        const Y = r.y[v] || [];
        pick = pickBox(k, 'sy', Object.keys(r.y).sort().reverse().map(y => [y, y]), v, 'Model year');
        body = '<div class="lsv-sc"><b class="lsv-li na">–</b><span>No score yet<br>no U.S. sales figure to score it</span></div>'
          + topBox(r.tp, r.tp && r.tp[1] != null ? `${esc(r.tp[1])}% of its complaints, all years` : '')
          + facts([Y[0] != null ? `${pl(Y[0], 'complaint')} about the ${esc(v)}` : '', Y[1] != null ? pl(Y[1], 'recall') : '']);
      } else if (r.k === 'ev') {
        const [cl, w] = band(r.li);
        body = (r.li != null ? `<div class="lsv-sc"><b class="lsv-li ${cl}">${esc(r.li)}</b><span>EV score, ${esc(r.w || '')}<br>100 = average car</span></div><p class="lsv-w ${cl}">${esc(w)}.</p>` : '')
          + topBox(r.tp, 'most-named in complaints')
          + facts([r.p != null ? `${num(r.p)} complaints per 100,000 sold` : '', r.rc != null ? pl(r.rc, 'recall') : '', r.rg ? `EPA range ${r.rg[0] === r.rg[1] ? r.rg[0] : `${r.rg[0]}–${r.rg[1]}`} mi` : '']);
      } else if (r.k === 'moto') {
        body = `<div class="lsv-sc"><b class="lsv-li">${num(r.cn)}</b><span>owner complaints<br>${esc(r.yr || '')} models</span></div>`
          + topBox(r.tp, r.tp && r.tp[1] != null ? `${esc(r.tp[1])}% of its complaints` : '')
          + facts([r.rc != null ? pl(r.rc, 'recall') : '', r.s != null ? `${esc(r.s)}% involved a crash, fire or injury` : '']);
      }
      return shell(x, k, url, img, fb, `<a href="${esc(url)}">${esc(name)}</a> ${pick}`, KIND[r.k] || '', body, !!r.c, name);
    }
    function card(x) {
      if (isX(x)) return xcard(x);
      const d = D[x.id], y = yOf(x), Y = d && y ? d.years[y] : null, k = key(x);
      const url = d ? d.url + (y && Y ? `${y}/` : '') : `/cars/${x.id}/` + (x.y ? `${x.y}/` : '');
      const img = x.img || FB(x.id);
      const yr = !x.y && d ? pickBox(k, 'sy', Object.keys(d.years).sort().reverse().map(v => [v, v]), y, 'Model year') : `<span class="lsv-yr">${esc(y || '')}</span>`;
      let body;
      if (!d) body = '<p class="lsv-na">Couldn&#39;t load this car&#39;s numbers just now. Refresh to try again.</p>';
      else if (!Y) body = `<p class="lsv-na">No data for the ${esc(y)} yet.</p>`;
      else {
        const sc = Y.ok ? `<div class="lsv-sc"><b class="lsv-li ${esc(Y.cls)}">${Y.li}</b><span>Lemon Index${Y.early ? ' (partial)' : ''}<br>100 = average car</span></div><p class="lsv-w ${esc(Y.cls)}">${esc(Y.word)}.</p>`
          : `<div class="lsv-sc"><b class="lsv-li na">–</b><span>No score yet<br>${esc(Y.pln || 'too few cars sold to score')}</span></div>`;
        const P = Y.parts && Y.parts[0];
        const tp = P ? `<p class="lsv-tp"><span>Top problem</span><b>${esc(P[0])}</b><em>${P[1]}% of its complaints</em></p>` : '<p class="lsv-tp"><span>Top problem</span><b class="lsv-mute">Too few complaints to say</b></p>';
        body = sc + tp + facts([Y.rc != null ? pl(Y.rc, 'recall') : '', Y.n != null ? `${num(Y.n)} complaints ${Y.early ? 'so far' : 'in its first 3 years'}` : '']);
      }
      return shell(x, k, url, img, FB(x.id), `<a href="${esc(url)}">${esc(d ? d.name : x.n)}</a> ${yr}`, '', body, true, label(d ? d.name : x.n, y));
    }
    // 11-15: the cars the recall-email box can watch (year + the NHTSA names the site's recall lists use), and the ones it can't yet
    function raList() {
      const out = [], seen = new Set(), NOW = new Date().getFullYear();
      for (const x of read()) {
        if (isX(x)) {
          const r = xr(x);
          if (r && r.g && r.nm) {
            const G = gen(x, r), ys = []; for (let y = Math.min(G[10], NOW + 1); y >= G[9]; y--) ys.push(String(y));
            const kk = `p|${r.c}|${G[0]}`; if (!seen.has(kk) && ys.length) { seen.add(kk); out.push({ k: kk, l: r.n, ys, n: [r.nm], f: "" }); }
          } else { const l = r ? r.n : x.n; if (!seen.has('x|' + l)) { seen.add('x|' + l); out.push({ k: 'x|' + key(x), l, x: 1 }); } }
          continue;
        }
        const d = D[x.id], y = yOf(x), Y = d && y ? d.years[y] : null;
        if (!Y) continue;
        if (!Y.nm) { const l = `${y} ${d.name}`; if (!seen.has('x|' + l)) { seen.add('x|' + l); out.push({ k: 'x|' + key(x), l, x: 1 }); } continue; }
        const kk = `${y}|${JSON.stringify(Y.nm)}`; if (seen.has(kk)) continue; seen.add(kk);
        out.push({ k: kk, l: d.name, y, n: Y.nm, f: x.id });
      }
      return out;
    }
    const raSync = () => { const el = rap.querySelector('[data-ra]'); if (el && window.LXRA && window.LXRA.cars) window.LXRA.cars(el, raList()); };
    function draw() {
      const L = read();
      [...sel].forEach(k => { if (!L.some(x => key(x) === k)) sel.delete(k); });
      if (first) { L.filter(x => cmpTok(x)).slice(0, CMP).forEach(x => sel.add(key(x))); first = false; }
      if (!L.length) {
        top.innerHTML = ''; rap.hidden = true;
        list.innerHTML = `<div class="lsv-empty"><p><b>No saved cars yet.</b> Tap <span class="lsv-hint">${HEART} Save</span> on any car or model-year page, or on a VIN report, and it shows up here.</p><p class="lsv-go2"><a class="btn" href="/cars/">Find a car</a><a class="btn btn-ghost" href="/vin/">Check a VIN</a></p></div>`;
        return;
      }
      const picked = L.filter(x => sel.has(key(x)) && cmpTok(x));
      const q = picked.map(cmpTok).join(',');
      top.innerHTML = `<div class="lsv-bar"><p class="lsv-cnt"><b>${L.length}</b> saved car${L.length === 1 ? '' : 's'}<span> · ${picked.length} picked to compare</span></p><div class="lsv-btns">`
        + `<button type="button" class="btn btn-ghost lsv-rab" aria-controls="lsv-rap" aria-expanded="${rap.hidden ? 'false' : 'true'}">Get recall emails for these cars</button>`
        + (picked.length ? `<a class="btn lsv-cmp" href="/compare/?cars=${q}">Compare these${picked.length > 1 ? ` ${picked.length}` : ''}</a>` : '<span class="btn lsv-cmp lsv-off" aria-disabled="true">Pick cars to compare</span>')
        + `</div><p class="lsv-msg" role="status"></p></div>`;
      const anyX = L.some(isX);
      list.innerHTML = `<div class="lsv-g">${L.map(card).join('')}</div>`
        + `<p class="lsv-src">Scores, top problems and recalls come from owner complaints and recalls filed with NHTSA, per car sold in the U.S. They're the model year's record, not one car's history, and a complaint isn't proof of a defect.${anyX ? ' Performance, supercar, complaints-only and motorcycle cards show the same raw counts as their pages (not per car sold); an EV score counts complaints filed by the end of the year after the model year, a shorter window than the main score.' : ''} <a href="/method/">How the score works</a>. Your list is kept in this browser only: no account, and nothing is sent to us. <button type="button" class="lsv-clr">Remove all</button></p>`;
      if (!rap.hidden) raSync();
    }
    // a missing picture: the model's picture, else no picture block (CSP blocks inline onerror, so one capturing listener)
    root.addEventListener('error', e => { const i = e.target; if (!i || i.tagName !== 'IMG' || !i.closest('.lsv-ph')) return;
      if (i.dataset.fb && i.getAttribute('src') !== i.dataset.fb) i.src = i.dataset.fb; else i.closest('.lsv-ph').classList.add('lsv-noimg'); }, true);
    list.addEventListener('change', e => {
      const t = e.target, k = t.dataset.k; if (!k) return;
      if (t.type === 'checkbox') {
        if (t.checked && sel.size >= CMP) { t.checked = false; const m = top.querySelector('.lsv-msg'); if (m) m.textContent = `The compare tool takes up to ${CMP} cars. Untick one first.`; return; }
        t.checked ? sel.add(k) : sel.delete(k); draw();
      } else if (t.tagName === 'SELECT') {
        const a = read(), x = a.find(z => key(z) === k); if (x) { x[t.dataset.f === 'sg' ? 'sg' : 'sy'] = t.value; write(a); } draw();
      }
    });
    root.addEventListener('click', async e => {
      if (e.target.closest('.lsv-rab')) {
        const b = e.target.closest('.lsv-rab'), open = rap.hidden;
        rap.hidden = !open; b.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (!open) return;
        if (!rap.firstChild) {
          rap.innerHTML = '<p class="lsv-load">Loading…</p>';
          if (!(await loadRA())) { rap.innerHTML = '<p class="lsv-na">The recall email sign-up didn&#39;t load. Refresh to try again.</p>'; raP = null; return; }
          rap.innerHTML = '<div class="rla" data-ra="{&quot;multi&quot;:1}"></div>';
        }
        raSync();
        const em = rap.querySelector('.rla-e'); rap.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); if (em && matchMedia('(hover: hover)').matches) em.focus({ preventScroll: true });
        return;
      }
      const rm = e.target.closest('.lsv-rm');
      if (rm) { write(read().filter(x => key(x) !== rm.dataset.k)); sel.delete(rm.dataset.k); draw(); sync(); return; }
      if (e.target.closest('.lsv-clr') && confirm('Remove every saved car from this browser?')) { write([]); sel.clear(); draw(); sync(); }
    });
    view = async () => { await load(read()); draw(); };
    await view();
  }

  window.LSAVE = { sync, has, ok };
  if (!document.querySelector('link[href^="/assets/saved.css"]')) { const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = '/assets/saved.css?v=2'; document.head.appendChild(l); }
  const go = () => {
    const c = ok ? pageCar() : null;
    if (c) addButtons(c);
    else if (ok) pageX().then(x => { if (x) { addButtons(x); sync(); } }).catch(() => { });
    sync();
    const root = document.getElementById('lsvx'); if (root) savedPage(root);
  };
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', go) : go();
})();
