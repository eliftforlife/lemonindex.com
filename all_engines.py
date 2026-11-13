# 11-12 (Elijah: "make an engine page that says all engines, you can search, and it has the different selectors like the All cars page, then add
# 1 engine per car model and mark them as coming soon"): /engines/ = every engine on the site in one searchable grid, with tabs like /cars/.
# exec'd by build.py after the engine hubs (supercar_engine_pages.py, bmw_pages.py) and perf_page, before find_index.py.
#   Live cards: the BMW engine pages (bmw_pages.py STATS), the supercar + performance engine pages (SCENG), the Civic's engines (data/engines_<model>.json).
#   Coming soon: one engine per car model that has no engine page yet = the EPA engine (data/extras_*: "2.5L 4-cyl") on the most model years,
#   or the performance list's own engine line (data/perf_cars.json). No codes are added: EPA only gives size + cylinders, and we never guess.
#   Engines shared by models of one brand become one card. Coming-soon cards are not links and have no pages of their own.
# assets/engines.js filters the cards (tabs set ?type=, the search box matches name, code, layout and the cars). AE_FIND feeds find_index.py.
import glob as _aeg
AE_URLS, AE_FIND = [], []
_AEF = lambda t: re.sub(r'[^a-z0-9.]+', ' ', html.unescape(str(t)).lower()).replace(' .', ' ').strip()
def _ae_img(ph):
    if not ph: return None
    th = ph['src'][:-5] + '-640.webp'
    return (th, 640, round(ph['h'] * 640 / ph['w'])) if ph['src'].endswith('.webp') and os.path.exists(th.lstrip('/')) else (ph['src'], ph['w'], ph['h'])
AE_LIVE = {}   # url -> card dict (a page listed by two hubs, e.g. the S62 on the BMW and performance hubs, is one card with both tags)
def _ae_add(url, **c):
    if not os.path.exists(os.path.join(OUT, url.split('#')[0].strip('/'), 'index.html')): return
    if url in AE_LIVE: AE_LIVE[url]['t'] |= c['t']; return
    AE_LIVE[url] = dict(url=url, **c)
# 1. BMW engine pages (ranked the same way as /engines/bmw/)
_ae_ytn = ENG_POOL_N   # 11-12 round 2: one YouTube rank pool for every engine (supercar_engine_pages.py), so no two cards say YT #1
for s in (globals().get('STATS') or []):
    code = s['code']; m = BENG[code]; asp = m.get('asp') or ''
    tur = 'twin-turbo' if 'twin-turbo' in asp else 'turbo' if 'turbo' in asp else ''
    _ae_add(ENG_URL(code), name=f'BMW {code}', code=code, lay=' '.join(x for x in (m['size'], m['layout'], tur) if x), yrs=s['years'], img=_ae_img(BPH.get(code)),
            yt=(_YTRANK.get(code), _ae_ytn, ENG_POOL_LBL), used=[BFAM.get(f, f).replace('BMW ', '') for f in s['fams']], t={'b'}, f='gas', mk='BMW', o=(0, _YTRANK.get(code, 999)))
# 2. supercar + performance engine pages
for e, d in SCENG['engines'].items():
    g = _GRP(e); tg = {'s' if g == 'super' else 'p'} | ({'b'} if d['make'] == 'BMW' else set()) | ({'h'} if d['make'] in ('Honda', 'Acura') else set())
    yrs = f'{d["y0"]}–{str(d["y1"])[-2:]}' if d.get('y1') and d['y1'] != d['y0'] else str(d.get('y0', ''))
    _ae_add(SCE_URL(e), name=d['name'], code=d.get('code', ''), lay=f'{d["size"]} {d["layout"]}, {d["asp"]}', yrs=yrs, img=_ae_img(SCP.get(e)),
            yt=(SCE_YTRANK.get(e), SCE_NRANK.get(g, 0), GW[g]), used=[_sce_label(d, c['slug']).replace(d['make'] + ' ', '') for c in d['cars']], t=tg, f='hybrid' if 'hybrid' in (d['asp'] + d['layout'] + d['name']).lower() else 'gas', mk=d['make'],
            o=(1 if g == 'super' else 2, SCE_YTRANK.get(e, 999)))
