# Supercars section data (11-04, Elijah: "add super cars"). -> data/supercars.json
# Per model family and model year, from free official sources only:
#   EPA fueleconomy.gov web services: every version's city/highway/combined mpg, yearly fuel cost, engine, transmission, drive, gas-guzzler flag
#   NHTSA recalls API: every recall campaign for the family's EPA model names that year; NHTSA complaints (complaints.db): count
# No prices or "average miles" (no free source; listing/auction sites forbid scraping). Specs like 0-60 / top speed are a later, sourced pass.
import json, os, re, hashlib, urllib.request, urllib.parse, time, sqlite3, collections, sys, concurrent.futures as cf
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'data', 'cache')
Y0, Y1 = 2010, 2025
def get(url, accept_json=True):
    p = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:20] + '.json')
    if os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    for k in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'LemonIndex/1.0 (lemonindex.com)', 'Accept': 'application/json'})
            raw = urllib.request.urlopen(req, timeout=20).read()
            d = json.loads(raw) if raw.strip() else None; json.dump(d, open(p, 'w', encoding='utf-8')); return d
        except Exception: time.sleep(1 + k)
    return None
EPA = 'https://www.fueleconomy.gov/ws/rest/vehicle/'
arr = lambda d, k='menuItem': [] if not d else (d[k] if isinstance(d.get(k), list) else [d[k]] if d.get(k) else [])
# (family, EPA make, model regex on the EPA model name, NHTSA make for recalls/complaints)
F = [
 ('Ferrari 458 Italia', 'Ferrari', r'458.*', 'FERRARI'), ('Ferrari 488', 'Ferrari', r'488.*', 'FERRARI'), ('Ferrari F8 Tributo', 'Ferrari', r'F8.*', 'FERRARI'),
 ('Ferrari 296', 'Ferrari', r'296.*', 'FERRARI'), ('Ferrari SF90 Stradale', 'Ferrari', r'SF90.*', 'FERRARI'), ('Ferrari 812 Superfast', 'Ferrari', r'812.*', 'FERRARI'),
 ('Ferrari F12berlinetta', 'Ferrari', r'F12.*', 'FERRARI'), ('Ferrari California', 'Ferrari', r'California.*', 'FERRARI'), ('Ferrari Portofino', 'Ferrari', r'Portofino.*', 'FERRARI'),
 ('Ferrari Roma', 'Ferrari', r'Roma.*', 'FERRARI'), ('Ferrari GTC4Lusso / FF', 'Ferrari', r'(GTC4.*|FF.*)', 'FERRARI'),
 ('Lamborghini Huracán', 'Lamborghini', r'Hurac.*', 'LAMBORGHINI'), ('Lamborghini Aventador', 'Lamborghini', r'Aventador.*', 'LAMBORGHINI'),
 ('Lamborghini Gallardo', 'Lamborghini', r'Gallardo.*', 'LAMBORGHINI'), ('Lamborghini Urus', 'Lamborghini', r'Urus.*', 'LAMBORGHINI'), ('Lamborghini Revuelto', 'Lamborghini', r'Revuelto.*', 'LAMBORGHINI'),
 ('McLaren 570S / 540C', 'McLaren Automotive', r'(570.*|540.*|600LT.*)', 'MCLAREN'), ('McLaren 720S / 750S', 'McLaren Automotive', r'(720.*|750.*|765.*)', 'MCLAREN'),
 ('McLaren 650S / 12C', 'McLaren Automotive', r'(650.*|MP4.*|12C.*|675.*)', 'MCLAREN'), ('McLaren GT', 'McLaren Automotive', r'GT.*', 'MCLAREN'), ('McLaren Artura', 'McLaren Automotive', r'Artura.*', 'MCLAREN'),
 ('Aston Martin Vantage', 'Aston Martin', r'(V8 |V12 )?Vantage.*', 'ASTON MARTIN'), ('Aston Martin DB11 / DB12', 'Aston Martin', r'DB1[12].*', 'ASTON MARTIN'),
 ('Aston Martin DBS', 'Aston Martin', r'DBS.*', 'ASTON MARTIN'), ('Aston Martin DBX', 'Aston Martin', r'DBX.*', 'ASTON MARTIN'),
 ('Bentley Continental GT', 'Bentley', r'Continental.*', 'BENTLEY'), ('Bentley Bentayga', 'Bentley', r'Bentayga.*', 'BENTLEY'),
 ('Rolls-Royce Ghost', 'Rolls-Royce', r'Ghost.*', 'ROLLS-ROYCE'), ('Rolls-Royce Cullinan', 'Rolls-Royce', r'Cullinan.*', 'ROLLS-ROYCE'), ('Rolls-Royce Phantom', 'Rolls-Royce', r'Phantom.*', 'ROLLS-ROYCE'),
 ('Bugatti Chiron', 'Bugatti', r'Chiron.*', 'BUGATTI'), ('Bugatti Veyron', 'Bugatti', r'Veyron.*', 'BUGATTI'),
 ('Audi R8', 'Audi', r'R8.*', 'AUDI'), ('Nissan GT-R', 'Nissan', r'GT-R.*', 'NISSAN'), ('Acura NSX', 'Acura', r'NSX.*', 'ACURA'),
 ('Mercedes-AMG GT', 'Mercedes-Benz', r'(AMG GT.*|SLS AMG.*)', 'MERCEDES-BENZ'), ('Chevrolet Corvette Z06', 'Chevrolet', r'Corvette.*', 'CHEVROLET'), ('Ford GT', 'Ford', r'GT', 'FORD'),
 ('Lotus Evora / Emira', 'Lotus', r'(Evora.*|Emira.*)', 'LOTUS'), ('Porsche 911 Turbo / GT3', 'Porsche', r'911 (Turbo.*|GT[23].*)', 'PORSCHE'), ('Porsche 918 Spyder', 'Porsche', r'918.*', 'PORSCHE'),
]
makes = sorted(set(f[1] for f in F))
# 1. EPA model names per make and year
jobs = [(mk, y) for mk in makes for y in range(Y0, Y1 + 1)]
with cf.ThreadPoolExecutor(10) as ex:
    menus = dict(zip(jobs, ex.map(lambda j: [m['value'] for m in arr(get(EPA + 'menu/model?' + urllib.parse.urlencode({'year': j[1], 'make': j[0]})))], jobs)))
