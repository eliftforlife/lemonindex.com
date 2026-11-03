# Car photos for the year pages (11-02, Elijah: "only the exact year, clean cutout, tiny Wikipedia credit"). Real Wikimedia Commons photos we already cut out
# for videos; each listed here was checked by eye. Writes assets/cars/<fid>-<year>.webp + data/photos.json {fid: {year: {src, credit}}}.
#   usage: py data_photos.py
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\shorts v2\kit\assets\cars'
HERO = r'C:\Users\elift\Desktop\Eliftforlife youtube\0 HQ\hero3d\assets\cars'
CR = {**json.load(open(os.path.join(KIT, 'credits.json'), encoding='utf-8'))}
for f in ('credits_f150_years.json', 'credits_year3.json'):
    for k, v in json.load(open(os.path.join(HERO, f), encoding='utf-8')).items(): CR['hero:' + k[:-4]] = v
# (family id, model year, source): kit file name, or hero:<name>. Title year = model year, US-market car, no show-floor/China/UK-spec photos.
PICK = [('ram-pickup', 2014, '2014-ram-1500-hemi'), ('mazda3', 2015, '2015-mazda3'), ('toyota-corolla', 2015, '2015-toyota-corolla-le'), ('chevrolet-cruze', 2016, '2016-chevrolet-cruze-lt'),
        ('honda-civic', 2016, '2016-honda-civic-ex'), ('nissan-sentra', 2016, '2016-nissan-sentra'), ('toyota-camry', 2016, '2016-toyota-camry'), ('toyota-rav4', 2016, '2016-toyota-rav4'),
        ('volkswagen-jetta', 2016, '2016-volkswagen-jetta'), ('bmw-x3', 2018, 'hero:x3-2018'), ('acura-mdx', 2017, 'acura-mdx-2017'), ('acura-rdx', 2019, 'acura-rdx-2019'),
        ('chevrolet-bolt', 2020, 'chevrolet-bolt-2020'), ('chevrolet-equinox', 2018, 'chevrolet-equinox-2018'), ('chevrolet-silverado', 2019, 'chevrolet-silverado'), ('chevrolet-volt', 2017, 'chevrolet-volt-2017'),
        ('chrysler-200', 2015, 'chrysler-200-2015'), ('chrysler-pacifica', 2017, 'chrysler-pacifica-2017'), ('ford-escape', 2010, 'ford-escape-2010'), ('ford-explorer', 2013, 'ford-explorer-2013'),
        ('ford-focus', 2014, 'ford-focus-2014'), ('ford-fusion', 2010, 'ford-fusion-2010'), ('gmc-yukon-xl', 2015, 'gmc-yukon-2015'), ('honda-accord', 2018, 'honda-accord-2018'),
        ('honda-civic', 2022, 'honda-civic-2022'), ('honda-cr-v', 2017, 'honda-cr-v-2017'), ('honda-odyssey', 2018, 'honda-odyssey-2018'), ('honda-pilot', 2016, 'honda-pilot-2016'),
        ('hyundai-accent', 2019, 'hyundai-accent'), ('jeep-cherokee', 2014, 'jeep-cherokee-2014'), ('jeep-gladiator', 2020, 'jeep-gladiator-2020'), ('jeep-renegade', 2015, 'jeep-renegade-2015'),
        ('jeep-wrangler', 2018, 'jeep-wrangler-2018'), ('kia-telluride', 2020, 'kia-telluride-2020'), ('lexus-es', 2019, 'lexus-es-2019'), ('nissan-pathfinder', 2013, 'nissan-pathfinder-2013'),
        ('subaru-outback', 2020, 'subaru-outback-2020'), ('tesla-model-y', 2020, 'tesla-model-y'), ('toyota-4runner', 2017, 'toyota-4runner'), ('toyota-camry', 2019, 'toyota-camry-2019'),
        ('toyota-corolla', 2020, 'toyota-corolla-2020'), ('toyota-rav4', 2019, 'toyota-rav4-2019'), ('toyota-sienna', 2021, 'toyota-sienna-2021'), ('toyota-tundra', 2022, 'toyota-tundra-2022'),
        ('volkswagen-atlas', 2018, 'volkswagen-atlas-2018'), ('bmw-3-series', 2006, 'hero:bmw3-2006'), ('honda-civic', 2012, 'hero:civic-2012')] + \
       [('ford-f-series', y, f'hero:f150-y{y}') for y in range(2015, 2021)]
# judged ugly on the 11-02 contact sheet: cropped/show-stand Explorer, ragged Silverado edge, Sentra+MDX cut off, dealer '2016' signs, Outback stray parts, Dutch-plate Pathfinder
SKIP = {'ford-explorer-2013', 'chevrolet-silverado', '2016-nissan-sentra', '2016-toyota-camry', '2016-volkswagen-jetta', 'acura-mdx-2017', 'subaru-outback-2020', 'nissan-pathfinder-2013', 'lexus-es-2019', 'acura-rdx-2019', '2016-chevrolet-cruze-lt', 'ford-escape-2010', 'hero:f150-y2015', 'kia-telluride-2020'} | set(sys.argv[1:])
YEARS = {f['id']: {v['y'] for v in f['years']} for f in json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8'))}
os.makedirs(os.path.join(HERE, 'assets', 'cars'), exist_ok=True)
out, sheet = {}, []
for fid, y, src in PICK:
    if src in SKIP or y not in YEARS.get(fid, set()): print('skip', fid, y, src); continue
    p = os.path.join(HERO, src[5:] + '.png') if src.startswith('hero:') else os.path.join(KIT, src + '.png')
    im = Image.open(p).convert('RGBA'); a = np.array(im); m = a[..., 3] > 40
    lab, n = ndimage.label(ndimage.binary_opening(m, iterations=3));   # opening drops thin antennas/wires
    sz = ndimage.sum(m, lab, range(1, n + 1)); keep = ndimage.binary_dilation(lab == (1 + int(np.argmax(sz))), iterations=4) & m
    a[..., 3] = np.where(keep, a[..., 3], 0); im = Image.fromarray(a); im = im.crop(im.getbbox()); im.thumbnail((1200, 800))
    name = f'{fid}-{y}.webp'; im.save(os.path.join(HERE, 'assets', 'cars', name), 'WEBP', quality=86)
    c = CR.get(src, {}); out.setdefault(fid, {})[str(y)] = {'src': '/assets/cars/' + name, 'author': c.get('author', ''), 'license': c.get('license', ''), 'page': c.get('page', ''), 'w': im.width, 'h': im.height}
    sheet.append((f'{fid} {y}', im))
json.dump(out, open(os.path.join(HERE, 'data', 'photos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
W = Image.new('RGB', (6 * 300, ((len(sheet) + 5) // 6) * 230), (246, 245, 240))
from PIL import ImageDraw
d = ImageDraw.Draw(W)
for i, (lab, im) in enumerate(sheet):
    t = im.copy(); t.thumbnail((280, 180)); x, yy = (i % 6) * 300 + 10, (i // 6) * 230 + 10; W.paste(t, (x, yy), t); d.text((x, yy + 190), lab, fill=(0, 0, 0))
W.save(os.path.join(os.environ.get('TEMP', '.'), 'photos_sheet.png')); print(len(sheet), 'photos')
