# 11-23 repair estimates for motorcycles, supercars and planes (money plan m33, job E): packs the m33-x dataset
# (3 Lemon Index/data/repair_est_x/{moto,super,plane}/scored/<unit>.json, made by that folder's score.py: AI labor hours + parts, or one
# all-in total for big jobs, per unit x repair x version, checked against what owners reported paying, 0-100 confidence + band) into one
# compact file the build reads (repair_est.py x_block):
#   data/repair_est_x.json = {"made": date, "kinds": {kind: {"rate": default $/h, "who": rate label, "names": {repair: name}}},
#       "units": {unit id: {"k": kind, "i": popularity rank, "u": page url, "n": name, "nick": generation name, "y": [first, last],
#           "e": {version key: label}, "a": [every repair that applies], "pe": [repairs priced per engine (twins)],
#           "o": {repair: which versions it applies to, in words (the est file's "only", e.g. "Twin-Cooled models"), when it isn't all of them},
#           "r": {repair: [[version|null, hours lo, hours hi, parts lo, parts hi, band H|M|L, score, lead a|o, owners n, median, lo, hi, src], ...]}}}}
#   Total-form jobs (plane overhauls, paint...) are stored as hours 0-0 and parts = the all-in total, so they don't move with the shop rate.
#   Only rows at Low or better are kept: Hidden rows (score under 30) are left out, so no number is shown for them (job E: "hide Hidden").
#   lead o = this unit's own owner bills lead (scoring rule: 5+, or 3-4 that disagree with the AI by more than half); src = where those owner
#   prices came from: n = NHTSA complaint bills (mostly dealers), y = said in owner YouTube videos, m = both.
# Nothing is invented: every number is copied from the scored files.
#
# RE-RUN after the cost pass (11-23: scratchpad/ownerprice_run/driver.py was running costpass on the moto/super/plane YouTube folders,
# 13 of 122 done; these pages were built from the scores that existed before it finished). When it's done:
#   cd "3 Lemon Index/data/repair_est_x" && py -X utf8 owner_prices.py && py -X utf8 score.py moto && py -X utf8 score.py super && py -X utf8 score.py plane
#   cd C:/Users/elift/Code/lemon-subtest && py -X utf8 data_repair_est_x.py      (then a normal full build + deploy_queue.py)
# More owner prices can lift rows from Hidden to Low+ (they appear) and make owner bills the main number on more rows.
#   usage: py -X utf8 data_repair_est_x.py
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\repair_est_x'
BAND = {'High': 'H', 'Medium': 'M', 'Low': 'L', 'Hidden': 'X'}
PER_ENGINE = {'engine-overhaul', 'turbine-overhaul', 'hot-section', 'prop-overhaul', 'prop-governor', 'magneto', 'alternator', 'starter', 'oil-change'}   # WORKER.md: plane twins
num = lambda x: (int(x) if float(x).is_integer() else round(float(x), 1)) if x is not None else None
kinds, units, made, count = {}, {}, '', {}
for kind in ('moto', 'super', 'plane'):
    rp = json.load(open(os.path.join(SRC, kind, 'repairs.json'), encoding='utf-8'))
    kinds[kind] = dict(rate=rp['default_rate'], who=rp['rate_label'], names={k: v['name'] for k, v in rp['repairs'].items()})
    q = {u['id']: u for u in json.load(open(os.path.join(SRC, kind, 'queue.json'), encoding='utf-8'))['units']}
    c = count.setdefault(kind, {'H': 0, 'M': 0, 'L': 0, 'X': 0, 'units': 0, 'empty': []})
    for p in sorted(glob.glob(os.path.join(SRC, kind, 'scored', '*.json'))):
        d = json.load(open(p, encoding='utf-8')); u = q.get(d['id'])
        if not u: continue
        made = max(made, d.get('scored', ''))
        tw = {v['key'] for v in d.get('versions') or [] if 'twin' in (v.get('tags') or [])}
        r, a, pe, on = {}, [], [], {}
        for k, x in d['repairs'].items():
            if x.get('status') != 'ok' or not x.get('variants'): continue
            a.append(k); rows = []
            for v in x['variants']:
                ai, cf, o, sh = v['ai'], v['confidence'], v.get('owners') or {}, v['show']
                b = BAND[cf['band']]; c[b] += 1
                if b == 'X': continue
                if 'total' in ai and ai.get('total'): h0 = h1 = 0; p0, p1 = ai['total']
                else: h0, h1 = ai['hours']; p0, p1 = ai['parts']
                lead = 'o' if sh['source'] == 'owners' and o.get('level') == 'unit' else 'a'
                src = o.get('sources') or {}
                s = ('m' if src.get('nhtsa') and src.get('yt') else 'n' if src.get('nhtsa') else 'y') if lead == 'o' else ''
                own = [o['n'], num(o['median']), num(sh['low']), num(sh['high']), s] if lead == 'o' else [0, None, None, None, '']
                rows.append([v.get('version'), num(h0), num(h1), num(p0), num(p1), b, cf['score'], lead, *own])
            if rows:
                r[k] = rows
                if x.get('only'): on[k] = x['only']
            if kind == 'plane' and k in PER_ENGINE and tw and any(rw[0] in tw or rw[0] is None for rw in rows): pe.append(k)
        if not r: c['empty'].append(d['id']); continue
        c['units'] += 1
        units[d['id']] = dict(k=kind, i=u['i'], u=u['url'], n=d['name'], nick=u.get('nick') or '', y=u.get('site_years') or d['years'],
                              e={v['key']: v['label'] for v in d.get('versions') or []}, a=a, pe=pe, o=on, r=r)
out = os.path.join(HERE, 'data', 'repair_est_x.json')
json.dump(dict(made=made, kinds=kinds, units=units,
               rerun='Built 11-23 from the scores that existed before the moto/super/plane cost pass finished. Re-run owner_prices.py + score.py (each kind) in 3 Lemon Index/data/repair_est_x, then data_repair_est_x.py, then build + deploy (see data_repair_est_x.py).'),
          open(out, 'w', encoding='utf-8'), separators=(',', ':'), sort_keys=True)
for kind, c in count.items():
    print(f'{kind}: {c["units"]} units shown; rows High {c["H"]}, Medium {c["M"]}, Low {c["L"]} shown; Hidden {c["X"]} left out' + (f'; no Low+ rows: {", ".join(c["empty"])}' if c['empty'] else ''))
print(f'-> data/repair_est_x.json ({os.path.getsize(out) / 1e6:.2f} MB)')
