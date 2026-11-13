# Planes + motorcycles sections (11-04). Run by build.py with exec() (page, E, phero, pimg, pcredit, who, qa_fold, BASE in scope).
# data/planes.json (data_planes.py, NTSB) + data/moto.json (data_moto.py, NHTSA complaints) + photos in data/vehicle_photos.json (data_vehicle_photos.py).
VPH = _load('data/vehicle_photos.json') if os.path.exists('data/vehicle_photos.json') else {}
slugify = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower().replace("'", '')).strip('-')
# 11-10 (Elijah): our own AI illustrations (data/ai_vehicle_images.json, assets/ai-vehicles/, gpt-image-2, checked by hand) replace the
# Wikimedia photos. A family without one keeps its Commons photo and credit. The disclosure sits behind the small 'i' (assets/imginfo.js).
AIV = _load('data/ai_vehicle_images.json') if os.path.exists('data/ai_vehicle_images.json') else {}
def vph(name):
    a = AIV.get(name)
    if a: return {'src': a['src'], 'w': a['w'], 'h': a['h'], 'author': '', 'ai': f"{a['year']} {a['name']}", 'noun': a['noun']}
    return VPH.get(name)
def vnote(what, noun):
    return ('<span class="iiw">' + YSL.info(f'Illustration (AI-generated) of {E(what)}, not a photo of a specific {noun}. Free to use under '
            f'<a href="{YSL.LIC}" rel="license noopener">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>') + '</span>')
def vcredit(ph):
    """Under a hero image: the AI disclosure for our illustration, the Commons credit for a photo."""
    if not ph: return ''
    return f'<p class="ph-cr">Illustration{vnote("a " + ph["ai"], ph["noun"])}</p>' if ph.get('ai') else pcredit(who(ph))
def vgrid_note(names, plural, noun):
    """Under a grid of cards: one 'i' for the illustrations, plus the Commons credit for any photo still shown."""
    phs = [vph(n) for n in names]; ai = [p for p in phs if p and p.get('ai')]; wk = [p for p in phs if p and not p.get('ai')]
    bits = (['Images: AI-generated illustrations' + vnote(f'the {plural} on this page', noun)] if ai else []) + ([f'Photos: {E(" · ".join(dict.fromkeys(who(*wk))))} (Wikimedia Commons)'] if wk else [])
    return f'<p class="yc-cap" style="text-align:center">{" · ".join(bits)}</p>' if bits else ''
