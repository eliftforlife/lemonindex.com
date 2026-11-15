# Best-of and statistics pages (11-06, SEO plan). Run by build.py with exec(). Every number comes from our own data; nothing here is hand-typed.
SEO_URLS = []
YT_SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\yt'
exec(open('best_ui.py', encoding='utf-8').read())   # 11-12 (Elijah): shared /best/ pieces: one-line hero, tap-to-open answers, VIN box, budget cards
exec(open('teen_page.py', encoding='utf-8').read())   # 11-12 /best/safest-cars-for-teens/ (sets TEEN_CARD for the /best/ hub below)
# 11-12 (Linda: the under-$10K list showed "–" for the Miata and Silverado): buyer-guide names ("Chevy Silverado", "VW Golf / GTI",
# "Ford F-150") resolve to our model, its score and its live page; a model we don't score still links its page and says why there's no score
def _bu_pages():
    L = [(f['name'], car_href(f['id']) or f'/cars/{f["id"]}/') for f in YEARS]
    for p_ in __import__('glob').glob('data/perf/*.json'):
        if not p_.endswith('.auto.json'):
            d_ = _load(p_); L.append((d_['name'], d_.get('page') or f'/cars/{d_["slug"]}/'))
    for f_ in ('data/extra_models.json', 'data/extra_models_new.json'):
        for m in (_load(f_) if os.path.exists(f_) else {}).values(): L.append((m['name'], f'/cars/{m["id"]}/'))
    L += [(c['name'], f'/electric/{c["slug"]}/') for c in EVX]
    return L
_BU_PAGES = _bu_pages()
def bu_resolve(model):
    nm = re.sub(r'^VW ', 'Volkswagen ', re.sub(r'^Chevy ', 'Chevrolet ', model)).split(' / ')[0].strip()
    nm = {'Ford F-150': 'Ford F-Series'}.get(nm, nm)
    c = BYNAME.get(nm)
    if c: return c, car_href(c['id'])
    tk = set(re.findall(r'[a-z0-9]+', nm.lower()))
    return None, next((u for n_, u in _BU_PAGES if tk <= set(re.findall(r'[a-z0-9]+', n_.lower()))), '')
# 11-13 v2 (Elijah: "bars or charts", best_ui.py): the most-reliable lists and the budget lists, visual first
def rel_vis(T, W, slug):
    PAGEID = {f['id'] for f in YEARS}
    mx = cbx_scale([c['li'] for c in T]); mw = cbx_scale([c['li'] for c in W])
    link = lambda c: f'<a href="/cars/{c["id"]}/">{E(c["name"])}</a>' if c['id'] in PAGEID else E(c['name'])
    def card(i, c):
        iss = c.get('issues') or []
        w_ = cbx_times(c['li']); why = f'{w_[0].upper()}{w_[1:]} (model years {E(c["years"].replace("-", "–"))}).'
        ms = cbx_meter('Complaints', c['li'], mx, c['li'], best_tier(c['li']), unit='Lemon Index')
        if iss: ms += cbx_meter(E(iss[0][0][0].upper() + iss[0][0][1:]), iss[0][1], 100, f'{iss[0][1]}%', 'gray', avg=False, unit='of complaints')
        return cbx_card(f'{slug}-{i}', i, best_img(c['id'], c['name']), link(c), why, ms)
    best = (f'<section class="cbx-sec cbx-list"><h2>Fewest complaints</h2>'
            + cbx_chart([(f'#{slug}-{i}', f'<b>{i}</b> {E(c["name"])}', c['li'], c['li'], best_tier(c['li'])) for i, c in enumerate(T, 1)], mx,
                        'Lemon Index: shorter bar = fewer complaints per car sold. Dashed line = the average car (100). Tap a car.')
            + '<ol class="cbx-cards">' + ''.join(card(i, c) for i, c in enumerate(T, 1)) + '</ol></section>')
    worst = (f'<section class="cbx-sec cbx-list"><h2>Most complaints</h2>'
             + cbx_chart([(f'/cars/{c["id"]}/' if c['id'] in PAGEID else '#', f'<b>{i}</b> {E(c["name"])}', c['li'], c['li'], best_tier(c['li'])) for i, c in enumerate(W, 1)], mw,
                         'Lemon Index: longer bar = more complaints per car sold. Dashed line = the average car (100).', title='The other end') + '</section>')
    return best + worst
