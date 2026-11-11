# Brand pages (11-03, Elijah: "start brand pages and make sure they look good like the rest of the website"). Run by build.py with exec(),
# so page(), E, plain, gauge, verdict, CARS, YEARS, mphoto, pimg, who, pcredit, BRANDS ... are in scope.
#   /brands/            every brand, best to worst, as photo cards
#   /brands/<brand>/    the brand's score, its models ranked as photo cards, its best and worst model, and (Ford, GM, Tesla) what the company
#                       itself reports spending on warranty repairs and recalls per vehicle sold (SEC annual reports, 10-K).
def _verdict(li):   # build.py's verdict() name gets reused as a string by the compare pages, so a local copy
    return ('good', 'One of the most reliable') if li < 50 else ('good', 'Better than average') if li < 85 else ('mid', 'About average') if li <= 115 else ('bad', 'Worse than average') if li < 200 else ('bad', 'Lemon alert')
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

brank = {n.rstrip('*'): (i + 1, li) for i, (n, li) in enumerate(BRANDS)}
burls = []
cards = []
for b, (rk, li) in brank.items():
    ms = sorted([c for c in CARS if c['brand'] == b], key=lambda c: c['li'])
    if not ms: continue
    top = max(ms, key=lambda c: c['sold']); ph = aph(top['id'])   # 11-10 (Elijah: 'update brands car images'): AI illustrations first, Commons only where none
    cls, word = _verdict(li); est = b in ('Tesla', 'Porsche')
    def mc(c):
        p = aph(c['id']); href = f'/cars/{c["id"]}/' if c['id'] in FY else f'/electric/{c["id"]}/'
        return (f'<a class="mc" href="{href}"><span class="mc-p">{pimg(p, c["name"]) if p else ""}</span><b>{E(c["name"].split(" ", 1)[1] if " " in c["name"] else c["name"])}</b>'
                f'<span class="{"good" if c["li"] < 100 else "bad"}">{c["li"]}</span></a>')
    best, worst = ms[0], ms[-1]
    two = '' if len(ms) < 2 else (f'<section class="tiles">'
        + ''.join(f'<a class="tile" href="/cars/{c["id"]}/"><div class="tt"><p class="te">{lab}</p><h2>{E(c["name"].split(" ", 1)[-1])}.</h2><p class="ts">{E(plain(c["li"]))}.</p>'
                  f'<span class="tl">See every year <i>›</i></span></div><div class="tp">{pimg(aph(c["id"]), c["name"])}<span class="tsc {"good" if c["li"] < 100 else "bad"}">{c["li"]}</span></div></a>'
                  for lab, c in ((f'Most reliable {E(b)}', best), (f'Least reliable {E(b)}', worst)) if c['id'] in FY) + '</section>')
    body = f'''<div class="pg mp6"><section class="ph yph6"><div class="yh-t"><p class="ph-e"><a href="/brands/">Brands</a> · #{rk} of {len(brank)}</p><h1>{E(b)}.</h1>
<p class="ph-s">Every {E(b)} model, ranked by owner complaints per car sold.</p>
<div class="yhero">{gauge(li, 190)}<div class="yverd {cls}"><p><b>{word}.</b> <span>All {E(b)} models, 2010–2022{"" if plain(li).lower() in word.lower() else ": " + E(plain(li))}.</span></p>
<p class="ybw">Best <a class="good" href="/cars/{best["id"]}/">{E(best["name"])}</a>{f' · Worst <a class="bad" href="/cars/{worst["id"]}/">{E(worst["name"])}</a>' if worst is not best else ''}</p></div></div></div>
<div class="ph-v">{YSL.model_hero_html(top['id'], top['name']) if ph and ph.get('ai') else pimg(ph, top["name"]) + pcredit(who(ph))}</div></section>
{warranty_html(b)}
<section><h2>Every {E(b)}, ranked. <span class="h2s">Lower is better. 100 is the average car.</span></h2><div class="mbs"><div class="mb"><div class="mg">{"".join(mc(c) for c in ms)}</div></div></div></section>
{two}
<p class="yc-cap" style="text-align:center">{"* Small sample or estimated sales. " if est else ""}Lemon Index = safety complaints filed with the U.S. government within 3 years, per car sold, against the average car. <a href="/method/">How it works</a> · <a href="/brands/">Every brand</a>{pcredit([x for c in ms for x in who(aph(c["id"]))]).replace('<p class="ph-cr">', ' ').replace('</p>', '')}</p>
{share_line(f'Is {b} reliable? Every {b} model ranked by owner complaints. Best: {best["name"]}. Worst: {worst["name"]}. Free:' if worst is not best else f'Is {b} reliable? Every {b} model ranked by owner complaints. Free:', f'Know someone looking at a {E(b)}?')}</div>'''
    page(f'/brands/{BSLUG(b)}/', f'Is {b} Reliable? Every {b} Model Ranked by Owner Complaints | The Lemon Index',
         f'{b} ranks #{rk} of {len(brank)} brands by NHTSA owner complaints per car sold (Lemon Index {li}; 100 is average). Most reliable {b}: {best["name"]}. Least: {worst["name"]}.',
         body, ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{b} reliability', "url": BASE + f'/brands/{BSLUG(b)}/'}])
    burls.append(f'/brands/{BSLUG(b)}/')
    cards.append(f'<a class="mc bc" href="/brands/{BSLUG(b)}/"><span class="mc-p">{pimg(ph, top["name"]) if ph else ""}</span><b>{E(b)}</b><small>#{rk}</small>'
                 f'<span class="{"good" if li < 100 else "bad"}">{li}</span></a>')
wtile = ''.join(f'<div class="wt"><b>${per(*w["yrs"][max(w["yrs"])]):,}</b><span>{E(w["short"])}, {max(w["yrs"])}</span></div>' for w in WARR.values())
page('/brands/', 'Most Reliable Car Brands, Ranked by Owner Complaints | The Lemon Index',
     f'All {len(cards)} car brands ranked by NHTSA owner complaints per car sold, best to worst, plus what Ford, GM and Tesla report spending on warranty repairs per vehicle.',
     f'''<div class="pg">{phero('Brands', 'Every brand, ranked.', 'Owner complaints per car sold, best to worst. 100 is the average car.')}
<section><div class="mbs"><div class="mb"><div class="mg">{"".join(cards)}</div></div></div><p class="yc-cap" style="text-align:center">Car images: AI-generated illustrations{ai_note("cars on this page")}</p></section>
<section class="bwar"><p class="te">What automakers tell investors</p><h2>Warranty costs are rising. <span class="h2s">Warranty and recall costs booked per vehicle sold, from each company&#39;s 10-K.</span></h2><div class="wts">{wtile}</div>
<p class="yc-cap">Ford&#39;s rose from $1,675 a vehicle in 2023 to $2,042 in 2025. GM&#39;s from $1,259 to $2,190. Open a brand for the details.</p></section>
{share_line("Every car brand ranked by owner complaints per car sold, best to worst. Free:")}</div>''',
     ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Car brands ranked by reliability", "url": BASE + '/brands/'}])
print('brand pages:', len(burls) + 1)
