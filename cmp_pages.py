# 11-12 (Elijah, desktop review of /compare/toyota-camry-vs-honda-civic/): the match-up page, rebuilt around what someone choosing
# between two cars wants to know, in this order:
#   1. who wins and WHY: both cars, "<car> wins because" + up to 3 data-backed reasons as cards (and where the other car is better)
#   2. a clean head-to-head scoreboard (value | label | value, nothing that can clip at any width) + one line on what the index is
#   3. which years of each to buy or avoid (the same picks as the model pages: good_years / avoid_years / rec_year)
#   4. year by year: one row per year, both cars side by side, newest first, "Your years" picker kept (assets/lfa.js reads .yrs .yr[data-a])
#   5. what breaks on each (complaint areas + owners' repair bills), recalls, what YouTube owners say (data/yt_buyer.json), our pick
# The old gray lede ("Toyota Camry or Honda Civic? Here's the Civic vs Camry question ...") stays in the HTML, inside "Where this comes from".
# Run by build.py with exec() (build.py's FY, BYNAME, extra, CARU, rec_year, good_years, avoid_years, worst_year, YTR, RCQ, TOPF ... in scope).
# Every number is from our data files; nothing is typed by hand. Classes: cb-* (assets/cb.css, shared with the /best/ pages).
CB_ASSET = '<link rel="stylesheet" href="/assets/cb.css?v=2">'
CB_JS = '<script src="/assets/cb.js?v=2" defer></script>'   # info popovers, sticky section nav, VIN box
# 11-13 v4 (Elijah: "the small gray text nobody reads"): explainers and sources live behind a small (i) button in each card's corner,
# a popover that opens on tap / click (hover on desktop), Esc closes. The text stays in the HTML, so every source is still on the page.
_CB_N = [0]
_CB_I = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round">'
         '<circle cx="12" cy="12" r="9.3" stroke-width="1.6"/><path d="M12 11v5.6" stroke-width="2"/><path d="M12 7.6h.01" stroke-width="2.6"/></svg>')
def cb_info(html_, label='How to read this', text=''):
    _CB_N[0] += 1; i = f'cbi{_CB_N[0]}'
    t = f'<span>{text}</span>' if text else ''
    return (f'<span class="cb-inf"><button type="button" class="cb-ib{" cb-ibt" if text else ""}" aria-label="{E(label)}" aria-expanded="false" aria-controls="{i}">{_CB_I}{t}</button>'
            f'<span class="cb-pop" id="{i}" role="note">{html_}</span></span>')
def cb_h2(id_, title, *corner):
    ida = f' id="{id_}"' if id_ else ''
    return f'<div class="cb-sh2"><h2{ida}>{title}</h2><div class="cb-sha">{"".join(corner)}</div></div>'
YBUY = _load('data/yt_buyer.json')   # 11-12 carousel agent's YouTube generation study (praise / complaints per generation); {} until it lands


def _cb_rec(F, years):
    """distinct NHTSA recall campaigns across these model years, and the systems recalled most: (n, [(system, n)])"""
    seen = {}
    for y in years:
        for r in extra(F['id'], y).get('recalls', []) or []:
            seen.setdefault(r['id'], r)
    sysn = defaultdict(int)
    for r in seen.values():
        p = (r.get('part') or '').split('|')[0].split(':')[0].strip()
        if p: sysn[PART.get(p, p.split(',')[0].lower())] += 1
    return len(seen), sorted(sysn.items(), key=lambda kv: (-kv[1], kv[0]))[:2]


# plain names for NHTSA's complaint areas (PART), and one simple line icon per area for "What breaks"
_CB_PN = {'speed control': 'throttle & cruise control', 'fuel or EV drive system': 'fuel system', 'body structure': 'body', 'service brakes, hydraulic': 'brakes',
          'service brakes, electric': 'brakes', 'automatic emergency braking': 'emergency braking'}
