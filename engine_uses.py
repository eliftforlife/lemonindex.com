# 11-13 navigation fix N3 (UX test 11-13 navigation, report problems 3 and 4): car pages and engine pages link each other, and the
# performance / supercar / electric pages link their regular model and back. exec'd by build.py after the hooks of ux_c.py and hd_pages.py.
#
# ENGINE_USES[engine page url][/cars/ model id] = {years, vers (the versions that have it), src}: which everyday car pages an engine that has
# its own page was sold in. Built ONLY from data the site already has; nothing is guessed (a car without data for an engine is left out):
#   - data/supercar_engines.json (EPA version names per model year, matched to the engine by data_supercar_engines.py), via EU_PARENT
#   - data/hd.json (data_hd.py: each owner complaint's VIN decoded by NHTSA vPIC): the F-150's 2.7 / 3.5 EcoBoost and 5.0 Coyote by year
#   - data/bmw_specs.json (EPA versions with their BMW engine codes)
#   - data/perf/<slug>.json (the performance pages' engines per generation, each with its page)
#   - data/engines_<model id>.json (the Civic's own engine list: anchors on its model page)
#   - data/engine_uses_tsb.json (data_engine_uses.py: the automaker's repair notes to dealers naming the code, 2+ bulletins per model year)
# CAR_ENG is the same map turned around, for the "Engines in this car" row on model and year pages (PIN_HTML, top of the page).
# CSS: assets/n3nav.css (prefix n3-), linked from the rows themselves so no shared stylesheet version changes.
import os as _euos, json as _euj, re as _eure, glob as _eug
if ENGU == 'hooks':
    import perf_page as _EUPP
    EU_CSS = '<link rel="stylesheet" href="/assets/n3nav.css?v=3">'
    EU_MODELS = {f['id']: f for f in YEARS}
    EU_YRS = {f['id']: {v['y'] for v in f['years']} for f in YEARS}
    _EU_BYNAME = sorted(((f['name'], f['id']) for f in YEARS), key=lambda t: -len(t[0]))
    def _eu_by_name(nm):
        """the /cars/ model whose name starts this car's name at a word or hyphen break ("Ford Mustang GT" -> Ford Mustang)"""
        for n, i in _EU_BYNAME:
            if nm == n or (nm.startswith(n) and nm[len(n)] in ' -'): return i
        return None
    # engine-data car slugs whose /cars/ model the name alone can't find (the model line they belong to, by name), and ones it finds wrongly
    EU_CAR_PARENT = {'ford-f-150-raptor': 'ford-f-series', 'ford-f-150-raptor-r': 'ford-f-series', 'ford-f-150-svt-lightning': 'ford-f-series',
                     'ford-shelby-gt350': 'ford-mustang', 'ford-shelby-gt500': 'ford-mustang', 'ram-1500-trx': 'ram-pickup', 'dodge-ram-srt-10': 'ram-pickup',
                     'mercedes-amg-c63': 'mercedes-benz-c-class', 'mercedes-amg-e63': 'mercedes-benz-e-class', 'mercedes-amg-e55': 'mercedes-benz-e-class',
                     'mercedes-amg-glc63': 'mercedes-benz-glk/glc', 'mercedes-amg-ml63': 'mercedes-benz-m/gle', 'mercedes-amg-ml63-gle63': 'mercedes-benz-m/gle',
                     'mercedes-amg-gle63': 'mercedes-benz-m/gle', 'mazdaspeed3': 'mazda3', 'mazdaspeed6': 'mazda6', 'toyota-gr-corolla': 'toyota-corolla',
                     'chrysler-300c-srt8': 'chrysler-300', 'bmw-m3-e9x': 'bmw-3-series', 'bmw-m5-e39': 'bmw-5-series', 'bmw-m5-e60': 'bmw-5-series', 'bmw-m5-g90': 'bmw-5-series'}
    EU_NOT = {'subaru-wrx-sti', 'ford-mustang-mach-e'}   # the WRX STI isn't on the Impreza's pages after 2014; the Mach-E is a different car
    def EU_PARENT(slug, name='', perf=''):
        if slug in EU_NOT: return None
        p = EU_CAR_PARENT.get(slug) or (_EUPP.PARENTS.get(perf) if perf else None) or _eu_by_name(name)
        return p if p in EU_MODELS else None
    _EU_SC = _load('data/supercar_engines.json') if _euos.path.exists('data/supercar_engines.json') else {'engines': {}}
    _EU_SLUG = {'rr-n73': 'rolls-royce-n73', 'rr-n74': 'rolls-royce-n74'}   # = supercar_engine_pages.SCE_SLUG
    _EU_MK = _eure.compile(r'^(GM|Ford|Toyota|Lexus|Mercedes-AMG|Mercedes|Chevrolet|Cadillac|Dodge|Hyundai|Nissan|Acura|Honda|Mitsubishi|Mazda|Subaru|BMW|Audi|Jaguar|Alfa Romeo|VW Group|VW|Porsche) ')
    ENGINE_USES, EU_NAME = {}, {}
    def _eu_add(url, fid, years, ver, src, name):
        if fid not in EU_MODELS: return
        ys = {int(y) for y in years} & EU_YRS[fid]
        if not ys: return
        u = ENGINE_USES.setdefault(url, {}).setdefault(fid, {'years': set(), 'vers': {}, 'src': set()})
        u['years'] |= ys; u['src'].add(src)
        if ver: u['vers'].setdefault(ver, set()).update(ys)
        EU_NAME.setdefault(url, name)
    # 1. the F-150's engines, decoded from the VIN of each owner complaint (first: its names win over the Ford GT's "3.5 EcoBoost (D35)")
    for _y, _v in (((HDT.get('ford-f-150') or {}).get('years') or {}) if 'HDT' in globals() else {}).items():
        for _k, _lab, _fu, _n, _pc in _v.get('eng') or []:
            if _k and _k in HE_URLS and _n >= 3: _eu_add(HE_URLS[_k], 'ford-f-series', [_y], 'F-150', 'vin', HDE[_k]['short'] if _k in HDE else _lab)
    # 2. supercar + performance engine data (EPA versions per model year)
    for _e, _d in _EU_SC['engines'].items():
        _url = f'/engines/{_EU_SLUG.get(_e, _e)}/'; _nm = _EU_MK.sub('', _d['name'])
        for _c in _d['cars']:
            _fid = EU_PARENT(_c['slug'], _c['name'], _c.get('perf') or '')
            if not _fid: continue
            _ys = [y for y, v in _d['years'].items() if _c['slug'] in v['cars']]
            _eu_add(_url, _fid, _ys, _c['name'], 'epa', _nm)
    # 3. BMW: EPA versions with their engine code
    for _fid, _yrs in ((BVER if 'BVER' in globals() else {}) or {}).items():
        for _y, _vl in _yrs.items():
            for _v in _vl:
                if _v.get('code') and _v['code'] in BEY: _eu_add(ENG_URL(_v['code']), _fid, [_y], _v.get('model', ''), 'epa', f'BMW {_v["code"]}')
    # 4. the performance pages' own engines (data/perf/<slug>.json: each generation names its engine, and the engine its page)
    EU_PERF = {}   # perf slug -> its data (pages that exist or get built: standalone ones and the injected M3)
    for _p in sorted(_eug.glob('data/perf/*.json')):
        if _p.endswith('.auto.json'): continue
        _D = _load(_p); EU_PERF[_D['slug']] = _D; _fid = _EUPP.parent_of(_D)
        if _fid not in EU_MODELS: continue
        for _g in _D.get('gens') or []:
            _en = (_D.get('engines') or {}).get(_g.get('engine')) or {}
            if _en.get('page', '').startswith('/engines/'): _eu_add(_en['page'], _fid, range(_g['y0'], _g['y1'] + 1), _D['name'], 'epa', _EU_MK.sub('', _eure.sub(r'\s*\(.*?\)', '', _en.get('name') or _g['engine'])))
    # 5. a model's own engine list (the Civic): anchors on its model page's engine chart (tabbed.py gives each engine an id)
    for _p in sorted(_eug.glob('data/engines_*.json')):
        _fid = _euos.path.basename(_p)[8:-5]
        for _g in _euj.load(open(_p, encoding='utf-8')):
            _eu_add(f'/cars/{_fid}/#eng-{_g["id"]}', _fid, _g.get('years') or [], '', 'list', f'{_g["name"]} ({_g["code"]})')
    # 6. the automaker's repair notes that name the engine code (data_engine_uses.py)
    for _fid, _es in ((_load('data/engine_uses_tsb.json') if _euos.path.exists('data/engine_uses_tsb.json') else {}).get('cars') or {}).items():
        for _e, _t in _es.items():
            _d = _EU_SC['engines'].get(_e)
            if _d: _eu_add(f'/engines/{_EU_SLUG.get(_e, _e)}/', _fid, _t['years'], _t['code'], 'tsb', _EU_MK.sub('', _d['name']))
    CAR_ENG = {}
    for _url, _cs in ENGINE_USES.items():
        for _fid, _u in _cs.items(): CAR_ENG.setdefault(_fid, {})[_url] = _u
    _eu_span = lambda ys: (f'{min(ys)}–{str(max(ys))[-2:]}' if max(ys) // 100 == min(ys) // 100 else f'{min(ys)}–{max(ys)}') if len(ys) > 1 else str(min(ys))
    _EU_SRC = {'epa': 'EPA version lists', 'vin': 'NHTSA VIN decoding of owner complaints', 'tsb': 'the automaker&#39;s repair notes to dealers (NHTSA)', 'list': 'EPA and the engine makers&#39; specs'}
    def _eu_vers(u, y=None): return [v for v, ys in u['vers'].items() if v and (y is None or y in ys)]
    def EU_ROW(fid, y=None):
        """'Engines in this car': every engine with a page that this model (this model year) was sold with, newest first"""
        es = CAR_ENG.get(fid) or {}
        rows = [(url, u) for url, u in es.items() if y is None or y in u['years']]
        if not rows: return ''
        mnm = EU_MODELS[fid]['name']; mk = mnm.split(' ')[0]
        rows.sort(key=lambda r: (-max(r[1]['years']), EU_NAME[r[0]]))
        more = len(rows) - 8 if y is None and len(rows) > 9 else 0
        if more: rows = rows[:8]
        def chip(url, u):
            vs = _eu_vers(u, y); vs = [v.replace(mk + ' ', '', 1) if v.startswith(mk + ' ') else v for v in vs]
            vs = [v for v in vs if v and v != mnm.replace(mk + ' ', '', 1)]
            sub = ', '.join(vs[:2]) + (' …' if len(vs) > 2 else '')
            sub = ' · '.join(x for x in (sub, _eu_span(u['years']) if y is None else '') if x)
            return f'<a class="n3-c" href="{E(url)}"><b>{E(EU_NAME[url])}</b>' + (f'<small>{E(sub)}</small>' if sub else '') + '</a>'
        srcs = sorted({s for _, u in rows for s in u['src']})
        js = '<script src="/assets/n3nav.js?v=2" defer></script>' if any('#eng-' in url for url, _ in rows) else ''
        return (f'<nav class="n3-row" aria-label="Engines in this car">{EU_CSS}{js}<p class="n3-h">{f"Engines in the {y} {E(mnm.split(' ', 1)[-1])}" if y else "Engines in this car"}</p><div class="n3-cs">'
                + ''.join(chip(url, u) for url, u in rows) + (f'<a class="n3-c n3-more" href="/engines/"><b>+{more} more</b><small>every engine</small></a>' if more else '') + '</div>'
                + f'<p class="n3-n">Engines with a page of their own, in the versions named, from {" and ".join(_EU_SRC[s] for s in srcs)}. Other versions can have other engines.</p></nav>')
    # ---- report problem 4: performance, supercar and electric pages <-> their regular model (two-way chips)
    EU_KIDS = {}   # /cars/ model id -> [(label, url, years or None, kind)]
    for _s, _D in EU_PERF.items():
        _fid = _EUPP.parent_of(_D)
        if _fid in EU_MODELS and _D.get('page') and _D['page'] != f'/cars/{_fid}/':
            EU_KIDS.setdefault(_fid, []).append((_D['name'].split(' ', 1)[-1], _D['page'], {y for g in _D.get('gens') or [] for y in range(g['y0'], g['y1'] + 1)}, 'perf'))
    EU_SC_PARENT = {}
    for _c in SCX:
        _fid = EU_PARENT(_slg(_c['name']), _c['name'])
        if _fid: EU_SC_PARENT[_slg(_c['name'])] = _fid; EU_KIDS.setdefault(_fid, []).append((_c['name'].split(' ', 1)[-1], f'/supercars/{_slg(_c["name"])}/', {y['y'] for y in _c['years']}, 'sc'))
    EU_EV_PARENT = {}
    for _c in EVX:
        _fid = None if _c['slug'] in EU_MODELS else EU_PARENT(_c['slug'], _c['name'])
        if _c['slug'] == 'ford-f-150-lightning': _fid = 'ford-f-series'   # the F-150's VIN decode lists the Lightning (data/hd.json)
        if _fid in EU_MODELS: EU_EV_PARENT[_c['slug']] = _fid; EU_KIDS.setdefault(_fid, []).append((_c['name'].split(' ', 1)[-1], f'/electric/{_c["slug"]}/', set(_evyears(_c)), 'ev'))
    _EU_KL = {'perf': 'Performance', 'sc': 'Supercar', 'ev': 'Electric'}
    def EU_KIDS_ROW(fid, y=None):
        ks = [k for k in EU_KIDS.get(fid) or [] if y is None or not k[2] or y in k[2]]
        if not ks: return ''
        ks.sort(key=lambda k: (('perf', 'sc', 'ev').index(k[3]), min(k[2] or {0}), k[0]))
        return (f'<nav class="n3-row n3-kids" aria-label="Other versions of this car">{EU_CSS}<p class="n3-h">{"Other " + str(y) + " versions" if y else "Other versions"}</p><div class="n3-cs">'
                + ''.join(f'<a class="n3-c" href="{E(u)}"><b>{E(lab)}</b><small>{_EU_KL[kd]}{" · " + _eu_span(ys) if y is None and ys else ""}</small></a>' for lab, u, ys, kd in ks) + '</div></nav>')
    def EU_PARENT_ROW(fid, here, ys=None, sibs=()):
        """on a performance / supercar / electric page: its regular model (+ the year pages it shares) and its sibling versions"""
        f = EU_MODELS.get(fid)
        if not f: return ''
        yl = sorted(set(ys or ()) & EU_YRS[fid])
        yc = ''.join(f'<a class="n3-y" href="{CARU(f, y)}">{y}</a>' for y in yl[-12:])
        sib = [k for k in EU_KIDS.get(fid) or [] if k[1] != here]
        return (f'<nav class="n3-row n3-par" aria-label="Regular model">{EU_CSS}<p class="n3-h">Regular model</p><div class="n3-cs"><a class="n3-c" href="{CARU(f)}"><b>{E(f["name"])}</b><small>every year, Lemon Index</small></a>'
                + ''.join(f'<a class="n3-c" href="{E(u)}"><b>{E(lab)}</b><small>{_EU_KL[kd]}</small></a>' for lab, u, _ys, kd in sib[:4]) + '</div>'
                + (f'<p class="n3-n">Year pages: <span class="n3-ys">{yc}</span></p>' if yc else '') + '</nav>')
    def _eu_perf_row(slug, D):   # perf_page.standalone() calls this in its hero
        fid = _EUPP.parent_of(D)
        return EU_PARENT_ROW(fid, D.get('page', ''), {y for g in D.get('gens') or [] for y in range(g['y0'], g['y1'] + 1)}) if fid in EU_MODELS else ''
    _EUPP.PARENT_ROW = _eu_perf_row
    def EU_SC_ROW(slug):
        """on a supercar page: its regular model when it has one (Corvette Z06 -> Corvette), and the compare tool with it filled in"""
        c = next((c for c in SCX if _slg(c['name']) == slug), None)
        par = EU_PARENT_ROW(EU_SC_PARENT[slug], f'/supercars/{slug}/', {y['y'] for y in c['years']}) if c and slug in EU_SC_PARENT else ''
        return par + f'<p class="n3-row n3-cmp">{EU_CSS}<a class="btn btn-ghost" href="/compare/?c=sc-{slug}">Compare it with another car</a></p>'
    _EU_PIN0 = PIN_HTML
    def PIN_HTML(fid, y=None):
        out = _EU_PIN0(fid, y)
        if fid in EU_MODELS: return out + EU_ROW(fid, y) + EU_KIDS_ROW(fid, y)
        if fid in EU_EV_PARENT:   # an electric page whose gas twin has its own model page
            c = next((c for c in EVX if c['slug'] == fid), None)
            return out + EU_PARENT_ROW(EU_EV_PARENT[fid], f'/electric/{fid}/', _evyears(c) if c else ())
        return out
    # ---- for the engine pages (built later): mainstream cars first, linked, with their year pages
    def EU_CARS(url):
        """[(model id, name, years, versions)] for an engine page, biggest-selling lines first (most model years)"""
        return sorted(((fid, EU_MODELS[fid]['name'], sorted(u['years']), sorted(u['vers'])) for fid, u in (ENGINE_USES.get(url) or {}).items()), key=lambda r: (-len(r[2]), r[1]))
    def EU_CARS_HTML(url, title='Everyday cars with this engine'):
        rs = [r for r in EU_CARS(url) if '#' not in url]
        if not rs: return ''
        srcs = sorted({s for u in ENGINE_USES[url].values() for s in u['src']})
        li = ''.join(f'<li><a class="n3-m" href="{CARU(EU_MODELS[fid])}">{E(nm)}</a>' + (f' <small>{E(", ".join(v.replace(nm + " ", "") for v in vs[:3]))}</small>' if vs and vs != [nm] else '')
                     + '<span class="n3-ys">' + ''.join(f'<a class="n3-y" href="{CARU(EU_MODELS[fid], y)}">{y}</a>' for y in ys) + '</span></li>' for fid, nm, ys, vs in rs)
        return (f'<section class="yc n3-eng">{EU_CSS}<h2>{E(title)} <span class="h2s">Tap a year for that car&#39;s full report.</span></h2><ul class="n3-ml">{li}</ul>'
                f'<p class="yc-cap">Model years from {" and ".join(_EU_SRC[s] for s in srcs)}. Only years we have a car page for.</p></section>')
    def EU_YEAR_URL(slug, name, perf, y):
        """a supercar/performance engine page's year row: the regular model's year page for this car and year, if there is one"""
        fid = EU_PARENT(slug, name, perf)
        return CARU(EU_MODELS[fid], int(y)) if fid and int(y) in EU_YRS[fid] else ''
    print('engine uses:', len(ENGINE_USES), 'engine pages x', len(CAR_ENG), 'car models |', sum(len(v) for v in EU_KIDS.values()), 'version links')
