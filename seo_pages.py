# Best-of and statistics pages (11-06, SEO plan). Run by build.py with exec(). Every number comes from our own data; nothing here is hand-typed.
SEO_URLS = []
YT_SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\yt'
def _seo_pages():
    PAGEID = {c['name']: c['id'] for c in CARS}; HAS = {f['id'] for f in YEARS}
    def carlink(c): return f'<a href="/cars/{c["id"]}/">{E(c["name"])}</a>' if c['id'] in HAS else E(c['name'])
    def rows(L, sub):
        return '<ol class="bestl">' + ''.join(f'<li><span class="rk">{i}</span><div><b>{carlink(c)}</b><small>{sub(c)}</small></div><span class="sc">{c["li"]}</span></li>' for i, c in enumerate(L, 1)) + '</ol>'
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
        for r in d['ranking'][:20]:
            c = BYNAME.get(r['model']); R.append((r, c))
        lis = '<ol class="bestl">' + ''.join(f'<li><span class="rk">{i}</span><div><b>{carlink(c) if c else E(r["model"])}</b><small>{r["videos"]} of {d["videos"]} videos</small></div><span class="sc">{c["li"] if c else "–"}</span></li>' for i, (r, c) in enumerate(R[:15], 1)) + '</ol>'
        safe = sorted([x for x in R if x[1] and x[1]['li'] < 100], key=lambda x: x[1]['li'])[:3]
        lede = f'In {d["videos"]} YouTube videos on the best used cars under {label}, the most-picked are the {R[0][0]["model"]}, {R[1][0]["model"]} and {R[2][0]["model"]}.' + (f' Among the top picks, the {safe[0][0]["model"]} has the fewest owner complaints.' if safe else '')
        body = f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/best/">Best cars</a></p><h1>Best used cars under {label}.</h1><p class="ans">{E(lede)}</p></header><div class="ygrid"><section class="yc"><h2>What buyers&#39; guides pick, with complaint scores</h2>{lis}<p class="yc-cap">Right column: Lemon Index, where 100 is the average car and lower is better. A dash means we don&#39;t score that model.</p></section></div><p class="yc-cap">Picks come from {d["videos"]} YouTube videos with {d["views"] / 1e6:.1f}M views. A pick counts when the model is in the title or named in the video. Check the exact model year before you buy.</p></div>'
        body += share_line(f'Best used cars under {label}: what {d["videos"]} buyer guide videos pick, with complaint scores. Free:', 'Know someone shopping on a budget?')
        page(f'/best/used-cars-under-{k[:-1]}000/', f'Best Used Cars Under {label}: What {d["videos"]} Videos Pick | The Lemon Index', lede, body); SEO_URLS.append(f'/best/used-cars-under-{k[:-1]}000/'); cards.append((f'/best/used-cars-under-{k[:-1]}000/', f'Best used cars under {label}'))
    if GAP:
        segof = {c['id']: c['seg'] for c in CARS}; L = sorted([m for m in GAP['mpg'] if segof.get(m['id']) == 'suv'], key=lambda m: -m['comb'])[:15]
        if len(L) >= 5:
            lede = f'The best gas mileage SUVs we track are the {L[0]["name"]} at {L[0]["comb"]} mpg combined, the {L[1]["name"]} at {L[1]["comb"]} and the {L[2]["name"]} at {L[2]["comb"]}, using their best gas or hybrid version.'
            body = ('<div class="advp"><header class="advh1"><p class="ph-e"><a href="/best/">Best cars</a></p><h1>SUVs with the best gas mileage.</h1><p class="ans">' + E(lede) + '</p></header><div class="ygrid"><section class="yc"><div class="tw"><table class="adv"><thead><tr><th>SUV</th><th>Combined</th><th>City / hwy</th><th>Fuel cost/yr</th><th>Lemon Index</th></tr></thead><tbody>'
                    + ''.join(f'<tr><td><a href="/cars/{m["id"]}/">{E(m["name"])}</a>{" (hybrid)" if m["hyb"] else ""}</td><td>{m["comb"]}</td><td>{m["city"]} / {m["hwy"]}</td><td>${m["cost"]:,}</td><td>{m["li"] or "–"}</td></tr>' for m in L) + '</tbody></table></div></section></div><p class="yc-cap">EPA mileage, best version sold 2019 to 2025, gas and hybrid only. Lemon Index covers model years 2010 to 2022, where 100 is the average car and lower is better.</p></div>')
            body += share_line('SUVs with the best gas mileage, next to their owner complaint scores. Free list:')
            page('/best/suvs-gas-mileage/', 'SUVs With the Best Gas Mileage, With Complaint Scores', lede, body); SEO_URLS.append('/best/suvs-gas-mileage/'); cards.append(('/best/suvs-gas-mileage/', 'SUVs with the best gas mileage'))
    hub = '<div class="advp"><header class="advh1"><h1>Best cars, by the data.</h1><p class="ans">Rankings built from government complaint data and YouTube buyer&#39;s guides.</p></header><ul class="bestl">' + ''.join(f'<li style="grid-template-columns:1fr"><b><a href="{u}">{E(t)}</a></b></li>' for u, t in cards + [('/best-gas-mileage/', 'Best gas mileage'), ('/check-engine-light/', 'Which cars get the check engine light most')]) + '</ul></div>'
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
    S_ = [f'<b>{sev["total"]:,}</b> owner complaints are in our dataset for the {len(YEARS)} models we track by model year.', f'Owners reported <b>{sev["crash"]:,}</b> crashes, <b>{sev["fire"]:,}</b> fires, <b>{sev["injured"]:,}</b> injuries and <b>{sev["deaths"]:,}</b> deaths in those complaints. These are owner reports, not verified counts.', f'Owners reported <b>{sev["towed"]:,}</b> vehicles towed.', f'We track <b>{len(rec):,}</b> different recall campaigns across those models.',
          f'The most reliable brand by owner complaints is <b>{br[0]["brand"]}</b>, with a Lemon Index of {br[0]["lemon_index"]}. The highest is <b>{br[-1]["brand"]}</b> at {br[-1]["lemon_index"]}. 100 is the average car.', f'The most reliable popular model is the <b>{popular[0]["name"]}</b> at {popular[0]["li"]}. The highest is the <b>{popular[-1]["name"]}</b> at {popular[-1]["li"]}.']
    if cel: S_.append(f'The <b>{cel[0]["name"]}</b> drew the most check engine light complaints per vehicle sold, at {cel[0]["per"]:g} per 100,000.')
    lede = f'{sev["total"]:,} U.S. owner complaints to the government, broken down by system, brand and model.'
    body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/">The Lemon Index</a></p><h1>Car complaint statistics.</h1><p class="ans">{E(lede)}</p></header><div class="ygrid"><section class="yc"><h2>Key numbers</h2><ul class="statl">' + ''.join(f'<li>{x}</li>' for x in S_) + '</ul></section>'
            '<section class="yc"><h2>Most complained-about systems</h2><div class="tw"><table class="adv"><thead><tr><th>System</th><th>Complaints</th><th>Share</th></tr></thead><tbody>' + ''.join(f'<tr><td>{E(PART.get(k, k.lower()))}</td><td>{v:,}</td><td>{v / all_c * 100:.1f}%</td></tr>' for k, v in tc) + '</tbody></table></div><p class="yc-cap">Model years 2010 to 2022, whole-model data. One complaint can name more than one system.</p></section>'
            '<section class="yc"><h2>Brands</h2><div class="tw"><table class="adv"><thead><tr><th>Brand</th><th>Lemon Index</th></tr></thead><tbody>' + ''.join(f'<tr><td>{E(r["brand"])}</td><td>{r["lemon_index"]}</td></tr>' for r in br) + '</tbody></table></div></section>'
            '<section class="yc"><h2>How to cite this</h2><p>Free to use with credit: <q>Source: The Lemon Index (lemonindex.com)</q>. The raw data is on the <a href="/data/">data page</a>, and the method is on <a href="/method/">how the index works</a>.</p></section></div><p class="yc-cap">Source: NHTSA owner complaints, recalls and sales estimates. Complaints are owner reports, not proof of a defect, and not every owner files one.</p></div>')
    body += share_line(f'{sev["total"]:,} car complaints to the government, broken down by brand, model and system. Free to cite:', 'Know someone who writes about cars?')
    page('/stats/car-complaints/', 'Car Complaint Statistics: Brands, Models and Systems | The Lemon Index', lede + ' Free to cite.', body); SEO_URLS.append('/stats/car-complaints/')
    print('seo pages', len(SEO_URLS), 'complaints', sev['total'], 'recalls', len(rec))
_seo_pages()
