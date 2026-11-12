# Advanced mode (11-06, Elijah: normal for regular people, advanced for car people, on every car, plane and motorcycle). Run by build.py with exec() after the year pages.
# Normal page = /cars/<id>/<year>/ (unchanged). Advanced = /cars/<id>/<year>/advanced/, its own URL, title and data, so it answers different searches:
# engine and transmission options (EPA), recall campaign numbers with the full defect, risk and remedy text, failure mileage by system, NHTSA investigations, dealer repair notes,
# complaint math. Thin pages (too little that the normal page lacks) are noindex and stay out of the sitemap.
import csv as _csv
ADV_URLS = []
_n = lambda s: re.sub(r'[^a-z0-9]', '', str(s).lower())
_EPA = defaultdict(list)
if os.path.exists('data/cache/vehicles.csv'):
    for _r in _csv.DictReader(open('data/cache/vehicles.csv', encoding='utf-8', errors='replace')): _EPA[(_n(_r['make']), int(_r['year']))].append(_r)
MAKEFIX = {'chevy': 'chevrolet', 'mercedes': 'mercedesbenz', 'mercedesbenz': 'mercedesbenz'}
def epa_rows(f, y, x):
    names = x.get('names') or []; out = {}
    if not names: return []
    mk = _n(names[0][0]); base = sorted({_n(m) for _, m, c in names if c >= max(2, names[0][2] * .02)}, key=len)
    for r in _EPA.get((MAKEFIX.get(mk, mk), y), []):
        bm = _n(r['baseModel'] or r['model'])
        if not any(bm.startswith(b) or b.startswith(bm) for b in base if len(b) >= 2): continue
        ev = r['atvType'] == 'EV'; t = ' turbo' if r['tCharger'] == 'T' else ' supercharged' if r['sCharger'] == 'S' else ''
        eng = 'Electric' if (ev or not r['displ']) else f"{float(r['displ']):.1f}L {r['cylinders']}-cyl{t}" + (' hybrid' if r['atvType'] == 'Hybrid' else ' diesel' if r['atvType'] == 'Diesel' else ' plug-in hybrid' if r['atvType'] == 'Plug-in Hybrid' else '')
        k = (eng, r['trany'], r['drive']); c, h, co = int(r['city08']), int(r['highway08']), int(r['comb08'])
        if k not in out: out[k] = dict(eng=eng, tr=r['trany'].replace('Automatic', 'Auto').replace('Manual', 'Manual'), dr=r['drive'].replace('-Wheel Drive', 'WD').replace(' Wheel Drive', 'WD').replace('Part-time 4', '4').replace('All', 'A').replace('Front', 'F').replace('Rear', 'R').replace('4-', '4'), c=c, h=h, co=co, fuel=r['fuelType1'].replace(' Gasoline', ''), cost=int(r['fuelCost08']))
    return sorted(out.values(), key=lambda a: (a['eng'], -a['co']))[:14]
def mode_toggle(normal, adv, cur):
    return (f'<nav class="modes" aria-label="Page mode"><a href="{normal}"{" aria-current=page" if cur == "n" else ""}>Normal</a><a href="{adv}"{" aria-current=page" if cur == "a" else ""}>Advanced</a></nav>')
TABLE = lambda head, rows: '<div class="tw"><table class="adv"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table></div>'
def _mi(n): return f'{int(n):,}'
_MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
def _date(d):   # NHTSA recall dates here are dd/mm/yyyy
    a = d.split('/'); return f'{_MON[int(a[1]) - 1]} {a[2]}' if len(a) == 3 and a[1].isdigit() and 1 <= int(a[1]) <= 12 else E(d)
def _sysrows(comps):
    """11-12 (Marcus: "Brakes" listed twice): NHTSA files two brake categories that read the same in plain words; keep the bigger one."""
    best = {}
    for c in comps:
        lab = NICE(c[0])
        if lab not in best or c[4] > best[lab][4]: best[lab] = c
    return [(lab, c) for lab, c in ((NICE(c[0]), c) for c in comps) if best[lab] is c]
