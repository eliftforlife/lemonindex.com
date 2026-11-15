# 11-14 growth plan 2D-1: repair cost pages, from what owners reported paying (data/repair_pages.json, data_repair_pages.py).
# exec'd by build.py twice:
#   RCP = 'hooks'  before the car pages: the data, plus the links car pages show (model page row, year page Related list)
#   RCP = 'pages'  near the end: /repair-cost/ (hub), /repair-cost/<repair>/ and /repair-cost/<repair>/<model>/
# Rules (plan 2D-1 + GROWTH CHUNK RULES.md):
#   - a model page only where owners reported 5+ bills for that repair on that model (RC_MIN); none below it
#   - a repair page is built when it has 15+ reports or a model page under it, and indexed only with 30+ reports from 5+ models;
#     the rest are noindex,follow and left out of the sitemap
#   - every number is "owners reported", with its sample size, its source (NHTSA complaint numbers, YouTube video + second) and the
#     same method as the year pages' cost blocks (repair_costs.py): the middle (median) and the middle half of the bills
#   - links: the model and year pages, the engine pages (CAR_ENG), engine code pages that exist, symptom pages if live
# CSS: assets/rcp.css (prefix rcp-), linked from the pages themselves.
import json as _rcj, os as _rcos, re as _rcre, statistics as _rcst
if RCP == 'hooks':
    _RCD = _rcj.load(open('data/repair_pages.json', encoding='utf-8')) if _rcos.path.exists('data/repair_pages.json') else {'repairs': {}, 'pts': []}
    RC_NAME = _RCD['repairs']; RC_MIN = 5; RC_HUB_BUILD = 15; RC_HUB_IDX = (30, 5)
    RC_BY = {}   # repair -> model id -> [points]
    for _p in _RCD['pts']:
        if _p[1] in FY: RC_BY.setdefault(_p[0], {}).setdefault(_p[1], []).append(_p)
    RC_MS = lambda fid: fid.replace('/', '-')   # one URL segment ('mercedes-benz-m/gle' -> 'mercedes-benz-m-gle')
    RC_N = {s: sum(len(v) for v in m.values()) for s, m in RC_BY.items()}
    RC_MODELP = {s: {fid for fid, v in m.items() if len(v) >= RC_MIN} for s, m in RC_BY.items()}
    RC_HUBS = {s for s in RC_BY if RC_N[s] >= RC_HUB_BUILD or RC_MODELP[s]}
    RC_HUB_OK = lambda s: RC_N[s] >= RC_HUB_IDX[0] and len(RC_BY[s]) >= RC_HUB_IDX[1]
    # the words people search: "<thing> cost"
    _RCQ = {'transmission-replacement': 'Transmission replacement', 'engine-replacement': 'Engine replacement', 'brakes': 'Brake repair',
            'tcm': 'TCM replacement', 'ecm': 'ECM (engine computer) replacement', 'tipm': 'TIPM replacement', 'bcm': 'BCM replacement',
            'abs-module': 'ABS module replacement', 'struts': 'Strut and shock replacement', 'air-suspension': 'Air suspension repair',
            'infotainment': 'Radio and infotainment screen repair', 'evap': 'EVAP system repair', 'differential': 'Differential repair',
            'wiring-harness': 'Wiring harness repair', 'airbag-module': 'Airbag module and clock spring replacement', 'clutch': 'Clutch replacement',
            'battery': 'Car battery replacement', 'brake-booster': 'Brake booster replacement', 'ball-joints': 'Ball joint replacement',
            'control-arms': 'Control arm replacement', 'lifters': 'Lifter replacement', 'cam-phaser': 'Cam phaser replacement',
            'fuel-injectors': 'Fuel injector replacement', 'ignition-coils': 'Ignition coil replacement', 'spark-plugs': 'Spark plug replacement',
            'tie-rods': 'Tie rod replacement', 'engine-mounts': 'Engine mount replacement', 'window-regulator': 'Window regulator replacement',
            'door-lock-actuator': 'Door lock actuator replacement', 'egr': 'EGR valve replacement', 'dpf': 'DPF replacement',
            'oxygen-sensor': 'O2 sensor replacement', 'maf-sensor': 'MAF sensor replacement', 'valve-body': 'Valve body replacement',
            'steering-column': 'Steering column repair', 'cv-axle': 'CV axle replacement', 'hybrid-battery': 'Hybrid battery replacement',
            'backup-camera': 'Backup camera repair', 'ac-compressor': 'AC compressor replacement', 'ac-condenser': 'AC condenser replacement',
            'ac-evaporator': 'AC evaporator replacement'}
    RC_Q = lambda s: _RCQ.get(s) or (RC_NAME[s] + ' replacement')
    RC_LOW = lambda q: q[0].lower() + q[1:] if q[1:2].islower() else q   # "Water pump replacement" -> "water pump ..."; "TCM ..." stays
    RC_HUBU = lambda s: f'/repair-cost/{s}/'
    RC_MU = lambda s, fid: f'/repair-cost/{s}/{RC_MS(fid)}/'
    def RC_LINKS(fid, y=None):
        """[(url, repair, reports)] for this model's repair pages, most reports first (y: only repairs owners of that year reported)"""
        out = [(RC_MU(s, fid), s, len(m[fid])) for s, m in RC_BY.items() if s in RC_HUBS and fid in RC_MODELP[s]
               and (y is None or any(p[2] == y for p in m[fid]))]
        return sorted(out, key=lambda t: (-t[2], t[1]))
    def RC_ROW(fid):
        """'What owners paid for repairs' chips on the model page (appended after the page's date hash, like the code search)"""
        ls = RC_LINKS(fid)
        if not ls: return ''
        nm = FY[fid]['name']
        return (f'<nav class="n3-row rcp-row" aria-label="Repair costs">{EU_CSS if "EU_CSS" in globals() else ""}<p class="n3-h">What {E(nm)} owners paid for repairs</p><div class="n3-cs">'
                + ''.join(f'<a class="n3-c" href="{u}"><b>{E(RC_Q(s))}</b><small>{n} owner reports</small></a>' for u, s, n in ls[:8])
                + '</div>' + (('<p class="n3-n">More: ' + ' · '.join(f'<a href="{u}">{E(RC_LOW(RC_Q(s)))}</a> ({n})' for u, s, n in ls[8:]) + '</p>') if ls[8:] else '') + '<p class="n3-n">Repair bills owners named in complaints to NHTSA and said out loud in YouTube videos. <a href="/repair-cost/">Every repair cost →</a></p></nav>')

