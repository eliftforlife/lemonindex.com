# Everyday-car engine pages from VIN-matched owner complaints (11-13, Elijah: "turn the Coming soon engines into real engine pages, highest
# traffic first"). Same method as data_hd.py (the F-150 / heavy-duty engines) and shorts v2/follow-B4 ("which engine is the lemon"):
#   1. extract: every NHTSA owner complaint (FLAT_CMPL.txt + COMPLAINTS_RECEIVED_2025-2026.zip) on the /cars/ models below, with its partial VIN.
#      A complaint belongs to a /cars/ model through the NHTSA make + model names that model's own pages count (data/extras_local*.json, the
#      rule data_engine_uses.py uses), so these pages and the car pages agree on which complaints are which car.
#   2. decode: the VIN's first 8 characters (maker + vehicle descriptor, which holds the engine on every make) and the model year are one key;
#      the most common 11-character VIN of each key is decoded with NHTSA vPIC's batch decoder (displacement, cylinders, engine model, fuel,
#      turbo, hybrid). Cached in data/vin_engines/decoded.json, 50 VINs per request, a pause between requests.
#   3. recalls: NHTSA recalls API per model name and year (the shared data/cache, like data_hd.py)
#   4. build -> data/vin_engines.json: per engine (years, cars, complaints, components, owner-words counts, mileage, quotes, recalls naming it)
# Which engine a complaint is about comes ONLY from its VIN decode plus the engine maker's model-year facts (e.g. a 3.5 V6 Tacoma from 2016 on
# is the 2GR-FKS). A decode that doesn't fit an engine's rule exactly stays unmatched. No sales by engine exist, so pages show counts and shares.
#   usage: py -X utf8 data_vin_engines.py [extract] [decode] [recalls] [build]     (no args = every stage; each stage caches its output)
import collections, hashlib, json, os, re, sys, time, urllib.parse, urllib.request, zipfile
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
WORK = os.path.join(LEMON, 'data', 'vin_engines'); os.makedirs(WORK, exist_ok=True)
FLAT = os.path.join(LEMON, 'video 1 most reliable', 'data', 'raw', 'FLAT_CMPL.txt')
NEWZ = os.path.join(LEMON, 'data', 'raw', 'nhtsa', 'COMPLAINTS_RECEIVED_2025-2026.zip')
CACHE = r'C:\Users\elift\Code\lemonindex-site\data\cache'   # the shared API cache (main checkout)
if not os.path.isdir(CACHE): CACHE = os.path.join(HERE, 'data', 'cache')
STAGES = set(sys.argv[1:]) or {'extract', 'decode', 'recalls', 'build'}
Y0, Y1 = 2000, 2026
norm = lambda s: re.sub(r'[^A-Z0-9]', '', (s or '').upper())

