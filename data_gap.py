# Data for the keyword-gap pages (11-06): check engine light complaints by model and year from the raw NHTSA file, and best real-world gas mileage models from EPA. Writes data/gap.json.
import collections, csv, json, re, sys
sys.stdout.reconfigure(encoding='utf-8'); csv.field_size_limit(10 ** 7)
RAW = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\video 1 most reliable\data\raw\FLAT_CMPL.txt'
YR = json.load(open('data/years.json', encoding='utf-8')); XL = json.load(open('data/extras_local.json', encoding='utf-8'))
CEL = re.compile(r'check engine|service engine soon|engine light|\bcel\b|malfunction indicator|engine warning light', re.I)
key = {}
for f in YR:
    for y, x in XL.get(f['id'], {}).items():
        for mk, md, n in (x.get('names') or []):
            if n >= 2: key[(mk, md, int(y))] = f['id']
cnt = collections.Counter(); tot = collections.Counter(); seen = set()
with open(RAW, encoding='latin-1') as fh:
    for line in fh:
        p = line.rstrip('\n').split('\t')
        if len(p) < 20 or not p[5].isdigit(): continue
        k = key.get((p[3], p[4], int(p[5])))
        if not k or p[1] in seen: continue
        seen.add(p[1]); tot[(k, int(p[5]))] += 1
        if CEL.search(p[19]): cnt[(k, int(p[5]))] += 1
rows = []; yrs = []
for f in YR:
    n = sold = t = 0
    for v in f['years']:
        y = v['y']
        if 2010 <= y <= 2022 and v.get('sold'):
            c = cnt[(f['id'], y)]; n += c; sold += v['sold']; t += tot[(f['id'], y)]
            if c >= 15 and v['sold'] >= 20000: yrs.append(dict(id=f['id'], name=f['name'], y=y, n=c, per=round(c / v['sold'] * 1e5, 1), share=round(c / max(1, tot[(f['id'], y)]) * 100)))
    if sold >= 200000 and n >= 10: rows.append(dict(id=f['id'], name=f['name'], n=n, sold=sold, per=round(n / sold * 1e5, 1), share=round(n / max(1, t) * 100)))
rows.sort(key=lambda r: -r['per']); yrs.sort(key=lambda r: -r['per'])
med = sorted(r['per'] for r in rows)[len(rows) // 2]
# EPA: best combined mpg by model for recent years, gas and hybrid (no plug-ins or EVs)
_n = lambda s: re.sub(r'[^a-z0-9]', '', str(s).lower()); best = {}
for r in csv.DictReader(open('data/cache/vehicles.csv', encoding='utf-8', errors='replace')):
    y = int(r['year'])
    if y < 2019 or y > 2025 or r['atvType'] in ('EV', 'Plug-in Hybrid', 'FCV'): continue
    best.setdefault((_n(r['make']), _n(r['baseModel'] or r['model'])), []).append(r)
M = []
for f in YR:
    names = next((x['names'] for y, x in sorted(XL.get(f['id'], {}).items(), reverse=True) if x.get('names')), None)
    if not names: continue
    mk = _n(names[0][0]); mk = {'chevy': 'chevrolet'}.get(mk, mk); base = {_n(m) for _, m, c in names if c >= 2}
    rs = [r for (a, b), L in best.items() if a == mk and any(b.startswith(x) or x.startswith(b) for x in base if len(x) >= 3) for r in L]
    if not rs: continue
    ok = [v for v in f['years'] if v.get('n', 0) >= 20 and 2010 <= v['y'] <= 2022]
    li = round(sum(v['li'] * v['sold'] for v in ok if v.get('sold')) / max(1, sum(v['sold'] for v in ok if v.get('sold')))) if ok else None
    t = max(rs, key=lambda r: int(r['comb08'])); g = [r for r in rs if r['atvType'] != 'Hybrid']; gas = max(g, key=lambda r: int(r['comb08'])) if g else None
    M.append(dict(id=f['id'], name=f['name'], seg=None, comb=int(t['comb08']), city=int(t['city08']), hwy=int(t['highway08']), hyb=t['atvType'] == 'Hybrid', year=int(t['year']), cost=int(t['fuelCost08']), gas=int(gas['comb08']) if gas else None, li=li))
M.sort(key=lambda r: -r['comb'])
json.dump(dict(cel=rows, cel_years=yrs[:40], cel_med=med, mpg=M), open('data/gap.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('models', len(rows), 'years', len(yrs), 'median', med, rows[:6]); print(yrs[:6]); print([(m['name'], m['comb'], m['hyb'], m['li']) for m in M[:12]])
