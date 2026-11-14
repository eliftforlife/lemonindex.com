# Brand pages (11-03, Elijah: "start brand pages and make sure they look good like the rest of the website"). Run by build.py with exec(),
# so page(), E, plain, gauge, verdict, CARS, YEARS, mphoto, pimg, who, pcredit, BRANDS ... are in scope.
#   /brands/            every brand, best to worst, as photo cards
#   /brands/<brand>/    the brand's score, its models ranked as photo cards, its best and worst model, and (Ford, GM, Tesla) what the company
#                       itself reports spending on warranty repairs and recalls per vehicle sold (SEC annual reports, 10-K).
def _verdict(li):   # build.py's verdict() name gets reused as a string by the compare pages, so a local copy
    return ('good', 'One of the most reliable') if li < 50 else ('good', 'Better than average') if li < 85 else ('mid', 'About average') if li <= 115 else ('bad', 'Worse than average') if li < 200 else ('bad', 'Avoid')
BSLUG = lambda b: b.lower().replace(' ', '-')
# Warranty and recall cost booked each year (warranties issued + changes to earlier estimates, $ millions) / vehicles sold (thousands).
# Ford: 10-K FY2025 Note 24 + "Wholesales ... Total Company"; GM: 10-K FY2025 product warranty table + wholesale vehicle sales; Tesla: 10-K FY2025 accrued
# warranty table + "delivered approximately" (FY2024/FY2025 10-Ks). Read 11-03 from sec.gov.
WARR = {
 'Ford': dict(co='Ford Motor Company', short='Ford', note='Ford and Lincoln, worldwide. Ford reports it net of what suppliers pay back.',
              src='https://www.sec.gov/Archives/edgar/data/37996/000003799626000015/f-20251231.htm', yrs={2023: (7391, 4413), 2024: (8984, 4470), 2025: (8973, 4395)}),
 'GM': dict(co='General Motors', short='GM', note='GM reports Chevrolet, GMC, Buick and Cadillac together, worldwide wholesale sales.',
            src='https://www.sec.gov/Archives/edgar/data/1467858/000146785826000013/gm-20251231.htm', yrs={2023: (4744, 3768), 2024: (5855, 4010), 2025: (8320, 3799)}),
 'Tesla': dict(co='Tesla', short='Tesla', note='Worldwide consumer vehicle deliveries.',
               src='https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm', yrs={2024: (3017, 1789), 2025: (3614, 1640)}),
}
WBRAND = {'Ford': 'Ford', 'Chevrolet': 'GM', 'GMC': 'GM', 'Tesla': 'Tesla'}
per = lambda c, u: round(c * 1e6 / (u * 1e3))
def warranty_html(b):
    k = WBRAND.get(b)
    if not k: return ''
    w = WARR[k]; ys = sorted(w['yrs']); vals = [(y, per(*w['yrs'][y])) for y in ys]; last, first = vals[-1], vals[0]
    ch = round((last[1] / first[1] - 1) * 100); mx = max(v for _, v in vals)
    bars = ''.join(f'<div class="wr"><span>{y}</span><span class="wb"><i style="width:{v / mx * 100:.0f}%"></i></span><b>${v:,}</b></div>' for y, v in vals)
    return (f'<section class="bwar"><p class="te">What {E(w["short"])} told its investors</p><h2>${last[1]:,} <span class="h2s">in warranty and recall costs for every vehicle {E(w["short"])} sold in {last[0]}.</span></h2>'
            f'<div class="wrs">{bars}</div><p class="wch {"bad" if ch > 0 else "good"}">{"Up" if ch > 0 else "Down"} {abs(ch)}% since {first[0]}.</p>'
            f'<p class="yc-cap">What the company booked each year for repairs under warranty and recalls, divided by the vehicles it sold. {E(w["note"])} '
            f'From {E(w["co"])}&#39;s annual report to the SEC (<a href="{w["src"]}" rel="noopener">10-K</a>). It&#39;s money the company expects to spend, not a repair bill for you.</p></section>')

