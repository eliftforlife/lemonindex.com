# 11-14 growth plan 2D-1: "what owners say it costs", per repair, for the /repair-cost/ pages (repair_cost_pages.py).
#   usage: py -X utf8 data_repair_pages.py      -> data/repair_pages.json
# Two sources, both owners' own words, never a shop's price list:
#   n = NHTSA: the repair bills owners name in their complaints to the government (3 Lemon Index/data/complaints.db). The same dollar
#       rules as data_repair_costs.py (its MONEY / COSTW / NOTREP: purchase prices, payments, rentals, warranties, towing, deductibles...
#       are left out; $50-$15,000 only; one number per complaint and repair, the biggest: the bill, not the diagnosis fee), but each
#       figure goes to the SPECIFIC repair named nearest to it ("$3,800 to replace the transmission" -> transmission replacement).
#   y = YouTube: the dollar amounts owners say out loud in repair and ownership videos (3 Lemon Index/data/yt/<study>/costs.json from
#       auto_costs.py -> costpass.py + costs.py), the repair items only, sorted with the same repair words. Parts-only prices
#       ("$23 on Amazon", "the part is $80") and DIY amounts are left out, so a number is what a repair cost the owner.
# Every point keeps its proof: the NHTSA complaint number, or the YouTube video id + second where it's said.
# pts: [repair slug, model id, model year (NHTSA) or 0, first year, last year (YouTube: the study's generation), dollars, 'n'|'y', ref, t, miles]
import collections, json, os, re, sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
YT = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\yt'
# data_repair_costs.py's setup (paths, MONEY, COSTW, NOTREP) without running its database pass
_src = open(os.path.join(HERE, 'data_repair_costs.py'), encoding='utf-8').read()
_ns = {'__file__': os.path.join(HERE, 'data_repair_costs.py'), '__name__': 'drc_setup'}
exec(compile(_src[:_src.index('\nc = sqlite3.connect(DB)')], 'data_repair_costs.py', 'exec'), _ns)
DB, MONEY, COSTW, NOTREP = _ns['DB'], _ns['MONEY'], _ns['COSTW'], _ns['NOTREP']

