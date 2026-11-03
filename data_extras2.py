# Builds data/extras2.json (11-02, Elijah: "more free data, dead simple for a 16- to 99-year-old"):
#   tsb:   the automaker's own notes to dealers about known problems and fixes (NHTSA manufacturer communications, MFR_COMMS_RECEIVED_*.csv),
#          count + the 3 most useful one-liners (ones about this year's top owner complaint areas first)
#   inv:   NHTSA defect investigations that covered the car (FLAT_INV.txt), open or closed
#   tech:  stability control / forward collision warning / lane departure warning: standard, optional or not offered (NHTSA ratings API)
#   crash: older 5-star results (before 2011 the API only has driver/passenger stars, no overall) + NHTSA's crash-test photo
#   usage: py data_extras2.py   (needs the NHTSA files in data/raw_more/, see RAW below; API responses cached in data/cache/ like data_fetch_api.py)
import csv, glob, hashlib, io, json, os, re, sys, time, urllib.parse, urllib.request, zipfile, concurrent.futures as cf
sys.stdout.reconfigure(encoding='utf-8'); csv.field_size_limit(10 ** 8)
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'data', 'cache'); RAW = os.path.join(HERE, 'data', 'raw_more')
LOCAL = json.load(open(os.path.join(HERE, 'data', 'extras_local.json'), encoding='utf-8'))
YEARS = json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8'))
norm = lambda s: re.sub(r'[^A-Z0-9]', '', (s or '').upper())

def get(url):
    path = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:20] + '.json')
    if os.path.exists(path): return json.load(open(path, encoding='utf-8'))
    for a in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'lemonindex.com data build'}), timeout=40) as r:
                body = r.read().decode('utf-8', 'replace'); data = json.loads(body) if body.strip() else None; break
        except urllib.error.HTTPError as e:
            if e.code in (400, 404): data = None; break
            time.sleep(2 * (a + 1))
        except Exception: time.sleep(2 * (a + 1))
    else: return None
    os.makedirs(CACHE, exist_ok=True); json.dump(data, open(path, 'w', encoding='utf-8')); return data

def names(fid, y):
    e = LOCAL.get(fid, {}).get(str(y)) or {}; tot = sum(n for *_, n in e.get('names', [])) or 1
    return [(mk, md) for mk, md, n in e.get('names', []) if n / tot >= .05][:3]

# ---- wanted (make, model-normalized) -> [(fid, year)]
WANT = {}
for f in YEARS:
    for v in f['years']:
        for mk, md in names(f['id'], v['y']): WANT.setdefault((mk, norm(md), v['y']), []).append(f['id'])
print(len(WANT), 'make/model/year keys')

# ---- service bulletins
PROB = re.compile(r'noise|leak|stall|hesitat|vibrat|rattl|no start|won.t start|inoperative|fail|warning light|check engine|shudder|slip|harsh|oil consumption|overheat|grind|squeal|clunk|loss of|intermittent|drain', re.I)
TOPIC = {'brakes': r'brake', 'transmission & drivetrain': r'transmission|shift|drivetrain|clutch|axle|differential|cvt', 'engine': r'engine|oil|misfire|timing|cam|turbo',
         'electrical': r'electrical|battery|module|wiring|alternator', 'steering': r'steering', 'suspension': r'suspension|strut|shock|ball joint', 'air bags': r'air ?bag|srs',
         'fuel system': r'fuel', 'body structure': r'door|latch|body|seal|water', 'cooling': r'coolant|radiator|water pump|cooling', 'climate control': r'a/c|hvac|air condition|heater'}
tsb = {}
for z in sorted(glob.glob(os.path.join(RAW, 'MFR_COMMS_RECEIVED_*.zip'))):
    zz = zipfile.ZipFile(z)
    for row in csv.reader(io.TextIOWrapper(zz.open(zz.namelist()[0]), encoding='utf-8', errors='replace')):
        if len(row) < 5 or row[0] == 'TSB/Document ID': continue
        mk, md = row[1].strip().upper(), norm(row[2]); summ = re.sub(r'\s+', ' ', row[4]).strip()
        for ys in row[3].split(','):
            if ys.strip().isdigit() and (mk, md, int(ys)) in WANT:
                tsb.setdefault((mk, md, int(ys)), {})[row[0]] = summ
    print('read', os.path.basename(z), len(tsb))

def one_line(s):
    s = re.split(r'(?<=[a-z0-9)])\s{2,}|(?<=[.!?])\s', s)[0].strip().rstrip('.')
    return (s[:110].rsplit(' ', 1)[0] + '…') if len(s) > 112 else s