# ---------------------------------------------------------------- engines with a page (facts: the engine makers' public names and model years)
# cars: /cars/ model id -> (first, last model year) this engine was offered in it. rule: what the vPIC decode must say.
#   turbo_ok = cars where the maker sold no non-turbo engine of this size in these years, so a decode with a blank Turbo field still counts
#   disp = displacement (L, rounded to 0.1), cyl, turbo True/False/None (None = don't care), code = regex the decode's engine model must match
#   when vPIC names one (a decode that names a different engine model is left out), hybrid False = conventional versions only.
ENG = {
    'toyota-2gr-fks': dict(name='Toyota 2GR-FKS 3.5 V6', short='2GR-FKS', maker='Toyota', code='2GR-FKS', lay='3.5 L V6, direct + port injection', fuel='gas',
                           cars={'toyota-tacoma': (2016, 2023), 'toyota-highlander': (2017, 2022), 'toyota-sienna': (2017, 2020), 'toyota-camry': (2018, 2024),
                                 'toyota-avalon': (2019, 2022), 'lexus-rx': (2016, 2022), 'lexus-es': (2019, 2025)},
                           rule=dict(disp=3.5, cyl=6, turbo=False, hybrid=False, code=r'2GR-?FKS|^$'), alias='2gr fks 2grfks 3.5 v6 tacoma highlander sienna camry v6'),
    'toyota-2gr-fe': dict(name='Toyota 2GR-FE 3.5 V6', short='2GR-FE', maker='Toyota', code='2GR-FE', lay='3.5 L V6', fuel='gas', page='/engines/toyota-2gr/',
                          cars={'toyota-camry': (2007, 2017), 'toyota-highlander': (2008, 2016), 'toyota-sienna': (2007, 2016), 'toyota-avalon': (2005, 2018),
                                'toyota-rav4': (2006, 2012), 'lexus-rx': (2007, 2015), 'lexus-es': (2007, 2018)},
                          rule=dict(disp=3.5, cyl=6, turbo=False, hybrid=False, code=r'2GR-?FE\b|^$'), alias='2gr fe 2grfe 3.5 v6 camry highlander sienna avalon rav4'),
    'gm-53-gen5': dict(name='GM 5.3 V8 (L83 / L84)', short='5.3 V8 (Gen V)', maker='GM', code='L83 / L84', lay='5.3 L V8, direct injection', fuel='gas',
                       cars={'chevrolet-silverado': (2014, 2025), 'gmc-sierra': (2014, 2025), 'chevrolet-tahoe': (2015, 2025), 'chevrolet-suburban': (2015, 2025),
                             'gmc-yukon': (2015, 2025), 'gmc-yukon-xl': (2015, 2025)},
                       rule=dict(disp=5.3, cyl=8, code=r'\bL8[34]\b|^$'), alias='5.3 v8 53 l83 l84 ecotec3 silverado sierra tahoe suburban yukon afm dfm lifter'),
    'gm-53-gen4': dict(name='GM 5.3 V8 (Vortec, 2007–13)', short='5.3 V8 (Gen IV)', maker='GM', code='LMG / LC9 / LH6 / LY5', lay='5.3 L V8', fuel='gas',
                       cars={'chevrolet-silverado': (2008, 2013), 'gmc-sierra': (2008, 2013), 'chevrolet-tahoe': (2007, 2014), 'chevrolet-suburban': (2007, 2014),
                             'gmc-yukon': (2007, 2014), 'gmc-yukon-xl': (2007, 2014), 'chevrolet-avalanche': (2007, 2013)},
                       rule=dict(disp=5.3, cyl=8, code=r'\bL(MG|C9|H6|Y5|MF)\b|^$', hybrid=False), alias='5.3 v8 53 vortec lmg lc9 lh6 ly5 silverado sierra tahoe suburban yukon avalanche afm oil consumption'),
    'gm-62-gen5': dict(name='GM 6.2 V8 (L86 / L87)', short='6.2 V8 (Gen V)', maker='GM', code='L86 / L87', lay='6.2 L V8, direct injection', fuel='gas',
                       cars={'chevrolet-silverado': (2014, 2025), 'gmc-sierra': (2014, 2025), 'chevrolet-tahoe': (2015, 2025), 'chevrolet-suburban': (2015, 2025),
                             'gmc-yukon': (2015, 2025), 'gmc-yukon-xl': (2015, 2025), 'cadillac-escalade': (2015, 2025)},
                       rule=dict(disp=6.2, cyl=8, code=r'\bL8[67]\b|^$'), alias='6.2 v8 62 l86 l87 silverado sierra denali escalade tahoe yukon lifter'),
    'hyundai-theta2-24': dict(name='Hyundai / Kia 2.4 Theta II', short='2.4 Theta II', maker='Hyundai', code='G4KJ / G4KE', lay='2.4 L inline-4', fuel='gas',
                              cars={'hyundai-sonata': (2011, 2019), 'kia-optima': (2011, 2020), 'hyundai-santa-fe': (2010, 2019), 'kia-sorento': (2011, 2020),
                                    'hyundai-tucson': (2010, 2021), 'kia-sportage': (2011, 2022)},
                              rule=dict(disp=2.4, cyl=4, turbo=None, hybrid=False), alias='2.4 theta 2 theta ii g4kj g4ke gdi sonata optima santa fe sorento tucson sportage engine failure knock sensor'),
    'hyundai-theta2-20t': dict(name='Hyundai / Kia 2.0 turbo Theta II', short='2.0T Theta II', maker='Hyundai', code='G4KH', lay='2.0 L inline-4 turbo', fuel='gas', page='/engines/hyundai-g4kh/',
                               cars={'hyundai-sonata': (2011, 2019), 'kia-optima': (2011, 2020), 'hyundai-santa-fe': (2013, 2020), 'kia-sorento': (2016, 2020),
                                     'kia-sportage': (2011, 2022)},
                               rule=dict(disp=2.0, cyl=4, turbo=True, hybrid=False), alias='2.0t theta ii turbo g4kh sonata turbo optima sx santa fe sport sportage sx'),
    'honda-j35': dict(name='Honda J35 3.5 V6', short='J35 V6', maker='Honda', code='J35', lay='3.5 L V6, VTEC', fuel='gas',
                      cars={'honda-pilot': (2003, 2025), 'honda-odyssey': (2005, 2025), 'honda-accord': (2008, 2017), 'honda-ridgeline': (2006, 2025),
                            'honda-passport': (2019, 2025), 'acura-mdx': (2007, 2020), 'acura-tl': (2009, 2014), 'acura-tlx': (2015, 2020), 'acura-rdx': (2013, 2018)},
                      rule=dict(disp=3.5, cyl=6, turbo=False, hybrid=False), alias='j35 3.5 v6 vtec vcm pilot odyssey accord v6 ridgeline passport mdx'),
    'ford-35-cyclone': dict(name='Ford 3.5 Duratec / Cyclone V6', short='3.5 Cyclone V6', maker='Ford', code='Duratec 35 / Cyclone', lay='3.5 L V6, non-turbo', fuel='gas',
                            cars={'ford-explorer': (2011, 2019), 'ford-edge': (2007, 2018), 'ford-flex': (2009, 2019), 'ford-taurus': (2008, 2019),
                                  'ford-f-series': (2015, 2017), 'lincoln-mkx': (2007, 2010), 'ford-fusion': (2010, 2012)},
                            rule=dict(disp=3.5, cyl=6, turbo=False, hybrid=False, vin8={'C', '8', 'W'}), alias='3.5 duratec cyclone ti-vct v6 explorer edge flex taurus water pump'),
    'ford-ecoboost-15': dict(name='Ford 1.5 EcoBoost', short='1.5 EcoBoost', maker='Ford', code='1.5 EcoBoost', lay='1.5 L inline-4 turbo', fuel='gas',
                             cars={'ford-escape': (2014, 2025), 'ford-fusion': (2014, 2020)},
                             rule=dict(disp=1.5, cyl=4, turbo=None, hybrid=False), alias='1.5 ecoboost escape fusion coolant intrusion'),
    'ford-ecoboost-20': dict(name='Ford 2.0 EcoBoost', short='2.0 EcoBoost', maker='Ford', code='2.0 EcoBoost', lay='2.0 L inline-4 turbo', fuel='gas',
                             cars={'ford-escape': (2013, 2025), 'ford-fusion': (2013, 2020), 'ford-edge': (2012, 2024), 'ford-explorer': (2012, 2016),
                                   'lincoln-mkz': (2013, 2020), 'lincoln-mkx': (2016, 2018), 'ford-taurus': (2013, 2016)},
                             rule=dict(disp=2.0, cyl=4, turbo=True, hybrid=False, turbo_ok={'ford-explorer', 'ford-edge', 'ford-taurus', 'ford-escape', 'lincoln-mkx'}), alias='2.0 ecoboost escape fusion edge explorer mkz coolant intrusion'),
    'nissan-vq35': dict(name='Nissan VQ35 3.5 V6', short='VQ35 V6', maker='Nissan', code='VQ35DE / VQ35DD', lay='3.5 L V6', fuel='gas',
                        cars={'nissan-altima': (2002, 2018), 'nissan-maxima': (2004, 2025), 'nissan-murano': (2003, 2025), 'nissan-pathfinder': (2013, 2025),
                              'nissan-quest': (2004, 2017)},
                        rule=dict(disp=3.5, cyl=6, turbo=False, hybrid=False), alias='vq35 vq35de vq35dd 3.5 v6 altima maxima murano pathfinder quest'),
    'chrysler-36-pentastar': dict(name='Chrysler 3.6 Pentastar V6', short='3.6 Pentastar', maker='Chrysler', code='Pentastar', lay='3.6 L V6', fuel='gas',
                                  cars={'jeep-grand-cherokee': (2011, 2025), 'jeep-wrangler': (2012, 2025), 'ram-pickup': (2013, 2025), 'dodge-durango': (2011, 2025),
                                        'chrysler-pacifica': (2017, 2025), 'dodge-grand-caravan': (2011, 2020), 'chrysler-town-and-country': (2011, 2016),
                                        'dodge-charger': (2011, 2023), 'chrysler-300': (2011, 2023), 'dodge-challenger': (2011, 2023), 'dodge-journey': (2011, 2020),
                                        'jeep-gladiator': (2020, 2025)},
                                  rule=dict(disp=3.6, cyl=6, turbo=False, hybrid=False), alias='3.6 pentastar v6 grand cherokee wrangler ram 1500 durango pacifica caravan charger 300 oil filter housing ticking'),
    'chrysler-57-hemi': dict(name='Chrysler 5.7 HEMI V8', short='5.7 HEMI', maker='Chrysler', code='5.7 HEMI', lay='5.7 L V8', fuel='gas',
                             cars={'ram-pickup': (2003, 2025), 'jeep-grand-cherokee': (2005, 2021), 'dodge-durango': (2004, 2025), 'dodge-charger': (2005, 2023),
                                   'chrysler-300': (2005, 2023), 'dodge-challenger': (2009, 2023), 'jeep-commander': (2006, 2010)},
                             rule=dict(disp=5.7, cyl=8, hybrid=False), alias='5.7 hemi v8 57 ram 1500 grand cherokee durango charger r/t 300c challenger lifter tick'),
    'subaru-fb25': dict(name='Subaru FB25 2.5 boxer', short='FB25', maker='Subaru', code='FB25', lay='2.5 L flat-4', fuel='gas',
                        cars={'subaru-forester': (2011, 2025), 'subaru-outback': (2013, 2025), 'subaru-legacy': (2013, 2025), 'subaru-crosstrek': (2024, 2025), 'subaru-impreza': (2024, 2025)},
                        rule=dict(disp=2.5, cyl=4, turbo=False, hybrid=False), alias='fb25 2.5 boxer forester outback legacy oil consumption'),
    'subaru-fb20': dict(name='Subaru FB20 2.0 boxer', short='FB20', maker='Subaru', code='FB20', lay='2.0 L flat-4', fuel='gas',
                        cars={'subaru-impreza': (2012, 2025), 'subaru-crosstrek': (2013, 2025)},
                        rule=dict(disp=2.0, cyl=4, turbo=False, hybrid=False), alias='fb20 2.0 boxer impreza crosstrek xv oil consumption'),
    'mazda-skyactiv-25': dict(name='Mazda Skyactiv-G 2.5', short='Skyactiv-G 2.5', maker='Mazda', code='PY-VPS', lay='2.5 L inline-4', fuel='gas',
                              cars={'mazda-cx-5': (2014, 2025), 'mazda6': (2014, 2021), 'mazda3': (2014, 2025)},
                              rule=dict(disp=2.5, cyl=4, turbo=False, hybrid=False), alias='skyactiv g 2.5 skyactiv-g py cx-5 mazda3 mazda6'),
    'toyota-a25a': dict(name='Toyota A25A 2.5 (Dynamic Force)', short='A25A', maker='Toyota', code='A25A-FKS', lay='2.5 L inline-4', fuel='gas',
                        cars={'toyota-camry': (2018, 2024), 'toyota-rav4': (2019, 2025), 'lexus-es': (2019, 2025)},
                        rule=dict(disp=2.5, cyl=4, turbo=False, hybrid=False, code=r'A25A|^$'), alias='a25a a25a-fks dynamic force 2.5 camry rav4 oil'),
    'toyota-2ar-fe': dict(name='Toyota 2AR-FE 2.5', short='2AR-FE', maker='Toyota', code='2AR-FE', lay='2.5 L inline-4', fuel='gas',
                          cars={'toyota-camry': (2010, 2017), 'toyota-rav4': (2009, 2018)},
                          rule=dict(disp=2.5, cyl=4, turbo=False, hybrid=False, code=r'2AR|^$'), alias='2ar 2ar-fe 2.5 camry rav4'),
    'vw-ea888': dict(name='VW / Audi 2.0 TSI (EA888)', short='EA888 2.0T', maker='VW', code='EA888', lay='2.0 L inline-4 turbo', fuel='gas', page='/engines/vw-ea888/',
                     cars={'volkswagen-golf': (2010, 2025), 'volkswagen-jetta': (2010, 2025), 'volkswagen-tiguan': (2009, 2025), 'volkswagen-atlas': (2018, 2025),
                           'volkswagen-passat': (2012, 2022), 'volkswagen-cc': (2009, 2017), 'audi-a3': (2009, 2025), 'audi-a4': (2009, 2025), 'audi-q5': (2011, 2025),
                           'audi-a6': (2012, 2025), 'audi-q3': (2015, 2025)},
                     rule=dict(disp=2.0, cyl=4, turbo=True, hybrid=False, diesel=False, turbo_ok={'volkswagen-golf', 'volkswagen-tiguan', 'volkswagen-atlas', 'volkswagen-passat', 'volkswagen-cc', 'audi-a3', 'audi-a4', 'audi-q5', 'audi-a6', 'audi-q3'}), alias='ea888 2.0t tsi tfsi gti gli tiguan atlas passat a4 a5 q5'),
    # ---- wave 2 (11-13): the next most-searched engines in big-selling models
    'ford-ecoboost-23': dict(name='Ford 2.3 EcoBoost', short='2.3 EcoBoost', maker='Ford', code='2.3 EcoBoost', lay='2.3 L inline-4 turbo', fuel='gas',
                             cars={'ford-explorer': (2016, 2025), 'ford-ranger': (2019, 2025), 'ford-mustang': (2015, 2025), 'ford-bronco': (2021, 2025)},
                             rule=dict(disp=2.3, cyl=4, turbo=None, hybrid=False), alias='2.3 ecoboost 23 explorer ranger mustang ecoboost bronco'),
    'gm-27-turbo': dict(name='GM 2.7 Turbo (L3B)', short='2.7 Turbo', maker='GM', code='L3B', lay='2.7 L inline-4 turbo', fuel='gas',
                        cars={'chevrolet-silverado': (2019, 2025), 'gmc-sierra': (2019, 2025), 'chevrolet-colorado': (2023, 2025), 'gmc-canyon': (2023, 2025)},
                        rule=dict(disp=2.7, cyl=4, hybrid=False), alias='2.7 turbo l3b turbomax silverado sierra colorado canyon 4 cylinder'),
    'gm-14-turbo': dict(name='GM 1.4 Turbo (LUJ / LUV / LE2)', short='1.4 Turbo', maker='GM', code='LUJ / LUV / LE2', lay='1.4 L inline-4 turbo', fuel='gas',
                        cars={'chevrolet-cruze': (2011, 2019), 'chevrolet-trax': (2015, 2022), 'buick-encore': (2013, 2022), 'chevrolet-sonic': (2012, 2020)},
                        rule=dict(disp=1.4, cyl=4, hybrid=False), alias='1.4 turbo 1.4t luj luv le2 cruze trax encore sonic'),
    'gm-24-ecotec': dict(name='GM 2.4 Ecotec (LAF / LEA)', short='2.4 Ecotec', maker='GM', code='LAF / LEA', lay='2.4 L inline-4, direct injection', fuel='gas',
                         cars={'chevrolet-equinox': (2010, 2017), 'gmc-terrain': (2010, 2017), 'buick-lacrosse': (2010, 2011), 'buick-regal': (2011, 2011)},
                         rule=dict(disp=2.4, cyl=4, turbo=False, hybrid=False, code=r'\bL(AF|EA)\b|^$'), alias='2.4 ecotec laf lea equinox terrain oil consumption piston rings'),
    'gm-36-v6': dict(name='GM 3.6 V6 (LLT / LFX / LGX)', short='3.6 V6', maker='GM', code='LLT / LFX / LGX', lay='3.6 L V6, direct injection', fuel='gas',
                     cars={'chevrolet-traverse': (2009, 2025), 'gmc-acadia': (2009, 2025), 'buick-enclave': (2009, 2025), 'chevrolet-impala': (2012, 2020),
                           'chevrolet-camaro': (2010, 2024), 'cadillac-srx': (2012, 2016), 'cadillac-cts': (2010, 2019), 'chevrolet-colorado': (2015, 2022), 'gmc-canyon': (2015, 2022)},
                     rule=dict(disp=3.6, cyl=6, turbo=False, hybrid=False, code=r'\bL(LT|FX|GX)\b|^$'), alias='3.6 v6 llt lfx lgx traverse acadia enclave impala camaro colorado timing chain'),
    'gm-15-turbo': dict(name='GM 1.5 Turbo (LFV / LYX)', short='1.5 Turbo', maker='GM', code='LFV / LYX', lay='1.5 L inline-4 turbo', fuel='gas',
                        cars={'chevrolet-malibu': (2016, 2025), 'chevrolet-equinox': (2018, 2024), 'gmc-terrain': (2018, 2024)},
                        rule=dict(disp=1.5, cyl=4, hybrid=False), alias='1.5 turbo 1.5t lfv lyx malibu equinox terrain'),
    'ram-30-ecodiesel': dict(name='Ram / Jeep 3.0 EcoDiesel V6', short='3.0 EcoDiesel', maker='Chrysler', code='EcoDiesel', lay='3.0 L V6 turbo diesel', fuel='diesel',
                             cars={'ram-pickup': (2014, 2023), 'jeep-grand-cherokee': (2014, 2019), 'jeep-wrangler': (2020, 2023), 'jeep-gladiator': (2021, 2023)},
                             rule=dict(disp=3.0, cyl=6, diesel=True), alias='3.0 ecodiesel eco diesel ram 1500 diesel grand cherokee diesel egr cooler'),
    'jeep-38-v6': dict(name='Chrysler 3.8 V6 (EGH)', short='3.8 V6', maker='Chrysler', code='EGH', lay='3.8 L V6, pushrod', fuel='gas',
                       cars={'jeep-wrangler': (2007, 2011), 'chrysler-town-and-country': (2007, 2010), 'dodge-grand-caravan': (2007, 2010)},
                       rule=dict(disp=3.8, cyl=6, hybrid=False), alias='3.8 v6 egh jeep wrangler jk 3.8 town and country grand caravan oil consumption'),
    'gm-48-vortec': dict(name='GM 4.8 Vortec V8', short='4.8 V8', maker='GM', code='LY2 / L20', lay='4.8 L V8', fuel='gas',
                         cars={'chevrolet-silverado': (2008, 2013), 'gmc-sierra': (2008, 2013), 'chevrolet-tahoe': (2007, 2013), 'gmc-yukon': (2007, 2013)},
                         rule=dict(disp=4.8, cyl=8, hybrid=False), alias='4.8 vortec v8 48 ly2 l20 silverado sierra tahoe yukon'),
    'ford-54-triton': dict(name='Ford 5.4 Triton V8 (3-valve)', short='5.4 Triton', maker='Ford', code='5.4 3V', lay='5.4 L V8, 3 valves per cylinder', fuel='gas',
                           cars={'ford-f-series': (2005, 2010), 'ford-expedition': (2005, 2014), 'lincoln-navigator': (2005, 2014)},
                           rule=dict(disp=5.4, cyl=8, turbo=False, hybrid=False), alias='5.4 triton 3v 3 valve f150 f-150 expedition navigator cam phaser spark plug'),
    'honda-15t': dict(name='Honda 1.5 Turbo (L15B7)', short='1.5 Turbo', maker='Honda', code='L15B7', lay='1.5 L inline-4 turbo', fuel='gas',
                      cars={'honda-cr-v': (2017, 2022), 'honda-accord': (2018, 2022)},
                      rule=dict(disp=1.5, cyl=4, turbo=None, hybrid=False), alias='1.5 turbo 1.5t l15b7 cr-v crv accord oil dilution gas in oil'),
    'honda-k24': dict(name='Honda K24 2.4', short='K24', maker='Honda', code='K24A / K24Z / K24W', lay='2.4 L inline-4', fuel='gas',
                      cars={'honda-cr-v': (2002, 2019), 'honda-accord': (2003, 2017), 'honda-element': (2003, 2011)},
                      rule=dict(disp=2.4, cyl=4, turbo=False, hybrid=False), alias='k24 k24a k24z k24w 2.4 cr-v crv accord element'),
    'nissan-qr25': dict(name='Nissan QR25DE 2.5', short='QR25DE', maker='Nissan', code='QR25DE', lay='2.5 L inline-4', fuel='gas',
                        cars={'nissan-rogue': (2008, 2020), 'nissan-altima': (2002, 2018), 'nissan-frontier': (2005, 2019), 'nissan-sentra': (2007, 2012)},
                        rule=dict(disp=2.5, cyl=4, turbo=False, hybrid=False), alias='qr25 qr25de 2.5 rogue altima frontier sentra se-r'),
    'toyota-2az-fe': dict(name='Toyota 2AZ-FE 2.4', short='2AZ-FE', maker='Toyota', code='2AZ-FE', lay='2.4 L inline-4', fuel='gas',
                          cars={'toyota-camry': (2002, 2009), 'toyota-rav4': (2004, 2008), 'toyota-highlander': (2001, 2007)},
                          rule=dict(disp=2.4, cyl=4, turbo=False, hybrid=False, code=r'2AZ|^$'), alias='2az 2az-fe 2.4 camry rav4 highlander oil consumption head bolt'),
    'toyota-1gr-fe': dict(name='Toyota 1GR-FE 4.0 V6', short='1GR-FE', maker='Toyota', code='1GR-FE', lay='4.0 L V6', fuel='gas',
                          cars={'toyota-tacoma': (2005, 2015), 'toyota-4runner': (2003, 2024), 'toyota-fj-cruiser': (2007, 2014), 'toyota-tundra': (2005, 2014)},
                          rule=dict(disp=4.0, cyl=6, turbo=False, hybrid=False, code=r'1GR|^$'), alias='1gr 1gr-fe 4.0 v6 tacoma 4runner fj cruiser tundra'),
    'toyota-3ur-fe': dict(name='Toyota 3UR-FE 5.7 V8', short='3UR-FE', maker='Toyota', code='3UR-FE', lay='5.7 L V8', fuel='gas',
                          cars={'toyota-tundra': (2007, 2021), 'toyota-sequoia': (2008, 2022)},
                          rule=dict(disp=5.7, cyl=8, hybrid=False, code=r'3UR|^$'), alias='3ur 3ur-fe 5.7 v8 tundra sequoia i-force'),
    'chrysler-24-tigershark': dict(name='Chrysler 2.4 Tigershark', short='2.4 Tigershark', maker='Chrysler', code='Tigershark', lay='2.4 L inline-4, MultiAir', fuel='gas',
                                   cars={'jeep-cherokee': (2014, 2023), 'jeep-renegade': (2015, 2023), 'jeep-compass': (2018, 2025), 'chrysler-200': (2015, 2017)},
                                   rule=dict(disp=2.4, cyl=4, turbo=False, hybrid=False), alias='2.4 tigershark multiair cherokee renegade compass chrysler 200 oil consumption'),
    'hyundai-lambda2-38': dict(name='Hyundai / Kia 3.8 V6 (Lambda II)', short='3.8 Lambda II', maker='Hyundai', code='G6DN', lay='3.8 L V6', fuel='gas',
                               cars={'hyundai-palisade': (2020, 2025), 'kia-telluride': (2020, 2025)},
                               rule=dict(disp=3.8, cyl=6, turbo=False, hybrid=False), alias='3.8 v6 lambda g6dn palisade telluride'),
    'hyundai-lambda2-33': dict(name='Hyundai / Kia 3.3 V6 (Lambda II)', short='3.3 Lambda II', maker='Hyundai', code='G6DH', lay='3.3 L V6', fuel='gas',
                               cars={'hyundai-santa-fe': (2013, 2019), 'kia-sorento': (2016, 2020), 'kia-sedona': (2015, 2021)},
                               rule=dict(disp=3.3, cyl=6, turbo=False, hybrid=False), alias='3.3 v6 lambda g6dh santa fe sorento sedona'),
}
# every /cars/ model and model year any engine above needs
TARGET = collections.defaultdict(set)
for e, d in ENG.items():
    for fid, (a, b) in d['cars'].items(): TARGET[fid] |= set(range(a, b + 1))

