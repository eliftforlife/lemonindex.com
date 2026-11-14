# 11-13 (Elijah: "turn the Coming soon engines into real engine pages, highest traffic first"): everyday-car engine pages built the way the
# F-150 / heavy-duty engine pages were (hd_pages.py): NHTSA owner complaints matched to the engine through each complaint's VIN (NHTSA vPIC),
# from data/vin_engines.json (data_vin_engines.py). Run by build.py with exec() in two phases, so everything build.py defines is in scope:
#   VEX = 'hooks'  (before engine_uses.py): VE_URL (engine -> page), VE_USE (engine page x /cars/ model x model years with 3+ VIN-matched
#                  complaints, for ENGINE_USES: "Engines in this car" on car pages and "Cars with this engine" on the engine page)
#   VEX = 'pages'  (after supercar_engine_pages.py, so the one YouTube rank pool includes these pages): a page for each engine that has none yet (/engines/<slug>/),
#                  VE_SCE(path) = the VIN-matched everyday-car sections for engines whose page already exists (the 2GR-FE, the EA888 from the
#                  Golf R file, the Hyundai G4KH from the N cars), VE_AE (cards for /engines/), VE_COVER (models whose coming-soon card these
#                  pages replace), VE_URLS (sitemap)
# No per-car rate: no one reports sales by engine. Every page shows counts and shares of complaints and says so. Engines that don't reach the
# site's bar (data_vin_engines.MIN_N complaints over MIN_YEARS model years) get no page and stay "Coming soon" on /engines/.
import json as _vj, os as _vos, re as _vre, html as _vh
if VEX == 'hooks':
    VEJ = _load('data/vin_engines.json') if _vos.path.exists('data/vin_engines.json') else {}
    VEE, VER = VEJ.get('engines') or {}, VEJ.get('recalls') or {}
    VE_URL = {e: d.get('page') or f'/engines/{e}/' for e, d in VEE.items()}
    # the name on car pages' engine chips ("Engines in the 2017 Highlander: 2GR-FKS 3.5 V6")
    VE_CHIP = {e: _vre.sub(r'^(Toyota|GM|Hyundai / Kia|Honda|Ford|Nissan|Chrysler|Subaru|Mazda|VW / Audi) ', '', d['name']) for e, d in VEE.items()}
    VE_USE = []
    for _e, _d in VEE.items():
        for _fid, _c in _d['by_car'].items():
            _ys = [int(y) for y, n in _c['years'].items() if n >= 3]
            if _ys: VE_USE.append((VE_URL[_e], _fid, _ys, VE_CHIP[_e]))

