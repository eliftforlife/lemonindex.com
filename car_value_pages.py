# 11-26 (Elijah: "a money evaluator on the site in the money section in main menu where you put car year model and trim and condition low
# medium or great and title status clean or salvage and then it says price range of what it's worth, even it's just estimate"):
# /car-value/, "What's this car worth?" (11-26 Elijah: "this" fits buyers and sellers). Make -> model -> year (-> trim, ~50 models), optional miles, condition (Rough / Average / Great)
# and title (Clean / Salvage) -> one big private-sale range, the dealer range under it. Run by build.py with exec() after budget_pages.py
# (needs page, faq_ld, E, BASE, SEO_URLS). Data: assets/carvalue.json from data_car_value.py (the year-page price box's AI estimates).
# The math runs in assets/carvalue.js (no inline scripts: CSP); tools/check_car_value.py checks it against prices_brackets.price_at().
# Rules of thumb on top of the data (stated in the method note and FAQ): Rough x0.80, Great x1.08 (never above the price-new caps),
# salvage or rebuilt title = low x0.60 / high x0.80 of the clean range. price_box.value_hook adds "Value this car" to every price box.
CV_CSS = '<link rel="stylesheet" href="/assets/carvalue.css?v=1">'
CV_JS = '<script src="/assets/carvalue.js?v=1" defer></script>'
CV_D = json.load(open('assets/carvalue.json', encoding='utf-8'))
CV_N = len(CV_D['m'])
CV_FAQ = [
    ('How is a car’s value worked out?',
     'We start from our estimate of a fair private-sale price for that model year at the miles most of them have, then adjust it for the miles, '
     'trim, condition and title. The numbers are Lemon Index AI estimates for ' + CV_D['date'] + ', not listings, sales records or an appraisal.'),
    ('What do Rough, Average and Great mean?',
     'Average is a normal car for its age: some wear, everything works. Rough needs work, like dents, a worn interior, warning lights or repairs due, '
     'and comes out about 20% lower. Great is clean inside and out with service records and nothing to fix, about 8% higher, never more than it cost new.'),
    ('How much is a car with a salvage or rebuilt title worth?',
     'Usually far less than the same car with a clean title, and prices vary a lot with the damage and the repair. We show 40% under the low end '
     'to 20% under the high end of the clean range. A rebuilt title counts as salvage here.'),
    ('Is this what a dealer will pay me?',
     'No. The dealer price is what a lot typically asks for a car like this one. A trade-in offer is usually lower than the private-sale range, '
     'because the dealer has to resell the car.'),
]


def _cv_page():
    mks = sorted({o['b'] for o in CV_D['m'].values()}, key=str.lower)
    mk_opts = ''.join(f'<option value="{E(b)}">{E(b)}</option>' for b in mks)
    # Eli phone pass: no label rows over the two bars (the buttons say it), so the price lands higher on a phone
    seg = lambda k, lab, opts, d: (f'<div class="cv-seg" role="group" aria-label="{lab}">'
                                   + ''.join(f'<button type="button" data-{k}="{v}" aria-pressed="{"true" if v == d else "false"}">{t}</button>' for v, t in opts) + '</div>')
    form = ('<form class="cv-f" id="cvf" autocomplete="off" novalidate action="/car-value/" method="get">'
            '<div class="cv-car"><label class="cv-fld"><span class="cv-lab">Make</span><select id="cv-mk"><option value="">Pick a make</option>' + mk_opts + '</select></label>'
            '<label class="cv-fld"><span class="cv-lab">Model</span><select id="cv-m" name="m" disabled><option value="">Model</option></select></label>'
            '<label class="cv-fld"><span class="cv-lab">Year</span><select id="cv-y" name="y" disabled><option value="">Year</option></select></label>'
            '<label class="cv-fld cv-trim" hidden><span class="cv-lab">Trim</span><select id="cv-t" name="t"><option value="">Not sure</option></select></label>'
            '<label class="cv-fld cv-mi"><span class="cv-lab">Miles <small>optional</small></span><input id="cv-mi" name="mi" type="text" inputmode="numeric" maxlength="7" placeholder="Typical"></label></div>'
            + seg('c', 'Condition', [('rough', 'Rough'), ('average', 'Average'), ('great', 'Great')], 'average')
            + seg('ti', 'Title', [('clean', 'Clean title'), ('salvage', 'Salvage title')], 'clean') + '</form>')
    out = ('<div class="cv-out" id="cvo" aria-live="polite"><p class="cv-empty">Pick a make, model and year.</p></div>'
           '<noscript><p class="cv-empty">This tool needs JavaScript. Each car&#39;s year page has its price by mileage.</p></noscript>')
    faq = ('<section class="cbx-sec cv-faq"><h2>How it works</h2><div class="cbx-qas">'
           + ''.join(f'<details class="cbx-qa"><summary>{E(q)}</summary><div class="cbx-a"><p>{E(a)}</p></div></details>' for q, a in CV_FAQ) + '</div></section>')
    body = ('<div class="advp cb cbx cv">' + '<link rel="stylesheet" href="/assets/cb.css?v=2">' + CV_CSS
            + '<header class="advh1 cbx-h"><h1>What&#39;s this car worth?</h1>'
            + f'<p class="cbx-line cv-ans">A free estimate of what a used car sells for, buying or selling. {CV_N} models, adjusted for miles, condition and title.</p></header>'
            + '<section class="cbx-sec cv-pick"><div class="cv-grid">' + form + out + '</div></section>' + faq + '</div>' + CV_JS)
    body += share_line('What is this car worth? Free estimate by model, year, miles and condition:', 'Know someone buying or selling a car?')
    desc = (f'Buying or selling? Free used car value estimate for {CV_N} models: pick the make, model, year, miles, condition and title to see a private-sale and dealer price range. '
            'No sign-up.')
    ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": "What's this car worth? Car value estimator", "url": BASE + '/car-value/',
           "applicationCategory": "FinanceApplication", "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
           "description": "Estimates a used car's private-sale and dealer price from its make, model, year, trim, miles, condition and title. AI estimates, not an appraisal. No sign-up."},
          faq_ld([(q, '', a) for q, a in CV_FAQ])]
    page('/car-value/', "What's This Car Worth? Free Car Value Estimate", desc, body, ld=ld)
    if 'SEO_URLS' in globals(): SEO_URLS.append('/car-value/')


_cv_page()
