# Engine code search + code pages (11-10, Lemon growth project 2A). Run by build.py with exec() before gap_pages.py.
# Data: data/engine_codes.json (engine_codes.py: which codes owners name in NHTSA complaints, on which cars) + engine_code_defs.py
# (meanings in our own words; generic SAE J2012 titles, manufacturer codes only where verified per make).
# Pages: /check-engine-light/<code>/ for codes with data. Indexed when we have a meaning and 10+ complaints; the rest are noindex,follow.
# Search: assets/codes.js + /assets/codes.json (client-side, lazy-loaded on first focus), big box on the hub, small box on model pages.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location('engine_code_defs', 'engine_code_defs.py'); ECD = _ilu.module_from_spec(_spec); _spec.loader.exec_module(ECD)
EC = _load('data/engine_codes.json') if os.path.exists('data/engine_codes.json') else None
CODE_URLS = []; CODE_NOINDEX = []
SYSN = {'P': 'Powertrain (engine and transmission)', 'B': 'Body (airbags, seats, lights, locks)', 'C': 'Chassis (brakes, steering, suspension)', 'U': 'Network (how the car\'s computers talk)'}

def _generic(c): return (c[0] == 'P' and (c[1] in '02' or c.startswith('P34'))) or (c[0] in 'BCU' and c[1] == '0')

SYSW = {'P': 'engine', 'B': 'body', 'C': 'chassis', 'U': 'network'}
def _nomean(c):
    # what we can honestly say about a code we have no checked meaning for
    if not _generic(c): return ('Manufacturer-specific code', f'{c} is a manufacturer-specific code, so its exact meaning depends on the make.',
        f'{c} is a manufacturer-specific code: each carmaker decides what it means, so the same code can point to different problems on different brands.')
    if c[0] == 'P': return (f'Standard {SYSW[c[0]]} code', f'{c} is a standard engine code we haven&#39;t explained yet.', f'{c} is a standard (generic) powertrain code.')
    return (f'{SYSN[c[0]].split(" (")[0]} code', f'{c} is a {SYSW[c[0]]} code from the standard list, but carmakers often use these codes their own way, so its exact meaning depends on the make.',
        f'{c} is in the standard {SYSW[c[0]]} code range, but carmakers often define {SYSW[c[0]]} codes their own way, so the same code can point to different problems on different brands.')

def _meaning(c):
    if c in ECD.MAKE: return dict(ECD.MAKE[c], mk=True)
    if c in ECD.D: return dict(ECD.D[c], mk=False)
    return None

def gauge(s, small=False, w=False):
    # half-circle gauge, needle at drive-on / soon / now. Lemon yellow -> red.
    ang = {1: -60, 2: 0, 3: 60}[s]; lab = (ECD.SEV_W[0] if w else ECD.SEV[s][0])
    return (f'<figure class="cgauge{" sm" if small else ""} s{s}" aria-label="Severity: {E(lab)}"><svg viewBox="0 0 200 112" aria-hidden="true">'
            '<path d="M14 100 A86 86 0 0 1 57 25" class="g1"/><path d="M61 23 A86 86 0 0 1 139 23" class="g2"/><path d="M143 25 A86 86 0 0 1 186 100" class="g3"/>'
            f'<g transform="rotate({ang} 100 100)"><line x1="100" y1="100" x2="100" y2="30" class="nd"/></g><circle cx="100" cy="100" r="8" class="hub"/></svg>'
            f'<figcaption>{E(lab)}</figcaption></figure>')

SEARCH_BIG = ('<section class="csearch" id="search" aria-label="Engine code search"><form class="cs-f" action="/check-engine-light/" method="get" role="search">'
              '<label for="cs-q">Type your engine code</label><div class="cs-row"><input id="cs-q" name="code" autocomplete="off" autocapitalize="characters" spellcheck="false" inputmode="text" maxlength="8" placeholder="P0420" aria-describedby="cs-h">'
              '<button type="submit">Look it up</button></div><p class="cs-h" id="cs-h">Any OBD-II code: P, B, C or U plus four characters. Free, nothing is saved.</p></form>'
              '<div class="cs-out" id="cs-out" aria-live="polite"></div></section>')
