# Performance-car page template (11-11, Elijah: "do first full performance + engine + yt pull for BMW M3 Comp so I can see how the layout
# looks, then we dupe for other super cars and performance cars"; memory lemon-performance-section: performance cars lead with performance
# and the engine, not the Lemon score).
#
# One template, data only per car:
#   data/perf/<slug>.json       hand-sourced: generations (years, image, engine), every variant's specs with source ids, engines (facts,
#                               known issues with sources and a regex for owner complaints), compare chips, the source list
#   data/perf/<slug>.auto.json  computed by data_perf.py: NHTSA complaints by year, issue mentions per generation, recalls, YouTube topics
#   live at build time          data/yt_scores.json (YouTube tone per model year), data/supercar_engine_yt.json + data/bmw_engine_yt.json
#                               (engine and trim studies from auto_gens.py); the YouTube topics re-read from the study folders when they
#                               exist on this PC, so the page fills in as pulls land (no tracked data file is written during a build)
# The car's existing model page (docs/cars/<slug>/index.html, built by build.py / bmw_pages.py and tabbed.py) keeps every tab; this
# replaces its hero with the generation slider and its Overview with the performance story, and adds two questions.
#
# To add a car: write data/perf/<slug>.json (copy bmw-m3.json's shape), add its YouTube studies to auto_gens (engine_studies*.py), run
# `py -X utf8 data_perf.py <slug>`, then build. build.py calls build_all(), which does every data/perf/*.json whose page exists.
import glob, html, json, os, re
from bs4 import BeautifulSoup
HERE = os.path.dirname(os.path.abspath(__file__))
E = lambda s: html.escape(str(s), quote=True)
V = '1'   # perf.css / perf.js version
ASSET = f'<link rel="stylesheet" href="/assets/perf.css?v={V}"><script src="/assets/perf.js?v={V}" defer></script>'
def _load(p, d=None):
    p = os.path.join(HERE, p)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else d

def _avg(d, y0, y1):
    s = [v['score'] for y, v in (d or {}).items() if y0 <= int(y) <= y1 and v and v.get('score') is not None]
    return (round(sum(s) / len(s)), len(s)) if s else (None, 0)

class Refs:
    """numbers sources in order of first use; ref('b21', 'z60') -> superscript links to the source list"""
    def __init__(self, S): self.S, self.order = S, []
    def __call__(self, *ids):
        out = []
        for i in ids:
            if i not in self.S: continue
            if i not in self.order: self.order.append(i)
            n = self.order.index(i) + 1; out.append(f'<a href="#pf-s{n}" class="pf-ref" aria-label="Source {n}">{n}</a>')
        return f'<sup class="pf-sup">{"".join(out)}</sup>' if out else ''
    def html(self):
        li = ''.join(f'<li id="pf-s{n}"><a href="{E(self.S[i]["u"])}" rel="noopener nofollow" target="_blank">{E(self.S[i]["t"])}</a> <span>{E(self.S[i]["k"])}</span></li>'
                     for n, i in enumerate(self.order, 1))
        return f'<ol class="pf-srcs">{li}</ol>'

_I = {'bolt': '<path d="M13 3 5 13h6l-1 8 8-10h-6z"/>', 'eng': '<rect x="4" y="8" width="13" height="9" rx="1.5"/><path d="M7 8V5h6v3M17 11h3v4h-3M4 12H2"/>',
      'play': '<rect x="3" y="5" width="18" height="14" rx="4"/><path d="m10 9 5 3-5 3z"/>', 'buy': '<path d="M5 12.5 10 17 19 7"/>',
      'warn': '<path d="M12 3.5 21.5 20h-19z"/><path d="M12 10v4.5M12 17.2v.3"/>', 'info': '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8v.2"/>',
      'vs': '<path d="M8 20V9M16 20V4M4 20h16"/>', 'shield': '<path d="M12 3 5 6v6c0 4 3 7.5 7 9 4-1.5 7-5 7-9V6z"/>'}
def ic(k, s=20): return f'<svg aria-hidden="true" viewBox="0 0 24 24" width="{s}" height="{s}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{_I[k]}</svg>'
def _views(n): return f'{n / 1e6:.1f}M views' if n >= 1e6 else f'{round(n / 1e3)}K views' if n >= 1e3 else f'{n} views'
def _z(z):
    """0-60: the magazine test when we have one, else BMW's figure, labelled"""
    if not z: return None, ''
    if z.get('v') is not None: return f'{z["v"]:.1f} s', z['who'] + ' test'
    if z.get('claim') is not None: return f'{z["claim"]:.1f} s', 'maker figure'
    return None, ''

