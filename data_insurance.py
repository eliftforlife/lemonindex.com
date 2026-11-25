# 11-25 (Elijah approved the insurance mockup: "yes do this stuff"): data/insurance.json for /insurance/ (insurance_pages.py, assets/insurance.js).
# Source: 3 Lemon Index/data/insurance/ -> groups.json + anchor.json (anchor.py: official sample drivers, the anchored estimate and its measured
# error), ai_est/<ST>.json (the AI's age and record SHAPE only, never its company prices), state_doi/averages.json (NAIC 2024).
#   py data_insurance.py
import json, os, re, statistics as st
SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\insurance'
J = lambda *p: json.load(open(os.path.join(SRC, *p), encoding='utf-8'))
G, A, NAIC = J('groups.json'), J('anchor.json'), J('state_doi', 'averages.json')
AGES = ['16-17', '18-20', '21-24', '25-29', '30-39', '40-59', '60-69', '70+']
NAMES = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
         'DC': 'Washington, DC', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
         'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
         'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
         'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
         'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
         'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'}
SLUG = {k: ('washington-dc' if k == 'DC' else v.lower().replace(' ', '-')) for k, v in NAMES.items()}
# the official sources, as each state names them (state_doi/SOURCES.md); note = shown with every result from that state
OFF = {
    'NV': ('Nevada Division of Insurance', '2026 Consumer’s Guide to Automobile Insurance Rates', '2026', ''),
    'MD': ('Maryland Insurance Administration', 'Auto Insurance: A Comparison Guide to Rates (rates of Aug 1, 2026)', '2026', ''),
    'ND': ('North Dakota Insurance Department', '2026 Auto Insurance Cost Comparison Survey', '2026', ''),
    'OK': ('Oklahoma Insurance Department', 'Auto Insurance Rate Comparison (Nov 2, 2026)', '2026', 'Oklahoma’s sample drivers carry the state minimum liability (25/50/25) plus collision and comprehensive.'),
    'UT': ('Utah Insurance Department', '2025 Annual Auto Insurance Comparison', '2025', ''),
    'FL': ('Florida Office of Insurance Regulation', 'CHOICES auto rate comparison (current filings)', '2026', 'Florida publishes only two single-car sample drivers. Prices from its 10 biggest counties.'),
    'NE': ('Nebraska Department of Insurance', 'Auto Rate Guide 2017 (its latest)', '2017', '2017 rates: use them to compare companies, not for today’s price.'),
    'KY': ('Kentucky Department of Insurance', 'Auto premium comparison examples (2021 guide, its latest)', '2021', '2021 rates: use them to compare companies, not for today’s price.'),
    'DC': ('DC Department of Insurance, Securities and Banking', '2024 Automobile Insurance Premium Comparison', '2024', 'Minimum coverage only (no collision or comprehensive), so full coverage costs more.'),
    'WV': ('West Virginia Offices of the Insurance Commissioner', '2024 West Virginia Automobile Survey', '2024', 'Minimum coverage only (no collision or comprehensive), so full coverage costs more.'),
    'HI': ('Hawaii Insurance Division', '2026 Sample Annual Motor Vehicle Insurance Premiums', '2026', 'Liability and PIP only (no collision or comprehensive), and Hawaii doesn’t say the driver’s age.'),
}
STALE = {'NE', 'KY'}
# states whose insurance department has its own by-company comparison that we could not add yet (a form, or blocked to our fetcher): a plain link
TOOLS = {'AL': 'https://aldoi.gov/ComparePremiums/AutoRates.aspx', 'AZ': 'https://difi.az.gov/sites/default/files/2023%20Arizona%20Auto%20Premium%20Report%20%282%29.pdf',
         'CA': 'https://interactive.web.insurance.ca.gov/apex_extprd/f?p=111:10', 'CO': 'https://doi.colorado.gov/for-consumers/consumer-resources/premium-comparison-reports-auto',
         'NH': 'https://nh.gov/insurance/pc/prem_comp_auto.htm', 'SC': 'https://online.doi.sc.gov/Eng/Public/HelpInsure/SampleRates.aspx', 'TX': 'https://www.helpinsure.com'}
TOOL_NAME = {'AL': 'Alabama Department of Insurance', 'AZ': 'Arizona Department of Insurance and Financial Institutions', 'CA': 'California Department of Insurance',
             'CO': 'Colorado Division of Insurance', 'NH': 'New Hampshire Insurance Department', 'SC': 'South Carolina Department of Insurance', 'TX': 'Texas Department of Insurance (HelpInsure)'}


def naic_t5(s):
    n = NAIC[s]; b = n.get('basis', '')
    return n.get('combined_avg_premium_2024') or n.get('combined_average_premium_2024') or (n['avg_annual_premium'] if 'Table 5' in b else None)


