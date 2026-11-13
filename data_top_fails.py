# 11-12 round 2 (Jake, Ryan: "What breaks" is only categories; the A/C condenser and steering rack were buried in Repairs and in video titles):
# the specific failures owners name most for each model year, with when they show up and what one repair cost.
#   usage: py -X utf8 data_top_fails.py      -> data/top_fails.json
# Plain counting from data we already hold:
#   - NHTSA owner complaints (3 Lemon Index/data/complaints.db), the family's own NHTSA model names per year (extras_local*.json `names`)
#   - a complaint counts for a failure when its own words name that part (the regexes below; `ctx` must also appear when set)
#   - mileage = the odometer the owner typed in (middle half), only when 5+ of those complaints have one
#   - cost = the repair bills owners named in those same complaints (data/repair_costs.json, joined by NHTSA complaint id), only with 5+ bills
# A failure is listed for a year when 8+ complaints and 2%+ of that year's complaints name it.
import collections, json, os, re, sqlite3, statistics, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
F = [  # (label, regex, context regex or None) - named the way a buyer or mechanic would say it
    ('A/C compressor', r'compressor', r'\ba/?c\b|air ?condition|\bac\b'),
    ('A/C condenser', r'condenser', None),
    ('A/C blowing warm air', r'(a/?c|air ?condition\w*|\bac\b)[^.]{0,40}(warm|hot) air|(warm|hot) air[^.]{0,40}(a/?c|air ?condition)', None),
    ('Steering rack / power steering', r'steering (rack|gear ?box|gear\b)|electric power steering|\beps\b|power steering (fail|assist|motor|loss|lost|went)|loss of power steering|lost power steering', None),
    ('Fuel pump', r'fuel pump', None),
    ('Oil in the fuel / oil dilution', r'oil dilution|(gas|fuel|gasoline) in (the )?oil|oil (level )?(rising|increas)', None),
    ('Oil consumption', r'oil consumption|burn(s|ing)? (excessive )?oil|consum(es|ing) oil|using oil', None),
    ('Oil leak', r'oil leak|leak(s|ing)? oil', None),
    ('Transmission failure', r'transmission (fail|went out|went bad|replaced|replacement|slip)|(rebuil|replac)\w* (the )?transmission|cvt (fail|replaced|replacement)', None),
    ('Rough or hard shifting', r'(hard|harsh|rough|delayed|jerk\w*|slam\w*) (shift|shifts|shifting)|shift(s|ing)? (hard|harsh|rough)|transmission (jerk|lurch|clunk|hesitat)', None),
    ('Torque converter', r'torque converter', None),
    ('Engine stalling', r'stall(s|ed|ing)?\b', r'engine|vehicle|car|truck'),
    ('Engine failure', r'engine (fail|seized|blew|blown|replaced|replacement)|(replac|rebuil)\w* (the )?engine|spun (a )?bearing|rod knock|thrown rod', None),
    ('Timing chain', r'timing chain|cam phaser', None),
    ('Water pump', r'water pump', None),
    ('Head gasket', r'head gasket', None),
    ('Turbocharger', r'turbo ?charger|\bturbo\b', None),
    ('Ignition coils / misfire', r'ignition coil|misfire', None),
    ('Catalytic converter', r'catalytic converter', None),
    ('Throttle body / loss of power', r'throttle body|reduced power|loss of (motive )?power|limp mode', None),
    ('Battery drain / dead battery', r'battery (drain|died|dies|dead|keeps dying)|dead battery|parasitic drain', None),
    ('Alternator', r'alternator', None),
    ('Starter', r'\bstarter\b', None),
    ('Infotainment screen / radio', r'infotainment|touch ?screen|radio (screen|display|freez|reboot|went)|head unit|(screen|display) (went black|goes black|freez|reboot)', None),
    ('Backup camera', r'back ?up camera|rear ?view camera|reverse camera', None),
    ('Airbag light / sensor', r'airbag (warning )?light|srs (warning )?light|occupant (classification|detection) sensor|airbag sensor', None),
    ('Brakes: ABS module / pump', r'\babs (module|pump|unit|control)', None),
    ('Brake booster / hard pedal', r'brake booster|hard brake pedal|brake pedal (went|goes|was) (hard|stiff)', None),
    ('Phantom braking (collision system)', r'phantom brak|(automatic|emergency) brak\w* (for no reason|on its own|activated|engaged)|collision mitigation|false (brak|alert|warning)', None),
    ('Wheel bearing', r'wheel bearing|hub bearing', None),
    ('Ball joint / control arm', r'ball joint|control arm', None),
    ('Struts / shocks', r'\bstruts?\b|shock absorber|\bshocks\b', None),
    ('Rust / frame corrosion', r'\brust(ed|ing)?\b|corro(sion|ded)', None),
    ('Sunroof leak or shatter', r'sun ?roof|moon ?roof', None),
    ('Door lock actuator', r'door lock actuator|lock actuator|door locks? (fail|don.t|won.t|not)', None),
    ('Power window regulator', r'window regulator|window motor', None),
    ('Headlights', r'headlights?|head lamps?', None),
    ('Coolant leak / overheating', r'coolant leak|leak(s|ing)? coolant|overheat', None),
    ('Hybrid battery / inverter', r'hybrid battery|inverter|hybrid system', None),
    ('Seat belt', r'seat ?belt (buckle|retractor|latch)|seatbelt (fail|won.t|does not)', None),
]
CF = [(t, re.compile(rx, re.I), re.compile(cx, re.I) if cx else None) for t, rx, cx in F]

