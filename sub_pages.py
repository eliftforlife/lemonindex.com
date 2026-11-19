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


# 11-19 r3 (Elijah: "do similar thing for all jdm cars"): every page in SUB_GROUPS gets its config made from its data/perf/<slug>.json.
# SUB_CARS entries (hand-written titles) win over the made ones.
SUB_GROUPS = {'jdm', 'cars'}
_SB_PERF = {}
for _p in glob.glob(os.path.join('data', 'perf', '*.json')):
    if _p.endswith('.auto.json'): continue
    try:
        _d = json.load(open(_p, encoding='utf-8'))
        if _d.get('page'): _SB_PERF[_d['page']] = _d
    except Exception: pass

def _sb_an(w):   
    return ('an ' if re.match(r'(?i)[aeio]', w) else 'a ') + w   # the make is said first: "an Acura NSX", "a Mazda RX-7"

def _sb_auto(path, D):
    nm = re.split(r' \(|:', D.get('h1') or D['name'])[0].strip()
    G = D.get('gens') or []
    yrs = f'{min(g["y0"] for g in G)}-{max(g["y1"] for g in G)}' if G and all(g.get('y0') and g.get('y1') for g in G) else ''
    yp = f' ({yrs})' if yrs else ''
    fl = D.get('films') or []
    films = list(dict.fromkeys(f['film'] for f in fl))
    who = list(dict.fromkeys(f['who'] for f in fl if f.get('who') and 'film cars' not in f['who'].lower() and 'crew' not in f['who'].lower()))
    ff = all(re.search(r'Fast|Furious', f) for f in films)
    if films:
        f_h1 = f'The {nm} in ' + (re.sub(r' \(\d{4}\)$', '', films[0]) if len(films) == 1 else ('the Fast & Furious films' if ff else 'the films'))
        f_t = f'{nm} in Fast and Furious' if ff else f'{nm} in the Movies'
        if who and len(f_t) + len(' & '.join(who)) + 10 <= 65: f_t += ': ' + ' and '.join(who) + ('&#39;s Car' if len(who) == 1 else '&#39;s Cars')
        f_d = f'The {nm} in ' + ' and '.join(films) + (': ' + ', '.join(f"{w}&#39;s car" for w in who) if who else '') + '. Which scene, which car, with sources.'
        films_pg = ('films', r'^In the films', 'films', None, None, f_t, f_h1, '', f_d)
    else:
        films_pg = ('films', r'^Why it', 'famous', None, None, f'Why the {nm} Is Famous', f'Why the {nm} is famous', '',
                    f'Why the {nm} is famous: the races, games and history behind it, with sources.')
    nh = bool(D.get('nhtsa'))
    return {'name': nm, 'pages': [
        films_pg,
        ('speed', r'^How fast', '0-60', None, None, f'{nm} 0-60, Horsepower and Specs{yp}', f'How fast is the {nm}?', '',
         f'{nm}{yp} 0-60 times, horsepower, torque, weight and price new for every version. Every number sourced.'),
        ('engine', r'^The engine', 'engine', None, None, f'{nm} Engine Specs{yp}', None, '', f'The {nm} engine: specs, power and what it was built for, with sources.'),
        ('problems', r'^(Known issues|Problems & recalls)', 'problems', 'Problems &amp; recalls' if nh else 'Known issues', 'warning',
         f'{nm} Problems and Recalls{yp}' if nh else f'{nm} Known Issues and Problems{yp}',
         f'{nm} problems and recalls' if nh else f'{nm} known issues', '',
         f'{nm}{yp} problems: known issues' + (', owner complaints to NHTSA by year and every recall' if nh else ' owners and buyers report') + ', with sources.'),
        ('buy', r'^(Should you buy|What owners say)', 'buying', None, None, f'Should You Buy {_sb_an(nm)}? What to Check',
         f'Should you buy {_sb_an(nm)}?', '', f'Should you buy {_sb_an(nm)}{yp}? Price new, best and worst years, what to check and what YouTube owners say.'),
    ]}

# 11-19 r4 regular cars, pilot first (Elijah picked "Pilot first": the 20 most-searched models and all their years, watch Search Console
# ~7 days, then the rest). Year page: problems, repairs, recalls, engines, mileage. Model page: youtube, engines.
SUB_CAR_PILOT = {'mercedes-benz-c-class', 'hyundai-sonata', 'honda-civic', 'bmw-3-series', 'nissan-sentra', 'chevrolet-equinox', 'audi-q5',
                 'audi-a4', 'jeep-patriot', 'toyota-4runner', 'toyota-camry', 'jeep-wrangler', 'toyota-tacoma', 'jeep-grand-cherokee',
                 'dodge-grand-caravan', 'ram-pickup', 'acura-mdx', 'acura-rdx', 'nissan-rogue', 'kia-sedona'}
SUB_THIN_KEYS = {'engines-y'}   # subpages too small to stand in search on their own (noindex, out of the sitemap; quality_gate.py)

