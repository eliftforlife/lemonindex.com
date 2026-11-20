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
from bs4 import BeautifulSoup as _CPS, Comment
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
_CP_KEEP = ('yyears', 'bw2', 'yhero', 'cpl', 'cpl-sec', 'rla-sec', 'opn', 'n3-row', 'pinb', 'trc', 'pf-yf', 'yav', 'xc-no', 'sce1')   # sce1: a supercar's one-row EPA numbers (vehicles_pages.py) stay open like the year table
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
    if 'show up' in tl or 'mileage' in tl:
        m = re.search(r'between ([\d,]+) and ([\d,]+) miles', t_all)
        if m: return f'Most problems at {m.group(1)}–{m.group(2)} miles'
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
    return re.sub(r'\b(buy|is it|Is it) a (?=[AEIOU])', r'\1 an ', _ep_txt(h).rstrip('.')) or 'More'
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
        m = re.search(r'([~\d][\d,–~]*(?: \([^)]*\))? hp)\b', t)
        if m and not pan.select('tbody tr'): return f'{m.group(1)} · every version'

        n = len(pan.select('tbody tr')) or len(pan.select('.chip'))
        if n: return f'{n} version{"s" * (n != 1)}' + (' with power and mpg' if 'mpg' in t.lower() else '')
    h = pan.find('h2')
    return _cp_first(pan, _cp_title(h) if h else '')
def CAR_HOOK(path, body, force=False):
    if 'class="tbx"' not in body or 'role="tab"' not in body: return body
    if path in _CP_INJ and not force: return body   # perf_page.inject() calls it again (force) once the page is finished
    try: return CPL_POLISH(_car_hook(path, body)) if force else _car_hook(path, body)   # perf inject pages are already past page()'s polish
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
    hb = None
    if notes:
        t0 = _ep_txt(notes[0]); src_only = all(_ep_txt(n).startswith('Source') for n in notes)
        hb = _cp_box(soup, 'Sources' if src_only else 'How to read these numbers', _cp_cut(_cp_label(t0), 60), notes, None, _CP_I('data'), h2=False)
        tbx.insert_after(hb)
    _cp_stack(soup, soup)
    rel = _cp_group(soup, tbx, base, hb)
    return str(soup) + (f'<!--cpl-rel-->{rel}<!--/cpl-rel-->' if rel else '')

# 11-18 round 4 (Elijah, the 2011 Civic page: "the cards blend in ... group them ... Related at the very bottom"): the boxes sit in groups.
# 1. one stack of every content box (no gaps between the old tab's sections, the model page's repair-cost / engine-code rows and the code
#    lookup join it; Questions last); 2. the open year chart with "How to read these numbers" under it; 3. recall alerts + owner opinions;
#    then the page's end boxes (share / data / feedback, from build.py end_block) and, last of all, Related (build.py moves it after the end
#    block: CAR_HOOK marks it with <!--cpl-rel-->). Spacing and the card look are in assets/cpl.css (.cpl-grp).
def _cp_cls(e): return e.get('class') or [] if hasattr(e, 'get') else []
def _cp_isbox(e): k = _cp_cls(e); return 'cpl-sec' in k or ('cpl' in k and 'cpl-one' in k)
def _cp_grp(soup, *cls):
    g = soup.new_tag('div'); g['class'] = ['cpl-grp'] + list(cls); return g
def _cp_csearch(soup, cs):
    """the model page's engine-code lookup form -> a box"""
    b = _cp_box(soup, 'Check engine light on?', 'Look up any code, like P0420', list(cs.contents), None, _CP_I('search'), h2=False)
    b['class'] = b['class'] + ['csearch', 'mini']; b['aria-label'] = 'Engine code search'; return b
def _cp_n3box(soup, nav):
    """a loose chip row (the perf page's 'Regular model · Type S' links) -> a box"""
    cs = [re.sub(r'\s*\(.*?\)', '', _ep_txt(a.find(['b', 'strong']) or a)) for a in nav.find_all('a')]
    if not cs: return None
    sub = _cp_cut(cs[0], 40) + (f' · {len(cs) - 1} more' if len(cs) > 1 else '')
    t = 'Other versions of this car' if 'n3-par' in _cp_cls(nav) else 'More like this'
    return _cp_box(soup, t, sub, [nav], None, _CP_I('car'), h2=False)
