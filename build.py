import hashlib
import re
# Builds lemonindex.com into docs/ (GitHub Pages serves main /docs).   usage: py build.py
# Pages: home, /studies/, /studies/most-reliable-cars/, /method/, 404 + sitemap.xml, robots.txt, llms.txt, CNAME.
# Look = the channel's thumbnails: white, Inter, #111 type, lemon yellow #ffd400 for the brand, red #e8141c only for "bad" (the lemon end).
# Every number comes from data/*.csv (autopilot/lib/lemon.py, with the 10-24 mysales sales-timing fix); was 3 Lemon Index/video 1 most reliable/findings.md (NHTSA complaints ÷ US sales, model years 2010-2022).
import os, re, json, html, datetime, shutil, csv
from collections import defaultdict
OUT = 'docs'; TODAY = datetime.date.today().isoformat(); BASE = 'https://lemonindex.com'
E = lambda s: html.escape(str(s), quote=True)
YT, TT, IG = 'https://www.youtube.com/@lemonindex', 'https://www.tiktok.com/@lemonindex', 'https://www.instagram.com/lemonindex/'
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
FAQ = [('What is the Lemon Index?', 'A car\'s safety complaints filed with the U.S. government (NHTSA) per 100,000 cars sold, compared with the average car from the same model years. 100 is average, 50 means half as many complaints, 300 means three times as many.'),
       ('What is the most reliable car by owner complaints?', 'The Toyota 4Runner, with a Lemon Index of 27: about a quarter of the complaints of the average car, across 1.27 million sold (model years 2010-2022).'),
       ('Which car brand has the fewest complaints?', 'Lexus, at 30, followed by Porsche (34, small sample), Toyota (50), BMW (52) and Mercedes-Benz (54).'),
       ('Why does Tesla score so badly?', 'Most Model 3 and Model Y complaints are about forward collision avoidance (phantom braking). Tesla doesn\'t publish U.S. sales by model, so its index uses published estimates.'),
       ('Is this the same as a repair-cost ranking?', 'No. It counts safety complaints filed with the government within 3 years of each model year. It is not a record of repair bills or out-of-warranty costs.')]

# ---- all 131 models for the explorer (copied from 3 Lemon Index/video 1 most reliable/data/out, 10-22)
PART = {'ELECTRICAL SYSTEM': 'electrical', 'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'VEHICLE SPEED CONTROL': 'speed control',
        'FUEL/PROPULSION SYSTEM': 'fuel or EV drive system', 'FORWARD COLLISION AVOIDANCE': 'automatic emergency braking', 'VISIBILITY/WIPER': 'wipers & visibility',
        'VISIBILITY': 'visibility', 'AIR BAGS': 'airbags', 'STRUCTURE': 'body structure', 'EXTERIOR LIGHTING': 'lights', 'ELECTRONIC STABILITY CONTROL (ESC)': 'stability control',
        'LANE DEPARTURE': 'lane assist', 'ENGINE AND ENGINE COOLING': 'engine', 'SEAT BELTS': 'seat belts'}
SEGN = {'car': 'Car', 'suv': 'SUV', 'truck': 'Truck', 'minivan': 'Minivan'}
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
COUNTED = sum(c['n'] for c in CARS)
BYNAME = {c['name']: c for c in CARS}
YP = {f['id'] for f in json.load(open('data/years.json', encoding='utf-8'))}   # models with a page per model year (10-29)
for c in CARS: c['yp'] = c['id'] in YP
PICK = {}
for f in json.load(open('data/years.json', encoding='utf-8')):
    if f['name'] in BYNAME: PICK.setdefault(BYNAME[f['name']]['brand'], []).append([f['name'], f['id'], [v['y'] for v in f['years']]])
PICK = dict(sorted((b, sorted(m)) for b, m in PICK.items()))
def finder(h='Look up any car', sub='Every model year, 2000 to 2025. Free.', foot=''):
    """10-29 (Elijah): the first thing on the page is an easy car filter. Type "2016 pilot", or pick brand, model, year (assets/lookup.js)."""
    pick = json.dumps(PICK, ensure_ascii=False).replace('</', '<\\/')
    return f"""<section class="finder" aria-labelledby="fh"><h1 id="fh">{h}</h1><p class="lede">{sub}</p>
<div class="fq"><input id="fq" type="search" placeholder="e.g. 2016 Honda Pilot" autocomplete="off" aria-label="Type a car"><div id="fsug" class="fsug" role="listbox" hidden></div></div>
<form class="look" id="look"><select id="lb" aria-label="Brand"><option value="">Brand</option></select><select id="lm" aria-label="Model" disabled><option value="">Model</option></select><select id="ly" aria-label="Year" disabled><option value="">Year</option></select><button type="button" class="btn" id="lgo" disabled>Show problems</button></form>
{foot}<script id="pick" type="application/json">{pick}</script></section>"""
BEST = [(n, v, sold or (f"{BYNAME[n]['sold'] / 1e6:.2f}M" if n in BYNAME else '')) for n, v, sold in BEST]   # fills the E-Class's missing sales

# 10-24: every list is rebuilt from the data (the 10-24 sales-timing fix moved some numbers; hand-typed lists drifted).
star = lambda c: c['name'] + ('*' if c['est'] else '')
BEST = [(star(c), c['li'], f"{c['sold'] / 1e6:.2f}M") for c in CARS[:10]]
WORST = [(star(c), c['li'], ', '.join(f'{p} {k}%' for p, k in c['issues'][:2])) for c in CARS[::-1][:10]]
BRANDS = [(r['brand'] + ('*' if r['brand'] in ('Porsche', 'Tesla') else ''), int(r['lemon_index'])) for r in sorted(csv.DictReader(open('data/brand_rates.csv', encoding='utf-8')), key=lambda r: int(r['lemon_index']))]
SEGMENTS = [(SEGN[k] + 's', ' · '.join(f"{c['name']} {c['li']}" for c in [c for c in CARS if c['seg'] == k][:3]), ' · '.join(f"{c['name']} {c['li']}" for c in [c for c in CARS if c['seg'] == k][::-1][:3])) for k in ('car', 'suv', 'truck', 'minivan')]
TOP, BR = CARS[0], dict((b.rstrip('*'), v) for b, v in BRANDS)
FAQ[1] = ('What is the most reliable car by owner complaints?', f"The {TOP['name']}, with a Lemon Index of {TOP['li']}: about a quarter of the complaints of the average car, across {TOP['sold'] / 1e6:.2f} million sold (model years 2010-2022).")
FAQ[2] = ('Which car brand has the fewest complaints?', f"Lexus, at {BR['Lexus']}, followed by Porsche ({BR['Porsche']}, small sample), Toyota ({BR['Toyota']}), BMW ({BR['BMW']}) and Mercedes-Benz ({BR['Mercedes-Benz']}).")

def plain(v):
    """A Lemon Index in plain words, next to every number (10-22: bare scores confused people)."""
    return f'{100 / v:.1f}× fewer complaints than average'.replace('.0×', '×') if v < 90 else 'about average' if v <= 110 else f"{v / 100:.1f}× the average car's complaints".replace('.0×', '×')

def short(v):
    """Short form for the bar charts, where the full sentence gets cut off."""
    return f'{100 / v:.1f}× fewer complaints'.replace('.0×', '×') if v < 90 else 'about average' if v <= 110 else f'{v / 100:.1f}× the complaints'.replace('.0×', '×')

