# Supercar engines (11-11, Elijah: "a supercar engines section like the BMW engines build"). -> data/supercar_engines.json
# Every engine family is matched to the cars in the supercars section (data/supercars.json) from EPA's version list (fueleconomy.gov
# vehicles.csv: model name, displacement, cylinders, turbo/supercharger, hybrid), and every code, car and year was checked against the
# sources stored with it (mostly the English Wikipedia engine articles, plus Porsche and Honda newsroom pages). A version whose engine no
# source confirms (e.g. the 2025 Bentley V8 plug-in hybrids, the 2025 Urus SE) stays "not confirmed" and isn't counted for any engine.
# Owner complaints (NHTSA complaints.db): counted for an engine only where the complaint's own model name and year leave no doubt
# (e.g. "488 GTB", "GT-R", "CORVETTE Z06"), or, for the Corvette, where the owner's own text names the Z06 / ZR1 / E-Ray in a year where
# that name had one engine. Supercars draw very few complaints, so most engines get "Not enough complaints to chart" - never an estimate.
# Recalls: NHTSA campaigns already pulled per model and year (data/supercars.json); counted for an engine when every confirmed version of
# that model-year had this engine, or the recall text names it. Repair notes: the automakers' notes to dealers (NHTSA manufacturer
# communications, data/raw_more/MFR_COMMS_RECEIVED_*.zip), same matching, engine-related ones only.
import csv, glob, io, json, os, re, sqlite3, sys, zipfile, collections
sys.stdout.reconfigure(encoding='utf-8'); csv.field_size_limit(10 ** 8)
HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = r'C:\Users\elift\Code\lemonindex-site'   # data/cache and data/raw_more are not in git; read them from the main checkout
CACHE = os.path.join(HERE, 'data', 'cache') if os.path.exists(os.path.join(HERE, 'data', 'cache', 'vehicles.csv')) else os.path.join(MAIN, 'data', 'cache')
RAW = os.path.join(HERE, 'data', 'raw_more') if os.path.exists(os.path.join(HERE, 'data', 'raw_more')) else os.path.join(MAIN, 'data', 'raw_more')
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index\data\complaints.db'
WP = 'https://en.wikipedia.org/wiki/'
S = lambda *a: [dict(title=t, url=(u if u.startswith('http') else WP + u)) for t, u in a]
# ---- engine families: what the sources say (factory power figures as the sources give them)
M = {
 'ferrari-f136': dict(make='Ferrari', code='F136', name='Ferrari F136', codes='F136 FB (458), F136 FL (458 Speciale), F136 IB / IH (California)', layout='90° V8', size='4.5 L and 4.3 L', asp='naturally aspirated',
     made='built by Ferrari, developed with Maserati', hp=[454, 597], src=S(('Ferrari F136 engine', 'Ferrari_F136_engine'))),
 'ferrari-f154': dict(make='Ferrari', code='F154', name='Ferrari F154', codes='F154 BB, BD, BE, BH, CB, CD, CG, FA, FB', layout='90° V8', size='3.9 L (SF90 4.0 L)', asp='twin-turbo',
     made='built by Ferrari', hp=[550, 786], hp_note='engine only; the SF90 makes 990 hp with its motors', src=S(('Ferrari F154 engine', 'Ferrari_F154_engine'))),
 'ferrari-f140': dict(make='Ferrari', code='F140', name='Ferrari F140', codes='F140 EB (FF), FC (F12), FG (F12tdf), ED (GTC4Lusso), GA (812), HB (812 Competizione)', layout='V12', size='6.3 L and 6.5 L', asp='naturally aspirated',
     hp=[651, 819], src=S(('Ferrari F140 engine', 'Ferrari_F140_engine'))),
 'ferrari-f163': dict(make='Ferrari', code='F163', name='Ferrari F163', codes='F163 BC', layout='120° V6', size='3.0 L', asp='twin-turbo plug-in hybrid', hp=[654, 654], hp_note='engine only; 819 hp with the motor',
     src=S(('Ferrari F163 engine', 'Ferrari_F163_engine'))),
 'lamborghini-v10': dict(make='Lamborghini', code='V10', name='Lamborghini / Audi 5.2 V10', codes='no single code; first Audi R8 V10: BUJ', layout='90° V10', size='5.2 L', asp='naturally aspirated',
     made='block cast at Audi Hungaria (Győr), assembled at Sant&#39;Agata', hp=[518, 631], src=S(('Lamborghini V10', 'Lamborghini_V10'), ('List of Volkswagen Group petrol engines', 'List_of_Volkswagen_Group_petrol_engines'))),
 'lamborghini-l539': dict(make='Lamborghini', code='L539', name='Lamborghini L539 V12', codes='L539', layout='V12', size='6.5 L', asp='naturally aspirated', hp=[690, 770],
     src=S(('Lamborghini Aventador', 'Lamborghini_Aventador'), ('Lamborghini V12', 'Lamborghini_V12'))),
 'lamborghini-l545': dict(make='Lamborghini', code='L545', name='Lamborghini L545 V12', codes='L545', layout='V12', size='6.5 L', asp='naturally aspirated plug-in hybrid', hp=[814, 814], hp_note='engine only; 1,001 hp with the motors',
     src=S(('Lamborghini Revuelto', 'Lamborghini_Revuelto'))),
 'vw-ea825': dict(make='Volkswagen Group', code='EA825', name='VW Group 4.0 TFSI V8 (EA825)', codes='EA825 (Bentley 2019+: CVDA)', layout='V8', size='4.0 L', asp='twin-turbo', hp=[542, 657],
     src=S(('List of Volkswagen Group petrol engines', 'List_of_Volkswagen_Group_petrol_engines'), ('Bentley Bentayga', 'Bentley_Bentayga'), ('Lamborghini Urus', 'Lamborghini_Urus')),
     caveat='Wikipedia&#39;s Continental GT article files the 2019+ Bentley V8 as EA824; the VW engine list and the Bentayga article file it as EA825.'),
 'audi-ea824': dict(make='Volkswagen Group', code='EA824', name='Audi 4.0 TFSI V8 (EA824)', codes='EA824 (Continental GT V8: CMMC / CYCB; V8 S: CMMD / CYCA)', layout='V8', size='4.0 L', asp='twin-turbo', hp=[500, 572],
     src=S(('Bentley Continental GT', 'Bentley_Continental_GT'), ('List of Volkswagen Group petrol engines', 'List_of_Volkswagen_Group_petrol_engines'))),
 'vw-ea839': dict(make='Volkswagen Group', code='EA839', name='VW Group 3.0 V6 (EA839)', codes='EA839', layout='V6', size='3.0 L', asp='turbo plug-in hybrid', hp=[443, 443], hp_note='with the motor',
     src=S(('Bentley Bentayga', 'Bentley_Bentayga'), ('List of Volkswagen Group petrol engines', 'List_of_Volkswagen_Group_petrol_engines'))),
 'vw-w12': dict(make='Bentley', code='W12', name='Bentley 6.0 W12', codes='EA398 family (BWR / BEB, Speed: CKHC / BWRA)', layout='W12', size='6.0 L', asp='twin-turbo', made='hand-built by Bentley in Crewe; production ended in 2024',
     hp=[552, 700], src=S(('Volkswagen Group W12 engine', 'Volkswagen_Group_W12_engine'), ('Bentley Continental GT', 'Bentley_Continental_GT'),
     ('End of an era as final Bentley W12 engine hand-built in Crewe (The Manufacturer)', 'https://www.themanufacturer.com/articles/end-of-an-era-as-final-bentley-w12-engine-hand-built-in-crewe/'))),
 'mclaren-m838t': dict(make='McLaren', code='M838T', name='McLaren M838T', codes='M838T (12C, 650S, 675LT), M838TE (540C, 570S, 600LT, 620R)', layout='90° flat-plane V8', size='3.8 L', asp='twin-turbo',
     made='assembled by Ricardo in Shoreham-by-Sea, UK', hp=[533, 666], src=S(('McLaren M838T engine', 'McLaren_M838T_engine'), ('McLaren 570S', 'McLaren_570S'))),
 'mclaren-m840t': dict(make='McLaren', code='M840T', name='McLaren M840T', codes='M840T (720S, 765LT), M840TE (GT)', layout='90° flat-plane V8', size='4.0 L', asp='twin-turbo',
     made='assembled by Ricardo in Shoreham-by-Sea, UK', hp=[612, 755], src=S(('McLaren M840T engine', 'McLaren_M840T_engine'), ('McLaren GT', 'McLaren_GT'))),
 'mclaren-m630': dict(make='McLaren', code='M630', name='McLaren M630', codes='M630', layout='120° V6', size='3.0 L', asp='twin-turbo plug-in hybrid', hp=[577, 577], hp_note='engine only; 671 hp with the motor',
     src=S(('McLaren M630 engine', 'McLaren_M630_engine'))),
 'aston-am-v8': dict(make='Aston Martin', code='AM14', name='Aston Martin 4.7 V8', codes='AM14 (also called AJ37; Jaguar AJ-V8 based)', layout='V8', size='4.7 L', asp='naturally aspirated',
     made='hand-assembled at Aston Martin&#39;s Cologne plant', hp=[420, 430], src=S(('Aston Martin V8 engine', 'Aston_Martin_V8_engine'), ('Aston Martin Vantage (2005)', 'Aston_Martin_Vantage_(2005)'))),
 'aston-am-v12': dict(make='Aston Martin', code='AM V12', name='Aston Martin 5.9 V12', codes='AM08 (DBS), AM11 (V12 Vantage), AM28 (V12 Vantage S)', layout='60° V12', size='5.9 L', asp='naturally aspirated',
     made='Aston Martin&#39;s engine plant in Cologne', hp=[510, 565], src=S(('Aston Martin V12 engine', 'Aston_Martin_V12_engine'), ('Aston Martin Vantage (2005)', 'Aston_Martin_Vantage_(2005)')),
     caveat='EPA lists the V12 Vantage S as 6.0 L; Aston Martin&#39;s figure is 5.9 L.'),
 'aston-ae31': dict(make='Aston Martin', code='AE31', name='Aston Martin AE31 V12', codes='AE31', layout='60° V12', size='5.2 L', asp='twin-turbo', hp=[600, 759],
     src=S(('Aston Martin DB11', 'Aston_Martin_DB11'), ('Aston Martin DBS Superleggera', 'Aston_Martin_DBS_Superleggera'), ('Aston Martin V12 engine', 'Aston_Martin_V12_engine'))),
 'amg-m177-m178': dict(make='Mercedes-AMG', code='M177/M178', name='Mercedes-AMG M177 / M178', codes='M178 (AMG GT 2-door), M177 (AMG GT 4-door and 2024+ coupe, every Aston Martin here)', layout='V8', size='4.0 L', asp='twin-turbo',
     made='hand-assembled at AMG in Affalterbach, one engine per builder', hp=[456, 720], src=S(('Mercedes-AMG M178 engine', 'Mercedes-Benz_M178_engine'), ('Mercedes-AMG GT', 'Mercedes-AMG_GT'), ('Aston Martin Vantage (2018)', 'Aston_Martin_Vantage_(2018)'), ('Aston Martin DBX', 'Aston_Martin_DBX'))),
 'amg-m159': dict(make='Mercedes-AMG', code='M159', name='Mercedes-AMG M159', codes='M159 (dry-sump M156)', layout='V8', size='6.2 L', asp='naturally aspirated', hp=[563, 622], src=S(('Mercedes-Benz M156 / M159 engine', 'Mercedes-Benz_M159_engine'))),
 'amg-m256': dict(make='Mercedes-Benz', code='M256', name='Mercedes M256', codes='M256 (GT 43, GT 53)', layout='inline-6', size='3.0 L', asp='turbo, 48-volt mild hybrid', hp=[362, 429], hp_note='engine only',
     src=S(('Mercedes-Benz M256 engine', 'Mercedes-Benz_M256_engine'), ('Mercedes-AMG GT 4-Door Coupé', 'Mercedes-AMG_GT_4-Door_Coup%C3%A9'))),
 'amg-m139': dict(make='Mercedes-AMG', code='M139', name='Mercedes-AMG M139', codes='M139', layout='inline-4', size='2.0 L', asp='turbo, mild hybrid', hp=[416, 416], made='hand-assembled, one engine per builder',
     src=S(('Mercedes-Benz M139 engine', 'Mercedes-Benz_M139_engine'), ('Mercedes-AMG GT', 'Mercedes-AMG_GT'))),
 'rr-n73': dict(make='BMW', code='N73', name='BMW N73 V12', codes='N73B68', layout='V12', size='6.75 L', asp='naturally aspirated', hp=[453, 453], src=S(('BMW N73', 'BMW_N73'), ('Rolls-Royce Phantom (2003)', 'Rolls-Royce_Phantom_(2003)'))),
 'rr-n74': dict(make='BMW', code='N74', name='BMW N74 V12', codes='N74B66 (Ghost to 2020), N74B68 (Phantom VIII, Cullinan, Ghost 2021+)', layout='60° V12', size='6.6 L and 6.75 L', asp='twin-turbo', hp=[563, 624],
     src=S(('BMW N74', 'BMW_N74'))),
 'bugatti-w16': dict(make='Bugatti', code='W16', name='Bugatti W16', codes='no public code', layout='W16', size='8.0 L', asp='quad-turbo', hp=[987, 1578], src=S(('Bugatti W16 engine', 'Bugatti_W16_engine'), ('Bugatti Chiron', 'Bugatti_Chiron'))),
 'audi-42-fsi': dict(make='Audi', code='4.2 FSI', name='Audi 4.2 FSI V8', codes='code not confirmed', layout='90° V8', size='4.2 L', asp='naturally aspirated', hp=[414, 414], src=S(('Audi R8 (Type 42)', 'Audi_R8_(Type_42)'))),
 'nissan-vr38dett': dict(make='Nissan', code='VR38DETT', name='Nissan VR38DETT', codes='VR38DETT', layout='60° V6', size='3.8 L', asp='twin-turbo', made='hand-built by Takumi craftsmen at Nissan&#39;s Yokohama plant',
     hp=[478, 592], src=S(('Nissan VR engine', 'Nissan_VR_engine'), ('Nissan GT-R', 'Nissan_GT-R'))),
 'acura-jnc1': dict(make='Acura', code='JNC1', name='Acura JNC1', codes='JNC1', layout='75° V6', size='3.5 L', asp='twin-turbo hybrid', made='hand-assembled at Honda&#39;s Anna, Ohio engine plant', hp=[573, 602], hp_note='with the motors',
     src=S(('Honda NSX (second generation)', 'Honda_NSX_(second_generation)'), ('First serial production 2017 Acura NSX rolls off the line (Honda)', 'https://global.honda/en/newsroom/news/2016/4160525eng.html'))),
 'gm-lt4': dict(make='Chevrolet', code='LT4', name='GM LT4', codes='LT4', layout='90° V8, pushrod', size='6.2 L', asp='supercharged', hp=[650, 650], src=S(('General Motors LS-based small-block engine', 'General_Motors_LS-based_small-block_engine'))),
 'gm-lt5': dict(make='Chevrolet', code='LT5', name='GM LT5', codes='LT5', layout='90° V8, pushrod', size='6.2 L', asp='supercharged', hp=[755, 755], src=S(('General Motors LS-based small-block engine', 'General_Motors_LS-based_small-block_engine'))),
 'gm-lt6': dict(make='Chevrolet', code='LT6', name='Chevrolet LT6', codes='LT6 (Gemini family)', layout='flat-plane V8, DOHC', size='5.5 L', asp='naturally aspirated', hp=[670, 670], src=S(('Chevrolet Gemini small-block engine', 'Chevrolet_Gemini_small-block_engine'))),
 'gm-lt7': dict(make='Chevrolet', code='LT7', name='Chevrolet LT7', codes='LT7 (Gemini family)', layout='V8, DOHC', size='5.5 L', asp='twin-turbo', hp=[1064, 1064], src=S(('Chevrolet Gemini small-block engine', 'Chevrolet_Gemini_small-block_engine'), ('Chevrolet Corvette (C8)', 'Chevrolet_Corvette_(C8)'))),
 'gm-lt2': dict(make='Chevrolet', code='LT2', name='GM LT2', codes='LT2', layout='90° V8, pushrod', size='6.2 L', asp='naturally aspirated hybrid', hp=[655, 655], hp_note='E-Ray, with the front motor',
     src=S(('Chevrolet Corvette (C8)', 'Chevrolet_Corvette_(C8)'))),
 'ford-ecoboost-35': dict(make='Ford', code='D35', name='Ford 3.5 EcoBoost (D35)', codes='D35 (second-generation 3.5 EcoBoost)', layout='V6', size='3.5 L', asp='twin-turbo', hp=[647, 660], src=S(('Ford EcoBoost engine', 'Ford_EcoBoost_engine'), ('Ford GT', 'Ford_GT'))),
 'toyota-2gr': dict(make='Toyota', code='2GR-FE', name='Toyota 2GR-FE', codes='2GR-FE', layout='60° V6', size='3.5 L', asp='naturally aspirated or supercharged', made='Toyota engine, Lotus engine management', hp=[276, 416],
     src=S(('Toyota GR engine', 'Toyota_GR_engine'), ('Lotus Evora', 'Lotus_Evora'), ('Lotus Emira', 'Lotus_Emira'))),
 'porsche-m97': dict(make='Porsche', code='M97', name='Porsche M97 (Mezger)', codes='M97.77 (GT3, GT3 RS 3.8), M97.74 (GT3 RS 4.0), M97.70 (GT2 RS)', layout='flat-6', size='3.6 to 4.0 L', asp='naturally aspirated (GT3) or twin-turbo (GT2 RS)', hp=[612, 612],
     hp_note='GT2 RS; the GT3 figures aren&#39;t in our sources', src=S(('Porsche 911 GT3', 'Porsche_911_GT3'), ('Porsche 911 GT2', 'Porsche_911_GT2'), ('Porsche 997', 'Porsche_997'))),
 'porsche-ma1-gt3': dict(make='Porsche', code='MA1 GT3', name='Porsche GT3 flat-6 (MA1)', codes='MA1.75 (991 GT3), MA1.76 (GT3 RS, 991.2 GT3); the 992 GT3 keeps the 991.2 engine', layout='flat-6', size='3.8 L and 4.0 L', asp='naturally aspirated',
     hp=[468, 513], hp_note='475 to 520 PS', src=S(('Porsche 911 GT3', 'Porsche_911_GT3'), ('Porsche 991', 'Porsche_991'), ('Porsche 911 (992)', 'Porsche_911_(992)'))),
 'porsche-turbo-38': dict(make='Porsche', code='3.8 Turbo', name='Porsche 3.8 twin-turbo flat-6', codes='997.2 and 991 Turbo (code not public); 991.2 GT2 RS: MDH.NA', layout='flat-6', size='3.8 L', asp='twin-turbo', hp=[493, 691],
     src=S(('Porsche 997', 'Porsche_997'), ('Porsche 991', 'Porsche_991'), ('Porsche 911 GT2', 'Porsche_911_GT2'))),
 'porsche-9a2': dict(make='Porsche', code='9A2 Evo', name='Porsche 9A2 Evo 3.7', codes='9A2 Evo (MDB.CB)', layout='flat-6', size='3.7 L', asp='twin-turbo', hp=[572, 641],
     src=S(('Porsche 911 (992)', 'Porsche_911_(992)'), ('Corazón y alma (Porsche Newsroom)', 'https://newsroom.porsche.com/es_ES/tecnologia/2020/es-porsche-motor-boxer-911-turbo-s-christophorus-394-20422.html'))),
 'porsche-918-v8': dict(make='Porsche', code='918 V8', name='Porsche 918 Spyder V8', codes='no public code (RS Spyder racing V8 architecture)', layout='V8', size='4.6 L', asp='naturally aspirated plug-in hybrid', hp=[599, 599], hp_note='engine only; 875 hp with the motors',
     src=S(('Porsche 918 Spyder', 'Porsche_918_Spyder'))),
}
NOTES = {   # known issues the sources state (no forum lore)
 'porsche-ma1-gt3': [('In 2014 Porsche replaced the engine in all 785 991 GT3s built so far after a supplier error in the connecting-rod bolts (two cars caught fire), and later gave a 10-year / 120,000-mile engine warranty over valvetrain wear.', WP + 'Porsche_911_GT3')],
 'vw-ea825': [('November 2020 recall: 2019-2020 Urus, fuel-line quick connectors could soften and leak (fire risk).', WP + 'Lamborghini_Urus')],
 'ford-ecoboost-35': [('About 200 2017-2018 Ford GTs were recalled for a possible hydraulic leak and fire risk.', WP + 'Ford_GT')],
}
# ---- EPA versions -> engine (only models the supercars section covers; same family regexes as data_supercars.py)
F = [('Ferrari 458 Italia', 'Ferrari', r'458.*'), ('Ferrari 488', 'Ferrari', r'488.*'), ('Ferrari F8 Tributo', 'Ferrari', r'F8.*'), ('Ferrari 296', 'Ferrari', r'296.*'), ('Ferrari SF90 Stradale', 'Ferrari', r'SF90.*'),
     ('Ferrari 812 Superfast', 'Ferrari', r'812.*'), ('Ferrari F12berlinetta', 'Ferrari', r'F12.*'), ('Ferrari California', 'Ferrari', r'California.*'), ('Ferrari Portofino', 'Ferrari', r'Portofino.*'),
     ('Ferrari Roma', 'Ferrari', r'Roma.*'), ('Ferrari GTC4Lusso / FF', 'Ferrari', r'(GTC4.*|FF.*)'), ('Lamborghini Huracán', 'Lamborghini', r'Hurac.*'), ('Lamborghini Aventador', 'Lamborghini', r'Aventador.*'),
     ('Lamborghini Gallardo', 'Lamborghini', r'Gallardo.*'), ('Lamborghini Urus', 'Lamborghini', r'Urus.*'), ('Lamborghini Revuelto', 'Lamborghini', r'Revuelto.*'),
     ('McLaren 570S / 540C', 'McLaren Automotive', r'(570.*|540.*|600LT.*)'), ('McLaren 720S / 750S', 'McLaren Automotive', r'(720.*|750.*|765.*)'), ('McLaren 650S / 12C', 'McLaren Automotive', r'(650.*|MP4.*|12C.*|675.*)'),
     ('McLaren GT', 'McLaren Automotive', r'GT.*'), ('McLaren Artura', 'McLaren Automotive', r'Artura.*'), ('Aston Martin Vantage', 'Aston Martin', r'(V8 |V12 )?Vantage.*'), ('Aston Martin DB11 / DB12', 'Aston Martin', r'DB1[12].*'),
     ('Aston Martin DBS', 'Aston Martin', r'DBS.*'), ('Aston Martin DBX', 'Aston Martin', r'DBX.*'), ('Bentley Continental GT', 'Bentley', r'Continental.*'), ('Bentley Bentayga', 'Bentley', r'Bentayga.*'),
     ('Rolls-Royce Ghost', 'Rolls-Royce', r'Ghost.*'), ('Rolls-Royce Cullinan', 'Rolls-Royce', r'Cullinan.*'), ('Rolls-Royce Phantom', 'Rolls-Royce', r'Phantom.*'), ('Bugatti Chiron', 'Bugatti', r'Chiron.*'),
     ('Bugatti Veyron', 'Bugatti', r'Veyron.*'), ('Audi R8', 'Audi', r'R8.*'), ('Nissan GT-R', 'Nissan', r'GT-R.*'), ('Acura NSX', 'Acura', r'NSX.*'), ('Mercedes-AMG GT', 'Mercedes-Benz', r'(AMG GT.*|SLS AMG.*)'),
     ('Chevrolet Corvette Z06', 'Chevrolet', r'Corvette.*'), ('Ford GT', 'Ford', r'GT'), ('Lotus Evora / Emira', 'Lotus', r'(Evora.*|Emira.*)'), ('Porsche 911 Turbo / GT3', 'Porsche', r'911 (Turbo.*|GT[23].*)'),
     ('Porsche 918 Spyder', 'Porsche', r'918.*')]
