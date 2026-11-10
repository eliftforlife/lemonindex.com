# 11-10 (Elijah): AI-generated year-by-year car illustrations + a "slide through every year" viewer.
# Data: data/ai_year_images.json  {model id: {year: {src, w, h, color, gen}}}  (images in assets/ai-cars/, made with gpt-image-2, checked by hand).
# Used by build.py: year_slider_html() on the model page, ai_year_html() on each year page. Generic: any model in the JSON gets both.
import json, html, os
E = lambda s: html.escape(str(s), quote=True)
BASE = 'https://lemonindex.com'
try: AIY = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ai_year_images.json'), encoding='utf-8'))
except FileNotFoundError: AIY = {}
LIC = 'https://creativecommons.org/licenses/by/4.0/'
NOTE = 'Illustration (AI-generated). Typical factory color of the era, not sales data. Free to use under <a href="' + LIC + '" rel="license noopener">CC BY 4.0</a>: credit The Lemon Index (lemonindex.com).'

def has(fid): return fid in AIY

def _ld(fid, y, name, im):
    return {"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": BASE + im['src'], "name": f'{y} {name} (illustration)',
            "description": f'AI-generated illustration of a {y} {name}, {im["gen"]}, in {im["color"]}.', "width": im['w'], "height": im['h'],
            "license": LIC, "acquireLicensePage": BASE + '/images/', "creditText": "The Lemon Index",
            "creator": {"@type": "Organization", "name": "The Lemon Index", "url": BASE}, "copyrightNotice": "The Lemon Index, CC BY 4.0"}

def ai_src(fid, y): return (AIY.get(fid, {}).get(str(y)) or {}).get('src')

def ai_year_html(fid, y, name, hero=False):
    """The year's illustration ('' if none). 11-10 (Elijah): where one exists it is the page's only car image (no Commons photo); hero=True loads it first."""
    im = AIY.get(fid, {}).get(str(y))
    if not im: return ''
    ld = 'fetchpriority="high" decoding="async"' if hero else 'loading="lazy" decoding="async"'
    return (f'<link rel="stylesheet" href="/assets/yslider.css?v=1"><figure class="yph aiy"><img src="{im["src"]}" alt="{y} {E(name)}, {E(im["gen"])}, illustration" width="{im["w"]}" height="{im["h"]}" {ld}>'
            f'<figcaption>Illustration (AI-generated) of a {y} {E(name)}. {NOTE.split(". ", 1)[1]}</figcaption></figure>'
            f'<script type="application/ld+json">{json.dumps(_ld(fid, y, name, im))}</script>')

def year_slider_html(fid, name, li=None, yt=None, pages=()):
    """'Every <model>, year by year' section: a crossfading image stage + a range slider. li/yt = {year: score}; pages = years with a page."""
    ims = AIY.get(fid)
    if not ims: return ''
    ys = sorted(int(y) for y in ims)
    data = [{"y": y, "src": ims[str(y)]['src'], "gen": ims[str(y)]['gen'], "li": (li or {}).get(y), "yt": (yt or {}).get(y),
             "url": f'/cars/{fid}/{y}/' if y in pages else None} for y in ys]
    first = ims[str(ys[0])]; short = name.split(' ', 1)[-1] if ' ' in name else name
    return (f'<link rel="stylesheet" href="/assets/yslider.css?v=1"><section class="ysl" id="every-year" aria-label="Every {E(short)}, year by year">'
            f'<h2>Every {E(short)}, year by year. <span class="h2s">Slide through {ys[0]} to {ys[-1]}.</span></h2>'
            f'<div class="ysl-stage"><img class="on" src="{first["src"]}" alt="{ys[0]} {E(name)} illustration" width="{first["w"]}" height="{first["h"]}" fetchpriority="low"><img alt="" width="{first["w"]}" height="{first["h"]}" aria-hidden="true">'
            f'<div class="ysl-yr"><b>{ys[0]}</b><span class="ysl-gen">{E(first["gen"])}</span></div></div>'
            f'<div class="ysl-info"><span class="ysl-li"></span><span class="ysl-yt"></span><a class="ysl-go" href="#"></a></div>'
            f'<input class="ysl-range" type="range" min="0" max="{len(ys) - 1}" step="1" value="0" aria-label="Model year" aria-valuetext="{ys[0]}">'
            f'<div class="ysl-ends"><span>{ys[0]}</span><span>{ys[-1]}</span></div>'
            f'<p class="yc-cap">{NOTE}</p>'
            f'<script type="application/json" class="ysl-data">{json.dumps({"name": name, "years": data})}</script></section>'
            f'<script src="/assets/yslider.js?v=1" defer></script>')

def yt_scores(fid):
    """{year: YouTube score} from data/yt_scores.json (the per-year YouTube rank data the site already shows)."""
    try: d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'yt_scores.json'), encoding='utf-8')).get(fid, {})
    except FileNotFoundError: return {}
    return {int(y): v['score'] for y, v in d.items() if isinstance(v, dict) and v.get('score') is not None and (v.get('videos') or 0) >= 3}
