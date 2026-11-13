# Heavy-duty pickups + truck engines (11-12 round-2 UX test, Mitch: "it'd tell me a 6.0 Power Stroke is a good buy"; Ryan: "which F-150 engine?").
# Writes data/hd.json for hd_pages.py. Free public NHTSA data only, no AI, nothing estimated:
#   1. extract: every complaint on the HD pickups (Ram 2500/3500, F-250/F-350 Super Duty, Silverado/Sierra 2500/3500) and the F-150, with its
#      partial VIN, from NHTSA's FLAT_CMPL.txt + the newer COMPLAINTS_RECEIVED_2025-2026.zip (one row per complaint number)
#   2. decode: the engine. VIN position 8 is the engine code on all three makes; for each (truck, model year, code) the most common 11-character
#      VIN is decoded with NHTSA vPIC (displacement, fuel, engine model), the way shorts v2/follow-B4 matched Ram 1500 engines
#   3. recalls: NHTSA recalls API per truck name and model year (cached like data_fetch_api.py)
#   4. aggregate -> data/hd.json: per truck and model year (complaints, components, engines, mileage, quotes, recalls) and per engine
#      generation (years, trucks, complaints, components, owner-words counts, recalls)
# No sales split exists for HD pickups (automakers report the whole F-Series / Ram / Silverado line), so there's no per-car-sold score here.
#   usage: py -X utf8 data_hd.py [extract] [decode] [recalls] [build]     (no args = every stage; each stage caches its output)
import collections, hashlib, json, os, re, statistics, sys, time, urllib.parse, urllib.request, zipfile
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
WORK = os.path.join(LEMON, 'data', 'hd'); os.makedirs(WORK, exist_ok=True)
FLAT = os.path.join(LEMON, 'video 1 most reliable', 'data', 'raw', 'FLAT_CMPL.txt')
NEWZ = os.path.join(LEMON, 'data', 'raw', 'nhtsa', 'COMPLAINTS_RECEIVED_2025-2026.zip')
CACHE = r'C:\Users\elift\Code\lemonindex-site\data\cache'   # the shared API cache data_fetch_api.py uses (main checkout)
if not os.path.isdir(CACHE): CACHE = os.path.join(HERE, 'data', 'cache')
STAGES = set(sys.argv[1:]) or {'extract', 'decode', 'recalls', 'build'}
Y0, Y1 = 1999, 2026

# truck id -> (name, NHTSA (make, model) names). Plain "SILVERADO"/"SIERRA" are left out: they mix 1500s and HDs.
TRUCKS = {
    'ford-super-duty': ('Ford Super Duty (F-250/F-350)', 'Ford', {('FORD', m) for m in ('F-250', 'F-250 SD', 'F-350', 'F-350 SD', 'F-350 SUPER DUTY')}),
    'ram-heavy-duty': ('Ram 2500/3500 (Heavy Duty)', 'Ram', {('DODGE', 'RAM 2500'), ('DODGE', 'RAM 3500'), ('RAM', '2500'), ('RAM', '3500')}),
    'chevrolet-silverado-hd': ('Chevrolet Silverado 2500HD/3500HD', 'Chevrolet', {('CHEVROLET', m) for m in ('SILVERADO 2500', 'SILVERADO 3500', 'SILVERADO 2500 HD', 'SILVERADO 3500 HD', 'SILVERADO HD')}),
    'gmc-sierra-hd': ('GMC Sierra 2500HD/3500HD', 'GMC', {('GMC', m) for m in ('SIERRA 2500', 'SIERRA 3500', 'SIERRA 2500 HD', 'SIERRA HD')}),
    'ford-f-150': ('Ford F-150', 'Ford', {('FORD', 'F-150')}),   # engine pages only (the F-150 keeps its F-Series model page)
}
KEY = {mm: t for t, (_, _, s) in TRUCKS.items() for mm in s}
CMPL_JL = os.path.join(WORK, 'cmpl.jsonl')

