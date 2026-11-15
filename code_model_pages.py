# 11-14 growth plan 2A-x: model x engine code pages, /check-engine-light/<code>/<model>/ ("P0420 Kia Soul", "P0300 Chevy Silverado").
# Data: data/code_models.json (code_models.py: NHTSA complaints that name the code on that model, by year, mileage, symptoms and the parts
# owners name as the cause or the repair) + engine_code_defs.py meanings (via engine_pages.py) + recalls (extras) + repair bills (repair_pages.json).
# exec'd by build.py twice:
#   CMP = 'hooks'  before the car pages: which pages exist (CM_OK), their URL, the model page chips (CM_ROW) and the code page links
#   CMP = 'pages'  after the code and repair cost pages: the pages themselves
# Rules (GROWTH CHUNK RULES.md): a page only where CM_MIN (10)+ owner complaints on that model name the code, and only when the code page
# itself exists. Indexed when we have a checked meaning that applies to the model's make; the rest are noindex,follow and out of the sitemap.
# CSS: assets/rcp.css (shared bar/list styles) + assets/cmx.css (prefix cmx-), linked from the pages themselves.
import json as _cmj, os as _cmos, re as _cmre, statistics as _cmst
if CMP == 'hooks':
    _CMD = _cmj.load(open('data/code_models.json', encoding='utf-8')) if _cmos.path.exists('data/code_models.json') else {'combos': {}}
    _CME = _cmj.load(open('data/engine_codes.json', encoding='utf-8')) if _cmos.path.exists('data/engine_codes.json') else {'codes': {}}
    import importlib.util as _cmilu
    _cms = _cmilu.spec_from_file_location('engine_code_defs', 'engine_code_defs.py'); _CMECD = _cmilu.module_from_spec(_cms); _cms.loader.exec_module(_CMECD)
    CM_MIN = 10
    CM_MS = lambda fid: fid.replace('/', '-')   # one URL segment, like the repair cost pages
    CM_URL = lambda c, fid: f'/check-engine-light/{c.lower()}/{CM_MS(fid)}/'
    def _cm_mean(c):
        if c in _CMECD.MAKE: return dict(_CMECD.MAKE[c], mk=True)
        if c in _CMECD.D: return dict(_CMECD.D[c], mk=False)
        return None
    def _cm_codepage(c):
        """the same rule engine_pages.py uses to build a code page"""
        v = _CME['codes'].get(c)
        if not v: return False
        return (_cm_mean(c) is not None and v['n'] >= 5) or v['n'] >= 20
    _CM_OK = None
    def CM_OK():
        """{(code, model id): combo} for every page we build (lazy: needs FY, which build.py sets after this hook runs)"""
        global _CM_OK
        if _CM_OK is None:
            _CM_OK = {(x['code'], x['fid']): x for x in _CMD['combos'].values() if x['n'] >= CM_MIN and x['fid'] in FY and _cm_codepage(x['code'])}
        return _CM_OK
    def CM_BY_MODEL(fid): return sorted((x for (c, f), x in CM_OK().items() if f == fid), key=lambda x: (-x['n'], x['code']))
    def CM_BY_CODE(c): return sorted((x for (k, f), x in CM_OK().items() if k == c), key=lambda x: (-x['n'], x['fid']))
    def _cm_short(t, n=44):
        t = _cmre.sub(r'[ ]*[(][^()]*[)]', '', t).strip()
        return t if len(t) <= n else t[:n].rsplit(' ', 1)[0].rstrip(' -/,') + '…'
    def CM_ROW(fid):
        """model page: the codes this model's owners name most, under the code search (added after the date hash, like the search box)"""
        xs = CM_BY_MODEL(fid)
        if not xs: return ''
        nm = FY[fid]['name']
        chip = lambda x: (f'<a class="n3-c" href="{CM_URL(x["code"], fid)}"><b>{x["code"]}</b><small>' + (E(_cm_short((_cm_mean(x["code"]) or {}).get('t', ''))) + ' · ' if _cm_mean(x['code']) else '')
                          + f'{x["n"]} complaints</small></a>')
        return ((EU_CSS if 'EU_CSS' in globals() else '') + f'<nav class="n3-row cmx-row" aria-label="Engine codes {E(nm)} owners report" data-mc="{",".join(x["code"] for x in xs)}" data-mf="{E(CM_MS(fid))}" data-mn="{E(nm)}">'
                f'<p class="n3-h">Engine codes {E(nm)} owners report most</p><div class="n3-cs">' + ''.join(chip(x) for x in xs[:8]) + '</div>'
                + (('<p class="n3-n">More: ' + ' · '.join(f'<a href="{CM_URL(x["code"], fid)}">{x["code"]}</a> ({x["n"]})' for x in xs[8:]) + '</p>') if xs[8:] else '')
                + f'<p class="n3-n">Codes named in {CM_MIN}+ owner complaints to NHTSA about the {E(nm)}. <a href="/check-engine-light/">Every engine code →</a></p></nav>')

