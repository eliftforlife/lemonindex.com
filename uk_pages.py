# UK MOT pass rate pages (11-15, Lemon growth project 3B-3). Run by build.py with exec(), after the car pages (US links check FY).
# Data: data/uk_mot.json (data_uk_mot.py: DVSA "Anonymised MOT tests and results", 2024 tests, Open Government Licence v3.0).
# Pages: /uk/ (hub: best + worst vs cars the same age, the age effect, a searchable + sortable table of every model with 10,000+ tests)
# and /uk/<make>-<model>/ for the top 100 models by test volume plus the Toyota Avensis (a viewer asked). Every page is in en-GB
# (html lang only: these pages have no equivalent in another language or region, so there is no hreflang pair to declare).
# Wording rules: "first registered in 2016" (never "model year"), "MOT pass rate" (never "unreliable" as fact), tyres, miles;
# every page says an MOT shows the car's condition on the test day and carries the OGL credit line. No gov.uk logos, no "official".
UKD = _load('data/uk_mot.json') if os.path.exists('data/uk_mot.json') else None
UK_URLS = []
SEGN['uk'] = 'UK MOT pass rates'
UK_ASSET = '<link rel="stylesheet" href="/assets/ukx.css?v=1">'
UK_OGL = 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
UK_CREDIT = (f'<p class="ukx-cap">Contains public sector information licensed under the <a href="{UK_OGL}" rel="noopener license" target="_blank">Open Government Licence v3.0</a>. '
             'Source: DVSA anonymised MOT tests and results.</p>')
UK_TEST_DAY = 'An MOT shows the car&#39;s condition on the test day, not how it will run tomorrow.'
# US model pages for the same car (only where the UK and US names are the same car line); US-market versions can differ
UK_US = {'mini-hatch': 'mini-cooper', 'honda-jazz': 'honda-fit', 'ford-kuga': 'ford-escape', 'mazda-3': 'mazda3', 'mazda-6': 'mazda6',
         'mercedes-benz-m-class-ml': 'mercedes-benz-m', 'volkswagen-up': None}

# plain-English names for MOT failure items (DVSA's wording is shown under each one)
UK_ITEM = [   # checked against the items that make the top 6 on the model pages (11-15); order matters (first match wins)
    (r'^Position lamp', 'Sidelight not working'), (r'^Stop lamp', 'Brake light not working'), (r'^Side repeater', 'Side indicator not working'),
    (r'^Direction indicator', 'Indicator not working'), (r'^Headlamp aim', 'Headlight aimed wrong'), (r'^Headlamp: not working on dipped', 'Dipped headlight not working'),
    (r'^Headlamp: not working on main', 'Main-beam headlight not working'), (r'^Headlamp', 'Headlight not working or damaged'),
    (r'^Registration plate lamp', 'Number plate light out'), (r'^Rear fog lamp', 'Rear fog light not working'), (r'^Reversing lamp', 'Reversing light not working'),
    (r'^Hazard warning', 'Hazard lights not working'), (r'^Tread depth', 'Tyre tread below the 1.6 mm legal limit'),
    (r'^Condition: .*bulge', 'Tyre with a bulge'), (r'^Condition: .*(ply|cord)', 'Tyre cut to, or showing, its cords'), (r'^Condition: .*tyre', 'Tyre damaged'),
    (r'^Wipers?', 'Wiper not clearing the windscreen'), (r'^Washers?', 'Screen washer empty or not working'),
    (r'^Windscreen|^Condition of glass|^Glazing', 'Windscreen damage in the driver&#39;s view'), (r'^Rear view mirror|^Mirrors?', 'Mirror missing or damaged'),
    (r'^Coil spring', 'Broken coil spring'), (r'^Shock absorbers: .*leak', 'Leaking shock absorber'), (r'^Shock absorbers', 'Worn shock absorber or its bush'),
    (r'^Ball joint dust cover|^Linkage ball joint dust cover', 'Split ball joint dust cover'), (r'^Ball joint', 'Worn suspension ball joint'),
    (r'^Pins and bushes', 'Worn suspension bush (arm or anti-roll bar)'), (r'^Track rod end', 'Worn track rod end (steering)'),
    (r'^Linkage ball joints?', 'Worn steering or anti-roll bar link joint'), (r'^Joints: constant velocity', 'Split CV boot on a driveshaft'),
    (r'^Brake pads', 'Brake pads under 1.5 mm'), (r'^Brake discs', 'Brake discs worn or damaged'), (r'^Rbt \(sp\)|^Parking brake (efficiency|performance)', 'Handbrake too weak on the brake test'),
    (r'^Service brake performance: .*binding', 'Brake dragging (binding)'), (r'^Service brake performance|imbalance', 'Brakes uneven or too weak on the brake test'),
    (r'^Rigid brake pipes', 'Corroded brake pipe'), (r'^Flexible brake hoses', 'Damaged brake hose'), (r'^Anti-lock braking', 'ABS warning light or fault'),
    (r'^SRS malfunction', 'Airbag warning light on'), (r'^Malfunction indicator lamp', 'Engine warning light on'),
    (r'^Catalyst emissions|emissions', 'Exhaust emissions outside the limits'), (r'^Exhaust system', 'Exhaust leaking or loose'),
    (r'^Fluid leaks|^Oil leak', 'Fluid or oil leak'), (r'^Seat belt', 'Seat belt fault'), (r'^Registration plate', 'Number plate damaged or wrong'),
    (r'^Horn', 'Horn not working'), (r'^Corrosion|^Vehicle structure', 'Rust on the body or chassis'), (r'^Battery', 'Battery loose or leaking'),
    (r'^Tyre pressure monitoring', 'Tyre pressure warning light on')]


