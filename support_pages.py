# /support/ ("Where your money goes") and /coming-soon/ ("What's coming to Lemon"), 11-24.
# Elijah approved the mockups 11-24 ("redo the pages to look like our home page and gen new image for each card"):
# home-style .mg grid of cards (picture, bold name, one gray line), images in assets/support/ (gpt-image-2 low + cutout).
# The monthly goal box reads data/support_goal.json; it hides itself when that file's month isn't the build month,
# so a stale "raised" number never shows. Update "raised" from Stripe (Lemon Index account) when donations come in.
# exec'd from build.py (uses page, E, json, datetime).
import json as _sj, datetime as _sdt

_SV = '1124g'


def _sp_card(img, title, line, href=None, tag=None):
    tg = f'<span class="tag">{tag}</span>' if tag else ''
    inner = (f'<span class="mc-p"><img src="/assets/support/{img}.webp?v={_SV}" alt="" width="600" height="360" loading="lazy"></span>'
             f'<b>{E(title)}</b><small class="mc-k">{E(line)}</small>{tg}')
    return f'<a class="mc" href="{href}">{inner}</a>' if href else f'<div class="mc">{inner}</div>'


def _sp_grid(cards): return '<div class="mg">' + ''.join(_sp_card(*c) for c in cards) + '</div>'


# 11-24 Elijah (phone screenshot of /coming-soon/): "What it helps with" = icons, not pictures. Flat black Lucide icons.
_SP_IC = {
    'adfree': '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
    'free': '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="m9 15 2 2 4-4"/>',
    'data': '<rect width="20" height="8" x="2" y="2" rx="2"/><rect width="20" height="8" x="2" y="14" rx="2"/><path d="M6 6h.01M6 18h.01"/>',
    'next': '<path d="m15 12-8.373 8.373a1 1 0 1 1-3-3L12 9"/><path d="m18 15 4-4"/><path d="m21.5 11.5-1.914-1.914A2 2 0 0 1 19 8.172V7l-2.26-1.13a6 6 0 0 0-2.663-.629H12.5l.9.9a3 3 0 0 1 0 4.242L12.3 11.3"/>',
}


def _sp_icons(cards):
    out = []
    for ic, title, line, *rest in cards:
        href = rest[0] if rest else None
        svg = f'<span class="spi-i"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_SP_IC[ic]}</svg></span>'
        inner = f'{svg}<b>{E(title)}</b><small>{E(line)}</small>'
        out.append(f'<a class="spi" href="{href}">{inner}</a>' if href else f'<div class="spi">{inner}</div>')
    return '<div class="spi-g">' + ''.join(out) + '</div>'


def _sp_hero(h1, lede): return f'<section class="finder"><h1>{E(h1)}</h1><p class="lede">{E(lede)}</p></section>'


_SP_LADDER = (100, 250, 500, 1000, 2500, 5000)   # 11-24 Elijah: $100 a month; hit it -> "Goal reached, new goal $250", and so on up


def _sp_goal():
    # data/support_goal.json {month: "YYYY-MM", raised: dollars this month} (stripe_goal.py writes it from Stripe).
    # A new month starts at $0 of $100, with last month's total under the bar.
    try: g = _sj.load(open('data/support_goal.json', encoding='utf-8'))
    except Exception: g = {}
    now = _sdt.date.today().strftime('%Y-%m')
    if g.get('month') == now: raised, last = int(g.get('raised') or 0), (int((g.get('last') or {}).get('raised') or 0) or None)
    else: raised, last = 0, (int(g.get('raised') or 0) if g.get('month') else None)
    goal = next((x for x in _SP_LADDER if x > raised), _SP_LADDER[-1])
    hit = max((x for x in _SP_LADDER if x <= raised), default=0)
    pct = max(1.5, min(100, raised * 100 / goal))
    note = (f'<p class="spg-goal-n"><b>${hit:,} goal reached.</b> New goal: ${goal:,}.</p>' if hit
            else f'<p class="spg-goal-n">Last month: ${last:,} raised.</p>' if last else '')
    return (f'<div class="spg-goal"><div class="spg-goal-t"><b>${raised:,} raised</b><span>of ${goal:,} this month</span></div>'
            f'<div class="spg-bar" role="img" aria-label="${raised:,} of ${goal:,} raised this month"><i style="width:{pct:.1f}%"></i></div>{note}</div>')


