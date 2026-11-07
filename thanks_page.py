# /thanks/ (11-07): where Stripe sends people after they donate (Elijah: "I want people to be like, oh, thank you... so people
# don't just feel like they gave money and then nothing happens"). Not in the sitemap and noindex: only donors land here.
# Each Stripe Payment Link's "After payment" setting must point to https://lemonindex.com/thanks/ for this to show.
# exec'd from build.py (uses page, OUT, CONTACT).
_TH = f'''<section class="thx">
<img class="thx-ic" src="/assets/icon-180.png" alt="" width="96" height="96">
<h1>Thank you. Really.</h1>
<p class="thx-lede">You just helped keep the Lemon Index free, for you and for the next person about to buy a car.</p>
<div class="thx-card">
<h2>What you just paid for</h2>
<ul>
<li>Turning millions of government complaint records into one clear page per car.</li>
<li>No paywall on any report, and no ad trackers following you around.</li>
<li>More cars, more years and more studies, like the ones people ask for in the comments.</li>
</ul>
</div>
<p class="thx-sig">Most people read the reports and move on, and that&#39;s fine. You chipped in, and it means a lot.<br><b>Elijah</b>, who runs the Lemon Index</p>
<div class="thx-go">
<a class="btn" href="/">Check another car</a>
<a class="btn ghost" href="/compare/">Compare two cars</a>
<button class="btn ghost" type="button" id="thx-share">Share the Lemon Index</button>
</div>
<p class="thx-fine">Donated the wrong amount, or didn&#39;t mean to? Email <a href="mailto:{CONTACT}">{CONTACT}</a> within 14 days for a full refund. Payments are handled by Stripe, and we never see your card number.</p>
</section>
<script>
(function () {{
  var b = document.getElementById('thx-share'); if (!b) return;
  b.addEventListener('click', function () {{
    var d = {{ title: 'The Lemon Index', text: 'Check any car for problems before you buy it. Free, from real owner complaints.', url: 'https://lemonindex.com/' }};
    if (navigator.share) {{ navigator.share(d).catch(function () {{}}); return; }}
    try {{ navigator.clipboard.writeText(d.url); b.textContent = 'Link copied'; }} catch (e) {{ b.textContent = 'lemonindex.com'; }}
  }});
}})();
</script>'''
page('/thanks/', 'Thank You for Supporting the Lemon Index', 'Thank you for your donation. It keeps every Lemon Index car report free, with no paywall and no ad trackers.', _TH)
_p = f'{OUT}/thanks/index.html'
_s = open(_p, encoding='utf-8').read()
open(_p, 'w', encoding='utf-8').write(_s.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow"><link rel="canonical"', 1))
