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
        body = [f'<div class="advp cpage"><header class="advh1"><p class="ph-e"><a href="/check-engine-light/">Check engine light</a> / Engine codes</p>'
                f'<h1>{c}: {E(title_bits)}</h1><p class="ans">{ans}</p></header>']
        body.append(f'<div class="creadout"><div class="cr-code"><span class="cr-sys">{E(SYSN[c[0]].split(" (")[0])} · {"Generic" if _generic(c) else "Manufacturer"}</span><b>{c}</b></div>' + (gauge(sev, w=bool(mm.get("w"))) if sev else '') + '</div>')
        body.append('<div class="ygrid">')
        if mm:
            body.append(f'<section class="yc" id="meaning"><h2>What {c} means</h2><p>{E(mm["m"])}</p>' +
                        (f'<p class="yc-cap">This meaning applies to {E(", ".join(mm["makes"]))}. On other makes {c} can mean something different.</p>' if mm['mk'] else '') + '</section>')
            body.append(f'<section class="yc" id="serious"><h2>Can I drive with {c}?</h2><p><b>{E(st[0])}.</b> {E(st[1])}</p>' +
                        (f'<p>{_pct(th[0][1], v["n"])}% of the owner complaints that name {c} also say the car {E(th[0][0])}. A complaint can describe more than one problem, so this doesn&#39;t prove the code caused it.</p>' if th else '') +
                        (f'<p>{_pct(v["towed"], v["n"])}% of those owners said the car had to be towed.</p>' if v['towed'] >= 5 and _pct(v['towed'], v['n']) >= 5 else '') + '</section>')
            body.append(f'<section class="yc" id="causes"><h2>Common causes of {c}</h2><ul class="fx">' + ''.join(f'<li>{E(x)}</li>' for x in mm['c']) + '</ul><p class="yc-cap">A shop should confirm the cause with a scan and tests before replacing parts.</p></section>')
        else:
            body.append(f'<section class="yc" id="meaning"><h2>What {c} means</h2><p>{_nomean(c)[2]} We haven&#39;t verified its meaning yet. A dealer or a scanner with the maker&#39;s software can tell you exactly what it means on your car.</p>'
                        f'<p>Owners who reported it drive: ' + ', '.join(f'{E(m)} ({k})' for m, k in v['makes'][:4]) + '.</p></section>')
        if models:
            body.append(f'<section class="yc" id="cars"><h2>Cars whose owners report {c} most</h2><div class="tw"><table class="adv"><thead><tr><th>Model</th><th>Complaints naming {c}</th></tr></thead><tbody>' +
                        ''.join(f'<tr><td><a href="/cars/{i}/">{E(nm)}</a></td><td>{k:,}</td></tr>' for i, nm, k in models) + '</tbody></table></div><p class="yc-cap">Raw complaint counts, not a failure rate: popular models get more complaints.</p>' +
                        ((f'<p class="yc-cap">Model years with the most complaints naming {c}: ' + ', '.join(f'<a href="/cars/{i}/{y}/">{y} {E(nm)}</a> ({k})' for i, nm, y, k in years[:6]) + '.</p>') if years else '') + '</section>')
        if th:
            body.append(f'<section class="yc" id="owners"><h2>What owners describe</h2><ul class="fx">' + ''.join(f'<li>{E(t[0].upper() + t[1:])}: {_pct(k, v["n"])}% of complaints</li>' for t, k in th) +
                        '</ul><p class="yc-cap">Share of complaints naming the code whose text also mentions each problem. Counted from the complaint text; we don&#39;t publish the complaints themselves.</p></section>')
        rel = [r for r in C if r != c and r[:4] == c[:4] and (_meaning(r) is not None and C[r]['n'] >= 5 or C[r]['n'] >= 20)][:8]
        if rel: body.append('<section class="yc" id="related"><h2>Related codes</h2><p class="crel">' + ' '.join(f'<a href="/check-engine-light/{r.lower()}/">{r}</a>' for r in rel) + '</p></section>')
        body.append('</div>' + SEARCH_MINI.replace('Check engine light on? Look up the code', 'Look up another code') +
                    f'<p class="yc-cap">Counts: NHTSA owner complaints whose text names {c}, all model years in our copy of the database. A complaint is an owner&#39;s report, not a diagnosis, and most owners with a code never file one. '
                    'Meanings: the standard SAE J2012 code definitions, explained in our own words; manufacturer codes are explained only where the meaning for that make was verified. General information, not repair advice for your car.</p></div>')
        faq = []
        if mm:
            faq = [(f'What does {c} mean?', f'{mm["t"]}. {mm["m"]}'), (f'Can I drive with {c}?', f'{st[0]}. {st[1]}'), (f'What causes {c}?', '; '.join(mm['c']) + '.')]
        ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": html.unescape(a)}} for q, a in faq]}] if faq else None
        tt = f'{c} Code: Meaning, Causes and Which Cars Get It | The Lemon Index' if mm else f'{c} Code: Which Cars Report It and What It Can Mean | The Lemon Index'
        desc = (f'{c} means {mm["t"]}. How serious it is, common causes, and the cars owners report it on most.' if mm else
                f'{c} is a {"manufacturer-specific" if not _generic(c) else "standard"} {SYSW[c[0]]} code. See which makes and models owners report it on, from {v["n"]:,} complaints to the U.S. government.')
        page(path, tt, desc, ''.join(body) + CODES_JS, ld=ld)
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
    if not EC: return ''
    rows = [(c, v) for c, v in EC['codes'].items() if f'/check-engine-light/{c.lower()}/' in CODE_URLS][:30]
    return ('<section class="yc" id="codes"><h2>Engine codes owners report most</h2><div class="tw"><table class="adv"><thead><tr><th>Code</th><th>What it means</th><th>Complaints</th></tr></thead><tbody>' +
            ''.join(f'<tr><td><a href="/check-engine-light/{c.lower()}/"><b>{c}</b></a></td><td>{E(_meaning(c)["t"])}</td><td>{v["n"]:,}</td></tr>' for c, v in rows) +
            f'</tbody></table></div><p class="yc-cap">From {EC["total"]:,} owner complaints to NHTSA that name a trouble code. Type any code in the box above for the full answer.</p></section>')
_code_pages()
