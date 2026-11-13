# 11-12 customer UX test fixes, part C (3 Lemon Index/UX test 11-12/FIX LIST.md: Compare, the Tesla/EV gaps, data downloads and press).
# Run by build.py with exec() in phases, so everything build.py defines is in scope:
#   UXC = 'hooks'    (before the model/year pages): battery-fire recall banners, the RAV4 Hybrid sections, sales-source links, the EV pages'
#                    YouTube block, and the data-file / chart helpers the /data/ page calls
#   UXC = 'compare'  (replaces the old /compare/ hub): performance side-by-side pages from data/perf/*.json + the hub ("Compare up to 4 cars")
#   UXC = 'data'     (last): docs/assets/compare.json for the compare tool (every model, EV, performance car and supercar) and the
#                    "Embed this chart" blocks on /rankings/ and /stats/car-complaints/
# No new score anywhere: every number is one the site already publishes (main Lemon Index, EV-page score, NHTSA counts, EPA, perf specs).
import json as _json, os as _os, re as _re, html as _html

if UXC == 'hooks':
    _EVJ = _json.load(open('data/ev.json', encoding='utf-8'))
    _EVS = {c['slug']: c for c in _EVJ['cars']}
    RAV4H = _load('data/rav4_hybrid.json')
    SALES_SRC = _load('data/sales_sources.json')

    # ---- battery-fire recalls (Dan: "the Bolt's battery recall shows up as an ordinary electrical card"): any EV recall on the high-voltage
    # (traction) battery whose summary or risk mentions fire gets a pinned banner on the model page, the year pages it covers and the EV page
    def _bf(r): return 'TRACTION BATTERY' in (r.get('part') or '').upper() and _re.search(r'\bfire\b', (r.get('summary') or '') + ' ' + (r.get('risk') or ''), _re.I)
    def _ryears(s):
        m = _re.search(r'(?:certain|all)\s+((?:(?:19|20)\d\d(?:\s*-\s*(?:19|20)\d\d)?(?:,|\s+and|\s)*)+)', s or '')
        out = set()
        for a, b in _re.findall(r'((?:19|20)\d\d)(?:\s*-\s*((?:19|20)\d\d))?', m.group(1) if m else ''): out |= set(range(int(a), int(b or a) + 1))
        return out
    BATT = {}
    for _fid in list(_EVS) + [f['id'] for f in YEARS]:
        for _y, _d in (XA.get(_fid) or {}).items():
            for _r in (_d or {}).get('recalls') or []:
                if _bf(_r): BATT.setdefault(_fid, {}).setdefault(_r['id'], dict(_r, years=set()))['years'].add(int(_y))
    for _s, _c in _EVS.items():
        for _r in _c['recalls']:
            if _bf(_r): BATT.setdefault(_s, {}).setdefault(_r['id'], dict(_r, years=set()))['years'] |= _ryears(_r['summary'])
    _rk = lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2]
    def _span(ys): ys = sorted(ys); return '' if not ys else str(ys[0]) if ys[0] == ys[-1] else f'{ys[0]}–{ys[-1]}'
    # 11-12 round 2 (Ryan, Mitch, Carlos: a battery-fire banner on the F-Series model page and every CR-V): on a gas car's pages the banner
    # shows only on the year pages it covers, and names the version that has the battery (CR-V Hybrid, Escape plug-in hybrid ...); the
    # F-150 Lightning's recalls live on its own EV page (scope_filter.py takes them off the F-Series)
    def _trim(rs):
        s = ' '.join((r.get('summary') or '') for r in rs)
        for rx, lab in ((r'lightning', 'F-150 Lightning'), (r'plug-in hybrid|\bphev\b|\b4xe\b|energi', 'plug-in hybrid'), (r'hybrid', 'hybrid'), (r'battery electric|\bbev\b', 'electric')):
            if _re.search(rx, s, _re.I): return lab
        return ''
    def PIN_HTML(fid, y=None):
        ev = fid in _EVS
        if y is None and not ev: return ''
        rs = [r for r in (BATT.get(fid) or {}).values() if y is None or y in r['years']]
        if not rs: return ''
        rs.sort(key=_rk); ys = set().union(*[r['years'] for r in rs]); bolt = fid == 'chevrolet-bolt'
        tr = '' if ev else _trim(rs); nm = (FY.get(fid) or {}).get('name', '')
        tl = {'hybrid': 'Hybrid', 'plug-in hybrid': 'Plug-in Hybrid', 'electric': 'EV'}.get(tr, tr)
        ver = (f'{nm} {tl}' if not tr.startswith('F-150') else tr) if tr else f'{nm} versions with a high-voltage battery'
        head = ('Battery replacement recall (fire risk): check yours by VIN' if bolt else 'High-voltage battery recall (fire risk): check yours by VIN' if ev
                else f'{E(ver)} only: high-voltage battery recall (fire risk)')
        if bolt: what = (f'GM recalled the Bolt EV{" and Bolt EUV" if max(ys) >= 2022 else ""} ({_span(ys)}) because the high-voltage battery can catch fire. '
                         'The fix replaces the battery modules (on many cars the whole pack), free at any Chevy dealer. A used Bolt should have it done: ask for the paperwork.')
        elif ev: what = (f'{len(rs)} recall{"s" if len(rs) != 1 else ""} on this car&#39;s high-voltage battery mention{"" if len(rs) != 1 else "s"} a fire risk ({_span(ys)} model years). '
                         'The repair is free at any dealer if it&#39;s still open on the car.')
        else: what = (f'{len(rs)} recall{"s" if len(rs) != 1 else ""} on the high-voltage battery of the {y} {E(ver)} mention{"" if len(rs) != 1 else "s"} a fire risk. '
                      'Gas-only versions have no high-voltage battery, so this doesn&#39;t apply to them. The repair is free at any dealer if it&#39;s still open on the car.')
        ids = ' · '.join(f'<a href="https://www.nhtsa.gov/recalls?nhtsaId={E(r["id"])}" rel="noopener nofollow" target="_blank">{E(r["id"])}</a>' for r in rs)
        return (f'<div class="pinb" role="note"><p class="pinb-h"><b>{head}</b></p><p class="pinb-t">{what}</p>'
                f'<p class="pinb-l">NHTSA recall{"s" if len(rs) != 1 else ""}: {ids}</p><p class="pinb-a"><a class="btn" href="/vin/">Check a VIN</a> '
                f'<a href="https://www.nhtsa.gov/recalls" rel="noopener nofollow" target="_blank">NHTSA recall lookup</a></p></div>')

    # ---- RAV4 Hybrid (Dan: "rav4 hybrid" -> "No match"; the 2021 page showed one "2.5L 4-cyl" at 28-40 mpg): EPA splits the versions,
    # NHTSA doesn't, and the section says so
    _rng = lambda a: '—' if not a else f'{a[0]}' if a[0] == a[1] else f'{a[0]}–{a[1]}'
    _usd = lambda a: '—' if not a else f'${a[0]:,}' if a[0] == a[1] else f'${a[0]:,}–{a[1]:,}'
    RAV4H_NOTE = ('Owner complaints can&#39;t be split by version: owners file almost every RAV4 complaint with NHTSA under &quot;RAV4&quot;, whichever one they drive, '
                  'so the score and complaint counts cover the gas, Hybrid and Prime together.')
    def rav4h_year(fid, y):
        r = ((RAV4H or {}).get('years') or {}).get(str(y)) if fid == 'toyota-rav4' else None
        if not r: return ''
        rows = [('RAV4 (gas)', r.get('gas')), ('RAV4 Hybrid', r.get('hybrid')), ('RAV4 Prime (plug-in hybrid)', r.get('prime'))]
        tr = ''.join(f'<tr><td>{n}</td><td>{E(", ".join(v["engines"]) or "—")}</td><td class="num">{_rng(v["comb"])}' + (' on gas' if 'Prime' in n else '') + '</td>'
                     f'<td class="num">{_usd(v.get("cost"))}</td><td class="num">' + (f'{_rng(v["ev_miles"])} mi' if v.get('ev_miles') else '—') + '</td></tr>' for n, v in rows if v)
        nh = r.get('nhtsa') or {}
        named = (f' Of the {nh["all"]:,} complaints for the {y} RAV4 (all dates), {nh["filed_hybrid"]} were filed under &quot;RAV4 Hybrid&quot; by name'
                 + (f' and {nh["filed_prime"]} under &quot;RAV4 Prime&quot;' if nh.get('filed_prime') else '') + '.') if nh.get('all') else ''
        return (f'<section class="yc rav4h" id="hybrid"><h2>{y} RAV4 Hybrid. <span class="h2s">Gas vs hybrid' + (' vs plug-in' if r.get('prime') else '') + ', from the EPA.</span></h2>'
                f'<div class="tw"><table><thead><tr><th>Version</th><th>Engine</th><th>MPG combined</th><th>Fuel cost a year</th><th>Electric range</th></tr></thead><tbody>{tr}</tbody></table></div>'
                f'<p class="yc-cap">{RAV4H_NOTE}{named} Mileage and fuel cost: EPA (fueleconomy.gov).</p></section>')
    def rav4h_model(fid):
        ys = ((RAV4H or {}).get('years') or {}) if fid == 'toyota-rav4' else {}
        if not ys: return ''
        tr = ''.join(f'<tr><td><a href="{CARU(FY[fid], int(y))}">{y}</a></td><td class="num">{_rng((r.get("hybrid") or {}).get("comb"))}</td><td class="num">{_rng((r.get("gas") or {}).get("comb"))}</td>'
                     f'<td>{E(", ".join((r.get("hybrid") or {}).get("engines") or []) or "—")}</td></tr>' for y, r in sorted(ys.items(), reverse=True)) if fid in FY else ''
        return (f'<section class="yc rav4h" id="hybrid"><h2>RAV4 Hybrid, every year. <span class="h2s">The hybrid is a RAV4 version, so it shares these pages.</span></h2>'
                f'<div class="tw"><table><thead><tr><th>Year</th><th>Hybrid MPG</th><th>Gas MPG</th><th>Hybrid engine</th></tr></thead><tbody>{tr}</tbody></table></div>'
                f'<p class="yc-cap">{RAV4H_NOTE} Mileage: EPA (fueleconomy.gov).</p></section>')
    _YSH0, _SH0 = YEAR_SPECS_HOOK, SPECS_HOOK
    def YEAR_SPECS_HOOK(fid, y): return _YSH0(fid, y) + rav4h_year(fid, y)
    def SPECS_HOOK(fid): return _SH0(fid) + rav4h_model(fid)

    # ---- per-model sales source (Priya: "scores can't be reproduced: no per-model sales source")
    def SALES_SRC_HTML(f):
        us = (SALES_SRC or {}).get(f['id']) or []
        if not us: return ''
        dom = lambda u: _re.sub(r'^https?://(www\.)?', '', u).split('/')[0]
        return ' U.S. sales source' + ('s' if len(us) > 1 else '') + ': ' + ', '.join(f'<a href="{E(u)}" rel="nofollow noopener" target="_blank">{E(dom(u))}</a>' for u in us[:3]) + '.'

    # ---- the EV pages' YouTube block (Dan: "No owner/YouTube section on any /electric/ page"): the car pages' own block, when the model has one
    def EV_YT(slug, c):
        h = ytfix('model:' + slug)
        if not h:
            for y in sorted(_evyears(c), reverse=True):
                h = ytfix(slug, y)
                if h: break
        return h

    # ---- data files and embeddable charts (Priya: Teslas in the CSVs, model + EV CSVs, worst model-years, chart images with credit)
    CREDIT = 'Source: The Lemon Index (lemonindex.com), from NHTSA owner complaints. CC BY 4.0'
    WY0, WY1 = 2015, 2025
    def worst_years(n=None):
        rows = [(f, v) for f in YEARS for v in f['years'] if v['ok'] and WY0 <= v['y'] <= WY1]
        rows.sort(key=lambda t: (-t[1]['li'], t[0]['name'], t[1]['y']))
        return rows[:n] if n else rows
    def _font(sz, bold=False):
        from PIL import ImageFont
        for p in ((r'C:\Windows\Fonts\segoeuib.ttf' if bold else r'C:\Windows\Fonts\segoeui.ttf'), (r'C:\Windows\Fonts\arialbd.ttf' if bold else r'C:\Windows\Fonts\arial.ttf'),
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans' + ('-Bold' if bold else '') + '.ttf'):
            if _os.path.exists(p): return ImageFont.truetype(p, sz)
        return ImageFont.load_default()
    def CHARTS():
        """[(id, title, sub, [(label, value, cls)], note)]: every chart is a number the site already shows on its pages"""
        out = [('brands', 'Car brands ranked by owner complaints', 'Lemon Index: complaints per car sold, 100 = the average car. Lower is better.',
                [(b, v, 'good' if v < 100 else 'bad') for b, v in BRANDS], 'Model years 2010-2022. * = rough estimate (few models or estimated sales).'),
               ('models', 'The most and least reliable cars', 'Lemon Index by model, 100 = the average car. Lower is better.',
                [(star(c), c['li'], 'good') for c in CARS[:8]] + [(star(c), c['li'], 'bad') for c in CARS[::-1][:8][::-1]], f'{len(CARS)} models, model years 2010-2022. * = estimated sales.'),
               ('worst-years', f'The worst car model years, {WY0}-{WY1}', 'Lemon Index for that model year, 100 = the average car of the same year.',
                [(f'{v["y"]} {f["name"]}', v['li'], 'bad') for f, v in worst_years(15)], 'Model years with 20,000+ sold. 2023-2025 are early reads.')]
        return out
    def chart_png(cid, title, sub, rows, note):
        from PIL import Image, ImageDraw
        W, P, RH = 1200, 48, 34; H = 150 + RH * len(rows) + 90
        im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
        d.text((P, 34), title, font=_font(38, True), fill='#111111'); d.text((P, 86), sub, font=_font(20), fill='#555555')
        lw = 330; x0 = P + lw; x1 = W - P - 70; mx = max(110, max(v for _, v, _ in rows)) * 1.05; top = 140
        ax = x0 + (x1 - x0) * 100 / mx
        for i, (lab, v, cl) in enumerate(rows):
            y = top + i * RH; f = _font(19)
            t = lab if d.textlength(lab, font=f) <= lw - 14 else lab[:30] + '…'
            d.text((x0 - 12 - d.textlength(t, font=f), y + 4), t, font=f, fill='#111111')
            w = (x1 - x0) * v / mx; d.rounded_rectangle((x0, y + 5, x0 + max(w, 3), y + RH - 7), radius=5, fill='#1f9d55' if cl == 'good' else '#e8141c')
            d.text((x0 + w + 8, y + 3), f'{v:,}', font=_font(19, True), fill='#111111')
        d.line((ax, top - 6, ax, top + RH * len(rows)), fill='#111111', width=2); d.text((ax + 4, top - 30), '100 = average', font=_font(16), fill='#555555')
        yb = top + RH * len(rows) + 22
        d.text((P, yb), note, font=_font(17), fill='#555555')
        d.rectangle((0, H - 44, W, H), fill='#ffd400'); d.text((P, H - 36), CREDIT, font=_font(19, True), fill='#111111')
        _os.makedirs(f'{OUT}/data/charts', exist_ok=True); im.save(f'{OUT}/data/charts/{cid}.png', optimize=True)
        return W, H
    def chart_svg(rows):
        """plain HTML bars (no script): label | bar with a line at 100 | value"""
        mx = max(110, max(v for _, v, _ in rows)) * 1.05
        return ('<div class="eb">' + ''.join(f'<div class="ebr"><span>{E(l)}</span><i><em class="{c}" style="width:{v / mx * 100:.1f}%"></em><s style="left:{100 / mx * 100:.1f}%"></s></i><b>{v:,}</b></div>'
                                              for l, v, c in rows) + '</div>')
    EMBED_URLS = []
    def build_embeds():
        """/data/charts/<id>.png (credit line drawn in) + /embed/<id>/ (a tiny standalone chart page for an iframe), for every chart"""
        out = {}
        for cid, title, sub, rows, note in CHARTS():
            w, h = chart_png(cid, title, sub, rows, note)
            css = ('body{margin:0;font:15px/1.35 Inter,system-ui,-apple-system,Segoe UI,Arial,sans-serif;color:#111;background:#fff}main{padding:16px 18px}'
                   'h1{font-size:20px;margin:0 0 2px}p{margin:0 0 10px;color:#555;font-size:13px}.ebr{display:grid;grid-template-columns:minmax(0,36%) 1fr 3.2em;gap:8px;align-items:center;margin:3px 0}'
                   '.ebr span{text-align:right;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ebr i{position:relative;display:block;height:18px}'
                   '.ebr em{display:block;height:100%;border-radius:4px;background:#e8141c}.ebr em.good{background:#1f9d55}.ebr s{position:absolute;top:-3px;bottom:-3px;width:0;border-left:2px solid #111}'
                   '.ebr b{font-size:12px;font-variant-numeric:tabular-nums}.cr{margin-top:12px;padding:8px 10px;background:#ffd400;color:#111;font-weight:700;border-radius:6px}.cr a{color:#111}')
            body = chart_svg(rows)
            hp = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
                  f'<title>{E(title)} | The Lemon Index</title><link rel="canonical" href="{BASE}/data/"><style>{css}</style></head><body><main><h1>{E(title)}</h1><p>{E(sub)}</p>{body}'
                  f'<p>{E(note)} The black line marks 100, the average car.</p><div class="cr"><a href="{BASE}/" target="_blank" rel="noopener">Source: The Lemon Index (lemonindex.com)</a>, from NHTSA owner complaints. CC BY 4.0</div></main></body></html>')
            _os.makedirs(f'{OUT}/embed/{cid}', exist_ok=True); open(f'{OUT}/embed/{cid}/index.html', 'w', encoding='utf-8').write(hp)
            ih = 120 + 27 * len(rows) + 90
            snip = f'<iframe src="{BASE}/embed/{cid}/" title="{E(title)} (The Lemon Index)" width="100%" height="{ih}" style="border:0;max-width:720px" loading="lazy"></iframe>'
            out[cid] = dict(title=title, png=f'/data/charts/{cid}.png', w=w, h=h, snip=snip)
        return out
    def embed_block(EMB, ids, head='Embed or download this chart'):
        cards = ''.join(f'<div class="emb-c"><img src="{EMB[i]["png"]}" alt="{E(EMB[i]["title"])} (chart, The Lemon Index)" width="{EMB[i]["w"]}" height="{EMB[i]["h"]}" loading="lazy">'
                        f'<p class="emb-t"><b>{E(EMB[i]["title"])}</b></p><p class="emb-a"><a class="btn btn-ghost" href="{EMB[i]["png"]}" download>Download PNG</a> '
                        f'<a href="/embed/{i}/" target="_blank" rel="noopener">Preview the embed</a></p>'
                        f'<div class="cpy"><p class="cpy-l">Embed code</p><div class="cpy-r"><code>{E(EMB[i]["snip"])}</code><button type="button" class="btn btn-ghost cpy-b" data-copy="{E(EMB[i]["snip"])}">Copy</button></div></div></div>'
                        for i in ids if i in EMB)
        return (f'<section class="emb" id="charts"><h2>{head}</h2><p class="sub">Free under CC BY 4.0. The credit line is built into the image and the embed.</p>'
                f'<div class="emb-g">{cards}</div></section>')
    def uxc_data_files(csv_write):
        """the extra CSVs (model-level, EVs, worst model-years) -> [(url, title, n, bytes, cols, desc)]"""
        os.makedirs(f'{OUT}/data', exist_ok=True); out = []
        src1 = lambda fid: ' '.join((SALES_SRC or {}).get(fid) or [])
        yrs_of = {f['name']: f for f in YEARS}
        rows = []
        for c in CARS + CARS_NEW:
            f = yrs_of.get(c['name'])
            rows.append([c['id'], c['name'], c['brand'], c['segName'], c['years'], c['li'], c['n'], c['per100k'], c['avg'], c.get('rank', ''), 'estimate' if c.get('est') else '',
                         f'{BASE}/cars/{f["id"]}/' if f else '', src1(c['id'])])
        cols = [('family_id', 'Our id for the model (same as the page URL)'), ('model', 'Make and model'), ('brand', 'Brand'), ('segment', 'Car, SUV, truck, minivan or van'),
                ('score_model_years', 'The model years the whole-model score covers'), ('lemon_index', 'Owner complaints per car sold, 100 = the average car of the same model years. Lower is better.'),
                ('nhtsa_complaints_3yr', 'NHTSA owner complaints filed within 3 years of each model year, summed over score_model_years'),
                ('complaints_per_100k_sold', 'nhtsa_complaints_3yr per 100,000 sold'), ('average_car_per_100k', 'The average car of the same model years, per 100,000 sold'),
                ('study_rank', 'Rank in the published study of 131 models (blank = added later, scored the same way)'), ('sales_note', '"estimate" = the maker doesn&#39;t report U.S. sales by model (Tesla, Porsche)'),
                ('page', 'The model&#39;s page'), ('sales_source', 'Where the U.S. sales figures come from (we don&#39;t republish the figures)')]
        n, b = csv_write(f'{OUT}/data/lemon-index-by-model.csv', [a for a, _ in cols], rows,
                         note='Counts: nhtsa_complaints_3yr = NHTSA owner complaints filed within 3 years of each model year, summed over score_model_years. Not a safety rating.')
        out.append(('/data/lemon-index-by-model.csv', 'Lemon Index by model', n, b, cols, 'One row per model: the whole-model score, complaints and the sales source.'))
        # EVs
        rows = []
        for c in _EVJ['cars']:
            e = c.get('epa') or {}; f = FY.get(c['slug'])
            rows.append([c['slug'], c['name'], c['years'], c['li'], c.get('rank', ''), c['n'], c['per100k'], c['noadas100k'], c['fire'], len(c['recalls']), c['recalls_fire'],
                         *(e.get('range') or ['', '']), *(e.get('mpg') or ['', '']), *(e.get('cost') or ['', '']), e.get('year', ''),
                         BYNAME[f['name']]['li'] if f else '', f'{BASE}/electric/{c["slug"]}/', c['src']])
        cols = [('slug', 'Our id (same as the page URL)'), ('model', 'Make and model'), ('model_years', 'Model years covered (2021-2024 window)'),
                ('ev_lemon_index', 'EV score: complaints per car sold vs the average car, with the EV window (filed by the end of the year after the model year)'),
                ('ev_rank', 'Rank among EVs with 20,000+ sold (blank = too few sold)'), ('nhtsa_complaints', 'NHTSA owner complaints in the EV window'),
                ('complaints_per_100k_sold', 'Per 100,000 sold (Kelley Blue Book sales estimates)'), ('complaints_without_driver_assist_per_100k', 'The same, leaving out driver-assist complaints (automatic braking, lane assist...)'),
                ('fire_complaints', 'Complaints that report a fire'), ('recalls', 'NHTSA recalls for these model years'), ('recalls_mentioning_fire', 'Recalls whose summary or risk mentions fire'),
                ('epa_range_low / high', 'EPA range in miles, across the versions sold'), ('mpge_low / high', 'EPA MPGe combined'), ('yearly_charging_cost_low / high', 'EPA yearly electricity cost in dollars'),
                ('epa_model_year', 'The model year the EPA figures are for'), ('main_lemon_index', 'The whole-model score on the main car page (3-year window, study model years), where it has one'),
                ('page', 'The EV page'), ('sales_source', 'Where the sales estimates come from')]
        n, b = csv_write(f'{OUT}/data/electric-cars.csv', ['slug', 'model', 'model_years', 'ev_lemon_index', 'ev_rank', 'nhtsa_complaints', 'complaints_per_100k_sold', 'complaints_without_driver_assist_per_100k',
                         'fire_complaints', 'recalls', 'recalls_mentioning_fire', 'epa_range_low', 'epa_range_high', 'mpge_low', 'mpge_high', 'yearly_charging_cost_low', 'yearly_charging_cost_high',
                         'epa_model_year', 'main_lemon_index', 'page', 'sales_source'], rows,
                         note=f'Counts: the EV window = complaints filed with NHTSA by the end of the year after the model year (model years {_EVJ["years"][0]}-{_EVJ["years"][1]}), so it differs from the main 3-year score in lemon-index-by-model.csv.')
        out.append(('/data/electric-cars.csv', 'Electric cars', n, b, cols, 'Every EV: its EV score, complaints, fires, recalls, EPA range, MPGe and charging cost.'))
        # worst model-years
        rows = [[i, f['id'], f['name'], v['y'], v['li'], v['n'], (v['parts'][0][0] if v['parts'] else ''), 'yes' if v.get('early') else '', f'{BASE}{CARU(f, v["y"])}'] for i, (f, v) in enumerate(worst_years(), 1)]
        cols = [('rank', '1 = most complaints per car sold'), ('family_id', 'Our id for the model'), ('model', 'Make and model'), ('model_year', f'{WY0}-{WY1}'),
                ('lemon_index', 'That model year&#39;s Lemon Index (100 = the average car of the same year)'), ('nhtsa_complaints', 'NHTSA owner complaints the score counts'),
                ('top_problem', 'The part owners complained about most'), ('early_read', '"yes" for 2023-2025: complaints filed so far'), ('page', 'The model year&#39;s page')]
        n, b = csv_write(f'{OUT}/data/worst-model-years-{WY0}-{WY1}.csv', [a for a, _ in cols], rows,
                         note=f'Counts: every scored model year {WY0}-{WY1} (20,000+ sold), worst first. nhtsa_complaints = filed within 3 years of the model year (2023-2025: through Oct 2026).')
        out.append((f'/data/worst-model-years-{WY0}-{WY1}.csv', f'Worst model years, {WY0}–{WY1}', n, b, cols, 'Every scored model year, ranked from most to fewest complaints per car sold.'))
        return out
    def worst_years_page(EMB):
        rs = worst_years(); top = rs[:50]
        tr = ''.join(f'<tr><td class="num">{i}</td><td><a href="{CARU(f, v["y"])}">{v["y"]} {E(f["name"])}</a>{" <small class=muted>early read</small>" if v.get("early") else ""}</td>'
                     f'<td class="num bad">{v["li"]:,}</td><td class="num">{v["n"]:,}</td><td>{E(v["parts"][0][0]) if v["parts"] else "—"}</td></tr>' for i, (f, v) in enumerate(top, 1))
        w = top[0]
        body = (f'<article class="study"><p class="kicker"><a href="/rankings/">Rankings</a> · Worst model years</p><h1>The worst car model years, {WY0}–{WY1}</h1>'
                f'<p class="lede">Of {len(rs):,} scored model years from {WY0} to {WY1}, the <b>{w[1]["y"]} {E(w[0]["name"])}</b> drew the most owner complaints per car sold: a Lemon Index of {w[1]["li"]:,}, '
                f'about {w[1]["li"] / 100:.0f} times the average car of that year.</p>'
                f'<p class="sub">Lemon Index = NHTSA owner complaints filed in a car&#39;s first 3 years, per car sold, against the average car of the same model year. <b>100 is average.</b> '
                f'Only model years with 20,000+ sold are scored. 2023–2025 are early reads (complaints filed so far). A complaint is an owner&#39;s report, not a confirmed defect, and this is not a safety rating.</p>'
                f'<p><a class="btn" href="/data/worst-model-years-{WY0}-{WY1}.csv" download>Download all {len(rs):,} (CSV)</a></p>'
                f'<div class="tw"><table><thead><tr><th>#</th><th>Model year</th><th>Lemon Index</th><th>Complaints</th><th>Top problem</th></tr></thead><tbody>{tr}</tbody></table></div>'
                + embed_block(EMB, ['worst-years'], 'Use this chart') +
                f'<p class="note">Every number here is on the model year&#39;s own page. <a href="/method/">How the index works</a> · <a href="/data/">All free data</a></p></article>')
        page('/rankings/worst-years/', f'The Worst Car Model Years, {WY0}–{WY1}, by Owner Complaints | The Lemon Index',
             f'The {len(top)} model years from {WY0} to {WY1} with the most NHTSA owner complaints per car sold, led by the {w[1]["y"]} {w[0]["name"]}. Free CSV of all {len(rs):,} scored model years.',
             body, kind='article', ld=[{"@context": "https://schema.org", "@type": "Dataset", "name": f"Worst car model years {WY0}-{WY1} by NHTSA complaints per car sold", "url": BASE + '/rankings/worst-years/',
                                        "license": "https://creativecommons.org/licenses/by/4.0/", "creator": {"@type": "Organization", "name": "The Lemon Index"}, "dateModified": TODAY,
                                        "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": f'{BASE}/data/worst-model-years-{WY0}-{WY1}.csv'}]}])
        return '/rankings/worst-years/'

