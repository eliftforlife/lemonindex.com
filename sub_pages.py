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
SUB_THIN = set()   # subpages with under 60 words of their own (noindex, out of the sitemap)
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
SUB_GROUPS = {'jdm', 'cars', 'moto', 'super', 'plane', 'perf'}
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
        ('problems', r'^(Known issues|Problems)', 'problems', 'Problems &amp; recalls' if nh else 'Known issues', 'warning',
         f'{nm} Problems and Recalls{yp}' if nh else f'{nm} Known Issues and Problems{yp}',
         f'{nm} problems and recalls' if nh else f'{nm} known issues', '',
         f'{nm}{yp} problems: known issues' + (', owner complaints to NHTSA by year and every recall' if nh else ' owners and buyers report') + ', with sources.'),
        ('recalls', r'^Recalls', 'recalls', None, None, f'{nm} Recalls{yp}', f'{nm} recalls', '', f'Every {nm} recall from NHTSA, by year.'),
        ('specs', r'^Specs', 'specs', None, None, f'{nm} Specs and Engines by Year', f'{nm} specs and engines', '',
         f'{nm} specs and engines for every year and version, from the EPA and the maker.'),
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

# 11-19 r5 motorcycles, planes, supercars, performance (Elijah's order after regular cars). Only the model pages: their year pages are
# made automatically and already stay out of search.
def _sb_simple(nm, kind):
    if kind == 'moto': return {'name': nm, 'pages': [
        ('problems', r'^Problems', 'problems', None, None, f'{nm} Problems', f'{nm} problems', '', f'{nm} problems: what owners report to NHTSA most, by part.'),
        ('recalls', r'^Recalls', 'recalls', None, None, f'{nm} Recalls', f'{nm} recalls', '', f'Every {nm} recall from NHTSA, newest first.'),
        ('specs', r'^Specs', 'specs', None, None, f'{nm} Specs and Engine', f'{nm} specs', '', f'{nm} specs: engine, power and weight from the maker.'),
        ('repairs', r'^Repairs', 'repairs', None, None, f'{nm} Repair Costs' if len(nm) > 12 else f'{nm} Repair and Service Costs', f'{nm} repair costs', '', f'What {nm} repairs cost: an estimate for each repair, checked against what owners paid.')]}
    if kind == 'super': return {'name': nm, 'pages': [
        ('repairs', r'^Repairs', 'repairs', None, None, f'{nm} Repair and Service Costs', f'{nm} repair and service costs', '',
         f'What {nm} service and repairs cost: an estimate for each job, plus what owners paid.'),
        ('recalls', r'^Recalls', 'recalls', None, None, f'{nm} Recalls', f'{nm} recalls', '', f'Every {nm} recall from NHTSA.'),
        ('specs', r'^Specs', 'specs', None, None, f'{nm} Specs, Engine and MPG', f'{nm} specs and engines', '',
         f'{nm} specs: engines, power and EPA fuel economy for every version.')]}
    if kind == 'plane': return {'name': nm, 'pages': [
        ('accidents', r'^(What happened|Pilot or plane|When$)', 'accidents', None, None, f'{nm} Accident Causes: What Happened',
         f'Why {nm} accidents happen', '', f'Why {nm} accidents happen: what NTSB found, pilot or plane, and the phase of flight.'),
        ('by-year', r'^Accidents per year', 'by-year', None, None, f'{nm} Accidents by Year', f'{nm} accidents by year', '',
         f'{nm} accidents in the US by year, from the NTSB database.'),
        ('repairs', r'^Repairs', 'repairs', None, None, f'{nm} Repair Costs' if len(nm) > 12 else f'{nm} Repair and Inspection Costs', f'{nm} repair costs', '', f'What {nm} repairs and inspections cost: an estimate for each job, checked against what owners paid.')]}

_SB_RENAME = {'When': 'Phase of flight'}

