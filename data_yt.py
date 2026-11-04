# YouTube video data for the site (11-04, Elijah: "pull data from yt vids... helps people find videos to fix their car").
# Input: <Lemon Index>/data/yt/<study>/videos.json (study.py / f150-1999 there: yt-dlp search, top ~100 by views, captions).
# Output: data/yt.json {page key: [entry]}; keys: <car id> (year pages, with years), model:<car id>, plane:<slug>, super:<slug>, moto:<slug>.
# We show counts, view totals, titles, thumbnails and links only; no transcript text is republished. Each video goes in ONE topic,
# picked from its TITLE (first match wins). Views = how many people watched, not how often something breaks.
import json, os, re
SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\yt'
Y = lambda a, b: list(range(a, b + 1))
STUDIES = [  # study, page key, years (year pages only), what it covers, kind, noun
 ('f150-1999', 'ford-f-series', Y(2000, 2003), '1997–2003 F-150', 'repair', 'truck'),
 ('bmw-f30', 'bmw-3-series', Y(2012, 2018), '2012–2018 BMW 3 Series (F30)', 'repair', 'car'),
 ('wrangler-jk', 'jeep-wrangler', Y(2007, 2018), '2007–2018 Jeep Wrangler (JK)', 'repair', 'Jeep'),
 ('rav4-2026', 'model:toyota-rav4', None, '2026 Toyota RAV4', 'new', ''),
 ('model-y-2026', 'model:tesla-model-y', None, '2026 Tesla Model Y', 'new', ''),
 ('cessna-172', 'plane:cessna-172-skyhawk', None, 'Cessna 172', 'plane', ''),
 ('cirrus-sr22', 'plane:cirrus-sr22', None, 'Cirrus SR22', 'plane', ''),
 ('huracan', 'super:lamborghini-hurac-n', None, 'Lamborghini Huracán', 'super', ''),
 ('ferrari-458', 'super:ferrari-458-italia', None, 'Ferrari 458', 'super', ''),
 ('sportster', 'moto:harley-davidson-sportster', None, 'Harley-Davidson Sportster', 'moto', ''),
 ('ninja-400', 'moto:kawasaki-ninja-300-400-650', None, 'Kawasaki Ninja 300 / 400 / 650', 'moto', ''),
]
GUIDE = {'repair': 'Reviews & buyer guides', 'plane': 'Buying advice', 'super': 'Buying advice & used', 'moto': 'Buying advice'}
TOPICS = {
 'repair': [
  ('Reviews & buyer guides', r'review|buyer|should you buy|problems|watch this before|what is a|for sale|walk ?around|spotlight|sold\b|reliab|worst|avoid|things to know'),
  ('Fuel pump, filter & tank', r'fuel pump|fuel filter|gas tank|fuel pressure|injector'),
  ('No-start: theft light, key & ignition', r'theft|anti-?theft|ignition lock|code 11|no start|won.?t start|cranks? but|ground|tipm'),
  ('Death wobble & steering', r'death wobble|track bar|steering|tie rod|drag link|steering box|stabilizer'),
  ('Transmission & shifter', r'transmission|shifter|output speed|clutch|gearbox'),
  ('Timing chain & engine', r'timing chain|guide|head gasket|engine (rebuild|swap|noise|tick|knock)|misfire|rod bearing|vanos|carbon'),
  ('Oil leaks & gaskets', r'oil (leak|filter housing|pan|cooler)|valve cover|gasket|rear main|ofhg'),
  ('Heat, A/C & blend door', r'heater|blend door|\bac\b|a/c|blower|cabin air|hvac'),
  ('Spark plugs & ignition coils', r'spark plug|ignition coil|coils'),
  ('Intake, EGR & engine sensors', r'intake|egr|idle air|mass air|p0171|vacuum leak|crankshaft position|oil pressure|sensor|throttle'),
  ('Cooling system', r'coolant|radiator|thermostat|water pump|overheat|expansion tank'),
  ('Brakes & ABS', r'brake|abs\b|caliper|rotor'),
  ('Steering & suspension', r'ball joint|control arm|shock|sway bar|wheel bearing|strut|bushing|suspension'),
  ('Driveshaft, axles & 4x4', r'u-?joint|universal joint|driveshaft|axle|4wd|4x4|transfer case|differential'),
  ('Windows, doors & mirrors', r'window|door|lock actuator|mirror|soft top|hard top|roof'),
  ('Gauges, lights & wiring', r'odometer|gauge|light|horn|fuse|relay|combination switch|battery|idrive|electrical'),
  ('Starter, alternator & belts', r'alternator|starter|serpentine|tensioner|idler|belt'),
  ('Oil changes & service', r'oil change|oil|service|maintenance|reset'),
 ],
 'new': [
  ('Problems, recalls & complaints', r'problem|issue|recall|complain|regret|wrong|worst|flaw|don.?t buy|hate|broke|disappoint'),
  ('Owner reviews & long-term', r'owner|ownership|long.?term|\d+ ?(months?|miles|weeks?|k)|living with|one year|1 year|after'),
  ('Versus rivals', r'\bvs\.?\b|versus|compar|better than'),
  ('Range, MPG & charging', r'mpg|range|fuel|efficien|charg|battery|kwh|economy|supercharg'),
  ('Price, trims & which to buy', r'price|cost|trim|which|lease|deal|worth|msrp|\$|buy'),
  ('Interior, tech & features', r'interior|tech|feature|screen|software|fsd|autopilot|how to|tips|hidden|setting'),
  ('Off-road, towing & tests', r'off.?road|tow|test|0-60|acceleration|snow|winter|track|crash'),
  ('Reviews & first drives', r'.'),
 ],
 'plane': [
  ('Buying advice', r'\bbuy|buying|should you|worth it|used|pre-?buy|before you|which plane'),
  ('Cost of owning', r'cost|price|expens|cheap|afford|own(ing|ership)|budget|money|how much|\$'),
  ('Accidents, emergencies & the parachute', r'crash|accident|emergency|engine failure|engine out|parachute|caps|ntsb|spin|stall|fire|mayday|forced landing|ditch'),
  ('Maintenance, annuals & upgrades', r'annual|maintenance|inspection|oil change|repair|restor|rebuild|overhaul|paint|interior|panel|upgrade|install|avionic|g1000|garmin|engine'),
  ('Reviews & walkarounds', r'review|walk ?around|tour|vs\.?|compar|everything|test'),
  ('Flying it: landings, lessons & checkrides', r'.'),
 ],
 'super': [
  ('Buying advice & used', r'\bbuy|buying|used|should you|worth|before you|mistake|cheapest'),
  ('Cost of owning', r'cost|own(ing|ership)|price|expens|cheap|afford|money|insurance|depreciat|\$|paid|bill'),
  ('Service, problems & repairs', r'service|maintenance|oil change|clutch|brake|tire|repair|fix|broke|problem|issue|warranty|engine|wreck|crash|destroyed|salvage'),
  ('Living with it', r'daily|long.?term|living with|year|months|miles|owner|after|week'),
  ('Mods, exhaust & tuning', r'exhaust|mod|tune|twin turbo|wrap|wheels|install|upgrade|carbon|straight pipe'),
  ('Versus rivals', r'\bvs\.?\b|versus|compar|better than'),
  ('Reviews, drives & sound', r'.'),
 ],
 'moto': [
  ('Buying advice', r'\bbuy|buying|used|should you|worth|before you|mistake|watch this|don.?t'),
  ('Beginner & learning to ride', r'beginner|first bike|new rider|learn|starter|should i'),
  ('Problems & repairs', r'problem|issue|fix|broke|repair|won.?t|leak|recall|stall|noise|crash'),
  ('Maintenance & DIY', r'oil|chain|service|maintenance|valve|battery|tire|brake|diy|how to|install|clean|change'),
  ('Mods & upgrades', r'mod|exhaust|upgrade|custom|build|bobber|cafe|slip.?on|stage|turned'),
  ('Long-term & high mileage', r'long.?term|miles|year|months|after|owner|ownership|high mileage'),
  ('Versus rivals', r'\bvs\.?\b|versus|compar'),
  ('Reviews & rides', r'.'),
 ],
}
HEAD = {'repair': 'Fixes owners look up most.', 'new': 'What buyers watch before they buy.', 'plane': 'What pilots and owners watch most.',
        'super': 'What owners and buyers watch most.', 'moto': 'What riders watch most.'}
