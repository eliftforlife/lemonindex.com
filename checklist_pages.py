# 11-25 paid before-you-buy checklists (lemon-store): /checklist/, /checklist/<generation>/, /account/, /account/signin/.
# exec'd from build.py (uses OUT, BASE, CONTACT, E). ON since the 11-25 launch; LEMON_CHECKLIST=0 turns it off (nothing written).
# These are standalone app pages, not page(): no ads, no analytics, no third-party script at all, and their own strict CSP, because the
# sign-in token lives in this origin's localStorage (the store Worker runs on workers.dev, so a cookie would be third-party).
# Public data only: data/checklist_store.json (names, years, check counts per area; build_content.py). The checklist itself and the answer
# (the offer engine) come from the Worker after sign-in, for an account that owns them. noindex while new (open question for Elijah).
CHECKLIST_ON = os.environ.get('LEMON_CHECKLIST', '1') == '1'   # 11-25 launch: on by default (LEMON_CHECKLIST=0 turns it off)
STORE_API = os.environ.get('LEMON_STORE_API', 'https://lemon-store.elift08.workers.dev').rstrip('/')
TURNSTILE_KEY = os.environ.get('LEMON_TURNSTILE_SITEKEY', '')     # set together with the Worker's TURNSTILE_ON = "1"
if not re.fullmatch(r'https://[a-z0-9-]+\.elift08\.workers\.dev|https://api\.lemonindex\.com|http://(127\.0\.0\.1|localhost):\d{2,5}', STORE_API):
    raise SystemExit('LEMON_STORE_API must be the lemon-store Worker (https://*.elift08.workers.dev) or a local wrangler dev address')
CL_V = '1125d'


