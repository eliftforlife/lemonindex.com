# lemon-store content build (11-25). Reads the PRIVATE checklist folder and writes, OUTSIDE this public repo:
#   <out>/gens/<gen id>.json   one paid checklist per generation (the wizard's data: checks, how-to, money numbers, unknowns, recalls)
#   <out>/kv_bulk.json         the same, as `wrangler kv bulk put` input (keys "index" + "gen:<id>")
#   <out>/leak_strings.json    every paid sentence, for test_leak.mjs
# and, INSIDE the repo, only the public teaser: data/checklist_store.json (names, years, counts and check-area names: no steps, no money).
# It also copies the private answer engine (<src>/store/engine.js) next to the Worker as worker/store/engine.js (gitignored): the offer
# engine is paid, so it runs inside the Worker and is never in a site bundle or a tracked file.
#
#   py -X utf8 worker/store/build_content.py [--src <checklist folder>] [--out <private out folder>]
# Source: the v13 checklist pages (<short>[-gN]-preview.html carry their data as JSON), notes/<model>.json (generation years) and
# store/store_copy.json (the wizard's short questions for the shared checks, mockup-approved wording). Nothing is sent anywhere.
import argparse, glob, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
SRC0 = os.path.join(os.path.expanduser('~'), 'Desktop', 'Eliftforlife youtube', '3 Lemon Index', 'checklist')
CH = {'go': 1, 'walk': 2, 'tires': 3, 'hood': 4, 'start': 5, 'ac': 6, 'inside': 7, 'drive': 8, 'paper': 9}
SECS = {1: 90, 2: 40, 3: 40, 4: 40, 5: 40, 6: 60, 7: 40, 8: 90, 9: 40}   # seconds per check when the copy table has none
VER = 1


def load_page(p):
    t = open(p, encoding='utf-8').read()
    m = re.search(r'<script id="lck-data" type="application/json">(.*?)</script>', t, re.S)
    return json.loads(m.group(1).replace('<\\/', '</'))


def cap1(s): s = str(s or '').strip(); return s[:1].upper() + s[1:]


def q_from_fn(fn):
    """A car-specific check with no hand-written question: ask about the problem itself, answers No / Yes (they match the question)."""
    f = re.sub(r'^(a|an)\s+', '', str(fn or 'a problem').strip())
    return cap1(f).rstrip('.') + '?'


def subst(s, d, y):
    if not s: return s
    s = s.replace('{brand}', d.get('brand') or 'the maker')
    p = next((r.get('v') for r in (y.get('pushR') or []) if not r.get('fit')), None)
    ign = 'press START twice with no foot on the brake' if p is True else 'turn the key to ON' if p is False else 'key to ON, or START twice with no foot on the brake'
    st = next((r.get('v') for r in (y.get('steerR') or []) if not r.get('fit')), None)
    return s.replace('{ign}', ign).replace('{steer}', {'rack': 'steering rack', 'box': 'steering box'}.get(st, 'steering gear'))


def check_of(it, ch, d, y, copy, seller=None):
    fx = it.get('fx') or {}
    c = copy.get(it['id']) or {}
    x = {'ch': ch, 'q': c.get('q') or q_from_fn(it.get('fn')), 'a': c.get('a') or ['No', 'Yes'],
         'how': subst(c.get('how') or it.get('do'), d, y), 'ok': subst(it.get('good'), d, y), 'bad': subst(it.get('bad'), d, y),
         'prob': c.get('prob') or cap1(it.get('fn') or it.get('sl') or 'Problem'), 'k': fx.get('k') or 'mech', 't': c.get('t') or SECS[ch]}
    if c.get('qd'): x['qd'] = c['qd']
    if c.get('i'): x['i'] = c['i']
    if c.get('act'): x['act'] = c['act']
    if c.get('kind'): x['kind'] = c['kind']
    why = c.get('why') or it.get('why')
    if why: x['why'] = subst(why, d, y)
    if it.get('nums'): x['src'] = ' '.join(it['nums'])
    if isinstance(it.get('how'), dict) and it['how'].get('t'): x['how2'] = it['how']['t']
    if fx.get('v'): x['cost'] = fx['v']
    if fx.get('g'): x['g'] = fx['g']
    if fx.get('n'): x['note'] = fx['n']
    for k in ('r', 'ck', 'chk'):                              # the offer engine: wear, cosmetic, "a mechanic confirms it first"
        if fx.get(k): x[k] = fx[k]
    if fx.get('opts'): x['opts'] = [{'fit': o.get('fit'), 'v': o.get('v')} for o in fx['opts']]
    for k in ('need', 'fixv'):                                # the "what to say" words: "It needs four new tires"
        if c.get(k): x[k] = c[k]
    tag = ('s' if it.get('safe') else '') + ('k' if (it.get('hot') or it.get('yr')) else '')
    if tag: x['tag'] = tag
    for k in ('key', 'big', 'safe', 'fit', 'only', 'dup'):
        if it.get(k): x[k] = it[k]
    if it.get('dl'): x['dl'] = {k: subst(v, d, y) for k, v in it['dl'].items() if k in ('do', 'good', 'bad')}
    if seller: x['seller'] = seller
    if it.get('sys'): x['sys'] = it['sys']
    return x