def extract():
    seen = {}
    def take(p):
        if len(p) < 20: return
        t = KEY.get((p[3].strip().upper(), p[4].strip().upper()))
        if not t or not p[5].strip().isdigit(): return
        y = int(p[5]);
        if not Y0 <= y <= Y1: return
        o = p[1].strip(); c = p[11].strip()
        if o in seen:
            if c: seen[o]['comps'].add(c)
            return
        seen[o] = dict(o=o, t=t, md=p[4].strip().upper(), y=y, vin=p[14].strip().upper(), comps={c} if c else set(), ld=p[16].strip(), mi=p[17].strip(),
                       cr=p[6] == 'Y', fi=p[8] == 'Y', inj=int(p[9]) if p[9].strip().isdigit() else 0, dth=int(p[10]) if p[10].strip().isdigit() else 0,
                       tow=(p[48] == 'Y') if len(p) > 48 else False, d=p[19].strip()[:2048])
    with open(FLAT, encoding='latin-1') as fh:
        for line in fh: take(line.rstrip('\r\n').split('\t'))
    n0 = len(seen)
    with zipfile.ZipFile(NEWZ) as z:
        with z.open(z.namelist()[0]) as fh:
            for raw in fh: take(raw.decode('latin-1').rstrip('\r\n').split('\t'))
    with open(CMPL_JL, 'w', encoding='utf-8') as out:
        for r in seen.values(): r['comps'] = sorted(r['comps']); out.write(json.dumps(r) + '\n')
    print('extract:', n0, 'from FLAT_CMPL,', len(seen) - n0, 'newer;', collections.Counter(r['t'] for r in seen.values()))

def load():
    return [json.loads(l) for l in open(CMPL_JL, encoding='utf-8')]

def get(url):
    path = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:20] + '.json')
    if os.path.exists(path): return json.load(open(path, encoding='utf-8'))
    for a in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'lemonindex.com data build'}), timeout=40) as r:
                body = r.read().decode('utf-8', 'replace')
            data = json.loads(body) if body.strip() else None; break
        except urllib.error.HTTPError as e:
            if e.code in (400, 404): data = None; break
            time.sleep(2 * (a + 1))
        except Exception: time.sleep(2 * (a + 1))
    else: return None
    os.makedirs(CACHE, exist_ok=True); json.dump(data, open(path, 'w', encoding='utf-8')); return data

VALID = re.compile(r'^[1-5][A-HJ-NPR-Z0-9]{10}$')
DEC_JS = os.path.join(WORK, 'decoded.json')
def decode():
    R = load(); samp = collections.defaultdict(list)
    for r in R:
        v = r['vin']
        if len(v) >= 11 and VALID.match(v[:11]): samp[(r['t'], r['y'], v[7])].append(v[:11])
    D = json.load(open(DEC_JS, encoding='utf-8')) if os.path.exists(DEC_JS) else {}
    todo = [(k, v) for k, v in sorted(samp.items()) if len(v) >= 3 and '|'.join(map(str, k)) not in D]
    print('decode:', len(samp), 'keys,', len(todo), 'to fetch')
    for i, (k, v) in enumerate(todo):
        cnt = collections.Counter(v).most_common(2); res = []
        for vin, _ in cnt:
            d = (get(f'https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json&modelyear={k[1]}') or {}).get('Results') or [{}]
            d = d[0]
            res.append(dict(vin=vin, disp=d.get('DisplacementL', ''), cyl=d.get('EngineCylinders', ''), model=d.get('EngineModel', ''), fuel=d.get('FuelTypePrimary', ''),
                            turbo=d.get('Turbo', ''), other=(d.get('OtherEngineInfo') or '')[:120], mfr=d.get('EngineManufacturer', ''), series=d.get('Series', ''), mdl=d.get('Model', '')))
        D['|'.join(map(str, k))] = dict(n=len(v), dec=res)
        if i % 25 == 0:
            print(' ', i, k, len(v), res[0]['disp'], res[0]['fuel'], res[0]['model'], flush=True); json.dump(D, open(DEC_JS, 'w', encoding='utf-8'), indent=0)
    json.dump(D, open(DEC_JS, 'w', encoding='utf-8'), indent=0); print('decoded', len(D))

