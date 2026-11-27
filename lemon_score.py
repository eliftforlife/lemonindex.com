# 11-26 the Lemon Score (Elijah approved the design 11-26). exec'd by build.py after hub_cards.py, so every data table it reads is loaded.
# One number per car model (and per model year), 0-100, higher = a better used buy. The old per-model number (complaints per car sold vs the
# average car, family_rates.csv `lemon_index`) is renamed the Complaint Score and becomes one input. Looks are NOT in the score.
#
# Four parts (weights out of 100):
#   Reliability & safety 40   Complaint Score 18 (data/family_rates.csv, years*.json: NHTSA owner complaints in the first 3 years per car sold,
#                                 100 = the average car of the same model years; the model-year sales fix is already inside those files)
#                             serious complaints 4 (share of complaints that report a crash, fire, injury or tow: extras_local `sev`)
#                             recalls 5 (NHTSA recall campaigns per model year, do-not-drive / park-outside campaigns count 3x, compared with
#                                 the median car of the same model year)
#                             cost of the common failures 3 (the failures owners name most, data/top_fails.json, priced with the AI repair
#                                 estimates in data/repair_est.json: an ESTIMATE)
#                             NHTSA crash tests 10 (5-Star overall rating, data/safety_ratings.json from data_safety.py, 2011+)
#   Cost to own 25            fuel 12 (EPA yearly fuel cost / 12, fueleconomy.gov), repair prices 10 (AI estimate for 10 everyday repairs, ESTIMATE),
#                             insurance 3 (data/insurance.json: NAIC state averages x the car-type factor, per MONTH, ESTIMATE; it only
#                                 separates sports cars from the rest, which is why it weighs little)
#   What YouTube thinks 20    the site's YouTube owner score (data/yt_scores.json), each year compared with the median car of the same model
#                             year, video-weighted (the same rule as the model page's YouTube rank)
#   Holds its value 15        data/price_est.json (AI private-party prices by mileage bracket, ESTIMATE): how much a car loses per year of age at
#                             the SAME mileage bracket (50-100K and 100-150K, model years 2011-2023: older cars' AI prices barely move), compared with cars of the same type
#                             at the same ages and miles
# Scoring: each input becomes a 0-100 percentile (100 = best). Reliability and safety are compared with every car; fuel, repair prices,
# insurance, YouTube and value with cars of the same type (car / SUV / truck / minivan + van), so a truck isn't marked down just for being a truck.
# A part is the weighted average of the inputs it has (Reliability & safety needs at least half its weight; Cost to own needs fuel or repairs).
# The Lemon Score = the weighted average of the parts it has (the middle car lands near 50; most cars fall between 35 and 65).
# Coverage: a score needs 3 of the 4 parts. Missing a part, or the Complaint Score (e.g. the F-150: no F-150-only sales), = "partial".
# Model years: the same, per year (the value part is the model's own: one price snapshot can't show one year's depreciation).
import math as _lsm, statistics as _lsst, json as _lsj, html as _lsh, re as _lsre

LS_V = '4'
LS_W = {'rel': 40, 'cost': 25, 'yt': 20, 'val': 15}
LS_SW = {'cpl': 18, 'sev': 4, 'rcl': 5, 'fail': 3, 'crash': 10, 'fuel': 12, 'rep': 10, 'ins': 3, 'yt': 1, 'val': 1}
LS_OF = {'cpl': 'rel', 'sev': 'rel', 'rcl': 'rel', 'fail': 'rel', 'crash': 'rel', 'fuel': 'cost', 'rep': 'cost', 'ins': 'cost', 'yt': 'yt', 'val': 'val'}
LS_NAME = {'rel': 'Reliability & safety', 'cost': 'Cost to own', 'yt': 'What YouTube thinks', 'val': 'Holds its value'}
LS_MISS = {'rel': 'no reliability data', 'cost': 'no cost data', 'yt': 'no YouTube data yet', 'val': 'no price data'}
LS_HI = {'cpl': False, 'sev': False, 'rcl': False, 'fail': False, 'crash': True, 'fuel': False, 'rep': False, 'ins': False, 'yt': True, 'val': True}
LS_SEGW = {'fuel', 'rep', 'ins', 'val', 'yt'}   # compared within the same type of car (YouTube too: truck videos are mostly repair / tow / mod videos)
LS_RATE = 140   # $/hour, the repair estimates' default shop rate (repair_est.py)
LS_BASKET = ('brakes', 'alternator', 'starter', 'water-pump', 'struts', 'wheel-bearing', 'ac-compressor', 'fuel-pump', 'control-arms', 'radiator')
LS_FAIL = {   # data/top_fails.json failure -> the repair_est.json repair it means (failures with no single repair, e.g. stalling or rust, aren't priced)
    'Steering rack / power steering': 'steering-rack', 'Throttle body / loss of power': 'throttle-body', 'Engine failure': 'engine-replacement',
    'Transmission failure': 'transmission-replacement', 'Fuel pump': 'fuel-pump', 'Coolant leak / overheating': 'water-pump',
    'Ball joint / control arm': 'control-arms', 'Airbag light / sensor': 'airbag-module', 'Backup camera': 'backup-camera',
    'Ignition coils / misfire': 'ignition-coils', 'Timing chain': 'timing-chain', 'Brakes: ABS module / pump': 'abs-module',
    'Brake booster / hard pedal': 'brake-booster', 'Alternator': 'alternator', 'Infotainment screen / radio': 'infotainment', 'Struts / shocks': 'struts',
    'Head gasket': 'head-gasket', 'Turbocharger': 'turbo', 'Torque converter': 'torque-converter', 'Power window regulator': 'window-regulator',
    'Hybrid battery / inverter': 'hybrid-battery', 'Catalytic converter': 'catalytic-converter', 'Starter': 'starter', 'Water pump': 'water-pump',
    'Battery drain / dead battery': 'battery', 'Wheel bearing': 'wheel-bearing', 'A/C condenser': 'ac-condenser', 'A/C compressor': 'ac-compressor',
    'A/C blowing warm air': 'ac-compressor', 'Door lock actuator': 'door-lock-actuator'}
LS_SPORTS = {'chevrolet-camaro', 'chevrolet-corvette', 'dodge-challenger', 'ford-mustang', 'nissan-350z', 'hyundai-tiburon'}   # insurance.json "sports car" type
LS_VAL_Y0 = 2011   # 11-26 v2 (Elijah's review: the Crown Vic, Century and Saturn SL read as holding value): AI prices of cars over ~15 years old barely move, so value is
                   # scored only from model years 2011+; older model years get no value part (partial)
LS_SEG = lambda seg: 'minivan' if seg in ('minivan', 'van') else seg

_LS_SAFE = (_load('data/safety_ratings.json') or {}).get('m', {})
_LS_TF = _load('data/top_fails.json')
_LS_PE = (_lsj.load(open('data/price_est.json', encoding='utf-8')) if os.path.exists('data/price_est.json') else {}).get('m', {})
_LS_RU = _lsj.load(open('data/recall_units.json', encoding='utf-8')) if os.path.exists('data/recall_units.json') else {}
_LS_IN = _lsj.load(open('data/insurance.json', encoding='utf-8'))
_LS_INS = _lsst.mean(s['est'][_LS_IN['meta']['ages'].index('30-39')] for s in _LS_IN['states'].values())   # U.S. average, 30-39, clean record, $/month
_LS_INK = lambda fid, seg: 'sports' if fid in LS_SPORTS else 'truck' if seg == 'truck' else 'regular'

