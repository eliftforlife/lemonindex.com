# 11-24 (Elijah: "the whole point of the prices was a button on all car pages that says find a car for your budget, and that page is the
# top 10 most reliable for price ranges like 5k 10k etc"). Run by build.py with exec() (needs YEARS, BYNAME, page, best_img, best_tier,
# cbx_* from best_ui.py). /budget/: for each price range, the 10 models whose most reliable model year fits it, ranked by that year's Lemon
# Index. A year fits a range when its private-seller price at the year's typical miles (the middle of the AI estimate) sits in it.
# Prices are AI estimates (price_box.py / data/price_est.json) and the page says so. BUDGET_HOOK puts the "Find a car for your budget" row
# first in the Overview list of every /cars/<model>/ and /cars/<model>/<year>/ page (after the date hash: page dates don't move).
BUD_SEGS = [('all', 'All'), ('car', 'Cars'), ('suv', 'SUVs'), ('truck', 'Trucks'), ('minivan', 'Minivans')]
BUD_CSS = '<link rel="stylesheet" href="/assets/budget.css?v=3">'
BUD_TOP = 10
# work vans: mostly fleet-sold, so complaints per car sold run unrealistically low; not what a budget shopper means by a car
BUD_SKIP = {'chevrolet-express', 'gmc-savana', 'ford-e-series', 'ford-transit', 'ford-transit-connect', 'mercedes-benz-sprinter', 'ram-promaster', 'ram-promaster-city', 'nissan-nv', 'nissan-nv200'}
BUD_MIN_SOLD = 15000   # a smaller year's score swings on a handful of complaints

def _bud_pool():
    """every scored model year with a price: (budget key, li, fid, year, name, seg, [plo, phi, dlo, dhi], typical miles)"""
    out = []
    for f in YEARS:
        if f['id'] in BUD_SKIP: continue
        c = BYNAME.get(f['name']) or {}
        for v in f['years']:
            if not v.get('ok') or v.get('li') is None or v.get('low') or v['li'] > 100 or (v.get('sold') or 0) < BUD_MIN_SOLD: continue   # most reliable = average or better
            a = PRICEBOX.at_price(f['id'], v['y']); k = PRICEBOX.budget_of(f['id'], v['y'])
            if not a or not k: continue
            mi = PRICEBOX._data()['m'][f['id']]['y'][str(v['y'])][0]
            out.append((k, v['li'], f['id'], v['y'], f['name'], c.get('seg', ''), a, mi))
    return out

def _bud_lists():
    pool = _bud_pool(); L = {}
    for k, *_ in PRICEBOX.BUDGETS:
        for sg, _l in BUD_SEGS:
            by = {}
            for r in pool:
                if r[0] == k and (sg == 'all' or r[5] == sg): by.setdefault(r[2], []).append(r)
            rows = []
            for rs in by.values():   # each model once: its lowest-scored year in this range (newer wins a tie), the other fitting years listed under it
                rs.sort(key=lambda r: (r[1], -r[3])); rows.append((rs[0], [r[3] for r in rs[1:]]))
            L[(k, sg)] = sorted(rows, key=lambda x: (x[0][1], -x[0][3]))[:BUD_TOP]
    return L

def _bud_row(i, r, others):
    k, li, fid, y, nm, sg, a, mi = r
    oth = sorted(set(others))
    more = f' · Also fits: {", ".join(map(str, oth[:4]))}' if oth else ''
    return (f'<li><span class="rk">{i}</span>{best_img(fid, nm)}<div><b><a href="/cars/{fid}/{y}/">{y} {E(nm)}</a></b>'
            f'<small>{PRICEBOX._rng(a[0], a[1])} private · {PRICEBOX._rng(a[2], a[3])} dealer · about {round(mi / 1000):,}K miles{more}</small></div>'
            f'<span class="sc {best_tier(li)}" title="Lemon Index: 100 is the average car, lower is better">{li}</span></li>')

