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
def finder(h='Look up any car', sub='Type your car, or pick it below. Every model year from 2000 to 2022: its score, its top problems and real owner complaints.'):
    """10-29 (Elijah): the first thing on the page is an easy car filter. Type "2016 pilot", or pick brand, model, year (assets/lookup.js)."""
    pick = json.dumps(PICK, ensure_ascii=False).replace('</', '<\\/')
    return f"""<section class="finder" aria-labelledby="fh"><h1 id="fh">{h}</h1><p class="lede">{sub}</p>
<div class="fq"><input id="fq" type="search" placeholder="e.g. 2016 Honda Pilot" autocomplete="off" aria-label="Type a car"><div id="fsug" class="fsug" role="listbox" hidden></div></div>
<form class="look" id="look"><select id="lb" aria-label="Brand"><option value="">Brand</option></select><select id="lm" aria-label="Model" disabled><option value="">Model</option></select><select id="ly" aria-label="Year" disabled><option value="">Year</option></select><button type="button" class="btn" id="lgo" disabled>Show problems</button></form>
<script id="pick" type="application/json">{pick}</script></section>"""
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
    data = json.dumps(CARS, ensure_ascii=False).replace('</', '<\\/')
    seed = ''.join(f'<div class="xr"><div class="xm"><span class="xk">#{c["rank"]}</span><span class="xn"><b>{E(c["name"])}</b><small>{c["segName"]} · {c["years"]}</small></span><span class="xb"><small>{plain(c["li"])}</small></span><span class="xi">{c["li"]}</span></div></div>' for c in CARS[:15])
    tabs = ''.join(f'<button type="button" data-seg="{k}" aria-pressed="{str(k == "all").lower()}">{l}</button>' for k, l in [('all', 'All'), ('car', 'Cars'), ('suv', 'SUVs'), ('truck', 'Trucks'), ('minivan', 'Minivans')])
    return f'''<section class="ex" id="explore" aria-labelledby="ex-h"><div class="exh"><div><h2 id="ex-h">Compare every model</h2>
<p class="sub">All {len(CARS)} models, model years 2010-2022. The Lemon Index compares a car's safety complaints per car sold with the average car: <b>100 is average, lower is better</b>. Hover a bar for what it means, click a car for details, tick two to compare.</p></div></div>
<div class="exbar"><input id="xq" type="search" placeholder="Search a model, e.g. RAV4" aria-label="Search a model"><div class="tabs" role="group" aria-label="Type">{tabs}</div>
<select id="xbrand" aria-label="Brand"></select><select id="xsort" aria-label="Sort"><option value="best">Most reliable first</option><option value="worst">Least reliable first</option><option value="sold">Most sold</option><option value="az">A to Z</option></select><span id="xcount" class="xcount"></span></div>
<div class="xhead" aria-hidden="true"><span>Rank</span><span>Model</span><span>Compared with the average car <i class="avg">│ = average</i></span><span>Index</span><span>Sold</span><span>Top complaint</span><span></span></div>
<div id="xrows" class="xrows">{seed}</div><button type="button" id="xmore" class="btn ghost xmore">Show all</button>
<p class="note">* Tesla doesn't publish U.S. sales by model, so its numbers use published estimates. Sold = U.S. sales over the model years shown.</p>
<div id="tray" class="tray" hidden></div><script id="cars" type="application/json">{data}</script></section>'''

