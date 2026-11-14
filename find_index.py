# 11-11 (Elijah: "M3" found nothing though /cars/bmw-m3/ is a full page): ONE search index for every car the site has, built at the end of
# the build from the same lists that make the pages and cards, so it can't drift. Run by build.py with exec() (all page lists in scope).
#   docs/assets/find.json = [[name, brand, url, kind, [years], aliases, soon], ...]
#     kind: '' scored car | co complaints only | sc supercar | ev electric | perf performance | moto motorcycle | nd no data yet
#     soon: 1 = a coming-soon / no-data card (no page yet): shown in search, grayed out, sorted last, not a link
# Build guard: every model page folder under docs/cars, supercars, electric and motorcycles, and every card link on the home grid, must be
# in the index, or the build stops (and says what's missing).
import glob as _glob
FIND, _seen = [], {}
def _fadd(name, brand, url, kind='', years=(), alias='', soon=0, pri=0):
    key = url or ('soon:' + name.lower())
    if key in _seen:   # same page from two lists: merge the aliases
        r = FIND[_seen[key]]; r[5] = ' '.join(dict.fromkeys((r[5] + ' ' + alias).split())); return
    _seen[key] = len(FIND); FIND.append([name, brand, url, kind, sorted(set(int(y) for y in years)), alias.strip(), soon] + ([pri] if pri else []))   # 8th: search priority (hd_pages.py)
_brand_of = lambda nm, mk=None: mk or (BYNAME.get(nm, {}).get('brand') if nm in BYNAME else nm.split(' ')[0])
# common names people type that aren't in the model name (11-11, Elijah's list); generation codes and engines come from data/perf/*.json
FIND_ALIAS = {'/cars/bmw-m3/': 'competition comp cs', 'ford-shelby-gt500': 'shelby gt500 mustang', 'shelby-gt500': 'shelby gt500 mustang',
              'civic-type-r': 'type r typer', '/cars/ford-f-series/': 'f150 f 150', '/cars/ram-pickup/': '1500',
              '/cars/chevrolet-silverado/': '1500', '/cars/gmc-sierra/': '1500',
              # 11-12 round 2 (Devin): trim names people type -> the model page that covers them (the M340i/340i have their own page)
              '/cars/bmw-3-series/': '330i 330e 328i 328d 335i 320i 325i 330xi 3er',
              '/cars/bmw-2-series/': 'm240i 240i m240 230i 228i m235i 2er'}
# 11-12 round 2 (Mitch: "cummins", "duramax", "lml", "2500hd" offered a RAV4; "f250" went to the half-ton F-150 page): heavy-duty truck and
# diesel words belong to the heavy-duty pages, not the half-ton ones (their 2500/3500 aliases are gone above). Matched on the NAME, so they
# move to the real HD pages when those are built (fix C); until then the coming-soon cards take them, and search opens their vote sheet.
HD_ALIAS = [(r'\bram\b.*(2500|3500|heavy duty|\bhd\b)', 'cummins 2500 3500 2500hd 3500hd hd heavy duty diesel'),
            (r'super ?duty|\bf-?[234]50\b', 'powerstroke f250 f350 f450 2500 3500 super duty superduty hd heavy duty diesel'),
            (r'silverado.*(2500|3500|heavy duty|\bhd\b)', 'duramax lb7 lly lbz lmm lml l5p 2500hd 3500hd 2500 3500 hd heavy duty diesel'),
            (r'sierra.*(2500|3500|heavy duty|\bhd\b)', '2500hd 3500hd 2500 3500 hd heavy duty diesel')]   # the Duramax words open the Silverado HD (Mitch's list)
# ... and where no page or card exists yet, a coming-soon card of its own (name, brand, kind, aliases, the name pattern that means it exists)
SOON_EXTRA = [('Chevrolet Silverado HD (2500/3500)', 'Chevrolet', 'nd', '', r'silverado.*(2500|3500|heavy duty|\bhd\b)'),
              ('GMC Sierra HD (2500/3500)', 'GMC', 'nd', '', r'sierra.*(2500|3500|heavy duty|\bhd\b)'),
              ('Subaru WRX', 'Subaru', 'perf', 'wrx va vb fa20dit fa24 fa24dit', r'^subaru wrx(?!.*\bsti\b)')]   # Devin: the current WRX (fix D built its page: then this isn't added)
