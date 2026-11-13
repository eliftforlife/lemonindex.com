# 11-12 round-2 UX test, fix C (Mitch, 3/10: "it'd tell me a 6.0 Power Stroke is a good buy"; Ryan: "which F-150 engine?"): heavy-duty pickups,
# HD diesel engines and the F-150's engines. Data: data/hd.json (data_hd.py: NHTSA complaints with the engine decoded from each complaint's VIN
# by NHTSA vPIC, NHTSA recalls). Run by build.py with exec() in phases, so everything build.py defines is in scope:
#   HDX = 'hooks'  (before the model/year pages): the half-ton banner on the F-Series / Ram / Silverado / Sierra pages (wraps PIN_HTML), the
#                  honest Q&A lines (wraps rel_top / year_faq), and HD_EXN (the HD "No data yet" cards on /cars/ become links)
#   HDX = 'pages'  (before supercar_engine_pages.py): the HD truck model + year pages, the HD diesel engine pages, the 2.7 EcoBoost page, the
#                  F-150 engine comparison, the diesel truck engine table; HD_SCE (F-150 sections for the 3.5 EcoBoost and Coyote pages),
#                  HD_AE (cards for /engines/), HD_FIND (search rows)
# No per-car-sold score here: automakers report HD sales together with the half-tons, and engine sales aren't reported at all. Every page says so
# and shows counts and shares of complaints, never a rate.
import json as _hj, os as _hos, re as _hre, html as _hh
if HDX == 'hooks':
    HDJ = _load('data/hd.json') if _hos.path.exists('data/hd.json') else {}
    HDT, HDE, HDR = HDJ.get('trucks') or {}, HDJ.get('engines') or {}, HDJ.get('recalls') or {}
    HDB = HDJ.get('blend') or {}
    # engine slug -> page url (F-150 3.5 / 5.0 data goes on the existing 3.5 EcoBoost and Coyote pages)
    HE_URLS = {'powerstroke-73': '/engines/ford-powerstroke-73/', 'powerstroke-60': '/engines/ford-powerstroke-60/', 'powerstroke-64': '/engines/ford-powerstroke-64/',
               'powerstroke-67': '/engines/ford-powerstroke-67/', 'cummins-59': '/engines/cummins-59/', 'cummins-67': '/engines/cummins-67/',
               'duramax-lb7': '/engines/duramax-lb7/', 'duramax-lly': '/engines/duramax-lly/', 'duramax-lbz': '/engines/duramax-lbz/', 'duramax-lmm': '/engines/duramax-lmm/',
               'duramax-lml': '/engines/duramax-lml/', 'duramax-l5p': '/engines/duramax-l5p/', 'ford-ecoboost-27': '/engines/ford-ecoboost-27/',
               'f150-ecoboost-35-g1': '/engines/ford-ecoboost-35/', 'f150-ecoboost-35-g2': '/engines/ford-ecoboost-35/', 'f150-coyote': '/engines/ford-coyote/'}
    HD_DIESEL = [e for e in HE_URLS if not e.startswith(('f150-', 'ford-ecoboost'))]
    HD_F150 = ['ford-ecoboost-27', 'f150-ecoboost-35-g1', 'f150-ecoboost-35-g2', 'f150-coyote']
    HD_F150_CMP = '/engines/ford-f150-engines/'
    HD_DIESEL_HUB = '/engines/diesel-trucks/'
    HDU = lambda t, y=None: f'/cars/{t}/' + (f'{y}/' if y else '')
    # the four whole-line pickup pages and their heavy-duty half
    HD_FAM = {'ford-f-series': dict(hd='ford-super-duty', ht='F-150s', hdn='F-250/F-350 Super Duty trucks', who='Ford reports F-Series sales as one line', eng=HD_DIESEL[:4], hdshort='Super Duty'),
              'ram-pickup': dict(hd='ram-heavy-duty', ht='1500s', hdn='2500/3500 trucks', who='Ram reports 1500, 2500 and 3500 sales together', eng=HD_DIESEL[4:6], hdshort='Ram 2500/3500'),
              'chevrolet-silverado': dict(hd='chevrolet-silverado-hd', ht='1500s', hdn='2500HD/3500HD trucks', who='GM reports Silverado sales as one line', eng=HD_DIESEL[6:], hdshort='Silverado HD'),
              'gmc-sierra': dict(hd='gmc-sierra-hd', ht='1500s', hdn='2500HD/3500HD trucks', who='GM reports Sierra sales as one line', eng=HD_DIESEL[6:], hdshort='Sierra HD')}
    def _hd_share(fid, y=None):
        b = HDB.get(fid) or {}
        v = b.get('score') if y is None else (b.get('years') or {}).get(str(y))
        return (round(v[1] / (v[0] + v[1]) * 100), v[0] + v[1]) if v and v[0] + v[1] else (None, 0)
    HD_PY = {t: {int(y) for y, v in T['years'].items() if v['n'] >= 10 and 1999 <= int(y) <= 2025} for t, T in HDT.items() if t != 'ford-f-150'}   # model years with a page
    def _hd_has(t, y=None): return t in HD_PY and (y is None or int(y) in HD_PY[t])
    def _hd_eng_links(m):
        return ' · '.join(f'<a href="{HE_URLS[e]}">{E(HDE[e]["short"])}</a>' for e in m['eng'] if e in HDE)
    def HD_PIN(fid, y=None):
        m = HD_FAM.get(fid)
        if not m or not HDT: return ''
        sh, n = _hd_share(fid, y)
        if sh is None: return ''
        gm = fid in ('chevrolet-silverado', 'gmc-sierra')
        nm = 'Silverado' if fid == 'chevrolet-silverado' else 'Sierra' if fid == 'gmc-sierra' else ''
        who = (f'{100 - sh}% are F-150s (incl. Raptor, Hybrid, Lightning) and {sh}% are {m["hdn"]}, gas and diesel mixed' if fid == 'ford-f-series' else
               f'{100 - sh}% are 1500s and {sh}% are {m["hdn"]}, gas and diesel mixed' if fid == 'ram-pickup' else
               f'only {sh}% are filed as {m["hdn"]}; the rest are filed as 1500s or just &ldquo;{nm}&rdquo;')
        if y is None:
            head = 'Mostly half-ton trucks: not valid for 2500/3500 diesels'
            txt = (f'Of the {n:,} owner complaints behind this score (model years 2010–2022, first 3 years), {who}, because {m["who"]}. '
                   'So the score and the best and worst years mostly reflect the half-ton and can&#39;t tell one diesel from another.')
        else:
            head = (f'Mostly {m["hdshort"]} this year: this score mixes it with the half-ton' if sh >= 50 else 'Mostly half-ton trucks: not valid for 2500/3500 diesels')
            txt = (f'Of the {n:,} owner complaints behind the {y} numbers (first 3 years), {who}, because {m["who"]}. '
                   + ('This score is not a rating of any one engine.' if sh >= 50 else 'So this score mostly reflects the half-ton.'))
        hu = HDU(m['hd'], y) if _hd_has(m['hd'], y) else HDU(m['hd']) if _hd_has(m['hd']) else ''
        hl = (f'<a class="btn" href="{hu}">{y} {E(m["hdshort"])} by engine</a>' if hu and y and _hd_has(m['hd'], y) else f'<a class="btn" href="{hu}">{E(m["hdshort"])} by year and engine</a>' if hu else '')
        el = _hd_eng_links(m)
        f150 = (f'<p class="pinb-l">Buying an F-150? <a href="{HD_F150_CMP}">2.7 vs 3.5 EcoBoost vs 5.0, by owner complaints</a></p>' if fid == 'ford-f-series' and (y is None or y >= 2011) else '')
        return (f'<div class="pinb hdb" role="note"><p class="pinb-h"><b>{head}</b></p><p class="pinb-t">{txt}</p>'
                + (f'<p class="pinb-l">Diesel engines: {el}</p>' if el else '') + f150 + (f'<p class="pinb-a">{hl}</p>' if hl else '') + '</div>')
    _HD_PIN0 = PIN_HTML
    def PIN_HTML(fid, y=None): return HD_PIN(fid, y) + _HD_PIN0(fid, y)
    # the notes under the hero said "Covers the whole ... line (1500, 2500 and 3500)" next to "Is the Ram 1500 reliable?" (Mitch): say what it is
    for _fid, _m in HD_FAM.items():
        _sh, _ = _hd_share(_fid)
        if _sh is None: continue
        _nt = (f'The score covers the whole {"F-Series" if _fid == "ford-f-series" else "Ram pickup" if _fid == "ram-pickup" else BYNAME.get(next((f["name"] for f in YEARS if f["id"] == _fid), ""), {}).get("name", "line")} line '
               f'because {_m["who"]}; {100 - _sh}% of its complaints are half-tons. 2500/3500 trucks have their own page: <a href="{HDU(_m["hd"])}">{E(HDT.get(_m["hd"], {}).get("name", _m["hdshort"]))}</a>.')
        SN[_fid] = (SN[_fid][0] if _fid in SN else next((f['name'] for f in YEARS if f['id'] == _fid), _fid), _nt)
    def _hd_caveat(fid, y=None):
        m = HD_FAM.get(fid); sh, _ = _hd_share(fid, y)
        if not m or sh is None: return ''
        return (f' This score is the whole line: {sh}% of its complaints{" that year" if y else ""} are {m["hdn"].replace(" trucks", "")}, gas and diesel mixed in. '
                f'For a 2500/3500 or a diesel, see the {m["hdshort"]} page, by engine.')
    _HD_RT0 = rel_top
    def rel_top(f, *a, **k):
        h, t, p = _HD_RT0(f, *a, **k)
        cv = _hd_caveat(f['id'])
        if cv: p = p.rstrip() + cv
        return h, t, p
    _HD_YF0 = year_faq
    def year_faq(f, v, y, x, best):
        out = _HD_YF0(f, v, y, x, best); m = HD_FAM.get(f['id'])
        if not m or not out: return out
        cv = _hd_caveat(f['id'], y)
        if cv: q, a, t = out[0]; out[0] = (q, a + E(cv), t + cv)
        hu = HDU(m['hd'], y) if _hd_has(m['hd'], y) else HDU(m['hd'])
        a = (f'No. Automakers report 2500/3500 sales together with the half-ton, so we can&#39;t give heavy-duty trucks their own per-truck score. '
             f'The <a href="{hu}">{y} {E(m["hdshort"])} page</a> shows their owner complaints split by engine (from each complaint&#39;s VIN), and each diesel has its own page.')
        out.insert(1, (f'Is this score valid for a {y} {m["hdshort"]} or a diesel?', a, _hre.sub('<[^>]+>', '', _hh.unescape(a))))
        return out
    # /cars/ grid: the "No data yet" HD cards (ford-super-duty, ram-heavy-duty in data/new_models.json) open their pages
    HD_EXN = {t: True for t in HDT if t != 'ford-f-150'}

