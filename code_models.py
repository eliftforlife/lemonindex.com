# Model x engine code data (11-14, Lemon growth plan 2A-x): for every model and every OBD-II code its owners name in NHTSA complaints,
# how often, which model years, the mileage, the symptoms they describe and the parts they say were blamed, replaced or repaired.
# Scans the complaint text once (a few minutes) and caches counts to data/code_models.json; build.py (code_model_pages.py) only reads that JSON.
#   py -X utf8 code_models.py
# Same code regex, same not-a-code list and the same complaint -> model mapping as engine_codes.py, so the counts line up with the code pages.
# Only counts and complaint numbers are kept (never complaint text, names, VINs or places), so nothing personal reaches the site.
import collections, json, os, re, sqlite3, statistics, sys
sys.stdout.reconfigure(encoding='utf-8')
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
KW = r'C:\Users\elift\Desktop\Eliftforlife youtube\0 HQ\Research\Keywords\lemon_keywords.csv'   # the 11-05 Keyword Planner pull (memory keyword-planner-pull)
MIN = 10   # complaints naming the code on one model before that model gets a page (code_model_pages.py uses the same number)
L = lambda p: json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
YR = L('data/years.json') + (L('data/years_new.json') or []) + (L('data/years_tesla.json') or [])
NAME = {f['id']: f['name'] for f in YR}
XL = {}
for p in ('data/extras_local.json', 'data/extras_local_new.json', 'data/extras_local_low.json', 'data/extras_local_tesla.json'):
    for fid, ys in (L(p) or {}).items(): XL.setdefault(fid, {}).update(ys)
key = {}   # (NHTSA make, model, year) -> our model id (data_gap.py / engine_codes.py mapping, over every model the site has year pages for)
for f in YR:
    for y, x in XL.get(f['id'], {}).items():
        for mk, md, n in (x.get('names') or []):
            if n >= 2: key[(mk, md, int(y))] = f['id']
CODE = re.compile(r'\b([PBCU][0-3][0-9A-F]{3})\b')
NOT_CODES = {'C1500', 'C2500', 'C3500', 'B1500', 'B2000', 'B2200', 'B2300', 'B2500', 'B2600', 'B3000', 'B3500', 'B150E', 'B250E', 'B350E'}
# symptoms in our own words (engine_codes.py THEMES, so a model page and its code page describe them the same way)
THEMES = [('stalls or shuts off', r'\bstall|shut(s|ting)? off|shut down|died while|engine died|cut(s)? off'),
          ('loses power or goes into limp mode', r'loss of power|lost power|loses power|limp mode|reduced power|no power|lack of power|hesitat'),
          ('shakes, runs rough or misfires', r'misfir|rough idle|running rough|runs rough|shak|stutter|sputter'),
          ("won't start or hard to start", r"won'?t start|would not start|no start|hard to start|failed to start|cranks? but"),
          ('check engine light comes on', r'check engine|engine light|service engine|\bmil\b|malfunction indicator'),
          ('flashing check engine light', r'(check engine|engine light|\bcel\b|\bmil\b)[^.!?]{0,25}(flash|blink)|(flash|blink)\w* (check )?engine light'),
          ('transmission slips or shifts hard', r'slip|hard shift|harsh shift|jerk|won\'?t shift|stuck in gear|shudder'),
          ('uses or leaks oil', r'oil consumption|burn(s|ing)? oil|low oil|oil leak|adding oil'),
          ('overheats', r'overheat|temperature gauge|coolant leak'),
          ('fuel smell or fuel leak', r'fuel smell|gas smell|smell of gas|fuel leak|gas leak'),
          ('rattles or knocks', r'rattl|knock|ticking|tapping'),
          ('brakes or ABS act up', r'\babs\b|brake'),
          ('warning lights and electrical faults', r'warning lights|dash lights|electrical|battery|alternator')]
