# Supercar engines (11-11, Elijah: "a supercar engines section like the BMW engines build"): /engines/supercars/ + /engines/<engine>/.
# exec'd by build.py after vehicles_pages.py and before the BMW pages phase (bmw_pages.py lists these images on /images/ and in the image
# sitemap from SCE_IMGS). Same design as the BMW engine pages v2 (article.eng2: engine image hero, one-line answer + chips, per-year chart,
# rules folded, compact versions table, folded FAQ).
# Data: data/supercar_engines.json (data_supercar_engines.py: EPA versions -> engine, every engine sourced), data/supercar_engine_yt.json
# (YouTube tone per engine and year, written by the YouTube workers: 3 Lemon Index/data/yt/engine_studies.py), data/supercar_engine_photos.json.
# Supercars draw very few government complaints, so a complaints-by-year chart only shows where there's real volume (30+ complaints the
# model name or the owner's words tie to the engine, over 3+ years). Everywhere else the page says so and leads with YouTube, recalls and
# the automaker's repair notes. Nothing is estimated or padded.
import html as _shtml
SCENG = _load('data/supercar_engines.json') if os.path.exists('data/supercar_engines.json') else {'engines': {}, 'cars': {}}
# YouTube scores: the workers write data/supercar_engine_yt.json in the main checkout (and commit it when they deploy); a snapshot of it is
# committed with each engine-page push so builds from other checkouts keep the ranks. The live file wins per engine.
SCY = dict(_load('data/supercar_engine_yt_snapshot.json') if os.path.exists('data/supercar_engine_yt_snapshot.json') else {})
SCY.update(_load('data/supercar_engine_yt.json') if os.path.exists('data/supercar_engine_yt.json') else {})
SCP = _load('data/supercar_engine_photos.json') if os.path.exists('data/supercar_engine_photos.json') else {}
SCE_URLS, SCE_IMGS = [], []
SCE_SLUG = {'rr-n73': 'rolls-royce-n73', 'rr-n74': 'rolls-royce-n74'}
SCE_URL = lambda e: f'/engines/{SCE_SLUG.get(e, e)}/'
SCE_HUB = '/engines/supercars/'
SC_NAME = {re.sub(r'[^a-z0-9]+', '-', c['name'].lower().replace("'", '')).strip('-'): c['name'] for c in (_load('data/supercars.json') if os.path.exists('data/supercars.json') else [])}
_SCCBY = 'https://creativecommons.org/licenses/by/4.0/'
_SCE_AI = ('Illustration (AI-generated) in the style of a factory press photo, not a photo of a specific engine; brand names and logos belong to their owners. '
           f'Free to use under <a href="{_SCCBY}" rel="noopener license">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>')
_SCYTI = '<svg aria-hidden="true" viewBox="0 0 24 24" width="11" height="11"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>'

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
ENG_POOL_RANK = {u: i + 1 for i, u in enumerate(sorted(ENG_POOL, key=lambda u: (-ENG_POOL[u], u)))}
ENG_POOL_N = len(ENG_POOL_RANK)
ENG_POOL_LBL = 'engines with a YouTube study'
SCE_YTRANK = {e: ENG_POOL_RANK[SCE_URL(e)] for e in _SCAVG if SCE_URL(e) in ENG_POOL_RANK}
SCE_NRANK = {g: ENG_POOL_N for g in ('super', 'perf')}
GW = {'super': ENG_POOL_LBL, 'perf': ENG_POOL_LBL}
# 11-12 round 2: perf-file-only engine pages (engine_more.py builds them from data/perf/*.json engines whose `page` is this URL) and the
# engine head-to-heads: (url, [engine page urls], "the other engines" label). The FA24 slot uses the WRX's turbo FA24 page once a performance
# file links one, else the BRZ/GR86 FA20/FA24 page (the page says which).
ENG_PERF_ONLY = {'/engines/vw-ea888/': ('VW EA888 2.0 TSI', 'Volkswagen', True), '/engines/subaru-fa24f/': ('Subaru FA24F 2.4 turbo', 'Subaru', False)}   # (name, make, used in cars not covered yet)
def _fa24_url():
    for _p in sorted(glob.glob('data/perf/*.json')):
        if _p.endswith('.auto.json'): continue
        for _k, _v in ((_load(_p) or {}).get('engines') or {}).items():
            if _v.get('page') and re.search(r'FA24D?IT|FA24F', _k + ' ' + (_v.get('name') or ''), re.I): return _v['page']
    return '/engines/subaru-fa/'
import glob
ENG_H2H = [('/engines/compare/fa24-vs-ea888-vs-coyote-vs-b58/', [_fa24_url(), '/engines/vw-ea888/', '/engines/ford-coyote/', '/engines/bmw-b58/'], 'FA24, EA888, Coyote and B58')]
def eng_band(url):
    """which third of the pool an engine's YouTube tone sits in: 'top' / 'mid' / 'low' (None = no study)"""
    r = ENG_POOL_RANK.get(url)
    if not r: return None
    return 'top' if r <= ENG_POOL_N / 3 else 'mid' if r <= 2 * ENG_POOL_N / 3 else 'low'
