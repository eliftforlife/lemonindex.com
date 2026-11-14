# 11-13 (Elijah via the image pipeline): our AI illustrations for the engine pages that had no picture (everyday VIN-matched engines, HD
# diesels, the 2.7 EcoBoost, EA888, FA24F; the GM LT5 / Porsche MA1 / Maserati Nettuno go through SCP in supercar_engine_pages.py).
# data/ai_engine_photos.json {page id: {src, w, h, ai, title, bytes}}, written by '3 Lemon Index/car images test/year images/engine_run.py'
# (gpt-image-2 LOW, vision QA for layout / induction / no text, WebP with the same IPTC trainedAlgorithmicMedia XMP as the supercar ones).
# exec'd by hd_pages.py (the first engine-page builder); vin_engine_pages.py, engine_more.py, all_engines.py and bmw_pages.py (/images/,
# image sitemap) read AIE / AIE_IMGS. A page with no entry keeps no picture.
AIE = _load('data/ai_engine_photos.json') if os.path.exists('data/ai_engine_photos.json') else {}
AIE_IMGS = []   # (page path, photo) for /images/ and the image sitemap
_AIE_CCBY = 'https://creativecommons.org/licenses/by/4.0/'
_AIE_NOTE = ('Illustration (AI-generated) in the style of a factory press photo, not a photo of a specific engine; brand names belong to their owners. '
             f'Free to use under <a href="{_AIE_CCBY}" rel="noopener license">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>')
def aie_photo(path): return AIE.get(path.strip('/').split('/')[-1])
def aie_vis(path, name, lay):
    """the hero figure (same markup and (i) disclosure as the supercar engine pages), '' when the engine has no illustration"""
    ph = aie_photo(path)
    if not ph: return ''
    if (path, ph) not in AIE_IMGS: AIE_IMGS.append((path, ph))
    return (f'<figure class="engph"><img src="{E(ph["src"])}"{rset(ph["src"], "(max-width: 700px) 100vw, 680px")} width="{ph["w"]}" height="{ph["h"]}" '
            f'alt="Illustration of the {E(name)} ({E(lay)}) engine" loading="eager">' + YSL.info(_AIE_NOTE) + '</figure>')
def aie_ld(path):
    ph = aie_photo(path)
    if not ph: return []
    return [{"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": BASE + ph['src'], "url": BASE + ph['src'], "name": ph['title'],
             "description": f'{ph["title"]}. AI-generated illustration, not a photo of a specific engine.', "width": ph['w'], "height": ph['h'], "encodingFormat": "image/webp",
             "license": _AIE_CCBY, "acquireLicensePage": BASE + '/images/', "creditText": "The Lemon Index", "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE + '/'},
             "copyrightNotice": "The Lemon Index (lemonindex.com), CC BY 4.0", "isAccessibleForFree": True}]
