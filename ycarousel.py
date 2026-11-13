# 11-12 (Elijah: "make the overview much better ... for a guy looking at these cars"). Runs on the tabbed model and year pages after tabbed.py:
#  - year pages: the year switcher under the verdict becomes an image carousel at the top. This year's car in the middle, last year's and
#    next year's peeking in half cut off at the edges; arrows, a tap on a peeking car or a swipe go to that year's page (assets/ycar.js).
#  - model pages: the verdict ("Is the <car> reliable?" + gauge) moves above the year slider, and the slider becomes one "year explorer":
#    the car, its year's numbers and a scrubber that IS the every-year chart (one bar per year, taller = more complaints per car sold).
#  - model pages: "What owners say on YouTube" opens the Overview tab: YouTube rank vs. cars the same age, YouTube's favorite and least-liked
#    years, and per generation what owners praise and complain about (data/yt_buyer.json), the fixes they look up (data/yt.json) and the
#    videos to watch before buying. Models we haven't pulled yet say so.
# Classes: ycr-* (carousel), yx-* (explorer), yot-* (YouTube block); CSS/JS in assets/ycar.css and assets/ycar.js.
import json, html, os, re
from bs4 import BeautifulSoup
E = lambda s: html.escape(str(s), quote=True)
HERE = os.path.dirname(os.path.abspath(__file__))
ASSET = '<link rel="stylesheet" href="/assets/ycar.css?v=1"><script src="/assets/ycar.js?v=1" defer></script>'
try: YB = json.load(open(os.path.join(HERE, 'data', 'yt_buyer.json'), encoding='utf-8'))
except FileNotFoundError: YB = {}
ORD = lambda n: f'{n}{"th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")}'

_CROP = {}
def crop(srcs):
    """the share of empty space above the car that EVERY picture in this set has (all are 1000x600 canvases, car on a shared baseline);
    trimming it moves the car up without cutting a roof. 0 when a picture can't be read."""
    k = tuple(sorted(set(srcs)))
    if k in _CROP: return _CROP[k]
    try:
        from PIL import Image
        tops = []
        for src in k:
            a = Image.open(os.path.join(HERE, src.split('?')[0].lstrip('/'))).convert('RGBA'); bb = a.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
            if not bb or bb == (0, 0) + a.size: bb = a.convert('L').point(lambda v: 255 if v < 245 else 0).getbbox()
            tops.append(bb[1] / a.size[1] if bb else 0)
        c = max(0, round(min(tops) - .03, 2)) if tops else 0
    except Exception: c = 0
    _CROP[k] = c; return c
def _ar(c): h = round(600 * (1 - c)); return f'--ar:1000 / {h};--arn:{1000 / h:.3f}'

def _vw(n): return f'{n / 1e6:.1f}M' if n >= 1e6 else f'{round(n / 1e3):,}K' if n >= 1e3 else str(n)
def _cls(li): return 'na' if li is None else 'bad' if li > 110 else 'good'

# ------------------------------------------------------------------ year page: carousel
def _item(c, it, role):
    """one car in the carousel; role = 'p' (previous), 'c' (this year), 'n' (next). 11-12 v2 (Elijah): the middle car has no year label
    (the title says it); the peeking cars carry a small one and only show on wide screens."""
    if not it: return f'<span class="ycr-it ycr-{role} ycr-none" aria-hidden="true"></span>'
    img = (f'<img src="{E(it["src"])}" alt="{it["y"]} {E(c["name"])}' + (f', {E(it["gen"])}' if it.get('gen') else '') + ', illustration" width="1000" height="600" '
           + ('fetchpriority="high" decoding="async"' if role == 'c' else 'loading="lazy" decoding="async"') + '>')
    if role == 'c': return f'<div class="ycr-it ycr-c" aria-current="page">{img}{{INFO}}</div>'
    word = 'Previous' if role == 'p' else 'Next'
    return f'<a class="ycr-it ycr-{role}" href="{E(it["url"])}" aria-label="{word} year: the {it["y"]} {E(c["name"])} report" tabindex="-1">{img}<span class="ycr-y"><b>{it["y"]}</b></span></a>'

