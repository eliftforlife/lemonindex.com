// goal.js (11-25): the donation goal box on /support/ and /coming-soon/ shows the live total.
// The page is built with a baked number (data/support_goal.json, support_pages.py _sp_goal); this asks the lemon-store Worker's GET /goal
// ({month, raised, n}: this month's donations from Stripe, cached 5 min there) and, when its month matches the box's data-month, changes only
// the text and the bar width of the same elements (no layout shift). Any failure leaves the baked number as it is.
(function () {
  var boxes = document.querySelectorAll('.spg-goal[data-month]');
  if (!boxes.length || !window.fetch) return;
  var LADDER = [100, 250, 500, 1000, 2500, 5000];   // same as _SP_LADDER in support_pages.py
  var usd = function (n) { return '$' + n.toLocaleString('en-US'); };
  fetch('https://lemon-store.elift08.workers.dev/goal', { credentials: 'omit', referrerPolicy: 'no-referrer' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (g) {
      if (!g || typeof g.month !== 'string' || typeof g.raised !== 'number' || !isFinite(g.raised) || g.raised < 0) return;
      var raised = Math.floor(g.raised), goal = LADDER[LADDER.length - 1], hit = 0, i;
      for (i = LADDER.length - 1; i >= 0; i--) { if (LADDER[i] > raised) goal = LADDER[i]; else if (!hit) hit = LADDER[i]; }
      var pct = Math.max(1.5, Math.min(100, raised * 100 / goal));
      Array.prototype.forEach.call(boxes, function (b) {
        if (b.getAttribute('data-month') !== g.month) return;
        var t = b.querySelector('.spg-goal-t b'), s = b.querySelector('.spg-goal-t span'), bar = b.querySelector('.spg-bar'),
          fill = bar && bar.querySelector('i'), note = b.querySelector('.spg-goal-n');
        if (t) t.textContent = usd(raised) + ' raised';
        if (s) s.textContent = 'of ' + usd(goal) + ' this month';
        if (bar) bar.setAttribute('aria-label', usd(raised) + ' of ' + usd(goal) + ' raised this month');
        if (fill) fill.style.width = pct.toFixed(1) + '%';
        if (note && hit) {                                  // an existing note line only (never a new element)
          var bb = document.createElement('b'); bb.textContent = usd(hit) + ' goal reached.';
          note.textContent = ''; note.appendChild(bb); note.appendChild(document.createTextNode(' New goal: ' + usd(goal) + '.'));
        }
      });
    })
    ['catch'](function () {});
})();
