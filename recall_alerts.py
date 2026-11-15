# 11-14 growth plan 4a: recall alert emails ("Get an email if your car gets a recall"). exec'd from build.py.
# The signup box (assets/ralert.js + ralert.css) goes on every /cars/<model>/<year>/ page (inside the Recalls section), every
# /cars/<model>/ page (under the tabs, with a year picker) and /vin/ (vin.js adds it after a lookup). It is added by RA_HOOK in page()
# AFTER the content hash, so adding it doesn't redate thousands of pages. Backend: the lemon-alerts Worker (worker/alerts_worker.js):
# double opt-in, weekly NHTSA check, one-click unsubscribe. /alerts/ (noindex, not in the sitemap) is where the email links land.
# The box sends the NHTSA make/model names this year's recall list uses (each name with 10%+ of complaints, max 2), never a VIN.
RA_ASSETS = '<link rel="stylesheet" href="/assets/ralert.css?v=1115"><script src="/assets/ralert.js?v=1115" defer></script>'
def _ra_names(fid, y):
    ns = extra(fid, y).get('names') or []
    if not ns: return None
    tot = sum(n for _, _, n in ns) or 1
    return [[mk, md] for mk, md, n in ns if n / tot >= .10][:2] or [list(ns[0][:2])]
def _ra_box(d): return f'<div class="rla" data-ra="{E(json.dumps(d, ensure_ascii=False, separators=(",", ":")))}"></div>'
def RA_HOOK(path, body):
    m = re.fullmatch(r'/cars/(.+?)/(\d{4})/', path)
    if m and m.group(1) in FY:
        fid, y = m.group(1), int(m.group(2)); names = _ra_names(fid, y); i = body.find('id="recalls"')
        j = body.find('</section>', i) if i >= 0 else -1
        if j < 0 or not names: return body
        return body[:j] + _ra_box({'y': y, 'n': names, 'f': fid, 'l': f'{y} {FY[fid]["name"]}'}) + RA_ASSETS + body[j:]
    m = re.fullmatch(r'/cars/(.+?)/', path)
    if m and m.group(1) in FY:
        f = FY[m.group(1)]; ys = {str(v['y']): _ra_names(f['id'], v['y']) for v in f['years']}; ys = {k: v for k, v in ys.items() if v}
        if not ys: return body
        try: y0 = popular_year(f)
        except Exception: y0 = None
        return body + f'<section class="rla-sec" id="recall-alerts">{_ra_box({"m": f["name"], "f": f["id"], "ys": ys, "y0": y0 if str(y0) in ys else max(map(int, ys))})}</section>' + RA_ASSETS
    if path == '/vin/': return body + RA_ASSETS
    return body
RA_PRIVACY = ('<h2 id="recall-alerts">Recall alerts</h2><p>If you sign up for recall alerts, we store your email address, the model year, make and model you picked '
              '(never a VIN: on the VIN check we keep only the year, make and model it decodes to), a confirm code and an unsubscribe code, and the NHTSA recall '
              'numbers we have already emailed you about. To stop repeat signups we also keep a daily scrambled code (a one-way hash of your IP address and the date) '
              'for 2 days. Nothing is sent until you tap the link in the confirm email; unconfirmed signups are deleted after 30 days. We check NHTSA&#39;s recall '
              'list once a week and email you only when a new recall is added. Every email has a one-click unsubscribe, and unsubscribing deletes your email address '
              'and all your alerts. Emails are sent through Resend; the list lives in a Cloudflare database. We never sell, rent or share the list.</p>')
def RA_PAGE():
    page('/alerts/', 'Recall Alerts | The Lemon Index', 'Get an email when NHTSA adds a new recall for your car. Confirm or stop your Lemon Index recall alerts here.', f'''<div class="pg"><section class="rla-page" id="rla-page">
<h1>Recall alerts</h1><div class="rla-intro"><p class="lede">Get an email when NHTSA adds a new recall for your car.</p>
<p>Pick your car on its Lemon Index page and tap <b>Email me</b> in its Recalls section, or <a href="/vin/">check your VIN</a> first. We check the recall list every week and email you only when something new is added. You confirm by email first, and every email has a one-click unsubscribe.</p>
<p><a class="btn" href="/cars/">Find your car</a></p></div><div class="rla-out" aria-live="polite" hidden></div>
<p class="note">Details in our <a href="/privacy/#recall-alerts">privacy policy</a>. We never sell or share the list.</p></section></div>{RA_ASSETS}''')
    _p = f'{OUT}/alerts/index.html'; _s = open(_p, encoding='utf-8').read()
    open(_p, 'w', encoding='utf-8').write(_s.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow"><link rel="canonical"', 1))
