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
ASSET = '<link rel="stylesheet" href="/assets/tabs.css?v=2"><script src="/assets/tabs.js?v=1"></script>'

def engines(fid):
    p = os.path.join(HERE, 'data', f'engines_{fid}.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []

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

def engine_chart(fid, name, li, yt, pages, cur=None, cls=lambda li: ''):
    """Every engine, with its image on the left and one row per model year on the right.
    li = {year: Lemon Index} (only years with enough complaints), yt = {year: YouTube rank #} (only rankable years), pages = years with a page."""
    gs = engines(fid)
    if not gs: return ''
    mx = max([120] + [v * 1.08 for v in li.values()])
    out = []
    for g in gs:
        im = g.get('img') or {}
        rows = []
        for y in g['years']:
            v = li.get(y); r = yt.get(y)
            c = (f'<span class="er-bt"><i style="width:{min(100, v / mx * 100):.1f}%"></i><em style="left:{100 / mx * 100:.1f}%"></em></span><b>{v}</b>' if v is not None else '<span class="er-bt na"></span><b class="mute"></b>')
            t = f'<b class="er-rk">#{r}</b>' if r is not None else '<b class="er-rk mute">·</b>'
            tag = 'a' if y in pages else 'div'; href = f' href="/cars/{fid}/{y}/"' if y in pages else ''
            rows.append(f'<{tag} class="er{" " + cls(v) if v is not None else ""}{" cur" if y == cur else ""}"{href}><span class="er-y">{y}</span>{c}{t}</{tag}>')
        img = (f'<span class="eg-im"><img src="{E(im["src"])}" alt="{E(name)} {E(g["name"])} engine illustration" width="{im["w"]}" height="{im["h"]}" loading="lazy" decoding="async">'
               + _info(f'Illustration (AI-generated) of the {E(name)} {E(g["name"])} engine, not a photo of a specific engine. Free to use under <a href="{LIC}" rel="license noopener">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>')
               + '</span>') if im else ''
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

def _tabs(panels, label):
    """panels = [(id, tab label, html)] -> tab bar + panels. The first is open by default."""
    panels = [p for p in panels if p[2].strip()]
    bar = ''.join(f'<button class="tb-t" role="tab" id="t-{i}" aria-controls="p-{i}" data-h="{i}" aria-selected="{"true" if n == 0 else "false"}" tabindex="{0 if n == 0 else -1}">{E(t)}</button>' for n, (i, t, _) in enumerate(panels))
    body = ''.join(f'<section class="tb-p{" on" if n == 0 else ""}" role="tabpanel" id="p-{i}" aria-labelledby="t-{i}" tabindex="0">{h}</section>' for n, (i, t, h) in enumerate(panels))
    return f'<div class="tbx"><div class="tb-bar" role="tablist" aria-label="{E(label)}">{bar}</div>{body}</div>'

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
    sl = _s(slider).replace('>Best year<', '>Safest year<')   # the slider opens on the site's safest year (complaints + YouTube); 'Best year' below means fewest complaints
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
    tabs = _tabs([('overview', 'Overview', over), ('years', 'Years & engines', ''.join(map(str, years))), ('compare', 'Compare', ''.join(map(str, cmp_))),
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
    hero = f'<section class="ph tb-hero">{_s(crumbs)}<div class="tb-img">{img}</div>{_s(h1)}{_s(early)}{_s(yhero)}{_s(sw)}{_s(modes)}</section>'   # the gauge + verdict already say it: no answer paragraph
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
                  ('recalls', 'Recalls & safety', J(rec)), ('years', 'Every year', J(yrs)), ('questions', 'Questions', J(qa))], 'Report sections')
    cls = ' '.join(root.get('class') or [])
    return f'{ASSET}<article class="{cls} tbl">{hero}{tabs}{J(tail)}</article>'
