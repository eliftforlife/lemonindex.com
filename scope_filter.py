# 11-12 round 2 (fix B; Ryan, Mitch, Carlos, Jake, Liam): keep each page to its own model, years and fuel. Run by build.py with exec() right
# after the extras load (XL, XA, X2), before any page or the battery banners (ux_c.py hooks) read them, so every count agrees everywhere.
#   - pickups (F-Series, Silverado, Sierra, Ram): recalls, investigations and dealer notes that NHTSA files only under the heavy-duty
#     2500/3500 (Super Duty) or the F-150 Lightning (its own EV page) leave the half-ton page (data/scope.json, data_scope.py). The year page
#     then counts the same recalls the VIN check shows, and says how many more the heavy-duty trucks have.
#   - "fuel or EV drive system" (NHTSA's FUEL/PROPULSION SYSTEM) reads "fuel system" on cars without an electric version
#   - "What to ask the shop" (repair_costs.py) and the dealer-note lists quote a bulletin only when it's about that system and that model
SCOPE = _load('data/scope.json')
_SC_OTHER = re.compile(r'\bSD\b|SUPER ?DUTY|\b[2-5][05]00\b|\bF-?[2-5][05]0\b|\bHD\b|LIGHTNING', re.I)
_SC_PICK = ('ford-f-series', 'chevrolet-silverado', 'gmc-sierra', 'ram-pickup')
_scn = lambda s: re.sub(r'[^A-Z0-9]', '', (s or '').upper())
def _sc_names(fid, y):
    e = XL.get(fid, {}).get(str(y)) or {}; tot = sum(n for *_, n in e.get('names', [])) or 1
    return [md for mk, md, n in e.get('names', []) if n / tot >= .05][:3]
def _sc_who(others):
    """'F-250/F-350 Super Duty', 'Silverado 2500/3500 HD', 'F-150 Lightning' from NHTSA model names"""
    out = []
    for md in others:
        u = md.upper()
        w = ('F-150 Lightning' if 'LIGHTNING' in u else 'F-250/F-350 Super Duty' if re.search(r'\bF-?[2-5][05]0\b|SD|SUPER', u) else
             'Silverado 2500/3500 HD' if 'SILVERADO' in u else 'Sierra 2500/3500 HD' if 'SIERRA' in u else 'Ram 2500/3500')
        if w not in out: out.append(w)
    return ' and '.join(out)
_sc_n = [0, 0, 0]
for _fid, _ys in (SCOPE.get('rec') or {}).items():
    for _y, _s in _ys.items():
        _d = XA.get(_fid, {}).get(_y)
        if not _d or 'recalls' not in _d: continue
        _o = set(_s['only']); _keep = [r for r in _d['recalls'] if r['id'] not in _o]; _gone = len(_d['recalls']) - len(_keep)
        _d['recalls'] = _keep; _sc_n[0] += _gone
        if _gone: _d['rec_other'] = {'n': _gone, 'who': _sc_who(_s['other'])}
_SCI = SCOPE.get('inv') or {}
for _fid in _SC_PICK:
    for _y, _d in (X2.get(_fid) or {}).items():
        own = {_scn(md) for md in _sc_names(_fid, _y) if not _SC_OTHER.search(md)}
        if _d.get('inv') and own:
            _k = [i for i in _d['inv'] if i['id'] not in _SCI or any(m in own and int(_y) in ys for m, ys in _SCI[i['id']].items())]
            _sc_n[1] += len(_d['inv']) - len(_k); _d['inv'] = _k
        _t = ((SCOPE.get('tsb') or {}).get(_fid) or {}).get(_y)
        if _d.get('tsb') and own: (_d.__setitem__('tsb', _t) if _t else _d.pop('tsb')); _sc_n[2] += 1
print(f'scope filter: {_sc_n[0]} heavy-duty/Lightning recalls, {_sc_n[1]} investigations off the half-ton pages; dealer notes recounted on {_sc_n[2]} pickup years')

