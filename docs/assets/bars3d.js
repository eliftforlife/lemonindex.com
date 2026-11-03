// 3D bars that react to scrolling (11-03, Elijah: "3D bars on the site like the videos"). Pure CSS 3D boxes (no WebGL):
// bars grow when the chart scrolls into view, and the whole chart turns gently as it moves through the screen.
// Markup: <div class="b3d" data-b3d><div class="b3d-stage"> .b3d-col (style --v: 0..1 height, --c: color) ... </div></div>
(() => {
  const charts = [...document.querySelectorAll('[data-b3d]')]; if (!charts.length) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .25 });
  charts.forEach(c => io.observe(c));
  if (reduce) { charts.forEach(c => c.classList.add('in')); return; }
  let ticking = false;
  const tilt = () => { ticking = false;
    charts.forEach(c => { const r = c.getBoundingClientRect(), p = Math.min(1, Math.max(0, (innerHeight - r.top) / (innerHeight + r.height)));   // 0 entering .. 1 leaving
      c.style.setProperty('--ry', `${(-30 + p * 22).toFixed(1)}deg`); c.style.setProperty('--rx', `${(-16 + p * 8).toFixed(1)}deg`); }); };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(tilt); } }, { passive: true }); tilt();
})();
