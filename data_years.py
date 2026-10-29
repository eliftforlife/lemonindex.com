# Builds data/years.json for the model-year pages (10-29: Elijah wants people to look up their exact car + year and see its real issues).
#   usage: py data_years.py      (reads the Lemon Index folder: autopilot/lib families + mysales, data/complaints.db, the fixed model_years.csv)
# Same rules as lemon.py: model years 2000-2022 (2000-2009 added 10-29), a complaint counts only if filed within 3 years of its model year, mysales year codes.
# Per family and year: Lemon Index, complaints, sold, the top problem areas (share of that year's complaints) and up to 3 short owner complaints,
# verbatim apart from letter case (NHTSA files most in ALL CAPS), with their NHTSA ODI number so anyone can check them.
import os, sys, re, csv, json, sqlite3, random
from collections import defaultdict
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
sys.path.insert(0, os.path.join(LEMON, 'autopilot', 'lib'))
from families import FAMILIES
import mysales
Y0, Y1, WINDOW = 2000, 2022, 3
OUTD = next(d for d in os.scandir(LEMON) if d.name.startswith('v3-unreliable')).path + r'\data\out'
PART = {'ELECTRICAL SYSTEM': 'electrical', 'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'VEHICLE SPEED CONTROL': 'speed control',
        'FUEL/PROPULSION SYSTEM': 'fuel or EV drive system', 'FORWARD COLLISION AVOIDANCE': 'automatic emergency braking', 'VISIBILITY/WIPER': 'wipers & visibility',
        'VISIBILITY': 'visibility', 'AIR BAGS': 'airbags', 'STRUCTURE': 'body structure', 'EXTERIOR LIGHTING': 'lights', 'ELECTRONIC STABILITY CONTROL (ESC)': 'stability control',
        'LANE DEPARTURE': 'lane assist', 'ENGINE AND ENGINE COOLING': 'engine', 'SEAT BELTS': 'seat belts', 'ENGINE': 'engine', 'STEERING': 'steering', 'SUSPENSION': 'suspension',
        'WHEELS': 'wheels', 'TIRES': 'tires', 'SEATS': 'seats', 'LATCHES/LOCKS/LINKAGES': 'doors, locks & latches', 'BACK OVER PREVENTION': 'backup camera',
        'PARKING BRAKE': 'parking brake', 'HYBRID PROPULSION SYSTEM': 'hybrid system', 'ELECTRONIC STABILITY CONTROL': 'stability control', 'EQUIPMENT': 'equipment'}
part = lambda c: PART.get(c, c.lower().replace('/', ' / '))
idof = lambda f: f.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('+', 'plus').replace('&', 'and')   # same ids as build.py

my = {}
for r in csv.DictReader(open(os.path.join(OUTD, 'model_years.csv'), encoding='utf-8')):
    my[(r['family'], int(r['year']))] = dict(li=int(r['lemon_index']), n=int(r['complaints']), sold=int(r['sold']))

# 10-29 (Elijah's car is a 2008): model years 2000-2009 too, scored exactly like analyze.py does 2010-2022 (same 3-year window, mysales fixes,
# the lower of the calendar and blended index, 20,000+ sold), against the average car of THAT model year. Sales: data/sales_2000.csv
# (sales.py's Wikipedia tables, kept from 2000 instead of 2005). 2010-2022 stay exactly as in model_years.csv.
O0, O1, MIN_SOLD = 2000, 2009, 20000
sales = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(LEMON, 'data', 'sales_2000.csv'), encoding='utf-8')): sales[r['family']][int(r['year'])] = int(r['us_sales'])
for r in csv.DictReader(open(os.path.join(LEMON, 'data', 'sales_manual.csv'), encoding='utf-8')):
    if '-' not in r['year']: sales[r['family']].setdefault(int(r['year']), int(r['us_sales']))
