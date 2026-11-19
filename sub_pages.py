# 11-19 (Elijah, on the Integra GS-R page): "instead of drop down when you click one of these it goes to its own page like a custom engine
# page for that engine or custom movie page ... we can go car by car, test it on this car".
# SUB_HOOK(path, body) runs in page() right after CAR_HOOK (so after the date hash). For a car listed in SUB_CARS, each main card stops being a
# dropdown and becomes a link row (.cpl-a, same look, right chevron) to a page of its own built from that card's content:
#   films    -> <car>/films/      the car in the films (who drove it, which scene)
#   speed    -> <car>/0-60/       0-60, horsepower, torque, weight, price new
#   engine   -> the engine's own page (/engines/<code>/), which already covers its specs, known issues and owner videos
#   problems -> <car>/problems/   known issues + owner complaints to NHTSA + recalls
#   buy      -> <car>/buying/     should you buy one + what YouTube owners say
# Questions stay on the car page (its FAQ schema lives there). Every subpage ends with the other cards as link rows plus the main page.
# Add a car = one SUB_CARS entry (titles and one-line answers written from that car's own data).
from bs4 import BeautifulSoup as _SBS

SUB_URLS = []
SUB_CARS = {
    '/jdm/acura-integra-gs-r/': {
        'name': 'Integra GS-R', 'crumb': '<a href="/jdm/">JDM</a> · <a href="/jdm/acura-integra-gs-r/">Acura Integra GS-R</a>',
        'pages': [
            ('films', r'^In the films', 'films', 'In the films', 'film',
             'Acura Integra in Fast and Furious: Edwin and Mia&#39;s Cars',
             'The Integra in The Fast and the Furious',
             'Two Integras are in the 2001 film: Edwin&#39;s 1996 GS-R in the opening street race, and Mia Toretto&#39;s blue 1994 Integra.',
             'Which Integras are in The Fast and the Furious (2001): Edwin\'s 1996 GS-R from the opening street race and Mia Toretto\'s blue 1994 Integra, with sources.'),
            ('speed', r'^How fast', '0-60', 'How fast is the Integra?', 'stopwatch',
             'Acura Integra GS-R 0-60, Horsepower and Specs (1994-2001)',
             'How fast is the Acura Integra GS-R?',
             'The GS-R makes 170 hp at 7,600 rpm and ran 0-60 in 6.9 seconds in Car and Driver&#39;s test. The Type R makes 195 hp and ran 6.6.',
             'Acura Integra GS-R (DC2, 1994-2001) 0-60 times, horsepower, torque, weight and price new, next to the Type R. Every number sourced.'),
            ('engine', r'^The engine', None, None, None, None, None, None, None),
            ('problems', r'^(Known issues|Problems & recalls)', 'problems', 'Problems & recalls', 'warning',
             'Acura Integra GS-R Problems and Recalls (1994-2001)',
             'Acura Integra GS-R problems and recalls',
             'Theft is the big one: the 1999 Integra coupe was the most-stolen vehicle in the US for 2004. Below: the known issues, owner complaints to NHTSA and every recall.',
             'Acura Integra GS-R (1994-2001) problems: known issues, owner complaints to NHTSA by year and every recall, with sources.'),
            ('buy', r'^(Should you buy|What owners say)', 'buying', 'Should you buy an Integra?', 'tag',
             'Should You Buy an Acura Integra GS-R? What to Check',
             'Should you buy an Acura Integra GS-R?',
             'What it cost new, which years owners and YouTube rate best, the recalls to check, and what owners say about living with one.',
             'Should you buy a used Acura Integra GS-R (1994-2001)? Price new, best and worst years, recalls to check and what YouTube owners say.'),
        ],
    },
}

_SB_CHEV = ('<svg aria-hidden="true" class="cpl-ar" fill="none" height="18" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" '
            'stroke-width="2.2" viewBox="0 0 24 24" width="18"><path d="m9 6 6 6-6 6"></path></svg>')

def _sb_row(href, label, icon):
    ic = _cp_svg(icon) if icon else ''
    return f'<a class="cpl-a sb-go" href="{href}">{ic}<span><b>{label}</b></span>{_SB_CHEV}</a>'

def _sb_title(d):
    sm = d.find('summary', recursive=False)
    if not sm: return ''
    t = sm.find(['h2', 'b'])   # the card's title only, never its small second line
    return (t or sm).get_text(' ', strip=True)

def _sb_inner(d):
    """a box's content without its summary; the box title becomes an h2 (a subpage merges two boxes)"""
    d = _SBS(str(d), 'html.parser').find('details')
    sm = d.find('summary', recursive=False)
    t = _sb_title(d)
    if sm: sm.decompose()
    return t, d.decode_contents()

