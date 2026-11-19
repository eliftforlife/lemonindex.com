# 11-18 (Elijah, from the 1994-2001 Integra page: "So everything is like the main page ... you see the JDM card, you see in the movies,
# recalls, problems, questions, YouTube, so that you can just press whatever you want to know, and then it'll open further. So it looks
# compact and super clean"): every tabbed car page (model, year, Advanced, performance/JDM, supercar, motorcycle, plane, EV, UK MOT) loses
# its tab bar. The tabs that held the year chart stay open on the page; every other tab becomes one small tap-to-open box (icon, title,
# one real fact, arrow), and the long sections of the main tab (the engine card, known issues, the films, YouTube, buying advice, sources)
# fold into boxes too. The hero, the verdict/gauge and the year chart stay open. Nothing is removed: every section stays in the HTML inside
# its <details>, with its id, and assets/cpl.js opens the box holding a #hash target (old #p-recalls / #recalls / #questions links).
# Runs in build.py page() after the date hash (like ENG_HOOK), so page dates don't move. exec'd by build.py (needs PILL_AR, _ep_txt, _ep_cut
# from engine_pills.py). Styles: assets/cpl.css (.cpl-stk, .cpl-pan). No film stills or logos: the films box uses our own clapperboard icon.
import copy, glob
from bs4 import BeautifulSoup as _CPS
_CP_I = lambda k: f'/assets/icons/{k}.webp'
_CP_PAN_ICON = {'problems': 'warning', 'repairs': 'wrench', 'recalls': 'bell', 'questions': 'question', 'compare': 'scale', 'data': 'data',
                'specs': 'engine', 'cost': 'tag', 'owners': 'wrench', 'uk-fails': 'warning', 'uk-faq': 'question', 'years': 'calendar', 'overview': 'chart'}
_CP_SEC_ICON = [  # (words in the section title, icon), first match wins
    (('in the film', 'film'), 'film'), (('show up', 'mileage', 'how fast', 'performance'), 'stopwatch'), (('known issue', 'what breaks', 'problem', 'complain', 'fail'), 'warning'), (('recall',), 'bell'),
    (('youtube',), 'youtube'), (('should you buy', 'buy', 'price', 'cost', 'fix or sell', 'range'), 'tag'),
    (('engine', 'version', 'spec'), 'engine'), (('similar', 'compare', ' vs', 'gas or hybrid', 'hybrid'), 'scale'), (('question', 'ask the seller', 'ask'), 'question'),
    (('source', 'how to read', 'about these', 'method'), 'data'), (('repair', 'fix'), 'wrench'), (('year',), 'calendar'), (('what owners say', 'opinion'), 'talk')]
def _cp_icon(t):
    t = ' ' + t.lower()
    for ks, ic in _CP_SEC_ICON:
        if any(k in t for k in ks): return _CP_I(ic)
    return _CP_I('chart')
_CP_OPEN_PANELS = ('p-years', 'p-uk-years')   # the year chart / year table stays open
_CP_KEEP = ('yyears', 'bw2', 'yhero', 'cpl', 'cpl-sec', 'rla-sec', 'opn', 'n3-row', 'pinb', 'trc', 'pf-yf', 'yav', 'xc-no')
def _cp_inject_pages():
    """performance pages that perf_page.inject() rewrites after the build: the hook runs there instead (POST_HOOK), on the finished page"""
    out = set()
    for f in glob.glob(os.path.join('data', 'perf', '*.json')):
        if f.endswith('.auto.json'): continue
        try:
            D = json.load(open(f, encoding='utf-8'))
            if D.get('mode') == 'inject' and D.get('page'): out.add(D['page'])
        except Exception: pass
    return out
_CP_INJ = _cp_inject_pages()
def _cp_label(t):
    """'Sources: NHTSA ...' -> 'NHTSA ...' (a short leading label goes)"""
    return re.sub(r'^(?:Sources?|How to read this|Method|Note)[:.]\s+(?=\S)', '', t, 1)
