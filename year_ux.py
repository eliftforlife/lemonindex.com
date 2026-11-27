# 11-25 year page top, v2 (Elijah's review of the go-live screens, /cars/toyota-corolla/2016/ on his phone). exec'd by build.py;
# YUX_HOOK(path, doc) runs last in page(), after the date hash, so none of this moves a page's date. Styles: assets/yux.css, assets/yux.js.
#   1. Heart + share sit UNDER the title on phones (CSS only: saved.js still draws them inside the H1).
#   2. H1 = the car name big + one small keyword line in the same H1 ("Problems, recalls and years to avoid"), so the heading still
#      carries the search words ("2016 toyota corolla problems") while the eye reads just the name. The <title> is unchanged.
#   3. No prev / next year arrows by the title (the years list and swipe on the photo still move between years).
#   4. "Better years to buy" + other generations: out of the hero, to the bottom of the page (before Similar cars / Related).
#   5. "All 26 years" + "Compare": one row of two equal buttons, full width, on every screen size (the desktop copy in the hero goes).
#   6. The score: the model page's single bar (model_hero.py _mh_gauge, 0-200, Good / Average / Bad) replaces the 0-300 rainbow gauge.
#   7. The lines under the score (owner complaints, EPA mpg) leave the page body and go into a "See where the score comes from" sheet.
#   8. Entry cards above the boxes, on years with a before-you-buy checklist (data/checklists.json from data_checklists.py):
#      "Can you afford this car?" + "Before-you-buy checklist". Behind CHECKLIST_ON until /afford/ and /checklist/ go live.
#   9. Less text: the verdict keeps its band word only (the Problems box names the top complaint), the generation line goes, and the
#      black "Too new: partial score" pill becomes one small line under the score (its explanation moves into the sheet).
import html as _yuh, json as _yuj, re as _yure
from bs4 import BeautifulSoup as _YUS

CHECKLIST_ON = False   # 11-25: /afford/ and /checklist/ aren't live yet; screenshots build with LEMON_CHECKLIST=1
import os as _yuos
if _yuos.environ.get('LEMON_CHECKLIST') == '1': CHECKLIST_ON = True

YUX_V = '2'
_YUX_PATH = _yure.compile(r'/cars/(.+?)/(\d{4})/')
try: _YUX_CL = _yuj.load(open('data/checklists.json', encoding='utf-8'))
except (OSError, ValueError): _YUX_CL = {}
_YUX_KW = {'problems': 'Problems, recalls and years to avoid', 'reliability': 'Reliability, recalls and years to avoid'}

def _yux_gen(fid, y):
    return next((g for g, a, b in _YUX_CL.get(fid, []) if a <= y <= b), None)

_YUX_SVG = lambda d, s=24: (f'<svg aria-hidden="true" focusable="false" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{d}</svg>')
_YUX_WALLET = _YUX_SVG('<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>')
_YUX_LIST = _YUX_SVG('<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>')
_YUX_GO = _YUX_SVG('<path d="m9 18 6-6-6-6"/>', 20)
_YUX_INFO = '<svg aria-hidden="true" focusable="false" width="18" height="18"><use href="/assets/ic.svg?v=1#info"></use></svg>'

def _yux_entry(fid, y, short):
    g = _yux_gen(fid, y)
    if not (CHECKLIST_ON and g): return ''
    slug = fid.replace('/', '-')
    return ('<div class="yux-entry">'
            f'<a class="yux-card yux-dark" href="/afford/{fid}/{y}/"><span class="yux-ci">{_YUX_WALLET}</span><span class="yux-ct"><b>Can you afford this car?</b>'
            f'<small>Your real monthly cost for the {y} {short} · 2 minutes · free</small></span><span class="yux-go">{_YUX_GO}</span></a>'
            f'<a class="yux-card" href="/checklist/{slug}-{g}/"><span class="yux-ci">{_YUX_LIST}</span><span class="yux-ct"><b>Before-you-buy checklist</b></span>'
            f'<span class="yux-go">{_YUX_GO}</span></a></div>')