# 2b. engine pages built from the performance files only (engine_more.py: the EA888 from the Golf R file)
for c in globals().get('ENG_EXTRA_CARDS') or []:
    _ae_add(c['url'], name=c['name'], code=c['code'], lay=c['lay'], yrs=c['yrs'], img=None, yt=(ENG_POOL_RANK.get(c['url']), ENG_POOL_N, ENG_POOL_LBL), used=c['used'], t={'p'}, f='gas', mk=c['mk'], o=(2, 999))
# 3. per-model engine lists (the Civic's, so far): each opens that model page's Engines view
_AE_MODEL_ENG = set()
for _p in sorted(_aeg.glob('data/engines_*.json')):
    fid = os.path.basename(_p)[8:-5]; fam = next((f for f in YEARS if f['id'] == fid), None)
    if not fam: continue
    _AE_MODEL_ENG.add(fid); mk = BYNAME[fam['name']]['brand']; short = _short(fam['name'], mk)
    for d in json.load(open(_p, encoding='utf-8')):
        ys = d.get('years') or []
        _ae_add(f'/cars/{fid}/#eng-{d["id"]}', name=f'{mk} {d["code"]}', code=d['code'], lay=d['size'], yrs=(f'{ys[0]}–{str(ys[-1])[-2:]}' if len(ys) > 1 else str(ys[0]) if ys else ''),
                img=_ae_img(d.get('img')), yt=(None, 0, ''), used=[short], t={'h'} if mk in ('Honda', 'Acura') else set(), f='hybrid' if re.search(r'hybrid|IMA', d.get('name', '') + ' ' + d.get('note', ''), re.I) else 'gas', mk=mk, o=(3, ys[0] if ys else 0), alias=d.get('name', ''))
# 4. 11-12 round 2: heavy-duty diesel + F-150 engine pages and the two comparisons (hd_pages.py), tab 'Trucks & diesel'
for _c in (globals().get('HD_AE') or []): _ae_add(**_c)
# 11-13 N3 (nav report 3: "list mainstream cars first in Used in"): the everyday /cars/ models from ENGINE_USES lead each card's list, so the
# 3.5 EcoBoost card says F-150 before GT and searching "camry" finds the 2GR-FE
for _u, _c in AE_LIVE.items():
    _new, _front = [], []
    for _fid, _nm, _ys, _vs in (globals().get('EU_CARS') or (lambda u: []))(_u.split('#')[0]):
        _lab = 'F-150' if _fid == 'ford-f-series' else _short(_nm, BYNAME[_nm]['brand'] if _nm in BYNAME else _nm.split(' ')[0])
        _hit = [x for x in _c['used'] if _lab.lower() in x.lower()]
        if _hit: _front += [x for x in _hit if x not in _front]
        elif _lab not in _new: _new.append(_lab)
    _c['used'] = _new + _front + [x for x in _c['used'] if x not in _front]
# ---- coming soon: one engine per model and fuel (11-12, Elijah: "one engine per fuel type it was actually sold with in the US")
# data/engine_fuels.json (data_engine_fuels.py: EPA records with their fuel type) where we have it, else the EPA engine list in the model-year data (gas).
# A model whose engines already have pages (BMW, supercar/performance hubs) skips only its gas engine; a model with its own engine list (Civic) skips all.
_ae_cov = {f for s in (globals().get('STATS') or []) for f in s['fams']} | set(((BS.get('versions') or {}) if 'BS' in globals() else {}).keys())
for k, v in SCENG['cars'].items(): _ae_cov.add(k.split(':', 1)[-1])
if globals().get('HD_AE'): _ae_cov.add('ford-f-series')   # 11-12 round 2: the F-150's engines have pages now (2.7, 3.5, 5.0)
for d in SCENG['engines'].values():
    for c in d['cars']: _ae_cov |= {c['slug']} | ({c['perf']} if c.get('perf') else set())
