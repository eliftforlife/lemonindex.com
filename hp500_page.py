# 11-25 (Elijah): /best/cheapest-500-hp-cars/, the 10 cheapest cars you can buy that make 500+ horsepower.
# Run by seo_pages.py with exec() (after best_ui.py, before the /best/ hub, which shows HP5_CARD).
# 11-25 v2 (Elijah: "get hp for all cars ... and rebuild"; "suvs trucks and supercars and performance cars all are allowed"):
#   horsepower  performance cars: data/perf/<slug>.json (factory ratings with their sources)
#               regular models:   data/hp500_hp.json (data_hp500.py, from 3 Lemon Index/data/hp: every version of all 613 generations, with source URLs)
#               cars we only know by engine (S63, XKR, Bentley ...): data/supercar_engines.json, the LOWEST rating that engine had (shown as "518+")
#   price       data/price_est.json when a table prices the 500 hp version itself (the price box's data: private-party price at the year's typical miles);
#               else data/hp500_prices.json, an AI estimate made for that fast version (never the base model's price: an M5 is not a 5 Series price)
#   YouTube     performance cars only: the generation's YouTube owner tone, computed as perf_page.build() does (data/yt_scores.json, else the car's study)
# Ranking: each car's cheapest model year that makes 500+ hp (middle of the private-party range), one entry per car (its cheapest generation).
# Nothing here is hand-typed except which version each price is for (HP5_CARS / HP5_EST) and the display names, body types and links.
import json as _h5j, os as _h5o, re as _h5r
HP5_URL = '/best/cheapest-500-hp-cars/'
# (perf slug, body, [(generation id, [variant ids the price table prices])], price model)
HP5_CARS = [
    ('bmw-x5-m', 'SUV', [('e70', ['e70-x5']), ('f85', ['f85-x5']), ('f95', ['f95-x5'])], 'bmw-x5-m'),
    ('cts-v', 'Sedan', [('g2', ['g2-sedan']), ('g3', ['g3-v'])], 'cts-v'),
    ('shelby-gt500', 'Coupe', [('s197-54', ['s197-07', 's197-10', 's197-11']), ('s197-58', ['s197-13']), ('s550', ['s550'])], 'shelby-gt500'),
    ('camaro-zl1', 'Coupe', [('g5', ['g5-cpe']), ('g6', ['g6-at'])], 'camaro-zl1'),
    ('charger-hellcat', 'Sedan', [('ld', ['ld-hellcat', 'ld-hellcat-wb'])], 'charger-hellcat'),
    ('challenger-hellcat', 'Coupe', [('lc', ['lc-hellcat', 'lc-hellcat-19'])], 'challenger-hellcat'),
    ('shelby-gt350', 'Coupe', [('s550', ['s550-16', 's550-17', 's550-19'])], 'shelby-gt350'),
    ('trackhawk', 'SUV', [('wk2', ['wk2-trackhawk'])], 'trackhawk'),
    ('ram-trx', 'Truck', [('dt', ['dt-trx'])], 'ram-trx'),
    ('durango-srt', 'SUV', [], 'durango-srt'),   # the table prices the 475 hp SRT 392 (the Hellcat only as a % on top): never eligible, kept for the record
]
# supercars: (supercars.json name, body, price model, years) where every engine our data maps to those years is rated 500+ hp
HP5_SUPER = [('Bentley Continental GT', 'Coupe', 'bentley-continental-gt', (2010, 2012)),
             ('Rolls-Royce Ghost', 'Sedan', 'rolls-royce-ghost', (2010, 2025)),
             ('Bentley Bentayga', 'SUV', 'bentley-bentayga', (2017, 2018)),
             ('Chevrolet Corvette Z06', 'Coupe', 'chevrolet-corvette-z06', (2019, 2025))]
# just under 500 hp (one line under the list)
HP5_NEAR = [('charger-392', 'ld12', ['ld12-srt8'], 'charger-392'), ('chrysler-300-srt8', 'ld', ['ld-srt8'], 'chrysler-300-srt8'),
            ('challenger-392', 'lc11', ['lc11-srt8'], 'challenger-392')]
