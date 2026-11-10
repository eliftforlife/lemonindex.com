# BMW specs + engines (11-10, Elijah: "people want engine / spec data for cars, do a full build for the BMW first").
# Writes data/bmw_specs.json for bmw_pages.py (exec'd by build.py). Run:  py -X utf8 data_bmw_specs.py
#
# Sources:
#   - EPA fueleconomy.gov vehicles.csv (public domain): every BMW version per model year: engine size, cylinders, turbo, fuel,
#     transmission, drive, hybrid/EV type, MPG. Cached in data/cache/ (gitignored).
#   - Engine codes + power/torque: NOT in EPA. Mapped below (RULES) from Wikipedia's BMW engine articles (application lists,
#     manufacturer ratings), each rule citing its article. A version with no rule shows EPA data only ("engine code not confirmed").
#   - Owner complaints: NHTSA, from 3 Lemon Index/data/complaints.db (table rows), counted by distinct complaint id.
#   - Recalls (new model pages only): NHTSA recallsByVehicle API.
#
# Engine x year reliability (Elijah 11-10: "each year for each engine and its reliability"). NHTSA files complaints by
# make/model/year, not engine, so every number says how it was attributed:
#   (a) the NHTSA model name identifies the version (BMW owners often file "335I" vs "328I"), and in that year that version
#       name maps to exactly one engine -> complaint count for that engine-year (no per-car rate: no sales by version)
#   (b) every version of a model in that year used the same engine -> the model-year's Lemon Index (per car sold) is a real
#       per-car score for that engine (only where we have sales: 3/5 Series, X1, X3, X5)
#   (c) complaints whose own text names the engine code (e.g. "N54")
#   combined: the model-year had several engines under one NHTSA name -> its score is shown as "all engines combined"
import csv, io, json, os, re, sqlite3, sys, time, urllib.parse, urllib.request, zipfile, collections
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
EPA_ZIP = os.path.join(HERE, 'data', 'cache', 'vehicles.csv.zip')
OUT = os.path.join(HERE, 'data', 'bmw_specs.json')
YMAX = 2026
W = 'https://en.wikipedia.org/wiki/'

if not os.path.exists(EPA_ZIP):
    os.makedirs(os.path.dirname(EPA_ZIP), exist_ok=True)
    urllib.request.urlretrieve('https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip', EPA_ZIP)

# ---- families: the 5 with Lemon Index pages already, plus new ones (complaints only, no sales -> no index)
FAM = {
    'bmw-2-series': 'BMW 2 Series', 'bmw-3-series': 'BMW 3 Series', 'bmw-4-series': 'BMW 4 Series', 'bmw-5-series': 'BMW 5 Series',
    'bmw-7-series': 'BMW 7 Series', 'bmw-x1': 'BMW X1', 'bmw-x2': 'BMW X2', 'bmw-x3': 'BMW X3', 'bmw-x4': 'BMW X4', 'bmw-x5': 'BMW X5',
    'bmw-x6': 'BMW X6', 'bmw-x7': 'BMW X7', 'bmw-z4': 'BMW Z4', 'bmw-i4': 'BMW i4', 'bmw-ix': 'BMW iX', 'bmw-m3': 'BMW M3', 'bmw-m5': 'BMW M5'}
HAS_INDEX = {'bmw-3-series', 'bmw-5-series', 'bmw-x1', 'bmw-x3', 'bmw-x5'}

