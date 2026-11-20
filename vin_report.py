# 11-14 growth plan project 1, chunks 1a + 1c (Elijah: "keep building data on site and pages"): the /vin/ decoder becomes a VIN report.
# Run by build.py with exec() right before the /vin/ page, so everything build.py defines is in scope.
#   - docs/assets/vr/<model id>.json: per model year the Lemon score + verdict, the top complaint areas, complaint and recall counts, the
#     YouTube rank, the engines with a page (CAR_ENG from engine_uses.py, incl. the VIN-matched ones in data/vin_engines.json) and a
#     "what to check on a test drive" list built ONLY from that year's top complaint areas. assets/vin.js fetches one file after a decode.
#     Written straight into docs/ (never the repo's assets/), so the YouTube workers' rebuilds commit the changes with docs/ as usual.
#   - VR_SEO / VR_FAQ: the page's real text for "free VIN check" searches, honest that it is a model-year record plus recalls, not a
#     vehicle history report. Rules (growth plan): "this model-year's record", never "this car's record"; we're not Carfax.
import json as _vrj, os as _vros, re as _vrre

# what to check on a test drive, per complaint area. An item shows only when that area is one of the model year's top complaint areas.
VR_TD = [(r'^transmission|drivetrain|power train', 'Shifting', 'From a stop and on the highway: no slipping, flaring revs, harsh or late shifts, or shudder.'),
         (r'^engine$', 'Engine', 'Start it cold if you can. Listen for ticking or knocking, and watch for smoke, a rough idle or a check-engine light.'),
         (r'^electrical', 'Electrical', 'Try every light, screen, window, lock and power feature, and watch the dash for warning lights.'),
         (r'^brakes|service brakes', 'Brakes', 'Brake firmly once at speed: it should stop straight, with no pulsing, grinding or brake warning light.'),
         (r'^parking brake', 'Parking brake', 'Set and release it on a slope; it should hold and let go cleanly.'),
         (r'^steering', 'Steering', 'Turn lock to lock and drive straight: no clunks, whine, wander or heavy spots, and no steering warning.'),
         (r'^suspension', 'Suspension', 'Drive over bumps: listen for clunks or rattles, and look for uneven tire wear.'),
         (r'^airbags?', 'Airbags', 'The airbag light should come on at start, then go out and stay out.'),
         (r'^fuel or ev', 'Fuel or EV drive', 'Watch for hard starts, stalling, a fuel smell or a reduced-power warning.'),
         (r'^fuel system', 'Fuel system', 'Watch for hard starts, stalling, hesitation or a fuel smell.'),
         (r'^ev drive|electric propulsion|hybrid propulsion', 'EV / hybrid drive', 'Watch for a reduced-power or battery warning, and check the range on the dash.'),
         (r'^speed control', 'Speed control', 'It should accelerate and hold speed smoothly, with no surging; try the cruise control.'),
         (r'automatic emergency braking|collision', 'Auto braking', 'Watch for sudden braking or collision warnings with nothing ahead.'),
         (r'^lane assist', 'Lane assist', 'Watch for false lane alerts or the wheel tugging on its own.'),
         (r'visibility|wipers', 'Wipers & visibility', 'Run the wipers, washers, defrost and mirror controls.'),
         (r'^lights|lighting', 'Lights', 'Walk around with the lights on: headlights, taillights, brake lights and turn signals.'),
         (r'^backup camera', 'Backup camera', 'Shift into reverse a few times: the camera should come on every time.'),
         (r'^body structure|structure', 'Body', 'Look underneath for rust, and check the doors, hood and hatch close and latch right.'),
         (r'^doors|locks|latches', 'Doors & locks', 'Lock and unlock every door from the fob and the switch, and open each one.'),
         (r'^seat belts?', 'Seat belts', 'Every belt should latch and retract.'),
         (r'^seats', 'Seats', 'Adjust each seat, try any heaters, and make sure they lock in place.'),
         (r'^tires', 'Tires', 'Check the tread is even across each tire, with no bulges, and note the tire date codes.'),
         (r'^wheels', 'Wheels', 'Look for bent or cracked wheels and listen for a hum or wobble at speed.'),
         (r'stability control|traction control', 'Stability control', 'The stability / traction warning light should stay off on the drive.')]