def _ls_pct(d, higher=True):
    """{key: value} -> {key: 0-100 percentile}, ties share their middle rank; 100 = best"""
    it = sorted(d.items(), key=lambda kv: kv[1]); n = len(it); out = {}; i = 0
    while i < n:
        j = i
        while j + 1 < n and it[j + 1][1] == it[i][1]: j += 1
        p = ((i + j) / 2 + .5) / n * 100 if n > 1 else 50.0
        for k in range(i, j + 1): out[it[k][0]] = p if higher else 100 - p
        i = j + 1
    return out

def _ls_rmid(rows):
    ok = [r for r in rows or [] if r[5] != 'X']
    return _lsst.mean((r[1] + r[2]) / 2 * LS_RATE + (r[3] + r[4]) / 2 for r in ok) if ok else None

_LS_GC = {}
def _ls_gen(gid):
    """(basket $, {repair slug: $}) for one repair_est generation"""
    if gid not in _LS_GC:
        g = REST._data()['gens'][gid]; c = {s: _ls_rmid(rows) for s, rows in g['r'].items()}
        b = [c[s] for s in LS_BASKET if c.get(s)]
        _LS_GC[gid] = (_lsst.mean(b) if len(b) >= 6 else None, c)
    return _LS_GC[gid]

def _ls_year_raw(f, v, seg):
    fid, y = f['id'], v['y']; x = extra(fid, y); r = {}; meta = {}
    if v.get('ok') and v.get('li') is not None: r['cpl'] = v['li']
    sv = (XL.get(fid, {}).get(str(y)) or {}).get('sev') or {}
    if (sv.get('total') or 0) >= 30:
        r['sev'] = min(100, (sv.get('crash', 0) + sv.get('fire', 0) + sv.get('injured', 0) + sv.get('towed', 0)) / sv['total'] * 100); meta['sev_n'] = sv['total']
    if isinstance(x.get('recalls'), list):
        rs = x['recalls']; bad = sum(1 for q in rs if any((_LS_RU.get(q.get('id')) or [0, 0, 0])[1:]))
        r['rcl_raw'] = len(rs) + 2 * bad; meta['rcl'] = (len(rs), bad)
    sf = _LS_SAFE.get(fid, {}).get(str(y))
    if sf and sf.get('overall'): r['crash'] = sf['overall']; meta['crash'] = (sf['overall'], sf['n'])
    mp = x.get('mpg')
    if mp and mp.get('cost'): r['fuel'] = _lsst.mean(mp['cost']) / 12
    gid = REST.gen_for(fid, y)
    if gid:
        bk, cost = _ls_gen(gid)
        if bk: r['rep'] = bk
        tf = (_LS_TF.get(fid, {}).get(str(y)) or {}).get('top') or []
        fl = [(t['n'], cost[LS_FAIL[t['t']]]) for t in tf if LS_FAIL.get(t['t']) and cost.get(LS_FAIL[t['t']])]
        if fl:
            r['fail'] = sum(n * c for n, c in fl) / sum(n for n, _ in fl); meta['fail_w'] = sum(n for n, _ in fl)
            meta['fail_top'] = max(((n, t['t']) for t in tf for n in [t['n']] if LS_FAIL.get(t['t']) and cost.get(LS_FAIL[t['t']])), default=(0, ''))[1]
    r['ins'] = _LS_INS * _LS_IN['meta']['car'][_LS_INK(fid, seg)]
    return r, meta

def _ls_value(fids):
    """{fid: (relative log-loss per year vs same-type cars at the same ages + miles, own yearly loss %, same-type yearly loss %)}"""
    G = {}
    for fid in fids:
        m = _LS_PE.get(fid)
        if not m: continue
        ys = m['y']; out = []
        for y in range(LS_VAL_Y0, 2023):
            a, b = ys.get(str(y)), ys.get(str(y + 1))
            if not a or not b: continue
            for k in (1, 2):   # 50-100K and 100-150K
                p0, p1 = a[1][k], b[1][k]
                if not p0 or not p1: continue
                m0, m1 = (p0[0] + p0[1]) / 2, (p1[0] + p1[1]) / 2
                if m0 > 0 and m1 > 0: out.append(((k, y), _lsm.log(m1 / m0)))
        if out: G[fid] = out
    return G

def _ls_combine(sp):
    """sub-percentiles {sub: 0-100} -> (composite or None, {part: score}, partial, [missing words])"""
    parts = {}
    for p in LS_W:
        subs = [s for s in sp if LS_OF[s] == p]
        tot = sum(LS_SW[s] for s in subs)
        if not subs: continue
        if p == 'rel' and tot < 20: continue
        if p == 'cost' and not ({'fuel', 'rep'} & set(subs)): continue
        parts[p] = sum(sp[s] * LS_SW[s] for s in subs) / tot
    if len(parts) < 3: return None, parts, True, [LS_MISS[p] for p in LS_W if p not in parts]
    comp = sum(LS_W[p] * parts[p] for p in parts) / sum(LS_W[p] for p in parts)
    miss = [LS_MISS[p] for p in LS_W if p not in parts] + (['no complaint rate'] if 'rel' in parts and 'cpl' not in sp else [])
    return comp, parts, bool(miss), miss

def _ls_score_pool(raw, segof):
    """raw {key: {sub: value}} -> {key: {sub: percentile}}"""
    sp = {k: {} for k in raw}
    for s in LS_SW:
        vals = {k: r[s] for k, r in raw.items() if r.get(s) is not None}
        if not vals: continue
        if s in LS_SEGW:
            for g in {segof(k) for k in vals}:
                sub = {k: v for k, v in vals.items() if segof(k) == g}
                for k, p in _ls_pct(sub, LS_HI[s]).items(): sp[k][s] = p
        else:
            for k, p in _ls_pct(vals, LS_HI[s]).items(): sp[k][s] = p
    return sp

