# 11-25 (Elijah approved the mockup "menu mockup 1124/insurance/insurance.html": "yes do this stuff"): the car insurance section.
#   /insurance/                 the tool: state, age, record, car type -> the state's official by-company prices (cheapest first), or our
#                               anchored estimate of the typical price where a state publishes none ("we won't guess" which company is cheapest)
#   /insurance/<state-slug>/    one page per state (51): that state's official table or estimate, the other sample drivers, FAQ from real data
# Promise on the page: no phone/email/name, no agents, we don't sell info, insurers can't pay to rank higher. No affiliate links, no lead forms.
# Data: data/insurance.json + assets/insurance.json (data_insurance.py, from 3 Lemon Index/data/insurance/: anchor.py, anchor.md).
# "Add what you pay": assets/insurance.js -> lemon-survey Worker POST /ins (anonymous, Turnstile). The pages read NOTHING from D1.
# Run by build.py with exec() twice: INSX = 'hooks' near the top (INS_HOOK: the "Compare insurers for you" row on car year pages, called in
# page() after the date hash), INSX = 'pages' near the end (the pages; INS_THIN = estimate-only state pages, noindexed by quality_gate.py).
if INSX == 'hooks':
    _INS_YEAR = re.compile(r'^/cars/([^/]+(?:/[a-z]+)?)/(\d{4})/$')
    _INS_ROW = ('<section class="cpl-sec cpl-pan" id="p-ins"><style>#p-ins .cpl>.cpl-a,#p-ins .cpl>.cpl-a:hover{{text-decoration:none;color:inherit;box-shadow:none;border-radius:0}}'
                '#p-ins .cpl>.cpl-a{{background:transparent}}#p-ins .cpl>.cpl-a:hover{{background:#ebebee}}</style><div class="cpl"><a class="cpl-a sb-go" href="{h}">'
                '<svg aria-hidden="true" class="cpl-i" focusable="false" height="24" width="24"><use href="/assets/ic.svg?v=2#shield"></use></svg><span><b>Compare insurers for you</b></span>'
                '<svg aria-hidden="true" class="cpl-ar" fill="none" height="18" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" viewbox="0 0 24 24" width="18">'
                '<path d="m9 6 6 6-6 6"></path></svg></a></div></section>')

    def INS_HOOK(path, doc):
        """car year pages: 'Compare insurers for you' right under 'Find a car for your budget' (the site shows no insurance figure on car pages yet)"""
        m = _INS_YEAR.match(path)
        if not m or 'id="p-ins"' in doc: return doc
        i = doc.find('id="p-budget"')
        if i < 0: return doc
        j = doc.find('</section>', i)
        if j < 0: return doc
        h = '/insurance/' + ('#car=truck' if PRICEBOX.seg_of(m.group(1)) == 'truck' else '')
        return doc[:j + 10] + _INS_ROW.format(h=h) + doc[j + 10:]