def uk_item(raw):
    for pat, nm in UK_ITEM:
        if re.search(pat, raw, re.I): return nm
    return raw.split(':')[0].strip().capitalize()


def uk_raw(raw):
    """DVSA's own wording, tidied: 'Tread depth: tread depth below requirements of 1.6mm' -> 'tread depth below requirements of 1.6mm'"""
    a, _, b = raw.partition(':')
    return (b or a).strip()


def _ukp(x, d=1): return f'{x * 100:.{d}f}%'
def _ukpts(d):
    if abs(d) < .05: return 'level with'
    return f'{abs(d):.1f} point{"s" * (abs(d) != 1.0)} ' + ('better than' if d > 0 else 'worse than')
def _uksg(d): return ('+' if d > 0 else '−' if d < 0 else '±') + f'{abs(d):.1f}'
def _ukcls(d): return 'ukx-up' if d >= 1 else 'ukx-dn' if d <= -1 else ''
def _ukm(v): return f'{v:,}' if v else '–'
def _ukyrs(ys): return f'{ys[0]}' if len(ys) == 1 else f'{ys[0]}–{ys[-1]}'
def _ukgroup(m): return 'cars' if m['kind'] == 'car' else 'vans'


def _uk_noun(m):
    """'Ford Fiestas' reads oddly for some names; 'Ford Fiesta cars' never does. Vans say vans."""
    return f'{m["name"]} ' + ('vans' if m['kind'] == 'van' else 'cars')


def _uk_picks(m):
    """Years to look for / be careful with, built only from the data: a year must be 2+ points and 2 standard errors away from the
    average for cars first registered that year."""
    good, bad = [], []
    for r in m['years']:
        need = max(2.0, 2 * r['se'])
        if r['diff'] >= need: good.append(r)
        elif r['diff'] <= -need: bad.append(r)
    good.sort(key=lambda r: -r['diff']); bad.sort(key=lambda r: r['diff'])
    return good[:4], bad[:4]


def _uk_us(m):
    fid = UK_US.get(m['id'], m['id'])
    if fid and fid in FY and os.path.exists(os.path.join(OUT, 'cars', fid, 'index.html')): return fid
    return None


def _uk_year_bars(m):
    rows = []
    for r in sorted(m['years'], key=lambda r: -r['y']):
        cls = 'ukx-good' if r['diff'] >= max(2.0, 2 * r['se']) else 'ukx-bad' if r['diff'] <= -max(2.0, 2 * r['se']) else ''
        sub = f'{_uksg(r["diff"])} pts vs {_ukgroup(m)} first registered in {r["y"]} ({_ukp(r["avg"])}) · {r["n"]:,} tests' + (f' · {r["miles"]:,} miles on average' if r['miles'] else '')
        rows.append(f'<li><span class="ukx-yl">{r["y"]}</span><span class="ukx-yb" role="img" aria-label="{r["y"]}: {_ukp(r["pass"])} passed first time; same-age average {_ukp(r["avg"])}">'
                    f'<i class="{cls}" style="width:{r["pass"] * 100:.1f}%"></i><em style="left:{r["avg"] * 100:.1f}%"></em></span><b>{_ukp(r["pass"])}</b><small>{sub}</small></li>')
    return (f'<ul class="ukx-yr">{"".join(rows)}</ul><p class="ukx-key"><span class="k1">{E(m["name"])} first-time pass rate</span>'
            f'<span class="k2">every {"car" if m["kind"] == "car" else "van"} first registered that year</span></p>')


