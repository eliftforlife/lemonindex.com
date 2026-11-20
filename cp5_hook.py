# 11-19 v5 (Elijah: "do the same to these pages"): the symptom, engine-code and repair-cost pages (article.study.tr2.cp2) get the v5 look
# in one place. exec'd from build.py after the V5_* helpers; page() calls CP5_HOOK(body) before the date hash.
#   - the first section (and any section with a car grid or a filter box) stays open, with a big centered heading
#   - every other section, each "The details" item, Quick answers and the closing source note become title-only tap-to-open boxes
#   - the black readout card above (.creadout / .rcp-read) turns light (CSS in assets/cpl.css, .cp5)
# Text, links and headings stay in the HTML (inside <details>), so search engines still read all of it.
from bs4 import BeautifulSoup as _C5S

_C5_ICONS = [(r'paid|cost|price|bill', 'tag'), (r'model year|by year', 'calendar'), (r'share', 'chart'), (r'code', 'engine'),
             (r'symptom', 'warning'), (r'related|keep going|more', 'signpost'), (r'often|when', 'history'), (r'cause|fix|shop|repair', 'wrench'),
             (r'cars|models|model', 'car'), (r'safe|serious|drive', 'warning')]


def _c5_ic(t):
    for pat, ic in _C5_ICONS:
        if re.search(pat, t, re.I): return ic
    return 'info'


def CP5_HOOK(body):
    i = body.find('<article class="study tr2 cp2')
    if i < 0: return body
    j = body.find('</article>', i)
    if j < 0: return body
    so = _C5S(body[i:j + len('</article>')], 'html.parser'); art = so.article
    if not art: return body
    kids = [c for c in art.children if getattr(c, 'name', None)]
    head, groups, tail, cur = [], [], [], None
    for c in kids:
        cls = c.get('class') or []
        if c.name == 'h2':
            cur = {'t': c.get_text(' ', strip=True), 'id': c.get('id'), 'h': c, 'els': []}; groups.append(cur); continue
        if c.name == 'section' and 'yqa' in cls:
            cur = None; groups.append({'qa': c}); continue
        if cur is None: (tail if groups else head).append(c)
        else: cur['els'].append(c)
    if not groups: return body
    seen, vis, boxes = 0, [], []
    for g in groups:
        if 'qa' in g:
            q = g['qa']; h = q.find('h2')
            if h: h.decompose()
            boxes.append(V5_BOX('talk', 'Questions', q.decode_contents(), 'questions', h2=True)); continue
        inner = ''.join(str(e) for e in g['els'])
        keep = seen == 0 or any(e.name == 'div' and 'mbs' in (e.get('class') or []) for e in g['els']) or 'class="cf-q' in inner
        seen += 1
        if keep:
            lx = [e for e in g['els'] if 'cpx' in (e.get('class') or [])]   # the code pages' link lists (by model, symptoms, years) go in a box
            if lx:
                inner = ''.join(str(e) for e in g['els'] if e not in lx)
                boxes.append(V5_BOX('signpost', 'More pages about this code', ''.join(str(e) for e in lx), 'more'))
            vis.append(f'<section class="cp5-sec"' + (f' id="{g["id"]}"' if g['id'] else '') + f'><h2>{g["h"].decode_contents()}</h2>{inner}</section>'); continue
        cpd = [e for e in g['els'] if e.name == 'details' and 'cpd' in (e.get('class') or [])]
        if cpd and len(cpd) == len(g['els']):   # "The details": each item becomes its own box
            for d in cpd:
                sm = d.find('summary'); t = sm.get_text(' ', strip=True) if sm else g['t']
                if sm: sm.decompose()
                boxes.append(V5_BOX(_c5_ic(t), html.escape(t), d.decode_contents()))
            continue
        boxes.append(V5_BOX(_c5_ic(g['t']), g['h'].decode_contents(), inner, g['id'] or '', h2=True))
    after = []
    for e in tail:
        if e.name == 'p' and 'note' in (e.get('class') or []): boxes.append(V5_BOX('info', 'Where this data comes from', f'<p class="yc-cap">{e.decode_contents()}</p>'))
        else: after.append(str(e))
    cls = ' '.join(art.get('class') or []) + ' cp5'
    new = (f'<article class="{cls}">' + ''.join(str(e) for e in head) + ''.join(vis)
           + (f'<div class="cpl cp5-pl">{"".join(boxes)}</div>' if boxes else '') + ''.join(after) + '</article>')
    return body[:i] + new + body[j + len('</article>'):]


