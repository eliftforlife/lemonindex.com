# 11-24 v2 (Elijah approved the best-for-the-price picks: "a best under 5k 5 car list, a best 5-10k list ... 15 private party then 15
# dealer ... per car group like suv, truck, sedan; supercar different money ranges ... by generations, like 2007-2009, so they can hunt for
# that in their area"; then "approve new higher price bracket" = $10-20K and $20K+). Run by build.py with exec() (needs page, best_img,
# best_tier, cbx_*, _vimg, SCX, share_line, faq_ld, E). Data: data/picks.json from data_picks.py (method in that file).
# /budget/: type chips (Cars, SUVs, Trucks, Minivans, Supercars) x budget chips x Private seller / Dealer = one list of 5 at a time.
# price_box.budget_hook puts the "Find a car for your budget" row first in the Overview list of every car model and year page.
BUD_CSS = '<link rel="stylesheet" href="/assets/budget.css?v=11">'
BUD_JS = '<script src="/assets/budget.js?v=4" defer></script>'   # CSP: no inline scripts
BUD_TYPES = [('car', 'Cars', 'cars'), ('suv', 'SUVs', 'SUVs'), ('truck', 'Trucks', 'trucks'), ('minivan', 'Minivans', 'minivans'), ('super', 'Supercars', 'supercars')]
# 11-24 Eli mobile pass: short chip labels so the budget row fits a phone (the hidden h2 and the FAQ keep the full amounts)
BUD_SHORT = {'u2': 'Under $2K', 'u5': 'Under $5K', '5to10': '$5–10K', '10to20': '$10–20K', '20up': '$20K+', 'u100': 'Under $100K', '100to200': '$100–200K', '200up': '$200K+'}
BUD_KINDS = [('private', 'Private seller'), ('dealer', 'Dealer')]
BUD_PK = json.load(open('data/picks.json', encoding='utf-8'))['lists']
_SCN = {_slg(c['name']): c['name'] for c in SCX}


def _bud_yrs(c): return str(c['y0']) if c['y0'] == c['y1'] else f"{c['y0']}–{c['y1']}"


def _bud_mi(c):
    a, b = round(c['mi'][0] / 1000), round(c['mi'][1] / 1000)
    return f'about {a}K miles' if a == b else f'{a}K–{b}K miles'


def _bud_card(c, t, kk, k=''):
    # 11-24 Eli pass v2 (Elijah: "make it look more like our home page: car image sizes and text amount on that look great"): the home page's own
    # car card (build.py mcard: a.mc in a .mg grid). Picture, years + car, ONE price (the private/dealer chip's), the score in the corner.
    # Generation, the other price, miles and the YouTube score live on the car page the card opens.
    pr = c['p'] if kk == 'private' else c['d']
    if t == 'super':
        nm = _SCN.get(c['id'], c['id']); ph = _vimg(nm); href = f'/supercars/{c["id"]}/'
        im = f'<img src="{ph["src"]}" alt="{E(nm)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async">' if ph else ''
        sc = ''
    else:
        nm = c['name']; href = f'/cars/{c["id"]}/{c["y0"]}/'
        # 11-25 (Elijah: "do year specific images"): the AI illustration of the run's middle year when there is one (a 2004 Altima, not today's)
        yi = next((YSL.AIY.get(c['id'], {}).get(str(y)) for y in sorted(range(c['y0'], c['y1'] + 1), key=lambda y: abs(y - (c['y0'] + c['y1']) / 2)) if YSL.AIY.get(c['id'], {}).get(str(y))), None)
        if yi: im = f'<img src="{yi["src"]}" alt="{c["y0"]} {E(nm)}" width="{yi["w"]}" height="{yi["h"]}" loading="lazy" decoding="async">'
        else:
            bi = best_img(c['id'], nm); im = bi[18:-7] if bi.startswith('<span class="bph">') and bi.endswith('</span>') else ''
        sc = f'<span class="{"good" if c["li"] < 100 else "bad"}" title="Lemon Index of these years: 100 is the average car, lower is better">{c["li"]}</span>'
    return (f'<a class="mc" href="{href}"><span class="mc-p">{im}</span><b>{_bud_yrs(c)} {E(nm)}</b>'
            f'<small class="mc-k bud-pr">{"From $" + format(pr[0], ",") if k == "u2" else PRICEBOX._rng(*pr)}</small>{sc}</a>')   # 11-25: under $2K shows the low end


