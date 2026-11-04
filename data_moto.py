# Motorcycle section data (11-04, Elijah: "add plane section and motorcycle section with images"). -> data/moto.json
# Source: the same NHTSA owner-complaint file as the cars (complaints.db), model years 2005-2025, grouped into model families by the model
# text owners/NHTSA filed. There are no free U.S. sales figures by motorcycle model, so NOTHING here is per bike sold: each family shows
# complaint counts, what they're about, how many involved a crash/fire/injury, typical miles, and NHTSA recalls (api.nhtsa.gov, cached).
import sqlite3, re, json, os, collections, statistics, hashlib, urllib.request, urllib.parse, time, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'data', 'cache')
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
Y0, Y1 = 2005, 2025
# (family, brand, make in NHTSA, model regex (fullmatch on the filed model), segment)
F = [
 ('Harley-Davidson Touring', 'Harley-Davidson', 'HARLEY-DAVIDSON', r'FLH.*|FLT.*|ELECTRA GLIDE.*|ROAD (GLIDE|KING).*|STREET GLIDE.*|ULTRA.*', 'Touring'),
 ('Harley-Davidson Softail', 'Harley-Davidson', 'HARLEY-DAVIDSON', r'FLS.*|FXS.*|FXST.*|FXBR.*|FXFB.*|FXLR.*|FLDE.*|FLFB.*|FXDR.*|SOFTAIL.*|FAT BOY.*|HERITAGE.*|BREAKOUT.*|LOW RIDER.*', 'Cruiser'),
 ('Harley-Davidson Sportster', 'Harley-Davidson', 'HARLEY-DAVIDSON', r'XL.*|SPORTSTER.*|IRON 883.*|FORTY.?EIGHT.*|RH1250.*', 'Cruiser'),
 ('Harley-Davidson Dyna', 'Harley-Davidson', 'HARLEY-DAVIDSON', r'FXD.*|DYNA.*', 'Cruiser'),
 ('Harley-Davidson Street 500/750', 'Harley-Davidson', 'HARLEY-DAVIDSON', r'XG.*|STREET (500|750|ROD).*', 'Standard'),
 ('Harley-Davidson Pan America', 'Harley-Davidson', 'HARLEY-DAVIDSON', r'RA1250.*|PAN AMERICA.*', 'Adventure'),
 ('Harley-Davidson LiveWire', 'Harley-Davidson', 'HARLEY-DAVIDSON', r'ELW.*|LIVEWIRE.*', 'Electric'),
 ('Honda Gold Wing', 'Honda', 'HONDA', r'GL1800.*|GOLD ?WING.*|GL 1800.*', 'Touring'),
 ('Honda CBR', 'Honda', 'HONDA', r'CBR.*', 'Sport'),
 ('Honda Shadow', 'Honda', 'HONDA', r'VT.*|SHADOW.*', 'Cruiser'),
 ('Honda Africa Twin', 'Honda', 'HONDA', r'CRF1000.*|CRF1100.*|AFRICA TWIN.*', 'Adventure'),
 ('Honda Rebel', 'Honda', 'HONDA', r'CMX.*|REBEL.*', 'Cruiser'),
 ('Honda NC700/NC750', 'Honda', 'HONDA', r'NC7.*', 'Standard'),
 ('Yamaha FJR1300', 'Yamaha', 'YAMAHA', r'FJR.*', 'Touring'),
 ('Yamaha YZF-R1', 'Yamaha', 'YAMAHA', r'YZF-?R1.*|R1', 'Sport'),
 ('Yamaha YZF-R6', 'Yamaha', 'YAMAHA', r'YZF-?R6.*|R6', 'Sport'),
 ('Yamaha Bolt', 'Yamaha', 'YAMAHA', r'BOLT.*|XVS95CR.*', 'Cruiser'),
 ('Yamaha V Star', 'Yamaha', 'YAMAHA', r'XVS.*|V.?STAR.*|XV1700.*|ROAD STAR.*|WARRIOR.*', 'Cruiser'),
 ('Yamaha Raider / Stratoliner', 'Yamaha', 'YAMAHA', r'XV19.*|XV1900.*|STRATOLINER.*|ROADLINER.*|RAIDER.*', 'Cruiser'),
 ('Yamaha MT-07 / MT-09', 'Yamaha', 'YAMAHA', r'MT-?0[79].*|FZ-?0[79].*|FZ-?09.*', 'Standard'),
 ('Yamaha Super Tenere', 'Yamaha', 'YAMAHA', r'XT1200.*|SUPER TENERE.*|TENERE.*', 'Adventure'),
 ('Kawasaki KLR650', 'Kawasaki', 'KAWASAKI', r'KLR.*|KL650.*', 'Adventure'),
 ('Kawasaki Ninja ZX-6R / ZX-10R', 'Kawasaki', 'KAWASAKI', r'(NINJA )?ZX-?(6|10|14).*|ZX[0-9]{3,4}.*', 'Sport'),
 ('Kawasaki Ninja 300/400/650', 'Kawasaki', 'KAWASAKI', r'NINJA (250|300|400|500|650).*|EX(250|300|400|500|650).*', 'Sport'),
 ('Kawasaki Concours 14', 'Kawasaki', 'KAWASAKI', r'CONCOURS.*|ZG1400.*', 'Touring'),
 ('Kawasaki Vulcan', 'Kawasaki', 'KAWASAKI', r'VULCAN.*|VN.*', 'Cruiser'),
 ('Kawasaki Versys', 'Kawasaki', 'KAWASAKI', r'VERSYS.*|KLE.*', 'Adventure'),
 ('Suzuki Boulevard', 'Suzuki', 'SUZUKI', r'VZR.*|VL.*|VZ.*|BOULEVARD.*|M109R.*|C50.*|M50.*|C90.*', 'Cruiser'),
 ('Suzuki GSX-R', 'Suzuki', 'SUZUKI', r'GSX-?R.*', 'Sport'),
 ('Suzuki Hayabusa', 'Suzuki', 'SUZUKI', r'HAYABUSA.*|GSX1300R.*', 'Sport'),
 ('Suzuki V-Strom', 'Suzuki', 'SUZUKI', r'DL.*|V-?STROM.*', 'Adventure'),
 ('BMW GS (R1200/R1250GS)', 'BMW Motorrad', 'BMW', r'R ?12[05]0 ?GS.*|R ?1[0-9]{3} ?GS.*|R1200GS.*|R1250GS.*', 'Adventure'),
 ('BMW RT (R1200/R1250RT)', 'BMW Motorrad', 'BMW', r'R ?12[05]0 ?RT.*|R1200RT.*|R1250RT.*', 'Touring'),
 ('BMW K1600', 'BMW Motorrad', 'BMW', r'K ?1600.*', 'Touring'),
 ('BMW S1000RR', 'BMW Motorrad', 'BMW', r'S ?1000.*', 'Sport'),
 ('Ducati Multistrada', 'Ducati', 'DUCATI', r'MULTISTRADA.*', 'Adventure'),
 ('Ducati Monster', 'Ducati', 'DUCATI', r'MONSTER.*|S[24]R.*', 'Standard'),
 ('Ducati Panigale', 'Ducati', 'DUCATI', r'PANIGALE.*|1199.*|1299.*|899.*|959.*|848.*|1098.*|1198.*', 'Sport'),
 ('Ducati Scrambler', 'Ducati', 'DUCATI', r'SCRAMBLER.*', 'Standard'),
 ('Ducati SportClassic', 'Ducati', 'DUCATI', r'SPORT ?CLASSIC.*|SPORT 1000.*|PAUL SMART.*|GT ?1000.*|1000GT.*', 'Standard'),
 ('Triumph Bonneville / Thruxton', 'Triumph', 'TRIUMPH', r'BONNEVILLE.*|THRUXTON.*|SCRAMBLER.*|STREET TWIN.*|T100.*|T120.*|SPEED TWIN.*', 'Standard'),
 ('Triumph Rocket 3', 'Triumph', 'TRIUMPH', r'ROCKET.*', 'Cruiser'),
 ('Triumph Tiger', 'Triumph', 'TRIUMPH', r'TIGER.*', 'Adventure'),
 ('KTM 790/890 Adventure', 'KTM', 'KTM', r'[78]90 ADVENTURE.*', 'Adventure'),
 ('KTM 690 Duke / Enduro', 'KTM', 'KTM', r'690.*', 'Standard'),
 ('KTM 390', 'KTM', 'KTM', r'390.*|RC ?390.*', 'Standard'),
 ('Indian Scout', 'Indian', 'INDIAN', r'SCOUT.*', 'Cruiser'),
 ('Indian Chief / Chieftain', 'Indian', 'INDIAN', r'CHIEF.*|ROADMASTER.*|SPRINGFIELD.*|PURSUIT.*|CHALLENGER.*', 'Touring'),
 ('Can-Am Spyder', 'Can-Am', 'CAN-AM', r'SPYDER.*', 'Three-wheel'),
 ('Can-Am Ryker', 'Can-Am', 'CAN-AM', r'RYKER.*', 'Three-wheel'),
]
PART = {'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'ELECTRICAL SYSTEM': 'electrical', 'ENGINE': 'engine', 'ENGINE AND ENGINE COOLING': 'engine',
        'FUEL/PROPULSION SYSTEM': 'fuel system', 'SUSPENSION': 'suspension', 'STEERING': 'steering', 'WHEELS': 'wheels', 'TIRES': 'tires', 'VEHICLE SPEED CONTROL': 'throttle & speed control',
        'EXTERIOR LIGHTING': 'lights', 'STRUCTURE': 'frame & body', 'LATCHES/LOCKS/LINKAGES': 'latches & linkages', 'EQUIPMENT': 'equipment', 'VISIBILITY': 'visibility', 'FUEL SYSTEM, GASOLINE': 'fuel system', 'FUEL SYSTEM, OTHER': 'fuel system', 'SERVICE BRAKES, HYDRAULIC': 'brakes', 'SERVICE BRAKES, AIR': 'brakes', 'SERVICE BRAKES, ELECTRIC': 'brakes', 'PARKING BRAKE': 'brakes', 'ELECTRONIC STABILITY CONTROL (ESC)': 'stability control', 'VISIBILITY/WIPER': 'visibility'}