def _cp_related(soup, nodes):
    """the page's related links (the year page's LX_HTML list, the UK page's "More Audi MOT pass rates") -> one box, last on the page"""
    for n in nodes:
        for h in n.find_all(['h2']) + n.find_all(class_='lx-h'): h.decompose()
    ts = [_ep_txt(a) for n in nodes for a in n.find_all('a')]
    sub = (_cp_cut(re.sub(r'\s*→$', '', ts[0]), 40) + (f' · {len(ts) - 1} more' if len(ts) > 1 else '')) if ts else ''
    b = _cp_box(soup, 'Related pages', sub, nodes, 'related', _CP_I('signpost'), h2=False)
    g = _cp_grp(soup, 'cpl-rel'); g.append(b); return g
def _cp_group(soup, tbx, base, notes):
    opened = [p for p in base.find_all('section', recursive=False) if 'cpl-open' in _cp_cls(p)]
    # 1. the main stack
    g1 = _cp_grp(soup, 'cpl-g1')
    kids = [k for k in base.find_all(recursive=False) if k not in opened and 'ovslim' not in _cp_cls(k)]
    if kids: kids[0].insert_before(g1)
    else: (opened[0].insert_before(g1) if opened else base.append(g1))
    for k in kids: g1.append(k.extract())
    for w in g1.find_all('div', class_='cpl-stk'): w.unwrap()   # the group is the stack now
    for w in g1.find_all('div', class_='ovk', recursive=False):
        if all(_cp_isbox(c) for c in w.find_all(recursive=False)): w.unwrap()
    # the top-level blocks after the page's article: repair costs, engine codes, the code lookup, recall alerts, opinions, Related
    top = tbx
    while top.parent is not None and top.parent is not soup: top = top.parent
    if top is not tbx and top.name in ('div', 'article', 'section'): top['class'] = _cp_cls(top) + ['cpl-page']   # (cpl.css: no side or bottom padding of its own, so the groups line up with the end boxes)
    after, a = [], tbx
    while a is not None and a is not soup:
        after += [e for e in a.find_next_siblings() if e is not notes]; a = a.parent
    qbox = g1.find(id=['p-questions', 'p-uk-faq'])
    def put_main(b):
        if qbox is not None: qbox.insert_before(b)
        else: g1.append(b)
    g3 = _cp_grp(soup, 'cpl-g3'); reln = []
    for e in after:
        k = _cp_cls(e)
        if 'cpl-one' in k: put_main(e.extract())
        elif e.name == 'section' and 'csearch' in k: b = _cp_csearch(soup, e); e.decompose(); put_main(b)
        elif e.name == 'nav' and 'lx' in k: reln.append(e.extract())
        elif e.name == 'section' and 'yc' in k and e.find('h2') is not None and _ep_txt(e.find('h2')).startswith('More ') and not e.find(class_='cpl'): reln.append(e.extract())   # UK: "More Audi MOT pass rates."
        elif e.name == 'p' and 'ukx-cap' in k and e.find('a') is not None and reln: e.attrs.pop('style', None); reln.append(e.extract())   # "Every UK model ranked ... →"
        elif 'rla-sec' in k or 'opn' in k: g3.append(e.extract())
    rel = _cp_related(soup, reln) if reln else None
    # loose chip rows in the stack -> boxes
    for nav in [n for n in g1.select('nav.n3-row') if n.find_parent(class_='cpl') is None]:
        ph = soup.new_tag('i'); nav.insert_before(ph); b = _cp_n3box(soup, nav)
        if b is not None: ph.replace_with(b)
        else: ph.decompose()
    lead, charts = [], []
    for c in g1.find_all(recursive=False):
        if _cp_isbox(c) or 'pf' in _cp_cls(c) or c.name not in ('section', 'div'): continue
        if c.name == 'section' and ('yav' in _cp_cls(c) or c.get('id') in ('avoid', 'ukx-pick')) : lead.append(c)
        elif c.name == 'section': charts.append(c)
    # the model page's "Looking at a 2023 or newer? ..." note (loose text under the hero) -> a box under the year chart
    newer = []
    for sl in base.find_all('p', class_='ovslim', recursive=False):
        m = re.match(r'(Looking at an? [^?]{3,40}\?)\s*(.+)$', _ep_txt(sl))
        if not m or sl.find('b') is not None: continue
        y = re.search(r'like the (\d{4}) best', m.group(2))
        sub = 'Too new for a full complaint score' + (f' · YouTube owners like the {y.group(1)} best' if y else '') if 'too new' in m.group(2).lower() else _cp_cut(m.group(2), 60)
        sl.attrs = {}; sl['class'] = ['yc-cap']; sl.string = m.group(2); newer.append(_cp_box(soup, m.group(1), sub, [sl.extract()], None, _CP_I('calendar'), h2=False))
    # 2. the year chart + years to avoid / buy (open)
    g2 = None
    if opened or charts:   # 11-19 (Elijah: "hero, the core cards, then the chart with avoid/buy"): years to avoid / buy open the chart group
        g2 = _cp_grp(soup, 'cpl-g2'); base.append(g2)
        for p in lead + charts + opened: g2.append(p.extract())
    else:
        for c in lead: g1.insert_before(c.extract())
    # 3. round 5 (11-19, Elijah: fewer cards): the stack keeps the boxes a buyer wants right away; every method/meta box (how to read, sources,
    #    the data table, embed, YouTube ranks, the engine-code tools, the newer-years note, and the end block's "Use this data free" and
    #    feedback) goes into ONE "Info" box as a nested stack. Similar cars / other versions join Related at the end; "Questions to ask the
    #    seller" opens inside Questions. cpl.js opens every parent <details> of an #anchor, so old links still land on the nested box.
    info, relb = [], []
    for x in [y for y in g1.find_all('section') if _cp_isbox(y) and y.find_parent(class_='cpl-b') is None]:
        t = _cp_btitle(x)
        if any(w in t for w in _CP_INFO_W): info.append(x.extract())
        elif x.get('id') == 'similar' or t.startswith(('similar', 'other versions', 'more like this', 'compare')): relb.append(x.extract())
    # boxes that belong to a core box open inside it (the seller questions in Questions, "What breaks most" in Problems, gas or hybrid in Engines)
    tops = lambda: [y for y in g1.find_all('section') if _cp_isbox(y) and y.find_parent(class_='cpl-b') is None]
    for kid, par in (('ask the seller', ('questions', 'common questions')), ('what breaks most', ('problems',)), ('gas or hybrid', ('engines', 'specs'), ),
                     ('reliability', ('problems',)), ('what owners say on youtube', ('should you buy',))):
        for x in [y for y in tops() if kid in _cp_btitle(y)]:
            near = [y for y in x.parent.find_all('section', recursive=False) if y is not x and _cp_isbox(y) and _cp_btitle(y).startswith(par) and kid not in _cp_btitle(y)]   # same generation first (perf pages)
            pb = (near or [y for y in tops() if y is not x and _cp_btitle(y).startswith(par) and kid not in _cp_btitle(y)] or [None])[0]
            pb = pb.find(class_='cpl-b') if pb is not None else None
            if pb is not None: pb.append(x.extract())
    if g2 is not None:
        for d in g2.select('div.cpl > details'):
            if d.find_parent(class_='cpl-b') is not None: continue
            if any(w in _cp_btitle(d) for w in ('how to read', 'youtube ranks', 'embed')):
                w = soup.new_tag('div'); w['class'] = ['cpl']; w.append(d.extract()); info.append(w)
        for c in g2.find_all('div', class_='cpl'):
            if not c.find(True): c.decompose()
    info += newer
    if notes is not None: info.append(notes.extract())
    pend = soup.find('div', class_='pend')   # perf inject pages: the end block is already on the page
    endb = pend.select('div.cpl > details') if pend is not None else []
    nest = soup.new_tag('div'); nest['class'] = ['cpl-nest']
    for x in info: nest.append(x)
    for d in endb: w = soup.new_tag('div'); w['class'] = ['cpl']; w.append(d.extract()); nest.append(w)
    if pend is None: nest.append(Comment('cpl-info-end'))   # build.py page() puts "Use this data free" and the feedback box here
    tl = ' '.join(_cp_btitle(x) for x in info) + (' use this data feedback' if pend is None or endb else '')
    words = [k for k, ws in _CP_INFO_LINE if any(w in tl for w in ws)][:3]   # one line on a phone
    line = ' · '.join(words); line = line[:1].upper() + line[1:]
    ib = _cp_box(soup, 'Info', line, [nest], 'info', _CP_I('info'), h2=False, cls='cpl-info')
    ib.find('summary')['class'] = ['cpl-keep']
    g4 = _cp_grp(soup, 'cpl-g4'); g4.append(ib)
    (g2 if g2 is not None else g1).insert_after(g4)
    # 4. recall alerts + opinions, after the article
    if g3.contents: top.insert_after(g3)
    # 11-19: a group of nothing but boxes is one inset list (cpl.css .cpl-ins)
    for g in (g1, nest):
        if all(_cp_isbox(c) or (c.name == 'div' and 'cpl' in _cp_cls(c)) for c in g.find_all(recursive=False)) and g.find(recursive=False) is not None: g['class'] = _cp_cls(g) + ['cpl-ins']
    if rel is None and relb: rel = _cp_grp(soup, 'cpl-rel')
    if rel is None: return ''
    for x in reversed(relb): rel.insert(0, x)
    rel['class'] = _cp_cls(rel) + ['cpl-ins']
    if pend is not None: pend.insert_after(rel); return ''
    return str(rel)   # build.py page() puts it after the end-of-page boxes
