# 11-25 viewer requests (Elijah: "add all these cars even if all we have is a youtube score or wait until they have a yt score but que it so
# once it has yt score its added"). data/yt_requests.json lists every vehicle viewers asked for that had no page ("3 Lemon Index/Requests we
# don't have 11-25.md"):
#   pages: one YouTube-only page each, live as soon as its score file has a ranked year (10+ videos, the model pages' YT_MIN):
#          kind moto -> /motorcycles/<slug>/ (its coming-soon card on /motorcycles/ becomes a link), perf -> /cars/<slug>/ (its performance
#          card on /cars/ goes live), car -> /cars/<slug>/ (a card under its brand on /cars/). Data = the pull worker's score file
#          (data/moto_yt.json, perf_yt.json, newcar_yt.json, yt_scores.json): {year: {score, videos, topics, top}}.
#   (older years / generations of models we have are NOT here: Elijah keeps them for the older-years project, "3 Lemon Index/Older years first list.md")
# The pull workers (3 Lemon Index/data/yt/auto_gens.py, queue3/front.json) pull the unscored ones first and, when one is scored, quick-build the
# 'quick' pages listed for it here, so a page appears with nobody touching it. Pages with little data are noindexed (YTO_THIN, quality_gate.py).
# Honest label on every page: YouTube buyer score only, no owner-complaint data yet. Nothing here is invented: every number is from the score file.
# exec'd by build.py twice: early (YTQ_URL: page address per request, for the cards and the search) and late (ytq_build(): the pages).
YTQ = _jl('data/yt_requests.json') or {}
YTQ_MAXY = 2025   # 2026 model years: launch reviews only, no owners yet (skipped, like the model pages' brand-new years)
_YTQ_SC = {}
def _ytq_sc(fn):
    if fn not in _YTQ_SC: _YTQ_SC[fn] = _jl('data/' + fn) or {}
    return _YTQ_SC[fn]
def ytq_years(p):
    """{year: entry} for one request: years up to YTQ_MAXY with a score"""
    d = _ytq_sc(p['file']).get(p['fid']) or {}
    return {int(y): v for y, v in d.items() if int(y) <= YTQ_MAXY and v and v.get('score') is not None}
def ytq_ranked(p):
    """[(year, score, videos)] best-liked first: years with YT_MIN+ videos (the model pages' rule)"""
    ys = ytq_years(p)
    return sorted(((y, v['score'], v.get('videos') or 0) for y, v in ys.items() if (v.get('videos') or 0) >= 10), key=lambda t: (-t[1], -t[2], -t[0]))
def ytq_url(p): return f'/motorcycles/{p["slug"]}/' if p['kind'] == 'moto' else f'/cars/{p["slug"]}/'
YTQ_LIVE = [p for p in YTQ.get('pages', []) if ytq_ranked(p)]
YTQ_URL = {f'{p["kind"]}:{p["slug"]}': ytq_url(p) for p in YTQ_LIVE}
YTQ_THIN = {ytq_url(p) for p in YTQ_LIVE if len(ytq_ranked(p)) < 2 or sum(v for _, _, v in ytq_ranked(p)) < 40}

def ytq_img(p):
    """the vehicle's illustration already on the site (coming-soon card / performance card / model card), else None"""
    if p.get('img'): return {'src': p['img'], 'w': p.get('w', 1000), 'h': p.get('h', 600), 'author': '', 'ai': f'{p.get("img_year", "")} {p["name"]}'.strip(), 'noun': 'motorcycle' if p['kind'] == 'moto' else 'car'}
    return None

