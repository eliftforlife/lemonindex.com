import hashlib
import re
# Builds lemonindex.com into docs/ (GitHub Pages serves main /docs).   usage: py build.py
# Pages: home, /studies/, /studies/most-reliable-cars/, /method/, 404 + sitemap.xml, robots.txt, llms.txt, CNAME.
# Look = the channel's thumbnails: white, Inter, #111 type, lemon yellow #ffd400 for the brand, red #e8141c only for "bad" (the lemon end).
# Every number comes from data/*.csv (autopilot/lib/lemon.py, with the 10-24 mysales sales-timing fix); was 3 Lemon Index/video 1 most reliable/findings.md (NHTSA complaints ÷ US sales, model years 2010-2022).
import os, re, json, html, datetime, shutil, csv
from collections import defaultdict
import year_slider as YSL   # 11-10: AI year illustrations + 'every year' slider (data/ai_year_images.json)
import tabbed as TAB   # 11-10 (Elijah, Civic first): centered hero + tabs + Years/Engines chart for the models in TAB.ON
OUT = 'docs'; TODAY = datetime.date.today().isoformat(); BASE = 'https://lemonindex.com'
E = lambda s: html.escape(str(s), quote=True)
YT, TT, IG = 'https://www.youtube.com/@lemonindex', 'https://www.tiktok.com/@lemonindex', 'https://www.instagram.com/lemonindex/'
# 11-10 footer social icons (monochrome line icons)
_SOC = lambda d: f'<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{d}</svg>'
F2_SOC = (f'<a href="{YT}" rel="noopener" aria-label="YouTube">' + _SOC('<rect x="2.5" y="5.5" width="19" height="13" rx="4"/><path d="M10 9.2v5.6l4.8-2.8z" fill="currentColor" stroke="none"/>') + '</a>'
          f'<a href="{TT}" rel="noopener" aria-label="TikTok">' + _SOC('<path d="M14 4v10.2a3.3 3.3 0 1 1-3.3-3.3"/><path d="M14 4c.4 2.4 2.1 4 4.6 4.2"/>') + '</a>'
          f'<a href="{IG}" rel="noopener" aria-label="Instagram">' + _SOC('<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".6" fill="currentColor"/>') + '</a>')
ADS = 'ca-pub-6568065738106248'   # Google AdSense, added 11-09 (auto ads; loader in assets/ads.js, ads.txt at the root)
GA = 'G-3352CDDC5E'   # Google Analytics 4, added 11-08 (Mediavine Journey checks GA4 sessions); config in assets/ga.js
CF = 'b04082d02f994049b6b6e0f5aa631ff4'   # Cloudflare Web Analytics (cookieless) token for lemonindex.com, added 10-21

BEST = [('Toyota 4Runner', 27, '1.27M'), ('Lexus ES', 28, '0.70M'), ('Porsche Macan', 31, '0.17M'), ('Lexus RX', 32, '1.34M'), ('Nissan Frontier', 37, '0.83M'),
        ('BMW 3 Series', 37, '1.24M'), ('Honda HR-V', 41, '0.74M'), ('Hyundai Accent', 42, '0.59M'), ('Toyota Tacoma', 44, '2.47M'), ('Mercedes-Benz E-Class', 45, '')]
WORST = [('Tesla Model S*', 430, 'suspension 34%, steering 16%'), ('Chevrolet Bolt', 410, 'electrical 54% (battery-fire recall)'), ('Tesla Model X*', 405, 'suspension 27%'),
         ('Tesla Model Y*', 360, 'forward collision avoidance 85% (phantom braking)'), ('Jeep Cherokee (2014+)', 307, 'power train 47%'),
         ('Chrysler Pacifica (2017+)', 281, 'engine 36%, electrical 35%'), ('Chrysler 200', 261, 'electrical, power train'), ('Chevrolet Volt', 261, 'electrical, power train'),
         ('Kia Telluride', 256, 'wipers and visibility 28%'), ('Hyundai Palisade', 249, 'wipers and visibility 25%')]
BRANDS = [('Lexus', 30), ('Porsche*', 34), ('Toyota', 50), ('BMW', 52), ('Mercedes-Benz', 54), ('Nissan', 66), ('Mazda', 66), ('Chevrolet', 70), ('Audi', 74), ('GMC', 86),
          ('Honda', 87), ('Kia', 89), ('Acura', 91), ('Hyundai', 109), ('Ram', 120), ('Dodge', 132), ('Volkswagen', 139), ('Subaru', 143), ('Ford', 144), ('Jeep', 196),
          ('Chrysler', 215), ('Tesla*', 322)]
SEGMENTS = [('Cars', 'Lexus ES 28 · BMW 3 Series 37 · Hyundai Accent 42', 'Tesla Model S 430 · Chevrolet Bolt 410 · Chrysler 200 261'),
            ('SUVs', 'Toyota 4Runner 27 · Porsche Macan 31 · Lexus RX 32', 'Tesla Model X 405 · Tesla Model Y 360 · Jeep Cherokee 307'),
            ('Trucks', 'Nissan Frontier 37 · Toyota Tacoma 44 · Chevrolet Silverado 53', 'Jeep Gladiator 194 · Honda Ridgeline 164 · Ram 1500 119'),
            ('Minivans', 'Toyota Sienna 53', 'Chrysler Pacifica 281 · Chrysler Town & Country 175')]
# 11-12 (Linda, Priya): ONE sentence for what the index measures, used site-wide. It counts owner complaints; it is not a crash-safety rating.
WHAT_LI_T = ("The Lemon Index counts owner complaints filed with the U.S. government (NHTSA) in a car's first 3 years, per car sold, "
             "against the average car of the same model years (100 = average, lower is better). It measures complaints, not crash safety.")
WHAT_LI = WHAT_LI_T.replace("'", '&#39;')
FAQ = [('What is the Lemon Index?', WHAT_LI_T + ' 50 means half as many complaints as the average car, 300 means three times as many.'),
       ('What is the most reliable car by owner complaints?', 'The Toyota 4Runner, with a Lemon Index of 27: about a quarter of the complaints of the average car, across 1.27 million sold (model years 2010-2022).'),
       ('Which car brand has the fewest complaints?', 'Lexus, at 30, followed by Porsche (34, small sample), Toyota (50), BMW (52) and Mercedes-Benz (54).'),
       ('Why does Tesla score so badly?', 'Most Model 3 and Model Y complaints are about forward collision avoidance (phantom braking). Tesla doesn\'t publish U.S. sales by model, so its index uses published estimates.'),
       ('Is this the same as a repair-cost ranking?', 'No. It counts owner complaints filed with the government within 3 years of each model year. It is not a record of repair bills or out-of-warranty costs.')]

# ---- all 131 models for the explorer (copied from 3 Lemon Index/video 1 most reliable/data/out, 10-22)
PART = {'ELECTRICAL SYSTEM': 'electrical', 'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'VEHICLE SPEED CONTROL': 'speed control',
        'FUEL/PROPULSION SYSTEM': 'fuel or EV drive system', 'FORWARD COLLISION AVOIDANCE': 'automatic emergency braking', 'VISIBILITY/WIPER': 'wipers & visibility',
        'VISIBILITY': 'visibility', 'AIR BAGS': 'airbags', 'STRUCTURE': 'body structure', 'EXTERIOR LIGHTING': 'lights', 'ELECTRONIC STABILITY CONTROL (ESC)': 'stability control',
        'LANE DEPARTURE': 'lane assist', 'ENGINE AND ENGINE COOLING': 'engine', 'SEAT BELTS': 'seat belts'}
SEGN = {'car': 'Car', 'suv': 'SUV', 'truck': 'Truck', 'minivan': 'Minivan', 'van': 'Van'}   # 11-11 'van': the full-size Ford Transit
ISS = defaultdict(list)
for r in csv.DictReader(open('data/family_components.csv', encoding='utf-8')):
    if r['component'] != 'UNKNOWN OR OTHER' and len(ISS[r['family']]) < 3: ISS[r['family']].append([PART.get(r['component'], r['component'].lower()), round(float(r['share_pct']))])
CARS = []
for r in csv.DictReader(open('data/family_rates.csv', encoding='utf-8')):
    sold = int(r['us_sold'])
    CARS.append(dict(id=r['family'].lower().replace(' ', '-').replace('(', '').replace(')', '').replace('+', 'plus').replace('&', 'and'), name=r['family'], brand=r['brand'],
                     seg=r['segment'], segName=SEGN.get(r['segment'], r['segment']), years=r['years'], sold=sold, est=r['sales_note'] == 'estimate' or r['brand'] == 'Tesla',
                     n=int(r['complaints_3yr']), per100k=round(float(r['per_100k'])), avg=round(float(r['expected']) / sold * 1e5), li=int(r['lemon_index']),
                     serious=round(float(r['serious_pct'])), worst=r['worst_year'], issues=ISS[r['family']]))
CARS.sort(key=lambda c: c['li'])
for i, c in enumerate(CARS, 1): c['rank'] = i
# 11-11 (Elijah: fill the "No data yet" cards): models added one by one by data_new_models.py, scored with the study's method against the
# published average car. They get model + year pages and a real /cars/ card, but stay out of the study's ranking of 131 (CARS / rank).
CARS_NEW = []
for r in (json.load(open('data/cars_new.json', encoding='utf-8')) if os.path.exists('data/cars_new.json') else []):
    CARS_NEW.append(dict(id=r['id'], name=r['name'], brand=r['brand'], seg=r['segment'], segName=SEGN.get(r['segment'], r['segment']), years=r['years'], sold=r['sold'], est=False,
                         n=r['n'], per100k=r['per100k'], avg=round(r['expected'] / r['sold'] * 1e5), li=r['li'], serious=r['serious'], worst=r['worst'], issues=r['issues'],
                         new=True, sales_url=r.get('sales_url'), sales_kind=r.get('sales_kind')))
_YJ = json.load(open('data/years.json', encoding='utf-8')) + (json.load(open('data/years_new.json', encoding='utf-8')) if os.path.exists('data/years_new.json') else [])
_YJ += json.load(open('data/years_tesla.json', encoding='utf-8')) if os.path.exists('data/years_tesla.json') else []   # 11-12 UX test: Tesla Model S/3/X year pages (data_tesla.py)
# 11-11 (Elijah): low-sales years (cited U.S. sales under 20,000) are listed too: complaints, problems, recalls and a year page, never a score
# (li None, ok False), never a best/worst pick. Study models: data/years_low.json (data_lowsales.py); new models carry them in years_new.json.
_YLOW = json.load(open('data/years_low.json', encoding='utf-8')) if os.path.exists('data/years_low.json') else {}
for _f in _YJ:
    if _YLOW.get(_f['id']): _f['years'] = sorted(_f['years'] + [v for v in _YLOW[_f['id']] if v['y'] not in {w['y'] for w in _f['years']}], key=lambda v: v['y'])
COUNTED = sum(c['n'] for c in CARS)
BYNAME = {c['name']: c for c in CARS + CARS_NEW}
YP = {f['id'] for f in _YJ}   # models with a page per model year (10-29)
for c in CARS: c['yp'] = c['id'] in YP
PICK = {}
for f in _YJ:
    if f['name'] in BYNAME: PICK.setdefault(BYNAME[f['name']]['brand'], []).append([f['name'], f['id'], [v['y'] for v in f['years']]])
PICK = dict(sorted((b, sorted(m)) for b, m in PICK.items()))
# 11-11 (Elijah: one Cars section, one search for everything): the finder also finds the supercars, the EVs and the performance cars.
# Their entries carry a 4th item (the page they open; they have no year pages, '' = coming soon) and a 5th (the kind: sc / ev / perf).
# PICK itself stays regular-only (the VIN page and the year pages use it).
_jl = lambda p: json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
_slg = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower().replace("'", '')).strip('-')
SCX = _jl('data/supercars.json') or []
EVX = (_jl('data/ev.json') or {}).get('cars', [])
# 11-12 (Priya, Dan: "Model S 430 here, 679 there"): two windows, always labelled. The main Lemon Index scores each model's own model years
# (data/family_rates.csv 'years') with complaints from each car's first 3 years; the EV ranking (data/ev.json) scores model years
# EV_WIN with complaints filed by the end of the year after the model year (so brand-new EVs get a complete window).
EV_WIN = (lambda y: f'{y[0]}–{y[1]}')((_jl('data/ev.json') or {}).get('years') or [2021, 2024])
EVBY = {c['slug']: c for c in EVX}
MAINBY = {c['id']: c for c in CARS}
YRS = lambda c: c['years'].replace('-', '–')   # a model's main-score window, e.g. 2012–2020
def two_windows(slug, here='main'):
    """One sentence naming both scores of a car that has both, each with its window ('' if it has only one)."""
    e, m = EVBY.get(slug), MAINBY.get(slug)
    if not e or not m: return ''
    a = f'Lemon Index <b>{m["li"]}</b> for model years {YRS(m)} (complaints in each car&#39;s first 3 years)'
    b = f'EV score <b>{e["li"]}</b> for model years {e["years"].replace("-", "–")} (complaints filed by the end of the year after the model year)'
    return (f'Two scores, two windows: {a if here == "main" else b} on this page; {b if here == "main" else a} on '
            + (f'<a href="/electric/{slug}/">its EV page</a>' if here == 'main' else f'<a href="/cars/{slug}/">its main page</a>' if slug in {f["id"] for f in _YJ} else 'the main rankings')
            + '. Different model years and windows, so the numbers differ.')
PERFX = _jl('data/perf_cars.json') or []   # the performance list (another agent researches it); empty = the tab shows "Coming soon"
if isinstance(PERFX, dict): PERFX = PERFX.get('cars', [])
_bk = {b.lower(): b for b in PICK}
_brandof = lambda mk: _bk.get(mk.lower(), mk.title() if mk.isupper() else mk)
def _evyears(c):
    a, _, z = str(c['years']).partition('-'); return list(range(int(a), int(z or a) + 1))
# 11-12 (Priya: "your headline lemon 404s"): a scored model's live page. /cars/<id>/ only when it has model + year pages; a Tesla or
# another EV without them opens its /electric/ page; anything else gets no link ('') instead of a 404.
_CAR_PAGES = {f['id'] for f in _YJ if f['name'] in BYNAME}; _EV_PAGES = {c['slug'] for c in EVX}
def car_href(cid):
    return f'/cars/{cid}/' if cid in _CAR_PAGES else f'/electric/{cid}/' if cid in _EV_PAGES else ''
def perf_info(c):
    """A performance car's id, brand, page ('' until it has one) and the line its card leads with (hp, 0-60, else the engine)."""
    nm = c.get('name') or f"{c.get('make', '')} {c.get('model', '')}".strip(); mk = c.get('make') or c.get('brand') or nm.split(' ')[0]
    hp = c.get('hp'); z = c.get('zero60') or c.get('0-60') or c.get('zero_to_60'); eng = c.get('engine') or ''
    _pid = c.get('slug') or _slg(nm); _pd = _jl(f'data/perf/{_pid}.json') or {}   # 11-11: a car with a performance page (perf_page.py) is live, not coming soon
    if _pd and not hp:   # its card leads with the featured trim's sourced hp and 0-60 (magazine test, else the maker's figure)
        try:
            import perf_page as _PP; _g, _v = _PP._star(_pd); hp = _PP._hp(_v); _zz = _PP._z(_v.get('z60'))[0]; z = _zz.replace(' s', '') if _zz else z
        except Exception: pass
    lead = ' · '.join(x for x in ((f'{hp:,} hp' if isinstance(hp, (int, float)) else str(hp) + ' hp') if hp else '', f'0–60 {z} s' if z else '') if x) or eng
    return dict(id=_pid, name=nm, brand=_brandof(mk), url=c.get('url') or _pd.get('page') or '', lead=lead)
PICK_ALL = {b: [list(x) for x in m] for b, m in PICK.items()}
for c in SCX: PICK_ALL.setdefault(_brandof(c['make']), []).append([c['name'], _slg(c['name']), [y['y'] for y in c['years']], f"/supercars/{_slg(c['name'])}/", 'sc'])
for c in EVX:
    if c['slug'] not in YP: PICK_ALL.setdefault(_brandof(c['make']), []).append([c['name'], c['slug'], _evyears(c), f"/electric/{c['slug']}/", 'ev'])
for c in PERFX:
    i = perf_info(c); PICK_ALL.setdefault(i['brand'], []).append([c.get('search') or i['name'], i['id'], [], i['url'], 'perf'])   # 11-11: full name keeps the trim aliases searchable
for _m in (_jl('data/moto.json') or []): PICK_ALL.setdefault(_brandof(_m['brand']), []).append([_m['name'], 'moto-' + _slg(_m['name']), [], f"/motorcycles/{_slg(_m['name'])}/", 'moto'])   # 11-11: motorcycles in the one search
for _m in (_jl('data/moto_soon.json') or []): PICK_ALL.setdefault(_brandof(_m['make']), []).append([_m.get('search') or _m['name'], 'moto-' + _m['slug'], [], '', 'moto'])
PICK_ALL = dict(sorted((b, sorted(m)) for b, m in PICK_ALL.items()))
def finder(h='Look up any car', sub='Every model year, 2000 to 2025. Free.', foot=''):
    """10-29 (Elijah): the first thing on the page is an easy car filter. Type "2016 pilot", or pick brand, model, year (assets/lookup.js)."""
    pick = json.dumps(PICK_ALL, ensure_ascii=False).replace('</', '<\\/')   # 11-11: supercars, EVs and performance cars too
    return f"""<section class="finder" aria-labelledby="fh"><h1 id="fh">{h}</h1><p class="lede">{sub}</p>
<div class="fq"><input id="fq" type="search" placeholder="e.g. 2016 Honda Pilot" autocomplete="off" aria-label="Type a car"><div id="fsug" class="fsug" role="listbox" hidden></div></div>
<form class="look" id="look"><select id="lb" aria-label="Brand"><option value="">Brand</option></select><select id="lm" aria-label="Model" disabled><option value="">Model</option></select><select id="ly" aria-label="Year" disabled><option value="">Year</option></select><button type="button" class="btn" id="lgo" disabled>Show problems</button></form>
{foot}<script id="pick" type="application/json" data-find="/assets/find.json?v={TODAY}">{pick}</script></section>"""   # 11-11: data-find = the full search index (find_index.py)
BEST = [(n, v, sold or (f"{BYNAME[n]['sold'] / 1e6:.2f}M" if n in BYNAME else '')) for n, v, sold in BEST]   # fills the E-Class's missing sales

# 10-24: every list is rebuilt from the data (the 10-24 sales-timing fix moved some numbers; hand-typed lists drifted).
star = lambda c: c['name'] + ('*' if c['est'] else '')
BEST = [(star(c), c['li'], f"{c['sold'] / 1e6:.2f}M") for c in CARS[:10]]
WORST = [(star(c), c['li'], ', '.join(f'{p} {k}%' for p, k in c['issues'][:2])) for c in CARS[::-1][:10]]
BRANDS = [(r['brand'] + ('*' if r['brand'] in ('Porsche', 'Tesla') else ''), int(r['lemon_index'])) for r in sorted(csv.DictReader(open('data/brand_rates.csv', encoding='utf-8')), key=lambda r: int(r['lemon_index']))]
SEGMENTS = [(SEGN[k] + 's', ' · '.join(f"{c['name']} {c['li']}" for c in [c for c in CARS if c['seg'] == k][:3]), ' · '.join(f"{c['name']} {c['li']}" for c in [c for c in CARS if c['seg'] == k][::-1][:3])) for k in ('car', 'suv', 'truck', 'minivan')]
TOP, BR = CARS[0], dict((b.rstrip('*'), v) for b, v in BRANDS)
# 11-12 dead links: brands_pages.py builds a page only for the scored brands with a ranked model; others (Buick, Volvo, Mini...) stay plain text
_BRAND_PG = {b for b, m in PICK_ALL.items() if any(len(x) < 5 or x[4] != 'moto' for x in m)} - {'Pontiac'}   # 11-13 (nav #5): every make has a brand page now
BRAND_A = lambda b: f'<a href="/brands/{b.lower().replace(" ", "-")}/">{E(b)}</a>' if b in _BRAND_PG else E(b)
FAQ[1] = ('What is the most reliable car by owner complaints?', f"The {TOP['name']}, with a Lemon Index of {TOP['li']}: about a quarter of the complaints of the average car, across {TOP['sold'] / 1e6:.2f} million sold (model years 2010-2022).")
FAQ[2] = ('Which car brand has the fewest complaints?', f"Lexus, at {BR['Lexus']}, followed by Porsche ({BR['Porsche']}, small sample), Toyota ({BR['Toyota']}), BMW ({BR['BMW']}) and Mercedes-Benz ({BR['Mercedes-Benz']}).")

# 11-12 round 2 (Carlos, Spanish-first: "1.9x fewer", "5x fewer" read as math homework): plain fractions instead of "N× fewer"
def _frac(v):
    """a Lemon Index as words: 'about half as many complaints' / 'about twice the complaints' (None = about average)"""
    f = v / 100
    if 0.9 <= f <= 1.1: return None
    if f < 1:
        for hi, w in ((0.15, 'less than a sixth as many'), (0.22, 'about a fifth as many'), (0.29, 'about a quarter as many'), (0.37, 'about a third as many'),
                      (0.45, 'a bit under half as many'), (0.56, 'about half as many'), (0.63, 'a bit over half as many'), (0.71, 'about two-thirds as many'),
                      (0.8, 'about three-quarters as many'), (0.9, 'a few less')):
            if f < hi: return w
    if f < 1.35: return 'a bit more than'
    if f < 1.75: return 'about one and a half times'
    if f < 2.5: return 'about twice'
    return f'about {int(f + 0.5)} times'
def plain(v):
    """A Lemon Index in plain words, next to every number (10-22: bare scores confused people)."""
    w = _frac(v)
    if w is None: return 'about average'
    if v < 90: return f'{w} complaints as the average car' if w != 'a few less' else 'somewhat fewer complaints than the average car'
    return f"{w} the average car's complaints"

def short(v):
    """Short form for the bar charts, where the full sentence gets cut off."""
    w = _frac(v)
    if w is None: return 'about average'
    if v < 90: return f'{w} complaints'.replace('a few less complaints', 'somewhat fewer complaints')
    return f'{w} the complaints'.replace('a bit more than the complaints', 'a bit more complaints')

def explorer():
    for c in CARS: ph = YSL.model_img(c['id']) or mphoto(c['id']); c['img'] = rsmall(ph['src']) if ph else ''   # 11-03 v6: a photo on every row
    data = json.dumps(CARS, ensure_ascii=False).replace('</', '<\\/')
    _t = lambda v: 'bad' if v > 110 else 'good' if v < 90 else 'mid'
    seed = ''.join(f'<div class="xcd"><div class="xcm"><span class="xci">' + (f'<img src="{c["img"]}" alt="" width="1000" height="600" loading="lazy" decoding="async">' if c['img'] else '')
                   + f'</span><span class="xct"><small class="xck">#{c["rank"]}</small><b class="xcn">{E(c["name"])}{"*" if c["est"] else ""}</b><small class="xcs">{c["segName"]} · {c["years"].replace("-", "–")}</small>'
                   f'<span class="xcw {_t(c["li"])}">{E(plain(c["li"]))}</span></span><span class="xcv {_t(c["li"])}">{c["li"]}</span></div></div>' for c in CARS[:15])
    tabs = ''.join(f'<button type="button" data-seg="{k}" aria-pressed="{str(k == "all").lower()}">{l}</button>' for k, l in [('all', 'All'), ('car', 'Cars'), ('suv', 'SUVs'), ('truck', 'Trucks'), ('minivan', 'Minivans')])
    return f'''<section class="ex" id="explore" aria-labelledby="ex-h"><div class="exh"><div><h2 id="ex-h">Every model, ranked. <span class="h2s">Tap one for every year.</span></h2></div></div>
<div class="exbar"><input id="xq" type="search" placeholder="Search a model, e.g. RAV4" aria-label="Search a model"><div class="tabs" role="group" aria-label="Type">{tabs}</div>
<select id="xbrand" aria-label="Brand"></select><select id="xsort" aria-label="Sort"><option value="best">Most reliable first</option><option value="worst">Least reliable first</option><option value="sold">Most sold</option><option value="az">A to Z</option></select><span id="xcount" class="xcount"></span></div>
<div id="xrows" class="xrows xgrid">{seed}</div><button type="button" id="xmore" class="btn ghost xmore">Show all</button>
<p class="note">* Tesla doesn't publish U.S. sales by model, so its numbers use published estimates. Sold = U.S. sales over the model years shown.</p>
<div id="tray" class="tray" hidden></div><script id="cars" type="application/json">{data}</script></section>'''

def share_btn(text, label='Share ↗'):
    """11-09 'send this to a friend' button (assets/share.js; native share sheet on phones, panel elsewhere)."""
    return f'<button type="button" class="btn btn-ghost" data-share="{E(text)}">{label}</button>'
def share_line(text, ask='Know someone shopping for a used car?', label='Send them this ↗'):
    return f'<p class="shline">{ask} <button type="button" class="shl" data-share="{E(text)}">{label}</button></p>'
NOFB = ('/vote/', '/terms/', '/privacy/', '/refunds/', '/contact/', '/thanks/')   # legal pages and pages that are already a form
def feedback_html(q, placeholder='', note=''):
    """11-09 feedback box above the footer (assets/feedback.js -> lemon-survey Worker /feedback). Same markup on all 4 sites."""
    return (f'<section class="fb" aria-labelledby="fb-h"><form class="fb-f" novalidate><h2 id="fb-h">{q}</h2><div class="fb-in">'
            f'<label class="fb-l" for="fb-m">Your message</label><textarea id="fb-m" name="message" rows="4" maxlength="1000" required placeholder="{E(placeholder)}"></textarea>{note}'
            '<label class="fb-l" for="fb-e">Email (optional, only if you want a reply)</label><input id="fb-e" name="email" type="email" maxlength="200" autocomplete="email">'
            '<div class="fb-hpw" aria-hidden="true"><label for="fb-w">Leave this empty</label><input id="fb-w" class="fb-hp" name="website" tabindex="-1" autocomplete="off"></div>'
            '<button class="fb-go" type="submit">Send</button></div><p class="fb-st" role="status" aria-live="polite" tabindex="-1"></p></form></section>')
def end_block(path, upd, shl):
    """11-10 desktop pass (Elijah: the share line, Updated, the credit line and the footer were 4 separately centered bits): one end-of-page
    block in the content column: the share line on the left, Updated + credit as one small line under it."""
    meta = ' · '.join(x for x in (upd, 'Free to use with credit: <q>Source: The Lemon Index (lemonindex.com)</q>. <a href="/data/">Get the data</a>' if path.startswith(('/cars/', '/stats/', '/best', '/electric/', '/engines/', '/check-engine-light/')) else '') if x)
    if not (shl or meta): return ''
    return f'<div class="pend">{shl.replace("<p class=" + chr(34) + "shline" + chr(34), "<p class=" + chr(34) + "shline pend-s" + chr(34), 1)}' + (f'<p class="pend-m">{meta}</p>' if meta else '') + '</div>'
def ask_html(path):
    """Bottom of every page: 11-09 the one-tap survey (survey.js) is gone (Elijah: "remove the bottom questions and instead just have a feedback box")."""
    fb = '' if path in NOFB else feedback_html('How can we make Lemon Index better?', 'A car we should add, something confusing, a mistake you spotted…')
    if fb: fb = f'<details class="fbx"><summary>Spot a mistake or have an idea? Tell us</summary>{fb}</details>'   # 11-10 desktop pass: folded on every page
    return ((fb + '<script src="/assets/feedback.js?v=1109" defer></script>' if fb else '')
            + '<script src="/assets/share.js?v=1112d" defer></script><script src="/assets/bars3d.js?v=1103" defer></script><script src="/assets/loan.js?v=1103" defer></script>')
def fit_title(t):
    if len(t) > 65 and t.endswith(' | The Lemon Index'): t = t[:-len(' | The Lemon Index')] + ' | Lemon Index'
    if len(t) > 65 and t.endswith(' | Lemon Index'): t = t[:-len(' | Lemon Index')]
    if len(t) > 65 and ': Which Has Fewer Problems?' in t: t = t.replace(': Which Has Fewer Problems?', ' by Year') if len(t) - 19 <= 65 else t.replace(': Which Has Fewer Problems?', '').replace(' Reliability: Problems, Recalls and Range', ' Reliability, Recalls & Range')
    if len(t) > 65: t = t.replace(': Years to Avoid & Best to Buy', ': Best & Worst Years')
    return t.replace(' Problems and Recalls', ' Problems & Recalls') if len(t) > 65 else t
def fit_desc(d):
    if len(d) <= 160: return d
    d = d.replace(' Real owner complaints and every other year.', '')
    if len(d) <= 160: return d
    k = d.rfind('. ', 0, 159)
    return d[:k + 1] if k > 100 else d[:157].rsplit(' ', 1)[0] + '…'
# top navigation (11-03, Elijah: "make mobile navigation on top better"): one row on desktop; on phones a swipeable chip row under the
# logo (assets/nav.js keeps the current page's chip in view and tucks the header away while scrolling down)
NAV = [('/cars/', 'Look up a car'), ('/brands/', 'Brands'), ('/compare/', 'Compare'), ('/electric/', 'Electric'), ('/motorcycles/', 'Motorcycles'), ('/planes/', 'Planes'), ('/supercars/', 'Supercars'), ('/vin/', 'VIN check'),
       ('/car-loan-rates/', 'Loan rates'), ('/studies/', 'Studies'), ('/data/', 'Free data'), ('/method/', 'How it works')]
# header v7 (11-05, Elijah: "headers look AI-made, look at Stripe and Apple"): Apple-thin bar, 7 plain links + More flyout, one small CTA pill;
# phones get a full-screen menu. Styles/JS: assets/gh.css + gh.js (master copy in 0 HQ/Tools/site header/).
# 11-13 (nav review #6): Trucks (the /cars/ grid's Trucks tab) in the bar; Studies and Motorcycles moved to More, Engines up from More
NAV_TOP = [('/cars/', 'Cars'), ('/?type=trucks', 'Trucks'), ('/brands/', 'Brands'), ('/compare/', 'Compare'), ('/electric/', 'Electric'), ('/engines/', 'Engines'), ('/vin/', 'VIN check')]
NAV_MORE = [('/best/', 'Best cars'), ('/rankings/', 'Every car ranked'), ('/stats/car-complaints/', 'Statistics'), ('/supercars/', 'Supercars'), ('/motorcycles/', 'Motorcycles'), ('/studies/', 'Studies'), ('/check-engine-light/', 'Engine code lookup'), ('/best-gas-mileage/', 'Gas mileage'), ('/planes/', 'Planes'), ('/car-loan-rates/', 'Loan rates'), ('/vote/', 'Vote'), ('/data/', 'Free data'), ('/method/', 'How it works')]
GH_CHEV = '<svg viewBox="0 0 8 8" aria-hidden="true"><path d="M2.5 1 5.5 4 2.5 7" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
GH_DOWN = '<svg viewBox="0 0 8 8" aria-hidden="true"><path d="M1 2.75 4 5.75 7 2.75" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
# 11-10 v2 (Elijah: "it still can look a little better"): one small monochrome line icon per main menu item (24 px grid, stroke 1.8)
GH_IC = {'/cars/': '<path d="M4 16v-4l2.2-5h11.6L20 12v4z"/><path d="M4 12h16"/><circle cx="7.5" cy="16.5" r="1.6"/><circle cx="16.5" cy="16.5" r="1.6"/>',
         '/?type=trucks': '<path d="M3 16v-5h9V7h5l3 4v5z"/><path d="M12 11h8"/><circle cx="7" cy="16.5" r="1.6"/><circle cx="16.5" cy="16.5" r="1.6"/>',
         '/brands/': '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/>',
         '/compare/': '<path d="M8 20V9M16 20V4M4 20h16"/>',
         '/vin/': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 9v6M10 9v6M13.5 9v6M17 9v6"/>',
         '/check-engine-light/': '<path d="M4 10h2V8h5v2h3l2 2h2v-2h2v6h-2v-2h-2l-2 3H8l-2-2H4z"/>',
         '/engines/': '<path d="M6 9h9l2 2h2V9h2v7h-2v-2h-2l-2 3H8l-2-2z"/><path d="M9 9V6h4v3M3 12v3"/>',
         '/best/': '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
         '/electric/': '<path d="M13 3L5 13h6l-1 8 8-10h-6z"/>',
         '/motorcycles/': '<circle cx="6" cy="16" r="3"/><circle cx="18" cy="16" r="3"/><path d="M6 16l4-6h5l3 6M14 10l-1.5-3H10"/>',
         '/supercars/': '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4-5"/>',
         '/best-gas-mileage/': '<path d="M5 20V5a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v15M3 20h13M5 10h9M14 8l3 3v6a1.5 1.5 0 0 0 3 0V9l-3-3"/>',
         '/studies/': '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M10 12h5M10 16h5"/>',
         '/stats/car-complaints/': '<path d="M4 20V4M4 20h16"/><path d="M7 15l4-4 3 3 5-6"/>'}
# 11-11 (Elijah: one Cars section): the menu's Electric and Supercars open that tab of /cars/; /electric/ and /supercars/ stay as pages
# (they rank for their own searches) and keep their links from the footer and from the tabs
GH_HREF = {'/cars/': '/', '/electric/': '/?type=electric', '/supercars/': '/?type=supercars'}   # 11-11: the grid lives on / now
def gh_ic(u):
    return (f'<svg class="gh-ic" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{GH_IC[u]}</svg>'
            if u in GH_IC else '')
def gh_header(path):
    cur = lambda u: ' aria-current="page"' if path.startswith(u) else ''
    top = ''.join(f'<a href="{GH_HREF.get(u, u)}"{cur(u)}>{t}</a>' for u, t in NAV_TOP)
    # 11-10 (Elijah: the phone menu didn't fit one screen): grouped (Look up / Explore / More) in two columns on phones; headings and the
    # top-bar links (gh-x) only show where the top bar is folded away (<1024 px). Lemon-only: the styles live in site.css, not the shared gh.css.
    inbar = {u for u, _ in NAV_TOP}; lab = dict(NAV_TOP + NAV_MORE); lab['/check-engine-light/'] = 'Engine codes'
    grp = [('Look up', ['/cars/', '/?type=trucks', '/brands/', '/compare/', '/vin/', '/engines/', '/check-engine-light/']),
           ('Explore', ['/best/', '/rankings/', '/electric/', '/motorcycles/', '/supercars/', '/best-gas-mileage/', '/studies/', '/stats/car-complaints/']),
           ('More', ['/planes/', '/car-loan-rates/', '/vote/', '/data/', '/method/'])]
    assert sorted(u for _, us in grp for u in us) == sorted(lab), 'gh menu groups miss a link'
    sheet = ''.join(f'<span class="gh-g gh-g{i}" aria-hidden="true">{g}</span>' + ''.join(f'<a class="{"gh-x " if u in inbar else ""}gh-i{i}" href="{GH_HREF.get(u, u)}"{cur(u)}>{gh_ic(u)}<span>{lab[u]}</span></a>' for u in us)
                    for i, (g, us) in enumerate(grp))
    return (f'<header class="gh wide" data-tuck><div class="gh-in"><a class="gh-brand" href="/"><img src="/assets/icon-64.png" alt="" width="24" height="24">The Lemon Index</a>'
            f'<nav class="gh-links" aria-label="Main">{top}<button class="gh-more" type="button" aria-expanded="false" aria-controls="gh-sheet">More{GH_DOWN}</button></nav>'
            f'<div class="gh-r">{GH_SD}{GH_SB}<a class="gh-cta" href="{YT}?sub_confirmation=1" rel="noopener">Subscribe{GH_CHEV}</a>'
            f'<button class="gh-menu" type="button" aria-label="Menu" aria-expanded="false" aria-controls="gh-sheet"><i></i><i></i></button></div></div>'
            f'<div class="gh-dim" aria-hidden="true"></div><nav class="gh-sheet" id="gh-sheet" aria-label="All pages"><div class="gh-sheet-in"><p>More from the Lemon Index</p>{GH_SEARCH}{sheet}</div></nav></header>')
# 11-12 (Jess: "no search in the menu"): one search box at the top of the menu on every page; the same search as the home finder
# (assets/lookup.js: cars, years, engine codes, problem words and questions). Without JS it opens the home finder with ?q=.
GH_SEARCH = ('<form class="gh-q" role="search" action="/" method="get"><div class="gh-qb"><input id="ghq" name="q" type="search" autocomplete="off" '
             'placeholder="Search a car, code or question" aria-label="Search cars, engine codes and lists" enterkeyhint="search">'
             '<div id="ghqs" class="fsug" role="listbox" hidden></div></div></form>')
# 11-13 navigation test (problem 1, "search is hidden on every non-home page"): a magnifier in the bar on every page (opens the menu with
# the search box focused) and, from 1024px, an inline search box in the bar. Same search (lookup.js attaches #ghd too). Styles: assets/lxs.css
_LXS_IC = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>'
GH_SB = f'<button class="lxs-btn" type="button" aria-label="Search" aria-controls="gh-sheet">{_LXS_IC}</button>'
GH_SD = (f'<form class="lxs-d" role="search" action="/" method="get"><div class="lxs-db">{_LXS_IC.replace("<svg ", "<svg class=\"lxs-di\" ", 1)}'
         '<input id="ghd" name="q" type="search" autocomplete="off" placeholder="Search cars, codes, lists" aria-label="Search cars, engine codes and lists" enterkeyhint="search">'
         '<div id="ghds" class="fsug" role="listbox" hidden></div></div></form>')
LXS_V = '1113b'   # lxs.css + lookup.js version (N1 navigation fixes)
GH_IC.setdefault('/rankings/', '<path d="M4 6h16M4 12h11M4 18h6"/>')   # 11-13 (N1, problem 12): "Every car ranked" in the menu, best to worst bars
def navlinks(path):
    on = lambda u: path.startswith(u) or (u == '/cars/' and path.startswith('/cars'))
    return ''.join(f'<a href="{u}"{" class=on aria-current=page" if on(u) else ""}>{t}</a>' for u, t in NAV)
