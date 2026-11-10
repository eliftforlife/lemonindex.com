# Small, gentle YouTube pull for BMW engine codes (11-10, Elijah: "a YouTube score per year per engine too").
# Info only (flat search results: title, views, channel), no transcripts, one search at a time, 20 s apart, no cookies or proxies.
# Stops on the first sign of a block (429 / "Sign in to confirm"). Output: data/cache/bmw_engine_videos.json
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'data', 'cache', 'bmw_engine_videos.json')
Q = ['BMW N54 reliability', 'BMW N55 reliability', 'BMW B58 reliability', 'BMW N52 reliability', 'BMW N20 timing chain problems',
     'BMW B48 reliability', 'BMW N63 problems', 'BMW N62 problems', 'BMW S55 reliability', 'BMW S58 reliability', 'BMW S63 problems',
     'BMW M54 reliability', 'N54 vs N55', 'B58 vs N55', 'BMW N63 years to avoid']
BLOCK = ('429', 'Sign in to confirm', 'not a bot', 'Too Many Requests')
res = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
for i, q in enumerate(Q):
    if q in res: continue
    p = subprocess.run([sys.executable, '-m', 'yt_dlp', '--ignore-config', '--flat-playlist', '-J', f'ytsearch40:{q}'], capture_output=True, text=True, encoding='utf-8', timeout=300)
    if any(b in (p.stderr or '') for b in BLOCK):
        print('BLOCK SIGN, stopping:', (p.stderr or '')[-300:]); break
    try: d = json.loads(p.stdout)
    except Exception: print('no json for', q, (p.stderr or '')[-200:]); continue
    res[q] = [dict(id=e.get('id'), title=e.get('title') or '', views=e.get('view_count') or 0, channel=e.get('channel') or '', duration=e.get('duration'))
              for e in d.get('entries') or [] if e.get('id')]
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(q, len(res[q]), flush=True)
    if i < len(Q) - 1: time.sleep(20)
print('done', sum(len(v) for v in res.values()), 'videos')
