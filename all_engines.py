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
_ae_ytn = len(globals().get('_YTRANK') or {})
for s in (globals().get('STATS') or []):
    code = s['code']; m = BENG[code]; asp = m.get('asp') or ''
    tur = 'twin-turbo' if 'twin-turbo' in asp else 'turbo' if 'turbo' in asp else ''
    _ae_add(ENG_URL(code), name=f'BMW {code}', code=code, lay=' '.join(x for x in (m['size'], m['layout'], tur) if x), yrs=s['years'], img=_ae_img(BPH.get(code)),
            yt=(_YTRANK.get(code), _ae_ytn, 'BMW engines'), used=[BFAM.get(f, f).replace('BMW ', '') for f in s['fams']], t={'b'}, mk='BMW', o=(0, _YTRANK.get(code, 999)))
# 2. supercar + performance engine pages
for e, d in SCENG['engines'].items():
    g = _GRP(e); tg = {'s' if g == 'super' else 'p'} | ({'b'} if d['make'] == 'BMW' else set()) | ({'h'} if d['make'] in ('Honda', 'Acura') else set())
    yrs = f'{d["y0"]}–{str(d["y1"])[-2:]}' if d.get('y1') and d['y1'] != d['y0'] else str(d.get('y0', ''))
    _ae_add(SCE_URL(e), name=d['name'], code=d.get('code', ''), lay=f'{d["size"]} {d["layout"]}, {d["asp"]}', yrs=yrs, img=_ae_img(SCP.get(e)),
            yt=(SCE_YTRANK.get(e), SCE_NRANK.get(g, 0), GW[g]), used=[_sce_label(d, c['slug']).replace(d['make'] + ' ', '') for c in d['cars']], t=tg, mk=d['make'],
            o=(1 if g == 'super' else 2, SCE_YTRANK.get(e, 999)))
# 3. per-model engine lists (the Civic's, so far): each opens that model page's Engines view
_AE_MODEL_ENG = set()
for _p in sorted(_aeg.glob('data/engines_*.json')):
    fid = os.path.basename(_p)[8:-5]; fam = next((f for f in YEARS if f['id'] == fid), None)
    if not fam: continue
    _AE_MODEL_ENG.add(fid); mk = BYNAME[fam['name']]['brand']; short = _short(fam['name'], mk)
    for d in json.load(open(_p, encoding='utf-8')):
        ys = d.get('years') or []
        _ae_add(f'/cars/{fid}/#eng-{d["id"]}', name=f'{mk} {d["code"]}', code=d['code'], lay=d['size'], yrs=(f'{ys[0]}–{str(ys[-1])[-2:]}' if len(ys) > 1 else str(ys[0]) if ys else ''),
                img=_ae_img(d.get('img')), yt=(None, 0, ''), used=[short], t={'h'} if mk in ('Honda', 'Acura') else set(), mk=mk, o=(3, ys[0] if ys else 0), alias=d.get('name', ''))
# ---- coming soon: models with no engine page yet
_ae_cov = set(_AE_MODEL_ENG) | {f for s in (globals().get('STATS') or []) for f in s['fams']} | set(((BS.get('versions') or {}) if 'BS' in globals() else {}).keys())
for k, v in SCENG['cars'].items(): _ae_cov.add(k.split(':', 1)[-1])
for d in SCENG['engines'].values():
    for c in d['cars']: _ae_cov |= {c['slug']} | ({c['perf']} if c.get('perf') else set())
_ae_ev = {c['slug'] for c in EVX}
def _ae_desc(t): return re.sub(r'(\d+)-cyl$', r'\1-cylinder', t.strip())
def _ae_epa(fid, years):
    """the EPA engine on the most model years (ties: the newer one)"""
    cnt, last = {}, {}
    for y in years:
        m = extra(fid, y).get('mpg') or {}
        if m.get('ev'): continue
        for t in m.get('engines') or []:
            cnt[t] = cnt.get(t, 0) + 1; last[t] = max(last.get(t, 0), int(y))
    return max(cnt, key=lambda t: (cnt[t], last[t])) if cnt else None