_ae_ev = {c['slug'] for c in EVX}
AE_FUEL = _load('data/engine_fuels.json')
AE_FL = {'gas': 'Gas', 'diesel': 'Diesel', 'hybrid': 'Hybrid', 'phev': 'Plug-in hybrid', 'electric': 'Electric'}
_FG = lambda f: 'hybrid' if f == 'phev' else f   # the selector's four groups: gas, diesel, hybrid (incl. plug-in), electric
_FSUF = {'gas': '', 'diesel': ' diesel', 'hybrid': ' hybrid', 'phev': ' plug-in hybrid', 'electric': ''}
def _ae_desc(t): return re.sub(r'(\d+)-cyl$', r'\1-cylinder', t.strip())
def _ae_fuels(fid, years=None):
    """[(engine text, fuel)]: per fuel group, the EPA engine on the most model years (ties: the newer one)"""
    ys = {str(y) for y in years} if years else None; cnt, last = {}, {}
    def add(k, y): cnt[k] = cnt.get(k, 0) + 1; last[k] = max(last.get(k, 0), int(y))
    if AE_FUEL.get(fid):
        for y, rs in AE_FUEL[fid].items():
            if ys and y not in ys: continue
            for eng, fu, mot in rs: add((_FG(fu), fu, 'electric motor' + (', ' + mot if mot else '') if fu == 'electric' else _ae_desc(eng) + _FSUF[fu]), y)
    else:
        for y in (years or ()):
            m = extra(fid, y).get('mpg') or {}
            if m.get('ev'): continue
            for t in m.get('engines') or []:
                if t != 'electric': add(('gas', 'gas', _ae_desc(t)), y)
    best = {}
    for k in cnt:
        if k[0] not in best or (cnt[k], last[k]) > (cnt[best[k[0]]], last[best[k[0]]]): best[k[0]] = k
    return [(k[2], k[1]) for k in best.values()]
_ae_models = []   # (model id, name, brand, engine text, fuel)
_ae_seen = set()
def _ae_model(fid, nm, mk, engs):
    if fid in _AE_MODEL_ENG: return
    mk = {'Ssc': 'SSC'}.get(mk, mk)
    for eng, fu in engs:
        if not eng or (fid, _FG(fu)) in _ae_seen or (fu == 'gas' and fid in _ae_cov): continue
        _ae_seen.add((fid, _FG(fu))); _ae_models.append((fid, nm, mk, eng, fu))
for f in YEARS: _ae_model(f['id'], f['name'], BYNAME[f['name']]['brand'], _ae_fuels(f['id'], [v['y'] for v in f['years']]))
for m in list(_load('data/extra_models.json').values()) + list(_load('data/extra_models_new.json').values()):
    _ae_model(m['id'], m['name'], m.get('brand') or m['name'].split(' ')[0], _ae_fuels(m['id'], range(int(m['a']), int(m['b']) + 1) if m.get('a') else None))
for fid, m in ((BS.get('new_models') or {}) if 'BS' in globals() else {}).items():
    _ae_model(fid, m['name'], 'BMW', _ae_fuels(fid, range(int(m['a']), int(m['b']) + 1) if m.get('a') else None))
for m in NEWM:
    if m['slug'] not in _DUP: _ae_model(m['slug'], m['name'], m['make'], _ae_fuels(m['slug'], range(2000, 2027)))
for c in EVX: _ae_model(c['slug'], c['name'], _brandof(c['make']), _ae_fuels(c['slug']) or [('electric motor', 'electric')])
for c in SCX:
    cnt = {}
    for y in c['years']:
        for t in y.get('engines') or []: cnt[t] = cnt.get(t, 0) + 1
    _ae_model(_slg(c['name']), c['name'], _brandof(c['make']), [(_ae_desc(max(cnt, key=lambda t: (cnt[t], t))), 'gas')] if cnt else [])
