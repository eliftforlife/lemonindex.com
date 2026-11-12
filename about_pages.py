# /about/ and /press/ (11-12, Priya, a journalist: "/press/ and /about/ are 404s... no named contact"). Run by build.py with exec() after the
# legal pages (page, E, CARS, BRANDS, COUNTED, XL, YEARS, CONTACT, LEGAL_NAME, YT, TT, IG in scope). Every number comes from the same data the
# other pages use, with what it covers spelled out, so a reporter can tell the totals apart.
def _about_pages():
    sev_total = sum(((x or {}).get('sev') or {}).get('total', 0) for ys in XL.values() for x in ys.values())
    nb = len({c['brand'] for c in CARS}); best, worst = CARS[0], CARS[-1]
    ex = next((c for c in CARS if c['id'] == 'honda-cr-v'), best)   # the citation example uses a real score
    br = sorted(BRANDS, key=lambda t: t[1]); bb, bw = br[0][0].rstrip('*'), br[-1][0].rstrip('*')
    def sec(h, body): return f'<section class="yc"><h2>{h}</h2>{body}</section>'
    about = ('<div class="advp abp"><header class="advh1"><p class="ph-e">About</p><h1>Who makes the Lemon Index.</h1>'
             '<p class="ans">The Lemon Index is made by Elijah Westbrook. It turns public U.S. government car data into one plain number per car: how many owner complaints it drew for every car sold, against the average car.</p></header><div class="ygrid">'
             + sec('Who runs it', f'<p>Elijah Westbrook researches, builds and writes the site and the <a href="{YT}" rel="noopener">Lemon Index YouTube channel</a>. It is published by {E(LEGAL_NAME)}. '
                   'We are not paid by, or affiliated with, any automaker or dealer. The site is free, paid for by ads and reader donations.</p>')
             + sec('Where the data comes from', '<ul class="ab-l">'
                   '<li><b>Owner complaints and recalls:</b> NHTSA, the U.S. government&#39;s road safety agency (its public complaint and recall files).</li>'
                   '<li><b>Crash-test stars:</b> NHTSA&#39;s 5-Star Safety Ratings.</li>'
                   '<li><b>Fuel economy:</b> the EPA (fueleconomy.gov).</li>'
                   '<li><b>Sales:</b> published U.S. sales figures (estimates for Tesla, which doesn&#39;t publish sales by model).</li>'
                   '<li><b>Buyer and owner videos:</b> some lists and the video sections count what YouTube buyer&#39;s guides and owners say, and each one says so.</li></ul>'
                   '<p>Complaints are owners&#39; own reports, not proof of a defect. The score measures early complaints per car sold; it is not a repair-cost or safety rating.</p>')
             + sec('How the score works', '<p>Complaints filed within 3 years of each model year, divided by U.S. sales, compared with the average car of the same model years. 100 is average; 50 means half the complaints; 200 means twice as many. '
                   'The full method, its limits and its corrections: <a href="/method/">how the index works</a>.</p>')
             + sec('Use the data', '<p>Everything is free to use with credit (CC BY 4.0): <a href="/data/">download the data</a>, <a href="/images/">free images</a>. Writing about cars? See the <a href="/press/">press page</a>.</p>')
             + sec('Contact', f'<p>Questions, corrections or a car you want covered: <a href="mailto:{CONTACT}">{CONTACT}</a> or the <a href="/contact/">contact page</a>. We usually answer within 2 business days.</p>')
             + '</div></div>')
    page('/about/', 'About the Lemon Index: Who Makes It and Where the Data Comes From', 'The Lemon Index is made by Elijah Westbrook from public NHTSA complaint, recall and crash-test data, EPA fuel economy and U.S. sales. How it works and how to reach us.', about,
         ld=[{"@context": "https://schema.org", "@type": "AboutPage", "url": BASE + '/about/', "name": "About the Lemon Index",
              "publisher": {"@type": "Organization", "name": "The Lemon Index", "url": BASE + '/', "founder": {"@type": "Person", "name": "Elijah Westbrook"}}}])
    stats = [('1,607,537', 'complaints in NHTSA&#39;s file', 'Every vehicle complaint in NHTSA&#39;s owner-complaint file, 1995 to October 2026. The raw pool everything is drawn from.'),
             (f'{COUNTED:,}', 'complaints in the ranking', f'The complaints behind the scores and rankings: filed within 3 years of a 2010 to 2022 model year, for the {len(CARS)} ranked models. This is the number on the home page and in the study.'),
             (f'{sev_total:,}', 'complaints on the car pages', f'All complaints on our model and year pages ({len(XL)} models, every model year we list). The total on the statistics page.'),
             (str(len(CARS)), 'models ranked', f'Models with enough U.S. sales to score, across {nb} brands.'),
             (f'{best["li"]}', f'{E(best["name"])}', f'The lowest Lemon Index of any ranked model: {plain(best["li"])}. 100 = average.'),
             (f'{worst["li"]}', f'{E(worst["name"])}{"*" if worst.get("est") else ""}', 'The highest Lemon Index of any ranked model' + (' (*sales are published estimates)' if worst.get('est') else '') + '.')]
    tiles = '<div class="stt prs">' + ''.join(f'<div><b>{a}</b><span>{b}</span><small>{c}</small></div>' for a, b, c in stats) + '</div>'
    press = ('<div class="advp abp"><header class="advh1"><p class="ph-e">Press</p><h1>For reporters.</h1>'
             '<p class="ans">Free car reliability data from NHTSA owner complaints per car sold. Cite it, chart it, use our images: just credit the Lemon Index and link to lemonindex.com.</p></header>'
             f'<section class="yc"><h2>Press contact</h2><p>Elijah Westbrook, The Lemon Index: <a href="mailto:{CONTACT}">{CONTACT}</a> (or the <a href="/contact/">contact page</a>). We usually answer within 2 business days, and we&#39;ll send the exact numbers behind any chart.</p></section>'
             f'<section class="yc"><h2>The key numbers, and what each one counts</h2>{tiles}<p class="yc-cap">Brands: {E(bb)} has the lowest brand score and {E(bw)} the highest (<a href="/brands/">every brand</a>). The complaint totals differ because each counts a different set of complaints; cite the one that matches your story.</p></section>'
             '<div class="ygrid">'
             + sec('How to cite', f'<p>Credit line: <q>Source: The Lemon Index (lemonindex.com)</q>, with a link. For a score, name the model, its model years and the date, e.g. <q>a Lemon Index of {ex["li"]} for the {ex["years"].replace("-", " to ")} {E(ex["name"])} (100 = average car)</q>.</p>'
                   '<p>Method and its limits: <a href="/method/">how the index works</a>. The study behind the rankings: <a href="/studies/most-reliable-cars/">The Most Reliable Cars, According to 1.6 Million Owner Complaints</a>.</p>')
             + sec('Downloads', '<ul class="ab-l"><li><a href="/data/">Data downloads</a>: scores and complaints by model year, transmission complaints (CSV, CC BY 4.0).</li>'
                   '<li><a href="/images/">Free images</a>: our car and engine illustrations (CC BY 4.0).</li>'
                   '<li>Logo: <a href="/assets/icon-512.png">512 px PNG</a> · social card: <a href="/assets/og.png">og.png</a>.</li>'
                   '<li><a href="/rankings/">Rankings</a> and <a href="/stats/car-complaints/">statistics</a> pages to link to.</li></ul>')
             + sec('What the score is, and isn&#39;t', '<p>Owner complaints to NHTSA filed within 3 years of each model year, per car sold, against the average car of the same model years (100 = average, lower is better). '
                   'Complaints are owners&#39; reports, not confirmed defects, and most owners never file one, so read scores as a comparison between cars, not a failure rate. It is not a repair-cost or a safety rating.</p>')
             + '</div></div>')
    page('/press/', 'Press: Lemon Index Data, Key Numbers and How to Cite', 'For reporters: the Lemon Index press contact, the key numbers and what each one counts, how to cite us, and free data and image downloads.', press,
         ld=[{"@context": "https://schema.org", "@type": "WebPage", "url": BASE + '/press/', "name": "Lemon Index press page"}])
    LEGAL_URLS.extend(['/about/', '/press/'])
_about_pages()
