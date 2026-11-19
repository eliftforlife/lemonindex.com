# 11-19 model page top, v2 (Elijah, on the Acura RDX page: "make header bigger and make the car image higher up and a little bigger ...
# remove some of the text that's overwhelming ... the score gauge right below the image and make it bigger ... bad and good on the
# sides, average at the top ... big text saying this car's score and right under it 100 is average, then straight to the year by year
# thing, then all the compact cards").
# Runs on the finished page after the date hash (MH_HOOK in page()), so restyling never moves a page's date.
#   name (big) -> car photo -> gauge (0-200 so 100 sits at the top: Good left, Average top, Bad right) -> score + "100 is average"
#   -> "Year by year" (the year explorer's year, chips and bars) -> the cards.
# Dropped from the top: the answer line ("Is it reliable? Mostly...") and the verdict block (the Questions card still answers it,
# and the bars + year pages carry fewest / most), and the hero Share button (the page's end has one).
import math, html as _html, re as _mh_re
from bs4 import BeautifulSoup as _MHS

_MH_PATH = _mh_re.compile(r'/cars/[a-z0-9-]+/')

def _mh_gauge(li, cls, label):
    """11-19 r2 (Elijah: "make the rainbow meter a bar instead that's the length of the car ... a line or needle where the car lands"):
    one bar under the photo, 0 to 200 so 100 sits in the middle. Green under 85, gray 85-115, red over 115 (band()); past 200 pegs."""
    p = min(max(li, 0), 200) / 2
    return (f'<figure class="mh-bar {cls}" data-gauge style="--p:{p:.1f}%" aria-label="{label}">'
            f'<div class="mh-track" aria-hidden="true"><i class="mh-g"></i><i class="mh-m"></i><i class="mh-r"></i><span class="mh-pin"></span></div>'
            f'<div class="mh-labs" aria-hidden="true"><span class="mh-good">Good</span><span class="mh-avg">Average</span><span class="mh-bad">Bad</span></div>'
            f'<figcaption><b>{li}</b><span>100 is average</span></figcaption></figure>')

