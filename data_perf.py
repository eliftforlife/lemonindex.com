# Performance-car pages (11-11, Elijah: "do first full performance + engine + yt pull for BMW M3 Comp so I can see how the layout looks,
# then we dupe for other super cars and performance cars"). The computed half of a performance page, next to the hand-sourced
# data/perf/<slug>.json (specs, engines, sources). Everything here is plain counting from data we already hold:
#   - NHTSA owner complaints per model year (3 Lemon Index/data/complaints.db, distinct complaint ids, the car's NHTSA model names)
#   - per generation: how many complaints mention each known engine issue in their own words (the issue's regex in <slug>.json)
#   - NHTSA recalls per model year (api.nhtsa.gov recallsByVehicle, cached in data/cache/)
#   - per YouTube study (one per generation, plus the engine and trim studies auto_gens.py runs): the most-viewed videos, and the share of
#     videos that praise / complain about each topic. A topic counts for a video when a praise word (or a trouble word) sits within ~100
#     characters of it in the title or transcript, the same rule as yt_score.py's problem topics, with yt_score.py's own word lists.
#   py -X utf8 data_perf.py bmw-m3          -> data/perf/bmw-m3.auto.json
# perf_page.py re-reads the YouTube part at build time (when the study folders exist on this PC), so pages fill in as pulls land.
import glob, json, os, re, sqlite3, sys, time, urllib.request, urllib.error, collections
HERE = os.path.dirname(os.path.abspath(__file__))
YT = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\yt'
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
PRAISE_TOPICS = {   # what owners and reviewers say they love about a performance car
    'Engine sound': r'(engine|exhaust) (sound|note|noise)|sounds? (amazing|incredible|insane|so good|unreal)|\bscream',
    'Power and acceleration': r'\bfast\b|accelerat|\bquick\b|powerful|\btorque\b|\bpull(s)? (hard|like)',
    'Handling and steering': r'handling|steering|cornering|\bchassis\b|\bgrip\b|\bbalance(d)?\b',
    'Manual gearbox': r'\bmanual\b|stick ?shift|six.?speed|6.?speed',
    'Everyday comfort': r'daily( driver)?|comfortable|practical|commut|four doors|back ?seats?',
    'Interior and seats': r'interior|carbon (bucket )?seats|bucket seats|cockpit',
    'Looks': r'\blooks\b|\bdesign\b|beautiful|gorgeous|stunning',
    'Value': r'\bvalue\b|bargain|for the money|depreciat',
}

def _load(p, d=None):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else d

def car(slug): return _load(os.path.join(HERE, 'data', 'perf', f'{slug}.json'))

def _words():
    src = open(os.path.join(YT, 'yt_score.py'), encoding='utf-8').read(); g = {'re': re}
    exec(src[src.index('PRAISE = re.compile'):src.index('def years_in')], g)
    c = open(os.path.join(YT, 'content.py'), encoding='utf-8').read(); a = c.index('CAR = {'); exec(c[a:c.index('\n}\n', a) + 3], g)
    return g

def _transcript(st, vid):
    fs = glob.glob(os.path.join(YT, st, 'captions', vid + '.en-orig.json3')) or glob.glob(os.path.join(YT, st, 'captions', vid + '.en*.json3'))
    if not fs: return ''
    try: return ' '.join(''.join(x.get('utf8', '') for x in e.get('segs') or []) for e in json.load(open(fs[0], encoding='utf-8')).get('events', []))
    except Exception: return ''

EXC = r'hot ?wheels|diecast|die-cast|lego|model kit|forza|\bgta\b|beamng|\brc (car|truck)\b|matchbox|\btoys?\b|roblox|minecraft|gran turismo|assetto|need for speed|\bnfs\b'
def yt_study(st, extra=None):
    """one study folder -> videos used, praise / trouble topic shares (%), the 3 most-viewed videos. None if not pulled yet."""
    p = os.path.join(YT, st, 'top.json')
    if not os.path.exists(os.path.join(YT, st, 'videos.json')) or not os.path.exists(p): return None
    g = _words(); PR, TR, NP = g['PRAISE'], g['TROUBLE'], g['NOTPROB']
    trouble = {k: v for k, v in g['CAR'].items() if k not in g['NOT_PROBLEMS']}; trouble.update(extra or {})
    vids = [v for v in json.load(open(p, encoding='utf-8')) if not re.search(EXC, v['title'], re.I)]
    pc, tc, n = collections.Counter(), collections.Counter(), 0
    for v in vids:
        blob = v['title'] + ' . ' + _transcript(st, v['id']); n += 1
        def near(rx, W):
            for m in re.finditer(rx, blob, re.I):
                w = blob[max(0, m.start() - 100):m.end() + 100]
                if W is TR:
                    if TR.search(w) and not NP.search(w): return True
                elif W.search(w): return True
            return False
        for k, rx in PRAISE_TOPICS.items():
            if near(rx, PR): pc[k] += 1
        for k, rx in trouble.items():
            if near(rx, TR): tc[k] += 1
    top = sorted(vids, key=lambda v: -(v.get('views') or 0))[:3]
    pct = lambda c: [[k, round(100 * x / n)] for k, x in c.most_common(4) if n and x / n >= .05]
    return dict(videos=n, praise=pct(pc), trouble=pct(tc), top=[dict(id=v['id'], title=v['title'], views=v.get('views') or 0, ch=v.get('channel') or '') for v in top])

