# 11-14 growth plan 2B-1 (Elijah approved the growth plan chunks): recall check pages that feed the /vin/ report.
# Run by build.py with exec(), so YEARS, BYNAME, extra, page, E, rsum, rtag_html, RPART, car_href, aph, pimg, who, pcredit ... are in scope.
#   RCLP = 'hooks' (before the car pages): RCL_LINK(path, body), called by page() AFTER the date hash (so no page is redated for a link):
#                  year pages and complaints-only pages get "every <model> recall" + "all <make> recalls" links in their recall section,
#                  model pages get a link in their "How many recalls" answer.
#   RCLP = 'pages' (before the sitemap):
#     /recalls/                 hub for "recall check", "is my car recalled", "car recalls by VIN": a VIN box (hands the VIN to /vin/), a
#                               make/model/year picker that lists the live NHTSA recalls in the browser (assets/rc.js), every make, the
#                               biggest and newest recalls, an honest "open on your car?" note and an FAQ.
#     /recalls/<make>/          recall campaigns by model, the biggest by vehicles covered, the newest, NHTSA's park-it warnings, FAQ.
#                               noindex when thin (fewer than 2 models with recalls or under 15 campaigns).
#     /recalls/<make>/<model>/  only for models with 8+ campaigns: the car pages list recalls one model year at a time and the model page
#                               only counts them, so this is the one list of every campaign across the years (each once, with the years it
#                               covers and the vehicles in the campaign). Smaller models link straight to their car page instead.
# Data: the site's own NHTSA recall lists (data/extras_api*.json, data/extra_models*.json via extra()), plus data/recall_units.json
# (data_recall_units.py: vehicles per campaign and the do-not-drive / park-outside flags from NHTSA's recall flat file, 2010 and later).
import json as _rclj, os as _rclos, re as _rclre
if RCLP == 'hooks':
    _RCLU = _rclj.load(open('data/recall_units.json', encoding='utf-8')) if _rclos.path.exists('data/recall_units.json') else {}
    _RCL = {}
    RCL_MODEL_MIN, RCL_MAKE_MIN = 8, 15
    _rclslug = lambda b: b.lower().replace(' ', '-')
    _rcldk = lambda r: (r.get('date') or '')[6:10] + (r.get('date') or '')[3:5] + (r.get('date') or '')[:2]   # NHTSA dates are DD/MM/YYYY
    _RCLMN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    def _rcldate(r):
        d = r.get('date') or ''
        return f'{_RCLMN[int(d[3:5]) - 1]} {d[6:10]}' if _rclre.match(r'^\d\d/(0[1-9]|1[0-2])/\d{4}$', d) else E(d[-4:])
    def _rclspan(ys):
        ys = sorted(set(ys)); out = []; i = 0
        while i < len(ys):
            j = i
            while j + 1 < len(ys) and ys[j + 1] == ys[j] + 1: j += 1
            out.append(str(ys[i]) if i == j else f'{ys[i]}–{ys[j]}'); i = j + 1
        return ', '.join(out)
    def _rcl_data():
        """models + makes with their recall campaigns, built once (first call: after every hook that edits the recall lists has run)"""
        if _RCL: return _RCL
        M = {}
        for f in YEARS:
            b = BYNAME[f['name']]['brand']; m = M.setdefault(f['id'], dict(id=f['id'], name=f['name'], brand=b, recs={}, ry={}, yc={}, years=[v['y'] for v in f['years']], kind='y'))
            for v in f['years']:
                rs = extra(f['id'], v['y']).get('recalls')
                if rs is None: continue
                m['yc'][v['y']] = 0
                for r in rs:
                    c = r.get('id')
                    if not c: continue
                    m['recs'].setdefault(c, r); m['ry'].setdefault(c, set()).add(v['y']); m['yc'][v['y']] += 1
        X = _load('data/extra_models.json'); X.update(_load('data/extra_models_new.json'))
        for x in X.values():   # complaints-only models (/cars/<id>/, no year pages)
            if x['id'] in M or not x.get('brand'): continue
            m = M[x['id']] = dict(id=x['id'], name=x['name'], brand=x['brand'], recs={}, ry={}, yc={}, years=list(range(x['a'], x['b'] + 1)), kind='x')
            for r in x.get('recalls') or []:
                c = r.get('id')
                if not c: continue
                m['recs'].setdefault(c, r); ys = set(r.get('years') or []) & set(m['years']); m['ry'].setdefault(c, set()).update(ys)
                for y in ys: m['yc'][y] = m['yc'].get(y, 0) + 1
        for m in M.values():
            mk = _rclslug(m['brand']); ms = m['id'][len(mk) + 1:] if m['id'].startswith(mk + '-') else m['id']
            m['mk'] = mk; m['short'] = m['name'][len(m['brand']) + 1:] if m['name'].startswith(m['brand'] + ' ') else m['name']
            m['n'] = len(m['recs']); m['url'] = f'/recalls/{mk}/{ms.replace("/", "-")}/' if m['n'] >= RCL_MODEL_MIN else ''
            m['car'] = car_href(m['id']) if m['kind'] == 'y' else f'/cars/{m["id"]}/'
        B = {}
        for m in sorted(M.values(), key=lambda m: m['name']):
            if not m['n']: continue
            b = B.setdefault(m['brand'], dict(name=m['brand'], mk=m['mk'], models=[], recs={}, cm={}))
            b['models'].append(m)
            for c, r in m['recs'].items(): b['recs'].setdefault(c, r); b['cm'].setdefault(c, []).append(m)
        for b in B.values():
            b['n'] = len(b['recs']); b['thin'] = len(b['models']) < 2 or b['n'] < RCL_MAKE_MIN
        _RCL.update(M=M, B=B); return _RCL
    def RCL_LINK(path, body):
        bm = _rclre.fullmatch(r'/brands/([^/]+)/', path)
        if bm:   # 11-15 growth 4c: each brand page links its make's recall page, right under the hero (after the date hash: no redate)
            b = next((b for b in _rcl_data()['B'].values() if b['mk'] == bm.group(1)), None)
            i = body.find('</section>')
            if not b or i < 0 or f'/recalls/{b["mk"]}/' in body: return body
            ln = (f'<p class="yc-cap rcx-bl" style="text-align:center;margin:14px 0 0"><a href="/recalls/{b["mk"]}/"><b>{E(b["name"])} recalls</b>: '
                  f'all {b["n"]:,} NHTSA recall campaigns, by model and year →</a></p>')
            return body[:i + 10] + ln + body[i + 10:]
        mm = _rclre.match(r'^/cars/(.+?)/(?:(\d{4})/)?$', path)
        if not mm or ('id="recalls"' not in body and 'recalls does the' not in body): return body
        m = _rcl_data()['M'].get(mm.group(1))
        if not m or not m['n']: return body
        mku = f'/recalls/{m["mk"]}/'
        if 'id="recalls"' in body:
            i = body.find('id="recalls"'); j = body.find('</section>', i)
            if j < 0: return body
            ln = (f'<p class="yc-cap rcx-l">' + (f'<a href="{m["url"]}">Every {E(m["name"])} recall, all years</a> · ' if m['url'] else '')
                  + f'<a href="{mku}">All {E(m["brand"])} recalls</a></p>')
            return body[:j] + ln + body[j:]
        if m['url']:   # a model page (no recall section): its "How many recalls" answer
            for q in ('&#39;', "'"):   # the tab layout (tabbed.py) re-serializes the page, so the apostrophe may be plain
                k = f'Each year{q}s page lists them.</p>'
                if k in body: return body.replace(k, f'Each year&#39;s page lists them, and <a href="{m["url"]}">every {E(m["name"])} recall is in one list here</a>.</p>', 1)
        return body

