// lemon-alerts Worker (11-14, growth plan 4a): "Get an email if your car gets a recall" for lemonindex.com.
// Cloudflare Worker + D1 (binding DB -> database lemon-alerts) + a cron trigger (alerts.toml). Deploy: worker/make_alerts.py, then
// `npx.cmd --yes wrangler deploy -c alerts.toml` from worker/. Schema: alerts_schema.sql (wrangler d1 execute lemon-alerts --remote --file ...).
//
// What it stores, per alert (table subs): the email, the model year, the NHTSA make + model names (max 2, the same ones the site's
// recall lists use), the Lemon page id when we cover the model, a confirm token (cleared once used) and an unsubscribe token, plus
// timestamps and the recall campaign numbers already sent. Never a VIN, never an IP address. A per-day salted IP hash (table hits) only
// caps repeat signups and is deleted after 2 days. Unsubscribing deletes every row for that email.
//
// Double opt-in: nothing but the confirm email goes to an address until its owner taps the confirm link (lemonindex.com/alerts/#c=...).
// Every email carries a one-click unsubscribe (List-Unsubscribe + List-Unsubscribe-Post header -> POST /unsub?t=..., and a link in the body).
//
// Sending is OFF until env SEND_ENABLED = "1" (set once lemonindex.com is verified in Resend). While off, signups are saved as pending
// ("queued") and the cron sends their confirm emails once sending is on; pending rows that never get confirmed are deleted after 30 days.
//
// Routes (CORS: lemonindex.com only, except the one-click unsubscribe, which mail providers POST without an Origin):
//   POST /signup  {email, y, n: [[MAKE, MODEL]], f?, hp, t?}   -> {ok, queued}
//   POST /info    {c} or {u}                                    -> {name, y, url}     (for the /alerts/ page; no email returned)
//   POST /confirm {c}                                           -> {ok, name, url}
//   POST /unsub   {u}  or  POST /unsub?t=<u> (one-click)        -> {ok, n}
//   GET  /unsub?t=<u>                                           -> 302 to lemonindex.com/alerts/#u=<u>
// Cron (*/15): cleanup, queued confirm emails, then up to CARS_PER_RUN cars due for their weekly NHTSA check; new campaigns -> one email
// per subscriber. A daily send cap (DAILY_CAP, Resend's free plan is 100 a day across the account) holds the rest for the next run.
const CARS = {"ford-f-series":"Ford F-Series","chevrolet-silverado":"Chevrolet Silverado","ram-pickup":"Ram pickup","gmc-sierra":"GMC Sierra","toyota-tacoma":"Toyota Tacoma","toyota-tundra":"Toyota Tundra","chevrolet-colorado":"Chevrolet Colorado","nissan-frontier":"Nissan Frontier","honda-ridgeline":"Honda Ridgeline","jeep-gladiator":"Jeep Gladiator","ford-escape":"Ford Escape","ford-explorer":"Ford Explorer","ford-edge":"Ford Edge","ford-expedition":"Ford Expedition","ford-ecosport":"Ford EcoSport","jeep-grand-cherokee":"Jeep Grand Cherokee","jeep-cherokee":"Jeep Cherokee","jeep-wrangler":"Jeep Wrangler","jeep-compass":"Jeep Compass","jeep-renegade":"Jeep Renegade","jeep-patriot":"Jeep Patriot","chevrolet-equinox":"Chevrolet Equinox","chevrolet-traverse":"Chevrolet Traverse","chevrolet-tahoe":"Chevrolet Tahoe","chevrolet-suburban":"Chevrolet Suburban","chevrolet-trax":"Chevrolet Trax","gmc-acadia":"GMC Acadia","gmc-terrain":"GMC Terrain","gmc-yukon":"GMC Yukon","gmc-yukon-xl":"GMC Yukon XL","dodge-durango":"Dodge Durango","dodge-journey":"Dodge Journey","toyota-rav4":"Toyota RAV4","toyota-highlander":"Toyota Highlander","toyota-4runner":"Toyota 4Runner","honda-cr-v":"Honda CR-V","honda-pilot":"Honda Pilot","honda-hr-v":"Honda HR-V","nissan-rogue":"Nissan Rogue","nissan-pathfinder":"Nissan Pathfinder","nissan-murano":"Nissan Murano","hyundai-tucson":"Hyundai Tucson","hyundai-santa-fe":"Hyundai Santa Fe","hyundai-kona":"Hyundai Kona","hyundai-palisade":"Hyundai Palisade","kia-sorento":"Kia Sorento","kia-sportage":"Kia Sportage","kia-soul":"Kia Soul","kia-telluride":"Kia Telluride","subaru-outback":"Subaru Outback","subaru-forester":"Subaru Forester","subaru-crosstrek":"Subaru Crosstrek","subaru-ascent":"Subaru Ascent","mazda-cx-5":"Mazda CX-5","mazda-cx-9":"Mazda CX-9","volkswagen-tiguan":"Volkswagen Tiguan","volkswagen-atlas":"Volkswagen Atlas","lexus-rx":"Lexus RX","acura-mdx":"Acura MDX","acura-rdx":"Acura RDX","toyota-camry":"Toyota Camry","toyota-corolla":"Toyota Corolla","toyota-avalon":"Toyota Avalon","honda-accord":"Honda Accord","honda-civic":"Honda Civic","honda-fit":"Honda Fit","ford-fusion":"Ford Fusion","ford-focus":"Ford Focus","ford-mustang":"Ford Mustang","ford-fiesta":"Ford Fiesta","ford-taurus":"Ford Taurus","chevrolet-malibu":"Chevrolet Malibu","chevrolet-cruze":"Chevrolet Cruze","chevrolet-impala":"Chevrolet Impala","chevrolet-camaro":"Chevrolet Camaro","chevrolet-sonic":"Chevrolet Sonic","chevrolet-spark":"Chevrolet Spark","chevrolet-volt":"Chevrolet Volt","chevrolet-bolt":"Chevrolet Bolt","nissan-altima":"Nissan Altima","nissan-sentra":"Nissan Sentra","nissan-versa":"Nissan Versa","nissan-maxima":"Nissan Maxima","hyundai-sonata":"Hyundai Sonata","hyundai-elantra":"Hyundai Elantra","hyundai-accent":"Hyundai Accent","kia-optima":"Kia Optima","kia-forte":"Kia Forte","kia-rio":"Kia Rio","subaru-impreza":"Subaru Impreza","subaru-legacy":"Subaru Legacy","mazda3":"Mazda3","mazda6":"Mazda6","volkswagen-jetta":"Volkswagen Jetta","volkswagen-passat":"Volkswagen Passat","dodge-charger":"Dodge Charger","dodge-challenger":"Dodge Challenger","dodge-dart":"Dodge Dart","chrysler-200":"Chrysler 200","chrysler-300":"Chrysler 300","lexus-es":"Lexus ES","tesla-model-y":"Tesla Model Y","bmw-3-series":"BMW 3 Series","bmw-5-series":"BMW 5 Series","bmw-x1":"BMW X1","bmw-x3":"BMW X3","bmw-x5":"BMW X5","mercedes-benz-c-class":"Mercedes-Benz C-Class","mercedes-benz-e-class":"Mercedes-Benz E-Class","mercedes-benz-glk/glc":"Mercedes-Benz GLK/GLC","mercedes-benz-m/gle":"Mercedes-Benz M/GLE","mercedes-benz-cla":"Mercedes-Benz CLA","mercedes-benz-gla":"Mercedes-Benz GLA","audi-a3":"Audi A3","audi-a4":"Audi A4","audi-q5":"Audi Q5","audi-q7":"Audi Q7","audi-q3":"Audi Q3","porsche-macan":"Porsche Macan","volkswagen-golf":"Volkswagen Golf","honda-odyssey":"Honda Odyssey","toyota-sienna":"Toyota Sienna","dodge-grand-caravan":"Dodge Grand Caravan","chrysler-town-and-country":"Chrysler Town & Country","chrysler-pacifica":"Chrysler Pacifica","kia-sedona":"Kia Sedona","ford-windstar":"Ford Windstar","toyota-prius":"Toyota Prius","chevrolet-cobalt":"Chevrolet Cobalt","jeep-liberty":"Jeep Liberty","mini-cooper":"Mini Cooper","ford-ranger":"Ford Ranger","chevrolet-corvette":"Chevrolet Corvette","dodge-dakota":"Dodge Dakota","chevrolet-hhr":"Chevrolet HHR","gmc-envoy":"GMC Envoy","nissan-titan":"Nissan Titan","ford-freestyle":"Ford Freestyle","jeep-commander":"Jeep Commander","toyota-sequoia":"Toyota Sequoia","cadillac-srx":"Cadillac SRX","nissan-xterra":"Nissan Xterra","chevrolet-avalanche":"Chevrolet Avalanche","acura-tl":"Acura TL","dodge-avenger":"Dodge Avenger","buick-enclave":"Buick Enclave","saturn-vue":"Saturn Vue","ford-bronco":"Ford Bronco","cadillac-escalade":"Cadillac Escalade","cadillac-cts":"Cadillac CTS","chevrolet-blazer":"Chevrolet Blazer","buick-lacrosse":"Buick LaCrosse","mazda-tribute":"Mazda Tribute","chevrolet-cavalier":"Chevrolet Cavalier","dodge-caliber":"Dodge Caliber","ford-flex":"Ford Flex","nissan-armada":"Nissan Armada","lincoln-mkz":"Lincoln MKZ","lexus-ls":"Lexus LS","mitsubishi-outlander":"Mitsubishi Outlander","lexus-is":"Lexus IS","volvo-xc90":"Volvo XC90","hyundai-genesis":"Hyundai Genesis","dodge-nitro":"Dodge Nitro","gmc-canyon":"GMC Canyon","lincoln-mkx":"Lincoln MKX","ford-bronco-sport":"Ford Bronco Sport","ford-transit":"Ford Transit","hyundai-veloster":"Hyundai Veloster","buick-regal":"Buick Regal","chevrolet-aveo":"Chevrolet Aveo","nissan-quest":"Nissan Quest","honda-element":"Honda Element","volvo-s60":"Volvo S60","audi-a6":"Audi A6","buick-rendezvous":"Buick Rendezvous","mitsubishi-lancer":"Mitsubishi Lancer","mazda-cx-7":"Mazda CX-7","dodge-neon":"Dodge Neon","scion-xb":"Scion xB","ford-crown-victoria":"Ford Crown Victoria","honda-passport":"Honda Passport","lincoln-navigator":"Lincoln Navigator","cadillac-deville":"Cadillac DeVille","volkswagen-cc":"Volkswagen CC","dodge-stratus":"Dodge Stratus","acura-tlx":"Acura TLX","toyota-yaris":"Toyota Yaris","toyota-fj-cruiser":"Toyota FJ Cruiser","chevrolet-express":"Chevrolet Express","buick-encore":"Buick Encore","fiat-500":"Fiat 500","ram-promaster":"Ram ProMaster","acura-tsx":"Acura TSX","buick-century":"Buick Century","buick-verano":"Buick Verano","cadillac-ats":"Cadillac ATS","cadillac-dts":"Cadillac DTS","cadillac-sts":"Cadillac STS","cadillac-xt5":"Cadillac XT5","chevrolet-astro":"Chevrolet Astro","chevrolet-captiva":"Chevrolet Captiva","chevrolet-s-10":"Chevrolet S-10","chevrolet-tracker":"Chevrolet Tracker","chevrolet-uplander":"Chevrolet Uplander","chrysler-300m":"Chrysler 300M","chrysler-concorde":"Chrysler Concorde","ford-c-max":"Ford C-Max","ford-e-series":"Ford E-Series","ford-transit-connect":"Ford Transit Connect","gmc-jimmy":"GMC Jimmy","gmc-sonoma":"GMC Sonoma","honda-insight":"Honda Insight","hyundai-azera":"Hyundai Azera","hyundai-tiburon":"Hyundai Tiburon","infiniti-fx35":"Infiniti FX35","infiniti-g37":"Infiniti G37","infiniti-m35":"Infiniti M35","infiniti-q50":"Infiniti Q50","infiniti-qx60":"Infiniti QX60","jaguar-x-type":"Jaguar X-Type","kia-niro":"Kia Niro","kia-seltos":"Kia Seltos","kia-sephia":"Kia Sephia","lincoln-aviator":"Lincoln Aviator","lincoln-mkc":"Lincoln MKC","lincoln-mks":"Lincoln MKS","mazda-626":"Mazda 626","mazda-mpv":"Mazda MPV","mazda-protege":"Mazda Protege","mazda-mazda5":"Mazda5","mercedes-benz-sprinter":"Mercedes-Benz Sprinter","mitsubishi-galant":"Mitsubishi Galant","mitsubishi-montero":"Mitsubishi Montero","mitsubishi-outlander-sport":"Mitsubishi Outlander Sport","nissan-350z":"Nissan 350Z","nissan-juke":"Nissan Juke","nissan-kicks":"Nissan Kicks","saturn-sl":"Saturn SL","scion-tc":"Scion tC","toyota-c-hr":"Toyota C-HR","toyota-venza":"Toyota Venza","volvo-s40":"Volvo S40","volvo-s80":"Volvo S80","volvo-xc60":"Volvo XC60","hummer-h2":"Hummer H2","hummer-h3":"Hummer H3","land-rover-discovery":"Land Rover Discovery","land-rover-range-rover-sport":"Land Rover Range Rover Sport","mercury-cougar":"Mercury Cougar","oldsmobile-bravada":"Oldsmobile Bravada","oldsmobile-intrigue":"Oldsmobile Intrigue","suzuki-sx4":"Suzuki SX4","tesla-model-s":"Tesla Model S","tesla-model-3":"Tesla Model 3","tesla-model-x":"Tesla Model X"};            // Lemon page id -> model name (assets/cars.json)
const PAIRS = new Set(["ACURA|MDX","ACURA|RDX","ACURA|TL","ACURA|TLX","ACURA|TLXTYPES","ACURA|TSX","AUDI|A3","AUDI|A3CABRIOLET","AUDI|A3ETRON","AUDI|A3SPORTBACKETRON","AUDI|A4","AUDI|A4ALLROAD","AUDI|A4AVANT","AUDI|A4CABRIOLET","AUDI|A6","AUDI|A6ALLROAD","AUDI|ALLROAD","AUDI|Q3","AUDI|Q5","AUDI|Q5E","AUDI|Q5HYBRID","AUDI|Q5SPORTBACK","AUDI|Q7","AUDI|RS3","AUDI|S3","AUDI|S4","AUDI|S6","AUDI|SQ5","AUDI|SQ7","BMW|320I","BMW|323I","BMW|325CI","BMW|325I","BMW|325XI","BMW|328","BMW|328D","BMW|328I","BMW|328IC","BMW|328XI","BMW|330CI","BMW|330E","BMW|330I","BMW|335I","BMW|340I","BMW|3SERIES","BMW|525I","BMW|528","BMW|528I","BMW|528XI","BMW|530","BMW|530E","BMW|530I","BMW|530XI","BMW|535D","BMW|535I","BMW|535XI","BMW|540I","BMW|545I","BMW|550I","BMW|5SERIES","BMW|M3","BMW|M340I","BMW|M5","BMW|M550I","BMW|X1","BMW|X1SAV","BMW|X3","BMW|X3SAV","BMW|X5","BMW|X5DIESELSAV","BMW|X5M","BMW|X5SAV","BUICK|CENTURY","BUICK|ENCLAVE","BUICK|ENCORE","BUICK|LACROSSE","BUICK|REGAL","BUICK|REGALTOURX","BUICK|RENDEZVOUS","BUICK|VERANO","CADILLAC|ATS","CADILLAC|ATSV","CADILLAC|CTS","CADILLAC|CTSV","CADILLAC|DEVILLE","CADILLAC|DTS","CADILLAC|ESCALADE","CADILLAC|ESCALADEESV","CADILLAC|ESCALADEEXT","CADILLAC|ESCALADEHYBRID","CADILLAC|SRX","CADILLAC|STS","CADILLAC|XT5","CHEVROLET|ASTRO","CHEVROLET|AVALANCHE","CHEVROLET|AVALANCHE1500","CHEVROLET|AVALANCHE2500","CHEVROLET|AVEO","CHEVROLET|BLAZER","CHEVROLET|BOLTEUV","CHEVROLET|BOLTEV","CHEVROLET|CAMARO","CHEVROLET|CAPTIVA","CHEVROLET|CAPTIVASPORT","CHEVROLET|CAVALIER","CHEVROLET|COBALT","CHEVROLET|COBALTSS","CHEVROLET|COLORADO","CHEVROLET|CORVETTE","CHEVROLET|CORVETTEZ06","CHEVROLET|CRUZE","CHEVROLET|EQUINOX","CHEVROLET|EXPRESS","CHEVROLET|EXPRESS1500","CHEVROLET|EXPRESS2500","CHEVROLET|EXPRESS3500","CHEVROLET|EXPRESS4500","CHEVROLET|EXPRESSCUTAWAY","CHEVROLET|EXPRESSCUTAWAYVAN","CHEVROLET|HHR","CHEVROLET|IMPALA","CHEVROLET|MALIBU","CHEVROLET|MALIBUCLASSIC","CHEVROLET|MALIBUHYBRID","CHEVROLET|MALIBUMAXX","CHEVROLET|S10","CHEVROLET|SILVERADO","CHEVROLET|SILVERADO1500","CHEVROLET|SILVERADO1500HD","CHEVROLET|SILVERADO2500","CHEVROLET|SILVERADO3500","CHEVROLET|SILVERADOEV","CHEVROLET|SONIC","CHEVROLET|SPARK","CHEVROLET|SPARKEV","CHEVROLET|SUBURBAN","CHEVROLET|SUBURBAN1500","CHEVROLET|SUBURBAN2500","CHEVROLET|TAHOE","CHEVROLET|TAHOEHYBRID","CHEVROLET|TRACKER","CHEVROLET|TRAVERSE","CHEVROLET|TRAX","CHEVROLET|UPLANDER","CHEVROLET|VOLT","CHRYSLER|200","CHRYSLER|300","CHRYSLER|300AWD","CHRYSLER|300C","CHRYSLER|300M","CHRYSLER|CONCORDE","CHRYSLER|PACIFICA","CHRYSLER|PACIFICAAWD","CHRYSLER|PACIFICAPLUGINHYBRID","CHRYSLER|TOWNANDCOUNTRY","CHRYSLER|TOWNANDCOUNTRYLWB","DODGE|AVENGER","DODGE|AVENGERAWD","DODGE|CALIBER","DODGE|CALIBERAWD","DODGE|CARAVAN","DODGE|CHALLENGER","DODGE|CHARGER","DODGE|CHARGERAWD","DODGE|DAKOTA","DODGE|DART","DODGE|DURANGO","DODGE|DURANGO4X4","DODGE|GRANDCARAVAN","DODGE|JOURNEY","DODGE|JOURNEYAWD","DODGE|NEON","DODGE|NEONRT","DODGE|NITRO","DODGE|NITRO4X2","DODGE|NITRO4X4","DODGE|RAM1500","DODGE|RAM2500","DODGE|RAM3500","DODGE|STRATUS","DODGE|STRATUSCOUPE","FIAT|500","FIAT|500E","FORD|BRONCO","FORD|BRONCOSPORT","FORD|CMAX","FORD|CMAXENERGI","FORD|CROWNVICTORIA","FORD|E150","FORD|E250","FORD|E350","FORD|E450","FORD|ECONOLINE","FORD|ECOSPORT","FORD|EDGE","FORD|ESCAPE","FORD|ESCAPEHEV","FORD|ESCAPEHYBRID","FORD|ESCAPEPHEV","FORD|EXPEDITION","FORD|EXPLORER","FORD|EXPLORERHYBRID","FORD|F150","FORD|F150HYBRID","FORD|F150LIGHTNINGBEV","FORD|F250","FORD|F250SD","FORD|F350","FORD|F350SD","FORD|F450","FORD|FIESTA","FORD|FLEX","FORD|FOCUS","FORD|FOCUSELECTRIC","FORD|FOCUSRS","FORD|FREESTYLE","FORD|FUSION","FORD|FUSIONENERGI","FORD|FUSIONHYBRID","FORD|MUSTANG","FORD|MUSTANGCONVERTIBLE","FORD|MUSTANGGT","FORD|RANGER","FORD|TAURUS","FORD|TRANSIT","FORD|TRANSITCONNECT","FORD|TRANSITT350HD","FORD|WINDSTAR","GMC|ACADIA","GMC|CANYON","GMC|ENVOY","GMC|ENVOY360","GMC|ENVOYDENALI","GMC|ENVOYDENALIXL","GMC|ENVOYXL","GMC|ENVOYXL370","GMC|ENVOYXUV","GMC|JIMMY","GMC|SIERRA","GMC|SIERRA1500","GMC|SIERRA1500HD","GMC|SIERRA2500","GMC|SIERRA2500HD","GMC|SIERRA3500","GMC|SIERRADENALI","GMC|SIERRAHD","GMC|SONOMA","GMC|SONOMACREW","GMC|STJIMMY","GMC|TERRAIN","GMC|YUKON","GMC|YUKONDENALI","GMC|YUKONDENALIXL","GMC|YUKONHYBRID","GMC|YUKONXL","GMC|YUKONXL1500","GMC|YUKONXL2500","GMC|YUKONXLDENALI","HONDA|ACCORD","HONDA|ACCORDCROSSTOUR","HONDA|ACCORDHYBRID","HONDA|ACCORDPLUGINHYBRID","HONDA|CIVIC","HONDA|CIVICHYBRID","HONDA|CIVICSI","HONDA|CIVICTYPER","HONDA|CRV","HONDA|CRVHYBRID","HONDA|ELEMENT","HONDA|FIT","HONDA|HRV","HONDA|INSIGHT","HONDA|ODYSSEY","HONDA|PASSPORT","HONDA|PILOT","HONDA|RIDGELINE","HUMMER|H2","HUMMER|H2SUT","HUMMER|H3","HUMMER|H3SUT","HUMMER|HUMMERH3","HYUNDAI|ACCENT","HYUNDAI|AZERA","HYUNDAI|ELANTRA","HYUNDAI|ELANTRACOUPE","HYUNDAI|ELANTRAGT","HYUNDAI|ELANTRAHYBRID","HYUNDAI|ELANTRAN","HYUNDAI|ELANTRATOURING","HYUNDAI|GENESIS","HYUNDAI|KONA","HYUNDAI|PALISADE","HYUNDAI|SANTAFE","HYUNDAI|SANTAFEHYBRID","HYUNDAI|SANTAFESPORT","HYUNDAI|SANTAFEXL","HYUNDAI|SONATA","HYUNDAI|SONATAHYBRID","HYUNDAI|SONATAPLUGINHYBRID","HYUNDAI|TIBURON","HYUNDAI|TUCSON","HYUNDAI|TUCSONHYBRID","HYUNDAI|TUCSONPLUGINHYBRID","HYUNDAI|VELOSTER","HYUNDAI|VELOSTERN","INFINITI|FX","INFINITI|FX35","INFINITI|FX37","INFINITI|FX45","INFINITI|FX50","INFINITI|G25","INFINITI|G37","INFINITI|JX","INFINITI|JX35","INFINITI|M","INFINITI|M35","INFINITI|M35HYBRID","INFINITI|M37","INFINITI|M45","INFINITI|M56","INFINITI|Q50","INFINITI|Q50HYBRID","INFINITI|QX60","INFINITI|QX60HYBRID","JAGUAR|XTYPE","JEEP|CHEROKEE","JEEP|COMMANDER","JEEP|COMMANDER4X2","JEEP|COMMANDER4X4","JEEP|COMPASS","JEEP|COMPASS4X4","JEEP|COMPASSFWD","JEEP|GLADIATOR","JEEP|GRANDCHEROKEE","JEEP|GRANDCHEROKEE4XE","JEEP|GRANDCHEROKEEL","JEEP|LIBERTY","JEEP|PATRIOT","JEEP|PATRIOT4X4","JEEP|PATRIOTFWD","JEEP|RENEGADE","JEEP|WRANGLER","JEEP|WRANGLER2DR4X4","JEEP|WRANGLER2DR4X4RHD","JEEP|WRANGLER4DR4X4","JEEP|WRANGLER4DR4X4RHD","JEEP|WRANGLER4XE","JEEP|WRANGLERSAHARA","KIA|CARNIVAL","KIA|FORTE","KIA|FORTEKOUP","KIA|K5","KIA|NIRO","KIA|NIROEV","KIA|NIROHYBRID","KIA|NIROPHEV","KIA|OPTIMA","KIA|OPTIMAHYBRID","KIA|RIO","KIA|RIOCINCO","KIA|SEDONA","KIA|SEDONAEX","KIA|SELTOS","KIA|SEPHIA","KIA|SORENTO","KIA|SORENTOHYBRID","KIA|SOUL","KIA|SPORTAGE","KIA|TELLURIDE","LANDROVER|DISCOVERY","LANDROVER|DISCOVERYII","LANDROVER|LR3","LANDROVER|LR4","LANDROVER|RANGEROVERSPORT","LEXUS|ES","LEXUS|ES250","LEXUS|ES300","LEXUS|ES300H","LEXUS|ES330","LEXUS|ES350","LEXUS|ESHYBRID","LEXUS|IS","LEXUS|IS250","LEXUS|IS250C","LEXUS|IS300","LEXUS|IS350","LEXUS|IS350C","LEXUS|ISF","LEXUS|LS","LEXUS|LS400","LEXUS|LS430","LEXUS|LS460","LEXUS|LS460L","LEXUS|LS500","LEXUS|LS600HL","LEXUS|LSHYBRID","LEXUS|RX","LEXUS|RX300","LEXUS|RX330","LEXUS|RX350","LEXUS|RX450H","LEXUS|RXHYBRID","LINCOLN|AVIATOR","LINCOLN|AVIATORPHEV","LINCOLN|MKC","LINCOLN|MKS","LINCOLN|MKX","LINCOLN|MKZ","LINCOLN|MKZHYBRID","LINCOLN|NAVIGATOR","MAZDA|626","MAZDA|CX5","MAZDA|CX7","MAZDA|CX9","MAZDA|MAZDA3","MAZDA|MAZDA5","MAZDA|MAZDA6","MAZDA|MPV","MAZDA|PROTEGE","MAZDA|PROTEGE5","MAZDA|TRIBUTE","MAZDA|TRIBUTEHYBRID","MERCEDESBENZ|AMGC43","MERCEDESBENZ|AMGC63","MERCEDESBENZ|AMGCLA35","MERCEDESBENZ|AMGCLA45","MERCEDESBENZ|AMGE53","MERCEDESBENZ|AMGE63","MERCEDESBENZ|AMGGLA35","MERCEDESBENZ|AMGGLA45","MERCEDESBENZ|AMGGLC43","MERCEDESBENZ|AMGGLC63","MERCEDESBENZ|AMGGLE43","MERCEDESBENZ|AMGGLE53","MERCEDESBENZ|AMGGLE63","MERCEDESBENZ|C200","MERCEDESBENZ|C230","MERCEDESBENZ|C240","MERCEDESBENZ|C250","MERCEDESBENZ|C280","MERCEDESBENZ|C300","MERCEDESBENZ|C3004MATIC","MERCEDESBENZ|C320","MERCEDESBENZ|C350","MERCEDESBENZ|C400","MERCEDESBENZ|C450","MERCEDESBENZ|C63","MERCEDESBENZ|CCLASS","MERCEDESBENZ|CLA250","MERCEDESBENZ|E250","MERCEDESBENZ|E300","MERCEDESBENZ|E320","MERCEDESBENZ|E350","MERCEDESBENZ|E3504MATIC","MERCEDESBENZ|E400","MERCEDESBENZ|E4004MATIC","MERCEDESBENZ|E430","MERCEDESBENZ|E450","MERCEDESBENZ|E4504MATIC","MERCEDESBENZ|E500","MERCEDESBENZ|E55","MERCEDESBENZ|E550","MERCEDESBENZ|E63","MERCEDESBENZ|ECLASS","MERCEDESBENZ|GLA250","MERCEDESBENZ|GLC","MERCEDESBENZ|GLC300","MERCEDESBENZ|GLC3004MATIC","MERCEDESBENZ|GLC350E","MERCEDESBENZ|GLE","MERCEDESBENZ|GLE300D","MERCEDESBENZ|GLE350","MERCEDESBENZ|GLE3504MATIC","MERCEDESBENZ|GLE400","MERCEDESBENZ|GLE450","MERCEDESBENZ|GLE4504MATIC","MERCEDESBENZ|GLE550E","MERCEDESBENZ|GLE580","MERCEDESBENZ|GLE5804MATIC","MERCEDESBENZ|GLK250","MERCEDESBENZ|GLK350","MERCEDESBENZ|MCLASS","MERCEDESBENZ|ML250","MERCEDESBENZ|ML320","MERCEDESBENZ|ML350","MERCEDESBENZ|ML430","MERCEDESBENZ|ML500","MERCEDESBENZ|ML55","MERCEDESBENZ|ML550","MERCEDESBENZ|ML63","MERCEDESBENZ|SPRINTER1500","MERCEDESBENZ|SPRINTER2500","MERCEDESBENZ|SPRINTER3500","MERCEDESBENZ|SPRINTER4500","MERCEDESBENZ|SPRINTERVS30","MERCURY|COUGAR","MINI|COOPER","MINI|COOPERCONVERTIBLE","MINI|COOPERS","MINI|COOPERSCONVERTIBLE","MITSUBISHI|GALANT","MITSUBISHI|LANCER","MITSUBISHI|LANCEREVO","MITSUBISHI|LANCEREVOLUTION","MITSUBISHI|LANCERRALIART","MITSUBISHI|LANCERRALLIART","MITSUBISHI|LANCERSPORTBACK","MITSUBISHI|LANCERSPORTSBACK","MITSUBISHI|LANCERWAGON","MITSUBISHI|MONTERO","MITSUBISHI|OUTLANDER","MITSUBISHI|OUTLANDERPHEV","MITSUBISHI|OUTLANDERSPORT","NISSAN|350Z","NISSAN|ALTIMA","NISSAN|ALTIMAHYBRID","NISSAN|ARMADA","NISSAN|FRONTIER","NISSAN|JUKE","NISSAN|KICKS","NISSAN|LEAF","NISSAN|MAXIMA","NISSAN|MURANO","NISSAN|PATHFINDER","NISSAN|QUEST","NISSAN|ROGUE","NISSAN|SENTRA","NISSAN|TITAN","NISSAN|TITANXD","NISSAN|VERSA","NISSAN|VERSANOTE","NISSAN|XTERRA","OLDSMOBILE|BRAVADA","OLDSMOBILE|INTRIGUE","PORSCHE|CAYENNE","PORSCHE|CAYENNEE2","PORSCHE|CAYENNES","PORSCHE|CAYENNESEHYBRID","PORSCHE|CAYENNESHYBRID","PORSCHE|CAYENNETURBO","PORSCHE|MACAN","PORSCHE|MACANGTS","PORSCHE|MACANS","PORSCHE|MACANTURBO","RAM|1500","RAM|2500","RAM|3500","RAM|PROMASTER","RAM|PROMASTER1500","RAM|PROMASTER2500","RAM|PROMASTER3500","SATURN|SC","SATURN|SC1","SATURN|SL","SATURN|SSERIESCOUPE","SATURN|SSERIESSEDAN","SATURN|SW","SATURN|VUE","SATURN|VUEHYBRID","SCION|TC","SCION|XB","SUBARU|ASCENT","SUBARU|CROSSTREK","SUBARU|CROSSTREKHYBRID","SUBARU|FORESTER","SUBARU|IMPREZA","SUBARU|IMPREZASTI","SUBARU|IMPREZAWRX","SUBARU|LEGACY","SUBARU|OUTBACK","SUBARU|WRX","SUBARU|WRXSTI","SUBARU|XVCROSSTREK","SUBARU|XVCROSSTREKHYBRID","SUZUKI|SX4","TESLA|MODEL3","TESLA|MODELS","TESLA|MODELX","TESLA|MODELY","TOYOTA|4RUNNER","TOYOTA|AVALON","TOYOTA|AVALONHYBRID","TOYOTA|CAMRY","TOYOTA|CAMRYHYBRID","TOYOTA|CAMRYSOLARA","TOYOTA|CHR","TOYOTA|COROLLA","TOYOTA|COROLLAHATCHBACK","TOYOTA|COROLLAHYBRID","TOYOTA|COROLLAIM","TOYOTA|FJCRUISER","TOYOTA|HIGHLANDER","TOYOTA|HIGHLANDERHYBRID","TOYOTA|PRIUS","TOYOTA|PRIUSC","TOYOTA|PRIUSPRIME","TOYOTA|PRIUSV","TOYOTA|RAV4","TOYOTA|RAV4EV","TOYOTA|RAV4HYBRID","TOYOTA|RAV4PRIME","TOYOTA|SEQUOIA","TOYOTA|SEQUOIAHYBRID","TOYOTA|SEQUOIASR5","TOYOTA|SIENNA","TOYOTA|TACOMA","TOYOTA|TUNDRA","TOYOTA|VENZA","TOYOTA|VENZAHYBRID","TOYOTA|YARIS","TOYOTA|YARISHB","VOLKSWAGEN|ATLAS","VOLKSWAGEN|ATLASCROSSSPORT","VOLKSWAGEN|CC","VOLKSWAGEN|EGOLF","VOLKSWAGEN|GOLF","VOLKSWAGEN|GOLFALLTRACK","VOLKSWAGEN|GOLFR","VOLKSWAGEN|GOLFSPORTWAGEN","VOLKSWAGEN|GTI","VOLKSWAGEN|JETTA","VOLKSWAGEN|JETTAGLI","VOLKSWAGEN|JETTAHYBRID","VOLKSWAGEN|JETTASPORTWAGEN","VOLKSWAGEN|PASSAT","VOLKSWAGEN|PASSATWAGON","VOLKSWAGEN|TIGUAN","VOLVO|S40","VOLVO|S40N","VOLVO|S60","VOLVO|S80","VOLVO|XC60","VOLVO|XC90"]); // NHTSA "MAKE|MODEL" pairs our pages use (data/extras_local*.json), letters and digits only
const SITE = 'https://lemonindex.com', SELF = 'https://lemon-alerts.elift08.workers.dev';
const ORIGINS = [SITE, 'https://www.lemonindex.com'];
const ADDRESS = 'The Lemon Index · Westbrook Software LLC · 4539 N 22nd St Ste R, Phoenix, AZ 85016';
const DAY = 864e5, WEEK = 7 * DAY, CARS_PER_RUN = 4, MAX_CARS_PER_EMAIL = 5;

