# Transmission complaints per model and year (11-02, from keyword research: "<model> transmission problems" is in Google autocomplete for 101 of 126 models).
# NHTSA files newer complaints under plain "POWER TRAIN" (transmission + axles + driveline), so a complaint counts as a transmission complaint when its
# component says TRANSMISSION, or it's POWER TRAIN and the owner's text mentions the transmission (transmission, shift, gear, CVT, slipping...).
# Uses every complaint for the model year (not just the first 3 years), like the "when problems start" timeline.
#   usage: py data_trans.py  -> data/trans.json {fid: {year: {n, rate, miles, sym: {label: n}, q: [quote...]}}}
import json, os, re, sqlite3, statistics, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
Y = json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8'))
XL = json.load(open(os.path.join(HERE, 'data', 'extras_local.json'), encoding='utf-8'))
TX = re.compile(r'\b(transmission|trans\b|shift|shifting|shifts|gear|gears|cvt|slipp|downshift|upshift|torque converter|clutch|neutral|lurch|jerk)', re.I)
SYM = [('Hard or jerky shifting', r'(hard|harsh|rough|jerk|clunk|slam|bang)\w*\s+(shift|into gear|downshift|upshift)|shifts? (hard|harsh|rough)|jerk'),
       ('Slipping', r'slip'), ('Delay or hesitation', r'hesitat|delay|lag\b|lagg'), ('Stuck in gear or limp mode', r'stuck in|limp mode|wouldn.?t shift|won.?t shift|will not shift|no reverse|lost reverse'),
       ('Shudder', r'shudder|judder|vibrat'), ('Rolled away or park trouble', r'roll(ed)? away|rolled|out of park|won.?t go into park|park position'),
       ('Lost power while driving', r'lost (all )?power|loss of power|power loss|stall'), ('Transmission replaced', r'(replace|rebuil)\w* (the |my |a )?transmission(?! (fluid|oil|filter|mount|cooler|line|solenoid|sensor|valve))|new transmission(?! (fluid|oil|filter))|transmission (was|had to be) (replaced|rebuilt)')]
SYMC = [(l, re.compile(p, re.I)) for l, p in SYM]
db = sqlite3.connect(DB)
BY = {}   # one pass: (make, model, year) -> power-train rows (a scan per model-year would read 1.6M rows thousands of times)
for mk, md, yr, comp, miles, descr, odi in db.execute("select make, model, year, comp, miles, descr, odino from rows where comp like '%POWER TRAIN%'"):
    BY.setdefault((mk, md, yr), []).append((comp, miles, descr, odi))
TOT = {tuple(k): n for k, n in [((a, b, c), n) for a, b, c, n in db.execute('select make, model, year, count(distinct odino) from rows group by make, model, year')]}
out = {}
for f in Y:
    fid = f['id']; names = {(mk, md) for yy in XL.get(fid, {}).values() for mk, md, *_ in yy.get('names', [])}
    if not names: continue
    sold = {v['y']: v.get('sold') or 0 for v in f['years']}
    for y in sold:
        rows = []
        for mk, md in names: rows += BY.get((mk, md, y), [])
        alln = sum(TOT.get((mk, md, y), 0) for mk, md in names)
        seen = set(); tr = []
        for comp, miles, descr, odi in rows:
            if odi in seen: continue
            seen.add(odi); comp = comp or ''; descr = descr or ''
            if 'TRANSMISSION' in comp or ('POWER TRAIN' in comp and TX.search(descr)): tr.append((miles, descr, odi))
        if not tr: continue
        ms = [m for m, _, _ in tr if m and 0 < m < 400000]
        sym = {l: sum(1 for _, d, _ in tr if c.search(d)) for l, c in SYMC}
        q = sorted((d for _, d, _ in tr if 120 < len(d) < 420 and TX.search(d)), key=len)[:2]
        out.setdefault(fid, {})[str(y)] = {'n': len(tr), 'all': alln, 'rate': round(len(tr) / sold[y] * 1e5, 1) if sold[y] else None,
                                            'miles': int(statistics.median(ms)) if len(ms) >= 5 else None, 'sym': {k: v for k, v in sym.items() if v}, 'q': q}
    print(fid, sum(v['n'] for v in out.get(fid, {}).values()), flush=True)
json.dump(out, open(os.path.join(HERE, 'data', 'trans.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('models', len(out))