# ---------------------------------------------------------------- 3. recalls (NHTSA API, every name the trucks are filed under)
RNAMES = {
    'ford-super-duty': [('ford', m) for m in ('f-250', 'f-250 sd', 'f-250 super duty', 'f-350', 'f-350 sd', 'f-350 super duty')],
    'ram-heavy-duty': [('dodge', 'ram 2500'), ('dodge', 'ram 3500'), ('ram', '2500'), ('ram', '3500'), ('ram', 'ram 2500'), ('ram', 'ram 3500')],
    'chevrolet-silverado-hd': [('chevrolet', m) for m in ('silverado 2500', 'silverado 2500 hd', 'silverado 2500hd', 'silverado 3500', 'silverado 3500 hd', 'silverado 3500hd', 'silverado hd')],
    'gmc-sierra-hd': [('gmc', m) for m in ('sierra 2500', 'sierra 2500 hd', 'sierra 2500hd', 'sierra 3500', 'sierra 3500 hd', 'sierra 3500hd', 'sierra hd')],
    'ford-f-150': [('ford', 'f-150')],
}
REC_JS = os.path.join(WORK, 'recalls.json')
def recalls():
    out = {}
    for t, names in RNAMES.items():
        for y in range(Y0 if t != 'ford-f-150' else 2011, 2027):
            seen = {}
            for mk, md in names:
                for r in (get(f'https://api.nhtsa.gov/recalls/recallsByVehicle?make={urllib.parse.quote(mk)}&model={urllib.parse.quote(md)}&modelYear={y}') or {}).get('results', []) or []:
                    c = r.get('NHTSACampaignNumber')
                    if c and c not in seen:
                        seen[c] = {'id': c, 'date': r.get('ReportReceivedDate', ''), 'part': r.get('Component', ''), 'summary': (r.get('Summary') or '').strip()[:700],
                                   'risk': (r.get('Consequence') or '').strip()[:400], 'fix': (r.get('Remedy') or '').strip()[:400]}
            out[f'{t}|{y}'] = sorted(seen.values(), key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2])
        print('recalls', t, sum(len(v) for k, v in out.items() if k.startswith(t + '|')), flush=True)
    json.dump(out, open(REC_JS, 'w', encoding='utf-8'), ensure_ascii=False)

# ---------------------------------------------------------------- 4. aggregate
# Engine generations with a page. Years = the model years we count for it in these trucks. Facts (names, years, codes) are the engine makers'
# public ones; which complaint belongs to which engine comes only from the VIN decode (vPIC), never from a guess.
ENG = {
    'powerstroke-73': dict(name='Ford 7.3 Power Stroke', short='7.3 Power Stroke', maker='Ford', code='Navistar T444E', fuel='diesel', lay='7.3 L V8 turbo diesel', trucks=['ford-super-duty']),
    'powerstroke-60': dict(name='Ford 6.0 Power Stroke', short='6.0 Power Stroke', maker='Ford', code='Navistar VT365', fuel='diesel', lay='6.0 L V8 turbo diesel', trucks=['ford-super-duty']),
    'powerstroke-64': dict(name='Ford 6.4 Power Stroke', short='6.4 Power Stroke', maker='Ford', code='Navistar MaxxForce 7', fuel='diesel', lay='6.4 L V8 twin-turbo diesel', trucks=['ford-super-duty']),
    'powerstroke-67': dict(name='Ford 6.7 Power Stroke', short='6.7 Power Stroke', maker='Ford', code='Scorpion', fuel='diesel', lay='6.7 L V8 turbo diesel', trucks=['ford-super-duty']),
    'cummins-59': dict(name='Cummins 5.9 (Ram)', short='5.9 Cummins', maker='Ram', code='Cummins ISB 5.9', fuel='diesel', lay='5.9 L inline-6 turbo diesel', trucks=['ram-heavy-duty']),
    'cummins-67': dict(name='Cummins 6.7 (Ram)', short='6.7 Cummins', maker='Ram', code='Cummins ISB 6.7', fuel='diesel', lay='6.7 L inline-6 turbo diesel', trucks=['ram-heavy-duty']),
    'duramax-lb7': dict(name='Duramax LB7', short='Duramax LB7', maker='GM', code='LB7', fuel='diesel', lay='6.6 L V8 turbo diesel', trucks=['chevrolet-silverado-hd', 'gmc-sierra-hd']),
    'duramax-lly': dict(name='Duramax LLY', short='Duramax LLY', maker='GM', code='LLY', fuel='diesel', lay='6.6 L V8 turbo diesel', trucks=['chevrolet-silverado-hd', 'gmc-sierra-hd']),
    'duramax-lbz': dict(name='Duramax LBZ', short='Duramax LBZ', maker='GM', code='LBZ', fuel='diesel', lay='6.6 L V8 turbo diesel', trucks=['chevrolet-silverado-hd', 'gmc-sierra-hd']),
    'duramax-lmm': dict(name='Duramax LMM', short='Duramax LMM', maker='GM', code='LMM', fuel='diesel', lay='6.6 L V8 turbo diesel', trucks=['chevrolet-silverado-hd', 'gmc-sierra-hd']),
    'duramax-lml': dict(name='Duramax LML', short='Duramax LML', maker='GM', code='LML', fuel='diesel', lay='6.6 L V8 turbo diesel', trucks=['chevrolet-silverado-hd', 'gmc-sierra-hd']),
    'duramax-l5p': dict(name='Duramax L5P', short='Duramax L5P', maker='GM', code='L5P', fuel='diesel', lay='6.6 L V8 turbo diesel', trucks=['chevrolet-silverado-hd', 'gmc-sierra-hd']),
    # F-150 (Ryan): the three engines people cross-shop, by VIN
    'ford-ecoboost-27': dict(name='Ford 2.7 EcoBoost', short='2.7 EcoBoost', maker='Ford', code='Nano', fuel='gas', lay='2.7 L V6 twin-turbo', trucks=['ford-f-150']),
    'f150-ecoboost-35-g1': dict(name='Ford 3.5 EcoBoost, 1st gen (F-150)', short='3.5 EcoBoost gen 1', maker='Ford', code='3.5 EcoBoost gen 1', fuel='gas', lay='3.5 L V6 twin-turbo', trucks=['ford-f-150']),
    'f150-ecoboost-35-g2': dict(name='Ford 3.5 EcoBoost, 2nd gen (F-150)', short='3.5 EcoBoost gen 2', maker='Ford', code='D35', fuel='gas', lay='3.5 L V6 twin-turbo', trucks=['ford-f-150']),
    'f150-coyote': dict(name='Ford 5.0 Coyote (F-150)', short='5.0 Coyote V8', maker='Ford', code='Coyote', fuel='gas', lay='5.0 L V8', trucks=['ford-f-150']),
}
PROD = {'powerstroke-73': (1999, 2003), 'powerstroke-60': (2003, 2007), 'powerstroke-64': (2008, 2010), 'powerstroke-67': (2011, 2026), 'cummins-59': (1999, 2007),
        'cummins-67': (2007, 2026), 'duramax-lb7': (2001, 2004), 'duramax-lly': (2004, 2006), 'duramax-lbz': (2006, 2007), 'duramax-lmm': (2007, 2010), 'duramax-lml': (2011, 2016),
        'duramax-l5p': (2017, 2026), 'ford-ecoboost-27': (2015, 2026), 'f150-ecoboost-35-g1': (2011, 2016), 'f150-ecoboost-35-g2': (2017, 2026), 'f150-coyote': (2011, 2026)}