# 11-25 v2: versions priced by data/hp500_prices.json: key there -> (display name, body, electric?, link override).
# Link default: regular models -> that model year's page (/cars/<model>/<year>/); engine-only cars -> the engine's page; perf -> the perf page.
HP5_EST = {
    'ml63': ('Mercedes ML63 AMG', 'SUV', False, None), 'rrs': ('Range Rover Sport Supercharged', 'SUV', False, None),
    'e63': ('Mercedes E63 AMG', 'Sedan', False, None), 'm5': ('BMW M5', 'Sedan', False, '/cars/bmw-m5/'),
    'model-s': ('Tesla Model S P85D', 'Sedan', True, None), 'model-x': ('Tesla Model X 90D', 'SUV', True, None),
    'srt10': ('Dodge Ram SRT-10', 'Truck', False, None), 'lightning': ('Ford F-150 Lightning Extended Range', 'Truck', True, None),
    'z06': ('Chevrolet Corvette Z06', 'Coupe', False, None), 'c63s': ('Mercedes-AMG C63 S', 'Sedan', False, '/cars/amg-c63/'),
    'glc63': ('Mercedes-AMG GLC63 S', 'SUV', False, None), 'sq7': ('Audi SQ7', 'SUV', False, None), 'x5-m50i': ('BMW X5 M50i', 'SUV', False, None),
    'x3m': ('BMW X3 M Competition', 'SUV', False, None), 'm550i': ('BMW M550i xDrive', 'Sedan', False, None),
    'dark-horse': ('Ford Mustang Dark Horse', 'Coupe', False, None), 'rs7': ('Audi RS 7', 'Hatchback', False, None),
    'xfr': ('Jaguar XFR', 'Sedan', False, '/cars/jaguar-xf/'), 's63': ('Mercedes S63 AMG', 'Sedan', False, None), 'm6': ('BMW M6', 'Coupe', False, None),
    'xkr': ('Jaguar XKR', 'Coupe', False, None), 'cls63': ('Mercedes CLS63 AMG', 'Sedan', False, None), 'gl63': ('Mercedes GL63 AMG', 'SUV', False, None),
    'cl63': ('Mercedes CL63 AMG', 'Coupe', False, None), 'stelvio-qv': ('Alfa Romeo Stelvio Quadrifoglio', 'SUV', False, None),
    'giulia-qv': ('Alfa Romeo Giulia Quadrifoglio', 'Sedan', False, None), 'f-type-r': ('Jaguar F-Type R', 'Coupe', False, None)}
# one entry per car: these keys / supercar names are the same car (the C6 Z06 is in the regular Corvette data, later ones are supercars)
HP5_FAM = {'z06': 'corvette-z06', 'Chevrolet Corvette Z06': 'corvette-z06'}
HP5_IMG = {'xfr': 'jaguar-xf'}   # engine-only cars whose regular model has an AI picture of that generation (the 2011 XF)
# 11-25 v3 (Elijah: "no engine pictures"): engine-only cars get a car picture of the priced generation, never the engine illustration.
# The XKR reuses the perf picture (X150, 2010); the W221 S63 and E63 M6 were made for this page (gpt-image-2 low, rembg cutout,
# 3 Lemon Index/car images test/hp500/gen_hp500.py + cut_hp500.py).
HP5_IMGF = {'s63': '/assets/ai-perf/amg-s63-w221.webp?v=1', 'm6': '/assets/ai-perf/bmw-m6-e63.webp?v=1', 'xkr': '/assets/ai-perf/jaguar-xkr.webp?v=1'}
# 11-25 v3: the two bars in each card come in two styles (A = where it sits on the list, B = two number tiles). Elijah picked B (11-25); HP5_BARS=A builds A.
HP5_BARS = (_h5o.environ.get('HP5_BARS') or 'B').upper()


def _h5_load(p, d=None):
    try: return _h5j.load(open(p, encoding='utf-8'))
    except Exception: return d


def _h5_years(s):
    """'2009–2014' / '2021, 2023–2025' / '2024–' -> set of years"""
    out = set()
    for part in str(s or '').split(','):
        m = _h5r.match(r'\s*(\d{4})\s*(?:[–-]\s*(\d{4})?)?\s*$', part)
        if not m: continue
        a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else (2026 if _h5r.search(r'[–-]\s*$', part) else a)
        out.update(range(a, b + 1))
    return out


_H5P = _h5_load('data/price_est.json', {}) or {}
_H5YT = _h5_load('data/yt_scores.json', {}) or {}
_H5SY = _h5_load('data/supercar_engine_yt.json', {}) or {}
_H5PC = {c['slug']: c for c in (_h5_load('data/perf_cars.json', []) or [])}
_H5ENG = _h5_load('data/supercar_engines.json', {}) or {}
_H5HP = (_h5_load('data/hp500_hp.json', {}) or {}).get('gens') or {}
_H5EP = (_h5_load('data/hp500_prices.json', {}) or {}).get('cars') or []
_H5EPH = _h5_load('data/supercar_engine_photos.json', {}) or {}


def _h5_url_links(urls):
    """source URLs (data/hp) -> links named after the page ('Wikipedia: Mercedes-Benz GLE-Class', else the site)"""
    from urllib.parse import urlparse, unquote
    out = []
    for u in urls or []:
        if not str(u).startswith('http'): continue
        h = urlparse(u).netloc.replace('www.', '')
        t = ('Wikipedia: ' + unquote(u.rstrip('/').rsplit('/', 1)[-1]).replace('_', ' ')) if 'wikipedia.org' in h else h
        out.append(f'<a href="{E(u)}" rel="noopener nofollow" target="_blank">{E(t)}</a>')
    return out


