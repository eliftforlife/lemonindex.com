# 11-19 (Elijah: "category cards open their own page, not a jump down /cars/"): every kind-of-car chip on /cars/ (the text tabs) and on the
# home page (the big photo cards) opens its own clean page: a big title, a search box (searches the whole site, this kind first; lookup.js
# #ckq), one grey line saying where the data comes from, then the cars by brand. Cards show the model name only; JDM cards add whose car
# it was in the film (plain text from data/perf/<slug>.json `films`, no stills, logos or likenesses; left off when the data names two people
# for the same film). New pages: /trucks/, /suvs/, /sedans/, /minivans/, /performance/ (the first four were redirect stubs to /?type=).
# Existing hubs keep their address, title, description and schema: /jdm/, /supercars/, /electric/, /motorcycles/ get the same top (CAT_HOOK,
# in page() after the date hash, so their dates don't move) and their old sections fold into boxes under the grid.
# Exec'd from build.py right after the home page (needs `lst`, the home grid's brand blocks).
import json as _ckj
from bs4 import BeautifulSoup as _CKS
# key (the /?type= tab), path, H1, grid tag, the grey source line, <title>, the plural for the description
CAT = [('trucks', '/trucks/', 'Trucks', 'tk', 'Owner complaints and recalls from NHTSA.', 'Truck Reliability by Model: Problems and Recalls', 'pickup trucks'),
       ('suvs', '/suvs/', 'SUVs', 'sv', 'Owner complaints and recalls from NHTSA.', 'SUV Reliability by Model: Problems and Recalls', 'SUVs and crossovers'),
       ('cars', '/sedans/', 'Sedans & hatchbacks', 'cr', 'Owner complaints and recalls from NHTSA.', 'Sedan and Hatchback Reliability by Model: Problems and Recalls', 'sedans, hatchbacks and other cars'),
       ('minivans', '/minivans/', 'Minivans', 'mv', 'Owner complaints and recalls from NHTSA.', 'Minivan Reliability by Model: Problems and Recalls', 'minivans and vans'),
       ('performance', '/performance/', 'Performance', 'p', 'Specs from automakers, owner complaints from NHTSA.', 'Performance Cars: Specs, Engines and Owner Complaints', 'performance cars'),
       ('supercars', '/supercars/', 'Supercars', 's', 'Fuel economy from the EPA, recalls from NHTSA.', None, None),
       ('electric', '/electric/', 'Electric', 'e', 'Owner complaints from NHTSA, range and running costs from the EPA.', None, None),
       ('jdm', '/jdm/', 'JDM', 'j', 'Specs from automakers, complaints from NHTSA.', None, None),
       ('motorcycles', '/motorcycles/', 'Motorcycles', None, 'Owner complaints and recalls from NHTSA.', None, None)]
CAT_BY = {c[1]: c for c in CAT}
CAT_URLS = []
_CK_BODY = ('tk', 'sv', 'cr', 'mv')   # body types skip the Electric-tab twins and "No data yet" cards (as the home tabs do, ctabs.js)
_CK_2W = ('MV Agusta', 'Moto Guzzi', 'Royal Enfield')

def _ck_owner(u):
    """'Dominic Toretto's' for a Fast & Furious car: the first film's driver, when the data names one person for that film"""
    f = f'data/perf/{u.strip("/").split("/")[-1].split("#")[0]}.json'
    try: fl = _ckj.load(open(f, encoding='utf-8')).get('films') or []
    except Exception: return ''
    if not fl: return ''
    w = [x.get('who') or '' for x in fl if x.get('film') == fl[0].get('film')]
    if len(set(w)) != 1 or not w[0] or any(k in w[0].lower() for k in ('crew', 'cars', 'reused', 'various')): return ''
    return w[0] + ("'" if w[0].endswith('s') else "'s")

def _ck_card(a, jdm=False, brand=''):
    """one card: the picture and the model name (JDM: whose car it was, then the name)"""
    p = a.find(class_='mc-p'); b = a.find('b')
    own = _ck_owner(a['href']) if jdm else ''
    nm = b.get_text(' ', strip=True) if b else ''
    if brand and re.fullmatch(r'[\d.]{1,3}', nm): nm = f'{brand} {nm}'   # "Polestar 2", not "2"
    if nm[:1].islower(): nm = nm[:1].upper() + nm[1:]   # 11-19: Ram 'pickup' -> 'Pickup'
    return (f'<a class="mc ck-c" href="{E(a["href"])}">{str(p) if p is not None else ""}'
            + (f'<small class="ck-o">{E(own)}</small>' if own else '') + f'<b>{E(nm)}</b></a>')

def _ck_grid(blocks, jdm=False):
    """[(brand, [<a> cards])] -> the brand blocks (the home grid's .mbs/.mb/.mg look)"""
    out = ''.join(f'<div class="mb"><h2 class="ck-b">{E(b)}</h2><div class="mg">' + ''.join(_ck_card(a, jdm, b) for a in cs) + '</div></div>' for b, cs in blocks if cs)
    return f'<div class="mbs">{out}</div>'