if VEX == 'hooks':
    VE_URLS, VE_AE, VE_COVER = [], [], {}
    if 'AIE' not in globals(): exec(open('ai_engine_photos.py', encoding='utf-8').read())   # 11-13 AI engine illustrations (data/ai_engine_photos.json)
    _vE = lambda s: E(_vh.unescape(str(s)))
    _VSRC = VEJ.get('src') or {}
    _VW = VEJ.get('words') or {}
    _VM = {f['id']: f for f in YEARS}
    _vsc = lambda t: sent_case(t) if 'sent_case' in globals() else t
    _vcar = lambda fid: _VM[fid]['name'] if fid in _VM else fid
    _VHOW = ('Complaints: NHTSA owner complaints filed under each car&#39;s own NHTSA names (the same ones its car pages count), all years filed, one per complaint number. '
             'Engine: decoded from the complaint&#39;s VIN with NHTSA&#39;s vPIC decoder (displacement, cylinders, engine model, turbo, hybrid) and the engine maker&#39;s model years; '
             'a VIN that doesn&#39;t decode to exactly one engine is left out. Older cars have had more years to collect complaints, and popular cars draw more because more were sold.')
    def _v_rows(head, R):
        return ('<div class="tw"><table class="adv"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr></thead><tbody>'
                + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in R) + '</tbody></table></div>')
    def _v_bars(items):
        mx = max([1] + [k for _, k in items])
        return '<div class="pts">' + ''.join(f'<div class="pt"><span>{_vE(p).capitalize()}</span><span class="bt"><i style="width:{k / mx * 100:.0f}%"></i></span><b>{k}%</b></div>' for p, k in items) + '</div>'
    _VMN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    def _v_date(d):
        a = d.split('/'); return f'{_VMN[int(a[1]) - 1]} {a[2]}' if len(a) == 3 and a[1].isdigit() and 1 <= int(a[1]) <= 12 else E(d)
    def _v_rec_li(r):
        cars = '; '.join(f'{_vcar(f).split(" ", 1)[-1]} {", ".join(str(y) for y in sorted(ys))}' for f, ys in (r.get('cars') or {}).items())
        return (f'<li><p class="advh"><a href="https://www.nhtsa.gov/recalls?nhtsaId={E(r["id"])}" target="_blank" rel="noopener nofollow">{E(r["id"])}</a> <small>{_v_date(r["date"])}</small> '
                f'<b>{E((r["part"] or "Other").split(":")[0].title())}</b> <small>{E(cars)}</small></p><p>{E(_vsc(r["summary"]))}</p>' + (f'<p><b>Fix.</b> {E(_vsc(r["fix"]))}</p>' if r.get('fix') else '') + '</li>')
    def _v_miles(g):
        return (f'Half of the owners who gave a mileage reported the problem between <b>{g["p25"]:,}</b> and <b>{g["p75"]:,}</b> miles; the middle report was at <b>{g["median"]:,}</b> miles '
                f'({g["n"]:,} complaints with a mileage).') if g else ''
    _v_share = lambda comps, key: next((p for nm, p, _ in comps if nm == key), 0)
    _v_fmt = lambda p: 'under 0.1' if p < .05 else f'{p:.1f}' if p < 10 else f'{p:.0f}'
    def _v_w(e, k):
        if k == 'fire': a = [VEE[e]['ser']['fire'], VEE[e]['n']]
        else: a = VEE[e]['words'].get(k) or [0, 0]
        return a[0], a[1], (a[0] / a[1] * 100 if a[1] else 0)
    def _v_med(e, k):
        xs = sorted(_v_w(o, k)[2] for o in VEE if o != e)
        return xs[len(xs) // 2] if xs else 0
    def _v_sup(e, k):
        n, N, p = _v_w(e, k); m = _v_med(e, k)
        return n >= 10 and p >= max(1.5 * m, 1.0), n, N, p, m
    _VWL = dict(_VW, fire='were filed with a fire reported')
    # widely discussed issues per engine, checked against the complaints before anything is said: engine -> [(word key, what it is)]
    VE_KNOWN = {'toyota-2gr-fks': [('water_pump', 'water pump leaks'), ('oil_leak', 'oil leaks')],
                'toyota-2gr-fe': [('oil_leak', 'the VVT-i oil line and other oil leaks'), ('water_pump', 'water pump leaks')],
                'gm-53-gen5': [('lifter', 'lifter failure and ticking'), ('deact', 'cylinder deactivation (AFM / DFM)'), ('oil_use', 'oil consumption')],
                'gm-53-gen4': [('oil_use', 'oil consumption (AFM)'), ('deact', 'cylinder deactivation (AFM)'), ('lifter', 'lifters and ticking')],
                'gm-62-gen5': [('lifter', 'lifter failure and ticking'), ('deact', 'cylinder deactivation (AFM / DFM)')],
                'hyundai-theta2-24': [('seize', 'engine knock and seizure (rod bearings)'), ('fire', 'engine fires'), ('oil_use', 'oil consumption')],
                'hyundai-theta2-20t': [('seize', 'engine knock and seizure (rod bearings)'), ('fire', 'engine fires'), ('turbo', 'the turbo')],
                'honda-j35': [('deact', 'cylinder deactivation (VCM)'), ('misfire', 'misfires'), ('oil_use', 'oil consumption')],
                'ford-35-cyclone': [('water_pump', 'the internal water pump'), ('coolant', 'coolant loss and overheating')],
                'ford-ecoboost-15': [('coolant', 'coolant loss into the cylinders'), ('head_gasket', 'head gaskets'), ('misfire', 'misfires')],
                'ford-ecoboost-20': [('coolant', 'coolant loss into the cylinders'), ('misfire', 'misfires')],
                'nissan-vq35': [('oil_use', 'oil consumption'), ('timing_chain', 'the timing chain')],
                'chrysler-36-pentastar': [('oil_housing', 'oil filter housing / oil cooler leaks'), ('lifter', 'rocker arm and lifter ticking')],
                'chrysler-57-hemi': [('lifter', 'lifter and camshaft failure (the "Hemi tick")'), ('misfire', 'misfires'), ('deact', 'cylinder deactivation (MDS)')],
                'subaru-fb25': [('oil_use', 'oil consumption')], 'subaru-fb20': [('oil_use', 'oil consumption')],
                'mazda-skyactiv-25': [('oil_use', 'oil consumption'), ('deact', 'cylinder deactivation')],
                'toyota-2ar-fe': [('oil_use', 'oil consumption'), ('water_pump', 'water pump leaks')], 'toyota-a25a': [('oil_use', 'oil consumption')],
                'vw-ea888': [('oil_use', 'oil consumption'), ('timing_chain', 'the timing chain tensioner'), ('water_pump', 'water pump and thermostat housing leaks'), ('carbon', 'carbon buildup')],
                'honda-15t': [('oil_dil', 'oil dilution (fuel in the oil)')], 'honda-k24': [('oil_use', 'oil consumption'), ('cam_phaser', 'VTC actuator rattle at cold start')],
                'nissan-qr25': [('oil_use', 'oil consumption')], 'toyota-2az-fe': [('oil_use', 'oil consumption'), ('head_gasket', 'head gaskets / head bolt threads')],
                'toyota-1gr-fe': [('head_gasket', 'head gaskets')], 'toyota-3ur-fe': [('water_pump', 'water pump leaks')], 'chrysler-24-tigershark': [('oil_use', 'oil consumption')],
                'hyundai-lambda2-33': [('oil_use', 'oil consumption')], 'gm-14-turbo': [('coolant', 'coolant leaks'), ('oil_leak', 'oil leaks (PCV / valve cover)')],
                'gm-36-v6': [('timing_chain', 'timing chain stretch')], 'gm-24-ecotec': [('oil_use', 'oil consumption (piston rings)'), ('timing_chain', 'the timing chain')],
                'ram-30-ecodiesel': [('seize', 'engine failure (crankshaft / bearings)')], 'jeep-38-v6': [('oil_use', 'oil consumption')], 'gm-48-vortec': [('oil_use', 'oil consumption')],
                'ford-54-triton': [('cam_phaser', 'cam phasers'), ('spark_plug', 'broken or ejected spark plugs')], 'ford-ecoboost-23': [('coolant', 'coolant loss')]}
    _VPEERS = f'{len(VEE)} everyday engines we track'
    _VOTH = f'other {len(VEE) - 1} everyday engines we track'
    VE_TRUCKS = {'gm-53-gen5', 'gm-53-gen4', 'gm-62-gen5', 'gm-48-vortec', 'gm-27-turbo', 'chrysler-57-hemi', 'ram-30-ecodiesel', 'ford-54-triton', 'toyota-3ur-fe', 'toyota-1gr-fe'}   # the 'Trucks & diesel' tab on /engines/
    def _v_known(e, h2=True):
        ok, no = [], []
        for k, what in VE_KNOWN.get(e, []):
            s, n, N, p, m = _v_sup(e, k)
            (ok if s else no).append((k, what, n, N, p, m))
        h = ''
        if ok:
            h += ('<ul class="hd-ki">' + ''.join(f'<li><b>{E(what[:1].upper() + what[1:])}.</b> {n:,} of {N:,} owner complaints ({_v_fmt(p)}%) {E(_VWL.get(k, k))}, against a median of {_v_fmt(m)}% for the {_VOTH}.'
                                              + ''.join(f'<blockquote><p>{E(_vsc(q["text"]))}</p><cite>{q["y"]} owner · NHTSA complaint {q["odi"]}</cite></blockquote>' for q in (VEE[e].get('wq') or {}).get(k, [])[:1] if k != 'fire') + '</li>' for k, what, n, N, p, m in ok) + '</ul>')
        if no:
            h += ('<p class="note">Also often talked about, but <b>not</b> standing out in complaints to NHTSA: ' + '; '.join(f'{E(what)} ({n:,} of {N:,}, {_v_fmt(p)}%, peers {_v_fmt(m)}%)' for k, what, n, N, p, m in no)
                  + '. That doesn&#39;t mean it never happens, only that owners rarely file it with the government.</p>')
        if not h: return ''
        return ((f'<section class="yc engk hd-k" id="known"><h2>Known issues, checked against owner complaints</h2>' if h2 else '<div class="engk hd-k"><h3>Known issues, checked against owner complaints</h3>')
                + (f'<p>Problems owners of cars with this engine name much more often than owners of the {_VOTH} (at least 1.5× the median, and 10+ complaints):</p>' if ok else
                   '<p>None of the issues people usually talk about stands out in this engine&#39;s complaints to NHTSA.</p>') + h + ('</section>' if h2 else '</div>'))
    def _v_years_chart(e):
        d = VEE[e]; mx = max([1] + list(d['by_year'].values()))
        def cars(y): return ', '.join(_vcar(f).split(' ', 1)[-1] for f, c in d['by_car'].items() if str(y) in c['years'])
        rows = ''.join(f'<div class="egr"><span class="egy">{y}<small>{E(cars(y))}</small></span><span class="eg-o"><i style="width:{n / mx * 100:.0f}%"></i></span><b>{n:,}</b></div>'
                       for y, n in sorted(d['by_year'].items()))
        return ('<div class="egc sce1"><div class="egh" aria-hidden="true"><span>Model year</span><span>Owner complaints <em>count, any part of the car, VIN-matched to this engine</em></span></div>' + rows + '</div>')
    def _v_cars_table(e):
        d = VEE[e]; R = []
        for f, c in sorted(d['by_car'].items(), key=lambda kv: -kv[1]['n']):
            ys = sorted(int(y) for y in c['years']); span = f'{ys[0]}–{str(ys[-1])[-2:]}' if len(ys) > 1 else str(ys[0])
            R.append([f'<a href="{CARU(_VM[f])}">{E(_vcar(f))}</a>' if f in _VM else E(f), span, f'{c["n"]:,}', f'{c["eng"]}%'])
        return _v_rows(['Car', 'Model years matched', 'Complaints', 'Name the engine'], R)
    def _v_rank(e): return sorted(VEE, key=lambda o: -_v_share(VEE[o]['comps'], 'engine')).index(e) + 1
    def _v_cmp(cur):
        R = []
        for o in sorted(VEE, key=lambda o: -_v_share(VEE[o]['comps'], 'engine')):
            d = VEE[o]; nm = f'<b>{_vE(d["short"])}</b>' if o == cur else f'<a href="{VE_URL[o]}">{_vE(d["short"])}</a>'
            R.append([nm, f'{d["years"][0]}–{str(d["years"][-1])[-2:]}', f'{d["n"]:,}', f'{_v_share(d["comps"], "engine")}%', f'{_v_fmt(_v_w(o, "power_loss")[2])}%',
                      f'{_v_fmt(_v_w(o, "oil_use")[2])}%', str(len(d['recalls']))])
        return _v_rows(['Engine', 'Years', 'Complaints', 'Name the engine', 'Stalled or lost power', 'Burning oil', 'Recalls naming it'], R)
    def _v_words(e):
        R = []
        for k, lab in _VW.items():
            n, N, p = _v_w(e, k); m = _v_med(e, k)
            if n < 5: continue
            R.append((p, [E(lab[:1].upper() + lab[1:]), f'{n:,}', f'{_v_fmt(p)}%', f'{_v_fmt(m)}%']))
        R.sort(key=lambda r: -r[0])
        if not R: return ''
        return (f'<section class="yc" id="words"><h2>What owners write</h2>' + _v_rows(['Complaints that', 'Count', 'Share', 'Median, other everyday engines'], [r for _, r in R[:10]])
                + '<p class="yc-cap">Counted from the owner&#39;s own words in each complaint (all of the car, not only the engine). A share, not a failure rate.</p></section>')
    def _v_recs(e):
        rr = [VER[i] for i in VEE[e]['recalls'] if i in VER]
        return (f'<section class="yc sce-r" id="recalls"><h2>Recalls that name this engine <span class="yc-n">{len(rr)}</span></h2>'
                + ('<ul class="advr">' + ''.join(_v_rec_li(r) for r in rr[:6]) + '</ul>' + (f'<details class="cpd"><summary>Show all {len(rr)}</summary><ul class="advr">' + ''.join(_v_rec_li(r) for r in rr[6:]) + '</ul></details>' if len(rr) > 6 else '')
                   if rr else '<p>No NHTSA recall on these cars and years names this engine.</p>')
                + '<p class="yc-cap">NHTSA recalls on these cars and model years whose text names this engine (its size or name). The rest (brakes, air bags, wiring ...) are on each car year&#39;s page.</p></section>'), rr
    def _v_carnames(e, n=None):
        cs = [_vcar(f) for f, _ in sorted(VEE[e]['by_car'].items(), key=lambda kv: -kv[1]['n'])]
        return cs if n is None else cs[:n]
    def _v_list(xs): return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]

    # ---- YouTube owner tone (11-13, Elijah: "every engine page should have a YouTube score"): the studies in 3 Lemon Index/data/yt/
    # engine_studies_vin.py, pulled and scored by auto_gens.py into data/supercar_engine_yt.json (same scoring as the supercar engines).
    # VE_YT: study id -> engine page; VE_YTAVG: page -> average tone over the engine's own model years (joins ENG_POOL in supercar_engine_pages.py)
    _VSY = _load('data/supercar_engine_yt.json') if _vos.path.exists('data/supercar_engine_yt.json') else {}
    VE_YT = {e: u for e, u in VE_URL.items() if not VEE[e].get('page')}
    VE_YT.update({k: f'/engines/{k}/' for k in ('ford-powerstroke-73', 'ford-powerstroke-60', 'ford-powerstroke-64', 'ford-powerstroke-67', 'cummins-59', 'cummins-67', 'duramax-lb7',
                                                 'duramax-lly', 'duramax-lbz', 'duramax-lmm', 'duramax-lml', 'duramax-l5p', 'ford-ecoboost-27', 'subaru-fa24f', 'vw-ea888')})
    VE_YTAVG, VE_YTD = {}, {}
    for _k, _u in VE_YT.items():
        _ys = (_VSY.get(_k) or {}).get('years') or {}
        _v = [d['score'] for d in _ys.values() if d and d.get('score') is not None]
        if _v: VE_YTAVG[_u] = sum(_v) / len(_v); VE_YTD[_u] = _VSY[_k]
    def VE_YT_SEC(url):
        """the YouTube owner tone section for an engine page (empty until its study is pulled and scored)"""
        d = VE_YTD.get(url)
        if not d: return ''
        ys = {y: v for y, v in d['years'].items() if v.get('score') is not None}
        rk = (globals().get('ENG_POOL_RANK') or {}).get(url); n = globals().get('ENG_POOL_N')
        vids = {}
        for v in d['years'].values():
            for t in v.get('top') or []: vids.setdefault(t['id'], t)
        top = sorted(vids.values(), key=lambda t: -(t.get('views') or 0))[:5]
        rows = ''.join(f'<div class="egr"><span class="egy">{y}</span><span class="eg-t"><i style="width:{v["score"]}%"></i></span><b>{v["score"]}</b></div>' for y, v in sorted(ys.items()))
        return (f'<section class="yc" id="youtube"><h2>What YouTube owners say <span class="h2s">Tone 0-100, higher = more praise than trouble.</span></h2>'
                f'<p>Average owner tone <b>{VE_YTAVG[url]:.0f}/100</b> across {len(ys)} model year{"" if len(ys) == 1 else "s"}, from {d.get("videos", 0):,} videos about this engine and its cars'
                + (f' (#{rk} of {n} engines with a YouTube study)' if rk and n else '') + '.</p>'
                + (f'<div class="egc sce1"><div class="egh" aria-hidden="true"><span>Model year</span><span>YouTube tone <em>0-100, higher = better</em></span></div>{rows}</div>' if rows else '')
                + ('<h3>Most-watched videos</h3><ul>' + ''.join(f'<li><a href="https://www.youtube.com/watch?v={E(t["id"])}" target="_blank" rel="noopener nofollow">{E(t["title"])}</a> <small>{(t.get("views") or 0):,} views</small></li>' for t in top) + '</ul>' if top else '')
                + '<p class="yc-cap">Counted from video titles and captions: praise words against trouble words, weighted by views. Videos only count when the title names this engine or a car that had only this engine in those years.</p></section>')
    # ------------------------------------------------------------------ a page for each engine without one
    def _v_page(e):
        d = VEE[e]; nm = d['name']; path = VE_URL[e]; ys = d['years']; y0, y1 = ys[0], ys[-1]
        es = _v_share(d['comps'], 'engine'); rank = _v_rank(e); cars = _v_carnames(e)
        ans1 = (f'The {E(d["lay"])} in the {E(_v_list(cars))}, model years {y0}–{y1}. Owners filed <b>{d["n"]:,} complaints</b> about cars with it (matched by VIN); '
                f'<b>{es}%</b> name the engine, #{rank} of the {_VPEERS} (1 = the most).')
        rsec, rr = _v_recs(e)
        chips = (f'<div class="trc"><div><b>{y0}–{str(y1)[-2:]}</b><span>model years</span></div><div><b>{d["n"]:,}</b><span>owner complaints</span></div>'
                 f'<div><b>{es}%</b><span>name the engine</span></div><div><b>{len(rr)}</b><span>recalls name it</span></div></div>')
        sec = [_v_known(e), VE_YT_SEC(path), (globals().get('EU_CARS_HTML') or (lambda *a: ''))(path, 'Cars with this engine')]
        sec.append('<h2>Owner complaints by model year</h2>' + _v_years_chart(e)
                   + '<p class="note">Counts of complaints filed so far. Older cars have had longer to collect them, and popular cars draw more because more were sold: '
                     'no one reports sales by engine, so there&#39;s no per-car rate. Compare the shares below instead.</p>')
        sec.append(f'<section class="yc" id="bycar"><h2>By car</h2>{_v_cars_table(e)}<p class="yc-cap">&ldquo;Name the engine&rdquo; = the share of that car&#39;s VIN-matched complaints that list the engine as a problem area.</p></section>')
        sec.append(f'<section class="yc" id="problems"><h2>What owners complain about</h2>' + _v_bars([(p, k) for p, k, _ in d['comps']]) + '<p class="yc-cap">Share of this engine&#39;s complaints that name each area (one complaint can name several).</p></section>')
        sec.append(_v_words(e))
        if d.get('miles'): sec.append(f'<section class="yc" id="mileage"><h2>When problems show up</h2><p>{_v_miles(d["miles"])}</p></section>')
        sec.append(rsec)
        if d.get('quotes'): sec.append(f'<section class="yc"><h2>In owners&#39; words</h2>' + ''.join(f'<blockquote><p>{E(_vsc(q["text"]))}</p><cite>{q["y"]} owner · NHTSA complaint {q["odi"]}</cite></blockquote>' for q in d['quotes']) + '</section>')
        sec.append(f'<section class="yc" id="compare"><h2>Against the other everyday engines</h2>' + _v_cmp(e)
                   + '<p class="yc-cap">Shares of each engine&#39;s own complaints, matched by VIN. They show what owners complain about, not how often engines break.</p></section>')
        top3 = ', '.join(p for p, _, _ in d['comps'][:3])
        sup = [(k, w) + _v_sup(e, k)[1:] for k, w in VE_KNOWN.get(e, []) if _v_sup(e, k)[0]][:2]
        faq = [(f'Is the {nm} reliable?', f'No one reports sales by engine, so there&#39;s no per-car score. Of the {d["n"]:,} complaints owners filed about cars with it, {es}% name the engine, #{rank} of the {_VPEERS} (1 = the most).'
                + (' ' + ' '.join(f'{n:,} ({_v_fmt(p)}%) {_VWL.get(k, k)}, against {_v_fmt(m)}% for the other engines.' for k, w, n, N, p, m in sup) if sup else '')),
               (f'What cars have the {nm}?', f'In our data: the {_v_list(cars)}, model years {y0}–{y1}, matched by the VIN in each owner complaint.'),
               (f'What are the most common {d["short"]} problems?', f'In owner complaints to the government: {top3}.'),
               (f'How many recalls name the {d["short"]}?', f'{len(rr)} NHTSA recall{"" if len(rr) == 1 else "s"} on these cars name{"s" if len(rr) == 1 else ""} it.')]
        sec.append('<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(_vh.unescape(q))}</h3><p>{E(_vh.unescape(a))}</p>' for q, a in faq)) + '</section>')
        body = (f'<article class="study tr2 eng2 hde"><p class="kicker"><a href="/engines/">Every engine</a>{" · <a href=\"/engines/?type=trucks\">Trucks &amp; diesel engines</a>" if e in VE_TRUCKS else ""}</p>'
                f'<h1>{E(nm)} reliability by year</h1><p class="tra">{ans1} '
                f'<button type="button" class="shl" data-share="{E(f"{nm}: owner complaints by year, matched by VIN. Free:")}">Share ↗</button></p>{chips}'
                + ''.join(x for x in sec if x) + f'<p class="yc-cap">{_VHOW} Source: {E(_VSRC.get("complaints", "NHTSA"))}; engines: {E(_VSRC.get("vin", ""))}; {E(_VSRC.get("recalls", ""))}. '
                f'Engine names and model years: {E(d["maker"])}.</p></article>')
        title = f'{_vh.unescape(nm)} Problems & Reliability by Year'
        desc = (f'{_vh.unescape(nm)} ({d["lay"]}), {y0}-{y1}: {d["n"]:,} owner complaints matched by VIN in the {", ".join(cars[:4])}{" and more" if len(cars) > 4 else ""}, {es}% name the engine. '
                f'Problems by year and {len(rr)} recalls that name it.')
        page(path, title, desc, body, ld=[faq_ld([(q, '', _vh.unescape(a)) for q, a in faq])] + aie_ld(path), vis=aie_vis(path, _vh.unescape(nm), d['lay']))
        VE_URLS.append(path)
        al = (d.get('alias') or '') + ' ' + d['lay'].split(' ')[0].replace('.', '')
        mk = {'GM': 'Chevrolet'}.get(d['maker'], d['maker'])
        VE_AE.append(dict(url=path, name=nm, code=d['code'], lay=d['lay'], yrs=f'{y0}–{str(y1)[-2:]}', img=None, yt=(None, 0, ''), used=[],   # all_engines.py fills it from ENGINE_USES (the cars' own short names, mainstream first)
                         
                          t=({'t'} if e in VE_TRUCKS else set()) | ({'h'} if d['maker'] == 'Honda' else set()),
                          f=d['fuel'], mk=mk, o=(0.5, -d['n']), alias=al))
    # ------------------------------------------------------------------ engines whose page already exists: sections to add to it
    def VE_SCE(path):
        out = []
        for e, d in VEE.items():
            if VE_URL[e] != path or not d.get('page'): continue
            es = _v_share(d['comps'], 'engine'); rank = _v_rank(e); cars = _v_carnames(e); rsec, rr = _v_recs(e)
            out.append(f'<section class="yc" id="vin"><h2>In everyday cars, matched by VIN</h2><p>Owners filed <b>{d["n"]:,} complaints</b> about the {E(_v_list(cars))} with the {E(d["short"])} '
                       f'(model years {d["years"][0]}–{d["years"][-1]}, engine read from each complaint&#39;s VIN). <b>{es}%</b> name the engine, #{rank} of the {_VPEERS} (1 = the most).</p>'
                       + _v_known(e, False) + _v_cars_table(e) + '<h3>Owner complaints by model year</h3>' + _v_years_chart(e)
                       + '<h3>What owners complain about</h3>' + _v_bars([(p, k) for p, k, _ in d['comps'][:6]])
                       + (f'<details class="cpd"><summary>{len(rr)} recall{"" if len(rr) == 1 else "s"} on these cars name{"s" if len(rr) == 1 else ""} the engine</summary><ul class="advr">' + ''.join(_v_rec_li(r) for r in rr) + '</ul></details>' if rr else '')
                       + '<h3>Against the other everyday engines</h3>' + _v_cmp(e)
                       + f'<p class="yc-cap">Counts and shares, not failure rates: no one reports sales by engine. {_VHOW} Source: {E(_VSRC.get("complaints", "NHTSA"))}; engines: {E(_VSRC.get("vin", ""))}.</p></section>')
        return out
if VEX == 'pages' and VEE:
    for _e, _d in VEE.items():
        if not _d.get('page'): _v_page(_e)
    # /cars/ models whose coming-soon engine card these pages replace: (model id) -> {"3.5L 6-cyl", ...} (EPA's size + cylinders)
    for _e, _d in VEE.items():
        _m = _vre.match(r'(\d\.\d) L (?:V(\d+)|inline-(\d)|flat-(\d))', _d['lay'])
        if not _m: continue
        for _fid in _d['by_car']: VE_COVER.setdefault(_fid, set()).add((f'{_m.group(1)}L {next(g for g in _m.groups()[1:] if g)}-cylinder', _d['fuel']))
    print('vin engine pages:', len(VE_URLS), 'new,', sum(1 for d in VEE.values() if d.get('page')), 'added to existing pages |', len(VEJ.get('held') or {}), 'held (not enough VIN-matched complaints)')
