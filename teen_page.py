# /best/safest-cars-for-teens/ (11-12, Linda: "It told me the 'safest' Corolla is a 2002. I need a site that knows what safe means for a kid.")
# Run by seo_pages.py with exec() (build.py's page, YEARS, BYNAME, extra, CARU, E, best_img, best_tier ... in scope). Every number is our data:
#   crash stars = NHTSA 5-Star Safety Ratings, overall rating, per model year and version (data_fetch_api.py -> extras_api*.json 'safety')
#   score       = that model year's Lemon Index (NHTSA owner complaints per car sold vs the average car of the same model year)
#   ESC         = electronic stability control, required on every new light vehicle from the 2012 model year (FMVSS No. 126), so 2012+ only
# Rank: the version NHTSA rated lowest that year (so every tested version is at least that), then the best version, then the fewest complaints.
# Prices: skipped on purpose. data/prices.json covers one model, and we have no free, citable used-price source for every model year yet.
TEEN_URL = '/best/safest-cars-for-teens/'
# Sports and muscle cars are left out, following IIHS's advice for teen drivers to stay away from high horsepower (iihs.org, safe vehicles for teens)
TEEN_SPORTY = re.compile(r'\b(Charger|Challenger|Mustang|Camaro|Corvette|370Z|350Z|GT-R|Nissan Z|WRX|BRZ|86|FR-S|Miata|MX-5|Genesis Coupe|Supra|Viper|911|Boxster|Cayman|M3|M4|AMG|SRT|Type R|Hellcat|GT500|Raptor|TRX)\b')
def _teen_page():
    rows = []
    for f in YEARS:
        c = BYNAME.get(f['name'])
        if not c or c['seg'] not in ('car', 'suv', 'minivan', 'truck') or TEEN_SPORTY.search(f['name']): continue   # no cargo vans; no sports or muscle cars
        for v in f['years']:
            if v['y'] < 2012 or v.get('early') or not v.get('ok') or v.get('li') is None or v['li'] > 110: continue   # stability control standard; a full 3 years of complaints; scored; not worse than average
            sf = extra(f['id'], v['y']).get('safety') or {}
            rated = [int(x['overall']) for x in (sf.get('variants') or []) if str(x.get('overall')).isdigit()]
            if not rated or max(rated) < 5: continue   # a 5-star overall rating for at least one version
            rows.append(dict(f=f, c=c, y=v['y'], li=v['li'], lo=min(rated), hi=max(rated), nv=len(rated)))
    key = lambda r: (-r['lo'], -r['hi'], r['li'], -r['y'])
    rows.sort(key=key)
    by = {}
    for r in rows: by.setdefault(r['f']['id'], []).append(r)
    models = sorted(by.values(), key=lambda rs: key(rs[0]))
    if len(models) < 10: print('teen page skipped: only', len(models), 'models qualify'); return None
    stars = lambda r: ('★' * 5 + ' all versions') if r['lo'] == 5 else f'★★★★★ best version · {r["lo"]}★ lowest'
    def chip(r):
        st = '5★' if r['lo'] == 5 else f'{r["lo"]}–5★'
        return f'<a class="tn-y" href="{CARU(r["f"], r["y"])}"><b>{r["y"]}</b><span>{st}</span><i class="{best_tier(r["li"])}">{r["li"]}</i></a>'
    def row(i, rs):
        r = rs[0]; f, nm = r['f'], r['f']['name']
        more = sorted(rs[1:], key=lambda x: x['y'])
        return (f'<li><span class="rk">{i}</span>{best_img(f["id"], nm)}<div><b><a href="{CARU(f, r["y"])}">{r["y"]} {E(nm)}</a></b>'
                f'<small>{E(r["c"]["segName"])} · {stars(r)}</small>'
                + (f'<span class="tn-ys">{"".join(chip(x) for x in more)}</span>' if more else '') + f'</div><span class="sc {best_tier(r["li"])}">{r["li"]}</span></li>')
    top = models[:20]
    segs = [('suv', 'SUVs'), ('car', 'Cars'), ('minivan', 'Minivans'), ('truck', 'Pickups')]
    # 11-12 (Elijah: "all the things are kind of confusing underneath"): the per-type lists were a second copy of the top 20 with every chip;
    # now one small card per type with its top 3
    def trow(rs):
        r = rs[0]; f = r['f']
        return f'<li><a href="{CARU(f, r["y"])}">{best_img(f["id"], f["name"])}<span>{r["y"]} {E(f["name"])}</span><i class="{best_tier(r["li"])}">{r["li"]}</i></a></li>'
    types = cbx_types([(lab, [rs for rs in models if rs[0]['c']['seg'] == sg]) for sg, lab in segs], trow)
    t0, t1, t2 = top[0][0], top[1][0], top[2][0]
    n5 = sum(1 for r in rows if r['lo'] == 5)
    lede = (f'The safest used cars for a teen driver, by our data: the {t0["y"]} {t0["f"]["name"]}, the {t1["y"]} {t1["f"]["name"]} and the {t2["y"]} {t2["f"]["name"]}. '
            f'Each has a 5-star NHTSA crash rating, standard stability control (every 2012 and newer car) and fewer owner complaints than the average car.')
    how = ('Model years 2012 to 2022 (stability control standard, and 3 full years of owner complaints); a 5-star NHTSA overall crash rating for at least one version; '
           'a Lemon Index of 110 or lower (about average or better); no sports or muscle cars (IIHS advises new drivers to stay away from high horsepower) and no cargo vans. '
           'Ranked by the lowest crash rating NHTSA gave any version that year, then by the fewest owner complaints per car sold. '
           '&#34;Lowest&#34; = the lowest overall rating NHTSA gave any version (body style, drive) that year: check the exact car&#39;s rating by VIN.')
    faq = [('What is the safest used car for a teenager?', f'By NHTSA crash ratings and owner complaints, the {t0["y"]} {t0["f"]["name"]} ranks first: 5 stars overall in NHTSA crash tests and a Lemon Index of {t0["li"]} (100 is the average car, lower is better).'),
           ('Why only 2012 and newer?', 'Electronic stability control, which helps stop skids and rollovers, has been required on every new U.S. passenger vehicle since the 2012 model year (federal standard FMVSS No. 126). Older cars may not have it.'),
           ('Does this list include prices?', 'Not yet. We only publish a price when we can cite where it came from, and we don\'t have a free used-price source for every model year. For budget picks, see the lists of the best used cars under $10,000, $15,000 and $20,000.')]
    qa = faq + [('How did you pick these cars?', how)]
    # 11-13 v2 (Elijah: "needs better design like bars or charts"): the whole top 20 as one bar chart, then a card per car with its numbers as bars
    mx = cbx_scale([rs[0]['li'] for rs in top])
    short = lambda f: E(f['name'].replace('Volkswagen', 'VW').replace('Chevrolet', 'Chevy'))
    chart = cbx_chart([(f'#teen-{i}', f'<b>{i}</b> {rs[0]["y"]} {short(rs[0]["f"])}', rs[0]['li'], rs[0]['li'], best_tier(rs[0]['li'])) for i, rs in enumerate(top, 1)], mx,
                      'Lemon Index: shorter bar = fewer complaints per car sold. Dashed line = the average car (100). Tap a car.')
    def card(i, rs):
        r = rs[0]; f = r['f']
        crash = '5 stars in every NHTSA crash test' if r['lo'] == 5 else f'5 stars in its best NHTSA crash test ({r["lo"]} in its lowest)'
        why = f'{crash}, and {cbx_times(r["li"], r["y"])}.'
        more = sorted(rs[1:], key=lambda x: x['y'])
        also = (f'<p class="cbx-also">Also on the list: ' + ' '.join(f'<a href="{CARU(f, x["y"])}">{x["y"]}</a>' for x in more) + '</p>') if more else ''
        return cbx_card(f'teen-{i}', i, best_img(f['id'], f['name']), f'<a href="{CARU(f, r["y"])}">{r["y"]} {E(f["name"])}</a>', why,
                        cbx_stars(r['lo'], r['hi']) + cbx_meter('Complaints', r['li'], mx, r['li'], best_tier(r['li']), unit='Lemon Index'), also)
    vis_list = (f'<section class="cbx-sec cbx-list"><h2>The top {len(top)}</h2>{chart}<ol class="cbx-cards">' + ''.join(card(i, rs) for i, rs in enumerate(top, 1)) + '</ol></section>')
    body = ('<div class="advp cb cbx">' + cbx_head('Safest used cars for teens.', '5-star crash tests first, then the fewest owner complaints per car sold. 2012 and newer, no sports cars.')
            + vis_list

            + types + cbx_faq([(q, f'<p>{E(a)}</p>') for q, a in qa]) + cbx_buy() + cbx_budgets()
            + cbx_src(f'{lede} Sources: NHTSA 5-Star Safety Ratings (overall rating, per model year and version, api.nhtsa.gov); NHTSA owner complaints filed within 3 years of each model year, per vehicle sold; '
                      f'published U.S. sales. Stability control: FMVSS No. 126. {n5:,} model years earned 5 stars for every version tested. Complaints are owner reports, not proof of a defect. '
                      'This is not a safety rating of its own: it combines NHTSA&#39;s crash tests with our complaint score.') + '</div>')
    body += share_line(f'The safest used cars for teens: 5-star crash tests, stability control and the fewest owner complaints. #1: the {t0["y"]} {t0["f"]["name"]}. Free list:', 'Know a parent shopping for a first car?')
    page(TEEN_URL, 'Safest Used Cars for Teens, by Crash Tests and Complaints | The Lemon Index', lede, body, ld=[faq_ld([(q, '', a) for q, a in faq])])
    SEO_URLS.append(TEEN_URL)
    print('teen page:', len(models), 'models,', len(rows), 'model years; top', t0['y'], t0['f']['name'])
    return (TEEN_URL, 'Safest used cars for teens', t0['f']['id'])
TEEN_CARD = _teen_page()