def _uk_area_bars(m, n=7):
    rows = []
    mx = max([a['share'] for a in m['areas'][:n]] + [a['exp'] for a in m['areas'][:n]] + [.0001])
    for a in m['areas'][:n]:
        ratio = a['share'] / a['exp'] if a['exp'] else None
        cmp_ = (f'{ratio:.1f}× the rate for {_ukgroup(m)} the same age ({_ukp(a["exp"])})' if ratio and (ratio >= 1.15 or ratio <= .87)
                else f'about the same as {_ukgroup(m)} the same age ({_ukp(a["exp"])})')
        rows.append(f'<li><span class="ukx-al">{E(a["a"])}</span><span class="ukx-ab"><i style="width:{a["share"] / mx * 100:.1f}%"></i><em style="left:{a["exp"] / mx * 100:.1f}%"></em></span>'
                    f'<b>{_ukp(a["share"])}</b><small>{cmp_}</small></li>')
    return f'<ul class="ukx-ar">{"".join(rows)}</ul>'


def _uk_items(m, n=6):
    out = []
    for it in m['items'][:n]:
        ratio = it['share'] / it['exp'] if it['exp'] else None
        r_ = f' · {ratio:.1f}× {_ukgroup(m)} the same age' if ratio and (ratio >= 1.25 or ratio <= .8) and it['n'] >= 50 else ''
        out.append(f'<li><b>{uk_item(it["raw"])}</b><small>{_ukp(it["share"])} of tests ({it["n"]:,}){r_} · DVSA wording: &ldquo;{E(uk_raw(it["raw"]))}&rdquo;</small></li>')
    return f'<ol class="ukx-items">{"".join(out)}</ol>'


def _uk_faq_html(qa): return '<section class="yc ukx-faq"><h2>Questions</h2>' + qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in qa)) + '</section>'
def _uk_faq_ld(qa):
    strip = lambda s: re.sub(r'<[^>]+>', '', s).replace('&#39;', "'").replace('&ldquo;', '“').replace('&rdquo;', '”').replace('&amp;', '&')
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in qa]}


def _uk_src(extra=''):
    meta = UKD['meta']
    return (f'<section class="ukx-src"><p class="ukx-cap"><b>How to read this.</b> {UK_TEST_DAY} It counts what a tester found that day, and some of it (tyres, bulbs, wipers) '
            'is down to how a car was looked after, not how it was built. So we only compare a model with cars first registered in the same year, and we show the test count '
            'and the reasons cars failed. A low MOT pass rate is not proof that a model is unreliable.</p>'
            f'<p class="ukx-cap"><b>Method.</b> Every class 4 (cars and light vans) normal MOT test carried out in Great Britain in {meta["test_year"]} with a result of pass, fail or '
            'PRS (fixed at the test centre within an hour), one row per test. First-time pass rate = tests passed outright, out of all of them. PRS counts as a fail because the car '
            'arrived failing (this is DVSA&#39;s own &ldquo;initial failure rate&rdquo;, turned around). Trim and engine names are merged into one model (&ldquo;FIESTA ZETEC&rdquo; and &ldquo;FIESTA&rdquo; '
            f'are both the Fiesta). Year = year of first registration in the UK, not the year the car was built. A year needs {meta["min_tests"]:,}+ tests to be shown. Vans, pickups and '
            f'van-based people carriers are compared with other vans. Northern Ireland isn&#39;t in this data. {extra}</p>{UK_CREDIT}</section>')


