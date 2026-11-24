# /support/ ("Where your money goes") and /coming-soon/ ("What's coming to Lemon"), 11-24.
# Elijah approved the mockups 11-24 ("redo the pages to look like our home page and gen new image for each card"):
# home-style .mg grid of cards (picture, bold name, one gray line), images in assets/support/ (gpt-image-2 low + cutout).
# The monthly goal box reads data/support_goal.json; it hides itself when that file's month isn't the build month,
# so a stale "raised" number never shows. Update "raised" from Stripe (Lemon Index account) when donations come in.
# exec'd from build.py (uses page, E, json, datetime).
import json as _sj, datetime as _sdt

_SV = '1124d'


def _sp_card(img, title, line, href=None, tag=None):
    tg = f'<span class="tag">{tag}</span>' if tag else ''
    inner = (f'<span class="mc-p"><img src="/assets/support/{img}.webp?v={_SV}" alt="" width="600" height="360" loading="lazy"></span>'
             f'<b>{E(title)}</b><small class="mc-k">{E(line)}</small>{tg}')
    return f'<a class="mc" href="{href}">{inner}</a>' if href else f'<div class="mc">{inner}</div>'


def _sp_grid(cards): return '<div class="mg">' + ''.join(_sp_card(*c) for c in cards) + '</div>'


def _sp_hero(h1, lede): return f'<section class="finder"><h1>{E(h1)}</h1><p class="lede">{E(lede)}</p></section>'


def _sp_goal():
    try: g = _sj.load(open('data/support_goal.json', encoding='utf-8'))
    except Exception: return ''
    if g.get('month') != _sdt.date.today().strftime('%Y-%m') or not g.get('goal'): return ''
    raised, goal = int(g.get('raised') or 0), int(g['goal'])
    pct = max(1.5, min(100, raised * 100 / goal))
    return (f'<div class="spg-goal"><div class="spg-goal-t"><b>${raised:,} raised</b><span>of ${goal:,} this month</span></div>'
            f'<div class="spg-bar" role="img" aria-label="${raised:,} of ${goal:,} raised this month"><i style="width:{pct:.1f}%"></i></div></div>')


_SP_CSS = '<link rel="stylesheet" href="/assets/support-pages.css?v=' + _SV + '">'

_SUPPORT = (_SP_CSS + '<div class="pg spg">' + _sp_hero('Where your money goes.', 'Lemon Index is free, with no ads. Donations keep it that way.')
    + _sp_goal()
    + '<h2>What it helps with</h2>' + _sp_grid([
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
    + '<h2>What it helps with</h2>' + _sp_grid([
        ('adfree', 'Keeps it ad-free', 'No pop-ups, no selling your data'),
        ('free', 'Keeps every report free', 'No paywall, no account'),
        ('data', 'Pays for data and hosting', 'Images, prices, servers'),
        ('next', 'Builds what’s next', 'Everything on this page'),
    ])
    + '<div class="spg-btns"><a class="btn ghost" href="/vote/">Vote on what’s next</a></div>'
    + '<p class="spg-note">Plans, not promises. The order can change.</p></div>')

page('/support/', 'Where Your Donation Goes', 'Lemon Index is free, with no ads. See what donations pay for: ad-free pages, free reports, data, hosting and new features.', _SUPPORT)
page('/coming-soon/', 'What’s Coming to the Lemon Index', 'Everything Lemon Index is building next: checklists, performance cars, 4x4s, dirt bikes, Spanish pages, repair costs and classic cars.', _COMING)
