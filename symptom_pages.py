# Car symptom pages (11-14, Lemon growth project 2C-2). Run by build.py with exec(), after engine_pages.py (related codes link to code pages)
# and before gap_pages.py (the check engine light hub links here).
# Data: data/symptoms.json (symptoms.py: which symptoms owners describe in NHTSA complaints, on which models and years) + symptom_info.py
# (causes, how serious, can I drive: our own words, kept general) + data/repair_costs.json bills matched by complaint number (in symptoms.json).
# Pages: /symptoms/ (hub) and /symptoms/<id>/. Indexed when 200+ complaints describe the symptom; the rest are noindex,follow and out of the sitemap.
import importlib.util as _ilu, statistics as _st
_sp = _ilu.spec_from_file_location('symptom_info', 'symptom_info.py'); SYI = _ilu.module_from_spec(_sp); _sp.loader.exec_module(SYI)
_sp = _ilu.spec_from_file_location('symptom_defs', 'symptom_defs.py'); SYD = _ilu.module_from_spec(_sp); _sp.loader.exec_module(SYD)
SYM = _load('data/symptoms.json') if os.path.exists('data/symptoms.json') else None
SYM_URLS = []; SYM_NOINDEX = []
SYM_MIN = 200       # complaints describing the symptom before the page is indexed
SYM_DEN = 50        # a model year needs this many complaints in our data before we show a share for it
SYM_SHARE_DEN = 150 # ... and this many (plus 10 matches) to enter the "highest share" list
SYM_COST_MIN = 10   # repair bills (in the symptom's own repair areas) before we show a cost range
# repair-bill areas (data/repair_costs.json) that fit each group; a few symptoms narrow it further
_SYA = {'Brakes': {'Brakes'}, 'Steering and suspension': {'Steering', 'Suspension'}, 'Engine': {'Engine', 'Fuel system', 'Cooling', 'Exhaust & emissions'},
        'Transmission': {'Transmission', '4x4 & axles'}, 'Electrical': {'Electrical'}, 'Heating, AC and body': {'A/C & heat'}}
_SYA_ONE = {'airbag-light-on': {'Airbags'}, 'backup-camera-not-working': {'Screen, radio & camera'}, 'touchscreen-freezing': {'Screen, radio & camera'},
            'power-window-not-working': {'Doors, locks & windows'}, 'car-door-wont-open': {'Doors, locks & windows'}, 'engine-overheating': {'Cooling', 'Engine'},
            'coolant-leak': {'Cooling', 'Engine'}, 'gas-smell': {'Fuel system'}, 'heater-not-working': {'A/C & heat', 'Cooling'}, 'water-leak-inside-car': {'Doors, locks & windows'},
            'sunroof-shattered': set(), 'musty-smell-in-car': {'A/C & heat'}, 'tire-pressure-light-on': set(), 'car-brakes-by-itself': set(),
            'car-wont-start-clicking': {'Electrical', 'Engine'}, 'car-wont-start': {'Electrical', 'Engine', 'Fuel system'}, 'engine-cranks-but-wont-start': {'Engine', 'Fuel system', 'Electrical'},
            'car-battery-keeps-dying': {'Electrical'}, 'clutch-pedal-stuck-to-floor': {'Transmission'}, 'whining-noise-when-accelerating': {'Transmission', '4x4 & axles'},
            'humming-noise-while-driving': {'Suspension', 'Steering', '4x4 & axles', 'Transmission'}, 'burning-smell': {'Engine', 'Brakes', 'Electrical', 'Transmission'}}

