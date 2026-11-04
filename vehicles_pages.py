# Planes + motorcycles sections (11-04). Run by build.py with exec() (page, E, phero, pimg, pcredit, who, qa_fold, BASE in scope).
# data/planes.json (data_planes.py, NTSB) + data/moto.json (data_moto.py, NHTSA complaints) + photos in data/vehicle_photos.json (data_vehicle_photos.py).
VPH = _load('data/vehicle_photos.json') if os.path.exists('data/vehicle_photos.json') else {}
slugify = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower().replace("'", '')).strip('-')
def vph(name): return VPH.get(name)
def bars_pct(rows, cls=''):
    mx = max([v for _, v in rows] + [1])
    return '<div class="pts">' + ''.join(f'<div class="pt"><span>{E(k)}</span><span class="bt"><i style="width:{v / mx * 100:.0f}%"></i></span><b>{v}%</b></div>' for k, v in rows) + '</div>'
def bars_n(rows):
    mx = max([v for _, v in rows] + [1])
    return '<div class="pts vyr">' + ''.join(f'<div class="pt"><span>{E(str(k))}</span><span class="bt"><i style="width:{v / mx * 100:.0f}%"></i></span><b>{v:,}</b></div>' for k, v in rows) + '</div>'
def stat(n, lab, cls=''): return f'<div class="yt"><b class="yt-v {cls}">{n}</b><small>{lab}</small></div>'
def card(href, ph, name, big, cls, small=''):
    return (f'<a class="mc vmc" href="{href}"><span class="mc-p">{pimg(ph, name) if ph else ""}</span><b>{E(name)}</b>'
            f'<span class="{cls}">{big}</span>{f"<small>{small}</small>" if small else ""}</a>')

