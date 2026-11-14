# 11-13 JDM section: the /jdm/ hub (Elijah: "add jdm section to site asap and first cars are the fast and furious main cars from 1 and 2 ...
# kinda like supercar or performance cars are set up"). exec'd by build.py right after perf_page.build_all (the car pages and the engine
# pages exist by then), before all_engines.py and find_index.py. Lists (jdm.py): the film cars by film, then their engines, then where each
# was sold. Every number on this page is read from the car files (data/perf/<slug>.json, sourced there) or NHTSA (data/perf/<slug>.auto.json);
# none is typed here.
import jdm as _JDM
JDM_URLS = []
def _jdm_hub():
    import perf_page as _JP
    C = {}
    for s in _JDM.CARS:
        D = _JP._load(f'data/perf/{s}.json'); A = _JP._load(f'data/perf/{s}.auto.json', {}) or {}
        if not D or not _JP.real_page(D['page'], OUT): continue
        C[s] = (D, A)
    if not C: return
    PL = _JP.perf_list()
    def card(s, film):
        D, A = C[s]; g, v = _JP._star(D); hp = _JP._hp(v); zv = _JP._z(v.get('z60'))[0]
        who = [f['who'] for f in D.get('films') or [] if f['film'] == film]
        img = (PL.get(s) or {}).get('img') or D.get('img') or ''
        eng = D['engines'][g['engine']]
        nums = ' · '.join(x for x in (f'{hp} hp' if hp else '', f'0–60 {zv}' if zv else '') if x)
        return (f'<a class="jdm-c" href="{E(D["page"])}"><span class="jdm-p">' + (f'<img src="{E(img)}"{rset(img.split("?")[0], "(max-width: 600px) 92vw, 300px")} alt="{E(D["name"])}, AI illustration" width="1000" height="600" loading="lazy" decoding="async">' if img else '')
                + f'</span><b>{E(D["name"])}</b><small class="jdm-w">{E(", ".join(who))}</small><small>{E(eng["name"])}' + (f' · {E(nums)}' if nums else '') + '</small>'
                + ('' if (D.get('us') or {}).get('sold', True) else '<span class="jdm-t">Never sold new in the US</span>') + '</a>')
    films = ''.join(f'<section class="jdm-f"><h2>{E(film)}</h2><div class="jdm-g">{"".join(card(s, film) for s in ss if s in C)}</div></section>' for film, ss in _JDM.FILMS)
    # engines: one row per engine page, the cars that use it here, the factory output range from the car files
    rows = {}
    for s, (D, A) in C.items():
        for gg in D['gens']:
            e = D['engines'][gg['engine']]; u = e.get('page') or ''
            r = rows.setdefault(u or e['name'], dict(u=u, name=_JDM.ENGINES.get(u, (None,))[0] or _JDM.SHARED.get(u) or e['name'], what=e.get('what', ''), cars=[], hp=set()))
            r['cars'].append((D['page'], f'{gg["code"]} {D["short"]}' if len(D['gens']) > 1 or D['short'] in ('Skyline GT-R',) else D['short']))
            for vv in gg['variants']:
                if isinstance(_JP._hp(vv), (int, float)) and vv.get('engine', gg['engine']) == gg['engine']: r['hp'].add(int(_JP._hp(vv)))   # a trim with another engine (variant `engine`) stays out
    def erow(r):
        live = r['u'] and os.path.exists(os.path.join(OUT, r['u'].strip('/'), 'index.html'))
        hp = sorted(r['hp']); hpt = (f'{hp[0]}' + (f'–{hp[-1]}' if len(hp) > 1 else '') + ' hp') if hp else '–'
        cars = ', '.join(f'<a href="{E(u)}">{E(t)}</a>' for u, t in dict.fromkeys(r['cars']))
        return (f'<tr><td>' + (f'<a href="{E(r["u"])}"><b>{E(r["name"])}</b></a>' if live else f'<b>{E(r["name"])}</b>') + f'<small>{E(r["what"])}</small></td><td>{hpt}</td><td>{cars}</td></tr>')
    etab = ('<div class="tw"><table class="adv jdm-e"><thead><tr><th>Engine</th><th>Factory output</th><th>JDM film cars with it</th></tr></thead><tbody>'
            + ''.join(erow(r) for r in sorted(rows.values(), key=lambda r: -max(r['hp'] or {0}))) + '</tbody></table></div>')
    # sold in the US? complaints and recalls for the film generation's model years (every version NHTSA files under that name)
    def urow(s):
        D, A = C[s]; us = D.get('us') or {}; y0 = min(g['y0'] for g in D['gens']); y1 = max(g['y1'] for g in D['gens'])
        if not D.get('nhtsa'): return f'<tr><td><a href="{E(D["page"])}">{E(D["name"])}</a></td><td>No</td><td>–</td><td>–</td></tr>'
        n = sum((((A.get('nhtsa') or {}).get('gens') or {}).get(g['id']) or {}).get('n') or 0 for g in D['gens'])
        rc = len({r['id'] for y in range(y0, y1 + 1) for r in (A.get('recalls') or {}).get(str(y), [])})
        return f'<tr><td><a href="{E(D["page"])}">{E(D["name"])}</a></td><td>{y0}–{y1}</td><td>{n:,}</td><td>{rc}</td></tr>'
    utab = ('<div class="tw"><table class="adv"><thead><tr><th>Car</th><th>Sold new in the US</th><th>Owner complaints</th><th>Recall campaigns</th></tr></thead><tbody>'
            + ''.join(urow(s) for s in C) + '</tbody></table></div>'
            '<p class="note">Owner complaints and recalls: NHTSA (api.nhtsa.gov), for those model years and every version NHTSA files under the model name (all Civics of 1993–1995, not only coupes). '
            'They are raw counts, not a Lemon Index: we don&#39;t have sales by year for these cars. Each car page shows what the complaints are about.</p>')
    never = [C[s][0] for s in C if not (C[s][0].get('us') or {}).get('sold', True)]
    faq = [('Which Japanese cars are in The Fast and the Furious?', 'In the 2001 film: ' + ', '.join(f'{f["who"]}: {C[s][0]["name"]}' for s in _JDM.FILMS[0][1] if s in C for f in C[s][0].get('films') or [] if f['film'] == _JDM.FILMS[0][0]) + '.'),
           ('Which Japanese cars are in 2 Fast 2 Furious?', 'In the 2003 film: ' + ', '.join(f'{f["who"]}: {C[s][0]["name"]}' for s in _JDM.FILMS[1][1] if s in C for f in C[s][0].get('films') or [] if f['film'] == _JDM.FILMS[1][0]) + '.')]
    if never: faq.append(('Which of these cars were never sold in the US?', ' '.join(f'{D["name"]}: {D["us"]["x"]}' for D in never)))
    sup = C.get('toyota-supra-mk4')
    if sup:
        g, v = _JP._star(sup[0]); e = sup[0]['engines'][g['engine']]
        faq.append(('What engine does the Fast and Furious Supra have?', f'The Mk IV Supra Turbo was built with the {e["name"]}, a {e["what"]}, rated {_JP._hp(v)} hp in the US. The film cars were modified; our numbers are for the stock car.'))
    body = (f'<div class="pg jdm"><section class="ph"><p class="ph-e"><a href="/?type=jdm">Cars · JDM</a></p><h1>JDM cars of The Fast and the Furious</h1>'
            f'<p class="ph-s">The Japanese hero cars of the first two films, as they left the factory: specs, the engine, and, where they were sold new in the US, owner complaints and recalls. '
            f'Every number is sourced on the car&#39;s page.{ai_note("JDM cars on this page")}</p></section>'
            f'{films}<section class="jdm-f"><h2>The engines</h2>{etab}</section>'
            f'<section class="jdm-f"><h2>Were they sold in the US?</h2>{utab}</section>'
            f'<section class="faq"><h2>Questions</h2>' + ''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq) + '</section>'
            '<p class="note">Film facts are plain text from the sources on each car page: no film stills, logos or likenesses. The pictures are AI illustrations of stock cars, not the film cars.</p></div>'
            '<style>.jdm .jdm-f{margin:34px 0}.jdm .jdm-f h2{font-size:clamp(22px,4.6vw,28px);letter-spacing:-.02em;margin:0 0 14px}'
            '.jdm-g{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,260px));justify-content:center;gap:12px}.jdm .jdm-f>h2{text-align:center}.jdm .faq h3{margin-top:24px}'
            '.jdm-c{display:flex;flex-direction:column;gap:4px;padding:14px 14px 16px;border-radius:20px;background:#f5f5f7;color:var(--ink);text-decoration:none;transition:transform .25s cubic-bezier(.2,.9,.25,1)}'
            '.jdm-c:hover{transform:translateY(-2px)}.jdm-p{display:flex;align-items:flex-end;justify-content:center;height:128px;margin-bottom:6px}'
            '.jdm-p img{max-width:100%;max-height:128px;width:auto;height:auto;filter:drop-shadow(0 8px 8px rgba(0,0,0,.12))}'
            '.jdm-c b{font-size:16px;line-height:1.25}.jdm-c small{font-size:13.5px;color:#6e6e73;line-height:1.35}.jdm-c .jdm-w{color:var(--ink);font-weight:500}'
            '.jdm-t{align-self:flex-start;margin-top:6px;padding:2px 9px;border-radius:999px;background:#ffd400;color:#17161a;font-size:12px;font-weight:600}'
            '.jdm-e td small{display:block;color:#6e6e73;font-size:13px}'
            '@media (max-width:600px){.jdm-g{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.jdm-c{padding:10px 10px 12px}.jdm-p{height:78px}.jdm-p img{max-height:78px}.jdm-c b{font-size:14.5px}.jdm-c small{font-size:12.5px}}</style>')
    title = 'JDM Cars of The Fast and the Furious: Specs, Engines, Problems'
    desc = f'The Japanese cars of The Fast and the Furious (2001) and 2 Fast 2 Furious (2003): {len(C)} cars from the Supra and RX-7 to the R34 GT-R, their engines, US sales and owner complaints. Every number sourced.'
    ld = [faq_ld([(q, '', a) for q, a in faq]), {"@context": "https://schema.org", "@type": "CollectionPage", "name": "JDM cars of The Fast and the Furious", "url": BASE + '/jdm/',
          "hasPart": [{"@type": "WebPage", "name": C[s][0]['name'], "url": BASE + C[s][0]['page']} for s in C]}]
    page('/jdm/', title, desc, body, ld=ld, img=((PL.get('toyota-supra-mk4') or {}).get('img') or '').split('?')[0] or None)
    JDM_URLS.append('/jdm/')
try: _jdm_hub()
except Exception as _ex:
    import traceback; print('JDM hub failed', repr(_ex)); traceback.print_exc()
print('jdm pages', JDM_URLS)
