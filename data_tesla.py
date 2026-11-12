# 11-12 (UX test, Dan + Priya: "/cars/tesla-model-3/ is a 404", "your headline lemon 404s"): model and year pages for the Tesla Model S, 3 and X,
# back to their first U.S. model year, built exactly like every other /cars/ page (data_new_models.run(): NHTSA owner complaints filed within
# 3 years of the model year, 2023-2025 every complaint so far, recalls / crash tests / EPA from the same public APIs).
#   usage: py -X utf8 data_tesla.py     -> data/years_tesla.json, data/extras_local_tesla.json, data/extras_api_tesla.json
# Scores: the model-level Lemon Index stays the published study's (family_rates.csv: Model S 430, Model 3 203, Model X 407, from Tesla's
# cumulative 2012-2020 estimates). Per model year, Tesla doesn't report U.S. sales by model, so:
#   2021-2024: the Kelley Blue Book / Cox Automotive EV Sales Report estimates (the same figures the /electric/ pages use) -> scored with
#              the main method when 20,000+ were sold, the same way the Model Y's years are scored from its estimates
#   every other year: complaints only, never a score (low = {sold: None, why: 'tesla'}), and the page says why
import json, os, sys, concurrent.futures as cf
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = sys.argv[:1]
src = open(os.path.join(HERE, 'data_new_models.py'), encoding='utf-8').read()
src = src[:src.index('def load(n):')]   # its functions + the API helpers, not its plan loop
G = {'__file__': os.path.join(HERE, 'data_new_models.py'), '__name__': 'data_new_models'}
exec(compile(src, 'data_new_models.py', 'exec'), G)
run, API = G['run'], G['API']
KBB_URL = 'https://www.coxautoinc.com/market-insights/'   # Kelley Blue Book EV Sales Report (Cox Automotive), Q4 2022 + Q4 2024 editions
KBB_NOTE = 'Kelley Blue Book / Cox Automotive EV Sales Report estimates (Q4 2022 and Q4 2024 editions)'
EV = {c['name']: c for c in json.load(open(os.path.join(HERE, 'data', 'ev.json'), encoding='utf-8'))['cars']}
# raw KBB calendar-year figures, 2021-2024 (3 Lemon Index/ev/ev_data.py KBB table; ev.json keeps them after the sales-timing merge)
KBB = {'Tesla Model 3': [121877, 211618, 230015, 189903], 'Tesla Model S': [17653, 32675, 18052, 12426], 'Tesla Model X': [22546, 26121, 24767, 19855]}
CARS = [('tesla-model-s', 'Tesla Model S', 'car', r'MODEL S', 2012), ('tesla-model-3', 'Tesla Model 3', 'car', r'MODEL 3', 2017), ('tesla-model-x', 'Tesla Model X', 'suv', r'MODEL X', 2016)]
YT, XLT, XAT = [], {}, {}
for fid, name, seg, rx, first in CARS:
    p = dict(name=name, brand='Tesla', seg=seg, make='TESLA', rx=rx,
             sales=dict(manual={str(2021 + i): v for i, v in enumerate(KBB[name])}, url=KBB_URL, kind='calendar', note=KBB_NOTE))
    fy, car, xl, extra, rep = run(fid, p)
    have = {v['y'] for v in fy['years']}
    for v in fy['years']:
        if v.get('low'): v['low']['note'] = KBB_NOTE
    # the years with no per-model sales figure: a second pass with a placeholder of 1 car sold, so run() lists them as complaints-only
    # (parts, quotes, window count) - then the placeholder is removed: sold None, and the page says Tesla doesn't report it
    miss = [y for y in range(first, 2026) if y not in have]
    p2 = dict(p, sales=dict(manual={str(y): 1 for y in miss}, url='', kind='model'))
    G['LOW_MIN'] = 0; fy2, _, xl2, _, _ = run(fid, p2); G['LOW_MIN'] = 1   # 0: a first year whose owners filed only later (2017 Model 3) still gets its page
    for v in fy2['years']:
        if v['y'] in miss and v.get('low'):
            v['low'] = dict(sold=None, url='', kind='none', why='tesla'); fy['years'].append(v); xl[str(v['y'])] = xl2[str(v['y'])]
    fy['years'] = sorted([v for v in fy['years'] if v['y'] >= first], key=lambda v: v['y'])
    xl = {y: e for y, e in xl.items() if int(y) >= first and int(y) in {v['y'] for v in fy['years']}}
    YT.append(fy); XLT[fid] = xl
    API['MAKES'][name] = ['TESLA']
    def one(y, e=None):
        e = xl[str(y)]; nms = API['main_names'](e) if e['names'] else [('TESLA', name.split(' ', 1)[1].upper())]
        return str(y), {'recalls': API['recalls'](str(y), nms), 'safety': API['safety'](str(y), nms, name) if y >= 2011 else None, 'mpg': API['mpg'](name, y)}
    with cf.ThreadPoolExecutor(6) as ex: XAT[fid] = dict(ex.map(one, [v['y'] for v in fy['years']]))
    print(f"{name}: " + ', '.join(f"{v['y']} ({v['n']}{'' if v['li'] is None else ', LI ' + str(v['li'])})" for v in fy['years']), flush=True)
json.dump(YT, open(os.path.join(HERE, 'data', 'years_tesla.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(XLT, open(os.path.join(HERE, 'data', 'extras_local_tesla.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(XAT, open(os.path.join(HERE, 'data', 'extras_api_tesla.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(YT), 'Tesla models,', sum(len(f['years']) for f in YT), 'model years')
