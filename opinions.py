# 11-18 owner opinions box (Elijah: readers leave their opinion on a car, anonymous or with their name, checked by AI before it shows).
# Run by build.py with exec() (needs FY, E, TS, QM in scope). OP_HOOK(path, body) adds the #opinions section to every model page
# (/cars/<id>/) and model-year page (/cars/<id>/<year>/). Approved opinions are baked into the HTML so they are real page content;
# assets/opinions.js loads the newest ones and posts new ones to the lemon-survey Worker (POST /op; rules, limits and AI review live there).
# Full builds refresh data/opinions.json from the Worker's GET /ops_all; quick builds reuse that file. No opinions = only a small
# "Share your take" button (no empty box, no "no opinions yet" text).
import urllib.request as _opu
_OP_F = 'data/opinions.json'
_OP_TS = '0x4AAAAAAFyhvovKDo2j0cLa'   # the site's public Turnstile key (same as TS on /vote/)
if not QM.ON:
    try:
        with _opu.urlopen(_opu.Request('https://lemon-survey.elift08.workers.dev/ops_all', headers={'User-Agent': 'lemonindex-build'}), timeout=20) as _r:
            _opd = json.loads(_r.read().decode('utf-8'))
        if isinstance(_opd, dict): json.dump(_opd, open(_OP_F, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    except Exception as _ex: print('opinions: Worker not reached, using the saved file:', type(_ex).__name__)
OPS = _jl(_OP_F) or {}
_OP_KIND = {'owner': 'Owner', 'former': 'Former owner', 'drove': 'Drove one', 'opinion': 'Opinion'}
_OP_CSS = '<link rel="stylesheet" href="/assets/opinions.css?v=1"><link rel="stylesheet" href="/assets/agrp.css?v=1">'   # 11-18: own file, so style tweaks don't need a full rebuild; 11-24 agrp.css: the open box + close x
_MNS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
def _op_item(o):
    d = datetime.datetime.fromtimestamp(o['ts'] / 1000, datetime.timezone.utc)
    meta = ' · '.join(x for x in (_OP_KIND.get(o.get('kind'), 'Opinion'), str(o['year']) if o.get('year') else '',
                                  'Would buy again' if o.get('buy') == 'yes' else 'Wouldn&#39;t buy again' if o.get('buy') == 'no' else '') if x)
    paras = ''.join(f'<p>{E(p)}</p>' for p in str(o.get('text', '')).split('\n') if p.strip())
    return (f'<article class="opn-i"><header><b>{E(o.get("name") or "Anonymous")}</b><span class="opn-m">{meta}</span>'
            f'<time datetime="{d:%Y-%m-%d}">{_MNS[d.month - 1]} {d.day}, {d.year}</time></header>{paras}</article>')
def _op_box(fid, y=None):
    f = FY[fid]; name = f['name']; ys = sorted({v['y'] for v in f['years']}, reverse=True)
    shown = globals()['QN'](f) if 'QN' in globals() else name   # 11-20 (QA: the F-150 year page asked 'Own a 2015 Ford F-Series?'): the page's own name
    ops = sorted(OPS.get(fid) or [], key=lambda o: ((o.get('year') == y) if y else 0, o['ts']), reverse=True)
    car = f'{y} {shown}' if y else shown; n = len(ops)
    yopt = '<option value="">Year (optional)</option>' + ''.join(f'<option value="{v}"{" selected" if v == y else ""}>{v}</option>' for v in ys)
    items = ''.join(_op_item(o) for o in ops[:8])
    return (f'{_OP_CSS}<section class="yc opn" id="opinions" data-fid="{E(fid)}" data-car="{E(name)}" data-y="{y or ""}" data-ts="{_OP_TS}">'
            f'<h2 class="opn-h"{"" if n else " hidden"}>What owners say <span class="h2s">{n} opinion{"s" * (n != 1)} from Lemon Index readers about the {E(shown)}. Checked before they show; not part of the score.</span></h2>'
            f'<div class="opn-l">{items}</div>'
            # 11-24 (Elijah: "some of them don't even have an exit"): the row is a toggle (chevron down; a close x while open, assets/agrp.css)
            # and the form opens inside the row's own card, under it
            f'<div class="opn-share cpl"><button class="cpl-a opn-open" type="button" aria-expanded="false" aria-controls="opn-f-{E(fid.replace("/", "-"))}">{PILL_SUM("/assets/icons/opinion.webp", f"Own a {E(car)}? Share your take", "Anonymous is fine. Checked before it shows.")}{PILL_AR}{PILL_X}</button>'
            f'<form class="opn-f" id="opn-f-{E(fid.replace("/", "-"))}" hidden novalidate><label for="opn-t-{E(fid.replace("/", "-"))}"><b>Your opinion of the {E(car)}</b></label>'
            f'<textarea id="opn-t-{E(fid.replace("/", "-"))}" name="text" maxlength="800" required placeholder="What has it been like? Problems, repairs, what you love, what you&#39;d tell a buyer."></textarea><span class="opn-c">0/800</span>'
            f'<div class="opn-row"><select name="kind" aria-label="How you know this car"><option value="owner">I own one</option><option value="former">I used to own one</option><option value="drove">I drove one</option><option value="opinion">Just an opinion</option></select>'
            f'<select name="year" aria-label="Model year">{yopt}</select></div>'
            f'<div class="opn-row" role="radiogroup" aria-label="Would you buy it again?"><span>Would you buy it again?</span><label><input type="radio" name="buy" value="yes"> Yes</label><label><input type="radio" name="buy" value="no"> No</label></div>'
            f'<div class="opn-row"><label><input type="checkbox" name="anon" checked> Post as Anonymous</label><span class="opn-name" hidden><input type="text" name="name" maxlength="30" autocomplete="nickname" placeholder="Your name (shown)" aria-label="Your name"></span></div>'
            f'<input class="opn-hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">'
            f'<div class="opn-ts"></div><p class="opn-rules">One opinion per car, up to 10 a day. Each one is checked automatically before it shows: no links, phone numbers, personal details or swearing.</p>'
            f'<button class="btn" type="submit">Post opinion</button></form><p class="opn-msg" hidden aria-live="polite"></p></div></section><script src="/assets/opinions.js?v=1124" defer></script>')
def OP_HOOK(path, body):
    m = re.fullmatch(r'/cars/(.+?)/(?:(\d{4})/)?', path)
    if not m or m.group(1) not in FY: return body
    return body + _op_box(m.group(1), int(m.group(2)) if m.group(2) else None)
print('opinions:', sum(len(v) for v in OPS.values()), 'approved on', len(OPS), 'models')
