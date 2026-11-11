# YouTube score per BMW engine per model year (11-10, Elijah: "a YouTube score per year per engine too").
# Same scoring as 3 Lemon Index/data/yt/yt_score.py (praise vs trouble words, title 3x, transcript once and scaled to 10 minutes,
# lean = (P - N) / (P + N + 4), year score = 50 + 50 x the view-weighted average lean), so engine scores sit on the same 0-100 scale as
# the model-year YouTube scores. Attribution (each video counts once):
#   - the title names an engine code (N54, B58 ...): the video counts for that engine, in the title's model years, or spread evenly over
#     the years that engine was sold in the study's model (no year in the title)
#   - else the title names a version (335i, X5 xDrive35i, M340i): it counts for the engine that version used in that model year, but only
#     where that version name maps to exactly one engine that year (2012 "328i" was both the N52 and the N20, so it doesn't count)
#   - else: not attributed to any engine (it stays in the model-year score, shown as "all engines combined")
# Sources: the existing per-generation studies (top 200 videos + captions) and a small engine-code search pull (titles only, no
# transcripts; data_bmw_yt_pull.py) -- NOT scored (review 11-10): its queries were worded "reliability" for some engines and "problems" /
# "years to avoid" for others, so title-only scores mostly echoed our own query words, and with no year in the title one search
# result was spread over every year of the engine. A year shows a score only with at least 3 videos' worth of weight. Each year also
# records how many distinct videos fed it and how many of them name that model year in the title (the rest are about the generation).
import glob, json, math, os, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
YT = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\yt'
_src = open(os.path.join(YT, 'yt_score.py'), encoding='utf-8').read()
_a = _src.index('PRAISE = re.compile'); _b = _src.index('def transcript')
exec(_src[_a:_b])   # PRAISE, TROUBLE, NOTPROB, YR4, YR2, years_in (kept identical to the site's YouTube score)
S = json.load(open(os.path.join(HERE, 'data', 'bmw_specs.json'), encoding='utf-8'))
V = S['versions']; EY = S['engine_years']
SY = json.load(open(os.path.join(YT, 'study_years.json'), encoding='utf-8'))
CODE = re.compile(r'\b(M54|N52|N54|N55|N20|B46|B48|B58|N62|N63|S55|S58|S63|S54|S65)\b', re.I)
VER = re.compile(r'\b(M?\d{3}(?:i|e|d|is|xi|ci)|[xX][1-7] ?[xs]?[Dd]rive ?\d\d[ie]|[xX][1-7] ?M\d0i|M\d0i)\b')
ENG_YEARS = {c: sorted(int(y) for y in ys) for c, ys in EY.items()}
def fam_of_study(st):
    m = re.match(r'(bmw-(?:\d-series|x\d))', st)
    return m.group(1) if m else ('bmw-3-series' if st == 'bmw-f30' else None)
def vkey(name):
    s = name.upper().replace(' ', '')
    m = re.match(r'^(M?)(\d{3})(IS|D|E|CI|XI|I)?', s)
    if m: return (m.group(1) + m.group(2), {'D': 'd', 'E': 'e', 'IS': 'is', 'CI': 'ci'}.get(m.group(3) or '', 'i'))
    m = re.match(r'^(X\d)(?:[XS]DRIVE)?(\d\d[IE]|M\d0I)', s)
    return (m.group(1), m.group(2).lower()) if m else None
def code_for(fam, y, name):
    vk = vkey(name)
    if not vk: return None
    codes = set()
    for v in V.get(fam, {}).get(str(y), []):
        m = v['model'].upper().replace(' ', '')
        if vk[0].startswith('X'):
            mm = re.match(r'^(X\d)(?:[XS]DRIVE)?(\d\d[IE]|M\d0I)', m)
            if mm and (mm.group(1), mm.group(2).lower()) == vk: codes.add(v['code'])
        elif v.get('vk') and v['vk'][0] == vk[0] and (v['vk'][1] == vk[1] or {v['vk'][1], vk[1]} <= {'i', 'ci'}): codes.add(v['code'])
    return codes.pop() if len(codes) == 1 and None not in codes else None
def transcript(st, vid):
    fs = glob.glob(os.path.join(YT, st, 'captions', vid + '.en-orig.json3')) or glob.glob(os.path.join(YT, st, 'captions', vid + '.en*.json3'))
    if not fs: return ''
    return ' '.join(''.join(x.get('utf8', '') for x in e.get('segs') or []) for e in json.load(open(fs[0], encoding='utf-8')).get('events', []))