_con = sqlite3.connect(os.path.join(LEMON, 'data', 'complaints.db'))
_pats = [(fam, set(make.split('|')), re.compile(rx)) for fam, make, rx, _, _ in FAMILIES]
# names NHTSA used for these models before 2010 (RX330, E320, "4 RUNNER", WRANGLER 4-DR 4X4 ...). Without them those years look far too good.
OLD_NAMES = {'Jeep Wrangler': r'WRANGLER( SAHARA| [24]-DR 4X[24]( RHD)?| X RHD 4X4)', 'Jeep Compass': r'COMPASS( 4X4| FWD)', 'Jeep Patriot': r'PATRIOT( 4X4| FWD)',
    'GMC Yukon XL': r'YUKON XL DENALI', 'Dodge Durango': r'DURANGO 4X4', 'Dodge Journey': r'JOURNEY AWD', 'Toyota 4Runner': r'4 RUNNER',
    'Lexus RX': r'RX ?(300|330|400H)', 'Lexus ES': r'ES ?(300|330)', 'Ford Mustang': r'MUSTANG (GT|CONVERTIBLE)', 'Chevrolet Malibu': r'MALIBU (MAXX|CLASSIC)',
    'Kia Rio': r'RIO CINCO', 'Subaru Impreza': r'IMPREZA STI', 'Volkswagen Passat': r'PASSAT WAGON', 'Dodge Charger': r'CHARGER AWD', 'Chrysler 300': r'300C|300 AWD',
    'Mercedes-Benz C-Class': r'C CLASS|C ?(230|240|280|320|32|55)( 4MATIC)?', 'Mercedes-Benz E-Class': r'E CLASS|E ?(320|430|500|55)( 4MATIC)?',
    'Mercedes-Benz M/GLE': r'M CLASS|ML ?(320|430|500|55)', 'BMW 3 Series': r'3[234]\d ?IC', 'BMW 5 Series': r'5[345]\dI', 'Chrysler Town & Country': r'TOWN AND COUNTRY LWB',
    'Chrysler Pacifica': r'PACIFICA AWD', 'Kia Sedona': r'SEDONA EX', 'Audi A4': r'A4 CABRIOLET', 'Ford Escape': r'ESCAPE HEV', 'Ford F-Series': r'F SUPER DUTY|F SERIES',
    'Chevrolet Silverado': r'SILVERADO CLASSIC'}
_pats = [(f, mk, re.compile(rx.pattern + ('|' + OLD_NAMES[f] if f in OLD_NAMES else ''))) for f, mk, rx in _pats]
owin = defaultdict(lambda: defaultdict(int))
for make, model, year, ldate in _con.execute(f'SELECT make, model, year, ldate FROM complaints WHERE year BETWEEN {O0} AND {O1}'):
    fam = next((f for f, mk, rx in _pats if make in mk and rx.fullmatch(model)), None)
    if not fam: continue
    year = mysales.code(fam, year)
    if ldate and int(ldate[:4]) <= year + WINDOW: owin[fam][year] += 1
S, B = {}, {}
for f, *_ in _pats:
    S[f], into, _ = mysales.merge(sales[f], owin[f], f, O0, O1); B[f] = mysales.blend(S[f], into, sales[f])
def baseline(D):
    out = {}
    for y in range(O0, O1 + 1):
        fs = [f for f, *_ in _pats if D[f].get(y)]; out[y] = sum(owin[f][y] for f in fs) / sum(D[f][y] for f in fs)
    return out
base, baseB = baseline(S), baseline(B)
for f, *_ in _pats:
    for y in range(O0, O1 + 1):
        s = S[f].get(y)
        if not s or s < MIN_SOLD: continue
        n = owin[f][y]
        my[(f, y)] = dict(li=min(round(100 * n / (s * base[y])), round(100 * n / (B[f][y] * baseB[y]))), n=n, sold=s)
print('2000-2009 model years scored:', sum(1 for k in my if k[1] < 2010))