def _cl_doc(path, title, desc, cfg, noscript):
    ts = ' https://challenges.cloudflare.com' if TURNSTILE_KEY else ''
    csp = (f"default-src 'none'; script-src 'self'{ts}; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; "
           f"connect-src {STORE_API} https://vpic.nhtsa.dot.gov https://api.nhtsa.gov; frame-src{ts or ' ' + chr(39) + 'none' + chr(39)}; "
           "base-uri 'none'; form-action 'none'; object-src 'none'; manifest-src 'self'")
    cfg_js = json.dumps(cfg, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    turn = '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit" async defer></script>' if TURNSTILE_KEY and cfg.get('page') == 'checklist' else ''
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><meta name="robots" content="noindex, follow"><link rel="canonical" href="{BASE}{path}">
<meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="no-referrer">
<link rel="icon" href="/assets/icon-64.png"><link rel="apple-touch-icon" href="/assets/icon-180.png"><link rel="stylesheet" href="/assets/cl.css?v={CL_V}">
</head><body><div id="app">{noscript}</div>
<script type="application/json" id="cl-cfg">{cfg_js}</script>{turn}
<script src="/assets/recall_names.js?v={CL_V}" defer></script><script src="/assets/cl.js?v={CL_V}" defer></script></body></html>'''
    os.makedirs(f'{OUT}{path}', exist_ok=True)
    open(f'{OUT}{path}index.html', 'w', encoding='utf-8').write(doc)


def CL_PAGES():
    if not CHECKLIST_ON: return 0
    T = json.load(open('data/checklist_store.json', encoding='utf-8'))
    models = {t['model'] for t in T.values()}
    titles = {}
    for g, t in sorted(T.items()):
        mid = (t['years'][0] + t['years'][1]) / 2   # this generation's own picture (assets/ai-cars/<model>-<year>.webp), else the model's
        yi = next((y for y in sorted(range(t['years'][0], t['years'][1] + 1), key=lambda y: abs(y - mid)) if os.path.exists(f"assets/ai-cars/{t['model']}-{y}.webp")), None)
        img = f"/assets/ai-cars/{t['model']}-{yi}.webp" if yi else f"/assets/ai-models/{t['model']}.webp" if os.path.exists(f"assets/ai-models/{t['model']}.webp") else '/assets/og.png'
        yrs = f"{t['years'][0]}–{t['years'][1]}"
        titles[g] = [f"{t['short']} {yrs}", img]
        tz = {'title': f"{t['short']} {yrs}", 'short': t['short'], 'type': t.get('type'), 'img': img, 'line': f"{t['name']}, {t['gen']} ({yrs})",
              'checks': t['checks'], 'all': t['all'], 'drive': t['drive'], 'mins': t.get('mins', 40), 'known': [k for k in t.get('known', []) if len(k) < 40][:2],
              'nModels': len(models), 'home': f"/cars/{t['model']}/", 'yearPage': f"/cars/{t['model']}/{{y}}/"}
        per = ''.join(f'<li>{E(n)}: {t["per"].get(str(i), 0)} checks</li>' for i, n in enumerate(['Before you go', 'Walk around it', 'Tires and brakes', 'Under the hood', 'Start it', 'A/C, then heat', 'Inside', 'Test drive', 'Paperwork'], 1) if t['per'].get(str(i)))
        ns = (f'<div class="acc" style="padding:20px"><h1>{E(t["name"])} checklist, {yrs}</h1><p class="s">{t["checks"]} quick checks ({t["all"]} in all) for the {E(t["gen"])}, '
              f'and your offer price at the end. Your first checklist is free.</p><ul class="note">{per}</ul><p class="note">This page needs JavaScript.</p></div>')
        _cl_doc(f'/checklist/{g}/', f"{t['name']} {yrs} Before-You-Buy Checklist", f"Step-by-step used {t['name']} checks for {yrs}, built from this generation's own known problems, with your offer price at the end.",
                {'page': 'checklist', 'api': STORE_API, 'gen': g, 'teaser': tz, 'turnstile': TURNSTILE_KEY or None, 'contact': CONTACT}, ns)
    # the list of every checklist (plain HTML, no script needed)
    by = {}
    for g, t in T.items(): by.setdefault(t['brand'] or 'Other', []).append((t['short'], t['years'], g))
    rows = ''.join(f'<p class="sec">{E(b)}</p>' + ''.join(f'<a class="hk-c mini" href="/checklist/{g}/"><span class="hk-t"><b>{E(s)} {y[0]}–{y[1]}</b><small>Checklist</small></span>'
                   f'<span class="hk-p"><img src="{titles[g][1]}" alt="" loading="lazy"></span></a>' for s, y, g in sorted(v)) for b, v in sorted(by.items()))
    idx = (f'<div class="nav"><a class="lg" href="/">The Lemon Index</a><span class="sp"></span><a class="nl" href="/account/">My checklists</a></div>'
           f'<div class="acc" style="padding:8px 20px 40px;max-width:640px;margin:0 auto"><h1>Before-you-buy checklists</h1>'
           f'<p class="s">Step by step at the car, built from each generation’s own known problems, with your offer price at the end. First checklist free; '
           f'$7.99 for one car, or $19.99 for every car and truck checklist (ones we add later too).</p>{rows}</div>')
    os.makedirs(f'{OUT}/checklist', exist_ok=True)
    open(f'{OUT}/checklist/index.html', 'w', encoding='utf-8').write(
        f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Used Car Checklists: Before You Buy | The Lemon Index</title>
<meta name="description" content="Step-by-step used car and truck checklists for {len(models)} models, with your offer price at the end. First checklist free."><meta name="robots" content="noindex, follow"><link rel="canonical" href="{BASE}/checklist/">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; object-src 'none'">
<link rel="icon" href="/assets/icon-64.png"><link rel="stylesheet" href="/assets/cl.css?v={CL_V}"></head><body>{idx}</body></html>''')
    _cl_doc('/account/', 'Your Checklists | The Lemon Index', 'Your Lemon Index checklists, purchases and sign-in.', {'page': 'account', 'api': STORE_API, 'titles': titles, 'contact': CONTACT},
            '<div class="acc" style="padding:20px"><h1>Your checklists</h1><p class="note">This page needs JavaScript.</p></div>')
    _cl_doc('/account/signin/', 'Signing In | The Lemon Index', 'Sign in to your Lemon Index checklists.', {'page': 'signin', 'api': STORE_API, 'contact': CONTACT},
            '<div class="acc" style="padding:20px"><h1>Signing you in</h1><p class="note">This page needs JavaScript.</p></div>')
    return len(T)


print('checklist pages:', CL_PAGES() if CHECKLIST_ON else 'off (LEMON_CHECKLIST=0)')
