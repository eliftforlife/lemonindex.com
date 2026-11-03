# One photo per model (11-03, Elijah: "Apple uses more photos than us"): the home tiles and the rankings rows show a real car for every model.
# Source: 3 Lemon Index/autopilot/lib/carphotos.py cutouts (Wikimedia Commons, commercial-use licenses, rembg) in <src dir> + its credits.json.
# Models that already have exact-year photos (data/photos.json) are skipped. Bad cutouts go in SKIP after a look at the contact sheet.
#   py data_model_photos.py <src dir>            -> assets/cars/m-<fid>.webp + data/model_photos.json {fid: {src, w, h, author, license, page}}
#   py data_model_photos.py <src dir> --sheet    -> _sheet.png contact sheet to check by eye
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
SRC = sys.argv[1]
# checked by eye 11-03: classic/old-generation, police, crashed or cut-off photos -> no photo rather than a wrong one
SKIP = {'chevrolet-impala', 'mercedes-benz-e-class', 'audi-a4', 'nissan-maxima', 'tesla-model-x', 'chrysler-town-and-country', 'dodge-charger',
        'subaru-crosstrek', 'mazda-cx-5', 'ford-taurus', 'dodge-journey', 'tesla-model-3', 'ford-explorer'}
ALIAS = {'mercedes-benz-glk/glc': 'mercedes-benz-glc', 'mercedes-benz-m/gle': 'mercedes-benz-gle'}
CR = json.load(open(os.path.join(SRC, 'credits.json'), encoding='utf-8'))
fid = lambda n: n.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('+', 'plus').replace('&', 'and')
import csv
names = [r['family'] for r in csv.DictReader(open('data/family_rates.csv', encoding='utf-8'))]
have = json.load(open('data/photos.json', encoding='utf-8'))
out, ims = {}, []
for n in names:
    k = fid(n); slug = ALIAS.get(k, k)   # carphotos.py names files by the same slug rule
    pth = os.path.join(SRC, slug + '.png')
    if k in have or slug in SKIP or not os.path.exists(pth) or slug not in CR: continue
    im = Image.open(pth).convert('RGBA'); im = im.crop(im.getbbox())
    if im.width > 900: im = im.resize((900, round(im.height * 900 / im.width)), Image.LANCZOS)
    ims.append((k, im))
    if '--sheet' in sys.argv: continue
    dst = f'assets/cars/m-{slug}.webp'; im.save(dst, 'WEBP', quality=82, method=6)
    c = CR[slug]; out[k] = dict(src='/' + dst, w=im.width, h=im.height, author=c['author'], license=c['license'], page=c['page'], title=c['title'])
if '--sheet' in sys.argv:
    W, H, cols = 300, 190, 6; rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGB', (W * cols, H * rows), 'white'); d = ImageDraw.Draw(sh)
    for i, (k, im) in enumerate(ims):
        t = im.copy(); t.thumbnail((W - 16, H - 30)); x, y = (i % cols) * W, (i // cols) * H
        sh.paste(t, (x + (W - t.width) // 2, y + 4), t); d.text((x + 6, y + H - 22), f'{i} {k}', fill='black')
    sh.save(os.path.join(SRC, '_sheet.png')); print('sheet', len(ims))
else:
    json.dump(out, open('data/model_photos.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False); print('wrote', len(out))
