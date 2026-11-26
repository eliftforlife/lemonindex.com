# 11-25 (Elijah's year-page review): which model years have a before-you-buy checklist, for the year page entry cards (year_ux.py).
# Reads the checklist notes (3 Lemon Index/checklist/notes/<model>.json, "gens") and keeps a generation only when its checklist page was
# built (<short>-<gen>-preview.html, or <short>-preview.html for a model built as one page with every generation).
#   py data_checklists.py            -> data/checklists.json  {model id: [[gen, first year, last year], ...]}
import glob, json, os, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser('~'), 'Desktop', 'Eliftforlife youtube', '3 Lemon Index', 'checklist')
out, n = {}, 0
for p in sorted(glob.glob(os.path.join(SRC, 'notes', '*.json'))):
    d = json.load(open(p, encoding='utf-8')); m = d['model']; short = m.split('-', 1)[-1]
    whole = os.path.exists(os.path.join(SRC, f'{short}-preview.html'))
    gs = [[g, v['years'][0], v['years'][1]] for g, v in d['gens'].items() if whole or os.path.exists(os.path.join(SRC, f'{short}-{g}-preview.html'))]
    if gs: out[m] = sorted(gs, key=lambda x: x[1]); n += len(gs)
NL = chr(10)
open('data/checklists.json', 'w', encoding='utf-8').write('{' + NL + (',' + NL).join(f'{json.dumps(k)}: {json.dumps(v)}' for k, v in sorted(out.items())) + NL + '}' + NL)
print(f'data/checklists.json: {len(out)} models, {n} generations')
