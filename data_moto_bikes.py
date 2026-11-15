# Motorcycle bike pages (11-14): the 43 bikes from "3 Lemon Index/Motorcycles plan 11-11.md" with 15+ NHTSA owner complaints
# (26 new bikes + 17 splits of an existing family) -> data/moto_bikes.json, built into /motorcycles/<slug>/ by vehicles_pages.py.
# Same rules as data_moto.py: the local NHTSA complaints flat file (complaints.db), model years 2000-2026 inside each bike's US years,
# one fullmatch regex per bike (bikes.py from the 11-11 plan). Recalls: api.nhtsa.gov recallsByVehicle, read from the plan's cache
# (car images test/motorcycles_new/nhtsa_cache, plain curl; a miss is fetched the same way, nothing else). Equipment campaigns ("E") are left out.
# COUNTS, NEVER RATES: there are no U.S. sales figures per motorcycle model year.
# Also writes AVOID: the "years to avoid" blocks for the 10 bikes in the 11-14 @lemonindexmotorcycle videos, with the videos' own numbers
# (NHTSA complaints API, 3 Lemon Index/motorcycles/data/<bike>.json), keyed by the page slug that shows them.
import sqlite3, re, json, os, sys, collections, statistics, hashlib, subprocess, time, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
LI = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
PLAN = os.path.join(LI, 'car images test', 'motorcycles_new'); CACHE = os.path.join(PLAN, 'nhtsa_cache')
sys.path.insert(0, PLAN); import bikes
DB = os.path.join(LI, 'data', 'complaints.db')
PART = {'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'ELECTRICAL SYSTEM': 'electrical', 'ENGINE': 'engine', 'ENGINE AND ENGINE COOLING': 'engine',
        'FUEL/PROPULSION SYSTEM': 'fuel system', 'SUSPENSION': 'suspension', 'STEERING': 'steering', 'WHEELS': 'wheels', 'TIRES': 'tires', 'VEHICLE SPEED CONTROL': 'throttle & speed control',
        'EXTERIOR LIGHTING': 'lights', 'STRUCTURE': 'frame & body', 'LATCHES/LOCKS/LINKAGES': 'latches & linkages', 'EQUIPMENT': 'equipment', 'VISIBILITY': 'visibility',
        'FUEL SYSTEM, GASOLINE': 'fuel system', 'FUEL SYSTEM, OTHER': 'fuel system', 'SERVICE BRAKES, HYDRAULIC': 'brakes', 'PARKING BRAKE': 'brakes', 'SEATS': 'seats', 'AIR BAGS': 'air bags', 'VISIBILITY/WIPER': 'visibility (mirrors, windscreen)'}
