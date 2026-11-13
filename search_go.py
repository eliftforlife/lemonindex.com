# 11-12 round 2 (fix B; Jake, Carlos, Liam: "civic vs corolla", "rav4 vs crv" and "elantra vs civic" gave two separate results and no compare):
# the site search turns "X vs Y" into "Compare X vs Y ->". Run by build.py with exec() right after docs/assets/compare.json is written
# (ux_c.py, UXC = 'data'), so it adds to find-go.json (find_index.py):
#   cmp: {page url: compare-tool id} for every car the compare tool has (any pair works: /compare/?cars=<id>-<year>,<id>)
#   cpg: {"<page url a> <page url b>": the prebuilt match-up page} (build.py's PAIRS + ux_c.py's performance pairs), used when no year is typed
_gp = f'{OUT}/assets/find-go.json'
_go = json.load(open(_gp, encoding='utf-8')) if os.path.exists(_gp) else {}
_go['cmp'] = {}
for _e in CMP: _go['cmp'].setdefault(_e['u'], _e['i'])
_go['cpg'] = {}
for _a, _b in PAIRS:
    if os.path.exists(f'{OUT}{CMPU(_a, _b)}index.html'): _go['cpg'][f'/cars/{_a}/ /cars/{_b}/'] = CMPU(_a, _b)
for _a, _b in (globals().get('PERF_PAIRS') or []):
    _ua = (_PD.get(_a) or {}).get('page'); _ub = (_PD.get(_b) or {}).get('page'); _pu = f'/compare/{_a}-vs-{_b}/'
    if _ua and _ub and os.path.exists(f'{OUT}{_pu}index.html'): _go['cpg'][f'{_ua} {_ub}'] = _pu
json.dump(_go, open(_gp, 'w', encoding='utf-8'), separators=(',', ':'))
print('search compare links:', len(_go['cmp']), 'cars,', len(_go['cpg']), 'match-up pages')