# free-data credit line under every car page (11-03): the data is CC BY 4.0, so copying it is fine as long as it credits us (see /data/)
CITE = '<p class="cite">Free to use with credit: <q>Source: The Lemon Index (lemonindex.com)</q>. <a href="/data/">Get the data</a></p>'
_AH = re.compile(r'<article class="study([^"]*)"><p class="kicker">(.*?)</p>\s*<h1>(.*?)</h1>\s*(?:<p class="lede">(.*?)</p>)?', re.S)
_TBL = re.compile(r'<table(?:\s[^>]*)?>.*?</table>', re.S)
def stack_tables(body):
    """11-10 (design audit: tables cut off on phones): every table with 4+ columns gets class "stk" and a data-label on each cell (its
    column header), so site.css can show each row as a small stacked card under 600 px. Narrower tables just fit the screen."""
    def one(m):
        t = m.group(0)
        if ' stk' in t[:200]: return t
        from bs4 import BeautifulSoup
        s = BeautifulSoup(t, 'html.parser'); tb = s.find('table'); rows = tb.find_all('tr')
        hr = next((r for r in rows if r.find('th') and not r.find('td')), None)
        if not hr: return t
        heads = [c.get_text(' ', strip=True) for c in hr.find_all(['th', 'td'])]
        if len(heads) < 4: return t
        for r in rows:
            if r is hr: continue
            for i, c in enumerate(r.find_all(['td', 'th'], recursive=False)):
                if i < len(heads) and heads[i]: c['data-label'] = heads[i]
        tb['class'] = (tb.get('class') or []) + ['stk']
        return str(s)
    return _TBL.sub(one, body)
def auto_hero(body, vis=''):
    """11-03 v6 for every remaining article page (studies, compare pairs, transmission, electric, legal): its kicker + h1 + lede become the
    centered photo hero the other pages have, and the article sits under it with the v6 spacing."""
    m = _AH.search(body)
    if not m: return body
    h1 = m.group(3).strip(); h1 = h1 + '.' if h1[-1:].isalnum() else h1
    lede = f'<p class="ph-s">{m.group(4)}</p>' if m.group(4) else ''
    hero = f'<section class="ph ph-a"><p class="ph-e">{m.group(2)}</p><h1>{h1}</h1>{lede}' + ('<div class="ph-v">' + vis.replace(' loading="lazy"', '') + '</div>' if vis else '') + '</section>'
    body = body[:m.start()] + '<div class="pg">' + hero + f'<article class="study{m.group(1)}">' + body[m.end():]
    i = body.rfind('</article>'); return body[:i] + '</article></div>' + body[i + len('</article>'):]
# 11-05 schema: breadcrumbs on every page (Home > Cars > Honda Civic > 2016) so Google and AI tools see where a page sits
SEGN = {'cars': 'Cars', 'brands': 'Brands', 'compare': 'Compare', 'electric': 'Electric', 'motorcycles': 'Motorcycles', 'planes': 'Planes', 'supercars': 'Supercars',
        'vin': 'VIN decoder', 'car-loan-rates': 'Car loan rates', 'studies': 'Studies', 'data': 'Free data', 'method': 'How it works', 'transmission': 'Transmission problems'}
def crumbs(path, title):
    parts = [x for x in path.strip('/').split('/') if x]; items = [('The Lemon Index', BASE + '/')]; FY = globals().get('FY', {})
    for j in range(len(parts) - 1, 0, -1):   # 11-13 (N1): a slash id ('mercedes-benz-m/gle', 'glk/glc') is one crumb, not a dead /cars/mercedes-benz-m/
        if parts[j - 1] + '/' + parts[j] in FY: parts[j - 1:j + 1] = [parts[j - 1] + '/' + parts[j]]
    for i, x in enumerate(parts):
        u = BASE + '/' + '/'.join(parts[:i + 1]) + '/'
        nm = SEGN.get(x) or (FY[x]['name'] if x in FY else x if x.isdigit() else x.replace('-', ' ').title())
        if i == len(parts) - 1 and not x.isdigit() and x not in SEGN and x not in FY: nm = title.split(' | ')[0].split(':')[0]
        items.append((nm, u))
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}
def car_ld(f, y=None, mpg=None, img=None):
    c = BYNAME.get(f['name']) or {}; brand = c.get('brand') or f['name'].split()[0]
    d = {"@context": "https://schema.org", "@type": "Car", "name": (f'{y} ' if y else '') + f['name'], "brand": {"@type": "Brand", "name": brand},
         "model": f['name'][len(brand):].strip() or f['name'], "url": BASE + (CARU(f, y) if y else CARU(f))}
    if y: d["vehicleModelDate"] = str(y)
    if mpg and not mpg.get('ev') and mpg.get('comb'): d["fuelEfficiency"] = {"@type": "QuantitativeValue", "value": mpg['comb'][1], "unitText": "MPG combined (EPA)"}
    if img: d["image"] = BASE + img
    return d
PD = json.load(open('data/page_dates.json', encoding='utf-8')) if os.path.exists('data/page_dates.json') else {}
# 11-12 search titles. title_overrides.json: {path: {title, query, ...}} written weekly by 0 HQ/Tools/gsc_titles.py (a Search Console
# query at position 4-20 put first in the title; reverted automatically if the page does clearly worse after 28 days).
# search_names.json: the spelling people search ("Mercedes C-Class"), and per model whether "<year> <model> problems" or
# "... reliability" is searched more (Keyword Planner + Search Console; `gsc_titles.py names` regenerates it).
TOV = json.load(open('data/title_overrides.json', encoding='utf-8')).get('pages', {}) if os.path.exists('data/title_overrides.json') else {}
_SNJ = json.load(open('data/search_names.json', encoding='utf-8')) if os.path.exists('data/search_names.json') else {}
_MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# 11-11 (Elijah: "above the top header might be better"): the phone donate bar sits at the very top, above the header, and scrolls away with
# the page while the header pins as usual. In the HTML (no layout jump); DB_JS hides it before paint for 7 days after x, 60 after a donation.
DONBAR = ('<div class="donbar" role="region" aria-label="Support the Lemon Index"><button type="button" class="donbar-go">Keep Lemon free &amp; ad-free · '
          '<b>Donate&nbsp;›</b></button><button type="button" class="donbar-x" aria-label="Close the donate bar">×</button></div>')
DB_JS = "try{var n=Date.now(),g=function(k){return +localStorage.getItem(k)||0};if(n-g('li-donbar-x')<6048e5||n-g('li-support-paid')<5184e6)document.documentElement.className+=' db-off'}catch(e){}"
import base64 as _b64
DB_HASH = 'sha256-' + _b64.b64encode(hashlib.sha256(DB_JS.encode('utf-8')).digest()).decode()
# 11-12 (Marcus: "Iâm"): some NHTSA complaint texts lost the middle bytes of a curly quote (UTF-8 ’ read as Latin-1, then the
# unprintable bytes dropped), leaving a lone "â". Repaired on every page before it's written, with patterns narrow enough that a real "â"
# (Château, São) is left alone.
_MJ = [(re.compile('â�'), '”'), (re.compile('â(?:\u0080\u0099|€™)'), '’'), (re.compile('â(?:\u0080\u009c|€œ)'), '“'),
       (re.compile('â(?:\u0080\u009d|€\u009d)'), '”'), (re.compile('â¢'), '•'), (re.compile('â¦'), '…'),
       (re.compile(r"(?<=[A-Za-z])â(?=(?:s|t|m|d|ll|re|ve)\b)"), '’'), (re.compile(r"(?<=[\s>(\"])â(?=[A-Za-z])"), '“'),
       (re.compile(r"(?<=[A-Za-z.,!?])â(?=[\s<,.)])"), '”')]
def fix_moji(t):
    if 'â' not in t: return t
    for rx, to in _MJ: t = rx.sub(to, t)
    return t
# 11-12 accurate freshness (research #5): a page's date (sitemap <lastmod>, "Updated", dateModified) moves only when its content hash
# changes. The hash skips what changes on every build without the page changing: numbered element ids (ii5101 -> ii5102 when another page
# gains an info button), ?v= asset versions and today's date. page_dates.json: {path: {c: hash, d: date, f: [complaints, recalls,
# investigations] on car pages, u/ud: the "N new recalls" note and its date}}. Pages whose date moved this build -> PD_NEW (IndexNow list).
_VOLX = re.compile(r'\b((?:id|for|aria-controls|aria-labelledby|aria-describedby|data-i)=")([a-z]{1,4})\d+"|\?v=[\w.-]+')
PD_NEW = []
LG = {}; _LGHREF = re.compile(r'<a\b[^>]*?\shref="(/[^"#?]*)'); _LGNOIX = re.compile(r'<meta name="robots" content="[^"]*noindex')
def _chash(body):
    t = _VOLX.sub(lambda m: f'{m.group(1)}{m.group(2)}#"' if m.group(1) else '?v=', body).replace(TODAY, '')
    return hashlib.md5(t.encode('utf-8')).hexdigest()[:10]
def _car_facts(path):
    """[complaints counted, recalls, investigations] for a /cars/ model or model-year page from the site's data, else None"""
    m = re.match(r'^/cars/(.+?)/(?:(\d{4})/)?$', path); FY_ = globals().get('FY', {})
    if not m or m.group(1) not in FY_ or 'X2' not in globals(): return None
    fid = m.group(1); ys = [int(m.group(2))] if m.group(2) else [v['y'] for v in FY_[fid]['years']]
    vs = {v['y']: v for v in FY_[fid]['years']}
    XL_ = globals().get('XL', {}); cn = lambda y: sum(n for *_, n in (XL_.get(fid, {}).get(str(y)) or {}).get('names', [])) or (vs[y].get('n') or 0)   # every complaint the site holds for that year (extras_local), else the study count
    return [sum(cn(y) for y in ys if y in vs), len({r.get('id') or r.get('summary', '')[:80] for y in ys for r in (extra(fid, y).get('recalls') or [])}),
            len({i.get('id') for y in ys for i in (X2.get(fid, {}).get(str(y), {}).get('inv') or [])})]
def _pd_mark(path, body, head=''):
    # 11-12 search titles: `head` = the <title> + meta description. A title change is a real content change (new date + IndexNow);
    # 't' is its hash and 'td' the day the title/description last changed (gsc_titles.py never re-touches a page within 28 days of it).
    c = _chash(body); e = PD.get(path); fx = _car_facts(path); t = hashlib.md5(head.encode('utf-8')).hexdigest()[:8] if head else None
    if e is None: PD[path] = e = {'c': c, 'd': TODAY}; PD_NEW.append(path)
    elif 'c' not in e: e['c'] = c; e.pop('h', None)   # first build with content hashes: keep the page's date
    elif e['c'] != c or (t and e.get('t') and e['t'] != t):
        e['c'] = c; e['d'] = TODAY; PD_NEW.append(path)
        if fx and e.get('f'):
            dl = [(a - b, w) for a, b, w in zip(fx, e['f'], ('complaint', 'recall', 'investigation')) if a > b]
            if dl: e['u'] = ', '.join(f'{n:,} new {w}{"s" * (n != 1)}' for n, w in dl); e['ud'] = TODAY
    if t:
        if e.get('t') and e['t'] != t: e['td'] = TODAY
        e['t'] = t   # first build with title hashes: recorded without moving the date
    if fx: e['f'] = fx
def page(path, title, desc, body, ld=None, kind='website', img=None, ask=None, vis='', canon=None):
    if TOV.get(path, {}).get('title'): title = TOV[path]['title']   # 11-12: search-title test from 0 HQ/Tools/gsc_titles.py (data/title_overrides.json)
    title, desc = fit_title(title), fit_desc(desc)
    body, desc = fix_moji(body), fix_moji(desc)
    _tm = re.match(r'^/cars/(.+?)/(?:(\d{4})/)?$', path)   # lazy, so slash ids ('mercedes-benz-glk/glc') match too
    if _tm and (_tm.group(1) in TAB.ON or _tm.group(1) in globals().get('FY', {})) and 'tab_body' in globals(): body = tab_body(_tm.group(1), int(_tm.group(2)) if _tm.group(2) else None, body)
    if 'class="advp"' in body and path.startswith(('/cars/', '/motorcycles/', '/planes/')) and 'adv_body' in globals(): body = adv_body(path, body)   # 11-10: the other template
    if 'class="pg mp6"' in body and re.match(r'^/(motorcycles|supercars|planes)/[^/]+/$', path) and 'adv_body' in globals(): body = adv_body(path, body, TAB.transform_mp6)   # 11-10: motorcycle, supercar and plane pages
    _pd_mark(path, body, title + '\n' + desc)
    _d = PD[path]['d']; _dl = f'{_MN[int(_d[5:7]) - 1]} {int(_d[8:])}, {_d[:4]}'; _upd = ''
    if path.startswith(('/cars/', '/motorcycles/', '/planes/', '/supercars/', '/best/', '/stats/', '/check-engine-light/', '/best-gas-mileage/', '/electric/', '/studies/')):
        _un = PD[path].get('u') if PD[path].get('ud') == _d else None   # "Updated Nov 12: 1 new recall" only while that data change is the page's latest change
        _upd = f'Updated <time datetime="{_d}">{_dl}</time>' + (f': {E(_un)}' if _un else ''); ld = list(ld or []) + [{"@context": "https://schema.org", "@type": "WebPage", "url": BASE + path, "name": title, "dateModified": _d}]
    body = auto_hero(body, vis)
    if '<table' in body: body = stack_tables(body)   # 11-10: wide tables become stacked rows on phones (site.css .stk)
    if re.fullmatch(r'/cars/[^/]+/', path) and 'SEARCH_MINI' in globals(): body += SEARCH_MINI + CODES_JS   # 11-10: engine code lookup on model pages (added after the date hash, so dates don't move)
    _lxm = re.fullmatch(r'/cars/(.+?)/(\d{4})/', path)
    if _lxm and 'LX_HTML' in globals(): body += LX_HTML(_lxm.group(1), int(_lxm.group(2)))   # 11-12 related links (after the date hash too)
    _shl = ''
    _sm = list(re.finditer(r'<p class="shline">.*?</p>', body, re.S))
    if _sm: _shl = _sm[-1].group(0); body = body[:_sm[-1].start()] + body[_sm[-1].end():]
    url = BASE + (canon or path); ld = list(ld or []) + [crumbs(path, title)]
    lds = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    beacon = f"<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{{\"token\": \"{CF}\"}}'></script>" if CF else ''
    if GA: beacon += f'<script src="/assets/ga.js?v=3" data-ga="{GA}" defer></script>'
    if ADS and path not in ('/thanks/',): beacon += f'<script src="/assets/ads.js?v=1" data-ads="{ADS}" defer></script>'   # 11-09: ga.js loads gtag.js (180 KB) after the page has loaded
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><script>{DB_JS}</script><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="{kind}"><meta property="og:site_name" content="The Lemon Index"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}{img or "/assets/og.png"}"><meta name="twitter:card" content="summary_large_image">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' '{DB_HASH}' https://static.cloudflareinsights.com https://challenges.cloudflare.com https://www.googletagmanager.com https://*.googlesyndication.com https://*.doubleclick.net https://*.google.com https://*.googleadservices.com https://*.gstatic.com https://*.adtrafficquality.google https://*.googletagservices.com; frame-src https://challenges.cloudflare.com https://*.googlesyndication.com https://*.doubleclick.net https://*.google.com https://*.googleadservices.com https://*.gstatic.com https://*.adtrafficquality.google https://*.googletagservices.com; style-src 'self' 'unsafe-inline'; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://cloudflareinsights.com https://*.google-analytics.com https://*.analytics.google.com https://*.googletagmanager.com https://vpic.nhtsa.dot.gov https://api.nhtsa.gov https://lemon-survey.elift08.workers.dev https://*.googlesyndication.com https://*.doubleclick.net https://*.google.com https://*.googleadservices.com https://*.gstatic.com https://*.adtrafficquality.google https://*.googletagservices.com; object-src 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="google-adsense-account" content="{ADS}"><meta name="msvalidate.01" content="2F84C8106BB577C5860ABE6EC15825EC"><link rel="icon" href="/assets/icon-64.png"><link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preload" href="/assets/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/lxs.css?v={LXS_V}">
<link rel="stylesheet" href="/assets/site.css?v=1112-r2d-hd1"><link rel="stylesheet" href="/assets/gh.css?v=2"><script src="/assets/gh.js?v=2" defer></script><script src="/assets/nav.js?v=1105" defer></script>{lds}</head>
<body>{'' if path.startswith('/thanks/') else DONBAR}{gh_header(path)}
<main>{body}{end_block(path, _upd, _shl)}{'' if path == '/vote/' else ask_html(path)}</main>
<footer class="foot f2"><div class="f2-in"><div class="f2-brand"><a class="f2-logo" href="/"><img src="/assets/icon-64.png" alt="" width="28" height="28">The Lemon Index</a>
<p>Car reliability from owner complaints to the U.S. government, per car sold. Free.</p><div class="f2-soc">{F2_SOC}</div></div>
<nav class="f2-col" aria-label="Explore"><p class="f2-h">Explore</p><a href="/compare/">Compare cars</a><a href="/best/">Best cars</a><a href="/rankings/">Every car ranked</a><a href="/brands/">Brands</a><a href="/engines/">Every engine</a><a href="/electric/">Electric cars</a><a href="/stats/car-complaints/">Statistics</a><a href="/car-loan-rates/">Car loan rates</a></nav>
<nav class="f2-col" aria-label="Tools and data"><p class="f2-h">Tools and data</p><a href="/vin/">VIN check</a><a href="/check-engine-light/">Engine codes</a><a href="/method/">How the index works</a><a href="/data/">Free data</a><a href="/images/">Free images</a><a href="/vote/">Vote</a></nav>
<nav class="f2-col" aria-label="Support"><p class="f2-h">Support</p><button class="supl" type="button">Keep Lemon ad-free</button><a href="/about/">About</a><a href="/press/">Press</a><a href="/contact/">Contact</a><a href="{YT}?sub_confirmation=1" rel="noopener">Subscribe on YouTube</a></nav></div>
<div class="f2-bot"><span>© {TODAY[:4]} The Lemon Index</span><a href="/terms/">Terms</a><a href="/privacy/">Privacy</a><a href="/refunds/">Refunds</a><span class="f2-dis">Built from public NHTSA complaint data and published U.S. sales figures. Not affiliated with any automaker. Not a repair-cost or safety rating.</span></div></footer><script src="/assets/explorer.js?v=1112d" defer></script><script src="/assets/support.js?v=1111d" defer></script><script src="/assets/imginfo.js?v=2" defer></script><script src="/assets/lookup.js?v={LXS_V}" defer></script>{beacon}</body></html>'''
    LG[path] = (set(_LGHREF.findall(doc)), bool(_LGNOIX.search(doc)), url)   # 11-12 link graph (linkgraph.py, end of build)
    f = os.path.join(OUT, path.strip('/'), 'index.html') if path.endswith('/') else os.path.join(OUT, path.strip('/'))
    os.makedirs(os.path.dirname(f), exist_ok=True)
    for _try in range(6):   # 11-09: Windows sometimes holds a just-written file for a moment (antivirus/indexer): retry instead of dying mid-build
        try: open(f, 'w', encoding='utf-8').write(doc); break
        except OSError:   # 11-10: Errno 22 (Invalid argument) is the same transient lock
            if _try == 5: raise
            import time; time.sleep(.5)
    LG[path] += (os.path.getmtime(f),)   # linkgraph re-reads only pages something rewrote after this

def bars(rows, mx, cls=''):
    tip = lambda n, v: f'{n}: Lemon Index {v}, {plain(v)}.'
    return (f'<div class="bars {cls}"><div class="bl" aria-hidden="true"><span></span><span class="al" style="--a:{100 / mx * 100:.1f}%">average car = 100</span><span></span></div>'
            + ''.join(f'<div class="b {"bad" if v > 110 else "good"}" data-tip="{E(tip(n, v))}"><span class="bn">{E(n)}</span><span class="bt"><i style="width:{min(100, v / mx * 100):.1f}%"></i><em style="left:{100 / mx * 100:.1f}%"></em></span><b>{v}</b><small>{short(v)}</small></div>' for n, v in rows) + '</div>')

STUDY = '/studies/most-reliable-cars/'
best_rows = ''.join(f'<tr><td>{i}</td><td>{E(n)}</td><td class="num good">{v}</td><td class="pw">{plain(v)}</td><td class="num">{E(s) or "—"}</td></tr>' for i, (n, v, s) in enumerate(BEST, 1))
worst_rows = ''.join(f'<tr><td>{E(n)}</td><td class="num bad">{v}</td><td class="pw">{plain(v)}</td><td>{E(w)}</td></tr>' for n, v, w in WORST)
seg_rows = ''.join(f'<tr><td><b>{E(a)}</b></td><td>{E(b)}</td><td>{E(c)}</td></tr>' for a, b, c in SEGMENTS)
faq = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in FAQ)
os.makedirs(OUT, exist_ok=True)

# ---- 11-03 redesign (Elijah: "why do Apple and Stripe look less AI-made... add all these things"): a signature score dial built from the
# logo's gauge, a hero with real car photos, a proof row and custom line icons. Yellow stays an accent (the dial's hub, the logo).
def gauge(li, size=220, label=True):
    """The Lemon gauge: a speedometer from 0 to 300 (100 = the average car); green below 85, gray around average, red above 115 (band()).
    label=True prints the plain caption; a string (11-12 r2: "2017 Lemon Index", "All years 2010-2022") says which score this is.
    The needle swings in when the dial scrolls into view (assets/nav.js adds .in). Scores past 300 peg the needle and still print the real number."""
    cx, cy, r = 120, 118, 92
    pt = lambda v, rr=r: (cx - rr * __import__('math').cos(__import__('math').pi * min(v, 300) / 300), cy - rr * __import__('math').sin(__import__('math').pi * min(v, 300) / 300))
    def arc(a, b, col):
        (x1, y1), (x2, y2) = pt(a), pt(b)
        return f'<path d="M{x1:.1f} {y1:.1f}A{r} {r} 0 0 1 {x2:.1f} {y2:.1f}" stroke="{col}" />'
    ticks = ''.join(f'<line x1="{pt(v, r - 16)[0]:.1f}" y1="{pt(v, r - 16)[1]:.1f}" x2="{pt(v, r - 24 if v % 100 else r - 30)[0]:.1f}" y2="{pt(v, r - 24 if v % 100 else r - 30)[1]:.1f}" />' for v in range(0, 301, 25))
    nums = ''.join(f'<text x="{pt(v, r - 44)[0]:.1f}" y="{pt(v, r - 44)[1] + 5:.1f}">{v}</text>' for v in (0, 100, 200, 300))
    a = min(li, 300) / 300 * 180 - 90
    cls = band(li)[0]   # 11-12 r2: the same bands as every verdict word (green under 85, gray 85-115, red over 115)
    return (f'<figure class="gauge {cls}" data-gauge style="--a:{a:.1f}deg;width:{size}px" aria-label="Lemon Index {li}: {E(plain(li))}">'
            f'<svg viewBox="0 0 240 150" role="img" aria-hidden="true"><g class="g-arc" fill="none" stroke-width="16" stroke-linecap="butt">{arc(0, 84, "#1a8f4c")}{arc(86, 114, "#c9ccd1")}{arc(116, 300, "#e8141c")}</g>'
            f'<g class="g-tick">{ticks}</g><g class="g-num">{nums}</g><g class="g-ndl"><path d="M{cx - 4} {cy}L{cx} {cy - r + 6}L{cx + 4} {cy}Z" /><circle cx="{cx}" cy="{cy}" r="11" /><circle class="g-hub" cx="{cx}" cy="{cy}" r="5" /></g></svg>'
            f'<figcaption><b>{li}</b>{(f"<span>{label} · 100 = average car</span>" if isinstance(label, str) else "<span>Lemon Index · 100 = average car</span>") if label else ""}</figcaption></figure>')

ICONS = {   # custom 24px line icons (stroke 1.8, round), drawn for the site 11-03
 'look': '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/><path d="M7.5 11.5l1-2.2h4l1 2.2v1.6h-6z"/><circle cx="8.6" cy="13.4" r=".6"/><circle cx="12.4" cy="13.4" r=".6"/>',
 'compare': '<rect x="3" y="9" width="6.5" height="11" rx="1.5"/><rect x="14.5" y="4" width="6.5" height="16" rx="1.5"/><path d="M6.2 5.5h4M17.8 1.8v0"/><path d="M8 5.5l2.2-2M8 5.5l2.2 2"/>',
 'vin': '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M6.5 9v6M9 9v6M11 9v6M14 9v6M16 9v6M17.8 9v6"/>',
 'loan': '<path d="M4 12.5 11.5 5H19v7.5L11.5 20z"/><circle cx="15.3" cy="8.7" r="1.3"/><path d="M8.6 14.6l3.6-3.6"/>',
 'vote': '<path d="M5 11h14l1.5 9h-17z"/><path d="M8 11V4.5h8V11"/><path d="M10.2 7.6l1.4 1.4 2.6-2.8"/>',
 'wrench': '<path d="M14.7 6.3a4 4 0 0 0 5 5L21 12.6l-1.6 1.6a4 4 0 0 1-5.2.5L7.3 21.6a2 2 0 0 1-2.9-2.9l6.9-6.9a4 4 0 0 1 .5-5.2L13.4 5z"/>',
 'warn': '<path d="M12 3.5 21.5 20h-19z"/><path d="M12 10v4.5M12 17.2v.3"/>',
 'up': '<path d="M4 17.5 10 11l3.5 3.5L20 8"/><path d="M15 8h5v5"/>',
 'doc': '<path d="M6.5 3h8l4 4v14h-12z"/><path d="M14.5 3v4h4M9.5 12h6M9.5 15.5h6"/>',
 'crash': '<path d="M3.5 16.5h11l-1.6-4.6H6.2z"/><circle cx="6.6" cy="17.6" r="1.6"/><circle cx="11.6" cy="17.6" r="1.6"/><path d="M17.5 3.5l.9 2.8 2.8-.9-1.8 2.3 1.9 2.1-2.9-.1-.4 2.9-1.4-2.6"/>',
 'injury': '<circle cx="12" cy="12" r="8.5"/><path d="M12 8v8M8 12h8"/>',
 'fire': '<path d="M12 21c-3.6 0-6-2.4-6-5.6 0-3.4 3-5.4 3.6-9.4 2.2 1.4 3.4 3.4 3.4 5.4 1-.6 1.6-1.6 1.8-2.8 1.8 1.6 3.2 4 3.2 6.6C18 18.6 15.6 21 12 21z"/>',
 'tow': '<path d="M2.5 16.5h11v-7h3.8l3.2 4.2v2.8h-2"/><circle cx="6.5" cy="17.2" r="1.7"/><circle cx="16.5" cy="17.2" r="1.7"/><path d="M2.5 12.5l4.5-6.5"/>',
 'data': '<ellipse cx="12" cy="5.5" rx="7.5" ry="2.8"/><path d="M4.5 5.5v6c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8v-6"/><path d="M4.5 11.5v6c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8v-6"/>',
}
icon = lambda k: f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">{ICONS[k]}</svg>'

_PH = json.load(open('data/photos.json', encoding='utf-8'))
MPH = json.load(open('data/model_photos.json', encoding='utf-8')) if os.path.exists('data/model_photos.json') else {}   # one checked photo per model (data_model_photos.py)
def mphoto(fid, year=None):
    """A model's photo: the exact year when we have it, else its newest checked year, else the model photo. {src, w, h, author}.
    11-10 (Elijah: "if a car has an AI image, don't show the Wikimedia one"): the model's AI illustration wins everywhere (author '', ai = name)."""
    m = YSL.model_img(fid)
    if m: return {'src': m['src'], 'w': m['w'], 'h': m['h'], 'author': '', 'ai': m['name']}
    ys = _PH.get(fid, {})
    if year and str(year) in ys: return ys[str(year)]
    if ys: return ys[max(ys)]
    return MPH.get(fid)
# 11-09 phone speed (Lighthouse mobile LCP 4-5 s): every local photo also ships as 400 and 800 px wide copies in assets/r/<w>/ (made here on
# first use), and each <img> gets srcset + sizes, so a phone downloads ~1/4 of the bytes. The sizes values are upper bounds of the width each
# slot is actually shown at (measured 300-1920 px), so no photo is ever shown blurrier than before.
RW, _RS = (400, 800), {}
def rsrc(src):
    """srcset for a local /assets/*.webp photo: its 400w/800w copies (made if missing or stale) + the original. '' for anything else."""
    if src in _RS: return _RS[src]
    p, out = (src or '').lstrip('/'), ''
    if p.startswith('assets/') and p.endswith('.webp') and os.path.exists(p):
        from PIL import Image
        im = Image.open(p); ow, parts = im.size[0], []
        for t in RW:
            if t > ow * .75: continue   # a copy under 25% narrower saves too little to be worth shipping
            q = 'assets/r/' + str(t) + p[len('assets'):]
            if not os.path.exists(q) or os.path.getmtime(q) < os.path.getmtime(p):
                os.makedirs(os.path.dirname(q), exist_ok=True); s = im if im.mode in ('RGB', 'RGBA') else im.convert('RGBA')
                s.resize((t, round(s.size[1] * t / s.size[0])), Image.LANCZOS).save(q, 'WEBP', quality=80, method=6)
            parts.append(f'/{q} {t}w')
        if parts: out = ', '.join(parts + [f'{src} {ow}w'])
    _RS[src] = out; return out
def rset(src, sizes): s = rsrc(src); return f' srcset="{s}" sizes="{sizes}"' if s else ''
def rsmall(src): s = rsrc(src); return s.split(' ')[0] if s else src   # the 400 px copy, for thumbnails (explorer rows are 60-76 px)
SZ_ONE, SZ_TWO = '(max-width: 600px) 95vw, 560px', '(max-width: 600px) 52vw, 400px'   # one photo in a slot / two or three side by side
def ai_note(what):
    """11-10: one small 'i' (image info) for a group of AI illustrations inside links, where a per-image button can't go."""
    return (f'<span class="iiw">' + YSL.info(f'Illustrations (AI-generated) of the {E(what)}, not photos of specific cars. Free to use under '
            f'<a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>').replace('<div class="ii-pop"', '<span class="ii-pop"').replace('</div>', '</span>') + '</span>')   # a span popup, so it can sit inside a <p> (a div there split the paragraph)
def aph(fid, y=None):
    """An AI illustration if the model has one, else the Commons photo."""
    m = YSL.model_img(fid)
    return {'src': m['src'], 'w': m['w'], 'h': m['h'], 'author': '', 'ai': m['name']} if m else mphoto(fid, y) if y else mphoto(fid)
def tiles():
    from PIL import Image
    yrs = {f['id']: f for f in _YJ}
    fid = lambda c: c['id']
    def img(ph, alt, cls=''):
        return f'<img class="{cls}" src="{ph["src"]}"{rset(ph["src"], SZ_TWO if cls else "(max-width: 600px) 88vw, 460px")} alt="{E(alt)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy">' if ph else ''
    who, ai = [], []
    def car_tile(c, eyebrow, cls):
        ph = aph(c['id']); ph and who.append(ph['author'].split('\ufffd')[0].strip()); ph and ph.get('ai') and ai.append(ph['ai'])
        return (f'<a class="tile {cls}" href="{car_href(c["id"]) or "/rankings/"}"><div class="tt"><p class="te">{eyebrow}</p><h2>{E(c["name"])}.</h2>'
                f'<p class="ts">{E(plain(c["li"]))}.</p><span class="tl">See every year <i>›</i></span></div>'
                f'<div class="tp">{img(ph, c["name"])}<span class="tsc {"good" if c["li"] < 100 else "bad"}">{c["li"]}</span></div></a>')
    best, worst = CARS[0], CARS[-1]
    a, b = aph('toyota-rav4', 2019), aph('honda-cr-v', 2017)
    vin = aph('toyota-camry', 2019); sv, fd = aph('chevrolet-silverado'), aph('ford-f-series')
    for ph in (a, b, vin, sv, fd): ph and who.append(ph['author'].split('\ufffd')[0].strip()); ph and ph.get('ai') and ai.append(ph['ai'])
    def vimg(name):
        w, h = Image.open(f'assets/vote/{name}.webp').size
        return {'src': f'/assets/vote/{name}.webp', 'w': w, 'h': h}
    if not sv: sv = vimg('chevy'); who.append('Ghostofakina')
    if not fd: fd = vimg('ford'); who.append('Kevauto')
    t = [car_tile(best, 'Most reliable', 't-good'), car_tile(worst, 'Biggest lemon' + ('*' if worst['est'] else ''), 't-bad'),
         f'<a class="tile" href="/compare/"><div class="tt"><p class="te">Compare</p><h2>Compare up to 4 cars.</h2><p class="ts">Side by side, year by year.</p><span class="tl">Compare cars <i>›</i></span></div>'
         f'<div class="tp tp2">{img(a, "Toyota RAV4", "l")}{img(b, "Honda CR-V", "r")}</div></a>',
         f'<a class="tile" href="/vote/"><div class="tt"><p class="te">Vote</p><h2>Chevy or Ford?</h2><p class="ts">Plus best brand and worst insurer.</p><span class="tl">Cast your vote <i>›</i></span></div>'
         f'<div class="tp tp2">{img(sv, "Chevy Silverado", "l")}{img(fd, "Ford F-150", "r")}</div></a>',
         f'<a class="tile" href="/vin/"><div class="tt"><p class="te">VIN check</p><h2>Open recalls.</h2><p class="ts">On the exact car you\'re looking at.</p><span class="tl">Check a VIN <i>›</i></span></div>'
         f'<div class="tp">{img(vin, "Toyota Camry")}</div></a>',
         f'<a class="tile t-dark" href="/data/"><div class="tt"><p class="te">Free data</p><h2>Take it. Credit us.</h2><p class="ts">Every score, as a spreadsheet.</p><span class="tl">Download <i>›</i></span></div>'
         f'<div class="tp tsheet"><div class="tsh">' + ''.join(f'<span>{E(c["name"])}</span><span>{c["years"].split("-")[0]}–{c["years"].split("-")[-1][-2:]}</span><b class="{"good" if c["li"] < 100 else "bad"}">{c["li"]}</b>' for c in (CARS[0], CARS[1], CARS[len(CARS) // 2], CARS[-2], CARS[-1])) + '</div></div></a>']
    cr = ' · '.join(dict.fromkeys(w for w in who if w))
    bits = ([f'Photos: {E(cr)} (Wikimedia Commons, CC BY-SA)'] if cr else []) + (['*Tesla uses estimated sales.'] if worst['est'] else [])
    return f'<section class="tiles">{"".join(t)}</section><p class="tiles-cr">{" · ".join(bits)}' + (ai_note(", ".join(dict.fromkeys(ai))) if ai else '') + '</p>'

def pimg(ph, alt, cls=''):
    return f'<img class="{cls}" src="{ph["src"]}"{rset(ph["src"], SZ_TWO if cls else SZ_ONE)} alt="{E(alt)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy">' if ph else ''
AI_MARK = '~ai~'   # who() puts this in for an AI illustration; pcredit() turns it into the (i) disclosure
def who(*phs): return [AI_MARK if ph.get('ai') else ph['author'].split('\ufffd')[0].strip() for ph in phs if ph and (ph.get('author') or ph.get('ai'))]
def pcredit(names):
    names = list(dict.fromkeys(n for n in names if n)); ai = AI_MARK in names; names = [n for n in names if n != AI_MARK]
    if not names and not ai: return ''
    return '<p class="ph-cr">' + (f'Photos: {E(" · ".join(names))} (Wikimedia Commons)' if names else '') + (ai_note('cars shown') if ai else '') + '</p>'
def pair(a, b, alts=('', '')): return f'<div class="ph-pair">{pimg(a, alts[0], "l")}{pimg(b, alts[1], "r")}</div>'
def trio(phs, alts): return '<div class="ph-trio">' + ''.join(pimg(ph, al, f"c{i}") for i, (ph, al) in enumerate(zip(phs, alts))) + '</div>'
def phero(eyebrow, title, sub, visual='', extra='', credit=''):
    """The v6 page top: eyebrow, h1, one line, then the tool (extra) and the photos (visual)."""
    v = '<div class="ph-v">' + visual.replace(' loading="lazy"', '') + '</div>' if visual else ''   # 11-09: hero photos load right away
    return f'<section class="ph"><p class="ph-e">{eyebrow}</p><h1>{title}</h1><p class="ph-s">{sub}</p>{extra}{v}{credit}</section>'
def qa_fold(html_):
    """<h3>Q</h3><p>A</p> pairs -> tap-to-open rows."""
    return re.sub(r'<h3>(.*?)</h3><p>(.*?)</p>', r'<details class="qa"><summary><h3 class="qh">\1</h3></summary><p>\2</p></details>', html_)
VOTE_IMG = lambda n: (lambda im: {'src': f'/assets/vote/{n}.webp', 'w': im.size[0], 'h': im.size[1], 'author': {'chevy': 'Ghostofakina', 'ford': 'Kevauto'}[n]})(__import__('PIL.Image', fromlist=['Image']).open(f'assets/vote/{n}.webp'))

# 11-11 (Elijah): three quick ways in, right under the search (outside the folding selects, so always visible)
HOME_CHIPS = ('<nav class="hqk" aria-label="Browse">' + ''.join(f'<a href="{u}">{gh_ic(i)}<span>{t}</span></a>' for u, i, t in
              (('/cars/', '/cars/', 'All cars'), ('/cars/?type=supercars', '/supercars/', 'Supercars'), ('/motorcycles/', '/motorcycles/', 'Motorcycles'))) + '</nav>')
def home_compare():
    """11-11 (Elijah: "right under the any car search should show the compare cars box first instead of the two random cars"): a compact compare
    box: one big match-up with both AI cars, two more popular ones as links, and the way into /compare/ to pick any two."""
    nm = {c['id']: c['name'] for c in CARS}
    pairs = [p for p in (('toyota-rav4', 'honda-cr-v'), ('toyota-camry', 'honda-civic'), ('chevrolet-silverado', 'ram-pickup'), ('nissan-rogue', 'ford-escape'))
             if p[0] in nm and p[1] in nm and os.path.exists(os.path.join(OUT, 'compare', f'{p[0]}-vs-{p[1]}')) or (p[0] in nm and p[1] in nm)][:3]
    (a, b), rest = pairs[0], pairs[1:]
    sh = lambda n: n if n.split(' ', 1)[0] in ('Ram',) else n.split(' ', 1)[-1]   # "Camry", but "Ram pickup"
    im = lambda fid, cls: (lambda ph: f'<img class="{cls}" src="{ph["src"]}" alt="{E(nm[fid])}" width="{ph["w"]}" height="{ph["h"]}" fetchpriority="high" decoding="async">' if ph else '')(aph(fid))
    return (f'<div class="hcmp"><p class="hcmp-k">Compare</p><h2>Compare up to 4 cars, side by side.</h2>'
            f'<a class="hcmp-pair" href="/compare/{a}-vs-{b}/"><span class="hcmp-im">{im(a, "l")}{im(b, "r")}</span><b>{E(nm[a])} <i>vs</i> {E(nm[b])}</b></a>'
            '<p class="hcmp-l">' + ' '.join(f'<a href="/compare/{x}-vs-{y}/">{E(sh(nm[x]))} vs {E(sh(nm[y]))}</a>' for x, y in rest) + '</p>'
            f'<a class="btn hcmp-go" href="/compare/">Compare up to 4 cars&nbsp;<i>›</i></a><span class="hcmp-ii">{ai_note("cars shown")}</span></div>')
def hero_cards():
    """Two real cars, one great and one a lemon, as stacked report cards with their dial (exact-year Commons photos from data_photos.py)."""
    ph = json.load(open('data/photos.json', encoding='utf-8')); yrs = {f['id']: f for f in _YJ}
    out = []
    # 11-10 (Elijah: a car with an AI image never shows the Wikimedia one): AI illustrations, credit behind one 'i' (the RAV4 card is the 2022,
    # the illustration's own generation; the Cherokee illustration is the same 2014-2023 generation)
    for fid, y, cls in (('toyota-rav4', 2022, 'hc-1'), ('jeep-cherokee', 2014, 'hc-2')):
        f = yrs[fid]; v = next(w for w in f['years'] if w['y'] == y); im = YSL.model_img(fid) or ph[fid][str(y)]
        top = (v.get('parts') or [['', 0]])[0][0]
        out.append(f'<a class="hc {cls}" href="/cars/{fid}/{y}/"><img src="{im["src"]}"{rset(im["src"], "(max-width: 620px) 44vw, (max-width: 999px) 94vw, 260px")} alt="{E(f["name"])}, illustration" width="{im["w"]}" height="{im["h"]}" fetchpriority="high">'
                   f'<div class="hc-b"><div><b>{y} {E(f["name"])}</b><span>{E(plain(v["li"]))}</span>{f"<small>Top complaint: {E(top.split(",")[0])}</small>" if top else ""}</div>{gauge(v["li"], 128, False)}</div></a>')
    return f'<div class="hcs">{"".join(out)}<p class="hc-cr">{ai_note("Toyota RAV4 and Jeep Cherokee")}</p></div>'

# ---- home: the car finder first (10-29), how to read a score, the explorer, then best vs worst side by side, then brands
best4, worst4 = CARS[0], CARS[-1]
# 10-30: Google showed /method/ for "lemon index" (its h1 was the only one saying the brand), so the home h1 now carries the name too.
# 11-08 internal links: the home page links straight to the model pages people search most, with "reliability" in the link text. First the
# ones Search Console shows just off page 1 of Google (C-Class #11, Mazda3 #10, Audi Q5 #10, Equinox #13 on 11-08), then best sellers.
POP_FIRST = ['mercedes-benz-c-class', 'mazda3', 'audi-q5', 'chevrolet-equinox', 'honda-accord', 'toyota-camry', 'bmw-3-series', 'audi-a4']
def pop_checks(n=28):
    have = {f['id'] for f in _YJ}; by = {c['id']: c for c in CARS}
    ids = list(dict.fromkeys([i for i in POP_FIRST if i in by and i in have] + [c['id'] for c in sorted(CARS, key=lambda c: -c['sold']) if c['id'] in have]))[:n]
    return ('<section class="hpop"><h2>Reliability checks people run most.</h2><p class="hpl">'
            + ''.join(f'<a href="/cars/{i}/">{E(by[i]["name"])} reliability</a>' for i in ids) + '</p></section>')
# 11-11 (Elijah: "make the page that says every model and has the 4 selectors the main page"): the home page is the /cars/ grid now (built
# after it, below). Its old sections (the 100 scale, best/worst cards, the full ranked list, the most-checked cars, the brand bars) moved here.
HOME_FAQ = faq
page('/rankings/', 'Car Reliability Rankings: Every Model and Brand, Best to Worst | The Lemon Index',
     f'Every car model and brand ranked by owner complaints per car sold, best to worst: {len(CARS)} models, model years 2010-2022. 100 is the average car; lower is better.', f'''