# performance cars: covered when their data/perf/<slug>.json engine has a page (or its code is already a live card, e.g. the Type R's K20C1 on
# the Civic list); otherwise the perf list's engine line, plus the newest engine name from that file when it has one (codes from our data only)
_ae_codes = {x.strip().upper() for c in AE_LIVE.values() for x in re.split(r'[/,]', c['code']) if x.strip()}
for c in PERFX:
    i = perf_info(c); eng = c.get('engine'); pe = ((_jl(f'data/perf/{i["id"]}.json') or {}).get('engines') or {})
    if any(v.get('page') for v in pe.values()) or any(k.upper() in _ae_codes for k in pe): _ae_cov.add(i['id']); continue
    if not eng: continue
    fu = 'hybrid' if 'hybrid' in eng.lower() else 'electric' if 'electric' in eng.lower() else 'gas'
    if pe:
        nm = re.sub(r'\s*\(.*?\)', '', list(pe.values())[-1].get('name', '')).strip()
        nm = nm[len(nm.split(' ')[0]) + 1:] if nm.split(' ')[0] in (i['brand'], 'VW', 'Ford', 'Honda') else nm
        if nm: eng = f'{eng} ({nm})'
    _ae_model(i['id'], i['name'], i['brand'], [(eng, fu)])
# electric: one card per brand ("Tesla electric motors"), since EPA names motors by power, not by a design we could tell apart; a regular model's
# electric version drops out when the EV list names it (Mustang -> Mustang Mach-E)
AE_SOON = {}
for fid, nm, mk, eng, fu in _ae_models:
    sh = _short(nm, mk); sh = nm if sh[:1].islower() else sh   # "Ram pickup", not "pickup"
    if fu == 'electric': eng = 'electric motors'
    v = AE_SOON.setdefault((mk, eng), {'models': [], 'fuel': fu})
    if sh not in v['models']: v['models'].append(sh)
for v in AE_SOON.values():
    if v['fuel'] == 'electric': v['models'] = [m for m in v['models'] if not any(o != m and o.startswith(m + ' ') for o in v['models'])]
# ---- the page
_AE_IC = ('<svg viewBox="0 0 64 40" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
          '<path d="M14 12h30l6 6h6v-4h4v16h-4v-4h-6l-5 6H20l-4-4h-6v4H6V14h4v4h4z"/><path d="M24 12V7h12v5M20 7h20"/></svg>')
_AE_YT = '<svg aria-hidden="true" viewBox="0 0 24 24" width="11" height="11"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>'
_ae_ftag = lambda fu: f'<span class="aec-f aec-f-{_FG(fu)}">{AE_FL[fu]}</span>'
def _ae_used(u, n=4): return 'Used in: ' + ', '.join(u[:n]) + (f' +{len(u) - n} more' if len(u) > n else '')
def _ae_card(c, eager=False):
    k = _AEF(' '.join([c['name'], c['code'], c.get('alias', ''), c['lay'], c['mk'], AE_FL[c['f']]] + c['used']))
    im = (f'<span class="aec-p"><img src="{E(c["img"][0])}" width="{c["img"][1]}" height="{c["img"][2]}" alt="{E(c["name"])} engine" '
          + ('fetchpriority="high" decoding="async">' if eager else 'loading="lazy" decoding="async">') + '</span>') if c['img'] else f'<span class="aec-p aec-ic">{_AE_IC}</span>'
    rk, n, grp = c['yt']
    yt = f'<span class="ytbadge aec-yt" title="YouTube rank by owner tone, of {n} {E(grp)} with enough videos">{_AE_YT}YT #{rk}</span>' if rk else ''
    im = im.replace('</span>', _ae_ftag(c['f']) + '</span>', 1) if c['img'] else im.replace('</svg></span>', '</svg>' + _ae_ftag(c['f']) + '</span>', 1)
    return (f'<a class="aec" data-t="{" ".join(sorted(c["t"]))}" data-f="{_FG(c["f"])}" data-k="{E(k)}" data-yr="{E(c["yrs"])}" href="{E(c["url"])}">{im}{yt}<b>{E(c["name"])}</b>'
            f'<small class="aec-l">{E(c["lay"])}{" · " + E(c["yrs"]) if c["yrs"] else ""}</small><small class="aec-u">{E(_ae_used(c["used"]))}</small></a>')
