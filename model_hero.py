# 11-19 model page top, v2 (Elijah, on the Acura RDX page: "make header bigger and make the car image higher up and a little bigger ...
# remove some of the text that's overwhelming ... the score gauge right below the image and make it bigger ... bad and good on the
# sides, average at the top ... big text saying this car's score and right under it 100 is average, then straight to the year by year
# thing, then all the compact cards").
# Runs on the finished page after the date hash (MH_HOOK in page()), so restyling never moves a page's date.
#   name (big) -> car photo -> gauge (0-200 so 100 sits at the top: Good left, Average top, Bad right) -> score + "100 is average"
#   -> "Year by year" (the year explorer's year, chips and bars) -> the cards.
# Dropped from the top: the answer line ("Is it reliable? Mostly...") and the verdict block (the Questions card still answers it,
# and the bars + year pages carry fewest / most), and the hero Share button (the page's end has one).
import math, re as _mh_re
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
    return body[:i] + str(s) + rest
