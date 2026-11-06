# Models with complaint data but no sales data yet (11-06: VW Taos, Pontiac). No Lemon Index without sales, so these pages show raw owner data, recalls and YouTube topics. Writes data/extra_models.json.
import collections, json, os, re, statistics, sys, time, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
RAW = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\video 1 most reliable\data\raw\FLAT_CMPL.txt'
PART = {'ELECTRICAL SYSTEM': 'electrical', 'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'SERVICE BRAKES, HYDRAULIC': 'brakes', 'VEHICLE SPEED CONTROL': 'speed control', 'FUEL/PROPULSION SYSTEM': 'fuel system', 'FUEL SYSTEM, GASOLINE': 'fuel system', 'FORWARD COLLISION AVOIDANCE': 'automatic emergency braking', 'VISIBILITY/WIPER': 'wipers & visibility', 'VISIBILITY': 'visibility', 'AIR BAGS': 'airbags', 'STRUCTURE': 'body structure', 'EXTERIOR LIGHTING': 'lights', 'ENGINE AND ENGINE COOLING': 'engine', 'ENGINE': 'engine', 'STEERING': 'steering', 'SUSPENSION': 'suspension', 'WHEELS': 'wheels', 'TIRES': 'tires', 'SEATS': 'seats', 'LATCHES/LOCKS/LINKAGES': 'doors, locks & latches', 'SEAT BELTS': 'seat belts'}
M = {'volkswagen-taos': ('Volkswagen Taos', 'Volkswagen', 'VOLKSWAGEN', ['TAOS'], 2022, 2026), 'pontiac-g6': ('Pontiac G6', 'Pontiac', 'PONTIAC', ['G6'], 2005, 2010), 'pontiac-grand-am': ('Pontiac Grand Am', 'Pontiac', 'PONTIAC', ['GRAND AM'], 1999, 2005), 'pontiac-grand-prix': ('Pontiac Grand Prix', 'Pontiac', 'PONTIAC', ['GRAND PRIX'], 1997, 2008), 'pontiac-bonneville': ('Pontiac Bonneville', 'Pontiac', 'PONTIAC', ['BONNEVILLE'], 1996, 2005),
     'pontiac-vibe': ('Pontiac Vibe', 'Pontiac', 'PONTIAC', ['VIBE'], 2003, 2010), 'pontiac-sunfire': ('Pontiac Sunfire', 'Pontiac', 'PONTIAC', ['SUNFIRE'], 1995, 2005), 'pontiac-montana': ('Pontiac Montana', 'Pontiac', 'PONTIAC', ['MONTANA'], 1999, 2009), 'pontiac-torrent': ('Pontiac Torrent', 'Pontiac', 'PONTIAC', ['TORRENT'], 2006, 2009), 'pontiac-solstice': ('Pontiac Solstice', 'Pontiac', 'PONTIAC', ['SOLSTICE'], 2006, 2009),
     'pontiac-aztek': ('Pontiac Aztek', 'Pontiac', 'PONTIAC', ['AZTEK'], 2001, 2005), 'pontiac-firebird': ('Pontiac Firebird', 'Pontiac', 'PONTIAC', ['FIREBIRD', 'TRANS AM'], 1993, 2002), 'pontiac-gto': ('Pontiac GTO', 'Pontiac', 'PONTIAC', ['GTO'], 2004, 2006), 'pontiac-g5': ('Pontiac G5', 'Pontiac', 'PONTIAC', ['G5'], 2007, 2009), 'pontiac-g8': ('Pontiac G8', 'Pontiac', 'PONTIAC', ['G8'], 2008, 2009)}
key = {(v[2], md): k for k, v in M.items() for md in v[3]}
D = {k: dict(by=collections.Counter(), parts=collections.Counter(), seen=set(), crash=0, fire=0, inj=0, dead=0, miles=[], q=[]) for k in M}
with open(RAW, encoding='latin-1') as fh:
    for line in fh:
        p = line.rstrip('\n').split('\t')
        if len(p) < 20 or p[3] not in ('PONTIAC', 'VOLKSWAGEN'): continue
        k = key.get((p[3], p[4]))
        if not k or not p[5].isdigit(): continue
        y = int(p[5]); nm, br, mk, mds, a, b = M[k]
        if not a <= y <= b: continue
        d = D[k]; c = p[11].split(':')[0].strip(); d['parts'][PART.get(c, c.lower())] += 1
        if p[1] in d['seen']: continue
        d['seen'].add(p[1]); d['by'][y] += 1; d['crash'] += p[6] == 'Y'; d['fire'] += p[8] == 'Y'; d['inj'] += int(p[9] or 0) > 0 if p[9].isdigit() else 0; d['dead'] += int(p[10] or 0) > 0 if p[10].isdigit() else 0
        if p[17].isdigit() and 0 < int(p[17]) < 500000: d['miles'].append(int(p[17]))
        t = p[19].strip()
        if 70 < len(t) < 240 and len(d['q']) < 300: d['q'].append((y, p[1], t))
def api(u):
    for k in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30))
        except Exception: time.sleep(1 + k)
    return {}
out = {}
for k, (nm, br, mk, mds, a, b) in M.items():
    d = D[k]; rec = {}
    for y in range(a, b + 1):
        for md in mds:
            for r in (api(f'https://api.nhtsa.gov/recalls/recallsByVehicle?make={urllib.parse.quote(mk.lower())}&model={urllib.parse.quote(md.lower())}&modelYear={y}').get('results') or []):
                c = r.get('NHTSACampaignNumber')
                if c: rec.setdefault(c, dict(id=c, date=r.get('ReportReceivedDate', ''), part=r.get('Component', ''), summary=(r.get('Summary') or '').strip()[:600], risk=(r.get('Consequence') or '').strip()[:400], fix=(r.get('Remedy') or '').strip()[:400], years=[])); c and rec[c]['years'].append(y)
    n = len(d['seen']); tot = sum(d['parts'].values()) or 1; ms = sorted(d['miles']); qs = sorted(d['q'], key=lambda q: q[1])[-3:]
    out[k] = dict(id=k, name=nm, brand=br, a=a, b=b, n=n, by_year={str(y): d['by'][y] for y in range(a, b + 1)}, parts=[[p, round(c / tot * 100)] for p, c in d['parts'].most_common(6)], crash=d['crash'], fire=d['fire'], injured=d['inj'], deaths=d['dead'], miles=dict(median=ms[len(ms) // 2], p25=ms[len(ms) // 4], p75=ms[len(ms) * 3 // 4], n=len(ms)) if len(ms) >= 20 else None,
                  recalls=sorted(rec.values(), key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2], reverse=True), quotes=[dict(y=y, odi=o, text=t[0] + t[1:].lower() if t.isupper() else t) for y, o, t in qs])
    print(nm, n, len(rec), d['parts'].most_common(2), flush=True)
json.dump(out, open('data/extra_models.json', 'w', encoding='utf-8'), ensure_ascii=False); print('written', len(out))
