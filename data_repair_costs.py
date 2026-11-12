# 11-12 (UX test: Marcus, Jess and Linda opened "Repairs & costs" and found no real costs). Builds data/repair_costs.json:
#   c: repair bills owners name in their own complaints to NHTSA ("the dealer quoted $3,800 to replace the transmission"), per model year,
#      sorted into a repair area by the words around the dollar figure. Purchase prices, payments, rentals, warranties, lawsuits and
#      amounts under $50 or over $15,000 are left out. One number per complaint and area (the biggest one it names: the bill, not the
#      diagnosis fee). Every number keeps its complaint id (ODI number) so anyone can check it at nhtsa.gov.
#   t: "what to ask the shop": the automaker's own notes to dealers (NHTSA manufacturer communications) that announce a software update,
#      a special coverage / extended warranty, or a CVT / oil-consumption fix, per model year, with the bulletin id.
# repair_costs.py turns it into the cost block on each year page (5+ complaints per area, or it says "not enough reports yet").
#   usage: py -X utf8 data_repair_costs.py      (needs 3 Lemon Index/data/complaints.db and data/raw_more/MFR_COMMS_RECEIVED_*.zip)
import csv, glob, io, json, os, re, sqlite3, sys, zipfile, collections
sys.stdout.reconfigure(encoding='utf-8'); csv.field_size_limit(10 ** 8)
HERE = os.path.dirname(os.path.abspath(__file__))
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
LOCAL = json.load(open(os.path.join(HERE, 'data', 'extras_local.json'), encoding='utf-8'))
YEARS = json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8'))
norm = lambda s: re.sub(r'[^A-Z0-9]', '', (s or '').upper())

def names(fid, y):
    e = LOCAL.get(fid, {}).get(str(y)) or {}; tot = sum(n for *_, n in e.get('names', [])) or 1
    return [(mk, md) for mk, md, n in e.get('names', []) if n / tot >= .05][:3]

WANT = collections.defaultdict(set)   # (make, model normalized, year) -> {fid}
for f in YEARS:
    for v in f['years']:
        for mk, md in names(f['id'], v['y']): WANT[(mk, norm(md), v['y'])].add(f['id'])

# repair areas, matched in the words around a dollar figure (nearest match wins)
AREA = [
    ('Transmission', r'TRANSMISSION|TRANSAXLE|\bTRANS\b|GEARBOX|\bCVT\b|TORQUE CONVERTER|VALVE BODY|\bTCM\b|SHIFT(ER)? (MODULE|CABLE)|CLUTCH|MECHATRONIC'),
    ('Engine', r'ENGINE|\bMOTOR\b(?! MOUNT)|HEAD GASKET|PISTON|TIMING (CHAIN|BELT)|CAMSHAFT|CRANKSHAFT|OIL CONSUMPTION|LIFTER|CYLINDER|TURBO'),
    ('Fuel system', r'FUEL PUMP|INJECTOR|FUEL SYSTEM|FUEL TANK|FUEL LINE'),
    ('Electrical', r'\bTIPM\b|\bBCM\b|BODY CONTROL|ALTERNATOR|BATTERY|STARTER|WIRING|HARNESS|FUSE|MODULE|\bPCM\b|\bECM\b|COMPUTER'),
    ('Brakes', r'BRAKE|ROTOR|CALIPER|\bABS\b|MASTER CYLINDER'),
    ('Steering', r'STEERING|\bEPS\b|STEERING RACK|TIE ROD|COLUMN'),
    ('Suspension', r'SUSPENSION|AIR RIDE|STRUT|SHOCK|CONTROL ARM|BALL JOINT|SWAY BAR|BUSHING'),
    ('A/C & heat', r'\bA/?C\b|AIR CONDITION|COMPRESSOR|HEATER CORE|BLEND DOOR|HVAC|CONDENSER|EVAPORATOR'),
    ('Cooling', r'WATER PUMP|RADIATOR|THERMOSTAT|COOLANT|OVERHEAT'),
    ('4x4 & axles', r'TRANSFER CASE|DIFFERENTIAL|DRIVESHAFT|DRIVE SHAFT|\bAXLE|CV (JOINT|AXLE)|WHEEL BEARING|HUB'),
    ('Exhaust & emissions', r'CATALYTIC|\bEGR\b|EXHAUST|\bDPF\b|EMISSION|OXYGEN SENSOR|\bO2 SENSOR|EVAP'),
    ('Screen, radio & camera', r'RADIO|SCREEN|UCONNECT|SYNC|INFOTAINMENT|DISPLAY|CAMERA|NAVIGATION'),
    ('Airbags', r'AIR ?BAG|CLOCK ?SPRING|\bSRS\b'),
    ('Doors, locks & windows', r'WINDOW REGULATOR|DOOR LOCK|LOCK ACTUATOR|LIFTGATE|TAILGATE|LATCH|SUNROOF'),
    ('Hybrid / EV battery', r'HYBRID BATTERY|HIGH VOLTAGE|TRACTION BATTERY|BATTERY PACK|INVERTER'),
]
AREA = [(n, re.compile(rx)) for n, rx in AREA]
MONEY = re.compile(r'\$\s?(\d{1,3}(?:,\d{3})+|\d{2,6})(?:\.\d\d)?(?!\d)|(?<![\d,.])(\d{1,3}(?:,\d{3})+|\d{3,5})\s?DOLLARS')
COSTW = re.compile(r'COST|CHARG|QUOTE|ESTIMAT|\bPAID\b|\bPAY\b|\bPAYING\b|REPAIR|REPLAC|\bFIX|BILL|INVOICE|OUT OF (MY )?POCKET|SPENT|SPEND|\bLABOR\b|\bPARTS?\b')
NOTREP = re.compile(r'PURCHAS|BOUGHT|\bBUY\b|MSRP|STICKER|\bSOLD\b|SELL|PRICE OF THE|PAYMENT|LOAN|FINANC|LEASE|EXTENDED WARRANTY|SERVICE CONTRACT|WARRANTY (PLAN|POLICY|COVERAGE COST)|'
                    r'RENTAL|RENT A|PER DAY|A DAY|/DAY|A MONTH|PER MONTH|/MONTH|MONTHLY|TRADE|TRADED|\bVALUE\b|KBB|BLUE BOOK|LAWSUIT|SETTLEMENT|DEDUCTIBLE|INSURANCE|'
                    r'TOW(ED|ING)?\b|UBER|LYFT|HOTEL|TICKET|FINE\b|GAS (MONEY|COST)|PER GALLON|A GALLON|DOWN PAYMENT|REBATE|DISCOUNT|GOODWILL|REIMBURS|REFUND', re.I)

