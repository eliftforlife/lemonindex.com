# 11-12 (Elijah: a Gas / Diesel / Hybrid / Electric selector on /engines/, and one coming-soon engine per fuel a model was sold with in the US).
# Reads ONLY the EPA vehicle records already in data/cache/ (fueleconomy.gov, fetched by data_fetch_api.py and the other data_* scripts), no network.
# For every model on the site: the engines EPA lists per model year with their fuel:
#   data/engine_fuels.json = {model id: {year: [[engine "2.0L 4-cyl", fuel gas|diesel|hybrid|phev|electric, motor (EVs: EPA evMotor) or ""], ...]}}
# Matching = the same rule as data_fetch_api.py's mpg(): EPA make + normalized EPA model name starting with the model's name (or its FE_MODEL regex).
# Heavy-duty pickups (Ram 2500, Silverado HD, Super Duty) are not EPA-rated, so their diesels are not in this data.
#   usage: py data_engine_fuels.py
import ast, glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
L = lambda p: json.load(open(os.path.join(HERE, p), encoding='utf-8')) if os.path.exists(os.path.join(HERE, p)) else None
norm = lambda s: re.sub(r'[^A-Z0-9]', '', str(s).upper())
_src = open(os.path.join(HERE, 'data_fetch_api.py'), encoding='utf-8').read()
FE_MODEL = ast.literal_eval(re.search(r'FE_MODEL = (\{.*?\n\})', _src, re.S).group(1))   # the fetch script's model regexes (a dict literal)
MULTI = ('Mercedes-Benz', 'Land Rover', 'Alfa Romeo', 'Aston Martin', 'Rolls-Royce', 'Gordon Murray')
EPA_MAKES = {'Ram': ['Ram', 'Dodge'], 'Mini': ['MINI'], 'MINI': ['MINI'], 'Smart': ['smart'], 'Mercedes-AMG': ['Mercedes-Benz']}
def split(name, make=None):
    mk = make or next((m for m in MULTI if name.startswith(m + ' ')), name.split(' ')[0])
    return mk, (name[len(mk) + 1:] if name.startswith(mk + ' ') else name)
models = {}   # id -> (name, make)
for f in (L('data/years.json') or []) + (L('data/years_new.json') or []): models[f['id']] = (f['name'], None)
for p in ('data/extra_models.json', 'data/extra_models_new.json'):
    for m in (L(p) or {}).values(): models.setdefault(m['id'], (m['name'], m.get('brand')))
for m in L('data/new_models.json') or []: models.setdefault(m['slug'], (m['name'], m['make']))
for fid, m in ((L('data/bmw_specs.json') or {}).get('new_models') or {}).items(): models.setdefault(fid, (m['name'], 'BMW'))
for c in ((L('data/ev.json') or {}).get('cars') or []): models.setdefault(c['slug'], (c['name'], c.get('make')))
# 1. every EPA vehicle record in the cache, by (make, year)
V = {}
for p in glob.glob(os.path.join(HERE, 'data', 'cache', '*.json')):
    try: d = json.load(open(p, encoding='utf-8'))
    except Exception: continue
    if not (isinstance(d, dict) and 'fuelType1' in d and d.get('make') and d.get('year')): continue
    V.setdefault((norm(d['make']), int(d['year'])), []).append(d)
print('EPA records in cache:', sum(map(len, V.values())), flush=True)
def fuel(v):
    a = (v.get('atvType') or '').lower(); f1 = (v.get('fuelType1') or '').lower()
    if a == 'ev' or f1 == 'electricity': return 'electric'
    if 'plug-in' in a: return 'phev'
    if 'hybrid' in a: return 'hybrid'
    if a == 'diesel' or 'diesel' in f1: return 'diesel'
    return 'gas'
out = {}
for fid, (name, make) in sorted(models.items()):
    mk, base = split(name, make)
    nb = norm(re.sub(r'\s*\(.*?\)', '', base))
    pat = re.compile(FE_MODEL.get(name) or re.escape(nb) + (r'(?!\d)' if nb[-1:].isdigit() else ''))   # CX-5 must not match CX-50 (Silverado 1500 still matches)
    makes = EPA_MAKES.get(mk, [mk])
    for y in range(1995, 2027):
        rows = set()
        for em in makes:
            for v in V.get((norm(em), y), []):
                if not pat.match(norm(v.get('model', ''))): continue
                fu = fuel(v); d = v.get('displ')
                eng = 'electric' if fu == 'electric' or d in (None, '', '0', '0.0') else f"{float(d):.1f}L {v.get('cylinders')}-cyl"
                rows.add((eng, fu, (v.get('evMotor') or '').strip() if fu == 'electric' else ''))
        if rows: out.setdefault(fid, {})[str(y)] = sorted(map(list, rows))
json.dump(out, open(os.path.join(HERE, 'data', 'engine_fuels.json'), 'w', encoding='utf-8'), separators=(',', ':'), sort_keys=True)
cnt = {}
for ys in out.values():
    for r in {r[1] for rs in ys.values() for r in rs}: cnt[r] = cnt.get(r, 0) + 1
print('models with EPA engines:', len(out), 'of', len(models), '| models per fuel:', cnt)