def epa_family(base, model):
    m = model.strip()
    if base == '3 Series': return 'bmw-3-series'
    if base == '5 Series': return 'bmw-5-series'
    if base == '2 Series': return 'bmw-2-series'
    if base == '4 Series': return 'bmw-4-series'
    if base == '7 Series': return 'bmw-7-series'
    if base in ('X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'X7', 'Z4'): return 'bmw-' + base.lower()
    if base == 'ActiveHybrid X6': return 'bmw-x6'
    if base == 'i4': return 'bmw-i4'
    if base == 'iX': return 'bmw-ix'
    if base == 'M':
        if re.match(r'M3\b', m): return 'bmw-m3'
        if re.match(r'M5\b', m): return 'bmw-m5'
        if re.match(r'M340i', m): return 'bmw-3-series'
        if re.match(r'M550i', m): return 'bmw-5-series'
        if re.match(r'M2\b|M235i|M240i', m): return 'bmw-2-series'
        if re.match(r'M4\b|M440i', m): return 'bmw-4-series'
        if re.match(r'M760i', m): return 'bmw-7-series'
        if re.match(r'X5 M', m): return 'bmw-x5'
        if re.match(r'X6 M', m): return 'bmw-x6'
    return None

# NHTSA model strings -> family (whole-string regex on the uppercased model name)
NH = [('bmw-2-series', r'2 SERIES|2\d\d[A-Z ]*|M2|M2\d\d[A-Z]*'), ('bmw-3-series', r'3[ -]SERIES|3\d\d[A-Z ]*|M340I|ACTIVE HYBRID 3'),
      ('bmw-4-series', r'4\d\d[A-Z ]*|M4|M4\d\d[A-Z]*'), ('bmw-5-series', r'5[ -]SERIES.*|5\d\d[A-Z ]*|M550I|ACTIVE HYBRID 5'),
      ('bmw-7-series', r'7[ -]SERIES|7\d\d[A-Z ]*|M760I|ACTIVE HYBRID 7'), ('bmw-x1', r'X1( SAV)?'), ('bmw-x2', r'X2'), ('bmw-x3', r'X3( SAV)?'),
      ('bmw-x4', r'X4'), ('bmw-x5', r'X5( SAV| DIESEL SAV| HYBRID| M)?'), ('bmw-x6', r'X6( SAV| SAC| M| ACTIVEHYBRID SAC)?'), ('bmw-x7', r'X7'),
      ('bmw-z4', r'Z4( M40I)?'), ('bmw-i4', r'I4( .*)?'), ('bmw-ix', r'IX( .*)?'), ('bmw-m3', r'M3( US)?'), ('bmw-m5', r'M5')]
def nh_family(s):
    for fid, rx in NH:
        if re.fullmatch(rx, s): return fid
    return None

# version key from a model name: ('335', 'i'), ('M340', 'i'), ('328', 'd'), ('330', 'e'), ('335', 'is'), ('328', 'ci'); None for X/Z/i models
def vkey(name, epa=True):
    s = name.upper().replace(' ', '')
    m = re.match(r'^(M?)(\d{3})(L?)(IS|D|E|CI|CXI|C|XI|XD|I|IX|IT|IA|IC|LI|LXI|IL|ILA|XIT)?', s)
    if not m: return None
    num = m.group(1) + m.group(2); suf = (m.group(4) or '')
    if suf in ('D', 'XD'): k = 'd'
    elif suf in ('E',) or (epa and re.search(r'\d{3}E', s)): k = 'e'
    elif suf == 'IS': k = 'is'
    elif suf in ('CI', 'CXI', 'C', 'IC'): k = 'ci'
    else: k = 'i'
    return (num, k)

# ---- engine metadata (all from the cited Wikipedia articles; problem notes say "according to")
ENG = {
    'M54': dict(name='BMW M54', layout='inline-6', asp='naturally aspirated', size='2.5 L / 3.0 L', made='2000–2006', src=W + 'BMW_M54', notes=[]),
    'N52': dict(name='BMW N52', layout='inline-6', asp='naturally aspirated', size='3.0 L', made='2004–2015', src=W + 'BMW_N52',
                notes=['A 2017 recall covered a crankcase-ventilation valve heater that could short-circuit (about 740,000 BMW six-cylinder cars).',
                       'A 2023 recall covered VANOS bolts that could loosen or break.',
                       'The block is magnesium-aluminum; magnesium is more sensitive to corrosion and to creep at high temperature.']),
    'N54': dict(name='BMW N54', layout='inline-6', asp='twin-turbo', size='3.0 L', made='2006–2016', src=W + 'BMW_N54',
                notes=['High-pressure fuel pump (HPFP) failures led to a recall, a class action and a 10-year/120,000-mile US warranty extension.',
                       'Fuel injectors got a 10-year/120,000-mile US warranty extension and an updated design.',
                       'Wastegate rattle from bushing wear got an 8-year/82,000-mile US warranty extension.']),
    'N55': dict(name='BMW N55', layout='inline-6', asp='single twin-scroll turbo', size='3.0 L', made='2009–2021', src=W + 'BMW_N55', notes=[]),
    'N20': dict(name='BMW N20', layout='inline-4', asp='single twin-scroll turbo', size='2.0 L', made='2011–2017', src=W + 'BMW_N20',
                notes=['A 2017 class action alleged early failure of the plastic timing-chain guides, letting the chain skip and damage the engine; in 2019 a judge let some claims proceed.']),
    'B48': dict(name='BMW B48 / B46', layout='inline-4', asp='single twin-scroll turbo', size='2.0 L', made='2014–present', src=W + 'BMW_B48',
                notes=['US cars get the B46, a low-emissions (SULEV) version that the article calls essentially identical to the B48.']),
    'B58': dict(name='BMW B58', layout='inline-6', asp='single twin-scroll turbo', size='3.0 L', made='2015–present', src=W + 'BMW_B58', notes=[]),
    'N62': dict(name='BMW N62', layout='V8', asp='naturally aspirated', size='4.4 L / 4.8 L', made='2001–2010', src=W + 'BMW_N62', notes=[]),
    'N63': dict(name='BMW N63', layout='V8', asp='twin-turbo ("hot-vee")', size='4.4 L', made='2008–present', src=W + 'BMW_N63',
                notes=['In December 2014 BMW North America issued a voluntary "Customer Care Package" covering timing-chain stretch, fuel injectors, mass-air-flow sensors, crankcase vent lines, the battery, the vacuum pump and a low-pressure fuel sensor, plus a shorter oil-service interval.',
                       'A 2019 class action settlement covered oil consumption and battery drain.']),
    'S55': dict(name='BMW S55', layout='inline-6', asp='twin-turbo', size='3.0 L', made='2014–2021', src=W + 'BMW_N55', notes=[]),
    'S58': dict(name='BMW S58', layout='inline-6', asp='twin-turbo', size='3.0 L', made='2019–present', src=W + 'BMW_S58', notes=[]),
    'S63': dict(name='BMW S63', layout='V8', asp='twin-turbo ("hot-vee")', size='4.4 L', made='2009–present', src=W + 'BMW_S63', notes=[]),
    'S54': dict(name='BMW S54', layout='inline-6', asp='naturally aspirated', size='3.2 L', made='2000–2008', src=W + 'BMW_M54', notes=[]),
}

# ---- RULES: (code, family, model regex (on EPA model, case-insensitive, matched from the start), first MY, last MY, cyl, displ, hp, lb-ft)
# Model years are US model years as listed in the cited article's applications; hp/torque are the article's figures for that
# application (manufacturer ratings; US-rated figures can differ by a few hp). None = not stated clearly for that application.
R = []
def r(code, fam, rx, a, b, cyl, displ, hp=None, tq=None): R.append(dict(code=code, fam=fam, rx=rx, a=a, b=b, cyl=cyl, displ=displ, hp=hp, tq=tq))
# M54 (E46 / E39-E60 / E83 / E53 / E85)
r('M54', 'bmw-3-series', r'(325i|325xi)$', 2001, 2005, 6, '2.5', 189, 181); r('M54', 'bmw-3-series', r'325ci$', 2001, 2006, 6, '2.5', 189, 181)
r('M54', 'bmw-3-series', r'(330i|330xi)$', 2001, 2005, 6, '3.0', 228, 221); r('M54', 'bmw-3-series', r'330ci$', 2001, 2006, 6, '3.0', 228, 221)
r('M54', 'bmw-5-series', r'525i$', 2001, 2005, 6, '2.5', 189, 181); r('M54', 'bmw-5-series', r'530i$', 2001, 2005, 6, '3.0', 228, 221)
r('M54', 'bmw-x3', r'X3$', 2004, 2006, 6, None); r('M54', 'bmw-x5', r'X5$', 2001, 2006, 6, '3.0', 228, 221)
r('M54', 'bmw-z4', r'Z4$', 2003, 2005, 6, None)
# S54 (E46 M3, US rating per the article)
r('S54', 'bmw-m3', r'M3$', 2001, 2006, 6, '3.2', 333, 262)
# N52
r('N52', 'bmw-3-series', r'(325i|325xi)$', 2006, 2007, 6, '3.0', 215, 185); r('N52', 'bmw-3-series', r'(330i|330xi)$', 2006, 2006, 6, '3.0')
r('N52', 'bmw-3-series', r'328', 2007, 2013, 6, '3.0', 228, 199)
r('N52', 'bmw-5-series', r'(525i|525xi)$', 2006, 2007, 6, '3.0', 215, 185); r('N52', 'bmw-5-series', r'(530i|530xi)$', 2006, 2007, 6, '3.0')
r('N52', 'bmw-5-series', r'528', 2008, 2010, 6, '3.0', 228, 199); r('N52', 'bmw-5-series', r'528i$', 2011, 2011, 6, '3.0', 241, 229)
r('N52', 'bmw-x3', r'X3 (3\.0i|3\.0si|xDrive30i|xDrive28i)$', 2007, 2012, 6, '3.0'); r('N52', 'bmw-x5', r'X5 (3\.0si|xDrive30i)$', 2007, 2010, 6, '3.0')
r('N52', 'bmw-z4', r'Z4 3\.0i$', 2006, 2008, 6, '3.0', 215, 185); r('N52', 'bmw-z4', r'Z4 (3\.0si|sDrive30i)$', 2006, 2011, 6, '3.0')
# N54
r('N54', 'bmw-3-series', r'335(i|xi|ci|cxi)?( xDrive| Sport Wagon xDrive| Coupe xDrive)?$', 2007, 2010, 6, '3.0', 302, 295)
r('N54', 'bmw-3-series', r'335is$', 2011, 2013, 6, '3.0', 322, 332)
r('N54', 'bmw-5-series', r'535(i|xi)( xDrive)?$', 2008, 2010, 6, '3.0', 302, 295)
r('N54', 'bmw-x6', r'X6 xDrive35i$', 2008, 2010, 6, '3.0', 302, 295)
r('N54', 'bmw-z4', r'Z4 sDrive35i$', 2009, 2016, 6, '3.0', 302, 295); r('N54', 'bmw-z4', r'Z4 sDrive35is$', 2011, 2016, 6, '3.0', 335, None)
r('N54', 'bmw-7-series', r'740L?i$', 2011, 2012, 6, '3.0', 322, 332)
# N55
r('N55', 'bmw-3-series', r'335(i|ci)( xDrive| Coupe xDrive)?$', 2011, 2016, 6, '3.0', 302, 295)
r('N55', 'bmw-3-series', r'ActiveHybrid 3', 2013, 2015, 6, '3.0', 335, None)
r('N55', 'bmw-5-series', r'535i( xDrive)?$', 2011, 2017, 6, '3.0', 302, 295); r('N55', 'bmw-5-series', r'535i GT$', 2010, 2010, 6, '3.0', 302, 295); r('N55', 'bmw-5-series', r'ActiveHybrid 5', 2012, 2016, 6, '3.0', 335, None)
r('N55', 'bmw-x1', r'X1 xDrive35i$', 2013, 2015, 6, '3.0', 302, 295); r('N55', 'bmw-x3', r'X3 xDrive35i$', 2011, 2017, 6, '3.0', 302, 295)
r('N55', 'bmw-x4', r'X4 xDrive35i$', 2015, 2016, 6, '3.0', 302, 295); r('N55', 'bmw-x4', r'X4 M40i$', 2016, 2018, 6, '3.0', 355, 343)
r('N55', 'bmw-x5', r'X5 [xs]Drive35i$', 2011, 2018, 6, '3.0', 302, 295); r('N55', 'bmw-x6', r'X6 [xs]Drive35i$', 2011, 2019, 6, '3.0', 302, 295)
r('N55', 'bmw-4-series', r'435i( xDrive)?$', 2014, 2016, 6, '3.0', 302, 295); r('N55', 'bmw-2-series', r'M235i( xDrive)?$', 2014, 2016, 6, '3.0', 322, None)
r('N55', 'bmw-2-series', r'M2$', 2016, 2018, 6, '3.0', 365, 343)
r('N55', 'bmw-7-series', r'740L?i( xDrive)?$', 2013, 2015, 6, '3.0', 315, 332); r('N55', 'bmw-7-series', r'ActiveHybrid 7L$', 2013, 2015, 6, '3.0')
# N20
r('N20', 'bmw-3-series', r'328i( xDrive)?$', 2012, 2016, 4, '2.0', 241, 258); r('N20', 'bmw-3-series', r'320i( xDrive)?$', 2013, 2016, 4, '2.0', 181, 199)
r('N20', 'bmw-4-series', r'428i( xDrive)?$', 2014, 2016, 4, '2.0', 241, 258); r('N20', 'bmw-5-series', r'528i( xDrive)?$', 2012, 2016, 4, '2.0', 241, 258)
r('N20', 'bmw-2-series', r'228i( xDrive)?$', 2014, 2016, 4, '2.0', 241, 258)
r('N20', 'bmw-x1', r'X1 [xs]Drive28i$', 2013, 2015, 4, '2.0', 241, 258); r('N20', 'bmw-x3', r'X3 [xs]Drive ?28i$', 2013, 2017, 4, '2.0', 241, 258)
r('N20', 'bmw-x4', r'X4 xDrive28i$', 2015, 2018, 4, '2.0', 241, 258); r('N20', 'bmw-z4', r'Z4 sDrive28i$', 2012, 2016, 4, '2.0', 241, 258)
r('N20', 'bmw-x5', r'X5 xDrive40e$', 2016, 2018, 4, '2.0')
# B48 / B46
r('B48', 'bmw-3-series', r'330i( xDrive)?$', 2017, 2018, 4, '2.0', 248, 258); r('B48', 'bmw-3-series', r'330i( xDrive)?$', 2019, 2022, 4, '2.0', 255, 295)
r('B48', 'bmw-3-series', r'330i( xDrive)?$', 2023, 2024, 4, '2.0'); r('B48', 'bmw-3-series', r'330e( xDrive)?$', 2016, 2024, 4, '2.0')
r('B48', 'bmw-2-series', r'230i( xDrive)?$', 2017, 2021, 4, '2.0', 248, 258); r('B48', 'bmw-2-series', r'230i( xDrive)?$', 2022, 2024, 4, '2.0')
r('B48', 'bmw-2-series', r'228i( xDrive)?$', 2020, 2024, 4, '2.0', 228, 258); r('B48', 'bmw-2-series', r'M235i xDrive$', 2020, 2024, 4, '2.0', 302, 332)
r('B48', 'bmw-4-series', r'430i( xDrive)?$', 2017, 2020, 4, '2.0', 248, 258); r('B48', 'bmw-4-series', r'430i( xDrive)?$', 2021, 2024, 4, '2.0', 255, 295)
r('B48', 'bmw-5-series', r'530i( xDrive)?$', 2017, 2023, 4, '2.0', 248, 258); r('B48', 'bmw-5-series', r'530e( xDrive)?$', 2018, 2023, 4, '2.0')
r('B48', 'bmw-x1', r'X1 [xs]Drive28i$', 2016, 2022, 4, '2.0', 228, 258); r('B48', 'bmw-x1', r'X1 xDrive28i$', 2023, 2026, 4, '2.0', 241, 295)
r('B48', 'bmw-x1', r'X1 M35i$', 2024, 2026, 4, '2.0', 312, 295)
r('B48', 'bmw-x2', r'X2 [xs]Drive28i$', 2018, 2023, 4, '2.0', 228, 258); r('B48', 'bmw-x2', r'X2 M35i$', 2019, 2023, 4, '2.0', 302, 332)
r('B48', 'bmw-x2', r'X2 M35i$', 2024, 2026, 4, '2.0', 312, 295)
r('B48', 'bmw-x3', r'X3 [xs]Drive30i$', 2018, 2024, 4, '2.0', 248, 258); r('B48', 'bmw-x3', r'X3 xDrive30e$', 2020, 2021, 4, '2.0')
r('B48', 'bmw-x4', r'X4 xDrive30i$', 2019, 2025, 4, '2.0', 248, 258); r('B48', 'bmw-z4', r'Z4 sDrive30i$', 2019, 2026, 4, '2.0', 255, 295)
r('B48', 'bmw-7-series', r'740e xDrive$', 2017, 2019, 4, '2.0')
# B58
r('B58', 'bmw-3-series', r'340i( xDrive)?$', 2016, 2019, 6, '3.0', 322, 332); r('B58', 'bmw-3-series', r'M340i( xDrive)?$', 2020, 2024, 6, '3.0', 382, 369)
r('B58', 'bmw-3-series', r'M340i( xDrive)?$', 2025, 2026, 6, '3.0')
r('B58', 'bmw-4-series', r'440i( xDrive)?$', 2017, 2020, 6, '3.0', 322, 332); r('B58', 'bmw-4-series', r'M440i( xDrive)?$', 2021, 2026, 6, '3.0', 382, 369)
r('B58', 'bmw-2-series', r'M240i( xDrive)?( Coupe)?( M Performance)?$', 2017, 2021, 6, '3.0', 335, None); r('B58', 'bmw-2-series', r'M240i( xDrive)?$', 2022, 2026, 6, '3.0', 382, 369)
r('B58', 'bmw-5-series', r'540i( xDrive)?$', 2017, 2023, 6, '3.0', 335, 332); r('B58', 'bmw-5-series', r'540i xDrive$', 2024, 2026, 6, '3.0', 375, 398)
r('B58', 'bmw-7-series', r'740i( xDrive)?$', 2016, 2019, 6, '3.0', 322, 332); r('B58', 'bmw-7-series', r'740i( xDrive)?$', 2020, 2022, 6, '3.0', 335, 332)
r('B58', 'bmw-7-series', r'740i( xDrive)?$', 2023, 2026, 6, '3.0', 375, 398); r('B58', 'bmw-7-series', r'745e xDrive$', 2020, 2022, 6, '3.0')
r('B58', 'bmw-x3', r'X3 M40i$', 2018, 2019, 6, '3.0', 355, 369); r('B58', 'bmw-x3', r'X3 M40i$', 2020, 2024, 6, '3.0', 382, 369)
r('B58', 'bmw-x4', r'X4 M40i$', 2019, 2019, 6, '3.0'); r('B58', 'bmw-x4', r'X4 M40i$', 2020, 2025, 6, '3.0', 382, 369)
r('B58', 'bmw-x5', r'X5 [xs]Drive40i$', 2019, 2023, 6, '3.0', 335, 332); r('B58', 'bmw-x5', r'X5 [xs]Drive40i$', 2024, 2026, 6, '3.0', 375, 398)
r('B58', 'bmw-x5', r'X5 xDrive45e$', 2021, 2023, 6, '3.0'); r('B58', 'bmw-x5', r'X5 xDrive50e$', 2025, 2026, 6, '3.0')
r('B58', 'bmw-x6', r'X6 [xs]Drive40i$', 2020, 2023, 6, '3.0', 335, 332); r('B58', 'bmw-x6', r'X6 xDrive40i$', 2024, 2026, 6, '3.0', 375, 398)
r('B58', 'bmw-x7', r'X7 xDrive40i$', 2019, 2022, 6, '3.0', 335, 332); r('B58', 'bmw-x7', r'X7 xDrive40i$', 2023, 2026, 6, '3.0', 375, 398)
r('B58', 'bmw-z4', r'Z4 M40i$', 2020, 2026, 6, '3.0', 382, 369)
# N62
r('N62', 'bmw-5-series', r'545i$', 2004, 2005, 8, '4.4', 329, 332); r('N62', 'bmw-5-series', r'550i$', 2006, 2010, 8, '4.8', 362, 361)
r('N62', 'bmw-7-series', r'745L?i$', 2002, 2005, 8, '4.4', 329, 332); r('N62', 'bmw-7-series', r'750L?i$', 2006, 2008, 8, '4.8', 362, 361)
r('N62', 'bmw-x5', r'X5$', 2004, 2006, 8, '4.4', 315, 325); r('N62', 'bmw-x5', r'X5 4\.8is$', 2004, 2006, 8, '4.8', 355, 369)
r('N62', 'bmw-x5', r'X5 (4\.8i|xDrive48i)$', 2007, 2010, 8, '4.8', 350, 350)
# N63
r('N63', 'bmw-x6', r'X6 xDrive50i$', 2008, 2014, 8, '4.4', 402, 443); r('N63', 'bmw-x6', r'X6 xDrive50i$', 2015, 2019, 8, '4.4', 444, 479)
r('N63', 'bmw-x6', r'ActiveHybrid X6', 2010, 2011, 8, '4.4'); r('N63', 'bmw-x6', r'X6 M50i$', 2020, 2023, 8, '4.4', 523, 553)
r('N63', 'bmw-7-series', r'750L?i( xDrive)?$', 2009, 2012, 8, '4.4', 402, 443); r('N63', 'bmw-7-series', r'750L?i( xDrive)?$', 2013, 2015, 8, '4.4', 444, 479)
r('N63', 'bmw-7-series', r'750i( xDrive)?$', 2016, 2019, 8, '4.4'); r('N63', 'bmw-7-series', r'750i( xDrive)?$', 2020, 2022, 8, '4.4', 523, 553)
r('N63', 'bmw-7-series', r'ActiveHybrid 7(i|Li|L)?$', 2011, 2012, 8, '4.4')
r('N63', 'bmw-5-series', r'550i( xDrive)?$', 2011, 2013, 8, '4.4', 402, 443); r('N63', 'bmw-5-series', r'550i( xDrive)?$', 2014, 2017, 8, '4.4', 444, 479)
r('N63', 'bmw-5-series', r'550( GT|i xDrive GT)$', 2010, 2010, 8, '4.4', 402, 443)
r('N63', 'bmw-5-series', r'M550i xDrive$', 2018, 2020, 8, '4.4'); r('N63', 'bmw-5-series', r'M550i xDrive$', 2021, 2023, 8, '4.4', 523, 553)
r('N63', 'bmw-x5', r'X5 xDrive50i$', 2011, 2013, 8, '4.4', 402, 443); r('N63', 'bmw-x5', r'X5 xDrive50i$', 2014, 2018, 8, '4.4', 444, 479)
r('N63', 'bmw-x5', r'X5 xDrive50i$', 2019, 2020, 8, '4.4', 456, 479); r('N63', 'bmw-x5', r'X5 M50i$', 2020, 2023, 8, '4.4', 523, 553)
r('N63', 'bmw-x7', r'X7 xDrive50i$', 2019, 2020, 8, '4.4', 456, 479); r('N63', 'bmw-x7', r'X7 M50i$', 2020, 2022, 8, '4.4', 523, 553)
# S55 (in the N55 article)
r('S55', 'bmw-m3', r'M3$', 2015, 2018, 6, '3.0', 425, None); r('S55', 'bmw-m3', r'M3 CS$', 2018, 2018, 6, '3.0', 453, None)
r('S55', 'bmw-4-series', r'M4$', 2015, 2020, 6, '3.0', 425, None); r('S55', 'bmw-4-series', r'M4 (Coupe |Convertible )?Competition$', 2019, 2020, 6, '3.0', 444, None)
r('S55', 'bmw-4-series', r'M4 CS$', 2019, 2020, 6, '3.0', 453, None); r('S55', 'bmw-4-series', r'M4 GTS$', 2016, 2016, 6, '3.0', 493, 443)
r('S55', 'bmw-4-series', r'M4 DTM', 2018, 2018, 6, '3.0', 493, 443)
r('S55', 'bmw-2-series', r'M2 Competition$', 2019, 2021, 6, '3.0', 405, 406); r('S55', 'bmw-2-series', r'M2 CS$', 2020, 2020, 6, '3.0', 444, None)
# S58
r('S58', 'bmw-m3', r'M3$', 2021, 2026, 6, '3.0', 473, 406); r('S58', 'bmw-m3', r'M3 Competition( M xDrive)?$', 2021, 2024, 6, '3.0', 503, 479)
r('S58', 'bmw-4-series', r'M4$', 2021, 2026, 6, '3.0', 473, 406); r('S58', 'bmw-4-series', r'M4 Competition( M xDrive)?$', 2021, 2024, 6, '3.0', 503, 479)
r('S58', 'bmw-x3', r'X3 M$', 2020, 2021, 6, '3.0', 473, 442); r('S58', 'bmw-x3', r'X3 M$', 2022, 2024, 6, '3.0', 473, 457)
r('S58', 'bmw-x3', r'X3 M Competition$', 2020, 2021, 6, '3.0', 503, 442); r('S58', 'bmw-x3', r'X3 M Competition$', 2022, 2024, 6, '3.0', 503, 479)
r('S58', 'bmw-x4', r'X4 M$', 2020, 2021, 6, '3.0', 473, 442); r('S58', 'bmw-x4', r'X4 M$', 2022, 2024, 6, '3.0', 473, 457)
r('S58', 'bmw-x4', r'X4 M Competition$', 2020, 2021, 6, '3.0', 503, 442); r('S58', 'bmw-x4', r'X4 M Competition$', 2022, 2024, 6, '3.0', 503, 479)
r('S58', 'bmw-2-series', r'M2$', 2023, 2024, 6, '3.0', 453, 406)
# S63
r('S63', 'bmw-x5', r'X5 (xDriveM|M)$', 2010, 2013, 8, '4.4', 547, 502); r('S63', 'bmw-x5', r'X5 M$', 2015, 2019, 8, '4.4', 567, 553)
r('S63', 'bmw-x5', r'X5 M$', 2020, 2023, 8, '4.4', 591, 553); r('S63', 'bmw-x5', r'X5 M Competition$', 2020, 2023, 8, '4.4', 617, 553)
r('S63', 'bmw-x6', r'X6 (xDriveM|M)$', 2010, 2014, 8, '4.4', 547, 502); r('S63', 'bmw-x6', r'X6 M$', 2015, 2019, 8, '4.4', 567, 553)
r('S63', 'bmw-x6', r'X6 M$', 2020, 2023, 8, '4.4', 591, 553); r('S63', 'bmw-x6', r'X6 M Competition$', 2020, 2023, 8, '4.4', 617, 553)
r('S63', 'bmw-m5', r'M5$', 2013, 2016, 8, '4.4', 553, 502); r('S63', 'bmw-m5', r'M5$', 2018, 2023, 8, '4.4', 591, 553)
r('S63', 'bmw-m5', r'M5 Competition$', 2019, 2023, 8, '4.4', 617, 553)

def rule_for(fam, model, y, cyl, displ):
    hits = [x for x in R if x['fam'] == fam and x['a'] <= y <= x['b'] and re.match(x['rx'] + ('' if x['rx'].endswith('$') else ''), model, re.I)
            and (x['cyl'] is None or str(x['cyl']) == cyl) and (x['displ'] is None or x['displ'] == displ)]
    return hits[0] if len({h['code'] for h in hits}) == 1 and hits else None

# ---- EPA versions
z = zipfile.ZipFile(EPA_ZIP)
rows = [x for x in csv.DictReader(io.TextIOWrapper(z.open('vehicles.csv'), encoding='utf-8')) if x['make'] == 'BMW' and 2000 <= int(x['year']) <= YMAX]
CLEAN = re.compile(r'\s*\((?:\d+\s*inch|\d+\s*Amp|94Ah)[^)]*\)', re.I)
BODY = re.compile(r'\s+(Coupe|Convertible|Sports? Wagon|Gran Turismo|Gran Coupe|Touring|Wagon|Sedan|Roadster|Cabriolet|Sports Activity (Vehicle|Coupe)|SAV)', re.I)
def label(m, y=None):   # body styles share the engine: 335i Convertible = 335i (except the 2010 535i GT: N55, while the 2010 535i sedan was N54)
    if y == 2010 and re.match(r'535i Gran Turismo', m): return '535i GT'
    return re.sub(r'\s+', ' ', BODY.sub('', CLEAN.sub('', m))).strip()
EPA_FIX = {(2025, 'M340i Sedan'): dict(cylinders='6'), (2025, 'M340i xDrive Sedan'): dict(cylinders='6')}   # EPA lists the 2025 M340i (3.0 L B58) as 4 cylinders
def trans(t):
    t = t.replace('Automatic', 'auto').replace('Manual', 'manual')
    m = re.search(r'(\d+)', t); n = m.group(1) if m else ''
    if t.startswith('manual'): return f'{n}-speed manual' if n else 'manual'
    if '(AV' in t or 'variable' in t.lower(): return 'CVT'
    if '(A1)' in t: return '1-speed'
    if 'AM' in t: return f'{n}-speed dual-clutch' if n else 'dual-clutch'
    return f'{n}-speed auto' if n else 'auto'
DRV = {'Rear-Wheel Drive': 'RWD', 'All-Wheel Drive': 'AWD', '4-Wheel or All-Wheel Drive': 'AWD', 'Front-Wheel Drive': 'FWD', '4-Wheel Drive': 'AWD'}
V = collections.defaultdict(lambda: collections.defaultdict(dict))
for x in rows:
    fam = epa_family(x['baseModel'], x['model'])
    if not fam: continue
    y = int(x['year']); x.update(EPA_FIX.get((y, x['model']), {})); lab = label(x['model'], y)
    ev = x['atvType'] == 'EV'; phev = x['atvType'] == 'Plug-in Hybrid'
    key = (lab, x['displ'], x['cylinders'], x['drive'])
    rr = None if ev else rule_for(fam, lab, y, x['cylinders'], x['displ'])
    v = V[fam][y].get(key)
    mpg = (int(x['city08'] or 0), int(x['highway08'] or 0), int(x['comb08'] or 0))
    if v:   # several EPA rows for one version (transmissions, tunes): keep the MPG range and every transmission
        v['tr'] = sorted(set(v['tr']) | {trans(x['trany'])}); v['mpg'] = [min(v['mpg'][0], mpg[0]), max(v['mpg'][1], mpg[1]), min(v['mpg'][2], mpg[2]), max(v['mpg'][3], mpg[2])]
        continue
    V[fam][y][key] = dict(model=lab, displ=None if ev else (x['displ'] or None), cyl=None if ev else (x['cylinders'] or None),
                          turbo='turbo' if x['tCharger'] else ('supercharged' if x['sCharger'] else ('' if ev else 'non-turbo')),
                          fuel=x['fuelType1'], kind='EV' if ev else ('plug-in hybrid' if phev else (('mild hybrid' if y >= 2019 and not x['model'].startswith('ActiveHybrid') else 'hybrid') if x['atvType'] == 'Hybrid' else ('diesel' if x['atvType'] == 'Diesel' else ''))),
                          ev_motor=x['evMotor'] if (ev or phev) else '', tr=[trans(x['trany'])], drive=DRV.get(x['drive'], x['drive']),
                          mpg=[mpg[0], mpg[1], mpg[2], mpg[2]], ev_range=int(x['range'] or 0) if ev else 0,
                          code=rr['code'] if rr else None, hp=rr['hp'] if rr else None, tq=rr['tq'] if rr else None, vk=vkey(lab))
versions = {f: {str(y): sorted(d.values(), key=lambda v: (v['code'] or 'ZZ', v['model'])) for y, d in sorted(V[f].items())} for f in V}
nver = sum(len(v) for f in versions.values() for v in f.values()); nmap = sum(1 for f in versions.values() for v in f.values() for x in v if x['code'])
nev = sum(1 for f in versions.values() for v in f.values() for x in v if x['kind'] == 'EV')
my_total = sum(len(f) for f in versions.values())
my_cov = sum(1 for f in versions.values() for y, v in f.items() if all(x['code'] or x['kind'] == 'EV' for x in v))
print(f'EPA versions {nver}, mapped {nmap}, EV {nev}; model-years {my_total}, fully coded {my_cov}', flush=True)

# ---- complaints
con = sqlite3.connect(DB)
fam_years = {f: set(int(y) for y in versions[f]) for f in versions}
C = collections.defaultdict(lambda: collections.defaultdict(lambda: dict(ids=set(), parts=collections.Counter(), crash=0, fire=0, inj=0, dead=0, miles=[], q=[])))
VC = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(set)))   # fam -> y -> vkey -> ids
STR = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
TXT = collections.defaultdict(lambda: collections.defaultdict(set))   # code -> y -> ids naming the code
CODE_RX = re.compile(r'\b(M54|N52|N54|N55|N20|N26|B46|B48|B58|N62|N63|S55|S58|S63|S54)\b')
PART = {'ELECTRICAL SYSTEM': 'electrical', 'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'SERVICE BRAKES, HYDRAULIC': 'brakes', 'VEHICLE SPEED CONTROL': 'speed control',
        'FUEL/PROPULSION SYSTEM': 'fuel system', 'FUEL SYSTEM, GASOLINE': 'fuel system', 'FUEL SYSTEM, OTHER': 'fuel system', 'ENGINE AND ENGINE COOLING': 'engine', 'ENGINE': 'engine', 'STEERING': 'steering',
        'SUSPENSION': 'suspension', 'AIR BAGS': 'air bags', 'STRUCTURE': 'body & structure', 'VISIBILITY': 'visibility', 'EXTERIOR LIGHTING': 'lights', 'WHEELS': 'wheels', 'TIRES': 'tires',
        'SEAT BELTS': 'seat belts', 'SEATS': 'seats', 'UNKNOWN OR OTHER': 'other', 'LATCHES/LOCKS/LINKAGES': 'locks & latches', 'BACK OVER PREVENTION': 'backup camera',
        'FORWARD COLLISION AVOIDANCE': 'collision warning', 'LANE DEPARTURE': 'lane assist', 'ELECTRONIC STABILITY CONTROL (ESC)': 'stability control', 'HYBRID PROPULSION SYSTEM': 'hybrid system',
        'POWER TRAIN:AUTOMATIC TRANSMISSION': 'transmission & drivetrain'}