def want_map():
    """(MAKE, normalized NHTSA model, year) -> /cars/ model id, from the names each model year's own page counts (5%+ of its complaints)"""
    W = {}
    for p in ('extras_local.json', 'extras_local_new.json', 'extras_local_low.json'):
        fp = os.path.join(HERE, 'data', p)
        if not os.path.exists(fp): continue
        for fid, ys in json.load(open(fp, encoding='utf-8')).items():
            if fid not in TARGET: continue
            for y, e in ys.items():
                tot = sum(n for *_, n in e.get('names', [])) or 1
                for mk, md, n in e.get('names', []):
                    if n / tot >= .05: W.setdefault((mk.upper(), norm(md)), {}).setdefault(int(y), set()).add(fid)
    # a model year whose page has no names list (newest years) uses the names the same model files under in other years
    for key, ys in W.items():
        fids = set().union(*ys.values())
        for fid in fids:
            for y in TARGET[fid]:
                if y not in ys: ys[y] = {fid}
    return W

CMPL_JL = os.path.join(WORK, 'cmpl.jsonl')
VALID = re.compile(r'^[1-5JKSWYZ][A-HJ-NPR-Z0-9]{10}$')
def extract():
    W = want_map(); seen = {}
    def take(p):
        if len(p) < 20 or not p[5].strip().isdigit(): return
        y = int(p[5])
        if not Y0 <= y <= Y1: return
        fids = (W.get((p[3].strip().upper(), norm(p[4]))) or {}).get(y)
        if not fids: return
        vin = p[14].strip().upper()
        if len(vin) < 11 or not VALID.match(vin[:11]): return   # no VIN = no engine: these pages only count VIN-matched complaints
        o = p[1].strip(); c = p[11].strip()
        if o in seen:
            if c: seen[o]['comps'].add(c)
            return
        seen[o] = dict(o=o, f=sorted(fids), mk=p[3].strip().upper(), md=p[4].strip().upper(), y=y, vin=vin[:11], comps={c} if c else set(), ld=p[16].strip(), mi=p[17].strip(),
                       cr=p[6] == 'Y', fi=p[8] == 'Y', inj=int(p[9]) if p[9].strip().isdigit() else 0, dth=int(p[10]) if p[10].strip().isdigit() else 0,
                       tow=(p[48] == 'Y') if len(p) > 48 else False, d=p[19].strip()[:1500])
    with open(FLAT, encoding='latin-1') as fh:
        for line in fh: take(line.rstrip('\r\n').split('\t'))
    n0 = len(seen)
    with zipfile.ZipFile(NEWZ) as z:
        with z.open(z.namelist()[0]) as fh:
            for raw in fh: take(raw.decode('latin-1').rstrip('\r\n').split('\t'))
    with open(CMPL_JL, 'w', encoding='utf-8') as out:
        for r in seen.values(): r['comps'] = sorted(r['comps']); out.write(json.dumps(r) + '\n')
    print('extract:', n0, 'from FLAT_CMPL,', len(seen) - n0, 'newer;', collections.Counter(f for r in seen.values() for f in r['f']).most_common())