# "Is it safe to drive ..." in words people search (names starting "Car " become "if your car ...")
_SYQ = {'grinding-noise-when-braking': 'with grinding brakes', 'squeaky-brakes': 'with squeaky brakes', 'brake-pedal-goes-to-floor': 'if the brake pedal goes to the floor',
        'brakes-not-working': 'if the brakes are not working', 'hard-brake-pedal': 'if the brake pedal is hard to push', 'abs-light-on': 'with the ABS light on',
        'clicking-noise-when-turning': 'with a clicking noise when turning', 'clunking-noise-over-bumps': 'with a clunking noise over bumps',
        'steering-wheel-hard-to-turn': 'if the steering wheel is hard to turn', 'steering-wheel-locked': 'if the steering wheel locked up', 'loose-steering': 'with loose steering',
        'death-wobble': 'with death wobble', 'uneven-tire-wear': 'with uneven tire wear', 'tire-pressure-light-on': 'with the tire pressure light on',
        'engine-misfire': 'with an engine misfire', 'check-engine-light-flashing': 'with the check engine light flashing', 'engine-cranks-but-wont-start': 'after it cranks but won’t start',
        'engine-overheating': 'with an overheating engine', 'engine-knocking': 'with a knocking or ticking engine', 'oil-leak': 'with an oil leak', 'coolant-leak': 'with a coolant leak',
        'burning-smell': 'with a burning smell', 'gas-smell': 'with a gas smell', 'exhaust-smell-in-car': 'with an exhaust smell inside the car',
        'white-smoke-from-exhaust': 'with white smoke from the exhaust', 'smoke-from-under-hood': 'with smoke from under the hood', 'engine-sputtering': 'with a sputtering engine',
        'rpm-goes-up-and-down': 'if the RPM goes up and down', 'transmission-slipping': 'with a slipping transmission', 'transmission-shifting-hard': 'if the transmission shifts hard',
        'transmission-shudder': 'with transmission shudder', 'whining-noise-when-accelerating': 'with a whining noise when accelerating',
        'clutch-pedal-stuck-to-floor': 'if the clutch pedal sticks to the floor', 'headlights-not-working': 'if the headlights are not working',
        'dashboard-warning-lights-on': 'with all the dashboard warning lights on', 'speedometer-not-working': 'if the speedometer is not working',
        'power-window-not-working': 'with a broken power window', 'backup-camera-not-working': 'if the backup camera is not working', 'touchscreen-freezing': 'if the touchscreen keeps freezing',
        'airbag-light-on': 'with the airbag light on', 'ac-blowing-warm-air': 'if the AC is blowing warm air', 'water-leak-inside-car': 'with water leaking inside the car',
        'musty-smell-in-car': 'with a musty smell in the car', 'sunroof-shattered': 'after the sunroof shattered', 'fuel-gauge-not-working': 'if the fuel gauge is not working',
        'humming-noise-while-driving': 'with a humming noise while driving', 'car-door-wont-open': 'if a door won’t open', 'car-wont-start-clicking': 'once a car that just clicks finally starts',
        'car-shaking-and-check-engine-light-on': 'if the car is shaking and the check engine light is on', 'car-rolled-away-in-park': 'after the car rolled away in park', 'heater-not-working': 'if the heater is not working'}
def _sy_safeq(k):
    h = SYD.P[k][0]
    return 'Is it safe to drive ' + (_SYQ[k] if k in _SYQ else 'if your car ' + h[4:] if h.startswith('Car ') else 'with ' + _sy_low(h)) + '?'
def _sy_name(k): return SYD.P[k][0]
SY_CSS = '<style>.crel.sy-ch a{font-family:inherit;font-weight:600}</style>'   # symptom chips in the body font (.crel is the monospace code-chip style)
def _sy_url(k): return f'/symptoms/{k}/'
def _sy_low(h): return h[0].lower() + h[1:] if not h.startswith(('ABS', 'AC ', 'RPM')) else h

def _sy_gauge(s):
    ang = {1: -60, 2: 0, 3: 60}[s]; lab = SYI.SEV[s][0]
    return (f'<figure class="cgauge s{s}" aria-label="How serious: {E(lab)}"><svg viewBox="0 0 200 112" aria-hidden="true">'
            '<path d="M14 100 A86 86 0 0 1 57 25" class="g1"/><path d="M61 23 A86 86 0 0 1 139 23" class="g2"/><path d="M143 25 A86 86 0 0 1 186 100" class="g3"/>'
            f'<g transform="rotate({ang} 100 100)"><line x1="100" y1="100" x2="100" y2="30" class="nd"/></g><circle cx="100" cy="100" r="8" class="hub"/></svg>'
            f'<figcaption>{E(lab)}</figcaption></figure>')

