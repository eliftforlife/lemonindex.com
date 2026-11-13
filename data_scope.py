# 11-12 round 2 (fix B; Ryan, Mitch: "Super Duty diesel notes and a diesel fuel-filter investigation on my gas F-150 page", "18 recalls on the
# year page vs 14 on the VIN check"): which NHTSA models each recall, investigation and dealer note really covers, so the build can keep the
# half-ton pages to half-ton data. Our pickup pages (F-Series, Silverado, Sierra, Ram) pool the NHTSA model names filed under them, and
# NHTSA files the F-250/F-350 Super Duty, Silverado/Sierra 2500/3500 and Ram 2500/3500 (and, on the F-Series, the F-150 Lightning, which
# has its own EV page) next to the F-150 / 1500. Output data/scope.json:
#   inv: {investigation id: {NHTSA model (normalized): [model years]}}   every investigation on a year page (FLAT_INV.txt)
#   rec: {fid: {year: {only: [recall ids only on the other models], other: [the other NHTSA models]}}}   pickups only, from the same
#        cached NHTSA recall API answers data_fetch_api.py used (one call per model), so the year page counts what the VIN check shows
#   tsb: {fid: {year: {n, top}}}   pickups only: the dealer-note count and the 3 most useful one-liners, recounted on the page's own models
#        with data_extras2.py's own scoring
# usage: py -X utf8 data_scope.py   (reads data/raw_more and data/cache from the main checkout, which has the full NHTSA cache; no network)
import csv, glob, hashlib, io, json, os, re, sys, urllib.parse, zipfile
sys.stdout.reconfigure(encoding='utf-8'); csv.field_size_limit(10 ** 8)
HERE = os.path.dirname(os.path.abspath(__file__)); MAIN = r'C:\Users\elift\Code\lemonindex-site'
_d = lambda sub: os.path.join(MAIN, 'data', sub) if os.path.isdir(os.path.join(MAIN, 'data', sub)) else os.path.join(HERE, 'data', sub)   # the main checkout holds the full cache
RAW, CACHE = _d('raw_more'), _d('cache')
_j = lambda p: json.load(open(os.path.join(HERE, 'data', p), encoding='utf-8')) if os.path.exists(os.path.join(HERE, 'data', p)) else {}
norm = lambda s: re.sub(r'[^A-Z0-9]', '', (s or '').upper())
LOCAL = _j('extras_local.json'); LOCAL.update(_j('extras_local_new.json'))
X2 = _j('extras2.json'); X2.update(_j('extras2_new.json'))
YEARS = _j('years.json') + (_j('years_new.json') or [])
PICKUPS = ('ford-f-series', 'chevrolet-silverado', 'gmc-sierra', 'ram-pickup')
# a model NHTSA files under the pickup page that isn't the half-ton: heavy duty (SD, 2500/3500/4500, F-250..F-550, HD) and, on the F-Series,
# the F-150 Lightning (its own EV page)
OTHER = re.compile(r'\bSD\b|SUPER ?DUTY|\b[2-5][05]00\b|\bF-?[2-5][05]0\b|\bHD\b|LIGHTNING', re.I)
def own(fid, md): return not (fid in PICKUPS and OTHER.search(md or ''))
def names(fid, y, cut=.05, k=3):
    e = LOCAL.get(fid, {}).get(str(y)) or {}; tot = sum(n for *_, n in e.get('names', [])) or 1
    return [(mk, md) for mk, md, n in e.get('names', []) if n / tot >= cut][:k]

# ---- investigations: which models and years each one covers
want_inv = {i['id'] for ys in X2.values() for d in ys.values() for i in (d or {}).get('inv') or []}
inv = {}
for line in open(os.path.join(RAW, 'FLAT_INV.txt'), encoding='latin-1'):
    p = line.split('\t', 4)
    if len(p) < 4 or p[0] not in want_inv or not p[3].isdigit(): continue
    inv.setdefault(p[0], {}).setdefault(norm(p[2]), set()).add(int(p[3]))
inv = {k: {m: sorted(ys) for m, ys in v.items()} for k, v in inv.items()}
print(len(inv), 'of', len(want_inv), 'investigations matched')

# ---- recalls on the pickups: the page's own models only (same API answers as data_fetch_api.py: models with 10%+ of complaints, at most 2)
def cached(url):
    p = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:20] + '.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
