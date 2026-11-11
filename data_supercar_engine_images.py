# Our own supercar and performance engine illustrations (AI-generated, gpt-image-2 LOW, Elijah 11-11) -> optimized WebP (1200 px + a 640 px card copy) with the
# same honest XMP as the BMW ones (data_bmw_engine_images.py: IPTC trainedAlgorithmicMedia, credit, CC BY 4.0). Each one was checked against
# reference photos of that engine (cylinder count and layout, turbo placement, intake and covers); an engine whose picture failed the check
# twice is left out (no image beats a wrong one). Updates data/supercar_engine_photos.json.   py -X utf8 data_supercar_engine_images.py
import json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\engine images test\supercar\cut'
LIC = 'https://creativecommons.org/licenses/by/4.0/'; LICENSOR = 'https://lemonindex.com/images/'
# 11-11 (Elijah approved): factory press-photo style with the real engine covers and their lettering (covers_test/, LOW). picks.json:
# engine id -> cutout file that passed the review (null = left without a picture; see the needs-medium list)
COV = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\engine images test\covers_test\cut'
PICK = {e: (COV, f) for e, f in json.load(open(os.path.join(COV, '..', 'picks.json'), encoding='utf-8')).items()}
D = json.load(open(os.path.join(HERE, 'data', 'supercar_engines.json'), encoding='utf-8'))['engines']
def xmp(title):
    return f'''<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
 xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/" xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" xmlns:plus="http://ns.useplus.org/ldf/xmp/1.0/">
<Iptc4xmpExt:DigitalSourceType>http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia</Iptc4xmpExt:DigitalSourceType>
<dc:title><rdf:Alt><rdf:li xml:lang="x-default">{title}</rdf:li></rdf:Alt></dc:title>
<dc:description><rdf:Alt><rdf:li xml:lang="x-default">{title}. AI-generated illustration, not a photo of a specific engine.</rdf:li></rdf:Alt></dc:description>
<dc:rights><rdf:Alt><rdf:li xml:lang="x-default">The Lemon Index (lemonindex.com), CC BY 4.0</rdf:li></rdf:Alt></dc:rights>
<photoshop:Credit>The Lemon Index (lemonindex.com)</photoshop:Credit>
<xmpRights:Marked>True</xmpRights:Marked><xmpRights:WebStatement>{LIC}</xmpRights:WebStatement>
<plus:Licensor><rdf:Seq><rdf:li rdf:parseType="Resource"><plus:LicensorURL>{LICENSOR}</plus:LicensorURL></rdf:li></rdf:Seq></plus:Licensor>
</rdf:Description></rdf:RDF></x:xmpmeta>
<?xpacket end="w"?>'''
import re, html
P = {}
for e, (src, fn) in PICK.items():
    if not fn or e not in D: continue
    d = D[e]; kind = re.sub(r'[^a-z0-9]+', '-', f'{d["asp"].split(" plug")[0].split(",")[0]} {d["layout"]}'.lower().replace('°', '')).strip('-')
    slug = f'{e}-{kind}-engine'.replace('--', '-')
    title = html.unescape(f'{d["name"]} {d["size"]} {d["layout"]} engine (illustration)')
    im = Image.open(os.path.join(src, fn)).convert('RGBA'); im = im.resize((1200, round(im.size[1] * 1200 / im.size[0])), Image.LANCZOS)
    dst = os.path.join(HERE, 'assets', 'engines', slug + '.webp'); q = 80
    while True:
        im.save(dst, 'WEBP', quality=q, method=6, exact=False, xmp=xmp(title).encode('utf-8'))
        if os.path.getsize(dst) < 150_000 or q <= 50: break
        q -= 6
    back = Image.open(dst).info.get('xmp', b'')
    assert b'trainedAlgorithmicMedia' in (back if isinstance(back, bytes) else back.encode()), 'XMP not embedded'
    sm = im.resize((640, round(im.size[1] * 640 / im.size[0])), Image.LANCZOS); sm.save(dst[:-5] + '-640.webp', 'WEBP', quality=78, method=6, xmp=xmp(title).encode('utf-8'))
    P[e] = dict(src=f'/assets/engines/{slug}.webp', w=im.size[0], h=im.size[1], ai=True, title=title, bytes=os.path.getsize(dst))
    print(e, slug, os.path.getsize(dst) // 1024, 'KB')
json.dump(P, open(os.path.join(HERE, 'data', 'supercar_engine_photos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(P), 'images')