NOT_REPAIR = re.compile(r'coyote|redesign|fast and the furious|performance headlight|fog light|oil separator|exhaust$|thrush|american eagle|resurrection|detail', re.I)
out = {}
for study, key, years, gen, kind, noun in STUDIES:
    p = os.path.join(SRC, study, 'videos.json')
    if not os.path.exists(p): print('missing', study); continue
    R = json.load(open(p, encoding='utf-8')); T, G = {}, []
    for r in R:
        t = re.sub(r'\s+', ' ', r['title'].replace('\ufffd', "'")).strip()
        if kind == 'repair' and NOT_REPAIR.search(t): continue
        if re.search(r'simulator|\bgame\b|\bgta\b|forza|roblox|beamng|\brc\b', t, re.I): continue   # games / toys, not the real thing
        top = next((n for n, pat in TOPICS[kind] if re.search(pat, t, re.I)), None)
        if not top: continue
        v = dict(id=r['id'], title=t, channel=r['channel'], views=r['views'])
        (G if top == GUIDE.get(kind) else T.setdefault(top, [])).append(v)
    topics = sorted(({'name': n, 'views': sum(v['views'] for v in vs), 'n': len(vs), 'best': max(vs, key=lambda v: v['views'])} for n, vs in T.items()), key=lambda d: -d['views'])
    G.sort(key=lambda v: (kind == 'repair' and not re.search(r'problem|buyer|should you buy|reliab', v['title'], re.I), -v['views']))
    costs = None; cp = os.path.join(SRC, study, 'costs.json')
    if os.path.exists(cp):
        C = json.load(open(cp, encoding='utf-8'))
        def pick(xs, minv=2):
            if len({x['id'] for x in xs}) < minv: return None
            vs = sorted(x['v'] for x in xs); n = len(vs); md = vs[n // 2] if n % 2 else (vs[n // 2 - 1] + vs[n // 2]) / 2
            q1, q3 = (vs[n // 4], vs[(3 * n) // 4 - (1 if n % 4 == 0 else 0)]) if n >= 4 else (vs[0], vs[-1])   # middle half when there are enough
            ref = min(xs, key=lambda x: (abs(x['v'] - md) / max(md, 1) > .25, -x['views']))
            return dict(median=round(md), lo=q1, hi=q3, n=n, videos=len({x['id'] for x in xs}), id=ref['id'], t=ref['t'], title=ref['title'])
        paid = pick(C['paid'], 3)
        if paid: paid['private'] = sum(x['private'] for x in C['paid']); paid['dealer'] = sum(x['dealer'] for x in C['paid'])
        used = pick(C['used'], 3); msrp = pick(C['new'], 3)
        LBL = {'Hangar / tie-down': 'Hangar / tie-down (usually monthly)'}
        ok = lambda x: x and (x['videos'] >= 3 or x['hi'] <= 3 * max(x['lo'], 1))   # 2 videos only count when they roughly agree
        items = sorted(((LBL.get(k, k), pick(v)) for k, v in C['items'].items() if ok(pick(v))), key=lambda kv: -kv[1]['videos'])[:8]
        costs = dict(paid=paid, used=used, msrp=msrp, items=items) if (paid or used or msrp or items) else None
    out.setdefault(key, []).append(dict(years=years, gen=gen, kind=kind, noun=noun, head=HEAD[kind], n=len(R), views=sum(r['views'] for r in R), topics=topics[:8], guides=G[:3], costs=costs))
    print(f'{study:14} {len(R):3} videos {sum(r["views"] for r in R) / 1e6:6.1f}M | ' + ' · '.join(f"{t['name']} {t['views'] / 1e6:.1f}M" for t in topics[:4]) + f' | guides {len(G)} | costs ' + (', '.join(k for k, _ in costs['items']) + (' +paid' if costs['paid'] else '') + (' +used' if costs['used'] else '') + (' +msrp' if costs['msrp'] else '') if costs else 'none'))
json.dump(out, open('data/yt.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