def _cb_pn(n): return _CB_PN.get(n, n)
_CB_IC = [(r'engine|cooling', '<path d="M4 10v6M2 13h2M4 9h3V7h6v2h3l2 3h2v4h-2l-2 3H8l-4-3z"/>'),
          (r'transmission|drivetrain|4x4|axle', '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>'),
          (r'electric|battery', '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>'),
          (r'emergency braking|lane|stability|collision', '<path d="M12 3 22 21H2z"/><path d="M12 10v5M12 18h.01"/>'),
          (r'brake', '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/>'),
          (r'steering', '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2"/><path d="M3.5 10h6.5M14 10h6.5M12 14v7"/>'),
          (r'suspension|wheel|tire', '<path d="M12 2v3M12 19v3M7 5h10M7 19h10M7 5l10 3.5L7 12l10 3.5L7 19"/>'),
          (r'airbag|seat belt', '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>'),
          (r'throttle|speed', '<path d="M4 18a9 9 0 1 1 16 0"/><path d="M12 14l4-5"/>'),
          (r'fuel', '<path d="M4 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16M3 21h12M6 8h6M14 10h2a2 2 0 0 1 2 2v4a1.5 1.5 0 0 0 3 0V8l-3-3"/>'),
          (r'a/c|heat', '<path d="M12 2v20M3.3 7l17.4 10M20.7 7 3.3 17"/>'),
          (r'wiper|visib', '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>'),
          (r'light', '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9V16h7v-2.1A6 6 0 0 0 12 3z"/>'),
          (r'screen|radio|camera', '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8"/>'),
          (r'door|window|lock|body', '<path d="M4 20V9l6-5h10v16z"/><path d="M15 12h2"/>'),
          (r'exhaust|emission', '<path d="M3 15h9M3 19h13M14 8a3 3 0 1 1 3 3h-3"/>')]
_CB_WR = '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18v3h3l6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>'
def _cb_ico(n, k='cb-ic'):
    d = next((d for rx, d in _CB_IC if re.search(rx, n.lower())), _CB_WR)
    return f'<span class="{k}"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{d}</svg></span>'


def _cb_apart(a, b):
    """two EPA cost ranges that don't overlap (only then is one car's fuel bill clearly lower: trims differ a lot)"""
    return a[1] < b[0] or b[1] < a[0]


def _cb_usd(a):
    return f'${a[0]:,}' if a[0] == a[1] else f'${a[0]:,}–{a[1]:,}'


def _cb_facts(F):
    """newest model year's MPG, crash stars and EPA fuel cost"""
    last = max(v['y'] for v in F['years']); xx = extra(F['id'], last); m, sf = xx.get('mpg'), xx.get('safety') or {}
    st = sf.get('best') if str(sf.get('best') or '').isdigit() else None
    return dict(last=last, mpg=(m['comb'] if m else None), cost=(m.get('cost') if m else None), ev=bool(m and m.get('ev')), st=int(st) if st else None)