con = sqlite3.connect(DB)
pats = [(f, b, mk, re.compile(rx), seg) for f, b, mk, rx, seg in F]
rows = collections.defaultdict(list)
for odino, make, model, year, crash, fire, inj, deaths, miles, comps in con.execute(
        f"SELECT odino, make, model, year, crash, fire, injured, deaths, miles, comps FROM complaints WHERE year BETWEEN {Y0} AND {Y1} AND make IN ({','.join('?' * len(set(p[2] for p in pats)))})",
        sorted(set(p[2] for p in pats))):
    m = (model or '').upper().strip()
    fam = next((f for f, b, mk, rx, seg in pats if mk == make and rx.fullmatch(m)), None)
    if fam: rows[fam].append((odino, m, year, crash, fire, inj, deaths, miles, comps))
def get(url):
    p = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:20] + '.json')
    if os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    for k in range(3):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'LemonIndex/1.0 (lemonindex.com)'}), timeout=15)); json.dump(d, open(p, 'w', encoding='utf-8')); return d
        except Exception: time.sleep(1 + k)
    return None
out = []
for f, b, mk, rx, seg in pats:
    R = {r[0]: r for r in rows[f]}.values(); R = list(R)
    if len(R) < 15: print('skip (few complaints)', f, len(R)); continue
    comp = collections.Counter(); ys = collections.Counter(); names = collections.Counter(r[1] for r in R)
    for r in R:
        ys[r[2]] += 1
        for c in set((r[8] or '').split(' | ')):
            c = c.split(':')[0].strip()
            if c and c not in ('UNKNOWN OR OTHER',): comp[PART.get(c, c.lower())] += 1
    n = len(R); ser = sum(1 for r in R if r[3] == 'Y' or r[4] == 'Y' or (r[5] or 0) > 0 or (r[6] or 0) > 0)
    mi = [r[7] for r in R if r[7] and 0 < r[7] < 200000]
    # recalls: every campaign for the family's top filed model names in the years it has complaints
    camp = {}
    import concurrent.futures as cf
    qs = [(name, y) for name, _ in names.most_common(2) for y in sorted(ys)]
    with cf.ThreadPoolExecutor(12) as ex:
        res = list(ex.map(lambda q: (q[1], get('https://api.nhtsa.gov/recalls/recallsByVehicle?' + urllib.parse.urlencode({'make': mk, 'model': q[0], 'modelYear': q[1]}))), qs))
    for y, d in res:
            for r in (d or {}).get('results', []):
                camp[r.get('NHTSACampaignNumber')] = dict(id=r.get('NHTSACampaignNumber'), date=r.get('ReportReceivedDate'), part=r.get('Component'), summary=(r.get('Summary') or '')[:300], y=y)
    years = sorted(ys)
    out.append(dict(name=f, brand=b, make=mk, seg=seg, n=n, years=[years[0], years[-1]], by_year={str(y): ys[y] for y in years},
                    parts=[[p, round(k / n * 100)] for p, k in comp.most_common(5)], serious=round(ser / n * 100), crash=sum(1 for r in R if r[3] == 'Y'),
                    fire=sum(1 for r in R if r[4] == 'Y'), injured=sum((r[5] or 0) for r in R), miles=int(statistics.median(mi)) if len(mi) >= 10 else None,
                    recalls=sorted(camp.values(), key=lambda r: r['date'] or '', reverse=True), names=[x for x, _ in names.most_common(6)]))
    print(f'{f:34} {n:5} complaints, {len(camp):3} recalls, serious {out[-1]["serious"]}%, top {out[-1]["parts"][:2]}', flush=True)
json.dump(out, open(os.path.join(HERE, 'data', 'moto.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('families', len(out))