_vr_disp = lambda s: (_vrre.search(r'(?<![\d.])(\d\.\d)(?![\d])', s or '') or [None, None])[1]

def _vr_td(parts, comps):
    out, seen = [], set()
    miles = {NICE(c[0]): c for c in comps or [] if len(c) >= 5}
    for p, pct in parts[:5]:
        raw = p.lower(); nm = NICE(p)
        for pat, lab, txt in VR_TD:
            if _vrre.search(pat, raw) or _vrre.search(pat, nm):
                if lab in seen: break
                seen.add(lab); c = miles.get(nm)
                out.append([lab, pct, txt, c[1] if c and c[4] >= 10 else None]); break
    return out

def vr_write(out_dir):
    """one small JSON per model (the decode tells us which); returns how many model years were written"""
    _vros.makedirs(out_dir, exist_ok=True); tot = 0
    vee = (VEJ.get('engines') or {}) if 'VEJ' in globals() else {}
    lay = {d.get('page') or f'/engines/{e}/': d.get('lay', '') for e, d in vee.items()}
    for f in YEARS:
        rk = yt_rank_map(f); ys = {}
        ce = (globals().get('CAR_ENG') or {}).get(f['id']) or {}
        for v in f['years']:
            y = v['y']; x = extra(f['id'], y); bv = buy_verdict(f, v, y)
            eng = sorted(([EU_NAME.get(url, url), url, _vr_disp(EU_NAME.get(url, '')) or _vr_disp(lay.get(url.split('#')[0], ''))] for url, u in ce.items() if y in u['years']), key=lambda r: r[0])
            parts = [[NICE(p), k] for p, k in (v.get('parts') or [])[:3]]
            ys[str(y)] = dict(li=v.get('li'), ok=bool(v['ok']), early=bool(v.get('early')), cls=CLS(v), word=bv[1] if bv else None, why=bv[2] if bv else None,
                              pln=PLN(v), n=v.get('n'), all=(x.get('sev') or {}).get('total'), parts=parts, rc=len(x['recalls']) if 'recalls' in x else None,
                              yt=[rk[y], len(rk)] if y in rk else None, eng=eng, td=_vr_td(v.get('parts') or [], x.get('comps')),
                              nm=_ra_names(f['id'], y) if '_ra_names' in globals() else None)   # 11-15 4d: NHTSA make/model names for the /saved/ recall-alert signup (same as the year page's box)
            tot += 1
        d = dict(id=f['id'], name=f['name'], url=CARU(f), ytn=len(rk), years=ys)
        with open(_vros.path.join(out_dir, f['id'].replace('/', '_') + '.json'), 'w', encoding='utf-8') as fh: _vrj.dump(d, fh, ensure_ascii=False, separators=(',', ':'))
    return tot

