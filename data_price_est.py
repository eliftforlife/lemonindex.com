# 11-24 (Elijah: "push live and build price box"): AI price estimates by mileage -> data/price_est.json for price_box.py.
# Source: the checklist price run (3 Lemon Index/checklist/prices/<model>.json + prices_brackets.py), AI estimates written and
# fact-checked by model, never listings or an appraisal. Re-run after the price files change:
#   py -X utf8 "<Lemon>/checklist/prices_brackets.py" && py -X utf8 data_price_est.py
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
CK = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\checklist'
JARGON = re.compile(r'multiplier|\b(engine|trim|drive)( and (trim|drive))? tables?\b|\bvia (the )?(trims|engine)|\badjusted by\b', re.I)


def clean_mk(t):
    """the builders' trim notes, minus internal words (the checklist's engine/trim multiplier tables)"""
    t = re.sub(r'\s*\([^)]*\b(multiplier|tables?)\b[^)]*\)', '', t)
    t = re.sub(r'\b(above|below) the (trim|engine) multipliers', r'\1 these prices', t)
    t = re.sub(r'\b(is|are) (not priced by|not covered by|not) (this table|these rows)', r'\1 not covered here', t)
    t = re.sub(r'\b(\d{4}-\d{2}) rows\b', r'\1 prices', t)
    t = re.sub(r'^(year )?table (is|set for) an? ', '', t.strip())
    out = []
    for sent in re.split(r'(?<=\.)\s+', t):
        parts = re.split(r';\s*', sent.rstrip('.'))
        cl = [c for c in parts if c and not JARGON.search(c)]
        if cl: out.append('; '.join(cl))
    t = '. '.join(out).strip().rstrip('.')
    return t[:1].upper() + t[1:] if t else ''


import sys; sys.path.insert(0, CK); import prices_brackets as PB   # 11-24: the price at the year's typical miles (the /budget/ page)
B = json.load(open(os.path.join(CK, 'prices_brackets.json'), encoding='utf-8'))
out = {'date': 'November 2026', 'brackets': B['brackets'], 'm': {}}
for m, years in B['models'].items():
    p = os.path.join(CK, 'prices', m + '.json')
    P = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    PP = PB.load(m); rows = {}
    for y, t in years.items():
        at = PB.price_at(PP, int(y), t['typical_miles']) if PP else None   # [private lo, hi], [dealer lo, hi] at typical miles
        rows[y] = [t['typical_miles'], [0 if b['rare'] else b['private'] + b['dealer'] for b in t['brackets']], (at[0] + at[1]) if at else 0]
    out['m'][m] = {'mk': clean_mk(str(P.get('market') or '')), 's': P.get('section', ''), 'y': rows}
json.dump(out, open(os.path.join(HERE, 'data', 'price_est.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(out['m']), 'models ->', 'data/price_est.json')