const cors = o => ({ 'Access-Control-Allow-Origin': ORIGINS.includes(o) ? o : SITE, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' });
const json = (o, body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...cors(o) } });
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const norm = s => String(s || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
const tok = () => { const b = crypto.getRandomValues(new Uint8Array(24)); return btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
const tokOk = t => typeof t === 'string' && /^[A-Za-z0-9_-]{32}$/.test(t);
const on = env => env.SEND_ENABLED === '1' && !!env.RESEND_KEY;
const cap = env => +(env.DAILY_CAP || 80);
const today = () => new Date().toISOString().slice(0, 10);
async function sha(s) { const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)); return [...new Uint8Array(h)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join(''); }

// "HONDA" "CR-V" -> "Honda CR-V": words with a digit or hyphen, and short ones, stay as NHTSA writes them
const MAKES = { 'MERCEDES-BENZ': 'Mercedes-Benz', 'ALFA ROMEO': 'Alfa Romeo', 'LAND ROVER': 'Land Rover', 'ASTON MARTIN': 'Aston Martin', BMW: 'BMW', GMC: 'GMC', MINI: 'MINI', KIA: 'Kia', RAM: 'Ram', VOLKSWAGEN: 'Volkswagen' };
const tc = w => /\d|-/.test(w) || w.length <= 3 ? w : w[0] + w.slice(1).toLowerCase();
const carName = (y, names, fid) => CARS[fid] ? `${y} ${CARS[fid]}` : `${y} ${MAKES[names[0][0]] || names[0][0].split(' ').map(tc).join(' ')} ${names[0][1].split(' ').map(tc).join(' ')}`;
const carUrl = (y, fid) => CARS[fid] ? `${SITE}/cars/${fid}/${y}/` : `${SITE}/vin/`;
const nhtsaUrl = (y, names) => `https://www.nhtsa.gov/vehicle/${y}/${encodeURIComponent(names[0][0])}/${encodeURIComponent(names[0][1])}`;

// every NHTSA recall campaign for a model year (up to 2 make/model names, the way the site's recall lists are built)
async function recallsFor(y, names) {
  const out = {};
  for (const [mk, md] of names) {
    const r = await fetch(`https://api.nhtsa.gov/recalls/recallsByVehicle?make=${encodeURIComponent(mk)}&model=${encodeURIComponent(md)}&modelYear=${y}`, { headers: { 'User-Agent': 'lemonindex.com recall alerts' } });
    if (!r.ok) throw new Error('nhtsa ' + r.status);
    for (const x of ((await r.json()).results || [])) {
      const id = x.NHTSACampaignNumber; if (!id || out[id]) continue;
      out[id] = { id, part: String(x.Component || 'Recall').split(':')[0], date: x.ReportReceivedDate || '', summary: x.Summary || '', remedy: x.Remedy || '' };
    }
  }
  return out;
}

async function send(env, msgs) {   // msgs: [{to, subject, html, text, unsub?}] -> true when Resend accepted them all
  if (!msgs.length) return true;
  const day = today();
  const used = (await env.DB.prepare('SELECT n FROM sends WHERE day = ?').bind(day).first('n')) || 0;
  if (used + msgs.length > cap(env)) return false;
  const body = msgs.map(m => ({ from: env.FROM || 'Lemon Index <recalls@lemonindex.com>', to: [m.to], subject: m.subject, html: m.html, text: m.text,
    reply_to: env.REPLY_TO || 'hello@elijahwestbrook.com',
    ...(m.unsub ? { headers: { 'List-Unsubscribe': `<${SELF}/unsub?t=${m.unsub}>`, 'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click' } } : {}) }));
  const r = await fetch(body.length === 1 ? 'https://api.resend.com/emails' : 'https://api.resend.com/emails/batch', { method: 'POST',
    headers: { Authorization: `Bearer ${env.RESEND_KEY}`, 'Content-Type': 'application/json' }, body: JSON.stringify(body.length === 1 ? body[0] : body) });
  if (!r.ok) { console.log('resend', r.status, (await r.text()).slice(0, 300)); return false; }
  console.log('resend ok', msgs.length, (await r.text()).slice(0, 300));   // email ids only, never addresses
  await env.DB.prepare('INSERT INTO sends (day, n) VALUES (?, ?) ON CONFLICT(day) DO UPDATE SET n = n + excluded.n').bind(day, msgs.length).run();
  return true;
}

// ---- emails: plain, light, one action each
const shell = (inner, foot) => `<!doctype html><html><body style="margin:0;background:#f5f5f7"><div style="max-width:560px;margin:0 auto;padding:28px 18px;font:16px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#1d1d1f">
<p style="margin:0 0 18px;font-weight:700;font-size:15px">The Lemon Index</p><div style="background:#fff;border-radius:18px;padding:24px 22px">${inner}</div>
<p style="margin:18px 4px 0;font-size:13px;line-height:1.5;color:#6e6e73">${foot}</p></div></body></html>`;
const btn = (href, label) => `<p style="margin:22px 0 6px"><a href="${esc(href)}" style="display:inline-block;background:#1d1d1f;color:#fff;text-decoration:none;font-weight:700;border-radius:999px;padding:12px 24px">${esc(label)}</a></p>`;
function confirmMail(row) {
  const names = JSON.parse(row.car), name = carName(row.y, names, row.fid), link = `${SITE}/alerts/#c=${row.ctok}`;
  return { to: row.email, subject: `Confirm recall alerts for your ${name}`,
    html: shell(`<h1 style="margin:0 0 10px;font-size:22px;line-height:1.25">Confirm recall alerts for the ${esc(name)}</h1>
<p style="margin:0">Tap the button to start. We check the U.S. government&#39;s (NHTSA) recall list every week and email you only when a new recall is added for this model year.</p>${btn(link, 'Yes, send me recall alerts')}
<p style="margin:14px 0 0;font-size:14px;color:#6e6e73">Didn&#39;t ask for this? Ignore this email and nothing else will be sent. The link works for 7 days.</p>`,
      `You got this because someone entered this address for recall alerts on lemonindex.com.<br>${esc(ADDRESS)}`),
    text: `Confirm recall alerts for the ${name}\n\nOpen this link to start: ${link}\n\nWe check NHTSA's recall list every week and email you only when a new recall is added for this model year.\nDidn't ask for this? Ignore this email and nothing else will be sent. The link works for 7 days.\n\n${ADDRESS}` };
}
const sentence = (s, n = 320) => { s = String(s || '').replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n - 20).replace(/\s\S*$/, '') + '…' : s; };
// the defect in plain words: drop NHTSA's "X is recalling certain 2013-2023 ... vehicles." opener (same idea as rsum() in build.py)
const defect = s => { s = String(s || '').replace(/\s+/g, ' ').trim(); const t = s.replace(/^.*?\brecalling\b.*?\b(vehicles|trucks|pick-ups|pickups|cars|SUVs|equipment|tires|seats|motorcycles)\b(?:[^.]|\.(?=\d))*?(?<!\bCo)(?<!\bInc)\.(?!\d)\s*/i, ''); return sentence(t.length >= 25 ? t : s); };
const first = s => sentence((String(s || '').replace(/\s+/g, ' ').trim().match(/^.*?[a-z)]\.(?=\s|$)/) || [String(s || '')])[0], 220);
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const usDate = d => { const m = String(d || '').match(/^(\d{2})\/(\d{2})\/(\d{4})/); return m ? `${MON[+m[2] - 1]} ${+m[1]}, ${m[3]}` : ''; };
function recallMail(row, recs) {
  const names = JSON.parse(row.car), name = carName(row.y, names, row.fid), page = carUrl(row.y, row.fid), un = `${SITE}/alerts/#u=${row.utok}`;
  const part = p => p.toLowerCase().replace(/\b\w/, c => c.toUpperCase());
  const subject = recs.length === 1 ? `New recall: ${name} (${part(recs[0].part).slice(0, 40)})` : `${recs.length} new recalls: ${name}`;
  const items = recs.map(r => `<div style="border-top:1px solid #e5e5ea;padding:16px 0 4px"><p style="margin:0 0 4px;font-weight:700">${esc(part(r.part))}</p>
<p style="margin:0 0 8px;font-size:13px;color:#6e6e73">NHTSA campaign <a href="https://www.nhtsa.gov/recalls?nhtsaId=${esc(r.id)}" style="color:#0066cc">${esc(r.id)}</a>${usDate(r.date) ? ' · issued ' + esc(usDate(r.date)) : ''}</p>
<p style="margin:0 0 8px">${esc(defect(r.summary))}</p>${r.remedy ? `<p style="margin:0 0 8px"><b>Free fix:</b> ${esc(first(r.remedy))}</p>` : ''}</div>`).join('');
  return { to: row.email, unsub: row.utok, subject,
    html: shell(`<h1 style="margin:0 0 10px;font-size:22px;line-height:1.25">${recs.length === 1 ? 'A new recall' : recs.length + ' new recalls'} for the ${esc(name)}</h1>
<p style="margin:0 0 6px">NHTSA added ${recs.length === 1 ? 'this safety recall' : 'these safety recalls'} for the ${esc(name)}. A recall can cover some or all cars of a model year, so check whether it&#39;s open on yours with its VIN. Recall repairs are free at any dealer.</p>${items}
${btn('https://www.nhtsa.gov/recalls', 'Check your VIN at nhtsa.gov')}<p style="margin:10px 0 0;font-size:15px"><a href="${esc(page)}" style="color:#0066cc">Every recall and problem for the ${esc(name)} on Lemon Index</a> · <a href="${esc(nhtsaUrl(row.y, names))}" style="color:#0066cc">NHTSA&#39;s page for it</a></p>`,
      `You get this because you asked for recall alerts for the ${esc(name)} on lemonindex.com. <a href="${esc(un)}" style="color:#6e6e73">Unsubscribe</a> (one click, deletes your email).<br>${esc(ADDRESS)}`),
    text: `${recs.length === 1 ? 'A new recall' : recs.length + ' new recalls'} for the ${name}\n\nNHTSA added ${recs.length === 1 ? 'this safety recall' : 'these safety recalls'}. A recall can cover some or all cars of a model year, so check whether it's open on yours with its VIN at https://www.nhtsa.gov/recalls. Recall repairs are free at any dealer.\n\n`
      + recs.map(r => `${part(r.part)} (NHTSA ${r.id}${usDate(r.date) ? ', issued ' + usDate(r.date) : ''})\n${defect(r.summary)}${r.remedy ? '\nFree fix: ' + first(r.remedy) : ''}\nhttps://www.nhtsa.gov/recalls?nhtsaId=${r.id}`).join('\n\n')
      + `\n\nOn Lemon Index: ${page}\n\nUnsubscribe (deletes your email): ${un}\n${ADDRESS}` };
}