GM_RPO = {'1': 'LB7', '2': 'LLY', 'D': 'LBZ', '6': 'LMM', '8': 'LML', 'Y': 'L5P'}   # GM HD VIN position 8, checked against vPIC's EngineModel below

def classify(t, y, code, dec):
    """-> (engine slug or None, label, fuel) from the vPIC decode of the most common VIN for this truck / model year / VIN position-8 code"""
    a = dec[0]; mdl = ' '.join(x.get('model', '') + ' ' + x.get('other', '') for x in dec)
    try: disp = round(float(a['disp']), 1)
    except (TypeError, ValueError): disp = None
    _f = (a['fuel'] or '').lower()
    fuel = 'diesel' if 'diesel' in _f else 'electric' if _f.startswith('electric') else 'gas' if _f else ''
    if fuel == 'electric': return None, 'electric (Lightning)' if t == 'ford-f-150' else 'electric', 'electric'
    if t in ('chevrolet-silverado-hd', 'gmc-sierra-hd'):
        m = re.search(r'\b(LB7|LLY|LBZ|LMM|LML|L5P|LGH)\b', mdl)
        rpo = m.group(1) if m else (GM_RPO.get(code) if fuel == 'diesel' or (disp == 6.6 and not fuel) else None)
        if rpo == 'LGH': rpo = 'LML'   # the LML's lower-output version (cab-chassis 3500s), same engine generation
        if rpo and (m or disp == 6.6): return f'duramax-{rpo.lower()}', f'6.6 Duramax {rpo} diesel', 'diesel'
        if disp == 6.6 and 'L8T' in mdl: return None, '6.6 V8 gas (L8T)', 'gas'
    if fuel == 'diesel' or (t == 'ford-super-duty' and disp in (7.3, 6.0, 6.4) and code in 'FPR' and not fuel) or (t == 'ram-heavy-duty' and disp in (5.9, 6.7) and not fuel and 'cummins' in (a['mfr'] or '').lower()):
        if t == 'ford-super-duty' and disp in (7.3, 6.0, 6.4, 6.7): return f'powerstroke-{str(disp).replace(".", "")}', f'{disp} Power Stroke diesel', 'diesel'
        if t == 'ram-heavy-duty' and disp in (5.9, 6.7): return f'cummins-{str(disp).replace(".", "")}', f'{disp} Cummins diesel', 'diesel'
        return None, f'{disp} diesel' if disp else 'diesel', 'diesel'
    if t == 'ram-heavy-duty' and disp == 5.9 and a.get('cyl') == '6': return 'cummins-59', '5.9 Cummins diesel', 'diesel'   # the only 5.9 inline-6 (the gas 5.9 is a V8)
    if t == 'ford-f-150' and disp:
        if disp == 3.5 and code == 'D' and y >= 2021: return None, '3.5 PowerBoost hybrid', 'hybrid'   # vPIC says HEV for 2021-22; same code after
        if disp == 3.5 and code == 'G' and y >= 2019: return None, '3.5 EcoBoost High Output (Raptor)', 'gas'   # 2019+: the regular 3.5 moved to codes 4 / 8
        if disp == 2.7: return 'ford-ecoboost-27', '2.7 EcoBoost V6', 'gas'
        if disp == 3.5:
            if re.search(r'Ti-VCT', mdl): return None, '3.5 V6 (non-turbo)', 'gas'
            if re.search(r'hybrid|powerboost|HEV', mdl, re.I) or 'electric' in (a['fuel'] + ' ' + (dec[0].get('other') or '')).lower(): return None, '3.5 PowerBoost hybrid', 'hybrid'
            if re.search(r'high output|\bHO\b', mdl, re.I): return None, '3.5 EcoBoost High Output (Raptor)', 'gas'
            return ('f150-ecoboost-35-g1' if y <= 2016 else 'f150-ecoboost-35-g2'), '3.5 EcoBoost V6', 'gas'
        if disp == 5.0 and y >= 2011: return 'f150-coyote', '5.0 Coyote V8', 'gas'
    cyl = a.get('cyl') or ''
    lab = (f'{disp} ' if disp else '') + (f'V{cyl}' if cyl in ('8', '10') else f'{cyl}-cyl' if cyl else '') + ' gas'
    return None, lab.strip(), fuel or 'gas'

