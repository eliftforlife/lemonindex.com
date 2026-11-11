# 11-10 (Elijah): AI-generated year-by-year car illustrations + a "slide through every year" viewer.
# Data: data/ai_year_images.json  {model id: {year: {src, w, h, color, gen}}}  (images in assets/ai-cars/, made with gpt-image-2, checked by hand).
# Used by build.py: year_slider_html() on the model page, ai_year_html() on each year page. Generic: any model in the JSON gets both.
import json, html, os
E = lambda s: html.escape(str(s), quote=True)
BASE = 'https://lemonindex.com'
try: AIY = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ai_year_images.json'), encoding='utf-8'))
except FileNotFoundError: AIY = {}
# 11-11: the former 'No data yet' models (data/years_new.json, added one by one) get their generation's picture on every year page as
# soon as the page exists: data/ai_gen_images.json {model id: [[first year, last year, src, color, generation], ...]} (newer generation wins on overlap)
try:
    _D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    _GI = json.load(open(os.path.join(_D, 'ai_gen_images.json'), encoding='utf-8'))
    for _f in json.load(open(os.path.join(_D, 'years_new.json'), encoding='utf-8')):
        if _f['id'] in AIY or _f['id'] not in _GI: continue
        _m = {}
        for _v in _f['years']:
            _g = [g for g in _GI[_f['id']] if g[0] <= _v['y'] <= g[1]]
            if _g: _g = max(_g, key=lambda g: g[0]); _m[str(_v['y'])] = {'src': _g[2], 'w': 1000, 'h': 600, 'color': _g[3], 'gen': _g[4]}
        if _m: AIY[_f['id']] = _m
except FileNotFoundError: pass
LIC = 'https://creativecommons.org/licenses/by/4.0/'
NOTE = 'Illustration (AI-generated). Typical factory color of the era, not sales data. Free to use under <a href="' + LIC + '" rel="license noopener">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com).'

def has(fid):
    """True when the model page gets the year slider: its years show more than one picture (11-10: one image per generation for every
    model, so one-generation models keep their single hero)."""
    return len({v["src"] for v in (AIY.get(fid) or {}).values()}) > 1

# 11-10 (Elijah): one AI illustration per model (data/ai_model_images.json, assets/ai-models/): the model-page hero and the /cars/ grid
# use it instead of the Wikimedia photo. All on one 1000x600 canvas, car centered on a shared baseline, facing left.
try: AIM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ai_model_images.json'), encoding='utf-8'))
except FileNotFoundError: AIM = {}
# 11-10 (Elijah: swap every Wikimedia car photo that has an AI match): the 'No data yet' illustrations (data/new_models.json) also count
# for models we score without year pages (e.g. VW ID.4, Kia EV6), and slash ids map to their file names.
try:
    for _m in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'new_models.json'), encoding='utf-8')):
        if _m['slug'] not in AIM and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'ai-models', _m['slug'] + '.webp')):
            AIM[_m['slug']] = {'src': f"/assets/ai-models/{_m['slug']}.webp?v=1", 'w': 1000, 'h': 600, 'year': _m.get('year'), 'name': _m['name'], 'color': ''}
except FileNotFoundError: pass
for _sl, _fl in (('mercedes-benz-glk/glc', 'mercedes-benz-glk-glc'), ('mercedes-benz-m/gle', 'mercedes-benz-m-gle')):
    if _sl not in AIM and _fl in AIM: AIM[_sl] = AIM[_fl]
def model_img(fid): return AIM.get(fid)
def model_info_text(fid):
    m = AIM[fid]
    return (f'Illustration (AI-generated) of a {m["year"]} {E(m["name"])}. Free to use under <a href="{LIC}" rel="license noopener">CC BY 4.0</a>: '
            f'credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>')
