# 11-17 batched deploys for lemonindex.com (Elijah: "why do full rebuild shouldn't we only do that when necessary to save credits").
# Agents don't build or push themselves any more: they commit their SOURCE change to a branch (or write a patch) and queue it. One runner
# takes site.lock once, applies every queued change onto origin/main, runs ONE build (quick mode when every item says which pages it
# touches), checks it, pushes, runs IndexNow, smoke-tests the live pages and marks each item shipped with the commit id.
#
#   py deploy_queue.py add --branch <branch> --title "What changed" [--only <pages/groups>] [--pages /a/ /b/] [--by <agent>]
#   py deploy_queue.py add --patch <file.patch> --title "..." [...]
#   py deploy_queue.py list                  what's queued, and the last 15 results
#   py deploy_queue.py drop <id>             take an item out of the queue
#   py deploy_queue.py run [--dry-run]       ship everything queued (--dry-run: build + check, no commit/push)
#
# --only: the item touches only these pages (same tokens as `build.py --only`, see quick_mode.py: /path/, /path/*, home, model:<id>,
#   brand:<make>, assets). Leave it out when the change touches shared data, scoring, nav or templates: then the batch gets a full build.
# --pages: live pages to smoke-test at 375 and 1440 px after the push (/, /cars/ and the 2016 Civic are always tested).
# Only source files ship from an item: anything it has under docs/ or data/page_dates.json is ignored (the runner's build makes those).
# An item that doesn't apply cleanly onto origin/main, or that breaks the build, is skipped and reported; the rest still ship.
# Queue + logs: 3 Lemon Index/data/deploy_queue/ (queue.json, runs/<time>.log, shots/<time>/). The runner works in its own worktree,
# C:\Users\elift\Code\lemon-queue (made on first run, data/cache linked to the main repo's), which it resets to origin/main every run.
import argparse, datetime, json, os, re, shutil, subprocess, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import quick_mode as QM   # the --only parser (no side effects on import)
REPO = r'C:\Users\elift\Code\lemonindex-site'
WT = r'C:\Users\elift\Code\lemon-queue'
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
LOCK = os.path.join(LEMON, 'data', 'yt', 'site.lock')
QD = os.path.join(LEMON, 'data', 'deploy_queue'); QF = os.path.join(QD, 'queue.json'); QLOCK = os.path.join(QD, 'queue.lock')
SMOKE_ALWAYS = ['/', '/cars/', '/cars/honda-civic/2016/']
ADV = 'docs/cars/honda-civic/2016/advanced/index.html'
SIGN = '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'
MAX_BUILDS = 5   # a run that needs more builds than this (several broken items) leaves the rest queued
NOW = lambda: datetime.datetime.now().isoformat(timespec='seconds')
LOG = None


def say(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True)
    if LOG: LOG.write(s + '\n'); LOG.flush()


