# Builds data/extras_api.json from official public APIs (10-31): recalls and crash-test ratings (NHTSA), fuel economy (EPA,
# fueleconomy.gov). Every response is cached under data/cache/, so a rerun only fetches what's missing.
#   usage: py data_fetch_api.py            (needs data/extras_local.json from data_extras_local.py for the NHTSA model names)
# Per family and model year:
#   recalls: every NHTSA campaign for the family's main model names that year (deduplicated by campaign number)
#   safety:  NHTSA 5-star results per body style/drive (overall, frontal, side, rollover), plus the best overall
#   mpg:     EPA combined mpg range and yearly fuel cost range across the matching versions, and the engines offered
import concurrent.futures as cf, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
sys.path.insert(0, os.path.join(LEMON, 'autopilot', 'lib'))
from families import FAMILIES

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'data', 'cache')
idof = lambda f: f.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('+', 'plus').replace('&', 'and')
LOCAL = json.load(open(os.path.join(HERE, 'data', 'extras_local.json'), encoding='utf-8'))


def get(url):
    """GET JSON with a disk cache and 3 retries. Returns None when the API has nothing (404/empty)."""
    path = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:20] + '.json')
    if os.path.exists(path):
        return json.load(open(path, encoding='utf-8'))
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'lemonindex.com data build'})
            with urllib.request.urlopen(req, timeout=40) as r:
                body = r.read().decode('utf-8', 'replace')
            data = json.loads(body) if body.strip() else None
            break
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                data = None; break
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    else:
        return None          # network trouble: not cached, so a rerun tries again
    os.makedirs(CACHE, exist_ok=True)
    json.dump(data, open(path, 'w', encoding='utf-8'))
    return data


# ---------- recalls + crash tests (NHTSA) ----------
def main_names(entry):
    """The family's NHTSA model names worth querying that year: each with at least 10% of complaints, at most 2."""
    total = sum(n for _, _, n in entry['names']) or 1
    picked = [(mk, md) for mk, md, n in entry['names'] if n / total >= 0.10][:2]
    return picked or [tuple(entry['names'][0][:2])]


def recalls(year, names):
    seen = {}
    for mk, md in names:
        url = f'https://api.nhtsa.gov/recalls/recallsByVehicle?make={urllib.parse.quote(mk.lower())}&model={urllib.parse.quote(md.lower())}&modelYear={year}'
        for r in (get(url) or {}).get('results', []) or []:
            c = r.get('NHTSACampaignNumber')
            if c and c not in seen:
                seen[c] = {'id': c, 'date': r.get('ReportReceivedDate', ''), 'part': r.get('Component', ''),
                           'summary': (r.get('Summary') or '').strip()[:600], 'risk': (r.get('Consequence') or '').strip()[:400],
                           'fix': (r.get('Remedy') or '').strip()[:400]}
    return sorted(seen.values(), key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2])   # dates are DD/MM/YYYY


def safety(year, names, fam):
    # NHTSA's ratings name models differently from its complaints ("C-CLASS" vs "C300", "F150" vs "F-150"), so pick from the
    # ratings' own model list for that make and year: names that start like the complaint name or the family name.
    mk, md = names[0]
    models = (get(f'https://api.nhtsa.gov/SafetyRatings/modelyear/{year}/make/{urllib.parse.quote(mk.lower())}') or {}).get('Results') or []
    base = norm(fam.split(' ', 1)[1] if ' ' in fam else fam)
    keys = [norm(md)[:max(3, len(norm(md)) - 2)], base[:max(3, len(base))]]
    picks = [m['Model'] for m in models if m.get('Model') and any(norm(m['Model']).startswith(k) or k.startswith(norm(m['Model'])) for k in keys)][:2]
    lst = []
    for model in picks or [md]:
        lst += (get(f'https://api.nhtsa.gov/SafetyRatings/modelyear/{year}/make/{urllib.parse.quote(mk.lower())}/model/{urllib.parse.quote(model.lower())}') or {}).get('Results') or []
    out = []
    for v in lst[:6]:
        r = ((get(f'https://api.nhtsa.gov/SafetyRatings/VehicleId/{v["VehicleId"]}') or {}).get('Results') or [{}])[0]
        if not r: continue
        out.append({'desc': v.get('VehicleDescription', ''), 'overall': r.get('OverallRating'), 'front': r.get('OverallFrontCrashRating'),
                    'side': r.get('OverallSideCrashRating'), 'rollover': r.get('RolloverRating')})
    rated = [int(x['overall']) for x in out if str(x['overall']).isdigit()]
    return {'variants': out, 'best': max(rated) if rated else None} if out else None


