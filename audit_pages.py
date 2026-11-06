# SEO page audit (11-06). Walks docs/ (or the Meal Monster deploy with an argument) and reports title, description, H1, canonical, alt text and size problems.  py audit_pages.py [root]
import collections, glob, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
R = sys.argv[1] if len(sys.argv) > 1 else 'docs'; T = collections.defaultdict(list); D = collections.defaultdict(list); P = collections.Counter(); EX = collections.defaultdict(list); sizes = []
for f in glob.glob(os.path.join(R, '**', 'index.html'), recursive=True):
    if '.git' in f or 'node_modules' in f: continue
    s = open(f, encoding='utf-8', errors='replace').read(); u = f[len(R):].replace('\\', '/').replace('index.html', ''); sizes.append((len(s), u)); noi = 'noindex' in s[:3000]
    if noi: continue
    def hit(k):
        P[k] += 1; len(EX[k]) < 4 and EX[k].append(u)
    t = re.search(r'<title>(.*?)</title>', s, re.S); d = re.search(r'<meta name="description" content="(.*?)"', s)
    if not t: hit('no title')
    else:
        T[t.group(1)].append(u)
        if len(t.group(1)) > 65: hit('title over 65')
        if len(t.group(1)) < 25: hit('title under 25')
    if not d: hit('no description')
    else:
        D[d.group(1)].append(u)
        if len(d.group(1)) > 165: hit('description over 165')
        if len(d.group(1)) < 70: hit('description under 70')
    h1 = len(re.findall(r'<h1[\s>]', s))
    if h1 != 1: hit(f'{h1} H1s')
    if 'rel="canonical"' not in s: hit('no canonical')
    for m in re.finditer(r'<img\b[^>]*>', s):
        if not re.search(r'\balt="[^"]+"', m.group(0)) and 'gh-brand' not in s[max(0, m.start() - 40):m.start()] and 'width="24"' not in m.group(0): hit('image without alt')
    if 'application/ld+json' not in s: hit('no schema')
    body = re.sub(r'<script.*?</script>|<style.*?</style>|<header.*?</header>|<footer.*?</footer>', '', s, flags=re.S); words = len(re.sub(r'<[^>]+>', ' ', body).split())
    if words < 120: hit('under 120 words')
print('pages', len(sizes), 'avg KB', sum(a for a, _ in sizes) // max(1, len(sizes)) // 1024, 'largest', sorted(sizes)[-3:])
for k, v in P.most_common(): print(f'{v:6} {k}', EX[k])
print('duplicate titles', sum(1 for v in T.values() if len(v) > 1), [v[:2] for v in T.values() if len(v) > 1][:4]); print('duplicate descriptions', sum(1 for v in D.values() if len(v) > 1), [v[:2] for v in D.values() if len(v) > 1][:3])