def bu_ylink(c, txt):
    """11-13 (nav review): the model years the videos picked link to those year pages"""
    F = FY.get(c['id']) if c else None
    if not F: return E(txt)
    have = {v['y'] for v in F['years']}
    return re.sub(r'(?:19|20)\d\d', lambda m: f'<a href="{CARU(F, int(m.group()))}">{m.group()}</a>' if int(m.group()) in have else m.group(), E(txt))
def bu_vis(R, d, span):
    nv = d['videos']; mx = cbx_scale([c['li'] for _, c, _ in R if c] or [100]); mv = max(r['videos'] for r, _, _ in R) * 1.1   # bars compare the picks with each other
    def card(i, r, c, u):
        nm = c['name'] if c else r['model']; sp = span(r)
        why = f'Picked in {r["videos"]} of {nv} buyer&#39;s-guide videos' + (f', most often the {bu_ylink(c, sp.split(" (")[0])} model years' if sp else '') + '. '
        why += (cbx_times(c['li'])[0].upper() + cbx_times(c['li'])[1:] + ' (2010–2022).') if c else ('No Lemon Index yet: see its problems and recalls.' if u else 'We don&#39;t cover this model yet.')
        ms = cbx_meter('Picked in', r['videos'], mv, f'{r["videos"]} of {nv}', 'pick', avg=False, unit='videos')
        if c: ms += cbx_meter('Complaints', c['li'], mx, c['li'], best_tier(c['li']), unit='Lemon Index')
        return cbx_card(f'bu-{i}', i, best_img(c['id'] if c else None, nm), f'<a href="{u}">{E(nm)}</a>' if u else E(nm), why, ms)
    chart = cbx_chart([(f'#bu-{i}', f'<b>{i}</b> {E(c["name"] if c else r["model"])}', r['videos'], r['videos'], 'pick') for i, (r, c, u) in enumerate(R, 1)], mv,
                      f'How many of the {nv} buyer&#39;s-guide videos picked each car. Tap a car.', avg=False)
    return f'<section class="cbx-sec cbx-list"><h2>Most-picked</h2>{chart}<ol class="cbx-cards">' + ''.join(card(i, r, c, u) for i, (r, c, u) in enumerate(R, 1)) + '</ol></section>'