# 11-12: AI factory-cover illustrations for the coming-soon engines (data/engine_soon_images.json, key = brand + engine without "(...)")
AE_SOON_IMG = _load('data/engine_soon_images.json')
_AE_KEY = lambda mk, eng: re.sub(r'[^a-z0-9]+', '-', f'{mk} {re.sub(r"\s*\(.*?\)", "", eng)}'.lower()).strip('-')
_AE_AI = ('Illustration (AI-generated) in the style of a factory press photo, not a photo of a specific engine; brand names and logos belong to their owners. '
          'Free to use under <a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener license">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>')
def _ae_soon(mk, eng, models, fu):
    k = _AEF(' '.join([mk, eng, AE_FL[fu]] + models)); ph = AE_SOON_IMG.get(_AE_KEY(mk, eng)); im = _ae_img(ph)
    pic = (f'<span class="aec-p"><img src="{E(im[0])}" width="{im[1]}" height="{im[2]}" alt="{E(mk)} {E(eng)} engine (illustration)" loading="lazy" decoding="async">{YSL.info(_AE_AI)}{_ae_ftag(fu)}</span>'
           if im else f'<span class="aec-p aec-ic">{_AE_IC}{_ae_ftag(fu)}</span>')
    return (f'<div class="aec aec-soon" data-t="c" data-f="{_FG(fu)}" data-k="{E(k)}" aria-disabled="true" title="Coming soon">{pic}'
            f'<span class="aec-b">Coming soon</span><b>{E(mk)} {E(eng)}</b><small class="aec-u">{E(_ae_used(models))}</small></div>')
_ae_live = sorted(AE_LIVE.values(), key=lambda c: (c['o'], c['name']))
_ae_soonl = sorted(AE_SOON.items(), key=lambda kv: (kv[0][0], ('gas', 'diesel', 'hybrid', 'phev', 'electric').index(kv[1]['fuel']), kv[0][1]))
_aeN, _aeS = len(_ae_live), len(_ae_soonl)
_ae_n = lambda t: sum(t in c['t'] for c in _ae_live)
AE_TABS = [('all', 'All', ''), ('trucks', 'Trucks & diesel', _ae_n('t')), ('bmw', 'BMW', _ae_n('b')), ('supercars', 'Supercars', _ae_n('s')), ('performance', 'Performance', _ae_n('p')),
           ('honda', 'Honda', _ae_n('h')), ('soon', 'Coming soon', _aeS)]
_ae_tabs = ('<nav class="ctabs aetabs" aria-label="Kinds of engine">' + ''.join(
    f'<a href="/engines/{"?type=" + k if k != "all" else ""}" data-type="{k}"{" aria-current=true" if k == "all" else ""}>{t}{f" <small>{n}</small>" if n else ""}</a>'
    for k, t, n in AE_TABS if k in ('all', 'soon') or n) + '</nav>')
_ae_fn = lambda g: sum(_FG(c['f']) == g for c in _ae_live) + sum(_FG(v['fuel']) == g for v in AE_SOON.values())
_ae_fuel = ('<div class="aefuel" role="group" aria-label="Fuel">' + ''.join(
    f'<a href="/engines/{"?fuel=" + g if g != "all" else ""}" data-fuel="{g}"{" aria-current=true" if g == "all" else ""}>{t}{f" <small>{_ae_fn(g)}</small>" if g != "all" else ""}</a>'
    for g, t in (('all', 'Any fuel'), ('gas', 'Gas'), ('diesel', 'Diesel'), ('hybrid', 'Hybrid'), ('electric', 'Electric')) if g == 'all' or _ae_fn(g)) + '</div>')