def load():
    return [json.loads(l) for l in open(CMPL_JL, encoding='utf-8')]

def get(url):
    path = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:20] + '.json')
    if os.path.exists(path): return json.load(open(path, encoding='utf-8'))
    for a in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'lemonindex.com data build'}), timeout=40) as r:
                body = r.read().decode('utf-8', 'replace')
            data = json.loads(body) if body.strip() else None; break
        except urllib.error.HTTPError as e:
            if e.code in (400, 404): data = None; break
            time.sleep(2 * (a + 1))
        except Exception: time.sleep(2 * (a + 1))
    else: return None
    os.makedirs(CACHE, exist_ok=True); json.dump(data, open(path, 'w', encoding='utf-8')); time.sleep(.3); return data

DEC_JS = os.path.join(WORK, 'decoded.json')
KEEP = ('DisplacementL', 'EngineCylinders', 'EngineModel', 'FuelTypePrimary', 'FuelTypeSecondary', 'Turbo', 'OtherEngineInfo', 'EngineManufacturer',
        'ElectrificationLevel', 'Make', 'Model', 'Series', 'Trim', 'EngineConfiguration', 'ErrorCode')
def vkey(r): return f'{r["vin"][:8]}|{r["y"]}'
def decode():
    """vPIC batch decoder: POST up to 50 'VIN,year' pairs per request, ~1 request every 1.5 s (NHTSA asks for polite automated use)"""
    R = load(); samp = collections.defaultdict(list)
    for r in R: samp[vkey(r)].append(r['vin'])
    D = json.load(open(DEC_JS, encoding='utf-8')) if os.path.exists(DEC_JS) else {}
    todo = [(k, collections.Counter(v).most_common(1)[0][0]) for k, v in sorted(samp.items(), key=lambda kv: -len(kv[1])) if len(v) >= 2 and k not in D]
    print('decode:', len(samp), 'keys,', sum(len(v) >= 2 for v in samp.values()), 'with 2+ complaints,', len(todo), 'to fetch', flush=True)
    for i in range(0, len(todo), 50):
        part = todo[i:i + 50]
        body = urllib.parse.urlencode({'format': 'json', 'data': ';'.join(f'{vin},{k.split("|")[1]}' for k, vin in part)}).encode()
        res = None
        for a in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request('https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/', data=body,
                                            headers={'User-Agent': 'lemonindex.com data build', 'Content-Type': 'application/x-www-form-urlencoded'}), timeout=90) as r:
                    res = json.loads(r.read().decode('utf-8', 'replace')).get('Results') or []
                break
            except Exception as ex:
                print('  retry', a, ex, flush=True); time.sleep(10 * (a + 1))
        if res is None: print('  gave up on batch', i); continue
        by = {}
        for x in res: by.setdefault((x.get('VIN') or '').upper()[:11], x)
        for k, vin in part:
            x = by.get(vin)
            if x: D[k] = dict(vin=vin, n=len(samp[k]), **{f: (x.get(f) or '')[:120] for f in KEEP})
        if (i // 50) % 10 == 0:
            json.dump(D, open(DEC_JS, 'w', encoding='utf-8')); print(' ', i + len(part), '/', len(todo), flush=True)
        time.sleep(1.5)
    json.dump(D, open(DEC_JS, 'w', encoding='utf-8')); print('decoded', len(D))

# ---------------------------------------------------------------- classify one decode
def _f(x):
    try: return round(float(x), 1)
    except (TypeError, ValueError): return None
def facts(x):
    em = (x.get('EngineModel') or '').strip(); oth = x.get('OtherEngineInfo') or ''
    fu = ' '.join([x.get('FuelTypePrimary') or '', x.get('FuelTypeSecondary') or '']).lower()
    el = (x.get('ElectrificationLevel') or '').lower()
    return dict(disp=_f(x.get('DisplacementL')), cyl=int(x['EngineCylinders']) if (x.get('EngineCylinders') or '').isdigit() else None, em=em,
                turbo=(x.get('Turbo') or '').lower() == 'yes' or bool(re.search(r'turbo|t-gdi|\btsi\b|tfsi|ecoboost|gtdi', em + ' ' + oth, re.I)),
                diesel='diesel' in fu, electric=fu.strip().startswith('electric'),
                hybrid=bool(re.search(r'hev|hybrid', el)) and not re.search(r'mild|mhev', el), mild=bool(re.search(r'mild|mhev', el)))
def classify(fid, y, x, vin=''):
    """-> engine slug or None: the one engine whose rule this decode fits for this car and model year (two fits = ambiguous = None)"""
    if not x or not x.get('DisplacementL'): return None
    a = facts(x); hits = []
    for e, d in ENG.items():
        if fid not in d['cars'] or not d['cars'][fid][0] <= y <= d['cars'][fid][1]: continue
        r = d['rule']
        if a['disp'] != r['disp'] or a['electric'] or a['diesel'] != bool(r.get('diesel')): continue
        if a['cyl'] is not None and a['cyl'] != r['cyl']: continue
        if r.get('turbo') is True and not a['turbo'] and fid not in r.get('turbo_ok', ()): continue   # turbo_ok: cars sold with no non-turbo engine of this size (vPIC often leaves Turbo blank)
        if r.get('turbo') is False and a['turbo']: continue
        if r.get('hybrid') is False and a['hybrid']: continue
        if r.get('code') and not re.search(r['code'], a['em'], re.I): continue
        if r.get('vin8') and (x.get('vin') or vin)[7:8] not in r['vin8']: continue   # Ford: VIN position 8 is the engine code (T / G = EcoBoost) where vPIC leaves Turbo blank
        hits.append(e)
    return hits[0] if len(hits) == 1 else None

# ---------------------------------------------------------------- 3. recalls (the names each model year's own page queries: 10%+ of its complaints, at most 2)
REC_JS = os.path.join(WORK, 'recalls.json')
def rnames():
    out = {}
    for p in ('extras_local.json', 'extras_local_new.json', 'extras_local_low.json'):
        fp = os.path.join(HERE, 'data', p)
        if not os.path.exists(fp): continue
        for fid, ys in json.load(open(fp, encoding='utf-8')).items():
            if fid not in TARGET: continue
            for y, e in ys.items():
                if int(y) not in TARGET[fid] or not e.get('names'): continue
                tot = sum(n for *_, n in e['names']) or 1
                out[f'{fid}|{y}'] = [(mk, md) for mk, md, n in e['names'] if n / tot >= .10][:2] or [tuple(e['names'][0][:2])]
    return out
def recalls():
    out = {}; N = rnames()
    for k, names in sorted(N.items()):
        y = k.split('|')[1]; seen = {}
        for mk, md in names:
            url = f'https://api.nhtsa.gov/recalls/recallsByVehicle?make={urllib.parse.quote(mk.lower())}&model={urllib.parse.quote(md.lower())}&modelYear={y}'
            for r in (get(url) or {}).get('results', []) or []:
                c = r.get('NHTSACampaignNumber')
                if c and c not in seen and c[2:3] == 'V':   # vehicle recalls only
                    seen[c] = {'id': c, 'date': r.get('ReportReceivedDate', ''), 'part': r.get('Component', ''), 'summary': (r.get('Summary') or '').strip()[:700],
                               'risk': (r.get('Consequence') or '').strip()[:400], 'fix': (r.get('Remedy') or '').strip()[:400]}
        out[k] = list(seen.values())
    json.dump(out, open(REC_JS, 'w', encoding='utf-8'), ensure_ascii=False)
    print('recalls:', len(out), 'model years,', len({r['id'] for v in out.values() for r in v}), 'campaigns')
# a recall names an engine when its summary names the engine (size + the words that tell it from the other engines of that size in these cars)
SZ = lambda s: r'(?<![\d.])' + re.escape(s) + r'\s?-?\s?(l\b|liter|litre)'
REC_RX = {
    'toyota-2gr-fks': (SZ('3.5') + r'|\bv6\b|2gr', r'hybrid'), 'toyota-2gr-fe': (SZ('3.5') + r'|\bv6\b|2gr', r'hybrid'),
    'gm-53-gen5': (SZ('5.3'), None), 'gm-53-gen4': (SZ('5.3'), None), 'gm-62-gen5': (SZ('6.2'), None),
    'hyundai-theta2-24': (SZ('2.4') + r'|theta', r'hybrid'), 'hyundai-theta2-20t': (SZ('2.0') + r'[^.]{0,40}turbo|2\.0t|turbo[^.]{0,30}' + SZ('2.0') + r'|theta', None),
    'honda-j35': (SZ('3.5') + r'|\bv6\b|j35', None), 'ford-35-cyclone': (SZ('3.5') + r'|\bv6\b', r'ecoboost|turbo|gtdi'),
    'ford-ecoboost-15': (SZ('1.5'), None), 'ford-ecoboost-20': (SZ('2.0') + r'[^.]{0,40}(ecoboost|gtdi|turbo)|2\.0l? ecoboost', None),
    'nissan-vq35': (SZ('3.5') + r'|\bv6\b|vq35', None), 'chrysler-36-pentastar': (SZ('3.6') + r'|pentastar', None),
    'chrysler-57-hemi': (SZ('5.7') + r'|hemi', r'6\.4|392|hellcat|6\.2|6\.1'), 'subaru-fb25': (SZ('2.5') + r'|fb25', r'turbo'), 'subaru-fb20': (SZ('2.0') + r'|fb20', r'turbo|hybrid'),
    'mazda-skyactiv-25': (SZ('2.5'), r'turbo'), 'toyota-a25a': (SZ('2.5') + r'|a25a', r'hybrid'), 'toyota-2ar-fe': (SZ('2.5') + r'|2ar', r'hybrid'),
    'vw-ea888': (SZ('2.0') + r'[^.]{0,40}(tsi|tfsi|turbo|gasoline)|2\.0t|ea888|tsi|tfsi', r'tdi|diesel'),
    'ford-ecoboost-23': (SZ('2.3'), None), 'gm-27-turbo': (SZ('2.7'), None), 'gm-14-turbo': (SZ('1.4'), None), 'gm-24-ecotec': (SZ('2.4'), r'eassist|hybrid'),
    'gm-36-v6': (SZ('3.6'), r'twin[- ]turbo'), 'gm-15-turbo': (SZ('1.5'), None), 'ram-30-ecodiesel': (SZ('3.0') + r'[^.]{0,40}diesel|ecodiesel|eco diesel', None),
    'jeep-38-v6': (SZ('3.8'), None), 'gm-48-vortec': (SZ('4.8'), None), 'ford-54-triton': (SZ('5.4'), r'supercharg'), 'honda-15t': (SZ('1.5') + r'[^.]{0,40}turbo|1\.5t', None),
    'honda-k24': (SZ('2.4'), r'hybrid'), 'nissan-qr25': (SZ('2.5'), r'hybrid'), 'toyota-2az-fe': (SZ('2.4') + r'|2az', r'hybrid'), 'toyota-1gr-fe': (SZ('4.0') + r'|1gr', None),
    'toyota-3ur-fe': (SZ('5.7') + r'|3ur', None), 'chrysler-24-tigershark': (SZ('2.4') + r'|tigershark', None), 'hyundai-lambda2-38': (SZ('3.8'), None), 'hyundai-lambda2-33': (SZ('3.3'), None),
}
SIZE_RX = re.compile(r'(?<![\d.])(\d\.\d)\s?-?\s?(?:l\b|liter|litre)', re.I)
def rec_names(e, r):
    s = r['summary']; rx, nrx = REC_RX[e]
    return bool(re.search(rx, s, re.I)) and not (nrx and re.search(nrx, s, re.I))

# ---------------------------------------------------------------- 4. aggregate
PART = {'ELECTRICAL SYSTEM': 'electrical', 'POWER TRAIN': 'transmission & drivetrain', 'SERVICE BRAKES': 'brakes', 'VEHICLE SPEED CONTROL': 'speed control',
        'FUEL/PROPULSION SYSTEM': 'fuel system', 'FUEL SYSTEM': 'fuel system', 'FORWARD COLLISION AVOIDANCE': 'automatic emergency braking', 'VISIBILITY/WIPER': 'wipers & visibility',
        'VISIBILITY': 'visibility', 'AIR BAGS': 'airbags', 'STRUCTURE': 'body structure', 'EXTERIOR LIGHTING': 'lights', 'ENGINE AND ENGINE COOLING': 'engine',
        'ENGINE': 'engine', 'STEERING': 'steering', 'SUSPENSION': 'suspension', 'WHEELS': 'wheels', 'TIRES': 'tires', 'SEATS': 'seats', 'SEAT BELTS': 'seat belts',
        'LATCHES/LOCKS/LINKAGES': 'doors, locks & latches', 'PARKING BRAKE': 'parking brake', 'ELECTRONIC STABILITY CONTROL': 'stability control', 'EQUIPMENT': 'equipment',
        'TRAILER HITCHES': 'trailer hitch', 'BACK OVER PREVENTION': 'backup camera', 'LANE DEPARTURE': 'lane assist', 'HYBRID PROPULSION SYSTEM': 'hybrid system'}
def part(c):
    c = c.split(':')[0].strip()
    if c.startswith('FUEL SYSTEM'): return 'fuel system'
    if c.startswith('ELECTRONIC STABILITY'): return 'stability control'
    if c.startswith('SERVICE BRAKES'): return 'brakes'
    return PART.get(c, c.lower())
# what owners write, counted per complaint (regex on the owner's own words). Labels say exactly what's counted.
WORDS = {
    'oil_use': ('mention burning or losing oil', r'(burn|burning|burns|consum\w*|using|uses|losing|loses|lose) (a lot of |excessive |too much )?(engine )?oil|oil consumption|low oil (level|light)'),
    'oil_leak': ('mention an oil leak', r'oil (leak|pan leak)|leak\w* oil'),
    'seize': ('say the engine knocked, seized or failed', r'knock|seiz|rod bearing|connecting rod|threw a rod|thrown rod|engine (failure|failed|blew|blown|locked)|blown engine|catastrophic engine'),
    'lifter': ('mention a lifter, rocker or ticking', r'lifter|rocker arm|\btick(ing)?\b'),
    'deact': ('mention cylinder deactivation (AFM / DFM / VCM / MDS)', r'\bafm\b|active fuel management|\bdfm\b|dynamic fuel management|cylinder deactivation|\bvcm\b|variable cylinder|\bmds\b|multi[- ]displacement'),
    'timing_chain': ('mention the timing chain', r'timing chain|chain tensioner'),
    'water_pump': ('mention the water pump', r'water pump'),
    'coolant': ('mention coolant loss or overheating', r'coolant|overheat|antifreeze'),
    'head_gasket': ('mention a head gasket', r'head gasket'),
    'misfire': ('mention a misfire', r'misfir'),
    'power_loss': ('say the engine stalled, shut off or lost power', r'\bstall|shut(s|ting)? (off|down)|lost (all )?power|loss of power|loses power|limp|reduced (engine )?power|no power|dies?\b while'),
    'oil_housing': ('mention the oil filter housing or oil cooler', r'oil (filter )?(housing|cooler)|filter housing'),
    'carbon': ('mention carbon buildup', r'carbon (build|deposit)'),
    'turbo': ('mention the turbo', r'turbo'),
    'fire_w': ('mention fire, flames or smoke', r'\bfire\b|flame|smok'),
    'oil_dil': ('mention fuel in the oil (oil dilution)', r'oil dilution|(gas|fuel|gasoline) in (the |my )?(engine )?oil|oil (level )?(is )?(rising|increas|overfull)|oil smell\w* (like|of) (gas|fuel)'),
    'cam_phaser': ('mention a cam phaser or VTC actuator', r'cam ?phaser|phaser|vtc actuator|vtc rattle'),
    'spark_plug': ('mention a spark plug', r'spark ?plug'),
}
WRX = {k: re.compile(p, re.I) for k, (_, p) in WORDS.items()}
def pct(k, n): return round(k / n * 100) if n else 0
def miles_of(rows):
    ms = sorted(int(r['mi']) for r in rows if r['mi'].isdigit() and 0 < int(r['mi']) < 500000)
    return dict(p25=ms[len(ms) // 4], median=ms[len(ms) // 2], p75=ms[len(ms) * 3 // 4], n=len(ms)) if len(ms) >= 20 else None
def comps_of(rows, top=8):
    c = collections.Counter(); n = len(rows)
    for r in rows:
        for p in {part(x) for x in r['comps']} - {'unknown or other'}: c[p] += 1
    return [[p, pct(k, n), k] for p, k in c.most_common(top)]
def words_of(rows):
    n = len(rows); return {k: [sum(1 for r in rows if WRX[k].search(r['d'])), n] for k in WORDS}
def quotes_of(rows, k=3, rx=None):
    qs = [r for r in rows if 80 < len(r['d']) < 300 and (rx is None or rx.search(r['d']))]
    qs.sort(key=lambda r: r['o'], reverse=True)
    return [dict(y=r['y'], odi=r['o'], text=r['d'][0] + r['d'][1:].lower() if r['d'].isupper() else r['d']) for r in qs[:k]]
def serious(rows): return dict(crash=sum(r['cr'] for r in rows), fire=sum(r['fi'] for r in rows), injured=sum(r['inj'] > 0 for r in rows), deaths=sum(r['dth'] > 0 for r in rows), towed=sum(r['tow'] for r in rows))
MIN_N, MIN_YEARS, MIN_YEAR_N = 30, 3, 3   # the site's engine-page bar: supercar_engine_pages charts 30+ complaints over 3+ years; data_hd keeps engine years with 3+

def build():
    R = load(); D = json.load(open(DEC_JS, encoding='utf-8')); RC = json.load(open(REC_JS, encoding='utf-8')) if os.path.exists(REC_JS) else {}
    nm = 0
    for r in R:
        r['eng'] = None; x = D.get(vkey(r))
        if x:
            hits = {classify(f, r['y'], x) for f in r['f']} - {None}
            if len(hits) == 1: r['eng'] = hits.pop(); nm += 1
        r['w3'] = bool(r['ld'][:4].isdigit() and int(r['ld'][:4]) <= r['y'] + 3)
    print('complaints', len(R), 'engine-matched', nm)
    recs = {}; engines = {}; held = {}
    for e, d in ENG.items():
        rows = [r for r in R if r['eng'] == e]
        by = collections.Counter(r['y'] for r in rows)
        yrs = sorted(y for y in by if by[y] >= MIN_YEAR_N)
        rows = [r for r in rows if r['y'] in yrs]
        if len(rows) < MIN_N or len(yrs) < MIN_YEARS:
            held[e] = dict(n=len(rows), years=len(yrs)); print('HELD', e, len(rows), 'complaints,', len(yrs), 'years'); continue
        cy = {}
        for r in rows:
            for f in r['f']:
                if f in d['cars'] and classify(f, r['y'], D.get(vkey(r))) == e: cy.setdefault(f, collections.Counter())[r['y']] += 1
        by_car = {}
        for f, c in cy.items():
            fr = [r for r in rows if f in r['f']]
            by_car[f] = dict(n=sum(c.values()), years={str(y): k for y, k in sorted(c.items())}, eng=pct(sum(1 for r in fr if any(part(x) == 'engine' for x in r['comps'])), len(fr)))
        rl = []
        for f in d['cars']:
            for y in yrs:
                if not cy.get(f, {}).get(y): continue
                for x in RC.get(f'{f}|{y}') or []:
                    if rec_names(e, x):
                        recs.setdefault(x['id'], dict(x, cars={}))['cars'].setdefault(f, [])
                        if y not in recs[x['id']]['cars'][f]: recs[x['id']]['cars'][f].append(y)
                        if x['id'] not in rl: rl.append(x['id'])
        engines[e] = dict({k: v for k, v in d.items() if k not in ('cars', 'rule')}, years=yrs, n=len(rows), by_year={str(y): by[y] for y in yrs}, by_car=by_car,
                          n3=sum(r['w3'] for r in rows), comps=comps_of(rows, 10), words=words_of(rows), miles=miles_of(rows), ser=serious(rows), quotes=quotes_of(rows),
                          recalls=sorted(rl, key=lambda i: recs[i]['date'][6:10] + recs[i]['date'][3:5] + recs[i]['date'][:2], reverse=True),
                          wq={k: quotes_of(rows, 2, WRX[k]) for k in WORDS})
        print(f'{e:24} {len(rows):6} complaints {yrs[0]}-{yrs[-1]} cars {len(by_car)} engine {engines[e]["comps"][0] if engines[e]["comps"] else ""} recalls {len(rl)}', flush=True)
    src = dict(complaints='NHTSA owner complaints (FLAT_CMPL + COMPLAINTS_RECEIVED_2025-2026), received through ' + max(r['ld'] for r in R if r['ld'][:4].isdigit()),
               vin='NHTSA vPIC VIN decoder (batch)', recalls='NHTSA recalls API')
    out = dict(engines=engines, held=held, recalls=recs, words={k: v[0] for k, v in WORDS.items()}, src=src, matched=nm, total=len(R))
    p = os.path.join(HERE, 'data', 'vin_engines.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('written data/vin_engines.json', round(os.path.getsize(p) / 1e6, 2), 'MB')

def audit():
    """per car + model year: what the decodes say and what got matched (to check the rules against the data)"""
    R = load(); D = json.load(open(DEC_JS, encoding='utf-8')); A = collections.defaultdict(collections.Counter)
    for r in R:
        x = D.get(vkey(r))
        for f in r['f']:
            a = facts(x) if x and x.get('DisplacementL') else None
            lab = f'{a["disp"]} {a["cyl"]}cyl{" T" if a["turbo"] else ""}{" HEV" if a["hybrid"] else ""}{" D" if a["diesel"] else ""} [{a["em"][:24]}]' if a else ('undecoded' if not x else 'no displacement')
            A[(f, r['y'])][(lab, classify(f, r['y'], x) if x else None)] += 1
    flt = sys.argv[2] if len(sys.argv) > 2 else ''
    for (f, y), c in sorted(A.items()):
        if flt and flt not in f: continue
        print(f, y, '; '.join(f'{lab} -> {e or "-"} {n}' for (lab, e), n in c.most_common(6)))

if __name__ == '__main__':
    if 'audit' in STAGES: audit(); sys.exit()
    if 'extract' in STAGES: extract()
    if 'decode' in STAGES: decode()
    if 'recalls' in STAGES: recalls()
    if 'build' in STAGES: build()