def part(c):
    c = (c or '').split(':')[0].strip()
    return PART.get(c, c.lower() or 'other')
for odi, model, y, comp, crash, fire, inj, dead, miles, descr in con.execute("select odino, model, year, comp, crash, fire, injured, deaths, miles, descr from rows where make='BMW' and year between 2000 and ?", (YMAX,)):
    s = re.sub(r'\s+', ' ', (model or '').upper().strip())
    fam = nh_family(s)
    if not fam or y not in fam_years.get(fam, ()): continue
    # a code named in the text counts only if this complaint's own model and year could have that engine (owners often name
    # other cars' engines, and bulletins quoted in complaints list several codes: "B58/N20/N55/S55" on a 320i)
    own = {v['code'] for v in versions[fam][str(y)] if v['code']}
    for code in {c.replace('B46', 'B48') for c in CODE_RX.findall((descr or '').upper())} & own: TXT[code][y].add(odi)
    d = C[fam][y]
    d['parts'][part(comp)] += 1
    if odi in d['ids']: continue
    d['ids'].add(odi); STR[fam][y][s] += 1
    d['crash'] += crash == 'Y'; d['fire'] += fire == 'Y'; d['inj'] += bool(inj); d['dead'] += bool(dead)
    if miles and 0 < int(miles) < 500000: d['miles'].append(int(miles))
    vk = vkey(s, epa=False) if re.match(r'^M?\d{3}', s.replace(' ', '')) else None
    if vk and not s.endswith(' US'): VC[fam][y][vk].add(odi)
    t = (descr or '').strip()
    if 70 < len(t) < 240 and len(d['q']) < 200: d['q'].append((odi, t))

