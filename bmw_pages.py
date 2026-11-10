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
    def _yt_cell(code, y):
        d = (BYT.get(code) or {}).get(str(y))
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
    def _engine_page(code):
        meta = BENG[code]; yrs = BEY.get(code) or {}
        if not yrs: return None
        ys = sorted(yrs, key=int); y0, y1 = ys[0], ys[-1]
        fams = sorted({f for y in ys for f in yrs[y]['models']}, key=lambda f: BFAM.get(f, f))
        hp = sorted({v['hp'] for f in BVER for y in BVER[f] for v in BVER[f][y] if v.get('code') == code and v.get('hp')})
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
        sec = []
        sec.append('<section class="yc engt"><h2>Reliability by year. <span class="h2s">Owner complaints and YouTube, per model year this engine was sold.</span></h2>'
                   + _rows(['Year', 'Cars with it', 'Owner complaints', f'Complaints naming "{E(code)}"', 'YouTube says', 'Top complaint areas'], rows)
                   + (f'<p>{bline}</p>' if bline else '') + (f'<p>{yline}</p>' if yline else '') + (f'<p>{agree}</p>' if agree else '')
                   + '<p class="yc-cap">How each number is matched to the engine: <b>(a)</b> complaints filed under a version name that used only this engine that year (e.g. "335I"); '
                   '<b>(b)</b> the model had only this engine that year, so its Lemon Index (complaints per car sold vs the average car) applies to every car with this engine; '
                   '"all engines combined" = the model had several engines under one name, so its number is not this engine&#39;s alone. '
                   'Owner complaints in (a) and (b) cover the whole car (brakes, air bags, electrics ...), not only the engine: see the top complaint areas. '
                   f'Complaints naming "{E(code)}" = complaints whose own text mentions the code, about a model and year that had it. None of these is a failure rate. '
                   'YouTube says = how positive the videos are, 0–100 (higher = more positive), from video titles and transcripts, counted only where the title names the engine or a version that used it. '
                   'A video whose title names no model year counts toward every year of its generation, so neighboring years share most of their videos; "naming" = how many titles name that year. Under 3 videos&#39; worth shows "not enough videos".</p></section>')
        if meta.get('notes'):
            sec.append(f'<section class="yc"><h2>Known issues on record</h2><ul>' + ''.join(f'<li>{E(n)}</li>' for n in meta['notes'])
                       + f'</ul><p class="yc-cap">According to <a href="{E(meta["src"])}" rel="noopener">Wikipedia&#39;s {E(meta["name"])} article</a> and its sources.</p></section>')
        vers = collections.OrderedDict()
        for f in BVER:
            for y in sorted(BVER[f], key=int):
                for v in BVER[f][y]:
                    if v.get('code') == code: vers.setdefault((f, v['model'], v.get('hp'), v.get('tq')), []).append(int(y))
        vr = [[_fam_link(f), E(m), f'{min(yl)}–{max(yl)}' if len(yl) > 1 else str(yl[0]), f'{hp_} hp' if hp_ else '—', f'{tq} lb-ft' if tq else '—'] for (f, m, hp_, tq), yl in vers.items()]
        sec.append('<section class="yc"><h2>Every US version with this engine</h2>' + _rows(['Model', 'Version', 'Model years', 'Power', 'Torque'], vr)
                   + f'<p class="yc-cap">Versions and years: EPA (fueleconomy.gov). Engine and power: <a href="{E(meta["src"])}" rel="noopener">Wikipedia, {E(meta["name"])}</a> (BMW ratings; US figures can differ by a few hp).</p></section>')
        faq = [(f'What cars have the {meta["name"]} engine?', f'In the US: the {models_s}, model years {y0}–{y1}. See the version table for each one.'),
               (f'Is the {code} reliable?', (re.sub('<[^>]+>', '', bline) + ' ' if bline else '') + 'Government complaints are filed by model and year, not engine, and they cover the whole car, so none of these numbers is an engine failure rate. We only credit a number to this engine where the version name or the model year leaves no doubt. Have any used car inspected.')]
        if hp: faq.append((f'How much horsepower does the {code} make?', f'BMW rated it at {hp[0]}' + (f' to {hp[-1]}' if len(hp) > 1 else '') + ' hp in US versions, depending on the car and year.'))
        sec.append('<section class="yc yqa"><h2>Quick answers</h2>' + ''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faq) + '</section>')
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
        body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/engines/bmw/">BMW engines</a> · <a href="/brands/bmw/">BMW</a></p>'
                f'<h1>BMW {E(code)} engine: reliability by year, specs and the cars that have it.</h1><p class="ans">{ans}</p>{fig}</header><div class="ygrid">{"".join(sec)}</div>'
                + share_line(f'BMW {code} engine reliability, year by year. Free:') + '</div>')
        title = next(t for t in (f'BMW {code} Engine Reliability by Year, Specs & Cars', f'BMW {code} Engine: Reliability by Year & Specs', f'BMW {code} Engine Reliability') if len(t) <= 65)
        ld = [faq_ld([(q, '', a) for q, a in faq])]
        if ph and ph.get('ai'): ld.append(img_ld(code, ph)); IMG_PAGES.append((path, ph))
        elif ph: IMG_PAGES.append((path, ph))
        page(path, title, _html.unescape(re.sub('<[^>]+>', '', ans)), body, ld=ld)
        ENG_OK.add(code); BMW_URLS.append(path)
        return dict(code=code, years=f'{y0}–{y1}', models=models_s, b=scored_b, a=scored_a, comb=comb_only, n=len(ys), txt=txt_total,
                    yt=(round(sum(yt_scores.values()) / len(yt_scores)) if yt_scores else None, len(yt_scores)),
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
        def _row(s, rk):
            return [rk, f'<a href="{ENG_URL(s["code"])}">{E(s["code"])}</a>', E(BENG[s["code"]]["size"]) + ' ' + E(BENG[s["code"]]["layout"]) + (' turbo' if 'turbo' in BENG[s["code"]]['asp'] else ''),
                    s['years'], E(s['models']),
                    (f'<b>{s["bavg"]}</b>' if s['bavg'] is not None else '<small>no single-engine year with sales</small>'),
                    f'{s["txt"]:,}',
                    (f'{s["yt"][0]} <small>({s["yt"][1]} scored yrs)</small>' if s['yt'][0] is not None else '<small>not enough videos</small>')]
        hr = [_row(s, str(i + 1)) for i, s in enumerate(ranked)] + [_row(s, '–') for s in rest]
        ans = ('Owners file government complaints by model and year, not engine, so we rank only where the data leaves no doubt: model years where one engine was the only engine in a model we have sales for. '
               + (f'By owner complaints per car sold, the {ranked[0]["code"]} ranks best ({ranked[0]["bavg"]}) and the {ranked[-1]["code"]} worst ({ranked[-1]["bavg"]}) of the {len(ranked)} engines we can score that way (100 = average car, lower is better; it counts complaints about the whole car, not just the engine). ' if len(ranked) >= 2 else '')
               + 'YouTube tone is shown separately. Each engine page breaks it down by model year.')
        body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/brands/bmw/">BMW</a></p><h1>BMW engines ranked by owner complaints, with specs and the cars that have them.</h1><p class="ans">{E(ans)}</p></header>'
                '<div class="ygrid"><section class="yc">' + _rows(['Rank', 'Engine', 'Type', 'US model years', 'Cars', 'Owner complaints per car (whole car)', 'Complaints naming it', 'YouTube tone'], hr)
                + '<p class="yc-cap">Rank = owner complaints per car sold (the Lemon Index: complaints about any part of the car, per car sold, 100 = average car, lower is better), averaged over the model years where this was the only engine in a model we have sales for. '
                  'Engines with no such year are listed after, unranked. Complaints naming it = NHTSA complaints whose text mentions the engine code, about a model and year that had it. '
                  'YouTube tone = how positive the videos are (0–100, higher = more positive), averaged over the scored years; it is not part of the rank. None of these is an engine failure rate.</p></section></div>'
                + share_line('Every BMW engine ranked by owner complaints, year by year. Free:') + '</div>')
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
        body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/cars/">All cars</a> · <a href="/brands/bmw/">BMW</a></p><h1>{nm} problems, specs and engines by year.</h1><p class="ans">{ans}</p></header>'
                f'<div class="ygrid">{"".join(sec)}</div>' + share_line(f'{m["name"]}: owner complaints, specs and engines by year. Free:') + '</div>')
        page(path, f'{m["name"]} Problems, Specs & Engines by Year', _html.unescape(re.sub('<[^>]+>', '', ans)), body, ld=[faq_ld([(q, '', a) for q, a in faq])])
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
        cards = ''.join(
            f'<figure class="imgcard"><img src="{E(ph["src"])}"{rset(ph["src"], "(max-width: 700px) 100vw, 340px")} width="{ph["w"]}" height="{ph["h"]}" alt="{E(ph["title"])}" loading="lazy">'
            f'<figcaption><b>{E(ph["title"])}</b><span>{ph["w"]}×{ph["h"]} WebP · {ph.get("bytes", 0) // 1024} KB · Illustration (AI-generated), not a photo of a specific engine.</span>'
            f'<span>Credit: <code>Image: The Lemon Index (lemonindex.com), CC BY 4.0</code></span>'
            f'<span><a href="{E(ph["src"])}">Open full size</a> · <a href="{p}">Used on: BMW {E(p.split("bmw-")[1].strip("/").upper())} engine page</a></span></figcaption></figure>' for p, ph in ours)
        lede = ('Engine illustrations we made for the Lemon Index. You may use them anywhere, including commercially, under Creative Commons Attribution 4.0 (CC BY 4.0), '
                'as long as you credit "The Lemon Index (lemonindex.com)" and link to the license. They are AI-generated illustrations, not photos of a specific engine.')
        # 11-10: the year-by-year car illustrations (year_slider.py / data/ai_year_images.json) are listed here too
        _names = {f['id']: f['name'] for f in YEARS}; _yp = {f['id']: {v['y'] for v in f['years']} for f in YEARS}
        car_cards = ''
        for _fid, _ims in sorted(YSL.AIY.items()):
            _nm = _names.get(_fid, _fid.replace('-', ' ').title())
            car_cards += (f'<h2>{E(_nm)}, every year</h2><div class="imggrid">' + ''.join(
                f'<figure class="imgcard"><img src="{E(im["src"])}" width="{im["w"]}" height="{im["h"]}" alt="{y} {E(_nm)} illustration" loading="lazy">'
                f'<figcaption><b>{y} {E(_nm)}</b><span>{E(im["gen"])} · Illustration (AI-generated), typical color of the era.</span>'
                f'<span>Credit: <code>Image: The Lemon Index (lemonindex.com), CC BY 4.0</code></span>'
                f'<span><a href="{E(im["src"])}">Open full size</a> · <a href="/cars/{_fid}/{y}/" >Used on: {y} {E(_nm)}</a></span></figcaption></figure>'
                if int(y) in _yp.get(_fid, set()) else
                f'<figure class="imgcard"><img src="{E(im["src"])}" width="{im["w"]}" height="{im["h"]}" alt="{y} {E(_nm)} illustration" loading="lazy">'
                f'<figcaption><b>{y} {E(_nm)}</b><span>{E(im["gen"])} · Illustration (AI-generated), typical color of the era.</span>'
                f'<span>Credit: <code>Image: The Lemon Index (lemonindex.com), CC BY 4.0</code></span>'
                f'<span><a href="{E(im["src"])}">Open full size</a> · <a href="/cars/{_fid}/#every-year">Used on: the {E(_nm)} year slider</a></span></figcaption></figure>'
                for y, im in sorted(_ims.items(), key=lambda kv: int(kv[0]))) + '</div>')
        lede = ('Car and engine illustrations we made for the Lemon Index. You may use them anywhere, including commercially, under Creative Commons Attribution 4.0 (CC BY 4.0), '
                'as long as you credit "The Lemon Index (lemonindex.com)" and link to the license. They are AI-generated illustrations, not photos of a specific car or engine.')
        body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/data/">Free data</a></p><h1>Free car and engine illustrations.</h1><p class="ans">{E(lede)}</p></header>'
                f'<div class="ygrid"><section class="yc"><h2>BMW engines</h2><div class="imggrid">{cards}</div></section>'
                f'<section class="yc">{car_cards}</section>'
                + (f'<section class="yc">{TAB.images_cards()}</section>' if TAB.images_cards() else '') +
                f'<section class="yc"><h2>How to credit</h2><p>Copy this line next to the image: <code>Image: The Lemon Index (lemonindex.com), CC BY 4.0</code>, '
                f'and link "CC BY 4.0" to <a href="{CCBY}" rel="noopener license" style="overflow-wrap:anywhere">{CCBY}</a>. If you change the image, say so.</p>'
                '<p class="yc-cap">Engine photos on our engine pages that come from Wikimedia Commons are not ours: they keep their authors&#39; own licenses, linked under each photo.</p></section></div></div>')
        page('/images/', 'Free Car & Engine Illustrations (CC BY 4.0) | Lemon Index', lede, body, ld=[img_ld(p.split('bmw-')[1].strip('/').upper(), ph) for p, ph in ours])
        BMW_URLS.append('/images/')
    # ---- image sitemap (listed in robots.txt by build.py)
    open(os.path.join(OUT, 'image-sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
        + ''.join(f'<url><loc>{BASE}{p}</loc><image:image><image:loc>{BASE}{E(ph["src"])}</image:loc></image:image></url>' for p, ph in IMG_PAGES)
        + ''.join(f'<url><loc>{BASE}/cars/{_f}/{y}/</loc><image:image><image:loc>{BASE}{E(im["src"])}</image:loc></image:image></url>'
                  for _f, _ii in YSL.AIY.items() for y, im in _ii.items() if int(y) in {v['y'] for f in YEARS if f['id'] == _f for v in f['years']})
        + ''.join(f'<url><loc>{BASE}{pg}</loc><image:image><image:loc>{BASE}{E(src)}</image:loc></image:image></url>' for pg, src in TAB.sitemap_images())
        + (''.join(f'<url><loc>{BASE}/images/</loc>' + ''.join(f'<image:image><image:loc>{BASE}{E(ph["src"])}</image:loc></image:image>' for _, ph in ours) + '</url>' for _ in [0]) if ours else '')
        + '</urlset>')
    print('bmw pages', len(BMW_URLS), 'engines', len(ENG_OK), 'engine images', len(IMG_PAGES), 'ours (CC BY)', len(ours))
