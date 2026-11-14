# 11-12 (Elijah: "the YouTube data stuff seems like it's missing or gone"): what owners and YouTubers praise and complain about, per
# generation, for every car model page's Overview (the M3 performance page's "What owners say on YouTube" block, for every model).
# Input: the generation pulls in <Lemon Index>/data/yt/<study>/ (auto_gens.py: top.json + captions; Civic/F-150 by hand).
# Output: data/yt_buyer.json {model id: [{sid, y0, y1, label, videos, praise: [[topic, %]], trouble: [[topic, %]], top: [{id, title, views, ch}]}]}
# Method = data_perf.yt_study (the M3 page's): a video counts for a topic when a praise (or trouble) word sits within 100 characters of it,
# in the title or the transcript. Toys, games, tuner and dyno videos are skipped. No transcript text is published, only shares and links.
#   py -X utf8 data_yt_buyer.py [fid ...]      (no ids = every model; ids = only those, merged into the existing file)
import json, os, re, sys
import data_perf as DP
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = DP.YT
OUT = os.path.join(HERE, 'data', 'yt_buyer.json')
# what a used-car buyer hears praised (the performance list is about sound and lap times)
PRAISE = {
    'Reliability': r'reliab|dependab|bullet ?proof|last(s|ed)? forever|(200|250|300),?000 miles|high mileage|never (broke|failed|left me)',
    'Fuel economy': r'\bmpg\b|fuel (economy|efficien)|gas mileage|miles per gallon|good on gas|sips',
    'Comfort and ride': r'comfortable|\bcomfort\b|ride (quality|is smooth|comfort)|smooth ride|\bquiet\b',
    'Space and practicality': r'\bspac(e|ious)\b|cargo|trunk|legroom|back ?seat|practical|family',
    'Value for money': r'\bvalue\b|for the money|bang for|affordable|\bcheap\b|bargain|resale',
    'Fun to drive': r'fun to drive|\bhandling\b|steering|\bsporty\b|\bnimble\b',
    'Power': r'\bpower(ful)?\b|accelerat|\btorque\b|\bquick\b|\bfast\b|\bpeppy\b',
    'Tech and features': r'carplay|android auto|infotainment|touch ?screen|safety (features|sense)|adaptive cruise',
    'Looks': r'\blooks\b|\bdesign\b|good.?looking|beautiful|\bstyl(e|ish|ing)\b',
}
Y = lambda a, b: list(range(a, b + 1))
BUYER = r'review|buy|problem|reliab|worth|owner|high.?mileage|long.?term|\d+k miles|years? later|should you|avoid|watch this|things to know|issues|honest'

def study(sid):
    """data_perf.yt_study, tuned for a buyer: topics named by 3%+ of the videos (up to 4 each), and the 3 most-watched videos that are
    reviews, owner reports or problem / buyer guides (not builds, dynos or drag runs: a 500 hp turbo sleeper is no guide to a used Civic)."""
    import collections, glob
    p = os.path.join(SRC, sid, 'top.json')
    if not os.path.exists(os.path.join(SRC, sid, 'videos.json')) or not os.path.exists(p): return None
    g = DP._words(); PR, TR, NP = g['PRAISE'], g['TROUBLE'], g['NOTPROB']
    trouble = {k: v for k, v in g['CAR'].items() if k not in g['NOT_PROBLEMS']}
    vids = [v for v in json.load(open(p, encoding='utf-8')) if not re.search(DP.EXC, v['title'], re.I) and not g['tuned'](v['title'], 400)]
    pc, tc, n = collections.Counter(), collections.Counter(), 0
    for v in vids:
        blob = v['title'] + ' . ' + DP._transcript(sid, v['id']); n += 1
        def near(rx, W):
            for m in re.finditer(rx, blob, re.I):
                w = blob[max(0, m.start() - 100):m.end() + 100]
                if W is TR:
                    if TR.search(w) and not NP.search(w): return True
                elif W.search(w): return True
            return False
        for k, rx in PRAISE.items():
            if near(rx, PR): pc[k] += 1
        for k, rx in trouble.items():
            if near(rx, TR): tc[k] += 1
    pct = lambda c: [[k, round(100 * x / n)] for k, x in c.most_common(4) if n and x / n >= .03]
    bv = [v for v in vids if re.search(BUYER, v['title'], re.I) and not re.search(r'\b(turbo (kit|build)|turbo(charged)? (civic|sleeper)|swap|swapped|build|dyno|drag|sleeper|\d{3,4} ?hp|whp)\b', v['title'], re.I)]
    top = sorted(bv, key=lambda v: -(v.get('views') or 0))[:3]
    return dict(videos=n, praise=pct(pc), trouble=pct(tc), top=[dict(id=v['id'], title=v['title'], views=v.get('views') or 0, ch=v.get('channel') or '') for v in top])

