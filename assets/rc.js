// Recall check pages (11-14, growth plan 2B-1). Two small tools, no data stored:
//  - #rcvf: the VIN box hands the VIN to /vin/ in the hash (/vin/#v=<VIN>; the hash never reaches a server). /vin/ decodes it and
//    shows that model year's report and its recalls.
//  - #rcpf (on /recalls/): pick make, model and year; every NHTSA recall for it comes live from api.nhtsa.gov (the same call /vin/
//    makes), newest first. NHTSA's public API works by make/model/year, so the page says how to confirm a recall is still open on one car.
(() => {
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const cap = s => (s || '').toLowerCase().replace(/(^|[\s/(-])\w/g, c => c.toUpperCase());
  const sentence = s => {   // same rule as vin.js: skip the "X is recalling certain ... vehicles" opener, keep the defect
    const t = (s || '').replace(/\s+/g, ' ').replace(/^.*?\brecalling\b.*?\b(vehicles|trucks|cars|SUVs|motorcycles)\b(?:[^.]|\.(?=\d))*\.\s*/i, '');
    const o = ((t || s || '').split(/(?<=[a-z)]\.)\s+(?=[A-Z])/)[0] || '').trim(); return o.length > 230 ? o.slice(0, 228) + '…' : o;
  };
  const yearAgo = (() => { const d = new Date(); return (d.getFullYear() - 1) * 100 + d.getMonth() + 1; })();
  const isNew = x => { const m = (x.ReportReceivedDate || '').match(/^(\d{2})\/(\d{2})\/(\d{4})/); return m ? +m[3] * 100 + +m[2] >= yearAgo : false; };
  const TC_DB = 'https://wwwapps.tc.gc.ca/Saf-Sec-Sur/7/VRDB-BDRV/search-recherche/menu.aspx?lang=eng';

  document.querySelectorAll('form.rcx-vf').forEach(vf => vf.addEventListener('submit', e => {
    e.preventDefault();
    const v = (vf.querySelector('input').value || '').toUpperCase().replace(/[^A-Z0-9]/g, ''), msg = vf.querySelector('.rcx-msg');
    if (!/^[A-Z0-9]{11,17}$/.test(v) || /[IOQ]/.test(v)) { if (msg) { msg.textContent = 'A VIN has 17 letters and numbers, never I, O or Q.'; msg.hidden = false; } return; }
    location.href = '/vin/#v=' + v;
  }));

  const pf = document.getElementById('rcpf'), dj = document.getElementById('rcpick'), out = document.getElementById('rcpout');
  if (!pf || !dj || !out) return;
  let P = {}; try { P = JSON.parse(dj.textContent); } catch (x) { return; }
  const opt = (sel, items) => { sel.innerHTML = items.map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join(''); };
  const makes = Object.keys(P).sort();
  const cur = () => (P[pf.mk.value] || []).find(m => m[1] === pf.md.value);
  const fillY = () => { const m = cur(); opt(pf.y, (m ? [...m[2]].sort((a, b) => b - a) : []).map(y => [y, y])); };
  const fillM = () => { opt(pf.md, (P[pf.mk.value] || []).map(m => [m[1], m[0]])); fillY(); };
  opt(pf.mk, makes.map(b => [b, b])); pf.mk.onchange = fillM; pf.md.onchange = fillY;
  const pre = (pf.dataset.make && P[pf.dataset.make]) ? pf.dataset.make : makes[0]; if (pre) { pf.mk.value = pre; fillM(); }
  pf.addEventListener('submit', async e => {
    e.preventDefault();
    const m = cur(), y = +pf.y.value; if (!m || !y) return;
    const [name, id, , nmk, nmd, rurl] = m, mk = pf.mk.value, full = name.startsWith(mk + ' ') ? name : `${mk} ${name}`, label = `${y} ${full}`;
    out.innerHTML = '<p class="note">Looking up recalls from NHTSA…</p>';
    let res;
    try { res = (await (await fetch(`https://api.nhtsa.gov/recalls/recallsByVehicle?make=${encodeURIComponent(nmk)}&model=${encodeURIComponent(nmd)}&modelYear=${y}`)).json()).results || []; }
    catch (x) { out.innerHTML = '<p class="vin-err">Couldn&#39;t reach NHTSA just now. Try again, or check at <a href="https://www.nhtsa.gov/recalls" rel="noopener" target="_blank">nhtsa.gov/recalls</a>.</p>'; return; }
    const seen = new Set();
    const rows = res.filter(x => x.NHTSACampaignNumber && !seen.has(x.NHTSACampaignNumber) && seen.add(x.NHTSACampaignNumber))
      .map(x => ({ x, d: (x.ReportReceivedDate || '').match(/^(\d{2})\/(\d{2})\/(\d{4})/) }))
      .sort((a, b) => (b.d ? b.d[3] + b.d[2] + b.d[1] : '').localeCompare(a.d ? a.d[3] + a.d[2] + a.d[1] : ''));
    const li = z => `<li><p class="vin-rh"><b>${esc(cap((z.x.Component || 'Recall').split(':')[0]))}</b> <small>· recall issued ${esc(z.d ? z.d[3] : '')} · <a href="https://www.nhtsa.gov/recalls?nhtsaId=${esc(z.x.NHTSACampaignNumber)}" rel="noopener" target="_blank">${esc(z.x.NHTSACampaignNumber)}</a></small>`
      + (z.x.parkIt ? ' <span class="rtag vin-park">Park it: don&#39;t drive</span>' : '') + (z.x.parkOutSide ? ' <span class="rtag vin-park">Park outside</span>' : '')
      + (isNew(z.x) ? ' <span class="rtag vin-new">New: most likely still open</span>' : '') + '</p>'
      + `<p>${esc(sentence(z.x.Summary))}</p>` + (z.x.Remedy ? `<p class="vin-fix"><b>Free fix:</b> ${esc(sentence(z.x.Remedy))}</p>` : '') + '</li>';
    out.innerHTML = `<h3 class="rcx-rh">Recalls for the ${esc(label)}: ${rows.length}</h3>`
      + (rows.length ? `<p class="note">This list covers every ${esc(label)}, not one car. Newest first: a recall from the last 12 months has had the least time to be fixed.</p><ul class="vin-rc">${rows.map(li).join('')}</ul>`
        : '<p>NHTSA lists no recalls for this make, model and year.</p>')
      + `<p class="vin-open"><b>Is one still open on your car?</b> Only its VIN can say: <a href="/vin/">check the VIN</a>, type it at <a href="https://www.nhtsa.gov/recalls" rel="noopener" target="_blank">nhtsa.gov/recalls</a>, or ask any dealer of that brand. In Canada, <a href="${TC_DB}" rel="noopener" target="_blank">search Transport Canada recalls</a>.</p>`
      + `<p class="note"><a href="/cars/${esc(id)}/${y}/">The ${esc(label)}: problems, complaints and its Lemon Index</a>` + (rurl ? ` · <a href="${esc(rurl)}">Every ${esc(full)} recall, all years</a>` : '') + '</p>';
  });
})();