TH = [(t, re.compile(p, re.I)) for t, p in THEMES]
# parts owners name as the cause or the repair, in our own words (label, pattern on the owner's text)
PARTS = [('spark-plugs', 'Spark plugs', r'spark ?plugs?'),
         ('coils', 'Ignition coils', r'ignition coils?|\bcoils?\b(?! spring)|coil ?packs?|coil on plug'),
         ('injectors', 'Fuel injectors', r'injectors?\b'),
         ('cat', 'Catalytic converter', r'catalytic|\bcat converter|\bcatalyst\b|\bcats\b'),
         ('o2', 'Oxygen (O2 / air-fuel) sensor', r'\bo2 sensors?|oxygen sensors?|air[ /-]?fuel (ratio )?sensors?|\ba/f sensors?|\bo2s\b'),
         ('evap', 'EVAP part (purge valve, vent valve, canister)', r'purge (valve|solenoid)|vent (valve|solenoid)|charcoal canister|\bcanister\b|evap (valve|solenoid|canister|line|hose|system part)'),
         ('gas-cap', 'Gas cap', r'gas cap|fuel cap|filler cap'),
         ('pcv', 'PCV valve or oil separator', r'\bpcv\b|oil separator|crankcase vent'),
         ('maf', 'Mass airflow (MAF) sensor', r'\bmaf\b|mass air ?flow'),
         ('throttle', 'Throttle body', r'throttle body|electronic throttle|throttle (actuator|position sensor|motor)'),
         ('timing', 'Timing chain, tensioner or cam phaser', r'timing (chain|belt|tensioner|guide)s?|cam ?phasers?|\bphasers?\b|\bvvt\b|\bvct\b|variable (valve|cam) timing'),
         ('camcrank', 'Cam or crank position sensor', r'(cam(shaft)?|crank(shaft)?) (position )?sensors?|\b(ckp|cmp)\b'),
         ('headgasket', 'Head gasket or coolant in a cylinder', r'head gaskets?|coolant (in|into|intrusion|getting into)|cracked (cylinder )?head|cylinder head'),
         ('engine', 'Engine replaced or rebuilt', r'(new|replace\w*|rebuil\w*|reman\w*|used) (the )?(engine|motor)\b|(engine|motor) (was |were |had to be |needed to be |needs to be )?(replaced|rebuilt)|short block|long block'),
         ('pistons', 'Pistons, rings or valves', r'pistons?|piston rings|valve job|(burnt|burned|bent|stuck) valves?'),
         ('software', 'Software update (reflash)', r'software|reprogram|re-?flash|flash(ed)? the|(update|updated|updating) the (computer|ecm|pcm|ecu|tcm|module)|computer (update|was updated)|recalibrat'),
         ('ecm', 'Engine computer (ECM / PCM)', r'\b(ecm|pcm|ecu)\b|engine (control )?(computer|module)|powertrain control module'),
         ('tcm', 'Transmission computer (TCM)', r'\btcm\b|transmission control module|transmission computer'),
         ('trans', 'Transmission replaced or rebuilt', r'(new|replace\w*|rebuil\w*|reman\w*|used) (the )?transmission|transmission (was |had to be |needed to be |needs to be )?(replaced|rebuilt)'),
         ('valvebody', 'Valve body or shift solenoid', r'valve body|shift solenoids?|solenoid (pack|block|body)|mechatronic|lead frame'),
         ('torque', 'Torque converter', r'torque converter'),
         ('wiring', 'Wiring or a connector', r'wiring|harness|connectors?\b|corroded|chafed|pinched wire|ground wire|short(ed)? (circuit|out)'),
         ('battery', '12-volt battery', r'(12 ?v(olt)? )?battery\b(?! (pack|cooling|control|module|management))'),
         ('fuelpump', 'Fuel pump', r'fuel pumps?|high pressure pump|\bhpfp\b'),
         ('egr', 'EGR valve or cooler', r'\begr\b|exhaust gas recirculation'),
         ('thermostat', 'Thermostat', r'thermostat'),
         ('intake', 'Intake manifold or gasket', r'intake manifold|intake gasket|manifold gasket|intake runner'),
         ('turbo', 'Turbocharger or wastegate', r'turbo(charger)?s?\b|wastegate|waste gate'),
         ('vacuum', 'Vacuum leak or hose', r'vacuum (leak|hose|line)s?'),
         ('knock', 'Knock sensor', r'knock sensors?'),
         ('wheelspeed', 'Wheel speed (ABS) sensor', r'wheel speed sensors?|abs (wheel )?sensors?|speed sensors?|tone ring'),
         ('abs', 'ABS module, pump or brake accumulator', r'abs (module|pump|unit|control|motor)|hydraulic (control )?unit|\bhcu\b|brake accumulator|\baccumulator\b|brake actuator|actuator assembly|brake booster pump'),
         ('dpf', 'DPF, DEF or NOx sensor (diesel)', r'\bdpf\b|particulate filter|\bdef\b|diesel exhaust fluid|nox sensors?|\bscr\b'),
         ('airpump', 'Secondary air pump or valve', r'secondary air|air (injection )?pump|air switching valve|combination valve|air injection'),
         ('alternator', 'Alternator', r'alternator'),
         ('hybrid', 'Hybrid battery or inverter', r'hybrid battery|inverter|high voltage battery|hv battery'),
         ('steering', 'Power steering part', r'power steering (pump|motor|rack|module)|steering (rack|gear|column|motor|angle sensor)|\beps\b')]
