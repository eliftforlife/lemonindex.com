# Tell Bing and the other IndexNow engines which lemonindex.com pages changed. Run after every push.
#   py indexnow.py               the pages whose content changed in the builds since the last submit (build.py writes them to
#                                data/cache/indexnow_pending.txt), then clears that list. Same as --pending. (11-12: this used to send all ~7.5K URLs)
#   py indexnow.py /path/ ...    just these pages (also dropped from the pending list)
#   py indexnow.py --all         every URL in the sitemap (only after a real site-wide change)
import json, os, re, sys, urllib.request
os.chdir(os.path.dirname(os.path.abspath(__file__)))
KEY = '3feeeaf370469523191adf4acc05fc45'; HOST = 'lemonindex.com'; PENDING = 'data/cache/indexnow_pending.txt'
args = [a for a in sys.argv[1:] if not a.startswith('--')]
pending = not args and '--all' not in sys.argv
if pending:
    args = [a for a in dict.fromkeys(l.strip() for l in open(PENDING, encoding='utf-8')) if a] if os.path.exists(PENDING) else []
    if not args: print('indexnow: nothing pending (no page content changed since the last submit)'); sys.exit(0)
urls = [f'https://{HOST}{p}' for p in args] or re.findall(r'<loc>([^<]+)</loc>', open('docs/sitemap.xml', encoding='utf-8').read())
assert urllib.request.urlopen(urllib.request.Request(f'https://{HOST}/{KEY}.txt', headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read().decode().strip() == KEY, 'key file not live'
for i in range(0, len(urls), 9000):
    body = json.dumps({'host': HOST, 'key': KEY, 'keyLocation': f'https://{HOST}/{KEY}.txt', 'urlList': urls[i:i + 9000]}).encode()
    r = urllib.request.urlopen(urllib.request.Request('https://api.indexnow.org/indexnow', data=body, headers={'Content-Type': 'application/json; charset=utf-8'}), timeout=60); print(r.status, len(urls[i:i + 9000]), 'URLs')
if os.path.exists(PENDING) and '--all' not in sys.argv:   # drop only what was sent (a build may have added more meanwhile); explicit paths count as sent too
    sent = set(args); left = [l.strip() for l in open(PENDING, encoding='utf-8') if l.strip() and l.strip() not in sent]
    open(PENDING, 'w', encoding='utf-8').write(''.join(l + '\n' for l in left))
