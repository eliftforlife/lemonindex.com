# /thanks/ (11-07): where Stripe sends people after they donate (Elijah: "I want people to be like, oh, thank you... so people
# don't just feel like they gave money and then nothing happens"). Not in the sitemap and noindex: only donors land here.
# Each Stripe Payment Link's "After payment" setting must point to https://lemonindex.com/thanks/ for this to show.
# exec'd from build.py (uses page, OUT, CONTACT).
# 11-10: the donor request box needs the lemon-survey Worker's /donor-request route deployed (Elijah). Flip to True after the deploy, then rebuild.
DONOR_REQ_LIVE = False
_REQ_OPEN = '<form class="thx-card thx-req" id="thx-req" novalidate>' if DONOR_REQ_LIVE else '<template id="thx-req-off"><form>'
_REQ_CLOSE = '</form>' if DONOR_REQ_LIVE else '</form></template>'
_TH = f'''<section class="thx">
<img class="thx-ic" src="/assets/icon-180.png" alt="" width="96" height="96">
<h1>Thank you. Really.</h1>
<p class="thx-lede">You just kept Lemon free and ad-free, for you and the next person buying a car.</p>
{_REQ_OPEN}
<h2>What car or feature should we add next?</h2>
<p>Optional. Donor requests go to the front of the line.</p>
<label for="thx-req-t" class="vh">Your request</label><textarea id="thx-req-t" maxlength="300" rows="3" placeholder="e.g. Every year of the Toyota Tacoma, or engine pages for Ford"></textarea>
<input type="text" id="thx-req-hp" name="website" tabindex="-1" autocomplete="off" class="vh" aria-hidden="true">
<div class="thx-go"><button class="btn" type="submit">Send request</button></div><p class="thx-req-m" role="status"></p>
{_REQ_CLOSE}
<details class="thx-more"><summary>What it pays for</summary><ul><li>More cars and years</li><li>Car images and year sliders</li><li>Engine pages for more brands</li><li>VIN reports and recall alerts</li></ul><p class="thx-note">Planned, no promised dates. Donor requests go first.</p></details>
<div class="thx-go">
<a class="btn" href="/">Check another car</a>
<button class="btn ghost" type="button" id="thx-share">Share the Lemon Index</button>
</div>
<p class="thx-ig">Left a name for a shout-out? Watch our Instagram story, <a href="https://www.instagram.com/lemonindex/" rel="noopener">@lemonindex</a>. <b>Elijah</b></p>
<p class="thx-fine">Donated the wrong amount, or didn&#39;t mean to? Email <a href="mailto:{CONTACT}">{CONTACT}</a> within 14 days for a full refund. Payments are handled by Stripe, and we never see your card number.</p>
</section>
<script>
(function () {{
  var b = document.getElementById('thx-share'); if (!b) return;
  var f = document.getElementById('thx-req');
  if (f) f.addEventListener('submit', function (e) {{
    e.preventDefault(); var t = document.getElementById('thx-req-t').value.trim(), m = f.querySelector('.thx-req-m');
    if (t.length < 2) {{ m.textContent = 'Type a car or a feature first.'; return; }}
    var sid = new URLSearchParams(location.search).get('session_id') || '';
    m.textContent = 'Sending...';
    fetch('https://lemon-survey.elift08.workers.dev/donor-request', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ request: t, session: sid, page: location.pathname, hp: document.getElementById('thx-req-hp').value }}) }})
      .then(function (r) {{ m.textContent = r.ok ? 'Got it. Thank you, it goes to the front of the line.' : (r.status === 429 ? 'Too many sends today. Try again tomorrow.' : 'That didn’t send. Try again in a minute.'); if (r.ok) f.querySelector('textarea').value = ''; }})
      .catch(function () {{ m.textContent = 'That didn’t send. Check your connection and try again.'; }});
  }});
  b.addEventListener('click', function () {{
    var d = {{ title: 'The Lemon Index', text: 'Check any car for problems before you buy it. Free, from real owner complaints.', url: 'https://lemonindex.com/' }};
    if (navigator.share) {{ navigator.share(d).catch(function () {{}}); return; }}
    try {{ navigator.clipboard.writeText(d.url); b.textContent = 'Link copied'; }} catch (e) {{ b.textContent = 'lemonindex.com'; }}
  }});
}})();
</script>'''
page('/thanks/', 'Thank You for Supporting the Lemon Index', 'Thank you for your donation. It keeps every Lemon Index car report free and ad-free, and pays for more cars, images and data.', _TH)
_p = f'{OUT}/thanks/index.html'
_s = open(_p, encoding='utf-8').read()
open(_p, 'w', encoding='utf-8').write(_s.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow"><link rel="canonical"', 1))
