# 11-11 (Elijah: "start filling out the cards that have no data… one at a time, full treatment"): the "No data yet" models, one by one.
#   usage: py data_new_models.py            (reads data/new_plan.json; writes data/years_new.json, cars_new.json, extras_local_new.json, extras_api_new.json)
# Same method as the published Lemon Index, computed for these models ONLY, so nothing already published moves:
#   complaints: NHTSA owner complaints (3 Lemon Index/data/complaints.db) filed within 3 years of the model year (model years 2023-2025: every
#               complaint so far, flagged early, like the site's early reads)
#   sales:      U.S. calendar-year sales from the model's Wikipedia sales table (the same parser as the study, autopilot/lib/sales.py) or a
#               model-year table where the article has one; the source URL is kept with every figure
#   index:      complaints per car sold against the average car of the same model year, with the average taken from the published data
#               (2010-2022: the study's model_years.csv, lower of calendar and blended like the study; 2000-2009 and 2023-2025: the site's years.json)
#   extras:     recalls, crash tests and EPA mpg from the same public APIs as data_fetch_api.py (its functions, its cache)
# A model year needs 20,000+ cars sold to get a score, like everywhere else on the site. No sales source = complaints only, no index.
import csv, glob, json, os, re, sqlite3, sys, random, collections, concurrent.futures as cf
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
sys.path.insert(0, os.path.join(LEMON, 'autopilot', 'lib'))
import mysales, sales as WIKI
from families import FAMILIES
PLAN = json.load(open(os.path.join(HERE, 'data', 'new_plan.json'), encoding='utf-8'))
ONLY = set(sys.argv[1:])
Y0, Y1, WINDOW, MIN_SOLD = 2000, 2025, 3, 20000
PART = {'ELECTRICAL SYSTEM': 'electrical', 'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'VEHICLE SPEED CONTROL': 'speed control',
        'FUEL/PROPULSION SYSTEM': 'fuel or EV drive system', 'FORWARD COLLISION AVOIDANCE': 'automatic emergency braking', 'VISIBILITY/WIPER': 'wipers & visibility',
        'VISIBILITY': 'visibility', 'AIR BAGS': 'airbags', 'STRUCTURE': 'body structure', 'EXTERIOR LIGHTING': 'lights', 'ELECTRONIC STABILITY CONTROL (ESC)': 'stability control',
        'LANE DEPARTURE': 'lane assist', 'ENGINE AND ENGINE COOLING': 'engine', 'SEAT BELTS': 'seat belts', 'ENGINE': 'engine', 'STEERING': 'steering', 'SUSPENSION': 'suspension',
        'WHEELS': 'wheels', 'TIRES': 'tires', 'SEATS': 'seats', 'LATCHES/LOCKS/LINKAGES': 'doors, locks & latches', 'BACK OVER PREVENTION': 'backup camera',
        'PARKING BRAKE': 'parking brake', 'HYBRID PROPULSION SYSTEM': 'hybrid system', 'ELECTRONIC STABILITY CONTROL': 'stability control', 'EQUIPMENT': 'equipment'}
part = lambda c: PART.get(c, c.lower().replace('/', ' / '))

# ---- the average car per model year, from what is already published
OUTD = glob.glob(os.path.join(LEMON, 'v3-unreliable*', 'data', 'out'))[0]
cal, bl = collections.defaultdict(lambda: [0, 0]), collections.defaultdict(lambda: [0, 0])
for r in csv.DictReader(open(os.path.join(OUTD, 'model_years.csv'), encoding='utf-8')):
    y = int(r['year']); cal[y][0] += int(r['complaints']); cal[y][1] += int(r['sold_calendar']); bl[y][0] += int(r['complaints']); bl[y][1] += int(float(r['sold_my_est']))