def gens():
    """{fid: [(sid, first year, last year)]} for every site model with generation pulls on disk (same sources as data_yt.py)."""
    have = [f['id'] for f in json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8'))]
    if os.path.exists(os.path.join(HERE, 'data', 'years_new.json')): have += [f['id'] for f in json.load(open(os.path.join(HERE, 'data', 'years_new.json'), encoding='utf-8'))]
    if os.path.exists(os.path.join(HERE, 'data', 'extra_models_new.json')): have += list(json.load(open(os.path.join(HERE, 'data', 'extra_models_new.json'), encoding='utf-8')))   # 11-13: complaints-only models' YouTube pages
    sys.path.insert(0, SRC); cwd = os.getcwd()
    import auto_gens as AG; os.chdir(cwd)
    out = {}
    pre = {'honda-civic': 'civic', 'ford-f-series': 'f150'}
    for fid in have:
        if fid not in AG.T: continue
        for g in AG.T[fid][2]:
            sid = f"{pre.get(fid, AG.slug(fid))}-g{g[0]}"
            if os.path.exists(os.path.join(SRC, sid, 'videos.json')): out.setdefault(fid, []).append((sid, g[1], g[2]))
    st = open(os.path.join(SRC, 'study.py'), encoding='utf-8').read()   # Civic gens were pulled by hand (study.py configs)
    for sid, q in re.findall(r"'(civic-g\d+)': dict\(n=\d+, q=\[(.*?)\]", st):
        ys = sorted({int(y) for y in re.findall(r"'(\d{4}) ", q)})
        if ys and os.path.exists(os.path.join(SRC, sid, 'videos.json')): out.setdefault('honda-civic', []).append((sid, ys[0], ys[-1]))
    os.chdir(SRC); from f150_gens import YEARS as F150; os.chdir(cwd)
    for sid, ys in F150.items():
        if os.path.exists(os.path.join(SRC, sid, 'videos.json')): out.setdefault('ford-f-series', []).append((sid, int(ys[0]), int(ys[-1])))
    return {k: sorted(set(v), key=lambda t: (t[1], t[2])) for k, v in out.items()}

def main(only=()):
    names = {f['id']: f['name'] for p in ('years.json', 'years_new.json') if os.path.exists(os.path.join(HERE, 'data', p))
             for f in json.load(open(os.path.join(HERE, 'data', p), encoding='utf-8'))}
    res = json.load(open(OUT, encoding='utf-8')) if only and os.path.exists(OUT) else {}
    for fid, gs in gens().items():
        if only and fid not in only: continue
        rows = []
        for sid, a, b in gs:
            s = study(sid)
            if not s or not s['videos']: continue
            rows.append(dict(sid=sid, y0=a, y1=b, label=f'{a}–{b}' if a != b else str(a), **s))
        if rows: res[fid] = rows; print(fid, len(rows), 'generations', sum(r['videos'] for r in rows), 'videos', flush=True)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(res), 'models ->', OUT)

if __name__ == '__main__': main(set(sys.argv[1:]))
