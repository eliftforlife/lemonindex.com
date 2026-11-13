// The Lemon Index explorer (10-22): search, type tabs, brand filter, sort, plain-English scores, hover explanations, compare two cars.
// Data comes from <script id="cars" type="application/json"> that build.py writes into the page (131 models).
(() => {
  // hover tooltip (mouse); touch users open the row instead
  const T = document.createElement('div'); T.className = 'tip'; T.hidden = true; document.body.appendChild(T);
  document.addEventListener('mouseover', e => { const x = e.target.closest('[data-tip]'); if (!x) { T.hidden = true; return; }
    T.textContent = x.dataset.tip; T.hidden = false; const r = x.getBoundingClientRect();
    T.style.left = Math.min(innerWidth - 336, Math.max(8, r.left)) + 'px'; T.style.top = (r.bottom + 8) + 'px'; });
  addEventListener('scroll', () => { T.hidden = true; }, { passive: true });
  const el = document.getElementById('cars'); if (!el) return;
  const CARS = JSON.parse(el.textContent);
  const $ = id => document.getElementById(id);
  const fmt = x => (x >= 10 ? Math.round(x) : Math.round(x * 10) / 10).toString();
  const big = n => n >= 1e6 ? (n / 1e6).toFixed(2).replace(/0$/, '') + 'M' : Math.round(n / 1e3) + 'K';
  const MAX = 440;                                   // bar scale: 0..440, so 100 (average) sits at ~23%
  // 11-12 round 2 (Carlos): plain fractions, not "1.9× fewer" (same wording as build.py plain())
  const frac = li => { const f = li / 100; if (f >= 0.9 && f <= 1.1) return null;
    if (f < 1) { for (const [hi, w] of [[0.15, 'less than a sixth as many'], [0.22, 'about a fifth as many'], [0.29, 'about a quarter as many'], [0.37, 'about a third as many'], [0.45, 'a bit under half as many'],
      [0.56, 'about half as many'], [0.63, 'a bit over half as many'], [0.71, 'about two-thirds as many'], [0.8, 'about three-quarters as many']]) if (f < hi) return w; return 'somewhat fewer'; }
    return f < 1.35 ? 'a bit more than' : f < 1.75 ? 'about one and a half times' : f < 2.5 ? 'about twice' : `about ${Math.round(f)} times`; };
  const words = c => { const w = frac(c.li); return !w ? 'about average' : c.li < 90 ? (w === 'somewhat fewer' ? 'somewhat fewer complaints than the average car' : `${w} complaints as the average car`) : `${w} the average car's complaints`; };
  const tip = c => `${c.name}: ${c.per100k} complaints per 100,000 sold, vs ${c.avg} for an average car of the same years. `
    + (c.li < 100 ? `About 1 complaint for every ${fmt(100 / c.li)} an average car gets.` : `About ${fmt(c.li / 100)} complaints for every 1 an average car gets.`);
  const issue = c => c.issues.length ? `${c.issues[0][0]} (${c.issues[0][1]}% of complaints)` : '—';
  const S = { q: '', seg: 'all', brand: '', sort: 'best', all: false, open: null, pick: [] };
  try { const s = JSON.parse(sessionStorage.getItem('li-ex') || '{}'); Object.assign(S, { seg: s.seg || 'all', sort: s.sort || 'best' }); } catch (e) {}

  function list() {
    const q = S.q.trim().toLowerCase();
    let L = CARS.filter(c => (S.seg === 'all' || c.seg === S.seg) && (!S.brand || c.brand === S.brand) && (!q || (c.name + ' ' + c.brand).toLowerCase().includes(q)));
    const by = { best: (a, b) => a.li - b.li, worst: (a, b) => b.li - a.li, sold: (a, b) => b.sold - a.sold, az: (a, b) => a.name.localeCompare(b.name) }[S.sort];
    return L.sort(by);
  }

  // 11-10 (Elijah: "make this look better, maybe bigger images or better layouts"): each model is a card like the /cars/ grid: a big
  // AI cutout, rank over the name, type + years, one plain line, the score on the right, and a small Compare chip in the corner.
  function row(c) {
    const on = S.open === c.id, picked = S.pick.includes(c.id), tier = c.li > 110 ? 'bad' : c.li < 90 ? 'good' : 'mid';
    return `<div class="xcd ${on ? 'open' : ''}" data-id="${c.id}">
      <button class="xcm" data-open="${c.id}" aria-expanded="${on}" title="${tip(c).replace(/"/g, '&quot;')}">
        <span class="xci">${c.img ? `<img src="${c.img}" alt="" width="1000" height="600" loading="lazy" decoding="async">` : ''}</span>
        <span class="xct"><small class="xck">#${c.rank}</small><b class="xcn">${c.name}${c.est ? '*' : ''}</b><small class="xcs">${c.segName} · ${c.years.replace('-', '–')}</small><span class="xcw ${tier}">${words(c)}</span></span>
        <span class="xcv ${tier}">${c.li}</span>
      </button>
      <label class="xcc${picked ? ' on' : ''}"><input type="checkbox" data-pick="${c.id}" ${picked ? 'checked' : ''} ${!picked && S.pick.length >= 2 ? 'disabled' : ''} aria-label="Compare the ${c.name}"><span>${picked ? '✓ Compare' : '+ Compare'}</span></label>
      ${on ? detail(c) : ''}</div>`;
  }

  function detail(c) {
    return `<div class="xd">
      <div><b>${c.per100k}</b><span>complaints per 100,000 sold (average car: ${c.avg})</span></div>
      <div><b>${c.n.toLocaleString()}</b><span>complaints counted, filed within 3 years of each model year</span></div>
      <div><b>${c.sold.toLocaleString()}${c.est ? '*' : ''}</b><span>sold in the U.S., model years ${c.years}</span></div>
      <div><b>${c.serious}%</b><span>of complaints involved a crash, fire or injury</span></div>
      <div><b>${c.worst || '—'}</b><span>its worst model year</span></div>
      <div class="xw"><span>What owners complained about</span><ul>${c.issues.map(([k, v]) => `<li><i style="width:${v}%"></i><span><b>${k}</b> ${v}%</span></li>`).join('')}</ul><small>One complaint can name several parts, so these can add up to more than 100%.</small></div>${c.yp ? `<div class="xl"><a class="btn ghost" href="/cars/${c.id}/">See every ${c.name} year and its problems →</a></div>` : ''}</div>`;
  }

  function render() {
    const L = list(), shown = S.all || S.q || S.brand ? L : L.slice(0, 15);
    $('xrows').innerHTML = shown.map(row).join('') || '<p class="note" style="padding:14px">No car matches. Try a model name like "RAV4" or "F-150".</p>';
    $('xcount').textContent = `${L.length} of ${CARS.length} models`;
    $('xmore').hidden = shown.length >= L.length;
    $('xmore').textContent = `Show all ${L.length}`;
    document.querySelectorAll('[data-seg]').forEach(b => b.setAttribute('aria-pressed', b.dataset.seg === S.seg));
    tray();
    try { sessionStorage.setItem('li-ex', JSON.stringify({ seg: S.seg, sort: S.sort })); } catch (e) {}
  }

  function tray() {
    const P = S.pick.map(id => CARS.find(c => c.id === id));
    $('tray').hidden = !P.length;
    if (!P.length) return;
    const lines = [['Lemon Index', c => `<b class="${c.li > 110 ? 'bad' : c.li < 90 ? 'good' : ''}">${c.li}</b> ${words(c)}`],
      ['Rank', c => `#${c.rank} of ${CARS.length}`], ['Per 100,000 sold', c => `${c.per100k} (average ${c.avg})`],
      ['Sold in the U.S.', c => `${c.sold.toLocaleString()}${c.est ? '*' : ''}`], ['Model years', c => c.years],
      ['Crash, fire or injury', c => `${c.serious}% of complaints`], ['Top complaint', issue], ['Worst model year', c => c.worst || '—']];
    $('tray').innerHTML = `<div class="tin"><div class="th"><b>${P.length === 1 ? 'Pick one more car to compare' : 'Side by side'}</b><button data-clear>Clear</button></div>
      <div class="tg" style="--n:${P.length}"><span></span>${P.map(c => `<b class="tn">${c.name}<button data-unpick="${c.id}" aria-label="Remove ${c.name}">×</button></b>`).join('')}
      ${lines.map(([l, f]) => `<span class="tl">${l}</span>${P.map(c => `<span>${f(c)}</span>`).join('')}`).join('')}</div></div>`;
  }

  // brand list
  const brands = [...new Set(CARS.map(c => c.brand))].sort();
  $('xbrand').innerHTML = '<option value="">All brands</option>' + brands.map(b => `<option>${b}</option>`).join('');
  $('xsort').value = S.sort;
  $('xq').addEventListener('input', e => { S.q = e.target.value; render(); });
  $('xbrand').addEventListener('change', e => { S.brand = e.target.value; render(); });
  $('xsort').addEventListener('change', e => { S.sort = e.target.value; render(); });
  $('xmore').addEventListener('click', () => { S.all = true; render(); });
  document.addEventListener('click', e => {
    const t = e.target.closest('[data-seg],[data-open],[data-unpick],[data-clear]'); if (!t) return;
    if (t.dataset.seg) { S.seg = t.dataset.seg; render(); }
    else if (t.dataset.open) { S.open = S.open === t.dataset.open ? null : t.dataset.open; render(); }
    else if (t.dataset.unpick) { S.pick = S.pick.filter(x => x !== t.dataset.unpick); render(); }
    else if ('clear' in t.dataset) { S.pick = []; render(); }
  });
  document.addEventListener('change', e => { const p = e.target.dataset && e.target.dataset.pick; if (!p) return;
    S.pick = e.target.checked ? [...S.pick, p].slice(-2) : S.pick.filter(x => x !== p); render(); });
  // hero search jumps into the explorer
  const hq = $('hq'); if (hq) hq.addEventListener('input', e => { S.q = e.target.value; $('xq').value = S.q; render(); });
  const hf = $('hform'); if (hf) hf.addEventListener('submit', e => { e.preventDefault(); $('explore').scrollIntoView({ behavior: 'smooth' }); });
  render();
})();