def _sb_nav(cfg, here, base):
    rows = []
    for key, rx, slug, label, icon, *_ in cfg['pages']:
        if key == here: continue
        if key == 'engine':
            if cfg.get('_engine'): rows.append(_sb_row(cfg['_engine'][0], cfg['_engine'][1], 'engine'))
            continue
        if slug and slug in cfg.get('_built', ()): rows.append(_sb_row(f'{base}{slug}/', label, icon))
    rows.append(_sb_row(base, f'Back to the {cfg["name"]} page', 'car'))
    return f'<section class="cpl-sec sb-more"><h2 class="sb-h">More on the {cfg["name"]}</h2><div class="cpl">{"".join(rows)}</div></section>'

SB_CSS = ('<style>.sbp .sb-dek{font-size:19px;line-height:1.45;color:#3a3a3c;max-width:640px;margin:10px auto 0;text-align:center}'
          '.sbp .sb-body{max-width:760px;margin:28px auto 0;padding:0}.sbp .sb-body>h2.sb-sh{font-size:24px;margin:34px 0 10px;letter-spacing:-.015em}'
          '.sbp .sb-body>h2.sb-sh:first-child{margin-top:0}.sbp .sb-more{max-width:760px;margin:40px auto 0;padding:0 16px}'
          '.sbp .sb-h{font-size:22px;margin:0 0 12px;letter-spacing:-.015em}.sbp .sb-more .cpl{display:grid;gap:8px}'
          '.sbp .sb-body details.pf-cs{margin-top:10px}.sbp .sb-pic{display:block;width:100%;max-width:520px;height:auto;margin:18px auto 0}'
          '.sbp .sb-body .pf-iss,.sbp .sb-body .pf-recs{padding-left:0;padding-right:0}a.sb-go,a.sb-go:hover{text-decoration:none}</style>')
SB_LINKCSS = '<style>a.sb-go,a.sb-go:hover{text-decoration:none;color:inherit}</style>'

def SUB_HOOK(path, body):
    cfg = SUB_CARS.get(path)
    if not cfg or 'cpl-sec' not in body: return body
    try: return _sub_hook(path, body, cfg)
    except Exception as ex:
        globals().setdefault('TAB_FAIL', []).append(f'sub_pages {path}: {type(ex).__name__} {ex}'); return body

def _sub_hook(path, body, cfg):
    soup = _SBS(body, 'html.parser')
    boxes = [d for d in soup.select('section.cpl-sec > div.cpl > details') if not d.find_parent('div', class_='cpl-b')]
    got = {}   # key -> [(title, html, details)]
    for d in boxes:
        t = _sb_title(d)
        for key, rx, *_ in cfg['pages']:
            if re.match(rx, t): got.setdefault(key, []).append(d); break
    assets = body[:body.find('<div class="advp')] if '<div class="advp' in body else ''
    hi = soup.select_one('section.tb-hero img.pf-car') or soup.select_one('section.tb-hero img')
    pic = ''
    if hi is not None:
        hi = _SBS(str(hi), 'html.parser').find('img'); hi['class'] = ['sb-pic']; hi['fetchpriority'] = 'high'
        pic = str(hi)
    cfg['_built'] = [p[2] for p in cfg['pages'] if p[2] and got.get(p[0])]
    if got.get('engine'):
        a = got['engine'][0].select_one('a[href^="/engines/"]')
        cfg['_engine'] = (a['href'].split('#')[0], _sb_title(got['engine'][0])) if a else None
    # the subpages
    for key, rx, slug, label, icon, title, h1, dek, desc in cfg['pages']:
        if not slug or not got.get(key): continue
        parts = [_sb_inner(d) for d in got[key]]
        inner = ''.join((f'<h2 class="sb-sh">{E(re.sub(r":.*", "", t))}</h2>' if len(parts) > 1 and '<h2' not in h else '') + h for t, h in parts)
        sub = (f'{assets}{SB_CSS}<div class="advp tbl pfp sbp"><section class="ph tb-hero pf-hero"><p class="ph-e">{cfg["crumb"]}</p>'
               f'<h1>{E(h1)}</h1><p class="sb-dek">{dek}</p>{pic}</section><div class="pf sb-body">{inner}</div>{_sb_nav(cfg, key, path)}</div>')
        u = f'{path}{slug}/'
        page(u, title.replace('&#39;', "'"), desc, sub)
        if u not in SUB_URLS: SUB_URLS.append(u)
    # the car page: each box becomes a link row (merged boxes: the first one stays as the row, the rest go)
    for key, rx, slug, label, icon, *_ in cfg['pages']:
        ds = got.get(key) or []
        if not ds: continue
        if key == 'engine':
            if not cfg.get('_engine'): continue
            href, lab, ico = cfg['_engine'][0], cfg['_engine'][1], 'engine'
        else: href, lab, ico = f'{path}{slug}/', label, icon
        ds[0].replace_with(_SBS(_sb_row(href, E(lab), ico), 'html.parser'))
        for d in ds[1:]:
            sec = d.find_parent('section', class_='cpl-sec'); d.decompose()
            if sec is not None and not sec.find(['details', 'a']): sec.decompose()
    first = soup.select_one('a.sb-go')
    if first is not None: first.insert_before(_SBS(SB_LINKCSS, 'html.parser'))
    return str(soup)
