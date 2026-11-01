# Electric-car pages (10-31, Elijah: "do all 5"). Run by build.py with exec(), so page(), E, plain, bars, stars, FY, CARU are in scope.
# Data: data/ev.json from 3 Lemon Index/ev/ev_data.py (NHTSA complaints, KBB sales estimates, EPA, NHTSA recalls, NHTSA driver-assist crash reports).
# Pages: /electric/ (ranking) + /electric/fires/ /electric/cost/ /electric/problems/ /electric/driver-assist-crashes/ + /electric/<car>/.
EV = json.load(open('data/ev.json', encoding='utf-8'))
EVC = EV['cars']; RK = [c for c in EVC if c.get('rank')]; P = EV['pooled']; SG = EV['sgo']
EPART = {'FORWARD COLLISION AVOIDANCE': 'automatic emergency braking', 'ELECTRICAL SYSTEM': 'electrical', 'VEHICLE SPEED CONTROL': 'cruise and speed control',
         'SERVICE BRAKES': 'brakes', 'STEERING': 'steering', 'LANE DEPARTURE': 'lane assist', 'POWER TRAIN': 'drivetrain', 'VISIBILITY/WIPER': 'wipers and visibility',
         'FUEL/PROPULSION SYSTEM': 'battery and drive system', 'BACK OVER PREVENTION': 'backup camera', 'EXTERIOR LIGHTING': 'lights', 'STRUCTURE': 'body structure',
         'AIR BAGS': 'airbags', 'SEATS': 'seats', 'ENGINE': 'motor and cooling', 'SUSPENSION': 'suspension', 'WHEELS': 'wheels', 'TIRES': 'tires',
         'SEAT BELTS': 'seat belts', 'LATCHES/LOCKS/LINKAGES': 'doors and latches', 'ELECTRONIC STABILITY CONTROL (ESC)': 'stability control', 'PARKING BRAKE': 'parking brake'}
ep = lambda c: EPART.get(c, c.lower())
EVU = lambda c: f'/electric/{c["slug"]}/'
ratio = lambda a, b: f'{a / b:.1f}'.replace('.0', '')
WIN = 'filed with NHTSA by the end of the year after the model year'
SRC_NOTE = ('Sales are Kelley Blue Book estimates for every brand (Tesla doesn\'t report U.S. sales by model). These scores use a shorter window than the main '
            'Lemon Index (complaints filed by the end of the year after the model year), so brand-new EVs like the Cybertruck get a fair, complete window. '
            'That\'s why a Tesla\'s score here differs a little from its main car page.')
cls = lambda v: 'bad' if v > 110 else 'good'
money = lambda v: f'${v:,.0f}'
MON = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
rdate = lambda d: f'{MON[int(d[3:5]) - 1]} {d[6:10]}' if len(d) == 10 else d   # NHTSA dates are DD/MM/YYYY
rkey = lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2]
costr = lambda a: money(a[0]) if a[0] == a[1] else f'{money(a[0])}–{money(a[1])}'
def rng(a, unit=''):
    return '—' if not a else (f'{a[0]:,}{unit}' if a[0] == a[1] else f'{a[0]:,}–{a[1]:,}{unit}')
ev_x = ratio(P['ev']['per100k'], P['gas']['per100k']); ev_x2 = ratio(P['ev']['noadas100k'], P['gas']['noadas100k'])
best, worst = RK[0], RK[-1]
eurls = []

# ---- hub: the ranking
rows = ''.join(f'<tr><td>{c["rank"]}</td><td><a href="{EVU(c)}">{E(c["name"])}</a><small class="muted"> {c["years"]}</small></td><td class="num {cls(c["li"])}">{c["li"]}</td>'
               f'<td class="pw">{plain(c["li"])}</td><td class="num">{c["sold"]:,}{"*" if c["small"] else ""}</td><td>{E(ep(c["issues"][0][0])) if c["issues"] else "—"}</td></tr>' for c in RK)
