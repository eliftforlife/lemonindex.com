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
SKIP = set()
# 11-03 second pass (Elijah listed every blank row): a year in the search gets the right generation; each checked on a contact sheet
ALIAS = {'mercedes-benz-glk/glc': 'mercedes-benz-glc', 'mercedes-benz-m/gle': 'mercedes-benz-gle',
         **{k: f'{y}-{k}' for y, k in [(2017, 'mercedes-benz-e-class'), (2017, 'audi-a4'), (2016, 'nissan-maxima'), (2019, 'porsche-cayenne'), (2017, 'nissan-rogue'),
            (2018, 'subaru-crosstrek'), (2017, 'mazda-cx-5'), (2014, 'chevrolet-impala'), (2013, 'ford-taurus'), (2015, 'dodge-charger'), (2014, 'dodge-journey'),
            (2019, 'audi-a6'), (2011, 'chrysler-town-and-country'), (2016, 'ford-explorer'), (2018, 'tesla-model-3'), (2016, 'tesla-model-x'), (2016, 'toyota-tacoma'), (2017, 'dodge-grand-caravan'), (2019, 'kia-sedona'), (2015, 'mercedes-benz-c-class')]}, 'lexus-rx': '2017-lexus-rx-350'}
CR = json.load(open(os.path.join(SRC, 'credits.json'), encoding='utf-8'))
fid = lambda n: n.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('+', 'plus').replace('&', 'and')
import csv
names = [r['family'] for r in csv.DictReader(open('data/family_rates.csv', encoding='utf-8'))]
have = json.load(open('data/photos.json', encoding='utf-8'))
def clean(im):
    """11-03 (Elijah: 'some clipping'): drop the faint haze rembg leaves and every blob that isn't the car (ghost cars, people, signs)."""
    import numpy as np
    from scipy import ndimage
    a = np.array(im); al = a[..., 3].astype(float)
    al[al < 48] = 0
    lab, n = ndimage.label(ndimage.binary_opening(al > 140, iterations=2))
    if n:
        big = 1 + int(np.argmax(ndimage.sum(np.ones_like(al), lab, range(1, n + 1))))
        keep = ndimage.binary_dilation(lab == big, iterations=4)
        al[~keep] = 0
    a[..., 3] = al.astype('uint8'); return Image.fromarray(a)
out, ims = {}, []
for n in names:
    k = fid(n); slug = ALIAS.get(k, k)   # carphotos.py names files by the same slug rule
    pth = os.path.join(SRC, slug + '.png')
    if k in have or slug in SKIP or not os.path.exists(pth) or slug not in CR: continue
    im = clean(Image.open(pth).convert('RGBA')); im = im.crop(im.getbbox())
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