slugify = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower().replace("'", '')).strip('-')
SC = {c['name']: c for c in json.load(open(os.path.join(HERE, 'data', 'supercars.json'), encoding='utf-8'))}
def epa_engine(fam, model, d, cyl, t, s, atv, y, dscr):
    d = float(d or 0); cyl = int(cyl or 0); ph = atv == 'Plug-in Hybrid'
    if fam.startswith('Ferrari'):
        if d in (4.5, 4.3): return 'ferrari-f136'
        if d == 3.9 and cyl == 8: return 'ferrari-f154'
        if cyl == 12: return 'ferrari-f140'
        if model.startswith('296'): return 'ferrari-f163'
    if fam in ('Lamborghini Huracán', 'Lamborghini Gallardo'): return 'lamborghini-v10'
    if fam == 'Lamborghini Aventador': return 'lamborghini-l539'
    if fam == 'Lamborghini Revuelto': return 'lamborghini-l545'
    if fam == 'Lamborghini Urus': return None if ph else 'vw-ea825'
    if fam.startswith('McLaren'): return 'mclaren-m630' if model == 'Artura' else 'mclaren-m838t' if d == 3.8 else 'mclaren-m840t' if d == 4.0 else None
    if fam.startswith('Aston Martin'):
        if d == 4.7: return 'aston-am-v8'
        if cyl == 12 and not t: return 'aston-am-v12'
        if cyl == 12 and t: return 'aston-ae31'
        if d == 4.0 and t: return 'amg-m177-m178'
    if fam.startswith('Bentley'):
        if cyl == 12: return 'vw-w12'
        if cyl == 6: return 'vw-ea839' if 'Bentayga' in model else None
        if d == 4.0 and not ph: return 'vw-ea825' if ('Bentayga' in model or y >= 2019) else 'audi-ea824'
        return None
    if fam.startswith('Rolls-Royce'): return 'rr-n73' if (model.startswith('Phantom') and not t) else 'rr-n74'
    if fam.startswith('Bugatti'): return 'bugatti-w16'
    if fam == 'Audi R8': return 'audi-42-fsi' if d == 4.2 else 'lamborghini-v10'
    if fam == 'Nissan GT-R': return 'nissan-vr38dett'
    if fam == 'Acura NSX': return 'acura-jnc1'
    if fam == 'Mercedes-AMG GT':
        if model.startswith('SLS'): return 'amg-m159'
        if d == 4.0: return 'amg-m177-m178'
        if d == 3.0: return 'amg-m256'
        if d == 2.0: return 'amg-m139'
    if fam == 'Chevrolet Corvette Z06':
        if 'E-Ray' in model or 'E-RAY' in model: return 'gm-lt2'
        if 'ZR1' in model: return 'gm-lt5' if d == 6.2 else 'gm-lt7'
        if 'Z06' in model or 'Z06' in dscr: return 'gm-lt4' if d == 6.2 else 'gm-lt6'
    if fam == 'Ford GT': return 'ford-ecoboost-35'
    if fam == 'Lotus Evora / Emira': return 'toyota-2gr' if d == 3.5 else None
    if fam == 'Porsche 911 Turbo / GT3':
        if 'GT3' in model: return 'porsche-m97' if y <= 2011 else 'porsche-ma1-gt3'
        if 'GT2' in model: return 'porsche-m97' if y <= 2011 else 'porsche-turbo-38'
        if 'Turbo' in model: return 'porsche-turbo-38' if d == 3.8 else 'porsche-9a2'
    if fam == 'Porsche 918 Spyder': return 'porsche-918-v8'
    return None
V = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(set)))   # eng -> year -> fam -> versions
FY = collections.defaultdict(lambda: collections.defaultdict(set))   # fam -> year -> engines (None = not confirmed)
HP = {}
for r in csv.DictReader(open(os.path.join(CACHE, 'vehicles.csv'), encoding='utf-8', errors='replace')):
    y = int(r['year'])
    if not 2010 <= y <= 2025: continue
    for fam, mk, rx in F:
        if r['make'] != mk or not re.fullmatch(rx, r['model']): continue
        # same picks as data_supercars.py, plus the 2015-2018 C7 Z06 (EPA files it under "Corvette" with "Z06" in the engine notes) and the 2024 E-Ray
        if fam == 'Chevrolet Corvette Z06' and not re.search(r'Z06|ZR1|E-Ray|E-RAY', r['model'] + ' ' + r['eng_dscr']): continue
        if fam in SC and y not in {x['y'] for x in SC[fam]['years']} and fam != 'Chevrolet Corvette Z06': continue
        e = epa_engine(fam, r['model'], r['displ'], r['cylinders'], r['tCharger'] == 'T', r['sCharger'] == 'S', r['atvType'], y, r['eng_dscr'])
        FY[fam][y].add(e)
        if e: V[e][y][fam].add('Corvette Z06' if r['model'] == 'Corvette' else r['model'])   # the C7 Z06 is filed as plain "Corvette" with "Z06" in EPA's engine notes
