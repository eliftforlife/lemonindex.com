# 11-26 (Elijah: "a money evaluator on the site in the money section ... car year model and trim and condition ... title status clean or
# salvage and then it says price range of what it's worth, even it's just estimate"): data for /car-value/ (car_value_pages.py).
# Reads the checklist price run (3 Lemon Index/checklist/prices/<model>.json, the same AI estimates the year-page price box shows) and
# writes ONE compact file the page fetches: assets/carvalue.json. Only what the price math needs: each year's private-party range at
# typical miles, the miles, dealer and price-new caps, rounding, and (about 50 models) the trims sold each year with their multipliers.
# The math is prices_brackets.price_at() (base trim) and checklist_template.html price() (a trim picked); assets/carvalue.js repeats it
# and tools/check_car_value.py checks the two match. Re-run after the price files change:
#   py -X utf8 data_car_value.py && py -X utf8 tools/check_car_value.py
# Names come from the site's own model lists (family_rates.csv, cars_new.json, perf_cars.json, supercars.json). Redirect ids (f150,
# dodge-ram ...) have no name there and are left out. A model year with no year page links its model page instead (checked in docs/).
import csv, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CK = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\checklist'
sys.path.insert(0, CK); import prices_brackets as PB
OUT = os.path.join(HERE, 'assets', 'carvalue.json')

idf = lambda n: n.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('+', 'plus').replace('&', 'and')
slg = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower().replace("'", '')).strip('-')
jl = lambda p: json.load(open(os.path.join(HERE, p), encoding='utf-8')) if os.path.exists(os.path.join(HERE, p)) else []
BRAND = {'MINI': 'Mini'}


def names():
    """id -> (make, full name, kind 'c' car page / 's' supercar page)"""
    N = {}
    for r in csv.DictReader(open(os.path.join(HERE, 'data', 'family_rates.csv'), encoding='utf-8')): N[idf(r['family'])] = (r['brand'], r['family'], 'c')
    for c in jl('data/cars_new.json'): N.setdefault(c['id'], (c['brand'], c['name'], 'c'))
    for c in jl('data/perf_cars.json'): N.setdefault(c['slug'], (c['make'], c['name'], 'c'))
    for c in jl('data/supercars.json'): N.setdefault(slg(c['name']), (c['make'], c['name'], 's'))
    N.setdefault('bmw-m3', ('BMW', 'BMW M3', 'c'))   # perf page on its model page (build.py _m3twin), not in perf_cars.json
    N.setdefault('kia-k5', ('Kia', 'Kia K5', 'c'))   # k5_split.py
    return N


def by_year(v, y):
    """a number, or [[from_year, mult], ...] (checklist byYear / make_checklist eng_adj)"""
    if isinstance(v, (int, float)): return v
    m = 1.0
    for fy, k in v or []:
        if y >= fy: m = k
    return m


def trims(P, notes, y):
    """[[name, a, na]] for the trims sold in model year y; a = trim x its engine multiplier (checklist adj() with no drive picked),
    na = the price-new multiplier (new.trim_mult, else a). A trim with its own price table that year (trim_years) -> [name, -1, -1]."""
    tm = {k: v for k, v in (P.get('trims') or {}).items() if not k.startswith('note')}
    em = {k: v for k, v in (P.get('engines') or {}).items() if not k.startswith('note')}
    nt = {k: v for k, v in ((P.get('new') or {}).get('trim_mult') or {}).items() if k != 'note'}
    ty = {k: v for k, v in (P.get('trim_years') or {}).items() if k != 'note'}
    out, seen = [], set()
    for t in notes.get('trims') or []:
        if not (t['years'][0] <= y <= t['years'][1]) or t['t'] in seen: continue
        seen.add(t['t'])
        if t['t'] in ty and str(y) in ty[t['t']]['years']: out.append([t['t'], -1, -1]); continue
        es = list((t.get('eng') or {}).values())
        e = sum(by_year(em.get(n, 1.0), y) for n in es) / len(es) if es else 1.0   # engine differs by body (Civic sedan / hatch): the average
        a = round(by_year(tm.get(t['t'], 1.0), y) * e, 4)
        na = round(by_year(nt[t['t']], y), 4) if t['t'] in nt else a
        out.append([t['t'], a, na])
    return out