def variant_card(v, R, star):
    hp = v['hp']; zv, zl = _z(v.get('z60'))
    rows = []
    def row(lbl, val, refs, note=''):
        rows.append(f'<div class="pf-r"><dt>{lbl}</dt><dd>{val}{refs}' + (f'<small>{E(note)}</small>' if note else '') + '</dd></div>')
    if v.get('tq'): row('Torque', f'{v["tq"]["v"]} lb-ft', R(*v['tq']['src']), v['tq'].get('note'))
    if zv:
        z = v['z60']; extra = f'Maker: {z["claim"]:.1f} s' if z.get('v') is not None and z.get('claim') is not None else ''
        row('0–60 mph', zv, R(*(z['src'] or z['csrc'])) + (R(*z['csrc']) if extra else ''), ' · '.join(x for x in (zl, extra) if x))
    if v.get('top'): row('Top speed', E(v['top']['v']), R(*v['top']['src']), v['top'].get('note'))
    if v.get('trans'): row('Gearbox', E(v['trans']['v']), R(*v['trans']['src']))
    if v.get('weight'): row('Weight', E(v['weight']['v']), R(*v['weight']['src']), v['weight'].get('note'))
    if v.get('price'): row('Price new' if not v.get('pkg') else 'Package price', E(v['price']['v']), R(*v['price']['src']), v['price'].get('note'))
    what = f'<p class="pf-what">{E(v["what"])}{R(*v.get("what_src", []))}</p>' if v.get('what') else ''
    cls = 'pf-v' + (' pf-star' if star else '') + (' pf-pkg' if v.get('pkg') else '')
    return (f'<article class="{cls}"><header><h4>{E(v["name"])}</h4><span>{E(v["years"])}</span></header>'
            f'<p class="pf-hp"><b>{hp["v"]}</b> hp{R(*hp["src"])}' + (f'<small>{E(hp["note"])}</small>' if hp.get('note') else '') + '</p>'
            f'{what}<dl>{"".join(rows)}</dl></article>')

