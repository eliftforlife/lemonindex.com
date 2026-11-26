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
CL_V = '1126e'


def _cl_doc(path, title, desc, cfg, noscript):
    ts = ' https://challenges.cloudflare.com' if TURNSTILE_KEY else ''
    csp = (f"default-src 'none'; script-src 'self'{ts}; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; "
           f"connect-src {STORE_API} https://vpic.nhtsa.dot.gov https://api.nhtsa.gov; frame-src{ts or ' ' + chr(39) + 'none' + chr(39)}; "
           "base-uri 'none'; form-action 'none'; object-src 'none'; manifest-src 'self'")
    cfg_js = json.dumps(cfg, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    turn = '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit" async defer></script>' if TURNSTILE_KEY and cfg.get('page') in ('checklist', 'account') else ''
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><meta name="robots" content="noindex, follow"><link rel="canonical" href="{BASE}{path}">
<meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="no-referrer">
<link rel="icon" href="/assets/icon-64.png"><link rel="apple-touch-icon" href="/assets/icon-180.png"><link rel="stylesheet" href="/assets/cl.css?v={CL_V}">
</head><body><div id="app"><div class="boot"><span class="ld"><i></i></span></div><noscript>{noscript}</noscript></div>
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
              f'and your offer price at the end. Your first checklist is free.</p><ul class="note">{per}</ul><p class="note">Turn on JavaScript to use the checklist.</p></div>')
        _cl_doc(f'/checklist/{g}/', f"{t['name']} {yrs} Before-You-Buy Checklist", f"Step-by-step used {t['name']} checks for {yrs}, built from this generation's own known problems, with your offer price at the end.",
                {'page': 'checklist', 'api': STORE_API, 'gen': g, 'teaser': tz, 'turnstile': TURNSTILE_KEY or None, 'contact': CONTACT}, ns)
    # the store: every checklist (plain HTML, no script needed; the page's CSP allows none).
    # 11-26 (Elijah: "just say BMW 3 Series without the years ... when they click in it, they can select the year ... more like a fun store,
    # splashes of yellow, bigger title"): one card per MODEL (its picture, no years); tapping it opens a "Choose your year" drop-down
    # (<details>, so no script) of year buttons, newest first. Each year opens its generation's checklist with ?y= so the year is already picked.
    by, mods = {}, {}
    for g, t in T.items():
        m = mods.setdefault(t['model'], {'name': t['name'], 'brand': t['brand'] or 'Other', 'ys': {}, 'img': None})
        for y in range(t['years'][0], t['years'][1] + 1): m['ys'][y] = g
    for k, m in mods.items():
        m['img'] = f"/assets/ai-models/{k}.webp" if os.path.exists(f"assets/ai-models/{k}.webp") else titles[max(set(m['ys'].values()), key=lambda g: T[g]['years'][1])][1]
        by.setdefault(m['brand'], []).append(k)
    _bid = lambda b: 'b-' + re.sub(r'[^a-z0-9]+', '-', b.lower()).strip('-')
    ic_ch = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'
    def _card(k):
        m = mods[k]
        yrs = ''.join(f'<a class="sx-y" href="/checklist/{g}/?y={y}">{y}</a>' for y, g in sorted(m['ys'].items(), reverse=True))
        return (f'<details class="sx"><summary><span class="sx-t"><b>{E(m["name"])}</b><span class="sx-go">Choose your year {ic_ch}</span></span>'
                f'<span class="sx-p"><img src="{m["img"]}" alt="" loading="lazy" decoding="async"></span></summary><div class="sx-ys">{yrs}</div></details>')
    bs = sorted(by)
    rows = ''.join(f'<h2 class="sx-b" id="{_bid(b)}">{E(b)}</h2><div class="sx-g">' + ''.join(_card(k) for k in sorted(by[b], key=lambda k: mods[k]['name'])) + '</div>' for b in bs)
    jump = '<nav class="sx-j" aria-label="Brands">' + ''.join(f'<a href="#{_bid(b)}">{E(b)}</a>' for b in bs) + '</nav>'
    idx = (f'<div class="nav"><a class="lg" href="/">The Lemon Index</a><span class="sp"></span><a class="nl" href="/account/">My checklists</a></div>'
           # 11-26 (Elijah): no prices, no "first checklist free" up here (both show once a car is picked), one short line under the title
           f'<main class="sx-w"><header class="sx-h"><h1>Know what to check <span>before you buy.</span></h1>'
           f'<p class="sx-s">A step-by-step checklist built from your model’s own problems.</p></header>'
           f'{jump}{rows}</main>')
    os.makedirs(f'{OUT}/checklist', exist_ok=True)
    open(f'{OUT}/checklist/index.html', 'w', encoding='utf-8').write(
        f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Used Car Checklists: Before You Buy | The Lemon Index</title>
<meta name="description" content="Step-by-step used car and truck checklists for {len(models)} models, with your offer price at the end. First checklist free."><meta name="robots" content="noindex, follow"><link rel="canonical" href="{BASE}/checklist/">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; object-src 'none'">
<link rel="icon" href="/assets/icon-64.png"><link rel="stylesheet" href="/assets/cl.css?v={CL_V}"></head><body>{idx}</body></html>''')
    _cl_doc('/account/', 'Your Checklists | The Lemon Index', 'Your Lemon Index checklists, purchases and sign-in.', {'page': 'account', 'api': STORE_API, 'titles': titles, 'turnstile': TURNSTILE_KEY or None, 'contact': CONTACT},
            '<div class="acc" style="padding:20px"><h1>Your account</h1><p class="note">Turn on JavaScript to sign in.</p></div>')
    _cl_doc('/account/signin/', 'Signing In | The Lemon Index', 'Sign in to your Lemon Index checklists.', {'page': 'signin', 'api': STORE_API, 'contact': CONTACT},
            '<div class="acc" style="padding:20px"><h1>Signing you in</h1><p class="note">Turn on JavaScript to sign in.</p></div>')
    # 11-26 security test: the sign-in and checklist pages can't be framed by another site (clickjacking). Cloudflare's static assets read
    # docs/_headers; the page's own meta CSP can't set frame-ancestors.
    open(f'{OUT}/_headers', 'w', encoding='utf-8', newline='\n').write(''.join(
        f"{pat}\n  X-Frame-Options: DENY\n  Content-Security-Policy: frame-ancestors 'none'\n  X-Content-Type-Options: nosniff\n"
        for pat in ('/account', '/account/*', '/checklist', '/checklist/*')))
    return len(T)


print('checklist pages:', CL_PAGES() if CHECKLIST_ON else 'off (LEMON_CHECKLIST=0)')
