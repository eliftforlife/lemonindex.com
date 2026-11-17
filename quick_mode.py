# 11-17 quick mode for build.py (Elijah: "why do full rebuild, shouldn't we only do that when necessary to save credits").
#   py build.py --only / /cars/honda-civic/ model:honda-civic brand:honda "/uk/*" assets
# Runs the normal build (every data file loads and every URL list fills, so the sitemap, page dates and links come out exactly as in a
# full build) but page() returns straight away for any page outside --only, and only the pages inside it are written. Nothing else in
# docs/ is rewritten: every other file the build would write is compared with what's on disk instead, and if any of them would change,
# the build ends with exit code 3 and lists them ("QUICK-HELD"): the change reaches past the pages you named, so run a full build.
# Equivalence with a full build: tools/check_quick.py.
#
# --only tokens:
#   /path/            that one page (a missing trailing slash is added: /uk -> /uk/)
#   /path/*           every page under it, the page itself included (/cars/honda-civic/* = the model page, its years, advanced, ...)
#   home              /
#   model:<id>        /cars/<id>/* and /embed/cars/<id>/*      (id as in the URL, e.g. honda-civic)
#   brand:<make>      /brands/<make>/*                          (e.g. brand:honda, brand:mercedes-benz)
#   assets            no pages: only the assets/ -> docs/assets/ copy (always done in quick mode; files copy only when they differ)
import builtins, io, locale, os, re, shutil, sys, tempfile

ON = False
EXACT, PREFIX = set(), []
WROTE, NEWPAGES, SKIPPED = [], [], []
_REAL_OPEN = builtins.open
_ROOT = os.getcwd()
_DOCS = _CACHE = _TMP = _RES = None
_PASS = 0   # >0 while quick mode itself copies assets (writes go straight through)


def _norm(p):
    p = '/' + p.strip().lstrip('/')
    if not p.endswith('/') and '.' not in p.rsplit('/', 1)[-1]: p += '/'
    return p


def unmsys(t):
    """Git Bash turns an argument like /uk/ into C:/Program Files/Git/uk/: undo that (PowerShell passes it as typed)"""
    m = re.match(r'^[A-Za-z]:/(?:Program Files/)?Git(/.*)$', t.replace(chr(92), '/'))
    return m.group(1) if m else t


def parse(toks):
    """--only tokens -> (exact paths, prefixes); ValueError on a token it doesn't know"""
    ex, pre = set(), []
    toks = [unmsys(t) for t in toks]
    if not toks: raise ValueError('--only needs at least one page, prefix or group (see quick_mode.py)')
    for t in toks:
        if t == 'home': ex.add('/')
        elif t == 'assets': pass
        elif t.startswith('model:') and t[6:].strip('/'): pre.extend([f'/cars/{t[6:].strip("/")}/', f'/embed/cars/{t[6:].strip("/")}/'])
        elif t.startswith('brand:') and t[6:].strip('/'): pre.append(f'/brands/{t[6:].strip("/").lower().replace(" ", "-")}/')
        elif t.startswith('/') and t.endswith('*'): pre.append(_norm(t[:-1]))
        elif t.startswith('/'): ex.add(_norm(t))
        else: raise ValueError(f'--only: unknown token {t!r} (use /path/, /path/*, home, model:<id>, brand:<make>, assets)')
    return ex, pre


def setup(out='docs', argv=None):
    """parse --only from argv (default sys.argv) and, if given, gate file writes; a normal build is left untouched"""
    global ON, _DOCS, _CACHE, _TMP, _RES
    argv = sys.argv if argv is None else argv
    if '--only' not in argv: return False
    try: ex, pre = parse([t for t in argv[argv.index('--only') + 1:] if not t.startswith('--')])
    except ValueError as e: raise SystemExit(f'build.py {e}')
    EXACT.update(ex); PREFIX.extend(pre); ON = True
    _DOCS = os.path.join(_ROOT, out); _CACHE = os.path.join(_ROOT, 'data', 'cache'); _TMP = tempfile.gettempdir()
    _RES = os.path.join(_ROOT, 'assets', 'r')
    shutil.rmtree(os.path.join(_CACHE, 'quick_held'), ignore_errors=True)
    builtins.open = _gate
    print('QUICK mode: only', ' '.join(sorted(EXACT) + [p + '*' for p in PREFIX]) or '(assets only)', flush=True)
    return True


def want(path):
    """True if --only covers this page (always True in a full build)"""
    if not ON: return True
    return path in EXACT or any(path.startswith(p) for p in PREFIX)


def _url_of(rel):   # docs-relative file -> page URL ('cars/x/index.html' -> '/cars/x/')
    rel = rel.replace('\\', '/')
    return '/' + rel[:-len('index.html')] if rel.endswith('index.html') else '/' + rel


def _inside(p, root): return p == root or p.startswith(root + os.sep)


VIRT = {}   # absolute path -> the bytes the build wrote there (held, not on disk); later reads of that path see these bytes


