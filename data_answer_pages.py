# 11-23 search traffic (Job C): the pages that get the most Google impressions, for the short answer box under the page top (ans_box.py).
# Reads Search Console rows (0 HQ/Autopost/gsc/gsc.db, pulled daily) and writes data/answer_pages.json = {"made", "window", "pages": [path, ...]}:
# the top 200 lemonindex.com pages by impressions in the latest window. Only paths go in the repo (no queries, no counts).
#   usage: py -X utf8 data_answer_pages.py
import json, os, sqlite3, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
DB = r'C:\Users\elift\Desktop\Eliftforlife youtube\0 HQ\Autopost\gsc\gsc.db'
c = sqlite3.connect(DB)
start, end = c.execute("select min(start), max(end) from rows where site = 'https://lemonindex.com/' and window = 'cur'").fetchone()
rows = c.execute("select page, sum(impr) i from rows where site = 'https://lemonindex.com/' and window = 'cur' group by page order by i desc").fetchall()
pages = []
for page, _ in rows:
    p = page.replace('https://lemonindex.com', '') or '/'
    if '?' in p or '#' in p or p in pages: continue
    pages.append(p)
    if len(pages) >= 200: break
json.dump(dict(made=datetime.date.today().isoformat(), window=f'{start} to {end}', pages=pages),
          open(os.path.join(HERE, 'data', 'answer_pages.json'), 'w', encoding='utf-8'), indent=0)
print(f'answer pages: {len(pages)} (Search Console {start} to {end})')