def valt(ph, name): return f'{name}, illustration' if ph and ph.get('ai') else name
def vld(ph, url):
    if not (ph and ph.get('ai')): return []
    return [{"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": BASE + ph['src'], "name": f'{ph["ai"]} (illustration)',
             "description": f'AI-generated illustration of a {ph["ai"]}.', "width": ph['w'], "height": ph['h'], "license": YSL.LIC, "acquireLicensePage": BASE + '/images/',
             "creditText": "The Lemon Index", "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE}, "copyrightNotice": "The Lemon Index, CC BY 4.0"}]
def bars_pct(rows, cls=''):
    mx = max([v for _, v in rows] + [1])
    return '<div class="pts">' + ''.join(f'<div class="pt"><span>{E(k)}</span><span class="bt"><i style="width:{v / mx * 100:.0f}%"></i></span><b>{v}%</b></div>' for k, v in rows) + '</div>'
def bars_n(rows):
    mx = max([v for _, v in rows] + [1])
    return '<div class="pts vyr">' + ''.join(f'<div class="pt"><span>{E(str(k))}</span><span class="bt"><i style="width:{v / mx * 100:.0f}%"></i></span><b>{v:,}</b></div>' for k, v in rows) + '</div>'
def hub_bars(rows, unit='', pre=''):
    """11-10 (Elijah: "this doesn't look good"): the hub ranking lists. A small AI cutout, the model on one line with the make under it,
    a light bar (red for the 3 highest, gray for the rest) and the number. Centered at 760 px; the label column never squeezes."""
    mx = max([v for _, v in rows] + [1]); hi = sorted((v for _, v in rows), reverse=True)[:3]
    out = []
    for k, v in rows:
        k = str(k); parts = k.split(' ', 1); make, model = (parts[0], parts[1]) if len(parts) == 2 else ('', k)
        ph = vph(k); im = f'<img src="{E(ph["src"])}" alt="" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async">' if ph else ''
        out.append(f'<div class="hb{" bad" if v in hi else ""}"><span class="hb-i">{im}</span><span class="hb-n"><b>{E(model)}</b><small>{E(make)}</small></span>'
                   f'<span class="hb-t"><i style="width:{v / mx * 100:.0f}%"></i></span><b class="hb-v">{pre}{v:,}{unit}</b></div>')
    return '<div class="hbl">' + ''.join(out) + '</div>'
def stat(n, lab, cls=''): return f'<div class="yt"><b class="yt-v {cls}">{n}</b><small>{lab}</small></div>'
def card(href, ph, name, big, cls, small=''):
    return (f'<a class="mc vmc" href="{href}"><span class="mc-p">{pimg(ph, valt(ph, name)) if ph else ""}</span><b>{E(name)}</b>'
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
<p class="ph-s">Every U.S. accident NTSB investigated, 2008 to 2025.</p><nav class="modes" aria-label="Page mode"><a href="/planes/{slug}/" aria-current="page">Normal</a><a href="/planes/{slug}/advanced/">Advanced</a></nav></div><div class="ph-v">{pimg(ph, valt(ph, p["name"])) if ph else ""}{vcredit(ph)}</div></section>
<div class="yts">{stat(f'{p["n"]:,}', 'accidents')}{stat(f'{p["fatal_pct"]}%', 'were fatal', 'bad' if p['fatal_pct'] >= 20 else '')}{stat(f'{p["deaths"]:,}', 'deaths')}{stat(f'{p["destroyed_pct"]}%', 'aircraft destroyed')}</div>{ytfix('plane:' + slug)}
<section class="yc"><h2>What happened. <span class="h2s">NTSB's defining event, share of accidents.</span></h2>{bars_pct(whatrows)}</section>
{mech}
<section class="yc"><h2>When. <span class="h2s">Phase of flight.</span></h2>{bars_pct(p["phase"])}</section>
<section class="yc"><h2>Accidents per year.</h2>{bars_n([(y, v) for y, v in p["by_year"].items()])}<p class="yc-cap">More planes flying means more accidents, so counts aren&#39;t a safety score by themselves. Compare the shares above.</p></section>
<p class="yc-cap" style="text-align:center">Source: {NTSB} <a href="https://www.ntsb.gov/Pages/investigations.aspx" rel="noopener">ntsb.gov</a> · <a href="/planes/">Every plane</a></p></div>'''
        page(f'/planes/{slug}/', f'{p["name"]} Accidents: What Happened, How Often Fatal | The Lemon Index',
             f'{p["n"]:,} U.S. {p["name"]} accidents NTSB investigated (2008-2025): {p["fatal_pct"]}% fatal, top event: {whatrows[0][0] if whatrows else "n/a"}. Plane-caused share, phase of flight and accidents per year.', body,
             ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{p["name"]} accidents', "url": BASE + f'/planes/{slug}/'}] + vld(ph, f'/planes/{slug}/'))
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
         f'''<div class="pg">{phero('Planes', 'Plane accidents, by model.', 'Every U.S. accident NTSB investigated, 2008 to 2025. Corner number: share that were fatal.', visual=pimg(vph('Cirrus SR22'), valt(vph('Cirrus SR22'), 'Cirrus SR22')) if vph('Cirrus SR22') else '', credit=vcredit(vph('Cirrus SR22')))}
<section class="tiles"><div class="tile"><div class="tt"><p class="te">When it crashes</p><h2>{E(fat[0]["name"])}.</h2><p class="ts">{fat[0]["fatal_pct"]}% of its accidents were fatal, the most of any common model.</p></div></div>
<div class="tile"><div class="tt"><p class="te">Airliners</p><h2>Mostly turbulence.</h2><p class="ts">About {turb}% of U.S. airliner accidents were turbulence encounters. Under 1 in 50 were fatal.</p></div></div></section>
<section><h2>Every model. <span class="h2s">Tap one for what happened, the phase of flight and the plane-vs-pilot split.</span></h2><div class="mbs">{groups}</div>{vgrid_note([p["name"] for p in PL], "planes and helicopters", "aircraft")}</section>
<section class="yc hbsec"><h2>When it crashes, how often is it fatal? <span class="h2s">Models with 80+ accidents.</span></h2>{hub_bars([(p["name"], p["fatal_pct"]) for p in fat[:12]], '%')}</section>
<section class="yc hbsec"><h2>How often is the plane to blame? <span class="h2s">Accidents where NTSB listed an engine, system, structure or propeller problem among the causes.</span></h2>{hub_bars([(p["name"], p["mech_pct"]) for p in mech[:12]], '%')}</section>
<p class="yc-cap" style="text-align:center">Counts follow fleet size (the Cessna 172 is the most common plane in the U.S.), so compare the shares, not the totals. Per-plane rates need the FAA registry; coming soon. Source: {NTSB}</p></div>''',
         ld=[{"@context": "https://schema.org", "@type": "Dataset", "name": "Plane accidents by model (NTSB, 2008-2025)", "url": BASE + '/planes/', "isBasedOn": "https://www.ntsb.gov/Pages/AviationQueryV2.aspx", "creator": {"@type": "Organization", "name": "The Lemon Index"}}])
    purls.insert(0, '/planes/')

# ---------------- motorcycles
MO = _load('data/moto.json') if os.path.exists('data/moto.json') else []
murls = []
if MO:
    for m in MO:
        slug = slugify(m['name']); m['slug'] = slug; ph = vph(m['name'])
        rc = ''.join(f'<li><b>{E((r["part"] or "").split(":")[0].title())}</b> <small>{E((r["date"] or "")[-4:] or (r["date"] or "")[:4])}</small><p>{E(rsum(r))}</p></li>' for r in m['recalls'][:3])
        more = ''.join(f'<li><b>{E((r["part"] or "").split(":")[0].title())}</b> <small>{E(r["id"])}</small><p>{E(rsum(r))}</p></li>' for r in m['recalls'][3:])
        recs = (f'<section class="yc" id="recalls"><h2>Recalls <span class="yc-n">{len(m["recalls"])}</span></h2>'
                + (f'<ul class="rc">{rc}</ul>' + (f'<details><summary>Show all {len(m["recalls"])}</summary><ul class="rc">{more}</ul></details>' if more else '') if m['recalls'] else '<p>No NHTSA recalls found for these model names.</p>')
                + '<p class="yc-cap">Recall repairs are free at any dealer. Check a specific bike&#39;s VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener">nhtsa.gov/recalls</a>.</p></section>')
        body = f'''<div class="pg mp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/motorcycles/">Motorcycles</a> · {E(m["brand"])} · {E(m["seg"])}</p><h1>{E(m["name"])}.</h1>
<p class="ph-s">Owner complaints to the U.S. government, {m["years"][0]} to {m["years"][1]} models.</p><nav class="modes" aria-label="Page mode"><a href="/motorcycles/{slug}/" aria-current="page">Normal</a><a href="/motorcycles/{slug}/advanced/">Advanced</a></nav></div><div class="ph-v">{pimg(ph, valt(ph, m["name"])) if ph else ""}{vcredit(ph)}</div></section>
<div class="yts">{stat(f'{m["n"]:,}', 'owner complaints')}{stat(f'{len(m["recalls"])}', 'recalls')}{stat(f'{m["serious"]}%', 'involved a crash, fire or injury', 'bad' if m['serious'] >= 25 else '')}{stat(f'{m["miles"]:,}' if m['miles'] else '—', 'typical miles at complaint')}</div>{ytfix('moto:' + slug)}
<section class="yc"><h2>What owners complain about. <span class="h2s">Share of complaints.</span></h2>{bars_pct(m["parts"])}</section>
{recs}
<section class="yc"><h2>Complaints by model year.</h2>{bars_n([(y, v) for y, v in m["by_year"].items()])}<p class="yc-cap">Popular years get more complaints just because more were sold. There are no free U.S. sales figures by motorcycle model, so these are counts, not rates.</p></section>
<p class="yc-cap" style="text-align:center">Filed as: {E(", ".join(m["names"][:5]))}. Source: NHTSA owner complaints and recalls. <a href="/motorcycles/">Every motorcycle</a></p></div>'''
        page(f'/motorcycles/{slug}/', f'{m["name"]} Problems & Recalls: Owner Complaints by Year | The Lemon Index',
             f'{m["n"]:,} NHTSA owner complaints about the {m["name"]} ({m["years"][0]}-{m["years"][1]}): top problem {m["parts"][0][0] if m["parts"] else "n/a"}, {len(m["recalls"])} recalls, {m["serious"]}% involved a crash, fire or injury.', body,
             ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{m["name"]} problems', "url": BASE + f'/motorcycles/{slug}/'}] + vld(ph, f'/motorcycles/{slug}/'))
        murls.append(f'/motorcycles/{slug}/')
    # 11-11: the next bikes (data/moto_soon.json, AI illustrations checked by hand): coming-soon cards, not links; no stub pages
    MS = _load('data/moto_soon.json') if os.path.exists('data/moto_soon.json') else []
    def mscard(s):
        nm = s['name'][len(s['make']) + 1:] if s['name'].startswith(s['make'] + ' ') else s['name']
        img = f'<img src="{s["img"]}" alt="{E(s["name"])}, illustration" width="{s["w"]}" height="{s["h"]}" loading="lazy">' if s.get('img') else ''
        return (f'<div class="mc vmc mc-nd" aria-disabled="true" title="Coming soon"><span class="mc-p">{img}</span><b>{E(nm)}</b>'
                f'<small class="mc-k">{E(s["engine"])}</small><span class="nd">Coming soon</span></div>')
    brands = list(dict.fromkeys(m['brand'] for m in sorted(MO, key=lambda m: -m['n']))) + sorted({s['make'] for s in MS} - {m['brand'] for m in MO})
    groups = ''.join(f'<div class="mb"><h3>{E(b)}</h3><div class="mg">' + ''.join(card(f'/motorcycles/{m["slug"]}/', vph(m['name']), m['name'].replace(b, '').strip() or m['name'], f'{len(m["recalls"])}', 'bad' if len(m['recalls']) >= 10 else 'good', f'{m["n"]:,} complaints') for m in sorted([m for m in MO if m['brand'] == b], key=lambda m: -m['n'])) + ''.join(mscard(s) for s in sorted([s for s in MS if s['make'] == b], key=lambda s: s['name'])) + '</div></div>' for b in brands)
    ser = sorted([m for m in MO if m['n'] >= 40], key=lambda m: -m['serious'])
    rec = sorted(MO, key=lambda m: -len(m['recalls']))
    page('/motorcycles/', 'Motorcycle Problems & Recalls by Model: Harley, Honda, Yamaha | The Lemon Index',
         f'Owner complaints and recalls for {len(MO)} popular motorcycles (Harley-Davidson, Honda, Yamaha, Kawasaki, Suzuki, BMW, Ducati and more), from NHTSA.',
         f'''<div class="pg">{phero('Motorcycles', 'Motorcycle problems, by model.', 'Owner complaints and recalls filed with the U.S. government. Corner number: recalls.', visual=pimg(vph('Harley-Davidson Touring'), valt(vph('Harley-Davidson Touring'), 'Harley-Davidson Touring')) if vph('Harley-Davidson Touring') else '', credit=vcredit(vph('Harley-Davidson Touring')))}
<section><h2>Every model. <span class="h2s">Tap one for its problems, recalls and complaints by year.{f' Cards marked Coming soon are next ({len(MS)} bikes).' if MS else ''}</span></h2><div class="mbs">{groups}</div>{vgrid_note([m["name"] for m in MO], "motorcycles", "motorcycle")}</section>
<section class="yc hbsec"><h2>Most recalls. <span class="h2s">NHTSA recall campaigns across the model years.</span></h2>{hub_bars([(m["name"], len(m["recalls"])) for m in rec[:10]])}</section>
<section class="yc hbsec"><h2>Most serious complaints. <span class="h2s">Share that involved a crash, fire or injury (models with 40+ complaints).</span></h2>{hub_bars([(m["name"], m["serious"]) for m in ser[:10]], '%')}</section>
<p class="yc-cap" style="text-align:center">There are no free U.S. sales figures by motorcycle model, so this section shows counts and shares, not a per-bike score like our cars. Source: NHTSA owner complaints and recalls.</p></div><script src="/assets/soonvote.js?v=2" defer></script>''',
         ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Motorcycle problems and recalls by model", "url": BASE + '/motorcycles/'}])
    murls.insert(0, '/motorcycles/')
print('planes pages', len(purls), 'moto pages', len(murls))

# ---------------- supercars (11-04): EPA fuel economy + NHTSA recalls per model year (data_supercars.py)
SC = _load('data/supercars.json') if os.path.exists('data/supercars.json') else []
surls = []
rng2 = lambda a, pre='', suf='': f'{pre}{a[0]:,}{suf}' if a[0] == a[1] else f'{pre}{a[0]:,}–{a[1]:,}{suf}'
_SCE = _load('data/supercar_engines.json') if os.path.exists('data/supercar_engines.json') else {'engines': {}, 'cars': {}}   # 11-11 supercar engine pages
_SCEU = lambda e: '/engines/' + {'rr-n73': 'rolls-royce-n73', 'rr-n74': 'rolls-royce-n74'}.get(e, e) + '/'
def _sce_links(slug, y):
    es = [e for e, yl in (_SCE['cars'].get(slug) or {}).items() if y in yl]
    return ''.join(f' · <a href="{_SCEU(e)}">{E(_SCE["engines"][e]["code"])}</a>' for e in es)
# 11-12 (Elijah on the NSX: the engine was a bare text link and the Specs tab looked empty): every engine is an image card that links to its
# page (no confirmed engine yet = the same card, muted, "Coming soon"), and the tab opens with spec cards in the M3 page's style, built only
# from data we hold: factory hp from each engine's sources, EPA versions, drive and mpg. No 0-60 / top speed / weight until a tested source exists.
_SCP = _load('data/supercar_engine_photos.json') if os.path.exists('data/supercar_engine_photos.json') else {}
_yr = lambda ys: f'{min(ys)}' + (f'–{max(ys)}' if max(ys) != min(ys) else '')
_DRVM = {'all-wheel drive': 'AWD', 'rear-wheel drive': 'RWD', 'front-wheel drive': 'FWD', '4-wheel drive': '4WD', 'part-time 4-wheel drive': '4WD'}
_DRV = lambda d: _DRVM.get(d.strip().lower(), d.strip())
_EIC = ('<svg aria-hidden="true" viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 10h2V8h3V6h6v2h2l2 3h1v5h-1l-2 3h-6l-2-2H9v-3H6v2H4z"/></svg>')
def _ecard(href, name, spec, years, ph=None, soon=False):
    """One engine card: illustration (640 px copy, lazy), name, spec line, years. The whole card links to the engine page; soon = muted, no link."""
    im = ''
    if ph:
        th = ph['src'][:-5] + '-640.webp'
        src, w, h = (th, 640, round(ph['h'] * 640 / ph['w'])) if os.path.exists(th.lstrip('/')) else (ph['src'], ph['w'], ph['h'])
        alt = re.sub(r'\s*\(illustration\)$', '', html.unescape(ph.get('title') or name)) + ', illustration'
        im = f'<img src="{E(src)}" alt="{E(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async">'
    inner = (f'<span class="ecard-i{"" if im else " ecard-ni"}">{im or (_EIC + ("" if soon else _ENI))}</span><span class="ecard-t"><b>{E(name)}</b><small>{E(spec)}</small>'
             f'<small class="ecard-y">{E(years)}</small>' + ('<span class="ecard-s">Coming soon</span>' if soon else '') + '</span>')
    return f'<div class="ecard ecard-soon" aria-disabled="true">{inner}</div>' if soon else f'<a class="ecard" href="{E(href)}">{inner}</a>'
def _sce_map(slug, c):
    """[(engine id or None, years)] for the car, oldest first; None = model years with a version no source ties to an engine yet"""
    es = sorted((_SCE['cars'].get(slug) or {}).items(), key=lambda kv: min(kv[1]))
    cov = {y for _, yl in es for y in yl}
    un = sorted(y['y'] for y in c['years'] if y['y'] not in cov)
    return es + ([(None, un)] if un else [])
_ENI = '<span class="ecard-nt">No illustration yet</span>'
def _sce_section(slug, name, c):
    es = _sce_map(slug, c)
    if not es: return ''
    cards = []
    for e, yl in sorted(es, key=lambda kv: (kv[0] is not None, max(kv[1])), reverse=True):   # newest first, like the spec cards; unconfirmed last
        if e is None:   # EPA's own engine line for the years no source ties to an engine
            ys = [y for y in c['years'] if y['y'] in yl]; t = sorted({t for y in ys for t in y['engines']})
            cards.append(_ecard('', ', '.join(t).replace('-cyl', '-cylinder') + (' hybrid' if any(y['hybrid'] for y in ys) else ''), 'Engine not confirmed by a source yet', _yr(yl), soon=True)); continue
        d = _SCE['engines'][e]
        cards.append(_ecard(_SCEU(e), html.unescape(d['name']), html.unescape(f'{d["size"]} {d["layout"]} {d["asp"]}'), _yr(yl), _SCP.get(e)))
    n = sum(1 for e, _ in es if e)
    return (f'<section class="yc" id="engines"><h2>Engines <span class="h2s">{n} engine{"" if n == 1 else "s"} in the {E(name)}. Tap one for its YouTube score by year, recalls and repair notes.</span></h2>'
            f'<div class="ecards">{"".join(cards)}</div><p><a class="btn" href="/engines/supercars/">Every supercar engine →</a></p></section>')
def _scs_specs(slug, c):
    """Spec cards, one per engine era of this car (the M3 page's look): factory hp, engine, drive, EPA mpg, where it's built.
    Returns (html, hero tiles). Drive and mpg only come from model years with one engine, so a card never shows another engine's numbers."""
    es = _sce_map(slug, c); Y = {y['y']: y for y in c['years']}; srcs = {}
    unc = set(_SCE.get('unconfirmed') or [])   # a covered year that also has an unconfirmed version counts as two engines
    per = {y: sum(1 for _, yl in es if y in yl) + (1 if f'{c["name"]} {y}' in unc and any(y in yl for e, yl in es if e) else 0) for y in Y}
    cards = []
    for e, yl in es:
        d = _SCE['engines'][e] if e else None
        names = {}
        for y in yl:
            for v in (((d['years'].get(str(y)) or {}).get('cars') or {}).get(slug, []) if d else Y[y]['names']): names[v.lower()] = v
        nm = list(names.values()); title = (' · '.join(nm[:3]) + (f' +{len(nm) - 3} more' if len(nm) > 3 else '')) if nm else c['name']
        one = [Y[y] for y in yl if per.get(y) == 1 and y in Y]
        rows = []
        if d: rows.append(('Engine', f'<a href="{_SCEU(e)}">{E(html.unescape(d["name"]))}</a>', html.unescape(f'{d["size"]} {d["layout"]} {d["asp"]}')))
        else: rows.append(('Engine', E(', '.join(sorted({t.replace('-cyl', '-cylinder') for y in yl for t in Y[y]['engines']}))), 'EPA listing; no source names the engine yet'))
        drv = sorted({_DRV(x) for y in one for x in y.get('drive') or []})
        if drv: rows.append(('Drive', E(' or '.join(drv)), 'EPA'))
        if one:
            rg = lambda k: (min(y[k][0] for y in one), max(y[k][1] for y in one)) if all(y.get(k) for y in one) else None
            ct, hw = rg('city'), rg('hwy')
            rows.append(('Fuel economy', f'{rng2(rg("comb"))} mpg combined', f'{rng2(ct)} city · {rng2(hw)} highway (EPA)' if ct and hw else 'EPA'))
        if d and d.get('made'): rows.append(('Built', E(html.unescape(d['made'])[:1].upper() + html.unescape(d['made'])[1:]), ''))
        big = ''
        if d and d.get('hp'):
            solo = all(x['slug'] == slug and not x.get('perf') for x in d['cars'])
            pl = 's' if d['hp'][0] != d['hp'][1] else ''
            note = '; '.join(x for x in ((html.unescape(d['hp_note']) if d.get('hp_note') else ''), ('' if solo else f'range across every car with the {html.unescape(d["code"])}')) if x)
            big = f'<p class="scs-hp"><b>{rng2(d["hp"])}</b> hp<small>Factory figure{pl}' + (f', {E(note)}' if note else '') + '</small></p>'
            for s in d.get('src') or []: srcs.setdefault(s['url'], s['title'])
        dl = ''.join(f'<div class="scs-r"><dt>{k}</dt><dd>{v}' + (f'<small>{E(n)}</small>' if n else '') + '</dd></div>' for k, v, n in rows)
        cards.append(((d is not None, max(yl)), f'<article class="scs-c{"" if d else " scs-nc"}"><header><h3>{E(title)}</h3><span>{_yr(yl)}</span></header>{big}<dl>{dl}</dl></article>'))
    cards = [h for _, h in sorted(cards, key=lambda x: x[0], reverse=True)]   # confirmed engines first, newest first like the year table
    srcs['https://www.fueleconomy.gov/'] = 'EPA fueleconomy.gov: versions, drive and mpg'
    fold = '<details class="scs-src"><summary>Sources</summary><ol>' + ''.join(f'<li><a href="{E(u)}" rel="noopener">{E(t)}</a></li>' for u, t in srcs.items()) + '</ol></details>'
    body = (f'<section class="yc scs" id="specs"><h2>Specs <span class="h2s">Factory power from each engine&#39;s sources, everything else from the EPA.</span></h2>'
            f'<div class="scs-g">{"".join(cards)}</div><p class="scs-soon">0–60 and top speed: coming soon. We only show times from a published test.</p>{fold}</section>')
    # hero tiles: lead with power and the engine (11-11 lemon-performance-section), from the newest engine era
    last = next((e for e, yl in sorted(es, key=lambda kv: -max(kv[1])) if e), None)
    tiles = []
    if last:
        d = _SCE['engines'][last]; solo = all(x['slug'] == slug and not x.get('perf') for x in d['cars'])
        if d.get('hp') and solo: tiles.append((f'{d["hp"][1]:,} hp', f'factory, {d["hp"][0]:,} to {d["hp"][1]:,}' if d['hp'][0] != d['hp'][1] else 'factory figure'))
        size = re.sub(r'\s*\(.*?\)', '', d['size'])
        tiles.append((html.unescape(re.sub(r'^\d+°\s*', '', d['layout'].split(',')[0])), html.unescape(f'{size} {d["asp"]} · {d["code"]}')))
    return body, tiles
if SC:
    for c in SC:
        slug = slugify(c['name']); c['slug'] = slug; ph = vph(c['name']); ys = c['years']; last = ys[-1]
        rows = ''.join(f'<tr><td><b>{y["y"]}</b></td><td class="num">{rng2(y["comb"])}</td><td class="num">{rng2(y["cost"], "$")}</td><td>{E(", ".join(y["engines"][:2]))}{" · hybrid" if y["hybrid"] else ""}{_sce_links(slug, y["y"])}</td>'
                       f'<td>{"Yes" if y["guzzler"] else "—"}</td><td class="num">{len(y["recalls"])}</td></tr>' for y in reversed(ys))
        allrec = sorted({r['id']: dict(r, y=y['y']) for y in ys for r in y['recalls']}.values(), key=lambda r: r['date'][-4:] if r['date'] else '', reverse=True)
        rc = ''.join(f'<li><b>{E((r["part"] or "").split(":")[0].title())}</b> <small>{r["y"]} model · {E(r["id"])}</small><p>{E(rsum(r))}</p></li>' for r in allrec[:4])
        more = ''.join(f'<li><b>{E((r["part"] or "").split(":")[0].title())}</b> <small>{r["y"]} model · {E(r["id"])}</small><p>{E(rsum(r))}</p></li>' for r in allrec[4:])
        recs = (f'<section class="yc" id="recalls"><h2>Recalls <span class="yc-n">{len(allrec)}</span></h2>' + (f'<ul class="rc">{rc}</ul>' + (f'<details><summary>Show all {len(allrec)}</summary><ul class="rc">{more}</ul></details>' if more else '') if allrec else '<p>No NHTSA recalls on record for these model years.</p>')
                + '<p class="yc-cap">Recall repairs are free at any dealer. Check a specific car&#39;s VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener">nhtsa.gov/recalls</a> or with our <a href="/vin/">VIN check</a>.</p></section>')
        specs, tiles = _scs_specs(slug, c)
        tl = [stat(E(v), E(s)) for v, s in tiles] + [stat(rng2(last["comb"], "", " mpg"), f'combined, {last["y"]} (EPA)'), stat(str(c["recalls"]), 'recalls, all years', 'bad' if c['recalls'] >= 8 else ''),
                                                    stat(rng2(last["cost"], "$"), f'fuel a year, {last["y"]} (EPA)', 'bad' if last['cost'][1] >= 5000 else '')]
        body = f'''<div class="pg mp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/supercars/">Supercars</a> · {E(c["make"])}</p><h1>{E(c["name"])}.</h1>
<p class="ph-s">Power, engine, fuel economy and recalls, {ys[0]["y"]} to {last["y"]}.</p></div><div class="ph-v">{pimg(ph, valt(ph, c["name"])) if ph else ""}{vcredit(ph)}</div></section>
<div class="yts">{"".join(tl[:3])}</div>{ytfix('super:' + slug)}
<section class="yc"><h2>Every year. <span class="h2s">EPA numbers across the versions sold that year.</span></h2><div class="tw"><table><thead><tr><th>Year</th><th>MPG</th><th>Fuel / yr</th><th>Engine</th><th>Guzzler tax</th><th>Recalls</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="yc-cap">EPA yearly fuel cost assumes 15,000 miles at national average prices. The gas-guzzler tax is a federal tax paid on new cars that use a lot of fuel.</p></section>
{specs}{_sce_section(slug, c["name"], c)}{recs}
<p class="yc-cap" style="text-align:center">Sources: EPA fueleconomy.gov, NHTSA recalls and each engine&#39;s sources (Specs tab). <a href="/supercars/">Every supercar</a></p></div>'''
        page(f'/supercars/{slug}/', f'{c["name"]} MPG, Fuel Cost & Recalls by Year | The Lemon Index',
             f'{c["name"]} by model year ({ys[0]["y"]}-{last["y"]}): EPA {rng2(last["comb"])} mpg, up to ${last["cost"][1]:,} a year in fuel, {c["recalls"]} NHTSA recalls.', body,
             ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{c["name"]} fuel economy and recalls', "url": BASE + f'/supercars/{slug}/'}] + vld(ph, f'/supercars/{slug}/'))
        surls.append(f'/supercars/{slug}/')
    mk = list(dict.fromkeys(c['make'] for c in sorted(SC, key=lambda c: c['make'])))
    groups = ''.join(f'<div class="mb"><h3>{E(m)}</h3><div class="mg">' + ''.join(card(f'/supercars/{c["slug"]}/', vph(c['name']), c['name'].replace(m, '').strip() or c['name'], f'{c["years"][-1]["comb"][0]} mpg', 'bad' if c['years'][-1]['comb'][0] <= 14 else '', f'{c["recalls"]} recalls') for c in [x for x in SC if x['make'] == m]) + '</div></div>' for m in mk)
    thirst = sorted(SC, key=lambda c: -c['years'][-1]['cost'][1])
    rec = sorted(SC, key=lambda c: -c['recalls'])
    page('/supercars/', 'Supercar MPG, Fuel Cost & Recalls: Ferrari, Lamborghini, McLaren | The Lemon Index',
         f'Fuel economy, yearly fuel cost and recalls for {len(SC)} supercars and luxury cars (Ferrari, Lamborghini, McLaren, Bugatti, Aston Martin, Rolls-Royce and more), every model year, from EPA and NHTSA.',
         f'''<div class="pg">{phero('Supercars', 'Supercars, by the numbers.', 'EPA fuel economy and NHTSA recalls for every model year. Corner number: combined mpg.', visual=pimg(vph('Lamborghini Huracán'), valt(vph('Lamborghini Huracán'), 'Lamborghini Huracán')) if vph('Lamborghini Huracán') else '', credit=vcredit(vph('Lamborghini Huracán')))}
<p class="ctn"><a class="ctn-b" href="/cars/?type=supercars">See them with every other car</a></p>
<section class="tiles"><div class="tile"><div class="tt"><p class="te">Thirstiest</p><h2>{E(thirst[0]["name"])}.</h2><p class="ts">{thirst[0]["years"][-1]["comb"][0]} mpg combined. About ${thirst[0]["years"][-1]["cost"][1]:,} a year in fuel (EPA).</p></div></div>
<div class="tile"><div class="tt"><p class="te">Most recalls</p><h2>{E(rec[0]["name"])}.</h2><p class="ts">{rec[0]["recalls"]} NHTSA recalls across its model years.</p></div></div></section>
<section><h2>Every model. <span class="h2s">Tap one for every year: mpg, fuel cost, engine and recalls.</span></h2><div class="mbs">{groups}</div>{vgrid_note([c["name"] for c in SC], "cars", "car")}</section>
{f'<section class="yc"><h2>Supercar engines. <span class="h2s">{sum(1 for d in _SCE["engines"].values() if d.get("group", "super") == "super")} engines, from the Ferrari F154 to the Bugatti W16: YouTube score by year, recalls and repair notes.</span></h2><p><a class="btn" href="/engines/supercars/">Every supercar engine →</a></p></section>' if _SCE["engines"] else ''}
<section class="yc hbsec"><h2>Yearly fuel cost. <span class="h2s">Newest model year, EPA estimate, the thirstiest version.</span></h2>{hub_bars([(c["name"], c["years"][-1]["cost"][1]) for c in thirst[:12]], pre='$')}</section>
<section class="yc hbsec"><h2>Most recalls. <span class="h2s">NHTSA campaigns across all model years 2010–2025.</span></h2>{hub_bars([(c["name"], c["recalls"]) for c in rec[:12]])}</section>
<p class="yc-cap" style="text-align:center">Owner complaints are too rare for supercars to score (Ferrari has about 70 in total), so this section shows EPA and recall data. Sources: EPA fueleconomy.gov, NHTSA.</p></div>''',
         ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Supercar fuel economy and recalls", "url": BASE + '/supercars/'}])
    surls.insert(0, '/supercars/')
print('supercar pages', len(surls))