_EBAND = {'top': 'in the top third', 'mid': 'in the middle third', 'low': 'in the bottom third'}
def eng_verdict(url, nm, tone, eng_recalls, issues):
    """(short word, one-line verdict, FAQ answer start) from our own numbers only: the YouTube tone and its place in the pool, the engine
    recalls on record, the known issues the performance pages list. Never a failure rate."""
    b = eng_band(url); rk = ENG_POOL_RANK.get(url)
    iss = [i for i in (issues or []) if not i['t'].lower().startswith('no ')]
    rec = eng_recalls or 0
    pos = f'YouTube owner tone {tone}/100, #{rk} of {ENG_POOL_N} {ENG_POOL_LBL} ({_EBAND[b]})' if b else ''
    tail = (f'{rec} engine-related recall{"" if rec == 1 else "s"} on record' if rec else 'no engine-related recall on record') + (f', {len(iss)} known issue{"" if len(iss) == 1 else "s"} listed below' if iss else '')
    if not b: return ('Not rated yet', f'Not rated yet: no YouTube study for the {nm} yet; {tail}.', f'We can&#39;t rate it yet: there&#39;s no YouTube owner study for it, and owner complaints are filed by car, not engine. It has {tail}.')
    if b == 'top' and rec <= 1: w, a = 'A safer bet', 'Mostly yes.'
    elif b == 'low': w, a = 'Less liked than most on YouTube', 'Not one of the safer bets on our data.'
    else: w, a = 'Middle of the pack', 'Mostly, with known issues to check.' if (iss or rec) else 'Mostly.'
    if b == 'top' and rec > 1: w, a = 'Liked, but check the recalls', 'Mostly, if the recalls were done.'
    return (w, f'{w}: {pos}; {tail}.', f'{a} {pos}; {tail}.')

SC_NAME = {**{c['slug']: c['name'] for _d in SCENG['engines'].values() for c in _d['cars']}, **SC_NAME}
def _car_href(c):
    """the car's own page: a supercar page, or a performance-car page once it exists (another agent adds those from data/perf_cars.json)"""
    if c.get('page'): return f'/supercars/{c["slug"]}/'
    for u in ((f'/cars/{c["perf"]}/', f'/performance/{c["perf"]}/') if c.get('perf') else ()):
        if os.path.exists(os.path.join(OUT, u.strip('/'), 'index.html')): return u
    return None
SC_MAKE = {re.sub(r'[^a-z0-9]+', '-', c['name'].lower().replace("'", '')).strip('-'): c['make'] for c in (_load('data/supercars.json') if os.path.exists('data/supercars.json') else [])}
def _sce_label(d, slug):
    """the car's name as this engine's page should say it: a family that had other engines too is named by its versions when there are
    one or two (the F154 page says "California T", not "California")"""
    nm = SC_NAME.get(slug, slug)
    if len(SCENG['cars'].get(slug) or {}) > 1:
        vs = sorted({v for y in d['years'].values() for v in y['cars'].get(slug, [])})
        if 1 <= len(vs) <= 2: return SC_MAKE.get(slug, nm.split()[0]) + ' ' + ' / '.join(vs)
    return nm
def _sce_cars_txt(d):
    return ', '.join(_sce_label(d, c['slug']) for c in d['cars'])
def _sce_short(d):
    nm = [_sce_label(d, c['slug']) for c in d['cars']]
    mk = d['make']
    nm = [n.replace(mk + ' ', '') if n.startswith(mk + ' ') else n for n in nm]
    return ', '.join(nm[:-1]) + (' and ' if len(nm) > 1 else '') + nm[-1]
def _sce_hp(d):
    a, b = d['hp']
    return f'{a:,}' + (f'–{b:,}' if b != a else '')
def _sce_rec_li(r):
    yrs = r['years']; ys = f'{yrs[0]}' + (f'–{str(yrs[-1])[-2:]}' if len(yrs) > 1 else '')
    cars = ', '.join(SC_NAME.get(re.sub(r'[^a-z0-9]+', '-', c.lower()).strip('-'), c) for c in r['cars'])
    return (f'<li><p class="advh"><a href="https://www.nhtsa.gov/recalls?nhtsaId={E(r["id"])}" target="_blank" rel="noopener nofollow">{E(r["id"])}</a> '
            f'<small>{E(r["part"] or "Other")} · {E(cars)} {ys}</small></p><p>{E(rsum(r) if "rsum" in globals() else r["summary"])}</p></li>')

WHY = {'super': 'Supercars sell in small numbers, so we show YouTube, recalls and the automaker&#39;s repair notes instead.',
       'perf': 'Performance versions are mostly filed under their base model (a Shelby GT500 is filed as a Mustang), so we only count complaints whose model name or the owner&#39;s own words tie them to this engine, and lead with YouTube, recalls and the automaker&#39;s repair notes.'}