BASE = {y: a / b for y, (a, b) in cal.items()}; BASEB = {y: a / b for y, (a, b) in bl.items()}
for f in json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8')):   # 2000-2009 and 2023-2025: the site's own scored years
    for v in f['years']:
        if v['y'] < 2010 or v['y'] > 2022: cal[('s', v['y'])][0] += v['n']; cal[('s', v['y'])][1] += v['sold']
for k in list(cal):
    if isinstance(k, tuple): BASE[k[1]] = cal[k][0] / cal[k][1]

# ---- complaints
con = sqlite3.connect(os.path.join(LEMON, 'data', 'complaints.db'))
BAD = re.compile(r'\d{5,}|@|https?:|www\.|\bVIN\b|\bMY NAME\b|\bMR\.|\bMRS\.|\bMS\.|\bDR\.|\bLLC\b|\bINC\b|\bthanks?\b|thank you|regards|sincerely|call me|contact me|my number|\b(my|our) (wife|husband|son|daughter|kids?|children)\b', re.I)
def clean(t, names):
    t = re.sub(r'\s*\*[A-Z]{2,3}\b.*$', '', t.strip()); t = re.sub(r'\s+', ' ', t).strip()
    if t.isupper() or sum(ch.isupper() for ch in t) > .6 * sum(ch.isalpha() for ch in t):
        t = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), t.lower()); t = re.sub(r'\bi\b', 'I', t)
        for w in names: t = re.sub(r'\b' + re.escape(w.lower()) + r'\b', w, t)
    return t