<div class="pg">{phero('Rankings', 'Every car, best to worst.', 'Owner complaints filed with the U.S. government, per car sold. 100 is the average car.')}</div>
<div class="home"><section class="hread"><h2>100 is the average car. <span class="h2s">Lower is better.</span></h2>
<div class="scale"><div class="sbar"><i style="left:{min(96, best4["li"] / 3.5):.1f}%" title="{E(best4["name"])}, {best4["li"]}"></i></div><div class="sl"><span>25 · ¼ the complaints</span><span>100 · average</span><span class="bad">300 · 3×</span></div></div></section>
{tiles()}
{explorer()}
{pop_checks()}
<section><h2>Every brand, best to worst.</h2>{bars(BRANDS, 330, 'two')}<p class="note">* Porsche is a small sample (2 models, 258,000 sold). Tesla uses estimated U.S. sales.</p></section>
{share_line("Every car ranked by real owner complaints, best to worst. Free:")}</div>''',
     ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Car reliability rankings", "url": BASE + '/rankings/'}])
HOME_PAGE = dict(title="Lemon Index (LemonIndex): Look Up Any Car's Problems by Year",
                 desc=f"Look up any car's problems by model year, 2000 to 2025: its reliability score, top problem areas and real owner complaints. Scores from {COUNTED:,} owner complaints to the government. 100 is the average car.",   # 11-12 r2 (Ryan): the meta said 1.6 million while the page says {COUNTED:,}
                 ld=[{"@context": "https://schema.org", "@type": "WebSite", "name": "The Lemon Index", "alternateName": ["Lemon Index", "LemonIndex", "lemonindex", "lemonindex.com"], "url": BASE + '/'},
                     {"@context": "https://schema.org", "@type": "Organization", "name": "The Lemon Index", "alternateName": ["Lemon Index", "LemonIndex", "lemonindex.com"], "url": BASE + '/', "logo": BASE + '/assets/icon-180.png', "sameAs": [YT, TT, IG]},
                     {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}])

# ---- study
page(STUDY, 'The Most Reliable Cars, According to 1.6 Million Owner Complaints', 'The most and least reliable cars and brands in the U.S., ranked by NHTSA owner complaints per 100,000 sold. Toyota 4Runner 26, Lexus 30, Tesla 322 (est.).', f'''
<article class="study"><p class="kicker">Study #1 · {TODAY}</p><h1>The Most Reliable Cars, According to 1.6 Million Owner Complaints</h1>
<p class="lede">The Toyota 4Runner drew about a quarter of the complaints of the average car. The Tesla Model S drew more than four times as many. Here's every number.</p><p>{share_btn("The most reliable cars, ranked by 1.6 million owner complaints. The 4Runner drew a quarter of the average car's:")}</p>
<div class="stats"><div><b>1,607,537</b><span>complaints in NHTSA's file since 1995</span></div><div><b>{COUNTED:,}</b><span>counted: filed within 3 years of a 2010-2022 model year</span></div><div><b>131</b><span>models ranked</span></div><div><b>22</b><span>brands</span></div><div><b>2010-2022</b><span>model years</span></div></div>
<p class="sub">How to read it: the Lemon Index compares a car's owner complaints per car sold with the average car of the same model years. <b>100 is average.</b> 26 means about a quarter of the average car's complaints; 430 means 4.3 times as many.</p>
<div class="stack"><div><h2>Most reliable: the top 10</h2><div class="tw"><table><thead><tr><th>#</th><th>Model</th><th>Index</th><th>Compared with average</th><th>Sold in the U.S.</th></tr></thead><tbody>{best_rows}</tbody></table></div>
<p class="note">What it means for you: a long-running model with a low index is the surest bet. Most of this list has been on sale, mostly unchanged, for a decade. Sold = U.S. sales across 2010-2022.</p></div>
<div><h2>Least reliable: the bottom 10</h2><div class="tw"><table><thead><tr><th>Model</th><th>Index</th><th>Compared with average</th><th>Top complaint (share of its complaints)</th></tr></thead><tbody>{worst_rows}</tbody></table></div>
<p class="note">What it means for you: one part can sink a car. Check the top complaint for the exact model year before you buy. * Tesla uses published sales estimates. Each score covers that model&#39;s own model years (shown in the table) with complaints from each car&#39;s first 3 years. The <a href="/electric/">EV ranking</a> scores model years {EV_WIN} with a shorter window, so an EV can show two numbers{(lambda m, e: f' (Tesla Model S: {m} here, {e} there)' if m and e else '')(MAINBY.get('tesla-model-s', {}).get('li'), EVBY.get('tesla-model-s', {}).get('li'))}.</p></div></div>
<h2>Brands, best to worst</h2>{bars(BRANDS, 330, "two")}<p class="note"><a href="/cars/">Look up any of the {len(CARS)} models by year →</a></p>
<h2>Best and worst by type</h2><div class="tw"><table><thead><tr><th>Type</th><th>Best</th><th>Worst</th></tr></thead><tbody>{seg_rows}</tbody></table></div>
<h2>Three patterns in the data</h2>
<ol class="beats"><li><b>New designs are a gamble, but year one is only a little worse.</b> Several of the worst models are recent all-new designs (Telluride, Palisade, Pacifica, the 2014-on Cherokee). Across 31 new models, the first model year drew about 20% more complaints than the next three, so waiting a year helps a little. It isn't a rule.</li>
<li><b>The Germans beat their reputation, early on.</b> In the first three years of ownership, BMW (52) and Mercedes-Benz (54) drew fewer complaints per car than Honda (87) or Ford (144). This measures early safety complaints, not out-of-warranty repair bills.</li>
<li><b>Tesla's problem is mostly one system.</b> About 80% of Model 3 and Model Y complaints are about forward collision avoidance, the car braking hard for nothing.</li></ol>
<p class="note"><b>Correction (10-24):</b> an earlier version (and our video) said first model years drew about 70% more complaints. After we fixed a sales-timing error (a new model's first cars often sell the calendar year before its model year), it's about 20%. A few scores moved by 1 to 5 points; the rankings didn't change, except that the Dodge Dart joined the bottom 10.</p>
<h2>How we measured it</h2><p>A complaint counts only if NHTSA received it within three years of the model year, so old and new cars get the same window. Each model year is divided by that year's U.S. sales, then compared with the average car of the same years. <a href="/method/">Full method and caveats →</a></p>
{share_line("The most reliable cars, ranked by 1.6 million owner complaints. The 4Runner drew a quarter of the average car's:")}</article>''', kind='article', vis=pimg(mphoto('toyota-4runner'), 'Toyota 4Runner') + pcredit(who(mphoto('toyota-4runner'))),
     ld=[{"@context": "https://schema.org", "@type": "Dataset", "name": "Lemon Index: U.S. car reliability by NHTSA complaints per 100,000 sold", "description": "131 models and 22 brands, model years 2010-2022, ranked by safety complaints filed with NHTSA within 3 years of the model year per 100,000 U.S. sales, indexed to the average car (100).",
          "url": BASE + STUDY, "creator": {"@type": "Organization", "name": "The Lemon Index"}, "license": "https://creativecommons.org/licenses/by/4.0/", "isBasedOn": "https://www.nhtsa.gov/nhtsa-datasets-and-apis", "temporalCoverage": "2010/2022", "dateModified": TODAY},
         {"@context": "https://schema.org", "@type": "Article", "headline": "The Most Reliable Cars, According to 1.6 Million Owner Complaints", "datePublished": TODAY, "dateModified": TODAY, "author": {"@type": "Organization", "name": "The Lemon Index"}, "image": BASE + '/assets/og.png'}])

# ---- studies index
# 11-12 monthly data studies (research #4): data/studies/<yyyy-mm>.json from 3 Lemon Index/data/studies/make_study.py; pages by studies_month.py (exec'd after /press/)
MST = [json.load(open(os.path.join('data/studies', _f), encoding='utf-8')) for _f in sorted((f for f in os.listdir('data/studies') if re.fullmatch(r'\d{4}-\d{2}\.json', f)), reverse=True)] if os.path.isdir('data/studies') else []
_MST_TILES = ''.join(f'<a class="tile" href="/studies/{s["ym"]}/"><div class="tt"><p class="te">Monthly study · {E(s["label"])}</p><h2>{E(s["title"])}</h2><p class="ts">{s["n"]:,} owner complaints to NHTSA{"" if s["final"] else " so far"}.</p><span class="tl">Read the study <i>›</i></span></div><div class="tp"><img src="{s["chart"]}" alt="Chart: most owner complaints by model, {E(s["label"])}" width="720" height="472" loading="lazy"></div></a>' for s in MST[:2])
page('/studies/', 'Car Reliability Studies: Rankings From Owner Complaints | Lemon Index', 'Every Lemon Index study: the most and least reliable cars, brands and electric cars, measured with 1.6 million NHTSA owner complaints and U.S. sales.', f'''
<div class="pg">{phero('Studies', 'Studies.', 'Millions of public records. One clear ranking each.')}
<section class="tiles">{_MST_TILES}
<a class="tile" href="{STUDY}"><div class="tt"><p class="te">Study #1</p><h2>The most reliable cars.</h2><p class="ts">131 models. 1.6 million owner complaints.</p><span class="tl">Read the study <i>›</i></span></div><div class="tp">{pimg(mphoto('toyota-4runner'), 'Toyota 4Runner')}</div></a>
<a class="tile" href="/electric/"><div class="tt"><p class="te">Electric cars</p><h2>The most reliable EVs.</h2><p class="ts">22 electric cars, plus fires and fuel cost.</p><span class="tl">See the ranking <i>›</i></span></div><div class="tp">{pimg(mphoto('tesla-model-s'), 'Tesla Model S')}</div></a></section>
{pcredit(who(mphoto('toyota-4runner'), mphoto('tesla-model-s')))}
{share_line("Which cars have the fewest problems? Free studies from 1.6 million owner complaints:")}</div>''',
     ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Car Reliability Studies", "url": BASE + '/studies/', "hasPart": [{"@type": "Article", "headline": s['title'], "url": BASE + f'/studies/{s["ym"]}/'} for s in MST] + [{"@type": "Article", "headline": "The Most Reliable Cars, According to 1.6 Million Owner Complaints", "url": BASE + STUDY}]}])

# ---- method
# 11-10 engine code lookup: the small search box on model pages (page() appends it) + the script; full search lives in engine_pages.py
SEARCH_MINI = ('<section class="csearch mini" aria-label="Engine code search"><form class="cs-f" action="/check-engine-light/" method="get" role="search">'
               '<label for="cs-q">Check engine light on? Look up the code</label><div class="cs-row"><input id="cs-q" name="code" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="8" placeholder="P0420">'
               '<button type="submit">Look it up</button></div></form><div class="cs-out" id="cs-out" aria-live="polite"></div></section>')
CODES_JS = '<script src="/assets/codes.js?v=2" defer></script>'
def faq_ld(qa): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": t}} for q, _, t in qa]}
METHOD_QA = [('Is it per car sold?', "Yes. Every score divides a car's complaints by how many were sold in the U.S. So Ford outselling Chevy doesn't make Ford look worse; a car only scores badly if it drew more complaints for each car on the road."), ("Isn't it just owners who skip maintenance?", "We only count complaints filed in a car's first 3 years, when it's nearly new and usually still under the factory warranty. That points at problems the car left the factory with, not a 15-year-old car that missed its oil changes."), ('Does it tell me how long a car will last?', "No. It measures early complaints, not lifespan. A truck can draw a lot of complaints in its first years and still run past 300,000 miles. Use it to see which years had problems, then check the car's own history."), ('Why so few complaints for a problem everyone knows about?', "Most owners never file with the government; they just go to a mechanic. So the counts are a small slice of real failures. That's fine for comparing cars, because every car is measured the same way, but don't read a count as the number of cars that broke."), ('Can you split it by engine or trim?', 'The government files list make, model and year, not the engine. Where the model name gives the engine away (BMW files the 328i and 335i separately, for example), we can split by it. Otherwise a score covers every engine sold that year.')]
page('/method/', 'Method: How We Score Car Reliability | The Lemon Index', 'How we turn NHTSA owner complaints and U.S. sales into one reliability number per car, plus the caveats that come with it.', '''
<div class="pg">''' + phero('How it works', 'One number per car.', 'Owner complaints per car sold, against the average car.') + '''<article class="study"><p class="note">A &ldquo;lemon&rdquo; is American slang for a car with a lot of problems (en español: un carro con muchas fallas). The Lemon Index measures how many problems owners report.</p><div class="hw"><div><b>1</b><h3>Count complaints</h3><p>Every complaint owners filed with the U.S. government (NHTSA) in the car&#39;s first 3 years.</p></div>
<div><b>2</b><h3>Divide by cars sold</h3><p>So a car that sold a million doesn&#39;t look worse than one that sold ten thousand.</p></div>
<div><b>3</b><h3>Compare with the average car</h3><p>100 = average. 50 = half the complaints. 200 = double.</p></div></div>
<div class="hwm"><div class="ym-bar"><i class="ym-avg" style="left:40%"><span>average car = 100</span></i><i class="ym-pin" style="left:12%"><b>30: great</b></i><i class="ym-pin" style="left:80%"><b>200: lemon</b></i></div><div class="ym-ends"><span>fewer complaints</span><span>more complaints</span></div></div>
<p><a class="btn" href="/cars/">Look up your car</a></p>
<details class="yd"><summary>The details</summary><ol class="beats"><li><b>Complaints:</b> the full NHTSA owner-complaint file (1,607,537 vehicle complaints, 1995 to October 2026; <a href="/data/#totals">why our totals differ</a>).</li>
<li><b>Sales:</b> U.S. sales per model per year from automakers' published figures. Tesla doesn't report by model, so we use published estimates and say so.</li>
<li><b>Same window for every car:</b> a complaint counts only if it was filed within 3 years of the model year.</li>
<li><b>Rate:</b> complaints per 100,000 cars sold, matched model year to sales year. When a new model's first cars sold the calendar year before its model year, those sales are counted with the first model year.</li>
<li><b>Index:</b> each car's rate against the average car of the same model years.</li></ol></details>
<h2>What it doesn't measure</h2><p>It isn&#39;t a crash-safety rating: each year page shows NHTSA&#39;s crash-test stars separately. A complaint is an owner&#39;s report to the government, not a repair record. Fleet and rental-heavy models have fewer owners filing. Luxury lessees often go straight to the dealer. Some owners file more readily than others. Read it as early-life owner complaints, not total cost of ownership.</p>
<details class="yd"><summary>Also on every car page</summary><ul><li><b>Recalls:</b> every NHTSA safety recall campaign for that model year (NHTSA recalls API).</li>
<li><b>Crash tests:</b> NHTSA 5-star safety ratings for each body style tested (model years 2011 on).</li>
<li><b>Fuel economy:</b> EPA combined mpg and yearly fuel cost from fueleconomy.gov, across the versions sold that year.</li>
<li><b>When problems show up:</b> the odometer reading owners gave in their complaints. Unlike the score, this uses every complaint for the model year, because high-mileage failures come years later. Readings of 0 or over 400,000 miles are left out.</li>
<li><b>How serious:</b> complaints in which the owner reported a crash, a fire, an injury, a death or a tow. Owners report these; NHTSA doesn&#39;t confirm the cause.</li></ul></details>
<h2>What people ask</h2>''' + qa_fold('''<h3>Is it per car sold?</h3><p>Yes. Every score divides a car&#39;s complaints by how many were sold in the U.S. So Ford outselling Chevy doesn&#39;t make Ford look worse; a car only scores badly if it drew more complaints for each car on the road.</p><h3>Isn&#39;t it just owners who skip maintenance?</h3><p>We only count complaints filed in a car&#39;s first 3 years, when it&#39;s nearly new and usually still under the factory warranty. That points at problems the car left the factory with, not a 15-year-old car that missed its oil changes.</p><h3>Does it tell me how long a car will last?</h3><p>No. It measures early complaints, not lifespan. A truck can draw a lot of complaints in its first years and still run past 300,000 miles. Use it to see which years had problems, then check the car&#39;s own history.</p><h3>Why so few complaints for a problem everyone knows about?</h3><p>Most owners never file with the government; they just go to a mechanic. So the counts are a small slice of real failures. That&#39;s fine for comparing cars, because every car is measured the same way, but don&#39;t read a count as the number of cars that broke.</p><h3>Can you split it by engine or trim?</h3><p>The government files list make, model and year, not the engine. Where the model name gives the engine away (BMW files the 328i and 335i separately, for example), we can split by it. Otherwise a score covers every engine sold that year.</p>''') + '''<h2>Using the data</h2><p>Free to cite with a link to lemonindex.com (CC BY 4.0). <a href="/data/">Download it</a>.</p></article></div>''',
     ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": "How We Score Car Reliability", "url": BASE + '/method/', "about": "Car reliability measured as NHTSA owner complaints per 100,000 U.S. sales"}, faq_ld([(q, '', a) for q, a in METHOD_QA])])

# ---- model-year lookup (10-29, Elijah: "a per year / model lookup so people can look at their car's exact issues").
# data/years.json comes from data_years.py: per family and model year the index, complaints, sold, top problem areas and up to 3 owner complaints.
YEARS = [f for f in _YJ if f['name'] in BYNAME]
# 10-29: model years 2000-2009 added (Elijah's car is a 2008). Their scores are rough (fewer owners filed online, launch years sold partly the
# calendar year before), so a pre-2010 year with under 20 complaints gets no score, and its page says the score is rough.
for f in YEARS:
    for v in f['years']: v['ok'] = v.get('li') is not None and ((v['y'] >= 2010 and not v.get('early')) or v['n'] >= 20)   # 11-03: early-read years (2023-2025) need 20+ complaints too; 11-11: low-sales years never
LOWS = lambda v: f'{v["low"]["sold"]:,}'   # the cited calendar-year U.S. sales of a low-sales year
# 11-12: a Tesla year with no per-model sales figure at all (low.why == 'tesla'): complaints only, and the page says why
NOSALES = lambda v: (v.get('low') or {}).get('why') == 'tesla'
NOSALES_WHY = 'Tesla doesn&#39;t report U.S. sales by model, and no estimate covers this model year on its own'
LOWSRC = lambda v: (f' (<a href="{E(v["low"]["url"])}" rel="nofollow">sales source</a>)' if v['low'].get('url') else '')
LIS = lambda v: v['li'] if v['ok'] else '–'
USD = lambda a: f'${a[0]:,}' if a[0] == a[1] else f'${a[0]:,}–${a[1]:,}'   # 11-12 r2 (Ryan: "$3050–4000"): money ranges with commas
# 11-12 round 2 (UX test: "Worth a look" on both 106 and 46, 3 labels for one car): ONE verdict per score band, used on year pages, model
# pages, compare, match-ups, the Years tab and brand pages (assets/compare.js and brands_pages.py mirror it). 2023+ years are partial everywhere.
def band(li):
    if li < 50: return 'good', 'One of the most reliable'
    if li < 85: return 'good', 'Better than average'
    if li <= 115: return 'mid', 'About average'
    if li < 200: return 'bad', 'Worse than average'
    return 'bad', 'Avoid'
PARTIAL = 'Too new: partial score'
CLS = lambda v: ('na' if v.get('early') else band(v['li'])[0]) if v['ok'] else 'na'   # 11-11: an unscored year is gray, never green; 11-12 r2: bands, partial = gray
PLN = lambda v: plain(v['li']) if v['ok'] else 'complaints only, no sales figure to score' if NOSALES(v) else 'complaints only, too few sold to score' if v.get('low') else 'too few complaints to score'
CARU = lambda f, y=None: f'/cars/{f["id"]}/' + (f'{y}/' if y else '')
yurls = []

# ---- 10-31 extras (Elijah: "do all 5"): recalls, crash tests and fuel economy from the official APIs (data_fetch_api.py),
# when problems show up (odometer at complaint) and how serious they were (data_extras_local.py).
_load = lambda p: json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
XL, XA = _load('data/extras_local.json'), _load('data/extras_api.json')
if os.path.exists('data/extras_local_new.json'): XL.update(_load('data/extras_local_new.json')); XA.update(_load('data/extras_api_new.json'))   # 11-11 new models
for _src, _dst in (('data/extras_local_low.json', XL), ('data/extras_api_low.json', XA), ('data/extras_local_tesla.json', XL), ('data/extras_api_tesla.json', XA)):   # 11-11 the study models' low-sales years
    for _fid, _ys in _load(_src).items(): _dst.setdefault(_fid, {}).update(_ys)
# 11-12 (Jess: "38 crashes, 4 fires" needs a baseline): how often a complaint mentions a crash / injury / fire / tow across every model year we track
_SV = defaultdict(int)
for _ys in XL.values():
    for _x in _ys.values():
        for _k, _n in ((_x or {}).get('sev') or {}).items(): _SV[_k] += _n
SEVR = {k: _SV[k] / _SV['total'] for k in ('crash', 'injured', 'fire', 'towed')} if _SV['total'] else {}
def extra(fid, y):
    d = dict(XL.get(fid, {}).get(str(y), {})); d.update(XA.get(fid, {}).get(str(y), {}) or {}); return d
# ---- 11-04 YouTube videos (data_yt.py): what owners/buyers watch most, by views, with the top video for each topic. Mobile first:
# 4 topics open, the rest behind "Show more"; each topic's top video is one big tap target (thumbnail + 2-line title).
YTV = _load('data/yt.json')
BMW_PHASE = 'hooks'; exec(open('bmw_pages.py', encoding='utf-8').read())   # 11-10 BMW specs + engines: SPECS_HOOK / YEAR_SPECS_HOOK
def _vw(n): return f'{n / 1e6:.1f}M' if n >= 1e6 else f'{round(n / 1e3):,}K' if n >= 1e3 else str(n)
import repair_costs as RCQ   # 11-12 fix D: "What repairs cost" (owners' repair bills to NHTSA + what to ask the shop)
_YRX = re.compile(r'(?<!\d)((?:19|20)\d\d)(?:\s*[-–]\s*((?:19|20)?\d\d))?(?!\d)')
def _vid_gen_ok(title, ys):
    """11-12 (UX test: a 2015 CR-V page showed 2007-2012 videos): a video whose title names model years counts for this generation only when
    at least half the years it names are in it; no year in the title = fine"""
    if not ys: return True
    named = set()
    for a, b in _YRX.findall(title or ''):
        a = int(a); b = (int(b) if len(b) == 4 else a // 100 * 100 + int(b)) if b else a
        named.update(range(a, b + 1) if a <= b <= a + 15 else [a])
    named = {n for n in named if 1980 <= n <= 2030}
    return not named or len(named & set(ys)) * 2 >= len(named)
def ytfix(key, y=None):
    d = next((e for e in YTV.get(key, []) if e['years'] is None or y in e['years']), None)
    rcq = RCQ.html_block(key, y, (d or {}).get('years'), (d or {}).get('gen') or '') if y and ':' not in key else ''
    if d and d.get('years'):   # 11-12: only this generation's videos
        gy = d['years']; d = dict(d, topics=[t for t in d['topics'] if _vid_gen_ok(t['best']['title'], gy)], guides=[v for v in d['guides'] if _vid_gen_ok(v['title'], gy)])
    if not d or not d['topics']: return rcq
    W = lambda v: f'https://www.youtube.com/watch?v={v["id"]}'
    TH = lambda v, w=160: f'<img src="https://i.ytimg.com/vi/{v["id"]}/mqdefault.jpg" alt="{E(v["title"])}" loading="lazy" width="{w}" height="{w * 9 // 16}">'
    mx = d['topics'][0]['views']
    def li(t):
        more = f' · {t["n"]} videos' if t['n'] > 1 else ''
        return (f'<li><div class="yf-h"><b>{E(t["name"])}</b><span>{_vw(t["views"])} views</span></div><span class="yf-bar"><i style="width:{max(4, round(t["views"] / mx * 100))}%"></i></span>'
                f'<a class="yf-v" href="{W(t["best"])}" target="_blank" rel="noopener nofollow">{TH(t["best"])}<span><b>{E(t["best"]["title"])}</b><small>{E(t["best"]["channel"])} · {_vw(t["best"]["views"])} views{more}</small></span></a></li>')
    tp = d['topics']; first = ''.join(li(t) for t in tp[:4]); rest = ''.join(li(t) for t in tp[4:])
    same = f' The {y} is the same {d["noun"]}.' if y and d['noun'] else ''
    cards = ''.join(f'<a class="yg" href="{W(v)}" target="_blank" rel="noopener nofollow">{TH(v, 320)}<b>{E(v["title"])}</b><small>{E(v["channel"])} · {_vw(v["views"])} views</small></a>' for v in d['guides'])
    cst = d.get('costs'); costh = ''; costcap = ''
    if cst:   # 11-10 (Elijah: "make this visually better"): uniform cost tiles with a range bar, prices as a small separate strip, disclaimer behind the (i)
        M = lambda n: f'${n / 1e6:.2f}M' if n >= 1e6 else f'${n:,.0f}'
        R = lambda n: M(float(f'{n:.2g}')) if n >= 100 else M(n)   # ranges: 2 significant figures
        HEAR = lambda x, what: f'<a class="yc-h" href="https://www.youtube.com/watch?v={x["id"]}&t={x["t"]}s" target="_blank" rel="noopener nofollow" aria-label="Hear it: {E(what)} in the video">&#9654; Hear it</a>'
        stats = []
        for key, label in (('paid', 'Owners paid'), ('used', 'Used price'), ('msrp', 'Price when new')):
            x = cst.get(key)
            if x: stats.append(f'<li><small>{label}</small><b>{M(x["median"])}</b><span>{x["videos"]} videos</span>{HEAR(x, label.lower())}</li>')
        def tile(k, x):
            nm, sub = (k.split(' (', 1) + [''])[:2]; sub = sub.rstrip(')')
            top = max(x['hi'], x['median']) * 1.25 or 1; L = lambda v: max(0, min(100, round(v / top * 100, 1)))
            return (f'<li><div class="yc-t"><span>{E(nm)}</span>' + (f'<small>{E(sub)}</small>' if sub else '') + '</div>'
                    f'<b>{M(x["median"])}</b>'
                    f'<span class="yc-r" aria-hidden="true"><i style="left:{L(x["lo"])}%;width:{max(2, L(x["hi"]) - L(x["lo"]))}%"></i><em style="left:{L(x["median"])}%"></em></span>'
                    f'<div class="yc-m"><small>most {R(x["lo"])}–{R(x["hi"])} · {x["videos"]} videos</small>{HEAR(x, nm)}</div></li>')
        # 11-12 (UX test: "$80 Other repairs" read like a total, and one-video quotes looked like facts): only repair items 5+ videos name, never
        # "Other" or ownership costs, each labeled as one repair
        tiles = ''.join(tile(k.split(' (')[0] + ' (one repair, as owners say it)', x) for k, x in cst['items']
                        if x['videos'] >= 5 and not re.match(r'(Other|Yearly|Insurance|Monthly|Lift|Exhaust / mods|Riding gear)', k))
        costh = ('<div class="ycost">' + (f'<h3>What owners say one repair costs on YouTube</h3><ul class="yc-g">{tiles}</ul>' if tiles else '')
                 + (f'<h3 class="yc-ph">Prices people quote</h3><ul class="yc-p">{"".join(stats)}</ul>' if stats else '') + '</div>')
        costcap = '<p class="yc-cap">Costs are the middle (median) of the dollar amounts people say out loud in these videos, so one wild number can&#39;t swing it. They aren&#39;t verified bills or sales; real prices depend on year, miles, condition and where you live. Tap Hear it to jump to the moment.</p>'
    cap = 'Views show how many people looked up each fix, not how often it breaks.' if d['kind'] == 'repair' else 'Views show what people watch most, not how often something goes wrong.'
    return rcq + (f'<section class="yc yfx" id="diy"><h2>{d["head"]}</h2><p class="yf-s">From {d["n"]} YouTube videos · {_vw(d["views"])} views · {E(d["gen"])}</p>'
            + (costh + '<h3 class="yf-g yf-g1">Most-watched topics</h3>' if costh else '') + f'<ol class="yfl">{first}</ol>' + (f'<details class="yf-more"><summary>Show {len(tp) - 4} more</summary><ol class="yfl">{rest}</ol></details>' if rest else '')
            + (f'<h3 class="yf-g">Before you buy, watch</h3><div class="ygs">{cards}</div>' if cards else '')
            + f'<p class="yc-cap">{cap} Videos belong to their creators; we link to them.{(" " + E(same.strip())) if same else ""}</p>' + costcap + '</section>')
mi = lambda n: f'{int(n):,} miles'
REPORT_NOTE = '<p class="note">The full Lemon Index report adds the mileage for every problem area, every recall in plain English and what to check before you buy. <b>Coming soon.</b></p>'
RPART = lambda s: PART.get((s or 'other').split(':')[0], (s or 'other').split(':')[0].lower()).replace('service brakes, hydraulic', 'brakes')   # 11-11: some NHTSA recalls carry no component
def rtag(r):
    """11-12 (UX test, Marcus: diesel fuel-pump and EGR recalls on his 3.6L gas Jeep): which engines or fuel a recall covers, from the
    "recalling certain ... vehicles equipped with ..." sentence. '' when the recall names no engine or fuel."""
    s = re.sub(r'\s+', ' ', r.get('summary') or '')
    sent = next((x for x in re.split(r'(?<=\.)\s+(?=[A-Z])', s) if 'recalling' in x.lower()), s[:300])
    if not re.search(r'equipped with|with (an? |the )?[0-9.]+ ?(l|liter)|(engines?|hybrid|diesel)\b', sent, re.I): return ''
    sz = re.search(r'\b(\d\.\d) ?(?:l\b|liter|-liter)', sent, re.I)
    if re.search(r'gasoline|\bgas\b', sent, re.I) and re.search(r'diesel', sent, re.I): return ''   # gas and diesel both covered
    if re.search(r'(equipped with|with)[^.]{0,60}(diesel|duramax|power ?stroke|cummins|\btdi\b|bluetec)|diesel engines?\b', sent, re.I): return (sz.group(1) + 'L diesel only') if sz else 'Diesel only'
    lm = re.search(r'recalling (?:certain )?(.*?)\b(vehicles|cars|trucks|SUVs)\b', sent, re.I)
    many = bool(lm and re.search(r',| and ', lm.group(1)))   # a list of models: a hybrid in it is a model name, not a limit on this car
    if re.search(r'equipped with[^.]{0,40}(plug-in|phev)', sent, re.I) or (not many and re.search(r'plug-in hybrid|\bphev\b|\b4xe\b', sent, re.I)): return 'Plug-in hybrid only'
    if re.search(r'equipped with[^.]{0,40}hybrid', sent, re.I) or (not many and re.search(r'hybrid (vehicles|models|electric)', sent, re.I)): return 'Hybrid only'
    if sz and re.search(r'equipped with[^.]{0,30}\d\.\d ?(?:l\b|liter|-liter)[^.]{0,40}engine', sent, re.I): return sz.group(1) + 'L engines only'
    return ''
def rtag_html(r):
    t = rtag(r)
    return f' <span class="rtag">{E(t)}</span>' if t else ''
def rsum(r):
    """A recall in one plain sentence: skip the "X is recalling certain ... vehicles ..." opener, keep the defect."""
    s = re.sub(r'\s+', ' ', r['summary']).strip()
    s = re.sub(r'^.*?\brecalling\b.*?\b(vehicles|trucks|pick-ups|pickups|cars|SUVs|equipment|tires|seats|motorcycles)\b(?:[^.]|\.(?=\d))*?(?<!\bCo)(?<!\bInc)\.(?!\d)\s*', '', s)
    first = re.split(r'(?<!\bCo)(?<!\bInc)(?<!\bCorp)(?<!\bNo)\.\s+(?=[A-Z(])', s)[0].strip().rstrip('.') if s else ''
    if len(first) < 25 or 'recalling' in first: first = re.sub(r'\s+', ' ', r.get('risk') or '').strip().rstrip('.')
    first = first + '.' if first else ''
    return first[:220] + ('…' if len(first) > 220 else '')
def stars(n):
    return f'<span class="stars" aria-label="{n} out of 5 stars">{"★" * int(n)}{"☆" * (5 - int(n))}</span>' if str(n).isdigit() else '<span class="muted">not rated</span>'
def miles_html(x, name):
    m, cs = x.get('miles'), x.get('comps') or []
    if not m: return ''
    top = cs[0] if cs else None
    return (f'<h2>When problems show up</h2><p>Half of the {name} complaints that listed a mileage came before <b>{mi(m["median"])}</b>. Most came between {mi(m["p25"])} and {mi(m["p75"])}.</p>'
            + (f'<p>The top problem area, <b>{E(top[0])}</b>, usually showed up between <b>{mi(top[2])} and {mi(top[3])}</b>.</p>' if top else '') + REPORT_NOTE)
# ---- 11-02 price box (Elijah): dealer asking prices by mileage, measured from real listings while researching each video (data/prices.json);
# private-party row waits for licensed data; salvage = sourced rule of thumb, never a made-up exact number.
def money(n): return f'${n / 1000:.1f}K'
def price_html(fid, y, name):
    d = (json.load(open('data/prices.json', encoding='utf-8')) if os.path.exists('data/prices.json') else {}).get(fid, {}).get(str(y))
    if not d: return ''
    rows = ''.join(f'<tr><td>{E(b["label"])}</td><td class="num pg">{money(b["med"] * .9)}</td><td class="num pf">{money(b["med"])}</td><td class="num ph">{money(b["med"] * 1.05)}+</td></tr>'
                   for b in d['buckets'] if b['n'] >= 10)
    if not rows: return ''
    return f'''<h2>What to pay</h2><p>Typical dealer asking price for a {y} {E(d.get("model", name))} by mileage, from <b>{d["n"]:,}</b> dealer listings nationwide ({E(d["date"])}). Under the great-deal number is about 10% below typical; over the high number is more than 5% above.</p>
<div class="tw"><table class="price"><thead><tr><th>Miles</th><th>Great deal<br><small>at or under</small></th><th>Typical</th><th>Too high<br><small>at or over</small></th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="pnotes"><p><b>Private seller:</b> coming soon. Private sellers often ask less than dealers, but we only publish a number once it&#39;s measured.</p>
<p><b>Salvage or rebuilt title:</b> usually sells for well under a clean title. Estimates run from about 27% less (a matched study of 2,389 cars) to as much as 50% less (Edmunds). This is a guide, not a price; get an inspection.</p></div>
<p class="note">Asking prices, not sale prices. Trim, engine, 4x4, condition and location move the price. Estimates, not an appraisal.</p>'''
def sev_html(x):
    s = x.get('sev')
    if not s or not s.get('total'): return ''
    cells = [('crash', 'reported a crash'), ('fire', 'reported a fire'), ('injured', 'reported an injury'), ('towed', 'needed a tow'), ('deaths', 'reported a death')]
    stat = ''.join(f'<div><b class="{"bad" if s.get(k) else "good"}">{s.get(k, 0):,}</b><span>{lbl}</span></div>' for k, lbl in cells if k != 'deaths' or s.get(k))
    return f'<h2>How serious</h2><div class="stats">{stat}</div><p class="note">Out of {s["total"]:,} complaints filed about this model year so far. Owners report these themselves; NHTSA doesn&#39;t confirm the cause.</p>'
def recalls_html(x, f, y):
    if 'recalls' not in x: return ''
    rs, nm = sorted(x['recalls'], key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2], reverse=True), E(f['name'])   # newest first; dates are DD/MM/YYYY
    mk, md = (x.get('names') or [['', '']])[0][:2]
    link = f'https://www.nhtsa.gov/vehicle/{y}/{mk.replace(" ", "%20")}/{md.replace(" ", "%20")}' if mk else 'https://www.nhtsa.gov/recalls'
    if not rs: return f'<h2>Recalls</h2><p>No safety recalls on record for the {y} {nm}. Still run the VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener">nhtsa.gov/recalls</a>.</p>'
    li = ''.join(f'<li><b>{E(RPART(r["part"]).capitalize())}</b> <small>· recall issued {E(r["date"][-4:])}</small>{rtag_html(r)}<br>{E(rsum(r))} <small class="muted">NHTSA {E(r["id"])}</small></li>' for r in rs[:6])
    more = f' <a href="{link}" rel="noopener">See all {len(rs)} at nhtsa.gov</a>.' if len(rs) > 6 else f' <a href="{link}" rel="noopener">Details at nhtsa.gov</a>.'
    return f'<h2>Recalls: {len(rs)}</h2><ul class="recalls">{li}</ul><p class="note">Recall work is free at any dealer. Check a specific car&#39;s VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener">nhtsa.gov/recalls</a>.{more}</p>'
def specs_html(x, y, name=''):
    out = ''
    s = x.get('safety')
    if s and s.get('variants'):
        rows = ''.join(f'<tr><td>{E(re.sub(r"^\d{4} ", "", v["desc"]).replace(name + " ", "").replace(name.split(" ", 1)[-1] + " ", ""))}</td><td>{stars(v["overall"])}</td><td>{stars(v["front"])}</td><td>{stars(v["side"])}</td><td>{stars(v["rollover"])}</td></tr>' for v in s['variants'])
        out += f'<h2>Crash tests</h2><p>Best NHTSA overall rating: {stars(s["best"]) if s.get("best") else "not rated"}</p><div class="tw"><table><thead><tr><th>Version</th><th>Overall</th><th>Frontal</th><th>Side</th><th>Rollover</th></tr></thead><tbody>{rows}</tbody></table></div><p class="note">NHTSA 5-star safety ratings (government crash tests).</p>'
    elif y >= 2011 and 'safety' in x:
        out += '<h2>Crash tests</h2><p>NHTSA didn&#39;t publish a 5-star crash test for this model year.</p>'
    m = x.get('mpg')
    if m:
        u = 'MPGe' if m.get('ev') else 'mpg'
        rng = lambda a, suf='': f'{a[0]:,}{suf}' if a[0] == a[1] else f'{a[0]:,}–{a[1]:,}{suf}'
        cost = f' About <b>{USD(m["cost"])}</b> a year in {"electricity" if m.get("ev") else "fuel"} (EPA estimate at today&#39;s prices).' if m.get('cost') else ''
        eng = f' Engines: {E(", ".join(m["engines"]))}.' if m.get('engines') and not m.get('ev') else ''
        out += f'<h2>Fuel economy</h2><p><b>{rng(m["comb"])} {u}</b> combined.{cost}{eng}</p><p class="note">EPA ratings from fueleconomy.gov, across the versions sold that year.</p>'
    return out
def ystar(fid, y):
    x = extra(fid, y); sf = x.get('safety') or {}; n = sf.get('best') or ((X2.get(fid, {}).get(str(y), {}).get('old') or {}).get('front'))
    return f'<i class="bst" title="NHTSA crash test: {n} of 5 stars" aria-label="{n} star crash test">{"★" * int(n)}</i>' if str(n).isdigit() else ''
# 11-05 (Elijah: "a different bar next to our old per year bars ... best based off YouTube"): data/yt_scores.json {fid: {year: {score, videos,
# topics, top}}} from 3 Lemon Index/data/yt/yt_score.py. Models that have it get a second bar per year (higher = YouTube likes it more), plus rows
# for older years that only YouTube covers (e.g. 1970s-90s Civics). Everything else is unchanged.
YTS = json.load(open('data/yt_scores.json', encoding='utf-8')) if os.path.exists('data/yt_scores.json') else {}
YT_MIN = 10   # 11-10 (Elijah: "remove YT rank from cars that don't have enough data, it's making them auto first place"): a year needs 10+ videos to be ranked
def yt_rankable(f, sc):
    """Years that may get a YouTube rank: 10+ videos, and (if 2010 or newer) an owner-complaint score too. Brand-new years only have
    launch reviews and no owner data yet, so they used to win #1 by default (e.g. the 2026 Civic)."""
    li = {v['y'] for v in f['years'] if v['ok']}
    return {int(y) for y, s in sc.items() if s.get('score') is not None and (s.get('videos') or 0) >= YT_MIN and (int(y) < 2010 or int(y) in li)}
def ybars_yt(f, cur, sc):
    mx = max(120, max(v['li'] for v in f['years'] if v['ok']) * 1.08); byy = {v['y']: v for v in f['years']}
    okr = yt_rankable(f, sc)
    ys = sorted(set(byy) | okr, reverse=True)   # 11-12 r2 (Jake: the Every year tab started at 1973): YouTube-only years show only when ranked
    got = sorted(((s['score'], s['videos'], int(y)) for y, s in sc.items() if int(y) in okr), reverse=True)
    if not got: got = [(50, 0, 0)]
    RK = {y: i + 1 for i, (_, _, y) in enumerate(got) if y}; lo, hi = got[-1][0], got[0][0]
    def row(y):
        v = byy.get(y); s = sc.get(str(y)) or {}; rk = RK.get(y); ss = s.get('score') if rk else None
        # bar = score stretched over the model's own range (YouTube scores sit close to 50); the number is the rank, #1 = YouTube's favorite year
        w = 8 + 92 * (ss - lo) / max(1, hi - lo) if ss is not None else 0
        tier = '' if rk is None else (' up' if rk <= len(RK) / 3 else ' dn' if rk > len(RK) * 2 / 3 else '')
        yt = (f'<span class="bt ytb{tier}"><i style="width:{w:.0f}%"></i></span><b class="ytn" title="YouTube rank {rk} of {len(RK)} {E(f['name'])} years">#{rk}</b>' if ss is not None else '<span class="bt ytb"></span><b class="ytn mute">·</b>')
        tip = f'{E(f["name"])} {y}: ' + (f'Lemon Index {v["li"]}' + (' (partial: too new)' if v.get('early') else '') if v and v['ok'] else f'{v["n"]} complaints, {"no sales figure to score" if NOSALES(v) else "too few sold to score"}' if v and v.get('low') else 'no complaint score') + (f'. YouTube rank #{rk} of {len(RK)} (score {ss}, {s["videos"]:g} videos)' if ss is not None else '. Not enough YouTube or owner data yet to rank')
        if v:
            return (f'<a class="b {CLS(v)}{" cur" if y == cur else ""}" href="{CARU(f, y)}" data-tip="{tip}."><span class="bn">{y}</span><span class="bt"><i style="width:{min(100, v["li"] / mx * 100) if v["ok"] else 0:.1f}%"></i>'
                    f'<em style="left:{100 / mx * 100:.1f}%"></em></span><b>{LIS(v)}</b>{yt}</a>')
        return f'<div class="b old" data-tip="{tip}."><span class="bn">{y}</span><span class="bt na"></span><b class="mute">·</b>{yt}</div>'
    return (f'<div class="bars yb yt2"><div class="bl yth2" aria-hidden="true"><span></span><span>Complaints <em>lower = better</em></span><span></span><span>YouTube rank <em>#1 = favorite</em></span><span></span></div>'
            + ''.join(row(y) for y in ys if y in byy) + '</div>'
            + (lambda old: f'<details class="yrs-more"><summary>Show {len(old)} older years ({old[-1]}–{old[0]}, YouTube reviews only, no complaint data)</summary><div class="bars yb yt2">{"".join(row(y) for y in old)}</div></details>' if old else '')([y for y in ys if y not in byy])
            + BARS_LEG(f, len(RK)))
def yt_rank_map(f):
    """{year: YouTube rank #} exactly as the year bars show it (rankable years only)."""
    sc = YTS.get(f['id']) or {}; okr = yt_rankable(f, sc)
    got = sorted(((s['score'], s['videos'], int(y)) for y, s in sc.items() if int(y) in okr), reverse=True)
    return {y: i + 1 for i, (_, _, y) in enumerate(got)}
TAB_FAIL = []
# The BeautifulSoup re-arrange costs ~80 s over ~2,300 pages, so results are cached outside the repo, keyed by the page body,
# the engine chart and tabbed.py + tabs code itself: an unchanged page skips the parse.
import pickle, tempfile
_TAB_CACHE = os.path.join(tempfile.gettempdir(), 'lemonindex_tabcache.pkl')
_TAB_SRC = hashlib.md5(b''.join(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), _f), 'rb').read() for _f in ('tabbed.py', 'year_slider.py'))).hexdigest()
try: _TAB_OLD = pickle.load(open(_TAB_CACHE, 'rb'))
except Exception: _TAB_OLD = {}
_TAB_NEW = {}
def tab_body(fid, y, body):
    """11-10: re-arrange a model/year page into the tabbed layout (tabbed.py); any page it can't parse keeps the old layout."""
    try: out = _tab_body(fid, y, body)
    except Exception as ex:
        TAB_FAIL.append(f'{fid}/{y or ""}: {type(ex).__name__} {ex}'); return body
    if fid not in FY: return out
    try:   # 11-12 carousel + year explorer + YouTube Overview (ycarousel.py), cached like the tab layout
        c = _yc_ctx(fid); k = hashlib.md5('|'.join(('yc', _YC_SRC, fid, str(y), out, json.dumps({a: b for a, b in c.items() if a != 'url'}, sort_keys=True, default=str),
                                                      json.dumps(YC.YB.get(fid)))).encode('utf-8')).hexdigest()
        if k in _TAB_OLD: _TAB_NEW[k] = _TAB_OLD[k]; return _TAB_OLD[k]
        r = YC.model_page(out, c) if y is None else YC.year_page(out, c, y); _TAB_NEW[k] = r; return r
    except Exception as ex:
        TAB_FAIL.append(f'ycarousel {fid}/{y or ""}: {type(ex).__name__} {ex}'); return out