def amounts(descr):
    """[(amount, area)] for the repair bills a complaint names"""
    t = re.sub(r'\s+', ' ', (descr or '').upper()); out = {}
    for m in MONEY.finditer(t):
        v = float((m.group(1) or m.group(2)).replace(',', ''))
        if not 50 <= v <= 15000: continue
        before, after = t[max(0, m.start() - 90):m.start()], t[m.end():m.end() + 50]
        near = before[-60:] + ' ' + after[:40]
        if NOTREP.search(near) or not COSTW.search(before + ' ' + after): continue
        best = None
        for name, rx in AREA:   # nearest repair word before or after the figure
            for mm in rx.finditer(t[max(0, m.start() - 160):m.end() + 80]):
                d = abs((max(0, m.start() - 160) + mm.start()) - m.start())
                if best is None or d < best[0]: best = (d, name)
        if not best or best[0] > 150: continue
        out[best[1]] = max(out.get(best[1], 0), v)
    return out

c = sqlite3.connect(DB)
rows = c.execute("select odino, make, model, year, max(descr) from rows where (descr like '%$%' or descr like '%DOLLARS%') and year between 1995 and 2026 group by odino").fetchall()
print(len(rows), 'complaints name a dollar figure')
OUT = collections.defaultdict(lambda: {'c': [], 't': {}})
hit = 0
for odi, mk, md, y, d in rows:
    fids = WANT.get(((mk or '').upper(), norm(md), y))
    if not fids: continue
    a = amounts(d)
    if not a: continue
    hit += 1
    for fid in fids:
        for area, v in a.items(): OUT[fid]['c'].append([y, area, int(round(v)), odi])
print(hit, 'complaints with a repair bill on site models')

