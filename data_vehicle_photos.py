# Photos for the plane + motorcycle sections (11-04): carphotos.py cutouts (Wikimedia Commons, commercial-use licenses) -> assets/v/<slug>.webp
# + data/vehicle_photos.json {family name: {src, w, h, author, license, page}}.   py data_vehicle_photos.py <src dir> [<src dir> ...] [--sheet]
import json, os, sys, re
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
Q = {  # family -> carphotos query slug
 'Cessna 172 Skyhawk': 'cessna-172', 'Cessna 150/152': 'cessna-152', 'Cessna 182 Skylane': 'cessna-182', 'Cessna 180/185 Skywagon': 'cessna-185', 'Cessna 206 Stationair': 'cessna-206',
 'Cessna 210 Centurion': 'cessna-210', 'Cessna 170': 'cessna-170', 'Cessna 208 Caravan': 'cessna-208-caravan', 'Cessna 310/340/414/421 twins': 'cessna-310',
 'Piper PA-28 Cherokee / Warrior / Archer': 'piper-pa-28', 'Piper PA-18 Super Cub': 'piper-pa-18-super-cub', 'Piper J-3 Cub': 'piper-j-3-cub', 'Piper PA-32 Saratoga / Cherokee Six': 'piper-pa-32',
 'Piper PA-34 Seneca': 'piper-pa-34-seneca', 'Piper PA-46 Malibu / M350 / M600': 'piper-pa-46', 'Piper PA-12 / PA-22': 'piper-pa-22', 'Beechcraft Bonanza': 'beechcraft-a36-bonanza',
 'Beechcraft Baron': 'beechcraft-baron', 'Beechcraft King Air': 'beechcraft-king-air', 'Cirrus SR20': 'cirrus-sr20', 'Cirrus SR22': 'cirrus-sr22', 'Mooney M20': 'mooney-m20',
 'Diamond DA40': 'diamond-da40', 'Diamond DA20': 'diamond-da20', 'Grumman AA-1 / AA-5': 'grumman-aa-5', 'Maule': 'maule-m-7', 'Aeronca Champ': 'aeronca-champ',
 'Air Tractor (crop dusters)': 'air-tractor-at-802', "Van's RV (kit planes)": 'vans-rv-7', 'Robinson R22': 'robinson-r22', 'Robinson R44': 'robinson-r44', 'Robinson R66': 'robinson-r66',
 'Bell 206 / 407': 'bell-206', 'Airbus AS350 (A-Star)': 'eurocopter-as350', 'Boeing 737': 'boeing-737', 'Boeing 757 / 767': 'boeing-767', 'Boeing 777 / 787': 'boeing-787',
 'Airbus A320 family': 'airbus-a320', 'Embraer regional jets': 'embraer-175',
 'Harley-Davidson Touring': 'harley-davidson-electra-glide', 'Harley-Davidson Softail': 'harley-davidson-softail', 'Harley-Davidson Sportster': 'harley-davidson-sportster',
 'Harley-Davidson Dyna': 'harley-davidson-dyna', 'Harley-Davidson Street 500/750': 'harley-davidson-street-750', 'Harley-Davidson Pan America': 'harley-davidson-pan-america',
 'Harley-Davidson LiveWire': 'harley-davidson-livewire', 'Honda Gold Wing': 'honda-gold-wing', 'Honda CBR': 'honda-cbr600rr', 'Honda Shadow': 'honda-shadow', 'Honda Africa Twin': 'honda-africa-twin',
 'Honda Rebel': 'honda-rebel', 'Honda NC700/NC750': 'honda-nc750x', 'Yamaha FJR1300': 'yamaha-fjr1300', 'Yamaha YZF-R1': 'yamaha-yzf-r1', 'Yamaha YZF-R6': 'yamaha-yzf-r6', 'Yamaha Bolt': 'yamaha-bolt',
 'Yamaha V Star': 'yamaha-v-star', 'Yamaha Raider / Stratoliner': 'yamaha-stratoliner', 'Yamaha MT-07 / MT-09': 'yamaha-mt-07', 'Yamaha Super Tenere': 'yamaha-super-tenere',
 'Kawasaki KLR650': 'kawasaki-klr-650', 'Kawasaki Ninja ZX-6R / ZX-10R': 'kawasaki-ninja-zx-6r', 'Kawasaki Ninja 300/400/650': 'kawasaki-ninja-400', 'Kawasaki Concours 14': 'kawasaki-1400gtr',
 'Kawasaki Vulcan': 'kawasaki-vulcan', 'Kawasaki Versys': 'kawasaki-versys', 'Suzuki Boulevard': 'suzuki-boulevard', 'Suzuki GSX-R': 'suzuki-gsx-r', 'Suzuki Hayabusa': 'suzuki-hayabusa',
 'Suzuki V-Strom': 'suzuki-dl650-v-strom', 'BMW GS (R1200/R1250GS)': 'bmw-r1200gs', 'BMW RT (R1200/R1250RT)': 'bmw-r1200rt', 'BMW K1600': 'bmw-k1600gt', 'BMW S1000RR': 'bmw-s1000rr',
 'Ducati Multistrada': 'ducati-multistrada', 'Ducati Monster': 'ducati-monster', 'Ducati Panigale': 'ducati-panigale', 'Ducati Scrambler': 'ducati-scrambler-icon', 'Ducati SportClassic': 'ducati-sportclassic',
 'Triumph Bonneville / Thruxton': 'triumph-bonneville', 'Triumph Rocket 3': 'triumph-rocket-3', 'Triumph Tiger': 'triumph-tiger', 'KTM 790/890 Adventure': 'ktm-790-adventure',
 'KTM 690 Duke / Enduro': 'ktm-690-duke', 'KTM 390': 'ktm-390-duke', 'Indian Scout': 'indian-scout-2015', 'Indian Chief / Chieftain': 'indian-chieftain', 'Can-Am Spyder': 'can-am-spyder-rt', 'Can-Am Ryker': 'can-am-ryker',
}
SKIP = set(a for a in sys.argv[1:] if a.startswith('skip=')); SKIP = {s[5:] for s in SKIP}
srcs = [a for a in sys.argv[1:] if not a.startswith(('--', 'skip='))]
CR = {}
for d in srcs:
    p = os.path.join(d, 'credits.json')
    if os.path.exists(p): CR.update({k: (v, d) for k, v in json.load(open(p, encoding='utf-8')).items()})