def build(slug, out='docs'):
    D = _load(f'data/perf/{slug}.json'); A = _load(f'data/perf/{slug}.auto.json', {}) or {}
    if not D: return False
    page = os.path.join(HERE, out, D['page'].strip('/'), 'index.html')
    if not os.path.exists(page): return False
    try:   # 11-11: fresh YouTube topics when the study folders are on this PC (pulls land between builds)
        import data_perf as DP
        if os.path.isdir(DP.YT):   # only the studies that weren't pulled when data_perf.py last ran (a full re-read takes ~30 s)
            A.setdefault('yt', {})
            for st in [g.get(k) for g in D['gens'] for k in ('yt_study', 'comp_study')] + [e.get('study') for e in D['engines'].values()]:
                if st and not A['yt'].get(st): A['yt'][st] = DP.yt_study(st, D.get('topics_extra'))
    except Exception: pass
    YS = (_load('data/yt_scores.json', {}) or {}).get(D['yt_model'], {}); BYT = _load('data/bmw_engine_yt.json', {}) or {}
    SCY = {**(A.get('scores') or {}), **(_load('data/supercar_engine_yt.json', {}) or {})}   # the snapshot data_perf.py took, the live file wins
    R = Refs(D['sources']); short = D['short']; G = D['gens']
    focus = next((i for i, g in enumerate(G) if g['id'] == D.get('focus')), len(G) - 1)
    # ---- scores
    gsc = {g['id']: _avg(YS, g['y0'], g['y1']) for g in G}
    granked = sorted([g['id'] for g in G if gsc[g['id']][0] is not None], key=lambda i: -gsc[i][0])
    def eng_score(code):
        e = D['engines'][code]; src, key = e['yt']   # the engine's own study (auto_gens) first, else the BMW engine attribution
        d = (SCY.get(e.get('study')) or {}).get('years') or (SCY.get(key) or {}).get('years') or (BYT.get(key) if src == 'bmw' else None)
        g = next(x for x in G if x['engine'] == code)
        return _avg(d, g['y0'], g['y1'])
    esc = {c: eng_score(c) for c in D['engines']}
    eranked = sorted([c for c in esc if esc[c][0] is not None], key=lambda c: -esc[c][0])
    # ---- hero: generation slider
    def lead(g):
        vs = g['variants']; return next((v for v in vs if v['id'] == D.get('star')), next((v for v in vs if not v.get('pkg')), vs[0]))
    stops = ''.join(f'<button type="button" class="pf-stop" data-i="{i}" aria-pressed="{"true" if i == focus else "false"}"><b>{E(g["code"])}</b><span>{E(g["years"])}</span></button>' for i, g in enumerate(G))
    imgs = ''.join(f'<img src="{E(g["img"])}" alt="{E(D["name"])} {E(g["code"])} ({E(g["years"])}) in {E(g["color"])}, AI illustration" width="1000" height="600" '
                   f'class="pf-car{" on" if i == focus else ""}" data-i="{i}" decoding="async"{"" if i == focus else " loading=" + chr(34) + "lazy" + chr(34)}>' for i, g in enumerate(G))
    def stats(g):
        v = lead(g); zv, zl = _z(v.get('z60'))
        top = v.get('top', {}).get('v', '')
        s = [(f'{v["hp"]["v"]}', 'horsepower', ''), (zv.replace(' s', '') if zv else '–', '0–60 mph, sec', zl), (top.replace(' mph', ''), 'mph top speed', (v.get('top') or {}).get('note', ''))]
        return (f'<div class="pf-stats{" on" if g is G[focus] else ""}" data-g="{g["id"]}"><p class="pf-sl">{E(v["name"])} <span>{E(g["code"])} · {E(v["years"])}</span></p>'
                + ''.join(f'<div class="pf-st"><b>{E(a)}</b><span>{E(b)}</span></div>' for a, b, _ in s) + f'<p class="pf-tag">{E(g["tag"])}</p></div>')
    hero_stats = ''.join(stats(g) for g in G)
    info = ('<button class="ii" type="button" aria-label="Image info" aria-expanded="false" aria-controls="pf-ii">i</button><div class="ii-pop" id="pf-ii" role="note" hidden>'
            'AI illustrations (one per generation), not photos of a specific car. Free to use under '
            '<a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener license">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a></div>')
    slider = (f'<div class="pf-gens" data-focus="{focus}"><div class="pf-stage">{imgs}{info}</div>'
              f'<div class="pf-track" role="group" aria-label="{E(short)} generation">{stops}</div>'
              f'<input class="pf-range" type="range" min="0" max="{len(G) - 1}" step="1" value="{focus}" aria-label="{E(short)} generation" aria-valuetext="{E(G[focus]["code"])}">{hero_stats}</div>')
    # ---- per generation: performance, engine, YouTube, buy
    nh = (A.get('nhtsa') or {}); rc = A.get('recalls') or {}; yt = A.get('yt') or {}
    blocks = []
    for gi, g in enumerate(G):
        eng = D['engines'][g['engine']]; ga = (nh.get('gens') or {}).get(g['id'], {})
        cards = ''.join(variant_card(v, R, v['id'] == D.get('star')) for v in g['variants'])
        perf = (f'<section class="pf-sec"><h2>{ic("bolt")} How fast is the {E(g["code"])} {E(short)}?</h2>'
                f'<p class="pf-dek">{E(g["body"])}, {E(g["years"])}. 0–60 times are magazine tests where we have one, otherwise the maker&#39;s figure.</p>'
                f'<div class="pf-vs">{cards}</div></section>')
        # engine
        sc, n_ = esc[g['engine']]
        rk = (eranked.index(g['engine']) + 1) if g['engine'] in eranked else None
        eph = (eng.get('photo') or (_load('data/bmw_engine_photos.json', {}) or {}).get(g['engine'])   # the engine's illustration: set in the data, the BMW set, or the supercar/performance set
               or (_load('data/supercar_engine_photos.json', {}) or {}).get(eng.get('study') or '') or {})
        eimg = (f'<img src="{E(eph["src"])}" alt="{E(eng["name"])} engine, AI illustration" width="{eph["w"]}" height="{eph["h"]}" loading="lazy" decoding="async">' if eph else '')
        facts = ''.join(f'<div class="pf-f"><span>{E(k)}</span><b>{E(v)}{R(*s)}</b></div>' for k, v, s in eng['facts'])
        ytl = (f'<p class="pf-eyt">{ic("play", 16)} YouTube owner tone <b>{sc}</b>/100' + (f' · #{rk} of {len(eranked)} {E(short)} engines' if rk and len(eranked) > 1 else '') + '</p>'
               if sc is not None else f'<p class="pf-eyt na">{ic("play", 16)} YouTube owner tone: the {E(eng["name"].split()[-1])} study is running, its score shows here when it lands.</p>')
        iss = []
        for i in eng['issues']:
            cnt = (ga.get('issues') or {}).get(i['t'])
            nline = (f'<span class="pf-n">{cnt["n"]} owner complaint{"" if cnt["n"] == 1 else "s"} to NHTSA mention it ({E(g["years"])})</span>' if cnt and cnt['n'] else '')
            iss.append(f'<li><div><b>{E(i["t"])}</b><span class="pf-k">{E(i["kind"])}</span></div><p>{E(i["x"])}{R(*i["src"])}</p>'
                       + (f'<p class="pf-fix">Fix: {E(i["fix"])}</p>' if i.get('fix') else '') + nline + '</li>')
        engine = (f'<section class="pf-sec"><h2>{ic("eng")} The engine: {E(eng["name"])}</h2><div class="pf-eng"><div class="pf-ei">{eimg}</div><div class="pf-ef">'
                  f'<p class="pf-ew">{E(eng["what"])}</p><div class="pf-fs">{facts}</div>{ytl}<a class="pf-go" href="{E(eng["page"])}">{E(eng["name"].split()[-1])} engine page →</a></div></div>'
                  f'<h3 class="pf-h3">Known issues</h3><ul class="pf-iss">{"".join(iss)}</ul></section>')
        # YouTube
        gs, gn = gsc[g['id']]; grk = granked.index(g['id']) + 1 if g['id'] in granked else None
        st = yt.get(g['yt_study']) or {}; cs = yt.get(g.get('comp_study')) if g.get('comp_study') else None
        comp_sc = _avg((SCY.get(g.get('comp_study')) or {}).get('years'), g['y0'], g['y1'])[0] if g.get('comp_study') else None
        def bars(rows, cls):
            if not rows: return '<p class="pf-none">Nothing stands out.</p>'
            mx = max(p for _, p in rows) or 1
            return ''.join(f'<div class="pf-b {cls}"><span>{E(k)}</span><i style="--w:{round(100 * p / mx)}%"></i><b>{p}%</b></div>' for k, p in rows)
        src_st = st   # topics + videos from the generation's own study (the trim study spans generations; it only adds its score)
        vids = ''.join(f'<a class="pf-vid" href="https://www.youtube.com/watch?v={E(v["id"])}" rel="noopener nofollow" target="_blank">'
                       f'<img src="https://i.ytimg.com/vi/{E(v["id"])}/mqdefault.jpg" alt="" width="320" height="180" loading="lazy" decoding="async">'
                       f'<span>{E(v["title"])}</span><small>{E(v["ch"])} · {_views(v["views"])}</small></a>' for v in (src_st.get('top') or [])[:3])
        comp_line = ''
        if g.get('comp_study'):
            cl = E(g.get('comp_label') or 'Competition')
            comp_line = (f'<div class="pf-yb"><b>{comp_sc}</b><span>{cl} videos only</span></div>' if comp_sc is not None else
                         f'<div class="pf-yb na"><b>…</b><span>{cl} study scoring now</span></div>')
        ytsec = (f'<section class="pf-sec"><h2>{ic("play")} What owners say on YouTube</h2><div class="pf-ys">'
                 + (f'<div class="pf-yb big"><b>{gs}</b><span>YouTube owner tone, out of 100' + (f' · #{grk} of {len(granked)} generations' if grk else '') + '</span></div>' if gs is not None else '<div class="pf-yb na"><b>–</b><span>Not enough videos yet</span></div>')
                 + comp_line + '</div>'
                 + (f'<div class="pf-pc"><div><h3>Owners praise</h3>{bars(src_st.get("praise"), "pf-gd")}</div><div><h3>Owners complain about</h3>{bars(src_st.get("trouble"), "pf-bd")}</div></div>'
                    f'<p class="pf-cap">Share of the {src_st.get("videos", 0)} most-watched {E(g["code"] + " " + short)} videos that praise or criticize each topic (a praise or trouble word near it in the title or transcript).</p>' if src_st else '')
                 + (f'<h3 class="pf-h3">Most-watched videos</h3><div class="pf-vids">{vids}</div>' if vids else '') + '</section>')
        # should you buy one
        yrs = range(g['y0'], g['y1'] + 1); by = {int(y): n for y, n in (nh.get('by_year') or {}).items() if int(y) in yrs}
        ytb = {int(y): v['score'] for y, v in YS.items() if int(y) in yrs and v.get('score') is not None}
        buy = []
        lv = lead(g)
        if lv.get('price'): buy.append(('buy', f'New, the {E(lv["name"])} cost {E(lv["price"]["v"])}' + (f' ({E(lv["price"]["note"])})' if lv["price"].get("note") else '') + f'.{R(*lv["price"]["src"])}'))
        if len(set(ytb.values())) > 1:
            b = max(ytb, key=lambda y: (ytb[y], y)); buy.append(('buy', f'YouTube likes the <b>{b}</b> best ({ytb[b]}/100).'))
        if len(by) >= 2:
            hi_ = max(by, key=by.get); lo_ = min(by, key=by.get)
            if by[hi_] >= 10: buy.append(('info', f'Most owner complaints: the <b>{hi_}</b> ({by[hi_]}). Fewest: the {lo_} ({by[lo_]}). Raw counts, not per car sold.'))
            else: buy.append(('buy', f'Few owner complaints so far: {sum(by.values())} to NHTSA for {g["y0"]}–{g["y1"]}.'))
        big = [i for i in eng['issues'] if i.get('rx') and (((ga.get('issues') or {}).get(i['t']) or {}).get('n') or 'BMW' in i['kind'])]
        for i in big[:2]:
            n_i = ((ga.get('issues') or {}).get(i['t']) or {}).get('n')
            buy.append(('warn', f'Budget for <b>{E(i["t"].lower())}</b>' + (f': {n_i} owner complaints mention it.' if n_i else f' ({E(i["kind"].lower())}).') + (f' {E(i["fix"])}' if i.get('fix') else '')))
        nrec = len({r['id'] for y in yrs for r in rc.get(str(y), [])})
        if nrec: buy.append(('warn', f'{nrec} recall campaign{"" if nrec == 1 else "s"} across {g["y0"]}–{g["y1"]}. <a href="/vin/">Check a VIN</a> before you buy.'))
        buy.append(('info', f'Repair costs: we don&#39;t have owner-reported repair costs for the {E(short)} yet.'))
        buysec = (f'<section class="pf-sec"><h2>{ic("buy")} Should you buy a {E(g["code"])} {E(short)}?</h2><ul class="pf-buy">'
                  + ''.join(f'<li class="pf-l-{k}">{ic(k, 18)}<span>{t}</span></li>' for k, t in buy) + '</ul></section>')
        blocks.append(f'<div class="pf-g{" on" if gi == focus else ""}" data-g="{g["id"]}" data-i="{gi}"><p class="pf-gh">{E(g["code"])} {E(short)} · {E(g["years"])}</p>{perf}{engine}{ytsec}{buysec}</div>')
    # ---- compare chips
    def cmp_url(c):
        for u in (f'/compare/{slug}-vs-{c["slug"]}/', f'/compare/{c["slug"]}-vs-{slug}/', f'/cars/{c["slug"]}/', f'/performance/{c["slug"]}/'):   # a head-to-head page first, else the rival's own page
            if os.path.exists(os.path.join(HERE, out, u.strip('/'), 'index.html')): return u
        return None
    chips = ''.join((f'<a class="pf-c" href="{u}">' if u else '<div class="pf-c soon">') + f'<img src="{E(c["img"])}" alt="" width="1000" height="600" loading="lazy" decoding="async">'
                    f'<span>{E(short)} vs {E(c["name"])}</span><small>{"Compare →" if u else "Coming soon"}</small>' + ('</a>' if u else '</div>') for c in D['compare'] for u in [cmp_url(c)])
    cmp_sec = f'<section class="pf-sec"><h2>{ic("vs")} Compare the {E(short)}</h2><div class="pf-cmp">{chips}</div></section>'
    return D, slider, ''.join(blocks), cmp_sec, R, esc, gsc, page

