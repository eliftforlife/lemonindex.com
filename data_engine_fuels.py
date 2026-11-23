# 11-12 (Elijah: a Gas / Diesel / Hybrid / Electric selector on /engines/, and one coming-soon engine per fuel a model was sold with in the US).
# 11-23 v2 (repair-estimate workers found wrong / missing engine lists): reads EPA's full vehicles.csv (data/cache/vehicles.csv, fueleconomy.gov,
# public domain) as well as the EPA vehicle records already in data/cache/ (fetched by data_fetch_api.py and the other data_* scripts), no network.
# For every model on the site: the engines EPA lists per model year with their fuel:
#   data/engine_fuels.json = {model id: {year: [[engine "2.0L 4-cyl", fuel gas|diesel|hybrid|phev|electric, motor (EVs: EPA evMotor) or ""], ...]}}
# and the year-page fix list (applied in build.py extra()):
#   data/engine_fix.json = {model id: {year: {"engines": [...], "comb": [lo, hi], "cost": [lo, hi], "ev": bool, "n": n, "why": "..."}}}
#   written only where the fetched year data (data/extras_api*.json 'mpg', made by data_fetch_api.py from the first few EPA versions only) has an
#   engine EPA doesn't list for that model and year (wrong-model match, e.g. the Transit Connect's 2.5 on the full-size Transit), an mpg range
#   pulled out by a version that isn't this car (Tucson Fuel Cell's 50 MPGe on the 2015 Tucson), or no engines at all while EPA has them.
# Matching = data_fetch_api.py's mpg() rule (EPA make + normalized EPA model name starting with the model's name, or its FE_MODEL regex), with
# the fixes below (EF_MODEL), and these EPA versions left out (JUNK): hydrogen fuel-cell and natural-gas fleet versions, mail-truck (USPS)
# versions, and electric cars EPA files under a gas model's name that are a different vehicle (Mustang Mach-E, Blazer EV, Equinox EV, Macan
# Electric, Charger Daytona, Silverado/Sierra EV, F-150 Lightning) or were fleet / lease-only (RAV4 EV, Ranger EV, Fit EV, S-10 Electric), and
# other models EPA names after this one (Explorer Sport Trac, Taurus X, Accord Crosstour, Camry Solara, Corolla Cross, Grand Vitara XL7 ...).
# Heavy-duty pickups and vans (Ram 2500, Silverado HD, Super Duty, Sprinter, Hummer H2, the Transit's diesel) are not EPA-rated, so they're not here.
#   usage: py data_engine_fuels.py [--review]      (--review prints every EPA model name matched per site model, to check for junk by eye)
import ast, csv, glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
L = lambda p: json.load(open(os.path.join(HERE, p), encoding='utf-8')) if os.path.exists(os.path.join(HERE, p)) else None
norm = lambda s: re.sub(r'[^A-Z0-9]', '', str(s).upper())
_src = open(os.path.join(HERE, 'data_fetch_api.py'), encoding='utf-8').read()
FE_MODEL = ast.literal_eval(re.search(r'FE_MODEL = (\{.*?\n\})', _src, re.S).group(1))   # the fetch script's model regexes (a dict literal)
EF_MODEL = {   # 11-23: models the default rule matched wrongly (another model's name starts the same) or not at all
    'Ford Transit': r'TRANSIT(?!CONNECT)',                       # the full-size Transit; the Transit Connect has its own page
    'Ford E-Series': r'E[123]50(?!0)',                            # EPA: E150 / E250 / E350 Van, Wagon, Club Wagon
    'Land Rover Discovery': r'DISCOVERY(?!SPORT)|LR3|LR4',        # LR3 (2005-09) and LR4 (2010-16) are the Discovery 3 and 4 sold under another name
    'Land Rover Range Rover Sport': r'(NEW)?RANGEROVERSPORT',
    'Land Rover Range Rover': r'RANGEROVER(?!SPORT|EVOQUE|VELAR)',     # Sport, Evoque and Velar are other models
    'Acura TL': r'(3\d)?TL(?!X)', 'Kia Sedona': r'SEDONA|CARNIVAL',   # EPA: '3.2 TL' (1999-2003); the site's 2022+ Sedona pages are the Carnival (NHTSA name)
    'Acura RL': r'RL(?!X)', 'Buick Encore': r'ENCORE(?!GX)', 'Ford Bronco': r'BRONCO(?!SPORT)',
    'Fiat 500': r'500(?![LX0-9])',                                # the 500L and 500X are other cars
    'Mazda5': r'5(?!\d)|MAZDA5', 'Mazda3': FE_MODEL.get('Mazda3', r'(MAZDA)?3(?!\d)'), 'Mazda6': FE_MODEL.get('Mazda6', r'(MAZDA)?6(?!\d)'),
}
JUNK = re.compile(r'MUSTANGMACHE|BLAZEREV|EQUINOXEV|SILVERADOEV|SIERRAEV|F150LIGHTNING|MACAN.*ELECTRIC|CAYENNE.*ELECTRIC|CHARGER(2DR)?DAYTONA'   # EVs that are another vehicle
                  r'|RAV4EV|RANGEREV|RANGERPICKUP2WDEV|FITEV|S10ELECTRIC|USPS|FUELCELL'                                        # fleet / lease-only versions
                  r'|EXPLORERSPORTTRAC|TAURUSX|ACCORDCROSSTOUR|CAMRYSOLARA|COROLLACROSS|PATHFINDERARMADA|GRANDVITARAXL7|ATLASCROSS|ECLIPSECROSS')   # other models