def _sy_q(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)
def _sy_usd(v): return f'${v:,.0f}' if v < 1000 else f'${round(v / 100) * 100:,.0f}'
def _sy_pct(k, n): return f'{k / n * 100:.0f}%' if k / n >= .01 else f'{k / n * 100:.1f}%'

def _sy_costs(k, v):
    areas = _SYA_ONE.get(k, _SYA[SYD.P[k][1]])
    bills = [usd for usd, a, fid, y in v['costs'] if a in areas and usd > 0]
    if len(bills) < SYM_COST_MIN: return None
    return dict(n=len(bills), lo=_sy_q(bills, .25), mid=_st.median(bills), hi=_sy_q(bills, .75), areas=sorted(areas))

def _sy_year_ok(fid, y): return os.path.exists(os.path.join(OUT, 'cars', fid, str(y), 'index.html'))
def _sy_model_ok(fid): return os.path.exists(os.path.join(OUT, 'cars', fid, 'index.html'))

def _sy_related(k, v):
    S = SYM['symptoms']; N = SYM['with_symptom']; out = []
    for j, n in v['rel']:
        if j not in S or n < 20: continue
        lift = n * N / (v['n'] * S[j]['n'])
        if lift >= 1.5: out.append((j, lift))
    out.sort(key=lambda t: -t[1]); rel = [j for j, _ in out[:6]]
    for j in SYD.P:   # top up from the same group so every page links its neighbours
        if len(rel) >= 6: break
        if j != k and j not in rel and SYD.P[j][1] == SYD.P[k][1]: rel.append(j)
    return rel

def _sy_codes(v):
    base = SYM['codes_all']; N = SYM['with_symptom']; out = []
    known = set(globals().get('CODE_URLS', [])) | set(globals().get('CODE_NOINDEX', []))
    for c, n in v['codes']:
        if n < 5 or f'/check-engine-light/{c.lower()}/' not in known: continue
        if n / v['n'] < 2 * base.get(c, n) / N: continue   # only codes clearly more common with this symptom than in symptom complaints overall
        mm = _meaning(c) if '_meaning' in globals() else None
        out.append((c, n, mm['t'] if mm else ''))
    return out[:8]