# what a complaint is about, from its text (regex on the upper-case description); the first label is how the page says it
THEMES = [('stalling', r'\bSTALL'), ('the throttle', r'THROTTLE'), ('losing power', r'LOS[ET]S? (ALL )?(ENGINE )?POWER|LOSS OF (ENGINE )?POWER|POWER LOSS'),
          ('the brakes', r'BRAKE'), ('the ABS', r'\bABS\b|ANTI-?LOCK'), ('a fuel leak or fuel smell', r'FUEL (LEAK|SMELL|ODOR)|GAS (LEAK|SMELL|ODOR)|LEAK\w* (OF )?(FUEL|GAS)'),
          ('the fuel pump', r'FUEL PUMP'), ('the clutch', r'CLUTCH'), ('the transmission or shifting', r'TRANSMISSION|GEARBOX|\bGEARS?\b|SHIFT|NEUTRAL'),
          ('the charging system (stator, regulator or battery)', r'STATOR|RECTIFIER|REGULATOR|CHARGING|ALTERNATOR|BATTER'),
          ('overheating', r'OVERHEAT|OVER HEAT|TOO HOT|EXCESSIVE HEAT|EXTREME HEAT'), ('an oil leak', r'OIL LEAK|LEAK\w* OIL'),
          ('the cam chain or tensioner', r'CAM ?CHAIN|TENSIONER'), ('the turn signals', r'TURN ?SIGNAL|BLINKER'), ('the cruise control', r'CRUISE'),
          ('a wobble or the steering', r'WOBBLE|WEAVE|HEAD ?SHAKE|TANK ?SLAP|STEERING'), ('the wheels', r'\bWHEEL|SPOKE'), ('the tires', r'\bTIRE'),
          ('the final drive or drive shaft', r'FINAL DRIVE|DRIVE ?SHAFT|SPLINE'), ('the drive belt or chain', r'\bBELT\b|DRIVE CHAIN'), ('a fire', r'\bFIRE\b|CAUGHT FIRE|FLAMES'),
          ('the cooling system', r'COOLANT|RADIATOR|WATER PUMP'), ('starting', r'STARTER|WON.?T START|NO.?START|WOULD NOT START|WILL NOT START'),
          ('a cracked frame', r'FRAME.{0,25}CRACK|CRACK.{0,25}FRAME'), ('the fuel gauge', r'FUEL (GAUGE|LEVEL|SENDER|SENSOR|LIGHT)|LOW FUEL (LIGHT|WARNING)'), ('the gauges', r'SPEEDOMETER|ODOMETER|INSTRUMENT CLUSTER|TACHOMETER'), ('the headlight or lights', r'HEADLIGHT|HEAD LIGHT|TAIL ?LIGHT|BRAKE LIGHT|LIGHTS'), ('the mirrors', r'MIRROR'),
          ('the side stand', r'KICKSTAND|KICK STAND|SIDE ?STAND|JIFFY'), ('the suspension or shocks', r'SUSPENSION|\bSHOCK|\bFORK')]
THEMES = [(l, re.compile(r)) for l, r in THEMES]
SERIOUS_RECALL = re.compile(r'CRASH|FIRE|STALL|BRAK|STEER|FUEL LEAK|LOSS OF (MOTIVE )?POWER|LOCK', re.I)

def get(url):
    p = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:16] + '.json')
    if os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    for k in range(3):   # the plan's own access: plain curl, nothing spoofed; a refusal stays a miss
        try:
            r = subprocess.run(['curl', '-s', '--max-time', '25', '-w', '\n%{http_code}', url], capture_output=True, timeout=40, text=True, encoding='utf-8')
            body, code = r.stdout.rsplit('\n', 1)
            if code == '403': return None
            if code == '400': d = {'results': []}
            else: d = json.loads(body)
            json.dump(d, open(p, 'w', encoding='utf-8')); time.sleep(0.2); return d
        except Exception: time.sleep(2)
    return None
# complaints NHTSA's file codes to the bike but whose text is about other bikes (checked by reading every one) are left out
EXCL = {('harley-davidson-street-bob', 2009, 'FXDB')}   # 17 "2009 FXDB" complaints: 16 describe touring bikes (Street Glide, Road Glide, Tri Glide, Ultra), a V-Rod or a Super Glide
TXT = {}
RV = lambda mk, nm, y: get('https://api.nhtsa.gov/recalls/recallsByVehicle?' + urllib.parse.urlencode({'make': mk, 'model': nm, 'modelYear': y}))

con = sqlite3.connect(DB)
NOW = 2026
USE = [b for b in bikes.B]
makes = sorted({m for x in USE for m in x['nhtsa_make']})
rows = collections.defaultdict(list)
for odino, make, model, year, crash, fire, inj, miles, comps in con.execute(
        f"SELECT odino, make, model, year, crash, fire, injured, miles, comps FROM complaints WHERE year BETWEEN 2000 AND {NOW} AND make IN ({','.join('?' * len(makes))})", makes):
    rows[make].append((odino, (model or '').upper().strip(), year, crash, fire, inj, miles, comps))

def fmtd(d):   # NHTSA recall dates come as DD/MM/YYYY
    m = re.match(r'(\d\d)/(\d\d)/(\d{4})', d or ''); return f'{m.group(3)}-{m.group(2)}-{m.group(1)}' if m else (d or '')
