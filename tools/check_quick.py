# 11-17 equivalence test for quick mode (quick_mode.py): `build.py --only ...` must write the same bytes, and the same page_dates.json
# entries, as a full build of the same commit, for every page type. Re-run it after any change to build.py's page() or quick_mode.py.
#   py tools/check_quick.py              quick build of the sample pages, then a full build, then compare (one full build: 15-60 min)
#   py tools/check_quick.py --keep       leave the full build's output in docs/ instead of restoring the commit's files
# Run it in your OWN worktree with a clean docs/ and data/page_dates.json (it restores both from git between and after the builds).
# Exit 0 = identical. Prints the timings of both builds.
import json, os, re, subprocess, sys, time, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
PAGES = ['/', '/cars/', '/cars/honda-civic/', '/cars/honda-civic/2016/', '/cars/honda-civic/2016/advanced/', '/brands/honda/', '/jdm/',
         '/jdm/honda-civic-type-r-ek9/', '/uk/', '/uk/honda-civic/', '/check-engine-light/p0420/', '/check-engine-light/p0420/honda-odyssey/',
         '/recalls/', '/recalls/honda/civic/']
GROUPS = ['model:honda-accord']   # a whole model: /cars/honda-accord/* + /embed/cars/honda-accord/*
GROUP_DIRS = ['docs/cars/honda-accord', 'docs/embed/cars/honda-accord']
ROOTS = ('docs/image-sitemap.xml', 'docs/llms.txt', 'docs/robots.txt', 'docs/404.html', 'docs/ads.txt', 'docs/CNAME')   # must match exactly
OWN = ('docs/sitemap.xml', 'docs/robots.txt', 'docs/llms.txt', 'docs/404.html', 'docs/ads.txt', 'docs/CNAME', 'data/page_dates.json')


def sh(*c, check=True):
    r = subprocess.run(list(c), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and r.returncode: sys.exit(f'failed: {" ".join(c)}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}')
    return r


def dirty():
    return [l for l in sh('git', 'status', '--porcelain', '--untracked-files=all', '--', 'docs', 'data/page_dates.json').stdout.splitlines() if l.strip()]


def restore():
    sh('git', 'checkout', '--', 'docs', 'data/page_dates.json'); sh('git', 'clean', '-fdq', '--', 'docs')


def fpath(u): return 'docs' + u + 'index.html' if u.endswith('/') else 'docs' + u


SAMPLE_URLS = {}


def snapshot():
    files = {fpath(u): u for u in PAGES}
    for d in GROUP_DIRS:
        for dp, _, fs in os.walk(d):
            for f in fs:
                p = os.path.join(dp, f).replace('\\', '/'); files[p] = '/' + p[5:-len('index.html')] if p.endswith('index.html') else '/' + p[5:]
    pd = json.load(open('data/page_dates.json', encoding='utf-8'))
    SAMPLE_URLS.update(files); out = {}
    for p, u in files.items():
        b = open(p, 'rb').read() if os.path.exists(p) else None
        out[p] = (hashlib.sha256(b).hexdigest() if b is not None else None, json.dumps(pd.get(u), sort_keys=True))
    sm = open('docs/sitemap.xml', encoding='utf-8').read()
    lm = dict(re.findall(r'<loc>https://lemonindex\.com([^<]+)</loc><lastmod>([^<]+)</lastmod>', sm))
    roots = {r: hashlib.sha256(open(r, 'rb').read()).hexdigest() if os.path.exists(r) else None for r in ROOTS}
    return out, lm, roots, pd


def build(args):
    t = time.time()
    r = subprocess.run([sys.executable, '-X', 'utf8', 'build.py', *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    dt = time.time() - t
    tail = '\n'.join((r.stdout or '').splitlines()[-25:])
    return r.returncode, dt, tail, r.stderr[-3000:]


if dirty(): sys.exit('docs/ or data/page_dates.json has uncommitted changes: run this in a clean worktree (it restores those paths from git)')
fails = []
print('quick build ...', flush=True)
rc, tq, tail, err = build(['--only', *PAGES, *GROUPS])
print(tail)
if rc not in (0, 3): restore(); sys.exit(f'quick build failed (rc {rc}):\n{err}')
if rc == 3: fails.append('quick build reported QUICK-HELD files (see above)')
# quick mode may only touch the pages it was given, the small root files, page_dates.json and docs/assets (the assets copy)
allowed = {fpath(u) for u in PAGES} | set(OWN)
stray = [l[3:] for l in dirty() if not (l[3:] in allowed or l[3:].startswith('docs/assets/') or any(l[3:].startswith(d + '/') for d in GROUP_DIRS))]
if stray: fails.append(f'quick build touched {len(stray)} files outside --only: {stray[:10]}')
quick, qlm, qroots, qpd = snapshot()
restore()
print(f'quick build: {tq:.0f} s. Full build ...', flush=True)
rc, tf, tail, err = build([])
print(tail)
if rc: restore(); sys.exit(f'full build failed (rc {rc}):\n{err}')
full, flm, froots, fpd = snapshot()
if '--keep' not in sys.argv: restore()
for p in sorted(set(quick) | set(full)):
    if quick.get(p) != full.get(p):
        fails.append(f'{p}: bytes {"same" if (quick.get(p) or [None])[0] == (full.get(p) or [None])[0] else "DIFFER"}, page_dates {"same" if (quick.get(p) or [0, 0])[1] == (full.get(p) or [0, 0])[1] else "DIFFER"}')
for r in ROOTS:
    if qroots[r] != froots[r]: fails.append(f'{r} differs')
if set(qlm) != set(flm): fails.append(f'sitemap URLs differ: {len(set(qlm) ^ set(flm))} (e.g. {sorted(set(qlm) ^ set(flm))[:3]})')
sample = set(SAMPLE_URLS.values())
redated = {u for u in fpd if (fpd.get(u) or {}).get('d') != (qpd.get(u) or {}).get('d')} - sample
for u in qlm:   # a lastmod may differ only for a page outside the sample that the full build re-dated (its content changed vs the commit)
    if qlm[u] != flm.get(u) and (u not in redated or u in sample): fails.append(f'sitemap lastmod {u}: quick {qlm[u]} vs full {flm.get(u)}')
print(f'pages the full build re-dated outside the sample (content differs from the commit, not a quick-mode issue): {len(redated)} {sorted(redated)[:8]}')
print(f'\n{len(full)} files compared ({len(PAGES)} sample pages of every type + every page of {", ".join(GROUPS)}), page_dates.json entries and sitemap lastmods.')
print(f'full build {tf:.0f} s, quick build {tq:.0f} s')
if fails:
    print('NOT EQUIVALENT:'); [print('  ', f) for f in fails[:50]]; sys.exit(1)
print('EQUIVALENT: quick mode output is byte-identical to the full build for every compared page')