MULTI = ('Mercedes-Benz', 'Land Rover', 'Alfa Romeo', 'Aston Martin', 'Rolls-Royce', 'Gordon Murray')
EPA_MAKES = {'Ram': ['Ram', 'Dodge'], 'Mini': ['MINI'], 'MINI': ['MINI'], 'Smart': ['smart'], 'Mercedes-AMG': ['Mercedes-Benz']}
GLUED = ('Mazda',)   # 'Mazda3' / 'Mazda5' / 'Mazda6': the make is glued to the model name
def split(name, make=None):
    g = next((m for m in GLUED if name.startswith(m) and name[len(m):len(m) + 1].isdigit()), None)
    if g and not make: return g, name
    mk = make or next((m for m in MULTI if name.startswith(m + ' ')), name.split(' ')[0])
    return mk, (name[len(mk) + 1:] if name.startswith(mk + ' ') else name)
models = {}   # id -> (name, make)
for f in (L('data/years.json') or []) + (L('data/years_new.json') or []) + (L('data/years_tesla.json') or []): models[f['id']] = (f['name'], None)
for p in ('data/extra_models.json', 'data/extra_models_new.json'):
    for m in (L(p) or {}).values(): models.setdefault(m['id'], (m['name'], m.get('brand')))
for m in L('data/new_models.json') or []: models.setdefault(m['slug'], (m['name'], m['make']))
for fid, m in ((L('data/bmw_specs.json') or {}).get('new_models') or {}).items(): models.setdefault(fid, (m['name'], 'BMW'))
for c in ((L('data/ev.json') or {}).get('cars') or []): models.setdefault(c['slug'], (c['name'], c.get('make')))
# 1. every EPA vehicle record, by (make, year): the full vehicles.csv first, then any cached REST record it doesn't have (same field names)
V, ids = {}, set()
def addv(d):
    try: k = (norm(d['make']), int(d['year']))
    except (KeyError, ValueError, TypeError): return
    i = str(d.get('id') or '')
    if i and i in ids: return
    ids.add(i); V.setdefault(k, []).append(d)
CSV = os.path.join(HERE, 'data', 'cache', 'vehicles.csv')
if os.path.exists(CSV):
    for r in csv.DictReader(open(CSV, encoding='utf-8', errors='replace')): addv(r)
for p in glob.glob(os.path.join(HERE, 'data', 'cache', '*.json')):
    try: d = json.load(open(p, encoding='utf-8'))
    except Exception: continue
    if isinstance(d, dict) and 'fuelType1' in d and d.get('make') and d.get('year'): addv(d)
print('EPA records:', sum(map(len, V.values())), flush=True)
def fuel(v):
    a = (v.get('atvType') or '').lower(); f1 = (v.get('fuelType1') or '').lower()
    if a == 'ev' or f1 == 'electricity': return 'electric'
    if 'plug-in' in a: return 'phev'
    if 'hybrid' in a: return 'hybrid'
    if a == 'diesel' or 'diesel' in f1: return 'diesel'
    return 'gas'
def junk(v):
    f1 = (v.get('fuelType1') or '').lower()
    return f1 in ('hydrogen', 'natural gas') or (v.get('atvType') or '') in ('FCV', 'eFCV', 'CNG', 'Bifuel (CNG)', 'Bifuel (LPG)') or bool(JUNK.search(norm(v.get('model', ''))))
def label(v, fu):
    d = v.get('displ')
    return 'electric' if fu == 'electric' or d in (None, '', '0', '0.0') else f"{float(d):.1f}L {v.get('cylinders')}-cyl"
