# Performance-car page template (11-11, Elijah: "do first full performance + engine + yt pull for BMW M3 Comp so I can see how the layout
# looks, then we dupe for other super cars and performance cars"; approved the same day: "this is good template"; memory
# lemon-performance-section: performance cars lead with performance and the engine, not the Lemon score).
#
# One template, data only per car:
#   data/perf/<slug>.json       hand-sourced: generations, every variant's specs with source ids, engines (facts, known issues with sources
#                               and a regex for owner complaints), compare chips, the NHTSA model names, the source list
#   data/perf/<slug>.auto.json  computed by data_perf.py: NHTSA complaints by year and part, issue mentions per generation, recalls,
#                               YouTube topics per study, a snapshot of the study scores
#   live at build time          data/yt_scores.json (site models' YouTube tone per year), data/supercar_engine_yt.json + data/bmw_engine_yt.json
#                               (car, trim and engine studies from auto_gens.py); topics re-read from study folders that weren't pulled yet
# Two modes:
#   - the car already has a model page (the BMW M3): its hero becomes the generation slider and its Overview the performance story; every
#     other tab stays
#   - no page yet (most performance cars): a standalone page at the data's `page` with Overview / Problems & recalls / Questions tabs
# Sources: each spec card, engine block and buy list ends in one small "Sources" fold listing its own sources (numbered as in the full list
# at the bottom); no superscripts on the values (11-11 Elijah). The citations stay in the HTML and in the page's schema (WebPage.citation).
# Images: generations with an `img` get the slider; otherwise one hero image (the car's coming-soon AI picture) and the generation pills
# only switch the content.
#
# To add a car: write data/perf/<slug>.json (copy bmw-m3.json's shape), add its YouTube study to auto_gens (3 Lemon Index/data/yt/
# engine_studies_m3.py CARS), run `py -X utf8 data_perf.py <slug>`, then build.
import glob, html, json, os, re
from bs4 import BeautifulSoup
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 'https://lemonindex.com'
E = lambda s: html.escape(str(s), quote=True)
V = '3'   # perf.css / perf.js version (11-12: generation filter)
ASSET = f'<link rel="stylesheet" href="/assets/perf.css?v={V}"><script src="/assets/perf.js?v={V}" defer></script>'
def _load(p, d=None):
    p = os.path.join(HERE, p)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else d

# 11-13 navigation fix N3 (report problem 4: "Mustang GT and Mustang don't link each other"): every performance page's regular model
# (/cars/<id>/), by name: the model line it is a version of. data/perf/<slug>.json `parent` (a URL) wins. build.py's engine_uses.py turns it
# into two-way chips: the parent's model and year pages list the performance versions, and the performance page links its parent and years.
PARENTS = {'mustang-gt': 'ford-mustang', 'shelby-gt350': 'ford-mustang', 'shelby-gt500': 'ford-mustang', 'mustang-mach-1': 'ford-mustang',
           'mustang-dark-horse': 'ford-mustang', 'mustang-boss-302': 'ford-mustang', 'svt-cobra': 'ford-mustang', 'mustang-gtd': 'ford-mustang',
           'camaro-ss': 'chevrolet-camaro', 'camaro-zl1': 'chevrolet-camaro', 'camaro-z28': 'chevrolet-camaro',
           'challenger-392': 'dodge-challenger', 'challenger-hellcat': 'dodge-challenger', 'challenger-demon': 'dodge-challenger',
           'charger-392': 'dodge-charger', 'charger-hellcat': 'dodge-charger', 'durango-srt': 'dodge-durango', 'trackhawk': 'jeep-grand-cherokee',
           'grand-cherokee-srt': 'jeep-grand-cherokee', 'wrangler-392': 'jeep-wrangler', 'chrysler-300-srt8': 'chrysler-300', 'neon-srt4': 'dodge-neon',
           'ram-trx': 'ram-pickup', 'ram-srt10': 'ram-pickup', 'f150-raptor': 'ford-f-series', 'f150-raptor-r': 'ford-f-series', 'svt-lightning': 'ford-f-series',
           'bronco-raptor': 'ford-bronco', 'focus-rs': 'ford-focus', 'focus-st': 'ford-focus', 'fiesta-st': 'ford-fiesta', 'cobalt-ss': 'chevrolet-cobalt',
           'trailblazer-ss': 'chevrolet-trailblazer', 'cts-v': 'cadillac-cts', 'escalade-v': 'cadillac-escalade', 'civic-type-r': 'honda-civic',
           'golf-r': 'volkswagen-golf', 'vw-r32': 'volkswagen-golf', 'lancer-evolution': 'mitsubishi-lancer', 'mazdaspeed3': 'mazda3',
           'elantra-n': 'hyundai-elantra', 'veloster-n': 'hyundai-veloster', 'gr-corolla': 'toyota-corolla', 'lexus-is-f': 'lexus-is', 'lexus-is-500': 'lexus-is',
           'tlx-type-s': 'acura-tlx', 'amg-c63': 'mercedes-benz-c-class', 'amg-e63': 'mercedes-benz-e-class', 'amg-e55': 'mercedes-benz-e-class',
           'amg-gle63': 'mercedes-benz-m/gle', 'amg-cla45': 'mercedes-benz-cla', 'bmw-m3': 'bmw-3-series', 'bmw-m340i': 'bmw-3-series', 'bmw-m4': 'bmw-4-series',
           'bmw-m5': 'bmw-5-series', 'bmw-x3-m': 'bmw-x3', 'bmw-x5-m': 'bmw-x5', 'audi-s4': 'audi-a4', 'audi-rs3': 'audi-a3', 'audi-rs6': 'audi-a6',
           'subaru-wrx': 'subaru-impreza', 'wrx-sti': 'subaru-impreza', 'macan-gts-turbo': 'porsche-macan'}
def parent_of(D):
    """a performance page's regular model id ('' if none)"""
    p = (D.get('parent') or '').strip('/').split('/')
    return '/'.join(p[1:]) if len(p) > 1 and p[0] == 'cars' else PARENTS.get(D.get('slug', ''), '')

def _avg(d, y0, y1):
    s = [v['score'] for y, v in (d or {}).items() if y0 <= int(y) <= y1 and v and v.get('score') is not None]
    return (int(sum(s) / len(s) + 0.5), len(s)) if s else (None, 0)   # 11-12: half-up, the same rounding as the engine pages

def engine_years(e, A=None):
    """11-12 (UX test: /engines/bmw-s58/ said 'not enough YouTube videos' while the M3 page said '#1'): ONE source for an engine's YouTube
    tone, read the same way by the performance pages and the engine pages: the engine's own study (supercar_engine_yt.json, live file first,
    then the snapshot data_perf.py took), else the BMW engine attribution (bmw_engine_yt.json)."""
    SCY = {**((A or {}).get('scores') or {}), **(_load('data/supercar_engine_yt_snapshot.json', {}) or {}), **(_load('data/supercar_engine_yt.json', {}) or {})}
    src, key = (e.get('yt') or ['scy', ''])[:2]
    return ((SCY.get(e.get('study') or '') or {}).get('years') or (SCY.get(key or '') or {}).get('years')
            or ((_load('data/bmw_engine_yt.json', {}) or {}).get(key) if src == 'bmw' else None) or {})