if HDX == 'pages' and HDT:
    HD_URLS, HD_AE, HD_FIND, HD_CMP = [], [], [], []
    _hdE = lambda s: E(_hh.unescape(str(s)))
    _hd_pct = lambda k, n: round(k / n * 100) if n else 0
    _HD_SRC = HDJ.get('src') or {}
    _HD_WHY = ('No Lemon Index score: automakers report heavy-duty pickup sales together with the half-ton (one F-Series, Ram or Silverado number), '
               'so there is no honest per-truck denominator. These are counts and shares of owner complaints, not failure rates.')
    _HD_HOW = ('Complaints: NHTSA owner complaints filed under the truck&#39;s 2500/3500 (F-250/F-350) names, all years filed, one per complaint number. '
               'Engine: decoded from the complaint&#39;s VIN (position 8 is the engine code) with NHTSA&#39;s vPIC decoder. '
               'Complaints filed as just &ldquo;Silverado&rdquo; or &ldquo;Sierra&rdquo; are left out (they mix 1500s and HDs). '
               'Older trucks have had more years to collect complaints, and popular years draw more because more were sold.')
    def _hd_rows(head, R, cls=''):
        return (f'<div class="tw"><table class="adv{cls}"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr></thead><tbody>'
                + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in R) + '</tbody></table></div>')
    def _hd_bars(items, unit='%'):
        mx = max([1] + [k for _, k in items])
        return '<div class="pts">' + ''.join(f'<div class="pt"><span>{_hdE(p).capitalize()}</span><span class="bt"><i style="width:{k / mx * 100:.0f}%"></i></span><b>{k}{unit}</b></div>' for p, k in items) + '</div>'
    _MN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    def _hd_date(d):
        a = d.split('/'); return f'{_MN[int(a[1]) - 1]} {a[2]}' if len(a) == 3 and a[1].isdigit() and 1 <= int(a[1]) <= 12 else E(d)
    _hd_sc = lambda t: sent_case(t) if 'sent_case' in globals() else t
    def _hd_rec_li(r, tag=''):
        return (f'<li><p class="advh"><a href="https://www.nhtsa.gov/recalls?nhtsaId={E(r["id"])}" target="_blank" rel="noopener nofollow">{E(r["id"])}</a> <small>{_hd_date(r["date"])}</small> '
                f'<b>{E((r["part"] or "Other").split(":")[0].title())}</b>{tag}</p><p>{E(_hd_sc(r["summary"]))}</p>' + (f'<p><b>Fix.</b> {E(_hd_sc(r["fix"]))}</p>' if r.get('fix') else '') + '</li>')
    def _hd_rec_tag(r):
        es = [HDE[e]['short'] for e in r.get('eng') or [] if e in HDE]
        return f' <span class="hd-tag">Names the {E(" / ".join(es))}</span>' if es else ''
    def _hd_q(qs, nm):
        return ''.join(f'<blockquote><p>{E(_hd_sc(q["text"]))}</p><cite>{q["y"]} {E(nm)} owner · NHTSA complaint {q["odi"]}</cite></blockquote>' for q in qs)
    def _hd_miles(g):
        return (f'Half of the owners who gave a mileage reported the problem between <b>{g["p25"]:,}</b> and <b>{g["p75"]:,}</b> miles; the middle report was at <b>{g["median"]:,}</b> miles '
                f'({g["n"]:,} complaints with a mileage).') if g else ''
    def _hd_ser(s, n):
        return _hd_rows(['Crashes', 'Fires', 'Injury reports', 'Death reports', 'Towed'], [[f'{s["crash"]:,}', f'{s["fire"]:,}', f'{s["injured"]:,}', f'{s["deaths"]:,}', f'{s["towed"]:,}']])
    def _hd_comp_share(comps, key):
        return next((p for nm, p, _ in comps if nm == key), 0)
    def _hd_img(t):
        ph = YSL.model_img(t) if hasattr(YSL, 'model_img') else None
        return YSL.model_hero_html(t, HDT[t]['name']) if ph else ''
    _HD_TYPE = {'ford-super-duty': 'Ford', 'ram-heavy-duty': 'Ram', 'chevrolet-silverado-hd': 'Chevrolet', 'gmc-sierra-hd': 'GMC'}
    _HD_LINE = {'ford-super-duty': 'ford-f-series', 'ram-heavy-duty': 'ram-pickup', 'chevrolet-silverado-hd': 'chevrolet-silverado', 'gmc-sierra-hd': 'gmc-sierra'}
    _HD_SHORT = {'ford-super-duty': 'Super Duty', 'ram-heavy-duty': 'Ram 2500/3500', 'chevrolet-silverado-hd': 'Silverado HD', 'gmc-sierra-hd': 'Sierra HD'}
    # 11-12 round 2 follow-up (live search test): no engine sizes on the trucks ("6.0 powerstroke" opens the 6.0 page), the Duramax codes on
    # the Silverado HD only (the Sierra HD's shorter name won every tie), and a small search priority (HD_PRI) so "2500hd" opens the Silverado HD
    _HD_ALIAS = {'ford-super-duty': 'f250 f 250 f-250 f350 f 350 f-350 super duty superduty powerstroke power stroke diesel',
                 'ram-heavy-duty': 'ram 2500 ram 3500 2500 3500 heavy duty hd cummins diesel',
                 'chevrolet-silverado-hd': 'silverado 2500 silverado 3500 2500hd 3500hd 2500 hd 3500 hd duramax lb7 lly lbz lmm lml l5p diesel',
                 'gmc-sierra-hd': 'sierra 2500 sierra 3500 2500hd 3500hd 2500 hd 3500 hd diesel'}
    HD_PRI = {'ford-super-duty': 0, 'ram-heavy-duty': .1, 'chevrolet-silverado-hd': 0, 'gmc-sierra-hd': .1}
    def _hd_engmix(yd):
        """[(slug, label, fuel, n, pct)] for one model year, labels for the cards"""
        return [tuple(x) for x in yd['eng']]
    def _hd_elink(slug, label):
        return f'<a href="{HE_URLS[slug]}">{_hdE(label)}</a>' if slug in HE_URLS and slug in HDE else _hdE(label)

    # ------------------------------------------------------------------ truck model + year pages
    def _hd_truck(t):
        T = HDT[t]; nm = T['name']; sh = _HD_SHORT[t]; mk = _HD_TYPE[t]; Y = {int(y): v for y, v in T['years'].items()}
        ys = sorted(HD_PY[t])
        line = _HD_LINE[t]; lf = next((f for f in YEARS if f['id'] == line), None)
        engs = [e for e, d in HDE.items() if t in d.get('trucks_years', {})]
        # ---- model page
        de = sorted(engs, key=lambda e: HDE[e]['trucks_years'][t][0])
        er = []
        for e in de:
            d = HDE[e]; ty = d['trucks_years'][t]; nT = d['by_truck'].get(t, 0)
            er.append([f'<a href="{HE_URLS[e]}"><b>{_hdE(d["short"])}</b></a><small>{_hdE(d["lay"])}</small>', f'{ty[0]}–{str(ty[-1])[-2:]}' if len(ty) > 1 else str(ty[0]),
                       f'{nT:,}', f'{_hd_comp_share(d["comps"], "engine")}%', f'{_hd_comp_share(d["comps"], "fuel system")}%'])
        eng_sec = (f'<section class="yc hd-eng" id="hdeng"><h2>Which diesel is in it</h2><p>Owners don&#39;t file complaints by engine, so we read each complaint&#39;s VIN. '
                   f'{T["vin"]:,} of {T["n"]:,} complaints have a VIN we could decode.</p>'
                   + _hd_rows(['Diesel engine', 'Years', 'Complaints', 'Name the engine', 'Name the fuel system'], er)
                   + f'<p class="yc-cap">&ldquo;Name the engine&rdquo; = the share of that engine&#39;s complaints (all {E(mk)} trucks we count with it) that list the engine as a problem area. '
                     'It compares what owners complain about, not how often trucks break. <a href="' + HD_DIESEL_HUB + '">Every diesel truck engine compared</a></p></section>') if er else ''
        mx = max([1] + [Y[y]['n'] for y in ys])
        def _top(v): return f'{_hdE(v["comps"][0][0]).capitalize()} ({v["comps"][0][1]}%)' if v['comps'] else '—'
        def _dz(v):
            d_ = [x for x in v['eng'] if x[2] == 'diesel']
            if not d_: return '—'
            return ', '.join(_hd_elink(x[0], x[1].replace(' diesel', '')) + f' {x[4]}%' for x in d_[:2])
        yrows = [[f'<a href="{HDU(t, y)}">{y}</a>', f'{Y[y]["n"]:,}', _dz(Y[y]), _top(Y[y]), str(len(Y[y]['recalls']))] for y in reversed(ys)]
        worst = sorted(ys, key=lambda y: -Y[y]['n'])[:3]
        years_sec = (f'<section class="yc" id="years"><h2>Complaints by model year</h2>'
                     + _hd_rows(['Model year', 'Complaints', 'Diesel (share of VIN-matched)', 'Top problem', 'Recalls'], yrows)
                     + '<p class="yc-cap">All complaints filed so far, so older trucks have had longer to collect them, and popular years draw more because more were sold. Counts, not a score.</p></section>')
        prob = f'<section class="yc" id="problems"><h2>What owners complain about</h2>' + _hd_bars([(p, k) for p, k, _ in T['comps']]) + '<p class="yc-cap">Share of complaints that name each area (one complaint can name several).</p></section>'
        mil = f'<section class="yc" id="mileage"><h2>When problems show up</h2><p>{_hd_miles(T["miles"])}</p></section>' if T.get('miles') else ''
        ser = f'<section class="yc" id="severity"><h2>How serious</h2>{_hd_ser(T["ser"], T["n"])}<p class="yc-cap">As reported by owners to NHTSA, not verified.</p></section>'
        allrec = sorted({r for y in ys for r in Y[y]['recalls']}, key=lambda i: (HDR[i]['date'][6:10] + HDR[i]['date'][3:5] + HDR[i]['date'][:2]) if i in HDR else '', reverse=True)
        allrec = [HDR[i] for i in allrec if i in HDR]
        rec = (f'<section class="yc" id="recalls"><h2>Recalls <span class="yc-n">{len(allrec)}</span></h2><p>Across {ys[0]}–{ys[-1]}. Newest first; each year&#39;s page lists its own.</p><ul class="advr">'
               + ''.join(_hd_rec_li(r, _hd_rec_tag(r)) for r in allrec[:6]) + '</ul>'
               + (f'<details class="cpd"><summary>Show all {len(allrec)}</summary><ul class="advr">' + ''.join(_hd_rec_li(r, _hd_rec_tag(r)) for r in allrec[6:]) + '</ul></details>' if len(allrec) > 6 else '')
               + '<p class="yc-cap">NHTSA recalls by model and year. Recall repairs are free at any dealer: check the exact truck&#39;s VIN.</p></section>') if allrec else ''
        dz = [e for e in de]
        topd = sorted(dz, key=lambda e: -_hd_comp_share(HDE[e]['comps'], 'engine'))
        ans = (f'Owners filed <b>{T["n"]:,} complaints</b> with the government about {ys[0]}–{ys[-1]} {E(nm)} trucks. '
               + (f'By VIN, the {_hdE(HDE[topd[0]]["short"])} years draw the most engine complaints: {_hd_comp_share(HDE[topd[0]]["comps"], "engine")}% of its complaints name the engine, '
                  f'against {_hd_comp_share(HDE[topd[-1]]["comps"], "engine")}% for the {_hdE(HDE[topd[-1]]["short"])}. ' if len(topd) > 1 else '')
               + 'No per-truck score: sales aren&#39;t reported apart from the half-ton.')
        faq = [(f'What are the most common {nm} problems?', f'In owner complaints to the government, the areas named most are {", ".join(p for p, _, _ in T["comps"][:3])}.'),
               (f'Which {sh} diesel has the most engine complaints?', (f'By VIN, the {HDE[topd[0]]["short"]}: {_hd_comp_share(HDE[topd[0]]["comps"], "engine")}% of its complaints name the engine. '
                 f'The {HDE[topd[-1]]["short"]} has the lowest share, {_hd_comp_share(HDE[topd[-1]]["comps"], "engine")}%. Shares of complaints, not failure rates.') if len(topd) > 1 else 'We can only match one diesel generation so far.'),
               (f'Which {sh} years have the most complaints?', f'{", ".join(str(y) for y in worst)} drew the most complaints filed so far ({", ".join(f"{Y[y]["n"]:,}" for y in worst)}). Popular years draw more because more were sold, so these are counts, not a score.'),
               (f'Why doesn&#39;t the {sh} have a Lemon Index score?', _HD_WHY),
               (f'How many recalls does the {nm} have?', f'{len(allrec)} NHTSA recalls across model years {ys[0]}–{ys[-1]}.')]
        if lf: faq.append((f'Where is the {sh} in the {lf["name"]} score?', f'Blended in: the {lf["name"]} page scores the whole line, because sales are reported for the whole line. Its banner shows how much of each year is heavy-duty.'))
        qa = '<section class="yc yqa"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in faq)) + '</section>'
        lnk = (f'<p class="yc-cap">The half-ton has its own scored page: <a href="{CARU(lf)}">{E(lf["name"])} reliability by year</a> (whole line, mostly half-tons). '
               f'Diesel engines: ' + ' · '.join(f'<a href="{HE_URLS[e]}">{_hdE(HDE[e]["short"])}</a>' for e in de) + f' · <a href="{HD_DIESEL_HUB}">all compared</a>.</p>') if lf else ''
        body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/cars/">All cars</a> · {BRAND_A(mk)} · Trucks</p><h1>{E(nm)} problems by year and engine.</h1><p class="ans">{ans}</p></header>'
                + (lambda h: f'<div class="advimg">{h}</div>' if h else '')(_hd_img(t))
                + f'<div class="ygrid">{eng_sec}{years_sec}{prob}{mil}{ser}{rec}{qa}</div>{lnk}<p class="yc-cap">{_HD_WHY} {_HD_HOW} Source: {E(_HD_SRC.get("complaints", "NHTSA"))}; {E(_HD_SRC.get("vin", ""))}; {E(_HD_SRC.get("recalls", ""))}.</p></div>')
        page(HDU(t), f'{nm} Problems by Year and Engine', _hh.unescape(_hre.sub('<[^>]+>', '', ans)), body, ld=[faq_ld([(q, '', _hh.unescape(_hre.sub('<[^>]+>', '', a))) for q, a in faq])])
        HD_URLS.append(HDU(t))
        HD_FIND.append((nm, mk, HDU(t), '', ys, _HD_ALIAS.get(t, ''), 0, HD_PRI.get(t, 0)))   # kind '': a typed year opens that year's page
        # the compare tool (ux_c.py appends HD_CMP to compare.json): complaints in each truck's first 3 years and recalls, never a score
        HD_CMP.append({'i': t, 'n': nm, 'b': mk, 'u': HDU(t), 'k': 'co', 'a': 'duramax lb7 lly lbz lmm lml l5p diesel' if t == 'chevrolet-silverado-hd' else _HD_ALIAS.get(t, ''),   # short: the compare box breaks ties by name + alias length
                       'y': {str(y): [None, Y[y]['n3'], len(Y[y]['recalls']), None, None, None, None, None, None, 0] for y in ys}, 'd': str(max([y for y in ys if y <= 2022] or ys))})
        # ---- year pages
        for i, y in enumerate(ys):
            v = Y[y]; prv, nxt = (ys[i - 1] if i else None), (ys[i + 1] if i + 1 < len(ys) else None)
            mix = _hd_engmix(v); vn = v['vin']
            erows = []
            for s, lab, fu, k, p in mix:
                if k < 3: continue
                ec = v.get('eng_comps', {}).get(s) or []
                erows.append([_hd_elink(s, lab), f'{p}%', f'{k:,}', ', '.join(f'{_hdE(c)} {pp}%' for c, pp, _ in ec[:3]) if ec else '<small>too few to split</small>'])
            dsl = [x for x in mix if x[2] == 'diesel' and x[0] in HDE]
            eng_sec = (f'<section class="yc hd-eng" id="hdeng"><h2>Which engine is in it</h2><p>{vn:,} of the {v["n"]:,} complaints have a VIN we could decode, which tells us the engine.</p>'
                       + _hd_rows(['Engine', 'Share', 'Complaints', 'What they name most'], erows)
                       + (('<p class="yc-cap">Each diesel&#39;s page: ' + ' · '.join(f'<a href="{HE_URLS[x[0]]}">{_hdE(HDE[x[0]]["name"])}</a>' for x in dsl) + '.</p>') if dsl else '')
                       + '</section>') if erows else ''
            prob = f'<section class="yc" id="problems"><h2>What owners complain about</h2>' + _hd_bars([(p, k) for p, k, _ in v['comps']]) + '<p class="yc-cap">Share of this year&#39;s complaints that name each area.</p></section>' if v['comps'] else ''
            mil = f'<section class="yc" id="mileage"><h2>When problems show up</h2><p>{_hd_miles(v["miles"])}</p></section>' if v.get('miles') else ''
            ser = f'<section class="yc" id="severity"><h2>How serious</h2>{_hd_ser(v["ser"], v["n"])}<p class="yc-cap">As reported by owners to NHTSA, not verified.</p></section>'
            rr = [HDR[r] for r in v['recalls'] if r in HDR]
            rec = (f'<section class="yc" id="recalls"><h2>Recalls <span class="yc-n">{len(rr)}</span></h2><ul class="advr">' + ''.join(_hd_rec_li(r, _hd_rec_tag(r)) for r in reversed(rr)) + '</ul>'
                   '<p class="yc-cap">NHTSA recalls for this model year under every name these trucks are filed under. A recall that names an engine applies only to trucks with it. Free at any dealer: check the VIN.</p></section>'
                   if rr else '<section class="yc" id="recalls"><h2>Recalls</h2><p>NHTSA lists no recalls for this model year under these names.</p></section>')
            qs = f'<section class="yc"><h2>In owners&#39; words</h2>{_hd_q(v["quotes"], nm)}</section>' if v['quotes'] else ''
            near = ' · '.join(f'<a href="{HDU(t, w)}">{w}: {Y[w]["n"]:,} complaints</a>' for w in (prv, nxt) if w)
            nb = f'<section class="yc" id="neighbors"><h2>Nearby model years</h2><p>{near} · <a href="{HDU(t)}">every year</a></p></section>'
            top = v['comps'][0] if v['comps'] else None
            md = max(mix, key=lambda x: x[3]) if mix else None
            ans = (f'Owners filed <b>{v["n"]:,} complaints</b> with the government about the {y} {E(nm)}'
                   + (f', most often about {_hdE(top[0])} ({top[1]}%)' if top else '') + '. '
                   + (f'By VIN, {md[4]}% of them are trucks with the {_hd_elink(md[0], md[1])}. ' if md and vn >= 20 else '')
                   + f'{len(rr)} recall{"" if len(rr) == 1 else "s"}. No per-truck score: sales aren&#39;t reported apart from the half-ton.')
            faq = [(f'Is the {y} {sh} reliable?', f'We can&#39;t score it per truck (heavy-duty sales aren&#39;t reported apart from the half-ton). Owners filed {v["n"]:,} complaints about it'
                    + (f', most often about {top[0]} ({top[1]}% of them)' if top else '') + '. ' + (f'Compare the diesel generations on their engine pages.' if dsl else '')),
                   (f'What engine does the {y} {sh} have?', 'By the VINs in owner complaints: ' + ', '.join(f'{x[1]} ({x[4]}%)' for x in mix if x[3] >= 3) + '.' if mix else 'Too few complaints had a VIN to tell.'),
                   (f'How many recalls does the {y} {nm} have?', f'{len(rr)}. Recall repairs are free at any dealer; check the truck&#39;s VIN at nhtsa.gov/recalls.')]
            qa = '<section class="yc yqa"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in faq)) + '</section>'
            ly = (f'<p class="yc-cap">The whole-line score for {y}, mostly half-tons: <a href="{CARU(lf, y)}">{y} {E(lf["name"])}</a>.</p>' if lf and any(w['y'] == y for w in lf['years']) else '')
            body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/cars/">All cars</a> · {BRAND_A(mk)} · <a href="{HDU(t)}">{E(nm)}</a></p>'
                    f'<h1>{y} {E(nm)} problems, engines and recalls.</h1><p class="ans">{ans}</p></header>'
                    + (lambda h: f'<div class="advimg">{h}</div>' if h else '')(_hd_img(t))
                    + f'<div class="ygrid">{eng_sec}{prob}{mil}{ser}{rec}{qs}{nb}{qa}</div>{ly}<p class="yc-cap">{_HD_WHY} {_HD_HOW}</p></div>')
            page(HDU(t, y), f'{y} {nm} Problems, Engines and Recalls', _hh.unescape(_hre.sub('<[^>]+>', '', ans)), body, kind='article',
                 ld=[faq_ld([(q, '', _hh.unescape(_hre.sub('<[^>]+>', '', a))) for q, a in faq])])
            HD_URLS.append(HDU(t, y))
    for _t in ('ford-super-duty', 'ram-heavy-duty', 'chevrolet-silverado-hd', 'gmc-sierra-hd'):
        if _t in HDT: _hd_truck(_t)

    # ------------------------------------------------------------------ engine pages
    HDW = HDJ.get('words') or {}
    # widely discussed issues per engine (checked against our complaint words before anything is said): engine -> [(word key, what it is)]
    HD_KNOWN = {'powerstroke-60': [('head_gasket', 'head gaskets'), ('egr', 'the EGR cooler / valve'), ('oil_cooler', 'the oil cooler'), ('injector', 'injectors')],
                'powerstroke-64': [('coolant', 'radiator and coolant leaks'), ('egr', 'the EGR cooler'), ('emissions', 'the DPF / regen system'), ('fuel_leak', 'fuel leaks')],
                'powerstroke-67': [('cp4', 'the CP4.2 high-pressure fuel pump'), ('emissions', 'the DPF / DEF / NOx sensors'), ('turbo', 'the turbo')],
                'powerstroke-73': [('injector', 'injectors'), ('power_loss', 'stalling (often the cam sensor)')],
                'cummins-59': [('injector', 'injectors'), ('power_loss', 'stalling and power loss (lift pump, VP44 pump on 1999–2002)')],
                'cummins-67': [('emissions', 'the DPF / EGR / DEF system'), ('egr', 'the EGR system'), ('turbo', 'the turbo')],
                'duramax-lb7': [('injector', 'injectors')], 'duramax-lly': [('coolant', 'overheating when towing'), ('injector', 'injectors')],
                'duramax-lbz': [('injector', 'injectors')], 'duramax-lmm': [('emissions', 'the DPF / regen system')],
                'duramax-lml': [('cp4', 'the CP4.2 high-pressure fuel pump'), ('emissions', 'the DPF / DEF system')], 'duramax-l5p': [('emissions', 'the DPF / DEF / NOx sensors'), ('fuel_leak', 'fuel leaks')],
                'ford-ecoboost-27': [('oil_leak', 'oil leaks (the oil pan on early trucks)'), ('cam_phaser', 'cam phaser rattle at cold start'), ('coolant', 'coolant leaks')],
                'f150-ecoboost-35-g1': [('intercooler', 'intercooler condensation (misfire or stumble under load)'), ('timing_chain', 'timing chain stretch'), ('misfire', 'misfires')],
                'f150-ecoboost-35-g2': [('cam_phaser', 'cam phaser rattle at cold start'), ('timing_chain', 'the timing chain')],
                'f150-coyote': [('oil_use', 'oil consumption'), ('misfire', 'misfires / ticking')]}
    def _hd_group(e): return HD_F150 if e in HD_F150 else HD_DIESEL
    def _hd_w(e, k):
        a = (HDE[e]['words'].get(k) or [0, 0]); return a[0], a[1], (a[0] / a[1] * 100 if a[1] else 0)
    def _hd_med(e, k):
        xs = sorted(_hd_w(o, k)[2] for o in _hd_group(e) if o in HDE and o != e)
        return xs[len(xs) // 2] if xs else 0
    def _hd_supported(e, k):
        n, N, p = _hd_w(e, k); m = _hd_med(e, k)
        return n >= 10 and p >= max(1.5 * m, 1.0), n, N, p, m
    def _hd_fmt(p): return 'under 0.1' if p < .05 else f'{p:.1f}' if p < 10 else f'{p:.0f}'
    def _hd_known_html(e):
        ok, no = [], []
        for k, what in HD_KNOWN.get(e, []):
            s, n, N, p, m = _hd_supported(e, k)
            (ok if s else no).append((k, what, n, N, p, m))
        peers = 'F-150 engines' if e in HD_F150 else 'diesel truck generations'
        h = ''
        if ok:
            h += ('<ul class="hd-ki">' + ''.join(f'<li><b>{E(what[:1].upper() + what[1:])}.</b> {n:,} of {N:,} owner complaints ({_hd_fmt(p)}%) {E(HDW.get(k, k))}, against a median of {_hd_fmt(m)}% for the other {peers} we track.'
                                              + ''.join(f'<blockquote><p>{E(_hd_sc(q["text"]))}</p><cite>{q["y"]} owner · NHTSA complaint {q["odi"]}</cite></blockquote>' for q in (HDE[e].get('wq') or {}).get(k, [])[:1]) + '</li>' for k, what, n, N, p, m in ok) + '</ul>')
        if no:
            h += ('<p class="note">Also often talked about, but <b>not</b> standing out in complaints to NHTSA: ' + '; '.join(f'{E(what)} ({n:,} of {N:,}, {_hd_fmt(p)}%, peers {_hd_fmt(m)}%)' for k, what, n, N, p, m in no)
                  + '. That doesn&#39;t mean it never happens, only that owners rarely file it with the government.</p>')
        if not h: return ''
        return (f'<section class="yc engk hd-k" id="known"><h2>Known issues, checked against owner complaints</h2>'
                + (f'<p>Problems owners of trucks with this engine name much more often than owners of other {peers} (at least 1.5× the median, and 10+ complaints):</p>' if ok else
                   f'<p>None of the issues people usually talk about stands out in this engine&#39;s complaints to NHTSA.</p>') + h + '</section>')
    def _hd_eng_years_chart(e):
        d = HDE[e]; by = d['by_year']; mx = max([1] + list(by.values()))
        rows = ''.join(f'<div class="egr"><span class="egy">{y}<small>{E(", ".join(_HD_SHORT.get(t, "F-150") for t, ys in d["trucks_years"].items() if int(y) in ys))}</small></span>'
                       f'<span class="eg-o"><i style="width:{n / mx * 100:.0f}%"></i></span><b>{n:,}</b></div>' for y, n in sorted(by.items()))
        return ('<div class="egc sce1"><div class="egh" aria-hidden="true"><span>Model year</span><span>Owner complaints <em>count, any part of the truck, VIN-matched to this engine</em></span></div>'
                + rows + '</div>')
    def _hd_cmp_table(group, cur=None):
        R = []
        for o in sorted([o for o in group if o in HDE], key=lambda o: -_hd_comp_share(HDE[o]['comps'], 'engine')):
            d = HDE[o]; nm = f'<b>{_hdE(d["short"])}</b>' if o == cur else f'<a href="{HE_URLS[o]}">{_hdE(d["short"])}</a>'
            R.append([nm, f'{d["years"][0]}–{str(d["years"][-1])[-2:]}', f'{d["n"]:,}', f'{_hd_comp_share(d["comps"], "engine")}%', f'{_hd_comp_share(d["comps"], "fuel system")}%',
                      f'{_hd_fmt(_hd_w(o, "power_loss")[2])}%', str(len(d['recalls']))])
        return _hd_rows(['Engine', 'Years', 'Complaints', 'Name the engine', 'Name the fuel system', 'Stalled or lost power', 'Recalls naming it'], R)
    def _hd_words_html(e):
        d = HDE[e]; R = []
        for k, lab in HDW.items():
            n, N, p = _hd_w(e, k); m = _hd_med(e, k)
            if n < 5: continue
            R.append((p, [E(lab[:1].upper() + lab[1:]), f'{n:,}', f'{_hd_fmt(p)}%', f'{_hd_fmt(m)}%']))
        R.sort(key=lambda r: -r[0])
        if not R: return ''
        peers = 'other F-150 engines' if e in HD_F150 else 'other diesel truck engines'
        return (f'<section class="yc" id="words"><h2>What owners write</h2>' + _hd_rows(['Complaints that', 'Count', 'Share', f'Median, {peers}'], [r for _, r in R[:10]])
                + '<p class="yc-cap">Counted from the owner&#39;s own words in each complaint (all of the truck, not only the engine). A share, not a failure rate.</p></section>')
    def _hd_engine_page(e):
        d = HDE[e]; nm = d['name']; path = HE_URLS[e]; ys = d['years']; y0, y1 = ys[0], ys[-1]; f150 = e in HD_F150
        trucks = [(t, tys) for t, tys in d['trucks_years'].items()]
        tnames = ' and '.join(HDT[t]['name'] if t in HDT else 'Ford F-150' for t, _ in trucks)
        es, fs = _hd_comp_share(d['comps'], 'engine'), _hd_comp_share(d['comps'], 'fuel system')
        grp = _hd_group(e); rank = sorted([o for o in grp if o in HDE], key=lambda o: -_hd_comp_share(HDE[o]['comps'], 'engine')).index(e) + 1
        ngrp = len([o for o in grp if o in HDE]); peers = 'F-150 engines' if f150 else 'diesel truck engine generations'
        ans1 = (f'The {E(d["lay"])} in the {E(tnames).replace("Ford F-150", '<a href="/cars/ford-f-series/">Ford F-150</a>', 1) if f150 else E(tnames)}, model years {y0}–{y1}. Owners filed <b>{d["n"]:,} complaints</b> about trucks with it (matched by VIN); '
                f'<b>{es}%</b> name the engine, #{rank} of the {ngrp} {peers} we track (1 = the most).')
        chips = (f'<div class="trc"><div><b>{y0}–{str(y1)[-2:]}</b><span>model years</span></div><div><b>{d["n"]:,}</b><span>owner complaints</span></div>'
                 f'<div><b>{es}%</b><span>name the engine</span></div><div><b>{len(d["recalls"])}</b><span>recalls name it</span></div></div>')
        sec = []
        sec.append(_hd_known_html(e))
        sec.append('<h2>Owner complaints by model year</h2>' + _hd_eng_years_chart(e)
                   + '<p class="note">Counts of complaints filed so far. Older trucks have had longer to collect them, and popular years draw more because more were sold: '
                     'no one reports sales by engine, so there&#39;s no per-truck rate. Compare the shares below instead.</p>')
        sec.append(f'<section class="yc" id="problems"><h2>What owners complain about</h2>' + _hd_bars([(p, k) for p, k, _ in d['comps']]) + '<p class="yc-cap">Share of this engine&#39;s complaints that name each area (one complaint can name several).</p></section>')
        sec.append(_hd_words_html(e))
        if d.get('miles'): sec.append(f'<section class="yc" id="mileage"><h2>When problems show up</h2><p>{_hd_miles(d["miles"])}</p></section>')
        rr = [HDR[i] for i in d['recalls'] if i in HDR]
        sec.append(f'<section class="yc sce-r" id="recalls"><h2>Recalls that name this engine <span class="yc-n">{len(rr)}</span></h2>'
                   + ('<ul class="advr">' + ''.join(_hd_rec_li(r) for r in rr[:6]) + '</ul>' + (f'<details class="cpd"><summary>Show all {len(rr)}</summary><ul class="advr">' + ''.join(_hd_rec_li(r) for r in rr[6:]) + '</ul></details>' if len(rr) > 6 else '')
                      if rr else '<p>No NHTSA recall on these trucks names this engine.</p>')
                   + '<p class="yc-cap">NHTSA recalls on these trucks and years whose text names this engine (its size, or diesel / Cummins / Duramax / Power Stroke). The rest (brakes, air bags, wiring ...) are on each truck year&#39;s page.</p></section>')
        tl = ''.join(f'<li><a href="{HDU(t)}">{E(HDT[t]["name"])}</a>: ' + ' · '.join(f'<a href="{HDU(t, y)}">{y}</a>' for y in tys if _hd_has(t, y)) + '</li>'
                     for t, tys in trucks if t in HDT and t != 'ford-f-150')
        if tl: sec.append(f'<section class="yc" id="trucks"><h2>Trucks with this engine</h2><ul class="hd-tl">{tl}</ul></section>')
        if f150: sec.insert(0, (globals().get('EU_CARS_HTML') or (lambda *a: ''))(path, 'Trucks with this engine'))   # 11-13 N3 (nav report 3): the F-150, each year linked, first
        if d.get('quotes'): sec.append(f'<section class="yc"><h2>In owners&#39; words</h2>{_hd_q(d["quotes"], tnames)}</section>')
        sec.append(f'<section class="yc" id="compare"><h2>Against the other {peers}</h2>' + _hd_cmp_table(grp, e)
                   + '<p class="yc-cap">Shares of each engine&#39;s own complaints, matched by VIN. They show what owners complain about, not how often trucks break.'
                   + (f' <a href="{HD_F150_CMP}">2.7 vs 3.5 vs 5.0 in the F-150, year by year</a>' if f150 else f' <a href="{HD_DIESEL_HUB}">Every diesel truck engine compared</a>') + '</p></section>')
        top3 = ', '.join(p for p, _, _ in d['comps'][:3])
        faq = [(f'Is the {nm} reliable?', f'No one reports sales by engine, so there&#39;s no per-truck score. Of the {d["n"]:,} complaints owners filed about trucks with it, {es}% name the engine, #{rank} of {ngrp} {peers} we track (1 = the most).'
                + (' ' + ' '.join(f'{n:,} ({_hd_fmt(p)}%) {HDW.get(k, k)}, against {_hd_fmt(m)}% for its peers.' for k, what, n, N, p, m in
                        [(k, w) + _hd_supported(e, k)[1:] for k, w in HD_KNOWN.get(e, []) if _hd_supported(e, k)[0]][:2]) if HD_KNOWN.get(e) else '')),
               (f'What trucks have the {nm}?', f'In our data: the {tnames}, model years {y0}–{y1}, matched by the VIN in each owner complaint.'),
               (f'What are the most common {d["short"]} problems?', f'In owner complaints to the government: {top3}.'),
               (f'How many recalls name the {d["short"]}?', f'{len(rr)} NHTSA recall{"" if len(rr) == 1 else "s"} on these trucks name{"s" if len(rr) == 1 else ""} it.')]
        sec.append('<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(_hh.unescape(a))}</p>' for q, a in faq)) + '</section>')
        kick = ('<a href="/engines/?type=trucks">Trucks &amp; diesel engines</a> · ' + (f'<a href="{HD_F150_CMP}">F-150 engines compared</a>' if f150 else f'<a href="{HD_DIESEL_HUB}">Diesel truck engines compared</a>'))
        body = (f'<article class="study tr2 eng2 hde"><p class="kicker">{kick}</p><h1>{E(nm)} reliability by year</h1><p class="tra">{ans1} '
                f'<button type="button" class="shl" data-share="{E(f"{nm}: owner complaints by year, matched by VIN. Free:")}">Share ↗</button></p>{chips}'
                + ''.join(x for x in sec if x) + f'<p class="yc-cap">Source: {E(_HD_SRC.get("complaints", "NHTSA"))}; engines: {E(_HD_SRC.get("vin", ""))}; {E(_HD_SRC.get("recalls", ""))}. '
                f'{"Engine names and years: Ford." if d["maker"] == "Ford" else "Engine names and years: Cummins / Ram." if d["maker"] == "Ram" else "Engine names and years: GM (RPO codes)."}</p></article>')
        title = f'{nm} Problems & Reliability by Year'
        desc = (f'{_hh.unescape(nm)} ({d["lay"]}), {y0}-{y1}: {d["n"]:,} owner complaints matched by VIN, {es}% name the engine. '
                f'Problems by year, what owners report, and {len(rr)} recalls that name it.')
        page(path, title, desc, body, ld=[faq_ld([(q, '', _hh.unescape(a)) for q, a in faq])])
        HD_URLS.append(path)
        al = {'cummins-59': 'cummins 5.9 24v 24 valve ram diesel', 'cummins-67': 'cummins 6.7 ram diesel', 'ford-ecoboost-27': '2.7 ecoboost 2.7l f150 f-150 nano',
              'powerstroke-73': 'powerstroke power stroke 7.3 f250 f350 diesel', 'powerstroke-60': 'powerstroke power stroke 6.0 f250 f350 diesel',
              'powerstroke-64': 'powerstroke power stroke 6.4 f250 f350 diesel', 'powerstroke-67': 'powerstroke power stroke 6.7 f250 f350 diesel scorpion'}.get(e, f'duramax {d["code"].lower()} 6.6 silverado sierra 2500hd 3500hd diesel')
        al += ' ' + d['lay'].split(' ')[0].replace('.', '')   # "6.0" is read as "60" by the site search
        HD_AE.append(dict(url=path, name=nm, code=d['code'], lay=d['lay'], yrs=f'{y0}–{str(y1)[-2:]}', img=None, yt=(None, 0, ''), used=[HDT[t]['name'] if t in HDT else 'Ford F-150' for t, _ in trucks],
                          t={'t'}, f=d['fuel'], mk={'GM': 'Chevrolet', 'Ram': 'Ram'}.get(d['maker'], d['maker']), o=(-1, 2, -es), alias=al))
    for _e in HD_DIESEL + ['ford-ecoboost-27']:
        if _e in HDE: _hd_engine_page(_e)

    # ------------------------------------------------------------------ diesel truck engines compared (the "Trucks & diesel" landing)
    def _hd_hub():
        _dz = [e for e in HD_DIESEL if e in HDE]
        top = sorted(_dz, key=lambda e: -_hd_comp_share(HDE[e]['comps'], 'engine'))
        lede = (f'{len(_dz)} heavy-duty diesel generations in the Ram 2500/3500, Ford Super Duty and Silverado / Sierra HD, matched to {sum(HDE[e]["n"] for e in _dz):,} owner complaints by VIN. '
                f'The {HDE[top[0]]["short"]} draws the biggest share of engine complaints ({_hd_comp_share(HDE[top[0]]["comps"], "engine")}%), the {HDE[top[-1]]["short"]} the smallest ({_hd_comp_share(HDE[top[-1]]["comps"], "engine")}%).')
        ki = []
        for e in _dz:
            for k, what in HD_KNOWN.get(e, []):
                s, n, N, p, m = _hd_supported(e, k)
                if s: ki.append(f'<li><a href="{HE_URLS[e]}"><b>{_hdE(HDE[e]["short"])}</b></a>: {E(what)}, {n:,} of {N:,} complaints ({_hd_fmt(p)}%) against a {_hd_fmt(m)}% median.</li>')
        body = (f'<article class="study tr2 eng2 hde"><p class="kicker"><a href="/engines/?type=trucks">Trucks &amp; diesel engines</a> · <a href="/engines/">Every engine</a></p>'
                f'<h1>Diesel truck engines compared</h1><p class="tra">{E(lede)}</p>'
                f'<section class="yc" id="compare"><h2>Every generation, side by side</h2>' + _hd_cmp_table(_dz)
                + '<p class="yc-cap">Each column is a share of that engine&#39;s own complaints (VIN-matched), so popular engines don&#39;t win just by selling more. '
                  'None of these is a failure rate: no one reports HD sales by engine.</p></section>'
                + (f'<section class="yc engk"><h2>Engines to check hardest</h2><p>Known problems that stand out in owner complaints (at least 1.5× the median of the other generations, 10+ complaints):</p><ul class="hd-ki">{"".join(ki)}</ul></section>' if ki else '')
                + '<section class="yc"><h2>The trucks</h2><ul class="hd-tl">' + ''.join(f'<li><a href="{HDU(t)}">{E(HDT[t]["name"])}</a></li>' for t in ('ram-heavy-duty', 'ford-super-duty', 'chevrolet-silverado-hd', 'gmc-sierra-hd') if t in HDT)
                + f'</ul><p class="yc-cap">Half-ton? <a href="{HD_F150_CMP}">F-150: 2.7 vs 3.5 EcoBoost vs 5.0</a>.</p></section>'
                + f'<p class="yc-cap">{_HD_HOW} Source: {E(_HD_SRC.get("complaints", "NHTSA"))}; {E(_HD_SRC.get("vin", ""))}; {E(_HD_SRC.get("recalls", ""))}.</p></article>')
        faq = [('Which diesel truck engine has the most engine complaints?', f'By VIN-matched owner complaints, the {HDE[top[0]]["name"]}: {_hd_comp_share(HDE[top[0]]["comps"], "engine")}% of its complaints name the engine. A share, not a failure rate.'),
               ('Which diesel truck engine has the fewest engine complaints?', f'The {HDE[top[-1]]["name"]}: {_hd_comp_share(HDE[top[-1]]["comps"], "engine")}% of its complaints name the engine.')]
        body = body.replace('</article>', '<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq)) + '</section></article>', 1)
        page(HD_DIESEL_HUB, 'Diesel Truck Engines Compared: Cummins, Duramax, Power Stroke', lede, body, ld=[faq_ld([(q, '', a) for q, a in faq])])
        HD_URLS.insert(0, HD_DIESEL_HUB)
        HD_AE.append(dict(url=HD_DIESEL_HUB, name='Diesel truck engines compared', code='', lay='Cummins, Duramax, Power Stroke', yrs='1999–25', img=None, yt=(None, 0, ''),
                          used=['Ram 2500/3500', 'Super Duty', 'Silverado HD', 'Sierra HD'], t={'t'}, f='diesel', mk='Trucks', o=(-1, 0, 0), alias='diesel trucks compare cummins duramax powerstroke hd'))
    _hd_hub()

    # ------------------------------------------------------------------ F-150: 2.7 vs 3.5 vs 5.0 (Ryan)
    def _hd_f150():
        es = [e for e in HD_F150 if e in HDE]
        if len(es) < 2: return
        R = []
        rows = [('Model years', lambda d, e: f'{d["years"][0]}–{str(d["years"][-1])[-2:]}'), ('Complaints (VIN-matched)', lambda d, e: f'{d["n"]:,}'),
                ('Name the engine', lambda d, e: f'{_hd_comp_share(d["comps"], "engine")}%'), ('Name the transmission / drivetrain', lambda d, e: f'{_hd_comp_share(d["comps"], "transmission & drivetrain")}%')]
        rows += [(HDW[k][:1].upper() + HDW[k][1:], (lambda k: lambda d, e: f'{_hd_fmt(_hd_w(e, k)[2])}%')(k)) for k in ('power_loss', 'oil_leak', 'oil_use', 'cam_phaser', 'timing_chain', 'misfire', 'intercooler') if k in HDW]
        rows += [('Middle mileage at the report', lambda d, e: f'{d["miles"]["median"]:,}' if d.get('miles') else '—'), ('Recalls that name it', lambda d, e: str(len(d['recalls'])))]
        head = ['', *[f'<a href="{HE_URLS[e]}">{_hdE(HDE[e]["short"])}</a>' for e in es]]
        tbl = _hd_rows(head, [[f'<b>{lab}</b>'] + [fn(HDE[e], e) for e in es] for lab, fn in rows], ' hd-cmp')
        yrs = sorted({int(y) for e in es for y in HDE[e]['by_year']})
        yr = [[str(y)] + [(f'{HDE[e]["by_year"].get(str(y), 0):,}' if str(y) in HDE[e]['by_year'] else '—') for e in es] for y in yrs if y >= 2011]
        ytbl = _hd_rows(['Model year', *[_hdE(HDE[e]['short']) for e in es]], yr)
        ki = []
        for e in es:
            for k, what in HD_KNOWN.get(e, []):
                s, n, N, p, m = _hd_supported(e, k)
                if s: ki.append(f'<li><a href="{HE_URLS[e]}"><b>{_hdE(HDE[e]["short"])}</b></a>: {E(what)}, {n:,} of {N:,} complaints ({_hd_fmt(p)}%) against a {_hd_fmt(m)}% median for the others.</li>')
        top = sorted(es, key=lambda e: -_hd_comp_share(HDE[e]['comps'], 'engine'))
        lede = (f'Ford doesn&#39;t report F-150 sales by engine, so nobody can honestly say which engine breaks more per truck. What we can show: what owners of each one complain about, '
                f'from {sum(HDE[e]["n"] for e in es):,} complaints matched to the engine by VIN. The {HDE[top[0]]["short"]} draws the biggest share of engine complaints '
                f'({_hd_comp_share(HDE[top[0]]["comps"], "engine")}%), the {HDE[top[-1]]["short"]} the smallest ({_hd_comp_share(HDE[top[-1]]["comps"], "engine")}%).')
        body = (f'<article class="study tr2 eng2 hde"><p class="kicker"><a href="/engines/?type=trucks">Trucks &amp; diesel engines</a> · <a href="/cars/ford-f-series/">Ford F-150 reliability by year</a></p>'
                f'<h1>F-150 engines: 2.7 vs 3.5 EcoBoost vs 5.0</h1><p class="tra">{lede}</p>'
                f'<section class="yc" id="compare"><h2>Side by side</h2>{tbl}<p class="yc-cap">Every percentage is a share of that engine&#39;s own complaints, counted from the area owners pick and their own words. '
                f'The 3.5 EcoBoost changed in 2017 (2nd generation, with port injection added), so it has two columns. Raptor (High Output), PowerBoost hybrid and Lightning complaints are left out.</p></section>'
                + (f'<section class="yc engk"><h2>What stands out</h2><ul class="hd-ki">{"".join(ki)}</ul><p class="yc-cap">Only problems at least 1.5× the median of the other F-150 engines, with 10+ complaints.</p></section>' if ki else '')
                + f'<section class="yc" id="years"><h2>Complaints by model year and engine</h2>{ytbl}<p class="yc-cap">Counts filed so far, not rates: the 3.5 EcoBoost sold the most, so it draws the most.</p></section>'
                + f'<section class="yc"><h2>Each engine</h2><ul class="hd-tl"><li><a href="{HE_URLS["ford-ecoboost-27"]}">2.7 EcoBoost</a></li><li><a href="/engines/ford-ecoboost-35/">3.5 EcoBoost</a> (F-150 data at the top of the page)</li>'
                  f'<li><a href="/engines/ford-coyote/">5.0 Coyote</a> (F-150 data at the top of the page)</li><li><a href="/cars/ford-f-series/">F-150 reliability by year</a></li></ul></section>'
                + f'<p class="yc-cap">Source: {E(_HD_SRC.get("complaints", "NHTSA"))}; engines: {E(_HD_SRC.get("vin", ""))} (VIN position 8); {E(_HD_SRC.get("recalls", ""))}.</p></article>')
        faq = [('Which F-150 engine is the most reliable?', _hh.unescape(_hre.sub('<[^>]+>', '', lede))),
               ('Is the 2.7 EcoBoost better than the 3.5?', f'By the share of owner complaints that name the engine: 2.7 {_hd_comp_share(HDE["ford-ecoboost-27"]["comps"], "engine")}%, 3.5 gen 1 {_hd_comp_share(HDE["f150-ecoboost-35-g1"]["comps"], "engine")}%, 3.5 gen 2 {_hd_comp_share(HDE["f150-ecoboost-35-g2"]["comps"], "engine")}%. Shares, not failure rates.' if all(x in HDE for x in ('ford-ecoboost-27', 'f150-ecoboost-35-g1', 'f150-ecoboost-35-g2')) else ''),
               ('Is the 5.0 Coyote more reliable than the EcoBoost?', f'The 5.0&#39;s complaints name the engine {_hd_comp_share(HDE["f150-coyote"]["comps"], "engine")}% of the time. Compare the table: each column is that engine&#39;s own complaints.' if 'f150-coyote' in HDE else '')]
        faq = [(q, a) for q, a in faq if a]
        body = body.replace('</article>', '<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{a}</p>' for q, a in faq)) + '</section></article>', 1)
        page(HD_F150_CMP, 'F-150 Engines Compared: 2.7 vs 3.5 EcoBoost vs 5.0 V8', _hh.unescape(_hre.sub('<[^>]+>', '', lede)), body, ld=[faq_ld([(q, '', _hh.unescape(_hre.sub('<[^>]+>', '', a))) for q, a in faq])])
        HD_URLS.append(HD_F150_CMP)
        HD_AE.append(dict(url=HD_F150_CMP, name='F-150 engines: 2.7 vs 3.5 vs 5.0', code='', lay='2.7 / 3.5 EcoBoost V6, 5.0 V8', yrs='2011–25', img=None, yt=(None, 0, ''),
                          used=['Ford F-150'], t={'t'}, f='gas', mk='Ford', o=(-1, 1, 0), alias='f150 f-150 2.7 3.5 5.0 ecoboost coyote compare vs'))
    _hd_f150()

    # sections for the existing supercar/performance engine pages (supercar_engine_pages.py calls HD_SCE(e) at the top of each page)
    def HD_SCE(e):
        es = {'ford-ecoboost-35': ['f150-ecoboost-35-g1', 'f150-ecoboost-35-g2'], 'ford-coyote': ['f150-coyote']}.get(e)
        if not es or not any(x in HDE for x in es): return []
        R = []
        for x in es:
            if x not in HDE: continue
            d = HDE[x]
            R.append([f'<b>{_hdE(d["short"])}</b>', f'{d["years"][0]}–{str(d["years"][-1])[-2:]}', f'{d["n"]:,}', f'{_hd_comp_share(d["comps"], "engine")}%',
                      ', '.join(p for p, _, _ in d['comps'][:3]), str(len(d['recalls']))])
        ki = []
        for x in es:
            for k, what in HD_KNOWN.get(x, []):
                s, n, N, p, m = _hd_supported(x, k)
                if s: ki.append(f'<li><b>{_hdE(HDE[x]["short"])}</b>: {E(what)}, {n:,} of {N:,} complaints ({_hd_fmt(p)}%) against a {_hd_fmt(m)}% median for the other F-150 engines.</li>')
        rr = sorted({i for x in es if x in HDE for i in HDE[x]['recalls']}, reverse=True)
        what = 'The same 3.5 EcoBoost family powers the F-150 (2nd generation from 2017).' if e == 'ford-ecoboost-35' else 'The 5.0 Coyote also powers the F-150.'
        return [(f'<section class="yc hd-sce" id="f150"><h2>In the Ford F-150</h2><p>{what} Owners filed '
                 f'{sum(HDE[x]["n"] for x in es if x in HDE):,} complaints about F-150s with it (matched by VIN):</p>'
                 + _hd_rows(['F-150 engine', 'Model years', 'Complaints', 'Name the engine', 'Top areas', 'Recalls naming it'], R)
                 + (f'<ul class="hd-ki">{"".join(ki)}</ul>' if ki else '')
                 + (f'<details class="cpd"><summary>F-150 recalls that name it ({len(rr)})</summary><ul class="advr">' + ''.join(_hd_rec_li(HDR[i]) for i in rr if i in HDR) + '</ul></details>' if rr else '')
                 + f'<p class="yc-cap">Engine from each complaint&#39;s VIN (NHTSA vPIC). Shares of that engine&#39;s own complaints, not failure rates: Ford doesn&#39;t report sales by engine. '
                   f'<a href="{HD_F150_CMP}">2.7 vs 3.5 vs 5.0 in the F-150</a> · <a href="/cars/ford-f-series/">F-150 by year</a></p>'
                 + (f'<p class="note">The rest of this page covers the {"Ford GT" if e == "ford-ecoboost-35" else "Mustang"} versions only.</p>') + '</section>')]
    # the F-150 engines on /engines/ were coming-soon cards with no link (Ryan)
    print('hd pages:', len(HD_URLS), 'urls,', len(HD_AE), 'engine cards')