import ycarousel as YC
_YC = {}; _YC_SRC = hashlib.md5(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ycarousel.py'), 'rb').read()).hexdigest()
def _yc_ctx(fid):
    """what ycarousel.py needs about one model: every year page with its picture and score, YouTube ranks, the fix/guide videos"""
    if fid in _YC: return _YC[fid]
    f = FY[fid]; mi = (YSL.model_img(fid) or {}).get('src')
    yrs = [{'y': v['y'], 'li': round(v['li']) if v['ok'] else None, 'url': CARU(f, v['y']), 'src': YSL.ai_src(fid, v['y']) or mi, 'gen': gen_of(f, v['y']), 'top': NICE(v['parts'][0][0]) if v.get('parts') else None} for v in f['years']]
    _YC[fid] = dict(fid=fid, name=f['name'], short=f['name'].split(' ', 1)[-1], years=yrs, yt_rank=yt_rank_map(f), ytr=YTR.get(fid), ytv=YTV.get(fid, []),
                    start=popular_year(f), url=lambda yy: CARU(f, yy))
    return _YC[fid]
def _tab_body(fid, y, body):
    f = FY.get(fid)
    if not f: return body
    li = {v['y']: v['li'] for v in f['years'] if v['ok']}; pages = {v['y'] for v in f['years']}
    ytr = yt_rank_map(f); _sc = YTS.get(fid) or {}
    eng = TAB.engine_chart(fid, f['name'], li, ytr, pages, cur=y, cls=lambda v: band(v)[0], ysc={yy: _sc[str(yy)]['score'] for yy in ytr}, part={v['y'] for v in f['years'] if v.get('early')})
    short = f['name'].split(' ', 1)[-1]
    k = hashlib.md5('|'.join((_TAB_SRC, fid, str(y), short, eng, body)).encode('utf-8')).hexdigest()
    if k in _TAB_OLD: _TAB_NEW[k] = _TAB_OLD[k]; return _TAB_OLD[k]
    if y is None:
        ld = ''.join(f'<script type="application/ld+json">{json.dumps(d)}</script>' for d in TAB.images_ld(fid, f['name']))
        out = TAB.transform_model(body, eng, short) + ld
    else: out = TAB.transform_year(body, eng, short)
    _TAB_NEW[k] = out; return out
def adv_body(path, body, fn=None):
    """11-10: the 'advp' template (no-sales model pages, Advanced pages) -> tabbed layout (tabbed.transform_adv); failures keep the old layout."""
    try:
        fn = fn or TAB.transform_adv
        _bm = re.match(r'^/cars/(bmw-[^/]+)/$', path); eng = ''
        if _bm and fn is TAB.transform_adv and TAB.bmw_groups(_bm.group(1)):   # 11-10: Years / Engines toggle on the no-sales BMW pages
            eng = TAB.engine_chart(_bm.group(1), globals().get('BFAM', {}).get(_bm.group(1), _bm.group(1)), {}, {}, set())
        k = hashlib.md5('|'.join((_TAB_SRC, fn.__name__, path, body, eng)).encode('utf-8')).hexdigest()
        if k in _TAB_OLD: _TAB_NEW[k] = _TAB_OLD[k]; return _TAB_OLD[k]
        _short = (globals().get('BFAM', {}).get(_bm.group(1), '') if _bm else '').replace('BMW ', '') or 'model'
        out = fn(body, _short, eng) if eng else fn(body, 'Page'); _TAB_NEW[k] = out; return out
    except Exception as ex:
        TAB_FAIL.append(f'{path}: {type(ex).__name__} {ex}'); return body
def yt_note(f):
    sc = YTS.get(f['id'])
    if not sc: return ''
    n = round(sum(s.get('videos') or 0 for s in sc.values())); yrs = sorted(int(y) for y, s in sc.items() if s.get('score') is not None)
    okr = yt_rankable(f, sc)
    if not okr: return ''
    best = max(okr, key=lambda y: (sc[str(y)]['score'], sc[str(y)]['videos'], y))   # 11-08: same tie-break as the bars' #1; 11-10: only rankable years
    return (f'<p class="yc-cap"><b>YouTube rank:</b> we read {n:,} YouTube videos about the {f["name"]}, {yrs[0]} to {yrs[-1]}, and ranked every year by how much they praise it '
            f'vs. how much they talk about problems. YouTube&#39;s favorite: <b>{best}</b>. Old cars rank lower partly because most of their videos are repair and restoration videos. A gray dot means not enough data yet: under 10 videos, or a new year with no owner complaints to compare.</p>')
# 11-08 (Elijah: "make the top of every car model page answer '<car> reliability' from the YouTube stuff, maybe a different ranking"):
# people search "Mercedes C-Class reliability", so the model page opens with that question, a plain answer and a 3-tile scorecard.
# YouTube scores climb with newer model years for every car (old cars = repair videos), so each year is compared with the median
# of every car of the SAME model year (>= 10 videos). Model rank = video-weighted average of those gaps. It measures how positively
# owners and reviewers talk, not a failure rate, and the page says so. (11-12: the recommended year is the one with the fewest complaints, see rec_year.)
def _yt_base():
    by = defaultdict(list)
    for d in YTS.values():
        for y, s in d.items():
            if s.get('score') is not None and (s.get('videos') or 0) >= 10 and int(y) >= 2000: by[int(y)].append(s['score'])
    return {y: sorted(v)[len(v) // 2] if len(v) % 2 else sum(sorted(v)[len(v) // 2 - 1:len(v) // 2 + 1]) / 2 for y, v in by.items() if len(v) >= 5}
YTB = _yt_base()
def yt_adj(fid):
    return {int(y): s['score'] - YTB[int(y)] for y, s in YTS.get(fid, {}).items() if s.get('score') is not None and (s.get('videos') or 0) >= 10 and int(y) in YTB}
def _yt_rank():
    m = {}
    for fid, d in YTS.items():
        a = yt_adj(fid)
        if len(a) >= 4:
            w = {y: d[str(y)]['videos'] for y in a}; m[fid] = (sum(a[y] * w[y] for y in a) / sum(w.values()), round(sum(w.values())))
    order = sorted(m, key=lambda k: -m[k][0])
    return {fid: (i + 1, len(order), m[fid][1]) for i, fid in enumerate(order)}
YTR = _yt_rank()
def rel_answer(f, c, snm, rec, kind, avoid):
    """('Yes.', one plain sentence) for 'Is the <car> reliable?', from complaints first, YouTube second."""
    li = c['li']
    word = 'Yes, very.' if li < 50 else 'Yes.' if li < 85 else 'About average.' if li <= 115 else 'Not really.'
    _r = YTR.get(f['id'])
    if _r and li <= 115:   # NHTSA counts complaints only; when YouTube owners clearly disagree, don't oversell
        top, low = _r[0] <= _r[1] / 3, _r[0] > _r[1] * 2 / 3
        word = ('Mostly.' if li < 85 else 'It&#39;s mixed.') if low else ('Yes, very.' if li < 50 and top else 'Yes.' if li < 85 else 'Mostly.' if top else word)
    comp = (f'It draws {plain(li)}' if li < 90 else 'It draws about as many complaints as the average car' if li <= 110
            else f'It draws {li / 100:.1f}× the average car&#39;s complaints'.replace('.0×', '×'))
    r = YTR.get(f['id']); yt = ''
    if r:
        rk, n, _ = r; good_c = li <= 110
        if rk <= n / 3: yt = (', and' if good_c else ', but') + ' YouTube owners sound happier with it than with most cars its age'
        elif rk > n * 2 / 3: yt = (', but' if good_c else ', and') + ' YouTube owners complain about it more than about most cars its age'
        else: yt = ', and YouTube owners rate it about average for its age'
    AND = lambda xs: ', '.join(map(str, xs[:-1])) + (' and ' if len(xs) > 1 else '') + str(xs[-1])
    tail = '.'
    if rec and kind == 'least': tail = f'. No year beat the average car. The year with the fewest complaints, <b>{rec["y"]}</b>, still drew {x_avg(rec["li"])} the average.'
    elif rec: tail = f'. Fewest complaints: <b>{rec["y"]}</b>.'
    av = sorted(v['y'] for v in avoid if not rec or v['y'] != rec['y'])[:3] if len(scored(f)) >= LIST_MIN else []
    if av: tail += f' Most complaints: <b>{AND(av)}</b>.'
    return word, comp + yt + tail
def rel_top(f, c, snm, ys, sc, rec, kind, worst, avoid, qn=None):
    word, ans = rel_answer(f, c, snm, rec, kind, avoid)
    vc, vw = verdict(c['li']); tiles = [f'<div class="rs {vc}"><small>Owner complaints</small><b>{E(vw)}</b><span>Lemon Index {c["li"]} · {E(c["years"].replace("-", "–"))} · 100 = average</span></div>']
    r = YTR.get(f['id'])
    if r:
        rk, n, vids = r; cl = 'good' if rk <= n / 3 else 'bad' if rk > n * 2 / 3 else 'mid'
        tiles.append(f'<div class="rs {cl}"><small>YouTube owners</small><b>#{rk} <i>of {n}</i></b><span>vs. cars the same age · {vids:,} videos</span></div>')
    if rec and kind == 'good': tiles.append(f'<a class="rs good rs-rec" href="{CARU(f, rec["y"])}"><small>Fewest complaints</small><b>{rec["y"]}</b><span>{E(short(rec["li"]))} · fewest per car sold</span></a>')
    elif rec: tiles.append(f'<a class="rs rs-rec" href="{CARU(f, rec["y"])}"><small>Fewest complaints</small><b>{rec["y"]}</b><span>{E(short(rec["li"]))}: no year beat the average car</span></a>')
    if not r: tiles.append(f'<a class="rs bad" href="{CARU(f, worst["y"])}"><small>Most complaints</small><b>{worst["y"]}</b><span>{E(short(worst["li"]))}</span></a>' if worst and worst['li'] > 110 and (not rec or worst['y'] != rec['y']) else
                           f'<div class="rs"><small>Years to avoid</small><b>None</b><span>no year far above average</span></div>')
    a = yt_adj(f['id']); last = max(v['y'] for v in sc); new = sorted((y for y in a if y > last), key=lambda y: -a[y])
    newer = (f'<p class="rs-new">Looking at a {min(new)} or newer? Those are too new for a full complaint score (any score shown is partial, in gray), but YouTube owners like the <a href="#years">{new[0]}</a> best.</p>'
             if len(new) >= 2 else '')
    # 11-12 search titles: the H1 says "<model> reliability" (what people search); the question opens the answer line
    return (f'<h1 class="rel-h">{E(qn or snm).replace("-", "-⁠")} reliability.</h1><p class="ans rel-a"><b>Is it reliable? {word}</b> {ans}</p>', f'<div class="rsc">{"".join(tiles)}</div>{newer}', (word + ' ' + html.unescape(re.sub('<[^>]+>', '', ans))))
# 11-12 r2 (Carlos, Liam, Jake): year lists run newest first; gray = partial (2023+) or unscored; ranks say what they rank
def BARS_LEG(f, yt=0):
    part = any(v.get('early') for v in f['years'])
    return ('<p class="yc-cap lfa-leg">Newest year first. Red = worse than average, gray = about average'
            + (', too new (2023+: a partial score, marked &ldquo;partial&rdquo;)' if part else '') + ' or too few complaints to score.'
            + (f' <b>#1, #2…</b> = that year&#39;s YouTube rank among the {yt} {E(f["name"])} years with enough videos (#1 = the year owners and reviewers talk about most positively). It is not a reliability rank.' if yt else '') + '</p>')
LFA_JS = '<script src="/assets/lfa.js?v=2" defer></script>'   # 11-12 r2: year lists open on the reader's year, match-up "your years"
def ybars(f, cur=None):
    out = _ybars(f, cur)
    if cur is None or out.count('class="b ') < 13: return out
    return out.replace('<div class="bars yb', f'<div data-cur="{cur}" class="lfa-sc bars yb', 1) + LFA_JS   # a long list scrolls inside its box to the page's year
def _ybars(f, cur=None):
    if YTS.get(f['id']): return ybars_yt(f, cur, YTS[f['id']])
    mx = max(120, max(v['li'] for v in f['years'] if v['ok']) * 1.08)
    return (f'<div class="bars yb"><div class="bl" aria-hidden="true"><span></span><span class="al" style="--a:{100 / mx * 100:.1f}%">average car = 100</span><span></span></div>'
            + ''.join(f'<a class="b {CLS(v)}{" cur" if v["y"] == cur else ""}{" early" if v.get("early") else ""}" href="{CARU(f, v["y"])}" data-tip="{E(f["name"])} {v["y"]}: ' + (f'Lemon Index {v["li"]}, {plain(v["li"])}' if v['ok'] else f'{v["n"]} complaints, {"no sales figure to score" if NOSALES(v) else "too few sold to score"}' if v.get('low') else f'only {v["n"]} complaints, too few to score') + f'."><span class="bn">{v["y"]}</span><span class="bt"><i style="width:{min(100, v["li"] / mx * 100) if v["ok"] else 0:.1f}%"></i><em style="left:{100 / mx * 100:.1f}%"></em></span><b>{LIS(v)}</b><small>{("partial · " if v.get("early") else "") + short(v["li"]) if v["ok"] else "few complaints"}</small></a>' for v in sorted(f['years'], key=lambda v: -v['y'])) + '</div>' + BARS_LEG(f))
# 10-31 idea 5: "X vs Y" pages for the best-selling rivals in each type (people search "camry vs accord reliability").
FY = {f['id']: f for f in YEARS}
RIVALS = defaultdict(list); PAIRS = []
for seg, top in (('car', 10), ('suv', 10), ('truck', 7), ('minivan', 5)):
    ids = [c['id'] for c in sorted((c for c in CARS if c['seg'] == seg and c['id'] in FY), key=lambda c: -c['sold'])][:top]
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            PAIRS.append((a, b)); RIVALS[a].append(b); RIVALS[b].append(a)
# 11-05 keyword map: add every "X vs Y" pair with 1,000+ monthly searches that the sales-rank pairs above missed
for a, b, v, _ in json.load(open('data/kw_pairs.json', encoding='utf-8')) if os.path.exists('data/kw_pairs.json') else []:
    if v >= 1000 and a in FY and b in FY and (a, b) not in PAIRS and (b, a) not in PAIRS:
        PAIRS.append((a, b)); RIVALS[a].append(b); RIVALS[b].append(a)
# 11-12 dead links: the compare pages below skip pairs with under 2 scored years in common (Town & Country vs Pacifica), so drop them here too
_oky = lambda i: {v['y'] for v in FY[i]['years'] if v.get('ok')}
_nopair = [p for p in PAIRS if len(_oky(p[0]) & _oky(p[1])) < 2]
for a, b in _nopair: PAIRS.remove((a, b)); RIVALS[a].remove(b); RIVALS[b].remove(a)
CMPU = lambda a, b: f'/compare/{a}-vs-{b}/'
cmpu = lambda a, b: CMPU(a, b) if (a, b) in PAIRS else CMPU(b, a)
# 11-12 internal links (research #6): year pages linked only to their own model's years. A small "Related" list at the end of every
# model-year page, all from the data: the nearest-year cars of the same type whose top owner complaint is the same system, one same-year
# car of the same type with a lower Lemon Index, the model's top compare page, and that type's most-reliable list. linkgraph.py
# (end of build) reports click depth, inbound links and orphans to 3 Lemon Index/data/linkgraph/latest.md.
_LXSEG = {'car': ('cars', 'cars'), 'suv': ('suvs', 'SUVs'), 'truck': ('trucks', 'trucks'), 'minivan': ('minivans', 'minivans')}
_LXIX = {}
def LX_HTML(fid, y):
    f = FY.get(fid); c = BYNAME.get(f['name']) if f else None
    v = next((w for w in f['years'] if w['y'] == y), None) if f else None
    if not (c and v): return ''
    if not _LXIX:
        for g in YEARS:
            for w in g['years']:
                if w.get('ok') and g['name'] in BYNAME: _LXIX.setdefault((BYNAME[g['name']]['seg'], w['y']), []).append((g, w))
    seg = c['seg']; out = []; used = {fid}
    peers = [p for yy in range(y - 2, y + 3) for p in _LXIX.get((seg, yy), []) if p[0]['id'] != fid]
    top = NICE(v['parts'][0][0]) if v.get('parts') else ''
    if top and top != 'other':
        for g, w in sorted((p for p in peers if p[1].get('parts') and NICE(p[1]['parts'][0][0]) == top), key=lambda p: (abs(p[1]['y'] - y), -p[1]['n'])):
            if g['id'] in used: continue
            used.add(g['id']); out.append((CARU(g, w['y']), f'{w["y"]} {g["name"]}', f'top complaint is also the {top}'))
            if len(out) == 2: break
    if v.get('ok'):
        for g, w in sorted((p for p in peers if p[1]['y'] == y and p[1]['li'] < v['li'] and p[0]['id'] not in used), key=lambda p: p[1]['li'])[:1]:
            used.add(g['id']); out.append((CARU(g, y), f'{y} {g["name"]}', f'fewer complaints per car sold (Lemon Index {w["li"]})'))
    for o in RIVALS.get(fid, [])[:1]: out.append((cmpu(fid, o) + f'#y{y}', f'{f["name"]} vs {FY[o]["name"]}', f'{y} and its neighbours side by side'))   # 11-12 r2: opens on this year (assets/lfa.js)
    if seg in _LXSEG: out.append((f'/best/most-reliable-{_LXSEG[seg][0]}/', f'Most reliable {_LXSEG[seg][1]}', 'ranked by owner complaints'))
    if not out: return ''
    return ('<link rel="stylesheet" href="/assets/lx.css?v=1"><nav class="lx" aria-label="Related"><h2 class="lx-h">Related</h2><ul class="lx-l">'
            + ''.join(f'<li><a href="{u}">{E(t)}</a><span>{E(s)}</span></li>' for u, t, s in out) + '</ul></nav>')
# ---- 11-02 year-page redesign (Elijah: "less text, bars and charts, numbers that matter, built for someone looking at their own car or one they want to buy")
NICE = lambda p: {'service brakes, hydraulic': 'brakes', 'brakes': 'brakes', 'service brakes, electric': 'brakes (electric)', 'service brakes, air': 'brakes', 'power train': 'transmission & drivetrain',
                  'unknown or other': 'other', 'vehicle speed control': 'speed control', 'equipment': 'equipment & accessories',
                  'fuel or ev drive system': 'fuel system'}.get(p.lower(), p.lower())   # 11-12 round 2 (Carlos): gas cars said "fuel or ev drive system" (scope_filter.py renames it per car first)
def verdict(li): return band(li)
def meter(li):
    mx = 250; pos = min(li, mx) / mx * 100
    return (f'<div class="ym" role="img" aria-label="Lemon Index {li}; the average car is 100"><div class="ym-bar"><i class="ym-avg" style="left:{100 / mx * 100:.1f}%"><span>average car</span></i>'
            f'<i class="ym-pin" style="left:{pos:.1f}%"><b>{li}{"+" if li > mx else ""}</b></i></div><div class="ym-ends"><span>fewer complaints</span><span>more complaints</span></div></div>')
def timeline(m, comps, tot=None):
    mx = 200000; P = lambda n: f'{min(n, mx) / mx * 100:.1f}%'
    ticks = ''.join(f'<span style="left:{k / mx * 100:.0f}%">{k // 1000}K</span>' for k in (0, 50000, 100000, 150000, 200000))
    seen = set(); cc = [c for c in comps if c[4] >= 15 and not (NICE(c[0]).split(' (')[0] in seen or seen.add(NICE(c[0]).split(' (')[0]))][:3]
    top = ''.join(f'<li><b>{E(NICE(c[0]))}</b> complaints mostly came at <b>{c[2] // 1000}K–{c[3] // 1000}K</b> miles <small class="km">({round(c[2] * 1.609344 / 1000)}K–{round(c[3] * 1.609344 / 1000)}K km)</small></li>' for c in cc)
    return (f'<section class="yc"><h2>When owners reported problems. <span class="h2s">From owner complaints to the government.</span></h2><div class="tl"><div class="tl-bar"><i class="tl-band" style="left:{P(m["p25"])};width:calc({P(m["p75"])} - {P(m["p25"])})"></i>'
            f'<i class="tl-mid" style="left:{P(m["median"])}"><b>half by {m["median"] // 1000}K</b></i></div><div class="tl-ticks">{ticks}</div></div>'
            f'<p class="yc-cap">Most owners who filed a complaint with NHTSA had <b>{m["p25"] // 1000}K to {m["p75"] // 1000}K miles</b> ({round(m["p25"] * 1.609344 / 1000)}K to {round(m["p75"] * 1.609344 / 1000)}K km) on the car ({m["n"]:,} of {'all ' + format(tot, ',') + ' ' if tot and tot >= m['n'] else 'the '}complaints filed so far listed the miles). This shows when people who had a problem reported it, not the odds that your car will have it.</p>'
            + (f'<ul class="tl-top">{top}</ul>' if top else '') + '</section>')
X2 = _load('data/extras2.json'); X2.update(_load('data/extras2_new.json'))   # 11-11 new models: repair notes, investigations, safety tech
exec(open('scope_filter.py', encoding='utf-8').read())   # 11-12 round 2 (fix B): each page keeps to its own model, years and fuel (heavy-duty/Lightning off the half-ton pages, "fuel system", bulletin quotes)
TR = _load('data/trans.json')   # transmission complaints per model-year (data_trans.py)
_tr_ok = lambda f: sum(1 for v in f['years'] if (TR.get(f['id'], {}).get(str(v['y'])) or {}).get('rate') is not None) >= 3   # 11-12: trans_body() builds the page only with 3+ rated years; link only then (was a 404 on the Audi Q3/A4)
PH = _load('data/photos.json')   # exact-year Wikimedia Commons cutouts (data_photos.py), {fid: {year: {src, author, license, page, w, h}}}
LIC = {'CC BY-SA 4.0': 'https://creativecommons.org/licenses/by-sa/4.0/', 'CC BY-SA 3.0': 'https://creativecommons.org/licenses/by-sa/3.0/', 'CC BY 4.0': 'https://creativecommons.org/licenses/by/4.0/'}
# 11-08 (Elijah: "the Wikimedia credit under every photo is long"): shortest credit each license allows. Public domain / CC0 = just
# "Wikimedia Commons". CC BY / BY-SA must name the author and say we changed it (background removed); the link goes to the photo's
# Commons page, which states the license (CC 4.0 s3(a)(2) allows attribution through a linked page).
def pcap(ph, who):
    lic = ph.get('license', ''); pg = E(ph.get('page', ''))
    if re.search(r'cc0|public domain|^pd', lic, re.I): return f'Photo: <a href="{pg}" rel="noopener">Wikimedia Commons</a>'
    return f'Photo: <a href="{pg}" rel="noopener" title="{E(lic)}">{E(who)} / Wikimedia Commons</a>, edited'
def car_photo(fid, y, name):
    ph = PH.get(fid, {}).get(str(y))
    if not ph: return ''
    who = ph['author'].split('\ufffd')[0].strip().replace('National Highway Traffic Safety Administration', 'NHTSA'); lic = ph['license']
    lic_h = f'<a href="{LIC[lic]}" rel="noopener license">{E(lic)}</a>' if lic in LIC else E(lic)
    return (f'<figure class="yph"><img src="{ph["src"]}"{rset(ph["src"], SZ_ONE)} alt="{y} {E(name)}" width="{ph["w"]}" height="{ph["h"]}" fetchpriority="high">'
            + YSL.info(f'{pcap(ph, who)} ({lic_h})') + '</figure>')
def year_photo(f, y):
    if YSL.model_img(f['id']): return YSL.model_hero_html(f['id'], f['name'])   # 11-10: the model's AI illustration beats any Commons photo
    ys = PH.get(f['id'], {}); nm = SNM(f)
    if str(y) in ys: return car_photo(f['id'], y, f['name'])
    near = sorted(ys, key=lambda k: abs(int(k) - y))
    ph, shown = (ys[near[0]], int(near[0])) if near and (abs(int(near[0]) - y) <= 3 or not MPH.get(f['id'])) else (MPH.get(f['id']), None)
    if not ph: return ''
    if shown is None: m = re.search(r'(19|20)\d\d', ph.get('title', '')); shown = int(m.group()) if m else None
    lic = ph.get('license', ''); who = (ph.get('author') or '').split('\ufffd')[0].strip()
    lic_h = f'<a href="{LIC[lic]}" rel="noopener license">{E(lic)}</a>' if lic in LIC else E(lic)
    note = f'{shown} shown · ' if shown and shown != y else ''
    return (f'<figure class="yph"><img src="{ph["src"]}"{rset(ph["src"], SZ_ONE)} alt="{E(nm)}" width="{ph["w"]}" height="{ph["h"]}" fetchpriority="high">'
            + YSL.info(f'{note}{pcap(ph, who)} ({lic_h})') + '</figure>')
def car_hero(f, y):   # 11-10 (Elijah): "if a car has an AI image, remove the wiki image"
    return YSL.ai_year_html(f['id'], y, f['name'], hero=True) or year_photo(f, y)
def clean_tsb(t):
    """An automaker repair note in plain words: drop the 'HONDA:' prefix and 'Some 2017-2018 X built before ... may exhibit', fix SHOUTING, skip shop-tool notes."""
    t = t.replace('�', '').replace('…', '').strip()
    if re.search(r'(VCM|IDS|diagnostic|scan tool|procedure|labor|warranty claim|technician|dealer should|service manual|part number)', t, re.I): return None
    t = RCQ._BOILER.sub('', t.strip('"')).strip()   # 11-12 round 2 (Jake, Liam): "Dealer message - American Honda Motor Co., Inc" says nothing
    if re.fullmatch(r'(?i)(dealer message|service bulletin|tsb|techline summary article)?[\s-]*(american honda motor co\.?,? inc\.?)?[\s.]*', t): return None
    t = re.sub(r'^[A-Z][A-Z &-]{1,20}:\s*', '', t)
    t = re.sub(r'^.*?may (exhibit|experience|have|display|produce|develop)\s+(an?\s+|the\s+)?', '', t, flags=re.I)
    if t.isupper() or sum(c.isupper() for c in t) > len(t) * .6: t = t.lower()
    t = t.strip(' ,.;:-')
    t = re.sub(r'(\s+(coming from|from|on|in|when|while|at|with|and|or|to|the|a|an|of|that|during|after|before))+$', '', t, flags=re.I).strip(' ,.;:-')
    if len(t) < 12: return None
    t = t[0].upper() + t[1:]
    return (t[:95].rsplit(' ', 1)[0] + '…') if len(t) > 97 else t
MAKER = lambda name: (BYNAME[name]['brand'] if name in BYNAME else name.split(' ')[0]).replace('Chevrolet', 'Chevy')   # 11-12: the brand, not the first word ("Mazda3 sent dealers")
# ---- 11-12 (6 customer tests, Elijah: fix them all): ONE recommended year per car, picked the same way on the model page, every year page,
# the Q&A, the compare pages and the Overview cards. It's the year with the FEWEST OWNER COMPLAINTS per car sold (never called "safest":
# the index counts complaints, it isn't a crash-safety rating). Pre-2010 scores are rough, so 2010+ years are used when the model has any.
# A year is only "good" at or under the average car (110). A model with no such year gets a "least bad" year, which is never worse than
# the model's own average. Best and avoid lists can't overlap, and both hide when fewer than 5 years are scored.
LIST_MIN = 5
def scored(f): return [v for v in f['years'] if v['ok'] and not v.get('early')]
def year_pool(f):
    sc = scored(f); p = [v for v in sc if v['y'] >= 2010]
    return p or sc
def model_li(f): c = BYNAME.get(f['name']); return c['li'] if c else None
def good_years(f): return sorted([v for v in year_pool(f) if v['li'] <= 110], key=lambda v: (v['li'], -v['y']))
def avoid_years(f):
    """Years far above the average car AND above the model's own average (so a weak model's least-bad year never shows as one to avoid)."""
    cut = max(110, model_li(f) or 0) if not good_years(f) else 110
    return sorted([v for v in year_pool(f) if v['li'] > cut], key=lambda v: -v['li'])
def rec_year(f):
    """(year dict, 'good' | 'least') or (None, None): the one year the site recommends for this model."""
    g = good_years(f)
    if g: return g[0], 'good'
    mli = model_li(f); lb = [v for v in year_pool(f) if mli is None or v['li'] <= mli]
    return (min(lb, key=lambda v: (v['li'], -v['y'])), 'least') if lb else (None, None)
def worst_year(f): p = year_pool(f); return max(p, key=lambda v: v['li']) if p else None
def popular_year(f):
    """11-12 (Jess: the CR-V page opened on 2001): the model page opens on a popular USED year: the best seller among cars 5-11 years old."""
    ty = int(TODAY[:4]); ys = [v for v in f['years'] if v.get('sold')]
    win = [v for v in ys if ty - 11 <= v['y'] <= ty - 5]
    if win: return max(win, key=lambda v: v['sold'])['y']
    pool = ys or f['years']; return min(pool, key=lambda v: (abs(v['y'] - (ty - 8)), -v['y']))['y'] if pool else None
def ok_pick(f, v):
    """May this year be suggested as a better buy? Good years (<= 110); for a model with no good year, years at or under the model's own average."""
    if v['li'] <= 110: return True
    mli = model_li(f); return not good_years(f) and mli is not None and v['li'] <= mli
def gen_of(f, y): return ((YSL.AIY.get(f['id']) or {}).get(str(y)) or {}).get('gen')
def near_pick(f, y):
    """The better buy for someone looking at year y: the lowest-complaint year within 3 model years (same generation when we know it).
    Returns (year dict, 'near') / (this year's dict, 'self') when y is already the best nearby / (model's rec year, 'model') / (None, None)."""
    cur = next((v for v in f['years'] if v['y'] == y), None)
    cand = [v for v in scored(f) if abs(v['y'] - y) <= 3 and ok_pick(f, v)]
    g = gen_of(f, y); same = [v for v in cand if g and gen_of(f, v['y']) == g]
    pool = same or cand
    if pool:
        b = min(pool, key=lambda v: (v['li'], abs(v['y'] - y)))
        if cur and cur['ok'] and not cur.get('early') and b['y'] != y and cur['li'] <= b['li']: b = cur
        if b['y'] == y: return b, 'self'
        if not (cur and cur['ok']) or b['li'] < cur['li']: return b, 'near'
    r, _ = rec_year(f)
    if r and r['y'] != y and (not (cur and cur['ok']) or r['li'] < cur['li']): return r, 'model'
    return None, None
def x_avg(mli): return f'{mli / 100:.1f}×'.replace('.0×', '×')
def model_context(f, v, y):
    """'A good year of a weak model' (or the reverse), in one plain sentence; '' when the year and its model agree."""
    mli = model_li(f)
    if not v['ok'] or mli is None: return ''
    if v['li'] <= 110 and mli > 130: return f'{y} is one of the better years of a model that draws {x_avg(mli)} the average car&#39;s complaints.'
    if v['li'] > 130 and mli < 90: return f'{y} is one of the weaker years of a model that usually draws {plain(mli)}.'
    return ''
def buy_verdict(f, v, y):
    """(class, band word, reason) from the year's score; None when unscored. 11-12 r2: the band words (band()), never 'Worth a look' on a
    worse-than-average year; a 2023+ year says it is too new and its score is partial."""
    if not v['ok']: return None
    li = v['li']
    cl, lab = ('na', PARTIAL) if v.get('early') else band(li)
    why = f'It drew {"about the average car&#39;s complaints" if 90 <= li <= 110 else plain(li)}' + (' so far' if v.get('early') else ' in its first 3 years')
    if v['parts']: why += f', most about {NICE(v["parts"][0][0])}'
    why += '.'
    ctx = model_context(f, v, y)
    return cl, lab, why + (' ' + ctx if ctx else '')
def _mgroups(lines):
    """[(60000, t), (100000, t), (150000, u)] -> [([60000, 100000], t), ([150000], u)]: one row per distinct meaning."""
    out = []
    for k, t in lines:
        if out and out[-1][1] == t: out[-1][0].append(k)
        else: out.append(([k], t))
    return out
def _kl(ks): ks = [f'{k // 1000}K' for k in ks]; return ks[0] if len(ks) == 1 else ', '.join(ks[:-1]) + ' and ' + ks[-1]
def _mi_r(n): return f'{int(round(n, -3)):,}' if n >= 10000 else f'{int(round(n, -2)):,}' if n >= 1000 else f'{int(n):,}'
# 11-12 round 2 (Liam, Ontario; 14% of the audience is Canadian): every mileage also in km
def _km(n): return f'{round(n * 1.609344 / 1000):,}K km' if n >= 1000 else f'{round(n * 1.609344):,} km'
def _kmK(ks): ks = [f'{round(k * 1.609344 / 1000)}K' for k in ks]; return (ks[0] if len(ks) == 1 else ', '.join(ks[:-1]) + ' and ' + ks[-1]) + ' km'
def mileage_guide(x):
    """'Most problems on this year show up around X-Y miles' + what that means at 60K / 100K / 150K, from the mileage owners typed into
    their complaints. None of it is a prediction for one car. Returns ((headline, [(miles, meaning)]), '') or (None, why there's no answer)."""
    m = x.get('miles')
    if not m: return None, 'No complaints for this year listed a mileage, so we can&#39;t say when problems show up.'
    if m.get('n', 0) < 20: return None, f'Only {m.get("n", 0)} complaints listed a mileage: too few to say when problems show up.'
    lo, hi = m['p25'], m['p75']
    def at(k):
        if k < lo: return 'still under the range where most problems showed up, so they may be ahead of it'
        if k <= hi: return 'right in the range where most owners reported problems'
        return 'past the range where most problems showed up: it has likely had them or dodged them, so repair records matter most'
    tot = (x.get('sev') or {}).get('total')   # 11-12 r2 (Jake: 389 vs 495 vs 1,083 unlabelled): say which slice each count is
    head = (f'Most problems on this year showed up between <b>{_mi_r(lo)}</b> and <b>{_mi_r(hi)}</b> miles <span class="km">({_mi_r(lo * 1.609344)}–{_mi_r(hi * 1.609344)} km)</span> '
            + (f'(the middle half of the {m["n"]:,} complaints, of all {tot:,} filed so far, that listed a mileage).' if tot and tot >= m['n'] else f'(the middle half of the {m["n"]:,} complaints that listed a mileage).'))
    return (head, [(k, at(k)) for k in (60000, 100000, 150000)]), ''
# what to ask the seller about each problem area (real items only: a question appears only when that area is one of the year's top problems)
ASKQ = [(r'transmission|power train|drivetrain', 'Any slipping, hard or late shifts, or a transmission warning light? Ask for transmission fluid service records.'),
        (r'^engine', 'Any oil burning, leaks or check-engine lights? Ask for oil-change records.'),
        (r'electrical', 'Do all the lights, screens and power features work? Has the battery, alternator or any wiring been replaced?'),
        (r'brake', 'Do the brakes feel even, with no ABS or brake warning light? When were the pads and brake fluid last done?'),
        (r'steering', 'Any steering noise, wander or power-steering warning? Has the steering rack or pump been replaced?'),
        (r'suspension', 'Any clunks over bumps or uneven tire wear? Were struts, shocks or control arms replaced?'),
        (r'airbag', 'Is the airbag light off, and were any airbag recalls done?'),
        (r'fuel|ev drive', 'Any fuel smell, stalling or hard starts? On a hybrid or EV, any reduced-power warning or battery work?'),
        (r'speed control', 'Does it accelerate and hold speed smoothly, with no surging or stalling?'),
        (r'emergency braking|collision', 'Has it ever braked hard for no reason? Ask whether the safety-system software was updated.'),
        (r'lane assist', 'Do the lane-keeping warnings work without false alerts?'),
        (r'wiper|visibility', 'Do the wipers, washers, defrost and mirrors all work?'),
        (r'lights', 'Do all the headlights, taillights and turn signals work?'),
        (r'structure', 'Any rust or damage underneath, or doors and hatches that don&#39;t close right?'),
        (r'seat belt', 'Do all the seat belts latch and retract?'),
        (r'seat', 'Do the seats adjust, heat and lock in place properly?'),
        (r'stability', 'Is the stability-control light off on a test drive?')]
# 11-12 round 2 (Liam, Ontario): Transport Canada runs Canada's recalls; NHTSA numbers are U.S. campaigns
TC_DB = 'https://wwwapps.tc.gc.ca/Saf-Sec-Sur/7/VRDB-BDRV/search-recherche/menu.aspx?lang=eng'
TC_VIN = 'https://tc.canada.ca/en/road-transportation/defects-recalls-vehicles-tires-child-car-seats/find-vehicle-tire-child-car-seat-manufacturer'
CA_RECALL = (f'<p class="yc-cap ca-note"><b>In Canada?</b> These are U.S. (NHTSA) recalls. Transport Canada runs its own, with its own numbers: '
             f'<a href="{TC_DB}" rel="noopener nofollow" target="_blank">search Transport Canada recalls</a> or <a href="{TC_VIN}" rel="noopener nofollow" target="_blank">check a VIN on the maker&#39;s Canadian recall site</a>. '
             'The complaints on this page come from U.S. owners; the same models sold in Canada share the same parts.</p>')
# 11-12 round 2 (Jake: A/C was the #1 repair bill, 117 owners, but no seller question asked about it): questions from the year's top
# repair-bill areas too (repair_costs.json, the same generation window as its "What repairs cost" block)
ASKB = {'A/C & heat': 'Does the A/C blow cold and the heat work? Ask whether the A/C compressor or condenser was replaced.',
        'Cooling': 'Any overheating, coolant smell or leaks? Ask whether the water pump or radiator was replaced.',
        'Doors, locks & windows': 'Do all the doors lock from the key fob, and do all the windows go up and down?',
        'Exhaust & emissions': 'Any check-engine light, exhaust smell or rattle underneath? Ask whether the catalytic converter was replaced.',
        'Screen, radio & camera': 'Does the screen respond, and does the backup camera come on every time?',
        '4x4 & axles': 'Does 4WD engage cleanly, with no clunks or grinding? Ask for transfer-case and differential fluid records.',
        'Hybrid / EV battery': 'Any hybrid or EV battery warning, or less range than it should have? Ask for a battery health report.'}
ASKB_PAT = {'Engine': r'^engine', 'Transmission': r'transmission|power train|drivetrain', 'Electrical': r'electrical', 'Brakes': r'brake', 'Steering': r'steering',
            'Suspension': r'suspension', 'Airbags': r'airbag', 'Fuel system': r'fuel|ev drive'}
def rc_window(fid, y):
    """the model years a year page's repair-bill block covers (the YouTube study's generation when there is one, else y-2..y+2)"""
    d = next((e for e in YTV.get(fid, []) if e['years'] is not None and y in e['years']), None)
    return (min(d['years']), max(d['years'])) if d and d.get('years') else (y - 2, y + 2)
def bill_areas(fid, y, k=2):
    y0, y1 = rc_window(fid, y)
    return [a for a in RCQ.areas(fid, y0, y1) if a[1] >= RCQ.MIN_N][:k]
# ---- 11-12 round 2 (Jake, Ryan: "what breaks" was only categories): the specific parts owners name most (data_top_fails.py)
TOPF = _load('data/top_fails.json')
TOPF_SYMPTOM = {'Engine stalling', 'A/C blowing warm air', 'Rough or hard shifting', 'Throttle body / loss of power', 'Coolant leak / overheating', 'Phantom braking (collision system)', 'Rust / frame corrosion'}   # symptoms, not one part: no single repair bill
def top_fails_html(f, y, nm):
    d = (TOPF.get(f['id']) or {}).get(str(y))
    if not d: return ''
    tops = d['top']; names = {t['t'] for t in tops}
    if names & {'A/C compressor', 'A/C condenser'}: tops = [t for t in tops if t['t'] != 'A/C blowing warm air']
    tops = tops[:3]
    def li(t):
        mi = t.get('mi'); c = t.get('cost')
        bits = [f'<span class="tf-n">{t["n"]:,} complaint{"" if t["n"] == 1 else "s"}</span>']
        if mi: bits.append(f'<span>mostly at {_mi_r(mi[0])}–{_mi_r(mi[2])} miles <small class="km">({_mi_r(mi[0] * 1.609344)}–{_mi_r(mi[2] * 1.609344)} km)</small></span>')
        if c and t['t'] not in TOPF_SYMPTOM: bits.append(f'<span>one repair: <b>{RCQ._r(c[0])}–{RCQ._r(c[2])}</b> <small>USD, middle half of {c[3]} bills owners named</small></span>')
        return f'<li><b class="tf-t">{E(t["t"])}</b>' + ''.join(bits) + '</li>'
    return (f'<section class="yc ytf" id="top-fails"><h2>What breaks most on the {y} {nm}</h2><ol class="tf-l">{"".join(li(t) for t in tops)}</ol>'
            f'<p class="yc-cap">Specific parts named in the {d["all"]:,} owner complaints filed with NHTSA for the {y} {nm} (all dates). Miles = the odometer owners typed in (middle half); '
            f'cost = the repair bills owners wrote in those same complaints, in U.S. dollars. Owners&#39; reports, not confirmed defects.</p></section>')
# ---- 11-12 round 2 (Ryan, 2016 F-150 at 112K: "fix or sell?"): only where we measured asking prices (data/prices.json, the "What to pay" table)
def fix_sell_html(f, y, nm):
    d = (_load('data/prices.json') or {}).get(f['id'], {}).get(str(y))
    if not d: return ''
    bk = [b for b in d['buckets'] if b['n'] >= 10]
    ba = bill_areas(f['id'], y, 3)
    if not bk or not ba: return ''
    big = max(ba, key=lambda a: a[3]); y0, y1 = rc_window(f['id'], y)
    rows = ''.join(f'<tr><td>{E(b["label"])} mi</td><td class="num">{money(b["med"])}</td><td class="num">{round(100 * big[3] / b["med"])}%</td></tr>' for b in bk)
    bills = ''.join(f'<li><b>{E(a)}</b> {RCQ._r(lo)}–{RCQ._r(hi)} <small>(middle {RCQ._r(mid)}, {n} owners)</small></li>' for a, n, lo, mid, hi, _ in ba)
    return (f'<section class="yc yfs" id="fix-or-sell"><h2>Fix or sell?</h2><p>What a {y} {E(d.get("model", nm))} is worth at your mileage, next to what its biggest repairs cost. All in U.S. dollars.</p>'
            f'<div class="tw"><table class="price"><thead><tr><th>Miles</th><th>Typical dealer asking price</th><th>A {E(big[0].lower())} repair ({RCQ._r(big[3])}, the middle bill) as a share of the price</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<h3 class="rcq-h">Typical repair bills ({y0}–{y1} model years)</h3><ul class="yfs-b">{bills}</ul>'
            f'<p class="yc-cap">Prices: typical dealer asking price from {d["n"]:,} listings ({E(d["date"])}), not a sale price or an appraisal. Bills: the middle half of the repair bills owners named in complaints to NHTSA. '
            f'Compare the two before you decide, and get a written quote for your truck.</p></section>')
def seller_questions(f, v, y, x, x2):
    """'Questions to ask the seller' from this year's own recalls, open investigations, top problem areas and the maker's repair notes."""
    out = []
    rs = sorted(x.get('recalls') or [], key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2], reverse=True)
    if rs:
        ids = [f'{E(r["id"])} ({E(RPART(r["part"]))})' for r in rs[:3]]
        out.append(f'Were recall{"s" if len(ids) > 1 else ""} {", ".join(ids[:-1]) + " and " + ids[-1] if len(ids) > 1 else ids[0]} done?'
                   + (f' It has {len(rs)} recalls in all.' if len(rs) > 3 else '') + ' Ask for the dealer printout, or <a href="/vin/">check the VIN</a>.')
    inv = [i for i in x2.get('inv', []) if i['open']]
    if inv: out.append(f'NHTSA has an open investigation into {E((inv[0]["subject"] or inv[0]["part"]).lower().rstrip("."))}. Has this car had that problem?')
    txt = ' '.join([s for s in (x2.get('tsb') or {}).get('top', []) if s] + [q.get('text', '') for q in v.get('quotes') or []] + [r.get('summary', '') for r in rs])
    cvt = bool(re.search(r'\bCVT\b|continuously variable', txt, re.I))
    seen = set()
    for p, _ in (v.get('parts') or [])[:3]:
        nm = NICE(p)
        for pat, q in ASKQ:
            if re.search(pat, nm):
                if pat not in seen:
                    seen.add(pat)
                    if cvt and pat.startswith('transmission'): q = 'Any shudder, whine or slipping from the CVT? Ask for CVT fluid service records.'
                    out.append(q)
                break
    for a, n, lo, mid, hi, _ in bill_areas(f['id'], y):   # 11-12 round 2: the top repair bills
        pat = ASKB_PAT.get(a); q = ASKB.get(a) or next((q for pp, q in ASKQ if pp == pat), None)
        if not q or (pat and pat in seen): continue
        if pat: seen.add(pat)
        out.append(f'{q} <small>({n} owners named a {E(a.lower())} repair bill; the middle one was {RCQ._r(mid)}.)</small>')
    tl = [c for c in (clean_tsb(z) for z in (x2.get('tsb') or {}).get('top', []) if sc_line_ok(f['id'], z)) if c]
    if x2.get('tsb') and tl: out.append(f'{E(MAKER(f["name"]))} sent dealers {x2["tsb"]["n"]} repair notes for this car. Was this one done: &ldquo;{E(tl[0])}&rdquo;?')
    return out[:7]
TECH = (('esc', 'Stability control'), ('fcw', 'Collision warning'), ('ldw', 'Lane departure warning'))
TWORD = {'Standard': ('good', 'Standard'), 'Optional': ('mid', 'Optional'), 'No': ('bad', 'Not offered')}
# What people type into Google. NHTSA/sales lump the heavy-duty trucks in, so the page says so.
SN = {'ford-f-series': ('Ford F-150', 'Covers the whole F-Series (F-150 plus the F-250/F-350 Super Duty): Ford reports their sales together.'),
      'ram-pickup': ('Ram 1500', 'Covers the whole Ram pickup line (1500, 2500 and 3500): Ram reports their sales together.')}
# 11-12 (UX test): the Tesla pages say where each number comes from, and link the EV page (shorter complaint window, 2021-2024)
for _t, _w in (('tesla-model-s', '2012–2020'), ('tesla-model-3', '2017–2020'), ('tesla-model-x', '2016–2020'), ('tesla-model-y', '')):
    SN.setdefault(_t, ('Tesla Model ' + _t.split('-')[-1].upper(),
                       'Tesla doesn&#39;t report U.S. sales by model. ' + (f'The whole-model score uses the study&#39;s cumulative {_w} U.S. estimate; ' if _w else '')
                       + 'scored model years use published per-year estimates (Kelley Blue Book, Wikipedia) and other years show complaints only. '
                       + f'For range, charging cost and the EV ranking, see <a href="/electric/{_t}/">the Model {_t.split("-")[-1].upper()} on our EV page</a>.'))
SNM = lambda f: SN.get(f['id'], (f['name'],))[0]
# 11-12 search titles (Search Console: "mercedes c class reliability" ranked #10.7 with 0 clicks under "Mercedes-Benz C-Class"):
# titles and H1s use the spelling people search (data/search_names.json, from Keyword Planner + Search Console) and the year-page
# word ("Problems" or "Reliability") that model's searches use more. Body text keeps the full names.
QN = lambda f: _SNJ.get('names', {}).get(f['id']) or SNM(f)
YW = lambda f: _SNJ.get('year_word', {}).get(f['id'], 'Problems')
def seo_title(cands, brand=' | Lemon Index', mx=60):
    """The first candidate that fits 60 characters; the brand goes at the end only if it still fits."""
    for t in cands:
        if len(t + brand) <= mx: return t + brand
        if len(t) <= mx: return t
    return cands[-1]
def vs_names(A, B):
    """Short names for 'X vs Y' ('Camry', 'Accord', the way people search it). Both keep the brand when either model name is
    mostly a code (A4, 300, F-150) or the two short names match."""
    def cut(F):
        n = QN(F); nb = len(BYNAME[F['name']]['brand'].split()) if F['name'] in BYNAME else 1
        return n.split(' ', nb)[nb] if len(n.split(' ')) > nb else n
    a, b = cut(A), cut(B)
    if sum(ch.isalpha() for ch in a) < 3 or sum(ch.isalpha() for ch in b) < 3 or a == b: return QN(A), QN(B)
    return a, b
def year_faq(f, v, y, x, best):
    """Plain questions people search, answered only from our own numbers: [(question, answer html, answer text)]."""
    n = SNM(f); out = []
    if v['ok']:
        li = v['li']; word = ('Yes, it is one of the most reliable' if li < 50 else 'Yes, better than average' if li < 85 else 'About average' if li <= 115 else 'No, it is worse than average' if li < 200 else 'No, it is one of the worst')
        _pl = plain(v["li"]); a = f'{word} by government complaints. It drew {"about the average number of complaints" if _pl.lower() == "about average" else _pl} filed with NHTSA in its first 3 years, per car sold (Lemon Index {v["li"]}; 100 is average, lower is better).'
        if v.get('early'): a = f'It&#39;s too early to be sure. So far it has drawn {plain(v["li"])} per car sold, against other {y} cars after the same time on the road (early Lemon Index {v["li"]}; 100 is average).'
        ctx = model_context(f, v, y)
        if ctx: a += ' ' + ctx
        if best['y'] != y: a += f' The {n} year with the fewest complaints per car sold{" since 2010" if best["y"] >= 2010 and f["years"][0]["y"] < 2010 else ""} is {best["y"]}.'   # 11-12: the same rec_year as everywhere else
    elif NOSALES(v): a = f'We can&#39;t score it: {NOSALES_WHY}, so there is no per-car rate. Owners filed {v["n"]} complaints with NHTSA in its first 3 years.'
    elif v.get('low'):
        a = (f'We can&#39;t score it: only {LOWS(v)} were sold in the U.S. in {y} (calendar-year sales), under the 20,000 we need for a fair per-car score. '
             f'Owners filed {v["n"]} complaints with NHTSA in its first 3 years.')
    else:
        a = f'There isn&#39;t enough data to score it: owners filed only {v["n"]} complaints in its first 3 years.'
    out.append((f'Is the {y} {n} reliable?', a))
    if v['parts']:
        ps = [f'{NICE(p)} ({k}%)' for p, k in v['parts'][:3]]
        out.append((f'What are the most common {y} {n} problems?', f'In owner complaints to the government, the parts named most are {", ".join(ps[:-1]) + " and " + ps[-1] if len(ps) > 1 else ps[0]}. That is the share of complaints, not the share of cars that break.'))
    if 'recalls' in x:
        rc = x['recalls']
        out.append((f'How many recalls does the {y} {n} have?', (f'{len(rc)} safety recall{"s" if len(rc) != 1 else ""}' + (f' (latest: {RPART(sorted(rc, key=lambda r: r["date"][6:10] + r["date"][3:5] + r["date"][:2])[-1]["part"]).lower()})' if rc else '') + '. Recall repairs are free at any dealer; check a specific car&#39;s VIN at nhtsa.gov/recalls.') if rc else 'None: NHTSA has no safety recalls on record for it.'))
    m = x.get('mpg')
    if m and not m.get('ev'):
        c = m['comb']; out.append((f'What gas mileage does the {y} {n} get?', f'{c[0] if c[0] == c[1] else f"{c[0]} to {c[1]}"} mpg combined, depending on the engine (EPA estimate).'))
    sf = x.get('safety') or {}
    if sf.get('best'): out.append((f'Is the {y} {n} safe?', f'NHTSA gave it {sf["best"]} out of 5 stars overall in its best tested version. Ratings differ by body style, and the full table is on the <a href="{CARU(f, y)}advanced/">advanced page</a>.'))
    mg, why = mileage_guide(x)   # 11-12 (Jess): the range plus what it means at 60K / 100K / 150K, not "the middle report was at 4,600 miles"
    if mg: out.append((f'At what mileage do {y} {n} problems show up?', mg[0] + ' ' + ' '.join(f'At {_kl(ks)} miles, a {y} is {t}.' for ks, t in _mgroups(mg[1])) + ' This is when owners who had a problem reported it, not a prediction for one car.'))
    if v['parts']:
        tr = next((k for p, k in v['parts'] if 'transmission' in p), None)
        out.append((f'Does the {y} {n} have transmission problems?', f'Transmission and drivetrain issues make up {tr}% of its owner complaints.' if tr else f'Transmission and drivetrain issues aren&#39;t among its top 5 complaint areas.'))
    if m and m.get('cost'):
        co = m['cost']; out.append((f'How much does the {y} {n} cost in fuel a year?', f'About {f"${co[0]:,}" if co[0] == co[1] else f"${co[0]:,} to ${co[1]:,}"} a year, by the EPA&#39;s current estimate.'))
    if m and m.get('engines') and not m.get('ev'): out.append((f'What engines does the {y} {n} have?', f'{", ".join(m["engines"])}.'))
    nb, how = near_pick(f, y)   # 11-12 (Jess): a year near hers, same generation when we know it, not 2001
    if nb and how == 'near': out.append((f'What {n} year is better than the {y}?', f'Nearby, the {nb["y"]} drew fewer owner complaints per car sold ({plain(nb["li"])}).' + (f' Across every year, {best["y"]} drew the fewest.' if best['y'] not in (y, nb['y']) else '')))
    elif nb and how == 'model': out.append((f'What {n} year is better than the {y}?', f'No year within 3 model years of it drew fewer complaints. Across every year, {nb["y"]} drew the fewest ({plain(nb["li"])}).'))
    elif how == 'self' and v['ok']: out.append((f'Is there a better {n} year than the {y}?', f'Not nearby: the {y} drew the fewest complaints per car sold of the {n} years within 3 model years of it.' + (f' Across every year, {best["y"]} drew the fewest.' if best['y'] != y else '')))
    return [(q, a, re.sub('<[^>]+>', '', html.unescape(a))) for q, a in out]
def answer_box(f, v, y, x, best):
    n = E(SNM(f)); rc = x.get('recalls'); m = x.get('mpg'); bits = []
    if v['ok']:
        w = ('one of the most reliable years' if v['li'] < 50 else 'better than average' if v['li'] < 85 else 'about average' if v['li'] <= 115 else 'worse than average' if v['li'] < 200 else 'one of the worst years')
        s1 = (f'The {y} {n} is <b>too new to judge</b>: its partial score so far is {v["li"]} (100 is the average {y} car), from {v["n"]:,} owner complaints.' if v.get('early') else
              f'The {y} {n} is <b>{w}</b> by owner complaints: {v["n"]:,} complaints in its first 3 years and a Lemon Index of {v["li"]}, where 100 is the average car.')
    elif NOSALES(v): s1 = f'The {y} {n} can&#39;t be scored ({NOSALES_WHY}): owners filed {v["n"]:,} complaints in its first 3 years.'
    elif v.get('low'): s1 = f'The {y} {n} sold too few to score ({LOWS(v)} in the U.S. in {y}, under 20,000): owners filed {v["n"]:,} complaints in its first 3 years.'
    else: s1 = f'The {y} {n} has too few complaints to score: {v["n"]:,} in its first 3 years.'
    if v['parts']: bits.append(f'owners complain most about {E(NICE(v["parts"][0][0]))}')
    if rc is not None: bits.append(f'it has {len(rc)} recall{"s" if len(rc) != 1 else ""}')
    if m and not m.get('ev'): c = m['comb']; bits.append(f'it gets {c[0] if c[0] == c[1] else f"{c[0]} to {c[1]}"} mpg combined')
    s2 = (bits[0][0].upper() + bits[0][1:] + (', ' + ', '.join(bits[1:-1]) + (',' if len(bits) > 2 else '') + ' and ' + bits[-1] if len(bits) > 1 else '') + '.') if bits else ''
    nb, how = near_pick(f, y); ctx = model_context(f, v, y)
    s3 = (f' {ctx}' if ctx else '') + (f' Nearby, the {nb["y"]} drew fewer complaints.' if how == 'near' else f' The {nb["y"]} drew the fewest complaints of any {n} year.' if how == 'model' else
                                       f' It drew the fewest complaints of any {n} year.' if best['y'] == y else '')
    return f'<p class="ans">{s1} {s2}{s3}</p>'
# 11-03 (Elijah: "add newer car years... just have a disclaimer"): 2023-2025 are early reads
ASOF = 'October 2026'
EARLY_NOTE = lambda y, nm: (f'<div class="early-n"><b>Too new: partial score.</b> The {y} {nm} hasn&#39;t finished its 3-year window yet. This counts every owner complaint filed so far '
                            f'(through {ASOF}) and compares it with other {y} cars, which have had the same time on the road. It can change as more owners file.</div>')
def year_body(f, v, y, x, best, worst, prev, nxt, qs_list, qa=()):
    nm = E(SNM(f)); x2 = X2.get(f['id'], {}).get(str(y), {}); mkr = E(MAKER(f['name']))
    share_txt = (f'{y} {SNM(f)}: {plain(v["li"])} per car sold' if v['ok'] else f'{y} {SNM(f)}: owner complaints and recalls') + (f', {len(x["recalls"])} recalls' if x.get('recalls') else '') + '. Free report:'
    rec = x.get('recalls') or []; m = x.get('mpg'); sf = x.get('safety'); s = x.get('sev') or {}
    if v['ok']:   # 11-12 (Jess, Marcus, Linda): a plain buy verdict with its reason, and the model's context when the two disagree
        cls, word, why = buy_verdict(f, v, y)
        hero = f'<div class="yhero">{gauge(v["li"], 190, f"{y} Lemon Index" + (" (partial)" if v.get("early") else ""))}<div class="yverd {cls}"><p class="yvd"><b>{word}.</b> <span>{why}</span></p>{{BW}}</div></div>'
    elif NOSALES(v):
        hero = (f'<div class="yhero yhero-na"><div class="yverd mid"><p><b>Complaints only.</b> <span>{NOSALES_WHY}, so there&#39;s no per-car score. '
                f'Owners filed {v["n"]:,} complaint{"" if v["n"] == 1 else "s"} in its first 3 years.</span></p>{{BW}}</div></div>')
    elif v.get('low'):
        hero = (f'<div class="yhero yhero-na"><div class="yverd mid"><p><b>Complaints only.</b> <span>Too few sold to score: {LOWS(v)} in the U.S. in {y}{LOWSRC(v)}, under the 20,000 a fair per-car '
                f'score needs. Owners filed {v["n"]:,} complaint{"" if v["n"] == 1 else "s"} in its first 3 years.</span></p>{{BW}}</div></div>')   # 11-11: in a .yhero, so the tabbed page keeps it
    else:
        hero = f'<div class="yhero yhero-na"><div class="yverd mid"><p><b>Not enough data.</b> <span>Only {v["n"]} complaint{"" if v["n"] == 1 else "s"} in its first 3 years: too few to score.</span></p>{{BW}}</div></div>'
    old = '<p class="yc-note">Older model year: fewer owners filed complaints back then, so treat the score as rough.</p>' if y < 2010 else ''
    if v.get('early'): old = EARLY_NOTE(y, nm)
    if v.get('low'): old = ''   # no score, so no "rough score" / "early read" caveat
    inv_open = [i for i in x2.get('inv', []) if i['open']]
    badges = ''.join(b for b in [f'<a class="yb bad" href="#inv">Under government investigation</a>' if inv_open else '',
                                 f'<a class="yb" href="#fixes">{x2["tsb"]["n"]} repair notes from {mkr}</a>' if x2.get('tsb') else ''] if b)
    old = (f'<div class="ybs">{badges}</div>' if badges else '') + old
    rng = lambda a: f'{a[0]}' if a[0] == a[1] else f'{a[0]}–{a[1]}'
    facts = [('Owner complaints', f'{v["n"]:,}', 'first 3 years' + (f' · {s["total"]:,} in all, so far' if s.get('total') and s['total'] > v['n'] else '')), ('Recalls', f'{len(rec)}' if 'recalls' in x else '—', 'free fix at any dealer' if rec else 'none on record'),
             ('Fuel economy', f'{rng(m["comb"])} {"MPGe" if m.get("ev") else "mpg"}' if m else '—', 'combined, EPA'),
             (('Crash test', stars(sf['best']), 'NHTSA overall') if sf and sf.get('best') else ('Front crash', stars(x2['old']['front']), 'NHTSA, driver') if (x2.get('old') or {}).get('front') else ('Crash test', '<span class="muted">not rated</span>', 'NHTSA'))]
    tiles = ''.join(f'<div class="yt"><span class="yt-l">{l}</span><b class="yt-v">{val}</b><small>{sub}</small></div>' for l, val, sub in facts if l != 'Recalls')
    nb, how = near_pick(f, y)   # 11-12 (Jess: "told me to buy a 2001"): the better buy near this year, same generation when we know it
    _ev = next((d for d in (EVBY.get(f['id']) or {}).get('years_detail', []) if d['y'] == y), None)   # 11-12 (Dan: Bolt 2021 272 here, 376 there)
    ev_note = (f'<p class="yc-cap">Two windows: the {y} scores {v["li"]} here (complaints in its first 3 years) and {_ev["li"]} on <a href="/electric/{f["id"]}/">its EV page</a> '
               f'(complaints filed by the end of {y + 1}). Different windows, so the numbers differ.</p>') if _ev and v['ok'] else ''
    nav = ''.join(f'<a class="ychip" href="{CARU(f, w["y"])}"><small>{lab}</small><b>{w["y"]}</b></a>' for lab, w in (('previous', prev), ('next', nxt)) if w)
    ph = car_hero(f, y)   # 11-10 (Elijah): the year's AI illustration alone when there is one, else the nearest-year Commons photo
    # 11-03 v3 header: a year switcher (‹ 2007 · 2008 · 2009 ›) and the best / worst years as one quiet line under the verdict
    seg = (f'<a href="{CARU(f, prev["y"])}" aria-label="{prev["y"]}">‹ {prev["y"]}</a>' if prev else '') + f'<span aria-current="page">{y}</span>' + (f'<a href="{CARU(f, nxt["y"])}" aria-label="{nxt["y"]}">{nxt["y"]} ›</a>' if nxt else '')
    bw = (lambda xs: f'<p class="ybw">{" · ".join(xs)}</p>' if xs else '')([f'{lab} <a class="{c}" href="{CARU(f, w["y"])}">{w["y"]}</a>' for lab, w, c in
                                                                         (('Fewer complaints nearby', nb if how == 'near' else None, 'good' if nb and nb['li'] <= 110 else ''),
                                                                          ('Fewest of any year', best, 'good' if best['li'] <= 110 else '')) if w and w['y'] != y and not (lab.startswith('Fewest') and how == 'near' and nb['y'] == best['y'])])
    _by = N2_BETTER(f, v, y)   # 11-13 nav (N2): 'Better years to buy' replaces the two chips; inside .yhero, so the tab layout keeps it
    n2_hero = (hero.replace('<div class="yhero', '<div class="n2-w yhero', 1) if _by else hero).replace('{BW}', '' if _by else bw)[:-6] + N2_ASSET + _by + '</div>'
    parts = ''.join(f'<div class="pt"><span>{E(NICE(p))}</span><span class="bt"><i style="width:{k}%"></i></span><b>{k}%</b></div>' for p, k in v['parts'])
    probs = f'<section class="yc" id="problems"><h2>What owners complain about most. <span class="h2s">From owner complaints to the government.</span></h2><div class="pts">{parts}</div><p class="yc-cap">Share of this year&#39;s owner complaints filed with NHTSA, not the share of cars that break. One complaint can name more than one area.</p>' + (f'<p class="yc-cap"><a href="{CARU(f)}transmission/">Transmission problems in every {nm} year →</a></p>' if _tr_ok(f) else '') + RCQ.code_links(f['id'], y, label=f'the {SNM(f)} ({y - 2}–{min(y + 2, 2026)})') + '</section>' if parts else ''
    sev_items = [(s.get('crash', 0), 'crashes'), (s.get('injured', 0), 'injuries'), (s.get('fire', 0), 'fires'), (s.get('towed', 0), 'tows')]
    _base = lambda k: round(s['total'] * SEVR[k]) if SEVR.get(k) else None
    _svc = lambda n, b: '' if b is None else 'bad' if n > b * 1.1 else 'good' if n < b * .9 else 'mid'   # 11-12 r2 (Ryan: Tows 109 vs 88 was green): red above the average car, green only below it
    sev = (f'<section class="ysev"><h2>How serious. <span class="h2s">Out of all {s["total"]:,} owner complaints filed so far (every year since it was sold, not just the first 3), owners reported:</span></h2><div class="sv">'
           + ''.join(f'<div class="{_svc(n, _base(k))}">{icon(ic)}<b>{n:,}</b><span>{lab}</span>' + (f'<small class="sv-b">average car: {_base(k):,}</small>' if _base(k) is not None else '') + '</div>'
                     for (n, lab), ic, k in zip(sev_items, ('crash', 'injury', 'fire', 'tow'), ('crash', 'injured', 'fire', 'towed')))
           + '</div><p class="yc-cap">&ldquo;Average car&rdquo; = what the same number of complaints would include at the rate across every model year we track. Owners report these themselves; NHTSA doesn&#39;t confirm the cause.</p></section>') if s.get('total') else ''
    if 'recalls' in x:
        rs = sorted(rec, key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2], reverse=True)
        _new = lambda r: (r['date'][6:10] + '-' + r['date'][3:5]) >= f'{int(TODAY[:4]) - 1}-{TODAY[5:7]}'   # 11-12 round 2 (Jake): issued in the last 12 months
        card = lambda r: f'<li><b>{E(RPART(r["part"]).capitalize())}</b> <small>· recall issued {E(r["date"][-4:])}</small>{rtag_html(r)}' + (' <span class="rtag rnew">New: most likely still open</span>' if _new(r) else '') + f'<p>{E(rsum(r))}</p></li>'   # 11-12: "Brakes · recall issued 2024", + which engines
        recs = (f'<section class="yc" id="recalls"><h2>Recalls <span class="yc-n">{len(rs)}</span></h2>'
                + (f'<ul class="rc">{"".join(card(r) for r in rs[:3])}</ul>' + (f'<details><summary>Show all {len(rs)} recalls</summary><ul class="rc">{"".join(card(r) for r in rs[3:])}</ul></details>' if len(rs) > 3 else '')
                   if rs else '<p>No safety recalls on record.</p>')
                + (f'<p class="yc-cap">These are the {nm} recalls the VIN check shows. NHTSA lists {x["rec_other"]["n"]} more for the {y} {E(x["rec_other"]["who"])}, which it files next to it; they aren&#39;t counted here.</p>' if x.get('rec_other') else '')   # 11-12 round 2 (Ryan: 18 here vs 14 on the VIN check)
                + '<p class="yc-cap">Recall repairs are free at any dealer. A recall only matters if it&#39;s still open on that exact car, so check its VIN.</p>'
                + '<p><a class="btn" href="/vin/">Check a VIN for open recalls</a></p>' + CA_RECALL + '</section>')
    else: recs = ''
    crash = ''
    if sf and sf.get('variants'):
        rows = ''.join(f'<tr><td>{E(re.sub(r"^\d{4} ", "", vv["desc"]))}</td><td>{stars(vv["overall"])}</td><td>{stars(vv["front"])}</td><td>{stars(vv["side"])}</td><td>{stars(vv["rollover"])}</td></tr>' for vv in sf['variants'])
        crash = f'<details class="yd"><summary>Crash test details</summary><div class="tw"><table><thead><tr><th>Version</th><th>Overall</th><th>Front</th><th>Side</th><th>Rollover</th></tr></thead><tbody>{rows}</tbody></table></div></details>'
    fuel = (f'<details class="yd"><summary>Fuel cost and engines</summary><p>About <b>{USD(m["cost"])}</b> (USD) a year in {"electricity" if m.get("ev") else "fuel"} (EPA estimate at U.S. prices, 15,000 miles or 24,000 km a year).'
            + (f' Engines: {E(", ".join(m["engines"]))}.' if m.get('engines') and not m.get('ev') else '') + '</p></details>') if m and m.get('cost') else ''
    fixes = ''
    tl = [c for c in (clean_tsb(z) for z in (x2.get('tsb') or {}).get('top', []) if sc_line_ok(f['id'], z)) if c]
    if x2.get('tsb') and tl:
        t = dict(x2['tsb'], top=tl)
        fixes = (f'<section class="yc" id="fixes"><h2>Problems {mkr} told dealers about</h2><p class="yc-cap">{mkr} sent dealers <b>{t["n"]}</b> repair notes for this car. The ones about its biggest problems:</p>'
                 f'<ul class="fx">{"".join(f"<li>{E(s1)}</li>" for s1 in t["top"])}</ul><p class="yc-cap">Ask a seller or mechanic if these were done. Some are free under warranty or a special program.</p></section>')
    invs = ''
    if x2.get('inv'):
        invs = (f'<section class="yc" id="inv"><h2>Government investigations</h2><ul class="iv">'
                + ''.join(f'<li><span class="ivs {"bad" if i["open"] else ""}">{"Open" if i["open"] else "Closed"}</span><b>{E(i["subject"] or i["part"])}</b><small>{i["opened"]}{"" if i["open"] or i["closed"] == i["opened"] else f"–{i['closed']}"}</small></li>' for i in x2['inv'][:4])
                + '</ul><p class="yc-cap">NHTSA looks into a problem when enough owners report it. Many end in a recall.</p></section>')
    safety = ''
    if x2.get('tech') or x2.get('photo'):
        chips = ''.join(f'<div class="tc {TWORD.get(x2["tech"].get(k), ("mid", "?"))[0]}"><span>{lab}</span><b>{TWORD.get(x2["tech"].get(k), ("mid", "Unknown"))[1]}</b></div>' for k, lab in TECH) if x2.get('tech') else ''
        oldst = x2.get('old') or {}
        oldrow = (f'<p class="yc-cap">Crash stars (older test): front {stars(oldst["front"]) if oldst.get("front") else "—"} · side {stars(oldst["side"]) if oldst.get("side") else "—"} · rollover {stars(oldst["roll"]) if oldst.get("roll") else "—"}</p>') if oldst else ''
        photo = f'<figure class="cph"><img src="{E(x2["photo"])}" alt="NHTSA front crash test of the {y} {nm}" loading="lazy"><figcaption>Front crash test · NHTSA</figcaption></figure>' if x2.get('photo') else ''
        safety = f'<section class="yc"><h2>Safety</h2>{f"<div class=tcs>{chips}</div>" if chips else ""}{oldrow}{photo}</section>'
    kc = []
    if v['parts']: kc.append(('wrench', 'Most common problem', E(NICE(v['parts'][0][0])).capitalize(), f'{v["parts"][0][1]}% of owner complaints', '#problems'))
    if 'recalls' in x: kc.append(('warn', 'Recalls', f'{len(rec)}', 'Free fix at any dealer' if rec else 'None on record', '#recalls'))
    if how in ('near', 'model'): kc.append(('up', 'Fewer complaints nearby' if how == 'near' else 'Fewest complaints', f'{nb["y"]}', E(plain(nb['li'])), CARU(f, nb['y'])))
    elif how == 'self': kc.append(('up', 'Fewest complaints nearby', f'{y}', f'No year within 3 of it drew fewer', CARU(f)))
    if inv_open: kc.append(('warn', 'Government investigation', f'{len(inv_open)} open', 'Owners reported enough to trigger one', '#inv'))
    elif x2.get('tsb'): kc.append(('doc', f'Repair notes from {mkr}', f'{x2["tsb"]["n"]}', 'Ask a seller if they were done', '#fixes'))
    buy = (f'<section class="ybuy"><h2>Before you buy. <span class="h2s">What matters most for this car.</span></h2><div class="ybuy-g">'
           + ''.join(f'<a class="yk" href="{h}">{icon(ic)}<span class="yk-l">{lab}</span><b>{val}</b><small>{sub}</small></a>' for ic, lab, val, sub, h in kc) + '</div></section>')
    # 11-12 (Jess, Marcus, Linda): when problems show up, in plain miles, and what to ask the seller (from this year's own recalls, problems and repair notes)
    mg, mwhy = mileage_guide(x)
    if mg:
        tops = [c for c in (x.get('comps') or []) if c[4] >= 15][:2]
        mil = (f'<section class="yc ymg" id="mileage-guide"><h2>When problems show up</h2><p>{mg[0]}</p><ul class="ymg-l">'
               + ''.join(f'<li><b>At {_kl(ks)} miles</b> <small class="km">({_kmK(ks)})</small> <span>{t[0].upper() + t[1:]}.</span></li>' for ks, t in _mgroups(mg[1])) + '</ul>'
               + (f'<p class="yc-cap">By area: ' + '; '.join(f'{E(NICE(c[0]))} mostly {_mi_r(c[2])}–{_mi_r(c[3])} miles ({_mi_r(c[2] * 1.609344)}–{_mi_r(c[3] * 1.609344)} km)' for c in tops) + '.</p>' if tops else '')
               + '<p class="yc-cap">This is when owners who had a problem reported it, not the odds that one car will have it.</p></section>')
    else: mil = f'<section class="yc ymg" id="mileage-guide"><h2>When problems show up</h2><p>{mwhy}</p></section>'
    sq = seller_questions(f, v, y, x, x2)
    ask = (f'<section class="yc yask" id="ask-seller"><h2>Questions to ask the seller</h2><ol class="yask-l">' + ''.join(f'<li>{q}</li>' for q in sq) + '</ol>'
           f'<p class="yc-cap">From this year&#39;s own recalls, top problems, top repair bills and {mkr}&#39;s repair notes. Recall repairs are free at any dealer.</p></section>') if sq else ''
    words = ''
    if qs_list:
        q0 = qs_list[0]; more = ''.join(f'<blockquote><p>{E(q["text"])}</p><cite>NHTSA complaint {q["odi"]}</cite></blockquote>' for q in qs_list[1:])
        words = (f'<section class="yc"><h2>In owners&#39; words</h2><blockquote><p>{E(q0["text"])}</p><cite>{y} {nm} owner · NHTSA complaint {q0["odi"]}</cite></blockquote>'
                 + (f'<details><summary>More owner reports</summary>{more}</details>' if more else '') + '</section>')
    return f'''
<article class="yp yp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/cars/">All cars</a> · <a href="{CARU(f)}">{nm}</a></p><h1>{y} {E(QN(f))} {YW(f).lower()}.</h1>{answer_box(f, v, y, x, best)}{'<p class="early-b">Too new: partial score</p>' if v.get('early') else ''}
{f'<p class="yc-note">{SN[f["id"]][1]}</p>' if f["id"] in SN else ""}{PIN_HTML(f['id'], y)}{n2_hero}
<nav class="modes" aria-label="Page mode"><a href="{CARU(f, y)}" aria-current="page">Normal</a><a href="{CARU(f, y)}advanced/">Advanced</a></nav><nav class="yswitch" aria-label="Model years"><div class="yseg">{seg}<a class="yall" href="{CARU(f)}">All years</a></div><div class="yact"><a class="btn btn-ghost" href="/compare/?c={f['id']}-{y}">Compare</a><button type="button" class="btn btn-ghost yshare" data-share="{E(share_txt)}">Share</button></div></nav></div>{f'<div class="ph-v">{ph}</div>' if ph else ''}</section>
{buy}{top_fails_html(f, y, nm)}{mil}{fix_sell_html(f, y, nm)}{ask}<div class="yts">{tiles}</div>{ytfix(f["id"], y)}{sev}{old}
<section class="yyears noph"><div class="yy-ch"><h2>Every {nm} year. <span class="h2s">{y} is highlighted. Lower is better.</span></h2>{N2_SORT}{ybars(f, y)}</div>{ev_note}</section>
<div class="ygrid">{probs}{timeline(x["miles"], x.get("comps") or [], (x.get("sev") or {}).get("total")) if x.get("miles") else ""}{recs}{(lambda pr: f'<section class="yc">{pr}</section>' if pr else '')(price_html(f["id"], y, f["name"]))}
{fixes}{invs}{safety}{f'<section class="yc">{crash}{fuel}</section>' if crash or fuel else ''}{YEAR_SPECS_HOOK(f['id'], y)}{words}
{f'<section class="yc yqa"><h2>Quick answers</h2>' + qa_fold("".join(f"<h3>{E(q)}</h3><p>{a}</p>" for q, a, _ in qa)) + '</section>' if qa else ''}</div>
<p class="yc-cap">{WHAT_LI} A complaint is an owner&#39;s report, not a confirmed defect. <a href="/method/">How it works</a></p>{share_line(share_txt)}</article>'''

UXC = 'hooks'; exec(open('ux_c.py', encoding='utf-8').read())   # 11-12 UX test (part C): battery-recall banners, RAV4 Hybrid, sales sources, EV YouTube, data files
HDX = 'hooks'; exec(open('hd_pages.py', encoding='utf-8').read())   # 11-12 round 2 (fix C): half-ton banner + honest Q&A on the F-Series/Ram/Silverado/Sierra pages
exec(open('n2_nav.py', encoding='utf-8').read())   # 11-13 navigation (N2): better years strip, year sort, model/year wayfinding
ENGU = 'hooks'; exec(open('engine_uses.py', encoding='utf-8').read())   # 11-13 nav fix N3: ENGINE_USES, "Engines in this car" + other-versions chips (wraps PIN_HTML), engine pages link back
def yearx(fid, y): return extra(fid, y)
# ---- 11-12 round 2 (Carlos: "rav4 hybrid" opened a RAV4 page that never said what the hybrid saves): a Gas or hybrid card on the model page
# of every model sold both ways (data_hybrid_split.py: EPA mpg and yearly fuel cost per version), with a commute line (assets/commute.js)
HYB = (_load('data/hybrid_split.json') or {}).get('models', {})
def gas_hybrid_html(f):
    d = (HYB.get(f['id']) or {}).get('years') or {}
    ys = sorted((y for y in d if int(y) <= 2025), reverse=True)
    if not ys: return ''
    y = ys[0]; r = d[y]; snm = SNM(f)
    rng = lambda a: '—' if not a else f'{a[0]}' if a[0] == a[1] else f'{a[0]}–{a[1]}'
    usd = lambda a: '—' if not a else f'${a[0]:,}' if a[0] == a[1] else f'${a[0]:,}–{a[1]:,}'
    rows = [('Gas', r.get('gas')), ('Hybrid', r.get('hybrid')), ('Plug-in hybrid', r.get('phev'))]
    tr = ''.join(f'<tr><td>{lab}<br><small>{E(", ".join(v["versions"][:3]))}</small></td><td class="num">{rng(v["comb"])} mpg' + (' <small>on gas</small>' if lab.startswith('Plug') else '') + f'</td><td class="num">{usd(v.get("cost"))}</td></tr>'
                 for lab, v in rows if v)
    alt = r.get('hybrid') or r.get('phev'); lab = 'hybrid' if r.get('hybrid') else 'plug-in hybrid'
    mid = lambda v: sum(v['cost']) / 2 if v and v.get('cost') else None
    gc, hc = mid(r.get('gas')), mid(alt)
    com = (f'<div class="ghc-c" data-gas="{gc:.0f}" data-hyb="{hc:.0f}" data-lab="{lab}"><label for="ghc-{f["id"]}">Your commute:</label> <input id="ghc-{f["id"]}" type="number" inputmode="numeric" min="1" max="400" value="40"> '
           f'<span>miles a day, 5 days a week</span> <output for="ghc-{f["id"]}" aria-live="polite">{(40 * 250):,} miles a year: gas about ${round(gc / 15000 * 10000 / 10) * 10:,.0f}, {lab} about ${round(hc / 15000 * 10000 / 10) * 10:,.0f}.</output></div>'
           '<script src="/assets/commute.js?v=1" defer></script>') if gc and hc else ''
    older = [yy for yy in ys[1:] if d[yy].get('hybrid')]
    by = ''.join(f'<tr><td>{yy}</td><td class="num">{rng(d[yy]["gas"]["comb"])}</td><td class="num">{rng(d[yy]["hybrid"]["comb"])}</td></tr>' for yy in older)
    return (f'<section class="yc ghc" id="gas-hybrid"><h2>Gas or hybrid? <span class="h2s">The {y} {E(snm)}, from the EPA.</span></h2>'
            f'<div class="tw"><table><thead><tr><th>Version</th><th>MPG combined</th><th>Fuel cost a year (USD)</th></tr></thead><tbody>{tr}</tbody></table></div>{com}'
            + (f'<details class="yd"><summary>Hybrid vs gas mpg, earlier years</summary><div class="tw"><table><thead><tr><th>Year</th><th>Gas</th><th>Hybrid</th></tr></thead><tbody>{by}</tbody></table></div></details>' if by else '')
            + f'<p class="ghc-n"><b>Complaints are combined.</b> Owner complaints to NHTSA don&#39;t reliably say which version the owner drives, so this model&#39;s score, complaints and recalls cover the gas and hybrid versions together.</p>'
            '<p class="yc-cap">MPG and fuel cost: EPA (fueleconomy.gov), which assumes 15,000 miles a year at U.S. fuel prices; the commute line is that cost per mile times your miles. '
            '<a href="https://www.fueleconomy.gov/feg/pdfs/guides/FEG2026.pdf" rel="noopener nofollow" target="_blank">EPA fuel economy guide</a>.</p></section>')
for f in YEARS:
    c = BYNAME[f['name']]; ys = f['years']; sc = scored(f)
    rec, kind = rec_year(f); best = rec or min(year_pool(f), key=lambda v: v['li']); kind = kind or 'least'; worst = worst_year(f)   # 11-12: one rule everywhere
    lists = len(sc) >= LIST_MIN; good3 = good_years(f)[:3] if lists else []
    # 11-12 r2 (Jake: "Years to stay away from" named only 2022 and missed the 2016 Civic): always the 3 years with the most complaints per car
    # sold, each with its band word, so a worse-than-its-neighbours year shows even when it sits near the average car
    bad3 = sorted((v for v in year_pool(f) if v['y'] != best['y'] and v not in good3), key=lambda v: -v['li'])[:3] if lists else []
    def why(v):
        xx = yearx(f['id'], v['y']); bits = [plain(v['li'])]
        if v['parts']: bits.append(f'top problem: {v["parts"][0][0]}')
        if 'recalls' in xx: bits.append(f'{len(xx["recalls"])} recalls')
        return E(', '.join(bits))
    buy = ''.join(f'<li><a href="{CARU(f, v["y"])}"><b>{v["y"]}</b></a>: {why(v)}</li>' for v in good3)
    avoid = ''.join(f'<li><a href="{CARU(f, v["y"])}"><b>{v["y"]}</b></a>: {why(v)}</li>' for v in bad3)
    chip = lambda v, cl: f'<a class="ych {cl}" href="{CARU(f, v["y"])}"><b>{v["y"]}</b><span>{v["li"]}</span><small>{E(plain(v["li"]))}</small></a>'
    if not lists:   # 11-12: under 5 scored years, no best / avoid lists (the Bolt listed the same 3 years under both)
        picks = (f'<section class="bw2"><div class="bwt"><p class="te">Fewest complaints</p><h2>{best["y"]}.</h2><p class="ts">Only {len(sc)} {E(f["name"])} year{"" if len(sc) == 1 else "s"} '
                 f'{"has" if len(sc) == 1 else "have"} enough complaints and sales to score, too few for best and worst lists. {best["y"]} drew {E(plain(best["li"]))}.</p></div></section>')
    else:
        picks = (('<section class="bw2">' + (f'<div class="bwt good"><p class="te">Fewest complaints</p><h2>{good3[0]["y"]}.</h2><div class="ychs">{"".join(chip(v, "good") for v in good3)}</div></div>' if good3 else
                  f'<div class="bwt"><p class="te">Fewest complaints</p><h2>{best["y"]}.</h2><p class="ts">No {E(f["name"])} year beat the average car. {best["y"]} drew the fewest complaints: {E(plain(best["li"]))}.</p></div>'))
                 + (f'<div class="bwt{" bad" if CLS(bad3[0]) == "bad" else ""}"><p class="te">Most complaints</p><h2>{bad3[0]["y"]}.</h2><div class="ychs">{"".join(chip(v, CLS(v)) for v in bad3)}</div></div>' if bad3 else
                    f'<div class="bwt"><p class="te">Years to avoid</p><h2>None.</h2><p class="ts">No {E(f["name"])} year drew much more than the average car&#39;s complaints.</p></div>') + '</section>')
    rv = [o for o in RIVALS.get(f['id'], []) if mphoto(o)][:4]
    vcards = ''.join(f'<a class="mu" href="{cmpu(f["id"], o)}"><span class="mu-p">{pimg(mphoto(f["id"]), f["name"], "l")}{pimg(mphoto(o), FY[o]["name"], "r")}</span><b>vs {E(FY[o]["name"])}</b></a>' for o in rv)
    vs = ' · '.join(f'<a href="{cmpu(f["id"], o)}">vs {E(FY[o]["name"])}</a>' for o in RIVALS.get(f['id'], [])[:8])
    def yx(v):
        xx = yearx(f['id'], v['y']); m = xx.get('mpg'); sf = xx.get('safety')
        return (f'<td class="num">{len(xx["recalls"]) if "recalls" in xx else "—"}</td><td>{stars(sf["best"]) if sf and sf.get("best") else "—"}</td>'
                f'<td class="num">{(f"{m["comb"][0]}–{m["comb"][1]}" if m["comb"][0] != m["comb"][1] else m["comb"][0]) if m else "—"}</td>')
    rows = ''.join(f'<tr><td><a href="{CARU(f, v["y"])}">{v["y"]}</a></td><td class="num {CLS(v)}">{LIS(v)}</td><td class="pw">{PLN(v)}</td><td class="num">{v["n"]:,}</td><td>{E(v["parts"][0][0]) + f" ({v["parts"][0][1]}%)" if v["parts"] else "—"}</td>{yx(v)}</tr>' for v in ys)
    snm = SNM(f); li = c['li']
    def _avoid_ans(f, b3, since):
        def g1(v):   # first model year of its generation (from the year illustrations' generation names), when we know it
            g = gen_of(f, v['y']); return bool(g) and gen_of(f, v['y'] - 1) not in (None, g)
        one = lambda v: f'{v["y"]} ({band(v["li"])[1].lower()}, Lemon Index {v["li"]}' + (', the first year of a new generation' if g1(v) else '') + ')'
        if all(v['li'] < 85 for v in b3):
            return f'No {snm} year stands out as bad{since}. Even the years with the most complaints per car sold beat the average car: ' + ', '.join(one(v) for v in b3) + '.'
        return f'The 3 years with the most complaints per car sold{since}: ' + ', '.join(one(v) for v in b3) + '. 100 is the average car; lower is better.'
    good_word = ('Yes, it is one of the most reliable models we track' if li < 50 else 'Yes, it draws fewer complaints than the average car' if li < 85 else 'It is about average' if li <= 115 else 'Not overall: it draws more complaints than the average car')
    _since = ' since 2010' if best['y'] >= 2010 and any(v['y'] < 2010 for v in sc) else ''
    mqa = [(f'Is the {snm} a good car?', f'{good_word}, by owner complaints to the government per car sold ({c["years"]}: Lemon Index {li}; 100 is average). Some years are much better than others: '
            f'{best["y"]} drew the fewest complaints{_since}' + (f' and {worst["y"]} the most.' if worst and worst['y'] != best['y'] else '.')),
           (f'What are the best {snm} years to buy?', (f'By owner complaints per car sold{_since}: ' + ', '.join(str(v["y"]) for v in good3) + f'. {good3[0]["y"]} drew the fewest.') if good3 else
            f'Only {len(sc)} {snm} years have enough data to score, so we don&#39;t list best years. {best["y"]} drew the fewest complaints ({plain(best["li"])}).' if not lists else
            f'No {snm} year beat the average car. {best["y"]} drew the fewest complaints ({plain(best["li"])}).'),
           (f'What {snm} years should you stay away from?', _avoid_ans(f, bad3, _since) if bad3 else
            f'Only {len(sc)} {snm} years have enough data to score, too few to single out years to avoid.' if not lists else f'No {snm} year drew much more than an average car&#39;s complaints.')]
    # 11-05 keyword map: "recalls on <car>" and "<car> problems" are big searches; answer them from our own numbers
    _rc = [(v['y'], len(extra(f['id'], v['y']).get('recalls') or [])) for v in ys if 'recalls' in extra(f['id'], v['y'])]
    if _rc and sum(n for _, n in _rc):
        _top = sorted(_rc, key=lambda t: -t[1])[:3]
        mqa.append((f'How many recalls does the {snm} have?', f'{sum(n for _, n in _rc)} safety recalls across the {len(_rc)} model years we track. Most: ' + ', '.join(f'{y} ({n})' for y, n in _top if n) + '. Each year&#39;s page lists them.'))
    _pt = defaultdict(float)
    for v in ys:
        for _p, _k in v['parts']: _pt[_p] += _k * v['n'] / 100
    if _pt:
        _tp = [NICE(x) for x, _ in sorted(_pt.items(), key=lambda kv: -kv[1])[:3]]
        mqa.append((f'What are the most common {snm} problems?', f'Across every year, owners&#39; complaints to the government name {", ".join(_tp[:-1])} and {_tp[-1]} most. Some years are much worse than others: see the chart above.'))
    qn = QN(f); rel_html, rel_tiles, rel_plain = rel_top(f, c, snm, ys, sc, best, kind, worst, avoid_years(f), qn)
    mqa.insert(0, (f'Is the {snm} reliable?', E(rel_plain)))
    model_qa_html = '<section class="yqa"><h2>Quick answers.</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{a}</p>' for q, a in mqa)) + '</section>'
    # 11-12 search titles: "<model> Reliability" first ("years to avoid" is searched ~4x more than "best years": Keyword Planner), and a
    # real number in the description
    _tt = seo_title([f'{qn} Reliability: Years to Avoid & Best Years', f'{qn} Reliability: Best & Worst Years', f'{qn} Reliability by Year', f'{qn} Reliability'])
    _mpl = plain(li); _mcmp = 'about as many complaints as the average car' if _mpl == 'about average' else _mpl
    page(CARU(f), _tt,
         f'{qn} reliability: {_mcmp}, per car sold (Lemon Index {li}, {c["years"].replace("-", "–")}). Fewest complaints: {best["y"]}. Most: {(worst or best)["y"]}.', f'''
<div class="pg mp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/cars/">All cars</a> · {BRAND_A(c["brand"])} · {E(c["segName"])}</p>{rel_html}{f'<p class="yc-note">{SN[f["id"]][1]}</p>' if f["id"] in SN else ""}{PIN_HTML(f['id'])}
<div class="yhero">{gauge(c["li"], 190, "All years " + c["years"].replace("-", "–"))}<div class="yverd {verdict(c["li"])[0]}"><p><b>{verdict(c["li"])[1]}.</b> <span>Whole model, {c["years"]}{"" if plain(c["li"]).lower() in verdict(c["li"])[1].lower() else ": " + E(plain(c["li"]))}.</span></p><p class="ybw">Fewest complaints <a class="{'good' if best['li'] <= 110 else ''}" href="{CARU(f, best["y"])}">{best["y"]}</a>{f' · Most complaints <a class="bad" href="{CARU(f, worst["y"])}">{worst["y"]}</a>' if worst and worst['y'] != best['y'] else ''}</p></div>{N2_ASSET}</div>
<p><button type="button" class="btn btn-ghost" data-share="{E(f'Every {snm} year ranked by owner complaints. Fewest: {best["y"]}. Most: {(worst or best)["y"]}. Free report:')}">Share ↗</button></p></div><div class="ph-v">{(YSL.year_slider_html(f['id'], f['name'], {v['y']: round(v['li']) for v in ys if v.get('ok') and v.get('li') is not None}, {y: sc_ for y, sc_ in YSL.yt_scores(f['id']).items() if y in yt_rankable(f, YTS.get(f['id'], {}))}, {v['y'] for v in ys}, start=popular_year(f), best=best['y'], hero=True, mli=c['li'], early={v['y'] for v in ys if v.get('early')}) if YSL.has(f['id']) else (YSL.model_hero_html(f['id'], f['name']) or car_hero(f, ys[-1]["y"])))}{rel_tiles}</div></section>
<section class="yyears noph" id="years"><div class="yy-ch"><h2>Every year. <span class="h2s">Lower is better. Tap a year for its full report.</span></h2>{N2_SORT}{ybars(f)}</div>{'<p class="yc-cap">Scores before 2010 are rough: fewer owners filed complaints back then.</p>' if ys[0]["y"] < 2010 else ''}{yt_note(f)}{(lambda t: f'<p class="yc-cap">{t}</p>' if t else '')(two_windows(f['id']))}</section>
{ytfix("model:" + f["id"])}{picks}{gas_hybrid_html(f)}{SPECS_HOOK(f["id"])}
{f'<section><h2>Compare the {E(f["name"])}.</h2><div class="mus">{vcards}</div>' + (f'<p class="yc-cap">{vs}</p>' if vs else '') + '</section>' if vcards or vs else ''}
{model_qa_html}
<section><details class="yd"><summary>Every year in one table</summary><div class="tw"><table><thead><tr><th>Year</th><th>Index</th><th>Compared with average</th><th>Complaints</th><th>Top complaint</th><th>Recalls</th><th>Crash test</th><th>MPG</th></tr></thead><tbody>{rows}</tbody></table></div></details>
<p class="yc-cap">{WHAT_LI}{SALES_SRC_HTML(f)} <a href="/method/">How it works</a></p>{f'<p><a class="btn" href="{CARU(f)}transmission/">{E(snm)} transmission problems by year →</a></p>' if _tr_ok(f) else ''}</section>{share_line(f'Every {snm} year ranked by owner complaints. Fewest: {best["y"]}. Most: {(worst or best)["y"]}. Free report:')}</div>''',
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{snm} reliability by year', "url": BASE + CARU(f)},
             faq_ld([(q, '', html.unescape(a)) for q, a in mqa]), car_ld(f, img=YSL.ai_src(f['id'], ys[-1]['y']) or (mphoto(f['id']) or {}).get('src'))])
    yurls.append(CARU(f))
    for i, v in enumerate(ys):
        y = v['y']; prev, nxt = (ys[i - 1] if i else None), (ys[i + 1] if i + 1 < len(ys) else None)
        parts = ''.join(f'<div class="pt"><span>{E(p)}</span><span class="bt"><i style="width:{k}%"></i></span><b>{k}%</b></div>' for p, k in v['parts'])
        qs = ''.join(f'<blockquote><p>{E(q["text"])}</p><cite>{y} {E(f["name"])} owner · NHTSA complaint {q["odi"]}</cite></blockquote>' for q in v['quotes'])
        top = ', '.join(f'{p} {k}%' for p, k in v['parts'][:2])
        near = ' · '.join(f'<a href="{CARU(f, w["y"])}">{w["y"]}: {LIS(w)}</a>' for w in (prev, nxt) if w)
        old = '<p class="note">Older model year: fewer owners filed complaints with the government back then, and a new model&#39;s first cars often sold the year before, so treat the score as rough. The problems and owner complaints below are exactly as filed.</p>' if y < 2010 and v['ok'] else '<p class="note">Older model year: fewer owners filed complaints with the government back then. The complaints below are exactly as filed.</p>' if y < 2010 else ''
        x = extra(f['id'], y); nrec = len(x['recalls']) if 'recalls' in x else None
        qa = year_faq(f, v, y, x, best); snm = SNM(f)
        _yw = YW(f); _yo = 'Reliability' if _yw == 'Problems' else 'Problems'; _ye = ' (Early Read)' if v.get('early') else ''; _yb = f'{y} {QN(f)} {_yw}'
        page(CARU(f, y), seo_title([f'{_yb}, {_yo} & Recalls{_ye}', f'{_yb} & {_yo}{_ye}', f'{_yb} & Recalls{_ye}', f'{_yb}{_ye}', _yb]),
             (f'Too new, partial score: so far the {y} {snm} has drawn {plain(v["li"])} per car sold (NHTSA).' if v['ok'] and v.get('early') else f'The {y} {snm} drew {plain(v["li"])} per car sold (NHTSA).' if v['ok'] else f'Owners filed only {v["n"]} NHTSA complaints about the {y} {snm} in its first 3 years.')
             + (f' {nrec} recall{"s" if nrec != 1 else ""}.' if nrec else '') + (f' Top problems: {top}.' if top else '') + ' Real owner complaints and every other year.', year_body(f, v, y, x, best, worst, prev, nxt, v['quotes'], qa), kind='article', ask=(f['id'], y, f'{y} {snm}'), img=YSL.ai_src(f['id'], y) or (YSL.model_img(f['id']) or {}).get('src') or (PH.get(f['id'], {}).get(str(y)) or {}).get('src'),
             ld=[car_ld(f, y, x.get('mpg'), YSL.ai_src(f['id'], y) or (YSL.model_img(f['id']) or {}).get('src') or (PH.get(f['id'], {}).get(str(y)) or {}).get('src')), {"@context": "https://schema.org", "@type": "WebPage", "name": f'{y} {snm} problems, reliability and recalls', "url": BASE + CARU(f, y)}
                 | ({"primaryImageOfPage": {"@type": "ImageObject", "contentUrl": BASE + PH[f['id']][str(y)]['src'], "license": LIC.get(PH[f['id']][str(y)]['license'], PH[f['id']][str(y)]['page']), "acquireLicensePage": PH[f['id']][str(y)]['page'], "creditText": PH[f['id']][str(y)]['author'].split('\ufffd')[0].strip()}} if str(y) in PH.get(f['id'], {}) and not YSL.ai_src(f['id'], y) and not YSL.model_img(f['id'])
                    else {"primaryImageOfPage": {"@type": "ImageObject", "contentUrl": BASE + (YSL.ai_src(f['id'], y) or YSL.model_img(f['id'])['src']), "license": YSL.LIC, "acquireLicensePage": BASE + '/images/', "creditText": "The Lemon Index"}} if YSL.ai_src(f['id'], y) or YSL.model_img(f['id']) else {})] + ([faq_ld(qa)] if qa else []))
        yurls.append(CARU(f, y))