_SVG = lambda d, s=22: (f'<svg viewBox="0 0 24 24" width="{s}" height="{s}" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
                        f'<path d="{"M15 5l-7 7 7 7" if d == "p" else "M9 5l7 7-7 7"}"/></svg>')
_MORE = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>')

def _nav_row(s, items):
    """11-12 v2 (Elijah: one navigation system on phones): the page's actions (All years, Compare, Share, Advanced) leave the hero and ride
    at the end of the sticky tab row: one item = a chip, more = a 'More' button with a small sheet. Wide screens keep the hero buttons."""
    row = s.find(class_='tb-row')
    if row is None or not items: return False
    if len(items) == 1: body = f'<div class="ycn">{items[0]}</div>'
    else: body = (f'<div class="ycn"><button type="button" class="ycn-b" aria-expanded="false" aria-controls="ycn-s">{_MORE}<span>More</span></button>'
                  f'<div class="ycn-s" id="ycn-s" role="menu" hidden>{"".join(items)}</div></div>')
    row.append(BeautifulSoup(body, 'html.parser')); return True

def year_page(out, c, y):
    """c = context from build.py (_yc_ctx). Leaves the page as it is when this year has no picture."""
    ys = c['years']; idx = next((i for i, v in enumerate(ys) if v['y'] == y), None)
    if idx is None or not ys[idx].get('src'): return out
    s = BeautifulSoup(out, 'html.parser'); hero = s.find('section', class_='tb-hero')
    if hero is None: return out
    box = hero.find(class_='tb-img')
    if box is None: return out
    fig = box.find('figure'); info = ''
    if fig is not None:
        b = fig.find('button', class_='ii'); p = fig.find(class_='ii-pop'); info = (str(b) if b else '') + (str(p) if p else ''); fig.decompose()
    yp = ys[idx - 1] if idx else None; yn = ys[idx + 1] if idx + 1 < len(ys) else None   # the title arrows: the neighbouring report pages
    prev = yp if yp and yp.get('src') else None; nxt = yn if yn and yn.get('src') else None   # the peeking cars: neighbours with a picture
    car = (f'<div class="ycr" style="{_ar(crop([v["src"] for v in ys if v.get("src")]))}" role="group" aria-roledescription="carousel" aria-label="{E(c["short"])} model years"'
           + (f' data-prev="{E(yp["url"])}"' if yp else '') + (f' data-next="{E(yn["url"])}"' if yn else '') + '>'
           f'<div class="ycr-track">{_item(c, prev, "p")}{_item(c, ys[idx], "c").replace("{INFO}", info)}{_item(c, nxt, "n")}</div></div>'
           + ''.join(f'<link rel="prefetch" href="{E(it["url"])}">' for it in (yp, yn) if it))
    box.insert(0, BeautifulSoup(ASSET + car, 'html.parser')); box['class'] = box.get('class', []) + ['ycr-box']
    hero['class'] = hero.get('class', []) + ['yc-hero']
    # one big title with the year arrows around it (the H1 text stays as the title template writes it)
    h1 = hero.find('h1')
    if h1 is not None:
        arr = lambda it, d: (f'<a class="yct-a yct-{d}" href="{E(it["url"])}" aria-label="{"Previous" if d == "p" else "Next"} year: {it["y"]} {E(c["name"])}" rel="{"prev" if d == "p" else "next"}" data-dir="{d}">{_SVG(d)}</a>'
                             if it else f'<span class="yct-a yct-{d} yct-x" aria-hidden="true">{_SVG(d)}</span>')
        frag = BeautifulSoup(f'<div class="yct">{arr(yp, "p")}<span class="yct-h"></span>{arr(yn, "n")}</div>'
                             + (f'<p class="yct-g">{E(ys[idx]["gen"])}</p>' if ys[idx].get('gen') else ''), 'html.parser')
        yct = frag.find(class_='yct'); gl = frag.find('p', class_='yct-g')
        h1.insert_before(yct.extract()); yct.find(class_='yct-h').replace_with(h1.extract())
        if gl is not None: yct.insert_after(gl.extract())
    _split_title(hero.find('h1')); _chips(hero)
    # the verdict in one short line: band word + the top complaint area (A's band words stay as written)
    vd = hero.select_one('.yverd p.yvd')
    if vd is not None and vd.find('b') is not None:
        word = vd.find('b').get_text(strip=True).rstrip('.'); top = ys[idx].get('top')
        vd.clear(); vd.append(BeautifulSoup(f'<b>{E(word)}</b>' + (f' <span>· most complaints: {E(top)}</span>' if top else ''), 'html.parser'))
    seg = hero.find(class_='yseg')   # the old '‹ 2000 · 2001 · 2002 ›' row: the title arrows do that now
    if seg is not None: seg.decompose()
    acts = hero.select_one('.tb-ctl .tb-acts')
    if acts is not None and _nav_row(s, [str(a) for a in acts.find_all(recursive=False)]):
        hero.select_one('.tb-ctl')['class'] = hero.select_one('.tb-ctl').get('class', []) + ['ycn-wide']
    return str(s)


