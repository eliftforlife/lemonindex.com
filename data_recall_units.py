# 11-14 growth plan 2B-1 (recall check pages): how many vehicles each recall campaign covers, and NHTSA's "do not drive" /
# "park outside" warnings, for the campaigns the site already lists. recall_pages.py reads data/recall_units.json.
#   usage: py -X utf8 data_recall_units.py   (after nhtsa_refresh.py has downloaded a fresh FLAT_RCL_POST_2010.zip)
# Source: NHTSA's recall flat file FLAT_RCL_POST_2010 (static.nhtsa.gov/odi/ffdd/rcl/), one row per make/model/year in a campaign.
#   field 2 CAMPNO, 12 POTAFF (vehicles potentially affected: the WHOLE campaign, every make and model in it), 28 DO_NOT_DRIVE, 29 PARK_OUTSIDE.
# Recalls filed before 2010 aren't in that file, so they get no vehicle count (the pages say so).
import glob, json, os, re, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
ZIP = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\raw\nhtsa\FLAT_RCL_POST_2010.zip'
want = set()
for p in glob.glob(os.path.join(HERE, 'data', '*.json')):   # every campaign number the site's data files hold (extras_api*, extra_models*, hd ...)
    if os.path.basename(p) in ('recall_units.json', 'page_dates.json'): continue
    want |= set(re.findall(r'"(\d\d[VE]\d{6})"', open(p, encoding='utf-8').read()))
out = {}
with zipfile.ZipFile(ZIP) as z, z.open(z.namelist()[0]) as fh:
    for line in fh:
        p = line.decode('latin-1').rstrip('\r\n').split('\t')
        if len(p) < 29 or p[1] not in want: continue
        n = int(p[11]) if p[11].strip().isdigit() else 0
        dnd, po = int(p[27].strip().lower() == 'yes'), int(p[28].strip().lower() == 'yes')
        o = out.get(p[1])
        out[p[1]] = [max(n, o[0]) if o else n, max(dnd, o[1]) if o else dnd, max(po, o[2]) if o else po]
json.dump(dict(sorted(out.items())), open(os.path.join(HERE, 'data', 'recall_units.json'), 'w', encoding='utf-8'), separators=(',', ':'))
print(f'{len(want)} campaigns on the site, {len(out)} found in the flat file ({sum(1 for v in out.values() if v[0])} with a vehicle count, '
      f'{sum(v[1] for v in out.values())} do-not-drive, {sum(v[2] for v in out.values())} park-outside) -> data/recall_units.json')