def _h5_est(r):
    """one data/hp500_prices.json row -> an entry, with its hp from our data (or None when the data doesn't back 500+ hp that year)"""
    cfg = HP5_EST.get(r['key'])
    if not cfg: return None
    name, body, ev, href = cfg
    y = r['year']; e = {'kind': 'est', 'key': r['key'], 'fam': HP5_FAM.get(r['key'], r['key']), 'name': name, 'body': body, 'ev': ev, 'y': y,
                        'mi': r['miles'], 'lo': r['lo'], 'hi': r['hi'], 'mid': (r['lo'] + r['hi']) / 2, 'yt': None, 'img': None}
    if r.get('gen'):
        G = _H5HP.get(r['gen']) or {}
        v = next((v for v in G.get('variants', []) if v['trim'] == r['trim'] and v['years'][0] <= y <= v['years'][1]), None)
        if not v or v['hp'] < 500: return None
        e.update(hp=v['hp'], hp_txt=f'{v["hp"]:,}', eng_txt=v['engine'], src=_h5_url_links(v['src']), note=G.get('notes') or '',
                 span=f'{v["years"][0]}–{v["years"][1]}' if v['years'][1] > v['years'][0] else str(y), href=href or f'/cars/{G["model"]}/{y}/')
        yi = None if YSL.no_img(G['model'], y) else (YSL.AIY.get(G['model']) or {}).get(str(y))
        yi = yi or YSL.model_img(G['model'])
        if yi: e['img'] = {'src': yi['src'], 'w': yi['w'], 'h': yi['h']}
    elif r.get('perf'):
        D = _h5_load(f'data/perf/{r["perf"]}.json')
        g = next((g for g in (D or {}).get('gens', []) for v in g['variants'] if v['id'] == r['variant']), None)
        v = next((v for v in (g or {}).get('variants', []) if v['id'] == r['variant']), None)
        hp = ((v or {}).get('hp') or {}).get('v')
        if not v or not isinstance(hp, (int, float)) or hp < 500 or y not in _h5_years(v.get('years')): return None
        e.update(hp=hp, hp_txt=f'{hp:,}', eng_txt=g['code'].split(' / ')[0], src=_h5_src_links(D, v['hp'].get('src') or []), note='',
                 span=v['years'].replace('-', '–'), href=href or D.get('page') or f'/cars/{r["perf"]}/', img=_h5_img(D, g, y))
    elif r.get('eng'):
        cars = _H5ENG.get('cars') or {}; eng = _H5ENG.get('engines') or {}
        es = [k for k, ys in (cars.get(r['eng']) or {}).items() if y in ys]
        if not es or any((eng.get(k) or {}).get('hp', [0])[0] < 500 for k in es): return None   # every engine that year must be rated 500+ hp
        lo_hp = min(eng[k]['hp'][0] for k in es)
        ys = sorted({yy for k in es for yy in cars[r['eng']][k]})
        e.update(hp=lo_hp, hp_txt=f'{lo_hp:,}+', eng_txt=' / '.join((eng[k].get('name') or k).replace((eng[k].get('make') or '') + ' ', '', 1) for k in es), eng=[eng[k] for k in es],
                 src=[f'<a href="{E(s["url"])}" rel="noopener nofollow" target="_blank">{E(s["title"])}</a>' for k in es for s in (eng[k].get('src') or [])[:2]],
                 note='', span=f'{ys[0]}–{ys[-1]}' if len(ys) > 1 else str(y), href=href or f'/engines/{es[0]}/')
        ph = _H5EPH.get(es[0]); mi = YSL.model_img(HP5_IMG[r['key']]) if r['key'] in HP5_IMG else None
        if r['key'] in HP5_IMGF: e['img'] = {'src': HP5_IMGF[r['key']], 'w': 1000, 'h': 600}
        elif mi: e['img'] = {'src': mi['src'], 'w': mi['w'], 'h': mi['h']}
        elif ph: e['img'] = {'src': ph['src'], 'w': ph['w'], 'h': ph['h']}; e['img_eng'] = True
    else: return None
    return e


def _h5_price(model, y):
    """(typical miles, private lo, private hi) at the year's typical miles, or None"""
    r = ((_H5P.get('m') or {}).get(model) or {}).get('y', {}).get(str(y))
    return (r[0], r[2][0], r[2][1]) if r and r[2] and r[2][0] else None


def _h5_img(D, g, y):
    """a picture of that generation: its own AI picture, else the car's when it shows this generation, else the regular model's year picture"""
    if g.get('img'): return {'src': g['img'], 'w': 1000, 'h': 600}
    pc = _H5PC.get(D['slug']) or {}
    src = D.get('img') or pc.get('img')
    if src and pc.get('img_year') and g['y0'] <= pc['img_year'] <= g['y1']: return {'src': src, 'w': pc.get('w', 1000), 'h': pc.get('h', 600)}
    import perf_page as _h5pp
    par = _h5pp.PARENTS.get(D['slug'], '')
    yi = (YSL.AIY.get(par) or {}).get(str(y)) if par else None
    return {'src': yi['src'], 'w': yi['w'], 'h': yi['h']} if yi else None