SINGLE = {(fam, y): next(iter(es)) for fam, yy in FY.items() for y, es in yy.items() if len(es) == 1 and None not in es}
# ---- NHTSA model names (complaints, repair notes) -> engine, only where the name and year leave no doubt
NH = [('FERRARI', r'458.*', 2010, 2015, 'ferrari-f136'), ('FERRARI', r'CALIFORNIA', 2010, 2014, 'ferrari-f136'), ('FERRARI', r'CALIFORNIA T|CALIFORNIA', 2015, 2018, 'ferrari-f154'),
      ('FERRARI', r'488.*|F8.*|PORTOFINO.*|ROMA.*|SF90.*|GTC4LUSSO T', 2016, 2025, 'ferrari-f154'), ('FERRARI', r'FF|F12.*|GTC4LUSSO|812.*', 2012, 2024, 'ferrari-f140'), ('FERRARI', r'296.*', 2022, 2025, 'ferrari-f163'),
      ('LAMBORGHINI', r'HURACAN.*|GALLARDO.*', 2010, 2024, 'lamborghini-v10'), ('LAMBORGHINI', r'AVENTADOR.*', 2012, 2022, 'lamborghini-l539'), ('LAMBORGHINI', r'REVUELTO', 2024, 2025, 'lamborghini-l545'),
      ('LAMBORGHINI', r'URUS', 2019, 2024, 'vw-ea825'), ('MCLAREN', r'MP4-12C.*|650S.*|675.*|570.*|540C|600LT.*|620R', 2012, 2020, 'mclaren-m838t'), ('MCLAREN', r'720S.*|765LT.*|GT', 2018, 2022, 'mclaren-m840t'),
      ('MCLAREN', r'ARTURA.*', 2023, 2023, 'mclaren-m630'), ('ASTON MARTIN', r'V8 VANTAGE.*|VANTAGE GT', 2010, 2016, 'aston-am-v8'), ('ASTON MARTIN', r'V12 VANTAGE.*', 2011, 2017, 'aston-am-v12'),
      ('ASTON MARTIN', r'DBS', 2010, 2012, 'aston-am-v12'), ('ASTON MARTIN', r'DBS SUPERLEGGERA|DBS', 2019, 2023, 'aston-ae31'), ('ASTON MARTIN', r'VANTAGE', 2019, 2022, 'amg-m177-m178'),
      ('ASTON MARTIN', r'VANTAGE', 2024, 2025, 'amg-m177-m178'), ('ASTON MARTIN', r'DBX.*|DB12', 2021, 2025, 'amg-m177-m178'), ('BENTLEY', r'BENTAYGA', 2017, 2018, 'vw-w12'),
      ('BENTLEY', r'BENTAYGA HYBRID', 2020, 2025, 'vw-ea839'), ('BENTLEY', r'CONTINENTAL.*', 2010, 2012, 'vw-w12'), ('BENTLEY', r'CONTINENTAL SUPERSPORTS|SUPERSPORTS|CONTINENTAL GT SPEED', 2010, 2024, 'vw-w12'),
      ('ROLLS-ROYCE', r'GHOST|CULLINAN', 2010, 2025, 'rr-n74'), ('ROLLS-ROYCE', r'PHANTOM.*', 2010, 2017, 'rr-n73'), ('ROLLS-ROYCE', r'PHANTOM.*', 2018, 2025, 'rr-n74'),
      ('BUGATTI', r'CHIRON.*|VEYRON.*', 2010, 2024, 'bugatti-w16'), ('AUDI', r'R8.*', 2016, 2023, 'lamborghini-v10'), ('NISSAN', r'GT-R', 2010, 2024, 'nissan-vr38dett'), ('ACURA', r'NSX', 2017, 2022, 'acura-jnc1'),
      ('MERCEDES-BENZ', r'(AMG )?SLS.*', 2011, 2015, 'amg-m159'), ('MERCEDES-BENZ', r'AMG GT|AMG GT S', 2016, 2018, 'amg-m177-m178'), ('MERCEDES-BENZ', r'AMG GT (C|R)( ROADSTER| COUPE)?|AMG GT ROADSTER', 2016, 2021, 'amg-m177-m178'),
      ('MERCEDES-BENZ', r'AMG GT ?63.*|AMG GT ?55.*', 2019, 2025, 'amg-m177-m178'), ('MERCEDES-BENZ', r'AMG GT ?53|AMG GT ?43', 2019, 2024, 'amg-m256'),
      ('CHEVROLET', r'CORVETTE Z06', 2015, 2019, 'gm-lt4'), ('CHEVROLET', r'CORVETTE Z06', 2023, 2025, 'gm-lt6'), ('CHEVROLET', r'CORVETTE ZR1', 2019, 2019, 'gm-lt5'), ('CHEVROLET', r'CORVETTE ZR1', 2025, 2025, 'gm-lt7'),
      ('CHEVROLET', r'CORVETTE( COUPE| CONVERTIBLE)? E-RAY', 2024, 2025, 'gm-lt2'), ('FORD', r'GT', 2017, 2022, 'ford-ecoboost-35'), ('LOTUS', r'EVORA.*|EMIRA', 2010, 2025, 'toyota-2gr'),
      ('PORSCHE', r'911 GT3.*', 2010, 2011, 'porsche-m97'), ('PORSCHE', r'911 GT2( RS)?', 2011, 2011, 'porsche-m97'), ('PORSCHE', r'911 GT3.*', 2014, 2024, 'porsche-ma1-gt3'),
      ('PORSCHE', r'911 TURBO.*', 2010, 2019, 'porsche-turbo-38'), ('PORSCHE', r'911 GT2( RS)?', 2018, 2019, 'porsche-turbo-38'), ('PORSCHE', r'911 TURBO.*', 2021, 2025, 'porsche-9a2'),
      ('PORSCHE', r'918.*', 2015, 2015, 'porsche-918-v8')]