# per family-year: complaints, engines, attribution
YEARS_JSON = {f['id']: {v['y']: v for v in f['years']} for f in json.load(open(os.path.join(HERE, 'data', 'years.json'), encoding='utf-8')) if f['id'] in HAS_INDEX}
fy = {}
for f in versions:
    for ys, vl in versions[f].items():
        y = int(ys); codes = {v['code'] for v in vl if v['kind'] != 'EV'}
        allmapped = all(v['code'] for v in vl if v['kind'] != 'EV') and vl
        li = YEARS_JSON.get(f, {}).get(y)
        fy[(f, y)] = dict(n=len(C[f][y]['ids']), codes=sorted(c for c in codes if c), single=(len(codes) == 1 and allmapped and None not in codes),
                          li=(li['li'] if li and (li.get('ok') is not False) and li.get('li') else None), li_n=li['n'] if li else None)
# version-level complaint counts (a): for an NHTSA version name (number, kind) in year y, the EPA versions sharing it must all map to one engine
VA = collections.defaultdict(dict)   # (f,y) -> {vk: {n, code or None}}
for f in VC:
    for y in VC[f]:
        for vk, ids in VC[f][y].items():
            cands = [v for v in versions.get(f, {}).get(str(y), []) if v['vk'] and v['vk'][0] == vk[0] and (v['vk'][1] == vk[1] or (vk[1] == 'i' and v['vk'][1] in ('i', 'ci')) or (vk[1] == 'ci' and v['vk'][1] in ('i', 'ci')))]
            codes = {v['code'] for v in cands}
            VA[(f, y)]['%s|%s' % vk] = dict(n=len(ids), code=(codes.pop() if len(codes) == 1 and None not in codes else None), versions=sorted({v['model'] for v in cands}))