PART = {'ELECTRICAL SYSTEM': 'electrical', 'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'VEHICLE SPEED CONTROL': 'speed control',
        'FUEL/PROPULSION SYSTEM': 'fuel system', 'FUEL SYSTEM': 'fuel system', 'FORWARD COLLISION AVOIDANCE': 'automatic emergency braking', 'VISIBILITY/WIPER': 'wipers & visibility',
        'VISIBILITY': 'visibility', 'AIR BAGS': 'airbags', 'STRUCTURE': 'body structure', 'EXTERIOR LIGHTING': 'lights', 'ENGINE AND ENGINE COOLING': 'engine',
        'ENGINE': 'engine', 'STEERING': 'steering', 'SUSPENSION': 'suspension', 'WHEELS': 'wheels', 'TIRES': 'tires', 'SEATS': 'seats', 'SEAT BELTS': 'seat belts',
        'LATCHES/LOCKS/LINKAGES': 'doors, locks & latches', 'PARKING BRAKE': 'parking brake', 'ELECTRONIC STABILITY CONTROL': 'stability control', 'EQUIPMENT': 'equipment',
        'TRAILER HITCHES': 'trailer hitch', 'BACK OVER PREVENTION': 'backup camera', 'LANE DEPARTURE': 'lane assist', 'HYBRID PROPULSION SYSTEM': 'hybrid system'}
def part(c):
    c = c.split(':')[0].strip()
    if c.startswith('FUEL SYSTEM'): return 'fuel system'
    if c.startswith('ELECTRONIC STABILITY'): return 'stability control'
    if c.startswith('SERVICE BRAKES'): return 'brakes'
    return PART.get(c, c.lower())