def _budget_page():
    L = _bud_lists(); B = PRICEBOX.BUDGETS; dflt = '10k'
    bch = ''.join(f'<button type="button" class="bud-c" data-b="{k}" aria-pressed="{"true" if k == dflt else "false"}">{E(lab.replace(" to ", "–").replace("Under ", "Under "))}</button>' for k, lo, hi, lab in B)
    sch = ''.join(f'<button type="button" class="bud-c" data-s="{s}" aria-pressed="{"true" if s == "all" else "false"}">{l}</button>' for s, l in BUD_SEGS)
    lists = ''
    for k, lo, hi, lab in B:
        for sg, sl in BUD_SEGS:
            R = L[(k, sg)]
            noun = {'all': 'cars', 'car': 'cars', 'suv': 'SUVs', 'truck': 'trucks', 'minivan': 'minivans'}[sg]
            head = f'<h2 class="bud-h">The {len(R) if len(R) < BUD_TOP else BUD_TOP} most reliable {noun} {"under $5,000" if k == "5k" else "for " + lab.replace(" to ", "–")}</h2>'
            body = ('<ol class="bestl bl2">' + ''.join(_bud_row(i, r, o) for i, (r, o) in enumerate(R, 1)) + '</ol>') if R else '<p class="bud-none">No scored cars in this range yet.</p>'
            lists += f'<section class="bud-l" data-b="{k}" data-s="{sg}"{"" if (k, sg) == (dflt, "all") else " hidden"}>{head}{body}</section>'
    top = {k: L[(k, 'all')] for k, *_ in B}
    def nm3(k): R = top[k][:3]; return ', '.join(f'{r[3]} {r[4]}' for r, _ in R[:-1]) + (f' and {R[-1][0][3]} {R[-1][0][4]}' if len(R) > 1 else (f'{R[0][0][3]} {R[0][0][4]}' if R else ''))
    faq = [(f'What is the most reliable used car {"under $5,000" if k == "5k" else "for " + lab.replace(" to ", "–")}?',
            f'By owner complaints per car sold, the {nm3(k)} come out on top among cars whose typical asking price lands {"under $5,000" if k == "5k" else "between " + lab.replace(" to ", " and ")}.')
           for k, lo, hi, lab in B if top[k]]
    faq.append(('Where do the prices come from?', 'They are Lemon Index estimates made with AI for November 2026, not listings or an appraisal: a fair private-seller price for an average car with a clean title at the mileage most cars of that year have. Check real listings and get an inspection before you buy.'))
    faq.append(('What does the score mean?', 'The Lemon Index of that model year: owner complaints to NHTSA in the first 3 years, per car sold, against the average car. 100 is average and lower is better.'))
    lede = f'The most reliable used cars for every budget. Under $5,000: {nm3("5k")}. $10,000 to $15,000: {nm3("15k")}.'
    body = ('<div class="advp cb cbx bud">' + BUD_CSS + cbx_head('Find a car for your budget.', 'The 10 most reliable used cars in each price range: the model year with the fewest owner complaints that fits, priced at its usual mileage.')
            + f'<section class="cbx-sec cbx-list bud-pick"><div class="bud-row" role="group" aria-label="Budget">{bch}</div><div class="bud-row bud-segs" role="group" aria-label="Type">{sch}</div>{lists}</section>'
            + '<p class="bud-note">Prices are AI estimates (November 2026), not listings: private seller and dealer, average condition, clean title, at the miles shown. Lower score = fewer complaints (100 is the average car).</p>'
            + cbx_faq([(q, f'<p>{E(a)}</p>') for q, a in faq]) + cbx_buy() + cbx_budgets('/budget/', 'What YouTube buyer guides pick')
            + cbx_src('Reliability: the Lemon Index of each model year, NHTSA owner complaints filed in its first 3 years per vehicle sold, against the average car (100). '
                      'A complaint is an owner&#39;s report, not a confirmed defect. Prices: Lemon Index AI estimates (November 2026) of a fair private-seller and dealer price at the year&#39;s typical mileage, '
                      'average condition, clean title; not listings, sales records or an appraisal. Each car shows its lowest-scored year whose private-seller price (middle of the range) fits the budget; '
                      'other years of the same model that also fit are listed under it. Left out: years scored worse than the average car, years with under 15,000 sold or too few complaints to score, and full-size work vans (mostly fleet-sold).')
            + '</div>' + BUD_JS)
    body += share_line('The most reliable used cars for your budget, with prices and complaint scores. Free:', 'Know someone shopping on a budget?')
    page('/budget/', 'Most Reliable Used Cars by Budget: Under $5K, $10K, $15K, $20K+ | The Lemon Index', lede, body,
         ld=[faq_ld([(q, '', a) for q, a in faq])])
    if 'SEO_URLS' in globals(): SEO_URLS.append('/budget/')

BUD_JS = '<script src="/assets/budget.js?v=1" defer></script>'   # CSP: no inline scripts

_budget_page()