def _uk_post(path):
    """en-GB on the UK pages, and a footer line that fits them (the shared footer talks about U.S. data)."""
    f = os.path.join(OUT, path.strip('/'), 'index.html'); s = open(f, encoding='utf-8').read()
    s = s.replace('<html lang="en">', '<html lang="en-GB">', 1)
    s = re.sub(r'<span class="f2-dis">.*?</span>', '<span class="f2-dis">UK pages: our own analysis of DVSA&#39;s anonymised MOT test data (Open Government Licence v3.0). '
               'Not affiliated with DVSA or any carmaker. Not a safety rating.</span>', s, count=1, flags=re.S)
    open(f, 'w', encoding='utf-8').write(s)


def _uk_model(m, byid):
    nm = E(m['name']); path = f'/uk/{m["id"]}/'; ys = [r['y'] for r in m['years']]; noun = E(_uk_noun(m)); grp = _ukgroup(m)
    good, bad = _uk_picks(m)
    best_y = max(m['years'], key=lambda r: r['diff']); worst_y = min(m['years'], key=lambda r: r['diff'])
    top_a = m['areas'][:3]
    stats = (f'<div class="stats ukx-st"><div><b>{_ukp(m["pass"])}</b><span>passed their MOT first time ({m["tests"]:,} tests in {UKD["meta"]["test_year"]})</span></div>'
             f'<div><b class="{_ukcls(m["diff"])}">{_uksg(m["diff"])} pts</b><span>vs {grp} first registered in the same years ({_ukp(m["exp"])})</span></div>'
             + (f'<div><b>{m["miles"]:,}</b><span>average miles at the test' + (f' (same-age {grp}: {m["exp_miles"]:,})' if m.get('exp_miles') else '') + '</span></div>' if m['miles'] else '')
             + (f'<div><b>{_ukp(top_a[0]["share"])}</b><span>of tests failed on {E(top_a[0]["a"].lower())}, the top reason</span></div>' if top_a else '') + '</div>')
    lede = (f'{noun} first registered {_ukyrs(ys)} passed {_ukp(m["pass"])} of their MOTs first time in {UKD["meta"]["test_year"]}: '
            f'{_ukpts(m["diff"])} {grp} the same age.')
    # years to look for / be careful with
    li = lambda r: (f'<li><b>First registered in {r["y"]}</b>: {_ukp(r["pass"])} passed first time, {_ukpts(r["diff"])} {grp} that age '
                    f'({r["n"]:,} tests)</li>')
    pick = ('<div class="ukx-pick">'
            + f'<div class="ukx-pg"><h3>Years to look for</h3>' + (f'<ul>{"".join(li(r) for r in good)}</ul>' if good else f'<p>No year of the {nm} beats {grp} its age by a clear margin (2+ points).</p>') + '</div>'
            + f'<div class="ukx-pb"><h3>Years to be careful with</h3>' + (f'<ul>{"".join(li(r) for r in bad)}</ul>' if bad else f'<p>No year of the {nm} trails {grp} its age by a clear margin (2+ points).</p>') + '</div>'
            + '</div><p class="ukx-cap">Built only from the 2024 MOT results: a year is listed when its first-time pass rate is at least 2 points (and twice its margin of error) away '
            f'from every {"car" if m["kind"] == "car" else "van"} first registered that year. It&#39;s that year&#39;s record, not the history of any one car: check the MOT history of the exact car too.</p>')
    years_tab = (f'<section class="yc" id="ukx-pick"><h2>Which {nm} years to look for. <span class="h2s">Against {grp} the same age.</span></h2>{pick}</section>'
                 f'<section class="yc" id="ukx-years"><h2>MOT pass rate by year of first registration. <span class="h2s">{len(ys)} years with {UKD["meta"]["min_tests"]:,}+ tests each.</span></h2>'
                 f'{_uk_year_bars(m)}<p class="ukx-cap">Older cars fail more often, whatever the make, so the gray line moves from year to year. What matters is how far the bar sits '
                 f'from it. Green = 2+ points (and twice the margin of error) better than {grp} first registered that year, red = that much worse.</p></section>')
    fails_tab = (f'<section class="yc" id="ukx-fails"><h2>Why {nm} {"cars" if m["kind"] == "car" else "vans"} fail their MOT. <span class="h2s">Share of tests with a fail in each area.</span></h2>'
                 f'{_uk_area_bars(m)}<p class="ukx-key"><span class="k1">{nm}</span><span class="k2">{grp} first registered in the same years</span></p>'
                 '<p class="ukx-cap">A test can fail in more than one area. Each share counts tests with at least one fail or PRS defect there. &ldquo;Body, chassis and underside&rdquo; also covers exhaust pipes, driveshaft (CV) boots and engine mounts.</p></section>'
                 f'<section class="yc" id="ukx-items"><h2>The most common fails. <span class="h2s">The exact items testers wrote down.</span></h2>{_uk_items(m)}'
                 + (f'<p class="ukx-cap">{_ukp(m["dangerous"])} of {nm} tests found at least one &ldquo;dangerous&rdquo; defect (the car shouldn&#39;t be driven until it&#39;s fixed), '
                    f'against {_ukp(m["exp_dangerous"])} for {grp} the same age.</p>' if m.get('exp_dangerous') else '') + '</section>')
    # FAQ
    a1 = (f'{_ukp(m["pass"])} of {noun} first registered {_ukyrs(ys)} passed their MOT first time in {UKD["meta"]["test_year"]}, from {m["tests"]:,} tests. '
          f'{grp.capitalize()} first registered in the same years passed {_ukp(m["exp"])}, so the {nm} is {_ukpts(m["diff"])} {grp} its age.')
    qa = [(f'What is the {nm} MOT pass rate?', a1)]
    if good: qa.append((f'Which {nm} years have the best MOT pass rate?', 'Against cars the same age: ' + '; '.join(f'first registered in {r["y"]}, {_ukp(r["pass"])} ({_uksg(r["diff"])} points)' for r in good[:3]) + '.'))
    else: qa.append((f'Which {nm} years have the best MOT pass rate?', f'No year clearly beats {grp} its age. The closest is first registered in {best_y["y"]}: {_ukp(best_y["pass"])}, {_ukpts(best_y["diff"])} {grp} that age.'))
    if bad: qa.append((f'Which {nm} years should I be careful with?', 'The years furthest below cars the same age: ' + '; '.join(f'first registered in {r["y"]}, {_ukp(r["pass"])} ({_uksg(r["diff"])} points)' for r in bad[:3]) + '.'))
    if top_a: qa.append((f'Why do {noun} fail their MOT?', 'The top areas: ' + ', '.join(f'{a["a"].lower()} ({_ukp(a["share"])} of tests)' for a in top_a)
                         + (f'. The single most common item is {uk_item(m["items"][0]["raw"]).lower()} ({_ukp(m["items"][0]["share"])} of tests).' if m['items'] else '.')))
    if m['miles']: qa.append((f'How many miles has a {nm} usually done at its MOT?', f'{m["miles"]:,} miles on average at the 2024 test, across first registration years {_ukyrs(ys)}'
                              + (f', against {m["exp_miles"]:,} for {grp} the same age.' if m.get('exp_miles') else '.')))
    qa.append((f'Does the MOT pass rate tell me if a {nm} is reliable?', f'Not on its own. {UK_TEST_DAY} Wear items like tyres, bulbs and wipers depend on the owner as much as the car. '
               f'Comparing the {nm} with {grp} first registered in the same years takes age out of it, but always check the MOT history and service record of the exact car.'))
    faq_tab = _uk_faq_html(qa)
    panels = [('uk-years', 'By year', years_tab), ('uk-fails', 'Why they fail', fails_tab), ('uk-faq', 'Questions', faq_tab)]
    tabs = TAB.ASSET + TAB._tabs(panels, f'{m["name"]} MOT data')
    # links
    same = [x for x in byid.values() if x['make'] == m['make'] and x['id'] != m['id'] and x.get('page')][:8]
    us = _uk_us(m)
    links = ''
    if same: links += f'<p class="crel ukx-ch">' + ' '.join(f'<a href="/uk/{x["id"]}/">{E(x["name"])}</a>' for x in same) + '</p>'
    if us: links += (f'<p class="ukx-cap">Also sold in the US: <a href="/cars/{us}/">{E(FY[us]["name"])} problems and best years</a> (owner complaints to the U.S. government; '
                     'US-market versions can differ from UK cars).</p>')
    body = (f'<div class="pg mp6 ukx">{UK_ASSET}<section class="ph"><p class="ph-e"><a href="/uk/">UK MOT pass rates</a> · {E(m["make_name"])}</p>'
            f'<h1>{nm} MOT pass rate.</h1><p class="ph-s">{lede}</p>{stats}</section>'
            f'{tabs}'
            + (f'<section class="yc"><h2>More {E(m["make_name"])} MOT pass rates.</h2>{links}</section>' if links else '')
            + f'<p class="ukx-cap" style="text-align:center"><a href="/uk/">Every UK model ranked against cars its age →</a></p>'
            + _uk_src(f'The {nm} here merges these DVSA model names: ' + ', '.join(E(k) for k in list(m['names'])[:6]) + ('…' if len(m['names']) > 6 else '') + '.')
            + share_line(f'{m["name"]} MOT pass rate by year, against cars the same age (2024 MOT tests):', f'Know someone buying a used {E(m["model_name"])}?') + '</div>')
    tt = f'{m["name"]} MOT Pass Rate by Year: Best and Worst Years | The Lemon Index'
    if len(tt) > 65 + len(' | The Lemon Index'): tt = f'{m["name"]} MOT Pass Rate by Year | The Lemon Index'
    desc = (f'{m["name"]} MOT pass rate: {_ukp(m["pass"])} passed first time in {m["tests"]:,} tests in 2024, {_ukpts(m["diff"])} {grp} the same age. '
            f'By year of first registration, top fails and mileage.')
    page(path, tt, desc, body, ld=[_uk_faq_ld(qa)])
    _uk_post(path); UK_URLS.append(path)