# ------------------------------------------------------------------ 11-12 v3 (Elijah): calmer heroes
def _split_title(h1):
    """'2016 Honda Civic reliability.' -> the car name big, the search word small and grey on the line under it. Same H1, same text
    (the search-titles agent's template), only wrapped in two spans."""
    if h1 is None or h1.find(class_='yct-big') is not None: return
    inner = h1.decode_contents().strip()
    if '<' in inner or ' ' not in inner: return
    big, word = inner.rsplit(' ', 1)
    h1.clear(); h1.append(BeautifulSoup(f'<span class="yct-big">{big}</span> <span class="yct-sw">{word}</span>', 'html.parser'))
    h1['class'] = h1.get('class', []) + ['yct-h1']

_CHIP = {'Fewest complaints': 'Fewest', 'Most complaints': 'Most', 'Fewer complaints nearby': 'Better nearby', 'Fewest of any year': 'Fewest',
         'Fewest complaints nearby': 'Fewest nearby'}
def _chips(hero):
    """the 'Fewest complaints 2011 · Most complaints 2022' sentence -> two small chips"""
    bw = hero.select_one('.yverd .ybw')
    if bw is None or not bw.find('a'): return
    out = []; lab = ''
    for n in bw.children:
        if getattr(n, 'name', None) == 'a':
            l = re.sub(r'\s+', ' ', lab).strip(' ·'); out.append(f'<a class="yb2 {" ".join(n.get("class") or [])}" href="{E(n.get("href", "#"))}"><span>{E(_CHIP.get(l, l))}</span> <b>{E(n.get_text(strip=True))}</b></a>'); lab = ''
        else: lab += n.get_text() if hasattr(n, 'get_text') else str(n)
    bw.replace_with(BeautifulSoup(f'<p class="ybw yb2s">{"".join(out)}</p>', 'html.parser'))