def ask_html(ask):
    """'Help our site' question box (assets/survey.js). ask = (family id, model year, '2018 Honda Odyssey') on car-year pages."""
    fid, y, name = ask or ('', '', '')
    return (f'<section class="ask" id="ask" hidden data-fid="{E(fid)}" data-year="{y or ""}" data-car="{E(name)}"></section>'
            '<script src="/assets/survey.js?v=1103" defer></script><script src="/assets/share.js?v=1103" defer></script>')
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
def page(path, title, desc, body, ld=None, kind='website', img=None, ask=None):
    title, desc = fit_title(title), fit_desc(desc)
    url = BASE + path; lds = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    beacon = f"<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{{\"token\": \"{CF}\"}}'></script>" if CF else ''
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="{kind}"><meta property="og:site_name" content="The Lemon Index"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}{img or "/assets/og.png"}"><meta name="twitter:card" content="summary_large_image">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' https://static.cloudflareinsights.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: https://static.nhtsa.gov; connect-src 'self' https://cloudflareinsights.com https://vpic.nhtsa.dot.gov https://lemon-survey.elift08.workers.dev; object-src 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="msvalidate.01" content="2F84C8106BB577C5860ABE6EC15825EC"><link rel="icon" href="/assets/icon-64.png"><link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap"><link rel="stylesheet" href="/assets/site.css?v=1103b">{lds}</head>
<body><header class="top"><a class="brand" href="/"><img src="/assets/icon-64.png" alt="" width="32" height="32">The Lemon Index</a>
<nav><a href="/cars/">Look up a car</a><a href="/electric/">Electric</a><a href="/studies/">Studies</a><a href="/compare/">Compare</a><a href="/vin/">VIN check</a><a href="/method/">How it works</a><a class="yt" href="{YT}?sub_confirmation=1" rel="noopener">Subscribe</a></nav></header>
<main>{body}{ask_html(ask)}</main>
<footer class="foot"><div class="cta"><div><h2>New car studies, straight from the data.</h2><p>Every study becomes a video. Subscribe to see the next one first.</p></div><a class="btn" href="{YT}?sub_confirmation=1" rel="noopener">Subscribe on YouTube</a></div>
<p class="socs"><a href="{YT}" rel="noopener">YouTube</a> · <a href="{TT}" rel="noopener">TikTok</a> · <a href="{IG}" rel="noopener">Instagram</a> · <a href="/method/">How the index works</a> · <a href="/compare/">Compare cars</a> · <button class="supl" type="button">Support the Lemon Index</button></p>
<p class="fine"><a href="/terms/">Terms</a> · <a href="/privacy/">Privacy</a> · <a href="/refunds/">Refunds</a> · <a href="/contact/">Contact</a><br>© {TODAY[:4]} The Lemon Index. Built from public NHTSA complaint data and published U.S. sales figures. Not affiliated with any automaker. Not a repair-cost or safety rating.</p></footer><script src="/assets/explorer.js" defer></script><script src="/assets/support.js?v=1103b" defer></script><script src="/assets/lookup.js?v=1103" defer></script>{beacon}</body></html>'''
    f = os.path.join(OUT, path.strip('/'), 'index.html') if path.endswith('/') else os.path.join(OUT, path.strip('/'))
    os.makedirs(os.path.dirname(f), exist_ok=True); open(f, 'w', encoding='utf-8').write(doc)

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

# ---- home: the car finder first (10-29), how to read a score, the explorer, then best vs worst side by side, then brands
best4, worst4 = CARS[0], CARS[-1]
# 10-30: Google showed /method/ for "lemon index" (its h1 was the only one saying the brand), so the home h1 now carries the name too.
page('/', "Lemon Index (LemonIndex): Look Up Any Car's Problems by Year", "Look up any car's problems by model year, 2000 to 2022: its reliability score, top problem areas and real owner complaints, from 1.6 million complaints filed with the government. 100 is the average car.", f'''
{finder(h='<span class="fbrand">The Lemon Index</span>Look up any car')}
<section class="hero2"><p class="kicker">How to read a score</p><p class="sub">We counted {COUNTED:,} safety complaints owners filed with the government, then divided by how many of each car were sold. <b>100 is the average car</b>, lower is better.</p>
<div class="scale"><div class="sbar"><i style="left:{min(96, best4["li"] / 3.5):.1f}%" title="{E(best4["name"])}, {best4["li"]}"></i></div><div class="sl"><span>25 · ¼ the complaints</span><span>100 · average car</span><span class="bad">300+ · 3× or worse</span></div></div></section>
{explorer()}
<section class="duo"><div><h2>The most reliable cars</h2><p class="sub">Lowest Lemon Index. Hover a bar to read it in plain English.</p>{bars([(n, v) for n, v, _ in BEST[:6]], 120)}</div>
<div><h2>The biggest lemons</h2><p class="sub">Highest Lemon Index. * Tesla uses published sales estimates.</p>{bars([(n, v) for n, v, _ in WORST[:6]], 440)}</div></section>
<section><h2>Every brand, best to worst</h2><p class="sub">All of a brand's models together, same scale: 100 is the average car.</p>{bars(BRANDS, 330, 'two')}<p class="note">* Porsche is a small sample (2 models, 258,000 sold). Tesla uses estimated U.S. sales.</p></section>
<section class="faq"><h2>Questions</h2>{faq}</section>''',
     ld=[{"@context": "https://schema.org", "@type": "WebSite", "name": "The Lemon Index", "alternateName": ["Lemon Index", "LemonIndex", "lemonindex", "lemonindex.com"], "url": BASE + '/'},
         {"@context": "https://schema.org", "@type": "Organization", "name": "The Lemon Index", "alternateName": ["Lemon Index", "LemonIndex", "lemonindex.com"], "url": BASE + '/', "logo": BASE + '/assets/icon-180.png', "sameAs": [YT, TT, IG]},
         {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}])

# ---- study
page(STUDY, 'The Most Reliable Cars, According to 1.6 Million Owner Complaints', 'The most and least reliable cars and brands in the U.S., ranked by NHTSA safety complaints per 100,000 sold. Toyota 4Runner 26, Lexus 30, Tesla 322 (est.).', f'''
<article class="study"><p class="kicker">Study #1 · {TODAY}</p><h1>The Most Reliable Cars, According to 1.6 Million Owner Complaints</h1>
<p class="lede">The Toyota 4Runner drew about a quarter of the complaints of the average car. The Tesla Model S drew more than four times as many. Here's every number.</p>
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
</article>''', kind='article',
     ld=[{"@context": "https://schema.org", "@type": "Dataset", "name": "Lemon Index: U.S. car reliability by NHTSA complaints per 100,000 sold", "description": "131 models and 22 brands, model years 2010-2022, ranked by safety complaints filed with NHTSA within 3 years of the model year per 100,000 U.S. sales, indexed to the average car (100).",
          "url": BASE + STUDY, "creator": {"@type": "Organization", "name": "The Lemon Index"}, "license": "https://creativecommons.org/licenses/by/4.0/", "isBasedOn": "https://www.nhtsa.gov/nhtsa-datasets-and-apis", "temporalCoverage": "2010/2022", "dateModified": TODAY},
         {"@context": "https://schema.org", "@type": "Article", "headline": "The Most Reliable Cars, According to 1.6 Million Owner Complaints", "datePublished": TODAY, "dateModified": TODAY, "author": {"@type": "Organization", "name": "The Lemon Index"}, "image": BASE + '/assets/og.png'}])

# ---- studies index
page('/studies/', 'Car Reliability Studies: Rankings From Owner Complaints | Lemon Index', 'Every Lemon Index study: the most and least reliable cars, brands and electric cars, measured with 1.6 million NHTSA owner complaints and U.S. sales.', f'''
<section><h1>Studies</h1><p class="lede">Each study turns millions of public records into one clear ranking.</p>
<a class="card" href="{STUDY}"><span class="kicker">Study #1</span><h2>The Most Reliable Cars, According to 1.6 Million Owner Complaints</h2><p>131 models, 22 brands. Toyota 4Runner 27 · Lexus 30 · Tesla 322 (est.)</p></a>
<a class="card" href="/electric/"><span class="kicker">Electric cars</span><h2>The Most Reliable Electric Cars, Ranked by Owner Complaints</h2><p>22 EVs, plus fires, yearly cost, common problems and driver-assist crash reports.</p></a>
<p class="note">Next up: cars that last past 300,000 miles, the most unreliable cars ever made, and the best used cars under $10K.</p></section>''',
     ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Car Reliability Studies", "url": BASE + '/studies/', "hasPart": [{"@type": "Article", "headline": "The Most Reliable Cars, According to 1.6 Million Owner Complaints", "url": BASE + STUDY}]}])

# ---- method
def faq_ld(qa): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": t}} for q, _, t in qa]}
METHOD_QA = [('Is it per car sold?', "Yes. Every score divides a car's complaints by how many were sold in the U.S. So Ford outselling Chevy doesn't make Ford look worse; a car only scores badly if it drew more complaints for each car on the road."), ("Isn't it just owners who skip maintenance?", "We only count complaints filed in a car's first 3 years, when it's nearly new and usually still under the factory warranty. That points at problems the car left the factory with, not a 15-year-old car that missed its oil changes."), ('Does it tell me how long a car will last?', "No. It measures early complaints, not lifespan. A truck can draw a lot of complaints in its first years and still run past 300,000 miles. Use it to see which years had problems, then check the car's own history."), ('Why so few complaints for a problem everyone knows about?', "Most owners never file with the government; they just go to a mechanic. So the counts are a small slice of real failures. That's fine for comparing cars, because every car is measured the same way, but don't read a count as the number of cars that broke."), ('Can you split it by engine or trim?', 'The government files list make, model and year, not the engine. Where the model name gives the engine away (BMW files the 328i and 335i separately, for example), we can split by it. Otherwise a score covers every engine sold that year.')]
page('/method/', 'Method: How We Score Car Reliability | The Lemon Index', 'How we turn NHTSA safety complaints and U.S. sales into one reliability number per car, plus the caveats that come with it.', '''
<article class="study"><p class="kicker">How it works</p><h1>How the Lemon Index works</h1>
<p class="lede">One number per car and year: how many safety complaints owners filed, compared with an average car.</p>
<div class="hw"><div><b>1</b><h3>Count complaints</h3><p>Every safety complaint owners filed with the U.S. government (NHTSA) in the car&#39;s first 3 years.</p></div>
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
<h2>What people ask</h2><h3>Is it per car sold?</h3><p>Yes. Every score divides a car&#39;s complaints by how many were sold in the U.S. So Ford outselling Chevy doesn&#39;t make Ford look worse; a car only scores badly if it drew more complaints for each car on the road.</p><h3>Isn&#39;t it just owners who skip maintenance?</h3><p>We only count complaints filed in a car&#39;s first 3 years, when it&#39;s nearly new and usually still under the factory warranty. That points at problems the car left the factory with, not a 15-year-old car that missed its oil changes.</p><h3>Does it tell me how long a car will last?</h3><p>No. It measures early complaints, not lifespan. A truck can draw a lot of complaints in its first years and still run past 300,000 miles. Use it to see which years had problems, then check the car&#39;s own history.</p><h3>Why so few complaints for a problem everyone knows about?</h3><p>Most owners never file with the government; they just go to a mechanic. So the counts are a small slice of real failures. That&#39;s fine for comparing cars, because every car is measured the same way, but don&#39;t read a count as the number of cars that broke.</p><h3>Can you split it by engine or trim?</h3><p>The government files list make, model and year, not the engine. Where the model name gives the engine away (BMW files the 328i and 335i separately, for example), we can split by it. Otherwise a score covers every engine sold that year.</p><h2>Using the data</h2><p>The rankings are free to cite with a link to lemonindex.com (CC BY 4.0). The raw complaint data is public at NHTSA.</p></article>''',
     ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": "How We Score Car Reliability", "url": BASE + '/method/', "about": "Car reliability measured as NHTSA safety complaints per 100,000 U.S. sales"}, faq_ld([(q, '', a) for q, a in METHOD_QA])])