num = lambda x: int(float(x)) if str(x or '').replace('.', '', 1).isdigit() and float(x) > 0 else None
out, rows_by, review = {}, {}, {}
for fid, (name, make) in sorted(models.items()):
    mk, base = split(name, make)
    nb = norm(re.sub(r'\s*\(.*?\)', '', base))
    rx = EF_MODEL.get(name) or FE_MODEL.get(name)
    pat = re.compile(rx or re.escape(nb) + (r'(?!\d(?!WD|X[24]|\d(IS|SI)$))' if nb[-1:].isdigit() else ''))   # CX-5 must not match CX-50, but 'CX-5 2WD' is a CX-5 and 'X5 4.6is' / 'X3 3.0si' an X5 / X3 (Silverado 1500 still matches)
    makes = EPA_MAKES.get(mk, [mk])
    for y in range(1995, 2027):
        rows, keep = set(), []
        for em in makes:
            for v in V.get((norm(em), y), []):
                if not pat.match(norm(v.get('model', ''))): continue
                review.setdefault(fid, {}).setdefault(('JUNK ' if junk(v) else '') + v.get('model', ''), set()).add(y)
                if junk(v): continue
                fu = fuel(v); keep.append(v)
                rows.add((label(v, fu), fu, (v.get('evMotor') or '').strip() if fu == 'electric' else ''))
        if rows: out.setdefault(fid, {})[str(y)] = sorted(map(list, rows)); rows_by[(fid, y)] = keep
# 1b. engines EPA doesn't rate (heavy vans: the Transit's 3.2 diesel, E-Series V10 / diesels, Sprinter, Hummer H2), from NHTSA VIN decodes
VX = (L('data/engine_vin_extra.json') or {}).get('models') or {}
for fid, ys in VX.items():
    for y, rs in ys.items():
        have = {(e, fu) for e, fu, _ in out.get(fid, {}).get(y, [])}
        add = [[e, fu, ''] for e, fu, _n in rs if (e, fu) not in have]
        if add: out.setdefault(fid, {})[y] = sorted(out.get(fid, {}).get(y, []) + add)
json.dump(out, open(os.path.join(HERE, 'data', 'engine_fuels.json'), 'w', encoding='utf-8'), separators=(',', ':'), sort_keys=True)
cnt = {}
for ys in out.values():
    for r in {r[1] for rs in ys.values() for r in rs}: cnt[r] = cnt.get(r, 0) + 1
print('models with EPA engines:', len(out), 'of', len(models), '| models per fuel:', cnt)
if '--review' in sys.argv:
    for fid, names in sorted(review.items()):
        print(fid); [print(f'    {n}  {min(ys)}-{max(ys)}') for n, ys in sorted(names.items())]

# 2. the year-page fix list
XA = {}
for p in ('data/extras_api.json', 'data/extras_api_new.json', 'data/extras_api_low.json', 'data/extras_api_tesla.json'):
    for f, ys in (L(p) or {}).items(): XA.setdefault(f, {}).update(ys)
fix = {}
for fid, ys in XA.items():
    for y, x in ys.items():
        keep = rows_by.get((fid, int(y)))
        if not keep: continue
        m = (x or {}).get('mpg') or {}
        ev = all(fuel(v) == 'electric' for v in keep)
        dsl = lambda e, fu: e + ' diesel' if fu == 'diesel' else e
        engs = sorted({label(v, fuel(v)) for v in keep}); shown = sorted({dsl(label(v, fuel(v)), fuel(v)) for v in keep})
        vin = [dsl(e, fu) for e, fu, _n in VX.get(fid, {}).get(y, []) if dsl(e, fu) not in shown]
        gas = [v for v in keep if fuel(v) != 'electric'] or keep   # a gas model with an EV version: mpg from the gas versions (no mpg + MPGe mix)
        comb = [c for c in (num(v.get('comb08')) for v in gas) if c]; cost = [c for c in (num(v.get('fuelCost08')) for v in gas) if c]
        have = m.get('engines') or []
        why = []
        if not ev and not have: why.append('no engines in the fetched data')
        elif not ev and set(have) - set(engs): why.append('engine EPA does not list for this model: ' + ', '.join(sorted(set(have) - set(engs))))
        if vin and not ev: why.append('NHTSA VIN decodes add (not EPA-rated): ' + ', '.join(vin))
        mc = m.get('comb') or []
        if comb and mc and (mc[0] < min(comb) or mc[1] > max(comb)): why.append(f'mpg {mc[0]}-{mc[1]} outside this model\'s EPA versions ({min(comb)}-{max(comb)})')
        if not why or not comb: continue
        fix.setdefault(fid, {})[y] = dict(engines=[] if ev else sorted(shown + vin)[:8], comb=[min(comb), max(comb)], cost=[min(cost), max(cost)] if cost else None, ev=ev, n=len(keep), why='; '.join(why))
json.dump(fix, open(os.path.join(HERE, 'data', 'engine_fix.json'), 'w', encoding='utf-8'), indent=0, sort_keys=True)
print('year-page engine fixes:', sum(map(len, fix.values())), 'model years in', len(fix), 'models -> data/engine_fix.json')
