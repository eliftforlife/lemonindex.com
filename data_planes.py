# Plane section data (11-04, Elijah: "plane section... top crashes or top issues"). -> data/planes.json
# Source: NTSB aviation accident database (avall.mdb, 2008-present, downloaded 11-04 from data.ntsb.gov/avdata; exported to CSV by
# 3 Lemon Index/data/planes/ntsb_export.py). U.S. events, 2008-2025, aircraft grouped into model families by make + model.
# Per family: accidents, fatal accidents, deaths, share destroyed, accidents per year, what happened (NTSB "defining event"), phase of flight,
# and how often an aircraft problem (engine, systems, structure, propeller/rotor) was among NTSB's listed CAUSES vs only people/environment.
# No fleet sizes yet (the FAA registry download needs a browser), so no per-plane rates: counts and shares only.
import csv, re, json, os, collections, sys
sys.stdout.reconfigure(encoding='utf-8'); csv.field_size_limit(10 ** 8)
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\planes'
Y0, Y1 = 2008, 2025
F = [  # (family, make regex, model regex, kind)
 ('Cessna 172 Skyhawk', r'CESSNA.*', r'R?172.*|SKYHAWK.*', 'Single-engine piston'),
 ('Cessna 150/152', r'CESSNA.*', r'15[02].*|A15[02].*', 'Single-engine piston'),
 ('Cessna 182 Skylane', r'CESSNA.*', r'R?182.*|SKYLANE.*', 'Single-engine piston'),
 ('Cessna 180/185 Skywagon', r'CESSNA.*', r'A?18[05].*', 'Single-engine piston'),
 ('Cessna 206 Stationair', r'CESSNA.*', r'[TU]?206.*|P206.*|STATIONAIR.*', 'Single-engine piston'),
 ('Cessna 210 Centurion', r'CESSNA.*', r'[TP]?210.*|CENTURION.*', 'Single-engine piston'),
 ('Cessna 170', r'CESSNA.*', r'170.*', 'Single-engine piston'),
 ('Cessna 208 Caravan', r'CESSNA.*|TEXTRON.*', r'208.*|CARAVAN.*', 'Turboprop'),
 ('Cessna 310/340/414/421 twins', r'CESSNA.*', r'T?3[14]0.*|41[04].*|421.*', 'Twin piston'),
 ('Piper PA-28 Cherokee / Warrior / Archer', r'PIPER.*', r'PA[- ]?28.*', 'Single-engine piston'),
 ('Piper PA-18 Super Cub', r'PIPER.*', r'PA[- ]?18.*|SUPER CUB.*', 'Single-engine piston'),
 ('Piper J-3 Cub', r'PIPER.*', r'J[- ]?3.*', 'Single-engine piston'),
 ('Piper PA-32 Saratoga / Cherokee Six', r'PIPER.*', r'PA[- ]?32.*', 'Single-engine piston'),
 ('Piper PA-34 Seneca', r'PIPER.*', r'PA[- ]?34.*', 'Twin piston'),
 ('Piper PA-46 Malibu / M350 / M600', r'PIPER.*', r'PA[- ]?46.*|M[356]00.*|M350.*', 'Single-engine (high perf.)'),
 ('Piper PA-12 / PA-22', r'PIPER.*', r'PA[- ]?(12|22).*', 'Single-engine piston'),
 ('Beechcraft Bonanza', r'BEECH.*|RAYTHEON.*|TEXTRON.*', r'[A-Z]?3[356].*|BONANZA.*', 'Single-engine piston'),
 ('Beechcraft Baron', r'BEECH.*|RAYTHEON.*|TEXTRON.*', r'[A-Z]?5[58].*|BARON.*', 'Twin piston'),
 ('Beechcraft King Air', r'BEECH.*|RAYTHEON.*|TEXTRON.*', r'[A-Z]?(90|100|200|300|350)[A-Z]?.*|B?200.*|KING AIR.*', 'Turboprop'),
 ('Cirrus SR20', r'CIRRUS.*', r'SR[- ]?20.*', 'Single-engine piston'),
 ('Cirrus SR22', r'CIRRUS.*', r'SR[- ]?22.*', 'Single-engine piston'),
 ('Mooney M20', r'MOONEY.*', r'M[- ]?20.*', 'Single-engine piston'),
 ('Diamond DA40', r'DIAMOND.*', r'DA[- ]?40.*', 'Single-engine piston'),
 ('Diamond DA20', r'DIAMOND.*', r'DA[- ]?20.*', 'Single-engine piston'),
 ('Grumman AA-1 / AA-5', r'GRUMMAN.*|AMERICAN.*', r'AA[- ]?[15].*', 'Single-engine piston'),
 ('Maule', r'MAULE.*', r'.*', 'Single-engine piston'),
 ('Aeronca Champ', r'AERONCA.*', r'7.*|CHAMP.*', 'Single-engine piston'),
 ('Air Tractor (crop dusters)', r'AIR TRACTOR.*', r'.*', 'Agricultural'),
 ("Van's RV (kit planes)", r'VANS?.*|VAN\'?S.*', r'RV.*', 'Kit-built'),
 ('Robinson R22', r'ROBINSON.*', r'R[- ]?22.*', 'Helicopter'),
 ('Robinson R44', r'ROBINSON.*', r'R[- ]?44.*', 'Helicopter'),
 ('Robinson R66', r'ROBINSON.*', r'R[- ]?66.*', 'Helicopter'),
 ('Bell 206 / 407', r'BELL.*', r'206.*|407.*', 'Helicopter'),
 ('Airbus AS350 (A-Star)', r'AIRBUS.*|EUROCOPTER.*|AEROSPATIALE.*', r'AS[- ]?350.*|H125.*', 'Helicopter'),
 ('Boeing 737', r'BOEING.*', r'737.*', 'Airliner'),
 ('Boeing 757 / 767', r'BOEING.*', r'7[56]7.*', 'Airliner'),
 ('Boeing 777 / 787', r'BOEING.*', r'7[78]7.*', 'Airliner'),
 ('Airbus A320 family', r'AIRBUS.*', r'A ?3(19|20|21).*', 'Airliner'),
 ('Embraer regional jets', r'EMBRAER.*', r'(ERJ|EMB)[- ]?(1[3-9]|170|175|190|195).*|ERJ.*|EMB[- ]?1[4-9]5.*', 'Airliner'),
]
rd = lambda n: list(csv.DictReader(open(os.path.join(SRC, n + '.csv'), encoding='utf-8')))
E = {r['ev_id']: r for r in rd('events')}
A = rd('aircraft')
FND = collections.defaultdict(list)
for r in rd('Findings'): FND[(r['ev_id'], r['Aircraft_Key'])].append(r)
SEQ = {}
for r in rd('Events_Sequence'):
    if r['Defining_ev'] == 'True': SEQ[(r['ev_id'], r['Aircraft_Key'])] = r['Occurrence_Description']