# ---- model-year lookup (10-29, Elijah: "a per year / model lookup so people can look at their car's exact issues").
# data/years.json comes from data_years.py: per family and model year the index, complaints, sold, top problem areas and up to 3 owner complaints.
YEARS = [f for f in json.load(open('data/years.json', encoding='utf-8')) if f['name'] in BYNAME]
# 10-29: model years 2000-2009 added (Elijah's car is a 2008). Their scores are rough (fewer owners filed online, launch years sold partly the
# calendar year before), so a pre-2010 year with under 20 complaints gets no score, and its page says the score is rough.
for f in YEARS:
    for v in f['years']: v['ok'] = v['y'] >= 2010 or v['n'] >= 20
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
def ybars(f, cur=None):
    mx = max(120, max(v['li'] for v in f['years'] if v['ok']) * 1.08)
    return (f'<div class="bars yb"><div class="bl" aria-hidden="true"><span></span><span class="al" style="--a:{100 / mx * 100:.1f}%">average car = 100</span><span></span></div>'
            + ''.join(f'<a class="b {CLS(v)}{" cur" if v["y"] == cur else ""}" href="{CARU(f, v["y"])}" data-tip="{E(f["name"])} {v["y"]}: ' + (f'Lemon Index {v["li"]}, {plain(v["li"])}' if v['ok'] else f'only {v["n"]} complaints, too few to score') + f'."><span class="bn">{v["y"]}</span><span class="bt"><i style="width:{min(100, v["li"] / mx * 100) if v["ok"] else 0:.1f}%"></i><em style="left:{100 / mx * 100:.1f}%"></em></span><b>{LIS(v)}</b><small>{short(v["li"]) if v["ok"] else "few complaints"}</small></a>' for v in f['years']) + '</div>')
