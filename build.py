# Builds lemonindex.com into docs/ (GitHub Pages serves main /docs).   usage: py build.py
# Pages: home, /studies/, /studies/most-reliable-cars/, /method/, 404 + sitemap.xml, robots.txt, llms.txt, CNAME.
# Look = the channel's thumbnails: white, Inter, #111 type, lemon yellow #ffd400 for the brand, red #e8141c only for "bad" (the lemon end).
# Every number comes from 3 Lemon Index/video 1 most reliable/findings.md (NHTSA complaints ÷ US sales, model years 2010-2022).
import os, json, html, datetime, shutil
OUT = 'docs'; TODAY = datetime.date.today().isoformat(); BASE = 'https://lemonindex.com'
E = lambda s: html.escape(str(s), quote=True)
YT, TT, IG = 'https://www.youtube.com/@lemonindex', 'https://www.tiktok.com/@lemonindex', 'https://www.instagram.com/lemonindex/'
CF = 'b04082d02f994049b6b6e0f5aa631ff4'   # Cloudflare Web Analytics (cookieless) token for lemonindex.com, added 10-21

BEST = [('Toyota 4Runner', 27, '1.27M'), ('Lexus ES', 28, '0.70M'), ('Porsche Macan', 31, '0.17M'), ('Lexus RX', 32, '1.34M'), ('Nissan Frontier', 37, '0.83M'),
        ('BMW 3 Series', 37, '1.24M'), ('Honda HR-V', 41, '0.74M'), ('Hyundai Accent', 42, '0.59M'), ('Toyota Tacoma', 44, '2.47M'), ('Mercedes E-Class', 45, '')]
WORST = [('Tesla Model S*', 430, 'suspension 34%, steering 16%'), ('Chevrolet Bolt', 410, 'electrical 54% (battery-fire recall)'), ('Tesla Model X*', 405, 'suspension 27%'),
         ('Tesla Model Y*', 360, 'forward collision avoidance 85% (phantom braking)'), ('Jeep Cherokee (2014+)', 307, 'power train 47%'),
         ('Chrysler Pacifica (2017+)', 281, 'engine 36%, electrical 35%'), ('Chrysler 200', 261, 'electrical, power train'), ('Chevrolet Volt', 261, 'electrical, power train'),
         ('Kia Telluride', 256, 'wipers and visibility 28%'), ('Hyundai Palisade', 249, 'wipers and visibility 25%')]
BRANDS = [('Lexus', 30), ('Porsche*', 34), ('Toyota', 50), ('BMW', 52), ('Mercedes-Benz', 54), ('Nissan', 66), ('Mazda', 66), ('Chevrolet', 70), ('Audi', 74), ('GMC', 86),
          ('Honda', 87), ('Kia', 89), ('Acura', 91), ('Hyundai', 109), ('Ram', 120), ('Dodge', 132), ('Volkswagen', 139), ('Subaru', 143), ('Ford', 144), ('Jeep', 196),
          ('Chrysler', 215), ('Tesla*', 322)]
SEGMENTS = [('Cars', 'Lexus ES 28 · BMW 3 Series 37 · Hyundai Accent 42', 'Tesla Model S 430 · Chevrolet Bolt 410 · Chrysler 200 261'),
            ('SUVs', 'Toyota 4Runner 27 · Porsche Macan 31 · Lexus RX 32', 'Tesla Model X 405 · Tesla Model Y 360 · Jeep Cherokee 307'),
            ('Trucks', 'Nissan Frontier 37 · Toyota Tacoma 44 · Chevrolet Silverado 53', 'Jeep Gladiator 194 · Honda Ridgeline 164 · Ram 1500 119'),
            ('Minivans', 'Toyota Sienna 53', 'Chrysler Pacifica 281 · Chrysler Town & Country 175')]
FAQ = [('What is the Lemon Index?', 'A car\'s safety complaints filed with the U.S. government (NHTSA) per 100,000 cars sold, compared with the average car from the same model years. 100 is average, 50 means half as many complaints, 300 means three times as many.'),
       ('What is the most reliable car by owner complaints?', 'The Toyota 4Runner, with a Lemon Index of 27: about a quarter of the complaints of the average car, across 1.27 million sold (model years 2010-2022).'),
       ('Which car brand has the fewest complaints?', 'Lexus, at 30, followed by Porsche (34, small sample), Toyota (50), BMW (52) and Mercedes-Benz (54).'),
       ('Why does Tesla score so badly?', 'Most Model 3 and Model Y complaints are about forward collision avoidance (phantom braking). Tesla doesn\'t publish U.S. sales by model, so its index uses published estimates.'),
       ('Is this the same as a repair-cost ranking?', 'No. It counts safety complaints filed with the government within 3 years of each model year. It is not a record of repair bills or out-of-warranty costs.')]