# 2. options (vehicle ids) for each matching model name
want = []
for fam, mk, rx, nmk in F:
    for y in range(Y0, Y1 + 1):
        for m in menus[(mk, y)]:
            if re.fullmatch(rx, m) and not (fam == 'Chevrolet Corvette Z06' and 'Z06' not in m and 'ZR1' not in m and y < 2020) and not (fam == 'Chevrolet Corvette Z06' and y >= 2020 and not re.search('Z06|ZR1|E-Ray', m)):
                want.append((fam, mk, y, m))
with cf.ThreadPoolExecutor(10) as ex:
    opts = list(ex.map(lambda w: arr(get(EPA + 'menu/options?' + urllib.parse.urlencode({'year': w[2], 'make': w[1], 'model': w[3]}))), want))
ids = [(w, o['value'], o['text']) for w, os_ in zip(want, opts) for o in os_]
with cf.ThreadPoolExecutor(10) as ex:
    vs = list(ex.map(lambda t: get(EPA + str(t[1])), ids))
fam_years = collections.defaultdict(lambda: collections.defaultdict(list))
for (w, vid, txt), v in zip(ids, vs):
    if not v: continue
    fam_years[w[0]][w[2]].append(dict(model=w[3], trim=txt, comb=int(v.get('comb08') or 0), city=int(v.get('city08') or 0), hwy=int(v.get('highway08') or 0),
        cost=int(v.get('fuelCost08') or 0), guzzler=bool(v.get('guzzler')), engine=f"{v.get('displ')}L {v.get('cylinders')}-cyl".replace('None', '?'), trany=v.get('trany'), drive=v.get('drive'),
        fuel=v.get('fuelType1'), hybrid=bool(v.get('atvType') in ('Hybrid', 'Plug-in Hybrid')) or 'Hybrid' in (v.get('eng_dscr') or '')))
# 3. recalls + complaints
con = sqlite3.connect(r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db')
rjobs = [(fam, nmk, y, m) for fam, mk, rx, nmk in F for y in fam_years[fam] for m in sorted({e['model'] for e in fam_years[fam][y]})]
with cf.ThreadPoolExecutor(12) as ex:
    rr = list(ex.map(lambda j: get('https://api.nhtsa.gov/recalls/recallsByVehicle?' + urllib.parse.urlencode({'make': j[1], 'model': j[3], 'modelYear': j[2]})), rjobs))
REC = collections.defaultdict(lambda: collections.defaultdict(dict))
for (fam, nmk, y, m), d in zip(rjobs, rr):
    for r in (d or {}).get('results', []): REC[fam][y][r.get('NHTSACampaignNumber')] = dict(id=r.get('NHTSACampaignNumber'), date=r.get('ReportReceivedDate'), part=r.get('Component'), summary=(r.get('Summary') or '')[:300])
out = []
for fam, mk, rx, nmk in F:
    Y = fam_years[fam]
    if not Y: print('no EPA data', fam); continue
    years = []
    for y in sorted(Y):
        e = [x for x in Y[y] if x['comb']]
        if not e: continue
        names = sorted({x['model'] for x in Y[y]})
        nc = sum(con.execute('SELECT count(*) FROM complaints WHERE make=? AND year=? AND upper(model) LIKE ?', (nmk, y, n.upper().split(' ')[0] + '%')).fetchone()[0] for n in names[:1])
        years.append(dict(y=y, versions=len(e), comb=[min(x['comb'] for x in e), max(x['comb'] for x in e)], city=[min(x['city'] for x in e), max(x['city'] for x in e)],
                          hwy=[min(x['hwy'] for x in e), max(x['hwy'] for x in e)], cost=[min(x['cost'] for x in e), max(x['cost'] for x in e)], guzzler=any(x['guzzler'] for x in e),
                          engines=sorted({x['engine'] for x in e}), drive=sorted({x['drive'] for x in e if x['drive']}), hybrid=any(x['hybrid'] for x in e), names=names,
                          recalls=sorted(REC[fam][y].values(), key=lambda r: r['date'] or '', reverse=True), complaints=nc))
    if not years: continue
    allrec = {r['id']: r for yy in years for r in yy['recalls']}
    out.append(dict(name=fam, make=mk.replace(' Automotive', ''), years=years, recalls=len(allrec), best_mpg=max(yy['comb'][1] for yy in years), worst_mpg=min(yy['comb'][0] for yy in years),
                    max_cost=max(yy['cost'][1] for yy in years), complaints=sum(yy['complaints'] for yy in years)))
    print(f"{fam:32} {years[0]['y']}-{years[-1]['y']}  mpg {out[-1]['worst_mpg']}-{out[-1]['best_mpg']}  fuel ${out[-1]['max_cost']:,}/yr  recalls {len(allrec)}  complaints {out[-1]['complaints']}", flush=True)
json.dump(out, open(os.path.join(HERE, 'data', 'supercars.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('families', len(out))