PT = [(k, lab, re.compile(p, re.I)) for k, lab, p in PARTS]
FIXV = re.compile(r'replac|repair|fix|install|swap|\bnew\b|changed|rebuil|reflash|re-flash|reprogram|update|clean', re.I)
CAUSEV = re.compile(r'diagnos(?!tic)|determin|found|caus|due to|because|fail|faulty|\bbad\b|defective|broke|crack|leak|told|said|stated|advised|recommend|clog|stuck|short|blamed|issue with|problem with', re.I)
BACK = re.compile(r"(did|does|would|will) ?n[o']?t (fix|resolve|correct|solve|repair|help|cure)|(didn'?t|did not|does not|doesn'?t|has not|hasn'?t|have not|haven'?t) (fix|resolve|correct|solve|help|cure)\w*|"
                  r"(came|comes|come|coming|was|is) back on|(light|code|problem|issue|it) (came|comes|come|has come) back|(light|code|problem|issue|symptoms?) (returned|reappeared|resurfaced)|"
                  r"(happened|came on|occurred|reoccurred|started|appeared|failed) again|(problem|issue|code|light) (is |was )?still|still (has|had|have|having|comes? on|came on|on\b|illuminat|there|the same|showing|throw|getting|present|exists?|occur)|"
                  r"persist|re-?occur|recur|continu(es|ed|ing) to (happen|occur|come|have|throw|show|stall|misfire|fail)|second time|third time|same (problem|issue|code) (again|returned|came)", re.I)
# 11-14: owners often copy the code's own title ("P0420 catalyst system efficiency below threshold", "P1326 knock sensor detection system"),
# which names a part without saying it failed or was replaced. Those titles are cut from the text before parts are counted.
import importlib.util as _ilu
_sp = _ilu.spec_from_file_location('engine_code_defs', 'engine_code_defs.py'); ECD = _ilu.module_from_spec(_sp); _sp.loader.exec_module(ECD)
def _title_re(t):
    w = re.findall(r'[A-Za-z0-9]+', re.sub(r'\(.*?\)', ' ', t))
    return re.compile(r'[\W_]+'.join(map(re.escape, w)) + r'(?:[\W_]*(?:bank|sensor)[\W_]*\d)?', re.I) if len(w) >= 2 else None
TITLE = {k: _title_re(v['t']) for k, v in list(ECD.D.items()) + list(ECD.MAKE.items())}
GENERIC_TITLES = re.compile(r'catalyst(?: system)? efficiency(?: below threshold)?|knock sensor detection system|throttle actuator control(?: system)?|evap(?:orative emission)? (?:control )?system', re.I)
def strip_titles(text, codes):
    for k in codes:
        r = TITLE.get(k)
        if r: text = r.sub(' ', text)
    return GENERIC_TITLES.sub(' ', text)
SENT = re.compile(r'(?<=[.!?;])\s+|\n')
RECALL = re.compile(r'\brecall', re.I)
WARR = re.compile(r'warrant', re.I)

c = sqlite3.connect(DB)
D = collections.defaultdict(lambda: dict(n=0, mk=collections.Counter(), years=collections.Counter(), miles=[], themes=collections.Counter(), comps=collections.Counter(),
                                         parts=collections.defaultdict(lambda: [0, 0, 0]), co=collections.Counter(), crash=0, fire=0, towed=0, recall=0, warranty=0, odi=[]))
MODEL_CODED = collections.Counter()   # model -> complaints that name any code
CODE_ALL = collections.Counter(); seen = set(); total = 0
for odi, mk, md, yr, comp, d, crash, fire, towed, miles in c.execute(
        "select odino, make, model, year, comp, descr, crash, fire, towed, miles from rows where descr glob '*[PBCU][0-3][0-9A-F][0-9A-F][0-9A-F]*'"):
    if odi in seen: continue
    codes = set(CODE.findall((d or '').upper())) - NOT_CODES
    if not codes: continue
    seen.add(odi); total += 1; CODE_ALL.update(codes)
    try: y = int(yr)
    except (TypeError, ValueError): y = None
    fid = key.get((mk, md, y)) if y else None
    if not fid: continue
    MODEL_CODED[fid] += 1
    text = d or ''
    th = [t for t, r in TH if r.search(text)]
    sents = [s for s in SENT.split(strip_titles(text, codes)) if s.strip()]
    named, fixed = set(), set()
    for s in sents:
        for k, lab, r in PT:
            if r.search(s):
                if FIXV.search(s): fixed.add(k); named.add(k)
                elif CAUSEV.search(s): named.add(k)
    back = bool(BACK.search(text))
    try: m = int(miles or 0)
    except ValueError: m = 0
    for code in codes:
        x = D[(code, fid)]; x['n'] += 1; x['mk'][(mk or '').title()] += 1; x['years'][y] += 1
        if 0 < m < 400000: x['miles'].append(m)
        x['themes'].update(th)
        for cc in (comp or '').split(','):
            if cc.strip(): x['comps'][cc.strip().title()] += 1
        for k in named:
            p = x['parts'][k]; p[0] += 1
            if k in fixed: p[1] += 1; p[2] += back
        x['co'].update(codes - {code})
        x['crash'] += crash == 'Y'; x['fire'] += fire == 'Y'; x['towed'] += towed == 'Y'
        x['recall'] += bool(RECALL.search(text)); x['warranty'] += bool(WARR.search(text)); x['odi'].append(odi)

