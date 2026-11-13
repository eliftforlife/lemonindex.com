# 11-12 (Elijah, desktop review of /best/safest-cars-for-teens/: "the top is slammed with a bunch of random text", "all the things are kind of
# confusing underneath"): shared pieces for every /best/ list, so the page reads top to bottom as
#   one-line hero (what the list ranks and how) -> the ranked list -> best by type -> quick answers as tap-to-open questions
#   -> "Before you buy" as cards (the VIN check in its own box) -> the budget lists as photo cards -> sources, small.
# Run by seo_pages.py with exec() before teen_page.py. Classes: cb-* (assets/cb.css). The answers stay in the HTML inside <details> for search.
CB_ASSET = '<link rel="stylesheet" href="/assets/cb.css?v=2">'
CB_JS = '<script src="/assets/cb.js?v=2" defer></script>'


def cbx_head(h1, line):
    return (f'{CB_ASSET}<header class="advh1 cbx-h"><p class="ph-e"><a href="/best/">Best cars</a></p><h1>{h1}</h1>'
            f'<p class="cbx-line">{line}</p></header>')


def cbx_faq(faq, title='Quick answers'):
    """questions only; tap one to open its answer (<details>, so the answer is in the HTML)"""
    return (f'<section class="cbx-sec"><h2>{title}</h2><div class="cbx-qas">'
            + ''.join(f'<details class="cbx-qa"><summary>{E(q)}</summary><div class="cbx-a">{a}</div></details>' for q, a in faq) + '</div></section>')


def cbx_vin():
    return ('<div class="cbx-vin"><h3>Check the VIN for open recalls</h3><p>Free. It&#39;s on the dashboard by the windshield, on the door frame, or on the registration.</p>'
            '<form class="cbx-vinf" action="/vin/" method="get" autocomplete="off"><input maxlength="17" placeholder="Enter a 17-character VIN" aria-label="VIN" spellcheck="false" autocapitalize="characters">'
            '<button class="btn" type="submit">Check</button></form></div>')


def cbx_buy(steps=None):
    """'Before you buy': the VIN box first, then the other steps as small cards"""
    steps = steps or [('Read that year&#39;s complaints', 'Open the exact model year from the list: its top problems, recalls and owners&#39; repair bills.'),
                      ('Get an inspection', 'Have an independent mechanic check the car before you pay.')]
    return ('<section class="cbx-sec"><h2>Before you buy</h2><div class="cbx-buy">' + cbx_vin()
            + ''.join(f'<div class="cbx-step"><b>{i}</b><h3>{t}</h3><p>{d}</p></div>' for i, (t, d) in enumerate(steps, 2)) + '</div></section>' + CB_JS)


def cbx_budgets(skip=None, title='Shopping on a budget?'):
    """one photo card per budget list (data/yt/best-used-<k>/consensus.json), with the list's #1 scored pick"""
    cards = []
    for k, label in (('5k', '$5,000'), ('10k', '$10,000'), ('15k', '$15,000'), ('20k', '$20,000')):
        u = f'/best/used-cars-under-{k[:-1]}000/'
        p_ = os.path.join(YT_SRC, f'best-used-{k}', 'consensus.json')
        if u == skip or not os.path.exists(p_): continue
        c0 = next((BYNAME.get(r['model']) for r in json.load(open(p_, encoding='utf-8'))['ranking'] if BYNAME.get(r['model'])), None)
        ph = aph(c0['id']) if c0 else None
        im = f'<span class="bcp"><img src="{ph["src"]}" alt="" width="{ph["w"]}" height="{ph["h"]}" loading="lazy" decoding="async"></span>' if ph else '<span class="bcp"></span>'
        cards.append(f'<a class="bcard cbx-bud" href="{u}">{im}<b>Under {label}</b>' + (f'<small>Top scored pick: {E(c0["name"])}</small>' if c0 else '') + '<span class="tl">See the list <i>›</i></span></a>')
    return f'<section class="cbx-sec"><h2>{title}</h2><div class="bcards cbx-buds">{"".join(cards)}</div></section>' if cards else ''