# ---- what to ask the shop: the automaker's notes that announce a fix you can ask for by number
TIP = [
    ('software', 'Transmission', re.compile(r'(TRANSMISSION|TRANSAXLE|\bTCM\b|SHIFT|CVT).{0,80}(SOFTWARE|REPROGRAM|REFLASH|\bFLASH|CALIBRATION)|(SOFTWARE|REPROGRAM|REFLASH|\bFLASH|CALIBRATION).{0,80}(TRANSMISSION|TRANSAXLE|\bTCM\b|SHIFT|CVT)', re.I)),
    ('coverage', 'Transmission', re.compile(r'(CVT|TRANSMISSION|TRANSAXLE).{0,80}(SPECIAL COVERAGE|WARRANTY EXTENSION|EXTENDED (NEW VEHICLE )?(LIMITED )?WARRANTY|CUSTOMER SATISFACTION)|(SPECIAL COVERAGE|WARRANTY EXTENSION|WARRANTY ENHANCEMENT|CUSTOMER SATISFACTION).{0,80}(CVT|TRANSMISSION|TRANSAXLE)', re.I)),
    ('fix', 'Transmission', re.compile(r'\bCVT\b.{0,60}(JUDDER|SHUDDER|WHINE|FLUID)|(JUDDER|SHUDDER).{0,60}\bCVT\b', re.I)),
    ('coverage', 'Engine', re.compile(r'(ENGINE|OIL CONSUMPTION|TURBO|PISTON).{0,80}(SPECIAL COVERAGE|WARRANTY EXTENSION|EXTENDED (NEW VEHICLE )?(LIMITED )?WARRANTY|CUSTOMER SATISFACTION)|(SPECIAL COVERAGE|WARRANTY EXTENSION|WARRANTY ENHANCEMENT|CUSTOMER SATISFACTION).{0,80}(ENGINE|OIL CONSUMPTION)', re.I)),
    ('fix', 'Engine', re.compile(r'OIL CONSUMPTION', re.I)),
    ('software', 'Engine', re.compile(r'(ENGINE|\bPCM\b|\bECM\b|STALL|HESITAT).{0,60}(SOFTWARE|REPROGRAM|REFLASH|CALIBRATION)|(SOFTWARE|REPROGRAM|REFLASH|CALIBRATION).{0,60}(ENGINE|\bPCM\b|\bECM\b|STALL|HESITAT)', re.I)),
    ('coverage', 'Electrical', re.compile(r'(TIPM|BODY CONTROL|\bBCM\b|FUEL PUMP RELAY).{0,80}(SPECIAL COVERAGE|WARRANTY EXTENSION|CUSTOMER SATISFACTION)', re.I)),
    ('software', 'Screen, radio & camera', re.compile(r'(RADIO|UCONNECT|SYNC|INFOTAINMENT|DISPLAY|CAMERA).{0,60}(SOFTWARE UPDATE|REPROGRAM|REFLASH)', re.I)),
]
NOISE = re.compile(r'VCM|scan tool|labor op|procedure only|technician|special tool', re.I)
def one_line(s):
    s = re.sub(r'\s+', ' ', s).strip(); s = re.split(r'(?<=[a-z0-9)])\s{2,}|(?<=[.!?])\s', s)[0].strip().rstrip('.')
    if s.isupper() or sum(ch.isupper() for ch in s) > len(s) * .6: s = s.lower()
    s = s[:1].upper() + s[1:]
    return (s[:120].rsplit(' ', 1)[0] + '…') if len(s) > 122 else s
RAW = os.path.join(HERE, 'data', 'raw_more'); want_mm = {(mk, md) for mk, md, _ in WANT}; nt = 0
for z in sorted(glob.glob(os.path.join(RAW, 'MFR_COMMS_RECEIVED_*.zip'))):
    zz = zipfile.ZipFile(z)
    for row in csv.reader(io.TextIOWrapper(zz.open(zz.namelist()[0]), encoding='utf-8', errors='replace')):
        if len(row) < 5 or row[0] == 'TSB/Document ID': continue
        mk, md = row[1].strip().upper(), norm(row[2])
        if (mk, md) not in want_mm: continue
        summ = re.sub(r'\s+', ' ', row[4]).strip()
        kinds = [(k, a) for k, a, rx in TIP if rx.search(summ)]
        if not kinds or NOISE.search(summ[:200]): continue
        for ys in row[3].split(','):
            if not ys.strip().isdigit(): continue
            for fid in WANT.get((mk, md, int(ys)), ()):
                tl = OUT[fid]['t'].setdefault(str(int(ys)), [])
                for k, a in kinds[:1]:
                    if not any(x[2] == row[0] for x in tl): tl.append([k, a, row[0], one_line(summ)]); nt += 1
print(nt, 'shop tips')
# ---- k: the trouble codes owners of each model year name most (for the code links on year pages), same code rule as engine_codes.py
CODE = re.compile(r'\b([PBCU][0-3][0-9A-F]{3})\b')
NOT_CODES = {'C1500', 'C2500', 'C3500', 'B1500', 'B2000', 'B2200', 'B2300', 'B2500', 'B2600', 'B3000', 'B3500', 'B150E', 'B250E', 'B350E'}
KC = collections.defaultdict(collections.Counter)
for odi, mk, md, y, d in c.execute("select odino, make, model, year, max(descr) from rows where descr glob '*[PBCU][0-3][0-9A-F][0-9A-F][0-9A-F]*' and year between 1995 and 2026 group by odino"):
    fids = WANT.get(((mk or '').upper(), norm(md), y))
    if not fids: continue
    cs = {m for m in CODE.findall((d or '').upper()) if m not in NOT_CODES}
    for fid in fids:
        for cd in cs: KC[(fid, y)][cd] += 1
res = {}
for fid, d in sorted(OUT.items()):
    d['c'].sort()
    res[fid] = {'c': d['c'], 't': {y: sorted(v, key=lambda x: ('coverage', 'software', 'fix').index(x[0]))[:6] for y, v in sorted(d['t'].items())}}
for (fid, y), cnt in KC.items():
    res.setdefault(fid, {'c': [], 't': {}}).setdefault('k', {})[str(y)] = [[cd, n] for cd, n in cnt.most_common(8)]
print(sum(len(v.get('k', {})) for v in res.values()), 'model years with codes')
json.dump(res, open(os.path.join(HERE, 'data', 'repair_costs.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
n5 = collections.Counter()
for fid, d in res.items():
    cnt = collections.Counter(a for _, a, _, _ in d['c'])
    n5[fid] = sum(1 for v in cnt.values() if v >= 5)
print(len(res), 'models;', sum(1 for v in n5.values() if v), 'have at least one area with 5+ bills (all years)')