# the owner's or automaker's own words naming a version with one engine that year (Corvette Z06 / ZR1 / E-Ray; Bentley W12 / V8; Audi R8 V10 / V8)
TXT = [('CHEVROLET', r'CORVETTE.*', r'\bZ06\b', [(2015, 2019, 'gm-lt4'), (2023, 2025, 'gm-lt6')]), ('CHEVROLET', r'CORVETTE.*', r'\bZR-?1\b', [(2019, 2019, 'gm-lt5'), (2025, 2025, 'gm-lt7')]),
       ('CHEVROLET', r'CORVETTE.*', r'\bE-?\s?RAY\b', [(2024, 2025, 'gm-lt2')]), ('BENTLEY', r'CONTINENTAL.*|FLYING SPUR|BENTAYGA', r'\bW12\b|\bW-12\b', [(2010, 2024, 'vw-w12')]),
       ('BENTLEY', r'CONTINENTAL.*', r'\bV8\b|4\.0', [(2013, 2017, 'audi-ea824'), (2020, 2024, 'vw-ea825')]), ('BENTLEY', r'BENTAYGA', r'\bV8\b|4\.0', [(2019, 2025, 'vw-ea825')]),
       ('AUDI', r'R8.*', r'\bV10\b|5\.2', [(2010, 2015, 'lamborghini-v10')]), ('AUDI', r'R8.*', r'\bV8\b|4\.2', [(2010, 2015, 'audi-42-fsi')]),
       ('ASTON MARTIN', r'DB11.*', r'\bV8\b', [(2018, 2023, 'amg-m177-m178')]), ('ASTON MARTIN', r'DB11.*', r'\bV12\b', [(2017, 2023, 'aston-ae31')])]