# ---------------- planes
PL = _load('data/planes.json') if os.path.exists('data/planes.json') else []
purls = []
NTSB = 'NTSB aviation accident database, U.S. accidents 2008–2025.'
if PL:
    for p in PL:
        slug = slugify(p['name']); p['slug'] = slug; ph = vph(p['name'])
        whatrows = [[k, v] for k, v in p['what'] if k]
        mech = '' if p['mech_pct'] is None else f'''<section class="yc"><h2>Pilot or plane? <span class="h2s">How often NTSB listed an aircraft problem among the causes.</span></h2>
<div class="vsplit"><div><b>{p["mech_pct"]}%</b><span>the plane was part of the cause<br><small>engine, systems, structure or propeller</small></span></div><div><b>{100 - p["mech_pct"]}%</b><span>people or weather only<br><small>pilot decisions, control, fuel planning</small></span></div></div>
<p class="yc-cap">Out of {p["judged"]:,} accidents where NTSB recorded a cause.{" When the plane was a cause, it was most often the " + E(p["mech_parts"][0][0]) + "." if p["mech_parts"] else ""}</p></section>'''
        body = f'''<div class="pg mp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/planes/">Planes</a> · {E(p["kind"])}</p><h1>{E(p["name"])}.</h1>
<p class="ph-s">Every U.S. accident NTSB investigated, 2008 to 2025.</p></div><div class="ph-v">{pimg(ph, p["name"]) if ph else ""}{pcredit(who(ph)) if ph else ""}</div></section>
<div class="yts">{stat(f'{p["n"]:,}', 'accidents')}{stat(f'{p["fatal_pct"]}%', 'were fatal', 'bad' if p['fatal_pct'] >= 20 else '')}{stat(f'{p["deaths"]:,}', 'deaths')}{stat(f'{p["destroyed_pct"]}%', 'aircraft destroyed')}</div>
<section class="yc"><h2>What happened. <span class="h2s">NTSB's defining event, share of accidents.</span></h2>{bars_pct(whatrows)}</section>
{mech}
<section class="yc"><h2>When. <span class="h2s">Phase of flight.</span></h2>{bars_pct(p["phase"])}</section>
<section class="yc"><h2>Accidents per year.</h2>{bars_n([(y, v) for y, v in p["by_year"].items()])}<p class="yc-cap">More planes flying means more accidents, so counts aren&#39;t a safety score by themselves. Compare the shares above.</p></section>
<p class="yc-cap" style="text-align:center">Source: {NTSB} <a href="https://www.ntsb.gov/Pages/investigations.aspx" rel="noopener">ntsb.gov</a> · <a href="/planes/">Every plane</a></p></div>'''
        page(f'/planes/{slug}/', f'{p["name"]} Accidents: What Happened, How Often Fatal | The Lemon Index',
             f'{p["n"]:,} U.S. {p["name"]} accidents NTSB investigated (2008-2025): {p["fatal_pct"]}% fatal, top event: {whatrows[0][0] if whatrows else "n/a"}. Plane-caused share, phase of flight and accidents per year.', body,
             ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{p["name"]} accidents', "url": BASE + f'/planes/{slug}/'}])
        purls.append(f'/planes/{slug}/')
    kinds = list(dict.fromkeys(p['kind'] for p in PL))
    groups = ''.join(f'<div class="mb"><h3>{E(k)}</h3><div class="mg">' + ''.join(card(f'/planes/{p["slug"]}/', vph(p['name']), p['name'], f'{p["fatal_pct"]}%', 'bad' if p['fatal_pct'] >= 20 else '', f'{p["n"]:,} accidents') for p in sorted([p for p in PL if p['kind'] == k], key=lambda p: -p['n'])) + '</div></div>' for k in kinds)
    big = [p for p in PL if p['n'] >= 80 and p['kind'] != 'Airliner']
    fat = sorted(big, key=lambda p: -p['fatal_pct'])
    mech = sorted([p for p in big if p['mech_pct'] is not None], key=lambda p: -p['mech_pct'])
    air = [p for p in PL if p['kind'] == 'Airliner']
    turb = round(sum(dict(p['what']).get('Turbulence encounter', 0) * p['n'] for p in air) / max(1, sum(p['n'] for p in air)))
    page('/planes/', 'Plane Accidents by Model: Which Small Planes Crash Most | The Lemon Index',
         f'Every U.S. plane and helicopter accident NTSB investigated, 2008-2025, by model: how often they were fatal, what happened, and how often the plane itself was a cause. {len(PL)} models.',
         f'''<div class="pg">{phero('Planes', 'Plane accidents, by model.', 'Every U.S. accident NTSB investigated, 2008 to 2025. Corner number: share that were fatal.', visual=pimg(vph('Cirrus SR22'), 'Cirrus SR22') if vph('Cirrus SR22') else '')}
<section class="tiles"><div class="tile"><div class="tt"><p class="te">When it crashes</p><h2>{E(fat[0]["name"])}.</h2><p class="ts">{fat[0]["fatal_pct"]}% of its accidents were fatal, the most of any common model.</p></div></div>
<div class="tile"><div class="tt"><p class="te">Airliners</p><h2>Mostly turbulence.</h2><p class="ts">About {turb}% of U.S. airliner accidents were turbulence encounters. Under 1 in 50 were fatal.</p></div></div></section>
<section><h2>Every model. <span class="h2s">Tap one for what happened, the phase of flight and the plane-vs-pilot split.</span></h2><div class="mbs">{groups}</div></section>
<section class="yc"><h2>When it crashes, how often is it fatal? <span class="h2s">Models with 80+ accidents.</span></h2>{bars_pct([[p["name"], p["fatal_pct"]] for p in fat[:12]])}</section>
<section class="yc"><h2>How often is the plane to blame? <span class="h2s">Accidents where NTSB listed an engine, system, structure or propeller problem among the causes.</span></h2>{bars_pct([[p["name"], p["mech_pct"]] for p in mech[:12]])}</section>
<p class="yc-cap" style="text-align:center">Counts follow fleet size (the Cessna 172 is the most common plane in the U.S.), so compare the shares, not the totals. Per-plane rates need the FAA registry; coming soon. Source: {NTSB}</p></div>''',
         ld=[{"@context": "https://schema.org", "@type": "Dataset", "name": "Plane accidents by model (NTSB, 2008-2025)", "url": BASE + '/planes/', "isBasedOn": "https://www.ntsb.gov/Pages/AviationQueryV2.aspx", "creator": {"@type": "Organization", "name": "The Lemon Index"}}])
    purls.insert(0, '/planes/')

# ---------------- motorcycles
MO = _load('data/moto.json') if os.path.exists('data/moto.json') else []
murls = []
if MO:
    for m in MO:
        slug = slugify(m['name']); m['slug'] = slug; ph = vph(m['name'])
        rc = ''.join(f'<li><b>{E((r["part"] or "").split(":")[0].title())}</b> <small>{E((r["date"] or "")[-4:] or (r["date"] or "")[:4])}</small><p>{E(r["summary"][:220])}…</p></li>' for r in m['recalls'][:3])
        more = ''.join(f'<li><b>{E((r["part"] or "").split(":")[0].title())}</b> <small>{E(r["id"])}</small><p>{E(r["summary"][:220])}…</p></li>' for r in m['recalls'][3:])
        recs = (f'<section class="yc" id="recalls"><h2>Recalls <span class="yc-n">{len(m["recalls"])}</span></h2>'
                + (f'<ul class="rc">{rc}</ul>' + (f'<details><summary>Show all {len(m["recalls"])}</summary><ul class="rc">{more}</ul></details>' if more else '') if m['recalls'] else '<p>No NHTSA recalls found for these model names.</p>')
                + '<p class="yc-cap">Recall repairs are free at any dealer. Check a specific bike&#39;s VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener">nhtsa.gov/recalls</a>.</p></section>')
        body = f'''<div class="pg mp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/motorcycles/">Motorcycles</a> · {E(m["brand"])} · {E(m["seg"])}</p><h1>{E(m["name"])}.</h1>
<p class="ph-s">Owner complaints to the U.S. government, {m["years"][0]} to {m["years"][1]} models.</p></div><div class="ph-v">{pimg(ph, m["name"]) if ph else ""}{pcredit(who(ph)) if ph else ""}</div></section>
<div class="yts">{stat(f'{m["n"]:,}', 'owner complaints')}{stat(f'{len(m["recalls"])}', 'recalls')}{stat(f'{m["serious"]}%', 'involved a crash, fire or injury', 'bad' if m['serious'] >= 25 else '')}{stat(f'{m["miles"]:,}' if m['miles'] else '—', 'typical miles at complaint')}</div>
<section class="yc"><h2>What owners complain about. <span class="h2s">Share of complaints.</span></h2>{bars_pct(m["parts"])}</section>
{recs}
<section class="yc"><h2>Complaints by model year.</h2>{bars_n([(y, v) for y, v in m["by_year"].items()])}<p class="yc-cap">Popular years get more complaints just because more were sold. There are no free U.S. sales figures by motorcycle model, so these are counts, not rates.</p></section>
<p class="yc-cap" style="text-align:center">Filed as: {E(", ".join(m["names"][:5]))}. Source: NHTSA owner complaints and recalls. <a href="/motorcycles/">Every motorcycle</a></p></div>'''
        page(f'/motorcycles/{slug}/', f'{m["name"]} Problems & Recalls: Owner Complaints by Year | The Lemon Index',
             f'{m["n"]:,} NHTSA owner complaints about the {m["name"]} ({m["years"][0]}-{m["years"][1]}): top problem {m["parts"][0][0] if m["parts"] else "n/a"}, {len(m["recalls"])} recalls, {m["serious"]}% involved a crash, fire or injury.', body,
             ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{m["name"]} problems', "url": BASE + f'/motorcycles/{slug}/'}])
        murls.append(f'/motorcycles/{slug}/')
    brands = list(dict.fromkeys(m['brand'] for m in sorted(MO, key=lambda m: -m['n'])))
    groups = ''.join(f'<div class="mb"><h3>{E(b)}</h3><div class="mg">' + ''.join(card(f'/motorcycles/{m["slug"]}/', vph(m['name']), m['name'].replace(b, '').strip() or m['name'], f'{len(m["recalls"])}', 'bad' if len(m['recalls']) >= 10 else 'good', f'{m["n"]:,} complaints') for m in sorted([m for m in MO if m['brand'] == b], key=lambda m: -m['n'])) + '</div></div>' for b in brands)
    ser = sorted([m for m in MO if m['n'] >= 40], key=lambda m: -m['serious'])
    rec = sorted(MO, key=lambda m: -len(m['recalls']))
    page('/motorcycles/', 'Motorcycle Problems & Recalls by Model: Harley, Honda, Yamaha | The Lemon Index',
         f'Owner complaints and recalls for {len(MO)} popular motorcycles (Harley-Davidson, Honda, Yamaha, Kawasaki, Suzuki, BMW, Ducati and more), from NHTSA.',
         f'''<div class="pg">{phero('Motorcycles', 'Motorcycle problems, by model.', 'Owner complaints and recalls filed with the U.S. government. Corner number: recalls.', visual=pimg(vph('Harley-Davidson Touring'), 'Harley-Davidson Touring') if vph('Harley-Davidson Touring') else '')}
<section><h2>Every model. <span class="h2s">Tap one for its problems, recalls and complaints by year.</span></h2><div class="mbs">{groups}</div></section>
<section class="yc"><h2>Most recalls. <span class="h2s">NHTSA recall campaigns across the model years.</span></h2>{bars_n([(m["name"], len(m["recalls"])) for m in rec[:10]])}</section>
<section class="yc"><h2>Most serious complaints. <span class="h2s">Share that involved a crash, fire or injury (models with 40+ complaints).</span></h2>{bars_pct([[m["name"], m["serious"]] for m in ser[:10]])}</section>
<p class="yc-cap" style="text-align:center">There are no free U.S. sales figures by motorcycle model, so this section shows counts and shares, not a per-bike score like our cars. Source: NHTSA owner complaints and recalls.</p></div>''',
         ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Motorcycle problems and recalls by model", "url": BASE + '/motorcycles/'}])
    murls.insert(0, '/motorcycles/')
print('planes pages', len(purls), 'moto pages', len(murls))

# ---------------- supercars (11-04): EPA fuel economy + NHTSA recalls per model year (data_supercars.py)
SC = _load('data/supercars.json') if os.path.exists('data/supercars.json') else []
surls = []
rng2 = lambda a, pre='', suf='': f'{pre}{a[0]:,}{suf}' if a[0] == a[1] else f'{pre}{a[0]:,}–{a[1]:,}{suf}'
if SC:
    for c in SC:
        slug = slugify(c['name']); c['slug'] = slug; ph = vph(c['name']); ys = c['years']; last = ys[-1]
        rows = ''.join(f'<tr><td><b>{y["y"]}</b></td><td class="num">{rng2(y["comb"])}</td><td class="num">{rng2(y["cost"], "$")}</td><td>{E(", ".join(y["engines"][:2]))}{" · hybrid" if y["hybrid"] else ""}</td>'
                       f'<td>{"Yes" if y["guzzler"] else "—"}</td><td class="num">{len(y["recalls"])}</td></tr>' for y in reversed(ys))
        allrec = sorted({r['id']: dict(r, y=y['y']) for y in ys for r in y['recalls']}.values(), key=lambda r: r['date'][-4:] if r['date'] else '', reverse=True)
        rc = ''.join(f'<li><b>{E((r["part"] or "").split(":")[0].title())}</b> <small>{r["y"]} model · {E(r["id"])}</small><p>{E(r["summary"][:230])}…</p></li>' for r in allrec[:4])
        more = ''.join(f'<li><b>{E((r["part"] or "").split(":")[0].title())}</b> <small>{r["y"]} model · {E(r["id"])}</small><p>{E(r["summary"][:230])}…</p></li>' for r in allrec[4:])
        recs = (f'<section class="yc" id="recalls"><h2>Recalls <span class="yc-n">{len(allrec)}</span></h2>' + (f'<ul class="rc">{rc}</ul>' + (f'<details><summary>Show all {len(allrec)}</summary><ul class="rc">{more}</ul></details>' if more else '') if allrec else '<p>No NHTSA recalls on record for these model years.</p>') + '</section>')
        body = f'''<div class="pg mp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/supercars/">Supercars</a> · {E(c["make"])}</p><h1>{E(c["name"])}.</h1>
<p class="ph-s">Fuel economy, fuel cost and recalls, {ys[0]["y"]} to {last["y"]}.</p></div><div class="ph-v">{pimg(ph, c["name"]) if ph else ""}{pcredit(who(ph)) if ph else ""}</div></section>
<div class="yts">{stat(rng2(last["comb"], "", " mpg"), f'combined, {last["y"]} (EPA)')}{stat(rng2(last["cost"], "$"), f'fuel a year, {last["y"]} (EPA)', 'bad' if last['cost'][1] >= 5000 else '')}{stat(str(c["recalls"]), 'recalls, all years', 'bad' if c['recalls'] >= 8 else '')}{stat("Yes" if last["guzzler"] else "No", 'gas-guzzler tax')}</div>
<section class="yc"><h2>Every year. <span class="h2s">EPA numbers across the versions sold that year.</span></h2><div class="tw"><table><thead><tr><th>Year</th><th>MPG</th><th>Fuel / yr</th><th>Engine</th><th>Guzzler tax</th><th>Recalls</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="yc-cap">EPA yearly fuel cost assumes 15,000 miles at national average prices. The gas-guzzler tax is a federal tax paid on new cars that use a lot of fuel.</p></section>
{recs}
<p class="yc-cap" style="text-align:center">Sources: EPA fueleconomy.gov and NHTSA recalls. 0–60 and top-speed specs coming soon. <a href="/supercars/">Every supercar</a></p></div>'''
        page(f'/supercars/{slug}/', f'{c["name"]} MPG, Fuel Cost & Recalls by Year | The Lemon Index',
             f'{c["name"]} by model year ({ys[0]["y"]}-{last["y"]}): EPA {rng2(last["comb"])} mpg, up to ${last["cost"][1]:,} a year in fuel, {c["recalls"]} NHTSA recalls.', body,
             ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{c["name"]} fuel economy and recalls', "url": BASE + f'/supercars/{slug}/'}])
        surls.append(f'/supercars/{slug}/')
    mk = list(dict.fromkeys(c['make'] for c in sorted(SC, key=lambda c: c['make'])))
    groups = ''.join(f'<div class="mb"><h3>{E(m)}</h3><div class="mg">' + ''.join(card(f'/supercars/{c["slug"]}/', vph(c['name']), c['name'].replace(m, '').strip() or c['name'], f'{c["years"][-1]["comb"][0]} mpg', 'bad' if c['years'][-1]['comb'][0] <= 14 else '', f'{c["recalls"]} recalls') for c in [x for x in SC if x['make'] == m]) + '</div></div>' for m in mk)
    thirst = sorted(SC, key=lambda c: -c['years'][-1]['cost'][1])
    rec = sorted(SC, key=lambda c: -c['recalls'])
    page('/supercars/', 'Supercar MPG, Fuel Cost & Recalls: Ferrari, Lamborghini, McLaren | The Lemon Index',
         f'Fuel economy, yearly fuel cost and recalls for {len(SC)} supercars and luxury cars (Ferrari, Lamborghini, McLaren, Bugatti, Aston Martin, Rolls-Royce and more), every model year, from EPA and NHTSA.',
         f'''<div class="pg">{phero('Supercars', 'Supercars, by the numbers.', 'EPA fuel economy and NHTSA recalls for every model year. Corner number: combined mpg.', visual=pimg(vph('Lamborghini Huracán'), 'Lamborghini Huracán') if vph('Lamborghini Huracán') else '')}
<section class="tiles"><div class="tile"><div class="tt"><p class="te">Thirstiest</p><h2>{E(thirst[0]["name"])}.</h2><p class="ts">{thirst[0]["years"][-1]["comb"][0]} mpg combined. About ${thirst[0]["years"][-1]["cost"][1]:,} a year in fuel (EPA).</p></div></div>
<div class="tile"><div class="tt"><p class="te">Most recalls</p><h2>{E(rec[0]["name"])}.</h2><p class="ts">{rec[0]["recalls"]} NHTSA recalls across its model years.</p></div></div></section>
<section><h2>Every model. <span class="h2s">Tap one for every year: mpg, fuel cost, engine and recalls.</span></h2><div class="mbs">{groups}</div></section>
<section class="yc"><h2>Yearly fuel cost. <span class="h2s">Newest model year, EPA estimate, the thirstiest version.</span></h2>{bars_n([(c["name"], c["years"][-1]["cost"][1]) for c in thirst[:12]]).replace("</b>", "</b>").replace('<b>', '<b>$')}</section>
<section class="yc"><h2>Most recalls. <span class="h2s">NHTSA campaigns across all model years 2010–2025.</span></h2>{bars_n([(c["name"], c["recalls"]) for c in rec[:12]])}</section>
<p class="yc-cap" style="text-align:center">Owner complaints are too rare for supercars to score (Ferrari has about 70 in total), so this section shows EPA and recall data. Sources: EPA fueleconomy.gov, NHTSA.</p></div>''',
         ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Supercar fuel economy and recalls", "url": BASE + '/supercars/'}])
    surls.insert(0, '/supercars/')
print('supercar pages', len(surls))
