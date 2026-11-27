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

HUB_V = '4'
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

def _hb_model_full(path, doc):
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

# ---- 11-26 r2 (Elijah: "start all year pages switch over and 98 models") -------------------------------------------------------------
# (A) every car year page /cars/<model>/<year>/ and (B) the model pages without the end-of-page action group (complaint-only models with no
# sales figure, the BMW spec pages, the heavy-duty trucks, the F-Series, the Sprinter) get the same hub, built from whichever boxes the page
# has. A card shows only when its box is on the page, and its one data line comes from that page's own data (complaint, recall and repair
# counts, the AI price, the YouTube rank): never a made-up number. Each box's content moves into its card or panel with its ids (#p-problems,
# #recalls, #price-guide, #p-years, #opinions, #similar, #p-questions, #ask-seller, #info...); a box the hub doesn't know stays below it.
# Year pages need the years list + the Problems box; model pages the years list + problems or repair costs. Pilot cars (SUB_CAR_PILOT)
# keep their own sub-pages: a box that is a link row becomes a link card. The hero above (score bar, All N years / Compare) is untouched.
# Performance pages (perf_page.py) are left alone.
HUB_COUNT = {'year': 0, 'model': 0}
HUB_OLD = {}   # path -> why it kept the old layout (end-of-build line)
_HY_YEAR = _hbre.compile(r'/cars/([a-z0-9-]+)/(\d{4})/')
_HY_IC2 = lambda k: f'<svg aria-hidden="true" focusable="false" width="20" height="20"><use href="/assets/ic.svg?v=2#{k}"></use></svg>'
_HY_IMG = lambda k: f'/assets/icons/{k}.webp'

def _hy_box(sec):
    """('box', its .cpl-b) / ('link', href) / (None, None)"""
    if sec is None: return None, None
    d = sec.select_one(':scope > .cpl > details')
    if d is not None:
        b = d.select_one(':scope > .cpl-b')
        return ('box', b) if b is not None else (None, None)
    a = sec.select_one(':scope > .cpl > a[href]')
    return ('link', a['href']) if a is not None else (None, None)

def _hy_ttl(sec):
    t = sec.select_one(':scope > .cpl > details > summary h2, :scope > .cpl > details > summary b, :scope > .cpl > a b') if sec is not None else None
    return t.get_text(' ', strip=True) if t is not None else ''

def _hy_card(sec, cid, title, sub, img, h2=False, icon=True, extra=''):
    """a big card from one old box (+ extra body html); '' when there is nothing to show"""
    k, b = _hy_box(sec)
    if k == 'link' and not extra:
        return f'<div class="mhb-i" id="{cid}">{_hb_card(title, sub, img, href=b, icon=icon)}</div>'
    body = (str(b) if k == 'box' else '') + extra
    if k == 'link': body += f'<div class="cpl-b"><div class="mhb-bt"><a href="{E_(b)}">See the full page</a></div></div>'
    return _hb_item(cid, _hb_card(title, sub, img, h2=h2, icon=icon), body) if body else ''

def _hy_unwrap(sec, keep_title=False):
    """a box for a panel: no tap-to-open of its own; keep_title keeps its heading (an h2) above the content"""
    if sec is None: return ''
    d = sec.select_one(':scope > .cpl > details')
    if d is not None:
        b = d.select_one(':scope > .cpl-b'); h = d.select_one(':scope > summary h2')
        if b is not None:
            if keep_title and h is not None: b.insert(0, _HBS(f'<h2 class="mhb-ph">{E_(h.get_text(" ", strip=True))}</h2>', 'html.parser'))
            d.replace_with(b)
    return str(sec)

def _hy_take(root, sel):
    """the first box matching sel that sits straight in an Overview group (never one nested inside another box)"""
    for x in root.select(sel):
        if x.parent is not None and 'cpl-grp' in (x.parent.get('class') or []): return x.extract()
    return None

def _hy_eng(root):
    for g in root.select('div.cpl-grp'):
        for x in g.select(':scope > section.cpl-sec'):
            if _hy_ttl(x).startswith('Engines'): return x.extract()
    return None

def _hy_outside(rest, cls):
    """(html of the group div with this class after the tab box, its start, its end) or (None, -1, -1); stops at </main>"""
    stop = rest.find('</main>'); k = rest.find(f'<div class="cpl-grp {cls}')
    if k < 0 or (stop >= 0 and k > stop): return None, -1, -1
    e = _hb_end(rest, k, 'div')
    return (rest[k:e], k, e) if e > 0 else (None, -1, -1)

