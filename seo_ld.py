# 11-23 SEO batch (titles-answers-schema, s03): structured data where a page type had none, and the visible "Quick answers" it needs.
# exec'd by build.py (next to ans_box.py), so page(), E, BASE, FY, crumbs, car_ld, faq_ld ... are in scope. Every answer here restates a
# number the same page already shows (no new numbers), and every FAQPage is built from Q&A that is visible on the page (in details boxes).
#   SL_QA_HTML(qa) / SL_FAQ(qa)       the Quick answers section (year-page markup: section.yqa > details.qa) and its FAQPage
#   SL_EV_QA / SL_SC_QA / SL_MO_QA / SL_PL_QA   Q&A for the /electric/, /supercars/, /motorcycles/ and /planes/ pages (called by their generators)
#   SL_CAR(...)                       a Car (or Vehicle) node: brand, model, vehicleModelDate (first/last model year), image
#   SL_PRE(path, title)               page(), first thing: remembers each page's title (sub-pages name their parent in the breadcrumbs)
#   SL_LD(path, title, body, ld)      page(), after the breadcrumbs: card sub-pages (sub_pages.py) get breadcrumbs through their parent
#                                     plus a Car node; compare pages get two Car nodes + FAQPage (the H1 question and the verdict line under
#                                     it); /recalls/ pages get a WebPage. Runs after the date hash and only touches JSON-LD, so no page date moves.
import html as _slh, re as _slr
SL_T = {}       # path -> title, filled by SL_PRE
SL_EVQ = {}     # /electric/<x>/ -> its first quick question (ans_box.py puts it over the page's answer line)
SEGN.setdefault('jdm', 'JDM')   # breadcrumbs said "Jdm"
_SL_TWO = ('Land Rover', 'Alfa Romeo', 'Aston Martin', 'Mercedes-AMG', 'Harley-Davidson', 'Royal Enfield', 'Moto Guzzi')


def _sl_txt(h): return _slr.sub(r'\s+', ' ', _slh.unescape(_slr.sub(r'<[^>]+>', '', h or ''))).strip()


def SL_QA_HTML(qa):
    if not qa: return ''
    return ('<section class="yc yqa" id="questions"><h2>Quick answers</h2>'
            + ''.join(f'<details class="qa"><summary><h3 class="qh">{q}</h3></summary><p>{a}</p></details>' for q, a in qa) + '</section>')


def SL_INS(body, qa):
    """the Quick answers section as the last block inside a page's root div (the mp6 layout files .yqa under a Questions tab)"""
    i = body.rfind('</div>')
    return body if not qa or i < 0 else body[:i] + SL_QA_HTML(qa) + body[i:]


def SL_FAQ(qa): return [faq_ld([(_sl_txt(q), '', _sl_txt(a)) for q, a in qa])] if qa else []


def _sl_brand(name, make=None):
    if make: return make
    c = BYNAME.get(name) if 'BYNAME' in globals() else None
    if c and c.get('brand'): return c['brand']
    return next((b for b in _SL_TWO if name.startswith(b + ' ')), name.split()[0])


def SL_CAR(name, url, y0=None, y1=None, img=None, make=None, typ='Car', **extra):
    b = _sl_brand(name, make)
    d = {"@context": "https://schema.org", "@type": typ, "name": name, "brand": {"@type": "Brand", "name": b},
         "model": name[len(b):].strip() if name.startswith(b) and name[len(b):].strip() else name, "url": BASE + url}
    if y0: d["vehicleModelDate"] = str(y0) if not y1 or y1 == y0 else f'{y0}/{y1}'   # first/last model year (ISO 8601 interval)
    if img: d["image"] = BASE + img
    d.update(extra)
    return d