def _h5_yt(D, g):
    A = _h5_load(f'data/perf/{D["slug"]}.auto.json', {}) or {}
    SCY = {**(A.get('scores') or {}), **_H5SY}
    YS = _H5YT.get(D.get('yt_model') or '', {}) or (SCY.get(D.get('yt_study') or '') or {}).get('years') or {}
    s = [v['score'] for y, v in YS.items() if g['y0'] <= int(y) <= g['y1'] and v and v.get('score') is not None]
    return int(sum(s) / len(s) + 0.5) if s else None


def _h5_src_links(D, ids):
    out = []
    for k in ids:
        s = D['sources'].get(k)
        if s: out.append(f'<a href="{E(s["u"])}" rel="noopener nofollow" target="_blank">{E(s["t"])}</a>')
    return out


def _h5_perf(slug, gens, model, body=None):
    """every eligible (gen, variant, year) of a performance car -> its cheapest generation's entry (or None)"""
    D = _h5_load(f'data/perf/{slug}.json')
    if not D: return None
    best = None
    for gid, vids in gens:
        g = next((x for x in D['gens'] if x['id'] == gid), None)
        if g is None: continue
        rows = []
        for v in g['variants']:
            hp = (v.get('hp') or {}).get('v')
            if v['id'] not in vids or not isinstance(hp, (int, float)) or hp < 500: continue   # (the near list passes its own threshold below)
            for y in sorted(_h5_years(v.get('years'))):
                if not g['y0'] <= y <= (g.get('y1') or y): continue
                p = _h5_price(model, y)
                if p: rows.append((y, v, p))
        if not rows: continue
        y, v, p = min(rows, key=lambda r: ((r[2][1] + r[2][2]) / 2, r[0]))
        e = {'kind': 'perf', 'D': D, 'g': g, 'v': v, 'y': y, 'hp': v['hp']['v'], 'hp_txt': f'{v["hp"]["v"]:,}', 'mi': p[0], 'lo': p[1], 'hi': p[2],
             'mid': (p[1] + p[2]) / 2, 'name': D['name'], 'href': D.get('page') or f'/cars/{slug}/', 'body': body, 'gen': g,
             'span': f'{min(r[0] for r in rows)}–{max(r[0] for r in rows)}' if len({r[0] for r in rows}) > 1 else str(y),
             'hp_range': sorted({r[1]['hp']['v'] for r in rows}), 'src': _h5_src_links(D, v['hp'].get('src') or [])}
        if best is None or e['mid'] < best['mid']: best = e
    return best


def _h5_super(name, body, model, yrs):
    cars = _H5ENG.get('cars') or {}; eng = _H5ENG.get('engines') or {}
    slug = _slg(name); m = cars.get(slug) or {}
    rows = []
    for y in range(yrs[0], yrs[1] + 1):
        es = [k for k, ys in m.items() if y in ys]
        if not es or any((eng.get(k) or {}).get('hp', [0])[0] < 500 for k in es): continue   # every engine that year must be rated 500+ hp
        p = _h5_price(model, y)
        if p: rows.append((y, es, p))
    if not rows: return None
    y, es, p = min(rows, key=lambda r: ((r[2][1] + r[2][2]) / 2, r[0]))
    lo_hp = min(eng[k]['hp'][0] for k in es)
    srcs = [f'<a href="{E(s["url"])}" rel="noopener nofollow" target="_blank">{E(s["title"])}</a>' for k in es for s in (eng[k].get('src') or [])[:2]]
    ph = _vimg(name)
    return {'kind': 'super', 'y': y, 'hp': lo_hp, 'hp_txt': f'{lo_hp:,}+', 'mi': p[0], 'lo': p[1], 'hi': p[2], 'mid': (p[1] + p[2]) / 2, 'name': name,
            'href': f'/supercars/{slug}/', 'body': body, 'eng': [eng[k] for k in es], 'img': ph, 'img_year': (_h5_load('data/ai_vehicle_images.json', {}) or {}).get(name, {}).get('year'),
            'span': f'{min(r[0] for r in rows)}–{max(r[0] for r in rows)}' if len(rows) > 1 else str(y), 'src': srcs, 'yt': None}


def _h5_list():
    L = []
    for slug, body, gens, model in HP5_CARS:
        e = _h5_perf(slug, gens, model, body)
        if e:
            e['img'] = _h5_img(e['D'], e['g'], e['y']); e['yt'] = _h5_yt(e['D'], e['g']); L.append(e)
    for name, body, model, yrs in HP5_SUPER:
        e = _h5_super(name, body, model, yrs)
        if e: L.append(e)
    for e in L: e['fam'] = HP5_FAM.get(e['name'], e['D']['slug'] if e['kind'] == 'perf' else e['name'])
    L += [e for e in map(_h5_est, _H5EP) if e]   # 11-25 v2: regular models, engine-only cars and unpriced perf versions (data/hp500_prices.json)
    best = {}
    for e in sorted(L, key=lambda e: (e['mid'], e['y'])): best.setdefault(e['fam'], e)   # one entry per car: its cheapest generation
    return sorted(best.values(), key=lambda e: (e['mid'], e['y']))