def clean(im):
    a = np.array(im); al = a[..., 3].astype(float); al[al < 48] = 0
    lab, n = ndimage.label(ndimage.binary_opening(al > 140, iterations=2))
    if n:
        big = 1 + int(np.argmax(ndimage.sum(np.ones_like(al), lab, range(1, n + 1)))); al[~ndimage.binary_dilation(lab == big, iterations=4)] = 0
    a[..., 3] = al.astype('uint8'); return Image.fromarray(a)
os.makedirs('assets/v', exist_ok=True); out, ims = {}, []
for fam, slug in Q.items():
    if slug not in CR or slug in SKIP: continue
    c, d = CR[slug]; pth = os.path.join(d, slug + '.png')
    if not os.path.exists(pth): continue
    im = clean(Image.open(pth).convert('RGBA')); im = im.crop(im.getbbox())
    if im.width > 900: im = im.resize((900, round(im.height * 900 / im.width)), Image.LANCZOS)
    ims.append((fam, im))
    if '--sheet' in sys.argv: continue
    im.save(f'assets/v/{slug}.webp', 'WEBP', quality=82, method=6)
    out[fam] = dict(src=f'/assets/v/{slug}.webp', w=im.width, h=im.height, author=c['author'], license=c['license'], page=c['page'], title=c['title'])
if '--sheet' in sys.argv:
    W, H, cols = 300, 190, 6; rows = (len(ims) + cols - 1) // cols
    sh = Image.new('RGB', (W * cols, H * rows), 'white'); dr = ImageDraw.Draw(sh)
    for i, (k, im) in enumerate(ims):
        t = im.copy(); t.thumbnail((W - 16, H - 30)); x, y = (i % cols) * W, (i // cols) * H; sh.paste(t, (x + (W - t.width) // 2, y + 4), t); dr.text((x + 6, y + H - 22), f'{i} {k[:40]}', fill='black')
    sh.save(os.path.join(srcs[0], '_sheet.png')); print('sheet', len(ims))
else:
    json.dump(out, open('data/vehicle_photos.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False); print('wrote', len(out))
