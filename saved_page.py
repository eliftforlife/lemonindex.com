# /saved/ "My cars" (11-14, growth plan 4d): the cars a visitor saved with the Save buttons on model, year and VIN report pages.
# The list lives in the visitor's browser only (localStorage, assets/saved.js); this page is the empty shell saved.js fills from
# /assets/vr/<model id>.json (vin_report.py). A personal tool page: noindex, not in the sitemap.
# exec'd from build.py (uses page, phero).
_SVB = f'''<div class="pg">{phero('<a href="/">All cars</a> · My cars', 'My cars.', 'The cars you saved, with their score and top problem. Pick up to 4 to compare.',
    extra='<link rel="stylesheet" href="/assets/saved.css?v=2"><div id="lsvx" aria-live="polite"><p class="lsv-load">Loading your saved cars…</p>'
          '<noscript><p class="lsv-empty">My cars needs JavaScript: your saved cars are kept in this browser, not on our server.</p></noscript></div>'
          '<script src="/assets/saved.js?v=3" defer></script>')}</div>'''
page('/saved/', 'My Cars: Your Saved Cars | The Lemon Index', 'The cars you saved on the Lemon Index, with each model year’s score, verdict and top problem. Kept in your browser only.', _SVB)
_p = f'{OUT}/saved/index.html'
_s = open(_p, encoding='utf-8').read()
open(_p, 'w', encoding='utf-8').write(_s.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow"><link rel="canonical"', 1))

# 11-15 growth 4d follow-up: the pages with no Car JSON-LD and no /assets/vr/ file (performance and JDM cars, supercars, complaints-only
# models, EV-only /electric/<id>/ pages, motorcycles) -> docs/assets/saved-x.json, keyed by page address. saved.js reads it for the Save
# button on those pages and for their cards on /saved/. Only numbers the pages already show: compare.json (ux_c.py) for cars, data/moto*.json
# for bikes (the same counts vehicles_pages.py prints), the hero picture from the built page. Call after compare.json is written.
def SVX_WRITE():
    import glob as _g
    J = json.load(open(f'{OUT}/assets/compare.json', encoding='utf-8'))['cars']
    _ld = lambda p: json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
    def hero_img(u):
        p = f'{OUT}{u}index.html'
        if not os.path.exists(p): return None
        s = open(p, encoding='utf-8').read(); i = s.find('<section class="ph')
        if i < 0: return None
        m = re.search(r'<img\b[^>]*?\bsrc="(/assets/[^"]+)"', s[i:s.find('</section>', i)] if s.find('</section>', i) > 0 else s[i:i + 20000])
        return m.group(1) if m else None
    XM = {}
    for p in ('data/extra_models.json', 'data/extra_models_new.json'): XM.update(_ld(p) or {})
    EVR = {c['slug']: c for c in (EVX if 'EVX' in globals() else [])}
    NOWY_ = int(TODAY[:4]); out = {}
    def tp(parts):
        for k, v in parts or []:
            if k and 'unknown' not in k.lower(): return [k, v]
        return None
    for e in J:
        k, u, i = e['k'], e['u'], e['i']
        if k == 'car': continue
        if k == 'ev' and u.startswith('/cars/'):   # an EV with a full model page: its /electric/ page saves that model (the vr file has its numbers)
            if e.get('ev', {}).get('u'): out[e['ev']['u']] = {'m': i, 'n': e['n']}
            continue
        r = {'n': e['n'], 'k': k, 'c': i}
        im = hero_img(u) or e.get('im')
        if im: r['im'] = im
        if k == 'perf':
            if u.startswith('/jdm/'): r['k'] = 'jdm'
            gs = []
            for g in e['g']:
                ys = [int(x) for x in re.findall(r'(?:19|20)\d{2}', g.get('y') or '')]
                if not ys: continue
                y1 = ys[-1] if len(ys) > 1 else (NOWY_ if re.search(r'\d{4}\s*\W\s*$', g['y']) else ys[0])
                gs.append([g['id'], g.get('c'), g.get('y'), g.get('v'), g.get('hp'), g.get('z'), g.get('e'), g.get('nc'), g.get('rc'), ys[0], min(y1, NOWY_ + 1), g.get('zt') or ''])
            r['g'] = gs; r['d'] = e.get('d')
            nh = (_ld(f'data/perf/{i}.json') or {}).get('nhtsa') or {}
            if nh.get('make') and nh.get('models'): r['nm'] = [nh['make'], nh['models'][0]]
        elif k == 'sc':
            r['y'] = {y: [v[2], v[3], v[4], (e.get('eng') or {}).get(y) or None] for y, v in e['y'].items()}; r['d'] = e.get('d')
        elif k == 'co':
            r['y'] = {y: [v[1], v[2]] for y, v in e['y'].items()}; r['d'] = e.get('d')
            x = XM.get(i) or {}
            r['cn'] = sum(v[1] or 0 for v in e['y'].values())
            if x.get('recalls') is not None: r['rc'] = len(x['recalls'])
            t = tp(x.get('parts'))
            if t: r['tp'] = t
        elif k == 'ev':
            ev = e.get('ev') or {}; c = EVR.get(i) or {}
            r.update(li=ev.get('li'), w=ev.get('w'), rg=ev.get('r'))
            if c.get('per100k') is not None: r['p'] = c['per100k']
            if c.get('recalls') is not None: r['rc'] = len(c['recalls'])
            d = e['y'].get(str(e.get('d'))) or []
            if len(d) > 6 and d[6]: r['tp'] = [d[6], None]
        out[u] = r
    MAV_ = _ld('data/moto_avoid.json') or {}
    for m in (_ld('data/moto.json') or []):
        slug = slugify(m['name']); u = f'/motorcycles/{slug}/'
        if not os.path.exists(f'{OUT}{u}index.html'): continue
        out[u] = {'n': m['name'], 'k': 'moto', 'im': hero_img(u), 'cn': m['n'], 'rc': len(m['recalls']), 'tp': tp(m.get('parts')), 's': m['serious'], 'yr': f'{m["years"][0]}–{m["years"][1]}'}
    for b in (_ld('data/moto_bikes.json') or []):
        u = f'/motorcycles/{b["slug"]}/'
        if not os.path.exists(f'{OUT}{u}index.html'): continue
        by = dict(b['by_year'])
        if b['slug'] in MAV_:   # the same counts the bike page prints (vehicles_pages.py)
            for y, v in MAV_[b['slug']]['chart']: by[str(y)] = v
            by = {y: v for y, v in by.items() if v}
        out[u] = {'n': b['name'], 'k': 'moto', 'im': hero_img(u), 'cn': sum(by.values()), 'rc': len(b['recalls']), 'tp': tp(b.get('parts')), 's': b['serious'], 'yr': f'{min(int(y) for y in by)}–{max(int(y) for y in by)}'}
    for r in out.values():
        if not r.get('im'): r.pop('im', None)
        if r.get('tp') is None: r.pop('tp', None)
    json.dump({'v': 1, 'p': out}, open(f'{OUT}/assets/saved-x.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('saved-x.json:', len(out), 'pages,', ', '.join(f'{kk} {sum(1 for r in out.values() if r.get("k", "ev-model") == kk)}' for kk in ('perf', 'jdm', 'sc', 'co', 'ev', 'moto', 'ev-model')))