out = []; skipped = []
for x in USE:
    rx = re.compile(x['cx']); y0, y1 = max(2000, x['y0']), x['y1']; seen = {}
    for mk in x['nhtsa_make']:
        for r in rows[mk]:
            if y0 <= r[2] <= y1 and rx.fullmatch(r[1]): seen[r[0]] = r
    R = [r for r in seen.values() if (x['slug'], r[2], r[1]) not in EXCL]
    if len(R) < 15: skipped.append((x['slug'], len(R))); continue
    names = collections.Counter(r[1] for r in R); ys = collections.Counter(r[2] for r in R)
    # complaint text for the themes
    txt = {}
    q = [r[0] for r in R]
    for i in range(0, len(q), 500):
        ch = q[i:i + 500]
        for od, d in con.execute(f"SELECT odino, descr FROM rows WHERE odino IN ({','.join('?' * len(ch))})", ch): txt[od] = (txt.get(od, '') + ' ' + (d or '').upper())
    TXT[x['slug']] = {y: [txt.get(r[0], '') for r in R if r[2] == y] for y in ys}
    def comps_of(r): return {PART.get(c.split(':')[0].strip(), c.split(':')[0].strip().lower()) for c in (r[7] or '').split(' | ') if c.split(':')[0].strip() and c.split(':')[0].strip() != 'UNKNOWN OR OTHER'}
    comp = collections.Counter(c for r in R for c in comps_of(r))
    n = len(R); ser = sum(1 for r in R if r[3] == 'Y' or r[4] == 'Y' or (r[5] or 0) > 0)
    mi = [r[6] for r in R if r[6] and 0 < r[6] < 200000]
    # recalls: the recall model names NHTSA lists for this make and year that match the bike, plus its top 2 complaint names in every year with complaints
    camp = {}
    qs = set()
    for mk in x['nhtsa_make']:
        for y in range(y0, y1 + 1):
            d = get('https://api.nhtsa.gov/products/vehicle/models?' + urllib.parse.urlencode(dict(modelYear=y, make=mk, issueType='r')))
            for m in (d or {}).get('results', []):
                nm = (m.get('model') or '').upper().strip()
                if rx.fullmatch(nm): qs.add((mk, nm, y))
        for nm, _ in names.most_common(2):
            for y in ys: qs.add((mk, nm, y))
    for mk, nm, y in sorted(qs):
        for r in (RV(mk, nm, y) or {}).get('results', []):
            cid = r.get('NHTSACampaignNumber') or ''
            if not re.fullmatch(r'\d\dV\d{6}', cid): continue   # vehicle campaigns only (no E equipment / T tire campaigns)
            c = camp.setdefault(cid, dict(id=cid, date=fmtd(r.get('ReportReceivedDate')), part=(r.get('Component') or '').split(':')[0].strip(),
                                          summary=re.sub(r'\s+', ' ', r.get('Summary') or '').strip(), consequence=re.sub(r'\s+', ' ', r.get('Consequence') or '').strip(), years=[]))
            if y not in c['years']: c['years'].append(y)
    for c in camp.values(): c['years'].sort()
    # per model year
    yd = {}
    for y in sorted(ys):
        Ry = [r for r in R if r[2] == y]
        cc = collections.Counter(c for r in Ry for c in comps_of(r))
        th = collections.Counter(l for r in Ry for l, p in THEMES if p.search(txt.get(r[0], '')))
        yd[str(y)] = dict(n=len(Ry), comps=cc.most_common(4), themes=th.most_common(4), crash=sum(1 for r in Ry if r[3] == 'Y'), fire=sum(1 for r in Ry if r[4] == 'Y'),
                          injured=sum((r[5] or 0) for r in Ry), recalls=sorted(c['id'] for c in camp.values() if y in c['years']))
    out.append(dict(slug=x['slug'], name=x['name'], brand=x['make'], category=x['category'], status=x['status'], inside=(x['note'] or '').replace('inside ', '').split(';')[0].split(' (')[0].strip(),
                    y0=x['y0'], y1=x['y1'], specs=dict(engine=x['engine'], family=x['family'], hp=x['hp'], tq=x['tq'], wet=x['wet'], seat=x['seat'], msrp=x['msrp']),
                    n=n, by_year={str(y): ys[y] for y in sorted(ys)}, parts=[[p, round(k / n * 100)] for p, k in comp.most_common(5)], serious=round(ser / n * 100),
                    crash=sum(1 for r in R if r[3] == 'Y'), fire=sum(1 for r in R if r[4] == 'Y'), injured=sum((r[5] or 0) for r in R),
                    miles=int(statistics.median(mi)) if len(mi) >= 10 else None, names=[k for k, _ in names.most_common(6)],
                    recalls=sorted(camp.values(), key=lambda c: c['date'], reverse=True), years=yd))
    o = out[-1]
    print(f"{x['slug']:34} {n:4} complaints {len(camp):3} recalls  worst {max(yd.items(), key=lambda kv: kv[1]['n'])[0]}  {o['names'][:3]}", flush=True)