_ae_models = []   # (model id, name, brand, engine)
_ae_seen = set()
def _ae_model(fid, nm, mk, eng):
    if not eng or fid in _ae_seen or fid in _ae_cov or fid in _ae_ev or 'electric' in eng.lower(): return
    _ae_seen.add(fid); _ae_models.append((fid, nm, mk, _ae_desc(eng)))
for f in YEARS: _ae_model(f['id'], f['name'], BYNAME[f['name']]['brand'], _ae_epa(f['id'], [v['y'] for v in f['years']]))
for m in list(_load('data/extra_models.json').values()) + list(_load('data/extra_models_new.json').values()):
    _ae_model(m['id'], m['name'], m.get('brand') or m['name'].split(' ')[0], _ae_epa(m['id'], range(int(m['a']), int(m['b']) + 1)) if m.get('a') else None)
for fid, m in ((BS.get('new_models') or {}) if 'BS' in globals() else {}).items():
    _ae_model(fid, m['name'], 'BMW', _ae_epa(fid, range(int(m['a']), int(m['b']) + 1)) if m.get('a') else None)
for m in NEWM:
    if m['slug'] not in _DUP: _ae_model(m['slug'], m['name'], m['make'], _ae_epa(m['slug'], range(2000, 2026)))
for c in SCX:
    cnt = {}
    for y in c['years']:
        for t in y.get('engines') or []: cnt[t] = cnt.get(t, 0) + 1
    _ae_model(_slg(c['name']), c['name'], _brandof(c['make']), max(cnt, key=lambda t: (cnt[t], t)) if cnt else None)
for c in PERFX:
    i = perf_info(c); _ae_model(i['id'], i['name'], i['brand'], c.get('engine'))
AE_SOON = {}
for fid, nm, mk, eng in _ae_models: AE_SOON.setdefault((mk, eng), []).append(_short(nm, mk))
# ---- the page
_AE_IC = ('<svg viewBox="0 0 64 40" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
          '<path d="M14 12h30l6 6h6v-4h4v16h-4v-4h-6l-5 6H20l-4-4h-6v4H6V14h4v4h4z"/><path d="M24 12V7h12v5M20 7h20"/></svg>')
_AE_YT = '<svg aria-hidden="true" viewBox="0 0 24 24" width="11" height="11"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>'
def _ae_used(u, n=4): return 'Used in: ' + ', '.join(u[:n]) + (f' +{len(u) - n} more' if len(u) > n else '')
def _ae_card(c, eager=False):
    k = _AEF(' '.join([c['name'], c['code'], c.get('alias', ''), c['lay'], c['mk']] + c['used']))
    im = (f'<span class="aec-p"><img src="{E(c["img"][0])}" width="{c["img"][1]}" height="{c["img"][2]}" alt="{E(c["name"])} engine" '
          + ('fetchpriority="high" decoding="async">' if eager else 'loading="lazy" decoding="async">') + '</span>') if c['img'] else f'<span class="aec-p aec-ic">{_AE_IC}</span>'
    rk, n, grp = c['yt']
    yt = f'<span class="ytbadge aec-yt" title="YouTube rank by owner tone, of {n} {E(grp)} with enough videos">{_AE_YT}YT #{rk}</span>' if rk else ''
    return (f'<a class="aec" data-t="{" ".join(sorted(c["t"]))}" data-k="{E(k)}" href="{E(c["url"])}">{im}{yt}<b>{E(c["name"])}</b>'
            f'<small class="aec-l">{E(c["lay"])}{" · " + E(c["yrs"]) if c["yrs"] else ""}</small><small class="aec-u">{E(_ae_used(c["used"]))}</small></a>')
def _ae_soon(mk, eng, models):
    k = _AEF(' '.join([mk, eng] + models))
    return (f'<div class="aec aec-soon" data-t="c" data-k="{E(k)}" aria-disabled="true" title="Coming soon"><span class="aec-p aec-ic">{_AE_IC}</span>'
            f'<span class="aec-b">Coming soon</span><b>{E(mk)} {E(eng)}</b><small class="aec-u">{E(_ae_used(models))}</small></div>')