// ---- the 15-minute job
async function run(env) {
  const now = Date.now(), DB = env.DB;
  await DB.batch([
    DB.prepare("DELETE FROM subs WHERE status = 'pending' AND ((conf_sent IS NULL AND created < ?) OR (conf_sent IS NOT NULL AND conf_sent < ?))").bind(now - 30 * DAY, now - WEEK),
    DB.prepare('DELETE FROM hits WHERE day < ?').bind(new Date(now - 2 * DAY).toISOString().slice(0, 10)),
    DB.prepare('DELETE FROM sends WHERE day < ?').bind(new Date(now - 40 * DAY).toISOString().slice(0, 10))]);
  if (!on(env)) return { off: true };
  // 1. confirm emails for signups saved while sending was off
  const q = (await DB.prepare("SELECT * FROM subs WHERE status = 'pending' AND conf_sent IS NULL ORDER BY id LIMIT 40").all()).results;
  if (q.length && await send(env, q.map(confirmMail)))
    await DB.batch(q.map(r => DB.prepare('UPDATE subs SET conf_sent = ?, conf_n = conf_n + 1 WHERE id = ?').bind(now, r.id)));
  // 2. weekly recall check, a few cars per run
  const due = (await DB.prepare("SELECT y, car FROM subs WHERE status = 'active' AND (checked IS NULL OR checked < ?) GROUP BY y, car ORDER BY MIN(COALESCE(checked, 0)) LIMIT ?").bind(now - WEEK, CARS_PER_RUN).all()).results;
  let mailed = 0, checked = 0;
  for (const c of due) {
    let recs; try { recs = await recallsFor(c.y, JSON.parse(c.car)); } catch (e) { console.log('nhtsa failed', c.y, c.car, String(e)); continue; }
    const ids = Object.keys(recs), subs = (await DB.prepare("SELECT * FROM subs WHERE status = 'active' AND y = ? AND car = ?").bind(c.y, c.car).all()).results;
    const quiet = [], mails = [];
    for (const s of subs) {
      if (s.seen == null) { quiet.push(DB.prepare('UPDATE subs SET seen = ?, checked = ? WHERE id = ?').bind(JSON.stringify(ids), now, s.id)); continue; }
      const seen = new Set(JSON.parse(s.seen)), fresh = ids.filter(i => !seen.has(i));
      if (!fresh.length) { quiet.push(DB.prepare('UPDATE subs SET checked = ? WHERE id = ?').bind(now, s.id)); continue; }
      mails.push([s, recallMail(s, fresh.map(i => recs[i]))]);
    }
    if (quiet.length) await DB.batch(quiet);
    if (mails.length) {
      if (!(await send(env, mails.map(m => m[1])))) break;   // over the daily cap or Resend said no: these stay due for the next run
      await DB.batch(mails.map(([s]) => DB.prepare('UPDATE subs SET seen = ?, checked = ? WHERE id = ?').bind(JSON.stringify([...new Set([...JSON.parse(s.seen), ...ids])]), now, s.id)));
      mailed += mails.length;
    }
    checked++;
  }
  return { queued: q.length, checked, mailed };
}

