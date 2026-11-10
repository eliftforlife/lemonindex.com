# Engine codes (11-10, Lemon growth project 2A): which OBD-II trouble codes owners name in their NHTSA complaints, and on which cars.
# Scans the complaint text once (5-10 min) and caches the counts to data/engine_codes.json; build.py only reads that JSON.
#   py -X utf8 engine_codes.py
# Only counts and short themes are kept (never complaint text, names, VINs or places), so nothing personal reaches the site.
import collections, json, os, re, sqlite3, statistics, sys
sys.stdout.reconfigure(encoding='utf-8')
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
YR = json.load(open('data/years.json', encoding='utf-8')); XL = json.load(open('data/extras_local.json', encoding='utf-8'))
NAME = {f['id']: f['name'] for f in YR}
key = {}   # (NHTSA make, model, year) -> our model id, same mapping as data_gap.py
for f in YR:
    for y, x in XL.get(f['id'], {}).items():
        for mk, md, n in (x.get('names') or []):
            if n >= 2: key[(mk, md, int(y))] = f['id']
CODE = re.compile(r'\b([PBCU][0-3][0-9A-F]{3})\b')
# 11-10 review: vehicle model names that look like codes (Chevy/GMC C1500-C3500 pickups, Mazda B-series pickups, Dodge B-vans).
# Measured on the complaint text: 50-95% of these sat right after a year or a make, so they name trucks, not trouble codes.
NOT_CODES = {'C1500', 'C2500', 'C3500', 'B1500', 'B2000', 'B2200', 'B2300', 'B2500', 'B2600', 'B3000', 'B3500', 'B150E', 'B250E', 'B350E'}
# Short themes in our own words, matched on the owner's text (counted, never quoted)
THEMES = [('stalls or shuts off', r'\bstall|shut(s|ting)? off|shut down|died while|engine died|cut(s)? off'),
          ('loses power or goes into limp mode', r'loss of power|lost power|loses power|limp mode|reduced power|no power|lack of power|hesitat'),
          ('shakes, runs rough or misfires', r'misfir|rough idle|running rough|runs rough|shak|stutter|sputter'),
          ("won't start or hard to start", r"won'?t start|would not start|no start|hard to start|failed to start|cranks? but"),
          ('check engine light comes on', r'check engine|engine light|service engine|\bmil\b|malfunction indicator'),
          ('transmission slips or shifts hard', r'slip|hard shift|harsh shift|jerk|won\'?t shift|stuck in gear|shudder'),
          ('uses or leaks oil', r'oil consumption|burn(s|ing)? oil|low oil|oil leak|adding oil'),
          ('overheats', r'overheat|temperature gauge|coolant leak'),
          ('fuel smell or fuel leak', r'fuel smell|gas smell|smell of gas|fuel leak|gas leak'),
          ('rattles or knocks', r'rattl|knock|ticking|tapping'),
          ('brakes or ABS act up', r'\babs\b|brake'),
          ('warning lights and electrical faults', r'warning lights|dash lights|electrical|battery|alternator')]
TH = [(t, re.compile(p, re.I)) for t, p in THEMES]
c = sqlite3.connect(DB)
D = collections.defaultdict(lambda: dict(n=0, makes=collections.Counter(), models=collections.Counter(), years=collections.Counter(), comps=collections.Counter(), themes=collections.Counter(), crash=0, fire=0, towed=0, miles=[]))
seen = set(); total = 0
for odi, mk, md, yr, comp, d, crash, fire, towed, miles in c.execute(
        "select odino, make, model, year, comp, descr, crash, fire, towed, miles from rows where descr glob '*[PBCU][0-3][0-9A-F][0-9A-F][0-9A-F]*'"):
    if odi in seen: continue
    codes = set(CODE.findall((d or '').upper())) - NOT_CODES
    if not codes: continue
    seen.add(odi); total += 1
    try: y = int(yr)
    except (TypeError, ValueError): y = None
    fid = key.get((mk, md, y)) if y else None
    th = [t for t, r in TH if r.search(d or '')]
    for code in codes:
        x = D[code]; x['n'] += 1; x['makes'][(mk or '').title()] += 1
        if fid: x['models'][fid] += 1; x['years'][(fid, y)] += 1
        for cc in (comp or '').split(','):
            if cc.strip(): x['comps'][cc.strip().title()] += 1
        x['themes'].update(th)
        x['crash'] += crash == 'Y'; x['fire'] += fire == 'Y'; x['towed'] += towed == 'Y'
        try:
            m = int(miles or 0)
            if 0 < m < 400000: x['miles'].append(m)
        except ValueError: pass
out = {}
for code, x in D.items():
    if x['n'] < 3: continue
    out[code] = dict(n=x['n'], makes=x['makes'].most_common(6),
                     models=[[i, NAME[i], k] for i, k in x['models'].most_common(10)],
                     years=[[i, NAME[i], y, k] for (i, y), k in x['years'].most_common(10)],
                     comps=x['comps'].most_common(4), themes=x['themes'].most_common(5),
                     crash=x['crash'], fire=x['fire'], towed=x['towed'],
                     miles=int(statistics.median(x['miles'])) if len(x['miles']) >= 5 else None)
json.dump(dict(total=total, codes=dict(sorted(out.items(), key=lambda kv: -kv[1]['n']))), open('data/engine_codes.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('complaints with a code', total, '| codes kept (3+)', len(out), '| 20+', sum(1 for v in out.values() if v['n'] >= 20))
