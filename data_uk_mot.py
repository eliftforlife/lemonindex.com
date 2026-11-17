"""UK MOT pass rates, stage 2 (growth plan 3B-2, 11-15): raw DVSA aggregates -> data/uk_mot.json.

Stage 1 (3 Lemon Index/uk/mot_extract.py) reads DVSA's zipped "Anonymised MOT tests and results" (2024 tests,
Open Government Licence v3.0) and writes counts per RAW make + model name + year of first use. This script:
  1. cleans the model names (UK_MAP below: MINI/COOPER/ONE -> MINI Hatch, BMW 320D/3 SERIES -> 3 Series,
     Mercedes C220/C-CLASS/C -> C-Class, Transit Custom kept apart from Transit, trim words dropped ...)
  2. splits vans, pickups and van-based people carriers (VANS) from cars
  3. scores each make + model + year of first use with >= MIN_TESTS tests: first-time pass rate = P / (P + F + PRS)
     (DVSA's "initial failure rate" turned around; PRS counts as a fail because the car arrived failing), against the
     same-age average (every car, or every van, first registered that year, all models)
  4. failure areas and items (share of tests with at least one fail/PRS item there) vs the same-age share,
     dangerous-defect share and average mileage at the test.

Usage: py -I data_uk_mot.py [raw.pkl] [out.json]
"""
import sys, os, re, json, pickle, math, time
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\uk\data', 'mot_raw_2024.pkl')
OUT = os.path.join(HERE, 'data', 'uk_mot.json')
TEST_YEAR = 2024
FY_MIN, FY_MAX = 2004, 2021        # first registered 2004-2021 = 3 to 20 years old at a 2024 test
MIN_TESTS = 1000                   # tests a make + model + year needs before it gets a score
HUB_MIN = 10000                    # tests (in scored years) before a model is listed on the hub
PAGES = 100                        # pages for the top models by tests ...
PAGES_ALSO = [('TOYOTA', 'Avensis')]   # ... plus these (a viewer asked about the Avensis)

# ---------------------------------------------------------------- makes
MAKE_FIX = {'MERCEDES': 'MERCEDES-BENZ', 'MERCEDES BENZ': 'MERCEDES-BENZ', 'VW': 'VOLKSWAGEN', 'LANDROVER': 'LAND ROVER',
            'ROLLS ROYCE': 'ROLLS-ROYCE', 'ALFA': 'ALFA ROMEO', 'CITROËN': 'CITROEN', 'DS AUTOMOBILES': 'DS', 'MG MOTOR UK': 'MG',
            'MG-MOTOR UK': 'MG', 'SSANGYONG MOTOR': 'SSANGYONG', 'IVECO-FORD': 'IVECO'}
MAKE_NAME = {'BMW': 'BMW', 'MINI': 'MINI', 'MG': 'MG', 'DS': 'DS', 'LAND ROVER': 'Land Rover', 'MERCEDES-BENZ': 'Mercedes-Benz',
             'ALFA ROMEO': 'Alfa Romeo', 'SSANGYONG': 'SsangYong', 'LDV': 'LDV', 'SEAT': 'SEAT', 'CUPRA': 'Cupra', 'KIA': 'Kia',
             'ROLLS-ROYCE': 'Rolls-Royce', 'ASTON MARTIN': 'Aston Martin', 'LEXUS': 'Lexus', 'JAGUAR': 'Jaguar'}