# ---- "fuel or EV drive system" -> "fuel system" unless the car has an electric version that year (EPA), "electric drive system" on an EV
_EVSL = {c['slug'] for c in (_load('data/ev.json').get('cars') or [])}
def _sc_fuel(fid, y=None):
    if fid in _EVSL: return 'electric drive system'
    m = (XA.get(fid, {}).get(str(y)) or {}).get('mpg') if y else None
    return 'fuel or electric drive system' if (m and m.get('ev')) or (y is None and any(((d or {}).get('mpg') or {}).get('ev') for d in (XA.get(fid) or {}).values())) else 'fuel system'
_FEV = 'fuel or ev drive system'
for _f in YEARS:
    for _v in _f['years']:
        for _p in _v.get('parts') or []:
            if _p[0].lower() == _FEV: _p[0] = _sc_fuel(_f['id'], _v['y'])
for _fid, _ys in XL.items():
    for _y, _x in _ys.items():
        for _c in (_x or {}).get('comps') or []:
            if isinstance(_c[0], str) and _c[0].lower() == _FEV: _c[0] = _sc_fuel(_fid, _y)
for _c in CARS + CARS_NEW:
    for _p in _c.get('issues') or []:
        if isinstance(_p[0], str) and _p[0].lower() == _FEV: _p[0] = _sc_fuel(_c['id'])

# ---- dealer notes and shop tips: only bulletins about this model (another model named and not this one = out), never a boilerplate title
_SC_BRAND_MODELS = defaultdict(set)
for _c in CARS + CARS_NEW: _SC_BRAND_MODELS[_c['brand']].add(_c['name'].split(' ', 1)[1] if ' ' in _c['name'] else _c['name'])
def _sc_rx(names_, exact=False):
    # exact: another model counts only as written ("Fit", "FIT"), so the words "fit" or "pilot light" never knock a line out
    ns = {v for n in names_ if len(n) >= 2 for v in ((n, n.upper()) if exact else (n,))}
    alts = sorted({'[- ]?'.join(re.escape(w) for w in re.split(r'[- ]+', n) if w) for n in ns}, key=len, reverse=True)
    return re.compile(r'(?<![A-Za-z0-9])(' + '|'.join(alts) + r')(?![A-Za-z0-9])', 0 if exact else re.I) if alts else None
_SC_MRX = {}
for _c in CARS + CARS_NEW:
    mine = {_c['name'].split(' ', 1)[1] if ' ' in _c['name'] else _c['name']} | {md.title() for ys in [XL.get(_c['id'], {})] for e in ys.values() for _, md, _n in (e or {}).get('names', [])}
    if _c['id'] == 'ford-f-series': mine |= {'F-150', 'F150', 'F-Series'}
    others = {n for n in _SC_BRAND_MODELS[_c['brand']] if n.lower() not in {m.lower() for m in mine} and not any(n.lower() in m.lower() or m.lower() in n.lower() for m in mine)}
    _SC_MRX[_c['id']] = (_sc_rx(mine), _sc_rx(others, True))
_SC_HD = re.compile(r'super ?duty|f-super|\bf-?[2-5][05]0\b|\b[2-5]500\s?hd\b|\b[2-5]500\b|heavy[- ]duty|\bhd\b|medium duty|chassis cab|6\.7\s?l|6\.4\s?l|6\.0\s?l diesel|6\.6\s?l|cummins|duramax|power ?stroke|lightning', re.I)
def sc_line_ok(fid, line):
    """False when a quoted bulletin line is about another model (or, on a half-ton pickup, a heavy-duty / Lightning one)"""
    if fid in _SC_PICK and _SC_HD.search(line or ''): return False
    own_, oth = _SC_MRX.get(fid, (None, None))
    if oth and oth.search(line or '') and not (own_ and own_.search(line or '')): return False
    return True
RCQ.LINE_OK = sc_line_ok