def _sl_list(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def _sl_rec(n): return f'{n} recall' + ('' if n == 1 else 's')


# ---------------- /electric/<x>/ (electric_pages.py): the numbers in its hero line, Top problems, Range & cost and Recalls boxes
def SL_EV_QA(c, big, mn, rank, rec_note, e):
    nm = E(c['name']); qa = []
    q1 = f'Is the {nm} reliable?'
    qa.append((q1, f'The {nm} drew {plain(big)}' + (f' (model years {YRS(mn)}).' if mn else f': {rank}.')
               + (f' Its EV ranking score is {c["li"]} for model years {c["years"].replace("-", "–")}, {rank} (100 is the average car).' if mn else ' 100 is the average car; lower is better.')))
    SL_EVQ[f'/electric/{c["slug"]}/'] = q1
    if c['issues']:
        qa.append((f'What are the most common {nm} problems?', 'In owner complaints to NHTSA, the areas named most are '
                   + _sl_list(f'{E(ep(p))} ({k}%)' for p, k in c['issues'][:3]) + '. That is the share of complaints that name each area.'))
    qa.append((f'How many recalls does the {nm} have?', f'{rec_note[0].upper() + rec_note[1:]}. Recall repairs are free at any dealer.'))
    qa.append((f'How many fire complaints does the {nm} have?', f'{c["fire"]:,} fire complaint{"" if c["fire"] == 1 else "s"} ({c["fire100k"]} per 100,000 sold); the average for all EVs is {P["ev"]["fire100k"]}.'))
    if e and e.get('range'):
        qa.append((f'What is the {nm}&#39;s range?', f'The EPA rates the {e["year"]} {nm} at {rng(e["range"], " miles")} of range'
                   + (f', and about {costr(e["cost"])} a year to charge (15,000 miles at national average prices).' if e.get('cost') else '.')))
    return qa


def SL_EV_LD(c, img=None):
    y = [int(x) for x in _slr.findall(r'\d{4}', c['years'])]
    return SL_CAR(c['name'], f'/electric/{c["slug"]}/', y[0] if y else None, y[-1] if y else None, img, fuelType='Electric')


# ---------------- /supercars/<x>/ (vehicles_pages.py): EPA tiles, the hp tile and the Recalls section
def SL_SC_QA(c, ys, nrec, tiles):
    nm = E(c['name']); last = ys[-1]; qa = []
    hp = next(((v, s) for v, s in tiles if v.endswith(' hp')), None)
    if hp: qa.append((f'How much horsepower does the {nm} have?', f'{E(hp[0])} ({E(hp[1])}).'))
    if last.get('comb'):
        qa.append((f'What MPG does the {nm} get?', f'The EPA rates the {last["y"]} {nm} at {rng2(last["comb"])} mpg combined'
                   + (f' ({rng2(last["city"])} city, {rng2(last["hwy"])} highway).' if last.get('city') and last.get('hwy') else '.')))
    if last.get('cost'):
        qa.append((f'How much does the {nm} cost in fuel?', f'About {rng2(last["cost"], "$")} a year for the {last["y"]} model, the EPA estimate for 15,000 miles at national average prices.'))
    qa.append((f'How many recalls does the {nm} have?', (f'{_sl_rec(nrec)} on record with NHTSA for model years {ys[0]["y"]}–{last["y"]}.' if nrec else
                                                          f'No NHTSA recalls on record for model years {ys[0]["y"]}–{last["y"]}.') + ' Recall repairs are free at any dealer.'))
    return qa


# ---------------- /motorcycles/<x>/ (vehicles_pages.py): the stat tiles, "What owners complain about", Recalls, "Complaints by model year"
def SL_MO_QA(m, n, by):
    nm = E(m['name']); qa = []
    if m.get('parts'):
        qa.append((f'What are the most common {nm} problems?', 'In owner complaints to NHTSA, the areas named most are '
                   + _sl_list(f'{E(p)} ({k}%)' for p, k in m['parts'][:3]) + '. That is the share of complaints that name each area.'))
    if by:
        top = sorted(by.items(), key=lambda kv: -kv[1])[:2]
        qa.append((f'Which {nm} model years have the most complaints?', _sl_list(f'{y} ({v:,} complaint{"" if v == 1 else "s"})' for y, v in top)
                   + f'. These are counts, not rates: there are no sales figures per motorcycle model year.'))
    nr = len(m['recalls'])
    qa.append((f'How many recalls does the {nm} have?', (f'{_sl_rec(nr)} from NHTSA.' if nr else 'No NHTSA recalls found for these model names.') + ' Recall repairs are free at any dealer.'))
    qa.append((f'How many owner complaints does the {nm} have?', f'{n:,} filed with NHTSA; {m["serious"]}% involved a crash, fire or injury.'))
    return qa


# ---------------- /planes/<x>/ (vehicles_pages.py): FAQ only (no vehicle node): the stat tiles, "What happened", "Pilot or plane?", "When"
def SL_PL_QA(p, whatrows):
    nm = E(p['name']); qa = []
    qa.append((f'How many {nm} accidents has the NTSB investigated?', f'{p["n"]:,} U.S. accidents from 2008 to 2025. {p["fatal_pct"]}% were fatal ({p["deaths"]:,} deaths) and {p["destroyed_pct"]}% of the aircraft were destroyed.'))
    if whatrows:
        qa.append((f'What happens in most {nm} accidents?', 'NTSB&#39;s defining event is most often ' + _sl_list(f'{E(k.lower())} ({v}%)' for k, v in whatrows[:3]) + '.'))
    if p.get('mech_pct') is not None:
        qa.append((f'Is it usually the pilot or the plane?', f'NTSB listed an aircraft problem among the causes in {p["mech_pct"]}% of the {p["judged"]:,} accidents where it recorded a cause; '
                   f'the other {100 - p["mech_pct"]}% were people or weather only.'))
    if p.get('phase'):
        k, v = p['phase'][0]
        qa.append((f'When do {nm} accidents happen?', f'Most often during {E(k.lower())} ({v}% of accidents).'))
    return qa


# ---------------- page() hooks
def SL_PRE(path, title): SL_T[path] = title


_SL_SUBP = 'class="advp tbl pfp sbp"'


def _sl_visible_qa(body):
    return [(_sl_txt(q), _sl_txt(a)) for q, a in _slr.findall(r'<details class="qa"><summary><h3[^>]*>(.*?)</h3></summary>\s*<p>(.*?)</p>', body, _slr.S)]


def SL_LD(path, title, body, ld):
    try:
        types = {x.get('@type') for x in ld}
        # card sub-pages: breadcrumbs through the parent (its real name, the /cars/ wayfinding for car pages) + the car itself
        if _SL_SUBP in body:
            par = path.rstrip('/').rsplit('/', 1)[0] + '/'
            hm = _slr.search(r'<h1>(.*?)</h1>', body, _slr.S); h1 = _sl_txt(hm.group(1)) if hm else title.split(' | ')[0]
            pc = crumbs(par, SL_T.get(par, title))
            items = pc['itemListElement'] + [{"@type": "ListItem", "position": len(pc['itemListElement']) + 1, "name": h1, "item": BASE + path}]
            ld = [x for x in ld if x.get('@type') != 'BreadcrumbList'] + [dict(pc, itemListElement=items)]
            car = None; m = _slr.fullmatch(r'/cars/([^/]+)/(?:(\d{4})/)?[^/]+/', path)
            if m and m.group(1) in FY:
                f = FY[m.group(1)]; ys = [v['y'] for v in f['years']]; ph = mphoto(m.group(1))
                if m.group(2): car = car_ld(f, int(m.group(2)), img=ph['src'] if ph else None)
                else: car = SL_CAR(f['name'], CARU(f), min(ys) if ys else None, max(ys) if ys else None, ph['src'] if ph else None)
            elif par in globals().get('_SB_PERF', {}):
                D = _SB_PERF[par]; G = [g for g in D.get('gens') or [] if g.get('y0')]
                car = SL_CAR(_slr.split(r' \(', D['name'])[0], par, min(g['y0'] for g in G) if G else None, max(g.get('y1') or g['y0'] for g in G) if G else None, make=D.get('make'))
            if car and 'Car' not in types: ld.append(car)
            vq = _sl_visible_qa(body)
            if vq and 'FAQPage' not in types: ld.append(faq_ld([(q, '', a) for q, a in vq]))
            return ld
        # compare pages: the two cars + the H1 question answered by the verdict line right under it
        m = _slr.fullmatch(r'/compare/(.+)/', path)
        if m and 'cb-vline' in body:
            s = m.group(1); ab = next(((s[:i], s[i + 4:]) for i in [x.start() for x in _slr.finditer('-vs-', s)] if s[:i] in FY and s[i + 4:] in FY), None)
            if ab and 'Car' not in types:
                for fid in ab:
                    f = FY[fid]; ys = [v['y'] for v in f['years']]; ph = mphoto(fid)
                    ld.append(SL_CAR(f['name'], CARU(f), min(ys) if ys else None, max(ys) if ys else None, ph['src'] if ph else None))
            hm = _slr.search(r'<h1>(.*?)</h1>', body, _slr.S); vm = _slr.search(r'<p class="cb-vline">(.*?)</p>', body, _slr.S)
            q = _sl_txt(hm.group(1)) if hm else ''; a = _sl_txt(vm.group(1)) if vm else ''
            if q.endswith('?') and len(a) > 30 and 'FAQPage' not in types: ld.append(faq_ld([(q, '', a)]))
            return ld
        if path.startswith('/recalls/') and 'WebPage' not in types:
            d = {"@context": "https://schema.org", "@type": "WebPage", "url": BASE + path, "name": title.split(' | ')[0]}
            if PD.get(path, {}).get('d'): d["dateModified"] = PD[path]['d']
            ld.append(d)
    except Exception as ex:
        globals().setdefault('TAB_FAIL', []).append(f'SL_LD {path}: {type(ex).__name__} {ex}')
    return ld