# ------------------------------------------------------------------ model page: verdict first, year explorer, YouTube in Overview
def _explorer(c, d, best):
    ys = d['years']; si = next((i for i, v in enumerate(ys) if v['y'] == c.get('start')), 0); v0 = ys[si]
    rk = c.get('yt_rank') or {}; nrk = len(rk)
    li_of = {v['y']: v.get('li') for v in c['years']}
    for v in ys: v['li'] = li_of.get(v['y'], v.get('li')); v['rk'] = rk.get(v['y']); v['n'] = nrk
    mx = max([v['li'] for v in ys if v.get('li') is not None] + [150])
    def bar(i, v):
        h = 8 if v.get('li') is None else max(10, min(100, round(v['li'] / mx * 100)))
        return f'<i class="{_cls(v.get("li"))}{" on" if i == si else ""}" style="--h:{h}%"></i>'
    def ytxt(v): return f'YouTube #{v["rk"]} of {nrk}' if v.get('rk') else ''
    li = v0.get('li')
    info = (f'<div class="yx-info"><span class="yx-li {_cls(li)}">' + (f'Lemon Index {li}' if li is not None else f'No score for {v0["y"]}') + '</span>'
            f'<span class="yx-yt"{"" if v0.get("rk") else " hidden"}>{ytxt(v0)}</span>'
            f'<span class="yx-best"{"" if v0["y"] == best else " hidden"}>Fewest complaints</span>'
            + (f'<a class="yx-go" href="{E(v0["url"])}">See the {v0["y"]} report ›</a>' if v0.get('url') else '<a class="yx-go" href="#" hidden></a>') + '</div>')
    nav = lambda dd: (f'<button type="button" class="yx-st yx-s{dd}" aria-label="{"Previous" if dd == "p" else "Next"} year"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" '
                      f'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="{"M15 5l-7 7 7 7" if dd == "p" else "M9 5l7 7-7 7"}"/></svg></button>')
    return (f'<section class="yx" aria-label="Every {E(c["short"])}, year by year">'
            f'<div class="yx-stage" style="{_ar(crop([v["src"] for v in ys]))}"><img class="on" src="{E(v0["src"])}" alt="{v0["y"]} {E(c["name"])} illustration" width="1000" height="600" fetchpriority="high"><img alt="" width="1000" height="600" aria-hidden="true">'
            f'{nav("p")}{nav("n")}{{INFO}}</div>'
            f'<p class="yx-yr"><b>{v0["y"]}</b><span class="yx-gen">{E(v0.get("gen") or "")}</span></p>{info}'
            f'<div class="yx-strip"><div class="yx-bars" aria-hidden="true">{"".join(bar(i, v) for i, v in enumerate(ys))}</div>'
            f'<input class="yx-r" type="range" min="0" max="{len(ys) - 1}" step="1" value="{si}" aria-label="Model year" aria-valuetext="{v0["y"]}"></div>'
            f'<div class="yx-ends"><span>{ys[0]["y"]}</span><span class="yx-key">Taller bar = more complaints per car sold</span><span>{ys[-1]["y"]}</span></div>'
            f'<script type="application/json" class="yx-data">{json.dumps({"name": c["name"], "best": best, "years": [{k: v.get(k) for k in ("y", "src", "gen", "li", "rk", "n", "url")} for v in ys]})}</script></section>')

def _bars(rows, cls):
    if not rows: return '<p class="yot-none">Nothing stands out.</p>'
    mx = max(p for _, p in rows) or 1
    return ''.join(f'<div class="yot-b {cls}"><span>{E(k)}</span><i style="--w:{round(100 * p / mx)}%"></i><b>{p}%</b></div>' for k, p in rows)

def _vid(v, ch_key='ch'):
    return (f'<a class="yot-v" href="https://www.youtube.com/watch?v={E(v["id"])}" target="_blank" rel="noopener nofollow">'
            f'<img src="https://i.ytimg.com/vi/{E(v["id"])}/mqdefault.jpg" alt="" width="320" height="180" loading="lazy" decoding="async">'
            f'<span>{E(v["title"])}</span><small>{E(v.get(ch_key) or v.get("channel") or "")} · {_vw(v.get("views") or 0)} views</small></a>')

def _gn(g):
    m = re.search(r'-g(\d+)$', g['sid']); return f'{ORD(int(m.group(1)))} gen' if m else 'generation'