# ---- investigations
inv = {}
for line in open(os.path.join(RAW, 'FLAT_INV.txt'), encoding='latin-1'):
    p = line.rstrip('\n').split('\t')
    if len(p) < 11 or not p[3].isdigit(): continue
    k = (p[1].strip().upper(), norm(p[2]), int(p[3]))
    if k in WANT: inv.setdefault(k, {})[p[0]] = {'id': p[0], 'part': p[4].strip().title(), 'opened': p[6][:4], 'closed': p[7][:4], 'subject': p[9].strip().capitalize(), 'open': not p[7].strip()}

# ---- safety tech + crash photo + older crash stars (NHTSA ratings API, same model picking as data_fetch_api.safety)
def ratings(fid, y):
    nm = names(fid, y)
    if not nm: return None
    mk, md = nm[0]; fam = next(f['name'] for f in YEARS if f['id'] == fid)
    models = (get(f'https://api.nhtsa.gov/SafetyRatings/modelyear/{y}/make/{urllib.parse.quote(mk.lower())}') or {}).get('Results') or []
    base = norm(fam.split(' ', 1)[1] if ' ' in fam else fam); keys = [norm(md)[:max(3, len(norm(md)) - 2)], base]
    picks = [m['Model'] for m in models if m.get('Model') and any(norm(m['Model']).startswith(k) or k.startswith(norm(m['Model'])) for k in keys)][:2]
    lst = []
    for model in picks or [md]: lst += (get(f'https://api.nhtsa.gov/SafetyRatings/modelyear/{y}/make/{urllib.parse.quote(mk.lower())}/model/{urllib.parse.quote(model.lower())}') or {}).get('Results') or []
    rs = [r for r in ((get(f'https://api.nhtsa.gov/SafetyRatings/VehicleId/{v["VehicleId"]}') or {}).get('Results') or [None] for v in lst[:6]) for r in [r[0] if isinstance(r, list) else r] if r]
    if not rs: return None
    rank = {'Standard': 2, 'Optional': 1, 'No': 0}
    tech = {k: max((r.get(f) or 'No' for r in rs), key=lambda x: rank.get(x, -1)) for k, f in (('esc', 'NHTSAElectronicStabilityControl'), ('fcw', 'NHTSAForwardCollisionWarning'), ('ldw', 'NHTSALaneDepartureWarning'))}
    stars = lambda f: max([int(r[f]) for r in rs if str(r.get(f, '')).isdigit()] or [0]) or None
    photo = next((r.get('FrontCrashPicture') for r in rs if (r.get('FrontCrashPicture') or '').startswith('http')), None)
    old = {'front': stars('FrontCrashDriversideRating'), 'side': stars('SideCrashDriversideRating'), 'roll': stars('RolloverRating2') or stars('RolloverRating')} if y < 2011 else None
    return {'tech': tech, 'photo': photo, 'old': old}

jobs = [(f['id'], v['y']) for f in YEARS for v in f['years']]
out, t0 = {}, time.time()
with cf.ThreadPoolExecutor(8) as ex:
    for i, ((fid, y), r) in enumerate(zip(jobs, ex.map(lambda j: ratings(*j), jobs)), 1):
        d = out.setdefault(fid, {}).setdefault(str(y), {})
        if r: d.update(r)
        if i % 200 == 0: print(f'ratings {i}/{len(jobs)} {time.time() - t0:.0f}s', flush=True)
for f in YEARS:
    tops = {}
    for v in f['years']:
        d = out[f['id']][str(v['y'])]; keys = [(mk, norm(md), v['y']) for mk, md in names(f['id'], v['y'])]
        allt = {}; [allt.update(tsb.get(k, {})) for k in keys]
        if allt:
            areas = [p for p, _ in v['parts'][:3]]; rx = [TOPIC[a] for a in areas if a in TOPIC]
            score = lambda s: (3 if any(re.search(r, s, re.I) for r in rx) else 0) + (1 if PROB.search(s) else 0) - (2 if re.search(r'campaign|program|radio|navigation|software update|paint|label|owner.s manual', s, re.I) else 0)
            best = sorted(allt.values(), key=lambda s: -score(s))
            d['tsb'] = {'n': len(allt), 'top': list(dict.fromkeys(one_line(s) for s in best[:8] if score(s) > 0))[:3]}
        alli = {}; [alli.update(inv.get(k, {})) for k in keys]
        if alli: d['inv'] = sorted(alli.values(), key=lambda x: (not x['open'], -int(x['opened'] or 0)))[:6]
json.dump(out, open(os.path.join(HERE, 'data', 'extras2.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
od = out['honda-odyssey']['2008']; print('sample 2008 Odyssey:', json.dumps(od, ensure_ascii=False)[:900])
