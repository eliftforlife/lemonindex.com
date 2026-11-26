# 11-23 search traffic (Job C, part 1): a short answer box near the top of the pages Google shows most (data/answer_pages.json, made by
# data_answer_pages.py from Search Console). The model and year page tops were cut down on purpose (11-12 / 11-19: no answer text in the
# hero), so the box sits right under the score instead of under the H1, and it only repeats the page's own first quick answer
# ("Is the 2019 Nissan Sentra reliable?" + its 2-3 sentence answer, written from the page's data by build.py). Nothing new is computed here.
# exec'd by build.py; ANS_HOOK(path, body) runs in page() after the date hash (like MH_HOOK), so it never moves a page's date by itself.
import json as _aj, os as _aos, re as _are
_ANS_P = set(_aj.load(open('data/answer_pages.json', encoding='utf-8'))['pages']) if _aos.path.exists('data/answer_pages.json') else set()
_ANS_RE = _are.compile(r'<section class="(?:yc )?yqa"><h2>Quick answers\.?</h2>.*?<h3[^>]*>(.*?)</h3>(?:</summary>)?\s*<p>(.*?)</p>', _are.S)
_ANS_CSS = ('<style id="ansb-css">.ansb{max-width:620px;margin:14px auto 0;padding:0 4px;text-align:center}'
            '.ansb p{margin:0;font-size:15.5px;line-height:1.5;color:#424245}.ansb b{color:#1d1d1f}</style>')
# 11-23 SEO batch (s02): the box also goes on every indexed year page that has a Quick answers block (not only the Search Console list),
# and on every /electric/<x>/ page. Indexed = what quality_gate.py keeps in search: not under 30 owner complaints for that year (page_dates.json
# facts, which page() sets before this hook runs), or Google has already shown the page (gsc_seen.json + gsc.db, read once).
_ANS_SEEN = None
def _ans_seen():
    global _ANS_SEEN
    if _ANS_SEEN is None:
        _ANS_SEEN = set(_aj.load(open('data/gsc_seen.json', encoding='utf-8'))) if _aos.path.exists('data/gsc_seen.json') else set()
        _db = globals().get('_QG_DB') or r'C:\Users\elift\Desktop\Eliftforlife youtube\0 HQ\Autopost\gsc\gsc.db'
        if _aos.path.exists(_db):
            try:
                import sqlite3 as _asq
                _c = _asq.connect(_db)
                _ANS_SEEN |= {pg.replace('https://lemonindex.com', '').split('#')[0].split('?')[0] or '/' for (pg,) in _c.execute("select distinct page from rows where site='https://lemonindex.com/' and impr > 0")}
                _c.close()
            except Exception: pass
    return _ANS_SEEN
def _ans_indexed(path):
    f = (PD.get(path) or {}).get('f')
    return not (f and f[0] < 30) or path in _ans_seen()   # quality_gate.py's own rule: thin = under 30 complaints and never shown by Google
# /electric/<x>/: the page's own answer line (p.tra, which EV5_HOOK lifts under the score) already is its first quick answer, so the box
# there is that line with its question on top (seo_ld.py SL_EVQ), not a second copy of the same sentence.
_ANS_EVCSS = '<style id="ansq-css">.tra .ansq{display:block;margin:0 0 4px;font-weight:600;color:#1d1d1f}</style>'
def ANS_HOOK(path, body):
    _evq = globals().get('SL_EVQ', {}).get(path)
    if _evq:
        if 'class="ansq"' in body or '<p class="tra">' not in body: return body
        return body.replace('<p class="tra">', f'{_ANS_EVCSS}<p class="tra"><b class="ansq">{_evq}</b>', 1)
    if not _are.fullmatch(r'/cars/[a-z0-9-]+/(\d{4}/)?', path) or 'class="ansb"' in body: return body
    if path not in _ANS_P and not (_are.fullmatch(r'/cars/[a-z0-9-]+/\d{4}/', path) and _ans_indexed(path)): return body
    m = _ANS_RE.search(body)
    if not m: return body
    q = _are.sub(r'<[^>]+>', '', m.group(1)).strip(); a = m.group(2).strip()
    if not q.endswith('?') or len(_are.sub(r'<[^>]+>', '', a)) < 40: return body
    box = f'{_ANS_CSS}<div class="ansb"><p><b>{q}</b> {a}</p></div>'
    i = body.find('tb-hero')
    if i < 0: return body
    k = body.find('<div class="mh-years">', i)   # model page: between the score and "Every year"
    if k < 0 or k > body.find('<div class="tbx"', i): k = body.find('<div class="tbx"', i)   # year page: right after the hero
    return body if k < 0 else body[:k] + box + body[k:]