EY = {e: {y for y in ys} for e, ys in V.items()}
def nh_engines(mk, md, y, text=''):
    md = re.sub(r'\s+', ' ', md.upper().strip()); out = set()
    for m, rx, a, b, e in NH:
        if mk == m and a <= y <= b and re.fullmatch(rx, md): out.add(e)
    for m, rx, trx, spans in TXT:
        if mk == m and re.fullmatch(rx, md) and re.search(trx, text or '', re.I):
            for a, b, e in spans:
                if a <= y <= b: out.add(e)
    return {e for e in out if y in EY.get(e, ())}
MAKES = ('FERRARI', 'LAMBORGHINI', 'MCLAREN', 'ASTON MARTIN', 'BENTLEY', 'ROLLS-ROYCE', 'BUGATTI', 'AUDI', 'NISSAN', 'ACURA', 'MERCEDES-BENZ', 'CHEVROLET', 'FORD', 'LOTUS', 'PORSCHE')
# ---- owner complaints
con = sqlite3.connect(DB)
CMP = collections.defaultdict(lambda: collections.defaultdict(set)); PART = collections.defaultdict(collections.Counter)
for odi, mk, md, y, comp, descr in con.execute(f"select odino, make, model, year, comp, descr from rows where make in ({','.join('?' * len(MAKES))}) and year between 2010 and 2025", MAKES):
    if mk == 'CHEVROLET' and not (md or '').upper().startswith('CORVETTE'): continue
    for e in nh_engines(mk, md or '', y, descr):
        if odi not in CMP[e][y]: PART[e][(comp or 'OTHER').split(':')[0].strip().title()] += 1
        CMP[e][y].add(odi)