_ae_body = f'''<div class="pg"><div class="ph ph-f"><section class="finder aefind" aria-labelledby="fh"><h1 id="fh"><span class="ph-e">Engines</span>Every engine.</h1>
<p class="lede">{_aeN} engines with their own page, from the BMW B58 to the Ferrari F154: owner complaints, recalls and a YouTube owner score by model year. Coming soon: one engine for every other model we cover, per fuel it was sold with (gas, diesel, hybrid, electric).</p>
<div class="fq"><input id="aeq" type="search" placeholder="e.g. LS3, B58, 2JZ, Honda K20" autocomplete="off" aria-label="Search engines" aria-controls="aegrid"></div>
<p class="fnote" id="aen" aria-live="polite"><b>{_aeN}</b> engines · <b>{_aeS}</b> coming soon</p></section></div>
<section class="aeng" id="aegrid">{_ae_tabs}{_ae_fuel}
<section class="aes" data-s="live"><h2>Engine pages <span class="h2s">YouTube rank in the corner, where owners have posted enough videos.</span></h2><div class="aeg">{"".join(_ae_card(c, i == 0) for i, c in enumerate(_ae_live))}</div></section>
<section class="aes" data-s="soon" data-nosnippet><h2>Coming soon <span class="h2s">One engine per model and fuel: the one EPA lists on the most model years. Pages are on the way.</span></h2><div class="aeg">{"".join(_ae_soon(mk, eng, v['models'], v['fuel']) for (mk, eng), v in _ae_soonl)}</div></section>
<p class="aenone" hidden>No engine matches that yet. Try a code like B58 or a model like Camry.</p>
<p class="note aehubs">Engine head-to-head: {" · ".join(f'<a href="{u}">{lab.replace(", ", " vs ").replace(" and ", " vs ")}</a>' for u, us, lab in ENG_H2H)}. YT # = YouTube rank among all {ENG_POOL_N} {ENG_POOL_LBL}.</p>
<p class="note aehubs">Engine hubs: <a href="/engines/bmw/">BMW engines</a> · <a href="/engines/supercars/">Supercar engines</a> · <a href="/engines/performance/">Performance engines</a> · <a href="/check-engine-light/">Check engine light codes</a> (OBD-II trouble codes, a different lookup)</p>
<p class="ph-cr">Engine images: AI-generated illustrations by The Lemon Index, free under CC BY 4.0 (<a href="/images/">download</a>), except the BMW S55 and S58 photos (Wikimedia Commons, credited on their pages). Engine sizes and cylinders: EPA (fueleconomy.gov).</p></section></div><script src="/assets/engines.js?v=6" defer></script><script src="/assets/soonvote.js?v=2" defer></script>'''
page('/engines/', 'Every Car Engine: Reliability, Problems & YouTube Owner Ranks',
     f'Search {_aeN} car engines, from the BMW B58 and N54 to the GM LS3 and Ferrari F154: owner complaints, recalls and YouTube owner ranks by model year. {_aeS} more coming soon.',
     _ae_body, ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Every car engine", "url": BASE + '/engines/',
                    "hasPart": [{"@type": "WebPage", "name": c['name'], "url": BASE + c['url']} for c in _ae_live if '#' not in c['url']]}])
AE_URLS.append('/engines/')
# search index rows: [name, brand, url, kind, years, aliases, soon]
for c in _ae_live: AE_FIND.append((c['name'] + ' engine', c['mk'], c['url'], 'eng', (), ' '.join([c['code'], c.get('alias', ''), 'engine', AE_FL[c['f']].lower()] + c['used']), 0))
for (mk, eng), v in _ae_soonl:
    ms = v['models']; AE_FIND.append((f'{mk} {eng} engine ({", ".join(ms[:3])}{"…" if len(ms) > 3 else ""})', mk, '', 'eng', (), ' '.join(ms + ['engine', AE_FL[v['fuel']].lower()]), 1))
print('all engines page:', _aeN, 'live,', _aeS, 'coming soon,', len({m[0] for m in _ae_models}), 'models | soon by fuel:', {g: sum(_FG(v['fuel']) == g for v in AE_SOON.values()) for g in ('gas', 'diesel', 'hybrid', 'electric')})