def _cp_cut(t, n=64):
    """_ep_cut, but never ends inside an open bracket ("$19,440 (1994 coupe base" -> "$19,440")"""
    t = re.sub(r'\s+:\s+', ' · ', t.replace('U.S.', 'US'))
    r = _ep_cut(t, n)
    if r.count('(') > r.count(')'): r = r[:r.rfind('(')].rstrip(' ,;–-')
    if len(r) < 14 and len(t) > len(r) + 4: r = _ep_cut(t.replace(':', ''), n)   # 'Filed as: F800 GS, ...' cut to 'Filed as'
    return r
def _cp_n(t):
    try: return int(re.sub(r'[^\d]', '', t) or 0)
    except ValueError: return 0
def _cp_box(soup, title, sub, nodes, sid=None, icon=None, h2=True, cls=None):
    """<section class="cpl-sec" id=sid> holding one closed box; `nodes` move into its white card"""
    sec = soup.new_tag('section'); sec['class'] = ['cpl-sec'] + ([cls] if cls else [])
    if sid: sec['id'] = sid
    head = f'<h2 class="cpl-h">{html.escape(title)}</h2>' if h2 else f'<b>{html.escape(title)}</b>'
    box = _CPS(f'<div class="cpl"><details><summary><img src="{icon or _cp_icon(title)}" alt="" width="44" height="44" loading="lazy" decoding="async">'
               f'<span>{head}' + (f'<small>{html.escape(sub)}</small>' if sub and sub.strip().lower() != title.strip().lower() else '')
               + f'</span>{PILL_AR}</summary><div class="cpl-b"></div></details></div>', 'html.parser')
    b = box.find(class_='cpl-b')
    for n in nodes: b.append(n.extract() if getattr(n, 'parent', None) is not None else n)
    sec.append(box); return sec
def _cp_first(sec, title=''):
    """first clause of the section's first real text line (not the title)"""
    for e in sec.find_all(['p', 'li', 'td', 'dd', 'b', 'a']):
        t = re.sub(r'\s*(?:See it|See all|Open)\s*→$', '', _ep_txt(e))
        if len(t) > 3 and t.lower().rstrip('.') != title.lower().rstrip('.') and not t.startswith(('Showing the years', 'Sources')): return _cp_cut(t, 60)
    return ''
