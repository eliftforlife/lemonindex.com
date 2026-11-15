# 11-14 growth plan 5b: "Embed this chart" on every model page and model-year page, a per-model embed page for each, and the /embed/ how-to.
# Run by build.py with exec() in two phases, so everything build.py defines is in scope:
#   EMBX = 'hooks'  (before the model/year pages): EMX_BTN(f, y) = the button + copy panel; EMX_HAS = models with an embed page
#   EMBX = 'pages'  (after the stats pages): docs/embed/cars/<model>/ (one tiny standalone chart per model) + the /embed/ how-to page
# The embed pages are plain HTML + inline CSS, no fonts, no analytics, no ads; assets/emb.js (under 1 KB) reads ?y=2016 (highlights that
# year) and ?theme=light|dark (else the reader's system setting). Every number on them is the model page's own Lemon Index by model year.
# The panel is left out of the page's content hash (build.py _chash), so adding it doesn't redate ~4,000 car pages.
import os as _os, json as _json, re as _re

if EMBX == 'hooks':
    EMX_V = '1114'
    def _emx_rows(f):
        """the scored model years, newest first (the same years and numbers as the model page's chart)"""
        return sorted((v for v in f['years'] if v['ok']), key=lambda v: -v['y'])
    EMX_HAS = {f['id'] for f in YEARS if len(_emx_rows(f)) >= 2}
    def EMX_H(f): return 215 + 23 * len(_emx_rows(f))   # iframe height: title + rows + credit line, no inner scroll
    def EMX_SNIP(f, y=None, theme=''):
        q = '&'.join(x for x in ((f'y={y}' if y else ''), (f'theme={theme}' if theme else '')) if x)
        src = f'{BASE}/embed/cars/{f["id"]}/' + (f'?{q}' if q else '')
        cred = BASE + CARU(f, y)
        what = f'{y} {f["name"]} reliability' if y else f'{f["name"]} reliability by year'
        return (f'<iframe src="{src}" title="{E(f["name"])} reliability by model year (The Lemon Index)" width="100%" height="{EMX_H(f)}" '
                f'style="border:0;max-width:720px" loading="lazy"></iframe>'
                f'<p style="font-size:13px;margin:4px 0 0">Data: <a href="{cred}">Lemon Index</a> ({E(what)})</p>')
    def EMX_BTN(f, y=None):
        if f['id'] not in EMX_HAS: return ''
        sn = {t: EMX_SNIP(f, y, t) for t in ('', 'light', 'dark')}
        prev = f'/embed/cars/{f["id"]}/' + (f'?y={y}' if y else '')
        thm = ''.join(f'<label><input type="radio" name="emx-t-{f["id"]}" value="{t}"{" checked" if not t else ""} data-snip="{E(s)}"> {lab}</label>'
                      for (t, s), lab in zip(sn.items(), ('Auto', 'Light', 'Dark')))
        return (f'<details class="emx"><summary>Embed this chart</summary><link rel="stylesheet" href="/assets/emx.css?v={EMX_V}">'
                f'<div class="emx-p"><p class="emx-h">Put this chart on your site, blog or forum. Free, with the credit line built in'
                + (f'; the {y} bar is highlighted' if y else '') + '.</p>'
                f'<fieldset class="emx-t"><legend>Colors</legend>{thm}</fieldset>'
                f'<div class="cpy"><div class="cpy-r"><code>{E(sn[""])}</code><button type="button" class="btn btn-ghost cpy-b" data-copy="{E(sn[""])}">Copy</button></div></div>'
                f'<p class="emx-l"><a href="{prev}" target="_blank" rel="noopener">Preview</a> · <a href="/embed/">How to embed (blogs, forums, videos)</a></p></div>'
                f'<script src="/assets/emx.js?v={EMX_V}" defer></script></details>')

