# 11-20 owner-quote cleanup (quote_clean.py): builds data/quote_vocab.json, the words owners actually use in NHTSA complaints.
# Every word in 10+ of ~450K complaint write-ups, with its count, so one-off typos ("accient") stay out, common slips ("om", "mu")
# show up as rare, and car words ("cvt", "tpms", "dealership") stay in. quote_clean.py uses it to spot garbled quotes, never to rewrite them.
#   usage: py tools/quote_vocab.py
import json, os, re, sqlite3
from collections import Counter
LEMON = r'C:\Users\elift\Desktop\Eliftforlife youtube\3 Lemon Index'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
con = sqlite3.connect(os.path.join(LEMON, 'data', 'complaints.db'))
df = Counter(); n = 0
for (t,) in con.execute('SELECT descr FROM rows WHERE descr IS NOT NULL AND rowid % 5 = 0'):
    df.update(set(re.findall(r"[a-z]+(?:'[a-z]+)?", t.lower()))); n += 1
voc = {w: c for w, c in sorted(df.items()) if c >= 10}   # word -> how many write-ups use it (quote_clean.py sets the cut-offs)
json.dump(voc, open(os.path.join(HERE, 'data', 'quote_vocab.json'), 'w', encoding='utf-8'), separators=(',', ':'))
print(n, 'write-ups,', len(voc), 'words -> data/quote_vocab.json')
