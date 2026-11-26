"""Load the paid checklists into the lemon-store KV namespace (binding CONTENT).   py -X utf8 worker/store/upload_content.py --local
11-25. Reads <private checklist folder>/store content/kv_bulk.json (written by build_content.py; never inside this repo) and hands it to
`wrangler kv bulk put`. It never prints a checklist, only counts and sizes.

  --local            the `wrangler dev` KV (.wrangler/state), for local testing. Safe to run any time.
  --remote --yes     the REAL namespace. A go-live step: only with Elijah's OK, after the namespace id is pasted into wrangler.toml.
Upload order: every gen:<id> first, the index last, so a new checklist is never listed before its content exists.
"""
import argparse, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC0 = os.path.join(os.path.expanduser('~'), 'Desktop', 'Eliftforlife youtube', '3 Lemon Index', 'checklist')


def put(items, where):
    fd, tmp = tempfile.mkstemp(suffix='.json', prefix='lemon-kv-')          # outside the repo; deleted right after
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f: json.dump(items, f, ensure_ascii=False)
        cmd = ['npx', 'wrangler', 'kv', 'bulk', 'put', tmp, '--binding', 'CONTENT', where]
        r = subprocess.run(cmd, cwd=HERE, shell=(os.name == 'nt'), capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            # wrangler's error text has no checklist content in it, but keep it short
            sys.exit('wrangler kv bulk put failed: ' + (r.stderr or r.stdout).strip()[-600:])
    finally:
        os.remove(tmp)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument('--local', action='store_true'); g.add_argument('--remote', action='store_true')
    ap.add_argument('--yes', action='store_true', help='needed with --remote')
    ap.add_argument('--src', default=os.environ.get('LEMON_CHECKLIST_SRC', SRC0))
    a = ap.parse_args()
    bulk_path = os.path.join(a.src, 'store content', 'kv_bulk.json')
    if os.path.commonpath([os.path.abspath(bulk_path), REPO]) == REPO: sys.exit('the paid content must not live inside the repo')
    if not os.path.exists(bulk_path): sys.exit('no kv_bulk.json: run build_content.py first')
    if a.remote:
        toml = open(os.path.join(HERE, 'wrangler.toml'), encoding='utf-8').read()
        if re.search(r'id = "0{32}"', toml): sys.exit('wrangler.toml still has the placeholder KV id: create the namespace first (go-live step)')
        if not a.yes: sys.exit('--remote writes the live namespace: add --yes (only with Elijah\'s OK)')
    bulk = json.load(open(bulk_path, encoding='utf-8'))
    for it in bulk:
        if not (it['key'] == 'index' or re.fullmatch(r'gen:[a-z0-9]+(?:-[a-z0-9]+){0,6}-g\d{1,2}', it['key'])): sys.exit('unexpected key ' + it['key'][:40])
        if len(it['value'].encode('utf-8')) > 20 * 1024 * 1024: sys.exit('value over 20 MB: ' + it['key'])
    gens = [x for x in bulk if x['key'] != 'index']; idx = [x for x in bulk if x['key'] == 'index']
    where = '--local' if a.local else '--remote'
    # chunks of ~40 MB (the bulk API takes up to 100 MB / 10,000 keys per call)
    chunk, size = [], 0
    for it in gens:
        n = len(it['value'].encode('utf-8'))
        if chunk and size + n > 40 * 1024 * 1024: put(chunk, where); chunk, size = [], 0
        chunk.append(it); size += n
    if chunk: put(chunk, where)
    put(idx, where)
    print(f'{len(gens)} checklists + the index -> KV CONTENT ({where[2:]}), {sum(len(x["value"].encode("utf-8")) for x in bulk) // 1024} KB')
