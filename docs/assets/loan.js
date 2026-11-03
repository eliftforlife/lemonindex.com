// "Is my car loan rate fair?" (11-03). Compares the APR a reader was offered with the average for their credit tier (Experian, in <script id="rates">),
// then says in dollars what the gap costs over the loan. All math happens here so the reader never has to do any.
(() => {
  const f = document.getElementById('loanf'); if (!f) return;
  const R = JSON.parse(document.getElementById('rates').textContent), out = document.getElementById('loanout');
  const pay = (P, apr, n) => { const r = apr / 1200; return r ? P * r / (1 - Math.pow(1 + r, -n)) : P / n; };
  const money = x => '$' + Math.round(x).toLocaleString('en-US');
  const run = () => {
    const tier = R.tiers[+f.tier.value], kind = f.kind.value, apr = parseFloat(f.apr.value), P = parseFloat(String(f.amount.value).replace(/[^0-9.]/g, '')), n = +f.term.value;
    if (!(apr >= 0 && apr < 60) || !(P > 500) || !n) { out.innerHTML = '<p class="note">Enter the APR you were offered and the amount you&#39;d borrow.</p>'; return; }
    const avg = tier[kind], gap = apr - avg, extra = (pay(P, apr, n) - pay(P, avg, n)) * n;
    const cls = gap <= .75 ? 'good' : gap <= 2.5 ? 'mid' : 'bad';
    const head = gap <= -.25 ? 'Better than average for your credit' : gap <= .75 ? 'About normal for your credit' : gap <= 2.5 ? 'Above average for your credit' : 'Way above average for your credit';
    const what = gap <= .75 ? 'This looks like a fair rate. It can still pay to get one more quote.'
      : `That&#39;s about <b>${money(extra)} extra</b> over ${n} months on ${money(P)}. Get a quote from your bank or a credit union before you sign, and ask the dealer to beat it.`;
    out.innerHTML = `<div class="loan-res ${cls}"><b>${head}</b><p>Average for ${tier.name.toLowerCase()} credit (${tier.range}) on a ${kind} car: <b>${avg.toFixed(2)}%</b>. Your offer: <b>${apr.toFixed(2)}%</b>${Math.abs(gap) >= .05 ? ` (${gap > 0 ? '+' : ''}${gap.toFixed(2)} points)` : ''}.</p><p>${what}</p>
<p class="loan-pay">Monthly payment: <b>${money(pay(P, apr, n))}</b> at your rate vs <b>${money(pay(P, avg, n))}</b> at the average.</p></div>`;
  };
  f.addEventListener('input', run); f.addEventListener('submit', e => { e.preventDefault(); run(); });
})();
