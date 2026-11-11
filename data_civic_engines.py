# 11-10: data/engines_honda-civic.json for tabbed.py's engine chart, from the checked groups file + the AI engine cutouts.
# Groups: years from EPA fueleconomy.gov (vehicles.csv, 1984+) and Wikipedia's Honda E/D/K/R/L engine articles (codes, pre-1984 years).
# Images: gpt-image-2 low quality, cut out with rembg, checked by hand; saved as WebP with alpha in assets/engines/civic/.
import json, os
from PIL import Image
SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\engine images test\civic'
# 11-11 (Elijah approved): factory-cover press-photo style with period-correct tops (air cleaner / valve cover / plastic cover);
# a group whose new picture failed the check twice keeps its 11-10 cutout.
COV = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\engine images test\covers_regular\cut'
HERE = os.path.dirname(os.path.abspath(__file__)); OUTD = os.path.join(HERE, 'assets', 'engines', 'civic'); os.makedirs(OUTD, exist_ok=True)
G = json.load(open(os.path.join(SRC, 'groups.json'), encoding='utf-8'))
out = []
for g in G:
    cut = os.path.join(COV, 'civic-' + g['id'] + '.png'); d = {k: v for k, v in g.items() if k != 'prompt'}
    if not os.path.exists(cut): cut = os.path.join(SRC, 'cut', g['id'] + '.png')
    if os.path.exists(cut):
        im = Image.open(cut).convert('RGBA'); im.thumbnail((640, 640)); name = f'honda-civic-{g["id"]}-engine.webp'
        im.save(os.path.join(OUTD, name), 'WEBP', quality=82, method=6)
        d['img'] = {'src': f'/assets/engines/civic/{name}', 'w': im.width, 'h': im.height}
    out.append(d)
json.dump(out, open(os.path.join(HERE, 'data', 'engines_honda-civic.json'), 'w', encoding='utf-8'), indent=1)
print(len(out), 'groups,', sum(1 for d in out if d.get('img')), 'with images')
