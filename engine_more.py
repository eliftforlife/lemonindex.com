# 11-12 round 2 (UX test, Devin: "the EA888 is Coming soon", "I want an engine head-to-head that ends with a safest-bet verdict").
# exec'd at the end of supercar_engine_pages.py (needs its ENG_POOL / eng_verdict / ENG_PERF_ONLY / ENG_H2H, the BMW hook-phase data BENG/BEY/BVER
# and perf_page.engine_ext). Builds:
#   1. engine pages that only the performance files know (ENG_PERF_ONLY, e.g. /engines/vw-ea888/ from data/perf/golf-r.json): the sourced
#      facts per generation, the known issues with their NHTSA mention counts, the cars' complaint and recall counts, and what's missing
#   2. engine head-to-heads (ENG_H2H): one table from the same numbers each engine page shows, and a verdict that says how it was picked
# Nothing is estimated: a missing number says it's missing.
ENG_MORE_URLS = []; ENG_EXTRA_CARDS = []

def _pe_files(url):
    """[(perf data, auto data, engine code, engine)] for every performance file engine whose page is `url`"""
    out = []
    for p in sorted(glob.glob('data/perf/*.json')):
        if p.endswith('.auto.json'): continue
        D = _load(p); A = _load(p[:-5] + '.auto.json') if os.path.exists(p[:-5] + '.auto.json') else {}
        for code, e in (D.get('engines') or {}).items():
            if e.get('page') == url: out.append((D, A, code, e))
    return out