def _sb_h1name(body):
    h = re.search(r'<h1[^>]*>(.*?)</h1>', body, re.S)
    if not h: return ''
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h.group(1))).strip()
    return re.split(r':', re.sub(r'\s+reliability\.?$|\.$', '', t))[0].strip()

def _sb_cfg(path, body=''):
    if path in SUB_CARS: return SUB_CARS[path]
    D = _SB_PERF.get(path)
    if D:
        grp = 'jdm' if D.get('jdm') else 'perf'
        if grp not in SUB_GROUPS or (D.get('mode') == 'inject' and not globals().get('_SB_POST')): return None   # the M3: after perf_page.inject
        return _sb_auto(path, D)
    m = re.fullmatch(r'/cars/([^/]+)/(?:(\d{4})/)?', path)
    if m and 'cars' in SUB_GROUPS and m.group(1) in SUB_CAR_PILOT:
        nm = _sb_h1name(body)
        return _sb_car(path, nm, m.group(2)) if nm else None
    m = re.fullmatch(r'/(motorcycles|supercars|planes)/([^/]+)/', path)
    if m:
        kind = {'motorcycles': 'moto', 'supercars': 'super', 'planes': 'plane'}[m.group(1)]
        nm = _sb_h1name(body)
        return _sb_simple(nm, kind) if nm and kind in SUB_GROUPS else None
    return None

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
          '.sbp .sb-body .pf-iss,.sbp .sb-body .pf-recs{padding-left:0;padding-right:0}a.sb-go,a.sb-go:hover{text-decoration:none}'
          # 11-19 v5 (polish list A1/A8): centered back pill, big centered title, the car's photo; headings centered with their second line small and gray;
          # engine chips wrap instead of running off the screen; later sections of model-year pages sit in boxes (_sb_box)
          '.sbp .sb-top{text-align:center;padding-top:14px}.sbp .sb-back{margin:0;padding:7px 14px 7px 8px;background:#f3f3f5;font-size:15px;color:#1d1d1f}'
          '.sbp .sb-back:hover{background:#e8e8ed}.sbp .sb-top h1{text-align:center;font-size:clamp(34px,10vw,58px);margin:14px auto 0;max-width:680px;letter-spacing:-.035em;line-height:1.04}'
          '.sbp .sb-im img{display:block;width:100%;max-width:440px;height:auto;margin:12px auto 0}'
          '.sbp .sb-body h2:not(.cpl-h){text-align:center;justify-content:center;font-size:clamp(24px,6.6vw,30px);line-height:1.12;letter-spacing:-.02em;margin-left:auto;margin-right:auto}'
          '.sbp .sb-body h2 .h2s{display:block;flex-basis:100%;margin-top:6px;font-size:15px;line-height:1.4;font-weight:500;letter-spacing:0;color:#6e6e73}'
          '.sbp .sb-body section.yc,.sbp .sb-body section.ysev{margin-top:34px}.sbp .sb-body .cpl-b>section:first-child{margin-top:0}'
          '.sbp .n3-row{text-align:center}.sbp .n3-cs{flex-wrap:wrap;overflow:visible;justify-content:center;padding-bottom:0}.sbp .n3-c{max-width:100%;flex:0 1 auto}'
          '.sbp .n3-c b,.sbp .n3-c small{white-space:normal;overflow:visible}'
          '.sbp .sb-bx{margin:12px 0 0;padding:0}.sbp .sb-bx+.sb-bx{margin-top:8px}.sbp .sb-body>:not(.sb-bx)+.sb-bx{margin-top:30px}.sbp .sb-bx .cpl-b section{margin-top:0}'
          '.sbp .sb-bx h2.cpl-h{font-size:17px;margin:0;text-align:left}.sbp .sb-bx .sb-bd{margin:0 0 10px}</style>')
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