# ---- engine x year table
EY = collections.defaultdict(dict)
for f in versions:
    for ys, vl in versions[f].items():
        y = int(ys)
        for v in vl:
            if not v['code']: continue
            e = EY[v['code']].setdefault(y, dict(models=collections.defaultdict(set), a=0, a_from=[], b=[], combined=[], c=0, parts=collections.Counter()))
            e['models'][f].add(v['model'])
for code, yrs in EY.items():
    for y, e in yrs.items():
        for f in e['models']:
            info = fy[(f, y)]
            if info['single'] and info['codes'] == [code]:
                e['b'].append(dict(fam=f, li=info['li'], n=info['n']))
                e['parts'].update(C[f][y]['parts'])
            else:
                got = [(k, a) for k, a in VA.get((f, y), {}).items() if a['code'] == code]
                if got:
                    for k, a in got:
                        e['a'] += a['n']; e['a_from'].append(dict(fam=f, name=k.split('|')[0] + {'i': 'i', 'ci': 'ci', 'is': 'is', 'd': 'd', 'e': 'e'}[k.split('|')[1]], n=a['n']))
                else: e['combined'].append(dict(fam=f, li=info['li'], n=info['n'], codes=info['codes']))
        e['c'] = len(TXT[code].get(y, ()))
        # parts for (a): use the version's own complaints
        for f in e['models']:
            for k, a in VA.get((f, y), {}).items():
                if a['code'] == code:
                    num, kind = k.split('|')
                    ids = VC[f][y][(num, kind)]
                    for odi, comp in con.execute(f"select odino, comp from rows where odino in ({','.join('?' * len(ids))})", tuple(ids)) if ids else []:
                        e['parts'][part(comp)] += 1
        e['models'] = {f: sorted(ms) for f, ms in e['models'].items()}
        e['parts'] = [[p, k] for p, k in e['parts'].most_common(4)]