# ---------------------------------------------------------------- models
# Model names that need more than their first word (checked against the merged-name lists in uk_mot.json)
MULTI = re.compile(
    r'^(RANGE ROVER (EVOQUE|SPORT|VELAR)|RANGE ROVER|LAND CRUISER|DISCOVERY SPORT|GRAND C4 PICASSO|GRAND C4 SPACETOURER|C4 PICASSO|'
    r'C4 SPACETOURER|C3 PICASSO|C4 CACTUS|C3 AIRCROSS|C5 AIRCROSS|C4 X|GOLF PLUS|GOLF SV|PRIUS PLUS|MODEL [3SXY]|SPACE STAR|GRAND VITARA|'
    r'GRAND SCENIC|GRAND MODUS|ZAFIRA TOURER|ZAFIRA LIFE|GRANDLAND|CROSSLAND|DEFENDER|ID\.? ?\d|GRAND C-MAX|IONIQ ?\d|'
    r'TRANSIT CUSTOM|TRANSIT CONNECT|TRANSIT COURIER|TOURNEO CUSTOM|TOURNEO CONNECT|TOURNEO COURIER|GRAND TOURNEO|'
    r'PROACE CITY|PROACE VERSO|PARTNER TEPEE|BERLINGO MULTISPACE|E-NV200|NV200|NV250|NV300|NV400|COMBO LIFE|'
    r'SANTA FE|LAND CRUISER|YARIS CROSS|COROLLA VERSO|AURIS TOURING|GOLF ESTATE|POLO ESTATE|QASHQAI\+2|NEW BEETLE|'
    r'GRAND CHEROKEE|ALHAMBRA|XSARA PICASSO|SCENIC XMOD|MX-5|MX-30|CX-\d+|RX-8|CR-V|HR-V|ZR-V|C-HR|E-PACE|F-PACE|I-PACE|F-TYPE|'
    r'S-MAX|C-MAX|B-MAX|KA\+|UP!?|E-UP!?|T-ROC|T-CROSS|TAIGO|SX4 S-CROSS|S-CROSS|IONIQ|KONA|NIRO|E-NIRO|SOUL|XCEED|PRO[_ ]?CEED|CEED)\b')

BMW_SERIES = re.compile(r'^(?:([1-8]) ?SERIES|([1-8])\d\d ?[A-Z]*|M([1-8])(?:\b|\d\d).*)')
MB_CLASS = re.compile(r'^(EQA|EQB|EQC|EQE|EQS|EQV|CLA|CLS|CLK|CLC|GLA|GLB|GLC|GLE|GLK|GLS|SLK|SLC|SL|ML|GL|A|B|C|E|S|G|V|X)(?:[ -]?CLASS\b|[ -]?\d{2,3}\b|\b)')
MB_VANS = re.compile(r'^(SPRINTER|VITO|CITAN|VIANO)\b')
MINI_RE = [('COUNTRYMAN', 'Countryman'), ('CLUBMAN', 'Clubman'), ('PACEMAN', 'Paceman'), ('CONVERTIBLE', 'Convertible'), ('CABRIO', 'Convertible'),
           ('ROADSTER', 'Roadster'), ('COUPE', 'Coupe')]
ALIAS = {   # (make, base) -> display base (merging spellings)
    ('VAUXHALL', 'GRANDLAND'): 'GRANDLAND', ('VAUXHALL', 'CROSSLAND'): 'CROSSLAND', ('VAUXHALL', 'MOKKA'): 'MOKKA',
    ('TOYOTA', 'CHR'): 'C-HR', ('HONDA', 'CRV'): 'CR-V', ('HONDA', 'HRV'): 'HR-V', ('VOLKSWAGEN', 'UP!'): 'UP', ('VOLKSWAGEN', 'E-UP!'): 'E-UP',
    ('VOLKSWAGEN', 'E-UP'): 'UP', ('KIA', 'PRO_CEED'): 'PROCEED', ('KIA', 'PRO CEED'): 'PROCEED', ('KIA', 'PROCEED'): 'PROCEED',
    ('KIA', 'CEE\'D'): 'CEED', ('KIA', 'E-NIRO'): 'NIRO', ('HYUNDAI', 'IONIQ5'): 'IONIQ 5', ('HYUNDAI', 'IONIQ6'): 'IONIQ 6',
    ('CITROEN', 'BERLINGO MULTISPACE'): 'BERLINGO', ('PEUGEOT', 'PARTNER TEPEE'): 'PARTNER', ('NISSAN', 'E-NV200'): 'NV200',
    ('NISSAN', 'QASHQAI+2'): 'QASHQAI', ('VAUXHALL', 'COMBO LIFE'): 'COMBO', ('FORD', 'GRAND TOURNEO'): 'TOURNEO CONNECT',
    ('SUZUKI', 'SX4 S-CROSS'): 'S-CROSS', ('LAND ROVER', 'DEFENDER'): 'DEFENDER', ('VOLKSWAGEN', 'GOLF ESTATE'): 'GOLF',
    ('VOLKSWAGEN', 'POLO ESTATE'): 'POLO', ('TOYOTA', 'AURIS TOURING'): 'AURIS', ('FORD', 'KA+'): 'KA+',
}


