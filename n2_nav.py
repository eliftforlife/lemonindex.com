# 11-13 navigation fixes, model + year page wayfinding (UX test 11-13 navigation, agent N2). Run by build.py with exec(), so FY, RIVALS,
# CARU, scored, year_pool, ok_pick, gen_of, band, E ... are in scope. Classes n2-*; CSS/JS in assets/n2.css and assets/n2.js.
#  - year pages: "Better years to buy" under the gauge: the 3 years of this generation (or within 3 model years when we don't know the
#    generation) and the 3 of other generations with the fewest complaints per car sold, each better than this year, linked with its score.
#  - Every year tab (year + model pages): sort the list newest first or by fewest complaints.
N2_ASSET = '<link rel="stylesheet" href="/assets/n2.css?v=2"><script src="/assets/n2.js?v=2" defer></script>'

def _n2_chip(f, w):
    return (f'<a class="n2-c {band(w["li"])[0]}" href="{CARU(f, w["y"])}" aria-label="{w["y"]} {E(f["name"])}: Lemon Index {w["li"]}">'
            f'<b>{w["y"]}</b><span>{w["li"]}</span></a>')

def N2_BETTER(f, v, y):
    """'' or the strip. Only years the site would suggest (ok_pick: better than average, or for a model with no such year, at or under its own
    average), never a partial (2023+) score, and each with a lower Lemon Index than this year when this year is scored."""
    cur = v['li'] if v.get('ok') and not v.get('early') else None
    ok = [w for w in scored(f) if w['y'] != y and ok_pick(f, w) and (cur is None or w['li'] < cur)]
    by = lambda ws: sorted(ws, key=lambda w: (w['li'], -w['y']))[:3]
    g = gen_of(f, y)
    if g:
        near = by([w for w in ok if gen_of(f, w['y']) == g]); lab1, lab2 = 'This generation', 'Other generations'
        rest = by([w for w in ok if gen_of(f, w['y']) != g and w in year_pool(f)])
    else:
        near = by([w for w in ok if abs(w['y'] - y) <= 3]); lab1, lab2 = 'Nearby years', 'Any year'
        rest = by([w for w in ok if w not in near and w in year_pool(f)])
    rows = [(l, ws) for l, ws in ((lab1, near), (lab2, rest)) if ws]
    if not rows:
        if g and cur is not None and cur <= 110 and not any(w for w in scored(f) if w['y'] != y and gen_of(f, w['y']) == g and w['li'] < cur):
            return f'<div class="n2-by n2-by1"><p class="n2-by-h">Fewest complaints of its generation ({E(g)}).</p></div>'
        return ''
    return ('<div class="n2-by" role="group" aria-label="Better years to buy"><p class="n2-by-h">Better years to buy</p>'
            + ''.join(f'<div class="n2-by-r"><span class="n2-by-l">{l}</span><span class="n2-by-cs">{"".join(_n2_chip(f, w) for w in ws)}</span></div>' for l, ws in rows)
            + '</div>')

# the sort switch for the Every year list (hidden until n2.js runs; the list itself stays newest first in the HTML)
N2_SORT = ('<div class="n2-so" role="group" aria-label="Sort the years" hidden><button type="button" data-k="y" aria-pressed="true">Newest first</button>'
           '<button type="button" data-k="li" aria-pressed="false">Fewest complaints</button></div>')

# ---- one breadcrumb system (problem 7): All cars › Ford › F-150 › 2015 on model and year pages, and the same items in the JSON-LD
# BreadcrumbList (crumbs() in build.py calls N2_LD for /cars/<model>/ and /cars/<model>/<year>/; slash ids like mercedes-benz-m/gle work too).
def _n2_names(f):
    c = BYNAME.get(f['name']) or {}; b = c.get('brand') or f['name'].split(' ')[0]; nm = SNM(f)
    for p in (b, MAKER(f['name'])):
        if nm.startswith(p + ' '): return b, nm[len(p) + 1:]
    return b, nm
def N2_CRUMB(f, y=None):
    b, short = _n2_names(f); sep = '<span class="n2-cs" aria-hidden="true">›</span>'
    items = ['<a href="/cars/">All cars</a>', BRAND_A(b)]
    items.append(f'<a href="{CARU(f)}">{E(short)}</a>' if y else f'<span aria-current="page">{E(short)}</span>')
    if y: items.append(f'<span aria-current="page">{y}</span>')
    return f'<p class="ph-e n2-cr">{N2_ASSET}{sep.join(items)}</p>'
def N2_LD(path, items):
    m = re.match(r'^/cars/(.+?)/(?:(\d{4})/)?$', path); f = FY.get(m.group(1)) if m else None
    if not f: return items
    b, short = _n2_names(f); out = [items[0], ('All cars', BASE + '/cars/')]
    if b in _BRAND_PG: out.append((b, BASE + f'/brands/{b.lower().replace(" ", "-")}/'))
    out.append((f['name'], BASE + CARU(f)))
    if m.group(2): out.append((m.group(2), BASE + CARU(f, int(m.group(2)))))
    return out

# ---- rivals (problem 13): the cars a shopper actually weighs against this one. Same type (car / SUV / truck / minivan) and the same price
# class (luxury brand or not), searched match-ups first (data/kw_pairs.json volume), then the best-selling rivals (RIVALS), then the
# same-type cars closest in U.S. sales. Never a luxury car for a mainstream one or the other way round (Civic -> BMW 5 Series, CR-V -> Q3).
N2_LUX = {'Acura', 'Audi', 'BMW', 'Cadillac', 'Genesis', 'Infiniti', 'Jaguar', 'Land Rover', 'Lexus', 'Lincoln', 'Maserati', 'Mercedes-Benz', 'Porsche', 'Tesla', 'Volvo',
          'Alfa Romeo', 'Saab'}