# 1. scored models (study + new), every year with a page
for f in YEARS: _fadd(f['name'], _brand_of(f['name']), f'/cars/{f["id"]}/', '', [v['y'] for v in f['years']], FIND_ALIAS.get(f'/cars/{f["id"]}/', ''))
PERF_LIVE = {}   # perf slug -> its live page (a card for the same car then links there instead of saying coming soon)
# 2a. performance pages first (their kind wins when the same page is also a BMW model page) (data/perf/<slug>.json): generation codes and engine codes are what enthusiasts type ("G80", "S58")
for pf in _glob.glob('data/perf/*.json'):
    if pf.endswith('.auto.json'): continue
    d = json.load(open(pf, encoding='utf-8')); u = d.get('page') or f'/cars/{d["slug"]}/'
    if not os.path.exists(f'{OUT}{u}index.html'): continue
    PERF_LIVE[d['slug']] = u
    al = ' '.join([g.get('code', '') for g in d.get('gens', [])] + list((d.get('engines') or {}).keys()) + [FIND_ALIAS.get(u, '')] + (['jdm fast furious'] if d.get('jdm') or d.get('films') else []))   # 11-13 JDM film cars
    _fadd(d['name'], d.get('make') or _brand_of(d['name']), u, 'perf', [y for g in d.get('gens', []) for y in range(g['y0'], g['y1'] + 1)], al)
# 2. complaints-only models (new ones, Pontiac, Taos...) and the BMW-only model pages
_XM = _load('data/extra_models.json'); _XM.update(_load('data/extra_models_new.json'))   # the same lists extra_pages.py builds from
for m in _XM.values():
    if os.path.exists(f'{OUT}/cars/{m["id"]}/index.html'): _fadd(m['name'], m.get('brand') or _brand_of(m['name']), f'/cars/{m["id"]}/', 'co', range(int(m['a']), int(m['b']) + 1) if m.get('a') else ())
for fid, m in (_load('data/bmw_specs.json').get('new_models') or {}).items():   # bmw_pages.py's BNEW
    if os.path.exists(f'{OUT}/cars/{fid}/index.html'): _fadd(m['name'], 'BMW', f'/cars/{fid}/', 'co', range(int(m['a']), int(m['b']) + 1) if m.get('a') else (), FIND_ALIAS.get(f'/cars/{fid}/', ''))
# 4. duplicates: the card's own name opens the model it's counted with (Dodge Caravan -> Grand Caravan)
for slug, tgt in _DUP.items():
    if tgt in _ID and slug in _PLAN: _fadd(_PLAN[slug]['name'], _PLAN[slug]['brand'], f'/cars/{tgt}/', '', [], '')
# 5. supercars and EVs
for c in SCX: _fadd(c['name'], c['make'], f'/supercars/{_slg(c["name"])}/', 'sc', [y['y'] for y in c['years']])
for c in EVX: _fadd(c['name'], _brandof(c['make']), f'/electric/{c["slug"]}/', 'ev', _evyears(c), 'ev electric')
# 6. motorcycles: pages, then the coming-soon bikes
for m in (globals().get('MO') or []): _fadd(m['name'], m['name'].split(' ')[0], f'/motorcycles/{slugify(m["name"])}/', 'moto', range(m['years'][0], m['years'][1] + 1) if m.get('years') else (), 'motorcycle bike')
# 7. coming soon: performance cars, supercars/hypercars still to come, bikes, and the "No data yet" models (shown grayed out, never a link)
for c in PERFX:
    i = perf_info(c); g = c.get('group', 'A'); u = i['url'] or PERF_LIVE.get(i['id'], '')
    _fadd(i['name'], i['brand'], u, 'perf' if g == 'A' else 'sc', [], ' '.join(filter(None, [FIND_ALIAS.get(i['id'], ''), c.get('search', '')])), 0 if u else 1)
for s in (globals().get('MS') or []): _fadd(s['name'], s['make'], '', 'moto', [], 'motorcycle bike ' + (s.get('search') or ''), 1)
for m in NEWM:
    if m['slug'] not in _DUP and m['slug'] not in _EXN: _fadd(m['name'], m['make'], '', 'nd', [], '', 1)
for r in (globals().get('HD_FIND') or []): _fadd(*r)   # 11-12 round 2: HD truck pages (hd_pages.py)
for r in (globals().get('AE_FIND') or []): _fadd(*r)   # 11-12 engines (all_engines.py): live engine pages + coming-soon engines
for r in (globals().get('UXC_FIND') or []): _fadd(*r)   # 11-12 UX test: the performance side-by-side pages (ux_c.py), e.g. "m3 vs c63"
# 11-13 navigation test (N1, problem 5: "chevy" opened the HHR, "ford" the Edge, "toyota" the RAV4): every brand page is a search result
# of its own, ranked above that brand's models (lookup.js kind 'br'); the name is the page's H1, so new brand pages join by themselves
for _bp in sorted(_glob.glob(f'{OUT}/brands/*/index.html')):
    _bt = open(_bp, encoding='utf-8').read()
    if _bt.startswith('<!doctype html><!--lx-alias'): continue   # a redirect stub (alias_pages.py: /brands/chevy/), not a brand page
    _bs = _bp.replace('\\', '/').split('/')[-2]; _bh = re.search(r'<h1[^>]*>(.*?)</h1>', _bt, re.S)
    _bn = html.unescape(re.sub(r'<[^>]+>', '', _bh.group(1))).strip() if _bh else ''
    _bm = re.match(r'(?i)' + r'[\s-]+'.join(map(re.escape, _bs.split('-'))) + r'(?![a-z0-9])', _bn)   # the brand at the start of the H1 ("Pontiac problems ..." -> Pontiac)
    _bn = _bm.group(0) if _bm else _bs.replace('-', ' ').title()
    _fadd(_bn, _bn, f'/brands/{_bs}/', 'br', [], 'brand make ' + _bs.replace('-', ' '))