def _yux_sheet(facts, scored):
    lab = 'See where the score comes from' if scored else 'See where these numbers come from'
    rows = ''.join(f'<li>{x}</li>' for x in facts)
    how = ('<li>Owner complaints per car sold, compared with the average car from the same year (100). Lower is better.</li>' if scored else '')
    return ('<details class="yux-src"><summary>' + _YUX_INFO + f'<span>{lab}</span></summary>'
            f'<div class="yux-sheet" role="dialog" aria-label="{lab[4:].capitalize()}"><div class="yux-sh-top"><p class="yux-sh-h">{lab[4:].capitalize()}</p>'
            '<button type="button" class="yux-x" aria-label="Close">Done</button></div>'
            f'<ul class="yux-sh-l">{how}{rows}</ul><p class="yux-sh-m"><a href="/method/">How the Lemon Index works</a></p></div></details>')

def _yux_end(doc, k, tag):
    depth = 0
    for m in _yure.finditer(rf'<{tag}\b|</{tag}>', doc[k:]):
        depth += 1 if m.group(0) != f'</{tag}>' else -1
        if depth == 0: return k + m.end()
    return -1

def YUX_HOOK(path, doc):
    m = _YUX_PATH.fullmatch(path)
    if not m or '<section class="ph tb-hero' not in doc: return doc
    fid, y = m.group(1), int(m.group(2))
    i = doc.find('<section class="ph tb-hero'); j = _yux_end(doc, i, 'section')
    if j < 0: return doc
    s = _YUS(doc[i:j], 'html.parser'); hero = s.section
    h1 = hero.find('h1')
    if h1 is None: return doc
    # 3. arrows + 9. generation line
    for a in hero.select('.yct-a, p.yct-g'): a.decompose()
    # 2. the keyword line
    sw = h1.select_one('.yct-sw')
    if sw is not None:
        w = sw.get_text(strip=True).rstrip('.').lower()
        sw.string = _YUX_KW.get(w, w.capitalize())
    big = h1.select_one('.yct-big')
    crumbs = hero.select('p.n2-cr a')
    short = crumbs[-1].get_text(strip=True) if len(crumbs) >= 3 else (big.get_text(strip=True) if big else '').split(' ', 2)[-1]
    # 4. better years: cut out here, added at the page bottom below
    by = hero.select_one('.n2-by'); by_html = ''
    if by is not None:
        by['class'] = by.get('class', []) + ['yux-by']; by_html = str(by.extract())
    # 5. one row of buttons
    pl = hero.select_one('p.n2-pl'); btns = ''
    if pl is not None:
        pl['class'] = ['yux-btns']; btns = str(pl.extract())
    for nav in hero.select('nav.yswitch'):
        labs = {x.get('aria-label', '') for x in nav.select('a, button')}
        if btns and all(l == 'All years' or l.startswith('Compare') for l in labs): nav.decompose()
    for x in hero.select('div.cpl-acts'):
        if not x.find(True): x.decompose()
    # 6 + 7. the score
    yh = hero.select_one('div.yhero'); fig = hero.select_one('div.yhero figure.gauge')
    # the one-line stats (ovslim) sit in the Overview panel, outside the hero
    rest = doc[j:]; facts = []
    om = _yure.search(r'<p class="ovslim">(.*?)</p>', rest[:20000], _yure.S)
    if om and 'pf-par' not in om.group(0):
        facts = [x.strip() for x in _yure.findall(r'<span>(.*?)</span>', om.group(1), _yure.S)] or [om.group(1)]
        rest = rest[:om.start()] + rest[om.end():]
    # 9. the black "Too new: partial score" pill (with its own (i)) -> one small amber line under the score, its explanation in the sheet
    eb = hero.select_one('p.early-b'); early = ''
    if eb is not None:
        pop = eb.select_one('.ii-pop'); early = _yuh.escape(pop.get_text(' ', strip=True)) if pop else ''
        eb.decompose()
    if early: facts = [early] + facts
    if yh is not None and fig is not None:
        mm = _yure.match(r'Lemon Index (\d+)', fig.get('aria-label', ''))
        cls = next((c for c in fig.get('class', []) if c in ('good', 'mid', 'bad')), 'mid')
        vd = yh.select_one('.yverd p b'); word = vd.get_text(strip=True).rstrip('.') if vd else ''
        part = '(partial)' in fig.get_text(' ', strip=True)
        if mm:
            bar = _mh_gauge(int(mm.group(1)), cls, _yuh.escape(fig['aria-label'])).replace('<span class="mh-avg">Average</span>', '<span class="mh-avg">100 = average</span>')
            if part or word.lower().startswith('too new'): word = ''   # the early-read badge above already says it
            bar = bar.replace('<span>100 is average</span>', (f'<span class="yux-vd {cls}">{_yuh.escape(word)}</span>' if word else '')
                              + ('<span class="yux-part">Too new: partial score</span>' if part or eb is not None else ''))
            yh.replace_with(_YUS(f'<div class="yux-score">{bar}{_yux_sheet(facts, True)}</div>', 'html.parser'))
    elif yh is not None and facts:   # no score (too few complaints or sales): the facts sheet sits under the verdict, not inside its flex row
        yh.insert_after(_YUS(f'<div class="yux-score yux-na">{_yux_sheet(facts, False)}</div>', 'html.parser'))
    if btns:
        sc = (hero.select('div.yux-score') or hero.select('div.yhero') or [None])[-1]
        frag = _YUS(btns, 'html.parser')
        if sc is not None: sc.insert_after(frag)
        else: hero.append(frag)
    hero['class'] = hero.get('class', []) + ['yux']
    hero.insert(0, _YUS(f'<link rel="stylesheet" href="/assets/yux.css?v={YUX_V}"><script src="/assets/yux.js?v={YUX_V}" defer></script>', 'html.parser'))
    doc = doc[:i] + str(s) + rest
    # 8. entry cards: first thing in the Overview panel
    ent = _yux_entry(fid, y, short)
    if ent:
        k = doc.find('<div class="cpl-grp cpl-g1', i)
        if k > 0: doc = doc[:k] + ent + doc[k:]
    # 11-27 (Elijah): no "Know someone shopping for a used car?" box at the end of year pages: the Share button under the title does the
    # same (share.js is delegated and loads on every page; no GA event or other script reads this box). Only a .pend holding nothing else goes.
    doc = _YUX_PEND.sub(lambda mm: '' if (mm.group(1).count('<button') == 1 and 'Know someone shopping' in mm.group(1)
                                          and '<div' not in mm.group(1) and '<details' not in mm.group(1)) else mm.group(0), doc, count=1)
    # 4. better years at the bottom, before Similar cars / Related (or the end of <main>)
    if by_html:
        k = doc.find('<div class="cpl-grp cpl-rel', i)
        if k < 0: k = doc.find('</main>', i)
        if k > 0: doc = doc[:k] + _yux_bys(by_html) + doc[k:]
    return doc

