# BMW specs, engines and engine x year reliability (11-10, Elijah: "people want engine / spec data ... full build for the BMW first",
# then "each year for each engine and its reliability" and "a YouTube score per year per engine too"). exec'd by build.py twice:
#   1. early (BMW_PHASE = 'hooks'): defines SPECS_HOOK / YEAR_SPECS_HOOK, used by the existing BMW model and year pages
#   2. late  (BMW_PHASE = 'pages'): new BMW model pages, /engines/bmw/ and /engines/bmw-<code>/, links in from /brands/bmw/
# Data: data/bmw_specs.json (data_bmw_specs.py) + data/bmw_engine_yt.json (data_bmw_yt.py). Every number on these pages says which
# way it was attributed to an engine (see data_bmw_specs.py): (a) version-named complaints, (b) single-engine model year (real
# per-car score), (c) complaints naming the engine, or "all engines combined".
if BMW_PHASE == 'hooks':
    BS = _load('data/bmw_specs.json'); BYT = _load('data/bmw_engine_yt.json'); BPH = _load('data/bmw_engine_photos.json')
    BENG = BS.get('engines', {}); BVER = BS.get('versions', {}); BFY = BS.get('fam_years', {}); BVC = BS.get('version_complaints', {})
    BEY = BS.get('engine_years', {}); BNEW = BS.get('new_models', {}); BFAM = BS.get('families', {})
    ENG_URL = lambda c: f'/engines/bmw-{c.lower()}/'
    ENG_OK = set()   # engine pages actually built (filled in the pages phase; hooks only link to codes with data)
    def _bpower(v):
        if v.get('hp'): return f'{v["hp"]} hp' + (f' · {v["tq"]} lb-ft' if v.get('tq') else '')
        return '—'
    def _bsize(v):
        if v['kind'] == 'EV': return 'Electric' + (f' · {v["ev_range"]} mi range' if v.get('ev_range') else '')
        cyl = {'4': 'I4', '6': 'I6', '8': 'V8', '12': 'V12', '3': 'I3', '2': '2-cyl', '10': 'V10'}.get(v['cyl'] or '', f'{v["cyl"]} cyl')
        if v['cyl'] == '6' and (v['displ'] or '').startswith('4'): cyl = 'V6'
        return f'{v["displ"]} L {cyl}' + (' turbo' if v['turbo'] == 'turbo' else '') + (f' + {v["kind"]}' if v['kind'] in ('plug-in hybrid', 'hybrid', 'mild hybrid') else '') + (' diesel' if v['kind'] == 'diesel' else '')
    def _bmpg(v):
        if v['kind'] == 'EV': return f'{v["mpg"][2]} MPGe' if v['mpg'][2] else '—'
        a, b = v['mpg'][2], v['mpg'][3]
        return (f'{a}' if a == b else f'{a}–{b}') + ' mpg' if a else '—'
    def _bcode(v):
        if not v.get('code'): return '<span class="muted">not confirmed</span>' if v['kind'] != 'EV' else '—'
        return f'<a href="{ENG_URL(v["code"])}">{E(v["code"])}</a>'
    _pl = lambda n: f'{n:,} complaint' + ('' if n == 1 else 's')
    def _bsignal(fid, y, v):
        """This version's reliability signal for that model year, labeled with how it was attributed."""
        fy = BFY.get(f'{fid}|{y}') or {}
        if v['kind'] == 'EV': return f'{_pl(fy.get("n", 0))} <small>(whole model)</small>'
        if fy.get('single') and fy.get('li'): return f'Index <b>{fy["li"]}</b> <small>(one engine that year)</small>'
        if v.get('vk'):
            for k, a in (BVC.get(f'{fid}|{y}') or {}).items():
                num, kind = k.split('|')
                if num == v['vk'][0] and (kind == v['vk'][1] or {kind, v['vk'][1]} <= {'i', 'ci'}) and a.get('code') == v.get('code') and a['n']:
                    return f'{_pl(a["n"])} <small>(filed as {E(num + kind)})</small>'
        if fy.get('li'): return f'Index {fy["li"]} <small>(all engines combined)</small>'
        return f'{_pl(fy.get("n", 0))} <small>(all engines combined)</small>' if fy.get('n') else '—'
    def _bver_table(fid, y, vl):
        rows = ''.join(f'<tr><td>{E(v["model"])}</td><td>{_bcode(v)}</td><td>{E(_bsize(v))}</td><td>{_bpower(v)}</td><td>{E(", ".join(v["tr"]))}</td><td>{E(v["drive"])}</td><td>{_bmpg(v)}</td><td>{_bsignal(fid, y, v)}</td></tr>' for v in vl)
        return ('<div class="tw"><table class="adv spec"><thead><tr><th>Version</th><th>Engine</th><th>Size</th><th>Power</th><th>Transmission</th><th>Drive</th><th>EPA</th><th>Owner complaints</th></tr></thead>'
                f'<tbody>{rows}</tbody></table></div>')
    SPEC_NOTE = ('<p class="yc-cap">Engine sizes, transmissions, drive and MPG: EPA (fueleconomy.gov). Engine codes and power: BMW&#39;s ratings as listed in Wikipedia&#39;s '
                 'BMW engine articles (US-rated figures can differ by a few hp); "not confirmed" means we couldn&#39;t source the code for that version. '
                 'Owner complaints: NHTSA, about the whole car (any system), not only the engine. Index = the model year&#39;s Lemon Index (complaints per car sold vs the average car); it is shown for a version only when that was the only engine that year. '
                 'A complaint count is not a failure rate: popular versions draw more complaints because more were sold.</p>')
    def SPECS_HOOK(fid):
        yrs = BVER.get(fid)
        if not yrs: return ''
        ys = sorted(yrs, key=int, reverse=True)
        codes = sorted({v['code'] for y in ys for v in yrs[y] if v.get('code')})
        eng = ''.join(f'<a class="chip" href="{ENG_URL(c)}">{E(c)}</a>' for c in codes if c in BEY)
        blocks = ''.join(f'<details class="yd"{" open" if i == 0 else ""}><summary>{y} · {len(yrs[y])} version{"s" if len(yrs[y]) != 1 else ""}</summary>{_bver_table(fid, int(y), yrs[y])}</details>' for i, y in enumerate(ys))
        nm = E(BFAM.get(fid, fid))
        return (f'<section class="yc bspec" id="specs"><h2>{nm} specs and engines, every year. <span class="h2s">Every version the EPA lists, with its engine and owner complaints.</span></h2>'
                + (f'<p class="chips">Engines used: {eng}</p>' if eng else '') + blocks + SPEC_NOTE + '</section>')
    def YEAR_SPECS_HOOK(fid, y):
        vl = (BVER.get(fid) or {}).get(str(y))
        if not vl: return ''
        nm = E(BFAM.get(fid, fid))
        return f'<section class="yc bspec" id="specs"><h2>{y} {nm} specs and engines</h2>{_bver_table(fid, y, vl)}{SPEC_NOTE}</section>'
    SEGN['engines'] = 'Engines'