# raw-name fixes before the first-word rule (abbreviations DVSA's vehicle records use, and names whose first word is another model)
PRE = [(r'\bSPRT\b', 'SPORT'), (r'^DISCOVERY SPT\b', 'DISCOVERY SPORT'), (r'^TRANSIT CUST\b\S*', 'TRANSIT CUSTOM'), (r'^TOURNEO CUST\b\S*', 'TOURNEO CUSTOM'),
       (r'^TRANSIT CONN?\b(?!ECT)', 'TRANSIT CONNECT'), (r'^KA ?\+|^KA PLUS\b', 'KA+'), (r'^PRIUS ?\+|^PRIUS PLUS\b', 'PRIUS+'), (r'^FOCUS C-MAX\b', 'C-MAX'),
       (r'^MEGANE SCENIC\b', 'SCENIC'), (r'^GRAND SCENIC\b', 'GRAND SCENIC'), (r'^C4 (GRAND|GR) (PICASSO|S ?TOURER|SPACETOURER|SPACE TOURER)\b', 'GRAND C4 PICASSO'),
       (r'^GRAND C4 (S ?TOURER|SPACETOURER|SPACE TOURER)\b', 'GRAND C4 PICASSO'), (r'^C4 (S ?TOURER|SPACETOURER|SPACE TOURER)\b', 'C4 PICASSO'),
       (r'^500 ?L\b', '500L'), (r'^500 ?X\b', '500X'), (r'^AMG ', '')]
MINI_CODE = {'R60': 'COUNTRYMAN', 'F60': 'COUNTRYMAN', 'R55': 'CLUBMAN', 'F54': 'CLUBMAN', 'R61': 'PACEMAN', 'R57': 'CONVERTIBLE', 'F57': 'CONVERTIBLE',
             'R58': 'COUPE', 'R59': 'ROADSTER'}


def canon(mk, md):
    """raw DVSA make + model -> (make, model) or None. Model is upper case, display-cased later by model_name()."""
    mk = MAKE_FIX.get(mk, mk)
    md = md.replace('-BENZ ', '').strip()
    for pat, rep in PRE: md = re.sub(pat, rep, md)
    md = md.strip()
    if mk == 'MINI' or (mk == 'BMW' and md.startswith('MINI')):
        for k, v in MINI_CODE.items():
            if re.search(rf'\b{k}\b', md): return 'MINI', v
        for k, v in MINI_RE:
            if k in md: return 'MINI', v.upper()
        return 'MINI', 'HATCH'
    if mk == 'BMW':
        if md.startswith(('X', 'Z', 'I')):
            m = re.match(r'^(X[1-7]|Z[348]|I[3-8X]\d?|IX\d?)\b', md)
            return ('BMW', m.group(1)) if m else None
        m = BMW_SERIES.match(md)
        if m: return 'BMW', f'{m.group(1) or m.group(2) or m.group(3)} SERIES'
        return None
    if mk == 'MERCEDES-BENZ':
        m = MB_VANS.match(md)
        if m: return mk, m.group(1)
        m = MB_CLASS.match(md)
        if m:
            c = m.group(1)
            return mk, (f'{c}-CLASS' if len(c) == 1 else c)
        return None
    if mk == 'CITROEN' and re.match(r'^DS ?([345])\b', md): return mk, 'DS' + re.match(r'^DS ?([345])', md).group(1)
    if mk == 'DS' and re.match(r'^DS ?(\d)', md): return mk, 'DS ' + re.match(r'^DS ?(\d)', md).group(1)
    hit = MULTI.match(md)
    b = hit.group(0).strip() if hit else md.split(' ')[0]
    b = re.sub(r'\s+', ' ', b)
    if mk == 'VAUXHALL' and b.startswith(('GRANDLAND', 'CROSSLAND')): b = b.split()[0]
    if mk == 'HYUNDAI' and re.match(r'^IONIQ ?\d', b): b = 'IONIQ ' + b[-1]
    if re.match(r'^ID\.? ?\d', b): b = 'ID.' + b[-1]
    return mk, ALIAS.get((mk, b), b)