# ---- repair notes (manufacturer communications)
ENGW = re.compile(r'\bengine (oil|coolant|noise|misfire|warning|light|stall|leak|knock|rattle|tick|damage|fault|power)|oil (leak|consumption|pressure|pump|level|loss)|turbo|coolant|misfire|camshaft|timing|fuel|ignition|spark plug|injector|cylinder|piston|valve|intake|exhaust|catalytic|water pump|thermostat|radiator|cooling|throttle|crankcase|check engine|\bMIL\b|\bDME\b|\bECM\b|\bECU\b|hybrid|high.voltage|supercharg|intercooler|head gasket|starter|alternator', re.I)
SKIP = re.compile(r'gearbox|transmission|\bDCT\b|clutch|brake|headla?mp|fog lamp|seat|door|window|wiper|infotainment|underbody|record is|database|repair procedures|please find|level [123]\b|software version management|scan tool|diagnostic tester|labor operation|warranty|special tool|owner letter|delivery hold|pre-delivery|accessory|radio|navigation|paint|tire pressure|wheel bolt', re.I)
TSB = collections.defaultdict(dict)
for z in sorted(glob.glob(os.path.join(RAW, 'MFR_COMMS_RECEIVED_*.zip'))):
    zz = zipfile.ZipFile(z)
    for row in csv.reader(io.TextIOWrapper(zz.open(zz.namelist()[0]), encoding='utf-8', errors='replace')):
        if len(row) < 5 or row[0] == 'TSB/Document ID': continue
        mk = row[1].strip().upper()
        if mk not in MAKES: continue
        summ = re.sub(r'\s+', ' ', row[4]).strip()
        if not ENGW.search(summ) or SKIP.search(summ): continue
        for ys in row[3].split(','):
            if ys.strip().isdigit():
                for e in nh_engines(mk, row[2], int(ys), summ): TSB[e].setdefault(row[0], (summ, set()))[1].add(int(ys))
