# 11-17: the engine YouTube scores and the ONE YouTube rank pool (ENG_POOL), split out of supercar_engine_pages.py so build.py can exec it
# BEFORE the first engine page is built. The heavy-duty diesel + 2.7 EcoBoost pages (hd_pages.py, built before supercar_engine_pages.py)
# showed "Average owner tone NN/100" with no "#N of M": ENG_POOL_RANK didn't exist yet when they were written.
# exec'd by build.py right before hd_pages.py's page phase, and again at the top of supercar_engine_pages.py (same data, same result).
# Coming-soon engines (11-17): data/engine_soon_yt.json (3 Lemon Index/data/yt/engine_studies_soon.py, scored from their cars' YouTube videos
# and their own pulls) joins the pool under 'soon:<card key>' (all_engines.py's _AE_KEY), so a coming-soon card can show its YT # too.
SCENG = _load('data/supercar_engines.json') if os.path.exists('data/supercar_engines.json') else {'engines': {}, 'cars': {}}
# YouTube scores: the workers write data/supercar_engine_yt.json in the main checkout (and commit it when they deploy); a snapshot of it is
# committed with each engine-page push so builds from other checkouts keep the ranks. The live file wins per engine.
SCY = dict(_load('data/supercar_engine_yt_snapshot.json') if os.path.exists('data/supercar_engine_yt_snapshot.json') else {})
SCY.update(_load('data/supercar_engine_yt.json') if os.path.exists('data/supercar_engine_yt.json') else {})
SCE_SLUG = {'rr-n73': 'rolls-royce-n73', 'rr-n74': 'rolls-royce-n74'}
SCE_URL = lambda e: f'/engines/{SCE_SLUG.get(e, e)}/'
SCE_HUB = '/engines/supercars/'
def _sce_yt(e):
    """{year: score} for the engine's own years, and the average (half-up, like the BMW pages)"""
    d = (SCY.get(e) or {}).get('years') or {}; yrs = SCENG['engines'][e]['years']
    s = {int(y): v['score'] for y, v in d.items() if y in yrs and v and v.get('score') is not None}
    return s, (int(sum(s.values()) / len(s) + 0.5) if s else None)
_SCAVG = {}
for _e in SCENG['engines']:
    _s, _a = _sce_yt(_e)
    if _s: _SCAVG[_e] = sum(_s.values()) / len(_s)
# 11-11: two groups share this code - supercar engines (/engines/supercars/) and performance-car engines (/engines/performance/);
# each engine's YouTube rank is among the engines of its own group
_GRP = lambda e: SCENG['engines'][e].get('group', 'super')
SCE_YTRANK = {}
for _g in ('super', 'perf'):
    SCE_YTRANK.update({e: i + 1 for i, e in enumerate(sorted([e for e in _SCAVG if _GRP(e) == _g], key=lambda e: (-_SCAVG[e], e)))})
SCE_NRANK = {g: sum(1 for e in SCE_YTRANK if _GRP(e) == g) for g in ('super', 'perf')}
GW = {'super': 'supercar engines', 'perf': 'performance engines'}
HUBS = {'super': '/engines/supercars/', 'perf': '/engines/performance/'}
SCE_N = len(SCENG['engines'])
# 11-12 round 2 (UX test, Devin: the B58 was "#1 of 13 BMW engines" while the Coyote was "#25 of 48 performance engines", and /engines/ showed
# "YT #1" twice): ONE YouTube ranking pool for every engine page on the site (BMW, performance, supercar), keyed by page URL, same average as
# each page shows (the engine's own model years). The BMW numbers use bmw_pages.py's rule (perf page engine study first, else the BMW attribution).
import perf_page as _PPX
ENG_POOL = {}   # url -> average YouTube tone
for _c in BENG:
    _yy = BEY.get(_c) or {}
    if not _yy: continue
    _x = _PPX.engine_ext(ENG_URL(_c)); _yd = (_x['years'] if _x and _x['years'] else None) or BYT.get(_c) or {}
    _v = [d['score'] for y, d in _yd.items() if y in _yy and d and d.get('score') is not None]
    if _v: ENG_POOL[ENG_URL(_c)] = sum(_v) / len(_v)
for _e, _a in _SCAVG.items():
    if _e not in {'bmw-s65'}: ENG_POOL.setdefault(SCE_URL(_e), _a)   # = SCE_EXTERNAL below: the BMW engine page owns that URL
for _u, _a in (globals().get('VE_YTAVG') or {}).items(): ENG_POOL.setdefault(_u, _a)   # 11-13: the everyday / diesel / EA888 engine studies (vin_engine_pages.py)
ENG_SOON_YT = _load('data/engine_soon_yt.json') if os.path.exists('data/engine_soon_yt.json') else {}
for _k, _r in ENG_SOON_YT.items():
    _v = [d['score'] for d in ((_r or {}).get('years') or {}).values() if d and d.get('score') is not None]
    if _v and _k.startswith('soon-'): ENG_POOL.setdefault('soon:' + _k[5:], sum(_v) / len(_v))
# 11-20 (Elijah: "fix the number"): /engines/ said "195 engines with their own page" while each page said "#21 of 409 engines": the 409 counted
# the coming-soon engines too, which have no page. The rank is now among the engine PAGES only; coming-soon cards show no YT #.
ENG_POOL_RANK = {u: i + 1 for i, u in enumerate(sorted((u for u in ENG_POOL if not u.startswith('soon:')), key=lambda u: (-ENG_POOL[u], u)))}
ENG_POOL_N = len(ENG_POOL_RANK)
ENG_POOL_LBL = 'engine pages with a YouTube study'
SCE_YTRANK = {e: ENG_POOL_RANK[SCE_URL(e)] for e in _SCAVG if SCE_URL(e) in ENG_POOL_RANK}
SCE_NRANK = {g: ENG_POOL_N for g in ('super', 'perf')}
GW = {'super': ENG_POOL_LBL, 'perf': ENG_POOL_LBL}
