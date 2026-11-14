# Pages for models with complaints but no sales data (11-06: VW Taos, Pontiac). Run by build.py with exec(). No Lemon Index here: it needs sales, so the page says so and shows the raw data.
EXTRA_URLS = []
# 11-13 (Elijah: "make every no-data model a real page now, from YouTube"): models with a YouTube study (data/yt_scores.json, data/yt_buyer.json)
# get the YouTube rank per model year next to their raw complaint counts, what owners praise and complain about, and the most-watched owner videos
# (titles + channels, no thumbnails). Counts are counts: no sales, so nothing here is per car sold.
def _ytx_rank(m, by):
    sc = YTS.get(m['id']) or {}
    ok = {int(y) for y, s in sc.items() if s.get('score') is not None and (s.get('videos') or 0) >= YT_MIN and (int(y) < 2010 or by.get(int(y), 0) > 0)}   # a new year with no owner reports can't win by default
    got = sorted(((sc[str(y)]['score'], sc[str(y)]['videos'], y) for y in ok), reverse=True)
    return sc, {y: i + 1 for i, (_, _, y) in enumerate(got)}
def _ytx_bars(m, by, rc):
    sc, RK = _ytx_rank(m, by)
    if not RK: return '', RK
    lo, hi = min(sc[str(y)]['score'] for y in RK), max(sc[str(y)]['score'] for y in RK); mx = max(by.values()) if by else 1; N = len(RK)
    def row(y):
        s = sc.get(str(y)) or {}; rk = RK.get(y); n = by.get(y)
        w = 8 + 92 * (s['score'] - lo) / max(1, hi - lo) if rk else 0; tier = '' if rk is None else (' up' if rk <= N / 3 else ' dn' if rk > N * 2 / 3 else '')
        yt = (f'<span class="bt ytb{tier}"><i style="width:{w:.0f}%"></i></span><b class="ytn" title="YouTube rank {rk} of {N} {E(m["name"])} years">#{rk}</b>' if rk else '<span class="bt ytb"></span><b class="ytn mute">·</b>')
        tip = (f'{E(m["name"])} {y}: ' + (f'{n:,} owner complaint{"s" if n != 1 else ""} (a count, not per car sold)' if n else 'no owner complaints on file') + (f', {rc[y]} recall{"s" if rc[y] != 1 else ""}' if rc.get(y) else '')
               + (f'. YouTube rank #{rk} of {N} (score {s["score"]}, {s["videos"]:g} videos)' if rk else '. Not enough YouTube videos to rank'))
        return (f'<div class="b xc-b" data-tip="{tip}."><span class="bn">{y}</span><span class="bt"><i style="width:{100 * (n or 0) / (mx or 1):.1f}%"></i></span><b>{f"{n:,}" if n else "·"}</b>{yt}</div>')
    ys = sorted(set(by) | set(RK), reverse=True); new = [y for y in ys if y >= min(by)] if by else ys; old = [y for y in ys if y not in new]
    return (f'<section class="yc" id="yt-years"><h2>YouTube rank and complaints, by model year</h2><div class="yyears noph"><div class="yy-ch"><div class="bars yb yt2"><div class="bl yth2" aria-hidden="true"><span></span><span>Complaints <em>a count, not per car</em></span><span></span><span>YouTube rank <em>#1 = favorite</em></span><span></span></div>'
            + ''.join(row(y) for y in new) + '</div></div></div>'
            + (f'<details class="yrs-more"><summary>Show {len(old)} older years ({old[-1]}–{old[0]}, YouTube videos only)</summary><div class="bars yb yt2">{"".join(row(y) for y in old)}</div></details>' if old else '')
            + f'<p class="yc-cap"><b>YouTube rank:</b> we read {round(sum(s.get("videos") or 0 for s in sc.values())):,} YouTube videos about the {E(m["name"])} and ranked each year with 10 or more videos by how much they praise it vs. how much they talk about problems. '
            'It measures tone, not failure rates. Complaints are the raw number owners filed with NHTSA: popular years draw more partly because more were sold, and without usable sales figures we can&#39;t turn them into a per-car score.</p></section>'), RK
def _ytx_block(m, by, RK):
    if not (YC.YB.get(m['id']) or RK): return ''
    c = dict(fid=m['id'], short=m['name'].split(' ', 1)[-1], name=m['name'], years=[{'y': y} for y in sorted(by)] or [{'y': m['a']}], yt_rank=RK, ytr=YTR.get(m['id']), ytv=[],
             start=max(by, key=by.get) if by else None, url=lambda y: '#yt-years')
    h = re.sub(r'<img src="https://i\.ytimg\.com[^>]*>', '', YC.yt_block(c))   # titles and channels only
    return YC.ASSET + h.replace('<section class="yot" id="youtube">', '<section class="yot" id="yt-owners">', 1)   # Overview tab, not Repairs