def _sy_pages():
    if not SYM: return
    S = SYM['symptoms']
    for k, (h1, grp, _p, _n) in SYD.P.items():
        v = S.get(k); info = SYI.I[k]
        if not v or v['n'] < 30: continue
        path = _sy_url(k); n = v['n']; s = info['s']; lab, labt = SYI.SEV[s]; low = _sy_low(h1)
        models = [m for m in v['models'] if m[2] >= 3 and _sy_model_ok(m[0])][:8]
        yrs = [y for y in v['years'] if _sy_year_ok(y[0], y[2])]
        top_count = yrs[:12]
        top_share = sorted([y for y in yrs if y[4] >= SYM_SHARE_DEN and y[3] >= 10], key=lambda y: -y[3] / y[4])[:8]
        topm = models[0][1] if models else ''
        cost = _sy_costs(k, v); rel = _sy_related(k, v); codes = _sy_codes(v)
        # the 3-part answer, then the cars, then everything else folded (the code page pattern)
        body = [f'<article class="study tr2 cp2"><p class="kicker"><a href="/symptoms/">Car symptoms</a> · {E(grp)}</p><h1>{E(h1)}</h1>',
                f'<div class="cpa"><div><span>What it usually means</span><p>{E(info["what"])}</p></div>'
                f'<div><span>How serious</span><p><b>{E(lab)}.</b> {E(info["drive"])}</p></div>'
                f'<div><span>Where a shop starts</span><p>{E(info["causes"][0])}. Then: {E("; ".join(c[:1].lower() + c[1:] for c in info["causes"][1:3]))}.</p></div></div>',
                f'<p class="cpm">Owners describe this in <b>{n:,}</b> complaints to the U.S. government' + (f', most often on the {E(topm)}.' if topm else '.') + '</p>']
        if models:
            cards = ''.join(f'<a class="mc cpc" href="/cars/{i}/"><span class="mc-p">' + (lambda ph: f'<img src="{ph["src"]}" alt="{E(nm)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async">' if ph else '')(aph(i))
                            + f'</span><b>{E(nm)}</b><span class="cpn">{c:,}</span></a>' for i, nm, c in models)
            body.append(f'<h2>Cars owners report it on most</h2><div class="mbs"><div class="mb"><div class="mg cpg">{cards}</div></div></div>'
                        '<p class="note">Complaints describing this symptom, by model, all years. Raw counts, not a failure rate: popular models get more complaints.</p>')
        if top_count:
            rows = ''.join(f'<tr><td><a href="/cars/{i}/{y}/">{y} {E(nm)}</a></td><td>{c:,}</td><td>{_sy_pct(c, d) if d >= SYM_DEN else "–"}</td></tr>' for i, nm, y, c, d in top_count)
            body.append(f'<h2>Model years that report it most</h2><div class="tw"><table class="adv"><thead><tr><th>Model year</th><th>Complaints</th><th>Share</th></tr></thead><tbody>{rows}</tbody></table></div>'
                        '<p class="note">Each row is that model year&#39;s record in NHTSA complaints, not the history of any one car. Share = complaints describing this symptom out of every complaint we hold for that model year'
                        f' (shown when the year has {SYM_DEN}+ complaints).</p>')
        if top_share:
            body.append('<h2>Where it makes up the biggest share</h2><p class="crel sy-ch">' + ' '.join(
                f'<a href="/cars/{i}/{y}/">{y} {E(nm)} · {_sy_pct(c, d)}</a>' for i, nm, y, c, d in top_share) + '</p>'
                f'<p class="note">Model years with {SYM_SHARE_DEN}+ complaints in our data and 10+ describing this symptom, ranked by share. A high share means owners of that year who complained often mentioned it.</p>')
        det = [(f'Common causes of {low}', '<ul class="fx">' + ''.join(f'<li>{E(c)}</li>' for c in info['causes']) + '</ul><p class="yc-cap">General causes, not a diagnosis. A shop should confirm the cause with tests before replacing parts.</p>')]
        now = info['now']
        flags = [(v['crash'], 'mention a crash'), (v['towed'], 'say the car was towed'), (v['fire'], 'mention a fire'), (v['injured'], 'report an injury')]
        fl = [f'{_sy_pct(c, n)} {w}' for c, w in flags if c >= 10 and c / n >= .005]
        det.append((E(_sy_safeq(k)),f'<p><b>{E(lab)}.</b> {E(info["drive"])}</p>' +
                    (('<p>Get help right away if ' + ('; '.join(E(x) for x in now) if now != ['always'] else 'you notice it at all') + '.</p>') if now else '') +
                    (f'<p>Of the {n:,} complaints describing it, {", ".join(fl[:-1]) + " and " + fl[-1] if len(fl) > 1 else fl[0]}.</p>' if fl else '')))
        comps = [(c, x) for c, x in v['comps'] if c and c not in ('Unknown Or Other',)][:4]
        bits = []
        if comps: bits.append('<p>The parts owners filed these complaints under: ' + ', '.join(f'{E(c.lower())} ({_sy_pct(x, n)})' for c, x in comps) + '. A complaint can list more than one.</p>')
        if v.get('miles'): bits.append(f'<p>Median odometer reading when owners reported it: <b>{v["miles"]:,} miles</b>.</p>')
        if v.get('makes'): bits.append('<p>Most reports by make: ' + ', '.join(f'{E(m)} ({c:,})' for m, c in v['makes'][:5] if m) + '.</p>')
        if bits: det.append(('What the complaints show', ''.join(bits)))
        if cost:
            det.append((f'What owners say it cost to fix', f'<p>Repair bills owners named in complaints that describe this symptom ({E(", ".join(a.lower() for a in cost["areas"]))} repairs): '
                        f'the middle half ran <b>{_sy_usd(cost["lo"])} to {_sy_usd(cost["hi"])}</b>, typical <b>{_sy_usd(cost["mid"])}</b>, from {cost["n"]:,} bills.</p>'
                        '<p class="yc-cap">Each figure is one repair bill as an owner wrote it in a complaint, not a quote for your car. Prices vary with the part, the shop and the year.</p>'))
        body.append('<h2>The details</h2>' + ''.join(f'<details class="cpd"><summary>{q}</summary>{h_}</details>' for q, h_ in det))
        if codes:
            body.append('<h2>Engine codes that come up with it</h2><p class="crel">' + ' '.join(f'<a href="/check-engine-light/{c.lower()}/" title="{E(t)}">{c}</a>' for c, x, t in codes) + '</p>'
                        '<p class="note">Trouble codes owners named in these complaints more often than in other symptom complaints. <a href="/check-engine-light/">Look up any code →</a></p>')
        if rel:
            body.append('<h2>Related symptoms</h2><p class="crel sy-ch">' + ' '.join(f'<a href="{_sy_url(j)}">{E(_sy_name(j))}</a>' for j in rel) + '</p>')
        top3 = [m[1] for m in models[:3]]
        faq = [(f'What causes {low}?', info['what'] + ' Common causes: ' + '; '.join(c[:1].lower() + c[1:] for c in info['causes']) + '.'),
               (_sy_safeq(k), f'{lab}. {info["drive"]}')]
        if top3: faq.append((f'Which cars have this problem most?', f'In complaints to NHTSA, owners describe it most on the {", ".join(top3[:-1]) + " and " + top3[-1] if len(top3) > 1 else top3[0]}. These are raw counts, so popular models rank higher; complaints are owner reports, not proof of a defect.'))
        if cost: faq.append(('How much does it cost to fix?', f'In {cost["n"]:,} repair bills owners named in complaints describing it, the middle half ran {_sy_usd(cost["lo"])} to {_sy_usd(cost["hi"])}. The right repair depends on the cause.'))
        body.append('<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq)) + '</section>')
        body.append(f'<p class="note">Counts: NHTSA owner complaints whose text describes this symptom (we matched owners&#39; own wording, then read samples to check the matches). '
                    'A complaint is an owner&#39;s report, not a diagnosis or proof of a defect. Causes and advice are general information in our own words, not repair advice for your car. '
                    '<a href="/symptoms/">Every symptom</a> · <a href="/check-engine-light/">Engine code lookup</a></p></article>')
        hero = (f'<div class="creadout"><div class="cr-code"><span class="cr-sys">{E(grp)} · owner complaints</span><b>{n:,}</b></div>' + _sy_gauge(s) + '</div>')
        ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}]
        tt = f'{h1}: Causes, Is It Safe, Cars That Get It | The Lemon Index'
        if len(tt) > 65 + len(' | The Lemon Index'): tt = f'{h1}: Causes and Cars That Get It | The Lemon Index'
        desc = f'{info["what"]} Common causes, how serious it is, and the models and years owners report it on most in {n:,} NHTSA complaints.'
        page(path, tt, desc, SY_CSS + ''.join(body), ld=ld, vis=hero)
        if n >= SYM_MIN: SYM_URLS.append(path)
        else:
            SYM_NOINDEX.append(path); p_ = os.path.join(OUT, path.strip('/'), 'index.html')
            s_ = open(p_, encoding='utf-8').read(); open(p_, 'w', encoding='utf-8').write(s_.replace('<link rel="canonical"', '<meta name="robots" content="noindex,follow"><link rel="canonical"', 1))
    _sy_hub()
    print('symptom pages', len(SYM_URLS), 'indexed', len(SYM_NOINDEX), 'noindex')