SCE_EXTERNAL = {'bmw-s65'}   # 11-11: built by the BMW M3 flagship work in the BMW engine design; the hub links to it, no second page here
_EU_PARENT_OF = lambda c: (globals().get('EU_PARENT') or (lambda *a: None))(c['slug'], c['name'], c.get('perf') or '')
def _sce_page(e):
    d = SCENG['engines'][e]; path = SCE_URL(e); yrs = d['years']; ys = sorted(yrs, key=int); y0, y1 = int(ys[0]), int(ys[-1])
    yts, ytavg = _sce_yt(e); rk = SCE_YTRANK.get(e); nm = d['name']; mk = d['make']; g = _GRP(e)
    cars_s = _sce_short(d); tot = d['complaints']
    # one-line answer + chips
    yb = max(yts, key=yts.get) if len(yts) >= 2 and len(set(yts.values())) > 1 else None
    ans1 = (f'{E(mk)}&#39;s {E(d["size"])} {E(d["asp"])} {E(d["layout"])} in the {E(cars_s)}, model years {y0}' + (f'–{y1}' if y1 != y0 else '') + '.'
            + (f' YouTube likes the <b>{yb}</b> best.' if yb else ''))
    _eux = [(fid, nm_) for fid, nm_, _ys, _vs in (globals().get('EU_CARS') or (lambda u: []))(path) if not any(_EU_PARENT_OF(c) == fid for c in d['cars'])]
    # 11-13 nav QB (report v2 #3: the 2GR page read like a Lotus page): a supercar-hub engine that is also in everyday /cars/ models is
    # mostly used in those (supercars sell in the hundreds or low thousands a year; the 2GR's Camry, RAV4, Highlander... and the 3.5
    # EcoBoost's F-150 sell in the millions), so its page is filed under Engines > its maker, opens on those cars (best sellers first, with
    # the years our data has) and shows one of them instead of the supercar-branded illustration
    _main = g == 'super' and bool(_eux)
    _hpw, _ylo, _yhi, mfig = '', y0, y1, ''
    if _main:
        _mu = sorted(((fid, nm_, set(ENGINE_USES[path][fid]['years']), ENGINE_USES[path][fid]['src']) for fid, nm_ in _eux),
                     key=lambda r: -(BYNAME.get(r[1]) or {}).get('sold', 0))
        _mn = lambda fid, nm_: 'F-150' if fid == 'ford-f-series' else nm_[len(mk) + 1:] if nm_.startswith(mk + ' ') else nm_
        _my = sorted(set().union(*(r[2] for r in _mu))); _ms = sorted(set().union(*(r[3] for r in _mu)))
        _ylo, _yhi = min(_my[0], y0), max(_my[-1], y1); _hpw = f', {E(_sce_cars_txt(d))}'
        _cl = [f'<a href="/cars/{fid}/">{E(_mn(fid, nm_))}</a>' for fid, nm_, _y, _s in _mu]
        _asp = '' if ' or ' in d['asp'] else E(d['asp']) + ' '   # "naturally aspirated or supercharged": the supercharger is the Lotus's
        ans1 = (f'{E(mk)}&#39;s {E(d["size"])} {_asp}{E(d["layout"])} in the ' + (', '.join(_cl[:-1]) + ' and ' + _cl[-1] if len(_cl) > 1 else _cl[0])
                + f', model years {_my[0]}–{_my[-1]} (from {" and ".join(_EU_SRC[s].replace(" (NHTSA)", ", via NHTSA") for s in _ms)}), and in the {E(_sce_cars_txt(d))}, {y0}' + (f'–{y1}' if y1 != y0 else '') + '.')
        for fid, nm_, _y, _s in _mu:   # the best seller with an illustration of one of its years with this engine (year_slider.py)
            _iy = [y for y in sorted(_y, reverse=True) if YSL.ai_src(fid, y)]
            if _iy: mfig = YSL.ai_year_html(fid, _iy[0], 'Ford F-150' if fid == 'ford-f-series' else nm_, hero=True); break
    elif _eux: ans1 += ' Also in the ' + ', '.join(f'<a href="/cars/{fid}/">{"Ford F-150" if fid == "ford-f-series" else E(nm_)}</a>' for fid, nm_ in _eux[:4]) + (' and more' if len(_eux) > 4 else '') + ' (below).'
    chips = (f'<div class="trc"><div><b>{_ylo}' + (f'–{str(_yhi)[-2:]}' if _yhi != _ylo else '') + '</b><span>model years</span></div>'
             + f'<div><b>{_sce_hp(d)}</b><span>hp (factory{_hpw})</span></div>'
             + (f'<div><b>#{rk}</b><span>YouTube rank of {SCE_NRANK[g]} {GW[g]}</span></div>' if rk else '<div><b>–</b><span>YouTube rank coming</span></div>') + '</div>')
    # 11-12 round 2 (UX test, Devin): a one-line verdict from our own numbers, the performance pages' known issues for this engine, and why
    # the car pages show more complaints and recalls than this page
    _x = _PPX.engine_ext(path); _iss = list((_x or {}).get('issues', {}).values())
    _ne = sum(1 for r in d['recalls'] if r['eng'])
    _vw, _vline, _vfaq = eng_verdict(path, nm, ytavg, _ne, _iss + [dict(t=n) for n, u in d.get('notes') or []])
    chips += f'<p class="note engvd"><b>{E(_vline.split(":", 1)[0])}:</b>{E(_shtml.unescape(_vline.split(":", 1)[1]))}' + (f' <a href="{ENG_H2H[0][0]}">Compare it with the {E(ENG_H2H[0][2])} →</a>' if path in ENG_H2H[0][1] else '') + '</p>'
    _ct = _PPX.engine_car_totals(path); _gap = ''
    if _ct:
        _gap = ('<p class="note">Why the car page' + ('s show' if len(_ct) > 1 else ' shows') + ' more: '
                + '; '.join(f'the <a href="{E(u)}">{E(sh)} page</a> counts {n:,} complaints and {rr} recall campaigns for {a}–{b}, everything NHTSA files as &quot;{E(m)}&quot;, other engines included' for sh, u, m, a, b, n, rr in _ct)
                + f'. This page counts only the {tot:,} complaint{"" if tot == 1 else "s"} and {len(d["recalls"])} recall{"" if len(d["recalls"]) == 1 else "s"} we can tie to the {E(nm)} by model name or the owner&#39;s own words.</p>')
    # per-year chart
    sec = list((globals().get('HD_SCE') or (lambda _e: []))(e))   # 11-12 round 2: the F-150's own data first (hd_pages.py)
    sec.append((globals().get('EU_CARS_HTML') or (lambda *a: ''))(path))   # 11-13 N3: the everyday /cars/ models with it, each year linked
    mxn = max([1] + [v['n'] for v in yrs.values()])
    def carsof(y): return ', '.join(_sce_label(d, s).replace(mk + ' ', '') for s in yrs[y]['cars'])
    _eun = {c['slug']: c for c in d['cars']}
    def carsof_h(y):   # 11-13 N3 (nav report 3): each name links its regular model's year page when there is one
        _u = lambda s: (globals().get('EU_YEAR_URL') or (lambda *a: ''))(s, (_eun.get(s) or {}).get('name', ''), (_eun.get(s) or {}).get('perf') or '', y)
        return ', '.join((f'<a href="{_u(s)}">{E(_sce_label(d, s).replace(mk + " ", ""))}</a>' if _u(s) else E(_sce_label(d, s).replace(mk + ' ', ''))) for s in yrs[y]['cars'])
    def row(y):
        sc = yts.get(int(y)); n = yrs[y]['n']
        yt = (f'<span class="eg-t"><i style="width:{sc}%"></i></span><b>{sc}</b>' if sc is not None else '<span class="eg-t na"></span><b class="mute">·</b>')
        ow = (f'<span class="eg-o"><i style="width:{n / mxn * 100:.0f}%"></i></span><b>{n:,}</b>' if n else '<span class="eg-o na"></span><b class="mute">0</b>') if d['chart'] else ''
        return f'<div class="egr"><span class="egy">{y}<small>{carsof_h(y)}</small></span>{ow}{yt}</div>'
    nc = '' if d['chart'] else (f'<p class="note sce-nc"><b>Not enough complaints to chart.</b> Owners filed {tot:,} complaint{"" if tot == 1 else "s"} with the government that we can tie to this engine&#39;s cars, {y0}–{y1}, about any part of the car. '
                                 + WHY[g] + '</p>' if tot else
                                 f'<p class="note sce-nc"><b>Not enough complaints to chart.</b> We found no government complaints we can tie to this engine&#39;s cars. ' + WHY[g] + '</p>')
    if yts or d['chart']:
        head = ('<div class="egh" aria-hidden="true"><span>Year</span>' + ('<span>Owner complaints <em>count, any part of the car</em></span>' if d['chart'] else '')
                + '<span>YouTube tone <em>0-100, higher = better</em></span></div>')
        chart = f'<div class="egc{"" if d["chart"] else " sce1"}">' + head + ''.join(row(y) for y in ys) + '</div>'
    else:
        chart = '<p class="sce-soon"><b>YouTube rank coming.</b> We&#39;re pulling every YouTube video about this engine and its cars now; the score per model year shows here when it&#39;s done.</p>'
    yline = ''
    if len(yts) >= 2 and yb:
        yw = min(yts, key=yts.get); yline = f'YouTube videos are most positive about the <b>{yb}</b> ({yts[yb]}) and least about the <b>{yw}</b> ({yts[yw]}); neighboring years share many of the same videos, so small gaps mean little.'
    rows = []
    for y in ys:
        sc = yts.get(int(y)); vd = ((SCY.get(e) or {}).get('years') or {}).get(y) or {}
        rc = sum(1 for r in d['recalls'] if int(y) in r['years'])
        rows.append([y, carsof_h(y), f'{yrs[y]["n"]:,}', (f'<b>{sc}</b> <small>({vd.get("videos", 0)} videos)</small>' if sc is not None else '<small>not enough videos yet</small>'), str(rc)])
    _tbl = lambda head, R: '<div class="tw"><table class="adv"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in R) + '</tbody></table></div>'
    sec.append('<h2>Reliability by year</h2>' + nc + _gap + chart + (f'<p class="note">{yline}</p>' if yline else '')
               + '<details class="trm"><summary>How we count: owner complaints only where the car&#39;s name and year leave no doubt; YouTube tone from videos that name this engine or its cars. <span>How we count</span></summary>'
               '<p>Owner complaints (NHTSA) are filed by model and year, not engine. We count one for this engine only when the model name and year had no other engine (e.g. "488 GTB", "GT-R"), '
               'or when the owner&#39;s own words name a version that had only this engine that year (Z06, ZR1, Hellcat, GT500 ...). They cover the whole car (wheels, air bags, electrics ...), not only the engine, and none of them is a failure rate. '
               'We chart them only for engines with 30 or more, over 3 or more years. '
               'YouTube tone = how positive the videos are, 0–100, from titles and transcripts (praise vs trouble words, the title counts 3 times), weighted by views; a year needs at least 3 videos&#39; worth. '
               'A video counts for this engine when its title names the engine or a car that only had this engine in the years it names; a video whose title names no model year counts toward every year of that car, so neighboring years share most of their videos.</p></details>'
               + '<details class="cpd engd"><summary>All the numbers, year by year</summary>' + _tbl(['Year', 'Cars', 'Owner complaints', 'YouTube says', 'Recalls'], rows) + '</details>')
    # recalls
    R = d['recalls']; ne = sum(1 for r in R if r['eng'])
    if R:
        sec.append(f'<section class="yc sce-r" id="recalls"><h2>Recalls on cars with this engine <span class="yc-n">{len(R)}</span></h2>'
                   + (f'<p class="yc-cap">{ne} of them {"is" if ne == 1 else "are"} about the engine, fuel, cooling or powertrain. They come first.</p>' if ne else '<p class="yc-cap">None of them is about the engine itself.</p>')
                   + '<ul class="advr">' + ''.join(_sce_rec_li(r) for r in R[:5]) + '</ul>'
                   + (f'<details class="cpd"><summary>Show all {len(R)}</summary><ul class="advr">' + ''.join(_sce_rec_li(r) for r in R[5:]) + '</ul></details>' if len(R) > 5 else '')
                   + '<p class="yc-cap">NHTSA recalls by model and year. A recall counts here when every confirmed version of that model-year had this engine, or the recall names it. Check a car&#39;s VIN for its own open recalls.</p></section>')
    else:
        sec.append('<section class="yc sce-r" id="recalls"><h2>Recalls on cars with this engine</h2><p>No NHTSA recalls we can tie to this engine&#39;s cars.</p></section>')
    # repair notes from the automaker
    t = d['tsb']; top = [x for x in t['top'] if not (re.search(r'\b918\b', x) and e != 'porsche-918-v8')]
    if t['n']:
        sec.append(f'<section class="yc sce-t" id="fixes"><h2>Engine problems {E(mk)} told dealers about</h2><p>{E(mk)} sent dealers <b>{t["n"]}</b> repair note{"" if t["n"] == 1 else "s"} about the engine on these cars'
                   + (', including:</p><ul>' + ''.join(f'<li>{E(x)}</li>' for x in top) + '</ul>' if top else '.</p>')
                   + '<p class="yc-cap">NHTSA manufacturer communications (technical service bulletins), matched by model name and year like the complaints, engine-related ones only. A repair note is not a recall: ask a seller whether it was done.</p></section>')
    _pi = ''.join(f'<li><b>{E(i["t"])}</b> <small>({E(i["kind"])})</small>. {E(i["x"])}' + (f' <b>Fix:</b> {E(i["fix"])}' if i.get('fix') else '')
                  + (f' <small>{i["n"]} owner complaint{"" if i["n"] == 1 else "s"} to NHTSA mention it ({E(", ".join(i["where"]))}).</small>' if i['n'] else '') + '</li>' for i in _iss)
    if d.get('notes') or _pi:
        _srcs = ', '.join(f'<a href="{E(v["u"])}" rel="noopener nofollow">{E(v["t"])}</a>' for v in ((_x or {}).get('sources') or {}).values())
        sec.append('<section class="yc engk"><h2>Known issues on record</h2><ul>' + _pi + ''.join(f'<li>{E(n)} <a href="{E(u)}" rel="noopener">Source</a></li>' for n, u in d.get('notes') or []) + '</ul>'
                   + (f'<p class="yc-cap">Sources: {_srcs}. The same list as on ' + ', '.join(dict.fromkeys(f'<a href="{E(u)}">the {E(n)} page</a>' for n, u, _g in _x['cars'] if u)) + '.</p>' if _pi else '') + '</section>')
    # versions
    vr = []
    for c in d['cars']:
        vs = sorted({v for y in ys for v in yrs[y]['cars'].get(c['slug'], [])})
        yl = c['years']; cn = SC_NAME.get(c['slug'], c['name'])
        hr = _car_href(c)
        _pf = _EU_PARENT_OF(c)
        vr.append([(f'<a href="{hr}">{E(cn)}</a>' if hr else E(cn)) + f' <small>{E(", ".join(vs[:6]))}{" ..." if len(vs) > 6 else ""}</small>'
                   + (f' <small>· <a href="/cars/{_pf}/">{E(EU_MODELS[_pf]["name"])}, every year</a></small>' if _pf else ''),
                   f'{min(yl)}–{str(max(yl))[-2:]}' if len(yl) > 1 else str(yl[0])])
    srcs = ' · '.join(f'<a href="{E(s["url"])}" rel="noopener">{E(s["title"])}</a>' for s in d['src'])
    sec.append('<section class="engv"><h2>Every US version with this engine</h2>' + _tbl(['Car and versions', 'Years'], vr)
               + f'<p class="yc-cap">Engine code{"s" if "," in d["codes"] else ""}: {E(d["codes"])}. ' + (d['made'][:1].upper() + d['made'][1:] + '. ' if d.get('made') else '')
               + f'Power: {_sce_hp(d)} hp, factory figures' + (f' ({E(d["hp_note"])})' if d.get('hp_note') else '') + '. ' + (d.get('caveat', '') + ' ' if d.get('caveat') else '')
               + f'Versions and years: EPA (fueleconomy.gov). Sources: {srcs}.</p></section>')
    faq = [(f'What cars have the {nm} engine?', f'In the US: the {_sce_cars_txt(d)}, model years {y0}–{y1}. See the version table for each one.'),
           (f'Is the {nm} reliable?', _vfaq + ' ' + (('Not enough owner complaints to judge it per car: supercars sell in small numbers. ' if g == 'super' else 'Not enough owner complaints to judge it per car: the government files most performance versions under their base model. ') if not d['chart'] else f'Owners filed {tot:,} complaints we can tie to it, about any part of the car. ')
            + (f'Its cars had {len(R)} recalls ({ne} about the engine, fuel or powertrain). ' if R else '') + 'Have any used car inspected.'),
           (f'How much horsepower does the {nm} make?', f'{_sce_hp(d)} hp in factory figures, depending on the car' + (f' ({d["hp_note"]})' if d.get('hp_note') else '') + '.')]
    sec.append('<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(_shtml.unescape(a))}</p>' for q, a in faq)) + '</section>')
    ph = None if mfig else SCP.get(e); fig = mfig   # QB: an everyday engine shows its best seller, not the supercar-branded illustration
    if ph:
        alt = f'Illustration of the {E(nm)} {E(d["size"])} {E(d["layout"])} engine'
        fig = (f'<figure class="engph"><img src="{E(ph["src"])}"{rset(ph["src"], "(max-width: 700px) 100vw, 680px")} width="{ph["w"]}" height="{ph["h"]}" alt="{alt}" loading="eager">' + YSL.info(_SCE_AI) + '</figure>')
    body = (f'<article class="study tr2 eng2 sce"><p class="kicker">' + (f'<a href="/engines/">Engines</a> › <a href="/engines/?q={E(mk.lower())}">{E(mk)} engines</a>' if _main else '<a href="/engines/supercars/">Supercar engines</a> · <a href="/supercars/">Supercars</a>' if g == 'super' else '<a href="/engines/performance/">Performance engines</a> · <a href="/cars/?type=performance">Performance cars</a>') + '</p>'
            + f'<h1>{E(nm)} engine reliability by year</h1><p class="tra">{ans1} <button type="button" class="shl" data-share="{E(f"{nm} engine reliability, year by year. Free:")}">Share ↗</button></p>{chips}'
            + ''.join(sec) + '</article>')
    title = next(t_ for t_ in (f'{nm} Engine Reliability by Year, Specs & Cars', f'{nm} Engine: Reliability by Year & Specs', f'{nm} Engine Reliability', f'{nm} Engine') if len(t_) <= 65)
    desc = (f'The {_shtml.unescape(nm)} ({_shtml.unescape(d["size"])} {d["asp"]} {d["layout"]}) in the ' + (', '.join('Ford F-150' if fid == 'ford-f-series' else nm_ for fid, nm_, _y, _s in _mu[:4]) + f' and {_sce_cars_txt(d)}, {_ylo}-{_yhi}' if _main else f'{_sce_cars_txt(d)}, {y0}-{y1}') + ': YouTube owner score by year, '
            f'{len(R)} recalls, {t["n"]} repair notes and every US version.')
    ld = [faq_ld([(q, '', _shtml.unescape(a)) for q, a in faq])]
    if ph:
        ld.append({"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": BASE + ph['src'], "url": BASE + ph['src'], "name": ph['title'],
                   "description": f'{ph["title"]}. AI-generated illustration, not a photo of a specific engine.', "width": ph['w'], "height": ph['h'], "encodingFormat": "image/webp",
                   "license": _SCCBY, "acquireLicensePage": BASE + '/images/', "creditText": "The Lemon Index", "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE + '/'},
                   "copyrightNotice": "The Lemon Index (lemonindex.com), CC BY 4.0", "isAccessibleForFree": True})
        if e not in SCE_EXTERNAL: SCE_IMGS.append((path, ph))
    if e not in SCE_EXTERNAL:
        page(path, title, desc, body, ld=ld, vis=fig)
        SCE_URLS.append(path)
    return dict(e=e, y0=y0, y1=y1, yt=ytavg, nyt=len(yts), rec=len(R), tsb=t['n'], tot=tot)

