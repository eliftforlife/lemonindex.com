# Real, free-licensed photos of BMW engines from Wikimedia Commons (11-10; no AI images). For each engine code: the Commons
# category's files, keep photos whose file name or description names the code, with a free license (PD / CC0 / CC BY / CC BY-SA),
# download an 800 px copy to assets/engines/<code>.jpg and record author + license in data/bmw_engine_photos.json.
# Each picked photo is then checked by eye before it ships (a wrong engine = no photo).   py -X utf8 data_bmw_engine_photos.py
import json, os, re, sys, time, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); UA = {'User-Agent': 'LemonIndex/1.0 (lemonindex.com; data bot)'}
CAT = {'M54': ['BMW M54 engine'], 'N52': ['BMW N52 engine'], 'N54': ['BMW N54'], 'N55': ['BMW N55'], 'N20': ['BMW N20'], 'B48': ['BMW B48'],
       'B58': ['BMW B58'], 'N62': ['BMW N62 engine'], 'N63': ['BMW N63 engine', 'BMW N63/S63 engine'], 'S55': ['BMW S55 engine'],
       'S58': ['BMW S58 engine', 'BMW S58'], 'S63': ['BMW S63 engine', 'BMW N63/S63 engine'], 'S54': ['BMW S54 engine', 'BMW S54']}
FREE = re.compile(r'^(public domain|pd|cc0|cc by(-sa)? [0-9.]+|cc-by(-sa)?-[0-9.]+)', re.I)
def get(params):
    u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(dict(params, format='json'))
    for k in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))
        except Exception as e: time.sleep(5 * (k + 1))
    return {}
OUT = {}; os.makedirs(os.path.join(HERE, 'assets', 'engines'), exist_ok=True)
for code, cats in CAT.items():
    cands = []
    for c in cats:
        d = get(dict(action='query', generator='categorymembers', gcmtitle='Category:' + c, gcmtype='file', gcmlimit=50, prop='imageinfo',
                     iiprop='url|extmetadata|size|mime', iiurlwidth=800))
        for p in (d.get('query') or {}).get('pages', {}).values():
            ii = (p.get('imageinfo') or [{}])[0]; md = ii.get('extmetadata') or {}
            lic = (md.get('LicenseShortName') or {}).get('value', ''); desc = re.sub('<[^>]+>', '', (md.get('ImageDescription') or {}).get('value', ''))
            art = re.sub('<[^>]+>', '', (md.get('Artist') or {}).get('value', '')).strip()
            if ii.get('mime') != 'image/jpeg' or not FREE.match(lic.strip()): continue
            named = re.search(r'\b' + code + r'\b', p['title'] + ' ' + desc, re.I) or (code in ('N63', 'S63') and re.search(r'\bN63\b|\bS63\b', p['title'] + desc, re.I))
            if not named: continue
            cands.append(dict(file=p['title'], url=ii.get('thumburl'), w=ii.get('width'), h=ii.get('height'), license=lic, author=art[:80], desc=desc[:200], page=ii.get('descriptionurl'), cat=c))
        time.sleep(2)
    cands.sort(key=lambda x: -(x['w'] or 0) * (x['h'] or 0))
    OUT[code] = cands[:4]
    print(code, len(cands), [x['file'] for x in cands[:4]], flush=True)
json.dump(OUT, open(os.path.join(HERE, 'data', 'cache', 'bmw_engine_photo_cands.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# download the top 2 candidates per code for an eye check
for code, cs in OUT.items():
    for i, c in enumerate(cs[:2]):
        if not c['url']: continue
        dst = os.path.join(HERE, 'data', 'cache', 'enginephotos', f'{code}_{i}.jpg'); os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            urllib.request.urlretrieve(c['url'], dst) if False else open(dst, 'wb').write(urllib.request.urlopen(urllib.request.Request(c['url'], headers=UA), timeout=60).read())
            time.sleep(2)
print('done')
