# 11-20 (Elijah: "2021+ model years are the Kia K5 but sit under /cars/kia-optima/"). The study (v3-unreliable ... data/out) counts the K5
# with the Optima (NHTSA files 2021+ complaints as "K5"). This writes data/k5_split.json: the study's model-level numbers recomputed for the two
# halves, the same way the study does it (complaints in each car's first 3 years / the average car of the same model years, 100 = average):
#   kia-optima: model years 2010-2020   kia-k5: model years 2021-2022 (the study's last scored year; 2023+ stay early, as on the year pages)
# Inputs: model_years.csv (per-year sold, complaints, serious share) and run_log.txt's market rate per model year; issues = each year's top
# problem areas (data/years.json) weighted by that year's complaints. build.py's k5_split.py reads the output. usage: py tools/k5_split.py
import csv, json, os, re, ast
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
OUTD = next(d for d in os.scandir(LEMON) if d.name.startswith('v3-unreliable')).path + r'\data\out'
rows = {int(r['year']): r for r in csv.DictReader(open(os.path.join(OUTD, 'model_years.csv'), encoding='utf-8')) if r['family'] == 'Kia Optima'}
log = open(os.path.join(OUTD, 'run_log.txt'), encoding='utf-8').read()
MKT = ast.literal_eval(re.search(r'market complaints per 100k by model year: (\{.*?\})', log).group(1))
fam = {r['family']: r for r in csv.DictReader(open(os.path.join(HERE, 'data', 'family_rates.csv'), encoding='utf-8'))}['Kia Optima']
# the study's expected count uses unrounded market rates; scale the rounded log rates so all 13 years give the study's own 1,496.2
scale = float(fam['expected']) / sum(int(rows[y]['sold']) * MKT[y] / 1e5 for y in range(2010, 2023))
YJ = {v['y']: v for f in json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8')) if f['id'] == 'kia-optima' for v in f['years']}
def part(a, b, name):
    ys = range(a, b + 1)
    n = sum(int(rows[y]['complaints']) for y in ys); sold = sum(int(rows[y]['sold']) for y in ys)
    exp = sum(int(rows[y]['sold']) * MKT[y] / 1e5 for y in ys) * scale
    ser = sum(float(rows[y]['serious_pct']) * int(rows[y]['complaints']) for y in ys) / n
    worst = max(ys, key=lambda y: float(rows[y]['per_100k']))
    iss = {}
    for y in ys:
        for p, k in YJ[y]['parts']: iss[p] = iss.get(p, 0) + k * YJ[y]['n']
    issues = [[p, round(v / n)] for p, v in sorted(iss.items(), key=lambda kv: -kv[1])[:3]]
    return dict(name=name, years=f'{a}-{b}', n_years=b - a + 1, sold=sold, n=n, per100k=round(n / sold * 1e5, 1), expected=round(exp, 1),
                li=round(n / exp * 100), serious=round(ser, 1), worst=str(worst), worst_per100k=float(rows[worst]['per_100k']), issues=issues)
out = {'kia-optima': part(2010, 2020, 'Kia Optima'), 'kia-k5': part(2021, 2022, 'Kia K5'),
       'note': 'Kia Optima (study family 2010-2022) split at the 2021 rename to K5; numbers from the study files, see tools/k5_split.py'}
json.dump(out, open(os.path.join(HERE, 'data', 'k5_split.json'), 'w', encoding='utf-8'), indent=1)
print(json.dumps(out, indent=1))
