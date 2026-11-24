# 11-24 v2 (Elijah approved the best-for-the-price picks: "a best under 5k 5 car list, a best 5-10k list ... 15 private party then 15
# dealer ... per car group like suv, truck, sedan; supercar different money ranges ... by generations, like 2007-2009, so they can hunt for
# that in their area"; then "approve new higher price bracket" = $10-20K and $20K+). Run by build.py with exec() (needs page, best_img,
# best_tier, cbx_*, _vimg, SCX, share_line, faq_ld, E). Data: data/picks.json from data_picks.py (method in that file).
# /budget/: type chips (Cars, SUVs, Trucks, Minivans, Supercars) x budget chips x Private seller / Dealer = one list of 5 at a time.
# price_box.budget_hook puts the "Find a car for your budget" row first in the Overview list of every car model and year page.
BUD_CSS = '<link rel="stylesheet" href="/assets/budget.css?v=4">'
BUD_JS = '<script src="/assets/budget.js?v=2" defer></script>'   # CSP: no inline scripts
BUD_TYPES = [('car', 'Cars', 'cars'), ('suv', 'SUVs', 'SUVs'), ('truck', 'Trucks', 'trucks'), ('minivan', 'Minivans', 'minivans'), ('super', 'Supercars', 'supercars')]
BUD_KINDS = [('private', 'Private seller'), ('dealer', 'Dealer')]
BUD_PK = json.load(open('data/picks.json', encoding='utf-8'))['lists']
_SCN = {_slg(c['name']): c['name'] for c in SCX}


def _bud_yrs(c): return str(c['y0']) if c['y0'] == c['y1'] else f"{c['y0']}–{c['y1']}"


def _bud_mi(c):
    a, b = round(c['mi'][0] / 1000), round(c['mi'][1] / 1000)
    return f'about {a}K miles' if a == b else f'{a}K–{b}K miles'


def _bud_row(i, c, t):
    if t == 'super':
        nm = _SCN.get(c['id'], c['id']); ph = _vimg(nm)
        img = f'<span class="bph"><img src="{ph["src"]}" alt="{E(nm)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async"></span>' if ph else '<span class="bph"></span>'
        sub = f'{PRICEBOX._rng(*c["p"])} private · {PRICEBOX._rng(*c["d"])} dealer · YouTube buyer score {c["yt"]}'
        return (f'<li><span class="rk">{i}</span>{img}<div><b><a href="/supercars/{c["id"]}/">{_bud_yrs(c)} {E(nm)}</a></b><small>{sub}</small></div></li>')
    twin = f' · Same vehicle as the {E(c["twin"])}' if c.get('twin') else ''
    yt = f' · YouTube buyer score {c["yt"]}' if c.get('yt') is not None else ''
    sub = (f'{E(c["gen"])} · {PRICEBOX._rng(*c["p"])} private · {PRICEBOX._rng(*c["d"])} dealer · {_bud_mi(c)}{yt}{twin}')
    return (f'<li><span class="rk">{i}</span>{best_img(c["id"], c["name"])}<div><b><a href="/cars/{c["id"]}/{c["y0"]}/">{_bud_yrs(c)} {E(c["name"])}</a></b>'
            f'<small>{sub}</small></div><span class="sc {best_tier(c["li"])}" title="Lemon Index of these years: 100 is the average car, lower is better">{c["li"]}</span></li>')


def _bud_names(cs, n=3):
    nm = lambda c: f"{_bud_yrs(c)} {_SCN.get(c['id'], c.get('name', c['id']))}"
    xs = [nm(c) for c in cs[:n]]
    return ', '.join(xs[:-1]) + (' and ' + xs[-1] if len(xs) > 1 else (xs[0] if xs else ''))


