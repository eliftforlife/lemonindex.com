# donate_v2.py (11-27, Elijah: "donations v2", modeled on Blender's fund page). exec'd from build.py before the home page (uses E).
# 1. HOME_ASK: Blender's homepage takeover, on the home page only (page() adds it after the date hash, so the home page's date, H1 and
#    SEO text don't change; data-nosnippet keeps it out of search snippets). The head script (DB_JS) hides it before paint: html.db-off
#    = donated in the last 60 days, or "Remind me later" in the last 7 (it reuses the retired phone bar's key, li-donbar-x).
#    support.js fills in today's date ("December 1: Help keep Lemon free." on Giving Tuesday) and the widget.
# 2. DV_WIDGET(): a placeholder of the widget's exact height (support.js builds the widget in it); without JS it's a plain $5 link.
# 3. DV_FEED() / DV_WALL(): /support/'s "Latest donations" and "Thank you" wall from data/support_feed.json (stripe_feed.py).
# The Stripe links live in assets/support.js (LINKS, MONTHLY); this file reads them from there so there's one copy.
import re as _dre, json as _dj, datetime as _ddt

DV_V = '1127d'
DV_CSS = f'<link rel="stylesheet" href="/assets/donate.css?v={DV_V}">'


def _dv_links():
    s = open('assets/support.js', encoding='utf-8').read()
    obj = lambda name: dict(_dre.findall(r"(\w+):\s*'([^']*)'", (_dre.search(r'const ' + name + r' = \{([^}]*)\}', s) or [None, ''])[1]))
    return obj('LINKS'), obj('MONTHLY')


DV_LINKS, _DV_M = _dv_links()
DV_PORTAL = (_dre.search(r"const PORTAL = '([^']+)'", open('assets/support.js', encoding='utf-8').read()) or [None, ''])[1]   # Stripe customer portal (monthly donors)
DV_MNG = f'<a class="dw-mng" href="{E(DV_PORTAL)}" rel="noopener">Manage or cancel your monthly donation</a>' if DV_PORTAL else ''
DV_MON = len(_DV_M) == 3 and all(v.startswith('https://') for v in _DV_M.values())   # the Monthly tab is live only when all 3 links exist
DV_LEVELS = (('pit', 'Pit Crew', 10), ('road', 'Road Trip', 5), ('daily', 'Daily Driver', 3))   # keep in step with MONTHLY_NAMES in support.js


def DV_WIDGET(spot, anchor=''):
    ida = f' id="{anchor}"' if anchor else ''
    return (f'<div class="dw dw-ph{" dw-m" if DV_MON else ""}" data-dw="{spot}"{ida}>'
            f'<a class="btn dw-go" href="{E(DV_LINKS.get("5", "/support/"))}" rel="noopener">Donate $5</a></div>')


HOME_ASK = (DV_CSS + '<section class="hask" aria-label="Donate to Lemon Index" data-nosnippet><div class="hask-in"><div class="hask-txt">'
            '<p class="hask-h"><span class="hask-d">&nbsp;</span><span class="hask-t">Keep Lemon free.</span></p>'
            '<p class="hask-l">Every car report is free. No paywall, no ads.</p>'
            '<p class="hask-a"><b>Today, we’re asking for $5.</b></p>'
            '<div class="hask-o"><button type="button" class="hask-paid">I already donated</button><button type="button" class="hask-later">Remind me later</button></div>'
            '</div>' + DV_WIDGET('home') + '</div></section>')


def _dv_feed_data():
    try: d = _dj.load(open('data/support_feed.json', encoding='utf-8'))
    except Exception: return {}
    return d if isinstance(d, dict) else {}


def _dv_usd(a): return f'${a:,.2f}' if isinstance(a, float) and a % 1 else f'${int(a):,}'


def _dv_when(iso):
    t = _ddt.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ')
    return f'{t:%b} {t.day}'


def _dv_row(f):
    who = f'<b>{E(f["name"])}</b>' if f.get('name') else 'Someone'
    amt = _dv_usd(f['amount']) + (' a month' if f.get('kind') == 'monthly' else '')
    return f'<li><i aria-hidden="true">♡</i><span>{who} chipped in {amt}</span><time datetime="{E(f["at"])}">{_dv_when(f["at"])}</time></li>'


def DV_FEED(show=5):
    """count line + newest donations; the rest behind See all. The count only shows in the month it's for (support.js re-checks)."""
    d = _dv_feed_data(); feed = d.get('feed') or []
    if not feed: return '<section class="spf-s" hidden><h2>Latest donations</h2><div class="spf"></div></section>'   # support.js fills it live (GET /feed)
    now = _ddt.date.today().strftime('%Y-%m')
    n = int(d.get('count') or 0) if d.get('month') == now else 0
    cnt = (f'<p class="spf-n" data-month="{now}"><b>{n:,}</b>{"person" if n == 1 else "people"} chipped in this month</p>' if n else '')
    rows = [_dv_row(f) for f in feed]
    more = (f'<details class="spf-more"><summary>See all</summary><ul class="spf-l">{"".join(rows[show:])}</ul></details>' if len(rows) > show else '')
    return f'<section class="spf-s"><h2>Latest donations</h2><div class="spf">{cnt}<ul class="spf-l">{"".join(rows[:show])}</ul>{more}</div></section>'


def DV_WALL():
    """'Thank you' credits: Pit Crew / Road Trip / Daily Driver / One-time, names only from the shout-out box.
    The monthly groups stay hidden until the monthly links exist (support.js shows them in ?monthly-preview)."""
    d = _dv_feed_data(); w, anon = d.get('wall') or {}, d.get('anon') or {}
    def names(g):
        out = []
        for e in w.get(g) or []:
            u = e.get('url') if g == 'pit' else None
            out.append(f'<a href="{E(u)}" rel="sponsored nofollow ugc noopener" target="_blank">{E(e["name"])}</a>' if u else E(e['name']))
        x = int(anon.get(g) or 0)
        s = ' · '.join(out)
        if x and out: s += f' <span class="spw-x">and {x} other{"s" if x != 1 else ""}</span>'
        elif x: s = f'{x:,} supporter{"s" if x != 1 else ""}'   # 11-27: no names (yet) = a count only
        return s
    groups = []
    for g, nm, amt in DV_LEVELS:
        body = names(g) or f'<a class="spw-cta" href="#give" data-pick="m{amt}">Be the first {nm} member</a>'
        groups.append(f'<div class="spw-g spw-m"{"" if DV_MON else " hidden"}><h3>{nm}<small>${amt} a month</small></h3><p class="spw-n">{body}</p></div>')
    once = names('once') or '<a class="spw-cta" href="#give" data-pick="5">Be the first</a>'
    groups.append(f'<div class="spw-g"><h3>One-time</h3><p class="spw-n">{once}</p></div>')
    return '<h2>Thank you</h2><div class="spw">' + ''.join(groups) + '</div>'


# 11-27: serve data/support_goal.json at /data/support_goal.json. The lemon-store Worker reads its 'renewals' (this month's monthly renewals,
# from stripe_goal.py's invoice read) and adds them to /goal, because the Worker's own Stripe key never reads invoices.
try:
    _dg = open('data/support_goal.json', encoding='utf-8').read()
    os.makedirs(os.path.join(OUT, 'data'), exist_ok=True)
    _dgp = os.path.join(OUT, 'data', 'support_goal.json')
    if not os.path.exists(_dgp) or open(_dgp, encoding='utf-8').read() != _dg: open(_dgp, 'w', encoding='utf-8').write(_dg)
except FileNotFoundError: pass
