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