def _cp_sub(sec, title):
    """the one-line fact under a folded section's title"""
    tl = title.lower(); t_all = _ep_txt(sec)
    if 'film' in tl:
        fs = [_ep_txt(li.find('b')) for li in sec.select('ul.pf-iss > li') if li.find('b')]
        if fs: return (f'{len(fs)} films · ' if len(fs) > 1 else '') + _cp_cut(fs[0], 44)
    if tl.startswith('the engine') or 'engine:' in tl:
        f = {_ep_txt(d.find('span')): _ep_txt(d.find('b')) for d in sec.select('.pf-f') if d.find('span') and d.find('b')}
        hp = re.search(r'([\d,–]+) hp', f.get('Output') or '')
        bits = [(f'{hp.group(1)} hp' if hp else re.split(r' at |,', f['Output'])[0]) if f.get('Output') else '',
                (re.sub(r'\s*\(.*?\)', '', f['Redline']) + ' redline') if f.get('Redline') else '']
        bits = [b for b in bits if b]
        if bits: return ' · '.join(bits)
        w = sec.select_one('.pf-ew')
        if w: return _cp_cut(_ep_txt(w), 56)
    if 'known issue' in tl:
        its = [_ep_txt(li.find('b')) for li in sec.select('li') if li.find('b')]
        if its: return ' · '.join(_cp_cut(x, 34) for x in its[:2])
    if 'youtube' in tl:
        m = re.search(r'\b(\d{1,3})\b[^.]{0,40}?(?:YouTube owner tone|owner tone)', t_all) or re.search(r'tone (\d+)/100', t_all)
        v = re.search(r'([\d,]+) (?:most-watched )?(?:[A-Z][\w-]* )*videos', t_all)
        rk = re.search(r'#(\d+) of ([\d,]+)', t_all)
        if rk and 'tone' in t_all: return f'#{rk.group(1)} of {rk.group(2)} cars by YouTube owner tone'
        if m: return f'Owner tone {m.group(1)}/100' + (f' · {v.group(1)} videos' if v else '')
    if 'how fast' in tl:
        hp = re.search(r'(\d[\d,]*) hp', t_all); z = re.search(r'0–60 mph\s*([\d.]+) s', t_all)
        bits = [f'{hp.group(1)} hp' if hp else '', f'0–60 in {z.group(1)} s' if z else '']
        if any(bits): return ' · '.join(b for b in bits if b)
    if 'should you buy' in tl:
        li = sec.select_one('ul.pf-buy > li, li')
        if li: return _cp_cut(_ep_txt(li), 58)
    if 'similar' in tl:
        n = len(sec.select('a'))
        if n: return f'{n} cars from the same year, side by side'
    if 'engines & versions' in tl or 'engines and versions' in tl:
        cs = [re.sub(r'\s*\(.*?\)', '', _ep_txt(a)) for a in sec.select('.n3-row a')]
        if cs: return _cp_cut(cs[0], 40) + (f' · {len(cs) - 1} more' if len(cs) > 1 else '')
    if 'ask the seller' in tl:
        n = len(sec.select('li'))
        if n: return f'{n} questions to ask before you buy'
    if 'what breaks' in tl:
        li = sec.select_one('li')
        if li:
            nm = li.find(['b', 'span', 'a']); return _cp_cut(_ep_txt(nm) if nm else _ep_txt(li), 56)
    if 'recall' in tl:
        n = len(sec.select('ul.pf-recs > li, ul.advr > li'))
        if n: return f'{n} recall{"s" * (n != 1)}'
    return _cp_first(sec, title)
def _cp_title(h):
    """an h2's own words (no .h2s second sentence, counters or buttons)"""
    h = copy.copy(h)
    for x in h.select('.h2s, button, .yc-n, svg, small'): x.decompose()
    return _ep_txt(h).rstrip('.') or 'More'
def _cp_fold_sec(soup, sec):
    """a <section> with an h2 -> a box; its h2 sits in the box's top row"""
    h = sec.find('h2', recursive=False)
    title = _cp_title(h); sub = _cp_sub(sec, title)
    hs = h.find(class_='h2s'); hs_t = _ep_txt(hs) if hs else ''
    h.extract()
    nodes = list(sec.contents)
    if hs_t: nodes = [_CPS(f'<p class="cpl-dek">{html.escape(hs_t)}</p>', 'html.parser')] + nodes
    if not sub and hs_t: sub = _cp_cut(hs_t, 60)
    box = _cp_box(soup, title, sub, nodes, sec.get('id'), _cp_icon(title), cls=None)
    keep = [c for c in (sec.get('class') or []) if c not in ('yc', 'pf-sec', 'tb-p', 'on')]   # the section's own classes (yqa, yot ...) go on the white card, so its styles and scripts still apply
    if keep: cb = box.find(class_='cpl-b'); cb['class'] = cb['class'] + keep
    sec.replace_with(box); return box