# vans, pickups and van-based people carriers: compared with each other, not with cars
VANS = {('FORD', 'TRANSIT'), ('FORD', 'TRANSIT CUSTOM'), ('FORD', 'TRANSIT CONNECT'), ('FORD', 'TRANSIT COURIER'), ('FORD', 'TOURNEO CUSTOM'),
        ('FORD', 'TOURNEO CONNECT'), ('FORD', 'TOURNEO COURIER'), ('FORD', 'RANGER'), ('VOLKSWAGEN', 'TRANSPORTER'), ('VOLKSWAGEN', 'CADDY'),
        ('VOLKSWAGEN', 'CRAFTER'), ('VOLKSWAGEN', 'AMAROK'), ('VOLKSWAGEN', 'CARAVELLE'), ('VOLKSWAGEN', 'CALIFORNIA'), ('VOLKSWAGEN', 'SHARAN_X'),
        ('VAUXHALL', 'VIVARO'), ('VAUXHALL', 'COMBO'), ('VAUXHALL', 'MOVANO'), ('CITROEN', 'BERLINGO'), ('CITROEN', 'DISPATCH'), ('CITROEN', 'RELAY'),
        ('CITROEN', 'NEMO'), ('CITROEN', 'SPACETOURER'), ('PEUGEOT', 'PARTNER'), ('PEUGEOT', 'EXPERT'), ('PEUGEOT', 'BOXER'), ('PEUGEOT', 'BIPPER'),
        ('PEUGEOT', 'RIFTER'), ('PEUGEOT', 'TRAVELLER'), ('RENAULT', 'TRAFIC'), ('RENAULT', 'KANGOO'), ('RENAULT', 'MASTER'),
        ('MERCEDES-BENZ', 'VITO'), ('MERCEDES-BENZ', 'SPRINTER'), ('MERCEDES-BENZ', 'CITAN'), ('MERCEDES-BENZ', 'VIANO'), ('MERCEDES-BENZ', 'X-CLASS'),
        ('FIAT', 'DOBLO'), ('FIAT', 'DUCATO'), ('FIAT', 'FIORINO'), ('FIAT', 'TALENTO'), ('FIAT', 'SCUDO'), ('FIAT', 'QUBO'), ('FIAT', 'FULLBACK'),
        ('NISSAN', 'NV200'), ('NISSAN', 'NV250'), ('NISSAN', 'NV300'), ('NISSAN', 'NV400'), ('NISSAN', 'PRIMASTAR'), ('NISSAN', 'NAVARA'),
        ('NISSAN', 'INTERSTAR'), ('TOYOTA', 'PROACE'), ('TOYOTA', 'PROACE CITY'), ('TOYOTA', 'PROACE VERSO'), ('TOYOTA', 'HILUX'),
        ('MITSUBISHI', 'L200'), ('ISUZU', 'D-MAX'), ('ISUZU', 'RODEO'), ('IVECO', 'DAILY'), ('LDV', 'V80'), ('SSANGYONG', 'MUSSO'),
        ('VAUXHALL', 'ZAFIRA LIFE'), ('OPEL', 'VIVARO')}

