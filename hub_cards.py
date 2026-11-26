# 11-26 (Elijah, after the Tacoma mock-up: "this is good to make go live"): model pages (/cars/<model>/) that have every card get
# "Everything about the <car>": big cards (title + one data line on the left, a picture on the right) instead of the Overview list
# and the end-of-page rows, plus 4 small black-icon buttons (Recall alerts, Your opinion, Questions, Data & sources) that open their
# panel in place. exec'd by build.py; HUB_HOOK(path, doc) runs last in page(), after the date hash, so it never moves a page's date.
#   Cards: Before-you-buy checklist (dark, only models in data/checklists.json) · Which years to buy · Can you afford it? ·
#          Problems & repairs · Engines & versions · What owners say · Compare.
#   A page gets the hub only when it has all of them (checklist aside): the years lists, a YouTube study, an engines box or page,
#   owner repair bills or the AI repair estimates (repair_est.py, newest generation) and AI prices (data/price_est.json). Every other page keeps the old layout. Nothing is dropped: each old
#   box's content moves into its card or panel, ids and all (#youtube, #p-years, #p-compare, #recall-alerts, #opinions, #p-questions, #info).
#   11-26 (Elijah: "engine cards... repair costs, we already have AI repair estimates, so just add those"): a model with no engines page or box
#   gets EPA's engines per model year (data/engine_fuels.json); one with no owner bills gets the newest generation's repair estimates.
#   Styles + the panel buttons: assets/hub.css, assets/hub.js. "What owners say" uses the speech-bubble picture: no YouTube logo
#   (trademark rule). "Can you afford it?" = the wallet (gpt-image-2 low, 11-26; the cash stack is assets/icons/cash.webp).
import html as _hbh, re as _hbre, json, os
from bs4 import BeautifulSoup as _HBS

HUB_V = '2'
HUB_ON = True
_HB_PATH = _hbre.compile(r'/cars/([a-z0-9-]+)/')
_HB_GO = ('<svg aria-hidden="true" focusable="false" class="mhc-go" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg>')
_HB_IC = lambda k: f'<svg aria-hidden="true" focusable="false" width="20" height="20"><use href="/assets/ic.svg?v=1#{k}"></use></svg>'
E_ = lambda s: _hbh.escape(str(s), quote=True)
HUB_SEEN = {}   # fid -> True (hub) / list of what's missing, for the end-of-build line + the gap list

def _hb_end(doc, k, tag):
    depth = 0
    for m in _hbre.finditer(rf'<{tag}\b|</{tag}>', doc[k:]):
        depth += 1 if m.group(0) != f'</{tag}>' else -1
        if depth == 0: return k + m.end()
    return -1

def _hb_card(title, sub, img, h2=False, dark=False, href=None, icon=False):
    t = f'<h2 class="mhc-h">{title}</h2>' if h2 else f'<b class="mhc-h">{title}</b>'
    pic = f'<span class="mhc-p{" mhc-ic" if icon else ""}"><img src="{E_(img)}" alt="" loading="lazy" decoding="async"></span>' if img else ''
    inner = f'<span class="mhc-t">{t}<small>{sub}</small></span>{pic}'
    if href: return f'<a class="mhc{" mhc-d" if dark else ""}" href="{E_(href)}">{inner}</a>'
    return f'<summary class="mhc">{inner}</summary>'

def _hb_item(sid, summ, body, cls=''):
    """one grid item: <section id> > .cpl (so the boxes' own .cpl .cpl-b styles still apply) > details(card summary + body)"""
    ida = f' id="{sid}"' if sid else ''
    return f'<section class="mhb-i{cls}"{ida}><div class="cpl"><details class="mhx">{summ}{body}</details></div></section>'

def _hb_inner(el):
    return ''.join(str(c) for c in el.contents)

def _hb_short(doc, fid):
    m = _hbre.search(r'<p class="ph-e n2-cr">(.*?)</p>', doc, _hbre.S)
    if m:
        parts = [x.strip() for x in _hbre.sub(r'<[^>]+>', '', m.group(1)).split('›') if x.strip()]
        if parts: return _hbh.unescape(parts[-1])
    return fid.split('-', 1)[-1].replace('-', ' ').title()

def _hb_name(doc, fid, short):
    m = _hbre.search(r'<p class="ph-e n2-cr">(.*?)</p>', doc, _hbre.S)
    if m:
        parts = [x.strip() for x in _hbre.sub(r'<[^>]+>', '', m.group(1)).split('›') if x.strip()]
        if len(parts) >= 3: return _hbh.unescape(parts[-2] + ' ' + parts[-1])
    return short