def _cp_split_engine(soup, sec):
    """the perf engine section: engine facts box + a separate "Known issues" box"""
    h3 = next((x for x in sec.find_all('h3', recursive=False) if _ep_txt(x).lower().startswith('known issue')), None)
    if h3 is None: return None
    ttl = _ep_txt(h3); nodes = []; n = h3.next_sibling
    while n is not None and not (getattr(n, 'name', None) in ('h3', 'details') or (getattr(n, 'name', None) == 'details')):
        nx = n.next_sibling; nodes.append(n); n = nx
    h3.extract()
    tmp = _CPS('<section></section>', 'html.parser').section
    for x in nodes: tmp.append(x.extract())
    eng = re.sub(r'^The engine:\s*', '', _cp_title(sec.find('h2', recursive=False)))
    title = f'{ttl}: {eng}' if eng and eng.lower() != 'the engine' else ttl
    return _cp_box(soup, title, _cp_sub(tmp, 'known issues'), list(tmp.contents), icon=_CP_I('warning'))
def _cp_stack(soup, root):
    """consecutive box sections -> one tight stack (8 px apart) instead of the panel's big section gaps"""
    for par in [root] + root.find_all(['div', 'section', 'article']):
        kids = [k for k in par.find_all(recursive=False)]
        run = []
        def flush():
            if len(run) > 1:
                w = soup.new_tag('div'); w['class'] = ['cpl-stk']; run[0].insert_before(w)
                for k in run: w.append(k.extract())
            run.clear()
        for k in kids:
            if 'cpl-sec' in (k.get('class') or []): run.append(k)
            else: flush()
        flush()
def _cp_pan_sub(pid, pan, card, label=''):
    """the fact under a whole tab's box: the old preview card's own numbers when there was one, else counted from the tab"""
    if card is not None and not card[2] and pid != 'p-data':
        bits = [b for b in card[:2] if b]
        if len(bits) == 2 and re.fullmatch(r'[\d,]+', bits[0]): return _cp_cut(f'{bits[0]} {bits[1]}', 64)   # '15 repair notes Ford sent dealers'
        if bits: return _cp_cut(' · '.join(bits), 64)
    t = _ep_txt(pan); k = pid.replace('p-', '')
    if k in ('questions', 'uk-faq'):
        n = len(pan.select('.yqa h3, .ukx-faq h3, .yqa summary, .yqa dt')) or len(pan.find_all('h3'))
        if n: return f'{n} quick answer{"s" * (n != 1)}'
    if k in ('recalls',):
        m = re.search(r'Recalls(?: we found)?\s+(\d+)', t) or re.search(r'(\d+) recalls?\b', t)
        n = int(m.group(1)) if m else len(pan.select('ul.pf-recs > li, ul.advr > li, #recalls li'))
        if n: return f'{n} recall{"s" * (n != 1)}' + (' · free fix at any dealer' if n else '')
        if re.search(r'\bno recalls\b', t, re.I): return 'No recalls on record'
    if k in ('problems', 'uk-fails'):
        m = re.search(r'([\d,]+) (?:owner )?complaints', t)
        top = pan.select_one('.pt span, .pf-b, tbody td')
        rc = len(pan.select('ul.pf-recs > li, ul.advr > li'))
        if m and rc: return f'{m.group(1)} owner complaints · {rc} recall{"s" * (rc != 1)}'
        if m: return f'{m.group(1)} owner complaints' + (f' · top: {_cp_cut(re.sub(r"[\d,%]+$", "", _ep_txt(top)).strip(), 28).lower()}' if top is not None and _ep_txt(top) else '')
        m = re.search(r'([\d.]+)% of tests', t)
        if m and top is not None: return _cp_cut(_ep_txt(top), 56)
    if k == 'cost':
        m = re.search(r'([\d,]+(?:–[\d,]+)?) miles', t)
        if m: return f'{m.group(1)} miles of EPA range'
    if 'youtube' in (label or '').lower():
        m = re.search(r'([\d,]+) YouTube videos', t)
        if m: return f'From {m.group(1)} YouTube videos'
    if k == 'compare':
        ms = [_ep_txt(a).replace('vs ', '') for a in pan.select('a') if _ep_txt(a).startswith('vs ')]
        if ms: return 'vs ' + ', '.join(ms[:2]) + (f' and {len(ms) - 2} more' if len(ms) > 2 else '')
    if k == 'data':
        tb = pan.find('table'); n = len(tb.select('tbody tr')) if tb is not None else 0
        if n: return f'{n} model years in one table'
    if k == 'specs':
        m = re.search(r'([~\d][\d,–~]*(?: \([^)]*\))? hp)', t)
        if m and not pan.select('tbody tr'): return f'{m.group(1)} · every version'

        n = len(pan.select('tbody tr')) or len(pan.select('.chip'))
        if n: return f'{n} version{"s" * (n != 1)}' + (' with power and mpg' if 'mpg' in t.lower() else '')
    h = pan.find('h2')
    return _cp_first(pan, _cp_title(h) if h else '')
