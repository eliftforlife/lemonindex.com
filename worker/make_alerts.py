# Writes alerts_worker.dist.js (the file uploaded to the lemon-alerts Worker) from alerts_worker.js + assets/cars.json (model names)
# + data/extras_local*.json (the NHTSA make/model names our pages use). Re-run and redeploy when models are added; until then a signup
# for a new model still works through the vPIC check.
import glob, json, os, re
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
cars = {k: v[0] for k, v in json.load(open(os.path.join(R, 'assets', 'cars.json'), encoding='utf-8')).items()}
pairs = set()
for p in glob.glob(os.path.join(R, 'data', 'extras_local*.json')):
    for fid, ys in json.load(open(p, encoding='utf-8')).items():
        for e in ys.values():
            for mk, md, n in e.get('names', []): pairs.add(re.sub(r'[^A-Z0-9]', '', mk.upper()) + '|' + re.sub(r'[^A-Z0-9]', '', md.upper()))
src = open(os.path.join(H, 'alerts_worker.js'), encoding='utf-8').read(); assert src.count('__CARS__') == 1 and src.count('__PAIRS__') == 1
src = src.replace('__CARS__', json.dumps(cars, ensure_ascii=False, separators=(',', ':'))).replace('__PAIRS__', json.dumps(sorted(pairs), separators=(',', ':')))
open(os.path.join(H, 'alerts_worker.dist.js'), 'w', encoding='utf-8').write(src)
print('alerts worker:', len(cars), 'models,', len(pairs), 'NHTSA names')
