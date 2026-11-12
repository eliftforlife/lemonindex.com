# 11-12 (UX test: "the Repairs & costs tab has no costs", Marcus, Jess, Linda): the cost block on each year page, from data/repair_costs.json
# (data_repair_costs.py). For the car's generation (the YouTube study's years when there is one, else the model year +-2):
#   - per repair area: the middle half and the middle of the repair bills owners named in their complaints to NHTSA, with how many
#     complaints; only areas with 5+ bills show a number, the rest say "not enough reports yet"
#   - "What to ask the shop": the automaker's own notes to dealers for this model year that announce a software update, a special
#     coverage / warranty extension or a known fix, by NHTSA document number
# Every figure is labeled as ONE repair bill, never a yearly or total cost of ownership.
import html, json, os, re, statistics
E = lambda s: html.escape(str(s), quote=True)
_D = None
def _data():
    global _D
    if _D is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'repair_costs.json')
        _D = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    return _D
MIN_N = 5
def _r(v): return f'${v:,.0f}' if v < 1000 else f'${round(v / 100) * 100:,.0f}'
def _q(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)

def areas(fid, y0, y1):
    """[(area, n, lo, mid, hi, [odi])] for the generation, most bills first"""
    by = {}
    for y, a, v, odi in _data().get(fid, {}).get('c', []):
        if y0 <= y <= y1: by.setdefault(a, []).append((v, odi))
    out = []
    for a, xs in by.items():
        vs = [v for v, _ in xs]
        out.append((a, len(vs), _q(vs, .25), statistics.median(vs), _q(vs, .75), [o for _, o in sorted(xs, key=lambda t: abs(t[0] - statistics.median(vs)))[:3]]))
    return sorted(out, key=lambda t: (-t[1], t[0]))

_TIPW = {
    ('coverage', 'Transmission'): 'ask whether a transmission special coverage or warranty extension applies to this car. Covered repairs can be free.',
    ('software', 'Transmission'): 'ask whether the latest transmission software update was done, and ask for it before paying for parts.',
    ('fix', 'Transmission'): 'ask for the CVT fluid records and whether the automaker&#39;s CVT fix was done.',
    ('coverage', 'Engine'): 'ask whether an engine special coverage or warranty extension applies. Covered repairs can be free.',
    ('fix', 'Engine'): 'ask whether an oil consumption test was done, and what it showed.',
    ('software', 'Engine'): 'ask whether the engine computer (PCM) update was done before chasing parts.',
    ('coverage', 'Electrical'): 'ask whether the electrical module special coverage applies. Covered repairs can be free.',
    ('software', 'Screen, radio & camera'): 'ask for the radio / screen software update first; it often fixes freezes and reboots without new parts.',
}
def tips(fid, y, prefer=()):
    """up to 3 'what to ask the shop' lines for this model year: one per (kind, area), coverage first, the car's big problem areas first"""
    rows = _data().get(fid, {}).get('t', {}).get(str(y), [])
    seen, out = set(), []
    for k, a, doc, line in sorted(rows, key=lambda r: (r[1] not in prefer, ('coverage', 'software', 'fix').index(r[0]))):
        if (k, a) in seen or (k, a) not in _TIPW: continue
        seen.add((k, a)); out.append((a, _TIPW[(k, a)], doc, line))
    return out[:3]