def _cp_btitle(x):
    sm = x if x.name == 'summary' else x.find('summary')
    t = sm.find(['h2', 'b']) if sm is not None else None
    return _ep_txt(t).lower() if t is not None else ''
_CP_INFO_W = ('how to read', 'sources', 'all the data', 'check engine light', 'engine codes', 'embed', 'youtube ranks', 'about these', 'looking at a', 'method')
_CP_INFO_LINE = [('sources', ('sources',)), ('data', ('all the data', 'use this data')), ('embed', ('embed',)), ('how to read', ('how to read', 'looking at a')),
                 ('YouTube ranks', ('youtube ranks',)), ('engine codes', ('engine codes', 'check engine light')), ('feedback', ('spot a mistake', 'feedback'))]
# 11-19 (Elijah): every card is title-only (the one-line fact under the title goes; the "Info" box keeps its short contents line), and the
# icons are flat black line icons from one open-source set (Lucide, ISC licence in the sprite; assets/ic.svg) instead of the GPT .webp set
# (those stay in assets/icons, unused). Runs on the finished page (build.py page() after the date hash, and on CAR_HOOK's output for perf
# inject pages), so page dates don't move.
IC_V = '1'
_CP_SPR = {'warning', 'wrench', 'bell', 'question', 'scale', 'data', 'tag', 'calendar', 'film', 'stopwatch', 'youtube', 'chart', 'embed', 'share', 'talk',
           'opinion', 'signpost', 'car', 'search', 'info', 'history', 'engine'}
