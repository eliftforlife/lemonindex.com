# 11-20 (QA, Elijah: "some bike pages list duplicate recalls and junk entries; a Yamaha Road Star Warrior recall shows on the Yamaha V Star
# page"). Run by vehicles_pages.py with exec() right after MO / MB load, before any page reads a recall list. Every bike's list is cleaned once:
#   1. one row per NHTSA campaign number;
#   2. a recall that names its models ("... is recalling certain 2007 Road Star Warrior motorcycles") stays only on the pages for those models:
#      when the named text matches another same-brand bike's page and not this one (or its parent family / own bikes), it moves to that page;
#   3. rows with no readable defect text are dropped; two campaigns with the same defect sentence (a re-recall) become one row naming both.
# The sentence shown (MR_SENT) drops the "X is recalling certain ... motorcycles" opener, fixes ALL-CAPS text and never ends on a cut word.
import re as _mre
_MR_PREFIX_SPLIT = _mre.compile(r'\s*(?:/|,|\(|\)|&|\bor\b|\band\b)\s*', _mre.I)
_MR_STOP = {'AND', 'THE', 'WITH', 'SERIES', 'MODELS', 'MODEL', 'BOXERROADSTERS'}
# a family that the complaint file groups more widely than its name: these bikes are not that family, so a recall naming them is not its recall
MR_NOT_IN_FAMILY = {'Yamaha V Star': {'yamaha-road-star'}}
# names a recall uses for a bike that its page name doesn't say: the 2006-2017 Street Bob was a Dyna (FXDB); NHTSA's 18V076000 spells V-Rod's VRSC as VSRC
MR_ALIAS = {'harley-davidson-street-bob': ['DYNA', 'FXDB'], 'harley-davidson-v-rod': ['VSRC', 'VRSC']}
def _mr_toks(t): return _mre.findall(r'[A-Z0-9]+', (t or '').upper())
def _mr_keys(name, brand):
    """Model keys from a page name: 'Kawasaki Ninja 300/400/650' -> NINJA300, NINJA400, NINJA650 (letters only, no spaces or dashes)."""
    nm = name
    for b in (brand, brand.split(' ')[0]):
        if nm.upper().startswith(b.upper() + ' '): nm = nm[len(b) + 1:]; break
    keys, pre = [], ''
    for part in _MR_PREFIX_SPLIT.split(nm):
        k = ''.join(_mr_toks(part))
        if not k: continue
        if k.isdigit() and pre: k = pre + k          # '400' after 'Ninja 300' -> NINJA400
        else: pre = _mre.match(r'[A-Z]*', k).group(0) or pre
        if len(k) >= 3 and k not in _MR_STOP and not k.isdigit(): keys.append(k)
        t_ = _mr_toks(part)
        if len(t_) > 1 and _mre.fullmatch('[A-Z]+[0-9]+[A-Z]*', t_[-1]): keys.append(t_[-1])   # 'YZF-R1' is also typed 'R1'
    return keys
def _mr_hit(toks, keys, series=False):
    """True when a key starts at a word boundary of the named text (so 'ROADSTAR' is in 'ROAD STAR WARRIOR' but 'VSTAR' is not).
    series=True also counts a named series that the key belongs to: 'R 1200 (GS, R, RT)' or 'R 1200 series' names the R1200R."""
    j = ''.join(toks); starts, p = [], 0
    for t in toks: starts.append(p); p += len(t)
    if any(j.startswith(k, s) for k in keys for s in starts): return True
    if series:
        ends = set(starts[1:]) | {len(j)}
        for a in starts:
            for b in ends:
                run = j[a:b]
                if b > a and len(run) >= 4 and _mre.search('[0-9]', run) and _mre.match('[A-Z]', run) and any(k.startswith(run) for k in keys): return True
    return False