def _sy_card(k):
    v = SYM['symptoms'][k]; s = SYI.I[k]['s']
    return f'<a class="cgc s{s}" href="{_sy_url(k)}"><b>{E(_sy_name(k))}</b><small>{v["n"]:,} complaints</small></a>'   # 11-19 v5: name + count only, causes on the page'

def _sy_live(): return [k for k in SYD.P if _sy_url(k) in SYM_URLS or _sy_url(k) in SYM_NOINDEX]

def _sy_hub():
    live = _sy_live(); S = SYM['symptoms']
    grid = ''
    for g in SYI.GROUPS:
        ks = sorted([k for k in live if SYD.P[k][1] == g], key=lambda k: -S[k]['n'])
        if not ks: continue
        grid += f'<h3 class="sy-g v5-gh">{E(g)}</h3>' + ''.join(_sy_card(k) for k in ks)
    big = sorted(live, key=lambda k: -S[k]['n'])[:3]
    faq = [('What is the most common car symptom in complaints?', f'Among the symptoms we track, owners describe {_sy_low(_sy_name(big[0]))} most ({S[big[0]]["n"]:,} complaints), then {_sy_low(_sy_name(big[1]))} and {_sy_low(_sy_name(big[2]))}.'),
           ('Which symptoms mean I should stop driving?', 'Brakes that fail or a pedal that sinks, steering that locks or goes heavy, overheating, smoke, a fuel smell, a flashing check engine light, a car that stalls or speeds up on its own, and exhaust fumes inside the car. Pull over safely and get help.'),
           ('Is a symptom proof that my car is defective?', 'No. These pages count owner complaints to NHTSA. They show which model years owners report a symptom on, not what is wrong with any one car. A shop has to diagnose your car.')]
    body = (f'<div class="pg v5">' + V5_HERO('Car symptoms', 'What&#39;s your car doing?', 'The usual causes, how serious it is, and the cars owners report it on most.',
                                          line=f'From <b>{SYM["total"]:,}</b> complaints to the U.S. government',
                                          extra='<input class="cf-q v5-q" type="search" placeholder="Search, e.g. brake, smell or noise" aria-label="Filter the symptoms" data-filter="#sygrid">')
            + f'<section class="v5-sec" id="symptoms"><div class="cgrid v5-sy" id="sygrid">{grid}</div><p class="cf-none" hidden>No symptom in this list matches. Try one word, like shake or leak.</p>'
            '<p class="v5-dots"><i class="s1"></i>Get it checked <i class="s2"></i>Fix soon <i class="s3"></i>Stop and get help</p></section>'
            '<div class="cpl v5-pl">' + V5_GO('engine', 'Warning light with a code? Look it up', '/check-engine-light/')
            + V5_BOX('talk', 'Questions', qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq)))
            + V5_BOX('info', 'How we count', f'<p class="yc-cap">We matched owners&#39; own wording in NHTSA complaint text (for example &ldquo;shakes when braking&rdquo;), then read samples of each match to check them. A complaint can describe several symptoms. '
                     f'Pages with fewer than {SYM_MIN} matching complaints stay out of search results. General information, not repair advice for your car.</p>') + '</div></div>')
    ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}]
    page('/symptoms/', 'Car Symptoms: Shakes, Noises, Smells and What They Mean | The Lemon Index',
         'What a shake, noise, smell or warning light usually means, how serious it is, and which cars owners report it on most in NHTSA complaints.',
         body + '<script src="/assets/cardfilter.js?v=1" defer></script>', ld=ld)
    SYM_URLS.insert(0, '/symptoms/')

def sym_cel_html():
    """the check engine light hub: no code? start from the symptom"""
    if not SYM or not SYM_URLS: return ''
    ks = [k for k in ('check-engine-light-flashing', 'car-shaking-and-check-engine-light-on', 'engine-misfire', 'car-shakes-at-idle', 'car-loses-power-while-driving',
                      'car-hesitates-when-accelerating', 'car-stalls-while-driving', 'engine-overheating') if _sy_url(k) in SYM_URLS]
    return (SY_CSS + '<section class="yc" id="symptoms"><h2>No code? Start from the symptom</h2><p class="crel sy-ch">' + ' '.join(f'<a href="{_sy_url(k)}">{E(_sy_name(k))}</a>' for k in ks) +
            '</p><p class="yc-cap"><a href="/symptoms/">Every car symptom →</a> Shakes, noises, smells and warning lights, with the cars owners report them on most.</p></section>')
_sy_pages()