def html_block(fid, y, gen_years=None, gen_label=''):
    """the 'What repairs cost' section (class yfx, so the tab template files it under Repairs) or '' when there's nothing to show"""
    if gen_years: y0, y1 = min(gen_years), max(gen_years)
    else: y0, y1 = y - 2, y + 2
    A = areas(fid, y0, y1)
    shown = [a for a in A if a[1] >= MIN_N][:5]; few = [a for a in A if a[1] < MIN_N]
    T = tips(fid, y, [a[0] for a in shown])
    if not shown and not T: return ''
    span = gen_label or f'{y0}–{y1} model years'
    rows = ''
    for a, n, lo, mid, hi, odis in shown:
        rows += (f'<li><div class="rcq-t"><span>{E(a)}</span><small>one repair bill</small></div><b>{_r(lo)}–{_r(hi)}</b>'
                 f'<div class="rcq-m"><small>middle {_r(mid)} · {n} owner{"" if n == 1 else "s"} named a bill</small>'
                 f'<small class="rcq-o">e.g. NHTSA complaints {", ".join(E(o) for o in odis)}</small></div></li>')
    fewl = (f'<p class="rcq-few">Not enough reports yet for a number: {E(", ".join(f"{a} ({n})" for a, n, *_ in few[:6]))}. We show a range once 5 owners name a bill.</p>' if few else '')
    tl = ''.join(f'<li><b>{E(a)}:</b> {w} <small>(automaker note to dealers, NHTSA document {E(doc)}: “{E(line)}”)</small></li>' for a, w, doc, line in T)
    return ('<section class="yc yfx" id="costs"><h2>What repairs cost</h2>'
            + (f'<p class="yf-s">Repair bills owners named in their complaints to the government (NHTSA), {E(span)}.</p><ul class="rcq">{rows}</ul>' if shown
               else f'<p class="yf-s">Not enough repair bills reported for the {E(span)} yet to show a cost.</p>')
            + (fewl if shown else '')
            + (f'<h3 class="rcq-h">What to ask the shop</h3><ul class="rcq-tips">{tl}</ul>' if tl else '')
            + ('<p class="yc-cap">Each range is the middle half of the bills owners wrote down (one repair, parts and labor as they said it), not a yearly or total cost. '
               'Owners who complain often had expensive repairs, so typical bills can be lower. Prices depend on the shop, the miles and where you live.</p>' if shown else '')
            + '</section>')

# ---- 11-12 (UX test, Marcus: "the 2019 page has no code lookup; the P0700 page only links the model page"): year page -> code pages
_EC = None
def _codes():
    """{code: (title, has a page)} from data/engine_codes.json + engine_code_defs.py, the same page rule as engine_pages.py"""
    global _EC
    if _EC is None:
        import importlib.util as _ilu
        here = os.path.dirname(os.path.abspath(__file__))
        sp = _ilu.spec_from_file_location('engine_code_defs', os.path.join(here, 'engine_code_defs.py')); ECD = _ilu.module_from_spec(sp); sp.loader.exec_module(ECD)
        p = os.path.join(here, 'data', 'engine_codes.json'); EC = json.load(open(p, encoding='utf-8'))['codes'] if os.path.exists(p) else {}
        _EC = {}
        for c, v in EC.items():
            mm = ECD.MAKE.get(c) or ECD.D.get(c)
            _EC[c] = ((mm or {}).get('t') or '', (mm is not None and v['n'] >= 5) or v['n'] >= 20)
    return _EC
def _trans(c, t): return c[:3] in ('P07', 'P08', 'P09') or bool(re.search(r'transmission|shift|gear|torque converter|cvt|clutch', t, re.I))
def code_links(fid, y=None, trans_only=False, label=''):
    """'Check engine light on?' + the codes owners of this car name most that have a code page (model years y-2..y+2, or every year)"""
    K = _data().get(fid, {}).get('k', {}); C = _codes(); cnt = {}
    for yy, rows in K.items():
        if y is None or abs(int(yy) - y) <= 2:
            for c, n in rows: cnt[c] = cnt.get(c, 0) + n
    top = [c for c, n in sorted(cnt.items(), key=lambda t: -t[1]) if C.get(c, ('', False))[1] and (not trans_only or _trans(c, C[c][0]))][:6]
    links = ' · '.join(f'<a href="/check-engine-light/{c.lower()}/">{c}</a>' + (f' <small>{E(C[c][0])}</small>' if C[c][0] else '') for c in top)
    if trans_only:
        return (f'<p class="yc-cap rcq-codes">Transmission codes {E(label)} owners name most: {links}. <a href="/check-engine-light/">Look up any code →</a></p>' if top else '')
    return (f'<p class="yc-cap rcq-codes">Check engine light on? ' + (f'Codes owners of {E(label) or "this car"} name most: {links}. ' if top else '')
            + '<a href="/check-engine-light/">Look up any code →</a></p>')

def has_costs(h):
    """does a repairs panel show at least one real cost number?"""
    return 'class="rcq"' in h or 'class="yc-g"' in h