def _cp_svg(k): return f'<svg class="cpl-i" width="24" height="24" aria-hidden="true" focusable="false"><use href="/assets/ic.svg?v={IC_V}#{k}"></use></svg>'
_CP_SUMM = re.compile(r'<summary\b[^>]*>.*?</summary>', re.S)
_CP_BTN = re.compile(r'<button\b[^>]*\bclass="cpl-a\b[^"]*"[^>]*>.*?</button>', re.S)
_CP_IMG = re.compile(r'<img\b[^>]*?\bsrc="/assets/icons/([\w-]+)\.webp(?:\?v=\d+)?"[^>]*>')
_CP_OLDY = re.compile(r'(<details\b[^>]*\bcpl-y\b[^>]*>\s*<summary\b[^>]*>)\s*<img\b[^>]*>')
_CP_SMALL = re.compile(r'<small\b[^>]*>.*?</small>', re.S)
def CPL_POLISH(h):
    if 'cpl' not in h: return h
    h = _CP_OLDY.sub(lambda m: m.group(1) + _cp_svg('history'), h)
    h = _CP_SUMM.sub(lambda m: m.group(0) if ('cpl-keep' in m.group(0) or 'cpl-ar' not in m.group(0)) else _CP_SMALL.sub('', m.group(0)), h)
    h = _CP_BTN.sub(lambda m: _CP_SMALL.sub('', m.group(0)), h)
    return _CP_IMG.sub(lambda m: _cp_svg(m.group(1) if m.group(1) in _CP_SPR else 'info'), h)