def ytq_build():
    out = []
    for p in YTQ_LIVE:
        url = ytq_url(p); nm = p['name']; rk = ytq_ranked(p); ys = ytq_years(p)
        n = round(sum(v.get('videos') or 0 for v in ys.values())); y0, y1 = min(ys), max(ys); best = rk[0][0]
        span = f'{y0}–{y1}' if y0 != y1 else str(y0)
        ph = ytq_img(p); hub = ('/motorcycles/', 'Motorcycles') if p['kind'] == 'moto' else ('/cars/', 'All cars')
        noun = 'bike' if p['kind'] == 'moto' else 'car'
        # every year, best-liked first is the rank; the chart runs newest first like the model pages
        R = {y: i + 1 for i, (y, _, _) in enumerate(rk)}; lo, hi = min(s for _, s, _ in rk), max(s for _, s, _ in rk)
        rows = ''.join(f'<div class="pt"><span>{y}</span><span class="bt"><i style="width:{8 + 92 * (ys[y]["score"] - lo) / max(1, hi - lo):.0f}%"></i></span><b>#{R[y]}</b></div>'
                       for y in sorted(R, reverse=True))
        few = [y for y in sorted(ys, reverse=True) if y not in R]
        chart = (f'<section class="cp5-sec yto-ch"><h2>Every year, ranked.</h2><div class="pts vyr">{rows}</div>'
                 + (f'<p class="yc-cap">Too few videos to rank: {", ".join(map(str, few))}.</p>' if few else '') + '</section>')
        # the most-watched videos across the years (each once)
        vids = {}
        for y, v in ys.items():
            for t in v.get('top') or []:
                if t.get('id') and t['id'] not in vids: vids[t['id']] = t
        top = sorted(vids.values(), key=lambda t: -(t.get('views') or 0))[:6]
        _vw = lambda x: f'{x / 1e6:.1f}M views' if x >= 1e6 else f'{round(x / 1e3)}K views' if x >= 1e3 else f'{x} views'
        vbox = ('<ul class="yto-v">' + ''.join(f'<li><a href="https://www.youtube.com/watch?v={E(t["id"])}" rel="noopener">{E(t["title"])}</a> <small>{_vw(t.get("views") or 0)}</small></li>' for t in top) + '</ul>') if top else ''
        # problems the videos talk about: share of the ranked years' videos naming each topic
        tc, tn = {}, sum(ys[y].get('videos') or 0 for y in R)
        for y in R:
            for k, c in ys[y].get('topics') or []: tc[k] = tc.get(k, 0) + c
        tops = sorted(((k, round(100 * c / tn)) for k, c in tc.items() if tn and c / tn >= .03), key=lambda t: -t[1])[:6]
        pbox = bars_pct(tops) + '<p class="yc-cap">Share of the videos that talk about each problem. A mention is not a failure rate.</p>' if tops else ''
        how = (f'<p class="yc-cap"><b>YouTube buyer score only.</b> We have no owner-complaint data for the {E(nm)} yet, so it has no Lemon Index score. '
               f'We read {n:,} YouTube videos about it ({span}): reviews, owner reports and problem videos. Each model year is scored by how much its videos praise it vs. how much they talk about problems, '
               f'and ranked against the other years: #1 is the year YouTube likes most. A year needs 10 videos to be ranked. This is how people talk about the {noun}, not a failure rate. '
               f'{"Viewers asked us for this " + noun + ", so it has a page before our usual data arrives." if p.get("asked") else ""}</p>')
        go = ''
        _ph = car_href(p['parent']) if p.get('parent') else ''
        if _ph: go += V5_GO('car', E(p.get('parent_name') or {f['id']: f['name'] for f in _YJ}.get(p['parent']) or 'The regular model'), _ph)
        for lab, href in p.get('rel') or []: go += V5_GO('signpost', E(lab), href)
        go += V5_GO('signpost', 'Every motorcycle' if p['kind'] == 'moto' else 'Every car', hub[0])
        boxes = ((V5_BOX('youtube', 'Most-watched videos', vbox, 'videos') if vbox else '') + (V5_BOX('warning', 'Problems the videos mention', pbox, 'problems') if pbox else '')
                 + V5_BOX('info', 'How this score works', how, 'how') + go)
        img = (f'<div class="v5-im">{pimg(ph, valt(ph, nm)).replace(" loading=" + chr(34) + "lazy" + chr(34), "")}</div>{vcredit(ph)}' if ph else '')
        body = ('<div class="pg v5 yto">' + V5_HERO(f'<a href="{hub[0]}">{hub[1]}</a> · {E(p["make"])}', f'{E(nm)}.', f'YouTube buyer score only. No owner-complaint data yet.',
                                                    big=f'<b>{best}</b><span>YouTube&#39;s favorite year</span>', line=f'From {n:,} YouTube videos ({span}).',
                                                    extra=img + f'<button class="btn btn-ghost" type="button" data-share="{E(nm + ": every year ranked by what YouTube owners and reviewers say. Free:")}">Share ↗</button>')   # vis_fixes turns it into the heart + share by the name
                + chart + f'<div class="cpl v5-pl">{boxes}</div>'
                + share_line(f'{nm}: every year ranked by what YouTube owners and reviewers say. Free:') + '</div>'
                + '<style>.yto .yto-ch{max-width:640px;margin-left:auto;margin-right:auto}.yto .pts .pt b{min-width:3em;text-align:right}'
                  '.yto-v{list-style:none;margin:0;padding:0}.yto-v li{padding:8px 0;border-bottom:1px solid var(--line,#e5e5ea);line-height:1.35;overflow-wrap:anywhere}.yto-v li:last-child{border-bottom:0}'
                  '.yto-v small{display:block;color:var(--mute,#6e6e73);margin-top:2px}</style>')
        title = f'{nm} Best & Worst Years: What YouTube Owners Say | The Lemon Index'
        desc = (f'Every {nm} model year ({span}) ranked by {n:,} YouTube reviews and owner videos. YouTube&#39;s favorite year: {best}. '
                'YouTube buyer score only: no owner-complaint data yet.').replace('&#39;', "'")
        page(url, title, desc, body, ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": f'{nm} best years on YouTube', "url": BASE + url}] + vld(ph, url))
        out.append(url)
    print('youtube-only request pages:', len(out), '|', len(YTQ_THIN), 'thin (noindex) |', len(YTQ.get('pages', [])) - len(out), 'requests still waiting for a score')
    return out
