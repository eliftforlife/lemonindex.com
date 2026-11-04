# YouTube repair-video data for car-year pages (11-04, Elijah: "pull data from yt vids... helps people find videos to fix their car").
# Input: <Lemon Index>/data/yt/<study>/videos.json (from search.py + extract.py there: yt-dlp search, captions, transcript facts).
# Output: data/yt.json {family id: {years, gen, n, views, hours, topics: [{name, views, n, best}], guides: [video]}}
# We show counts, view totals, titles and links only. No transcript text is republished. Ranking is by the video TITLE's topic
# (cleaner than transcript mentions); views = how many people looked that fix up, not how often it breaks.
import json, os, re, collections
SRC = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\yt'
STUDIES = [  # study folder, site family id, site years it applies to, generation label
    ('f150-1999', 'ford-f-series', [2000, 2001, 2002, 2003], '1997–2003 F-150'),
]
TOPIC = [  # first match wins; order matters
 ('Reviews & buyer guides', r'review|buyer|should you buy|problems|watch this before|what is a|for sale|walk ?around|spotlight|sold\b'),
 ('Fuel pump, filter & tank', r'fuel pump|fuel filter|gas tank|fuel pressure'),
 ('No-start: theft light, key & ignition', r'theft|anti-?theft|ignition lock|code 11|no start|won.?t start|cranks? but|ground'),
 ('Transmission & shifter', r'transmission|shifter|output speed|clutch'),
 ('Heat, A/C & blend door', r'heater|blend door|\bac\b|a/c|blower|cabin air'),
 ('Spark plugs & ignition coils', r'spark plug|ignition coil|coils'),
 ('Intake, EGR & engine sensors', r'intake|egr|idle air|mass air|p0171|vacuum leak|misfire|crankshaft position|oil pressure'),
 ('Brakes & ABS', r'brake|abs\b|caliper'),
 ('Steering & suspension', r'ball joint|control arm|shock|sway bar|wheel bearing|tie rod|lift'),
 ('Driveshaft, axles & 4x4', r'u-?joint|universal joint|driveshaft|axle|4wd|4x4|transfer case'),
 ('Windows, doors & mirrors', r'window|door|lock actuator|mirror'),
 ('Gauges, lights & wiring', r'odometer|gauge|light|horn|fuse|relay|combination switch'),
 ('Cooling system', r'coolant|radiator|thermostat|water pump'),
 ('Starter, alternator & belts', r'alternator|starter|battery|serpentine|tensioner|idler'),
 ('Oil changes & leaks', r'oil|valve cover|gasket'),
]
NOT_REPAIR = re.compile(r'coyote|redesign|fast and the furious|performance headlight|fog light|oil separator|exhaust$|thrush|american eagle|lightning \|resurrection|detail', re.I)
out = {}
for study, fid, years, gen in STUDIES:
    R = json.load(open(os.path.join(SRC, study, 'videos.json'), encoding='utf-8'))
    T, G = collections.defaultdict(list), []
    for r in R:
        t = r['title']; top = next((n for n, p in TOPIC if re.search(p, t, re.I)), None)
        v = dict(id=r['id'], title=re.sub(r'\s+', ' ', t.replace('\ufffd', "'")).strip(), channel=r['channel'], views=r['views'], dur=r['dur'])
        if top == 'Reviews & buyer guides' and not NOT_REPAIR.search(t): G.append(v)
        elif top and not NOT_REPAIR.search(t): T[top].append(v)
    topics = sorted(({'name': n, 'views': sum(v['views'] for v in vs), 'n': len(vs), 'best': max(vs, key=lambda v: v['views']),
                      'more': sorted(vs, key=lambda v: -v['views'])[1:4]} for n, vs in T.items()), key=lambda d: -d['views'])
    out[fid] = dict(years=years, gen=gen, n=len(R), views=sum(r['views'] for r in R), hours=round(sum(r['dur'] for r in R) / 3600),
                    topics=topics, guides=sorted(G, key=lambda v: -v['views'])[:4])
    print(fid, len(R), 'videos;', ', '.join(f"{t['name']} {t['views'] / 1e6:.2f}M/{t['n']}" for t in topics[:8]), '| guides', len(G))
json.dump(out, open('data/yt.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