# ---------- fuel economy (EPA) ----------
FE_MAKE = {'BMW': 'BMW', 'GMC': 'GMC', 'RAM': 'Ram', 'MINI': 'MINI'}
fe_make = lambda mk: FE_MAKE.get(mk, mk.title())
norm = lambda s: re.sub(r'[^A-Z0-9]', '', s.upper())
FE_MODEL = {   # regex on the normalized EPA model name, where the default (family name without the make) doesn't fit
    'Ford F-Series': r'F150', 'Ram pickup': r'(RAM)?1500', 'Mercedes-Benz C-Class': r'C\d{3}', 'Mercedes-Benz E-Class': r'E\d{3}',
    'Mercedes-Benz GLK/GLC': r'GL[KC]\d{3}', 'Mercedes-Benz M/GLE': r'(ML|GLE)\d{3}', 'Mercedes-Benz CLA': r'CLA\d{3}', 'Mercedes-Benz GLA': r'GLA\d{3}',
    'BMW 3 Series': r'3\d\d', 'BMW 5 Series': r'5\d\d', 'Lexus RX': r'RX\d', 'Lexus ES': r'ES\d', 'Mazda3': r'(MAZDA)?3(?!\d)|(MAZDA)?3[45]DOOR', 'Mazda6': r'(MAZDA)?6(?!\d)',
    'Chrysler Town & Country': r'TOWNANDCOUNTRY|TOWNCOUNTRY', 'GMC Yukon': r'YUKON(?!.*XL)', 'GMC Yukon XL': r'YUKON.*XL',
    'Jeep Cherokee': r'CHEROKEE', 'Dodge Grand Caravan': r'(CARAVAN)?GRANDCARAVAN', 'Subaru Outback': r'(LEGACY)?OUTBACK', 'Subaru Crosstrek': r'(XV)?CROSSTREK', 'Hyundai Santa Fe': r'SANTAFE', 'Chrysler 300': r'300', 'Chrysler 200': r'200',
}
MAKES = {f: mk.split('|') for f, mk, *_ in FAMILIES}


def fe_pattern(fam):
    if fam in FE_MODEL: return re.compile(FE_MODEL[fam])
    base = fam.split(' ', 1)[1] if ' ' in fam else fam
    return re.compile(re.escape(norm(base)))


def mpg(fam, year):
    pat, ids = fe_pattern(fam), []
    for mk in MAKES[fam]:
        menu = get(f'https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year={year}&make={urllib.parse.quote(fe_make(mk))}') or {}
        items = menu.get('menuItem') or []
        items = items if isinstance(items, list) else [items]
        for m in items:
            if not pat.match(norm(m['value'])): continue
            opts = get(f'https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year={year}&make={urllib.parse.quote(fe_make(mk))}&model={urllib.parse.quote(m["value"])}') or {}
            o = opts.get('menuItem') or []
            ids += [x['value'] for x in (o if isinstance(o, list) else [o])][:4]
    cars = [v for v in (get(f'https://www.fueleconomy.gov/ws/rest/vehicle/{i}') for i in ids[:12]) if v]
    comb = [int(v['comb08']) for v in cars if str(v.get('comb08', '')).isdigit() and int(v['comb08']) > 0]
    cost = [int(v['fuelCost08']) for v in cars if str(v.get('fuelCost08', '')).isdigit() and int(v['fuelCost08']) > 0]
    if not comb: return None
    engines = sorted({(f"{float(v['displ']):.1f}L {v['cylinders']}-cyl" if v.get('displ') not in (None, '', '0', '0.0') else 'electric')
                      for v in cars if v.get('cylinders') or v.get('displ')})
    ev = any((v.get('atvType') or '') == 'EV' for v in cars)
    return {'comb': [min(comb), max(comb)], 'cost': [min(cost), max(cost)] if cost else None, 'engines': engines[:6], 'ev': ev, 'n': len(cars)}


# ---------- run ----------
def one(fam, fid, year, entry):
    names = main_names(entry)
    return fid, year, {'recalls': recalls(year, names), 'safety': safety(year, names, fam) if int(year) >= 2011 else None, 'mpg': mpg(fam, int(year))}


jobs = [(fam, idof(fam), y, LOCAL[idof(fam)][y]) for fam, *_ in FAMILIES if idof(fam) in LOCAL for y in sorted(LOCAL[idof(fam)])]
print(len(jobs), 'model years to fetch', flush=True)
out, t0 = {}, time.time()
with cf.ThreadPoolExecutor(8) as ex:
    for i, (fid, year, data) in enumerate(ex.map(lambda j: one(*j), jobs), 1):
        out.setdefault(fid, {})[year] = data
        if i % 100 == 0: print(f'{i}/{len(jobs)} in {time.time() - t0:.0f}s', flush=True)
json.dump(out, open(os.path.join(HERE, 'data', 'extras_api.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
n_rec = sum(len(v['recalls']) for f in out.values() for v in f.values())
n_saf = sum(1 for f in out.values() for v in f.values() if v['safety'])
n_mpg = sum(1 for f in out.values() for v in f.values() if v['mpg'])
print(f'done: {n_rec} recalls, {n_saf} model years with crash tests, {n_mpg} with mpg -> data/extras_api.json')
