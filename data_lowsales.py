# 11-11 (Elijah): low-sales years on the study's model pages. A model year whose cited U.S. sales are under 20,000 can't get a Lemon Index,
# so the study left it out; it now shows as "complaints only, too few sold to score": its complaint count, top problems, recalls and its own
# year page, never a score, never a best/worst-year pick. Same counting as everywhere else (data_new_models.run(): complaints filed within
# 3 years of the model year; 2023-2025 every complaint so far) and the study's own sales table (3 Lemon Index/data/sales.csv, one cited URL per
# figure). Only years with complaints AND a known sales figure under 20,000 are added: a year we have no sales for stays out (it may be a
# different vehicle under the same name, or a year that wasn't sold here). Writes data/years_low.json, extras_local_low.json, extras_api_low.json.
import csv, json, os, sys, collections, concurrent.futures as cf
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = sys.argv[:1]   # data_new_models reads argv as its slug filter; it must not run its plan here
src = open(os.path.join(HERE, 'data_new_models.py'), encoding='utf-8').read()
src = src[:src.index('def load(n):')]   # its functions + the API helpers, not its plan loop
G = {'__file__': os.path.join(HERE, 'data_new_models.py'), '__name__': 'data_new_models'}
exec(compile(src, 'data_new_models.py', 'exec'), G)
LEMON, FAMILIES, run, API, MIN_SOLD = G['LEMON'], G['FAMILIES'], G['run'], G['API'], G['MIN_SOLD']

S, SRC = collections.defaultdict(dict), {}
for r in csv.DictReader(open(os.path.join(LEMON, 'data', 'sales.csv'), encoding='utf-8')):
    S[r['family']][int(r['year'])] = int(r['us_sales']); SRC.setdefault(r['family'], r.get('source') or '')
for r in csv.DictReader(open(os.path.join(LEMON, 'data', 'sales_manual.csv'), encoding='utf-8')):
    if '-' not in r['year']: S[r['family']].setdefault(int(r['year']), int(r['us_sales'])); SRC.setdefault(r['family'], r.get('source') or '')
YJ = {f['name']: f for f in json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8'))}
CARS = {r['family']: dict(brand=r['brand']) for r in csv.DictReader(open(os.path.join(HERE, 'data', 'family_rates.csv'), encoding='utf-8'))}

YL, XLL, XAL = {}, {}, {}
for name, make, rx, fam, seg in FAMILIES:
    f = YJ.get(name)
    if not f or not S.get(fam): continue
    have = {v['y'] for v in f['years']}
    p = dict(name=name, brand=CARS.get(name, {}).get('brand', name.split(' ')[0]), seg=seg, make=make, rx=rx,
             sales=dict(manual={str(y): v for y, v in S[fam].items()}, url=SRC.get(fam, ''), note='study sales table'))
    if not any(v < MIN_SOLD for v in S[fam].values()): continue   # nothing under 20,000: no low-sales year possible
    fy, car, xl, extra, rep = run(f['id'], p)
    low = [v for v in fy['years'] if v.get('low') and v['y'] not in have]
    if not low: continue
    YL[f['id']] = low; XLL[f['id']] = {str(v['y']): xl[str(v['y'])] for v in low}
    API['MAKES'][name] = make.split('|')
    def one(y, e=None):
        e = xl[str(y)]; nms = API['main_names'](e) if e['names'] else [(make, name.split(' ', 1)[1].upper())]
        return str(y), {'recalls': API['recalls'](str(y), nms), 'safety': API['safety'](str(y), nms, name) if y >= 2011 else None, 'mpg': API['mpg'](name, y)}
    with cf.ThreadPoolExecutor(6) as ex: XAL[f['id']] = dict(ex.map(one, [v['y'] for v in low]))
    print(f"{name}: + {', '.join(f'{v['y']} ({v['n']} complaints, {v['low']['sold']:,} sold)' for v in low)}", flush=True)
json.dump(YL, open(os.path.join(HERE, 'data', 'years_low.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(XLL, open(os.path.join(HERE, 'data', 'extras_local_low.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(XAL, open(os.path.join(HERE, 'data', 'extras_api_low.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(YL), 'models,', sum(len(v) for v in YL.values()), 'low-sales years')