_N2KW = {}
for _a, _b, _v, _ in (json.load(open('data/kw_pairs.json', encoding='utf-8')) if os.path.exists('data/kw_pairs.json') else []):
    _N2KW[(_a, _b)] = _N2KW[(_b, _a)] = _v
_N2RV = {}
def N2_RIVALS(fid):
    if fid in _N2RV: return _N2RV[fid]
    f = FY.get(fid); c = BYNAME.get(f['name']) if f else None
    if not c: _N2RV[fid] = []; return []
    lux = c['brand'] in N2_LUX
    def peer(o):
        g = FY.get(o); d = BYNAME.get(g['name']) if g else None
        return d is not None and o != fid and d['seg'] == c['seg'] and (d['brand'] in N2_LUX) == lux
    import math
    rv = [o for o in RIVALS.get(fid, []) if peer(o)]
    rv += [b for (a, b), _ in sorted(_N2KW.items(), key=lambda kv: -kv[1]) if a == fid and b not in rv and peer(b)]   # searched pairs under the 1,000 PAIRS cut (4Runner vs Pilot)
    rv.sort(key=lambda o: -_N2KW.get((fid, o), 0))   # stable: searched match-ups first, then RIVALS' sales order
    rest = sorted((g['id'] for g in YEARS if g['id'] not in rv and peer(g['id'])), key=lambda o: abs(math.log(max(1, BYNAME[FY[o]['name']]['sold']) / max(1, c['sold']))))
    _N2RV[fid] = rv + rest; return _N2RV[fid]

def N2_SIMILAR(f, y):
    """'Similar cars' line at the end of a year page's Overview: the same model year of up to 3 rivals, with their Lemon Index."""
    out = []
    for o in N2_RIVALS(f['id']):
        w = next((w for w in FY[o]['years'] if w['y'] == y), None)
        if not w: continue
        g = FY[o]; _, sh = _n2_names(g)
        sc = f' <b class="{CLS(w)}">{w["li"]}</b>' if w.get('ok') and not w.get('early') else ''
        out.append(f'<a href="{CARU(g, y)}">{y} {E(SNM(g))}{sc}</a>')
        if len(out) == 3: break
    if not out: return ''
    return (f'<section class="n2-sim" id="similar"><h2 class="n2-sim-h">Similar cars, same year</h2><p class="n2-sim-l">{"".join(out)}</p>'
            + ('<p class="n2-sim-n">Lemon Index: 100 = the average car, lower is better.</p>' if any('<b class' in o for o in out) else '') + '</section>')

# ---- model pages (problem 11): "#3 of the most reliable SUVs" badge linking to that list, when the model is on it (seo_pages.py lists the
# 15 best of each type with 150,000+ sold, by the model's Lemon Index)
_N2SEG = {'car': ('cars', 'car'), 'suv': ('suvs', 'SUV'), 'truck': ('trucks', 'truck'), 'minivan': ('minivans', 'minivan')}
def N2_RANK(f):
    c = BYNAME.get(f['name'])
    if not c or c.get('new') or c['seg'] not in _N2SEG: return ''
    L = sorted([d for d in CARS if d['seg'] == c['seg'] and d['sold'] >= 150000], key=lambda d: d['li'])[:15]
    i = next((k for k, d in enumerate(L, 1) if d['id'] == c['id']), None)
    if not i: return ''
    slug, nm = _N2SEG[c['seg']]
    return (f'<p class="n2-rk"><a href="/best/most-reliable-{slug}/" aria-label="Number {i} on our list of the most reliable {nm}s">#{i} most reliable {nm}'
            f' <span aria-hidden="true">›</span></a></p>')

# ---- phones (problem 8): All years and Compare as two visible pills under the hero (the More menu keeps Share and Advanced); wide screens
# already show the hero buttons
_N2I = {'all': '<path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/>', 'cmp': '<path d="M7 20V9M12 20V4M17 20v-7"/>'}
_n2svg = lambda k: f'<svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_N2I[k]}</svg>'
def N2_PILLS(f, y):
    return (f'<p class="n2-pl"><a href="{CARU(f)}">{_n2svg("all")}All {len(f["years"])} years</a>'
            f'<a href="/compare/?c={f["id"]}-{y}">{_n2svg("cmp")}Compare</a></p>')

# ---- model pages (problem 7): every model gets a Compare tab. Models without a match-up page (4Runner, Ranger, Mustang...) open the
# compare tool with their closest rivals (N2_RIVALS)
def N2_CMP(f):
    rv = N2_RIVALS(f['id'])[:4]
    if not rv: return ''
    me = mphoto(f['id'])
    cards = ''.join(f'<a class="mu" href="/compare/?cars={f["id"]},{o}"><span class="mu-p">{pimg(me, f["name"], "l")}{pimg(mphoto(o), FY[o]["name"], "r")}</span><b>vs {E(FY[o]["name"])}</b></a>'
                    for o in rv if me and mphoto(o))
    links = '' if cards else ' · '.join(f'<a href="/compare/?cars={f["id"]},{o}">vs {E(FY[o]["name"])}</a>' for o in rv) + '. '
    return (f'<section><h2>Compare the {E(f["name"])}.</h2>' + (f'<div class="mus">{cards}</div>' if cards else '')
            + f'<p class="yc-cap">{links}Opens the compare tool with both cars, every year side by side. <a href="/compare/?cars={f["id"]}">Compare with any car →</a></p></section>')