# ---- transmission pages (11-02): data/trans.json from data_trans.py
def sent_case(t):
    t = re.sub(r'\s+', ' ', t).strip(); t = re.sub(r'\s*\*\w{1,3}$', '', t)
    if sum(c.isupper() for c in t) > len(t) * .5: t = '. '.join(x[:1].upper() + x[1:] for x in t.lower().split('. '))
    return re.sub(r'\bi\b', 'I', t)
def trans_body(f):
    nm = E(SNM(f)); td = TR.get(f['id'], {}); ys = [v['y'] for v in f['years']]
    rows = [(y, td.get(str(y))) for y in ys]; rated = [(y, d) for y, d in rows if d and d.get('rate') is not None]
    if len(rated) < 3: return None, None
    mx = max(d['rate'] for _, d in rated) * 1.05 or 1; avg = sorted(d['rate'] for _, d in rated)[len(rated) // 2]
    worst = sorted(rated, key=lambda r: -r[1]['rate'])[:3]; best = [r for r in sorted(rated, key=lambda r: r[1]['rate']) if r[0] >= 2010][:3]
    # 11-10 v2 (Elijah: "too much text… too much white space… simplify"): a one-sentence answer + 3 stat chips under the car, a one-line
    # method with the full note behind "How we count", tier-colored bars (red worst, green best since 2010, gray the rest) with a tick at
    # the typical year, quotes clamped to 3 lines, and the questions folded into tap-to-open rows (still real text + FAQPage schema).
    bestset = {y for y, _ in best}
    def tier(y, d): return 'bad' if d and d.get('rate') and d['rate'] > avg * 2 and d['n'] >= 20 else 'good' if y in bestset else ''
    def wid(d): return (d['rate'] / mx * 100) if d and d.get('rate') else 0
    def rate(d): return ('%.1f' % d['rate']).rstrip('0').rstrip('.') if d and d.get('rate') is not None else '–'
    def tip(y, d): return f'{y}: {(d or {}).get("n", 0):,} transmission complaints' + (f', {rate(d)} per 100,000 sold' if d and d.get('rate') is not None else ', no sales data')
    tick = f'<em style="left:{avg / mx * 100:.1f}%"></em>'
    bars = ''.join(f'<a class="b {tier(y, d)}" href="{CARU(f, y)}" title="{E(tip(y, d))}"><span class="bn">{y}</span><span class="bt"><i style="width:{wid(d):.1f}%"></i>{tick}</span><b>{rate(d)}</b></a>' for y, d in rows)
    tot = {}
    for _, d in rated:
        for k, n in d['sym'].items(): tot[k] = tot.get(k, 0) + n
    alltr = sum(d['n'] for _, d in rated)
    smax = max(tot.values()) if tot else 1
    sym = ''.join(f'<div class="pt"><span>{E(k)}</span><span class="bt"><i style="width:{n / smax * 100:.0f}%"></i></span><b>{round(n / alltr * 100)}%</b></div>' for k, n in sorted(tot.items(), key=lambda kv: -kv[1])[:6])
    recs = []
    for y in ys:
        for r in extra(f['id'], y).get('recalls') or []:
            if re.search(r'POWER TRAIN|TRANSMISSION', r['part'], re.I): recs.append((y, r))
    seen = set(); rl = ''
    for y, r in sorted(recs, key=lambda t: -t[0]):
        k = rsum(r)[:80]
        if k in seen or not k or k.lower().startswith(('also included', 'this recall', 'the vehicles')): continue
        seen.add(k); rl += f'<li><b>{y}</b> <small>{E(r["date"][-4:])}</small><p>{E(rsum(r))}</p></li>'
        if len(seen) >= 5: break
    wq = max(worst, key=lambda r: r[1]['n']); qs = [q for q in wq[1]['q']][:2]
    quotes = ''.join(f'<blockquote class="q3"><input type="checkbox" id="q3-{i}" class="q3x" hidden><p>{E(sent_case(q))}</p>'
                     + (f'<label for="q3-{i}" class="q3m">more</label>' if len(q) > 110 else '') + f'<cite>{wq[0]} {nm} owner · NHTSA complaint</cite></blockquote>' for i, q in enumerate(qs))
    AND = lambda xs: ', '.join(map(str, xs[:-1])) + (' and ' if len(xs) > 1 else '') + str(xs[-1])
    wys = sorted(y for y, _ in worst); bys = sorted(y for y, _ in best)
    chips = (f'<div class="trc"><div><b>{worst[0][0]}</b><span>worst year</span></div>' + (f'<div><b>{best[0][0]}</b><span>fewest since 2010</span></div>' if best else '')
             + f'<div><b>{alltr:,}</b><span>transmission complaints</span></div></div>')
    qa = [(f'Which {SNM(f)} years have transmission problems?', '', f'By transmission complaints filed with NHTSA per car sold, the worst {SNM(f)} years are {", ".join(str(y) for y, _ in worst)}.'),
          (f'What are common {SNM(f)} transmission problems?', '', 'Owners most often describe ' + ', '.join(k.lower() for k, _ in sorted(tot.items(), key=lambda kv: -kv[1])[:3]) + '.' if tot else 'Owners describe a range of shifting problems.')]
    if best: qa.append((f'Which {SNM(f)} years have the fewest transmission complaints?', '', f'Since 2010, the {SNM(f)} years with the fewest transmission complaints per car sold are {", ".join(str(y) for y, _ in best)}.'))
    share = E(f'{SNM(f)} transmission problems by year. Worst: {", ".join(str(y) for y, _ in worst)}. Free report:')
    body = f'''
<article class="study tr2"><p class="kicker"><a href="/cars/">All cars</a> · <a href="{CARU(f)}">{nm}</a> · Transmission</p><h1>{nm} transmission problems by year</h1>
<p class="tra">Worst years: <b>{AND(wys)}</b>.{f" Best since 2010: <b>{AND(bys)}</b>." if best else ""} <button type="button" class="shl" data-share="{share}">Share ↗</button></p>
{chips}
<h2>Every year</h2>
<details class="trm"><summary>Transmission complaints per 100,000 cars sold, from NHTSA owner reports. <span>How we count</span></summary><p>A complaint counts when it&#39;s filed under the transmission, or under the power train and the owner describes the transmission (shifting, slipping, gears, CVT). It&#39;s an owner&#39;s report, not a confirmed defect, and older years have had longer to collect complaints. The thin line on each bar marks a typical year for this model. Tap a year for its full report.</p></details>
<div class="bars yb trb">{bars}</div>
{f'<h2>What owners describe</h2><div class="pts trp">{sym}</div><p class="note">Share of this model&#39;s transmission complaints that mention each symptom. One complaint can mention several.</p>' if sym else ''}
{f'<h2>Transmission and power train recalls</h2><ul class="rc">{rl}</ul><p class="note">Recall repairs are free at any dealer. Check a specific car&#39;s VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener">nhtsa.gov/recalls</a>.</p>' if rl else ''}
{f'<h2>In owners&#39; words</h2>{quotes}' if quotes else ''}
<section class="yqa trq"><h2>Quick answers</h2>{qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(t)}</p>' for q, _, t in qa))}</section>
{RCQ.code_links(f['id'], None, trans_only=True, label=SNM(f))}<p class="note">Every problem, not just the transmission: <a href="{CARU(f)}">{nm} reliability by year</a>.</p></article>'''
    return body, qa
turls = []
for f in YEARS:
    body, qa = trans_body(f)
    if not body: continue
    snm = SNM(f); wy = sorted(((v['y'], TR[f['id']][str(v['y'])]['rate']) for v in f['years'] if str(v['y']) in TR.get(f['id'], {}) and TR[f['id']][str(v['y'])].get('rate') is not None), key=lambda t: -t[1])[:2]
    page(CARU(f) + 'transmission/', f'{snm} Transmission Problems by Year | The Lemon Index',
         f'Which {snm} years have the most transmission complaints per car sold, what owners describe, and every transmission recall. Worst years: {", ".join(str(y) for y, _ in wy)}. From NHTSA owner complaints.',
         body, kind='article', ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{snm} transmission problems by year', "url": BASE + CARU(f) + 'transmission/'}, faq_ld(qa)], vis=car_hero(f, f['years'][-1]['y']))
    turls.append(CARU(f) + 'transmission/')
TRANS_OK = {u.split('/')[2] for u in turls}
yurls += turls

# ---- car loan rates (11-03, Elijah: "see if dealers are screwing you"). Experian State of the Automotive Finance Market, Q2 2026 (VantageScore 4.0).
LOAN = {'as_of': 'Q2 2026', 'tiers': [
    {'name': 'Super prime', 'range': '781–850', 'new': 4.41, 'used': 6.29, 'pay_new': 741, 'pay_used': 534},
    {'name': 'Prime', 'range': '661–780', 'new': 6.15, 'used': 8.81, 'pay_new': 770, 'pay_used': 528},
    {'name': 'Near prime', 'range': '601–660', 'new': 9.71, 'used': 13.93, 'pay_new': 816, 'pay_used': 555},
    {'name': 'Subprime', 'range': '501–600', 'new': 13.52, 'used': 19.10, 'pay_new': 805, 'pay_used': 567},
    {'name': 'Deep subprime', 'range': '300–500', 'new': 16.11, 'used': 21.62, 'pay_new': 779, 'pay_used': 570}]}
def bars3d(rows, mx, unit='%'):
    """CSS 3D bar chart (assets/bars3d.js): rows = [(label, sub, value, color)]."""
    cols = ''.join(f'<div class="b3d-col" style="--v:{v / mx:.3f};--c:{c}"><b class="b3d-val">{v:g}{unit}</b><div class="b3d-bar"><i class="f"></i><i class="s"></i><i class="t"></i></div>'
                   f'<span class="b3d-lab">{E(l)}<small>{E(sub)}</small></span></div>' for l, sub, v, c in rows)
    return f'<div class="b3d" data-b3d><div class="b3d-stage">{cols}</div></div>'
def loan_body():
    T = LOAN['tiers']
    opts = ''.join(f'<option value="{i}"{" selected" if i == 1 else ""}>{E(t["name"])} ({t["range"]})</option>' for i, t in enumerate(T))
    tbl = ''.join(f'<tr><td><b>{E(t["name"])}</b><br><small>{t["range"]}</small></td><td class="num">{t["new"]:.2f}%</td><td class="num">{t["used"]:.2f}%</td><td class="num">${t["pay_new"]}</td><td class="num">${t["pay_used"]}</td></tr>' for t in T)
    mx = max(t['used'] for t in T)
    rates = '<div class="lr">' + ''.join(f'<div class="lr-r"><span class="lr-n"><b>{E(t["name"])}</b><small>{t["range"]}</small></span><span class="lr-b"><i class="nw" style="width:{t["new"] / mx * 100:.1f}%"><em>{t["new"]:.1f}% new</em></i><i class="us{" hi" if t["used"] > 12 else ""}" style="width:{t["used"] / mx * 100:.1f}%"><em>{t["used"]:.1f}% used</em></i></span></div>' for t in T) + '</div>'
    return f"""
<div class="pg">{phero('Car loans', 'Is your rate fair?', 'Type the rate the dealer offered. See what it costs you.', visual=pimg(mphoto('honda-accord', 2018), 'Honda Accord'))}<article class="study">
<form id="loanf" class="loan-f" autocomplete="off">
<label>Your credit score<select name="tier">{opts}</select></label>
<label>New or used<select name="kind"><option value="used" selected>Used car</option><option value="new">New car</option></select></label>
<label>APR you were offered<input name="apr" inputmode="decimal" placeholder="e.g. 11.9" aria-label="APR in percent"></label>
<label>Amount you&#39;d borrow<input name="amount" inputmode="numeric" value="25000"></label>
<label>Loan length<select name="term"><option value="36">36 months</option><option value="48">48 months</option><option value="60" selected>60 months</option><option value="72">72 months</option><option value="84">84 months</option></select></label>
<button class="btn" type="submit">Check my rate</button></form>
<div id="loanout" aria-live="polite"></div>
<script id="rates" type="application/json">{json.dumps(LOAN, separators=(",", ":"))}</script>
<h2>What people pay. <span class="h2s">Average APR by credit score.</span></h2>{rates}
<div class="tw"><table><thead><tr><th>Credit</th><th>New APR</th><th>Used APR</th><th>New payment</th><th>Used payment</th></tr></thead><tbody>{tbl}</tbody></table></div>
<p class="note">Averages for loans opened in {LOAN["as_of"]}, from Experian&#39;s State of the Automotive Finance Market (VantageScore 4.0). Your own rate also depends on the loan length, the car&#39;s age and the lender.</p>
<h2>How dealers make money on your loan</h2>
<p>When a dealer arranges your loan, the lender approves a rate (the &ldquo;buy rate&rdquo;) and the dealer can add points on top. Federal settlements with several big lenders capped that markup at about 1 to 1.25 points, and lenders commonly cap it at 2 to 3. That markup is negotiable.</p>
<ol class="beats"><li><b>Get pre-approved first.</b> A quote from your bank or a credit union is your leverage.</li><li><b>Ask the dealer to beat it.</b> If they can&#39;t, use your own loan.</li><li><b>Compare the total cost, not the monthly payment.</b> A longer loan lowers the payment and raises what you pay overall.</li></ol>
<p class="note">General information, not financial advice. Check a specific car&#39;s problems and recalls before you buy: <a href="/cars/">look up any car</a> or <a href="/vin/">check a VIN</a>.</p></article></div>"""
# ---- free data (11-03, Elijah: "how do we give this data away for free with attribution" -> "build data page"). CC BY 4.0.
# Only our own numbers go in the files: the Lemon Index score, NHTSA complaint counts and the transmission rate. No sales figures
# (third-party), no prices (CarGurus/MarketCheck terms), no complaint text.
import csv
def csv_write(path, head, rows, note=''):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        fh.write('# The Lemon Index (lemonindex.com). License: CC BY 4.0, free to use with credit: "Source: The Lemon Index (lemonindex.com)". Updated ' + TODAY + '\n')
        if note: fh.write('# ' + note + '\n')   # 11-12 (Priya): what this file's counts cover
        w = csv.writer(fh); w.writerow(head); w.writerows(rows)
    return len(rows), os.path.getsize(path)
os.makedirs(f'{OUT}/data', exist_ok=True)
_top = lambda v, k: (v['parts'][k][0], v['parts'][k][1]) if k < len(v.get('parts') or []) else ('', '')
_r1 = [[f['id'], f['name'], v['y'], v['li'], v['n']] + [x for k in range(3) for x in _top(v, k)] + ['yes' if v.get('early') else ''] for f in YEARS for v in f["years"]]
DL1 = csv_write(f'{OUT}/data/lemon-index-by-year.csv', ['family_id', 'model', 'model_year', 'lemon_index', 'nhtsa_complaints', 'top_problem_1', 'top_problem_1_complaints',
                'top_problem_2', 'top_problem_2_complaints', 'top_problem_3', 'top_problem_3_complaints', 'early_read'], _r1,
                note='Counts: nhtsa_complaints = owner complaints filed with NHTSA within 3 years of the model year (2023-2025: every complaint filed so far). Blank lemon_index = not scored (under 20,000 sold, no per-model sales figure, or too few complaints). Not a safety rating.')
_names = {f["id"]: f["name"] for f in YEARS}
_r2 = [[fid, _names.get(fid, fid), int(y), d['n'], d['all'], d['rate']] for fid, ys in TR.items() for y, d in sorted(ys.items())]
DL2 = csv_write(f'{OUT}/data/transmission-complaints-by-year.csv', ['family_id', 'model', 'model_year', 'transmission_complaints', 'all_complaints', 'transmission_complaints_per_100k_sold'], _r2,
                note='Counts: every NHTSA complaint for the model year, whenever it was filed (not just the first 3 years), so all_complaints is higher than nhtsa_complaints in lemon-index-by-year.csv.')
DLX = uxc_data_files(csv_write); EMB = build_embeds(); UXC_URLS = [worst_years_page(EMB)]   # 11-12 UX test (Priya): model + EV + worst-years CSVs, chart PNGs + embeds
_kb = lambda b: f'{b / 1024:,.0f} KB'
_cols1 = [('family_id', 'Our id for the model (same as the page URL)'), ('model', 'Make and model'), ('model_year', 'Model year'),
          ('lemon_index', 'Owner complaints per car sold, scaled so 100 = the average car. Lower is better.'),
          ('nhtsa_complaints', 'Owner complaints filed with NHTSA that the score counts'), ('top_problem_1..3', 'The three parts owners complained about most, with how many complaints each'),
          ('early_read', '"yes" for 2023-2025: complaints filed so far, against other cars of the same model year. Can still change.')]
_cols2 = [('transmission_complaints', 'Complaints that describe a transmission problem (matched on the complaint text)'), ('all_complaints', 'All complaints for that model year'),
          ('transmission_complaints_per_100k_sold', 'Transmission complaints per 100,000 cars sold')]
_tbl = lambda cols: '<div class="tw"><table><thead><tr><th>Column</th><th>What it means</th></tr></thead><tbody>' + ''.join(f'<tr><td><code>{E(a)}</code></td><td>{E(b)}</td></tr>' for a, b in cols) + '</tbody></table></div>'
_copy = lambda label, text: f'<div class="cpy"><p class="cpy-l">{label}</p><div class="cpy-r"><code>{E(text)}</code><button type="button" class="btn btn-ghost cpy-b" data-copy="{E(text)}">Copy</button></div></div>'
def _ds(name, desc, url, cols):
    return {"@context": "https://schema.org", "@type": "Dataset", "name": name, "description": desc, "url": BASE + '/data/', "license": "https://creativecommons.org/licenses/by/4.0/",
            "isAccessibleForFree": True, "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE}, "dateModified": TODAY, "variableMeasured": [a for a, _ in cols],
            "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE + url}], "isBasedOn": "https://www.nhtsa.gov/nhtsa-datasets-and-apis"}
DATA_SHEET = '<div class="tsh">' + ''.join(f'<span>{E(c["name"])}</span><span>{c["years"].split("-")[0]}–{c["years"].split("-")[-1][-2:]}</span><b class="{"good" if c["li"] < 100 else "bad"}">{c["li"]}</b>' for c in (CARS[0], CARS[1], CARS[len(CARS) // 2], CARS[-2], CARS[-1])) + '</div>'
# 11-12 (Priya: "five different complaint totals"): what each site-wide total covers, in one block (/data/, /stats/, linked from home + /method/)
def totals_html():
    t3 = sum(v['n'] for f in YEARS for v in f['years']); tr_all = sum(d.get('all') or 0 for ys in TR.values() for d in ys.values())
    return ('<section class="yc" id="totals"><h2>Why our complaint totals differ</h2><p>Each number counts a different slice of the same government file:</p><ul>'
            f'<li><b>1,607,537</b>: every vehicle complaint in NHTSA&#39;s file, 1995 to {ASOF}, all makes (the study and method pages).</li>'
            f'<li><b>{_SV["total"]:,}</b>: every complaint about the {len(YEARS)} models we track, model years 2000 to 2025, filed at any time (the statistics page and the &ldquo;How serious&rdquo; counts on year pages).</li>'
            f'<li><b>{t3:,}</b>: the same models and years, counting only complaints filed in each car&#39;s first 3 years (the complaint count on each year page and the by-year CSV).</li>'
            f'<li><b>{COUNTED:,}</b>: first-3-year complaints for the {len(CARS)} models in the study, model years 2010 to 2022 (the home page). These set the main Lemon Index.</li>'
            f'<li><b>{tr_all:,}</b>: every complaint filed at any time for the model years in the transmission CSV (its all_complaints column), so it runs larger than the first-3-year counts.</li></ul>'
            f'<p class="yc-cap">EV scores use their own window: model years {EV_WIN}, complaints filed by the end of the year after the model year.</p></section>')
page('/data/', 'Free Car Reliability Data (CSV, CC BY 4.0) | Lemon Index',
     'Download free car reliability data: the Lemon Index score, NHTSA owner complaints and transmission complaints for every model year we cover. Free to use with credit.',
     f"""<div class="pg">{phero('Free data', 'Take it. Credit us.', 'For articles, videos, apps and research. Free under CC BY 4.0.', visual=DATA_SHEET)}<article class="study">
<div class="lic"><b>License: <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener">CC BY 4.0</a></b><p>You can copy, share, chart, remix and even use it commercially. Just credit <q>The Lemon Index (lemonindex.com)</q> and link back when you can.</p></div>
<h2>How to credit us</h2>
{_copy('In an article or post', 'Source: The Lemon Index (lemonindex.com), based on NHTSA owner complaints.')}
{_copy('As a link (HTML)', '<a href="https://lemonindex.com/">The Lemon Index</a>')}
{_copy('In a video', 'Data: lemonindex.com')}
<h2>Download</h2>
<div class="dls"><a class="dl" href="/data/lemon-index-by-year.csv" download><b>Lemon Index by model year</b><span>{DL1[0]:,} model years · CSV · {_kb(DL1[1])}</span></a>
<a class="dl" href="/data/transmission-complaints-by-year.csv" download><b>Transmission complaints by model year</b><span>{DL2[0]:,} model years · CSV · {_kb(DL2[1])}</span></a>
{''.join(f'<a class="dl" href="{u}" download><b>{E(t)}</b><span>{n:,} rows · CSV · {_kb(b)}</span></a>' for u, t, n, b, _, _ in DLX)}</div>
<p class="note">Line 2 of each file says exactly what its counts cover, so totals from different files aren&#39;t mixed up. The worst model years are also a page: <a href="/rankings/worst-years/">the worst car model years, 2015–2025</a>.</p>
<p class="note">Updated {TODAY}. Line 1 of each file is the credit line, starting with #. In a spreadsheet just delete that row; in code, skip comment lines (pandas: <code>comment=&#39;#&#39;</code>).</p>
<details class="yd"><summary>What&#39;s in the files</summary><h3>Lemon Index by model year</h3>{_tbl(_cols1)}<h3>Transmission complaints by model year</h3>{_tbl(_cols2)}{''.join(f'<h3>{E(t)}</h3><p>{E(d)}</p>' + _tbl([(a, html.unescape(b)) for a, b in c]) for _, t, _, _, c, d in DLX)}</details>
{totals_html()}
{embed_block(EMB, list(EMB), 'Charts to embed or download')}
<h2>Where the numbers come from</h2><p>Owner complaints come from NHTSA, the U.S. government&#39;s vehicle safety agency, which publishes them for free. The score and the transmission matching are ours. <a href="/method/">See exactly how the index works</a>.</p>
<p class="note">Not included: car prices, sales figures and complaint text (other sources own those); each model&#39;s sales source is linked in the model CSV and on its page. Please don&#39;t present the data as an official rating, and don&#39;t suggest we endorse you. Using it somewhere big, or want a custom cut? <a href="/contact/">Tell us</a>. We&#39;d love to see it.</p>
</article></div><script src="/assets/data.js?v=1103" defer></script>""",
     ld=[_ds('Lemon Index car reliability by model year', 'Owner complaints per car sold for each model year (100 = the average car), plus each year&#39;s top problem areas, from NHTSA owner complaints.'.replace('&#39;', "'"), '/data/lemon-index-by-year.csv', _cols1),
         _ds('Transmission complaints by car model year', 'Transmission-related NHTSA owner complaints for each model year, as a count and per 100,000 cars sold.', '/data/transmission-complaints-by-year.csv', _cols2)]
        + [_ds(t, d, u, c) for u, t, _, _, c, d in DLX])

# ---- vote page (11-03): polls in data/votes.json (data_votes.py), counts from the lemon-survey Worker (/v). TS = Turnstile site key (public) once Elijah creates it.
TS = '0x4AAAAAAFyhvovKDo2j0cLa'   # Turnstile site key (public, 11-03); the secret lives only in the lemon-survey Worker as TURNSTILE_SECRET
page('/vote/', 'Vote: Most Reliable Car Brand, Best Insurance, Best Years | Lemon Index',
     'Vote on the most reliable car brand, the best and worst car insurance, the best used SUV, truck and model years. See what won this week, this month or all time.',
     f'''{phero('Vote', 'What do owners really think?', 'Quick polls. See what won this week, month or all time.', visual=pair(VOTE_IMG('chevy'), VOTE_IMG('ford'), ('Chevy Silverado', 'Ford F-150')))}
<main id="vote" data-site="lemon" data-ts="{TS}"></main><script src="/assets/vote.js?v=1103h" defer></script>''',
     ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": "Lemon Index car polls", "url": BASE + '/vote/'}])
page('/car-loan-rates/', 'Car Loan Rates by Credit Score and Payment Calculator | Lemon Index',
     'Average new and used car loan rates for every credit score tier (Experian, Q2 2026), and a free check that shows what an above-average dealer rate costs you.',
     loan_body(), ask=('', '', '', 'credit'), ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": "Car loan rates by credit score", "url": BASE + '/car-loan-rates/'},
     faq_ld([('What is a good car loan rate for my credit score?', '', 'Average rates in Q2 2026 (Experian): super prime (781+) 4.41% new / 6.29% used; prime (661-780) 6.15% / 8.81%; near prime (601-660) 9.71% / 13.93%; subprime (501-600) 13.52% / 19.10%; deep subprime (300-500) 16.11% / 21.62%.'),
             ('Can a dealer mark up my car loan rate?', '', 'Yes. The lender approves a buy rate and the dealer can add points on top. Federal settlements with several big lenders capped that at about 1 to 1.25 points, and lenders commonly cap it at 2 to 3. Get a pre-approval from a bank or credit union first.')])])
pick = {}
for f in YEARS: pick.setdefault(BYNAME[f['name']]['brand'], []).append([f['name'], f['id'], [v['y'] for v in f['years']]])
pick = dict(sorted((b, sorted(m)) for b, m in pick.items()))
SEGT = {'truck': 'tk', 'suv': 'sv', 'car': 'cr', 'minivan': 'mv', 'van': 'mv'}   # 11-13 (nav #6): body-type tabs (assets/ctabs.js)
# complaints-only models have no segment in their data; their body type (HD trucks: hd_pages.py)
SEG_EXN = {'chevrolet-trailblazer': 'suv', 'land-rover-range-rover': 'suv', 'mercury-mariner': 'suv', 'saturn-outlook': 'suv', 'mercury-mountaineer': 'suv',
           'ford-excursion': 'suv', 'honda-prologue': 'suv', 'isuzu-rodeo': 'suv', 'fisker-ocean': 'suv', 'ford-maverick': 'truck', 'ford-freestar': 'minivan',
           'chevrolet-venture': 'minivan', 'ford-super-duty': 'truck', 'ram-heavy-duty': 'truck', 'chevrolet-silverado-hd': 'truck', 'gmc-sierra-hd': 'truck',
           **{k: 'car' for k in ('saturn-ion', 'chrysler-pt-cruiser', 'mercury-milan', 'chrysler-sebring', 'dodge-intrepid', 'volkswagen-beetle', 'mercury-grand-marquis',
                                 'mercury-sable', 'buick-lesabre', 'oldsmobile-alero', 'saturn-ls', 'saturn-aura', 'chevrolet-monte-carlo', 'infiniti-g35', 'saab-9-3',
                                 'mitsubishi-eclipse', 'toyota-matrix', 'dodge-magnum', 'ford-five-hundred', 'lincoln-town-car', 'lincoln-ls', 'buick-lucerne', 'kia-spectra', 'suzuki-forenza')}}
def mcard(n, i):
    li = BYNAME[n]['li']; ph = YSL.model_img(i) or mphoto(i)   # 11-10 (Elijah): AI illustrations replace the Wikimedia photos on the grid
    im = (f'<img src="{ph["src"]}"{rset(ph["src"], "(max-width: 600px) 45vw, 170px")} alt="{E(n)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy">' if ph else '')
    w = f'<small class="mc-k">{YRS(BYNAME[n])} score</small>' if i in EVBY else ''   # 11-12: Bolt / Model Y also have an EV card with an EV-window score
    return f'<a class="mc" data-t="r {SEGT.get(BYNAME[n]["seg"], "")}" href="/cars/{i}/" title="Lemon Index, model years {YRS(BYNAME[n])}"><span class="mc-p">{im}</span><b>{E(n.split(" ", 1)[1] if " " in n else n)}</b>{w}<span class="{"good" if li < 100 else "bad"}">{li}</span></a>'
# 11-10 (Elijah): models we don't have data for yet show as gray, non-clickable "No data yet" cards with their illustration
try: NEWM = json.load(open('data/new_models.json', encoding='utf-8'))
except FileNotFoundError: NEWM = []
_have = {f['id'] for f in YEARS}
NEWM = [m for m in NEWM if m['slug'] not in _have and os.path.exists(f'assets/ai-models/{m["slug"]}.webp')]
NEWM = [m for m in NEWM if m['slug'] not in {c['slug'] for c in EVX}]   # 11-11: an EV already has its EV card on /cars/ (Ioniq 5, Leaf, ID.4, Polestar 2, EV6 showed twice)
_EXN = _load('data/extra_models_new.json')   # 11-11 complaints-only models (no sales source yet)
_EXN.update(globals().get('HD_EXN') or {})   # 11-12 round 2: the HD truck cards open their pages (hd_pages.py)
_PLAN = _load('data/new_plan.json'); _DUP = {k: v['dupe_of'] for k, v in _PLAN.items() if v.get('dupe_of')}
# 11-12 round 2 (Devin: the WRX tile opened the Impreza): a model with its own performance page (data/perf/<slug>.json, e.g. the WRX) is no longer
# a duplicate card; its performance card (perf_cars.json) links to that page instead
_DUP = {k: v for k, v in _DUP.items() if not os.path.exists(f'data/perf/{k}.json')}
NEWM = [m for m in NEWM if not os.path.exists(f'data/perf/{m["slug"]}.json')]
_ID = {c['id']: c for c in CARS + CARS_NEW}
def ndcard(m):
    nm = m['name']; short = nm.split(' ', 1)[1] if nm.startswith(m['make'] + ' ') else nm
    img = f'<span class="mc-p"><img src="{m.get("src") or f"/assets/ai-models/{m['slug']}.webp?v=1"}" alt="{E(m.get("alt") or nm)}" width="1000" height="600" loading="lazy"></span>'
    if m['slug'] in _DUP and _DUP[m['slug']] in _ID:   # the same model under another name: the card opens that model's page
        t = _ID[_DUP[m['slug']]]
        return f'<a class="mc" data-t="r {SEGT.get(t["seg"], "")}" href="/cars/{t["id"]}/" title="Counted with the {E(t["name"])}">{img}<b>{E(short)}</b><span class="{"good" if t["li"] < 100 else "bad"}">{t["li"]}</span></a>'
    if m['slug'] in _EXN:
        return f'<a class="mc mc-co" data-t="r {SEGT.get(SEG_EXN.get(m["slug"]), "")}" href="/cars/{m["slug"]}/" title="Owner complaints, no sales figures yet">{img}<b>{E(short)}</b><span class="nd">Complaints only</span></a>'
    return (f'<div class="mc mc-nd" data-t="r" aria-disabled="true" title="No data yet"><span class="mc-p"><img src="/assets/ai-models/{m["slug"]}.webp?v=1" alt="{E(nm)}" width="1000" height="600" loading="lazy"></span>'
            f'<b>{E(short)}</b><span class="nd">No data yet</span></div>')
_nd = {}
for m in NEWM: _nd.setdefault(m['make'], []).append(m)
# 11-13 (nav #5/#6): the Silverado HD and Sierra HD have pages (hd_pages.py) but had no card on the grid or their brand page. No illustration of
# their own yet, so the card shows the half-ton's (alt says so)
for _t, _T in (globals().get('HDT') or {}).items():
    if _t in _EXN and _t not in {m['slug'] for m in NEWM}:
        _mk = _T['name'].split(' ')[0]; _ht = YSL.model_img(_t.replace('-hd', ''))
        _nd.setdefault(_mk, []).append(dict(slug=_t, name=_T['name'], make=_mk, **({'src': _ht['src'], 'alt': _ht['name'] + ' (half-ton shown)'} if _ht else {})))
# 11-11 (Elijah: one Cars section): the supercars, the EVs and the performance cars join the grid under their brands, tagged for the tabs
# (data-t: r regular, s supercar, e electric, p performance). Supercar and performance cards lead with the engine / hp, not a score.
_AIV = _jl('data/ai_vehicle_images.json') or {}; _VPH = _jl('data/vehicle_photos.json') or {}
def _vimg(name):
    a = _AIV.get(name); return {'src': a['src'], 'w': a['w'], 'h': a['h']} if a else _VPH.get(name)
def _cimg(ph, alt):
    return (f'<img src="{ph["src"]}"{rset(ph["src"], "(max-width: 600px) 45vw, 170px")} alt="{E(alt)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy">' if ph else '')
def _short(nm, mk): return nm[len(mk) + 1:] if nm.startswith(mk + ' ') else nm
def sccard(c):
    last = c['years'][-1]; eng = (last.get('engines') or [''])[0].replace('-cyl', '-cylinder')
    return (f'<a class="mc mc-sc" data-t="s" href="/supercars/{_slg(c["name"])}/" title="Supercar: engine, fuel cost and recalls"><span class="mc-p">{_cimg(_vimg(c["name"]), c["name"])}</span>'
            f'<b>{E(_short(c["name"], c["make"]))}</b><small class="mc-k">{E(eng)}</small></a>')
def evcard(c, dup=False):
    return (f'<a class="mc{" mc-dup" if dup else ""}" data-t="e {SEGT.get(c.get("seg"), "")}" href="/electric/{c["slug"]}/" title="EV score: complaints per car sold, model years {E(c["years"])}, filed by the end of the next year"><span class="mc-p">{_cimg(mphoto(c["slug"]), c["name"])}</span>'
            f'<b>{E(_short(c["name"], c["name"].split(" ")[0]))}</b>' + (f'<small class="mc-k">EV score {E(c["years"].replace("-", "–"))}</small>' if c['slug'] in MAINBY else '') + f'<span class="{"good" if c["li"] < 100 else "bad"}">{c["li"]}</span></a>')
def pfcard(c):
    i = perf_info(c); ph = _vimg(i['name']) or ({'src': c['img'], 'w': c.get('w', 1000), 'h': c.get('h', 600)} if c.get('img') else None)
    inner = (f'<span class="mc-p">{_cimg(ph, i["name"])}</span><b>{E(_short(i["name"], i["brand"]))}</b>' + (f'<small class="mc-k">{E(i["lead"])}</small>' if i['lead'] else ''))
    t = 's' if c.get('group') in ('B', 'C') else 'p'   # 11-11: the list's supercars (B) and hypercars (C) join the Supercars tab
    t += {'pickup': ' tk', 'SUV': ' sv'}.get(c.get('body'), '')   # 11-13: the Raptor and TRX on the Trucks tab, the Trackhawk on SUVs (sports cars stay off the Cars tab)
    if i['url']: return f'<a class="mc mc-sc" data-t="{t}" href="{E(i["url"])}">{inner}</a>'
    nd = 'Hypercar · coming soon' if c.get('group') == 'C' else 'Coming soon'
    return f'<div class="mc mc-nd mc-sc" data-t="{t}" aria-disabled="true" title="{nd}">{inner}<span class="nd">{nd}</span></div>'
_xb = {}
for c in SCX: _xb.setdefault(_brandof(c['make']), []).append((c['name'], sccard(c)))
for c in EVX:
    _xb.setdefault(_brandof(c['make']), []).append((c['name'], evcard(c, c['slug'] in YP)))   # Bolt / Model Y: Electric-tab twin of the regular card
for c in PERFX: _xb.setdefault(perf_info(c)['brand'], []).append((perf_info(c)['name'], pfcard(c)))
# 11-12 (UX test, Tyler: "the M3 is missing from the BMW row"): the M3's performance page lives on its model page (/cars/bmw-m3/), so it isn't in
# data/perf_cars.json; its Performance-tab twin goes in the BMW row too (mc-dup: hidden on All cars, where the regular M3 card shows)
def _m3twin():
    try:
        import perf_page as _PP; _d = _PP._load('data/perf/bmw-m3.json'); _g, _v = _PP._star(_d); _zz = _PP._z(_v.get('z60'))[0]
        lead = ' · '.join(x for x in (f'{_PP._hp(_v)} hp' if _PP._hp(_v) else '', f'0–60 {_zz.replace(" s", "")} s' if _zz else '') if x) or '3.0L twin-turbo inline-6'
    except Exception: lead = '3.0L twin-turbo inline-6'
    m = YSL.model_img('bmw-m3')
    return (f'<a class="mc mc-sc mc-dup" data-t="p" href="/cars/bmw-m3/"><span class="mc-p">{_cimg(m, "BMW M3") if m else ""}</span><b>M3</b>'
            f'<small class="mc-k">{E(lead)}</small></a>')
if os.path.exists('data/perf/bmw-m3.json') and not any(c.get('slug') == 'bmw-m3' for c in PERFX): _xb.setdefault('BMW', []).append(('BMW M3', _m3twin()))
# 11-10 (Elijah): brands with no scored model at all go last, under a small "Coming soon" heading (A-Z within each group)
_brand = lambda b: (f'<div class="mb"><h3>{E(b)}</h3><div class="mg">' + ''.join(mcard(n, i) for n, i, _ in pick.get(b, [])) + ''.join(h for _, h in sorted(_xb.get(b, [])))
                    + ''.join(ndcard(m) for m in sorted(_nd.get(b, []), key=lambda m: m['name'])) + '</div></div>')
_soon = sorted(set(_nd) - set(pick) - set(_xb))
lst = ''.join(_brand(b) for b in sorted(set(pick) | set(_xb))) + (f'<p class="mb-soon">Coming soon: no scores yet for these brands</p>' + ''.join(_brand(b) for b in _soon) if _soon else '')
def _mwcard(s):
    if s == 'bmw-m3':
        m = YSL.model_img('bmw-m3')
        return (f'<a class="mc mc-sc mc-dup" data-t="p" href="/cars/bmw-m3/"><span class="mc-p">{_cimg(m, "BMW M3") if m else ""}</span><b>BMW M3</b>'
                f'<small class="mc-k">3.0L twin-turbo inline-6</small></a>')
    c = next((c for c in PERFX if c.get('slug') == s), None)
    return pfcard(c).replace('class="mc ', 'class="mc mc-dup ', 1) if c else ''
_MW = ''.join(_mwcard(s) for s in ('bmw-m3', 'gr-supra', 'shelby-gt500', 'trackhawk', 'ct5-v-blackwing', 'civic-type-r'))
_MW = f'<div class="mb pf-top"><h3>Most wanted</h3><div class="mg">{_MW}</div></div>' if PERFX else ''
_nev = len(EVX); _npf = sum(c.get('group', 'A') == 'A' for c in PERFX); _nsc = len(SCX) + sum(c.get('group') in ('B', 'C') for c in PERFX)
# 11-13 (nav review #6): Trucks / SUVs / Cars / Minivans tabs from each card's body type (the count = cards that tab shows: no Electric-tab twins, no "No data yet")
_nseg = {g: sum(1 for cl, t in re.findall(r'<(?:a|div) class="mc([^"]*)" data-t="([^"]*)"', lst) if g in t.split() and 'mc-dup' not in cl and 'mc-nd' not in cl) for g in ('tk', 'sv', 'cr', 'mv')}
CTABS = ('<nav class="ctabs ctb8" aria-label="Kinds of car">' + ''.join(f'<a href="{u}" data-type="{k}"{" aria-current=true" if k == "all" else ""}>{t}{f" <small>{n}</small>" if n else ""}</a>' for u, k, t, n in (
    ('/', 'all', 'All cars', ''), ('/?type=trucks', 'trucks', 'Trucks', _nseg['tk']), ('/?type=suvs', 'suvs', 'SUVs', _nseg['sv']), ('/?type=cars', 'cars', 'Cars', _nseg['cr']),
    ('/?type=minivans', 'minivans', 'Minivans', _nseg['mv']), ('/?type=performance', 'performance', 'Performance', _npf or 'soon'),
    ('/?type=supercars', 'supercars', 'Supercars', _nsc), ('/?type=electric', 'electric', 'Electric', _nev))) + '</nav>')
# 11-11: one slim row of other ways in, right under the tabs (replaces the home's 3 pill buttons and its big compare box)
HCHIPS = ('<nav class="hchips" aria-label="More ways in"><a href="/compare/">Compare up to 4 cars</a><a href="/rankings/">Rankings</a>'
          '<a href="/best/safest-cars-for-teens/">Safest for teens</a><a href="/motorcycles/">Motorcycles</a></nav>')
_nsx = sum(c.get('group') in ('B', 'C') for c in PERFX)   # 11-11 (Elijah: tidy the Performance tab): a real tab header instead of one plain sentence
CNOTES = (f'<div class="ctn pfh" data-for="performance" hidden><span class="pfh-pill">Coming soon</span><h3>Performance cars</h3>'
          f'<p class="pfh-s">Horsepower, engines and owner reports, from the GT500 to the Type R.{ai_note("performance cars on this tab")}</p>'
          + (f'<p class="pfh-n"><b>{_npf + _nsx} cars on the way:</b> {_npf} here, {_nsx} supercars and hypercars under <a href="/cars/?type=supercars">Supercars</a>.</p>' if _npf else '') + '</div>'
          f'<p class="ctn" data-for="supercars" hidden>Owner complaints are too rare to score supercars, so their cards lead with the engine. Cards marked Coming soon, hypercars included, are next. <a href="/supercars/">Supercar fuel costs and recalls, ranked</a></p>'
          + ''.join(f'<p class="ctn" data-for="{k}" hidden>{_nseg[g]} {w}{x}. <a href="/best/most-reliable-{k}/">The most reliable {k if k != "suvs" else "SUVs"}, ranked</a></p>'
                    for k, g, w, x in (('trucks', 'tk', 'trucks', ', from the Tacoma to the HD pickups and the Raptor'), ('suvs', 'sv', 'SUVs', ''), ('cars', 'cr', 'cars', '. Sports cars are under Performance'), ('minivans', 'mv', 'minivans and vans', '')))
          + f'<p class="ctn" data-for="electric" hidden>EV scores cover model years {EV_WIN}, with complaints filed by the end of the year after the model year. Under All cars, an EV with its own page (Bolt, Model Y) shows the main Lemon Index for its own years instead, so its two numbers differ. <a href="/electric/">The most reliable EVs, ranked</a></p>')
CARS_GRID = f'''<section class="cgrid">{CTABS}{HCHIPS}<h2 data-hide="p">Every model. <span class="h2s" data-hide="s p">Score in the corner: 100 is average, lower is better.</span></h2>{CNOTES}<div class="mbs">{_MW}{lst}</div><p class="ph-cr" data-hide="p">Car images: AI-generated illustrations by The Lemon Index, free under CC BY 4.0 (<a href="/images/">download</a>).</p></section><script src="/assets/soonvote.js?v=2" defer></script>
<style>.pfh{{max-width:560px}}.pfh h3{{font-size:clamp(28px,6.5vw,36px);letter-spacing:-.03em;margin:10px 0 6px}}.pfh-pill{{display:inline-block;padding:4px 12px;border-radius:999px;background:#ffd400;color:#17161a;font-size:12.5px;font-weight:700;letter-spacing:.02em}}.pfh-s{{margin:0 0 6px;font-size:16px}}.pfh-n{{margin:0;font-size:14px;color:#6e6e73}}.cgrid[data-tab="performance"] .mc.mc-dup:not([hidden]){{display:flex}}.cgrid .ph-cr{{margin-top:28px}}
.ctabs.ctb8{{grid-template-columns:repeat(4,minmax(0,1fr));max-width:720px;border-radius:24px;scroll-margin-top:72px}}.ctabs.ctb8 a{{border-radius:20px}}
@media (max-width:600px){{.ctabs.ctb8{{gap:3px;padding:3px;border-radius:20px}}.ctabs.ctb8 a{{min-height:40px;padding:0 2px;font-size:13px;gap:3px;border-radius:17px}}.ctabs.ctb8 a small{{display:none}}}}</style>'''   # 11-11: shared by /cars/ and the home page
page('/cars/', 'Look Up Your Car: Problems by Model and Year | The Lemon Index', f'Pick your car and model year to see its owner complaints, its top problems and how it compares with every other year. {len(YEARS)} models, 2000-2025, plus {len(SCX)} supercars and {len(EVX)} electric cars.', f'''
<div class="pg"><div class="ph ph-f">{finder('<span class="ph-e">Look up</span>Look up your car.', 'Every model year, 2000 to 2025. Free.')}</div>
{CARS_GRID}</div><script src="/assets/ctabs.js?v=3" defer></script>''',
     ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": "Look up your car", "url": BASE + '/'}], canon='/')   # 11-11: same grid as the home page: one indexable copy
# 11-11: the home page = this grid (search, the 4 tabs, every model), with the home's own title, schema, H1 and trust line
page('/', HOME_PAGE['title'], HOME_PAGE['desc'], f'''
<div class="pg pg-home"><div class="ph ph-f">{finder('<span class="ph-e">The Lemon Index</span>Look up any car.', 'Every model year, 2000 to 2025. Free.', foot=f'<p class="fnote">Scores from {COUNTED:,} owner complaints filed with the U.S. government in each car&#39;s first 3 years (model years 2010–2022). <a href="/data/#totals">What each total covers</a></p><p class="fnote">A &ldquo;lemon&rdquo; is American slang for a car with a lot of problems (en español: un carro con muchas fallas). In Canada? The complaints are from U.S. owners, and the same models are sold in Canada with the same parts; recalls there: <a href="{TC_DB}" rel="noopener nofollow" target="_blank">Transport Canada</a>.</p>')}</div>
{CARS_GRID}
<section class="faq"><h2>Questions</h2>{HOME_FAQ}</section></div><script src="/assets/ctabs.js?v=3" defer></script>''', ld=HOME_PAGE['ld'])

curls = []
for a, b in PAIRS:
    A, B = FY[a], FY[b]; ca, cb = BYNAME[A['name']], BYNAME[B['name']]
    ya, yb = {v['y']: v for v in A['years'] if v['ok']}, {v['y']: v for v in B['years'] if v['ok']}
    shared = sorted(set(ya) & set(yb))
    if len(shared) < 2: continue
    # 11-12 r2 (Carlos, Liam): 2023+ years are partial, so they show (gray, labelled) but never count toward a winner
    full = [y for y in shared if not (ya[y].get('early') or yb[y].get('early'))] or shared
    wa = sum(ya[y]['li'] < yb[y]['li'] for y in full); wb = sum(yb[y]['li'] < ya[y]['li'] for y in full)
    lead, trail = (A, B) if ca['li'] <= cb['li'] else (B, A)
    rows = ''.join(f'<tr><td>{y}</td><td class="num {CLS(ya[y])}"><a href="{CARU(A, y)}">{ya[y]["li"]}</a></td><td class="num {CLS(yb[y])}"><a href="{CARU(B, y)}">{yb[y]["li"]}</a></td><td>{E(A["name"] if ya[y]["li"] < yb[y]["li"] else B["name"] if yb[y]["li"] < ya[y]["li"] else "tie")}</td></tr>' for y in shared)
    def facts(F):
        last = max(v['y'] for v in F['years']); xx = extra(F['id'], last); m, sf = xx.get('mpg'), xx.get('safety')
        rec = sum(len(extra(F['id'], v['y']).get('recalls', [])) for v in F['years'] if v['y'] in shared)
        return rec, (f'{m["comb"][0]}–{m["comb"][1]}' if m and m['comb'][0] != m['comb'][1] else (m['comb'][0] if m else '—')), (stars(sf['best']) if sf and sf.get('best') else '—'), last
    fa, fb = facts(A), facts(B)
    _sa, _sb = vs_names(A, B)   # 11-12 search titles: "camry vs accord" (59 impressions) ranked #61 under "Toyota Camry vs Honda Accord Reliability by Year"
    title = seo_title([f'{_sa} vs {_sb}: Which Is More Reliable?', f'{_sa} vs {_sb} Reliability by Year', f'{_sa} vs {_sb} Reliability'])
    sh_txt = f'{A["name"]} vs {B["name"]}: which has fewer problems? Free comparison from owner complaints:'
    # 11-02 (Elijah): one clear winner up top, a 2-column scorecard that stays side by side on phones, and bars instead of a wide table
    close = abs(ca['li'] - cb['li']) <= max(ca['li'], cb['li']) * .08
    lc_, tc_ = (ca, cb) if lead is A else (cb, ca); fewer = round((1 - lc_['li'] / max(tc_['li'], 1)) * 100)
    lw, tw_ = (wa, wb) if lead is A else (wb, wa)
    if close: verdict = f'<p class="vk">Verdict</p><p class="vw">Too close to call</p><p class="vs">Overall they drew about the same complaints per car sold ({ca["li"]} vs {cb["li"]}). Pick by model year below.</p>'
    else: verdict = f'<p class="vk">Winner</p><p class="vw">{E(lead["name"])}</p><p class="vs">About <b>{fewer}% fewer</b> owner complaints per car sold than the {E(trail["name"])}, and fewer in <b>{lw} of {len(full)}</b> model years both were sold ({full[0]}–{full[-1]}).</p><p class="vs lfa-vs">Overall score: {E(A["name"])} {ca["li"]}, {E(B["name"])} {cb["li"]} ({E(ca["years"].replace("-", "–"))}). Shopping certain years? Pick them under Year by year.</p>'
    num = lambda x: float(re.match(r'[\d.]+', str(x)).group()) if re.match(r'[\d.]+', str(x)) else None
    def better(x, y, high):
        if x is None or y is None or x == y: return '', ''
        return ('w', '') if (x > y) == high else ('', 'w')
    def srow(lab, va, vb, cls):
        return f'<div class="dl">{lab}</div><div class="dv {cls[0]}">{va}</div><div class="dv {cls[1]}">{vb}</div>'
    stA = num(re.sub(r'<[^>]+>', '', fa[2]).count('★')) if '★' in fa[2] else None; stB = num(re.sub(r'<[^>]+>', '', fb[2]).count('★')) if '★' in fb[2] else None
    bA, bB = rec_year(A)[0] or min((ya[y] for y in ya), key=lambda v: v['li']), rec_year(B)[0] or min((yb[y] for y in yb), key=lambda v: v['li'])   # 11-12: the same pick as the model pages
    duel = f'<div class="duel"><div></div><div class="dh"><a href="{CARU(A)}">{E(A["name"])}</a></div><div class="dh"><a href="{CARU(B)}">{E(B["name"])}</a></div>' + \
        srow('Lemon Index<br><small>100 = average, lower is better</small>', f'<b>{ca["li"]}</b>', f'<b>{cb["li"]}</b>', better(ca['li'], cb['li'], False)) + \
        srow(f'Years with fewer complaints<br><small>{full[0]}–{full[-1]}</small>', f'{wa} of {len(full)}', f'{wb} of {len(full)}', better(wa, wb, True)) + \
        srow(f'Recalls<br><small>{shared[0]}–{shared[-1]}</small>', fa[0], fb[0], better(fa[0], fb[0], False)) + \
        srow('MPG<br><small>latest year</small>', fa[1], fb[1], better(num(fa[1]), num(fb[1]), True)) + \
        srow('Crash test<br><small>best, latest year</small>', fa[2], fb[2], better(stA, stB, True)) + \
        srow('Best score (per car sold)<br><small>the year each model page recommends</small>', f'<a href="{CARU(A, bA["y"])}">{bA["y"]}</a>', f'<a href="{CARU(B, bB["y"])}">{bB["y"]}</a>', ('', '')) + '</div>'
    mx = max(max(ya[y]['li'], yb[y]['li']) for y in shared)
    def _yr(y):
        pt = y not in full; wA = not pt and ya[y]['li'] < yb[y]['li']; wB = not pt and yb[y]['li'] < ya[y]['li']
        tag = ' <small>partial</small>' if pt else ''
        return f'''<div class="yr{' lfa-pt' if pt else ''}" data-y="{y}" data-a="{ya[y]['li']}" data-b="{yb[y]['li']}"{' data-p="1"' if pt else ''}><div class="yy">{y}</div><div class="yb">
<a class="ybar {CLS(ya[y])}{' w' if wA else ''}" href="{CARU(A, y)}"><i style="width:{ya[y]['li'] / mx * 100:.0f}%"></i><span>{E(A["name"])} <b>{ya[y]['li']}</b>{tag}</span></a>
<a class="ybar {CLS(yb[y])}{' w' if wB else ''}" href="{CARU(B, y)}"><i style="width:{yb[y]['li'] / mx * 100:.0f}%"></i><span>{E(B["name"])} <b>{yb[y]['li']}</b>{tag}</span></a></div></div>'''
    # 11-12 r2 (Carlos, Liam: "2020-25, then 2001-19, my years hidden"): every year newest first; a gap year says why it has no side-by-side
    _fyA, _fyB = {v['y']: v for v in A['years']}, {v['y']: v for v in B['years']}
    def _why(F, fy, yy):
        v = fy.get(yy)
        return f'{E(F["name"])}: no {yy} model year in our data' if not v else f'{E(F["name"])}: {E(PLN(v))}' if not v['ok'] else ''
    def _gap(y): return f'<div class="yr lfa-gap" data-y="{y}"><div class="yy">{y}</div><p>No side-by-side for {y}. ' + '; '.join(w for w in (_why(A, _fyA, y), _why(B, _fyB, y)) if w) + '.</p></div>'
    _all = [y for y in range(shared[-1], shared[0] - 1, -1)]
    _cut = full[-min(8, len(full))]
    _top = [y for y in _all if y >= _cut or (y in shared and y not in full)]   # partial years + the 8 newest full years show; older ones fold
    _rest = [y for y in _all if y not in _top]
    _row = lambda y: _yr(y) if y in shared else _gap(y)
    _opt = lambda sel: ''.join(f'<option value="{y}"{" selected" if y == sel else ""}>{y}</option>' for y in sorted(full, reverse=True))
    pick = (f'<form class="lfa-yp" data-a="{E(A["name"])}" data-b="{E(B["name"])}" aria-label="Your model years"><b>Your years:</b> <label><span class="vh">From</span><select name="f">{_opt(full[0])}</select></label> to '
            f'<label><span class="vh">To</span><select name="t">{_opt(full[-1])}</select></label><output class="lfa-yr-res" aria-live="polite"></output></form>')
    yrs = ''.join(_row(y) for y in _top) + (f'<details class="yrs-more"><summary>Show {len(_rest)} older years</summary>' + ''.join(_row(y) for y in _rest) + '</details>' if _rest else '')
    _ld_name = title.replace(' | Lemon Index', '')
    _lead_s, _trail_s = (_sa, _sb) if lead is A else (_sb, _sa)
    page(CMPU(a, b), title,
         f'{QN(A)} vs {QN(B)} reliability: ' + (f'about the same owner complaints per car sold (Lemon Index {ca["li"]} vs {cb["li"]}).' if close else
         f'the {_lead_s} drew {fewer}% fewer owner complaints per car sold than the {_trail_s} (Lemon Index {lc_["li"]} vs {tc_["li"]}).')
         + f' Every model year both were sold, {shared[0]}–{shared[-1]}, plus recalls, crash tests and MPG.', f'''
<article class="study cmpp"><p class="kicker"><a href="/cars/">All cars</a> · Compare</p><h1>{E(_sa)} vs {E(_sb)}: which is more reliable?</h1>
<p class="sub cmp-lede">{E(QN(A))} or {E(QN(B))}? Here is the {E(_sb)} vs {E(_sa)} question answered from owner complaints filed with the government, for every model year both were sold.</p>
<div class="verdict{' tie' if close else ''}">{verdict}</div><p class="cmp-sh">{share_btn(sh_txt)}</p>
<h2>Head to head</h2>{duel}
<p class="sub">Lemon Index = owner complaints filed with the government within 3 years, per car sold, against the average car of the same model year. <b>100 is average, lower is better.</b> It measures complaints, not crash safety. Green check = the better of the two on that line.</p>
<h2 id="your-years">Year by year</h2><p class="sub">Newest first. Shorter bar = fewer complaints per car sold; the check marks the better car that year. Gray = about average{', or 2023+ (too new: a partial score that doesn&#39;t count toward the winner)' if len(full) < len(shared) else ''}. Tap a year for its full report.</p>{pick}<div class="yrs">{yrs}</div>{LFA_JS}
<p class="note"><a href="{CARU(A)}">Every {E(A["name"])} year</a> · <a href="{CARU(B)}">Every {E(B["name"])} year</a> · <a href="/method/">How the index works</a></p>{share_line(sh_txt, 'Know someone choosing between these two?')}</article>''', kind='article',
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": _ld_name, "url": BASE + CMPU(a, b)}], vis=pair(mphoto(a), mphoto(b), (A['name'], B['name'])) + pcredit(who(mphoto(a), mphoto(b))))
    curls.append(CMPU(a, b))
_cp = list(zip([p for p in PAIRS if CMPU(*p) in curls], curls))
cl = ''.join(f'<li><a href="{u}">{E(FY[a]["name"])} vs {E(FY[b]["name"])}</a></li>' for (a, b), u in _cp)
_top, _seen = [], set()   # 8 match-ups, no car twice, so it isn't all Camry
for (a, b), u in _cp:
    if mphoto(a) and mphoto(b) and a not in _seen and b not in _seen and len(_top) < 8: _top.append((a, b, u)); _seen |= {a, b}
mcards = ''.join(f'<a class="mu" href="{u}"><span class="mu-p">{pimg(mphoto(a), FY[a]["name"], "l")}{pimg(mphoto(b), FY[b]["name"], "r")}</span><b>{E(FY[a]["name"])} <i>vs</i> {E(FY[b]["name"])}</b></a>' for a, b, u in _top)
UXC = 'compare'; exec(open('ux_c.py', encoding='utf-8').read())   # 11-12 UX test: performance side-by-sides + the hub (up to 4 cars, every car)

# 10-31: policy pages Stripe checks before it activates payments (and that a paid report needs anyway).
LEGAL_NAME, ADDRESS, CONTACT = 'Westbrook Software LLC', '4539 N 22nd St Ste R, Phoenix, AZ 85016', 'hello@elijahwestbrook.com'
def legal(path, title, body, seo_title, desc):
    page(path, seo_title, desc, f'<article class="study"><p class="kicker">Updated {TODAY}</p><h1>{title}</h1>{body}</article>')
legal('/contact/', 'Contact', f'''<p>Questions about the data, a correction, a car you want covered or a donation: email <a href="mailto:{CONTACT}">{CONTACT}</a>. We usually answer within 2 business days.</p>
<p>The Lemon Index is operated by {LEGAL_NAME}, {ADDRESS}.</p>''', 'Contact the Lemon Index: Data Questions and Corrections',
      'Email the Lemon Index about our car reliability data, a correction, a car you want us to cover or a donation. We usually answer within 2 business days.')
legal('/refunds/', 'Refund policy', f'''<p>Every Lemon Index report is free. Donations are voluntary and don&#39;t unlock anything extra.</p>
<p>If you were charged twice, donated the wrong amount or didn&#39;t mean to donate, email <a href="mailto:{CONTACT}">{CONTACT}</a> within 14 days and we&#39;ll refund it in full. Payments are processed by Stripe.</p>''', 'Refund Policy for Donations | The Lemon Index',
      'Lemon Index reports are free and donations are voluntary. If you were charged twice or donated by mistake, email us within 14 days for a full refund.')
legal('/privacy/', 'Privacy policy', f'''<p>{LEGAL_NAME} ("we") runs lemonindex.com. This page says what we collect and why.</p>
<h2>Visiting the site</h2><p>We use Cloudflare Web Analytics, which counts visits without cookies, and Google Analytics, which uses cookies to count visits and see which pages people read. Google Analytics gets your browser type, rough location and the pages you visit; it doesn&#39;t get your name or email. You can opt out with Google&#39;s <a href="https://tools.google.com/dlpage/gaoptout" rel="noopener">opt-out add-on</a> or by blocking cookies.</p>
<h2>Ads</h2><p>The site is free because it shows ads from Google AdSense. Google and its partners use cookies to show ads based on your visits to this and other websites. Read <a href="https://policies.google.com/technologies/partner-sites" rel="noopener">how Google uses information from sites that use its services</a>. You can turn off personalized ads in <a href="https://adssettings.google.com" rel="noopener">Google&#39;s Ads Settings</a> or opt out of other ad networks&#39; cookies at <a href="https://www.aboutads.info/choices/" rel="noopener">aboutads.info</a>.</p>
<h2>If you donate or give us your email</h2><p>Donations are handled by Stripe; we never see or store your card number. If you give us your email, we use it to send car-buying tips and new studies, and every email has an unsubscribe link.</p>
<h2>Instagram shout-outs for donors</h2><p>When you donate, the Stripe checkout asks if you want a shout-out on our Instagram story. It&#39;s optional. If you type a name or handle there, we may post it with a thank-you (never the amount). Leave it blank and we never name you. Email us any time and we&#39;ll take a story down.</p>
<h2>The "Help our site" questions</h2><p>Answers are anonymous. We store your answer, the page and car you were on, and a daily scrambled code (a one-way hash of your IP address and the date) that only stops repeat answers. We never store your IP address, and there&#39;s no email, name or account.</p>
<h2>The feedback box</h2><p>Feedback messages and optional emails are stored to improve the site and never sold. We don&#39;t store your IP address with them.</p>
<h2>Donor requests</h2><p>After donating, you can tell us what car or feature to add next. We store what you type, the page, a daily scrambled code (a one-way hash of your IP address and the date) that only limits repeat sends, and, if Stripe passed it to the thank-you page, the checkout session ID so a request can be matched to a real donation. No name or email is asked for. Requests are not shown publicly.</p>
<h2>Sharing</h2><p>We don&#39;t sell your personal information. We share it only with the services that run the site (hosting, sign-in, email, Stripe) and when the law requires it.</p>
<h2>Your choices</h2><p>Email <a href="mailto:{CONTACT}">{CONTACT}</a> to get a copy of your data or to have it deleted.</p>
<p>{LEGAL_NAME}, {ADDRESS}.</p>''', 'Privacy Policy: What We Collect and Why | Lemon Index',
      'What lemonindex.com collects: visit counts from Cloudflare and Google Analytics, Google AdSense ad cookies, and your email only if you give it to us. Donations run through Stripe.')
legal('/terms/', 'Terms of use', f'''<p>lemonindex.com is operated by {LEGAL_NAME}, {ADDRESS}. By using the site you agree to these terms.</p>
<h2>The data</h2><p>Our scores, recalls, crash tests and fuel-economy figures come from public U.S. government data (NHTSA and the EPA) and published sales figures. Owner complaints are owners&#39; own reports, not confirmed defects. The site is for general information. It isn&#39;t a mechanical inspection, a repair-cost estimate or a guarantee about any car. Have a car inspected before you buy it.</p>
<h2>Donations</h2><p>Every report is free. Donations are voluntary, processed by Stripe, and don&#39;t unlock anything. See the <a href="/refunds/">refund policy</a>.</p>
<h2>Using our work</h2><p>You may cite our rankings with a link to lemonindex.com (CC BY 4.0). Don&#39;t copy the site wholesale or resell it.</p><p>Our own engine illustrations (listed on <a href="/images/">/images/</a>) are free to use under <a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener license">CC BY 4.0</a>: credit &quot;The Lemon Index (lemonindex.com)&quot;. They are AI-generated illustrations, not photos of a specific engine. Photos credited to Wikimedia Commons authors keep their own licenses.</p>
<h2>Limits</h2><p>The site is provided as is. To the extent the law allows, {LEGAL_NAME} isn&#39;t liable for decisions made using it. Arizona law governs these terms.</p>
<p>Questions: <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>''', 'Terms of Use: How You Can Use Lemon Index Data',
      'The terms for using lemonindex.com: where our car reliability data comes from, what it is and isn&#39;t, citing our rankings, and donations.'.replace('&#39;', "'"))
LEGAL_URLS = ['/contact/', '/refunds/', '/privacy/', '/terms/']
exec(open('about_pages.py', encoding='utf-8').read())   # 11-12 /about/ + /press/ (journalist tester: both were 404s)
exec(open('studies_month.py', encoding='utf-8').read())   # 11-12 monthly data studies /studies/<yyyy-mm>/ (MST_URLS)

# 10-31: electric cars (ranking, fires, cost, problems, driver-assist crashes, one page per EV)
exec(open('electric_pages.py', encoding='utf-8').read())
exec(open('brands_pages.py', encoding='utf-8').read())   # 11-03 brand pages
exec(open('vehicles_pages.py', encoding='utf-8').read())   # 11-04 planes + motorcycles
exec(open('advanced_pages.py', encoding='utf-8').read())   # 11-06 advanced mode
exec(open('engine_pages.py', encoding='utf-8').read())   # 11-10 engine code search + code pages (before gap_pages: the hub lists them)
exec(open('gap_pages.py', encoding='utf-8').read())   # 11-06 keyword gaps
exec(open('seo_pages.py', encoding='utf-8').read())   # 11-06 best-of + stats pages
exec(open('extra_pages.py', encoding='utf-8').read())   # 11-06 Taos + Pontiac
HDX = 'pages'; exec(open('hd_pages.py', encoding='utf-8').read())   # 11-12 round 2 (fix C): HD truck + diesel engine pages, 2.7 EcoBoost, F-150 engines compared (before the engine hubs)
exec(open('supercar_engine_pages.py', encoding='utf-8').read())   # 11-11 supercar engines hub + engine pages (before the BMW pages phase: /images/ lists their images)
BMW_PHASE = 'pages'; exec(open('bmw_pages.py', encoding='utf-8').read())   # 11-10 BMW model pages + engine pages
exec(open('thanks_page.py', encoding='utf-8').read())   # 11-07 donation thank-you page (noindex)
import perf_page; PERF_URLS = perf_page.build_all(OUT, page)   # 11-11 performance-car pages (data/perf/<slug>.json): the M3's own page gets the slider + performance Overview; the rest get pages of their own
exec(open('all_engines.py', encoding='utf-8').read())   # 11-12 /engines/: every engine, searchable, + one coming-soon engine per model
exec(open('find_index.py', encoding='utf-8').read())   # 11-11: the search index of every car page and card + a build check that none is missing
exec(open('alias_pages.py', encoding='utf-8').read())   # 11-13 (N1): redirect stubs at the addresses people type (/cars/ford-f150/, /cars/honda/, reversed match-ups)
json.dump(PD, open('data/page_dates.json', 'w', encoding='utf-8'), separators=(',', ':'))

# 11-13 navigation test (N1, problem 10: "the 404 page has 3 buttons and no search, and loads the whole 250 KB home page"): a light page
# (the /contact/ page's header and footer) with an open search box; assets/lx404.js turns the address into a search and opens one clear
# match on its own (/cars/ford-f150/2015/ -> the 2015 F-150), else shows the top 3. noindex, no canonical.
_404 = open(f'{OUT}/contact/index.html', encoding='utf-8').read()
_404 = re.sub(r'<title>.*?</title>', '<title>Page not found | The Lemon Index</title>', _404, count=1, flags=re.S)
_404 = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="That page doesn&#39;t exist. Search every car, engine code and list on the Lemon Index.">', _404, count=1)
_404 = re.sub(r'<link rel="canonical"[^>]*>', '<meta name="robots" content="noindex">', _404, count=1)
_404 = re.sub(r'<meta property="og:url"[^>]*>', '', _404, count=1)
_404 = re.sub(r'<script type="application/ld\+json">.*?</script>', '', _404, flags=re.S)
_404 = _404.replace(' aria-current="page"', '')
_404 = re.sub(r'<main>.*</main>', lambda m: (
    '<main><div class="lxs-404"><p class="ph-e">404 · page not found</p><h1>That page drove off.</h1>'
    '<p class="lxs-sub" id="lxsub">It may have moved. Search for it:</p>'
    '<form class="lxs-f" role="search" action="/" method="get"><input id="lxq" name="q" type="search" autocomplete="off" placeholder="Search a car, code or question" '
    'aria-label="Search cars, engine codes and lists" enterkeyhint="search"><div id="lxqs" class="fsug" role="listbox" hidden></div></form>'
    '<div id="lxtop" class="lxs-top" hidden></div>'
    '<ul class="lxs-links"><li><a href="/">Look up a car</a></li><li><a href="/brands/">Every brand</a></li><li><a href="/compare/">Compare</a></li>'
    '<li><a href="/best/">Best cars</a></li><li><a href="/engines/">Engines</a></li><li><a href="/check-engine-light/">Engine codes</a></li></ul></div></main>'), _404, count=1, flags=re.S)
_404 = _404.replace('</body>', f'<script src="/assets/lx404.js?v={LXS_V}" defer></script></body>', 1)
open(f'{OUT}/404.html', 'w', encoding='utf-8').write(_404)
urls = ['/', '/rankings/', STUDY, '/studies/', '/method/', '/vin/', '/car-loan-rates/', '/vote/', '/data/', '/brands/'] + PERF_URLS + burls + purls + murls + surls + eurls + GAP_URLS + CODE_URLS + SEO_URLS + EXTRA_URLS + BMW_URLS + SCE_URLS + AE_URLS + yurls + ADV_URLS + curls + LEGAL_URLS + UXC_URLS + MST_URLS + globals().get('HD_URLS', [])
open(f'{OUT}/sitemap.xml', 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{BASE}{u}</loc><lastmod>{PD.get(u, {}).get("d", TODAY)}</lastmod></url>' for u in urls) + '</urlset>')
open(f'{OUT}/ads.txt', 'w').write(f'google.com, {ADS.replace("ca-", "")}, DIRECT, f08c47fec0942fa0\n')
open(f'{OUT}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\nUser-agent: Googlebot-Image\nAllow: /\n\n# bulk dataset scrapers: the data is free at /data/ with credit instead\nUser-agent: CCBot\nDisallow: /\nUser-agent: Bytespider\nDisallow: /\nUser-agent: Diffbot\nDisallow: /\nUser-agent: Omgilibot\nDisallow: /\nUser-agent: ImagesiftBot\nDisallow: /\n\nSitemap: {BASE}/sitemap.xml\nSitemap: {BASE}/image-sitemap.xml\n')
open(f'{OUT}/llms.txt', 'w', encoding='utf-8').write(f'# The Lemon Index\n\n> Car reliability from public data. The Lemon Index = NHTSA owner complaints in the first 3 years per 100,000 U.S. sales, vs the average car of the same model years (100 = average). It measures complaints, not crash safety.\n\n- [The Most Reliable Cars, According to 1.6 Million Owner Complaints]({BASE}{STUDY}): Toyota 4Runner 26, Lexus ES 27, Lexus brand 30, Tesla brand 322 (est.)\n- [The Most Reliable Electric Cars]({BASE}/electric/): {len(RK)} EVs by NHTSA complaints per car sold, best {best['name']} {best['li']}, plus fires, yearly cost and driver-assist crash reports\n- [Engine code lookup]({BASE}/check-engine-light/): what any OBD-II trouble code means, how serious it is, and which cars owners report it on most in NHTSA complaints\n- [Free engine illustrations]({BASE}/images/): free BMW engine illustrations, CC BY 4.0 (AI-generated, credit The Lemon Index)\n- [Every car engine]({BASE}/engines/): every engine with a page (BMW, supercar, performance, Honda Civic), searchable, YouTube owner ranks\n- [BMW engines by year]({BASE}/engines/bmw/): every BMW engine (N54, N55, B58, N63 ...) by model year: US versions and specs (EPA), owner complaints (NHTSA) and a YouTube score\n- [Supercar engines by year]({BASE}/engines/supercars/): {sum(1 for d in SCENG['engines'].values() if d.get('group', 'super') == 'super')} supercar engines (Ferrari F154, Lamborghini V10, McLaren M838T, Nissan VR38DETT ...) matched to their cars (EPA), with a YouTube owner score by model year, NHTSA recalls and automaker repair notes\n- [Performance car engines by year]({BASE}/engines/performance/): {sum(1 for d in SCENG['engines'].values() if d.get('group') == 'perf')} performance-car engines (Hellcat, Coyote, LS3, LS7, 2UR-GSE, EJ257, S65, S85 ...) matched to their cars (EPA), with a YouTube owner score by model year, NHTSA recalls and automaker repair notes\n- [Method]({BASE}/method/)\n')
open(f'{OUT}/CNAME', 'w').write('lemonindex.com')
open(f'{OUT}/google00cb28bea71f4c18.html', 'w').write('google-site-verification: google00cb28bea71f4c18.html')   # Search Console ownership (11-02); never remove
open(f'{OUT}/' + open('.indexnow_key').read().strip() + '.txt', 'w').write(open('.indexnow_key').read().strip())   # IndexNow key (Bing/Yandex instant URL pings, 11-02)
VALIAS = {}   # NHTSA make|model (as owners' complaints name it, e.g. FORD|F150) -> family id, for the VIN page
for fid, yrs in XL.items():
    for e in yrs.values():
        for mk, md, n in e.get('names', []): VALIAS.setdefault(re.sub(r'[^A-Z0-9]', '', mk.upper()) + '|' + re.sub(r'[^A-Z0-9]', '', md.upper()), fid)
VNAMES = {}   # 11-12 round 2 (Jake: no-VIN recall helper): family id -> the NHTSA make + model most of its complaints use (what the recalls API wants)
for fid, yrs in XL.items():
    _cn = defaultdict(int)
    for e in yrs.values():
        for mk, md, n in e.get('names', []): _cn[(mk, md)] += n
    if _cn: VNAMES[fid] = list(max(_cn, key=_cn.get))
CJ = {}
for f in YEARS:
    yy = {}
    for v in f['years']:
        xx = extra(f['id'], v['y']); m = xx.get('mpg'); sf = xx.get('safety')
        yy[str(v['y'])] = [v['li'] if v['ok'] else None, v['n'], len(xx['recalls']) if 'recalls' in xx else None, m['comb'][0] if m else None, m['comb'][1] if m else None,
                          sf.get('best') if sf else None, NICE(v['parts'][0][0]) if v['parts'] else None]
    CJ[f['id']] = [f['name'], yy]
json.dump(CJ, open('assets/cars.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
UXC = 'data'; exec(open('ux_c.py', encoding='utf-8').read())   # 11-12 UX test: docs/assets/compare.json (every car) + chart embeds on /rankings/ and /stats/
exec(open('search_go.py', encoding='utf-8').read())   # 11-12 round 2 (fix B): search "X vs Y" -> the compare tool (find-go.json cmp/cpg)
page('/vin/', 'Free VIN Decoder and Recall Check: Look Up Any VIN | The Lemon Index', 'Free VIN decoder and lookup: type a 17-character VIN to see the exact year, engine and factory, then that car\'s recalls and owner complaints. From the U.S. government VIN database.', f'''
<div class="pg"><section class="finder ph ph-f"><h1><span class="ph-e">Free VIN decoder</span>Check any VIN.</h1><p class="lede">Decode it, then see that car&#39;s recalls and problems.</p>
<form id="vinf" class="vinf" autocomplete="off"><input name="vin" maxlength="20" placeholder="e.g. 1FTEW1EG8JKF05094" aria-label="VIN" spellcheck="false"><button class="btn" type="submit">Check</button></form>
<div id="vinout" class="vinout"></div><p class="fnote">It&#39;s on the dashboard by the windshield, the door frame, or your registration. We don&#39;t store it.</p>
<p class="fnote vin-buy"><b>Buying?</b> Ask the seller for the VIN before you go see the car. Honest sellers share it; it&#39;s also in most online listings and on the windshield.</p>
<section class="vnv" id="no-vin"><h2>No VIN yet?</h2><p class="note">Pick the car and year. You&#39;ll see every recall for it, newest first: a recall from the last 12 months has had the least time to be fixed, so it&#39;s the one most likely still open on a used car.</p>
<form id="vnvf" class="vnv-f" autocomplete="off"><label><span>Make</span><select name="mk" aria-label="Make"></select></label><label><span>Model</span><select name="md" aria-label="Model"></select></label><label><span>Year</span><select name="y" aria-label="Year"></select></label><button class="btn" type="submit">Show recalls</button></form>
<div id="vnvout" class="vin-recalls" aria-live="polite"></div></section>
<p class="fnote vin-ca"><b>In Canada?</b> Recalls there are run by Transport Canada: <a href="{TC_DB}" rel="noopener nofollow" target="_blank">search Transport Canada recalls</a> or <a href="{TC_VIN}" rel="noopener nofollow" target="_blank">check a VIN on the maker&#39;s Canadian recall site</a>.</p>
<div class="ph-v">{pimg(mphoto('toyota-camry', 2019), 'Toyota Camry')}</div>{pcredit(who(mphoto('toyota-camry', 2019)))}
<script id="pick" type="application/json">{json.dumps(PICK, ensure_ascii=False).replace("</", "<\\/")}</script><script id="valias" type="application/json">{json.dumps(VALIAS, separators=(",", ":"))}</script><script id="vnames" type="application/json">{json.dumps(VNAMES, separators=(",", ":"))}</script><script id="vimg" type="application/json">{json.dumps(sorted(f[:-5] for f in os.listdir("assets/ai-models") if f.endswith(".webp")), separators=(",", ":"))}</script><script src="/assets/vin.js?v=1112e" defer></script></section></div>''')
shutil.copytree('assets', f'{OUT}/assets', dirs_exist_ok=True); shutil.copy('data/survey.json', f'{OUT}/assets/survey-q.json'); shutil.copy('data/votes.json', f'{OUT}/assets/votes.json')
print('built', len(urls), 'pages into', OUT)
# 11-12 accurate freshness: pages whose content changed this build -> data/cache/indexnow_pending.txt (git-ignored); `py indexnow.py --pending`
# after a push submits only those and clears the list. PD is saved again here because /vin/ is built after the first save.
json.dump(PD, open('data/page_dates.json', 'w', encoding='utf-8'), separators=(',', ':'))
_smset = set(urls); _chg = [u for u in dict.fromkeys(PD_NEW) if u in _smset]
if _chg:
    os.makedirs('data/cache', exist_ok=True)
    with open('data/cache/indexnow_pending.txt', 'a', encoding='utf-8') as _fh: _fh.write(''.join(u + '\n' for u in _chg))
print(f'freshness: {len(_chg)} of {len(urls)} sitemap pages changed content this build; {sum(1 for u in urls if PD.get(u, {}).get("d") == TODAY)} have lastmod {TODAY}')
try:
    import linkgraph; print(linkgraph.run(LG, urls, OUT))   # 11-12 click depth / inbound links / orphans -> 3 Lemon Index/data/linkgraph/latest.md
except Exception as ex: print('linkgraph failed:', type(ex).__name__, ex)
print('tab layout failures:', len(TAB_FAIL), TAB_FAIL[:5], '| cache hits', sum(1 for k in _TAB_NEW if k in _TAB_OLD), 'of', len(_TAB_NEW))
try:
    with open(_TAB_CACHE + '.tmp', 'wb') as _fh: pickle.dump(_TAB_NEW, _fh, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(_TAB_CACHE + '.tmp', _TAB_CACHE)
except Exception as ex: print('tab cache not saved:', ex)