# 11-19 v5, engine pages (article.study.tr2.eng2, engine_pages.py): hero + tiles, then the by-year chart open under a big centered
# heading, then every box. The "Cars with this engine" year links, Quick answers and the source note become boxes too.
def ENG5_HOOK(body):
    i = body.find('<article class="study tr2 eng2')
    if i < 0: return body
    j = body.find('</article>', i)
    if j < 0: return body
    art = _C5S(body[i:j + len('</article>')], 'html.parser').article
    if not art: return body
    head, chart, secs, mid, cars, qa, cap = [], [], [], [], None, None, []
    for c in [c for c in art.children if getattr(c, 'name', None)]:
        cls = c.get('class') or []
        if 'n3-eng' in cls: cars = c
        elif 'yqa' in cls: qa = c
        elif 'cpl-sec' in cls: secs.append(str(c))
        elif c.name == 'h2' or (chart and c.name == 'div' and ('egc' in cls or 'cpl-eng' in cls)): chart.append(c)
        elif c.name == 'p' and 'yc-cap' in cls and (chart or secs): cap.append(c)
        elif not chart and not secs: head.append(str(c))
        else: mid.append(str(c))
    out = ''.join(head)
    if chart:
        h = chart[0]
        # the h2 stays a direct child: engine_pills.ENG_HOOK (runs later) boxes the notes that follow it ("How to read this chart")
        out += (f'<h2 class="cp5-h">{h.decode_contents()}</h2>' + ''.join(str(e) for e in chart[1:])) if h.name == 'h2' else ''.join(str(e) for e in chart)
    out += ''.join(secs) + ''.join(mid)
    boxes = ''
    if cars:
        h = cars.find('h2'); sub = h.find('span', class_='h2s') if h else None
        sub_t = sub.get_text(' ', strip=True) if sub else ''
        if sub: sub.decompose()
        t = h.decode_contents().strip() if h else 'Cars with this engine'
        if h: h.decompose()
        boxes += V5_BOX('car', t, (f'<p class="yc-cap">{html.escape(sub_t)}</p>' if sub_t else '') + cars.decode_contents(), 'eng-cars', h2=True)
    if qa:
        h = qa.find('h2')
        if h: h.decompose()
        boxes += V5_BOX('talk', 'Quick answers', qa.decode_contents(), 'questions', h2=True)
    for p in cap: boxes += V5_BOX('info', 'Where this data comes from', f'<p class="yc-cap">{p.decode_contents()}</p>')
    if boxes: out += f'<section class="cpl-sec"><div class="cpl">{boxes}</div></section>'
    cls = ' '.join(art.get('class') or []) + ' cp5 eng5'
    return body[:i] + f'<article class="{cls}">' + out + '</article>' + body[j + len('</article>'):]


# 11-19 v5 ranked rows (polish list A2-A4): rank, small photo, name + one small line, score on the right. Each row is one link.
def V5_RANK(items, start=1):
    """items: dicts {href, ph, title, sub, score, cls}; ph from aph()/mphoto() (may be None)."""
    out = []
    for i, it in enumerate(items, start):
        ph = it.get('ph')
        th = (f'<img src="{rsmall(ph["src"])}" alt="" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async">' if ph else '')
        out.append(f'<li><a href="{it["href"]}"><span class="rk5-n">{i}</span><span class="rk5-p">{th}</span>'
                   f'<span class="rk5-t"><b>{it["title"]}</b>' + (f'<small>{it["sub"]}</small>' if it.get('sub') else '') + '</span>'
                   + (f'<b class="rk5-s {it.get("cls", "")}">{it["score"]}</b>' if it.get('score') not in (None, '') else '') + '</a></li>')
    return f'<ol class="rk5" start="{start}">' + ''.join(out) + '</ol>'


