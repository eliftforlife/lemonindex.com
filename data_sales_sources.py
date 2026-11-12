# 11-12 (UX test, Priya: "scores can't be reproduced: no per-model sales source"): the U.S. sales source(s) behind every scored model,
# from the study's own sales tables (3 Lemon Index/data/sales.csv + sales_manual.csv) and the new-model batches (data/cars_new.json sales_url).
#   usage: py -X utf8 data_sales_sources.py   -> data/sales_sources.json {family_id: [url, ...]} (the figures themselves stay out: third-party data)
import csv, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
idof = lambda f: f.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('+', 'plus').replace('&', 'and')   # same ids as build.py
out = {}
for fn in ('sales.csv', 'sales_manual.csv', 'sales_2000.csv'):
    p = os.path.join(LEMON, 'data', fn)
    if not os.path.exists(p): continue
    for r in csv.DictReader(open(p, encoding='utf-8')):
        u = re.match(r'https?://\S+', (r.get('source') or '').strip())
        if u: out.setdefault(idof(r['family']), [])
        if u and u.group(0) not in out[idof(r['family'])]: out[idof(r['family'])].append(u.group(0))
for c in json.load(open(os.path.join(HERE, 'data', 'cars_new.json'), encoding='utf-8')):
    if c.get('sales_url'): out.setdefault(c['id'], []); out[c['id']] = [c['sales_url']] + [u for u in out[c['id']] if u != c['sales_url']]
for t in ('tesla-model-s', 'tesla-model-3', 'tesla-model-x'):   # data_tesla.py: per-year estimates from the KBB / Cox Automotive EV Sales Report
    out.setdefault(t, []); out[t] += [u for u in ('https://www.coxautoinc.com/market-insights/',) if u not in out[t]]
json.dump(out, open(os.path.join(HERE, 'data', 'sales_sources.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(out), 'models with a sales source')