elif EMBX == 'pages':
    _EMX_CSS = (':root{color-scheme:light dark;--bg:#fff;--ink:#1d1d1f;--mu:#6e6e73;--ln:#d2d2d7;--tr:#ececf0;--gd:#1f9d55;--md:#8e8e93;--bd:#e8141c;--na:#c7c7cc;--hl:#fff6c2}'
                '@media (prefers-color-scheme:dark){:root:not(.light){--bg:#161618;--ink:#f5f5f7;--mu:#a1a1a6;--ln:#3a3a3c;--tr:#2c2c2e;--gd:#30c06a;--md:#8e8e93;--bd:#ff453a;--na:#48484a;--hl:#3d3517}}'
                ':root.dark{--bg:#161618;--ink:#f5f5f7;--mu:#a1a1a6;--ln:#3a3a3c;--tr:#2c2c2e;--gd:#30c06a;--md:#8e8e93;--bd:#ff453a;--na:#48484a;--hl:#3d3517}'
                'body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.35 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}'
                'main{padding:14px 16px 12px}h1{font-size:18px;line-height:1.2;margin:0 0 2px;letter-spacing:-.01em}p{margin:0}.sub{color:var(--mu);font-size:12.5px;margin:0 0 10px}'
                '.r{display:grid;grid-template-columns:3.2em minmax(0,1fr) 2.6em;gap:8px;align-items:center;height:23px;border-radius:5px;padding:0 4px;margin:0 -4px}'
                '.r.cur{background:var(--hl)}.r span{font-size:12.5px;color:var(--mu);font-variant-numeric:tabular-nums}.r.cur span{color:var(--ink);font-weight:700}'
                '.r i{position:relative;display:block;height:13px;background:var(--tr);border-radius:4px}.r em{display:block;height:100%;border-radius:4px;background:var(--md)}'
                '.r.good em{background:var(--gd)}.r.bad em{background:var(--bd)}.r.na em{background:var(--na)}.r s{position:absolute;top:-3px;bottom:-3px;width:0;border-left:1.5px dashed var(--ink);opacity:.55}'
                '.r b{font-size:12.5px;text-align:right;font-variant-numeric:tabular-nums}.k{color:var(--mu);font-size:11.5px;margin:8px 0 0}'
                '.cr{margin:8px 0 0;padding-top:8px;border-top:1px solid var(--ln);font-size:12.5px;color:var(--mu);display:flex;flex-wrap:wrap;gap:2px 10px;justify-content:space-between}'
                '.cr a{color:var(--ink);font-weight:700}.cr b{color:var(--ink)}')
    _EMX_CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'self'; base-uri 'none'; form-action 'none'"
    def _emx_page(f):
        rows = _emx_rows(f); mx = max(120, max(v['li'] for v in rows) * 1.08)
        bars = ''.join(f'<div class="r {CLS(v)}" id="y{v["y"]}"><span>{v["y"]}</span><i><em style="width:{min(100, v["li"] / mx * 100):.1f}%"></em>'
                       f'<s style="left:{100 / mx * 100:.1f}%"></s></i><b>{v["li"]}</b></div>' for v in rows)
        part = any(v.get('early') for v in rows)
        u = BASE + CARU(f)
        return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<meta http-equiv="Content-Security-Policy" content="{_EMX_CSP}"><meta name="robots" content="noindex"><meta name="referrer" content="strict-origin-when-cross-origin">'
                f'<title>{E(f["name"])} reliability by model year | The Lemon Index</title><style>{_EMX_CSS}</style></head><body><main>'
                f'<h1>{E(f["name"])} reliability by model year</h1><p class="sub">Owner complaints per car sold, 100 = the average car of the same year. Shorter is better.</p>'
                f'{bars}<p class="k">Green = fewer complaints than average, red = more, gray = about average'
                + (' or too new to score fully' if part else '') + '. Dashed line = 100.</p>'
                f'<p class="cr"><span>Data: <a href="{u}" target="_blank" rel="noopener">Lemon Index</a></span><span>From NHTSA owner complaints · CC BY 4.0</span></p>'
                f'</main><script src="/assets/emb.js?v={EMX_V}" defer></script></body></html>')
    _n = 0
    for f in YEARS:
        if f['id'] not in EMX_HAS: continue
        d = f'{OUT}/embed/cars/{f["id"]}'; _os.makedirs(d, exist_ok=True)
        h = _emx_page(f); p = f'{d}/index.html'
        if not _os.path.exists(p) or open(p, encoding='utf-8').read() != h: open(p, 'w', encoding='utf-8').write(h)
        _n += 1
    print('embed pages (per model):', _n)

    # ---- /embed/: the how-to page, with a picker that writes the code for any model or model year
    _EMX_PICK = sorted(([f['name'], f['id'], [v['y'] for v in _emx_rows(f)], EMX_H(f)] for f in YEARS if f['id'] in EMX_HAS), key=lambda r: r[0])
    _ex = FY.get('honda-civic') or YEARS[0]
    _EMX_J = _json.dumps({'base': BASE, 'def': _ex['id'], 'cars': _EMX_PICK}, ensure_ascii=False, separators=(',', ':')).replace('</', '<' + chr(92) + '/')
    def _li(items): return '<ul class="ab-l">' + ''.join(f'<li>{x}</li>' for x in items) + '</ul>'
    _sec = lambda h, b: f'<section class="yc"><h2>{h}</h2>{b}</section>'
    body = ('<div class="advp abp emxp"><header class="advh1"><p class="ph-e"><a href="/press/">Press</a> · Free embeds</p><h1>Embed a Lemon Index chart.</h1>'
            f'<p class="ans">Every model we score has a free chart of its owner complaints by model year: {len(_EMX_PICK)} models. Paste one line of code into your site, blog or forum post. '
            'The numbers update when ours do, and the credit line is built in.</p></header>'
            f'<link rel="stylesheet" href="/assets/emx.css?v={EMX_V}">'
            '<section class="yc emx-gen" id="get"><h2>Get the code</h2>'
            '<div class="emx-f"><label><span>Car</span><select id="emx-m" aria-label="Car"></select></label>'
            '<label><span>Highlight a year</span><select id="emx-y" aria-label="Year to highlight"><option value="">None</option></select></label>'
            '<label><span>Colors</span><select id="emx-c" aria-label="Colors"><option value="">Auto (reader&#39;s setting)</option><option value="light">Light</option><option value="dark">Dark</option></select></label></div>'
            f'<div class="cpy"><div class="cpy-r"><code id="emx-code">{E(EMX_SNIP(_ex))}</code><button type="button" class="btn btn-ghost cpy-b" id="emx-copy" data-copy="{E(EMX_SNIP(_ex))}">Copy</button></div></div>'
            f'<p class="emx-l"><a id="emx-prev" href="/embed/cars/{_ex["id"]}/" target="_blank" rel="noopener">Preview the chart</a> · or use the <b>Embed this chart</b> button under the year chart on any car page.</p>'
            f'<script type="application/json" id="emx-data">{_json.dumps({"base": BASE, "def": _ex["id"], "cars": _EMX_PICK}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}</script></section>'
            '<div class="ygrid">'
            + _sec('On a website or blog', _li(['<b>WordPress:</b> add a <i>Custom HTML</i> block and paste the code.', '<b>Squarespace:</b> add a <i>Code</i> block. <b>Wix:</b> <i>Embed code</i> → <i>Embed HTML</i>. <b>Ghost:</b> an <i>HTML</i> card.',
                                                 'The chart fills the column up to 720 px wide and works on phones. Keep the <q>Data: Lemon Index</q> line under it: that&#39;s the credit.',
                                                 'Sites that strip iframes (Substack, Medium): post a screenshot of the preview with a link to the car&#39;s page instead.']))
            + _sec('On a forum', _li(['Most car forums don&#39;t allow iframes. Open the preview, take a screenshot, and post it with the car page&#39;s link, e.g. '
                                      f'<q>Data: Lemon Index, {BASE}{CARU(_ex)}</q>.', 'Forums that allow HTML embeds (some XenForo and Discourse setups) take the code as is.']))
            + _sec('In a YouTube video', _li(['Open the preview full screen, pick Light or Dark to match your edit, and screen-record or screenshot it.',
                                              'Keep the <q>Data: Lemon Index</q> line in frame, or say it, and put the car page&#39;s link in your description.']))
            + _sec('The rules', _li(['Free for anyone under <a href="https://creativecommons.org/licenses/by/4.0/" rel="noopener license">CC BY 4.0</a>: credit <q>The Lemon Index (lemonindex.com)</q> with a link.',
                                     'Don&#39;t change the numbers or cut off the credit line.', 'The chart shows owner complaints per car sold. A complaint is an owner&#39;s report, not proof of a defect, and this is not a safety rating. '
                                     '<a href="/method/">How the index works</a>.']))
            + '</div>'
            + embed_block(EMB, list(EMB), 'Site-wide charts')
            + '<p class="yc-cap">Numbers on every chart come from NHTSA owner complaints and published U.S. sales. Reporters: see the <a href="/press/">press page</a> and the <a href="/stats/car-complaints/">car complaint statistics</a>.</p>'
            f'<script src="/assets/emx.js?v={EMX_V}" defer></script></div>')
    page('/embed/', 'Embed a Car Reliability Chart: Free for Blogs and Forums | The Lemon Index',
         f'Free car reliability charts to embed: owner complaints by model year for {len(_EMX_PICK)} models, with the credit built in. Copy the code for a blog, forum or video.', body,
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": "Embed a Lemon Index chart", "url": BASE + '/embed/'}])
    SEO_URLS.append('/embed/')
