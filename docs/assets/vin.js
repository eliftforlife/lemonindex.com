// VIN check (11-02): decode a VIN with NHTSA's free vPIC API (runs in the browser), then send the reader to that car's Lemon Index page.
(() => {
  const f = document.getElementById('vinf'); if (!f) return;
  const out = document.getElementById('vinout'), PICK = JSON.parse(document.getElementById('pick').textContent);
  const VA = JSON.parse(document.getElementById('valias').textContent);
  const ALL = Object.entries(PICK).flatMap(([b, ms]) => ms.map(([n, id, ys]) => ({ b, n, id, ys })));
  const nz = s => (s || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  f.onsubmit = async e => {
    e.preventDefault();
    const vin = nz(f.vin.value);
    if (vin.length !== 17) { out.innerHTML = '<p class="vin-err">A VIN is 17 letters and numbers. It&#39;s on the driver-side dashboard (look through the windshield) and on your registration or insurance card.</p>'; return; }
    out.innerHTML = '<p>Checking…</p>';
    try {
      const r = (await (await fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/${vin}?format=json`)).json()).Results[0];
      if (!r.Make) { out.innerHTML = '<p class="vin-err">That VIN didn&#39;t decode. Double-check it (no letters I, O or Q).</p>'; return; }
      const mk = nz(r.Make), md = nz(r.Model), y = +r.ModelYear;
      const byAlias = VA[mk + '|' + md] && ALL.find(c => c.id === VA[mk + '|' + md]);
      const hit = byAlias || ALL.find(c => nz(c.b) === mk && (nz(c.n.replace(c.b, '')).startsWith(md) || md.startsWith(nz(c.n.replace(c.b, ''))))) || ALL.find(c => nz(c.b) === mk && nz(c.n).includes(md));
      const eng = [r.DisplacementL && `${(+r.DisplacementL).toFixed(1)}L`, r.EngineCylinders && `${r.EngineCylinders}-cylinder`, r.FuelTypePrimary && r.FuelTypePrimary.toLowerCase()].filter(Boolean).join(' ');
      const rows = [['Car', `${r.ModelYear} ${r.Make[0] + r.Make.slice(1).toLowerCase()} ${r.Model}${r.Trim ? ' ' + r.Trim : ''}`], ['Engine', eng], ['Drive', r.DriveType], ['Body', r.BodyClass], ['Built in', [r.PlantCity, r.PlantCountry].filter(Boolean).join(', ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase()).replace('(Usa)', '(USA)')]].filter(x => x[1]);
      out.innerHTML = `<div class="vin-card"><dl>${rows.map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join('')}</dl>
${hit && hit.ys.includes(y) ? `<a class="btn" href="/cars/${hit.id}/${y}/">See its problems and recalls →</a>` : hit ? `<a class="btn" href="/cars/${hit.id}/">See every ${hit.n} year →</a>` : '<p class="note">We don&#39;t cover this model yet.</p>'}
<p class="note">Open recalls are tied to the exact car: check this VIN for free at <a href="https://www.nhtsa.gov/recalls" rel="noopener" target="_blank">nhtsa.gov/recalls</a>.</p></div>`;
    } catch (err) { out.innerHTML = '<p class="vin-err">Couldn&#39;t reach the government VIN service. Try again in a minute.</p>'; }
  };
})();