def adv_year(f, v, y, x, x2, best, worst, ys):
    nm = E(SNM(f)); mkr = E(MAKER(f['name'])); sold = v.get('sold'); rate = v['n'] / sold * 1e5 if sold else None; sc = sorted([w for w in ys if w['ok'] and not w.get('early')], key=lambda w: w['li'])
    rk = next((i + 1 for i, w in enumerate(sc) if w['y'] == y), None); facts = []
    facts.append(('Lemon Index', f'{v["li"]}' if v['ok'] else '–', '100 = average car'))
    facts.append(('Complaints', f'{v["n"]:,}', 'NHTSA, first 3 years'))
    if sold: facts.append(('Sold', f'{sold:,}', 'U.S. model year'))
    if rate: facts.append(('Per 100K sold', f'{rate:,.0f}', 'complaints'))
    if rk: facts.append(('Complaint rank', f'#{rk} of {len(sc)}', '#1 = fewest complaints per car sold (not the YouTube rank)'))   # 11-12 (Marcus: "#2 of 23" vs the YouTube "#15")
    tiles = '<div class="yts">' + ''.join(f'<div class="yt"><span class="yt-l">{l}</span><b class="yt-v">{a}</b><small>{b}</small></div>' for l, a, b in facts) + '</div>'
    sec = []; unique = 0
    rows = epa_rows(f, y, x)
    if rows:
        unique += 2; sec.append(f'<section class="yc" id="engines"><h2>Engines and drivetrains <span class="yc-n">{len(rows)}</span></h2>' + TABLE(['Engine', 'Transmission', 'Drive', 'City / hwy / combined', 'Fuel', 'Fuel cost/yr'], [[E(a['eng']), E(a['tr']), E(a['dr']), f'{a["c"]} / {a["h"]} / {a["co"]}', E(a['fuel']), f'${a["cost"]:,}'] for a in rows]) + '<p class="yc-cap">EPA test versions for this model year. Fuel cost is the EPA&#39;s current estimate, not the price in that year.</p></section>')
    m = x.get('miles') or {}; comps = x.get('comps') or []
    if m or comps:
        unique += 1
        head = f'<p>Half of owners who gave a mileage reported the problem between <b>{_mi(m.get("p25", 0))}</b> and <b>{_mi(m.get("p75", 0))}</b> miles. Median <b>{_mi(m.get("median", 0))}</b>, from {m.get("n", 0):,} complaints with a mileage.</p>' if m else ''
        sec.append(f'<section class="yc" id="mileage"><h2>Failure mileage by system</h2>{head}' + (TABLE(['System', 'Median', 'Middle half', 'Complaints'], [[E(lab).capitalize(), _mi(c[1]), f'{_mi(c[2])}–{_mi(c[3])}', f'{c[4]:,}'] for lab, c in _sysrows(comps)]) if comps else '') + '<p class="yc-cap">Mileage owners typed into their NHTSA complaint, all complaints for this model year. People report some problems late, so read it as a range.</p></section>')
    if v.get('parts'): sec.append('<section class="yc" id="systems"><h2>Complaints by system</h2>' + TABLE(['System', 'Share of complaints'], [[E(NICE(p)).capitalize(), f'{k}%'] for p, k in v['parts']]) + '<p class="yc-cap">One complaint can name more than one system, so shares can add to more than 100%.</p></section>')
    s = x.get('sev') or {}
    if s.get('total'): sec.append('<section class="yc" id="severity"><h2>Severity, all complaints</h2>' + TABLE(['Total', 'Crashes', 'Fires', 'Injuries', 'Deaths', 'Tows'], [[f'{s["total"]:,}', s.get('crash', 0), s.get('fire', 0), s.get('injured', 0), s.get('deaths', 0), s.get('towed', 0)]]) + '<p class="yc-cap">As reported by owners to NHTSA. Not verified.</p></section>')
    rec = x.get('recalls') or []
    if rec:
        unique += 2; rs = sorted(rec, key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2], reverse=True)
        sec.append(f'<section class="yc" id="campaigns"><h2>Recall campaigns <span class="yc-n">{len(rs)}</span></h2><ul class="advr">' + ''.join(f'<li><p class="advh"><a href="https://www.nhtsa.gov/recalls?nhtsaId={E(r["id"])}" target="_blank" rel="noopener nofollow">{E(r["id"])}</a> <small>{_date(r["date"])}</small> <b>{E((r["part"] or "Other").replace(":", " / ").title())}</b></p><p><b>Defect.</b> {E(r["summary"])}</p>' + (f'<p><b>Risk.</b> {E(r["risk"])}</p>' if r.get('risk') else '') + (f'<p><b>Remedy.</b> {E(r["fix"])}</p>' if r.get('fix') else '') + '</li>' for r in rs) + '</ul></section>')
    if x2.get('inv'):
        unique += 1; sec.append(f'<section class="yc" id="investigations"><h2>NHTSA investigations</h2>' + TABLE(['Status', 'Subject', 'Opened', 'Closed'], [['Open' if i['open'] else 'Closed', E(i['subject'] or i['part']), E(i['opened']), E(i.get('closed') or '–')] for i in x2['inv']]) + '</section>')
    tl = [c for c in (clean_tsb(z) for z in (x2.get('tsb') or {}).get('top', [])) if c]
    if x2.get('tsb'): unique += 1; sec.append(f'<section class="yc" id="tsb"><h2>Manufacturer communications <span class="yc-n">{x2["tsb"]["n"]}</span></h2><p>{mkr} filed {x2["tsb"]["n"]} service communications for this car with NHTSA.</p>' + (f'<ul class="fx">{"".join(f"<li>{E(s1)}</li>" for s1 in tl)}</ul>' if tl else '') + '</section>')
    sf = x.get('safety') or {}
    if sf.get('variants'): sec.append('<section class="yc" id="crash"><h2>Crash ratings by version</h2>' + TABLE(['Version', 'Overall', 'Front', 'Side', 'Rollover'], [[E(re.sub(r'^\d{4} ', '', w['desc'])), stars(w['overall']), stars(w['front']), stars(w['side']), stars(w['rollover'])] for w in sf['variants']]) + '</section>')
    tech = x2.get('tech') or {}
    if tech: sec.append('<section class="yc" id="tech"><h2>Safety equipment</h2>' + TABLE(['Electronic stability', 'Forward collision warning', 'Lane departure warning'], [[E(tech.get('esc', '–')), E(tech.get('fcw', '–')), E(tech.get('ldw', '–'))]]) + '</section>')
    yd = next((e for e in YTV.get(f['id'], []) if e['years'] and y in e['years']), None)
    if yd and yd.get('topics'):
        unique += 1; sec.append(f'<section class="yc" id="youtube"><h2>YouTube repair topics</h2><p>{yd["n"]} videos about the {E(yd["gen"])}, {_vw(yd["views"])} views.</p>' + TABLE(['Topic', 'Videos', 'Views'], [[E(t['name']), t['n'], _vw(t['views'])] for t in yd['topics']]) + '</section>')
    nbrs = [w for w in ys if abs(w['y'] - y) <= 3]
    sec.append('<section class="yc" id="neighbors"><h2>Nearby model years</h2>' + TABLE(['Year', 'Lemon Index', 'Complaints', 'Sold', 'Top system'], [[f'<a href="{CARU(f, w["y"])}advanced/">{w["y"]}</a>' if w['y'] != y else f'<b>{w["y"]}</b>', w['li'] if w['ok'] else '–', f'{w["n"]:,}', f'{w["sold"]:,}' if w.get('sold') else '–', E(NICE(w['parts'][0][0])).capitalize() if w.get('parts') else '–'] for w in nbrs]) + '</section>')
    body = (f'<div class="advp"><header class="advh1"><p class="ph-e"><a href="/cars/">All cars</a> · <a href="{CARU(f)}">{nm}</a> · <a href="{CARU(f, y)}">{y}</a></p><h1>{y} {nm}. Advanced data.</h1>'
            f'<p>The raw numbers: engines, recall campaign numbers, failure mileage and manufacturer communications.</p>{mode_toggle(CARU(f, y), CARU(f, y) + "advanced/", "a")}</header>{tiles}<div class="ygrid">{"".join(sec)}</div>'
            f'<p class="yc-cap">Sources: NHTSA complaints, recalls, investigations and manufacturer communications; EPA fuel economy data; YouTube video titles. Complaints are owner reports, not proof of a defect.</p></div>')
    return body, unique