# 11-13 (nav review #5, Elijah: "fix all these"): a brand page lists EVERY model we cover, not only the study's 131 (the Toyota page showed 9 and
# missed the Prius, Sequoia, Yaris and FJ; Lexus showed 2 of 7), plus an "Also on Lemon Index" block (performance, EV, supercar and motorcycle
# pages), and every make gets a page (Cadillac, Buick, Lincoln, Volvo were 404s). The brand score itself is still the study's (data/brand_rates.csv).
#   ranked:     study models + the models added later (CARS_NEW), scored the same way from their own model years
#   complaints: models with complaint records but no sales figures (a "Complaints only" card, its own page)
#   also:       the make's performance / EV / supercar cards from the /cars/ grid (_xb), and its motorcycles
#   not yet:    "No data yet" models, as plain names
# Thin pages: a make with no brand score, under 2 scored models and under 3 pages to send people to is noindex,follow and out of the sitemap.
brank = {n.rstrip('*'): (i + 1, li) for i, (n, li) in enumerate(BRANDS)}
burls = []
cards = []
BNAME = {'Ssc': 'SSC'}   # makes the data spells in caps
_eff_dup = lambda m: m['slug'] in _DUP and _DUP[m['slug']] in _ID   # the same model under another name: already on the page
def _bmc(c):
    p = aph(c['id']); href = car_href(c['id'])   # 11-12: /cars/ page, else the EV page, else no link (was a 404 for the Porsche Cayenne)
    tag = f'a class="mc" href="{href}"' if href else 'div class="mc"'
    w = f'<small class="mc-k">{YRS(c)} score</small>' if c['id'] in EVBY else ''   # 11-12 (Priya): an EV's main score, labelled with its window (its EV page uses another)
    return (f'<{tag} title="Lemon Index, model years {YRS(c)}"><span class="mc-p">{pimg(p, c["name"]) if p else ""}</span><b>{E(c["name"].split(" ", 1)[1] if " " in c["name"] else c["name"])}</b>{w}'
            f'<span class="{"good" if c["li"] < 100 else "bad"}">{c["li"]}</span></{tag.split()[0]}>')
def _bdata(b):
    ms = sorted([c for c in CARS + CARS_NEW if c['brand'] == b], key=lambda c: c['li'])
    nd = [m for m in _nd.get(b, []) if not _eff_dup(m)]
    co = sorted([m for m in nd if m['slug'] in _EXN], key=lambda m: m['name']); soon = sorted(m['name'] for m in nd if m['slug'] not in _EXN)
    xs = sorted(_xb.get(b, []), key=lambda x: ({'p': 0, 'e': 1, 's': 2}.get((re.search(r'data-t="(\w)', x[1]) or [0, 'z'])[1], 3), x[0]))
    live = [h for _, h in xs if 'mc-dup' not in h and 'mc-nd' not in h]; later = [n for n, h in xs if 'mc-nd' in h]
    moto = [(x[0], x[3]) for x in PICK_ALL.get(b, []) if len(x) > 4 and x[4] == 'moto' and x[3]]
    return ms, co, soon, live, later, moto
def _short_nm(n, b): return n[len(b) + 1:] if n.startswith(b + ' ') else n
BN4_CSS = ('<style>.bn4 section > .yc-cap,.bn4 .bn4-soon,.bn4 .bn4-moto{text-align:center;max-width:640px;margin-left:auto;margin-right:auto}'
           '.bn4-h .ybw{text-align:center}.bn4-moto{margin-top:18px;font-size:15px;line-height:1.7}</style>')
