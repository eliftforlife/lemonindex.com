# /thanks/ (11-07): where Stripe sends people after they donate (Elijah: "I want people to be like, oh, thank you... so people
# don't just feel like they gave money and then nothing happens"). Not in the sitemap and noindex: only donors land here.
# Each Stripe Payment Link's "After payment" setting must point to https://lemonindex.com/thanks/ for this to show.
# exec'd from build.py (uses page, OUT, CONTACT). The page's script is assets/thanks.js (11-25: the CSP blocks inline scripts).
# 11-10: the donor request box needs the lemon-survey Worker's /donor-request route deployed (Elijah). Flip to True after the deploy, then rebuild.
DONOR_REQ_LIVE = False
_REQ_OPEN = '<form class="thx-card thx-req" id="thx-req" novalidate>' if DONOR_REQ_LIVE else '<template id="thx-req-off"><form>'
_REQ_CLOSE = '</form>' if DONOR_REQ_LIVE else '</form></template>'
_TH = f'''<section class="thx">
<img class="thx-ic" src="/assets/icon-180.png" alt="" width="96" height="96">
<h1>Thank you. Really.</h1>
<p class="thx-lede">You just helped keep Lemon free, for you and the next person buying a car.</p>
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
<p class="thx-fine">Donated the wrong amount, or didn&#39;t mean to? Email <a href="mailto:{CONTACT}">{CONTACT}</a> within 14 days for a full refund (unless your shout-out has already been posted). Payments are handled by Stripe, and we never see your card number.</p>
{('<p class="thx-fine">' + DV_MNG + '</p>') if globals().get('DV_MON') and globals().get('DV_MNG') else ''}
</section>
<script src="/assets/thanks.js?v=1125" defer></script>'''
page('/thanks/', 'Thank You for Supporting the Lemon Index', 'Thank you for your donation. It helps keep every Lemon Index car report free, and pays for more cars, images and data.', _TH)
_p = f'{OUT}/thanks/index.html'
_s = open(_p, encoding='utf-8').read()
open(_p, 'w', encoding='utf-8').write(_s.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow"><link rel="canonical"', 1))