def _sb_pic(body):
    """11-19 v5 (A1/A8): the car's own photo from its parent page (the hero image first), for the subpage hero"""
    best = None
    for t in re.findall(r'<img\b[^>]*>', body):
        src, w = re.search(r'\bsrc="([^"]+)"', t), re.search(r'\bwidth="(\d+)"', t)
        if not src or not w or int(w.group(1)) < 600 or not src.group(1).startswith('/assets/') or re.search(r'/assets/(engines|icons)/|icon-', src.group(1)): continue
        if best is None or 'fetchpriority="high"' in t: best = t
        if 'fetchpriority="high"' in t: break
    if best is None: return ''
    g = lambda a: (re.search(a + r'="([^"]*)"', best) or [None, ''])[1]
    return (f'<div class="sb-im"><img alt="{g("alt")}" decoding="async" fetchpriority="high" height="{g("height") or 600}" src="{g("src")}" '
            f'width="{g("width")}"></div>')

_SB_BXIC = ((r'words|say', 'talk'), (r'recall', 'bell'), (r'repair|cost|bill', 'wrench'), (r'when|mileage|year', 'calendar'), (r'engine', 'engine'),
            (r'crash|safety|serious', 'warning'), (r'source', 'info'))

def _sb_box(html):
    """11-19 v5 (A1): a model-year subpage keeps its first two sections open (the main chart); the rest go into boxes. Same words, same ids."""
    x = _SBS(html, 'html.parser')
    root = x.select_one('div.cpl-b') or x
    secs = root.find_all('section', recursive=False)
    if len(secs) < 3: return html
    bx = []
    for sec in secs[2:]:
        h = sec.find('h2', recursive=False)
        if h is None: continue
        sm = h.select_one('.h2s')
        if sm is not None: sm = sm.extract()
        t = h.decode_contents().strip()
        h.decompose()
        if sm is not None and sm.get_text(strip=True): sec.insert(0, _SBS(f'<p class="yc-cap sb-bd">{sm.decode_contents()}</p>', 'html.parser'))
        tl = re.sub(r'<[^>]+>', '', t).lower()
        ic = next((i for rx, i in _SB_BXIC if re.search(rx, tl)), 'chart')
        bx.append(f'<div class="cpl sb-bx">{V5_BOX(ic, t, str(sec), h2=True)}</div>')
        sec.decompose()
    return str(x) + ''.join(bx)   # the boxes go last, after the open sections

SB_LINKCSS = '<style>a.sb-go,a.sb-go:hover{text-decoration:none;color:inherit}</style>'

def SUB_HOOK(path, body):
    cfg = _sb_cfg(path, body)
    if not cfg or 'cpl-sec' not in body: return body
    try: return _sub_hook(path, body, cfg)
    except Exception as ex:
        globals().setdefault('TAB_FAIL', []).append(f'sub_pages {path}: {type(ex).__name__} {ex}'); return body

# 11-23 (old-pages audit #9, Elijah approved): on the engine sub-pages (/cars/<model>/<year>/engines/ and /cars/<model>/engines/) the
# "ENGINES IN THIS CAR" capital label + pill chips become a sentence-case heading and one inset list (title + years), the source note in a box
_N3C = re.compile(r'<(a|span) class="n3-c[^"]*"(?: href="([^"]*)")?><b>(.*?)</b>(?:<small>(.*?)</small>)?</' + chr(92) + '1>', re.S)
N3L_CSS = ('<style>.n3l-h{text-align:center;font-size:clamp(24px,6.6vw,30px);letter-spacing:-.02em;margin:8px 0 0}.n3l{margin-top:16px}'
           '.n3l .cpl-a span{display:flex;flex-direction:column;gap:2px;min-width:0}.n3l .cpl-a small{font-size:13px;font-weight:500;color:#6e6e73}'
           '.n3l .n3l-x{display:flex;align-items:center;gap:12px;padding:14px 16px;color:#1d1d1f}.n3l-i{margin-top:12px}</style>')