# what owners write, counted per complaint (regex on the owner's own words). Labels say exactly what's counted.
WORDS = {
    'head_gasket': ('mention a head gasket', r'head gasket'),
    'egr': ('mention the EGR system', r'\begr\b'),
    'oil_cooler': ('mention the oil cooler', r'oil cooler'),
    'injector': ('mention an injector', r'injector'),
    'cp4': ('mention the CP4 or the high-pressure fuel pump', r'\bcp[- ]?4|high[- ]pressure (fuel )?pump|injection pump'),
    'emissions': ('mention the DPF, DEF or regen system', r'\bdpf\b|\bdef\b|\bregen|particulate|\bscr\b|nox sensor'),
    'turbo': ('mention the turbo', r'turbo'),
    'power_loss': ('say the engine stalled, shut off or lost power', r'\bstall|shut(s|ting)? (off|down)|lost (all )?power|loss of power|loses power|limp|reduced (engine )?power|no power|dies?\b while'),
    'cam_phaser': ('mention a cam phaser or a rattle at start-up', r'cam ?phaser|phaser|rattl\w* (on|at|when|during) (cold )?start|cold start\w* rattl|start[- ]?up rattl'),
    'oil_leak': ('mention an oil leak', r'oil (leak|pan leak)|leak\w* oil'),
    'oil_use': ('mention burning or losing oil', r'(burn|burning|consum\w*|using|uses|losing|loses) (a lot of |excessive )?oil|oil consumption'),
    'timing_chain': ('mention the timing chain', r'timing chain'),
    'coolant': ('mention coolant loss or overheating', r'coolant|overheat|antifreeze'),
    'misfire': ('mention a misfire', r'misfir'),
    'intercooler': ('mention intercooler condensation', r'intercooler|condensation'),
    'death_wobble': ('mention a "death wobble"', r'death wobble'),
    'fuel_leak': ('mention a fuel leak', r'fuel leak|leak\w* fuel|diesel leak'),
}
WRX = {k: re.compile(p, re.I) for k, (_, p) in WORDS.items()}
ENG_RX = {   # a recall names this engine when its summary names its size (and diesel / Power Stroke / Cummins / Duramax where sizes overlap)
    'powerstroke-73': r'7\.3\s?-?\s?(l\b|liter|litre)[^.]{0,40}diesel|7\.3l? power ?stroke|7\.3l? diesel', 'powerstroke-60': r'6\.0\s?-?\s?(l\b|liter|litre)[^.]{0,30}diesel|6\.0l? (power ?stroke|diesel)',
    'powerstroke-64': r'6\.4\s?-?\s?(l\b|liter|litre)[^.]{0,30}diesel|6\.4l? (power ?stroke|diesel)', 'powerstroke-67': r'6\.7\s?-?\s?(l\b|liter|litre)[^.]{0,30}diesel|6\.7l? (power ?stroke|diesel)',
    'cummins-59': r'5\.9\s?-?\s?(l\b|liter|litre)?[^.]{0,30}(diesel|cummins)|cummins 5\.9', 'cummins-67': r'6\.7\s?-?\s?(l\b|liter|litre)?[^.]{0,30}(diesel|cummins)|cummins 6\.7',
    'duramax-lb7': r'6\.6\s?-?\s?(l\b|liter|litre)?[^.]{0,30}diesel|duramax|\blb7\b', 'duramax-lly': r'6\.6\s?-?\s?(l\b|liter|litre)?[^.]{0,30}diesel|duramax|\blly\b',
    'duramax-lbz': r'6\.6\s?-?\s?(l\b|liter|litre)?[^.]{0,30}diesel|duramax|\blbz\b', 'duramax-lmm': r'6\.6\s?-?\s?(l\b|liter|litre)?[^.]{0,30}diesel|duramax|\blmm\b',
    'duramax-lml': r'6\.6\s?-?\s?(l\b|liter|litre)?[^.]{0,30}diesel|duramax|\blml\b', 'duramax-l5p': r'6\.6\s?-?\s?(l\b|liter|litre)?[^.]{0,30}diesel|duramax|\bl5p\b',
    'ford-ecoboost-27': r'2\.7\s?-?\s?(l\b|liter|litre)', 'f150-ecoboost-35-g1': r'3\.5\s?-?\s?(l\b|liter|litre)[^.]{0,30}(ecoboost|gtdi|turbo)|3\.5l? ecoboost',
    'f150-ecoboost-35-g2': r'3\.5\s?-?\s?(l\b|liter|litre)[^.]{0,30}(ecoboost|gtdi|turbo)|3\.5l? ecoboost', 'f150-coyote': r'5\.0\s?-?\s?(l\b|liter|litre)',
}
SIZE_RX = re.compile(r'\b(\d\.\d)\s?-?\s?(?:l\b|liter|litre)', re.I)
def rec_engines(r, cands):
    """which of the candidate engines (slugs) a recall's summary names: [] = names none of them"""
    s = r['summary']; return [e for e in cands if re.search(ENG_RX[e], s, re.I)]