# 10-31 idea 5: "X vs Y" pages for the best-selling rivals in each type (people search "camry vs accord reliability").
FY = {f['id']: f for f in YEARS}
RIVALS = defaultdict(list); PAIRS = []
for seg, top in (('car', 10), ('suv', 10), ('truck', 7), ('minivan', 5)):
    ids = [c['id'] for c in sorted((c for c in CARS if c['seg'] == seg and c['id'] in FY), key=lambda c: -c['sold'])][:top]
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
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
    return (f'<section class="yc"><h2>When owners reported problems <span class="h2s">(from owner complaints to the government)</span></h2><div class="tl"><div class="tl-bar"><i class="tl-band" style="left:{P(m["p25"])};width:calc({P(m["p75"])} - {P(m["p25"])})"></i>'
            f'<i class="tl-mid" style="left:{P(m["median"])}"><b>half by {m["median"] // 1000}K</b></i></div><div class="tl-ticks">{ticks}</div></div>'
            f'<p class="yc-cap">Most owners who filed a complaint with NHTSA had <b>{m["p25"] // 1000}K to {m["p75"] // 1000}K miles</b> on the car ({m["n"]:,} complaints listed the miles). This shows when people who had a problem reported it, not the odds that your car will have it.</p>'
            + (f'<ul class="tl-top">{top}</ul>' if top else '') + '</section>')