_MR_NAMED = _mre.compile(r'\b(motorcycles?|scooters?|trikes?|vehicles)\b', _mre.I)
def _mr_named(r):
    """The model text a recall names: its first sentence that says 'motorcycles', up to the last 'motorcycles' in it ('' when none does).
    Only the first two sentences: later ones describe the defect ('loose bolts' is not the Yamaha Bolt)."""
    s = _mre.sub(r'\s+', ' ', r.get('summary') or '')[:900]
    for head in _mre.split(r'(?<=\.)\s+', s)[:2]:
        ms = list(_MR_NAMED.finditer(head))   # up to the last 'motorcycles' (a list can name several groups)
        if ms: return _mr_toks(head[:ms[-1].start()])
    return []
def _mr_years(r):
    if r.get('years'): return set(int(y) for y in r['years'])
    return {int(r['y'])} if r.get('y') else set()
def mr_clean():
    pages = []   # (record, slug, brand, own keys, related keys, years)
    fam_children = {}
    for b in MB:
        if b.get('status') == 'split' and b.get('inside'): fam_children.setdefault(b['inside'], []).append(b)
    byname = {m['name']: m for m in MO}
    for m in MO:
        br = m['brand'].split(' ')[0]; slug = slugify(m['name'])
        excl = MR_NOT_IN_FAMILY.get(m['name'], set())
        kids = [b for b in fam_children.get(m['name'], []) if b['slug'] not in excl]
        bad = set()
        for b in fam_children.get(m['name'], []):
            if b['slug'] in excl: bad |= set(_mr_keys(b['name'], b['brand'])) | {''.join(_mr_toks(n)) for n in b.get('names', [])}
        own = _mr_keys(m['name'], m['brand']) + [k for k in (''.join(_mr_toks(n)) for n in m.get('names', [])) if len(k) >= 3 and k not in bad]
        rel = [k for b in kids for k in _mr_keys(b['name'], b['brand']) + [''.join(_mr_toks(n)) for n in b.get('names', [])] if len(k) >= 3]
        pages.append(dict(rec=m, slug=slug, br=br, own=own, rel=rel, ys=set(range(m['years'][0], m['years'][1] + 1)) if m.get('years') else set()))
    for b in MB:
        br = b['brand'].split(' ')[0]; par = byname.get(b.get('inside') or '')
        rel = []
        if par and b['slug'] not in MR_NOT_IN_FAMILY.get(par['name'], set()):
            rel = _mr_keys(par['name'], par['brand']) + [k for k in (''.join(_mr_toks(n)) for n in par.get('names', [])) if len(k) >= 3]
        own = _mr_keys(b['name'], b['brand']) + [k for k in (''.join(_mr_toks(n)) for n in b.get('names', [])) if len(k) >= 3] + MR_ALIAS.get(b['slug'], [])
        ys = set(int(y) for y in (b.get('by_year') or {})) or (set(range(int(b['y0']), int(b['y1']) + 1)) if b.get('y0') else set())
        pages.append(dict(rec=b, slug=b['slug'], br=br, own=own, rel=rel, ys=ys))
    moved, dropped = [], 0
    adds = {}
    for p in pages:
        keep, seen = [], set()
        for r in p['rec'].get('recalls') or []:
            if not r.get('id') or r['id'] in seen: continue   # 1. one row per campaign
            seen.add(r['id'])
            toks = _mr_named(r)
            if toks and not _mr_hit(toks, p['own'] + p['rel'], series=True):
                tg = [q for q in pages if q is not p and q['br'] == p['br'] and _mr_hit(toks, _mr_keys(q['rec']['name'], q['rec'].get('brand') or q['br']))]
                if tg:   # 2. it names another bike, not this one
                    for q in tg: adds.setdefault(id(q), (q, []))[1].append(r)
                    moved.append((p['slug'], r['id'], [q['slug'] for q in tg])); continue
            keep.append(r)
        p['rec']['recalls'] = keep
    for q, rs in adds.values():
        have = {r['id'] for r in q['rec']['recalls']}
        for r in rs:
            if r['id'] not in have: q['rec']['recalls'].append(dict(r)); have.add(r['id'])
        q['rec']['recalls'].sort(key=lambda r: _mr_date(r.get('date')), reverse=True)
    for p in pages:   # 3. readable rows only; the same defect sentence twice = one row naming both campaigns
        out, bytxt = [], {}
        for r in p['rec']['recalls']:
            t = MR_SENT(r)
            if not t: dropped += 1; continue
            k = _mre.sub(r'\W', '', t.lower())
            if k in bytxt: bytxt[k].setdefault('also', []).append(r['id']); continue
            r = dict(r); r['plain_s'] = t; bytxt[k] = r; out.append(r)
        p['rec']['recalls'] = out
    return moved, dropped