def page(path, title, desc, body, ld=None, kind='website'):
    url = BASE + path; lds = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    beacon = f"<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{{\"token\": \"{CF}\"}}'></script>" if CF else ''
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="{kind}"><meta property="og:site_name" content="The Lemon Index"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}/assets/og.png"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/icon-64.png"><link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap"><link rel="stylesheet" href="/assets/site.css">{lds}</head>
<body><header class="top"><a class="brand" href="/"><img src="/assets/icon-64.png" alt="" width="32" height="32">The Lemon Index</a>
<nav><a href="/studies/">Studies</a><a href="/method/">Method</a><a class="yt" href="{YT}?sub_confirmation=1" rel="noopener">Subscribe</a></nav></header>
<main>{body}</main>
<footer class="foot"><div class="cta"><div><h2>New car studies, straight from the data.</h2><p>Every study becomes a video. Subscribe to see the next one first.</p></div><a class="btn" href="{YT}?sub_confirmation=1" rel="noopener">Subscribe on YouTube</a></div>
<p class="socs"><a href="{YT}" rel="noopener">YouTube</a> · <a href="{TT}" rel="noopener">TikTok</a> · <a href="{IG}" rel="noopener">Instagram</a> · <a href="/method/">How the index works</a></p>
<p class="fine">© {TODAY[:4]} The Lemon Index. Built from public NHTSA complaint data and published U.S. sales figures. Not affiliated with any automaker. Not a repair-cost or safety rating.</p></footer>{beacon}</body></html>'''
    f = os.path.join(OUT, path.strip('/'), 'index.html') if path.endswith('/') else os.path.join(OUT, path.strip('/'))
    os.makedirs(os.path.dirname(f), exist_ok=True); open(f, 'w', encoding='utf-8').write(doc)

def bars(rows, mx):
    return '<div class="bars">' + ''.join(f'<div class="b {"bad" if v > 100 else "good"}"><span class="bn">{E(n)}</span><span class="bt"><i style="width:{min(100, v / mx * 100):.1f}%"></i><em style="left:{100 / mx * 100:.1f}%"></em></span><b>{v}</b></div>' for n, v in rows) + '</div>'

STUDY = '/studies/most-reliable-cars/'
best_rows = ''.join(f'<tr><td>{i}</td><td>{E(n)}</td><td class="num good">{v}</td><td class="num">{E(s)}</td></tr>' for i, (n, v, s) in enumerate(BEST, 1))
worst_rows = ''.join(f'<tr><td>{E(n)}</td><td class="num bad">{v}</td><td>{E(w)}</td></tr>' for n, v, w in WORST)
seg_rows = ''.join(f'<tr><td><b>{E(a)}</b></td><td>{E(b)}</td><td>{E(c)}</td></tr>' for a, b, c in SEGMENTS)
faq = ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in FAQ)
os.makedirs(OUT, exist_ok=True)

# ---- home
page('/', 'The Lemon Index: Car Reliability From 1.6M Owner Complaints', 'Which cars break? We ranked 131 models and 22 brands by government safety complaints per car sold. 100 is average. Free data, updated with every study.', f'''
<section class="hero"><p class="kicker">Car data, not opinions</p><h1>Which cars break? <mark>1.6 million</mark> owner complaints, ranked.</h1>
<p class="lede">We read every safety complaint American drivers filed with the government since 1995, then divided by how many of each car were sold. The result is one number per car.</p>
<div class="scale"><div class="sbar"><i style="left:22%"></i></div><div class="sl"><span>0 · solid</span><span>100 · average car</span><span class="bad">300+ · lemon</span></div></div>
<div class="row"><a class="btn" href="{STUDY}">See the full ranking</a><a class="btn ghost" href="/method/">How the index works</a></div></section>
<section><h2>The most reliable cars</h2><p class="sub">Lowest Lemon Index, model years 2010-2022. Lower is better.</p>{bars([(n, v) for n, v, _ in BEST[:6]], 120)}</section>
<section><h2>The biggest lemons</h2><p class="sub">Highest Lemon Index. * Tesla uses published sales estimates.</p>{bars([(n, v) for n, v, _ in WORST[:6]], 440)}</section>
<section><h2>Every brand, best to worst</h2>{bars(BRANDS, 330)}<p class="note">* Porsche is a small sample. Tesla uses estimated U.S. sales.</p></section>
<section class="faq"><h2>Questions</h2>{faq}</section>''',
     ld=[{"@context": "https://schema.org", "@type": "WebSite", "name": "The Lemon Index", "url": BASE + '/'},
         {"@context": "https://schema.org", "@type": "Organization", "name": "The Lemon Index", "url": BASE + '/', "logo": BASE + '/assets/icon-180.png', "sameAs": [YT, TT, IG]},
         {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}])

# ---- study
page(STUDY, 'The Most Reliable Cars, According to 1.6 Million Owner Complaints', 'The most and least reliable cars and brands in the U.S., ranked by NHTSA safety complaints per 100,000 sold. Toyota 4Runner 27, Lexus 30, Tesla 322 (est.).', f'''
<article class="study"><p class="kicker">Study #1 · {TODAY}</p><h1>The Most Reliable Cars, According to 1.6 Million Owner Complaints</h1>
<p class="lede">The Toyota 4Runner drew about a quarter of the complaints of the average car. The Tesla Model S drew more than four times as many. Here's every number.</p>
<div class="stats"><div><b>1,607,537</b><span>complaints in the file</span></div><div><b>131</b><span>models ranked</span></div><div><b>22</b><span>brands</span></div><div><b>2010-2022</b><span>model years</span></div></div>
<h2>Most reliable: the top 10</h2><div class="tw"><table><thead><tr><th>#</th><th>Model</th><th>Lemon Index</th><th>U.S. sold</th></tr></thead><tbody>{best_rows}</tbody></table></div>
<p class="note">What it means for you: a long-running model with a low index is the safest bet. Most of this list has been on sale, mostly unchanged, for a decade.</p>
<h2>Least reliable: the bottom 10</h2><div class="tw"><table><thead><tr><th>Model</th><th>Lemon Index</th><th>Top complaint</th></tr></thead><tbody>{worst_rows}</tbody></table></div>
<p class="note">What it means for you: one part can sink a car. Check the top complaint for the exact model year before you buy. * Tesla uses published sales estimates.</p>
<h2>Brands, best to worst</h2>{bars(BRANDS, 330)}
<h2>Best and worst by type</h2><div class="tw"><table><thead><tr><th>Type</th><th>Best</th><th>Worst</th></tr></thead><tbody>{seg_rows}</tbody></table></div>
<h2>Three patterns in the data</h2>
<ol class="beats"><li><b>Year one is the risky year.</b> The bottom of the list is full of all-new models in their first years (Telluride, Palisade, Pacifica, the 2014 Cherokee). Wait for year two or three.</li>
<li><b>The Germans beat their reputation, early on.</b> BMW (52) and Mercedes-Benz (54) beat Honda (87) and Ford (144) in the first three years. This measures early safety complaints, not out-of-warranty repair bills.</li>
<li><b>Tesla's problem is mostly one system.</b> About 80% of Model 3 and Model Y complaints are about forward collision avoidance, the car braking hard for nothing.</li></ol>
<h2>How we measured it</h2><p>A complaint counts only if NHTSA received it within three years of the model year, so old and new cars get the same window. Each model year is divided by that year's U.S. sales, then compared with the average car of the same years. <a href="/method/">Full method and caveats →</a></p>
</article>''', kind='article',
     ld=[{"@context": "https://schema.org", "@type": "Dataset", "name": "Lemon Index: U.S. car reliability by NHTSA complaints per 100,000 sold", "description": "131 models and 22 brands, model years 2010-2022, ranked by safety complaints filed with NHTSA within 3 years of the model year per 100,000 U.S. sales, indexed to the average car (100).",
          "url": BASE + STUDY, "creator": {"@type": "Organization", "name": "The Lemon Index"}, "license": "https://creativecommons.org/licenses/by/4.0/", "isBasedOn": "https://www.nhtsa.gov/nhtsa-datasets-and-apis", "temporalCoverage": "2010/2022", "dateModified": TODAY},
         {"@context": "https://schema.org", "@type": "Article", "headline": "The Most Reliable Cars, According to 1.6 Million Owner Complaints", "datePublished": TODAY, "dateModified": TODAY, "author": {"@type": "Organization", "name": "The Lemon Index"}, "image": BASE + '/assets/og.png'}])

# ---- studies index
page('/studies/', 'Car Reliability Studies | The Lemon Index', 'Every Lemon Index study: car reliability, recalls and owner complaints, measured with public data.', f'''
<section><h1>Studies</h1><p class="lede">Each study turns millions of public records into one clear ranking.</p>
<a class="card" href="{STUDY}"><span class="kicker">Study #1</span><h2>The Most Reliable Cars, According to 1.6 Million Owner Complaints</h2><p>131 models, 22 brands. Toyota 4Runner 27 · Lexus 30 · Tesla 322 (est.)</p></a>
<p class="note">Next up: cars that last past 300,000 miles, the most unreliable cars ever made, and the best used cars under $10K.</p></section>''',
     ld=[{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Car Reliability Studies", "url": BASE + '/studies/', "hasPart": [{"@type": "Article", "headline": "The Most Reliable Cars, According to 1.6 Million Owner Complaints", "url": BASE + STUDY}]}])

# ---- method
page('/method/', 'How the Lemon Index Works | The Lemon Index', 'How we turn NHTSA safety complaints and U.S. sales into one reliability number per car, plus the caveats that come with it.', '''
<article class="study"><h1>How the Lemon Index works</h1>
<ol class="beats"><li><b>Complaints:</b> the full NHTSA owner-complaint file (1,607,537 vehicle complaints, 1995 to October 2026).</li>
<li><b>Sales:</b> U.S. sales per model per year from automakers' published figures. Tesla doesn't report by model, so we use published estimates and say so.</li>
<li><b>Same window for every car:</b> a complaint counts only if it was filed within 3 years of the model year.</li>
<li><b>Rate:</b> complaints per 100,000 cars sold, matched model year to sales year.</li>
<li><b>Index:</b> each car's rate against the average car of the same model years. 100 = average, 50 = half the complaints, 300 = triple.</li></ol>
<h2>What it doesn't measure</h2><p>A complaint is a safety complaint filed with the government, not a repair record. Fleet and rental-heavy models have fewer owners filing. Luxury lessees often go straight to the dealer. Some owners file more readily than others. Read it as early-life safety complaints, not total cost of ownership.</p>
<h2>Using the data</h2><p>The rankings are free to cite with a link to lemonindex.com (CC BY 4.0). The raw complaint data is public at NHTSA.</p></article>''',
     ld=[{"@context": "https://schema.org", "@type": "WebPage", "name": "How the Lemon Index Works", "url": BASE + '/method/', "about": "Car reliability measured as NHTSA safety complaints per 100,000 U.S. sales"}])

open(f'{OUT}/404.html', 'w', encoding='utf-8').write(open(f'{OUT}/index.html', encoding='utf-8').read().replace('<main>', '<main><section><h1>That page drove off.</h1><p><a href="/">Back to the rankings</a></p></section><!--', 1).replace('</main>', '--></main>', 1))
urls = ['/', STUDY, '/studies/', '/method/']
open(f'{OUT}/sitemap.xml', 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{BASE}{u}</loc><lastmod>{TODAY}</lastmod></url>' for u in urls) + '</urlset>')
open(f'{OUT}/robots.txt', 'w').write(f'User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')
open(f'{OUT}/llms.txt', 'w', encoding='utf-8').write(f'# The Lemon Index\n\n> Car reliability from public data. The Lemon Index = NHTSA safety complaints per 100,000 U.S. sales, vs the average car of the same model years (100 = average).\n\n- [The Most Reliable Cars, According to 1.6 Million Owner Complaints]({BASE}{STUDY}): Toyota 4Runner 27, Lexus ES 28, Lexus brand 30, Tesla brand 322 (est.)\n- [Method]({BASE}/method/)\n')
open(f'{OUT}/CNAME', 'w').write('lemonindex.com')
shutil.copytree('assets', f'{OUT}/assets', dirs_exist_ok=True)
print('built', len(urls), 'pages into', OUT)