def cmp_page(a, b):
    A, B = FY[a], FY[b]; ca, cb = BYNAME[A['name']], BYNAME[B['name']]
    ya, yb = {v['y']: v for v in A['years'] if v['ok']}, {v['y']: v for v in B['years'] if v['ok']}
    shared = sorted(set(ya) & set(yb))
    if len(shared) < 2: return None
    full = [y for y in shared if not (ya[y].get('early') or yb[y].get('early'))] or shared   # 2023+ partial years never count toward a winner
    wa = sum(ya[y]['li'] < yb[y]['li'] for y in full); wb = sum(yb[y]['li'] < ya[y]['li'] for y in full)
    _sa, _sb = vs_names(A, B)   # 'Camry', 'Civic' (the way people search)
    title = seo_title([f'{_sa} vs {_sb}: Which Is More Reliable?', f'{_sa} vs {_sb} Reliability by Year', f'{_sa} vs {_sb} Reliability'])   # unchanged (search-titles agent owns it)
    sh_txt = f'{A["name"]} vs {B["name"]}: which has fewer problems? Free comparison from owner complaints:'
    close = abs(ca['li'] - cb['li']) <= max(ca['li'], cb['li']) * .08
    aL = ca['li'] <= cb['li']   # A leads
    L, T, cL, cT, sL, sT = (A, B, ca, cb, _sa, _sb) if aL else (B, A, cb, ca, _sb, _sa)
    fewer = round((1 - cL['li'] / max(cT['li'], 1)) * 100)
    nm = {A['id']: _sa, B['id']: _sb}
    fa, fb = _cb_facts(A), _cb_facts(B)
    ra, rb = _cb_rec(A, shared), _cb_rec(B, shared)
    wA, wB = worst_year(A), worst_year(B)
    bA = rec_year(A)[0] or min(ya.values(), key=lambda v: v['li']); bB = rec_year(B)[0] or min(yb.values(), key=lambda v: v['li'])
    span = f'{full[0]}–{full[-1]}'; rspan = f'{shared[0]}–{shared[-1]}'

    # ---- 1. winner card: both cars, "X wins because" + 3 reasons
    def img(F):
        ph = mphoto(F['id'])
        return pimg(ph, F['name'], 'cb-im').replace(' loading="lazy"', '') if ph else '<span class="cb-im cb-im0"></span>'
    def car(F, c):
        win = (not close) and F is L
        return (f'<a class="cb-car{" cb-win" if win else ""}" href="{CARU(F)}">{img(F)}<b>{E(F["name"])}</b>'
                f'<span class="cb-car-s">Lemon Index <i>{c["li"]}</i></span>' + ('<span class="cb-flag">WINNER</span>' if win else '') + '</a>')
    lw, tw = (wa, wb) if aL else (wb, wa)
    lr, tr = (ra[0], rb[0]) if aL else (rb[0], ra[0])
    lwy, twy = (wA, wB) if aL else (wB, wA)
    lf, tf = (fa, fb) if aL else (fb, fa)
    lb_, tb_ = (bA, bB) if aL else (bB, bA)
    cand = []   # (side, priority, big, label, sub): side = 'L' if the leader is better, 'T' if the other car is. Fixed priority (Elijah's list):
    # a milder worst year, fewer recalls, more years won, a better best year, then the fuel bill
    if lr != tr:
        s_, lo, hi = ('L', lr, tr) if lr < tr else ('T', tr, lr)
        cand.append((s_, 2, f'{lo}&nbsp;<small>vs&nbsp;{hi}</small>', 'fewer recalls', f'NHTSA recall campaigns, {rspan} models'))
    if lwy and twy and lwy['li'] != twy['li']:
        s_ = 'L' if lwy['li'] < twy['li'] else 'T'; P, Q = (lwy, twy) if s_ == 'L' else (twy, lwy); nP, nQ = (sL, sT) if s_ == 'L' else (sT, sL)
        cand.append((s_, 3, f'{P["li"]}&nbsp;<small>vs&nbsp;{Q["li"]}</small>', 'a milder worst year', f'Lemon Index of its worst year: {P["y"]} {E(nP)} vs {Q["y"]} {E(nQ)}'))
    if lw != tw:
        s_, hi, lo = ('L', lw, tw) if lw > tw else ('T', tw, lw)
        cand.append((s_, 1, f'{hi}&nbsp;<small>of&nbsp;{len(full)}</small>', 'more years with fewer complaints', f'model years {span}, head to head'))
    if lb_ and tb_ and lb_['li'] != tb_['li']:
        s_ = 'L' if lb_['li'] < tb_['li'] else 'T'; P, Q = (lb_, tb_) if s_ == 'L' else (tb_, lb_); nP, nQ = (sL, sT) if s_ == 'L' else (sT, sL)
        cand.append((s_, 0, f'{P["li"]}&nbsp;<small>vs&nbsp;{Q["li"]}</small>', 'a better best year', f'Lemon Index of its best year: {P["y"]} {E(nP)} vs {Q["y"]} {E(nQ)}'))
    if lf['cost'] and tf['cost'] and not (lf['ev'] or tf['ev']) and _cb_apart(lf['cost'], tf['cost']):
        if True:
            s_ = 'L' if lf['cost'][1] < tf['cost'][0] else 'T'; P, Q = (lf, tf) if s_ == 'L' else (tf, lf)
            cand.append((s_, -1, f'{USD(P["cost"])}', 'a smaller fuel bill', f'a year, vs {USD(Q["cost"])} (EPA estimate, {P["last"]} vs {Q["last"]})'))
    winL = sorted([x for x in cand if x[0] == 'L'], key=lambda x: -x[1]); winT = sorted([x for x in cand if x[0] == 'T'], key=lambda x: -x[1])
    def rcard(big, lab, sub, k=''):
        return f'<div class="cb-r{k}"><b>{big}</b><span>{lab}</span><small>{sub}</small></div>'
    if close:
        why = (f'<p class="cb-why">Too close to call</p><p class="cb-why-s">About the same complaints per car sold ({ca["li"]} vs {cb["li"]}). Pick by model year below.</p>'
               + '<div class="cb-rs">' + ''.join(rcard(big, f'{E(nm[(L if s_ == "L" else T)["id"]])}: {lab}', sub) for s_, _, big, lab, sub in sorted(cand, key=lambda x: -x[1])[:3]) + '</div>')
        other = ''
    else:
        top = [rcard(f'{fewer}%', 'fewer complaints per car sold', f'Lemon Index {cL["li"]} vs {cT["li"]}', ' cb-r1')] + [rcard(big, lab, sub) for _, _, big, lab, sub in winL[:2]]
        why = f'<p class="cb-why">The {E(sL)} wins because it has</p><div class="cb-rs">{"".join(top)}</div>'
        other = (f'<p class="cb-oth"><b>Where the {E(sT)} is better:</b> ' + '; '.join(f'{lab} ({re.sub("<[^>]+>", "", big)})' for _, _, big, lab, _ in winT[:3]) + '.</p>') if winT else ''
    crd = pcredit(who(mphoto(a), mphoto(b)))
    try: _cbh = round(600 * (1 - YC.crop([ph['src'] for ph in (mphoto(a), mphoto(b)) if ph])))   # trim the empty sky both pictures share (ycarousel.py)
    except Exception: _cbh = 600
    src_ = (f'<p class="sub cmp-lede">{E(QN(A))} or {E(QN(B))}? Here is the {E(_sb)} vs {E(_sa)} question answered from owner complaints filed with the government, for every model year both were sold.</p>'
           f'<p>{WHAT_LI} A year counts toward the head-to-head only when both cars have 3 full years of complaints, so 2023 and newer show as partial. '
           f'Recalls are NHTSA campaigns, counted once each. Fuel costs are the EPA&#39;s estimates (15,000 miles a year). YouTube: the most-watched owner reviews and buyer guides for each generation. '
           f'<a href="/method/">How the index works</a></p>')
    hero = (f'<section class="cb-hero{" cb-tie" if close else ""}"><div class="cb-cars" style="--ar:1000 / {_cbh}">{car(A, ca)}<span class="cb-vs">VS</span>{car(B, cb)}</div>{why}{other}'
            f'<div class="cb-hf">{cb_info(src_, "Where this data comes from", "Data sources")}<span class="cb-sh">{crd}{share_btn(sh_txt)}</span></div></section>')
    src = ''

    # ---- 2. head to head: value | label | value
    def better(x, y, high):
        if x is None or y is None or x == y: return '', ''
        return (' cb-w', '') if (x > y) == high else ('', ' cb-w')
    def srow(lab, sub, va, vb, w, k=''):
        return f'<div class="cb-row{k}"><div class="cb-v{w[0]}">{va}</div><div class="cb-l">{lab}<small>{sub}</small></div><div class="cb-v{w[1]}">{vb}</div></div>'
    yv = lambda v: f'{v["li"]}<small>{v["y"]}</small>' if v else '–'
    mpgv = lambda f: ('–' if not f['mpg'] else (f'{f["mpg"][0]}' if f['mpg'][0] == f['mpg'][1] else f'{f["mpg"][0]}–{f["mpg"][1]}') + ('<small>MPGe</small>' if f['ev'] else ''))
    stv = lambda f: f'{f["st"]}<small>of 5 ★</small>' if f['st'] else '–'
    mid = lambda f: sum(f['cost']) / 2 if f['cost'] else None
    rows = [srow('Complaints per car sold', 'Lemon Index', f'{ca["li"]}', f'{cb["li"]}', better(ca['li'], cb['li'], False)),
            srow('Years with fewer complaints', span, f'{wa}<small>of {len(full)}</small>', f'{wb}<small>of {len(full)}</small>', better(wa, wb, True)),
            srow('Best year', 'fewest complaints', yv(bA), yv(bB), better(bA['li'] if bA else None, bB['li'] if bB else None, False)),
            srow('Worst year', 'most complaints', yv(wA), yv(wB), better(wA['li'] if wA else None, wB['li'] if wB else None, False)),
            srow('Recalls', f'campaigns, {rspan} models', f'{ra[0]}', f'{rb[0]}', better(ra[0], rb[0], False))]
    if fa['st'] or fb['st']: rows.append(srow('Crash test', 'NHTSA, newest model', stv(fa), stv(fb), better(fa['st'], fb['st'], True)))
    if fa['mpg'] and fb['mpg'] and fa['ev'] == fb['ev']: rows.append(srow('MPGe' if fa['ev'] else 'MPG', 'combined, newest model', mpgv(fa), mpgv(fb), better(fa['mpg'][1], fb['mpg'][1], True)))
    if fa['cost'] and fb['cost']: rows.append(srow('Fuel a year' if not (fa['ev'] and fb['ev']) else 'Electricity a year', 'EPA estimate, newest model', _cb_usd(fa['cost']), _cb_usd(fb['cost']), better(mid(fa), mid(fb), False) if _cb_apart(fa['cost'], fb['cost']) else ('', ''), ' cb-money'))
    board = (f'<div class="cb-board"><div class="cb-row cb-bh"><div class="cb-v"><a href="{CARU(A)}">{E(_sa)}</a></div><div class="cb-l"></div><div class="cb-v"><a href="{CARU(B)}">{E(_sb)}</a></div></div>{"".join(rows)}</div>')

    # ---- 3. years to buy (11-13 v4, Elijah: bars instead of plain numbers): each car's 3 best and 3 worst full model years (2010+,
    # partial 2023+ scores left out) as Lemon Index bars against the average-car line; best in brand yellow, worst in red when above average
    _pool = {F['id']: sorted(year_pool(F), key=lambda v: (v['li'], -v['y'])) for F in (A, B)}
    ymx = max([120] + [v['li'] * 1.04 for P in _pool.values() for v in P])
    def ybar(F, v, k):
        return (f'<a class="cb-yb {k}" href="{CARU(F, v["y"])}"><span class="cb-ybl">{v["y"]}</span><span class="cb-ybt"><i style="--w:{max(2, min(100, v["li"] / ymx * 100)):.1f}%"></i>'
                f'<em style="left:{100 / ymx * 100:.1f}%"></em></span><b>{v["li"]}</b></a>')
    def buycard(F, sN):
        P = _pool[F['id']]; best3 = P[:3]; worst3 = [v for v in sorted(P, key=lambda v: (-v['li'], -v['y'])) if v not in best3][:3]
        why_ = ''
        if worst3 and worst3[0]['li'] > 110:
            t = ((TOPF.get(F['id']) or {}).get(str(worst3[0]['y'])) or {}).get('top') or []
            if t: why_ = f'<p class="cb-yw">{worst3[0]["y"]}: owners name <b>{E(t[0]["t"].lower())}</b> most ({t[0]["n"]:,} complaints)</p>'
        bests = ''.join(ybar(F, v, 'best') for v in best3) or '<span class="cb-none">Not enough scored years.</span>'
        worsts = ('<p class="cb-k2">Most complaints</p>' + ''.join(ybar(F, v, 'bad' if v['li'] > 110 else 'mid') for v in worst3)) if worst3 else ''
        return f'<div class="cb-card cb-buy"><h3><a href="{CARU(F)}">{E(F["name"])}</a></h3><p class="cb-k2">Fewest complaints</p>{bests}{worsts}{why_}</div>'
    buy = (cb_h2('buy', 'Which years to buy', cb_info('Each bar is that model year&#39;s Lemon Index: owner complaints to NHTSA in its first 3 years, per car sold, against the average car of the same year. '
                                                      'Shorter bar = fewer complaints. The dashed line is the average car (100). Model years 2010 and newer with 3 full years of complaints; '
                                                      'partial 2023+ scores are left out. Red = worse than average. Tap a year for its full report.', 'How to read these bars'))
           + f'<div class="cb-two">{buycard(A, _sa)}{buycard(B, _sb)}</div>')

    # ---- 4. year by year: one row per year, both cars side by side
    mx = max(max(ya[y]['li'], yb[y]['li']) for y in shared)
    def cell(F, v, w, pt):
        return (f'<a class="cb-yv {CLS(v)}{" cb-w" if w else ""}" href="{CARU(F, v["y"])}"><b>{v["li"]}</b>'
                f'<i style="--w:{max(4, min(100, v["li"] / mx * 100)):.0f}%"></i>{"<small>partial</small>" if pt else ""}</a>')
    def _yr(y):
        pt = y not in full; wA_ = not pt and ya[y]['li'] < yb[y]['li']; wB_ = not pt and yb[y]['li'] < ya[y]['li']
        return (f'<div class="yr cb-yr{" lfa-pt" if pt else ""}" data-y="{y}" data-a="{ya[y]["li"]}" data-b="{yb[y]["li"]}"{" data-p=\"1\"" if pt else ""}>'
                f'<div class="yy">{y}</div>{cell(A, ya[y], wA_, pt)}{cell(B, yb[y], wB_, pt)}</div>')
    _fyA, _fyB = {v['y']: v for v in A['years']}, {v['y']: v for v in B['years']}
    def _why(F, fy, yy):
        v = fy.get(yy)
        return f'{E(F["name"])}: no {yy} model' if not v else f'{E(F["name"])}: {E(PLN(v))}' if not v['ok'] else ''
    def _gap(y): return f'<div class="yr cb-yr lfa-gap" data-y="{y}"><div class="yy">{y}</div><p>' + '; '.join(w for w in (_why(A, _fyA, y), _why(B, _fyB, y)) if w) + '</p></div>'
    _all = list(range(shared[-1], shared[0] - 1, -1))
    _cut = full[-min(8, len(full))]
    _top = [y for y in _all if y >= _cut or (y in shared and y not in full)]
    _rest = [y for y in _all if y not in _top]
    _row = lambda y: _yr(y) if y in shared else _gap(y)
    _opt = lambda sel: ''.join(f'<option value="{y}"{" selected" if y == sel else ""}>{y}</option>' for y in sorted(full, reverse=True))
    pick = (f'<form class="lfa-yp cb-yp" data-a="{E(A["name"])}" data-b="{E(B["name"])}" aria-label="Your model years"><b>Shopping certain years?</b> <span class="cb-yp-s"><label><span class="vh">From</span><select name="f">{_opt(full[0])}</select></label> to '
            f'<label><span class="vh">To</span><select name="t">{_opt(full[-1])}</select></label></span><output class="lfa-yr-res" aria-live="polite"></output></form>')
    yh = f'<div class="cb-yr cb-yh"><div class="yy"></div><div>{E(_sa)}</div><div>{E(_sb)}</div></div>'
    yrs = (f'<div class="yrs cb-yrs">{yh}' + ''.join(_row(y) for y in _top)
           + (f'<details class="yrs-more"><summary>Show {len(_rest)} older years</summary>' + ''.join(_row(y) for y in _rest) + '</details>' if _rest else '') + '</div>')
    _pt = '; 2023 and newer are partial and don&#39;t count toward the winner' if len(full) < len(shared) else ''
    ybys = (cb_h2('your-years', 'Year by year', cb_info(f'Lemon Index per model year, newest first: owner complaints per car sold, 100 = the average car, lower is better. '
                                                        f'Green = the car with fewer complaints that year{_pt}. Tap a year for its report.', 'How to read this'))
            + f'{pick}{yrs}')

    # ---- 5. what breaks (11-13 v2, Elijah: "still a little confusing and bland"): one plain headline per car from its top complaint area,
    # the #1 problem big with an icon, #2-#3 small, then "What owners paid to fix it": the median repair cost big, the middle half small
    def breaks(F, c, sN):
        ys_ = [v['y'] for v in year_pool(F)]; y0, y1 = (min(ys_), max(ys_)) if ys_ else (shared[0], shared[-1])
        iss = [(_cb_pn(p_), k) for p_, k in (c.get('issues') or [])]
        yrs_ = E(c['years'].replace('-', '–'))
        if not iss:
            top_ = f'<h3 class="cb-bk-car"><a href="{CARU(F)}">{E(sN)}</a></h3><p class="cb-bk-hl">Not enough complaints to break down</p>'
        else:
            n1, p1 = iss[0]; k_ = -(-100 // p1) if p1 else 0
            if p1 >= 25: hl = f'{"More than " if p1 - 100 / k_ >= 1.5 else ""}1 in {k_} complaints {"is" if k_ == 1 else "are"} about {E(n1)}'
            else: hl = f'{E(n1[0].upper() + n1[1:])} tops the list'
            top_ = (f'<h3 class="cb-bk-car"><a href="{CARU(F)}">{E(sN)}</a></h3><p class="cb-bk-hl">{hl}</p>'
                    f'<div class="cb-bk1">{_cb_ico(n1, "cb-bki")}<span>{E(n1[0].upper() + n1[1:])}<small>#1 problem area</small></span><b>{p1}%</b><i style="--w:{p1}%"></i></div>'
                    + (f'<ul class="cb-bkn">' + ''.join(f'<li>{_cb_ico(n_)}<span>{E(n_[0].upper() + n_[1:])}</span><b>{k}%</b></li>' for n_, k in iss[1:3]) + '</ul>' if len(iss) > 1 else ''))
        A_ = RCQ.areas(F['id'], y0, y1); tot = sum(x[1] for x in A_)
        bills = [x for x in A_ if x[1] >= RCQ.MIN_N][:2]
        if bills:
            _ex = (f'From {tot:,} repair costs owners wrote into their NHTSA complaints, {y0}–{y1} models. Typical = the middle (median) cost; '
                   'half of owners paid within the range under it. One repair each, in U.S. dollars, not a yearly cost.')
            paid = (f'<div class="cb-k2row"><p class="cb-k2 cb-bkp">What owners paid to fix it</p>{cb_info(_ex, "Where these costs come from")}</div>'
                    + ''.join(f'<div class="cb-bkc">{_cb_ico(ar.lower())}<span>{E(ar)}</span><b>{RCQ._r(md)}<small>typical</small></b><em>half paid {RCQ._r(lo)}–{RCQ._r(hi)}</em></div>' for ar, n, lo, md, hi, _ in bills))
        else: paid = '<p class="cb-k2 cb-bkp">What owners paid to fix it</p><p class="cb-bkx">Not enough owners wrote down what they paid yet.</p>'
        return f'<div class="cb-card cb-bk">{top_}{paid}</div>'
    brk = (cb_h2('breaks', 'What breaks', cb_info('Percent = the share of each car&#39;s owner complaints to NHTSA about that area, model years 2010–2022. One complaint can name several areas.', 'Where these numbers come from'))
           + f'<div class="cb-two">{breaks(A, ca, _sa)}{breaks(B, cb, _sb)}</div>')

    # ---- 6. recalls
    def rcard2(F, r):
        return (f'<div class="cb-card cb-rc"><h3><a href="{CARU(F)}">{E(F["name"])}</a></h3><p class="cb-big">{r[0]}</p><p class="cb-k">recall campaigns, {rspan} models</p>'
                + (f'<p class="cb-rc-s">Most for: ' + ', '.join(f'<b>{E(s)}</b> ({n})' for s, n in r[1]) + '</p>' if r[1] else '') + '</div>')
    rec = (cb_h2('recalls', 'Recalls', '<a class="cb-cbtn" href="/vin/">VIN check</a>',
                 cb_info(f'NHTSA recall campaigns for the {rspan} model years both cars were sold, each campaign counted once. '
                         'Whether a recall is still open on one exact car depends on its VIN: check it on our <a href="/vin/">VIN check</a>.', 'About these recalls'))
           + f'<div class="cb-two">{rcard2(A, ra)}{rcard2(B, rb)}</div>')

    # ---- 7. YouTube
    def ytcard(F):
        gens = YBUY.get(F['id']) or []; py = popular_year(F)
        g = next((g for g in gens if py and g['y0'] <= py <= g['y1']), gens[-1] if gens else None)
        r = YTR.get(F['id'])
        if not g and not r: return f'<div class="cb-card cb-yt"><h3>{E(F["name"])}</h3><p class="cb-none">We haven&#39;t studied {E(F["name"])} YouTube videos yet.</p></div>'
        rk = (f'<p class="cb-ytr"><b>#{r[0]}</b> of {r[1]} models for owner tone <small>({r[2]:,} videos)</small></p>') if r else ''
        chips = lambda L, k: ''.join(f'<span class="cb-tc {k}">{E(t)} <b>{p}%</b></span>' for t, p in L[:3]) or '<span class="cb-none">Nothing stands out.</span>'
        body_ = (f'<p class="cb-k">{E(g["label"])} · {g["videos"]} most-watched videos</p><p class="cb-k2">Praised for</p><div class="cb-tcs">{chips(g.get("praise") or [], "good")}</div>'
                 f'<p class="cb-k2">Complaints</p><div class="cb-tcs">{chips(g.get("trouble") or [], "bad")}</div>') if g else '<p class="cb-none">No generation study yet.</p>'
        return f'<div class="cb-card cb-yt"><h3><a href="{CARU(F)}">{E(F["name"])}</a></h3>{rk}{body_}</div>'
    yt = (cb_h2('youtube', 'What YouTube owners say', cb_info('% = the share of the generation&#39;s most-watched owner reviews and buyer guides that praise or complain about that topic. '
                                                             'Owner tone rank: how positively videos talk about the model vs. every model we track. It measures tone, not failure rates. Videos belong to their creators.', 'Where this comes from'))
          + f'<div class="cb-two">{ytcard(A)}{ytcard(B)}</div>')

    # ---- 8. our pick
    nf = full[-min(5, len(full)):]
    pk = [('Overall', (f'Too close to call' if close else f'{E(L["name"])}'), (f'Lemon Index {ca["li"]} vs {cb["li"]}' if close else f'{fewer}% fewer complaints per car sold'))]
    if len(nf) >= 3:
        ma, mb = round(sum(ya[y]['li'] for y in nf) / len(nf)), round(sum(yb[y]['li'] for y in nf) / len(nf))
        if abs(ma - mb) <= max(ma, mb) * .08: pk.append((f'Buying {nf[0]}–{nf[-1]}', 'Too close to call', f'average Lemon Index {ma} vs {mb}: compare the exact year'))
        else:
            P_ = A if ma < mb else B
            pk.append((f'Buying {nf[0]}–{nf[-1]}', E(P_['name']), f'average Lemon Index for those years {min(ma, mb)} vs {max(ma, mb)}'))
    if bA and bB:
        P_, v_ = (A, bA) if bA['li'] <= bB['li'] else (B, bB)
        pk.append(('Best single year', f'<a href="{CARU(P_, v_["y"])}">{v_["y"]} {E(P_["name"])}</a>', f'Lemon Index {v_["li"]}'))
    if fa['cost'] and fb['cost'] and _cb_apart(fa['cost'], fb['cost']) and fa['ev'] == fb['ev']:
        P_, f_ = (A, fa) if mid(fa) < mid(fb) else (B, fb)
        pk.append(('Lowest fuel bill', E(P_['name']), f'{USD(f_["cost"])} a year (EPA, {f_["last"]})'))
    pick_ = ('<section class="cb-pick"><h2 id="our-pick">Our pick</h2><dl>' + ''.join(f'<div><dt>{k}</dt><dd><b>{v}</b><small>{s}</small></dd></div>' for k, v, s in pk) + '</dl></section>')

    # 11-13 (nav review): more match-ups with either car, so a reader can keep comparing
    _mu = [p for p in PAIRS if p != (a, b) and (a in p or b in p) and p[0] in FY and p[1] in FY][:8]
    more_ = ('<section class="cb-more"><h2>More match-ups</h2><div class="cb-mus">' + ''.join(
        f'<a href="{CMPU(*p)}">{E(vs_names(FY[p[0]], FY[p[1]])[0])} <i>vs</i> {E(vs_names(FY[p[0]], FY[p[1]])[1])}</a>' for p in _mu) + '</div></section>') if _mu else ''
    nav = ('<nav class="cb-jump" aria-label="On this page"><div class="cb-jin">' + ''.join(f'<a href="#{h}">{t}</a>' for h, t in (
           ('h2h', 'Head to head'), ('buy', 'Years to buy'), ('your-years', 'Year by year'), ('breaks', 'What breaks'), ('recalls', 'Recalls'), ('youtube', 'YouTube'), ('our-pick', 'Our pick'))) + '</div></nav>')
    h2h = cb_h2('h2h', 'Head to head', cb_info('Lemon Index = owner complaints to NHTSA per car sold, against the average car of the same model years. '
                                               '100 is the average car; lower is better. Green check = the better of the two on that line.', 'How to read this'))
    _ld_name = title.replace(' | Lemon Index', '')
    _lead_s, _trail_s = (_sa, _sb) if aL else (_sb, _sa)
    page(CMPU(a, b), title,
         f'{QN(A)} vs {QN(B)} reliability: ' + (f'about the same owner complaints per car sold (Lemon Index {ca["li"]} vs {cb["li"]}).' if close else
         f'the {_lead_s} drew {fewer}% fewer owner complaints per car sold than the {_trail_s} (Lemon Index {cL["li"]} vs {cT["li"]}).')
         + f' Every model year both were sold, {shared[0]}–{shared[-1]}, plus recalls, crash tests and MPG.', f'''
<article class="study cmpp cb"><p class="kicker"><a href="/cars/">All cars</a> · Compare</p><h1>{E(_sa)} vs {E(_sb)}: which is more reliable?</h1>
{CB_ASSET}{hero}{src}{nav}
{h2h}{board}
{buy}{ybys}{LFA_JS}{brk}{rec}{yt}{pick_}
{more_}{CB_JS}<p class="note"><a href="{CARU(A)}">Every {E(A["name"])} year</a> · <a href="{CARU(B)}">Every {E(B["name"])} year</a> · <a href="/method/">How the index works</a></p>{share_line(sh_txt, 'Know someone choosing between these two?')}</article>''', kind='article',
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": _ld_name, "url": BASE + CMPU(a, b)}])
    return CMPU(a, b)