def yt_block(c):
    """'What owners say on YouTube' for the model Overview. '' never: a model without a study says it's coming."""
    fid, short = c['fid'], c['short']; gens = YB.get(fid) or []
    first = min(v['y'] for v in c['years']); gens = [g for g in gens if g['y1'] >= first - 8]   # the generations a used buyer can still find
    rk = c.get('yt_rank') or {}; ytr = c.get('ytr'); ytv = c.get('ytv') or []
    h2 = '<h2 class="yot-h">What owners say on YouTube</h2>'
    if not gens and not rk:
        return (f'<section class="yot yot-q" id="youtube"><p><b>What owners say on YouTube:</b> we haven&#39;t studied {E(c["name"])} videos yet. When that study runs, '
                'the most-watched owner reviews and buyer guides for each generation, and what owners praise and complain about, show up here.</p></section>')
    tiles = []
    if ytr:
        r, n, vids = ytr; cl = 'good' if r <= n / 3 else 'bad' if r > n * 2 / 3 else ''
        tiles.append(f'<div class="yot-t big {cl}"><b>#{r}<i> of {n}</i></b><span>YouTube owner tone vs. cars the same age · {vids:,} videos</span></div>')
    prk = {y: r for y, r in rk.items() if any(v['y'] == y for v in c['years'])}   # years a used buyer can open a report for (not a 1997 restoration video)
    if len(prk) >= 3:
        top = min(prk, key=prk.get); low = max(prk, key=prk.get)
        tiles.append(f'<a class="yot-t good" href="{E(c["url"](top))}"><b>{top}</b><span>YouTube&#39;s favorite year</span></a>')
        tiles.append(f'<a class="yot-t bad" href="{E(c["url"](low))}"><b>{low}</b><span>Least-liked year on YouTube</span></a>')
    pop = c.get('start'); gi = next((i for i, g in enumerate(gens) if pop and g['y0'] <= pop <= g['y1']), len(gens) - 1)
    chips = ''.join(f'<button type="button" class="yot-g" data-i="{i}" aria-pressed="{"true" if i == gi else "false"}"><b>{E(g["label"])}</b><span>{_gn(g)}</span></button>'
                    for i, g in enumerate(gens)) if len(gens) > 1 else ''
    panes = []
    for i, g in enumerate(gens):
        yy = set(range(g['y0'], g['y1'] + 1))
        e = next((e for e in ytv if e.get('years') and yy & set(e['years'])), None)   # data/yt.json: fixes owners look up + buyer guides for this generation
        fixes = ''
        if e and e.get('topics'):
            fixes = ('<h3>Fixes owners look up most</h3><ol class="yot-fx">' + ''.join(
                f'<li><a href="https://www.youtube.com/watch?v={E(t["best"]["id"])}" target="_blank" rel="noopener nofollow"><b>{E(t["name"])}</b><span>{_vw(t["views"])} views</span></a></li>'
                for t in e['topics'][:3]) + '</ol>')
        vids = (e or {}).get('guides') or []
        vids = ''.join(_vid(v, 'channel') for v in vids[:3]) if vids else ''.join(_vid(v) for v in g.get('top', [])[:3])
        panes.append(f'<div class="yot-p{" on" if i == gi else ""}" data-i="{i}"{"" if i == gi else " hidden"}>'
                     f'<p class="yot-n">{E(g["label"])} {E(short)} · {g["videos"]} most-watched videos</p>'
                     f'<div class="yot-pc"><div><h3>Owners praise</h3>{_bars(g.get("praise"), "gd")}</div><div><h3>Owners complain about</h3>{_bars(g.get("trouble"), "bd")}</div></div>'
                     f'{fixes}' + (f'<h3>Before you buy, watch</h3><div class="yot-vs">{vids}</div>' if vids else '') + '</div>')
    cap = ('<p class="yot-cap">Praise and complaints: the share of each generation&#39;s most-watched videos that mention a topic with a praise or trouble word next to it, '
           'in the title or what&#39;s said. YouTube rank: how positive owners and reviewers sound, compared with every car of the same model year. It measures tone, not failure rates. '
           'Videos belong to their creators; we link to them.</p>')
    return (f'<section class="yot" id="youtube">{h2}' + (f'<div class="yot-ts">{"".join(tiles)}</div>' if tiles else '')
            + (f'<div class="yot-gs" role="group" aria-label="Generation">{chips}</div>' if chips else '') + ''.join(panes) + (cap if gens else '') + '</section>')