def model_ld(fid):
    m = AIM[fid]
    return {"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": BASE + m['src'], "name": f'{m["year"]} {m["name"]} (illustration)',
            "description": f'AI-generated illustration of a {m["year"]} {m["name"]}' + (f' in {m["color"]}.' if m.get("color") else '.'), "width": m['w'], "height": m['h'],
            "license": LIC, "acquireLicensePage": BASE + '/images/', "creditText": "The Lemon Index",
            "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE}, "copyrightNotice": "The Lemon Index, CC BY 4.0"}
def model_hero_html(fid, name):
    """The model page's top image when it has no year slider ('' if no illustration)."""
    m = AIM.get(fid)
    if not m: return ''
    return (f'<link rel="stylesheet" href="/assets/yslider.css?v=6"><figure class="yph aiy aim"><img src="{m["src"]}" alt="{m["year"]} {E(name)}, illustration" '
            f'width="{m["w"]}" height="{m["h"]}" fetchpriority="high" decoding="async">' + info(model_info_text(fid)) + '</figure>'
            f'<script type="application/ld+json">{json.dumps(model_ld(fid))}</script>')

_IIN = [0]
def info(html_text):
    """11-10 (Elijah): image credit / AI disclosure behind a small 'i' button in the image's bottom-right corner (assets/imginfo.js).
    The text stays in the page (hidden until opened); ImageObject markup and alt text carry the same facts for machines."""
    _IIN[0] += 1; i = f'ii{_IIN[0]}'
    return (f'<button class="ii" type="button" aria-label="Image info" aria-expanded="false" aria-controls="{i}">i</button>'
            f'<div class="ii-pop" id="{i}" role="note" hidden>{html_text}</div>')

def _ld(fid, y, name, im):
    return {"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": BASE + im['src'], "name": f'{y} {name} (illustration)',
            "description": f'AI-generated illustration of a {y} {name}, {im["gen"]}' + (f', in {im["color"]}.' if im.get("color") else '.'), "width": im['w'], "height": im['h'],
            "license": LIC, "acquireLicensePage": BASE + '/images/', "creditText": "The Lemon Index",
            "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE}, "copyrightNotice": "The Lemon Index, CC BY 4.0"}

def ai_src(fid, y): return (AIY.get(fid, {}).get(str(y)) or {}).get('src')

def ai_year_html(fid, y, name, hero=False):
    """The year's illustration ('' if none). 11-10 (Elijah): where one exists it is the page's only car image (no Commons photo); hero=True loads it first."""
    im = AIY.get(fid, {}).get(str(y))
    if not im: return ''
    ld = 'fetchpriority="high" decoding="async"' if hero else 'loading="lazy" decoding="async"'
    return (f'<link rel="stylesheet" href="/assets/yslider.css?v=6"><figure class="yph aiy{' aim' if im['h'] == 600 else ''}"><img src="{im["src"]}" alt="{y} {E(name)}, {E(im["gen"])}, illustration" width="{im["w"]}" height="{im["h"]}" {ld}>'
            + info(f'Illustration (AI-generated) of a {y} {E(name)}. {NOTE.split(". ", 1)[1]} <a href="/images/">Download and credit text</a>') + '</figure>'
            f'<script type="application/ld+json">{json.dumps(_ld(fid, y, name, im))}</script>')

def year_slider_html(fid, name, li=None, yt=None, pages=(), start=None, hero=False):
    """'Every <model>, year by year' section: a crossfading image stage + a range slider. li/yt = {year: score}; pages = years with a page."""
    ims = AIY.get(fid)
    if not ims: return ''
    ys = sorted(int(y) for y in ims)
    data = [{"y": y, "src": ims[str(y)]['src'], "gen": ims[str(y)]['gen'], "li": (li or {}).get(y), "yt": (yt or {}).get(y),
             "url": f'/cars/{fid}/{y}/' if y in pages else None} for y in ys]
    si = ys.index(start) if start in ys else 0; y0 = ys[si]   # 11-10 (Elijah): the hero slider opens on the page's best year
    first = ims[str(y0)]; short = name.split(' ', 1)[-1] if ' ' in name else name
    return (f'<link rel="stylesheet" href="/assets/yslider.css?v=6"><section class="ysl{' ysl-hero' if hero else ''}" id="every-year" aria-label="Every {E(short)}, year by year">'
            + ('' if hero else f'<h2>Every {E(short)}, year by year. <span class="h2s">Slide through {ys[0]} to {ys[-1]}.</span></h2>') +
            f'<div class="ysl-stage"><img class="on" src="{first["src"]}" alt="{y0} {E(name)} illustration" width="{first["w"]}" height="{first["h"]}" fetchpriority="{'high' if hero else 'low'}"><img alt="" width="{first["w"]}" height="{first["h"]}" aria-hidden="true">'
            f'<div class="ysl-yr"><b>{y0}</b><span class="ysl-gen">{E(first["gen"])}</span></div>'
            + info(f'Illustrations (AI-generated) of every {E(name)} model year. Typical factory color of the era, not sales data. Free to use under <a href="{LIC}" rel="license noopener">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com). <a href="/images/">Download and credit text</a>') + '</div>'
            + _info(data[si], start in ys) +
            f'<input class="ysl-range" type="range" min="0" max="{len(ys) - 1}" step="1" value="{si}" aria-label="Model year" aria-valuetext="{y0}">'
            f'<div class="ysl-ends"><span>{ys[0]}</span><span>{ys[-1]}</span></div>'

            f'<script type="application/json" class="ysl-data">{json.dumps({"name": name, "years": data, "best": y0 if start in ys else None})}</script></section>'
            f'<script src="/assets/yslider.js?v=4" defer></script>')

def _info(v, best):
    """The score row, filled for the starting year in the HTML itself so nothing shifts when yslider.js takes over (11-10: CLS)."""
    li = v.get('li'); cls = 'ysl-li' + (' na' if li is None else ' good' if li <= 80 else ' bad' if li >= 130 else '')
    lt = f'Lemon Index {li}' if li is not None else f'No Lemon Index for {v["y"]}'
    yt = f'<span class="ysl-yt">YouTube score {v["yt"]}</span>' if v.get('yt') is not None else '<span class="ysl-yt" hidden></span>'
    go = f'<a class="ysl-go" href="{v["url"]}">See the {v["y"]} report ›</a>' if v.get('url') else '<a class="ysl-go" href="#" hidden></a>'
    return (f'<div class="ysl-info"><span class="ysl-best"{"" if best else " hidden"}>Best year</span><span class="{cls}">{lt}</span>{yt}{go}</div>')

def yt_scores(fid):
    """{year: YouTube score} from data/yt_scores.json (the per-year YouTube rank data the site already shows)."""
    try: d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'yt_scores.json'), encoding='utf-8')).get(fid, {})
    except FileNotFoundError: return {}
    return {int(y): v['score'] for y, v in d.items() if isinstance(v, dict) and v.get('score') is not None and (v.get('videos') or 0) >= 3}