def _ck_from_lst(tag):
    s = _CKS(lst, 'html.parser'); seen = set(); blocks = []
    for mb in s.find_all('div', class_='mb'):
        h = mb.find('h3'); cs = []
        for a in mb.find_all('a', class_='mc'):
            k = a.get('class') or []; t = (a.get('data-t') or '').split()
            if tag not in t or not a.get('href') or a['href'] in seen: continue
            if tag in _CK_BODY and ('mc-dup' in k or 'mc-nd' in k): continue
            seen.add(a['href']); cs.append(a)
        if cs: blocks.append((h.get_text(' ', strip=True) if h else '', cs))
    return blocks

def _ck_bikes(cards):
    """motorcycles: the hub's own cards, regrouped by brand (the name loses its brand, which is the heading)"""
    by = {}
    for a in cards:
        n = a.find('b').get_text(' ', strip=True) if a.find('b') else ''
        br = next((w for w in _CK_2W if n.startswith(w + ' ')), n.split(' ')[0])
        if a.find('b') is not None and n.startswith(br + ' '): a.find('b').string = n[len(br) + 1:]
        by.setdefault(br, []).append(a)
    return [(b, by[b]) for b in sorted(by, key=str.lower)]

def _ck_top(c, n):
    k, path, h1, tag, src = c[:5]
    what = {'cars': 'sedans', 'minivans': 'minivans', 'electric': 'electric cars', 'jdm': 'JDM cars', 'motorcycles': 'motorcycles'}.get(k, h1.lower() if k != 'suvs' else 'SUVs')
    return (f'<section class="ck-h"><h1>{E(h1)}</h1>'
            f'<form class="lxs-f ck-s" role="search" action="/" method="get"><input id="ckq" name="q" type="search" autocomplete="off" '
            f'placeholder="Search {E(what)} or any car" aria-label="Search every car, {E(what)} first" enterkeyhint="search" data-pref="grid">'
            f'<div id="ckqs" class="fsug" role="listbox" hidden></div></form><p class="ck-src">{E(src)}</p></section>')

_CK_CR = '<p class="ph-cr ck-cr">Pictures: AI-generated illustrations by The Lemon Index, free under CC BY 4.0 (<a href="/images/">download</a>).</p>'

def _ck_new(c):
    k, path, h1, tag, src, title, plural = c
    blocks = _ck_from_lst(tag); n = sum(len(cs) for _, cs in blocks)
    if not n: return
    names = [f'{b} {a.find("b").get_text(" ", strip=True)}' for b, cs in blocks for a in cs if a.find('b')]
    rel = [(f'/best/most-reliable-{k}/', f'The most reliable {h1 if k == "suvs" else h1.lower()}, ranked')] if k in ('trucks', 'suvs', 'minivans') else []
    rel += ([('/best/cheapest-500-hp-cars/', 'The cheapest 500 hp cars')] if k == 'performance' else []) + [('/rankings/', 'Every car ranked'), ('/compare/', 'Compare up to 4 cars'), ('/', 'Every car, A to Z')]
    relb = ('<div class="cpl-grp cpl-rel cpl-ins"><div class="cpl">' + PILL('/assets/icons/signpost.webp', 'Related pages', '', '<ul class="ck-rl">'
            + ''.join(f'<li><a href="{u}">{E(t)}</a></li>' for u, t in rel) + '</ul>') + '</div></div>')
    feat = (f'<style>.ck-feat a,.ck-feat a b{{text-decoration:none}}</style><div class="cpl ck-feat" style="max-width:420px;margin:22px auto 0">{V5_GO("tag", "The cheapest 500 hp cars", "/best/cheapest-500-hp-cars/")}</div>' if k == 'performance' else '')   # 11-25 (Elijah)
    body = f'<div class="pg ckp">{_ck_top(c, n)}{feat}<section class="ckg" aria-label="{E(h1)} by brand">{_ck_grid(blocks)}</section>{relb}{_CK_CR}</div>'
    desc = (f'{n} {plural}, from the {names[0]} to the {names[-1]}, by brand: owner complaints, the problem years and recalls from NHTSA. Free.' if k != 'performance'
            else f'{n} performance cars, from the {names[0]} to the {names[-1]}, by brand: specs from the automakers, the engine and owner complaints from NHTSA. Free.')
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": h1, "url": BASE + path,
           "hasPart": [{"@type": "WebPage", "name": f'{b} {a.find("b").get_text(" ", strip=True)}', "url": BASE + a['href'].split('#')[0]} for b, cs in blocks for a in cs if a.get('href', '').startswith('/')][:200]}]
    page(path, f'{title} | The Lemon Index', desc, body, ld=ld)
    CAT_URLS.append(path)