con = sqlite3.connect(os.path.join(LEMON, 'data', 'complaints.db'))
pats = [(fam, set(make.split('|')), re.compile(rx)) for fam, make, rx, _, _ in FAMILIES]
comp = defaultdict(lambda: defaultdict(int)); tot = defaultdict(int); ids = defaultdict(lambda: defaultdict(list))
for odino, make, model, year, ldate, comps in con.execute(f'SELECT odino, make, model, year, ldate, comps FROM complaints WHERE year BETWEEN {Y0} AND {Y1}'):
    fam = next((f for f, mk, rx in (_pats if year < 2010 else pats) if make in mk and rx.fullmatch(model)), None)
    if fam is None: continue
    year = mysales.code(fam, year)
    if not (ldate and int(ldate[:4]) <= year + WINDOW): continue
    tot[(fam, year)] += 1
    for c in set((comps or '').split(' | ')):
        c = c.split(':')[0].strip() or 'UNKNOWN'
        comp[(fam, year)][c] += 1; ids[(fam, year)][c].append(odino)

BAD = re.compile(r'\d{5,}|@|https?:|www\.|\bVIN\b|\bMY NAME\b|\bMR\.|\bMRS\.|\bMS\.|\bDR\.|\bLLC\b|\bINC\b|\bthanks?\b|thank you|regards|sincerely|call me|contact me|my number|\b(my|our) (wife|husband|son|daughter|kids?|children)\b', re.I)   # no personal details or sign-offs with names
NAMES = sorted({w for f, _, _, _, _ in FAMILIES for w in f.replace('(', ' ').replace(')', ' ').split() if w[:1].isupper() and len(w) > 2} | {'NHTSA', 'BMW', 'VW', 'GM'}, key=len, reverse=True)
def clean(t):
    t = re.sub(r'\s*\*[A-Z]{2,3}\b.*$', '', t.strip())          # NHTSA staff tags (*TR, *JB ...) and anything after them
    t = re.sub(r'\s+', ' ', t).strip()
    if t.isupper() or sum(ch.isupper() for ch in t) > .6 * sum(ch.isalpha() for ch in t):   # sentence case for ALL-CAPS filings
        t = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), t.lower())
        t = re.sub(r'\bi\b', 'I', t)
        for w in NAMES: t = re.sub(r'\b' + re.escape(w.lower()) + r'\b', w, t)   # brand and model names keep their capitals
    return t
def quotes(fam, year, top):
    pool = []
    for c in top:
        for o in ids[(fam, year)][c]: pool.append(o)
    pool = list(dict.fromkeys(pool)); random.Random(f'{fam}{year}').shuffle(pool)
    out, seen = [], set()
    for o in pool[:400]:
        row = con.execute('SELECT descr FROM rows WHERE odino=? AND descr IS NOT NULL LIMIT 1', (o,)).fetchone()
        if not row: continue
        t = clean(row[0])
        if not (50 <= len(t) <= 230) or BAD.search(t) or t[:40] in seen: continue
        seen.add(t[:40]); out.append({'odi': o, 'text': t})
        if len(out) == 3: break
    return out

data = []
for fam, _, _ in pats:
    yrs = []
    for y in range(Y0, Y1 + 1):
        m = my.get((fam, y))
        if not m: continue
        cs = [(c, k) for c, k in sorted(comp[(fam, y)].items(), key=lambda x: -x[1]) if c not in ('UNKNOWN OR OTHER', 'UNKNOWN')]
        n = tot[(fam, y)] or 1
        parts = [[part(c), round(100 * k / n)] for c, k in cs[:5]]
        yrs.append(dict(y=y, li=m['li'], n=m['n'], sold=m['sold'], parts=parts, quotes=quotes(fam, y, [c for c, _ in cs[:2]])))
    if yrs: data.append(dict(id=idof(fam), name=fam, years=yrs))
os.makedirs('data', exist_ok=True)
json.dump(data, open('data/years.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(data), 'families,', sum(len(d['years']) for d in data), 'model years,', sum(len(y['quotes']) for d in data for y in d['years']), 'quotes ->', 'data/years.json')