def _brand_lists(b, ms, co, soon, live, later, moto, study_ids):
    out = BN4_CSS
    if ms:
        added = [c for c in ms if c['id'] not in study_ids]
        note = ''
        if b in brank and added:
            note = (f'<p class="yc-cap">The brand score counts the {len(ms) - len(added)} {E(b)} model{"s" * (len(ms) - len(added) != 1)} in our 2010–2022 study. '
                    f'{E(", ".join(_short_nm(c["name"], b) for c in added))} {"were" if len(added) > 1 else "was"} added later: scored the same way, from {"their" if len(added) > 1 else "its"} own model years, but not part of the brand score.</p>')
        elif added and b not in brank:
            note = f'<p class="yc-cap">Each score covers that model&#39;s own model years. {E(b)} wasn&#39;t one of the 22 brands in our 2010–2022 study, so it has no brand score.</p>'
        if any(c['id'] in EVBY for c in ms):
            note += f'<p class="yc-cap">The <a href="/electric/">EV ranking</a> scores model years {EV_WIN} with complaints filed by the end of the next year, so an EV&#39;s number there differs.</p>'
        out += (f'<section><h2>Every {E(b)}, ranked. <span class="h2s">Lower is better. 100 is the average car.</span></h2>'
                f'<div class="mbs"><div class="mb"><div class="mg">{"".join(_bmc(c) for c in ms)}</div></div></div>{note}</section>')
    if co:
        out += (f'<section><h2>{"More " if ms else ""}{E(b)} models with owner complaints. <span class="h2s">No score: we don&#39;t have their U.S. sales by year, so each page shows the complaints and recalls.</span></h2>'
                f'<div class="mbs"><div class="mb"><div class="mg">{"".join(ndcard(m) for m in co)}</div></div></div></section>')
    if live or moto:
        mo = (f'<p class="bn4-moto"><b>{E(b)} motorcycles:</b> ' + ' · '.join(f'<a href="{E(u)}">{E(_short_nm(n, b))}</a>' for n, u in moto) + '</p>') if moto else ''
        out += (f'<section class="bn4-also"><h2>Also on Lemon Index. <span class="h2s">{E(b)} performance, electric and supercar pages.</span></h2>'
                + (f'<div class="mbs"><div class="mb"><div class="mg">{"".join(live)}</div></div></div>' if live else '') + mo
                + (f'<p class="yc-cap">Coming soon: {E(", ".join(_short_nm(n, b) for n in later))}.</p>' if later else '') + '</section>')
    elif later:
        out += f'<section class="bn4-also"><h2>Coming soon.</h2><p class="yc-cap">{E(", ".join(_short_nm(n, b) for n in later))}.</p></section>'
    if soon:
        out += f'<p class="yc-cap bn4-soon">No data yet: {E(", ".join(_short_nm(n, b) for n in soon))}. These get a page once we have their complaint records.</p>'
    return out
def _best_tiles(b, ms):
    if len(ms) < 2: return ''
    best, worst = ms[0], ms[-1]
    return (f'<section class="tiles">'
        + ''.join(f'<a class="tile" href="/cars/{c["id"]}/"><div class="tt"><p class="te">{lab}</p><h2>{E(c["name"].split(" ", 1)[-1])}.</h2><p class="ts">{E(plain(c["li"]))}.</p>'
                  f'<span class="tl">See every year <i>›</i></span></div><div class="tp">{pimg(aph(c["id"]), c["name"])}<span class="tsc {"good" if c["li"] < 100 else "bad"}">{c["li"]}</span></div></a>'
                  for lab, c in ((f'Most reliable {E(b)}', best), (f'Least reliable {E(b)}', worst)) if c['id'] in FY) + '</section>')