def studies(D):
    """every study a page uses: per generation (site models), the car's own study, a trim study (e.g. the M3 Competition), one per engine"""
    ids = [g.get(k) for g in D['gens'] for k in ('yt_study', 'comp_study')] + [D.get('yt_study')] + [e.get('study') for e in D['engines'].values()]
    return list(dict.fromkeys(i for i in ids if i))

def yt_all(D):
    return {st: yt_study(st, D.get('topics_extra')) for st in studies(D)}

def nhtsa(D):
    """complaints per model year, and per generation how many complaints mention each engine issue (with 2 example complaint ids)"""
    if not os.path.exists(DB): return None
    c = sqlite3.connect(DB); n = D['nhtsa']
    q = f"select odino, year, max(descr), group_concat(comp, '|') from rows where make=? and model in ({','.join('?' * len(n['models']))}) and year between 1990 and 2026 group by odino"
    allr = c.execute(q, [n['make']] + n['models']).fetchall()
    rows = [(o, y, d) for o, y, d, _ in allr]
    by_year = collections.Counter(y for _, y, _ in rows)
    inyrs = lambda y: any(g['y0'] <= y <= g['y1'] for g in D['gens'])
    parts = collections.Counter()   # what the complaints are about (NHTSA's component, first level), each complaint once per part
    for o, y, d, cp in allr:
        if inyrs(y): parts.update({x.split(':')[0].strip().capitalize() for x in (cp or '').split('|') if x.strip()})
    gens = {}
    for gd in D['gens']:
        rs = [(o, y, d or '') for o, y, d in rows if gd['y0'] <= y <= gd['y1']]
        iss = {}
        for i in D['engines'][gd['engine']]['issues']:
            if not i.get('rx'): continue
            hit = [o for o, y, d in rs if re.search(i['rx'], d, re.I)]
            iss[i['t']] = dict(n=len(hit), ex=hit[:2])
        gens[gd['id']] = dict(n=len(rs), issues=iss)
    return dict(by_year={str(y): by_year[y] for y in sorted(by_year)}, gens=gens, parts=[[k, v] for k, v in parts.most_common(6)])

def recalls(D):
    """NHTSA recalls per model year (each campaign once per year), cached"""
    cp = os.path.join(HERE, 'data', 'cache', f'perf_recalls_{D["slug"]}.json'); cache = _load(cp, {})
    out = {}
    for gd in D['gens']:
        for y in range(gd['y0'], gd['y1'] + 1):
            for m in D['nhtsa']['models'][:1]:
                k = f'{m}|{y}'
                if k not in cache:
                    u = f'https://api.nhtsa.gov/recalls/recallsByVehicle?make={D["nhtsa"]["make"]}&model={urllib.request.quote(m)}&modelYear={y}'
                    try: cache[k] = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'LemonIndex/1.0 (lemonindex.com)'}), timeout=20)).get('results', [])
                    except urllib.error.HTTPError as e:
                        if e.code != 400: print('recall fetch failed', k, e); continue
                        cache[k] = []   # NHTSA answers 400 for a model year it has no recall records for
                    except Exception as e: print('recall fetch failed', k, e); continue
                    time.sleep(.5)
                out[str(y)] = [dict(id=r.get('NHTSACampaignNumber'), part=r.get('Component', ''), summary=(r.get('Summary') or '')[:400]) for r in cache[k]]
    os.makedirs(os.path.dirname(cp), exist_ok=True); json.dump(cache, open(cp, 'w', encoding='utf-8'))
    return out

MAIN = r'C:\Users\elift\Code\lemonindex-site'   # the checkout the auto_gens workers write their scores into
def scores(D):
    """snapshot of the engine / trim study scores. auto_gens writes them to the MAIN checkout's data/supercar_engine_yt.json (committed only
    when its deploy runs), so a page built from any checkout still has them; perf_page.py lets the live file win."""
    live = {}
    for p in (os.path.join(HERE, 'data', 'supercar_engine_yt.json'), os.path.join(MAIN, 'data', 'supercar_engine_yt.json')):
        live.update(_load(p, {}) or {})
    return {i: live[i] for i in studies(D) if i in live}

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for slug in sys.argv[1:]:
        D = car(slug)
        A = dict(built=time.strftime('%Y-%m-%d'), nhtsa=nhtsa(D), recalls=recalls(D), yt=yt_all(D), scores=scores(D))
        json.dump(A, open(os.path.join(HERE, 'data', 'perf', f'{slug}.auto.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(slug, 'complaints', sum(A['nhtsa']['by_year'].values()), 'recall-years', len(A['recalls']), 'studies', {k: (v or {}).get('videos') for k, v in A['yt'].items()})