def build(src, out, check_only=False):
    copy = json.load(open(os.path.join(src, 'store', 'store_copy.json'), encoding='utf-8'))
    U, INFO, QS = copy['u'], copy['info'], copy['questions']
    gens, teaser, strings = {}, {}, set()
    for p in sorted(glob.glob(os.path.join(src, '*-preview.html'))):
        d = load_page(p); model = d['id']
        notes = json.load(open(os.path.join(src, 'notes', model + '.json'), encoding='utf-8'))
        by_gen = {}
        for ys, y in d['years'].items():
            g = next((g for g, v in notes['gens'].items() if v['years'][0] <= int(ys) <= v['years'][1]), None)
            if g: by_gen.setdefault(g, {})[ys] = y
        for g, years in by_gen.items():
            gid = f'{model}-{g}'
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+){0,6}-g\d{1,2}', gid): sys.exit(f'bad generation id {gid}')
            checks, ys_out = {}, {}
            def put(cid, x):                                      # one copy per id; a year whose text differs gets its own key
                k = cid
                if k in checks and checks[k] != x:
                    k = f'{cid}@{len([1 for z in checks if z.split("@")[0] == cid])}'
                    for z, v in checks.items():
                        if z.split('@')[0] == cid and v == x: return z
                checks[k] = x; return k
            for ys, y in sorted(years.items()):
                ids = []
                for st in y['steps']:
                    ch = CH[st['id']]
                    for it in st['items']: ids.append(put(it['id'], check_of(it, ch, d, y, U)))
                for sel, key in (('p', 'private'), ('d', 'dealer')):
                    for it in sorted(d['who'].get(key) or [], key=lambda z: z.get('at', 0)): ids.append(put(it['id'], check_of(it, 9, d, y, U, sel)))
                unk = [{k: u.get(k) for k in ('id', 't', 'ask', 'why', 'q', 'note', 'checks', 'v', 'fit', 'records', 'mi_min', 'mech_only', 'proof', 'if_bad', 'plural', 'key') if u.get(k) not in (None, False, [])}
                       for u in (y.get('unk') or [])]
                ys_out[ys] = {'ids': ids, 'price': y.get('price'), 'unk': unk, 'li': y.get('li'), 'word': y.get('word'),
                              'trims': [{'t': t['t'], 'eng': t.get('eng') or {}, 'tr': t.get('tr', 'both'), 'sub': t.get('sub')} for t in y.get('trims') or []],
                              'eng2': [{'name': e['name'], 'adj': e.get('adj', 1), 'est': e.get('est')} for e in y.get('eng2') or []],
                              'driveR': y.get('driveR') or [], 'drives': y.get('drives') or [], 'cabs': y.get('cabs') or [], 'manual': bool(y.get('manual')),
                              'gear': [{'tr': x.get('tr'), 'name': x.get('name'), 'fit': x.get('fit')} for x in y.get('gear') or []],
                              'recalls': [[r['id'], r.get('t'), bool(r.get('danger'))] for r in y.get('recalls') or []],
                              'likely': [{'t': l['t'], 'v': l.get('v')} for l in y.get('likely') or []]}
                ys_out[ys]['quick'] = [c for c in ids if quick_check(c, checks[c], ys_out[ys])]
            M = d['money']
            doc = {'v': VER, 'id': gid, 'model': model, 'name': d['name'], 'short': d.get('short') or d['name'].split(' ', 1)[-1], 'brand': d.get('brand'),
                   'type': d.get('type'), 'gen': notes['gens'][g].get('label'), 'years': notes['gens'][g]['years'],
                   'money': {k: M.get(k) for k in ('dealer', 'miles', 'round', 'bands', 'cap', 'floor', 'trims', 'drive', 'cab', 'newTrims', 'records', 'fees', 'trimYears', 'today')},
                   'info': INFO, 'questions': QS, 'checks': checks, 'ys': ys_out}
            gens[gid] = doc
            # strings that only the paid checklist may show (leak test)
            for x in checks.values():
                for k in ('how', 'ok', 'bad', 'why', 'how2', 'note', 'src'):
                    v = x.get(k)
                    if isinstance(v, str) and len(v.strip()) >= 30: strings.add(v.strip())
                for v in (x.get('dl') or {}).values():
                    if len(v) >= 30: strings.add(v)
            for y in ys_out.values():
                for u in y['unk']:
                    for k in ('ask', 'why', 'q', 'note'):
                        if isinstance(u.get(k), str) and len(u[k]) >= 30: strings.add(u[k])
            # public teaser: no steps, no money
            first = sorted(ys_out)[len(ys_out) // 2]
            yq = ys_out[first]
            quick = list({c.split('@')[0]: c for c in yq['quick'] if checks[c].get('seller') != 'd'}.values())   # what a private-seller buyer sees, one per check
            per = {}
            for c in quick: per[checks[c]['ch']] = per.get(checks[c]['ch'], 0) + 1
            teaser[gid] = {'model': model, 'name': d['name'], 'short': doc['short'], 'brand': d.get('brand'), 'type': d.get('type'), 'cat': 'car',
                           'gen': doc['gen'], 'years': doc['years'], 'checks': len(quick), 'all': len(set(c.split('@')[0] for c in yq['ids'])),
                           'drive': per.get(8, 0), 'per': per, 'mins': max(5, round(sum(checks[c].get('t') or 30 for c in quick if checks[c]['ch'] >= 2) / 60)), 'known': sorted({u['t'] for y in ys_out.values() for u in y['unk']})[:4]}
    for s in list(QS['p']) + list(QS['d']): strings.add(s)
    for v in U.values():
        for k in ('how', 'why'):
            if isinstance(v.get(k), str) and len(v[k]) >= 30: strings.add(v[k])
    for v in INFO.values():
        for k in ('what', 'ok', 'bad'):
            if isinstance(v.get(k), str) and len(v[k]) >= 30: strings.add(v[k])
    if check_only: return gens, teaser, strings
    os.makedirs(os.path.join(out, 'gens'), exist_ok=True)
    index = {'v': VER, 'gens': {g: {'cat': t['cat'], 'name': f"{t['name']} {t['years'][0]}-{t['years'][1]}"} for g, t in teaser.items()}}
    bulk = [{'key': 'index', 'value': json.dumps(index, separators=(',', ':'))}]
    for g, doc in gens.items():
        s = json.dumps(doc, ensure_ascii=False, separators=(',', ':'))
        open(os.path.join(out, 'gens', g + '.json'), 'w', encoding='utf-8').write(s)
        bulk.append({'key': 'gen:' + g, 'value': s})
    json.dump(bulk, open(os.path.join(out, 'kv_bulk.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(sorted(strings), open(os.path.join(out, 'leak_strings.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    pub = os.path.join(REPO, 'data', 'checklist_store.json')
    NL = '\n'
    open(pub, 'w', encoding='utf-8', newline='\n').write('{' + NL + (',' + NL).join(f'{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}' for k, v in sorted(teaser.items())) + NL + '}' + NL)
    eng = os.path.join(src, 'store', 'engine.js')
    if os.path.exists(eng): shutil.copyfile(eng, os.path.join(HERE, 'engine.js'))
    return gens, teaser, strings


def quick_check(cid, x, y):
    """Quick check (the default run): must-dos, safety, this year's known issues, walk-aways and every check an unknown needs."""
    base = cid.split('@')[0]
    if any(base in (u.get('checks') or []) for u in y['unk']): return True
    return bool(x.get('key') or x.get('safe') or x.get('big') or 'k' in (x.get('tag') or '') or x.get('k') == 'walk' or x.get('kind') == 'vin')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--src', default=os.environ.get('LEMON_CHECKLIST_SRC', SRC0)); ap.add_argument('--out')
    a = ap.parse_args()
    out = os.path.abspath(a.out or os.path.join(a.src, 'store content'))
    if os.path.commonpath([out, REPO]) == REPO: sys.exit('refusing to write paid content inside the public repo: ' + out)
    gens, teaser, strings = build(a.src, out)
    sz = sorted(len(json.dumps(d, ensure_ascii=False)) for d in gens.values())
    print(f'{len(gens)} checklists -> {out}  ({sz[0] // 1024}-{sz[-1] // 1024} KB each, {sum(sz) // 1024} KB in all); '
          f'{len(strings)} paid strings; teaser -> data/checklist_store.json; engine copied: {os.path.exists(os.path.join(HERE, "engine.js"))}')