def runs(per_year):
    """{year: [[name, a, na]...]} -> [[name, y0, y1, a, na]...]: one entry per unbroken run of years with the same numbers"""
    out = []
    for y in sorted(per_year):
        for n, a, na in per_year[y]:
            last = next((r for r in reversed(out) if r[0] == n), None)
            if last and last[2] == y - 1 and last[3] == a and last[4] == na: last[2] = y
            else: out.append([n, y, y, a, na])
    return out


def main():
    N = names(); docs = os.path.join(HERE, 'docs')
    models = sorted({f[:-5] for f in os.listdir(os.path.join(CK, 'prices')) if f.endswith('.json')} |
                    {f[:-5] for f in os.listdir(os.path.join(CK, 'costs')) if f.endswith('.json')})
    M, skipped, nopage = {}, [], 0
    for mid in models:
        if mid not in N: skipped.append(mid); continue
        P = PB.load(mid)
        if not P or not P.get('years'): skipped.append(mid); continue
        mk, full, kind = N[mid]; mk = BRAND.get(mk, mk)
        short = full[len(mk) + 1:] if full.lower().startswith(mk.lower() + ' ') else full
        new = (P.get('new') or {}); nys = new.get('years') or {}
        o = {'n': short, 'b': mk, 'k': kind, 'r': P.get('round', 250),
             'mi': [P['miles']['per10k'], P['miles']['min'], P['miles']['max']], 'd': [P['dealer']['mult'], P['dealer']['add']],
             'cap': new.get('cap', .98), 'pc': (P.get('bands') or {}).get('private_cap') or 0,
             'y': {y: [v[0], v[1], v[2], nys.get(y) or 0] for y, v in sorted(P['years'].items())}}
        if kind == 'c' and os.path.isdir(docs):
            ys = [int(y) for y in o['y']]   # every year the page's Year list shows (first to last priced year), gaps included
            np_ = [y for y in range(min(ys), max(ys) + 1) if not os.path.exists(os.path.join(docs, 'cars', mid, str(y), 'index.html'))]
            if np_: o['np'] = np_; nopage += len(np_)
        np_path = os.path.join(CK, 'notes', mid + '.json')
        if os.path.exists(np_path) and any(not k.startswith('note') for k in (P.get('trims') or {})):
            notes = json.load(open(np_path, encoding='utf-8'))
            py = {int(y): trims(P, notes, int(y)) for y in o['y']}
            if any(py.values()):
                o['t'] = runs({y: v for y, v in py.items() if v})
                ty = {k: v for k, v in (P.get('trim_years') or {}).items() if k != 'note'}
                used = {r[0] for r in o['t'] if r[3] == -1}
                if used: o['ty'] = {k: {'y': ty[k]['years'], 'n': ty[k].get('new') or {}, 'pc': ty[k].get('private_cap') or 0, 'cap': ty[k].get('cap') or 0} for k in used}
        M[mid] = o
    out = {'date': 'November 2026', 'now': PB.YEAR_NOW, 'm': M}
    s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    open(OUT, 'w', encoding='utf-8').write(s)
    print(f'{len(M)} models ({sum(1 for o in M.values() if o["k"] == "s")} supercars, {sum(1 for o in M.values() if "t" in o)} with trims), '
          f'{sum(len(o["y"]) for o in M.values())} model-years, {nopage} without a year page -> assets/carvalue.json ({len(s) // 1024} KB)')
    print('left out (no site name: redirect ids):', skipped)


if __name__ == '__main__':
    main()