def engine_tone(e, A=None):
    """(tone 0-100, scored years): the average over every scored year of the engine, so the car page and the engine page show the same number"""
    return _avg(engine_years(e, A), 0, 9999)

def engine_ext(url):
    """11-12: what the performance pages know about the engine whose page is `url` (e.g. '/engines/bmw-s58/'), for the engine page itself:
    hp of every performance version using it, the known issues with their sources and owner-complaint counts, the YouTube tone.
    None when no performance page uses this engine."""
    out = None
    for p in sorted(glob.glob(os.path.join(HERE, 'data', 'perf', '*.json'))):
        if p.endswith('.auto.json'): continue
        D = _load(p); A = _load(p[:-5] + '.auto.json', {}) or {}
        for code, e in (D.get('engines') or {}).items():
            if not url or e.get('page') != url: continue
            if out is None: out = dict(hp=set(), issues={}, cars=[], tone=engine_tone(e, A), years=engine_years(e, A), study=e.get('study'), sources={})
            gs = [g for g in D['gens'] if g['engine'] == code]
            out['cars'].append((D['short'], D['page'], ', '.join(g['code'] for g in gs)))
            for g in gs:
                for v in g['variants']:
                    if isinstance(_hp(v), (int, float)): out['hp'].add(int(_hp(v)))
            for i in e.get('issues') or []:
                if i['t'].lower().startswith('no known pattern'): continue
                it = out['issues'].setdefault(i['t'], dict(i, n=0, where=[]))
                for g in gs:
                    n = ((((A.get('nhtsa') or {}).get('gens') or {}).get(g['id']) or {}).get('issues') or {}).get(i['t'], {}).get('n') or 0
                    if n: it['n'] += n; it['where'].append(f'{g["code"]} {D["short"]}')
                for sid in i.get('src') or []:
                    if sid in D['sources']: out['sources'][sid] = D['sources'][sid]
    return out

def engine_car_totals(url):
    """11-12 round 2 (UX test, Devin: the Mustang page said 103 S650 complaints and 15 recalls, the Coyote page 27 complaints and no recalls):
    per performance page using the engine at `url`, the counts that page shows for the generations with this engine (every car NHTSA files
    under the model name) -> [(short, page, nhtsa name, y0, y1, complaints, recall campaigns)]"""
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, 'data', 'perf', '*.json'))):
        if p.endswith('.auto.json'): continue
        D = _load(p); A = _load(p[:-5] + '.auto.json', {}) or {}
        codes = [c for c, e in (D.get('engines') or {}).items() if url and e.get('page') == url]
        gs = [g for g in D.get('gens', []) if g['engine'] in codes]
        if not gs: continue
        y0, y1 = min(g['y0'] for g in gs), max(g['y1'] for g in gs)
        n = sum((((A.get('nhtsa') or {}).get('gens') or {}).get(g['id']) or {}).get('n') or 0 for g in gs)
        rc = A.get('recalls') or {}; rec = len({r['id'] for g in gs for y in range(g['y0'], g['y1'] + 1) for r in rc.get(str(y), [])})
        out.append((D['short'], D['page'], ((D.get('nhtsa') or {}).get('models') or [''])[0].title(), y0, y1, n, rec))
    return out

def sce_counts(url, y0, y1):
    """the engine page's own counts (data/supercar_engines.json: complaints tied to the engine by model name or the owner's words, recalls tied
    to it) for model years y0-y1, or None when that URL isn't one of those engine pages"""
    S = _load('data/supercar_engines.json', {}) or {}
    for k, d in (S.get('engines') or {}).items():
        if f'/engines/{k}/' != url: continue
        n = sum((d['years'].get(str(y)) or {}).get('n', 0) for y in range(y0, y1 + 1))
        r = sum(1 for x in d.get('recalls') or [] if any(y0 <= y <= y1 for y in x['years']))
        return dict(name=d['name'], n=n, rec=r)
    return None

class Refs:
    """Numbers sources in order of first use. R(ids...) records them for the open card (and returns '' so values carry no superscripts);
    close() gives that card's 'Sources' fold; html() the full numbered list."""
    def __init__(self, S): self.S, self.order, self.cards = S, [], []
    def __call__(self, *ids):
        for i in ids:
            if i not in self.S: continue
            if i not in self.order: self.order.append(i)
            if self.cards and i not in self.cards[-1]: self.cards[-1].append(i)
        return ''
    def open(self): self.cards.append([])
    def close(self, label='Sources'):
        ids = self.cards.pop()
        if not ids: return ''
        li = ''.join(f'<li value="{self.order.index(i) + 1}"><a href="{E(self.S[i]["u"])}" rel="noopener nofollow" target="_blank">{E(self.S[i]["t"])}</a></li>'
                     for i in sorted(ids, key=self.order.index))
        return f'<details class="pf-cs"><summary>{label}</summary><ol>{li}</ol></details>'
    def html(self):
        li = ''.join(f'<li id="pf-s{n}"><a href="{E(self.S[i]["u"])}" rel="noopener nofollow" target="_blank">{E(self.S[i]["t"])}</a> <span>{E(self.S[i]["k"])}</span></li>'
                     for n, i in enumerate(self.order, 1))
        return f'<ol class="pf-srcs">{li}</ol>'
    def ld(self, url, name):
        return {"@context": "https://schema.org", "@type": "WebPage", "@id": url + "#sources", "url": url, "name": name,
                "citation": [{"@type": "CreativeWork", "name": self.S[i]['t'], "url": self.S[i]['u']} for i in self.order]}

_I = {'bolt': '<path d="M13 3 5 13h6l-1 8 8-10h-6z"/>', 'eng': '<rect x="4" y="8" width="13" height="9" rx="1.5"/><path d="M7 8V5h6v3M17 11h3v4h-3M4 12H2"/>',
      'play': '<rect x="3" y="5" width="18" height="14" rx="4"/><path d="m10 9 5 3-5 3z"/>', 'buy': '<path d="M5 12.5 10 17 19 7"/>',
      'warn': '<path d="M12 3.5 21.5 20h-19z"/><path d="M12 10v4.5M12 17.2v.3"/>', 'info': '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8v.2"/>',
      'vs': '<path d="M8 20V9M16 20V4M4 20h16"/>', 'shield': '<path d="M12 3 5 6v6c0 4 3 7.5 7 9 4-1.5 7-5 7-9V6z"/>'}
def ic(k, s=20): return f'<svg aria-hidden="true" viewBox="0 0 24 24" width="{s}" height="{s}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{_I[k]}</svg>'
def _views(n): return f'{n / 1e6:.1f}M views' if n >= 1e6 else f'{round(n / 1e3)}K views' if n >= 1e3 else f'{n} views'
def _z(z):
    """0-60: the magazine test when we have one, else the maker's figure, labelled"""
    if not z: return None, ''
    if z.get('v') is not None: return f'{z["v"]:.1f} s', (z.get('who') or 'Magazine') + ' test'
    if z.get('claim') is not None: return f'{z["claim"]:.1f} s', 'maker figure'
    return None, ''
