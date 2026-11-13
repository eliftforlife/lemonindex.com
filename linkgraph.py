# Internal-link graph + orphan check (11-12, research #6). Runs at the end of every build.py (build.py collects each page's links while
# it writes it, so this takes seconds); `py -X utf8 linkgraph.py` scans docs/ instead (slower, ~1 min) for a check without a build.
# Reports: click depth from the home page (aim: 3 or less), inbound internal links per page, orphans (indexable sitemap pages that no other
# page links to), sitemap pages nothing reaches from /, links to pages that don't exist, and indexable pages missing from the sitemap.
# -> 3 Lemon Index/data/linkgraph/latest.md (+ latest.json with the per-page numbers). Never changes the site.
import collections, datetime, json, os, re, sys
REPORT = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\linkgraph'
BASE = 'https://lemonindex.com'
HREF = re.compile(r'<a\b[^>]*?\shref="(/[^"#?]*)')
NOIX = re.compile(r'<meta name="robots" content="[^"]*noindex')
CANON = re.compile(r'<link rel="canonical" href="([^"]+)"')
FILE = re.compile(r'\.[a-z0-9]{2,5}$', re.I)


def _path_of(fp, out):
    p = '/' + os.path.relpath(fp, out).replace(os.sep, '/')
    return p[:-10] if p.endswith('/index.html') else p


def scan(out='docs'):
    """{path: (links, noindex, canonical url)} for every html page in docs (skips assets/ and embed/)"""
    G = {}
    for dp, dn, fn in os.walk(out):
        dn[:] = [d for d in dn if not (dp == out and d in ('assets', 'embed'))]
        for f in fn:
            if not f.endswith('.html'): continue
            fp = os.path.join(dp, f); t = open(fp, encoding='utf-8', errors='replace').read()
            c = CANON.search(t)
            G[_path_of(fp, out)] = (set(HREF.findall(t)), bool(NOIX.search(t)), c.group(1) if c else '')
    return G