cnt = collections.Counter()
for code, yrs in EY.items():
    for y, e in yrs.items():
        has_b = any(b['li'] for b in e['b']); cnt['engine_years'] += 1
        if has_b: cnt['per_car(b)'] += 1
        elif e['a'] or e['b']: cnt['counts_only(a/b-no-sales)'] += 1
        elif e['combined']: cnt['combined_only'] += 1
        else: cnt['none'] += 1
print('engine-years:', dict(cnt), flush=True)

# ---- new-model page data (complaints, problems, recalls) for families without a Lemon Index page
RCACHE_P = os.path.join(HERE, 'data', 'cache', 'bmw_recalls_cache.json')
RCACHE = json.load(open(RCACHE_P, encoding='utf-8')) if os.path.exists(RCACHE_P) else {}
def api(u):
    if u in RCACHE: return RCACHE[u]
    for k in range(2):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'LemonIndex/1.0 (lemonindex.com)'}), timeout=15))
            RCACHE[u] = {'results': [{kk: r.get(kk) for kk in ('NHTSACampaignNumber', 'ReportReceivedDate', 'Component', 'Summary')} for r in d.get('results') or []]}
            if len(RCACHE) % 25 == 0: json.dump(RCACHE, open(RCACHE_P, 'w', encoding='utf-8'))
            return RCACHE[u]
        except Exception: time.sleep(2)
    return {}