def _h5_near():
    out = []
    for slug, gid, vids, model in HP5_NEAR:
        D = _h5_load(f'data/perf/{slug}.json')
        g = next((x for x in (D or {}).get('gens', []) if x['id'] == gid), None)
        if g is None: continue
        for v in g['variants']:
            hp = (v.get('hp') or {}).get('v')
            if v['id'] not in vids or not isinstance(hp, (int, float)) or not 450 <= hp < 500: continue
            ps = [(y, _h5_price(model, y)) for y in sorted(_h5_years(v.get('years'))) if _h5_price(model, y)]
            if ps:
                y, p = min(ps, key=lambda r: (r[1][1] + r[1][2]) / 2)
                out.append({'name': f"{D['make']} {v['name'].split(' / ')[0]}" if not v['name'].startswith(D['make']) else v['name'], 'href': D.get('page') or f'/cars/{slug}/', 'y': y, 'hp': hp, 'lo': p[1], 'hi': p[2], 'mid': (p[1] + p[2]) / 2,
                            'vname': v['name'], 'src': _h5_src_links(D, v['hp'].get('src') or [])})
    return sorted(out, key=lambda e: e['mid'])


def _h5_short(e):
    """'BMW X5 M (E70)' / 'Cadillac CTS-V (2nd gen)'"""
    if e['kind'] != 'perf': return e['name'].replace('Ram 1500 TRX', 'Ram TRX')
    nm = e['D']['name'].split(' / ')[0]
    return f'{nm} ({e["g"]["code"].split(" / ")[0]})' if len(e['D']['gens']) > 1 else nm


def _h5_k(v): return f'${int(v / 1000 + 0.5)}K'   # whole thousands: '$12.5K' wrapped in the chart's value column


def _h5_kk(v):
    """$8K / $11.5K (half thousands kept)"""
    return f'${round(v / 500) / 2:g}K'


def _h5_bars(e, L):
    """the card's price + power: option A = a scale from the list's cheapest to priciest (least to most powerful), B = two number tiles"""
    plo, phi = min(x['lo'] for x in L), max(x['hi'] for x in L)
    hlo, hhi = min(x['hp'] for x in L), max(x['hp'] for x in L)
    mi = f'at ~{round(e["mi"] / 1000)}K miles'
    hpu = 'hp combined' if e.get('ev') else 'hp'
    if HP5_BARS == 'B':
        pw = max(4, e['mid'] / phi * 100); hw = 6 + 94 * (e['hp'] - hlo) / max(1, hhi - hlo)   # power across this list's range (500-691 hp), so 503 vs 555 shows
        return ('<div class="h5t">'
                f'<div class="h5t-c"><span class="h5t-l">Price</span><b class="h5t-v">{_h5_kk(e["lo"])[:-1]}–{_h5_kk(e["hi"])[1:]}</b>'
                f'<span class="h5t-b" aria-hidden="true"><i style="width:{pw:.1f}%"></i></span><span class="h5t-s">{mi}</span></div>'
                f'<div class="h5t-c"><span class="h5t-l">Power</span><b class="h5t-v">{e["hp_txt"]}<small> hp</small></b>'
                f'<span class="h5t-b" aria-hidden="true"><i class="pw" style="width:{hw:.1f}%"></i></span><span class="h5t-s h5t-x"><span>{hlo:,}</span><span>{hhi:,} hp</span></span></div></div>')   # the bar's scale: this list's least to most powerful
    span = max(1, phi - plo); a = (e['lo'] - plo) / span * 100; w = (e['hi'] - e['lo']) / span * 100
    hp = (e['hp'] - hlo) / max(1, hhi - hlo)
    return ('<div class="h5m">'
            f'<div class="h5m-t"><span class="h5m-l">Price<small>{mi}</small></span><b class="h5m-v">{PRICEBOX._rng(e["lo"], e["hi"])}</b></div>'
            f'<span class="h5m-b" aria-hidden="true"><i style="left:{a:.1f}%;width:{w:.1f}%"></i></span>'
            f'<span class="h5m-x" aria-hidden="true"><span>Cheapest {_h5_kk(plo)}</span><span>{_h5_kk(phi)} priciest</span></span></div>'
            '<div class="h5m">'
            f'<div class="h5m-t"><span class="h5m-l">Power</span><b class="h5m-v">{e["hp_txt"]}<small> {hpu}</small></b></div>'
            f'<span class="h5m-b" aria-hidden="true"><i class="pw" style="left:calc((100% - 16px) * {hp:.3f})"></i></span>'
            f'<span class="h5m-x" aria-hidden="true"><span>{hlo:,} hp</span><span>{hhi:,} hp</span></span></div>')