MH_CSS = '''<style id="mh-css">
.tbl .tb-hero.mh { display: flex; flex-direction: column; align-items: stretch; }
.tbl .tb-hero.mh .yct-h1 { margin-top: 4px; line-height: .98; }
.tbl .tb-hero.mh .yct-h1 .yct-big { font-size: clamp(46px, 13vw, 76px); letter-spacing: -.035em; overflow-wrap: anywhere; }
.tbl .tb-hero.mh .yct-h1 .yct-sw { font-size: clamp(17px, 4.6vw, 22px); margin-top: .35em; }
.tbl .tb-hero.mh .tb-img { margin: 8px 0 0 !important; }
.tbl .tb-hero.mh .yx { max-width: 820px; gap: 4px; }
.tbl .tb-hero.mh .yx-stage { width: min(calc(100% + 24px), 720px); margin: -30px auto 0; }
@media (max-width: 699px) { .tbl .tb-hero.mh .yx-stage { margin: -14vw -12px 0; } }
.tbl .tb-hero.mh .yx-stage img { mix-blend-mode: multiply; }   /* the photos' white backdrop pulls up under the title without covering it */
.mh-score { width: 100%; max-width: 680px; margin: 10px auto 4px; }
.mh-bar { margin: 0; }
.mh-track { position: relative; display: flex; gap: 3px; height: 16px; margin: 22px 0 0; }
.mh-track i { display: block; height: 100%; }
.mh-g { flex: 0 0 calc(42.5% - 2px); background: #1a8f4c; border-radius: 8px 0 0 8px; }
.mh-m { flex: 0 0 calc(15% - 2px); background: #c9ccd1; }
.mh-r { flex: 1 1 auto; background: #e8141c; border-radius: 0 8px 8px 0; }
.mh-pin { position: absolute; top: -14px; bottom: -14px; left: 0; width: 5px; margin-left: -2.5px; border-radius: 3px; background: #1d1d1f;
  box-shadow: 0 0 0 2.5px #fff; transition: left 1.2s cubic-bezier(.25, 1.25, .45, 1); }
.mh-pin::before { content: ""; position: absolute; left: 50%; top: -9px; width: 16px; height: 16px; margin-left: -8px; border-radius: 50%;
  background: #ffd400; border: 4px solid #1d1d1f; box-sizing: border-box; }
.mh-bar.in .mh-pin { left: var(--p); }
@media (prefers-reduced-motion: reduce) { .mh-pin { transition: none; } }
.mh-labs { position: relative; height: 22px; margin-top: 18px; font: 700 16px/1 var(--sys, Inter, sans-serif); }
.mh-labs span { position: absolute; top: 0; }
.mh-good { left: 0; color: #1a8f4c; }
.mh-avg { left: 50%; transform: translateX(-50%); color: #6e6e73; }
.mh-bad { right: 0; color: #d0121a; }
.mh-bar figcaption { margin-top: 18px; text-align: center; }
.mh-bar figcaption b { display: block; font: 800 clamp(64px, 18vw, 84px)/.95 var(--sys, Archivo, Inter, sans-serif); letter-spacing: -.04em; font-variant-numeric: tabular-nums; color: var(--ink); }
.mh-bar.good figcaption b { color: var(--good); }
.mh-bar.bad figcaption b { color: var(--red); }
.mh-bar figcaption span { display: block; margin-top: 6px; font-size: 17px; font-weight: 600; color: var(--mute); }
.tbl .tb-hero.mh > .ycn-wide, .tbl .tb-hero.mh > .cpl-acts { display: none; }
/* r3 (Elijah, MDX screenshot): no photo arrows / year strip; the "Every year" list (Lemon Index + YouTube rank per year) sits under the score.
   Hidden, not removed: ycar.js still binds to them, and the photo keeps its default year. */
.tbl .tb-hero.mh .yx-sp, .tbl .tb-hero.mh .yx-sn, .tbl .tb-hero.mh .yx-yr, .tbl .tb-hero.mh .yx-info, .tbl .tb-hero.mh .yx-strip, .tbl .tb-hero.mh .yx-ends { display: none !important; }
.mh-years { width: 100%; max-width: 760px; margin: 4px auto 0; text-align: left; box-sizing: border-box; }
.mh-years .yyears { margin: 0; }
.mh-years .yy-ch > h2 { margin-top: 0; }
.tbl .tb-hero.mh .yx-stage + .mh-score { margin-bottom: 0; }
</style>'''

def _mh_take_years(body, start):
    """Cut the page's 'Every year' list (section#years) out of the body after `start`; returns (body, html or '')."""
    k = body.find('<section class="yyears noph" id="years">', start)
    if k < 0: return body, ''
    depth, p = 0, k
    for m in _mh_re.finditer(r'<section\b|</section>', body[k:]):
        depth += 1 if m.group(0) == '<section' else -1
        if depth == 0: p = k + m.end(); break
    else: return body, ''
    return body[:k] + body[p:], body[k:p]