def _extra_pages():
    if not os.path.exists('data/extra_models.json'): return
    X = _load('data/extra_models.json'); X.update(_load('data/extra_models_new.json'));   # 11-11 + complaints-only new models
    rows = lambda head, R: '<div class="tw"><table class="adv"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in R) + '</tbody></table></div>'
    for m in X.values():
        nm = E(m['name']); path = f'/cars/{m["id"]}/'; top = m['parts'][0][0] if m['parts'] else ''; by = {int(k): v for k, v in m['by_year'].items()}; wy = max(by, key=by.get) if by and max(by.values()) else None
        ans = f'Owners filed <b>{m["n"]:,} complaints</b> about the {m["a"]} to {m["b"]} {nm} with the government' + (f', most about {E(top)}' if top else '') + (f'. The {wy} drew the most, with {by[wy]:,}' if wy else '') + f'. It has {len(m["recalls"])} recall{"s" if len(m["recalls"]) != 1 else ""} on record.'
        rc = {}
        for r in m.get('recalls') or []:
            for y in set(r.get('years') or []): rc[y] = rc.get(y, 0) + 1
        ytbars, RK = _ytx_bars(m, by, rc) if m.get('id') in YTS else ('', {})
        ytblock = _ytx_block(m, by, RK)
        nol = (f'<section class="yc xc-no"><p><b>No Lemon Index score yet:</b> {"too few were sold in the U.S. for a fair per-car score" if m.get("why") == "thin" else "too few model years have finished our complaint window" if m.get("why") == "young" else "we don&#39;t have reliable sales numbers for this car"}, '
               'so here&#39;s what YouTube owners say, next to the raw complaint counts.</p></section>') if (RK or ytblock) else ''
        sec = [x for x in (nol, ytbars, ytblock) if x]
        sec += [f'<section class="yc" id="years"><h2>Complaints {"and recalls " if rc else ""}by model year</h2>' + rows(['Model year', 'Complaints'] + (['Recalls'] if rc else []), [[y, f'{by[y]:,}'] + ([rc.get(y, 0)] if rc else []) for y in sorted(by)]) + '<p class="yc-cap">Popular years draw more complaints partly because more were sold. We don&#39;t have usable sales for this model, so these are counts, not a score.</p></section>']
        if m['parts']: sec.append('<section class="yc" id="problems"><h2>What owners complain about</h2>' + rows(['System', 'Share of complaints'], [[E(p).capitalize(), f'{k}%'] for p, k in m['parts']]) + '</section>')
        if m['miles']: g = m['miles']; sec.append(f'<section class="yc"><h2>When problems show up</h2><p>Half of the owners who gave a mileage reported the problem between <b>{g["p25"]:,}</b> and <b>{g["p75"]:,}</b> miles. The middle report was at <b>{g["median"]:,}</b> miles, from {g["n"]:,} complaints.</p></section>')
        sec.append('<section class="yc"><h2>How serious</h2>' + rows(['Crashes', 'Fires', 'Injury reports', 'Death reports'], [[f'{m["crash"]:,}', f'{m["fire"]:,}', f'{m["injured"]:,}', f'{m["deaths"]:,}']]) + '<p class="yc-cap">As reported by owners to NHTSA. Not verified.</p></section>')
        if m['recalls']:
            MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']; dt = lambda d: (lambda a: f'{MN[int(a[1]) - 1]} {a[2]}' if len(a) == 3 and a[1].isdigit() and 1 <= int(a[1]) <= 12 else E(d))(d.split('/'))
            sec.append(f'<section class="yc" id="recalls"><h2>Recalls <span class="yc-n">{len(m["recalls"])}</span></h2><ul class="advr">' + ''.join(f'<li><p class="advh"><a href="https://www.nhtsa.gov/recalls?nhtsaId={E(r["id"])}" target="_blank" rel="noopener nofollow">{E(r["id"])}</a> <small>{dt(r["date"])}</small> <b>{E((r["part"] or "Other").replace(":", " / ").title())}</b></p><p>{E(r["summary"])}</p>' + (f'<p><b>Fix.</b> {E(r["fix"])}</p>' if r.get('fix') else '') + '</li>' for r in m['recalls']) + '</ul><p class="yc-cap">Recall repairs are free at any dealer. Check the exact car&#39;s VIN for open recalls.</p></section>')
        if m['quotes']: sec.append('<section class="yc"><h2>In owners&#39; words</h2>' + ''.join(f'<blockquote><p>{E(q["text"])}</p><cite>{q["y"]} {nm} owner · NHTSA complaint {q["odi"]}</cite></blockquote>' for q in m['quotes']) + '</section>')
        faq = [(f'What are the most common {m["name"]} problems?', f'In owner complaints to the government, the top areas are {", ".join(p for p, _ in m["parts"][:3])}.' if m['parts'] else 'There are too few complaints to say.'), (f'How many recalls does the {m["name"]} have?', f'{len(m["recalls"])} safety recall{"s" if len(m["recalls"]) != 1 else ""} on record for the {m["a"]} to {m["b"]} models.')]
        sec.append('<section class="yc yqa"><h2>Quick answers</h2>' + ''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq) + '</section>')
        def _why(m):   # 11-11: thin-sales models say so, with the sales source
            if m.get('why') == 'thin':
                return (f'We don&#39;t give this model a Lemon Index: too few were sold in the U.S. for a fair per-car score '
                        f'({m["sales_under"]} of the {m["sales_years"]} years we have sales for were under 20,000, <a href="{E(m["sales_url"])}" rel="nofollow">sales source</a>).')
            if m.get('why') == 'young':   # 11-11: it sells plenty, but too few model years have finished their 3-year complaint window
                fy = m.get('full') or []
                return (f'We don&#39;t give this model a Lemon Index yet: {"only the " + str(fy[0]) + " model year has" if len(fy) == 1 else "too few model years have"} finished the 3-year '
                        f'window we count complaints in. Newer years are still being counted (<a href="{E(m["sales_url"])}" rel="nofollow">sales source</a>).')
            return 'We don&#39;t give this model a Lemon Index because we don&#39;t have its sales by year yet.'
        body = f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/cars/">All cars</a> · {f'<a href="/brands/{m["brand"].lower()}/">{E(m["brand"])}</a>' if f'/brands/{m["brand"].lower()}/' in globals().get('burls', []) or m['brand'] == 'Pontiac' else E(m['brand'])}</p><h1>{E(QN(m))} reliability: problems and recalls.</h1><p class="ans">{ans}</p></header>{(lambda h: f'<div class="advimg">{h}</div>' if h else "")(YSL.model_hero_html(m["id"], m["name"]))}{ytfix("model:" + m["id"])}<div class="ygrid">{"".join(sec)}</div><p class="yc-cap">Source: NHTSA owner complaints and recalls{', YouTube videos (titles and channels link to them)' if nol else ''}. {_why(m)} Complaints are owner reports, not proof of a defect.</p></div>'
        page(path, seo_title([f'{QN(m)} Reliability: Problems & Recalls by Year', f'{QN(m)} Reliability: Problems & Recalls', f'{QN(m)} Reliability']), re.sub('<[^>]+>', '', ans), body, ld=[faq_ld([(q, '', a) for q, a in faq])]); EXTRA_URLS.append(path)
    P = sorted([m for m in X.values() if m['brand'] == 'Pontiac'], key=lambda m: -m['n'])
    if P:
        lede = f'Pontiac ended in 2010, but owners still look these cars up. Here are {len(P)} models and {sum(m["n"] for m in P):,} owner complaints to the government.'
        body = '<div class="advp"><header class="advh1"><p class="ph-e"><a href="/brands/">Brands</a></p><h1>Pontiac problems and recalls, by model.</h1><p class="ans">' + E(lede) + '</p></header><div class="ygrid"><section class="yc">' + rows(['Model', 'Years', 'Complaints', 'Recalls', 'Top complaint'], [[f'<a href="/cars/{m["id"]}/">{E(m["name"])}</a>', f'{m["a"]}–{m["b"]}', f'{m["n"]:,}', len(m['recalls']), E(m['parts'][0][0]).capitalize() if m['parts'] else '–'] for m in P]) + '</section></div><p class="yc-cap">Source: NHTSA. No Lemon Index for Pontiac yet, because we don&#39;t have sales by year.</p></div>'
        page('/brands/pontiac/', 'Pontiac Problems and Recalls by Model', lede, body); EXTRA_URLS.insert(0, '/brands/pontiac/')
    # links in from existing pages, so these aren't orphans
    for f, html_ in (('docs/brands/index.html', '<p class="yc-cap" style="text-align:center"><a href="/brands/pontiac/">Pontiac (discontinued): problems and recalls by model</a></p>'), ('docs/cars/index.html', '<p class="ctn mb-more" data-hide="p s e"><b>More:</b> <a href="/brands/pontiac/">Pontiac models (discontinued)</a> · <a href="/cars/volkswagen-taos/">Volkswagen Taos</a></p>'), ('docs/brands/volkswagen/index.html', '<p class="yc-cap" style="text-align:center"><a href="/cars/volkswagen-taos/">Volkswagen Taos problems and recalls</a></p>')):
        if os.path.exists(f):
            s = open(f, encoding='utf-8').read()
            _at = '<p class="ph-cr" data-hide="p">' if f == 'docs/cars/index.html' and '<p class="ph-cr" data-hide="p">' in s else '</main>'   # 11-11: inside the /cars/ grid, so the tabs can hide it
            if html_ not in s: open(f, 'w', encoding='utf-8').write(s.replace(_at, html_ + _at, 1))
    print('extra pages', len(EXTRA_URLS))
_extra_pages()
