# 11-24 visual fixes on car and bike pages (Elijah, Ford Ranger + BMW S1000RR screenshots). exec'd by build.py with the other hooks;
# VF_HOOK(path, doc) runs at the end of page(), after the date hash, so none of this moves a page's date:
#   1. Normal / Advanced: the switch is gone everywhere ("Normal is going to be better looking"). The /advanced/ pages still build for old
#      links, but every one is noindex and none is in the sitemap (advanced_pages.py adds no URLs) and no page links to them.
#   2. "Owners praise" / "Owners complain about" (model pages' YouTube block, performance pages): when one side is "Nothing stands out.",
#      the other side runs full width and the empty side becomes one quiet line under it (.yot-pc1 / .pf-pc1).
#   3. "Engines in this car": each chip shows that engine's picture (the illustration its engine page and /engines/ use), home-card style.
#      The pictures existed all along; the chip row (engine_uses.py EU_ROW, 11-13) was built as text before most of them were made.
#   4. Save + Share: the hero Share buttons (model page's top-right icon, the year page's Share in the action row and phone More menu) are
#      removed here; their share text rides on the <h1> (data-lsv-share) and assets/saved.js draws one heart + share pair next to the name.
import json as _vfj, os as _vfos, re as _vfre

_VF_NOI = '<meta name="robots" content="noindex,follow">'
_VF_VEH = _vfre.compile(r'^/(?:cars|motorcycles|supercars|electric|jdm|planes)/')

# ---- 1. Normal / Advanced
_VF_MROW = _vfre.compile(r'<div class="tb-mrow">\s*(<nav[^>]*\bmodes\b[^>]*>.*?</nav>)?\s*</div>', _vfre.S)
_VF_MODES = _vfre.compile(r'<nav(?=[^>]*class="[^"]*\bmodes\b)[^>]*>.*?</nav>', _vfre.S)
_VF_TBMODE = _vfre.compile(r'<a\b(?=[^>]*class="[^"]*\btb-mode\b)[^>]*>.*?</a>', _vfre.S)
_VF_FAQADV = _vfre.compile(r',? and the full table is on the <a href=(\\?)"[^"\\]*/advanced/\1">advanced page</a>')

# ---- 2. one-sided praise / complaints
_VF_PCRX = {}
def _vf_pc(doc, p):
    if p not in _VF_PCRX:
        none = _vfre.escape(f'<p class="{p}-none">Nothing stands out.</p>')
        bars = r'((?:<div class="' + p + r'-b[^"]*">(?:(?!</div>).)*</div>)*)'
        _VF_PCRX[p] = _vfre.compile(f'<div class="{p}-pc"><div><h3>Owners praise</h3>(?:{none}|{bars})</div><div><h3>Owners complain about</h3>(?:{none}|{bars})</div></div>', _vfre.S)
    def rep(m):
        pr, co = m.group(1), m.group(2)
        if pr is not None and co is not None: return m.group(0)
        if pr is None and co is None: return f'<p class="{p}-n1">Owners don&#39;t single out anything to praise or complain about.</p>'
        h, bs, note = ('Owners praise', pr, 'No complaint stands out.') if co is None else ('Owners complain about', co, 'No praise stands out.')
        return f'<div class="{p}-pc {p}-pc1"><div><h3>{h}</h3>{bs}<p class="{p}-n1">{note}</p></div></div>'
    return _VF_PCRX[p].sub(rep, doc)

# ---- 3. engine pictures: engine page address -> {src, w, h}, from the same files the engine pages and /engines/ use
_VF_EIMG = None
def _vf_json(p):
    try: return _vfj.load(open(p, encoding='utf-8'))
    except (OSError, ValueError): return {}
def _vf_thumb(ph):
    if not ph or not ph.get('src'): return None
    th = ph['src'][:-5] + '-640.webp'
    if ph['src'].endswith('.webp') and _vfos.path.exists(th.lstrip('/')): return (th, 640, round(ph['h'] * 640 / ph['w']))
    return (ph['src'], ph.get('w') or 640, ph.get('h') or 480)
def _vf_eimgs():
    global _VF_EIMG
    if _VF_EIMG is not None: return _VF_EIMG
    m = {}
    for slug, ph in _vf_json('data/ai_engine_photos.json').items(): m[f'/engines/{slug}/'] = ph   # 11-13 AI engine illustrations (everyday engines)
    slugs = globals().get('_EU_SLUG') or {'rr-n73': 'rolls-royce-n73', 'rr-n74': 'rolls-royce-n74'}
    for e, ph in _vf_json('data/supercar_engine_photos.json').items(): m[f'/engines/{slugs.get(e, e)}/'] = ph   # supercar + performance engines
    cut = {'S58': {'src': '/assets/engines/bmw-s58-twin-turbo-inline-6-engine.webp', 'w': 1200, 'h': 850},
           'S55': {'src': '/assets/engines/bmw-s55-twin-turbo-inline-6-engine.webp', 'w': 1200, 'h': 1056}}   # = all_engines.py _AE_CUT
    for code, ph in _vf_json('data/bmw_engine_photos.json').items(): m[f'/engines/bmw-{code.lower()}/'] = cut.get(code) or ph
    import glob as _g
    for p in _g.glob('data/engines_*.json'):   # the Civic's own engine list: chips open its model page's Engines view
        fid = _vfos.path.basename(p)[8:-5]
        for d in _vf_json(p) or []:
            if isinstance(d, dict) and d.get('img'): m[f'/cars/{fid}/#eng-{d["id"]}'] = d['img']
    _VF_EIMG = {u: t for u, t in ((u, _vf_thumb(ph)) for u, ph in m.items()) if t}
    ce = globals().get('CAR_ENG') or {}
    used = {u for es in ce.values() for u in es}
    miss = sorted(u for u in used if u not in _VF_EIMG)
    print(f'vis_fixes: "Engines in this car" chips: {len(used)} engines with a page, {len(miss)} without a picture', miss[:12])
    return _VF_EIMG