def _ls_build():
    M, Y = {}, {}
    segm = {f['id']: LS_SEG(BYNAME[f['name']]['seg']) for f in YEARS}
    yraw, ymeta = {}, {}
    for f in YEARS:
        for v in f['years']:
            r, mt = _ls_year_raw(f, v, segm[f['id']])
            yraw[(f['id'], v['y'])] = r; ymeta[(f['id'], v['y'])] = mt
    # recalls: compared with the median car of the same model year
    byy = defaultdict(list)
    for (fid, y), r in yraw.items():
        if 'rcl_raw' in r: byy[y].append(r['rcl_raw'])
    RMED = {y: _lsst.median(v) for y, v in byy.items() if len(v) >= 10}
    for (fid, y), r in yraw.items():
        if 'rcl_raw' in r and y in RMED: r['rcl'] = r['rcl_raw'] - RMED[y]; ymeta[(fid, y)]['rcl_med'] = RMED[y]
    # YouTube: each year vs the median car of the same model year (build.py yt_adj), rankable years only
    YA = {}
    for f in YEARS:
        okr = yt_rankable(f, YTS.get(f['id'], {})); a = yt_adj(f['id'])
        YA[f['id']] = {y: d for y, d in a.items() if y in okr}
        for y, d in YA[f['id']].items():
            if (f['id'], y) in yraw: yraw[(f['id'], y)]['yt'] = d
    # value: like with like (same type, same bracket, same model-year pair)
    G = _ls_value([f['id'] for f in YEARS])
    cell = defaultdict(list)
    for fid, prs in G.items():
        for key, g in prs: cell[(segm[fid], key)].append(g)
    CMED = {k: _lsst.median(v) for k, v in cell.items() if len(v) >= 3}
    VAL = {}
    for fid, prs in G.items():
        d = [(g, CMED[(segm[fid], key)]) for key, g in prs if (segm[fid], key) in CMED]
        if len(d) >= 3:
            own = _lsst.mean(g for g, _ in d); ref = _lsst.mean(c for _, c in d)
            VAL[fid] = (-(own - ref), (1 - _lsm.exp(-own)) * 100, (1 - _lsm.exp(-ref)) * 100, len(d))   # own/ref = log price step per year of age (newer / older)
    # model-level raw inputs
    mraw, mmeta = {}, {}
    for f in YEARS:
        fid = f['id']; c = BYNAME[f['name']]; r = {}; mt = {'seg': segm[fid]}
        if fid not in FS_IDS and c.get('li') is not None: r['cpl'] = c['li']
        yy = [(v['y'], yraw[(fid, v['y'])], ymeta[(fid, v['y'])]) for v in f['years']]
        sv = [XL.get(fid, {}).get(str(y), {}).get('sev') or {} for y, _, _ in yy]
        tot = sum(s.get('total') or 0 for s in sv)
        if tot >= 50: r['sev'] = min(100, sum(s.get('crash', 0) + s.get('fire', 0) + s.get('injured', 0) + s.get('towed', 0) for s in sv) / tot * 100)
        rc = [x['rcl'] for _, x, _ in yy if 'rcl' in x]
        if len(rc) >= 2:
            r['rcl'] = _lsst.mean(rc); mt['rcl'] = (_lsst.mean(x['rcl_raw'] for _, x, _ in yy if 'rcl' in x), _lsst.mean(m['rcl_med'] for _, x, m in yy if 'rcl' in x))
        fw = [(m['fail_w'], x['fail']) for _, x, m in yy if 'fail' in x]
        if fw: r['fail'] = sum(w * c_ for w, c_ in fw) / sum(w for w, _ in fw)
        cr = [x['crash'] for _, x, _ in yy if 'crash' in x]
        if cr: r['crash'] = _lsst.mean(cr); mt['crash'] = (r['crash'], len(cr))
        for s in ('fuel', 'rep'):
            vs = [x[s] for _, x, _ in yy if s in x]
            if vs: r[s] = _lsst.mean(vs)
        r['ins'] = _LS_INS * _LS_IN['meta']['car'][_LS_INK(fid, segm[fid])]
        a = YA.get(fid, {})
        if len(a) >= 4:
            w = {y: YTS[fid][str(y)]['videos'] for y in a}
            r['yt'] = sum(a[y] * w[y] for y in a) / sum(w.values()); mt['yt'] = (round(sum(w.values())), len(a))
        if fid in VAL: r['val'] = VAL[fid][0]; mt['val'] = VAL[fid][1:]
        mraw[fid] = r; mmeta[fid] = mt
    # percentiles, parts, the score
    msp = _ls_score_pool(mraw, lambda k: segm[k])
    mc = {}
    for fid, sp in msp.items():
        comp, parts, partial, miss = _ls_combine(sp)
        if 'val' not in parts and _LS_PE.get(fid): miss = ['no resale part (older model years)' if m == LS_MISS['val'] else m for m in miss]
        M[fid] = dict(comp=comp, parts=parts, partial=partial, miss=miss, sp=sp, raw=mraw[fid], meta=mmeta[fid])
        if comp is not None: mc[fid] = comp
    for fid, c_ in mc.items(): M[fid]['s'] = max(1, min(99, round(c_)))   # the weighted average itself (median car ~50); a 2nd percentile pass exaggerated small gaps
    for k in yraw:   # the value part of a model year is its model's (none for years over ~15 years old: their AI prices barely move)
        if k[0] in VAL and k[1] >= LS_VAL_Y0: yraw[k]['val'] = VAL[k[0]][0]
    ysp = _ls_score_pool({k: {s: v for s, v in r.items() if s != 'rcl_raw'} for k, r in yraw.items()}, lambda k: segm[k[0]])
    yc = {}
    early = {(f['id'], v['y']) for f in YEARS for v in f['years'] if v.get('early')}
    for k, sp in ysp.items():
        comp, parts, partial, miss = _ls_combine(sp)
        if k in early: partial = True; miss = ['too new (complaints still coming in)'] + miss
        if k[1] < LS_VAL_Y0 and LS_MISS['val'] in miss: miss = [m if m != LS_MISS['val'] else 'no resale part (15+ years old)' for m in miss]
        Y.setdefault(k[0], {})[k[1]] = dict(comp=comp, parts=parts, partial=partial, miss=miss, sp=sp, raw=yraw[k], meta=dict(ymeta[k], seg=segm[k[0]], val=mmeta[k[0]].get('val')))
        if comp is not None: yc[k] = comp
    for k, c_ in yc.items(): Y[k[0]][k[1]]['s'] = max(1, min(99, round(c_)))
    return M, Y

LS_M, LS_Y = _ls_build()
LS = lambda fid: (LS_M.get(fid) or {}).get('s')
LS_YR = lambda fid, y: ((LS_Y.get(fid) or {}).get(y) or {}).get('s')
print(f'lemon score: {sum(1 for m in LS_M.values() if m.get("s") and not m["partial"])} full, {sum(1 for m in LS_M.values() if m.get("s") and m["partial"])} partial, '
      f'{sum(1 for m in LS_M.values() if not m.get("s"))} none of {len(LS_M)} models; model years: '
      f'{sum(1 for d in LS_Y.values() for m in d.values() if m.get("s") and not m["partial"])} full, {sum(1 for d in LS_Y.values() for m in d.values() if m.get("s") and m["partial"])} partial')

# ---------- display ----------
def ls_band(s):   # cut points from the 11-26 spread of model scores: about the top 10% / next 20% / middle / next 20% / bottom 10%
    if s >= 63: return 'good', 'One of the best buys'
    if s >= 56: return 'good', 'Better buy than most'
    if s >= 45: return 'mid', 'About average'
    if s >= 38: return 'bad', 'Worse buy than most'
    return 'bad', 'One of the worst buys'
_ls_cls = lambda p: 'good' if p >= 60 else 'bad' if p <= 40 else 'mid'
_LS_INFO = '<svg aria-hidden="true" focusable="false" width="16" height="16"><use href="/assets/ic.svg?v=1#info"></use></svg>'
_LS_WARN = '<svg aria-hidden="true" focusable="false" width="16" height="16"><use href="/assets/ic.svg?v=1#warning"></use></svg>'
_LS_EST = '<i class="ls-est">EST</i>'
_ls_usd = lambda v: f'${round(v / 10) * 10:,.0f}' if v < 1000 else f'${round(v / 50) * 50:,.0f}'

