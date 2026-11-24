# 11-24 (Elijah, on the BMW S68 page; applies to every engine page /engines/<id>/, article.eng2): exec'd by build.py, ENG6_HOOK runs in
# page() right after engine_pills.ENG_HOOK (so after the date hash: a layout change never redates a page).
#   3. the stat chips in a row ("2023–26 model years", "577 hp", "#28 YouTube rank") become a stacked stat column beside the engine
#      picture: big numbers, small labels, a yellow mark (under the picture on a phone)
#   4. the intro paragraph under the picture shrinks to one plain line: what the engine is and the first cars it's in
#   5. "A safer bet: YouTube owner tone 55/100, #28 of 178 engine pages ..." becomes a plain verdict card ("YouTube owners like it" +
#      one line: where it ranks, engine recalls)
#   7. "Known issues on record" goes away when its only entry is "Too new to judge"
#   8. "Every US version with this engine" + "Everyday cars with this engine" (+ "By car") = one "Cars with this engine" box
#   9 + 11. "All the numbers, year by year", "How to read this chart", "How we count", "Owner score = ..." and the sources note = one
#      "Year-by-year numbers and how we count" box, last
#   10. boxes in the order a buyer cares about: problems, owner complaints, recalls, dealer notes, YouTube, cars, specs/comparisons,
#      Quick answers, then the method
# Every fact and link stays in the HTML (the full intro paragraph moves into the method box); only order and wording around the numbers change.
import copy
from bs4 import BeautifulSoup as _E6S

_E6_RE = re.compile(r'/engines/[^/]+/')
E6_CSS = '''<style id="e6-css">
.e6-hv{display:grid;grid-template-columns:minmax(0,1fr);gap:18px;align-items:center;max-width:860px;margin:10px auto 0}
.pg:has(> article.eng2) > .ph-a .e6-hv .engph{width:100%;max-width:520px;margin:0 auto}
.e6-st{display:grid;grid-template-columns:minmax(0,1fr);gap:0;margin:0 auto;width:100%;max-width:420px;text-align:left}
.e6-s{display:block;padding:10px 0 10px 16px;border-left:4px solid #ffd400;border-top:1px solid #ececf0}
.e6-s:first-child{border-top:0}
.e6-s b{display:block;white-space:nowrap;font-size:32px;font-weight:800;letter-spacing:-.03em;line-height:1;margin:0 0 4px;color:#1d1d1f;font-variant-numeric:tabular-nums}
.e6-s span{display:block;font-size:14px;font-weight:600;color:#6e6e73;line-height:1.25}
@media (min-width:760px){.e6-hv{grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:36px}
.e6-st{margin:0;max-width:none}.e6-s{padding:14px 0 14px 20px}
.e6-s b{font-size:46px;margin:0 0 6px}.e6-s span{font-size:15px}}
.e6-hv.e6-no{grid-template-columns:minmax(0,1fr)}.e6-hv.e6-no .e6-st{margin:0 auto;max-width:420px}
@media (min-width:760px){.e6-hv.e6-no .e6-st{grid-template-columns:repeat(auto-fit,minmax(0,1fr));gap:0 18px;max-width:820px}.e6-hv.e6-no .e6-s{border-top:0}.e6-hv.e6-no .e6-s b{font-size:40px}}
article.eng2 p.tra.e6-in{max-width:600px;margin:16px auto 0;font-size:15px;line-height:1.45;color:#6e6e73;text-align:center}
article.eng2 p.tra.e6-in .shl{margin-left:6px}
.e6-vd{display:block;max-width:640px;margin:22px auto 0;padding:18px 20px;border-radius:18px;background:#f5f5f7;text-align:left}
.e6-vd i{display:inline-block;width:11px;height:11px;border-radius:50%;margin:0 9px 1px 0;vertical-align:middle;background:#8e8e93}
.e6-vd.top i{background:#1f9d55}.e6-vd.chk i{background:#ffd400}.e6-vd.low i{background:#e8141c}
.e6-vd b{display:block;font-size:19px;font-weight:800;letter-spacing:-.015em;color:#1d1d1f}
.e6-vd span{display:block;margin-top:3px;font-size:15px;line-height:1.4;color:#424245}
.e6-vd a{color:#1d1d1f;font-weight:600}
.cpl-b h3.e6-sh{font-size:16px;font-weight:700;margin:18px 0 6px}.cpl-b h3.e6-sh:first-child{margin-top:4px}
</style>'''
_E6_AWAY = re.compile(r'\s*\d+°')   # "90° V8" -> "V8": the bank angle means nothing to a buyer (still in the method box)


def _e6_t(e): return re.sub(r'\s+', ' ', e.get_text(' ', strip=True)) if e else ''