# display names (anything not listed: title case)
NAME = {'CR-V': 'CR-V', 'HR-V': 'HR-V', 'ZR-V': 'ZR-V', 'C-HR': 'C-HR', 'CX-3': 'CX-3', 'CX-5': 'CX-5', 'CX-30': 'CX-30', 'CX-60': 'CX-60',
        'MX-5': 'MX-5', 'RX-8': 'RX-8', 'S-MAX': 'S-MAX', 'C-MAX': 'C-MAX', 'B-MAX': 'B-MAX', 'GRAND C-MAX': 'Grand C-MAX', 'KA+': 'Ka+',
        'UP': 'up!', 'T-ROC': 'T-Roc', 'T-CROSS': 'T-Cross', 'ID.3': 'ID.3', 'ID.4': 'ID.4', 'ID.5': 'ID.5', 'I10': 'i10', 'I20': 'i20', 'I30': 'i30',
        'I40': 'i40', 'IX20': 'ix20', 'IX35': 'ix35', 'X1': 'X1', 'X2': 'X2', 'X3': 'X3', 'X4': 'X4', 'X5': 'X5', 'X6': 'X6', 'X7': 'X7', 'Z4': 'Z4',
        'I3': 'i3', 'IX': 'iX', 'GLA': 'GLA', 'GLB': 'GLB', 'GLC': 'GLC', 'GLE': 'GLE', 'GLK': 'GLK', 'GLS': 'GLS', 'CLA': 'CLA', 'CLS': 'CLS',
        'CLK': 'CLK', 'SLK': 'SLK', 'SLC': 'SLC', 'ML': 'M-Class (ML)', 'GL': 'GL', 'SL': 'SL', 'A1': 'A1', 'A3': 'A3', 'A4': 'A4', 'A5': 'A5',
        'A6': 'A6', 'A7': 'A7', 'A8': 'A8', 'Q2': 'Q2', 'Q3': 'Q3', 'Q5': 'Q5', 'Q7': 'Q7', 'Q8': 'Q8', 'TT': 'TT', 'XC40': 'XC40', 'XC60': 'XC60',
        'XC90': 'XC90', 'V40': 'V40', 'V60': 'V60', 'V70': 'V70', 'V90': 'V90', 'S60': 'S60', 'S80': 'S80', 'S90': 'S90', 'XE': 'XE', 'XF': 'XF',
        'XJ': 'XJ', 'E-PACE': 'E-Pace', 'F-PACE': 'F-Pace', 'I-PACE': 'I-Pace', 'F-TYPE': 'F-Type', 'DS3': 'DS3', 'DS4': 'DS4', 'DS5': 'DS5',
        'C1': 'C1', 'C3': 'C3', 'C4': 'C4', 'C5': 'C5', 'DS 3': 'DS 3', 'DS 4': 'DS 4', 'DS 7': 'DS 7', 'L200': 'L200', 'D-MAX': 'D-Max',
        'NV200': 'NV200', 'NV300': 'NV300', 'NV400': 'NV400', 'MODEL 3': 'Model 3', 'MODEL S': 'Model S', 'MODEL X': 'Model X',
        'MODEL Y': 'Model Y', 'RAV4': 'RAV4', 'IQ': 'iQ', 'GT86': 'GT86', 'MX-30': 'MX-30', 'SX4': 'SX4', 'S-CROSS': 'S-Cross', 'ZS': 'ZS',
        'HS': 'HS', 'MG3': 'MG3', 'MG4': 'MG4', 'MG5': 'MG5', 'GS': 'GS', 'IS': 'IS', 'NX': 'NX', 'RX': 'RX', 'CT': 'CT', 'UX': 'UX', 'ES': 'ES',
        'XCEED': 'XCeed', 'PROCEED': 'ProCeed', 'CEED': 'Ceed', 'E-NIRO': 'e-Niro', 'IONIQ': 'Ioniq', 'IONIQ 5': 'Ioniq 5', 'HATCH': 'Hatch',
        'DS5_': 'DS5', '500X': '500X', '500L': '500L', '595': '595', '124': '124', 'CR-Z': 'CR-Z', 'FR-V': 'FR-V', 'ASX': 'ASX', 'ECOSPORT': 'EcoSport', 'PRIUS+': 'Prius+', 'GRAND C4 PICASSO': 'Grand C4 Picasso', 'EQA': 'EQA', 'EQB': 'EQB', 'EQC': 'EQC', 'EQE': 'EQE', 'EQS': 'EQS', 'EQV': 'EQV', 'IX3': 'iX3', 'I4': 'i4', 'I8': 'i8', 'X-CLASS': 'X-Class'}