async function realCar(y, names) {   // names our pages use pass straight away; anything else (a decoded VIN) must be a vPIC model for that year
  if (names.every(([mk, md]) => PAIRS.has(norm(mk) + '|' + norm(md)))) return true;
  if (names.length !== 1) return false;
  const [mk, md] = names[0];
  try {
    const r = await fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/${encodeURIComponent(mk)}/modelyear/${y}?format=json`);
    return r.ok && ((await r.json()).Results || []).some(m => norm(m.Model_Name) === norm(md));
  } catch (e) { return false; }
}

export default {
  async scheduled(ev, env, ctx) { ctx.waitUntil(run(env).then(r => console.log('run', JSON.stringify(r)))); },
  async fetch(req, env, ctx) {
    const o = req.headers.get('Origin') || '', url = new URL(req.url), DB = env.DB, now = Date.now();
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(o) });
    // one-click unsubscribe (RFC 8058): Gmail/Yahoo POST here with no Origin; a browser opening the header link gets the page
    if (url.pathname === '/unsub' && url.searchParams.has('t')) {
      const t = url.searchParams.get('t');
      if (req.method === 'GET') return Response.redirect(`${SITE}/alerts/#u=${tokOk(t) ? t : ''}`, 302);
      if (req.method === 'POST' && !o) {
        if (tokOk(t)) { const e = await DB.prepare('SELECT email FROM subs WHERE utok = ?').bind(t).first('email'); if (e) await DB.prepare('DELETE FROM subs WHERE email = ?').bind(e).run(); }
        return new Response('Unsubscribed', { headers: { 'Content-Type': 'text/plain' } });
      }
    }
    if (!ORIGINS.includes(o)) return json(o, { error: 'origin' }, 403);
    if (req.method !== 'POST') return json(o, { error: 'not found' }, 404);
    let b; try { b = await req.json(); } catch { return json(o, { error: 'bad' }, 400); }
    const ip = req.headers.get('CF-Connecting-IP') || '';
    if (env.RL && !(await env.RL.limit({ key: url.pathname + ip })).success) return json(o, { error: 'limit' }, 429);

    if (url.pathname === '/signup') {
      if (b.hp) return json(o, { ok: true, queued: !on(env) });                            // honeypot: only bots fill it in
      const email = typeof b.email === 'string' ? b.email.trim().toLowerCase() : '', y = +b.y, maxY = new Date().getUTCFullYear() + 2;
      const names = Array.isArray(b.n) ? b.n.slice(0, 2).map(p => Array.isArray(p) ? [String(p[0] || '').trim().toUpperCase(), String(p[1] || '').trim().toUpperCase()] : null) : [];
      if (!/^[^@\s"<>]{1,64}@[a-z0-9.-]+\.[a-z]{2,}$/.test(email) || email.length > 200) return json(o, { error: 'email' }, 400);
      if (!Number.isInteger(y) || y < 1981 || y > maxY || !names.length || names.some(p => !p || !/^[A-Z0-9][A-Z0-9 .&\/-]{0,39}$/.test(p[0]) || !/^[A-Z0-9][A-Z0-9 .&\/+()-]{0,49}$/.test(p[1]))) return json(o, { error: 'bad' }, 400);
      if (env.TURNSTILE_SECRET) {
        const fd = new FormData(); fd.append('secret', env.TURNSTILE_SECRET); fd.append('response', String(b.t || '')); fd.append('remoteip', ip);
        const ok = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: fd }).then(r => r.json()).then(j => j.success).catch(() => false);
        if (!ok) return json(o, { error: 'human' }, 403);
      }
      const day = today(), ih = await sha(`${ip}|${day}|${env.SALT || 'lemon-alerts'}|alerts`);
      const hits = (await DB.prepare('INSERT INTO hits (ih, day, n) VALUES (?, ?, 1) ON CONFLICT(ih, day) DO UPDATE SET n = n + 1 RETURNING n').bind(ih, day).first('n')) || 1;
      if (hits > 10) return json(o, { error: 'limit' }, 429);                               // 10 signups per visitor per day
      if (((await DB.prepare('SELECT COUNT(*) n FROM subs WHERE created >= ?').bind(now - DAY).first('n')) || 0) >= 500) return json(o, { error: 'limit' }, 429);   // flood guard
      if (!(await realCar(y, names))) return json(o, { error: 'car' }, 400);
      const fid = typeof b.f === 'string' && CARS[b.f] ? b.f : null, car = JSON.stringify(names);
      let row = await DB.prepare('SELECT * FROM subs WHERE email = ? AND y = ? AND car = ?').bind(email, y, car).first();
      if (row && row.status === 'active') return json(o, { ok: true, queued: false });     // already on: same answer, no email
      if (!row) {
        if (((await DB.prepare('SELECT COUNT(*) n FROM subs WHERE email = ?').bind(email).first('n')) || 0) >= MAX_CARS_PER_EMAIL) return json(o, { error: 'max' }, 400);
        const ut = (await DB.prepare('SELECT utok FROM subs WHERE email = ? LIMIT 1').bind(email).first('utok')) || tok();   // one unsubscribe token per address
        row = await DB.prepare("INSERT INTO subs (email, y, car, fid, status, ctok, utok, created) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?) RETURNING *").bind(email, y, car, fid, tok(), ut, now).first();
      }
      if (!on(env)) return json(o, { ok: true, queued: true });
      // a pending signup gets at most 3 confirm emails, 10+ minutes apart
      if (row.conf_n < 3 && (!row.conf_sent || now - row.conf_sent > 6e5)) {
        if (!row.ctok) row.ctok = tok();
        if (!(await send(env, [confirmMail(row)]))) return json(o, { error: 'busy' }, 503);
        await DB.prepare('UPDATE subs SET ctok = ?, conf_sent = ?, conf_n = conf_n + 1 WHERE id = ?').bind(row.ctok, now, row.id).run();
      }
      return json(o, { ok: true, queued: false });
    }
    if (url.pathname === '/info') {
      const r = tokOk(b.c) ? await DB.prepare("SELECT y, car, fid FROM subs WHERE ctok = ? AND status = 'pending'").bind(b.c).first()
        : tokOk(b.u) ? await DB.prepare('SELECT y, car, fid FROM subs WHERE utok = ? LIMIT 1').bind(b.u).first() : null;
      if (!r) return json(o, { error: 'gone' }, 404);
      return json(o, { name: carName(r.y, JSON.parse(r.car), r.fid), y: r.y, url: carUrl(r.y, r.fid) });
    }
    if (url.pathname === '/confirm') {
      if (!tokOk(b.c)) return json(o, { error: 'gone' }, 404);
      const r = await DB.prepare("SELECT * FROM subs WHERE ctok = ? AND status = 'pending' AND conf_sent > ?").bind(b.c, now - WEEK).first();
      if (!r) return json(o, { error: 'gone' }, 404);
      let seen = null; try { seen = JSON.stringify(Object.keys(await recallsFor(r.y, JSON.parse(r.car)))); } catch (e) { /* the cron sets the baseline */ }
      await DB.prepare("UPDATE subs SET status = 'active', ctok = NULL, confirmed = ?, seen = ?, checked = ? WHERE id = ?").bind(now, seen, seen ? now : null, r.id).run();
      return json(o, { ok: true, name: carName(r.y, JSON.parse(r.car), r.fid), url: carUrl(r.y, r.fid), n: seen ? JSON.parse(seen).length : null });
    }
    if (url.pathname === '/unsub') {
      if (!tokOk(b.u)) return json(o, { error: 'gone' }, 404);
      const e = await DB.prepare('SELECT email FROM subs WHERE utok = ?').bind(b.u).first('email');
      if (!e) return json(o, { ok: true, n: 0 });
      const res = await DB.prepare('DELETE FROM subs WHERE email = ?').bind(e).run();
      return json(o, { ok: true, n: res.meta?.changes || 0 });
    }
    return json(o, { error: 'not found' }, 404);
  }
};