rec = {}
for fid in PICKUPS:
    for y in sorted(LOCAL.get(fid, {})):
        e = LOCAL[fid][y]; nm = names(fid, y, .10, 2) or [tuple(e['names'][0][:2])]
        if all(own(fid, md) for _, md in nm): continue
        main, oth, ok = set(), set(), True
        for mk, md in nm:
            r = cached(f'https://api.nhtsa.gov/recalls/recallsByVehicle?make={urllib.parse.quote(mk.lower())}&model={urllib.parse.quote(md.lower())}&modelYear={y}')
            if r is None: ok = False; break
            (main if own(fid, md) else oth).update(x.get('NHTSACampaignNumber') for x in r.get('results') or [] if x.get('NHTSACampaignNumber'))
        if ok and any(own(fid, md) for _, md in nm):   # only: on the other models and not on the page's own (a recall NHTSA adds later stays)
            rec.setdefault(fid, {})[y] = {'only': sorted(oth - main), 'other': [md for _, md in nm if not own(fid, md)]}
print('pickup recall years split:', sum(len(v) for v in rec.values()))

# ---- dealer notes on the pickups, recounted on the page's own models (data_extras2.py's scoring)
PROB = re.compile(r'noise|leak|stall|hesitat|vibrat|rattl|no start|won.t start|inoperative|fail|warning light|check engine|shudder|slip|harsh|oil consumption|overheat|grind|squeal|clunk|loss of|intermittent|drain', re.I)
TOPIC = {'brakes': r'brake', 'transmission & drivetrain': r'transmission|shift|drivetrain|clutch|axle|differential|cvt', 'engine': r'engine|oil|misfire|timing|cam|turbo',
         'electrical': r'electrical|battery|module|wiring|alternator', 'steering': r'steering', 'suspension': r'suspension|strut|shock|ball joint', 'air bags': r'air ?bag|srs',
         'fuel system': r'fuel', 'body structure': r'door|latch|body|seal|water', 'cooling': r'coolant|radiator|water pump|cooling', 'climate control': r'a/c|hvac|air condition|heater'}
def one_line(s):
    s = re.split(r'(?<=[a-z0-9)])\s{2,}|(?<=[.!?])\s', s)[0].strip().rstrip('.')
    return (s[:110].rsplit(' ', 1)[0] + '…') if len(s) > 112 else s
keys = {}
for fid in PICKUPS:
    for y in LOCAL.get(fid, {}):
        for mk, md in names(fid, y):
            if own(fid, md): keys.setdefault((mk, norm(md), int(y)), []).append(fid)
tsbk = {}
for z in sorted(glob.glob(os.path.join(RAW, 'MFR_COMMS_RECEIVED_*.zip'))):
    zz = zipfile.ZipFile(z)
    for row in csv.reader(io.TextIOWrapper(zz.open(zz.namelist()[0]), encoding='utf-8', errors='replace')):
        if len(row) < 5 or row[0] == 'TSB/Document ID': continue
        mk, md = row[1].strip().upper(), norm(row[2])
        for ys in row[3].split(','):
            if ys.strip().isdigit() and (mk, md, int(ys)) in keys:
                tsbk.setdefault((mk, md, int(ys)), {})[row[0]] = re.sub(r'\s+', ' ', row[4]).strip()
PARTS = {f['id']: {v['y']: v['parts'] for v in f['years']} for f in YEARS if f['id'] in PICKUPS}
tsb = {}
for fid in PICKUPS:
    for y in LOCAL.get(fid, {}):
        allt = {}
        for mk, md in names(fid, y):
            if own(fid, md): allt.update(tsbk.get((mk, norm(md), int(y)), {}))
        if not allt: continue
        rx = [TOPIC[a] for a, _ in (PARTS.get(fid, {}).get(int(y)) or [])[:3] if a in TOPIC]
        score = lambda s: (3 if any(re.search(r, s, re.I) for r in rx) else 0) + (1 if PROB.search(s) else 0) - (2 if re.search(r'campaign|program|radio|navigation|software update|paint|label|owner.s manual', s, re.I) else 0)
        best = sorted(allt.values(), key=lambda s: -score(s))
        tsb.setdefault(fid, {})[y] = {'n': len(allt), 'top': list(dict.fromkeys(one_line(s) for s in best[:8] if score(s) > 0))[:3]}
print('pickup dealer-note years recounted:', sum(len(v) for v in tsb.values()))
json.dump({'inv': inv, 'rec': rec, 'tsb': tsb}, open(os.path.join(HERE, 'data', 'scope.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('wrote data/scope.json')