_STUDY = {c['id'] for c in CARS}
for b, (rk, li) in brank.items():
    ms, co, soon, live, later, moto = _bdata(b)
    study = [c for c in ms if c['id'] in _STUDY]
    if not study: continue
    top = max(study, key=lambda c: c['sold']); ph = aph(top['id'])   # 11-10 (Elijah: 'update brands car images'): AI illustrations first, Commons only where none
    cls, word = _verdict(li); est = b in ('Tesla', 'Porsche')
    best, worst = ms[0], ms[-1]
    body = f'''<div class="pg mp6 bn4"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/brands/">Brands</a> · #{rk} of {len(brank)} brands with enough data</p><h1>{E(b)}.</h1>
<p class="ph-s">Every {E(b)} model, ranked by owner complaints per car sold.</p>
<div class="yhero">{gauge(li, 190)}<div class="yverd {cls}"><p><b>{word}.</b> <span>{E(b)} models in our 2010–2022 study{"" if plain(li).lower() in word.lower() else ": " + E(plain(li))}.</span></p>
<p class="ybw">Best <a class="good" href="{car_href(best["id"]) or "/brands/"}">{E(best["name"])}</a>{f' · Worst <a class="bad" href="{car_href(worst["id"]) or "/brands/"}">{E(worst["name"])}</a>' if worst is not best else ''}</p></div></div></div>
<div class="ph-v">{YSL.model_hero_html(top['id'], top['name']) if ph and ph.get('ai') else pimg(ph, top["name"]) + pcredit(who(ph))}</div></section>
{warranty_html(b)}
{_brand_lists(b, ms, co, soon, live, later, moto, _STUDY)}
{_best_tiles(b, ms)}
<p class="yc-cap" style="text-align:center">{"* Small sample or estimated sales. " if est else ""}{WHAT_LI} <a href="/method/">How it works</a> · <a href="/brands/">Every brand</a>{pcredit([x for c in ms for x in who(aph(c["id"]))]).replace('<p class="ph-cr">', ' ').replace('</p>', '')}</p>
{share_line(f'Is {b} reliable? Every {b} model ranked by owner complaints. Best: {best["name"]}. Worst: {worst["name"]}. Free:' if worst is not best else f'Is {b} reliable? Every {b} model ranked by owner complaints. Free:', f'Know someone looking at a {E(b)}?')}</div>'''
    page(f'/brands/{BSLUG(b)}/', f'Is {b} Reliable? Every {b} Model Ranked by Owner Complaints | The Lemon Index',
         f'{b} ranks #{rk} of {len(brank)} brands by NHTSA owner complaints per car sold (Lemon Index {li}; 100 is average). Most reliable {b}: {best["name"]}. Least: {worst["name"]}.',
         body, ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{b} reliability', "url": BASE + f'/brands/{BSLUG(b)}/'}])
    burls.append(f'/brands/{BSLUG(b)}/')
    cards.append(f'<a class="mc bc" href="/brands/{BSLUG(b)}/"><span class="mc-p">{pimg(ph, top["name"]) if ph else ""}</span><b>{E(b)}</b><small>#{rk}</small>'
                 f'<span class="{"good" if li < 100 else "bad"}">{li}</span></a>')
# 11-13: every other make (no brand score): its models, scored where we can, and its other pages
_SCORED_B = {u.split('/')[2] for u in burls}
_MAKES = sorted((set(c['brand'] for c in CARS + CARS_NEW) | set(_nd) | set(_xb)) - {'Pontiac'})   # Pontiac: extra_pages.py builds its own page
_more, _noix = [], []
for b in _MAKES:
    if BSLUG(b) in _SCORED_B: continue
    ms, co, soon, live, later, moto = _bdata(b)
    npg = len(ms) + len(co) + len(live) + len(moto)
    if not (npg or later or soon): continue
    bn = BNAME.get(b, b); path = f'/brands/{BSLUG(b)}/'
    thin = npg < 3 and len(ms) < 2   # 2+ scored models (Volvo: XC90, S60) is a real ranking
    best, worst = (ms[0], ms[-1]) if ms else (None, None)
    top = max(ms, key=lambda c: c['sold']) if ms else None; ph = aph(top['id']) if top else None
    bw = (f'<p class="ybw">Best <a class="good" href="{car_href(best["id"]) or path}">{E(best["name"])}</a> {best["li"]}'
          + (f' · Worst <a class="bad" href="{car_href(worst["id"]) or path}">{E(worst["name"])}</a> {worst["li"]}' if worst is not best else '') + '</p>') if ms else ''
    _k = [w for t, w in (('p', 'performance'), ('e', 'electric'), ('s', 'supercar')) if any(f'data-t="{t}' in h for h in live)] + (['motorcycle'] if moto else [])
    parts = [f'{len(ms)} with a Lemon Index' if ms else '', f'{len(co)} with owner complaints' if co else '',
             f'{len(live) + len(moto)} {" and ".join(_k) if len(_k) < 3 else ", ".join(_k[:-1]) + " and " + _k[-1]} page{"s" * (len(live) + len(moto) != 1)}' if live or moto else '']
    parts = [p for p in parts if p]
    sub = (f'Every {E(bn)} model we track: ' + ', '.join(parts) + '.') if parts else f'The {E(bn)} models we track. Pages are on the way.'
    vis = (YSL.model_hero_html(top['id'], top['name']) if ph and ph.get('ai') else pimg(ph, top['name']) + pcredit(who(ph))) if ph else ''
    body = (f'<div class="pg mp6 bn4"><section class="ph yph6 bn4-h"><div class="yh-t"><p class="ph-e"><a href="/brands/">Brands</a> · No brand score</p><h1>{E(bn)}.</h1>'
            f'<p class="ph-s">{sub}</p>{bw}</div>' + (f'<div class="ph-v">{vis}</div>' if vis else '') + '</section>'
            + _brand_lists(bn, ms, co, soon, live, later, moto, _STUDY) + _best_tiles(bn, ms)
            + f'<p class="yc-cap" style="text-align:center">{WHAT_LI} <a href="/method/">How it works</a> · <a href="/brands/">Every brand</a></p>'
            + (share_line(f'Is {bn} reliable? Every {bn} model we track, by owner complaints. Free:', f'Know someone looking at a {E(bn)}?') if ms or co else '') + '</div>')
    desc = (f'Every {bn} model on the Lemon Index: ' + ', '.join(parts) + '.' + (f' Most reliable by NHTSA owner complaints per car sold: {best["name"]} ({best["li"]}; 100 is average).' if ms and len(ms) > 1 else '')) if parts else f'The {bn} models the Lemon Index tracks.'
    page(path, f'Is {bn} Reliable? Every {bn} Model by Owner Complaints | The Lemon Index', desc, body,
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{bn} reliability', "url": BASE + path}])
    if thin:   # the site's thin-page rule (advanced_pages.py, engine_pages.py): noindex,follow and out of the sitemap
        _f = os.path.join(OUT, path.strip('/'), 'index.html'); _s = open(_f, encoding='utf-8').read()
        if 'name="robots"' not in _s: open(_f, 'w', encoding='utf-8').write(_s.replace('<link rel="canonical"', '<meta name="robots" content="noindex,follow"><link rel="canonical"', 1))
        _noix.append(path)
    else: burls.append(path)
    if npg: _more.append((bn, path, npg))   # a make with nothing but "coming soon" keeps its page (no 404) but isn't listed
_BRAND_PG.update(b for b in _MAKES)   # BRAND_A links every make from here on (extra_pages.py, hd_pages.py)
wtile = ''.join(f'<div class="wt"><b>${per(*w["yrs"][max(w["yrs"])]):,}</b><span>{E(w["short"])}, {max(w["yrs"])}</span></div>' for w in WARR.values())
_morehtml = (f'<section class="bn4-more"><h2>Every other brand. <span class="h2s">Not in the 2010–2022 study, so no brand score. Their models are scored one by one where we have the data.</span></h2>'
             '<p class="chips">' + ''.join(f'<a class="chip" href="{p}">{E(n)} <small>{k}</small></a>' for n, p, k in _more) + '</p><p class="yc-cap" style="text-align:center">The number is how many of its models and pages are on the Lemon Index.</p></section>') if _more else ''
page('/brands/', 'Most Reliable Car Brands, Ranked by Owner Complaints | The Lemon Index',
     f'All {len(cards)} car brands ranked by NHTSA owner complaints per car sold, best to worst, plus what Ford, GM and Tesla report spending on warranty repairs per vehicle.',
     f'''<div class="pg">{phero('Brands', 'Every brand, ranked.', 'Owner complaints per car sold, best to worst. 100 is the average car.')}
<section><div class="mbs"><div class="mb"><div class="mg">{"".join(cards)}</div></div></div><p class="yc-cap" style="text-align:center">Car images: AI-generated illustrations{ai_note("cars on this page")}</p></section>
{_morehtml}
<section class="bwar"><p class="te">What automakers tell investors</p><h2>Warranty costs are rising. <span class="h2s">Warranty and recall costs booked per vehicle sold, from each company&#39;s 10-K.</span></h2><div class="wts">{wtile}</div>
<p class="yc-cap">Ford&#39;s rose from $1,675 a vehicle in 2023 to $2,042 in 2025. GM&#39;s from $1,259 to $2,190. Open a brand for the details.</p></section>
{share_line("Every car brand ranked by owner complaints per car sold, best to worst. Free:")}
<style>.bn4-more .chips{{justify-content:center}}.bn4-more .chip small{{color:#6e6e73;font-size:12px;margin-left:4px}}</style></div>''',
     ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Car brands ranked by reliability", "url": BASE + '/brands/'}])
print('brand pages:', len(burls) + 1, 'indexed;', len(_noix), 'noindex (thin):', ' '.join(_noix))