def inject(slug, out='docs'):
    r = build(slug, out)
    if not r: return False
    D, slider, blocks, cmp_sec, R, esc, gsc, page = r
    s = BeautifulSoup(open(page, encoding='utf-8').read(), 'html.parser')
    if s.find(class_='pf-gens'): return False   # already done (a page that wasn't rebuilt this run)
    hero = s.find('section', class_='tb-hero'); ov = s.find('section', id='p-overview')
    if not hero or not ov: return False
    short = D['short']; G = D['gens']
    # hero: crumbs, h1, the slider + big numbers; the old picture and complaint sentence go
    for t in hero.find_all(class_=['tb-img', 'tb-ans', 'yhero']): t.decompose()
    h1 = hero.find('h1'); h1.string = D['h1']
    h1.insert_after(BeautifulSoup(slider, 'html.parser'))
    hero['class'] = hero.get('class', []) + ['pf-hero']
    # Overview: the performance story first, then the reliability cards that were there (secondary), compare, sources
    old = ''.join(str(c) for c in ov.contents)
    no_li = (f'<p class="pf-li">{ic("shield", 18)}<span>No Lemon Index for the {E(short)}: the index is complaints per car sold, and we don&#39;t have U.S. sales by year for it. '
             f'The counts below are raw owner complaints to NHTSA.</span></p>')
    rel = f'<section class="pf-sec pf-rel"><h2>{ic("shield")} Reliability</h2>{no_li}{old}</section>'
    ov.clear(); ov.append(BeautifulSoup(f'<div class="pf">{blocks}{rel}{cmp_sec}<details class="pf-sd"><summary>Sources ({len(R.order)})</summary>{R.html()}</details></div>', 'html.parser'))
    # Questions tab: two performance answers from the same data
    qa = s.find('section', class_='yqa')
    if qa:
        g = next(x for x in G if x['id'] == D.get('focus')); v = next(x for x in g['variants'] if x['id'] == D.get('star'))
        zv, zl = (f'{v["z60"]["v"]:g} seconds', v['z60']['who']) if v['z60'].get('v') is not None else (f'{v["z60"]["claim"]:g} seconds', 'BMW')
        q1 = (f'<h3>How fast is the {E(D["make"])} {E(v["name"])}?</h3><p>The {E(g["code"])} {E(v["name"])} makes {v["hp"]["v"]} hp and {v["tq"]["v"]} lb-ft. '
              f'{E(zl)} measured 0–60 mph in {zv}. Top speed is {E(v["top"]["v"])} ({E(v["top"].get("note", ""))}).</p>')
        codes = [x for x in sorted(esc, key=lambda c: -(esc[c][0] or -1)) if esc[x][0] is not None]
        q2 = (f'<h3>Which {E(D["name"])} engine do YouTube owners like most?</h3><p>' + (', '.join(f'{E(D["engines"][c]["name"])} {esc[c][0]}/100' for c in codes) +
              '. That&#39;s the tone of the most-watched videos about each engine, praise words against trouble words.</p>' if len(codes) >= 2 else
              'The engine studies are still running; the scores show here when they land.</p>'))
        qa.append(BeautifulSoup(q1 + q2, 'html.parser'))
    # head: title, description, our css/js
    g = next(x for x in G if x['id'] == D.get('focus')); v = next(x for x in g['variants'] if x['id'] == D.get('star'))
    t = s.find('title'); t.string = f'{D["name"]} & {v["name"]}: 0-60, Horsepower, Engines, Problems'
    desc = (f'{D["name"]} performance by generation: the {g["code"]} {v["name"]} makes {v["hp"]["v"]} hp and runs 0-60 in {_z(v["z60"])[0]}. '
            f'Engines, known issues, YouTube owner verdicts and recalls, every number sourced.')
    for m in s.find_all('meta'):
        if m.get('name') == 'description' or m.get('property') in ('og:description',) or m.get('name') == 'twitter:description': m['content'] = desc
        if m.get('property') == 'og:title' or m.get('name') == 'twitter:title': m['content'] = t.string
    s.head.append(BeautifulSoup(ASSET + ('' if s.find('script', src=re.compile('imginfo')) else '<script src="/assets/imginfo.js?v=1" defer></script>'), 'html.parser'))
    open(page, 'w', encoding='utf-8').write(str(s))
    return True

def build_all(out='docs'):
    done = []
    for p in sorted(glob.glob(os.path.join(HERE, 'data', 'perf', '*.json'))):
        slug = os.path.basename(p)[:-5]
        if slug.endswith('.auto'): continue
        try:
            if inject(slug, out): done.append(slug)
        except Exception as e: print('perf page failed', slug, repr(e))
    print('perf pages:', done)
    return done

if __name__ == '__main__':
    import sys; sys.stdout.reconfigure(encoding='utf-8'); build_all()