def MH_HOOK(path, body):
    if not _MH_PATH.fullmatch(path) or 'tb-hero yx-hero' not in body: return body
    i = body.find('<section class="ph tb-hero yx-hero'); j = body.find('<div class="tbx"', i)
    if i < 0 or j < 0: return body
    s = _MHS(body[i:j], 'html.parser'); hero = s.section
    fig = hero.select_one('div.yhero figure.gauge'); img = hero.select_one('div.tb-img'); h1 = hero.find('h1')
    if fig is None or img is None or h1 is None: return body
    m = _mh_re.match(r'Lemon Index (\d+)', fig.get('aria-label', ''))
    if not m: return body
    cls = next((c for c in fig.get('class', []) if c in ('good', 'mid', 'bad')), 'mid')
    rest, years = _mh_take_years(body[j:], 0)
    rest, shr = _mh_acts(rest)
    score = _MHS(f'<div class="mh-score">{_mh_gauge(int(m.group(1)), cls, fig["aria-label"])}</div>'
                 + (f'<div class="mh-years">{years}</div>' if years else ''), 'html.parser')
    hero.select_one('div.yhero').decompose()
    for x in hero.select('p.tb-ans'): x.decompose()
    h1.insert_after(img.extract())
    stage = img.select_one('.yx-stage')
    if stage is not None: stage.insert_after(score)
    else: img.insert_after(score)
    hero['class'] = hero.get('class', []) + ['mh']
    hero.insert(0, _MHS(MH_CSS, 'html.parser'))
    if shr:
        hero.insert(1, _MHS(f'<button type="button" class="mh-share" data-share="{shr.replace(chr(38), "&amp;").replace(chr(34), "&quot;")}" aria-label="Share this page" title="Share">{_MH_SHARE_SVG}</button>', 'html.parser'))
    return body[:i] + str(s) + rest

# 11-19 r4 (Elijah, MDX phone screenshots): the recall-email, "Share your take" and Compare boxes become three small tiles side by side
# (a tap opens that one full width under the row), and the "Know someone shopping for a used car?" row becomes a share icon in the hero.
MH_ACTS_CSS = '''<style id="mh-acts-css">
.tbl .tb-hero.mh { position: relative; }
.tbl .tb-hero.mh .yct-h1 { padding-right: 46px; }
.mh-share { position: absolute; top: 6px; right: 0; z-index: 2; display: grid; place-items: center; width: 42px; height: 42px; padding: 0; border: 0;
  border-radius: 50%; background: #f5f5f7; color: #1d1d1f; cursor: pointer; }
.mh-share:hover { background: #ececf0; } .mh-share:focus-visible { outline: 3px solid var(--lemon, #ffd400); outline-offset: 2px; }
.mh-share svg { width: 21px; height: 21px; }
.mh-acts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-auto-flow: row dense; gap: 8px; max-width: 760px; margin: 24px auto 0; }
.mh-acts > section { margin: 0 !important; padding: 0 !important; min-width: 0; max-width: none; }
.mh-acts .rla, .mh-acts .cpl { margin: 0 !important; }
.mh-acts .opn-share { margin: 0; display: block; }
.mh-acts .rla-tg, .mh-acts .opn-open, .mh-acts #p-compare details > summary {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; width: 100%; max-width: none; height: 100%;
  min-height: 82px; padding: 12px 6px !important; box-sizing: border-box; border-radius: 16px; text-align: center; }
.mh-acts #p-compare, .mh-acts #p-compare .cpl, .mh-acts #p-compare details, .mh-acts .rla-sec, .mh-acts .rla, .mh-acts .opn-share { height: 100%; }
.mh-acts .rla-tg .rla-ar, .mh-acts .opn-open .cpl-ar, .mh-acts #p-compare summary .cpl-ar { display: none; }
.mh-acts .rla-tg .cpl-i, .mh-acts .opn-open .cpl-i, .mh-acts #p-compare summary .cpl-i { width: 26px; height: 26px; margin: 0; }
.mh-acts .rla-tg span, .mh-acts .opn-open span, .mh-acts #p-compare summary span { flex: none; display: block; text-align: center; }
.mh-acts .opn-open span, .mh-acts #p-compare summary span, .mh-acts .rla-tg span { line-height: 1.2; }
.mh-acts .opn-open b, .mh-acts #p-compare summary b { display: block; font-size: 14px; line-height: 1.2; }
.mh-acts > #p-compare details[open] > summary b, .mh-acts > .rla-sec:has(.rla-open) .rla-tg span::after { font-size: 16px; }
.mh-acts .rla-tg span { font-size: 0; }
.mh-acts .rla-tg span::after { content: "Recall alerts"; font-size: 14px; font-weight: 700; line-height: 1.2; letter-spacing: -.01em; }
/* an open tile takes the whole row (the other two stay tiles) */
.mh-acts > .rla-sec:has(.rla-open), .mh-acts > .opn:has(.opn-f:not([hidden])), .mh-acts > .opn:has(.opn-h:not([hidden])),
.mh-acts > #p-compare:has(details[open]) { grid-column: 1 / -1; }
.mh-acts > .rla-sec:has(.rla-open) .rla-tg, .mh-acts > #p-compare details[open] > summary {
  flex-direction: row; justify-content: flex-start; gap: 12px; min-height: 0; height: auto; padding: 10px 16px !important; text-align: left; }
.mh-acts > .rla-sec:has(.rla-open) .rla-tg .rla-ar, .mh-acts > #p-compare details[open] .cpl-ar { display: block; margin-left: auto; }
.mh-acts > .rla-sec:has(.rla-open), .mh-acts > .rla-sec:has(.rla-open) .rla, .mh-acts > #p-compare:has(details[open]),
.mh-acts > #p-compare:has(details[open]) .cpl, .mh-acts > #p-compare details[open] { height: auto; }
.mh-acts > .opn:has(.opn-h:not([hidden])) .opn-open { flex-direction: row; min-height: 0; height: auto; padding: 10px 16px !important; }
.mh-acts > .opn:has(.opn-h:not([hidden])) .opn-share { height: auto; margin-top: 8px; }
</style>'''

