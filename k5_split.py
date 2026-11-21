# 11-20 (Elijah: "Kia Optima vs K5: 2021+ model years are the Kia K5 but sit under /cars/kia-optima/. Split them"). Run by build.py with
# exec() right after its imports, before any data file is read. The data files key the car as 'kia-optima' for every model year (NHTSA files
# 2021+ complaints as "K5"; the study counted both as one family), so the split happens as each file is read:
#   - every per-year table under 'kia-optima' (year keys, year rows, [year, ...] rows, year lists) gives its 2021+ part to 'kia-k5';
#   - data/years.json's Optima record becomes two records (Kia Optima to 2020, Kia K5 from 2021);
#   - per-generation lists (YouTube) move their 2021+ generation; the 'K5 = duplicate of the Optima' plan card goes away;
#   - model-level numbers (score, complaints, sold) come from data/k5_split.json (tools/k5_split.py, the study's own method), see K5_CARS.
# Year pages that moved (/cars/kia-optima/2021/ ...) become redirect stubs to /cars/kia-k5/<year>/ (K5_REDIRECTS, end of the build).
K5_FROM, K5_OLD, K5_NEW = 2021, 'kia-optima', 'kia-k5'
_K5_SKIP = ('page_dates', 'opinions', 'thin_pages', 'gsc_seen', 'k5_split')
def _k5_yr(k):
    try: return int(str(k)[:4]) if re.fullmatch(r'\d{4}', str(k)) else None
    except Exception: return None
def _k5_rename(o):
    """Display names in moved records: 'Kia Optima' -> 'Kia K5' (slugs and image paths stay)."""
    if isinstance(o, str): return o.replace('Kia Optima', 'Kia K5')
    if isinstance(o, list): return [_k5_rename(x) for x in o]
    if isinstance(o, dict): return {k: (v if k in ('src', 'sid', 'id', 'url', 'page', 'odi') else _k5_rename(v)) for k, v in o.items()}
    return o
def _k5_cut(v):
    """(old part, new part) of one per-model value, or None when it isn't per year."""
    if isinstance(v, dict):
        ks = list(v)
        if ks and all(_k5_yr(k) for k in ks):
            return {k: x for k, x in v.items() if _k5_yr(k) < K5_FROM}, {k: _k5_rename(x) for k, x in v.items() if _k5_yr(k) >= K5_FROM}
        if ks and all(isinstance(x, (dict, list)) for x in v.values()):   # e.g. repair_costs {c: [year rows], t: {year: ...}, k: {year: ...}}
            old, new, hit = {}, {}, False
            for k, x in v.items():
                c = _k5_cut(x)
                if c is None: old[k] = x; continue
                hit = True; old[k], new[k] = c
            return (old, new if any(new.values()) else {}) if hit else None
        return None
    if isinstance(v, list) and v:
        if all(isinstance(x, int) and 1990 < x < 2100 for x in v):
            return [x for x in v if x < K5_FROM], [x for x in v if x >= K5_FROM]
        if all(isinstance(x, list) and x and isinstance(x[0], int) and 1990 < x[0] < 2100 for x in v):   # [year, ...] rows; [y0, y1, ...] generation rows
            return [x for x in v if x[0] < K5_FROM], [_k5_rename(x) for x in v if x[0] >= K5_FROM]
        if all(isinstance(x, dict) for x in v):
            def y0(x):
                if isinstance(x.get('years'), list) and x['years']: return min(x['years'])
                for k in ('y0', 'y', 'year'):
                    if isinstance(x.get(k), int): return x[k]
                return None
            if all(y0(x) is not None for x in v):
                return [x for x in v if y0(x) < K5_FROM], [_k5_rename(x) for x in v if y0(x) >= K5_FROM]
    return None
def K5_FIX(o, depth=0):
    """Split every 'kia-optima' entry inside a loaded data object (in place). Returns o."""
    if depth > 4: return o
    if isinstance(o, dict):
        if K5_NEW in o and isinstance(o[K5_NEW], dict) and o[K5_NEW].get('dupe_of') == K5_OLD: del o[K5_NEW]   # new_plan: the K5 card that opened the Optima
        if K5_OLD in o:
            v = o[K5_OLD]
            c = _k5_cut(v)
            if c is not None:
                old, new = c
                if new:
                    if K5_NEW not in o: o[K5_NEW] = new
                    elif isinstance(o[K5_NEW], dict) and isinstance(new, dict): o[K5_NEW] = {**new, **o[K5_NEW]}
                    o[K5_OLD] = old
            elif isinstance(v, list) and v and all(isinstance(x, str) for x in v) and K5_NEW not in o:
                o[K5_NEW] = list(v)   # sales sources: the K5's sales come from the same page
        for k, x in list(o.items()):
            if k not in (K5_OLD, K5_NEW) and isinstance(x, (dict, list)): K5_FIX(x, depth + 1)
    elif isinstance(o, list):
        i = 0
        while i < len(o):
            x = o[i]
            if isinstance(x, dict) and x.get('id') == K5_OLD:
                if isinstance(x.get('years'), list) and x['years'] and isinstance(x['years'][0], dict) and 'y' in x['years'][0]:   # years.json
                    new = [v for v in x['years'] if v['y'] >= K5_FROM]
                    if new:
                        x['years'] = [v for v in x['years'] if v['y'] < K5_FROM]
                        o.insert(i + 1, {**{k: v for k, v in x.items() if k != 'years'}, 'id': K5_NEW, 'name': 'Kia K5', 'years': new}); i += 1
                elif isinstance(x.get('y'), int) and x['y'] >= K5_FROM:   # one row per model year (gap.json cel_years)
                    x['id'] = K5_NEW; x['name'] = _k5_rename(x.get('name', ''))
            elif isinstance(x, (dict, list)) and depth < 3: K5_FIX(x, depth + 1)
            i += 1
    return o