elif UXC == 'compare':
    # ---- performance side-by-sides (Tyler: the "M3 vs C63" chip was a dead "Coming soon"; the C63's "vs M3" opened the M3 page)
    import perf_page as _PP
    PERF_ALIAS = {'mercedes-amg-c63': 'amg-c63', 'audi-rs-5': 'audi-rs5', 'alfa-romeo-giulia-quadrifoglio': 'giulia-qv'}   # the M3 file's chip slugs -> the perf ids
    _PD = {}
    for _p in sorted(_os.listdir('data/perf')):
        if _p.endswith('.json') and not _p.endswith('.auto.json'):
            _d = _json.load(open(f'data/perf/{_p}', encoding='utf-8')); _PD[_d['slug']] = _d
    _PL = _PP.perf_list(); _YSJ = _load('data/yt_scores.json'); _SCYJ = _load('data/supercar_engine_yt.json')
    def perf_gens(slug):
        """one row per generation: its headline trim's specs (the perf page's own lead trim), engine, YouTube tone, NHTSA complaints and recalls"""
        D = _PD[slug]; A = _load(f'data/perf/{slug}.auto.json') or {}
        SCY = {**(A.get('scores') or {}), **(_SCYJ or {})}
        YS = (_YSJ or {}).get(D.get('yt_model') or '', {}) or (SCY.get(D.get('yt_study') or '') or {}).get('years') or {}
        nh = A.get('nhtsa') or {}; rc = A.get('recalls') or {}; out = []
        for g in D['gens']:
            vs = g['variants']
            v = next((x for x in vs if x['id'] == D.get('star')), next((x for x in vs if x.get('star')), next((x for x in vs if not x.get('pkg') and _PP._hp(x)), vs[0])))
            zv, zl = _PP._z(v.get('z60')); eng = D['engines'].get(g['engine']) or {}
            ep = eng.get('page') if eng.get('page') and _os.path.exists(f'{OUT}{eng["page"]}index.html') else ''
            yrs = range(g['y0'], g['y1'] + 1)
            out.append(dict(id=g['id'], c=g['code'], y=g['years'], y0=g['y0'], y1=g['y1'], v=v['name'], hp=_PP._hp(v), tq=(v.get('tq') or {}).get('v'), z=zv.replace(' s', '') if zv else None, zs=zl,
                            top=(v.get('top') or {}).get('v'), wt=(v.get('weight') or {}).get('v'), p=(v.get('price') or {}).get('v'), pn=(v.get('price') or {}).get('note') or '',
                            e=eng.get('name') or g['engine'], ew=eng.get('what') or '', eu=ep, yt=_PP._avg(YS, g['y0'], g['y1'])[0],
                            nc=((nh.get('gens') or {}).get(g['id']) or {}).get('n'), rc=len({r['id'] for y in yrs for r in rc.get(str(y), [])})))
        return out
    def perf_focus(slug):
        G = perf_gens(slug); fid = _PD[slug].get('focus')
        return next((g for g in G if g['id'] == fid), G[-1]), G
    def perf_img(slug):
        c = _PL.get(slug) or {}; D = _PD.get(slug) or {}
        src = c.get('img') or next((g.get('img') for g in reversed(D.get('gens', [])) if g.get('img')), '')
        if slug == 'bmw-m3': m = YSL.model_img('bmw-m3'); src = m['src'] if m else src
        return {'src': src, 'w': c.get('w', 1000), 'h': c.get('h', 600), 'author': '', 'ai': D.get('name', '')} if src else None
    _num = lambda s: float(_re.sub(r'[^\d.]', '', str(s))) if s is not None and _re.search(r'\d', str(s)) else None
    def _w(a, b, high):
        x, y = _num(a), _num(b)
        if x is None or y is None or x == y: return '', ''
        return ('w', '') if (x > y) == high else ('', 'w')
    PERF_PAIR_URLS, PERF_PAIRS = [], []
    _first = [('bmw-m3', 'amg-c63'), ('shelby-gt500', 'camaro-zl1'), ('gr-supra', 'nissan-z'), ('bmw-m4', 'audi-rs5'), ('mustang-gt', 'camaro-ss'), ('challenger-hellcat', 'shelby-gt500'),
              ('civic-type-r', 'golf-r'), ('wrx-sti', 'lancer-evolution'), ('gr86', 'mx-5-miata'), ('f150-raptor', 'ram-trx')]
    _seen = set()
    for a, b in _first + [(d['slug'], PERF_ALIAS.get(c['slug'], c['slug'])) for d in _PD.values() for c in d.get('compare', [])]:
        if a in _PD and b in _PD and a != b and frozenset((a, b)) not in _seen: _seen.add(frozenset((a, b))); PERF_PAIRS.append((a, b))
    for a, b in PERF_PAIRS:
        A, B = _PD[a], _PD[b]; (ga, GA), (gb, GB) = perf_focus(a), perf_focus(b)
        na, nb = A['name'], B['name']; sa, sb = A.get('short') or na, B.get('short') or nb
        url = f'/compare/{a}-vs-{b}/'
        def row(lab, va, vb, cls=('', '')): return f'<div class="dl">{lab}</div><div class="dv {cls[0]}">{va}</div><div class="dv {cls[1]}">{vb}</div>'
        dash = lambda x, suf='': '—' if x in (None, '') else f'{E(x)}{suf}'
        eng = lambda g: (f'<a href="{E(g["eu"])}">{E(g["e"])}</a>' if g['eu'] else E(g['e'])) + (f'<br><small>{E(g["ew"])}</small>' if g['ew'] else '')
        duel = (f'<div class="duel"><div></div><div class="dh"><a href="{E(A["page"])}">{E(na)}</a><br><small>{E(ga["c"])} {E(ga["v"])} · {E(ga["y"])}</small></div>'
                f'<div class="dh"><a href="{E(B["page"])}">{E(nb)}</a><br><small>{E(gb["c"])} {E(gb["v"])} · {E(gb["y"])}</small></div>'
                + row('Horsepower', f'<b>{dash(ga["hp"])}</b>', f'<b>{dash(gb["hp"])}</b>', _w(ga['hp'], gb['hp'], True))
                + row('Torque<br><small>lb-ft</small>', dash(ga['tq']), dash(gb['tq']), _w(ga['tq'], gb['tq'], True))
                + row('0–60 mph<br><small>seconds; magazine test, else maker</small>', dash(ga['z']), dash(gb['z']), _w(ga['z'], gb['z'], False))
                + row('Top speed', dash(ga['top']), dash(gb['top']), _w(ga['top'], gb['top'], True))
                + row('Weight', dash(ga['wt']), dash(gb['wt']), _w(ga['wt'], gb['wt'], False))
                + row('Price new<br><small>base, when new</small>', dash(ga['p']), dash(gb['p']), _w(ga['p'], gb['p'], False))
                + row('Engine', eng(ga), eng(gb))
                + row('YouTube owner tone<br><small>out of 100, these years</small>', dash(ga['yt']), dash(gb['yt']), _w(ga['yt'], gb['yt'], True))
                + row(f'Owner complaints<br><small>NHTSA, raw count, these years</small>', dash(ga['nc']), dash(gb['nc']))
                + row('Recalls<br><small>these years</small>', dash(ga['rc']), dash(gb['rc']), _w(ga['rc'], gb['rc'], False)) + '</div>')
        def gtab(D, G):
            tr = ''.join(f'<tr><td>{E(g["c"])} · {E(g["y"])}</td><td>{E(g["v"])}</td><td class="num">{dash(g["hp"])}</td><td class="num">{dash(g["z"])}</td><td>{eng(g).split("<br>")[0]}</td>'
                         f'<td class="num">{dash(g["yt"])}</td><td class="num">{dash(g["nc"])}</td><td class="num">{dash(g["rc"])}</td></tr>' for g in reversed(G))
            return (f'<h3>{E(D["name"])}</h3><div class="tw"><table><thead><tr><th>Generation</th><th>Trim</th><th>hp</th><th>0–60</th><th>Engine</th><th>YouTube tone</th><th>Complaints</th><th>Recalls</th></tr></thead>'
                    f'<tbody>{tr}</tbody></table></div>')
        tool = f'/compare/?cars={a}-{ga["id"]},{b}-{gb["id"]}'
        faster = ga if (_num(ga['z']) or 99) < (_num(gb['z']) or 99) else gb if (_num(gb['z']) or 99) < (_num(ga['z']) or 99) else None
        lede = (f'The newest {E(sa)} ({E(ga["v"])}, {E(ga["y"])}) makes <b>{dash(ga["hp"])} hp</b>; the {E(sb)} ({E(gb["v"])}, {E(gb["y"])}) makes <b>{dash(gb["hp"])} hp</b>.'
                + (f' The {E(sa if faster is ga else sb)} is quicker to 60 ({E(faster["z"])} s).' if faster and faster['z'] else ''))
        title = f'{na} vs {nb}: Specs, Engines and Reliability'
        ia, ib = perf_img(a), perf_img(b)
        page(url, title + ' | The Lemon Index',
             f'{na} vs {nb} side by side: horsepower, torque, 0-60, top speed, weight, price new, engines, YouTube owner tone, NHTSA complaints and recalls, generation by generation.', f'''
<article class="study cmpp pfcmp"><p class="kicker"><a href="/compare/">Compare</a> · Performance</p><h1>{E(na)} vs {E(nb)}</h1>
<p class="lede">{lede}</p><p class="cmp-sh">{share_btn(f"{na} vs {nb}: specs, engines and owner complaints side by side. Free:")}</p>
<h2>Head to head</h2><p class="sub">Each car&#39;s headline trim of its newest generation. Green check = the better of the two on that line (more power, quicker, lighter, cheaper, fewer recalls).</p>{duel}
<p class="note">Owner complaints are raw counts from NHTSA, not per car sold: performance cars sell too few for a fair per-car score, and the busier seller usually draws more. YouTube owner tone = how positively the most-watched videos about those model years talk about the car (100 = all praise).</p>
<p><a class="btn" href="{E(tool)}">Pick other generations or add a car</a></p>
<h2>Every generation</h2>{gtab(A, GA)}{gtab(B, GB)}
<p class="note"><a href="{E(A["page"])}">Everything on the {E(na)}</a> · <a href="{E(B["page"])}">Everything on the {E(nb)}</a> · Specs and their sources are on each car&#39;s page.</p>{share_line(f"{na} vs {nb}: specs and owner complaints side by side. Free:", 'Know someone choosing between these two?')}</article>''',
             kind='article', ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": BASE + url}],
             vis=(pair(ia, ib, (na, nb)) + pcredit(who(ia, ib))) if ia and ib else '')
        PERF_PAIR_URLS.append(url)
    curls.extend(PERF_PAIR_URLS)
    UXC_FIND = [(f'{_PD[a]["name"]} vs {_PD[b]["name"]}', _PD[a].get('make') or _PD[a]['name'].split(' ')[0], f'/compare/{a}-vs-{b}/', 'perf', [],
                 f'{_PD[a].get("short") or ""} vs {_PD[b].get("short") or ""} compare versus') for a, b in PERF_PAIRS]   # find_index.py adds them to the search
    print('performance compare pages:', len(PERF_PAIR_URLS))

    # ---- the hub (Tyler/Dan/Linda: "Any two cars" -> up to 4, every car; mobile match-ups lead with performance and EV pairs)
    def _mu(u, ia, ib, na, nb, tag=''):
        return (f'<a class="mu" href="{E(u)}"><span class="mu-p">{pimg(ia, na, "l")}{pimg(ib, nb, "r")}</span><b>{E(na)} <i>vs</i> {E(nb)}</b>' + (f'<small class="mu-k">{tag}</small>' if tag else '') + '</a>')
    _ev = lambda s: aph(s) or mphoto(s)
    _evn = {c['slug']: c['name'] for c in EVX}
    PERF_TOP = [p for p in PERF_PAIRS if p in _first[:3]]
    EV_TOP = [('tesla-model-3', 2022, 'hyundai-ioniq-5', 2023), ('chevrolet-bolt', 2021, 'nissan-leaf', 2021)]
    _evok = lambda s: s in _evn or s in FY
    ev_cards = ''.join(_mu(f'/compare/?cars={a}-{ya},{b}-{yb}', _ev(a), _ev(b), (FY[a]['name'] if a in FY else _evn[a]).replace('Chevrolet ', 'Chevy '), (FY[b]['name'] if b in FY else _evn[b]), 'Electric')
                       for a, ya, b, yb in EV_TOP if _evok(a) and _evok(b) and _ev(a) and _ev(b))
    pf_cards = ''.join(_mu(f'/compare/{a}-vs-{b}/', perf_img(a), perf_img(b), _PD[a].get('short') or _PD[a]['name'], _PD[b].get('short') or _PD[b]['name'], 'Performance') for a, b in PERF_TOP if perf_img(a) and perf_img(b))
    eco_cards = ''.join(f'<a class="mu" href="{u}"><span class="mu-p">{pimg(mphoto(a), FY[a]["name"], "l")}{pimg(mphoto(b), FY[b]["name"], "r")}</span><b>{E(FY[a]["name"])} <i>vs</i> {E(FY[b]["name"])}</b></a>' for a, b, u in _top[:6])
    pl = ''.join(f'<li><a href="/compare/{a}-vs-{b}/">{E(_PD[a]["name"])} vs {E(_PD[b]["name"])}</a></li>' for a, b in PERF_PAIRS)
    n_all = len(curls)
    page('/compare/', 'Compare Cars Side by Side: Reliability, Specs, EVs | The Lemon Index',
         f'Compare up to 4 cars side by side: owner complaints, recalls, mpg or MPGe, EV range, yearly fuel cost, crash tests and performance specs. Every model, EV and performance car. {n_all} ready-made match-ups.', f'''
<div class="pg">{phero('Compare', 'Compare up to 4 cars.', 'Problems, recalls, mpg, EV range, fuel cost and performance specs, side by side.', visual=pair(mphoto('toyota-rav4', 2019), mphoto('honda-cr-v', 2017), ('Toyota RAV4', 'Honda CR-V')), extra='<div id="cmpx" class="cmpx"><p class="note">Loading…</p></div>')}
<section><h2>Popular match-ups.</h2><div class="mus">{pf_cards}{ev_cards}{eco_cards}</div>
<details class="yd"><summary>{len(PERF_PAIRS)} performance match-ups</summary><ul class="cmp">{pl}</ul></details>
<details class="yd"><summary>All {len(_cp)} everyday-car match-ups</summary><ul class="cmp">{cl}</ul></details></section>
{pcredit(who(*[mphoto(x) for a, b, _ in _top[:6] for x in (a, b)], mphoto('toyota-rav4', 2019), mphoto('honda-cr-v', 2017), *[_ev(x) for a, _, b, _ in EV_TOP for x in (a, b) if _evok(x)], *[perf_img(x) for p in PERF_TOP for x in p]))}
{share_line("Compare up to 4 cars side by side: problems, recalls, mpg, EV range and specs. Free:", 'Know someone stuck between cars?')}</div><script src="/assets/compare.js?v=1112c2" defer></script>''',
         ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Car comparisons", "url": BASE + '/compare/'}])
    curls.insert(0, '/compare/')

elif UXC == 'data':
    # ---- the compare tool's data: every model the site has a page for (Tyler: "M3", "C63", "Supra" found nothing; Dan: no Model 3, no Ioniq 5)
    _al = {}
    for r in FIND:
        if r[2]: _al[r[2]] = (_al.get(r[2], '') + ' ' + (r[5] or '')).strip()
    CMP = []
    def _ev_extra(slug):
        c = _EVS.get(slug)
        if not c: return None
        e = c.get('epa') or {}
        return {'r': e.get('range'), 'c': e.get('cost'), 'e': e.get('mpg'), 'yr': e.get('year'), 'li': c['li'], 'w': c['years'], 'u': f'/electric/{slug}/'}
    def _dflt(ys):
        ok = [y for y, v in ys.items() if v[0] is not None]
        return max(ok) if ok else max(ys)
    for f in YEARS:
        ys = {}
        for v in f['years']:
            x = extra(f['id'], v['y']); m = x.get('mpg'); sf = x.get('safety')
            ys[str(v['y'])] = [v['li'] if v['ok'] else None, v['n'], len(x['recalls']) if 'recalls' in x else None, m['comb'][0] if m else None, m['comb'][1] if m else None,
                               sf.get('best') if sf else None, NICE(v['parts'][0][0]) if v['parts'] else None, (m.get('cost') or [None, None])[0] if m else None,
                               (m.get('cost') or [None, None])[1] if m else None, 1 if m and m.get('ev') else 0]
        u = f'/cars/{f["id"]}/'; e = {'i': f['id'], 'n': f['name'], 'b': BYNAME[f['name']]['brand'], 'u': u, 'k': 'ev' if f['id'] in _EVS else 'car', 'a': _al.get(u, ''), 'y': ys, 'd': _dflt(ys)}
        if f['id'] in _EVS: e['ev'] = _ev_extra(f['id'])
        CMP.append(e)
    if 'toyota-rav4' in FY and RAV4H:   # the RAV4 Hybrid: the RAV4's complaints and score (NHTSA files them together), the hybrid's own EPA mpg and cost
        R = next(e for e in CMP if e['i'] == 'toyota-rav4'); hy = {}
        for y, r in RAV4H['years'].items():
            if y in R['y'] and r.get('hybrid'):
                h = r['hybrid']; v = list(R['y'][y]); v[3], v[4] = h['comb']; v[7], v[8] = (h.get('cost') or [None, None]); hy[y] = v
        if hy: CMP.append({'i': 'toyota-rav4-hybrid', 'n': 'Toyota RAV4 Hybrid', 'b': 'Toyota', 'u': '/cars/toyota-rav4/', 'k': 'car', 'a': 'rav4 hybrid rav4hybrid hybrid', 'y': hy, 'd': _dflt(hy),
                           'h': 'Score and complaints: every RAV4 version together (NHTSA files them under RAV4). MPG and fuel cost: the Hybrid (EPA).'})
    for c in EVX:   # EVs without a main car page: the EV page's own score (its shorter window), labelled as such
        if c['slug'] in FY: continue
        ys = {}
        epa = c.get('epa') or {}
        recs = [(_ryears(r['summary']) or set(range(_evyears(c)[0], _evyears(c)[-1] + 1))) for r in c['recalls']]
        for v in c['years_detail']:
            ys[str(v['y'])] = [v['li'], v['n'], sum(1 for s in recs if v['y'] in s), *(epa.get('mpg') or [None, None]), None, (EPART.get(c['issues'][0][0], c['issues'][0][0].lower()) if c['issues'] else None),
                               *(epa.get('cost') or [None, None]), 1]
        u = f'/electric/{c["slug"]}/'
        CMP.append({'i': c['slug'], 'n': c['name'], 'b': _brandof(c['make']), 'u': u, 'k': 'ev', 'a': (_al.get(u, '') + ' ev electric').strip(), 'y': ys, 'd': max(ys) if ys else '', 'w': 'ev', 'ev': _ev_extra(c['slug'])})
    for slug, D in _PD.items():   # performance cars: one choice per generation
        if not _os.path.exists(f'{OUT}{D["page"]}index.html'): continue
        G = perf_gens(slug)
        CMP = [e for e in CMP if e['u'] != D['page']]   # the M3's model page: the performance entry wins (it's what people compare)
        CMP.append({'i': slug, 'n': D['name'], 'b': D.get('make') or D['name'].split(' ')[0], 'u': D['page'], 'k': 'perf', 'a': _al.get(D['page'], ''),
                    'g': [{k: g[k] for k in ('id', 'c', 'y', 'v', 'hp', 'tq', 'z', 'zs', 'top', 'wt', 'p', 'e', 'eu', 'yt', 'nc', 'rc')} for g in G], 'd': D.get('focus') or G[-1]['id']})
    for c in SCX:   # supercars: EPA mpg, fuel cost and recalls per model year
        ys = {str(y['y']): [None, None, len(y.get('recalls') or []), *(y.get('comb') or [None, None]), None, None, *(y.get('cost') or [None, None]), 0] for y in c['years']}
        u = f'/supercars/{_slg(c["name"])}/'
        CMP.append({'i': 'sc-' + _slg(c['name']), 'n': c['name'], 'b': c['make'], 'u': u, 'k': 'sc', 'a': _al.get(u, ''), 'y': ys, 'd': max(ys),
                    'eng': {str(y['y']): (y.get('engines') or [''])[0] for y in c['years']}})
    _have = {e['u'] for e in CMP}
    for m in _XM.values():   # complaints-only models (no sales figure): complaints and recalls per model year, never a score
        u = f'/cars/{m["id"]}/'
        if u in _have or not _os.path.exists(f'{OUT}{u}index.html'): continue
        by = m.get('by_year') or {}; rc = m.get('recalls') or []
        ys = {y: [None, n, sum(1 for r in rc if int(y) in (r.get('years') or [])) if rc and rc[0].get('years') is not None else None, None, None, None, None, None, None, 0] for y, n in by.items()}
        if ys: CMP.append({'i': m['id'], 'n': m['name'], 'b': m.get('brand') or m['name'].split(' ')[0], 'u': u, 'k': 'co', 'a': _al.get(u, ''), 'y': ys, 'd': max(ys)})
    _os.makedirs(f'{OUT}/assets', exist_ok=True)
    _json.dump({'v': 2, 'cars': CMP}, open(f'{OUT}/assets/compare.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('compare.json:', len(CMP), 'cars,', sum(1 for e in CMP if e['k'] == 'perf'), 'performance,', sum(1 for e in CMP if e['k'] == 'ev'), 'electric')
    # every EV must be comparable (Dan's Model 3 / Ioniq 5 case), and every performance page: the build stops otherwise
    _cu = {e['u'] for e in CMP}
    _miss = [f'/electric/{c["slug"]}/' for c in EVX if f'/electric/{c["slug"]}/' not in _cu and f'/cars/{c["slug"]}/' not in _cu] + [D['page'] for D in _PD.values() if _os.path.exists(f'{OUT}{D["page"]}index.html') and D['page'] not in _cu]
    if _miss: raise SystemExit(f'compare.json is missing: {_miss[:10]}')

    # ---- "Embed this chart" on the rankings and stats pages (Priya: "embeddable charts, or chart images with the credit built in")
    def _inject(path, ids):
        p = f'{OUT}{path}index.html'
        if not _os.path.exists(p): return
        h = open(p, encoding='utf-8').read()
        if 'id="charts"' in h or '</main>' not in h: return
        blk = f'<div class="pg">{embed_block(EMB, ids)}</div>' + ('' if 'assets/data.js' in h else '<script src="/assets/data.js?v=1103" defer></script>')
        open(p, 'w', encoding='utf-8').write(h.replace('</main>', blk + '</main>', 1))
    _inject('/rankings/', ['brands', 'models', 'worst-years'])
    _inject('/stats/car-complaints/', ['brands', 'worst-years'])