# 11-19 v5 (polish list A3): every /best/ list (best_ui.py: div.advp.cb.cbx). Hero with the #1 car's picture, the first ranked list open
# under a big centered heading ("At a glance" chart folded into a box above the cards), every other section a box. Same words and links.
_CBX_IC = [(r'complaint|other end', 'warning'), (r'type', 'car'), (r'question|answer', 'talk'), (r'before you buy', 'signpost'), (r'budget', 'tag')]
def CBX5_HOOK(body):
    i = body.find('<div class="advp cb cbx">')
    if i < 0: return body
    so = _C5S(body[i:], 'html.parser'); d = so.find('div', class_='advp')
    if d is None: return body
    end = i + len(str(d)) if body[i:].startswith(str(d)) else -1
    hd = d.find('header', class_='cbx-h', recursive=False)
    first = d.find('section', class_='cbx-list', recursive=False)
    im = first.find('img') if first else None
    vis, boxes, keep = [], [], []
    for c_ in [x for x in d.children if getattr(x, 'name', None)]:
        cls = c_.get('class') or []
        if c_ is hd:
            k = hd.find(class_='ph-e'); h1 = hd.find('h1'); ln = hd.find(class_='cbx-line')
            ph = ''
            if im is not None:
                ph = (f'<div class="v5-im"><img src="{im["src"]}" alt="{im.get("alt", "")}" width="{im.get("width", 1000)}" height="{im.get("height", 600)}" decoding="async"></div>')
            vis.append(V5_HERO(k.decode_contents() if k else '', h1.decode_contents() if h1 else '', ln.decode_contents() if ln else '', extra=ph))
        elif c_ is first:
            h = c_.find('h2'); ch = c_.find('div', class_='cbx-chart')
            if ch is not None:
                ch.extract(); boxes.insert(0, V5_BOX('chart', 'At a glance', str(ch), 'glance'))
            ht = h.decode_contents() if h else ''
            if h: h.decompose()
            vis.append(f'<section class="cp5-sec cbx-list"><h2>{ht}</h2>' + (''.join(boxes) and f'<div class="cpl cp5-pl cbx5-g">{boxes.pop(0)}</div>') + c_.decode_contents() + '</section>')
        elif c_.name == 'section' and 'cbx-sec' in cls:
            h = c_.find('h2'); t = h.get_text(' ', strip=True) if h else ''
            ht = h.decode_contents() if h else t
            if h: h.decompose()
            ic = next((v for p, v in _CBX_IC if re.search(p, t, re.I)), 'info')
            boxes.append(V5_BOX(ic, ht, c_.decode_contents(), c_.get('id') or '', h2=True))
        elif 'cbx-srcrow' in cls:
            pop = c_.find(class_='cb-pop')
            boxes.append(V5_BOX('info', 'Sources and method', f'<p class="yc-cap">{pop.decode_contents() if pop else c_.decode_contents()}</p>'))
        else: keep.append(str(c_))
    new = (f'<div class="advp cb cbx v5 cbx5">' + ''.join(keep) + ''.join(vis) + (f'<div class="cpl v5-pl">{"".join(boxes)}</div>' if boxes else '') + '</div>')
    s = str(so); j = s.find(str(d))
    return body[:i] + s[:j] + new + s[j + len(str(d)):]


# 11-19 v5 (polish list A5, A9): the info pages. Two shapes:
#   div.pg > section.ph + article.study with top-level h2s (car loans, data)  -> group by h2 (a <section> with its own h2 is its own group)
#   div.advp > header.advh1 + section.yc (about, press, images)                -> the header becomes the v5 hero, each section a group
# The first KEEP groups stay open under big centered headings, the rest become boxes that keep their h2. Same words, links and ids.
INFO5_KEEP = {'/car-loan-rates/': 1, '/data/': 2, '/about/': 1, '/press/': 2, '/images/': 0}
def _i5_groups(kids):
    pre, groups, cur = [], [], None
    for c_ in kids:
        cls = c_.get('class') or []
        if c_.name == 'h2':
            cur = {'h': c_.decode_contents(), 't': c_.get_text(' ', strip=True), 'id': c_.get('id') or '', 'els': []}; groups.append(cur); continue
        if c_.name == 'section' and c_.find('h2', recursive=False) is not None:
            h = c_.find('h2', recursive=False); ht, tt = h.decode_contents(), h.get_text(' ', strip=True); h.decompose()
            groups.append({'h': ht, 't': tt, 'id': c_.get('id') or '', 'els': [c_], 'sec': True}); cur = None; continue
        if cur is None:
            if groups: groups[-1]['els'].append(c_)
            else: pre.append(c_)
        else: cur['els'].append(c_)
    return pre, groups
def _i5_render(groups, keep, loan=False):
    vis, boxes = [], []
    n = 0
    for g in groups:
        inner = (g['els'][0].decode_contents() + ''.join(str(e) for e in g['els'][1:])) if g.get('sec') else ''.join(str(e) for e in g['els'])
        if n < keep:
            if loan:   # the same rates as a table (with monthly payments) go in a box under the chart
                tw = [e for e in g['els'] if e.name == 'div' and 'tw' in (e.get('class') or [])]
                if tw:
                    inner = ''.join(str(e) for e in g['els'] if e not in tw)
                    inner += '<div class="cpl cp5-pl i5-in">' + V5_BOX('data', 'Rates and monthly payments, as a table', ''.join(str(e) for e in tw), 'rates-table') + '</div>'
            vis.append(f'<section class="cp5-sec"' + (f' id="{g["id"]}"' if g['id'] else '') + f'><h2>{g["h"]}</h2>{inner}</section>')
        else:
            boxes.append(V5_BOX(_c5_ic(g['t']), g['h'], inner, g['id'], h2=True))
        n += 1
    return ''.join(vis), boxes