def model_name(mk, md):
    if md in NAME: return NAME[md]
    if re.fullmatch(r'\d SERIES', md): return md[0] + ' Series'
    if md.endswith('-CLASS'): return md[0] + '-Class'
    return ' '.join(w if re.search(r'\d', w) and len(w) <= 4 else '-'.join(p.capitalize() for p in w.split('-')) for w in md.split(' '))


def make_name(mk): return MAKE_NAME.get(mk, mk.title())


def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower().replace('+', ' plus').replace('!', '')).strip('-')


# ---------------------------------------------------------------- plain-English names
AREA = {'Lamps, reflectors and electrical equipment': 'Lights and electrics', 'Lamps, Reflectors and Electrical Equipment': 'Lights and electrics',
        'Suspension': 'Suspension', 'Tyres': 'Tyres', 'Brakes': 'Brakes', 'Brake performance': 'Brakes',
        'Visibility': 'Windscreen, wipers and mirrors', "Driver's View of the Road": 'Windscreen, wipers and mirrors', 'Steering': 'Steering',
        'Body, chassis, structure': 'Body, chassis and underside', 'Body, Structure and General Items': 'Body, chassis and underside',
        'Noise, emissions and leaks': 'Emissions, noise and leaks', 'Exhaust, Fuel and Emissions': 'Emissions, noise and leaks',
        'Seat belts and supplementary restraint systems': 'Seat belts and airbags', 'Seat Belts and Supplementary Restraint Systems': 'Seat belts and airbags',
        'Seat belt installation check': 'Seat belts and airbags', 'Road Wheels': 'Wheels', 'Registration Plates and VIN': 'Number plates and VIN',
        'Identification of the vehicle': 'Number plates and VIN', 'Speedometer and speed limiter': 'Speedometer and controls',
        'Driving Controls and Speed Limiters': 'Speedometer and controls', 'Towbars': 'Towbar'}