def model_page(out, c):
    s = BeautifulSoup(out, 'html.parser'); hero = s.find('section', class_='tb-hero')
    if hero is None: return out
    box = hero.find(class_='tb-img'); ysl = box.find('section', class_='ysl') if box else None
    if ysl is not None:   # the slider -> one year explorer
        try: d = json.loads(ysl.find('script', class_='ysl-data').string)
        except Exception: d = None
        if d:
            ii = ysl.find('button', class_='ii'); pop = ysl.find(class_='ii-pop')
            new = _explorer(c, d, d.get('best')).replace('{INFO}', (str(ii) if ii else '') + (str(pop) if pop else ''))
            for sc in box.find_all('script', src=re.compile('yslider')): sc.decompose()
            ysl.replace_with(BeautifulSoup(new, 'html.parser'))
    if box is not None:   # verdict first (Elijah): crumbs, question, answer, gauge, then the cars
        box.extract(); anchor = hero.find(class_='yhero') or hero.find('p', class_='tb-ans') or hero.find('h1')
        if anchor is not None: anchor.insert_after(box)
        else: hero.append(box)
    hero['class'] = hero.get('class', []) + ['yx-hero', 'yc-hero']
    vb = hero.select_one('.yverd > p:first-child')   # 11-12 v3: 'Better than average · 2010–2022' (the answer above already says how many complaints)
    if vb is not None and vb.find('b') is not None:
        word = vb.find('b').get_text(strip=True).rstrip('.'); yrs = re.search(r'(\d{4})\s*[-–]\s*(\d{4})', vb.get_text())
        vb.clear(); vb.append(BeautifulSoup(f'<b>{E(word)}</b>' + (f' <span>· {yrs.group(1)}–{yrs.group(2)}</span>' if yrs else ''), 'html.parser'))
    an = hero.find('p', class_='tb-ans')   # one short answer: 'Is it reliable? Yes. It draws 1.5x fewer complaints than average.'
    if an is not None:
        h = an.decode_contents()
        h = re.sub(r',\s*(and|but)\s+YouTube owners[^.<]*', '', h)
        h = re.sub(r'\s*Fewest complaints:.*$', '', h, flags=re.S)
        h = h.replace('It draws ', '').replace('It drew ', '')
        h = re.sub(r'(</b>\s*)([a-z])', lambda m: m.group(1) + m.group(2).upper(), h, count=1)   # '... Yes.</b> About two-thirds as many ...'
        an.clear(); an.append(BeautifulSoup(h.strip(), 'html.parser'))
    _split_title(hero.find('h1')); _chips(hero)
    sh = next((b for b in hero.find_all('button', attrs={'data-share': True})), None)   # phones: Share rides at the end of the tab row
    if sh is not None and _nav_row(s, [str(sh).replace('btn btn-ghost', 'tb-ic').replace('>Share ↗<', '><span class="tb-ic-l">Share</span><')]):
        sh.parent['class'] = sh.parent.get('class', []) + ['ycn-wide']
    ov = s.find(id='p-overview')
    if ov is not None:
        yb = yt_block(c)
        if 'yot-q' in yb: ov.append(BeautifulSoup(yb, 'html.parser'))   # nothing studied yet: a quiet line under the cards
        else: ov.insert(0, BeautifulSoup(yb, 'html.parser'))
    hero.insert(0, BeautifulSoup(ASSET, 'html.parser'))
    return str(s)