if INSX == 'pages':
    INS = json.load(open('data/insurance.json', encoding='utf-8'))
    INS_M, INS_S = INS['meta'], INS['states']
    INS_CSS = '<link rel="stylesheet" href="/assets/insurance.css?v=1">'
    INS_JS = '<script src="/assets/insurance.js?v=1" defer></script>'
    SEGN['insurance'] = 'Car insurance'
    INS_THIN = set(); INS_URLS = ['/insurance/']
    _ins_m = lambda v: f'${v:,}'
    INS_AGES = INS_M['ages']
    INS_CARN = {'regular': 'Regular car', 'truck': 'Truck', 'sports': 'Sports car', 'super': 'Supercar'}

    def _ins_pick(st, age=35, rec='clean', kind='regular'):
        """the state's sample driver closest to the visitor (same rule as insurance.js pick())"""
        gs = (INS_S[st].get('off') or {}).get('groups') or []
        def score(g):
            a = 15 if g['age'] is None else abs(g['age'] - age)
            k = 0 if g['kind'] == kind or (kind in ('sports', 'super') and g['kind'] == 'regular') else 8 if g['kind'] in ('truck', 'regular') else 10
            return a + (0 if g['rec'] == rec else 12) + k + (1 if g['cpl'] else 0) + (0 if g['cov'] == 'full' else 2)
        return min(gs, key=score) if gs else None

    def _ins_short(g):
        p = g['lab'].split(', '); i = next((k for k, x in enumerate(p) if re.search(r'record|ticket|accident|DUI|violation', x)), 1)
        return ', '.join(p[:i + 1]) + {'truck': ', pickup', 'ev': ', Tesla'}.get(g['kind'], '')

    def _ins_rows(g, cap=None):
        rows = [r for r in g['rows'] if r[0] != 'USAA']; us = next((r for r in g['rows'] if r[0] == 'USAA'), None)
        mx = max([r[1] for r in g['rows']] or [1])
        out, n = '', 0
        for b, v, e in rows:
            n += 1
            out += (f'<li class="ins-r{" ins-top" if n == 1 else ""}{" ins-more" if cap and n > cap else ""}" title="{E(e)}"><span class="ins-n">{n}</span><span class="ins-nm">{E(b)}</span>'
                    f'<span class="ins-bar"><i style="width:{max(3, v / mx * 100):.0f}%"></i></span><span class="ins-p">{_ins_m(v)}</span></li>')
        if us:
            out += (f'<li class="ins-r ins-usaa" title="{E(us[2])}"><span class="ins-n"></span><span class="ins-nm">USAA<small>Military families only</small></span>'
                    f'<span class="ins-bar"><i style="width:{max(3, us[1] / mx * 100):.0f}%"></i></span><span class="ins-p">{_ins_m(us[1])}</span></li>')
        more = (f'<button type="button" class="ins-all">Show all {len(rows)} companies</button>' if cap and len(rows) > cap else '')
        return f'<ol class="ins-list{" ins-cap" if cap and len(rows) > cap else ""}">{out}</ol>{more}', rows

    def _ins_src(st, g):
        o = INS_S[st]['off']; nm = INS_S[st]['n']
        places = f', middle price across {g["nloc"]} {nm} sample places' if g['nloc'] > 1 else ''
        return (f'<p class="ins-src">Source: <a href="{E(o["url"])}" rel="noopener nofollow" target="_blank">{E(o["who"])}</a>, {E(o["what"])}. '
                f'Their sample driver: {E(g["lab"][0].lower() + g["lab"][1:])}{places}. Your own quote will differ: use this to know who to call first.</p>'
                + (f'<p class="ins-note">{E(o["note"])}</p>' if o['note'] else ''))

    def _ins_official_card(st, g, you):
        lst, rows = _ins_rows(g, cap=10)
        top = rows[0] if rows else g['rows'][0]
        return (f'<p class="ins-you">{you}</p><div class="ins-card"><div class="ins-big">Cheapest for this driver<b>{E(top[0])} · {_ins_m(top[1])}/mo</b></div>'
                f'{lst}{_ins_src(st, g)}</div>')

    def _ins_est(st, ag='30-39', rec='clean'):
        v = INS_S[st]['est'][INS_AGES.index(ag)]
        return round(v * (INS_S[st]['rm'][rec] if rec != 'clean' else 1))

    def _ins_est_card(st, you):
        d = INS_S[st]; v = _ins_est(st); e = INS_M['err'] / 100
        lo, hi = round(v * (1 - e)), round(v * (1 + e))
        tool = (f'<p>{E(d["n"])}&#39;s insurance department publishes its own comparison by company, which we haven&#39;t added yet: '
                f'<a href="{E(d["tool"][0])}" rel="noopener nofollow" target="_blank">{E(d["tool"][1])}</a>.</p>' if d.get('tool') else '')
        return (f'<p class="ins-you">{you}</p><div class="ins-card"><div class="ins-big">Typical price for you <span class="ins-est">Estimate</span><b>About {_ins_m(v)}/mo</b></div>'
                f'<div class="ins-rb" style="--m:50%"><i></i></div><div class="ins-range"><span>{_ins_m(lo)}</span><span>likely range</span><span>{_ins_m(hi)}</span></div>'
                f'<p class="ins-src">{E(d["n"])} doesn&#39;t publish prices by company, so this is our estimate: the official NAIC 2024 average for {E(d["n"])}, adjusted for age and record. '
                f'In states that do publish prices, our estimates were off by about {INS_M["err"]}% up or down, so treat it as a rough guide, not a quote.</p></div>'
                f'<div class="ins-warn"><p><b>Which company is cheapest?</b> We don&#39;t know yet for {E(d["n"])}, and we won&#39;t guess. Every price people add below gets us closer.</p>{tool}</div>')

    def _ins_form(st=''):
        opts = ''.join(f'<option value="{k}"{" selected" if k == st else ""}>{E(v["n"])}</option>' for k, v in sorted(INS_S.items(), key=lambda x: x[1]['n']))
        ages = ''.join(f'<option value="{a}"{" selected" if a == 35 else ""}>{a}{"+" if a == 85 else ""}</option>' for a in range(16, 86))
        chip = lambda grp, k, l, on: f'<button type="button" class="ins-c" data-{grp}="{k}" aria-pressed="{"true" if on else "false"}">{l}</button>'
        recs = ''.join(chip('rec', k, l, k == 'clean') for k, l in (('clean', 'Clean'), ('ticket', 'Ticket'), ('accident', 'Accident'), ('dui', 'DUI')))
        cars = ''.join(chip('kind', k, l, k == 'regular') for k, l in INS_CARN.items())
        return (f'<form class="ins-card ins-f" id="insf" autocomplete="off" data-st="{st}"><div class="ins-g2"><label class="ins-fl">State<select name="st" required>'
                f'{"" if st else "<option value=\"\" selected disabled>Pick your state</option>"}{opts}</select></label>'
                f'<label class="ins-fl">Your age<select name="age">{ages}</select></label></div>'
                f'<div class="ins-g2"><div class="ins-fl"><span>Driving record (last 3 years)</span><div class="ins-chips" role="group" aria-label="Driving record">{recs}</div></div>'
                f'<div class="ins-fl"><span>Car you&#39;re getting</span><div class="ins-chips" role="group" aria-label="Car type">{cars}</div></div></div>'
                f'<button class="ins-go" type="submit">Show my prices</button></form>')

    def _ins_add(st=''):
        nm = INS_S[st]['n'] if st else 'your state'
        return (f'<section class="ins-add" id="add" aria-labelledby="ins-add-h"{"" if st else " hidden"}><button type="button" class="ins-go ins-y ins-open" aria-expanded="false" aria-controls="insaf">Help others: add what you pay</button>'
                f'<form class="ins-card" id="insaf" data-ts="{TS}" hidden autocomplete="off" novalidate><h2 id="ins-add-h">Help fill in <span class="ins-stn">{E(nm)}</span></h2>'
                '<p class="ins-for"></p>'
                '<label class="ins-in"><span>Your age</span><input name="age" type="number" inputmode="numeric" min="16" max="99" required></label>'
                '<label class="ins-in"><span>Your insurance company</span><input name="company" list="ins-cos" maxlength="40" required></label>'
                '<label class="ins-in"><span>What you pay per month ($)</span><input name="usd" type="number" inputmode="numeric" min="20" max="3000" required></label>'
                '<label class="ins-in"><span>Your car (year, make, model)</span><input name="car" maxlength="60" placeholder="2019 Honda Civic"></label>'
                '<div class="ins-hp" aria-hidden="true"><label>Leave this empty<input name="hp" tabindex="-1" autocomplete="off"></label></div><div class="ins-ts"></div>'
                '<p class="ins-lock">No name, email or phone. Ever.</p><button class="ins-go" type="submit">Add my price</button><p class="ins-msg" role="status" aria-live="polite" hidden></p></form></section>')

    _INS_COS = sorted({r[0] for v in INS_S.values() for g in (v.get('off') or {}).get('groups', []) for r in g['rows']} | {'State Farm', 'GEICO', 'Progressive', 'Allstate', 'USAA', 'Liberty Mutual', 'Farmers', 'Nationwide', 'Travelers', 'American Family', 'Erie', 'Auto-Owners'})
    INS_DL = '<datalist id="ins-cos">' + ''.join(f'<option value="{E(c)}">' for c in _INS_COS) + '</datalist>'

    def _ins_method():
        m = INS_M
        return V5_BOX('info', 'How this works', (
            f'<p><b>Official prices.</b> 11 state insurance departments publish what each company charges sample drivers: DC, Florida, Hawaii, Kentucky, Maryland, Nebraska, '
            f'Nevada, North Dakota, Oklahoma, Utah and West Virginia. We show their numbers per month (yearly or 6-month premiums divided down), each company at the middle of its '
            f'prices across the state&#39;s sample places, and pick the sample driver closest to your age and record. Brands with several companies show their cheapest one '
            f'(hover a row for the company&#39;s legal name). Old or minimum-coverage sources carry a note.</p>'
            f'<p><b>Estimates.</b> Where a state publishes nothing by company, we show a typical price: the official <a href="{m["naic_url"]}" rel="noopener nofollow" target="_blank">NAIC 2024 average premium</a> '
            f'for that state (liability, collision and comprehensive), scaled to one driver with full coverage and adjusted by an AI-estimated age and record curve. '
            f'Tested against 22 published sample drivers in 6 states (each state held out in turn), it was off by {m["err"]}% on average (worst {m["max_err"]}%). '
            f'The AI&#39;s own prices were off by {m["raw_err"]}%. It runs low for teens and young drivers. We never use AI to rank companies: it picked the cheapest one in 1 state out of 8.</p>'
            f'<p><b>Car type.</b> No official source prices car types for these drivers, so this part is always our estimate: trucks ×{m["car"]["truck"]:g} (in Nevada&#39;s guide a Ram 1500 cost about 4% less than a Corolla), '
            f'sports cars ×{m["car"]["sports"]:g}, supercars ×{m["car"]["super"]:g}. It changes the price, never the order of the companies.</p>'
            '<p><b>What we promise.</b> Nothing to sign up for, no agents, we don&#39;t sell your info, and insurers can&#39;t pay to rank higher. There are no affiliate links on these pages. '
            'Prices people add go to a review list first and are not shown yet.</p>'), 'how')

    def _ins_states_box(cur=''):
        li = ''.join(f'<a href="/insurance/{v["slug"]}/"{" aria-current=\"page\"" if k == cur else ""}>{E(v["n"])}{"<small>State prices</small>" if v.get("off") else ""}</a>'
                     for k, v in sorted(INS_S.items(), key=lambda x: x[1]['n']))
        return V5_BOX('signpost', 'Every state', f'<nav class="ins-sts" aria-label="Car insurance by state">{li}</nav>', 'states')

    def _ins_page(st=''):
        d = INS_S.get(st)
        if d:
            g = _ins_pick(st)
            you = f'35 · clean record · regular car · {E(d["n"])}' if not g else f'{E(d["n"])} · closest sample driver to a 35-year-old with a clean record'
            res = _ins_official_card(st, g, you) if g else _ins_est_card(st, f'35 · clean record · regular car · {E(d["n"])}')
            if g and g['cov'] != 'full' or (d.get('off') and d['off']['stale']):
                res += f'<p class="ins-extra">Typical full-coverage price for a 35-year-old with a clean record: about {_ins_m(_ins_est(st))}/mo <span class="ins-est">Estimate</span></p>'
        else: res = ''
        h1 = f'Cheapest car insurance in {E(d["n"])}' if d else 'Find the cheapest car insurance for you'
        sub = (f'{"Real prices by company from " + E(d["off"]["who"]) if d.get("off") else "A clearly marked estimate for " + E(d["n"]) + ", and the companies when we know them"}. Nothing to sign up for.' if d
               else 'Real prices by company from state insurance departments where they publish them, clearly marked estimates where they don&#39;t. Nothing to sign up for.')
        top = (f'{INS_CSS}<div class="ins" data-ins="1"><header class="ins-h"><p class="ins-bc"><a href="/insurance/">Car insurance</a></p><h1>{h1}</h1><p class="ins-sub">{sub}</p>'
               '<ul class="ins-trust"><li>No phone number, no email, no agents</li><li>We don&#39;t sell your info</li><li>Insurers can&#39;t pay to rank higher</li></ul></header>')
        if not d: top = top.replace('<p class="ins-bc"><a href="/insurance/">Car insurance</a></p>', '')
        boxes = []
        if d and d.get('off'):
            o = d['off']; g0 = _ins_pick(st)
            oth = [g for g in o['groups'] if g is not g0]
            if oth:   # one title-only box (Eli review 11-25: 17 separate boxes were a wall); each driver opens inside it
                inner = ''.join(f'<details class="ins-sd" id="g-{re.sub(r"[^a-z0-9]+", "-", g["id"].lower())}"><summary>{E(_ins_short(g))}</summary>{_ins_rows(g)[0]}{_ins_src(st, g)}</details>' for g in oth)
                boxes.append(V5_BOX('chart', f'Other sample drivers ({len(oth)})', inner, 'drivers'))
            ents = ''.join(f'<tr><td>{E(e)}</td><td class="num">{_ins_m(v)}</td></tr>' for e, v in g0['ents'])
            boxes.append(V5_BOX('data', 'Every company as the state lists it', f'<p class="ins-src">{E(g0["desc"])}</p><div class="tw"><table><thead><tr><th>Company</th><th>Per month</th></tr></thead><tbody>{ents}</tbody></table></div>', 'all'))
        if d:
            e = INS_M['err']
            rows = ''.join(f'<tr><td>{a}</td><td class="num">{_ins_m(v)}</td></tr>' for a, v in zip(INS_AGES, d['est']))
            rec = ''.join(f'<tr><td>{l}</td><td class="num">{_ins_m(_ins_est(st, "30-39", r))}</td></tr>' for r, l in (('ticket', 'One speeding ticket'), ('accident', 'One at-fault accident'), ('dui', 'One DUI')))
            boxes.append(V5_BOX('tag', 'Typical price by age (estimate)', f'<div class="tw"><table><thead><tr><th>Age</th><th>Per month, clean record</th></tr></thead><tbody>{rows}</tbody></table></div>'
                                f'<div class="tw"><table><thead><tr><th>Age 30-39 with</th><th>Per month</th></tr></thead><tbody>{rec}</tbody></table></div>'
                                f'<p class="ins-src">Our estimate, full coverage, regular car: the NAIC 2024 average for {E(d["n"])} ({_ins_m(round(d["naic"] / 12))}/mo across all drivers and policies), '
                                f'adjusted for one driver, age and record. Off by about {e}% up or down where states publish prices.</p>', 'ages'))
        faq = _ins_faq(st)
        body = (top + _ins_form(st) + f'<div id="ins-out" class="ins-out" aria-live="polite">{res}</div>' + _ins_add(st) + INS_DL
                + (f'<div class="cpl cp5-pl ins-boxes">{"".join(boxes)}</div>' if boxes else '')
                + '<section class="ins-faq"><h2>Questions</h2>' + ''.join(f'<details><summary>{E(q)}</summary><p>{a}</p></details>' for q, a in faq) + '</section>'
                + f'<div class="cpl cp5-pl ins-boxes">{_ins_method()}{_ins_states_box(st)}</div></div>'
                + INS_JS)
        return body, faq

    def _ins_faq(st):
        if not st:
            m = INS_M
            return [('Which car insurance company is cheapest?', 'It depends on your state, age and record, and the order changes a lot from state to state. Where a state insurance department publishes prices by company, this page ranks them for the sample driver closest to you.'),
                    ('Which states publish car insurance prices by company?', 'DC, Florida, Hawaii, Kentucky, Maryland, Nebraska, Nevada, North Dakota, Oklahoma, Utah and West Virginia publish them, and this page shows them. Alabama, Arizona, California, Colorado, New Hampshire, South Carolina and Texas have their own comparison tools, linked on their state pages.'),
                    ('How accurate are the estimates?', f'Tested against 22 published sample drivers in 6 states, our estimates were off by {m["err"]}% on average, up or down (worst {m["max_err"]}%). They run low for teens and young drivers.'),
                    ('Do you sell my information?', 'No. The tool runs in your browser and saves nothing. There is no sign-up, no phone number and no email. Insurers cannot pay to rank higher, and these pages have no affiliate links.')]
        d = INS_S[st]; nm = d['n']; nav = _ins_m(round(d['naic'] / 12)); out = []
        if d.get('off'):
            o = d['off']; g = _ins_pick(st); rows = [r for r in g['rows'] if r[0] != 'USAA']; us = next((r for r in g['rows'] if r[0] == 'USAA'), None)
            t3 = ', '.join(f'{E(b)} ({_ins_m(v)}/mo)' for b, v, _ in rows[:3])
            out.append((f'Which company has the cheapest car insurance in {nm}?',
                        f'In the {E(o["who"])}&#39;s {E(o["what"])}, the cheapest for its sample driver ({E(g["lab"][0].lower() + g["lab"][1:])}) were {t3}.'
                        + (f' USAA was {_ins_m(us[1])}/mo, for military families only.' if us else '') + (' ' + E(o['note']) if o['note'] else '')))
            out.append((f'How much is car insurance in {nm} per month?',
                        f'The NAIC&#39;s 2024 average for {nm} was {nav}/mo (liability, collision and comprehensive, across all drivers). '
                        f'In the state&#39;s own guide, that sample driver paid {_ins_m(rows[0][1])} to {_ins_m(rows[-1][1])} a month depending on the company.'))
        else:
            out.append((f'How much is car insurance in {nm} per month?',
                        f'The NAIC&#39;s 2024 average for {nm} was {nav}/mo (liability, collision and comprehensive, across all drivers). Our estimate for a 35-year-old with a clean record '
                        f'and full coverage is about {_ins_m(_ins_est(st))}/mo, which can be off by about {INS_M["err"]}% either way.'))
            out.append((f'Which company has the cheapest car insurance in {nm}?',
                        f'We don&#39;t know yet. {nm} doesn&#39;t publish prices by company in a form we could add, and we won&#39;t guess.'
                        + (f' Its insurance department has its own comparison: <a href="{E(d["tool"][0])}" rel="noopener nofollow" target="_blank">{E(d["tool"][1])}</a>.' if d.get('tool') else '')))
        return out

    def _ins_build():
        b, faq = _ins_page()
        ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": "Cheapest car insurance finder", "url": BASE + '/insurance/', "applicationCategory": "FinanceApplication",
               "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
               "description": "Ranks car insurance companies by price from state insurance department data where states publish it, and gives a clearly labelled estimate where they don't. No sign-up, nothing saved."},
              faq_ld([(q, '', re.sub(r'<[^>]+>', '', a).replace('&#39;', "'")) for q, a in faq])]
        page('/insurance/', 'Cheapest Car Insurance by State, Age and Record | Lemon Index',
             'Which insurer is cheapest for you: official prices by company from state insurance departments, monthly, and an honest estimate where states publish none. No sign-up.', b, ld=ld)
        for st, d in INS_S.items():
            u = f'/insurance/{d["slug"]}/'; b, faq = _ins_page(st); INS_URLS.append(u)
            if d.get('off'):
                g = _ins_pick(st); rows = [r for r in g['rows'] if r[0] != 'USAA']
                t = f'Cheapest Car Insurance in {d["n"]} by Company ({d["off"]["year"]} State Data)'
                ds = (f'{d["off"]["who"]} {d["off"]["year"]} prices, monthly: ' + ', '.join(f'{b_} ${v}' for b_, v, _ in rows[:3])
                      + f' for a sample {g["lab"].split(", ")[0].lower()} driver. Every company, cheapest first. No sign-up.')
            else:
                INS_THIN.add(u)   # estimate only: useful to a visitor, too little of its own for search (lemon-thin-page-gate)
                t = f'Car Insurance in {d["n"]}: Typical Monthly Price by Age'
                ds = (f'About ${_ins_est(st)}/mo for a 35-year-old with a clean record (our estimate from the NAIC 2024 {d["n"]} average, ±{INS_M["err"]}%). '
                      'Ticket, accident and DUI too. No sign-up.')
            page(u, t, ds, b, ld=[faq_ld([(q, '', re.sub(r'<[^>]+>', '', a).replace('&#39;', "'")) for q, a in faq])])
        if 'SEO_URLS' in globals(): SEO_URLS.extend(INS_URLS)

    _ins_build()