def _hp500_page():
    global HP5_CARD
    L = _h5_list()[:10]
    if len(L) < 10: print('hp500: only', len(L), 'cars');
    if not L: return
    near = [n for n in _h5_near()[:2] if n['mid'] < L[0]['mid']]   # 11-25 v2: only when a car just under 500 hp is cheaper than the #1 (else it isn't worth a line)
    dt = (_H5P.get('date') or 'November 2026')
    mxp = max(e['hi'] for e in L) * 1.05
    one = L[0]

    def plain(e): return (e['D']['name'].split(' / ')[0] if e['kind'] == 'perf' else e['name'])
    def title(e): return f'{e["y"]} {E(plain(e))}'

    def card(i, e):
        # 11-25 Eli pass (phone): the priced year in the title, one short line (type, generation, its years, YouTube score), two bars
        why = E(('Electric ' + e['body'].lower()) if e.get('ev') else e['body'])
        if e['kind'] == 'perf' and len(e['D']['gens']) > 1: why += f' · {E(e["g"]["code"].split(" / ")[0])}'
        if e['kind'] == 'super': why += ' · ' + ' / '.join(E(x.get('layout') or '') for x in e['eng'])
        if e['kind'] == 'est' and not e['eng_txt'].lower().startswith('electric'): why += ' · ' + E(e['eng_txt'])
        why += f' · {e["span"]}' if '–' in e['span'] else ''
        if e.get('yt') is not None: why += f' · YouTube score {e["yt"]}/100'
        ms = _h5_bars(e, L)   # 11-25 v3 (Elijah: "simpler, better, easier to see"): two styles to pick from (HP5_BARS)
        ph = e.get('img')
        alt = f'{e["name"]}' + (f' ({e["img_year"]} model shown)' if e.get('img_year') and e['kind'] == 'super' else '') + ', AI illustration'
        if e.get('img_eng'): alt = f'{e["eng_txt"]} engine of the {e["name"]}, AI illustration'
        im = (f'<span class="bph"><img src="{ph["src"]}" alt="{E(alt)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async"></span>' if ph else '<span class="bph"></span>')
        return cbx_card(f'hp5-{i}', i, im, f'<a href="{e["href"]}">{title(e)}</a>', why, ms)

    chart = cbx_chart([(f'#hp5-{i}', f'<b>{i}</b> {E(plain(e))}', e['mid'], _h5_k(e['mid']), 'pick') for i, e in enumerate(L, 1)], mxp,
                      'Estimated private-seller price (middle of the range) of each car&#39;s cheapest 500 hp model year, at the miles most of those cars have. Tap a car.', avg=False)
    nearl = ''
    if near:
        nearl = ('<p class="hp5-near">Just under 500 hp: ' + '; '.join(f'<a href="{n["href"]}">{n["y"]} {E(n["name"])}</a> ({n["hp"]} hp, about {PRICEBOX._rng(n["lo"], n["hi"])})' for n in near) + '.</p>')
    lst = (f'<section class="cbx-sec cbx-list"><h2>The 10 cheapest</h2>{chart}<ol class="cbx-cards">' + ''.join(card(i, e) for i, e in enumerate(L, 1)) + f'</ol>{nearl}'
           f'<p class="bud-note hp5-note">Prices are AI estimates for {E(dt)}, not listings.'
           + (' + = the lowest rating that engine had.' if any(e['hp_txt'].endswith('+') for e in L) else '')
           + (' Tesla hp = combined motor output (Tesla doesn&#39;t publish it).' if any(e.get('ev') for e in L) else '') + '</p></section>')
    # FAQ: only what the list shows
    sed = next((e for e in L if e['body'] == 'Sedan'), None); cpe = next((e for e in L if e['body'] == 'Coupe'), None)
    suv = next((e for e in L if e['body'] == 'SUV'), None); evc = next((e for e in L if e.get('ev')), None)
    h700 = next((e for e in L if e['hp'] >= 700), None)
    nm = lambda e: f'{e["y"]} {plain(e)}'
    faq = [('What is the cheapest car with 500 horsepower?',
            f'The {nm(one)}: {one["hp_txt"]} hp for about {PRICEBOX._rng(one["lo"], one["hi"])} from a private seller (Lemon Index AI estimate, {dt}). '
            f'Next are the {nm(L[1])} (about {PRICEBOX._rng(L[1]["lo"], L[1]["hi"])}) and the {nm(L[2])} (about {PRICEBOX._rng(L[2]["lo"], L[2]["hi"])}).')]
    if sed: faq.append(('What is the cheapest 500 hp sedan?', f'The {nm(sed)}: {sed["hp_txt"]} hp for about {PRICEBOX._rng(sed["lo"], sed["hi"])}.'))
    if suv: faq.append(('What is the cheapest 500 hp SUV?', f'The {nm(suv)}: {suv["hp_txt"]} hp for about {PRICEBOX._rng(suv["lo"], suv["hi"])}.'))
    if cpe: faq.append(('What is the cheapest 500 hp coupe?', f'The {nm(cpe)}: {cpe["hp_txt"]} hp for about {PRICEBOX._rng(cpe["lo"], cpe["hi"])}.'))
    if evc: faq.append(('What is the cheapest electric car with 500 horsepower?', f'The {nm(evc)}: {evc["hp_txt"]} hp combined for about {PRICEBOX._rng(evc["lo"], evc["hi"])}. '
                         "Tesla doesn't publish horsepower; that is the combined motor output Wikipedia lists."))
    if h700: faq.append(('What is the cheapest car with 700 horsepower?', f'The {nm(h700)}: {h700["hp_txt"]} hp for about {PRICEBOX._rng(h700["lo"], h700["hi"])}.'))
    if near: faq.append(('Which cars are just under 500 hp?', ' '.join(f'The {n["y"]} {n["name"]} makes {n["hp"]} hp and costs about {PRICEBOX._rng(n["lo"], n["hi"])}.' for n in near)))
    faq.append(('Where do the prices come from?', f'They are Lemon Index estimates made with AI for {dt}, not listings or an appraisal: a fair private-seller price for the 500 hp version itself, an average car with a clean title at the miles most cars of that year have. '
                'Fast cars swing with miles, modifications and how hard they were driven, so check real listings and get an inspection before you buy.'))
    # 11-25 Eli pass: one short paragraph per topic, the horsepower sources one car per line (no wall of text)
    src = (f'<b>Prices:</b> Lemon Index AI estimates ({E(dt)}) of a fair private-seller price for the 500 hp version itself, at the model year&#39;s typical miles, average condition, clean title. '
           'Not listings or an appraisal. Where our price table prices that exact version (like the X5 M), the list uses it. '
           'Where it only prices the regular model (an ML350, not an ML63 AMG), we estimated the fast version on its own.<br><br>'
           '<b>Ranking:</b> each car&#39;s cheapest model year with 500 hp or more, by the middle of its price range, one entry per car (its cheapest generation). '
           'Cars, SUVs, trucks, electric cars and supercars all count.<br><br>'
           + ('<b>YouTube score:</b> how the most-watched YouTube videos about that generation talk about it, out of 100 (performance cars only).<br><br>' if any(e.get('yt') is not None for e in L) else '')
           + '<b>Horsepower:</b> factory ratings from the maker&#39;s specs, press releases and Wikipedia, the same sources as our car pages. '
           'A + is the lowest rating that car&#39;s engine had (Wikipedia), so every car of those years makes at least that. '
           'Tesla doesn&#39;t publish horsepower: its numbers are the combined motor outputs Wikipedia lists.<br><br>'
           '<b>By car</b> (horsepower source · where the price comes from):<br>'
           + '<br>'.join(f'{E(plain(e))}: ' + ', '.join(e['src'][:2]) + (' · own estimate' if e['kind'] == 'est' else ' · price table') for e in L if e['src']))
    lede = (f'The cheapest 500 hp car is the {nm(one)}: {one["hp_txt"]} hp for about {PRICEBOX._rng(one["lo"], one["hi"])}. '
            f'The top 10, with factory horsepower and estimated {dt.split(" ")[-1]} prices.')
    # 11-25 v3 (Elijah: "improve the top"): no gray box. The #1 car's picture big, then its name and its two numbers as big figures under it
    # (CSS order moves the hero's line under the picture; spans only, since it sits in a <p>)
    ans = (f'<span class="h5w-k">Cheapest 500 hp car</span><a class="h5w-n" href="#hp5-1">{nm(one)}</a>'
           f'<span class="h5w-st"><span><b>{PRICEBOX._rng(one["lo"], one["hi"])}</b><small>estimated price</small></span>'
           f'<span><b>{one["hp_txt"]}</b><small>{"hp combined" if one.get("ev") else "horsepower"}</small></span></span>')
    css = ('<style>'
           # hero: the picture bigger, the #1 car under it
           '.hp5 .v5-h{display:flex;flex-direction:column;align-items:center;padding-bottom:0}.hp5 .v5-h .v5-im{order:2;width:100%}'
           '.hp5 .v5-h .v5-im img{max-width:640px;margin-top:clamp(-56px,-4vw,-8px)}'
           '.hp5 .v5-h .v5-s{order:3;max-width:none;margin:0 auto;display:grid;justify-items:center}'
           '.hp5 .h5w-k{font-size:15px;font-weight:600;color:#6e6e73}'
           '.hp5 .h5w-n{margin-top:2px;font-size:22px;font-weight:700;letter-spacing:-.01em;color:#1d1d1f;text-decoration:none}.hp5 .h5w-n:hover{text-decoration:underline}'
           '.hp5 .h5w-st{display:flex;justify-content:center;gap:clamp(20px,6vw,44px);margin-top:14px}'
           '.hp5 .h5w-st>span{display:grid;justify-items:center}'
           '.hp5 .h5w-st b{font-size:clamp(26px,7.2vw,36px);font-weight:800;letter-spacing:-.025em;line-height:1.05;color:#1d1d1f;font-variant-numeric:tabular-nums}'
           '.hp5 .h5w-st small{margin-top:4px;font-size:13.5px;color:#6e6e73}'
           # cards: bigger car pictures
           '.hp5 .cbx-chd{grid-template-columns:auto 156px minmax(0,1fr);gap:14px}'
           '@media (max-width:600px){.hp5 .cbx-chd{grid-template-columns:auto 128px minmax(0,1fr);gap:10px}.hp5 .cbx-cn h3{font-size:17px}}'
           # option A: label + big number on one line, a thick scale bar, the list's two ends under it
           '.hp5 .cbx-ms{gap:18px;margin-top:14px;padding-top:16px}'
           '.hp5 .h5m{display:grid;gap:8px}'
           '.hp5 .h5m-t{display:flex;align-items:baseline;justify-content:space-between;gap:12px}'
           '.hp5 .h5m-l{display:grid;font-size:15px;font-weight:600;color:#1d1d1f;line-height:1.2}.hp5 .h5m-l small{font-size:12.5px;font-weight:500;color:#6e6e73}'
           '.hp5 .h5m-v{font-size:22px;font-weight:700;letter-spacing:-.015em;line-height:1.1;white-space:nowrap;font-variant-numeric:tabular-nums}'
           '.hp5 .h5m-v small{font-size:14px;font-weight:600;color:#6e6e73}'
           '.hp5 .h5m-b{position:relative;display:block;height:14px;border-radius:7px;background:#e3e3e8}'
           '.hp5 .h5m-b i{position:absolute;top:0;bottom:0;min-width:16px;border-radius:7px;background:#ffcc00;box-shadow:inset 0 0 0 1px rgba(0,0,0,.08)}'
           '.hp5 .h5m-b i.pw{width:16px;background:#1d1d1f;box-shadow:none}'
           '.hp5 .h5m-x{display:flex;justify-content:space-between;font-size:12px;line-height:1;color:#86868b}'
           # option B: two tiles, the number big, a thick bar under it (longer = pricier / more powerful, out of the list's top)
           '.hp5 .cbx-ms:has(.h5t){border-top:0;padding-top:0}'
           '.hp5 .h5t{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}'
           '.hp5 .h5t-c{display:grid;gap:6px;align-content:start;min-width:0;padding:12px 12px 14px;border-radius:16px;background:#fff}'
           '.hp5 .h5t-l{font-size:13.5px;font-weight:600;color:#6e6e73}'
           '.hp5 .h5t-v{font-size:clamp(19px,5.6vw,28px);font-weight:800;letter-spacing:-.03em;line-height:1.05;white-space:nowrap;font-variant-numeric:tabular-nums}'
           '.hp5 .h5t-v small{font-size:15px;font-weight:700;color:#6e6e73}'
           '.hp5 .h5t-b{position:relative;display:block;height:10px;margin-top:4px;border-radius:5px;background:#ececf0}'
           '.hp5 .h5t-b i{position:absolute;inset:0 auto 0 0;border-radius:5px;background:#ffcc00}.hp5 .h5t-b i.pw{background:#1d1d1f}'
           '.hp5 .h5t-s{font-size:12.5px;color:#6e6e73}.hp5 .h5t-x{display:flex;justify-content:space-between}'
           '.hp5 .hp5-near{margin:22px auto 0;max-width:760px;text-align:center;font-size:15px;line-height:1.5;color:#424245}'
           '.hp5 .hp5-note{text-align:center;max-width:560px;margin-left:auto;margin-right:auto;font-size:14px;line-height:1.5;color:#6e6e73}'
           '.hp5 .bph img[src*="/assets/engines/"]{object-fit:contain;object-position:50% 50%;mix-blend-mode:multiply}</style>')
    # 11-25 v3: hp5 is a class on the list's own div (no wrapper div: CBX5_HOOK's parser dropped the wrapper's end tag, which pulled the
    # end-of-page boxes inside it and off-center)
    body = (f'{css}<div class="advp cb cbx hp5">' + cbx_head('The cheapest 500 hp cars.', ans) + lst
            + cbx_faq([(q, f'<p>{E(a)}</p>') for q, a in faq]) + cbx_src(src) + '</div>')
    body += share_line(f'The cheapest 500 hp cars, ranked by estimated price. #1: the {nm(one)}. Free list:', 'Know someone who wants a fast car cheap?')
    ld = [faq_ld([(q, '', a) for q, a in faq]),
          {"@context": "https://schema.org", "@type": "ItemList", "name": "The 10 cheapest 500 hp cars", "itemListOrder": "https://schema.org/ItemListOrderAscending",
           "numberOfItems": len(L), "itemListElement": [{"@type": "ListItem", "position": i, "name": f'{e["span"]} {_h5_short(e)}', "url": BASE + e['href']} for i, e in enumerate(L, 1)]}]
    page(HP5_URL, '10 Cheapest 500 HP Cars You Can Buy (2026 Prices) | The Lemon Index', lede, body, ld=ld)
    SEO_URLS.append(HP5_URL)
    HP5_CARD = (HP5_URL, 'Cheapest 500 hp cars', next((e['img'] for e in L if e.get('img') and not e.get('img_eng')), None))
    globals()['HP5_TOP'] = L


HP5_CARD = None
try: _hp500_page()
except Exception as _h5x:
    import traceback; print('hp500 page failed', repr(_h5x)); traceback.print_exc()