def lean_of(t, tx):
    tp = len(PRAISE.findall(t)); tt = len(TROUBLE.findall(t)) - len(NOTPROB.findall(t))
    xp = len(PRAISE.findall(tx)); xt = len(TROUBLE.findall(tx)) - len(NOTPROB.findall(tx))
    k = 1500 / max(1500, len(tx.split()))
    P, N = 3 * tp + xp * k, 3 * max(0, tt) + max(0, xt) * k
    return (P - N) / (P + N + 4)
Y = collections.defaultdict(lambda: collections.defaultdict(lambda: dict(w=0.0, lean=0.0, n=0.0, titles=[], via=collections.Counter(), ids=set(), named=set())))
seen = set()
def add(code, years, v, lean, via, named=()):
    years = [y for y in years if y in ENG_YEARS.get(code, [])]
    if not years: return False
    share = 1 / len(years); wv = math.log10(max(10, v['views'] or 10))
    for y in years:
        d = Y[code][y]; w = wv * share; d['w'] += w; d['lean'] += w * lean; d['n'] += share; d['via'][via] += share
        d['ids'].add(v['id'])
        if y in named: d['named'].add(v['id'])
        d['titles'].append((v['views'] or 0, v['title'], v['id']))
    return True
studies = sorted(d for d in os.listdir(YT) if d.startswith('bmw-') and os.path.exists(os.path.join(YT, d, 'top.json')))
att = collections.Counter()
for st in studies:
    fam = fam_of_study(st); gy = [int(y) for y in SY.get(st, [])]
    if not fam: continue
    for v in json.load(open(os.path.join(YT, st, 'top.json'), encoding='utf-8')):
        if v['id'] in seen: continue
        t = v['title']; ty = years_in(t, 1973, 2026); ys = ty or gy
        codes = {c.upper().replace('B46', 'B48') for c in CODE.findall(t)}
        if codes:
            seen.add(v['id']); ln = lean_of(t, transcript(st, v['id']))
            for c in codes:
                fam_years = [y for y in ys if any(x['code'] == c for x in V.get(fam, {}).get(str(y), []))] or ys
                if add(c, fam_years, v, ln, 'engine code in title', ty or ()): att['code'] += 1
            continue
        vers = VER.findall(t)
        if not vers: continue
        per = collections.defaultdict(list)
        for name in vers:
            for y in ys:
                c = code_for(fam, y, name)
                if c: per[c].append(y)
        if not per: continue
        seen.add(v['id']); ln = lean_of(t, transcript(st, v['id']))
        for c, yl in per.items():
            if add(c, sorted(set(yl)), v, ln, 'version in title', ty or ()): att['version'] += 1
PULL = os.path.join(HERE, 'data', 'cache', 'bmw_engine_videos.json')
USE_PULL = False   # see the header: query-worded, title-only, year-less -> not a fair per-year score
if USE_PULL and os.path.exists(PULL):
    for q, vids in json.load(open(PULL, encoding='utf-8')).items():
        for v in vids:
            if v['id'] in seen: continue
            codes = {c.upper().replace('B46', 'B48') for c in CODE.findall(v['title'])}
            if not codes: continue
            seen.add(v['id']); ty = years_in(v['title'], 1973, 2026); ln = lean_of(v['title'], '')
            for c in codes:
                if add(c, ty or ENG_YEARS.get(c, []), v, ln, 'engine search (titles only)'): att['pull'] += 1
OUTD = {}
for c, ys in Y.items():
    OUTD[c] = {}
    for y, d in sorted(ys.items()):
        ok = d['n'] >= 3
        OUTD[c][str(y)] = dict(score=round(50 + 50 * d['lean'] / d['w']) if ok and d['w'] else None, weight=round(d['n'], 1), videos=len(d['ids']), named=len(d['named']),
                               via={k: round(v, 1) for k, v in d['via'].items()},
                               top=[dict(id=i, title=t, views=vw) for vw, t, i in sorted(d['titles'], reverse=True)[:3]])
json.dump(OUTD, open(os.path.join(HERE, 'data', 'bmw_engine_yt.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
scored = sum(1 for c in OUTD.values() for y in c.values() if y['score'] is not None); tot = sum(len(ys) for ys in ENG_YEARS.values())
print('attributed', dict(att), '| engine-years with a YouTube score', scored, 'of', tot)
for c in sorted(OUTD): print(c, {y: (d['score'], d['videos']) for y, d in OUTD[c].items() if d['score'] is not None})
