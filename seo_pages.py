# Best-of and statistics pages (11-06, SEO plan). Run by build.py with exec(). Every number comes from our own data; nothing here is hand-typed.
SEO_URLS = []
YT_SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\yt'
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
        body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/best/">Best cars</a></p><h1>The most reliable {nm}, ranked.</h1><p class="ans">{E(lede)}</p></header><div class="ygrid"><section class="yc"><h2>Fewest complaints</h2>{rows(T, top)}</section><section class="yc"><h2>Most complaints</h2>{rows(W, top)}</section>'
                '<section class="yc yqa"><h2>Quick answers</h2>' + ''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq) + '</section></div><p class="yc-cap">Lemon Index: NHTSA owner complaints filed in a model year&#39;s first 3 years, per vehicle sold, against the average car. Model years 2010 to 2022, models with 150,000 or more sold. Complaints are owner reports, not proof of a defect.</p></div>')
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
        body = f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/best/">Best cars</a></p><h1>Best used cars under {label}.</h1><p class="ans">{E(lede)}</p></header><div class="ygrid"><section class="yc"><h2>What buyers&#39; guides pick, with complaint scores</h2>{lis}<p class="yc-cap">Right column: the model&#39;s Lemon Index (model years 2010 to 2022), where 100 is the average car and lower is better. A dash means we don&#39;t score that model yet. &#34;Years picked most&#34; = the model-year range the most videos named for this budget; open the car for each year&#39;s own score.</p></section></div><p class="yc-cap">Picks come from {d["videos"]} YouTube videos with {d["views"] / 1e6:.1f}M views. A pick counts when the model is in the title or named in the video. These are buyer-guide picks, not prices: check the exact model year and price before you buy. Shopping for a new driver? See the <a href="/best/safest-cars-for-teens/">safest used cars for teens</a>.</p></div>'
        body += share_line(f'Best used cars under {label}: what {d["videos"]} buyer guide videos pick, with complaint scores. Free:', 'Know someone shopping on a budget?')
        page(f'/best/used-cars-under-{k[:-1]}000/', f'Best Used Cars Under {label}: What {d["videos"]} Videos Pick | The Lemon Index', lede, body); SEO_URLS.append(f'/best/used-cars-under-{k[:-1]}000/'); cards.append((f'/best/used-cars-under-{k[:-1]}000/', f'Best used cars under {label}'))
    if GAP:
        segof = {c['id']: c['seg'] for c in CARS}; L = sorted([m for m in GAP['mpg'] if segof.get(m['id']) == 'suv'], key=lambda m: -m['comb'])[:15]
        if len(L) >= 5:
            lede = f'The best gas mileage SUVs we track are the {L[0]["name"]} at {L[0]["comb"]} mpg combined, the {L[1]["name"]} at {L[1]["comb"]} and the {L[2]["name"]} at {L[2]["comb"]}, using their best gas or hybrid version.'
            body = ('<div class="advp"><header class="advh1"><p class="ph-e"><a href="/best/">Best cars</a></p><h1>SUVs with the best gas mileage.</h1><p class="ans">' + E(lede) + '</p></header><div class="ygrid"><section class="yc">' + mpg_rows(L) + '</section></div><p class="yc-cap">EPA mileage, best version sold 2019 to 2025, gas and hybrid only. Lemon Index covers model years 2010 to 2022, where 100 is the average car and lower is better.</p></div>')
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
    # ---- statistics
    tot = sum(sum(v.get('n', 0) for v in f['years']) for f in YEARS); sev = defaultdict(int); rec = set()
    for fid, ys in XL.items():
        for y, x in ys.items():
            for k, v in (x.get('sev') or {}).items(): sev[k] += v
    for fid, ys in XA.items():
        for y, x in (ys or {}).items():
            for r in (x or {}).get('recalls') or []: rec.add(r['id'])
    comps = defaultdict(int)
    for r in csv.DictReader(open('data/family_components.csv', encoding='utf-8')): comps[r['component']] += int(r['complaints'])
    all_c = sum(comps.values()); tc = sorted(comps.items(), key=lambda kv: -kv[1])[:5]
    br = sorted(csv.DictReader(open('data/brand_rates.csv', encoding='utf-8')), key=lambda r: int(r['lemon_index']))
    popular = sorted([c for c in CARS if c['sold'] >= 150000], key=lambda c: c['li'])
    cel = GAP['cel'] if GAP else []
    S_ = [f'<b>{sev["total"]:,}</b> owner complaints are in our dataset for the {len(YEARS)} models we track, model years 2000 to 2025, filed at any time.', f'Owners reported <b>{sev["crash"]:,}</b> crashes, <b>{sev["fire"]:,}</b> fires, <b>{sev["injured"]:,}</b> injuries and <b>{sev["deaths"]:,}</b> deaths in those complaints. These are owner reports, not verified counts.', f'Owners reported <b>{sev["towed"]:,}</b> vehicles towed.', f'We track <b>{len(rec):,}</b> different recall campaigns across those models.',
          f'The most reliable brand by owner complaints is <b>{br[0]["brand"]}</b>, with a Lemon Index of {br[0]["lemon_index"]}. The highest is <b>{br[-1]["brand"]}</b> at {br[-1]["lemon_index"]}. 100 is the average car.', f'The most reliable popular model is the <b>{popular[0]["name"]}</b> at {popular[0]["li"]}. The highest is the <b>{popular[-1]["name"]}</b> at {popular[-1]["li"]}.']
    if cel: S_.append(f'The <b>{cel[0]["name"]}</b> drew the most check engine light complaints per vehicle sold, at {cel[0]["per"]:g} per 100,000.')
    lede = f'{sev["total"]:,} U.S. owner complaints to the government, broken down by system, brand and model.'
    # 11-10 v2 (design audit: a list of sentences + plain tables): big stat tiles, three simple bar charts, short source lines, the cite box kept
    T_ = [(f'{sev["total"]:,}', 'owner complaints', f'{len(YEARS)} models, model years 2000–2025, filed any time'), (f'{sev["crash"]:,}', 'crashes reported', 'owner reports, not verified'),
          (f'{sev["fire"]:,}', 'fires reported', 'owner reports'), (f'{sev["injured"]:,}', 'injuries reported', 'owner reports'),
          (f'{sev["deaths"]:,}', 'deaths reported', 'owner reports'), (f'{sev["towed"]:,}', 'cars towed', 'owner reports'), (f'{len(rec):,}', 'recall campaigns', 'across those models')]
    tiles = '<div class="stt">' + ''.join(f'<div><b>{a}</b><span>{b}</span><small>{c}</small></div>' for a, b, c in T_) + '</div>'
    def hbar(rows, mx, line=None, unit=''):
        return '<div class="sbb">' + ''.join(f'<div class="sbr {cl}"><span class="sbl">{lab}</span><span class="sbt"><i style="width:{v / mx * 100:.1f}%"></i>'
                                             + (f'<em style="left:{line / mx * 100:.1f}%"></em>' if line else '') + f'</span><b>{txt}</b></div>' for lab, v, txt, cl in rows) + '</div>'
    sysr = [(E(PART.get(k, k.lower())).capitalize(), v, f'{v / all_c * 100:.0f}%', '') for k, v in tc]
    brr = [(E(r['brand']), int(r['lemon_index']), r['lemon_index'], 'good' if int(r['lemon_index']) < 90 else 'bad' if int(r['lemon_index']) > 110 else '') for r in br]
    pm = popular[:5] + popular[-5:]
    pmr = [(f'<a href="{car_href(c["id"])}">{E(c["name"])}</a>' if car_href(c['id']) else E(c['name']), c['li'], str(c['li']), 'good' if c['li'] < 90 else 'bad' if c['li'] > 110 else '') for c in pm]
    body = (f'<div class="advp stp"><header class="advh1"><p class="ph-e"><a href="/">The Lemon Index</a></p><h1>Car complaint statistics.</h1><p class="ans">{E(lede)}</p></header>{tiles}'
            '<section class="yc"><h2>Most complained-about systems</h2>' + hbar(sysr, max(v for _, v, _, _ in sysr)) + '<p class="yc-cap">Share of complaints, model years 2010 to 2022. One complaint can name several systems.</p></section>'
            '<section class="yc"><h2>Brands, by Lemon Index</h2>' + hbar(brr, max(130, max(v for _, v, _, _ in brr)) * 1.05, 100) + '<p class="yc-cap">Complaints per car sold against the average car. 100 (the line) is average, lower is better.</p></section>'
            '<section class="yc"><h2>Popular models: best 5 and worst 5</h2>' + hbar(pmr, max(c['li'] for c in pm) * 1.05, 100) + '<p class="yc-cap">Models with 150,000 or more sold.'
            + (f' Most check engine light complaints per car sold: the {E(cel[0]["name"])} ({cel[0]["per"]:g} per 100,000).' if cel else '') + '</p></section>'
            + totals_html() +   # 11-12 (Priya): what each site-wide total covers
            '<section class="yc stc"><h2>How to cite this</h2><p>Free to use with credit: <q>Source: The Lemon Index (lemonindex.com)</q>. Raw data on the <a href="/data/">data page</a>; method on <a href="/method/">how the index works</a>.</p></section>'
            '<p class="yc-cap">Source: NHTSA owner complaints and recalls, and published U.S. sales. Complaints are owner reports, not proof of a defect.</p></div>')
    body += share_line(f'{sev["total"]:,} car complaints to the government, broken down by brand, model and system. Free to cite:', 'Know someone who writes about cars?')
    page('/stats/car-complaints/', 'Car Complaint Statistics: Brands, Models and Systems | The Lemon Index', lede + ' Free to cite.', body); SEO_URLS.append('/stats/car-complaints/')
    print('seo pages', len(SEO_URLS), 'complaints', sev['total'], 'recalls', len(rec))
_seo_pages()