PH = ['Standing', 'Taxi', 'Takeoff', 'Initial climb', 'Enroute', 'Maneuvering', 'Approach', 'Emergency descent', 'Landing', 'Uncontrolled descent', 'Post-impact']
MECH = ('Aircraft-Aircraft systems', 'Aircraft-Aircraft power plant', 'Aircraft-Aircraft propeller', 'Aircraft-Aircraft structures')
pats = [(f, re.compile(mk), re.compile(md), kind) for f, mk, md, kind in F]
G = collections.defaultdict(list)
for a in A:
    e = E.get(a['ev_id'])
    if not e or e['ev_country'] != 'USA' or not e['ev_year'].isdigit() or not Y0 <= int(e['ev_year']) <= Y1: continue
    if a['homebuilt'] == 'Y' and 'RV' not in a['acft_model'].upper(): continue
    mk, md = a['acft_make'].upper().strip(), re.sub(r'\s+', ' ', a['acft_model'].upper().strip())
    fam = next((f for f, pm, pd, k in pats if pm.fullmatch(mk) and pd.fullmatch(md)), None)
    if fam: G[fam].append((a, e))
def phase_event(desc):
    for p in sorted(PH, key=len, reverse=True):
        if desc.startswith(p): return p, re.sub(r'^[a-z][a-z/\- ]*(?=[A-Z])', '', desc[len(p):].strip(' -'))   # drop the sub-phase ('flare/touchdown')
    return 'Other', re.sub(r'^[a-z][a-z/\- ]*(?=[A-Z])', '', desc)
out = []
for f, pm, pd, kind in pats:
    R = G[f]
    if len(R) < 25: print('skip', f, len(R)); continue
    acc = [x for x in R if x[1]['ev_type'] == 'ACC'] or R
    n = len(acc); fatal = sum(1 for a, e in acc if e['ev_highest_injury'] == 'FATL')
    deaths = sum(int(float(e['inj_tot_f'] or 0)) for a, e in {e['ev_id']: (a, e) for a, e in acc}.values())
    destroyed = sum(1 for a, e in acc if a['damage'] == 'DEST')
    ys = collections.Counter(int(e['ev_year']) for a, e in acc)
    what, phase = collections.Counter(), collections.Counter(); mech = 0; mech_k = collections.Counter(); judged = 0
    for a, e in acc:
        d = SEQ.get((a['ev_id'], a['Aircraft_Key']))
        if d: p, ev = phase_event(d); phase[p] += 1; what[ev] += 1
        fs = [x for x in FND.get((a['ev_id'], a['Aircraft_Key']), []) if x['Cause_Factor'] == 'C']
        if fs:
            judged += 1
            m = [x for x in fs if x['finding_description'].startswith(MECH)]
            if m: mech += 1; mech_k['-'.join(m[0]['finding_description'].split('-')[2:3]).strip().lower()] += 1
    out.append(dict(name=f, kind=kind, n=n, fatal=fatal, fatal_pct=round(fatal / n * 100), deaths=deaths, destroyed_pct=round(destroyed / n * 100),
                    by_year={str(y): ys[y] for y in range(Y0, Y1 + 1)}, what=[[k, round(v / n * 100)] for k, v in what.most_common(6)],
                    phase=[[k, round(v / n * 100)] for k, v in phase.most_common(5)], mech_pct=round(mech / judged * 100) if judged else None,
                    mech_parts=[[k, v] for k, v in mech_k.most_common(4)], judged=judged))
    print(f'{f:42} {n:5} acc  fatal {out[-1]["fatal_pct"]:3}%  plane-caused {out[-1]["mech_pct"]}%  top {out[-1]["what"][:2]}')
json.dump(out, open(os.path.join(HERE, 'data', 'planes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('families', len(out))