def INFO5_HOOK(path, body):
    keep = INFO5_KEEP.get(path)
    if keep is None: return body
    if '<article class="study">' in body:
        i = body.find('<article class="study">'); j = body.find('</article>', i)
        art = _C5S(body[i:j + 10], 'html.parser').article
        pre, groups = _i5_groups([x for x in art.children if getattr(x, 'name', None)])
        vis, boxes = _i5_render(groups, keep, loan=path == '/car-loan-rates/')
        new = ('<article class="study cp5 i5">' + ''.join(str(e) for e in pre) + vis + (f'<div class="cpl cp5-pl">{"".join(boxes)}</div>' if boxes else '') + '</article>')
        return body[:i] + new + body[j + 10:]
    i = body.find('<div class="advp')
    if i < 0: return body
    so = _C5S(body[i:], 'html.parser'); d = so.find('div', class_='advp')
    hd = d.find('header', class_='advh1', recursive=False)
    for g_ in d.find_all('div', class_='ygrid', recursive=False): g_.unwrap()
    kids = [x for x in d.children if getattr(x, 'name', None)]
    hero, rest = '', []
    jump = ''
    for c_ in kids:
        if c_ is hd:
            k = hd.find(class_='ph-e'); h1 = hd.find('h1'); p = hd.find('p', class_=lambda v: v != 'ph-e')
            hero = V5_HERO(k.decode_contents() if k else '', h1.decode_contents() if h1 else '', p.decode_contents() if p else '')
        elif c_.name == 'nav' and 'imgj' in (c_.get('class') or []):
            jump = V5_BOX('signpost', 'Jump to a group', str(c_), 'jump')
        else: rest.append(c_)
    pre, groups = _i5_groups(rest)
    vis, boxes = _i5_render(groups, keep)
    # /images/: the search box and its "no match" line stay on top, the groups go in boxes (imgpage.js opens the boxes that match a search)
    new = (f'<div class="{" ".join(d.get("class") or [])} v5 i5">' + hero + (f'<div class="cpl cp5-pl">{jump}</div>' if jump else '') + ''.join(str(e) for e in pre) + vis
           + (f'<div class="cpl cp5-pl">{"".join(boxes)}</div>' if boxes else '') + '</div>')
    s = str(so); j = s.find(str(d))
    return body[:i] + s[:j] + new + s[j + len(str(d)):]


# 11-19 v5 (polish list A1): the Advanced pages (cars, motorcycles, planes). Centered hero with the car's photo and roomy 2-up tiles;
# "Nearby model years" / "Complaints by model year" (the long open stack) goes into a box; one chart stays open (complaints by system).
# Same words, ids and URLs.
def ADV5_HOOK(path, body):
    if not path.endswith('/advanced/') or 'class="advp tbl cpl-page"' not in body: return body
    try:
        s = _C5S(body, 'html.parser')
        root = s.select_one('div.advp.tbl.cpl-page')
        root['class'] = root.get('class', []) + ['adv5']
        hero = root.select_one('section.tb-hero')
        m = re.fullmatch(r'/cars/([^/]+)/(\d{4})/advanced/', path)
        if hero is not None and m and hero.h1 is not None and not hero.find('img'):
            ay = YSL.AIY.get(m.group(1), {}).get(m.group(2))   # that model year's own illustration (as on the year page), else the model photo
            ph = {'src': ay['src'], 'w': ay.get('w', 1000), 'h': ay.get('h', 600)} if ay and ay.get('src') else mphoto(m.group(1), int(m.group(2)))
            if ph: hero.h1.insert_after(_C5S(f'<div class="v5-im adv5-im">{pimg(ph, hero.h1.get_text(" ", strip=True).split(".")[0]).replace(" loading=" + chr(34) + "lazy" + chr(34), " fetchpriority=" + chr(34) + "high" + chr(34))}</div>', 'html.parser'))
        for op in root.select('section.cpl-open'):
            for sec in op.find_all('section', class_='yc', recursive=False):
                h = sec.find('h2', recursive=False)
                if h is None: continue
                t = h.decode_contents().strip(); h.decompose()
                sec.replace_with(_C5S(f'<div class="cpl adv5-bx">{V5_BOX("calendar", t, str(sec), h2=True)}</div>', 'html.parser'))
        sy = root.select_one('section#systems details') or root.select_one('section.cpl-sec:not(.cpl-info) details')
        if sy is not None: sy['open'] = ''
        return str(s)
    except Exception as ex:
        globals().setdefault('TAB_FAIL', []).append(f'ADV5 {path}: {type(ex).__name__} {ex}'); return body