EFAQ = [('What is the most reliable electric car?', f'By owner complaints per car sold, the {best["name"]} (Lemon Index {best["li"]}), then the {RK[1]["name"]} ({RK[1]["li"]}) and the {RK[2]["name"]} ({RK[2]["li"]}), model years {EV["years"][0]}-{EV["years"][1]}. 100 is the average car.'),
        ('Are electric cars less reliable than gas cars?', f'They draw more safety complaints. Across {len(RK)} EVs, owners filed {P["ev"]["per100k"]} complaints per 100,000 cars sold, against {P["gas"]["per100k"]} for other cars of the same years: about {ev_x} times as many. Much of the gap is driver-assist systems, mostly automatic emergency braking. Without those complaints it\'s about {ev_x2} times.'),
        ('Which electric car has the most problems?', f'The {worst["name"]} ({worst["li"]}), then the {RK[-2]["name"]} ({RK[-2]["li"]}) and the {RK[-3]["name"]} ({RK[-3]["li"]}). Their top complaint area: {ep(worst["issues"][0][0])}.'),
        ('Do electric cars catch fire more than gas cars?', f'Fire complaints are rare for both: {P["ev"]["fire100k"]} per 100,000 EVs sold and {P["gas"]["fire100k"]} per 100,000 other cars, in the first year or two. See the fire page for the details.'),
        ('Why does Tesla score badly?', 'Mostly one system. About 6 in 10 Model 3 and Model Y complaints are about automatic emergency braking, the car braking hard for nothing ("phantom braking"). Take those out and both rank among the best EVs.')]
efaq = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in EFAQ)
topics = [('/electric/fires/', 'Do electric cars catch fire more?', f'{P["ev"]["fire100k"]} fire complaints per 100,000 EVs vs {P["gas"]["fire100k"]} for other cars'),
          ('/electric/cost/', 'What an EV costs to drive per year', 'EPA yearly fuel cost for every EV vs its gas twin or rival'),
          ('/electric/problems/', 'The most common EV problems', f'automatic emergency braking is {round(P["ev"]["comps"].get("FORWARD COLLISION AVOIDANCE", 0))}% of EV complaints'),
          ('/electric/driver-assist-crashes/', 'Autopilot and driver-assist crash reports', f'Tesla filed {SG["tesla_share"]:.0f}% of them. Here\'s why that isn\'t the whole story')]
cards = ''.join(f'<a class="card" href="{u}"><h2>{E(h)}</h2><p>{E(s)}</p></a>' for u, h, s in topics)
page('/electric/', 'The Most Reliable Electric Cars, Ranked by Owner Complaints | The Lemon Index',
     f'{len(RK)} electric cars ranked by NHTSA safety complaints per car sold, model years {EV["years"][0]}-{EV["years"][1]}. Most reliable: {best["name"]}. Least: {worst["name"]}. Plus fires, yearly cost and driver-assist crashes.', f'''
<article class="study"><p class="kicker">Electric cars · {TODAY}</p><h1>The most reliable electric cars, ranked by owner complaints</h1>
<p class="lede">Every electric car we ranked drew more complaints per car sold than the average car. The <b>{E(best["name"])}</b> came closest. The <b>{E(worst["name"])}</b> drew {worst["li"] / 100:.0f} times the average.</p>
<div class="stats"><div><b>{len(RK)}</b><span>electric cars ranked</span></div><div><b>{P["ev"]["sold"]:,}</b><span>sold in the U.S., {EV["years"][0]}-{EV["years"][1]}</span></div><div><b>{ev_x}×</b><span>the complaints of other cars, per car sold</span></div><div><b>{best["li"]}</b><span>best score: {E(best["name"])}</span></div></div>
<p class="sub">Lemon Index = safety complaints {WIN}, per car sold, against the average car of the same model year. <b>100 is average, lower is better.</b></p>
<div class="tw"><table><thead><tr><th>#</th><th>Electric car</th><th>Index</th><th>Compared with average</th><th>Sold in the U.S.</th><th>Top complaint</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">* Under 50,000 sold: a smaller sample, so read it as a rough score. What it means for you: an EV's software and driver-assist features cause many of its complaints, so check the top complaint before you buy. {E(SRC_NOTE)}</p>
<h2>More electric-car data</h2><div class="stack">{cards}</div>
<section class="faq"><h2>Questions</h2>{efaq}</section></article>''', kind='article',
     ld=[{"@context": "https://schema.org", "@type": "Dataset", "name": "Electric car reliability by NHTSA complaints per car sold", "url": BASE + '/electric/', "creator": {"@type": "Organization", "name": "The Lemon Index"},
          "description": f"{len(RK)} electric cars, model years {EV['years'][0]}-{EV['years'][1]}, ranked by NHTSA safety complaints per U.S. sale.", "license": "https://creativecommons.org/licenses/by/4.0/", "dateModified": TODAY},
         {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in EFAQ]}])