def _mh_block(body, k, tag='div'):
    """end index of the <tag> element that starts at k (depth-matched), or -1"""
    depth = 0
    for m in _mh_re.finditer(rf'<{tag}\b|</{tag}>', body[k:]):
        depth += 1 if m.group(0) != f'</{tag}>' else -1
        if depth == 0: return k + m.end()
    return -1

_MH_SHARE_SVG = '<svg aria-hidden="true" focusable="false"><use href="/assets/ic.svg?v=1#share"></use></svg>'

def _mh_acts(rest):
    """returns (rest, share text or ''): the recall / opinions / compare boxes as one tile row, the share row cut out"""
    g = rest.find('<div class="cpl-grp cpl-g3">'); r = rest.find('<div class="cpl-grp cpl-rel cpl-ins">', g)
    if g < 0 or r < 0: return rest, ''
    e = _mh_block(rest, r)
    if e < 0: return rest, ''
    s = _MHS(rest[g:e], 'html.parser')
    rla, opn, cmp_ = s.select_one('section.rla-sec'), s.select_one('section#opinions'), s.select_one('section#p-compare')
    if not (rla and opn and cmp_): return rest, ''
    shr = ''
    pend = s.select_one('div.pend')
    if pend is not None:
        b = pend.select_one('[data-share]')
        if b is not None and 'Know someone shopping' in b.get_text():
            shr = b['data-share']; (b.find_parent('div', class_='cpl') or b).decompose()
            if not pend.find(True): pend.decompose()
    lab = opn.select_one('.opn-open b')
    if lab is not None: lab.string = 'Share your take'
    g3 = s.select_one('div.cpl-g3')
    acts = s.new_tag('div', attrs={'class': 'mh-acts'})
    g3.insert_before(acts)
    for x in (rla, opn, cmp_): acts.append(x.extract())
    for grp in s.select('div.cpl-g3, div.cpl-rel'):
        if not grp.find(True): grp.decompose()
    rest = rest[:g] + MH_ACTS_CSS + str(s) + rest[e:]
    if not shr:   # page() turns the page's last share line into the end "Know someone shopping" box later; take it here instead
        sm = [m for m in _mh_re.finditer(r'<p class="shline">.*?</p>', rest, _mh_re.S) if 'Know someone shopping' in m.group(0)]
        d = _mh_re.search(r'data-share="([^"]*)"', sm[-1].group(0)) if sm else None
        if d: shr = _html.unescape(d.group(1)); rest = rest[:sm[-1].start()] + rest[sm[-1].end():]
    return rest, shr
