# 11-11: data_extras2.py (automaker repair notes, investigations, safety tech, crash photo) for the models data_new_models.py adds:
# the same code, run on data/years_new.json + extras_local_new.json, written to data/extras2_new.json (nothing already published changes).
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'data_extras2.py'), encoding='utf-8').read()
src = src.replace("RAW = os.path.join(HERE, 'data', 'raw_more')", "RAW = 'C:/Users/elift/Code/lemonindex-site/data/raw_more'")
src = src.replace("'extras_local.json'", "'extras_local_new.json'").replace("'years.json'", "'years_new.json'").replace("'extras2.json'", "'extras2_new.json'")
src = src[:src.index("od = out['honda-odyssey']")]
exec(compile(src, 'data_extras2.py', 'exec'), {'__file__': os.path.join(HERE, 'data_extras2.py'), '__name__': '__main__'})
print('extras2_new written')
