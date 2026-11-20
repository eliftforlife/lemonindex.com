# 11-18 (Elijah: "make the engine pages that are confusing with long text stuff have the same compact box style as home page and other
# pages we just changed"): on every engine study page (/engines/<id>/, article.eng2) the long-text sections fold into small boxes:
# icon, the section's own h2 (kept as a heading), one short line, arrow; tap opens the full section in a white card. The hero
# (intro, stat tiles), the year chart and Quick answers stay open. The loose notes under the chart ("not enough complaints",
# "how we count", "all the numbers") become boxes too. Runs after the page's date hash (like RA_HOOK), so page dates don't move.
# Run by build.py with exec() (needs PILL_AR in scope). Styles: assets/cpl.css (.cpl-h, .cpl-sec).
from bs4 import BeautifulSoup as _EPS
_EP_RE = re.compile(r'/engines/[^/]+/')
_EP_ICON = [  # (words in the h2, icon)
    (('youtube',), 'youtube'), (('recall',), 'bell'), (('known issue', 'told dealers', 'problems acura', 'technical'), 'wrench'),
    (('in owners', 'what owners write'), 'talk'), (('every us version', 'trucks with', 'cars with this', 'against the other', 'versions'), 'engine'),
    (('how we count', 'source', 'all the numbers'), 'data')]
def _ep_icon(t):
    t = t.lower()
    for ks, ic in _EP_ICON:
        if any(k in t for k in ks): return f'/assets/icons/{ic}.webp'
    return '/assets/icons/chart.webp'
def _ep_txt(e): return re.sub(r'\s+', ' ', e.get_text(' ', strip=True)) if e else ''
def _ep_cut(t, n=64):
    """first clause of t, at most n characters, cut at a word (no trailing '…' unless it had to cut mid-clause)"""
    t = re.split(r'(?<=[.;:])\s', t.strip(), 1)[0].rstrip('.;:')
    if len(t) <= n: return t
    t = t[:n].rsplit(' ', 1)[0].rstrip(' ,(-–')
    return t + '…'
def _ep_sub(sec, title, h2s_txt=''):
    """the one short line under a box's title, from the section's own content"""
    tl = title.lower()
    t_all = _ep_txt(sec)
    m = re.search(r'([\d,]+) repair notes', t_all)
    if 'told dealers' in tl and m: return f'{m.group(1)} repair notes sent to dealers'
    if 'complain about' in tl:
        r = sec.select_one('.pt')
        if r and r.find('span') and r.find('b'): return f'Top: {_ep_txt(r.find("span"))}, {_ep_txt(r.find("b"))}'
    if 'what owners write' in tl:
        r = sec.select_one('tbody tr') or (sec.select('tr')[1:2] or [None])[0]
        if r and r.find('td'): return _ep_cut(_ep_txt(r.find('td')), 56)
    if 'show up' in tl:
        m = re.search(r'between ([\d,]+) and ([\d,]+) miles', t_all)
        if m: return f'Most between {m.group(1)} and {m.group(2)} miles'
    if 'known issue' in tl or 'told dealers' in tl:
        items = [re.split(r'[.(:]', _ep_txt(li), 1)[0].strip() for li in sec.find_all('li')]
        items = [x for x in items if 2 < len(x) <= 40][:3]
        if items: return ' · '.join(items)
    if 'youtube' in tl:
        t = _ep_txt(sec); m = re.search(r'tone (\d+)/100', t); v = re.search(r'from ([\d,]+) videos', t)
        if m: return f'Owner tone {m.group(1)}/100' + (f' · {v.group(1)} videos' if v else '')
    if 'recall' in tl:
        n = len(sec.select('ul.advr > li')) or len(sec.find_all('li'))
        if n: return f'{n} recall{"s" * (n != 1)}'
        p = sec.find('p')
        if p: return _ep_cut(_ep_txt(p))
    if 'in owners' in tl:
        n = len(sec.find_all('blockquote'))
        if n: return f'{n} complaint{"s" * (n != 1)}, in the owners’ own words'
    if 'every us version' in tl or 'against the other' in tl:
        n = len(sec.select('tbody tr')) or len(sec.select('.tw tr')) - 1
        if n > 0: return f'{n} {"version" if "version" in tl else "engine"}{"s" * (n != 1)} side by side'
    if h2s_txt: return _ep_cut(h2s_txt)
    p = sec.find(['p', 'li'], recursive=True)
    return _ep_cut(_ep_txt(p)) if p else ''