def _e6_years(v):
    """'2023–26' -> '2023–2026' (Elijah: "model years 2023–2026")"""
    m = re.fullmatch(r'((?:19|20)\d\d)\s*[–-]\s*(\d\d)', v.strip())
    if not m: return v
    a = int(m.group(1)); b = a // 100 * 100 + int(m.group(2))
    return f'{a}–{b + 100 if b < a else b}'


def _e6_stat(v, lab):
    """(value, label) of one chip, in plain words"""
    l = lab.lower()
    if l.startswith('model years'): return _e6_years(v), 'Model years' + (' covered' if 'covered' in l else '')
    m = re.match(r'hp \((.*)\)', l)
    if l.startswith('hp'):
        extra = re.sub(r'^(factory|us),?\s*', '', m.group(1)) if m else ''
        return v, 'Horsepower' + (f', {lab[lab.lower().find(extra):-1]}' if extra else '')
    m = re.search(r'#(\d+) of (\d+)', lab)
    if 'youtube' in l and m: return '#' + m.group(1), f'Owner rank on YouTube, of {m.group(2)} engines'
    m = re.search(r'of (\d+)', lab)
    if 'youtube rank' in l and m: return v, f'Owner rank on YouTube, of {m.group(1)} engines'
    if l == 'owner complaints': return v, 'Owner complaints filed'
    if l == 'name the engine': return v, 'of complaints name the engine'
    if l == 'recalls name it': return v, 'Recalls that name the engine'
    return v, lab[:1].upper() + lab[1:]


def _e6_list(xs):
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def _e6_intro(t):
    """one plain line: what the engine is and the first cars it's in (years and counts are in the stat column)"""
    t = re.sub(r'\s*Share ↗\s*$', '', t).strip()
    m = re.match(r'^(.+?) in the (.+?)\s*, model years [^.,(]+(?:\([^)]*\))?(?:, and in the (.+?), (?:19|20)\d\d)?', t)
    m2 = re.match(r'^(.+?)\. This page covers the versions we have sourced so far: the (.+?), model years', t)
    if m2: desc, cars, more = m2.group(1), m2.group(2), None
    elif m: desc, cars, more = m.group(1), m.group(2), m.group(3)
    else: return re.split(r'(?<=[.])\s', t, 1)[0]
    cs = [c.strip() for c in re.split(r',\s+|\s+and\s+', cars) if c.strip()]
    if more: cs.append(more.strip())
    desc = _E6_AWAY.sub('', desc).replace(', DOHC', '').strip()
    shown = _e6_list(cs) if len(cs) <= 4 else ', '.join(cs[:3]) + f' and {len(cs) - 3} more'
    return f'{desc}, in the {shown}.'


_E6_VD = {'a safer bet': ('YouTube owners like it', 'top'), 'liked, but check the recalls': ('Owners like it, but check the recalls', 'chk'),
          'middle of the pack': ('Owners are mixed on it', ''), 'less liked than most on youtube': ('Less liked than most', 'low')}


def _e6_verdict(p, issues_kept):
    b = p.find('b'); lab = _e6_t(b).rstrip(':').strip()
    if b: b.extract()
    t = _e6_t(p); links = p.find_all('a')
    head, cls = _E6_VD.get(lab.lower(), (lab, ''))
    rk = re.search(r'#(\d+) of (\d+) engine', t); th = re.search(r'in the (top|middle|bottom) third', t)
    rc = re.search(r'(no|\d+) engine-related recalls? on record', t); ki = re.search(r'(\d+) known issues? listed below', t)
    bits = []
    if rk: bits.append(f'Ranks in the {th.group(1)} third of {rk.group(2)} engines on YouTube.' if th else f'Ranks #{rk.group(1)} of {rk.group(2)} engines on YouTube.')
    if rc: bits.append('No engine recalls on record.' if rc.group(1) == 'no' else f'{rc.group(1)} engine recall{"s" * (rc.group(1) != "1")} on record.')
    if ki and issues_kept: bits.append(f'{ki.group(1)} known issue{"s" * (ki.group(1) != "1")} below.')
    if not bits: return None
    ln = ' '.join(bits) + ''.join(f' <a href="{html.escape(a.get("href", ""))}">{a.decode_contents()}</a>' for a in links)
    return f'<div class="e6-vd {cls}"><b><i aria-hidden="true"></i>{html.escape(head)}</b><span>{ln}</span></div>'


# box order (item 10): first match wins; unknown boxes sit between YouTube and the cars
_E6_ORDER = [(r'^known issue', 0), (r'complain about|what owners write|when problems show up|in owners|owner complaints and recalls|stands out', 1),
             (r'recall', 2), (r'told dealers|technical|service bulletin', 3), (r'youtube', 4), (r'^__cars__$', 6),
             (r'specs|against the other|side by side|each engine|by generation|compare', 7), (r'quick answers|^questions$', 8),
             (r"don't have yet|do not have yet", 9), (r'^__how__$', 10)]