def _load(p, d=None):
    p = os.path.join(HERE, p)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else d

def main():
    XL = {}
    for p in ('data/extras_local.json', 'data/extras_local_new.json', 'data/extras_local_low.json', 'data/extras_local_tesla.json'):
        for fid, ys in (_load(p, {}) or {}).items():
            for y, e in ys.items(): XL.setdefault(fid, {}).setdefault(y, e)
    key = {}   # (MAKE, MODEL, year) -> fid
    for fid, ys in XL.items():
        for y, e in ys.items():
            for mk, md, _ in (e or {}).get('names') or []: key.setdefault((mk, md, int(y)), fid)
    RC = _load('data/repair_costs.json', {}) or {}
    bill = {(fid, o): v for fid, d in RC.items() for yy, a, v, o in d.get('c', [])}
    c = sqlite3.connect(DB)
    comp = collections.defaultdict(dict)   # (fid, year) -> {odino: (descr, miles)}
    for o, mk, md, y, mi, d in c.execute('select odino, make, model, year, max(miles), max(descr) from rows where year between 2000 and 2026 group by odino'):
        fid = key.get((mk, md, y))
        if fid: comp[(fid, y)][o] = (d or '', mi)
    out = {}
    q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(round((len(xs) - 1) * p)))]
    for (fid, y), rows in comp.items():
        n_all = len(rows); res = []
        for t, rx, cx in CF:
            hit = [o for o, (d, _) in rows.items() if rx.search(d) and (not cx or cx.search(d))]
            if len(hit) < 8 or len(hit) < .02 * n_all: continue
            mis = sorted(rows[o][1] for o in hit if rows[o][1] and 0 < rows[o][1] < 400000)
            bs = sorted(bill[(fid, o)] for o in hit if (fid, o) in bill)
            res.append(dict(t=t, n=len(hit), mi=[q(mis, .25), int(statistics.median(mis)), q(mis, .75), len(mis)] if len(mis) >= 5 else None,
                            cost=[q(bs, .25), int(statistics.median(bs)), q(bs, .75), len(bs)] if len(bs) >= 5 else None, ex=hit[:2]))
        if res: out.setdefault(fid, {})[str(y)] = dict(all=n_all, top=sorted(res, key=lambda r: -r['n'])[:5])
    json.dump(out, open(os.path.join(HERE, 'data', 'top_fails.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('top_fails:', len(out), 'models,', sum(len(v) for v in out.values()), 'model years')

if __name__ == '__main__':
    main()