def _sb_car(path, nm, year):
    if year:
        return {'name': nm, 'pages': [
            ('problems', r'^Problems$', 'problems', None, None, f'{nm} Problems and Complaints', f'{nm} problems', '',
             f'{nm} problems: what owners reported to NHTSA most, by part, with real complaint counts.'),
            ('repairs', r'^Repairs', 'repairs', None, None, f'{nm} Repair Costs', f'{nm} repair costs', '',
             f'What {nm} repairs cost: the bills owners named in their complaints to NHTSA, by part.'),
            ('recalls', r'^Recalls', 'recalls', None, None, f'{nm} Recalls and Safety Ratings', f'{nm} recalls and safety', '',
             f'Every {nm} recall and its crash test ratings, from NHTSA.'),
            ('engines-y', r'^Engines', 'engines', None, None, f'{nm} Engines', f'{nm} engines', '',
             f'The engines in the {nm}, each with a page of its own.'),
            ('mileage', r'^When problems show up', 'mileage', None, None, f'{nm} Problems by Mileage', f'When {nm} problems show up', '',
             f'At what mileage {nm} problems show up, from the mileage owners gave in their NHTSA complaints.'),
        ]}
    return {'name': nm, 'pages': [
        ('youtube', r'^What owners say', 'youtube', None, None, f'{nm} Owner Reviews: What YouTube Owners Say', f'What {nm} owners say on YouTube', '',
         f'What {nm} owners say on YouTube: the topics they praise and complain about, the best-rated years and the most-watched videos.'),
        ('engines', r'^Engines', 'engines', None, None, f'{nm} Engines by Year', f'{nm} engines and versions', '',
         f'Every {nm} engine and version by year, gas or hybrid, with specs from EPA and the maker.'),
    ]}

def _sb_cfg(path, body=''):
    if path in SUB_CARS: return SUB_CARS[path]
    m = re.fullmatch(r'/cars/([^/]+)/(?:(\d{4})/)?', path)
    if m and 'cars' in SUB_GROUPS and m.group(1) in SUB_CAR_PILOT and path not in _SB_PERF:
        h = re.search(r'<h1[^>]*>(.*?)</h1>', body, re.S)
        nm = re.sub(r'\s+reliability\.?$', '', re.sub(r'<[^>]+>', '', h.group(1)).strip()) if h else ''
        return _sb_car(path, nm, m.group(2)) if nm else None
    D = _SB_PERF.get(path)
    if not D: return None
    grp = 'jdm' if D.get('jdm') else 'perf'
    return _sb_auto(path, D) if grp in SUB_GROUPS else None

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

SB_CSS = ('<style>.sbp .sb-top{max-width:760px;margin:0 auto;padding:18px 0 0}'
          '.sbp .sb-back{display:inline-flex;align-items:center;gap:4px;margin-left:-6px;padding:6px 10px 6px 4px;border-radius:999px;color:#1d1d1f;'
          'font-size:17px;font-weight:600;text-decoration:none}.sbp .sb-back:hover{background:#f3f3f5}'
          '.sbp .sb-top h1{font-size:clamp(36px,9vw,56px);line-height:1.05;letter-spacing:-.03em;font-weight:800;margin:14px 0 0;text-align:left}'
          '.sbp .sb-dek{font-size:19px;line-height:1.45;color:#3a3a3c;max-width:640px;margin:10px auto 0;text-align:center}'
          '.sbp .sb-body{max-width:760px;margin:28px auto 0;padding:0}.sbp .sb-body>h2.sb-sh{font-size:24px;margin:34px 0 10px;letter-spacing:-.015em}'
          '.sbp .sb-body>h2.sb-sh:first-child{margin-top:0}.sbp .sb-more{max-width:760px;margin:40px auto 0;padding:0 16px}'
          '.sbp .sb-h{font-size:22px;margin:0 0 12px;letter-spacing:-.015em}.sbp .sb-more .cpl{display:grid;gap:8px}'
          '.sbp .sb-body details.pf-cs{margin-top:10px}.sbp .sb-pic{display:block;width:100%;max-width:520px;height:auto;margin:18px auto 0}'
          '.sbp .sb-body>.cpl-b{padding:0;margin:0}.sbp .sb-body>.cpl-b>:first-child,.sbp .sb-body>.cpl-b>:first-child>h2:first-child{margin-top:0!important;padding-top:0!important}'
          '.sbp .sb-body .pf-iss,.sbp .sb-body .pf-recs{padding-left:0;padding-right:0}a.sb-go,a.sb-go:hover{text-decoration:none}</style>')
_SB_BACK = ('<svg aria-hidden="true" fill="none" height="22" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" '
            'stroke-width="2.4" viewBox="0 0 24 24" width="22"><path d="m15 18-6-6 6-6"></path></svg>')