_E6_CARS = re.compile(r"^(every us version|everyday cars with|cars with this engine|trucks with this engine|in everyday cars|by car$|by truck$|the trucks$)", re.I)
_E6_HOW = re.compile(r"^(how to read this chart|how we count|all the numbers|owner score =|where this data comes from|sources$|what we don't have yet)", re.I)


def _e6_rank(t):
    for pat, n in _E6_ORDER:
        if re.search(pat, t, re.I): return n
    return 5


def _e6_title(d):
    s = d.find('summary', recursive=False); h = s.find(['h2', 'b']) if s else None
    return _e6_t(h) if h else _e6_t(s)


def _e6_merge(soup, parts, title, h2=True):
    """one box from several: the first part's summary (icon, arrow) with the new title; each part's body under its own small heading"""
    first = parts[0][0]
    d = soup.new_tag('details')
    s = copy.copy(first.find('summary', recursive=False)); h = s.find(['h2', 'b'])
    if h is not None:
        nh = soup.new_tag('h2' if h2 else 'b'); nh.string = title
        if h2: nh['class'] = ['cpl-h']
        h.replace_with(nh)
    for sm in s.find_all('small'): sm.decompose()
    d.append(s); body = soup.new_tag('div'); body['class'] = ['cpl-b']; d.append(body)
    for det, ids, t in parts:
        for i in ids:
            a = soup.new_tag('span'); a['id'] = i; body.append(a)
        if len(parts) > 1 or t.lower() != title.lower():
            hh = soup.new_tag('h3'); hh['class'] = ['e6-sh']; hh.string = re.sub(r'…$', '', t); body.append(hh)
        b = det.find('div', class_='cpl-b', recursive=False)
        for c in list((b or det).contents):
            if getattr(c, 'name', None) == 'summary': continue
            body.append(c.extract())
    return d