class _Sink(io.BytesIO):
    """stands in for a write outside --only: nothing reaches the disk. The bytes go to VIRT (so a later step that reads the file back
    and adds to it, like search_go.py on find-go.json, sees what the build wrote), and finish() compares the last version with the disk"""
    def __init__(self, path, append, quiet=False):
        super().__init__(); self._p, self._a, self._q = path, append, quiet
    def close(self):
        if not self.closed and self._q: SKIPPED.append(self._p)
        elif not self.closed:
            base = b''
            if self._a:
                base = VIRT.get(self._p)
                if base is None:
                    try:
                        with _REAL_OPEN(self._p, 'rb') as fh: base = fh.read()
                    except OSError: base = b''
            VIRT[self._p] = base + self.getvalue()
        super().close()


def _gate(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    if _PASS or isinstance(file, int):
        return _REAL_OPEN(file, mode, buffering, encoding, errors, newline, closefd, opener)
    if not any(c in mode for c in 'wax+'):
        p = os.path.abspath(os.fspath(file))
        if p not in VIRT: return _REAL_OPEN(file, mode, buffering, encoding, errors, newline, closefd, opener)
        bio = io.BytesIO(VIRT[p])
        return bio if 'b' in mode else io.TextIOWrapper(bio, encoding=encoding or locale.getpreferredencoding(False), errors=errors, newline=newline)
    p = os.path.abspath(os.fspath(file))
    through = (_inside(p, _CACHE) or _inside(p, _TMP) or _inside(p, _RES) or p == os.path.join(_ROOT, 'data', 'page_dates.json'))
    quiet = False
    if not through and _inside(p, _DOCS):
        rel = os.path.relpath(p, _DOCS)
        if os.sep not in rel and rel != 'index.html': through = True   # sitemap.xml, robots.txt, llms.txt, 404.html, CNAME ...
        elif want(_url_of(rel)):
            through = True; WROTE.append(_url_of(rel))
        elif rel.endswith('.html'):
            # another page: a post-build edit (noindex tag, extra links ...) of a page this run didn't rebuild. The edit was made to the
            # page as it was last built, so its result says nothing about this change: dropped, not reported
            quiet = True
    if through: return _REAL_OPEN(file, mode, buffering, encoding, errors, newline, closefd, opener)
    sink = _Sink(p, 'a' in mode, quiet)
    if 'b' in mode: return sink
    return io.TextIOWrapper(sink, encoding=encoding or locale.getpreferredencoding(False), errors=errors, newline=newline, write_through=True)


def _held():
    """files outside --only whose final would-be bytes differ from the disk (CRLF vs LF ignored: git stores docs/ with LF, a checkout has CRLF)"""
    lf = lambda b: b.replace(bytes([13, 10]), bytes([10]))
    out = []
    for p, new in VIRT.items():
        try:
            with _REAL_OPEN(p, 'rb') as fh: old = fh.read()
        except OSError: old = None
        if old is None or lf(old) != lf(new):
            rel = os.path.relpath(p, _ROOT).replace(os.sep, '/'); out.append(rel)
            try:   # the file as the build would have written it, to diff by hand
                keep = os.path.join(_CACHE, 'quick_held', rel); os.makedirs(os.path.dirname(keep), exist_ok=True)
                with _REAL_OPEN(keep, 'wb') as fh: fh.write(new)
            except OSError: pass
    return out


def copy_assets(src, dst):
    """quick mode's assets/ -> docs/assets/: same result as shutil.copytree(..., dirs_exist_ok=True), but only files that differ are copied"""
    global _PASS
    n = 0; _PASS += 1
    try:
        for d, _, fs in os.walk(src):
            od = os.path.join(dst, os.path.relpath(d, src)); os.makedirs(od, exist_ok=True)
            for f in fs:
                a, b = os.path.join(d, f), os.path.join(od, f)
                try:
                    sa, sb = os.stat(a), os.stat(b)
                    if sa.st_size == sb.st_size and int(sa.st_mtime) == int(sb.st_mtime): continue
                    with _REAL_OPEN(a, 'rb') as x, _REAL_OPEN(b, 'rb') as y:
                        if x.read() == y.read(): continue
                except OSError: pass
                shutil.copy2(a, b); n += 1
    finally: _PASS -= 1
    return n


def page_new(path, existed):
    if ON and not existed: NEWPAGES.append(path)


def finish():
    """print what quick mode wrote and held back; exit 3 if anything outside --only would have changed"""
    if not ON: return
    builtins.open = _REAL_OPEN
    w = sorted(set(WROTE)); h = sorted(set(_held()))
    print(f'QUICK wrote {len(w)} pages:', ' '.join(w[:40]) + (' ...' if len(w) > 40 else ''), f'({len(SKIPPED)} post-build edits of other pages skipped)')
    if NEWPAGES: print(f'QUICK new pages ({len(NEWPAGES)}): ' + ' '.join(NEWPAGES[:20]) + ' (sitemap.xml was rewritten for them)')
    if h:
        print(f'QUICK-HELD {len(h)} files outside --only would change (not written), so this change needs a full build (the would-be files are in data/cache/quick_held/):')
        for x in h[:60]: print('   ', x)
        sys.stdout.flush(); sys.exit(3)
    print('QUICK ok: nothing outside --only changed')