for _nm, _br, _k, _al, _rx in SOON_EXTRA:
    if not any(re.search(_rx, r[0], re.I) and r[3] != 'eng' for r in FIND): _fadd(_nm, _br, '', _k, [], _al, 1)
for _r in FIND:
    if _r[3] == 'eng': continue
    for _rx, _al in HD_ALIAS:
        if re.search(_rx, _r[0], re.I): _r[5] = ' '.join(dict.fromkeys((_r[5] + ' ' + _al).split()))
# 11-13 navigation re-review (NQ, problem 4: "chevy" never showed the Silverado, "ford" never the F-150): a 9th field = the model's U.S. sales
# rank (CARS + CARS_NEW 'sold', 1 = most sold), so equally good matches list best sellers first (lookup.js); the 8th (priority) becomes 0 if unset
_SR = {f'/cars/{c["id"]}/': i for i, c in enumerate(sorted((c for c in CARS + CARS_NEW if c.get('sold')), key=lambda c: -c['sold']), 1)}
for _r in FIND:
    if _r[2] in _SR and _r[3] in ('', 'co'):
        if len(_r) < 8: _r.append(0)
        _r.append(_SR[_r[2]])
os.makedirs(f'{OUT}/assets', exist_ok=True)   # straight into the built site: no untracked assets/find.json in the repo (it blocked the workers' auto-deploy)
json.dump(FIND, open(f'{OUT}/assets/find.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# 11-12 (6 usability testers): where the search sends codes, problem words and questions, so it only ever links pages that exist
#   find-go.json = {codes: engine codes with a page, tr: models with a transmission page, best: the top-level pages and lists}
_dirs = lambda pat: sorted(p_.replace('\\', '/').split('/')[-2] for p_ in _glob.glob(pat))
_GO = {'codes': _dirs(f'{OUT}/check-engine-light/*/index.html'),
       'tr': sorted({u.split('/')[2] for u in globals().get('turls', [])}),
       'best': sorted({'/' + p_[len(OUT) + 1:].replace('\\', '/')[:-len('index.html')] for p_ in _glob.glob(f'{OUT}/*/index.html') + _glob.glob(f'{OUT}/best/*/index.html')})}
# 11-13 (N1 + N3): a performance version -> its regular model (perf_page.parent_of / PARENTS), so "2018 mustang gt" puts that model's
# year page first (lookup.js). Only the years whose parent page really holds that car (N3: 2015+ WRX are filed apart from the Impreza):
# if the version's own name shows up in the parent's NHTSA model names (data/extras_local*.json, e.g. IMPREZA year 2016: "WRX"), only
# the years where it does; a trim whose name holds the parent's model word (Mustang GT under MUSTANG) also its own years. par = {page: [parent, [years]]}
import collections
PERF_PAR = {}   # perf slug -> (its page, parent id, {year: parent year url}) for alias_pages.py
try:
    import perf_page as _pp
    _GO['par'] = {}; _live = {r[2] for r in FIND if r[2] and not r[6]}; _XLp = globals().get('XL', {})
    _nf = lambda t: ' ' + re.sub(r'[^a-z0-9]+', ' ', str(t).lower()).strip() + ' '
    for _pf in _glob.glob('data/perf/*.json'):
        if _pf.endswith('.auto.json'): continue
        _d = json.load(open(_pf, encoding='utf-8')); _u = _d.get('page') or f'/cars/{_d["slug"]}/'
        _par = _pp.parent_of(_d) if hasattr(_pp, 'parent_of') else ''
        if not (_par and _u in _live and os.path.exists(f'{OUT}/cars/{_par}/index.html')): continue
        _mk = _nf(_d.get('make') or ''); _tok = _nf(_d.get('name', '')).replace(_mk, ' ', 1).strip() if _mk.strip() else _nf(_d.get('name', '')).strip()
        _tok = re.sub(r'^(mercedes amg|mercedes benz|mercedes|amg) ', 'amg ', _tok) if _tok.startswith(('mercedes', 'amg')) else _tok
        _named = {int(y) for y, e in (_XLp.get(_par) or {}).items() if _tok and any(f' {_tok} ' in _nf(md) for _, md, _n in e.get('names', []))}
        _own = {y for g in _d.get('gens', []) for y in range(int(g['y0']), int(g['y1']) + 1)}
        _pn = next((r[0] for r in FIND if r[2] == f'/cars/{_par}/'), _par)   # a trim name holds the parent's own model word (MUSTANG GT, CIVIC TYPE R):
        _pw = [w for w in _nf(_pn).replace(_mk, ' ', 1).split() if len(w) >= 3]   # filed under the parent in every year; a separate name (WRX, M4) only where seen
        _cnt = collections.Counter()
        for e in (_XLp.get(_par) or {}).values():
            for _, md, _n in e.get('names', []): _cnt[_nf(md).strip()] += _n
        _base = _cnt.most_common(1)[0][0] if _cnt else ''   # the parent's main NHTSA name (F150, 1500, MUSTANG)
        _trim = any(f' {w} ' in f' {_tok} ' for w in _pw) or (len(_base) >= 3 and (f' {_base} ' in f' {_tok} ' or _tok.replace(' ', '').startswith(_base.replace(' ', ''))))
        _cov = sorted(y for y in (_named | _own if _trim else _named) if os.path.exists(f'{OUT}/cars/{_par}/{y}/index.html'))
        _GO['par'][_u] = [f'/cars/{_par}/', _cov]
        PERF_PAR[_d['slug']] = (_u, _par, {y: f'/cars/{_par}/{y}/' for y in _cov}, sorted(_own))
except Exception as _ex: print('find-go parents skipped:', _ex)
print('search parents:', len(_GO.get('par', {})), '| e.g.', {k: (v[0], v[1][:1] + v[1][-1:]) for k, v in list(_GO.get('par', {}).items())[:3]})
json.dump(_GO, open(f'{OUT}/assets/find-go.json', 'w', encoding='utf-8'), separators=(',', ':'))

# ---- the guard
_idx = {r[2] for r in FIND if r[2]}; _miss = []
for d in ('cars', 'supercars', 'electric', 'motorcycles'):
    for p_ in _glob.glob(f'{OUT}/{d}/*/index.html'):
        u = '/' + p_[len(OUT) + 1:].replace('\\', '/')[:-len('index.html')]
        if d == 'electric' and u.rstrip('/').split('/')[-1] in ('fires', 'cost', 'problems', 'driver-assist-crashes'): continue   # EV topic pages, not cars
        with open(p_, encoding='utf-8', errors='replace') as _fh:
            if _fh.read(30).startswith('<!doctype html><!--lx-alias'): continue   # 11-13: a redirect stub (alias_pages.py), not a page
        if u not in _idx: _miss.append(u)
_home = open(f'{OUT}/index.html', encoding='utf-8').read()
for u in dict.fromkeys(re.findall(r'<a class="mc[^"]*"[^>]*href="(/[^"]+)"', _home)):
    if u not in _idx: _miss.append('card ' + u)
# coming-soon / no-data cards aren't links: each one's name must match an index entry (cards drop the brand, so match on the end of the name)
fold_ = lambda t: re.sub(r'[^a-z0-9]+', ' ', html.unescape(t).lower()).strip()
_names = [fold_(r[0]) for r in FIND]
for _pg in ('index.html', 'motorcycles/index.html'):
    _h = open(f'{OUT}/{_pg}', encoding='utf-8').read() if os.path.exists(f'{OUT}/{_pg}') else ''
    for nm in dict.fromkeys(re.findall(r'<div class="mc[^"]*mc-nd[^"]*"[^>]*>.*?<b>(.*?)</b>', _h)):
        n_ = fold_(re.sub('<[^>]+>', '', nm))
        if n_ and not any(x == n_ or x.endswith(' ' + n_) for x in _names): _miss.append(f'soon card "{nm}" on /{_pg[:-10]}')
_eh = open(f'{OUT}/engines/index.html', encoding='utf-8').read() if os.path.exists(f'{OUT}/engines/index.html') else ''   # 11-12: every /engines/ card is searchable
for u in dict.fromkeys(re.findall(r'<a class="aec"[^>]*href="([^"]+)"', _eh)):
    if html.unescape(u) not in _idx: _miss.append('engine card ' + u)
for nm in dict.fromkeys(re.findall(r'<div class="aec aec-soon"[^>]*>.*?<b>(.*?)</b>', _eh)):
    if not any(x.startswith(fold_(re.sub('<[^>]+>', '', nm)) + ' ') for x in _names): _miss.append(f'soon engine "{nm}"')
if _miss: raise SystemExit(f'find index is missing {len(_miss)} page(s) - add their list to find_index.py: {_miss[:12]}')
print('find index', len(FIND), 'entries,', sum(r[6] for r in FIND), 'coming soon; every page and card covered')