def ENG6_HOOK(path, body):
    if not _E6_RE.fullmatch(path) or 'eng2' not in body: return body
    try:
        soup = _E6S(body, 'html.parser'); art = soup.find('article', class_='eng2')
        if art is None: return body
        hero = art.find_parent('div', class_='pg'); hero = hero.find('section', class_='ph-a') if hero else None
        # 7. "Too new to judge" as the only known issue -> no box
        issues_kept = True
        for d in art.find_all('details'):
            if not re.match(r'^known issue', _e6_title(d), re.I): continue
            lis = d.select('.cpl-b > ul > li') or d.find_all('li')
            if lis and all(_e6_t(li).lower().startswith('too new to judge') for li in lis):
                sec = d.find_parent('section', class_='cpl-sec')
                (sec if sec is not None and len(sec.find_all('details')) == 1 else d).decompose(); issues_kept = False
        if not issues_kept:
            for tn in art.find_all(string=re.compile(r'known issues? listed below')):
                tn.replace_with(re.sub(r',?\s*\d+ known issues? listed below', '', str(tn)))
        # 3. stat column beside the picture
        trc = art.find('div', class_='trc')
        if trc is not None:
            st = []
            for c in trc.find_all('div', recursive=False):
                v, l = c.find('b'), c.find('span')
                if v is None: continue
                vv, ll = _e6_stat(_e6_t(v), _e6_t(l))
                st.append(f'<div class="e6-s"><b>{html.escape(vv)}</b><span>{html.escape(ll)}</span></div>')
            trc.decompose()
            stats = _E6S(f'<div class="e6-st" aria-label="Engine stats">{"".join(st)}</div>', 'html.parser')
            pv = hero.find('div', class_='ph-v') if hero else None
            fig = pv.find('figure', class_='engph') if pv else None
            if fig is not None:
                box = soup.new_tag('div'); box['class'] = ['e6-hv']; pv.replace_with(box); box.append(fig); box.append(stats)
            else:
                box = soup.new_tag('div'); box['class'] = ['e6-hv', 'e6-no']; box.append(stats)
                h1 = hero.find('h1') if hero else None
                (h1.insert_after(box) if h1 is not None else art.insert(0, box))
        # 4. the intro -> one plain line (the full paragraph goes into the method box)
        tra = art.find('p', class_='tra', recursive=False) if trc is not None else None; full = None
        if tra is not None:
            shl = tra.find('button', class_='shl'); full = copy.copy(tra); full['class'] = ['note']
            for x in full.find_all('button'): x.decompose()
            line = _e6_intro(_e6_t(tra))
            tra.clear(); tra['class'] = ['tra', 'e6-in']; tra.append(line)
            if shl is not None: tra.append(' '); tra.append(shl)
        # 5. the verdict note -> a plain card
        vd = art.find('p', class_='engvd')
        if vd is not None:
            nv = _e6_verdict(vd, issues_kept)
            if nv: vd.replace_with(_E6S(nv, 'html.parser'))
            else: vd.decompose()
        # 8-11. collect every box, merge, order
        boxes, others, chart, head = [], [], [], []
        for c in [c for c in art.children if getattr(c, 'name', None)]:
            cls = c.get('class') or []
            if c.name == 'h2' or (c.name == 'div' and 'egc' in cls): chart.append(c); continue
            ds = []
            if c.name == 'div' and 'cpl' in cls: ds = c.find_all('details', recursive=False)
            elif c.name == 'section' and 'cpl-sec' in cls:
                for cp in c.find_all('div', class_='cpl', recursive=False): ds += cp.find_all('details', recursive=False)
            if ds:
                sid = c.get('id')
                for k, d in enumerate(ds):
                    ids = [sid] if sid and k == 0 else []
                    if d.get('id'): ids.append(d['id']); del d['id']
                    boxes.append((d, ids, _e6_title(d)))
                continue
            (others if (chart or boxes) else head).append(c)
        if not boxes: return str(soup)
        cars = [b for b in boxes if _E6_CARS.match(b[2])]
        how = [b for b in boxes if _E6_HOW.match(b[2])]
        rest = [b for b in boxes if b not in cars and b not in how]
        # a loose source line at the end ("Sources: ...") goes into the method box too
        for c in list(others):
            if c.name == 'p' and 'yc-cap' in (c.get('class') or []) and re.match(r'(sources?|complaints|data)\b', _e6_t(c), re.I):
                hb = _E6S(V5_BOX('info', 'Sources', ''), 'html.parser').details
                hb.find('div').append(c.extract()); others.remove(c); how.append((hb, [], 'Sources'))
        # "What owners write" (the word counts) + "In owners' words" (the quotes) = one box
        ww = [b for b in rest if re.match(r"^(what owners write|in owners)", b[2], re.I)]
        if len(ww) == 2:
            i0 = rest.index(ww[0]); md = _e6_merge(soup, ww, 'What owners write')
            rest = [x for x in rest if x not in ww]; rest.insert(i0, (md, [], 'What owners write'))
        out = []
        if cars:
            cars.sort(key=lambda b: (0 if re.match(r'(everyday cars|cars with|trucks with|the trucks)', b[2], re.I) else 1 if re.match(r'every us', b[2], re.I) else 2))
            tt = 'Trucks with this engine' if any('truck' in b[2].lower() for b in cars) else 'Cars with this engine'
            md = _e6_merge(soup, cars, tt) if len(cars) > 1 else cars[0][0]
            ids = [i for b in cars for i in b[1]] if len(cars) == 1 else []
            if len(cars) == 1:
                for i in ids:
                    a = soup.new_tag('span'); a['id'] = i; md.find('div', class_='cpl-b').insert(0, a)
            cb = md.find('div', class_='cpl-b')
            if cb is not None and cb.find(class_='n3-ml') is not None: cb['class'] = cb.get('class', []) + ['n3-eng']   # n3nav.css styles the year list under .n3-eng
            out.append((_e6_rank('__cars__'), md))
        if how or full is not None:
            how.sort(key=lambda b: (0 if b[2].lower().startswith('all the numbers') else 2 if re.match(r'where this|sources', b[2], re.I) else 1))
            if full is not None:
                hb = _E6S(V5_BOX('info', 'About this engine', ''), 'html.parser').details
                hb.find('div').append(full); how.append((hb, [], 'About this engine'))
            tt = ('Year-by-year numbers and how we count' if how[0][2].lower().startswith('all the numbers') else 'Sources' if all(b[2] in ('Sources', 'About this engine') for b in how) else 'How we count')
            out.append((_e6_rank('__how__'), _e6_merge(soup, how, tt, h2=False)))
        for d, ids, t in rest:
            for i in ids:
                a = soup.new_tag('span'); a['id'] = i
                b_ = d.find('div', class_='cpl-b', recursive=False)
                (b_ if b_ is not None else d).insert(0, a)
            out.append((_e6_rank(t), d))
        out.sort(key=lambda x: x[0])   # stable: same-rank boxes keep their page order
        for c in chart + others: c.extract()
        for c in [c for c in art.children if getattr(c, 'name', None)]:
            if c not in head: c.extract()
        for c in chart: art.append(c)
        sec = _E6S('<section class="cpl-sec e6-bx"><div class="cpl"></div></section>', 'html.parser').section
        cp = sec.find('div')
        for _, d in out: cp.append(d)
        art.append(sec)
        for c in others: art.append(c)
        art.insert(0, _E6S(E6_CSS, 'html.parser'))
        return str(soup)
    except Exception as ex:
        globals().setdefault('TAB_FAIL', []).append(f'ENG6 {path}: {type(ex).__name__} {ex}')
        return body