X2 = _load('data/extras2.json')
TR = _load('data/trans.json')   # transmission complaints per model-year (data_trans.py)
PH = _load('data/photos.json')   # exact-year Wikimedia Commons cutouts (data_photos.py), {fid: {year: {src, author, license, page, w, h}}}
LIC = {'CC BY-SA 4.0': 'https://creativecommons.org/licenses/by-sa/4.0/', 'CC BY-SA 3.0': 'https://creativecommons.org/licenses/by-sa/3.0/', 'CC BY 4.0': 'https://creativecommons.org/licenses/by/4.0/'}
def car_photo(fid, y, name):
    ph = PH.get(fid, {}).get(str(y))
    if not ph: return ''
    who = ph['author'].split('\ufffd')[0].strip().replace('National Highway Traffic Safety Administration', 'NHTSA'); lic = ph['license']
    lic_h = f'<a href="{LIC[lic]}" rel="noopener license">{E(lic)}</a>' if lic in LIC else E(lic)
    return (f'<figure class="yph"><img src="{ph["src"]}" alt="{y} {E(name)}" width="{ph["w"]}" height="{ph["h"]}" fetchpriority="high">'
            f'<figcaption>Photo: <a href="{E(ph["page"])}" rel="noopener">{E(who)}</a>, Wikimedia Commons · {lic_h} · background removed</figcaption></figure>')
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
        a = f'{word} by government complaints. It drew {plain(v["li"])} filed with NHTSA in its first 3 years, per car sold (Lemon Index {v["li"]}; 100 is average, lower is better).'
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
    return [(q, a, re.sub('<[^>]+>', '', html.unescape(a))) for q, a in out]
def year_body(f, v, y, x, best, worst, prev, nxt, qs_list, qa=()):
    nm = E(SNM(f)); x2 = X2.get(f['id'], {}).get(str(y), {}); mkr = E(MAKER(f['name']))
    share_txt = (f'{y} {SNM(f)}: {plain(v["li"])} per car sold' if v['ok'] else f'{y} {SNM(f)}: owner complaints and recalls') + (f', {len(x["recalls"])} recalls' if x.get('recalls') else '') + '. Free report:'
    rec = x.get('recalls') or []; m = x.get('mpg'); sf = x.get('safety'); s = x.get('sev') or {}
    if v['ok']:
        cls, word = verdict(v['li'])
        hero = (f'<div class="yv {cls}"><b>{word}</b><span>{E(plain(v["li"]))}</span></div>{meter(v["li"])}')
    else:
        hero = f'<div class="yv mid"><b>Not enough data</b><span>Only {v["n"]} complaints in its first 3 years: too few to score.</span></div>'
    old = '<p class="yc-note">Older model year: fewer owners filed complaints back then, so treat the score as rough.</p>' if y < 2010 else ''
    inv_open = [i for i in x2.get('inv', []) if i['open']]
    badges = ''.join(b for b in [f'<a class="yb bad" href="#inv">Under government investigation</a>' if inv_open else '',
                                 f'<a class="yb" href="#fixes">{x2["tsb"]["n"]} repair notes from {mkr}</a>' if x2.get('tsb') else ''] if b)
    old = (f'<div class="ybs">{badges}</div>' if badges else '') + old
    rng = lambda a: f'{a[0]}' if a[0] == a[1] else f'{a[0]}–{a[1]}'
    facts = [('Owner complaints', f'{v["n"]:,}', 'first 3 years'), ('Recalls', f'{len(rec)}' if 'recalls' in x else '—', 'free fix at any dealer' if rec else 'none on record'),
             ('Fuel economy', f'{rng(m["comb"])} {"MPGe" if m.get("ev") else "mpg"}' if m else '—', 'combined, EPA'),
             (('Crash test', stars(sf['best']), 'NHTSA overall') if sf and sf.get('best') else ('Front crash', stars(x2['old']['front']), 'NHTSA, driver') if (x2.get('old') or {}).get('front') else ('Crash test', '<span class="muted">not rated</span>', 'NHTSA'))]
    tiles = ''.join(f'<div class="yt"><span class="yt-l">{l}</span><b class="yt-v">{val}</b><small>{sub}</small></div>' for l, val, sub in facts)
    yrs = ''.join(f'<a class="ychip {c}" href="{CARU(f, w["y"])}"><small>{lab}</small><b>{w["y"]}</b></a>' for lab, w, c in (('best year', best, 'good'), ('worst year', worst, 'bad')) if w['y'] != y)
    nav = ''.join(f'<a class="ychip" href="{CARU(f, w["y"])}"><small>{lab}</small><b>{w["y"]}</b></a>' for lab, w in (('previous', prev), ('next', nxt)) if w)
    parts = ''.join(f'<div class="pt"><span>{E(NICE(p))}</span><span class="bt"><i style="width:{k}%"></i></span><b>{k}%</b></div>' for p, k in v['parts'])
    probs = f'<section class="yc"><h2>What owners complain about most <span class="h2s">(from owner complaints to the government)</span></h2><div class="pts">{parts}</div><p class="yc-cap">Share of this year&#39;s owner complaints filed with NHTSA, not the share of cars that break. One complaint can name more than one area.</p>' + (f'<p class="yc-cap"><a href="{CARU(f)}transmission/">Transmission problems in every {nm} year →</a></p>' if f['id'] in TR else '') + '</section>' if parts else ''
    sev_items = [(s.get('crash', 0), 'crashes'), (s.get('injured', 0), 'injuries'), (s.get('fire', 0), 'fires'), (s.get('towed', 0), 'tows')]
    sev = (f'<section class="yc"><h2>How serious</h2><p class="yc-cap">Out of {s["total"]:,} owner complaints, owners reported:</p><div class="sv">'
           + ''.join(f'<div class="{"bad" if n else "good"}"><b>{n:,}</b><span>{lab}</span></div>' for n, lab in sev_items) + '</div></section>') if s.get('total') else ''
    if 'recalls' in x:
        rs = sorted(rec, key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2], reverse=True)
        card = lambda r: f'<li><b>{E(RPART(r["part"]))}</b> <small>{E(r["date"][-4:])}</small><p>{E(rsum(r))}</p></li>'
        recs = (f'<section class="yc"><h2>Recalls <span class="yc-n">{len(rs)}</span></h2>'
                + (f'<ul class="rc">{"".join(card(r) for r in rs[:3])}</ul>' + (f'<details><summary>Show all {len(rs)} recalls</summary><ul class="rc">{"".join(card(r) for r in rs[3:])}</ul></details>' if len(rs) > 3 else '')
                   if rs else '<p>No safety recalls on record.</p>')
                + '<p class="yc-cap">Recall repairs are free at any dealer. Check a specific car&#39;s VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener">nhtsa.gov/recalls</a>.</p></section>')
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
    words = ''
    if qs_list:
        q0 = qs_list[0]; more = ''.join(f'<blockquote><p>{E(q["text"])}</p><cite>NHTSA complaint {q["odi"]}</cite></blockquote>' for q in qs_list[1:])
        words = (f'<section class="yc"><h2>In owners&#39; words</h2><blockquote><p>{E(q0["text"])}</p><cite>{y} {nm} owner · NHTSA complaint {q0["odi"]}</cite></blockquote>'
                 + (f'<details><summary>More owner reports</summary>{more}</details>' if more else '') + '</section>')
    return f'''
<article class="yp"><p class="kicker"><a href="/cars/">All cars</a> · <a href="{CARU(f)}">{nm}</a> · {y}</p>
{car_photo(f["id"], y, f["name"])}<div class="ytop"><header class="yh"><h1>{y} {nm}</h1><p class="yh-sub">Reliability, problems and recalls</p>{f'<p class="yc-note">{SN[f["id"]][1]}</p>' if f["id"] in SN else ""}{hero}{old}</header>
<div class="ytop-r"><div class="yts">{tiles}</div>
<div class="ychips">{yrs}{nav}<a class="ychip" href="{CARU(f)}"><small>every</small><b>all years</b></a><a class="ychip ycmp" href="/compare/?c={f['id']}-{y}"><small>side by side</small><b>Compare ⇄</b></a><button type="button" class="ychip yshare" data-share="{E(share_txt)}"><small>send to a friend</small><b>Share ↗</b></button></div></div></div>
<div class="ygrid">{probs}{timeline(x["miles"], x.get("comps") or []) if x.get("miles") else ""}{(lambda ph: f'<section class="yc ywide">{ph}</section>' if ph else '')(price_html(f["id"], y, f["name"]))}{sev}{recs}
{fixes}{invs}{safety}{f'<section class="yc">{crash}{fuel}</section>' if crash or fuel else ''}{words}
{f'<section class="yc ywide yqa"><h2>Quick answers</h2>' + "".join(f"<h3>{E(q)}</h3><p>{a}</p>" for q, a, _ in qa) + '</section>' if qa else ''}
<section class="yc ywide"><h2>Every {nm} year</h2>{ybars(f, y)}</section></div>
<p class="yc-cap">Lemon Index = safety complaints filed with the U.S. government (NHTSA) in a car&#39;s first 3 years, per car sold, against the average car of the same model year. 100 is average; lower is better. A complaint is an owner&#39;s report, not a confirmed defect. <a href="/method/">How it works</a></p></article>'''