def _ls_rows(d, year=None):
    """the inputs under each part: [(part, label html, value html)]. 11-27 (Elijah: "Owners vs other cars: -1" meant nothing): every input
    says in one short line what it is and what's typical, a small bar shows where the car sits against other cars (the input's own 0-100
    score: middle tick = typical, right = better), and links go to the page's deeper section (#@key: LS_HOOK keeps only links whose
    target is on the page)"""
    r, mt, sp = d['raw'], d['meta'], d['sp']; out = []; fid = d.get('fid'); seg = mt.get('seg')
    sw = _LS_SEGW_N.get(seg, 'car'); typ = lambda k: _ls_typ(k, seg, year)
    def row(part, lab, mean, val, s=None, go=''):
        out.append((part, f'{lab}<small>{mean}</small>' + (_ls_mb(sp[s]) if s in sp else '') + go, val))
    if 'cpl' in r:
        row('rel', 'Complaint Score', 'owner complaints per car sold · 100 = average car, lower is better', f'<b class="{band(r["cpl"])[0]}">{round(r["cpl"])}</b>', 'cpl', _ls_go('cpl', 'Problems'))
    else:
        row('rel', 'Complaint Score', 'owner complaints per car sold', '<span class="ls-na">no sales figure to score</span>')
    if 'sev' in r: row('rel', 'Serious complaints', 'share that report a crash, fire, injury or tow', f'<b>{r["sev"]:.0f}%</b>', 'sev')
    if year is not None and 'rcl' in mt:
        n, bad = mt['rcl']
        row('rel', 'Recalls', (f'{bad} do-not-drive or park-outside · ' if bad else '') + f'typical car this year: {mt.get("rcl_med", 0):g}', f'<b>{n}</b>', 'rcl', _ls_go('rcl', 'Recalls'))
    elif 'rcl' in mt:
        a, b = mt['rcl']; row('rel', 'Recalls per model year', f'typical car, same years: {b:.1f}', f'<b>{a:.1f}</b>', 'rcl')
    if 'fail' in r:
        row('rel', f'Common failures cost {_LS_EST}' + _ls_ii(_LS_FAIL_WHY.format(w='this year' if year is not None else 'this model')),
            'what fixing the problems owners report most costs', f'<b>{_ls_usd(r["fail"])}</b>', 'fail')
    if 'crash' in r:
        st, n = mt['crash']
        row('rel', 'NHTSA crash test', 'overall stars, out of 5' + (f' · {n} versions' if year is not None and n > 1 else ''), f'<b>{st:.1f}★</b>' if st % 1 else f'<b>{st:.0f}★</b>', 'crash')
    else:
        out.append(('rel', 'NHTSA crash test', '<span class="ls-na">not rated' + (' (2011+ only)' if (year or 2011) < 2011 else '') + '</span>'))
    if 'fuel' in r:
        m = (extra(fid, year).get('mpg') or {}) if year is not None and fid else {}
        cb = m.get('comb'); cb = [c for c in cb if c] if isinstance(cb, list) else ([cb] if cb else [])
        mpg = ((f'EPA {min(cb):.0f} mpg' if round(min(cb)) == round(max(cb)) else f'EPA {min(cb):.0f}-{max(cb):.0f} mpg') if cb else 'EPA fuel cost')
        row('cost', 'Fuel', mpg + (f' · typical {sw}: {_ls_usd(typ("fuel"))}/mo' if typ('fuel') else ''), f'<b>{_ls_usd(r["fuel"])}/mo</b>', 'fuel')
    if 'rep' in r:
        row('cost', f'Everyday repairs {_LS_EST}', 'our average for 10 common repairs (brakes, starter, struts...) at $140/hr + parts'
            + (f' · typical {sw}: {_ls_usd(typ("rep"))}' if typ('rep') else ''), f'<b>{_ls_usd(r["rep"])}</b>', 'rep', _ls_go('rep', 'Repair prices'))
    row('cost', f'Insurance {_LS_EST}', 'per month: state averages × car type, driver 30-39, clean record', f'<b>{_ls_usd(r["ins"])}/mo</b>', 'ins',
        '<a class="ls-go" href="/insurance/">Insurance by state ›</a>')
    if 'yt' in r:
        ys = (YTS.get(fid) or {}).get(str(year)) if year is not None and fid else None
        if ys and ys.get('score') is not None and year in YTB:
            row('yt', 'YouTube owner score', f'how positive {round(ys.get("videos") or 0):,} owner and review videos sound, 0-100 · typical car this year: {YTB[year]:.0f}',
                f'<b>{ys["score"]}</b>', 'yt', _ls_go('yt', 'What owners say'))
        else:
            dv = r['yt']; nv = f'{mt["yt"][0]:,} videos, ' if 'yt' in mt else ''
            row('yt', 'YouTube owner score vs typical', f'how positive owner and review videos sound ({nv}0-100), minus the typical car of the same years',
                f'<b>{"+" if dv >= 0 else "−"}{abs(dv):.0f}</b>', 'yt', _ls_go('yt', 'What owners say'))
    vm = mt.get('val')
    if vm and 'val' in sp:
        own, ref = vm[0], vm[1]
        row('val', f'Value lost per year {_LS_EST}', f'at the same miles, from our price estimates · similar {sw}s: {ref:.0f}%', f'<b>{own:.0f}%</b>', 'val')
    return out

# 11-27 helpers for the parts list + the "why" line (LS_HOOK -> _ls_explain)
_LS_SEGW_N = {'car': 'car', 'suv': 'SUV', 'truck': 'truck', 'minivan': 'minivan'}
_LS_TYP = {}
def _ls_typ(key, seg, year):
    """the typical (median) raw value of one input among cars of the same type: model years for a year page, models for a model page"""
    k = (key, seg, year is not None)
    if k not in _LS_TYP:
        pool = [yd for dd in LS_Y.values() for yd in dd.values()] if year is not None else list(LS_M.values())
        vs = [x['raw'][key] for x in pool if x['raw'].get(key) is not None and x['meta'].get('seg') == seg]
        _LS_TYP[k] = _lsst.median(vs) if vs else None
    return _LS_TYP[k]
def _ls_mb(v):
    """a small bar: the input's 0-100 score against other cars (middle tick = typical, right = better)"""
    return f'<i class="ls-mb {_ls_cls(v)}" style="--v:{max(2, min(98, v)):.0f}%" aria-hidden="true"></i>'
_LS_GO = {'cpl': ('p-problems', 'problems'), 'rcl': ('p-recalls', 'recalls'), 'rep': ('estimates', 'p-repairs', 'repairs'), 'yt': ('mhb-owners', 'youtube', 'yt-owners')}
_ls_go = lambda k, lab: f'<a class="ls-go" href="#@{k}">{lab} ›</a>'
def _ls_links(fig, doc):
    """#@key -> the first of that key's section ids found on the page; a link with no target there goes"""
    def one(m):
        t = next((i for i in _LS_GO.get(m.group(1), ()) if f'id="{i}"' in doc), None)
        if not t: return '<a class="ls-go" hidden>'
        c = _lsre.search(rf'id="{t}"><a class="mhc" href="([^"#]+)"', doc)   # a hub card that links to its own page (Problems, Repairs & costs...): go there
        if c: return f'<a class="ls-go" href="{c.group(1)}{"#estimates" if m.group(1) == "rep" else ""}">'
        return f'<a class="ls-go" href="#{t}">'
    fig = _lsre.sub(r'<a class="ls-go" href="#@(\w+)">', one, fig)
    return _lsre.sub(r'<a class="ls-go" hidden>[^<]*</a>', '', fig)