def sales_for(p):
    """{calendar or model year: units}, kind, source url, note."""
    src = p.get('sales') or {}
    if src.get('manual'):   # figures typed from a cited table that the parser can't read; every row keeps its own source
        return {int(y): int(v) for y, v in src['manual'].items()}, src.get('kind', 'calendar'), src['url'], src.get('note', '')
    if src.get('gcbc'):
        url = f"https://www.goodcarbadcar.net/{src['gcbc']}-sales-figures/"; cp = os.path.join(HERE, 'data', 'cache', 'gcbc', src['gcbc'] + '.html')
        if not os.path.exists(cp):
            import urllib.request; os.makedirs(os.path.dirname(cp), exist_ok=True)
            open(cp, 'w', encoding='utf-8').write(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'LemonIndexResearch/0.1 (data journalism; lemonindex.com)'}), timeout=30).read().decode('utf-8', 'replace'))
        h = open(cp, encoding='utf-8').read(); got = {}
        for t in re.findall(r'<table[^>]*>.*?</table>', h, re.S):   # the first 'Year | Units' table is the U.S. one (Canada follows)
            hd = [re.sub('<[^>]+>', '', x).strip() for x in re.findall(r'<th[^>]*>(.*?)</th>', t, re.S)]
            if len(hd) >= 2 and hd[0] == 'Year' and hd[1] in ('Units', 'Sales Units'):
                for r in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S):
                    c = [re.sub('<[^>]+>', '', x).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
                    if len(c) >= 2 and re.fullmatch(r'\d{4}', c[0]) and re.fullmatch(r'[\d,]+', c[1]): got[int(c[0])] = int(c[1].replace(',', ''))
                break
        return got, 'calendar', url, 'GoodCarBadCar annual U.S. sales'
    if not src: return {}, 'none', '', 'no sales source'
    title = src.get('wiki') or p['name']
    html = WIKI.fetch(title); url = 'https://en.wikipedia.org/wiki/' + title.replace(' ', '_')
    if src.get('col'):   # a table the generic parser misreads: pick the year column + the U.S. column by regex, first row per year wins
        got, note = {}, ''
        for t in WIKI.tables(html):
            cols = list(t.columns); uc = next((c for c in cols if re.search(src['col'], c)), None)
            if uc is None: continue
            yc = next((c for c in cols if re.search(r'year', c, re.I)), cols[0])
            for _, r in t.iterrows():
                m = re.match(r'^\s*(19[89]\d|20[0-3]\d)(\[\d+\])?\s*$', str(r[yc]))
                v = re.sub(r'\[.*?\]', '', str(r[uc])).replace(',', '').strip()
                if m and re.fullmatch(r'\d+(\.\d+)?', v) and int(m.group(1)) not in got: got[int(m.group(1))] = round(float(v) * src.get('scale', 1))
            note = f'col={uc!r}'
            if got: break
    else:
        got, note = WIKI.us_sales(html, title)
    return got, src.get('kind', 'calendar'), url, note

def run(slug, p):
    makes = set(p['make'].split('|')); rx = re.compile(p['rx']); names = sorted({w for w in re.findall(r'[A-Z][A-Za-z0-9-]{2,}', p['name'])} | {'NHTSA'}, key=len, reverse=True)
    win, allc, comp, ids, sev, nm, miles = collections.Counter(), collections.Counter(), collections.defaultdict(collections.Counter), collections.defaultdict(lambda: collections.defaultdict(list)), \
        collections.defaultdict(lambda: dict(total=0, crash=0, fire=0, towed=0, injured=0, deaths=0)), collections.defaultdict(collections.Counter), collections.defaultdict(list)
    comp_all, tot_all, miles_all = collections.Counter(), collections.Counter(), []
    for odino, make, model, year, ldate, comps, crash, fire, inj, dead, towed, mi in con.execute(
            f'SELECT odino, make, model, year, ldate, comps, crash, fire, injured, deaths, towed, miles FROM complaints WHERE year BETWEEN {Y0} AND {Y1} AND make IN ({",".join("?" * len(makes))})', sorted(makes)):
        if not rx.fullmatch(model or ''): continue
        allc[year] += 1; nm[year][(make, model)] += 1
        for c in set((comps or '').split(' | ')): comp_all[c.split(':')[0].strip() or 'UNKNOWN'] += 1
        tot_all['crash'] += crash == 'Y'; tot_all['fire'] += fire == 'Y'; tot_all['injured'] += (inj or 0) > 0; tot_all['deaths'] += (dead or 0) > 0
        if mi and 0 < mi < 400000: miles_all.append(mi)
        early = year >= 2023
        if not early and not (ldate and int(ldate[:4]) <= year + WINDOW): continue
        win[year] += 1; s = sev[year]; s['total'] += 1; s['crash'] += crash == 'Y'; s['fire'] += fire == 'Y'; s['towed'] += towed == 'Y'
        s['injured'] += (inj or 0) > 0; s['deaths'] += (dead or 0) > 0
        if mi and 0 < mi < 400000: miles[year].append(mi)
        for c in set((comps or '').split(' | ')):
            c = c.split(':')[0].strip() or 'UNKNOWN'; comp[year][c] += 1; ids[year][c].append(odino)
    cs, kind, url, note = sales_for(p)
    sold, into, flags = (mysales.merge(cs, win, p['name'], Y0, Y1) if kind == 'calendar' else ({y: v for y, v in cs.items() if Y0 <= y <= Y1}, {}, []))
    blended = mysales.blend(sold, into, cs) if kind == 'calendar' else sold
    years, xl, years_all = [], {}, []
    med = sorted(win[y] for y in sold if win[y]) or [0]; med = med[len(med) // 2]
    for y in range(Y0, Y1 + 1):
        n = win[y]
        if not allc[y]: continue
        s = sold.get(y); li = None
        if s and s >= MIN_SOLD and y in BASE and n < max(5, .05 * med):   # sales but (almost) no complaints: the model wasn't really sold as that model year
            flags.append(f'{p["name"]} {y}: {s:,} sold but only {n} complaints in window -> not scored')
        elif s and s >= MIN_SOLD and y in BASE:
            li = round(100 * n / (s * BASE[y]))
            if 2010 <= y <= 2022 and blended.get(y): li = min(li, round(100 * n / (blended[y] * BASEB[y])))
        top = [(c, k) for c, k in comp[y].most_common() if c not in ('UNKNOWN OR OTHER', 'UNKNOWN')]
        parts = [[part(c), round(100 * k / max(n, 1))] for c, k in top[:5]]
        pool = list(dict.fromkeys(o for c, _ in top[:2] for o in ids[y][c])); random.Random(f'{slug}{y}').shuffle(pool); qs, seen = [], set()
        for o in pool[:400]:
            row = con.execute('SELECT descr FROM rows WHERE odino=? AND descr IS NOT NULL LIMIT 1', (o,)).fetchone()
            if not row: continue
            t = clean(row[0], names)
            if not (50 <= len(t) <= 230) or BAD.search(t) or t[:40] in seen: continue
            seen.add(t[:40]); qs.append({'odi': o, 'text': t})
            if len(qs) == 3: break
        ms = sorted(miles[y])
        xl[str(y)] = {'sev': sev[y], 'names': [[mk, md, k] for (mk, md), k in nm[y].most_common(4)],
                      'miles': {'median': ms[len(ms) // 2], 'p25': ms[len(ms) // 4], 'p75': ms[3 * len(ms) // 4], 'n': len(ms)} if len(ms) >= 5 else None}
        years_all.append(dict(y=y, n=allc[y], quotes=qs))
        if li is not None: years.append(dict(y=y, li=li, n=n, sold=s, parts=parts, quotes=qs) | ({'early': True} if y >= 2023 else {}))   # like years.json: scored years only
    # the whole-model score: model years 2010-2022 like the study; a model that mostly ended before 2010 uses all its scored years (the page says which)
    scored = [v for v in years if 2010 <= v['y'] <= 2022]
    if len(scored) < 3: scored = [v for v in years if not v.get('early')]
    car = None
    if scored:
        N = sum(v['n'] for v in scored); S_ = sum(v['sold'] for v in scored); EXP = sum(v['sold'] * BASE[v['y']] for v in scored)
        tot = collections.Counter();
        for v in scored:
            for c, k in comp[v['y']].items():
                if c not in ('UNKNOWN OR OTHER', 'UNKNOWN'): tot[c] += k
        ser = sum(sev[v['y']]['crash'] + sev[v['y']]['fire'] + sev[v['y']]['injured'] for v in scored)
        car = dict(name=p['name'], brand=p['brand'], segment=p['seg'], years=f'{scored[0]["y"]}-{scored[-1]["y"]}', sold=S_, n=N, per100k=round(N / S_ * 1e5),
                   expected=EXP, li=round(100 * N / EXP), serious=round(100 * ser / max(N, 1)), worst=str(max(scored, key=lambda v: v['li'])['y']),
                   issues=[[part(c), round(100 * k / N)] for c, k in tot.most_common(3)], sales_url=url, sales_kind=kind)
    ms = sorted(miles_all); n_all = sum(allc.values()); tp = sum(k for c, k in comp_all.items() if c not in ('UNKNOWN OR OTHER', 'UNKNOWN')) or 1
    by = {y: allc[y] for y in sorted(allc) if allc[y]}
    extra = dict(id=slug, name=p['name'], brand=p['brand'], a=min(by) if by else Y0, b=max(by) if by else Y1, n=n_all, by_year={str(y): v for y, v in by.items()},
                 parts=[[part(c), round(100 * k / tp)] for c, k in comp_all.most_common() if c not in ('UNKNOWN OR OTHER', 'UNKNOWN')][:6],
                 crash=tot_all['crash'], fire=tot_all['fire'], injured=tot_all['injured'], deaths=tot_all['deaths'],
                 miles={'median': ms[len(ms) // 2], 'p25': ms[len(ms) // 4], 'p75': ms[3 * len(ms) // 4], 'n': len(ms)} if len(ms) >= 5 else None,
                 quotes=[dict(y=v['y'], odi=q['odi'], text=q['text']) for v in sorted(years_all, key=lambda v: -v['n'])[:3] for q in v['quotes'][:1]])
    return dict(id=slug, name=p['name'], years=years), car, xl, extra, dict(slug=slug, sales=cs, kind=kind, url=url, note=note, flags=flags, complaints=sum(allc.values()),
                                                                     scored=[v['y'] for v in years if v['li'] is not None])

# ---- the same public APIs as data_fetch_api.py (its own functions and disk cache)
src = open(os.path.join(HERE, 'data_fetch_api.py'), encoding='utf-8').read(); src = src[:src.index('# ---------- run ----------')]
API = {'__file__': os.path.join(HERE, 'data_fetch_api.py')}
src = src.replace("LOCAL = json.load(open(os.path.join(HERE, 'data', 'extras_local.json'), encoding='utf-8'))", 'LOCAL = {}')
exec(compile(src, 'data_fetch_api.py', 'exec'), API)

def load(n): p = os.path.join(HERE, 'data', n); return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else ({} if 'years' not in n and 'cars' not in n else [])
Y_, C_, XL_, XA_ = load('years_new.json'), load('cars_new.json'), load('extras_local_new.json'), load('extras_api_new.json')
EX_ = load('extra_models_new.json') or {}
Y_ = {f['id']: f for f in Y_}; C_ = {c['id']: c for c in C_}
report = []
for slug, p in PLAN.items():
    if ONLY and slug not in ONLY: continue
    if p.get('dupe_of'): print(f"{p['name']}: duplicate of /cars/{p['dupe_of']}/ (its card links there)"); continue
    fam, car, xl, extra, rep = run(slug, p); report.append(rep)
    if car and fam['years']: Y_[slug] = fam; XL_[slug] = xl; C_[slug] = dict(car, id=slug); EX_.pop(slug, None)
    else: Y_.pop(slug, None); C_.pop(slug, None); XL_.pop(slug, None); EX_[slug] = extra
    API['MAKES'][p['name']] = p['make'].split('|')
    if p.get('fe'): API['FE_MODEL'][p['name']] = p['fe']
    jobs = [(y, xl[y]) for y in sorted(xl)]
    def one(j):
        y, e = j; nms = API['main_names'](e) if e['names'] else [(p['make'].split('|')[0], p['name'].split(' ', 1)[1].upper())]
        return y, {'recalls': API['recalls'](y, nms), 'safety': API['safety'](y, nms, p['name']) if int(y) >= 2011 else None, 'mpg': API['mpg'](p['name'], int(y))}
    with cf.ThreadPoolExecutor(6) as ex: api = dict(ex.map(one, jobs))
    if slug in EX_:   # complaints-only: recalls across all years, each with the model years it covers
        rc = {}
        for y, d in api.items():
            for r in d['recalls']: rc.setdefault(r['id'], dict(r, years=[])); rc[r['id']]['years'].append(int(y))
        EX_[slug]['recalls'] = sorted(rc.values(), key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2], reverse=True)
        XA_.pop(slug, None)
    else: XA_[slug] = api
    print(f"{p['name']}: {rep['complaints']:,} complaints, {'scored years ' + str(rep['scored']) if slug in C_ else 'COMPLAINTS ONLY'}, sales {rep['kind']} {rep['note']} {rep['url']}", flush=True)
    for fl in rep['flags']: print('   ', fl)
json.dump(list(Y_.values()), open(os.path.join(HERE, 'data', 'years_new.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(list(C_.values()), open(os.path.join(HERE, 'data', 'cars_new.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
json.dump(XL_, open(os.path.join(HERE, 'data', 'extras_local_new.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(XA_, open(os.path.join(HERE, 'data', 'extras_api_new.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(EX_, open(os.path.join(HERE, 'data', 'extra_models_new.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(report, open(os.path.join(HERE, 'data', 'new_models_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