VR_NM = len(YEARS); VR_NY = sum(len(f['years']) for f in YEARS)
VR_QA = [('Is this VIN check free?', f'Yes. Type a 17-character VIN and you get the decoded car, its model-year record and its recalls, free, with no sign-up. The VIN is decoded in your browser by the U.S. government&#39;s vPIC service (NHTSA). We don&#39;t store it.'),
         ('Does it show this car&#39;s accident, title or owner history?', 'No. That needs a vehicle history report (title, salvage, odometer and accident records), which this is not. We show the record of the model year the VIN decodes to: how many owner complaints that year drew per car sold, what they were about, and its recalls. For title history, see the government&#39;s National Motor Vehicle Title Information System (vehiclehistory.gov) or a paid history report.'),
         ('Can it tell me if a recall is still open on this exact car?', 'Not on its own. NHTSA&#39;s public recalls data lists every recall for a make, model and year, so we show that list and tag recalls that cover a different engine. Whether one is still unrepaired on this VIN is in the automaker&#39;s records: check the VIN at nhtsa.gov/recalls or ask any dealer of that brand. Recall repairs are free, even on a used car.'),
         ('What is the Lemon Index score?', 'Owner complaints to NHTSA in a model year&#39;s first 3 years, per 100,000 sold in the U.S., against the average car of the same years. 100 is average; 50 means half the complaints; 200 means twice. 2023 and newer years have had less time, so their scores are partial.'),
         ('Where does the test-drive list come from?', 'Only from the problem areas owners complained about most for that model year in NHTSA complaints. If electrical problems top the list, the electrical check is on it; areas owners rarely complained about are left off.'),
         ('Where do I find the VIN?', 'On the driver-side dashboard (look through the windshield), on the driver&#39;s door frame, and on the registration and insurance card. Most online listings show it too; ask the seller for it before you go see the car.'),
         ('Does it work for cars in Canada?', 'The decode does. Recall lists come from the U.S. (NHTSA); a car sold in Canada can have different recalls, so the report links Transport Canada&#39;s recall search.')]
VR_FAQ = [(_vrre.sub(r'&#39;', "'", q), '', _vrre.sub(r'&#39;', "'", a)) for q, a in VR_QA]
VR_SEO = (f'<section class="vr-seo"><h2>Free VIN check: the model-year&#39;s record, not the car&#39;s history</h2>'
          f'<p>This VIN lookup decodes the VIN, then shows the record of the model year it belongs to: the Lemon Index score from owner complaints to NHTSA per car sold, '
          f'the 3 problem areas owners reported most, complaint and recall counts, a YouTube rank, and what to check on a test drive. It covers {VR_NM} models and {VR_NY:,} model years. '
          f'It is not a vehicle history report: it can&#39;t see this car&#39;s accidents, owners, title or service records.</p>'
          '<h3>What the report shows</h3><ul class="vr-list"><li><b>The car:</b> year, make, model, trim, engine, drive and where it was built, from NHTSA&#39;s vPIC VIN decoder.</li>'
          '<li><b>Reliability of that model year:</b> its Lemon Index score and verdict, the 3 biggest complaint areas and how many complaints it drew.</li>'
          '<li><b>Recalls:</b> every NHTSA recall for that make, model and year, live from NHTSA, with the ones that cover another engine marked.</li>'
          '<li><b>Test drive checklist:</b> one check for each of that year&#39;s top complaint areas, nothing generic.</li>'
          '<li><b>A share card:</b> one screen with the score, the risks and the recall count, to send to whoever you&#39;re buying with.</li></ul>'
          '<h2>Questions</h2>' + qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in VR_QA)) + '</section>')

# 11-19 v5: the same text as title-only tap-to-open boxes (the page's v5 look); VR_SEO stays for anything else that uses it
VR_BOXES = ('<div class="cpl v5-pl">'
            + V5_BOX('question', 'Buying? Ask for the VIN first', '<p class="yc-cap">Ask the seller for the VIN before you go see the car. Honest sellers share it; it&#39;s also in most online listings and on the windshield.</p>')
            + V5_BOX('data', 'What the free VIN check shows', VR_SEO.split('<h2>Questions</h2>')[0].replace('<section class="vr-seo">', '').replace("<h2>Free VIN check: the model-year&#39;s record, not the car&#39;s history</h2>", '<h2 class="v5-bh">Free VIN check: the model-year&#39;s record, not the car&#39;s history</h2>'))
            + V5_BOX('talk', 'Questions', qa_fold(''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in VR_QA)))
            + V5_GO('warning', 'Recalls by make and model', '/recalls/')
            + '</div>')