def main(raw=RAW, out=OUT):
    t0 = time.time()
    R = pickle.load(open(raw, 'rb'))   # our own stage-1 output (mot_extract.py on this PC), not downloaded data
    keys, cnt, msum, mcount = R['keys'], R['cnt'], R['msum'], R['mcount']
    areas = R['areas']; gA = R['area_tests']; dang = R['dangerous']
    K = len(keys)
    # raw key -> canonical group
    cmap = np.full(K, -1, dtype=np.int64); groups = {}; gkey = []; merged = defaultdict(lambda: defaultdict(int)); dropped = defaultdict(int)
    fy = np.array([int(k[2]) for k in keys])
    for i, (mk, md, y) in enumerate(keys):
        y = int(y)
        if y < FY_MIN or y > FY_MAX: continue
        c = canon(mk, md)
        if not c: dropped[f'{mk}|{md}'] += int(cnt[i].sum()); continue
        g = (c[0], c[1], y)
        if g not in groups: groups[g] = len(groups); gkey.append(g)
        cmap[i] = groups[g]; merged[c][md] += int(cnt[i].sum())
    G = len(groups); ok = cmap >= 0
    def gsum(arr):
        o = np.zeros((G,) + arr.shape[1:], dtype=np.float64)
        np.add.at(o, cmap[ok], arr[ok]); return o
    C = gsum(cnt); MS = gsum(msum); MC = gsum(mcount); GA = gsum(gA); DG = gsum(dang)
    # rfr per group
    rk = R['rfr_key']; rg = cmap[rk]; m_ = rg >= 0
    RF = defaultdict(lambda: defaultdict(int))
    for g, r, n in zip(rg[m_], R['rfr_id'][m_], R['rfr_n'][m_]): RF[int(g)][int(r)] += int(n)
    # area merge: raw area index -> plain name (a test can only be counted once per raw area; two raw areas that map to the
    # same plain name are combined with max(), a lower bound, so nothing is double counted)
    pa = sorted(set(AREA.get(a, 'Other') for a in areas))
    def plain_areas(row):
        d = defaultdict(float)
        for j, a in enumerate(areas):
            p = AREA.get(a, 'Other'); d[p] = max(d[p], row[j])
        return d
    kind = lambda c: 'van' if (c[0], c[1]) in VANS else 'car'
    # same-age averages per kind + year of first use (every scored make/model, any size)
    base = defaultdict(lambda: {'n': 0, 'p': 0, 'ms': 0.0, 'mc': 0.0, 'a': defaultdict(float), 'r': defaultdict(int), 'd': 0})
    for gi, (mk, md, y) in enumerate(gkey):
        b = base[(kind((mk, md)), y)]; n = C[gi].sum()
        b['n'] += n; b['p'] += C[gi][0]; b['ms'] += MS[gi]; b['mc'] += MC[gi]; b['d'] += DG[gi]
        for a, v in plain_areas(GA[gi]).items(): b['a'][a] += v
        for r, v in RF[gi].items(): b['r'][r] += v
    det = R['rfr_detail']; iname = R['item_names']
    def item_raw(r):
        t, s_, d, cat = det.get(r, ('', '', str(r), ''))
        return (iname.get(t, '') + ': ' + d).strip(': '), cat
    # model level
    M = defaultdict(list)
    for gi, (mk, md, y) in enumerate(gkey): M[(mk, md)].append(gi)
    models = []
    for (mk, md), gis in M.items():
        k = kind((mk, md))
        yrs = [gi for gi in gis if C[gi].sum() >= MIN_TESTS]
        if not yrs: continue
        n = sum(C[gi].sum() for gi in yrs)
        if n < HUB_MIN: continue
        rows = []
        exp_p = exp_m = 0.0; ea = defaultdict(float); er = defaultdict(float); ed = 0.0
        for gi in sorted(yrs, key=lambda g: gkey[g][2]):
            y = gkey[gi][2]; b = base[(k, y)]; ny = C[gi].sum(); py = C[gi][0] / ny; by = b['p'] / b['n']
            se = math.sqrt(py * (1 - py) / ny)
            mil = MS[gi] / MC[gi] if MC[gi] else None; bmil = b['ms'] / b['mc'] if b['mc'] else None
            rows.append({'y': y, 'n': int(ny), 'pass': round(py, 4), 'avg': round(by, 4), 'diff': round((py - by) * 100, 1), 'se': round(se * 100, 2),
                         'miles': round(mil) if mil else None, 'avg_miles': round(bmil) if bmil else None,
                         'fail': int(C[gi][1]), 'prs': int(C[gi][2])})
            exp_p += ny * by; exp_m += ny * (bmil or 0); ed += ny * b['d'] / b['n']
            for a, v in b['a'].items(): ea[a] += ny * v / b['n']
            for r, v in b['r'].items(): er[r] += ny * v / b['n']
        P = sum(C[gi][0] for gi in yrs); msn = sum(MS[gi] for gi in yrs); mcn = sum(MC[gi] for gi in yrs)
        ar = defaultdict(float)
        for gi in yrs:
            for a, v in plain_areas(GA[gi]).items(): ar[a] += v
        rf = defaultdict(int)
        for gi in yrs:
            for r, v in RF[gi].items(): rf[r] += v
        top_items = []
        for r, v in sorted(rf.items(), key=lambda kv: -kv[1])[:10]:
            raw_, cat = item_raw(r)
            top_items.append({'rfr': r, 'raw': raw_, 'cat': cat, 'n': int(v), 'share': round(v / n, 4), 'exp': round(er.get(r, 0) / n, 4)})
        mn = make_name(mk); dn = model_name(mk, md)
        models.append({
            'id': slug(f'{mn} {dn}'), 'make': mk, 'model': md, 'make_name': mn, 'model_name': dn, 'name': f'{mn} {dn}', 'kind': k,
            'tests': int(n), 'pass': round(P / n, 4), 'exp': round(exp_p / n, 4), 'diff': round((P - exp_p) / n * 100, 1),
            'miles': round(msn / mcn) if mcn else None, 'exp_miles': round(exp_m / n) if exp_m else None,
            'dangerous': round(sum(DG[gi] for gi in yrs) / n, 4), 'exp_dangerous': round(ed / n, 4),
            'years': rows,
            'areas': sorted(({'a': a, 'n': int(v), 'share': round(v / n, 4), 'exp': round(ea.get(a, 0) / n, 4)} for a, v in ar.items() if a != 'Other' and v),
                            key=lambda x: -x['share']),
            'items': top_items,
            'names': dict(sorted(merged[(mk, md)].items(), key=lambda kv: -kv[1])[:12]),
            'all_years': {str(gkey[gi][2]): int(C[gi].sum()) for gi in sorted(gis, key=lambda g: gkey[g][2])},
        })
    models.sort(key=lambda m: -m['tests'])
    for i, m in enumerate(models, 1): m['rank_tests'] = i
    pages = {m['id'] for m in models[:PAGES]} | {m['id'] for m in models if (m['make'], m['model_name']) in PAGES_ALSO}
    # ... and every model the /uk/ hub names in its best / worst lists (cars 50,000+ tests top and bottom 10, vans 30,000+ top and bottom 5)
    pc = [m for m in models if m['kind'] == 'car' and m['tests'] >= 50000]; pv = [m for m in models if m['kind'] == 'van' and m['tests'] >= 30000]
    for grp_, k in ((pc, 10), (pv, 5)):
        o = sorted(grp_, key=lambda m: m['diff']); pages |= {m['id'] for m in o[:k] + o[-k:]}
    for m in models: m['page'] = m['id'] in pages
    avg = {k: {str(y): {'n': int(b['n']), 'pass': round(b['p'] / b['n'], 4), 'miles': round(b['ms'] / b['mc']) if b['mc'] else None,
                        'dangerous': round(b['d'] / b['n'], 4), 'areas': {a: round(v / b['n'], 4) for a, v in sorted(b['a'].items()) if a != 'Other'}}
               for (kk, y), b in sorted(base.items()) if kk == k}
           for k in ('car', 'van')}
    totn = sum(b['n'] for b in base.values()); totp = sum(b['p'] for b in base.values())
    meta = {
        'source': 'DVSA, "Anonymised MOT tests and results", 2024 test files (open.data.dvsa.gov.uk / data.gov.uk)',
        'licence': 'Open Government Licence v3.0', 'licence_url': 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
        'attribution': 'Contains public sector information licensed under the Open Government Licence v3.0. Source: DVSA anonymised MOT tests and results.',
        'test_year': TEST_YEAR, 'fy_min': FY_MIN, 'fy_max': FY_MAX, 'min_tests': MIN_TESTS, 'hub_min': HUB_MIN,
        'method': ('Class 4 (cars and light vans) normal MOT tests carried out in 2024 with result pass, fail or PRS (passed after a repair '
                   'within an hour), one row per test. First-time pass rate = passes / all those tests (DVSA\'s initial failure rate, turned '
                   'around). Grouped by make + model (trim and engine names merged) + year of first registration, 2004-2021. A year needs '
                   f'{MIN_TESTS:,}+ tests. Same-age average = every car (or every van) first registered that year. Failure areas and items = share '
                   'of tests with at least one fail or PRS defect there.'),
        'tests_in_scope': int(totn), 'pass_in_scope': round(totp / totn, 4), 'models': len(models), 'pages': len(pages),
        'raw': R['meta'], 'built': time.strftime('%Y-%m-%d'),
        'dropped_top': dict(sorted(dropped.items(), key=lambda kv: -kv[1])[:40]),
    }
    json.dump({'meta': meta, 'avg': avg, 'models': models}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'{len(models)} models on the hub, {len(pages)} pages, {totn:,} tests in scope -> {out} ({time.time()-t0:.0f}s)')


if __name__ == '__main__':
    main(*sys.argv[1:3])