eurls.append('/electric/')

# ---- fires
fr = sorted([c for c in RK], key=lambda c: (-c['recalls_fire'], -c['fire100k']))
frows = ''.join(f'<tr><td><a href="{EVU(c)}">{E(c["name"])}</a></td><td class="num">{c["fire"]}</td><td class="num">{c["fire100k"]}</td><td class="num">{c["recalls_fire"]} of {len(c["recalls"])}</td></tr>' for c in fr)
page('/electric/fires/', 'Do Electric Cars Catch Fire More Than Gas Cars? What Owner Complaints Show | The Lemon Index',
     f'Fire complaints per 100,000 cars sold: {P["ev"]["fire100k"]} for electric cars, {P["gas"]["fire100k"]} for other cars (model years {EV["years"][0]}-{EV["years"][1]}). Plus every EV\'s fire-related recalls.', f'''
<article class="study"><p class="kicker"><a href="/electric/">Electric cars</a> · Fires</p><h1>Do electric cars catch fire more than gas cars?</h1>
<p class="lede">Fire complaints are rare for both. In their first year or two, owners reported a fire in <b>{P["ev"]["fire100k"]}</b> of every 100,000 electric cars sold, and in <b>{P["gas"]["fire100k"]}</b> of every 100,000 other cars.</p>
<div class="stats"><div><b>{P["ev"]["fire"]}</b><span>EV complaints that report a fire</span></div><div><b>{P["ev"]["fire100k"]}</b><span>per 100,000 EVs sold</span></div><div><b>{P["gas"]["fire100k"]}</b><span>per 100,000 other cars sold</span></div><div><b>{sum(c["recalls_fire"] for c in RK)}</b><span>EV recalls that mention fire</span></div></div>
<p>So EVs come out a little higher per car, but the numbers are tiny: {P["ev"]["fire"]} fire complaints across {P["ev"]["sold"]:,} electric cars. A handful of reports either way would flip it. What the data doesn't support is the idea that EVs burn far more often in normal use.</p>
<h2>Fire complaints and fire recalls, by EV</h2><div class="tw"><table><thead><tr><th>Electric car</th><th>Fire complaints</th><th>Per 100,000 sold</th><th>Recalls that mention fire</th></tr></thead><tbody>{frows}</tbody></table></div>
<p class="note">What it means for you: the bigger fire risk is an open recall. Check yours at nhtsa.gov/recalls with your VIN, and get recall repairs done. The Chevrolet Bolt's battery recall replaced battery packs for that reason.</p>
<h2>What this does and doesn't cover</h2><p>These are complaints in which the owner reported a fire, {WIN}, for model years {EV["years"][0]}-{EV["years"][1]}. NHTSA doesn\'t confirm the cause. It doesn\'t cover fires after crashes that weren\'t reported to NHTSA, or older cars, where battery and engine fires both become more common. Recalls come from NHTSA\'s recall database: a recall counts when its summary or risk mentions fire.</p></article>''', kind='article',
     ld=[{"@context": "https://schema.org", "@type": "Article", "headline": "Do electric cars catch fire more than gas cars?", "datePublished": TODAY, "dateModified": TODAY, "author": {"@type": "Organization", "name": "The Lemon Index"}}])
eurls.append('/electric/fires/')

# ---- yearly cost
cc = sorted([c for c in EVC if c.get('epa') and c.get('saves') is not None], key=lambda c: -c['saves'])
crow = ''.join(f'<tr><td><a href="{EVU(c)}">{E(c["name"])}</a></td><td class="num">{rng(c["epa"]["range"], " mi")}</td><td class="num">{costr(c["epa"]["cost"])}</td>'
               f'<td>{E(c["twin"])}{" (gas twin)" if c["twin_true"] else ""}</td><td class="num">{costr(c["twin_epa"]["cost"])}</td><td class="num good">{money(c["saves"])}</td></tr>' for c in cc)
