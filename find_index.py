# 11-11 (Elijah: "M3" found nothing though /cars/bmw-m3/ is a full page): ONE search index for every car the site has, built at the end of
# the build from the same lists that make the pages and cards, so it can't drift. Run by build.py with exec() (all page lists in scope).
#   docs/assets/find.json = [[name, brand, url, kind, [years], aliases, soon], ...]
#     kind: '' scored car | co complaints only | sc supercar | ev electric | perf performance | moto motorcycle | nd no data yet
#     soon: 1 = a coming-soon / no-data card (no page yet): shown in search, grayed out, sorted last, not a link
# Build guard: every model page folder under docs/cars, supercars, electric and motorcycles, and every card link on the home grid, must be
# in the index, or the build stops (and says what's missing).
import glob as _glob
FIND, _seen = [], {}
def _fadd(name, brand, url, kind='', years=(), alias='', soon=0):
    key = url or ('soon:' + name.lower())
    if key in _seen:   # same page from two lists: merge the aliases
        r = FIND[_seen[key]]; r[5] = ' '.join(dict.fromkeys((r[5] + ' ' + alias).split())); return
    _seen[key] = len(FIND); FIND.append([name, brand, url, kind, sorted(set(int(y) for y in years)), alias.strip(), soon])
_brand_of = lambda nm, mk=None: mk or (BYNAME.get(nm, {}).get('brand') if nm in BYNAME else nm.split(' ')[0])
# common names people type that aren't in the model name (11-11, Elijah's list); generation codes and engines come from data/perf/*.json
FIND_ALIAS = {'/cars/bmw-m3/': 'competition comp cs', 'ford-shelby-gt500': 'shelby gt500 mustang', 'shelby-gt500': 'shelby gt500 mustang',
              'civic-type-r': 'type r typer', '/cars/ford-f-series/': 'f150 f 150 f250 f350 super duty', '/cars/ram-pickup/': '1500 2500 3500',
              '/cars/chevrolet-silverado/': '1500 2500 3500', '/cars/gmc-sierra/': '1500 2500 3500'}
# 1. scored models (study + new), every year with a page
for f in YEARS: _fadd(f['name'], _brand_of(f['name']), f'/cars/{f["id"]}/', '', [v['y'] for v in f['years']], FIND_ALIAS.get(f'/cars/{f["id"]}/', ''))
PERF_LIVE = {}   # perf slug -> its live page (a card for the same car then links there instead of saying coming soon)
# 2a. performance pages first (their kind wins when the same page is also a BMW model page) (data/perf/<slug>.json): generation codes and engine codes are what enthusiasts type ("G80", "S58")
for pf in _glob.glob('data/perf/*.json'):
    if pf.endswith('.auto.json'): continue
    d = json.load(open(pf, encoding='utf-8')); u = d.get('page') or f'/cars/{d["slug"]}/'
    if not os.path.exists(f'{OUT}{u}index.html'): continue
    PERF_LIVE[d['slug']] = u
    al = ' '.join([g.get('code', '') for g in d.get('gens', [])] + list((d.get('engines') or {}).keys()) + [FIND_ALIAS.get(u, '')])
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
for r in (globals().get('AE_FIND') or []): _fadd(*r)   # 11-12 engines (all_engines.py): live engine pages + coming-soon engines
os.makedirs(f'{OUT}/assets', exist_ok=True)   # straight into the built site: no untracked assets/find.json in the repo (it blocked the workers' auto-deploy)
json.dump(FIND, open(f'{OUT}/assets/find.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# 11-12 (6 usability testers): where the search sends codes, problem words and questions, so it only ever links pages that exist
#   find-go.json = {codes: engine codes with a page, tr: models with a transmission page, best: the top-level pages and lists}
_dirs = lambda pat: sorted(p_.replace('\\', '/').split('/')[-2] for p_ in _glob.glob(pat))
_GO = {'codes': _dirs(f'{OUT}/check-engine-light/*/index.html'),
       'tr': sorted({u.split('/')[2] for u in globals().get('turls', [])}),
       'best': sorted({'/' + p_[len(OUT) + 1:].replace('\\', '/')[:-len('index.html')] for p_ in _glob.glob(f'{OUT}/*/index.html') + _glob.glob(f'{OUT}/best/*/index.html')})}
json.dump(_GO, open(f'{OUT}/assets/find-go.json', 'w', encoding='utf-8'), separators=(',', ':'))

# ---- the guard
_idx = {r[2] for r in FIND if r[2]}; _miss = []
for d in ('cars', 'supercars', 'electric', 'motorcycles'):
    for p_ in _glob.glob(f'{OUT}/{d}/*/index.html'):
        u = '/' + p_[len(OUT) + 1:].replace('\\', '/')[:-len('index.html')]
        if d == 'electric' and u.rstrip('/').split('/')[-1] in ('fires', 'cost', 'problems', 'driver-assist-crashes'): continue   # EV topic pages, not cars
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