print('built', len(out), 'skipped (under 15):', len(skipped))
json.dump(out, open(os.path.join(HERE, 'data', 'moto_bikes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

# ---- worst and best years (counts only). A year to avoid has clearly more complaints than the bike's others (the top year, plus up to 2 more
# within 60% of it, each 5+); the problem is named from the complaint text (themes) or the top system. Best = fewest complaints on file among
# years that drew at least one (so a year the bike wasn't sold doesn't read as "best"), at least 3 model years old.
P = lambda *a: [(re.compile(a[i]), a[i + 1]) for i in range(0, len(a), 2)]
FUELG = r'FUEL (GAUGE|GUAGE|LEVEL|STRIP|SENDER|SENDING|SENSOR)|GAS GAUGE|LOW FUEL|RUN(NING)? OUT OF (FUEL|GAS)|RAN OUT OF (FUEL|GAS)'
PROB = {   # (bike, year): what the complaints describe, each with the regex that counts them (read by hand on 11-14 before writing the phrase)
 ('yamaha-fz1-fz6', 2004): P(r'STALL|\bDIE[SD]?\b|QUIT', 'describe the engine stalling or dying, often at low speed'),
 ('honda-vfr800', 2002): P(r'ELECTRIC|WIR|FUSE|BURN|MELT|CHARG|STATOR|REGULATOR|HEADLIGHT', 'describe an electrical failure (wiring, fuses or charging) that killed the lights or the engine'),
 ('honda-vfr800', 2003): P(r'ELECTRIC|WIR|FUSE|BURN|MELT|CHARG|STATOR|REGULATOR|HEADLIGHT', 'describe an electrical failure (wiring, fuses or charging) that killed the lights or the engine'),
 ('honda-vfr800', 2010): P(r'THROTTLE|SURG|STUMBL|STUTTER|HESITAT|LOOSE POWER|LOS[ET] POWER', 'describe the new VFR1200F surging, stumbling or losing power', r'BRAKE LIGHT|BRAKE SWITCH', 'a brake light that stops working'),
 ('suzuki-sv650', 2003): P(r'ELECTRIC|SHUT|CUT.?OUT|DEAD|IGNITION|CHARG|STATOR|REGULATOR|BATTER|LOST POWER|LOSS OF POWER|STALL', 'describe the bike losing electrical power, stalling or cutting out'),
 ('triumph-speed-triple', 2005): P(r'BRAKE', 'describe a soft or inconsistent front brake lever'),
 ('bmw-r1200r', 2007): P(FUELG, 'describe the fuel gauge reading wrong, some until the bike ran dry', r'FUEL PUMP|FLANGE|LEAK', 'a fuel pump problem or a fuel leak'),
 ('bmw-r1200r', 2008): P(FUELG, 'describe the fuel gauge reading wrong, some until the bike ran dry', r'\bABS\b', 'the ABS'),
 ('bmw-r1200r', 2013): P(FUELG + '|GUAGE', "describe the fuel gauge (the tank's fuel level strip) reading wrong, some until the bike ran dry"),
 ('ducati-streetfighter', 2010): P(r'TANK.{0,60}(EXPAND|SWELL|BULG|DEFORM)|(EXPAND|SWELL|BULG|DEFORM).{0,40}TANK', 'describe the plastic fuel tank swelling or deforming'),
 ('ducati-supersport', 2017): P(r'MIRROR', 'describe the mirrors vibrating too much to see behind'),
 ('buell-1125r', 2009): P(r'STATOR|REGULATOR|RECTIFIER|CHARG|BATTER|VOLTAGE', 'describe the charging system failing (stator, regulator or battery)', r'BOIL|VENT|RAW (GAS|FUEL)|FUEL SMELL|GAS SMELL', 'fuel boiling or venting from the tank'),
 ('buell-xb', 2003): P(r'HEADLIGHT|HEAD LAMP|HEADLAMP|HEAD LIGHT|REFLECT|LIGHTING', 'describe the headlights going dim as the reflector coating flakes off'),
 ('buell-xb', 2004): P(r'HEADLIGHT|HEAD LAMP|HEADLAMP|HEAD LIGHT|REFLECT|LIGHTING', 'describe the headlights going dim as the reflector coating flakes off'),
 ('buell-xb', 2006): P(r'HEADLIGHT|HEAD LAMP|HEADLAMP|HEAD LIGHT|REFLECT|LIGHTING', 'describe the headlights going dim as the reflector coating flakes off'),
 ('honda-st1300', 2003): P(r'HEAT|\bHOT\b|DEGREE|BURN', 'describe engine heat on the rider', r'WIR|HARNESS', 'the wiring harness'),
 ('honda-st1300', 2004): P(r'BRAKE', 'describe the linked brakes, some locking up'),
 ('honda-st1300', 2006): P(r'BRAKE', 'describe the brakes, most often the rear brake dragging or locking', r'\bTIRE', 'tires'),
 ('bmw-f-gs', 2009): P(r'STALL|ENGINE (STOPPED|QUIT|DIED|SHUTS?)|CUT OUT|CUTS OUT', 'describe the engine stalling or cutting out', r'TANK.{0,40}CRACK|CRACK.{0,40}TANK|SPLIT', 'the fuel tank cracking'),
 ('bmw-f900xr', 2007): P(r'STALL', 'describe the engine stalling, often when downshifting', r'WHEEL BEARING|REAR WHEEL|FINAL DRIVE|WOBBLE', 'the rear wheel bearing or a wobble', r'FUEL (LEAK|SMELL)|LEAK\w* FUEL|FUEL PUMP|FUEL W', 'a fuel leak or the fuel pump'),
 ('bmw-f900xr', 2008): P(r'STALL|SHUT\w* OFF|DIES|DIED', 'describe the engine stalling or shutting off'),
 ('bmw-k1200-k1300', 2009): P(r'STALL|ENGINE (STOPS|STOPPED|QUIT|DIED|CUT)|CUT OUT', 'describe the engine stalling, often when slowing down or pulling in the clutch'),
 ('bmw-k1200lt', 2000): P(r'FINAL DRIVE|REAR DRIVE|REAR END|CROWN BEARING|DRIVE SHAFT|DRIVESHAFT', 'describe the final drive (rear drive) failing', r'SHIFT\w* LINKAGE|SHIFTER|LINKAGE', 'the shift linkage breaking'),
 ('bmw-k1200lt', 2002): P(r'FINAL DRIVE|REAR DRIVE|REAR END|CROWN BEARING|DRIVE SHAFT|DRIVESHAFT', 'describe the final drive (rear drive) failing', r'SHIFT\w* LINKAGE|SHIFTER|LINKAGE', 'the shift linkage breaking'),
 ('victory-vision', 2008): P(r'BRAKE', 'describe the brakes failing or fading, most often the rear'),
 ('victory-cross-country', 2012): P(r'SADDLE ?BAG|LATCH|\bBAGS?\b', 'describe a saddlebag latch wearing so the bag can open'),
 ('victory-cross-country', 2013): P(r'SADDLE ?BAG|LATCH|\bBAGS?\b', 'describe a saddlebag latch wearing so the bag can open', r'STALL|DIED|POPPED', 'the engine stalling or dying'),
 ('victory-cross-country', 2014): P(r'SADDLE ?BAG|LATCH|\bBAGS?\b', 'describe a saddlebag latch wearing so the bag can open', r'STALL|DIED|POPPED', 'the engine stalling or dying'),
 ('triumph-sprint-st', 2000): P(r'FUEL|GAS', 'describe a fuel leak or the plastic fuel tank swelling'),
 ('triumph-sprint-st', 2001): P(r'FUEL|GAS', 'describe a fuel leak or the plastic fuel tank swelling'),
 ('triumph-sprint-st', 2006): P(r'BRAKE', 'describe weak front brakes'),
 ('husqvarna-tr650', 2013): P(r'STALL', 'describe stalling, mostly pulling away or at low speed'),
 ('harley-davidson-v-rod', 2006): P(FUELG + '|GAUGE', 'describe the fuel gauge reading wrong', r'BRAKE', 'the brakes'),
 ('harley-davidson-v-rod', 2007): P(FUELG + '|GAUGE', 'describe the fuel gauge reading wrong, some until the bike ran dry', r'BRAKE', 'the brakes'),
 ('victory-vegas', 2005): P(r'TRANSMISS|GEAR|SHIFT', 'describe the transmission: gears skipping, or locking the rear wheel'),
 ('cfmoto-700cl-x', 2022): P(r'CRUISE|GEAR (SENSOR|POSITION|INDICATOR)', 'describe the cruise control cutting out when the gear sensor misreads', r'FUEL GAUGE', 'the fuel gauge'),
 ('honda-cbr600rr', 2004): P(r'BRAKE', 'describe the brakes, several in crashes'),
 ('honda-cbr600rr', 2026): P(r'\bOIL', 'describe the engine burning or leaking oil'),
 ('honda-cbr1000rr', 2008): P(r'\bOIL', 'describe the engine burning or leaking oil'),
 ('kawasaki-ninja-zx-14r', 2006): P(r'FRAME|STEERING HEAD|CRACK', 'describe the frame cracking or breaking'),
 ('yamaha-mt-09', 2014): P(r'CAM ?(SHAFT )?CHAIN|TENSIONER', 'describe the cam chain tensioner rattling or failing'),
 ('yamaha-mt-09', 2015): P(r'FRAME|CRACK', 'describe a cracked frame', r'CLUTCH', 'the clutch'),
 ('yamaha-road-star', 2002): P(r'TRANSMISS|GEAR|SHIFT', 'describe the transmission (second gear) failing, many waiting months for recall parts'),
 ('yamaha-road-star', 2003): P(r'TRANSMISS|GEAR|SHIFT', 'describe the transmission (second gear) failing, many waiting months for recall parts'),
 ('honda-vtx1800', 2002): P(r'PLUG', 'describe fouled spark plugs', r'\bTIRE', 'the tires'),
 ('honda-vtx1800', 2003): P(r'WOBBLE|SHAKE|WEAVE|SHIMMY|VIBRAT', 'describe a front-end wobble or vibration', r'\bTIRE', 'the tires'),
 ('honda-vtx1800', 2004): P(r'WOBBLE|SHAKE|WEAVE|SHIMMY|WABBLE', 'describe a front-end wobble, often while slowing from 40-50 mph'),
 ('triumph-tiger-900', 2011): P(r'STALL|STOPS', 'describe the engine stalling'),
 ('triumph-tiger-900', 2012): P(r'STALL', 'describe the engine stalling', r'TURN (SIGNAL|INDICATOR)|INDICATOR', 'the turn signal stalks breaking'),
 ('ktm-390-adventure', 2025): P(r'STALL|CUTS? OFF|CUT OUT', 'describe the engine stalling, mostly when coming to a stop'),
 ('harley-davidson-road-glide', 2009): P(r'BRAKE', 'describe the brakes or the ABS', r'LIMP|THROTTLE', 'the throttle-by-wire going into limp mode'),
 ('harley-davidson-road-glide', 2011): P(r'WOBBLE|SHAKE|WEAVE|SWERVE|SHIMMY', 'describe a front-end shake or wobble around 40 mph'),
 ('harley-davidson-road-glide', 2016): P(r'RAIN|WATER|INSTRUMENT|GAUGE|SPEEDO|INFOTAINMENT|SCREEN|GLARE|RADIO', 'describe the instruments or infotainment screen (water, glare)'),
 ('harley-davidson-fat-boy', 2007): P(r'OFF.?CENT|OFFSET|MISALIGN|NOT CENTERED|TILTS|LEANS', 'describe a front wheel that sits off center'),
 ('harley-davidson-heritage-classic', 2000): P(r'\bCAM', 'describe Twin Cam 88 cam bearing failures'),
 ('harley-davidson-heritage-classic', 2009): P(r'BRAKE', 'describe the brakes or the brake light switch'),
 ('harley-davidson-heritage-classic', 2012): P(r'WOBBLE|SHAKE|WEAVE|INSTABIL|SPOKE|FRONT WHEEL|WHEEL BEARING', 'describe a wobble or a front wheel problem'),
 ('harley-davidson-street-bob', 2006): P(r'BOLT', 'describe bolts coming loose or shearing (rear sprocket or alternator rotor)'),
 ('ducati-panigale-v4', 2018): P(r'MIRROR', 'describe mirrors that crack or break easily'),
 ('ducati-panigale-v4', 2025): P(r'BRAKE', 'describe the rear brake line (heat damage from the exhaust)'),
}
MIXED = {   # years whose complaints share no one problem: said in words, no count
 ('ktm-1290-super-duke-r', 2015): 'No single problem: a collapsed oil filter, pulsing front brakes, the speedometer, and one fatal crash fire.',
 ('ktm-1290-super-adventure', 2015): 'No single problem: heated seats switching on, a collapsed oil filter, the fuel pump and an electrical shutdown.',
 ('harley-davidson-sportster-s', 2022): 'No single problem: a broken steering stop, the clutch, a loss of power and a hand-control module.',
 ('harley-davidson-sportster-s', 2023): 'Half are about the steering recall (25V590000); also clogged fuel filters and a cam tensioner bolt.',
 ('triumph-tiger-900', 2022): 'No single problem: stalling when stopping or downshifting, broken spokes and a soft front brake.',
}
def analyse(b):
    yd = b['years']; ys = sorted((int(y), v['n']) for y, v in yd.items())
    top = max(n for _, n in ys)
    worst = []
    if top >= 5:
        for y, n in sorted(ys, key=lambda t: (-t[1], t[0])):
            if len(worst) == 3: break
            if n >= 5 and (not worst or n >= 0.6 * top): worst.append(y)
    W = []
    for y in worst:
        v = yd[str(y)]; n = v['n']
        th = [(l, k) for l, k in v['themes'] if k >= max(3, 0.3 * n)]
        cp = v['comps'][0] if v['comps'] else None
        tx = TXT[b['slug']].get(y, [])
        pr = [[sum(1 for t in tx if rx_.search(t)), ph] for rx_, ph in PROB.get((b['slug'], y), [])]
        W.append(dict(y=y, n=n, prob=pr, mixed=MIXED.get((b['slug'], y)), theme=list(th[0]) if th else None, theme2=list(th[1]) if len(th) > 1 else None, comp=list(cp) if cp else None,
                      crash=v['crash'], fire=v['fire'], recalls=[r['id'] for r in b['recalls'] if y in r['years'] and SERIOUS_RECALL.search(r['consequence'] + ' ' + r['summary'])][:3]))
    best = []
    if worst:
        cand = [(y, n) for y, n in ys if y not in worst and y <= NOW - 3 and n <= 0.34 * top]
        best = [dict(y=y, n=n) for y, n in sorted(cand, key=lambda t: (t[1], t[0]))[:3]]
        best.sort(key=lambda d: d['y'])
    after = None
    if worst:
        lw = max(worst); rest = [n for y, n in ys if y > lw]
        if rest and lw < max(y for y, _ in ys): after = dict(y=lw, max=max(rest))
    return dict(worst=W, best=best, after=after, top=top)
for b in out: b.update(analyse(b))
json.dump(out, open(os.path.join(HERE, 'data', 'moto_bikes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
for b in out:
    print(f"\n{b['name']} ({b['n']})  after={b['after']}  best={[(d['y'], d['n']) for d in b['best']]}")
    for w in b['worst']: print('   ', w['y'], w['n'], w['prob'], w['mixed'], w['theme'], w['theme2'], w['comp'], 'crash', w['crash'], 'fire', w['fire'], w['recalls'])