def one_line(s):
    s = re.sub(r'\*[A-Z]{2}\b.*$', '', s).strip()
    s = re.sub(r'^[A-Z][A-Z &-]{1,20}:\s*', '', s)
    s = re.split(r'(?<=[a-z0-9)])\s{2,}|(?<=[.!?])\s', s)[0].strip().rstrip('.')
    if s.isupper() or sum(c.isupper() for c in s) > len(s) * .6: s = s.lower()
    s = re.sub(r'^(subject regarding|information on|concerns with|complaint|this bulletin (provides information|contains instructions|provides a repair|describes)( for| on| about)?( when)?)\s+', '', s, flags=re.I)
    s = s[:1].upper() + s[1:]
    return (s[:110].rsplit(' ', 1)[0] + '…') if len(s) > 112 else s
PROB = re.compile(r'noise|leak|stall|hesitat|vibrat|rattl|no start|won.t start|inoperative|fail|warning|check engine|misfire|shudder|loss of|intermittent|overheat|crack|smoke|rough|fault', re.I)
JUNK = re.compile(r'appl(y|ies) to|does not apply|vehicles with code|this document|has determined|bulletin has been|workshop manual|technical information for a|Q5|LEAF|Titan|Hand detection|^[A-Z]+;|Mustang|GT500|Resubmitting|design package|VDDM|spoiler|AC charging|HVAC|Air Condition|Techline|SERVICE INFORMATION|Supporting Evidence|throttle pedal|have been identified|identified as having|Because of an error|Automobili Lamborghini|air ducts|rubber boot|splash shield|muffler|^Information regarding', re.I)
def tsb_top(tl):
    seen, out = set(), []
    for s, _ in tl:
        if not PROB.search(s): continue
        t = re.sub(r'^[A-Z][A-Za-z-]+;\s*', '', one_line(s))
        if JUNK.search(t) or JUNK.search(s[:60]): continue
        k = re.sub(r'[^a-z]', '', t.lower())[:28]
        if k in seen: continue
        seen.add(k); out.append(t)
        if len(out) == 3: break
    return out
# ---- recalls (already pulled per family and year in supercars.json)
ENGR = re.compile(r'engine|fuel|oil|turbo|coolant|cooling|exhaust|ignition|hybrid|power ?train|electrical system:12v|throttle|propulsion', re.I)
def rec_engines(fam, y, r):
    if (fam, y) in SINGLE: return {SINGLE[(fam, y)]}
    t = (r.get('summary') or '') + ' ' + (r.get('part') or ''); out = set()
    for e in {x for x in FY[fam][y] if x}:
        m = M[e]; toks = [re.escape(m['code'])] + {'vw-w12': [r'W12'], 'audi-ea824': [r'V8'], 'vw-ea825': [r'V8'], 'vw-ea839': [r'hybrid'], 'amg-m177-m178': [r'V8'], 'aston-ae31': [r'V12'], 'aston-am-v12': [r'V12'],
                                                          'aston-am-v8': [r'V8'], 'lamborghini-v10': [r'V10'], 'audi-42-fsi': [r'V8'], 'amg-m256': [r'GT ?53|GT ?43'], 'gm-lt2': [r'E-?Ray']}.get(e, [])
        if any(re.search(rf'\b{x}\b', t, re.I) for x in toks): out.add(e)
    return out
REC = collections.defaultdict(dict)
for fam, c in SC.items():
    for yy in c['years']:
        for r in yy['recalls']:
            for e in rec_engines(fam, yy['y'], r):
                d = REC[e].setdefault(r['id'], dict(id=r['id'], date=r['date'], part=(r['part'] or '').split(':')[0].strip().title(), summary=r['summary'], years=set(), cars=set(), eng=bool(ENGR.search(r['part'] or ''))))
                d['years'].add(yy['y']); d['cars'].add(fam)
# ---- assemble
out = {}
for e, m in M.items():
    yrs = V.get(e)
    if not yrs: print('NO EPA VERSIONS', e); continue
    years = {}
    for y in sorted(yrs):
        years[str(y)] = dict(cars={slugify(f): sorted(v) for f, v in yrs[y].items()}, n=len(CMP[e].get(y, ())), only=all((f, y) in SINGLE for f in yrs[y]))
    tot = sum(v['n'] for v in years.values())
    tl = sorted(TSB[e].values(), key=lambda x: (-(1 if PROB.search(x[0]) else 0), -max(x[1])))
    recs = sorted(REC[e].values(), key=lambda r: (not r['eng'], r['date'][-4:] + r['date'][3:5] if r['date'] else ''), reverse=False)
    recs = sorted(recs, key=lambda r: (not r['eng'], -int((r['date'] or '0000')[-4:] or 0)))
    cars = collections.OrderedDict()
    for y in sorted(yrs):
        for f in yrs[y]: cars.setdefault(f, []).append(y)
    out[e] = dict(m, notes=NOTES.get(e, []), y0=min(yrs), y1=max(yrs), years=years, complaints=tot, parts=PART[e].most_common(4), chart=tot >= 30 and sum(1 for v in years.values() if v['n']) >= 3,
                  cars=[dict(slug=slugify(f), name=f, years=ys, page=f in SC) for f, ys in cars.items()],
                  recalls=[dict(r, years=sorted(r['years']), cars=sorted(r['cars'])) for r in recs],
                  tsb=dict(n=len(TSB[e]), top=tsb_top(tl)))
    print(f"{e:20} {out[e]['y0']}-{out[e]['y1']} cars {len(cars)} complaints {tot:4} recalls {len(recs):3} (engine {sum(r['eng'] for r in recs)}) notes {len(TSB[e]):4}  chart {out[e]['chart']}")
car_eng = collections.defaultdict(dict)
for e, d in out.items():
    for c in d['cars']:
        car_eng[c['slug']][e] = c['years']
nc = sorted({(f, y) for f, yy in FY.items() for y, es in yy.items() if None in es})
print('model-years with a version no source confirms:', nc)
json.dump(dict(engines=out, cars=car_eng, unconfirmed=[f'{f} {y}' for f, y in nc]), open(os.path.join(HERE, 'data', 'supercar_engines.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('engines', len(out))