def _sb_trim(html, key):
    """only what the card is about: side notes (.pf-li), fine print (.pf-cap/.pf-dek) and nested boxes opened up; problems keeps its counts"""
    x = _SBS(html, 'html.parser')
    for d in x.find_all('details'):
        if 'pf-cs' in (d.get('class') or []) or (d.summary and d.summary.get_text(strip=True).startswith(('Sources', 'Engine sources'))): continue
        sm = d.find('summary', recursive=False)
        t = _sb_title(d) if sm else ''
        if sm: sm.decompose()
        if t and not d.find('h2') and not re.match(r'(?i)(show|more|see) ', t): d.insert(0, _SBS(f'<h2 class="sb-sh">{E(t)}</h2>', 'html.parser'))   # "Show all 5 recalls" just opens
        d.unwrap()
    for el in x.select('.pf-li'):
        if key == 'problems' and el.get_text(' ', strip=True).startswith('NHTSA files'): continue
        el.decompose()
    for el in x.select('.pf-cap, .pf-dek'):
        if key == 'problems' and (el.get_text(strip=True).startswith('Source: NHTSA') or 'complaint' in el.get_text()): continue
        el.decompose()
    for el in x.select('li'):   # "we don't have ... yet" lines say nothing on a page this short
        if re.search(r"we don.t have", el.get_text(' ', strip=True)): el.decompose()
    for el in x.select('.pf-recs p'):   # NHTSA recall text arrives in capitals
        t = el.get_text(' ', strip=True)
        if sum(c.isupper() for c in t) > .6 * max(1, sum(c.isalpha() for c in t)): el.string = t[:1] + t[1:].lower()
    return str(x)

SB_LINKCSS = '<style>a.sb-go,a.sb-go:hover{text-decoration:none;color:inherit}</style>'

def SUB_HOOK(path, body):
    cfg = _sb_cfg(path, body)
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
    assets = body[:body.find('<div class="advp')] if '<div class="advp' in body else ''.join(str(t) for t in soup.find_all(['link', 'style']) + soup.find_all('script', src=True))
    if got.get('engine'):
        a = got['engine'][0].select_one('a[href^="/engines/"]')
        cfg['_engine'] = (a['href'].split('#')[0], _sb_title(got['engine'][0])) if a else None
    # the subpages (11-19 r2, Elijah: "only have what they clicked for ... short, big header and back arrow"): back arrow, big title, that
    # card's content and its sources. No photo, intro line, other cards, side notes, fine print or feedback box.
    for key, rx, slug, label, icon, title, h1, dek, desc in cfg['pages']:
        if not slug or not got.get(key) or (key == 'engine' and cfg.get('_engine')): continue   # an engine with its own page links there
        h1 = h1 or _sb_title(got[key][0])
        parts = [_sb_inner(d) for d in got[key]]
        inner = ''.join((f'<h2 class="sb-sh">{E(re.sub(r":.*", "", t))}</h2>' if len(parts) > 1 and '<h2' not in h else '') + h for t, h in parts)
        inner = _sb_trim(inner, key)
        sub = (f'{assets}{SB_CSS}<div class="advp tbl pfp sbp"><section class="sb-top"><a class="sb-back" href="{path}">{_SB_BACK}<span>{E(cfg["name"])}</span></a>'
               f'<h1>{E(h1)}</h1></section><div class="pf sb-body">{inner}</div></div>')
        u = f'{path}{slug}/'
        if u not in NOFB: globals()['NOFB'] = tuple(NOFB) + (u,)   # no feedback box on these short pages
        page(u, title.replace('&#39;', "'"), desc, sub)
        if u not in SUB_URLS: SUB_URLS.append(u)
    # the car page: each box becomes a link row (merged boxes: the first one stays as the row, the rest go)
    for key, rx, slug, label, icon, *_ in cfg['pages']:
        ds = got.get(key) or []
        if not ds: continue
        if key == 'engine' and cfg.get('_engine'): href, lab, ico = cfg['_engine'][0], cfg['_engine'][1], 'engine'
        elif not slug: continue
        else:
            sm = ds[0].find('summary', recursive=False)
            u, im = sm.select_one('use') if sm else None, sm.select_one('img[src*="/assets/icons/"]') if sm else None
            href, lab = f'{path}{slug}/', label or E(_sb_title(ds[0]))
            ico = icon or (u.get('href', '').rsplit('#', 1)[-1] if u is not None else re.sub(r'\.\w+(\?.*)?$', '', im['src'].rsplit('/', 1)[-1]) if im is not None else None)
            if ico and ico not in _CP_SPR: ico = 'info'
        ds[0].replace_with(_SBS(_sb_row(href, lab if '&' in lab else E(lab), ico), 'html.parser'))
        for d in ds[1:]:
            sec = d.find_parent('section', class_='cpl-sec'); d.decompose()
            if sec is not None and not sec.find(['details', 'a']): sec.decompose()
    first = soup.select_one('a.sb-go')
    if first is not None: first.insert_before(_SBS(SB_LINKCSS, 'html.parser'))
    return str(soup)