def rec_other_engine(r, cands):
    """True when the summary names an engine size and none of the candidates (it's about another engine, e.g. the 6.2L gas)"""
    sizes = set(SIZE_RX.findall(r['summary']))
    return bool(sizes) and not rec_engines(r, cands)

def pct(k, n): return round(k / n * 100) if n else 0
def miles_of(rows):
    ms = sorted(int(r['mi']) for r in rows if r['mi'].isdigit() and 0 < int(r['mi']) < 500000)
    return dict(p25=ms[len(ms) // 4], median=ms[len(ms) // 2], p75=ms[len(ms) * 3 // 4], n=len(ms)) if len(ms) >= 20 else None
def comps_of(rows, top=8):
    c = collections.Counter(); n = len(rows)
    for r in rows:
        for p in {part(x) for x in r['comps']} - {'unknown or other'}: c[p] += 1
    return [[p, pct(k, n), k] for p, k in c.most_common(top)]
def words_of(rows):
    n = len(rows); return {k: [sum(1 for r in rows if WRX[k].search(r['d'])), n] for k in WORDS}
def quotes_of(rows, k=3, rx=None):
    qs = [r for r in rows if 80 < len(r['d']) < 300 and (rx is None or rx.search(r['d']))]
    qs.sort(key=lambda r: r['o'], reverse=True)
    return [dict(y=r['y'], odi=r['o'], text=r['d'][0] + r['d'][1:].lower() if r['d'].isupper() else r['d']) for r in qs[:k]]
def serious(rows): return dict(crash=sum(r['cr'] for r in rows), fire=sum(r['fi'] for r in rows), injured=sum(r['inj'] > 0 for r in rows), deaths=sum(r['dth'] > 0 for r in rows), towed=sum(r['tow'] for r in rows))

def build():
    R = load(); D = json.load(open(DEC_JS, encoding='utf-8')); RC = json.load(open(REC_JS, encoding='utf-8'))
    for r in R:
        r['eng'], r['elab'], r['fuel'] = None, None, None
        v = r['vin']
        if len(v) >= 11 and VALID.match(v[:11]):
            d = D.get(f'{r["t"]}|{r["y"]}|{v[7]}')
            if d: r['eng'], r['elab'], r['fuel'] = classify(r['t'], r['y'], v[7], d['dec'])
        r['w3'] = bool(r['ld'][:4].isdigit() and int(r['ld'][:4]) <= r['y'] + 3)
    recs = {}; trucks = {}
    for t, (nm, mk, _) in TRUCKS.items():
        rows_t = [r for r in R if r['t'] == t]; years = {}
        for y in sorted({r['y'] for r in rows_t}):
            rows = [r for r in rows_t if r['y'] == y]
            if len(rows) < 5 and y > 2024: continue
            el = collections.Counter((r['eng'], r['elab'], r['fuel']) for r in rows if r['elab'])
            vn = sum(el.values())
            rr = [x for x in RC.get(f'{t}|{y}') or [] if x['id'][2:3] == 'V']   # vehicle recalls only (the API also returns aftermarket equipment and tire campaigns)
            cands = [e for e, d in ENG.items() if t in d['trucks']]
            for x in rr:
                recs.setdefault(x['id'], dict(x, eng=[], trucks={}))
                recs[x['id']]['trucks'].setdefault(t, []).append(y)
                recs[x['id']]['eng'] = sorted(set(recs[x['id']]['eng']) | set(rec_engines(x, cands)))
                recs[x['id']]['other'] = rec_other_engine(x, cands)
            years[str(y)] = dict(n=len(rows), n3=sum(r['w3'] for r in rows), comps=comps_of(rows), vin=vn,
                                 eng=[[s, lab, fu, k, pct(k, vn)] for (s, lab, fu), k in el.most_common()],
                                 eng_comps={s: comps_of([r for r in rows if r['eng'] == s], 4) for (s, _, _), k in el.items() if s and k >= 15},
                                 miles=miles_of(rows), ser=serious(rows), quotes=quotes_of(rows), recalls=[x['id'] for x in rr],
                                 diesel=sum(k for (_, _, fu), k in el.items() if fu == 'diesel'))
        trucks[t] = dict(name=nm, make=mk, n=len(rows_t), comps=comps_of(rows_t), years=years, miles=miles_of(rows_t), ser=serious(rows_t),
                         vin=sum(1 for r in rows_t if r['elab']), names=sorted({r['md'] for r in rows_t}))
        print(t, len(rows_t), 'complaints,', trucks[t]['vin'], 'engine-matched', flush=True)
    engines = {}
    for e, d in ENG.items():
        rows = [r for r in R if r['eng'] == e]
        if not rows: print('NO ROWS', e); continue
        ys = sorted({r['y'] for r in rows}); by = collections.Counter(r['y'] for r in rows)
        # the model years this engine was built for these trucks (maker facts); a complaint outside them is a mis-typed year or VIN
        a, b = PROD[e]; yrs = [y for y in ys if a <= y <= b and by[y] >= 3]
        rows = [r for r in rows if r['y'] in yrs]
        tr = {t: sorted({r['y'] for r in rows if r['t'] == t}) for t in d['trucks']}
        rl = []
        for rid, x in recs.items():
            if e in x['eng'] and any(t in x['trucks'] and set(x['trucks'][t]) & set(yrs) for t in d['trucks']): rl.append(rid)
        engines[e] = dict(d, years=yrs, n=len(rows), by_year={str(y): by[y] for y in yrs}, by_truck={t: sum(1 for r in rows if r['t'] == t) for t in d['trucks']},
                          n3=sum(r['w3'] for r in rows), comps=comps_of(rows, 10), words=words_of(rows), miles=miles_of(rows), ser=serious(rows), quotes=quotes_of(rows),
                          trucks_years={t: v for t, v in tr.items() if v}, recalls=sorted(rl, key=lambda i: recs[i]['date'][6:10] + recs[i]['date'][3:5] + recs[i]['date'][:2], reverse=True),
                          wq={k: quotes_of(rows, 2, WRX[k]) for k in WORDS})
        print(e, len(rows), 'complaints', yrs[0], '-', yrs[-1], 'recalls naming it', len(rl), flush=True)
    p = os.path.join(HERE, 'data', 'hd.json'); H = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    H.update(trucks=trucks, engines=engines, recalls=recs, words={k: v[0] for k, v in WORDS.items()},
             src=dict(complaints='NHTSA owner complaints (FLAT_CMPL + COMPLAINTS_RECEIVED_2025-2026), received through ' + max(r['ld'] for r in R if r['ld'][:4].isdigit()),
                      vin='NHTSA vPIC VIN decoder', recalls='NHTSA recalls API'))
    json.dump(H, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('written data/hd.json', round(os.path.getsize(p) / 1e6, 1), 'MB')

def blend():
    """How much of each whole-line pickup score is heavy-duty: complaints.db with the study's own family regexes and window (families.py,
    lemon.py: received by model year + 3), split into half-ton and 2500/3500 names. -> {family id: {all: [ht, hd], years: {y: [ht, hd]}}}"""
    import sqlite3
    sys.path.insert(0, os.path.join(LEMON, 'autopilot', 'lib')); from families import FAMILIES
    fam = {f: (set(mk.split('|')), re.compile(rx)) for f, mk, rx, _, _ in FAMILIES if f in ('Ford F-Series', 'Ram pickup', 'Chevrolet Silverado', 'GMC Sierra')}
    hdrx = re.compile(r'(2500|3500|F-250|F-350|F-450)')
    out = {}
    con = sqlite3.connect(os.path.join(LEMON, 'data', 'complaints.db'))
    for f, (mks, rx) in fam.items():
        ys = collections.defaultdict(lambda: [0, 0])
        for mk, md, y, ld in con.execute(f"SELECT make, model, year, ldate FROM complaints WHERE make IN ({','.join('?' * len(mks))}) AND year BETWEEN 2000 AND 2025", tuple(mks)):
            if not rx.fullmatch(md) or not ld or int(ld[:4]) > y + 3: continue
            ys[y][1 if hdrx.search(md) else 0] += 1
        fid = f.lower().replace(' ', '-')
        sc = [ys[y] for y in range(2010, 2023)]
        out[fid] = dict(score=[sum(a for a, _ in sc), sum(b for _, b in sc)], years={str(y): v for y, v in sorted(ys.items())})
        print('blend', fid, out[fid]['score'], round(out[fid]['score'][1] / sum(out[fid]['score']) * 100, 1), '% HD (2010-22)')
    return out

if __name__ == '__main__':
    if 'blend' in STAGES:
        p = os.path.join(HERE, 'data', 'hd.json'); H = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
        H['blend'] = blend(); json.dump(H, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    if 'extract' in STAGES: extract()
    if 'decode' in STAGES: decode()
    if 'recalls' in STAGES: recalls()
    if 'build' in STAGES: build()