def yearx(fid, y): return extra(fid, y)
for f in YEARS:
    c = BYNAME[f['name']]; ys = f['years']; sc = [v for v in ys if v['ok']]; best, worst = min(sc, key=lambda v: v['li']), max(sc, key=lambda v: v['li'])
    good3 = sorted(sc, key=lambda v: v['li'])[:3]; bad3 = [v for v in sorted(sc, key=lambda v: -v['li']) if v['li'] > 110][:3]
    def why(v):
        xx = yearx(f['id'], v['y']); bits = [plain(v['li'])]
        if v['parts']: bits.append(f'top problem: {v["parts"][0][0]}')
        if 'recalls' in xx: bits.append(f'{len(xx["recalls"])} recalls')
        return E(', '.join(bits))
    buy = ''.join(f'<li><a href="{CARU(f, v["y"])}"><b>{v["y"]}</b></a>: {why(v)}</li>' for v in good3)
    avoid = ''.join(f'<li><a href="{CARU(f, v["y"])}"><b>{v["y"]}</b></a>: {why(v)}</li>' for v in bad3)
    picks = (f'<div class="stack"><div><h2>Best {E(SNM(f))} years to buy</h2><ol class="beats">{buy}</ol></div>'
             + (f'<div><h2>{E(SNM(f))} years to avoid</h2><ol class="beats">{avoid}</ol></div>' if avoid else f'<div><h2>Years to avoid</h2><p>No {E(f["name"])} year drew more than about the average car&#39;s complaints.</p></div>') + '</div>')
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
    model_qa_html = '<section class="yqa"><h2>Quick answers</h2>' + ''.join(f'<h3>{E(q)}</h3><p>{a}</p>' for q, a in mqa) + '</section>'
    page(CARU(f), f'{snm} Reliability by Year: Years to Avoid & Best to Buy',
         f'Every {snm} model year from {ys[0]["y"]} to {ys[-1]["y"]}, ranked by NHTSA owner complaints per car sold. Best: {best["y"]}. Worst: {worst["y"]} ({plain(worst["li"])}).', f'''
<article class="study"><p class="kicker"><a href="/cars/">All cars</a> · {E(c["segName"])}</p><h1>{E(snm)} reliability by year</h1>{f'<p class="sub">{SN[f["id"]][1]}</p>' if f["id"] in SN else ""}
<p class="lede">Best year: <b>{best["y"]}</b>, {plain(best["li"])}. Worst year: <b>{worst["y"]}</b>, {plain(worst["li"])}. Click a year to see what owners reported.</p>
<p><button type="button" class="btn btn-ghost" data-share="{E(f'Every {snm} year ranked by owner complaints. Best: {best["y"]}. Worst: {worst["y"]}. Free report:')}">Share ↗</button></p>
<p class="sub">Lemon Index = safety complaints filed with the government within 3 years, per car sold, compared with the average car of the same model year. <b>100 is average, lower is better.</b>{" Scores before 2010 are rough: fewer owners filed complaints back then." if ys[0]["y"] < 2010 else ""}</p>
{ybars(f)}{picks}{model_qa_html}<h2>Every year</h2><div class="tw"><table><thead><tr><th>Year</th><th>Index</th><th>Compared with average</th><th>Complaints</th><th>Top complaint</th><th>Recalls</th><th>Crash test</th><th>MPG</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Whole model ({c["years"]}): Lemon Index {c["li"]}, {plain(c["li"])}. <a href="/method/">How the index works</a></p>{f'<p><a class="btn" href="{CARU(f)}transmission/">{E(snm)} transmission problems by year →</a></p>' if f["id"] in TR else ''}{f'<h2>Compare the {E(f["name"])}</h2><p>{vs}</p>' if vs else ''}</article>''',
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{snm} reliability by year', "url": BASE + CARU(f)},
             faq_ld([(q, '', html.unescape(a)) for q, a in mqa])])
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
        page(CARU(f, y), f'{y} {snm} Reliability, Problems and Recalls | The Lemon Index',
             (f'The {y} {snm} drew {plain(v["li"])} per car sold (NHTSA).' if v['ok'] else f'Owners filed only {v["n"]} NHTSA complaints about the {y} {snm} in its first 3 years.')
             + (f' {nrec} recall{"s" if nrec != 1 else ""}.' if nrec else '') + (f' Top problems: {top}.' if top else '') + ' Real owner complaints and every other year.', year_body(f, v, y, x, best, worst, prev, nxt, v['quotes'], qa), kind='article', ask=(f['id'], y, f'{y} {snm}'), img=(PH.get(f['id'], {}).get(str(y)) or {}).get('src'),
             ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{y} {snm} reliability, problems and recalls', "url": BASE + CARU(f, y)}
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
         body, kind='article', ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{snm} transmission problems by year', "url": BASE + CARU(f) + 'transmission/'}, faq_ld(qa)])
    turls.append(CARU(f) + 'transmission/')
TRANS_OK = {u.split('/')[2] for u in turls}
yurls += turls
pick = {}
for f in YEARS: pick.setdefault(BYNAME[f['name']]['brand'], []).append([f['name'], f['id'], [v['y'] for v in f['years']]])
pick = dict(sorted((b, sorted(m)) for b, m in pick.items()))
lst = ''.join(f'<div><h3>{E(b)}</h3>' + ''.join(f'<a href="/cars/{i}/">{E(n)}</a>' for n, i, _ in m) + '</div>' for b, m in pick.items())
page('/cars/', 'Look Up Your Car: Problems by Model and Year | The Lemon Index', f'Pick your car and model year to see its owner complaints, its top problems and how it compares with every other year. {len(YEARS)} models, 2000-2022.', f'''
{finder('Look up your car')}
<section><h2>Every model</h2><div class="brands">{lst}</div></section>''',
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
<div class="verdict{' tie' if close else ''}">{verdict}</div>
<h2>Head to head</h2>{duel}
<p class="sub">Lemon Index = safety complaints filed with the government within 3 years, per car sold, against the average car of the same model year. <b>100 is average, lower is better.</b> Green check = the better of the two on that line.</p>
<h2>Year by year</h2><p class="sub">Shorter bar = fewer complaints per car sold. Tap a year for its full report.</p><div class="yrs">{yrs}</div>
<p class="note"><a href="{CARU(A)}">Every {E(A["name"])} year</a> · <a href="{CARU(B)}">Every {E(B["name"])} year</a> · <a href="/method/">How the index works</a></p></article>''', kind='article',
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": BASE + CMPU(a, b)}])
    curls.append(CMPU(a, b))
cl = ''.join(f'<li><a href="{u}">{E(FY[a]["name"])} vs {E(FY[b]["name"])}</a></li>' for (a, b), u in zip([p for p in PAIRS if CMPU(*p) in curls], curls))
page('/compare/', 'Car Reliability Comparisons: Model vs Model | The Lemon Index', f'{len(curls)} head-to-head reliability comparisons of popular rivals, year by year, from NHTSA owner complaints per car sold.', f'''
<section><h1>Compare cars</h1><p class="lede">Put up to 3 cars side by side: problems, recalls, fuel economy and crash tests.</p><div id="cmpx" class="cmpx"><p class="note">Loading…</p></div></section>
<section><h2>Popular match-ups</h2><ul class="cmp">{cl}</ul></section><script src="/assets/compare.js?v=1102" defer></script>''',
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
<h2>Visiting the site</h2><p>We use Cloudflare Web Analytics, which counts visits without cookies and without identifying you. We don&#39;t run ad trackers.</p>
<h2>If you donate or give us your email</h2><p>Donations are handled by Stripe; we never see or store your card number. If you give us your email, we use it to send car-buying tips and new studies, and every email has an unsubscribe link.</p>
<h2>The "Help our site" questions</h2><p>Answers are anonymous. We store your answer, the page and car you were on, and a daily scrambled code (a one-way hash of your IP address and the date) that only stops repeat answers. We never store your IP address, and there&#39;s no email, name or account.</p>
<h2>Sharing</h2><p>We don&#39;t sell your personal information. We share it only with the services that run the site (hosting, sign-in, email, Stripe) and when the law requires it.</p>
<h2>Your choices</h2><p>Email <a href="mailto:{CONTACT}">{CONTACT}</a> to get a copy of your data or to have it deleted.</p>
<p>{LEGAL_NAME}, {ADDRESS}.</p>''', 'Privacy Policy: No Ad Trackers, Cookieless Stats | Lemon Index',
      'What lemonindex.com collects: cookieless visit counts from Cloudflare, no ad trackers, and your email only if you give it to us. Donations run through Stripe.')
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

open(f'{OUT}/404.html', 'w', encoding='utf-8').write(open(f'{OUT}/index.html', encoding='utf-8').read().replace('<main>', '<main><section><h1>That page drove off.</h1><p><a href="/">Back to the rankings</a></p></section><!--', 1).replace('</main>', '--></main>', 1))
urls = ['/', STUDY, '/studies/', '/method/', '/vin/'] + eurls + yurls + curls + LEGAL_URLS
open(f'{OUT}/sitemap.xml', 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{BASE}{u}</loc><lastmod>{TODAY}</lastmod></url>' for u in urls) + '</urlset>')
open(f'{OUT}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')
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
page('/vin/', 'Free VIN Check: Decode Any VIN and See Its Problems | The Lemon Index', 'Type a 17-character VIN to see the exact year, engine and factory, then that car\'s owner complaints and recalls. Free, from the U.S. government VIN database.', f'''
<section class="finder"><h1>Free VIN check</h1><p class="lede">Type the 17-character VIN to see exactly what car it is, then its problems and recalls.</p>
<form id="vinf" class="vinf" autocomplete="off"><input name="vin" maxlength="20" placeholder="e.g. 1FTEW1EG8JKF05094" aria-label="VIN" spellcheck="false"><button class="btn" type="submit">Check</button></form>
<div id="vinout" class="vinout"></div><p class="note">The VIN is on the driver-side dashboard (look through the windshield), the driver door frame, and your registration or insurance card. Decoded by NHTSA&#39;s free vPIC database; we don&#39;t store it.</p>
<script id="pick" type="application/json">{json.dumps(PICK, ensure_ascii=False).replace("</", "<\\/")}</script><script id="valias" type="application/json">{json.dumps(VALIAS, separators=(",", ":"))}</script><script src="/assets/vin.js?v=1102b" defer></script></section>''')
shutil.copytree('assets', f'{OUT}/assets', dirs_exist_ok=True); shutil.copy('data/survey.json', f'{OUT}/assets/survey-q.json')
print('built', len(urls), 'pages into', OUT)
