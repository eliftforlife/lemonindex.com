# /saved/ "My cars" (11-14, growth plan 4d): the cars a visitor saved with the Save buttons on model, year and VIN report pages.
# The list lives in the visitor's browser only (localStorage, assets/saved.js); this page is the empty shell saved.js fills from
# /assets/vr/<model id>.json (vin_report.py). A personal tool page: noindex, not in the sitemap.
# exec'd from build.py (uses page, phero).
_SVB = f'''<div class="pg">{phero('<a href="/cars/">All cars</a> · My cars', 'My cars.', 'The cars you saved, with their score and top problem. Pick up to 4 to compare.',
    extra='<link rel="stylesheet" href="/assets/saved.css?v=1"><div id="lsvx" aria-live="polite"><p class="lsv-load">Loading your saved cars…</p>'
          '<noscript><p class="lsv-empty">My cars needs JavaScript: your saved cars are kept in this browser, not on our server.</p></noscript></div>'
          '<script src="/assets/saved.js?v=1" defer></script>')}</div>'''
page('/saved/', 'My Cars: Your Saved Cars | The Lemon Index', 'The cars you saved on the Lemon Index, with each model year’s score, verdict and top problem. Kept in your browser only.', _SVB)
_p = f'{OUT}/saved/index.html'
_s = open(_p, encoding='utf-8').read()
open(_p, 'w', encoding='utf-8').write(_s.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow"><link rel="canonical"', 1))