if RCLP == 'pages':
    RCL = _rcl_data(); RCL_URLS = []; _rcl_noix = []
    _RCLCSS = '<link rel="stylesheet" href="/assets/rcx.css?v=4"><script src="/assets/rc.js?v=3" defer></script>'
    def _rcl_noindex(path):
        _f = _rclos.path.join(OUT, path.strip('/'), 'index.html'); _s = open(_f, encoding='utf-8').read()
        if 'name="robots"' not in _s: open(_f, 'w', encoding='utf-8').write(_s.replace('<link rel="canonical"', '<meta name="robots" content="noindex,follow"><link rel="canonical"', 1))
        _rcl_noix.append(path)
    def _rcl_u(c): return (_RCLU.get(c) or [0, 0, 0])
    def _rcl_flags(c):
        u = _rcl_u(c)
        return (' <span class="rtag vin-park">Park it: don&#39;t drive</span>' if u[1] else '') + (' <span class="rtag vin-park">Park outside</span>' if u[2] else '')
    _rcl_new = lambda r: _rcldk(r) >= f'{int(TODAY[:4]) - 1}{TODAY[5:7]}00'
    def _rcl_vin(note=''):
        return (f'<form class="vinf rcx-vf" autocomplete="off" action="/vin/"><input maxlength="20" placeholder="Type the 17-character VIN" aria-label="VIN" spellcheck="false">'
                f'<button class="btn" type="submit">Check recalls</button><p class="rcx-msg" role="alert" hidden></p></form>' + (f'<p class="fnote">{note}</p>' if note else ''))
    def _rcl_card(r, who_='', years=None):
        """one recall as the car pages show it (ul.rc), plus the model years it covers and the vehicles in the campaign"""
        c = r['id']; u = _rcl_u(c)
        meta = [f'recall issued {_rcldate(r)}'] + ([f'{E(who_)}'] if who_ else []) + ([f'model years {_rclspan(years)}' if len(set(years)) > 1 else f'model year {_rclspan(years)}'] if years else [])
        return (f'<li><b>{E(RPART(r.get("part")).capitalize())}</b> <small>· {" · ".join(meta)}</small>{rtag_html(r)}{_rcl_flags(c)}'
                + (' <span class="rtag rnew">New: most likely still open</span>' if _rcl_new(r) else '')
                + f'<p>{E(rsum(r))}</p><p class="rcx-m">' + (f'<b>{u[0]:,}</b> vehicles in the whole campaign · ' if u[0] else '')
                + f'<a href="https://www.nhtsa.gov/recalls?nhtsaId={E(c)}" rel="noopener nofollow" target="_blank">NHTSA {E(c)}</a></p></li>')
    def _rcl_bars(rows, unit='campaign'):
        """rows: (label html, number, sub html). Flat bars, longest first."""
        mx = max((n for _, n, _ in rows), default=1) or 1
        return ('<ul class="rcx-bars">' + ''.join(f'<li><span class="rcx-bl">{lab}</span><span class="rcx-bb"><i style="width:{max(2, round(n / mx * 100))}%"></i></span>'
                                                  f'<b>{n:,}</b>' + (f'<small>{sub}</small>' if sub else '') + '</li>' for lab, n, sub in rows) + '</ul>')
    def _rcl_faq(qa): return '<section class="yc rcx-faq"><h2>Questions</h2>' + qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in qa)) + '</section>'
    _rcl_ld = lambda qa: faq_ld([(_rclre.sub(r'<[^>]+>', '', q).replace('&#39;', "'"), '', _rclre.sub(r'<[^>]+>', '', a).replace('&#39;', "'")) for q, a in qa])
    _RCL_OPEN = ('<p><b>A recall only matters if it&#39;s still open on that exact car.</b> NHTSA&#39;s public recall data works by make, model and year, so these lists '
                'cover every car of that model year, not one VIN. Whether a recall was already fixed on a particular car is in the automaker&#39;s records: '
                'type the VIN at <a href="https://www.nhtsa.gov/recalls" rel="noopener nofollow" target="_blank">nhtsa.gov/recalls</a> or ask any dealer of that brand. '
                'The repair is free.</p>')
    _RCL_SRC = ('<p class="yc-cap">Source: NHTSA recall campaigns (api.nhtsa.gov), matched to the model names owners use in NHTSA complaints. Vehicle counts and the '
               '"park it" warnings come from NHTSA&#39;s recall file, which starts in 2010, so older recalls have no count. A campaign&#39;s count covers every '
               'make and model in it.</p>')
    # 11-19 v5 (Elijah, phone: "make this page more like the home page / the new model page"): centered title, one big number, a rounded
    # VIN field with the button inside, car cards like the home grid, and every list as a tap-to-open box (the car pages' compact style)
    _RX_IC = lambda i: f'<svg class="cpl-i" width="24" height="24" aria-hidden="true" focusable="false"><use href="/assets/ic.svg?v=1#{i}"></use></svg>'
    def _rx_box(ic, t, sub, body, id_=''):
        return (f'<details{f" id={chr(34)}{id_}{chr(34)}" if id_ else ""}><summary>{_RX_IC(ic)}<span><b>{t}</b>' + (f'<small>{sub}</small>' if sub else '')
                + f'</span>{PILL_AR}</summary><div class="cpl-b">{body}</div></details>')
    def _rx_go(ic, t, sub, href):
        return f'<a class="cpl-a" href="{href}">{_RX_IC(ic)}<span><b>{t}</b></span>{PILL_GO}</a>'   # title-only, like every compact box (11-19)
    def _rx_vin(note=''):
        return (f'<form class="vinf rcx-vf rx5-vf" autocomplete="off" action="/vin/"><input maxlength="20" placeholder="Enter a VIN (17 characters)" aria-label="VIN" spellcheck="false">'
                f'<button class="btn" type="submit">Check</button><p class="rcx-msg" role="alert" hidden></p></form>' + (f'<p class="rx5-fn">{note}</p>' if note else ''))
    _rx_big = lambda n, lab: f'<div class="rx5-big"><b>{n}</b><span>{lab}</span></div>'
    def _rx_card(href, ph, name, n, sub=''):
        tag = 'a' if href else 'div'
        return (f'<{tag} class="rx5-c"' + (f' href="{href}"' if href else '') + f'><span class="rx5-cn">{n:,}</span>{pimg(ph, name)}<b>{E(name)}</b>'
                + (f'<small>{sub}</small>' if sub else '') + f'</{tag}>')
    def _rx_bars(rows, keep=14):
        """rows: (label html, number): the model page's year chart look; the busiest row(s) red"""
        mx = max((k for _, k in rows), default=1) or 1
        li = lambda lab, k: (f'<li{" class=hi" if k == mx else ""}><span class="rx5-bl">{lab}</span><span class="rx5-bb"><i style="width:{max(3, round(k / mx * 100))}%"></i></span><b>{k:,}</b></li>')
        out = '<ul class="rx5-bars">' + ''.join(li(*r) for r in rows[:keep]) + '</ul>'
        if len(rows) > keep:
            out += (f'<details class="rx5-more"><summary>Show {len(rows) - keep} more</summary><ul class="rx5-bars">' + ''.join(li(*r) for r in rows[keep:]) + '</ul></details>')
        return out
    _rx_ph = lambda ms: next((aph(m['id']) for m in sorted(ms, key=lambda m: -(BYNAME.get(m['name'], {}).get('sold') or 0)) if m['kind'] == 'y' and aph(m['id'])), None)
    M, B = RCL['M'], RCL['B']

    # ---- per-model pages
    for m in sorted((m for m in M.values() if m['url']), key=lambda m: m['name']):
        rs = sorted(m['recs'].values(), key=_rcldk, reverse=True); n = len(rs); nm = E(m['name'])
        ys = sorted(y for y in m['yc']); y0, y1 = (min(ys), max(ys)) if ys else (None, None)
        tot = sum(m['yc'].values()); topy = max(m['yc'], key=lambda y: (m['yc'][y], y)) if m['yc'] else None
        parts = {}
        for r in rs: parts[RPART(r.get('part')).capitalize()] = parts.get(RPART(r.get('part')).capitalize(), 0) + 1
        parts = sorted(parts.items(), key=lambda kv: (-kv[1], kv[0]))
        big = sorted((r for r in rs if _rcl_u(r['id'])[0]), key=lambda r: -_rcl_u(r['id'])[0])[:3]
        park = [r for r in rs if _rcl_u(r['id'])[1] or _rcl_u(r['id'])[2]]
        newn = sum(1 for r in rs if _rcl_new(r))
        yrow = [(f'<a href="{m["car"]}{y}/">{y}</a>' if m['kind'] == 'y' and m['car'].startswith('/cars/') else str(y), m['yc'][y], '') for y in sorted(m['yc'], reverse=True)]
        ph = aph(m['id']) if m['kind'] == 'y' else None
        vis = (pimg(ph, m['name']) + pcredit(who(ph))) if ph else ''
        stats = (f'<div class="stats rcx-st"><div><b>{n}</b><span>recall campaigns, model years {y0}–{y1}</span></div>'
                 + (f'<div><b>{topy}</b><span>the most-recalled year ({m["yc"][topy]} campaigns)</span></div>' if topy else '')
                 + f'<div><b>{_rcldate(rs[0])}</b><span>newest recall ({E(RPART(rs[0].get("part")))})</span></div>'
                 + (f'<div><b>{len(park)}</b><span>with a park-it or park-outside warning</span></div>' if park else '') + '</div>')
        cards = ''.join(_rcl_card(r, years=m['ry'].get(r['id'])) for r in rs[:8])
        more = ''.join(_rcl_card(r, years=m['ry'].get(r['id'])) for r in rs[8:])
        qa = [(f'How many recalls does the {nm} have?', f'{n} recall campaigns across model years {y0}–{y1}, from NHTSA. Many campaigns cover several model years; '
               f'counted once for every model year they cover (the way each year&#39;s page counts them), that&#39;s {tot}.')]
        if topy: qa.append((f'Which {nm} year has the most recalls?', f'The {topy}, with {m["yc"][topy]} campaigns. ' + ', '.join(f'{y}: {k}' for y, k in sorted(m['yc'].items(), key=lambda kv: (-kv[1], -kv[0]))[1:4]) + '.'))
        if parts: qa.append((f'What are most {nm} recalls about?', f'{E(parts[0][0])}: {parts[0][1]} of the {n} campaigns.' + (f' Then {E(parts[1][0].lower())} ({parts[1][1]})' + (f' and {E(parts[2][0].lower())} ({parts[2][1]})' if len(parts) > 2 else '') + '.' if len(parts) > 1 else '')))
        qa.append((f'What is the newest {nm} recall?', f'{E(RPART(rs[0].get("part")).capitalize())}, filed {_rcldate(rs[0])} (NHTSA {E(rs[0]["id"])}): {E(rsum(rs[0]))}'))
        if big: qa.append((f'What is the biggest {nm} recall?', f'NHTSA {E(big[0]["id"])} ({E(RPART(big[0].get("part")))}, {_rcldate(big[0])}) covers {_rcl_u(big[0]["id"])[0]:,} vehicles in all, every model in that campaign. {E(rsum(big[0]))}'))
        qa.append((f'How do I check if my {nm} has an open recall?', f'Use its VIN: type it at nhtsa.gov/recalls or ask any {E(m["brand"])} dealer. Our <a href="/vin/">VIN check</a> decodes it and lists every recall for that model year. Recall repairs are free.'))
        _yr = [(lab, k) for lab, k, _ in yrow]
        _open = f'{_RCL_OPEN}{_rcl_vin()}{CA_RECALL}'
        body = (f'<div class="pg rcx rx5">{_RCLCSS}<section class="rx5-h"><p class="rx5-e"><a href="/recalls/">Recall check</a> › <a href="/recalls/{m["mk"]}/">{E(m["brand"])}</a></p>'
                f'<h1>{nm}</h1><p class="rx5-s">recalls.</p>' + (f'<div class="rx5-im">{pimg(ph, m["name"]).replace(" loading=" + chr(34) + "lazy" + chr(34), "")}</div>' if ph else '')
                + _rx_big(n, f'recall campaigns, {y0}–{y1}')
                + f'<p class="rx5-line">Newest: <b>{_rcldate(rs[0])}</b> ({E(RPART(rs[0].get("part")))})' + (f' · Most-recalled year: <b>{topy}</b>' if topy else '') + '</p>'
                + _rx_vin('Check a VIN to see that exact car&#39;s recalls. We don&#39;t store it.') + '</section>'
                + f'<section class="rx5-sec"><h2>Every year.</h2><p class="rx5-sub">Recall campaigns that cover each model year.' + (' Tap a year for its full report.' if m['kind'] == 'y' and m['car'].startswith('/cars/') else '') + f'</p>{_rx_bars(_yr)}</section>'
                + '<div class="cpl rx5-pl">'
                + (_rx_box('warning', 'Park-it warnings', f'{len(park)} where NHTSA says don&#39;t drive it or park outside', f'<ul class="rc rcx-warn">{"".join(_rcl_card(r, years=m["ry"].get(r["id"])) for r in park)}</ul>', 'park') if park else '')
                + _rx_box('bell', 'Every recall', f'All {n}, newest first' + (f' · {newn} in the last 12 months' if newn else ''),
                          (f'<p class="yc-cap">{newn} filed in the last 12 months. A new recall has had the least time to be fixed, so it&#39;s the one most likely still open on a used car.</p>' if newn else '')
                          + f'<ul class="rc">{cards}</ul>' + (f'<details class="rcx-more"><summary>Show all {n} recalls</summary><ul class="rc">{more}</ul></details>' if more else ''), 'every')
                + (_rx_box('wrench', 'What they fix', f'Most: {E(parts[0][0].lower())} ({parts[0][1]})', _rx_bars([(E(pp), k) for pp, k in parts[:10]], 10), 'fix') if parts else '')
                + _rx_box('question', f'Is one open on your {E(m["short"])}?', 'How to check one car, and what the fix costs', _open, 'open')
                + _rx_box('talk', 'Questions', f'{len(qa)} answers about {nm} recalls', qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in qa)))
                + (_rx_go('car', f'{nm} problems', 'Every year&#39;s complaints and the best years to buy', m['car']) if m['car'] else '')
                + _rx_go('warning', f'All {E(m["brand"])} recalls', 'Every model, the biggest and the newest', f'/recalls/{m["mk"]}/')
                + _rx_box('info', 'Where this data comes from', 'NHTSA recall campaigns', _RCL_SRC + (pcredit(who(ph)) if ph else ''))
                + '</div>'
                + share_line(f'Every {m["name"]} recall, {y0}–{y1}: {n} campaigns. Free:', f'Know someone with a {E(m["short"])}?') + '</div>')
        page(m['url'], f'{m["name"]} Recalls: All {n} Recalls by Year ({y0}–{y1}) | The Lemon Index',
             f'Every {m["name"]} recall from NHTSA: {n} campaigns for model years {y0}–{y1}, newest first, with the years each covers. Most-recalled year: {topy}. Check a VIN free.',
             body, ld=[_rcl_ld(qa)])
        RCL_URLS.append(m['url'])

    # ---- per-make pages
    for b in sorted(B.values(), key=lambda b: b['name']):
        bn = E(b['name']); path = f'/recalls/{b["mk"]}/'; rs = sorted(b['recs'].values(), key=_rcldk, reverse=True); n = b['n']
        ms = sorted(b['models'], key=lambda m: (-m['n'], m['name']))
        allys = [y for m in ms for y in m['yc']]; y0, y1 = min(allys), max(allys)
        who_ = lambda c: ', '.join(dict.fromkeys(x['short'] for x in b['cm'][c]))
        yrs_ = lambda c: sorted({y for x in b['cm'][c] for y in x['ry'].get(c, ())})
        big = sorted((r for r in rs if _rcl_u(r['id'])[0]), key=lambda r: -_rcl_u(r['id'])[0])[:6]
        park = [r for r in rs if _rcl_u(r['id'])[1] or _rcl_u(r['id'])[2]]
        mrow = [((f'<a href="{m["url"]}">{E(m["short"])}</a>' if m['url'] else f'<a href="{m["car"]}">{E(m["short"])}</a>' if m['car'] else E(m['short'])), m['n'],
                 f'{min(m["yc"])}–{max(m["yc"])}' + (f' · most: {max(m["yc"], key=lambda y: (m["yc"][y], y))}' if m['yc'] else '')) for m in ms]
        top = ms[0]; ph = next((aph(m['id']) for m in sorted(ms, key=lambda m: -(BYNAME.get(m['name'], {}).get('sold') or 0)) if m['kind'] == 'y' and aph(m['id'])), None)
        vis = (pimg(ph, b['name']) + pcredit(who(ph))) if ph else ''
        stats = (f'<div class="stats rcx-st"><div><b>{n:,}</b><span>recall campaigns, model years {y0}–{y1}</span></div><div><b>{len(ms)}</b><span>{bn} models we track</span></div>'
                 f'<div><b>{_rcldate(rs[0])}</b><span>newest recall</span></div>' + (f'<div><b>{_rcl_u(big[0]["id"])[0]:,}</b><span>vehicles in the biggest campaign</span></div>' if big else '') + '</div>')
        qa = [(f'How many recalls does {bn} have?', f'{n:,} NHTSA recall campaigns on the {len(ms)} {bn} model{"s" * (len(ms) != 1)} we track, model years {y0}–{y1}. A campaign that covers several models or years counts once.')]
        if len(ms) > 1: qa.append((f'Which {bn} has the most recalls?', f'The {E(top["name"])}, with {top["n"]} campaigns. Then ' + ', '.join(f'the {E(m["short"])} ({m["n"]})' for m in ms[1:4]) + '. Models with more model years on sale have had more time to collect recalls.'))
        if big: qa.append((f'What is the biggest {bn} recall?', f'NHTSA {E(big[0]["id"])} ({E(RPART(big[0].get("part")))}, {_rcldate(big[0])}): {_rcl_u(big[0]["id"])[0]:,} vehicles in the whole campaign, on the {E(who_(big[0]["id"]))} among the models we track. {E(rsum(big[0]))}'))
        qa.append((f'What is the newest {bn} recall?', f'Filed {_rcldate(rs[0])} for the {E(who_(rs[0]["id"]))} (NHTSA {E(rs[0]["id"])}): {E(rsum(rs[0]))}'))
        qa.append((f'How do I check a {bn} for recalls by VIN?', f'Type the VIN at nhtsa.gov/recalls or ask any {bn} dealer: that shows whether a recall is still open on that car. Our <a href="/vin/">VIN check</a> decodes it and lists every recall for that model year. Recall repairs are free.'))
        _mc, _mx, _phs = [], [], []
        for m in ms:
            _h = m['url'] or m['car'] or ''
            _p = aph(m['id']) if m['kind'] == 'y' else None
            if _p: _mc.append(_rx_card(_h, _p, m['short'], m['n'], f'{min(m["yc"])}–{max(m["yc"])}' if m['yc'] else '')); _phs.append(_p)
            else: _mx.append((f'<a class="chip" href="{_h}">' if _h else '<span class="chip">') + f'{E(m["short"])} <small>{m["n"]}</small>' + ('</a>' if _h else '</span>'))
        _open = f'{_RCL_OPEN}{_rcl_vin()}{CA_RECALL}'
        body = (f'<div class="pg rcx rx5">{_RCLCSS}<section class="rx5-h"><p class="rx5-e"><a href="/recalls/">Recall check</a> › <a href="/brands/{b["mk"]}/">{bn}</a></p>'
                f'<h1>{bn}</h1><p class="rx5-s">recalls.</p>' + (f'<div class="rx5-im">{pimg(ph, b["name"]).replace(" loading=" + chr(34) + "lazy" + chr(34), "")}</div>' if ph else '')
                + _rx_big(f'{n:,}', f'recall campaigns on {len(ms)} model{"s" * (len(ms) != 1)}, {y0}–{y1}')
                + f'<p class="rx5-line">Newest: <b>{_rcldate(rs[0])}</b>' + (f' · Biggest: <b>{_rcl_u(big[0]["id"])[0]:,}</b> vehicles' if big else '') + '</p>'
                + _rx_vin('We hand the VIN to our free VIN check: the car and every recall for it. We don&#39;t store it.') + '</section>'
                + (f'<section class="rx5-sec"><h2>Every {bn} model.</h2><p class="rx5-sub">Recall campaigns in the corner, all years. Tap one for its full list.</p><div class="rx5-g">{"".join(_mc)}</div>'
                   + (f'<p class="chips rcx-chips rx5-chips">{"".join(_mx)}</p>' if _mx else '') + '</section>' if _mc else
                   f'<section class="rx5-sec"><h2>Every {bn} model.</h2>{_rx_bars([(lab, k) for lab, k, _ in mrow], 20)}</section>')
                + '<div class="cpl rx5-pl">'
                + (_rx_box('warning', 'Park-it warnings', f'{len(park)} where NHTSA says don&#39;t drive it or park outside',
                           f'<ul class="rc rcx-warn">{"".join(_rcl_card(r, who_(r["id"]), yrs_(r["id"])) for r in park[:8])}</ul>'
                           + (f'<details class="rcx-more"><summary>Show all {len(park)}</summary><ul class="rc">{"".join(_rcl_card(r, who_(r["id"]), yrs_(r["id"])) for r in park[8:])}</ul></details>' if len(park) > 8 else ''), 'park') if park else '')
                + (_rx_box('chart', f'The biggest {bn} recalls', 'By vehicles in the campaign, since 2010', f'<ul class="rc">{"".join(_rcl_card(r, who_(r["id"]), yrs_(r["id"])) for r in big)}</ul>', 'biggest') if big else '')
                + _rx_box('bell', f'The newest {bn} recalls', f'Latest: {_rcldate(rs[0])}', f'<ul class="rc">{"".join(_rcl_card(r, who_(r["id"]), yrs_(r["id"])) for r in rs[:6])}</ul>', 'newest')
                + _rx_box('question', f'Is one open on your {bn}?', 'How to check one car, and what the fix costs', _open, 'open')
                + _rx_box('talk', 'Questions', f'{len(qa)} answers about {bn} recalls', qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in qa)))
                + _rx_go('scale', f'Is {bn} reliable?', 'Every model scored on owner complaints', f'/brands/{b["mk"]}/')
                + _rx_go('warning', 'Recall check for every make', 'By VIN, or pick the car', '/recalls/')
                + _rx_box('info', 'Where this data comes from', 'NHTSA recall campaigns', _RCL_SRC + pcredit(who(*_phs, ph)))
                + '</div>'
                + share_line(f'Every {b["name"]} recall by model and year: {n:,} campaigns. Check yours by VIN, free:', f'Know someone with a {bn}?') + '</div>')
        page(path, f'{b["name"]} Recalls: Check by VIN, Model and Year | The Lemon Index',
             f'{n:,} NHTSA recall campaigns on {len(ms)} {b["name"]} model{"s" * (len(ms) != 1)} ({y0}–{y1}): by model, the biggest, the newest. Check your {b["name"]} for recalls by VIN, free.',
             body, ld=[_rcl_ld(qa)])
        if b['thin']: _rcl_noindex(path)
        else: RCL_URLS.append(path)
    # /brands/<make>/ pages link here from under their hero (RCL_LINK, 11-15 growth 4c).

    # ---- hub
    AR = {}
    for b in B.values():
        for c, r in b['recs'].items(): AR.setdefault(c, (r, b))
    allr = sorted(AR.values(), key=lambda t: _rcldk(t[0]), reverse=True)
    bigall = sorted((t for t in allr if _rcl_u(t[0]['id'])[0]), key=lambda t: -_rcl_u(t[0]['id'])[0])[:8]
    def _who_all(c):
        out = []
        for b in B.values():
            if c in b['cm']: out += [x['name'] for x in b['cm'][c]]
        out = list(dict.fromkeys(out)); return ', '.join(out[:3]) + (f' + {len(out) - 3} more' if len(out) > 3 else '')
    def _yrs_all(c): return sorted({y for b in B.values() if c in b['cm'] for x in b['cm'][c] for y in x['ry'].get(c, ())})
    VN_ = {}
    for fid, yrs in XL.items():
        _cn = defaultdict(int)
        for e in yrs.values():
            for mk_, md_, k in e.get('names', []): _cn[(mk_, md_)] += k
        if _cn: VN_[fid] = list(max(_cn, key=_cn.get))
    PK = {}
    for m in sorted(M.values(), key=lambda m: m['short']):
        if m['kind'] == 'y' and m['id'] in VN_ and m['years'] and m['car'].startswith('/cars/'): PK.setdefault(m['brand'], []).append([m['short'], m['id'], m['years'], VN_[m['id']][0], VN_[m['id']][1], m['url']])
    mk_list = sorted(B.values(), key=lambda b: (b['thin'], -b['n'], b['name']))
    chips = ''.join(f'<a class="chip" href="/recalls/{b["mk"]}/">{E(b["name"])} <small>{b["n"]:,}</small></a>' for b in mk_list)
    ncamp = len(AR); nmod = sum(len(b['models']) for b in B.values()); ally = [y for b in B.values() for m in b['models'] for y in m['yc']]
    pop = [M[i] for i in ('ford-f-series', 'honda-civic', 'toyota-camry', 'honda-cr-v', 'toyota-rav4', 'chevrolet-silverado', 'jeep-grand-cherokee', 'nissan-altima') if i in M and M[i]['url']]
    qa = [('How do I check if my car has a recall?', 'Use its VIN, the 17-character number on the dashboard by the windshield, on the driver&#39;s door frame and on the registration. Type it at nhtsa.gov/recalls or ask any dealer of that brand: that shows whether a recall is still open on that car. Our <a href="/vin/">VIN check</a> decodes the VIN and lists every recall for that model year, free.'),
          ('Is my car recalled if its model is on a recall list?', 'Not always. A recall covers the cars the automaker names, which can be one engine, one plant or a range of build dates, and your car may already have been fixed. The lists here cover every car of a make, model and year. Only the VIN tells you if a recall is open on your car.'),
          ('Can I check car recalls by VIN for free?', 'Yes. NHTSA&#39;s lookup at nhtsa.gov/recalls is free and covers recalls from the last 15 years, and so is ours. We don&#39;t store the VIN. NHTSA&#39;s public data API works by make, model and year, not by VIN, which is why the final check of one car is at nhtsa.gov or a dealer.'),
          ('Do I pay for a recall repair?', 'No. The automaker pays: the dealer fixes it free, used car or not. U.S. law (49 U.S.C. 30120) requires a free fix on vehicles under 15 years old when the recall is filed.'),
          ('What does "park it" or "park outside" mean on a recall?', 'NHTSA flags the most urgent recalls: "park it" means don&#39;t drive the car until it&#39;s fixed, and "park outside" means it could catch fire while parked, so keep it away from buildings.'),
          ('Does this cover cars in Canada?', 'The recall lists here are U.S. (NHTSA) campaigns. Canadian cars can have different recalls: search Transport Canada&#39;s recall database or check the VIN on the maker&#39;s Canadian recall site.'),
          ('Where does this data come from?', f'NHTSA&#39;s recall campaigns (api.nhtsa.gov) for the {nmod} models we track, model years {min(ally)}–{max(ally)}, and NHTSA&#39;s recall file for vehicle counts and park-it warnings (2010 and later). The make, model and year lookup at the top asks NHTSA live, so it&#39;s always current.')]
    _top = [b for b in mk_list if not b['thin']][:12]
    _bp = {b['mk']: _rx_ph(b['models']) for b in _top}
    _mkc = ''.join(_rx_card(f'/recalls/{b["mk"]}/', _bp[b['mk']], b['name'], b['n']) for b in _top if _bp[b['mk']])
    _popc = ''.join(_rx_card(m['url'], aph(m['id']), m['name'], m['n']) for m in pop if aph(m['id']))
    _newn = sum(1 for t in allr if _rcl_new(t[0]))
    body = (f'<div class="pg rcx rx5">{_RCLCSS}<section class="rx5-h"><p class="rx5-e">Recall check</p><h1>Is your car recalled?</h1>'
            f'<p class="rx5-s2">Check by VIN, or pick the car. Every NHTSA recall, free.</p>{_rx_vin("We hand the VIN to our free VIN check, which lists its recalls. We don&#39;t store it.")}'
            f'<section class="vnv rx5-pick" id="no-vin"><h2>No VIN? Pick the car.</h2>'
            f'<form id="rcpf" class="vnv-f" autocomplete="off"><label><span>Make</span><select name="mk" aria-label="Make"></select></label><label><span>Model</span><select name="md" aria-label="Model"></select></label><label><span>Year</span><select name="y" aria-label="Year"></select></label><button class="btn" type="submit">Show recalls</button></form>'
            f'<div id="rcpout" class="vin-recalls" aria-live="polite"></div></section>'
            f'<p class="rx5-line"><b>{ncamp:,}</b> recall campaigns · <b>{nmod}</b> models, {min(ally)}–{max(ally)} · <b>{_newn}</b> in the last 12 months</p>'
            f'<script id="rcpick" type="application/json">{_rclj.dumps(PK, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}</script></section>'
            + (f'<section class="rx5-sec"><h2>Recalls by make.</h2><p class="rx5-sub">Recall campaigns in the corner, on the models we track.</p><div class="rx5-g">{_mkc}</div></section>' if _mkc else '')
            + (f'<section class="rx5-sec"><h2>Popular models.</h2><p class="rx5-sub">Every recall for each, in one list.</p><div class="rx5-g">{_popc}</div></section>' if _popc else '')
            + '<div class="cpl rx5-pl">'
            + _rx_box('car', f'All {len(mk_list)} makes', 'Recall campaigns per make', f'<p class="chips rcx-chips">{chips}</p>', 'makes')
            + _rx_box('question', 'Recalled, or still open?', 'Not the same thing: how to check one car', f'{_RCL_OPEN}{CA_RECALL}', 'open')
            + _rx_box('chart', 'The biggest recalls', 'By vehicles in the campaign, since 2010', f'<ul class="rc">{"".join(_rcl_card(r, _who_all(r["id"]), _yrs_all(r["id"])) for r, _ in bigall)}</ul>', 'biggest')
            + _rx_box('bell', 'The newest recalls', f'{_newn} filed in the last 12 months', f'<ul class="rc">{"".join(_rcl_card(r, _who_all(r["id"]), _yrs_all(r["id"])) for r, _ in allr[:8])}</ul>', 'newest')
            + _rx_box('talk', 'Questions', f'{len(qa)} answers about recalls', qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in qa)))
            + _rx_box('info', 'Where this data comes from', 'NHTSA recall campaigns', _RCL_SRC + pcredit(who(*[x for x in _bp.values() if x], *[aph(m['id']) for m in pop if aph(m['id'])])))
            + '</div>'
            + share_line('Free recall check: by VIN, or pick the make, model and year. Every NHTSA recall:', 'Know someone shopping for a used car?') + '</div>')
    page('/recalls/', 'Recall Check: Is My Car Recalled? Search by VIN or Model | The Lemon Index',
         f'Free car recall check: type a VIN, or pick the make, model and year to see every NHTSA recall. {ncamp:,} recall campaigns on {nmod} models, by make, with the newest and biggest.',
         body, ld=[_rcl_ld(qa), {"@context": "https://schema.org", "@type": "WebApplication", "name": "Free car recall check", "url": BASE + '/recalls/', "applicationCategory": "UtilitiesApplication",
                               "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                               "description": "Check car recalls by VIN or by make, model and year, from NHTSA recall data. Shows every recall for a model year; confirm an open recall on one car at nhtsa.gov/recalls or a dealer."}])
    RCL_URLS.insert(0, '/recalls/')
    print(f'recall pages: {len(RCL_URLS)} indexed (hub, {sum(1 for u in RCL_URLS if u.count("/") == 3)} makes, {sum(1 for u in RCL_URLS if u.count("/") == 4)} models); {len(_rcl_noix)} noindex (thin):', ' '.join(_rcl_noix))
