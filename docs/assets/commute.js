// 11-12 round 2 (Carlos, 60-mile commute: "what does the hybrid save me?"): the commute line on the Gas or hybrid card (build.py gas_hybrid_html).
// Plain arithmetic on the EPA numbers in the card's data attributes: EPA's yearly fuel cost assumes 15,000 miles a year, so cost per mile =
// yearly cost / 15,000; a commute of N miles a day, 5 days a week for 50 weeks = N x 250 miles a year.
(() => {
  document.querySelectorAll('.ghc-c').forEach(box => {
    const inp = box.querySelector('input'), out = box.querySelector('output'); if (!inp || !out) return;
    const g = +box.dataset.gas / 15000, h = +box.dataset.hyb / 15000, lab = box.dataset.lab || 'hybrid';
    const fmt = n => '$' + (Math.round(n / 10) * 10).toLocaleString('en-US');
    const run = () => {
      const mi = Math.max(0, Math.min(400, +inp.value || 0)), yr = mi * 250;
      if (!mi) { out.textContent = ''; return; }
      const d = (g - h) * yr;
      out.textContent = `${yr.toLocaleString('en-US')} miles a year: gas about ${fmt(g * yr)}, ${lab} about ${fmt(h * yr)}. ` + (d > 0 ? `The ${lab} saves about ${fmt(d)} a year.` : `No fuel savings for the ${lab}.`);
    };
    inp.addEventListener('input', run); run();
  });
})();
