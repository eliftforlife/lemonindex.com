// The car finder (10-29): the first thing on the home page and /cars/. Type a car ("2016 pilot", "civic 2022", "f-150")
// and pick a match, or pick brand, model and year from the lists. Data: <script id="pick"> = {brand: [[name, id, [years]], ...]}.
// 11-12 search v2 (6 usability testers: "crv", "2015 crv", "rouge", "rav4 hybrid", "P0700", "jeep grand cherokee transmission" and
// "safest car for teen under 10000" all said "No match"): one matcher for the finder, the search box in the menu (every page) and
// /compare/ (window.LQ). It folds case, hyphens, spaces and accents (crv = CR-V, huracan = Huracán), knows the names people use
// (chevy, vw, merc, beemer), forgives a typo (rouge -> Rogue), takes the year anywhere, sends engine codes to their code page,
// problem words to the problem page and questions ("safest", "first car", "under 10k", "most reliable suv") to the /best/ lists,
// and never ends on a dead "No match": the closest cars show instead.
(() => {
  const $ = id => document.getElementById(id);
  const fold = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const norm = s => fold(s).replace(/&/g, ' and ').replace(/['’]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  const words = s => norm(s).split(' ').filter(Boolean);
  // names people type that aren't the model's own words (run on the normalized text, whole words only)
  const SYN = [[/\bchevy\b|\bchev\b/g, 'chevrolet'], [/\bvw\b|\bvolks\b|\bvolkswagon\b/g, 'volkswagen'], [/\bmerc\b|\bmb\b|\bmercedes benz\b/g, 'mercedes'],
    [/\bbeemer\b|\bbimmer\b|\bbeamer\b/g, 'bmw'], [/\bcaddy\b|\bcaddilac\b/g, 'cadillac'], [/\blandrover\b/g, 'land rover'], [/\brangerover\b/g, 'range rover'],
    [/\bvette\b/g, 'corvette'], [/\bstang\b/g, 'mustang'], [/\bforerunner\b|\b4 runner\b|\bfour runner\b/g, '4runner'], [/\bgrand cherokee\b/g, 'grand cherokee'],
    [/\bmazda ?(\d)\b/g, 'mazda$1'], [/\bmiata\b/g, 'miata'], [/\bf ?(150|250|350)\b/g, 'f$1'], [/\bmodel ?([3sxy])\b/g, 'model $1']];
  const syn = s => SYN.reduce((t, [r, v]) => t.replace(r, v), s);
  // versions the pages don't split out (yet): matched without them, and the hint says the page covers every version
  const TRIM = new Set('hybrid phev plugin plug prime awd 4wd fwd rwd 4x4 2wd ex exl lx le se xle xse sport limited touring base premium platinum trd sr5 sv sl sel titanium xlt lariat ltz lt ls z71 crew cab v6 v8 turbo diesel manual automatic auto sedan coupe hatchback hatch wagon convertible'.split(' '));
  const STOP = new Set('the a an my for of and to in on is are was vs versus which what whats should i buy buying good bad used year years car cars most reliable reliability review reviews rating ratings score scores worth it any how do does with price prices cost'.split(' '));
  const osa = (a, b) => {   // edit distance with swapped letters counting as one edit ("rouge" -> "rogue" = 1)
    const d = []; for (let i = 0; i <= a.length; i++) d.push([i]); for (let j = 1; j <= b.length; j++) d[0][j] = j;
    for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) {
      let v = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) v = Math.min(v, d[i - 2][j - 2] + 1);
      d[i][j] = v;
    }
    return d[a.length][b.length];
  };
  // an entry's words: its name, brand and aliases; S = word runs that can be typed joined up ("cr v" -> "crv", "cx 5" -> "cx5")
  const prep = (n, b, al) => {
    const nt = words(syn(norm(n))), bt = words(b), at = words(syn(norm(al || ''))), mt = nt.filter(t => !bt.includes(t));
    return { T: [...new Set([...nt, ...bt, ...at])], S: [nt, at], C: [nt.join(''), mt.join(''), at.join('')].filter(x => x.length > 2), bw: bt };
  };
  const NUM = /\d/;
  const wcost = (x, e, fz) => {   // 0 exact word, 1 start of a word, 3-5 a typo, 9 no match
    let best = 9;
    for (const t of e.T) { if (t === x) return 0; if (t.startsWith(x)) best = Math.min(best, x.length > 1 || NUM.test(x) ? 1 : 2); }
    for (const s of e.S) for (let i = 0; i < s.length - 1; i++) {
      if (!x.startsWith(s[i])) continue; let acc = s[i];
      for (let j = i + 1; j < s.length && x.length > acc.length; j++) { acc += s[j]; if (acc === x) return 0; if (acc.startsWith(x)) best = Math.min(best, 1); if (!x.startsWith(acc)) break; }
    }
    if (best < 9 || !fz || x.length < 4 || NUM.test(x)) return best;
    const lim = x.length >= 7 ? 2 : 1;
    for (const t of e.T) {
      if (t.length < 3 || NUM.test(t) || Math.abs(t.length - x.length) > lim + (x.length >= 5 ? 9 : 0)) continue;
      let d = Math.abs(t.length - x.length) <= lim ? osa(x, t) : 9;
      if (x.length >= 5 && t.length > x.length) d = Math.min(d, osa(x, t.slice(0, x.length)) + 1);   // a typo in the start of a long word
      if (d <= lim) best = Math.min(best, 3 + d);
    }
    return best;
  };
  // every word has to match; a run typed joined up or split ("rav 4") still matches the whole name
  const score = (e, W, fz) => {
    let c = 0;
    for (const x of W) { const k = wcost(x, e, fz && fz.has(x)); if (k >= 9) { c = -1; break; } c += k; }
    if (c >= 0) return c;
    const q = W.join(''); if (q.length > 2 && e.C.some(s => s.startsWith(q))) return 2 * W.length;
    return -1;
  };
  // rank a list of entries for words W: exact and start-of-word matches first; typo matching only for words nothing else matched
  const rank = (W, L, pen) => {
    const fz = new Set(W.filter(x => !L.some(e => wcost(x, e) < 9)));
    const out = [];
    for (const e of L) { const s = score(e, W, fz); if (s >= 0) out.push([s + (pen ? pen(e) : 0), e]); }
    return out.sort((a, b) => a[0] - b[0] || (a[1].n || '').length - (b[1].n || '').length || String(a[1].n).localeCompare(String(b[1].n))).map(x => x[1]);
  };
  // /compare/ and any other box: LQ.pick("crv", ids, id => name) -> the ids that match, best first
  const cache = new WeakMap();
  window.LQ = {
    norm, words,
    pick(text, ids, nameOf) {
      let L = cache.get(ids); if (!L) { L = ids.map(i => Object.assign(prep(nameOf(i), '', ''), { id: i, n: nameOf(i) })); cache.set(ids, L); }
      let W = words(syn(norm(text))).filter(w => !STOP.has(w)); if (!W.length) return [];
      let r = rank(W, L); if (!r.length) { const W2 = W.filter(w => !TRIM.has(w)); if (W2.length && W2.length < W.length) r = rank(W2, L); }
      return r.map(e => e.id);
    }
  };

  // ---- the index: the small list in the page (#pick) at once, then the full one (assets/find.json, every page and card, with a
  // build check that nothing is missing) plus find-go.json (which engine codes, transmission pages and /best/ lists exist)
  const el = $('pick'), P = el ? JSON.parse(el.textContent) : {};
  const KIND = { sc: 'Supercar · engine, fuel cost and recalls', ev: 'Electric car · EV score and problems', perf: 'Performance car · specs, engines and problems', moto: 'Motorcycle · complaints and recalls', co: 'Owner complaints and recalls', eng: 'Engine · reliability by year' };
  const AK = { 'ford-f-series': 'f150 f 150 f250 f350 super duty', 'ram-pickup': '1500 2500 3500', 'chevrolet-silverado': '1500 2500 3500', 'gmc-sierra': '1500 2500 3500' };
  const mk = (n, b, u, t, ys, al, soon) => { const id = (u.match(/^\/cars\/([^/]+)\/$/) || [])[1] || ''; return Object.assign(prep(n, b, (al || '') + ' ' + (AK[id] || '') + (t === 'ev' ? ' ev electric' : '')), { n, b, u, t: t || '', ys: ys || [], id, soon: !!soon }); };
  let ALL = Object.entries(P).flatMap(([b, ms]) => ms.map(([n, id, ys, u, t]) => mk(n, b, u || '/cars/' + id + '/', t, ys, '', t === 'perf' && !u || (t === 'moto' && !u))));
  let GO = null, loading = null;
  const FU = (el && el.dataset.find) || '/assets/find.json';
  const load = () => loading || (loading = Promise.all([
    fetch(FU).then(r => r.ok ? r.json() : null).catch(() => null),
    fetch(FU.replace('find.json', 'find-go.json')).then(r => r.ok ? r.json() : null).catch(() => null)])
    .then(([F, G]) => { if (F && F.length) ALL = F.map(r => mk(...r)); GO = G || {}; boxes.forEach(b => b.refresh()); }));

  // ---- what the words ask for besides a car
  const BEST = (u, b, s) => ({ u, b, s: s || 'Ranked list', kind: 'list' });
  const has = u => !GO || !GO.best || GO.best.includes(u);
  const INTENT = [
    [/\b(teen(ager)?s?|first (car|time driver)s?|new drivers?|student drivers?|young drivers?|(for )?(my )?(daughter|son|kid)s?|16 ?(year|yr) ?olds?)\b/, () => BEST('/best/safest-cars-for-teens/', 'Safest used cars for teens', 'Crash-test stars + fewest complaints, by model year')],
    [/\b(safe(st|ty)?|crash (test|rating)s?)\b/, () => BEST('/best/safest-cars-for-teens/', 'Safest used cars, by model year', 'NHTSA crash-test stars + fewest complaints')],
    [/\b(most |least )?(reliable|reliability|dependable|best|top( \d+)?|good|great|recommended)\b.*\b(suv|suvs|crossovers?|trucks?|pickups?|minivans?|vans?|sedans?|cars|car|vehicles?)\b|\b(suv|suvs|crossovers?|trucks?|pickups?|minivans?|sedans?)\b.*\b(reliable|reliability|best|top)\b/, m => {
      const t = m[0]; const s = /suv|crossover/.test(t) ? 'suvs' : /truck|pickup/.test(t) ? 'trucks' : /van/.test(t) ? 'minivans' : 'cars';
      return /least/.test(t) ? BEST('/rankings/', 'Every car, best to worst', 'Rankings') : BEST(`/best/most-reliable-${s}/`, `Most reliable ${s === 'suvs' ? 'SUVs' : s}`, 'Ranked by owner complaints per car sold'); }],
    [/^\s*(the )?(most reliable|reliable|dependable)( cars?| vehicles?)?\s*$/, () => BEST('/best/most-reliable-cars/', 'Most reliable cars', 'Ranked by owner complaints per car sold')],
    [/\b(mpg|gas mileage|fuel (economy|efficient)|good on gas|best mileage)\b/, (m, s) => /\bsuv/.test(s) ? BEST('/best/suvs-gas-mileage/', 'SUVs with the best gas mileage') : BEST('/best-gas-mileage/', 'Best gas mileage, with complaint scores')],
    [/\b(worst|lemons?|avoid|least reliable|unreliable|rankings?|ranked)\b/, () => BEST('/rankings/', 'Every car, best to worst', 'Rankings')],
    [/\b(check engine( light)?|engine light|cel|obd ?2?|engine codes?|error codes?|codes?)\b/, () => BEST('/check-engine-light/', 'Engine code lookup', 'What a check engine light code means')],
    [/\b(vin|recall check|check recalls?)\b/, () => BEST('/vin/', 'VIN check', 'Decode a VIN, then see its recalls')],
    [/\b(compare|comparison)\b/, () => BEST('/compare/', 'Compare cars side by side', 'Compare')],
    [/\b(press|media|journalists?|reporters?)\b/, () => BEST('/press/', 'Press and media', 'Key numbers, how to cite, contact')],
    [/\b(about|who runs|who made)\b/, () => BEST('/about/', 'About the Lemon Index', 'Who runs it and where the data comes from')],
    [/\b(method|methodology|how it works|how do you score)\b/, () => BEST('/method/', 'How the index works', 'Method')],
    [/\b(download|csv|dataset|raw data)\b/, () => BEST('/data/', 'Free data downloads', 'CSV files, free with credit')],
    [/\b(brands?|makes?)\b/, () => BEST('/brands/', 'Every brand, ranked', 'Brands')],
    [/\b(electric|evs?)\b/, () => BEST('/electric/', 'The most reliable EVs, ranked', 'Electric')],
    [/\b(contact|email)\b/, () => BEST('/contact/', 'Contact', '')]
  ];
  // budgets: "under 10000", "under 10k", "$10k", "10 grand" -> the smallest list that fits (5K, 10K, 15K, 20K)
  const BUDGET = /\$ ?(\d[\d,.]*) ?(k|grand|thousand)?(?! ?(?:miles|mi)\b)|\b(?:under|below|less than|max|budget|up to|around|about)\s*(\d[\d,.]*) ?(k|grand|thousand)?\b(?! ?(?:miles|mi)\b)|\b(\d[\d.]*) ?(k|grand|thousand)\b(?! ?(?:miles|mi)\b)/;
  const budget = s => { const m = s.match(BUDGET); if (!m) return null;
    let v = parseFloat((m[1] || m[3] || m[5]).replace(/,/g, '')); const k = m[2] || m[4] || m[6]; if (k || v <= 100) v *= 1000;
    if (!(v >= 1000) || (!m[1] && !k && v >= 1990 && v <= 2030 && !/\b(under|below|less than|budget|max|up to)\b/.test(m[0]))) return null;
    const cap = [5000, 10000, 15000, 20000].find(c => v <= c) || 20000;
    return { m: m[0], item: BEST(`/best/used-cars-under-${cap}/`, `Best used cars under $${cap.toLocaleString('en-US')}`, 'What buyer guides pick, with complaint scores, by year') }; };
  // problem words: the transmission page where the model has one, else the year page's problems (or recalls) tab
  const PROB = /\b(transmissions?|tranny|cvt|gearbox|shifting|hard shifts?|slipping)\b|\b(problems?|issues?|complaints?|defects?|engine|brakes?|electrical|airbags?|steering|suspension|ac|air conditioning|battery|stalling|stalls|rust|leaks?|oil)\b|\b(recalls?)\b/;
  const CODE = /\b([pbcu]) ?-?([0-3][0-9a-f]{3})\b/;

  function search(raw) {
    let s = fold(raw).replace(/([a-z])((?:19|20)\d{2})\b/g, '$1 $2');
    const cm = s.match(CODE), lists = [];
    let code = null;
    if (cm) {   // a code page where we have one (435 codes), else the lookup, which explains any code
      const c = (cm[1] + cm[2]).toUpperCase(), pg = !GO || (GO.codes || []).includes(c.toLowerCase());
      code = { u: pg ? `/check-engine-light/${c.toLowerCase()}/` : `/check-engine-light/?code=${c}`, b: `${c}: what this engine code means`, s: 'Check engine light code · how serious, common causes and fixes', kind: 'code' };
      s = s.replace(cm[0], ' ');
    }
    const bd = budget(s); if (bd) s = s.replace(bd.m, ' ');
    let t = syn(norm(s));
    for (const [re, f] of INTENT) { const m = t.match(re); if (m) { const it = f(m, t); if (has(it.u) && !lists.some(x => x.u === it.u)) lists.push(it); t = t.replace(m[0], ' '); } }
    if (bd && has(bd.item.u)) lists.push(bd.item);
    let prob = null, pm;   // every problem word goes; the transmission wins, then recalls
    while ((pm = t.match(PROB))) { const k = pm[1] ? 'transmission' : pm[3] ? 'recalls' : 'problems'; if (!prob || k === 'transmission' || (k === 'recalls' && prob === 'problems')) prob = k; t = t.replace(pm[0], ' '); }
    const ym = t.match(/\b(19|20)\d{2}\b/), y = ym ? +ym[0] : 0; if (ym) t = t.replace(ym[0], ' ');
    let W = words(t).filter(w => !STOP.has(w));
    return { code, lists, prob, y, W, eng: /\bengines?\b/.test(fold(raw)) };
  }
  const KP = { '': 0, co: .3, perf: .4, ev: .4, sc: .6, nd: 0, moto: 2.5, eng: 3 };
  function find(raw) {
    const q = search(raw), { y } = q; let W = q.W, notes = '', close = false;
    // a year alone lists the brands that have it; year + brand lists that brand's models (11-02, Elijah types the year first)
    if (!W.length && y && !q.code && !q.lists.length && !q.prob) {
      const br = [...new Set(ALL.filter(c => !c.t && c.ys.includes(y)).map(c => c.b))].sort();
      return { brands: br.map(b => ({ brand: b, y })) };
    }
    let hits = [];
    if (W.length) {
      const pen = c => (c.soon ? 100 : 0) + (KP[c.t] === undefined ? 1 : (c.t === 'eng' && q.eng ? 0 : KP[c.t])) + (y && !c.t && !c.ys.includes(y) ? 1 : 0) - (W.some(w => c.bw.includes(w)) ? .5 : 0);
      hits = rank(W, ALL, pen);
      if (!hits.some(c => !c.soon && c.t !== 'eng')) {   // "rav4 hybrid": the RAV4 page covers the hybrid, and the line says so
        const W2 = W.filter(w => !TRIM.has(w));
        if (W2.length && W2.length < W.length) { const h2 = rank(W2, ALL, pen); if (h2.length) { hits = [...h2, ...hits.filter(c => !h2.includes(c))]; notes = W.filter(w => TRIM.has(w)).join(' '); } }
      }
      if (!hits.length) {   // closest: the cars that match the most words
        let bestN = 0; const sc = [];
        for (const c of ALL) { let n = 0, k = 0; for (const x of W) { const v = wcost(x, c, true); if (v < 9) { n++; k += v; } } if (n) { sc.push([n, k + pen(c), c]); bestN = Math.max(bestN, n); } }
        hits = sc.filter(r => r[0] === bestN).sort((a, b) => a[1] - b[1]).map(r => r[2]); close = true;
      }
    }
    const top = hits.filter(c => !c.soon);
    const out = [];
    if (q.code) out.push(q.code);
    // problem words + a car: its problem page first
    const car = top.find(c => !c.t && c.ys.length) || null;
    if (q.prob && car && !close) {
      const old = car.ys.filter(v => v <= 2024), yy = y && car.ys.includes(y) ? y : old.length ? Math.max(...old) : car.ys[car.ys.length - 1];   // the newest year with a full year of complaints
      if (q.prob === 'transmission' && GO && (GO.tr || []).includes(car.id)) out.push({ u: car.u + 'transmission/', b: `${car.n} transmission problems by year`, s: 'Every year, what owners describe, transmission recalls', kind: 'go' });
      else out.push({ u: `${car.u}${yy}/#${q.prob === 'recalls' ? 'recalls' : 'problems'}`, b: `${yy} ${car.n}: ${q.prob === 'recalls' ? 'recalls' : 'what owners complain about'}`, s: q.prob === 'transmission' ? 'Problems tab · transmission and every other area' : 'Problems, recalls and owner complaints', kind: 'go' });
    }
    const n = y ? 12 : 8;
    const carItems = hits.slice(0, n).map(c => {
      const yy = y && !c.t && !c.soon && c.ys.includes(y) ? y : 0, miss = y && !c.t && !c.soon && !c.ys.includes(y) ? y : 0;
      const u = c.soon ? '' : yy ? c.u + yy + '/' : c.u;
      const lab = c.soon ? (c.t === 'nd' ? 'No data yet' : 'Coming soon') + ({ perf: ' · performance car', sc: ' · supercar', moto: ' · motorcycle', eng: ' · engine' }[c.t] || '')
        : c.t ? KIND[c.t] : yy ? 'problems and owner complaints' : miss ? `no ${miss} in our data · every year ${c.ys[0]}-${c.ys.at(-1)}` : c.ys.length ? `every year ${c.ys[0]}-${c.ys.at(-1)}` : 'problems and owner complaints';
      return { u, b: (yy ? yy + ' ' : '') + c.n, s: (close ? 'Closest match · ' : '') + lab + (notes && !c.t ? ` · covers every version, ${notes} included` : ''), soon: c.soon, kind: close ? 'close' : 'car' };
    });
    // the question lists go first when the words were a question, after the cars when a car was named too
    if (!W.length || close) out.push(...q.lists, ...carItems); else out.push(...carItems, ...q.lists);
    if (!out.length || out.every(x => x.kind === 'close')) {
      const pop = ['/cars/honda-cr-v/', '/cars/toyota-rav4/', '/cars/honda-civic/', '/cars/ford-f-series/', '/cars/toyota-camry/'];
      if (!out.length) out.push(...ALL.filter(c => pop.includes(c.u) && !c.t).map(c => ({ u: c.u, b: c.n, s: 'Popular · every year', kind: 'close' })));
      out.push(BEST('/best/', 'Best cars, by the data', 'Every ranked list'));
      return { items: out, hint: `No exact match for “${raw.trim()}”. Closest:` };
    }
    return { items: out };
  }

  window.LQ.find = find; window.LQ.load = load;   // for other boxes, and for testing the search cases in a console

  // ---- a search box: the finder on / and /cars/ (#fq) and the one in the menu (#ghq); same list, keys and Enter
  const boxes = [];
  function attach(q, sug, say) {
    let res = { items: [] }, cur = -1;
    const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const show = () => {
      if (res.brands) {
        sug.hidden = !res.brands.length; const y = res.brands[0] && res.brands[0].y;
        sug.innerHTML = `<p class="fhint">${y}: pick the brand</p><div class="fbr">` + res.brands.map((h, i) => `<button type="button" data-b="${esc(h.brand)}" class="${i === cur ? 'on' : ''}">${esc(h.brand)}</button>`).join('') + '</div>';
        sug.querySelectorAll('[data-b]').forEach(x => x.onclick = () => { q.value = `${y} ${x.dataset.b} `; q.focus(); run(); });
        return;
      }
      const it = res.items; sug.hidden = !it.length && !res.hint;
      sug.innerHTML = (res.hint ? `<p class="fhint">${esc(res.hint)}</p>` : '') + it.map((h, i) => {
        const cl = (i === cur ? 'on' : '') + (h.u ? '' : ' fsoon') + (h.kind === 'list' || h.kind === 'code' || h.kind === 'go' ? ' fgo' : '');
        return `<a role="option" ${h.u ? `href="${esc(h.u)}"` : 'aria-disabled="true"'} class="${cl.trim()}"><b>${esc(h.b)}</b><small>${esc(h.s)}</small></a>`; }).join('');
    };
    const run = () => { const v = q.value.trim(); res = v ? find(q.value) : { items: [] }; cur = res.brands ? -1 : (res.items.length && !res.hint ? 0 : -1); show(); say(''); };
    const go = () => {
      const v = q.value.trim(); if (!v) return false;
      res = find(q.value);
      if (res.brands) { say(`Add the brand and model, e.g. '${res.brands[0] ? res.brands[0].y : 2016} Honda Civic'.`); show(); return false; }
      const h = res.items[cur >= 0 && cur < res.items.length ? cur : 0];
      if (res.hint && cur < 0) { show(); say('Pick one of the closest matches.'); return false; }
      if (!h) return false;
      if (!h.u) { say(`The ${h.b} is coming soon.`); return false; }
      location.href = h.u; return true;
    };
    q.addEventListener('input', run);
    ['focus', 'pointerdown', 'input'].forEach(ev => q.addEventListener(ev, load, { once: true }));
    q.addEventListener('keydown', e => {
      const n = res.brands ? res.brands.length : res.items.length;
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (n) { cur = (cur + (e.key === 'ArrowDown' ? 1 : -1) + n) % n; show(); } }
      else if (e.key === 'Enter') {
        e.preventDefault();
        if (res.brands && res.brands[cur]) { q.value = `${res.brands[cur].y} ${res.brands[cur].brand} `; run(); }
        else if (q.value.trim()) (loading && !GO ? loading.then(go) : go());
      }
      else if (e.key === 'Escape' && !sug.hidden) { e.stopPropagation(); sug.hidden = true; }
    });
    document.addEventListener('click', e => { if (!q.parentNode.contains(e.target)) sug.hidden = true; });
    q.addEventListener('focus', () => { if (res.items.length || res.brands) sug.hidden = false; });
    const b = { q, go, refresh: () => { if (q.value.trim()) run(); } }; boxes.push(b); return b;
  }

  // the search box in the menu (every page, built by build.py's gh_header)
  const mq = $('ghq');
  if (mq) {
    const mf = mq.form, msay = document.createElement('p'); msay.className = 'fmiss gh-qm'; msay.setAttribute('role', 'status'); msay.setAttribute('aria-live', 'polite');
    mf.appendChild(msay);
    attach(mq, $('ghqs'), t => { msay.textContent = t || ''; });
    mf.addEventListener('submit', e => { e.preventDefault(); load().then(() => { const b = boxes.find(x => x.q === mq); b && b.go(); }); });
  }

  if (!el) return;
  const lookForm = $('look'); if (lookForm) lookForm.addEventListener('submit', e => e.preventDefault());   // was an inline onsubmit (blocked by the CSP)
  // 11-11 (Elijah: "the buttons underneath should come in when you click the look-up box"): Brand / Model / Year / Show problems stay
  // folded (inert, not tabbable) until the box is focused, tapped or typed in; then they slide in and stay. Without JS they simply show.
  const box = $('fq'), form = $('look');
  if (box && form) {
    const open = () => { if (!form.classList.contains('fo-closed')) return; form.classList.remove('fo-closed'); form.inert = false; form.removeAttribute('aria-hidden'); box.setAttribute('aria-expanded', 'true'); };
    form.classList.add('fo-closed'); form.inert = true; form.setAttribute('aria-hidden', 'true');
    box.setAttribute('aria-controls', 'look'); box.setAttribute('aria-expanded', 'false');
    ['focus', 'pointerdown', 'input'].forEach(ev => box.addEventListener(ev, open));
  }
  const miss = t => { const m = document.querySelector('.finder .fmiss'); if (m) m.textContent = t; };
  const fb = box && $('fsug') ? attach(box, $('fsug'), miss) : null;
  // ?q= (the menu's search form without JS, or a shared link) fills the finder
  const pq = new URLSearchParams(location.search).get('q');
  if (fb && pq) { box.value = pq; load().then(() => { box.dispatchEvent(new Event('input')); }); }

  // or pick from the lists
  // 11-10 (Elijah: "the Show problems button doesn't work"): the button now follows the typed search first (its top match), then the
  // lists; picking a year no longer jumps away on its own, so the button is the one way to go. No target -> a short hint, never a dead button.
  const b = $('lb'), m = $('lm'), y = $('ly'), g = $('lgo'); if (!b) return;
  const tip = document.createElement('p'); tip.className = 'fmiss'; tip.setAttribute('role', 'status'); tip.setAttribute('aria-live', 'polite');
  (lookForm || g).after(tip);
  const say = t => { tip.textContent = t || ''; };
  const opt = (s, l, ph) => { s.innerHTML = `<option value="">${ph}</option>` + l.map(([v, t]) => `<option value="${v}">${t}</option>`).join(''); s.disabled = !l.length; };
  opt(b, Object.keys(P).map(k => [k, k]), 'Brand');
  b.onchange = () => { opt(m, (P[b.value] || []).map(([n, i]) => [i, n]), 'Model'); opt(y, [], 'Year'); say(''); };
  m.onchange = () => { const r = (P[b.value] || []).find(x => x[1] === m.value); opt(y, r && !r[4] ? r[2].slice().reverse().map(v => [v, v]) : [], 'Year (optional)'); say(''); };
  y.onchange = () => say('');
  g.disabled = false;
  g.onclick = () => {
    if (box && box.value.trim()) { if (!fb.go()) box.focus(); return; }
    if (m.value) { const r = (P[b.value] || []).find(x => x[1] === m.value); if (!r) return; const u = r[3] || (r[4] === 'perf' || r[4] === 'moto' ? '' : '/cars/' + r[1] + '/');
      if (!u) { say(`The ${r[0]} is coming soon.`); return; } location.href = y.value && !r[4] ? u + y.value + '/' : u; return; }
    say(b.value ? 'Pick a model, then press Show problems.' : 'Type a car above, or pick a brand and model.');
  };
})();