def CAR_HOOK(path, body, force=False):
    if 'class="tbx"' not in body or 'role="tab"' not in body: return body
    if path in _CP_INJ and not force: return body   # perf_page.inject() calls it again (force) once the page is finished
    try: return _car_hook(path, body)
    except Exception as ex:
        globals().setdefault('TAB_FAIL', []).append(f'car_pills {path}: {type(ex).__name__} {ex}'); return body
def _car_hook(path, body):
    soup = _CPS(body, 'html.parser'); tbx = soup.find('div', class_='tbx')
    if tbx is None: return body
    labels = {b.get('aria-controls'): _ep_txt(b) for b in tbx.select('[role=tab]')}
    pans = [p for p in tbx.find_all('section', recursive=False) if 'tb-p' in (p.get('class') or [])]
    if not pans: return body
    base = next((p for p in pans if p.get('id') == 'p-overview'), None) or next((p for p in pans if 'on' in (p.get('class') or [])), pans[0])
    # 1. the tab bar goes; the phone page-actions menu (.ycn: All years / Compare / Share / Advanced) moves under the hero
    row = tbx.find(class_='tb-row', recursive=False)
    ycn = row.find(class_='ycn') if row else None
    hero = soup.find('section', class_='tb-hero')
    if ycn is not None and hero is not None:
        w = soup.new_tag('div'); w['class'] = ['cpl-acts']; w.append(ycn.extract()); hero.append(w)
    if row is not None: row.decompose()
    # 2. the main tab's long sections fold (the hero, verdict and chart stay open)
    cards = {}
    for g in base.find_all(class_='ovg'):
        for a in g.find_all('a', class_='ovc'):
            m = re.match(r'#(p-[\w-]+)', a.get('href', ''))
            if m: cards[m.group(1)] = (_ep_txt(a.find(class_='ovc-v')), _ep_txt(a.find(class_='ovc-s')), 'ovc-na' in (a.get('class') or []))
    ovg = base.find(class_='ovg')
    anchor = soup.new_tag('div'); anchor['class'] = ['cpl-here']
    if ovg is not None:
        ovg.insert_before(anchor)
        a_sec = anchor.find_parent('section')
        while a_sec is not None and a_sec is not base and base in a_sec.find_parents():   # the cards sat inside a section that folds (the M3's "Reliability"): the boxes go right after it
            a_sec.insert_after(anchor.extract()); a_sec = anchor.find_parent('section')
    for g in base.find_all(class_='ovg'): g.decompose()
    def foldable(s):
        k = s.get('class') or []
        if s.name != 'section' or s.find('h2', recursive=False) is None or any(c in _CP_KEEP for c in k) or s.get('id') in ('years', 'yt-years'): return False
        if s.find(class_=['yyears', 'yy-ch']) is not None: return False   # a year chart stays open
        return not _cp_title(s.find('h2', recursive=False)).lower().startswith('every year')
    for sec in ([] if base.get('id') in _CP_OPEN_PANELS else list(base.find_all('section'))):
        if sec.parent is None or sec.find_parent('details') is not None or sec.find_parent(class_='cpl') is not None: continue
        if not foldable(sec): continue
        if sec.find_parent('section', class_=lambda c: c and ('yyears' in c or 'bw2' in c)) is not None: continue
        ks = None
        if 'pf-sec' in (sec.get('class') or []) and sec.find('h2', recursive=False) and _cp_title(sec.find('h2', recursive=False)).lower().startswith('the engine'):
            ks = _cp_split_engine(soup, sec)
        b = _cp_fold_sec(soup, sec)
        if ks is not None: b.insert_after(ks)
    h0 = base.find('h2', recursive=False)
    if h0 is not None and base.get('id') not in _CP_OPEN_PANELS:   # the main tab is one section itself (EV pages: "Top problems")
        tmp = _CPS('<section></section>', 'html.parser').section
        for x in list(base.contents): tmp.append(x.extract())
        base.append(tmp); _cp_fold_sec(soup, tmp)
    # the perf page's "All sources" fold -> a box
    for d in base.find_all('details', class_='pf-sd'):
        sm = d.find('summary'); n = re.search(r'\((\d+)\)', _ep_txt(sm)); sm.extract()
        b = _cp_box(soup, 'All sources', f'{n.group(1)} sources, numbered' if n else '', list(d.contents), d.get('id'), _CP_I('data'), h2=False); d.replace_with(b)
    # 3. every other tab -> one box (in the stack where the old preview cards were, Questions last); the year chart tab stays open
    boxes, opened = [], []
    for p in pans:
        if p is base: continue
        pid = p.get('id') or ''
        if pid in _CP_OPEN_PANELS: opened.append(p); continue
        k = pid.replace('p-', ''); lab = labels.get(pid) or k.replace('-', ' ').capitalize()
        sub = _cp_pan_sub(pid, p, cards.get(pid), lab)
        b = _cp_box(soup, lab, sub, list(p.contents), pid, _CP_I(_CP_PAN_ICON.get(k, 'chart')), h2=False, cls='cpl-pan')
        p.decompose(); boxes.append((k in ('questions', 'uk-faq'), b))
    boxes = [b for _, b in sorted(boxes, key=lambda x: x[0])]
    qs = [b for b in boxes if b.get('id') in ('p-questions', 'p-uk-faq')]; rest = [b for b in boxes if b not in qs]
    src = base.find('section', id='pf-sources')
    def put_end(b):
        if src is not None: src.insert_before(b)
        else: base.append(b)
    if anchor.parent is not None:   # where the preview cards were
        for b in rest: anchor.insert_before(b)
        anchor.decompose()
    else:
        for b in rest: put_end(b)
    for b in qs: put_end(b)   # Questions after everything else
    # the year chart tabs: open, after the boxes
    for p in opened:
        p['class'] = [c for c in (p.get('class') or []) if c not in ('tb-p', 'on')] + ['cpl-open']; p.extract(); base.append(p)
    base['class'] = [c for c in (base.get('class') or []) if c != 'on'] + ['on', 'cpl-main']
    for sl in base.find_all('p', class_='ovslim', recursive=False): base.insert(0, sl.extract())   # the one-line stats sit above the boxes, not between them
    # 4. loose notes after the tabs (the index explainer, EV score note, UK method) -> one box
    host = tbx.parent
    notes = [c for c in host.find_all(['p', 'section'], recursive=False) if c is not tbx and (
        (c.name == 'p' and any(x in (c.get('class') or []) for x in ('yc-cap', 'note'))) or 'ukx-src' in (c.get('class') or []))]
    if notes:
        t0 = _ep_txt(notes[0]); src_only = all(_ep_txt(n).startswith('Source') for n in notes)
        hb = _cp_box(soup, 'Sources' if src_only else 'How to read these numbers', _cp_cut(_cp_label(t0), 60), notes, None, _CP_I('data'), h2=False)
        tbx.insert_after(hb)
    _cp_stack(soup, soup)
    return str(soup)
