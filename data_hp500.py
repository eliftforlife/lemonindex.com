# 11-25: horsepower of every regular-model generation, for /best/cheapest-500-hp-cars/ (hp500_page.py).
# Source: 3 Lemon Index/data/hp/<gen id>.json (613 generations; per version: trim, engine, years, hp, src URLs; gen notes).
# Writes data/hp500_hp.json with every version rated 450 hp or more (the page needs 500+; 450-499 kept for a "just under" line),
# plus the site model id of each generation (3 Lemon Index/data/repair_est/queue.json). Nothing is typed by hand here.
# Run: py -X utf8 data_hp500.py
import glob, json, os
D = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data'
Q = {g['id']: g for g in json.load(open(os.path.join(D, 'repair_est', 'queue.json'), encoding='utf-8'))['gens']}
out = {}
for f in sorted(glob.glob(os.path.join(D, 'hp', '*.json'))):
    g = json.load(open(f, encoding='utf-8'))
    vs = [v for v in g.get('variants', []) if isinstance(v.get('hp'), (int, float)) and v['hp'] >= 450 and v.get('src')]
    if not vs: continue
    q = Q.get(g['gen']) or {}
    out[g['gen']] = {'name': g['name'], 'model': q.get('model'), 'years': g['years'], 'notes': g.get('notes') or '',
                     'variants': [{k: v[k] for k in ('trim', 'engine', 'years', 'hp', 'perf', 'src', 'conf') if k in v} for v in vs]}
json.dump({'note': 'Factory hp per version, from 3 Lemon Index/data/hp (data_hp500.py). 450+ hp only.', 'gens': out},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'hp500_hp.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(out), 'generations,', sum(len(g['variants']) for g in out.values()), 'versions')