else:
    # ---------------------------------------------------------------- pages phase
    BMW_URLS = []; import html as _html
    _rows = lambda head, R: '<div class="tw"><table class="adv"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in R) + '</tbody></table></div>'
    def _noindex(path):
        p = os.path.join(OUT, path.strip('/'), 'index.html'); s = open(p, encoding='utf-8').read()
        if 'name="robots"' not in s: open(p, 'w', encoding='utf-8').write(s.replace('<link rel="canonical"', '<meta name="robots" content="noindex,follow"><link rel="canonical"', 1))
    def _fam_link(fid):
        if fid in BYNAME_ID or fid in BNEW: return f'<a href="/cars/{fid}/">{E(BFAM.get(fid, fid))}</a>'
        return E(BFAM.get(fid, fid))
    BYNAME_ID = {c['id'] for c in CARS}
    # ---- our own engine illustrations: CC BY 4.0 (Elijah 11-10), Google Images licensing markup, an /images/ page and an image sitemap.
    # The AI illustrations are ours to license as far as the law allows; real Commons photos keep their own licenses and aren't relicensed.
    CCBY = 'https://creativecommons.org/licenses/by/4.0/'; IMG_PAGES = []
    def img_ld(code, ph):
        return {"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": BASE + ph['src'], "url": BASE + ph['src'],
                "name": ph.get('title') or f'BMW {code} engine (illustration)', "description": f'{ph.get("title") or "BMW " + code + " engine"}. AI-generated illustration, not a photo of a specific engine.',
                "width": ph['w'], "height": ph['h'], "encodingFormat": "image/webp", "license": CCBY, "acquireLicensePage": BASE + '/images/',
                "creditText": "The Lemon Index", "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE + '/'},
                "copyrightNotice": "The Lemon Index (lemonindex.com), CC BY 4.0", "isAccessibleForFree": True}
    # ---- engine pages
    # 11-12 (UX test: this page said "not enough YouTube videos" while the M3 page said "#1 of 4 M3 engines"): ONE YouTube source per engine.
    # An engine a performance page covers (S54, S55, S58) reads the performance page's engine (perf_page.engine_ext: its own engine study);
    # the rest keep the BMW engine attribution (data/bmw_engine_yt.json).
    import perf_page as _PP
    _EXT = {c: _PP.engine_ext(ENG_URL(c)) for c in BENG}
    def _yty(code):
        x = _EXT.get(code)
        return (x['years'] if x and x['years'] else None) or BYT.get(code) or {}
    def _yt_cell(code, y):
        d = _yty(code).get(str(y))
        if d and d.get('score') is not None:
            nm = d.get('named', 0)
            return f'<b>{d["score"]}</b> <small>({d["videos"]} videos, {nm if nm else "none"} naming {y})</small>', d['score']
        return '<small>not enough videos</small>', None
    def _owner_cell(e):
        b = [x for x in e['b'] if x.get('li')]
        if b:
            avg = round(sum(x['li'] for x in b) / len(b))
            return f'Index <b>{avg}</b> <small>(b: whole-car score; {", ".join(E(BFAM.get(x["fam"], x["fam"])) for x in b)} had only this engine)</small>', ('b', avg)
        if e['a']:
            return f'<b>{e["a"]:,}</b> complaint{"" if e["a"] == 1 else "s"} <small>(a: filed as {", ".join(E(x["name"]) for x in e["a_from"])})</small>', ('a', e['a'])
        nob = [x for x in e['b'] if not x.get('li')]
        if nob:
            n = sum(x['n'] for x in nob)
            return f'<b>{n:,}</b> complaints <small>(b: only engine in {", ".join(E(BFAM.get(x["fam"], x["fam"])) for x in nob)}; no sales data, so no per-car score)</small>', ('a', n)
        if e['combined']:
            parts = [f'{E(BFAM.get(x["fam"], x["fam"]))} {("Index " + str(x["li"])) if x.get("li") else (str(x["n"]) + " complaints")}' for x in e['combined']]
            return f'<small>all engines combined: {"; ".join(parts)}</small>', None
        return '—', None
    # 11-10 v2: each engine's YouTube rank among the BMW engines here (average tone over its years with enough videos), for the page badge
    _YTAVG = {}
    # 11-11 fix: ONE ranking for the engine page badge AND the /engines/bmw/ hub badge - only the engine's own years (the years its
    # page lists), only engines that have a page, same order (average tone, then code to break ties)
    for _c in BENG:
        _yy = BEY.get(_c) or {}
        _v = [d['score'] for y, d in _yty(_c).items() if y in _yy and d and d.get('score') is not None]
        if _v: _YTAVG[_c] = sum(_v) / len(_v)
    _YTRANK = {c: i + 1 for i, c in enumerate(sorted(_YTAVG, key=lambda c: (-_YTAVG[c], c)))}
    def _engine_page(code):
        meta = BENG[code]; yrs = BEY.get(code) or {}
        if not yrs: return None
        ys = sorted(yrs, key=int); y0, y1 = ys[0], ys[-1]
        fams = sorted({f for y in ys for f in yrs[y]['models']}, key=lambda f: BFAM.get(f, f))
        hp = sorted({v['hp'] for f in BVER for y in BVER[f] for v in BVER[f][y] if v.get('code') == code and v.get('hp')} | ((_EXT.get(code) or {}).get('hp') or set()))   # 11-12: + the performance pages' versions (M3 CS, M4 CSL), so both pages give one range
        rows, scored_b, scored_a, comb_only, yt_scores, own = [], 0, 0, 0, {}, {}
        for y in ys:
            e = yrs[y]; cell, kind = _owner_cell(e); ytc, yts = _yt_cell(code, y)
            if kind and kind[0] == 'b': scored_b += 1; own[int(y)] = ('b', kind[1])
            elif kind: scored_a += 1; own[int(y)] = ('a', kind[1])
            elif e['combined']: comb_only += 1
            if yts is not None: yt_scores[int(y)] = yts
            models = '<br>'.join(f'{_fam_link(f)} <small>{E(", ".join(ms))}</small>' for f, ms in e['models'].items())
            txt = e['c']; parts = ', '.join(f'{E(p)}' for p, _ in e['parts'][:3]) or '—'
            yp = next((f for f in e['models'] if os.path.exists(os.path.join(OUT, 'cars', f, str(y), 'index.html'))), None)   # only link year pages that were built
            rows.append([f'<a href="/cars/{yp}/{y}/">{y}</a>' if yp else y, models, cell, f'{txt:,}' if txt else '0', ytc, parts])
        # best / most-complaint years, from like-for-like numbers only
        bline = ''
        bs = {y: v for y, (k, v) in own.items() if k == 'b'}
        if len(bs) >= 2:
            lo = min(bs, key=bs.get); hi = max(bs, key=bs.get)
            bline = f'Where this was the only engine in the model, the <b>{lo}</b> had the fewest owner complaints per car (Index {bs[lo]}) and the <b>{hi}</b> the most (Index {bs[hi]}), counting complaints about any part of the car.'
        else:
            ac = {y: v for y, (k, v) in own.items() if k == 'a'}
            if len(ac) >= 2:
                hi = max(ac, key=ac.get); bline = f'The most owner complaints (about any part of the car) filed under version names that used this engine were for the <b>{hi}</b> ({ac[hi]:,}). Counts follow sales, so this is not a failure rate.'
        yline = ''
        if len(yt_scores) >= 2:
            yb = max(yt_scores, key=yt_scores.get); yw = min(yt_scores, key=yt_scores.get)
            yline = (f'YouTube videos are most positive about the <b>{yb}</b> ({yt_scores[yb]}) and least about the <b>{yw}</b> ({yt_scores[yw]}); neighboring years share many of the same videos, so small gaps mean little.'
                     if yt_scores[yb] != yt_scores[yw] else '')
        agree = ''
        both = [y for y in yt_scores if y in bs]
        if len(both) >= 2:
            ob = min(both, key=lambda y: bs[y]); yb2 = max(both, key=lambda y: yt_scores[y])
            agree = (f'Owners and YouTube agree: the {ob} is the best of these years on both.' if ob == yb2 else
                     f'Owners and YouTube disagree: owner complaints favor the {ob}, YouTube favors the {yb2}.')
        txt_total = sum(BS.get('text_mentions', {}).get(code, {}).values())
        models_s = ', '.join(BFAM[f].replace('BMW ', '') for f in fams)
        ans = (f'The {E(meta["name"])} is BMW&#39;s {E(meta["size"])} {E(meta["asp"])} {E(meta["layout"])}, made {E(meta["made"])}. '
               f'In the US it was used in the {E(models_s)} from model years {y0} to {y1}' + (f', rated {hp[0]}' + (f'–{hp[-1]}' if len(hp) > 1 else '') + ' hp' if hp else '') + '. '
               + (f'{txt_total:,} owner complaints to the government name the {E(code)} in their own words. ' if txt_total else '') + (bline.replace('<b>', '').replace('</b>', '') + ' ' if bline else ''))
        # 11-10 v2 (design audit): one-line answer, 3 chips, a per-year chart (owner score + YouTube tone), the matching rules folded,
        # and the "fewest complaints" sentence said once (it used to repeat in the answer, under the table and in the FAQ).
        lo_y = min(bs, key=bs.get) if len(bs) >= 2 else None
        yb_y = max(yt_scores, key=yt_scores.get) if len(yt_scores) >= 2 and len(set(yt_scores.values())) > 1 else None
        ans1 = (f'BMW&#39;s {E(meta["size"])} {E(meta["asp"])} {E(meta["layout"])} in the {E(models_s)}, model years {y0}–{y1}.'
                + (f' Fewest owner complaints per car: the <b>{lo_y}</b>.' if lo_y else '') + (f' YouTube likes the <b>{yb_y}</b> best.' if yb_y else ''))
        rk = _YTRANK.get(code)
        chips = (f'<div class="trc"><div><b>{y0}–{str(y1)[-2:]}</b><span>model years</span></div>'
                 + (f'<div><b>{hp[0]}' + (f'–{hp[-1]}' if len(hp) > 1 else '') + '</b><span>hp (US)</span></div>' if hp else '')
                 + (f'<div><b>{int(_YTAVG[code] + 0.5)}</b><span>YouTube owner tone /100 · #{rk} of {len(_YTRANK)} BMW engines</span></div>' if rk else '<div><b>–</b><span>not enough YouTube videos to rank</span></div>') + '</div>')
        mxi = max([150] + [v for k, v in own.values() if k == 'b'])
        def erow(y):
            e = yrs[y]; k = own.get(int(y)); sc = yt_scores.get(int(y))
            if k and k[0] == 'b': ow = f'<span class="eg-o {"bad" if k[1] > 110 else "good" if k[1] < 90 else ""}"><i style="width:{min(100, k[1] / mxi * 100):.0f}%"></i></span><b class="{"bad" if k[1] > 110 else "good" if k[1] < 90 else ""}">{k[1]}</b>'
            elif k: ow = f'<span class="eg-o na"></span><b class="mute">{k[1]:,}<small> compl.</small></b>'
            else: ow = '<span class="eg-o na"></span><b class="mute">·</b>'
            yt = (f'<span class="eg-t"><i style="width:{sc}%"></i></span><b>{sc}</b>' if sc is not None else '<span class="eg-t na"></span><b class="mute">·</b>')
            cars = ', '.join(BFAM.get(f, f).replace('BMW ', '') for f in e['models'])
            return f'<div class="egr"><span class="egy">{y}<small>{E(cars)}</small></span>{ow}{yt}</div>'
        chart = ('<div class="egc"><div class="egh" aria-hidden="true"><span>Year</span><span>Owner complaints <em>Lemon Index, lower = better</em></span><span>YouTube tone <em>0-100, higher = better</em></span></div>'
                 + ''.join(erow(y) for y in ys) + '</div>')
        sec = []
        sec.append('<h2>Reliability by year</h2>' + chart + (f'<p class="note">{yline}</p>' if yline else '') + (f'<p class="note">{agree}</p>' if agree else '')
                   + '<details class="trm"><summary>Owner score = the whole car&#39;s Lemon Index where this was its only engine that year; a gray dot means the model shared engines, so the number isn&#39;t this engine&#39;s alone. <span>How we count</span></summary>'
                   '<p>How each number is matched to the engine: <b>(a)</b> complaints filed under a version name that used only this engine that year (e.g. "335I"); '
                   '<b>(b)</b> the model had only this engine that year, so its Lemon Index (complaints per car sold vs the average car) applies to every car with this engine; '
                   '"all engines combined" = the model had several engines under one name, so its number is not this engine&#39;s alone. '
                   'Owner complaints cover the whole car (brakes, air bags, electrics ...), not only the engine. None of these is a failure rate. '
                   'YouTube tone = how positive the videos are, 0–100, from titles and transcripts that name the engine or a version that used it. '
                   'A video whose title names no model year counts toward every year of its generation, so neighboring years share most of their videos.</p></details>'
                   + '<details class="cpd engd"><summary>All the numbers, year by year</summary>'
                   + _rows(['Year', 'Cars with it', 'Owner complaints', f'Complaints naming "{E(code)}"', 'YouTube says', 'Top complaint areas'], rows) + '</details>')
        # 11-12: the known issues the performance pages list for this engine (same text, sources and owner-complaint counts as the M3 page), then Wikipedia's notes
        _x = _EXT.get(code); _pi = ''
        if _x and _x['issues']:
            _pi = ''.join(f'<li><b>{E(i["t"])}</b> <small>({E(i["kind"])})</small>. {E(i["x"])}' + (f' <b>Fix:</b> {E(i["fix"])}' if i.get('fix') else '')
                          + (f' <small>{i["n"]} owner complaint{"" if i["n"] == 1 else "s"} to NHTSA mention it ({E(", ".join(i["where"]))}).</small>' if i['n'] else '') + '</li>' for i in _x['issues'].values())
            _pi += ''.join(f'<li>{E(n)} <small>(Wikipedia)</small></li>' for n in meta.get('notes') or [])
            _srcs = ', '.join(f'<a href="{E(v["u"])}" rel="noopener nofollow">{E(v["t"])}</a>' for v in _x['sources'].values())
            sec.append(f'<section class="engk"><h2>Known issues on record</h2><ul>{_pi}</ul><p class="yc-cap">Sources: {_srcs}' + (f'; <a href="{E(meta["src"])}" rel="noopener">Wikipedia, {E(meta["name"])}</a>' if meta.get('notes') else '')
                       + '. The same list as on ' + ', '.join(f'<a href="{E(u)}">the {E(n)} page</a>' for n, u, _g in _x['cars'] if u) + '.</p></section>')
        elif meta.get('notes'):
            sec.append(f'<section class="engk"><h2>Known issues on record</h2><ul>' + ''.join(f'<li>{E(n)}</li>' for n in meta['notes'])
                       + f'</ul><p class="yc-cap">According to <a href="{E(meta["src"])}" rel="noopener">Wikipedia&#39;s {E(meta["name"])} article</a> and its sources.</p></section>')
        vers = collections.OrderedDict()
        for f in BVER:
            for y in sorted(BVER[f], key=int):
                for v in BVER[f][y]:
                    if v.get('code') == code: vers.setdefault((f, v['model'], v.get('hp'), v.get('tq')), []).append(int(y))
        # 11-10 v2: 3 compact columns (model + version, years, power / torque) so it fits a phone without stacking
        vr = [[f'{_fam_link(f)} <small>{E(m)}</small>', f'{min(yl)}–{str(max(yl))[-2:]}' if len(yl) > 1 else str(yl[0]), (f'{hp_} hp' if hp_ else '—') + (f'<small> · {tq} lb-ft</small>' if tq else '')] for (f, m, hp_, tq), yl in vers.items()]
        sec.append('<section class="engv"><h2>Every US version with this engine</h2>' + _rows(['Model and version', 'Years', 'Power'], vr)
                   + f'<p class="yc-cap">Versions and years: EPA (fueleconomy.gov). Engine and power: <a href="{E(meta["src"])}" rel="noopener">Wikipedia, {E(meta["name"])}</a> (BMW ratings; US figures can differ by a few hp).</p></section>')
        faq = [(f'What cars have the {meta["name"]} engine?', f'In the US: the {models_s}, model years {y0}–{y1}. See the version table for each one.'),
               (f'Is the {code} reliable?', (re.sub('<[^>]+>', '', bline) + ' ' if bline else '') + 'Government complaints are filed by model and year, not engine, and they cover the whole car, so none of these numbers is an engine failure rate. We only credit a number to this engine where the version name or the model year leaves no doubt. Have any used car inspected.')]
        if hp: faq.append((f'How much horsepower does the {code} make?', f'BMW rated it at {hp[0]}' + (f' to {hp[-1]}' if len(hp) > 1 else '') + ' hp in US versions, depending on the car and year.'))
        sec.append('<section class="yqa trq"><h2>Quick answers</h2>' + qa_fold(''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq)) + '</section>')
        path = ENG_URL(code)
        ph = BPH.get(code); fig = ''
        if ph:   # a real Wikimedia Commons photo whose file name/description names this code, or (N54/N55/B58/N63 only, Elijah 11-10) a labeled AI illustration
            lic = ph.get('license', ''); pg = E(ph.get('page', ''))
            if ph.get('ai'):
                cr = ('Illustration (AI-generated), not a photo of a specific engine. '
                      f'Free to use under <a href="{CCBY}" rel="noopener license">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>')
            else:
                lm = re.match(r'CC (BY(?:-SA)?) ([0-9.]+)$', lic.strip(), re.I)
                lic_h = f'<a href="https://creativecommons.org/licenses/{lm.group(1).lower()}/{lm.group(2)}/" rel="noopener license">{E(lic)}</a>' if lm else E(lic)
                cr = (f'Photo: <a href="{pg}" rel="noopener">Wikimedia Commons</a>' if re.search(r'cc0|public domain', lic, re.I)
                      else f'Photo: {E(ph.get("author", ""))} / <a href="{pg}" rel="noopener">Wikimedia Commons</a> ({lic_h}), resized')
            alt = f'Illustration of a BMW {E(code)} {E(BENG[code]["size"])} {E(BENG[code]["layout"])} engine' if ph.get('ai') else f'BMW {E(code)} engine'
            fig = (f'<figure class="engph"><img src="{E(ph["src"])}"{rset(ph["src"], "(max-width: 700px) 100vw, 680px")} width="{ph["w"]}" height="{ph["h"]}" '
                   f'alt="{alt}" loading="eager">' + YSL.info(cr) + '</figure>')
        body = (f'<article class="study tr2 eng2"><p class="kicker"><a href="/engines/bmw/">BMW engines</a> · <a href="/brands/bmw/">BMW</a></p>'
                f'<h1>BMW {E(code)} engine reliability by year</h1><p class="tra">{ans1} <button type="button" class="shl" data-share="{E(f"BMW {code} engine reliability, year by year. Free:")}">Share ↗</button></p>{chips}'
                + ''.join(sec) + '</article>')
        title = next(t for t in (f'BMW {code} Engine Reliability by Year, Specs & Cars', f'BMW {code} Engine: Reliability by Year & Specs', f'BMW {code} Engine Reliability') if len(t) <= 65)
        ld = [faq_ld([(q, '', a) for q, a in faq])]
        if ph and ph.get('ai'): ld.append(img_ld(code, ph)); IMG_PAGES.append((path, ph))
        elif ph: IMG_PAGES.append((path, ph))
        page(path, title, _html.unescape(re.sub('<[^>]+>', '', ans)), body, ld=ld, vis=fig)
        ENG_OK.add(code); BMW_URLS.append(path)
        return dict(code=code, years=f'{y0}–{y1}', y0=int(y0), y1=int(y1), fams=fams, models=models_s, b=scored_b, a=scored_a, comb=comb_only, n=len(ys), txt=txt_total,
                    yt=(int(sum(yt_scores.values()) / len(yt_scores) + 0.5) if yt_scores else None, len(yt_scores)),   # 11-11: half-up, so 50.5 shows 51 and matches the rank order
                    bavg=(round(sum(v for k, v in own.values() if k == 'b') / max(1, sum(1 for k, _ in own.values() if k == 'b')))) if any(k == 'b' for k, _ in own.values()) else None)
    YP_IDS = {f['id'] for f in YEARS}
    import collections
    STATS = [s for s in (_engine_page(c) for c in BENG) if s]
    # hub
    if STATS:
        # 11-10 (Elijah): rank by OWNER COMPLAINTS (per-car whole-car score where one engine owned the model-year, lower = fewer complaints per car sold);
        # YouTube tone is its own column, never mixed into the rank. Engines without a per-car score are listed after, unranked.
        ranked = sorted([s for s in STATS if s['bavg'] is not None], key=lambda s: s['bavg'])
        rest = sorted([s for s in STATS if s['bavg'] is None], key=lambda s: s['years'])
        # 11-10 (Elijah: the 8-column table wrapped one word per line on phones, "should have the engine images"):
        # a card grid with each engine's illustration, plus filter pills and a sort. Every card is in the HTML (crawlable); assets/enghub.js only filters/sorts.
        def _kind(code):
            m = BENG[code]; lay = m['layout']; asp = m['asp']
            cyl = '4' if 'inline-4' in lay else '6' if 'inline-6' in lay else '8' if 'V8' in lay else ''
            tur = 'twin-turbo' if 'twin-turbo' in asp else 'turbo' if 'turbo' in asp else ''
            return cyl, tur
        _YTI = '<svg aria-hidden="true" viewBox="0 0 24 24" width="11" height="11"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>'
        def _card(s, rk, eager):
            code = s['code']; m = BENG[code]; cyl, tur = _kind(code); ph = BPH.get(code)
            typ = f'{m["size"]} {m["layout"]}' + (f' {tur}' if tur else '')
            img = ''
            if ph:
                cr = ('Illustration (AI-generated), not a photo of a specific engine. '
                      f'Free to use under <a href="{CCBY}" rel="noopener license">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>') if ph.get('ai') \
                     else f'Photo: {E(ph.get("author", ""))} / <a href="{E(ph.get("page", ""))}" rel="noopener">Wikimedia Commons</a> ({E(ph.get("license", ""))})'
                th = ph['src'][:-5] + '-640.webp'   # 640 px copy for the cards (cards are <= 420 px wide); the 1200 px one stays on the engine page
                src, w, h = (th, 640, round(ph['h'] * 640 / ph['w'])) if ph['src'].endswith('.webp') and os.path.exists(th.lstrip('/')) else (ph['src'], ph['w'], ph['h'])
                img = (f'<div class="ehc-im"><img src="{E(src)}" width="{w}" height="{h}" alt="BMW {E(code)} {E(m["size"])} {E(m["layout"])} engine" '
                       + ('fetchpriority="high" decoding="async">' if eager else 'loading="lazy" decoding="async">') + f'{YSL.info(cr)}</div>')
            if s['bavg'] is not None:
                b = s['bavg']; cls = 'good' if b < 90 else 'bad' if b > 115 else 'mid'
                main = f'<p class="ehc-n {cls}"><b>{b}</b><span>owner complaints per car<br>100 = average car</span></p>'
            else:
                main = f'<p class="ehc-n none"><b>–</b><span>no per-car score<br>{s["txt"]:,} complaints name it</span></p>'
            yt = (f'YouTube tone <b>{s["yt"][0]}</b> <small>· {s["yt"][1]} scored years</small>' if s['yt'][0] is not None else 'YouTube: <small>not enough videos</small>')
            fams = [BFAM.get(f, f).replace('BMW ', '') for f in s['fams']]
            chips = ''.join(f'<li>{E(f)}</li>' for f in fams[:6]) + (f'<li class="more">+{len(fams) - 6} more</li>' if len(fams) > 6 else '')
            return (f'<li class="ehc" data-rank="{rk if rk else 999}" data-own="{s["bavg"] if s["bavg"] is not None else 9999}" data-yt="{s["yt"][0] if s["yt"][0] is not None else -1}" '
                    f'data-y0="{s["y0"]}" data-y1="{s["y1"]}" data-cyl="{cyl}" data-turbo="{1 if tur else 0}" data-m="{1 if code.startswith("S") else 0}">'
                    + img + f'<span class="ehc-rk" title="Rank by owner complaints">{"#" + str(rk) if rk else "Unranked"}</span>'
                    + (f'<span class="ytbadge ehc-yr" title="YouTube rank by tone, of {len(_ytr)} engines with enough videos">{_YTI}YT #{_ytr[code]}</span>' if code in _ytr
                       else f'<span class="ytbadge ehc-yr na" title="Not enough YouTube videos to rank">{_YTI}YT –</span>')
                    + f'<h2><a class="ehc-a" href="{ENG_URL(code)}">{E(code)}</a></h2><p class="ehc-t">{E(typ)} · {E(s["years"])}</p>'
                    + main + f'<p class="ehc-yt">{yt}</p><ul class="ehc-cars" aria-label="Cars with the {E(code)}">{chips}</ul></li>')
        _ytr = _YTRANK   # 11-11: same ranking as each engine page's badge (was ranked separately here and could disagree)
        cards = [_card(s, i + 1, i == 0) for i, s in enumerate(ranked)] + [_card(s, None, False) for s in rest]
        kinds = [(_kind(s['code']), s['code']) for s in STATS]
        pills = [('all', 'All')] + [(k, lab) for k, lab, ok in (('4', '4-cylinder', any(c == '4' for (c, _), _x in kinds)), ('6', '6-cylinder', any(c == '6' for (c, _), _x in kinds)),
                 ('8', 'V8', any(c == '8' for (c, _), _x in kinds)), ('m', 'M engines', any(x.startswith('S') for _k, x in kinds)),
                 ('turbo', 'Turbo', any(t for (_, t), _x in kinds)), ('na', 'Non-turbo', any(not t for (_, t), _x in kinds))) if ok]
        ans = ('Owners file government complaints by model and year, not engine, so we rank only where the data leaves no doubt: model years where one engine was the only engine in a model we have sales for. '
               + (f'By owner complaints per car sold, the {ranked[0]["code"]} ranks best ({ranked[0]["bavg"]}) and the {ranked[-1]["code"]} worst ({ranked[-1]["bavg"]}) of the {len(ranked)} engines we can score that way (100 = average car, lower is better; it counts complaints about the whole car, not just the engine). ' if len(ranked) >= 2 else '')
               + 'YouTube tone is shown separately. Each engine page breaks it down by model year.')
        short = (f'The {ranked[0]["code"]} draws the fewest owner complaints per car, the {ranked[-1]["code"]} the most. Tap an engine for every year.' if len(ranked) >= 2 else 'Tap an engine for every year.')
        method = ('Rank = owner complaints per car sold (the Lemon Index: complaints about any part of the car, per car sold, 100 = average car, lower is better), '
                  'averaged over the model years where this was the only engine in a model we have sales for. Engines with no such year are listed after, unranked. '
                  'Government complaints are filed by model and year, not engine. YouTube tone = how positive the videos are (0–100), averaged over the scored years; it is not part of the rank. '
                  'None of these is an engine failure rate. Images: AI illustrations, free to use under CC BY 4.0.')
        body = (f'<div class="advp ehub"><header class="advh1"><p class="ph-e"><a href="/brands/bmw/">BMW</a></p><h1>BMW engines, ranked by owner complaints.</h1>'
                f'<p class="ans">{E(short)} <span class="ehub-i">{YSL.info(E(method))}</span></p></header>'
                '<div class="ehub-bar"><div class="ehub-f" role="group" aria-label="Show">'
                + ''.join(f'<button type="button" class="ehub-p" data-f="{k}" aria-pressed="{"true" if k == "all" else "false"}">{lab}</button>' for k, lab in pills)
                + '</div><label class="ehub-s">Sort <select id="ehub-sort"><option value="own">Owner complaints</option><option value="new">Newest</option>'
                  '<option value="old">Oldest</option><option value="yt">YouTube tone</option></select></label></div>'
                + f'<p class="ehub-c" aria-live="polite">{len(cards)} engines</p><ol class="ehub-g">{"".join(cards)}</ol>'
                + share_line('Every BMW engine ranked by owner complaints, year by year. Free:') + '</div><script src="/assets/enghub.js?v=1" defer></script>')
        faq = [('Which BMW engine is the most reliable?', ans)]
        page('/engines/bmw/', 'BMW Engines Ranked by Owner Complaints (N54, B58 & More)', ans, body, ld=[faq_ld([(q, '', a) for q, a in faq])]); BMW_URLS.insert(0, '/engines/bmw/')
    # ---- new BMW model pages (no sales -> no Lemon Index; complaints, specs, engines)
    for fid, m in BNEW.items():
        if fid in BYNAME_ID: continue
        nm = E(m['name']); path = f'/cars/{fid}/'
        by = {int(k): v for k, v in m['by_year'].items()}; wy = max(by, key=by.get) if by and max(by.values()) else None
        codes = sorted({v['code'] for y in BVER.get(fid, {}) for v in BVER[fid][y] if v.get('code')})
        top = m['parts'][0][0] if m['parts'] else ''
        ans = (f'Owners filed <b>{m["n"]:,} complaints</b> about the {m["a"]}–{m["b"]} {nm} with the government' + (f', most about {E(top)}' if top else '')
               + (f'. The {wy} drew the most, with {by[wy]:,}' if wy else '') + '.' + (f' Engines: {", ".join(f"<a href=\"{ENG_URL(c)}\">{E(c)}</a>" for c in codes if c in ENG_OK)}.' if codes else ''))
        yr = [[y, f'{by[y]:,}', ', '.join(f'<a href="{ENG_URL(c)}">{E(c)}</a>' if c in ENG_OK else E(c) for c in (BFY.get(f'{fid}|{y}') or {}).get('codes', [])) or '<small>not confirmed / electric</small>',
               ', '.join(E(p) for p, _ in m['yparts'].get(str(y), [])[:2]) or '—'] for y in sorted(by)]
        sec = [f'<section class="yc" id="years"><h2>Complaints by model year</h2>' + _rows(['Model year', 'Complaints', 'Engines', 'Top areas'], yr)
               + '<p class="yc-cap">We don&#39;t have US sales for this model yet, so there&#39;s no Lemon Index: popular years draw more complaints partly because more were sold.</p></section>']
        if m['parts']: sec.append('<section class="yc" id="problems"><h2>What owners complain about</h2>' + _rows(['System', 'Share of complaints'], [[E(p).capitalize(), f'{k}%'] for p, k in m['parts']]) + '</section>')
        if m.get('miles'): g = m['miles']; sec.append(f'<section class="yc"><h2>When problems show up</h2><p>Half of the owners who gave a mileage reported the problem between <b>{g["p25"]:,}</b> and <b>{g["p75"]:,}</b> miles (middle: {g["median"]:,}, from {g["n"]:,} complaints).</p></section>')
        sec.append('<section class="yc"><h2>How serious</h2>' + _rows(['Crashes', 'Fires', 'Injury reports', 'Death reports'], [[f'{m["crash"]:,}', f'{m["fire"]:,}', f'{m["injured"]:,}', f'{m["deaths"]:,}']]) + '<p class="yc-cap">As reported by owners to NHTSA. Not verified.</p></section>')
        if m['recalls']:
            sec.append(f'<section class="yc" id="recalls"><h2>Recalls we found <span class="yc-n">{len(m["recalls"])}</span></h2><ul class="advr">' + ''.join(
                f'<li><p class="advh"><a href="https://www.nhtsa.gov/recalls?nhtsaId={E(r["id"])}" target="_blank" rel="noopener nofollow">{E(r["id"])}</a> <small>{E(r["date"])} · {E(", ".join(str(y) for y in r["years"]))}</small></p><p>{E(r["part"])}</p></li>' for r in m['recalls'][:25])
                + '</ul><p class="yc-cap">From NHTSA&#39;s recall lookup by model name and year; check a car&#39;s VIN for its own open recalls.</p></section>')
        sec.append(SPECS_HOOK(fid))
        faq = [(f'What are the most common {m["name"]} problems?', f'In owner complaints to the government, the top areas are {", ".join(p for p, _ in m["parts"][:3])}.' if m['parts'] else 'There are too few complaints to say.')]
        if codes: faq.append((f'What engines does the {m["name"]} have?', 'By model year: ' + '; '.join(f'{y}: {", ".join((BFY.get(f"{fid}|{y}") or {}).get("codes", [])) or "not confirmed"}' for y in sorted(by)[-6:]) + '. Full list in the specs table.'))
        sec.append('<section class="yc yqa"><h2>Quick answers</h2>' + ''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq) + '</section>')
        body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/cars/">All cars</a> · <a href="/brands/bmw/">BMW</a></p><h1>{nm} reliability: problems, specs and engines by year.</h1><p class="ans">{ans}</p></header>' + (lambda h: f'<div class="advimg">{h}</div>' if h else '')(YSL.model_hero_html(fid, m["name"])) +
                f'<div class="ygrid">{"".join(sec)}</div>' + share_line(f'{m["name"]}: owner complaints, specs and engines by year. Free:') + '</div>')
        page(path, seo_title([f'{m["name"]} Reliability: Problems, Specs & Engines', f'{m["name"]} Reliability by Year', f'{m["name"]} Reliability']), _html.unescape(re.sub('<[^>]+>', '', ans)), body, ld=[faq_ld([(q, '', a) for q, a in faq])])
        if m['n'] < 20: _noindex(path)
        else: BMW_URLS.append(path)
    # ---- links in from the BMW brand page and the cars index
    links = ('<section class="yc"><h2>More BMW models, specs and engines</h2><p class="chips">' + ''.join(f'<a class="chip" href="/cars/{fid}/">{E(m["name"].replace("BMW ", ""))}</a>' for fid, m in BNEW.items() if fid not in BYNAME_ID and m['n'] >= 20)
             + '</p><p class="chips">' + ''.join(f'<a class="chip" href="{ENG_URL(c)}">{E(c)} engine</a>' for c in sorted(ENG_OK)) + '</p><p><a class="btn" href="/engines/bmw/">Every BMW engine, year by year →</a></p></section>')
    for f_ in ('docs/brands/bmw/index.html',):
        if os.path.exists(f_):
            s = open(f_, encoding='utf-8').read()
            if 'More BMW models, specs and engines' not in s: open(f_, 'w', encoding='utf-8').write(s.replace('</main>', links + '</main>', 1))
    # ---- /images/: our free engine illustrations, CC BY 4.0, with copy-paste credit text (the acquireLicensePage in the ImageObject markup)
    ours = [(p, ph) for p, ph in IMG_PAGES if ph.get('ai')]
    if ours:
        # 11-10 v2 (design audit: /images/ was 155,000 px tall): small thumbnail cards (name + full size + where it's used), the credit line
        # once at the top, jump links per group, a text filter, and only the first 12 of each group shown until "Show all" (assets/imgpage.js).
        # Every card stays in the HTML, so the page still lists every image for search engines.
        def card(src, w, h, alt, name, use_url, use_txt, extra=''):
            return (f'<figure class="imgcard"><a class="ic-i" href="{E(src)}"><img src="{E(src)}" width="{w}" height="{h}" alt="{E(alt)}" loading="lazy" decoding="async"></a>'
                    f'<figcaption><b>{E(name)}</b>{extra}<span><a href="{E(src)}">Full size</a>' + (f' · <a href="{use_url}">{E(use_txt)}</a>' if use_url else '') + '</span></figcaption></figure>')
        groups = []
        groups.append(('engines', 'BMW engines', [card(ph['src'], ph['w'], ph['h'], ph['title'], ph['title'], p_, 'Engine page') for p_, ph in ours]))
        if globals().get('SCE_IMGS'): groups.append(('supercar-engines', 'Supercar and performance engines', [card(ph['src'], ph['w'], ph['h'], ph['title'], ph['title'], p_, 'Engine page') for p_, ph in SCE_IMGS]))   # 11-11 (supercar_engine_pages.py)
        _ES = json.load(open('data/engine_soon_images.json', encoding='utf-8')) if os.path.exists('data/engine_soon_images.json') else {}   # 11-12 /engines/ coming-soon engines
        if _ES: groups.append(('engines-coming-soon', 'More engines (pages coming soon)', [card(ph['src'], ph['w'], ph['h'], ph['title'], ph['title'], '/engines/?type=soon', 'All engines') for _k, ph in sorted(_ES.items())]))
        _pages = {f['id'] for f in YEARS}
        if YSL.AIM:
            groups.append(('models', 'Every car model', [card(m['src'], m['w'], m['h'], f'{m["year"]} {m["name"]} illustration', f'{m["year"]} {m["name"]}',
                                                              f'/cars/{_fid}/' if _fid in _pages else m.get('page'), 'Model page')
                                                         for _fid, m in sorted(YSL.AIM.items(), key=lambda kv: kv[1]['name'])]))
        _AIV = json.load(open('data/ai_vehicle_images.json', encoding='utf-8')) if os.path.exists('data/ai_vehicle_images.json') else {}
        for _c, _t in (('motorcycle', 'Motorcycles'), ('supercar', 'Supercars'), ('plane', 'Planes and helicopters')):
            L = [card(v['src'], v['w'], v['h'], f'{v["year"]} {v["name"]} illustration', f'{v["year"]} {v["name"]}', v['page'], 'Page') for _fam, v in sorted(_AIV.items(), key=lambda kv: kv[1]['name']) if v['category'] == _c]
            if L: groups.append((_c + 's', _t, L))
        _PF = [c for c in (json.load(open('data/perf_cars.json', encoding='utf-8')) if os.path.exists('data/perf_cars.json') else []) if isinstance(c, dict) and c.get('img')]   # 11-11 coming-soon performance cars
        if _PF: groups.append(('performance', 'Performance cars, supercars and hypercars', [card(c['img'], c.get('w', 1000), c.get('h', 600), f'{c["name"]} illustration', c['name'], '/cars/?type=' + ('supercars' if c.get('group') in ('B', 'C') else 'performance'), 'Cars page (coming soon)') for c in _PF]))
        _MS = [c for c in (json.load(open('data/moto_soon.json', encoding='utf-8')) if os.path.exists('data/moto_soon.json') else []) if c.get('img')]   # 11-11 coming-soon motorcycles
        if _MS: groups.append(('motorcycles-soon', 'Motorcycles (coming soon)', [card(c['img'], c['w'], c['h'], f'{c["name"]} illustration', c['name'], '/motorcycles/', 'Motorcycles page (coming soon)') for c in _MS]))
        _names = {f['id']: f['name'] for f in YEARS}; _yp = {f['id']: {v['y'] for v in f['years']} for f in YEARS}
        _gen = []   # 11-10: one picture per generation for every model
        for _fid, _ims in sorted(YSL.AIY.items(), key=lambda kv: _names.get(kv[0], kv[0])):
            _grp, _ms = {}, (YSL.AIM.get(_fid) or {}).get('src')
            for _y, _im in sorted(_ims.items(), key=lambda kv: int(kv[0])): _grp.setdefault(_im['src'], []).append(int(_y))
            if not (any(len(v) > 1 for v in _grp.values()) or _ms in _grp): continue
            _nm = _names.get(_fid, _fid.replace('-', ' ').title())
            for _s, _v in _grp.items():
                if _s == _ms: continue
                _im, _lab = _ims[str(_v[0])], (f'{_v[0]}' if len(_v) == 1 else f'{_v[0]}-{_v[-1]}')
                _gen.append(card(_im['src'], _im['w'], _im['h'], f'{_lab} {_nm} illustration', f'{_lab} {_nm}', f'/cars/{_fid}/{_v[0]}/', 'Year page', f'<small>{E(_im["gen"])}</small>'))
        if _gen: groups.append(('generations', 'Every car generation', _gen))
        for _fid, _ims in sorted(YSL.AIY.items()):
            _ss = {_im['src'] for _im in _ims.values()}
            if len(_ss) < len(_ims) or (YSL.AIM.get(_fid) or {}).get('src') in _ss: continue   # shown above (one card per generation) or under Every car model
            _nm = _names.get(_fid, _fid.replace('-', ' ').title())
            groups.append((f'years-{_fid}', f'{_nm}, every year', [card(im['src'], im['w'], im['h'], f'{y} {_nm} illustration', f'{y} {_nm}',
                                                                      f'/cars/{_fid}/{y}/' if int(y) in _yp.get(_fid, set()) else f'/cars/{_fid}/', 'Year page' if int(y) in _yp.get(_fid, set()) else 'Year slider',
                                                                      f'<small>{E(im["gen"])}</small>') for y, im in sorted(_ims.items(), key=lambda kv: int(kv[0]))]))
        total = sum(len(g[2]) for g in groups)
        jump = '<nav class="imgj" aria-label="Image groups">' + ''.join(f'<a href="#g-{gid}">{E(t)} <span>{len(L)}</span></a>' for gid, t, L in groups) + '</nav>'
        secs = ''.join(f'<section class="yc imgsec" id="g-{gid}"><h2>{E(t)} <span class="h2s">{len(L)} images</span></h2><div class="imggrid ig2" data-cap="12">{"".join(L)}</div></section>' for gid, t, L in groups)
        lede = (f'{total} illustrations we made for the Lemon Index: cars, engines (BMW and supercar), motorcycles, supercars and planes. Free to use anywhere, including commercially, under CC BY 4.0. '
                'They are AI-generated, not photos of a specific vehicle.')
        body = (f'<div class="advp imgp"><header class="advh1"><p class="ph-e"><a href="/data/">Free data</a></p><h1>Free car and engine illustrations.</h1><p class="ans">{E(lede)}</p></header>'
                f'<section class="yc imgcr"><h2>How to credit</h2><p>Put this line next to the image: <code>Image: The Lemon Index (lemonindex.com), CC BY 4.0</code>, '
                f'and link "CC BY 4.0" to <a href="{CCBY}" rel="noopener license" style="overflow-wrap:anywhere">{CCBY}</a>. If you change the image, say so.</p></section>'
                f'{jump}<input class="cf-q imgq" type="search" placeholder="Find an image, e.g. Civic or N54" aria-label="Find an image">'
                f'<p class="cf-none imgnone" hidden>No image matches.</p>{secs}' + (f'<section class="yc imgsec">{TAB.images_cards()}</section>' if TAB.images_cards() else '') +
                '<p class="yc-cap">Engine photos on our engine pages that come from Wikimedia Commons are not ours: they keep their authors&#39; own licenses, linked under each photo.</p></div>'
                '<script src="/assets/imgpage.js?v=1" defer></script>')
        page('/images/', 'Free Car & Engine Illustrations (CC BY 4.0) | Lemon Index', lede, body, ld=[img_ld(p.split('bmw-')[1].strip('/').upper(), ph) for p, ph in ours] + [dict(img_ld('', ph), name=ph['title'], description=ph['title'] + '. AI-generated illustration, not a photo of a specific engine.') for p, ph in globals().get('SCE_IMGS', [])])
        BMW_URLS.append('/images/')
    # ---- image sitemap (listed in robots.txt by build.py)
    _PFS = [c for c in (json.load(open('data/perf_cars.json', encoding='utf-8')) if os.path.exists('data/perf_cars.json') else []) if isinstance(c, dict) and c.get('img')]   # 11-11: the coming-soon performance cards on /cars/
    open(os.path.join(OUT, 'image-sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
        + ''.join(f'<url><loc>{BASE}{p}</loc><image:image><image:loc>{BASE}{E(ph["src"])}</image:loc></image:image></url>' for p, ph in IMG_PAGES)
        + ''.join(f'<url><loc>{BASE}/cars/{_f}/{y}/</loc><image:image><image:loc>{BASE}{E(im["src"])}</image:loc></image:image></url>'
                  for _f, _ii in YSL.AIY.items() for y, im in _ii.items() if int(y) in {v['y'] for f in YEARS if f['id'] == _f for v in f['years']})
        + ''.join(f'<url><loc>{BASE}{pg}</loc><image:image><image:loc>{BASE}{E(src)}</image:loc></image:image></url>' for pg, src in TAB.sitemap_images())
        + ''.join(f'<url><loc>{BASE}/cars/{_f}/</loc><image:image><image:loc>{BASE}{E(m["src"])}</image:loc></image:image></url>'
                  for _f, m in YSL.AIM.items() if _f in {f['id'] for f in YEARS} and not YSL.has(_f))
        + ''.join(f'<url><loc>{BASE}{m["page"]}</loc><image:image><image:loc>{BASE}{E(m["src"])}</image:loc></image:image></url>'
                  for _f, m in YSL.AIM.items() if m.get('page') and _f not in {f['id'] for f in YEARS})
        + ''.join(f'<url><loc>{BASE}{v["page"]}</loc><image:image><image:loc>{BASE}{E(v["src"])}</image:loc></image:image></url>'
                  for v in (json.load(open('data/ai_vehicle_images.json', encoding='utf-8')) if os.path.exists('data/ai_vehicle_images.json') else {}).values())
        + ''.join(f'<url><loc>{BASE}{p}</loc><image:image><image:loc>{BASE}{E(ph["src"])}</image:loc></image:image></url>' for p, ph in globals().get('SCE_IMGS', []))   # 11-11 supercar engines
        + (f'<url><loc>{BASE}/cars/</loc>' + ''.join(f'<image:image><image:loc>{BASE}{E(c["img"])}</image:loc></image:image>' for c in _PFS) + '</url>' if _PFS else '')
        + (lambda _M: f'<url><loc>{BASE}/motorcycles/</loc>' + ''.join(f'<image:image><image:loc>{BASE}{E(c["img"])}</image:loc></image:image>' for c in _M) + '</url>' if _M else '')([c for c in (json.load(open('data/moto_soon.json', encoding='utf-8')) if os.path.exists('data/moto_soon.json') else []) if c.get('img')])
        + (''.join(f'<url><loc>{BASE}/images/</loc>' + ''.join(f'<image:image><image:loc>{BASE}{E(ph["src"])}</image:loc></image:image>' for _, ph in ours + list(globals().get('SCE_IMGS', []))) + '</url>' for _ in [0]) if ours else '')
        + '</urlset>')
    print('bmw pages', len(BMW_URLS), 'engines', len(ENG_OK), 'engine images', len(IMG_PAGES), 'ours (CC BY)', len(ours))