def _sce_hub(g):   # a function, so the hub's locals (order, best, cards ...) don't overwrite build.py globals
    _ST = [_sce_page(e) for e in SCENG['engines'] if _GRP(e) == g]
    HUB = HUBS[g]; NG = len(_ST); NR = SCE_NRANK[g]
    def _skind(e):
        d = SCENG['engines'][e]; lay = d['layout'].lower(); a = d['asp'].lower()
        cyl = '12' if re.search(r'v12|w12|w16|v10', lay) else '8' if 'v8' in lay else '4' if re.search(r'inline-[345]|flat-4', lay) else '6'
        return cyl, ('turbo' in a or 'supercharg' in a), ('hybrid' in a)
    def _scard(s, eager):
        e = s['e']; d = SCENG['engines'][e]; ph = SCP.get(e); cyl, tur, hyb = _skind(e); rk = SCE_YTRANK.get(e)
        img = ''
        if ph:
            th = ph['src'][:-5] + '-640.webp'
            src, w, h = (th, 640, round(ph['h'] * 640 / ph['w'])) if os.path.exists(th.lstrip('/')) else (ph['src'], ph['w'], ph['h'])
            img = (f'<div class="ehc-im"><img src="{E(src)}" width="{w}" height="{h}" alt="{E(d["name"])} {E(d["size"])} {E(d["layout"])} engine" '
                   + ('fetchpriority="high" decoding="async">' if eager else 'loading="lazy" decoding="async">') + f'{YSL.info(_SCE_AI)}</div>')
        main = (f'<p class="ehc-n"><b>{s["yt"]}</b><span>YouTube tone, 0-100<br>{s["nyt"]} scored years</span></p>' if s['yt'] is not None
                else '<p class="ehc-n none"><b>–</b><span>YouTube score coming<br>videos being pulled now</span></p>')
        sub = f'{s["rec"]} recall{"" if s["rec"] == 1 else "s"} · {s["tsb"]} repair note{"" if s["tsb"] == 1 else "s"} to dealers'
        cars = [_sce_label(d, c['slug']).replace(d['make'] + ' ', '') for c in d['cars']]
        chips = ''.join(f'<li>{E(c)}</li>' for c in cars[:5]) + (f'<li class="more">+{len(cars) - 5} more</li>' if len(cars) > 5 else '')
        yrs = f'{s["y0"]}–{str(s["y1"])[-2:]}' if s['y1'] != s['y0'] else str(s['y0'])
        return (f'<li class="ehc" data-rank="{rk or 999}" data-own="{rk or 999}" data-yt="{s["yt"] if s["yt"] is not None else -1}" data-y0="{s["y0"]}" data-y1="{s["y1"]}" data-cyl="{cyl}" '
                f'data-turbo="{1 if tur else 0}" data-hy="{1 if hyb else 0}" data-mk="{E(d["make"])}" data-rec="{s["rec"]}">'
                + img + f'<span class="ehc-rk sce-mk" title="Maker">{E(d["make"])}</span>'
                + (f'<span class="ytbadge ehc-yr" title="YouTube rank by tone, of {NR} {GW[g]}">{_SCYTI}YT #{rk}</span>' if rk
                   else '<span class="ytbadge ehc-yr na" title="YouTube rank coming">' + _SCYTI + 'YT –</span>')
                + f'<h2><a class="ehc-a" href="{SCE_URL(e)}">{E(d["name"])}</a></h2><p class="ehc-t">{E(d["size"])} {E(d["layout"])} {E(d["asp"])} · {yrs}</p>'
                + main + f'<p class="ehc-yt">{sub}</p><ul class="ehc-cars" aria-label="Cars with the {E(d["name"])}">{chips}</ul></li>')
    order = sorted(_ST, key=lambda s: (SCE_YTRANK.get(s['e'], 999), SCENG['engines'][s['e']]['make'], s['y0']))
    cards = [_scard(s, i == 0) for i, s in enumerate(order)]
    kinds = [_skind(s['e']) for s in _ST]
    has = lambda f: any((k[0] == f) if f in ('12', '8', '6', '4') else k[2] if f == 'hy' else k[1] if f == 'turbo' else not k[1] for k in kinds)
    pills = [('all', 'All')] + [(k, lab) for k, lab in (('12', 'V10, V12, W12, W16' if g == 'super' else 'V10, V12'), ('8', 'V8'), ('6', '6-cylinder'), ('4', '3, 4 and 5-cylinder'),
                                                         ('turbo', 'Turbo or supercharged'), ('na', 'Naturally aspirated'), ('hy', 'Hybrid')) if has(k)]
    nscored = NR
    ncars = len({c['perf'] or c['slug'] for s_ in _ST for c in SCENG['engines'][s_['e']]['cars']})
    short = ((f'{NG} engines in {len(SC_MAKE)} supercars, every one sourced. Supercars draw too few government complaints to score per car, so each engine shows its YouTube owner tone, recalls and the automaker&#39;s repair notes.' if g == 'super' else
              f'{NG} engines in {ncars} performance cars, every one sourced. The government files most performance versions under their base model, so each engine leads with its YouTube owner tone, recalls and the automaker&#39;s repair notes.')
             + ('' if nscored else ' YouTube ranks are coming: we&#39;re pulling the videos now.'))
    method = ('Each engine is matched to its cars from EPA&#39;s version list (fueleconomy.gov) and checked against the engine&#39;s Wikipedia article or the automaker. '
              'YouTube tone = how positive the videos that name the engine or its cars are (0–100), averaged over the scored model years; the YT badge ranks engines by it. '
              'Recalls: NHTSA, for cars and years with this engine. Repair notes: the automaker&#39;s engine-related notes to dealers (NHTSA manufacturer communications). '
              'Owner complaints are charted only where there are 30 or more. None of these is an engine failure rate. Images: AI illustrations, free to use under CC BY 4.0.')
    crumb = ('<a href="/supercars/">Supercars</a> · <a href="/engines/performance/">Performance engines</a> · <a href="/engines/bmw/">BMW engines</a>' if g == 'super' else
             '<a href="/cars/?type=performance">Performance cars</a> · <a href="/engines/supercars/">Supercar engines</a> · <a href="/engines/bmw/">BMW engines</a>')
    body = (f'<div class="advp ehub sceh"><header class="advh1"><p class="ph-e">{crumb}</p><h1>{"Supercar" if g == "super" else "Performance"} engines, by year.</h1>'
            f'<p class="ans">{short} <span class="ehub-i">{YSL.info(method)}</span></p></header>'
            '<div class="ehub-bar"><div class="ehub-f" role="group" aria-label="Show">'
            + ''.join(f'<button type="button" class="ehub-p" data-f="{k}" aria-pressed="{"true" if k == "all" else "false"}">{lab}</button>' for k, lab in pills)
            + '</div><label class="ehub-s">Sort <select id="ehub-sort"><option value="own">YouTube rank</option><option value="new">Newest</option>'
              '<option value="old">Oldest</option><option value="rec">Most recalls</option><option value="mk">Maker</option></select></label></div>'
            + f'<p class="ehub-c" aria-live="polite">{len(cards)} engines</p><ol class="ehub-g">{"".join(cards)}</ol>'
            + share_line(f'Every {"supercar" if g == "super" else "performance car"} engine, year by year: YouTube score, recalls, repair notes. Free:') + '</div><script src="/assets/enghub.js?v=2" defer></script>')
    best = [s for s in order if s['yt'] is not None]
    hub_ans = ((f'We cover {NG} supercar engines, from the Ferrari F154 to the Bugatti W16. Supercars draw too few owner complaints to rank per car, so we rank them by YouTube owner tone' if g == 'super' else
                f'We cover {NG} performance-car engines, from the Hellcat and the Coyote to the LS family and the EJ257. The government files most performance versions under their base model, so we rank them by YouTube owner tone')
               + (f': the {SCENG["engines"][best[0]["e"]]["name"]} ranks first ({best[0]["yt"]} of 100).' if best else ' once the video pull finishes.')
               + ' Each engine page shows its recalls and the automaker&#39;s repair notes by model year.')
    faq = ([('Which supercar engine is the most reliable?', _shtml.unescape(hub_ans)),
            ('Why no owner-complaint score for supercars?', 'The Lemon Index scores cars by government complaints per car sold. Supercars sell in the hundreds or low thousands a year and draw a handful of complaints, too few to rank fairly, so we show the count and lead with YouTube, recalls and repair notes.')] if g == 'super' else
           [('Which performance car engine is the most reliable?', _shtml.unescape(hub_ans)),
            ('Why no owner-complaint score for performance engines?', 'Owners file government complaints under the model name, and a Hellcat is filed as a Challenger, a GT500 as a Mustang. We only count complaints whose model name or the owner&#39;s own words tie them to one engine, which is too few to rank fairly, so we lead with YouTube, recalls and repair notes.')])
    faq = [(q, _shtml.unescape(a)) for q, a in faq]
    body = body.replace('</div><script src="/assets/enghub.js', '<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq)) + '</section></div><script src="/assets/enghub.js', 1)
    page(HUB, 'Supercar Engines: Reliability by Year (Ferrari, Lamborghini, McLaren)' if g == 'super' else 'Performance Car Engines by Year: Hellcat, Coyote, LS, 2UR', _shtml.unescape(short.replace('&#39;', "'")), body,
         ld=[faq_ld([(q, '', a) for q, a in faq]), {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Supercar engines" if g == 'super' else 'Performance car engines', "url": BASE + HUB,
             "hasPart": [{"@type": "WebPage", "name": SCENG['engines'][s['e']]['name'], "url": BASE + SCE_URL(s['e'])} for s in order]}])
    SCE_URLS.insert(0, HUB)
for _g in ('perf', 'super'):
    if any(_GRP(e) == _g for e in SCENG['engines']): _sce_hub(_g)
exec(open('engine_more.py', encoding='utf-8').read())   # 11-12 round 2: the EA888 page (from the Golf R file) + engine head-to-heads
print('supercar engine pages', len(SCE_URLS), 'images', len(SCE_IMGS), 'YouTube-ranked', len(SCE_YTRANK))