NEWF = {}
for f in FAM:
    if f in HAS_INDEX or f not in versions: continue
    ys = sorted(int(y) for y in versions[f]); tot_parts = collections.Counter(); n = 0; crash = fire = inj = dead = 0; miles = []; quotes = []
    for y in ys:
        d = C[f][y]; tot_parts.update(d['parts']); n += len(d['ids']); crash += d['crash']; fire += d['fire']; inj += d['inj']; dead += d['dead']; miles += d['miles']
        quotes += [(y, o, t) for o, t in d['q']]
    rec = {}
    for y in ys:
        names = {s for s, k in sorted(STR[f][y].items(), key=lambda kv: -kv[1])[:3] if k >= 3 and not re.search(r'SERIES|SAV|SAC| US$', s)}
        names.add(FAM[f].split(' ', 1)[1].replace(' Series', '').lower())
        for md in sorted(names):
            if not md or md.isdigit(): continue
            for x in (api(f'https://api.nhtsa.gov/recalls/recallsByVehicle?make=bmw&model={urllib.parse.quote(md.lower())}&modelYear={y}').get('results') or []):
                cn = x.get('NHTSACampaignNumber')
                if cn: rec.setdefault(cn, dict(id=cn, date=x.get('ReportReceivedDate', ''), part=x.get('Component', ''), summary=(x.get('Summary') or '').strip()[:600], years=set()))['years'].add(y)
            time.sleep(.15)
    tot = sum(tot_parts.values()) or 1; ms = sorted(miles)
    qs = sorted(quotes, key=lambda q: q[1])[-3:]
    NEWF[f] = dict(id=f, name=FAM[f], a=ys[0], b=ys[-1], n=n, by_year={str(y): len(C[f][y]['ids']) for y in ys},
                   parts=[[p, round(c / tot * 100)] for p, c in tot_parts.most_common(6)], crash=crash, fire=fire, injured=inj, deaths=dead,
                   miles=dict(n=len(ms), p25=ms[len(ms) // 4], median=ms[len(ms) // 2], p75=ms[3 * len(ms) // 4]) if len(ms) >= 20 else None,
                   recalls=[dict(r, years=sorted(r['years'])) for r in sorted(rec.values(), key=lambda r: r['date'][6:10] + r['date'][3:5] + r['date'][:2], reverse=True)],
                   quotes=[dict(y=y, odi=o, text=t[0] + t[1:].lower() if t.isupper() else t) for y, o, t in qs],
                   yparts={str(y): [[p, k] for p, k in C[f][y]['parts'].most_common(3)] for y in ys})
    print(f, 'complaints', n, 'recalls', len(rec), flush=True)
    json.dump(RCACHE, open(RCACHE_P, 'w', encoding='utf-8'))

json.dump(dict(families=FAM, has_index=sorted(HAS_INDEX), versions=versions, engines=ENG,
               rules=[{k: v for k, v in x.items()} for x in R],
               engine_years={c: {str(y): e for y, e in sorted(yrs.items())} for c, yrs in EY.items()},
               fam_years={f'{f}|{y}': v for (f, y), v in fy.items()},
               version_complaints={f'{f}|{y}': v for (f, y), v in VA.items()},
               text_mentions={c: {str(y): len(ids) for y, ids in sorted(v.items())} for c, v in TXT.items()},
               new_models=NEWF,
               sources=dict(epa='https://www.fueleconomy.gov/feg/download.shtml', nhtsa='https://www.nhtsa.gov/nhtsa-datasets-and-apis'),
               built=time.strftime('%Y-%m-%d'),
               coverage=dict(versions=nver, mapped=nmap, ev=nev, model_years=my_total, fully_coded=my_cov, engine_years=dict(cnt))),
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), default=list)
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
