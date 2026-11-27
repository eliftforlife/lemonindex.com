# 11-26 Lemon Score (Elijah approved the design 11-26): NHTSA 5-Star crash-test ratings for every car model year the site covers
# -> data/safety_ratings.json, the safety input of the Lemon Score (lemon_score.py).
#   usage: py -X utf8 data_safety.py            (re-run any time; every API answer is cached under data/cache/, so a rerun only asks for what's new)
#          py -X utf8 data_safety.py --offline  (cache only, no network: what's already been fetched)
# Source: NHTSA's free public API, https://api.nhtsa.gov/SafetyRatings/ ...
#   /modelyear/<y>/make/<make>               -> the rated model names for that make and year
#   /modelyear/<y>/make/<make>/model/<model> -> its rated versions (VehicleId per body style / drive)
#   /VehicleId/<id>                          -> OverallRating, OverallFrontCrashRating, OverallSideCrashRating, RolloverRating
# Polite: one request at a time, a short pause between network requests, a plain client name, no proxies. A refused or blocked request
# (403 / 429) is dropped and logged, never retried another way.
# Model years 2011+ only: NHTSA's current 5-star program (with an overall rating) started with the 2011 model year.
# Matching (logged in the file's "log" block): our model's NHTSA names come from its own complaints (data/extras_local*.json `names`, each name
# with 10%+ of that year's complaints, F-150: data/f150_split.json), plus the model's own name. A rated model counts when its name, without
# spaces and dashes, equals one of those names, or is one of them plus only body / drive / cab words (CAMRY HYBRID, F-150 SUPERCREW,
# SILVERADO 1500 CREW CAB). Anything else is not counted, and the year is listed under "unmatched" with the make's rated names.
import hashlib, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'data', 'cache')
OFFLINE = '--offline' in sys.argv
PAUSE = 0.35
FIRST = 2011
STATS = {'net': 0, 'cache': 0, 'refused': 0, 'failed': 0}
REFUSED = []


def get(url):
    """GET JSON through the same disk cache as data_fetch_api.py (sha1 of the URL). None = nothing there, refused, or offline."""
    path = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:20] + '.json')
    if os.path.exists(path):
        STATS['cache'] += 1
        return json.load(open(path, encoding='utf-8'))
    if OFFLINE: return None
    for attempt in range(2):
        time.sleep(PAUSE)
        STATS['net'] += 1
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'lemonindex.com data build'})
            with urllib.request.urlopen(req, timeout=40) as r:
                body = r.read().decode('utf-8', 'replace')
            data = json.loads(body) if body.strip() else None
            break
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):   # refused or rate-limited: drop it, never work around it
                STATS['refused'] += 1; REFUSED.append(url); return None
            if e.code in (400, 404):
                data = None; break
            time.sleep(3)
        except Exception:
            time.sleep(3)
    else:
        STATS['failed'] += 1
        return None   # network trouble: not cached, so a rerun tries again
    os.makedirs(CACHE, exist_ok=True)
    json.dump(data, open(path, 'w', encoding='utf-8'))
    return data


norm = lambda s: re.sub(r'[^A-Z0-9]', '', str(s).upper())
# words NHTSA adds to a model name for the body, drive or cab; the rest of the name must be one of our names
SUFFIX = re.compile(r'^(?:HYBRID|PLUGINHYBRID|PLUGIN|PHEV|ENERGI|ECO|4DR|2DR|5DR|3DR|4WD|2WD|AWD|FWD|RWD|4X4|4X2|SEDAN|COUPE|HATCHBACK|HATCH|HB|WAGON|SPORTWAGON|'
                    r'CONVERTIBLE|CABRIOLET|CREWCAB|CREWMAX|DOUBLECAB|ACCESSCAB|KINGCAB|QUADCAB|MEGACAB|REGULARCAB|REGCAB|EXTENDEDCAB|EXTCAB|SUPERCREW|SUPERCAB|'
                    r'PICKUP|1500|LD|CLASSIC|LIMITED|NEW|SUV|LWB|SWB|SPORT|SPORTBACK|GT|XL|L|LONGBED|SHORTBED|UNLIMITED|JK|JL|4XE|HEV|BEV|EV|HV|GAS|DIESEL|HARDTOP|'
                    r'ALLVARIANTS|ALLVARIANTS\dSEAT|ALLVARIANTS\dPSGR|P?\d{2,3}D|\d{3}[HLIE]?|T\d|[XS]DRIVE\d*[A-Z]*|SAV|ALL4|B\d|2DOOR|4DOOR|WITHRECARO|WITHOUTRECARO|LT1|SS|ZL1)+$')


# the model's own NHTSA ratings names where neither its complaint names nor its name match (checked by hand against the ratings lists)
ALIAS = {'mercedes-benz-glk/glc': {'GLKCLASS', 'GLCCLASS'}, 'mercedes-benz-m/gle': {'MLCLASS', 'GLECLASS'}, 'mercedes-benz-cla': {'CLACLASS'},
         'mercedes-benz-gla': {'GLACLASS'}, 'subaru-crosstrek': {'XVCROSSTREK', 'CROSSTREK'}, 'mazda-mazda5': {'MAZDA5'}, 'mazda6': {'MAZDA6'},
         'mini-cooper': {'HARDTOP', 'COOPERHARDTOP', 'COOPERSHARDTOP'}}
MAKE_X = {'ram-pickup': [('RAM', '1500')]}   # 2011-2012 Ram pickups are filed as DODGE RAM 1500 but rated under RAM 1500


