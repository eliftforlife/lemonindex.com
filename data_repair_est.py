# 11-23 repair estimates on the site (money plan m33): packs the repair-estimate dataset (3 Lemon Index/data/repair_est/scored/<gen>.json,
# made by that folder's score.py: AI labor hours + parts per generation x 69 repairs, checked against what owners reported paying, with a
# 0-100 confidence score and a band) into one compact file the build reads:
#   data/repair_est.json = {"rate": 140, "made": date, "gens": {gen id: {"i": popularity rank (queue order), "m": model id, "y": [first, last], "sy": [site first, last],
#       "e": {engine key: label}, "r": {repair: [[engine key|null, hours lo, hours hi, parts lo, parts hi, band H|M|L|X, score, lead a|o,
#       owners n, owners median, owners lo, owners hi], ...]}}}, "names": {repair: name}}
#   band X = Hidden (under 30): no number is shown. lead o = owner bills from this generation lead (5+, or 3-4 that disagree with the AI by
#   more than half), so "What owners paid" is the main number; a = the estimate (hours x the visitor's shop rate + parts).
# Repairs the worker marked "na" (no such part on this car) are left out. Nothing here is invented: every number is from the scored files.
#   usage: py -X utf8 data_repair_est.py
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\repair_est'
BAND = {'High': 'H', 'Medium': 'M', 'Low': 'L', 'Hidden': 'X'}
num = lambda x: (int(x) if float(x).is_integer() else round(float(x), 1)) if x is not None else None
q = {g['id']: g for g in json.load(open(os.path.join(SRC, 'queue.json'), encoding='utf-8'))['gens']}
names = {k: v['name'] for k, v in json.load(open(os.path.join(SRC, 'repairs.json'), encoding='utf-8'))['repairs'].items()}
out, rate, n_rows = {}, None, 0
for p in sorted(glob.glob(os.path.join(SRC, 'scored', '*.json'))):
    d = json.load(open(p, encoding='utf-8')); gid = d['id']; g = q.get(gid)
    if not g: continue
    rate = rate or d.get('default_rate')
    r = {}
    for k, x in d['repairs'].items():
        if x.get('status') != 'ok' or not x.get('variants'): continue
        rows = []
        for v in x['variants']:
            a, c, o, sh = v['ai'], v['confidence'], v.get('owners') or {}, v['show']
            lead = 'o' if sh['source'] == 'owners' else 'a'
            own = [o['n'], num(o['median']), num(o['mid_half'][0]), num(o['mid_half'][1])] if lead == 'o' and o.get('level') == 'gen' else [0, None, None, None]
            rows.append([v.get('engine'), num(a['hours'][0]), num(a['hours'][1]), num(a['parts'][0]), num(a['parts'][1]), BAND[c['band']], c['score'], lead, *own])
        r[k] = rows; n_rows += len(rows)
    out[gid] = dict(i=g['i'], m=d['model'], y=d['years'], sy=g['site_years'], e={e['key']: e['label'] for e in d.get('engines') or []}, r=r)
json.dump(dict(rate=rate or 140, made=max(json.load(open(p, encoding='utf-8')).get('scored', '') for p in glob.glob(os.path.join(SRC, 'scored', '*.json'))[:50]),
               names=names, gens=out), open(os.path.join(HERE, 'data', 'repair_est.json'), 'w', encoding='utf-8'), separators=(',', ':'), sort_keys=True)
print(f'repair estimates: {len(out)} generations, {n_rows:,} rows -> data/repair_est.json ({os.path.getsize(os.path.join(HERE, "data", "repair_est.json")) / 1e6:.1f} MB)')
