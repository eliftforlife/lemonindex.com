// VIN check (11-02): decode a VIN with NHTSA's free vPIC API (runs in the browser), then send the reader to that car's Lemon Index page.
// 11-12 (UX test, Marcus: "the VIN check doesn't check recalls; it sends me to nhtsa.gov"): the recalls for that make, model and year come
// straight from NHTSA's free recalls API (api.nhtsa.gov allows lemonindex.com), each tagged against the decoded engine and fuel
// ("3.0L diesel only" on a 3.6L gas car = probably not this car). NHTSA has no free public open-recall-by-VIN API, so the page says how to
// confirm one is still open: the VIN lookup at nhtsa.gov/recalls or any dealer. The picture switches to the decoded model (it was a Camry).
// 11-14 (growth plan 1a + 1c): a VIN report. After the decode, /assets/vr/<model id>.json (vin_report.py) gives that model year's Lemon
// score and verdict, top complaint areas, counts, YouTube rank, engine pages and a test-drive list built only from its top complaint areas.
// The report card on top is made to be screenshotted and shared: its link is /vin/#v=<VIN> (the hash never reaches a server; it's cleared on load).
// Wording rule: "this model-year's record", never "this car's record": we can't see one car's history.
(() => {
  const f = document.getElementById('vinf'); if (!f) return;
  const out = document.getElementById('vinout'), PICK = JSON.parse(document.getElementById('pick').textContent);
  const VA = JSON.parse(document.getElementById('valias').textContent);
  const VI = (() => { const e = document.getElementById('vimg'); try { return new Set(JSON.parse(e ? e.textContent : '[]')); } catch (x) { return new Set(); } })();
  const ALL = Object.entries(PICK).flatMap(([b, ms]) => ms.map(([n, id, ys]) => ({ b, n, id, ys })));
  const nz = s => (s || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const cap = s => (s || '').toLowerCase().replace(/(^|[\s/(-])\w/g, c => c.toUpperCase());
  // which engines / fuel a recall covers, from its "recalling certain ... equipped with ..." sentence (same rules as build.py rtag)
  const rtag = sum => {
    const s = (sum || '').replace(/\s+/g, ' ');
    const sent = s.split(/(?<=\.)\s+(?=[A-Z])/).find(x => /recalling/i.test(x)) || s.slice(0, 300);
    if (!/equipped with|with (an? |the )?[0-9.]+ ?(l|liter)|(engines?|hybrid|diesel)\b/i.test(sent)) return null;
    const sz = sent.match(/\b(\d\.\d) ?(?:l\b|liter|-liter)/i);
    if (/gasoline|\bgas\b/i.test(sent) && /diesel/i.test(sent)) return null;
    if (/(equipped with|with)[^.]{0,60}(diesel|duramax|power ?stroke|cummins|\btdi\b|bluetec)|diesel engines?\b/i.test(sent)) return { fuel: 'diesel', l: sz ? sz[1] : null, t: (sz ? sz[1] + 'L diesel' : 'Diesel') + ' only' };
    const lm = sent.match(/recalling (?:certain )?(.*?)\b(vehicles|cars|trucks|SUVs)\b/i), many = !!(lm && /,| and /i.test(lm[1]));   // a model list: a hybrid in it is a name, not a limit
    if (/equipped with[^.]{0,40}(plug-in|phev)/i.test(sent) || (!many && /plug-in hybrid|\bphev\b|\b4xe\b/i.test(sent))) return { fuel: 'phev', t: 'Plug-in hybrid only' };
    if (/equipped with[^.]{0,40}hybrid/i.test(sent) || (!many && /hybrid (vehicles|models|electric)/i.test(sent))) return { fuel: 'hybrid', t: 'Hybrid only' };
    if (sz && /equipped with[^.]{0,30}\d\.\d ?(?:l\b|liter|-liter)[^.]{0,40}engine/i.test(sent)) return { l: sz[1], t: sz[1] + 'L engines only' };
    return null;
  };
  const fits = (tag, car) => {   // false = another engine / fuel; true = matches this car; null = can't tell
    if (!tag) return null;
    if (tag.fuel === 'diesel' && car.fuel && car.fuel !== 'diesel') return false;
    if (tag.fuel === 'phev' && car.elec !== undefined && !/phev|plug/i.test(car.elec)) return false;
    if (tag.fuel === 'hybrid' && car.elec !== undefined && !/hev|hybrid/i.test(car.elec)) return false;
    if (tag.l && car.l && Math.abs(+tag.l - car.l) > 0.05) return false;
    return (tag.fuel === 'diesel' && car.fuel === 'diesel') || (tag.l && car.l) ? true : null;
  };
  const sentence = s => {
    const t = (s || '').replace(/\s+/g, ' ').replace(/^.*?\brecalling\b.*?\b(vehicles|trucks|cars|SUVs|motorcycles)\b(?:[^.]|\.(?=\d))*\.\s*/i, '');
    const o = ((t || s || '').split(/(?<=[a-z)]\.)\s+(?=[A-Z])/)[0] || '').trim(); return o.length > 230 ? o.slice(0, 228) + '…' : o;
  };
  const pic = document.querySelector('.ph-v img'), picBox = document.querySelector('.ph-v');
  // 11-12 round 2 (Liam, Ontario): Transport Canada runs Canada's recalls
  const TC_DB = 'https://wwwapps.tc.gc.ca/Saf-Sec-Sur/7/VRDB-BDRV/search-recherche/menu.aspx?lang=eng';
  const TC_VIN = 'https://tc.canada.ca/en/road-transportation/defects-recalls-vehicles-tires-child-car-seats/find-vehicle-tire-child-car-seat-manufacturer';
  const tcLinks = `<a href="${TC_DB}" rel="noopener" target="_blank">search Transport Canada recalls</a> or <a href="${TC_VIN}" rel="noopener" target="_blank">check this VIN on the maker&#39;s Canadian recall site</a>`;
  // 11-12 round 2 (Ryan: a VIN with a wrong 9th character was accepted): the North American check digit (49 CFR 565)
  const checkOk = vin => {
    const tr = { A: 1, B: 2, C: 3, D: 4, E: 5, F: 6, G: 7, H: 8, J: 1, K: 2, L: 3, M: 4, N: 5, P: 7, R: 9, S: 2, T: 3, U: 4, V: 5, W: 6, X: 7, Y: 8, Z: 9 };
    const w = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]; let sum = 0;
    for (let i = 0; i < 17; i++) { const c = vin[i], v = /\d/.test(c) ? +c : tr[c]; if (v === undefined) return false; sum += v * w[i]; }
    const d = sum % 11; return vin[8] === (d === 10 ? 'X' : String(d));
  };
  const yearAgo = (() => { const d = new Date(); return (d.getFullYear() - 1) * 100 + d.getMonth() + 1; })();
  const isNew = x => { const m = (x.ReportReceivedDate || '').match(/^(\d{2})\/(\d{2})\/(\d{4})/); return m ? +m[3] * 100 + +m[2] >= yearAgo : false; };
  async function recalls(r, y, car, label, boxId, ca) {
    const box = document.getElementById(boxId || 'vinrc'); if (!box) return;
    let res;
    try { res = (await (await fetch(`https://api.nhtsa.gov/recalls/recallsByVehicle?make=${encodeURIComponent(r.Make)}&model=${encodeURIComponent(r.Model)}&modelYear=${y}`)).json()).results || []; }
    catch (e) { box.innerHTML = '<p class="vin-err">Couldn&#39;t load the recall list from NHTSA just now. Check the VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener" target="_blank">nhtsa.gov/recalls</a>.</p>'; return null; }
    const seen = new Set();
    const rows = res.filter(x => x.NHTSACampaignNumber && !seen.has(x.NHTSACampaignNumber) && seen.add(x.NHTSACampaignNumber))
      .map(x => { const tag = rtag(x.Summary); return { x, tag, fit: fits(tag, car), d: (x.ReportReceivedDate || '').match(/(\d{4})/) }; })
      .sort((a, b) => (a.fit === false) - (b.fit === false) || (b.d ? b.d[1] : '').localeCompare(a.d ? a.d[1] : ''));
    const other = rows.filter(z => z.fit === false).length;
    const li = z => `<li class="${z.fit === false ? 'vin-no' : ''}"><p class="vin-rh"><b>${esc(cap((z.x.Component || 'Recall').split(':')[0]))}</b> <small>· recall issued ${esc(z.d ? z.d[1] : '')} · <a href="https://www.nhtsa.gov/recalls?nhtsaId=${esc(z.x.NHTSACampaignNumber)}" rel="noopener" target="_blank">${esc(z.x.NHTSACampaignNumber)}</a></small>`
      + (z.tag ? ` <span class="rtag">${esc(z.tag.t)}</span>` : '') + (z.x.parkIt ? ' <span class="rtag vin-park">Park it: don&#39;t drive</span>' : '')
      + (isNew(z.x) && z.fit !== false ? ' <span class="rtag vin-new">New: most likely still open</span>' : '') + '</p>'
      + (z.fit === false ? `<p class="vin-fit">Probably not this car: it has a ${esc(car.desc)}.</p>` : '')
      + `<p>${esc(sentence(z.x.Summary))}</p>` + (z.x.Remedy && z.fit !== false ? `<p class="vin-fix"><b>Free fix:</b> ${esc(sentence(z.x.Remedy))}</p>` : '') + '</li>';
    box.innerHTML = (ca ? `<p class="vin-cabox"><b>This car was built in Canada${/^2/.test(ca) ? ' (its VIN starts with 2)' : ''}.</b> If it was sold or registered in Canada, its recalls are on Transport Canada&#39;s list: ${tcLinks}. The U.S. (NHTSA) list below may not match.</p>` : '')
      + `<h2>Recalls for the ${esc(label)}: ${rows.length}</h2>`
      + (rows.length ? `<p class="note">${other ? `${rows.length - other} may apply to this car; ${other} cover${other === 1 ? 's' : ''} other engines (listed last). ` : ''}This list covers every ${esc(label)}, not only this VIN.</p><ul class="vin-rc">${rows.map(li).join('')}</ul>`
        : '<p>NHTSA lists no recalls for this make, model and year.</p>')
      + (boxId ? `<p class="vin-open"><b>Is a recall still open on the car you&#39;re looking at?</b> Only its VIN can say. Ask the seller for it and check it above, or at <a href="https://www.nhtsa.gov/recalls" rel="noopener" target="_blank">nhtsa.gov/recalls</a>. Recall repairs are free, even on a used car. In Canada: ${tcLinks.replace('this VIN', 'a VIN')}.</p>`
        : `<p class="vin-open"><b>Is a recall still open on this exact car?</b> Only the VIN can say. Confirm it free at <a href="https://www.nhtsa.gov/recalls" rel="noopener" target="_blank">nhtsa.gov/recalls</a> (type this VIN) or ask any ${esc(cap(r.Make))} dealer. Recall repairs are free, even on a used car.${ca ? '' : ` In Canada: ${tcLinks}.`}</p>`);
    return { total: rows.length, other };
  }
  // ---- 11-14 VIN report helpers
  let RUN = 0;
  const num = n => n == null ? '' : Number(n).toLocaleString('en-US');
  // one line per verdict band (build.py band()): what the model year's record says about buying one. Never a claim about this one car.
  const BUY = { 'One of the most reliable': 'A strong pick, as model years go. Still have a mechanic check this one.',
    'Better than average': 'A good bet, as model years go. Still have a mechanic check this one.',
    'About average': 'An average model year: buy on this car&#39;s condition and service records.',
    'Worse than average': 'Only with proof the problem areas below were fixed, and a mechanic&#39;s check.',
    'Avoid': 'We&#39;d pass, unless records show the problem areas below were already fixed.',
    'Too new: partial score': 'Too new to call: its score covers less than 3 years of complaints so far.' };
  // the site's Lemon gauge (build.py gauge()), drawn here because the report is built in the browser
  const gauge = (li, lab) => {
    const cx = 120, cy = 118, r = 92, t = v => Math.PI * Math.min(v, 300) / 300, P = (v, rr = r) => [cx - rr * Math.cos(t(v)), cy - rr * Math.sin(t(v))], n1 = n => n.toFixed(1);
    const arc = (a, b, col) => { const [x1, y1] = P(a), [x2, y2] = P(b); return `<path d="M${n1(x1)} ${n1(y1)}A${r} ${r} 0 0 1 ${n1(x2)} ${n1(y2)}" stroke="${col}" />`; };
    let ticks = '', nums = '';
    for (let v = 0; v <= 300; v += 25) { const [a1, b1] = P(v, r - 16), [a2, b2] = P(v, v % 100 ? r - 24 : r - 30); ticks += `<line x1="${n1(a1)}" y1="${n1(b1)}" x2="${n1(a2)}" y2="${n1(b2)}" />`; }
    for (const v of [0, 100, 200, 300]) { const [a, b] = P(v, r - 44); nums += `<text x="${n1(a)}" y="${n1(b + 5)}">${v}</text>`; }
    const cls = li < 85 ? 'good' : li <= 115 ? 'mid' : 'bad';
    return `<figure class="gauge ${cls}" data-vrg style="--a:${n1(Math.min(li, 300) / 300 * 180 - 90)}deg" aria-label="Lemon Index ${li}"><svg viewBox="0 0 240 150" role="img" aria-hidden="true">`
      + `<g class="g-arc" fill="none" stroke-width="16" stroke-linecap="butt">${arc(0, 84, '#1a8f4c')}${arc(86, 114, '#c9ccd1')}${arc(116, 300, '#e8141c')}</g><g class="g-tick">${ticks}</g><g class="g-num">${nums}</g>`
      + `<g class="g-ndl"><path d="M${cx - 4} ${cy}L${cx} ${cy - r + 6}L${cx + 4} ${cy}Z" /><circle cx="${cx}" cy="${cy}" r="11" /><circle class="g-hub" cx="${cx}" cy="${cy}" r="5" /></g></svg>`
      + `<figcaption><b>${li}</b><span>${esc(lab)} · 100 = average car</span></figcaption></figure>`;
  };
  const cap1 = s => (s || '').charAt(0).toUpperCase() + (s || '').slice(1);
  const NOREC = 'No model-year record to go on yet: judge it on this car&#39;s condition, service records and a mechanic&#39;s check.';
  // 1c: the report card, one screen made for screenshots and sharing
  const card = (label, sub, Y, D, y, short) => {
    let top, buy;
    if (Y && Y.ok) { top = gauge(Y.li, `${y} Lemon Index${Y.early ? ' (partial)' : ''}`) + `<div class="vr-v"><p class="vr-w ${Y.cls}">${esc(Y.word)}.</p><p class="vr-why">${Y.why || ''}</p></div>`; buy = BUY[Y.word] || ''; }
    else if (Y) { top = `<div class="vr-nos"><b>–</b>No score</div><div class="vr-v"><p class="vr-w na">No score yet.</p><p class="vr-why">${esc(cap1(Y.pln))}.</p></div>`; buy = 'No score for this model year, so judge it on this car&#39;s condition, service records and a mechanic&#39;s check.'; }
    else if (D) { const ys = Object.keys(D.years); top = `<div class="vr-v"><p class="vr-w na">No data yet for the ${y}.</p><p class="vr-why">We have the ${esc(D.name)} for ${ys[0]} to ${ys[ys.length - 1]}.</p></div>`; buy = NOREC; }
    else { top = `<div class="vr-v"><p class="vr-w na">No data yet.</p><p class="vr-why">We don&#39;t score the ${esc(label)} yet. Its recalls are below.</p></div>`; buy = NOREC; }
    const P = Y && Y.parts && Y.parts.length ? Y.parts : null, mx = P ? Math.max(...P.map(p => p[1])) : 1;
    const risks = P ? `<p class="vr-h">Biggest risks for the ${y} <small class="vr-none">· share of its owner complaints</small></p><ol class="vr-risks">${P.map(([nm, pct]) => `<li><b>${esc(nm)}</b><em>${pct}%</em><span class="vr-bar"><i style="width:${Math.max(4, pct / mx * 100).toFixed(0)}%"></i></span></li>`).join('')}</ol>`
      : `<p class="vr-h">Biggest risks</p><p class="vr-none">No data yet: too few owner complaints for this model year.</p>`;
    const yu = Y && D ? `${D.url}${y}/` : D ? D.url : '';
    return `<article class="vr-card" aria-label="Model-year report card"><p class="vr-k"><img src="/assets/icon-64.png" alt="" width="18" height="18">Lemon Index · this model year&#39;s record</p>`
      + `<h2 class="vr-t">${esc(label)}${sub ? `<span>${esc(sub)}</span>` : ''}</h2><div class="vr-top">${top}</div>`
      + `<p class="vr-buy"><b>Should you buy one?</b>${buy}</p>`
      + `<div class="vr-stats"><div><small>Recalls</small><b id="vr-rc">…</b><span id="vr-rcs">NHTSA, ${y}</span></div>`
      + (Y && Y.n != null ? `<div><small>Complaints</small><b>${num(Y.n)}</b><span>to NHTSA ${Y.early ? 'so far' : 'in its first 3 years'}${Y.all > Y.n ? ` (${num(Y.all)} in all)` : ''}</span></div>` : `<div><small>Complaints</small><b class="mute">No data yet</b><span>NHTSA</span></div>`)
      + (Y && Y.yt ? `<div><small>YouTube rank</small><b>#${Y.yt[0]}</b><span>of ${Y.yt[1]} ${esc(short)} years in reviews</span></div>` : `<div><small>YouTube rank</small><b class="mute">No data yet</b><span>too few videos to rank</span></div>`)
      + `</div>${risks}<p class="vr-src">From NHTSA owner complaints and recalls, U.S. sales and YouTube reviews for the ${y} model year. It isn&#39;t this car&#39;s history (accidents, owners, title or service). lemonindex.com</p>`
      + `<div class="vr-act"><button type="button" class="btn vr-share">Share this report</button>${D && Y ? `<button type="button" class="btn btn-ghost lsv-b lsv-bt vr-save" data-lsv-id="${esc(D.id)}" data-lsv-y="${esc(y)}" data-lsv-n="${esc(D.name)}"${VI.has(D.id) ? ` data-lsv-img="/assets/ai-models/${esc(D.id)}.webp?v=1"` : ''}><svg class="lsv-h" aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20.5s-7.5-4.6-9.2-9.4C1.7 7.9 3.6 4.5 7 4.5c2 0 3.7 1.1 5 3 1.3-1.9 3-3 5-3 3.4 0 5.3 3.4 4.2 6.6-1.7 4.8-9.2 9.4-9.2 9.4z"/></svg><span class="lsv-l">Save</span></button>` : ''}${yu ? `<a class="btn btn-ghost" href="${esc(yu)}">${Y ? `Full ${y} ${esc(short)} page` : `Every ${esc(short)} year`} →</a>` : ''}<span class="vr-msg" role="status"></span></div></article>`;
  };
  // share: the phone's share sheet (Web Share API), else copy the link, else show it selected. The VIN rides in the hash, never the query string.
  async function share(btn, vin, text) {
    const url = `${location.origin}/vin/?utm_source=share#v=${vin}`, box = btn.parentNode, msg = box.querySelector('.vr-msg');
    if (navigator.share && matchMedia('(pointer: coarse)').matches) { try { await navigator.share({ title: document.title, text, url }); return; } catch (e) { if (e && e.name === 'AbortError') return; } }
    try { await navigator.clipboard.writeText(url); msg.textContent = 'Link copied ✓'; return; } catch (x) { /* no clipboard: show it */ }
    let i = box.querySelector('.vr-cp');
    if (!i) { i = document.createElement('input'); i.className = 'vr-cp'; i.readOnly = true; i.setAttribute('aria-label', 'Link to this report'); box.appendChild(i); }
    i.value = url; i.focus(); i.select(); msg.textContent = 'Copy this link';
  }
  f.onsubmit = async e => {
    e.preventDefault();
    const run = ++RUN;
    const vin = nz(f.vin.value);
    if (vin.length !== 17) { out.innerHTML = '<p class="vin-err">A VIN is 17 letters and numbers. It&#39;s on the driver-side dashboard (look through the windshield) and on your registration or insurance card.</p>'; return; }
    const bad = !checkOk(vin);
    out.innerHTML = '<p>Checking…</p>';
    let r;
    try { r = (await (await fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/${vin}?format=json`)).json()).Results[0]; }
    catch (err) { out.innerHTML = '<p class="vin-err">Couldn&#39;t reach the government VIN service. Try again in a minute.</p>'; return; }
    if (run !== RUN) return;
    if (!r || !r.Make) { out.innerHTML = '<p class="vin-err">That VIN didn&#39;t decode. Double-check it (no letters I, O or Q).</p>'; return; }
    const mk = nz(r.Make), md = nz(r.Model), y = +r.ModelYear;
    const byAlias = VA[mk + '|' + md] && ALL.find(c => c.id === VA[mk + '|' + md]);
    const hit = byAlias || ALL.find(c => nz(c.b) === mk && (nz(c.n.replace(c.b, '')).startsWith(md) || md.startsWith(nz(c.n.replace(c.b, ''))))) || ALL.find(c => nz(c.b) === mk && nz(c.n).includes(md));
    const eng = [r.DisplacementL && `${(+r.DisplacementL).toFixed(1)}L`, r.EngineCylinders && `${r.EngineCylinders}-cylinder`, r.FuelTypePrimary && r.FuelTypePrimary.toLowerCase()].filter(Boolean).join(' ');
    const label = `${r.ModelYear} ${cap(r.Make)} ${r.Model}`;
    const rows = [['Car', `${label}${r.Trim ? ' ' + r.Trim : ''}`], ['Engine', eng], ['Drive', r.DriveType], ['Body', r.BodyClass], ['Built in', [r.PlantCity, r.PlantCountry].filter(Boolean).join(', ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase()).replace('(Usa)', '(USA)')]].filter(x => x[1]);
    const warn = bad ? `<p class="vin-warn"><b>Check this VIN for a typo.</b> Its 9th character (${esc(vin[8])}) doesn&#39;t match the check digit the other 16 add up to, so one character is probably mistyped. Compare it with the VIN on the car itself. (Cars built for sale outside North America can skip the check digit.)</p>` : '';
    const ft = r.FuelTypePrimary || '';
    const fuel = /diesel/i.test(ft) ? 'diesel' : /electric/i.test(ft) && !r.DisplacementL ? 'electric' : ft ? 'gas' : null;
    const car = { fuel, l: r.DisplacementL ? Math.round(+r.DisplacementL * 10) / 10 : null, elec: ft ? (r.ElectrificationLevel || '') : undefined,
                  desc: [r.DisplacementL && `${(+r.DisplacementL).toFixed(1)}L`, fuel === 'gas' ? 'gas' : fuel, 'engine'].filter(Boolean).join(' ') };
    const ca = /^2/.test(vin) || /canada/i.test(r.PlantCountry || '') ? vin : '';
    // 11-14: the model-year report (vin_report.py -> /assets/vr/<id>.json)
    out.innerHTML = warn + '<p>Loading the model-year report…</p>';
    let D = null;
    if (hit) { try { const res = await fetch(`/assets/vr/${hit.id.replace(/\//g, '_')}.json`); if (res.ok) D = await res.json(); } catch (x) { D = null; } }
    if (run !== RUN) return;
    const Y = D && D.years[String(y)];
    const short = D ? D.name.replace(/^\S+\s/, '') : cap(r.Model);
    const sub = [r.Trim, eng.replace(/ gasoline$/, ' gas')].filter(Boolean).join(' · ');
    const disp = car.l ? car.l.toFixed(1) : null, ENG = Y ? Y.eng || [] : [];
    const em = disp ? ENG.filter(x => x[2] === disp) : [];
    const engRow = em.length ? [em.length > 1 ? `Engine pages (${disp}L)` : 'Engine page', em] : (!disp && ENG.length ? [`Engines in the ${y}`, ENG] : null);
    const dl = rows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join('')
      + (engRow ? `<dt>${esc(engRow[0])}</dt><dd><ul class="vr-eng">${engRow[1].map(([n, u]) => `<li><a href="${esc(u)}">${esc(n)} →</a></li>`).join('')}</ul></dd>` : '');
    const td = !Y ? `<p class="vr-none">No data yet for this model year.</p>`
      : Y.td.length ? `<ol>${Y.td.map(([lab, pct, txt, mi]) => `<li><b>${esc(lab)}</b> <small>· ${pct}% of complaints${mi ? ` · owners&#39; median ${num(mi)} miles` : ''}</small><p>${esc(txt)}</p></li>`).join('')}</ol>`
      : `<p class="vr-none">No data yet: too few owner complaints for the ${y} to say which areas to check.</p>`;
    out.innerHTML = warn + card(label, sub, Y, D, y, short)
      + `<section class="vr-sec"><h2>The car</h2><div class="vin-card"><dl>${dl}</dl>${hit && !D ? `<a class="btn" href="/cars/${hit.id}/">See every ${esc(hit.n)} year →</a>` : hit ? '' : '<p class="note">We don&#39;t cover this model yet, so there&#39;s no model-year score. Its recalls are below.</p>'}</div></section>`
      + `<section class="vr-sec vr-td"><h2>What to check on a test drive</h2>${Y && Y.td.length ? `<p class="note">One check for each of the ${y} ${esc(short)}&#39;s top complaint areas in NHTSA owner complaints, biggest first. A mechanic&#39;s inspection still matters most.</p>` : ''}${td}</section>`
      + `<section class="vin-recalls" id="vinrc" aria-live="polite"><p>Looking up recalls…</p></section>`;
    requestAnimationFrame(() => requestAnimationFrame(() => out.querySelectorAll('[data-vrg]').forEach(g => g.classList.add('in'))));
    if (window.LSAVE) LSAVE.sync(out);   // 11-14 growth 4d: the Save button (saved.js) shows whether this model year is already saved
    const sb = out.querySelector('.vr-share');
    if (sb) sb.onclick = () => share(sb, vin, `${label}: ${Y && Y.ok ? `${Y.word} (Lemon Index ${Y.li})` : 'model-year report'}. Free VIN report:`);
    if (pic && picBox) {   // the picture follows the decoded model (our AI illustration of it), or goes away
      if (hit && VI.has(hit.id)) { pic.removeAttribute('srcset'); pic.src = `/assets/ai-models/${hit.id}.webp?v=1`; pic.alt = hit.n; picBox.hidden = false; }
      else picBox.hidden = true;
    }
    const rc = await recalls(r, y, car, label, null, ca);
    if (run !== RUN) return;
    const rb = document.getElementById('vr-rc'), rs = document.getElementById('vr-rcs');
    if (rb && rc) { rb.textContent = rc.other ? rc.total - rc.other : rc.total; rs.textContent = rc.other ? `of ${rc.total} for the ${y}; the rest cover other engines` : `NHTSA, every ${y} ${short}`; }
    else if (rb && Y && Y.rc != null) { rb.textContent = Y.rc; rs.textContent = `NHTSA, ${y} (our last update)`; }
    else if (rb) { rb.textContent = '–'; rb.classList.add('mute'); rs.textContent = 'NHTSA didn\'t answer just now'; }
  };
  // ---- 11-12 round 2 (Jake: "nothing tells a buyer to ask for the VIN, or which recall is probably still open"): no-VIN helper
  const nf = document.getElementById('vnvf'), VN = (() => { const e = document.getElementById('vnames'); try { return JSON.parse(e ? e.textContent : '{}'); } catch (x) { return {}; } })();
  // 11-12: the VIN box on the /best/ lists (assets/cb.js) hands the VIN over in the hash (#v=...), never the query string
  const hv = (location.hash.match(/^#v=([A-Za-z0-9]{11,17})$/) || [])[1];
  if (hv) { f.vin.value = hv.toUpperCase(); history.replaceState(null, '', location.pathname + location.search); f.requestSubmit ? f.requestSubmit() : f.onsubmit(new Event('submit')); }
  if (nf) {
    const opt = (sel, items) => { sel.innerHTML = items.map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join(''); };
    const brands = Object.keys(PICK).filter(b => PICK[b].some(([, id, ys]) => VN[id] && ys.length)).sort();
    const fillY = () => { const c = ALL.find(c => c.id === nf.md.value); opt(nf.y, (c ? [...c.ys].sort((a, b) => b - a) : []).map(y => [y, y])); };
    const fillM = () => { opt(nf.md, PICK[nf.mk.value].filter(([, id, ys]) => VN[id] && ys.length).map(([n, id]) => [id, n])); fillY(); };
    opt(nf.mk, brands.map(b => [b, b])); nf.mk.onchange = fillM; nf.md.onchange = fillY; if (brands.length) fillM();
    nf.onsubmit = e => {
      e.preventDefault(); const c = ALL.find(c => c.id === nf.md.value), y = +nf.y.value; if (!c || !y || !VN[c.id]) return;
      const box = document.getElementById('vnvout'); box.innerHTML = '<p>Looking up recalls…</p>';
      recalls({ Make: VN[c.id][0], Model: VN[c.id][1] }, y, {}, `${y} ${c.n}`, 'vnvout', '')
        .then(() => { if (c.ys.includes(y)) box.insertAdjacentHTML('beforeend', `<p class="note"><a href="/cars/${c.id}/${y}/">The ${y} ${esc(c.n)}: problems, repair costs and questions to ask the seller →</a></p>`); });
    };
  }
})();
