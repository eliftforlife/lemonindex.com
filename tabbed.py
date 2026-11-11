# 11-10 (Elijah, Civic first): model + year pages as a centered hero and ~6 tabs instead of one long scroll, plus a Years / Engines
# toggle on the "every year" chart. Reusable: a model id in ON gets it; everything else keeps the old layout.
# The page HTML is still built by build.py; transform_model() / transform_year() only re-arrange its sections, so every section stays in
# the HTML (crawlable). assets/tabs.js hides the inactive panels (and handles #hash deep links); without JS everything shows.
# Engine groups per model: data/engines_<model id>.json (years from EPA fueleconomy.gov, codes from Wikipedia's engine articles).
import json, os, re, html
from bs4 import BeautifulSoup

ON = {'honda-civic'}
HERE = os.path.dirname(os.path.abspath(__file__))
E = lambda s: html.escape(str(s), quote=True)
LIC = 'https://creativecommons.org/licenses/by/4.0/'
BASE = 'https://lemonindex.com'
ASSET = '<link rel="stylesheet" href="/assets/tabs.css?v=4"><script src="/assets/tabs.js?v=1"></script>'

def engines(fid):
    p = os.path.join(HERE, 'data', f'engines_{fid}.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []

_BMW = None
def bmw_groups(fid):
    """11-10 rollout: BMW models get the Years / Engines toggle from data/bmw_specs.json (engine code per EPA version + year),
    with the engine illustration from data/bmw_engine_photos.json when there is one."""
    global _BMW
    if not fid.startswith('bmw-'): return []
    if _BMW is None:
        try:
            _BMW = (json.load(open(os.path.join(HERE, 'data', 'bmw_specs.json'), encoding='utf-8')),
                    json.load(open(os.path.join(HERE, 'data', 'bmw_engine_photos.json'), encoding='utf-8')) if os.path.exists(os.path.join(HERE, 'data', 'bmw_engine_photos.json')) else {})
        except Exception: _BMW = ({}, {})
    sp, ph = _BMW
    by = {}
    for y, vs in ((sp.get('versions') or {}).get(fid) or {}).items():
        for v in vs:
            if v.get('code'): by.setdefault(v['code'], set()).add(int(y))
    out = []
    for code, ys in by.items():
        e = (sp.get('engines') or {}).get(code) or {}
        asp = {'naturally aspirated': '', 'non-turbo': '', 'single twin-scroll turbo': 'turbo'}.get(e.get('asp') or '', e.get('asp') or '')
        nm = ' '.join(x for x in (e.get('size'), asp, e.get('layout')) if x) or code
        g = {'id': code.lower(), 'name': nm, 'code': code, 'years': sorted(ys), 'src': [x for x in (e.get('src'), 'https://www.fueleconomy.gov/') if x]}
        im = ph.get(code)
        if im: g['img'] = {'src': im['src'], 'w': im['w'], 'h': im['h']}
        out.append(g)
    return sorted(out, key=lambda g: (g['years'][0], g['code']))

def groups(fid): return engines(fid) or bmw_groups(fid)

def _span(ys):
    """[1973..1979] -> '1973–1979'; gaps -> '2017–2021, 2023–2026'."""
    ys = sorted(ys); out = []; a = b = ys[0]
    for y in ys[1:]:
        if y == b + 1: b = y
        else: out.append((a, b)); a = b = y
    out.append((a, b))
    return ', '.join(f'{a}' if a == b else f'{a}–{b}' for a, b in out)

def _info(txt):
    import year_slider as YSL
    return YSL.info(txt)

YTI = '<svg aria-hidden="true" viewBox="0 0 24 24" width="11" height="11"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>'
def engine_chart(fid, name, li, yt, pages, cur=None, cls=lambda li: '', ysc=None):
    """Every engine, with its image on the left and one row per model year on the right.
    li = {year: Lemon Index} (only years with enough complaints), yt = {year: YouTube rank #} (only rankable years), pages = years with a page."""
    gs = groups(fid)
    if not gs: return ''
    mx = max([120] + [v * 1.08 for v in li.values()])
    # 11-10 (Elijah: "put YT rank in the corner of all engines"): each engine's YouTube rank among the engines here, by its average
    # YouTube score over its rankable years (ysc = {year: score} for those years); engines with no such year show 'YT –'.
    ysc = ysc or {}
    gm = {i: sum(ysc[y] for y in g['years'] if y in ysc) / n for i, g in enumerate(gs) if (n := sum(1 for y in g['years'] if y in ysc))}
    grk = {i: r + 1 for r, (i, _) in enumerate(sorted(gm.items(), key=lambda kv: -kv[1]))}
    out = []
    for gi, g in enumerate(gs):
        im = g.get('img') or {}
        ytb = (f'<span class="ytbadge eg-yr" title="YouTube rank by tone, of {len(grk)} {E(name)} engines with enough videos">{YTI}YT #{grk[gi]}</span>' if gi in grk
               else '<span class="ytbadge eg-yr na" title="Not enough YouTube videos to rank">' + YTI + 'YT –</span>')
        rows = []
        for y in g['years']:
            v = li.get(y); r = yt.get(y)
            c = (f'<span class="er-bt"><i style="width:{min(100, v / mx * 100):.1f}%"></i><em style="left:{100 / mx * 100:.1f}%"></em></span><b>{v}</b>' if v is not None else '<span class="er-bt na"></span><b class="mute"></b>')
            t = f'<b class="er-rk">#{r}</b>' if r is not None else '<b class="er-rk mute">·</b>'
            tag = 'a' if y in pages else 'div'; href = f' href="/cars/{fid}/{y}/"' if y in pages else ''
            rows.append(f'<{tag} class="er{" " + cls(v) if v is not None else ""}{" cur" if y == cur else ""}"{href}><span class="er-y">{y}</span>{c}{t}</{tag}>')
        img = (f'<span class="eg-im"><img src="{E(im["src"])}" alt="{E(name)} {E(g["name"])} engine illustration" width="{im["w"]}" height="{im["h"]}" loading="lazy" decoding="async">'
               + _info(f'Illustration (AI-generated) of the {E(name)} {E(g["name"])} engine, not a photo of a specific engine. Free to use under <a href="{LIC}" rel="license noopener">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>')
               + ytb + '</span>') if im else ytb
        out.append(f'<div class="eg">{img}<div class="eg-n"><b>{E(g["name"])}</b><small>{E(g["code"])}</small><small>{_span(g["years"])}</small></div><div class="eg-r">{"".join(rows)}</div></div>')
    src = sorted({s for g in gs for s in g.get('src', [])})
    links = ' · '.join(f'<a href="{E(s)}" rel="noopener">{"EPA fueleconomy.gov" if "fueleconomy" in s else "Wikipedia: " + s.rsplit("/", 1)[1].replace("_", " ")}</a>' for s in src)
    return (f'<div class="engc"><div class="engc-h" aria-hidden="true"><span>Engine</span><span>Year</span><span>Complaints <em>lower = better</em></span><span>YouTube rank <em>#1 = favorite</em></span></div>'
            + ''.join(out) + f'<p class="yc-cap">Scores are per model year, so a year with several engines shows the same score next to each one. An empty complaints bar means too few complaints to score that year; a gray dot means not enough YouTube videos. Sources: {links}.</p></div>')

def images_ld(fid, name):
    return [{"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": BASE + g['img']['src'], "url": BASE + g['img']['src'],
             "name": f'{name} {g["name"]} engine (illustration)', "description": f'AI-generated illustration of the {name} {g["name"]} engine ({g["code"]}), not a photo of a specific engine.',
             "width": g['img']['w'], "height": g['img']['h'], "encodingFormat": "image/webp", "license": LIC, "acquireLicensePage": BASE + '/images/',
             "creditText": "The Lemon Index", "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE + '/'}, "copyrightNotice": "The Lemon Index (lemonindex.com), CC BY 4.0"}
            for g in engines(fid) if g.get('img')]

def images_cards():
    """Cards for /images/ (bmw_pages.py adds them): every model's engine illustrations."""
    out = ''
    for fid in sorted(ON):
        gs = [g for g in engines(fid) if g.get('img')]
        if not gs: continue
        nm = fid.replace('-', ' ').title()
        out += (f'<h2>{E(nm)} engines</h2><div class="imggrid">' + ''.join(
            f'<figure class="imgcard"><img src="{E(g["img"]["src"])}" width="{g["img"]["w"]}" height="{g["img"]["h"]}" alt="{E(nm)} {E(g["name"])} engine illustration" loading="lazy">'
            f'<figcaption><b>{E(nm)} {E(g["name"])}</b><span>{E(g["code"])} · {_span(g["years"])} · Illustration (AI-generated), not a photo of a specific engine.</span>'
            f'<span>Credit: <code>Image: The Lemon Index (lemonindex.com), CC BY 4.0</code></span>'
            f'<span><a href="{E(g["img"]["src"])}">Open full size</a> · <a href="/cars/{fid}/#years">Used on: the {E(nm)} engine chart</a></span></figcaption></figure>' for g in gs) + '</div>')
    return out

def sitemap_images():
    return [(f'/cars/{fid}/', g['img']['src']) for fid in sorted(ON) for g in engines(fid) if g.get('img')]

# ---------------------------------------------------------------- layout
def _first_sentence(tag):
    """Keep the answer to one sentence (Elijah: 'a little too much text')."""
    h = re.sub(r'\s+', ' ', tag.decode_contents()).strip(); out = ''
    for m in re.finditer(r'.*?[.!?](?=\s|<|$)(</b>)?', h):
        out += m.group(0)
        if len(re.sub('<[^>]+>', '', out)) >= 40: break
    return out.strip() or h

def _tabs(panels, label, extra=''):
    """panels = [(id, tab label, html)] -> tab bar + panels. The first is open by default.
    extra = small controls that share the sticky tab row (e.g. the Normal / Advanced switch), outside the tablist."""
    panels = [p for p in panels if p[2].strip()]
    bar = ''.join(f'<button class="tb-t" role="tab" id="t-{i}" aria-controls="p-{i}" data-h="{i}" aria-selected="{"true" if n == 0 else "false"}" tabindex="{0 if n == 0 else -1}">{E(t)}</button>' for n, (i, t, _) in enumerate(panels))
    body = ''.join(f'<section class="tb-p{" on" if n == 0 else ""}" role="tabpanel" id="p-{i}" aria-labelledby="t-{i}" tabindex="0">{h}</section>' for n, (i, t, h) in enumerate(panels))
    head = f'<div class="tb-bar" role="tablist" aria-label="{E(label)}">{bar}</div>'
    if extra: head = f'<div class="tb-row">{head}{extra}</div>'
    return f'<div class="tbx">{head}{body}</div>'

# 11-10 (Elijah: "can we make this part better?"): the year page's 4 stacked control rows (year pills, big Compare/Share buttons,
# Normal/Advanced, tabs) become 2: the year switcher with small icon buttons on one row, and Normal/Advanced riding on the tab row.
_ICON = {
    'all': '<path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/>',
    'cmp': '<path d="M7 20V9M12 20V4M17 20v-7"/>',
    'shr': '<path d="M12 15V3M8 7l4-4 4 4M5 12v7a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-7"/>',
}
_svg = lambda k: f'<svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_ICON[k]}</svg>'

def _controls(sw):
    """yswitch nav -> one compact row: '‹ prev · YEAR · next ›' plus small All years / Compare / Share icon buttons."""
    if not sw: return ''
    seg = sw.find(class_='yseg'); act = sw.find(class_='yact')
    if not seg: return str(sw)
    alla = seg.find('a', class_='yall'); alla = alla.extract() if alla else None
    cur = seg.find('span', attrs={'aria-current': True}); yr = cur.get_text(strip=True) if cur else ''
    for a in seg.find_all('a'):   # '2004' -> 'Go to the 2004 report' for screen readers; the visible text keeps its arrow
        a['aria-label'] = f'{a.get_text(strip=True).strip("‹› ")} report'
    btns = []
    if alla: btns.append(f'<a class="tb-ic" href="{E(alla["href"])}" aria-label="All years"><span class="tb-ic-i">{_svg("all")}</span><span class="tb-ic-l">All years</span></a>')
    if act:
        c = act.find('a'); sh = act.find(attrs={'data-share': True})
        if c: btns.append(f'<a class="tb-ic" href="{E(c["href"])}" aria-label="Compare the {E(yr)} with other cars"><span class="tb-ic-i">{_svg("cmp")}</span><span class="tb-ic-l">Compare</span></a>')
        if sh: btns.append(f'<button class="tb-ic yshare" type="button" data-share="{E(sh["data-share"])}" aria-label="Share this report"><span class="tb-ic-i">{_svg("shr")}</span><span class="tb-ic-l">Share</span></button>')
    return f'<nav aria-label="Model years" class="yswitch tb-ctl">{seg}<div class="tb-acts">{"".join(btns)}</div></nav>'

def _modes(modes):
    """Normal / Advanced (separate URLs, so still links) as a small switch at the end of the tab row."""
    if not modes: return ''
    CUR = ' aria-current="page"'
    links = ''.join(f'<a href="{E(a["href"])}"{CUR if a.get("aria-current") else ""}>{E(a.get_text(strip=True))}</a>' for a in modes.find_all('a'))
    return f'<nav aria-label="Page mode" class="modes tb-modes">{links}</nav>'

def _toggle(years_html, eng_html, short):
    if not eng_html: return years_html
    return (f'<div class="tg"><div class="tg-b" role="group" aria-label="Show">'
            f'<button type="button" class="tg-o" data-v="years" aria-pressed="true">Every {E(short)} year</button>'
            f'<button type="button" class="tg-o" data-v="engines" aria-pressed="false">Engines</button></div>'
            f'<div class="tg-v on" data-v="years">{years_html}</div><div class="tg-v" data-v="engines">{eng_html}</div></div>')

def _s(x): return str(x) if x is not None else ''

def transform_model(body, eng_html, short):
    s = BeautifulSoup(body, 'html.parser'); root = s.find(['div', 'article'])
    ph = root.find('section', class_='ph'); yt = ph.find(class_='yh-t'); pv = ph.find(class_='ph-v')
    crumbs = yt.find('p', class_='ph-e'); h1 = yt.find('h1'); ans = yt.find('p', class_='ans'); yhero = yt.find(class_='yhero')
    share = next((p for p in yt.find_all('p', recursive=False) if p.find('button')), None)
    note = yt.find('p', class_='yc-note')
    slider = pv.find('section', class_='ysl') if pv else None
    links = [l for l in (pv.find_all(['link', 'script'], recursive=False) if pv else [])]
    rsc = pv.find(class_='rsc') if pv else None; rnew = pv.find(class_='rs-new') if pv else None
    short_ans = f'<p class="ans tb-ans">{_first_sentence(ans)}</p>' if ans else ''
    sl = _s(slider).replace('>Best year<', '>Safest year<')
    if not slider and pv:   # 11-10 rollout: no year images -> the model's own picture fills the same hero slot (car-image work can drop in here later)
        fig = pv.find('figure', class_='yph'); sl = _s(fig)   # the slider opens on the site's safest year (complaints + YouTube); 'Best year' below means fewest complaints
    hero = (f'<section class="ph tb-hero">{_s(crumbs)}<div class="tb-img">{"".join(map(str, links))}{sl}</div>{_s(h1)}{short_ans}{_s(yhero)}{_s(share)}</section>')
    secs = [c for c in root.find_all(recursive=False) if c is not ph]
    pick = lambda pred: [c for c in secs if pred(c)]
    years = pick(lambda c: c.get('id') == 'years')
    bw = pick(lambda c: 'bw2' in (c.get('class') or []))
    cmp_ = pick(lambda c: c.find('h2') and c.find('h2').get_text().startswith('Compare'))
    qa = pick(lambda c: 'yqa' in (c.get('class') or []))
    table = pick(lambda c: c.find('table') is not None and c.get('id') != 'years')
    used = set(map(id, years + bw + cmp_ + qa + table))
    rest = [c for c in secs if id(c) not in used and 'shline' not in (c.get('class') or [])]
    tail = ''.join(str(c) for c in secs if 'shline' in (c.get('class') or []))
    if years:
        ys = years[0]; ch = ys.find(class_='yy-ch')
        if ch:
            h2 = ch.find('h2'); h2s = str(h2) if h2 else ''
            if h2: h2.extract()
            inner = ch.decode_contents(); ch.clear(); ch.append(BeautifulSoup(h2s + _toggle(inner, eng_html, short), 'html.parser'))
    over = f'{_s(note)}{_s(rsc)}{_s(rnew)}' + ''.join(map(str, bw + rest))
    tabs = _tabs([('overview', 'Overview', over), ('years', 'Years & engines' if eng_html else 'Years', ''.join(map(str, years))), ('compare', 'Compare', ''.join(map(str, cmp_))),
                  ('questions', 'Questions', ''.join(map(str, qa))), ('data', 'All the data', ''.join(map(str, table)))], f'{short} sections')
    cls = ' '.join(root.get('class') or [])
    return f'{ASSET}<div class="{cls} tbl">{hero}{tabs}{tail}</div>'

def transform_year(body, eng_html, short):
    s = BeautifulSoup(body, 'html.parser'); root = s.find(['article', 'div'])
    ph = root.find('section', class_='ph'); yt = ph.find(class_='yh-t'); pv = ph.find(class_='ph-v')
    crumbs = yt.find('p', class_='ph-e'); h1 = yt.find('h1'); ans = yt.find('p', class_='ans'); yhero = yt.find(class_='yhero')
    modes = yt.find('nav', class_='modes'); sw = yt.find('nav', class_='yswitch'); early = yt.find(class_='early-b'); note = yt.find('p', class_='yc-note')
    img = ''.join(str(c) for c in (pv.find_all(recursive=False) if pv else []))
    short_ans = f'<p class="ans tb-ans">{_first_sentence(ans)}</p>' if ans else ''
    hero = f'<section class="ph tb-hero">{_s(crumbs)}<div class="tb-img">{img}</div>{_s(h1)}{_s(early)}{_s(yhero)}{_controls(sw)}</section>'   # the gauge + verdict already say it: no answer paragraph
    top = [c for c in root.find_all(recursive=False) if c is not ph]
    grid = next((c for c in top if 'ygrid' in (c.get('class') or [])), None)
    items = [c for c in top if c is not grid] + (grid.find_all(recursive=False) if grid else [])
    H = lambda c: (c.find('h2').get_text(' ', strip=True) if c.find('h2') else '')
    C = lambda c: c.get('class') or []
    over, probs, fix, rec, yrs, qa, tail = [], [], [], [], [], [], []
    for c in items:
        h = H(c); k = C(c)
        if 'shline' in k or ('yc-cap' in k and c.name == 'p'): tail.append(c)
        elif 'yyears' in k: yrs.append(c)
        elif 'yqa' in k: qa.append(c)
        elif c.get('id') in ('problems',) or 'ysev' in k or h.startswith(('When owners', 'In owners', 'What owners')): probs.append(c)
        elif c.get('id') in ('diy', 'fixes') or 'yfx' in k or h.startswith(('Problems ', 'Fixes', 'What owners say it costs', 'Prices', 'What it')) or c.find(class_='price'): fix.append(c)
        elif c.get('id') in ('recalls', 'inv') or h.startswith(('Recalls', 'Government', 'Safety', 'Specs')) or c.find('details', class_='yd'): rec.append(c)
        else: over.append(c)
    for ys in yrs:
        ch = ys.find(class_='yy-ch')
        if ch:
            h2 = ch.find('h2'); h2s = str(h2) if h2 else ''
            if h2: h2.extract()
            inner = ch.decode_contents(); ch.clear(); ch.append(BeautifulSoup(h2s + _toggle(inner, eng_html, short), 'html.parser'))
    J = lambda xs: ''.join(map(str, xs))
    tabs = _tabs([('overview', 'Overview', _s(note) + J(over)), ('problems', 'Problems', J(probs)), ('repairs', 'Repairs & costs', J(fix)),
                  ('recalls', 'Recalls & safety', J(rec)), ('years', 'Every year', J(yrs)), ('questions', 'Questions', J(qa))], 'Report sections', _modes(modes))
    cls = ' '.join(root.get('class') or [])
    return f'{ASSET}<article class="{cls} tbl">{hero}{tabs}{J(tail)}</article>'

# 11-10 rollout, part 2: the other template ("advp": the 27 no-sales model pages, every Advanced year page, motorcycle and plane
# Advanced pages). Same idea: centered hero (crumbs, image, h1, one-sentence answer, stat tiles), sections sorted into tabs, the
# Normal / Advanced switch on the tab row. Nothing is dropped: an unknown section lands in Overview.
_ADV = [  # (tab id, label, section ids, h2 prefixes)
    ('years', 'Years', ('years', 'neighbors'), ('Complaints by model year', 'Nearby model years', 'Every model year')),
    ('problems', 'Problems', ('problems', 'mileage', 'systems', 'severity'), ('What owners complain', 'When problems', 'How serious', 'In owners', 'Failure mileage', 'Complaints by system', 'Severity')),
    ('repairs', 'Repairs & costs', ('diy', 'fixes', 'youtube'), ('Fixes', 'YouTube repair', 'What owners say it costs')),
    ('recalls', 'Recalls & safety', ('recalls', 'campaigns', 'investigations', 'tsb', 'tech', 'inv', 'crash'), ('Recall', 'NHTSA investigations', 'Manufacturer communications', 'Safety', 'Investigations', 'Crash')),
    ('specs', 'Specs & engines', ('engines', 'specs'), ('Engines', 'Specs')),
    ('questions', 'Questions', (), ()),
]
def _adv_sort(items, modes, short, order=None):
    """Sections -> (tab bar + panels, tail items), by section id / h2 (see _ADV)."""
    H = lambda c: (c.find('h2').get_text(' ', strip=True) if c.find('h2') else '')
    got = {t[0]: [] for t in _ADV}; over, tail = [], []
    for c in items:
        k = c.get('class') or []; h = H(c); cid = c.get('id') or ''
        if 'shline' in k or (c.name == 'p' and 'yc-cap' in k): tail.append(c); continue
        if 'yqa' in k: got['questions'].append(c); continue
        for tid, _, ids, pre in _ADV:
            if cid in ids or (cid.startswith(ids) if ids else False) or (pre and h.startswith(pre)) or ('yfx' in k and tid == 'repairs') or ('bspec' in k and tid == 'specs'):
                got[tid].append(c); break
        else: over.append(c)
    J = lambda xs: ''.join(map(str, xs))
    panels = [('overview', 'Overview', J(over))] + [(tid, lab, J(got[tid])) for tid, lab, _, _ in _ADV]
    if order: panels = sorted(panels, key=lambda p: order.index(p[0]) if p[0] in order else len(order))   # 11-10: Advanced pages open on the meatiest tab
    tabs = _tabs(panels, f'{short} sections', _modes(modes))
    return tabs, tail

def transform_adv(body, short, eng_html=''):
    s = BeautifulSoup(body, 'html.parser'); root = s.find('div', class_='advp')
    if root is None or 'tbl' in (root.get('class') or []): return body
    hd = root.find('header', class_='advh1', recursive=False)
    crumbs = hd.find('p', class_='ph-e') if hd else None; h1 = hd.find('h1') if hd else None
    modes = hd.find('nav', class_='modes') if hd else None
    ans = (hd.find('p', class_='ans') or next((p for p in hd.find_all('p', recursive=False) if p is not crumbs), None)) if hd else None
    img = root.find('div', class_='advimg', recursive=False); yts = root.find('div', class_='yts', recursive=False)
    short_ans = f'<p class="ans tb-ans">{_first_sentence(ans)}</p>' if ans else ''
    hero = (f'<section class="ph tb-hero">{_s(crumbs)}' + (f'<div class="tb-img">{img.decode_contents()}</div>' if img else '')
            + f'{_s(h1)}{short_ans}{_s(yts)}</section>')
    items = []
    for c in root.find_all(recursive=False):
        if c in (hd, img, yts): continue
        if 'ygrid' in (c.get('class') or []): items += c.find_all(recursive=False)
        else: items.append(c)
    adv = bool(h1 and 'Advanced' in h1.get_text())
    if eng_html:   # 11-10: no-sales BMWs get the Years / Engines toggle on their year table (engine groups from bmw_specs.json)
        ys = next((c for c in items if c.get('id') == 'years'), None)
        if ys is not None:
            h2 = ys.find('h2'); h2s = str(h2) if h2 else ''
            if h2: h2.extract()
            inner = ys.decode_contents(); ys.clear(); ys.append(BeautifulSoup(h2s + _toggle(inner, eng_html, short), 'html.parser'))
    tabs, tail = _adv_sort(items, modes, short, ['problems', 'recalls', 'specs', 'repairs', 'years', 'overview', 'questions'] if adv else None); J = lambda xs: ''.join(map(str, xs))
    cls = ' '.join(root.get('class') or [])
    return f'{ASSET}<div class="{cls} tbl">{hero}{tabs}{J(tail)}</div>'

def transform_mp6(body, short):
    """Motorcycle pages (vehicles_pages.py, 'pg mp6'): centered hero (crumbs, photo + its credit, h1, one line, stat tiles) and tabs."""
    s = BeautifulSoup(body, 'html.parser'); root = s.find('div', class_='mp6')
    if root is None or 'tbl' in (root.get('class') or []): return body
    ph = root.find('section', class_='ph', recursive=False); yt = ph.find(class_='yh-t'); pv = ph.find(class_='ph-v')
    crumbs = yt.find('p', class_='ph-e'); h1 = yt.find('h1'); sub = yt.find('p', class_='ph-s'); modes = yt.find('nav', class_='modes')
    yts = root.find('div', class_='yts', recursive=False)
    hero = (f'<section class="ph tb-hero">{_s(crumbs)}' + (f'<div class="tb-img">{pv.decode_contents()}</div>' if pv else '')
            + f'{_s(h1)}' + (f'<p class="ans tb-ans">{sub.decode_contents()}</p>' if sub else '') + f'{_s(yts)}</section>')
    items = [c for c in root.find_all(recursive=False) if c not in (ph, yts)]
    tabs, tail = _adv_sort(items, modes, short); J = lambda xs: ''.join(map(str, xs))
    cls = ' '.join(root.get('class') or [])
    return f'{ASSET}<div class="{cls} tbl">{hero}{tabs}{J(tail)}</div>'