# 11-27 (Elijah: "Better years to buy" read as part of the share card above it): its own section with a real heading, a small (i) saying
# what the chip number is (the Complaint Score, lower = better; not the Lemon Score in the hero), and each row of chips as equal-width
# buttons (assets/yux.css; the (i) opens via assets/yux.js, the note stays in the HTML)
_YUX_PEND = _yure.compile(r'<div class="pend"><div class="cpl">(.*?)</div></div>', _yure.S)
_YUX_BYN = 'The number on each year is its Complaint Score: owner complaints per car sold. 100 = the average car, lower is better.'
def _yux_bys(by_html):
    head = '<p class="n2-by-h">Better years to buy</p>'
    if head not in by_html:   # the one-line "Fewest complaints of its generation" note
        return f'<section class="yux-bys yux-by1">{by_html}</section>'
    by_html = by_html.replace(head, '', 1).replace(' role="group"', '', 1).replace(' aria-label="Better years to buy"', '', 1)
    return ('<section class="yux-bys" aria-labelledby="yux-by-h"><div class="yux-byh"><h2 id="yux-by-h">Better years to buy</h2>'
            f'<button type="button" class="yux-ib" aria-expanded="false" aria-controls="yux-byn" aria-label="What the numbers mean">{_YUX_INFO}</button></div>'
            f'<p class="yux-byn" id="yux-byn" hidden>{_YUX_BYN}</p>{by_html}</section>')