for _c in CAT:
    if _c[5]:
        try: _ck_new(_c)
        except Exception as _ex:
            import traceback; print('category page failed', _c[1], repr(_ex)); traceback.print_exc()

def _ck_title(h):
    """an h2 like 'Every model. <span>Tap one...</span>' -> 'Every model'"""
    t = h.find(string=True, recursive=False) or h.get_text(' ', strip=True)
    return re.sub(r'\.\s*$', '', str(t).strip())

_CK_IC = [(('furious', 'film'), 'film'), (('legend', 'every model', 'cars:'), 'car'), (('engine',), 'engine'), (('question',), 'question'), (('recall',), 'bell'),
          (('complaint', 'problem'), 'warning'), (('sold in the us',), 'tag'), (('fuel', 'cost'), 'tag'), (('more ',), 'signpost')]
def _ck_icon(t):
    tl = t.lower()
    return _CP_I(next((ic for ks, ic in _CK_IC if any(k in tl for k in ks)), 'chart'))

def CAT_HOOK(path, body):
    c = CAT_BY.get(path)
    if c is None or 'ck-h' in body: return body
    try: return _ck_hook(c, body)
    except Exception as ex:
        import traceback; globals().setdefault('TAB_FAIL', []).append(f'cat_pages {path}: {type(ex).__name__} {ex} ' + traceback.format_exc()[-600:]); return body

def _ck_hook(c, body):
    k, path, h1, tag = c[:4]
    s = _CKS(body, 'html.parser'); root = s.find('div', class_='pg')
    if root is None: return body
    art = root.find('article', class_='study', recursive=False)
    if art is not None: art.unwrap()   # /electric/: the article's parts are the sections
    hero = root.find('section', class_='ph', recursive=False)
    # the grid
    if tag:
        blocks = _ck_from_lst(tag); have = {a['href'] for _, cs in blocks for a in cs}
    else: blocks, have = [], set()
    for sec in root.find_all('section', recursive=False):
        h = sec.find('h2', recursive=False)
        if h is None or not _ck_title(h).startswith('Every model'): continue
        cs = sec.find_all('a', class_='mc')
        if k == 'motorcycles': blocks = _ck_bikes(cs); have = {a['href'] for a in cs}
        grid = _ck_grid(blocks, k == 'jdm') if blocks else ''
        if all(a.get('href') in have for a in cs): sec.decompose()   # the new grid holds every one of its cars
    if not blocks: return body
    if k != 'motorcycles': grid = _ck_grid(blocks, k == 'jdm')
    for x in root.find_all(['p', 'nav'], class_=['ctn', 'jdm-j'], recursive=False): x.decompose()   # "See them with every other car", the "legends ↓" jump
    top = _CKS(_ck_top(c, 0) + f'<section class="ckg" aria-label="{E(h1)} by brand">{grid}</section>', 'html.parser')
    # the old page under the grid, as boxes: the old hero's line first (under its old headline), then one box per section with an h2
    boxes, cur = [], None
    if hero is not None:
        oh = hero.find('h1'); keep = [p.extract() for p in hero.find_all('p', class_='ph-s')]
        cur = (_ck_title(oh) if oh else h1, keep); boxes.append(cur)
        hero.decompose()
    shl = []
    for e in list(root.children):
        if not getattr(e, 'name', None): continue
        if e.name in ('style', 'script') or e.get('class') == ['shline']:
            if e.get('class') == ['shline']: shl.append(e.extract())
            continue
        h = e.find('h2', recursive=False) if e.name in ('section', 'div') else (e if e.name == 'h2' else None)
        if h is not None and (e.name != 'section' or 'tiles' not in (e.get('class') or [])):
            t = _ck_title(h); sub = h.find(class_='h2s')
            if e.name == 'h2': e.extract(); cur = (t, []); boxes.append(cur); continue
            if sub is not None: sub.name = 'p'; sub['class'] = ['cpl-dek']; h.insert_after(sub.extract())
            h.decompose(); cur = (t, [e.extract()]); boxes.append(cur)
        else:
            if cur is None: cur = (h1, []); boxes.append(cur)
            cur[1].append(e.extract())
    secs = []
    for i, (t, nodes) in enumerate(boxes):
        if not nodes: continue
        sid = None
        for n in nodes:
            if getattr(n, 'get', None) and n.get('id'): sid = n['id']; del n['id']; break
        secs.append(_cp_box(s, t, '', nodes, sid, _ck_icon(t), h2=True))
    grp = s.new_tag('div'); grp['class'] = ['cpl-grp', 'ck-more', 'cpl-ins']
    for x in secs: grp.append(x)
    root['class'] = (root.get('class') or []) + ['ckp']
    for x in reversed(list(top.contents)): root.insert(0, x.extract())   # (the old page's <style> blocks stay, after it)
    root.append(grp)
    for x in shl: root.append(x)
    root.append(_CKS(_CK_CR, 'html.parser'))
    return str(s)
