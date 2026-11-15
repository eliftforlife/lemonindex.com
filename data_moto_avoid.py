# "Years to avoid" blocks (11-14) for the 10 bikes in the first @lemonindexmotorcycle videos -> data/moto_avoid.json, shown by vehicles_pages.py
# on the matching motorcycle page (a family page, or the bike's own page for the Street Glide and Road King).
# The numbers are the videos' own: NHTSA complaints API (complaintsByVehicle / recallsByVehicle), model years 2005-2024, pulled 2026-11-14 by the
# two motorcycle builders (3 Lemon Index/motorcycles/data/<bike>.json + method.md). The chart reads per_year from those files; the year notes and
# recall lines below repeat what the videos say (method.md tables, findings_used_in_short). Every campaign id is checked against the files.
# Photos: the same Wikimedia Commons photos the videos used, with their credits -> assets/v/moto/real/<key>.webp (copied to docs/ by the build) (900 px wide).
# COUNTS, NEVER RATES: there are no sales figures per motorcycle model year.
import json, os, sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
LI = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
RES = os.path.join(LI, 'motorcycles', 'data'); PHOTOS = r'C:\Users\elift\Desktop\Eliftforlife youtube\0 HQ\hero3d\assets\moto'
OUTP = os.path.join(HERE, 'assets', 'v', 'moto', 'real'); os.makedirs(OUTP, exist_ok=True)
C = lambda t, a, l, lu, pg: dict(title=t, author=a, license=l, license_url=lu, page=pg)
SA3, SA4, BY2, BY3 = 'https://creativecommons.org/licenses/by-sa/3.0', 'https://creativecommons.org/licenses/by-sa/4.0', 'https://creativecommons.org/licenses/by/2.0', 'https://creativecommons.org/licenses/by/3.0'
A = [
 dict(page='harley-davidson-street-glide', key='street-glide', file='harley-street-glide.json', bike='Street Glide', models='FLHX, FLHXS, FLHXSE and the other Street Glide codes',
      photo=('street-glide-2011.jpg', C('Paris - Salon de la moto 2011 - Harley-Davidson - FLHX Street Glide - 001', 'Thesupermat', 'CC BY-SA 3.0', SA3, 'https://commons.wikimedia.org/wiki/File:Paris_-_Salon_de_la_moto_2011_-_Harley-Davidson_-_FLHX_Street_Glide_-_001.jpg')),
      years=[(2008, 'Brakes are the top complaint (8).', ['18V076000', '08V357000']), (2009, 'Electrical is the top complaint.', ['18V076000']),
             (2010, 'Brakes are the top complaint (14).', ['18V076000']), (2014, 'Three clutch recalls on this year.', ['13V515000', '14V537000', '15V216000'])],
      after='Since 2019, no Street Glide year drew more than 13.'),
 dict(page='harley-davidson-sportster', key='sportster', file='harley-sportster.json', bike='Sportster', models='every XL 883 and XL 1200 code, Iron 883 included',
      photo=('sportster-883.jpg', C('Harley-Davidson Sportster 883', 'Nacho from Oviedo', 'CC BY 2.0', BY2, 'https://commons.wikimedia.org/wiki/File:Harley-Davidson_Sportster_883.jpg')),
      years=[(2005, '', ['04V607000']), (2006, '', []), (2007, 'Electrical is the top complaint (8 of 16).', ['06V476000'])],
      after='From 2008 on, no Sportster year drew more than 9.'),
 dict(page='harley-davidson-street-500-750', key='street-750', file='harley-street-750.json', bike='Street 750', models='XG750 and XG750A',
      photo=('street-750.jpg', C('2014 Harley-Davidson Street 750 side view', 'Ryan Urlacher', 'CC BY 2.0', BY2, 'https://commons.wikimedia.org/wiki/File:2014_Harley-Davidson_Street_750_side_view.jpg')),
      years=[(2015, 'Its first year. 58 of 79 list the fuel system: owners say it stalls or surges, often when the tank runs low.', ['15V474000'])],
      after='The 2016 to 2018 drew 6, 7 and 3, but 2016-2019 Street 750s were recalled for brake calipers that can corrode and drag (18V927000).'),
 dict(page='kawasaki-ninja-300-400-650', key='ninja-300', file='kawasaki-ninja-300-400.json', bike='Ninja 300 / 400', models='Ninja 300 (EX300) and Ninja 400 (EX400); not the 250, 500 or 650',
      photo=('ninja-300-2013.jpg', C('2013 Kawasaki Ninja 300 Seattle Motorcycle Show', 'Dennis Bratland', 'CC BY-SA 3.0', SA3, 'https://commons.wikimedia.org/wiki/File:2013_Kawasaki_Ninja_300_Seattle_Motorcycle_Show.jpg')),
      years=[(2013, 'The first Ninja 300. 44 of 56 describe the engine stalling, mostly while slowing down.', ['13V328000'])],
      after='After 2013, no year drew more than 3. Some 2021 Ninja 400s were recalled for the cam chain tensioner (20V774000).'),
 dict(page='yamaha-yzf-r1', key='r1', file='yamaha-yzf-r1.json', bike='YZF-R1', models='YZF-R1, R1M and R1S codes',
      photo=('yzf-r1-2007.jpg', C('YAMAHA YZF-R1 2007TMS', 'PekePON', 'CC BY-SA 3.0', SA3, 'https://commons.wikimedia.org/wiki/File:YAMAHA_YZF-R1_2007TMS.jpg')),
      years=[(2007, '75 of 90 mention second gear: the bike lags, then surges. No recall covers it.', []), (2015, 'The redesigned R1.', ['15V802000'])],
      after='Most other years drew 10 or fewer.'),
 dict(page='honda-gold-wing', key='gold-wing', file='honda-gold-wing.json', bike='Gold Wing', models='GL1800 codes; not the Valkyrie', skip=[2011, 2017],
      photo=('b-goldwing-gl1800-2001-10.jpg', C('Honda Gold Wing GL1800 White', 'Midnight Runner', 'CC BY-SA 3.0', SA3, 'https://commons.wikimedia.org/wiki/File:Honda_Gold_Wing_GL1800_White.jpg')),
      years=[(2008, 'Brakes are the top complaint (12): the rear brakes drag or lock.', ['15V700000', '11V567000']), (2012, '20 of 31 describe a stumble at low speed.', []),
             (2018, 'The first year of the new Gold Wing.', ['24V820000', '24V113000'])],
      after='There was no 2011 or 2017 Gold Wing in the US.'),
 dict(page='harley-davidson-road-king', key='road-king', file='harley-davidson-road-king.json', bike='Road King', models='FLHR, FLHRC, FLHRCI, FLHRS and the other Road King codes',
      photo=('b-roadking-2006.jpg', C('Harley-Davidson Road King Custom 2006', 'Nitot', 'CC BY-SA 3.0', SA3, 'https://commons.wikimedia.org/wiki/File:Harley-Davidson_Road_King_Custom_2006.jpg')),
      years=[(2008, '15 of 30 describe throttle, power-loss or cruise control problems.', ['08V357000', '18V076000']), (2007, 'Engine and power train lead (7 each).', []),
             (2009, 'Brakes are the top complaint (9).', ['18V076000'])],
      after='After 2011, no Road King year drew more than 7.'),
 dict(page='bmw-gs-r1200-r1250gs', key='r1200gs', file='bmw-r-gs.json', bike='R 1200 GS / R 1250 GS', models='R 1200 GS, GS Adventure, R 1250 GS and GS Adventure',
      photo=('b-r1200gs-hexhead.jpg', C('R1200GS 2004', 'Gsmonkey', 'CC BY 3.0', BY3, 'https://commons.wikimedia.org/wiki/File:R1200GS_2004.jpg')),
      years=[(2007, '42 of 65 are about fuel, 20 about a cracked fuel pump flange leaking gas.', ['13V617000', '20V471000']), (2005, 'Final drive (16) and fuel (13) lead.', ['13V617000']),
             (2008, '35 mention fuel.', ['13V617000']), (2009, 'Fuel system is the top complaint (19).', ['13V617000'])],
      after='From 2010 on, no year drew more than 19.'),
 dict(page='suzuki-gsx-r', key='gsx-r600-750', file='suzuki-gsx-r600-750.json', bike='GSX-R600 / GSX-R750', models='GSX-R600 and GSX-R750 codes; not the GSX-R1000',
      photo=('b-gsxr750-2006.jpg', C('2006 gsxr750', 'Maoisn (en.wikipedia)', 'CC BY-SA 3.0', SA3, 'https://commons.wikimedia.org/wiki/File:2006_gsxr750.jpg')),
      years=[(2007, 'More than half (39 of 73) mention the throttle, and 8 report a fire, most tied to the charging system.', ['13V449000']), (2006, '29 of 51 mention the same jerky throttle.', ['13V449000'])],
      after='From 2009 on, no year drew more than 1. The 2007 drew more complaints than every other year since 2005 combined.'),
 dict(page='kawasaki-klr650', key='klr650', file='kawasaki-klr650.json', bike='KLR650', models='KLR650 codes', skip=[2019, 2020, 2021],
      photo=('b-klr650-2009.jpg', C('2009 black Kawasaki KLR 650', 'Carsamar', 'CC BY-SA 4.0', SA4, 'https://commons.wikimedia.org/wiki/File:2009_black_Kawasaki_KLR_650.jpg')),
      years=[(2008, 'The first of the redesigned KLR. 84 of 116 say the turn signals fell off, some onto the hot exhaust.', ['07V244000']), (2023, 'All 16 are about the steering, often catching at low speed.', [])],
      after='Most other years have no complaints on file. There was no 2019-2021 KLR650 in the US.'),
]
# each cited recall in one plain sentence, written from its NHTSA summary and consequence (shown under the year)
RTXT = {
 '18V076000': 'If old brake fluid leaves deposits, a valve in the ABS unit can stick and reduce braking (2008-2011 Touring bikes with ABS).',
 '08V357000': 'The fuel filter shell can crack and drop fuel pressure, so the engine can stall or not start (2008 Touring bikes).',
 '13V515000': 'Air in the clutch system or a wrong clutch release plate can keep the clutch from disengaging.',
 '14V537000': 'A part in the clutch master cylinder can fail, so the clutch may not stay disengaged and the bike can creep forward.',
 '15V216000': 'The clutch master cylinder may not disengage the clutch, especially after the bike sits parked for a while.',
 '04V607000': 'The fuel valve ON and RESERVE positions may be reversed, so the bike can run dry with no reserve.',
 '06V476000': 'The voltage regulator can catch the front fender and make the bike hard to steer.',
 '15V474000': 'A poor seal at the fuel pump inlet can interrupt the fuel supply: a hesitation, then power comes back abruptly.',
 '13V328000': 'An engine computer (ECU) setting can make the bike stall while slowing down.',
 '15V802000': 'Transmission gears can fail and lock up.',
 '15V700000': 'The rear brake can drag after it is released, and long rides with it dragging can get hot enough to start a fire (2001-2010 and 2012-2015).',
 '11V567000': 'The linked brakes\' secondary master cylinder can make the rear brake drag.',
 '24V820000': 'The primary drive gear bolt can break, stalling the engine and locking the rear wheel (2018-2021).',
 '24V113000': 'Fuel pump impellers can deform and the pump can fail, stalling the engine (2018-2024).',
 '13V617000': 'The fuel pump flange can crack and leak fuel, a fire risk (2005-2011 R models).',
 '20V471000': 'A follow-up to 13V617000: on bikes that got the support-ring fix, the flange can still crack and leak fuel.',
 '13V449000': 'Corrosion inside the front brake master cylinder can reduce front braking (2004-2013 GSX-R600 and GSX-R750).',
 '07V244000': 'The side stand spring pin may not be fully welded and can fall out, letting the stand drop while riding.',
}
out = {}
for a in A:
    d = json.load(open(os.path.join(RES, a['file']), encoding='utf-8'))
    py = {int(y): v for y, v in d['per_year'].items()}
    rec = {}
    for y, v in py.items():
        rl = v.get('recall_list') if isinstance(v.get('recall_list'), list) else (v['recalls'] if isinstance(v.get('recalls'), list) else [])
        for r in rl:
            c = rec.setdefault(r['campaign'], dict(id=r['campaign'], part=(r.get('component') or '').split(':')[0], summary=' '.join((r.get('summary') or '').split()), consequence=' '.join((r.get('consequence') or '').split()), years=[]))
            c['years'].append(y)
    yrs = sorted(y for y in py if y not in a.get('skip', []))
    chart = [[y, py[y]['complaints']] for y in yrs]
    # trim leading/trailing empty years so the chart starts and ends where the bike has data (inside 2005-2024)
    while chart and chart[0][1] == 0: chart.pop(0)
    while chart and chart[-1][1] == 0 and chart[-1][0] < 2024: chart.pop()
    ys = []
    for y, note, rids in a['years']:
        for r in rids: assert r in rec, (a['key'], r)
        ys.append(dict(y=y, n=py[y]['complaints'], note=note, recalls=[dict(id=r, plain=RTXT[r], years=[min(rec[r]['years']), max(rec[r]['years'])], part=rec[r]['part'], summary=rec[r]['summary'], consequence=rec[r]['consequence']) for r in rids]))
    src, cred = a['photo']
    im = Image.open(os.path.join(PHOTOS, src)).convert('RGB'); w = 900; h = round(im.height * w / im.width)
    im.resize((w, h), Image.LANCZOS).save(os.path.join(OUTP, a['key'] + '.webp'), 'WEBP', quality=82)
    out[a['page']] = dict(bike=a['bike'], models=a['models'], chart=chart, years=ys, after=a['after'], total=sum(n for _, n in chart),
                          photo=dict(src=f'/assets/v/moto/real/{a["key"]}.webp', w=w, h=h, **cred))
    print(f"{a['page']:32} {a['bike']:22} chart {chart[0][0]}-{chart[-1][0]} total {out[a['page']]['total']}  avoid {[(x['y'], x['n']) for x in ys]}")
json.dump(out, open(os.path.join(HERE, 'data', 'moto_avoid.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