def _hb_price_rows(fid):
    """[(year, typical miles, private lo, private hi)] newest first, from data/price_est.json"""
    M = PRICEBOX._data()['m'].get(fid)
    if not M: return []
    out = []
    for y, r in M['y'].items():
        a = r[2] if len(r) > 2 and r[2] else None
        if a: out.append((int(y), r[0], a[0], a[1]))
    return sorted(out, reverse=True)

def _hb_yt(fid):
    f = FY.get(fid) if 'FY' in globals() else None
    if not f: return '', None
    sc = YTS.get(fid) or {}; nv = round(sum(s.get('videos') or 0 for s in sc.values()))
    rk = yt_rank_map(f); fav = min(rk, key=rk.get) if len(rk) >= 3 else None
    return nv, fav

def _hb_est(fid):
    """(newest generation id, its repair slugs owners name most, with a number) from the AI repair estimates, or None"""
    if 'REST' not in globals(): return None
    D = REST._data(); gs = REST.gens_of(fid)
    if not gs: return None
    gid = gs[-1]; g = D['gens'][gid]; pop = D['pop']
    shown = [x for x in sorted(g['r'], key=lambda x: (-pop.get(x, 0), D['names'].get(x, x))) if any(r[5] != 'X' for r in g['r'][x])]
    return (gid, shown) if len(shown) >= 3 else None

_HB_EF = None
_HB_FUEL = {'gas': 'Gas', 'diesel': 'Diesel', 'hybrid': 'Hybrid', 'phev': 'Plug-in hybrid', 'electric': 'Electric'}
def _hb_epa(fid):
    """[(engine, fuel word, 'years')] newest first, from EPA's version list (data/engine_fuels.json, made by data_engine_fuels.py)"""
    global _HB_EF
    if _HB_EF is None:
        _HB_EF = json.load(open('data/engine_fuels.json', encoding='utf-8')) if os.path.exists('data/engine_fuels.json') else {}
    by = {}
    for y, es in (_HB_EF.get(fid) or {}).items():
        for e, fu, mo in es:
            if fu == 'electric':
                kw = _hbre.findall(r'(\d+)\s*kW', mo or ''); lab = f'Electric motor ({"+".join(kw)} kW)' if kw else 'Electric motor'
            else:
                m = _hbre.fullmatch(r'([\d.]+)L (\d+)-cyl', e); lab = f'{m.group(1)} L {m.group(2)}-cylinder' if m else e
            by.setdefault((lab, _HB_FUEL.get(fu, fu)), set()).add(int(y))
    def span(ys):
        ys = sorted(ys); out = []; a = b = ys[0]
        for y in ys[1:]:
            if y == b + 1: b = y
            else: out.append((a, b)); a = b = y
        out.append((a, b)); return ', '.join(f'{a}–{b}' if a != b else str(a) for a, b in reversed(out))
    return [(lab, fu, span(ys)) for (lab, fu), ys in sorted(by.items(), key=lambda t: (-max(t[1]), t[0]))]

def _hb_check(doc, fid):
    """what this model page is missing for the hub ([] = gets it)"""
    miss = []
    if 'id="p-years"' not in doc: miss.append('years')
    if 'id="youtube"' not in doc or 'yot-q' in doc: miss.append('youtube')
    if f'href="/cars/{fid}/engines/"' not in doc and 'Engines &amp; versions' not in doc and not _hb_epa(fid): miss.append('engines')
    if 'What owners paid for repairs' not in doc and not _hb_est(fid): miss.append('repairs')
    if not _hb_price_rows(fid): miss.append('price')
    return miss