lo, hi = min(c['saves'] for c in cc), max(c['saves'] for c in cc)
page('/electric/cost/', 'Electric vs Gas Car: Yearly Fuel Cost, Model by Model (EPA) | The Lemon Index',
     f'What every popular electric car costs to charge per year vs its gas twin or rival, from EPA estimates. Savings run from {money(lo)} to {money(hi)} a year.', f'''
<article class="study"><p class="kicker"><a href="/electric/">Electric cars</a> · Cost</p><h1>Electric vs gas: what each one costs to drive per year</h1>
<p class="lede">By the EPA's numbers, every electric car here costs less to fuel than its gas twin or rival: <b>{money(lo)} to {money(hi)} less a year</b>.</p>
<div class="tw"><table><thead><tr><th>Electric car</th><th>EPA range</th><th>Yearly charging cost</th><th>Compared with</th><th>Its yearly gas cost</th><th>EV saves per year</th></tr></thead><tbody>{crow}</tbody></table></div>
<p class="note">EPA estimates for the newest model year listed (mostly 2025): 15,000 miles a year, 55% city driving, at national average electricity and gas prices. Ranges show the versions sold. Charging at home is usually cheaper than fast-charging on the road, so a road-trip-heavy driver saves less.</p>
<p>What it means for you: the fuel savings are real, but check the price gap and the score. An EV that saves {money(round(sum(c["saves"] for c in cc) / len(cc), -2))} a year but spends time at the dealer for repairs can cost you more in hassle than it saves. <a href="/electric/">See each EV\'s reliability score</a>.</p></article>''', kind='article',
     ld=[{"@context": "https://schema.org", "@type": "Article", "headline": "Electric vs gas: what each one costs to drive per year", "datePublished": TODAY, "dateModified": TODAY, "author": {"@type": "Organization", "name": "The Lemon Index"}}])
eurls.append('/electric/cost/')

# ---- problems
keys = [k for k in P['ev']['comps'] if k in P['gas']['comps']][:10]
prow = ''.join(f'<tr><td>{E(ep(k))}</td><td class="num">{P["ev"]["comps"][k]:.0f}%</td><td class="num">{P["gas"]["comps"][k]:.0f}%</td></tr>' for k in keys)
cprow = ''.join(f'<tr><td><a href="{EVU(c)}">{E(c["name"])}</a></td><td>{E(", ".join(f"{ep(p)} {k}%" for p, k in c["issues"][:3]))}</td><td class="num">{c["per100k"]}</td><td class="num">{c["noadas100k"]}</td></tr>' for c in sorted(RK, key=lambda c: c['noadas100k']))
page('/electric/problems/', 'The Most Common Electric Car Problems, From Owner Complaints | The Lemon Index',
     f'What owners complain about on electric cars vs gas cars, and every EV\'s top problems. Automatic emergency braking is {P["ev"]["comps"].get("FORWARD COLLISION AVOIDANCE", 0):.0f}% of EV complaints.', f'''
<article class="study"><p class="kicker"><a href="/electric/">Electric cars</a> · Problems</p><h1>The most common electric car problems</h1>
<p class="lede">The #1 EV complaint isn\'t the battery. It\'s <b>automatic emergency braking</b>: {P["ev"]["comps"].get("FORWARD COLLISION AVOIDANCE", 0):.0f}% of EV complaints, against {P["gas"]["comps"].get("FORWARD COLLISION AVOIDANCE", 0):.0f}% for other cars. Owners describe the car braking hard for nothing.</p>
<h2>EVs vs other cars: share of complaints</h2><div class="tw"><table><thead><tr><th>Problem area</th><th>Electric cars</th><th>Other cars</th></tr></thead><tbody>{prow}</tbody></table></div>
<p class="note">One complaint can name several areas, so the shares add up to more than 100%. Engines and transmissions sit near the top for gas cars and barely show up for EVs.</p>
<h2>Without the driver-assist complaints</h2><p>Take out complaints about automatic emergency braking, lane assist, blind-spot and backup sensors, and EVs still draw more: <b>{P["ev"]["noadas100k"]}</b> per 100,000 sold against <b>{P["gas"]["noadas100k"]}</b> for other cars. The Tesla Model 3 and Model Y move from the bottom half to near the top.</p>
<div class="tw"><table><thead><tr><th>Electric car</th><th>Top problems</th><th>Complaints per 100,000</th><th>Without driver-assist</th></tr></thead><tbody>{cprow}</tbody></table></div>
<p class="note">Sorted by complaints without driver-assist, fewest first. Complaints {WIN}, model years {EV["years"][0]}-{EV["years"][1]}.</p></article>''', kind='article',
     ld=[{"@context": "https://schema.org", "@type": "Article", "headline": "The most common electric car problems", "datePublished": TODAY, "dateModified": TODAY, "author": {"@type": "Organization", "name": "The Lemon Index"}}])