def run(G, urls, out='docs', report=REPORT):
    """G from build.py: {path: (links, noindex, canonical, mtime when page() wrote it)}. Pages a later build step rewrote (brand lists,
    new-model links ...) or wrote without page() are re-read from disk, so the graph matches what's live (a stat per file, ~seconds)."""
    G = dict(G); reread = 0
    for dp, dn, fn in os.walk(out):
        dn[:] = [d for d in dn if not (dp == out and d in ('assets', 'embed'))]
        for f in fn:
            if not f.endswith('.html'): continue
            fp = os.path.join(dp, f); p = _path_of(fp, out); e = G.get(p)
            if e is None or len(e) < 4 or os.path.getmtime(fp) > e[3] + 1:
                t = open(fp, encoding='utf-8', errors='replace').read(); c = CANON.search(t); reread += 1
                G[p] = (set(HREF.findall(t)), bool(NOIX.search(t)), c.group(1) if c else '')
    sm = list(dict.fromkeys(urls)); sms = set(sm)
    inb = collections.Counter(); src = collections.defaultdict(list)
    for p, (ls, *_) in G.items():
        for l in ls:
            if l != p: inb[l] += 1; src[l].append(p)
    depth = {'/': 0}; q = collections.deque(['/'])
    while q:
        p = q.popleft()
        for l in sorted(G.get(p, ((), 0, ''))[0]):
            if l not in depth and l in G: depth[l] = depth[p] + 1; q.append(l)
    idx = lambda p: p in G and not G[p][1] and G[p][2] in ('', BASE + p)   # indexable: no noindex, canonical to itself
    orph = [u for u in sm if inb[u] == 0 and u != '/']
    unreach = [u for u in sm if u not in depth]
    deep = sorted((u for u in sm if depth.get(u, 0) > 3), key=lambda u: -depth[u])
    broken = sorted({l for p, (ls, *_) in G.items() for l in ls if l not in G and not FILE.search(l) and not l.startswith(('/assets/', '/data/', '/embed/'))})
    missing_sm = sorted(p for p in G if idx(p) and p not in sms and p.endswith('/') and p != '/404.html')
    def _ondisk_noix(p):   # 11-13 (N1): pages set to noindex within a second of page() writing them (thin code + advanced pages, /thanks/)
        try: return bool(NOIX.search(open(os.path.join(out, p.strip('/'), 'index.html'), encoding='utf-8', errors='replace').read(12000)))
        except OSError: return False
    missing_sm = [p for p in missing_sm if not _ondisk_noix(p)]
    low = sorted((u for u in sm if inb[u] <= 1 and u != '/'), key=lambda u: (inb[u], u))
    dd = collections.Counter(depth.get(u, -1) for u in sm)
    secs = collections.Counter('/' + u.strip('/').split('/')[0] + '/' if u != '/' else '/' for u in low)
    ib = sorted(inb[u] for u in sm)
    med = ib[len(ib) // 2] if ib else 0
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    L = [f'# Lemon Index internal-link graph ({now})', '',
         f'From `linkgraph.py`, run at the end of every `build.py`. {len(sm):,} sitemap pages, {len(G):,} HTML pages built.', '',
         '## Summary', '',
         f'- **Click depth from the home page:** ' + ', '.join(f'{k} clicks: {dd[k]:,}' for k in sorted(k for k in dd if k >= 0)) + (f', not reachable: {dd[-1]:,}' if dd[-1] else ''),
         f'- **Deeper than 3 clicks:** {len(deep)}', f'- **Orphans** (sitemap pages no other page links to): {len(orph)}',
         f'- **Sitemap pages not reachable from /:** {len(unreach)}', f'- **Weakly linked** (1 inbound link or none): {len(low)}' + (' (' + ', '.join(f'{k} {v}' for k, v in secs.most_common(8)) + ')' if low else ''),
         f'- **Median inbound links per sitemap page:** {med}', f'- **Internal links to pages that don\'t exist:** {len(broken)}',
         f'- **Indexable pages missing from the sitemap:** {len(missing_sm)}', '']
    def lst(title, items, fmt, n=60):
        if not items: return
        L.extend([f'## {title}', ''] + [fmt(u) for u in items[:n]] + ([f'- ... and {len(items) - n} more (latest.json)'] if len(items) > n else []) + [''])
    lst('Orphans', orph, lambda u: f'- {u}')
    lst('Deeper than 3 clicks', deep, lambda u: f'- {u} ({depth[u]} clicks)')
    lst('Not reachable from the home page', unreach, lambda u: f'- {u}')
    lst('Broken internal links', broken, lambda u: f'- {u} (linked from {len(src[u])} pages, e.g. {src[u][0]})')
    lst('Weakly linked pages', low, lambda u: f'- {u}: {inb[u]} inbound' + (f' (from {src[u][0]})' if src[u] else ''))
    lst('Indexable pages missing from the sitemap', missing_sm, lambda u: f'- {u}')
    os.makedirs(report, exist_ok=True)
    open(os.path.join(report, 'latest.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    json.dump({'at': now, 'pages': len(sm), 'depth': dict(sorted((str(k), v) for k, v in dd.items())), 'orphans': orph, 'deep': {u: depth[u] for u in deep}, 'unreachable': unreach,
               'broken': broken, 'weak': {u: inb[u] for u in low}, 'missing_from_sitemap': missing_sm, 'median_inbound': med,
               'inbound': {u: inb[u] for u in sm}, 'depth_by_page': {u: depth.get(u) for u in sm}},
              open(os.path.join(report, 'latest.json'), 'w', encoding='utf-8'), separators=(',', ':'))
    return (f'linkgraph: {len(sm)} pages ({reread} re-read from disk), depth<=3 {sum(v for k, v in dd.items() if 0 <= k <= 3)}, deeper {len(deep)}, orphans {len(orph)}, '
            f'unreachable {len(unreach)}, weak {len(low)}, broken {len(broken)}, median inbound {med} -> {report}\\latest.md')


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sm = re.findall(r'<loc>' + re.escape(BASE) + r'([^<]+)</loc>', open('docs/sitemap.xml', encoding='utf-8').read())
    print(run({}, sm))   # every page read from disk