def cov_short(g):
    s, k = g['state'], g['gid']
    if g['coverage'] == 'min': return 'state minimum coverage'
    if g['coverage'] == 'nocoll': return 'liability and PIP, no collision'
    if g['coverage'] == 'liab': return 'liability only'
    m = re.search(r'(\d+/\d+(?:/\d+)?)', g['cov_text'] or '')
    return (m.group(1) + ' coverage with collision' if m else 'full coverage')


def rec_txt(g):
    return {'clean': 'clean record', 'ticket': '1 ticket', 'accident': '1 at-fault accident', 'dui': 'a DUI'}.get(g['record']) or re.sub(r'\s+in 3 yrs', '', g['record_text'] or '')


def car_txt(g):
    cs = [re.sub(r'\s*\(.*?\)|\s+4-door|\s+4D|,.*$', '', c).strip() for c in g['cars'] if c]
    if not cs: return ''
    return cs[0] if len(cs) == 1 else (', '.join(cs[:-1]) + ' or ' + cs[-1]) if len(cs) <= 2 else cs[0] + ' and similar cars'


def who(g):
    d = g['desc'].lower(); a = g['age']
    if g['state'] == 'HI': return 'Age not stated'
    if g['state'] == 'NV' and g['gid'][0] in 'EH': return f'Married couple, both {a}'
    if g['state'] == 'UT' and g['gid'].startswith('mc'): return f'Married couple, both {a}'
    if g['state'] in ('OK', 'NE', 'FL') and g['couple']: return f'Age {a}, married'
    s = f'Age {a}'
    if "father's policy" in d or 'father’s policy' in d: s += ' on a parent’s policy'
    return s


def label(g):
    return ', '.join(x for x in (who(g), rec_txt(g), car_txt(g), cov_short(g)) if x)


out = {'meta': {'made': A['made'], 'K': A['K'], 'err': A['error_pct'], 'raw_err': A['raw_error_pct'], 'max_err': A['max_error_pct'], 'car': A['car_factor'],
                'naic': 'NAIC 2024 Auto Insurance Database Average Premium Supplement (combined average premium, Table 5)',
                'naic_url': 'https://content.naic.org/sites/default/files/2024-adb-average-premium-supplement.pdf', 'ages': AGES}, 'states': {}}
for s, nm in NAMES.items():
    aj = J('ai_est', f'{s}.json'); ai = aj['state_avg']; t5 = naic_t5(s); base = t5 / 12 * A['K']
    if 'variants' not in ai:   # 7 AI files (UT VA VT WA WI WV WY) have no state-level record prices: use the median company's record/age-35 ratio
        ai = dict(ai, variants={r: ai['ages']['30-39'] * st.median(c['variants'][r] / c['ages']['30-39'] for c in aj['companies'].values()) for r in ('ticket', 'accident', 'dui')})
    d = {'n': nm, 'slug': SLUG[s], 'naic': round(t5), 'est': [round(base * ai['ages'][a] / ai['ages']['30-39']) for a in AGES],
         'rm': {r: round(ai['variants'][r] / ai['ages']['30-39'], 3) for r in ('ticket', 'accident', 'dui')}}
    if s in TOOLS: d['tool'] = [TOOLS[s], TOOL_NAME[s]]
    gs = [g for g in G if g['state'] == s]
    if gs and s in OFF:
        doi = J('state_doi', f'{s}.json'); who_, what, yr, note = OFF[s]
        d['off'] = {'who': who_, 'what': what, 'year': yr, 'url': doi['source_url'], 'note': note, 'stale': s in STALE,
                    'groups': [{'id': g['gid'], 'age': g['age'], 'ag': g['age_group'], 'rec': g['record'], 'kind': g['kind'], 'cov': g['coverage'], 'cpl': g['couple'],
                                'lab': label(g), 'desc': g['desc'], 'nloc': g['n_loc'], 'rows': [[b, round(v), e] for b, v, e in g['brands']],
                                'ents': [[e, round(v)] for e, v in g['entities']]} for g in gs]}
    out['states'][s] = d
os.makedirs('data', exist_ok=True)
json.dump(out, open('data/insurance.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# the browser copy (assets/insurance.json, fetched by assets/insurance.js): no legal entity lists or long state descriptions (the state pages carry those)
cl = json.loads(json.dumps(out))
for v in cl['states'].values():
    for g in (v.get('off') or {}).get('groups', []): g.pop('ents'); g.pop('desc')
json.dump(cl, open('assets/insurance.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('assets/insurance.json:', os.path.getsize('assets/insurance.json') // 1024, 'KB')
print('data/insurance.json:', len(out['states']), 'states,', sum(1 for v in out['states'].values() if 'off' in v), 'with official prices,',
      os.path.getsize('data/insurance.json') // 1024, 'KB; error shown', A['error_pct'], '%')
for s in ('NV', 'MD', 'HI', 'FL'):
    for g in out['states'][s]['off']['groups'][:3]: print(' ', s, g['id'], '|', g['lab'])