def _hy_small(link_secs, pans):
    """the small buttons: links (budget, insurers; each keeps its box id) then the panel buttons; the panels under them"""
    btns = ''.join(f'<a class="mhb-b" id="{sid}" href="{E_(h)}">{ic}<span>{lab}</span></a>' for sid, h, ic, lab in link_secs)
    btns += ''.join(f'<a class="mhb-b" href="#{k}" aria-controls="{k}" aria-expanded="false">{_HB_IC(ic)}<span>{lab}</span></a>' for k, ic, lab, _ in pans)
    return btns, ''.join(f'<div class="mhb-p cpl" id="{k}">{body}</div>' for k, _, _, body in pans)

def _hy_hub(h2, cards, btns, panels, label):
    return (f'<link rel="stylesheet" href="/assets/hub.css?v={HUB_V}"><script src="/assets/hub.js?v={HUB_V}" defer></script>'
            f'<section class="mhb" aria-labelledby="mhb-h"><h2 class="mhb-h" id="mhb-h">{h2}</h2>'
            f'<div class="mhb-g">{"".join(c for c in cards if c)}</div><nav class="mhb-sm mhb-n{btns.count('class="mhb-b"')}" aria-label="{E_(label)}">{btns}</nav>{panels}</section>')

def _hy_left(*grps):
    left = ''
    for grp in grps:
        if grp is None: continue
        if grp.find(True) is not None and grp.get_text(strip=True): left += str(grp.extract())
        else: grp.decompose()
    return left

def _hy_years_clean(yrs):
    yrs['class'] = [c for c in yrs.get('class', []) if c != 'cpl-open']
    for k in ('role', 'tabindex', 'aria-labelledby'): yrs.attrs.pop(k, None)
    return f'<div class="cpl-b">{yrs}</div>'

def _hy_checklist(fid, y=None):
    """the dark Before-you-buy checklist card: the generation holding this year (year pages) or the newest one (model pages)"""
    gens = _YUX_CL.get(fid) if '_YUX_CL' in globals() else None
    if not gens: return ''
    if y is None: g, ga, gb = max(gens, key=lambda r: r[2])
    else:
        hit = [r for r in gens if r[1] <= y <= r[2]]
        if not hit: return ''
        g, ga, gb = hit[0]
    ys = ([y] if y is not None else []) + [z for z in range(gb, ga - 1, -1) if z != y]
    src = next((YSL.ai_src(fid, z) for z in ys if YSL.ai_src(fid, z)), None)
    im = rsmall(src) if src else (f'/assets/ai-models/{fid}.webp' if os.path.exists(f'assets/ai-models/{fid}.webp') else _HY_IMG('car'))
    return f'<div class="mhb-i mhb-d">{_hb_card("Before-you-buy checklist", "Step by step at the car · your first one is free", im, dark=True, href="/checklist/" + fid + "-" + g + "/")}</div>'

def _hy_engines_year(fid, y):
    """[(engine, fuel word)] EPA lists for this model year (data/engine_fuels.json)"""
    _hb_epa(fid)   # loads _HB_EF
    out = []
    for e, fu, mo in (_HB_EF.get(fid) or {}).get(str(y), []):
        if fu == 'electric':
            kw = _hbre.findall(r'(\d+)\s*kW', mo or ''); lab = f'Electric motor ({"+".join(kw)} kW)' if kw else 'Electric motor'
        else:
            m = _hbre.fullmatch(r'([\d.]+)L (\d+)-cyl', e); lab = f'{m.group(1)} L {m.group(2)}-cylinder' if m else e
        if (lab, _HB_FUEL.get(fu, fu)) not in out: out.append((lab, _HB_FUEL.get(fu, fu)))
    return out