def _build_adv():
    global _adv_idx, _adv_no
    _adv_idx = _adv_no = 0
    for f in YEARS:
        ys = f['years']; sc = [v for v in ys if v['ok'] and not v.get('early')]; best, worst = min(sc, key=lambda v: v['li']), max(sc, key=lambda v: v['li']); snm = SNM(f)
        for v in ys:
            y = v['y']; x = yearx(f['id'], y); x2 = X2.get(f['id'], {}).get(str(y), {}); body, u = adv_year(f, v, y, x, x2, best, worst, ys); path = CARU(f, y) + 'advanced/'
            nrec = len(x.get('recalls') or [])
            page(path, f'{y} {snm} Specs, Recalls and Failure Mileage',
                 f'{y} {snm} technical data: every EPA engine and transmission, {nrec} recall campaign{"s" if nrec != 1 else ""} with defect and remedy, failure mileage by system and manufacturer communications.', body)
            if u >= 3: ADV_URLS.append(path); _adv_idx += 1
            else:
                p = os.path.join(OUT, path.strip('/'), 'index.html'); s = open(p, encoding='utf-8').read().replace('<link rel="canonical"', '<meta name="robots" content="noindex,follow"><link rel="canonical"', 1); open(p, 'w', encoding='utf-8').write(s); _adv_no += 1
    print('advanced year pages', _adv_idx, 'indexed', _adv_no, 'noindex')