if CMP == 'pages':
    CM_URLS = []; CM_NOINDEX = []
    _CSS = '<link rel="stylesheet" href="/assets/rcp.css?v=1"><link rel="stylesheet" href="/assets/cmx.css?v=1">'
    _PL = _CMD.get('parts') or {}
    _HAS = lambda u: u in LG
    # the part as a noun in a sentence ("the most-named part is the ...")
    _NOUN = {'engine': 'engine (replaced or rebuilt)', 'trans': 'transmission (replaced or rebuilt)', 'software': 'engine software (a reflash)',
             'headgasket': 'head gasket', 'pistons': 'pistons, rings or valves', 'wiring': 'wiring or a connector', 'vacuum': 'vacuum lines',
             'o2': 'oxygen (O2) sensor', 'evap': 'EVAP purge or vent valve', 'gas-cap': 'gas cap', 'abs': 'ABS module, pump or accumulator',
             'dpf': 'diesel exhaust parts (DPF, DEF, NOx sensor)', 'battery': '12-volt battery', 'pcv': 'PCV valve or oil separator',
             'maf': 'mass airflow (MAF) sensor', 'tcm': 'transmission computer (TCM)', 'ecm': 'engine computer (ECM / PCM)'}
    _pn = lambda k: _NOUN.get(k) or (lambda l: l if l[:3].isupper() else l[0].lower() + l[1:])(_PL.get(k, k))
    _pct = lambda k, n: round(k / n * 100) if n else 0
    # parts owners name -> the repair cost pages (repair_cost_pages.py slugs)
    _P2R = {'cat': 'catalytic-converter', 'o2': 'oxygen-sensor', 'coils': 'ignition-coils', 'spark-plugs': 'spark-plugs', 'throttle': 'throttle-body',
            'evap': 'evap', 'maf': 'maf-sensor', 'egr': 'egr', 'thermostat': 'thermostat', 'timing': 'timing-chain', 'injectors': 'fuel-injectors',
            'fuelpump': 'fuel-pump', 'turbo': 'turbo', 'headgasket': 'head-gasket', 'engine': 'engine-replacement', 'trans': 'transmission-replacement',
            'torque': 'torque-converter', 'valvebody': 'valve-body', 'tcm': 'tcm', 'ecm': 'ecm', 'abs': 'abs-module', 'battery': 'battery',
            'alternator': 'alternator', 'hybrid': 'hybrid-battery', 'dpf': 'dpf', 'intake': 'intake-manifold', 'camcrank': 'crank-sensor', 'knock': None}
    # our symptom words -> the symptom pages (growth plan 2C), linked only once that page is built
    _T2S = {'stalls or shuts off': 'car-stalls-while-driving', 'loses power or goes into limp mode': 'car-loses-power-while-driving',
            'shakes, runs rough or misfires': 'engine-misfire', "won't start or hard to start": 'car-wont-start', 'flashing check engine light': 'check-engine-light-flashing',
            'transmission slips or shifts hard': 'transmission-slipping', 'uses or leaks oil': 'car-burning-oil', 'overheats': 'engine-overheating',
            'fuel smell or fuel leak': 'gas-smell', 'rattles or knocks': 'engine-knocking', 'brakes or ABS act up': 'abs-light-on',
            'warning lights and electrical faults': 'dashboard-warning-lights-on'}
    _sym = lambda t: (lambda u: u if (_HAS(u) or _cmos.path.exists(_cmos.path.join(OUT, u.strip('/'), 'index.html'))) else None)(f'/symptoms/{_T2S[t]}/') if t in _T2S else None
    # NHTSA complaint components and recall parts, in the same few systems
    _SYS = [('engine', 'engine'), ('fuel', 'fuel'), ('propulsion', 'fuel'), ('power train', 'powertrain'), ('brake', 'brakes'), ('electrical', 'electrical'),
            ('speed control', 'speed'), ('steering', 'steering'), ('suspension', 'suspension'), ('exhaust', 'exhaust'), ('emission', 'exhaust'), ('hybrid', 'hybrid')]
    _sysof = lambda s: {g for k, g in _SYS if k in (s or '').lower()}
    _BILLS = {}   # complaint number -> [(repair, amount)] (NHTSA bills only)
    for _s, _m in RC_BY.items():
        for _f, _pts in _m.items():
            for _p in _pts:
                if _p[6] == 'n': _BILLS.setdefault((_f, _p[7]), []).append((_s, _p[5]))
    _M = lambda v: f'${v:,.0f}'
    def _miles(v): return f'{round(v, -3):,.0f}' if v >= 10000 else f'{v:,}'
    def _yl(fid, y, nm, short=False):
        u = f'/cars/{fid}/{y}/'; t = f'{y}' if short else f'{y} {E(nm)}'
        return f'<a href="{u}">{t}</a>' if _HAS(u) else t
    def _noindex(path):
        p = _cmos.path.join(OUT, path.strip('/'), 'index.html'); s = open(p, encoding='utf-8').read()
        open(p, 'w', encoding='utf-8').write(s.replace('<link rel="canonical"', '<meta name="robots" content="noindex,follow"><link rel="canonical"', 1))
    def _faq_ld(qa): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": _cmre.sub(r'<[^>]+>', '', html.unescape(a))}} for q, a in qa]}
    def _qa(qa): return '<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{a}</p>' for q, a in qa)) + '</section>'
    def _list(xs):
        xs = list(xs)
        return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1] if xs else ''
    _METHOD = ('<p>We read every owner complaint in the NHTSA file whose text names this trouble code, and count the ones filed about this model '
               '(matched by the make, model and model year on the complaint). Mileage is what the owner entered on the form.</p>'
               '<p>Parts: a complaint counts for a part when one of the owner&#39;s own sentences names that part together with a cause word '
               '(failed, bad, diagnosed, caused by, leaking ...) or a repair word (replaced, repaired, new, reprogrammed ...). "Came back" means the same complaint '
               'also says the problem returned or the repair didn&#39;t fix it. These are counts of what owners wrote, not a diagnosis, and one complaint can name several parts.</p>'
               '<p>Complaints are reports, not proof of a defect, and most owners never file one. Popular models get more complaints, so the counts are not a failure rate. '
               'The code meaning is the standard SAE J2012 definition in our own words, or the carmaker&#39;s meaning where we verified it for that make.</p>')
    built = 0
    for (c, fid), x in sorted(CM_OK().items(), key=lambda kv: (-kv[1]['n'], kv[0])):
        cpath = f'/check-engine-light/{c.lower()}/'
        if not _HAS(cpath): print('code x model: skipped, no code page', c, fid); continue
        f = FY[fid]; nm = f['name']; n = x['n']; path = CM_URL(c, fid)
        mm = _meaning(c); applies = bool(mm) and (not mm['mk'] or any(x['mk'].lower() == m.lower() for m in mm.get('makes') or []))
        if mm and not applies: mm = None   # a carmaker's meaning for another make doesn't apply here
        st = ECD.sev_text(mm) if mm else None
        title_bits = mm['t'] if mm else _nomean(c)[0]
        mean1 = (E(_cmre.split(r'(?<=[.!?])\s', mm['m'].strip(), 1)[0]) if mm else _nomean(c)[1])
        yrs = [(y, k) for y, k in x['years']]; ytop = sorted(yrs, key=lambda t: (-t[1], -t[0]))
        y0, y1 = min(y for y, _ in yrs), max(y for y, _ in yrs)
        mc = _CMD['model_coded'].get(fid) or 0; share_m = _pct(n, mc); share_all = round(_CMD['code_all'].get(c, 0) / _CMD['total'] * 100, 1) if _CMD.get('total') else 0
        rk = x['rank']
        th = [(t, k) for t, k in x['themes'] if t != 'check engine light comes on' and k >= 2][:6]
        cel = dict(x['themes']).get('check engine light comes on', 0)
        parts = [p for p in x['parts'] if p[1] >= 2 and (p[1] >= 3 or p[1] / n >= .1)][:8]
        co = [(k, v) for k, v in x['co'] if v >= 2][:6]
        ms = x.get('miles')
        topy = ', '.join(f'{y} ({k})' for y, k in ytop[:3])
        topp = parts[0] if parts else None
        # ---- the answer + tiles
        ans = (f'{E(nm)} owners named {c} in <b>{n}</b> complaints to the U.S. government (NHTSA), most often on the {_list([str(y) for y, _ in ytop[:3]])} model year{"s" * (len(ytop[:3]) > 1)}'
               + (f', at a middle of {_miles(ms["med"])} miles' if ms else '') + '. '
               + (f'The part they name most is the {E(_pn(topp[0]))} ({topp[1]} complaint{"s" * (topp[1] != 1)}). ' if topp else '')
               + 'Complaints are owner reports, not proof of a defect.')
        rkt = f'the #{rk} code {E(nm)} owners name' if rk <= 10 else f'one of {x["of"]} codes {E(nm)} owners name'
        tiles = (f'<div class="cpa"><div><span>What {c} means</span><p>{mean1} <a href="{cpath}">Full {c} page</a></p></div>'
                 f'<div><span>On the {E(nm)}</span><p><b>{n}</b> owner complaints · {rkt}' + (f' · {share_m}% of {E(nm)} complaints that name a code (every car: {share_all}%)' if mc >= 30 else '') + '</p></div>'
                 + (f'<div><span>Mileage owners report</span><p>Middle of <b>{_miles(ms["med"])}</b> miles · most between {_miles(ms["lo"])} and {_miles(ms["hi"])} ({ms["n"]} owners gave it)</p></div>' if ms
                    else f'<div><span>Model years</span><p>{y0}–{y1} {E(nm)} · most: {topy}</p></div>') + '</div>')
        body = [f'<article class="study tr2 cp2 rcp cmx"><p class="kicker"><a href="/check-engine-light/">Check engine light</a> · <a href="{cpath}">{c}</a> · {E(nm)}</p><h1>{c} on the {E(nm)}</h1>'
                f'<p class="lede">{E(title_bits)}: what {n} {E(nm)} owners reported.</p>', _CSS, tiles, f'<p class="cpm rcp-ans">{ans}</p>']
        # ---- model years
        mx = max(k for _, k in yrs)
        body.append(f'<h2>{E(nm)} model years that report {c}</h2><ul class="rcp-hist cmx-yr">' + ''.join(
            f'<li><span>{_yl(fid, y, nm, short=True)}</span><span class="rcp-hb"><i style="width:{max(3, round(k / mx * 100))}%"></i></span><b>{k}</b></li>' for y, k in sorted(yrs, reverse=True))
            + f'</ul><p class="yc-cap">Owner complaints naming {c}, by model year. Raw counts: years that sold more get more complaints, so this is each model year&#39;s record, not a failure rate.</p>')
        if ms:
            L = lambda v: max(0, min(100, round(v / max(ms['hi'] * 1.25, 1) * 100, 1)))
            body.append(f'<h2>Mileage when it happened</h2><div class="cmx-mi"><p><b>{_miles(ms["med"])}</b> miles is the middle of what {ms["n"]} owners entered. Half were between {_miles(ms["lo"])} and {_miles(ms["hi"])} miles.</p>'
                        f'<span class="cmx-track" aria-hidden="true"><i style="left:{L(ms["lo"])}%;width:{max(2, L(ms["hi"]) - L(ms["lo"]))}%"></i><em style="left:{L(ms["med"])}%"></em></span></div>'
                        '<p class="yc-cap">The mileage on the complaint form, when the owner gave one.</p>')
        # ---- parts owners name
        if parts:
            def _pli(p):
                k, nd, fx, bk = p; lab = _PL.get(k, k); s = _P2R.get(k)
                cost = ''
                if s and s in RC_HUBS:
                    cost = (f' · <a href="{RC_MU(s, fid)}">what {E(nm)} owners paid</a>' if fid in RC_MODELP.get(s, set()) else f' · <a href="{RC_HUBU(s)}">what owners paid</a>')
                sub = (f'{fx} mention{"s" * (fx == 1)} a repair or replacement' + ((f', {bk} of them say the problem came back' if bk > 1 else ', 1 of them says the problem came back') if bk else '') if fx else 'named as the cause, no repair mentioned')
                return f'<li><span><b>{E(lab)}</b></span><span>{nd} complaint{"s" * (nd != 1)}</span><small>{sub}{cost}</small></li>'
            lead = parts[0]; ll = _pn(lead[0])
            para = (f'<p>The most-named part is the <b>{E(ll)}</b>, in {lead[1]} of the {n} complaints ({_pct(lead[1], n)}%).'
                    + (f' {lead[2]} of those mention it being replaced or repaired' + (f', and {lead[3]} say the problem came back afterwards' if lead[3] else '') + '.' if lead[2] else '')
                    + (' Next: ' + _list([f'{E(_pn(p[0]))} ({p[1]})' for p in parts[1:4]]) + '.' if parts[1:] else '') + '</p>')
            extra_ = []
            if x.get('recall', 0) >= 3: extra_.append(f'{x["recall"]} complaints mention a recall')
            if x.get('warranty', 0) >= 3: extra_.append(f'{x["warranty"]} mention a warranty')
            body.append(f'<h2>What owners say caused it or fixed it</h2>{para}<ul class="rcp-tf cmx-p">' + ''.join(_pli(p) for p in parts) + '</ul>'
                        + (f'<p class="cmx-n">{_list(extra_).capitalize()}.</p>' if extra_ else '')
                        + '<p class="yc-cap">Counted from the owners&#39; own words: a part counts when a sentence names it with a cause or repair word. What owners wrote, not a diagnosis. A shop should confirm the cause before replacing parts.</p>')
        # ---- symptoms
        if th or cel:
            li = ''.join(f'<li><span>' + (f'<a href="{_sym(t)}">{E(t[0].upper() + t[1:])}</a>' if _sym(t) else E(t[0].upper() + t[1:])) + f'</span><b>{_pct(k, n)}%</b><small>{k} of {n} complaints</small></li>' for t, k in th)
            body.append(f'<h2>Symptoms owners describe with {c}</h2>'
                        + (f'<p>{_pct(cel, n)}% of these complaints say the check engine light came on.' + (f' {_pct(x["towed"], n)}% say the {E(nm)} had to be towed.' if x['towed'] >= 3 and _pct(x['towed'], n) >= 5 else '') + '</p>' if cel else '')
                        + (f'<ul class="rcp-yr cmx-s">{li}</ul><p class="yc-cap">Share of the complaints naming {c} whose text also describes each problem. A complaint can describe more than one.</p>' if th else ''))
        if co:
            body.append(f'<h2>Codes owners report with it</h2><p class="crel">' + ' '.join(
                (f'<a href="{CM_URL(k, fid)}">{k}</a>' if (k, fid) in CM_OK() and _HAS(f'/check-engine-light/{k.lower()}/') else f'<a href="/check-engine-light/{k.lower()}/">{k}</a>' if _HAS(f'/check-engine-light/{k.lower()}/') else f'<span class="cmx-c">{k}</span>')
                + f' <small class="cmx-k">{v}</small>' for k, v in co) + f'</p><p class="yc-cap">Other codes named in the same {E(nm)} complaints, and in how many.</p>')
        # ---- repair costs: bills owners named in these very complaints, then the repair cost pages
        bills = [b for o in x['odi'] for b in _BILLS.get((fid, o), [])]
        costh = ''
        if len(bills) >= 3:
            by = {}
            for s, v in bills: by.setdefault(s, []).append(v)
            rows = sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            costh = ('<ul class="rcp-yr">' + ''.join(f'<li><span>' + (f'<a href="{RC_MU(s, fid)}">{E(RC_Q(s))}</a>' if s in RC_HUBS and fid in RC_MODELP.get(s, set()) else f'<a href="{RC_HUBU(s)}">{E(RC_Q(s))}</a>' if s in RC_HUBS else E(RC_Q(s)))
                     + f'</span><b>{_M(_cmst.median(vs)) if len(vs) >= 3 else ", ".join(_M(v) for v in sorted(vs))}</b><small>{len(vs)} bill{"s" * (len(vs) != 1)}' + (' · middle bill' if len(vs) >= 3 else '') + '</small></li>' for s, vs in rows[:6])
                     + f'</ul><p class="yc-cap">Repair bills owners named in these {n} complaints ({len(bills)} in all). Owner reports, not a quote: costs vary by shop and region.</p>')
        rlinks = []
        for k, *_ in parts:
            s = _P2R.get(k)
            if s and s in RC_HUBS and fid in RC_MODELP.get(s, set()) and RC_MU(s, fid) not in costh: rlinks.append(f'<a href="{RC_MU(s, fid)}">{E(nm)} {E(RC_LOW(RC_Q(s)))} cost</a>')
        if costh or rlinks:
            body.append('<h2>Repair costs</h2>' + costh + (f'<p class="rcp-eng">' + ' · '.join(rlinks[:5]) + '</p>' if rlinks else ''))
        # ---- recalls on these model years for the same systems
        sysset = set()
        for comp, k in x['comps']:
            if k / n >= .15: sysset |= _sysof(comp)
        recs = {}
        for y, _ in yrs:
            for r in (extra(fid, y).get('recalls') or []):
                if _sysof((r.get('part') or '').split(':')[0]) & sysset:
                    recs.setdefault(r['id'], [r, set()])[1].add(y)
        rl = sorted(recs.values(), key=lambda t: t[0]['date'][6:10] + t[0]['date'][3:5] + t[0]['date'][:2], reverse=True)
        if rl:
            body.append(f'<h2>Recalls on these {E(nm)} years</h2><ul class="recalls">' + ''.join(
                f'<li><b>{E(RPART(r["part"]).capitalize())}</b> <small>· {E(", ".join(str(y) for y in sorted(ys)))} · issued {E(r["date"][-4:])}</small><br>{E(rsum(r))} <small class="muted">NHTSA {E(r["id"])}</small></li>' for r, ys in rl[:5])
                + f'</ul><p class="note">{len(rl)} recall{"s" * (len(rl) != 1)} for the same systems ({E(_list(sorted(sysset)))}) on the {E(nm)} model years above. A recall for the same system isn&#39;t proof it&#39;s behind {c}. Recall work is free at any dealer: check a VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener">nhtsa.gov/recalls</a> or with our <a href="/vin/">VIN check</a>.</p>')
        # ---- more
        links = [f'<a href="{cpath}">{c}: meaning, causes and every car that reports it</a>', f'<a href="/cars/{fid}/">{E(nm)} reliability by year</a>']
        if _HAS(f'/cars/{fid}/{ytop[0][0]}/'): links.append(f'<a href="/cars/{fid}/{ytop[0][0]}/">{ytop[0][0]} {E(nm)} problems and recalls</a>')
        others = [o for o in CM_BY_MODEL(fid) if o['code'] != c]
        ocars = [o for o in CM_BY_CODE(c) if o['fid'] != fid]
        body.append('<h2>Keep going</h2><ul class="rcp-more">' + ''.join(f'<li>{l}</li>' for l in links) + '</ul>'
                    + (f'<h3 class="rcp-h3">Other codes {E(nm)} owners report</h3><p class="crel">' + ' '.join(f'<a href="{CM_URL(o["code"], fid)}">{o["code"]}</a>' for o in others[:10]) + '</p>' if others else '')
                    + (f'<h3 class="rcp-h3">{c} on other cars</h3><p class="rcp-eng">' + ' · '.join(f'<a href="{CM_URL(c, o["fid"])}">{E(FY[o["fid"]]["name"])}</a> <small>({o["n"]})</small>' for o in ocars[:10]) + '</p>' if ocars else ''))
        nh = x['odi'][:12]
        body.append('<h2>The details</h2>' + f'<details class="cpd"><summary>How we count</summary>{_METHOD}</details>'
                    + (f'<details class="cpd"><summary>What {c} means</summary><p>{E(mm["m"])}</p>' + (f'<p><b>{E(st[0])}.</b> {E(st[1])}</p>' if st else '') + '<ul class="fx">' + ''.join(f'<li>{E(z)}</li>' for z in mm['c']) + '</ul></details>' if mm else
                       f'<details class="cpd"><summary>What {c} means</summary><p>{_nomean(c)[2]} We haven&#39;t verified its meaning for {E(x["mk"])} yet. A dealer or a scanner with the maker&#39;s software can tell you exactly.</p></details>')
                    + f'<details class="cpd"><summary>Check the complaints yourself</summary><p>NHTSA complaint numbers (search them at <a href="https://www.nhtsa.gov/recalls" rel="noopener nofollow" target="_blank">nhtsa.gov</a>): {", ".join(nh)}{" and " + str(n - len(nh)) + " more" if n > len(nh) else ""}.</p></details>')
        # ---- quick answers
        qa = []
        if mm: qa.append((f'What does {c} mean on a {nm}?', f'{E(mm["t"])}. {E(mm["m"])}'))
        qa.append((f'Which {nm} years have the most {c} complaints?', f'In complaints to NHTSA, owners of the {topy} {E(nm)} named {c} most ({n} complaints in all, {y0}–{y1}). Raw counts, not a failure rate.'))
        if parts:
            qa.append((f'What fixes {c} on a {nm}?', f'Owners most often name the {E(ll)} ({parts[0][1]} of {n} complaints)'
                       + (', then ' + _list([E(_pn(p[0])) for p in parts[1:3]]) if parts[1:] else '')
                       + '. That&#39;s what owners wrote, not a diagnosis: have a shop confirm the cause with a scan and tests before replacing parts.'))
        if ms: qa.append((f'At what mileage does {c} show up on a {nm}?', f'Owners who gave their mileage reported a middle of {_miles(ms["med"])} miles; half were between {_miles(ms["lo"])} and {_miles(ms["hi"])} ({ms["n"]} owners).'))
        if st: qa.append((f'Can I drive my {nm} with {c}?', f'{E(st[0])}. {E(st[1])}'))
        body.append(_qa(qa) + SEARCH_MINI.replace('Check engine light on? Look up the code', 'Look up another code')
                    + f'<p class="note">Sources: NHTSA owner complaints that name {c} on the {E(nm)}, counted by The Lemon Index; NHTSA recalls; repair bills owners named. '
                    'Meanings: SAE J2012 in our own words. Owner reports, not a diagnosis or repair advice for your car.</p></article>' + CODES_JS)
        hero = (f'<div class="creadout"><div class="cr-code"><span class="cr-sys">{E(nm)} · {n} owner complaints</span><b>{c}</b></div>'
                + (gauge(mm['s'], w=bool(mm.get('w'))) if mm else '') + '</div>')
        tt = f'{c} {nm}: Causes, Model Years and What Owners Report | The Lemon Index'
        desc = (f'{nm} owners named {c}' + (f' ({_cmre.sub(r"[ ]*[(][^()]*[)]$", "", mm["t"])})' if mm else '') + f' in {n} complaints to NHTSA, most on the {_list([str(y) for y, _ in ytop[:3]])} models.'
                + (' Mileage, ' if ms else ' ') + 'what owners say fixed it, symptoms, costs and recalls.')
        page(path, tt, desc, ''.join(body), ld=[_faq_ld(qa)], vis=hero)
        built += 1
        if mm: CM_URLS.append(path)
        else: CM_NOINDEX.append(path); _noindex(path)
    print('code x model pages:', built, 'built,', len(CM_URLS), 'indexed,', len(CM_NOINDEX), 'noindex (no checked meaning for that make)')