def _mr_date(d):
    d = d or ''
    if _mre.match(r'\d{2}/\d{2}/\d{4}$', d): return d[6:] + d[3:5] + d[:2]
    return _mre.sub(r'\D', '', d)[:8]
_MR_ABBR = r'(?<!\baux)(?<!\bapprox)(?<!\bNo)(?<!\bno)(?<!\bCo)(?<!\bInc)(?<!\bCorp)(?<!\bU\.S)(?<!\bvs)(?<!\betc)(?<!\bSt)(?<!\be\.g)(?<!\bi\.e)(?<!\bLtd)(?<!\bLLC)'
_MR_SPLIT = _mre.compile(_MR_ABBR + r'\.\s+(?=[A-Z(])')
_MR_ENDS = '.!?)"\'”'
def _mr_case(t):
    """ALL-CAPS NHTSA text -> normal sentence case (keeps ABS, ECU, VIN ... in caps)."""
    if sum(ch.isupper() for ch in t) <= .6 * max(1, sum(ch.isalpha() for ch in t)): return t
    t = _mre.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), t.lower())
    for w in ('ABS', 'ECU', 'ECM', 'NHTSA', 'FMVSS', 'LED', 'VIN', 'TPMS', 'CVO', 'USA'): t = _mre.sub(rf'\b{w.lower()}\b', w, t)
    return t
def MR_SENT(r):
    """One plain sentence for a recall row: the defect, not the 'X is recalling ...' opener ('' when there is nothing readable)."""
    raw = _mre.sub(r'\s+', ' ', r.get('summary') or '').strip()
    if len(_mre.findall(r'[A-Za-z]{3,}', raw)) < 4: return ''
    s = _mr_case(raw)
    if len(raw) >= 295 and s[-1:] not in _MR_ENDS: s = s.rsplit(' ', 1)[0].rstrip(',;:(') + '…'   # cut mid-word when stored: mark the cut
    sents = [x.strip() for x in _MR_SPLIT.split(s) if x.strip()]
    pick = ''
    for i, x in enumerate(sents):
        if _mre.search(r'\brecalling\b', x, _mre.I) and i + 1 < len(sents): continue   # the opener: who is recalling which models
        x = _mre.sub(r'^(?:on|in) (?:certain|some|the affected)\b[^,]{0,120}?\b(?:motorcycles?|scooters?|vehicles|models?)\s*,\s*', '', x, flags=_mre.I)
        if len(x) >= 25: pick = x; break
    if not pick:
        c = _mr_case(_mre.sub(r'\s+', ' ', r.get('consequence') or '').strip())
        pick = (_MR_SPLIT.split(c)[0].strip() if c else '') or (sents[0] if sents else '')
    if not pick or len(pick) < 20: return ''
    pick = pick[0].upper() + pick[1:]
    if len(pick) > 220: pick = pick[:220].rsplit(' ', 1)[0].rstrip(',;:(') + '…'
    elif pick[-1] not in _MR_ENDS and not pick.endswith('…'): pick += '.'
    return pick
MR_MOVED, MR_DROPPED = mr_clean()
print(f'moto recalls: {len(MR_MOVED)} moved to the bike they name, {MR_DROPPED} unreadable rows dropped', MR_MOVED[:12])