def _seo_pages():
    PAGEID = {c['name']: c['id'] for c in CARS}; HAS = {f['id'] for f in YEARS}
    def carlink(c): return f'<a href="/cars/{c["id"]}/">{E(c["name"])}</a>' if c['id'] in HAS else E(c['name'])
    # 11-10 v2 (design audit): every ranking row gets the car's AI illustration and a tier-colored score (helpers in gap_pages.py)
    bimg, tier = best_img, best_tier
    def rows(L, sub):
        return '<ol class="bestl bl2">' + ''.join(f'<li><span class="rk">{i}</span>{bimg(c["id"], c["name"])}<div><b>{carlink(c)}</b><small>{sub(c)}</small></div><span class="sc {tier(c["li"])}">{c["li"]}</span></li>' for i, c in enumerate(L, 1)) + '</ol>'
    top = lambda c: E(', '.join(f'{p} {k}%' for p, k in c['issues'][:2])) if c.get('issues') else ''
    SEG = [('cars', 'car', 'cars'), ('suvs', 'suv', 'SUVs'), ('trucks', 'truck', 'trucks'), ('minivans', 'minivan', 'minivans')]
    cards = []
    for slug, sg, nm in SEG:
        L = sorted([c for c in CARS if c['seg'] == sg and c['sold'] >= 150000], key=lambda c: c['li']); T = L[:15]; W = L[::-1][:10]
        lede = f'The most reliable {nm} by owner complaints per vehicle sold are the {T[0]["name"]}, {T[1]["name"]} and {T[2]["name"]}. A score of 100 is the average car, and lower is better.'
        faq = [(f'What is the most reliable {nm[:-1]}?', f'By owner complaints per vehicle sold, model years 2010 to 2022, the {T[0]["name"]} ranks first with a Lemon Index of {T[0]["li"]}.'), (f'Which {nm} get the most complaints?', f'The {W[0]["name"]} and {W[1]["name"]} drew the most complaints per vehicle sold among popular {nm}.')]
        body = ('<div class="advp cb cbx">' + cbx_head(f'The most reliable {nm}, ranked.', f'Popular {nm} ranked by owner complaints per car sold, model years 2010 to 2022.')
                + rel_vis(T, W, slug)
                + cbx_faq([(q, f'<p>{E(a)}</p>') for q, a in faq]) + cbx_buy() + cbx_budgets()
                + cbx_src(f'{E(lede)} Lemon Index: NHTSA owner complaints filed in a model year&#39;s first 3 years, per vehicle sold, against the average car. Model years 2010 to 2022, models with 150,000 or more sold. Complaints are owner reports, not proof of a defect.') + '</div>')
        body += share_line(f'The most reliable {nm}, ranked by owner complaints. #1 is the {T[0]["name"]}. Free list:')
        page(f'/best/most-reliable-{slug}/', f'Most Reliable {nm[0].upper() + nm[1:]}, Ranked by Owner Complaints | The Lemon Index', lede, body, ld=[faq_ld([(q, '', a) for q, a in faq])]); SEO_URLS.append(f'/best/most-reliable-{slug}/'); cards.append((f'/best/most-reliable-{slug}/', f'Most reliable {nm}'))
    for k, label in (('5k', '$5,000'), ('10k', '$10,000'), ('15k', '$15,000'), ('20k', '$20,000')):
        p = os.path.join(YT_SRC, f'best-used-{k}', 'consensus.json')
        if not os.path.exists(p): continue
        d = json.load(open(p, encoding='utf-8')); R = []
        py_ = os.path.join(YT_SRC, f'best-used-{k}', 'years.json'); YRS = json.load(open(py_, encoding='utf-8')) if os.path.exists(py_) else {}
        for r in d['ranking'][:20]:
            c, u = bu_resolve(r['model']); R.append((r, c, u))
        R = R[:15]   # 11-12 (Linda): the intro only names cars that are in the list
        def span(r):   # the model years the videos named most often for this budget (data/yt/best-used-<k>/years.json)
            sp = (YRS.get(r['model']) or {}).get('spans') or []
            if sp: s_, n_ = max(sp, key=lambda x: x[1]); return f'{s_.replace("-", "–")} ({n_} video{"s" if n_ > 1 else ""})'
            ys_ = (YRS.get(r['model']) or {}).get('years') or []
            return ', '.join(y_ for y_, _ in sorted(ys_, key=lambda x: -x[1])[:2]) if ys_ else ''
        def bu_row(i, r, c, u):
            nm = c['name'] if c else r['model']; sp = span(r)
            link = f'<a href="{u}">{E(nm)}</a>' if u else E(nm)
            why = '' if c else (' · No Lemon Index yet: see its problems and recalls' if u else ' · No Lemon Index: we don&#39;t cover this model yet')
            return (f'<li><span class="rk">{i}</span>{bimg(c["id"] if c else None, nm)}<div><b>{link}</b><small>{("Years picked most: " + sp + " · ") if sp else ""}{r["videos"]} of {d["videos"]} videos{why}</small></div>'
                    f'<span class="sc {tier(c["li"]) if c else ""}">{c["li"] if c else "–"}</span></li>')
        lis = '<ol class="bestl bl2">' + ''.join(bu_row(i, r, c, u) for i, (r, c, u) in enumerate(R, 1)) + '</ol>'
        safe = sorted([x for x in R if x[1] and x[1]['li'] < 100], key=lambda x: x[1]['li'])[:3]
        nm3 = [x[1]['name'] if x[1] else x[0]['model'] for x in R[:3]]
        lede = f'In {d["videos"]} YouTube videos on the best used cars under {label}, the most-picked are the {nm3[0]}, {nm3[1]} and {nm3[2]}.' + (f' Of the {len(R)} picks below, the {safe[0][1]["name"]} has the fewest owner complaints.' if safe else '')
        faq = [(f'What are the best used cars under {label}?', lede), ('Where do these picks come from?', f'From {d["videos"]} YouTube buyer&#39;s guide videos with {d["views"] / 1e6:.1f}M views. A pick counts when the model is in the title or named in the video.'),
               ('Does this list show prices?', 'No. These are buyer-guide picks, not prices: check the exact model year and price before you buy.')]
        body = ('<div class="advp cb cbx">' + cbx_head(f'Best used cars under {label}.', f'The cars {d["videos"]} YouTube buyer&#39;s guides pick most, with each one&#39;s owner-complaint score.')
                + bu_vis(R, d, span)
                + cbx_faq([(q, f'<p>{a if q.startswith(("Where", "Does")) else E(a)}</p>') for q, a in faq]) + cbx_buy() + cbx_budgets(f'/best/used-cars-under-{k[:-1]}000/', 'Other budgets')
                + cbx_src(f'Picks come from {d["videos"]} YouTube videos with {d["views"] / 1e6:.1f}M views. A pick counts when the model is in the title or named in the video. &#34;Years picked most&#34; = the model-year range the most videos named for this budget; open the car for each year&#39;s own score. Shopping for a new driver? See the <a href="/best/safest-cars-for-teens/">safest used cars for teens</a>.') + '</div>')
        body += share_line(f'Best used cars under {label}: what {d["videos"]} buyer guide videos pick, with complaint scores. Free:', 'Know someone shopping on a budget?')
        page(f'/best/used-cars-under-{k[:-1]}000/', f'Best Used Cars Under {label}: What {d["videos"]} Videos Pick | The Lemon Index', lede, body, ld=[faq_ld([(q, '', re.sub('<[^>]+>', '', a).replace('&#39;', "'")) for q, a in faq])]); SEO_URLS.append(f'/best/used-cars-under-{k[:-1]}000/'); cards.append((f'/best/used-cars-under-{k[:-1]}000/', f'Best used cars under {label}'))
    if GAP:
        segof = {c['id']: c['seg'] for c in CARS}; L = sorted([m for m in GAP['mpg'] if segof.get(m['id']) == 'suv'], key=lambda m: -m['comb'])[:15]
        if len(L) >= 5:
            lede = f'The best gas mileage SUVs we track are the {L[0]["name"]} at {L[0]["comb"]} mpg combined, the {L[1]["name"]} at {L[1]["comb"]} and the {L[2]["name"]} at {L[2]["comb"]}, using their best gas or hybrid version.'
            body = ('<div class="advp cb cbx">' + cbx_head('SUVs with the best gas mileage.', 'EPA combined mileage, best gas or hybrid version, next to each SUV&#39;s owner-complaint score.')
                    + '<section class="cbx-sec cbx-list"><h2>Top 15</h2>' + mpg_rows(L) + '</section>' + cbx_buy() + cbx_budgets()
                    + cbx_src(E(lede) + ' EPA mileage, best version sold 2019 to 2025, gas and hybrid only. Lemon Index covers model years 2010 to 2022, where 100 is the average car and lower is better.') + '</div>')
            body += share_line('SUVs with the best gas mileage, next to their owner complaint scores. Free list:')
            page('/best/suvs-gas-mileage/', 'SUVs With the Best Gas Mileage, With Complaint Scores', lede, body); SEO_URLS.append('/best/suvs-gas-mileage/'); cards.append(('/best/suvs-gas-mileage/', 'SUVs with the best gas mileage'))
    # 11-10 v2: the index as photo cards, each with the #1 car of its list
    lead = {}
    for slug, sg, nm in SEG:
        L = sorted([c for c in CARS if c['seg'] == sg and c['sold'] >= 150000], key=lambda c: c['li']); lead[f'/best/most-reliable-{slug}/'] = L[0]['id']
    for k in ('5k', '10k', '15k', '20k'):
        p_ = os.path.join(YT_SRC, f'best-used-{k}', 'consensus.json')
        if os.path.exists(p_):
            c0 = next((BYNAME.get(r['model']) for r in json.load(open(p_, encoding='utf-8'))['ranking'] if BYNAME.get(r['model'])), None)
            if c0: lead[f'/best/used-cars-under-{k[:-1]}000/'] = c0['id']
    if GAP:
        segof = {c['id']: c['seg'] for c in CARS}
        lead['/best/suvs-gas-mileage/'] = next((m['id'] for m in sorted([m for m in GAP['mpg'] if segof.get(m['id']) == 'suv'], key=lambda m: -m['comb'])), None)
        lead['/best-gas-mileage/'] = GAP['mpg'][0]['id']; lead['/check-engine-light/'] = GAP['cel'][0]['id']
    allc = cards + [('/best-gas-mileage/', 'Best gas mileage'), ('/check-engine-light/', 'Which cars get the check engine light most')]
    if TEEN_CARD: allc.insert(0, TEEN_CARD[:2]); lead[TEEN_CARD[0]] = TEEN_CARD[2]   # 11-12: the teen list first (Linda)
    def _bc(u, t):
        ph = aph(lead[u]) if lead.get(u) else None
        im = f'<span class="bcp"><img src="{ph["src"]}" alt="" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async"></span>' if ph else '<span class="bcp"></span>'
        return f'<a class="bcard" href="{u}">{im}<b>{E(t)}</b><span class="tl">See the list <i>›</i></span></a>'
    hub = ('<div class="advp"><header class="advh1"><h1>Best cars, by the data.</h1><p class="ans">Rankings built from government complaint data and YouTube buyer&#39;s guides.</p></header><div class="bcards">'
           + ''.join(_bc(u, t) for u, t in allc) + '</div></div>')
    hub += share_line('The best cars, SUVs, trucks and minivans, ranked by real owner data. Free:')
    page('/best/', 'Best Cars Ranked by Real Owner Data | The Lemon Index', 'The most reliable cars, SUVs, trucks and minivans, plus the best used cars by budget, ranked from government complaint data.', hub); SEO_URLS.insert(0, '/best/')
    # ---- statistics (11-14 growth plan 5c: every number computed here from the site's data at build time; the page's date and the citation
    # date are its content-hash date, so they move only when a number or the text changes)
    global STATS_LLM
    tot = sum(sum(v.get('n', 0) for v in f['years']) for f in YEARS); sev = defaultdict(int); rec = set()
    for fid, ys in XL.items():
        for y, x in ys.items():
            for k, v in (x.get('sev') or {}).items(): sev[k] += v
    for fid, ys in XA.items():
        for y, x in (ys or {}).items():
            for r in (x or {}).get('recalls') or []: rec.add(r['id'])
    comps = defaultdict(int)
    for r in csv.DictReader(open('data/family_components.csv', encoding='utf-8')): comps[r['component']] += int(r['complaints'])
    all_c = sum(comps.values()); tc = sorted(((k, v) for k, v in comps.items() if k not in ('UNKNOWN OR OTHER', 'UNKNOWN')), key=lambda kv: -kv[1])[:8]   # 11-14: named systems only
    br = sorted(csv.DictReader(open('data/brand_rates.csv', encoding='utf-8')), key=lambda r: int(r['lemon_index']))
    popular = sorted([c for c in CARS if c['sold'] >= 150000], key=lambda c: c['li'])
    cel = GAP['cel'] if GAP else []
    # the most complained-about model years: the /rankings/worst-years/ list (Lemon Index per car sold, model years WY0-WY1)
    WYR = worst_years(); WYX = [t for t in WYR if not t[1].get('early')]; wy = WYX[:10]
    WYF = max(t[1]['y'] for t in WYX)   # the last model year with a full 3-year complaint window (2023+ are early reads), from the data
    # complaints per 100,000 sold by model year, 2010-2022 (each year's first 3 years of complaints, every model with a sales figure)
    TY = list(range(2010, 2023)); tn = defaultdict(int); ts = defaultdict(int)
    for f in YEARS:
        for v in f['years']:
            if v['y'] in TY and v.get('sold') and v.get('li') is not None and not v.get('early'): tn[v['y']] += v['n']; ts[v['y']] += v['sold']
    trend = [(y, tn[y] / ts[y] * 1e5) for y in TY if ts[y]]
    t_hi = max(trend, key=lambda t: t[1]); t_lo = min(trend, key=lambda t: t[1])
    # EVs vs other cars: the EV study's pooled numbers (same model years, same window)
    PE, PG = _EVJ['pooled']['ev'], _EVJ['pooled']['gas']; evy = _EVJ['years']
    evx = PE['per100k'] / PG['per100k']; evx2 = PE['noadas100k'] / PG['noadas100k']
    # share of complaints filed in a car's first 3 years: the ranked models, model years 2010-2022 (data/family_rates.csv)
    FR = list(csv.DictReader(open('data/family_rates.csv', encoding='utf-8')))
    f3 = sum(int(r['complaints_3yr']) for r in FR); fall = sum(int(r['complaints_all_time']) for r in FR); f3p = f3 / fall * 100 if fall else 0
    sysn = lambda k: PART.get(k, k.lower())
    wyn = lambda t: f'{t[1]["y"]} {t[0]["name"]}'
    x_ = lambda li: f'{li / 100:.1f}'.replace('.0', '')
    lede = f'{sev["total"]:,} U.S. owner complaints to the government, broken down by model year, brand, system and fuel type.'
    # the quotable lines: plain sentences with one number each, for reporters and AI answers
    facts = [
        f'The <b>{E(wyn(wy[0]))}</b> drew the most owner complaints per car sold of any model year from {WY0} to {WYF}: a Lemon Index of {wy[0][1]["li"]:,}, about {x_(wy[0][1]["li"])} times the average car of that year.',
        f'The brand with the fewest complaints per car sold is <b>{E(br[0]["brand"])}</b> (Lemon Index {br[0]["lemon_index"]}). The most: <b>{E(br[-1]["brand"])}</b> ({br[-1]["lemon_index"]}). 100 is the average car.',
        f'<b>{E(sysn(tc[0][0])).capitalize()}</b> is the most common problem area: {tc[0][1] / all_c * 100:.0f}% of complaint mentions, then {E(sysn(tc[1][0]))} ({tc[1][1] / all_c * 100:.0f}%) and {E(sysn(tc[2][0]))} ({tc[2][1] / all_c * 100:.0f}%).',
        f'Electric cars drew <b>{PE["per100k"]}</b> complaints per 100,000 sold, against <b>{PG["per100k"]}</b> for other cars of the same model years ({evy[0]}–{evy[1]}): about {evx:.1f} times as many. Without driver-assist complaints, {evx2:.1f} times.',
        f'Only <b>{f3p:.0f}%</b> of the complaints filed so far about 2010–2022 model years of the {len(FR)} models we rank came in within 3 years of the model year. The other {100 - f3p:.0f}% came later.',
        f'Of the 2010–2022 model years, <b>{t_hi[0]}</b> drew the most complaints per car sold ({t_hi[1]:.0f} per 100,000 in their first 3 years) and <b>{t_lo[0]}</b> the fewest ({t_lo[1]:.0f}).',
        f'The most reliable popular model is the <b>{E(popular[0]["name"])}</b> (Lemon Index {popular[0]["li"]}). The least: the <b>{E(popular[-1]["name"])}</b> ({popular[-1]["li"]}).']
    T_ = [(f'{sev["total"]:,}', 'owner complaints', f'{len(YEARS)} models, model years 2000–2025, filed any time'), (f'{sev["crash"]:,}', 'crashes reported', 'owner reports, not verified'),
          (f'{sev["fire"]:,}', 'fires reported', 'owner reports'), (f'{sev["injured"]:,}', 'injuries reported', 'owner reports'),
          (f'{sev["deaths"]:,}', 'deaths reported', 'owner reports'), (f'{sev["towed"]:,}', 'cars towed', 'owner reports'), (f'{len(rec):,}', 'recall campaigns', 'across those models')]
    tiles = '<div class="stt">' + ''.join(f'<div><b>{a}</b><span>{b}</span><small>{c}</small></div>' for a, b, c in T_) + '</div>'
    def hbar(rows, mx, line=None, unit=''):
        return '<div class="sbb">' + ''.join(f'<div class="sbr {cl}"><span class="sbl">{lab}</span><span class="sbt"><i style="width:{v / mx * 100:.1f}%"></i>'
                                             + (f'<em style="left:{line / mx * 100:.1f}%"></em>' if line else '') + f'</span><b>{txt}</b></div>' for lab, v, txt, cl in rows) + '</div>'
    tone = lambda li: 'good' if li < 90 else 'bad' if li > 110 else ''
    sysr = [(E(sysn(k)).capitalize(), v, f'{v / all_c * 100:.0f}%', '') for k, v in tc]
    brr = [(E(r['brand']), int(r['lemon_index']), r['lemon_index'], tone(int(r['lemon_index']))) for r in br]
    pm = popular[:5] + popular[-5:]
    pmr = [(f'<a href="{car_href(c["id"])}">{E(c["name"])}</a>' if car_href(c['id']) else E(c['name']), c['li'], str(c['li']), tone(c['li'])) for c in pm]
    wyr = [(f'<a href="{CARU(f, v["y"])}">{v["y"]} {E(f["name"])}</a>' + (' <small>early</small>' if v.get('early') else ''), v['li'], f'{v["li"]:,}', 'bad') for f, v in wy]
    avg_t = sum(tn.values()) / sum(ts.values()) * 1e5
    trr = [(str(y), r, f'{r:.0f}', 'bad' if r > avg_t * 1.1 else 'good' if r < avg_t * .9 else '') for y, r in trend]
    evr = [('Electric cars', PE['per100k'], str(PE['per100k']), 'bad'), ('Other cars', PG['per100k'], str(PG['per100k']), ''),
           ('Electric, no driver-assist', PE['noadas100k'], str(PE['noadas100k']), 'bad'), ('Other, no driver-assist', PG['noadas100k'], str(PG['noadas100k']), '')]
    f3r = [('First 3 years', f3, f'{f3p:.0f}%', ''), ('Later', fall - f3, f'{100 - f3p:.0f}%', '')]
    url = BASE + '/stats/car-complaints/'
    cite_apa = f'The Lemon Index. (%%PD_DATE%%). Car complaint statistics. {url}'
    cite_line = 'Source: The Lemon Index (lemonindex.com), based on NHTSA owner complaints.'
    cite_html = f'<a href="{url}">Car complaint statistics, The Lemon Index</a>'
    def _cp(lab, txt):
        return f'<div class="cpy"><p class="cpy-l">{lab}</p><div class="cpy-r"><code>{E(txt)}</code><button type="button" class="btn btn-ghost cpy-b" data-copy="{E(txt)}">Copy</button></div></div>'
    sec = lambda id_, h, inner, cap: f'<section class="yc" id="{id_}"><h2>{h}</h2>{inner}<p class="yc-cap">{cap}</p></section>'
    body = (f'<div class="advp stp"><header class="advh1"><p class="ph-e"><a href="/">The Lemon Index</a></p><h1>Car complaint statistics.</h1><p class="ans">{E(lede)}</p>'
            '<p class="yc-cap">Numbers last changed <b>%%PD_DATE%%</b>. Every figure is computed from our data files when the site is built.</p></header>'
            '<section class="yc" id="key-facts"><h2>Key facts</h2><ul>' + ''.join(f'<li>{x}</li>' for x in facts) + '</ul></section>'
            + tiles
            + sec('worst-model-years', f'Most complained-about model years, {WY0}–{WYF}', hbar(wyr, max(v for _, v, _, _ in wyr) * 1.05, 100),
                  f'Lemon Index for that model year: complaints per car sold against the average car of the same year (100, the line). Model years with 20,000+ sold and a full 3 years of complaints. '
                  f'<a href="/rankings/worst-years/">All {len(WYR):,} model years ranked, {WY0}–{WY1}</a> (2023+ as early reads).')
            + sec('brands', 'Brands ranked by complaints per car sold', hbar(brr, max(130, max(v for _, v, _, _ in brr)) * 1.05, 100),
                  'Lemon Index, model years 2010 to 2022. 100 (the line) is the average car; lower is better. <a href="/brands/">Every brand</a>.')
            + sec('trend', 'Complaints per car sold, by model year', hbar(trr, max(r for _, r, _, _ in trr) * 1.08, avg_t),
                  f'Owner complaints per 100,000 cars sold, filed in each model year&#39;s first 3 years, for every model we track with a U.S. sales figure. The line is the 2010–2022 average ({avg_t:.0f}).')
            + sec('problem-areas', 'Most common problem areas', hbar(sysr, max(v for _, v, _, _ in sysr) * 1.05),
                  f'Share of all complaint mentions, model years 2010 to 2022 ({(comps.get("UNKNOWN OR OTHER", 0) + comps.get("UNKNOWN", 0)) / all_c * 100:.0f}% name no system and are left off). One complaint can name several systems.')
            + sec('ev-vs-gas', 'Electric cars vs other cars', hbar(evr, max(PE['per100k'], PG['per100k']) * 1.08),
                  f'Owner complaints per 100,000 cars sold, model years {evy[0]}–{evy[1]}, filed by the end of the year after the model year: {PE["sold"]:,} EVs and {PG["sold"]:,} other cars. '
                  f'Driver-assist = automatic emergency braking, lane keeping, blind-spot and backup systems. Fire complaints: {PE["fire100k"]} per 100,000 EVs, {PG["fire100k"]} per 100,000 other cars. '
                  '<a href="/electric/">Every EV ranked</a>.')
            + sec('first-3-years', 'When complaints are filed', hbar(f3r, fall),
                  f'All {fall:,} complaints filed so far about the 2010–2022 model years of the {len(FR)} models we rank, split by whether NHTSA got them within 3 years of the model year. '
                  'Our scores count only the first 3 years, so old and new cars are compared fairly.')
            + sec('models', 'Popular models: best 5 and worst 5', hbar(pmr, max(c['li'] for c in pm) * 1.05, 100),
                  'Models with 150,000 or more sold.' + (f' Most check engine light complaints per car sold: the {E(cel[0]["name"])} ({cel[0]["per"]:g} per 100,000).' if cel else ''))
            + totals_html() +   # 11-12 (Priya): what each site-wide total covers
            '<section class="yc stc" id="cite"><h2>How to cite this</h2><p>Free to use under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener">CC BY 4.0</a> with credit and a link.</p>'
            + _cp('Credit line', cite_line) + _cp('Citation', cite_apa) + _cp('Link (HTML)', cite_html)
            + '<p>Raw data: <a href="/data/">free CSV downloads</a>. Method: <a href="/method/">how the index works</a>. Charts for your site: <a href="/embed/">embed a chart</a>. Reporters: <a href="/press/">press page</a>.</p></section>'
            '<p class="yc-cap">Source: NHTSA owner complaints and recalls, and published U.S. sales. Complaints are owner reports, not proof of a defect. Not a safety rating.</p></div>'
            '<script src="/assets/data.js?v=1103" defer></script>')
    body += share_line(f'{sev["total"]:,} car complaints to the government, broken down by brand, model and system. Free to cite:', 'Know someone who writes about cars?')
    ds = {"@context": "https://schema.org", "@type": "Dataset", "name": "Car complaint statistics (The Lemon Index)", "url": url,
          "description": f'{lede} Includes the most complained-about model years, brands ranked by complaints per car sold, complaints per car sold by model year, the most common problem areas, electric vs other cars, and the share of complaints filed in a car\'s first 3 years.',
          "keywords": ["car complaints", "NHTSA complaints", "car reliability statistics", "most complained about cars", "car brands reliability", "electric car complaints"],
          "license": "https://creativecommons.org/licenses/by/4.0/", "isAccessibleForFree": True, "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE},
          "isBasedOn": "https://www.nhtsa.gov/nhtsa-datasets-and-apis", "temporalCoverage": "2000/2025", "spatialCoverage": "United States", "dateModified": "%%PD_ISO%%",
          "citation": cite_line, "variableMeasured": ["Lemon Index (owner complaints per car sold, 100 = average)", "NHTSA owner complaints", "Complaints per 100,000 sold", "Recalls"],
          "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE + u} for u in ('/data/lemon-index-by-year.csv', '/data/lemon-index-by-model.csv', f'/data/worst-model-years-{WY0}-{WY1}.csv', '/data/electric-cars.csv')]}
    page('/stats/car-complaints/', 'Car Complaint Statistics: Brands, Models and Systems | The Lemon Index', lede + ' Free to cite.', body, ld=[ds]); SEO_URLS.append('/stats/car-complaints/')
    _txt = lambda h: re.sub(r'<[^>]+>', '', h).replace('&#39;', "'").replace('&amp;', '&')
    STATS_LLM = (f'- [Car complaint statistics]({url}): {sev["total"]:,} NHTSA owner complaints by model year, brand, system and fuel type, with a ready citation (CC BY 4.0). '
                 + ' '.join(_txt(x) for x in facts[:5]) + '\n')
    print('seo pages', len(SEO_URLS), 'complaints', sev['total'], 'recalls', len(rec))
_seo_pages()