_LS_WD = {'cpl': ('many owner complaints per car sold', 'few owner complaints per car sold'),
          'sev': ('a high share of serious complaints', 'few serious complaints'),
          'rcl': ('more recalls than most cars', 'fewer recalls than most cars'),
          'fail': ('costly common failures', 'cheap common failures'),
          'crash': ('a weak crash-test rating', 'a strong crash-test rating'),
          'fuel': ('high fuel cost for its type', 'low fuel cost for its type'),
          'rep': ('pricey everyday repairs', 'cheap everyday repairs'),
          'ins': ('high insurance cost', 'low insurance cost'),
          'yt': ('lukewarm YouTube owner reviews', 'warm YouTube owner reviews'),
          'val': ('losing value fast', 'holding its value well')}
def _ls_why(d):
    """one plain line: the inputs that moved this score most (from its own numbers: each input's points above or below the middle car)"""
    sp, parts = d['sp'], d['parts']; tw = sum(LS_W[p] for p in parts) or 1; con = []
    for s, v in sp.items():
        p = LS_OF[s]
        if p not in parts or s not in _LS_WD: continue
        sw_ = sum(LS_SW[x] for x in sp if LS_OF[x] == p)
        con.append((LS_W[p] / tw * LS_SW[s] / sw_ * (v - 50), s))
    neg = sorted(c for c in con if c[0] <= -1.5); pos = sorted((c for c in con if c[0] >= 1.5), reverse=True)
    say = lambda cs: ' and '.join(_LS_WD[s][0 if c < 0 else 1] for c, s in cs)
    b = ls_band(d['s'])[0]
    if b == 'bad' and neg: return f'Mostly because of {say(neg[:2])}.'
    if b == 'good' and pos: return f'Mostly because of {say(pos[:2])}.'
    bits = ([f'helped by {say(pos[:1])}'] if pos else []) + ([f'held back by {say(neg[:1])}'] if neg else [])
    return (', '.join(bits) + '.')[0].upper() + (', '.join(bits) + '.')[1:] if bits else ''
def _ls_explain(fig, d, y, doc):
    """LS_HOOK: the why line at the top of the open (i), a bar legend, why each missing part is missing, and the section links"""
    why = _ls_why(d)
    if why: fig = fig.replace('<div class="ls-ddb">', f'<div class="ls-ddb"><p class="ls-why">{_lsh.escape(why)}</p>', 1)   # first thing in the open (i)
    fig = fig.replace('<div class="ls-ps4">', '<p class="ls-lg"><i class="ls-mb good" style="--v:75%" aria-hidden="true"></i><span>Bars: vs other cars, middle = typical, right = better</span></p><div class="ls-ps4">', 1)
    for p in LS_W:
        if p in d['parts']: continue
        ms = [m for m in d['miss'] if m == LS_MISS[p] or (p == 'val' and m.startswith('no resale part'))]
        w = ' '.join(_LS_WHY[m] for m in ms if m in _LS_WHY)
        if not w: continue
        fig = _lsre.sub(rf'<div class="ls-p ls-p0">(<span class="ls-pn">{_lsre.escape(LS_NAME[p])}<small>.*?</small></span>.*?)</div>',
                        lambda m: f'<details class="ls-p ls-pm"><summary>{m.group(1)}</summary><p class="ls-ps">{_lsh.escape(w)}</p></details>', fig, count=1, flags=_lsre.S)
    return _ls_links(fig, doc)

_LS_SRC = {'rel': 'NHTSA owner complaints and U.S. sales, NHTSA recalls and 5-Star crash tests; failure costs are AI repair estimates.',
           'cost': 'EPA fuel cost (fueleconomy.gov); repair and insurance numbers are estimates (AI repair estimates at $140/hour; NAIC state averages).',
           'yt': 'What owners and reviewers say in YouTube videos about each model year, compared with other cars of the same years.',
           'val': 'AI price estimates by mileage (not listings): how much a year of age takes off at the same miles, vs the same type of car.'}

def _ls_parts(d, y):
    """the (i) dropdown: the 4 parts with their weight and this car's part score, each opening to its inputs and source"""
    rows = _ls_rows(d, y); out = ''
    for p in LS_W:
        nm = f'<span class="ls-pn">{LS_NAME[p]}<small>{LS_W[p]}%</small></span>'
        if p in d['parts']:
            ps = round(d['parts'][p]); pc = _ls_cls(ps)
            inner = ''.join(f'<li><span>{lab}</span>{val}</li>' for pp, lab, val in rows if pp == p)
            out += (f'<details class="ls-p"><summary>{nm}<span class="ls-pb {pc}"><i style="width:{max(3, ps)}%"></i></span>'
                    f'<b class="ls-pv {pc}">{ps}</b></summary><ul class="ls-pr">{inner}</ul><p class="ls-ps">{_LS_SRC[p]}</p></details>')
        else:
            out += f'<div class="ls-p ls-p0">{nm}<span class="ls-pb"></span><span class="ls-pv ls-na">–</span></div>'
    return out

# 11-27 (Elijah couldn't tell what "Partial score: no resale part" meant): the partial line opens a short plain explanation, one per reason
# _ls_combine / _ls_build can give (LS_MISS + the extra miss strings); a reason not listed here just shows the general line
_LS_WHY = {
    LS_MISS['rel']: 'Not enough complaint, recall and crash-test data, so the Reliability & safety part is left out.',
    LS_MISS['cost']: 'No EPA fuel cost or repair estimates for it yet, so the Cost to own part is left out.',
    LS_MISS['yt']: 'Too few YouTube owner and review videos about it so far, so the What YouTube thinks part is left out.',
    LS_MISS['val']: 'No price estimates for it yet, so the Holds its value part is left out.',
    'no resale part (15+ years old)': ('We only score resale for 2011 and newer model years: price estimates for older cars barely change from one year to the next, '
                                       'so the Holds its value part is left out.'),
    'no resale part (older model years)': ('We only score resale for 2011 and newer model years (older cars’ price estimates barely move), and this model has too few of them, '
                                           'so the Holds its value part is left out.'),
    'no complaint rate': 'No Complaint Score (we need a sales figure to count complaints per car sold), so Reliability & safety uses its other numbers.',
    'too new (complaints still coming in)': 'Owner complaints take about 3 years to come in, so this is an early read.',
}
_LS_FAIL_WHY = ('The problems owners report most for {w} (NHTSA complaints), each priced with our repair estimate (labor hours × $140/hr + parts) '
                'and weighted by how often owners name it. Problems with no single fix, like stalling, aren’t counted. Real prices vary by shop and area.')
def _ls_ii(text):
    """a tiny (i) that opens one short explanation under a label (assets/ls.css .ls-ii)"""
    return (f'<details class="ls-ii"><summary aria-label="What this means"><span class="ls-iic">{_LS_INFO}</span></summary>'
            f'<span class="ls-iit">{_lsh.escape(text)}</span></details>')