def _hy_year(path, doc, fid, y):
    """(new doc, '') or (doc, why it kept the old layout)"""
    F = FY.get(fid) if 'FY' in globals() else None   # None on the heavy-duty trucks' year pages (their own template): data lines come from the page
    v = next((w for w in (F or {}).get('years', []) if w['y'] == y), None) or {}
    i = doc.find('<div class="tbx">'); j = _hb_end(doc, i, 'div') if i >= 0 else -1
    if j < 0: return doc, 'no tab box'
    s = _HBS(doc[i:j], 'html.parser')
    ov = s.select_one('#p-overview'); g1 = s.select_one('.cpl-g1'); g2 = s.select_one('.cpl-g2'); g4 = s.select_one('.cpl-g4')
    if ov is None or g1 is None: return doc, 'no Overview list'
    T = lambda sel: _hy_take(s, sel)
    bud, ins, prob, rep, rec = T('#p-budget'), T('#p-ins'), T('#p-problems'), T('#p-repairs'), T('#p-recalls')
    mil, pg, qa, ask, yrs, info = T('#mileage-guide'), T('#price-guide'), T('#p-questions'), T('#ask-seller'), T('#p-years'), T('#info')
    fos, hde, hyb = T('#fix-or-sell'), T('#hdeng'), T('#hybrid')
    eng = _hy_eng(s)
    if prob is None or yrs is None: return doc, 'no years list or Problems box'
    for x in s.select('.yux-entry'): x.decompose()   # the old entry cards (checklist + /afford/): the checklist card replaces them
    x = extra(fid, y) if F else {}; short = _hb_short(doc, fid)
    if F: nm = SNM(F)
    else:
        cm = _hbre.search(r'<p class="ph-e n2-cr">(.*?)</p>', doc, _hbre.S)
        cp = [z.strip() for z in _hbre.sub(r'<[^>]+>', '', cm.group(1)).split('›') if z.strip()] if cm else []
        h1 = _hbre.search(r'<h1[^>]*>(.*?)</h1>', doc, _hbre.S)   # "2010 Chevrolet Silverado 2500HD/3500HD problems, engines and recalls."
        hn = _hbre.split(r'\s+(?:reliability|problems)\b|[:,.]\s', _hbre.sub(r'^\s*\d{4}\s+', '', _hbre.sub(r'<[^>]+>', ' ', h1.group(1))).strip())[0].strip() if h1 else ''
        nm = _hbh.unescape(' '.join(hn.split())) if hn else (_hbh.unescape(' '.join(cp[-3:-1])) if len(cp) >= 3 else fid.replace('-', ' ').title())
    if _hbre.fullmatch(r'[\d\s-]+|.{1,3}', short) or short == str(y): short = nm
    rest = doc[j:]
    # outside the tab box: the owners' opinions (cpl-g3) and Similar cars (cpl-rel)
    g3h, a3, b3 = _hy_outside(rest, 'cpl-g3'); opn = None
    if g3h:
        g3 = _HBS(g3h, 'html.parser'); opn = g3.select_one('#opinions')
        if opn is not None: opn.extract()
        rest = rest[:a3] + _hy_left(g3.select_one('div.cpl-grp')) + rest[b3:]
    rlh, a4, b4 = _hy_outside(rest, 'cpl-rel'); sim = None
    if rlh:
        rl = _HBS(rlh, 'html.parser'); sim = rl.select_one('#similar')
        if sim is not None:
            sim.extract(); rest = rest[:a4] + _hy_left(rl.select_one('div.cpl-grp')) + rest[b4:]
    cards = [_hy_checklist(fid, y)]
    # what it's worth: the price box (its private-seller range at the year's typical miles), + Fix or sell?
    ext = _hy_unwrap(fos, True) if fos is not None else ''
    fos_left = ''
    money = [(sid, kb[1], ic, lab) for sec, sid, ic, lab in ((bud, 'p-budget', 'search', 'Your budget'), (ins, 'p-ins', 'shield', 'Insurance')) for kb in [_hy_box(sec)] if kb[0] == 'link']
    if pg is not None:   # the money links sit in this card (as on the model hub's "Can you afford it?"), each keeping its old box id
        a = PRICEBOX.at_price(fid, y)
        mb = ('<div class="mhb-bt">' + ''.join(f'<a id="{sid}" href="{E_(h)}">{"Find a car for your budget" if sid == "p-budget" else "Compare insurers"}</a>' for sid, h, _, _ in money)
              + '</div>') if money else ''
        kb = _hy_box(pg)
        if mb and kb[0] == 'box': kb[1].append(_HBS(mb, 'html.parser')); mb = ''   # under the price table, in the same box
        cards.append(_hy_card(pg, 'price-guide', 'What it&#39;s worth', f'Private seller: ${a[0]:,}–{a[1]:,}' if a else 'Fair price by mileage', _HY_IMG('tag'), h2=True,
                              extra=(f'<div class="cpl-b">{ext}</div>' if ext else '') + (f'<div class="cpl-b">{mb}</div>' if mb else '')))
        money = []
    else: fos_left = ext
    # problems: complaints filed so far + the area named most (first 3 years)
    n = (x.get('sev') or {}).get('total') or v.get('n') or 0
    top = NICE(v['parts'][0][0]) if v.get('parts') else ''
    if F: sub = ' · '.join(z for z in ((f'{n:,} owner complaint{"" if n == 1 else "s"}' if n else 'No owner complaints yet'), (f'top: {E_(top)}' if top else '')) if z)
    else:
        tp = prob.select_one('#problems td, #problems .pt span'); sub = f'Most complaints: {E_(tp.get_text(strip=True))}' if tp is not None else 'What owners report'
    cards.append(_hy_card(prob, 'p-problems', 'Problems', sub, _HY_IMG('warning')))
    # repairs & costs: the area owners named a bill for most (repair_costs.py, same generation as the box) + how many AI estimates
    if rep is not None:
        d = next((e for e in YTV.get(fid, []) if e['years'] is None or y in e['years']), None) if 'YTV' in globals() else None
        gy = (d or {}).get('years'); y0, y1 = (min(gy), max(gy)) if gy else (y - 2, y + 2)
        shown = [a for a in RCQ.areas(fid, y0, y1) if a[1] >= RCQ.MIN_N]
        gid = REST.gen_for(fid, y); ne = 0
        if gid:
            gg = REST._data()['gens'][gid]; ne = len(gg['r']) if sum(1 for z in gg['r'] if any(r[5] != 'X' for r in gg['r'][z])) >= 3 else 0
        sub = ' · '.join(z for z in ((f'Top repair: {E_(shown[0][0])}' if shown else ''), (f'{ne} estimates' if ne else '')) if z) or 'What repairs cost'
        cards.append(_hy_card(rep, 'p-repairs', 'Repairs &amp; costs', sub, _HY_IMG('wrench')))
    # recalls & safety: recall count + NHTSA's best overall crash rating
    if rec is not None:
        rc = x.get('recalls') if 'recalls' in x else None; sf = x.get('safety') or {}; best = sf.get('best')
        if rc is None:
            nr = rec.select_one('#recalls .yc-n'); nr = nr.get_text(strip=True) if nr is not None else ''
            rc = [0] * int(nr) if nr.isdigit() else None
        sub = ' · '.join(z for z in (((f'{len(rc)} recall{"" if len(rc) == 1 else "s"}' if rc else 'No recalls') if rc is not None else ''),
                                     (f'{best}-star crash test' if str(best).isdigit() else '')) if z) or 'Recalls and crash tests'
        cards.append(_hy_card(rec, 'p-recalls', 'Recalls &amp; safety', sub, _HY_IMG('bell')))
    # when problems show up: the middle half of the mileage owners gave (20+ complaints); no answer = the box goes to Data & sources
    mil_pan = ''
    if mil is not None:
        mm = x.get('miles') or {}
        if mm.get('n', 0) >= 20 and mm.get('p25') is not None:
            cards.append(_hy_card(mil, 'mileage-guide', 'When problems show up', f'Most between {_mi_r(mm["p25"])} and {_mi_r(mm["p75"])} miles', _HY_IMG('stopwatch'), h2=True))
        elif _hy_box(mil)[0] == 'link':
            cards.append(_hy_card(mil, 'mileage-guide', 'When problems show up', 'The miles owners gave', _HY_IMG('stopwatch'), h2=True))
        else: mil_pan = _hy_unwrap(mil, True)
    # engines: the old box (its engines with pages), else EPA's list for this year; + Which diesel / Gas or hybrid
    hde_t = _hy_ttl(hde) if hde is not None else ''
    ext = ''.join(f'<div class="cpl-b">{_hy_unwrap(z, True)}</div>' for z in (hde, hyb) if z is not None)
    if eng is not None:
        names = [b.get_text(' ', strip=True) for b in eng.select('.n3-c b')]
        ep = _hy_engines_year(fid, y) if not names else []
        sub = (names[0] if len(names) == 1 else f'{len(names)} engines') if names else ((ep[0][0] if len(ep) == 1 else f'{len(ep)} engines') if ep else f'Every engine in the {y}')
        im = eng.select_one('.n3-ig img'); im = im.get('src') if im is not None else None
        cards.append(_hy_card(eng, 'mhb-engines', 'Engines &amp; versions', E_(sub), im or _HY_IMG('engine'), h2=True, icon=not im, extra=ext))
    else:
        ep = _hy_engines_year(fid, y)
        if ep or ext:
            rows = ''.join(f'<div class="mhb-pr mhb-er"><b>{E_(lab)}</b><span>{E_(fu)}</span><em></em></div>' for lab, fu in ep)
            eb = (f'<div class="cpl-b mhb-af"><p class="mhb-lab">Engines in the {y} {E_(short)}</p><div class="mhb-prs">{rows}</div>'
                  f'<p class="mhb-cap">Every engine EPA lists for the {y} {E_(short)} (fueleconomy.gov).</p></div>') if ep else ''
            sub = (ep[0][0] if len(ep) == 1 else f'{len(ep)} engines') if ep else (hde_t if hde is not None else 'Gas or hybrid')
            cards.append(_hb_item('mhb-engines', _hb_card('Engines &amp; versions', E_(sub), _HY_IMG('engine'), h2=True, icon=True), eb + ext))
    # which years to buy: the model's fewest / most complaints per car sold (scored years)
    ok = [w for w in (F or {}).get('years', []) if w.get('ok') and w.get('li') is not None and not w.get('early')]   # early reads (too new) aren't a fair best / worst
    if len(ok) >= 2:
        bw = min(ok, key=lambda w: w['li']); ww = max(ok, key=lambda w: w['li'])
        sub = f'Fewest complaints {bw["y"]} · most {ww["y"]}'
    elif F: sub = f'All {len(F["years"])} years'
    else:   # heavy-duty year pages: their list shows the years either side of this one
        hh = yrs.select_one('h2'); sub = E_(hh.get_text(' ', strip=True).rstrip('.')) if hh is not None else 'The years around it'
    cards.append(_hb_item('mhb-years', _hb_card('Which years to buy' if F else 'Other model years', sub, _HY_IMG('chart'), icon=True), _hy_years_clean(yrs)))
    # what owners say: the year's YouTube rank (as the years chart shows it) + readers' opinions
    rk = yt_rank_map(F) if F and 'yt_rank_map' in globals() else {}; r = rk.get(y)
    no = 0
    if opn is not None:
        hm = opn.select_one('.opn-h'); mo = _hbre.search(r'(\d[\d,]*) opinions?', hm.get_text(' ', strip=True)) if hm is not None and not hm.has_attr('hidden') else None
        no = int(mo.group(1).replace(',', '')) if mo else 0
    if opn is not None or r:
        nv, _ = _hb_yt(fid)
        yb = ''
        if r:
            yb = (f'<div class="cpl-b mhb-af"><p class="mhb-lab">On YouTube</p><p class="mhb-cap">Owners on YouTube rank the {y} #{r} of the {len(rk)} {E_(short)} years we could rank (#1 = best-liked).</p>'
                  + (f'<div class="mhb-bt"><a href="/cars/{fid}/#youtube">What owners say about every year</a></div>' if nv else '') + '</div>')
        sub = ' · '.join(z for z in ((f'YouTube rank #{r} of {len(rk)}' if r else ''), (f'{no} reader opinion{"" if no == 1 else "s"}' if no else '')) if z) or 'Share your take'
        cards.append(_hb_item('mhb-owners', _hb_card('What owners say', sub, _HY_IMG('talk'), h2=True, icon=True), yb + (f'<div class="cpl-b">{opn}</div>' if opn is not None else '')))
    # compare: Similar cars (same year) + the side-by-side tool
    ch = f'/compare/?c={fid}-{y}'
    if sim is not None:
        names = []
        for a in sim.select('.n2-sim-l a'):
            t = a.find(string=True, recursive=False); t = _hbre.sub(r'^\d{4}\s+', '', (t or '').strip())
            if t and t not in names: names.append(t)
        names = names[:2] if sum(len(z) for z in names[:2]) <= 34 else names[:1]
        kb = _hy_box(sim)
        sb = sim.select_one(':scope > .cpl > details > summary h2')
        lab = f'<p class="mhb-lab">{E_(sb.get_text(" ", strip=True))}</p>' if sb is not None else ''
        if kb[0] == 'box': kb[1].insert(0, _HBS(lab, 'html.parser'))
        body = (str(kb[1]) if kb[0] == 'box' else '') + f'<div class="cpl-b"><div class="mhb-bt"><a href="{E_(ch)}">Compare side by side</a></div></div>'
        cards.append(_hb_item('similar', _hb_card('Compare', ('vs ' + ', '.join(E_(z) for z in names)) if names else 'Side by side with any car', _HY_IMG('scale'), icon=True), body))
    else:
        cards.append(f'<div class="mhb-i">{_hb_card("Compare", "Side by side with any car", _HY_IMG("scale"), href=ch, icon=True)}</div>')
    # small buttons: the money links (budget, insurers) and the Questions / Data & sources panels
    lk = [(sid, h, _HY_IC2(ic), lab) for sid, h, ic, lab in money]   # no price box: the money links are small buttons
    qh = (_hy_unwrap(qa) if qa is not None else '') + (_hy_unwrap(ask, True) if ask is not None else '')
    dh = (_hy_unwrap(info) if info is not None else '') + (f'<section class="cpl-sec">{mil_pan}</section>' if mil_pan else '') + fos_left
    pans = [p for p in (('hx-qa', 'question', 'Questions', qh), ('hx-data', 'data', 'Data &amp; sources', dh)) if p[3]]
    btns, panels = _hy_small(lk, pans)
    hub = _hy_hub(f'Everything about the {y} {E_(nm)}', cards, btns, panels, f'More about the {y} {nm}')
    hub = hub.replace('<section class="mhb"', '<section class="mhb mhb-acc"', 1)   # 11-27 (Elijah): one card or panel open at a time (assets/hub.js)
    ov.insert(0, _HBS(hub + _hy_left(g1, g2, g4), 'html.parser'))
    return doc[:i] + str(s) + rest, ''