# (slug, page name, regex on UPPER-CASE text, lowest believable bill). Most specific first: where two patterns cover the same words
# ("transmission control module"), the earlier one claims them. ENGINE alone is never a repair (too vague), only a new / rebuilt one.
W = r'(?:\W+\w+){0,3}?\W+'   # up to 3 words between
_NOTTR = r'(?!\W*(TEMP|SENSOR|MODULE|FLUID|FILTER|SOLENOID|COOLER|LINES?|MOUNT|PAN|SPEED|RANGE|CONTROL|SHIFT|CABLE|DIPSTICK|SEAL|GASKET|HOSE|FLUSH|SERVICE|SOFTWARE|UPDATE|COMPUTER|WIRING|HARNESS|PLUG|CONNECTOR|BRACKET|VALVE))'
_NOTENG = r'(?!\W*(CONTROL|COMPUTER|MOUNT|LIGHT|MODULE|WIRING|HARNESS|SENSOR|OIL|COVER|AIR|CODE|SPEED|DIAG|MANAGEMENT|BAY|COMPARTMENT|NOISE|PART))'
R = [
    ('tcm', 'Transmission control module (TCM)', r'\bTCM\b|TRANSMISSION CONTROL MODULE|MECHATRONIC', 100),
    ('torque-converter', 'Torque converter', r'TORQUE CONVERTER', 200),
    ('valve-body', 'Transmission valve body', r'VALVE BODY', 200),
    ('transmission-replacement', 'Transmission replacement or rebuild',
     r'(NEW|REPLAC\w*|REBUIL\w*|REMAN\w*|USED|OVERHAUL\w*)' + W + r'(TRANSMISSION|TRANSAXLE|\bTRANS\b|\bCVT\b|GEARBOX)' + _NOTTR + r'|(TRANSMISSION|TRANSAXLE|\bCVT\b|GEARBOX)' + _NOTTR + W + r'(REPLACE\w*|REBUIL\w*|REMAN\w*|OVERHAUL\w*)', 700),
    ('clutch', 'Clutch replacement', r'\bCLUTCH(ES)?\b(?! (PEDAL )?(MASTER|SLAVE|SWITCH|FLUID))', 200),
    ('ecm', 'Engine computer (ECM / PCM)', r'\bPCM\b|\bECM\b|\bECU\b|ENGINE CONTROL MODULE|POWERTRAIN CONTROL MODULE|ENGINE COMPUTER', 100),
    ('tipm', 'TIPM (fuse box module)', r'\bTIPM\b|TOTALLY INTEGRATED POWER MODULE', 100),
    ('bcm', 'Body control module (BCM)', r'\bBCM\b|BODY CONTROL MODULE', 100),
    ('timing-chain', 'Timing chain', r'TIMING CHAINS?', 200),
    ('timing-belt', 'Timing belt', r'TIMING BELTS?', 150),
    ('cam-phaser', 'Cam phasers', r'(CAM )?PHASERS?\b', 200),
    ('lifters', 'Lifters', r'\bLIFTERS?\b', 200),
    ('head-gasket', 'Head gasket', r'HEAD GASKETS?', 300),
    ('engine-replacement', 'Engine replacement or rebuild',
     r'(NEW|REPLAC\w*|REBUIL\w*|REMAN\w*|USED|ANOTHER)' + W + r'ENGINE\b' + _NOTENG + r'|(NEW|USED|REBUILT|REMAN\w*|ANOTHER) MOTOR\b(?! (UNIT|ASSEMBL|MOUNT))|ENGINE\W+(REPLACEMENT|REBUILD|WAS REPLACED|HAD TO BE REPLACED|NEEDS TO BE REPLACED|NEEDED TO BE REPLACED)|LONG ?BLOCK|SHORT ?BLOCK', 1000),
    ('turbo', 'Turbocharger', r'TURBO ?CHARGERS?|(REPLAC\w*|NEW|BAD|FAILED|BLOWN)' + W + r'TURBOS?\b|\bTURBOS?\W+(\w+\W+){0,2}(REPLAC\w*|FAIL\w*|WENT|BLEW)', 200),
    ('water-pump', 'Water pump', r'WATER PUMPS?', 100),
    ('radiator', 'Radiator', r'RADIATORS?', 100),
    ('thermostat', 'Thermostat', r'THERMOSTAT', 50),
    ('ac-compressor', 'A/C compressor', r'(?<!AIR SUSPENSION )(?<!AIR RIDE )COMPRESSOR', 150),
    ('ac-condenser', 'A/C condenser', r'CONDENSER', 100),
    ('ac-evaporator', 'A/C evaporator', r'EVAPORATOR', 150),
    ('heater-core', 'Heater core', r'HEATER CORE', 150),
    ('blend-door', 'Blend door actuator', r'BLEND DOOR', 50),
    ('catalytic-converter', 'Catalytic converter', r'CATALYTIC|CAT(ALYST)? CONVERTER', 100),
    ('oxygen-sensor', 'Oxygen (O2) sensor', r'(OXYGEN|\bO2) SENSORS?', 50),
    ('egr', 'EGR valve or cooler', r'\bEGR\b', 100),
    ('dpf', 'Diesel particulate filter (DPF)', r'\bDPF\b|PARTICULATE FILTER', 200),
    ('abs-module', 'ABS module or pump', r'\bABS\W+(\w+\W+){0,1}(MODULE|PUMP|UNIT|CONTROL\w*|ACTUATOR)|ANTI-?LOCK BRAKE (MODULE|PUMP|CONTROL)|HYDRAULIC (CONTROL )?UNIT|BRAKE ACTUATOR', 150),
    ('brake-booster', 'Brake booster', r'BRAKE BOOSTER|VACUUM PUMP', 100),
    ('master-cylinder', 'Brake master cylinder', r'MASTER CYLINDER', 100),
    ('brakes', 'Brake repair (pads, rotors, calipers)', r'BRAKE PADS?|\bROTORS?\b|CALIPERS?|BRAKE JOB|BRAKE LINES?|\bBRAKES\b', 50),
    ('fuel-pump', 'Fuel pump', r'FUEL PUMPS?', 100),
    ('fuel-injectors', 'Fuel injectors', r'INJECTORS?', 100),
    ('throttle-body', 'Throttle body', r'THROTTLE BODY', 100),
    ('ignition-coils', 'Ignition coils', r'IGNITION COILS?|COIL PACKS?|\bCOILS\b', 50),
    ('spark-plugs', 'Spark plugs', r'SPARK PLUGS?', 50),
    ('hybrid-battery', 'Hybrid battery', r'HYBRID BATTERY|HIGH VOLTAGE BATTERY|TRACTION BATTERY|BATTERY PACK', 300),
    ('alternator', 'Alternator', r'ALTERNATORS?', 100),
    ('starter', 'Starter', r'\bSTARTER\b', 100),
    ('battery', 'Car battery (12-volt)', r'(NEW|REPLAC\w*)\W+(\w+\W+){0,2}(?<!HYBRID )(?<!VOLTAGE )(?<!TRACTION )BATTERY\b(?! PACK)|(?<!HYBRID )(?<!VOLTAGE )(?<!TRACTION )\bBATTERY\W+(WAS |HAD TO BE |NEEDED TO BE )?(REPLAC\w*)', 50),
    ('wiring-harness', 'Wiring harness', r'WIRING HARNESS|\bHARNESS\b', 100),
    ('power-steering-pump', 'Power steering pump', r'POWER STEERING PUMP', 100),
    ('steering-rack', 'Steering rack', r'STEERING RACK|RACK AND PINION|RACK & PINION|STEERING GEAR(BOX| BOX)?\b', 200),
    ('steering-column', 'Steering column', r'STEERING COLUMN', 100),
    ('tie-rods', 'Tie rods', r'TIE RODS?', 50),
    ('wheel-bearing', 'Wheel bearing', r'WHEEL BEARINGS?|HUB BEARINGS?|HUB ASSEMBL\w*', 100),
    ('ball-joints', 'Ball joints', r'BALL JOINTS?', 100),
    ('control-arms', 'Control arms', r'CONTROL ARMS?', 100),
    ('air-suspension', 'Air suspension', r'AIR (SUSPENSION|RIDE|STRUTS?|SPRINGS?|BAG SUSPENSION)', 200),
    ('struts', 'Struts and shocks', r'\bSTRUTS?\b|\bSHOCKS\b|SHOCK ABSORBERS?', 100),
    ('transfer-case', 'Transfer case', r'TRANSFER CASE', 200),
    ('differential', 'Differential', r'DIFFERENTIAL|\bREAR END\b', 200),
    ('cv-axle', 'CV axle', r'CV (AXLES?|JOINTS?|SHAFTS?|BOOTS?)|HALF ?SHAFTS?|\bAXLES?\b', 100),
    ('driveshaft', 'Driveshaft', r'DRIVE ?SHAFTS?', 100),
    ('engine-mounts', 'Engine mounts', r'(ENGINE|MOTOR|TRANSMISSION) MOUNTS?', 100),
    ('intake-manifold', 'Intake manifold', r'INTAKE MANIFOLD', 100),
    ('valve-cover-gasket', 'Valve cover gasket', r'VALVE COVER GASKETS?', 100),
    ('oil-pan', 'Oil pan', r'OIL PAN', 100),
    ('oil-cooler', 'Oil cooler', r'OIL COOLER', 100),
    ('rear-main-seal', 'Rear main seal', r'REAR MAIN SEAL', 200),
    ('window-regulator', 'Window regulator', r'WINDOW REGULATORS?|WINDOW MOTORS?', 50),
    ('door-lock-actuator', 'Door lock actuator', r'(DOOR )?LOCK ACTUATORS?', 50),
    ('infotainment', 'Radio / infotainment screen', r'INFOTAINMENT|HEAD UNIT|TOUCH ?SCREEN|UCONNECT|\bMCU\b|(NEW|REPLAC\w*)\W+(\w+\W+){0,2}RADIO\b|\bRADIO (UNIT|REPLACEMENT|MODULE)|NAVIGATION (UNIT|SYSTEM)', 100),
    ('backup-camera', 'Backup camera', r'(BACK ?UP|REAR ?VIEW|REVERSE) CAMERA', 50),
    ('crank-sensor', 'Crankshaft position sensor', r'CRANK(SHAFT)? (POSITION )?SENSOR', 50),
    ('cam-sensor', 'Camshaft position sensor', r'CAM(SHAFT)? (POSITION )?SENSOR', 50),
    ('maf-sensor', 'Mass air flow (MAF) sensor', r'MASS AIR ?FLOW|\bMAF\b', 50),
    ('evap', 'EVAP purge valve or canister', r'PURGE VALVE|\bEVAP\b|CHARCOAL CANISTER', 50),
    ('airbag-module', 'Airbag module or clock spring', r'CLOCK ?SPRINGS?|AIR ?BAG (CONTROL )?MODULE|\bSRS MODULE', 100),
]
# parts that aren't one of the repairs above: when one of them is named nearer to the dollar figure, the bill is for something else
BLOCK = r'TRANSMISSION|TRANSAXLE|\bCVT\b|\bENGINE\b|\bMOTOR\b|\bA/?C\b|AIR CONDITION\w*|SUSPENSION|ELECTRICAL|\bSTEERING\b|EXHAUST|COOLING SYSTEM|SUN ?ROOF|MOON ?ROOF|\bDOORS?\b|\bSEATS?\b|AIR ?BAGS?|HEADLIGHTS?|HEAD ?LAMPS?|\bTIRES?\b|\bKEYS?\b|IGNITION|WINDSHIELD|\bPAINT\b|\bRUST\b|\bFRAME\b|\bLIGHTS?\b|\bRECALL|\bDIAGNOS\w*|\bTOW\w*|\bRENTAL'
RX = [(s, re.compile(rx)) for s, _, rx, _ in R] + [('_', re.compile(BLOCK))]
LO = {s: lo for s, _, _, lo in R}
NOTOWN = re.compile(r'\bOWE|COVERING|PICKED UP THE|PAID FOR (THE )?(PART|REST)|SPLIT|HALF OF|ON THE CAR\b|CLASS ACTION|FIRE ENGINEER')   # money the owner didn't pay for this repair