# Keyword Planner demand (11-05 pull): searches that name a code and a model, matched to our model ids by name words
ALIAS = {'honda-cr-v': ['crv', 'cr-v', 'cr v'], 'toyota-rav4': ['rav4', 'rav 4'], 'chevrolet-silverado': ['silverado'], 'ford-f-series': ['f150', 'f-150', 'f 150', 'f250', 'f-250', 'f350'],
         'ram-pickup': ['ram 1500', 'ram 2500', 'dodge ram', 'ram'], 'gmc-sierra': ['sierra'], 'mazda-mazda3': ['mazda3', 'mazda 3'], 'mazda-cx-5': ['cx5', 'cx-5'],
         'chrysler-town-country': ['town and country', 'town & country'], 'dodge-grand-caravan': ['grand caravan', 'caravan']}
def words(fid):
    if fid in ALIAS: return ALIAS[fid]
    nm = NAME[fid].lower(); parts = nm.split(' ', 1)
    return [parts[1]] if len(parts) > 1 else [nm]
kw = collections.Counter()
if os.path.exists(KW):
    import csv
    for row in csv.DictReader(open(KW, encoding='utf-8')):
        k = row['keyword'].lower(); cs = CODE.findall(k.upper())
        if len(cs) != 1: continue
        try: v = int(float(row['volume'] or 0))
        except ValueError: continue
        hits = [fid for fid in NAME if any(re.search(r'(?<![a-z0-9])' + re.escape(w) + r'(?![a-z0-9])', k) for w in words(fid))]
        if len(hits) == 1: kw[(cs[0], hits[0])] += v

rank = {}   # (code, model) -> rank of the code among the codes owners of that model name
by_model = collections.defaultdict(list)
for (code, fid), x in D.items(): by_model[fid].append((x['n'], code))
for fid, xs in by_model.items():
    for i, (n, code) in enumerate(sorted(xs, key=lambda t: (-t[0], t[1]))): rank[(code, fid)] = i + 1
q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]
out = {}
for (code, fid), x in sorted(D.items(), key=lambda kv: (-kv[1]['n'], kv[0])):
    if x['n'] < MIN: continue
    ms = x['miles']
    out[f'{code}|{fid}'] = dict(
        code=code, fid=fid, n=x['n'], mk=x['mk'].most_common(1)[0][0], rank=rank[(code, fid)], of=len(by_model[fid]),
        years=sorted([y, k] for y, k in x['years'].items() if y),
        miles=dict(n=len(ms), med=int(statistics.median(ms)), lo=q(ms, .25), hi=q(ms, .75)) if len(ms) >= 5 else None,
        themes=x['themes'].most_common(), comps=x['comps'].most_common(5),
        parts=sorted(([k, *v] for k, v in x['parts'].items() if v[0] >= 2), key=lambda t: (-t[1], -t[2], t[0])),
        co=[[k, v] for k, v in x['co'].most_common(8) if v >= 2],
        crash=x['crash'], fire=x['fire'], towed=x['towed'], recall=x['recall'], warranty=x['warranty'],
        odi=sorted(set(x['odi']), key=lambda o: -int(o)), kw=kw.get((code, fid), 0))
json.dump(dict(total=total, min=MIN, model_coded=dict(MODEL_CODED), code_all=dict(CODE_ALL), parts={k: lab for k, lab, _ in PARTS}, combos=out),
          open('data/code_models.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('complaints with a code', total, '| on a model we track', sum(MODEL_CODED.values()), '| model x code combos with', MIN, '+ complaints:', len(out),
      '| with Keyword Planner demand:', sum(1 for v in out.values() if v['kw']))