def cbx_types(groups, rowf):
    """'Best by type': one card per type with its top 3 (groups = [(label, [items])])"""
    out = ''.join(f'<div class="cbx-type"><h3>{lab}</h3><ol>{"".join(rowf(x) for x in L[:3])}</ol></div>' for lab, L in groups if len(L) >= 2)
    return f'<section class="cbx-sec"><h2>Best by type</h2><div class="cbx-types">{out}</div></section>' if out else ''


def cbx_src(html_):
    # 11-13 v4: the sources sit behind a small corner button (popover), still in the HTML
    return f'<div class="cbx-srcrow">{cb_info(html_, "Sources and method", "Sources and method")}</div>'


# ---- 11-13 v2 (Elijah on the phone screens: "the safety screen things need better design like bars or charts ... it's a little confusing still"):
# every list is visual first: a ranked bar chart of the whole list at the top (tap a bar = jump to that car), then one card per car with
# a plain-English line on why it's there and its numbers as labeled bars (Lemon Index against the average-car line, crash stars as 5 segments,
# buyer-guide picks as a share of the videos). Only numbers we have; every bar carries its number and unit.
def cbx_scale(vals): return max(120, max(vals) * 1.08)


def cbx_chart(rows, mx, cap, avg=True, title='At a glance'):
    """rows = [(href, label_html, value, value_txt, cls)]; bar length = value / mx; a dashed line at 100 (the average car) when avg"""
    line = f'<em style="left:{100 / mx * 100:.1f}%"></em>' if avg else ''
    return (f'<div class="cbx-chart"><div class="cbx-ct"><b>{title}</b>{cb_info(cap, "How to read this chart")}</div>'
            + ''.join(f'<a class="cbx-cr" href="{h}"><span class="cbx-crl">{lab}</span><span class="cbx-crt"><i class="{k}" style="--w:{max(1.5, min(100, v / mx * 100)):.1f}%"></i>{line}</span><b class="{k}">{t}</b></a>'
                      for h, lab, v, t, k in rows) + '</div>')


def cbx_meter(label, v, mx, txt, cls='', avg=True, unit=''):
    line = f'<em style="left:{100 / mx * 100:.1f}%" title="average car = 100"></em>' if avg else ''
    return (f'<div class="cbx-m"><span class="cbx-ml">{label}</span><span class="cbx-mt"><i class="{cls}" style="--w:{max(1.5, min(100, v / mx * 100)):.1f}%"></i>{line}</span>'
            f'<b class="{cls}">{txt}<small>{unit}</small></b></div>')


def cbx_stars(lo, hi):
    star = lambda k: f'<svg class="{k}" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M12 2.6l2.9 6 6.5.8-4.8 4.5 1.2 6.5L12 17.3l-5.8 3.1 1.2-6.5L2.6 9.4l6.5-.8z"/></svg>'
    seg = ''.join(star('on' if k <= lo else 'hi' if k <= hi else '') for k in range(1, 6))   # yellow = earned by every version; outlined = only the best version
    txt = '5 of 5' if lo == 5 else f'{lo}–{hi} of 5'
    return f'<div class="cbx-m"><span class="cbx-ml">Crash test</span><span class="cbx-st" aria-label="NHTSA crash test {txt} stars">{seg}</span><b>{txt}<small>stars</small></b></div>'


def cbx_times(li, y=None):
    """a Lemon Index in plain words: '12x fewer complaints than the average 2018 car'"""
    avg = f'the average {y} car' if y else 'the average car'
    if li <= 50: return f'{round(100 / li)}× fewer complaints than {avg}'
    if li < 90: return f'{100 - li}% fewer complaints than {avg}'
    if li <= 110: return f'about as many complaints as {avg}'
    return f'{li / 100:.1f}× the complaints of {avg}'


def cbx_card(anchor, rank, img, title_html, why, meters, extra=''):
    return (f'<li class="cbx-card" id="{anchor}"><div class="cbx-chd"><span class="cbx-rk">{rank}</span>{img}<div class="cbx-cn"><h3>{title_html}</h3></div></div><p class="cbx-why">{why}</p>'
            f'<div class="cbx-ms">{meters}</div>{extra}</li>')
