// 11-14 growth plan 4d: saved cars ("My cars"). Loaded on every page by nav.js.
// Storage: this browser only (localStorage "li-saved", every read and write in try/catch). No account, nothing is sent anywhere.
//   entry = {id: model id (as in /cars/<id>/ and compare.json), y: model year or null (a model page saves the model), n: model name,
//            img: picture path, sy: the year picked on /saved/ for a model entry, t: saved time}
// What it does:
//   1. a Save button next to Share on model pages, year pages and Advanced pages (found from the page's Car JSON-LD or the
//      /cars/<id>/<year>/advanced/ address), plus any [data-lsv-id] button another script draws (the /vin/ report card)
//   2. once something is saved: a count bubble on the header's More / menu button, and "My cars" first in its sheet
//   3. the /saved/ page (#lsvx): each saved model year's score, verdict, top problem and recalls from /assets/vr/<id>.json
//      (vin_report.py), and a "Compare" link to /compare/?cars=<id>-<year>,... (compare.js reads ?cars=, up to 4)
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

  function toggle(c) {
    if (!ok || !c || !c.id) return null;
    const a = read(), i = a.findIndex(x => same(x, c.id, c.y));
    if (i >= 0) { a.splice(i, 1); write(a); return false; }
    if (a.length >= MAX) return 'full';
    a.unshift({ id: c.id, y: c.y ? String(c.y) : null, n: c.n || c.id, img: c.img || '', t: Date.now() });
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

  function mkBtn(c, kind) {
    const b = document.createElement('button'); b.type = 'button';
    b.dataset.lsvId = c.id; if (c.y) b.dataset.lsvY = c.y; b.dataset.lsvN = c.n; if (c.img) b.dataset.lsvImg = c.img;
    if (kind === 'ic') { b.className = 'tb-ic lsv-b'; b.innerHTML = `<span class="tb-ic-i">${HEART}</span><span class="tb-ic-l">Save</span>`; }
    else { b.className = 'btn btn-ghost lsv-b lsv-bt'; b.innerHTML = `${HEART}<span class="lsv-l">Save</span>`; }
    return b;
  }
  function addButtons() {
    const c = pageCar(); if (!c) return;
    let n = 0;
    document.querySelectorAll('[data-share]').forEach(sh => {
      if (sh.classList.contains('shl') || sh.nextElementSibling && sh.nextElementSibling.matches('[data-lsv-id]')) return;
      if (sh.classList.contains('tb-ic')) { sh.after(mkBtn(c, 'ic')); n++; }
      else if (sh.classList.contains('btn') && sh.closest('.ph, .tb-hero, .ycn-wide')) { sh.after(mkBtn(c, 'bt')); n++; }
    });
    if (!n) {   // Advanced pages: no Share button up top, so the Save button goes under the answer line
      const hero = document.querySelector('.ph, .tb-hero'); if (!hero) return;
      const at = hero.querySelector('.ans') || hero.querySelector('h1'); if (!at) return;
      const p = document.createElement('p'); p.className = 'lsv-row'; p.appendChild(mkBtn(c, 'bt')); at.after(p);
    }
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
    const c = { id: b.dataset.lsvId, y: b.dataset.lsvY || null, n: b.dataset.lsvN || b.dataset.lsvId, img: b.dataset.lsvImg || '' };
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
  async function savedPage(root) {
    if (!ok) { root.innerHTML = '<p class="lsv-empty">This browser is blocking site storage (a private window or a privacy setting), so it can&#39;t keep saved cars. Try a regular window.</p>'; return; }
    const D = {}, tried = new Set(), sel = new Set();
    let first = true;
    const key = x => `${x.id}|${yk(x.y)}`;
    const dY = d => { const ys = Object.keys(d.years).sort().reverse(); return ys.find(y => d.years[y].ok && !d.years[y].early) || ys[0]; };
    const yOf = x => { const d = D[x.id]; if (x.y) return String(x.y); if (d && x.sy && d.years[x.sy]) return x.sy; return d ? dY(d) : null; };
    const num = v => (v == null ? '' : Number(v).toLocaleString('en-US'));
    const FB = id => `/assets/ai-models/${id.replace(/\//g, '-')}.webp?v=1`;   // the model's picture (the file name swaps a slash for a dash)
    async function load(L) {
      const need = [...new Set(L.map(x => x.id))].filter(id => !tried.has(id));
      need.forEach(id => tried.add(id));
      await Promise.all(need.map(async id => { try { const r = await fetch(`/assets/vr/${id.replace(/\//g, '_')}.json`); if (r.ok) D[id] = await r.json(); } catch (e) { } }));
    }
    function card(x) {
      const d = D[x.id], y = yOf(x), Y = d && y ? d.years[y] : null, k = key(x);
      const url = d ? d.url + (y && Y ? `${y}/` : '') : `/cars/${x.id}/` + (x.y ? `${x.y}/` : '');
      const img = x.img || FB(x.id);
      const name = esc(d ? d.name : x.n);
      const yr = !x.y && d ? `<label class="lsv-ys"><span class="vh">Model year</span><select data-k="${esc(k)}">${Object.keys(d.years).sort().reverse().map(v => `<option value="${v}"${v === y ? ' selected' : ''}>${v}</option>`).join('')}</select></label>` : `<span class="lsv-yr">${esc(y || '')}</span>`;
      let body;
      if (!d) body = '<p class="lsv-na">Couldn&#39;t load this car&#39;s numbers just now. Refresh to try again.</p>';
      else if (!Y) body = `<p class="lsv-na">No data for the ${esc(y)} yet.</p>`;
      else {
        const sc = Y.ok ? `<div class="lsv-sc"><b class="lsv-li ${esc(Y.cls)}">${Y.li}</b><span>Lemon Index${Y.early ? ' (partial)' : ''}<br>100 = average car</span></div><p class="lsv-w ${esc(Y.cls)}">${esc(Y.word)}.</p>`
          : `<div class="lsv-sc"><b class="lsv-li na">–</b><span>No score yet<br>${esc(Y.pln || 'too few cars sold to score')}</span></div>`;
        const P = Y.parts && Y.parts[0];
        const tp = P ? `<p class="lsv-tp"><span>Top problem</span><b>${esc(P[0])}</b><em>${P[1]}% of its complaints</em></p>` : '<p class="lsv-tp"><span>Top problem</span><b class="lsv-mute">Too few complaints to say</b></p>';
        const facts = [Y.rc != null ? `${num(Y.rc)} recall${Y.rc === 1 ? '' : 's'}` : '', Y.n != null ? `${num(Y.n)} complaints ${Y.early ? 'so far' : 'in its first 3 years'}` : ''].filter(Boolean).join(' · ');
        body = sc + tp + (facts ? `<p class="lsv-f">${facts}</p>` : '');
      }
      return `<article class="lsv-c" data-k="${esc(k)}"><a class="lsv-ph" href="${esc(url)}" tabindex="-1" aria-hidden="true"><img src="${esc(img)}" data-fb="${esc(FB(x.id))}" alt="" width="1000" height="600" loading="lazy" decoding="async"></a>`
        + `<div class="lsv-bd"><h2 class="lsv-n"><a href="${esc(url)}">${name}</a> ${yr}</h2>${body}`
        + `<div class="lsv-act"><label class="lsv-ck"><input type="checkbox" data-k="${esc(k)}"${sel.has(k) ? ' checked' : ''}> Compare</label>`
        + `<a class="lsv-go" href="${esc(url)}">Full report</a><button type="button" class="lsv-rm" data-k="${esc(k)}" aria-label="Remove the ${esc(label(d ? d.name : x.n, y))}">Remove</button></div></div></article>`;
    }
    function draw() {
      const L = read();
      [...sel].forEach(k => { if (!L.some(x => key(x) === k)) sel.delete(k); });
      if (first) { L.slice(0, CMP).forEach(x => sel.add(key(x))); first = false; }
      if (!L.length) {
        root.innerHTML = `<div class="lsv-empty"><p><b>No saved cars yet.</b> Tap <span class="lsv-hint">${HEART} Save</span> on any car or model-year page, or on a VIN report, and it shows up here.</p><p class="lsv-go2"><a class="btn" href="/cars/">Find a car</a><a class="btn btn-ghost" href="/vin/">Check a VIN</a></p></div>`;
        return;
      }
      const picked = L.filter(x => sel.has(key(x)));
      const q = picked.map(x => { const y = yOf(x); return encodeURIComponent(x.id) + (y ? `-${y}` : ''); }).join(',');
      const bar = `<div class="lsv-bar"><p class="lsv-cnt"><b>${L.length}</b> saved car${L.length === 1 ? '' : 's'}<span> · ${picked.length} picked to compare</span></p>`
        + (picked.length ? `<a class="btn lsv-cmp" href="/compare/?cars=${q}">Compare these${picked.length > 1 ? ` ${picked.length}` : ''}</a>` : '<span class="btn lsv-cmp lsv-off" aria-disabled="true">Pick cars to compare</span>')
        + `<p class="lsv-msg" role="status"></p></div>`;
      root.innerHTML = bar + `<div class="lsv-g">${L.map(card).join('')}</div>`
        + `<p class="lsv-src">Scores, top problems and recalls come from owner complaints and recalls filed with NHTSA, per car sold in the U.S. They're the model year's record, not one car's history, and a complaint isn't proof of a defect. <a href="/method/">How the score works</a>. Your list is kept in this browser only: no account, and nothing is sent to us. <button type="button" class="lsv-clr">Remove all</button></p>`;
    }
    // a missing picture: the model's picture, else no picture block (CSP blocks inline onerror, so one capturing listener)
    root.addEventListener('error', e => { const i = e.target; if (!i || i.tagName !== 'IMG' || !i.closest('.lsv-ph')) return;
      if (i.dataset.fb && i.getAttribute('src') !== i.dataset.fb) i.src = i.dataset.fb; else i.closest('.lsv-ph').classList.add('lsv-noimg'); }, true);
    root.addEventListener('change', e => {
      const t = e.target, k = t.dataset.k; if (!k) return;
      if (t.type === 'checkbox') {
        if (t.checked && sel.size >= CMP) { t.checked = false; const m = root.querySelector('.lsv-msg'); if (m) m.textContent = `The compare tool takes up to ${CMP} cars. Untick one first.`; return; }
        t.checked ? sel.add(k) : sel.delete(k); draw();
      } else if (t.tagName === 'SELECT') {
        const a = read(), x = a.find(z => key(z) === k); if (x) { x.sy = t.value; write(a); } draw();
      }
    });
    root.addEventListener('click', e => {
      const rm = e.target.closest('.lsv-rm');
      if (rm) { write(read().filter(x => key(x) !== rm.dataset.k)); sel.delete(rm.dataset.k); draw(); sync(); return; }
      if (e.target.closest('.lsv-clr') && confirm('Remove every saved car from this browser?')) { write([]); sel.clear(); draw(); sync(); }
    });
    view = async () => { await load(read()); draw(); };
    await view();
  }

  window.LSAVE = { sync, has, ok };
  if (!document.querySelector('link[href^="/assets/saved.css"]')) { const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = '/assets/saved.css?v=1'; document.head.appendChild(l); }
  const go = () => {
    if (ok) addButtons();
    sync();
    const root = document.getElementById('lsvx'); if (root) savedPage(root);
  };
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', go) : go();
})();