def _n3_list(h):
    m = re.search(r'<nav(?=[^>]*class="n3-row")(?=[^>]*aria-label="Engines in this car")[^>]*>(.*?)</nav>', h, re.S)
    if not m: return h
    inner = m.group(1)
    hd = re.search(r'<p class="n3-h">(.*?)</p>', inner, re.S); nt = re.search(r'<p class="n3-n">(.*?)</p>', inner, re.S)
    rows = []
    for tag, href, name, small in _N3C.findall(inner):
        t = f'<span><b>{name}</b>' + (f'<small>{small}</small>' if small else '') + '</span>'
        rows.append(f'<div class="cpl"><a class="cpl-a" href="{href}">{V5_IC("engine")}{t}{PILL_GO}</a></div>' if tag == 'a' and href
                    else f'<div class="cpl"><div class="n3l-x">{V5_IC("engine")}{t}</div></div>')
    if not rows: return h
    keep = ''.join(re.findall(r'<script[^>]*></script>', inner))
    out = (N3L_CSS + keep + (f'<h2 class="n3l-h">{hd.group(1)}</h2>' if hd else '') + '<div class="cpl-grp cpl-ins n3l">' + ''.join(rows) + '</div>'
           + (f'<div class="cpl n3l-i">{V5_BOX("info", "Where this list comes from", "<p class=" + chr(34) + "yc-cap" + chr(34) + ">" + nt.group(1) + "</p>")}</div>' if nt else ''))
    return h[:m.start()] + out + h[m.end():]