def _budget_page():
    dt, db, dk = 'suv', '5to10', 'private'
    tch = ''.join(f'<button type="button" class="bud-c" data-t="{t}" aria-pressed="{"true" if t == dt else "false"}">{l}</button>' for t, l, _ in BUD_TYPES)
    bch = ''.join(f'<button type="button" class="bud-c" data-b="{k}" data-set="{"super" if st == "super" else "reg"}" aria-pressed="{"true" if k == db else "false"}"'
                  f'{" hidden" if st == "super" else ""}>{l}</button>' for st, k, _, l, _lo, _hi in PRICEBOX.BUD_TIERS_ALL)
    kch = ''.join(f'<button type="button" class="bud-c" data-k="{k}" aria-pressed="{"true" if k == dk else "false"}">{l}</button>' for k, l in BUD_KINDS)
    lists = ''; faq = []
    for t, tl, noun in BUD_TYPES:
        for st, k, tk, bl, lo, hi in PRICEBOX.BUD_TIERS_ALL:
            if (st == 'super') != (t == 'super'): continue
            for kk, kl in BUD_KINDS:
                cs = BUD_PK.get(f'{t}|{kk}|{tk}') or []
                where = 'under ' + bl[6:] if bl.startswith('Under ') else ('over ' + bl[5:] if bl.startswith('Over ') else 'for ' + bl.replace(' to ', '–'))
                head = f'<h2 class="bud-h">The {"best " + str(len(cs)) if len(cs) > 1 else "best"} used {noun} {where} <span>({kl.lower()} price)</span></h2>'
                body = ('<ol class="bestl bl2">' + ''.join(_bud_row(i, c, t) for i, c in enumerate(cs, 1)) + '</ol>') if cs else '<p class="bud-none">None of our scored generations fit this range yet.</p>'
                if len(cs) < 5 and cs: body += f'<p class="bud-none">Only {len(cs)} {"generation scores" if len(cs) == 1 else "generations score"} well enough at this price.</p>'
                lists += f'<section class="bud-l" data-t="{t}" data-b="{k}" data-k="{kk}"{"" if (t, k, kk) == (dt, db, dk) else " hidden"}>{head}{body}</section>'
                if kk == 'private' and cs:
                    faq.append((f'What is the best used {noun[:-1] if noun.endswith("s") else noun} {where}?',
                                f'From a private seller, the {_bud_names(cs)} rank highest among {noun} that usually sell {where.replace("for ", "")}'
                                + ('' if t == 'super' else ': fewer owner complaints than the average car, and YouTube buyer guides rate them well') + '.'))
    faq.append(('Why years and not one model year?', 'Each pick is a run of model years from one generation, so you can search for any of them near you. Every year in the run scores as well as or better than the average car.'))
    faq.append(('Where do the prices come from?', 'They are Lemon Index estimates made with AI for November 2026, not listings or an appraisal: a fair private-seller and dealer price for an average car with a clean title at the mileage most cars of those years have. Check real listings and get an inspection before you buy.'))
    faq.append(('How are the picks ranked?', 'Mostly by reliability: the Lemon Index of those years (owner complaints to NHTSA in the first 3 years, per car sold; 100 is the average car, lower is better). Then by how well YouTube buyer guides and owner reviews rate those years, and a little extra for a longer run of good years. Supercars have too few complaints to score, so they are ranked by YouTube buyer score and price only.'))
    c5 = BUD_PK.get('car|private|u5') or []; s10 = BUD_PK.get('suv|private|5-10') or []
    lede = f'The 5 best used cars, SUVs, trucks and minivans for every budget. Under $5,000: {_bud_names(c5, 2)}. SUVs for $5,000–10,000: {_bud_names(s10, 2)}.'
    body = ('<div class="advp cb cbx bud">' + BUD_CSS + cbx_head('Find a car for your budget.', 'The 5 best used picks in every price range: model years with fewer owner complaints than the average car that YouTube buyer guides rate well, priced at their usual mileage.')
            + f'<section class="cbx-sec cbx-list bud-pick"><div class="bud-row" role="group" aria-label="Type">{tch}</div><div class="bud-row bud-segs" role="group" aria-label="Budget">{bch}</div>'
            + f'<div class="bud-row bud-segs" role="group" aria-label="Price from">{kch}</div>{lists}</section>'
            + '<p class="bud-note">Prices are AI estimates (November 2026), not listings: average condition, clean title, at the miles shown. Private seller prices are usually lower than a dealer&#39;s. Lower score = fewer complaints (100 is the average car).</p>'
            + cbx_faq([(q, f'<p>{E(a)}</p>') for q, a in faq]) + cbx_buy() + cbx_budgets('/budget/', 'What YouTube buyer guides pick')
            + cbx_src('Reliability: the Lemon Index of each model year, NHTSA owner complaints filed in its first 3 years per vehicle sold, against the average car (100). '
                      'A complaint is an owner&#39;s report, not a confirmed defect. YouTube buyer score: how YouTube buyer guides and owner reviews rate those years (Lemon Index analysis of video titles and transcripts). '
                      'Prices: Lemon Index AI estimates (November 2026) of a fair private-seller and dealer price at the years&#39; typical mileage, average condition, clean title; not listings, sales records or an appraisal. '
                      'A pick is a run of consecutive model years in one generation, each scored at or better than the average car, with 15,000+ sold each year, whose price (middle of the range) fits the budget. '
                      'Ranked 60% reliability, 40% YouTube buyer score, plus a little for a longer run. Twins sold under two brands count once. Left out: full-size work vans (mostly fleet-sold). Supercars: YouTube buyer score and price only.')
            + '</div>' + BUD_JS)
    body += share_line('The best used cars for your budget, with prices and complaint scores. Free:', 'Know someone shopping on a budget?')
    page('/budget/', 'Best Used Cars for Your Budget: Under $5K, $10K, $20K+ | The Lemon Index', lede, body,
         ld=[faq_ld([(q, '', a) for q, a in faq])])
    if 'SEO_URLS' in globals(): SEO_URLS.append('/budget/')


_budget_page()