_build_adv()

# ---- planes and motorcycles: a raw-numbers page for each, same toggle
def adv_table_page(path, normal, title, desc, h1, crumbs_html, tiles, secs):
    t = '<div class="yts">' + ''.join(f'<div class="yt"><span class="yt-l">{l}</span><b class="yt-v">{a}</b><small>{b}</small></div>' for l, a, b in tiles) + '</div>'
    page(path, title, desc, f'<div class="advp"><header class="advh1"><p class="ph-e">{crumbs_html}</p><h1>{h1}</h1><p>The raw numbers behind the page, in one place.</p>{mode_toggle(normal, path, "a")}</header>{t}<div class="ygrid">{"".join(secs)}</div></div>'); ADV_URLS.append(path)
def _sec(i, h, head, rows, cap=''): return f'<section class="yc" id="{i}"><h2>{h}</h2>' + TABLE(head, rows) + (f'<p class="yc-cap">{cap}</p>' if cap else '') + '</section>'
def _build_v():
    for m in _load('data/moto.json'):
        slug = slugify(m['name']); n = f'/motorcycles/{slug}/'; a = n + 'advanced/'
        rows = [[y, c] for y, c in sorted(m.get('by_year', {}).items())]; secs = [_sec('years', 'Complaints by model year', ['Model year', 'Complaints'], rows)] if rows else []
        if m.get('parts'): secs.append(_sec('systems', 'Complaints by system', ['System', 'Share of complaints'], [[E(str(p[0])).capitalize(), f'{p[1]}%'] for p in m['parts']]))
        adv_table_page(a, n, f'{m["name"]} Complaint Data by Year and System | Advanced Data', f'{m["name"]} raw NHTSA data: {m["n"]} complaints by model year and system, crashes, fires and injuries.', f'{E(m["name"])}. Advanced data.', f'<a href="/motorcycles/">Motorcycles</a> · <a href="{n}">{E(m["name"])}</a>',
                       [('Complaints', f'{int(m["n"]):,}', 'NHTSA'), ('Crashes', m.get('crash', 0), 'reported'), ('Fires', m.get('fire', 0), 'reported'), ('Injuries', m.get('injured', 0), 'reported'), ('Median miles', f'{int(m["miles"]):,}' if m.get('miles') else '–', 'at complaint')], secs)
    for pl in _load('data/planes.json'):
        slug = slugify(pl['name']); n = f'/planes/{slug}/'; a = n + 'advanced/'
        secs = [_sec('years', 'Accidents by year', ['Year', 'Accidents'], [[y, c] for y, c in sorted(pl.get('by_year', {}).items())])] if pl.get('by_year') else []
        for k, h in (('what', 'What happened'), ('phase', 'Phase of flight')):
            if pl.get(k): secs.append(_sec(k, h, [h, 'Share of accidents'], [[E(str(p[0])), f'{p[1]}%'] for p in pl[k]]))
        if pl.get('mech_parts'): secs.append(_sec('mech', 'Mechanical causes', ['Part', 'Share'], [[E(str(p[0])), f'{p[1]}%'] for p in pl['mech_parts']]))
        adv_table_page(a, n, f'{pl["name"]} Accident Data by Cause and Phase of Flight | Advanced Data', f'{pl["name"]} raw NTSB data: {pl["n"]} accidents, {pl.get("fatal", 0)} fatal, by year, cause and phase of flight.', f'{E(pl["name"])}. Advanced data.', f'<a href="/planes/">Planes</a> · <a href="{n}">{E(pl["name"])}</a>',
                       [('Accidents', f'{int(pl["n"]):,}', 'NTSB'), ('Fatal', pl.get('fatal', 0), f'{pl.get("fatal_pct", 0)}% of accidents'), ('Deaths', pl.get('deaths', 0), 'NTSB'), ('Destroyed', f'{pl.get("destroyed_pct", 0)}%', 'of aircraft'), ('Mechanical', f'{pl.get("mech_pct", 0)}%', 'of accidents')], secs)
_build_v()
print('advanced total in sitemap', len(ADV_URLS))