def _hp(v): return (v.get('hp') or {}).get('v')
def z_fallback(g, v):
    """11-12 round 2 (Devin: the STI and Mustang GT heroes showed '–' for 0-60 while their trim cards list 4.8 s and 4.2 s): the lead trim's
    0-60, else the quickest tested trim of the same generation. -> (value 's', label, trim name or '' when it is the lead trim)"""
    zv, zl = _z(v.get('z60'))
    if zv: return zv, zl, ''
    best = None
    for x in g['variants']:
        xv, xl = _z(x.get('z60'))
        if xv and (best is None or float(xv.split()[0]) < float(best[0].split()[0])): best = (xv, xl, x['name'])
    return best or (None, '', '')

def variant_card(v, R, star):
    R.open(); hp = v.get('hp') or {}; zv, zl = _z(v.get('z60'))
    rows = []
    def row(lbl, val, note=''):
        rows.append(f'<div class="pf-r"><dt>{lbl}</dt><dd>{val}' + (f'<small>{E(note)}</small>' if note else '') + '</dd></div>')
    R(*hp.get('src', []))
    if v.get('tq'): R(*v['tq']['src']); row('Torque', f'{E(v["tq"]["v"])} lb-ft', re.sub(r'^lb-?ft[ ,;]*', '', v['tq'].get('note') or ''))
    if zv:
        z = v['z60']; extra = f'Maker: {z["claim"]:.1f} s' if z.get('v') is not None and z.get('claim') is not None else ''
        R(*(z.get('src') or [])); R(*(z.get('csrc') or []))
        row('0–60 mph', zv, ' · '.join(x for x in (zl, extra) if x))
    for k, lbl in (('top', 'Top speed'), ('trans', 'Gearbox'), ('weight', 'Weight'), ('price', 'Package price' if v.get('pkg') else 'Price new')):
        if v.get(k) and v[k].get('v') not in (None, ''): R(*v[k].get('src', [])); row(lbl, E(v[k]['v']), v[k].get('note'))
    what = f'<p class="pf-what">{E(v["what"])}</p>' if v.get('what') else ''
    R(*v.get('what_src', []))
    cls = 'pf-v' + (' pf-star' if star else '') + (' pf-pkg' if v.get('pkg') else '')
    big = (f'<p class="pf-hp"><b>{E(hp["v"])}</b> hp' + (f'<small>{E(hp["note"])}</small>' if hp.get('note') else '') + '</p>') if hp.get('v') is not None else ''
    return (f'<article class="{cls}"><header><h4>{E(v["name"])}</h4><span>{E(v["years"])}</span></header>{big}'
            f'{what}<dl>{"".join(rows)}</dl>{R.close()}</article>')

_PERF = None
PERF_ALIAS = {'mercedes-amg-c63': 'amg-c63', 'audi-rs-5': 'audi-rs5', 'alfa-romeo-giulia-quadrifoglio': 'giulia-qv'}   # chip slug -> performance id
def perf_list():
    global _PERF
    if _PERF is None:
        d = _load('data/perf_cars.json', []) or []
        _PERF = {c['slug']: c for c in (d.get('cars', []) if isinstance(d, dict) else d)}
    return _PERF
def perf_url(slug, out='docs'):
    """the page a performance car lives at once it has one ('' = coming soon)"""
    D = _load(f'data/perf/{slug}.json')
    if D and D.get('page'): return D['page']
    for u in (f'/cars/{slug}/', f'/performance/{slug}/', f'/supercars/{slug}/'):
        if os.path.exists(os.path.join(HERE, out, u.strip('/'), 'index.html')): return u
    return ''

# ---- 11-12 (UX test, Tyler: "the G80 tab shows 2008 data"): the Years, Problems, Recalls and Specs tabs follow the generation picker.
# Year-specific rows carry data-pfy="<years>"; perf.js hides (class pf-off) the ones outside the picked generation, and a note on each tab
# says which years show, with a "Show every year" button. Without JS every year shows.
def _gy1(G, g):
    """the last model year a generation covers for the filter (the newest one stays open: next year's cars belong to it)"""
    return max(g['y1'], 2030) if g is G[-1] and (g.get('years') or '').rstrip().endswith(('–', '-')) or g is G[-1] else g['y1']