_k5_json_load = json.load
def _k5_load(fp, *a, **k):
    o = _k5_json_load(fp, *a, **k)
    nm = str(getattr(fp, 'name', '')).replace('\\', '/')
    if '/data/' in '/' + nm and nm.endswith('.json') and not any(s in nm for s in _K5_SKIP): K5_FIX(o)
    if nm.endswith('ai_model_images.json'):   # the K5's own model illustration (already made for its 'No data yet' card)
        if isinstance(o, dict) and K5_OLD in o and K5_NEW not in o and os.path.exists('assets/ai-models/kia-k5.webp'):
            o[K5_NEW] = {**o[K5_OLD], 'src': '/assets/ai-models/kia-k5.webp?v=1', 'year': 2022, 'name': 'Kia K5', 'color': None}
    return o
json.load = _k5_load
K5S = (lambda p: _k5_json_load(open(p, encoding='utf-8')) if os.path.exists(p) else {})('data/k5_split.json')
def K5_CARS(cars, cars_new, segn):
    """The study's Kia Optima (2010-2022) becomes the Optima 2010-2020; the K5 (2021-2022) joins the added models (not the study's ranking)."""
    if not K5S: return
    o, n = K5S.get(K5_OLD), K5S.get(K5_NEW)
    for c in cars:
        if c['id'] == K5_OLD and o:
            c.update(years=o['years'], sold=o['sold'], n=o['n'], per100k=round(o['per100k']), avg=round(o['expected'] / o['sold'] * 1e5), li=o['li'],
                     serious=round(o['serious']), worst=o['worst'], issues=o['issues'])
    if n and not any(c['id'] == K5_NEW for c in cars + cars_new):
        cars_new.append(dict(id=K5_NEW, name='Kia K5', brand='Kia', seg='car', segName=segn.get('car', 'Car'), years=n['years'], sold=n['sold'], est=False,
                             n=n['n'], per100k=round(n['per100k']), avg=round(n['expected'] / n['sold'] * 1e5), li=n['li'], serious=round(n['serious']),
                             worst=n['worst'], issues=n['issues'], new=True, sales_url='https://en.wikipedia.org/wiki/Kia_Optima', sales_kind='calendar'))
# the line both model pages (and the year pages) carry, linking each to the other
def K5_NOTE(path):
    if path.startswith(f'/cars/{K5_OLD}/'):
        return '<p class="k5-note">The Optima was renamed the K5 for 2021. <a href="/cars/kia-k5/">Kia K5 (2021 on) &rarr;</a></p>'
    if path.startswith(f'/cars/{K5_NEW}/'):
        return '<p class="k5-note">The K5 is the renamed Optima (2021 on). <a href="/cars/kia-optima/">Kia Optima (to 2020) &rarr;</a></p>'
    return ''
def K5_REDIRECTS(out):
    """/cars/kia-optima/<2021+>/... (pages from before the split) -> the same page under /cars/kia-k5/ (meta refresh + canonical, noindex)."""
    base = f'{out}/cars/{K5_OLD}'; n = 0
    if not os.path.isdir(base): return 0
    for d in sorted(os.listdir(base)):
        if not (_k5_yr(d) and _k5_yr(d) >= K5_FROM): continue
        for root, _dirs, files in os.walk(f'{base}/{d}'):
            if 'index.html' not in files: continue
            rel = root[len(base):].replace('\\', '/').strip('/') + '/'
            tgt = f'/cars/{K5_NEW}/{rel}'
            if not os.path.exists(f'{out}{tgt}index.html'): tgt = f'/cars/{K5_NEW}/{d}/' if os.path.exists(f'{out}/cars/{K5_NEW}/{d}/index.html') else f'/cars/{K5_NEW}/'
            with open(f'{root}/index.html', 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><!--lx-alias--><html lang="en"><head><meta charset="utf-8"><title>Moved | The Lemon Index</title><meta name="robots" content="noindex">'
                         f'<link rel="canonical" href="https://lemonindex.com{tgt}"><meta http-equiv="refresh" content="0; url={tgt}"><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
                         f'<body style="font-family:system-ui,sans-serif;padding:24px"><p>The 2021 and later Optima is the Kia K5: this page is at <a href="{tgt}">lemonindex.com{tgt}</a>.</p></body></html>')
            n += 1
    return n
def K5_NOTE_INS(path, body):
    """Put K5_NOTE under the title: model page before the photo, year page before the score."""
    n = K5_NOTE(path)
    if not n or 'k5-note' in body or path.count('/') > 4: return body
    i = body.find('<div class="yct">')   # a year page: right after the title row (h1 between the prev / next arrows)
    j = body.find('</div>', i) if i > 0 else -1
    if j > 0: return body[:j + 6] + n + body[j + 6:]
    i = body.find('</h1>')   # the model page: right under the title
    return body[:i + 5] + n + body[i + 5:] if i > 0 else body
