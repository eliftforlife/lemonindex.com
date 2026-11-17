# 11-17 visitor report (site feedback): the 2005-2010 Chrysler 300 pages listed only the 5.7 HEMI and 6.1 SRT8 in "Engines in the <year> 300",
# because that row shows only engines with a page of their own. EPA's version list (fueleconomy.gov vehicles.csv) also has the 2.7 L V6 and
# 3.5 L V6 in those years. This writes, per model year, the EPA engines of a /cars/ model that have no page of their own, so the row can
# name them too (plain chips, no link). Only the models in WANT, with their EPA model names; nothing guessed.
#   py -X utf8 data_engine_epa_other.py -> data/engine_epa_other.json
import csv, json, os
csv.field_size_limit(10 ** 8)
HERE = os.path.dirname(os.path.abspath(__file__))
WANT = {'chrysler-300': ('Chrysler', ('300', '300 AWD', '300C AWD', '300C/SRT-8', '300/SRT-8'), 2005, 2010, {(5.7, 8), (6.1, 8)})}   # (make, EPA models, years, engines that have a page)
out = {}
for r in csv.DictReader(open(os.path.join(HERE, 'data', 'cache', 'vehicles.csv'), encoding='utf-8', errors='replace')):
    for fid, (mk, models, y0, y1, has) in WANT.items():
        y = int(r['year'])
        if r['make'] != mk or r['model'] not in models or not y0 <= y <= y1 or not r['displ']: continue
        d, c = float(r['displ']), int(float(r['cylinders'] or 0))
        if (d, c) in has: continue
        lab = f'{d:.1f} L ' + ({4: 'I4', 6: 'V6', 8: 'V8'}.get(c) or f'{c}-cyl')
        out.setdefault(fid, {}).setdefault(str(y), set()).add(lab)
out = {f: {y: sorted(v) for y, v in sorted(d.items())} for f, d in out.items()}
json.dump(dict(note='EPA fueleconomy.gov vehicles.csv: engines per model year with no engine page of their own', models=out),
          open(os.path.join(HERE, 'data', 'engine_epa_other.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(out)