def _years_in(t):
    ys = set()
    for a, b in re.findall(r'\b((?:19|20)\d\d)(?:\s*[–-]\s*((?:19|20)?\d\d))?\b', t or ''):
        a = int(a); b = int(b) if b and len(b) == 4 else (a // 100 * 100 + int(b) if b else a)
        ys.update(range(a, b + 1) if a <= b <= a + 20 else [a])
    return sorted(ys)
# 11-12 round 2 (Devin: a 2008-14 recall on the 2015-21 STI, a 2018 Mustang video among the S650's most-watched, an "oil consumption
# (2018-2020)" card counting 2024+ complaints): an engine issue whose title (or a year range in its text) names model years outside the
# generation, and a video whose title names other years, stay off that generation
def _gen_ok(ys, g, y1):
    return not ys or any(g['y0'] <= y <= y1 for y in ys)
def issue_in_gen(i, g, y1):
    ys = _years_in(i.get('t'))
    if not ys:
        ys = set()
        for a, b in re.findall(r'\b((?:19|20)\d\d)\s*[–-]\s*((?:19|20)?\d\d)\b', i.get('x') or ''): ys.update(_years_in(f'{a}–{b}'))
    return _gen_ok(sorted(ys), g, y1)
def video_in_gen(title, g, y1):
    ys = [y for y in _years_in(title) if 1980 <= y <= 2030]
    return not ys or sum(g['y0'] <= y <= y1 for y in ys) * 2 >= len(ys)
YF_NOTE = ('<p class="pf-yf"><span class="pf-yft">Showing the <b class="pf-yfg"></b> years only (<span class="pf-yfr"></span>).</span><span class="pf-yfx">Showing every year.</span> '
           '<button type="button" class="pf-yall" aria-pressed="false">Show every year</button></p>')
def _gen_parts(D, A, label):
    """one 'what owners complain about' table per generation (NHTSA complaints in its model years), tagged for the filter"""
    out = ''
    for g in D['gens']:
        ga = ((A.get('nhtsa') or {}).get('gens') or {}).get(g['id']) or {}; n = ga.get('n') or 0; parts = [p for p in ga.get('parts') or [] if not p[0].lower().startswith('unknown')]
        ys = ' '.join(str(y) for y in range(g['y0'], _gy1(D['gens'], g) + 1))
        if not n:
            out += f'<section class="yc" data-pfy="{ys}"><h2>What {E(g["code"])} {E(label)} owners complain about</h2><p class="pf-none">No owner complaints on file for {E(g["years"])}.</p></section>'
            continue
        rows = ''.join(f'<tr><td>{E(k)}</td><td>{round(100 * v / n)}%</td><td>{v:,}</td></tr>' for k, v in parts[:6])
        out += (f'<section class="yc" data-pfy="{ys}"><h2>What {E(g["code"])} {E(label)} owners complain about</h2>'
                f'<p>{n:,} owner complaint{"" if n == 1 else "s"} to NHTSA for model years {E(g["years"])}. A complaint can name more than one system.</p>'
                f'<div class="tw"><table class="adv"><thead><tr><th>System</th><th>Share of complaints</th><th>Complaints</th></tr></thead><tbody>{rows}</tbody></table></div></section>')
    return out

def build(slug, out='docs'):
    """everything both modes share: hero (slider or single image + big numbers), one block per generation, compare, the sources"""
    D = _load(f'data/perf/{slug}.json'); A = _load(f'data/perf/{slug}.auto.json', {}) or {}
    if not D: return None
    try:   # fresh YouTube topics for studies that weren't pulled when data_perf.py last ran (pulls land between builds)
        import data_perf as DP
        if os.path.isdir(DP.YT):
            A.setdefault('yt', {})
            for st in DP.studies(D):
                if not A['yt'].get(st): A['yt'][st] = DP.yt_study(st, D.get('topics_extra'), DP.hp_cap(D))
    except Exception: pass
    BYT = _load('data/bmw_engine_yt.json', {}) or {}
    SCY = {**(A.get('scores') or {}), **(_load('data/supercar_engine_yt.json', {}) or {})}   # the snapshot data_perf.py took, the live file wins
    YS = (_load('data/yt_scores.json', {}) or {}).get(D.get('yt_model') or '', {}) or (SCY.get(D.get('yt_study') or '') or {}).get('years') or {}
    BPH = _load('data/bmw_engine_photos.json', {}) or {}; SCP = _load('data/supercar_engine_photos.json', {}) or {}
    R = Refs(D['sources']); short = D['short']; G = D['gens']
    focus = next((i for i, g in enumerate(G) if g['id'] == D.get('focus')), len(G) - 1)
    gsc = {g['id']: _avg(YS, g['y0'], g['y1']) for g in G}
    granked = sorted([g['id'] for g in G if gsc[g['id']][0] is not None], key=lambda i: -gsc[i][0])
    def eng_score(code):
        # 11-12: the engine's tone over ALL its scored years (engine_tone), the same number its engine page shows
        return engine_tone(D['engines'][code], A)
    esc = {c: eng_score(c) for c in D['engines']}
    eranked = sorted([c for c in esc if esc[c][0] is not None], key=lambda c: -esc[c][0])
    def lead(g):
        vs = g['variants']
        return next((v for v in vs if v['id'] == D.get('star')), next((v for v in vs if v.get('star')), next((v for v in vs if not v.get('pkg') and _hp(v)), vs[0])))
    # ---- hero
    pills = len(G) > 1
    stops = ''.join(f'<button type="button" class="pf-stop" data-i="{i}" data-y0="{g["y0"]}" data-y1="{_gy1(G, g)}" aria-pressed="{"true" if i == focus else "false"}"><b>{E(g["code"])}</b><span>{E(g["years"])}</span></button>' for i, g in enumerate(G))
    multi = all(g.get('img') for g in G) and len(G) > 1
    if multi:
        imgs = ''.join(f'<img src="{E(g["img"])}" alt="{E(D["name"])} {E(g["code"])} ({E(g["years"])})' + (f' in {E(g["color"])}' if g.get('color') else '') + ', AI illustration" width="1000" height="600" '
                       f'class="pf-car{" on" if i == focus else ""}" data-i="{i}" decoding="async"{"" if i == focus else " loading=" + chr(34) + "lazy" + chr(34)}>' for i, g in enumerate(G))
    else:
        pc = perf_list().get(slug) or {}
        src = D.get('img') or (G[focus].get('img') if G[focus].get('img') else pc.get('img')) or ''
        # 11-12 (UX test: the C63's W206 tab showed a W204): one picture for every generation says which generation it shows, and perf.js
        # shows that line whenever another generation is picked
        pg = next((i for i, g in enumerate(G) if pc.get('img_year') and g['y0'] <= pc['img_year'] <= g['y1']), None) if (not D.get('img') or D['img'].split('?')[0] == (pc.get('img') or '').split('?')[0]) else None
        imgs = (f'<img src="{E(src)}" alt="{E(D["name"])}' + (f' {E(G[pg]["code"])}' if pg is not None and pills else '') + (f' in {E(pc["img_color"])}' if pc.get('img_color') else '')
                + f', AI illustration" width="{pc.get("w", 1000)}" height="{pc.get("h", 600)}" class="pf-car on pf-one" decoding="async" fetchpriority="high"'
                + (f' data-pg="{pg}"' if pg is not None and pills else '') + '>') if src else ''
        if src and pg is not None and pills:
            imgs += f'<p class="pf-pic">Pictured: the {E(G[pg]["code"])} {E(short)} ({pc["img_year"]}). <span class="pf-picn"></span></p>'
    def stats(g):
        v = lead(g); zv, zl, zt = z_fallback(g, v); top = ((v.get('top') or {}).get('v') or '')
        s = [(str(_hp(v) if _hp(v) is not None else '–'), 'horsepower'), (zv.replace(' s', '') if zv else '–', '0–60 mph, sec' + (f' ({zt})' if zt else '')), (top.replace(' mph', '') or '–', 'mph top speed')]
        if s[2][0] == '–' and s[1][0] != '–': s = s[:2]   # 11-12 round 2: no empty "top speed" tile when we have no figure
        return (f'<div class="pf-stats{" on" if g is G[focus] else ""}" data-g="{g["id"]}"><p class="pf-sl">{E(v["name"])} <span>{E(g["code"])} · {E(v["years"])}</span></p>'
                + ''.join(f'<div class="pf-st"><b>{E(a)}</b><span>{E(b)}</span></div>' for a, b in s) + (f'<p class="pf-tag">{E(g["tag"])}</p>' if g.get('tag') else '') + '</div>')
    info = ('<button class="ii" type="button" aria-label="Image info" aria-expanded="false" aria-controls="pf-ii">i</button><div class="ii-pop" id="pf-ii" role="note" hidden>'
            + ('AI illustrations (one per generation)' if multi else 'AI illustration') + ', not photos of a specific car. Free to use under '
            '<a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener license">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a></div>')
    slider = (f'<div class="pf-gens{"" if multi else " pf-single"}" data-focus="{focus}">' + (f'<div class="pf-stage">{imgs}{info}</div>' if imgs else '')
              + (f'<div class="pf-track" role="group" aria-label="{E(short)} generation" style="--n:{len(G)}">{stops}</div>' if pills else '')
              + f'{"".join(stats(g) for g in G)}</div>')
    # ---- one block per generation: performance, engine, YouTube, buy
    nh = (A.get('nhtsa') or {}); rc = A.get('recalls') or {}; yt = A.get('yt') or {}
    blocks = []
    for gi, g in enumerate(G):
        eng = D['engines'][g['engine']]; ga = (nh.get('gens') or {}).get(g['id'], {})
        cards = ''.join(variant_card(v, R, v['id'] == D.get('star') or bool(v.get('star'))) for v in g['variants'])
        perf = (f'<section class="pf-sec"><h2>{ic("bolt")} How fast is the {E(g["code"])} {E(short)}?</h2>' if pills else f'<section class="pf-sec"><h2>{ic("bolt")} How fast is the {E(short)}?</h2>') + (
                f'<p class="pf-dek">{E(g.get("body") or "")}{", " if g.get("body") else ""}{E(g["years"])}. 0–60 times are magazine tests where we have one, otherwise the maker&#39;s figure.</p>'
                f'<div class="pf-vs">{cards}</div></section>')
        # engine
        R.open()
        sc, _ = esc[g['engine']]
        rk = (eranked.index(g['engine']) + 1) if g['engine'] in eranked else None
        eph = (eng.get('photo') or BPH.get(g['engine']) or SCP.get(eng.get('study') or '') or {})
        eimg = (f'<img src="{E(eph["src"])}" alt="{E(eng["name"])} engine, ' + ('AI illustration' if eph.get('ai') or not eph.get('page') else 'photo') + f'" width="{eph["w"]}" height="{eph["h"]}" loading="lazy" decoding="async">' if eph else '')
        if eph and eph.get('page') and not eph.get('ai'):   # 11-12: a real Commons photo (the S55/S58) carries its credit
            eimg += f'<p class="pf-cap">Photo: {E(eph.get("author", ""))} / <a href="{E(eph["page"])}" rel="noopener nofollow">Wikimedia Commons</a> ({E(eph.get("license", ""))})</p>'
        facts = ''.join(f'<div class="pf-f"><span>{E(k)}</span><b>{E(v)}</b></div>' for k, v, s in eng['facts'] if R(*s) == '')
        ytl = (f'<p class="pf-eyt">{ic("play", 16)}<span>Engine&#39;s YouTube owner tone <b>{sc}</b>/100' + (f' · #{rk} of {len(eranked)} {E(short)} engines' if rk and len(eranked) > 1 else '') + f' <small>(videos about the {E(eng["name"])} in every car that uses it, so it differs from this car&#39;s own tone below)</small></span></p>'
               if sc is not None else (f'<p class="pf-eyt na">{ic("play", 16)}<span>YouTube owner tone for the {E(eng["name"])}: its study is queued; the score shows here when it lands.</span></p>' if eng.get('study') else ''))
        iss = []; gy1 = _gy1(G, g); gis = [i for i in eng['issues'] if issue_in_gen(i, g, gy1)]
        for i in gis:
            R(*i.get('src', []))
            cnt = (ga.get('issues') or {}).get(i['t'])
            nline = (f'<span class="pf-n">{cnt["n"]} owner complaint{"" if cnt["n"] == 1 else "s"} to NHTSA mention{"s" if cnt["n"] == 1 else ""} it ({E(g["years"])})</span>' if cnt and cnt['n'] else '')
            iss.append(f'<li><div><b>{E(i["t"])}</b><span class="pf-k">{E(i["kind"])}</span></div><p>{E(i["x"])}</p>'
                       + (f'<p class="pf-fix">Fix: {E(i["fix"])}</p>' if i.get('fix') else '') + nline + '</li>')
        epage = next((u for u in (eng.get('page'), '/engines/performance/', '/engines/supercars/') if u and os.path.exists(os.path.join(HERE, out, u.strip('/'), 'index.html'))), '')
        elink = (f'<a class="pf-go" href="{E(epage)}">' + (f'{E(eng["name"])} engine page →' if epage == eng.get('page') else 'Performance engines →') + '</a>') if epage else ''
        # 11-12 round 2 (UX test, Devin): the engine page counts fewer complaints and recalls than this page; say why, with both numbers
        rcn = ''
        scx = sce_counts(eng.get('page'), g['y0'], min(g['y1'], 2026)) if eng.get('page') else None
        if scx and epage == eng.get('page'):
            n_car = ga.get('n') or 0; r_car = len({r['id'] for y in range(g['y0'], g['y1'] + 1) for r in (A.get('recalls') or {}).get(str(y), [])})
            if (scx['n'], scx['rec']) != (n_car, r_car):
                mdl = E(((D.get('nhtsa') or {}).get('models') or [''])[0].title())
                rcn = (f'<p class="pf-cap">Why the <a href="{E(epage)}">engine page</a> shows fewer: it counts only the {scx["n"]:,} owner complaint{"" if scx["n"] == 1 else "s"} and {scx["rec"]} recall{"" if scx["rec"] == 1 else "s"} '
                       f'for {E(g["years"])} that name this engine or a version that only had it. This page counts all {n_car:,} complaints and {r_car} recall campaigns NHTSA files under &quot;{mdl}&quot; for those years, other engines included.</p>')
        engine = (f'<section class="pf-sec"><h2>{ic("eng")} The engine: {E(eng["name"])}</h2><div class="pf-eng' + ('' if eimg else ' pf-noimg') + '">' + (f'<div class="pf-ei">{eimg}</div>' if eimg else '') + '<div class="pf-ef">'
                  f'<p class="pf-ew">{E(eng["what"])}</p><div class="pf-fs">{facts}</div>{ytl}{elink}{rcn}</div></div>'
                  + (f'<h3 class="pf-h3">Known issues</h3><ul class="pf-iss">{"".join(iss)}</ul>' if iss else '') + f'{R.close("Engine sources")}</section>')
        # YouTube
        gs, _ = gsc[g['id']]; grk = granked.index(g['id']) + 1 if g['id'] in granked else None
        st = yt.get(g.get('yt_study') or D.get('yt_study') or '') or {}
        comp_sc = _avg((SCY.get(g.get('comp_study')) or {}).get('years'), g['y0'], g['y1'])[0] if g.get('comp_study') else None
        def bars(rows, cls):
            if not rows: return '<p class="pf-none">Nothing stands out.</p>'
            mx = max(p for _, p in rows) or 1
            return ''.join(f'<div class="pf-b {cls}"><span>{E(k)}</span><i style="--w:{round(100 * p / mx)}%"></i><b>{p}%</b></div>' for k, p in rows)
        vids = ''.join(f'<a class="pf-vid" href="https://www.youtube.com/watch?v={E(v["id"])}" rel="noopener nofollow" target="_blank">'
                       f'<img src="https://i.ytimg.com/vi/{E(v["id"])}/mqdefault.jpg" alt="" width="320" height="180" loading="lazy" decoding="async">'
                       f'<span>{E(v["title"])}</span><small>{E(v["ch"])} · {_views(v["views"])}</small></a>' for v in [v for v in (st.get('top') or []) if video_in_gen(v.get('title'), g, _gy1(G, g))][:3])
        comp_line = ''
        if g.get('comp_study'):
            cl = E(g.get('comp_label') or 'Competition')
            comp_line = (f'<div class="pf-yb"><b>{comp_sc}</b><span>{cl} videos only</span></div>' if comp_sc is not None else
                         f'<div class="pf-yb na"><b>…</b><span>{cl} study scoring now</span></div>')
        who = (g['code'] + ' ' + short) if pills else short
        if gs is None and not st:
            ytsec = (f'<section class="pf-sec"><h2>{ic("play")} What owners say on YouTube</h2><p class="pf-none">The {E(short)} YouTube study is queued: the 200 most-watched '
                     f'videos, their tone and what owners praise and complain about show here when it lands.</p></section>')
        else:
            ytsec = (f'<section class="pf-sec"><h2>{ic("play")} What owners say on YouTube</h2><div class="pf-ys">'
                     + (f'<div class="pf-yb big"><b>{gs}</b><span>This car&#39;s YouTube owner tone, out of 100' + (f' · #{grk} of {len(granked)} generations' if grk and len(granked) > 1 else '') + ' · videos about this generation only (the engine&#39;s tone above covers every car with that engine)</span></div>' if gs is not None else '<div class="pf-yb na"><b>–</b><span>Not enough videos for a score</span></div>')
                     + comp_line + '</div>'
                     + (f'<div class="pf-pc"><div><h3>Owners praise</h3>{bars(st.get("praise"), "pf-gd")}</div><div><h3>Owners complain about</h3>{bars(st.get("trouble"), "pf-bd")}</div></div>'
                        f'<p class="pf-cap">Share of the {st.get("videos", 0)} most-watched {E(who)} videos that praise or criticize each topic (a praise or trouble word near it in the title or transcript).</p>' if st else '')
                     + (f'<h3 class="pf-h3">Most-watched videos</h3><div class="pf-vids">{vids}</div>' if vids else '') + '</section>')
        # should you buy one
        R.open()
        yrs = range(g['y0'], g['y1'] + 1); by = {int(y): n for y, n in (nh.get('by_year') or {}).items() if int(y) in yrs}
        ytb = {int(y): v['score'] for y, v in YS.items() if int(y) in yrs and v and v.get('score') is not None}
        buy = []
        lv = lead(g)
        if lv.get('price'): R(*lv['price'].get('src', [])); buy.append(('buy', f'New, the {E(lv["name"])} cost {E(lv["price"]["v"])}' + (f' ({E(lv["price"]["note"])})' if lv["price"].get("note") else '') + '.'))
        if len(set(ytb.values())) > 1:
            b = max(ytb, key=lambda y: (ytb[y], y)); buy.append(('buy', f'YouTube likes the <b>{b}</b> best ({ytb[b]}/100).'))
        filed = (nh.get('note') or D.get('nhtsa', {}).get('note') or '')
        if len(by) >= 2:
            hi_ = max(by, key=by.get); lo_ = min(by, key=by.get)
            if by[hi_] >= 10: buy.append(('info', f'Most owner complaints: the <b>{hi_}</b> ({by[hi_]}). Fewest: the {lo_} ({by[lo_]}). Raw counts, not per car sold' + (', for every version NHTSA files under this name.' if filed else '.')))
            elif not filed: buy.append(('buy', f'Few owner complaints so far: {sum(by.values())} to NHTSA for {g["y0"]}–{g["y1"]}.'))
        big = [i for i in gis if i.get('rx') and (((ga.get('issues') or {}).get(i['t']) or {}).get('n') or re.search(r'bulletin|recall|service action|warranty', i['kind'], re.I))]
        for i in big[:2]:
            n_i = ((ga.get('issues') or {}).get(i['t']) or {}).get('n')
            if n_i: buy.append(('warn', f'Budget for <b>{E(i["t"].lower())}</b>: {n_i} owner complaint{"" if n_i == 1 else "s"} mention{"s" if n_i == 1 else ""} it.' + (f' {E(i["fix"])}' if i.get('fix') else '')))
            else: buy.append(('warn', ('Recall' if re.search('recall', i['kind'], re.I) else 'Maker fix') + f': <b>{E(i["t"])}</b>.' + (f' {E(i["fix"])}' if i.get('fix') else '')))
        nrec = len({r['id'] for y in yrs for r in rc.get(str(y), [])})
        if nrec: buy.append(('warn', f'{nrec} recall campaign{"" if nrec == 1 else "s"} across {g["y0"]}–{g["y1"]}' + (' (all ' + E(D["nhtsa"]["models"][0].title()) + ' versions)' if filed else '') + '. <a href="/vin/">Check a VIN</a> before you buy.'))
        buy.append(('info', f'Repair costs: we don&#39;t have owner-reported repair costs for the {E(short)} yet.'))
        buysec = (f'<section class="pf-sec"><h2>{ic("buy")} Should you buy ' + (f'a {E(g["code"])} {E(short)}' if pills else f'a {E(short)}') + '?</h2><ul class="pf-buy">'
                  + ''.join(f'<li class="pf-l-{k}">{ic(k, 18)}<span>{t}</span></li>' for k, t in buy) + f'</ul>{R.close()}</section>')
        blocks.append(f'<div class="pf-g{" on" if gi == focus else ""}" data-g="{g["id"]}" data-i="{gi}"><p class="pf-gh">{E(g["code"])} {E(short)} · {E(g["years"])}</p>{perf}{engine}{ytsec}{buysec}</div>')
    # ---- compare chips (a rival's page once it has one, else "coming soon")
    PL = perf_list(); chips = ''
    for c in D.get('compare', []):
        u = None; cs = PERF_ALIAS.get(c['slug'], c['slug'])   # 11-12: the M3 file's chip slugs name the cars differently (mercedes-amg-c63 = amg-c63)
        for x in (f'/compare/{slug}-vs-{cs}/', f'/compare/{cs}-vs-{slug}/'):
            if os.path.exists(os.path.join(HERE, out, x.strip('/'), 'index.html')): u = x; break
        u = u or perf_url(cs, out) or None
        img = c.get('img') or (PL.get(cs) or {}).get('img') or ''
        chips += ((f'<a class="pf-c" href="{E(u)}">' if u else '<div class="pf-c soon">') + (f'<img src="{E(img)}" alt="" width="1000" height="600" loading="lazy" decoding="async">' if img else '')
                  + f'<span>{E(short)} vs {E(c["name"])}</span><small>{"See it →" if u else "Coming soon"}</small>' + ('</a>' if u else '</div>'))
    cmp_sec = f'<section class="pf-sec"><h2>{ic("vs")} Compare the {E(short)}</h2><div class="pf-cmp">{chips}</div></section>' if chips else ''
    return dict(D=D, A=A, slider=slider, blocks=''.join(blocks), cmp=cmp_sec, R=R, esc=esc, G=G, focus=focus, lead=lead, YS=YS)

def _star(D):
    g = next(x for x in D['gens'] if x['id'] == D.get('focus')) if any(x['id'] == D.get('focus') for x in D['gens']) else D['gens'][-1]
    v = next((x for x in g['variants'] if x['id'] == D.get('star')), next((x for x in g['variants'] if x.get('star')), g['variants'][0]))
    return g, v

def _qa(D, P):
    """3 short answers from the same data (also the FAQPage schema on standalone pages)"""
    g, v = _star(D); zv, zl = _z(v.get('z60')); out = []
    if _hp(v) is not None:
        a = f'The {g["code"]} {v["name"]} makes {_hp(v)} hp' + (f' and {v["tq"]["v"]} lb-ft' if v.get('tq') else '') + '.'
        if zv: a += f' {zl.replace(" test", "") if "test" in zl else "The maker"} {"measured" if "test" in zl else "quotes"} 0–60 mph in {zv.replace(" s", " seconds")}.'
        if v.get('top'): a += f' Top speed: {v["top"]["v"]}' + (f' ({v["top"]["note"]})' if v['top'].get('note') else '') + '.'
        out.append((f'How fast is the {D["make"]} {v["name"]}?' if not v['name'].startswith(D['make']) else f'How fast is the {v["name"]}?', a))
    eng = D['engines'][g['engine']]
    out.append((f'What engine does the {D["name"]} have?', f'The {g["code"]} {D["short"]} ({g["years"]}) uses the {eng["name"]}, a {eng["what"]}.'
                + (' Older generations: ' + '; '.join(f'{x["code"]}: {D["engines"][x["engine"]]["name"]}' for x in D['gens'] if x is not g) + '.' if len(D['gens']) > 1 else '')))
    sc = [(c, P['esc'][c][0]) for c in D['engines'] if P['esc'][c][0] is not None]
    if len(sc) >= 2: out.append((f'Which {D["name"]} engine do YouTube owners like most?', ', '.join(f'{D["engines"][c]["name"]} {s}/100' for c, s in sorted(sc, key=lambda x: -x[1]))
                                 + '. That&#39;s the tone of the most-watched videos about each engine, praise words against trouble words.'))
    return out

def inject(slug, out='docs'):
    """mode 1: the car already has a model page (BMW M3)"""
    P = build(slug, out)
    if not P: return False
    D, R = P['D'], P['R']
    page = os.path.join(HERE, out, D['page'].strip('/'), 'index.html')
    if not os.path.exists(page): return False
    s = BeautifulSoup(open(page, encoding='utf-8').read(), 'html.parser')
    if s.find(class_='pf-gens'): return False   # already done (a page that wasn't rebuilt this run)
    hero = s.find('section', class_='tb-hero'); ov = s.find('section', id='p-overview')
    if not hero or not ov: return False
    short = D['short']
    for t in hero.find_all(class_=['tb-img', 'tb-ans', 'yhero']): t.decompose()
    h1 = hero.find('h1'); h1.string = D['h1']
    h1.insert_after(BeautifulSoup(P['slider'], 'html.parser'))
    hero['class'] = hero.get('class', []) + ['pf-hero']
    old = ''.join(str(c) for c in ov.contents)
    no_li = (f'<p class="pf-li">{ic("shield", 18)}<span>No Lemon Index for the {E(short)}: the index is complaints per car sold, and we don&#39;t have U.S. sales by year for it. '
             f'The counts below are raw owner complaints to NHTSA.</span></p>')
    rel = f'<section class="pf-sec pf-rel"><h2>{ic("shield")} Reliability</h2>{no_li}{old}</section>'
    ov.clear(); ov.append(BeautifulSoup(f'<div class="pf">{P["blocks"]}{rel}{P["cmp"]}<details class="pf-sd" id="pf-sources"><summary>All sources ({len(R.order)})</summary>{R.html()}</details></div>', 'html.parser'))
    qa = s.find('section', class_='yqa')
    if qa: qa.append(BeautifulSoup(''.join(f'<h3>{E(q)}</h3><p>{a}</p>' for q, a in _qa(D, P)), 'html.parser'))
    if len(D['gens']) > 1:   # 11-12: the other tabs follow the generation picker (see _gy1)
        def tag(el, ys):
            if ys: el['data-pfy'] = ' '.join(str(y) for y in ys)
        yp = s.find('section', id='p-years')
        if yp:
            for tr in yp.find_all('tr'):
                td = tr.find('td')
                if td: tag(tr, _years_in(td.get_text(' ')))
        rp = s.find('section', id='p-recalls')
        if rp:
            for li in rp.find_all('li'):
                sm = li.find('small')
                if sm and '·' in sm.get_text(): tag(li, _years_in(sm.get_text().split('·', 1)[1]))
        sp = s.find('section', id='p-specs')
        if sp:
            for dd in sp.find_all('details', class_='yd'):
                sm = dd.find('summary')
                if sm: tag(dd, _years_in(sm.get_text().split('·')[0]))
        pp = s.find('section', id='p-problems')
        if pp:   # one table per generation first; the every-year numbers stay, folded and labeled
            whole = ''.join(str(c) for c in pp.contents); yall = f'{D["gens"][0]["y0"]}–{D["gens"][-1]["years"].split("–")[-1] or "now"}'
            pp.clear(); pp.append(BeautifulSoup(_gen_parts(D, P['A'], short)
                                                + f'<details class="yd pf-allyrs"><summary>Every {E(short)} year combined ({E(yall)})</summary>{whole}</details>', 'html.parser'))
        for sid in ('p-years', 'p-problems', 'p-recalls', 'p-specs'):
            sec = s.find('section', id=sid)
            if sec: sec.insert(0, BeautifulSoup(YF_NOTE, 'html.parser'))
    g, v = _star(D)
    t = s.find('title'); t.string = f'{D["name"]} & {v["name"]}: 0-60, Horsepower, Engines, Problems'
    desc = (f'{D["name"]} performance by generation: the {g["code"]} {v["name"]} makes {_hp(v)} hp and runs 0-60 in {_z(v.get("z60"))[0]}. '
            f'Engines, known issues, YouTube owner verdicts and recalls, every number sourced.')
    for m in s.find_all('meta'):
        if m.get('name') == 'description' or m.get('property') in ('og:description',) or m.get('name') == 'twitter:description': m['content'] = desc
        if m.get('property') == 'og:title' or m.get('name') == 'twitter:title': m['content'] = t.string
    ld = f'<script type="application/ld+json">{json.dumps(R.ld(BASE + D["page"], t.string), ensure_ascii=False)}</script>'
    s.head.append(BeautifulSoup(ASSET + ld + ('' if s.find('script', src=re.compile('imginfo')) else '<script src="/assets/imginfo.js?v=2" defer></script>'), 'html.parser'))
    open(page, 'w', encoding='utf-8').write(str(s))
    return True

def standalone(slug, page_fn, out='docs'):
    """mode 2: a page of its own, through build.py's page() (header, footer, schema, dates)"""
    P = build(slug, out)
    if not P: return None
    import tabbed as TAB
    D, A, R = P['D'], P['A'], P['R']; short = D['short']; G = D['gens']; nh = A.get('nhtsa') or {}; rc = A.get('recalls') or {}
    pc = perf_list().get(slug) or {}
    mk = D['make']; mslug = re.sub(r'[^a-z0-9]+', '-', mk.lower()).strip('-')
    crumbs = (f'<p class="ph-e"><a href="/?type=performance">Performance cars</a>'
              + (f' · <a href="/brands/{mslug}/">{E(mk)}</a>' if os.path.exists(os.path.join(HERE, out, 'brands', mslug, 'index.html')) else '') + '</p>')
    hero = f'<section class="ph tb-hero pf-hero">{crumbs}<h1>{E(D["h1"])}</h1>{P["slider"]}{PARENT_ROW(slug, D)}</section>'
    # Problems & recalls (secondary, honest about what NHTSA's model names cover)
    note = (D.get('nhtsa') or {}).get('note') or ''
    y0, y1 = min(g['y0'] for g in G), max(g['y1'] for g in G)
    by = {int(y): n for y, n in (nh.get('by_year') or {}).items() if y0 <= int(y) <= y1 and any(g['y0'] <= int(y) <= g['y1'] for g in G)}
    tot = sum(by.values()); mx = max(by.values() or [1]) or 1
    multi = len(G) > 1   # 11-12: rows carry their years so the generation picker filters this tab (perf.js)
    bars = ''.join(f'<div class="pf-yr"' + (f' data-pfy="{y}"' if multi else '') + f'><span>{y}</span><i style="--w:{round(100 * n / mx)}%"></i><b>{n}</b></div>' for y, n in sorted(by.items()))
    def _pbars(parts):
        return ''.join(f'<div class="pf-b pf-bd"><span>{E(k)}</span><i style="--w:{round(100 * n / max(1, parts[0][1]))}%"></i><b>{n}</b></div>' for k, n in parts) if parts else ''
    parts = (nh.get('parts') or [])[:5]
    parts_h = _pbars(parts)
    gp = {g['id']: (lambda ps: None if ps is None else [p for p in ps if not p[0].lower().startswith('unknown')])(((nh.get('gens') or {}).get(g['id']) or {}).get('parts')) for g in G}
    if multi and all(v is not None for v in gp.values()):   # one "what they're about" per generation
        parts_h = ''.join(f'<div class="pf-gp" data-pfy="{" ".join(str(y) for y in range(g["y0"], _gy1(G, g) + 1))}"><p class="pf-cap">{E(g["code"])} · {E(g["years"])}</p>'
                          + (_pbars(gp[g['id']][:5]) or '<p class="pf-none">No owner complaints on file.</p>') + '</div>' for g in G)
    recs = []
    for g in G:
        seen = {}
        for y in range(g['y0'], g['y1'] + 1):
            for r in rc.get(str(y), []): seen.setdefault(r['id'], (r, []))[1].append(y)
        for rid, (r, ys) in seen.items():
            first = re.split(r'(?<=[.])\s', r['summary'])[0][:260]
            recs.append(f'<li' + (f' data-pfy="{" ".join(map(str, ys))}"' if multi else '') + f'><b>{E(rid)}</b> <span class="pf-k">{E(r["part"].split(":")[0].title() or "Recall")}</span><span class="pf-ry">{ys[0]}' + (f'–{ys[-1]}' if len(ys) > 1 else '') + f'</span><p>{E(first)}</p></li>')
    rel = ((YF_NOTE if multi else '') + f'<section class="pf-sec"><h2>{ic("shield")} Owner complaints to NHTSA</h2>'
           + (f'<p class="pf-li">{ic("info", 18)}<span>{E(note)}</span></p>' if note else '')
           + f'<p class="pf-li">{ic("shield", 18)}<span>No Lemon Index for the {E(short)}: the index is complaints per car sold, and sales by trim aren&#39;t published. These are raw counts.</span></p>'
           + ((''.join(f'<p class="pf-dek" data-pfy="{" ".join(str(y) for y in range(g["y0"], _gy1(G, g) + 1))}">{E(g["code"])}: {sum(n for y, n in by.items() if g["y0"] <= y <= g["y1"]):,} complaints for {E(g["years"])}.</p>' for g in G) if multi
                else f'<p class="pf-dek">{tot:,} complaint{"" if tot == 1 else "s"} for {y0}–{y1}.</p>') + f'<div class="pf-yrs">{bars}</div>' if by else '<p class="pf-none">No owner complaints on file for these years.</p>')
           + (f'<h3 class="pf-h3">What they&#39;re about</h3><div class="pf-parts">{parts_h}</div>' if parts_h else '') + '</section>'
           + f'<section class="pf-sec"><h2>{ic("warn")} Recalls</h2>' + (f'<ul class="pf-recs">{"".join(recs)}</ul>' if recs else '<p class="pf-none">No recalls on file for these years.</p>')
           + f'<p class="pf-cap">Source: NHTSA (api.nhtsa.gov). <a href="/vin/">Check a VIN</a> for open recalls on one car.</p></section>')
    qa = _qa(D, P)
    qh = '<section class="pf-sec yqa"><h2>Quick answers</h2>' + ''.join(f'<h3>{E(q)}</h3><p>{a}</p>' for q, a in qa) + '</section>'
    over = f'<div class="pf">{P["blocks"]}{P["cmp"]}<details class="pf-sd" id="pf-sources"><summary>All sources ({len(R.order)})</summary>{R.html()}</details></div>'
    tabs = TAB._tabs([('overview', 'Overview', over), ('problems', 'Problems & recalls', f'<div class="pf">{rel}</div>'), ('questions', 'Questions', f'<div class="pf">{qh}</div>')], f'{short} sections')
    body = f'{TAB.ASSET}{ASSET}<script src="/assets/imginfo.js?v=2" defer></script><div class="advp tbl pfp">{hero}{tabs}</div>'
    g, v = _star(D)
    title = f'{D["name"]}: 0-60, Horsepower, Engine, Problems'
    zv = _z(v.get('z60'))[0]
    desc = (f'{D["name"]}: the {v["name"]} makes {_hp(v)} hp' + (f' and runs 0-60 in {zv}' if zv else '') + '. Engines, known issues, YouTube owner verdicts, complaints and recalls, every number sourced.')
    url = BASE + D['page']
    ld = [R.ld(url, title), {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub('<[^>]+>', '', a).replace('&#39;', "'")}} for q, a in qa]}]
    page_fn(D['page'], title, desc, body, ld=ld, img=(pc.get('img') or '').split('?')[0] or None)
    return D['page']