def _hy_model(path, doc, fid):
    """(B) a model page without the end-of-page action group: (new doc, '') or (doc, why not)"""
    if '/assets/perf.css' in doc: return doc, 'performance page'
    i = doc.find('<div class="tbx">'); j = _hb_end(doc, i, 'div') if i >= 0 else -1
    if j < 0: return doc, 'no tab box'
    s = _HBS(doc[i:j], 'html.parser')
    ov = s.select_one('#p-overview'); g1 = s.select_one('.cpl-g1'); g2 = s.select_one('.cpl-g2'); g4 = s.select_one('.cpl-g4')
    if ov is None or g1 is None or s.select_one('#p-years') is None: return doc, 'no years list'
    rep = cod = None
    for z in g1.select(':scope > div.cpl-one'):
        t = z.get_text(' ', strip=True)[:60]
        if t.startswith('What owners paid for repairs'): rep = z
        elif t.startswith('Engine codes owners report most'): cod = z
    est = _hb_est(fid) if rep is None else None
    if s.select_one('#p-problems') is None and rep is None and est is None: return doc, 'no problems or repair costs'
    if rep is not None: rep.extract()
    if cod is not None: cod.extract()
    T = lambda sel: _hy_take(s, sel)
    bud, ins, prob, rec, qa, yrs, info = T('#p-budget'), T('#p-ins'), T('#p-problems'), T('#p-recalls'), T('#p-questions'), T('#p-years'), T('#info')
    yt = T('#youtube') or T('#yt-owners'); spec = T('#p-specs'); hde = T('#hdeng'); eng = _hy_eng(s)
    ytyrs = xcno = None
    if g2 is not None:
        ytyrs = g2.select_one(':scope > section#yt-years'); xcno = g2.select_one(':scope > section.xc-no')
        for z in (ytyrs, xcno):
            if z is not None: z.extract()
    short = _hb_short(doc, fid); name = _hb_name(doc, fid, short)
    cm = _hbre.search(r'<p class="ph-e n2-cr">(.*?)</p>', doc, _hbre.S)
    if not cm or len([z for z in _hbre.sub(r'<[^>]+>', '', cm.group(1)).split('›') if z.strip()]) < 3:   # complaint-only pages: no model crumb, the name is the H1's
        h1 = _hbre.search(r'<h1[^>]*>(.*?)</h1>', doc, _hbre.S)
        hn = _hbh.unescape(_hbre.split(r'\s+(?:reliability|problems)\b|:', _hbre.sub(r'<[^>]+>', ' ', h1.group(1)).strip())[0]).strip() if h1 else ''
        if hn: short = name = ' '.join(hn.split())
    if _hbre.fullmatch(r'[\d\s-]+|.{1,3}', short): short = name
    rest = doc[j:]
    g3h, a3, b3 = _hy_outside(rest, 'cpl-g3'); opn = ral = None
    if g3h:
        g3 = _HBS(g3h, 'html.parser'); opn = g3.select_one('#opinions'); ral = g3.select_one('#recall-alerts')
        for z in (opn, ral):
            if z is not None: z.extract()
        rest = rest[:a3] + _hy_left(g3.select_one('div.cpl-grp')) + rest[b3:]
    cmp = None
    rlh, a4, b4 = _hy_outside(rest, 'cpl-rel')
    if rlh:
        rl = _HBS(rlh, 'html.parser'); cmp = rl.select_one('#p-compare')
        if cmp is not None: cmp.extract(); rest = rest[:a4] + _hy_left(rl.select_one('div.cpl-grp')) + rest[b4:]
    cards = [_hy_checklist(fid)]
    # every year: the years list (+ the YouTube rank chart and the "no score yet" note on complaint-only models)
    best = yrs.select_one('.bw3c .bw3r.good b') or yrs.select_one('.bw2 .bwt h2'); worst = [c for c in yrs.select('.bw3c') if 'Most' in c.get_text(' ', strip=True)[:20]]
    worst = worst[0].select_one('.bw3r b') if worst else None
    ny = len(set(_hbre.findall(r'<td[^>]*>(?:<a [^>]*>)?((?:19|20)\d\d)(?:</a>)?</td>', str(yrs)))) or len(set(_hbre.findall(rf'href="/cars/{_hbre.escape(fid)}/(\d{{4}})/"', doc)))
    sub = ' · '.join(z for z in ((f'Fewest complaints {best.get_text(strip=True).rstrip(".")}' if best else ''), (f'most {worst.get_text(strip=True)}' if worst else '')) if z) or (f'All {ny} model years' if ny else 'Every model year')
    yb = ''.join(f'<div class="cpl-b">{z}</div>' for z in (xcno, ytyrs) if z is not None) + _hy_years_clean(yrs)
    cards.append(_hb_item('mhb-years', _hb_card('Which years to buy' if best else 'Every model year', sub, _HY_IMG('chart'), icon=True), yb))
    # can you afford it? only with AI prices; without them budget + insurers become small buttons
    pr = _hb_price_rows(fid)
    if pr:
        lo = min(r[2] for r in pr); hi = max(r[3] for r in pr); hy = {int(z) for z in _hbre.findall(rf'href="/cars/{_hbre.escape(fid)}/(\d{{4}})/"', doc)}
        def prow(r):
            y, mi, a, b = r; tag = 'a' if y in hy else 'div'; hr = f' href="/cars/{fid}/{y}/#price-guide"' if y in hy else ''
            return f'<{tag} class="mhb-pr"{hr}><b>{y}</b><span>about {round(mi / 1000):,}K miles</span><em>${a:,}–{b:,}</em></{tag}>'
        top, more_ = pr[:8], pr[8:]
        more = (f'<details class="mhb-more"><summary>Older years ({len(more_)})</summary><div class="mhb-prs">{"".join(prow(r) for r in more_)}</div></details>' if more_ else '')
        af = (f'<div class="cpl-b mhb-af"><p class="mhb-lab">What a used {E_(short)} sells for</p><p class="mhb-cap">Private seller, at each year&#39;s typical miles.</p>'
              f'<div class="mhb-prs">{"".join(prow(r) for r in top)}</div>{more}'
              f'<p class="mhb-cap">Lemon Index estimates (AI, {E_(PRICEBOX._data().get("date", ""))}), not listings or an appraisal. Dealers usually ask more.</p>'
              f'<div class="mhb-bt"><a{" id=" + chr(34) + "p-budget" + chr(34) if bud is not None else ""} href="{E_(PRICEBOX.budget_href(fid, None))}">Find a car for your budget</a>'
              f'<a{" id=" + chr(34) + "p-ins" + chr(34) if ins is not None else ""} href="/insurance/">Compare insurers</a><a href="/car-loan-rates/">Car loan rates</a></div></div>')
        cards.append(_hb_item('mhb-afford', _hb_card('Can you afford it?', f'Used: ${lo:,} to ${hi:,}', _HY_IMG('wallet'), icon=True), af))
    # problems & repairs: the complaints box, owner repair bills or the AI estimates, the engine codes owners name
    pb = ''
    kb = _hy_box(prob)
    if kb[0] == 'box': pb += _hb_inner(kb[1])
    rb = rep.select_one('.cpl-b') if rep is not None else None
    if rb is not None: pb += f'<p class="mhb-lab">What owners paid for repairs</p>{_hb_inner(rb)}'
    elif est:
        gid, shown = est; uid = 'hub' + _hbre.sub(r'[^a-z0-9]', '', gid)
        pb += (f'{REST.CSS}<p class="mhb-lab">What repairs should cost</p><p class="mhb-cap">Estimates for the {E_(REST.gen_label(gid))} {E_(short)}, one repair at an independent shop.</p>'
               + REST.rate_input(uid) + '<ul class="rst-list">' + ''.join(h for z in shown[:8] for h in REST._rows(gid, z)) + '</ul>' + REST.legend(uid) + REST.JS)
    cb = cod.select_one('.cpl-b') if cod is not None else None
    if cb is not None: pb += f'<p class="mhb-lab">Check-engine codes owners report most</p>{_hb_inner(cb)}'
    top_r = rb.select_one('.n3-c b') if rb is not None else None
    tr = _hbre.sub(r'\s*\(.*?\)', '', top_r.get_text(strip=True).replace(' replacement', '').replace(' repair', '')) if top_r else ''
    tp = prob.select_one('#problems td, #problems .pt span') if prob is not None else None
    sub = (f'Top repair: {E_(tr)}' if tr else (f'Most complaints: {E_(tp.get_text(strip=True))}' if tp is not None else ('Repair cost estimates' if est else 'What owners report')))
    cards.append(_hb_item('p-problems', _hb_card('Problems &amp; repairs', sub, _HY_IMG('wrench'), icon=True), f'<div class="cpl-b mhb-pb{" rst" if est and rb is None else ""}">{pb}</div>'))
    # recalls & safety
    if rec is not None:
        nr = rec.select_one('#recalls .yc-n'); nr = nr.get_text(strip=True) if nr is not None else ''
        cards.append(_hy_card(rec, 'p-recalls', 'Recalls &amp; safety', (f'{nr} recall{"" if nr == "1" else "s"}' if nr.isdigit() else 'Every recall'), _HY_IMG('bell')))
    # engines & versions: the old box (engines, BMW specs, which diesel) or EPA's list per model year
    ext = f'<div class="cpl-b">{_hy_unwrap(hde, True)}</div>' if hde is not None else ''
    if eng is not None or spec is not None:
        src = eng if eng is not None else spec
        n = len(src.select('.n3-ig .n3-c')) or len(src.select('p.chips a.chip')); im = src.select_one('.n3-ig img'); im = im.get('src') if im is not None else None
        cards.append(_hy_card(src, 'p-specs' if eng is None else 'mhb-engines', 'Engines &amp; versions', f'{n} engine{"s" if n != 1 else ""}' if n else 'Every engine and version', im or _HY_IMG('engine'), h2=True, icon=not im, extra=ext))
    else:
        ep = _hb_epa(fid)
        if ep or ext:
            rows = ''.join(f'<div class="mhb-pr mhb-er"><b>{E_(lab)}</b><span>{E_(fu)}</span><em>{E_(ys)}</em></div>' for lab, fu, ys in ep)
            eb = (f'<div class="cpl-b mhb-af"><p class="mhb-lab">Engines in the {E_(short)}, by model year</p><div class="mhb-prs">{rows}</div>'
                  f'<p class="mhb-cap">Every engine EPA lists for the {E_(short)} (fueleconomy.gov).</p></div>') if ep else ''
            sub = (f'{len(ep)} engines' if len(ep) > 1 else ep[0][0]) if ep else 'Which diesel is in it'
            cards.append(_hb_item('mhb-engines', _hb_card('Engines &amp; versions', E_(sub), _HY_IMG('engine'), h2=True, icon=True), eb + ext))
    # what owners say (YouTube)
    if yt is not None:
        t = yt.get_text(' ', strip=True); mv = _hbre.search(r'([\d,]+) videos', t); fv = yt.select_one('.yot-t.good b')
        nv, fav = _hb_yt(fid)
        nv = nv or (int(mv.group(1).replace(',', '')) if mv else 0); fav = fav or (fv.get_text(strip=True) if fv is not None else None)
        sub = ' · '.join(z for z in ((f'{nv:,} YouTube videos' if nv else 'YouTube owner videos'), (f'favorite year {fav}' if fav else '')) if z)
        cards.append(_hy_card(yt, yt.get('id', 'youtube'), 'What owners say', sub, _HY_IMG('talk'), h2=True))
    # compare
    if cmp is not None:
        riv = []
        for mu in cmp.select('.mu'):
            alts = [im.get('alt', '') for im in mu.select('img.r') if im.get('alt')]
            r = alts[0] if alts else _hbre.sub(r'^vs\s+', '', mu.select_one('b').get_text(strip=True) if mu.select_one('b') else '')
            if r and r not in riv: riv.append(r)
        riv = riv[:2] if sum(len(r) for r in riv[:2]) <= 34 else riv[:1]
        cards.append(_hy_card(cmp, 'p-compare', 'Compare', ('vs ' + ', '.join(E_(r) for r in riv)) if riv else 'Side by side with any car', _HY_IMG('scale')))
    lk = []
    if not pr:
        for sec, sid, ic, lab in ((bud, 'p-budget', 'search', 'Your budget'), (ins, 'p-ins', 'shield', 'Insurance')):
            kb = _hy_box(sec)
            if kb[0] == 'link': lk.append((sid, kb[1], _HY_IC2(ic), lab))
    pans = [('hx-alerts', 'bell', 'Recall alerts', str(ral) if ral is not None else ''), ('hx-opinion', 'opinion', 'Your opinion', str(opn) if opn is not None else ''),
            ('hx-qa', 'question', 'Questions', _hy_unwrap(qa)), ('hx-data', 'data', 'Data &amp; sources', _hy_unwrap(info))]
    pans = [p for p in pans if p[3]]
    btns, panels = _hy_small(lk, pans)
    hub = _hy_hub(f'Everything about the {E_(short)}', cards, btns, panels, f'More about the {name}')
    ov.insert(0, _HBS(hub + _hy_left(g1, g2, g4), 'html.parser'))
    return doc[:i] + str(s) + rest, ''

def HUB_HOOK(path, doc):
    if not HUB_ON or '<div class="tbx">' not in doc: return doc
    m = _HY_YEAR.fullmatch(path)
    if m:
        try: out, why = _hy_year(path, doc, m.group(1), int(m.group(2)))
        except Exception as ex: out, why = doc, f'error {type(ex).__name__}: {ex}'
        if why: HUB_OLD[path] = why
        else: HUB_COUNT['year'] += 1
        return out
    m = _HB_PATH.fullmatch(path)
    if not m: return doc
    if 'mh-acts' in doc: return _hb_model_full(path, doc)
    try: out, why = _hy_model(path, doc, m.group(1))
    except Exception as ex: out, why = doc, f'error {type(ex).__name__}: {ex}'
    if why: HUB_OLD[path] = why
    else: HUB_COUNT['model'] += 1; HUB_SEEN[m.group(1)] = True
    return out