if RCP == 'pages':
    os.makedirs(os.path.join(OUT, 'repair-cost'), exist_ok=True)
    RC_URLS = []; RC_NOINDEX = []
    _q, _r = RCQ._q, RCQ._r
    _CSS = '<link rel="stylesheet" href="/assets/rcp.css?v=1">'
    _GROUPS = [
        ('Engine', 'engine-replacement timing-chain timing-belt head-gasket turbo lifters cam-phaser intake-manifold valve-cover-gasket oil-pan oil-cooler rear-main-seal engine-mounts spark-plugs ignition-coils fuel-pump fuel-injectors throttle-body crank-sensor cam-sensor maf-sensor'),
        ('Transmission and drivetrain', 'transmission-replacement torque-converter valve-body tcm clutch transfer-case differential cv-axle driveshaft'),
        ('Brakes, steering and suspension', 'brakes abs-module brake-booster master-cylinder steering-rack power-steering-pump steering-column tie-rods wheel-bearing ball-joints control-arms struts air-suspension'),
        ('Cooling and A/C', 'water-pump radiator thermostat ac-compressor ac-condenser ac-evaporator heater-core blend-door'),
        ('Electrical and tech', 'battery alternator starter hybrid-battery ecm tipm bcm wiring-harness infotainment backup-camera airbag-module window-regulator door-lock-actuator'),
        ('Exhaust and emissions', 'catalytic-converter oxygen-sensor egr dpf evap')]
    _GRP = {s: g for g, ss in _GROUPS for s in ss.split()}
    # engine codes that commonly point a shop toward the repair (standard SAE J2012 code meanings); shown only when the code has a page
    _CODES = {'catalytic-converter': 'P0420 P0430', 'oxygen-sensor': 'P0130 P0133 P0135 P0136 P0141 P0155', 'turbo': 'P0299 P0234',
              'timing-chain': 'P0016 P0017 P0008 P0009 P0018 P0019', 'cam-phaser': 'P0011 P0014 P0021 P0016',
              'ignition-coils': 'P0300 P0301 P0302 P0303 P0304 P0305 P0306 P0351 P0352', 'spark-plugs': 'P0300 P0301 P0302 P0303 P0304',
              'throttle-body': 'P2135 P2111 P2112 P2101 P2119 P0121 P0122', 'evap': 'P0455 P0456 P0442 P0441 P0446 P0496',
              'maf-sensor': 'P0101 P0102 P0103', 'egr': 'P0401 P0400 P0402 P0404', 'thermostat': 'P0128',
              'transmission-replacement': 'P0700 P0730 P0715 P0720 P0731 P0732 P0733 P0734', 'torque-converter': 'P0741 P0740',
              'valve-body': 'P0750 P0755 P0760 P0700', 'tcm': 'P0700 P0613', 'crank-sensor': 'P0335 P0336', 'cam-sensor': 'P0340 P0341 P0345',
              'fuel-pump': 'P0087 P0230 P0190 P0191', 'fuel-injectors': 'P0201 P0202 P0203 P0204 P0205 P0206', 'alternator': 'P0562 P0620 P0622',
              'dpf': 'P2002 P244A P2463'}
    # the failure names data_top_fails.py counts in owner complaints (how often owners of a model year report the failure itself)
    _TF = {'water-pump': ('Water pump',), 'head-gasket': ('Head gasket',), 'turbo': ('Turbocharger',), 'timing-chain': ('Timing chain',),
           'cam-phaser': ('Timing chain',), 'catalytic-converter': ('Catalytic converter',), 'ac-compressor': ('A/C compressor',),
           'ac-condenser': ('A/C condenser',), 'fuel-pump': ('Fuel pump',), 'transmission-replacement': ('Transmission failure',),
           'torque-converter': ('Torque converter',), 'engine-replacement': ('Engine failure',), 'steering-rack': ('Steering rack / power steering',),
           'power-steering-pump': ('Steering rack / power steering',), 'throttle-body': ('Throttle body / loss of power',), 'alternator': ('Alternator',),
           'starter': ('Starter',), 'ignition-coils': ('Ignition coils / misfire',), 'abs-module': ('Brakes: ABS module / pump',),
           'brake-booster': ('Brake booster / hard pedal',), 'wheel-bearing': ('Wheel bearing',), 'ball-joints': ('Ball joint / control arm',),
           'control-arms': ('Ball joint / control arm',), 'struts': ('Struts / shocks',), 'door-lock-actuator': ('Door lock actuator',),
           'window-regulator': ('Power window regulator',), 'infotainment': ('Infotainment screen / radio',), 'backup-camera': ('Backup camera',),
           'hybrid-battery': ('Hybrid battery / inverter',), 'battery': ('Battery drain / dead battery',)}
    _TOPF = TOPF if 'TOPF' in globals() else {}
    _SYM = _rcos.path.exists(_rcos.path.join(OUT, 'symptoms', 'index.html'))   # the symptom pages (growth plan 2C), linked once they're live
    _M = lambda v: f'${v:,.0f}'
    _span = lambda a, b: f'{a}–{b}' if a != b else str(a)

    def _stats(pts):
        vs = [p[5] for p in pts]
        return dict(n=len(vs), med=_rcst.median(vs), lo=_q(vs, .25), hi=_q(vs, .75), mn=min(vs), mx=max(vs),
                    nn=sum(1 for p in pts if p[6] == 'n'), ny=sum(1 for p in pts if p[6] == 'y'))
    def _src_line(st):
        a = []
        if st['nn']: a.append(f'{st["nn"]:,} complaint{"s" * (st["nn"] != 1)} to NHTSA')
        if st['ny']: a.append(f'{st["ny"]:,} YouTube video{"s" * (st["ny"] != 1)}')
        return ' and '.join(a)
    def _readout(st, label):
        """the signature block: the middle bill big, the middle half as a bar on the full spread"""
        top = max(st['mx'], 1); L = lambda v: max(0, min(100, round(v / top * 100, 1)))
        return (f'{_CSS}<div class="rcp-read" role="img" aria-label="{E(label)}: owners reported a median of {_r(st["med"])}, middle half {_r(st["lo"])} to {_r(st["hi"])}, from {st["n"]} reports">'
                f'<div class="rcp-big"><span>Owners reported</span><b>{_r(st["med"])}</b><small>the middle bill · {st["n"]:,} reports</small></div>'
                f'<div class="rcp-bar" aria-hidden="true"><span class="rcp-track"><i style="left:{L(st["lo"])}%;width:{max(2, L(st["hi"]) - L(st["lo"]))}%"></i><em style="left:{L(st["med"])}%"></em></span>'
                f'<span class="rcp-ax"><small>{_r(st["mn"])}</small><small>middle half {_r(st["lo"])}–{_r(st["hi"])}</small><small>{_r(st["mx"])}</small></span></div></div>')
    _BINS = [(0, 500, 'Under $500'), (500, 1000, '$500–$1,000'), (1000, 2500, '$1,000–$2,500'), (2500, 5000, '$2,500–$5,000'), (5000, 10 ** 9, '$5,000 and up')]
    def _hist(pts):
        n = len(pts); rows = [(lab, sum(1 for p in pts if a <= p[5] < b)) for a, b, lab in _BINS]
        mx = max(k for _, k in rows) or 1
        return ('<ul class="rcp-hist">' + ''.join(f'<li><span>{lab}</span><span class="rcp-hb"><i style="width:{round(k / mx * 100) if k else 0}%"></i></span><b>{round(k / n * 100)}%</b></li>' for lab, k in rows)
                + f'</ul><p class="yc-cap">Share of the {n:,} owner reports in each price band.</p>')
    def _proof(pts):
        nh = sorted({p[7] for p in pts if p[6] == 'n'}, key=lambda o: -int(o))[:12]
        yt = []; seen = set()
        for p in sorted((p for p in pts if p[6] == 'y'), key=lambda p: p[5]):
            if p[7] in seen: continue
            seen.add(p[7]); yt.append(p)
        h = ''
        if nh: h += f'<p>NHTSA complaint numbers (search them at <a href="https://www.nhtsa.gov/recalls" rel="noopener nofollow" target="_blank">nhtsa.gov</a>): {", ".join(nh)}{" and more" if sum(1 for p in pts if p[6] == "n") > 12 else ""}.</p>'
        if yt: h += '<p>Said out loud on YouTube: ' + ' · '.join(f'<a href="https://www.youtube.com/watch?v={E(p[7])}&amp;t={p[8]}s" target="_blank" rel="noopener nofollow">{_M(p[5])} ▶</a>' for p in yt[:8]) + '</p>'
        return h
    def _codes(s):
        cs = [c for c in (_CODES.get(s) or '').split() if f'/check-engine-light/{c.lower()}/' in CODE_URLS]
        if not cs: return ''
        return ('<p class="rcp-codes"><b>Engine codes that can lead here:</b> ' + ' '.join(f'<a href="/check-engine-light/{c.lower()}/">{c}</a>' for c in cs)
                + '. A code is where a shop starts, not proof the part failed.</p>')
    _METHOD = ('<p>Every number here is a repair bill an owner reported, never a shop&#39;s price list. Two sources: the bills owners wrote in their own complaints '
               'to the U.S. government (NHTSA), and the dollar amounts owners said out loud in YouTube repair and ownership videos. A figure counts for a repair '
               'when that repair is the part named nearest to it. Left out: purchase prices, payments, rentals, towing, warranties and deductibles, amounts under $50 or '
               'over $15,000, parts-only prices ("the part was $80 on Amazon"), bills for two different repairs named together, and money someone else paid. One number per complaint '
               '(or video) and repair: the biggest, so it&#39;s the bill, not the diagnosis fee.</p>'
               '<p>The range is the middle half of the bills (the 25th to the 75th percentile), so one wild number can&#39;t swing it. Owners who complain to the government '
               'often had expensive repairs, so a typical bill can be lower. Costs vary by shop and region, by dealer vs independent shop, by parts and by miles. '
               'This is what owners reported, not a quote for your car.</p>')
    def _faq_ld(qa): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": _rcre.sub(r'<[^>]+>', '', html.unescape(a))}} for q, a in qa]}
    def _qa(qa): return '<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{a}</p>' for q, a in qa)) + '</section>'
    def _noindex(path):
        p = _rcos.path.join(OUT, path.strip('/'), 'index.html'); s = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(s.replace('<link rel="canonical"', '<meta name="robots" content="noindex,follow"><link rel="canonical"', 1))
    _HAS = lambda u: u in LG   # built in this build (a stale file left in docs/ doesn't count)
    def _ylink(fid, y, nm):
        u = f'/cars/{fid}/{y}/'
        return f'<a href="{u}">{y} {E(nm)}</a>' if _HAS(u) else f'{y} {E(nm)}'
    ALL = {s: _stats([p for v in RC_BY[s].values() for p in v]) for s in RC_HUBS}

    # ---- /repair-cost/<repair>/<model>/
    for s in sorted(RC_HUBS):
        q = RC_Q(s); ql = RC_LOW(q); allst = ALL[s]
        for fid in sorted(RC_MODELP[s]):
            pts = RC_BY[s][fid]; st = _stats(pts); f = FY[fid]; nm = f['name']; path = RC_MU(s, fid)
            ys = sorted({p[2] for p in pts if p[6] == 'n'})
            gens = sorted({(p[3], p[4]) for p in pts if p[6] == 'y'})
            miles = [p[9] for p in pts if p[9]]
            vs = f'{"higher than" if st["med"] > allst["med"] * 1.1 else "lower than" if st["med"] < allst["med"] * .9 else "about the same as"}'
            ans = (f'{E(nm)} owners reported paying a median of <b>{_r(st["med"])}</b> for a {E(ql)}, with the middle half of bills between {_r(st["lo"])} and {_r(st["hi"])}. '
                   f'That&#39;s from {st["n"]} owner reports ({_src_line(st)}). Costs vary by shop and region.')
            # by model year (NHTSA bills carry the model year; YouTube amounts the video's generation)
            yrows = []
            for y in ys:
                yp = [p for p in pts if p[6] == 'n' and p[2] == y]; yl = f'{y} {nm}'
                link = _ylink(fid, y, nm)
                yrows.append(f'<li><span>{link}</span><b>{len(yp)}</b><small>{_r(_rcst.median([p[5] for p in yp])) + " middle bill" if len(yp) >= 3 else "too few for a middle"}</small></li>')
            for a, b in gens:
                gp = [p for p in pts if p[6] == 'y' and (p[3], p[4]) == (a, b)]
                yrows.append(f'<li><span>{_span(a, b)} {E(nm)} <small>(YouTube)</small></span><b>{len(gp)}</b><small>{_r(_rcst.median([p[5] for p in gp])) + " middle bill" if len(gp) >= 3 else "too few for a middle"}</small></li>')
            # how often owners report the failure itself (data/top_fails.json: complaints whose words name the part, per model year)
            tf = []
            for y, d in sorted((_TOPF.get(fid) or {}).items()):
                for t in d.get('top') or []:
                    if t['t'] in _TF.get(s, ()) and d.get('all'):
                        tf.append((int(y), t['n'], d['all']))
            tf.sort(key=lambda t: (-t[1], t[0]))
            tfh = ''
            if tf:
                tfh = ('<h2>How often owners report the failure</h2><ul class="rcp-tf">' + ''.join(
                    f'<li>{_ylink(fid, y, nm)}<span>{n:,} complaints name it</span><small>{round(n / a * 100)}% of that year&#39;s complaints</small></li>' for y, n, a in tf[:6])
                    + f'</ul><p class="yc-cap">Owner complaints to NHTSA whose own words name a {E(_TF[s][0].lower())}. Raw counts: popular years get more complaints. A complaint is a report, not proof of a defect.</p>')
            yr_all = sorted(set(ys) | {y for a, b in gens for y in range(a, b + 1)})
            eng = [(u, EU_NAME.get(u, u)) for u, x in ((globals().get('CAR_ENG') or {}).get(fid) or {}).items() if set(x.get('years') or []) & set(yr_all)]
            others = [(u, s2, n) for u, s2, n in RC_LINKS(fid) if s2 != s]
            cpa = (f'<div class="cpa"><div><span>What owners paid</span><p><b>{_r(st["med"])}</b> middle bill · most between {_r(st["lo"])} and {_r(st["hi"])}</p></div>'
                   f'<div><span>Compared with every car</span><p>{vs.capitalize()} the {_r(allst["med"])} middle bill owners of all {len(RC_BY[s])} models reported.</p></div>'
                   + (f'<div><span>When it happened</span><p>Owners who gave their mileage: a middle of {round(_rcst.median(miles), -3):,.0f} miles ({len(miles)} reports).</p></div>' if len(miles) >= 5
                      else f'<div><span>Model years reported</span><p>{E(_span(min(yr_all), max(yr_all)))} {E(nm)}</p></div>') + '</div>')
            body = [f'<article class="study tr2 cp2 rcp"><p class="kicker"><a href="/repair-cost/">Repair costs</a> · <a href="{RC_HUBU(s)}">{E(q)}</a></p><h1>{E(nm)} {E(ql)} cost</h1>'
                    f'<p class="lede">What {st["n"]} {E(nm)} owners reported paying.</p>',
                    cpa, f'<p class="cpm rcp-ans">{ans}</p>',
                    '<h2>What owners paid</h2>' + _hist(pts),
                    '<h2>By model year</h2><ul class="rcp-yr">' + ''.join(yrows) + '</ul><p class="yc-cap">Reports per model year, with the middle bill where there are 3 or more. YouTube amounts count for the generation the video covers.</p>',
                    tfh]
            if eng:
                body.append('<h2>Engines in these years</h2><p class="rcp-eng">' + ' · '.join(f'<a href="{E(u)}">{E(n_)}</a>' for u, n_ in sorted(eng, key=lambda t: t[1])[:8])
                            + '</p><p class="yc-cap">Engines with a page of their own that this model was sold with in the years above. Owners don&#39;t always say which engine they had.</p>')
            links = [f'<a href="/cars/{fid}/">{E(nm)} reliability by year</a>', f'<a href="{RC_HUBU(s)}">{E(q)} cost on every car</a>']
            if _SYM: links.append('<a href="/symptoms/">Car symptoms and what they can mean</a>')
            body.append(_codes(s) + '<h2>Keep going</h2><ul class="rcp-more">' + ''.join(f'<li>{l}</li>' for l in links) + '</ul>'
                        + (f'<h3 class="rcp-h3">Other repairs {E(nm)} owners reported</h3><p class="rcp-eng">' + ' · '.join(f'<a href="{u}">{E(RC_Q(s2))}</a> <small>({n})</small>' for u, s2, n in others) + '</p>' if others else ''))
            body.append('<h2>The details</h2>' + f'<details class="cpd"><summary>How we count</summary>{_METHOD}</details>'
                        + f'<details class="cpd"><summary>Check the bills yourself</summary>{_proof(pts)}</details>')
            qa = [(f'How much does {ql} cost on a {nm}?', f'{nm} owners reported a median of {_r(st["med"])}, and the middle half paid {_r(st["lo"])} to {_r(st["hi"])}, from {st["n"]} owner reports. Costs vary by shop and region.'),
                  (f'Is a {nm} {ql} more expensive than on other cars?', f'The {nm} middle bill of {_r(st["med"])} is {vs} the {_r(allst["med"])} owners of all {len(RC_BY[s])} models we have reports for paid.'),
                  (f'Where do these {nm} repair costs come from?', f'From {_src_line(st)}: what owners themselves said they paid. They aren&#39;t verified bills or a shop&#39;s quote.')]
            if tf: qa.append((f'Which {nm} years report this failure most?', f'In complaints to NHTSA, owners of the ' + ', '.join(f'{y} ({n:,})' for y, n, _ in tf[:3]) + f' {nm} named it most. Raw counts, not a failure rate.'))
            body.append(_qa(qa) + f'<p class="note">Sources: NHTSA owner complaints and YouTube videos (amounts said out loud), sorted by The Lemon Index. Owner reports, not a price quote. Costs vary by shop and region.</p></article>')
            tt = f'{nm} {q} Cost: What {st["n"]} Owners Paid | The Lemon Index'
            desc = f'{nm} owners reported paying a median of {_r(st["med"])} for a {ql} (most {_r(st["lo"])}–{_r(st["hi"])}), from {st["n"]} owner reports. By model year, with sources.'
            page(path, tt, desc, ''.join(body), ld=[_faq_ld(qa)], vis=_readout(st, f'{nm} {ql}'))
            RC_URLS.append(path)

    # ---- /repair-cost/<repair>/
    for s in sorted(RC_HUBS):
        q = RC_Q(s); ql = RC_LOW(q); st = ALL[s]; path = RC_HUBU(s); M = RC_BY[s]
        rows = sorted(((fid, _stats(v)) for fid, v in M.items()), key=lambda t: (-t[1]['n'], FY[t[0]]['name']))
        top = [fid for fid, x in rows if fid in RC_MODELP[s]][:8]
        cards = ''.join(f'<a class="mc cpc" href="{RC_MU(s, fid)}"><span class="mc-p">' + (lambda ph: f'<img src="{ph["src"]}" alt="{E(FY[fid]["name"])}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async">' if ph else '')(aph(fid))
                        + f'</span><b>{E(FY[fid]["name"])}</b><span class="cpn">{len(M[fid])}</span></a>' for fid in top)
        trs = ''.join(f'<tr><td>' + (f'<a href="{RC_MU(s, fid)}">{E(FY[fid]["name"])}</a>' if fid in RC_MODELP[s] else E(FY[fid]['name'])) + f'</td><td>{x["n"]}</td>'
                      + (f'<td>{_r(x["med"])}</td><td>{_r(x["lo"])}–{_r(x["hi"])}</td>' if x['n'] >= RC_MIN else '<td colspan="2">too few for a range</td>') + '</tr>'
                      for fid, x in rows if x['n'] >= 3)
        few = sum(1 for _, x in rows if x['n'] < 3)
        topn = ', '.join(E(FY[fid]['name']) for fid, _ in rows[:3])
        ans = (f'Owners reported paying a median of <b>{_r(st["med"])}</b> for a {E(ql)}, with the middle half of bills between {_r(st["lo"])} and {_r(st["hi"])}. '
               f'That&#39;s {st["n"]:,} owner reports on {len(M)} models ({_src_line(st)}). Costs vary by shop and region.')
        rel = [s2 for s2 in sorted(RC_HUBS, key=lambda x: -RC_N[x]) if s2 != s and _GRP.get(s2) == _GRP.get(s)][:8]
        body = [f'<article class="study tr2 cp2 rcp"><p class="kicker"><a href="/repair-cost/">Repair costs</a> · What owners paid</p><h1>{E(q)} cost</h1>'
                f'<p class="lede">What {st["n"]:,} owners reported paying, in their own words.</p>',
                f'<div class="cpa"><div><span>What owners paid</span><p><b>{_r(st["med"])}</b> middle bill · most between {_r(st["lo"])} and {_r(st["hi"])}</p></div>'
                f'<div><span>Sample size</span><p>{st["n"]:,} owner reports on {len(M)} models</p></div>'
                f'<div><span>Comes up most on</span><p>{topn}</p></div></div>',
                f'<p class="cpm rcp-ans">{ans}</p>',
                '<h2>What owners paid</h2>' + _hist([p for v in M.values() for p in v])]
        if cards:
            body.append(f'<h2>Cars where it comes up most</h2><div class="mbs"><div class="mb"><div class="mg cpg">{cards}</div></div></div>'
                        '<p class="note">Owner reports per model. Raw counts, not a failure rate: popular models get more reports.</p>')
        if trs:
            body.append(f'<h2>Every model, what owners paid</h2><table class="rcp-t"><thead><tr><th>Model</th><th>Reports</th><th>Middle bill</th><th>Middle half</th></tr></thead><tbody>{trs}</tbody></table>'
                        f'<p class="yc-cap">Models with 3+ reports. A model gets its own page and a range at {RC_MIN}+ reports.' + (f' {few} more model{"s" * (few != 1)} with 1–2 reports count in the totals above.' if few else '') + '</p>')
        links = []
        if _SYM: links.append('<a href="/symptoms/">Car symptoms and what they can mean</a>')
        links.append('<a href="/repair-cost/">Every repair cost</a>'); links.append('<a href="/check-engine-light/">Look up an engine code</a>')
        body.append(_codes(s) + (f'<h2>Related repairs</h2><p class="rcp-eng">' + ' · '.join(f'<a href="{RC_HUBU(s2)}">{E(RC_Q(s2))}</a> <small>{_r(ALL[s2]["med"])}</small>' for s2 in rel) + '</p>' if rel else '')
                    + '<ul class="rcp-more">' + ''.join(f'<li>{l}</li>' for l in links) + '</ul>')
        body.append('<h2>The details</h2>' + f'<details class="cpd"><summary>How we count</summary>{_METHOD}</details>'
                    + f'<details class="cpd"><summary>Check the bills yourself</summary>{_proof([p for v in M.values() for p in v])}</details>')
        qa = [(f'How much does a {ql} cost?', f'Owners reported a median of {_r(st["med"])}, and the middle half paid {_r(st["lo"])} to {_r(st["hi"])}, from {st["n"]:,} owner reports on {len(M)} models. Costs vary by shop and region.'),
              (f'Which cars need a {ql} most?', f'The most owner reports come from the {topn}. These are raw counts: popular models get more reports, so this isn&#39;t a failure rate.'),
              (f'Why do {ql} costs vary so much?', 'Shop labor rates differ by region, dealers usually charge more than independent shops, new, used and rebuilt parts cost different amounts, and some bills include other work done at the same time.'),
              ('Where do these numbers come from?', f'From {_src_line(st)}: the repair bills owners themselves reported. Owner reports, not a price quote.')]
        body.append(_qa(qa) + '<p class="note">Sources: NHTSA owner complaints and YouTube videos (amounts said out loud), sorted by The Lemon Index. Owner reports, not a price quote. Costs vary by shop and region.</p></article>')
        tt = f'{q} Cost: What {st["n"]:,} Owners Paid | The Lemon Index'
        desc = f'Owners reported paying a median of {_r(st["med"])} for a {ql} (most {_r(st["lo"])}–{_r(st["hi"])}), from {st["n"]:,} reports on {len(M)} models. By model, with sources.'
        page(path, tt, desc, ''.join(body), ld=[_faq_ld(qa)], vis=_readout(st, ql))
        if RC_HUB_OK(s): RC_URLS.append(path)
        else: RC_NOINDEX.append(path); _noindex(path)

    # ---- /repair-cost/
    allpts = [p for s in RC_HUBS for v in RC_BY[s].values() for p in v]
    hubs = sorted(RC_HUBS, key=lambda s: -RC_N[s])
    grp = ('<div class="cgrid rcp-grid" id="rgrid">' + ''.join(
        f'<a class="cgc rcp-c" href="{RC_HUBU(s)}"><b>{E(RC_Q(s))}</b><span>{_r(ALL[s]["med"])} middle bill</span><small>{RC_N[s]:,} reports · {len(RC_BY[s])} models · {E(_GRP.get(s, "Other"))}</small></a>' for s in hubs) + '</div>')
    big = sorted(RC_HUBS, key=lambda s: -RC_N[s])[:3]
    hqa = [('How much do car repairs cost?', 'It depends on the repair. Owners reported a median of ' + ', '.join(f'{_r(ALL[s]["med"])} for a {RC_LOW(RC_Q(s))}' for s in big) + '. Each repair page has the range, the sample size and the cars it comes up on most.'),
           ('Where do these repair costs come from?', 'From repair bills owners named in their own complaints to the U.S. government (NHTSA) and amounts owners said out loud in YouTube videos. They are owner reports, not a shop&#39;s price list or a quote for your car.'),
           ('Why is my quote different?', 'Costs vary by shop and region, by dealer vs independent shop, by parts (new, used or rebuilt) and by what else was done at the same time. Use these numbers to know if a quote is in the usual range, then get a second quote.'),
           ('Which repair costs the most?', 'Among the repairs with 30+ reports, owners reported the highest middle bills for ' + ', '.join(f'{RC_LOW(RC_Q(s))} ({_r(ALL[s]["med"])})' for s in [x for x in sorted(RC_HUBS, key=lambda x: -ALL[x]['med']) if RC_N[x] >= 30][:3]) + '.')]
    body = ('<article class="study tr2 cp2 rcp"><p class="kicker">Repair costs</p><h1>Car repair costs: what owners paid</h1>'
            f'<p class="lede">{len(allpts):,} repair bills from owners, sorted into {len(RC_HUBS)} repairs.</p>'
            f'<p class="cpm rcp-ans">Every number on these pages is a bill an owner reported: {sum(1 for p in allpts if p[6] == "n"):,} from complaints to the U.S. government (NHTSA) and '
            f'{sum(1 for p in allpts if p[6] == "y"):,} said out loud in YouTube videos. Each page shows the middle bill, the middle half and the sample size. Costs vary by shop and region.</p>'
            '<h2>Every repair, most reports first</h2><input class="cf-q" type="search" placeholder="Filter, e.g. water pump or transmission" aria-label="Filter the repairs" data-filter="#rgrid">'
            f'<div class="rcp-all">{grp}<p class="cf-none" hidden>No repair matches. Try a shorter word.</p></div>'
            + '<h2>The details</h2>' + f'<details class="cpd"><summary>How we count</summary>{_METHOD}</details>'
            + _qa(hqa) + '<p class="note">Sources: NHTSA owner complaints and YouTube videos, sorted by The Lemon Index. Owner reports, not a price quote.</p></article><script src="/assets/cardfilter.js?v=1" defer></script>')
    bst = _stats(allpts) if allpts else None
    page('/repair-cost/', 'Car Repair Costs: What Owners Actually Paid | The Lemon Index',
         f'What {len(allpts):,} owners reported paying for {len(RC_HUBS)} car repairs: transmission, engine, water pump, timing chain, brakes and more. Middle bill, range and sample size for each.',
         body, ld=[_faq_ld(hqa)], vis=(_CSS + '<div class="rcp-read rcp-read-h"><div class="rcp-big"><span>Owner repair bills</span><b>' + f'{len(allpts):,}' + f'</b><small>{len(RC_HUBS)} repairs · {sum(len(v) for v in RC_MODELP.values())} car pages</small></div></div>') if bst else '')
    RC_URLS.insert(0, '/repair-cost/')
    print('repair cost pages:', len(RC_URLS), 'indexed,', len(RC_NOINDEX), 'noindex |', sum(len(v) for v in RC_MODELP.values()), 'model pages,', len(RC_HUBS), 'repair pages')