def HUB_HOOK(path, doc):
    m = _HB_PATH.fullmatch(path)
    if not (HUB_ON and m) or '<div class="tbx">' not in doc or 'mh-acts' not in doc: return doc
    fid = m.group(1)
    miss = _hb_check(doc, fid); HUB_SEEN[fid] = miss or True
    if miss: return doc
    i = doc.find('<div class="tbx">'); a0 = doc.find('<div class="cpl-grp mh-acts', i)
    if a0 < 0: return doc
    a1 = _hb_end(doc, a0, 'div')
    if a1 < 0: return doc
    s = _HBS(doc[i:a1], 'html.parser')
    short = _hb_short(doc, fid); name = _hb_name(doc, fid, short)
    if _hbre.fullmatch(r'[\d\s-]+|.{1,3}', short): short = name   # 'Ram 1500', not 'the 1500'
    g1 = s.select_one('.cpl-g1'); g2 = s.select_one('.cpl-g2'); acts = s.select_one('.mh-acts')
    if g1 is None or acts is None: return doc
    take = lambda sel, root=s: (root.select_one(sel).extract() if root.select_one(sel) is not None else None)
    years = take('#p-years'); bud = take('#p-budget'); yt = take('#youtube'); qa = take('#p-questions')
    eng = next((x for x in g1.select(':scope > section.cpl-sec') if 'Engines & versions' in x.get_text(' ', strip=True)[:40]), None)
    if eng is not None: eng.extract()
    rep = cod = None
    for x in g1.select(':scope > div.cpl-one'):
        t = x.get_text(' ', strip=True)[:60]
        if t.startswith('What owners paid for repairs'): rep = x.extract()
        elif t.startswith('Engine codes owners report'): cod = x.extract()
    ral = take('#recall-alerts', acts); opn = take('#opinions', acts); cmp = take('#p-compare', acts); info = take('#info', acts)
    est = _hb_est(fid) if rep is None else None
    if years is None or yt is None or (rep is None and est is None) or cmp is None: return doc
    cards = []
    # 1. checklist (dark): the newest generation's checklist, its picture from a year in that generation
    gens = _YUX_CL.get(fid) if '_YUX_CL' in globals() else None
    if gens:
        g, ga, gb = max(gens, key=lambda r: r[2])
        ys = [y for y in range(gb, ga - 1, -1) if YSL.ai_src(fid, y)]
        im = rsmall(YSL.ai_src(fid, ys[0])) if ys else f'/assets/ai-models/{fid}.webp'
        cards.append(f'<div class="mhb-i mhb-d">{_hb_card("Before-you-buy checklist", "Step by step at the car · your first one is free", im, dark=True, href="/checklist/" + fid + "-" + g + "/")}</div>')
    # 2. which years to buy
    best = years.select_one('.bw3c .bw3r.good b') or years.select_one('.bw2 .bwt h2'); worst = [c for c in years.select('.bw3c') if 'Most' in c.get_text(' ', strip=True)[:20]]
    worst = worst[0].select_one('.bw3r b') if worst else None
    ny = len(set(_hbre.findall(rf'href="/cars/{_hbre.escape(fid)}/(\d{{4}})/"', doc)))
    sub = ' · '.join(x for x in ((f'Fewest complaints {best.get_text(strip=True).rstrip(".")}' if best else ''), (f'most {worst.get_text(strip=True)}' if worst else '')) if x) or f'All {ny} years'
    years['class'] = [c for c in years.get('class', []) if c != 'cpl-open']
    for k in ('role', 'tabindex', 'aria-labelledby'): years.attrs.pop(k, None)
    cards.append(_hb_item('mhb-years', _hb_card('Which years to buy', sub, '/assets/icons/chart.webp', icon=True), f'<div class="cpl-b">{years}</div>'))
    # 3. can you afford it? the private-seller price at each year's typical miles (AI estimate), then the money links
    pr = _hb_price_rows(fid); lo = min(r[2] for r in pr); hi = max(r[3] for r in pr)
    def prow(r):
        y, mi, a, b = r
        return (f'<a class="mhb-pr" href="/cars/{fid}/{y}/#price-guide"><b>{y}</b><span>about {round(mi / 1000):,}K miles</span>'
                f'<em>${a:,}–{b:,}</em></a>')
    top, rest = pr[:8], pr[8:]
    more = (f'<details class="mhb-more"><summary>Older years ({len(rest)})</summary><div class="mhb-prs">{"".join(prow(r) for r in rest)}</div></details>' if rest else '')
    bh = PRICEBOX.budget_href(fid, None)
    af = (f'<div class="cpl-b mhb-af"><p class="mhb-lab">What a used {E_(short)} sells for</p><p class="mhb-cap">Private seller, at each year&#39;s typical miles. Tap a year for every mileage.</p>'
          f'<div class="mhb-prs">{"".join(prow(r) for r in top)}</div>{more}'
          f'<p class="mhb-cap">Lemon Index estimates (AI, {E_(PRICEBOX._data().get("date", ""))}), not listings or an appraisal. Dealers usually ask more.</p>'
          f'<div class="mhb-bt"><a href="{E_(bh)}">Find a car for your budget</a><a href="/insurance/">Compare insurers</a><a href="/car-loan-rates/">Car loan rates</a></div></div>')
    cards.append(_hb_item('mhb-afford', _hb_card('Can you afford it?', f'Used: ${lo:,} to ${hi:,}', '/assets/icons/wallet.webp', icon=True), af))
    # 4. problems & repairs: owner repair bills, the engine codes owners name, the recall list
    rb = rep.select_one('.cpl-b') if rep is not None else None; top_r = rb.select_one('.n3-c b') if rb else None
    rl = next(iter(_hbre.findall(r'href="(/recalls/[a-z0-9-]+/[a-z0-9-]+/)"', doc)), None)
    pb = f'<div class="cpl-b mhb-pb{" rst" if est else ""}">'
    if rb is not None: pb += f'<p class="mhb-lab">What owners paid for repairs</p>{_hb_inner(rb)}'
    elif est:   # no owner bills on this page: the AI repair estimates for the newest generation (same rows as the year pages' #estimates)
        gid, shown = est; uid = 'hub' + _hbre.sub(r'[^a-z0-9]', '', gid); g = REST._data()['gens'][gid]
        pb += (f'{REST.CSS}<p class="mhb-lab">What repairs should cost</p><p class="mhb-cap">Estimates for the {E_(REST.gen_label(gid))} {E_(short)}, one repair at an independent shop.</p>'
               + REST.rate_input(uid) + '<ul class="rst-list">' + ''.join(h for x in shown[:8] for h in REST._rows(gid, x)) + '</ul>' + REST.legend(uid)
               + (f'<div class="mhb-bt"><a href="/cars/{fid}/{g["sy"][1]}/#estimates">All {len(shown)} repairs</a></div>' if len(shown) > 8 and f'href="/cars/{fid}/{g["sy"][1]}/"' in doc else '')
               + REST.JS)
    cb = cod.select_one('.cpl-b') if cod is not None else None
    if cb is not None: pb += f'<p class="mhb-lab">Check-engine codes owners report most</p>{_hb_inner(cb)}'
    if rl: pb += f'<div class="mhb-bt"><a href="{rl}">Every {E_(short)} recall</a></div>'
    pb += '</div>'
    tr = _hbre.sub(r'\s*\(.*?\)', '', top_r.get_text(strip=True).replace(' replacement', '').replace(' repair', '')) if top_r else ''
    sub = ' · '.join(x for x in ((f'Top repair: {E_(tr)}' if tr else ('Repair cost estimates' if est else 'What owners paid')), ('recalls' if rl else '')) if x)
    cards.append(_hb_item('mhb-problems', _hb_card('Problems &amp; repairs', sub, '/assets/icons/wrench.webp', icon=True), pb))
    # 5. engines & versions: its own page, or the old box's content
    def eng_img(root):
        im = root.select_one('.n3-ig img') if root is not None else None
        return im.get('src') if im is not None else None
    if f'href="/cars/{fid}/engines/"' not in doc and eng is None:   # no engines page or box: EPA's engines per model year
        ep = _hb_epa(fid); fus = sorted({fu for _, fu, _ in ep}, key=list(_HB_FUEL.values()).index) if ep else []
        sub = ' · '.join(x for x in ((f'{len(ep)} engines' if len(ep) > 1 else ep[0][0]), (' or '.join(fus).capitalize() if (len(fus) > 1 or fus != ['Gas']) and not (len(ep) == 1 and fus[0] in ep[0][0]) else '')) if x)
        rows = ''.join(f'<div class="mhb-pr mhb-er"><b>{E_(lab)}</b><span>{E_(fu)}</span><em>{E_(ys)}</em></div>' for lab, fu, ys in ep)
        eb = (f'<div class="cpl-b mhb-af"><p class="mhb-lab">Engines in the {E_(short)}, by model year</p><div class="mhb-prs">{rows}</div>'
              f'<p class="mhb-cap">Every engine EPA lists for the {E_(short)} (fueleconomy.gov).</p></div>')
        cards.append(_hb_item('mhb-engines', _hb_card('Engines &amp; versions', sub, '/assets/icons/engine.webp', h2=True, icon=True), eb))
    elif f'href="/cars/{fid}/engines/"' in doc:
        us = [u for u, cs in (ENGINE_USES.items() if 'ENGINE_USES' in globals() else []) if fid in cs]
        im = None
        for u in us:
            sl = u.strip('/').split('/')[-1]
            hit = sorted(x for x in os.listdir('assets/engines') if x.startswith(sl + '-') and x.endswith('-640.webp')) if os.path.isdir('assets/engines') else []
            if hit: im = '/assets/engines/' + hit[0]; break
        sub = f'{len(us)} engines · every version' if len(us) > 1 else 'Every engine and version'
        cards.append(f'<div class="mhb-i">{_hb_card("Engines &amp; versions", sub, im or "/assets/icons/engine.webp", href="/cars/" + fid + "/engines/", icon=not im)}</div>')
    else:
        eb = eng.select_one('details > .cpl-b'); n = len(eng.select('.n3-ig .n3-c')); im = eng_img(eng)
        sub = ' · '.join(x for x in ((f'{n} engine{"s" if n != 1 else ""} in this car' if n else 'Engines in this car'), ('gas or hybrid' if eng.select_one('#gas-hybrid') else '')) if x)
        cards.append(_hb_item('mhb-engines', _hb_card('Engines &amp; versions', sub, im or '/assets/icons/engine.webp', h2=True, icon=not im), str(eb) if eb else ''))
    # 6. what owners say (YouTube study): its own page, or the old box's content
    nv, fav = _hb_yt(fid)
    sub = ' · '.join(x for x in ((f'{nv:,} YouTube videos' if nv else 'YouTube owner videos'), (f'favorite year {fav}' if fav else '')) if x)
    if f'href="/cars/{fid}/youtube/"' in doc:
        cards.append(f'<div class="mhb-i" id="youtube">{_hb_card("What owners say", sub, "/assets/icons/talk.webp", href="/cars/" + fid + "/youtube/", icon=True)}</div>')
    else:
        yb = yt.select_one('details > .cpl-b')
        cards.append(_hb_item('youtube', _hb_card('What owners say', sub, '/assets/icons/talk.webp', h2=True, icon=True), str(yb) if yb else ''))
    # 7. compare
    riv = []
    for mu in cmp.select('.mu'):   # the rival's full name from its picture's alt (the label's 'vs Ram pickup' would shorten badly)
        alts = [im.get('alt', '') for im in mu.select('img.r') if im.get('alt')]   # the left picture is always this car
        r = alts[0] if alts else _hbre.sub(r'^vs\s+', '', mu.select_one('b').get_text(strip=True) if mu.select_one('b') else '')
        if r and r not in riv: riv.append(r)
    riv = riv[:2] if sum(len(r) for r in riv[:2]) <= 34 else riv[:1]
    cb2 = cmp.select_one('details > .cpl-b')
    cards.append(_hb_item('p-compare', _hb_card('Compare', ('vs ' + ', '.join(E_(r) for r in riv)) if riv else 'Side by side with any car', '/assets/icons/scale.webp', icon=True),
                          str(cb2) if cb2 else ''))
    # the small buttons + their panels (each old section keeps its id inside the panel)
    def unwrap(sec):
        if sec is None: return ''
        d = sec.select_one(':scope > .cpl > details'); b = d.select_one(':scope > .cpl-b') if d is not None else None
        if b is not None: d.replace_with(b)
        return str(sec)
    pans = [('hx-alerts', 'bell', 'Recall alerts', str(ral) if ral is not None else ''), ('hx-opinion', 'opinion', 'Your opinion', str(opn) if opn is not None else ''),
            ('hx-qa', 'question', 'Questions', unwrap(qa)), ('hx-data', 'data', 'Data &amp; sources', unwrap(info))]
    pans = [p for p in pans if p[3]]
    btns = ''.join(f'<a class="mhb-b" href="#{k}" aria-controls="{k}" aria-expanded="false">{_HB_IC(ic)}<span>{lab}</span></a>' for k, ic, lab, _ in pans)
    panels = ''.join(f'<div class="mhb-p cpl" id="{k}">{body}</div>' for k, _, _, body in pans)
    hub = (f'<link rel="stylesheet" href="/assets/hub.css?v={HUB_V}"><script src="/assets/hub.js?v={HUB_V}" defer></script>'
           f'<section class="mhb" aria-labelledby="mhb-h"><h2 class="mhb-h" id="mhb-h">Everything about the {E_(short)}</h2>'
           f'<div class="mhb-g">{"".join(cards)}</div><nav class="mhb-sm" aria-label="More about the {E_(name)}">{btns}</nav>{panels}</section>')
    # what's left in the old groups (notes and the like) stays, under the hub
    left = ''
    for grp in (g1, g2, acts):
        if grp is not None and grp.find(True) is not None and grp.get_text(strip=True): left += str(grp.extract())
        elif grp is not None: grp.decompose()
    ov = s.select_one('#p-overview')
    if ov is None: return doc
    ov.insert(0, _HBS(hub + left, 'html.parser'))
    return doc[:i] + str(s) + doc[a1:]
