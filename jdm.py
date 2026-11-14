# 11-13 JDM section (Elijah: "add jdm section to site asap and first cars are the fast and furious main cars from 1 and 2 and generate
# images for them and spec/engine stats etc kinda like supercar or performance cars are set up"). Shared lists for:
#   - perf_page.py: each car is a performance-template page (data/perf/<slug>.json with jdm: true, films, us; page /jdm/<slug>/)
#   - supercar_engine_pages.py / engine_more.py: the JDM engine pages, built from those files only (ENG_PERF_ONLY), kicker "JDM"
#   - vin_engine_pages.py: each engine page's YouTube study (3 Lemon Index/data/yt/engine_studies_jdm.py) -> its page (VE_YT)
#   - jdm_pages.py: the /jdm/ hub
# Film facts live in the car files (sourced). This file holds no numbers.
FILMS = [('The Fast and the Furious (2001)', ['toyota-supra-mk4', 'mazda-rx-7-fd', 'mitsubishi-eclipse-2g', 'nissan-skyline-gt-r-r33', 'nissan-240sx-s14',
                                              'nissan-maxima-a32', 'honda-s2000', 'acura-integra-gs-r', 'honda-civic-coupe-ej']),
         ('2 Fast 2 Furious (2003)', ['nissan-skyline-gt-r-r34', 'mitsubishi-lancer-evolution-vii', 'mitsubishi-eclipse-spyder-gts', 'honda-s2000',
                                      'toyota-supra-mk4', 'mazda-rx-7-fd', 'acura-nsx-na1'])]
CARS = list(dict.fromkeys(s for _, ss in FILMS for s in ss))
# engine page -> (name, make, used in other cars this site doesn't cover yet, YouTube study id)
ENGINES = {
 '/engines/toyota-2jz/': ('Toyota 2JZ-GTE / 2JZ-GE', 'Toyota', True, 'toyota-2jz'),
 '/engines/nissan-rb26dett/': ('Nissan RB26DETT', 'Nissan', True, 'nissan-rb26dett'),
 '/engines/mazda-13b-rew/': ('Mazda 13B-REW rotary', 'Mazda', False, 'mazda-13b-rew'),
 '/engines/honda-c30a-c32b/': ('Honda C30A / C32B V6', 'Acura', False, 'honda-c30a-c32b'),
 '/engines/honda-b18c/': ('Honda B18C1 / B18C5', 'Acura', True, 'honda-b18c'),
 '/engines/nissan-ka24de/': ('Nissan KA24DE', 'Nissan', True, 'nissan-ka24de'),
 '/engines/mitsubishi-6g72/': ('Mitsubishi 6G72 3.0 V6', 'Mitsubishi', True, 'mitsubishi-6g72'),
 '/engines/nissan-vq30de/': ('Nissan VQ30DE', 'Nissan', True, 'nissan-vq30de'),
 '/engines/honda-d16z6/': ('Honda D16Z6', 'Honda', True, 'honda-d16z6'),
}
YT = {v[3]: u for u, v in ENGINES.items()}
# engine pages the JDM cars share with pages built elsewhere (listed on the hub, not rebuilt here)
SHARED = {'/engines/mitsubishi-4g63t/': 'Mitsubishi 4G63T', '/engines/honda-f20c/': 'Honda F20C / F22C1'}