_SP_CSS = '<link rel="stylesheet" href="/assets/support-pages.css?v=' + _SV + '">'

_SUPPORT = (_SP_CSS + '<div class="pg spg">' + _sp_hero('Where your money goes.', 'Lemon Index is free, with no ads. Donations keep it that way.')
    + _sp_goal()
    + '<h2>What it helps with</h2>' + _sp_icons([
        ('adfree', 'Keeps it ad-free', 'No pop-ups, no selling your data'),
        ('free', 'Keeps every report free', 'No paywall, no account'),
        ('data', 'Pays for data and hosting', 'Images, prices, servers'),
        ('next', 'Builds what’s next', 'New cars, bikes and countries', '/coming-soon/'),
    ])
    + '<div class="spg-btns"><button class="btn supl" type="button">Chip in</button><a class="btn ghost" href="/coming-soon/">See what’s coming</a></div>'
    + '<p class="spg-note">Payments by Stripe. Not tax-deductible. Full refund within 14 days.</p></div>')

_COMING = (_SP_CSS + '<div class="pg spg">' + _sp_hero('What’s coming to Lemon.', 'Everything we’re building next. Donations decide how fast.')
    + '<h2>Building now</h2>' + _sp_grid([
        ('checklists', 'Before-you-buy checklists', 'What to check, car by car', None, 'Soon'),
        ('budget', 'Cars for your budget', 'The 5 best picks per price', '/budget/', 'New'),
        ('performance', 'Performance cars', 'Prices and owner scores', None, 'Soon'),
    ])
    + '<h2>Next</h2>' + _sp_grid([
        ('offroad', '4x4s, quads and UTVs', 'Problems and recalls'),
        ('dirtbikes', 'Dirt bikes', 'Gas and electric'),
        ('espanol', 'Lemon Index en español', 'Every report in Spanish'),
        ('repairs', 'Repair costs', 'What each fix costs'),
    ])
    + '<h2>Later</h2>' + _sp_grid([
        ('toys', 'Lemon Index Toys', 'E-bikes, scooters, RC cars'),
        ('world', 'India and Latin America', 'Local cars, own sites'),
        ('listing', 'Listing checker', 'Paste a listing, get a report'),
        ('canada', 'Canada, Australia, NZ', 'Local cars and recalls'),
        ('semis', 'Semi trucks', 'Problems, recalls and costs'),   # 11-25 Elijah
    ])
    + '<h2>Classic cars</h2>' + _sp_grid([
        ('dec90', '90s cars', 'Supra, NSX, Miata'),
        ('dec80', '80s cars', 'DeLorean, E30, Fox Mustang'),
        ('dec70', '70s cars', 'Trans Am, Bronco, 911'),
        ('dec60', '60s cars', 'Mustang, Corvette, Beetle'),
    ])
    # 11-24 Elijah: the top bar now sends people here, so this page makes the ask: big donate button, goal, what it helps with
    + '<section class="spg-ask"><h2>Want to make this happen?</h2>'
    + '<p class="spg-ask-l">Every donation goes into building these. The more we raise, the faster they ship.</p>'
    + _sp_goal()
    + '<button class="btn supl spg-big" type="button">Help build it</button>'
    + '<p class="spg-note">Payments by Stripe. Not tax-deductible. Full refund within 14 days.</p></section>'
    + '<h2>What it helps with</h2>' + _sp_icons([
        ('adfree', 'Keeps it ad-free', 'No pop-ups, no selling your data'),
        ('free', 'Keeps every report free', 'No paywall, no account'),
        ('data', 'Pays for data and hosting', 'Images, prices, servers'),
        ('next', 'Builds what’s next', 'Everything on this page'),
    ])
    + '<div class="spg-btns"><a class="btn ghost" href="/vote/">Vote on what’s next</a></div>'
    + '<p class="spg-note">Plans, not promises. The order can change.</p></div>')

page('/support/', 'Where Your Donation Goes', 'Lemon Index is free, with no ads. See what donations pay for: ad-free pages, free reports, data, hosting and new features.', _SUPPORT)
page('/coming-soon/', 'What’s Coming to the Lemon Index', 'Everything Lemon Index is building next: checklists, performance cars, 4x4s, dirt bikes, Spanish pages, repair costs and classic cars.', _COMING)
