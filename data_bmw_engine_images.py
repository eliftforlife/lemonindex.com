# Our own BMW engine illustrations (AI-generated, Elijah 11-10) -> optimized WebP with honest, machine-readable metadata.
# exiftool isn't installed on this PC, so the XMP packet is written with Pillow (already installed): IPTC Digital Source Type =
# trainedAlgorithmicMedia (Google reads this to label AI images), plus Credit, Copyright Notice, Web Statement of Rights (CC BY 4.0)
# and Licensor URL (/images/). Updates data/bmw_engine_photos.json.   py -X utf8 data_bmw_engine_images.py
import json, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\engine images test'
IMG = {'N54': ('bmw_n54_medium.png', 'bmw-n54-twin-turbo-inline-6-engine', 'BMW N54 3.0-liter twin-turbo inline-6 engine (illustration)'),
       'N55': ('bmw_n55_medium.png', 'bmw-n55-turbo-inline-6-engine', 'BMW N55 3.0-liter single-turbo inline-6 engine (illustration)'),
       'B58': ('bmw_b58_medium.png', 'bmw-b58-turbo-inline-6-engine', 'BMW B58 3.0-liter turbo inline-6 engine (illustration)'),
       'N63': ('bmw_n63_medium.png', 'bmw-n63-twin-turbo-v8-engine', 'BMW N63 4.4-liter twin-turbo V8 engine (illustration)')}
# not used: bmw_s54_medium.png (anatomically wrong); bmw_m30_medium.png (no M30 page: its cars predate our data)
LIC = 'https://creativecommons.org/licenses/by/4.0/'; LICENSOR = 'https://lemonindex.com/images/'
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
P = json.load(open(os.path.join(HERE, 'data', 'bmw_engine_photos.json'), encoding='utf-8'))
for f in os.listdir(os.path.join(HERE, 'assets', 'engines')):
    if f.endswith('-ai.webp'): os.remove(os.path.join(HERE, 'assets', 'engines', f))
for code, (fn, slug, title) in IMG.items():
    im = Image.open(os.path.join(SRC, fn)).convert('RGB'); im = im.resize((1200, round(im.size[1] * 1200 / im.size[0])), Image.LANCZOS)
    dst = os.path.join(HERE, 'assets', 'engines', slug + '.webp'); q = 80
    while True:
        im.save(dst, 'WEBP', quality=q, method=6, xmp=xmp(title).encode('utf-8'))
        if os.path.getsize(dst) < 150_000 or q <= 50: break
        q -= 6
    back = Image.open(dst).info.get('xmp', b'')
    assert b'trainedAlgorithmicMedia' in (back if isinstance(back, bytes) else back.encode()), 'XMP not embedded'
    P[code] = dict(src=f'/assets/engines/{slug}.webp', w=im.size[0], h=im.size[1], ai=True, title=title, bytes=os.path.getsize(dst))
    print(code, dst, os.path.getsize(dst) // 1024, 'KB, XMP ok')
json.dump(P, open(os.path.join(HERE, 'data', 'bmw_engine_photos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