PARENT_ROW = lambda slug, D: ''   # 11-13 N3: set by build.py's engine_uses.py (the regular model + its year pages + sibling versions)

def link_parent(slug, out='docs'):
    """11-12 round 2 (Devin: "the 3 Series page never mentions the M340i"; the WRX tile opened the Impreza): a performance version that has
    its own page gets one line at the top of its base model's Overview (data/perf/<slug>.json `parent`), with the featured trim's sourced hp
    and 0-60"""
    D = _load(f'data/perf/{slug}.json') or {}
    if not D.get('parent'): return False
    pg = os.path.join(HERE, out, D['parent'].strip('/'), 'index.html')
    if not os.path.exists(pg): return False
    s = BeautifulSoup(open(pg, encoding='utf-8').read(), 'html.parser'); ov = s.find('section', id='p-overview')
    if not ov or ov.find(class_='pf-par'): return False
    g, v = _star(D); zv, zl = _z(v.get('z60'))
    nums = ' and '.join(x for x in ((f'makes {_hp(v)} hp' if _hp(v) else ''), (f'runs 0–60 in {zv} ({zl})' if zv else '')) if x)
    who = v['name'] if v['name'].startswith(D['make']) else f'{D["make"]} {v["name"]}'
    ov.insert(0, BeautifulSoup(f'<p class="ovslim pf-par">Performance version: <a href="{E(D["page"])}">{E(D["name"])} →</a>'
                               + (f' The {E(g["code"])} {E(who)} {E(nums)}.' if nums else '') + '</p>', 'html.parser'))
    open(pg, 'w', encoding='utf-8').write(str(s))
    return True

def build_all(out='docs', page_fn=None):
    done, urls = [], []
    for p in sorted(glob.glob(os.path.join(HERE, 'data', 'perf', '*.json'))):
        slug = os.path.basename(p)[:-5]
        if slug.endswith('.auto'): continue
        try:
            D = _load(f'data/perf/{slug}.json')
            if D.get('mode') == 'inject' or (not page_fn and os.path.exists(os.path.join(HERE, out, D['page'].strip('/'), 'index.html'))):
                if inject(slug, out): done.append(slug)
            elif page_fn:
                u = standalone(slug, page_fn, out)
                if u: done.append(slug); urls.append(u)
        except Exception as e:
            import traceback; print('perf page failed', slug, repr(e)); traceback.print_exc()
    for slug in done:
        try: link_parent(slug, out)
        except Exception as e: print('perf parent link failed', slug, repr(e))
    print('perf pages:', done)
    return urls

if __name__ == '__main__':
    import sys; sys.stdout.reconfigure(encoding='utf-8'); build_all()
