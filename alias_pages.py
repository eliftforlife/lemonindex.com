# 11-13 navigation test (N1, problem 10: "/cars/ford-f-150/, /cars/ford-f150/, /cars/honda/ and reversed compare URLs are 404s"):
# small redirect pages at the addresses people type, each pointing to the real page (meta refresh 0 + canonical, noindex, not in the
# sitemap). GitHub Pages has no server redirects, so this is the standard static way. Anything not covered here still lands on the 404
# page, which turns the address into a search (assets/lx404.js). Run by build.py with exec() after find_index.py (needs FIND).
# Every stub starts with ALIAS_MARK, so find_index.py's guard and this file can tell a stub from a real page.
ALIAS_MARK = '<!doctype html><!--lx-alias-->'
def _is_real(u):
    p_ = f'{OUT}{u}index.html'
    if not os.path.exists(p_): return False
    with open(p_, encoding='utf-8', errors='replace') as fh: return not fh.read(len(ALIAS_MARK)).startswith(ALIAS_MARK)
_ALIAS = {}   # alias path -> real path
def _al(a, tgt):
    a = '/' + a.strip('/') + '/'
    if a == tgt or a in _ALIAS or _is_real(a) or not _is_real(tgt): return
    _ALIAS[a] = tgt
_cars = {r[2]: r for r in FIND if r[2].startswith('/cars/') and r[3] in ('', 'co') and r[2].count('/') == 3}
_bslug = {u.split('/')[2] for u in (f'/brands/{x}/' for x in os.listdir(f'{OUT}/brands') if os.path.isdir(f'{OUT}/brands/{x}')) if _is_real(u)}
_BRAND_AKA = {'chevrolet': ['chevy'], 'volkswagen': ['vw'], 'mercedes-benz': ['mercedes'], 'land-rover': ['landrover']}
# 1. a brand typed under /cars/ (/cars/honda/) or by its nickname (/brands/chevy/) -> the brand page
for b in _bslug:
    for nick in [b] + _BRAND_AKA.get(b, []):
        _al(f'/cars/{nick}/', f'/brands/{b}/')
        if nick != b: _al(f'/brands/{nick}/', f'/brands/{b}/')
# 2. model nicknames: brand nicknames (/cars/chevy-tahoe/) and short codes typed joined up (/cars/honda-crv/, /cars/mazda-cx5/)
for u in _cars:
    fid = u.split('/')[2]
    for b, nicks in _BRAND_AKA.items():
        if fid.startswith(b + '-'):
            for nick in nicks: _al(f'/cars/{nick}-{fid[len(b) + 1:]}/', u)
    bs = re.sub(r'[^a-z0-9]+', '-', _cars[u][1].lower()).strip('-')
    if not fid.startswith(bs + '-') or '/' in fid: continue
    seg = fid[len(bs) + 1:].split('-'); j = []   # the model part only ('cr-v' -> 'crv'; never 'bmw-3' -> 'bmw3')
    for s_ in seg:
        if j and len(j[-1]) <= 3 and len(s_) <= 2 and j[-1].isalnum() and s_.isalnum(): j[-1] += s_
        else: j.append(s_)
    if len(j) < len(seg): _al(f'/cars/{bs}-{"-".join(j)}/', u)
# 3. the trucks people type by their half-ton number (the most-visited pages), with every year
_TRUCK = {'ford-f-series': ['ford-f-150', 'ford-f150', 'f-150', 'f150', 'ford-f-150-pickup'], 'ram-pickup': ['ram-1500', 'dodge-ram-1500', 'dodge-ram'],
          'chevrolet-silverado': ['chevrolet-silverado-1500', 'chevy-silverado-1500'], 'gmc-sierra': ['gmc-sierra-1500']}
for fid, nicks in _TRUCK.items():
    r = _cars.get(f'/cars/{fid}/')
    if not r: continue
    for nick in nicks:
        _al(f'/cars/{nick}/', f'/cars/{fid}/')
        for y in r[4]: _al(f'/cars/{nick}/{y}/', f'/cars/{fid}/{y}/')
# 4. match-ups typed the other way round (/compare/toyota-corolla-vs-honda-civic/)
for d in os.listdir(f'{OUT}/compare'):
    m_ = re.fullmatch(r'(.+?)-vs-(.+)', d)
    if m_ and _is_real(f'/compare/{d}/'): _al(f'/compare/{m_.group(2)}-vs-{m_.group(1)}/', f'/compare/{d}/')
for a, tgt in _ALIAS.items():
    os.makedirs(f'{OUT}{a}', exist_ok=True)
    with open(f'{OUT}{a}index.html', 'w', encoding='utf-8') as fh:
        fh.write(f'{ALIAS_MARK}<html lang="en"><head><meta charset="utf-8"><title>Moved | The Lemon Index</title><meta name="robots" content="noindex">'
                 f'<link rel="canonical" href="{BASE}{tgt}"><meta http-equiv="refresh" content="0; url={tgt}"><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
                 f'<body style="font-family:system-ui,sans-serif;padding:24px"><p>This page is at <a href="{tgt}">lemonindex.com{tgt}</a>.</p></body></html>')
print('alias redirect pages:', len(_ALIAS), '| e.g.', list(_ALIAS.items())[:4])