# SEARCH_MINI and CODES_JS live in build.py (model pages are built before this file runs)

def _pct(k, n): return round(k / n * 100)

def _code_pages():
    if not EC: return
    C = EC['codes']; idx = {}
    for c, v in C.items():
        mm = _meaning(c); page_ok = (mm is not None and v['n'] >= 5) or v['n'] >= 20
        indexed = mm is not None and v['n'] >= 10
        idx[c] = dict(n=v['n'], mk=[m for m, _ in v['makes'][:3]], top=[[i, nm, k] for i, nm, k in v['models'][:3] if k >= 2], p=1 if page_ok else 0)
        if mm: idx[c].update(t=mm['t'], m=mm['m'], s=mm['s'], c=mm['c'][:3], mf=mm.get('makes') if mm['mk'] else None, w=mm.get('w'))
        if not page_ok: continue
        slug = c.lower(); path = f'/check-engine-light/{slug}/'
        sev = mm['s'] if mm else None; st = ECD.sev_text(mm) if mm else None
        title_bits = mm['t'] if mm else _nomean(c)[0]
        th = [(t, k) for t, k in v['themes'] if t != 'check engine light comes on' and k >= 2][:4]
        models = [m for m in v['models'] if m[2] >= 2 and os.path.exists(os.path.join(OUT, 'cars', m[0], 'index.html'))][:10]; years = [y for y in v['years'] if y[3] >= 2 and os.path.exists(os.path.join(OUT, 'cars', y[0], str(y[2]), 'index.html'))][:8]
        topm = models[0][1] if models else (v['makes'][0][0] if v['makes'] else '')
        ans = (f'{c} means: {E(mm["t"])}. ' if mm else _nomean(c)[1] + ' ') + \
              (f'{E(st[1])} ' if sev else '') + \
              f'Owners named {c} in {v["n"]:,} complaints to the U.S. government' + (f', most often on the {E(topm)}.' if topm else '.')
        # 11-10 v2 (design audit: code pages were a wall of sections): the transmission-page pattern. Code + gauge under the title, a 3-part
        # answer (what it means / how serious / typical fix), the cars owners report it on as photo cards, everything else folded.
        fix = ((mm['c'][0] + ('. Then: ' + '; '.join(x[:1].lower() + x[1:] for x in mm['c'][1:3]) if len(mm['c']) > 1 else '') + '.') if mm else 'Have a shop read it with the maker&#39;s own scan tool first.')   # 11-12: the checks in order, not a "fix"
        mean1 = (E(re.split(r'(?<=[.!?])\s', mm['m'].strip(), 1)[0]) if mm else _nomean(c)[1])   # the plain-English first sentence (the title repeats the h1)
        sevt = (f'<b>{E(st[0])}.</b> {E(st[1])}' if sev else 'Depends on what it means on your make. Get it read before a long drive.')
        cards = ''.join(f'<a class="mc cpc" href="/cars/{i}/"><span class="mc-p">' + (lambda ph: f'<img src="{ph["src"]}" alt="{E(nm)}" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async">' if ph else '')(aph(i))
                        + f'</span><b>{E(nm)}</b><span class="cpn">{k:,}</span></a>' for i, nm, k in models[:8])
        det = []
        if mm:
            det.append((f'What {c} means', f'<p>{E(mm["m"])}</p>' + (f'<p class="yc-cap">This meaning applies to {E(", ".join(mm["makes"]))}. On other makes {c} can mean something different.</p>' if mm['mk'] else '')))
            det.append((f'Can I drive with {c}?', f'<p><b>{E(st[0])}.</b> {E(st[1])}</p>' +
                        (f'<p>{_pct(th[0][1], v["n"])}% of the owner complaints that name {c} also say the car {E(th[0][0])}. A complaint can describe more than one problem, so this doesn&#39;t prove the code caused it.</p>' if th else '') +
                        (f'<p>{_pct(v["towed"], v["n"])}% of those owners said the car had to be towed.</p>' if v['towed'] >= 5 and _pct(v['towed'], v['n']) >= 5 else '')))
            det.append((f'Common causes of {c}', '<ul class="fx">' + ''.join(f'<li>{E(x)}</li>' for x in mm['c']) + '</ul><p class="yc-cap">A shop should confirm the cause with a scan and tests before replacing parts.</p>'))
        else:
            det.append((f'What {c} means', f'<p>{_nomean(c)[2]} We haven&#39;t verified its meaning yet. A dealer or a scanner with the maker&#39;s software can tell you exactly what it means on your car.</p>'
                        '<p>Owners who reported it drive: ' + ', '.join(f'{E(m)} ({k})' for m, k in v['makes'][:4]) + '.</p>'))
        if th:
            det.append(('What owners describe', '<ul class="fx">' + ''.join(f'<li>{E(t[0].upper() + t[1:])}: {_pct(k, v["n"])}% of complaints</li>' for t, k in th) +
                        '</ul><p class="yc-cap">Share of complaints naming the code whose text also mentions each problem.</p>'))
        if years:
            det.append((f'Model years that report {c} most', '<p>' + ', '.join(f'<a href="/cars/{i}/{y}/">{y} {E(nm)}</a> ({k})' for i, nm, y, k in years[:6]) + '.</p>'))
        _rk = [r for r in C if r != c and r[:3] == c[:3] and (_meaning(r) is not None and C[r]['n'] >= 5 or C[r]['n'] >= 20)]   # 11-12 link graph: the nearest codes first (same 4-character group, then the same 3), so every code page gets linked from its neighbours (U0170 was an orphan)
        rel = sorted(_rk, key=lambda r: (r[:4] != c[:4], abs(int('0' + re.sub(r'[^0-9A-Fa-f]', '', r[1:]), 16) - int('0' + re.sub(r'[^0-9A-Fa-f]', '', c[1:]), 16)), r))[:8]
        hero = (f'<div class="creadout"><div class="cr-code"><span class="cr-sys">{E(SYSN[c[0]].split(" (")[0])} · {"Generic" if _generic(c) else "Manufacturer"}</span><b>{c}</b></div>'
                + (gauge(sev, w=bool(mm.get("w"))) if sev else '') + '</div>')
        body = [f'<article class="study tr2 cp2"><p class="kicker"><a href="/check-engine-light/">Check engine light</a> · Engine codes</p><h1>{c}: {E(title_bits)}</h1>',
                f'<div class="cpa"><div><span>What it means</span><p>{mean1}</p></div><div><span>How serious</span><p>{sevt}</p></div><div><span>Where a shop starts</span><p>{E(fix) if mm else fix}</p></div></div>',
                f'<p class="cpm">Owners named {c} in <b>{v["n"]:,}</b> complaints to the U.S. government' + (f', most often on the {E(topm)}.' if topm else '.') + '</p>']
        if cards:
            body.append(f'<h2>Cars owners report it on</h2><div class="mbs"><div class="mb"><div class="mg cpg">{cards}</div></div></div><p class="note">Complaints that name {c}, by model. Raw counts, not a failure rate: popular models get more complaints.</p>')
        _tr = c[:3] in ('P07', 'P08', 'P09') or bool(re.search(r'transmission|shift|gear|torque converter|cvt|clutch', title_bits, re.I))
        _tl = [(i, nm) for i, nm, k in models[:8] if _tr and os.path.exists(os.path.join(OUT, 'cars', i, 'transmission', 'index.html'))]
        if years or _tl:
            body.append('<div class="cpx">' + (f'<p><b>Years owners report it on most:</b> ' + ' · '.join(f'<a href="/cars/{i}/{y}/">{y} {E(nm)}</a>' for i, nm, y, k in years[:6]) + '</p>' if years else '')
                        + (f'<p><b>Transmission problems by year:</b> ' + ' · '.join(f'<a href="/cars/{i}/transmission/">{E(nm)}</a>' for i, nm in _tl[:6]) + '</p>' if _tl else '') + '</div>')
        body.append('<h2>The details</h2>' + ''.join(f'<details class="cpd"><summary>{q}</summary>{h}</details>' for q, h in det))
        if rel: body.append('<h2>Related codes</h2><p class="crel">' + ' '.join(f'<a href="/check-engine-light/{r.lower()}/">{r}</a>' for r in rel) + '</p>')
        faq0 = [(f'What does {c} mean?', f'{mm["t"]}. {mm["m"]}'), (f'Can I drive with {c}?', f'{st[0]}. {st[1]}'), (f'What causes {c}?', '; '.join(mm['c']) + '.')] if mm else []
        if faq0: body.append('<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq0)) + '</section>')
        body.append(SEARCH_MINI.replace('Check engine light on? Look up the code', 'Look up another code') +
                    f'<p class="note">Counts: NHTSA owner complaints whose text names {c}. A complaint is an owner&#39;s report, not a diagnosis. Meanings: the standard SAE J2012 definitions in our own words; '
                    'manufacturer codes only where verified for that make. General information, not repair advice for your car.</p></article>')
        CEL_HERO = hero
        faq = []
        if mm:
            faq = [(f'What does {c} mean?', f'{mm["t"]}. {mm["m"]}'), (f'Can I drive with {c}?', f'{st[0]}. {st[1]}'), (f'What causes {c}?', '; '.join(mm['c']) + '.')]
        ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": html.unescape(a)}} for q, a in faq]}] if faq else None
        tt = f'{c} Code: Meaning, Causes and Which Cars Get It | The Lemon Index' if mm else f'{c} Code: Which Cars Report It and What It Can Mean | The Lemon Index'
        desc = (f'{c} means {mm["t"]}. How serious it is, common causes, and the cars owners report it on most.' if mm else
                f'{c} is a {"manufacturer-specific" if not _generic(c) else "standard"} {SYSW[c[0]]} code. See which makes and models owners report it on, from {v["n"]:,} complaints to the U.S. government.')
        page(path, tt, desc, ''.join(body) + CODES_JS, ld=ld, vis=CEL_HERO)
        if indexed: CODE_URLS.append(path)
        else:
            CODE_NOINDEX.append(path); p = os.path.join(OUT, path.strip('/'), 'index.html')
            s = open(p, encoding='utf-8').read(); open(p, 'w', encoding='utf-8').write(s.replace('<link rel="canonical"', '<meta name="robots" content="noindex,follow"><link rel="canonical"', 1))
    # codes with a meaning but (almost) no complaints still answer in the search box
    for c in list(ECD.D) + list(ECD.MAKE):
        if c not in idx:
            mm = _meaning(c); idx[c] = dict(n=0, mk=[], top=[], p=0, t=mm['t'], m=mm['m'], s=mm['s'], c=mm['c'][:3], mf=mm.get('makes') if mm['mk'] else None, w=mm.get('w'))
    os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
    json.dump(dict(total=EC['total'], codes=idx), open(os.path.join(OUT, 'assets', 'codes.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('engine code pages', len(CODE_URLS), 'indexed', len(CODE_NOINDEX), 'noindex | search index', len(idx), 'codes')

def cel_top_html():
    """11-10 v2: the codes owners report most, as a filterable grid of cards (assets/cardfilter.js) instead of 30 table rows."""
    if not EC: return ''
    rows = [(c, v) for c, v in EC['codes'].items() if f'/check-engine-light/{c.lower()}/' in CODE_URLS][:30]
    sevc = lambda c: (_meaning(c) or {}).get('s') or 0
    return ('<section class="yc" id="codes"><h2>Engine codes owners report most</h2>'
            '<input class="cf-q" type="search" placeholder="Filter, e.g. misfire or P0420" aria-label="Filter the codes" data-filter="#cgrid">'
            '<div class="cgrid" id="cgrid">' +
            ''.join(f'<a class="cgc s{sevc(c)}" href="/check-engine-light/{c.lower()}/"><b>{c}</b><span>{E(_meaning(c)["t"])}</span><small>{v["n"]:,} complaints</small></a>' for c, v in rows) +
            f'</div><p class="cf-none" hidden>No code in this list matches. Use the code box above for any code.</p><p class="yc-cap">From {EC["total"]:,} owner complaints to NHTSA that name a trouble code. The color dot is how serious the code usually is: yellow get it checked, orange soon, red now.</p></section>')
_code_pages()
