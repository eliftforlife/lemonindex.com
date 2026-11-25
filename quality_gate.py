# 11-18 (AdSense "Low value content" -> Mediavine prep, Elijah: "if all of them help, go ahead"): the thin-page gate.
# Run by build.py right after the sitemap URL list is made. Thin pages stay on the site for visitors (noindex,follow: Google still follows their
# links) but leave search and the sitemap, so Google and ad-network reviewers judge the site by its strong pages.
# A page is thin when it has little data of its own:
#   /cars/<model>/<year>/              under 30 owner complaints for that model year (page_dates.json facts)
#   /cars/<model>/<year>/advanced/     always: the year page covers the same car and year (advanced keeps the deep data for visitors)
#   /repair-cost/<repair>/<model>/     under 20 owner repair bills
#   /check-engine-light/<code>/<model>/ under 25 owner complaints naming the code
#   /compare/<a>-vs-<b>/, /motorcycles/<bike>/<year>/, /planes/<x>/<y>/   always (made automatically, little text of their own)
# ...unless Google has already shown the page in search: any page with Search Console impressions stays indexed, so nothing that earns
# traffic is hidden. Seen pages are kept for good in data/gsc_seen.json (read from 0 HQ/Autopost/gsc/gsc.db when it's there).
# Quick builds (quick_mode.py) reuse the last full build's list (data/thin_pages.json), so they never touch pages outside --only.
import sqlite3 as _sq, collections as _qgc
_QG_DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\0 HQ\Autopost\gsc\gsc.db'
_QG_SEEN_F, _QG_THIN_F = 'data/gsc_seen.json', 'data/thin_pages.json'
_QG_NOI = '<meta name="robots" content="noindex,follow">'

def _qg_seen():
    seen = set(_jl(_QG_SEEN_F) or [])
    if os.path.exists(_QG_DB):
        try:
            c = _sq.connect(_QG_DB)
            for (pg,) in c.execute("select distinct page from rows where site='https://lemonindex.com/' and impr > 0"):
                seen.add(pg.replace('https://lemonindex.com', '').split('#')[0].split('?')[0] or '/')
            c.close()
        except Exception as ex: print('quality gate: gsc.db not read:', ex)
    return seen

def _qg_file(u): return os.path.join(OUT, u.strip('/'), 'index.html')

def _qg_num(u, rx):
    try: s = open(_qg_file(u), encoding='utf-8').read(6000)
    except OSError: return None
    m = re.search(rx, s); return int(m.group(1).replace(',', '')) if m else None

def _qg_thin(u):
    if re.fullmatch(r'/cars/[^/]+/\d{4}/advanced/', u): return 'advanced'
    if re.fullmatch(r'/cars/[^/]+/\d{4}/', u):
        f = PD.get(u, {}).get('f'); return 'few complaints' if f and f[0] < 30 else None
    if re.fullmatch(r'/repair-cost/[^/]+/[^/]+/', u):
        n = _qg_num(u, r'from (\d[\d,]*) owner reports'); return 'few repair bills' if n is not None and n < 20 else None
    if re.fullmatch(r'/check-engine-light/[^/]+/[^/]+/', u):
        n = _qg_num(u, r'in (\d[\d,]*) complaints'); return 'few complaints' if n is not None and n < 25 else None
    if re.fullmatch(r'/compare/[^/]+/', u): return 'compare'
    # 11-24: motorcycle Repairs / Recalls sub-pages are real pages (Elijah: they deserve their own page); thin ones are
    # already noindexed by sub_pages.py's 60-word rule, so only the other auto pages fall under this blanket rule
    if re.fullmatch(r'/motorcycles/[^/]+/(?!repairs/|recalls/)[^/]+/', u) or re.fullmatch(r'/planes/[^/]+/[^/]+/', u): return 'auto year page'
    return None

if QM.ON:
    THIN = set(_jl(_QG_THIN_F) or [])
else:
    _QG_SEEN = _qg_seen(); json.dump(sorted(_QG_SEEN), open(_QG_SEEN_F, 'w', encoding='utf-8'), indent=0)
    _qgw = {}
    for _u in dict.fromkeys(urls):
        if _u in _QG_SEEN: continue
        _w = _qg_thin(_u)
        if _w: _qgw[_u] = _w
    THIN = set(_qgw)
    json.dump(sorted(THIN), open(_QG_THIN_F, 'w', encoding='utf-8'), indent=0)
    print('quality gate:', len(THIN), 'thin pages noindex + out of the sitemap |', dict(_qgc.Counter(_qgw.values())),
          '| kept because Google showed them:', sum(1 for u in urls if u in _QG_SEEN and _qg_thin(u)))
# 11-19 sub_pages.py: a card's own page is thin when its car page is, and SUB_THIN_KEYS pages always (quick builds too)
for _u in [u for u in urls if u in globals().get('SUB_URLS', ()) or (PD.get(u) or {}).get('sb')]:
    _par = re.sub(r'[^/]+/$', '', _u)
    if _u in globals().get('SUB_THIN', ()) or _par in THIN or any(_u.endswith(f'/{s}/') and re.search(r'/\d{4}/[^/]+/$', _u) for s in ('engines',)): THIN.add(_u)
THIN |= set(globals().get('YTQ_THIN', ()))
THIN |= set(globals().get('INS_THIN', ()))   # 11-25 estimate-only /insurance/<state>/ pages (insurance_pages.py; quick builds too)   # 11-25 YouTube-only request pages with 1 ranked year or under 40 videos (yt_req_pages.py; quick builds too)
_qg_n = 0
for _u in THIN:
    if not QM.want(_u): continue
    _f = _qg_file(_u)
    try: _s = open(_f, encoding='utf-8').read()
    except OSError: continue
    if 'name="robots"' in _s[:6000] or '<link rel="canonical"' not in _s: continue
    open(_f, 'w', encoding='utf-8').write(_s.replace('<link rel="canonical"', _QG_NOI + '<link rel="canonical"', 1)); _qg_n += 1
urls = [u for u in urls if u not in THIN]
print('quality gate: noindex written to', _qg_n, 'page files;', len(urls), 'pages left in the sitemap')
