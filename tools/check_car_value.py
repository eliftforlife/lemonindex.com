# 11-26: /car-value/ math check. Runs assets/carvalue.js under node on random model / year / miles combos and compares it with
#   - prices_brackets.price_at() (no trim: the year-page price box's own math), and
#   - a Python copy of checklist_template.html price() with a trim picked (trim x engine multiplier, price-new trim multiplier,
#     enthusiast trims with their own table),
# Average condition, clean title. Every number must match exactly.   py -X utf8 tools/check_car_value.py [n=60]
import json, os, random, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CK = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\checklist'
sys.path.insert(0, CK); import prices_brackets as PB

D = json.load(open(os.path.join(HERE, 'assets', 'carvalue.json'), encoding='utf-8'))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
rng = random.Random(1126)


def ref_trim(P, mid, y, t, miles):
    """checklist price() with trim t picked (drive and cab left at 1), from the raw price file"""
    o = D['m'][mid]; row = next(r for r in o['t'] if r[0] == t and r[1] <= y <= r[2])
    T = None
    if row[3] == -1:
        T = P['trim_years'][t]; r = T['years'][str(y)]; p = dict(lo=r[0], hi=r[1], mi=r[2], new=(T.get('new') or {}).get(str(y)))
        a = na = 1
    else:
        ty = P['years'][str(y)]; p = dict(lo=ty[0], hi=ty[1], mi=ty[2], new=((P.get('new') or {}).get('years') or {}).get(str(y))); a, na = row[3], row[4]
    m = miles or p['mi']; age = PB.YEAR_NOW - y; rate = 0
    for ag, rr in P['miles']['per10k']:
        if age >= ag: rate = rr
    f = min(P['miles']['max'], max(P['miles']['min'], 1 + rate * (p['mi'] - m) / 10000))
    pp = [p['lo'] * f * a, p['hi'] * f * a]
    pcap = (T.get('private_cap') if T else (P.get('bands') or {}).get('private_cap'))
    dcap = (T.get('cap') or P['new'].get('cap', .98)) if T else P['new'].get('cap', .98)
    if p['new'] and pcap:
        pc = p['new'] * na * pcap
        if pp[1] > pc: pp[1] = pc; pp[0] = min(pp[0], pc * .85)
    d = P['dealer']; dl = [v * d['mult'] + d['add'] * min(1, v / 8000) for v in pp]
    if p['new']:
        c = p['new'] * na * dcap; dl[1] = min(dl[1], c); dl[0] = min(dl[0], dl[1] * .88)
    dl[0] = max(dl[0], pp[0] * 1.05); dl[1] = max(dl[1], pp[1] * 1.05)
    s = P.get('round', 250)
    return [PB.rnd(v, s) for v in pp], [PB.rnd(v, s) for v in dl]


cases = []
ids = sorted(D['m'])
for i in range(N):
    mid = rng.choice(ids); y = int(rng.choice(sorted(D['m'][mid]['y']))); typ = D['m'][mid]['y'][str(y)][2]
    mi = rng.choice([0, 0, int(typ * rng.uniform(.3, 2.2)) // 100 * 100, rng.randrange(1000, 300000, 500)])
    cases.append([mid, y, '', mi])
tr = [m for m in ids if 't' in D['m'][m]]
for i in range(N):
    mid = rng.choice(tr); r = rng.choice(D['m'][mid]['t']); y = rng.randint(r[1], r[2])
    if str(y) not in D['m'][mid]['y'] and r[3] != -1: continue
    cases.append([mid, y, r[0], rng.choice([0, rng.randrange(5000, 250000, 500)])])
for mid in ('ford-mustang', 'honda-civic', 'jeep-grand-cherokee'):   # every enthusiast trim with its own table, at least once
    for r in D['m'][mid]['t']:
        if r[3] == -1: cases.append([mid, r[1], r[0], 0])

js = os.path.join(HERE, 'assets', 'carvalue.js').replace('\\', '/')
drv = """
global.window = {}; global.document = {getElementById: function () { return null; }};
require(%s);
var D = require(%s), C = window.LX_CV; C.data(D);
var cases = %s, out = cases.map(function (c) { var o = D.m[c[0]], b = C.base(o, c[1], c[2], c[3]); if (!b) return null;
  var v = C.value(o, c[1], c[2], c[3], 'average', 'clean'); return [v.pp, v.dl]; });
process.stdout.write(JSON.stringify(out));
""" % (json.dumps(js), json.dumps(os.path.join(HERE, 'assets', 'carvalue.json').replace('\\', '/')), json.dumps(cases))
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as fh: fh.write(drv); tmp = fh.name
try: res = json.loads(subprocess.run(['node', tmp], capture_output=True, text=True, check=True).stdout)
finally: os.unlink(tmp)

bad = 0; nt = 0
for c, got in zip(cases, res):
    mid, y, t, mi = c; P = PB.load(mid)
    if t: want = ref_trim(P, mid, y, t, mi); nt += 1
    else:
        want = PB.price_at(P, y, mi or P['years'][str(y)][2]); want = [want[0], want[1]] if want else None
    if (got and [list(map(int, got[0])), list(map(int, got[1]))]) != (want and [list(want[0]), list(want[1])]):
        bad += 1; print('MISMATCH', c, 'js', got, 'py', want)
print(f'{len(cases)} cases ({len(cases) - nt} base vs price_at, {nt} with a trim vs checklist price()): {len(cases) - bad} match, {bad} differ')
sys.exit(1 if bad else 0)
