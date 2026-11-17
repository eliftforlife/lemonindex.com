# 11-17 F-150 split (REQUESTED CARS BRIEF 11-15): /cars/ford-f-series/ is the F-150's page, but it scored the whole F-Series family, and in
# some model years most of its complaints were F-250/F-350 Super Duty trucks (2019: 84%, 2017: 78%). The Super Duty has its own page
# (/cars/ford-super-duty/, hd_pages.py). Now the F-150 pages count the F-150's own NHTSA names only (data/f150_split.json, data_f150_split.py),
# and they carry no Lemon Index: Ford reports F-150 and Super Duty U.S. sales together as "F-Series", so there is no F-150-only sales figure.
# The study's whole-line "Ford F-Series" row (data/family_rates.csv) stays in the study ranking; the F-150 page says it isn't an F-150 score.
# Run by build.py with exec() in phases (everything build.py defines is in scope):
#   FSX = 'years'   right after data/years*.json load: the F-150's years become complaints-only (low.why = 'fseries')
#   FSX = 'extras'  after XL (extras_local) loads: F-150-only mileage, severity and NHTSA names
#   FSX = 'pages'   before the model/year page loop: FS_IDS (skipped by that loop), FS_PAGES(f) builds the model + year pages, FS_BARS
import json as _fj, os as _fos
if FSX == 'years':
    FS = _fj.load(open('data/f150_split.json', encoding='utf-8')) if _fos.path.exists('data/f150_split.json') else None
    FS_IDS = {'ford-f-series'} if FS else set()
    FS_WHY = 'Ford reports F-150 and Super Duty sales together as one F-Series number (there is no F-150-only sales figure)'
    FS_CO = lambda v: (v.get('low') or {}).get('why') == 'fseries'
    for _f in _YJ:
        if _f['id'] not in FS_IDS: continue
        for _v in _f['years']:
            _a = FS['years'].get(str(_v['y'])) or {}
            _v.update(li=None, sold=None, n=_a.get('n', 0), parts=_a.get('parts') or [], quotes=_a.get('quotes') or [], low=dict(sold=None, url='', kind='none', why='fseries'))
            _v.pop('early', None)
elif FSX == 'extras':
    for _fid in FS_IDS:
        XL[_fid] = {y: e for y, e in FS['extras'].items()}