def _bud_names(cs, n=3):
    nm = lambda c: f"{_bud_yrs(c)} {_SCN.get(c['id'], c.get('name', c['id']))}"
    xs = [nm(c) for c in cs[:n]]
    return ', '.join(xs[:-1]) + (' and ' + xs[-1] if len(xs) > 1 else (xs[0] if xs else ''))


def _budget_page():
    dt, db, dk = 'suv', '5to10', 'private'
    tch = ''.join(f'<button type="button" class="bud-c" data-t="{t}" aria-pressed="{"true" if t == dt else "false"}">{l}</button>' for t, l, _ in BUD_TYPES)
    bch = ''.join(f'<button type="button" class="bud-c" data-b="{k}" data-set="{"super" if st == "super" else "reg"}" aria-pressed="{"true" if k == db else "false"}"'
                  f'{" hidden" if st == "super" else ""}>{BUD_SHORT.get(k, l)}</button>' for st, k, _, l, _lo, _hi in PRICEBOX.BUD_TIERS_ALL)
    kch = ''.join(f'<button type="button" class="bud-c" data-k="{k}" aria-pressed="{"true" if k == dk else "false"}">{l}</button>' for k, l in BUD_KINDS)
    lists = ''; faq = []
    for t, tl, noun in BUD_TYPES:
        tops = []   # FAQ: one question per type, the #1 private-seller pick in each budget
        for st, k, tk, bl, lo, hi in PRICEBOX.BUD_TIERS_ALL:
            if (st == 'super') != (t == 'super'): continue
            for kk, kl in BUD_KINDS:
                if k == 'u2' and kk == 'dealer': continue   # 11-25: under $2,000 is private seller only (budget.js hides the Dealer chip)
                cs = BUD_PK.get(f'{t}|{kk}|{tk}') or []
                where = 'under ' + bl[6:] if bl.startswith('Under ') else ('over ' + bl[5:] if bl.startswith('Over ') else 'for ' + bl.replace(' to ', '–'))
                head = f'<h2 class="bud-vh">Best used {noun} {where} ({kl.lower()} price)</h2>'   # the chips already say it on screen
                body = (f'<div class="mg bud-g{" bud-sup" if t == "super" else ""}">' + ''.join(_bud_card(c, t, kk, k) for c in cs) + '</div>') if cs else '<p class="bud-none">None of our scored picks fit this price yet.</p>'
                # short list: one line instead of two (the page's price note hides while this list shows, budget.css)
                if k == 'u2' and not cs: body = f'<p class="bud-none">No {noun} we would trust under $2,000. Try Under $5K.</p>'
                elif k == 'u2': body += ('<p class="bud-none">' + ('At this price you are buying an older car with high miles, from a private seller. These are the ones owners report the fewest problems with. '
                                      'The low end of each price is a car with more miles or wear: check it before you pay.' if cs else 'No ' + noun + ' we would trust at this price.') + '</p>')
                elif len(cs) < 5 and cs: body += f'<p class="bud-none">Only {len(cs)} {"pick scores" if len(cs) == 1 else "picks score"} well at this price. Prices are AI estimates, not listings.</p>'
                lists += f'<section class="bud-l" data-t="{t}" data-b="{k}" data-k="{kk}"{"" if (t, k, kk) == (dt, db, dk) else " hidden"}>{head}{body}</section>'
                if kk == 'private' and cs: tops.append(f'{where.replace("for ", "")}, the {_bud_names(cs, 1)}')
        if tops:
            one = noun[:-1] if noun.endswith('s') else noun
            faq.append((f'What is the best used {one} ' + ('for the money?' if t == 'super' else 'on a budget?'),
                        'Our top private-seller picks: ' + '; '.join(tops) + '. '
                        + ('Supercars have too few complaints to score, so they are ranked by YouTube buyer score and price.' if t == 'super'
                           else 'Each has fewer owner complaints than the average car, and YouTube buyer guides rate it well.')))
    # 11-24 Eli mobile pass: ~22 questions -> 7 (one per type + how picked + prices); 'Why years' and 'How ranked' merged
    faq.append(('How are the picks chosen?', 'Mostly by reliability: the Lemon Index of those years (owner complaints to NHTSA in the first 3 years, per car sold; 100 is the average car, lower is better), then by how YouTube buyer guides rate them. '
                'Each pick is a run of model years from one generation, every one scoring as well as or better than the average car, so you can search for any of them near you.'))
    faq.append(('Can you get a reliable car for under $2,000?', 'Yes, from a private seller: dealers rarely sell cars this cheap. Expect a car about 20 years old with high miles. '
                'Our under-$2,000 list shows the models and years owners report the fewest problems with, priced by the low end of what they sell for. Check any car before you pay.'))
    faq.append(('Where do the prices come from?', 'They are Lemon Index estimates made with AI for November 2026, not listings or an appraisal: a fair private-seller and dealer price for an average car with a clean title at the mileage most cars of those years have. Check real listings and get an inspection before you buy.'))
    c5 = BUD_PK.get('car|private|u5') or []; s10 = BUD_PK.get('suv|private|5-10') or []
    lede = f'The 5 best used cars, SUVs, trucks and minivans for every budget. Under $5,000: {_bud_names(c5, 2)}. SUVs for $5,000–10,000: {_bud_names(s10, 2)}.'
    body = ('<div class="advp cb cbx bud">' + BUD_CSS + cbx_head('Find a car for your budget.', 'The 5 best used picks in every price range.')
            + f'<section class="cbx-sec cbx-list bud-pick"><div class="bud-row" role="group" aria-label="Type">{tch}</div><div class="bud-bar"><div class="bud-row bud-segs" role="group" aria-label="Budget">{bch}</div>'
            + f'<div class="bud-kind" role="group" aria-label="Price from">{kch}</div></div>{lists}'
            + '<p class="bud-note">Prices are AI estimates for November 2026, not listings.<span class="bud-sn"> Score: lower is better (100 is the average car).</span></p><p class="bud-note">Insurance is part of the real monthly cost: <a href="/insurance/">compare insurers for you</a>.</p></section>'
            + cbx_faq([(q, f'<p>{E(a)}</p>') for q, a in faq]) + cbx_buy()
            + cbx_src('Reliability: the Lemon Index of each model year, NHTSA owner complaints filed in its first 3 years per vehicle sold, against the average car (100). '
                      'A complaint is an owner&#39;s report, not a confirmed defect. YouTube buyer score: how YouTube buyer guides and owner reviews rate those years (Lemon Index analysis of video titles and transcripts). '
                      'Prices: Lemon Index AI estimates (November 2026) of a fair private-seller and dealer price at the years&#39; typical mileage, average condition, clean title; not listings, sales records or an appraisal. '
                      'A pick is a run of consecutive model years in one generation, each scored at or better than the average car, with 15,000+ sold each year, whose price (middle of the range) fits the budget; under $2,000 (private sellers only), the low end of the range. '
                      'Ranked 60% reliability, 40% YouTube buyer score, plus a little for a longer run. Twins sold under two brands count once. Left out: full-size work vans (mostly fleet-sold). Supercars: YouTube buyer score and price only.')
            + '</div>' + BUD_JS)
    body += share_line('The best used cars for your budget, with prices and complaint scores. Free:', 'Know someone shopping on a budget?')
    page('/budget/', 'Best Used Cars for Your Budget: Under $2K, $5K, $10K+ | The Lemon Index', lede, body,
         ld=[faq_ld([(q, '', a) for q, a in faq])])
    if 'SEO_URLS' in globals(): SEO_URLS.append('/budget/')


_budget_page()