def _uk_hub(models, pages):
    meta = UKD['meta']; avg = UKD['avg']; cars = [m for m in models if m['kind'] == 'car']; vans = [m for m in models if m['kind'] == 'van']
    pop = [m for m in cars if m['tests'] >= 50000]; popv = [m for m in vans if m['tests'] >= 30000]
    link = lambda m: f'<a href="/uk/{m["id"]}/">{E(m["name"])}</a>' if m['id'] in pages else E(m['name'])
    def lst(ms, title):
        return (f'<div><h3>{title}</h3><ol>' + ''.join(f'<li><span>{link(m)}</span><b class="{_ukcls(m["diff"])}">{_uksg(m["diff"])} pts</b></li>' for m in ms) + '</ol></div>')
    best = sorted(pop, key=lambda m: -m['diff'])[:10]; worst = sorted(pop, key=lambda m: m['diff'])[:10]
    bestv = sorted(popv, key=lambda m: -m['diff'])[:5]; worstv = sorted(popv, key=lambda m: m['diff'])[:5]
    ca = avg['car']; yrs = sorted(int(y) for y in ca)
    cn = sum(ca[str(y)]['n'] for y in yrs); cp = sum(ca[str(y)]['n'] * ca[str(y)]['pass'] for y in yrs) / cn
    age = ''.join(f'<li><b>{ca[str(y)]["pass"] * 100:.0f}</b><i style="height:{max(4, (ca[str(y)]["pass"] - .4) / .6 * 100):.0f}%"></i><span>{str(y)[2:]}</span></li>' for y in yrs)
    y_new, y_old = yrs[-1], yrs[0]
    # national failure areas for cars (weighted over years)
    ar = defaultdict(float)
    for y in yrs:
        for a, v in ca[str(y)]['areas'].items(): ar[a] += v * ca[str(y)]['n']
    ar = sorted(((a, v / cn) for a, v in ar.items()), key=lambda t: -t[1])[:8]
    mx = ar[0][1] if ar else 1
    abars = '<ul class="ukx-ar">' + ''.join(f'<li><span class="ukx-al">{E(a)}</span><span class="ukx-ab"><i style="width:{v / mx * 100:.1f}%"></i></span><b>{_ukp(v)}</b></li>' for a, v in ar) + '</ul>'
    # the table
    rows = ''.join(
        f'<tr data-s="{E((m["name"] + " " + " ".join(m["names"])).lower())}" data-k="{m["kind"]}"><td data-v="{E(m["name"])}">{link(m)}' + ('<small>van</small>' if m['kind'] == 'van' else '') + '</td>'
        f'<td data-v="{m["tests"]}">{m["tests"]:,}</td><td data-v="{m["pass"]}">{_ukp(m["pass"])}</td><td data-v="{m["diff"]}" class="{_ukcls(m["diff"])}">{_uksg(m["diff"])}</td>'
        f'<td class="ukx-hm" data-v="{m["miles"] or 0}">{_ukm(m["miles"])}</td><td class="ukx-hm" data-v="{m["years"][0]["y"]}">{_ukyrs([r["y"] for r in m["years"]])}</td></tr>'
        for m in models)
    th = lambda t, k='num', cls='': f'<th scope="col" data-t="{k}"{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}><button type="button">{t}</button></th>'
    table = (f'<div class="ukx-tools"><input id="ukx-q" type="search" placeholder="Search a model, e.g. Avensis or Corsa" aria-label="Search the models">'
             f'<select id="ukx-k" aria-label="Cars or vans"><option value="">Cars and vans</option><option value="car">Cars only</option><option value="van">Vans and pickups only</option></select>'
             f'<span id="ukx-n" class="ukx-cap" role="status" aria-live="polite">{len(models)} models</span></div>'
             f'<div class="ukx-tw"><table class="ukx-t" id="ukx-t"><thead><tr>{th("Model", "text")}{th("Tests")}{th("Passed first time")}{th("vs same age (pts)")}'
             f'{th("Avg miles", cls="ukx-hm")}{th("First registered", cls="ukx-hm")}</tr></thead><tbody>{rows}</tbody></table></div>'
             '<p id="ukx-none" class="ukx-none" hidden>No model matches. Try one word, like Golf.</p>'
             f'<p class="ukx-cap">{len(models)} models with {meta["hub_min"]:,}+ tests in years that have {meta["min_tests"]:,}+ tests each; {len(pages)} have their own page. '
             '&ldquo;vs same age&rdquo; = the model&#39;s first-time pass rate minus the average for every car (or van) first registered in the same years, weighted by its tests.</p>')
    top_bad = worst[0] if worst else None; top_good = best[0] if best else None
    av = next((m for m in models if m['id'] == 'toyota-avensis'), None)
    qa = [('Which used cars have the best MOT pass rate in the UK?', 'Against cars the same age, among models with 50,000+ tests in 2024: '
           + ', '.join(f'the {E(m["name"])} ({_uksg(m["diff"])} points)' for m in best[:5]) + '.'),
          ('Which cars fail their MOT most?', 'Against cars the same age, among models with 50,000+ tests: ' + ', '.join(f'the {E(m["name"])} ({_uksg(m["diff"])} points)' for m in worst[:5])
           + f'. {UK_TEST_DAY} A low pass rate is not proof that a model is unreliable.'),
          ('Why compare cars with cars the same age?', f'Because age matters more than anything. Cars first registered in {y_new} passed {_ukp(ca[str(y_new)]["pass"])} of their 2024 MOTs first time; '
           f'cars first registered in {y_old} passed {_ukp(ca[str(y_old)]["pass"])}. A model sold mostly as new cars would look good next to one whose cars are mostly old, so each model is '
           'compared with every car first registered in the same years.'),
          ('What do cars fail their MOT on most?', 'Across cars first registered ' + f'{y_old}–{y_new}: ' + ', '.join(f'{a.lower()} ({_ukp(v)} of tests)' for a, v in ar[:4]) + '.'),
          ('Where does this data come from?', f'DVSA&#39;s anonymised MOT tests and results: every MOT test carried out in Great Britain in {meta["test_year"]}, published free under the '
           'Open Government Licence v3.0. The scores are our own analysis, not DVSA&#39;s.')]
    if av: qa.insert(2, ('Is the Toyota Avensis good on MOTs?', f'Yes, against cars its age. {_ukp(av["pass"])} of Avensis cars passed first time in {av["tests"]:,} tests, '
                         f'{_ukpts(av["diff"])} cars first registered in the same years, even though they averaged {av["miles"]:,} miles at the test (same-age cars: {av["exp_miles"]:,}).'))
    body = (f'<div class="pg mp6 ukx uk5">{UK_ASSET}<section class="ph"><p class="ph-e"><a href="/">The Lemon Index</a> · UK</p>'
            f'<h1>UK MOT pass rates by car model.</h1><p class="ph-s">Which used cars pass their MOT first time, compared with cars the same age. '
            f'From {meta["tests_in_scope"]:,} MOT tests in Great Britain in {meta["test_year"]}.</p>'
            f'<div class="stats ukx-st"><div><b>{meta["tests_in_scope"] / 1e6:.1f}M</b><span>MOT tests on cars and vans first registered {y_old}–{y_new}</span></div>'
            f'<div><b>{_ukp(cp)}</b><span>of cars passed first time</span></div><div><b>{len(models)}</b><span>models with {meta["hub_min"]:,}+ tests</span></div>'
            f'<div><b>{ca[str(y_new)]["pass"] * 100:.0f}% vs {ca[str(y_old)]["pass"] * 100:.0f}%</b><span>cars first registered in {y_new} vs {y_old}</span></div></div></section>'
            f'<section class="yc" id="ukx-best"><h2>Best and worst popular cars. <span class="h2s">MOT pass rate against cars the same age, models with 50,000+ tests.</span></h2>'
            f'<div class="ukx-bw">{lst(best, "Pass more than cars their age")}{lst(worst, "Fail more than cars their age")}</div>'
            f'<p class="ukx-cap">Points = first-time pass rate minus the average for every car first registered in the same years. {UK_TEST_DAY}</p></section>'
            + '<div class="cpl v5-pl uk5-pl">'
            + V5_BOX('car', 'Vans and pickups.', '<p class="yc-cap">Against other vans the same age, 30,000+ tests.</p>'
                     f'<div class="ukx-bw">{lst(bestv, "Best")}{lst(worstv, "Worst")}</div><p class="ukx-cap">Vans do more miles and harder work than cars, so they get their own average. '
                     'Van-based people carriers (Berlingo, Tourneo, Transporter) count as vans. Goods vans over 3,000 kg take a different MOT (class 7) that isn&#39;t in these numbers, '
                     'so big vans like the Ducato, Boxer and Sprinter count only their lighter versions and motorhomes, which take the car MOT.</p>', 'ukx-vans', h2=True)
            + V5_BOX('data', 'Every model.', '<p class="yc-cap">Search, then tap a column to sort. The list scrolls.</p>' + table, 'ukx-models', h2=True)
            + V5_BOX('calendar', 'Why we compare cars with cars the same age.', '<p class="yc-cap">First-time MOT pass rate by year of first registration, every car.</p>'
                     f'<ul class="ukx-age" aria-label="Pass rate by year of first registration">{age}</ul>'
                     f'<p class="ukx-cap">Cars first registered in {y_new} (3 years old, many on their first MOT) passed {_ukp(ca[str(y_new)]["pass"])}; cars first registered in {y_old} passed '
                     f'{_ukp(ca[str(y_old)]["pass"])}. A model sold mostly as new cars would beat one whose cars are mostly old, whatever the build quality. So every score here compares a model '
                     'with every car first registered in the same years, weighted by its tests.</p>', 'ukx-age', h2=True)
            + V5_BOX('wrench', 'What cars fail on.', '<p class="yc-cap">Share of car tests with a fail in each area.</p>' + abars
                     + '<p class="ukx-cap">A test can fail in more than one area. Lights and electrics are mostly bulbs; tyres are mostly tread under the 1.6 mm legal limit; &ldquo;body, chassis and underside&rdquo; also covers exhaust pipes, driveshaft (CV) boots and engine mounts.</p>', 'ukx-why', h2=True)
            + V5_BOX('talk', 'Questions', qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in qa)), 'questions', h2=True)
            + V5_BOX('info', 'How to read this, and where the data comes from', _uk_src())
            + '</div>'
            + share_line(f'UK MOT pass rates for {len(models)} car models, against cars the same age (2024 MOT tests):', 'Know someone buying a used car in the UK?')
            + '</div><script src="/assets/ukx.js?v=1" defer></script>')
    page('/uk/', 'UK MOT Pass Rates by Car Model: Best and Worst Cars | The Lemon Index',
         f'Which cars pass their MOT first time: {len(models)} UK models ranked against cars the same age, from {meta["tests_in_scope"] / 1e6:.1f}M MOT tests in {meta["test_year"]}. Search any model.',
         body, ld=[_uk_faq_ld(qa)])
    _uk_post('/uk/'); UK_URLS.insert(0, '/uk/')


def _uk_pages():
    if not UKD: return
    models = UKD['models']; byid = {m['id']: m for m in models}
    pages = {m['id'] for m in models if m.get('page')}
    for m in models:
        if m['id'] in pages: _uk_model(m, byid)
    _uk_hub(models, pages)
    print('uk pages', len(UK_URLS), 'indexed, 0 noindex')
_uk_pages()