_VF_ROW = _vfre.compile(r'<nav(?=[^>]*aria-label="Engines in this car")([^>]*)>(.*?)</nav>', _vfre.S)
_VF_CHIP = _vfre.compile(r'<(a|span) class="n3-c( n3-more)?"( href="[^"]*")?><b>(.*?)</b>(?:<small>(.*?)</small>)?</\1>', _vfre.S)
_VF_EIC = '<span class="n3-p n3-p0" aria-hidden="true"><svg width="28" height="28" focusable="false"><use href="/assets/ic.svg?v=1#engine"></use></svg></span>'
def _vf_chip(m):
    tag, more, href, name, small = m.group(1), m.group(2) or '', m.group(3) or '', m.group(4), m.group(5)
    t = f'<span class="n3-t"><b>{name}</b>' + (f'<small>{small}</small>' if small else '') + '</span>'
    if more: return f'<{tag} class="n3-c n3-more"{href}>{t}</{tag}>'
    u = _vfre.search(r'href="([^"]*)"', href).group(1) if href else ''
    im = _vf_eimgs().get(u) if u else None
    pic = (f'<span class="n3-p"><img src="{im[0]}" alt="" width="{im[1]}" height="{im[2]}" loading="lazy" decoding="async"></span>' if im else _VF_EIC)
    return f'<{tag} class="n3-c"{href}>{t}{pic}</{tag}>'
def _vf_engines(doc):
    def row(m):
        at = m.group(1)
        at = _vfre.sub(r'class="([^"]*)"', lambda c: f'class="{c.group(1)} n3-ig"', at, count=1) if 'class="' in at else at + ' class="n3-ig"'
        return f'<nav{at}>' + _VF_CHIP.sub(_vf_chip, m.group(2)) + '</nav>'
    return _VF_ROW.sub(row, doc)

# ---- 4. hero Share buttons -> the heart + share pair by the name (assets/saved.js)
_VF_SHARES = [
    _vfre.compile(r'<button(?=[^>]*class="mh-share")[^>]*>.*?</button>', _vfre.S),   # model pages: the top-right icon (model_hero.py)
    _vfre.compile(r'<button(?=[^>]*class="tb-ic yshare")[^>]*>.*?</button>', _vfre.S),   # year pages: action row + phone More menu (tabbed.py)
    _vfre.compile(r'<button(?=[^>]*class="tb-ic")(?=[^>]*data-share=)[^>]*>.*?</button>', _vfre.S),   # model pages: phone tab row chip (ycarousel.py)
    _vfre.compile(r'<button(?=[^>]*class="btn btn-ghost")(?=[^>]*data-share=)[^>]*>Share ↗</button>', _vfre.S),   # model pages: the hidden wide-screen copy
]
_VF_YCN1 = _vfre.compile(r'<div class="ycn">\s*</div>')
_VF_YCNM = _vfre.compile(r'<div class="ycn"><button[^>]*class="ycn-b"[^>]*>.*?</button><div class="ycn-s"[^>]*>(.*?)</div></div>', _vfre.S)
def _vf_hero(doc):
    """(start, end) of the page's hero: <main> to the end of the first top-level <section> in it (heroes hold nested sections)"""
    i = doc.find('<main>')
    if i < 0: return None
    k = doc.find('<section', i)
    if k < 0: return None
    d = 0
    for m in _vfre.finditer(r'<section\b|</section>', doc[k:]):
        d += 1 if m.group(0) != '</section>' else -1
        if d == 0: return i, k + m.end()
    return None
def _vf_share(path, doc):
    hr = _vf_hero(doc)
    if not hr or '<h1' not in doc[hr[0]:hr[1]]: return doc
    a, b = hr; hero = doc[a:b]; txt = None
    for rx in _VF_SHARES:
        for m in rx.finditer(hero):
            t = _vfre.search(r'data-share="([^"]*)"', m.group(0))
            if t and txt is None: txt = t.group(1)
        hero = rx.sub('', hero)
    # the phone More menu: All years + Compare are already on the page (n2 row), so a menu left with only those goes
    hero = _VF_YCNM.sub(lambda m: '' if not _vfre.search(r'<(?:a|button)\b', _vfre.sub(r'<a[^>]*aria-label="(?:All years|Compare[^"]*)"[^>]*>.*?</a>', '', m.group(1), flags=_vfre.S)) else m.group(0), hero)
    hero = _VF_YCN1.sub('', hero)
    if txt: hero = hero.replace('<h1', f'<h1 data-lsv-share="{txt}"', 1)
    return doc[:a] + hero + doc[b:]

def VF_HOOK(path, doc):
    if path.endswith('/advanced/') and 'name="robots"' not in doc[:6000]:   # 1. old links still work, search engines skip them
        doc = doc.replace('<link rel="canonical"', _VF_NOI + '<link rel="canonical"', 1)
    if 'modes' in doc or 'tb-mode' in doc:
        doc = _VF_MROW.sub('', doc); doc = _VF_MODES.sub('', doc); doc = _VF_TBMODE.sub('', doc)
    if 'advanced page</a>' in doc: doc = _VF_FAQADV.sub('', doc)
    if 'Nothing stands out.' in doc: doc = _vf_pc(_vf_pc(doc, 'yot'), 'pf')
    if 'aria-label="Engines in this car"' in doc: doc = _vf_engines(doc)
    if _VF_VEH.match(path): doc = _vf_share(path, doc)
    return doc