elif FSX == 'pages':
    SN['ford-f-series'] = ('Ford F-150', 'F-150 complaints only (NHTSA files them as F-150 and F-150 Hybrid). The F-250/F-350 Super Duty has '
                           '<a href="/cars/ford-super-duty/">its own page</a>, and the F-150 Lightning has <a href="/electric/ford-f-150-lightning/">its EV page</a>.')
    HD_FAM.pop('ford-f-series', None)   # no half-ton banner or "whole line" caveat: these pages are F-150 only now
    _FS_SD = lambda y=None: (f'/cars/ford-super-duty/{y}/' if y and _hd_has('ford-super-duty', y) else '/cars/ford-super-duty/')
    def FS_BARS(f, cur=None):
        """Every year: the F-150's own complaint count (a count, not per truck sold) and the YouTube rank, like the complaints-only pages."""
        ys = sorted((v for v in f['years']), key=lambda v: -v['y']); mx = max([1] + [v['n'] for v in ys])
        sc = YTS.get(f['id']) or {}
        okr = {int(y) for y, s in sc.items() if s.get('score') is not None and (s.get('videos') or 0) >= YT_MIN and (int(y) < 2010 or any(v['y'] == int(y) and v['n'] for v in ys))}
        got = sorted(((sc[str(y)]['score'], sc[str(y)]['videos'], y) for y in okr), reverse=True); RK = {y: i + 1 for i, (_, _, y) in enumerate(got)}
        lo, hi = (got[-1][0], got[0][0]) if got else (0, 1)
        def row(v):
            y = v['y']; rk = RK.get(y); s = sc.get(str(y)) or {}
            w = 8 + 92 * (s['score'] - lo) / max(1, hi - lo) if rk else 0; tier = '' if rk is None else (' up' if rk <= len(RK) / 3 else ' dn' if rk > len(RK) * 2 / 3 else '')
            yt = (f'<span class="bt ytb{tier}"><i style="width:{w:.0f}%"></i></span><b class="ytn" title="YouTube rank {rk} of {len(RK)} F-150 years">#{rk}</b>' if rk else '<span class="bt ytb"></span><b class="ytn mute">·</b>')
            tip = (f'{y} Ford F-150: {v["n"]:,} owner complaints in its first 3 years (a count, not per truck sold)'
                   + (f'. YouTube rank #{rk} of {len(RK)} (score {s["score"]}, {s["videos"]:g} videos)' if rk else '. Not enough YouTube videos to rank'))
            return (f'<a class="b na{" cur" if y == cur else ""}" href="{CARU(f, y)}" data-tip="{E(tip)}."><span class="bn">{y}</span><span class="bt"><i style="width:{100 * v["n"] / mx:.1f}%"></i></span>'
                    f'<b>{v["n"]:,}</b>{yt}</a>')
        return (f'<div class="bars yb yt2"><div class="bl yth2" aria-hidden="true"><span></span><span>Complaints <em>a count, first 3 years</em></span><span></span><span>YouTube rank <em>#1 = favorite</em></span><span></span></div>'
                + ''.join(row(v) for v in ys) + '</div>'
                + '<p class="yc-cap lfa-leg">Newest year first. Complaints = F-150 owner complaints filed with NHTSA in each model year&#39;s first 3 years. It is a count, not a rate: '
                  'years that sold more draw more, and Ford doesn&#39;t report F-150 sales on their own, so we can&#39;t turn it into a per-truck score.'
                + (f' <b>#1, #2…</b> = that year&#39;s YouTube rank among the {len(RK)} F-150 years with enough videos (#1 = the year owners and reviewers talk about most positively). It is not a reliability rank.' if RK else '') + '</p>')
    def FS_PAGES(f):
        c = BYNAME[f['name']]; ys = f['years']; snm = SNM(f); qn = QN(f)
        tot = sum(v['n'] for v in ys if 2010 <= v['y'] <= 2022)
        _pt = defaultdict(float)
        for v in ys:
            for _p, _k in v['parts']: _pt[_p] += _k * v['n'] / 100
        tp = [NICE(x) for x, _ in sorted(_pt.items(), key=lambda kv: -kv[1])[:3]]
        sd_tot = sum((FS['years'].get(str(y)) or {}).get('n_sd', 0) for y in range(2010, 2023)); fam_tot = sum((FS['years'].get(str(y)) or {}).get('n_fam', 0) for y in range(2010, 2023))
        r = YTR.get(f['id'])
        ans = (f'We can&#39;t give the F-150 a Lemon Index: {FS_WHY}, and a score needs complaints per truck sold. What we can show is the F-150&#39;s own owner complaints: '
               f'{tot:,} filed with NHTSA in the first 3 years of model years 2010–2022, most often about {", ".join(tp[:-1])} and {tp[-1]}.' if len(tp) > 1 else '')
        note = (f'<p class="yc-note">{SN[f["id"]][1]} Until November 2026 this page counted the whole F-Series family, and {round(100 * sd_tot / max(1, fam_tot))}% of those 2010–2022 '
                f'complaints were Super Duty trucks (2019: {round(100 * FS["years"]["2019"]["n_sd"] / FS["years"]["2019"]["n_fam"])}%). Our study&#39;s Ford F-Series score '
                f'(Lemon Index {c["li"]}, {c["years"].replace("-", "–")}) still counts the whole line, F-150 and Super Duty together; it is not an F-150 score.</p>')
        tiles = [f'<div class="rs"><small>Owner complaints</small><b>{tot:,}</b><span>F-150 only · first 3 years · 2010–2022</span></div>']
        if r:
            rk, n, vids = r; cl = 'good' if rk <= n / 3 else 'bad' if rk > n * 2 / 3 else 'mid'
            tiles.append(f'<div class="rs {cl}"><small>YouTube owners</small><b>#{rk} <i>of {n}</i></b><span>vs. cars the same age · {vids:,} videos</span></div>')
        tiles.append(f'<a class="rs" href="/cars/ford-super-duty/"><small>F-250 / F-350</small><b>Super Duty</b><span>its own page, by year and engine</span></a>')
        rel_tiles = f'<div class="rsc">{"".join(tiles)}</div>'
        def yx(v):
            xx = yearx(f['id'], v['y']); m = xx.get('mpg'); sf = xx.get('safety')
            return (f'<td class="num">{len(xx["recalls"]) if "recalls" in xx else "—"}</td><td>{stars(sf["best"]) if sf and sf.get("best") else "—"}</td>'
                    f'<td class="num">{(f"{m["comb"][0]}–{m["comb"][1]}" if m["comb"][0] != m["comb"][1] else m["comb"][0]) if m else "—"}</td>')
        rows = ''.join(f'<tr><td><a href="{CARU(f, v["y"])}">{v["y"]}</a></td><td class="num">{v["n"]:,}</td><td>{E(v["parts"][0][0]) + f" ({v["parts"][0][1]}%)" if v["parts"] else "—"}</td>{yx(v)}</tr>' for v in ys)
        mqa = [(f'Is the {snm} reliable?', f'We can&#39;t score it per truck sold: {FS_WHY}. The F-150&#39;s own owner complaints are on every year&#39;s page: {tot:,} in the first 3 years of model years 2010–2022.'),
               (f'What are the best {snm} years to buy?', 'We don&#39;t rank F-150 years by complaints: without F-150 sales, a year that sold more would look worse just for selling more. '
                + ('Each year&#39;s YouTube rank (how positively owners and reviewers talk about it) is in the chart above.' if r else 'Each year&#39;s page lists its own problems and recalls.')),
               (f'Does the F-150 score include the F-250 and F-350?', 'No. These pages count only complaints NHTSA files as F-150 or F-150 Hybrid. The F-250/F-350 Super Duty has '
                '<a href="/cars/ford-super-duty/">its own page</a> with its complaints by year and engine.')]
        _rc = [(v['y'], len(extra(f['id'], v['y']).get('recalls') or [])) for v in ys if 'recalls' in extra(f['id'], v['y'])]
        if _rc and sum(n for _, n in _rc):
            _top = sorted(_rc, key=lambda t: -t[1])[:3]
            mqa.append((f'How many recalls does the {snm} have?', f'{sum(n for _, n in _rc)} safety recalls across the {len(_rc)} model years we track. Most: ' + ', '.join(f'{y} ({n})' for y, n in _top if n) + '. Each year&#39;s page lists them.'))
        if tp: mqa.append((f'What are the most common {snm} problems?', f'Across every year, F-150 owners&#39; complaints to the government name {", ".join(tp[:-1])} and {tp[-1]} most.'))
        model_qa_html = '<section class="yqa"><h2>Quick answers.</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{a}</p>' for q, a in mqa)) + '</section>'
        hero_img = (YSL.year_slider_html(f['id'], f['name'], {}, {y: sc_ for y, sc_ in YSL.yt_scores(f['id']).items()}, {v['y'] for v in ys}, start=popular_year(f), best=None, hero=True, mli=None, early=set())
                    if YSL.has(f['id']) else (YSL.model_hero_html(f['id'], f['name']) or car_hero(f, ys[-1]['y'])))
        page(CARU(f), seo_title([f'{qn} Reliability: Problems & Recalls by Year', f'{qn} Reliability by Year', f'{qn} Reliability']),
             f'{qn} reliability: {tot:,} F-150 owner complaints to NHTSA (model years 2010–2022, first 3 years), most about {tp[0] if tp else "steering"}. Problems and recalls for every year.', f'''
<div class="pg mp6"><section class="ph yph6"><div class="yh-t">{N2_CRUMB(f)}<h1 class="rel-h">{E(qn).replace("-", "-⁠")} reliability.</h1><p class="ans rel-a"><b>Is it reliable?</b> {ans}</p>{note}{PIN_HTML(f['id'])}
<p><button type="button" class="btn btn-ghost" data-share="{E(f'Every {snm} year: owner complaints, problems and recalls. Free report:')}">Share ↗</button></p></div><div class="ph-v">{hero_img}{rel_tiles}</div></section>
<section class="yyears noph" id="years"><div class="yy-ch"><h2>Every year. <span class="h2s">Tap a year for its full report.</span></h2>{FS_BARS(f)}</div></section>
{ytfix("model:" + f["id"])}{gas_hybrid_html(f)}{SPECS_HOOK(f["id"])}{N2_CMP(f)}
{model_qa_html}
<section><details class="yd"><summary>Every year in one table</summary><div class="tw"><table><thead><tr><th>Year</th><th>Complaints (first 3 years)</th><th>Top complaint</th><th>Recalls</th><th>Crash test</th><th>MPG</th></tr></thead><tbody>{rows}</tbody></table></div></details>
<p class="yc-cap">Complaints: NHTSA owner complaints filed as F-150 or F-150 Hybrid within 3 years of the model year. No Lemon Index here, because {FS_WHY}. A complaint is an owner&#39;s report, not a confirmed defect. <a href="/method/">How it works</a></p>{f'<p><a class="btn" href="{CARU(f)}transmission/">{E(snm)} transmission problems by year →</a></p>' if _tr_ok(f) else ''}</section>{share_line(f'Every {snm} year: owner complaints, problems and recalls. Free report:')}</div>''',
             ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{snm} reliability by year', "url": BASE + CARU(f)},
                 faq_ld([(q, '', html.unescape(re.sub('<[^>]+>', '', a))) for q, a in mqa]), car_ld(f, img=YSL.ai_src(f['id'], ys[-1]['y']) or (mphoto(f['id']) or {}).get('src'))])
        yurls.append(CARU(f))
        best = worst = None
        for i, v in enumerate(ys):
            y = v['y']; prev, nxt = (ys[i - 1] if i else None), (ys[i + 1] if i + 1 < len(ys) else None)
            top = ', '.join(f'{p} {k}%' for p, k in v['parts'][:2])
            x = extra(f['id'], y); nrec = len(x['recalls']) if 'recalls' in x else None
            qa = year_faq(f, v, y, x, best)
            _sd = (FS['years'].get(str(y)) or {}).get('n_sd', 0)
            if _sd: qa.insert(1, (f'Does this include the {y} F-250 and F-350?', f'No. These are the {v["n"]:,} complaints NHTSA files as F-150 or F-150 Hybrid. The {y} Super Duty drew {_sd:,} of its own in its first 3 years; they are on <a href="{_FS_SD(y)}">its own page</a>.',
                                  f'No. These are the {v["n"]:,} complaints NHTSA files as F-150 or F-150 Hybrid. The {y} Super Duty drew {_sd:,} of its own in its first 3 years; they are on its own page.'))
            _yw = YW(f); _yo = 'Reliability' if _yw == 'Problems' else 'Problems'; _yb = f'{y} {qn} {_yw}'
            _ni = YSL.no_img(f['id'], y); _mimg = None if _ni else YSL.model_img(f['id']); _ph = {} if _ni else PH.get(f['id'], {})
            _img = YSL.ai_src(f['id'], y) or (_mimg or {}).get('src') or (_ph.get(str(y)) or {}).get('src')
            page(CARU(f, y), seo_title([f'{_yb}, {_yo} & Recalls', f'{_yb} & {_yo}', f'{_yb} & Recalls', _yb]),
                 f'Owners filed {v["n"]:,} NHTSA complaints about the {y} {snm} in its first 3 years (F-150 only).' + (f' {nrec} recall{"s" if nrec != 1 else ""}.' if nrec else '') + (f' Top problems: {top}.' if top else '') + ' Real owner complaints and every other year.',
                 year_body(f, v, y, x, best, worst, prev, nxt, v['quotes'], qa), kind='article', ask=(f['id'], y, f'{y} {snm}'), img=_img,
                 ld=[car_ld(f, y, x.get('mpg'), _img), {"@context": "https://schema.org", "@type": "WebPage", "name": f'{y} {snm} problems, reliability and recalls', "url": BASE + CARU(f, y)}
                     | ({"primaryImageOfPage": {"@type": "ImageObject", "contentUrl": BASE + _img, "license": YSL.LIC, "acquireLicensePage": BASE + '/images/', "creditText": "The Lemon Index"}} if _img and (YSL.ai_src(f['id'], y) or _mimg) else {})]
                    + ([faq_ld(qa)] if qa else []))
            yurls.append(CARU(f, y))