eurls.append('/electric/problems/')

# ---- driver-assist crash reports (NHTSA Standing General Order, Level 2)
srow = ''.join(f'<tr><td>{E(m["make"])}</td><td class="num">{m["n"]:,}</td><td class="num">{m["fatal"]}</td><td class="num">{m["tele"]}%</td></tr>' for m in SG['by_make'])
tm = ' · '.join(f'{E(k)} {v:,}' for k, v in SG['tesla_models'].items() if v >= 50)
page('/electric/driver-assist-crashes/', 'Tesla Autopilot Crash Reports: What NHTSA\'s Data Shows (and Doesn\'t) | The Lemon Index',
     f'{SG["total"]:,} crashes involving Level 2 driver assist were reported to NHTSA since 2021. Tesla filed {SG["tesla_share"]:.0f}%. Why that isn\'t a per-mile safety ranking.', f'''
<article class="study"><p class="kicker"><a href="/electric/">Electric cars</a> · Driver assist</p><h1>Tesla Autopilot crash reports: what the government data shows</h1>
<p class="lede">Since 2021, automakers have reported <b>{SG["total"]:,}</b> crashes in which a driver-assist system like Autopilot or Super Cruise was in use. Tesla filed <b>{SG["tesla_share"]:.0f}%</b> of them.</p>
<div class="stats"><div><b>{SG["total"]:,}</b><span>crash reports, {SG["years"][0]}-{SG["years"][1]}</span></div><div><b>{SG["tesla_share"]:.0f}%</b><span>from Tesla</span></div><div><b>{SG["tesla_fatal"]}</b><span>of {SG["fatal"]} reported deaths were in a Tesla</span></div><div><b>{SG["tele_tesla"]}%</b><span>of Tesla reports came from the car itself</span></div></div>
<h2>Why that isn\'t a safety ranking</h2><ol class="beats"><li><b>Teslas report themselves.</b> {SG["tele_tesla"]}% of Tesla\'s reports came from the car\'s own data connection. For other brands it was {SG["tele_other"]}%: most of them hear about a crash only if the owner complains or sues. A brand that doesn\'t get the data can\'t report it.</li>
<li><b>No miles.</b> The reports don\'t say how many miles each system drove. Tesla has the most cars with driver assist on the road, and owners use it a lot. More use means more crashes even at the same rate.</li>
<li><b>Reported, not proven.</b> A report means the system was on within 30 seconds of the crash. It doesn\'t say the system caused it. NHTSA itself warns against comparing brands with these reports.</li></ol>
<h2>Reports by brand</h2><div class="tw"><table><thead><tr><th>Brand</th><th>Crash reports</th><th>Deaths reported</th><th>Reports from the car\'s own data</th></tr></thead><tbody>{srow}</tbody></table></div>
<p class="note">Tesla by model: {tm}. Level 2 driver assist only (Autopilot, Full Self-Driving (Supervised), Super Cruise, BlueCruise and similar), not robotaxis. NHTSA Standing General Order 2021-01 files (2021-2025 archive and the current file, updated October 2026). Duplicate and updated reports of the same crash are counted once.</p>
<p>What it means for you: these systems need your eyes on the road. The data can\'t say which brand\'s system is safest. It does show that crashes happen with all of them on.</p></article>''', kind='article',
     ld=[{"@context": "https://schema.org", "@type": "Article", "headline": "Tesla Autopilot crash reports: what the government data shows", "datePublished": TODAY, "dateModified": TODAY, "author": {"@type": "Organization", "name": "The Lemon Index"}}])
eurls.append('/electric/driver-assist-crashes/')