def _ls_partial(d, y):
    if not d['partial']: return ''
    why = ' '.join(_LS_WHY[m] for m in d['miss'] if m in _LS_WHY)
    lead = (f'A partial score is missing one of the 4 parts, so it uses the other {len(d["parts"])}' if len(d['parts']) < 4 else
            'A partial score is missing part of its data')
    lead += '.' if y else ', and the car isn’t ranked in our best-of lists.'
    return (f'<details class="ls-pl"><summary>{_LS_WARN}<span>Partial score: {_lsh.escape(d["miss"][0])}</span><span class="ls-iic">{_LS_INFO}</span></summary>'
            f'<p class="ls-plb">{_lsh.escape(lead)} {_lsh.escape(why)}</p></details>')

def ls_hero(fid, y=None, name='', facts=()):
    """11-26 v2 (Elijah: "put it still where the old average car score thing was ... a bar and it has the score ... just now it's a lemon score
    and it has an info icon saying what this score is made of, and then it drops down the things and what percentage they affect the score"):
    the hero's bar (model_hero.py _mh_gauge look), flipped for higher = better: Bad (red) left, 50 = middle car, Good (green) right; the big
    number; "Lemon Score"; the band word + (i) that drops down the 4 parts. Partial = one small line under it."""
    d = (LS_Y.get(fid) or {}).get(y) if y else LS_M.get(fid)
    if not d or not d.get('s'): return ''
    d = dict(d, fid=fid); s = d['s']; cls, word = ls_band(s)
    what = f'{y} {name}' if y else name
    part = _ls_partial(d, y)   # 11-27: the partial line opens a one-line plain explanation
    # 11-26 v3 (Elijah's taste: no uppercase kicker, no repeated warning): one plain line heads the parts
    head = (f'Uses {len(d["parts"])} of the 4 parts: {_lsh.escape("; ".join(d["miss"]))}.' if d['partial'] else 'Made of 4 parts:')
    # 11-26 v2 (coordinator): the old number first, on its own line: older videos quote it ("Lemon Index 19, lower is better"), so it's one tap away
    cp = d['raw'].get('cpl')
    cs = (f'<div class="ls-cs"><span>Complaint Score<small>100 = average car, lower is better</small></span><b class="{band(cp)[0]}">{round(cp)}</b></div>' if cp is not None else
          '<div class="ls-cs"><span>Complaint Score<small>owner complaints per car sold</small></span><span class="ls-na">no sales figure to score</span></div>')
    fx = (''.join(f'<li>{x}</li>' for x in facts))
    fx = f'<ul class="ls-fx">{fx}</ul>' if fx else ''
    return (f'<figure class="mh-bar ls-bar {cls}" data-gauge style="--p:{s}%" aria-label="Lemon Score {s} out of 100 for the {_lsh.escape(what)}: {word.lower()}">'
            f'<div class="mh-track" aria-hidden="true"><i class="lsb-r"></i><i class="lsb-m"></i><i class="lsb-g"></i><span class="mh-pin"></span></div>'
            f'<div class="mh-labs" aria-hidden="true"><span class="lsb-bad">Bad</span><span class="mh-avg">50 = middle car</span><span class="lsb-good">Good</span></div>'
            f'<figcaption><b>{s}</b><span class="ls-k">Lemon Score</span></figcaption>{part}'   # the partial line once, under the score (above the dropdown)   # the dropdown sits outside the figcaption: model_hero's figcaption b/span styles stay off it
            f'<details class="ls-dd"><summary aria-label="{word}. What the Lemon Score is made of"><span class="ls-w {cls}">{word}</span><span class="ls-ib">{_LS_INFO}</span></summary>'
            f'<div class="ls-ddb">{cs}<p class="ls-ddh">{head}</p><div class="ls-ps4">{_ls_parts(d, y)}</div>{fx}'
            f'<a class="ls-how" href="/lemon-score/">How the Lemon Score works</a></div></details></figure>')

LS_CSS = f'<link rel="stylesheet" href="/assets/ls.css?v={LS_V}">'
_LS_CAR = _lsre.compile(r'/cars/(.+?)/(?:(\d{4})/)?')
_LS_FIG = _lsre.compile(r'<figure[^>]*class="mh-bar[^"]*"[^>]*>.*?</figure>', _lsre.S)

def _ls_name(doc):
    m = _lsre.search(r'<span class="yct-big">(.*?)</span>', doc) or _lsre.search(r'<h1[^>]*>(.*?)</h1>', doc, _lsre.S)
    return _lsre.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''

# the old number keeps its meaning under its new name: "Lemon Index 49" -> "Complaint Score 49" (the site and brand stay "Lemon Index")
_LS_RN = [(_lsre.compile(r'Lemon Index(?= \d)'), 'Complaint Score'), (_lsre.compile(r'Lemon Index(?= of \d)'), 'Complaint Score'),
          (_lsre.compile(r'(?<=\d{4} )Lemon Index'), 'Complaint Score'), (_lsre.compile(r'Lemon Index(?= ·)'), 'Complaint Score'),
          (_lsre.compile(r'Lemon Index(?= \(partial)'), 'Complaint Score'), (_lsre.compile(r'The Lemon Index counts owner complaints'), 'The Complaint Score counts owner complaints'),
          (_lsre.compile(r'No Lemon score'), 'No Complaint Score'), (_lsre.compile(r'its Lemon Index'), 'its Complaint Score'),
          (_lsre.compile(r'(?<=[(>] )?Lemon Index(?= = )'), 'Complaint Score'), (_lsre.compile(r'Lemon Index(?=: \d+ = the average)'), 'Complaint Score'),
          (_lsre.compile(r'Lemon Index(?= \(\d+ = average\))'), 'Complaint Score'), (_lsre.compile(r'\(Lemon Index \+ YouTube'), '(Complaint Score + YouTube'),
          (_lsre.compile(r'a Lemon Index:'), 'a Complaint Score:'), (_lsre.compile(r'No Lemon Index here'), 'No Complaint Score here')]
def LS_RENAME(doc):
    for rx, to in _LS_RN: doc = rx.sub(to, doc)
    return doc

_LS_YSRC = _lsre.compile(r'<details class="yux-src">.*?</details>', _lsre.S)
def LS_HOOK(path, doc):
    m = _LS_CAR.fullmatch(path)
    if m and 'class="ph tb-hero' in doc:
        fid, y = m.group(1), int(m.group(2)) if m.group(2) else None
        facts = ()
        if y:   # the year hero's "See where the score comes from" sheet: its numbers move into the (i) dropdown (one info button, not two)
            sm = _LS_YSRC.search(doc)
            if sm and (LS_Y.get(fid) or {}).get(y, {}).get('s'):
                facts = [x for x in _lsre.findall(r'<li>(.*?)</li>', sm.group(0), _lsre.S) if not x.startswith('Owner complaints per car sold, compared')]
                doc = doc[:sm.start()] + doc[sm.end():]
        fig = ls_hero(fid, y, _ls_name(doc), facts)
        if fig: fig = _ls_explain(fig, dict((LS_Y.get(fid) or {}).get(y) if y else LS_M.get(fid), fid=fid), y, doc)   # 11-27: why line, missing-part reasons, links
        if fig:
            fm = _LS_FIG.search(doc)
            if fm:   # the hero's Complaint Score bar (model_hero.py / year_ux.py) becomes the Lemon Score bar; the Complaint Score sits inside its (i)
                doc = doc[:fm.start()] + LS_CSS + fig + doc[fm.end():]
            elif y and '<div class="yhero">' in doc:   # a year with no Complaint Score (too few complaints or sales): its "no score" verdict gives way
                k = doc.find('<div class="yhero">'); e = _ls_end(doc, k)
                if e > 0: doc = (doc[:k] + LS_CSS + f'<div class="yux-score">{fig}</div>' + doc[e:]).replace('<div class="yux-score yux-na"></div>', '', 1)
            else:   # model pages with no Complaint Score bar (the F-150): under the photo slider
                st = doc.find('class="yx-stage"')
                k = doc.find('</section>', st) + 10 if st > 0 else -1
                if k > 9: doc = doc[:k] + LS_CSS + f'<div class="mh-score ls-only">{fig}</div>' + doc[k:]
    return LS_RENAME(doc)

