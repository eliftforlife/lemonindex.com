# 11-23 (repair-estimate workers: "the full-size Transit has a 3.2 Power Stroke diesel"; Sprinter / Hummer H2 have no engine list at all):
# engines EPA doesn't rate. Vans and trucks over 8,500 lb (Transit diesel, Hummer H2, Express 2500/3500 diesels and big V8s) have no
# fueleconomy.gov record, so data_engine_fuels.py can't list them. This script finds them from NHTSA's own VIN decoder instead:
#   1. every NHTSA owner complaint (FLAT_CMPL.txt + COMPLAINTS_RECEIVED_2025-2026.zip) on the models below, by the NHTSA make + model names
#      their own pages count (data/extras_local*.json 'names'), with its partial VIN
#   2. the VIN's first 8 characters + model year = one key; one VIN per key decoded with NHTSA vPIC's batch decoder (public, free; cached)
#   3. an engine (displacement + cylinders + fuel, or electric) counts for a model year when 5+ complaints' VINs (and 4%+ of the year's, in a year
#      with 10+ decoded complaints) decode to it
#   -> data/engine_vin_extra.json = {model id: {year: [[engine "3.2L 5-cyl", fuel gas|diesel|electric, complaints], ...]}}
# data_engine_fuels.py adds these to engine_fuels.json and the year-page fix list (source: NHTSA vPIC VIN decodes).
#   usage: py -X utf8 data_engine_vin_extra.py            (re-reads the complaint files; only new VIN keys hit vPIC)
import collections, json, os, re, sys, time, urllib.parse, urllib.request, zipfile
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
FLAT = os.path.join(LEMON, 'video 1 most reliable', 'data', 'raw', 'FLAT_CMPL.txt')
NEWZ = os.path.join(LEMON, 'data', 'raw', 'nhtsa', 'COMPLAINTS_RECEIVED_2025-2026.zip')
WORK = os.path.join(LEMON, 'data', 'engine_vin_extra'); os.makedirs(WORK, exist_ok=True)
DEC = os.path.join(WORK, 'decoded.json')
MODELS = ['ford-transit', 'hummer-h2', 'chevrolet-express']   # 11-23: E-Series and Sprinter decodes left out: their partial VINs decode to engines those vans
                                                             # never had (E-Series 6.7 diesel, Sprinter 2.2 '6-cyl'), so the decoder can't be trusted there
MIN_N, MIN_SHARE, MIN_YEAR = 5, 0.04, 10   # an engine needs 5+ complaints and 4%+ of that model year's decoded ones (one-off decodes are often another model's VIN)
VALID = re.compile(r'^[A-HJ-NPR-Z0-9]{11}$')
L = lambda p: json.load(open(os.path.join(HERE, p), encoding='utf-8')) if os.path.exists(os.path.join(HERE, p)) else {}
XL = {}
for p in ('data/extras_local.json', 'data/extras_local_new.json', 'data/extras_local_low.json'):
    for f, ys in L(p).items(): XL.setdefault(f, {}).update(ys)
W = {}   # (make, model, year) -> model id
for fid in MODELS:
    for y, x in XL.get(fid, {}).items():
        for mk, md, _n in (x or {}).get('names') or []: W[(mk.upper(), md.upper(), int(y))] = fid
print('NHTSA names:', len(W), 'make/model/years for', len({v for v in W.values()}), 'models', flush=True)
keys = collections.Counter(); rep = {}
def take(p):
    if len(p) < 16 or not p[5].strip().isdigit(): return
    fid = W.get((p[3].strip().upper(), p[4].strip().upper(), int(p[5])))
    if not fid: return
    v = p[14].strip().upper()[:11]
    if not VALID.match(v): return
    k = (fid, v[:8], p[5].strip()); keys[k] += 1; rep.setdefault(k, v)
with open(FLAT, encoding='latin-1') as fh:
    for line in fh: take(line.rstrip('\r\n').split('\t'))
if os.path.exists(NEWZ):
    with zipfile.ZipFile(NEWZ) as z:
        with z.open(z.namelist()[0]) as fh:
            for raw in fh: take(raw.decode('latin-1').rstrip('\r\n').split('\t'))
print('complaints with a VIN:', sum(keys.values()), '| VIN keys:', len(keys), flush=True)
dec = json.load(open(DEC, encoding='utf-8')) if os.path.exists(DEC) else {}
todo = [k for k in keys if f'{k[1]}|{k[2]}' not in dec]
for i in range(0, len(todo), 50):
    chunk = todo[i:i + 50]
    body = urllib.parse.urlencode({'format': 'json', 'data': ';'.join(f'{rep[k]}******,{k[2]}' for k in chunk)}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request('https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/', data=body,
                                                                headers={'User-Agent': 'lemonindex.com data build'}), timeout=90))
    for k, res in zip(chunk, r['Results']):
        dec[f'{k[1]}|{k[2]}'] = {x: res.get(x) for x in ('Make', 'Model', 'Series', 'DisplacementL', 'EngineCylinders', 'EngineModel', 'FuelTypePrimary', 'ElectrificationLevel', 'GVWR')}
    json.dump(dec, open(DEC, 'w', encoding='utf-8'), indent=0); time.sleep(2)
print('decoded:', len(todo), 'new keys', flush=True)
def engine(d):
    f = (d.get('FuelTypePrimary') or '').lower(); el = (d.get('ElectrificationLevel') or '').lower()
    if 'electric' in f or 'bev' in el: return ('electric', 'electric')
    try: disp = float(d.get('DisplacementL') or 0); cyl = int(float(d.get('EngineCylinders') or 0))
    except ValueError: return None
    if not (0.6 <= disp <= 9.0 and 2 <= cyl <= 12) or not re.match(r'^\d+\.\d', str(d.get('DisplacementL'))): return None   # '6' = a bad decode
    return (f'{disp:.1f}L {cyl}-cyl', 'diesel' if 'diesel' in f else 'gas')
cnt = collections.defaultdict(collections.Counter)
for (fid, v8, y), n in keys.items():
    e = engine(dec.get(f'{v8}|{y}') or {})
    if e: cnt[(fid, y)][e] += n
out = {}
for (fid, y), c in sorted(cnt.items()):
    tot = sum(c.values())
    if tot < MIN_YEAR: continue   # too few decoded complaints that year to tell
    rows = [[e, fu, n] for (e, fu), n in sorted(c.items()) if n >= MIN_N and n >= MIN_SHARE * tot]
    if rows: out.setdefault(fid, {})[y] = rows
json.dump(dict(note='NHTSA vPIC VIN decodes of NHTSA owner complaints (engines with 5+ complaints and 4%+ of a model year); data_engine_vin_extra.py', models=out),
          open(os.path.join(HERE, 'data', 'engine_vin_extra.json'), 'w', encoding='utf-8'), indent=0, sort_keys=True)
for fid, ys in out.items(): print(fid, {y: [f'{e} {fu} ({n})' for e, fu, n in r] for y, r in ys.items()})
