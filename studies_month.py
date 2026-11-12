# Monthly data studies (11-12, research #4). Run by build.py with exec() after the about/press pages (page, E, BASE, MST in scope).
# The numbers come from data/studies/<yyyy-mm>.json, written by 3 Lemon Index/data/studies/make_study.py (NHTSA complaints by the date
# NHTSA received them + recalls received that month). A month stays labelled "month to date" until NHTSA's file covers its last day.
# Classes: the about/press template (advp, advh1, ans, ygrid, yc, ab-l) + ms- for the few new bits (assets/studies.css).
MST_URLS = []
def _month_studies():
    if not MST: return
    def sec(h, body, cls=''): return f'<section class="yc{cls}"><h2>{h}</h2>{body}</section>'
    lk = lambda u, t: f'<a href="{u}">{E(t)}</a>' if u else E(t)
    for S in MST:
        ym, u = S['ym'], f'/studies/{S["ym"]}/'
        mtd = not S['final']; prev = S['prev']
        lead = (S['findings'] or [''])[0]
        banner = (f'<p class="ms-mtd"><b>Month to date.</b> Complaints NHTSA received {E(S["month"])} 1 to {S["days"]}, {S["year"]} (NHTSA&#39;s public file runs a few days behind). '
                  f'This page updates as more of the month comes in; the full-month version publishes in early {E(["January","February","March","April","May","June","July","August","September","October","November","December"][int(ym[5:]) % 12])}.</p>') if mtd else ''
        f = S['flags']
        keys = (f'<div class="ms-k"><p><b>{S["n"]:,}</b><span>owner complaints</span></p><p><b>{S["per_day"]:,}</b><span>a day ({E(prev["month"])}: {prev["per_day"]:,})</span></p>'
                f'<p><b>{f.get("crash", 0):,}</b><span>reported a crash</span></p><p><b>{f.get("fire", 0):,}</b><span>reported a fire</span></p></div>')
        sub = lambda *x: '<small class="ms-s">' + ' · '.join(y for y in x if y) + '</small>'   # 11-12: 3 columns max so phones keep a real table (4+ columns stack into cards)
        rows = ''.join(f'<tr><td>{i}. {lk(r["url"], r["name"])}{sub(E(r["top_part"]).capitalize(), ("most: " + lk(r["year_url"], r["top_year"])) if r["top_year"] else "")}</td><td>{r["n"]:,}</td><td>{r["prev_same"]:,}</td></tr>'
                       for i, r in enumerate(S['top'][:20], 1))
        top = (f'<p><img class="ms-chart" src="{S["chart"]}" alt="Bar chart: the 10 models with the most owner complaints, {E(S["label"])}" width="720" height="472" loading="lazy"></p>'
               f'<table class="ms-t"><thead><tr><th>Model, most common problem</th><th>Complaints</th><th>{E(prev["month"][:3])} 1-{S["days"]}</th></tr></thead><tbody>{rows}</tbody></table>'
               '<p class="yc-cap">The top 20, all model years together (every model is in the CSV). Raw counts favour cars that sell in big numbers; the next list is per car sold.</p>')
        rate = ''.join(f'<tr><td>{lk(r["url"], r["name"])}{sub(E(r["top_part"]).capitalize(), f"{r['sold']:,} sold")}</td><td>{r["per100k"]:g}</td><td>{r["n"]:,}</td></tr>' for r in S['rate'])
        rate = (f'<table class="ms-t"><thead><tr><th>Model year</th><th>Per 100,000 sold</th><th>Complaints</th></tr></thead><tbody>{rate}</tbody></table>'
                '<p class="yc-cap">Model years from the last 3 years with U.S. sales in our data, at least 20,000 sold and at least 6 complaints this month. A few days of complaints are a small sample: read this as a watch list, not a verdict.</p>') if rate else ''
        ris = ('<ul class="ab-l">' + ''.join(f'<li>{lk(r["url"], r["name"])}: <b>{r["n"]}</b> complaints, up from {r["prev_same"]} in the same days of {E(prev["month"])} (most often {E(r["top_part"])}).</li>' for r in S['risers']) + '</ul>') if S['risers'] else ''
        parts = ''.join(f'<tr><td>{E(p["part"]).capitalize()}{sub(f"{p['n']:,} complaints")}</td><td>{p["share"]:g}%</td><td>{p["prev_share"]:g}%</td></tr>' for p in S['parts'])
        parts = (f'<table class="ms-t"><thead><tr><th>Problem area</th><th>Share</th><th>In {E(prev["month"])}</th></tr></thead><tbody>{parts}</tbody></table>'
                 '<p class="yc-cap">One complaint can name more than one area, so shares add up to more than 100%.</p>')
        rec = ''.join(f'<tr><td>{lk(r["url"], ", ".join(r["cars"]))}{sub(E(r["part"]), E(r["mfr"]), "NHTSA " + E(r["id"]))}</td><td>{r["units"]:,}</td></tr>' for r in S['recalls'])
        rec = (f'<p>NHTSA received <b>{S["recalls_n"]}</b> new car recall{"s" * (S["recalls_n"] != 1)} covering <b>{S["recall_units"]:,}</b> vehicles.</p>'
               f'<table class="ms-t"><thead><tr><th>Cars, part, maker, campaign</th><th>Vehicles</th></tr></thead><tbody>{rec}</tbody></table>') if S['recalls'] else f'<p>No new car recalls in NHTSA&#39;s file for {E(S["label"])} yet.</p>'
        emb = E(f'<a href="{BASE}{u}"><img src="{BASE}{S["chart"]}" alt="{S["title"]}" width="720" style="max-width:100%;height:auto"></a><br>Source: <a href="{BASE}{u}">The Lemon Index</a>')
        dl = (f'<ul class="ab-l"><li><a href="{S["csv"]}" download>Every model, {E(S["label"])} (CSV)</a>: complaints, the same days of {E(prev["month"])}, crashes, fires, injuries and the most common problem.</li>'
              f'<li><a href="{S["chart"]}">The chart (SVG)</a></li></ul><p class="yc-cap">Embed the chart:</p><pre class="ms-emb"><code>{emb}</code></pre>'
              f'<p>Credit: <q>Source: The Lemon Index (lemonindex.com), from NHTSA owner complaints</q>, with a link to this page. Free to use (CC BY 4.0). Reporters: <a href="/press/">press page</a>.</p>')
        how = ('<p>Every vehicle complaint in NHTSA&#39;s public owner-complaint file that NHTSA <b>received</b> in the month, counted once per complaint (its ODI number), '
               'grouped by model across all model years, with the site&#39;s own make and model matching (a Ram 1500 and a Ram 2500 are both a Ram pickup). '
               'Per-car-sold numbers divide one model year&#39;s complaints by its U.S. sales. Recalls are the vehicle recalls NHTSA received that month, for car brands we cover.</p>'
               '<p>Complaints are owners&#39; own reports, not confirmed defects, and most owners never file one. This is not the Lemon Index score, which uses each car&#39;s first 3 years: '
               '<a href="/method/">how the index works</a>.</p>')
        other = [o for o in MST if o['ym'] != ym]
        more = sec('Other monthly studies', '<ul class="ab-l">' + ''.join(f'<li><a href="/studies/{o["ym"]}/">{E(o["title"])}</a></li>' for o in other) + '<li><a href="/studies/">All studies</a></li></ul>') if other else ''
        body = (f'<link rel="stylesheet" href="/assets/studies.css?v=2"><div class="advp abp msd"><header class="advh1"><p class="ph-e">Monthly study · {E(S["label"])}</p><h1>{E(S["title"])}</h1><p class="ans">{E(lead)}</p>{banner}</header>'
                '<div class="ygrid">'
                + sec('Key findings', keys + '<ul class="ab-l">' + ''.join(f'<li>{E(x)}</li>' for x in S['findings']) + '</ul>')
                + sec('Most complaints, by model', top)
                + (sec('Most complaints per car sold: newer cars', rate) if rate else '')
                + (sec(f'Rising fast vs {E(prev["month"])}', ris) if ris else '')
                + sec('What owners complained about', parts)
                + sec('New recalls', rec)
                + sec('Download, embed and cite', dl)
                + sec('How we counted', how) + more + '</div></div>')
        desc = (f'{"Month to date: " if mtd else ""}the cars that drew the most NHTSA owner complaints in {S["month"]} {S["year"]}, per car sold, the problems owners reported and new recalls. Free CSV and chart.')
        page(u, f'{S["title"]} | Lemon Index', desc, body, kind='article',
             ld=[{"@context": "https://schema.org", "@type": "Article", "headline": S['title'], "datePublished": S['made'][:10], "dateModified": S['made'][:10],
                  "author": {"@type": "Organization", "name": "The Lemon Index"}, "image": BASE + S['chart'], "url": BASE + u},
                 {"@context": "https://schema.org", "@type": "Dataset", "name": f'NHTSA owner complaints by model, {S["label"]}', "url": BASE + u, "license": "https://creativecommons.org/licenses/by/4.0/",
                  "temporalCoverage": f'{ym}-01/{S["through"]}', "isBasedOn": "https://www.nhtsa.gov/nhtsa-datasets-and-apis", "creator": {"@type": "Organization", "name": "The Lemon Index"},
                  "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE + S['csv']}]}])
        MST_URLS.append(u)
_month_studies()