def run(*c, cwd=WT, check=True, quiet=False):
    r = subprocess.run(list(c), cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if not quiet or r.returncode: say('$', ' '.join(c)[:300], '->', r.returncode, ((r.stdout or '')[-800:] + (r.stderr or '')[-800:]).strip()[:1600])
    if check and r.returncode: raise RuntimeError(f'failed: {" ".join(c)[:200]}')
    return r


def alive(pid):
    r = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/NH'], capture_output=True, text=True)
    return 'python' in r.stdout.lower()


def take(lock, wait=True, why=''):
    t0 = time.time(); shown = False
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.write(fd, str(os.getpid()).encode()); os.close(fd); return time.time() - t0
        except FileExistsError:
            try:
                pid = int(open(lock).read().strip() or 0)
                if pid and not alive(pid): os.remove(lock); continue
            except (ValueError, OSError): pass
            if not wait: return None
            if not shown and why: say(f'waiting for {why} ...'); shown = True
            time.sleep(1)


def give(lock):
    try:
        if open(lock).read().strip() == str(os.getpid()): os.remove(lock)
    except OSError: pass


class Queue:
    """queue.json under its own short lock, so agents can add while a run is going"""
    def __enter__(self):
        os.makedirs(QD, exist_ok=True); take(QLOCK)
        self.items = json.load(open(QF, encoding='utf-8')) if os.path.exists(QF) else []
        return self
    def __exit__(self, *a):
        try:
            if a[0] is None:
                json.dump(self.items, open(QF + '.tmp', 'w', encoding='utf-8'), indent=1, ensure_ascii=False); os.replace(QF + '.tmp', QF)
        finally: give(QLOCK)


def update(iid, **kw):
    with Queue() as q:
        for it in q.items:
            if it['id'] == iid: it.update(kw)


# ---------- add / list / drop ----------
def cmd_add(a):
    it = dict(id=datetime.datetime.now().strftime('%m%d-%H%M%S') + f'-{os.getpid() % 1000:03d}', added=NOW(), by=a.by or os.environ.get('USERNAME', '?'),
              title=a.title.strip(), only=[QM.unmsys(t) for t in a.only] if a.only else None, pages=[q for q in (QM.unmsys(p) for p in (a.pages or [])) if q.startswith('/')], status='queued')
    if a.branch:
        r = run('git', 'rev-parse', '--verify', a.branch + '^{commit}', cwd=REPO, check=False, quiet=True)
        if r.returncode: sys.exit(f'no such branch/commit: {a.branch} (commit your change first; branches are shared by every worktree)')
        it.update(kind='branch', branch=a.branch, sha=r.stdout.strip())
        base = run('git', 'merge-base', it['sha'], 'origin/main', cwd=REPO, quiet=True).stdout.strip()
        files = run('git', 'diff', '--name-only', base, it['sha'], cwd=REPO, quiet=True).stdout.split()
    else:
        os.makedirs(os.path.join(QD, 'patches'), exist_ok=True)
        dst = os.path.join(QD, 'patches', it['id'] + '.patch'); shutil.copyfile(a.patch, dst)
        it.update(kind='patch', patch=dst)
        files = [m for m in re.findall(r'^\+\+\+ b/(\S+)', open(dst, encoding='utf-8', errors='replace').read(), re.M)]
    src = [f for f in files if not (f.startswith('docs/') or f == 'data/page_dates.json')]
    if not src: sys.exit('that change has no source files (only built docs/ or page_dates.json): nothing to queue')
    it['files'] = src[:200]
    if a.only:   # the same parser build.py uses, so a typo fails now and not in the runner
        try: QM.parse(a.only)
        except ValueError as e: sys.exit(str(e))
    with Queue() as q: q.items.append(it)
    print(f'queued {it["id"]}: {it["title"]} ({len(src)} source files; {"quick: " + " ".join(a.only) if a.only else "needs a full build"})')
    print('Ship the queue with: py deploy_queue.py run')


def cmd_list(a):
    with Queue() as q: items = q.items
    qd = [i for i in items if i['status'] in ('queued', 'running')]
    print(f'{len(qd)} queued:')
    for i in qd: print(f'  {i["id"]}  {i["status"]:7} {i["title"][:70]}  [{"only " + " ".join(i["only"]) if i.get("only") else "full build"}] by {i["by"]}')
    print('last results:')
    for i in [i for i in items if i['status'] not in ('queued', 'running')][-15:]:
        print(f'  {i["id"]}  {i["status"]:8} {i.get("commit", "")[:11]:11} {i["title"][:60]}  {i.get("note", "")[:90]}')


def cmd_drop(a):
    with Queue() as q:
        for i in q.items:
            if i['id'] == a.id and i['status'] == 'queued': i['status'] = 'dropped'; i['note'] = f'dropped {NOW()}'; print('dropped', a.id); return
    print('no queued item', a.id)


# ---------- the runner ----------
def ensure_wt():
    if not os.path.isdir(WT):
        run('git', 'worktree', 'add', '--detach', WT, 'origin/main', cwd=REPO)
    cache = os.path.join(WT, 'data', 'cache')
    if not os.path.exists(cache):
        subprocess.run(['cmd', '/c', 'mklink', '/J', cache, os.path.join(REPO, 'data', 'cache')], capture_output=True)
    if not os.path.exists(os.path.join(cache, 'vehicles.csv')): raise RuntimeError('data/cache/vehicles.csv missing in the runner worktree (Specs & engines tab would drop)')


def reset(base):
    run('git', 'reset', '--hard', base, quiet=True); run('git', 'clean', '-fdq', '--', 'docs', 'assets', quiet=True)


def item_patch(it, base):
    """the item's source change as a patch against its merge base (built docs/ and page_dates.json left out)"""
    if it['kind'] == 'patch': return open(it['patch'], 'rb').read(), ['--exclude=docs/*', '--exclude=data/page_dates.json']
    mb = run('git', 'merge-base', it['sha'], base, quiet=True).stdout.strip()
    r = subprocess.run(['git', 'diff', '--binary', mb, it['sha'], '--', '.', ':(exclude)docs', ':(exclude)data/page_dates.json'], cwd=WT, capture_output=True)
    if r.returncode: raise RuntimeError(r.stderr.decode('utf-8', 'replace')[-300:])
    return r.stdout, []   # bytes, so a file in any encoding applies unchanged


def apply_items(items, base):
    """reset to base and apply the items one by one, a commit each; returns (applied, [(item, why)] that didn't apply)"""
    reset(base); ok, bad = [], []
    for it in items:
        try: diff, ex = item_patch(it, base)
        except RuntimeError as e: bad.append((it, f'cannot read the change: {e}')); continue
        pf = os.path.join(QD, 'cur.patch')
        open(pf, 'wb').write(diff)
        r = run('git', 'apply', '--3way', '--index', *ex, pf, check=False, quiet=True)
        if r.returncode:
            run('git', 'reset', '--hard', 'HEAD', quiet=True); run('git', 'clean', '-fdq', '--', 'docs', 'assets', quiet=True)
            bad.append((it, 'does not apply onto origin/main: ' + ((r.stderr or r.stdout).strip().splitlines() or ['?'])[-1][:200])); continue
        if not run('git', 'diff', '--cached', '--name-only', quiet=True).stdout.strip():
            bad.append((it, 'nothing left to apply (already on main?)')); continue
        pyc = [f for f in run('git', 'diff', '--cached', '--name-only', quiet=True).stdout.split() if f.endswith('.py') and os.path.exists(os.path.join(WT, f))]
        if pyc:
            r = run(sys.executable, '-m', 'py_compile', *pyc, check=False, quiet=True)
            if r.returncode:
                run('git', 'reset', '--hard', 'HEAD', quiet=True)
                bad.append((it, 'Python syntax error: ' + (r.stderr or '').strip().splitlines()[-1][:200])); continue
        run('git', 'commit', '-q', '-m', f'{it["title"]}\n\nQueued by {it["by"]} (deploy_queue {it["id"]}){SIGN}', quiet=True)
        ok.append(it)
    return ok, bad


def build(items):
    """one build of the current tree: quick mode if every item named its pages, else full; a quick build that finds changes outside
    its pages (exit 3) is redone as a full build. Returns (ok, mode, seconds, output tail)"""
    only = [t for it in items for t in (it.get('only') or [])] if items and all(it.get('only') for it in items) else None
    for mode in (['quick', 'full'] if only else ['full']):
        args = ['--only', *dict.fromkeys(only)] if mode == 'quick' else []
        t = time.time(); r = subprocess.run([sys.executable, '-X', 'utf8', 'build.py', *args], cwd=WT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        dt = time.time() - t; out = (r.stdout or '') + '\n' + (r.stderr or '')
        say(f'{mode} build rc {r.returncode} in {dt:.0f} s')
        if mode == 'quick' and r.returncode == 3:
            say('quick build found changes outside the listed pages, so a full build follows:', ' '.join(l.strip() for l in out.splitlines() if l.startswith('    '))[:600])
            reset_docs(); continue
        return r.returncode == 0, mode, dt, out[-4000:]
    return False, 'full', 0, ''


def reset_docs():
    run('git', 'checkout', '--', 'docs', 'data/page_dates.json', quiet=True); run('git', 'clean', '-fdq', '--', 'docs', quiet=True)


def solve(base, items, state):
    """largest set of items that applies and builds; items that break the build are found by halving and reported.
    state: builds used, the set the tree was last built with, failures."""
    def attempt(its):
        if state['builds'] >= MAX_BUILDS: return None
        ok, bad = apply_items(its, base)
        for it, why in bad: state['bad'][it['id']] = why
        its = [i for i in its if i['id'] not in state['bad']]
        if not its: state['last'] = (); return True
        state['builds'] += 1; good, mode, dt, tail = build(its)
        state['last'] = tuple(i['id'] for i in its) if good else None; state['mode'] = mode; state['secs'] = dt
        if not good:
            state['tails'].append(tail); say('build failed:', '\n'.join(tail.strip().splitlines()[-6:]))
        return good
    def go(good, cand):
        cand = [c for c in cand if c['id'] not in state['bad']]
        if not cand: return good
        r = attempt(good + cand)
        if r is None: state['left'] += cand; return good
        if r: return good + [c for c in cand if c['id'] not in state['bad']]
        if len(cand) == 1:
            state['bad'][cand[0]['id']] = 'breaks the build: ' + ' | '.join(state['tails'][-1].strip().splitlines()[-3:])[:400]; return good
        h = len(cand) // 2
        g = go(good, cand[:h]); return go(g, cand[h:])
    final = go([], items)
    if final and state['last'] != tuple(i['id'] for i in final):   # the tree was last built with another set: build the winners again
        state['last'] = None
        if attempt(final) is not True: return []
    return final


def link_check():
    """internal links in every page this build changed must point at a page or file that exists (links already broken before are ignored)"""
    st = run('git', 'status', '--porcelain', '--untracked-files=all', '--', 'docs', quiet=True).stdout.splitlines()
    pages = [l[3:].strip('"') for l in st if l[3:].endswith('.html')]
    href = re.compile(r'<a\b[^>]*?\shref="(/[^"#?]*)')
    seen = {}
    def exists(u):
        if u not in seen:
            p = os.path.join(WT, 'docs', u.lstrip('/'))
            seen[u] = os.path.isfile(p) or os.path.isfile(os.path.join(p, 'index.html'))
        return seen[u]
    broken = []
    for p in pages:
        try: bad = {u for u in href.findall(open(os.path.join(WT, p), encoding='utf-8', errors='replace').read()) if not exists(u)}
        except OSError: continue
        if not bad: continue
        old = run('git', 'show', f'HEAD:{p}', check=False, quiet=True)   # only for pages with a dead link: was it already there?
        bad -= set(href.findall(old.stdout)) if old.returncode == 0 else set()
        broken += [f'{p[4:]} -> {u}' for u in sorted(bad)]
    return len(pages), broken


def wait_live(pages, timeout=900):
    """GitHub Pages is live when each page's bytes match the build (cache-busting query); returns the pages still stale"""
    left = list(pages); t0 = time.time()
    while left and time.time() - t0 < timeout:
        for u in list(left):
            f = os.path.join(WT, 'docs', u.lstrip('/'), 'index.html') if u.endswith('/') else os.path.join(WT, 'docs', u.lstrip('/'))
            try:
                want = open(f, 'rb').read().replace(b'\r\n', b'\n')
                got = urllib.request.urlopen(urllib.request.Request(f'https://lemonindex.com{u}?dq={int(time.time())}', headers={'User-Agent': 'lemonindex-deploy-check'}), timeout=30).read().replace(b'\r\n', b'\n')
                if got == want: left.remove(u)
            except Exception: pass
        if left: time.sleep(20)
    return left


def cmd_run(a):
    global LOG
    os.makedirs(os.path.join(QD, 'runs'), exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'); LOG = open(os.path.join(QD, 'runs', stamp + '.log'), 'w', encoding='utf-8')
    with Queue() as q:
        for i in q.items:   # a runner that was killed leaves its items 'running': queue them again
            if i['status'] == 'running' and not alive(i.get('pid', 0)): i['status'] = 'queued'
        items = [i for i in q.items if i['status'] == 'queued']
        for i in items: i['status'] = 'running'; i['run'] = stamp; i['pid'] = os.getpid()
    if not items: say('queue is empty'); return 0
    say(f'run {stamp}: {len(items)} item(s):', '; '.join(f'{i["id"]} {i["title"][:50]}' for i in items))
    result = {}; state = dict(builds=0, last=None, bad={}, tails=[], left=[], mode='', secs=0)
    held = None; commit = None; smoke_pages = []
    try:
        ensure_wt()
        held = take(LOCK, why='site.lock'); say(f'site.lock held (pid {os.getpid()}) after {held:.0f} s')
        run('git', 'fetch', '-q', 'origin', quiet=True)
        base = run('git', 'rev-parse', 'origin/main', quiet=True).stdout.strip()
        final = solve(base, items, state)
        for iid, why in state['bad'].items(): result[iid] = ('skipped', why)
        for it in state['left']: result[it['id']] = ('queued', 'left for the next run (build limit reached)')
        if not final: raise RuntimeError('nothing left to ship')
        if not os.path.isfile(os.path.join(WT, ADV)) or 'url=/cars/honda-civic/2016/"' not in open(os.path.join(WT, ADV), encoding='utf-8').read():   # 11-25: Advanced pages are redirect stubs now (advanced_pages.py ADV_REDIRECTS)
            raise RuntimeError('the old Advanced page is not a redirect stub to its year page: ' + ADV)
        n, broken = link_check(); say(f'link check: {n} changed pages, {len(broken)} new broken links', broken[:10])
        if broken: raise RuntimeError(f'{len(broken)} new broken links, e.g. {broken[:3]}')
        st = run('git', 'status', '--porcelain', '--untracked-files=all', quiet=True).stdout.splitlines()
        paths = [l[3:].strip('"') for l in st if l[3:].startswith(('docs/', 'assets/')) or l[3:].strip('"') == 'data/page_dates.json']
        other = [l[3:] for l in st if l[3:].strip('"') not in paths]
        if other: say('left uncommitted (written by the build outside docs/assets):', other[:10])
        smoke_pages = list(dict.fromkeys(SMOKE_ALWAYS + [p for it in final for p in it.get('pages', [])]))
        if a.dry_run:
            say(f'DRY RUN: would commit {len(paths)} built files and push {len(final)} item(s):', [i['id'] for i in final])
            for it in final: result[it['id']] = ('queued', f'dry run {stamp} built OK ({state["mode"]})')
            return 0
        for i in range(0, len(paths), 200): run('git', 'add', '--', *paths[i:i + 200], quiet=True)
        if run('git', 'diff', '--cached', '--name-only', quiet=True).stdout.strip():
            run('git', 'commit', '-q', '-m', f'Built pages: {"; ".join(i["title"] for i in final)[:200]} (deploy_queue {stamp}, {state["mode"]} build){SIGN}', quiet=True)
        run('git', 'fetch', '-q', 'origin', quiet=True)
        if run('git', 'rev-parse', 'origin/main', quiet=True).stdout.strip() != base:
            raise RuntimeError('origin/main moved during the build (someone pushed without site.lock): nothing pushed, the items stay queued')
        run('git', 'push', '-q', 'origin', 'HEAD:main')
        commit = run('git', 'rev-parse', 'HEAD', quiet=True).stdout.strip()
        src = {it['id']: c for it in final for c in [run('git', 'log', '-1', '--format=%H', '--grep', f'deploy_queue {it["id"]}', quiet=True).stdout.strip()]}
        say('PUSHED', commit, f'({state["mode"]} build, {state["secs"]:.0f} s)')
        for it in final: result[it['id']] = ('shipped', f'{state["mode"]} build; source {src.get(it["id"], "")[:11]}; built {commit[:11]}')
    except Exception as e:
        say('RUN STOPPED:', e)
        for it in items:
            if it['id'] not in result: result[it['id']] = ('queued', f'run {stamp} stopped before shipping: {str(e)[:200]}')
    finally:
        if held is not None: give(LOCK); say('site.lock released')
        for iid, (st_, note) in result.items(): update(iid, status=st_, note=note, **({'commit': commit} if st_ == 'shipped' else {}))
        for it in items:
            if it['id'] not in result: update(it['id'], status='queued', note=f'run {stamp} did not reach it')
    if commit:
        r = run(sys.executable, '-X', 'utf8', 'indexnow.py', check=False, quiet=True); say('indexnow:', ((r.stdout or r.stderr).strip().splitlines() or ['?'])[-1][:120])
        stale = wait_live(smoke_pages); say('live:', 'every smoke page serves the new build' if not stale else f'still stale after 15 min: {stale}')
        shots = os.path.join(QD, 'shots', stamp)
        r = subprocess.run(['node', os.path.join(WT, 'tools', 'smoke_live.mjs'), shots, *smoke_pages], cwd=WT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        say('smoke test (375 + 1440):\n' + (r.stdout or r.stderr).strip()); say('screenshots:', shots)
        if r.returncode: say('SMOKE TEST FAILED: the batch is live; fix forward')
    say('\nresult:'); [say(f'  {iid} {s}: {n}') for iid, (s, n) in result.items()]
    return 0 if commit and not state['bad'] else 1


def main():
    p = argparse.ArgumentParser(description='lemonindex.com deploy queue'); sp = p.add_subparsers(dest='cmd', required=True)
    x = sp.add_parser('add'); g = x.add_mutually_exclusive_group(required=True); g.add_argument('--branch'); g.add_argument('--patch')
    x.add_argument('--title', required=True); x.add_argument('--only', nargs='+'); x.add_argument('--pages', nargs='+'); x.add_argument('--by')
    sp.add_parser('list'); d = sp.add_parser('drop'); d.add_argument('id')
    r = sp.add_parser('run'); r.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    sys.exit({'add': cmd_add, 'list': cmd_list, 'drop': cmd_drop, 'run': cmd_run}[a.cmd](a) or 0)


if __name__ == '__main__':
    main()