def nearest(t, pos, before=130, after=70):
    """the specific repair named nearest to the dollar figure at pos (before / after window), or None. A later (less specific) pattern
    can't claim words an earlier one already matched."""
    a = max(0, pos - before); win = t[a:pos + after]; taken = []; hits = []
    for s, rx in RX:
        for m in rx.finditer(win):
            sp = (a + m.start(), a + m.end())
            if any(sp[0] < b and x < sp[1] for x, b in taken): continue
            taken.append(sp)
            d = min(abs(sp[0] - pos), abs(sp[1] - pos))
            hits.append((d, s))
    hits.sort(); real = [h for h in hits if h[1] != '_']
    if not hits or hits[0][1] == '_': return None   # another part is named nearer
    # a bill for two different repairs named about as near ("replace the radiator and the transmission, $4,800") belongs to neither
    if any(s2 != hits[0][1] and d2 <= hits[0][0] + 35 for d2, s2 in real[1:]): return None
    return hits[0][1]

def bills(descr):
    """{repair: dollars} for the repair bills one NHTSA complaint names (data_repair_costs.amounts' rules, specific repair instead of area)"""
    t = re.sub(r'\s+', ' ', (descr or '').upper()); out = {}
    for m in MONEY.finditer(t):
        v = float((m.group(1) or m.group(2)).replace(',', ''))
        if not 50 <= v <= 15000: continue
        before, after = t[max(0, m.start() - 90):m.start()], t[m.end():m.end() + 50]
        near = before[-60:] + ' ' + after[:40]
        if NOTREP.search(near) or NOTOWN.search(near) or not COSTW.search(before + ' ' + after): continue
        s = nearest(t, m.start())
        if s and v >= LO[s]: out[s] = max(out.get(s, 0), v)
    return out