def _ep_box(soup, title, sub, inner_nodes, sid=None, h2=True):
    """a <section> (keeps the id, so #recalls links still land) holding one closed box"""
    sec = soup.new_tag('section'); sec['class'] = ['cpl-sec']
    if sid: sec['id'] = sid
    head = (f'<h2 class="cpl-h">{html.escape(title)}</h2>' if h2 else f'<b>{html.escape(title)}</b>')
    box = _EPS(f'<div class="cpl"><details><summary><img src="{_ep_icon(title)}" alt="" width="44" height="44" loading="lazy" decoding="async">'
               f'<span>{head}' + (f'<small>{html.escape(sub)}</small>' if sub else '') + f'</span>{PILL_AR}</summary><div class="cpl-b"></div></details></div>', 'html.parser')
    body = box.find(class_='cpl-b')
    for n in inner_nodes: body.append(n.extract())
    sec.append(box); return sec
_EP_KEEP = ('n3-eng', 'yqa', 'cp5-sec')   # open: the "Trucks/cars with this engine" year list and Quick answers
def _ep_details_box(soup, node):
    """<details class="trm|cpd"><summary>Title: rest</summary>...</details> -> a box"""
    sm = node.find('summary'); t = _ep_txt(sm); sm.extract()
    tt, _, rest = t.partition(':')
    title, sub = (tt.strip(), _ep_cut(rest.strip())) if rest.strip() else (_ep_cut(t, 48), '')
    return _ep_box(soup, title, sub, list(node.contents), h2=False).find('details')
def ENG_HOOK(path, body):
    if not _EP_RE.fullmatch(path) or 'eng2' not in body: return body
    soup = _EPS(body, 'html.parser'); art = soup.find('article', class_='eng2')
    if art is None: return body
    # 1. sections with an h2 -> boxes (the h2 stays a heading, inside the box's top row)
    for sec in art.find_all('section', recursive=False):
        if any(k in (sec.get('class') or []) for k in _EP_KEEP): continue
        h = sec.find('h2', recursive=False)
        if h is None: continue
        hs = h.find(class_='h2s'); h2s_txt = _ep_txt(hs)
        if hs: hs.extract()
        for x in h.find_all(['button', 'span']): x.extract()
        title = _ep_txt(h); h.extract()
        sub = _ep_sub(sec, title, h2s_txt)
        sec.replace_with(_ep_box(soup, title, sub, list(sec.contents), sec.get('id')))
    # 2. loose notes and folded tables after the year chart -> one stack of boxes where the first of them was
    seen, notes, dets = False, [], []
    for c in art.find_all(recursive=False):
        cls = c.get('class') or []
        if c.name == 'h2': seen = True
        elif seen and c.name == 'p' and 'note' in cls and 'engvd' not in cls: notes.append(c)
        elif seen and c.name == 'details' and ('trm' in cls or 'cpd' in cls): dets.append(c)
    if notes or dets:
        last = max(notes + dets, key=lambda e: art.contents.index(e)); stack = soup.new_tag('div'); stack['class'] = ['cpl', 'cpl-eng']; last.insert_after(stack)
        if notes: stack.append(_ep_box(soup, 'How to read this chart', _ep_cut(_ep_txt(notes[0])), notes, h2=False).find('details'))
        for d in dets: b = _ep_details_box(soup, d); d.extract(); stack.append(b)
    # 3. the source line at the end -> a box
    for p in art.find_all('p', class_='yc-cap', recursive=False):
        if _ep_txt(p).startswith('Source:'):
            holder = soup.new_tag('div'); holder['class'] = ['cpl', 'cpl-eng']; p.insert_before(holder)
            holder.append(_ep_box(soup, 'Sources', 'NHTSA owner complaints, recalls and YouTube', [p], h2=False).find('details'))
    return str(soup)