def _perf_only_page(url, name, make):
    F = _pe_files(url)
    if not F: return None
    x = _PPX.engine_ext(url) or {}
    iss = list((x.get('issues') or {}).values())
    gens = [(D, A, code, e, g) for D, A, code, e in F for g in D['gens'] if g['engine'] == code]
    y0 = min(g['y0'] for *_, g in gens); y1 = max(g['y1'] for *_, g in gens)
    hp = sorted(x.get('hp') or [])
    cars = list(dict.fromkeys(f'{D["make"]} {D["short"]}' if not D['short'].startswith(D['make']) else D['short'] for D, *_ in F))
    srcs = {}
    def S(ids, D):
        for i in ids:
            if i in D['sources']: srcs.setdefault(D['sources'][i]['u'], D['sources'][i]['t'])
    # per generation: the sourced facts, the NHTSA complaints and recalls for those model years (filed under the car's own NHTSA name)
    rows, gsec = [], ''
    for D, A, code, e, g in gens:
        ga = ((A.get('nhtsa') or {}).get('gens') or {}).get(g['id']) or {}
        rec = len({r['id'] for y in range(g['y0'], g['y1'] + 1) for r in (A.get('recalls') or {}).get(str(y), [])})
        for _k, _v, _s in e.get('facts') or []: S(_s, D)
        facts = ''.join(f'<li><b>{E(k)}:</b> {E(v)}</li>' for k, v, _s in e.get('facts') or [])
        gsec += f'<h3>{E(e["name"].replace(" (" + D["short"] + ")", ""))}: {E(g["code"])} {E(D["short"])}, {E(g["years"])}</h3><ul>{facts}</ul>'
        filed = ' / '.join(m.title() for m in (D.get('nhtsa') or {}).get('models') or [])
        rows.append([f'<a href="{E(D["page"])}">{E(g["code"])} {E(D["short"])}</a>', E(g['years']), f'{ga.get("n", 0):,}', str(rec), E(filed)])
    for i in iss:
        for D, *_ in F: S(i.get('src') or [], D)
    _w, vline, vfaq = eng_verdict(url, name, None, sum(1 for i in iss if re.search('recall', i['kind'], re.I)), iss)
    rk = ENG_POOL_RANK.get(url)
    chips = (f'<div class="trc"><div><b>{y0}–{str(y1)[-2:]}</b><span>model years covered</span></div>'
             + (f'<div><b>{hp[0]}' + (f'–{hp[-1]}' if len(hp) > 1 else '') + '</b><span>hp (factory)</span></div>' if hp else '')
             + '<div><b>–</b><span>no YouTube study yet</span></div></div>')
    what = F[0][3].get('what') or ''
    ans1 = (f'{E(make)}&#39;s {E(what)}. This page covers the versions we have sourced so far: the {E(", ".join(cars))}, model years {y0}–{y1}. '
            + ('The engine is used in other cars too; those aren&#39;t covered here yet.' if ENG_PERF_ONLY[url][2] else ''))
    issl = ''.join(f'<li><b>{E(i["t"])}</b> <small>({E(i["kind"])})</small>. {E(i["x"])}' + (f' <b>Fix:</b> {E(i["fix"])}' if i.get('fix') else '')
                   + (f' <small>{i["n"]} owner complaint{"" if i["n"] == 1 else "s"} to NHTSA mention it ({E(", ".join(i["where"]))}).</small>' if i['n'] else '') + '</li>' for i in iss)
    tbl = ('<div class="tw"><table class="adv"><thead><tr><th>Car</th><th>Years</th><th>Owner complaints</th><th>Recall campaigns</th><th>NHTSA files it as</th></tr></thead><tbody>'
           + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table></div>')
    h2h = next(((u, lab) for u, us, lab in ENG_H2H if url in us), None)
    srcl = ' · '.join(f'<a href="{E(u)}" rel="noopener nofollow">{E(t)}</a>' for u, t in srcs.items())
    faq = [(f'What cars have the {name} engine?', f'On this site so far: the {", ".join(cars)}, model years {y0}–{y1}.' + (' It is used in other cars we haven&#39;t covered yet.' if ENG_PERF_ONLY[url][2] else '')),
           (f'Is the {name} reliable?', vfaq + ' Owner complaints are filed by car, not engine, and cover the whole car, so none of these numbers is an engine failure rate.')]
    if hp: faq.append((f'How much horsepower does the {name} make?', f'{hp[0]}' + (f' to {hp[-1]}' if len(hp) > 1 else '') + ' hp in the versions on this page (factory figures).'))
    faq = [(q, html.unescape(a)) for q, a in faq]
    body = (f'<article class="study tr2 eng2 sce"><p class="kicker"><a href="/engines/performance/">Performance engines</a> · <a href="/engines/">Every engine</a></p>'
            f'<h1>{E(name)} engine: known problems and recalls</h1><p class="tra">{ans1}</p>{chips}'
            f'<p class="note engvd"><b>{E(vline.split(":", 1)[0])}:</b>{E(html.unescape(vline.split(":", 1)[1]))}' + (f' <a href="{h2h[0]}">Compare it with the {E(h2h[1])} →</a>' if h2h else '') + '</p>'
            + (f'<section class="yc engk"><h2>Known issues on record</h2><ul>{issl}</ul></section>' if issl else '')
            + (globals().get('EU_CARS_HTML') or (lambda *a: ''))(url)   # 11-13 N3 (nav report 3): the regular models (Golf for the Golf R), each year linked
            + f'<section class="yc"><h2>Owner complaints and recalls</h2><p>Counts for the cars on this page, from NHTSA. They cover every part of the car, not only the engine.</p>{tbl}</section>'
            + f'<section class="yc"><h2>Specs by generation</h2>{gsec}</section>'
            + '<section class="yc"><h2>What we don&#39;t have yet</h2><ul><li>A YouTube owner study for this engine (and for the ' + E(', '.join(cars)) + '): not pulled yet, so there&#39;s no YouTube tone or rank.</li>'
              + ('<li>The engine&#39;s other cars: only the versions above are sourced so far.</li>' if ENG_PERF_ONLY[url][2] else '') + '</ul></section>'
            + '<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq)) + '</section>'
            + (f'<p class="yc-cap">Sources: {srcl}. Complaints and recalls: NHTSA (api.nhtsa.gov).</p>' if srcl else '') + '</article>')
    title = f'{name} Engine: Known Problems, Recalls & Specs'
    desc = html.unescape(f'The {name} in the {", ".join(cars)} ({y0}-{y1}): {len(iss)} known issues with sources, owner complaints and recalls by generation, and specs. Every number sourced.')
    page(url, title, desc, body, ld=[faq_ld([(q, '', a) for q, a in faq])])
    ENG_MORE_URLS.append(url)
    ENG_EXTRA_CARDS.append(dict(url=url, name=name, code=re.sub(r'^\w+ ', '', name).split(' ')[0], lay=what, yrs=f'{y0}–{str(y1)[-2:]}', mk=make, used=[c.replace(make + ' ', '').replace('Volkswagen ', '') for c in cars]))
    return url

for _u, (_n, _m, _o) in ENG_PERF_ONLY.items():
    try: _perf_only_page(_u, _n, _m)
    except Exception as _ex: print('perf engine page failed', _u, repr(_ex))

# ---- head-to-heads
def _eng_sum(url):
    """one engine's row, from the data its own page shows"""
    x = _PPX.engine_ext(url) or {}
    iss = [i for i in (x.get('issues') or {}).values()]
    s = dict(url=url, built=os.path.exists(os.path.join(OUT, url.strip('/'), 'index.html')) or url in ENG_MORE_URLS, tone=None, rank=ENG_POOL_RANK.get(url),
             iss=iss, recalls=sum(1 for i in iss if re.search('recall', i['kind'], re.I)), mentions=sum(i['n'] for i in iss), note='')
    if url in ENG_POOL: s['tone'] = int(ENG_POOL[url] + 0.5)
    sce = next((k for k in SCENG['engines'] if SCE_URL(k) == url), None)
    bmw = next((c for c in BENG if ENG_URL(c) == url and BEY.get(c)), None)
    if bmw:
        m = BENG[bmw]; ys = sorted(BEY[bmw], key=int)
        hp = sorted({v['hp'] for f in BVER for y in BVER[f] for v in BVER[f][y] if v.get('code') == bmw and v.get('hp')} | (x.get('hp') or set()))
        s.update(name=m['name'], lay=f'{m["size"]} {m["layout"]}, {m["asp"]}', years=f'{ys[0]}–{ys[-1]}', hp=hp,
                 cars=sorted({BFAM.get(f, f).replace('BMW ', '') for y in ys for f in BEY[bmw][y]['models']}))
    elif sce:
        d = SCENG['engines'][sce]
        s.update(name=d['name'], lay=f'{d["size"]} {d["layout"]}, {d["asp"]}', years=f'{d["y0"]}–{d["y1"]}', hp=list(d['hp']),
                 cars=[_sce_label(d, c['slug']).replace(d['make'] + ' ', '') for c in d['cars']])
        s['recalls'] = max(s['recalls'], sum(1 for r in d['recalls'] if r['eng']))
        s['iss'] = iss + [dict(t=n, kind='Wikipedia', n=0) for n, _u in d.get('notes') or []]
        if sce == 'subaru-fa': s['note'] = 'The non-turbo FA20/FA24 in the BRZ and GR86. The WRX&#39;s turbo FA24 has no engine page yet.'
    elif url in ENG_PERF_ONLY:
        F = _pe_files(url); gs = [g for D, A, c, e in F for g in D['gens'] if g['engine'] == c]
        s.update(name=ENG_PERF_ONLY[url][0], lay=(F[0][3].get('what') or '') if F else '', years=f'{min(g["y0"] for g in gs)}–{max(g["y1"] for g in gs)}' if gs else '', hp=sorted(x.get('hp') or []),
                 cars=list(dict.fromkeys(D['short'] for D, *_ in F)), note='Covers the Golf R versions only so far.' if 'ea888' in url else '')
    else:
        s.update(name=url.strip('/').split('/')[-1], lay='', years='', hp=[], cars=[], note='No engine page yet.')
    return s

def _h2h_page(url, urls, label):
    S = [_eng_sum(u) for u in urls]
    nm = lambda s: re.sub(r'^(Ford|BMW|VW|Subaru) ', '', s['name'])
    rated = [s for s in S if s['tone'] is not None]
    best = min(rated, key=lambda s: s['rank']) if rated else None
    most_rec = max(S, key=lambda s: s['recalls'])
    unrated = [s for s in S if s['tone'] is None]
    if best:
        vb = (f'Safest bet on our data: the <b>{E(best["name"])}</b>. Its YouTube owner tone is the best of the {len(rated)} rated here ({best["tone"]}/100, #{best["rank"]} of {ENG_POOL_N} {ENG_POOL_LBL})'
              + (f', and it has {best["recalls"]} engine recall{"" if best["recalls"] == 1 else "s"} on record.' if best is not most_rec or not best['recalls'] else f', but it also has the most engine recalls on record here ({best["recalls"]}): check they were done.')
              + (' ' + ' '.join(f'The {E(nm(s))} isn&#39;t rated: no YouTube study yet.' for s in unrated) if unrated else ''))
    else: vb = 'None of these engines has a YouTube study yet, so we can&#39;t pick one.'
    def cell_tone(s): return f'<b>{s["tone"]}</b><small> /100 · #{s["rank"]} of {ENG_POOL_N}</small>' if s['tone'] is not None else '<small>no YouTube study yet</small>'
    def cell_iss(s):
        t = [i['t'] for i in s['iss'] if not i['t'].lower().startswith('no ')]
        return (f'<b>{len(t)}</b><small> · {E("; ".join(t[:3]))}{" …" if len(t) > 3 else ""}</small>') if t else '<small>none listed</small>'
    rows = [('Type', lambda s: E(s['lay']) or '—'), ('Model years', lambda s: E(s['years']) or '—'),
            ('Horsepower', lambda s: (f'{min(s["hp"])}–{max(s["hp"])}' if len(set(s['hp'])) > 1 else str(s['hp'][0])) + ' hp' if s['hp'] else '—'),
            ('Used in', lambda s: E(', '.join(s['cars'][:6]) + (f' +{len(s["cars"]) - 6} more' if len(s['cars']) > 6 else '')) if s['cars'] else '—'),
            ('YouTube owner tone<br><small>0–100, higher = better</small>', cell_tone),
            ('Known issues on record<br><small>from our performance pages</small>', cell_iss),
            ('Engine recalls on record', lambda s: f'<b>{s["recalls"]}</b>'),
            ('Owner complaints naming those issues<br><small>raw count, follows sales</small>', lambda s: f'{s["mentions"]:,}' if s['iss'] else '—')]
    head = '<tr><th></th>' + ''.join(f'<th>' + (f'<a href="{E(s["url"])}">{E(nm(s))}</a>' if s['built'] else E(nm(s))) + '</th>' for s in S) + '</tr>'
    body_rows = ''.join(f'<tr><th scope="row">{lab}</th>' + ''.join(f'<td>{fn(s)}</td>' for s in S) + '</tr>' for lab, fn in rows)
    notes = ''.join(f'<li><b>{E(nm(s))}:</b> {s["note"]}</li>' for s in S if s['note'])
    title = f'{" vs ".join(nm(s) for s in S)}: Which Engine Is the Safest Bet?'
    faq = [(f'Which is more reliable: the {", ".join(nm(s) for s in S[:-1])} or the {nm(S[-1])}?', html.unescape(re.sub('<[^>]+>', '', vb))),
           ('How is the pick made?', 'By YouTube owner tone, the one number every engine page measures the same way (praise vs trouble words in the most-watched videos, 0-100). '
            'Owner complaints to NHTSA are filed by car, not engine, and follow how many were sold, so they are shown but not used to pick. Recalls and known issues come from our performance pages, each with its source.')]
    body = (f'<article class="study eng2 eh2h"><p class="kicker"><a href="/engines/">Every engine</a> · Engine head-to-head</p>'
            f'<h1>{E(" vs ".join(nm(s) for s in S))}: which engine is the safest bet?</h1>'
            f'<div class="verdict"><p class="vk">Verdict</p><p class="vs">{vb}</p></div>'
            f'<div class="tw"><table class="adv eh2h-t"><thead>{head}</thead><tbody>{body_rows}</tbody></table></div>'
            + (f'<ul class="note">{notes}</ul>' if notes else '')
            + '<p class="note">YouTube tone and rank: the same numbers each engine page shows, ranked among every engine on the site with a YouTube study. '
              'Known issues and recalls: the sourced lists on our performance pages (open an engine for the sources). None of these is an engine failure rate.</p>'
            + '<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq)) + '</section></article>')
    page(url, title, html.unescape(re.sub('<[^>]+>', '', vb))[:300], body, ld=[faq_ld([(q, '', a) for q, a in faq])], kind='article')
    ENG_MORE_URLS.append(url)

for _u, _us, _lab in ENG_H2H:
    try: _h2h_page(_u, _us, _lab)
    except Exception as _ex:
        import traceback; print('engine head-to-head failed', _u, repr(_ex)); traceback.print_exc()
SCE_URLS.extend(ENG_MORE_URLS)
print('engine pages (perf-only + head-to-heads):', ENG_MORE_URLS)