def _ls_end(doc, k, tag='div'):
    depth = 0
    for mm in _lsre.finditer(rf'<{tag}|</{tag}>', doc[k:]):
        depth += 1 if mm.group(0) != f'</{tag}>' else -1
        if depth == 0: return k + mm.end()
    return -1

def ls_chip(fid, y=None):
    s = LS_YR(fid, y) if y else LS(fid)
    if not s: return ''
    return f'<span class="ls-chip {ls_band(s)[0]}" title="Lemon Score {s} out of 100"><b>{s}</b><small>Lemon Score</small></span>'

def ls_export(out_dir):
    """docs/data/lemon-score.json + .csv: every model's score, parts and inputs (the build output, never committed)"""
    rows, js = [], {}
    nm = {f['id']: f['name'] for f in YEARS}
    for fid, d in sorted(LS_M.items()):
        rec = dict(name=nm[fid], score=d.get('s'), partial=d['partial'], missing=d['miss'], parts={p: round(v, 1) for p, v in d['parts'].items()},
                   inputs={k: (round(v, 2) if isinstance(v, float) else v) for k, v in d['raw'].items()}, input_pct={k: round(v, 1) for k, v in d['sp'].items()},
                   years={y: dict(score=yd.get('s'), partial=yd['partial'], parts={p: round(v, 1) for p, v in yd['parts'].items()}) for y, yd in sorted((LS_Y.get(fid) or {}).items())})
        js[fid] = rec
        rows.append([fid, nm[fid], d.get('s') or '', 'partial' if d['partial'] else 'full' if d.get('s') else 'none', '; '.join(d['miss'])]
                    + [round(d['parts'][p]) if p in d['parts'] else '' for p in LS_W]
                    + [round(d['raw'][k], 1) if isinstance(d['raw'].get(k), float) else d['raw'].get(k, '') for k in ('cpl', 'sev', 'rcl', 'fail', 'crash', 'fuel', 'rep', 'ins', 'yt', 'val')])
    os.makedirs(out_dir, exist_ok=True)
    _lsj.dump(dict(made=TODAY, weights=LS_W, input_weights=LS_SW, models=js), open(os.path.join(out_dir, 'lemon-score.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(out_dir, 'lemon-score.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh); w.writerow(['family_id', 'model', 'lemon_score', 'coverage', 'missing', 'reliability_safety', 'cost_to_own', 'youtube', 'holds_value',
                                        'complaint_score', 'serious_pct', 'recalls_vs_median', 'failure_cost_est', 'nhtsa_stars', 'fuel_usd_mo', 'repair_est_usd', 'insurance_est_usd_mo', 'youtube_vs_median', 'value_vs_type'])
        w.writerows(rows)

# ---------- /lemon-score/: how it works (sources, weights, what's an estimate) ----------
def _ls_method():
    nm = len(LS_M); full = sum(1 for m in LS_M.values() if m.get('s') and not m['partial']); part = sum(1 for m in LS_M.values() if m.get('s') and m['partial'])
    yfull = sum(1 for d in LS_Y.values() for m in d.values() if m.get('s')); nsafe = sum(len(v) for v in _LS_SAFE.values())
    cards = ''.join(f'<div><b>{LS_W[p]}</b><h3>{LS_NAME[p]}</h3><p>{t}</p></div>' for p, t in (
        ('rel', 'Owner complaints per car sold, how serious they are, recalls, what the common failures cost, NHTSA crash tests.'),
        ('cost', 'Fuel (EPA), everyday repair prices and insurance, per month.'),
        ('yt', 'How owners and reviewers talk about it on YouTube.'),
        ('val', 'How much value it loses per year at the same miles.')))
    rows = [('Reliability &amp; safety', 'Complaint Score', '18', 'NHTSA owner complaints in the first 3 years per car sold, vs the average car of the same years (100). <a href="/method/">How it works</a>', ''),
            ('', 'Serious complaints', '4', 'Share of those complaints that report a crash, fire, injury or tow (NHTSA)', ''),
            ('', 'Recalls', '5', 'NHTSA recall campaigns per model year vs the median car of the same year; do-not-drive and park-outside recalls count 3 times', ''),
            ('', 'Cost of common failures', '3', 'The failures owners name most, priced with our repair estimates', 'EST'),
            ('', 'Crash tests', '10', f'NHTSA 5-Star overall rating, model years 2011 and newer ({nsafe:,} model years matched)', ''),
            ('Cost to own', 'Fuel', '12', 'EPA yearly fuel cost (fueleconomy.gov), per month', ''),
            ('', 'Repair prices', '10', 'Average of 10 everyday repairs (brakes, alternator, starter, water pump, struts and more) at $140 an hour', 'EST'),
            ('', 'Insurance', '3', 'NAIC state averages for a 30-39 driver with a clean record, by car type (sports cars cost more), per month', 'EST'),
            ('What YouTube thinks', 'Owner score', '20', 'How positively owners and reviewers talk about each model year on YouTube, vs other cars of the same years and type', ''),
            ('Holds its value', 'Value loss per year', '15', 'Our AI price estimates by mileage: what one more year of age takes off at the same miles, vs the same type of car', 'EST')]
    tbl = ('<table class="ls-mt"><thead><tr><th>Part</th><th>Input</th><th>Points</th><th>Source</th></tr></thead><tbody>'
           + ''.join(f'<tr><td>{a}</td><td>{b}{_LS_EST if e else ""}</td><td class="num">{w}</td><td>{s}</td></tr>' for a, b, w, s, e in rows) + '</tbody></table>')
    q = '&#39;'
    body = ('<div class="pg">' + phero('Lemon Score', 'One score for the whole car.', 'Reliability, cost to own, what owners say and resale value, out of 100.')
            + f'{LS_CSS}<article class="study ls-meth"><div class="hw ls-hw">{cards}</div>'
            '<p>Each input is scored 0 to 100 against other cars (100 = the best of them), and the Lemon Score is the weighted average. <b>About 50 is the middle car</b>; most cars land between 35 and 65, and 63 or more puts a car in the top tenth.</p>'
            f'<p>Reliability and crash tests are compared with every car. Fuel, repairs, insurance, YouTube and value are compared with the same type of car (car, SUV, truck, minivan), so a truck isn{q}t marked down for being a truck.</p>'
            f'<details class="yd" open><summary>Every input and its source</summary>{tbl}</details>'
            f'<details class="yd"><summary>What{q}s an estimate</summary><p>Numbers tagged {_LS_EST} are our estimates, not measurements: repair prices are AI-written labor hours and parts prices checked against owner repair bills; '
            'prices by mileage are AI estimates, not listings or an appraisal; insurance is the official NAIC state average adjusted for age and car type, not a quote. Together they are 31 of the 100 points.</p></details>'
            f'<details class="yd"><summary>Which cars get a score</summary><p>A car needs at least 3 of the 4 parts. With one missing, the others count for more and the score says &ldquo;Partial&rdquo; and what is missing. '
            f'The same goes for a car with no Complaint Score (for example the F-150: Ford reports F-150 and Super Duty sales as one number). Today <b>{full}</b> models have a full score, <b>{part}</b> a partial one and '
            f'<b>{nm - full - part}</b> none. {yfull:,} model years have their own score; a model year uses its model{q}s value part, since one set of prices can{q}t show how one year depreciates. Value is scored from model years 2011 on: older cars{q} estimated prices barely move, so their model years get no value part.</p></details>'
            f'<details class="yd"><summary>What it leaves out</summary><p>Looks, comfort and how it drives: they matter, but they{q}re taste, not data. Brand-new model years get a partial score until their complaints are in (3 years). Rankings and best-of lists only rank cars with all 4 parts.</p></details>'
            '<details class="yd"><summary>The Complaint Score</summary><p>The number this site started with is now called the Complaint Score: owner complaints per car sold against the average car (100 = average, lower is better). '
            'It is the biggest single input of the Lemon Score, and it still picks the years to avoid and the years to buy (those are about problems). <a href="/method/">How the Complaint Score works</a></p></details>'
            '<p><a class="btn" href="/">Look up your car</a></p></article></div>')
    page('/lemon-score/', 'Lemon Score: How We Score Every Car Out of 100 | Lemon Index',
         'The Lemon Score rates every car 0-100 from owner complaints, recalls, NHTSA crash tests, fuel and repair costs, YouTube owner reviews and resale value.', body)
LS_URLS = ['/lemon-score/']

# ---------- 11-26 v2: rankings by the Lemon Score (higher = better) ----------
# Ranked lists use FULL scores only (all 4 parts); partial scores are listed apart, unranked, so a car missing a part (often an old car with no
# resale part) can't top a list. Years to avoid / years to buy stay on the Complaint Score: they're about problems.
def ls_full(fid): d = LS_M.get(fid) or {}; return d.get('s') if d.get('s') and not d['partial'] else None
def ls_ranked(cars):
    """cars (CARS dicts) -> (ranked best first by full Lemon Score, partial-score cars by score, unscored)"""
    r = sorted([c for c in cars if ls_full(c['id'])], key=lambda c: (-ls_full(c['id']), c.get('li') or 999))
    p = sorted([c for c in cars if LS(c['id']) and not ls_full(c['id'])], key=lambda c: -LS(c['id']))
    return r, p, [c for c in cars if not LS(c['id'])]
def ls_brands(min_models=2):
    """[(brand, sales-weighted Lemon Score of its fully scored models, n models)] best first"""
    by = defaultdict(list)
    for c in CARS:
        s = ls_full(c['id'])
        if s and c.get('sold'): by[c['brand']].append((s, c['sold']))
    out = [(b, round(sum(s * n for s, n in v) / sum(n for _, n in v)), len(v)) for b, v in by.items() if len(v) >= min_models]
    return sorted(out, key=lambda x: -x[1])

def LS_RANKINGS():
    R, P, _ = ls_ranked(CARS)
    row = lambda c, s: {'href': car_href(c['id']) or '/rankings/', 'ph': aph(c['id']), 'title': E(c['name']) + ('*' if c.get('est') else ''),
                        'sub': f'{E(c["segName"])} · {ls_band(s)[1]}', 'score': f'{s}', 'cls': ls_band(s)[0]}
    rk = [row(c, ls_full(c['id'])) for c in R]
    pr = [dict(row(c, LS(c['id'])), sub=f'{E(c["segName"])} · partial: {E((LS_M[c["id"]]["miss"] or [""])[0])}') for c in P]
    b0 = R[0]; ph0 = aph(b0['id']); BR = ls_brands()
    brows = [{'href': f'/brands/{b.lower().replace(" ", "-")}/', 'ph': None, 'title': E(b), 'sub': f'{n} models scored', 'score': f'{s}', 'cls': ls_band(s)[0]} for b, s, n in BR]
    page('/rankings/', 'Every Car Ranked by the Lemon Score, Best to Worst | The Lemon Index',
         f'Every car model ranked best to worst by the Lemon Score: reliability and safety, cost to own, what YouTube owners say and resale value, out of 100. {len(R)} models; higher is better.',
         '<div class="pg v5 rk5p">' + V5_HERO('', 'Every car, best to worst.', f'Ranked by the Lemon Score: reliability and safety, cost to own, YouTube owners and resale, out of 100. '
                                             f'Higher is better; 50 is the middle car. The <b>{E(b0["name"])}</b> ranks first of {len(R)} models.',
                                             extra=(f'<div class="v5-im">{pimg(ph0, b0["name"]).replace(" loading=" + chr(34) + "lazy" + chr(34), "")}</div>' if ph0 else ''))
         + '<section class="cp5-sec"><h2>Top 20, best buys first.</h2>' + V5_RANK(rk[:20]) + '</section>'
         + '<div class="cpl v5-pl">'
         + V5_BOX('chart', f'Show #21–{len(rk)}', V5_RANK(rk[20:], 21), 'more')
         + (V5_BOX('warning', f'Partial scores ({len(pr)}, not ranked)', '<p class="yc-cap">These cars are missing one of the 4 parts (most are older cars whose resale we don&#39;t score), so they aren&#39;t ranked with the rest.</p>'
                   + V5_RANK(pr), 'partial') if pr else '')
         + V5_BOX('tag', 'Every brand, best to worst', V5_RANK(brows) + '<p class="note">Each brand = its fully scored models, weighted by how many were sold. Brands with 2 or more scored models.</p>', 'brands')
         + V5_GO('warning', 'The worst model years', '/rankings/worst-years/')
         + V5_BOX('info', 'How the score works', '<p class="yc-cap">The Lemon Score rates each car out of 100: reliability and safety (40%), cost to own (25%), what YouTube owners and reviewers say (20%) and how well it holds its value (15%). '
                  '<b>Higher is better; 50 is the middle car.</b> Reliability counts owner complaints per car sold (the Complaint Score), how serious they are, recalls and NHTSA crash tests.</p>'
                  '<p class="yc-cap">* Tesla doesn&#39;t publish U.S. sales by model, so its numbers use published estimates. <a href="/lemon-score/">How the Lemon Score works</a> · <a href="/data/">All free data</a></p>')
         + '</div>' + pcredit(who(*[r['ph'] for r in rk[:20] if r['ph']]))
         + share_line("Every car ranked by the Lemon Score, best to worst. Free:") + '</div>',
         ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Every car ranked by the Lemon Score", "url": BASE + '/rankings/'}])
LS_RANKINGS()
_ls_method()
