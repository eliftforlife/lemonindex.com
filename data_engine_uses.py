# Builds data/engine_uses_tsb.json (11-13 navigation fix N3, report problem 3: "the 2GR page lists only the Lotus, not the Camry or Highlander").
# Which everyday /cars/ models an engine that has its own page was sold in, from the automaker's own words: NHTSA manufacturer communications
# (technical service bulletins, data/raw_more/MFR_COMMS_RECEIVED_*.zip) whose text names the engine code, filed under that make, model and year.
# Only codes in ALLOW, only under the makes listed with them, and a model year needs 2+ separate bulletins naming the code. Codes that bulletins
# use loosely (GM RPO lists, Mercedes multi-engine lists) are left out on purpose: we never guess which engine a car has.
#   usage: py -X utf8 data_engine_uses.py      (needs the NHTSA files in data/raw_more/; run from the repo, or set LEMON_RAW)
import csv, glob, io, json, os, re, sys, zipfile
sys.stdout.reconfigure(encoding='utf-8'); csv.field_size_limit(10 ** 8)
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.environ.get('LEMON_RAW') or os.path.join(HERE, 'data', 'raw_more')
norm = lambda s: re.sub(r'[^A-Z0-9]', '', (s or '').upper())
# code regex -> (engine page key, makes whose bulletins count, the page's own name for the code)
ALLOW = {r'\b2GR-?FE\b': ('toyota-2gr', {'TOYOTA', 'LEXUS'}, '2GR-FE')}
MIN_DOCS = 2
# (make, normalized model, year) -> /cars/ model ids, from the NHTSA names each model-year's complaints are filed under (same rule as data_extras2.py)
WANT = {}
for p in ('extras_local.json', 'extras_local_new.json', 'extras_local_low.json'):
    fp = os.path.join(HERE, 'data', p)
    if not os.path.exists(fp): continue
    for fid, ys in json.load(open(fp, encoding='utf-8')).items():
        for y, e in ys.items():
            tot = sum(n for *_, n in e.get('names', [])) or 1
            for mk, md, n in e.get('names', []):
                if n / tot >= .05: WANT.setdefault((mk.upper(), norm(md), int(y)), set()).add(fid)
hits = {}   # (fid, engine) -> {years: set, docs: set}
for z in sorted(glob.glob(os.path.join(RAW, 'MFR_COMMS_RECEIVED_*.zip'))):
    zz = zipfile.ZipFile(z)
    for row in csv.reader(io.TextIOWrapper(zz.open(zz.namelist()[0]), encoding='utf-8', errors='replace')):
        if len(row) < 5 or row[0] == 'TSB/Document ID': continue
        mk = row[1].strip().upper(); txt = row[4]
        for rx, (eng, makes, code) in ALLOW.items():
            if mk not in makes or not re.search(rx, txt, re.I): continue
            for ys in row[3].split(','):
                if not ys.strip().isdigit(): continue
                for fid in WANT.get((mk, norm(row[2]), int(ys)), ()):
                    h = hits.setdefault((fid, eng), {'yd': {}, 'docs': set(), 'code': code}); h['yd'].setdefault(int(ys), set()).add(row[0]); h['docs'].add(row[0])
    print('read', os.path.basename(z), len(hits))
out = {}
for (fid, eng), h in sorted(hits.items()):
    h['years'] = {y for y, d in h['yd'].items() if len(d) >= MIN_DOCS}   # a year counts when 2+ bulletins name the code for it (one bulletin's year list can span other engines' years)
    if len(h['docs']) < MIN_DOCS or not h['years']: continue
    out.setdefault(fid, {})[eng] = {'code': h['code'], 'years': sorted(h['years']), 'docs': len(h['docs']), 'ids': sorted(h['docs'])[:5]}
    print(f'{fid:28} {eng:14} {h["code"]:8} {len(h["docs"]):3} bulletins, years {min(h["years"])}-{max(h["years"])} ({len(h["years"])})')
json.dump({'src': 'NHTSA manufacturer communications (technical service bulletins) that name the engine code', 'cars': out},
          open(os.path.join(HERE, 'data', 'engine_uses_tsb.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote data/engine_uses_tsb.json:', sum(len(v) for v in out.values()), 'model-engine pairs')