def explorer():
    for c in CARS: ph = mphoto(c['id']); c['img'] = rsmall(ph['src']) if ph else ''   # 11-03 v6: a photo on every row
    data = json.dumps(CARS, ensure_ascii=False).replace('</', '<\\/')
    seed = ''.join(f'<div class="xr"><div class="xm"><span class="xk">#{c["rank"]}</span><span class="xn"><b>{E(c["name"])}</b><small>{c["segName"]} · {c["years"]}</small></span><span class="xb"><small>{plain(c["li"])}</small></span><span class="xi">{c["li"]}</span></div></div>' for c in CARS[:15])
    tabs = ''.join(f'<button type="button" data-seg="{k}" aria-pressed="{str(k == "all").lower()}">{l}</button>' for k, l in [('all', 'All'), ('car', 'Cars'), ('suv', 'SUVs'), ('truck', 'Trucks'), ('minivan', 'Minivans')])
    return f'''<section class="ex" id="explore" aria-labelledby="ex-h"><div class="exh"><div><h2 id="ex-h">Every model, ranked. <span class="h2s">Tap one for every year.</span></h2></div></div>
<div class="exbar"><input id="xq" type="search" placeholder="Search a model, e.g. RAV4" aria-label="Search a model"><div class="tabs" role="group" aria-label="Type">{tabs}</div>
<select id="xbrand" aria-label="Brand"></select><select id="xsort" aria-label="Sort"><option value="best">Most reliable first</option><option value="worst">Least reliable first</option><option value="sold">Most sold</option><option value="az">A to Z</option></select><span id="xcount" class="xcount"></span></div>
<div class="xhead" aria-hidden="true"><span>Rank</span><span>Model</span><span>Compared with the average car <i class="avg">│ = average</i></span><span>Index</span><span>Sold</span><span>Top complaint</span><span></span></div>
<div id="xrows" class="xrows">{seed}</div><button type="button" id="xmore" class="btn ghost xmore">Show all</button>
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
def ask_html(path):
    """Bottom of every page: 11-09 the one-tap survey (survey.js) is gone (Elijah: "remove the bottom questions and instead just have a feedback box")."""
    return (('' if path in NOFB else feedback_html('How can we make Lemon Index better?', 'A car we should add, something confusing, a mistake you spotted…') + '<script src="/assets/feedback.js?v=1109" defer></script>')
            + '<script src="/assets/share.js?v=1109" defer></script><script src="/assets/bars3d.js?v=1103" defer></script><script src="/assets/loan.js?v=1103" defer></script>')
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
NAV_TOP = [('/cars/', 'Cars'), ('/brands/', 'Brands'), ('/compare/', 'Compare'), ('/electric/', 'Electric'), ('/motorcycles/', 'Motorcycles'), ('/vin/', 'VIN check'), ('/studies/', 'Studies')]
NAV_MORE = [('/best/', 'Best cars'), ('/stats/car-complaints/', 'Statistics'), ('/supercars/', 'Supercars'), ('/check-engine-light/', 'Check engine light'), ('/best-gas-mileage/', 'Gas mileage'), ('/planes/', 'Planes'), ('/car-loan-rates/', 'Loan rates'), ('/vote/', 'Vote'), ('/data/', 'Free data'), ('/method/', 'How it works')]
GH_CHEV = '<svg viewBox="0 0 8 8" aria-hidden="true"><path d="M2.5 1 5.5 4 2.5 7" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
GH_DOWN = '<svg viewBox="0 0 8 8" aria-hidden="true"><path d="M1 2.75 4 5.75 7 2.75" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
def gh_header(path):
    cur = lambda u: ' aria-current="page"' if path.startswith(u) else ''
    top = ''.join(f'<a href="{u}"{cur(u)}>{t}</a>' for u, t in NAV_TOP)
    sheet = ''.join(f'<a class="gh-x" href="{u}"{cur(u)}>{t}</a>' for u, t in NAV_TOP) + ''.join(f'<a href="{u}"{cur(u)}>{t}</a>' for u, t in NAV_MORE)
    return (f'<header class="gh wide" data-tuck><div class="gh-in"><a class="gh-brand" href="/"><img src="/assets/icon-64.png" alt="" width="24" height="24">The Lemon Index</a>'
            f'<nav class="gh-links" aria-label="Main">{top}<button class="gh-more" type="button" aria-expanded="false" aria-controls="gh-sheet">More{GH_DOWN}</button></nav>'
            f'<div class="gh-r"><a class="gh-cta" href="{YT}?sub_confirmation=1" rel="noopener">Subscribe{GH_CHEV}</a>'
            f'<button class="gh-menu" type="button" aria-label="Menu" aria-expanded="false" aria-controls="gh-sheet"><i></i><i></i></button></div></div>'
            f'<nav class="gh-sheet" id="gh-sheet" aria-label="All pages"><div class="gh-sheet-in"><p>More from the Lemon Index</p>{sheet}</div></nav></header>')
def navlinks(path):
    on = lambda u: path.startswith(u) or (u == '/cars/' and path.startswith('/cars'))
    return ''.join(f'<a href="{u}"{" class=on aria-current=page" if on(u) else ""}>{t}</a>' for u, t in NAV)
# free-data credit line under every car page (11-03): the data is CC BY 4.0, so copying it is fine as long as it credits us (see /data/)
CITE = '<p class="cite">Free to use with credit: <q>Source: The Lemon Index (lemonindex.com)</q>. <a href="/data/">Get the data</a></p>'
_AH = re.compile(r'<article class="study([^"]*)"><p class="kicker">(.*?)</p>\s*<h1>(.*?)</h1>\s*(?:<p class="lede">(.*?)</p>)?', re.S)
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
_MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
def page(path, title, desc, body, ld=None, kind='website', img=None, ask=None, vis=''):
    title, desc = fit_title(title), fit_desc(desc)
    _h = hashlib.md5(body.encode('utf-8')).hexdigest()[:10]
    if PD.get(path, {}).get('h') != _h: PD[path] = {'h': _h, 'd': TODAY}
    _d = PD[path]['d']; _dl = f'{_MN[int(_d[5:7]) - 1]} {int(_d[8:])}, {_d[:4]}'
    if path.startswith(('/cars/', '/motorcycles/', '/planes/', '/supercars/', '/best/', '/stats/', '/check-engine-light/', '/best-gas-mileage/', '/electric/')):
        body += f'<p class="upd">Updated <time datetime="{_d}">{_dl}</time></p>'; ld = list(ld or []) + [{"@context": "https://schema.org", "@type": "WebPage", "url": BASE + path, "name": title, "dateModified": _d}]
    body = auto_hero(body, vis)
    url = BASE + path; ld = list(ld or []) + [crumbs(path, title)]
    lds = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    beacon = f"<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{{\"token\": \"{CF}\"}}'></script>" if CF else ''
    if GA: beacon += f'<script src="/assets/ga.js?v=3" data-ga="{GA}" defer></script>'
    if ADS and path not in ('/thanks/',): beacon += f'<script src="/assets/ads.js?v=1" data-ads="{ADS}" defer></script>'   # 11-09: ga.js loads gtag.js (180 KB) after the page has loaded
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="{kind}"><meta property="og:site_name" content="The Lemon Index"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}{img or "/assets/og.png"}"><meta name="twitter:card" content="summary_large_image">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' https://static.cloudflareinsights.com https://challenges.cloudflare.com https://www.googletagmanager.com https://*.googlesyndication.com https://*.doubleclick.net https://*.google.com https://*.googleadservices.com https://*.gstatic.com https://*.adtrafficquality.google https://*.googletagservices.com; frame-src https://challenges.cloudflare.com https://*.googlesyndication.com https://*.doubleclick.net https://*.google.com https://*.googleadservices.com https://*.gstatic.com https://*.adtrafficquality.google https://*.googletagservices.com; style-src 'self' 'unsafe-inline'; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://cloudflareinsights.com https://*.google-analytics.com https://*.analytics.google.com https://*.googletagmanager.com https://vpic.nhtsa.dot.gov https://lemon-survey.elift08.workers.dev https://*.googlesyndication.com https://*.doubleclick.net https://*.google.com https://*.googleadservices.com https://*.gstatic.com https://*.adtrafficquality.google https://*.googletagservices.com; object-src 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="google-adsense-account" content="{ADS}"><meta name="msvalidate.01" content="2F84C8106BB577C5860ABE6EC15825EC"><link rel="icon" href="/assets/icon-64.png"><link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preload" href="/assets/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css?v=1109f"><link rel="stylesheet" href="/assets/gh.css?v=2"><script src="/assets/gh.js?v=1" defer></script><script src="/assets/nav.js?v=1105" defer></script>{lds}</head>
<body>{gh_header(path)}
<main>{body}{CITE if path.startswith('/cars/') else ''}{'' if path == '/vote/' else ask_html(path)}</main>
<footer class="foot"><div class="cta"><div><h2>New car studies, straight from the data.</h2><p>Every study becomes a video. Subscribe to see the next one first.</p></div><a class="btn" href="{YT}?sub_confirmation=1" rel="noopener">Subscribe on YouTube</a></div>
<p class="socs"><a href="{YT}" rel="noopener">YouTube</a> · <a href="{TT}" rel="noopener">TikTok</a> · <a href="{IG}" rel="noopener">Instagram</a> · <a href="/method/">How the index works</a> · <a href="/compare/">Compare cars</a> · <a href="/car-loan-rates/">Car loan rates</a> · <a href="/vote/">Vote</a> · <a href="/data/">Free data</a> · <button class="supl" type="button">Support the Lemon Index</button></p>
<p class="fine"><a href="/terms/">Terms</a> · <a href="/privacy/">Privacy</a> · <a href="/refunds/">Refunds</a> · <a href="/contact/">Contact</a><br>© {TODAY[:4]} The Lemon Index. Built from public NHTSA complaint data and published U.S. sales figures. Not affiliated with any automaker. Not a repair-cost or safety rating.</p></footer><script src="/assets/explorer.js?v=1103v6" defer></script><script src="/assets/support.js?v=1107" defer></script><script src="/assets/lookup.js?v=1103" defer></script>{beacon}</body></html>'''
    f = os.path.join(OUT, path.strip('/'), 'index.html') if path.endswith('/') else os.path.join(OUT, path.strip('/'))
    os.makedirs(os.path.dirname(f), exist_ok=True)
    for _try in range(6):   # 11-09: Windows sometimes holds a just-written file for a moment (antivirus/indexer): retry instead of dying mid-build
        try: open(f, 'w', encoding='utf-8').write(doc); break
        except PermissionError:
            if _try == 5: raise
            import time; time.sleep(.5)

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
    """The Lemon gauge: a speedometer from 0 to 300 (100 = the average car); green below 75, gray around average, red above 125.
    The needle swings in when the dial scrolls into view (assets/nav.js adds .in). Scores past 300 peg the needle and still print the real number."""
    cx, cy, r = 120, 118, 92
    pt = lambda v, rr=r: (cx - rr * __import__('math').cos(__import__('math').pi * min(v, 300) / 300), cy - rr * __import__('math').sin(__import__('math').pi * min(v, 300) / 300))
    def arc(a, b, col):
        (x1, y1), (x2, y2) = pt(a), pt(b)
        return f'<path d="M{x1:.1f} {y1:.1f}A{r} {r} 0 0 1 {x2:.1f} {y2:.1f}" stroke="{col}" />'
    ticks = ''.join(f'<line x1="{pt(v, r - 16)[0]:.1f}" y1="{pt(v, r - 16)[1]:.1f}" x2="{pt(v, r - 24 if v % 100 else r - 30)[0]:.1f}" y2="{pt(v, r - 24 if v % 100 else r - 30)[1]:.1f}" />' for v in range(0, 301, 25))
    nums = ''.join(f'<text x="{pt(v, r - 44)[0]:.1f}" y="{pt(v, r - 44)[1] + 5:.1f}">{v}</text>' for v in (0, 100, 200, 300))
    a = min(li, 300) / 300 * 180 - 90
    cls = 'good' if li < 75 else 'bad' if li > 125 else 'mid'
    return (f'<figure class="gauge {cls}" data-gauge style="--a:{a:.1f}deg;width:{size}px" aria-label="Lemon Index {li}: {E(plain(li))}">'
            f'<svg viewBox="0 0 240 150" role="img" aria-hidden="true"><g class="g-arc" fill="none" stroke-width="16" stroke-linecap="butt">{arc(0, 74, "#1a8f4c")}{arc(76, 124, "#c9ccd1")}{arc(126, 300, "#e8141c")}</g>'
            f'<g class="g-tick">{ticks}</g><g class="g-num">{nums}</g><g class="g-ndl"><path d="M{cx - 4} {cy}L{cx} {cy - r + 6}L{cx + 4} {cy}Z" /><circle cx="{cx}" cy="{cy}" r="11" /><circle class="g-hub" cx="{cx}" cy="{cy}" r="5" /></g></svg>'
            f'<figcaption><b>{li}</b>{"<span>Lemon Index · 100 = average car</span>" if label else ""}</figcaption></figure>')

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
    """A model's photo: the exact year when we have it, else its newest checked year, else the model photo. {src, w, h, author}."""
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
def tiles():
    from PIL import Image
    yrs = {f['id']: f for f in json.load(open('data/years.json', encoding='utf-8'))}
    fid = lambda c: c['id']
    def img(ph, alt, cls=''):
        return f'<img class="{cls}" src="{ph["src"]}"{rset(ph["src"], SZ_TWO if cls else "(max-width: 600px) 88vw, 460px")} alt="{E(alt)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy">' if ph else ''
    who = []
    def car_tile(c, eyebrow, cls):
        ph = mphoto(c['id']); ph and who.append(ph['author'].split('\ufffd')[0].strip())
        return (f'<a class="tile {cls}" href="/cars/{c["id"]}/"><div class="tt"><p class="te">{eyebrow}</p><h2>{E(c["name"])}.</h2>'
                f'<p class="ts">{E(plain(c["li"]))}.</p><span class="tl">See every year <i>›</i></span></div>'
                f'<div class="tp">{img(ph, c["name"])}<span class="tsc {"good" if c["li"] < 100 else "bad"}">{c["li"]}</span></div></a>')
    best, worst = CARS[0], CARS[-1]
    a, b = mphoto('toyota-rav4', 2019), mphoto('honda-cr-v', 2017)
    for ph in (a, b): ph and who.append(ph['author'].split('\ufffd')[0].strip())
    vin = mphoto('toyota-camry', 2019); vin and who.append(vin['author'].split('\ufffd')[0].strip())
    def vimg(name):
        w, h = Image.open(f'assets/vote/{name}.webp').size
        return {'src': f'/assets/vote/{name}.webp', 'w': w, 'h': h}
    who += ['Ghostofakina', 'Kevauto']
    t = [car_tile(best, 'Most reliable', 't-good'), car_tile(worst, 'Biggest lemon' + ('*' if worst['est'] else ''), 't-bad'),
         f'<a class="tile" href="/compare/"><div class="tt"><p class="te">Compare</p><h2>Any two cars.</h2><p class="ts">Side by side, year by year.</p><span class="tl">Compare cars <i>›</i></span></div>'
         f'<div class="tp tp2">{img(a, "Toyota RAV4", "l")}{img(b, "Honda CR-V", "r")}</div></a>',
         f'<a class="tile" href="/vote/"><div class="tt"><p class="te">Vote</p><h2>Chevy or Ford?</h2><p class="ts">Plus best brand and worst insurer.</p><span class="tl">Cast your vote <i>›</i></span></div>'
         f'<div class="tp tp2">{img(vimg("chevy"), "Chevy Silverado", "l")}{img(vimg("ford"), "Ford F-150", "r")}</div></a>',
         f'<a class="tile" href="/vin/"><div class="tt"><p class="te">VIN check</p><h2>Open recalls.</h2><p class="ts">On the exact car you\'re looking at.</p><span class="tl">Check a VIN <i>›</i></span></div>'
         f'<div class="tp">{img(vin, "Toyota Camry")}</div></a>',
         f'<a class="tile t-dark" href="/data/"><div class="tt"><p class="te">Free data</p><h2>Take it. Credit us.</h2><p class="ts">Every score, as a spreadsheet.</p><span class="tl">Download <i>›</i></span></div>'
         f'<div class="tp tsheet"><div class="tsh">' + ''.join(f'<span>{E(c["name"])}</span><span>{c["years"].split("-")[0]}–{c["years"].split("-")[-1][-2:]}</span><b class="{"good" if c["li"] < 100 else "bad"}">{c["li"]}</b>' for c in (CARS[0], CARS[1], CARS[len(CARS) // 2], CARS[-2], CARS[-1])) + '</div></div></a>']
    cr = ' · '.join(dict.fromkeys(w for w in who if w))
    return f'<section class="tiles">{"".join(t)}</section><p class="tiles-cr">Photos: {E(cr)} (Wikimedia Commons, CC BY-SA)' + (' · *Tesla uses estimated sales.' if worst['est'] else '') + '</p>'

def pimg(ph, alt, cls=''):
    return f'<img class="{cls}" src="{ph["src"]}"{rset(ph["src"], SZ_TWO if cls else SZ_ONE)} alt="{E(alt)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy">' if ph else ''
def who(*phs): return [ph['author'].split('\ufffd')[0].strip() for ph in phs if ph and ph.get('author')]
def pcredit(names): names = list(dict.fromkeys(n for n in names if n)); return f'<p class="ph-cr">Photos: {E(" · ".join(names))} (Wikimedia Commons)</p>' if names else ''
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

def hero_cards():
    """Two real cars, one great and one a lemon, as stacked report cards with their dial (exact-year Commons photos from data_photos.py)."""
    ph = json.load(open('data/photos.json', encoding='utf-8')); yrs = {f['id']: f for f in json.load(open('data/years.json', encoding='utf-8'))}
    out = []
    for fid, y, cls in (('toyota-rav4', 2016, 'hc-1'), ('jeep-cherokee', 2014, 'hc-2')):
        f = yrs[fid]; v = next(w for w in f['years'] if w['y'] == y); im = ph[fid][str(y)]
        top = (v.get('parts') or [['', 0]])[0][0]
        out.append(f'<a class="hc {cls}" href="/cars/{fid}/{y}/"><img src="{im["src"]}"{rset(im["src"], "(max-width: 620px) 44vw, (max-width: 999px) 94vw, 260px")} alt="{y} {E(f["name"])}" width="{im["w"]}" height="{im["h"]}" fetchpriority="high">'
                   f'<div class="hc-b"><div><b>{y} {E(f["name"])}</b><span>{E(plain(v["li"]))}</span>{f"<small>Top complaint: {E(top.split(",")[0])}</small>" if top else ""}</div>{gauge(v["li"], 128, False)}</div></a>')
    return f'<div class="hcs">{"".join(out)}<p class="hc-cr">Photos: Wikimedia Commons</p></div>'

# ---- home: the car finder first (10-29), how to read a score, the explorer, then best vs worst side by side, then brands
best4, worst4 = CARS[0], CARS[-1]
# 10-30: Google showed /method/ for "lemon index" (its h1 was the only one saying the brand), so the home h1 now carries the name too.
# 11-08 internal links: the home page links straight to the model pages people search most, with "reliability" in the link text. First the
# ones Search Console shows just off page 1 of Google (C-Class #11, Mazda3 #10, Audi Q5 #10, Equinox #13 on 11-08), then best sellers.
POP_FIRST = ['mercedes-benz-c-class', 'mazda3', 'audi-q5', 'chevrolet-equinox', 'honda-accord', 'toyota-camry', 'bmw-3-series', 'audi-a4']
def pop_checks(n=28):
    have = {f['id'] for f in json.load(open('data/years.json', encoding='utf-8'))}; by = {c['id']: c for c in CARS}
    ids = list(dict.fromkeys([i for i in POP_FIRST if i in by and i in have] + [c['id'] for c in sorted(CARS, key=lambda c: -c['sold']) if c['id'] in have]))[:n]
    return ('<section class="hpop"><h2>Reliability checks people run most.</h2><p class="hpl">'
            + ''.join(f'<a href="/cars/{i}/">{E(by[i]["name"])} reliability</a>' for i in ids) + '</p></section>')
page('/', "Lemon Index (LemonIndex): Look Up Any Car's Problems by Year", "Look up any car's problems by model year, 2000 to 2025: its reliability score, top problem areas and real owner complaints, from 1.6 million complaints filed with the government. 100 is the average car.", f'''
<div class="home"><div class="hhero">{finder(h='<span class="fbrand">The Lemon Index</span>Look up any car.', foot=f'<p class="fnote">From {COUNTED:,} owner complaints filed with the U.S. government.</p>')}{hero_cards()}</div>
<section class="hread"><h2>100 is the average car. <span class="h2s">Lower is better.</span></h2>
<div class="scale"><div class="sbar"><i style="left:{min(96, best4["li"] / 3.5):.1f}%" title="{E(best4["name"])}, {best4["li"]}"></i></div><div class="sl"><span>25 · ¼ the complaints</span><span>100 · average</span><span class="bad">300 · 3×</span></div></div></section>
{tiles()}
{explorer()}
{pop_checks()}
<section><h2>Every brand, best to worst.</h2>{bars(BRANDS, 330, 'two')}<p class="note">* Porsche is a small sample (2 models, 258,000 sold). Tesla uses estimated U.S. sales.</p></section>
{share_line("Before you buy a used car, look up its problems by model year. Free, from real owner complaints:")}
<section class="faq"><h2>Questions</h2>{faq}</section></div>''',
     ld=[{"@context": "https://schema.org", "@type": "WebSite", "name": "The Lemon Index", "alternateName": ["Lemon Index", "LemonIndex", "lemonindex", "lemonindex.com"], "url": BASE + '/'},
         {"@context": "https://schema.org", "@type": "Organization", "name": "The Lemon Index", "alternateName": ["Lemon Index", "LemonIndex", "lemonindex.com"], "url": BASE + '/', "logo": BASE + '/assets/icon-180.png', "sameAs": [YT, TT, IG]},
         {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}])

# ---- study
page(STUDY, 'The Most Reliable Cars, According to 1.6 Million Owner Complaints', 'The most and least reliable cars and brands in the U.S., ranked by NHTSA safety complaints per 100,000 sold. Toyota 4Runner 26, Lexus 30, Tesla 322 (est.).', f'''
<article class="study"><p class="kicker">Study #1 · {TODAY}</p><h1>The Most Reliable Cars, According to 1.6 Million Owner Complaints</h1>
<p class="lede">The Toyota 4Runner drew about a quarter of the complaints of the average car. The Tesla Model S drew more than four times as many. Here's every number.</p><p>{share_btn("The most reliable cars, ranked by 1.6 million owner complaints. The 4Runner drew a quarter of the average car's:")}</p>
<div class="stats"><div><b>1,607,537</b><span>complaints in NHTSA's file since 1995</span></div><div><b>{COUNTED:,}</b><span>counted: filed within 3 years of a 2010-2022 model year</span></div><div><b>131</b><span>models ranked</span></div><div><b>22</b><span>brands</span></div><div><b>2010-2022</b><span>model years</span></div></div>
<p class="sub">How to read it: the Lemon Index compares a car's safety complaints per car sold with the average car of the same model years. <b>100 is average.</b> 26 means about a quarter of the average car's complaints; 430 means 4.3 times as many.</p>
<div class="stack"><div><h2>Most reliable: the top 10</h2><div class="tw"><table><thead><tr><th>#</th><th>Model</th><th>Index</th><th>Compared with average</th><th>Sold in the U.S.</th></tr></thead><tbody>{best_rows}</tbody></table></div>
<p class="note">What it means for you: a long-running model with a low index is the safest bet. Most of this list has been on sale, mostly unchanged, for a decade. Sold = U.S. sales across 2010-2022.</p></div>
<div><h2>Least reliable: the bottom 10</h2><div class="tw"><table><thead><tr><th>Model</th><th>Index</th><th>Compared with average</th><th>Top complaint (share of its complaints)</th></tr></thead><tbody>{worst_rows}</tbody></table></div>
<p class="note">What it means for you: one part can sink a car. Check the top complaint for the exact model year before you buy. * Tesla uses published sales estimates.</p></div></div>
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
page('/studies/', 'Car Reliability Studies: Rankings From Owner Complaints | Lemon Index', 'Every Lemon Index study: the most and least reliable cars, brands and electric cars, measured with 1.6 million NHTSA owner complaints and U.S. sales.', f'''
<div class="pg">{phero('Studies', 'Studies.', 'Millions of public records. One clear ranking each.')}
<section class="tiles">
<a class="tile" href="{STUDY}"><div class="tt"><p class="te">Study #1</p><h2>The most reliable cars.</h2><p class="ts">131 models. 1.6 million owner complaints.</p><span class="tl">Read the study <i>›</i></span></div><div class="tp">{pimg(mphoto('toyota-4runner'), 'Toyota 4Runner')}</div></a>
<a class="tile" href="/electric/"><div class="tt"><p class="te">Electric cars</p><h2>The most reliable EVs.</h2><p class="ts">22 electric cars, plus fires and fuel cost.</p><span class="tl">See the ranking <i>›</i></span></div><div class="tp">{pimg(mphoto('tesla-model-s'), 'Tesla Model S')}</div></a></section>
{pcredit(who(mphoto('toyota-4runner'), mphoto('tesla-model-s')))}
<section class="pg-next"><h2>Coming next.</h2><p class="ph-s">Cars that pass 300,000 miles. The worst cars ever made. The best used cars under $10K.</p></section>
{share_line("Which cars have the fewest problems? Free studies from 1.6 million owner complaints:")}</div>''',
     ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Car Reliability Studies", "url": BASE + '/studies/', "hasPart": [{"@type": "Article", "headline": "The Most Reliable Cars, According to 1.6 Million Owner Complaints", "url": BASE + STUDY}]}])

# ---- method
def faq_ld(qa): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": t}} for q, _, t in qa]}
METHOD_QA = [('Is it per car sold?', "Yes. Every score divides a car's complaints by how many were sold in the U.S. So Ford outselling Chevy doesn't make Ford look worse; a car only scores badly if it drew more complaints for each car on the road."), ("Isn't it just owners who skip maintenance?", "We only count complaints filed in a car's first 3 years, when it's nearly new and usually still under the factory warranty. That points at problems the car left the factory with, not a 15-year-old car that missed its oil changes."), ('Does it tell me how long a car will last?', "No. It measures early complaints, not lifespan. A truck can draw a lot of complaints in its first years and still run past 300,000 miles. Use it to see which years had problems, then check the car's own history."), ('Why so few complaints for a problem everyone knows about?', "Most owners never file with the government; they just go to a mechanic. So the counts are a small slice of real failures. That's fine for comparing cars, because every car is measured the same way, but don't read a count as the number of cars that broke."), ('Can you split it by engine or trim?', 'The government files list make, model and year, not the engine. Where the model name gives the engine away (BMW files the 328i and 335i separately, for example), we can split by it. Otherwise a score covers every engine sold that year.')]
page('/method/', 'Method: How We Score Car Reliability | The Lemon Index', 'How we turn NHTSA safety complaints and U.S. sales into one reliability number per car, plus the caveats that come with it.', '''
<div class="pg">''' + phero('How it works', 'One number per car.', 'Owner complaints per car sold, against the average car.') + '''<article class="study"><div class="hw"><div><b>1</b><h3>Count complaints</h3><p>Every safety complaint owners filed with the U.S. government (NHTSA) in the car&#39;s first 3 years.</p></div>
<div><b>2</b><h3>Divide by cars sold</h3><p>So a car that sold a million doesn&#39;t look worse than one that sold ten thousand.</p></div>
<div><b>3</b><h3>Compare with the average car</h3><p>100 = average. 50 = half the complaints. 200 = double.</p></div></div>
<div class="hwm"><div class="ym-bar"><i class="ym-avg" style="left:40%"><span>average car = 100</span></i><i class="ym-pin" style="left:12%"><b>30: great</b></i><i class="ym-pin" style="left:80%"><b>200: lemon</b></i></div><div class="ym-ends"><span>fewer complaints</span><span>more complaints</span></div></div>
<p><a class="btn" href="/cars/">Look up your car</a></p>
<details class="yd"><summary>The details</summary><ol class="beats"><li><b>Complaints:</b> the full NHTSA owner-complaint file (1,607,537 vehicle complaints, 1995 to October 2026).</li>
<li><b>Sales:</b> U.S. sales per model per year from automakers' published figures. Tesla doesn't report by model, so we use published estimates and say so.</li>
<li><b>Same window for every car:</b> a complaint counts only if it was filed within 3 years of the model year.</li>
<li><b>Rate:</b> complaints per 100,000 cars sold, matched model year to sales year. When a new model's first cars sold the calendar year before its model year, those sales are counted with the first model year.</li>
<li><b>Index:</b> each car's rate against the average car of the same model years.</li></ol></details>
<h2>What it doesn't measure</h2><p>A complaint is a safety complaint filed with the government, not a repair record. Fleet and rental-heavy models have fewer owners filing. Luxury lessees often go straight to the dealer. Some owners file more readily than others. Read it as early-life safety complaints, not total cost of ownership.</p>
<h2>Also on every car page</h2><ul><li><b>Recalls:</b> every NHTSA safety recall campaign for that model year (NHTSA recalls API).</li>
<li><b>Crash tests:</b> NHTSA 5-star safety ratings for each body style tested (model years 2011 on).</li>
<li><b>Fuel economy:</b> EPA combined mpg and yearly fuel cost from fueleconomy.gov, across the versions sold that year.</li>
<li><b>When problems show up:</b> the odometer reading owners gave in their complaints. Unlike the score, this uses every complaint for the model year, because high-mileage failures come years later. Readings of 0 or over 400,000 miles are left out.</li>
<li><b>How serious:</b> complaints in which the owner reported a crash, a fire, an injury, a death or a tow. Owners report these; NHTSA doesn&#39;t confirm the cause.</li></ul>
<h2>What people ask</h2>''' + qa_fold('''<h3>Is it per car sold?</h3><p>Yes. Every score divides a car&#39;s complaints by how many were sold in the U.S. So Ford outselling Chevy doesn&#39;t make Ford look worse; a car only scores badly if it drew more complaints for each car on the road.</p><h3>Isn&#39;t it just owners who skip maintenance?</h3><p>We only count complaints filed in a car&#39;s first 3 years, when it&#39;s nearly new and usually still under the factory warranty. That points at problems the car left the factory with, not a 15-year-old car that missed its oil changes.</p><h3>Does it tell me how long a car will last?</h3><p>No. It measures early complaints, not lifespan. A truck can draw a lot of complaints in its first years and still run past 300,000 miles. Use it to see which years had problems, then check the car&#39;s own history.</p><h3>Why so few complaints for a problem everyone knows about?</h3><p>Most owners never file with the government; they just go to a mechanic. So the counts are a small slice of real failures. That&#39;s fine for comparing cars, because every car is measured the same way, but don&#39;t read a count as the number of cars that broke.</p><h3>Can you split it by engine or trim?</h3><p>The government files list make, model and year, not the engine. Where the model name gives the engine away (BMW files the 328i and 335i separately, for example), we can split by it. Otherwise a score covers every engine sold that year.</p>''') + '''<h2>Using the data</h2><p>Free to cite with a link to lemonindex.com (CC BY 4.0). <a href="/data/">Download it</a>.</p></article></div>''',
     ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": "How We Score Car Reliability", "url": BASE + '/method/', "about": "Car reliability measured as NHTSA safety complaints per 100,000 U.S. sales"}, faq_ld([(q, '', a) for q, a in METHOD_QA])])

# ---- model-year lookup (10-29, Elijah: "a per year / model lookup so people can look at their car's exact issues").
# data/years.json comes from data_years.py: per family and model year the index, complaints, sold, top problem areas and up to 3 owner complaints.
YEARS = [f for f in json.load(open('data/years.json', encoding='utf-8')) if f['name'] in BYNAME]
# 10-29: model years 2000-2009 added (Elijah's car is a 2008). Their scores are rough (fewer owners filed online, launch years sold partly the
# calendar year before), so a pre-2010 year with under 20 complaints gets no score, and its page says the score is rough.
for f in YEARS:
    for v in f['years']: v['ok'] = (v['y'] >= 2010 and not v.get('early')) or v['n'] >= 20   # 11-03: early-read years (2023-2025) need 20+ complaints too
LIS = lambda v: v['li'] if v['ok'] else '–'
CLS = lambda v: ('bad' if v['li'] > 110 else 'good') if v['ok'] else 'good'
PLN = lambda v: plain(v['li']) if v['ok'] else 'too few complaints to score'
CARU = lambda f, y=None: f'/cars/{f["id"]}/' + (f'{y}/' if y else '')
yurls = []

# ---- 10-31 extras (Elijah: "do all 5"): recalls, crash tests and fuel economy from the official APIs (data_fetch_api.py),
# when problems show up (odometer at complaint) and how serious they were (data_extras_local.py).
_load = lambda p: json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
XL, XA = _load('data/extras_local.json'), _load('data/extras_api.json')
def extra(fid, y):
    d = dict(XL.get(fid, {}).get(str(y), {})); d.update(XA.get(fid, {}).get(str(y), {}) or {}); return d
# ---- 11-04 YouTube videos (data_yt.py): what owners/buyers watch most, by views, with the top video for each topic. Mobile first:
# 4 topics open, the rest behind "Show more"; each topic's top video is one big tap target (thumbnail + 2-line title).
YTV = _load('data/yt.json')
def _vw(n): return f'{n / 1e6:.1f}M' if n >= 1e6 else f'{round(n / 1e3):,}K' if n >= 1e3 else str(n)
def ytfix(key, y=None):
    d = next((e for e in YTV.get(key, []) if e['years'] is None or y in e['years']), None)
    if not d or not d['topics']: return ''
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
    cst = d.get('costs'); costh = ''
    if cst:
        M = lambda n: f'${n / 1e6:.2f}M' if n >= 1e6 else f'${n:,.0f}'
        R = lambda n: M(float(f'{n:.2g}')) if n >= 100 else M(n)   # ranges: 2 significant figures
        HEAR = lambda x: f'<a class="yc-h" href="https://www.youtube.com/watch?v={x["id"]}&t={x["t"]}s" target="_blank" rel="noopener nofollow">Hear it &#9654;</a>'
        big = []
        if cst.get('paid'):
            pp = cst['paid']; who = ' · ' + ', '.join(w for w in ([f'{pp["private"]} private party'] if pp['private'] else []) + ([f'{pp["dealer"]} from dealers'] if pp['dealer'] else []))
            big.append(f'<div class="yc-b"><small>Price owners say they paid</small><b>{M(pp["median"])}</b><span>middle of {pp["n"]} prices in {pp["videos"]} videos{who if (pp["private"] or pp["dealer"]) else ""}; most between {R(pp["lo"])} and {R(pp["hi"])}.</span>{HEAR(pp)}</div>')
        if cst.get('used'):
            pu = cst['used']; big.append(f'<div class="yc-b"><small>Used prices people quote</small><b>{M(pu["median"])}</b><span>middle of {pu["n"]} prices in {pu["videos"]} videos; most fall between {R(pu["lo"])} and {R(pu["hi"])}.</span>{HEAR(pu)}</div>')
        if cst.get('msrp'):
            pm = cst['msrp']; big.append(f'<div class="yc-b"><small>New price people quote</small><b>{M(pm["median"])}</b><span>middle of {pm["n"]} quotes in {pm["videos"]} videos; most between {R(pm["lo"])} and {R(pm["hi"])}.</span>{HEAR(pm)}</div>')
        rows = ''.join(f'<li><span>{E(k)}</span><b>{M(x["median"])}</b><small>{x["videos"]} videos · most {R(x["lo"])}–{R(x["hi"])}</small>{HEAR(x)}</li>' for k, x in cst['items'])
        costh = (f'<div class="ycost"><h3>What owners say it costs</h3>' + (f'<div class="yc-bs">{"".join(big)}</div>' if big else '')
                 + (f'<ul class="yc-l">{rows}</ul>' if rows else '')
                 + '<p class="yc-cap">Dollar amounts people say out loud in these videos (median, so one wild number can&#39;t swing it). Not verified sales; real prices depend on year, miles, condition and where you live. Tap Hear it to jump to the moment.</p></div>')
    cap = 'Views show how many people looked up each fix, not how often it breaks.' if d['kind'] == 'repair' else 'Views show what people watch most, not how often something goes wrong.'
    return (f'<section class="yc yfx" id="diy"><h2>{d["head"]}</h2><p class="yf-s">From {d["n"]} YouTube videos about the {E(d["gen"])}, {_vw(d["views"])} views.{same}</p>'
            + (costh + '<h3 class="yf-g yf-g1">Most-watched topics</h3>' if costh else '') + f'<ol class="yfl">{first}</ol>' + (f'<details class="yf-more"><summary>Show {len(tp) - 4} more</summary><ol class="yfl">{rest}</ol></details>' if rest else '')
            + (f'<h3 class="yf-g">Before you buy, watch</h3><div class="ygs">{cards}</div>' if cards else '')
            + f'<p class="yc-cap">{cap} Videos belong to their creators; we link to them.</p></section>')
mi = lambda n: f'{int(n):,} miles'
REPORT_NOTE = '<p class="note">The full Lemon Index report adds the mileage for every problem area, every recall in plain English and what to check before you buy. <b>Coming soon.</b></p>'
RPART = lambda s: PART.get(s.split(':')[0], s.split(':')[0].lower()).replace('service brakes, hydraulic', 'brakes')
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
    li = ''.join(f'<li><b>{E(RPART(r["part"]))}</b> <small>{E(r["date"][-4:])}</small><br>{E(rsum(r))} <small class="muted">NHTSA {E(r["id"])}</small></li>' for r in rs[:6])
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
        cost = f' About <b>${rng(m["cost"])}</b> a year in {"electricity" if m.get("ev") else "fuel"} (EPA estimate at today&#39;s prices).' if m.get('cost') else ''
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
def ybars_yt(f, cur, sc):
    mx = max(120, max(v['li'] for v in f['years'] if v['ok']) * 1.08); byy = {v['y']: v for v in f['years']}
    ys = sorted(set(byy) | {int(y) for y in sc})
    got = sorted(((s['score'], s['videos'], int(y)) for y, s in sc.items() if s.get('score') is not None), reverse=True)
    RK = {y: i + 1 for i, (_, _, y) in enumerate(got)}; lo, hi = got[-1][0], got[0][0]
    def row(y):
        v = byy.get(y); s = sc.get(str(y)) or {}; ss = s.get('score'); rk = RK.get(y)
        # bar = score stretched over the model's own range (YouTube scores sit close to 50); the number is the rank, #1 = YouTube's favorite year
        w = 8 + 92 * (ss - lo) / max(1, hi - lo) if ss is not None else 0
        tier = '' if rk is None else (' up' if rk <= len(RK) / 3 else ' dn' if rk > len(RK) * 2 / 3 else '')
        yt = (f'<span class="bt ytb{tier}"><i style="width:{w:.0f}%"></i></span><b class="ytn">#{rk}</b>' if ss is not None else '<span class="bt ytb"></span><b class="ytn mute">·</b>')
        tip = f'{E(f["name"])} {y}: ' + (f'Lemon Index {v["li"]}' if v and v['ok'] else 'no complaint score') + (f'. YouTube rank #{rk} of {len(RK)} (score {ss}, {s["videos"]:g} videos)' if ss is not None else '. Too few YouTube videos to rank')
        if v:
            return (f'<a class="b {CLS(v)}{" cur" if y == cur else ""}" href="{CARU(f, y)}" data-tip="{tip}."><span class="bn">{y}</span><span class="bt"><i style="width:{min(100, v["li"] / mx * 100) if v["ok"] else 0:.1f}%"></i>'
                    f'<em style="left:{100 / mx * 100:.1f}%"></em></span><b>{LIS(v)}</b>{yt}</a>')
        return f'<div class="b old" data-tip="{tip}."><span class="bn">{y}</span><span class="bt na"></span><b class="mute">·</b>{yt}</div>'
    return (f'<div class="bars yb yt2"><div class="bl yth2" aria-hidden="true"><span></span><span>Complaints <em>lower = better</em></span><span></span><span>YouTube rank <em>#1 = favorite</em></span><span></span></div>'
            + ''.join(row(y) for y in ys) + '</div>')
def yt_note(f):
    sc = YTS.get(f['id'])
    if not sc: return ''
    n = round(sum(s.get('videos') or 0 for s in sc.values())); yrs = sorted(int(y) for y, s in sc.items() if s.get('score') is not None)
    best = max((int(y) for y, s in sc.items() if s.get('score') is not None), key=lambda y: (sc[str(y)]['score'], sc[str(y)]['videos'], y))   # 11-08: same tie-break as the bars' #1 (score, then videos)
    return (f'<p class="yc-cap"><b>YouTube rank:</b> we read {n:,} YouTube videos about the {f["name"]}, {yrs[0]} to {yrs[-1]}, and ranked every year by how much they praise it '
            f'vs. how much they talk about problems. YouTube&#39;s favorite: <b>{best}</b>. Old cars rank lower partly because most of their videos are repair and restoration videos. A gray dot means too few videos to rank.</p>')
# 11-08 (Elijah: "make the top of every car model page answer '<car> reliability' from the YouTube stuff, maybe a different ranking"):
# people search "Mercedes C-Class reliability", so the model page opens with that question, a plain answer and a 3-tile scorecard.
# YouTube scores climb with newer model years for every car (old cars = repair videos), so each year is compared with the median
# of every car of the SAME model year (>= 10 videos). Model rank = video-weighted average of those gaps. It measures how positively
# owners and reviewers talk, not a failure rate, and the page says so. "Safest year" = the year complaints and YouTube agree on most.
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
def safest_year(fid, sc):
    """The scored year that complaints (lower Lemon Index) and YouTube (vs. same-age cars) rank best together; None without YouTube data."""
    a = yt_adj(fid); both = [v for v in sc if v['y'] in a and v['li'] <= 110]   # a year with more complaints than average is never the safest
    if len(both) < 3: return None
    pc = {v['y']: i / (len(both) - 1) for i, v in enumerate(sorted(both, key=lambda v: v['li']))}
    py = {v['y']: i / (len(both) - 1) for i, v in enumerate(sorted(both, key=lambda v: -a[v['y']]))}
    return min(both, key=lambda v: (pc[v['y']] + py[v['y']], v['li']))
def rel_answer(f, c, snm, best, bad3, sy):
    """('Yes.', one plain sentence) for 'Is the <car> reliable?', from complaints first, YouTube second."""
    li = c['li']
    word = 'Yes, very.' if li < 50 else 'Yes.' if li < 85 else 'About average.' if li <= 115 else 'Not really.'
    _r = YTR.get(f['id'])
    if _r and li <= 115:   # NHTSA counts safety complaints only; when YouTube owners clearly disagree, don't oversell
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
    pick = sy or best; av = sorted(v['y'] for v in bad3 if v['y'] != pick['y'])
    AND = lambda xs: ', '.join(map(str, xs[:-1])) + (' and ' if len(xs) > 1 else '') + str(xs[-1])
    if pick['li'] > 110: tail = f'. Even its best year, <b>{pick["y"]}</b>, draws more complaints than average.'
    else: tail = f'. {"Safest" if sy else "Best"} year: <b>{pick["y"]}</b>.'
    if av: tail += f' Avoid <b>{AND(av)}</b>.'
    return word, comp + yt + tail
def rel_top(f, c, snm, ys, sc, best, worst, bad3):
    sy = safest_year(f['id'], sc); word, ans = rel_answer(f, c, snm, best, bad3, sy)
    vc, vw = verdict(c['li']); tiles = [f'<div class="rs {vc}"><small>Owner complaints</small><b>{E(vw)}</b><span>Lemon Index {c["li"]} · 100 = average car</span></div>']
    r = YTR.get(f['id'])
    if r:
        rk, n, vids = r; cl = 'good' if rk <= n / 3 else 'bad' if rk > n * 2 / 3 else 'mid'
        tiles.append(f'<div class="rs {cl}"><small>YouTube owners</small><b>#{rk} <i>of {n}</i></b><span>vs. cars the same age · {vids:,} videos</span></div>')
    if sy: tiles.append(f'<a class="rs good" href="{CARU(f, sy["y"])}"><small>Safest year</small><b>{sy["y"]}</b><span>complaints and YouTube agree</span></a>')
    elif best['li'] <= 110: tiles.append(f'<a class="rs good" href="{CARU(f, best["y"])}"><small>Best year</small><b>{best["y"]}</b><span>fewest complaints per car sold</span></a>')
    else: tiles.append(f'<a class="rs" href="{CARU(f, best["y"])}"><small>Least bad year</small><b>{best["y"]}</b><span>{E(short(best["li"]))}</span></a>')
    if not r: tiles.append(f'<a class="rs bad" href="{CARU(f, worst["y"])}"><small>Worst year</small><b>{worst["y"]}</b><span>{E(short(worst["li"]))}</span></a>' if worst['li'] > 110 else
                           f'<div class="rs"><small>Years to avoid</small><b>None</b><span>no year far above average</span></div>')
    a = yt_adj(f['id']); last = max(v['y'] for v in sc); new = sorted((y for y in a if y > last), key=lambda y: -a[y])
    newer = (f'<p class="rs-new">Looking at a {min(new)} or newer? Those are too new for complaint data, but YouTube owners like the <a href="#years">{new[0]}</a> best.</p>'
             if len(new) >= 2 else '')
    return (f'<h1 class="rel-h">Is the {E(snm).replace("-", "-⁠")} reliable?</h1><p class="ans rel-a"><b>{word}</b> {ans}</p>', f'<div class="rsc">{"".join(tiles)}</div>{newer}', (word + ' ' + html.unescape(re.sub('<[^>]+>', '', ans))))
def ybars(f, cur=None):
    if YTS.get(f['id']): return ybars_yt(f, cur, YTS[f['id']])
    mx = max(120, max(v['li'] for v in f['years'] if v['ok']) * 1.08)
    return (f'<div class="bars yb"><div class="bl" aria-hidden="true"><span></span><span class="al" style="--a:{100 / mx * 100:.1f}%">average car = 100</span><span></span></div>'
            + ''.join(f'<a class="b {CLS(v)}{" cur" if v["y"] == cur else ""}{" early" if v.get("early") else ""}" href="{CARU(f, v["y"])}" data-tip="{E(f["name"])} {v["y"]}: ' + (f'Lemon Index {v["li"]}, {plain(v["li"])}' if v['ok'] else f'only {v["n"]} complaints, too few to score') + f'."><span class="bn">{v["y"]}</span><span class="bt"><i style="width:{min(100, v["li"] / mx * 100) if v["ok"] else 0:.1f}%"></i><em style="left:{100 / mx * 100:.1f}%"></em></span><b>{LIS(v)}</b><small>{("early read · " if v.get("early") else "") + short(v["li"]) if v["ok"] else "few complaints"}</small></a>' for v in f['years']) + '</div>')
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
CMPU = lambda a, b: f'/compare/{a}-vs-{b}/'
cmpu = lambda a, b: CMPU(a, b) if (a, b) in PAIRS else CMPU(b, a)
# ---- 11-02 year-page redesign (Elijah: "less text, bars and charts, numbers that matter, built for someone looking at their own car or one they want to buy")
NICE = lambda p: {'service brakes, hydraulic': 'brakes', 'brakes': 'brakes', 'service brakes, electric': 'brakes (electric)', 'service brakes, air': 'brakes', 'power train': 'transmission & drivetrain',
                  'unknown or other': 'other', 'vehicle speed control': 'speed control', 'equipment': 'equipment & accessories'}.get(p.lower(), p.lower())
def verdict(li):
    if li < 50: return 'good', 'One of the most reliable'
    if li < 85: return 'good', 'Better than average'
    if li <= 115: return 'mid', 'About average'
    if li < 200: return 'bad', 'Worse than average'
    return 'bad', 'Lemon alert'
def meter(li):
    mx = 250; pos = min(li, mx) / mx * 100
    return (f'<div class="ym" role="img" aria-label="Lemon Index {li}; the average car is 100"><div class="ym-bar"><i class="ym-avg" style="left:{100 / mx * 100:.1f}%"><span>average car</span></i>'
            f'<i class="ym-pin" style="left:{pos:.1f}%"><b>{li}{"+" if li > mx else ""}</b></i></div><div class="ym-ends"><span>fewer complaints</span><span>more complaints</span></div></div>')
def timeline(m, comps):
    mx = 200000; P = lambda n: f'{min(n, mx) / mx * 100:.1f}%'
    ticks = ''.join(f'<span style="left:{k / mx * 100:.0f}%">{k // 1000}K</span>' for k in (0, 50000, 100000, 150000, 200000))
    seen = set(); cc = [c for c in comps if c[4] >= 15 and not (NICE(c[0]).split(' (')[0] in seen or seen.add(NICE(c[0]).split(' (')[0]))][:3]
    top = ''.join(f'<li><b>{E(NICE(c[0]))}</b> complaints mostly came at <b>{c[2] // 1000}K–{c[3] // 1000}K</b> miles</li>' for c in cc)
    return (f'<section class="yc"><h2>When owners reported problems. <span class="h2s">From owner complaints to the government.</span></h2><div class="tl"><div class="tl-bar"><i class="tl-band" style="left:{P(m["p25"])};width:calc({P(m["p75"])} - {P(m["p25"])})"></i>'
            f'<i class="tl-mid" style="left:{P(m["median"])}"><b>half by {m["median"] // 1000}K</b></i></div><div class="tl-ticks">{ticks}</div></div>'
            f'<p class="yc-cap">Most owners who filed a complaint with NHTSA had <b>{m["p25"] // 1000}K to {m["p75"] // 1000}K miles</b> on the car ({m["n"]:,} complaints listed the miles). This shows when people who had a problem reported it, not the odds that your car will have it.</p>'
            + (f'<ul class="tl-top">{top}</ul>' if top else '') + '</section>')
X2 = _load('data/extras2.json')
TR = _load('data/trans.json')   # transmission complaints per model-year (data_trans.py)
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
            f'<figcaption>{pcap(ph, who)}</figcaption></figure>')
def year_photo(f, y):
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
            f'<figcaption>{note}{pcap(ph, who)}</figcaption></figure>')
def clean_tsb(t):
    """An automaker repair note in plain words: drop the 'HONDA:' prefix and 'Some 2017-2018 X built before ... may exhibit', fix SHOUTING, skip shop-tool notes."""
    t = t.replace('�', '').replace('…', '').strip()
    if re.search(r'(VCM|IDS|diagnostic|scan tool|procedure|labor|warranty claim|technician|dealer should|service manual|part number)', t, re.I): return None
    t = re.sub(r'^[A-Z][A-Z &-]{1,20}:\s*', '', t)
    t = re.sub(r'^.*?may (exhibit|experience|have|display|produce|develop)\s+(an?\s+|the\s+)?', '', t, flags=re.I)
    if t.isupper() or sum(c.isupper() for c in t) > len(t) * .6: t = t.lower()
    t = t.strip(' ,.;:-')
    t = re.sub(r'(\s+(coming from|from|on|in|when|while|at|with|and|or|to|the|a|an|of|that|during|after|before))+$', '', t, flags=re.I).strip(' ,.;:-')
    if len(t) < 12: return None
    t = t[0].upper() + t[1:]
    return (t[:95].rsplit(' ', 1)[0] + '…') if len(t) > 97 else t
MAKER = lambda name: name.split(' ')[0].replace('Chevrolet', 'Chevy')
TECH = (('esc', 'Stability control'), ('fcw', 'Collision warning'), ('ldw', 'Lane departure warning'))
TWORD = {'Standard': ('good', 'Standard'), 'Optional': ('mid', 'Optional'), 'No': ('bad', 'Not offered')}
# What people type into Google. NHTSA/sales lump the heavy-duty trucks in, so the page says so.
SN = {'ford-f-series': ('Ford F-150', 'Covers the whole F-Series (F-150 plus the F-250/F-350 Super Duty): Ford reports their sales together.'),
      'ram-pickup': ('Ram 1500', 'Covers the whole Ram pickup line (1500, 2500 and 3500): Ram reports their sales together.')}
SNM = lambda f: SN.get(f['id'], (f['name'],))[0]
def year_faq(f, v, y, x, best):
    """Plain questions people search, answered only from our own numbers: [(question, answer html, answer text)]."""
    n = SNM(f); out = []
    if v['ok']:
        li = v['li']; word = ('Yes, it is one of the most reliable' if li < 50 else 'Yes, better than average' if li < 85 else 'About average' if li <= 115 else 'No, it is worse than average' if li < 200 else 'No, it is one of the worst')
        _pl = plain(v["li"]); a = f'{word} by government complaints. It drew {"about the average number of complaints" if _pl.lower() == "about average" else _pl} filed with NHTSA in its first 3 years, per car sold (Lemon Index {v["li"]}; 100 is average, lower is better).'
        if v.get('early'): a = f'It&#39;s too early to be sure. So far it has drawn {plain(v["li"])} per car sold, against other {y} cars after the same time on the road (early Lemon Index {v["li"]}; 100 is average).'
        nb = [w for w in f['years'] if w['ok'] and w['y'] >= 2010]; b2 = min(nb, key=lambda w: w['li']) if nb else best   # pre-2010 scores are rough
        if b2['y'] != y: a += f' The best {n} year by this measure{" since 2010" if nb and b2 is not best else ""} is {b2["y"]}.'
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
    mi_ = x.get('miles')
    if mi_ and mi_.get('n', 0) >= 20: out.append((f'At what mileage do {y} {n} problems start?', f'Half of the owners who gave a mileage reported the problem between {mi_["p25"]:,} and {mi_["p75"]:,} miles. The middle report was at {mi_["median"]:,} miles, from {mi_["n"]:,} complaints.'))
    if v['parts']:
        tr = next((k for p, k in v['parts'] if 'transmission' in p), None)
        out.append((f'Does the {y} {n} have transmission problems?', f'Transmission and drivetrain issues make up {tr}% of its owner complaints.' if tr else f'Transmission and drivetrain issues aren&#39;t among its top 5 complaint areas.'))
    if m and m.get('cost'):
        co = m['cost']; out.append((f'How much does the {y} {n} cost in fuel a year?', f'About ${co[0] if co[0] == co[1] else f"{co[0]} to ${co[1]}"} a year, by the EPA&#39;s current estimate.'))
    if m and m.get('engines') and not m.get('ev'): out.append((f'What engines does the {y} {n} have?', f'{", ".join(m["engines"])}.'))
    good = sorted([w for w in f['years'] if w['ok'] and not w.get('early') and w['y'] >= 2010], key=lambda w: w['li'])
    if len(good) >= 3 and good[0]['y'] != y: out.append((f'What {n} year is better than the {y}?', f'By owner complaints per car sold, the best recent years are {good[0]["y"]}, {good[1]["y"]} and {good[2]["y"]}.'))
    return [(q, a, re.sub('<[^>]+>', '', html.unescape(a))) for q, a in out]
def answer_box(f, v, y, x, best):
    n = E(SNM(f)); rc = x.get('recalls'); m = x.get('mpg'); bits = []
    if v['ok']:
        w = ('one of the most reliable years' if v['li'] < 50 else 'better than average' if v['li'] < 85 else 'about average' if v['li'] <= 115 else 'worse than average' if v['li'] < 200 else 'one of the worst years')
        s1 = f'The {y} {n} is <b>{"so far " if v.get("early") else ""}{w}</b> by owner complaints: {v["n"]:,} complaints in its first 3 years and a Lemon Index of {v["li"]}, where 100 is the average car.'
    else: s1 = f'The {y} {n} has too few complaints to score: {v["n"]:,} in its first 3 years.'
    if v['parts']: bits.append(f'owners complain most about {E(NICE(v["parts"][0][0]))}')
    if rc is not None: bits.append(f'it has {len(rc)} recall{"s" if len(rc) != 1 else ""}')
    if m and not m.get('ev'): c = m['comb']; bits.append(f'it gets {c[0] if c[0] == c[1] else f"{c[0]} to {c[1]}"} mpg combined')
    s2 = (bits[0][0].upper() + bits[0][1:] + (', ' + ', '.join(bits[1:-1]) + (',' if len(bits) > 2 else '') + ' and ' + bits[-1] if len(bits) > 1 else '') + '.') if bits else ''
    s3 = f' The best {n} year is {best["y"]}.' if best['y'] != y else f' It&#39;s the best {n} year we track.'
    return f'<p class="ans">{s1} {s2}{s3}</p>'
# 11-03 (Elijah: "add newer car years... just have a disclaimer"): 2023-2025 are early reads
ASOF = 'October 2026'
EARLY_NOTE = lambda y, nm: (f'<div class="early-n"><b>Early read.</b> The {y} {nm} hasn&#39;t finished its 3-year window yet. This counts every owner complaint filed so far '
                            f'(through {ASOF}) and compares it with other {y} cars, which have had the same time on the road. It can change as more owners file.</div>')
def year_body(f, v, y, x, best, worst, prev, nxt, qs_list, qa=()):
    nm = E(SNM(f)); x2 = X2.get(f['id'], {}).get(str(y), {}); mkr = E(MAKER(f['name']))
    share_txt = (f'{y} {SNM(f)}: {plain(v["li"])} per car sold' if v['ok'] else f'{y} {SNM(f)}: owner complaints and recalls') + (f', {len(x["recalls"])} recalls' if x.get('recalls') else '') + '. Free report:'
    rec = x.get('recalls') or []; m = x.get('mpg'); sf = x.get('safety'); s = x.get('sev') or {}
    if v['ok']:
        cls, word = verdict(v['li'])
        if v.get('early'): word = 'Early read: ' + word[0].lower() + word[1:]
        pl = plain(v['li']); pl = '' if pl.lower() in word.lower() else f' <span>{E(pl)}.</span>'   # no "About average. about average."
        hero = f'<div class="yhero">{gauge(v["li"], 190)}<div class="yverd {cls}"><p><b>{word}.</b>{pl}</p>{{BW}}</div></div>'
    else:
        hero = f'<div class="yverd mid"><p><b>Not enough data.</b> <span>Only {v["n"]} complaints in its first 3 years: too few to score.</span></p>{{BW}}</div>'
    old = '<p class="yc-note">Older model year: fewer owners filed complaints back then, so treat the score as rough.</p>' if y < 2010 else ''
    if v.get('early'): old = EARLY_NOTE(y, nm)
    inv_open = [i for i in x2.get('inv', []) if i['open']]
    badges = ''.join(b for b in [f'<a class="yb bad" href="#inv">Under government investigation</a>' if inv_open else '',
                                 f'<a class="yb" href="#fixes">{x2["tsb"]["n"]} repair notes from {mkr}</a>' if x2.get('tsb') else ''] if b)
    old = (f'<div class="ybs">{badges}</div>' if badges else '') + old
    rng = lambda a: f'{a[0]}' if a[0] == a[1] else f'{a[0]}–{a[1]}'
    facts = [('Owner complaints', f'{v["n"]:,}', 'first 3 years'), ('Recalls', f'{len(rec)}' if 'recalls' in x else '—', 'free fix at any dealer' if rec else 'none on record'),
             ('Fuel economy', f'{rng(m["comb"])} {"MPGe" if m.get("ev") else "mpg"}' if m else '—', 'combined, EPA'),
             (('Crash test', stars(sf['best']), 'NHTSA overall') if sf and sf.get('best') else ('Front crash', stars(x2['old']['front']), 'NHTSA, driver') if (x2.get('old') or {}).get('front') else ('Crash test', '<span class="muted">not rated</span>', 'NHTSA'))]
    tiles = ''.join(f'<div class="yt"><span class="yt-l">{l}</span><b class="yt-v">{val}</b><small>{sub}</small></div>' for l, val, sub in facts if l != 'Recalls')
    yrs = ''.join(f'<a class="ychip {c}" href="{CARU(f, w["y"])}"><small>{lab}</small><b>{w["y"]}</b></a>' for lab, w, c in (('best year', best, 'good'), ('worst year', worst, 'bad')) if w['y'] != y)
    nav = ''.join(f'<a class="ychip" href="{CARU(f, w["y"])}"><small>{lab}</small><b>{w["y"]}</b></a>' for lab, w in (('previous', prev), ('next', nxt)) if w)
    ph = year_photo(f, y)   # 11-03 v6: nearest-year or model photo, captioned with the year it shows
    # 11-03 v3 header: a year switcher (‹ 2007 · 2008 · 2009 ›) and the best / worst years as one quiet line under the verdict
    seg = (f'<a href="{CARU(f, prev["y"])}" aria-label="{prev["y"]}">‹ {prev["y"]}</a>' if prev else '') + f'<span aria-current="page">{y}</span>' + (f'<a href="{CARU(f, nxt["y"])}" aria-label="{nxt["y"]}">{nxt["y"]} ›</a>' if nxt else '')
    bw = (lambda xs: f'<p class="ybw">{" · ".join(xs)}</p>' if xs else '')([f'{lab} <a class="{c}" href="{CARU(f, w["y"])}">{w["y"]}</a>' for lab, w, c in (('Best year', best, 'good'), ('Worst year', worst, 'bad')) if w['y'] != y])
    parts = ''.join(f'<div class="pt"><span>{E(NICE(p))}</span><span class="bt"><i style="width:{k}%"></i></span><b>{k}%</b></div>' for p, k in v['parts'])
    probs = f'<section class="yc" id="problems"><h2>What owners complain about most. <span class="h2s">From owner complaints to the government.</span></h2><div class="pts">{parts}</div><p class="yc-cap">Share of this year&#39;s owner complaints filed with NHTSA, not the share of cars that break. One complaint can name more than one area.</p>' + (f'<p class="yc-cap"><a href="{CARU(f)}transmission/">Transmission problems in every {nm} year →</a></p>' if f['id'] in TR else '') + '</section>' if parts else ''
    sev_items = [(s.get('crash', 0), 'crashes'), (s.get('injured', 0), 'injuries'), (s.get('fire', 0), 'fires'), (s.get('towed', 0), 'tows')]
    sev = (f'<section class="ysev"><h2>How serious. <span class="h2s">Out of {s["total"]:,} owner complaints, owners reported:</span></h2><div class="sv">'
           + ''.join(f'<div class="{"bad" if n else "good"}">{icon(ic)}<b>{n:,}</b><span>{lab}</span></div>' for (n, lab), ic in zip(sev_items, ('crash', 'injury', 'fire', 'tow'))) + '</div></section>') if s.get('total') else ''
    if 'recalls' in x:
        rs = sorted(rec, key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2], reverse=True)
        card = lambda r: f'<li><b>{E(RPART(r["part"]))}</b> <small>{E(r["date"][-4:])}</small><p>{E(rsum(r))}</p></li>'
        recs = (f'<section class="yc" id="recalls"><h2>Recalls <span class="yc-n">{len(rs)}</span></h2>'
                + (f'<ul class="rc">{"".join(card(r) for r in rs[:3])}</ul>' + (f'<details><summary>Show all {len(rs)} recalls</summary><ul class="rc">{"".join(card(r) for r in rs[3:])}</ul></details>' if len(rs) > 3 else '')
                   if rs else '<p>No safety recalls on record.</p>')
                + '<p class="yc-cap">Recall repairs are free at any dealer. A recall only matters if it&#39;s still open on that exact car, so check its VIN.</p>'
                + '<p><a class="btn" href="/vin/">Check a VIN for open recalls</a></p></section>')
    else: recs = ''
    crash = ''
    if sf and sf.get('variants'):
        rows = ''.join(f'<tr><td>{E(re.sub(r"^\d{4} ", "", vv["desc"]))}</td><td>{stars(vv["overall"])}</td><td>{stars(vv["front"])}</td><td>{stars(vv["side"])}</td><td>{stars(vv["rollover"])}</td></tr>' for vv in sf['variants'])
        crash = f'<details class="yd"><summary>Crash test details</summary><div class="tw"><table><thead><tr><th>Version</th><th>Overall</th><th>Front</th><th>Side</th><th>Rollover</th></tr></thead><tbody>{rows}</tbody></table></div></details>'
    fuel = (f'<details class="yd"><summary>Fuel cost and engines</summary><p>About <b>${rng(m["cost"])}</b> a year in {"electricity" if m.get("ev") else "fuel"} (EPA estimate).'
            + (f' Engines: {E(", ".join(m["engines"]))}.' if m.get('engines') and not m.get('ev') else '') + '</p></details>') if m and m.get('cost') else ''
    fixes = ''
    tl = [c for c in (clean_tsb(z) for z in (x2.get('tsb') or {}).get('top', [])) if c]
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
    if best['y'] != y: kc.append(('up', 'Better year to buy', f'{best["y"]}', E(plain(best['li'])), CARU(f, best['y'])))
    else: kc.append(('up', 'Best year', f'{y}', f'The best {nm} year we track', CARU(f)))
    if inv_open: kc.append(('warn', 'Government investigation', f'{len(inv_open)} open', 'Owners reported enough to trigger one', '#inv'))
    elif x2.get('tsb'): kc.append(('doc', f'Repair notes from {mkr}', f'{x2["tsb"]["n"]}', 'Ask a seller if they were done', '#fixes'))
    buy = (f'<section class="ybuy"><h2>Before you buy. <span class="h2s">What matters most for this car.</span></h2><div class="ybuy-g">'
           + ''.join(f'<a class="yk" href="{h}">{icon(ic)}<span class="yk-l">{lab}</span><b>{val}</b><small>{sub}</small></a>' for ic, lab, val, sub, h in kc) + '</div></section>')
    words = ''
    if qs_list:
        q0 = qs_list[0]; more = ''.join(f'<blockquote><p>{E(q["text"])}</p><cite>NHTSA complaint {q["odi"]}</cite></blockquote>' for q in qs_list[1:])
        words = (f'<section class="yc"><h2>In owners&#39; words</h2><blockquote><p>{E(q0["text"])}</p><cite>{y} {nm} owner · NHTSA complaint {q0["odi"]}</cite></blockquote>'
                 + (f'<details><summary>More owner reports</summary>{more}</details>' if more else '') + '</section>')
    return f'''
<article class="yp yp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/cars/">All cars</a> · <a href="{CARU(f)}">{nm}</a></p><h1>{y} {nm}.</h1>{answer_box(f, v, y, x, best)}{'<p class="early-b">Early read</p>' if v.get('early') else ''}
{f'<p class="yc-note">{SN[f["id"]][1]}</p>' if f["id"] in SN else ""}{hero.replace('{BW}', bw)}
<nav class="modes" aria-label="Page mode"><a href="{CARU(f, y)}" aria-current="page">Normal</a><a href="{CARU(f, y)}advanced/">Advanced</a></nav><nav class="yswitch" aria-label="Model years"><div class="yseg">{seg}<a class="yall" href="{CARU(f)}">All years</a></div><div class="yact"><a class="btn btn-ghost" href="/compare/?c={f['id']}-{y}">Compare</a><button type="button" class="btn btn-ghost yshare" data-share="{E(share_txt)}">Share</button></div></nav></div>{f'<div class="ph-v">{ph}</div>' if ph else ''}</section>
{buy}<div class="yts">{tiles}</div>{ytfix(f["id"], y)}{sev}{old}
<section class="yyears noph"><div class="yy-ch"><h2>Every {nm} year. <span class="h2s">{y} is highlighted. Lower is better.</span></h2>{ybars(f, y)}</div></section>
<div class="ygrid">{probs}{timeline(x["miles"], x.get("comps") or []) if x.get("miles") else ""}{recs}{(lambda pr: f'<section class="yc">{pr}</section>' if pr else '')(price_html(f["id"], y, f["name"]))}
{fixes}{invs}{safety}{f'<section class="yc">{crash}{fuel}</section>' if crash or fuel else ''}{words}
{f'<section class="yc yqa"><h2>Quick answers</h2>' + qa_fold("".join(f"<h3>{E(q)}</h3><p>{a}</p>" for q, a, _ in qa)) + '</section>' if qa else ''}</div>
<p class="yc-cap">Lemon Index = safety complaints filed with the U.S. government (NHTSA) in a car&#39;s first 3 years, per car sold, against the average car of the same model year. 100 is average; lower is better. A complaint is an owner&#39;s report, not a confirmed defect. <a href="/method/">How it works</a></p>{share_line(share_txt)}</article>'''

def yearx(fid, y): return extra(fid, y)
for f in YEARS:
    c = BYNAME[f['name']]; ys = f['years']; sc = [v for v in ys if v['ok'] and not v.get('early')]; best, worst = min(sc, key=lambda v: v['li']), max(sc, key=lambda v: v['li'])
    good3 = sorted(sc, key=lambda v: v['li'])[:3]; bad3 = [v for v in sorted(sc, key=lambda v: -v['li']) if v['li'] > 110][:3]
    def why(v):
        xx = yearx(f['id'], v['y']); bits = [plain(v['li'])]
        if v['parts']: bits.append(f'top problem: {v["parts"][0][0]}')
        if 'recalls' in xx: bits.append(f'{len(xx["recalls"])} recalls')
        return E(', '.join(bits))
    buy = ''.join(f'<li><a href="{CARU(f, v["y"])}"><b>{v["y"]}</b></a>: {why(v)}</li>' for v in good3)
    avoid = ''.join(f'<li><a href="{CARU(f, v["y"])}"><b>{v["y"]}</b></a>: {why(v)}</li>' for v in bad3)
    chip = lambda v, cl: f'<a class="ych {cl}" href="{CARU(f, v["y"])}"><b>{v["y"]}</b><span>{v["li"]}</span><small>{E(plain(v["li"]))}</small></a>'
    picks = (f'<section class="bw2"><div class="bwt good"><p class="te">Best years to buy</p><h2>{good3[0]["y"]}.</h2><div class="ychs">{"".join(chip(v, "good") for v in good3)}</div></div>'
             + (f'<div class="bwt bad"><p class="te">Years to avoid</p><h2>{bad3[0]["y"]}.</h2><div class="ychs">{"".join(chip(v, "bad") for v in bad3)}</div></div>' if bad3 else
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
    good_word = ('Yes, it is one of the most reliable models we track' if li < 50 else 'Yes, it draws fewer complaints than the average car' if li < 85 else 'It is about average' if li <= 115 else 'Not overall: it draws more complaints than the average car')
    mqa = [(f'Is the {snm} a good car?', f'{good_word}, by owner complaints to the government per car sold ({c["years"]}: Lemon Index {li}; 100 is average). Some years are much better than others: the best is {best["y"]} and the worst is {worst["y"]}.'),
           (f'What are the best {snm} years to buy?', f'By owner complaints per car sold: ' + ', '.join(str(v["y"]) for v in good3) + '.'),
           (f'What {snm} years should you stay away from?', (f'The years with the most complaints per car sold: ' + ', '.join(str(v["y"]) for v in bad3) + '.') if bad3 else f'No {snm} year drew much more than an average car&#39;s complaints.')]
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
    rel_html, rel_tiles, rel_plain = rel_top(f, c, snm, ys, sc, best, worst, bad3)
    mqa.insert(0, (f'Is the {snm} reliable?', E(rel_plain)))
    model_qa_html = '<section class="yqa"><h2>Quick answers.</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{a}</p>' for q, a in mqa)) + '</section>'
    _tt = next(t for t in (f'{snm} Reliability: Years to Avoid & Best Years', f'{snm} Reliability & Years to Avoid', f'{snm} Reliability by Year') if len(t) <= 65 or t.endswith('by Year'))
    page(CARU(f), _tt,
         f'Is the {snm} reliable? {rel_plain.split(". ")[0].rstrip(".")}. Every year {ys[0]["y"]}–{ys[-1]["y"]} ranked by owner complaints' + (' and YouTube owner reviews' if f['id'] in YTR else '') + f'. Best: {best["y"]}. Worst: {worst["y"]}.', f'''
<div class="pg mp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/cars/">All cars</a> · <a href="/brands/{c["brand"].lower().replace(" ", "-")}/">{E(c["brand"])}</a> · {E(c["segName"])}</p>{rel_html}{f'<p class="yc-note">{SN[f["id"]][1]}</p>' if f["id"] in SN else ""}
<div class="yhero">{gauge(c["li"], 190)}<div class="yverd {verdict(c["li"])[0]}"><p><b>{verdict(c["li"])[1]}.</b> <span>Whole model, {c["years"]}{"" if plain(c["li"]).lower() in verdict(c["li"])[1].lower() else ": " + E(plain(c["li"]))}.</span></p><p class="ybw">Best year <a class="good" href="{CARU(f, best["y"])}">{best["y"]}</a> · Worst year <a class="bad" href="{CARU(f, worst["y"])}">{worst["y"]}</a></p></div></div>
<p><button type="button" class="btn btn-ghost" data-share="{E(f'Every {snm} year ranked by owner complaints. Best: {best["y"]}. Worst: {worst["y"]}. Free report:')}">Share ↗</button></p></div><div class="ph-v">{year_photo(f, ys[-1]["y"])}{rel_tiles}</div></section>
<section class="yyears noph" id="years"><div class="yy-ch"><h2>Every year. <span class="h2s">Lower is better. Tap a year for its full report.</span></h2>{ybars(f)}</div>{'<p class="yc-cap">Scores before 2010 are rough: fewer owners filed complaints back then.</p>' if ys[0]["y"] < 2010 else ''}{yt_note(f)}</section>
{ytfix("model:" + f["id"])}{picks}
{f'<section><h2>Compare the {E(f["name"])}.</h2><div class="mus">{vcards}</div>' + (f'<p class="yc-cap">{vs}</p>' if vs else '') + '</section>' if vcards or vs else ''}
{model_qa_html}
<section><details class="yd"><summary>Every year in one table</summary><div class="tw"><table><thead><tr><th>Year</th><th>Index</th><th>Compared with average</th><th>Complaints</th><th>Top complaint</th><th>Recalls</th><th>Crash test</th><th>MPG</th></tr></thead><tbody>{rows}</tbody></table></div></details>
<p class="yc-cap">Lemon Index = safety complaints filed with the government within 3 years, per car sold, against the average car of the same model year. 100 is average, lower is better. <a href="/method/">How it works</a></p>{f'<p><a class="btn" href="{CARU(f)}transmission/">{E(snm)} transmission problems by year →</a></p>' if f["id"] in TR else ''}</section>{share_line(f'Every {snm} year ranked by owner complaints. Best: {best["y"]}. Worst: {worst["y"]}. Free report:')}</div>''',
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{snm} reliability by year', "url": BASE + CARU(f)},
             faq_ld([(q, '', html.unescape(a)) for q, a in mqa]), car_ld(f, img=(mphoto(f['id']) or {}).get('src'))])
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
        page(CARU(f, y), f'{y} {snm} Problems, Reliability and Recalls' + (' (Early Read)' if v.get('early') else '') + ' | The Lemon Index',
             (f'Early read: so far the {y} {snm} has drawn {plain(v["li"])} per car sold (NHTSA).' if v['ok'] and v.get('early') else f'The {y} {snm} drew {plain(v["li"])} per car sold (NHTSA).' if v['ok'] else f'Owners filed only {v["n"]} NHTSA complaints about the {y} {snm} in its first 3 years.')
             + (f' {nrec} recall{"s" if nrec != 1 else ""}.' if nrec else '') + (f' Top problems: {top}.' if top else '') + ' Real owner complaints and every other year.', year_body(f, v, y, x, best, worst, prev, nxt, v['quotes'], qa), kind='article', ask=(f['id'], y, f'{y} {snm}'), img=(PH.get(f['id'], {}).get(str(y)) or {}).get('src'),
             ld=[car_ld(f, y, x.get('mpg'), (PH.get(f['id'], {}).get(str(y)) or {}).get('src')), {"@context": "https://schema.org", "@type": "WebPage", "name": f'{y} {snm} problems, reliability and recalls', "url": BASE + CARU(f, y)}
                 | ({"primaryImageOfPage": {"@type": "ImageObject", "contentUrl": BASE + PH[f['id']][str(y)]['src'], "license": LIC.get(PH[f['id']][str(y)]['license'], PH[f['id']][str(y)]['page']), "acquireLicensePage": PH[f['id']][str(y)]['page'], "creditText": PH[f['id']][str(y)]['author'].split('\ufffd')[0].strip()}} if str(y) in PH.get(f['id'], {}) else {})] + ([faq_ld(qa)] if qa else []))
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
    def rtxt(d): return ('%g per 100K sold' % d['rate']) if d and d.get('rate') is not None else 'no sales data'
    def bad(d): return 'bad' if d and d.get('rate') and d['rate'] > avg * 2 and d['n'] >= 20 else ''
    def wid(d): return (d['rate'] / mx * 100) if d and d.get('rate') else 0
    bars = ''.join(f'<a class="b {bad(d)}" href="{CARU(f, y)}"><span class="bn">{y}</span><span class="bt"><i style="width:{wid(d):.1f}%"></i></span><b>{(d or {}).get("n", 0):,}</b><small>{rtxt(d)}</small></a>' for y, d in rows)
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
    quotes = ''.join(f'<blockquote><p>{E(sent_case(q))}</p><cite>{wq[0]} {nm} owner · NHTSA complaint</cite></blockquote>' for q in qs)
    wtxt = ', '.join(f'{y} ({d["n"]:,} complaints)' for y, d in worst)
    qa = [(f'Which {SNM(f)} years have transmission problems?', '', f'By transmission complaints filed with NHTSA per car sold, the worst {SNM(f)} years are {", ".join(str(y) for y, _ in worst)}.'),
          (f'What are common {SNM(f)} transmission problems?', '', 'Owners most often describe ' + ', '.join(k.lower() for k, _ in sorted(tot.items(), key=lambda kv: -kv[1])[:3]) + '.' if tot else 'Owners describe a range of shifting problems.')]
    if best: qa.append((f'Which {SNM(f)} years have the fewest transmission complaints?', '', f'Since 2010, the {SNM(f)} years with the fewest transmission complaints per car sold are {", ".join(str(y) for y, _ in best)}.'))
    body = f'''
<article class="study"><p class="kicker"><a href="/cars/">All cars</a> · <a href="{CARU(f)}">{nm}</a> · Transmission</p><h1>{nm} transmission problems by year</h1>
<p class="lede">Worst years for transmission complaints per car sold: <b>{wtxt}</b>.{f" Fewest since 2010: <b>{', '.join(str(y) for y, _ in best)}</b>." if best else ""}</p>
<p><button type="button" class="btn btn-ghost" data-share="{E(f'{SNM(f)} transmission problems by year. Worst: {", ".join(str(y) for y, _ in worst)}. Free report:')}">Share ↗</button></p>
<p class="sub">Transmission complaints owners filed with the U.S. government (NHTSA) for each model year, per 100,000 cars sold. A complaint counts when it&#39;s filed under the transmission, or under the power train and the owner describes the transmission (shifting, slipping, gears, CVT). It&#39;s an owner&#39;s report, not a confirmed defect, and older years have had longer to collect complaints.</p>
<div class="bars yb">{bars}</div>
{f'<h2>What owners describe</h2><div class="pts">{sym}</div><p class="note">Share of this model&#39;s transmission complaints that mention each symptom. One complaint can mention several.</p>' if sym else ''}
{f'<h2>Transmission and power train recalls</h2><ul class="rc">{rl}</ul><p class="note">Recall repairs are free at any dealer. Check a specific car&#39;s VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener">nhtsa.gov/recalls</a>.</p>' if rl else ''}
{f'<h2>In owners&#39; words</h2>{quotes}' if quotes else ''}
<section class="yqa"><h2>Quick answers</h2>{''.join(f'<h3>{E(q)}</h3><p>{E(t)}</p>' for q, _, t in qa)}</section>
<p class="note">See every problem, not just the transmission: <a href="{CARU(f)}">{nm} reliability by year</a>. <a href="/method/">How we count</a></p></article>'''
    return body, qa
turls = []
for f in YEARS:
    body, qa = trans_body(f)
    if not body: continue
    snm = SNM(f); wy = sorted(((v['y'], TR[f['id']][str(v['y'])]['rate']) for v in f['years'] if str(v['y']) in TR.get(f['id'], {}) and TR[f['id']][str(v['y'])].get('rate') is not None), key=lambda t: -t[1])[:2]
    page(CARU(f) + 'transmission/', f'{snm} Transmission Problems by Year | The Lemon Index',
         f'Which {snm} years have the most transmission complaints per car sold, what owners describe, and every transmission recall. Worst years: {", ".join(str(y) for y, _ in wy)}. From NHTSA owner complaints.',
         body, kind='article', ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{snm} transmission problems by year', "url": BASE + CARU(f) + 'transmission/'}, faq_ld(qa)], vis=year_photo(f, f['years'][-1]['y']))
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
def csv_write(path, head, rows):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        fh.write('# The Lemon Index (lemonindex.com). License: CC BY 4.0, free to use with credit: "Source: The Lemon Index (lemonindex.com)". Updated ' + TODAY + '\n')
        w = csv.writer(fh); w.writerow(head); w.writerows(rows)
    return len(rows), os.path.getsize(path)
os.makedirs(f'{OUT}/data', exist_ok=True)
_top = lambda v, k: (v['parts'][k][0], v['parts'][k][1]) if k < len(v.get('parts') or []) else ('', '')
_r1 = [[f['id'], f['name'], v['y'], v['li'], v['n']] + [x for k in range(3) for x in _top(v, k)] + ['yes' if v.get('early') else ''] for f in YEARS for v in f["years"]]
DL1 = csv_write(f'{OUT}/data/lemon-index-by-year.csv', ['family_id', 'model', 'model_year', 'lemon_index', 'nhtsa_complaints', 'top_problem_1', 'top_problem_1_complaints',
                'top_problem_2', 'top_problem_2_complaints', 'top_problem_3', 'top_problem_3_complaints', 'early_read'], _r1)
_names = {f["id"]: f["name"] for f in YEARS}
_r2 = [[fid, _names.get(fid, fid), int(y), d['n'], d['all'], d['rate']] for fid, ys in TR.items() for y, d in sorted(ys.items())]
DL2 = csv_write(f'{OUT}/data/transmission-complaints-by-year.csv', ['family_id', 'model', 'model_year', 'transmission_complaints', 'all_complaints', 'transmission_complaints_per_100k_sold'], _r2)
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
<a class="dl" href="/data/transmission-complaints-by-year.csv" download><b>Transmission complaints by model year</b><span>{DL2[0]:,} model years · CSV · {_kb(DL2[1])}</span></a></div>
<p class="note">Updated {TODAY}. Line 1 of each file is the credit line, starting with #. In a spreadsheet just delete that row; in code, skip comment lines (pandas: <code>comment=&#39;#&#39;</code>).</p>
<details class="yd"><summary>What&#39;s in the files</summary><h3>Lemon Index by model year</h3>{_tbl(_cols1)}<h3>Transmission complaints by model year</h3>{_tbl(_cols2)}</details>
<h2>Where the numbers come from</h2><p>Owner complaints come from NHTSA, the U.S. government&#39;s vehicle safety agency, which publishes them for free. The score and the transmission matching are ours. <a href="/method/">See exactly how the index works</a>.</p>
<p class="note">Not included: car prices, sales figures and complaint text (other sources own those). Please don&#39;t present the data as an official rating, and don&#39;t suggest we endorse you. Using it somewhere big, or want a custom cut? <a href="/contact/">Tell us</a>. We&#39;d love to see it.</p>
</article></div><script src="/assets/data.js?v=1103" defer></script>""",
     ld=[_ds('Lemon Index car reliability by model year', 'Owner complaints per car sold for each model year (100 = the average car), plus each year&#39;s top problem areas, from NHTSA owner complaints.'.replace('&#39;', "'"), '/data/lemon-index-by-year.csv', _cols1),
         _ds('Transmission complaints by car model year', 'Transmission-related NHTSA owner complaints for each model year, as a count and per 100,000 cars sold.', '/data/transmission-complaints-by-year.csv', _cols2)])

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
def mcard(n, i):
    li = BYNAME[n]['li']; ph = mphoto(i)
    return f'<a class="mc" href="/cars/{i}/"><span class="mc-p">{pimg(ph, n) if ph else ""}</span><b>{E(n.split(" ", 1)[1] if " " in n else n)}</b><span class="{"good" if li < 100 else "bad"}">{li}</span></a>'
lst = ''.join(f'<div class="mb"><h3>{E(b)}</h3><div class="mg">' + ''.join(mcard(n, i) for n, i, _ in m) + '</div></div>' for b, m in pick.items())
page('/cars/', 'Look Up Your Car: Problems by Model and Year | The Lemon Index', f'Pick your car and model year to see its owner complaints, its top problems and how it compares with every other year. {len(YEARS)} models, 2000-2025.', f'''
<div class="pg"><div class="ph ph-f">{finder('<span class="ph-e">Look up</span>Look up your car.', 'Every model year, 2000 to 2025. Free.')}</div>
<section><h2>Every model. <span class="h2s">Score in the corner: 100 is average, lower is better.</span></h2><div class="mbs">{lst}</div></section>
<p class="ph-cr">Photos: Wikimedia Commons contributors (CC BY-SA and similar). Credits on each car&#39;s page.</p></div>''',
     ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": "Look up your car", "url": BASE + '/cars/'}])
yurls.insert(0, '/cars/')

curls = []
for a, b in PAIRS:
    A, B = FY[a], FY[b]; ca, cb = BYNAME[A['name']], BYNAME[B['name']]
    ya, yb = {v['y']: v for v in A['years'] if v['ok']}, {v['y']: v for v in B['years'] if v['ok']}
    shared = sorted(set(ya) & set(yb))
    if len(shared) < 2: continue
    wa = sum(ya[y]['li'] < yb[y]['li'] for y in shared); wb = sum(yb[y]['li'] < ya[y]['li'] for y in shared)
    lead, trail = (A, B) if ca['li'] <= cb['li'] else (B, A)
    rows = ''.join(f'<tr><td>{y}</td><td class="num {CLS(ya[y])}"><a href="{CARU(A, y)}">{ya[y]["li"]}</a></td><td class="num {CLS(yb[y])}"><a href="{CARU(B, y)}">{yb[y]["li"]}</a></td><td>{E(A["name"] if ya[y]["li"] < yb[y]["li"] else B["name"] if yb[y]["li"] < ya[y]["li"] else "tie")}</td></tr>' for y in shared)
    def facts(F):
        last = max(v['y'] for v in F['years']); xx = extra(F['id'], last); m, sf = xx.get('mpg'), xx.get('safety')
        rec = sum(len(extra(F['id'], v['y']).get('recalls', [])) for v in F['years'] if v['y'] in shared)
        return rec, (f'{m["comb"][0]}–{m["comb"][1]}' if m and m['comb'][0] != m['comb'][1] else (m['comb'][0] if m else '—')), (stars(sf['best']) if sf and sf.get('best') else '—'), last
    fa, fb = facts(A), facts(B)
    title = f'{A["name"]} vs {B["name"]} Reliability: Which Has Fewer Problems?'
    sh_txt = f'{A["name"]} vs {B["name"]}: which has fewer problems? Free comparison from owner complaints:'
    # 11-02 (Elijah): one clear winner up top, a 2-column scorecard that stays side by side on phones, and bars instead of a wide table
    close = abs(ca['li'] - cb['li']) <= max(ca['li'], cb['li']) * .08
    lc_, tc_ = (ca, cb) if lead is A else (cb, ca); fewer = round((1 - lc_['li'] / max(tc_['li'], 1)) * 100)
    lw, tw_ = (wa, wb) if lead is A else (wb, wa)
    if close: verdict = f'<p class="vk">Verdict</p><p class="vw">Too close to call</p><p class="vs">Overall they drew about the same complaints per car sold ({ca["li"]} vs {cb["li"]}). Pick by model year below.</p>'
    else: verdict = f'<p class="vk">Winner</p><p class="vw">{E(lead["name"])}</p><p class="vs">About <b>{fewer}% fewer</b> owner complaints per car sold than the {E(trail["name"])}, and fewer in <b>{lw} of {len(shared)}</b> model years both were sold.</p>'
    num = lambda x: float(re.match(r'[\d.]+', str(x)).group()) if re.match(r'[\d.]+', str(x)) else None
    def better(x, y, high):
        if x is None or y is None or x == y: return '', ''
        return ('w', '') if (x > y) == high else ('', 'w')
    def srow(lab, va, vb, cls):
        return f'<div class="dl">{lab}</div><div class="dv {cls[0]}">{va}</div><div class="dv {cls[1]}">{vb}</div>'
    stA = num(re.sub(r'<[^>]+>', '', fa[2]).count('★')) if '★' in fa[2] else None; stB = num(re.sub(r'<[^>]+>', '', fb[2]).count('★')) if '★' in fb[2] else None
    bA, bB = min((ya[y] for y in ya), key=lambda v: v['li']), min((yb[y] for y in yb), key=lambda v: v['li'])
    duel = f'<div class="duel"><div></div><div class="dh"><a href="{CARU(A)}">{E(A["name"])}</a></div><div class="dh"><a href="{CARU(B)}">{E(B["name"])}</a></div>' + \
        srow('Lemon Index<br><small>100 = average, lower is better</small>', f'<b>{ca["li"]}</b>', f'<b>{cb["li"]}</b>', better(ca['li'], cb['li'], False)) + \
        srow(f'Years with fewer complaints<br><small>{shared[0]}–{shared[-1]}</small>', f'{wa} of {len(shared)}', f'{wb} of {len(shared)}', better(wa, wb, True)) + \
        srow(f'Recalls<br><small>{shared[0]}–{shared[-1]}</small>', fa[0], fb[0], better(fa[0], fb[0], False)) + \
        srow('MPG<br><small>latest year</small>', fa[1], fb[1], better(num(fa[1]), num(fb[1]), True)) + \
        srow('Crash test<br><small>best, latest year</small>', fa[2], fb[2], better(stA, stB, True)) + \
        srow('Best year to buy', f'<a href="{CARU(A, bA["y"])}">{bA["y"]}</a>', f'<a href="{CARU(B, bB["y"])}">{bB["y"]}</a>', ('', '')) + '</div>'
    mx = max(max(ya[y]['li'], yb[y]['li']) for y in shared)
    yrs = ''.join(f'''<div class="yr"><div class="yy">{y}</div><div class="yb">
<a class="ybar {CLS(ya[y])}{' w' if ya[y]['li'] < yb[y]['li'] else ''}" href="{CARU(A, y)}"><i style="width:{ya[y]['li'] / mx * 100:.0f}%"></i><span>{E(A["name"])} <b>{ya[y]['li']}</b></span></a>
<a class="ybar {CLS(yb[y])}{' w' if yb[y]['li'] < ya[y]['li'] else ''}" href="{CARU(B, y)}"><i style="width:{yb[y]['li'] / mx * 100:.0f}%"></i><span>{E(B["name"])} <b>{yb[y]['li']}</b></span></a></div></div>''' for y in shared)
    page(CMPU(a, b), title + ' | The Lemon Index',
         f'{lead["name"]} vs {trail["name"]}: owner complaints per car sold for every model year both were sold ({shared[0]}-{shared[-1]}), plus recalls, crash tests and fuel economy.', f'''
<article class="study cmpp"><p class="kicker"><a href="/cars/">All cars</a> · Compare</p><h1>{E(A["name"])} vs {E(B["name"])}: which has fewer problems?</h1>
<div class="verdict{' tie' if close else ''}">{verdict}</div><p class="cmp-sh">{share_btn(sh_txt)}</p>
<h2>Head to head</h2>{duel}
<p class="sub">Lemon Index = safety complaints filed with the government within 3 years, per car sold, against the average car of the same model year. <b>100 is average, lower is better.</b> Green check = the better of the two on that line.</p>
<h2>Year by year</h2><p class="sub">Shorter bar = fewer complaints per car sold. Tap a year for its full report.</p><div class="yrs">{yrs}</div>
<p class="note"><a href="{CARU(A)}">Every {E(A["name"])} year</a> · <a href="{CARU(B)}">Every {E(B["name"])} year</a> · <a href="/method/">How the index works</a></p>{share_line(sh_txt, 'Know someone choosing between these two?')}</article>''', kind='article',
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": BASE + CMPU(a, b)}], vis=pair(mphoto(a), mphoto(b), (A['name'], B['name'])) + pcredit(who(mphoto(a), mphoto(b))))
    curls.append(CMPU(a, b))
_cp = list(zip([p for p in PAIRS if CMPU(*p) in curls], curls))
cl = ''.join(f'<li><a href="{u}">{E(FY[a]["name"])} vs {E(FY[b]["name"])}</a></li>' for (a, b), u in _cp)
_top, _seen = [], set()   # 8 match-ups, no car twice, so it isn't all Camry
for (a, b), u in _cp:
    if mphoto(a) and mphoto(b) and a not in _seen and b not in _seen and len(_top) < 8: _top.append((a, b, u)); _seen |= {a, b}
mcards = ''.join(f'<a class="mu" href="{u}"><span class="mu-p">{pimg(mphoto(a), FY[a]["name"], "l")}{pimg(mphoto(b), FY[b]["name"], "r")}</span><b>{E(FY[a]["name"])} <i>vs</i> {E(FY[b]["name"])}</b></a>' for a, b, u in _top)
page('/compare/', 'Car Reliability Comparisons: Model vs Model | The Lemon Index', f'{len(curls)} head-to-head reliability comparisons of popular rivals, year by year, from NHTSA owner complaints per car sold.', f'''
<div class="pg">{phero('Compare', 'Any two cars.', 'Problems, recalls, mpg and crash tests, side by side.', visual=pair(mphoto('toyota-rav4', 2019), mphoto('honda-cr-v', 2017), ('Toyota RAV4', 'Honda CR-V')), extra='<div id="cmpx" class="cmpx"><p class="note">Loading…</p></div>')}
<section><h2>Popular match-ups.</h2><div class="mus">{mcards}</div>
<details class="yd"><summary>All {len(curls)} match-ups</summary><ul class="cmp">{cl}</ul></details></section>
{pcredit(who(*[mphoto(x) for a, b, _ in _top for x in (a, b)], mphoto('toyota-rav4', 2019), mphoto('honda-cr-v', 2017)))}
{share_line("Compare any two cars side by side: problems, recalls, mpg and crash tests. Free:", 'Know someone stuck between two cars?')}</div><script src="/assets/compare.js?v=1102" defer></script>''',
     ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Car reliability comparisons", "url": BASE + '/compare/'}])
curls.insert(0, '/compare/')

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
<h2>Sharing</h2><p>We don&#39;t sell your personal information. We share it only with the services that run the site (hosting, sign-in, email, Stripe) and when the law requires it.</p>
<h2>Your choices</h2><p>Email <a href="mailto:{CONTACT}">{CONTACT}</a> to get a copy of your data or to have it deleted.</p>
<p>{LEGAL_NAME}, {ADDRESS}.</p>''', 'Privacy Policy: What We Collect and Why | Lemon Index',
      'What lemonindex.com collects: visit counts from Cloudflare and Google Analytics, Google AdSense ad cookies, and your email only if you give it to us. Donations run through Stripe.')
legal('/terms/', 'Terms of use', f'''<p>lemonindex.com is operated by {LEGAL_NAME}, {ADDRESS}. By using the site you agree to these terms.</p>
<h2>The data</h2><p>Our scores, recalls, crash tests and fuel-economy figures come from public U.S. government data (NHTSA and the EPA) and published sales figures. Owner complaints are owners&#39; own reports, not confirmed defects. The site is for general information. It isn&#39;t a mechanical inspection, a repair-cost estimate or a guarantee about any car. Have a car inspected before you buy it.</p>
<h2>Donations</h2><p>Every report is free. Donations are voluntary, processed by Stripe, and don&#39;t unlock anything. See the <a href="/refunds/">refund policy</a>.</p>
<h2>Using our work</h2><p>You may cite our rankings with a link to lemonindex.com (CC BY 4.0). Don&#39;t copy the site wholesale or resell it.</p>
<h2>Limits</h2><p>The site is provided as is. To the extent the law allows, {LEGAL_NAME} isn&#39;t liable for decisions made using it. Arizona law governs these terms.</p>
<p>Questions: <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>''', 'Terms of Use: How You Can Use Lemon Index Data',
      'The terms for using lemonindex.com: where our car reliability data comes from, what it is and isn&#39;t, citing our rankings, and donations.'.replace('&#39;', "'"))
LEGAL_URLS = ['/contact/', '/refunds/', '/privacy/', '/terms/']

# 10-31: electric cars (ranking, fires, cost, problems, driver-assist crashes, one page per EV)
exec(open('electric_pages.py', encoding='utf-8').read())
exec(open('brands_pages.py', encoding='utf-8').read())   # 11-03 brand pages
exec(open('vehicles_pages.py', encoding='utf-8').read())   # 11-04 planes + motorcycles
exec(open('advanced_pages.py', encoding='utf-8').read())   # 11-06 advanced mode
exec(open('gap_pages.py', encoding='utf-8').read())   # 11-06 keyword gaps
exec(open('seo_pages.py', encoding='utf-8').read())   # 11-06 best-of + stats pages
exec(open('extra_pages.py', encoding='utf-8').read())   # 11-06 Taos + Pontiac
exec(open('thanks_page.py', encoding='utf-8').read())   # 11-07 donation thank-you page (noindex)
json.dump(PD, open('data/page_dates.json', 'w', encoding='utf-8'), separators=(',', ':'))

open(f'{OUT}/404.html', 'w', encoding='utf-8').write(open(f'{OUT}/index.html', encoding='utf-8').read().replace('<main>', '<main><div class="pg"><section class="ph"><p class="ph-e">404</p><h1>That page drove off.</h1><p class="ph-s">It may have moved. Try one of these.</p><p class="ph-404"><a class="btn" href="/cars/">Look up a car</a> <a class="btn btn-ghost" href="/brands/">Every brand</a> <a class="btn btn-ghost" href="/">Home</a></p></section></div><!--', 1).replace('</main>', '--></main>', 1))
urls = ['/', STUDY, '/studies/', '/method/', '/vin/', '/car-loan-rates/', '/vote/', '/data/', '/brands/'] + burls + purls + murls + surls + eurls + GAP_URLS + SEO_URLS + EXTRA_URLS + yurls + ADV_URLS + curls + LEGAL_URLS
open(f'{OUT}/sitemap.xml', 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{BASE}{u}</loc><lastmod>{TODAY}</lastmod></url>' for u in urls) + '</urlset>')
open(f'{OUT}/ads.txt', 'w').write(f'google.com, {ADS.replace("ca-", "")}, DIRECT, f08c47fec0942fa0\n')
open(f'{OUT}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\n\n# bulk dataset scrapers: the data is free at /data/ with credit instead\nUser-agent: CCBot\nDisallow: /\nUser-agent: Bytespider\nDisallow: /\nUser-agent: Diffbot\nDisallow: /\nUser-agent: Omgilibot\nDisallow: /\nUser-agent: ImagesiftBot\nDisallow: /\n\nSitemap: {BASE}/sitemap.xml\n')
open(f'{OUT}/llms.txt', 'w', encoding='utf-8').write(f'# The Lemon Index\n\n> Car reliability from public data. The Lemon Index = NHTSA safety complaints per 100,000 U.S. sales, vs the average car of the same model years (100 = average).\n\n- [The Most Reliable Cars, According to 1.6 Million Owner Complaints]({BASE}{STUDY}): Toyota 4Runner 26, Lexus ES 27, Lexus brand 30, Tesla brand 322 (est.)\n- [The Most Reliable Electric Cars]({BASE}/electric/): {len(RK)} EVs by NHTSA complaints per car sold, best {best['name']} {best['li']}, plus fires, yearly cost and driver-assist crash reports\n- [Method]({BASE}/method/)\n')
open(f'{OUT}/CNAME', 'w').write('lemonindex.com')
open(f'{OUT}/google00cb28bea71f4c18.html', 'w').write('google-site-verification: google00cb28bea71f4c18.html')   # Search Console ownership (11-02); never remove
open(f'{OUT}/' + open('.indexnow_key').read().strip() + '.txt', 'w').write(open('.indexnow_key').read().strip())   # IndexNow key (Bing/Yandex instant URL pings, 11-02)
VALIAS = {}   # NHTSA make|model (as owners' complaints name it, e.g. FORD|F150) -> family id, for the VIN page
for fid, yrs in XL.items():
    for e in yrs.values():
        for mk, md, n in e.get('names', []): VALIAS.setdefault(re.sub(r'[^A-Z0-9]', '', mk.upper()) + '|' + re.sub(r'[^A-Z0-9]', '', md.upper()), fid)
CJ = {}
for f in YEARS:
    yy = {}
    for v in f['years']:
        xx = extra(f['id'], v['y']); m = xx.get('mpg'); sf = xx.get('safety')
        yy[str(v['y'])] = [v['li'] if v['ok'] else None, v['n'], len(xx['recalls']) if 'recalls' in xx else None, m['comb'][0] if m else None, m['comb'][1] if m else None,
                          sf.get('best') if sf else None, NICE(v['parts'][0][0]) if v['parts'] else None]
    CJ[f['id']] = [f['name'], yy]
json.dump(CJ, open('assets/cars.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
page('/vin/', 'Free VIN Decoder and Recall Check: Look Up Any VIN | The Lemon Index', 'Free VIN decoder and lookup: type a 17-character VIN to see the exact year, engine and factory, then that car\'s recalls and owner complaints. From the U.S. government VIN database.', f'''
<div class="pg"><section class="finder ph ph-f"><h1><span class="ph-e">Free VIN decoder</span>Check any VIN.</h1><p class="lede">Decode it, then see that car&#39;s recalls and problems.</p>
<form id="vinf" class="vinf" autocomplete="off"><input name="vin" maxlength="20" placeholder="e.g. 1FTEW1EG8JKF05094" aria-label="VIN" spellcheck="false"><button class="btn" type="submit">Check</button></form>
<div id="vinout" class="vinout"></div><p class="fnote">It&#39;s on the dashboard by the windshield, the door frame, or your registration. We don&#39;t store it.</p>
<div class="ph-v">{pimg(mphoto('toyota-camry', 2019), 'Toyota Camry')}</div>{pcredit(who(mphoto('toyota-camry', 2019)))}
<script id="pick" type="application/json">{json.dumps(PICK, ensure_ascii=False).replace("</", "<\\/")}</script><script id="valias" type="application/json">{json.dumps(VALIAS, separators=(",", ":"))}</script><script src="/assets/vin.js?v=1106a" defer></script></section></div>''')
shutil.copytree('assets', f'{OUT}/assets', dirs_exist_ok=True); shutil.copy('data/survey.json', f'{OUT}/assets/survey-q.json'); shutil.copy('data/votes.json', f'{OUT}/assets/votes.json')
print('built', len(urls), 'pages into', OUT)
