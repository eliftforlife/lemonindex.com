# Car symptoms (11-14, Lemon growth project 2C-1): which symptoms owners describe in their NHTSA complaints, and on which models and
# model years. Scans the complaint text once (~20 min on 14 cores) and caches counts to data/symptoms.json; build.py only reads that JSON.
#   py -X utf8 symptoms.py
# Patterns live in symptom_defs.py. Only counts are kept (never complaint text, names, VINs or places), so nothing personal reaches the site.
# Per symptom: complaints that match, by model and model year (with that model year's total complaints in our data, for the share),
# the NHTSA component areas they were filed under, crash/fire/tow flags, median odometer, the trouble codes they name, which other
# symptoms the same complaints describe, and the repair bills owners named (data/repair_costs.json, matched by complaint number).
import collections, importlib.util, json, os, re, sqlite3, statistics, sys, time
from multiprocessing import Pool
sys.stdout.reconfigure(encoding='utf-8')
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
HERE = os.path.dirname(os.path.abspath(__file__))
_sp = importlib.util.spec_from_file_location('symptom_defs', os.path.join(HERE, 'symptom_defs.py')); SD = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(SD)
CODE = re.compile(r'\b([PBCU][0-3][0-9A-F]{3})\b')
NOT_CODES = {'C1500', 'C2500', 'C3500', 'B1500', 'B2000', 'B2200', 'B2300', 'B2500', 'B2600', 'B3000', 'B3500', 'B150E', 'B250E', 'B350E'}   # truck names (engine_codes.py)

def work(chunk):
    out = []
    for o, d in chunk:
        s = SD.match(d)
        if s: out.append((o, tuple(s), tuple(sorted(set(CODE.findall(d.upper())) - NOT_CODES))))
    return out

def L(p): return json.load(open(os.path.join(HERE, p), encoding='utf-8')) if os.path.exists(os.path.join(HERE, p)) else None

if __name__ == '__main__':
    t0 = time.time()
    YR = (L('data/years.json') or []) + (L('data/years_new.json') or []) + (L('data/years_tesla.json') or [])
    NAME = {f['id']: f['name'] for f in YR}
    key = {}   # (NHTSA make, model, year) -> our model id, same mapping as engine_codes.py / data_gap.py, plus the newer model files
    for p in ('data/extras_local.json', 'data/extras_local_new.json', 'data/extras_local_low.json', 'data/extras_local_tesla.json'):
        for fid, ys in (L(p) or {}).items():
            if fid not in NAME: continue
            for y, x in ys.items():
                for mk, md, n in (x.get('names') or []):
                    if n >= 2: key.setdefault((mk, md, int(y)), fid)
    COST = {}   # complaint number -> (usd, area, fid, year)
    for fid, v in (L('data/repair_costs.json') or {}).items():
        for y, a, usd, odi in v.get('c', []): COST[str(odi)] = (usd, a, fid, y)
    c = sqlite3.connect(DB, check_same_thread=False)   # the pool reads the generator from its own thread
    # pass A: the text, once per complaint
    seen = set(); R = {}; N_ALL = 0

    def chunks():
        global N_ALL
        buf = []
        for o, d in c.execute('select odino, descr from rows'):
            if not o or o == '0' or o in seen or not d: continue
            seen.add(o); buf.append((o, d))
            if len(buf) >= 2500: yield buf; buf = []
        if buf: yield buf
    with Pool(14) as pool:
        for i, res in enumerate(pool.imap_unordered(work, chunks(), chunksize=1)):
            for o, s, cd in res: R[o] = (s, cd)
            if i % 100 == 0: print(f'  {i * 2500:,} complaints, {len(R):,} with a symptom, {time.time() - t0:.0f}s', flush=True)
    N_ALL = len(seen); seen = None
    print('pass A done', N_ALL, len(R), round(time.time() - t0))
    # pass B: vehicles, components and flags per complaint
    S = {k: dict(n=0, years=collections.Counter(), models=collections.Counter(), makes=collections.Counter(), comps=collections.Counter(),
                 crash=0, fire=0, towed=0, injured=0, miles=[], codes=collections.Counter(), rel=collections.Counter(), costs=[]) for k in SD.P}
    for o, (s, cd) in R.items():
        for k in s:
            x = S[k]; x['n'] += 1; x['codes'].update(cd); x['rel'].update(j for j in s if j != k)
            if o in COST: x['costs'].append(list(COST[o]))
    den = collections.Counter(); seenK = set(); seenO = set(); seenC = set()
    def top(comp): return (comp or '').split(':')[0].strip().title()
    for o, mk, md, yr, comp, crash, fire, towed, inj, miles in c.execute('select odino, make, model, year, comp, crash, fire, towed, injured, miles from rows'):
        if not o or o == '0': continue
        try: y = int(yr)
        except (TypeError, ValueError): y = None
        fid = key.get((mk, md, y)) if y else None
        if fid and (o, fid, y) not in seenK:
            seenK.add((o, fid, y)); den[(fid, y)] += 1; new_k = True
        else: new_k = False
        r = R.get(o)
        if not r: continue
        s = r[0]
        if new_k:
            for k in s:
                S[k]['years'][(fid, y)] += 1
                if (o, fid) not in seenO: S[k]['models'][fid] += 1
            seenO.add((o, fid))
        cp = top(comp)
        if cp and (o, cp) not in seenC:
            seenC.add((o, cp))
            for k in s: S[k]['comps'][cp] += 1
        if (o, '') not in seenC:   # once per complaint
            seenC.add((o, ''))
            for k in s:
                x = S[k]; x['makes'][(mk or '').title()] += 1
                x['crash'] += crash == 'Y'; x['fire'] += fire == 'Y'; x['towed'] += towed == 'Y'; x['injured'] += (inj or 0) > 0
                try:
                    m = int(miles or 0)
                    if 0 < m < 400000: x['miles'].append(m)
                except (TypeError, ValueError): pass
    out = {}
    for k, x in S.items():
        yrs = [[fid, NAME[fid], y, n, den[(fid, y)]] for (fid, y), n in x['years'].most_common() if n >= 3][:400]
        out[k] = dict(n=x['n'], mapped=sum(x['models'].values()), models=[[i, NAME[i], n] for i, n in x['models'].most_common(40)], years=yrs,
                      makes=x['makes'].most_common(8), comps=x['comps'].most_common(6), crash=x['crash'], fire=x['fire'], towed=x['towed'], injured=x['injured'],
                      miles=int(statistics.median(x['miles'])) if len(x['miles']) >= 20 else None, codes=x['codes'].most_common(25),
                      rel=x['rel'].most_common(12), costs=sorted(x['costs']))
    allc = collections.Counter()   # how often each code appears in any complaint with a symptom, for "more common with this symptom than usual"
    for s, cd in R.values(): allc.update(cd)
    json.dump(dict(total=N_ALL, with_symptom=len(R), den_note='complaints per model year mapped to our models', codes_all=dict(allc.most_common(400)), symptoms=out),
              open(os.path.join(HERE, 'data', 'symptoms.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('done', round(time.time() - t0), 's |', ' '.join(f'{k}={v["n"]}' for k, v in sorted(out.items(), key=lambda kv: -kv[1]['n'])))