_ae_live = sorted(AE_LIVE.values(), key=lambda c: (c['o'], c['name']))
_ae_soonl = sorted(AE_SOON.items(), key=lambda kv: (kv[0][0], kv[0][1]))
_aeN, _aeS = len(_ae_live), len(_ae_soonl)
_ae_n = lambda t: sum(t in c['t'] for c in _ae_live)
AE_TABS = [('all', 'All', ''), ('bmw', 'BMW', _ae_n('b')), ('supercars', 'Supercars', _ae_n('s')), ('performance', 'Performance', _ae_n('p')),
           ('honda', 'Honda', _ae_n('h')), ('soon', 'Coming soon', _aeS)]
_ae_tabs = ('<nav class="ctabs aetabs" aria-label="Kinds of engine">' + ''.join(
    f'<a href="/engines/{"?type=" + k if k != "all" else ""}" data-type="{k}"{" aria-current=true" if k == "all" else ""}>{t}{f" <small>{n}</small>" if n else ""}</a>'
    for k, t, n in AE_TABS if k in ('all', 'soon') or n) + '</nav>')
_ae_body = f'''<div class="pg"><div class="ph ph-f"><section class="finder aefind" aria-labelledby="fh"><h1 id="fh"><span class="ph-e">Engines</span>Every engine.</h1>
<p class="lede">{_aeN} engines with their own page, from the BMW B58 to the Ferrari F154: owner complaints, recalls and a YouTube owner score by model year. One engine for every other model we cover is coming soon.</p>
<div class="fq"><input id="aeq" type="search" placeholder="e.g. LS3, B58, 2JZ, Honda K20" autocomplete="off" aria-label="Search engines" aria-controls="aegrid"></div>
<p class="fnote" id="aen" aria-live="polite"><b>{_aeN}</b> engines · <b>{_aeS}</b> coming soon</p></section></div>
<section class="aeng" id="aegrid">{_ae_tabs}
<section class="aes" data-s="live"><h2>Engine pages <span class="h2s">YouTube rank in the corner, where owners have posted enough videos.</span></h2><div class="aeg">{"".join(_ae_card(c, i == 0) for i, c in enumerate(_ae_live))}</div></section>
<section class="aes" data-s="soon" data-nosnippet><h2>Coming soon <span class="h2s">One engine per model, the one EPA lists on the most model years. Pages are on the way.</span></h2><div class="aeg">{"".join(_ae_soon(mk, eng, ms) for (mk, eng), ms in _ae_soonl)}</div></section>
<p class="aenone" hidden>No engine matches that yet. Try a code like B58 or a model like Camry.</p>
<p class="note aehubs">Engine hubs: <a href="/engines/bmw/">BMW engines</a> · <a href="/engines/supercars/">Supercar engines</a> · <a href="/engines/performance/">Performance engines</a> · <a href="/check-engine-light/">Check engine light codes</a> (OBD-II trouble codes, a different lookup)</p>
<p class="ph-cr">Engine images: AI-generated illustrations by The Lemon Index, free under CC BY 4.0 (<a href="/images/">download</a>). Engine sizes and cylinders: EPA (fueleconomy.gov).</p></section></div><script src="/assets/engines.js?v=1" defer></script>'''
page('/engines/', 'Every Car Engine: Reliability, Problems & YouTube Owner Ranks',
     f'Search {_aeN} car engines, from the BMW B58 and N54 to the GM LS3 and Ferrari F154: owner complaints, recalls and YouTube owner ranks by model year. {_aeS} more coming soon.',
     _ae_body, ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Every car engine", "url": BASE + '/engines/',
                    "hasPart": [{"@type": "WebPage", "name": c['name'], "url": BASE + c['url']} for c in _ae_live if '#' not in c['url']]}])
AE_URLS.append('/engines/')
# search index rows: [name, brand, url, kind, years, aliases, soon]
for c in _ae_live: AE_FIND.append((c['name'] + ' engine', c['mk'], c['url'], 'eng', (), ' '.join([c['code'], c.get('alias', ''), 'engine'] + c['used']), 0))
for (mk, eng), ms in _ae_soonl: AE_FIND.append((f'{mk} {eng} engine ({", ".join(ms[:3])}{"…" if len(ms) > 3 else ""})', mk, '', 'eng', (), ' '.join(ms + ['engine']), 1))
print('all engines page:', _aeN, 'live,', _aeS, 'coming soon,', len(_ae_models), 'models')