def name_ok(rated, ours, make=''):
    r0 = norm(rated); rs = [r0]
    if make and r0.startswith(norm(make)) and r0 != norm(make): rs.append(r0[len(norm(make)):])   # 2022+ lists can repeat the make ("AUDI A4"); MAZDA3 stays MAZDA3 too
    for r in rs:
        for o in ours:
            if not o: continue
            if r == o: return True
            if r.startswith(o) and SUFFIX.match(r[len(o):]): return True
    return False


def load(p):
    p = os.path.join(HERE, 'data', p)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def jobs():
    """[(fid, model name, year, [(MAKE, MODEL)])] for every car model year 2011+ the site has complaint names for"""
    names = {}
    for p in ('years.json', 'years_new.json', 'years_tesla.json'):
        for f in load(p) or []: names[f['id']] = f['name']
    loc = {}
    for p in ('extras_local.json', 'extras_local_new.json', 'extras_local_low.json', 'extras_local_tesla.json'):
        for fid, ys in load(p).items(): loc.setdefault(fid, {}).update(ys)
    fs = load('f150_split.json')
    if fs.get('extras'): loc['ford-f-series'] = fs['extras']   # the F-150 page counts F-150 names only (f150_split.py)
    out = []
    for fid in sorted(loc):
        if fid not in names: continue
        for y in sorted(loc[fid]):
            if int(y) < FIRST: continue
            nm = (loc[fid][y] or {}).get('names') or []
            tot = sum(n for _, _, n in nm) or 1
            pick = [(mk, md) for mk, md, n in nm if n / tot >= 0.10][:3] or [tuple(nm[0][:2])] if nm else []
            if pick: out.append((fid, names[fid], int(y), pick))
    return out


def rating(v):
    return int(v) if str(v).isdigit() else None


def main():
    todo = jobs()
    print(len(todo), 'model years to check (2011+)', flush=True)
    out, unmatched, t0 = {}, [], time.time()
    for i, (fid, fam, y, pick) in enumerate(todo, 1):
        pick = pick + [x for x in MAKE_X.get(fid, []) if x not in pick]
        makes = sorted({mk for mk, _ in pick})
        base = fam.split(' ', 1)[1] if ' ' in fam else fam
        found, seen_models = [], {}
        for mk in makes:
            lst = (get(f'https://api.nhtsa.gov/SafetyRatings/modelyear/{y}/make/{urllib.parse.quote(mk.lower())}') or {}).get('Results') or []
            rated = [m['Model'] for m in lst if m.get('Model')]
            seen_models[mk] = rated
            ours = {norm(md) for m2, md in pick if m2 == mk}
            hit = [m for m in rated if name_ok(m, ours, mk)]
            if not hit:   # 2nd try: the model's own name (NHTSA rates "C-CLASS" while owners file "C300"), then the hand-checked aliases
                hit = [m for m in rated if name_ok(m, {norm(base)} | ALIAS.get(fid, set()), mk)]
            hits = seen_models.setdefault('_hit', []); hits += hit
            for model in hit[:4]:
                vs = (get(f'https://api.nhtsa.gov/SafetyRatings/modelyear/{y}/make/{urllib.parse.quote(mk.lower())}/model/{urllib.parse.quote(model.lower())}') or {}).get('Results') or []
                for v in vs[:8]:
                    r = ((get(f'https://api.nhtsa.gov/SafetyRatings/VehicleId/{v["VehicleId"]}') or {}).get('Results') or [{}])[0]
                    if not r: continue
                    found.append({'model': model, 'desc': v.get('VehicleDescription', ''), 'id': v['VehicleId'], 'overall': rating(r.get('OverallRating')),
                                  'front': rating(r.get('OverallFrontCrashRating')), 'side': rating(r.get('OverallSideCrashRating')), 'rollover': rating(r.get('RolloverRating'))})
        rated = [x['overall'] for x in found if x['overall']]
        if rated:
            out.setdefault(fid, {})[str(y)] = {'overall': round(sum(rated) / len(rated), 2), 'best': max(rated), 'worst': min(rated), 'n': len(rated),
                                               'models': sorted({x['model'] for x in found}), 'variants': found}
        else:
            unmatched.append({'fid': fid, 'year': y, 'ours': [f'{mk} {md}' for mk, md in pick], 'matched': sorted({x['model'] for x in found}),
                              'why': 'rated model found, no overall rating' if found else 'name matched, no rated versions returned' if seen_models.get('_hit') else 'no rated model name matched',
                              'nhtsa_names': {mk: sorted(set(v))[:40] for mk, v in seen_models.items() if mk != '_hit'}})
        if i % 200 == 0: print(f'{i}/{len(todo)} in {time.time() - t0:.0f}s ({STATS["net"]} network, {STATS["cache"]} cached)', flush=True)
    res = {'source': 'NHTSA 5-Star Safety Ratings, api.nhtsa.gov/SafetyRatings (model years 2011+)', 'made': time.strftime('%Y-%m-%d'),
           'counts': {'checked': len(todo), 'rated': sum(len(v) for v in out.values()), 'models': len(out), 'unmatched': len(unmatched),
                      'refused': STATS['refused'], 'failed': STATS['failed']},
           'm': out, 'log': {'unmatched': unmatched, 'refused': REFUSED}}
    json.dump(res, open(os.path.join(HERE, 'data', 'safety_ratings.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(json.dumps(res['counts']), STATS, '-> data/safety_ratings.json')


if __name__ == '__main__':
    main()