def main():
    XL = {}
    for p in ('data/extras_local.json', 'data/extras_local_new.json', 'data/extras_local_low.json', 'data/extras_local_tesla.json'):
        p = os.path.join(HERE, p)
        if not os.path.exists(p): continue
        for fid, ys in json.load(open(p, encoding='utf-8')).items():
            for y, e in ys.items(): XL.setdefault(fid, {}).setdefault(y, e)
    key = {}   # (MAKE, MODEL, year) -> model id, the NHTSA names each site model year is filed under (as data_top_fails.py)
    for fid, ys in XL.items():
        for y, e in ys.items():
            for mk, md, _ in (e or {}).get('names') or []: key.setdefault((mk, md, int(y)), fid)
    pts = []
    c = sqlite3.connect(DB)
    q = ("select odino, make, model, year, max(miles), max(descr) from rows where (descr like '%$%' or descr like '%DOLLARS%') "
         "and year between 1995 and 2026 group by odino")
    n_c = 0
    for o, mk, md, y, mi, d in c.execute(q):
        fid = key.get((mk, md, y))
        if not fid: continue
        b = bills(d)
        if b: n_c += 1
        for s, v in b.items(): pts.append([s, fid, y, y, y, int(round(v)), 'n', o, 0, int(mi) if mi and 0 < mi < 500000 else 0])
    print(n_c, 'NHTSA complaints name a bill for a specific repair;', len(pts), 'points')
    # ---- YouTube (auto_costs.py data): every study the site shows on year pages (data_yt.py's STUDIES, same years)
    sys.path.insert(0, YT); cwd = os.getcwd(); os.chdir(HERE)
    src = open(os.path.join(HERE, 'data_yt.py'), encoding='utf-8').read(); ns = {'__name__': 'data_yt_setup'}
    try: exec(compile(src[:src.index('\nGUIDE = ')], 'data_yt.py', 'exec'), ns)
    finally: os.chdir(cwd)
    REP = re.compile(r'^(Transmission|Timing chain|Water pump|Oil leak|Steering|Fuel pump|Brakes|Battery|Other repairs)')
    PARTS = re.compile(r'AMAZON|ROCK ?AUTO|EBAY|JUNK ?YARD|PICK.?N.?PULL|\bTHE PART\b|PARTS? (ONLY|ALONE|ITSELF)|FOR (THE )?PARTS?\b|PART (IS|WAS|COSTS?|ITSELF)|\bDIY\b|MYSELF|YOURSELF|'
                       r'\bKIT\b|AFTERMARKET|\bOEM\b|ON SALE|PER (HOUR|MONTH|YEAR)|A (MONTH|YEAR)\b|WARRANTY|INSURANCE|SAVE|SAVED|SAVING', re.I)
    ny = 0; seen = set()
    for st in ns['STUDIES']:
        sid, fid, years = st[0], st[1], st[2]
        if not years or ':' in fid: continue
        p = os.path.join(YT, sid, 'costs.json')
        if not os.path.exists(p): continue
        items = json.load(open(p, encoding='utf-8')).get('items') or {}
        for k, xs in items.items():
            if not REP.match(k): continue
            for x in xs:
                ctx = (x.get('ctx') or '').upper(); i = ctx.find(' $')
                if i < 0 or PARTS.search(ctx): continue
                s = nearest(ctx, i + 1, 60, 30)
                v = x['v']
                if not s or not 50 <= v <= 15000 or v < LO[s]: continue
                kk = (s, fid, x['id'])
                if kk in seen: continue   # one number per video and repair
                seen.add(kk); ny += 1
                pts.append([s, fid, 0, min(years), max(years), int(round(v)), 'y', x['id'], int(x.get('t') or 0), 0])
    print(ny, 'YouTube points')
    out = dict(repairs={s: n for s, n, _, _ in R}, pts=sorted(pts, key=lambda r: (r[0], r[1], r[2], r[5])))
    json.dump(out, open(os.path.join(HERE, 'data', 'repair_pages.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    by = collections.Counter(r[0] for r in pts); bm = collections.Counter((r[0], r[1]) for r in pts)
    for s, n in by.most_common():
        print(f'{s:22} {n:5}  models 5+: {sum(1 for (a, _), k in bm.items() if a == s and k >= 5)}')
    print('model pages (5+):', sum(1 for k in bm.values() if k >= 5))

if __name__ == '__main__': main()