def _sub_hook(path, body, cfg):
    soup = _SBS(body, 'html.parser')
    boxes = [d for d in soup.select('section.cpl-sec > div.cpl > details') if not d.find_parent('div', class_='cpl-b')]
    got = {}   # key -> [(title, html, details)]
    for d in boxes:
        t = _sb_title(d)
        for key, rx, *_ in cfg['pages']:
            if re.match(rx, t): got.setdefault(key, []).append(d); break
    assets = body[:body.find('<div class="advp')] if '<div class="advp' in body else ''.join(str(t) for t in soup.find_all(['link', 'style']) + soup.find_all('script', src=True))
    # engines (11-19 r5): each engine card links to that engine's own page; one engine card without a page gets a subpage
    eng = got.pop('engine', [])
    for d in eng:
        a = d.select_one('a[href^="/engines/"]')
        if a is not None: d.replace_with(_SBS(_sb_row(a['href'].split('#')[0], E(_sb_title(d)), 'engine'), 'html.parser'))
    if len(eng) == 1 and eng[0].select_one('a[href^="/engines/"]') is None: got['engine'] = eng
    # the subpages (11-19 r2, Elijah: "only have what they clicked for ... short, big header and back arrow"): back arrow, big title, that
    # card's content and its sources. No photo, intro line, other cards, side notes, fine print or feedback box.
    pic = _sb_pic(body)
    for key, rx, slug, label, icon, title, h1, dek, desc in cfg['pages']:
        if not slug or not got.get(key): continue
        h1 = h1 or _sb_title(got[key][0])
        parts = [_sb_inner(d) for d in got[key]]
        ts = [_SB_RENAME.get(re.sub(r':.*', '', t), re.sub(r':.*', '', t)) for t, _ in parts]
        if len(set(ts)) < len(ts): ts = [t for t, _ in parts]   # "Known issues: BMW S54", "Known issues: BMW S65" keep their engine
        inner = ''.join((f'<h2 class="sb-sh">{E(t)}</h2>' if len(parts) > 1 and '<h2' not in h else '') + h for t, (_, h) in zip(ts, parts))
        inner = _sb_trim(inner, key)
        if slug == 'engines': inner = _n3_list(inner)   # 11-23 (old-pages audit #9): engine chips -> one inset list
        if re.fullmatch(r'/cars/[^/]+/\d{4}/', path): inner = _sb_box(inner)
        sub = (f'{assets}{SB_CSS}<div class="advp tbl pfp sbp"><section class="sb-top"><a class="sb-back" href="{path}">{_SB_BACK}<span>{E(cfg["name"])}</span></a>'
               f'<h1>{E(h1)}</h1>{pic}</section><div class="pf sb-body">{inner}</div></div>')
        u = f'{path}{slug}/'
        if len(re.sub(r'<[^>]+>', ' ', inner).split()) < 60: SUB_THIN.add(u)
        if u not in NOFB: globals()['NOFB'] = tuple(NOFB) + (u,)   # no feedback box on these short pages
        page(u, title.replace('&#39;', "'"), desc, sub)
        if u not in SUB_URLS: SUB_URLS.append(u)
        if u in PD: PD[u]['sb'] = 2 if u in SUB_THIN else 1   # remembered in page_dates.json, so quick builds that skip this car keep it (SUB_ALL)
    # the car page: each box becomes a link row (merged boxes: the first one stays as the row, the rest go). 11-19 r5: on a page with a
    # generation picker (.pf-g blocks, only the picked one shows) a card that spans generations gets ONE row after the last block, so it
    # shows whichever generation is picked; a one-generation card (the engine) keeps its row inside its block.
    gens = soup.select('div.pf-g')
    shared = None
    for key, rx, slug, label, icon, title, h1, *_ in cfg['pages']:
        ds = got.get(key) or []
        if not ds or not slug: continue
        sm = ds[0].find('summary', recursive=False)
        u, im = sm.select_one('use') if sm else None, sm.select_one('img[src*="/assets/icons/"]') if sm else None
        multi = len({id(d.find_parent('div', class_='pf-g')) for d in ds}) > 1 or (len(ds) > 1 and ds[0].find_parent('div', class_='pf-g') is not None)
        if key == 'problems' and got.get('recalls') and label and 'recalls' in label: label = 'Problems'   # the M3 has its own Recalls card
        href, lab = f'{path}{slug}/', label or (E(h1) if multi and h1 else E(_sb_title(ds[0])))
        ico = icon or (u.get('href', '').rsplit('#', 1)[-1] if u is not None else re.sub(r'\.\w+(\?.*)?$', '', im['src'].rsplit('/', 1)[-1]) if im is not None else None)
        if ico and ico not in _CP_SPR: ico = 'info'
        row = _SBS(_sb_row(href, lab if '&' in lab else E(lab), ico), 'html.parser')
        if gens and any(d.find_parent('div', class_='pf-g') is not None for d in ds):
            if shared is None:
                shared = _SBS('<section class="cpl-sec sb-shared"><div class="cpl"></div></section>', 'html.parser').section
                gens[-1].insert_after(shared)
            shared.div.append(row)
            rest = ds
        else:
            ds[0].replace_with(row); rest = ds[1:]
        for d in rest:
            sec = d.find_parent('section', class_='cpl-sec'); d.decompose()
            if sec is not None and not sec.find(['details', 'a']): sec.decompose()
    first = soup.select_one('a.sb-go')
    if first is not None: first.insert_before(_SBS(SB_LINKCSS, 'html.parser'))
    return str(soup)

def SUB_POST(path, body, force=False):
    """perf_page.inject() (the M3): fold into boxes first, then cards -> own pages"""
    body = CAR_HOOK(path, body, force)
    globals()['_SB_POST'] = True
    try:
        cfg = _sb_cfg(path, body)
        return _sub_hook(path, body, cfg) if cfg and 'cpl-sec' in body else body
    finally: globals()['_SB_POST'] = False

def SUB_ALL():
    """every card page for the sitemap: the ones built now, plus (quick builds) the ones whose car wasn't rebuilt, from page_dates.json"""
    out = list(SUB_URLS)
    if QM.ON:
        for u, e in PD.items():
            if isinstance(e, dict) and e.get('sb') and u not in SUB_URLS and not QM.want(u):
                out.append(u)
                if e['sb'] == 2: SUB_THIN.add(u)
    return out
