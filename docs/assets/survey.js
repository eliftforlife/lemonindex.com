// "Help our site" (11-03, Elijah): one anonymous multiple-choice question at the bottom of every page; after a tap, show how everyone answered.
// On a car-year page, about half the time it asks about that exact car (own it? miles, price paid, dealer or private party, problems...).
// Questions: /assets/survey-q.json (from data/survey.json). Answers: the lemon-survey Cloudflare Worker (worker/survey_worker.js, D1).
(() => {
  const box = document.getElementById('ask'); if (!box) return;
  const API = 'https://lemon-survey.elift08.workers.dev', fid = box.dataset.fid || '', year = +box.dataset.year || 0, carName = box.dataset.car || '';
  const KEY = 'li-ask-done', done = (() => { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch { return {}; } })();
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(done)); } catch {} };
  const E = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  let Q, byId = {};
  const keyOf = q => q.car ? `${q.id}|${fid}|${year}` : q.id;
  const pickSite = () => { const open = Q.site.filter(q => !done[q.id]); return open.length ? open[Math.floor(Math.random() * open.length)] : null; };
  const first = () => { const f0 = byId[box.dataset.first || '']; if (f0 && !done[keyOf(f0)]) return f0;   // a page can lead with its own question (loan page: credit range)
    const own = byId.own; if (fid && year && own && !done[keyOf(own)] && Math.random() < .5) return own; return pickSite() || (fid && year && own && !done[keyOf(own)] ? own : null); };
  const shell = inner => `<div class="ask-card"><p class="ask-kick">Help our site</p>${inner}<p class="ask-fine">Anonymous. No email, no account. Just tap an answer.</p></div>`;
  const show = q => {
    if (!q) { box.hidden = true; return; }
    box.hidden = false;
    box.innerHTML = shell(`<h2 class="ask-q">${E(q.q.replace('{car}', carName))}</h2><div class="ask-opts">${q.a.map((a, i) => `<button type="button" data-i="${i}">${E(a)}</button>`).join('')}</div>`);
    box.querySelectorAll('[data-i]').forEach(b => b.addEventListener('click', () => answer(q, q.a[+b.dataset.i])));
  };
  const results = (q, mine, counts) => {
    const tot = Object.values(counts).reduce((s, n) => s + n, 0) || 1;
    const rows = q.a.map(a => { const n = counts[a] || 0, p = Math.round(n / tot * 100);
      return `<div class="ask-r${a === mine ? ' me' : ''}"><i style="--w:${p}%"></i><span>${E(a)}${a === mine ? ' <em>· you</em>' : ''}</span><b>${p}%</b></div>`; }).join('');
    const next = q.next && (typeof q.next === 'string' ? q.next : q.next[mine]);
    const nq = next ? byId[next] : pickSite();
    requestAnimationFrame(() => requestAnimationFrame(() => box.querySelectorAll('.ask-r i').forEach(i => i.classList.add('go'))));
    box.innerHTML = shell(`<h2 class="ask-q">${E(q.q.replace('{car}', carName))}</h2><div class="ask-rs">${rows}</div>
<p class="ask-n">${tot === 1 ? "You're the first to answer. Thanks!" : tot < 10 ? `You're one of the first ${tot} to answer. Thanks!` : `${tot.toLocaleString()} answers so far. Thanks!`}</p>${nq ? '<button type="button" class="btn ask-next">Next question →</button>' : ''}`);
    const nb = box.querySelector('.ask-next'); if (nb) nb.addEventListener('click', () => show(nq));
  };
  const answer = async (q, a) => {
    done[keyOf(q)] = a; save();
    let counts = { [a]: 1 };
    try {
      const r = await fetch(API + '/a', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ qid: q.id, a, fid: q.car ? fid : undefined, year: q.car ? year : undefined, page: location.pathname }) });
      if (r.ok) counts = (await r.json()).counts || counts;
    } catch {}
    results(q, a, counts);
  };
  fetch('/assets/survey-q.json').then(r => r.json()).then(j => {
    Q = { site: j.site, car: j.car.map(q => ({ ...q, car: true })) }; [...Q.site, ...Q.car].forEach(q => byId[q.id] = q);
    if (!fid || !year) Q.car = [];
    show(first());
  }).catch(() => { box.hidden = true; });
})();