# ---- one page per EV
SGM = {'Tesla Model 3': 'Model 3', 'Tesla Model Y': 'Model Y', 'Tesla Model S': 'Model S', 'Tesla Model X': 'Model X', 'Tesla Cybertruck': 'Cybertruck'}
for c in EVC:
    yrs = ''.join(f'<tr><td>{y["y"]}</td><td class="num {cls(y["li"])}">{y["li"]}</td><td class="pw">{plain(y["li"])}</td><td class="num">{y["n"]:,}</td><td class="num">{y["sold"]:,}</td></tr>' for y in c['years_detail'])
    iss = ''.join(f'<li><b>{E(ep(p))}</b>: {k}% of complaints</li>' for p, k in c['issues'])
    rec = ''.join(f'<li><b>{E(RPART(r["part"]))}</b> <small>{rdate(r["date"])}</small><br>{E(rsum(r))}{" <b class=\"bad\">Fire risk.</b>" if r["fire"] else ""} <small class="muted">NHTSA {E(r["id"])}</small></li>' for r in sorted(c['recalls'], key=rkey, reverse=True)[:8])
    e, t = c.get('epa'), c.get('twin_epa')
    cost = (f'<h2>Range and yearly cost</h2><div class="tw"><table><tbody><tr><td>EPA range ({e["year"]})</td><td class="num">{rng(e["range"], " miles")}</td></tr>'
            f'<tr><td>Electricity use</td><td class="num">{rng(e["kwh100"])} kWh per 100 miles</td></tr><tr><td>Yearly charging cost (EPA)</td><td class="num">{costr(e["cost"])}</td></tr>'
            + (f'<tr><td>{E(c["twin"])}{" (gas twin)" if c["twin_true"] else ""}, yearly gas cost</td><td class="num">{costr(t["cost"])}</td></tr><tr><td>Saves per year</td><td class="num good">about {money(c["saves"])}</td></tr>' if c.get('saves') is not None else '')
            + '</tbody></table></div><p class="note">EPA estimate: 15,000 miles a year at national average prices. <a href="/electric/cost/">Every EV\'s cost →</a></p>') if e and e.get('cost') else ''
    sg = f'<p>Driver-assist crash reports to NHTSA involving a {E(c["name"])}: <b>{SG["tesla_models"].get(SGM[c["name"]], 0):,}</b> since 2021. <a href="/electric/driver-assist-crashes/">What those reports do and don\'t show →</a></p>' if c['name'] in SGM else ''
    main = f' <a href="{CARU(FY[c["slug"]])}">Its main car page</a> covers older model years.' if c['slug'] in FY else ''
    rank = f'#{c["rank"]} of {len(RK)} electric cars' if c.get('rank') else f'not ranked (under {EV["min_sold"]:,} sold)'
    rec_note = f'{len(c["recalls"])} recalls for model years {c["years"]}' + (f', {c["recalls_fire"]} mentioning fire' if c['recalls_fire'] else '')
    title = f'{c["name"]} Reliability: Problems, Recalls and Range ({c["years"]})'
    page(EVU(c), title + ' | The Lemon Index',
         f'{c["name"]}: Lemon Index {c["li"]} ({plain(c["li"])}), {rank}. Top problem: {ep(c["issues"][0][0]) if c["issues"] else "n/a"}. Recalls, fire complaints, EPA range and yearly cost.', f'''
<article class="study"><p class="kicker"><a href="/electric/">Electric cars</a> · {E(c["name"])}</p><h1>{E(c["name"])} reliability, {c["years"]}</h1>
<p class="lede">The {E(c["name"])} drew <b>{plain(c["li"])}</b>: {rank}.{main}</p>
<div class="stats"><div><b class="{cls(c["li"])}">{c["li"]}</b><span>Lemon Index (100 = average car)</span></div><div><b>{c["per100k"]}</b><span>complaints per 100,000 sold</span></div><div><b>{c["noadas100k"]}</b><span>without driver-assist complaints</span></div><div><b>{c["sold"]:,}</b><span>sold in the U.S., {c["years"]}{" (small sample)" if c["small"] else ""}</span></div></div>
<h2>Year by year</h2><div class="tw"><table><thead><tr><th>Model year</th><th>Index</th><th>Compared with average</th><th>Complaints</th><th>Sold</th></tr></thead><tbody>{yrs}</tbody></table></div>
<h2>Top problems</h2><ul>{iss}</ul>
<p>Fire complaints: <b>{c["fire"]}</b> ({c["fire100k"]} per 100,000 sold; all EVs average {P["ev"]["fire100k"]}). <a href="/electric/fires/">EV fires vs gas →</a></p>
{cost}
<h2>Recalls</h2><p>{rec_note}.{" The newest:" if rec else ""}</p><ul class="recalls">{rec}</ul>
{sg}
<p class="note">Complaints {WIN}. {E(SRC_NOTE)} Sales source: {E(c["src"])}.</p></article>''', kind='article',
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": BASE + EVU(c)}])
    eurls.append(EVU(c))
print('electric pages:', len(eurls))
