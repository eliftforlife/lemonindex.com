// The car finder (10-29): the first thing on the home page and /cars/. Type a car ("2016 pilot", "civic 2022", "f-150")
// and pick a match, or pick brand, model and year from the lists. Data: <script id="pick"> = {brand: [[name, id, [years]], ...]}.
// 11-12 search v2 (6 usability testers: "crv", "2015 crv", "rouge", "rav4 hybrid", "P0700", "jeep grand cherokee transmission" and
// "safest car for teen under 10000" all said "No match"): one matcher for the finder, the search box in the menu (every page) and
// /compare/ (window.LQ). It folds case, hyphens, spaces and accents (crv = CR-V, huracan = Huracán), knows the names people use
// (chevy, vw, merc, beemer), forgives a typo (rouge -> Rogue), takes the year anywhere, sends engine codes to their code page,
// problem words to the problem page and questions ("safest", "first car", "under 10k", "most reliable suv") to the /best/ lists,
// and never ends on a dead "No match": the closest cars show instead.
// 11-12 round 2 (6 more testers): "rav4 vs crv", "civic or corolla" and "civic corolla" put "Compare A vs B →" first (Enter opens it);
// Enter opens the top match everywhere (a coming-soon one opens its vote sheet); engine sizes and engine/symptom words ("2.7", "ecoboost",
// "oil leak", "cold start") no longer break a model + year match; truck and trim words (cummins, duramax, powerstroke, f250, 2500hd,
// m340i) come from find_index.py's aliases.
// 11-13 navigation test (N1): brand pages come first for a brand name ("chevy", "vw", "benz", "toyota"), a hub word ("engines") offers its
// hub, at most 1 coming-soon match shows (last) and at most 1 match-up page unless the search says "vs", "<car> engine" never defaults
// to a 2023+ year, and the header's own search (#ghd, 1024px+) and its magnifier (.lxs-btn) use the same matcher.
(() => {
  const $ = id => document.getElementById(id);
  // 11-12 round 2 (Mitch: "the grey Heavy Duty row in search does nothing"): a coming-soon match opens the cards' vote sheet (soonvote.js)
  const vote = (name, back) => {
    const open = () => window.LSV && window.LSV.open(name, back);
    if (window.LSV) return open();
    const s = document.createElement('script'); s.src = '/assets/soonvote.js?v=2'; s.onload = open; document.head.appendChild(s);
  };
  if (document.head) { const st = document.createElement('style'); st.textContent = '.fsug a.fsv{cursor:pointer}.fsug a.fsv:hover{background:#f2f2f4}'; document.head.appendChild(st); }
  const fold = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const norm = s => fold(s).replace(/&/g, ' and ').replace(/['’]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  const words = s => norm(s).split(' ').filter(Boolean);
  // names people type that aren't the model's own words (run on the normalized text, whole words only)
  const SYN = [[/\bchevy\b|\bchev\b/g, 'chevrolet'], [/\bvw\b|\bvolks\b|\bvolkswagon\b/g, 'volkswagen'], [/\bmerc\b|\bmb\b|\bmercedes benz\b|\bbenz\b/g, 'mercedes'],
    [/\bbeemer\b|\bbimmer\b|\bbeamer\b/g, 'bmw'], [/\bcaddy\b|\bcaddilac\b/g, 'cadillac'], [/\blandrover\b/g, 'land rover'], [/\brangerover\b/g, 'range rover'],
    [/\bvette\b/g, 'corvette'], [/\bstang\b/g, 'mustang'], [/\bforerunner\b|\b4 runner\b|\bfour runner\b/g, '4runner'], [/\bgrand cherokee\b/g, 'grand cherokee'],
    [/\bmazda ?(\d)\b/g, 'mazda$1'], [/\bmiata\b/g, 'miata'], [/\bf ?(150|250|350|450)\b/g, 'f$1'], [/\bmodel ?([3sxy])\b/g, 'model $1'],
    [/\bpower ?stroke\b/g, 'powerstroke'], [/\b([23]500) ?hd\b/g, '$1hd']];
  const syn = s => SYN.reduce((t, [r, v]) => t.replace(r, v), s);
  // versions the pages don't split out (yet): matched without them, and the hint says the page covers every version
  const TRIM = new Set('hybrid phev plugin plug prime awd 4wd fwd rwd 4x4 2wd ex exl lx le se xle xse sport limited touring base premium platinum trd sr5 sv sl sel titanium xlt lariat ltz lt ls z71 crew cab v6 v8 turbo diesel manual automatic auto sedan coupe hatchback hatch wagon convertible'.split(' '));
  const STOP = new Set('the a an my for of and to in on is are was vs versus which what whats should i buy buying good bad used year years car cars most reliable reliability review reviews rating ratings score scores worth it any how do does with price prices cost better worse or km kms kilometers kilometres miles mi'.split(' '));
  // engine words: dropped like TRIM when the full words match no car, so "2016 f150 2.7 ecoboost" still opens the 2016 F-150 page
  const SOFT = new Set('ecoboost coyote hemi ecotec vortec triton modular boxer pentastar skyactiv vtec tdi tsi tfsi gdi gtdi dohc sohc liter litre liters litres cyl cylinder cylinders i4 i6 v10 twin supercharged supercharger motor'.split(' '));
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
    return { T: [...new Set([...nt, ...bt, ...at])], S: [nt, at], C: [nt.join(''), mt.join(''), at.join('')].filter(x => x.length > 2), bw: bt, M: mt.join('') };
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
  const KIND = { sc: 'Supercar · engine, fuel cost and recalls', ev: 'Electric car · EV score and problems', perf: 'Performance car · specs, engines and problems', moto: 'Motorcycle · complaints and recalls', co: 'Owner complaints and recalls', eng: 'Engine · reliability by year', br: 'Brand · every model, ranked' };
  const AK = { 'ford-f-series': 'f150 f 150', 'ram-pickup': '1500', 'chevrolet-silverado': '1500', 'gmc-sierra': '1500' };   // 11-12 round 2: 2500/3500/f250 go to the HD cards
  const mk = (n, b, u, t, ys, al, soon, pr) => { const id = (u.match(/^\/cars\/([^/]+)\/$/) || [])[1] || ''; return Object.assign(prep(n, b, (al || '') + ' ' + (AK[id] || '') + (t === 'ev' ? ' ev electric' : '')), { n, b, u, t: t || '', ys: ys || [], id, soon: !!soon, pr: pr || 0 }); };   // pr: find.json's optional search priority (11-12 r2: Silverado HD before Sierra HD)
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
    [/^\s*(all |every |car )?engines?( reliability| ranked| list)?\s*$/, () => BEST('/engines/', 'Every engine, ranked', 'Engines · reliability by year')],
    [/\b(brands?|makes?)\b/, () => BEST('/brands/', 'Every brand, ranked', 'Brands')],
    [/\b(electric|evs?)\b/, () => BEST('/electric/', 'The most reliable EVs, ranked', 'Electric')],
    [/\b(contact|email)\b/, () => BEST('/contact/', 'Contact', '')]
  ];
  // budgets: "under 10000", "under 10k", "$10k", "10 grand" -> the smallest list that fits (5K, 10K, 15K, 20K)
  const BUDGET = /\$ ?(\d[\d,.]*) ?(k|grand|thousand)?(?! ?(?:miles|mi|km|kms)\b)|\b(?:under|below|less than|max|budget|up to|around|about)\s*(\d[\d,.]*) ?(k|grand|thousand)?\b(?! ?(?:miles|mi|km|kms)\b)|\b(\d[\d.]*) ?(k|grand|thousand)\b(?! ?(?:miles|mi|km|kms)\b)/;
  const budget = s => { const m = s.match(BUDGET); if (!m) return null;
    let v = parseFloat((m[1] || m[3] || m[5]).replace(/,/g, '')); const k = m[2] || m[4] || m[6]; if (k || v <= 100) v *= 1000;
    if (!(v >= 1000) || (!m[1] && !k && v >= 1990 && v <= 2030 && !/\b(under|below|less than|budget|max|up to)\b/.test(m[0]))) return null;
    const cap = [5000, 10000, 15000, 20000].find(c => v <= c) || 20000;
    return { m: m[0], item: BEST(`/best/used-cars-under-${cap}/`, `Best used cars under $${cap.toLocaleString('en-US')}`, 'What buyer guides pick, with complaint scores, by year') }; };
  // problem words: the transmission page where the model has one, else the year page's problems (or recalls) tab
  // 11-12 round 2 (Ryan: "f150 2.7 oil leak", "rough cold start f150"): symptom words count as problem words too
  const PROB = /\b(transmissions?|tranny|cvt|gearbox|shifting|hard shifts?|slipping)\b|\b(problems?|issues?|complaints?|defects?|engine|brakes?|electrical|airbags?|steering|suspension|ac|air conditioning|battery|stalling|stalls|rust|leak(?:s|ing)?|oil|cold starts?|rough (?:idle|idling|start|starts|running)|rough|idle|rattles?|rattling|start ?up|misfires?|misfiring|knock(?:s|ing)?|tick(?:s|ing)?|noises?|smoke|smoking|overheat(?:s|ing)?|vibrat\w*|shudder\w*|whine|hesitat\w*|timing chains?|cam phasers?|phasers?|water pumps?|head gaskets?|coolant|won t start|no start|hard start\w*)\b|\b(recalls?)\b/;
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
    s = s.replace(/\b\d[\d,.]*\s*(?:k\s*)?(?:km|kms|kilomet\w*|miles|mi)\b/g, ' ');   // "120,000 km", "75k miles": a mileage, not a price
    const sz = [];   // engine sizes: "2.7" -> "27" (an engine page's "2 7" still matches it), dropped like the engine words when no car matches
    s = s.replace(/\b(\d)\.(\d)\s*(?:l|liters?|litres?|t)?\b/g, (m, a, b) => { sz.push(a + '.' + b); return ` ${a}${b} `; });
    const bd = budget(s); if (bd) s = s.replace(bd.m, ' ');
    let t = syn(norm(s));
    for (const [re, f] of INTENT) { const m = t.match(re); if (m) { const it = f(m, t); if (has(it.u) && !lists.some(x => x.u === it.u)) lists.push(it); t = t.replace(m[0], ' '); } }
    if (bd && has(bd.item.u)) lists.push(bd.item);
    let prob = null, pm, pe = true;   // every problem word goes; the transmission wins, then recalls. pe: the only one was "engine(s)"
    while ((pm = t.match(PROB))) { const k = pm[1] ? 'transmission' : pm[3] ? 'recalls' : 'problems'; if (!prob || k === 'transmission' || (k === 'recalls' && prob === 'problems')) prob = k; if (!/^engines?$/.test(pm[0].trim())) pe = false; t = t.replace(pm[0], ' '); }
    const ym = t.match(/\b(19|20)\d{2}\b/), y = ym ? +ym[0] : 0; if (ym) t = t.replace(ym[0], ' ');
    let W = words(t).filter(w => !STOP.has(w));
    return { code, lists, prob, pe: !!prob && pe, y, W, sz: sz.map(x => x.replace('.', '')), szd: sz, eng: /\bengines?\b/.test(fold(raw)) };
  }
  const KP = { '': 0, co: .3, perf: .4, ev: .4, sc: .6, nd: 0, moto: 2.5, eng: 3, br: -1.5 };   // br: a brand page beats that brand's models
  // a prebuilt compare page ranks after the car page itself
  const penFor = (W, y, eng) => c => (c.soon ? 100 : 0) + (c.pr || 0) + (KP[c.t] === undefined ? 1 : (c.t === 'eng' && eng ? -1 : KP[c.t])) + (y && !c.t && !c.ys.includes(y) ? 1 : 0) - (W.some(w => c.bw.includes(w)) ? .5 : 0) + (c.u.startsWith('/compare/') ? .5 : 0);
  const isCar = c => !c.soon && c.t !== 'eng' && c.t !== 'br' && !!c.u && !c.u.startsWith('/compare/');
  const dropW = (q, W) => W.filter(w => !TRIM.has(w) && !SOFT.has(w) && !q.sz.includes(w));   // versions, engine words and sizes
  // ---- 11-12 round 2 (Jake, Carlos, Liam: "civic vs corolla", "rav4 vs crv", "elantra vs civic"): one side of a comparison = its best car
  // page (never a brand alone, an engine, a version word or a coming-soon card)
  function resolve(W, y, q) {
    if (!W.some(w => /[a-z]/.test(w) && !TRIM.has(w) && !SOFT.has(w))) return null;
    const pen = penFor(W, y, false);
    let h = rank(W, ALL, pen).filter(isCar);
    if (!h.length) { const W2 = dropW(q, W); if (W2.length && W2.length < W.length) h = rank(W2, ALL, pen).filter(isCar); }
    const c = h[0];
    return c && W.some(w => (/[a-z]/.test(w) || w.length >= 3) && !c.bw.includes(w)) ? c : null;   // "ram 2500": the 2500 is more than the brand
  }
  // "Compare A vs B →": the prebuilt match-up page when there's one and no year was typed, else the compare tool with those cars (any pair)
  function compareItem(S) {
    if (!GO || !GO.cmp) return null;
    const ids = S.map(s => GO.cmp[s.c.u]);
    if (ids.some(i => !i) || new Set(ids).size < ids.length) return null;
    const y0 = (S.find(s => s.y) || {}).y || 0, ys = S.map(s => s.y || y0);
    let u = !y0 && S.length === 2 && GO.cpg ? GO.cpg[S[0].c.u + ' ' + S[1].c.u] || GO.cpg[S[1].c.u + ' ' + S[0].c.u] || '' : '';
    const pre = !!u;
    if (!u) u = '/compare/?cars=' + ids.map((i, k) => ys[k] ? `${i}-${ys[k]}` : i).join(',');
    return { u, b: `Compare ${S.map(s => s.c.n).join(' vs ')} →`, kind: 'go',
             s: (pre ? 'Every year side by side' : 'Side by side' + (y0 ? `, ${[...new Set(ys)].join(' vs ')} models` : '')) + ': scores, complaints, recalls and mpg' };
  }
  const sideItem = s => {
    const yy = s.y && !s.c.t && s.c.ys.includes(s.y) ? s.y : 0;
    return { u: yy ? s.c.u + yy + '/' : s.c.u, b: (yy ? yy + ' ' : '') + s.c.n, kind: 'car',
             s: s.c.t ? KIND[s.c.t] : yy ? 'problems and owner complaints' : s.c.ys.length ? `every year ${s.c.ys[0]}-${s.c.ys.at(-1)}` : 'problems and owner complaints' };
  };
  const VS = /\s+(?:vs\.?|v\.?|versus|or|and|&|compared (?:to|with)|against)\s+/;
  function versus(raw) {
    const parts = fold(raw).split(VS).map(x => x.trim()).filter(Boolean);
    if (parts.length < 2 || parts.length > 4) return null;
    const S = [];
    for (const p of parts) { const q = search(p); if (q.code || q.lists.length) return null; const c = resolve(q.W, q.y, q); if (!c) return null; S.push({ c, y: q.y }); }
    const y0 = (S.find(s => s.y) || {}).y || 0; S.forEach(s => { s.y = s.y || y0; });   // "2019 rav4 vs crv": both 2019
    const it = compareItem(S);
    return it ? { items: [it, ...S.map(sideItem)], strong: true } : null;
  }
  function find(raw) {
    const vs = versus(raw); if (vs) return vs;
    const q = search(raw), { y } = q; let W = q.W, notes = '', close = false, pair = null;
    // a year alone lists the brands that have it; year + brand lists that brand's models (11-02, Elijah types the year first)
    if (!W.length && y && !q.code && !q.lists.length && !q.prob) {
      const br = [...new Set(ALL.filter(c => !c.t && c.ys.includes(y)).map(c => c.b))].sort();
      return { brands: br.map(b => ({ brand: b, y })) };
    }
    let hits = [], ex = [], strong = false;
    if (W.length) {
      const pen = penFor(W, y, q.eng);
      hits = rank(W, ALL, pen);
      // 11-12 round 2 (fix C): a size + engine name with no year ("6.0 powerstroke") opens the live engine page that matches every word
      const engHit = !y && q.sz.length && hits.some(c => c.t === 'eng' && !c.soon);
      if (!hits.some(isCar) && !engHit) {   // "rav4 hybrid": the RAV4 page covers the hybrid, and the line says so
        // 11-12 round 2 (Ryan: "2016 f150 2.7 ecoboost" showed BMW engines): engine sizes and engine words drop the same way, so the car
        // ranks first and the engine pages that match every word follow it
        const W2 = dropW(q, W);
        if (W2.length && W2.length < W.length) { const h2 = rank(W2, ALL, penFor(W2, y, q.eng)); const good = h2.some(isCar) ? isCar : c => c.soon && c.t !== 'eng';   // a live car, else a coming-soon card ("6.0 powerstroke")
        if (h2.some(good)) { const g2 = h2.filter(good); hits = [...g2, ...hits.filter(c => !g2.includes(c)), ...h2.filter(c => !good(c) && !hits.includes(c))]; notes = W.filter(w => !W2.includes(w)).map(w => q.szd[q.sz.indexOf(w)] || w).join(' '); } }
      }
      if (!hits.some(isCar) && W.length >= 2 && W.length <= 6) {   // "civic corolla": two cars named one after the other
        for (let k = 1; k < W.length && !pair; k++) { const a = resolve(W.slice(0, k), y, q), b = a && resolve(W.slice(k), y, q); if (a && b && a !== b) pair = [a, b]; }
        const it = pair && compareItem(pair.map(c => ({ c, y })));
        if (it) return { items: [it, ...pair.map(c => sideItem({ c, y }))] };   // a guess from two names in a row: never "strong"
      }
      // a coming-soon card that is exactly what was typed ("wrx" -> the current WRX) goes right after the first live match, not last
      ex = hits.filter(c => c.soon && c.t !== 'eng' && c.M && c.M === W.filter(w => !c.bw.includes(w)).join(''));
      if (ex.length) { hits = hits.filter(c => !ex.includes(c)); hits.splice(hits.findIndex(c => !c.soon) + 1, 0, ...ex); }
      // 11-13 (N1): one clear winner (every word exact, and the name is what was typed or it beats the next page) = "strong": the 404 page
      // (lx404.js) opens it on its own (/cars/ford-f150/ -> the F-Series, /cars/honda/ -> the Honda brand page)
      const live = hits.filter(c => !c.soon && c.u);
      if (live.length && !notes && score(live[0], W, null) === 0) {
        const mw = W.filter(w => !live[0].bw.includes(w)).join(''), s1 = live[1] ? score(live[1], W, null) : -1;
        strong = (!!mw && live[0].M === mw) || (live[0].t === 'br' && !mw) || s1 < 0 || s1 + pen(live[1]) > pen(live[0]);
      }
      if (!hits.length) {   // closest: the cars that match the most words
        let bestN = 0; const sc = [];
        for (const c of ALL) { let n = 0, k = 0; for (const x of W) { const v = wcost(x, c, true); if (v < 9) { n++; k += v; } } if (n) { sc.push([n, k + pen(c), c]); bestN = Math.max(bestN, n); } }
        hits = sc.filter(r => r[0] === bestN).sort((a, b) => a[1] - b[1]).map(r => r[2]); close = true;
      }
    }
    // 11-13 navigation test (N1): coming-soon cards (no page) filled half the list: at most 1, last (the exact one typed keeps its place);
    // match-up pages ("civic years to avoid" showed 4 Type R ones): at most 1 unless the search compares ("vs", "or", "compare")
    // engines: at most 2 after a car match unless the search names an engine ("2016 civic" listed 4 Civic engine sections)
    { const vsw = /\b(vs|versus|v|or|compare|compared|against)\b/.test(fold(raw)); let sn = ex.length, cn = 0, en = 0; const keep = [], late = [];
      const ecap = !q.eng && !q.sz.length && hits[0] && hits[0].t !== 'eng' && !W.some(w => SOFT.has(w));
      for (const c of hits) {
        if (c.soon && !ex.includes(c)) { if (!sn++) late.push(c); continue; }
        if (!vsw && c.u.startsWith('/compare/') && cn++) continue;
        if (ecap && c.t === 'eng' && en++ >= 2) continue;
        keep.push(c);
      }
      hits = [...keep, ...late]; }
    const top = hits.filter(c => !c.soon);
    const out = [];
    if (q.code) out.push(q.code);
    // problem words + a car: its problem page first
    const car = top.find(c => !c.t && c.ys.length) || null;
    // 11-13 (N1): "tacoma engine" opened the 2024 Tacoma: the word "engine" alone (no year) is not a problem search, and the default
    // year is never 2023 or newer (those years are still partial)
    if (q.prob && car && !close && !(q.pe && !y)) {
      const old = car.ys.filter(v => v <= 2022), yy = y && car.ys.includes(y) ? y : old.length ? Math.max(...old) : car.ys[car.ys.length - 1];   // the newest year with a full year of complaints
      if (q.prob === 'transmission' && GO && (GO.tr || []).includes(car.id)) out.push({ u: car.u + 'transmission/', b: `${car.n} transmission problems by year`, s: 'Every year, what owners describe, transmission recalls', kind: 'go' });
      else out.push({ u: `${car.u}${yy}/#${q.prob === 'recalls' ? 'recalls' : 'problems'}`, b: `${yy} ${car.n}: ${q.prob === 'recalls' ? 'recalls' : 'what owners complain about'}`, s: q.prob === 'transmission' ? 'Problems tab · transmission and every other area' : 'Problems, recalls and owner complaints', kind: 'go' });
    }
    const n = y ? 12 : 8;
    const carItems = hits.slice(0, n).map(c => {
      const yy = y && !c.t && !c.soon && c.ys.includes(y) ? y : 0, miss = y && !c.t && !c.soon && !c.ys.includes(y) ? y : 0;
      const u = c.soon ? '' : yy ? c.u + yy + '/' : c.u;
      const lab = c.soon ? (c.t === 'nd' ? 'No data yet' : 'Coming soon') + ({ perf: ' · performance car', sc: ' · supercar', moto: ' · motorcycle', eng: ' · engine' }[c.t] || '') + ' · tap to vote for it'
        : c.t ? KIND[c.t] : yy ? 'problems and owner complaints' : miss ? `no ${miss} in our data · every year ${c.ys[0]}-${c.ys.at(-1)}` : c.ys.length ? `every year ${c.ys[0]}-${c.ys.at(-1)}` : 'problems and owner complaints';
      return { u, b: (yy ? yy + ' ' : '') + c.n, s: (close ? 'Closest match · ' : '') + lab + (notes && !c.t ? ` · covers every version, ${notes} included` : ''), soon: c.soon, kind: close ? 'close' : 'car' };
    });
    // the question lists go first when the words were a question, after the cars when a car was named too
    if (!W.length || close) out.push(...q.lists, ...carItems); else out.push(...carItems, ...q.lists);
    if (!out.length || out.every(x => x.kind === 'close')) {
      const pop = ['/cars/honda-cr-v/', '/cars/toyota-rav4/', '/cars/honda-civic/', '/cars/ford-f-series/', '/cars/toyota-camry/'];
      if (!out.length) out.push(...ALL.filter(c => pop.includes(c.u) && !c.t).map(c => ({ u: c.u, b: c.n, s: 'Popular · every year', kind: 'pop' })));
      out.push(Object.assign(BEST('/best/', 'Best cars, by the data', 'Every ranked list'), { kind: 'pop' }));
      return { items: out, hint: `No exact match for “${raw.trim()}”. Closest:` };
    }
    if (!W.length && !q.prob && (q.code ? !q.lists.length : q.lists.length === 1)) strong = true;   // a code, or one list
    return { items: out, strong: strong && !close };
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
        const cl = (i === cur ? 'on' : '') + (h.u ? '' : ' fsoon fsv') + (h.kind === 'list' || h.kind === 'code' || h.kind === 'go' ? ' fgo' : '');
        return `<a role="option" ${h.u ? `href="${esc(h.u)}"` : `href="#" data-sv="${esc(h.b)}"`} class="${cl.trim()}"><b>${esc(h.b)}</b><small>${esc(h.s)}</small></a>`; }).join('');
      sug.querySelectorAll('[data-sv]').forEach(a => a.onclick = e => { e.preventDefault(); vote(a.dataset.sv, q); });   // a coming-soon match opens its vote sheet
    };
    // 11-12 round 2 (Liam, Mitch: "Enter does nothing"): Enter opens the highlighted match, else the top one, closest matches included
    const first = () => res.items.findIndex(h => h.kind !== 'pop');
    const run = () => { const v = q.value.trim(); res = v ? find(q.value) : { items: [] }; cur = res.brands ? -1 : first(); show(); say(''); };
    const go = () => {
      const v = q.value.trim(); if (!v) return false;
      res = find(q.value);
      if (res.brands) { say(`Add the brand and model, e.g. '${res.brands[0] ? res.brands[0].y : 2016} Honda Civic'.`); show(); return false; }
      const h = res.items[cur >= 0 && cur < res.items.length ? cur : first()];
      if (!h) { show(); say('Pick one of the closest matches.'); return false; }
      if (!h.u) { vote(h.b, q); return false; }
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
  // 11-13 navigation test (N1, problem 1): the bar's own search box (1024px+) and the magnifier (under 1024px: opens the menu, search focused)
  // ... and the 404 page's box (#lxq, assets/lx404.js fills it from the address that wasn't found)
  [['ghd', 'ghds'], ['lxq', 'lxqs']].forEach(([qi, si]) => {
    const xq = $(qi); if (!xq || !xq.form) return;
    const xf = xq.form, xsay = document.createElement('p'); xsay.className = 'fmiss'; xsay.setAttribute('role', 'status'); xsay.setAttribute('aria-live', 'polite');
    xf.appendChild(xsay);
    attach(xq, $(si), t => { xsay.textContent = t || ''; });
    xf.addEventListener('submit', e => { e.preventDefault(); load().then(() => { const b = boxes.find(x => x.q === xq); b && b.go(); }); });
  });
  const dq = $('ghd');
  if (dq) {
    addEventListener('keydown', e => {   // "/" focuses it, like most sites' search
      if (e.key !== '/' || e.ctrlKey || e.metaKey || e.altKey || !dq.offsetParent) return;
      const a = document.activeElement; if (a && (/^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName) || a.isContentEditable)) return;
      e.preventDefault(); dq.focus();
    });
  }
  const sbtn = document.querySelector('.lxs-btn');
  if (sbtn && mq) sbtn.addEventListener('click', e => {
    e.stopPropagation(); load();
    const h = sbtn.closest('.gh');
    if (h && !h.classList.contains('open')) { const m = h.querySelector('.gh-menu'); const o = m && m.offsetParent ? m : h.querySelector('.gh-more'); if (o) o.click(); }
    mq.focus({ preventScroll: true }); setTimeout(() => { if (document.activeElement !== mq) mq.focus({ preventScroll: true }); }, 60);
  });

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
  b.onchange = () => {   // 11-12 (UX test, Jess: "Honda's model list mixes in motorcycles"): cars first, motorcycles in their own group
    const all = P[b.value] || [], cars = all.filter(r => r[4] !== 'moto'), bikes = all.filter(r => r[4] === 'moto');
    opt(m, cars.map(([n, i]) => [i, n]), 'Model');
    if (bikes.length) { const g2 = document.createElement('optgroup'); g2.label = 'Motorcycles'; bikes.forEach(([n, i]) => g2.appendChild(new Option(n, i))); m.appendChild(g2); m.disabled = false; }
    opt(y, [], 'Year'); say('');
  };
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
